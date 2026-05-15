from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from pm_bot.trading_core.schemas import GENERATED_AT, clean_text

TASK_ID = "ORCH-PMBOT-TRADING-MVP-070A-SIGNED-ORDER-PAYLOAD-DRY-RUN-NO-SUBMIT"

EXECUTION_MODE = "preflight"
MODE = "signed order payload dry-run / contract-only / no-submit"

DEFAULT_ALLOWED_MARKET = "BTC"
DEFAULT_ALLOWED_STRATEGY = "tiny-momentum"
DEFAULT_MAX_NOTIONAL_USD = 1.0

STATUS_BLOCKED_NO_SUBMIT = "blocked_non_executable_signed_order_payload_dry_run_no_submit"

LOCAL_DIAGNOSTIC_STATUS_NOT_REQUESTED = "diagnostic_not_requested"
LOCAL_DIAGNOSTIC_STATUS_MISSING_TOKEN_ID = "missing_token_id"
LOCAL_DIAGNOSTIC_STATUS_MAX_NOTIONAL_EXCEEDED = "max_notional_exceeded"
LOCAL_DIAGNOSTIC_STATUS_SIGNING_NOT_IMPLEMENTED = "signing_not_implemented"
LOCAL_DIAGNOSTIC_STATUS_DEPENDENCY_MISSING = "dependency_missing"

SIGNED_ORDER_PAYLOAD_DRY_RUN_RESULT_CONTRACT = "pmbot_signed_order_payload_dry_run_070a.v1"
SIGNED_ORDER_PAYLOAD_LATEST_STATUS_CONTRACT = "pmbot_latest_signed_order_payload_dry_run_status_070a.v1"
SIGNED_ORDER_PAYLOAD_CONTRACT_CONTRACT = "pmbot_signed_order_payload_contract_070a.v1"
SIGNED_ORDER_PAYLOAD_REDACTION_POLICY_CONTRACT = "pmbot_signed_order_payload_redaction_policy_070a.v1"
SIGNED_ORDER_PAYLOAD_SAFETY_CONTRACT = "pmbot_signed_order_payload_safety_contract_070a.v1"
SIGNED_ORDER_PAYLOAD_VALIDATION_CONTRACT = "pmbot_signed_order_payload_dry_run_validation_070a.v1"

REQUIRED_FALSE_FLAGS = (
    "allowed_for_live",
    "live_execution_approved",
    "live_execution_allowed",
    "live_execution_performed",
    "real_execution_available",
    "real_order_submitted",
    "real_order_cancelled",
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
    "signed_payload_submit_enabled",
    "signed_payload_submit_attempted",
    "signed_payload_submitted",
    "order_payload_signing_enabled",
    "order_payload_signing_attempted",
    "order_payload_signed",
    "signed_order_generation_enabled",
    "signed_order_generation_attempted",
    "signed_order_generated",
    "signed_order_payload_generated",
    "signed_payload_generated",
    "signed_payload_fingerprint_stored",
    "full_signed_payload_emitted",
    "raw_signed_payload_emitted",
    "full_signed_order_emitted",
    "raw_signed_order_emitted",
    "authenticated_trading_enabled",
    "authenticated_endpoint_enabled",
    "authenticated_request_performed",
    "authenticated_trading_call_performed",
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
    "environment_values_read",
    "secret_files_read",
    "private_key_value_emitted",
    "raw_private_key_emitted",
    "raw_secret_values_emitted",
    "credential_value_serialized",
    "credential_values_serialized",
    "credential_values_printed",
    "credential_values_stored",
    "credential_values_hashed",
    "credential_values_transformed",
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
    "scheduler_or_daemon_added",
    "background_worker_added",
    "autonomous_live_trading_added",
)

