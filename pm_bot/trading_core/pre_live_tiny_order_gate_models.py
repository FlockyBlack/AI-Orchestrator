from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

from pm_bot.trading_core.schemas import GENERATED_AT, clean_text

TASK_ID = "ORCH-PMBOT-TRADING-MVP-062P-PRE-LIVE-TINY-ORDER-GATE-AND-OPERATOR-CHECKLIST-NO-SUBMISSION"

EXECUTION_MODE = "preflight"
MODE = "preflight / review-only"

PRE_LIVE_TINY_ORDER_GATE_CONFIG_CONTRACT = "pmbot_pre_live_tiny_order_gate_config_062p.v1"
PRE_LIVE_TINY_ORDER_CHECKLIST_CONTRACT = "pmbot_pre_live_tiny_order_checklist_062p.v1"
PRE_LIVE_TINY_ORDER_BLOCKER_CONTRACT = "pmbot_pre_live_tiny_order_blocker_062p.v1"
PRE_LIVE_TINY_ORDER_BLOCKERS_CONTRACT = "pmbot_pre_live_tiny_order_blockers_062p.v1"
PRE_LIVE_TINY_ORDER_READINESS_SUMMARY_CONTRACT = "pmbot_pre_live_tiny_order_readiness_summary_062p.v1"
LATEST_PRE_LIVE_TINY_ORDER_GATE_STATUS_CONTRACT = "pmbot_latest_pre_live_tiny_order_gate_status_062p.v1"
PRE_LIVE_TINY_ORDER_GATE_RESULT_CONTRACT = "pmbot_pre_live_tiny_order_gate_result_062p.v1"
PRE_LIVE_TINY_ORDER_GATE_VALIDATION_CONTRACT = "pmbot_pre_live_tiny_order_gate_validation_062p.v1"

STATUS_PRESENT = "present"
STATUS_MISSING = "missing"
STATUS_BLOCKED = "blocked"
STATUS_UNAVAILABLE = "unavailable"

FORCED_FALSE_EXECUTION_FIELDS = (
    "operator_approved",
    "candidate_is_executable",
    "signing_available",
    "signed_payload_available",
    "order_submission_available",
    "wallet_available",
    "cancel_plan_present",
    "failure_plan_present",
    "live_execution_approved",
    "ready_for_future_live_enablement",
    "allowed_for_live",
    "canary_executable_now",
    "real_execution_available",
    "order_submission_enabled",
    "wallet_signing_enabled",
    "signing_enabled",
    "signed_payload_generation_enabled",
    "signed_order_generation_enabled",
    "authenticated_polymarket_enabled",
    "live_connector_enabled",
    "live_execution_allowed",
    "live_execution_performed",
    "wallet_enabled",
    "wallet_used",
    "wallet_signing_performed",
    "cryptographic_signing_enabled",
    "cryptographic_signing_performed",
    "signed_payload_generated",
    "signed_order_payload_generated",
    "order_payload_generated",
    "real_order_submitted",
    "order_submitted",
    "real_order_cancelled",
    "order_submission_attempted",
    "order_cancellation_attempted",
    "wallet_connection_attempted",
    "signer_instantiated",
    "signing_attempted",
    "balance_read_attempted",
    "position_read_attempted",
    "fill_read_attempted",
    "balance_read_enabled",
    "position_read_enabled",
    "fill_read_enabled",
    "authenticated_endpoint_call_performed",
    "authenticated_request_performed",
    "real_authenticated_get_performed",
    "private_key_read",
    "seed_phrase_read",
    "mnemonic_read",
    "private_key_envs_checked",
    "environment_secrets_read",
    "secrets_read",
    "secrets_printed",
    "secrets_persisted",
    "raw_values_emitted",
    "actual_secret_values_exposed",
    "credentials_values_exposed",
    "browser_automation_added",
    "scheduler_or_daemon_added",
    "background_worker_added",
    "autonomous_live_trading_added",
)

FORBIDDEN_MODEL_FIELDS = frozenset(
    {
        "order_id",
        "client_order_id",
        "tx_hash",
        "transaction_hash",
        "fill_id",
        "fill_price",
        "filled_size",
        "execution_status",
        "balance",
        "pnl",
        "profit",
        "realized_pnl",
        "unrealized_pnl",
        "position_opened",
        "position_closed",
        "signature",
        "signed_payload_value",
    }
)


