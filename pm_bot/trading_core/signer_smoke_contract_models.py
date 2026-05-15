from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from pm_bot.trading_core.schemas import GENERATED_AT, clean_text

TASK_ID = "ORCH-PMBOT-TRADING-MVP-068A-SIGNER-SMOKE-CONTRACT-NO-ORDER-NO-SUBMIT"

EXECUTION_MODE = "preflight"
MODE = "signer smoke contract / contract-only / dry-run"
STATUS_BLOCKED = "blocked_contract_only_no_signer_smoke_execution"

SIGNER_SMOKE_FUTURE_CONTRACT = "pmbot_signer_smoke_future_contract_068a.v1"
SIGNER_SMOKE_SAFETY_CONTRACT = "pmbot_signer_smoke_safety_contract_068a.v1"
SIGNER_SMOKE_REDACTION_POLICY_CONTRACT = "pmbot_signer_smoke_redaction_policy_068a.v1"
SIGNER_SMOKE_CONTRACT_RESULT_CONTRACT = "pmbot_signer_smoke_contract_068a.v1"
SIGNER_SMOKE_LATEST_STATUS_CONTRACT = "pmbot_latest_signer_smoke_contract_status_068a.v1"
SIGNER_SMOKE_VALIDATION_CONTRACT = "pmbot_signer_smoke_contract_validation_068a.v1"

DEFAULT_ALLOWED_MARKET = "BTC"
DEFAULT_ALLOWED_STRATEGY = "tiny-momentum"

