from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

from pm_bot.trading_core.authenticated_polymarket_connector import (
    summarize_authenticated_connector_capability_report,
)
from pm_bot.trading_core.live_enablement_config import summarize_live_enablement_config_preflight
from pm_bot.trading_core.live_canary_replay_acceptance import build_live_connector_blocker_matrix
from pm_bot.trading_core.schemas import GENERATED_AT, bullet_lines, clean_text, mapping_rows, trading_core_safety_summary
from pm_bot.trading_core.secret_boundary_policy import (
    validate_secret_boundary_tiny_live_canary_gonogo_gate,
)

TINY_LIVE_CANARY_GONOGO_GATE_CONTRACT = "pmbot_tiny_live_canary_gonogo_gate.v1"
TINY_LIVE_CANARY_GONOGO_GATE_SUMMARY_CONTRACT = "pmbot_tiny_live_canary_gonogo_gate_summary.v1"
TINY_LIVE_CANARY_GONOGO_GATE_VALIDATION_CONTRACT = "pmbot_tiny_live_canary_gonogo_gate_validation.v1"

TASK_ID = (
    "ORCH-PMBOT-TRADING-MVP-042-TINY-LIVE-CANARY-MANUAL-EXECUTION-CHECKLIST-AND-FINAL-GO-NOGO-GATE"
)
SCHEMA_VERSION = "042.v1"
GATE_NAME = "tiny_live_canary_manual_execution_checklist_and_final_gonogo_gate"

STATUS_NO_GO_UNRESOLVED_BLOCKERS = "NO_GO_UNRESOLVED_BLOCKERS"
STATUS_READY_FOR_OPERATOR_REVIEW_ONLY = "READY_FOR_OPERATOR_REVIEW_ONLY"
STATUS_HARD_BLOCK_LIVE_EXECUTION_CLAIM = "HARD_BLOCK_LIVE_EXECUTION_CLAIM"
STATUS_NO_GO_INCOMPLETE_PACKET = "NO_GO_INCOMPLETE_PACKET"
FORBIDDEN_GO_STATUS = "GO_FOR_LIVE"

OVERALL_DECISION_NO_GO = "NO_GO"
DECISION_LEVEL_FINAL_MANUAL_REVIEW_ONLY = "FINAL_MANUAL_REVIEW_ONLY"

FORCED_FALSE_EXECUTION_FIELDS = (
    "final_live_enablement_present",
    "live_execution_approved",
    "allowed_for_live",
    "canary_executable_now",
    "order_submission_enabled",
    "authenticated_polymarket_enabled",
    "real_execution_available",
    "live_connector_enabled",
    "would_submit_order",
    "order_submitted",
    "real_order_submitted",
    "order_submission_claimed",
    "real_order_placement_performed",
    "authenticated_endpoint_enabled",
    "authenticated_endpoints_enabled",
    "authenticated_endpoint_called",
    "authenticated_endpoint_call_performed",
    "authenticated_endpoint_used",
    "signing_enabled",
    "cryptographic_signing_enabled",
    "cryptographic_signing_performed",
    "wallet_enabled",
    "wallet_signing_enabled",
    "wallet_signing_performed",
    "transaction_signing_performed",
    "wallet_used",
    "real_wallet_used",
    "private_key_used",
    "real_signature_created",
    "live_execution_allowed",
    "live_execution_enabled",
    "live_execution_performed",
    "execution_enabling",
    "execution_enabled",
    "live_action_exposed",
    "network_used",
    "external_api_calls_performed",
    "external_api_call_performed",
    "browser_automation_used",
    "scheduler_created",
    "daemon_created",
    "autonomous_trading_enabled",
)

MANUAL_EXECUTION_CHECKLIST_ITEMS = (
    (
        "confirm_target_btc_market",
        "Confirm target BTC market is exactly the intended market.",
    ),
    (
        "confirm_market_open_and_fresh",
        "Confirm the BTC market is open, unresolved, and based on fresh read-only data.",
    ),
    (
        "confirm_dry_run_intent_only",
        "Confirm the order intent is dry-run only and is not order submission.",
    ),
    (
        "confirm_tiny_order_notional",
        "Confirm max order notional remains tiny, currently 1 USD by policy.",
    ),
    (
        "confirm_tiny_daily_loss_cap",
        "Confirm daily loss cap remains tiny, currently 5 USD by policy.",
    ),
    (
        "confirm_tiny_total_exposure_cap",
        "Confirm total exposure cap remains tiny, currently 10 USD by policy.",
    ),
    (
        "confirm_one_market_only",
        "Confirm exactly one BTC market is in scope.",
    ),
    (
        "confirm_one_order_trade_per_day",
        "Confirm one order/trade per day remains the active policy.",
    ),
    (
        "confirm_kill_switch_manual_reachable",
        "Confirm a kill switch exists and is manually reachable.",
    ),
    (
        "confirm_no_scheduler_daemon_autonomy",
        "Confirm no scheduler, daemon, or autonomous live mode is active.",
    ),
    (
        "confirm_wallet_signing_order_submission_disabled",
        "Confirm wallet access, signing, and order submission are not enabled in this task.",
    ),
    (
        "confirm_credentials_never_displayed",
        "Confirm raw credentials are never displayed and only redacted status is used.",
    ),
    (
        "confirm_not_live_approval",
        "Confirm the operator understands this packet is not live approval.",
    ),
)

FINAL_PRE_LIVE_CHECKLIST_ITEMS = (
    (
        "future_task_required_for_live_enablement",
        "A separate future live-enabling task must explicitly approve any live execution path.",
    ),
    (
        "future_dual_control_approval_required",
        "Dual-control live operator approval must exist before any live canary.",
    ),
    (
        "future_credentials_verified_without_exposure",
        "Live credentials must be verified out-of-band without exposing raw values.",
    ),
    (
        "future_authenticated_endpoint_boundary_required",
        "Authenticated endpoint boundary and audit policy must be separately approved.",
    ),
    (
        "future_wallet_and_signing_boundary_required",
        "Wallet and signing boundaries must be separately approved and reviewed.",
    ),
    (
        "future_order_adapter_disabled_first_required",
        "Any future order adapter must start disabled-first and rejection-first.",
    ),
    (
        "future_kill_switch_live_verified_required",
        "Kill switch must be live-verified against any future adapter boundary.",
    ),
    (
        "future_blocker_matrix_zero_unresolved_required",
        "All live blockers must be resolved in separate reviewed tasks before live approval.",
    ),
)

GO_REQUIREMENTS = (
    "all live blockers resolved in separate operator-approved tasks",
    "explicit future live-enabling task completed",
    "dual-control human approval collected for live canary",
    "raw credentials remain undisclosed and operator-verified out-of-band",
    "authenticated endpoint boundary reviewed and approved",
    "wallet/signing boundary reviewed and approved",
    "disabled-first order adapter reviewed before any enabled path exists",
    "kill switch wired to live boundary and manually verified",
    "one-market, one-order/trade-per-day, tiny-notional risk limits confirmed",
)

