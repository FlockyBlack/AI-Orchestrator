from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from pm_bot.trading_core.risk_prep_config import (
    RISK_ENGINE_CONFIG_VERSION,
    build_default_risk_engine_config,
    validate_risk_engine_config,
)
from pm_bot.trading_core.schemas import (
    ARTIFACT_DIR,
    GENERATED_AT,
    bullet_lines,
    clean_text,
    load_json_object,
    mapping_rows,
    trading_core_safety_summary,
    write_json,
    write_text,
)
from pm_bot.trading_core.trade_intent_candidate import build_paper_trade_intent_candidates

RISK_DECISION_INPUT_CONTRACT = "pmbot_risk_engine_decision_input.v1"
RISK_DECISION_CONTRACT = "pmbot_risk_engine_decision.v1"
RISK_DECISION_LEDGER_CONTRACT = "pmbot_risk_engine_decision_ledger.v1"

DECISION_ALLOWED = "allowed"
DECISION_BLOCKED = "blocked"
DECISION_NEEDS_MANUAL_APPROVAL = "needs_manual_approval"

APPROVED_OPERATOR_STATUSES = {
    "approved",
    "operator_approved",
    "approved_for_scoped_public_read_only_fetch_only",
    "operator_approved_public_read_only_refresh",
}
FRESH_EVIDENCE_STATUSES = {"fresh", "fresh_enough", "covered_with_local_evidence"}
SOURCE_GAP_FREE_STATUSES = {"no_gap", "no_gaps", "covered", "covered_with_local_evidence"}


class RiskEngineDecisionError(ValueError):
    pass


def build_risk_decision_input(
    *,
    run_id: str,
    market_id: str,
    action_type: str,
    requested_notional_usd: float,
    current_total_exposure_usd: float,
    current_market_exposure_usd: float,
    evidence_freshness_status: str,
    source_gap_status: str,
    operator_approval_status: str,
    config_version: str,
    intent_id: str = "",
    hypothesis_id: str = "",
) -> dict[str, Any]:
    return {
        "contract_version": RISK_DECISION_INPUT_CONTRACT,
        "run_id": clean_text(run_id),
        "market_id": clean_text(market_id),
        "intent_id": clean_text(intent_id),
        "hypothesis_id": clean_text(hypothesis_id),
        "action_type": clean_text(action_type),
        "requested_notional_usd": float(requested_notional_usd),
        "current_total_exposure_usd": float(current_total_exposure_usd),
        "current_market_exposure_usd": float(current_market_exposure_usd),
        "evidence_freshness_status": clean_text(evidence_freshness_status),
        "source_gap_status": clean_text(source_gap_status),
        "operator_approval_status": clean_text(operator_approval_status),
        "config_version": clean_text(config_version),
    }