@dataclass(frozen=True)
class PreLiveTinyOrderGateConfig:
    market_symbol: str
    strategy_name: str
    source_tiny_scaffold_path: str
    source_signer_boundary_path: str
    source_auth_preflight_path: str
    source_safety_scan_path: str
    max_notional: float
    market_whitelist: tuple[str, ...]
    from_latest_tiny_scaffold: bool
    require_operator_approval: bool
    artifacts_dir: str
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = PRE_LIVE_TINY_ORDER_GATE_CONFIG_CONTRACT
        value["task_id"] = TASK_ID
        value["mode"] = MODE
        value["execution_mode"] = EXECUTION_MODE
        value["market_symbol"] = clean_text(self.market_symbol).upper() or "BTC"
        value["strategy_name"] = clean_text(self.strategy_name) or "tiny-momentum"
        value["max_notional"] = float(self.max_notional)
        value["market_whitelist"] = [clean_text(item).upper() for item in self.market_whitelist if clean_text(item)]
        value["from_latest_tiny_scaffold"] = self.from_latest_tiny_scaffold is True
        value["require_operator_approval"] = self.require_operator_approval is True
        value.update(pre_live_tiny_order_gate_safety_flags())
        return value


@dataclass(frozen=True)
class PreLiveTinyOrderBlocker:
    blocker_id: str
    blocker_category: str
    reason: str
    severity: str = "critical"
    resolution_status: str = "unresolved"
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = PRE_LIVE_TINY_ORDER_BLOCKER_CONTRACT
        value["task_id"] = TASK_ID
        value["blocker_id"] = clean_text(self.blocker_id)
        value["blocker_category"] = clean_text(self.blocker_category)
        value["reason"] = clean_text(self.reason)
        value["severity"] = clean_text(self.severity) or "critical"
        value["resolution_status"] = clean_text(self.resolution_status) or "unresolved"
        value["blocks_live_execution"] = True
        value["resolved"] = False
        value.update(pre_live_tiny_order_gate_safety_flags())
        return value


@dataclass(frozen=True)
class PreLiveTinyOrderChecklist:
    market_symbol: str
    strategy_name: str
    source_tiny_scaffold_path: str
    source_signer_boundary_path: str
    source_auth_preflight_path: str
    source_safety_scan_path: str
    tiny_candidate_present: bool
    approval_packet_present: bool
    operator_approved: bool
    candidate_is_executable: bool
    hard_limits_passed: bool
    market_whitelisted: bool
    signer_boundary_present: bool
    auth_preflight_present: bool
    safety_scan_present: bool
    signing_available: bool
    signed_payload_available: bool
    order_submission_available: bool
    wallet_available: bool
    cancel_plan_present: bool
    failure_plan_present: bool
    live_execution_approved: bool
    ready_for_future_live_enablement: bool
    allowed_for_live: bool
    blockers: tuple[Mapping[str, Any], ...]
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = PRE_LIVE_TINY_ORDER_CHECKLIST_CONTRACT
        value["task_id"] = TASK_ID
        _normalize_common(value)
        value["checklist_items"] = _checklist_items(value)
        value["operator_summary"] = "Pre-live checklist is review-only and keeps the future live order gate blocked."
        return value


@dataclass(frozen=True)
class PreLiveTinyOrderReadinessSummary:
    market_symbol: str
    strategy_name: str
    source_tiny_scaffold_path: str
    source_signer_boundary_path: str
    source_auth_preflight_path: str
    source_safety_scan_path: str
    tiny_candidate_present: bool
    approval_packet_present: bool
    operator_approved: bool
    candidate_is_executable: bool
    hard_limits_passed: bool
    market_whitelisted: bool
    signer_boundary_present: bool
    auth_preflight_present: bool
    safety_scan_present: bool
    signing_available: bool
    signed_payload_available: bool
    order_submission_available: bool
    wallet_available: bool
    cancel_plan_present: bool
    failure_plan_present: bool
    live_execution_approved: bool
    ready_for_future_live_enablement: bool
    allowed_for_live: bool
    blocker_count: int
    blockers: tuple[Mapping[str, Any], ...]
    next_operator_action: str
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = PRE_LIVE_TINY_ORDER_READINESS_SUMMARY_CONTRACT
        value["task_id"] = TASK_ID
        _normalize_common(value)
        blockers = [dict(row) for row in self.blockers]
        value["blockers"] = blockers
        value["blocker_count"] = len(blockers)
        value["top_blocker_reasons"] = [clean_text(row.get("reason")) for row in blockers[:10]]
        value["readiness_status"] = STATUS_BLOCKED
        value["ready_for_future_live_enablement"] = False
        value["allowed_for_live"] = False
        value["operator_summary"] = (
            "Not ready for future live enablement; unresolved blockers must be reviewed before any separate "
            "live-enabling task."
        )
        return value