OPERATOR_REQUIRED_ACTIONS = (
    "Review this final go/no-go packet as a non-executable artifact.",
    "Do not treat this packet as live approval.",
    "Do not submit orders, connect wallets, sign payloads, or call authenticated endpoints from this task.",
    "Resolve live blockers only through separate future operator-approved tasks.",
    "Use the next recommended task only to merge this review-only gate, not to enable live trading.",
)


@dataclass(frozen=True)
class TinyLiveCanaryGoNoGoGate:
    packet_id: str
    task_id: str
    schema_version: str
    gate_name: str
    status: str
    overall_decision: str
    decision_level: str
    created_at: str
    generated_at: str
    market_id: str
    market_slug: str
    btc_market_snapshot_summary: Mapping[str, Any]
    btc_analysis_summary: Mapping[str, Any]
    dry_run_order_intent_summary: Mapping[str, Any]
    risk_limit_summary: Mapping[str, Any]
    auth_boundary_summary: Mapping[str, Any]
    order_submission_boundary_summary: Mapping[str, Any]
    operator_signed_intent_summary: Mapping[str, Any]
    readiness_evidence_summary: Mapping[str, Any]
    live_enablement_config_preflight_summary: Mapping[str, Any]
    authenticated_polymarket_connector_scaffold_summary: Mapping[str, Any]
    kill_switch_summary: Mapping[str, Any]
    blocker_matrix_summary: Mapping[str, Any]
    manual_execution_checklist: Mapping[str, Any]
    final_pre_live_checklist: Mapping[str, Any]
    go_requirements: tuple[str, ...]
    no_go_reasons: tuple[str, ...]
    unresolved_blockers: tuple[Mapping[str, Any], ...]
    operator_required_actions: tuple[str, ...]
    live_execution_violation_reasons: tuple[str, ...]
    input_secret_boundary_summary: Mapping[str, Any]

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = TINY_LIVE_CANARY_GONOGO_GATE_CONTRACT
        value["btc_market_snapshot_summary"] = dict(self.btc_market_snapshot_summary)
        value["btc_analysis_summary"] = dict(self.btc_analysis_summary)
        value["dry_run_order_intent_summary"] = dict(self.dry_run_order_intent_summary)
        value["risk_limit_summary"] = dict(self.risk_limit_summary)
        value["auth_boundary_summary"] = dict(self.auth_boundary_summary)
        value["order_submission_boundary_summary"] = dict(self.order_submission_boundary_summary)
        value["operator_signed_intent_summary"] = dict(self.operator_signed_intent_summary)
        value["readiness_evidence_summary"] = dict(self.readiness_evidence_summary)
        value["live_enablement_config_preflight_summary"] = dict(self.live_enablement_config_preflight_summary)
        value["authenticated_polymarket_connector_scaffold_summary"] = dict(
            self.authenticated_polymarket_connector_scaffold_summary
        )
        value["kill_switch_summary"] = dict(self.kill_switch_summary)
        value["blocker_matrix_summary"] = dict(self.blocker_matrix_summary)
        value["manual_execution_checklist"] = dict(self.manual_execution_checklist)
        value["final_pre_live_checklist"] = dict(self.final_pre_live_checklist)
        value["go_requirements"] = list(self.go_requirements)
        value["no_go_reasons"] = list(self.no_go_reasons)
        value["unresolved_blockers"] = [dict(row) for row in self.unresolved_blockers]
        value["operator_required_actions"] = list(self.operator_required_actions)
        value["live_execution_violation_reasons"] = list(self.live_execution_violation_reasons)
        value["input_secret_boundary_summary"] = dict(self.input_secret_boundary_summary)
        value["explicit_human_approval_required"] = True
        value["final_live_enablement_present"] = False
        value["live_execution_approved"] = False
        value["allowed_for_live"] = False
        value["canary_executable_now"] = False
        value["order_submission_enabled"] = False
        value["authenticated_polymarket_enabled"] = False
        value["real_execution_available"] = False
        value["live_connector_enabled"] = False
        value["go_for_live_status_emitted"] = False
        value["resolved_blocker_count"] = int(dict(self.blocker_matrix_summary).get("resolved_blocker_count", 0) or 0)
        value["unresolved_blocker_count"] = int(
            dict(self.blocker_matrix_summary).get("unresolved_blocker_count", 0) or 0
        )
        value["checklist_count"] = int(dict(self.manual_execution_checklist).get("item_count", 0) or 0)
        value["final_pre_live_checklist_count"] = int(
            dict(self.final_pre_live_checklist).get("item_count", 0) or 0
        )
        value["no_go_reason_count"] = len(self.no_go_reasons)
        value["operator_required_action_count"] = len(self.operator_required_actions)
        value["packet_complete_for_operator_review"] = _packet_complete_for_operator_review(value)
        value["safety_summary"] = trading_core_safety_summary()
        value.update(_gate_safety_flags())
        return value


