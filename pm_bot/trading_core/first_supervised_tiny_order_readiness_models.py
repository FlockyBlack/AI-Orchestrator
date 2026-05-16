from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from pm_bot.trading_core.schemas import GENERATED_AT, clean_text

TASK_ID = "ORCH-PMBOT-TRADING-MVP-077A-FIRST-SUPERVISED-TINY-ORDER_READINESS_PACKET_NO_LIVE"

DEFAULT_MARKET = "BTC"
DEFAULT_STRATEGY = "tiny-momentum"

MODE = "first supervised tiny post-only order readiness packet / no-live / no-submit"
EXECUTION_MODE = "local_artifact_read_only_first_supervised_tiny_order_readiness_packet"

FIRST_SUPERVISED_TINY_ORDER_READINESS_RESULT_CONTRACT = (
    "pmbot_first_supervised_tiny_order_readiness_077a_result.v1"
)
FIRST_SUPERVISED_TINY_ORDER_READINESS_LATEST_STATUS_CONTRACT = (
    "pmbot_latest_first_supervised_tiny_order_readiness_077a_status.v1"
)
FIRST_SUPERVISED_TINY_ORDER_READINESS_BLOCKERS_CONTRACT = (
    "pmbot_first_supervised_tiny_order_readiness_077a_blockers.v1"
)
FIRST_SUPERVISED_TINY_ORDER_READINESS_VALIDATION_CONTRACT = (
    "pmbot_first_supervised_tiny_order_readiness_077a_validation.v1"
)
FIRST_SUPERVISED_TINY_ORDER_READINESS_SAFETY_SNAPSHOT_CONTRACT = (
    "pmbot_first_supervised_tiny_order_readiness_077a_safety_snapshot.v1"
)

STATUS_BLOCKED_MISSING_LOCAL_REAL_CHECK_EVIDENCE = "blocked_missing_local_real_check_evidence"
STATUS_BLOCKED_MISSING_SELECTED_CANDIDATE = "blocked_missing_selected_candidate"
STATUS_BLOCKED_UNVERIFIED_SELECTED_TOKEN = "blocked_unverified_selected_token"
STATUS_BLOCKED_SIGNER_DIAGNOSTIC_NOT_OK = "blocked_signer_diagnostic_not_ok"
STATUS_BLOCKED_PAYLOAD_DRY_RUN_NOT_READY = "blocked_payload_dry_run_not_ready"
STATUS_BLOCKED_RISK_ENGINE_REVIEW = "blocked_risk_engine_review"
STATUS_BLOCKED_OPERATOR_STOP_REQUESTED = "blocked_operator_stop_requested"
STATUS_BLOCKED_MISSING_EXPLICIT_LIVE_AUTHORIZATION = "blocked_missing_explicit_live_authorization"
STATUS_READY_FOR_SEPARATE_LIVE_AUTHORIZATION_PACKET = "ready_for_separate_live_authorization_packet"

VALID_STATUSES = {
    STATUS_BLOCKED_MISSING_LOCAL_REAL_CHECK_EVIDENCE,
    STATUS_BLOCKED_MISSING_SELECTED_CANDIDATE,
    STATUS_BLOCKED_UNVERIFIED_SELECTED_TOKEN,
    STATUS_BLOCKED_SIGNER_DIAGNOSTIC_NOT_OK,
    STATUS_BLOCKED_PAYLOAD_DRY_RUN_NOT_READY,
    STATUS_BLOCKED_RISK_ENGINE_REVIEW,
    STATUS_BLOCKED_OPERATOR_STOP_REQUESTED,
    STATUS_BLOCKED_MISSING_EXPLICIT_LIVE_AUTHORIZATION,
    STATUS_READY_FOR_SEPARATE_LIVE_AUTHORIZATION_PACKET,
}

