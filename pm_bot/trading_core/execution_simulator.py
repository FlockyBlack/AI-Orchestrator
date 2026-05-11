from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Mapping, Sequence

from pm_bot.trading_core.risk_gate import run_risk_gate
from pm_bot.trading_core.schemas import (
    ARTIFACT_DIR,
    GENERATED_AT,
    SIMULATED_EXECUTION_RESULT_CONTRACT,
    assert_valid,
    bullet_lines,
    clean_text,
    load_json_object,
    mapping_rows,
    trading_core_safety_summary,
    validate_simulated_execution_result,
    write_json,
    write_text,
)
from pm_bot.trading_core.trade_intent_candidate import build_paper_trade_intent_candidates

SIMULATED_EXECUTION_BATCH_CONTRACT = "pmbot_simulated_execution_result_batch.v1"
FIXTURE_FILL_PRICE_USD = 1.0


def simulate_execution_for_intent(
    candidate: Mapping[str, Any],
    risk_result: Mapping[str, Any],
    *,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    action_type = clean_text(candidate.get("paper_action_type"))
    intended_notional = float(candidate.get("intended_notional_usd", 0) or 0)

    if risk_result.get("blocked") is True:
        status = "rejected"
        simulated_fill = False
        filled_notional = 0.0
        paper_units = 0.0
        reason = "risk_gate_blocked"
    elif action_type == "observe_only":
        status = "skipped"
        simulated_fill = False
        filled_notional = 0.0
        paper_units = 0.0
        reason = "observe_only_candidate"
    elif action_type == "simulated_entry":
        status = "immediate_fill"
        simulated_fill = True
        filled_notional = intended_notional
        paper_units = filled_notional / FIXTURE_FILL_PRICE_USD if FIXTURE_FILL_PRICE_USD else 0.0
        reason = "paper_simulator_fixture_fill"
    else:
        status = "skipped"
        simulated_fill = False
        filled_notional = 0.0
        paper_units = 0.0
        reason = "simulated_skip_candidate"

    result = {
        "contract_version": SIMULATED_EXECUTION_RESULT_CONTRACT,
        "execution_id": f"sim-exec-020-021-{clean_text(candidate.get('intent_id'))}",
        "intent_id": clean_text(candidate.get("intent_id")),
        "risk_gate_result_id": clean_text(risk_result.get("gate_result_id")),
        "market_id": clean_text(candidate.get("market_id")),
        "market_title": clean_text(candidate.get("market_title")),
        "hypothesis_id": clean_text(candidate.get("hypothesis_id")),
        "executed_at": generated_at,
        "paper_action_type": action_type,
        "execution_status": status,
        "execution_reason": reason,
        "simulated_fill": simulated_fill,
        "filled_notional_usd": filled_notional,
        "paper_fill_price_usd": FIXTURE_FILL_PRICE_USD if simulated_fill else None,
        "paper_units": paper_units,
        "fixture_price_used": simulated_fill,
        "fixture_price_note": (
            "No local live price/reference exists; the simulator uses an explicit paper fixture "
            "placeholder only for ledger plumbing."
            if simulated_fill
            else "No fixture fill needed."
        ),
        "paper_only": True,
        "real_order_submitted": False,
        "wallet_used": False,
        "trading_endpoint_used": False,
        "live_price_used": False,
    }
    valid, errors = validate_simulated_execution_result(result)
    assert_valid(result["execution_id"], valid, errors)
    return result


def run_execution_simulator(
    *,
    candidates_batch: Mapping[str, Any] | None = None,
    risk_gate_batch: Mapping[str, Any] | None = None,
    out_json_path: str | Path = ARTIFACT_DIR / "simulated_execution_results.json",
    out_md_path: str | Path = ARTIFACT_DIR / "simulated_execution_results.md",
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    candidates = dict(candidates_batch or build_paper_trade_intent_candidates(generated_at=generated_at))
    risk_batch = dict(risk_gate_batch or run_risk_gate(candidates_batch=candidates, generated_at=generated_at))
    risk_by_intent = {clean_text(row.get("intent_id")): row for row in mapping_rows(risk_batch.get("results"))}
    results = [
        simulate_execution_for_intent(candidate, risk_by_intent[clean_text(candidate.get("intent_id"))], generated_at=generated_at)
        for candidate in mapping_rows(candidates.get("candidates"))
    ]
    report = {
        "contract_version": SIMULATED_EXECUTION_BATCH_CONTRACT,
        "batch_id": "simulated-execution-results-night-020-021",
        "generated_at": generated_at,
        "simulated_execution_count": len(results),
        "simulated_fill_count": len([row for row in results if row["simulated_fill"]]),
        "skipped_count": len([row for row in results if row["execution_status"] == "skipped"]),
        "rejected_count": len([row for row in results if row["execution_status"] == "rejected"]),
        "results": results,
        "safety_summary": trading_core_safety_summary(),
    }
    write_json(out_json_path, report)
    write_text(out_md_path, render_simulated_execution_results_markdown(report))
    return report


def render_simulated_execution_results_markdown(report: Mapping[str, Any]) -> str:
    lines = [
        "# PMBOT Simulated Execution Results",
        "",
        f"- Results: {report.get('simulated_execution_count')}",
        f"- Paper fixture fills: {report.get('simulated_fill_count')}",
        f"- Skipped: {report.get('skipped_count')}",
        f"- Rejected: {report.get('rejected_count')}",
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
                f"- Status: `{result.get('execution_status')}`",
                f"- Filled paper notional: `${result.get('filled_notional_usd')}`",
                f"- Fixture price used: `{str(result.get('fixture_price_used')).lower()}`",
                f"- Reason: {result.get('execution_reason')}",
                "",
            ]
        )
    lines.extend(
        [
            "## Safety",
            "",
            *bullet_lines(
                [
                    "real_order_submitted is false for every result",
                    "wallet_used is false for every result",
                    "trading_endpoint_used is false for every result",
                    "live_price_used is false for every result",
                    "No network calls are made by this simulator",
                ]
            ),
        ]
    )
    return "\n".join(lines) + "\n"


def load_and_run_execution_simulator(
    *,
    candidates_path: str | Path = ARTIFACT_DIR / "paper_trade_intent_candidates.json",
    risk_gate_path: str | Path = ARTIFACT_DIR / "risk_gate_results.json",
    out_json_path: str | Path = ARTIFACT_DIR / "simulated_execution_results.json",
    out_md_path: str | Path = ARTIFACT_DIR / "simulated_execution_results.md",
) -> dict[str, Any]:
    candidates = load_json_object(candidates_path, label="paper trade intent candidates")
    risk_gate = load_json_object(risk_gate_path, label="risk gate results")
    return run_execution_simulator(
        candidates_batch=candidates,
        risk_gate_batch=risk_gate,
        out_json_path=out_json_path,
        out_md_path=out_md_path,
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the PMBOT paper execution simulator.")
    parser.add_argument("--candidates", default=str(ARTIFACT_DIR / "paper_trade_intent_candidates.json"))
    parser.add_argument("--risk-gate", default=str(ARTIFACT_DIR / "risk_gate_results.json"))
    parser.add_argument("--out-json", default=str(ARTIFACT_DIR / "simulated_execution_results.json"))
    parser.add_argument("--out-md", default=str(ARTIFACT_DIR / "simulated_execution_results.md"))
    args = parser.parse_args(argv)
    load_and_run_execution_simulator(
        candidates_path=args.candidates,
        risk_gate_path=args.risk_gate,
        out_json_path=args.out_json,
        out_md_path=args.out_md,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
