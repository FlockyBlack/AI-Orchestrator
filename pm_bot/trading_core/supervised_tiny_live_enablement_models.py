from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

from pm_bot.trading_core.schemas import GENERATED_AT, clean_text

TASK_ID = "ORCH-PMBOT-TRADING-MVP-063-SUPERVISED-TINY-LIVE-ENABLEMENT-GATE-NO-EXECUTION"

EXECUTION_MODE = "preflight"
MODE = "supervised tiny live enablement preparation / review-only"

SUPERVISED_TINY_LIVE_ENABLEMENT_GATE_CONTRACT = "pmbot_supervised_tiny_live_enablement_gate_063.v1"
SUPERVISED_TINY_LIVE_READINESS_SUMMARY_CONTRACT = "pmbot_supervised_tiny_live_readiness_summary_063.v1"
SUPERVISED_TINY_LIVE_OPERATOR_CHECKLIST_CONTRACT = "pmbot_supervised_tiny_live_operator_checklist_063.v1"
SUPERVISED_TINY_LIVE_BLOCKER_CONTRACT = "pmbot_supervised_tiny_live_blocker_063.v1"
SUPERVISED_TINY_LIVE_BLOCKER_MATRIX_CONTRACT = "pmbot_supervised_tiny_live_blocker_matrix_063.v1"
SUPERVISED_TINY_LIVE_RISK_LIMITS_CONTRACT = "pmbot_supervised_tiny_live_risk_limits_063.v1"
SUPERVISED_TINY_LIVE_KILL_SWITCH_PLAN_CONTRACT = "pmbot_supervised_tiny_live_kill_switch_plan_063.v1"
SUPERVISED_TINY_LIVE_CANCEL_PLAN_CONTRACT = "pmbot_supervised_tiny_live_cancel_plan_063.v1"
SUPERVISED_TINY_LIVE_FAILURE_PLAN_CONTRACT = "pmbot_supervised_tiny_live_failure_plan_063.v1"
SUPERVISED_TINY_LIVE_ENV_READINESS_CONTRACT = "pmbot_supervised_tiny_live_env_readiness_063.v1"
SUPERVISED_TINY_LIVE_MANUAL_APPROVAL_PACKET_CONTRACT = (
    "pmbot_supervised_tiny_live_manual_approval_packet_063.v1"
)
LATEST_SUPERVISED_TINY_LIVE_ENABLEMENT_STATUS_CONTRACT = (
    "pmbot_latest_supervised_tiny_live_enablement_status_063.v1"
)
SUPERVISED_TINY_LIVE_ENABLEMENT_VALIDATION_CONTRACT = (
    "pmbot_supervised_tiny_live_enablement_validation_063.v1"
)

STATUS_BLOCKED = "blocked"
STATUS_PRESENT = "present"
STATUS_MISSING = "missing"

REQUIRED_FALSE_FLAGS = (
    "live_execution_approved",
    "canary_executable_now",
    "real_execution_available",
    "order_submission_enabled",
    "order_cancel_enabled",
    "wallet_signing_enabled",
    "signing_enabled",
    "signed_payload_generation_enabled",
    "signed_order_generation_enabled",
    "authenticated_polymarket_enabled",
    "live_connector_enabled",
    "allowed_for_live",
    "operator_approved",
    "candidate_is_executable",
)

FORCED_FALSE_EXECUTION_FIELDS = (
    *REQUIRED_FALSE_FLAGS,
    "order_submission_available",
    "order_cancel_available",
    "wallet_available",
    "signer_available",
    "signed_payload_available",
    "signed_order_available",
    "live_execution_allowed",
    "live_execution_performed",
    "wallet_enabled",
    "wallet_used",
    "wallet_connection_attempted",
    "wallet_signing_performed",
    "signer_instantiated",
    "signing_attempted",
    "cryptographic_signing_enabled",
    "cryptographic_signing_performed",
    "signed_payload_generated",
    "signed_order_payload_generated",
    "order_payload_generated",
    "real_order_submitted",
    "order_submitted",
    "real_order_cancelled",
    "order_cancelled",
    "order_submission_attempted",
    "order_cancellation_attempted",
    "balance_read_attempted",
    "position_read_attempted",
    "fill_read_attempted",
    "pnl_read_attempted",
    "balance_read_enabled",
    "position_read_enabled",
    "fill_read_enabled",
    "pnl_read_enabled",
    "authenticated_endpoint_call_performed",
    "authenticated_request_performed",
    "real_authenticated_get_performed",
    "private_key_read",
    "seed_phrase_read",
    "mnemonic_read",
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
    "telegram_live_order_controls_added",
    "telegram_signing_controls_added",
    "telegram_wallet_controls_added",
    "kill_switch_plan_executable",
    "cancel_plan_executable",
    "failure_plan_executable",
)