REQUIRED_FALSE_FLAGS = (
    "allowed_for_live",
    "live",
    "live_ready",
    "submit_ready",
    "ready_for_submit",
    "canary_executable_now",
    "first_supervised_tiny_order_ready_for_execution",
    "first_supervised_tiny_order_execution_authorized",
    "first_supervised_tiny_order_execution_enabled",
    "explicit_live_authorization_present",
    "live_execution_allowed",
    "live_execution_approved",
    "live_execution_authorized",
    "live_execution_performed",
    "live_trading_enabled",
    "operator_approved_for_live",
    "order_submission_enabled",
    "order_submission_attempted",
    "order_submission_performed",
    "order_submitted",
    "order_cancel_enabled",
    "order_cancel_attempted",
    "order_cancel_performed",
    "order_cancellation_enabled",
    "order_cancellation_attempted",
    "order_cancellation_performed",
    "signing_by_default",
    "signing_enabled",
    "signing_attempted",
    "signing_performed",
    "signer_instantiated",
    "signer_instantiated_by_default",
    "signer_instantiation_attempted",
    "wallet_connected",
    "wallet_connection_enabled",
    "wallet_connection_attempted",
    "wallet_enabled",
    "wallet_used",
    "wallet_signing_enabled",
    "wallet_signing_attempted",
    "cryptographic_signing_enabled",
    "cryptographic_signing_performed",
    "private_key_read",
    "seed_phrase_read",
    "mnemonic_read",
    "api_secret_read",
    "auth_token_read",
    "passphrase_read",
    "credential_values_read",
    "credential_values_printed",
    "credential_values_serialized",
    "secret_files_read",
    "secrets_read",
    "secrets_printed",
    "secrets_persisted",
    "raw_values_emitted",
    "raw_secret_values_emitted",
    "private_key_value_emitted",
    "raw_private_key_emitted",
    "signed_payload_generated",
    "signed_payload_generation_attempted",
    "signed_payload_submit_enabled",
    "signed_payload_submit_attempted",
    "signed_payload_submitted",
    "full_signed_payload_output",
    "full_signed_payload_emitted",
    "raw_signed_payload_emitted",
    "full_signed_order_output",
    "full_signed_order_emitted",
    "raw_signed_order_emitted",
    "network_trading_call_performed",
    "trading_write_call_performed",
    "network_write_call_performed",
    "network_write_performed",
    "network_post_performed",
    "network_put_performed",
    "network_patch_performed",
    "network_delete_performed",
    "authenticated_endpoint_enabled",
    "authenticated_request_performed",
    "authenticated_trading_enabled",
    "authenticated_trading_call_performed",
    "trading_requested",
    "browser_automation_added",
    "scheduler_or_daemon_added",
    "background_worker_added",
    "autonomous_live_trading_added",
    "fake_balances_emitted",
    "fake_orders_emitted",
    "fake_fills_emitted",
    "fake_pnl_emitted",
    "fake_order_ids_emitted",
    "fake_tx_hashes_emitted",
)

FORBIDDEN_RAW_FIELD_NAMES = frozenset(
    {
        "token_id",
        "selected_token_id",
        "outcome_token_id",
        "clob_token_id",
        "target_token_id",
        "operator_selected_token_id",
        "raw_token_id",
        "full_token_id",
        "private_key",
        "wallet_private_key",
        "seed_phrase",
        "mnemonic",
        "api_secret",
        "auth_token",
        "passphrase",
        "secret",
        "signature",
        "signed_payload",
        "signed_order",
        "order_id",
        "client_order_id",
        "tx_hash",
        "transaction_hash",
        "fill_id",
        "balance",
        "balances",
        "position",
        "positions",
        "pnl",
        "realized_pnl",
        "unrealized_pnl",
    }
)


@dataclass(frozen=True)
class FirstSupervisedTinyOrderReadinessSafetySnapshot:
    market_symbol: str = DEFAULT_MARKET
    strategy_name: str = DEFAULT_STRATEGY
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        value = {
            "contract_version": FIRST_SUPERVISED_TINY_ORDER_READINESS_SAFETY_SNAPSHOT_CONTRACT,
            "task_id": TASK_ID,
            "status": "active_first_supervised_tiny_order_readiness_077a_safety_snapshot",
            "mode": MODE,
            "execution_mode": EXECUTION_MODE,
            "market": _market(self.market_symbol),
            "market_symbol": _market(self.market_symbol),
            "strategy": _strategy(self.strategy_name),
            "strategy_name": _strategy(self.strategy_name),
            "local_artifact_read_only": True,
            "readiness_packet_only": True,
            "final_no_live_readiness_contract": True,
            "generated_at": self.generated_at,
        }
        value.update(first_supervised_tiny_order_readiness_safety_flags())
        return value


