from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

from pm_bot.trading_core.schemas import GENERATED_AT, clean_text

TASK_ID = "ORCH-PMBOT-TRADING-MVP-065D-FIRST-LIVE-ORDER-OPERATOR-APPROVAL-CONTRACT-NO-EXECUTION"
EXECUTION_MODE = "approval_contract_definition"
MODE = "first live order operator approval contract / definition-only / no execution"

DEFAULT_ALLOWED_MARKET = "BTC"
DEFAULT_ALLOWED_STRATEGY = "tiny-momentum"
MAX_NOTIONAL_USD = 1.0
MAX_ORDERS_PER_DAY = 1
APPROVAL_TIMEOUT_MINUTES = 15
APPROVAL_TIMEOUT_SECONDS = APPROVAL_TIMEOUT_MINUTES * 60

EXACT_REQUIRED_APPROVAL_TEXT = (
    "STOP - REAL MONEY RISK. I, the operator, explicitly approve ONE FUTURE SUPERVISED TINY "
    "LIVE ORDER for BTC using strategy tiny-momentum only, capped at 1.00 USD notional, "
    "expiring 15 minutes after my approval, one-shot only with no repeats, no scheduler, "
    "no daemon, no background loop, and revocable by me before use. I understand no approval "
    "means no execution, and this 065D approval contract itself cannot execute, connect a "
    "wallet, instantiate a signer, sign payloads, generate signed orders, submit orders, "
    "cancel orders, make authenticated trading calls, read credentials, or create fills/PnL."
)

FIRST_LIVE_ORDER_APPROVAL_TEXT_CONTRACT = "pmbot_first_live_order_required_approval_text_065d.v1"
FIRST_LIVE_ORDER_APPROVAL_SCOPE_CONTRACT = "pmbot_first_live_order_approval_scope_065d.v1"
FIRST_LIVE_ORDER_APPROVAL_LIMITS_CONTRACT = "pmbot_first_live_order_approval_limits_065d.v1"
FIRST_LIVE_ORDER_APPROVAL_REVOCATION_POLICY_CONTRACT = (
    "pmbot_first_live_order_approval_revocation_policy_065d.v1"
)
FIRST_LIVE_ORDER_APPROVAL_TIMEOUT_POLICY_CONTRACT = (
    "pmbot_first_live_order_approval_timeout_policy_065d.v1"
)
FIRST_LIVE_ORDER_APPROVAL_AUDIT_TEMPLATE_CONTRACT = (
    "pmbot_first_live_order_approval_audit_record_template_065d.v1"
)
LATEST_FIRST_LIVE_ORDER_APPROVAL_STATUS_CONTRACT = (
    "pmbot_latest_first_live_order_approval_contract_status_065d.v1"
)
FIRST_LIVE_ORDER_APPROVAL_RESULT_CONTRACT = "pmbot_first_live_order_approval_contract_065d.v1"
FIRST_LIVE_ORDER_APPROVAL_VALIDATION_CONTRACT = (
    "pmbot_first_live_order_approval_contract_validation_065d.v1"
)

STATUS_DEFINED_EXECUTION_BLOCKED = "approval_contract_defined_execution_blocked"
STATUS_SCOPE_BLOCKED = "approval_contract_scope_blocked_execution_blocked"

FORCED_FALSE_APPROVAL_CONTRACT_FIELDS = (
    "approval_contract_executable",
    "allowed_for_live",
    "live_execution_approved",
    "operator_approval_recorded",
    "approval_consumed",
    "contract_can_execute",
    "credential_values_read",
    "credential_values_serialized",
    "authenticated_trading_calls_made",
    "real_execution_performed",
    "fill_or_pnl_recorded",
    "autonomous_repeat_allowed",
    "scheduler_or_daemon_allowed",
    "background_loop_allowed",
)

FORBIDDEN_EXECUTION_PAYLOAD_FIELDS = frozenset(
    {
        "private_key",
        "seed_phrase",
        "mnemonic",
        "api_secret",
        "api_secret_value",
        "auth_token",
        "passphrase",
        "secret",
        "raw_value",
        "signature",
        "signed_payload",
        "signed_order",
        "order_payload",
        "submission_payload",
        "cancel_payload",
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
        "profit",
        "realized_pnl",
        "unrealized_pnl",
    }
)