@dataclass(frozen=True)
class LatestPreLiveTinyOrderGateStatus:
    status: str
    market_symbol: str
    strategy_name: str
    source_tiny_scaffold_path: str
    source_signer_boundary_path: str
    source_auth_preflight_path: str
    source_safety_scan_path: str
    tiny_candidate_present: bool
    approval_packet_present: bool
    operator_approved: bool
    candidate_is_executable: bool
    hard_limits_passed: bool
    market_whitelisted: bool
    signer_boundary_present: bool
    auth_preflight_present: bool
    safety_scan_present: bool
    signing_available: bool
    signed_payload_available: bool
    order_submission_available: bool
    wallet_available: bool
    cancel_plan_present: bool
    failure_plan_present: bool
    live_execution_approved: bool
    ready_for_future_live_enablement: bool
    allowed_for_live: bool
    blocker_count: int
    blockers: tuple[Mapping[str, Any], ...]
    next_operator_action: str
    artifact_path: str
    latest_status_path: str
    operator_markdown_path: str
    checklist_path: str
    blockers_path: str
    readiness_summary_path: str
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = LATEST_PRE_LIVE_TINY_ORDER_GATE_STATUS_CONTRACT
        value["task_id"] = TASK_ID
        value["status"] = clean_text(self.status)
        _normalize_common(value)
        blockers = [dict(row) for row in self.blockers]
        value["blockers"] = blockers
        value["blocker_count"] = len(blockers)
        value["top_blocker_reasons"] = [clean_text(row.get("reason")) for row in blockers[:10]]
        value["tiny_scaffold"] = STATUS_PRESENT if self.source_tiny_scaffold_path else STATUS_MISSING
        value["signer_boundary"] = STATUS_PRESENT if self.signer_boundary_present else STATUS_MISSING
        value["auth_preflight"] = STATUS_PRESENT if self.auth_preflight_present else STATUS_MISSING
        value["safety_scan"] = STATUS_PRESENT if self.safety_scan_present else STATUS_MISSING
        value["signing"] = STATUS_BLOCKED
        value["order_submission"] = STATUS_BLOCKED
        value["wallet"] = STATUS_BLOCKED
        value["live_execution"] = STATUS_BLOCKED
        value["operator_summary"] = _latest_operator_summary(value)
        return value