ALLOWED_LOCAL_DIAGNOSTIC_STATUSES = frozenset(
    {
        LOCAL_DIAGNOSTIC_STATUS_NOT_REQUESTED,
        LOCAL_DIAGNOSTIC_STATUS_MISSING_TOKEN_ID,
        LOCAL_DIAGNOSTIC_STATUS_MAX_NOTIONAL_EXCEEDED,
        LOCAL_DIAGNOSTIC_STATUS_SIGNING_NOT_IMPLEMENTED,
        LOCAL_DIAGNOSTIC_STATUS_DEPENDENCY_MISSING,
    }
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
class SignedOrderPayloadSafetyContract:
    market_symbol: str = DEFAULT_ALLOWED_MARKET
    strategy_name: str = DEFAULT_ALLOWED_STRATEGY
    max_notional_usd: float = DEFAULT_MAX_NOTIONAL_USD
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        value = {
            "contract_version": SIGNED_ORDER_PAYLOAD_SAFETY_CONTRACT,
            "task_id": TASK_ID,
            "status": "active_signed_order_payload_dry_run_safety_contract",
            "mode": MODE,
            "execution_mode": EXECUTION_MODE,
            "market": _market(self.market_symbol),
            "market_symbol": _market(self.market_symbol),
            "strategy_name": _strategy(self.strategy_name),
            "default_mode_reads_private_key": False,
            "default_mode_signs_payload": False,
            "default_mode_builds_executable_payload": False,
            "local_signing_diagnostic_requires_explicit_flag": True,
            "local_signing_diagnostic_requires_dry_run": True,
            "local_signing_diagnostic_max_notional_usd": DEFAULT_MAX_NOTIONAL_USD,
            "requested_max_notional_usd": _notional(self.max_notional_usd),
            "local_signing_diagnostic_requires_market_and_token_id": True,
            "signed_payload_output_allowed": False,
            "full_signed_payload_output_allowed": False,
            "raw_private_key_output_allowed": False,
            "no_network_writes": True,
            "no_submit": True,
            "no_cancel": True,
            "separate_future_operator_approval_required": True,
            "generated_at": self.generated_at,
        }
        value.update(signed_order_payload_safety_flags())
        return value


@dataclass(frozen=True)
class SignedOrderPayloadRedactionPolicy:
    market_symbol: str = DEFAULT_ALLOWED_MARKET
    strategy_name: str = DEFAULT_ALLOWED_STRATEGY
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        value = {
            "contract_version": SIGNED_ORDER_PAYLOAD_REDACTION_POLICY_CONTRACT,
            "task_id": TASK_ID,
            "status": "active_signed_order_payload_redaction_policy",
            "mode": MODE,
            "execution_mode": EXECUTION_MODE,
            "market": _market(self.market_symbol),
            "market_symbol": _market(self.market_symbol),
            "strategy_name": _strategy(self.strategy_name),
            "redaction_policy_exists": True,
            "redaction_required": True,
            "contract_output_format": "field_names_types_constraints_and_hash_fingerprints_only",
            "signed_material_output_format": "not_implemented_future_hash_fingerprint_metadata_only",
            "raw_private_key_output_allowed": False,
            "raw_secret_value_output_allowed": False,
            "full_signed_payload_output_allowed": False,
            "full_signed_order_output_allowed": False,
            "submitted_execution_result_output_allowed": False,
            "generated_at": self.generated_at,
        }
        value.update(signed_order_payload_safety_flags())
        return value


def signed_order_payload_safety_flags() -> dict[str, Any]:
    return {
        "execution_mode": EXECUTION_MODE,
        "mode": MODE,
        "review_only": True,
        "preflight_only": True,
        "dry_run_only": True,
        "paper_only": True,
        "non_executable": True,
        "local_artifact_only": True,
        "allowed_for_live": False,
        "live_execution_approved": False,
        "live_execution_allowed": False,
        "live_execution_performed": False,
        "real_execution_available": False,
        "real_order_submitted": False,
        "real_order_cancelled": False,
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
        "signed_payload_submit_enabled": False,
        "signed_payload_submit_attempted": False,
        "signed_payload_submitted": False,
        "order_payload_signing_enabled": False,
        "order_payload_signing_attempted": False,
        "order_payload_signed": False,
        "signed_order_generation_enabled": False,
        "signed_order_generation_attempted": False,
        "signed_order_generated": False,
        "signed_order_payload_generated": False,
        "signed_payload_generated": False,
        "signed_payload_fingerprint_stored": False,
        "full_signed_payload_emitted": False,
        "raw_signed_payload_emitted": False,
        "full_signed_order_emitted": False,
        "raw_signed_order_emitted": False,
        "authenticated_trading_enabled": False,
        "authenticated_endpoint_enabled": False,
        "authenticated_request_performed": False,
        "authenticated_trading_call_performed": False,
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
        "environment_values_read": False,
        "secret_files_read": False,
        "private_key_value_emitted": False,
        "raw_private_key_emitted": False,
        "raw_secret_values_emitted": False,
        "credential_value_serialized": False,
        "credential_values_serialized": False,
        "credential_values_printed": False,
        "credential_values_stored": False,
        "credential_values_hashed": False,
        "credential_values_transformed": False,
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
        "scheduler_or_daemon_added": False,
        "background_worker_added": False,
        "autonomous_live_trading_added": False,
        "resolved_blocker_count": 0,
    }


def validate_signed_order_payload_dry_run_result(
    result: Mapping[str, Any],
    *,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    value = dict(result or {})
    errors: list[str] = []
    statuses: list[str] = []
    if value.get("contract_version") != SIGNED_ORDER_PAYLOAD_DRY_RUN_RESULT_CONTRACT:
        errors.append(f"contract_version must be {SIGNED_ORDER_PAYLOAD_DRY_RUN_RESULT_CONTRACT}")
        statuses.append("invalid_contract")
    if value.get("local_signing_diagnostic_status") not in ALLOWED_LOCAL_DIAGNOSTIC_STATUSES:
        errors.append("local_signing_diagnostic_status is not recognized")
        statuses.append("unknown_local_diagnostic_status")
    for field in ("review_only", "preflight_only", "dry_run_only", "paper_only", "non_executable"):
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
            errors.append(f"{path}.{key} is forbidden in signed order payload dry-run artifacts")
            statuses.append("forbidden_value_field_detected")
    valid = not errors
    return {
        "contract_version": SIGNED_ORDER_PAYLOAD_VALIDATION_CONTRACT,
        "valid": valid,
        "status": "passed" if valid else "blocked_validation_failed",
        "statuses": _dedupe(statuses)
        or (["signed_order_payload_dry_run_valid"] if valid else ["signed_order_payload_dry_run_blocked"]),
        "errors": errors,
        "generated_at": generated_at,
        **signed_order_payload_safety_flags(),
    }


def _market(value: Any) -> str:
    return clean_text(value).upper() or DEFAULT_ALLOWED_MARKET


def _strategy(value: Any) -> str:
    return clean_text(value) or DEFAULT_ALLOWED_STRATEGY


def _notional(value: Any) -> float:
    if isinstance(value, bool):
        return DEFAULT_MAX_NOTIONAL_USD
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return DEFAULT_MAX_NOTIONAL_USD
    return numeric


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