REQUIRED_UNRESOLVED_BLOCKER_IDS = (
    "operator_approved_false",
    "live_enablement_task_not_present",
    "private_key_unavailable_and_not_read",
    "wallet_unavailable",
    "signer_unavailable",
    "signing_unavailable",
    "signed_payload_generation_unavailable",
    "order_submission_unavailable",
    "order_cancel_unavailable",
    "authenticated_trading_unavailable",
    "balances_positions_fills_pnl_unavailable",
    "live_execution_not_approved",
    "candidate_non_executable",
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
        "balances",
        "pnl",
        "profit",
        "realized_pnl",
        "unrealized_pnl",
        "position",
        "positions",
        "position_opened",
        "position_closed",
        "signature",
        "signed_payload_value",
        "signed_order_value",
    }
)


@dataclass(frozen=True)
class SupervisedTinyLiveBlocker:
    blocker_id: str
    blocker_category: str
    reason: str
    severity: str = "critical"
    resolution_status: str = "unresolved"
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = SUPERVISED_TINY_LIVE_BLOCKER_CONTRACT
        value["task_id"] = TASK_ID
        value["blocker_id"] = clean_text(self.blocker_id)
        value["blocker_category"] = clean_text(self.blocker_category)
        value["reason"] = clean_text(self.reason)
        value["severity"] = clean_text(self.severity) or "critical"
        value["resolution_status"] = clean_text(self.resolution_status) or "unresolved"
        value["resolved"] = False
        value["blocks_live_execution"] = True
        value.update(supervised_tiny_live_enablement_safety_flags())
        return value


@dataclass(frozen=True)
class SupervisedTinyLiveRiskLimits:
    market_symbol: str
    strategy_name: str
    max_order_notional_usd: float
    max_daily_notional_usd: float
    max_orders_per_day: int
    max_market_count: int
    allowed_market: str
    allowed_strategy: str
    operator_approval_required_for_later_live_task: bool
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = SUPERVISED_TINY_LIVE_RISK_LIMITS_CONTRACT
        value["task_id"] = TASK_ID
        _normalize_common(value)
        value["max_order_notional_usd"] = min(float(self.max_order_notional_usd), 1.0)
        value["max_daily_notional_usd"] = min(float(self.max_daily_notional_usd), 1.0)
        value["max_orders_per_day"] = min(int(self.max_orders_per_day), 1)
        value["max_market_count"] = min(int(self.max_market_count), 1)
        value["allowed_market"] = clean_text(self.allowed_market).upper() or "BTC"
        value["allowed_strategy"] = clean_text(self.allowed_strategy) or "tiny-momentum"
        value["preparation_constraints_only"] = True
        value["limits_are_executable"] = False
        value["operator_approval_required_for_later_live_task"] = True
        value["operator_summary"] = (
            "Tiny-live intended limits are preparation constraints only; they do not enable live execution."
        )
        return value


@dataclass(frozen=True)
class SupervisedTinyLiveKillSwitchPlan:
    market_symbol: str
    strategy_name: str
    stop_future_live_enablement_steps: tuple[str, ...]
    operator_confirmation_required: bool
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = SUPERVISED_TINY_LIVE_KILL_SWITCH_PLAN_CONTRACT
        value["task_id"] = TASK_ID
        _normalize_common(value)
        value["stop_future_live_enablement_steps"] = [
            clean_text(step) for step in self.stop_future_live_enablement_steps if clean_text(step)
        ]
        value["operator_confirmation_required"] = True
        value["plan_is_descriptive_only"] = True
        value["plan_is_executable"] = False
        value["kill_switch_plan_executable"] = False
        value["operator_summary"] = (
            "Operator can stop future live enablement by declining approval, preserving blockers, and closing any "
            "later live-enabling task without execution."
        )
        return value


