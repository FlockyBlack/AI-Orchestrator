from __future__ import annotations

import argparse
import copy
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from pm_bot.trading_core.live_canary_readiness import (
    APPROVAL_DRY_RUN_ONLY,
    APPROVAL_EXPIRED,
    APPROVAL_REJECTED,
    APPROVAL_REQUESTED,
    CANARY_STATUS_BLOCKED,
    CANARY_STATUS_DRY_RUN_READY,
    CANARY_STATUS_NEEDS_OPERATOR_APPROVAL,
    CANARY_STATUS_REJECTED,
    DRY_RUN_ACCEPTANCE_ACCEPTED,
    DRY_RUN_ACCEPTANCE_BLOCKED,
    build_canary_dry_run_acceptance_receipt,
    build_canary_operator_approval_record,
    build_canary_readiness_packet,
    scan_forbidden_fields,
    validate_canary_readiness_packet,
)
from pm_bot.trading_core.risk_engine import DECISION_ALLOWED, build_risk_decision_input, evaluate_risk_decision
from pm_bot.trading_core.risk_prep_config import (
    RISK_ENGINE_CONFIG_VERSION,
    build_default_risk_engine_config,
    validate_risk_engine_config,
)
from pm_bot.trading_core.real_wallet_connector_disabled_adapter import DISABLED_CONNECTOR_UNRESOLVED_BLOCKER_IDS
from pm_bot.trading_core.schemas import (
    ARTIFACT_DIR,
    GENERATED_AT,
    bullet_lines,
    clean_text,
    load_json_object,
    mapping_rows,
    normalize_path,
    trading_core_safety_summary,
    write_json,
    write_text,
)
from pm_bot.trading_core.signing_simulator import STATUS_DRY_RUN_RECEIPT_READY, simulate_signing_for_execution_request
from pm_bot.trading_core.wallet_execution_boundary import (
    STATUS_APPROVED_FOR_FUTURE_SIMULATION,
    build_execution_request_packet,
    build_risk_approved_action_packet,
)

CANARY_REPLAY_REPORT_CONTRACT = "pmbot_live_canary_replay_report.v1"
CANARY_ACCEPTANCE_MATRIX_CONTRACT = "pmbot_live_canary_acceptance_matrix.v1"
LIVE_CONNECTOR_BLOCKER_MATRIX_CONTRACT = "pmbot_live_connector_blocker_matrix.v1"
OPERATOR_LIVE_CANARY_CHECKLIST_CONTRACT = "pmbot_tiny_live_canary_operator_checklist.v1"
CANARY_GOVERNANCE_SUMMARY_CONTRACT = "pmbot_live_canary_governance_summary.v1"

REQUIRED_CANARY_REFERENCE_FIELDS = (
    ("source_evidence_ref", "MISSING_SOURCE_EVIDENCE_REF"),
    ("risk_decision_id", "MISSING_RISK_DECISION"),
    ("wallet_boundary_packet_id", "MISSING_WALLET_BOUNDARY_PACKET"),
    ("signing_simulator_receipt_id", "MISSING_SIGNING_SIMULATOR_RECEIPT"),
)
_BENIGN_REPLAY_VALIDATION_ERRORS = {
    "source_evidence_ref must be a non-empty string",
    "risk_decision_status must be a non-empty string",
}

ACCEPTANCE_CASE_IDS = (
    "all_required_artifacts_present",
    "missing_evidence",
    "stale_evidence",
    "source_gap_present",
    "missing_risk_decision",
    "risk_blocked",
    "kill_switch_enabled",
    "missing_wallet_boundary_packet",
    "wallet_boundary_blocked",
    "missing_signing_simulator_receipt",
    "signing_simulator_blocked",
    "missing_operator_dry_run_approval",
    "rejected_operator_approval",
    "expired_operator_approval",
    "forbidden_field_present",
    "approved_for_dry_run_only",
)

EXPECTED_ACCEPTANCE_RESULTS: dict[str, dict[str, Any]] = {
    "all_required_artifacts_present": {
        "expected_canary_status": CANARY_STATUS_NEEDS_OPERATOR_APPROVAL,
        "expected_reason_codes": ["DRY_RUN_OPERATOR_APPROVAL_REQUIRED"],
        "expected_dry_run_acceptance_status": DRY_RUN_ACCEPTANCE_BLOCKED,
    },
    "missing_evidence": {
        "expected_canary_status": CANARY_STATUS_BLOCKED,
        "expected_reason_codes": [
            "MISSING_SOURCE_EVIDENCE_REF",
            "EVIDENCE_NOT_FRESH",
            "SOURCE_GAP_PRESENT",
        ],
        "expected_dry_run_acceptance_status": DRY_RUN_ACCEPTANCE_BLOCKED,
    },
    "stale_evidence": {
        "expected_canary_status": CANARY_STATUS_BLOCKED,
        "expected_reason_codes": ["EVIDENCE_NOT_FRESH"],
        "expected_dry_run_acceptance_status": DRY_RUN_ACCEPTANCE_BLOCKED,
    },
    "source_gap_present": {
        "expected_canary_status": CANARY_STATUS_BLOCKED,
        "expected_reason_codes": ["SOURCE_GAP_PRESENT"],
        "expected_dry_run_acceptance_status": DRY_RUN_ACCEPTANCE_BLOCKED,
    },
    "missing_risk_decision": {
        "expected_canary_status": CANARY_STATUS_BLOCKED,
        "expected_reason_codes": ["MISSING_RISK_DECISION"],
        "expected_dry_run_acceptance_status": DRY_RUN_ACCEPTANCE_BLOCKED,
    },
    "risk_blocked": {
        "expected_canary_status": CANARY_STATUS_BLOCKED,
        "expected_reason_codes": [
            "RISK_DECISION_NOT_ALLOWED",
            "WALLET_BOUNDARY_PACKET_NOT_READY",
            "SIGNING_SIMULATOR_RECEIPT_NOT_READY",
            "PROPOSED_NOTIONAL_EXCEEDS_MAX_CANARY_NOTIONAL",
        ],
        "expected_dry_run_acceptance_status": DRY_RUN_ACCEPTANCE_BLOCKED,
    },
    "kill_switch_enabled": {
        "expected_canary_status": CANARY_STATUS_BLOCKED,
        "expected_reason_codes": [
            "RISK_DECISION_NOT_ALLOWED",
            "KILL_SWITCH_ENABLED",
            "WALLET_BOUNDARY_PACKET_NOT_READY",
            "SIGNING_SIMULATOR_RECEIPT_NOT_READY",
        ],
        "expected_dry_run_acceptance_status": DRY_RUN_ACCEPTANCE_BLOCKED,
    },
    "missing_wallet_boundary_packet": {
        "expected_canary_status": CANARY_STATUS_BLOCKED,
        "expected_reason_codes": ["MISSING_WALLET_BOUNDARY_PACKET", "KILL_SWITCH_ENABLED"],
        "expected_dry_run_acceptance_status": DRY_RUN_ACCEPTANCE_BLOCKED,
    },
    "wallet_boundary_blocked": {
        "expected_canary_status": CANARY_STATUS_BLOCKED,
        "expected_reason_codes": ["WALLET_BOUNDARY_PACKET_NOT_READY"],
        "expected_dry_run_acceptance_status": DRY_RUN_ACCEPTANCE_BLOCKED,
    },
    "missing_signing_simulator_receipt": {
        "expected_canary_status": CANARY_STATUS_BLOCKED,
        "expected_reason_codes": ["MISSING_SIGNING_SIMULATOR_RECEIPT"],
        "expected_dry_run_acceptance_status": DRY_RUN_ACCEPTANCE_BLOCKED,
    },
    "signing_simulator_blocked": {
        "expected_canary_status": CANARY_STATUS_BLOCKED,
        "expected_reason_codes": ["SIGNING_SIMULATOR_RECEIPT_NOT_READY"],
        "expected_dry_run_acceptance_status": DRY_RUN_ACCEPTANCE_BLOCKED,
    },
    "missing_operator_dry_run_approval": {
        "expected_canary_status": CANARY_STATUS_NEEDS_OPERATOR_APPROVAL,
        "expected_reason_codes": [
            "OPERATOR_APPROVAL_NOT_REQUESTED",
            "DRY_RUN_OPERATOR_APPROVAL_REQUIRED",
        ],
        "expected_dry_run_acceptance_status": DRY_RUN_ACCEPTANCE_BLOCKED,
    },
    "rejected_operator_approval": {
        "expected_canary_status": CANARY_STATUS_REJECTED,
        "expected_reason_codes": ["OPERATOR_APPROVAL_REJECTED"],
        "expected_dry_run_acceptance_status": DRY_RUN_ACCEPTANCE_BLOCKED,
    },
    "expired_operator_approval": {
        "expected_canary_status": CANARY_STATUS_BLOCKED,
        "expected_reason_codes": ["OPERATOR_APPROVAL_EXPIRED"],
        "expected_dry_run_acceptance_status": DRY_RUN_ACCEPTANCE_BLOCKED,
    },
    "forbidden_field_present": {
        "expected_canary_status": CANARY_STATUS_BLOCKED,
        "expected_reason_codes": [
            "PACKET_INVALID:forbidden canary field detected at $.order_payload",
            "FORBIDDEN_CANARY_FIELD_PRESENT",
        ],
        "expected_dry_run_acceptance_status": DRY_RUN_ACCEPTANCE_BLOCKED,
    },
    "approved_for_dry_run_only": {
        "expected_canary_status": CANARY_STATUS_DRY_RUN_READY,
        "expected_reason_codes": [],
        "expected_dry_run_acceptance_status": DRY_RUN_ACCEPTANCE_ACCEPTED,
    },
}