def evaluate_risk_decision(
    decision_input: Mapping[str, Any],
    risk_config: Mapping[str, Any] | None = None,
    *,
    created_at: str = GENERATED_AT,
) -> dict[str, Any]:
    config = dict(risk_config or build_default_risk_engine_config(generated_at=created_at))
    config_valid, config_errors = validate_risk_engine_config(config)
    if not config_valid:
        raise RiskEngineDecisionError("; ".join(config_errors))

    input_errors = _validate_risk_decision_input(decision_input)
    if input_errors:
        raise RiskEngineDecisionError("; ".join(input_errors))

    normalized_input = _normalized_decision_input(decision_input, config)
    requested_notional = float(normalized_input["requested_notional_usd"])
    current_total_exposure = float(normalized_input["current_total_exposure_usd"])
    current_market_exposure = float(normalized_input["current_market_exposure_usd"])
    projected_total_exposure = round(current_total_exposure + requested_notional, 2)
    projected_market_exposure = round(current_market_exposure + requested_notional, 2)
    market_id = clean_text(normalized_input.get("market_id"))
    allowlist = {clean_text(item) for item in config.get("market_allowlist", []) if clean_text(item)}
    denylist = {clean_text(item) for item in config.get("market_denylist", []) if clean_text(item)}

    blocking_reasons: list[str] = []
    manual_reasons: list[str] = []

    if config.get("kill_switch_enabled") is True:
        _append_reason(blocking_reasons, "KILL_SWITCH_ENABLED")
    if market_id in denylist:
        _append_reason(blocking_reasons, "MARKET_DENYLISTED")
    if allowlist and market_id not in allowlist:
        _append_reason(blocking_reasons, "MARKET_NOT_ALLOWLISTED")
    if projected_total_exposure > float(config.get("max_total_exposure_usd", 0) or 0):
        _append_reason(blocking_reasons, "TOTAL_EXPOSURE_LIMIT_EXCEEDED")
    if projected_market_exposure > float(config.get("max_market_exposure_usd", 0) or 0):
        _append_reason(blocking_reasons, "MARKET_EXPOSURE_LIMIT_EXCEEDED")
    if requested_notional > float(config.get("max_single_action_notional_usd", 0) or 0):
        _append_reason(blocking_reasons, "SINGLE_ACTION_NOTIONAL_LIMIT_EXCEEDED")

    evidence_status = clean_text(normalized_input.get("evidence_freshness_status")).lower()
    evidence_is_fresh = evidence_status in FRESH_EVIDENCE_STATUSES
    if not evidence_is_fresh:
        if config.get("require_fresh_evidence") is True and config.get("manual_approval_required") is True:
            _append_reason(manual_reasons, "EVIDENCE_NOT_FRESH_REQUIRES_MANUAL_APPROVAL")
        elif config.get("require_fresh_evidence") is True:
            _append_reason(blocking_reasons, "EVIDENCE_NOT_FRESH")
        elif config.get("manual_approval_required") is True:
            _append_reason(manual_reasons, "EVIDENCE_NOT_FRESH_REVIEW")

    source_gap_status = clean_text(normalized_input.get("source_gap_status")).lower()
    source_gap_present = source_gap_status not in SOURCE_GAP_FREE_STATUSES
    if source_gap_present:
        if config.get("block_on_source_gap") is True:
            _append_reason(blocking_reasons, "SOURCE_GAP_PRESENT")
        elif config.get("manual_approval_required") is True:
            _append_reason(manual_reasons, "SOURCE_GAP_REQUIRES_MANUAL_APPROVAL")

    operator_status = clean_text(normalized_input.get("operator_approval_status")).lower()
    if config.get("manual_approval_required") is True and operator_status not in APPROVED_OPERATOR_STATUSES:
        _append_reason(manual_reasons, "MANUAL_APPROVAL_REQUIRED")

    if blocking_reasons:
        decision = DECISION_BLOCKED
    elif manual_reasons:
        decision = DECISION_NEEDS_MANUAL_APPROVAL
    else:
        decision = DECISION_ALLOWED

    reason_codes = [*blocking_reasons, *[reason for reason in manual_reasons if reason not in blocking_reasons]]
    limit_snapshot = {
        "config_id": clean_text(config.get("config_id")),
        "config_version": clean_text(config.get("config_version") or RISK_ENGINE_CONFIG_VERSION),
        "requested_notional_usd": requested_notional,
        "current_total_exposure_usd": current_total_exposure,
        "projected_total_exposure_usd": projected_total_exposure,
        "max_total_exposure_usd": float(config.get("max_total_exposure_usd", 0) or 0),
        "current_market_exposure_usd": current_market_exposure,
        "projected_market_exposure_usd": projected_market_exposure,
        "max_market_exposure_usd": float(config.get("max_market_exposure_usd", 0) or 0),
        "max_single_action_notional_usd": float(config.get("max_single_action_notional_usd", 0) or 0),
        "market_allowlist_non_empty": bool(allowlist),
        "market_allowlisted": not allowlist or market_id in allowlist,
        "market_denylisted": market_id in denylist,
        "require_fresh_evidence": config.get("require_fresh_evidence") is True,
        "block_on_source_gap": config.get("block_on_source_gap") is True,
        "manual_approval_required": config.get("manual_approval_required") is True,
        "kill_switch_enabled": config.get("kill_switch_enabled") is True,
    }
    audit_id = _audit_id(normalized_input, config, decision, reason_codes)
    return {
        "contract_version": RISK_DECISION_CONTRACT,
        "risk_decision_id": _risk_decision_id(audit_id),
        "decision_input": normalized_input,
        "decision": decision,
        "reason_codes": reason_codes,
        "human_readable_summary": _decision_summary(decision, market_id, reason_codes),
        "limit_snapshot": limit_snapshot,
        "audit_id": audit_id,
        "created_at": clean_text(created_at),
        "paper_only": True,
        "live_prep_only": True,
        "paper_live_prep_only": True,
        "passive_reporting_only": True,
        "applied_to_paper_execution": False,
        "applied_to_real_execution": False,
        "real_order_allowed": False,
        "real_order_submitted": False,
        "wallet_required": False,
        "wallet_used": False,
        "private_key_used": False,
        "signing_used": False,
        "trading_endpoint_required": False,
        "trading_endpoint_used": False,
        "authenticated_endpoint_used": False,
        "autonomous_trading_enabled": False,
        "network_used": False,
        "external_api_calls_performed": False,
        "outcome_resolution_invented": False,
        "pnl_invented": False,
    }


