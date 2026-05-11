from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Mapping, Sequence

from pm_bot.trading_core.risk_limits import default_paper_risk_limits
from pm_bot.trading_core.schemas import (
    ARTIFACT_DIR,
    GENERATED_AT,
    RISK_GATE_RESULT_CONTRACT,
    assert_valid,
    bullet_lines,
    clean_text,
    load_json_object,
    mapping_rows,
    trading_core_safety_summary,
    validate_risk_gate_result,
    write_json,
    write_text,
)
from pm_bot.trading_core.trade_intent_candidate import build_paper_trade_intent_candidates

RISK_GATE_BATCH_CONTRACT = "pmbot_risk_gate_result_batch.v1"


def evaluate_paper_trade_intent(
    candidate: Mapping[str, Any],
    limits: Mapping[str, Any] | None = None,
    *,
    current_market_exposure_usd: float = 0.0,
    current_total_exposure_usd: float = 0.0,
    current_open_positions: int = 0,
    market_blocked: bool = False,
) -> dict[str, Any]:
    active_limits = dict(limits or default_paper_risk_limits())
    block_reasons: list[str] = []
    warnings: list[str] = []
    intended_notional = float(candidate.get("intended_notional_usd", 0) or 0)

    if candidate.get("paper_only") is not True:
        block_reasons.append("paper_only_not_true")
    if candidate.get("non_executable") is not True:
        block_reasons.append("non_executable_not_true")
    if candidate.get("real_order_allowed") is True:
        block_reasons.append("real_order_allowed_true")
    if candidate.get("wallet_required") is True:
        block_reasons.append("wallet_required_true")
    if candidate.get("trading_endpoint_required") is True:
        block_reasons.append("trading_endpoint_required_true")
    if candidate.get("operator_review_required") is not True:
        block_reasons.append("operator_review_not_required")
    if active_limits.get("allow_real_orders") is not False:
        block_reasons.append("risk_limits_allow_real_orders_not_false")
    if active_limits.get("allow_wallet") is not False:
        block_reasons.append("risk_limits_allow_wallet_not_false")
    if active_limits.get("allow_trading_endpoints") is not False:
        block_reasons.append("risk_limits_allow_trading_endpoints_not_false")
    if active_limits.get("allow_autonomous_execution") is not False:
        block_reasons.append("risk_limits_allow_autonomous_execution_not_false")
    if intended_notional > float(active_limits.get("max_single_intent_notional_usd", 0)):
        block_reasons.append("intended_notional_exceeds_single_intent_limit")
    if current_market_exposure_usd + intended_notional > float(active_limits.get("max_market_paper_exposure_usd", 0)):
        block_reasons.append("market_exposure_limit_exceeded")
    if current_total_exposure_usd + intended_notional > float(active_limits.get("max_total_paper_exposure_usd", 0)):
        block_reasons.append("total_exposure_limit_exceeded")
    if current_open_positions >= int(active_limits.get("max_open_paper_positions", 0)) and intended_notional > 0:
        block_reasons.append("max_open_paper_positions_exceeded")
    if _has_severe_missing_evidence(candidate):
        block_reasons.append("severe_missing_evidence")
    if market_blocked or candidate.get("market_blocked") is True:
        block_reasons.append("market_blocked")

    if candidate.get("paper_action_type") == "observe_only":
        warnings.append("observe_only_candidate_has_no_fill_intent")
    if "saved_public_evidence_packet_missing" in candidate.get("missing_evidence", []):
        warnings.append("saved_public_evidence_packet_missing")
    if "outcome_unresolved" in candidate.get("missing_evidence", []):
        warnings.append("outcome_unresolved")

    allowed = not block_reasons
    result = {
        "contract_version": RISK_GATE_RESULT_CONTRACT,
        "gate_result_id": f"risk-gate-020-021-{clean_text(candidate.get('intent_id'))}",
        "intent_id": clean_text(candidate.get("intent_id")),
        "market_id": clean_text(candidate.get("market_id")),
        "market_title": clean_text(candidate.get("market_title")),
        "risk_gate_status": "allowed_for_paper_simulation" if allowed else "blocked",
        "allowed": allowed,
        "blocked": not allowed,
        "block_reasons": block_reasons,
        "warnings": warnings,
        "intended_notional_usd": intended_notional,
        "paper_action_type": clean_text(candidate.get("paper_action_type")),
        "paper_only": True,
        "non_executable": True,
        "real_order_allowed": False,
        "wallet_required": False,
        "trading_endpoint_required": False,
        "operator_review_required": True,
        "limits_checked": {
            "max_total_paper_exposure_usd": active_limits.get("max_total_paper_exposure_usd"),
            "max_market_paper_exposure_usd": active_limits.get("max_market_paper_exposure_usd"),
            "max_single_intent_notional_usd": active_limits.get("max_single_intent_notional_usd"),
            "max_open_paper_positions": active_limits.get("max_open_paper_positions"),
        },
    }
    valid, errors = validate_risk_gate_result(result)
    assert_valid(result["gate_result_id"], valid, errors)
    return result


