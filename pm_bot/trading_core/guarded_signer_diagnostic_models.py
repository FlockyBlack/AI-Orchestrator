from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from pm_bot.trading_core.schemas import GENERATED_AT, clean_text

TASK_ID = "ORCH-PMBOT-TRADING-MVP-069A-GUARDED-SIGNER-DIAGNOSTIC-SMOKE-NO-ORDER-NO-SUBMIT"

EXECUTION_MODE = "preflight"
MODE = "guarded signer diagnostic smoke / dry-run / no-order-no-submit"

DEFAULT_ALLOWED_MARKET = "BTC"
DEFAULT_ALLOWED_STRATEGY = "tiny-momentum"

DIAGNOSTIC_CHALLENGE = "PMBOT_SIGNER_DIAGNOSTIC_ONLY_NO_ORDER_NO_SUBMIT"

DIAGNOSTIC_STATUS_NOT_REQUESTED = "diagnostic_not_requested"
DIAGNOSTIC_STATUS_DEPENDENCY_MISSING = "dependency_missing"
DIAGNOSTIC_STATUS_MISSING_PRIVATE_KEY = "missing_private_key"
DIAGNOSTIC_STATUS_INVALID_KEY_FORMAT = "invalid_key_format"
DIAGNOSTIC_STATUS_MISSING_WALLET_ADDRESS = "missing_wallet_address"
DIAGNOSTIC_STATUS_WALLET_MISMATCH = "wallet_mismatch"
DIAGNOSTIC_STATUS_DIAGNOSTIC_OK = "diagnostic_ok"
DIAGNOSTIC_STATUS_DIAGNOSTIC_FAILED = "diagnostic_failed"

GUARDED_SIGNER_DIAGNOSTIC_RESULT_CONTRACT = "pmbot_guarded_signer_diagnostic_smoke_069a.v1"
GUARDED_SIGNER_DIAGNOSTIC_LATEST_STATUS_CONTRACT = "pmbot_latest_guarded_signer_diagnostic_status_069a.v1"
GUARDED_SIGNER_DIAGNOSTIC_SAFETY_CONTRACT = "pmbot_guarded_signer_diagnostic_safety_contract_069a.v1"
GUARDED_SIGNER_DIAGNOSTIC_REDACTION_POLICY_CONTRACT = (
    "pmbot_guarded_signer_diagnostic_redaction_policy_069a.v1"
)
GUARDED_SIGNER_DIAGNOSTIC_VALIDATION_CONTRACT = "pmbot_guarded_signer_diagnostic_validation_069a.v1"

REQUIRED_FALSE_FLAGS = (
    "allowed_for_live",
    "order_payload_signing_enabled",
    "order_payload_signing_attempted",
    "order_payload_signed",
    "order_payload_generated",
    "signed_order_generation_enabled",
    "signed_order_generation_attempted",
    "signed_order_generated",
    "signed_order_payload_generated",
    "signed_payload_generated",
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
    "authenticated_trading_enabled",
    "authenticated_endpoint_enabled",
    "authenticated_request_performed",
    "authenticated_trading_call_performed",
    "wallet_connection_enabled",
    "wallet_connection_attempted",
    "wallet_enabled",
    "wallet_used",
    "wallet_signing_enabled",
    "wallet_signing_attempted",
    "live_execution_approved",
    "live_execution_allowed",
    "live_execution_performed",
    "real_execution_available",
    "real_order_submitted",
    "real_order_cancelled",
    "private_key_value_emitted",
    "raw_private_key_emitted",
    "raw_secret_values_emitted",
    "full_diagnostic_signature_emitted",
    "raw_diagnostic_signature_emitted",
    "diagnostic_challenge_order_payload_fields_present",
    "scheduler_or_daemon_added",
    "background_worker_added",
    "autonomous_live_trading_added",
)

ALLOWED_DIAGNOSTIC_STATUSES = frozenset(
    {
        DIAGNOSTIC_STATUS_NOT_REQUESTED,
        DIAGNOSTIC_STATUS_DEPENDENCY_MISSING,
        DIAGNOSTIC_STATUS_MISSING_PRIVATE_KEY,
        DIAGNOSTIC_STATUS_INVALID_KEY_FORMAT,
        DIAGNOSTIC_STATUS_MISSING_WALLET_ADDRESS,
        DIAGNOSTIC_STATUS_WALLET_MISMATCH,
        DIAGNOSTIC_STATUS_DIAGNOSTIC_OK,
        DIAGNOSTIC_STATUS_DIAGNOSTIC_FAILED,
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
        "signed_payload",
        "signed_order",
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
        "position",
        "positions",
        "pnl",
        "realized_pnl",
        "unrealized_pnl",
    }
)