@dataclass(frozen=True)
class SupervisedTinyLiveCancelPlan:
    market_symbol: str
    strategy_name: str
    required_before_any_real_order: tuple[str, ...]
    operator_confirmation_required: bool
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = SUPERVISED_TINY_LIVE_CANCEL_PLAN_CONTRACT
        value["task_id"] = TASK_ID
        _normalize_common(value)
        value["required_before_any_real_order"] = [
            clean_text(step) for step in self.required_before_any_real_order if clean_text(step)
        ]
        value["operator_confirmation_required"] = True
        value["plan_is_descriptive_only"] = True
        value["plan_is_executable"] = False
        value["cancel_plan_executable"] = False
        value["operator_summary"] = (
            "Cancel planning is descriptive only; a later approved task must define and verify any real cancellation "
            "capability before a real order could be considered."
        )
        return value


@dataclass(frozen=True)
class SupervisedTinyLiveFailurePlan:
    market_symbol: str
    strategy_name: str
    later_task_failure_steps: tuple[str, ...]
    operator_confirmation_required: bool
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = SUPERVISED_TINY_LIVE_FAILURE_PLAN_CONTRACT
        value["task_id"] = TASK_ID
        _normalize_common(value)
        value["later_task_failure_steps"] = [
            clean_text(step) for step in self.later_task_failure_steps if clean_text(step)
        ]
        value["operator_confirmation_required"] = True
        value["plan_is_descriptive_only"] = True
        value["plan_is_executable"] = False
        value["failure_plan_executable"] = False
        value["operator_summary"] = (
            "Failure handling is a future-task runbook only; this gate performs no placement, auth, network, account, "
            "signing, wallet, or order runtime action."
        )
        return value


@dataclass(frozen=True)
class SupervisedTinyLiveEnvReadiness:
    market_symbol: str
    strategy_name: str
    marker_checks: tuple[Mapping[str, Any], ...]
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        checks = [_normalize_marker_check(row) for row in self.marker_checks]
        missing = [row for row in checks if row["present"] is not True]
        value = {
            "contract_version": SUPERVISED_TINY_LIVE_ENV_READINESS_CONTRACT,
            "task_id": TASK_ID,
            "market_symbol": clean_text(self.market_symbol).upper() or "BTC",
            "strategy_name": clean_text(self.strategy_name) or "tiny-momentum",
            "marker_checks": checks,
            "marker_count": len(checks),
            "missing_marker_count": len(missing),
            "all_required_markers_present": bool(checks) and not missing,
            "env_presence_checked": True,
            "values_redacted": True,
            "presence_only": True,
            "readiness_status": STATUS_BLOCKED,
            "operator_summary": (
                "Environment readiness is presence-only and redacted; missing markers keep live enablement blocked."
            ),
            "generated_at": self.generated_at,
        }
        _normalize_common(value)
        return value


@dataclass(frozen=True)
class SupervisedTinyLiveManualApprovalPacket:
    market_symbol: str
    strategy_name: str
    approval_required: bool
    approval_scope: str
    later_live_enabling_task_required: bool
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = SUPERVISED_TINY_LIVE_MANUAL_APPROVAL_PACKET_CONTRACT
        value["task_id"] = TASK_ID
        _normalize_common(value)
        value["approval_required"] = True
        value["approval_scope"] = "first_tiny_live_order_preparation_only"
        value["operator_approved"] = False
        value["approval_packet_is_executable"] = False
        value["this_packet_is_not_executable"] = True
        value["later_live_enabling_task_required"] = True
        value["no_order_can_be_submitted_from_this_packet"] = True
        value["operator_summary"] = (
            "Manual packet is preparation-only; operator_approved=false and a later explicit live-enabling task is "
            "required."
        )
        return value