def first_supervised_tiny_order_readiness_safety_flags() -> dict[str, Any]:
    return {
        "mode": MODE,
        "execution_mode": EXECUTION_MODE,
        "paper_only": True,
        "review_only": True,
        "preflight_only": True,
        "dry_run_only": True,
        "local_artifact_only": True,
        "local_artifact_read_only": True,
        "read_only": True,
        "safe_summary_only": True,
        "non_executable": True,
        "readiness_packet_only": True,
        "final_no_live_readiness_contract": True,
        "allowed_for_live": False,
        "live": False,
        "live_ready": False,
        "submit_ready": False,
        "ready_for_submit": False,
        "canary_executable_now": False,
        "first_supervised_tiny_order_ready_for_execution": False,
        "first_supervised_tiny_order_execution_authorized": False,
        "first_supervised_tiny_order_execution_enabled": False,
        "explicit_live_authorization_present": False,
        "live_execution_allowed": False,
        "live_execution_approved": False,
        "live_execution_authorized": False,
        "live_execution_performed": False,
        "live_trading_enabled": False,
        "operator_approved_for_live": False,
        "order_submission_enabled": False,
        "order_submission_attempted": False,
        "order_submission_performed": False,
        "order_submitted": False,
        "order_cancel_enabled": False,
        "order_cancel_attempted": False,
        "order_cancel_performed": False,
        "order_cancellation_enabled": False,
        "order_cancellation_attempted": False,
        "order_cancellation_performed": False,
        "signing_by_default": False,
        "signing_enabled": False,
        "signing_attempted": False,
        "signing_performed": False,
        "signer_instantiated": False,
        "signer_instantiated_by_default": False,
        "signer_instantiation_attempted": False,
        "wallet_connected": False,
        "wallet_connection_enabled": False,
        "wallet_connection_attempted": False,
        "wallet_enabled": False,
        "wallet_used": False,
        "wallet_signing_enabled": False,
        "wallet_signing_attempted": False,
        "cryptographic_signing_enabled": False,
        "cryptographic_signing_performed": False,
        "private_key_read": False,
        "seed_phrase_read": False,
        "mnemonic_read": False,
        "api_secret_read": False,
        "auth_token_read": False,
        "passphrase_read": False,
        "credential_values_read": False,
        "credential_values_printed": False,
        "credential_values_serialized": False,
        "secret_files_read": False,
        "secrets_read": False,
        "secrets_printed": False,
        "secrets_persisted": False,
        "raw_values_emitted": False,
        "raw_secret_values_emitted": False,
        "private_key_value_emitted": False,
        "raw_private_key_emitted": False,
        "signed_payload_generated": False,
        "signed_payload_generation_attempted": False,
        "signed_payload_submit_enabled": False,
        "signed_payload_submit_attempted": False,
        "signed_payload_submitted": False,
        "full_signed_payload_output": False,
        "full_signed_payload_emitted": False,
        "raw_signed_payload_emitted": False,
        "full_signed_order_output": False,
        "full_signed_order_emitted": False,
        "raw_signed_order_emitted": False,
        "network_trading_call_performed": False,
        "network_trading_calls_performed": 0,
        "trading_write_call_performed": False,
        "network_write_call_performed": False,
        "network_write_performed": False,
        "network_post_performed": False,
        "network_put_performed": False,
        "network_patch_performed": False,
        "network_delete_performed": False,
        "authenticated_endpoint_enabled": False,
        "authenticated_request_performed": False,
        "authenticated_trading_enabled": False,
        "authenticated_trading_call_performed": False,
        "trading_requested": False,
        "browser_automation_added": False,
        "scheduler_or_daemon_added": False,
        "background_worker_added": False,
        "autonomous_live_trading_added": False,
        "fake_balances_emitted": False,
        "fake_orders_emitted": False,
        "fake_fills_emitted": False,
        "fake_pnl_emitted": False,
        "fake_order_ids_emitted": False,
        "fake_tx_hashes_emitted": False,
        "resolved_blocker_count": 0,
    }


