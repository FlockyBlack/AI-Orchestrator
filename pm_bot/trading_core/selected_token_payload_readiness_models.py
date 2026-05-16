from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from pm_bot.trading_core.schemas import GENERATED_AT, clean_text

TASK_ID = "ORCH-PMBOT-TRADING-MVP-073C-SELECTED-TOKEN-SIGNED-PAYLOAD-READINESS-GATE-NO-SUBMIT"

EXECUTION_MODE = "preflight"
MODE = "selected token signed payload readiness gate / dry-run / no-submit"

DEFAULT_ALLOWED_MARKET = "BTC"
DEFAULT_ALLOWED_STRATEGY = "tiny-momentum"

STATUS_READY = "ready_for_signed_payload_diagnostic"
STATUS_BLOCKED_MISSING_SELECTED_TOKEN = "blocked_missing_selected_token"
STATUS_BLOCKED_UNVERIFIED_SELECTED_TOKEN = "blocked_unverified_selected_token"
STATUS_BLOCKED_MISSING_SIGNER_DIAGNOSTIC = "blocked_missing_signer_diagnostic"
STATUS_BLOCKED_SIGNER_DIAGNOSTIC_NOT_OK = "blocked_signer_diagnostic_not_ok"
STATUS_BLOCKED_MISSING_SIGNER_DIAGNOSTIC_EVIDENCE = "blocked_missing_signer_diagnostic_evidence"
STATUS_BLOCKED_SIGNER_DIAGNOSTIC_FAILED = "blocked_signer_diagnostic_failed"
STATUS_BLOCKED_MISSING_APPROVAL_CONTRACT = "blocked_missing_approval_contract"
STATUS_BLOCKED_APPROVAL_CONTRACT_NOT_READY = "blocked_approval_contract_not_ready"
STATUS_BLOCKED_MISSING_SIGNED_PAYLOAD_DRY_RUN = "blocked_missing_signed_payload_dry_run"
STATUS_BLOCKED_SIGNED_PAYLOAD_DRY_RUN_NOT_READY = "blocked_signed_payload_dry_run_not_ready"
STATUS_BLOCKED_SOURCE_SAFETY_NOT_READY = "blocked_source_safety_not_ready"

SELECTED_TOKEN_PAYLOAD_READINESS_RESULT_CONTRACT = "pmbot_selected_token_payload_readiness_gate_073c_result.v1"
SELECTED_TOKEN_PAYLOAD_READINESS_LATEST_STATUS_CONTRACT = (
    "pmbot_latest_selected_token_payload_readiness_status_073c.v1"
)
SELECTED_TOKEN_PAYLOAD_READINESS_SOURCES_CONTRACT = "pmbot_selected_token_payload_readiness_sources_073c.v1"
SELECTED_TOKEN_PAYLOAD_READINESS_BLOCKERS_CONTRACT = "pmbot_selected_token_payload_readiness_blockers_073c.v1"
SELECTED_TOKEN_PAYLOAD_READINESS_SAFETY_SNAPSHOT_CONTRACT = (
    "pmbot_selected_token_payload_readiness_safety_snapshot_073c.v1"
)
SELECTED_TOKEN_PAYLOAD_READINESS_VALIDATION_CONTRACT = (
    "pmbot_selected_token_payload_readiness_validation_073c.v1"
)

ALLOWED_STATUSES = frozenset(
    {
        STATUS_READY,
        STATUS_BLOCKED_MISSING_SELECTED_TOKEN,
        STATUS_BLOCKED_UNVERIFIED_SELECTED_TOKEN,
        STATUS_BLOCKED_MISSING_SIGNER_DIAGNOSTIC,
        STATUS_BLOCKED_SIGNER_DIAGNOSTIC_NOT_OK,
        STATUS_BLOCKED_MISSING_SIGNER_DIAGNOSTIC_EVIDENCE,
        STATUS_BLOCKED_SIGNER_DIAGNOSTIC_FAILED,
        STATUS_BLOCKED_MISSING_APPROVAL_CONTRACT,
        STATUS_BLOCKED_APPROVAL_CONTRACT_NOT_READY,
        STATUS_BLOCKED_MISSING_SIGNED_PAYLOAD_DRY_RUN,
        STATUS_BLOCKED_SIGNED_PAYLOAD_DRY_RUN_NOT_READY,
        STATUS_BLOCKED_SOURCE_SAFETY_NOT_READY,
    }
)

