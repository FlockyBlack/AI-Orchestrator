from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from pm_bot.trading_core.schemas import GENERATED_AT, clean_text

TASK_ID = "ORCH-PMBOT-TRADING-MVP-072E-SIGNED-PAYLOAD-DIAGNOSTIC-ADAPTER-SCAFFOLD-NO-SUBMIT"

EXECUTION_MODE = "preflight"
MODE = "signed payload diagnostic adapter / dry-run / unsigned-readiness / no-submit"

DEFAULT_ALLOWED_MARKET = "BTC"
DEFAULT_ALLOWED_STRATEGY = "tiny-momentum"

STATUS_UNSIGNED_READY = "unsigned_diagnostic_readiness_ready_no_signing"
STATUS_BLOCKED_MISSING_REQUIRED_ARTIFACTS = "blocked_missing_required_local_artifacts"
STATUS_BLOCKED_REQUIRED_FIELDS = "blocked_required_fields_missing"
STATUS_BLOCKED_TOKEN_SELECTION = "blocked_selected_token_candidate_not_ready"
STATUS_BLOCKED_FUTURE_SIGNING_NOT_IMPLEMENTED = "blocked_future_signing_not_implemented"

SIGNED_PAYLOAD_DIAGNOSTIC_ADAPTER_RESULT_CONTRACT = "pmbot_signed_payload_diagnostic_adapter_072e.v1"
SIGNED_PAYLOAD_DIAGNOSTIC_ADAPTER_LATEST_STATUS_CONTRACT = (
    "pmbot_latest_signed_payload_diagnostic_adapter_status_072e.v1"
)
SIGNED_PAYLOAD_DIAGNOSTIC_ADAPTER_CONTRACT = "pmbot_signed_payload_diagnostic_adapter_contract_072e.v1"
SIGNED_PAYLOAD_DIAGNOSTIC_ADAPTER_REDACTION_POLICY_CONTRACT = (
    "pmbot_signed_payload_diagnostic_adapter_redaction_policy_072e.v1"
)
SIGNED_PAYLOAD_DIAGNOSTIC_ADAPTER_SAFETY_SNAPSHOT_CONTRACT = (
    "pmbot_signed_payload_diagnostic_adapter_safety_snapshot_072e.v1"
)
SIGNED_PAYLOAD_DIAGNOSTIC_ADAPTER_VALIDATION_CONTRACT = (
    "pmbot_signed_payload_diagnostic_adapter_validation_072e.v1"
)

ALLOWED_STATUSES = frozenset(
    {
        STATUS_UNSIGNED_READY,
        STATUS_BLOCKED_MISSING_REQUIRED_ARTIFACTS,
        STATUS_BLOCKED_REQUIRED_FIELDS,
        STATUS_BLOCKED_TOKEN_SELECTION,
        STATUS_BLOCKED_FUTURE_SIGNING_NOT_IMPLEMENTED,
    }
)

REQUIRED_FALSE_FLAGS = (
    "allowed_for_live",
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
    "credential_values_hashed",
    "credential_values_transformed",
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
    "future_signing_implemented",
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
class SignedPayloadDiagnosticAdapterRedactionPolicy:
    market_symbol: str = DEFAULT_ALLOWED_MARKET
    strategy_name: str = DEFAULT_ALLOWED_STRATEGY
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        value = {
            "contract_version": SIGNED_PAYLOAD_DIAGNOSTIC_ADAPTER_REDACTION_POLICY_CONTRACT,
            "task_id": TASK_ID,
            "status": "active_signed_payload_diagnostic_adapter_redaction_policy",
            "mode": MODE,
            "execution_mode": EXECUTION_MODE,
            "market": _market(self.market_symbol),
            "market_symbol": _market(self.market_symbol),
            "strategy_name": _strategy(self.strategy_name),
            "redaction_policy_exists": True,
            "redaction_required": True,
            "token_id_output_format": "presence_and_sha256_fingerprint_only",
            "source_payload_output_format": "contract_version_status_paths_and_safe_flags_only",
            "raw_private_key_output_allowed": False,
            "raw_secret_value_output_allowed": False,
            "full_signed_payload_output_allowed": False,
            "raw_signed_payload_output_allowed": False,
            "full_signed_order_output_allowed": False,
            "execution_identifier_output_allowed": False,
            "generated_at": self.generated_at,
        }
        value.update(signed_payload_diagnostic_adapter_safety_flags())
        return value


@dataclass(frozen=True)
class SignedPayloadDiagnosticAdapterSafetySnapshot:
    market_symbol: str = DEFAULT_ALLOWED_MARKET
    strategy_name: str = DEFAULT_ALLOWED_STRATEGY
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        value = {
            "contract_version": SIGNED_PAYLOAD_DIAGNOSTIC_ADAPTER_SAFETY_SNAPSHOT_CONTRACT,
            "task_id": TASK_ID,
            "status": "active_signed_payload_diagnostic_adapter_safety_snapshot",
            "mode": MODE,
            "execution_mode": EXECUTION_MODE,
            "market": _market(self.market_symbol),
            "market_symbol": _market(self.market_symbol),
            "strategy_name": _strategy(self.strategy_name),
            "default_mode_reads_private_key": False,
            "default_mode_signs_payload": False,
            "default_mode_builds_executable_payload": False,
            "future_signing_requires_separate_operator_approved_task": True,
            "future_signing_status": "not_implemented_blocked",
            "signed_payload_output_allowed": False,
            "full_signed_payload_output_allowed": False,
            "raw_private_key_output_allowed": False,
            "no_submit": True,
            "no_cancel": True,
            "no_trading_writes": True,
            "local_artifact_read_only": True,
            "generated_at": self.generated_at,
        }
        value.update(signed_payload_diagnostic_adapter_safety_flags())
        return value


def signed_payload_diagnostic_adapter_safety_flags() -> dict[str, Any]:
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
        "unsigned_readiness_only": True,
        "allowed_for_live": False,
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
        "polymarket_api_calls_performed": 0,
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
        "credential_values_hashed": False,
        "credential_values_transformed": False,
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
        "future_signing_implemented": False,
        "resolved_blocker_count": 0,
    }