REQUIRED_FALSE_FLAGS = (
    "allowed_for_live",
    "signer_smoke_executable",
    "signer_smoke_execution_enabled",
    "signer_smoke_executed",
    "signer_smoke_live_mode_enabled",
    "private_key_read",
    "polymarket_private_key_read",
    "seed_phrase_read",
    "mnemonic_read",
    "api_secret_read",
    "auth_token_read",
    "credential_value_read",
    "credential_values_read",
    "credential_value_serialized",
    "credential_values_serialized",
    "credential_value_printed",
    "credential_values_printed",
    "credential_value_stored",
    "credential_values_stored",
    "credential_value_hashed",
    "credential_values_hashed",
    "credential_value_transformed",
    "credential_values_transformed",
    "environment_values_read",
    "secret_files_read",
    "raw_key_material_logged",
    "raw_key_material_emitted",
    "redacted_key_material_emitted",
    "address_derivation_enabled",
    "address_derivation_performed",
    "derived_address_emitted",
    "diagnostic_challenge_signing_enabled",
    "diagnostic_challenge_signing_attempted",
    "diagnostic_challenge_signed",
    "diagnostic_challenge_output_emitted",
    "order_payload_signing_enabled",
    "order_payload_signing_attempted",
    "order_payload_signed",
    "order_payload_generated",
    "signed_payload_generated",
    "signed_order_payload_generated",
    "signed_order_generation_enabled",
    "signed_order_generation_attempted",
    "order_submission_enabled",
    "order_submission_attempted",
    "order_submission_performed",
    "order_cancellation_enabled",
    "order_cancellation_attempted",
    "order_cancellation_performed",
    "authenticated_trading_enabled",
    "authenticated_endpoint_enabled",
    "authenticated_request_performed",
    "wallet_connection_enabled",
    "wallet_connection_attempted",
    "wallet_enabled",
    "wallet_used",
    "wallet_signing_enabled",
    "wallet_signing_attempted",
    "cryptographic_signing_enabled",
    "cryptographic_signing_performed",
    "live_execution_approved",
    "live_execution_allowed",
    "live_execution_performed",
    "real_execution_available",
    "real_order_submitted",
    "order_submitted",
    "real_order_cancelled",
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
class FutureSignerSmokeContract:
    market_symbol: str = DEFAULT_ALLOWED_MARKET
    strategy_name: str = DEFAULT_ALLOWED_STRATEGY
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        value = {
            "contract_version": SIGNER_SMOKE_FUTURE_CONTRACT,
            "task_id": TASK_ID,
            "status": STATUS_BLOCKED,
            "mode": MODE,
            "execution_mode": EXECUTION_MODE,
            "market": _market(self.market_symbol),
            "market_symbol": _market(self.market_symbol),
            "strategy_name": _strategy(self.strategy_name),
            "contract_only": True,
            "future_mode_documented": True,
            "future_mode_enabled": False,
            "future_mode_requires_separate_operator_approved_task": True,
            "future_credential_source_marker": "POLYMARKET_PRIVATE_KEY",
            "future_credential_source_value_allowed_in_artifacts": False,
            "future_allowed_diagnostic_checks": [
                {
                    "check_id": "address_derivation",
                    "future_may_verify": True,
                    "currently_enabled": False,
                    "uses_order_payload": False,
                    "emits_address_value": False,
                    "operator_note": "Future opt-in smoke may derive an address without logging raw keys.",
                },
                {
                    "check_id": "diagnostic_challenge_signing",
                    "future_may_verify": True,
                    "currently_enabled": False,
                    "uses_order_payload": False,
                    "emits_signed_material": False,
                    "operator_note": "Future opt-in smoke may use a non-order diagnostic challenge only.",
                },
            ],
            "future_explicit_non_goals": [
                "no order payload",
                "no order signing",
                "no order submit",
                "no order cancel",
                "no raw key log",
                "no wallet UI",
                "no authenticated trading call",
            ],
            "operator_summary": (
                "068A defines a future signer smoke contract only. It documents address derivation and "
                "non-order diagnostic challenge signing as possible future checks, but they are not enabled here."
            ),
            "generated_at": self.generated_at,
        }
        value.update(signer_smoke_safety_flags())
        return value


@dataclass(frozen=True)
class SignerSmokeSafetyContract:
    market_symbol: str = DEFAULT_ALLOWED_MARKET
    strategy_name: str = DEFAULT_ALLOWED_STRATEGY
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        value = {
            "contract_version": SIGNER_SMOKE_SAFETY_CONTRACT,
            "task_id": TASK_ID,
            "status": STATUS_BLOCKED,
            "mode": MODE,
            "execution_mode": EXECUTION_MODE,
            "market": _market(self.market_symbol),
            "market_symbol": _market(self.market_symbol),
            "strategy_name": _strategy(self.strategy_name),
            "all_current_signer_smoke_checks_disabled": True,
            "order_payload_boundary_enforced": True,
            "raw_key_output_boundary_enforced": True,
            "separate_future_live_task_required": True,
            "operator_approval_does_not_exist_in_this_task": True,
            "generated_at": self.generated_at,
        }
        value.update(signer_smoke_safety_flags())
        return value


@dataclass(frozen=True)
class SignerSmokeRedactionPolicy:
    market_symbol: str = DEFAULT_ALLOWED_MARKET
    strategy_name: str = DEFAULT_ALLOWED_STRATEGY
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        value = {
            "contract_version": SIGNER_SMOKE_REDACTION_POLICY_CONTRACT,
            "task_id": TASK_ID,
            "status": "active_for_contract_only_artifacts",
            "mode": MODE,
            "execution_mode": EXECUTION_MODE,
            "market": _market(self.market_symbol),
            "market_symbol": _market(self.market_symbol),
            "strategy_name": _strategy(self.strategy_name),
            "redaction_policy_exists": True,
            "redaction_required": True,
            "presence_booleans_only": True,
            "credential_value_output_allowed": False,
            "derived_address_output_allowed": False,
            "diagnostic_challenge_output_allowed": False,
            "order_payload_output_allowed": False,
            "raw_values_emitted": False,
            "operator_summary": (
                "Artifacts may contain only static booleans, review labels, and future-mode requirements. "
                "Credential values, derived addresses, diagnostic signed material, order payloads, and "
                "execution identifiers are forbidden."
            ),
            "generated_at": self.generated_at,
        }
        value.update(signer_smoke_safety_flags())
        return value


def signer_smoke_safety_flags() -> dict[str, Any]:
    return {
        "execution_mode": EXECUTION_MODE,
        "mode": MODE,
        "review_only": True,
        "preflight_only": True,
        "dry_run_only": True,
        "paper_only": True,
        "contract_only": True,
        "non_executable": True,
        "allowed_for_live": False,
        "signer_smoke_executable": False,
        "signer_smoke_execution_enabled": False,
        "signer_smoke_executed": False,
        "signer_smoke_live_mode_enabled": False,
        "private_key_read": False,
        "polymarket_private_key_read": False,
        "seed_phrase_read": False,
        "mnemonic_read": False,
        "api_secret_read": False,
        "auth_token_read": False,
        "credential_value_read": False,
        "credential_values_read": False,
        "credential_value_serialized": False,
        "credential_values_serialized": False,
        "credential_value_printed": False,
        "credential_values_printed": False,
        "credential_value_stored": False,
        "credential_values_stored": False,
        "credential_value_hashed": False,
        "credential_values_hashed": False,
        "credential_value_transformed": False,
        "credential_values_transformed": False,
        "environment_values_read": False,
        "secret_files_read": False,
        "raw_key_material_logged": False,
        "raw_key_material_emitted": False,
        "redacted_key_material_emitted": False,
        "address_derivation_enabled": False,
        "address_derivation_performed": False,
        "derived_address_emitted": False,
        "diagnostic_challenge_signing_enabled": False,
        "diagnostic_challenge_signing_attempted": False,
        "diagnostic_challenge_signed": False,
        "diagnostic_challenge_output_emitted": False,
        "order_payload_signing_enabled": False,
        "order_payload_signing_attempted": False,
        "order_payload_signed": False,
        "order_payload_generated": False,
        "signed_payload_generated": False,
        "signed_order_payload_generated": False,
        "signed_order_generation_enabled": False,
        "signed_order_generation_attempted": False,
        "order_submission_enabled": False,
        "order_submission_attempted": False,
        "order_submission_performed": False,
        "order_cancellation_enabled": False,
        "order_cancellation_attempted": False,
        "order_cancellation_performed": False,
        "authenticated_trading_enabled": False,
        "authenticated_endpoint_enabled": False,
        "authenticated_request_performed": False,
        "wallet_connection_enabled": False,
        "wallet_connection_attempted": False,
        "wallet_enabled": False,
        "wallet_used": False,
        "wallet_signing_enabled": False,
        "wallet_signing_attempted": False,
        "cryptographic_signing_enabled": False,
        "cryptographic_signing_performed": False,
        "live_execution_approved": False,
        "live_execution_allowed": False,
        "live_execution_performed": False,
        "real_execution_available": False,
        "real_order_submitted": False,
        "order_submitted": False,
        "real_order_cancelled": False,
        "scheduler_or_daemon_added": False,
        "background_worker_added": False,
        "autonomous_live_trading_added": False,
        "resolved_blocker_count": 0,
    }


def validate_signer_smoke_contract(
    result: Mapping[str, Any],
    *,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    value = dict(result or {})
    errors: list[str] = []
    statuses: list[str] = []
    if value.get("contract_version") != SIGNER_SMOKE_CONTRACT_RESULT_CONTRACT:
        errors.append(f"contract_version must be {SIGNER_SMOKE_CONTRACT_RESULT_CONTRACT}")
        statuses.append("invalid_contract")
    for field in ("review_only", "preflight_only", "dry_run_only", "contract_only", "non_executable"):
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
            errors.append(f"{path}.{key} is forbidden in signer smoke contract artifacts")
            statuses.append("forbidden_value_field_detected")
    valid = not errors
    return {
        "contract_version": SIGNER_SMOKE_VALIDATION_CONTRACT,
        "valid": valid,
        "status": "passed" if valid else STATUS_BLOCKED,
        "statuses": _dedupe(statuses)
        or (["signer_smoke_contract_valid"] if valid else ["signer_smoke_contract_blocked"]),
        "errors": errors,
        "generated_at": generated_at,
        **signer_smoke_safety_flags(),
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