REQUIRED_FALSE_FLAGS = (
    "allowed_for_live",
    "live",
    "selected_token_payload_ready_for_submit",
    "signing_by_default",
    "signer_ready_for_live",
    "order_submit_ready",
    "full_signed_payload_output",
    "live_execution_approved",
    "live_execution_allowed",
    "live_execution_performed",
    "real_execution_available",
    "real_order_submitted",
    "real_order_cancelled",
    "operator_approved",
    "order_generation_enabled",
    "order_generation_attempted",
    "order_payload_generated",
    "order_payload_executable",
    "order_payload_signing_enabled",
    "order_payload_signing_attempted",
    "order_payload_signed",
    "signing_enabled",
    "signing_attempted",
    "signed_order_generation_enabled",
    "signed_order_generation_attempted",
    "signed_order_generated",
    "signed_order_payload_generated",
    "signed_payload_generation_enabled",
    "signed_payload_generation_attempted",
    "signed_payload_generated",
    "signed_payload_fingerprint_stored",
    "full_signed_payload_emitted",
    "raw_signed_payload_emitted",
    "full_signed_order_emitted",
    "raw_signed_order_emitted",
    "signed_payload_submit_enabled",
    "signed_payload_submit_attempted",
    "signed_payload_submitted",
    "order_submission_enabled",
    "order_submission_attempted",
    "order_submission_performed",
    "order_submitted",
    "submit_call_performed",
    "order_cancel_enabled",
    "order_cancel_attempted",
    "order_cancel_performed",
    "order_cancellation_enabled",
    "order_cancellation_attempted",
    "order_cancellation_performed",
    "cancel_call_performed",
    "authenticated_polymarket_enabled",
    "authenticated_endpoint_enabled",
    "authenticated_request_performed",
    "authenticated_trading_enabled",
    "authenticated_trading_call_performed",
    "network_trading_call_performed",
    "trading_write_call_performed",
    "network_write_call_performed",
    "network_write_performed",
    "network_post_performed",
    "network_put_performed",
    "network_patch_performed",
    "network_delete_performed",
    "private_key_read",
    "seed_phrase_read",
    "mnemonic_read",
    "api_secret_read",
    "auth_token_read",
    "passphrase_read",
    "credential_value_read",
    "credential_values_read",
    "credential_values_printed",
    "credential_values_stored",
    "credential_values_serialized",
    "environment_values_read",
    "secret_files_read",
    "secrets_read",
    "secrets_printed",
    "secrets_persisted",
    "private_key_value_emitted",
    "raw_private_key_emitted",
    "raw_secret_values_emitted",
    "credential_value_serialized",
    "raw_values_emitted",
    "wallet_connection_enabled",
    "wallet_connection_attempted",
    "wallet_enabled",
    "wallet_used",
    "wallet_signing_enabled",
    "wallet_signing_attempted",
    "cryptographic_signing_enabled",
    "cryptographic_signing_performed",
    "local_payload_signing_attempted",
    "local_payload_signed",
    "browser_automation_added",
    "scheduler_or_daemon_added",
    "background_worker_added",
    "autonomous_live_trading_added",
)