def validate_first_supervised_tiny_order_readiness_result(value: Mapping[str, Any]) -> dict[str, Any]:
    result = dict(value or {})
    errors: list[str] = []
    statuses: list[str] = []
    status = clean_text(result.get("status"))

    if result.get("contract_version") != FIRST_SUPERVISED_TINY_ORDER_READINESS_RESULT_CONTRACT:
        errors.append("contract_version mismatch")
        statuses.append("invalid_contract")
    if result.get("task_id") != TASK_ID:
        errors.append("task_id mismatch")
        statuses.append("task_id_mismatch")
    if status not in VALID_STATUSES:
        errors.append("status is not a recognized 077A readiness status")
        statuses.append("invalid_status")
    if result.get("dry_run") is not True:
        errors.append("dry_run must be true")
        statuses.append("dry_run_missing")
    if result.get("first_supervised_tiny_order_ready_for_execution") is not False:
        errors.append("first_supervised_tiny_order_ready_for_execution must be false")
        statuses.append("execution_ready_not_false")
    if result.get("explicit_live_authorization_present") is not False:
        errors.append("explicit_live_authorization_present must be false")
        statuses.append("explicit_live_authorization_not_false")
    if status == STATUS_READY_FOR_SEPARATE_LIVE_AUTHORIZATION_PACKET:
        if result.get("first_supervised_tiny_order_ready_for_authorization") is not True:
            errors.append("ready packet status requires first_supervised_tiny_order_ready_for_authorization=true")
            statuses.append("ready_status_without_authorization_readiness")
        if clean_text(result.get("current_top_blocker")) != STATUS_BLOCKED_MISSING_EXPLICIT_LIVE_AUTHORIZATION:
            errors.append("ready packet status must still name missing explicit live authorization as execution blocker")
            statuses.append("ready_status_missing_execution_blocker")
    else:
        if result.get("first_supervised_tiny_order_ready_for_authorization") is not False:
            errors.append("blocked status requires first_supervised_tiny_order_ready_for_authorization=false")
            statuses.append("blocked_status_with_authorization_readiness")

    for path, key, nested in _walk_fields(result):
        if key in REQUIRED_FALSE_FLAGS and nested is not False:
            errors.append(f"{path}.{key} must be false")
            statuses.append("unsafe_false_flag_detected")
        if key == "resolved_blocker_count" and nested != 0:
            errors.append(f"{path}.{key} must be 0")
            statuses.append("resolved_blocker_detected")
        if key in FORBIDDEN_RAW_FIELD_NAMES and nested:
            errors.append(f"{path}.{key} must not be emitted by 077A")
            statuses.append("raw_or_sensitive_field_detected")

    valid = not errors
    return {
        "contract_version": FIRST_SUPERVISED_TINY_ORDER_READINESS_VALIDATION_CONTRACT,
        "task_id": TASK_ID,
        "valid": valid,
        "status": "passed" if valid else "blocked_validation_failed",
        "statuses": _dedupe(statuses)
        or (
            ["first_supervised_tiny_order_readiness_077a_valid"]
            if valid
            else ["first_supervised_tiny_order_readiness_077a_blocked"]
        ),
        "errors": errors,
        "generated_at": clean_text(result.get("generated_at")) or GENERATED_AT,
        **first_supervised_tiny_order_readiness_safety_flags(),
    }


def _market(value: Any) -> str:
    return clean_text(value).upper() or DEFAULT_MARKET


def _strategy(value: Any) -> str:
    return clean_text(value) or DEFAULT_STRATEGY


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