@dataclass(frozen=True)
class SupervisedTinyLiveBlockerMatrix:
    market_symbol: str
    strategy_name: str
    blockers: tuple[Mapping[str, Any], ...]
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        rows = [dict(row) for row in self.blockers]
        value = {
            "contract_version": SUPERVISED_TINY_LIVE_BLOCKER_MATRIX_CONTRACT,
            "task_id": TASK_ID,
            "market_symbol": clean_text(self.market_symbol).upper() or "BTC",
            "strategy_name": clean_text(self.strategy_name) or "tiny-momentum",
            "status": "unresolved_blockers_present",
            "blocker_count": len(rows),
            "resolved_blocker_count": 0,
            "required_unresolved_blocker_ids": list(REQUIRED_UNRESOLVED_BLOCKER_IDS),
            "unresolved_blocker_ids": [clean_text(row.get("blocker_id")) for row in rows],
            "blockers": rows,
            "generated_at": self.generated_at,
        }
        _normalize_common(value)
        return value


@dataclass(frozen=True)
class SupervisedTinyLiveOperatorChecklist:
    market_symbol: str
    strategy_name: str
    source_pre_live_gate_path: str
    source_tiny_scaffold_path: str
    risk_limits: Mapping[str, Any]
    kill_switch_plan: Mapping[str, Any]
    cancel_plan: Mapping[str, Any]
    failure_plan: Mapping[str, Any]
    env_readiness: Mapping[str, Any]
    manual_approval_packet: Mapping[str, Any]
    blocker_matrix: Mapping[str, Any]
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        risk_limits = dict(self.risk_limits)
        kill_switch_plan = dict(self.kill_switch_plan)
        cancel_plan = dict(self.cancel_plan)
        failure_plan = dict(self.failure_plan)
        env_readiness = dict(self.env_readiness)
        manual_approval_packet = dict(self.manual_approval_packet)
        blocker_matrix = dict(self.blocker_matrix)
        value = {
            "contract_version": SUPERVISED_TINY_LIVE_OPERATOR_CHECKLIST_CONTRACT,
            "task_id": TASK_ID,
            "market_symbol": clean_text(self.market_symbol).upper() or "BTC",
            "strategy_name": clean_text(self.strategy_name) or "tiny-momentum",
            "source_pre_live_gate_path": clean_text(self.source_pre_live_gate_path),
            "source_tiny_scaffold_path": clean_text(self.source_tiny_scaffold_path),
            "risk_limits_present": bool(risk_limits),
            "kill_switch_plan_present": bool(kill_switch_plan),
            "cancel_plan_present": bool(cancel_plan),
            "failure_plan_present": bool(failure_plan),
            "env_readiness_present": bool(env_readiness),
            "manual_approval_packet_present": bool(manual_approval_packet),
            "blocker_matrix_present": bool(blocker_matrix),
            "checklist_items": _checklist_items(
                source_pre_live_gate_path=self.source_pre_live_gate_path,
                source_tiny_scaffold_path=self.source_tiny_scaffold_path,
                env_readiness=env_readiness,
                blocker_matrix=blocker_matrix,
            ),
            "risk_limits": risk_limits,
            "kill_switch_plan": kill_switch_plan,
            "cancel_plan": cancel_plan,
            "failure_plan": failure_plan,
            "env_readiness": env_readiness,
            "manual_approval_packet": manual_approval_packet,
            "blocker_matrix": blocker_matrix,
            "operator_summary": (
                "Operator checklist is complete for preparation review only; all execution blockers remain unresolved."
            ),
            "generated_at": self.generated_at,
        }
        _normalize_common(value)
        return value