FORBIDDEN_VALUE_FIELD_NAMES = frozenset(
    {
        "private_key",
        "seed_phrase",
        "mnemonic",
        "api_secret",
        "auth_token",
        "passphrase",
        "secret",
        "raw_value",
        "masked_value",
        "signature",
        "signed_payload",
        "signed_order",
        "order_id",
        "client_order_id",
        "tx_hash",
        "transaction_hash",
        "fill_id",
        "fill",
        "fills",
        "fill_price",
        "filled_size",
        "execution_status",
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
class SelectedTokenPayloadReadinessSafetySnapshot:
    market_symbol: str = DEFAULT_ALLOWED_MARKET
    strategy_name: str = DEFAULT_ALLOWED_STRATEGY
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        value = {
            "contract_version": SELECTED_TOKEN_PAYLOAD_READINESS_SAFETY_SNAPSHOT_CONTRACT,
            "task_id": TASK_ID,
            "status": "active_selected_token_payload_readiness_safety_snapshot",
            "mode": MODE,
            "execution_mode": EXECUTION_MODE,
            "market": _market(self.market_symbol),
            "market_symbol": _market(self.market_symbol),
            "strategy_name": _strategy(self.strategy_name),
            "readiness_gate_only": True,
            "local_artifact_read_only": True,
            "default_mode_reads_private_key": False,
            "default_mode_signs_payload": False,
            "default_mode_builds_executable_payload": False,
            "selected_token_payload_ready_for_submit": False,
            "signing_by_default": False,
            "signer_ready_for_live": False,
            "order_submit_ready": False,
            "full_signed_payload_output": False,
            "future_signed_payload_diagnostic_requires_separate_operator_task": True,
            "full_signed_payload_output_allowed": False,
            "raw_private_key_output_allowed": False,
            "no_submit": True,
            "no_cancel": True,
            "no_trading_writes": True,
            "generated_at": self.generated_at,
        }
        value.update(selected_token_payload_readiness_safety_flags())
        return value


def selected_token_payload_readiness_safety_flags() -> dict[str, Any]:
    return {
        "execution_mode": EXECUTION_MODE,
        "mode": MODE,
        "review_only": True,
        "preflight_only": True,
        "dry_run_only": True,
        "paper_only": True,
        "non_executable": True,
        "local_artifact_only": True,
        "local_artifact_read_only": True,
        "readiness_gate_only": True,
        "allowed_for_live": False,
        "live": False,
        "selected_token_payload_ready_for_submit": False,
        "signing_by_default": False,
        "signer_ready_for_live": False,
        "order_submit_ready": False,
        "full_signed_payload_output": False,
        "live_execution_approved": False,
        "live_execution_allowed": False,
        "live_execution_performed": False,
        "real_execution_available": False,
        "real_order_submitted": False,
        "real_order_cancelled": False,
        "operator_approved": False,
        "order_generation_enabled": False,
        "order_generation_attempted": False,
        "order_payload_generated": False,
        "order_payload_executable": False,
        "order_payload_signing_enabled": False,
        "order_payload_signing_attempted": False,
        "order_payload_signed": False,
        "signing_enabled": False,
        "signing_attempted": False,
        "signed_order_generation_enabled": False,
        "signed_order_generation_attempted": False,
        "signed_order_generated": False,
        "signed_order_payload_generated": False,
        "signed_payload_generation_enabled": False,
        "signed_payload_generation_attempted": False,
        "signed_payload_generated": False,
        "signed_payload_fingerprint_stored": False,
        "full_signed_payload_emitted": False,
        "raw_signed_payload_emitted": False,
        "full_signed_order_emitted": False,
        "raw_signed_order_emitted": False,
        "signed_payload_submit_enabled": False,
        "signed_payload_submit_attempted": False,
        "signed_payload_submitted": False,
        "order_submission_enabled": False,
        "order_submission_attempted": False,
        "order_submission_performed": False,
        "order_submitted": False,
        "submit_call_performed": False,
        "order_cancel_enabled": False,
        "order_cancel_attempted": False,
        "order_cancel_performed": False,
        "order_cancellation_enabled": False,
        "order_cancellation_attempted": False,
        "order_cancellation_performed": False,
        "cancel_call_performed": False,
        "authenticated_polymarket_enabled": False,
        "authenticated_endpoint_enabled": False,
        "authenticated_request_performed": False,
        "authenticated_trading_enabled": False,
        "authenticated_trading_call_performed": False,
        "network_trading_call_performed": False,
        "network_trading_calls_performed": 0,
        "trading_write_call_performed": False,
        "network_write_call_performed": False,
        "network_write_performed": False,
        "network_post_performed": False,
        "network_put_performed": False,
        "network_patch_performed": False,
        "network_delete_performed": False,
        "private_key_read": False,
        "seed_phrase_read": False,
        "mnemonic_read": False,
        "api_secret_read": False,
        "auth_token_read": False,
        "passphrase_read": False,
        "credential_value_read": False,
        "credential_values_read": False,
        "credential_values_printed": False,
        "credential_values_stored": False,
        "credential_values_serialized": False,
        "environment_values_read": False,
        "secret_files_read": False,
        "secrets_read": False,
        "secrets_printed": False,
        "secrets_persisted": False,
        "private_key_value_emitted": False,
        "raw_private_key_emitted": False,
        "raw_secret_values_emitted": False,
        "credential_value_serialized": False,
        "raw_values_emitted": False,
        "wallet_connection_enabled": False,
        "wallet_connection_attempted": False,
        "wallet_enabled": False,
        "wallet_used": False,
        "wallet_signing_enabled": False,
        "wallet_signing_attempted": False,
        "cryptographic_signing_enabled": False,
        "cryptographic_signing_performed": False,
        "local_payload_signing_attempted": False,
        "local_payload_signed": False,
        "browser_automation_added": False,
        "scheduler_or_daemon_added": False,
        "background_worker_added": False,
        "autonomous_live_trading_added": False,
        "resolved_blocker_count": 0,
    }


def validate_selected_token_payload_readiness_gate_result(
    value: Mapping[str, Any],
    *,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    errors: list[str] = []
    statuses: list[str] = []

    if value.get("contract_version") != SELECTED_TOKEN_PAYLOAD_READINESS_RESULT_CONTRACT:
        errors.append("contract_version is not selected token payload readiness gate 073C result")
    if value.get("task_id") != TASK_ID:
        errors.append("task_id mismatch")
    if value.get("status") not in ALLOWED_STATUSES:
        errors.append("status is not recognized")
        statuses.append("unknown_status")
    if value.get("allowed_for_live") is not False:
        errors.append("allowed_for_live must be false")
        statuses.append("allowed_for_live_not_false")
    if value.get("selected_token_payload_ready_for_submit") is not False:
        errors.append("selected_token_payload_ready_for_submit must be false")
        statuses.append("submit_readiness_not_false")
    if value.get("dry_run") is not True:
        errors.append("dry_run must be true")
    if value.get("local_artifact_read_only") is not True:
        errors.append("local_artifact_read_only must be true")
    if value.get("status") == STATUS_READY and value.get("blocker_count") not in {0, "0"}:
        errors.append("ready status must not have readiness blockers")
        statuses.append("ready_with_blockers")

    for path, field, nested in _walk_fields(value):
        if field in REQUIRED_FALSE_FLAGS and nested is not False:
            errors.append(f"{path}.{field} must be false")
            statuses.append(f"{field}_not_false")
        if field == "resolved_blocker_count" and nested != 0:
            errors.append(f"{path}.resolved_blocker_count must be 0")
            statuses.append("resolved_blocker_count_not_zero")
        if field in FORBIDDEN_VALUE_FIELD_NAMES and nested:
            errors.append(f"{path}.{field} must not be emitted")
            statuses.append(f"{field}_emitted")

    return {
        "contract_version": SELECTED_TOKEN_PAYLOAD_READINESS_VALIDATION_CONTRACT,
        "task_id": TASK_ID,
        "valid": not errors,
        "status": "valid" if not errors else "invalid",
        "errors": _dedupe(errors),
        "validation_statuses": _dedupe(statuses),
        "allowed_for_live": False,
        "selected_token_payload_ready_for_submit": False,
        "generated_at": generated_at,
    }


def _market(value: Any) -> str:
    return clean_text(value).upper() or DEFAULT_ALLOWED_MARKET


def _strategy(value: Any) -> str:
    return clean_text(value) or DEFAULT_ALLOWED_STRATEGY


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
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        text = clean_text(value)
        if text and text not in seen:
            seen.add(text)
            out.append(text)
    return out