LIVE_CONNECTOR_BLOCKERS = (
    {
        "blocker_id": "PMBOT-LIVE-BLOCKER-001",
        "blocker_name": "real wallet connector absent",
        "severity": "critical",
        "required_future_task": "Design and review a real wallet connector interface in a separate operator-approved task.",
        "current_status": "absent",
        "why_it_blocks_live_execution": "No reviewed connector exists for balances, addresses, or operator-scoped wallet access.",
    },
    {
        "blocker_id": "PMBOT-LIVE-BLOCKER-002",
        "blocker_name": "secret handling policy absent or incomplete",
        "severity": "critical",
        "required_future_task": "Write a credential handling and redaction policy before any connector work.",
        "current_status": "absent",
        "why_it_blocks_live_execution": "Sensitive material cannot be requested, stored, redacted, or audited safely.",
    },
    {
        "blocker_id": "PMBOT-LIVE-BLOCKER-003",
        "blocker_name": "real signing adapter absent",
        "severity": "critical",
        "required_future_task": "Specify a reviewed signing adapter boundary without implementing signing in this task.",
        "current_status": "absent",
        "why_it_blocks_live_execution": "Current receipts are deterministic dry-run records only and cannot authorize anything.",
    },
    {
        "blocker_id": "PMBOT-LIVE-BLOCKER-004",
        "blocker_name": "order adapter absent",
        "severity": "critical",
        "required_future_task": "Define an order adapter contract and rejection-first tests in a separate future task.",
        "current_status": "absent",
        "why_it_blocks_live_execution": "No reviewed adapter exists for converting approved intents into executable requests.",
    },
    {
        "blocker_id": "PMBOT-LIVE-BLOCKER-005",
        "blocker_name": "authenticated endpoint policy absent",
        "severity": "critical",
        "required_future_task": "Create an endpoint allowlist, rate-limit, logging, and redaction policy before live connectors.",
        "current_status": "absent",
        "why_it_blocks_live_execution": "No policy defines which authenticated endpoints may be called or how calls are audited.",
    },
    {
        "blocker_id": "PMBOT-LIVE-BLOCKER-006",
        "blocker_name": "production kill switch not wired to real execution",
        "severity": "critical",
        "required_future_task": "Design a production kill-switch path and prove it blocks every future live execution adapter.",
        "current_status": "not_wired",
        "why_it_blocks_live_execution": "Current kill-switch checks guard local dry-run readiness only.",
    },
    {
        "blocker_id": "PMBOT-LIVE-BLOCKER-007",
        "blocker_name": "operator live approval flow absent",
        "severity": "critical",
        "required_future_task": "Build a separate dual-control operator approval flow for a tiny live canary proposal.",
        "current_status": "absent",
        "why_it_blocks_live_execution": "The existing approval record is dry-run-only and explicitly cannot authorize live execution.",
    },
    {
        "blocker_id": "PMBOT-LIVE-BLOCKER-008",
        "blocker_name": "post-trade audit absent",
        "severity": "critical",
        "required_future_task": "Define immutable post-trade audit records and operator review checks before any live attempt.",
        "current_status": "absent",
        "why_it_blocks_live_execution": "There is no live audit trail for requests, approvals, responses, or reconciliation.",
    },
    {
        "blocker_id": "PMBOT-LIVE-BLOCKER-009",
        "blocker_name": "real balance/exposure reconciliation absent",
        "severity": "critical",
        "required_future_task": "Design balance, exposure, and position reconciliation before any tiny live canary.",
        "current_status": "absent",
        "why_it_blocks_live_execution": "No trusted live balance or exposure check exists to prevent stale state from being used.",
    },
    {
        "blocker_id": "PMBOT-LIVE-BLOCKER-010",
        "blocker_name": "emergency halt procedure absent",
        "severity": "critical",
        "required_future_task": "Document and test an emergency halt procedure before connector implementation.",
        "current_status": "absent",
        "why_it_blocks_live_execution": "Operators have no validated live incident stop procedure or recovery checklist.",
    },
    {
        "blocker_id": "PMBOT-LIVE-BLOCKER-011",
        "blocker_category": "real_wallet_connector_disabled",
        "blocker_name": "real wallet connector explicitly disabled",
        "severity": "critical",
        "required_future_task": "Create a separate operator-approved task before any real wallet connector can move beyond disabled boundary status.",
        "current_status": "disabled",
        "why_it_blocks_live_execution": "The only connector-shaped adapter in this build is refusal-only and cannot access wallets.",
    },
    {
        "blocker_id": "PMBOT-LIVE-BLOCKER-012",
        "blocker_category": "secret_boundary_not_configured",
        "blocker_name": "secret boundary static policy only",
        "severity": "critical",
        "required_future_task": "Design and approve a live credential handling process in a separate task before any secret configuration exists.",
        "current_status": "static_policy_only",
        "why_it_blocks_live_execution": "This build validates packet shape only and does not configure, inspect, read, or store secrets.",
    },
    {
        "blocker_id": "PMBOT-LIVE-BLOCKER-013",
        "blocker_category": "authenticated_endpoint_boundary_missing",
        "blocker_name": "authenticated endpoint boundary missing",
        "severity": "critical",
        "required_future_task": "Define an authenticated endpoint boundary, allowlist, logging, and redaction policy in a separate future task.",
        "current_status": "missing",
        "why_it_blocks_live_execution": "No authenticated endpoint boundary exists, so endpoint calls remain blocked.",
    },
    {
        "blocker_id": "PMBOT-LIVE-BLOCKER-014",
        "blocker_category": "real_order_submission_disabled",
        "blocker_name": "real order submission disabled",
        "severity": "critical",
        "required_future_task": "Design a rejection-first order adapter contract in a future task without enabling submission.",
        "current_status": "disabled",
        "why_it_blocks_live_execution": "No real order adapter can submit, place, or send orders in this build.",
    },
    {
        "blocker_id": "PMBOT-LIVE-BLOCKER-015",
        "blocker_category": "live_operator_approval_not_implemented",
        "blocker_name": "live operator approval not implemented",
        "severity": "critical",
        "required_future_task": "Build dual-control live operator approval packets in a separate future task.",
        "current_status": "not_implemented",
        "why_it_blocks_live_execution": "Current approval artifacts are dry-run-only and cannot authorize live execution.",
    },
    {
        "blocker_id": "PMBOT-LIVE-BLOCKER-016",
        "blocker_category": "production_kill_switch_not_wired_to_live_adapter",
        "blocker_name": "production kill switch not wired to live adapter",
        "severity": "critical",
        "required_future_task": "Wire and test a production kill switch against any future live adapter boundary.",
        "current_status": "not_wired",
        "why_it_blocks_live_execution": "The existing kill-switch checks guard dry-run readiness and are not wired to a live adapter.",
    },
    {
        "blocker_id": "PMBOT-LIVE-BLOCKER-017",
        "blocker_category": "live_connector_audit_sink_not_finalized",
        "blocker_name": "live connector audit sink not finalized",
        "severity": "critical",
        "required_future_task": "Finalize immutable live connector audit records before any live connector implementation task.",
        "current_status": "not_finalized",
        "why_it_blocks_live_execution": "The disabled adapter can write local refusal audits only; no live audit sink exists.",
    },
    {
        "blocker_id": "PMBOT-LIVE-BLOCKER-018",
        "blocker_category": "tiny_live_canary_preflight_contract_review_only",
        "blocker_name": "tiny live canary preflight contract is review-only",
        "severity": "critical",
        "required_future_task": "Create a separate future gated task to convert review-only preflight into an approved proposal process.",
        "current_status": "review_only",
        "why_it_blocks_live_execution": "The preflight contract defines prerequisites but does not authorize or execute a canary.",
    },
    {
        "blocker_id": "PMBOT-LIVE-BLOCKER-019",
        "blocker_category": "manual_runbook_not_operator_executed",
        "blocker_name": "manual runbook not operator executed",
        "severity": "critical",
        "required_future_task": "Collect manual operator acknowledgement and evidence in a separate future gated task.",
        "current_status": "not_operator_executed",
        "why_it_blocks_live_execution": "The runbook is text-only and has not been executed as an operator approval workflow.",
    },
    {
        "blocker_id": "PMBOT-LIVE-BLOCKER-020",
        "blocker_category": "kill_switch_not_live_verified",
        "blocker_name": "kill switch not live verified",
        "severity": "critical",
        "required_future_task": "Design and verify a live kill-switch path against any future connector boundary.",
        "current_status": "requirements_defined_not_live_verified",
        "why_it_blocks_live_execution": "Current kill-switch requirements are defined but not wired to live execution.",
    },
    {
        "blocker_id": "PMBOT-LIVE-BLOCKER-021",
        "blocker_category": "live_canary_manual_approval_not_collected",
        "blocker_name": "live canary manual approval not collected",
        "severity": "critical",
        "required_future_task": "Collect separate dual-control live-canary approval in a future task after all technical blockers are cleared.",
        "current_status": "not_collected",
        "why_it_blocks_live_execution": "Operator review artifacts in this build are not live trading approvals.",
    },
    {
        "blocker_id": "PMBOT-LIVE-BLOCKER-022",
        "blocker_category": "live_canary_execution_adapter_disabled",
        "blocker_name": "live canary execution adapter disabled",
        "severity": "critical",
        "required_future_task": "Design a rejection-first execution adapter in a separate future task without enabling submission.",
        "current_status": "disabled",
        "why_it_blocks_live_execution": "No adapter exists that can execute a tiny canary, and this build must keep it that way.",
    },
    {
        "blocker_id": "PMBOT-LIVE-BLOCKER-023",
        "blocker_category": "live_canary_funding_not_configured",
        "blocker_name": "live canary funding not configured",
        "severity": "critical",
        "required_future_task": "Define funding, balance, reconciliation, and exposure checks in a separate future task.",
        "current_status": "not_configured",
        "why_it_blocks_live_execution": "No live funding source, balance check, or reconciliation path exists.",
    },
    {
        "blocker_id": "PMBOT-LIVE-BLOCKER-024",
        "blocker_category": "live_canary_market_selection_not_finalized",
        "blocker_name": "live canary market selection not finalized",
        "severity": "critical",
        "required_future_task": "Finalize a single market through a manual evidence process in a separate future gated task.",
        "current_status": "not_finalized",
        "why_it_blocks_live_execution": "No live market selection has been manually finalized for any executable canary.",
    },
    {
        "blocker_id": "PMBOT-LIVE-BLOCKER-025",
        "blocker_category": "operator_intent_packet_dry_run_only",
        "blocker_name": "operator intent packet is dry-run only",
        "severity": "critical",
        "required_future_task": "Create a separate future gated task before any operator intent can be considered for live-canary authorization.",
        "current_status": "dry_run_only",
        "why_it_blocks_live_execution": "The operator intent packet is a human acknowledgement artifact and cannot approve live execution.",
    },
    {
        "blocker_id": "PMBOT-LIVE-BLOCKER-026",
        "blocker_category": "operator_intent_not_live_approval",
        "blocker_name": "operator intent is not live approval",
        "severity": "critical",
        "required_future_task": "Build a separate dual-control live approval model after all technical blockers are cleared.",
        "current_status": "not_live_approval",
        "why_it_blocks_live_execution": "Operator intent records reviewed artifacts only and do not authorize trading.",
    },
    {
        "blocker_id": "PMBOT-LIVE-BLOCKER-027",
        "blocker_category": "operator_intent_acknowledgement_not_collected_for_live",
        "blocker_name": "operator intent acknowledgement not collected for live",
        "severity": "critical",
        "required_future_task": "Collect live-specific operator acknowledgement in a separate future task after live approval criteria exist.",
        "current_status": "not_collected_for_live",
        "why_it_blocks_live_execution": "Any acknowledgement in this build is dry-run review text only.",
    },
    {
        "blocker_id": "PMBOT-LIVE-BLOCKER-028",
        "blocker_category": "cryptographic_signing_still_unavailable",
        "blocker_name": "cryptographic signing still unavailable",
        "severity": "critical",
        "required_future_task": "Design and review a signing boundary in a separate task before any signing implementation exists.",
        "current_status": "unavailable",
        "why_it_blocks_live_execution": "No cryptographic, wallet, transaction, or order signing capability exists in this build.",
    },
    {
        "blocker_id": "PMBOT-LIVE-BLOCKER-029",
        "blocker_category": "live_canary_execution_still_disabled",
        "blocker_name": "live canary execution still disabled",
        "severity": "critical",
        "required_future_task": "Design a disabled-first live canary execution adapter in a future gated task.",
        "current_status": "disabled",
        "why_it_blocks_live_execution": "No code path may execute a live canary in this build.",
    },
    {
        "blocker_id": "PMBOT-LIVE-BLOCKER-030",
        "blocker_category": "live_canary_funding_still_not_configured",
        "blocker_name": "live canary funding still not configured",
        "severity": "critical",
        "required_future_task": "Define funding, balance, and exposure reconciliation in a separate future task.",
        "current_status": "not_configured",
        "why_it_blocks_live_execution": "No live funding configuration, balance source, or reconciliation path exists.",
    },
    {
        "blocker_id": "PMBOT-LIVE-BLOCKER-031",
        "blocker_category": "live_canary_order_adapter_still_disabled",
        "blocker_name": "live canary order adapter still disabled",
        "severity": "critical",
        "required_future_task": "Design an order adapter contract in a separate task without enabling order submission.",
        "current_status": "disabled",
        "why_it_blocks_live_execution": "No order adapter can submit, place, or transmit real orders.",
    },
    {
        "blocker_id": "PMBOT-LIVE-BLOCKER-032",
        "blocker_category": "readiness_evidence_bundle_review_only",
        "blocker_name": "readiness evidence bundle is review-only",
        "severity": "critical",
        "required_future_task": "Use the evidence bundle only as review input for a separate future gated task.",
        "current_status": "review_only",
        "why_it_blocks_live_execution": "The evidence bundle links artifacts but cannot authorize live execution.",
    },
    {
        "blocker_id": "PMBOT-LIVE-BLOCKER-033",
        "blocker_category": "readiness_evidence_bundle_not_live_approval",
        "blocker_name": "readiness evidence bundle is not live approval",
        "severity": "critical",
        "required_future_task": "Build a separate dual-control live approval flow after all live blockers are resolved.",
        "current_status": "not_live_approval",
        "why_it_blocks_live_execution": "Bundle review readiness is not operator approval for a live canary.",
    },
    {
        "blocker_id": "PMBOT-LIVE-BLOCKER-034",
        "blocker_category": "readiness_evidence_bundle_not_operator_executed",
        "blocker_name": "readiness evidence bundle not operator executed",
        "severity": "critical",
        "required_future_task": "Collect separate operator execution evidence in a future gated task.",
        "current_status": "not_operator_executed",
        "why_it_blocks_live_execution": "The bundle is generated locally and has not been executed as an operator workflow.",
    },
    {
        "blocker_id": "PMBOT-LIVE-BLOCKER-035",
        "blocker_category": "evidence_bundle_does_not_resolve_live_blockers",
        "blocker_name": "evidence bundle does not resolve live blockers",
        "severity": "critical",
        "required_future_task": "Resolve each live blocker in separately reviewed tasks before any live canary proposal.",
        "current_status": "blockers_unresolved",
        "why_it_blocks_live_execution": "The bundle summarizes unresolved blockers without reducing their severity.",
    },
    {
        "blocker_id": "PMBOT-LIVE-BLOCKER-036",
        "blocker_category": "live_canary_execution_still_disabled",
        "blocker_name": "live canary execution still disabled",
        "severity": "critical",
        "required_future_task": "Design a disabled-first live canary execution adapter in a future gated task.",
        "current_status": "disabled",
        "why_it_blocks_live_execution": "No code path may execute a live canary in this build.",
    },
    {
        "blocker_id": "PMBOT-LIVE-BLOCKER-037",
        "blocker_category": "live_canary_real_funding_still_not_configured",
        "blocker_name": "live canary real funding still not configured",
        "severity": "critical",
        "required_future_task": "Define funding, balance, and exposure reconciliation in a separate future task.",
        "current_status": "not_configured",
        "why_it_blocks_live_execution": "No live funding configuration, balance source, or reconciliation path exists.",
    },
    {
        "blocker_id": "PMBOT-LIVE-BLOCKER-038",
        "blocker_category": "live_canary_order_adapter_still_disabled",
        "blocker_name": "live canary order adapter still disabled after evidence bundle",
        "severity": "critical",
        "required_future_task": "Design an order adapter contract in a separate task without enabling order submission.",
        "current_status": "disabled",
        "why_it_blocks_live_execution": "No order adapter can submit, place, or transmit real orders.",
    },
)


