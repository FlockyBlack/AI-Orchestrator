from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

from pm_bot.trading_core.schemas import GENERATED_AT, clean_text

TASK_ID = "ORCH-PMBOT-TRADING-MVP-070B-FIRST-TINY-ORDER-MARKET-TOKEN-RESOLVER-NO-TRADING"

EXECUTION_MODE = "preflight"
MODE = "first order market token resolver / dry-run / no-trading"

DEFAULT_ALLOWED_MARKET = "BTC"
DEFAULT_ALLOWED_STRATEGY = "tiny-momentum"

STATUS_READY = "first_order_market_token_contract_ready_review_only"
STATUS_BLOCKED_MISSING_TOKEN_ID = "blocked_missing_token_id"
STATUS_BLOCKED_SCOPE_MISMATCH = "blocked_scope_mismatch"
STATUS_BLOCKED_INVALID_MARKET_SLUG = "blocked_invalid_market_slug"
STATUS_BLOCKED_INVALID_CONDITION_ID = "blocked_invalid_condition_id"
STATUS_BLOCKED_INVALID_TOKEN_ID = "blocked_invalid_token_id"

FIRST_ORDER_MARKET_TOKEN_CONTRACT = "pmbot_first_order_market_token_contract_070b.v1"
FIRST_ORDER_MARKET_TOKEN_RESULT_CONTRACT = "pmbot_first_order_market_token_resolver_070b_result.v1"
FIRST_ORDER_MARKET_TOKEN_LATEST_STATUS_CONTRACT = "pmbot_latest_first_order_market_token_status_070b.v1"
FIRST_ORDER_MARKET_TOKEN_VALIDATION_CONTRACT = "pmbot_first_order_market_token_validation_070b.v1"