@dataclass(frozen=True)
class SupervisedTinyLiveReadinessSummary:
    market_symbol: str
    strategy_name: str
    source_pre_live_gate_path: str
    source_tiny_scaffold_path: str
    risk_limits_path: str
    kill_switch_plan_path: str
    cancel_plan_path: str
    failure_plan_path: str
    env_readiness_path: str
    manual_approval_packet_path: str
    blocker_matrix_path: str
    blocker_matrix: Mapping[str, Any]
    env_readiness: Mapping[str, Any]
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        blockers = [dict(row) for row in dict(self.blocker_matrix).get("blockers", []) if isinstance(row, Mapping)]
        value = {
            "contract_version": SUPERVISED_TINY_LIVE_READINESS_SUMMARY_CONTRACT,
            "task_id": TASK_ID,
            "status": "supervised_tiny_live_enablement_prepared_live_blocked",
            "readiness_status": STATUS_BLOCKED,
            "market_symbol": clean_text(self.market_symbol).upper() or "BTC",
            "strategy_name": clean_text(self.strategy_name) or "tiny-momentum",
            "source_pre_live_gate_path": clean_text(self.source_pre_live_gate_path),
            "source_tiny_scaffold_path": clean_text(self.source_tiny_scaffold_path),
            "source_pre_live_gate": STATUS_PRESENT if clean_text(self.source_pre_live_gate_path) else STATUS_MISSING,
            "source_tiny_scaffold": STATUS_PRESENT if clean_text(self.source_tiny_scaffold_path) else STATUS_MISSING,
            "risk_limits_path": clean_text(self.risk_limits_path),
            "kill_switch_plan_path": clean_text(self.kill_switch_plan_path),
            "cancel_plan_path": clean_text(self.cancel_plan_path),
            "failure_plan_path": clean_text(self.failure_plan_path),
            "env_readiness_path": clean_text(self.env_readiness_path),
            "manual_approval_packet_path": clean_text(self.manual_approval_packet_path),
            "blocker_matrix_path": clean_text(self.blocker_matrix_path),
            "blockers": blockers,
            "blocker_count": len(blockers),
            "resolved_blocker_count": 0,
            "missing_env_marker_count": int(dict(self.env_readiness).get("missing_marker_count", 0) or 0),
            "next_operator_action": "review preparation artifacts; a separate live-enabling task is still required",
            "operator_summary": (
                "Preparation package generated. Live execution remains blocked by unresolved approval, wallet, signer, "
                "submission, cancellation, authenticated trading, and account-runtime blockers."
            ),
            "generated_at": self.generated_at,
        }
        _normalize_common(value)
        return value


@dataclass(frozen=True)
class SupervisedTinyLiveEnablementGate:
    status: str
    market_symbol: str
    strategy_name: str
    source_pre_live_gate_path: str
    source_tiny_scaffold_path: str
    readiness_summary: Mapping[str, Any]
    operator_checklist: Mapping[str, Any]
    blocker_matrix: Mapping[str, Any]
    risk_limits: Mapping[str, Any]
    kill_switch_plan: Mapping[str, Any]
    cancel_plan: Mapping[str, Any]
    failure_plan: Mapping[str, Any]
    env_readiness: Mapping[str, Any]
    manual_approval_packet: Mapping[str, Any]
    latest_status: Mapping[str, Any]
    artifact_paths: Mapping[str, str]
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        blocker_matrix = dict(self.blocker_matrix)
        blockers = [dict(row) for row in blocker_matrix.get("blockers", []) if isinstance(row, Mapping)]
        value = {
            "contract_version": SUPERVISED_TINY_LIVE_ENABLEMENT_GATE_CONTRACT,
            "task_id": TASK_ID,
            "status": clean_text(self.status),
            "mode": MODE,
            "execution_mode": EXECUTION_MODE,
            "review_only": True,
            "preflight_only": True,
            "preparation_only": True,
            "gate_only": True,
            "dry_run": True,
            "market": clean_text(self.market_symbol).upper() or "BTC",
            "market_symbol": clean_text(self.market_symbol).upper() or "BTC",
            "strategy_name": clean_text(self.strategy_name) or "tiny-momentum",
            "source_pre_live_gate_path": clean_text(self.source_pre_live_gate_path),
            "source_tiny_scaffold_path": clean_text(self.source_tiny_scaffold_path),
            "operator_approved": False,
            "candidate_is_executable": False,
            "blocker_count": len(blockers),
            "resolved_blocker_count": 0,
            "blockers": blockers,
            "readiness_summary": dict(self.readiness_summary),
            "operator_checklist": dict(self.operator_checklist),
            "blocker_matrix": blocker_matrix,
            "risk_limits": dict(self.risk_limits),
            "kill_switch_plan": dict(self.kill_switch_plan),
            "cancel_plan": dict(self.cancel_plan),
            "failure_plan": dict(self.failure_plan),
            "env_readiness": dict(self.env_readiness),
            "manual_approval_packet": dict(self.manual_approval_packet),
            "latest_status": dict(self.latest_status),
            "artifact_paths": dict(self.artifact_paths),
            "operator_summary": (
                "Supervised tiny live enablement gate generated preparation artifacts only. It cannot execute, sign, "
                "connect wallets, submit, cancel, or read account runtime state."
            ),
            "generated_at": self.generated_at,
        }
        value.update(supervised_tiny_live_enablement_safety_flags())
        value["validation"] = validate_supervised_tiny_live_enablement_gate(value, generated_at=self.generated_at)
        return value