@dataclass(frozen=True)
class PreLiveTinyOrderGateResult:
    status: str
    config: Mapping[str, Any]
    checklist: Mapping[str, Any]
    readiness_summary: Mapping[str, Any]
    latest_status: Mapping[str, Any]
    blockers: tuple[Mapping[str, Any], ...]
    artifact_paths: Mapping[str, str]
    operator_summary: str
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        config = dict(self.config)
        checklist = dict(self.checklist)
        readiness_summary = dict(self.readiness_summary)
        latest_status = dict(self.latest_status)
        blockers = [dict(row) for row in self.blockers]
        value = {
            "contract_version": PRE_LIVE_TINY_ORDER_GATE_RESULT_CONTRACT,
            "task_id": TASK_ID,
            "status": clean_text(self.status),
            "mode": MODE,
            "execution_mode": EXECUTION_MODE,
            "review_only": True,
            "preflight_only": True,
            "gate_only": True,
            "dry_run": True,
            "market": clean_text(config.get("market_symbol")).upper() or "BTC",
            "market_symbol": clean_text(config.get("market_symbol")).upper() or "BTC",
            "strategy_name": clean_text(config.get("strategy_name")) or "tiny-momentum",
            "source_tiny_scaffold_path": clean_text(config.get("source_tiny_scaffold_path")),
            "source_signer_boundary_path": clean_text(config.get("source_signer_boundary_path")),
            "source_auth_preflight_path": clean_text(config.get("source_auth_preflight_path")),
            "source_safety_scan_path": clean_text(config.get("source_safety_scan_path")),
            "tiny_candidate_present": checklist.get("tiny_candidate_present") is True,
            "approval_packet_present": checklist.get("approval_packet_present") is True,
            "operator_approved": False,
            "candidate_is_executable": False,
            "hard_limits_passed": checklist.get("hard_limits_passed") is True,
            "market_whitelisted": checklist.get("market_whitelisted") is True,
            "signer_boundary_present": checklist.get("signer_boundary_present") is True,
            "signing_available": False,
            "signed_payload_available": False,
            "order_submission_available": False,
            "wallet_available": False,
            "cancel_plan_present": False,
            "failure_plan_present": False,
            "live_execution_approved": False,
            "ready_for_future_live_enablement": False,
            "allowed_for_live": False,
            "resolved_blocker_count": 0,
            "blockers": blockers,
            "blocker_count": len(blockers),
            "next_operator_action": clean_text(readiness_summary.get("next_operator_action")),
            "config": config,
            "checklist": checklist,
            "readiness_summary": readiness_summary,
            "latest_status": latest_status,
            "artifact_paths": dict(self.artifact_paths),
            "operator_summary": clean_text(self.operator_summary),
            "generated_at": self.generated_at,
        }
        value.update(pre_live_tiny_order_gate_safety_flags())
        value["tiny_candidate_present"] = checklist.get("tiny_candidate_present") is True
        value["approval_packet_present"] = checklist.get("approval_packet_present") is True
        value["hard_limits_passed"] = checklist.get("hard_limits_passed") is True
        value["market_whitelisted"] = checklist.get("market_whitelisted") is True
        value["signer_boundary_present"] = checklist.get("signer_boundary_present") is True
        value["validation"] = validate_pre_live_tiny_order_gate_result(value, generated_at=self.generated_at)
        return value


def pre_live_tiny_order_gate_safety_flags() -> dict[str, Any]:
    return {
        "execution_mode": EXECUTION_MODE,
        "review_only": True,
        "preflight_only": True,
        "gate_only": True,
        "dry_run_only": True,
        "paper_only": True,
        "non_executable": True,
        "operator_approved": False,
        "candidate_is_executable": False,
        "signing_available": False,
        "signed_payload_available": False,
        "order_submission_available": False,
        "wallet_available": False,
        "cancel_plan_present": False,
        "failure_plan_present": False,
        "live_execution_approved": False,
        "ready_for_future_live_enablement": False,
        "allowed_for_live": False,
        "canary_executable_now": False,
        "real_execution_available": False,
        "order_submission_enabled": False,
        "wallet_signing_enabled": False,
        "signing_enabled": False,
        "signed_payload_generation_enabled": False,
        "signed_order_generation_enabled": False,
        "authenticated_polymarket_enabled": False,
        "live_connector_enabled": False,
        "live_execution_allowed": False,
        "live_execution_performed": False,
        "wallet_enabled": False,
        "wallet_used": False,
        "wallet_signing_performed": False,
        "cryptographic_signing_enabled": False,
        "cryptographic_signing_performed": False,
        "signed_payload_generated": False,
        "signed_order_payload_generated": False,
        "order_payload_generated": False,
        "real_order_submitted": False,
        "order_submitted": False,
        "real_order_cancelled": False,
        "order_submission_attempted": False,
        "order_cancellation_attempted": False,
        "wallet_connection_attempted": False,
        "signer_instantiated": False,
        "signing_attempted": False,
        "balance_read_attempted": False,
        "position_read_attempted": False,
        "fill_read_attempted": False,
        "balance_read_enabled": False,
        "position_read_enabled": False,
        "fill_read_enabled": False,
        "authenticated_endpoint_call_performed": False,
        "authenticated_request_performed": False,
        "real_authenticated_get_performed": False,
        "private_key_read": False,
        "seed_phrase_read": False,
        "mnemonic_read": False,
        "private_key_envs_checked": False,
        "environment_secrets_read": False,
        "secrets_read": False,
        "secrets_printed": False,
        "secrets_persisted": False,
        "raw_values_emitted": False,
        "actual_secret_values_exposed": False,
        "credentials_values_exposed": False,
        "browser_automation_added": False,
        "scheduler_or_daemon_added": False,
        "background_worker_added": False,
        "autonomous_live_trading_added": False,
        "resolved_blocker_count": 0,
    }


