from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from pm_bot.trading_core.schemas import GENERATED_AT, clean_text

TASK_ID = "ORCH-PMBOT-TRADING-MVP-065B-SIGNER-ORDER-BOUNDARY-SKELETON-NO-SECRETS-NO-ORDERS"

EXECUTION_MODE = "preflight"
MODE = "non-executable signer/order boundary skeleton / interface-only / review-only"
STATUS_BLOCKED = "blocked_non_executable_boundary_skeleton"

NON_EXECUTABLE_SIGNER_BOUNDARY_CONTRACT = "pmbot_non_executable_signer_boundary_065b.v1"
NON_EXECUTABLE_ORDER_SUBMISSION_BOUNDARY_CONTRACT = (
    "pmbot_non_executable_order_submission_boundary_065b.v1"
)
NON_EXECUTABLE_ORDER_CANCEL_BOUNDARY_CONTRACT = "pmbot_non_executable_order_cancel_boundary_065b.v1"
LIVE_BOUNDARY_SAFETY_CONTRACT = "pmbot_live_boundary_safety_contract_065b.v1"
LIVE_ORDER_REDACTION_POLICY_CONTRACT = "pmbot_live_order_redaction_policy_065b.v1"
FUTURE_LIVE_ORDER_BOUNDARY_CHECKLIST_CONTRACT = "pmbot_future_live_order_boundary_checklist_065b.v1"
LIVE_ORDER_NON_EXECUTABLE_INTERFACES_CONTRACT = "pmbot_live_order_non_executable_interfaces_065b.v1"
LIVE_ORDER_BOUNDARY_CONTRACT_RESULT_CONTRACT = "pmbot_live_order_boundary_contract_065b.v1"
LIVE_ORDER_BOUNDARY_LATEST_STATUS_CONTRACT = "pmbot_latest_live_order_boundary_contract_status_065b.v1"
LIVE_ORDER_BOUNDARY_VALIDATION_CONTRACT = "pmbot_live_order_boundary_validation_065b.v1"

DEFAULT_ALLOWED_MARKET = "BTC"
DEFAULT_ALLOWED_STRATEGY = "tiny-momentum"