@dataclass(frozen=True)
class GuardedSignerDiagnosticSafetyContract:
    market_symbol: str = DEFAULT_ALLOWED_MARKET
    strategy_name: str = DEFAULT_ALLOWED_STRATEGY
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        value = {
            "contract_version": GUARDED_SIGNER_DIAGNOSTIC_SAFETY_CONTRACT,
            "task_id": TASK_ID,
            "status": "active_guarded_diagnostic_safety_contract",
            "mode": MODE,
            "execution_mode": EXECUTION_MODE,
            "market": _market(self.market_symbol),
            "market_symbol": _market(self.market_symbol),
            "strategy_name": _strategy(self.strategy_name),
            "diagnostic_requires_explicit_flag": True,
            "default_mode_reads_private_key": False,
            "diagnostic_challenge_is_not_order_payload": True,
            "no_order_payload_signing": True,
            "no_order_submission": True,
            "no_order_cancel": True,
            "no_authenticated_trading": True,
            "private_key_value_output_allowed": False,
            "full_signature_output_allowed": False,
            "generated_at": self.generated_at,
        }
        value.update(guarded_signer_diagnostic_safety_flags())
        return value


@dataclass(frozen=True)
class GuardedSignerDiagnosticRedactionPolicy:
    market_symbol: str = DEFAULT_ALLOWED_MARKET
    strategy_name: str = DEFAULT_ALLOWED_STRATEGY
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        value = {
            "contract_version": GUARDED_SIGNER_DIAGNOSTIC_REDACTION_POLICY_CONTRACT,
            "task_id": TASK_ID,
            "status": "active_guarded_diagnostic_redaction_policy",
            "mode": MODE,
            "execution_mode": EXECUTION_MODE,
            "market": _market(self.market_symbol),
            "market_symbol": _market(self.market_symbol),
            "strategy_name": _strategy(self.strategy_name),
            "redaction_policy_exists": True,
            "redaction_required": True,
            "private_key_value_output_allowed": False,
            "raw_secret_value_output_allowed": False,
            "full_diagnostic_signature_output_allowed": False,
            "address_output_format": "redacted_prefix_suffix_only",
            "diagnostic_signature_output_format": "redacted_hash_fingerprint_and_length_only",
            "diagnostic_challenge_payload_output_allowed": False,
            "order_payload_output_allowed": False,
            "generated_at": self.generated_at,
        }
        value.update(guarded_signer_diagnostic_safety_flags())
        return value


def guarded_signer_diagnostic_safety_flags() -> dict[str, Any]:
    return {
        "execution_mode": EXECUTION_MODE,
        "mode": MODE,
        "review_only": True,
        "preflight_only": True,
        "dry_run_only": True,
        "paper_only": True,
        "non_executable": True,
        "allowed_for_live": False,
        "no_order_payload_signing": True,
        "no_order_submission": True,
        "no_order_cancel": True,
        "no_authenticated_trading": True,
        "order_payload_signing_enabled": False,
        "order_payload_signing_attempted": False,
        "order_payload_signed": False,
        "order_payload_generated": False,
        "signed_order_generation_enabled": False,
        "signed_order_generation_attempted": False,
        "signed_order_generated": False,
        "signed_order_payload_generated": False,
        "signed_payload_generated": False,
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
        "authenticated_trading_enabled": False,
        "authenticated_endpoint_enabled": False,
        "authenticated_request_performed": False,
        "authenticated_trading_call_performed": False,
        "wallet_connection_enabled": False,
        "wallet_connection_attempted": False,
        "wallet_enabled": False,
        "wallet_used": False,
        "wallet_signing_enabled": False,
        "wallet_signing_attempted": False,
        "live_execution_approved": False,
        "live_execution_allowed": False,
        "live_execution_performed": False,
        "real_execution_available": False,
        "real_order_submitted": False,
        "real_order_cancelled": False,
        "private_key_value_emitted": False,
        "raw_private_key_emitted": False,
        "raw_secret_values_emitted": False,
        "full_diagnostic_signature_emitted": False,
        "raw_diagnostic_signature_emitted": False,
        "diagnostic_challenge_order_payload_fields_present": False,
        "scheduler_or_daemon_added": False,
        "background_worker_added": False,
        "autonomous_live_trading_added": False,
        "resolved_blocker_count": 0,
    }


def validate_guarded_signer_diagnostic_result(
    result: Mapping[str, Any],
    *,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    value = dict(result or {})
    errors: list[str] = []
    statuses: list[str] = []
    if value.get("contract_version") != GUARDED_SIGNER_DIAGNOSTIC_RESULT_CONTRACT:
        errors.append(f"contract_version must be {GUARDED_SIGNER_DIAGNOSTIC_RESULT_CONTRACT}")
        statuses.append("invalid_contract")
    if value.get("diagnostic_status") not in ALLOWED_DIAGNOSTIC_STATUSES:
        errors.append("diagnostic_status is not recognized")
        statuses.append("unknown_diagnostic_status")
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
            errors.append(f"{path}.{key} is forbidden in guarded signer diagnostic artifacts")
            statuses.append("forbidden_value_field_detected")
    valid = not errors
    return {
        "contract_version": GUARDED_SIGNER_DIAGNOSTIC_VALIDATION_CONTRACT,
        "valid": valid,
        "status": "passed" if valid else "blocked_validation_failed",
        "statuses": _dedupe(statuses)
        or (["guarded_signer_diagnostic_valid"] if valid else ["guarded_signer_diagnostic_blocked"]),
        "errors": errors,
        "generated_at": generated_at,
        **guarded_signer_diagnostic_safety_flags(),
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