def build_pre_live_tiny_order_blockers_report(
    blockers: Sequence[Mapping[str, Any]],
    *,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    rows = [dict(row) for row in blockers]
    value = {
        "contract_version": PRE_LIVE_TINY_ORDER_BLOCKERS_CONTRACT,
        "task_id": TASK_ID,
        "status": "unresolved_blockers_present",
        "blocker_count": len(rows),
        "resolved_blocker_count": 0,
        "blockers": rows,
        "top_blocker_reasons": [clean_text(row.get("reason")) for row in rows[:10]],
        "generated_at": generated_at,
    }
    value.update(pre_live_tiny_order_gate_safety_flags())
    return value


def validate_pre_live_tiny_order_gate_result(
    result: Mapping[str, Any],
    *,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    value = dict(result or {})
    errors: list[str] = []
    statuses: list[str] = []
    if value.get("contract_version") != PRE_LIVE_TINY_ORDER_GATE_RESULT_CONTRACT:
        errors.append(f"contract_version must be {PRE_LIVE_TINY_ORDER_GATE_RESULT_CONTRACT}")
        statuses.append("invalid_contract")
    if value.get("execution_mode") != EXECUTION_MODE:
        errors.append("execution_mode must be preflight")
        statuses.append("invalid_execution_mode")
    for field in ("review_only", "preflight_only", "gate_only"):
        if value.get(field) is not True:
            errors.append(f"{field} must be true")
            statuses.append(f"{field}_missing")
    if value.get("resolved_blocker_count") != 0:
        errors.append("resolved_blocker_count must be 0")
        statuses.append("resolved_blocker_detected")
    for field in FORCED_FALSE_EXECUTION_FIELDS:
        if value.get(field) is not False:
            errors.append(f"{field} must be false")
            statuses.append("unsafe_execution_flag_detected")
    for path, key, nested in _walk_fields(value):
        if key in FORCED_FALSE_EXECUTION_FIELDS and nested is not False:
            errors.append(f"{path}.{key} must be false")
            statuses.append("nested_unsafe_execution_flag_detected")
        if key in FORBIDDEN_MODEL_FIELDS:
            errors.append(f"{path}.{key} is forbidden in pre-live tiny order gate artifacts")
            statuses.append("forbidden_model_field_detected")
    valid = not errors
    return {
        "contract_version": PRE_LIVE_TINY_ORDER_GATE_VALIDATION_CONTRACT,
        "validation_id": _stable_id(
            "pre-live-tiny-order-gate-validation-062p",
            {"status": value.get("status"), "errors": errors},
        ),
        "valid": valid,
        "status": "passed" if valid else "blocked",
        "statuses": _dedupe(statuses)
        or (["pre_live_tiny_order_gate_valid"] if valid else ["pre_live_tiny_order_gate_blocked"]),
        "errors": errors,
        "generated_at": generated_at,
        **pre_live_tiny_order_gate_safety_flags(),
    }


def _normalize_common(value: dict[str, Any]) -> None:
    blockers = [dict(row) for row in value.get("blockers", []) if isinstance(row, Mapping)]
    value["mode"] = MODE
    value["execution_mode"] = EXECUTION_MODE
    value["review_only"] = True
    value["preflight_only"] = True
    value["gate_only"] = True
    value["market"] = clean_text(value.get("market_symbol")).upper() or "BTC"
    value["market_symbol"] = clean_text(value.get("market_symbol")).upper() or "BTC"
    value["strategy_name"] = clean_text(value.get("strategy_name")) or "tiny-momentum"
    value["operator_approved"] = False
    value["candidate_is_executable"] = False
    value["signing_available"] = False
    value["signed_payload_available"] = False
    value["order_submission_available"] = False
    value["wallet_available"] = False
    value["cancel_plan_present"] = False
    value["failure_plan_present"] = False
    value["live_execution_approved"] = False
    value["ready_for_future_live_enablement"] = False
    value["allowed_for_live"] = False
    value["blockers"] = blockers
    value["blocker_count"] = len(blockers)
    value["resolved_blocker_count"] = 0
    value.update(pre_live_tiny_order_gate_safety_flags())
    value["tiny_candidate_present"] = value.get("tiny_candidate_present") is True
    value["approval_packet_present"] = value.get("approval_packet_present") is True
    value["hard_limits_passed"] = value.get("hard_limits_passed") is True
    value["market_whitelisted"] = value.get("market_whitelisted") is True
    value["signer_boundary_present"] = value.get("signer_boundary_present") is True
    value["auth_preflight_present"] = value.get("auth_preflight_present") is True
    value["safety_scan_present"] = value.get("safety_scan_present") is True


def _checklist_items(value: Mapping[str, Any]) -> list[dict[str, Any]]:
    return [
        _item("tiny_scaffold_source_present", value.get("source_tiny_scaffold_path"), "latest 061 source exists"),
        _item("tiny_candidate_present", value.get("tiny_candidate_present"), "tiny candidate source exists"),
        _item("approval_packet_present", value.get("approval_packet_present"), "manual approval packet exists"),
        _item("operator_approved_false", False, "operator_approved remains false and blocks live action"),
        _item("candidate_non_executable", False, "candidate_is_executable remains false"),
        _item("hard_limits_passed", value.get("hard_limits_passed"), "tiny hard limits are satisfied"),
        _item("market_whitelisted", value.get("market_whitelisted"), "market is in the review whitelist"),
        _item("signer_boundary_present", value.get("signer_boundary_present"), "latest 060 signer boundary exists"),
        _item("auth_preflight_present", value.get("auth_preflight_present"), "latest 059 no-order auth status exists"),
        _item("safety_scan_present", value.get("safety_scan_present"), "latest 060Q safety scan exists"),
        _item("signing_unavailable", False, "signing remains blocked"),
        _item("signed_payload_unavailable", False, "signed payload generation remains blocked"),
        _item("order_submission_unavailable", False, "order submission and cancellation remain blocked"),
        _item("wallet_unavailable", False, "wallet connection remains blocked"),
        _item("cancel_plan_missing", False, "rollback/cancel planning is still checklist-only"),
        _item("failure_plan_missing", False, "failure planning is still checklist-only"),
        _item("live_execution_not_approved", False, "live execution approval remains false"),
        _item("future_live_enablement_not_ready", False, "a separate live-enabling task is still required"),
    ]


def _item(check_id: str, ready: Any, detail: str) -> dict[str, Any]:
    is_ready = ready is True or (isinstance(ready, str) and bool(clean_text(ready)))
    return {
        "check_id": check_id,
        "ready": is_ready,
        "status": "ready" if is_ready else STATUS_BLOCKED,
        "detail": detail,
    }


def _latest_operator_summary(value: Mapping[str, Any]) -> str:
    return (
        "Pre-live tiny order gate completed as review-only. Tiny scaffold="
        + clean_text(value.get("tiny_scaffold"))
        + "; operator_approved=false; candidate_is_executable=false; signing, signed payload generation, "
        "order submission, wallet use, live execution, and autonomous trading remain blocked."
    )


def _walk_fields(value: Any, path: str = "$") -> list[tuple[str, str, Any]]:
    rows: list[tuple[str, str, Any]] = []
    if isinstance(value, Mapping):
        for key, nested in value.items():
            key_text = clean_text(key)
            rows.append((path, key_text, nested))
            rows.extend(_walk_fields(nested, f"{path}.{key_text}"))
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            rows.extend(_walk_fields(nested, f"{path}[{index}]"))
    return rows


def _dedupe(values: Sequence[Any]) -> list[str]:
    result: list[str] = []
    for value in values:
        text = clean_text(value)
        if text and text not in result:
            result.append(text)
    return result


def _stable_id(prefix: str, payload: Mapping[str, Any]) -> str:
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()
    return f"{prefix}-{digest[:16]}"