FORBIDDEN_FAKE_EXECUTION_VALUE_TOKENS = (
    "fake-execution-id",
    "fake-order-id",
    "fake-client-order-id",
    "fake-tx-hash",
    "fake-fill",
    "fake-pnl",
    "fake-balance",
    "fake-position",
)


@dataclass(frozen=True)
class FirstLiveOrderRequiredApprovalText:
    market_symbol: str
    strategy_name: str
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        value = {
            "contract_version": FIRST_LIVE_ORDER_APPROVAL_TEXT_CONTRACT,
            "task_id": TASK_ID,
            "market": _market(self.market_symbol),
            "market_symbol": _market(self.market_symbol),
            "strategy_name": _strategy(self.strategy_name),
            "required_approval_text": EXACT_REQUIRED_APPROVAL_TEXT,
            "approval_text_exact_match_required": True,
            "approval_text_case_sensitive": True,
            "approval_text_non_empty": True,
            "approval_text_may_be_shortened": False,
            "no_approval_means_no_execution": True,
            "generated_at": self.generated_at,
        }
        value.update(first_live_order_approval_safety_flags())
        return value


@dataclass(frozen=True)
class FirstLiveOrderApprovalScope:
    market_symbol: str
    strategy_name: str
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        market_symbol = _market(self.market_symbol)
        strategy_name = _strategy(self.strategy_name)
        market_allowed = market_symbol == DEFAULT_ALLOWED_MARKET
        strategy_allowed = strategy_name == DEFAULT_ALLOWED_STRATEGY
        value = {
            "contract_version": FIRST_LIVE_ORDER_APPROVAL_SCOPE_CONTRACT,
            "task_id": TASK_ID,
            "requested_market": market_symbol,
            "requested_strategy": strategy_name,
            "default_market": DEFAULT_ALLOWED_MARKET,
            "default_strategy": DEFAULT_ALLOWED_STRATEGY,
            "allowed_markets": [DEFAULT_ALLOWED_MARKET],
            "allowed_strategies": [DEFAULT_ALLOWED_STRATEGY],
            "btc_only": True,
            "tiny_momentum_only": True,
            "market_allowed_by_scope": market_allowed,
            "strategy_allowed_by_scope": strategy_allowed,
            "scope_valid": market_allowed and strategy_allowed,
            "scope_violation_blocks_future_use": not (market_allowed and strategy_allowed),
            "no_market_expansion_in_this_contract": True,
            "generated_at": self.generated_at,
        }
        value.update(first_live_order_approval_safety_flags())
        return value


@dataclass(frozen=True)
class FirstLiveOrderApprovalLimits:
    max_notional_usd: float = MAX_NOTIONAL_USD
    max_orders_per_day: int = MAX_ORDERS_PER_DAY
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        max_notional = float(self.max_notional_usd)
        max_orders = int(self.max_orders_per_day)
        value = {
            "contract_version": FIRST_LIVE_ORDER_APPROVAL_LIMITS_CONTRACT,
            "task_id": TASK_ID,
            "max_notional_usd": max_notional,
            "max_notional_limit_passes_contract": 0 < max_notional <= MAX_NOTIONAL_USD,
            "max_orders_per_day": max_orders,
            "daily_order_cap_passes_contract": max_orders == MAX_ORDERS_PER_DAY,
            "one_shot_only": True,
            "approval_reuse_allowed": False,
            "autonomous_repeat_allowed": False,
            "no_autonomous_repeat": True,
            "no_scheduler": True,
            "no_daemon": True,
            "no_background_loop": True,
            "generated_at": self.generated_at,
        }
        value.update(first_live_order_approval_safety_flags())
        return value


