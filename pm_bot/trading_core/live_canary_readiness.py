from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from pm_bot.trading_core.risk_engine import DECISION_ALLOWED, FRESH_EVIDENCE_STATUSES, SOURCE_GAP_FREE_STATUSES
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
from pm_bot.trading_core.signing_simulator import STATUS_DRY_RUN_RECEIPT_READY
from pm_bot.trading_core.wallet_execution_boundary import STATUS_APPROVED_FOR_FUTURE_SIMULATION

LIVE_CANARY_READINESS_PACKET_CONTRACT = "pmbot_live_canary_readiness_packet.v1"
LIVE_CANARY_OPERATOR_APPROVAL_RECORD_CONTRACT = "pmbot_live_canary_dry_run_operator_approval_record.v1"
LIVE_CANARY_DRY_RUN_RECEIPT_CONTRACT = "pmbot_live_canary_dry_run_acceptance_receipt.v1"

CANARY_STATUS_DRAFT = "draft"
CANARY_STATUS_BLOCKED = "blocked"
CANARY_STATUS_NEEDS_OPERATOR_APPROVAL = "needs_operator_approval"
CANARY_STATUS_DRY_RUN_READY = "dry_run_ready"
CANARY_STATUS_REJECTED = "rejected"
ALLOWED_CANARY_STATUSES = {
    CANARY_STATUS_DRAFT,
    CANARY_STATUS_BLOCKED,
    CANARY_STATUS_NEEDS_OPERATOR_APPROVAL,
    CANARY_STATUS_DRY_RUN_READY,
    CANARY_STATUS_REJECTED,
}

APPROVAL_NOT_REQUESTED = "not_requested"
APPROVAL_REQUESTED = "requested"
APPROVAL_DRY_RUN_ONLY = "approved_for_dry_run_only"
APPROVAL_REJECTED = "rejected"
APPROVAL_EXPIRED = "expired"
ALLOWED_OPERATOR_APPROVAL_STATUSES = {
    APPROVAL_NOT_REQUESTED,
    APPROVAL_REQUESTED,
    APPROVAL_DRY_RUN_ONLY,
    APPROVAL_REJECTED,
    APPROVAL_EXPIRED,
}

DRY_RUN_ACCEPTANCE_ACCEPTED = "accepted_for_dry_run"
DRY_RUN_ACCEPTANCE_BLOCKED = "blocked"

FORBIDDEN_CANARY_FIELD_NAMES = {
    "api_key",
    "access_token",
    "auth_token",
    "auth_header",
    "bearer",
    "bearer_token",
    "clob_order",
    "client_secret",
    "mnemonic",
    "order_payload",
    "private_key",
    "privkey",
    "raw_transaction",
    "recovery_phrase",
    "secret",
    "seed",
    "seed_phrase",
    "signature",
    "signed_order",
    "signed_payload",
    "transaction_hash",
    "wallet_password",
    "wallet_private_key",
}
SAFE_NEGATIVE_FIELD_PREFIXES = ("no_", "no_real_", "not_")
SAFE_NEGATIVE_FIELD_NAMES = {
    "no_authenticated_endpoint_called",
    "no_external_api_call",
    "no_external_api_call_performed",
    "no_order_endpoint",
    "no_private_key",
    "no_real_execution",
    "no_real_execution_performed",
    "no_real_order_submitted",
    "no_real_private_key_used",
    "no_real_signature",
    "no_real_signature_created",
    "no_real_wallet_used",
    "real_signature_created",
}

REQUIRED_SAFETY_ASSERTIONS = {
    "no_private_key": True,
    "no_real_signature": True,
    "no_order_endpoint": True,
    "no_external_api_call": True,
    "no_real_execution": True,
}

BTC_MARKET_READINESS_REVIEW_ONLY_BLOCKER_CATEGORIES = (
    "btc_read_only_connector_review_only",
    "btc_market_snapshot_not_live_trade_approval",
    "btc_market_analysis_not_yet_order_intent",
    "authenticated_live_order_connector_still_disabled",
    "real_order_submission_still_disabled",
)


class CanaryReadinessValidationError(ValueError):
    pass


def btc_market_readiness_blocker_categories() -> tuple[str, ...]:
    return BTC_MARKET_READINESS_REVIEW_ONLY_BLOCKER_CATEGORIES


def stable_canary_id(*, run_id: str, market_id: str) -> str:
    return _stable_id(
        "live-canary-readiness-029",
        {"run_id": clean_text(run_id), "market_id": clean_text(market_id)},
    )