def build_tiny_live_canary_gonogo_gate(
    *,
    market_id: str = "",
    market_slug: str = "",
    btc_market_snapshot_summary: Mapping[str, Any] | None = None,
    btc_analysis_summary: Mapping[str, Any] | None = None,
    dry_run_order_intent_summary: Mapping[str, Any] | None = None,
    risk_limit_summary: Mapping[str, Any] | None = None,
    auth_boundary_summary: Mapping[str, Any] | None = None,
    order_submission_boundary_summary: Mapping[str, Any] | None = None,
    operator_signed_intent_summary: Mapping[str, Any] | None = None,
    readiness_evidence_summary: Mapping[str, Any] | None = None,
    live_enablement_config_preflight_summary: Mapping[str, Any] | None = None,
    authenticated_polymarket_connector_scaffold_summary: Mapping[str, Any] | None = None,
    kill_switch_summary: Mapping[str, Any] | None = None,
    blocker_matrix: Mapping[str, Any] | None = None,
    blocker_matrix_summary: Mapping[str, Any] | None = None,
    latest_tiny_live_canary_gonogo_gate_path: str = "",
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    btc_market = _btc_market_snapshot_summary(btc_market_snapshot_summary)
    btc_analysis = _btc_analysis_summary(btc_analysis_summary)
    dry_run_intent = _dry_run_order_intent_summary(dry_run_order_intent_summary or btc_analysis_summary)
    risk_limits = _risk_limit_summary(risk_limit_summary)
    auth_boundary = _auth_boundary_summary(auth_boundary_summary)
    order_boundary = _order_submission_boundary_summary(order_submission_boundary_summary)
    operator_intent = _operator_signed_intent_summary(operator_signed_intent_summary)
    evidence = _readiness_evidence_summary(readiness_evidence_summary)
    live_config_preflight = _live_enablement_config_preflight_summary(live_enablement_config_preflight_summary)
    authenticated_connector = _authenticated_polymarket_connector_scaffold_summary(
        authenticated_polymarket_connector_scaffold_summary
    )
    kill_switch = _kill_switch_summary(kill_switch_summary)
    matrix = dict(blocker_matrix or {})
    if not matrix and blocker_matrix_summary is None:
        matrix = build_live_connector_blocker_matrix(generated_at=generated_at)
    blocker_summary = _blocker_matrix_summary(blocker_matrix_summary or matrix)
    blockers = tuple(_unresolved_blockers(matrix or blocker_summary))

    input_payload = {
        "btc_market_snapshot_summary": btc_market_snapshot_summary or {},
        "btc_analysis_summary": btc_analysis_summary or {},
        "dry_run_order_intent_summary": dry_run_order_intent_summary or {},
        "risk_limit_summary": risk_limit_summary or {},
        "auth_boundary_summary": auth_boundary_summary or {},
        "order_submission_boundary_summary": order_submission_boundary_summary or {},
        "operator_signed_intent_summary": operator_signed_intent_summary or {},
        "readiness_evidence_summary": readiness_evidence_summary or {},
        "live_enablement_config_preflight_summary": live_enablement_config_preflight_summary or {},
        "authenticated_polymarket_connector_scaffold_summary": (
            authenticated_polymarket_connector_scaffold_summary or {}
        ),
        "kill_switch_summary": kill_switch_summary or {},
        "blocker_matrix": blocker_matrix or {},
        "blocker_matrix_summary": blocker_matrix_summary or {},
    }
    live_violations = _live_execution_violation_reasons(input_payload)
    input_secret_summary = _input_secret_boundary_summary(input_payload, generated_at=generated_at)

    no_go_reasons = _no_go_reasons(
        live_execution_violation_reasons=live_violations,
        blocker_summary=blocker_summary,
        auth_boundary=auth_boundary,
        order_boundary=order_boundary,
        operator_intent=operator_intent,
        evidence=evidence,
        live_enablement_config_preflight=live_config_preflight,
        authenticated_polymarket_connector_scaffold=authenticated_connector,
        kill_switch=kill_switch,
    )
    manual_checklist = _manual_execution_checklist(
        market_id=clean_text(market_id) or clean_text(btc_market.get("market_id")) or clean_text(dry_run_intent.get("market_id")),
        market_slug=clean_text(market_slug)
        or clean_text(btc_market.get("market_slug"))
        or clean_text(dry_run_intent.get("market_slug")),
        risk_limits=risk_limits,
        generated_at=generated_at,
    )
    final_pre_live_checklist = _final_pre_live_checklist(generated_at=generated_at)
    status = _gate_status(
        live_execution_violation_reasons=live_violations,
        blocker_summary=blocker_summary,
        packet_complete=(
            manual_checklist.get("item_count", 0) > 0
            and final_pre_live_checklist.get("item_count", 0) > 0
            and bool(no_go_reasons)
        ),
    )
    packet_id = _stable_id(
        "tiny-live-canary-gonogo-gate-042",
        {
            "gate_name": GATE_NAME,
            "status": status,
            "market_id": clean_text(market_id) or btc_market.get("market_id") or dry_run_intent.get("market_id"),
            "market_slug": clean_text(market_slug) or btc_market.get("market_slug") or dry_run_intent.get("market_slug"),
            "unresolved_blocker_count": blocker_summary.get("unresolved_blocker_count"),
            "resolved_blocker_count": blocker_summary.get("resolved_blocker_count"),
            "violation_count": len(live_violations),
        },
    )
    packet = TinyLiveCanaryGoNoGoGate(
        packet_id=packet_id,
        task_id=TASK_ID,
        schema_version=SCHEMA_VERSION,
        gate_name=GATE_NAME,
        status=status,
        overall_decision=OVERALL_DECISION_NO_GO,
        decision_level=DECISION_LEVEL_FINAL_MANUAL_REVIEW_ONLY,
        created_at=generated_at,
        generated_at=generated_at,
        market_id=clean_text(market_id) or clean_text(btc_market.get("market_id")) or clean_text(dry_run_intent.get("market_id")),
        market_slug=clean_text(market_slug)
        or clean_text(btc_market.get("market_slug"))
        or clean_text(dry_run_intent.get("market_slug")),
        btc_market_snapshot_summary=btc_market,
        btc_analysis_summary=btc_analysis,
        dry_run_order_intent_summary=dry_run_intent,
        risk_limit_summary=risk_limits,
        auth_boundary_summary=auth_boundary,
        order_submission_boundary_summary=order_boundary,
        operator_signed_intent_summary=operator_intent,
        readiness_evidence_summary=evidence,
        live_enablement_config_preflight_summary=live_config_preflight,
        authenticated_polymarket_connector_scaffold_summary=authenticated_connector,
        kill_switch_summary=kill_switch,
        blocker_matrix_summary=blocker_summary,
        manual_execution_checklist=manual_checklist,
        final_pre_live_checklist=final_pre_live_checklist,
        go_requirements=GO_REQUIREMENTS,
        no_go_reasons=tuple(no_go_reasons),
        unresolved_blockers=blockers,
        operator_required_actions=OPERATOR_REQUIRED_ACTIONS,
        live_execution_violation_reasons=tuple(live_violations),
        input_secret_boundary_summary=input_secret_summary,
    ).to_dict()
    packet["latest_tiny_live_canary_gonogo_gate_path"] = clean_text(latest_tiny_live_canary_gonogo_gate_path)
    validation = validate_tiny_live_canary_gonogo_gate(packet, generated_at=generated_at)
    packet["validation"] = validation
    if validation.get("valid") is not True and packet["status"] == STATUS_READY_FOR_OPERATOR_REVIEW_ONLY:
        packet["status"] = STATUS_HARD_BLOCK_LIVE_EXECUTION_CLAIM
        packet["overall_decision"] = OVERALL_DECISION_NO_GO
        packet["validation"] = validate_tiny_live_canary_gonogo_gate(packet, generated_at=generated_at)
    return packet


def summarize_tiny_live_canary_gonogo_gate(
    packet: Mapping[str, Any] | None,
    *,
    latest_tiny_live_canary_gonogo_gate_path: str = "",
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    value = dict(packet or {})
    validation = (
        dict(value.get("validation", {}))
        if isinstance(value.get("validation"), Mapping)
        else validate_tiny_live_canary_gonogo_gate(value, generated_at=generated_at)
        if value
        else {"valid": False, "status": "blocked", "errors": ["go/no-go packet not provided"]}
    )
    checklist = dict(value.get("manual_execution_checklist", {}))
    final_checklist = dict(value.get("final_pre_live_checklist", {}))
    blockers = dict(value.get("blocker_matrix_summary", {}))
    live_config_preflight = dict(value.get("live_enablement_config_preflight_summary", {}))
    authenticated_connector = dict(value.get("authenticated_polymarket_connector_scaffold_summary", {}))
    summary = {
        "contract_version": TINY_LIVE_CANARY_GONOGO_GATE_SUMMARY_CONTRACT,
        "summary_id": _stable_id(
            "tiny-live-canary-gonogo-gate-summary-042",
            {
                "packet_id": value.get("packet_id"),
                "status": value.get("status"),
                "latest_path": clean_text(latest_tiny_live_canary_gonogo_gate_path),
            },
        ),
        "generated_at": generated_at,
        "packet_id": clean_text(value.get("packet_id")),
        "gate_name": clean_text(value.get("gate_name") or GATE_NAME),
        "status": clean_text(value.get("status") or "not_available"),
        "overall_decision": clean_text(value.get("overall_decision") or OVERALL_DECISION_NO_GO),
        "decision_level": clean_text(value.get("decision_level") or DECISION_LEVEL_FINAL_MANUAL_REVIEW_ONLY),
        "review_only_status": clean_text(value.get("status") or "not_available"),
        "market_id": clean_text(value.get("market_id")),
        "market_slug": clean_text(value.get("market_slug")),
        "manual_execution_checklist_count": int(checklist.get("item_count", 0) or 0),
        "manual_execution_checklist_pending_count": int(checklist.get("pending_operator_confirmation_count", 0) or 0),
        "final_pre_live_checklist_count": int(final_checklist.get("item_count", 0) or 0),
        "top_no_go_reasons": list(value.get("no_go_reasons", []))[:5],
        "no_go_reason_count": len(value.get("no_go_reasons", [])),
        "unresolved_blocker_count": int(blockers.get("unresolved_blocker_count", 0) or 0),
        "resolved_blocker_count": int(blockers.get("resolved_blocker_count", 0) or 0),
        "explicit_human_approval_required": True,
        "no_executable_action": True,
        "packet_complete_for_operator_review": value.get("packet_complete_for_operator_review") is True,
        "validation_status": clean_text(validation.get("status") or "blocked"),
        "validation_error_count": len(validation.get("errors", [])),
        "live_enablement_config_preflight_status": clean_text(
            live_config_preflight.get("status") or "not_available"
        ),
        "live_enablement_config_future_live_requested": (
            live_config_preflight.get("future_live_requested") is True
        ),
        "live_enablement_config_dry_run_review_allowed": (
            live_config_preflight.get("dry_run_review_allowed") is True
        ),
        "live_enablement_config_allowed_for_live": False,
        "authenticated_polymarket_connector_scaffold_status": clean_text(
            authenticated_connector.get("status") or "not_available"
        ),
        "authenticated_polymarket_connector_scaffold_review_only": (
            authenticated_connector.get("review_only") is not False
        ),
        "authenticated_polymarket_connector_network_calls_enabled": False,
        "authenticated_polymarket_connector_authenticated_calls_enabled": False,
        "authenticated_polymarket_connector_order_submission_enabled": False,
        "authenticated_polymarket_connector_real_execution_available": False,
        "latest_tiny_live_canary_gonogo_gate_path": clean_text(
            latest_tiny_live_canary_gonogo_gate_path
            or value.get("latest_tiny_live_canary_gonogo_gate_path")
        ),
    }
    summary.update(_gate_safety_flags())
    return summary


def validate_tiny_live_canary_gonogo_gate(
    packet: Mapping[str, Any],
    *,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    value = dict(packet or {})
    errors: list[str] = []
    statuses: list[str] = []
    if value.get("contract_version") != TINY_LIVE_CANARY_GONOGO_GATE_CONTRACT:
        errors.append(f"contract_version must be {TINY_LIVE_CANARY_GONOGO_GATE_CONTRACT}")
        statuses.append("invalid_contract")
    if clean_text(value.get("schema_version")) != SCHEMA_VERSION:
        errors.append(f"schema_version must be {SCHEMA_VERSION}")
        statuses.append("invalid_schema_version")
    if clean_text(value.get("gate_name")) != GATE_NAME:
        errors.append(f"gate_name must be {GATE_NAME}")
        statuses.append("invalid_gate_name")
    if clean_text(value.get("status")) == FORBIDDEN_GO_STATUS:
        errors.append("GO_FOR_LIVE is forbidden in task 042")
        statuses.append("forbidden_go_for_live_status")
    if clean_text(value.get("overall_decision")) != OVERALL_DECISION_NO_GO:
        errors.append("overall_decision must remain NO_GO")
        statuses.append("unsafe_overall_decision")
    if clean_text(value.get("decision_level")) != DECISION_LEVEL_FINAL_MANUAL_REVIEW_ONLY:
        errors.append("decision_level must be final manual review only")
        statuses.append("invalid_decision_level")
    if value.get("explicit_human_approval_required") is not True:
        errors.append("explicit_human_approval_required must be true")
        statuses.append("missing_human_approval_requirement")
    for field in FORCED_FALSE_EXECUTION_FIELDS:
        if value.get(field) is not False:
            errors.append(f"{field} must be false")
            statuses.append("unsafe_execution_flag_detected")
    for path, key, nested in _walk_flags(value):
        if key in FORCED_FALSE_EXECUTION_FIELDS and nested is not False:
            errors.append(f"{path}.{key} must be false")
            statuses.append("nested_unsafe_execution_flag_detected")
        if _looks_like_go_for_live(nested):
            errors.append(f"{path}.{key} must not contain GO_FOR_LIVE")
            statuses.append("forbidden_go_for_live_status")
    blocker_summary = dict(value.get("blocker_matrix_summary", {}))
    unresolved_count = int(blocker_summary.get("unresolved_blocker_count", 0) or 0)
    resolved_count = int(blocker_summary.get("resolved_blocker_count", 0) or 0)
    if unresolved_count <= 0 and value.get("status") == STATUS_NO_GO_UNRESOLVED_BLOCKERS:
        errors.append("NO_GO_UNRESOLVED_BLOCKERS requires unresolved blockers")
        statuses.append("missing_unresolved_blockers")
    if resolved_count != 0:
        errors.append("resolved_blocker_count must remain 0")
        statuses.append("resolved_blocker_detected")
    if value.get("status") == STATUS_READY_FOR_OPERATOR_REVIEW_ONLY and value.get("live_execution_approved") is not False:
        errors.append("operator review status cannot approve live execution")
        statuses.append("unsafe_operator_review_status")
    if value.get("go_for_live_status_emitted") is not False:
        errors.append("go_for_live_status_emitted must be false")
        statuses.append("forbidden_go_for_live_status")
    if value.get("packet_complete_for_operator_review") is not True:
        errors.append("packet_complete_for_operator_review must be true")
        statuses.append("incomplete_operator_review_packet")

    secret_validation = validate_secret_boundary_tiny_live_canary_gonogo_gate(value, generated_at=generated_at)
    if secret_validation.get("valid") is not True:
        errors.append("tiny live canary go/no-go packet violates static secret boundary")
        statuses.append("secret_boundary_blocked")

    valid = not errors
    if valid:
        statuses = ["tiny_live_canary_gonogo_gate_valid"]
    else:
        statuses = _dedupe(statuses)
    return {
        "contract_version": TINY_LIVE_CANARY_GONOGO_GATE_VALIDATION_CONTRACT,
        "validation_id": _stable_id(
            "tiny-live-canary-gonogo-gate-validation-042",
            {
                "packet_id": value.get("packet_id"),
                "status": value.get("status"),
                "errors": errors,
            },
        ),
        "generated_at": generated_at,
        "valid": valid,
        "status": "passed" if valid else "blocked",
        "statuses": statuses,
        "errors": errors,
        "secret_boundary_validation": secret_validation,
        "explicit_human_approval_required": True,
        "final_live_enablement_present": False,
        "live_execution_approved": False,
        "allowed_for_live": False,
        "canary_executable_now": False,
        "order_submission_enabled": False,
        "real_execution_available": False,
        "live_connector_enabled": False,
        "go_for_live_status_emitted": False,
    }


def render_tiny_live_canary_gonogo_gate_markdown(packet: Mapping[str, Any]) -> str:
    summary = summarize_tiny_live_canary_gonogo_gate(packet)
    lines = [
        "# Tiny Live Canary Go/No-Go Gate",
        "",
        f"- Packet: `{packet.get('packet_id')}`",
        f"- Status: `{packet.get('status')}`",
        f"- Decision: `{packet.get('overall_decision')}`",
        f"- Market: `{packet.get('market_id')}` / `{packet.get('market_slug')}`",
        f"- Explicit human approval required: `{str(packet.get('explicit_human_approval_required')).lower()}`",
        f"- Final live enablement present: `{str(packet.get('final_live_enablement_present')).lower()}`",
        f"- Live execution approved: `{str(packet.get('live_execution_approved')).lower()}`",
        f"- Canary executable now: `{str(packet.get('canary_executable_now')).lower()}`",
        f"- Order submission enabled: `{str(packet.get('order_submission_enabled')).lower()}`",
        f"- Unresolved blockers: `{summary.get('unresolved_blocker_count')}`",
        "",
        "## Top No-Go Reasons",
        "",
        *bullet_lines(str(item) for item in summary.get("top_no_go_reasons", [])),
        "",
        "## Operator Required Actions",
        "",
        *bullet_lines(str(item) for item in packet.get("operator_required_actions", [])),
    ]
    return "\n".join(lines) + "\n"


def _btc_market_snapshot_summary(summary: Mapping[str, Any] | None) -> dict[str, Any]:
    value = dict(summary or {})
    return {
        "market_id": clean_text(value.get("market_id")),
        "market_slug": clean_text(value.get("market_slug")),
        "market_title": clean_text(value.get("market_title")),
        "btc_market_connector_status": clean_text(value.get("btc_market_connector_status") or value.get("status")),
        "is_btc_related": value.get("is_btc_related") is True,
        "market_status": clean_text(value.get("market_status")),
        "is_open": value.get("is_open") is True,
        "is_resolved": value.get("is_resolved") is True,
        "stale": value.get("stale") is True,
        "snapshot_age_seconds": value.get("snapshot_age_seconds"),
        "risk_control_market_data_status": clean_text(value.get("risk_control_market_data_status")),
        "read_only_network_enabled": value.get("read_only_network_enabled") is True,
        "execution_enabling": False,
        "allowed_for_live": False,
        "live_execution_approved": False,
        "canary_executable_now": False,
    }


def _btc_analysis_summary(summary: Mapping[str, Any] | None) -> dict[str, Any]:
    value = dict(summary or {})
    return {
        "btc_market_analysis_status": clean_text(value.get("btc_market_analysis_status") or value.get("analysis_status")),
        "btc_intent_candidate_status": clean_text(value.get("btc_intent_candidate_status")),
        "analysis_is_not_live_recommendation": value.get("analysis_is_not_live_recommendation") is not False,
        "allowed_for_live": False,
        "execution_enabling": False,
        "live_execution_approved": False,
    }


def _dry_run_order_intent_summary(summary: Mapping[str, Any] | None) -> dict[str, Any]:
    value = dict(summary or {})
    return {
        "dry_run_order_intent_status": clean_text(value.get("dry_run_order_intent_status")),
        "intent_market_id": clean_text(value.get("intent_market_id") or value.get("market_id")),
        "intent_market_slug": clean_text(value.get("intent_market_slug") or value.get("market_slug")),
        "market_id": clean_text(value.get("intent_market_id") or value.get("market_id")),
        "market_slug": clean_text(value.get("intent_market_slug") or value.get("market_slug")),
        "intent_notional_usd": value.get("intent_notional_usd") or value.get("notional_usd"),
        "intent_limit_price": value.get("intent_limit_price") or value.get("limit_price"),
        "risk_decision_status": clean_text(value.get("risk_decision_status")),
        "allowed_for_dry_run": value.get("allowed_for_dry_run") is True,
        "order_intent_is_not_order_submission": value.get("order_intent_is_not_order_submission") is not False,
        "allowed_for_live": False,
        "order_submission_enabled": False,
        "would_submit_order": False,
        "execution_enabling": False,
        "live_execution_approved": False,
        "canary_executable_now": False,
    }


def _risk_limit_summary(summary: Mapping[str, Any] | None) -> dict[str, Any]:
    value = dict(summary or {})
    return {
        "risk_control_plane_status": clean_text(
            value.get("risk_control_plane_status") or value.get("status") or "not_available"
        ),
        "policy_id": clean_text(value.get("policy_id")),
        "mode": clean_text(value.get("mode") or "dry_run"),
        "max_order_notional_usd": value.get("max_order_notional_usd"),
        "max_daily_loss_usd": value.get("max_daily_loss_usd"),
        "max_total_exposure_usd": value.get("max_total_exposure_usd"),
        "max_market_exposure_usd": value.get("max_market_exposure_usd"),
        "max_active_markets": value.get("max_active_markets") or value.get("max_market_count"),
        "max_orders_per_day": value.get("max_orders_per_day") or value.get("max_order_count"),
        "max_trades_per_day": value.get("max_trades_per_day"),
        "risk_limits_enforced_for_order_intents": value.get("risk_limits_enforced_for_order_intents") is True,
        "allowed_for_dry_run": value.get("allowed_for_dry_run") is True,
        "allowed_for_live": False,
        "live_execution_approved": False,
        "canary_executable_now": False,
        "real_execution_available": False,
        "live_connector_enabled": False,
        "order_submission_enabled": False,
    }


def _auth_boundary_summary(summary: Mapping[str, Any] | None) -> dict[str, Any]:
    value = dict(summary or {})
    return {
        "live_credentials_boundary_status": clean_text(
            value.get("live_credentials_boundary_status") or value.get("decision_status") or "not_available"
        ),
        "live_credentials_configured": value.get("live_credentials_configured") is True,
        "redacted_credential_status_ready": value.get("redacted_credential_status_ready") is not False,
        "credential_statuses_redacted": value.get("credential_statuses_redacted") is not False,
        "secrets_redacted": value.get("secrets_redacted") is not False,
        "actual_secret_values_exposed": value.get("actual_secret_values_exposed") is True,
        "required_credentials_count": int(value.get("required_credentials_count", 0) or 0),
        "missing_credentials_count": int(value.get("missing_credentials_count", 0) or 0),
        "authenticated_endpoints_enabled": False,
        "signing_enabled": False,
        "cryptographic_signing_enabled": False,
        "wallet_signing_enabled": False,
        "order_submission_enabled": False,
        "allowed_for_live": False,
        "canary_executable_now": False,
        "live_execution_approved": False,
        "real_execution_available": False,
        "live_connector_enabled": False,
    }


def _order_submission_boundary_summary(summary: Mapping[str, Any] | None) -> dict[str, Any]:
    value = dict(summary or {})
    return {
        "status": clean_text(value.get("status") or "not_available"),
        "boundary_name": clean_text(value.get("boundary_name")),
        "dry_run_review_ready": value.get("dry_run_review_ready") is True
        or value.get("allowed_for_dry_run_review") is True,
        "market_id": clean_text(value.get("market_id")),
        "market_slug": clean_text(value.get("market_slug")),
        "authenticated_endpoint_required": value.get("authenticated_endpoint_required") is True,
        "signing_required_for_future_live": value.get("signing_required_for_future_live") is True,
        "wallet_required_for_future_live": value.get("wallet_required_for_future_live") is True,
        "would_submit_order": False,
        "order_submission_enabled": False,
        "authenticated_endpoint_enabled": False,
        "authenticated_endpoints_enabled": False,
        "signing_enabled": False,
        "cryptographic_signing_enabled": False,
        "wallet_enabled": False,
        "wallet_signing_enabled": False,
        "allowed_for_live": False,
        "live_execution_approved": False,
        "real_execution_available": False,
        "canary_executable_now": False,
        "live_connector_enabled": False,
        "top_refusal_reasons": list(value.get("top_refusal_reasons", []))[:5],
        "top_blocker_reasons": list(value.get("top_blocker_reasons", []))[:8],
        "boundary_is_not_live_approval": True,
        "receipt_is_not_order_submission": True,
    }


def _operator_signed_intent_summary(summary: Mapping[str, Any] | None) -> dict[str, Any]:
    value = dict(summary or {})
    return {
        "operator_intent_packet_status": clean_text(
            value.get("operator_intent_packet_status") or value.get("intent_packet_status") or "not_available"
        ),
        "operator_intent_packet_review_ready": value.get("operator_intent_packet_review_ready") is True,
        "operator_signed_intent_is_human_acknowledgement_only": (
            value.get("operator_signed_intent_is_human_acknowledgement_only") is not False
        ),
        "operator_intent_is_not_live_approval": value.get("operator_intent_is_not_live_approval") is not False,
        "explicit_human_approval_required": True,
        "live_execution_approved": False,
        "allowed_for_live": False,
        "canary_executable_now": False,
        "real_execution_available": False,
        "live_connector_enabled": False,
        "order_submission_enabled": False,
    }


def _readiness_evidence_summary(summary: Mapping[str, Any] | None) -> dict[str, Any]:
    value = dict(summary or {})
    return {
        "readiness_evidence_bundle_status": clean_text(
            value.get("readiness_evidence_bundle_status") or value.get("status") or "not_available"
        ),
        "readiness_evidence_bundle_review_ready": (
            value.get("readiness_evidence_bundle_review_ready") is True
            or value.get("evidence_bundle_review_ready") is True
        ),
        "readiness_evidence_bundle_is_not_live_approval": True,
        "evidence_item_count": int(value.get("evidence_item_count", 0) or 0),
        "missing_required_evidence_count": int(value.get("missing_required_evidence_count", 0) or 0),
        "unresolved_live_blocker_count": int(value.get("unresolved_live_blocker_count", 0) or 0),
        "live_execution_approved": False,
        "allowed_for_live": False,
        "canary_executable_now": False,
        "real_execution_available": False,
        "live_connector_enabled": False,
        "order_submission_enabled": False,
    }


def _kill_switch_summary(summary: Mapping[str, Any] | None) -> dict[str, Any]:
    value = dict(summary or {})
    return {
        "kill_switch_requirements_defined": value.get("kill_switch_requirements_defined") is True
        or value.get("requirements_defined") is True,
        "kill_switch_verified_for_live": False,
        "kill_switch_blocks_live_execution": value.get("kill_switch_blocks_live_execution") is not False,
        "emergency_stop_documented": value.get("emergency_stop_documented") is not False,
        "current_kill_switch_state": clean_text(value.get("current_kill_switch_state") or "blocks_live"),
        "live_execution_approved": False,
        "allowed_for_live": False,
        "canary_executable_now": False,
        "real_execution_available": False,
        "live_connector_enabled": False,
    }


def _live_enablement_config_preflight_summary(summary: Mapping[str, Any] | None) -> dict[str, Any]:
    value = summarize_live_enablement_config_preflight(summary)
    return {
        "status": clean_text(value.get("status") or "not_available"),
        "future_live_requested": value.get("future_live_requested") is True,
        "dry_run_review_allowed": value.get("dry_run_review_allowed") is True,
        "allowed_for_dry_run_review": value.get("allowed_for_dry_run_review") is True,
        "top_blocked_reasons": list(value.get("top_blocked_reasons", []))[:5],
        "violation_reasons": list(value.get("violation_reasons", []))[:5],
        "validation_status": clean_text(value.get("validation_status") or "blocked"),
        "latest_live_enablement_config_preflight_path": clean_text(
            value.get("latest_live_enablement_config_preflight_path")
        ),
        "review_only": True,
        "execution_enabling": False,
        "live_approval": False,
        "allowed_for_live": False,
        "canary_executable_now": False,
        "live_execution_approved": False,
        "real_execution_available": False,
        "live_connector_enabled": False,
        "order_submission_enabled": False,
        "authenticated_polymarket_enabled": False,
        "wallet_signing_enabled": False,
        "resolved_blocker_count": 0,
        "no_executable_action": True,
    }


def _authenticated_polymarket_connector_scaffold_summary(summary: Mapping[str, Any] | None) -> dict[str, Any]:
    value = summarize_authenticated_connector_capability_report(summary)
    return {
        "status": clean_text(value.get("status") or "REVIEW_ONLY"),
        "connector_name": clean_text(value.get("connector_name")),
        "review_only": True,
        "dry_run_only": True,
        "network_calls_enabled": False,
        "authenticated_calls_enabled": False,
        "live_connector_enabled": False,
        "order_submission_enabled": False,
        "signing_enabled": False,
        "cryptographic_signing_enabled": False,
        "wallet_signing_enabled": False,
        "real_execution_available": False,
        "allowed_for_live": False,
        "canary_executable_now": False,
        "live_execution_approved": False,
        "authenticated_polymarket_enabled": False,
        "execution_enabling": False,
        "live_approval": False,
        "resolved_blocker_count": 0,
        "no_executable_action": True,
        "top_blocked_reasons": list(value.get("top_blocked_reasons", []))[:5],
        "credentials_redacted_or_missing_only": (
            value.get("credentials_redacted_or_missing_only") is not False
        ),
        "latest_authenticated_polymarket_connector_scaffold_path": clean_text(
            value.get("latest_authenticated_polymarket_connector_scaffold_path")
        ),
    }


def _blocker_matrix_summary(summary: Mapping[str, Any] | None) -> dict[str, Any]:
    value = dict(summary or {})
    blockers = mapping_rows(value.get("blockers"))
    unresolved_ids = _clean_list(value.get("unresolved_blockers"))
    if blockers and not unresolved_ids:
        unresolved_ids = [
            clean_text(row.get("blocker_id"))
            for row in blockers
            if clean_text(row.get("resolution_status") or "unresolved") != "resolved"
        ]
    resolved_count = int(value.get("resolved_blocker_count", 0) or 0)
    unresolved_count = int(value.get("unresolved_blocker_count", 0) or len(unresolved_ids) or 0)
    blocker_count = int(value.get("blocker_count", 0) or len(blockers) or unresolved_count)
    return {
        "blocker_matrix_status": clean_text(value.get("status") or value.get("blocker_matrix_status") or "not_available"),
        "blocker_count": blocker_count,
        "critical_blocker_count": int(value.get("critical_blocker_count", 0) or blocker_count),
        "unresolved_blocker_count": unresolved_count,
        "resolved_blocker_count": resolved_count,
        "all_blockers_unresolved": resolved_count == 0 and unresolved_count > 0,
        "unresolved_blocker_ids": unresolved_ids,
        "live_execution_available": False,
        "allowed_for_live": False,
        "live_execution_approved": False,
        "real_execution_available": False,
        "canary_executable_now": False,
        "live_connector_enabled": False,
        "order_submission_enabled": False,
    }


def _manual_execution_checklist(
    *,
    market_id: str,
    market_slug: str,
    risk_limits: Mapping[str, Any],
    generated_at: str,
) -> dict[str, Any]:
    rows = []
    for item_id, label in MANUAL_EXECUTION_CHECKLIST_ITEMS:
        rows.append(
            {
                "item_id": item_id,
                "label": label,
                "market_id": market_id if item_id == "confirm_target_btc_market" else "",
                "market_slug": market_slug if item_id == "confirm_target_btc_market" else "",
                "required": True,
                "operator_confirmed": False,
                "status": "pending_manual_operator_review",
                "execution_enabling": False,
                "live_approval": False,
            }
        )
    counts = _checklist_counts(rows)
    return {
        "contract_version": "pmbot_tiny_live_canary_manual_execution_checklist.v1",
        "generated_at": generated_at,
        "item_count": counts["item_count"],
        "required_item_count": counts["required_item_count"],
        "operator_confirmed_count": counts["operator_confirmed_count"],
        "pending_operator_confirmation_count": counts["pending_operator_confirmation_count"],
        "max_order_notional_usd": risk_limits.get("max_order_notional_usd"),
        "max_daily_loss_usd": risk_limits.get("max_daily_loss_usd"),
        "max_total_exposure_usd": risk_limits.get("max_total_exposure_usd"),
        "max_active_markets": risk_limits.get("max_active_markets"),
        "max_orders_per_day": risk_limits.get("max_orders_per_day"),
        "max_trades_per_day": risk_limits.get("max_trades_per_day"),
        "items": rows,
        "review_only": True,
        "execution_enabling": False,
        "live_approval": False,
    }


def _final_pre_live_checklist(*, generated_at: str) -> dict[str, Any]:
    rows = [
        {
            "item_id": item_id,
            "label": label,
            "required": True,
            "operator_confirmed": False,
            "status": "future_task_required",
            "execution_enabling": False,
            "live_approval": False,
        }
        for item_id, label in FINAL_PRE_LIVE_CHECKLIST_ITEMS
    ]
    counts = _checklist_counts(rows)
    return {
        "contract_version": "pmbot_tiny_live_canary_final_pre_live_checklist.v1",
        "generated_at": generated_at,
        "item_count": counts["item_count"],
        "required_item_count": counts["required_item_count"],
        "operator_confirmed_count": counts["operator_confirmed_count"],
        "pending_operator_confirmation_count": counts["pending_operator_confirmation_count"],
        "items": rows,
        "review_only": True,
        "execution_enabling": False,
        "live_approval": False,
    }


def _no_go_reasons(
    *,
    live_execution_violation_reasons: Sequence[str],
    blocker_summary: Mapping[str, Any],
    auth_boundary: Mapping[str, Any],
    order_boundary: Mapping[str, Any],
    operator_intent: Mapping[str, Any],
    evidence: Mapping[str, Any],
    live_enablement_config_preflight: Mapping[str, Any],
    authenticated_polymarket_connector_scaffold: Mapping[str, Any],
    kill_switch: Mapping[str, Any],
) -> list[str]:
    reasons = []
    if live_execution_violation_reasons:
        reasons.append("input_claimed_live_execution_or_order_submission_enabled")
    if int(blocker_summary.get("unresolved_blocker_count", 0) or 0) > 0:
        reasons.append("live_blockers_remain_unresolved")
    if int(blocker_summary.get("resolved_blocker_count", 0) or 0) != 0:
        reasons.append("blocker_matrix_claims_resolved_blockers")
    if auth_boundary.get("authenticated_endpoints_enabled") is not False:
        reasons.append("authenticated_endpoints_claimed_enabled")
    if order_boundary.get("order_submission_enabled") is not False:
        reasons.append("order_submission_claimed_enabled")
    if operator_intent.get("operator_intent_is_not_live_approval") is not True:
        reasons.append("operator_intent_not_confirmed_as_non_live_approval")
    if evidence.get("readiness_evidence_bundle_is_not_live_approval") is not True:
        reasons.append("readiness_evidence_bundle_not_confirmed_as_non_live_approval")
    if live_enablement_config_preflight.get("allowed_for_live") is not False:
        reasons.append("live_enablement_config_claimed_allowed_for_live")
    if clean_text(live_enablement_config_preflight.get("status")) != "REVIEW_ONLY_PREFLIGHT_READY":
        reasons.append("live_enablement_config_preflight_not_review_only_ready")
    if authenticated_polymarket_connector_scaffold.get("review_only") is not True:
        reasons.append("authenticated_polymarket_connector_scaffold_not_review_only")
    if authenticated_polymarket_connector_scaffold.get("network_calls_enabled") is not False:
        reasons.append("authenticated_polymarket_connector_network_calls_claimed_enabled")
    if authenticated_polymarket_connector_scaffold.get("authenticated_calls_enabled") is not False:
        reasons.append("authenticated_polymarket_connector_authenticated_calls_claimed_enabled")
    if authenticated_polymarket_connector_scaffold.get("order_submission_enabled") is not False:
        reasons.append("authenticated_polymarket_connector_order_submission_claimed_enabled")
    if kill_switch.get("kill_switch_verified_for_live") is not False:
        reasons.append("kill_switch_claimed_live_verified")
    reasons.extend(
        [
            "explicit_future_live_enablement_task_not_present",
            "live_execution_approved_false",
            "canary_executable_now_false",
            "real_execution_available_false",
            "live_connector_enabled_false",
        ]
    )
    return _dedupe(reasons)


def _gate_status(
    *,
    live_execution_violation_reasons: Sequence[str],
    blocker_summary: Mapping[str, Any],
    packet_complete: bool,
) -> str:
    if live_execution_violation_reasons:
        return STATUS_HARD_BLOCK_LIVE_EXECUTION_CLAIM
    if int(blocker_summary.get("unresolved_blocker_count", 0) or 0) > 0:
        return STATUS_NO_GO_UNRESOLVED_BLOCKERS
    if packet_complete:
        return STATUS_READY_FOR_OPERATOR_REVIEW_ONLY
    return STATUS_NO_GO_INCOMPLETE_PACKET


def _unresolved_blockers(blocker_matrix: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows = mapping_rows(blocker_matrix.get("blockers"))
    if rows:
        return [
            {
                "blocker_id": clean_text(row.get("blocker_id")),
                "blocker_category": clean_text(row.get("blocker_category") or row.get("blocker_name")),
                "severity": clean_text(row.get("severity") or "critical"),
                "current_status": clean_text(row.get("current_status") or "unresolved"),
                "resolution_status": clean_text(row.get("resolution_status") or "unresolved"),
                "why_it_blocks_live_execution": clean_text(
                    row.get("why_it_blocks_live_execution") or row.get("message")
                ),
            }
            for row in rows
            if clean_text(row.get("resolution_status") or "unresolved") != "resolved"
        ]
    return [
        {
            "blocker_id": blocker_id,
            "blocker_category": blocker_id,
            "severity": "critical",
            "current_status": "unresolved",
            "resolution_status": "unresolved",
            "why_it_blocks_live_execution": "This blocker remains unresolved and blocks live execution.",
        }
        for blocker_id in _clean_list(blocker_matrix.get("unresolved_blocker_ids") or blocker_matrix.get("unresolved_blockers"))
    ]


def _input_secret_boundary_summary(payload: Mapping[str, Any], *, generated_at: str) -> dict[str, Any]:
    validation = validate_secret_boundary_tiny_live_canary_gonogo_gate(payload, generated_at=generated_at)
    return {
        "contract_version": "pmbot_tiny_live_canary_gonogo_input_secret_boundary_summary.v1",
        "generated_at": generated_at,
        "valid": validation.get("valid") is True,
        "status": clean_text(validation.get("status") or "blocked"),
        "forbidden_secret_field_count": int(validation.get("forbidden_secret_field_count", 0) or 0),
        "forbidden_secret_value_count": int(validation.get("forbidden_secret_value_count", 0) or 0),
        "forbidden_secret_field_paths": list(validation.get("forbidden_secret_field_paths", [])),
        "forbidden_secret_value_paths": list(validation.get("forbidden_secret_value_paths", [])),
        "environment_secrets_read": False,
        "secrets_read": False,
        "secrets_printed": False,
        "secrets_persisted": False,
        "raw_secret_values_printed": False,
        "raw_secret_values_persisted": False,
    }


def _live_execution_violation_reasons(payload: Mapping[str, Any]) -> list[str]:
    reasons = []
    for path, key, value in _walk_flags(payload):
        if key in FORCED_FALSE_EXECUTION_FIELDS and value is True:
            reasons.append(f"{path}.{key}=true")
        if _looks_like_go_for_live(value):
            reasons.append(f"{path}.{key}=GO_FOR_LIVE")
    return _dedupe(reasons)


def _packet_complete_for_operator_review(packet: Mapping[str, Any]) -> bool:
    return (
        clean_text(packet.get("packet_id")) != ""
        and clean_text(packet.get("gate_name")) == GATE_NAME
        and clean_text(packet.get("overall_decision")) == OVERALL_DECISION_NO_GO
        and int(packet.get("checklist_count", 0) or 0) == len(MANUAL_EXECUTION_CHECKLIST_ITEMS)
        and int(packet.get("final_pre_live_checklist_count", 0) or 0) == len(FINAL_PRE_LIVE_CHECKLIST_ITEMS)
        and bool(packet.get("go_requirements"))
        and bool(packet.get("no_go_reasons"))
        and bool(packet.get("operator_required_actions"))
        and packet.get("explicit_human_approval_required") is True
        and packet.get("final_live_enablement_present") is False
        and packet.get("live_execution_approved") is False
        and packet.get("allowed_for_live") is False
        and packet.get("canary_executable_now") is False
        and packet.get("order_submission_enabled") is False
        and packet.get("real_execution_available") is False
        and packet.get("live_connector_enabled") is False
    )


def _checklist_counts(rows: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    required = [row for row in rows if row.get("required") is True]
    confirmed = [row for row in rows if row.get("operator_confirmed") is True]
    return {
        "item_count": len(rows),
        "required_item_count": len(required),
        "operator_confirmed_count": len(confirmed),
        "pending_operator_confirmation_count": len(required) - len(confirmed),
    }


def _gate_safety_flags() -> dict[str, Any]:
    return {
        "local_artifact_only": True,
        "passive_artifact_only": True,
        "manual_review_only": True,
        "review_only": True,
        "dry_run_only": True,
        "paper_only": True,
        "execution_enabling": False,
        "live_approval": False,
        "environment_inspected": False,
        "environment_secrets_read": False,
        "secrets_read": False,
        "secrets_printed": False,
        "secrets_persisted": False,
        "network_used": False,
        "network_calls_enabled": False,
        "external_api_calls_performed": False,
        "external_api_call_performed": False,
        "authenticated_calls_enabled": False,
        "authenticated_endpoints_enabled": False,
        "authenticated_polymarket_enabled": False,
        "authenticated_endpoint_called": False,
        "authenticated_endpoint_call_performed": False,
        "real_wallet_integration_added": False,
        "real_wallet_access_performed": False,
        "wallet_enabled": False,
        "wallet_used": False,
        "real_wallet_used": False,
        "private_key_used": False,
        "private_key_or_mnemonic_handling_added": False,
        "cryptographic_signing_added": False,
        "cryptographic_signing_enabled": False,
        "cryptographic_signing_performed": False,
        "signing_enabled": False,
        "wallet_signing_added": False,
        "wallet_signing_enabled": False,
        "wallet_signing_performed": False,
        "transaction_signing_added": False,
        "transaction_signing_performed": False,
        "real_signature_created": False,
        "real_order_placement_added": False,
        "real_order_placement_performed": False,
        "real_order_submitted": False,
        "would_submit_order": False,
        "order_submitted": False,
        "order_submission_claimed": False,
        "order_submission_enabled": False,
        "authenticated_endpoint_enabled": False,
        "authenticated_endpoint_used": False,
        "browser_automation_added": False,
        "browser_automation_used": False,
        "scheduler_or_daemon_added": False,
        "scheduler_created": False,
        "daemon_created": False,
        "autonomous_live_trading_added": False,
        "autonomous_trading_enabled": False,
        "final_live_enablement_present": False,
        "allowed_for_live": False,
        "live_execution_approved": False,
        "live_connector_enabled": False,
        "live_execution_allowed": False,
        "live_execution_enabled": False,
        "live_execution_performed": False,
        "execution_enabled": False,
        "live_action_exposed": False,
        "real_execution_available": False,
        "canary_executable_now": False,
        "outcome_resolution_invented": False,
        "pnl_invented": False,
    }


def _walk_flags(value: Any, path: str = "$") -> list[tuple[str, str, Any]]:
    rows: list[tuple[str, str, Any]] = []
    if isinstance(value, Mapping):
        for key, nested in value.items():
            key_text = clean_text(key)
            rows.append((path, key_text, nested))
            rows.extend(_walk_flags(nested, f"{path}.{key_text}"))
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            rows.extend(_walk_flags(nested, f"{path}[{index}]"))
    return rows


def _looks_like_go_for_live(value: Any) -> bool:
    return clean_text(value).upper() == FORBIDDEN_GO_STATUS


def _clean_list(value: Any) -> list[str]:
    if isinstance(value, (list, tuple)):
        return [clean_text(item) for item in value if clean_text(item)]
    text = clean_text(value)
    return [text] if text else []


def _dedupe(values: Sequence[Any]) -> list[str]:
    rows: list[str] = []
    for value in values:
        text = clean_text(value)
        if text and text not in rows:
            rows.append(text)
    return rows


def _stable_id(prefix: str, payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]
    return f"{prefix}-{digest}"