@dataclass(frozen=True)
class FirstLiveOrderApprovalRevocationPolicy:
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        value = {
            "contract_version": FIRST_LIVE_ORDER_APPROVAL_REVOCATION_POLICY_CONTRACT,
            "task_id": TASK_ID,
            "revocable_by_operator": True,
            "revocation_window": "any time before a separate future approval is consumed or expires",
            "revocation_effect": "revoked approval blocks any later use of this approval text",
            "revocation_requires_separate_operator_record": True,
            "revoked_approval_blocks_future_use": True,
            "no_approval_means_no_execution": True,
            "approval_after_revocation_requires_new_separate_task": True,
            "generated_at": self.generated_at,
        }
        value.update(first_live_order_approval_safety_flags())
        return value


@dataclass(frozen=True)
class FirstLiveOrderApprovalTimeoutPolicy:
    timeout_minutes: int = APPROVAL_TIMEOUT_MINUTES
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        minutes = int(self.timeout_minutes)
        seconds = minutes * 60
        value = {
            "contract_version": FIRST_LIVE_ORDER_APPROVAL_TIMEOUT_POLICY_CONTRACT,
            "task_id": TASK_ID,
            "approval_expires": True,
            "approval_timeout_minutes": minutes,
            "approval_timeout_seconds": seconds,
            "timeout_within_required_maximum": 0 < minutes <= APPROVAL_TIMEOUT_MINUTES,
            "approval_clock_starts": "when an operator records the exact approval text in a separate future task",
            "expired_approval_blocks_future_use": True,
            "no_open_ended_approval": True,
            "generated_at": self.generated_at,
        }
        value.update(first_live_order_approval_safety_flags())
        return value


@dataclass(frozen=True)
class FirstLiveOrderApprovalAuditRecordTemplate:
    market_symbol: str
    strategy_name: str
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        value = {
            "contract_version": FIRST_LIVE_ORDER_APPROVAL_AUDIT_TEMPLATE_CONTRACT,
            "task_id": TASK_ID,
            "market": _market(self.market_symbol),
            "market_symbol": _market(self.market_symbol),
            "strategy_name": _strategy(self.strategy_name),
            "template_only": True,
            "required_operator_artifacts": [
                "exact approval text copy",
                "operator approval timestamp",
                "revocation status checked before any separate future use",
                "BTC/tiny-momentum scope check",
                "1.00 USD maximum notional check",
                "one-shot consumption note if a separate future task ever uses the approval",
                "timeout check no later than 15 minutes after approval",
            ],
            "forbidden_audit_artifacts_in_065d": [
                "credential values",
                "signed payloads",
                "signed orders",
                "submitted order references",
                "cancellation references",
                "fills",
                "PnL",
            ],
            "future_action_reference": "empty in 065D; a separate operator-approved future task is required",
            "operator_must_confirm_no_revocation": True,
            "operator_must_confirm_not_expired": True,
            "operator_must_confirm_one_shot_unused": True,
            "generated_at": self.generated_at,
        }
        value.update(first_live_order_approval_safety_flags())
        return value


@dataclass(frozen=True)
class LatestFirstLiveOrderApprovalContractStatus:
    status: str
    market_symbol: str
    strategy_name: str
    approval_text_path: str
    scope_path: str
    limits_path: str
    revocation_policy_path: str
    timeout_policy_path: str
    audit_template_path: str
    result_path: str
    operator_summary_path: str
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        value = {
            "contract_version": LATEST_FIRST_LIVE_ORDER_APPROVAL_STATUS_CONTRACT,
            "task_id": TASK_ID,
            "status": clean_text(self.status) or STATUS_DEFINED_EXECUTION_BLOCKED,
            "market": _market(self.market_symbol),
            "market_symbol": _market(self.market_symbol),
            "strategy_name": _strategy(self.strategy_name),
            "required_approval_text": EXACT_REQUIRED_APPROVAL_TEXT,
            "approval_text_exact_match_required": True,
            "approval_expires": True,
            "approval_timeout_minutes": APPROVAL_TIMEOUT_MINUTES,
            "one_shot_only": True,
            "max_notional_usd": MAX_NOTIONAL_USD,
            "max_orders_per_day": MAX_ORDERS_PER_DAY,
            "approval_contract_executable": False,
            "allowed_for_live": False,
            "no_approval_means_no_execution": True,
            "approval_text_path": clean_text(self.approval_text_path),
            "scope_path": clean_text(self.scope_path),
            "limits_path": clean_text(self.limits_path),
            "revocation_policy_path": clean_text(self.revocation_policy_path),
            "timeout_policy_path": clean_text(self.timeout_policy_path),
            "audit_template_path": clean_text(self.audit_template_path),
            "artifact_path": clean_text(self.result_path),
            "operator_summary_path": clean_text(self.operator_summary_path),
            "generated_at": self.generated_at,
        }
        value.update(first_live_order_approval_safety_flags())
        return value