def supervised_tiny_live_enablement_safety_flags() -> dict[str, Any]:
    return {
        "execution_mode": EXECUTION_MODE,
        "mode": MODE,
        "review_only": True,
        "preflight_only": True,
        "preparation_only": True,
        "gate_only": True,
        "dry_run_only": True,
        "paper_only": True,
        "non_executable": True,
        "live_execution_approved": False,
        "canary_executable_now": False,
        "real_execution_available": False,
        "order_submission_enabled": False,
        "order_cancel_enabled": False,
        "wallet_signing_enabled": False,
        "signing_enabled": False,
        "signed_payload_generation_enabled": False,
        "signed_order_generation_enabled": False,
        "authenticated_polymarket_enabled": False,
        "live_connector_enabled": False,
        "allowed_for_live": False,
        "operator_approved": False,
        "candidate_is_executable": False,
        "order_submission_available": False,
        "order_cancel_available": False,
        "wallet_available": False,
        "signer_available": False,
        "signed_payload_available": False,
        "signed_order_available": False,
        "live_execution_allowed": False,
        "live_execution_performed": False,
        "wallet_enabled": False,
        "wallet_used": False,
        "wallet_connection_attempted": False,
        "wallet_signing_performed": False,
        "signer_instantiated": False,
        "signing_attempted": False,
        "cryptographic_signing_enabled": False,
        "cryptographic_signing_performed": False,
        "signed_payload_generated": False,
        "signed_order_payload_generated": False,
        "order_payload_generated": False,
        "real_order_submitted": False,
        "order_submitted": False,
        "real_order_cancelled": False,
        "order_cancelled": False,
        "order_submission_attempted": False,
        "order_cancellation_attempted": False,
        "balance_read_attempted": False,
        "position_read_attempted": False,
        "fill_read_attempted": False,
        "pnl_read_attempted": False,
        "balance_read_enabled": False,
        "position_read_enabled": False,
        "fill_read_enabled": False,
        "pnl_read_enabled": False,
        "authenticated_endpoint_call_performed": False,
        "authenticated_request_performed": False,
        "real_authenticated_get_performed": False,
        "private_key_read": False,
        "seed_phrase_read": False,
        "mnemonic_read": False,
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
        "telegram_live_order_controls_added": False,
        "telegram_signing_controls_added": False,
        "telegram_wallet_controls_added": False,
        "kill_switch_plan_executable": False,
        "cancel_plan_executable": False,
        "failure_plan_executable": False,
        "resolved_blocker_count": 0,
    }