def run_risk_gate(
    *,
    candidates_batch: Mapping[str, Any] | None = None,
    limits: Mapping[str, Any] | None = None,
    out_json_path: str | Path = ARTIFACT_DIR / "risk_gate_results.json",
    out_md_path: str | Path = ARTIFACT_DIR / "risk_gate_results.md",
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    batch = dict(candidates_batch or build_paper_trade_intent_candidates(generated_at=generated_at))
    active_limits = dict(limits or default_paper_risk_limits(generated_at=generated_at))
    market_exposure: dict[str, float] = {}
    total_exposure = 0.0
    open_positions = 0
    results = []
    for candidate in mapping_rows(batch.get("candidates")):
        market_id = clean_text(candidate.get("market_id"))
        result = evaluate_paper_trade_intent(
            candidate,
            active_limits,
            current_market_exposure_usd=market_exposure.get(market_id, 0.0),
            current_total_exposure_usd=total_exposure,
            current_open_positions=open_positions,
        )
        results.append(result)
        if result["allowed"] and float(candidate.get("intended_notional_usd", 0) or 0) > 0:
            notional = float(candidate.get("intended_notional_usd", 0) or 0)
            market_exposure[market_id] = market_exposure.get(market_id, 0.0) + notional
            total_exposure += notional
            open_positions += 1

    report = {
        "contract_version": RISK_GATE_BATCH_CONTRACT,
        "batch_id": "risk-gate-results-night-020-021",
        "generated_at": generated_at,
        "risk_allowed_count": len([row for row in results if row["allowed"]]),
        "risk_blocked_count": len([row for row in results if row["blocked"]]),
        "results": results,
        "paper_exposure_reserved_usd": total_exposure,
        "safety_summary": trading_core_safety_summary(),
    }
    write_json(out_json_path, report)
    write_text(out_md_path, render_risk_gate_results_markdown(report))
    return report


def render_risk_gate_results_markdown(report: Mapping[str, Any]) -> str:
    lines = [
        "# PMBOT Paper Risk Gate Results",
        "",
        f"- Allowed for paper simulation: {report.get('risk_allowed_count')}",
        f"- Blocked: {report.get('risk_blocked_count')}",
        f"- Paper exposure reserved: `${report.get('paper_exposure_reserved_usd')}`",
        "",
        "## Results",
        "",
    ]
    for result in mapping_rows(report.get("results")):
        lines.extend(
            [
                f"### `{result.get('market_id')}`",
                "",
                f"- Intent: `{result.get('intent_id')}`",
                f"- Status: `{result.get('risk_gate_status')}`",
                f"- Intended paper notional: `${result.get('intended_notional_usd')}`",
                "- Block reasons:",
                *bullet_lines(str(item) for item in result.get("block_reasons", [])),
                "- Warnings:",
                *bullet_lines(str(item) for item in result.get("warnings", [])),
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def load_and_run_risk_gate(
    *,
    candidates_path: str | Path = ARTIFACT_DIR / "paper_trade_intent_candidates.json",
    limits_path: str | Path = ARTIFACT_DIR / "paper_risk_limits.json",
    out_json_path: str | Path = ARTIFACT_DIR / "risk_gate_results.json",
    out_md_path: str | Path = ARTIFACT_DIR / "risk_gate_results.md",
) -> dict[str, Any]:
    candidates = load_json_object(candidates_path, label="paper trade intent candidates")
    limits = load_json_object(limits_path, label="paper risk limits")
    return run_risk_gate(
        candidates_batch=candidates,
        limits=limits,
        out_json_path=out_json_path,
        out_md_path=out_md_path,
    )


def _has_severe_missing_evidence(candidate: Mapping[str, Any]) -> bool:
    missing = set(candidate.get("missing_evidence", []))
    if "analysis_source_missing" in missing or "active_hypothesis_missing" in missing:
        return True
    if candidate.get("paper_action_type") == "simulated_entry" and "saved_public_evidence_packet_missing" in missing:
        return True
    return False


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the PMBOT paper risk gate.")
    parser.add_argument("--candidates", default=str(ARTIFACT_DIR / "paper_trade_intent_candidates.json"))
    parser.add_argument("--limits", default=str(ARTIFACT_DIR / "paper_risk_limits.json"))
    parser.add_argument("--out-json", default=str(ARTIFACT_DIR / "risk_gate_results.json"))
    parser.add_argument("--out-md", default=str(ARTIFACT_DIR / "risk_gate_results.md"))
    args = parser.parse_args(argv)
    load_and_run_risk_gate(
        candidates_path=args.candidates,
        limits_path=args.limits,
        out_json_path=args.out_json,
        out_md_path=args.out_md,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