@dataclass(frozen=True)
class FirstLiveOrderApprovalContractResult:
    status: str
    market_symbol: str
    strategy_name: str
    required_approval_text: Mapping[str, Any]
    approval_scope: Mapping[str, Any]
    approval_limits: Mapping[str, Any]
    revocation_policy: Mapping[str, Any]
    timeout_policy: Mapping[str, Any]
    audit_record_template: Mapping[str, Any]
    latest_status: Mapping[str, Any]
    artifact_paths: Mapping[str, str]
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        value = {
            "contract_version": FIRST_LIVE_ORDER_APPROVAL_RESULT_CONTRACT,
            "task_id": TASK_ID,
            "status": clean_text(self.status) or STATUS_DEFINED_EXECUTION_BLOCKED,
            "mode": MODE,
            "execution_mode": EXECUTION_MODE,
            "market": _market(self.market_symbol),
            "market_symbol": _market(self.market_symbol),
            "strategy_name": _strategy(self.strategy_name),
            "required_approval_text": dict(self.required_approval_text),
            "approval_scope": dict(self.approval_scope),
            "approval_limits": dict(self.approval_limits),
            "revocation_policy": dict(self.revocation_policy),
            "timeout_policy": dict(self.timeout_policy),
            "audit_record_template": dict(self.audit_record_template),
            "latest_status": dict(self.latest_status),
            "artifact_paths": dict(self.artifact_paths),
            "approval_text_exact_match_required": True,
            "approval_expires": True,
            "one_shot_only": True,
            "max_notional_usd": MAX_NOTIONAL_USD,
            "max_orders_per_day": MAX_ORDERS_PER_DAY,
            "approval_contract_executable": False,
            "allowed_for_live": False,
            "no_approval_means_no_execution": True,
            "operator_summary": (
                "065D defines only the future operator approval contract. It records no approval and cannot perform "
                "any live action."
            ),
            "generated_at": self.generated_at,
        }
        value.update(first_live_order_approval_safety_flags())
        value["validation"] = validate_first_live_order_approval_contract(value, generated_at=self.generated_at)
        return value


def first_live_order_approval_safety_flags() -> dict[str, Any]:
    return {
        "execution_mode": EXECUTION_MODE,
        "mode": MODE,
        "definition_only": True,
        "review_only": True,
        "dry_run_only": True,
        "paper_only": True,
        "non_executable": True,
        "approval_contract_executable": False,
        "allowed_for_live": False,
        "live_execution_approved": False,
        "operator_approval_recorded": False,
        "approval_consumed": False,
        "contract_can_execute": False,
        "credential_values_read": False,
        "credential_values_serialized": False,
        "authenticated_trading_calls_made": False,
        "real_execution_performed": False,
        "fill_or_pnl_recorded": False,
        "autonomous_repeat_allowed": False,
        "scheduler_or_daemon_allowed": False,
        "background_loop_allowed": False,
        "approval_required_before_future_execution": True,
        "separate_future_execution_task_required": True,
        "no_autonomous_repeat": True,
        "no_scheduler": True,
        "no_daemon": True,
        "no_background_loop": True,
        "no_approval_means_no_execution": True,
    }