def validate_supervised_tiny_live_enablement_gate(
    result: Mapping[str, Any],
    *,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    value = dict(result or {})
    errors: list[str] = []
    statuses: list[str] = []
    if value.get("contract_version") != SUPERVISED_TINY_LIVE_ENABLEMENT_GATE_CONTRACT:
        errors.append(f"contract_version must be {SUPERVISED_TINY_LIVE_ENABLEMENT_GATE_CONTRACT}")
        statuses.append("invalid_contract")
    if value.get("execution_mode") != EXECUTION_MODE:
        errors.append("execution_mode must be preflight")
        statuses.append("invalid_execution_mode")
    for field in ("review_only", "preflight_only", "preparation_only", "gate_only", "non_executable"):
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
    blocker_ids = {
        clean_text(row.get("blocker_id")) for row in value.get("blockers", []) if isinstance(row, Mapping)
    }
    for blocker_id in REQUIRED_UNRESOLVED_BLOCKER_IDS:
        if blocker_id not in blocker_ids:
            errors.append(f"required unresolved blocker missing: {blocker_id}")
            statuses.append("required_blocker_missing")
    for path, key, nested in _walk_fields(value):
        if key in FORCED_FALSE_EXECUTION_FIELDS and nested is not False:
            errors.append(f"{path}.{key} must be false")
            statuses.append("nested_unsafe_execution_flag_detected")
        if key == "resolved_blocker_count" and nested != 0:
            errors.append(f"{path}.{key} must remain 0")
            statuses.append("nested_resolved_blocker_detected")
        if key in FORBIDDEN_MODEL_FIELDS:
            errors.append(f"{path}.{key} is forbidden in supervised tiny live enablement artifacts")
            statuses.append("forbidden_model_field_detected")
    valid = not errors
    return {
        "contract_version": SUPERVISED_TINY_LIVE_ENABLEMENT_VALIDATION_CONTRACT,
        "validation_id": _stable_id(
            "supervised-tiny-live-enablement-validation-063",
            {"status": value.get("status"), "errors": errors},
        ),
        "valid": valid,
        "status": "passed" if valid else STATUS_BLOCKED,
        "statuses": _dedupe(statuses)
        or (["supervised_tiny_live_enablement_gate_valid"] if valid else ["supervised_tiny_live_enablement_blocked"]),
        "errors": errors,
        "generated_at": generated_at,
        **supervised_tiny_live_enablement_safety_flags(),
    }


def _normalize_common(value: dict[str, Any]) -> None:
    value["mode"] = MODE
    value["execution_mode"] = EXECUTION_MODE
    value["review_only"] = True
    value["preflight_only"] = True
    value["preparation_only"] = True
    value["gate_only"] = True
    value["market"] = clean_text(value.get("market_symbol")).upper() or "BTC"
    value["market_symbol"] = clean_text(value.get("market_symbol")).upper() or "BTC"
    value["strategy_name"] = clean_text(value.get("strategy_name")) or "tiny-momentum"
    value.update(supervised_tiny_live_enablement_safety_flags())


def _checklist_items(
    *,
    source_pre_live_gate_path: str,
    source_tiny_scaffold_path: str,
    env_readiness: Mapping[str, Any],
    blocker_matrix: Mapping[str, Any],
) -> list[dict[str, Any]]:
    return [
        _item("source_pre_live_gate_referenced", bool(clean_text(source_pre_live_gate_path)), "062P gate source path recorded"),
        _item("source_tiny_scaffold_referenced", bool(clean_text(source_tiny_scaffold_path)), "061 tiny scaffold source path recorded"),
        _item("risk_limits_present", True, "tiny preparation limits exist and are not executable"),
        _item("kill_switch_plan_present", True, "operator stop plan exists and is descriptive only"),
        _item("cancel_plan_present", True, "future cancellation prerequisites are descriptive only"),
        _item("failure_plan_present", True, "future failure plan is descriptive only"),
        _item("env_readiness_presence_only", True, "environment readiness emits only booleans and redacted labels"),
        _item(
            "env_markers_missing",
            int(env_readiness.get("missing_marker_count", 0) or 0) == 0,
            "missing readiness markers keep live enablement blocked",
        ),
        _item("operator_approved_false", False, "operator_approved remains false"),
        _item("candidate_non_executable", False, "candidate_is_executable remains false"),
        _item(
            "unresolved_blockers_present",
            False,
            f"{int(blocker_matrix.get('blocker_count', 0) or 0)} unresolved blockers remain",
        ),
    ]


def _item(check_id: str, ready: bool, detail: str) -> dict[str, Any]:
    return {
        "check_id": clean_text(check_id),
        "ready": ready is True,
        "status": "ready" if ready is True else STATUS_BLOCKED,
        "detail": clean_text(detail),
    }


def _normalize_marker_check(value: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "marker_label": clean_text(value.get("marker_label")),
        "present": value.get("present") is True,
        "required": value.get("required") is not False,
        "value_redacted": True,
        "raw_value_emitted": False,
    }


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
