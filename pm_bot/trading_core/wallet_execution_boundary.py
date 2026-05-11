from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from pm_bot.trading_core.risk_engine import (
    APPROVED_OPERATOR_STATUSES,
    DECISION_ALLOWED,
    DECISION_BLOCKED,
    DECISION_NEEDS_MANUAL_APPROVAL,
    FRESH_EVIDENCE_STATUSES,
    SOURCE_GAP_FREE_STATUSES,
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

WALLET_BOUNDARY_CONTRACT = "pmbot_wallet_execution_boundary_design_simulation_only.v1"
RISK_APPROVED_ACTION_PACKET_CONTRACT = "pmbot_wallet_boundary_risk_approved_action_packet.v1"
EXECUTION_REQUEST_PACKET_CONTRACT = "pmbot_wallet_boundary_execution_request_packet.v1"
EXECUTION_REQUEST_VALIDATION_CONTRACT = "pmbot_wallet_boundary_execution_request_validation.v1"
WALLET_BOUNDARY_AUDIT_LEDGER_CONTRACT = "pmbot_wallet_boundary_audit_ledger.v1"

STATUS_DRAFT = "draft"
STATUS_BLOCKED = "blocked"
STATUS_NEEDS_MANUAL_APPROVAL = "needs_manual_approval"
STATUS_APPROVED_FOR_FUTURE_SIMULATION = "approved_for_future_simulation"
ALLOWED_EXECUTION_REQUEST_STATUSES = {
    STATUS_DRAFT,
    STATUS_BLOCKED,
    STATUS_NEEDS_MANUAL_APPROVAL,
    STATUS_APPROVED_FOR_FUTURE_SIMULATION,
}

REQUIRED_EXPOSURE_LIMIT_FIELDS = (
    "requested_notional_usd",
    "current_total_exposure_usd",
    "projected_total_exposure_usd",
    "max_total_exposure_usd",
    "current_market_exposure_usd",
    "projected_market_exposure_usd",
    "max_market_exposure_usd",
    "max_single_action_notional_usd",
)

FORBIDDEN_EXECUTION_REQUEST_FIELD_NAMES = {
    "api_key",
    "api_token",
    "authenticated_endpoint",
    "authenticated_endpoint_url",
    "bearer_token",
    "credential",
    "credentials",
    "endpoint_url",
    "order_endpoint",
    "order_endpoint_url",
    "order_payload",
    "placement_payload",
    "private_key",
    "secret",
    "signature",
    "signed_payload",
    "wallet_private_key",
    "wallet_secret",
}

SAFETY_ASSERTION = "no signing / no wallet / no order placement"


def build_wallet_boundary_contract(*, generated_at: str = GENERATED_AT) -> dict[str, Any]:
    return {
        "contract_version": WALLET_BOUNDARY_CONTRACT,
        "boundary_id": "wallet-execution-boundary-design-simulation-only-027",
        "boundary_name": "PMBOT wallet/execution boundary design simulation-only contract",
        "boundary_scope": "design_simulation_only",
        "generated_at": generated_at,
        "required_input_packet": RISK_APPROVED_ACTION_PACKET_CONTRACT,
        "execution_request_packet_contract": EXECUTION_REQUEST_PACKET_CONTRACT,
        "allowed_execution_request_statuses": sorted(ALLOWED_EXECUTION_REQUEST_STATUSES),
        "required_risk_action_packet_fields": [
            "risk_decision_id",
            "audit_id",
            "risk_decision",
            "kill_switch_status",
            "manual_approval_status",
            "evidence_freshness_status",
            "source_gap_status",
            "market_id",
            "proposed_notional_usd",
            "risk_snapshot",
            "paper_only",
            "live_prep_only",
        ],
        "required_risk_snapshot_exposure_fields": list(REQUIRED_EXPOSURE_LIMIT_FIELDS),
        "forbidden_execution_request_field_names": sorted(FORBIDDEN_EXECUTION_REQUEST_FIELD_NAMES),
        "risk_engine_v1_required": True,
        "kill_switch_status_required": True,
        "kill_switch_must_be_disabled": True,
        "manual_approval_status_required": True,
        "evidence_freshness_status_required": True,
        "source_gap_status_required": True,
        "paper_only": True,
        "live_prep_only": True,
        "simulation_only": True,
        "passive_artifact_only": True,
        "execution_enabled": False,
        "live_execution_enabled": False,
        "real_order_allowed": False,
        "real_order_submitted": False,
        "authenticated_endpoint_used": False,
        "external_api_calls_performed": False,
        "network_used": False,
        "safety_assertion": SAFETY_ASSERTION,
    }


def build_risk_approved_action_packet(
    *,
    candidate: Mapping[str, Any],
    risk_decision: Mapping[str, Any],
    risk_config: Mapping[str, Any],
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    decision_input = dict(risk_decision.get("decision_input", {}))
    limit_snapshot = dict(risk_decision.get("limit_snapshot", {}))
    market_id = clean_text(decision_input.get("market_id") or candidate.get("market_id"))
    proposed_notional = _number(
        decision_input.get("requested_notional_usd"),
        fallback=candidate.get("intended_notional_usd"),
    )
    audit_id = clean_text(risk_decision.get("audit_id"))
    risk_decision_id = clean_text(risk_decision.get("risk_decision_id"))
    action_packet = {
        "contract_version": RISK_APPROVED_ACTION_PACKET_CONTRACT,
        "action_packet_id": _stable_id(
            "wallet-boundary-action-packet-027",
            {
                "audit_id": audit_id,
                "risk_decision_id": risk_decision_id,
                "market_id": market_id,
                "proposed_notional_usd": proposed_notional,
            },
        ),
        "generated_at": generated_at,
        "run_id": clean_text(decision_input.get("run_id") or candidate.get("daily_run_id") or candidate.get("run_id")),
        "intent_id": clean_text(decision_input.get("intent_id") or candidate.get("intent_id")),
        "market_id": market_id,
        "proposed_notional_usd": proposed_notional,
        "risk_decision_id": risk_decision_id,
        "audit_id": audit_id,
        "risk_decision": clean_text(risk_decision.get("decision")),
        "risk_reason_codes": [clean_text(item) for item in risk_decision.get("reason_codes", [])],
        "kill_switch_status": "enabled" if risk_config.get("kill_switch_enabled") is True else "disabled",
        "manual_approval_status": clean_text(decision_input.get("operator_approval_status")),
        "manual_approval_required": limit_snapshot.get("manual_approval_required") is True
        or risk_config.get("manual_approval_required") is True,
        "evidence_freshness_status": clean_text(decision_input.get("evidence_freshness_status")),
        "source_gap_status": clean_text(decision_input.get("source_gap_status")),
        "risk_snapshot": _risk_snapshot(limit_snapshot),
        "paper_only": True,
        "live_prep_only": True,
        "simulation_only": True,
        "passive_artifact_only": True,
        "execution_enabled": False,
        "live_execution_enabled": False,
    }
    return action_packet


def build_execution_request_packet(
    *,
    risk_approved_action_packet: Mapping[str, Any],
    boundary_contract: Mapping[str, Any] | None = None,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    contract = dict(boundary_contract or build_wallet_boundary_contract(generated_at=generated_at))
    packet = {
        "contract_version": EXECUTION_REQUEST_PACKET_CONTRACT,
        "packet_id": _stable_id(
            "wallet-boundary-execution-request-027",
            {
                "action_packet_id": risk_approved_action_packet.get("action_packet_id"),
                "risk_decision_id": risk_approved_action_packet.get("risk_decision_id"),
                "audit_id": risk_approved_action_packet.get("audit_id"),
                "market_id": risk_approved_action_packet.get("market_id"),
                "proposed_notional_usd": risk_approved_action_packet.get("proposed_notional_usd"),
            },
        ),
        "generated_at": generated_at,
        "packet_status": STATUS_DRAFT,
        "boundary_contract_version": contract.get("contract_version"),
        "requested_boundary_action": "future_simulation_review_only",
        "risk_approved_action_packet": dict(risk_approved_action_packet),
        "paper_only": True,
        "live_prep_only": True,
        "simulation_only": True,
        "passive_artifact_only": True,
        "execution_enabled": False,
        "live_execution_enabled": False,
    }
    validation = validate_execution_request_packet(packet, boundary_contract=contract, generated_at=generated_at)
    packet["packet_status"] = validation["status"]
    packet["validation"] = validation
    return packet


def validate_execution_request_packet(
    packet: Mapping[str, Any],
    *,
    boundary_contract: Mapping[str, Any] | None = None,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    contract = dict(boundary_contract or build_wallet_boundary_contract(generated_at=generated_at))
    blocking_reasons: list[str] = []
    manual_reasons: list[str] = []

    _require_equal(packet, "contract_version", EXECUTION_REQUEST_PACKET_CONTRACT, blocking_reasons)
    _require_nonempty(packet, "packet_id", blocking_reasons)
    if packet.get("packet_status") not in ALLOWED_EXECUTION_REQUEST_STATUSES:
        _append_reason(blocking_reasons, "PACKET_STATUS_NOT_ALLOWED")
    for field in ("paper_only", "live_prep_only", "simulation_only", "passive_artifact_only"):
        if packet.get(field) is not True:
            _append_reason(blocking_reasons, f"{field.upper()}_FLAG_REQUIRED")
    for field in ("execution_enabled", "live_execution_enabled"):
        if packet.get(field) is not False:
            _append_reason(blocking_reasons, f"{field.upper()}_MUST_BE_FALSE")

    forbidden_paths = _find_forbidden_packet_fields(packet)
    if forbidden_paths:
        _append_reason(blocking_reasons, "FORBIDDEN_EXECUTION_REQUEST_FIELD_PRESENT")

    action_packet = packet.get("risk_approved_action_packet")
    if not isinstance(action_packet, Mapping):
        _append_reason(blocking_reasons, "MISSING_RISK_APPROVED_ACTION_PACKET")
        action_packet = {}

    _validate_action_packet_schema(action_packet, blocking_reasons)
    _validate_risk_gate(action_packet, blocking_reasons)
    _validate_kill_switch(action_packet, blocking_reasons)
    _validate_evidence_and_source(action_packet, blocking_reasons)
    _validate_exposure_snapshot(action_packet, blocking_reasons)
    _validate_manual_approval(action_packet, blocking_reasons, manual_reasons)

    reason_codes = _dedupe([*blocking_reasons, *manual_reasons])
    if blocking_reasons:
        status = STATUS_BLOCKED
    elif manual_reasons:
        status = STATUS_NEEDS_MANUAL_APPROVAL
    else:
        status = STATUS_APPROVED_FOR_FUTURE_SIMULATION
    return {
        "contract_version": EXECUTION_REQUEST_VALIDATION_CONTRACT,
        "packet_id": clean_text(packet.get("packet_id")),
        "status": status,
        "reason_codes": reason_codes,
        "forbidden_field_paths": forbidden_paths,
        "gate_results": {
            "risk_decision_present": bool(clean_text(action_packet.get("risk_decision_id"))),
            "audit_id_present": bool(clean_text(action_packet.get("audit_id"))),
            "risk_engine_allows_or_requires_manual_approval": clean_text(action_packet.get("risk_decision"))
            in {DECISION_ALLOWED, DECISION_NEEDS_MANUAL_APPROVAL},
            "kill_switch_disabled": clean_text(action_packet.get("kill_switch_status")).lower() == "disabled",
            "manual_approval_present_when_required": not manual_reasons,
            "evidence_requirements_satisfied": not any(
                reason in reason_codes for reason in ("EVIDENCE_FRESHNESS_STATUS_MISSING", "EVIDENCE_NOT_FRESH")
            ),
            "source_requirements_satisfied": not any(
                reason in reason_codes for reason in ("SOURCE_GAP_STATUS_MISSING", "SOURCE_GAP_PRESENT")
            ),
            "exposure_limits_present": not any(
                reason.startswith("EXPOSURE_LIMIT_") or reason == "RISK_SNAPSHOT_MISSING" for reason in reason_codes
            ),
        },
        "boundary_contract_version": contract.get("contract_version"),
        "paper_only": True,
        "live_prep_only": True,
        "simulation_only": True,
        "passive_artifact_only": True,
        "execution_enabled": False,
        "live_execution_enabled": False,
        "real_order_allowed": False,
        "real_order_submitted": False,
        "authenticated_endpoint_used": False,
        "external_api_calls_performed": False,
        "network_used": False,
    }


def build_wallet_boundary_audit_ledger(
    *,
    candidates_batch: Mapping[str, Any],
    risk_decision_ledger: Mapping[str, Any],
    risk_config: Mapping[str, Any],
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    decisions_by_intent = _risk_decisions_by_intent(risk_decision_ledger)
    boundary_contract = build_wallet_boundary_contract(generated_at=generated_at)
    packets: list[dict[str, Any]] = []
    for candidate in mapping_rows(candidates_batch.get("candidates")):
        intent_id = clean_text(candidate.get("intent_id"))
        decision = decisions_by_intent.get(intent_id, {})
        action_packet = build_risk_approved_action_packet(
            candidate=candidate,
            risk_decision=decision,
            risk_config=risk_config,
            generated_at=generated_at,
        )
        packets.append(
            build_execution_request_packet(
                risk_approved_action_packet=action_packet,
                boundary_contract=boundary_contract,
                generated_at=generated_at,
            )
        )

    reason_summary = _reason_code_summary(packets)
    status_counts = _status_counts(packets)
    run_date = clean_text(candidates_batch.get("run_date") or generated_at[:10])
    return {
        "contract_version": WALLET_BOUNDARY_AUDIT_LEDGER_CONTRACT,
        "ledger_id": f"wallet-boundary-audit-ledger-027-{run_date}",
        "generated_at": generated_at,
        "run_id": clean_text(candidates_batch.get("daily_run_id") or candidates_batch.get("run_id")),
        "run_date": run_date,
        "boundary_contract": boundary_contract,
        "execution_request_packets": packets,
        "packet_count": len(packets),
        "boundary_packets_created": len(packets),
        "blocked_packet_count": status_counts[STATUS_BLOCKED],
        "needs_manual_approval_count": status_counts[STATUS_NEEDS_MANUAL_APPROVAL],
        "approved_for_future_simulation_count": status_counts[STATUS_APPROVED_FOR_FUTURE_SIMULATION],
        "draft_packet_count": status_counts[STATUS_DRAFT],
        "missing_approval_count": reason_summary.get("MANUAL_APPROVAL_REQUIRED", 0),
        "missing_risk_decision_count": reason_summary.get("MISSING_RISK_DECISION_ID", 0)
        + reason_summary.get("MISSING_RISK_AUDIT_ID", 0),
        "kill_switch_block_count": reason_summary.get("KILL_SWITCH_ENABLED", 0),
        "reason_code_summary": reason_summary,
        "safety_assertion": SAFETY_ASSERTION,
        "future_next_step_notes": [
            "Build a signing simulator only as a separate fixture after explicit operator approval.",
            "Keep the simulator disconnected from wallet material and external endpoints.",
            "Add reconciliation and dual-control review before any separate live execution proposal.",
        ],
        "paper_only": True,
        "live_prep_only": True,
        "simulation_only": True,
        "passive_artifact_only": True,
        "applied_to_paper_execution": False,
        "applied_to_real_execution": False,
        "execution_enabled": False,
        "live_execution_enabled": False,
        "real_order_allowed": False,
        "real_order_submitted": False,
        "wallet_required": False,
        "wallet_used": False,
        "private_key_used": False,
        "signing_used": False,
        "trading_endpoint_required": False,
        "trading_endpoint_used": False,
        "authenticated_endpoint_used": False,
        "external_api_calls_performed": False,
        "network_used": False,
        "outcome_resolution_invented": False,
        "pnl_invented": False,
        "safety_summary": trading_core_safety_summary(),
    }


def write_wallet_boundary_audit_ledger(
    *,
    candidates_batch: Mapping[str, Any],
    risk_decision_ledger: Mapping[str, Any],
    risk_config: Mapping[str, Any],
    out_json_path: str | Path = ARTIFACT_DIR / "wallet_boundary_audit_ledger.json",
    out_md_path: str | Path = ARTIFACT_DIR / "wallet_boundary_audit_ledger.md",
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    ledger = build_wallet_boundary_audit_ledger(
        candidates_batch=candidates_batch,
        risk_decision_ledger=risk_decision_ledger,
        risk_config=risk_config,
        generated_at=generated_at,
    )
    write_json(out_json_path, ledger)
    write_text(out_md_path, render_wallet_boundary_audit_ledger_markdown(ledger))
    return ledger


def render_wallet_boundary_audit_ledger_markdown(ledger: Mapping[str, Any]) -> str:
    lines = [
        "# PMBOT Wallet Boundary Audit Ledger",
        "",
        "- Boundary/design/simulation-only artifact.",
        f"- Safety assertion: {ledger.get('safety_assertion')}",
        f"- Boundary packets created: {ledger.get('boundary_packets_created')}",
        f"- Blocked packets: {ledger.get('blocked_packet_count')}",
        f"- Needs manual approval: {ledger.get('needs_manual_approval_count')}",
        f"- Approved for future simulation: {ledger.get('approved_for_future_simulation_count')}",
        f"- Missing approval: {ledger.get('missing_approval_count')}",
        f"- Missing risk decision: {ledger.get('missing_risk_decision_count')}",
        f"- Kill switch blocks: {ledger.get('kill_switch_block_count')}",
        "",
        "## Reason Code Summary",
        "",
        *bullet_lines(f"{key}: `{value}`" for key, value in dict(ledger.get("reason_code_summary", {})).items()),
        "",
        "## Packets",
        "",
    ]
    for packet in mapping_rows(ledger.get("execution_request_packets")):
        action_packet = dict(packet.get("risk_approved_action_packet", {}))
        validation = dict(packet.get("validation", {}))
        lines.extend(
            [
                f"- `{packet.get('packet_id')}` `{packet.get('packet_status')}` "
                f"market `{action_packet.get('market_id')}` notional `${action_packet.get('proposed_notional_usd')}`",
                f"  - Risk decision: `{action_packet.get('risk_decision')}`",
                f"  - Risk decision ID: `{action_packet.get('risk_decision_id')}`",
                f"  - Audit ID: `{action_packet.get('audit_id')}`",
                f"  - Reason codes: `{', '.join(validation.get('reason_codes', []))}`",
            ]
        )
    lines.extend(
        [
            "",
            "## Future Next-Step Notes",
            "",
            *bullet_lines(str(item) for item in ledger.get("future_next_step_notes", [])),
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def load_and_write_wallet_boundary_audit_ledger(
    *,
    candidates_path: str | Path = ARTIFACT_DIR / "paper_trade_intent_candidates.json",
    risk_decision_ledger_path: str | Path = ARTIFACT_DIR / "risk_engine_decision_ledger.json",
    risk_config_path: str | Path = ARTIFACT_DIR / "future_risk_engine_config.json",
    out_json_path: str | Path = ARTIFACT_DIR / "wallet_boundary_audit_ledger.json",
    out_md_path: str | Path = ARTIFACT_DIR / "wallet_boundary_audit_ledger.md",
) -> dict[str, Any]:
    return write_wallet_boundary_audit_ledger(
        candidates_batch=load_json_object(candidates_path, label="intent candidates"),
        risk_decision_ledger=load_json_object(risk_decision_ledger_path, label="risk decision ledger"),
        risk_config=load_json_object(risk_config_path, label="risk config"),
        out_json_path=out_json_path,
        out_md_path=out_md_path,
    )


def _validate_action_packet_schema(action_packet: Mapping[str, Any], blocking_reasons: list[str]) -> None:
    _require_equal(action_packet, "contract_version", RISK_APPROVED_ACTION_PACKET_CONTRACT, blocking_reasons)
    for field, reason in (
        ("risk_decision_id", "MISSING_RISK_DECISION_ID"),
        ("audit_id", "MISSING_RISK_AUDIT_ID"),
        ("market_id", "MISSING_MARKET_ID"),
        ("evidence_freshness_status", "EVIDENCE_FRESHNESS_STATUS_MISSING"),
        ("source_gap_status", "SOURCE_GAP_STATUS_MISSING"),
    ):
        if not clean_text(action_packet.get(field)):
            _append_reason(blocking_reasons, reason)
    if not isinstance(action_packet.get("proposed_notional_usd"), (int, float)) or isinstance(
        action_packet.get("proposed_notional_usd"),
        bool,
    ):
        _append_reason(blocking_reasons, "MISSING_PROPOSED_NOTIONAL")
    elif float(action_packet.get("proposed_notional_usd", 0)) < 0:
        _append_reason(blocking_reasons, "PROPOSED_NOTIONAL_NEGATIVE")
    for field in ("paper_only", "live_prep_only", "simulation_only", "passive_artifact_only"):
        if action_packet.get(field) is not True:
            _append_reason(blocking_reasons, f"ACTION_PACKET_{field.upper()}_FLAG_REQUIRED")
    for field in ("execution_enabled", "live_execution_enabled"):
        if action_packet.get(field) is not False:
            _append_reason(blocking_reasons, f"ACTION_PACKET_{field.upper()}_MUST_BE_FALSE")


def _validate_risk_gate(action_packet: Mapping[str, Any], blocking_reasons: list[str]) -> None:
    risk_decision = clean_text(action_packet.get("risk_decision"))
    snapshot = (
        dict(action_packet.get("risk_snapshot", {}))
        if isinstance(action_packet.get("risk_snapshot"), Mapping)
        else {}
    )
    if risk_decision == DECISION_BLOCKED:
        _append_reason(blocking_reasons, "RISK_ENGINE_DECISION_BLOCKED")
        return
    if risk_decision == DECISION_NEEDS_MANUAL_APPROVAL:
        if snapshot.get("manual_approval_required") is not True:
            _append_reason(blocking_reasons, "RISK_MANUAL_APPROVAL_DECISION_WITHOUT_CONFIG")
        return
    if risk_decision != DECISION_ALLOWED:
        _append_reason(blocking_reasons, "RISK_ENGINE_DECISION_MISSING_OR_UNKNOWN")


def _validate_kill_switch(action_packet: Mapping[str, Any], blocking_reasons: list[str]) -> None:
    status = clean_text(action_packet.get("kill_switch_status")).lower()
    if not status:
        _append_reason(blocking_reasons, "KILL_SWITCH_STATUS_MISSING")
    elif status != "disabled":
        _append_reason(blocking_reasons, "KILL_SWITCH_ENABLED")


def _validate_manual_approval(
    action_packet: Mapping[str, Any],
    blocking_reasons: list[str],
    manual_reasons: list[str],
) -> None:
    snapshot = (
        dict(action_packet.get("risk_snapshot", {}))
        if isinstance(action_packet.get("risk_snapshot"), Mapping)
        else {}
    )
    manual_required = (
        action_packet.get("manual_approval_required") is True
        or snapshot.get("manual_approval_required") is True
    )
    if not manual_required:
        return
    status = clean_text(action_packet.get("manual_approval_status")).lower()
    if not status:
        _append_reason(blocking_reasons, "MANUAL_APPROVAL_STATUS_MISSING")
    elif status not in APPROVED_OPERATOR_STATUSES:
        _append_reason(manual_reasons, "MANUAL_APPROVAL_REQUIRED")


def _validate_evidence_and_source(action_packet: Mapping[str, Any], blocking_reasons: list[str]) -> None:
    snapshot = (
        dict(action_packet.get("risk_snapshot", {}))
        if isinstance(action_packet.get("risk_snapshot"), Mapping)
        else {}
    )
    evidence_status = clean_text(action_packet.get("evidence_freshness_status")).lower()
    source_status = clean_text(action_packet.get("source_gap_status")).lower()
    if snapshot.get("require_fresh_evidence") is True and evidence_status not in FRESH_EVIDENCE_STATUSES:
        _append_reason(blocking_reasons, "EVIDENCE_NOT_FRESH")
    if snapshot.get("block_on_source_gap") is True and source_status not in SOURCE_GAP_FREE_STATUSES:
        _append_reason(blocking_reasons, "SOURCE_GAP_PRESENT")


def _validate_exposure_snapshot(action_packet: Mapping[str, Any], blocking_reasons: list[str]) -> None:
    snapshot = action_packet.get("risk_snapshot")
    if not isinstance(snapshot, Mapping):
        _append_reason(blocking_reasons, "RISK_SNAPSHOT_MISSING")
        return
    for field in REQUIRED_EXPOSURE_LIMIT_FIELDS:
        if field not in snapshot:
            _append_reason(blocking_reasons, f"EXPOSURE_LIMIT_FIELD_MISSING_{field.upper()}")
            continue
        value = snapshot.get(field)
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            _append_reason(blocking_reasons, f"EXPOSURE_LIMIT_FIELD_INVALID_{field.upper()}")


def _risk_snapshot(limit_snapshot: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "config_id": clean_text(limit_snapshot.get("config_id")),
        "config_version": clean_text(limit_snapshot.get("config_version")),
        "requested_notional_usd": _number(limit_snapshot.get("requested_notional_usd")),
        "current_total_exposure_usd": _number(limit_snapshot.get("current_total_exposure_usd")),
        "projected_total_exposure_usd": _number(limit_snapshot.get("projected_total_exposure_usd")),
        "max_total_exposure_usd": _number(limit_snapshot.get("max_total_exposure_usd")),
        "current_market_exposure_usd": _number(limit_snapshot.get("current_market_exposure_usd")),
        "projected_market_exposure_usd": _number(limit_snapshot.get("projected_market_exposure_usd")),
        "max_market_exposure_usd": _number(limit_snapshot.get("max_market_exposure_usd")),
        "max_single_action_notional_usd": _number(limit_snapshot.get("max_single_action_notional_usd")),
        "require_fresh_evidence": limit_snapshot.get("require_fresh_evidence") is True,
        "block_on_source_gap": limit_snapshot.get("block_on_source_gap") is True,
        "manual_approval_required": limit_snapshot.get("manual_approval_required") is True,
        "kill_switch_enabled": limit_snapshot.get("kill_switch_enabled") is True,
    }


def _risk_decisions_by_intent(risk_decision_ledger: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    return {
        clean_text(row.get("decision_input", {}).get("intent_id")): row
        for row in mapping_rows(risk_decision_ledger.get("decisions"))
        if clean_text(row.get("decision_input", {}).get("intent_id"))
    }


def _find_forbidden_packet_fields(value: Any, path: str = "$") -> list[str]:
    paths: list[str] = []
    if isinstance(value, Mapping):
        for key, nested in value.items():
            nested_path = f"{path}.{key}"
            if clean_text(key).lower() in FORBIDDEN_EXECUTION_REQUEST_FIELD_NAMES:
                paths.append(nested_path)
            paths.extend(_find_forbidden_packet_fields(nested, nested_path))
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            paths.extend(_find_forbidden_packet_fields(nested, f"{path}[{index}]"))
    return paths


def _status_counts(packets: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    return {
        status: len([packet for packet in packets if packet.get("packet_status") == status])
        for status in ALLOWED_EXECUTION_REQUEST_STATUSES
    }


def _reason_code_summary(packets: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for packet in packets:
        for reason in dict(packet.get("validation", {})).get("reason_codes", []):
            reason_text = clean_text(reason)
            if reason_text:
                counts[reason_text] = counts.get(reason_text, 0) + 1
    return {key: counts[key] for key in sorted(counts)}


def _require_equal(value: Mapping[str, Any], field: str, expected: Any, reasons: list[str]) -> None:
    if value.get(field) != expected:
        _append_reason(reasons, f"{field.upper()}_INVALID")


def _require_nonempty(value: Mapping[str, Any], field: str, reasons: list[str]) -> None:
    if not clean_text(value.get(field)):
        _append_reason(reasons, f"{field.upper()}_MISSING")


def _append_reason(reasons: list[str], reason: str) -> None:
    if reason not in reasons:
        reasons.append(reason)


def _dedupe(values: Sequence[str]) -> list[str]:
    result: list[str] = []
    for value in values:
        if value and value not in result:
            result.append(value)
    return result


def _number(value: Any, *, fallback: Any = 0.0) -> float:
    candidate = value if value is not None else fallback
    if isinstance(candidate, bool):
        return 0.0
    if isinstance(candidate, (int, float)):
        return round(float(candidate), 2)
    try:
        return round(float(candidate), 2)
    except (TypeError, ValueError):
        return 0.0


def _stable_id(prefix: str, payload: Mapping[str, Any]) -> str:
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()
    return f"{prefix}-{digest[:16]}"


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Write PMBOT wallet boundary design simulation-only artifacts.")
    parser.add_argument("--candidates", default=str(ARTIFACT_DIR / "paper_trade_intent_candidates.json"))
    parser.add_argument("--risk-decision-ledger", default=str(ARTIFACT_DIR / "risk_engine_decision_ledger.json"))
    parser.add_argument("--risk-config", default=str(ARTIFACT_DIR / "future_risk_engine_config.json"))
    parser.add_argument("--out-json", default=str(ARTIFACT_DIR / "wallet_boundary_audit_ledger.json"))
    parser.add_argument("--out-md", default=str(ARTIFACT_DIR / "wallet_boundary_audit_ledger.md"))
    args = parser.parse_args(argv)
    load_and_write_wallet_boundary_audit_ledger(
        candidates_path=args.candidates,
        risk_decision_ledger_path=args.risk_decision_ledger,
        risk_config_path=args.risk_config,
        out_json_path=args.out_json,
        out_md_path=args.out_md,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