def validate_first_live_order_approval_contract(
    result: Mapping[str, Any],
    *,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    value = dict(result or {})
    errors: list[str] = []
    statuses: list[str] = []

    if value.get("contract_version") != FIRST_LIVE_ORDER_APPROVAL_RESULT_CONTRACT:
        errors.append(f"contract_version must be {FIRST_LIVE_ORDER_APPROVAL_RESULT_CONTRACT}")
        statuses.append("invalid_contract")
    if value.get("execution_mode") != EXECUTION_MODE:
        errors.append(f"execution_mode must be {EXECUTION_MODE}")
        statuses.append("invalid_execution_mode")
    approval_text = dict(value.get("required_approval_text", {}))
    text = clean_text(approval_text.get("required_approval_text"))
    if not text:
        errors.append("required approval text must be non-empty")
        statuses.append("approval_text_empty")
    if text != EXACT_REQUIRED_APPROVAL_TEXT:
        errors.append("required approval text must match the exact 065D text")
        statuses.append("approval_text_not_exact")
    scope = dict(value.get("approval_scope", {}))
    if scope.get("allowed_markets") != [DEFAULT_ALLOWED_MARKET]:
        errors.append("allowed_markets must be BTC only")
        statuses.append("scope_market_not_btc_only")
    if scope.get("allowed_strategies") != [DEFAULT_ALLOWED_STRATEGY]:
        errors.append("allowed_strategies must be tiny-momentum only")
        statuses.append("scope_strategy_not_tiny_momentum_only")
    if scope.get("scope_valid") is not True:
        errors.append("default approval scope must be valid for BTC/tiny-momentum")
        statuses.append("default_scope_invalid")
    limits = dict(value.get("approval_limits", {}))
    if float(limits.get("max_notional_usd", 0) or 0) > MAX_NOTIONAL_USD:
        errors.append("max_notional_usd must be <= 1.00")
        statuses.append("max_notional_too_high")
    if int(limits.get("max_orders_per_day", 0) or 0) != MAX_ORDERS_PER_DAY:
        errors.append("max_orders_per_day must equal 1")
        statuses.append("daily_order_cap_invalid")
    if limits.get("one_shot_only") is not True:
        errors.append("one_shot_only must be true")
        statuses.append("one_shot_missing")
    timeout = dict(value.get("timeout_policy", {}))
    if timeout.get("approval_expires") is not True:
        errors.append("approval_expires must be true")
        statuses.append("approval_does_not_expire")
    timeout_minutes = int(timeout.get("approval_timeout_minutes", 0) or 0)
    if timeout_minutes <= 0 or timeout_minutes > APPROVAL_TIMEOUT_MINUTES:
        errors.append("approval_timeout_minutes must be > 0 and <= 15")
        statuses.append("approval_timeout_invalid")
    for field in FORCED_FALSE_APPROVAL_CONTRACT_FIELDS:
        if value.get(field) is not False:
            errors.append(f"{field} must be false")
            statuses.append("unsafe_contract_flag_detected")
    for path, key, nested in _walk_fields(value):
        if key in FORCED_FALSE_APPROVAL_CONTRACT_FIELDS and nested is not False:
            errors.append(f"{path}.{key} must be false")
            statuses.append("nested_unsafe_contract_flag_detected")
        if key in FORBIDDEN_EXECUTION_PAYLOAD_FIELDS:
            errors.append(f"{path}.{key} is forbidden in 065D approval contract artifacts")
            statuses.append("forbidden_execution_payload_field_detected")
        if isinstance(nested, str):
            lowered = nested.lower()
            for token in FORBIDDEN_FAKE_EXECUTION_VALUE_TOKENS:
                if token in lowered:
                    errors.append(f"{path}.{key} contains forbidden fake execution marker")
                    statuses.append("fake_execution_marker_detected")
    valid = not errors
    return {
        "contract_version": FIRST_LIVE_ORDER_APPROVAL_VALIDATION_CONTRACT,
        "validation_id": "first-live-order-approval-contract-065d-passed"
        if valid
        else "first-live-order-approval-contract-065d-blocked",
        "valid": valid,
        "status": "passed" if valid else "blocked",
        "statuses": _dedupe(statuses)
        or (["first_live_order_approval_contract_valid"] if valid else ["first_live_order_approval_contract_blocked"]),
        "errors": errors,
        "generated_at": generated_at,
        **first_live_order_approval_safety_flags(),
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