REQUIRED_FALSE_FLAGS = (
    "signer_boundary_available",
    "signer_available",
    "signer_instantiated",
    "signing_enabled",
    "signing_attempted",
    "wallet_signing_enabled",
    "cryptographic_signing_enabled",
    "cryptographic_signing_performed",
    "private_key_read",
    "seed_phrase_read",
    "mnemonic_read",
    "api_secret_read",
    "auth_token_read",
    "credential_value_read",
    "credential_values_read",
    "environment_values_read",
    "secret_files_read",
    "credential_value_serialized",
    "credential_values_serialized",
    "credential_values_printed",
    "credential_values_stored",
    "credential_values_hashed",
    "credential_values_transformed",
    "signed_payload_generation_enabled",
    "signed_order_generation_enabled",
    "signed_payload_generated",
    "signed_order_payload_generated",
    "order_payload_generation_enabled",
    "order_payload_generated",
    "order_submission_boundary_available",
    "order_submission_enabled",
    "order_submission_attempted",
    "order_submission_performed",
    "order_cancel_boundary_available",
    "order_cancel_enabled",
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
    "live_execution_approved",
    "live_execution_allowed",
    "live_execution_performed",
    "real_execution_available",
    "real_order_submitted",
    "order_submitted",
    "real_order_cancelled",
    "allowed_for_live",
    "boundary_is_executable",
    "candidate_is_executable",
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
class NonExecutableSignerBoundary:
    market_symbol: str = DEFAULT_ALLOWED_MARKET
    strategy_name: str = DEFAULT_ALLOWED_STRATEGY
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        value = {
            "contract_version": NON_EXECUTABLE_SIGNER_BOUNDARY_CONTRACT,
            "task_id": TASK_ID,
            "boundary_name": "non_executable_signer_boundary_065b",
            "status": STATUS_BLOCKED,
            "mode": MODE,
            "execution_mode": EXECUTION_MODE,
            "market": _market(self.market_symbol),
            "market_symbol": _market(self.market_symbol),
            "strategy_name": _strategy(self.strategy_name),
            "interface_only": True,
            "review_only": True,
            "preflight_only": True,
            "dry_run_only": True,
            "paper_only": True,
            "non_executable": True,
            "boundary_is_executable": False,
            "signer_boundary_available": False,
            "signer_available": False,
            "signer_instantiated": False,
            "private_key_read": False,
            "seed_phrase_read": False,
            "mnemonic_read": False,
            "api_secret_read": False,
            "auth_token_read": False,
            "credential_value_read": False,
            "credential_values_read": False,
            "environment_values_read": False,
            "secret_files_read": False,
            "credential_value_serialized": False,
            "credential_values_serialized": False,
            "credential_values_printed": False,
            "credential_values_stored": False,
            "credential_values_hashed": False,
            "credential_values_transformed": False,
            "signing_enabled": False,
            "signing_attempted": False,
            "wallet_signing_enabled": False,
            "cryptographic_signing_enabled": False,
            "cryptographic_signing_performed": False,
            "signed_payload_generation_enabled": False,
            "signed_order_generation_enabled": False,
            "signed_payload_generated": False,
            "signed_order_payload_generated": False,
            "wallet_connection_enabled": False,
            "wallet_connection_attempted": False,
            "wallet_enabled": False,
            "wallet_used": False,
            "allowed_for_live": False,
            "operator_summary": (
                "Signer boundary is an interface-only placeholder. It cannot instantiate a signer, read "
                "credential material, connect a wallet, or create any signed material."
            ),
            "generated_at": self.generated_at,
        }
        value.update(live_boundary_safety_flags())
        return value


@dataclass(frozen=True)
class NonExecutableOrderSubmissionBoundary:
    market_symbol: str = DEFAULT_ALLOWED_MARKET
    strategy_name: str = DEFAULT_ALLOWED_STRATEGY
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        value = {
            "contract_version": NON_EXECUTABLE_ORDER_SUBMISSION_BOUNDARY_CONTRACT,
            "task_id": TASK_ID,
            "boundary_name": "non_executable_order_submission_boundary_065b",
            "status": STATUS_BLOCKED,
            "mode": MODE,
            "execution_mode": EXECUTION_MODE,
            "market": _market(self.market_symbol),
            "market_symbol": _market(self.market_symbol),
            "strategy_name": _strategy(self.strategy_name),
            "interface_only": True,
            "review_only": True,
            "preflight_only": True,
            "dry_run_only": True,
            "paper_only": True,
            "non_executable": True,
            "boundary_is_executable": False,
            "order_submission_boundary_available": False,
            "order_submission_enabled": False,
            "order_submission_attempted": False,
            "order_submission_performed": False,
            "order_payload_generation_enabled": False,
            "order_payload_generated": False,
            "authenticated_trading_enabled": False,
            "authenticated_endpoint_enabled": False,
            "authenticated_request_performed": False,
            "signed_payload_generation_enabled": False,
            "signed_payload_generated": False,
            "wallet_connection_enabled": False,
            "wallet_connection_attempted": False,
            "allowed_for_live": False,
            "operator_summary": (
                "Order submission boundary is a non-executable interface record only. It has no executable "
                "submission path and cannot create or transmit an order payload."
            ),
            "generated_at": self.generated_at,
        }
        value.update(live_boundary_safety_flags())
        return value


@dataclass(frozen=True)
class NonExecutableOrderCancelBoundary:
    market_symbol: str = DEFAULT_ALLOWED_MARKET
    strategy_name: str = DEFAULT_ALLOWED_STRATEGY
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        value = {
            "contract_version": NON_EXECUTABLE_ORDER_CANCEL_BOUNDARY_CONTRACT,
            "task_id": TASK_ID,
            "boundary_name": "non_executable_order_cancel_boundary_065b",
            "status": STATUS_BLOCKED,
            "mode": MODE,
            "execution_mode": EXECUTION_MODE,
            "market": _market(self.market_symbol),
            "market_symbol": _market(self.market_symbol),
            "strategy_name": _strategy(self.strategy_name),
            "interface_only": True,
            "review_only": True,
            "preflight_only": True,
            "dry_run_only": True,
            "paper_only": True,
            "non_executable": True,
            "boundary_is_executable": False,
            "order_cancel_boundary_available": False,
            "order_cancel_enabled": False,
            "order_cancellation_enabled": False,
            "order_cancellation_attempted": False,
            "order_cancellation_performed": False,
            "authenticated_trading_enabled": False,
            "authenticated_endpoint_enabled": False,
            "authenticated_request_performed": False,
            "wallet_connection_enabled": False,
            "wallet_connection_attempted": False,
            "allowed_for_live": False,
            "operator_summary": (
                "Order cancellation boundary is a non-executable interface record only. It has no executable "
                "cancellation path and cannot transmit cancellation intent."
            ),
            "generated_at": self.generated_at,
        }
        value.update(live_boundary_safety_flags())
        return value


@dataclass(frozen=True)
class LiveBoundarySafetyContract:
    market_symbol: str = DEFAULT_ALLOWED_MARKET
    strategy_name: str = DEFAULT_ALLOWED_STRATEGY
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        value = {
            "contract_version": LIVE_BOUNDARY_SAFETY_CONTRACT,
            "task_id": TASK_ID,
            "status": STATUS_BLOCKED,
            "mode": MODE,
            "execution_mode": EXECUTION_MODE,
            "market": _market(self.market_symbol),
            "market_symbol": _market(self.market_symbol),
            "strategy_name": _strategy(self.strategy_name),
            "all_boundaries_non_executable": True,
            "all_boundaries_interface_only": True,
            "separate_future_live_task_required": True,
            "operator_approval_does_not_exist_in_this_task": True,
            "generated_at": self.generated_at,
        }
        value.update(live_boundary_safety_flags())
        return value


@dataclass(frozen=True)
class RedactionPolicy:
    market_symbol: str = DEFAULT_ALLOWED_MARKET
    strategy_name: str = DEFAULT_ALLOWED_STRATEGY
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        value = {
            "contract_version": LIVE_ORDER_REDACTION_POLICY_CONTRACT,
            "task_id": TASK_ID,
            "status": "active_for_non_executable_boundary_artifacts",
            "mode": MODE,
            "execution_mode": EXECUTION_MODE,
            "market": _market(self.market_symbol),
            "market_symbol": _market(self.market_symbol),
            "strategy_name": _strategy(self.strategy_name),
            "redaction_policy_exists": True,
            "redaction_required": True,
            "value_fields_forbidden": True,
            "presence_booleans_only": True,
            "raw_values_emitted": False,
            "credential_value_read": False,
            "credential_values_read": False,
            "credential_value_serialized": False,
            "credential_values_serialized": False,
            "credential_values_printed": False,
            "credential_values_stored": False,
            "credential_values_hashed": False,
            "credential_values_transformed": False,
            "operator_summary": (
                "Artifacts may contain only static boundary flags and review labels. Credential-like values, "
                "signatures, executable payloads, account state, and execution identifiers are forbidden."
            ),
            "generated_at": self.generated_at,
        }
        value.update(live_boundary_safety_flags())
        return value


@dataclass(frozen=True)
class FutureLiveOrderBoundaryChecklist:
    safety_contract: Mapping[str, Any]
    redaction_policy: Mapping[str, Any]
    market_symbol: str = DEFAULT_ALLOWED_MARKET
    strategy_name: str = DEFAULT_ALLOWED_STRATEGY
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        safety = dict(self.safety_contract)
        policy = dict(self.redaction_policy)
        items = [
            _checklist_item(
                "signer_boundary_non_executable",
                safety.get("signer_boundary_available") is False and safety.get("signer_instantiated") is False,
                "signer boundary is unavailable and signer_instantiated remains false",
            ),
            _checklist_item(
                "credential_values_not_read",
                safety.get("credential_value_read") is False and policy.get("credential_value_read") is False,
                "credential values are not read, emitted, stored, hashed, transformed, or serialized",
            ),
            _checklist_item(
                "signed_material_generation_disabled",
                safety.get("signed_payload_generation_enabled") is False
                and safety.get("signed_order_generation_enabled") is False,
                "signed material generation remains disabled",
            ),
            _checklist_item(
                "order_submission_boundary_non_executable",
                safety.get("order_submission_enabled") is False
                and safety.get("order_submission_attempted") is False,
                "order submission remains unavailable and unattempted",
            ),
            _checklist_item(
                "order_cancel_boundary_non_executable",
                safety.get("order_cancel_enabled") is False
                and safety.get("order_cancellation_attempted") is False,
                "order cancellation remains unavailable and unattempted",
            ),
            _checklist_item(
                "authenticated_trading_disabled",
                safety.get("authenticated_trading_enabled") is False
                and safety.get("authenticated_request_performed") is False,
                "authenticated trading calls remain disabled and unperformed",
            ),
            _checklist_item(
                "wallet_connection_disabled",
                safety.get("wallet_connection_enabled") is False
                and safety.get("wallet_connection_attempted") is False,
                "wallet connection remains disabled and unattempted",
            ),
            _checklist_item(
                "live_enablement_blocked",
                safety.get("allowed_for_live") is False and safety.get("boundary_is_executable") is False,
                "allowed_for_live and boundary_is_executable remain false",
            ),
        ]
        value = {
            "contract_version": FUTURE_LIVE_ORDER_BOUNDARY_CHECKLIST_CONTRACT,
            "task_id": TASK_ID,
            "status": STATUS_BLOCKED,
            "mode": MODE,
            "execution_mode": EXECUTION_MODE,
            "market": _market(self.market_symbol),
            "market_symbol": _market(self.market_symbol),
            "strategy_name": _strategy(self.strategy_name),
            "checklist_exists": True,
            "checklist_items": items,
            "ready_item_count": 0,
            "blocked_item_count": len(items),
            "resolved_blocker_count": 0,
            "next_operator_action": "review scaffold only; create a separate future task for any executable live boundary",
            "generated_at": self.generated_at,
        }
        value.update(live_boundary_safety_flags())
        return value


def live_boundary_safety_flags() -> dict[str, Any]:
    return {
        "execution_mode": EXECUTION_MODE,
        "mode": MODE,
        "review_only": True,
        "preflight_only": True,
        "dry_run_only": True,
        "paper_only": True,
        "interface_only": True,
        "non_executable": True,
        "boundary_is_executable": False,
        "signer_boundary_available": False,
        "signer_available": False,
        "signer_instantiated": False,
        "signing_enabled": False,
        "signing_attempted": False,
        "wallet_signing_enabled": False,
        "cryptographic_signing_enabled": False,
        "cryptographic_signing_performed": False,
        "private_key_read": False,
        "seed_phrase_read": False,
        "mnemonic_read": False,
        "api_secret_read": False,
        "auth_token_read": False,
        "credential_value_read": False,
        "credential_values_read": False,
        "environment_values_read": False,
        "secret_files_read": False,
        "credential_value_serialized": False,
        "credential_values_serialized": False,
        "credential_values_printed": False,
        "credential_values_stored": False,
        "credential_values_hashed": False,
        "credential_values_transformed": False,
        "signed_payload_generation_enabled": False,
        "signed_order_generation_enabled": False,
        "signed_payload_generated": False,
        "signed_order_payload_generated": False,
        "order_payload_generation_enabled": False,
        "order_payload_generated": False,
        "order_submission_boundary_available": False,
        "order_submission_enabled": False,
        "order_submission_attempted": False,
        "order_submission_performed": False,
        "order_cancel_boundary_available": False,
        "order_cancel_enabled": False,
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
        "live_execution_approved": False,
        "live_execution_allowed": False,
        "live_execution_performed": False,
        "real_execution_available": False,
        "real_order_submitted": False,
        "order_submitted": False,
        "real_order_cancelled": False,
        "allowed_for_live": False,
        "candidate_is_executable": False,
        "scheduler_or_daemon_added": False,
        "background_worker_added": False,
        "autonomous_live_trading_added": False,
        "resolved_blocker_count": 0,
    }


def validate_live_order_boundary_contract(
    result: Mapping[str, Any],
    *,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    value = dict(result or {})
    errors: list[str] = []
    statuses: list[str] = []
    if value.get("contract_version") != LIVE_ORDER_BOUNDARY_CONTRACT_RESULT_CONTRACT:
        errors.append(f"contract_version must be {LIVE_ORDER_BOUNDARY_CONTRACT_RESULT_CONTRACT}")
        statuses.append("invalid_contract")
    for field in ("review_only", "preflight_only", "dry_run_only", "interface_only", "non_executable"):
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
        if key in FORBIDDEN_VALUE_FIELD_NAMES:
            errors.append(f"{path}.{key} is forbidden in live order boundary artifacts")
            statuses.append("forbidden_value_field_detected")
    valid = not errors
    return {
        "contract_version": LIVE_ORDER_BOUNDARY_VALIDATION_CONTRACT,
        "valid": valid,
        "status": "passed" if valid else STATUS_BLOCKED,
        "statuses": _dedupe(statuses)
        or (["live_order_boundary_contract_valid"] if valid else ["live_order_boundary_contract_blocked"]),
        "errors": errors,
        "generated_at": generated_at,
        **live_boundary_safety_flags(),
    }


def _checklist_item(check_id: str, ready: bool, detail: str) -> dict[str, Any]:
    return {
        "check_id": clean_text(check_id),
        "ready": False,
        "evidence_present": ready is True,
        "status": STATUS_BLOCKED,
        "detail": clean_text(detail),
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