def replay_canary_readiness_decision(packet: Mapping[str, Any]) -> dict[str, Any]:
    reason_codes: list[str] = []
    missing_references: list[str] = []
    valid_packet, packet_errors = validate_canary_readiness_packet(packet)
    if not valid_packet:
        reason_codes.extend(
            f"PACKET_INVALID:{error}" for error in packet_errors if error not in _BENIGN_REPLAY_VALIDATION_ERRORS
        )
    for field, reason in REQUIRED_CANARY_REFERENCE_FIELDS:
        if not clean_text(packet.get(field)):
            _append_reason(reason_codes, reason)
            missing_references.append(field)

    risk_status = clean_text(packet.get("risk_decision_status"))
    if risk_status and risk_status != DECISION_ALLOWED:
        _append_reason(reason_codes, "RISK_DECISION_NOT_ALLOWED")
    if clean_text(packet.get("kill_switch_status")).lower() != "disabled":
        _append_reason(reason_codes, "KILL_SWITCH_ENABLED")
    if clean_text(packet.get("evidence_freshness_status")).lower() not in {"fresh", "fresh_enough", "covered_with_local_evidence"}:
        _append_reason(reason_codes, "EVIDENCE_NOT_FRESH")
    if clean_text(packet.get("source_gap_status")).lower() not in {"no_gap", "no_gaps", "covered", "covered_with_local_evidence"}:
        _append_reason(reason_codes, "SOURCE_GAP_PRESENT")

    wallet_status = clean_text(packet.get("wallet_boundary_status"))
    if wallet_status and wallet_status != STATUS_APPROVED_FOR_FUTURE_SIMULATION:
        _append_reason(reason_codes, "WALLET_BOUNDARY_PACKET_NOT_READY")
    signing_status = clean_text(packet.get("signing_simulator_receipt_status"))
    if signing_status and signing_status != STATUS_DRY_RUN_RECEIPT_READY:
        _append_reason(reason_codes, "SIGNING_SIMULATOR_RECEIPT_NOT_READY")

    approval_status = clean_text(packet.get("operator_approval_status"))
    if not clean_text(packet.get("operator_approval_record_id")):
        _append_reason(reason_codes, "OPERATOR_APPROVAL_NOT_REQUESTED")
    if approval_status == APPROVAL_REJECTED:
        _append_reason(reason_codes, "OPERATOR_APPROVAL_REJECTED")
    elif approval_status == APPROVAL_EXPIRED:
        _append_reason(reason_codes, "OPERATOR_APPROVAL_EXPIRED")
    elif approval_status != APPROVAL_DRY_RUN_ONLY:
        _append_reason(reason_codes, "DRY_RUN_OPERATOR_APPROVAL_REQUIRED")

    proposed = _number_or_none(packet.get("proposed_notional_usd"))
    max_canary = _number_or_none(packet.get("max_canary_notional_usd"))
    if proposed is None:
        _append_reason(reason_codes, "MISSING_PROPOSED_NOTIONAL_USD")
    elif proposed < 0:
        _append_reason(reason_codes, "PROPOSED_NOTIONAL_NEGATIVE")
    if max_canary is None:
        _append_reason(reason_codes, "MISSING_MAX_CANARY_NOTIONAL_USD")
    elif max_canary < 0:
        _append_reason(reason_codes, "MAX_CANARY_NOTIONAL_NEGATIVE")
    elif proposed is not None and proposed > max_canary:
        _append_reason(reason_codes, "PROPOSED_NOTIONAL_EXCEEDS_MAX_CANARY_NOTIONAL")

    action_type = clean_text(packet.get("action_type")).lower()
    if action_type and "simulated" not in action_type and "proposed" not in action_type:
        _append_reason(reason_codes, "ACTION_TYPE_NOT_SIMULATED_OR_PROPOSED")

    forbidden_paths = scan_forbidden_fields(packet)
    if forbidden_paths:
        _append_reason(reason_codes, "FORBIDDEN_CANARY_FIELD_PRESENT")

    replayed_status = _replayed_canary_status(reason_codes, approval_status)
    return {
        "canary_status": replayed_status,
        "reason_codes": _dedupe(reason_codes),
        "missing_references": missing_references,
        "forbidden_field_paths": forbidden_paths,
        "dry_run_only": True,
        "live_execution_forbidden": True,
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


def build_canary_replay_report(
    *,
    packets: Sequence[Mapping[str, Any]],
    receipts: Sequence[Mapping[str, Any]] | None = None,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    receipt_by_canary_id = {
        clean_text(receipt.get("canary_id")): receipt for receipt in (receipts or []) if clean_text(receipt.get("canary_id"))
    }
    rows: list[dict[str, Any]] = []
    canary_ids: list[str] = []
    logical_keys: list[str] = []
    for index, packet in enumerate(packets):
        replay = replay_canary_readiness_decision(packet)
        second_replay = replay_canary_readiness_decision(packet)
        replayed_receipt = build_canary_dry_run_acceptance_receipt(_packet_with_replayed_status(packet, replay), generated_at=generated_at)
        second_replayed_receipt = build_canary_dry_run_acceptance_receipt(
            _packet_with_replayed_status(packet, second_replay),
            generated_at=generated_at,
        )
        canary_id = clean_text(packet.get("canary_id"))
        logical_key = _logical_key(packet)
        stored_receipt = receipt_by_canary_id.get(canary_id, {})
        expected_reason_codes = _dedupe(str(item) for item in packet.get("reason_codes", []))
        actual_reason_codes = list(replay["reason_codes"])
        reason_code_drift = sorted(expected_reason_codes) != sorted(actual_reason_codes)
        status_drift = clean_text(packet.get("canary_status")) != clean_text(replay.get("canary_status"))
        receipt_status_drift = False
        if stored_receipt:
            receipt_status_drift = clean_text(stored_receipt.get("acceptance_status")) != clean_text(
                replayed_receipt.get("acceptance_status")
            )
        deterministic = _logical_replay_signature(replay, replayed_receipt) == _logical_replay_signature(
            second_replay,
            second_replayed_receipt,
        )
        rows.append(
            {
                "row_index": index,
                "canary_id": canary_id,
                "logical_key": logical_key,
                "expected_canary_status": clean_text(packet.get("canary_status")),
                "actual_canary_status": clean_text(replay.get("canary_status")),
                "expected_reason_codes": expected_reason_codes,
                "actual_reason_codes": actual_reason_codes,
                "expected_dry_run_acceptance_status": clean_text(stored_receipt.get("acceptance_status")),
                "actual_dry_run_acceptance_status": clean_text(replayed_receipt.get("acceptance_status")),
                "status_drift": status_drift,
                "reason_code_drift": reason_code_drift,
                "receipt_status_drift": receipt_status_drift,
                "idempotency_passed": deterministic,
                "missing_references": list(replay.get("missing_references", [])),
                "forbidden_field_paths": list(replay.get("forbidden_field_paths", [])),
                "row_passed": not status_drift
                and not reason_code_drift
                and not receipt_status_drift
                and deterministic
                and not replay.get("missing_references")
                and not replay.get("forbidden_field_paths"),
            }
        )
        canary_ids.append(canary_id)
        logical_keys.append(logical_key)

    duplicate_canary_ids = _duplicates(canary_ids)
    duplicate_logical_keys = _duplicates(logical_keys)
    forbidden_paths = scan_forbidden_fields({"rows": rows})
    failed_rows = [row for row in rows if row.get("row_passed") is not True]
    report_passed = not failed_rows and not duplicate_canary_ids and not duplicate_logical_keys and not forbidden_paths
    return {
        "contract_version": CANARY_REPLAY_REPORT_CONTRACT,
        "generated_at": generated_at,
        "packet_count": len(rows),
        "receipt_count": len(receipts or []),
        "passed": report_passed,
        "status": "passed" if report_passed else "failed",
        "status_drift_count": len([row for row in rows if row.get("status_drift") is True]),
        "reason_code_drift_count": len([row for row in rows if row.get("reason_code_drift") is True]),
        "receipt_status_drift_count": len([row for row in rows if row.get("receipt_status_drift") is True]),
        "missing_reference_count": sum(len(row.get("missing_references", [])) for row in rows),
        "duplicate_canary_ids": duplicate_canary_ids,
        "duplicate_logical_keys": duplicate_logical_keys,
        "forbidden_field_paths": forbidden_paths,
        "rows": rows,
        "dry_run_only": True,
        "live_execution_forbidden": True,
        "live_execution_available": False,
        "live_execution_allowed": False,
        "external_api_calls_performed": False,
        "outcome_resolution_invented": False,
        "pnl_invented": False,
        "safety_summary": trading_core_safety_summary(),
    }


def build_canary_acceptance_matrix(*, generated_at: str = GENERATED_AT) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for case_id in ACCEPTANCE_CASE_IDS:
        artifacts = build_canary_acceptance_case_artifacts(case_id, generated_at=generated_at)
        packet = artifacts["packet"]
        replay = replay_canary_readiness_decision(packet)
        replayed_packet = _packet_with_replayed_status(packet, replay)
        receipt = build_canary_dry_run_acceptance_receipt(replayed_packet, generated_at=generated_at)
        expected = EXPECTED_ACCEPTANCE_RESULTS[case_id]
        expected_reason_codes = list(expected["expected_reason_codes"])
        actual_reason_codes = list(replay["reason_codes"])
        live_execution_forbidden = _live_execution_forbidden(packet, receipt)
        row_passed = (
            clean_text(expected["expected_canary_status"]) == clean_text(replay["canary_status"])
            and expected_reason_codes == actual_reason_codes
            and clean_text(expected["expected_dry_run_acceptance_status"])
            == clean_text(receipt.get("acceptance_status"))
            and live_execution_forbidden
        )
        rows.append(
            {
                "case_id": case_id,
                "case_name": case_id.replace("_", " "),
                "expected_canary_status": expected["expected_canary_status"],
                "actual_canary_status": clean_text(replay["canary_status"]),
                "expected_reason_codes": expected_reason_codes,
                "actual_reason_codes": actual_reason_codes,
                "dry_run_receipt_can_be_produced": receipt.get("acceptance_status") == DRY_RUN_ACCEPTANCE_ACCEPTED,
                "expected_dry_run_acceptance_status": expected["expected_dry_run_acceptance_status"],
                "actual_dry_run_acceptance_status": receipt.get("acceptance_status"),
                "live_execution_remains_forbidden": live_execution_forbidden,
                "forbidden_field_paths": list(replay.get("forbidden_field_paths", [])),
                "passed": row_passed,
            }
        )
    forbidden_paths = scan_forbidden_fields({"rows": rows})
    passed = all(row.get("passed") is True for row in rows) and not forbidden_paths
    return {
        "contract_version": CANARY_ACCEPTANCE_MATRIX_CONTRACT,
        "generated_at": generated_at,
        "case_count": len(rows),
        "passed_case_count": len([row for row in rows if row.get("passed") is True]),
        "failed_case_count": len([row for row in rows if row.get("passed") is not True]),
        "passed": passed,
        "status": "passed" if passed else "failed",
        "forbidden_field_paths": forbidden_paths,
        "rows": rows,
        "dry_run_only": True,
        "live_execution_forbidden": True,
        "live_execution_available": False,
        "live_execution_allowed": False,
        "external_api_calls_performed": False,
        "outcome_resolution_invented": False,
        "pnl_invented": False,
        "safety_summary": trading_core_safety_summary(),
    }


def build_canary_acceptance_case_artifacts(case_id: str, *, generated_at: str = GENERATED_AT) -> dict[str, Any]:
    if case_id not in ACCEPTANCE_CASE_IDS:
        raise ValueError(f"unknown canary acceptance case_id: {case_id}")

    approval_status = APPROVAL_DRY_RUN_ONLY
    include_approval = True
    source_ledger: Mapping[str, Any] | None = None
    source_freshness = "fresh"
    source_gap = "no_gap"
    include_risk = True
    include_wallet = True
    include_signing = True
    config_overrides: dict[str, Any] = {}
    input_overrides: dict[str, Any] = {}
    packet_mutator: Callable[[dict[str, Any]], None] | None = None
    artifact_mutator: Callable[[dict[str, Any]], None] | None = None

    if case_id == "all_required_artifacts_present":
        approval_status = APPROVAL_REQUESTED
    elif case_id == "missing_evidence":
        source_ledger = {}
    elif case_id == "stale_evidence":
        source_freshness = "stale"
    elif case_id == "source_gap_present":
        source_gap = "gaps_present"
    elif case_id == "missing_risk_decision":
        include_risk = False
    elif case_id == "risk_blocked":
        input_overrides["requested_notional_usd"] = 30.0
    elif case_id == "kill_switch_enabled":
        config_overrides["kill_switch_enabled"] = True
    elif case_id == "missing_wallet_boundary_packet":
        include_wallet = False
    elif case_id == "wallet_boundary_blocked":
        artifact_mutator = _mutate_wallet_boundary_blocked
    elif case_id == "missing_signing_simulator_receipt":
        include_signing = False
    elif case_id == "signing_simulator_blocked":
        artifact_mutator = _mutate_signing_simulator_blocked
    elif case_id == "missing_operator_dry_run_approval":
        include_approval = False
    elif case_id == "rejected_operator_approval":
        approval_status = APPROVAL_REJECTED
    elif case_id == "expired_operator_approval":
        approval_status = APPROVAL_EXPIRED
    elif case_id == "forbidden_field_present":
        packet_mutator = _mutate_forbidden_packet_field
    elif case_id == "approved_for_dry_run_only":
        approval_status = APPROVAL_DRY_RUN_ONLY

    artifacts = _canonical_acceptance_artifacts(
        config_overrides=config_overrides,
        input_overrides=input_overrides,
        source_ledger=source_ledger,
        source_freshness=source_freshness,
        source_gap=source_gap,
        include_risk=include_risk,
        include_wallet=include_wallet,
        include_signing=include_signing,
        include_approval=include_approval,
        approval_status=approval_status,
        generated_at=generated_at,
    )
    if artifact_mutator is not None:
        artifact_mutator(artifacts)
        artifacts["packet"] = _build_packet_from_artifacts(artifacts, generated_at=generated_at)
    if packet_mutator is not None:
        packet_mutator(artifacts["packet"])
    artifacts["canary_receipt"] = build_canary_dry_run_acceptance_receipt(
        _packet_with_replayed_status(artifacts["packet"], replay_canary_readiness_decision(artifacts["packet"])),
        generated_at=generated_at,
    )
    return artifacts


def build_live_connector_blocker_matrix(*, generated_at: str = GENERATED_AT) -> dict[str, Any]:
    blockers = []
    for row in LIVE_CONNECTOR_BLOCKERS:
        blocker = dict(row)
        blocker.setdefault("blocker_category", clean_text(blocker.get("blocker_name")).replace(" ", "_"))
        blocker.setdefault("resolution_status", "unresolved")
        blockers.append(blocker)
    critical_blockers = [row for row in blockers if row.get("severity") == "critical"]
    unresolved_blockers = [row for row in blockers if row.get("resolution_status") != "resolved"]
    resolved_blockers = [row for row in blockers if row.get("resolution_status") == "resolved"]
    required_categories_present = all(
        category in {clean_text(row.get("blocker_category")) for row in blockers}
        for category in DISABLED_CONNECTOR_UNRESOLVED_BLOCKER_IDS
    )
    report = {
        "contract_version": LIVE_CONNECTOR_BLOCKER_MATRIX_CONTRACT,
        "generated_at": generated_at,
        "blocker_count": len(blockers),
        "critical_blocker_count": len(critical_blockers),
        "unresolved_blocker_count": len(unresolved_blockers),
        "resolved_blocker_count": len(resolved_blockers),
        "all_blockers_unresolved": len(resolved_blockers) == 0,
        "required_disabled_connector_categories_present": required_categories_present,
        "blockers": blockers,
        "critical_blockers": [row["blocker_id"] for row in critical_blockers],
        "unresolved_blockers": [row["blocker_id"] for row in unresolved_blockers],
        "disabled_connector_blocker_categories": list(DISABLED_CONNECTOR_UNRESOLVED_BLOCKER_IDS),
        "current_live_connector_status": "blocked",
        "next_recommended_non_live_task": (
            "Build the live connector audit replay and operator approval packet as disabled/local artifacts only; "
            "do not wire wallet, signing, order, or authenticated endpoint code."
        ),
        "dry_run_only": True,
        "live_execution_forbidden": True,
        "live_execution_available": False,
        "live_execution_allowed": False,
        "external_api_calls_performed": False,
        "outcome_resolution_invented": False,
        "pnl_invented": False,
        "safety_summary": trading_core_safety_summary(),
    }
    forbidden_paths = scan_forbidden_fields(report)
    report["forbidden_field_paths"] = forbidden_paths
    report["passed"] = (
        not forbidden_paths
        and len(blockers) >= 10
        and len(resolved_blockers) == 0
        and required_categories_present
    )
    report["status"] = "passed" if report["passed"] else "failed"
    return report


def build_operator_live_canary_checklist(*, generated_at: str = GENERATED_AT) -> dict[str, Any]:
    checklist = {
        "contract_version": OPERATOR_LIVE_CANARY_CHECKLIST_CONTRACT,
        "generated_at": generated_at,
        "title": "PMBOT tiny live canary operator checklist",
        "current_status": "dry_run_only_live_execution_unavailable",
        "files_or_artifacts_that_must_exist": [
            "pm_bot/trading_core/artifacts/night_020_021/live_canary_readiness_packet.json",
            "pm_bot/trading_core/artifacts/night_020_021/live_canary_dry_run_acceptance_receipt.json",
            "pm_bot/trading_core/artifacts/night_020_021/live_canary_operator_approval_record.json",
            "pm_bot/trading_core/artifacts/night_020_021/public_evidence_refresh_ledger.json",
            "pm_bot/trading_core/artifacts/night_020_021/risk_engine_decision_ledger.json",
            "pm_bot/trading_core/artifacts/night_020_021/wallet_boundary_audit_ledger.json",
            "pm_bot/trading_core/artifacts/night_020_021/dry_run_execution_receipts.json",
            "pm_bot/trading_core/artifacts/night_020_021/live_canary_replay_report.json",
            "pm_bot/trading_core/artifacts/night_020_021/live_canary_acceptance_matrix.json",
            "pm_bot/trading_core/artifacts/night_020_021/live_connector_blocker_matrix.json",
            "pm_bot/trading_core/artifacts/night_020_021/tiny_live_canary_preflight_contract.json",
            "pm_bot/trading_core/artifacts/night_020_021/tiny_live_canary_manual_runbook.json",
            "pm_bot/trading_core/artifacts/night_020_021/live_canary_operator_intent_packet.json",
            "pm_bot/trading_core/artifacts/night_020_021/live_canary_readiness_evidence_bundle.json",
        ],
        "validations_that_must_pass": [
            "canary readiness dry-run packet validation",
            "canary replay report status passed",
            "canary acceptance matrix status passed",
            "live connector blocker matrix present with all blockers unresolved",
            "tiny live canary preflight contract validates as review-only",
            "manual runbook includes non-execution, kill-switch, abort, and evidence sections",
            "operator intent packet validates as dry-run human acknowledgement only",
            "readiness evidence bundle validates as review-only and not live approval",
            "forbidden field scan reports no unsafe field names in relevant PMBOT live-prep artifacts",
            "pytest pm_bot/tests",
            "python -m compileall pm_bot",
        ],
        "manual_approvals_required": [
            "dry-run-only operator approval record for the readiness packet",
            "dry-run-only operator intent acknowledgement packet for future review",
            "separate future operator approval for any live connector design work",
            "separate future operator approval for any real live canary proposal",
        ],
        "must_still_be_forbidden": [
            "real wallet access",
            "private key, seed phrase, mnemonic, or credential material access",
            "cryptographic signing",
            "real order placement",
            "authenticated endpoint calls",
            "external API calls from the dry-run suite",
            "autonomous live trading",
            "market recommendation as real trading advice",
            "invented market outcomes or PnL",
        ],
        "dry_run_only_command_or_runner_path": (
            "python -m pm_bot.trading_core.live_canary_replay_acceptance "
            "--packet pm_bot/trading_core/artifacts/night_020_021/live_canary_readiness_packet.json "
            "--receipt pm_bot/trading_core/artifacts/night_020_021/live_canary_dry_run_acceptance_receipt.json"
        ),
        "dry_run_only_assertion": "This checklist does not make live execution available.",
        "live_execution_available": False,
        "live_execution_allowed": False,
        "dry_run_only": True,
        "external_api_calls_performed": False,
        "outcome_resolution_invented": False,
        "pnl_invented": False,
    }
    forbidden_paths = scan_forbidden_fields(checklist)
    checklist["forbidden_field_paths"] = forbidden_paths
    checklist["passed"] = not forbidden_paths and checklist["live_execution_available"] is False
    checklist["status"] = "passed" if checklist["passed"] else "failed"
    return checklist


def build_canary_governance_summary(
    *,
    packet: Mapping[str, Any],
    receipt: Mapping[str, Any],
    audit_replay_result: Mapping[str, Any] | None = None,
    operator_approval_packet: Mapping[str, Any] | None = None,
    operator_intent_packet: Mapping[str, Any] | None = None,
    readiness_evidence_bundle: Mapping[str, Any] | None = None,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    replay_report = build_canary_replay_report(packets=[packet], receipts=[receipt], generated_at=generated_at)
    acceptance_matrix = build_canary_acceptance_matrix(generated_at=generated_at)
    blocker_matrix = build_live_connector_blocker_matrix(generated_at=generated_at)
    checklist = build_operator_live_canary_checklist(generated_at=generated_at)
    audit_replay = dict(audit_replay_result or {})
    operator_packet = dict(operator_approval_packet or {})
    operator_intent = dict(operator_intent_packet or {})
    evidence_bundle = dict(readiness_evidence_bundle or {})
    passed = (
        replay_report.get("passed") is True
        and acceptance_matrix.get("passed") is True
        and blocker_matrix.get("status") == "passed"
        and checklist.get("status") == "passed"
    )
    return {
        "contract_version": CANARY_GOVERNANCE_SUMMARY_CONTRACT,
        "generated_at": generated_at,
        "canary_replay_status": replay_report.get("status"),
        "canary_replay_passed": replay_report.get("passed"),
        "acceptance_matrix_status": acceptance_matrix.get("status"),
        "acceptance_matrix_passed": acceptance_matrix.get("passed"),
        "acceptance_matrix_case_count": acceptance_matrix.get("case_count"),
        "acceptance_matrix_failed_case_count": acceptance_matrix.get("failed_case_count"),
        "live_connector_blocker_count": blocker_matrix.get("blocker_count"),
        "unresolved_live_connector_blocker_count": blocker_matrix.get("unresolved_blocker_count"),
        "resolved_live_connector_blocker_count": blocker_matrix.get("resolved_blocker_count"),
        "all_live_connector_blockers_unresolved": blocker_matrix.get("all_blockers_unresolved"),
        "live_connector_blocker_ids": blocker_matrix.get("unresolved_blockers"),
        "critical_blockers": blocker_matrix.get("critical_blockers"),
        "critical_blocker_count": blocker_matrix.get("critical_blocker_count"),
        "next_recommended_non_live_task": blocker_matrix.get("next_recommended_non_live_task"),
        "operator_checklist_status": checklist.get("status"),
        "live_connector_audit_replay_status": clean_text(audit_replay.get("status") or "not_provided"),
        "operator_approval_packet_status": clean_text(operator_packet.get("operator_packet_status") or "not_provided"),
        "operator_review_ready": operator_packet.get("operator_review_ready") is True,
        "operator_intent_packet_status": clean_text(operator_intent.get("intent_packet_status") or "not_provided"),
        "operator_intent_packet_review_ready": operator_intent.get("operator_intent_packet_review_ready") is True,
        "operator_intent_is_not_live_approval": (
            operator_intent.get("operator_intent_is_not_live_approval") is True if operator_intent else True
        ),
        "operator_signed_intent_is_human_acknowledgement_only": (
            operator_intent.get("operator_signed_intent_is_human_acknowledgement_only") is True
            if operator_intent
            else True
        ),
        "readiness_evidence_bundle_status": clean_text(
            evidence_bundle.get("bundle_status") or evidence_bundle.get("readiness_evidence_bundle_status") or "not_provided"
        ),
        "readiness_evidence_bundle_review_ready": (
            evidence_bundle.get("evidence_bundle_review_ready") is True
            or evidence_bundle.get("readiness_evidence_bundle_review_ready") is True
        ),
        "readiness_evidence_bundle_is_not_live_approval": True,
        "evidence_item_count": int(evidence_bundle.get("evidence_item_count", 0) or 0),
        "missing_required_evidence_count": int(evidence_bundle.get("missing_required_evidence_count", 0) or 0),
        "tiny_live_canary_preflight_status": clean_text(
            dict(operator_packet.get("tiny_live_canary_preflight_summary", {})).get("preflight_result_status")
            or "not_provided"
        ),
        "manual_runbook_status": clean_text(
            dict(operator_packet.get("tiny_live_canary_preflight_summary", {})).get("manual_runbook_status")
            or "not_provided"
        ),
        "canary_executable_now": False,
        "operator_review_is_not_live_approval": (
            operator_packet.get("operator_review_is_not_live_approval") is True if operator_packet else True
        ),
        "dry_run_only_assertion": checklist.get("dry_run_only_assertion"),
        "passed": passed,
        "status": "passed" if passed else "failed",
        "dry_run_only": True,
        "live_execution_forbidden": True,
        "live_execution_available": False,
        "live_execution_approved": False,
        "real_execution_available": False,
        "live_connector_enabled": False,
        "live_execution_allowed": False,
        "external_api_calls_performed": False,
        "outcome_resolution_invented": False,
        "pnl_invented": False,
    }


def scan_relevant_canary_live_prep_artifacts(paths: Sequence[str | Path]) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for raw_path in paths:
        path = Path(raw_path)
        if not _is_relevant_canary_live_prep_artifact(path):
            continue
        if not path.exists():
            rows.append({"path": normalize_path(path), "status": "missing", "forbidden_field_paths": []})
            continue
        payload = load_json_object(path, label=f"canary live-prep artifact {path}")
        forbidden_paths = scan_forbidden_fields(payload)
        rows.append(
            {
                "path": normalize_path(path),
                "status": "failed" if forbidden_paths else "passed",
                "forbidden_field_paths": forbidden_paths,
            }
        )
    failed_rows = [row for row in rows if row.get("status") != "passed"]
    return {
        "artifact_count": len(rows),
        "failed_artifact_count": len(failed_rows),
        "passed": not failed_rows,
        "status": "passed" if not failed_rows else "failed",
        "rows": rows,
        "scanned_only_relevant_pmbot_live_prep_artifacts": True,
    }


def write_canary_replay_acceptance_artifacts(
    *,
    packet_paths: Sequence[str | Path],
    receipt_paths: Sequence[str | Path],
    out_replay_json_path: str | Path = ARTIFACT_DIR / "live_canary_replay_report.json",
    out_replay_md_path: str | Path = ARTIFACT_DIR / "live_canary_replay_report.md",
    out_acceptance_json_path: str | Path = ARTIFACT_DIR / "live_canary_acceptance_matrix.json",
    out_acceptance_md_path: str | Path = ARTIFACT_DIR / "live_canary_acceptance_matrix.md",
    out_blocker_json_path: str | Path = ARTIFACT_DIR / "live_connector_blocker_matrix.json",
    out_blocker_md_path: str | Path = ARTIFACT_DIR / "live_connector_blocker_matrix.md",
    out_checklist_json_path: str | Path = ARTIFACT_DIR / "tiny_live_canary_operator_checklist.json",
    out_checklist_md_path: str | Path = ARTIFACT_DIR / "tiny_live_canary_operator_checklist.md",
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    packets = [load_json_object(path, label="canary readiness packet") for path in packet_paths]
    receipts = [load_json_object(path, label="canary dry-run receipt") for path in receipt_paths]
    replay = build_canary_replay_report(packets=packets, receipts=receipts, generated_at=generated_at)
    acceptance = build_canary_acceptance_matrix(generated_at=generated_at)
    blockers = build_live_connector_blocker_matrix(generated_at=generated_at)
    checklist = build_operator_live_canary_checklist(generated_at=generated_at)
    write_json(out_replay_json_path, replay)
    write_text(out_replay_md_path, render_canary_replay_report_markdown(replay))
    write_json(out_acceptance_json_path, acceptance)
    write_text(out_acceptance_md_path, render_canary_acceptance_matrix_markdown(acceptance))
    write_json(out_blocker_json_path, blockers)
    write_text(out_blocker_md_path, render_live_connector_blocker_matrix_markdown(blockers))
    write_json(out_checklist_json_path, checklist)
    write_text(out_checklist_md_path, render_operator_live_canary_checklist_markdown(checklist))
    return {
        "replay_report": replay,
        "acceptance_matrix": acceptance,
        "live_connector_blocker_matrix": blockers,
        "operator_checklist": checklist,
        "paths": {
            "replay_json": normalize_path(out_replay_json_path),
            "replay_md": normalize_path(out_replay_md_path),
            "acceptance_json": normalize_path(out_acceptance_json_path),
            "acceptance_md": normalize_path(out_acceptance_md_path),
            "blocker_json": normalize_path(out_blocker_json_path),
            "blocker_md": normalize_path(out_blocker_md_path),
            "checklist_json": normalize_path(out_checklist_json_path),
            "checklist_md": normalize_path(out_checklist_md_path),
        },
    }


def render_canary_replay_report_markdown(report: Mapping[str, Any]) -> str:
    lines = [
        "# PMBOT Live Canary Replay Report",
        "",
        "- Deterministic dry-run replay only; no wallet, signing, order, authenticated endpoint, or network path is used.",
        f"- Status: `{report.get('status')}`",
        f"- Packets: {report.get('packet_count')}",
        f"- Status drift: {report.get('status_drift_count')}",
        f"- Reason-code drift: {report.get('reason_code_drift_count')}",
        f"- Missing references: {report.get('missing_reference_count')}",
        f"- Duplicate canary IDs: `{report.get('duplicate_canary_ids')}`",
        f"- Duplicate logical keys: `{report.get('duplicate_logical_keys')}`",
        "",
        "## Rows",
        "",
    ]
    for row in mapping_rows(report.get("rows")):
        lines.extend(
            [
                f"- `{row.get('canary_id')}` expected `{row.get('expected_canary_status')}` "
                f"actual `{row.get('actual_canary_status')}` passed `{str(row.get('row_passed')).lower()}`",
                f"  - expected reasons: `{', '.join(row.get('expected_reason_codes', []))}`",
                f"  - actual reasons: `{', '.join(row.get('actual_reason_codes', []))}`",
                f"  - missing refs: `{', '.join(row.get('missing_references', []))}`",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def render_canary_acceptance_matrix_markdown(matrix: Mapping[str, Any]) -> str:
    lines = [
        "# PMBOT Live Canary Dry-Run Acceptance Matrix",
        "",
        "- Static deterministic acceptance cases for dry-run readiness only.",
        f"- Status: `{matrix.get('status')}`",
        f"- Cases: {matrix.get('case_count')}",
        f"- Passed: {matrix.get('passed_case_count')}",
        f"- Failed: {matrix.get('failed_case_count')}",
        "",
        "## Cases",
        "",
    ]
    for row in mapping_rows(matrix.get("rows")):
        lines.extend(
            [
                f"- `{row.get('case_id')}` expected `{row.get('expected_canary_status')}` "
                f"actual `{row.get('actual_canary_status')}` passed `{str(row.get('passed')).lower()}`",
                f"  - expected reasons: `{', '.join(row.get('expected_reason_codes', []))}`",
                f"  - receipt can be produced: `{str(row.get('dry_run_receipt_can_be_produced')).lower()}`",
                f"  - live execution forbidden: `{str(row.get('live_execution_remains_forbidden')).lower()}`",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def render_live_connector_blocker_matrix_markdown(matrix: Mapping[str, Any]) -> str:
    lines = [
        "# PMBOT Live Connector Blocker Matrix",
        "",
        "- Real live execution remains unavailable. These blockers must be cleared in separate future tasks.",
        f"- Status: `{matrix.get('current_live_connector_status')}`",
        f"- Blockers: {matrix.get('blocker_count')}",
        f"- Critical blockers: {matrix.get('critical_blocker_count')}",
        f"- Unresolved blockers: {matrix.get('unresolved_blocker_count')}",
        f"- Resolved blockers: {matrix.get('resolved_blocker_count')}",
        f"- Next non-live task: {matrix.get('next_recommended_non_live_task')}",
        "",
        "## Blockers",
        "",
    ]
    for row in mapping_rows(matrix.get("blockers")):
        lines.extend(
            [
                f"- `{row.get('blocker_id')}` `{row.get('severity')}` {row.get('blocker_name')}",
                f"  - Category: `{row.get('blocker_category')}`",
                f"  - Resolution: `{row.get('resolution_status')}`",
                f"  - Current status: `{row.get('current_status')}`",
                f"  - Required future task: {row.get('required_future_task')}",
                f"  - Why it blocks: {row.get('why_it_blocks_live_execution')}",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def render_operator_live_canary_checklist_markdown(checklist: Mapping[str, Any]) -> str:
    lines = [
        "# PMBOT Tiny Live Canary Operator Checklist",
        "",
        "- Real live execution is still unavailable. This checklist is for future readiness review only.",
        f"- Current status: `{checklist.get('current_status')}`",
        f"- Dry-run assertion: {checklist.get('dry_run_only_assertion')}",
        "",
        "## Required Files",
        "",
        *bullet_lines(str(item) for item in checklist.get("files_or_artifacts_that_must_exist", [])),
        "",
        "## Required Validations",
        "",
        *bullet_lines(str(item) for item in checklist.get("validations_that_must_pass", [])),
        "",
        "## Manual Approvals",
        "",
        *bullet_lines(str(item) for item in checklist.get("manual_approvals_required", [])),
        "",
        "## Still Forbidden",
        "",
        *bullet_lines(str(item) for item in checklist.get("must_still_be_forbidden", [])),
        "",
        "## Dry-Run Command",
        "",
        f"`{checklist.get('dry_run_only_command_or_runner_path')}`",
    ]
    return "\n".join(lines).rstrip() + "\n"


def _canonical_acceptance_artifacts(
    *,
    config_overrides: Mapping[str, Any],
    input_overrides: Mapping[str, Any],
    source_ledger: Mapping[str, Any] | None,
    source_freshness: str,
    source_gap: str,
    include_risk: bool,
    include_wallet: bool,
    include_signing: bool,
    include_approval: bool,
    approval_status: str,
    generated_at: str,
) -> dict[str, Any]:
    config = _risk_config(generated_at=generated_at, **dict(config_overrides))
    decision = evaluate_risk_decision(_decision_input(**dict(input_overrides)), config)
    action_packet = build_risk_approved_action_packet(
        candidate=_candidate(),
        risk_decision=decision,
        risk_config=config,
        generated_at=generated_at,
    )
    wallet_packet = build_execution_request_packet(
        risk_approved_action_packet=action_packet,
        generated_at=generated_at,
    )
    signing_receipt = simulate_signing_for_execution_request(wallet_packet, generated_at=generated_at)
    strategy = _strategy_ledger(decision, generated_at=generated_at)
    artifacts = {
        "config": config,
        "decision": decision,
        "wallet_packet": wallet_packet,
        "signing_receipt": signing_receipt,
        "strategy_ledger": strategy,
        "source_ledger": source_ledger
        if source_ledger is not None
        else _source_ledger(freshness=source_freshness, gap_status=source_gap),
        "risk_ledger": {
            "ledger_id": "risk-engine-decision-ledger-canary-030",
            "run_id": "canary-acceptance-test-run",
            "run_date": "2026-05-11",
            "decisions": [decision] if include_risk else [],
        },
        "wallet_ledger": {
            "ledger_id": "wallet-boundary-audit-ledger-canary-030",
            "run_id": "canary-acceptance-test-run",
            "run_date": "2026-05-11",
            "execution_request_packets": [wallet_packet] if include_wallet else [],
        },
        "signing_ledger": {
            "ledger_id": "dry-run-execution-receipt-ledger-canary-030",
            "run_id": "canary-acceptance-test-run",
            "run_date": "2026-05-11",
            "receipts": [signing_receipt] if include_signing else [],
        },
        "approval": (
            build_canary_operator_approval_record(
                run_id="canary-acceptance-test-run",
                market_id="market-030",
                approval_status=approval_status,
                generated_at=generated_at,
            )
            if include_approval
            else None
        ),
    }
    artifacts["packet"] = _build_packet_from_artifacts(artifacts, generated_at=generated_at)
    return artifacts


def _build_packet_from_artifacts(artifacts: Mapping[str, Any], *, generated_at: str) -> dict[str, Any]:
    return build_canary_readiness_packet(
        paper_strategy_ledger=artifacts["strategy_ledger"],
        source_evidence_status=artifacts["source_ledger"],
        risk_decision_ledger=artifacts["risk_ledger"],
        wallet_boundary_audit_ledger=artifacts["wallet_ledger"],
        signing_simulator_receipt_ledger=artifacts["signing_ledger"],
        operator_approval_record=artifacts["approval"],
        run_context={
            "run_id": "canary-acceptance-test-run",
            "run_date": "2026-05-11",
            "tracked_markets": [_candidate()],
        },
        canary_market_id="market-030",
        generated_at=generated_at,
    )


def _risk_config(*, generated_at: str, **overrides: Any) -> dict[str, Any]:
    config = build_default_risk_engine_config(generated_at=generated_at)
    config.update(
        {
            "max_total_exposure_usd": 100.0,
            "max_market_exposure_usd": 50.0,
            "max_per_market_exposure_usd": 50.0,
            "max_single_action_notional_usd": 25.0,
            "kill_switch_enabled": False,
            "manual_approval_required": True,
            "require_fresh_evidence": True,
            "block_on_source_gap": True,
        }
    )
    config.update(overrides)
    if "max_market_exposure_usd" in overrides and "max_per_market_exposure_usd" not in overrides:
        config["max_per_market_exposure_usd"] = config["max_market_exposure_usd"]
    valid, errors = validate_risk_engine_config(config)
    if not valid:
        raise ValueError(f"invalid acceptance risk config: {'; '.join(errors)}")
    config["validation"] = {"valid": valid, "errors": errors}
    return config


def _decision_input(**overrides: Any) -> dict[str, Any]:
    value = build_risk_decision_input(
        run_id="canary-acceptance-test-run",
        market_id="market-030",
        intent_id="intent-030",
        hypothesis_id="hypothesis-030",
        action_type="proposed_canary_dry_run",
        requested_notional_usd=10.0,
        current_total_exposure_usd=0.0,
        current_market_exposure_usd=0.0,
        evidence_freshness_status="fresh",
        source_gap_status="no_gap",
        operator_approval_status="approved",
        config_version=RISK_ENGINE_CONFIG_VERSION,
    )
    value.update(overrides)
    return value


def _candidate() -> dict[str, Any]:
    return {
        "daily_run_id": "canary-acceptance-test-run",
        "run_date": "2026-05-11",
        "intent_id": "intent-030",
        "market_id": "market-030",
        "market_title": "Static acceptance fixture market",
        "market_slug": "static-acceptance-fixture-market",
        "hypothesis_id": "hypothesis-030",
        "paper_action_type": "simulated_entry",
        "intended_notional_usd": 10.0,
    }


def _source_ledger(*, freshness: str, gap_status: str) -> dict[str, Any]:
    return {
        "refresh_id": "source-refresh-canary-030",
        "run_id": "canary-acceptance-test-run",
        "run_date": "2026-05-11",
        "network_used": False,
        "external_api_calls_performed": False,
        "summary_counts": {
            "records": 1,
            "fresh_records": 1 if freshness == "fresh" else 0,
            "stale_records": 1 if freshness == "stale" else 0,
            "missing_source_reference_records": 1 if freshness == "missing" else 0,
            "missing_local_capture_records": 0,
            "unknown_freshness_records": 1 if freshness == "unknown" else 0,
        },
        "records": [
            {
                "record_id": "source-record-market-030",
                "market_id": "market-030",
                "freshness_status": freshness,
            }
        ],
        "quality_ledger": {
            "quality_ledger_id": "quality-ledger-canary-030",
            "summary_counts": {
                "markets_with_gaps": 0 if gap_status == "no_gap" else 1,
                "missing_evidence_gaps": 0 if gap_status == "no_gap" else 1,
            },
            "market_source_status": [
                {
                    "market_id": "market-030",
                    "gap_status": gap_status,
                    "fresh_count": 1 if freshness == "fresh" else 0,
                    "stale_count": 1 if freshness == "stale" else 0,
                    "unknown_freshness_count": 1 if freshness == "unknown" else 0,
                    "missing_source_reference_count": 1 if freshness == "missing" else 0,
                    "missing_local_capture_count": 0,
                }
            ],
        },
    }


def _strategy_ledger(decision: Mapping[str, Any], *, generated_at: str) -> dict[str, Any]:
    return {
        "contract_version": "pmbot_paper_strategy_evaluation_ledger.v1",
        "ledger_id": "paper-strategy-evaluation-ledger-canary-030",
        "generated_at": generated_at,
        "run_id": "canary-acceptance-test-run",
        "run_date": "2026-05-11",
        "records": [
            {
                "evaluation_record_id": "paper-strategy-eval-canary-market-030",
                "run_id": "canary-acceptance-test-run",
                "run_date": "2026-05-11",
                "market_id": "market-030",
                "market_title": "Static acceptance fixture market",
                "market_slug": "static-acceptance-fixture-market",
                "intent_id": "intent-030",
                "hypothesis_id": "hypothesis-030",
                "simulated_action_type": "simulated_entry",
                "risk_engine_decision": {
                    "risk_decision_id": decision.get("risk_decision_id", ""),
                    "audit_id": decision.get("audit_id", ""),
                    "decision": decision.get("decision", ""),
                    "reason_codes": decision.get("reason_codes", []),
                    "requested_notional_usd": decision.get("decision_input", {}).get("requested_notional_usd", 0),
                },
                "source_links": {
                    "analysis_artifact_path": "pm_bot/tests/fixtures/canary_030/analysis.json",
                    "evidence_artifact_paths": ["pm_bot/tests/fixtures/canary_030/source.json"],
                },
            }
        ],
        "record_count": 1,
        "idempotency": {"record_ids_unique": True},
        "paper_only": True,
        "analysis_only": True,
        "unresolved_pnl_not_invented": True,
    }


def _mutate_wallet_boundary_blocked(artifacts: dict[str, Any]) -> None:
    packet = copy.deepcopy(artifacts["wallet_ledger"]["execution_request_packets"][0])
    packet["packet_status"] = "blocked"
    packet["validation"] = dict(packet.get("validation", {}))
    packet["validation"]["status"] = "blocked"
    packet["validation"]["reason_codes"] = ["WALLET_BOUNDARY_FORCED_BLOCKED_FIXTURE"]
    artifacts["wallet_ledger"]["execution_request_packets"] = [packet]
    artifacts["wallet_packet"] = packet


def _mutate_signing_simulator_blocked(artifacts: dict[str, Any]) -> None:
    receipt = copy.deepcopy(artifacts["signing_ledger"]["receipts"][0])
    receipt["status"] = "blocked"
    receipt["blocked_reason"] = "SIGNING_SIMULATOR_FORCED_BLOCKED_FIXTURE"
    receipt["reason_codes"] = ["SIGNING_SIMULATOR_FORCED_BLOCKED_FIXTURE"]
    artifacts["signing_ledger"]["receipts"] = [receipt]
    artifacts["signing_receipt"] = receipt


def _mutate_forbidden_packet_field(packet: dict[str, Any]) -> None:
    packet["order_payload"] = {"fixture_only": True}


def _packet_with_replayed_status(packet: Mapping[str, Any], replay: Mapping[str, Any]) -> dict[str, Any]:
    value = dict(packet)
    value["canary_status"] = clean_text(replay.get("canary_status"))
    value["reason_codes"] = list(replay.get("reason_codes", []))
    value["blocked_reason_summary"] = list(replay.get("reason_codes", []))
    return value


def _replayed_canary_status(reason_codes: Sequence[str], approval_status: str) -> str:
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


def _logical_key(packet: Mapping[str, Any]) -> str:
    idempotency = packet.get("idempotency")
    if isinstance(idempotency, Mapping) and clean_text(idempotency.get("logical_key")):
        return clean_text(idempotency.get("logical_key"))
    return f"{clean_text(packet.get('run_id'))}:{clean_text(packet.get('market_id'))}"


def _logical_replay_signature(replay: Mapping[str, Any], receipt: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "canary_status": clean_text(replay.get("canary_status")),
        "reason_codes": list(replay.get("reason_codes", [])),
        "missing_references": list(replay.get("missing_references", [])),
        "forbidden_field_paths": list(replay.get("forbidden_field_paths", [])),
        "acceptance_status": clean_text(receipt.get("acceptance_status")),
        "receipt_reason_codes": list(receipt.get("reason_codes", [])),
    }


def _duplicates(values: Sequence[str]) -> list[str]:
    return sorted({value for value in values if value and values.count(value) > 1})


def _live_execution_forbidden(packet: Mapping[str, Any], receipt: Mapping[str, Any]) -> bool:
    unsafe_truths = (
        packet.get("live_execution_allowed"),
        packet.get("live_execution_enabled"),
        packet.get("live_execution_performed"),
        packet.get("real_wallet_used"),
        packet.get("private_key_used"),
        packet.get("real_signature_created"),
        packet.get("real_order_submitted"),
        packet.get("authenticated_endpoint_called"),
        packet.get("external_api_call_performed"),
        receipt.get("live_execution_allowed"),
        receipt.get("live_execution_enabled"),
        receipt.get("live_execution_performed"),
        receipt.get("real_wallet_used"),
        receipt.get("private_key_used"),
        receipt.get("real_signature_created"),
        receipt.get("real_order_submitted"),
        receipt.get("authenticated_endpoint_called"),
        receipt.get("external_api_call_performed"),
    )
    return all(value is False for value in unsafe_truths)


def _is_relevant_canary_live_prep_artifact(path: Path) -> bool:
    normalized = path.name.lower()
    relevant_names = (
        "live_canary_readiness_packet",
        "live_canary_dry_run_acceptance_receipt",
        "live_canary_operator_approval_record",
        "live_canary_replay_report",
        "live_canary_acceptance_matrix",
        "live_connector_blocker_matrix",
        "tiny_live_canary_operator_checklist",
        "tiny_live_canary_preflight_contract",
        "tiny_live_canary_manual_runbook",
        "tiny_live_canary_preflight_result",
        "live_canary_operator_intent_packet",
        "live_canary_readiness_evidence_bundle",
    )
    return normalized.endswith(".json") and any(name in normalized for name in relevant_names)


def _number_or_none(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return round(float(value), 2)
    try:
        return round(float(value), 2)
    except (TypeError, ValueError):
        return None


def _append_reason(reasons: list[str], reason: str) -> None:
    if reason and reason not in reasons:
        reasons.append(reason)


def _dedupe(values: Sequence[Any]) -> list[str]:
    result: list[str] = []
    for value in values:
        text = clean_text(value)
        if text and text not in result:
            result.append(text)
    return result


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build PMBOT live canary replay, acceptance, blocker, and checklist artifacts."
    )
    parser.add_argument(
        "--packet",
        action="append",
        default=[],
        help="Path to a live canary readiness packet JSON. May be passed more than once.",
    )
    parser.add_argument(
        "--receipt",
        action="append",
        default=[],
        help="Path to a live canary dry-run receipt JSON. May be passed more than once.",
    )
    parser.add_argument("--out-dir", default=str(ARTIFACT_DIR))
    args = parser.parse_args(argv)
    out_dir = Path(args.out_dir)
    packet_paths = args.packet or [ARTIFACT_DIR / "live_canary_readiness_packet.json"]
    receipt_paths = args.receipt or [ARTIFACT_DIR / "live_canary_dry_run_acceptance_receipt.json"]
    write_canary_replay_acceptance_artifacts(
        packet_paths=packet_paths,
        receipt_paths=receipt_paths,
        out_replay_json_path=out_dir / "live_canary_replay_report.json",
        out_replay_md_path=out_dir / "live_canary_replay_report.md",
        out_acceptance_json_path=out_dir / "live_canary_acceptance_matrix.json",
        out_acceptance_md_path=out_dir / "live_canary_acceptance_matrix.md",
        out_blocker_json_path=out_dir / "live_connector_blocker_matrix.json",
        out_blocker_md_path=out_dir / "live_connector_blocker_matrix.md",
        out_checklist_json_path=out_dir / "tiny_live_canary_operator_checklist.json",
        out_checklist_md_path=out_dir / "tiny_live_canary_operator_checklist.md",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