def build_risk_decision_ledger(
    *,
    candidates_batch: Mapping[str, Any] | None = None,
    risk_config: Mapping[str, Any] | None = None,
    source_evidence_refresh_ledger: Mapping[str, Any] | None = None,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    candidates = dict(candidates_batch or build_paper_trade_intent_candidates(generated_at=generated_at))
    config = dict(risk_config or build_default_risk_engine_config(generated_at=generated_at))
    run_id = clean_text(candidates.get("daily_run_id") or candidates.get("run_id"))
    run_date = clean_text(candidates.get("run_date") or generated_at[:10])
    source_by_market = _source_status_by_market(source_evidence_refresh_ledger or {})
    market_exposure: dict[str, float] = {}
    total_exposure = 0.0
    decisions = []

    for candidate in mapping_rows(candidates.get("candidates")):
        market_id = clean_text(candidate.get("market_id"))
        requested_notional = float(candidate.get("intended_notional_usd", 0) or 0)
        source_status = source_by_market.get(market_id, {})
        decision_input = build_risk_decision_input(
            run_id=run_id,
            market_id=market_id,
            intent_id=clean_text(candidate.get("intent_id")),
            hypothesis_id=clean_text(candidate.get("hypothesis_id")),
            action_type=_risk_action_type(candidate),
            requested_notional_usd=requested_notional,
            current_total_exposure_usd=total_exposure,
            current_market_exposure_usd=market_exposure.get(market_id, 0.0),
            evidence_freshness_status=_evidence_freshness_status(source_status),
            source_gap_status=_source_gap_status(source_status),
            operator_approval_status=_operator_approval_status(candidate, config),
            config_version=clean_text(config.get("config_version") or RISK_ENGINE_CONFIG_VERSION),
        )
        decision = evaluate_risk_decision(decision_input, config, created_at=generated_at)
        decisions.append(decision)
        if decision["decision"] == DECISION_ALLOWED and requested_notional > 0:
            market_exposure[market_id] = round(market_exposure.get(market_id, 0.0) + requested_notional, 2)
            total_exposure = round(total_exposure + requested_notional, 2)

    decision_counts = {
        DECISION_ALLOWED: len([row for row in decisions if row["decision"] == DECISION_ALLOWED]),
        DECISION_BLOCKED: len([row for row in decisions if row["decision"] == DECISION_BLOCKED]),
        DECISION_NEEDS_MANUAL_APPROVAL: len(
            [row for row in decisions if row["decision"] == DECISION_NEEDS_MANUAL_APPROVAL]
        ),
    }
    reason_summary = _reason_code_summary(decisions)
    ledger = {
        "contract_version": RISK_DECISION_LEDGER_CONTRACT,
        "ledger_id": f"risk-engine-decision-ledger-026-{run_date}",
        "generated_at": generated_at,
        "run_id": run_id,
        "run_date": run_date,
        "config_id": clean_text(config.get("config_id")),
        "config_version": clean_text(config.get("config_version") or RISK_ENGINE_CONFIG_VERSION),
        "decision_count": len(decisions),
        "allowed_count": decision_counts[DECISION_ALLOWED],
        "blocked_count": decision_counts[DECISION_BLOCKED],
        "needs_manual_approval_count": decision_counts[DECISION_NEEDS_MANUAL_APPROVAL],
        "decision_counts": decision_counts,
        "reason_code_summary": reason_summary,
        "unresolved_evidence_gap_awareness": _unresolved_evidence_gap_awareness(
            candidates,
            decisions,
            source_evidence_refresh_ledger or {},
        ),
        "decisions": decisions,
        "paper_only": True,
        "live_prep_only": True,
        "paper_live_prep_only": True,
        "passive_reporting_only": True,
        "applied_to_paper_execution": False,
        "applied_to_real_execution": False,
        "risk_recommendations_generated": False,
        "outcome_resolution_invented": False,
        "pnl_invented": False,
        "network_used": False,
        "external_api_calls_performed": False,
        "safety_summary": trading_core_safety_summary(),
    }
    return ledger


def write_risk_decision_ledger(
    *,
    candidates_batch: Mapping[str, Any] | None = None,
    risk_config: Mapping[str, Any] | None = None,
    source_evidence_refresh_ledger: Mapping[str, Any] | None = None,
    out_json_path: str | Path = ARTIFACT_DIR / "risk_engine_decision_ledger.json",
    out_md_path: str | Path = ARTIFACT_DIR / "risk_engine_decision_ledger.md",
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    ledger = build_risk_decision_ledger(
        candidates_batch=candidates_batch,
        risk_config=risk_config,
        source_evidence_refresh_ledger=source_evidence_refresh_ledger,
        generated_at=generated_at,
    )
    write_json(out_json_path, ledger)
    write_text(out_md_path, render_risk_decision_ledger_markdown(ledger))
    return ledger


def render_risk_decision_ledger_markdown(ledger: Mapping[str, Any]) -> str:
    awareness = dict(ledger.get("unresolved_evidence_gap_awareness", {}))
    lines = [
        "# PMBOT Risk Engine Decision Ledger",
        "",
        "- Passive paper/live-prep risk decisions only; no execution layer is connected.",
        f"- Decisions: {ledger.get('decision_count')}",
        f"- Allowed: {ledger.get('allowed_count')}",
        f"- Blocked: {ledger.get('blocked_count')}",
        f"- Needs manual approval: {ledger.get('needs_manual_approval_count')}",
        f"- Unresolved outcome markers: {awareness.get('outcome_unresolved_candidate_count')}",
        f"- Markets with source gaps: {awareness.get('markets_with_source_gaps')}",
        f"- Stale or missing evidence decisions: {awareness.get('stale_or_missing_evidence_decision_count')}",
        "- No paper PnL, resolved outcome, wallet, signing, order, authenticated endpoint, or live action is produced.",
        "",
        "## Reason Codes",
        "",
        *bullet_lines(f"{key}: `{value}`" for key, value in dict(ledger.get("reason_code_summary", {})).items()),
        "",
        "## Decisions",
        "",
    ]
    for decision in mapping_rows(ledger.get("decisions")):
        decision_input = dict(decision.get("decision_input", {}))
        limit_snapshot = dict(decision.get("limit_snapshot", {}))
        lines.extend(
            [
                f"### `{decision_input.get('market_id')}`",
                "",
                f"- Risk decision: `{decision.get('risk_decision_id')}`",
                f"- Audit: `{decision.get('audit_id')}`",
                f"- Intent: `{decision_input.get('intent_id')}`",
                f"- Decision: `{decision.get('decision')}`",
                f"- Requested notional: `${limit_snapshot.get('requested_notional_usd')}`",
                "- Reason codes:",
                *bullet_lines(str(item) for item in decision.get("reason_codes", [])),
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def load_and_write_risk_decision_ledger(
    *,
    candidates_path: str | Path = ARTIFACT_DIR / "paper_trade_intent_candidates.json",
    risk_config_path: str | Path = ARTIFACT_DIR / "future_risk_engine_config.json",
    source_evidence_refresh_path: str | Path | None = None,
    out_json_path: str | Path = ARTIFACT_DIR / "risk_engine_decision_ledger.json",
    out_md_path: str | Path = ARTIFACT_DIR / "risk_engine_decision_ledger.md",
) -> dict[str, Any]:
    candidates = load_json_object(candidates_path, label="intent candidates")
    config = load_json_object(risk_config_path, label="risk engine config")
    source = (
        load_json_object(source_evidence_refresh_path, label="source evidence refresh")
        if source_evidence_refresh_path is not None and Path(source_evidence_refresh_path).exists()
        else {}
    )
    return write_risk_decision_ledger(
        candidates_batch=candidates,
        risk_config=config,
        source_evidence_refresh_ledger=source,
        out_json_path=out_json_path,
        out_md_path=out_md_path,
    )


def _validate_risk_decision_input(decision_input: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if decision_input.get("contract_version") != RISK_DECISION_INPUT_CONTRACT:
        errors.append(f"contract_version must be {RISK_DECISION_INPUT_CONTRACT}")
    for field in (
        "run_id",
        "market_id",
        "action_type",
        "evidence_freshness_status",
        "source_gap_status",
        "operator_approval_status",
        "config_version",
    ):
        if not clean_text(decision_input.get(field)):
            errors.append(f"{field} must be a non-empty string")
    action_type = clean_text(decision_input.get("action_type")).lower()
    if action_type and "simulated" not in action_type and "proposed" not in action_type:
        errors.append("action_type must be explicitly simulated or proposed")
    for field in (
        "requested_notional_usd",
        "current_total_exposure_usd",
        "current_market_exposure_usd",
    ):
        value = decision_input.get(field)
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            errors.append(f"{field} must be numeric")
        elif value < 0:
            errors.append(f"{field} must be >= 0")
    return errors


def _normalized_decision_input(decision_input: Mapping[str, Any], config: Mapping[str, Any]) -> dict[str, Any]:
    value = dict(decision_input)
    value["config_version"] = clean_text(value.get("config_version") or config.get("config_version"))
    for field in (
        "requested_notional_usd",
        "current_total_exposure_usd",
        "current_market_exposure_usd",
    ):
        value[field] = round(float(value.get(field, 0) or 0), 2)
    return value


def _append_reason(reasons: list[str], reason: str) -> None:
    if reason not in reasons:
        reasons.append(reason)


def _audit_id(
    decision_input: Mapping[str, Any],
    risk_config: Mapping[str, Any],
    decision: str,
    reason_codes: Sequence[str],
) -> str:
    payload = {
        "decision_input": decision_input,
        "config_id": risk_config.get("config_id"),
        "config_version": risk_config.get("config_version"),
        "decision": decision,
        "reason_codes": list(reason_codes),
    }
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()
    return f"risk-audit-v1-{digest[:16]}"


def _risk_decision_id(audit_id: str) -> str:
    suffix = clean_text(audit_id).removeprefix("risk-audit-v1-")
    return f"risk-decision-v1-{suffix}"


def _decision_summary(decision: str, market_id: str, reason_codes: Sequence[str]) -> str:
    if decision == DECISION_ALLOWED:
        return f"Risk engine allowed the simulated/proposed action for market {market_id} under the configured limits."
    if decision == DECISION_NEEDS_MANUAL_APPROVAL:
        return (
            f"Risk engine requires manual approval for the simulated/proposed action for market {market_id}; "
            f"reason codes: {', '.join(reason_codes)}."
        )
    return (
        f"Risk engine blocked the simulated/proposed action for market {market_id}; "
        f"reason codes: {', '.join(reason_codes)}."
    )


def _source_status_by_market(source_evidence_refresh_ledger: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    quality = dict(source_evidence_refresh_ledger.get("quality_ledger", {}))
    return {
        clean_text(row.get("market_id")): row
        for row in mapping_rows(quality.get("market_source_status"))
        if clean_text(row.get("market_id"))
    }


def _evidence_freshness_status(source_status: Mapping[str, Any]) -> str:
    if not source_status:
        return "missing"
    if int(source_status.get("missing_source_reference_count", 0) or 0) > 0:
        return "missing"
    if int(source_status.get("missing_local_capture_count", 0) or 0) > 0:
        return "missing"
    if int(source_status.get("stale_count", 0) or 0) > 0:
        return "stale"
    if int(source_status.get("unknown_freshness_count", 0) or 0) > 0:
        return "unknown"
    if int(source_status.get("fresh_count", 0) or 0) > 0:
        return "fresh"
    return "missing"


def _source_gap_status(source_status: Mapping[str, Any]) -> str:
    if not source_status:
        return "gaps_present"
    return clean_text(source_status.get("gap_status") or "gaps_present")


def _operator_approval_status(candidate: Mapping[str, Any], config: Mapping[str, Any]) -> str:
    explicit = clean_text(candidate.get("operator_approval_status"))
    if explicit:
        return explicit
    if config.get("manual_approval_required") is True or candidate.get("operator_review_required") is True:
        return "pending"
    return "not_required"


def _risk_action_type(candidate: Mapping[str, Any]) -> str:
    action_type = clean_text(candidate.get("paper_action_type"))
    if action_type == "observe_only":
        return "simulated_observe_only"
    if action_type.startswith("simulated_"):
        return action_type
    if action_type:
        return f"simulated_{action_type}"
    return "simulated_unknown"


def _reason_code_summary(decisions: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for decision in decisions:
        for reason in decision.get("reason_codes", []):
            reason_text = clean_text(reason)
            if reason_text:
                counts[reason_text] = counts.get(reason_text, 0) + 1
    return {key: counts[key] for key in sorted(counts)}


def _unresolved_evidence_gap_awareness(
    candidates: Mapping[str, Any],
    decisions: Sequence[Mapping[str, Any]],
    source_evidence_refresh_ledger: Mapping[str, Any],
) -> dict[str, Any]:
    source_counts = dict(source_evidence_refresh_ledger.get("summary_counts", {}))
    return {
        "outcome_unresolved_candidate_count": len(
            [
                row
                for row in mapping_rows(candidates.get("candidates"))
                if "outcome_unresolved" in row.get("missing_evidence", [])
            ]
        ),
        "markets_with_source_gaps": int(
            dict(source_evidence_refresh_ledger.get("quality_ledger", {}))
            .get("summary_counts", {})
            .get("markets_with_gaps", 0)
            or 0
        ),
        "missing_source_reference_records": int(source_counts.get("missing_source_reference_records", 0) or 0),
        "missing_local_capture_records": int(source_counts.get("missing_local_capture_records", 0) or 0),
        "stale_records": int(source_counts.get("stale_records", 0) or 0),
        "unknown_freshness_records": int(source_counts.get("unknown_freshness_records", 0) or 0),
        "stale_or_missing_evidence_decision_count": len(
            [
                row
                for row in decisions
                if clean_text(row.get("decision_input", {}).get("evidence_freshness_status")).lower()
                not in FRESH_EVIDENCE_STATUSES
            ]
        ),
        "outcome_resolution_invented": False,
        "pnl_invented": False,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Write PMBOT passive risk engine decision ledger artifacts.")
    parser.add_argument("--candidates", default=str(ARTIFACT_DIR / "paper_trade_intent_candidates.json"))
    parser.add_argument("--risk-config", default=str(ARTIFACT_DIR / "future_risk_engine_config.json"))
    parser.add_argument("--source-evidence-refresh", default=None)
    parser.add_argument("--out-json", default=str(ARTIFACT_DIR / "risk_engine_decision_ledger.json"))
    parser.add_argument("--out-md", default=str(ARTIFACT_DIR / "risk_engine_decision_ledger.md"))
    args = parser.parse_args(argv)
    load_and_write_risk_decision_ledger(
        candidates_path=args.candidates,
        risk_config_path=args.risk_config,
        source_evidence_refresh_path=args.source_evidence_refresh,
        out_json_path=args.out_json,
        out_md_path=args.out_md,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