def validate_signed_payload_diagnostic_adapter_result(
    result: Mapping[str, Any],
    *,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    value = dict(result or {})
    adapter_contract = dict(value.get("adapter_contract", {}))
    errors: list[str] = []
    statuses: list[str] = []
    if value.get("contract_version") != SIGNED_PAYLOAD_DIAGNOSTIC_ADAPTER_RESULT_CONTRACT:
        errors.append(f"contract_version must be {SIGNED_PAYLOAD_DIAGNOSTIC_ADAPTER_RESULT_CONTRACT}")
        statuses.append("invalid_contract")
    if value.get("status") not in ALLOWED_STATUSES:
        errors.append("status is not recognized")
        statuses.append("unknown_status")
    if adapter_contract.get("contract_version") != SIGNED_PAYLOAD_DIAGNOSTIC_ADAPTER_CONTRACT:
        errors.append(f"adapter_contract.contract_version must be {SIGNED_PAYLOAD_DIAGNOSTIC_ADAPTER_CONTRACT}")
        statuses.append("invalid_adapter_contract")
    for field in (
        "review_only",
        "preflight_only",
        "dry_run_only",
        "paper_only",
        "non_executable",
        "unsigned_readiness_only",
    ):
        if value.get(field) is not True:
            errors.append(f"{field} must be true")
            statuses.append(f"{field}_missing")
    if value.get("resolved_blocker_count") != 0:
        errors.append("resolved_blocker_count must be 0")
        statuses.append("resolved_blocker_detected")
    for field in REQUIRED_FALSE_FLAGS:
        if value.get(field) is not False:
            errors.append(f"{field} must be false")
            statuses.append("unsafe_false_flag_detected")
    for path, key, nested in _walk_fields(value):
        if key in REQUIRED_FALSE_FLAGS and nested is not False:
            errors.append(f"{path}.{key} must be false")
            statuses.append("nested_unsafe_false_flag_detected")
        if key == "resolved_blocker_count" and nested != 0:
            errors.append(f"{path}.{key} must be 0")
            statuses.append("nested_resolved_blocker_detected")
        if key in FORBIDDEN_VALUE_FIELD_NAMES:
            errors.append(f"{path}.{key} is forbidden in signed payload diagnostic adapter artifacts")
            statuses.append("forbidden_value_field_detected")
    valid = not errors
    return {
        "contract_version": SIGNED_PAYLOAD_DIAGNOSTIC_ADAPTER_VALIDATION_CONTRACT,
        "task_id": TASK_ID,
        "valid": valid,
        "status": "passed" if valid else "blocked_validation_failed",
        "statuses": _dedupe(statuses)
        or (
            ["signed_payload_diagnostic_adapter_valid"]
            if valid
            else ["signed_payload_diagnostic_adapter_blocked"]
        ),
        "errors": errors,
        "generated_at": generated_at,
        **signed_payload_diagnostic_adapter_safety_flags(),
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
    result: list[str] = []
    for value in values:
        text = clean_text(value)
        if text and text not in result:
            result.append(text)
    return result