REQUIRED_FALSE_FLAGS = (
    "allowed_for_live",
    "live_execution_approved",
    "live_execution_allowed",
    "live_execution_performed",
    "real_execution_available",
    "canary_executable_now",
    "operator_approved",
    "target_contract_executable",
    "token_id_generated",
    "fake_token_id_generated",
    "market_id_generated",
    "fake_market_id_generated",
    "order_generation_enabled",
    "order_generation_attempted",
    "order_payload_generated",
    "signed_payload_generated",
    "signed_order_payload_generated",
    "signed_order_generation_enabled",
    "signed_order_generation_attempted",
    "signing_enabled",
    "signing_attempted",
    "wallet_signing_enabled",
    "wallet_signing_attempted",
    "wallet_connection_enabled",
    "wallet_connection_attempted",
    "wallet_enabled",
    "wallet_used",
    "cryptographic_signing_enabled",
    "cryptographic_signing_performed",
    "order_submission_enabled",
    "order_submission_attempted",
    "order_submission_performed",
    "order_submitted",
    "real_order_submitted",
    "order_cancellation_enabled",
    "order_cancellation_attempted",
    "order_cancellation_performed",
    "real_order_cancelled",
    "authenticated_polymarket_enabled",
    "authenticated_endpoint_enabled",
    "authenticated_request_performed",
    "authenticated_trading_call_performed",
    "network_trading_call_performed",
    "private_key_read",
    "seed_phrase_read",
    "mnemonic_read",
    "api_secret_read",
    "auth_token_read",
    "credential_values_read",
    "credential_values_printed",
    "credential_values_stored",
    "secrets_read",
    "secrets_printed",
    "secrets_persisted",
    "raw_values_emitted",
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
class FirstOrderMarketTokenContract:
    status: str
    market_symbol: str
    strategy_name: str
    market_slug: str
    condition_id: str
    token_id: str
    outcome_name: str
    scope_valid: bool
    market_slug_format_status: str
    condition_id_format_status: str
    token_id_format_status: str
    token_id_source: str
    local_market_discovery_artifacts: tuple[Mapping[str, Any], ...]
    blockers: tuple[Mapping[str, Any], ...]
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        token_id_text = clean_text(self.token_id)
        value = asdict(self)
        value["contract_version"] = FIRST_ORDER_MARKET_TOKEN_CONTRACT
        value["task_id"] = TASK_ID
        value["status"] = clean_text(self.status) or STATUS_BLOCKED_MISSING_TOKEN_ID
        value["mode"] = MODE
        value["execution_mode"] = EXECUTION_MODE
        value["market"] = _market(self.market_symbol)
        value["market_symbol"] = _market(self.market_symbol)
        value["strategy_name"] = _strategy(self.strategy_name)
        value["target_scope"] = "polymarket_btc_tiny_momentum"
        value["target_contract_only"] = True
        value["target_contract_executable"] = False
        value["market_slug"] = clean_text(self.market_slug)
        value["condition_id"] = clean_text(self.condition_id)
        value["token_id"] = token_id_text
        value["outcome_token_id"] = token_id_text
        value["outcome_name"] = clean_text(self.outcome_name)
        value["token_id_present"] = bool(token_id_text)
        value["token_id_generated"] = False
        value["fake_token_id_generated"] = False
        value["market_id_generated"] = False
        value["fake_market_id_generated"] = False
        value["scope_valid"] = self.scope_valid is True
        value["market_slug_format_status"] = clean_text(self.market_slug_format_status)
        value["condition_id_format_status"] = clean_text(self.condition_id_format_status)
        value["token_id_format_status"] = clean_text(self.token_id_format_status)
        value["market_slug_format_valid"] = value["market_slug_format_status"] in {"valid", "missing_optional"}
        value["condition_id_format_valid"] = value["condition_id_format_status"] in {"valid", "missing_optional"}
        value["token_id_format_valid"] = value["token_id_format_status"] == "valid"
        value["token_id_source"] = clean_text(self.token_id_source)
        value["local_market_discovery_artifacts"] = [
            dict(row) for row in self.local_market_discovery_artifacts
        ]
        value["blockers"] = [dict(row) for row in self.blockers]
        value["blocker_count"] = len(value["blockers"])
        value["resolved_blocker_count"] = 0
        value["operator_summary"] = _contract_operator_summary(value)
        value.update(first_order_market_token_safety_flags())
        return value


@dataclass(frozen=True)
class FirstOrderMarketTokenLatestStatus:
    status: str
    market_symbol: str
    strategy_name: str
    market_slug: str
    condition_id: str
    token_id: str
    token_id_format_status: str
    token_id_source: str
    blocker_count: int
    artifact_path: str
    latest_status_path: str
    target_contract_path: str
    validation_path: str
    operator_markdown_path: str
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        token_id_text = clean_text(self.token_id)
        value = asdict(self)
        value["contract_version"] = FIRST_ORDER_MARKET_TOKEN_LATEST_STATUS_CONTRACT
        value["task_id"] = TASK_ID
        value["status"] = clean_text(self.status) or STATUS_BLOCKED_MISSING_TOKEN_ID
        value["mode"] = MODE
        value["execution_mode"] = EXECUTION_MODE
        value["market"] = _market(self.market_symbol)
        value["market_symbol"] = _market(self.market_symbol)
        value["strategy_name"] = _strategy(self.strategy_name)
        value["market_slug"] = clean_text(self.market_slug)
        value["condition_id"] = clean_text(self.condition_id)
        value["token_id"] = token_id_text
        value["outcome_token_id"] = token_id_text
        value["token_id_present"] = bool(token_id_text)
        value["token_id_source"] = clean_text(self.token_id_source)
        value["token_id_format_status"] = clean_text(self.token_id_format_status)
        value["token_id_format_valid"] = value["token_id_format_status"] == "valid"
        value["target_contract_only"] = True
        value["target_contract_executable"] = False
        value["blocker_count"] = int(self.blocker_count or 0)
        value["resolved_blocker_count"] = 0
        value["live_execution"] = "blocked"
        value["order_generation"] = "blocked"
        value["signing"] = "blocked"
        value["order_submission"] = "blocked"
        value["authenticated_trading"] = "blocked"
        value["next_operator_action"] = _next_operator_action(value)
        value["operator_summary"] = _latest_operator_summary(value)
        value.update(first_order_market_token_safety_flags())
        return value


def first_order_market_token_safety_flags() -> dict[str, Any]:
    return {
        "execution_mode": EXECUTION_MODE,
        "mode": MODE,
        "review_only": True,
        "preflight_only": True,
        "dry_run_only": True,
        "paper_only": True,
        "resolver_only": True,
        "target_contract_only": True,
        "non_executable": True,
        "allowed_for_live": False,
        "live_execution_approved": False,
        "live_execution_allowed": False,
        "live_execution_performed": False,
        "real_execution_available": False,
        "canary_executable_now": False,
        "operator_approved": False,
        "target_contract_executable": False,
        "token_id_generated": False,
        "fake_token_id_generated": False,
        "market_id_generated": False,
        "fake_market_id_generated": False,
        "order_generation_enabled": False,
        "order_generation_attempted": False,
        "order_payload_generated": False,
        "signed_payload_generated": False,
        "signed_order_payload_generated": False,
        "signed_order_generation_enabled": False,
        "signed_order_generation_attempted": False,
        "signing_enabled": False,
        "signing_attempted": False,
        "wallet_signing_enabled": False,
        "wallet_signing_attempted": False,
        "wallet_connection_enabled": False,
        "wallet_connection_attempted": False,
        "wallet_enabled": False,
        "wallet_used": False,
        "cryptographic_signing_enabled": False,
        "cryptographic_signing_performed": False,
        "order_submission_enabled": False,
        "order_submission_attempted": False,
        "order_submission_performed": False,
        "order_submitted": False,
        "real_order_submitted": False,
        "order_cancellation_enabled": False,
        "order_cancellation_attempted": False,
        "order_cancellation_performed": False,
        "real_order_cancelled": False,
        "authenticated_polymarket_enabled": False,
        "authenticated_endpoint_enabled": False,
        "authenticated_request_performed": False,
        "authenticated_trading_call_performed": False,
        "network_trading_call_performed": False,
        "network_trading_calls_performed": 0,
        "polymarket_api_calls_performed": 0,
        "private_key_read": False,
        "seed_phrase_read": False,
        "mnemonic_read": False,
        "api_secret_read": False,
        "auth_token_read": False,
        "credential_values_read": False,
        "credential_values_printed": False,
        "credential_values_stored": False,
        "secrets_read": False,
        "secrets_printed": False,
        "secrets_persisted": False,
        "raw_values_emitted": False,
        "browser_automation_added": False,
        "scheduler_or_daemon_added": False,
        "background_worker_added": False,
        "autonomous_live_trading_added": False,
        "resolved_blocker_count": 0,
    }


def validate_first_order_market_token_result(
    result: Mapping[str, Any],
    *,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    value = dict(result or {})
    target_contract = dict(value.get("target_contract", {}))
    errors: list[str] = []
    statuses: list[str] = []
    if value.get("contract_version") != FIRST_ORDER_MARKET_TOKEN_RESULT_CONTRACT:
        errors.append(f"contract_version must be {FIRST_ORDER_MARKET_TOKEN_RESULT_CONTRACT}")
        statuses.append("invalid_contract")
    if target_contract.get("contract_version") != FIRST_ORDER_MARKET_TOKEN_CONTRACT:
        errors.append(f"target_contract.contract_version must be {FIRST_ORDER_MARKET_TOKEN_CONTRACT}")
        statuses.append("invalid_target_contract")
    if value.get("target_contract_only") is not True:
        errors.append("target_contract_only must be true")
        statuses.append("target_contract_only_missing")
    if value.get("resolved_blocker_count") != 0:
        errors.append("resolved_blocker_count must be 0")
        statuses.append("resolved_blocker_detected")
    if value.get("status") == STATUS_READY and not clean_text(target_contract.get("token_id")):
        errors.append("ready status requires explicit token_id")
        statuses.append("ready_missing_token_id")
    if value.get("status") == STATUS_READY and target_contract.get("token_id_format_valid") is not True:
        errors.append("ready status requires valid token_id format")
        statuses.append("ready_invalid_token_id")
    if target_contract.get("token_id_generated") is not False:
        errors.append("token_id_generated must be false")
        statuses.append("token_id_generation_detected")
    if target_contract.get("fake_token_id_generated") is not False:
        errors.append("fake_token_id_generated must be false")
        statuses.append("fake_token_id_generation_detected")
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
            errors.append(f"{path}.{key} is forbidden in first order market token artifacts")
            statuses.append("forbidden_value_field_detected")
    valid = not errors
    return {
        "contract_version": FIRST_ORDER_MARKET_TOKEN_VALIDATION_CONTRACT,
        "task_id": TASK_ID,
        "valid": valid,
        "status": "passed" if valid else "blocked_validation_failed",
        "statuses": _dedupe(statuses)
        or (
            ["first_order_market_token_contract_valid"]
            if valid
            else ["first_order_market_token_contract_blocked"]
        ),
        "errors": errors,
        "generated_at": generated_at,
        **first_order_market_token_safety_flags(),
    }


def _market(value: Any) -> str:
    return clean_text(value).upper() or DEFAULT_ALLOWED_MARKET


def _strategy(value: Any) -> str:
    return clean_text(value) or DEFAULT_ALLOWED_STRATEGY


def _contract_operator_summary(value: Mapping[str, Any]) -> str:
    status = clean_text(value.get("status"))
    if status == STATUS_BLOCKED_MISSING_TOKEN_ID:
        return "No token_id was provided; the resolver did not invent one and live execution remains blocked."
    if status == STATUS_READY:
        return "Explicit token_id format is valid; the output is a target contract only and is not executable."
    if status == STATUS_BLOCKED_SCOPE_MISMATCH:
        return "Requested market or strategy is outside BTC/tiny-momentum scope; output is blocked."
    return "Input format validation blocked the target contract; no live action is available."


def _latest_operator_summary(value: Mapping[str, Any]) -> str:
    return (
        "First order market/token resolver completed with status="
        + clean_text(value.get("status"))
        + "; token_id_present="
        + str(value.get("token_id_present") is True).lower()
        + "; token_id_generated=false; allowed_for_live=false; order generation, signing, submission, "
        "cancellation, wallet use, and authenticated trading are blocked."
    )


def _next_operator_action(value: Mapping[str, Any]) -> str:
    if clean_text(value.get("status")) == STATUS_BLOCKED_MISSING_TOKEN_ID:
        return "provide an explicit validated Polymarket outcome token_id in a separate supervised dry-run"
    if clean_text(value.get("status")) == STATUS_READY:
        return "review target contract only; do not trade, sign, submit, cancel, or authenticate"
    return "correct blocked input fields before reviewing the target contract"


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