def build_canary_operator_approval_record(
    *,
    run_id: str,
    market_id: str,
    canary_id: str = "",
    approval_status: str = APPROVAL_NOT_REQUESTED,
    requested_at: str | None = None,
    approved_at: str | None = None,
    expires_at: str | None = None,
    reviewed_by: str = "",
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    status = clean_text(approval_status)
    if status not in ALLOWED_OPERATOR_APPROVAL_STATUSES:
        raise CanaryReadinessValidationError(
            f"approval_status must be one of {sorted(ALLOWED_OPERATOR_APPROVAL_STATUSES)}"
        )
    normalized_run_id = clean_text(run_id)
    normalized_market_id = clean_text(market_id)
    normalized_canary_id = clean_text(canary_id) or stable_canary_id(
        run_id=normalized_run_id,
        market_id=normalized_market_id,
    )
    return {
        "contract_version": LIVE_CANARY_OPERATOR_APPROVAL_RECORD_CONTRACT,
        "approval_record_id": _stable_id(
            "live-canary-dry-run-approval-029",
            {
                "canary_id": normalized_canary_id,
                "run_id": normalized_run_id,
                "market_id": normalized_market_id,
                "approval_status": status,
            },
        ),
        "canary_id": normalized_canary_id,
        "run_id": normalized_run_id,
        "market_id": normalized_market_id,
        "approval_status": status,
        "approval_scope": "dry_run_readiness_only",
        "requested_at": requested_at,
        "approved_at": approved_at,
        "expires_at": expires_at,
        "reviewed_by": clean_text(reviewed_by),
        "created_at": generated_at,
        "local_artifact_only": True,
        "dry_run_only": True,
        "live_execution_approval_supported": False,
        "live_execution_approved": False,
        "real_wallet_access_approved": False,
        "private_key_access_approved": False,
        "cryptographic_signing_approved": False,
        "order_submission_approved": False,
        "authenticated_endpoint_approved": False,
        "external_api_call_approved": False,
        "idempotency": {
            "stable_id_excludes_timestamps": True,
            "timestamps_are_metadata": True,
        },
    }


def validate_canary_operator_approval_record(record: Mapping[str, Any]) -> tuple[bool, list[str]]:
    errors: list[str] = []
    if record.get("contract_version") != LIVE_CANARY_OPERATOR_APPROVAL_RECORD_CONTRACT:
        errors.append(f"contract_version must be {LIVE_CANARY_OPERATOR_APPROVAL_RECORD_CONTRACT}")
    for field in ("approval_record_id", "canary_id", "run_id", "market_id", "approval_status"):
        if not clean_text(record.get(field)):
            errors.append(f"{field} must be a non-empty string")
    if record.get("approval_status") not in ALLOWED_OPERATOR_APPROVAL_STATUSES:
        errors.append("approval_status is not supported for canary dry-run readiness")
    if record.get("approval_scope") != "dry_run_readiness_only":
        errors.append("approval_scope must be dry_run_readiness_only")
    for field in (
        "local_artifact_only",
        "dry_run_only",
    ):
        if record.get(field) is not True:
            errors.append(f"{field} must be true")
    for field in (
        "live_execution_approval_supported",
        "live_execution_approved",
        "real_wallet_access_approved",
        "private_key_access_approved",
        "cryptographic_signing_approved",
        "order_submission_approved",
        "authenticated_endpoint_approved",
        "external_api_call_approved",
    ):
        if record.get(field) is not False:
            errors.append(f"{field} must be false")
    errors.extend(_forbidden_scan_errors(record))
    return not errors, errors


def select_canary_market_id(
    *,
    paper_strategy_ledger: Mapping[str, Any] | None = None,
    risk_decision_ledger: Mapping[str, Any] | None = None,
    wallet_boundary_audit_ledger: Mapping[str, Any] | None = None,
    source_evidence_status: Mapping[str, Any] | None = None,
) -> str:
    strategy_records = sorted(
        mapping_rows((paper_strategy_ledger or {}).get("records")),
        key=lambda row: (clean_text(row.get("market_id")), clean_text(row.get("intent_id"))),
    )
    if strategy_records:
        return clean_text(strategy_records[0].get("market_id"))
    decisions = sorted(
        mapping_rows((risk_decision_ledger or {}).get("decisions")),
        key=lambda row: (
            clean_text(row.get("decision_input", {}).get("market_id")),
            clean_text(row.get("decision_input", {}).get("intent_id")),
        ),
    )
    if decisions:
        return clean_text(decisions[0].get("decision_input", {}).get("market_id"))
    packets = sorted(
        mapping_rows((wallet_boundary_audit_ledger or {}).get("execution_request_packets")),
        key=lambda row: clean_text(row.get("risk_approved_action_packet", {}).get("market_id")),
    )
    if packets:
        return clean_text(packets[0].get("risk_approved_action_packet", {}).get("market_id"))
    source_rows = sorted(
        mapping_rows(dict((source_evidence_status or {}).get("quality_ledger", {})).get("market_source_status")),
        key=lambda row: clean_text(row.get("market_id")),
    )
    return clean_text(source_rows[0].get("market_id")) if source_rows else ""


def build_canary_readiness_packet(
    *,
    paper_strategy_ledger: Mapping[str, Any] | None = None,
    source_evidence_status: Mapping[str, Any] | None = None,
    risk_decision_ledger: Mapping[str, Any] | None = None,
    wallet_boundary_audit_ledger: Mapping[str, Any] | None = None,
    signing_simulator_receipt_ledger: Mapping[str, Any] | None = None,
    operator_approval_record: Mapping[str, Any] | None = None,
    run_context: Mapping[str, Any] | None = None,
    canary_market_id: str = "",
    max_canary_notional_usd: float | None = None,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    strategy_ledger = dict(paper_strategy_ledger or {})
    source_status = dict(source_evidence_status or {})
    risk_ledger = dict(risk_decision_ledger or {})
    wallet_ledger = dict(wallet_boundary_audit_ledger or {})
    receipt_ledger = dict(signing_simulator_receipt_ledger or {})
    context = dict(run_context or {})
    market_id = clean_text(canary_market_id) or select_canary_market_id(
        paper_strategy_ledger=strategy_ledger,
        risk_decision_ledger=risk_ledger,
        wallet_boundary_audit_ledger=wallet_ledger,
        source_evidence_status=source_status,
    )
    strategy_record = _strategy_record_for_market(strategy_ledger, market_id)
    intent_id = clean_text(strategy_record.get("intent_id"))
    risk_decision = _risk_decision_for_market(risk_ledger, market_id, intent_id)
    wallet_packet = _wallet_packet_for_decision_or_market(wallet_ledger, risk_decision, market_id)
    signing_receipt = _signing_receipt_for_packet_or_decision(receipt_ledger, wallet_packet, risk_decision)
    source_market_status = _source_status_for_market(source_status, market_id)
    action_packet = _action_packet(wallet_packet)
    decision_input = dict(risk_decision.get("decision_input", {}))
    limit_snapshot = dict(risk_decision.get("limit_snapshot", {}))

    run_id = _first_text(
        context.get("run_id"),
        strategy_ledger.get("run_id"),
        risk_ledger.get("run_id"),
        wallet_ledger.get("run_id"),
        receipt_ledger.get("run_id"),
        decision_input.get("run_id"),
        action_packet.get("run_id"),
    )
    canary_id = stable_canary_id(run_id=run_id, market_id=market_id)
    approval_record_missing = operator_approval_record is None
    approval = (
        dict(operator_approval_record)
        if operator_approval_record is not None
        else build_canary_operator_approval_record(run_id=run_id, market_id=market_id, canary_id=canary_id)
    )
    approval_status = clean_text(approval.get("approval_status") or APPROVAL_NOT_REQUESTED)
    proposed_notional = _number_or_none(
        decision_input.get("requested_notional_usd"),
        strategy_record.get("risk_engine_decision", {}).get("requested_notional_usd"),
        action_packet.get("proposed_notional_usd"),
    )
    max_canary_notional = (
        round(float(max_canary_notional_usd), 2)
        if max_canary_notional_usd is not None
        else _number_or_none(limit_snapshot.get("max_single_action_notional_usd"), action_packet.get("risk_snapshot", {}).get("max_single_action_notional_usd"))
    )
    evidence_freshness_status = _evidence_freshness_status(source_market_status)
    source_gap_status = _source_gap_status(source_market_status)
    risk_status = clean_text(risk_decision.get("decision"))
    wallet_status = clean_text(wallet_packet.get("packet_status") or wallet_packet.get("validation", {}).get("status"))
    signing_status = clean_text(signing_receipt.get("status"))
    kill_switch_status = clean_text(action_packet.get("kill_switch_status"))
    action_type = _action_type(decision_input, strategy_record, action_packet)

    reason_codes: list[str] = []
    missing_artifacts: list[str] = []
    _collect_missing_and_gate_reasons(
        reason_codes=reason_codes,
        missing_artifacts=missing_artifacts,
        strategy_record=strategy_record,
        source_market_status=source_market_status,
        risk_decision=risk_decision,
        wallet_packet=wallet_packet,
        signing_receipt=signing_receipt,
        operator_approval_record=operator_approval_record,
        run_id=run_id,
        market_id=market_id,
        proposed_notional=proposed_notional,
        max_canary_notional=max_canary_notional,
        action_type=action_type,
        evidence_freshness_status=evidence_freshness_status,
        source_gap_status=source_gap_status,
        risk_status=risk_status,
        wallet_status=wallet_status,
        signing_status=signing_status,
        kill_switch_status=kill_switch_status,
        approval_status=approval_status,
        approval=approval,
    )

    packet = {
        "contract_version": LIVE_CANARY_READINESS_PACKET_CONTRACT,
        "canary_id": canary_id,
        "run_id": run_id,
        "run_date": clean_text(context.get("run_date") or strategy_ledger.get("run_date")),
        "market_id": market_id,
        "market_title": _market_title(strategy_record, context, market_id),
        "market_slug": _market_slug(strategy_record, context, market_id),
        "proposed_notional_usd": proposed_notional if proposed_notional is not None else 0.0,
        "max_canary_notional_usd": max_canary_notional if max_canary_notional is not None else 0.0,
        "action_type": action_type,
        "paper_strategy_ledger_ref": _strategy_ref(strategy_ledger, strategy_record),
        "source_evidence_ref": _source_ref(source_status, source_market_status, market_id),
        "evidence_freshness_status": evidence_freshness_status,
        "source_gap_status": source_gap_status,
        "risk_decision_id": clean_text(risk_decision.get("risk_decision_id")),
        "risk_decision_status": risk_status,
        "risk_reason_codes": [clean_text(item) for item in risk_decision.get("reason_codes", [])],
        "wallet_boundary_packet_id": clean_text(wallet_packet.get("packet_id")),
        "wallet_boundary_status": wallet_status,
        "signing_simulator_receipt_id": clean_text(signing_receipt.get("receipt_id")),
        "signing_simulator_receipt_status": signing_status,
        "operator_approval_record_id": "" if approval_record_missing else clean_text(approval.get("approval_record_id")),
        "operator_approval_status": approval_status,
        "kill_switch_status": kill_switch_status or "unknown",
        "canary_status": _canary_status(reason_codes, approval_status),
        "reason_codes": _dedupe(reason_codes),
        "blocked_reason_summary": _dedupe(reason_codes),
        "missing_artifact_summary": sorted(set(missing_artifacts)),
        "forbidden_field_paths": [],
        "next_operator_action": "",
        "created_at": generated_at,
        "idempotency": {
            "logical_key": f"{run_id}:{market_id}",
            "stable_canary_id": True,
            "stable_id_excludes_timestamps": True,
            "timestamps_are_metadata": True,
        },
        "safety_assertions": dict(REQUIRED_SAFETY_ASSERTIONS),
        "dry_run_only": True,
        "paper_only": True,
        "live_readiness_only": True,
        "passive_artifact_only": True,
        "local_artifact_only": True,
        "live_execution_allowed": False,
        "live_execution_enabled": False,
        "real_wallet_used": False,
        "private_key_used": False,
        "real_signature_created": False,
        "real_order_submitted": False,
        "authenticated_endpoint_called": False,
        "external_api_call_performed": False,
        "live_execution_performed": False,
        "outcome_resolution_invented": False,
        "pnl_invented": False,
        "safety_summary": trading_core_safety_summary(),
    }
    forbidden_paths = scan_forbidden_fields(packet)
    if forbidden_paths:
        _append_reason(reason_codes, "FORBIDDEN_CANARY_FIELD_PRESENT")
        packet["forbidden_field_paths"] = forbidden_paths
        packet["reason_codes"] = _dedupe(reason_codes)
        packet["blocked_reason_summary"] = _dedupe(reason_codes)
        packet["canary_status"] = CANARY_STATUS_BLOCKED
    packet["next_operator_action"] = _next_operator_action(packet)
    return packet


def validate_canary_readiness_packet(packet: Mapping[str, Any]) -> tuple[bool, list[str]]:
    errors: list[str] = []
    if packet.get("contract_version") != LIVE_CANARY_READINESS_PACKET_CONTRACT:
        errors.append(f"contract_version must be {LIVE_CANARY_READINESS_PACKET_CONTRACT}")
    for field in (
        "canary_id",
        "run_id",
        "market_id",
        "action_type",
        "paper_strategy_ledger_ref",
        "source_evidence_ref",
        "evidence_freshness_status",
        "source_gap_status",
        "risk_decision_status",
        "operator_approval_status",
        "kill_switch_status",
        "canary_status",
    ):
        if not clean_text(packet.get(field)):
            errors.append(f"{field} must be a non-empty string")
    if packet.get("canary_status") not in ALLOWED_CANARY_STATUSES:
        errors.append("canary_status is not supported")
    if packet.get("operator_approval_status") not in ALLOWED_OPERATOR_APPROVAL_STATUSES:
        errors.append("operator_approval_status is not supported")
    action_type = clean_text(packet.get("action_type")).lower()
    if action_type and "simulated" not in action_type and "proposed" not in action_type:
        errors.append("action_type must be explicitly simulated or proposed")
    for field in ("proposed_notional_usd", "max_canary_notional_usd"):
        if not isinstance(packet.get(field), (int, float)) or isinstance(packet.get(field), bool):
            errors.append(f"{field} must be numeric")
        elif float(packet.get(field, 0)) < 0:
            errors.append(f"{field} must be >= 0")
    safety_assertions = packet.get("safety_assertions")
    if not isinstance(safety_assertions, Mapping):
        errors.append("safety_assertions must be an object")
    elif dict(safety_assertions) != REQUIRED_SAFETY_ASSERTIONS:
        errors.append("safety_assertions must match the dry-run-only canary safety assertions")
    for field in (
        "dry_run_only",
        "paper_only",
        "live_readiness_only",
        "passive_artifact_only",
        "local_artifact_only",
    ):
        if packet.get(field) is not True:
            errors.append(f"{field} must be true")
    for field in (
        "live_execution_allowed",
        "live_execution_enabled",
        "real_wallet_used",
        "private_key_used",
        "real_signature_created",
        "real_order_submitted",
        "authenticated_endpoint_called",
        "external_api_call_performed",
        "live_execution_performed",
        "outcome_resolution_invented",
        "pnl_invented",
    ):
        if packet.get(field) is not False:
            errors.append(f"{field} must be false")
    errors.extend(_forbidden_scan_errors(packet))
    return not errors, errors


def validate_canary_dry_run_acceptance(packet: Mapping[str, Any]) -> dict[str, Any]:
    reason_codes: list[str] = []
    valid_packet, packet_errors = validate_canary_readiness_packet(packet)
    if not valid_packet:
        reason_codes.extend(f"PACKET_INVALID:{error}" for error in packet_errors)
    if clean_text(packet.get("risk_decision_status")) != DECISION_ALLOWED:
        _append_reason(reason_codes, "RISK_DECISION_NOT_ALLOWED")
    if clean_text(packet.get("kill_switch_status")).lower() != "disabled":
        _append_reason(reason_codes, "KILL_SWITCH_MUST_BE_DISABLED")
    if clean_text(packet.get("evidence_freshness_status")).lower() not in FRESH_EVIDENCE_STATUSES:
        _append_reason(reason_codes, "EVIDENCE_NOT_FRESH")
    if clean_text(packet.get("source_gap_status")).lower() not in SOURCE_GAP_FREE_STATUSES:
        _append_reason(reason_codes, "SOURCE_GAP_PRESENT")
    if clean_text(packet.get("wallet_boundary_status")) != STATUS_APPROVED_FOR_FUTURE_SIMULATION:
        _append_reason(reason_codes, "WALLET_BOUNDARY_PACKET_NOT_READY")
    if clean_text(packet.get("signing_simulator_receipt_status")) != STATUS_DRY_RUN_RECEIPT_READY:
        _append_reason(reason_codes, "SIGNING_SIMULATOR_RECEIPT_NOT_READY")
    if clean_text(packet.get("operator_approval_status")) != APPROVAL_DRY_RUN_ONLY:
        _append_reason(reason_codes, "DRY_RUN_OPERATOR_APPROVAL_REQUIRED")
    if clean_text(packet.get("canary_status")) != CANARY_STATUS_DRY_RUN_READY:
        _append_reason(reason_codes, "CANARY_PACKET_NOT_DRY_RUN_READY")
    proposed = float(packet.get("proposed_notional_usd", 0) or 0)
    max_canary = float(packet.get("max_canary_notional_usd", 0) or 0)
    if proposed > max_canary:
        _append_reason(reason_codes, "PROPOSED_NOTIONAL_EXCEEDS_MAX_CANARY_NOTIONAL")
    forbidden_paths = scan_forbidden_fields(packet)
    if forbidden_paths:
        _append_reason(reason_codes, "FORBIDDEN_CANARY_FIELD_PRESENT")
    return {
        "valid": not reason_codes,
        "status": DRY_RUN_ACCEPTANCE_ACCEPTED if not reason_codes else DRY_RUN_ACCEPTANCE_BLOCKED,
        "reason_codes": _dedupe(reason_codes),
        "forbidden_field_paths": forbidden_paths,
        "gate_results": {
            "risk_engine_approved": clean_text(packet.get("risk_decision_status")) == DECISION_ALLOWED,
            "kill_switch_disabled": clean_text(packet.get("kill_switch_status")).lower() == "disabled",
            "evidence_requirements_satisfied": clean_text(packet.get("evidence_freshness_status")).lower()
            in FRESH_EVIDENCE_STATUSES,
            "source_gap_requirements_satisfied": clean_text(packet.get("source_gap_status")).lower()
            in SOURCE_GAP_FREE_STATUSES,
            "wallet_boundary_packet_ready": clean_text(packet.get("wallet_boundary_status"))
            == STATUS_APPROVED_FOR_FUTURE_SIMULATION,
            "signing_simulator_receipt_ready": clean_text(packet.get("signing_simulator_receipt_status"))
            == STATUS_DRY_RUN_RECEIPT_READY,
            "operator_approval_dry_run_only": clean_text(packet.get("operator_approval_status"))
            == APPROVAL_DRY_RUN_ONLY,
            "canary_packet_dry_run_ready": clean_text(packet.get("canary_status")) == CANARY_STATUS_DRY_RUN_READY,
            "forbidden_field_paths_absent": not forbidden_paths,
            "notional_within_canary_limit": proposed <= max_canary,
        },
    }


def build_canary_dry_run_acceptance_receipt(
    packet: Mapping[str, Any],
    *,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    validation = validate_canary_dry_run_acceptance(packet)
    status = clean_text(validation.get("status"))
    reason_codes = [clean_text(item) for item in validation.get("reason_codes", []) if clean_text(item)]
    receipt_id = _stable_id(
        "live-canary-dry-run-receipt-029",
        {
            "canary_id": packet.get("canary_id"),
            "run_id": packet.get("run_id"),
            "market_id": packet.get("market_id"),
            "status": status,
            "reason_codes": reason_codes,
        },
    )
    receipt = {
        "contract_version": LIVE_CANARY_DRY_RUN_RECEIPT_CONTRACT,
        "receipt_id": receipt_id,
        "canary_id": clean_text(packet.get("canary_id")),
        "run_id": clean_text(packet.get("run_id")),
        "market_id": clean_text(packet.get("market_id")),
        "created_at": generated_at,
        "approval_scope": "dry_run_only",
        "acceptance_status": status,
        "canary_status": clean_text(packet.get("canary_status")),
        "reason_codes": reason_codes,
        "validation": validation,
        "no_real_wallet_used": True,
        "no_real_private_key_used": True,
        "no_real_signature_created": True,
        "no_real_order_submitted": True,
        "no_authenticated_endpoint_called": True,
        "no_external_api_call_performed": True,
        "no_live_execution_performed": True,
        "safety_statements": [
            "no real wallet used",
            "no real private key used",
            "no real signature created",
            "no real order submitted",
            "no authenticated endpoint called",
            "no external API call performed",
            "no live execution performed",
        ],
        "dry_run_only": True,
        "paper_only": True,
        "live_readiness_only": True,
        "passive_artifact_only": True,
        "local_artifact_only": True,
        "live_execution_allowed": False,
        "live_execution_enabled": False,
        "live_execution_performed": False,
        "real_wallet_used": False,
        "private_key_used": False,
        "real_signature_created": False,
        "real_order_submitted": False,
        "authenticated_endpoint_called": False,
        "external_api_call_performed": False,
        "outcome_resolution_invented": False,
        "pnl_invented": False,
        "idempotency": {
            "stable_receipt_id": True,
            "stable_id_excludes_timestamps": True,
            "timestamps_are_metadata": True,
        },
    }
    forbidden_paths = scan_forbidden_fields(receipt)
    if forbidden_paths:
        receipt["acceptance_status"] = DRY_RUN_ACCEPTANCE_BLOCKED
        receipt["reason_codes"] = _dedupe([*reason_codes, "FORBIDDEN_CANARY_FIELD_PRESENT"])
        receipt["validation"] = dict(validation)
        receipt["validation"]["forbidden_field_paths"] = forbidden_paths
        receipt["validation"]["valid"] = False
    return receipt


def build_canary_dashboard_summary(
    packet: Mapping[str, Any],
    receipt: Mapping[str, Any] | None = None,
    *,
    live_connector_audit_replay_status: str = "",
    operator_review_packet_status: str = "",
    operator_review_ready: bool = False,
    operator_intent_packet_status: str = "",
    operator_intent_packet_review_ready: bool = False,
    readiness_evidence_bundle_status: str = "",
    readiness_evidence_bundle_review_ready: bool = False,
    readiness_evidence_bundle_is_not_live_approval: bool = True,
    evidence_item_count: int = 0,
    missing_required_evidence_count: int = 0,
    unresolved_live_blocker_count: int = 0,
    latest_readiness_evidence_bundle_path: str = "",
    risk_control_plane_status: str = "review_only_not_live_enforced",
) -> dict[str, Any]:
    receipt_value = dict(receipt or {})
    return {
        "canary_id": clean_text(packet.get("canary_id")),
        "canary_readiness_status": clean_text(packet.get("canary_status")),
        "blocked_reason_summary": list(packet.get("blocked_reason_summary", [])),
        "missing_artifact_summary": list(packet.get("missing_artifact_summary", [])),
        "operator_approval_status": clean_text(packet.get("operator_approval_status")),
        "risk_decision_status": clean_text(packet.get("risk_decision_status")),
        "wallet_boundary_status": clean_text(packet.get("wallet_boundary_status")),
        "signing_simulator_receipt_status": clean_text(packet.get("signing_simulator_receipt_status")),
        "dry_run_acceptance_status": clean_text(receipt_value.get("acceptance_status")),
        "live_connector_audit_replay_status": clean_text(live_connector_audit_replay_status),
        "operator_review_packet_status": clean_text(operator_review_packet_status),
        "operator_review_ready": operator_review_ready is True,
        "operator_intent_packet_status": clean_text(operator_intent_packet_status) or "not_generated",
        "operator_intent_packet_review_ready": operator_intent_packet_review_ready is True,
        "operator_intent_is_not_live_approval": True,
        "readiness_evidence_bundle_status": clean_text(readiness_evidence_bundle_status) or "not_generated",
        "readiness_evidence_bundle_review_ready": readiness_evidence_bundle_review_ready is True,
        "readiness_evidence_bundle_is_not_live_approval": readiness_evidence_bundle_is_not_live_approval is True,
        "evidence_item_count": int(evidence_item_count or 0),
        "missing_required_evidence_count": int(missing_required_evidence_count or 0),
        "unresolved_live_blocker_count": int(unresolved_live_blocker_count or 0),
        "latest_readiness_evidence_bundle_path": clean_text(latest_readiness_evidence_bundle_path),
        "risk_control_plane_status": clean_text(risk_control_plane_status),
        "risk_limit_control_plane_review_only": True,
        "risk_limits_not_live_enforced_against_real_connector": True,
        "btc_market_connector_not_configured": True,
        "live_order_adapter_not_enabled": True,
        "real_execution_still_unavailable": True,
        "live_execution_approved": False,
        "real_execution_available": False,
        "live_connector_enabled": False,
        "canary_executable_now": False,
        "tiny_live_canary_preflight_status": "not_generated",
        "manual_runbook_status": "not_generated",
        "next_operator_action": clean_text(packet.get("next_operator_action")),
        "dry_run_only": True,
        "live_execution_allowed": False,
        "external_api_call_performed": False,
        "real_wallet_used": False,
        "private_key_used": False,
        "real_signature_created": False,
        "real_order_submitted": False,
        "authenticated_endpoint_called": False,
        "outcome_resolution_invented": False,
        "pnl_invented": False,
    }


def scan_forbidden_fields(value: Any, path: str = "$") -> list[str]:
    paths: list[str] = []
    if isinstance(value, Mapping):
        for key, nested in value.items():
            key_text = clean_text(key)
            nested_path = f"{path}.{key_text}"
            if _is_forbidden_key(key_text):
                paths.append(nested_path)
            paths.extend(scan_forbidden_fields(nested, nested_path))
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            paths.extend(scan_forbidden_fields(nested, f"{path}[{index}]"))
    return paths


def write_canary_readiness_artifacts(
    *,
    packet: Mapping[str, Any],
    receipt: Mapping[str, Any],
    operator_approval_record: Mapping[str, Any] | None = None,
    out_packet_json_path: str | Path = ARTIFACT_DIR / "live_canary_readiness_packet.json",
    out_packet_md_path: str | Path = ARTIFACT_DIR / "live_canary_readiness_packet.md",
    out_receipt_json_path: str | Path = ARTIFACT_DIR / "live_canary_dry_run_acceptance_receipt.json",
    out_receipt_md_path: str | Path = ARTIFACT_DIR / "live_canary_dry_run_acceptance_receipt.md",
    out_operator_approval_json_path: str | Path | None = ARTIFACT_DIR / "live_canary_operator_approval_record.json",
    out_operator_approval_md_path: str | Path | None = ARTIFACT_DIR / "live_canary_operator_approval_record.md",
) -> dict[str, str]:
    write_json(out_packet_json_path, dict(packet))
    write_text(out_packet_md_path, render_canary_readiness_packet_markdown(packet))
    write_json(out_receipt_json_path, dict(receipt))
    write_text(out_receipt_md_path, render_canary_dry_run_receipt_markdown(receipt))
    paths = {
        "packet_json": _normalize_path(out_packet_json_path),
        "packet_md": _normalize_path(out_packet_md_path),
        "receipt_json": _normalize_path(out_receipt_json_path),
        "receipt_md": _normalize_path(out_receipt_md_path),
    }
    if operator_approval_record is not None and out_operator_approval_json_path is not None:
        write_json(out_operator_approval_json_path, dict(operator_approval_record))
        paths["operator_approval_json"] = _normalize_path(out_operator_approval_json_path)
    if operator_approval_record is not None and out_operator_approval_md_path is not None:
        write_text(out_operator_approval_md_path, render_canary_operator_approval_markdown(operator_approval_record))
        paths["operator_approval_md"] = _normalize_path(out_operator_approval_md_path)
    return paths


def render_canary_operator_approval_markdown(record: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# PMBOT Live Canary Dry-Run Operator Approval Record",
            "",
            f"- Approval record: `{record.get('approval_record_id')}`",
            f"- Canary: `{record.get('canary_id')}`",
            f"- Run: `{record.get('run_id')}`",
            f"- Market: `{record.get('market_id')}`",
            f"- Status: `{record.get('approval_status')}`",
            f"- Scope: `{record.get('approval_scope')}`",
            "- This record can approve dry-run readiness only and cannot approve live execution.",
            "- No real wallet, private key, signing, order submission, authenticated endpoint, or external API call is approved.",
        ]
    ) + "\n"


def render_canary_readiness_packet_markdown(packet: Mapping[str, Any]) -> str:
    lines = [
        "# PMBOT Live Canary Readiness Packet",
        "",
        f"- Canary: `{packet.get('canary_id')}`",
        f"- Run: `{packet.get('run_id')}`",
        f"- Market: `{packet.get('market_id')}`",
        f"- Status: `{packet.get('canary_status')}`",
        f"- Operator approval: `{packet.get('operator_approval_status')}`",
        f"- Risk decision: `{packet.get('risk_decision_status')}`",
        f"- Kill switch: `{packet.get('kill_switch_status')}`",
        f"- Evidence freshness: `{packet.get('evidence_freshness_status')}`",
        f"- Source gaps: `{packet.get('source_gap_status')}`",
        f"- Wallet boundary: `{packet.get('wallet_boundary_status')}`",
        f"- Signing simulator receipt: `{packet.get('signing_simulator_receipt_status')}`",
        f"- Proposed notional: `${packet.get('proposed_notional_usd')}`",
        f"- Max canary notional: `${packet.get('max_canary_notional_usd')}`",
        "",
        "## Blocked Reasons",
        "",
        *bullet_lines(str(item) for item in packet.get("blocked_reason_summary", [])),
        "",
        "## Missing Artifacts",
        "",
        *bullet_lines(str(item) for item in packet.get("missing_artifact_summary", [])),
        "",
        "## Next Operator Action",
        "",
        f"- {packet.get('next_operator_action')}",
        "",
        "## Safety",
        "",
        "- Dry-run/live-readiness artifact only.",
        "- No real wallet, private key, real signature, order endpoint, external API call, or live execution exists.",
    ]
    return "\n".join(lines) + "\n"


def render_canary_dry_run_receipt_markdown(receipt: Mapping[str, Any]) -> str:
    lines = [
        "# PMBOT Live Canary Dry-Run Acceptance Receipt",
        "",
        f"- Receipt: `{receipt.get('receipt_id')}`",
        f"- Canary: `{receipt.get('canary_id')}`",
        f"- Status: `{receipt.get('acceptance_status')}`",
        f"- Approval scope: `{receipt.get('approval_scope')}`",
        "",
        "## Reason Codes",
        "",
        *bullet_lines(str(item) for item in receipt.get("reason_codes", [])),
        "",
        "## Explicit Safety Statements",
        "",
        *bullet_lines(str(item) for item in receipt.get("safety_statements", [])),
    ]
    return "\n".join(lines) + "\n"


def load_and_write_canary_readiness_gate(
    *,
    paper_strategy_ledger_path: str | Path = ARTIFACT_DIR / "paper_strategy_evaluation_ledger.json",
    source_evidence_status_path: str | Path = ARTIFACT_DIR / "public_evidence_refresh_ledger.json",
    risk_decision_ledger_path: str | Path = ARTIFACT_DIR / "risk_engine_decision_ledger.json",
    wallet_boundary_audit_ledger_path: str | Path = ARTIFACT_DIR / "wallet_boundary_audit_ledger.json",
    signing_simulator_receipt_ledger_path: str | Path = ARTIFACT_DIR / "dry_run_execution_receipts.json",
    operator_approval_record_path: str | Path | None = None,
    out_packet_json_path: str | Path = ARTIFACT_DIR / "live_canary_readiness_packet.json",
    out_packet_md_path: str | Path = ARTIFACT_DIR / "live_canary_readiness_packet.md",
    out_receipt_json_path: str | Path = ARTIFACT_DIR / "live_canary_dry_run_acceptance_receipt.json",
    out_receipt_md_path: str | Path = ARTIFACT_DIR / "live_canary_dry_run_acceptance_receipt.md",
    out_operator_approval_json_path: str | Path = ARTIFACT_DIR / "live_canary_operator_approval_record.json",
    out_operator_approval_md_path: str | Path = ARTIFACT_DIR / "live_canary_operator_approval_record.md",
    generated_at: str = GENERATED_AT,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    strategy = _load_optional_json_object(paper_strategy_ledger_path, "paper strategy ledger")
    source = _load_optional_json_object(source_evidence_status_path, "source evidence status")
    risk = _load_optional_json_object(risk_decision_ledger_path, "risk decision ledger")
    wallet = _load_optional_json_object(wallet_boundary_audit_ledger_path, "wallet boundary ledger")
    signing = _load_optional_json_object(signing_simulator_receipt_ledger_path, "signing simulator receipt ledger")
    approval = (
        _load_optional_json_object(operator_approval_record_path, "operator approval")
        if operator_approval_record_path is not None
        else None
    )
    if approval is None:
        market_id = select_canary_market_id(
            paper_strategy_ledger=strategy,
            risk_decision_ledger=risk,
            wallet_boundary_audit_ledger=wallet,
            source_evidence_status=source,
        )
        approval = build_canary_operator_approval_record(
            run_id=_first_text(strategy.get("run_id"), risk.get("run_id"), wallet.get("run_id"), signing.get("run_id")),
            market_id=market_id,
            generated_at=generated_at,
        )
    packet = build_canary_readiness_packet(
        paper_strategy_ledger=strategy,
        source_evidence_status=source,
        risk_decision_ledger=risk,
        wallet_boundary_audit_ledger=wallet,
        signing_simulator_receipt_ledger=signing,
        operator_approval_record=approval,
        generated_at=generated_at,
    )
    receipt = build_canary_dry_run_acceptance_receipt(packet, generated_at=generated_at)
    write_canary_readiness_artifacts(
        packet=packet,
        receipt=receipt,
        operator_approval_record=approval,
        out_packet_json_path=out_packet_json_path,
        out_packet_md_path=out_packet_md_path,
        out_receipt_json_path=out_receipt_json_path,
        out_receipt_md_path=out_receipt_md_path,
        out_operator_approval_json_path=out_operator_approval_json_path,
        out_operator_approval_md_path=out_operator_approval_md_path,
    )
    return packet, receipt, approval


def _collect_missing_and_gate_reasons(
    *,
    reason_codes: list[str],
    missing_artifacts: list[str],
    strategy_record: Mapping[str, Any],
    source_market_status: Mapping[str, Any],
    risk_decision: Mapping[str, Any],
    wallet_packet: Mapping[str, Any],
    signing_receipt: Mapping[str, Any],
    operator_approval_record: Mapping[str, Any] | None,
    run_id: str,
    market_id: str,
    proposed_notional: float | None,
    max_canary_notional: float | None,
    action_type: str,
    evidence_freshness_status: str,
    source_gap_status: str,
    risk_status: str,
    wallet_status: str,
    signing_status: str,
    kill_switch_status: str,
    approval_status: str,
    approval: Mapping[str, Any],
) -> None:
    if not run_id:
        _append_reason(reason_codes, "MISSING_RUN_ID")
    if not market_id:
        _append_reason(reason_codes, "MISSING_MARKET_ID")
    if not strategy_record:
        _append_reason(reason_codes, "MISSING_PAPER_STRATEGY_LEDGER_REF")
        missing_artifacts.append("paper_strategy_ledger")
    if not source_market_status:
        _append_reason(reason_codes, "MISSING_SOURCE_EVIDENCE_REF")
        missing_artifacts.append("source_evidence_status")
    if not risk_decision:
        _append_reason(reason_codes, "MISSING_RISK_DECISION")
        missing_artifacts.append("risk_decision_ledger")
    if not wallet_packet:
        _append_reason(reason_codes, "MISSING_WALLET_BOUNDARY_PACKET")
        missing_artifacts.append("wallet_boundary_packet")
    if not signing_receipt:
        _append_reason(reason_codes, "MISSING_SIGNING_SIMULATOR_RECEIPT")
        missing_artifacts.append("signing_simulator_receipt")
    if operator_approval_record is None:
        _append_reason(reason_codes, "OPERATOR_APPROVAL_NOT_REQUESTED")
        missing_artifacts.append("operator_approval_record")
    if proposed_notional is None:
        _append_reason(reason_codes, "MISSING_PROPOSED_NOTIONAL_USD")
    elif proposed_notional < 0:
        _append_reason(reason_codes, "PROPOSED_NOTIONAL_NEGATIVE")
    if max_canary_notional is None:
        _append_reason(reason_codes, "MISSING_MAX_CANARY_NOTIONAL_USD")
    elif max_canary_notional < 0:
        _append_reason(reason_codes, "MAX_CANARY_NOTIONAL_NEGATIVE")
    elif proposed_notional is not None and proposed_notional > max_canary_notional:
        _append_reason(reason_codes, "PROPOSED_NOTIONAL_EXCEEDS_MAX_CANARY_NOTIONAL")
    if not action_type or ("simulated" not in action_type.lower() and "proposed" not in action_type.lower()):
        _append_reason(reason_codes, "ACTION_TYPE_NOT_SIMULATED_OR_PROPOSED")
    if risk_status and risk_status != DECISION_ALLOWED:
        _append_reason(reason_codes, "RISK_DECISION_NOT_ALLOWED")
    if kill_switch_status.lower() != "disabled":
        _append_reason(reason_codes, "KILL_SWITCH_ENABLED")
    if evidence_freshness_status.lower() not in FRESH_EVIDENCE_STATUSES:
        _append_reason(reason_codes, "EVIDENCE_NOT_FRESH")
    if source_gap_status.lower() not in SOURCE_GAP_FREE_STATUSES:
        _append_reason(reason_codes, "SOURCE_GAP_PRESENT")
    if wallet_status and wallet_status != STATUS_APPROVED_FOR_FUTURE_SIMULATION:
        _append_reason(reason_codes, "WALLET_BOUNDARY_PACKET_NOT_READY")
    if signing_status and signing_status != STATUS_DRY_RUN_RECEIPT_READY:
        _append_reason(reason_codes, "SIGNING_SIMULATOR_RECEIPT_NOT_READY")
    if approval_status == APPROVAL_REJECTED:
        _append_reason(reason_codes, "OPERATOR_APPROVAL_REJECTED")
    elif approval_status == APPROVAL_EXPIRED:
        _append_reason(reason_codes, "OPERATOR_APPROVAL_EXPIRED")
    elif approval_status != APPROVAL_DRY_RUN_ONLY:
        _append_reason(reason_codes, "DRY_RUN_OPERATOR_APPROVAL_REQUIRED")
    if clean_text(approval.get("canary_id")) and clean_text(approval.get("canary_id")) != stable_canary_id(
        run_id=run_id,
        market_id=market_id,
    ):
        _append_reason(reason_codes, "OPERATOR_APPROVAL_CANARY_ID_MISMATCH")
    valid_approval, approval_errors = validate_canary_operator_approval_record(approval)
    if not valid_approval:
        reason_codes.extend(f"OPERATOR_APPROVAL_INVALID:{error}" for error in approval_errors)


def _canary_status(reason_codes: Sequence[str], approval_status: str) -> str:
    if approval_status == APPROVAL_REJECTED:
        return CANARY_STATUS_REJECTED
    technical_reasons = [
        reason
        for reason in reason_codes
        if reason
        not in {
            "DRY_RUN_OPERATOR_APPROVAL_REQUIRED",
            "OPERATOR_APPROVAL_NOT_REQUESTED",
        }
    ]
    if technical_reasons:
        return CANARY_STATUS_BLOCKED
    if approval_status != APPROVAL_DRY_RUN_ONLY:
        return CANARY_STATUS_NEEDS_OPERATOR_APPROVAL
    return CANARY_STATUS_DRY_RUN_READY


def _next_operator_action(packet: Mapping[str, Any]) -> str:
    status = clean_text(packet.get("canary_status"))
    if status == CANARY_STATUS_DRY_RUN_READY:
        return "Run the local canary dry-run acceptance flow and review the receipt; this does not permit live execution."
    if status == CANARY_STATUS_NEEDS_OPERATOR_APPROVAL:
        return "Create a local dry-run-only operator approval record for this canary packet, then rerun the readiness builder."
    if status == CANARY_STATUS_REJECTED:
        return "Do not continue this canary packet; create a new operator-reviewed record if the scope changes."
    return "Resolve blocked reason codes in local artifacts, then rerun the readiness builder."


def _strategy_record_for_market(ledger: Mapping[str, Any], market_id: str) -> Mapping[str, Any]:
    records = [
        row for row in mapping_rows(ledger.get("records")) if clean_text(row.get("market_id")) == clean_text(market_id)
    ]
    if not records:
        return {}
    return sorted(records, key=lambda row: clean_text(row.get("intent_id")))[0]


def _risk_decision_for_market(
    ledger: Mapping[str, Any],
    market_id: str,
    intent_id: str,
) -> Mapping[str, Any]:
    decisions = [
        row
        for row in mapping_rows(ledger.get("decisions"))
        if clean_text(row.get("decision_input", {}).get("market_id")) == clean_text(market_id)
        and (not intent_id or clean_text(row.get("decision_input", {}).get("intent_id")) == intent_id)
    ]
    if not decisions:
        return {}
    return sorted(decisions, key=lambda row: clean_text(row.get("decision_input", {}).get("intent_id")))[0]


def _wallet_packet_for_decision_or_market(
    ledger: Mapping[str, Any],
    decision: Mapping[str, Any],
    market_id: str,
) -> Mapping[str, Any]:
    risk_decision_id = clean_text(decision.get("risk_decision_id"))
    packets = []
    for packet in mapping_rows(ledger.get("execution_request_packets")):
        action = _action_packet(packet)
        if risk_decision_id and clean_text(action.get("risk_decision_id")) == risk_decision_id:
            packets.append(packet)
        elif clean_text(action.get("market_id")) == clean_text(market_id):
            packets.append(packet)
    if not packets:
        return {}
    return sorted(packets, key=lambda row: clean_text(row.get("packet_id")))[0]


def _signing_receipt_for_packet_or_decision(
    ledger: Mapping[str, Any],
    wallet_packet: Mapping[str, Any],
    decision: Mapping[str, Any],
) -> Mapping[str, Any]:
    packet_id = clean_text(wallet_packet.get("packet_id"))
    risk_decision_id = clean_text(decision.get("risk_decision_id"))
    receipts = []
    for receipt in mapping_rows(ledger.get("receipts")):
        if packet_id and clean_text(receipt.get("packet_id")) == packet_id:
            receipts.append(receipt)
        elif risk_decision_id and clean_text(receipt.get("risk_decision_id")) == risk_decision_id:
            receipts.append(receipt)
    if not receipts:
        return {}
    return sorted(receipts, key=lambda row: clean_text(row.get("receipt_id")))[0]


def _source_status_for_market(ledger: Mapping[str, Any], market_id: str) -> Mapping[str, Any]:
    quality = dict(ledger.get("quality_ledger", {}))
    for row in mapping_rows(quality.get("market_source_status")):
        if clean_text(row.get("market_id")) == clean_text(market_id):
            return row
    return {}


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
    return clean_text(source_status.get("freshness_status") or "missing")


def _source_gap_status(source_status: Mapping[str, Any]) -> str:
    if not source_status:
        return "gaps_present"
    return clean_text(source_status.get("gap_status") or "gaps_present")


def _source_ref(ledger: Mapping[str, Any], source_status: Mapping[str, Any], market_id: str) -> str:
    if not source_status:
        return ""
    refresh_id = clean_text(ledger.get("refresh_id") or ledger.get("ledger_id"))
    record_ids = [
        clean_text(row.get("record_id"))
        for row in mapping_rows(ledger.get("records"))
        if clean_text(row.get("market_id")) == clean_text(market_id) and clean_text(row.get("record_id"))
    ]
    suffix = ",".join(record_ids) if record_ids else f"market:{market_id}"
    return f"{refresh_id}#{suffix}" if refresh_id else suffix


def _strategy_ref(ledger: Mapping[str, Any], record: Mapping[str, Any]) -> str:
    ledger_id = clean_text(ledger.get("ledger_id"))
    record_id = clean_text(record.get("evaluation_record_id"))
    if ledger_id and record_id:
        return f"{ledger_id}#{record_id}"
    return ledger_id or record_id


def _market_title(record: Mapping[str, Any], context: Mapping[str, Any], market_id: str) -> str:
    if clean_text(record.get("market_title")):
        return clean_text(record.get("market_title"))
    for market in mapping_rows(context.get("tracked_markets")):
        if clean_text(market.get("market_id")) == clean_text(market_id):
            return clean_text(market.get("market_title"))
    return ""


def _market_slug(record: Mapping[str, Any], context: Mapping[str, Any], market_id: str) -> str:
    for source in (record,):
        for field in ("market_slug", "slug"):
            if clean_text(source.get(field)):
                return clean_text(source.get(field))
    for market in mapping_rows(context.get("tracked_markets")):
        if clean_text(market.get("market_id")) == clean_text(market_id):
            return clean_text(market.get("market_slug") or market.get("slug"))
    return ""


def _action_type(
    decision_input: Mapping[str, Any],
    strategy_record: Mapping[str, Any],
    action_packet: Mapping[str, Any],
) -> str:
    return _first_text(
        decision_input.get("action_type"),
        strategy_record.get("simulated_action_type"),
        action_packet.get("requested_boundary_action"),
        "simulated_unknown",
    )


def _action_packet(packet: Mapping[str, Any]) -> Mapping[str, Any]:
    action = packet.get("risk_approved_action_packet")
    return action if isinstance(action, Mapping) else {}


def _forbidden_scan_errors(value: Mapping[str, Any]) -> list[str]:
    return [f"forbidden canary field detected at {path}" for path in scan_forbidden_fields(value)]


def _is_forbidden_key(key: str) -> bool:
    normalized = _normalize_key(key)
    if normalized in SAFE_NEGATIVE_FIELD_NAMES or normalized.startswith(SAFE_NEGATIVE_FIELD_PREFIXES):
        return False
    if normalized in FORBIDDEN_CANARY_FIELD_NAMES:
        return True
    tokens = [token for token in normalized.split("_") if token]
    if "secret" in tokens or "seed" in tokens or "mnemonic" in tokens or "bearer" in tokens:
        return True
    if "signature" in tokens:
        return True
    for suffix in ("private_key", "api_key", "auth_token", "order_payload", "signed_order", "clob_order", "transaction_hash"):
        if normalized.endswith(f"_{suffix}") or normalized == suffix:
            return True
    return False


def _normalize_key(value: str) -> str:
    normalized = "".join(character if character.isalnum() else "_" for character in value.lower())
    while "__" in normalized:
        normalized = normalized.replace("__", "_")
    return normalized.strip("_")


def _load_optional_json_object(path: str | Path | None, label: str) -> dict[str, Any]:
    if path is None:
        return {}
    path_obj = Path(path)
    if not path_obj.exists():
        return {}
    return load_json_object(path_obj, label=label)


def _number_or_none(*values: Any) -> float | None:
    for value in values:
        if value is None or isinstance(value, bool):
            continue
        if isinstance(value, (int, float)):
            return round(float(value), 2)
        try:
            return round(float(value), 2)
        except (TypeError, ValueError):
            continue
    return None


def _append_reason(reasons: list[str], reason: str) -> None:
    if reason and reason not in reasons:
        reasons.append(reason)


def _dedupe(values: Sequence[str]) -> list[str]:
    result: list[str] = []
    for value in values:
        text = clean_text(value)
        if text and text not in result:
            result.append(text)
    return result


def _first_text(*values: Any) -> str:
    for value in values:
        text = clean_text(value)
        if text:
            return text
    return ""


def _stable_id(prefix: str, payload: Mapping[str, Any]) -> str:
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()
    return f"{prefix}-{digest[:16]}"


def _normalize_path(path: str | Path) -> str:
    return str(path).replace("\\", "/")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build PMBOT live canary readiness dry-run gate artifacts.")
    parser.add_argument("--paper-strategy-ledger", default=str(ARTIFACT_DIR / "paper_strategy_evaluation_ledger.json"))
    parser.add_argument("--source-evidence-status", default=str(ARTIFACT_DIR / "public_evidence_refresh_ledger.json"))
    parser.add_argument("--risk-decision-ledger", default=str(ARTIFACT_DIR / "risk_engine_decision_ledger.json"))
    parser.add_argument("--wallet-boundary-ledger", default=str(ARTIFACT_DIR / "wallet_boundary_audit_ledger.json"))
    parser.add_argument("--signing-receipts", default=str(ARTIFACT_DIR / "dry_run_execution_receipts.json"))
    parser.add_argument("--operator-approval", default=None)
    parser.add_argument("--out-packet-json", default=str(ARTIFACT_DIR / "live_canary_readiness_packet.json"))
    parser.add_argument("--out-packet-md", default=str(ARTIFACT_DIR / "live_canary_readiness_packet.md"))
    parser.add_argument(
        "--out-receipt-json",
        default=str(ARTIFACT_DIR / "live_canary_dry_run_acceptance_receipt.json"),
    )
    parser.add_argument(
        "--out-receipt-md",
        default=str(ARTIFACT_DIR / "live_canary_dry_run_acceptance_receipt.md"),
    )
    parser.add_argument(
        "--out-operator-approval-json",
        default=str(ARTIFACT_DIR / "live_canary_operator_approval_record.json"),
    )
    parser.add_argument(
        "--out-operator-approval-md",
        default=str(ARTIFACT_DIR / "live_canary_operator_approval_record.md"),
    )
    args = parser.parse_args(argv)
    load_and_write_canary_readiness_gate(
        paper_strategy_ledger_path=args.paper_strategy_ledger,
        source_evidence_status_path=args.source_evidence_status,
        risk_decision_ledger_path=args.risk_decision_ledger,
        wallet_boundary_audit_ledger_path=args.wallet_boundary_ledger,
        signing_simulator_receipt_ledger_path=args.signing_receipts,
        operator_approval_record_path=args.operator_approval,
        out_packet_json_path=args.out_packet_json,
        out_packet_md_path=args.out_packet_md,
        out_receipt_json_path=args.out_receipt_json,
        out_receipt_md_path=args.out_receipt_md,
        out_operator_approval_json_path=args.out_operator_approval_json,
        out_operator_approval_md_path=args.out_operator_approval_md,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
