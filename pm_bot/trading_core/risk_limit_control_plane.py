from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

from pm_bot.trading_core.schemas import GENERATED_AT, clean_text, mapping_rows, trading_core_safety_summary

RISK_LIMIT_POLICY_CONTRACT = "pmbot_risk_limit_policy.v1"
RISK_LIMIT_STATE_CONTRACT = "pmbot_risk_limit_state.v1"
RISK_LIMIT_ORDER_INTENT_CONTRACT = "pmbot_risk_limit_order_intent.v1"
RISK_LIMIT_EXPOSURE_SNAPSHOT_CONTRACT = "pmbot_risk_limit_exposure_snapshot.v1"
RISK_LIMIT_DAILY_LOSS_SNAPSHOT_CONTRACT = "pmbot_risk_limit_daily_loss_snapshot.v1"
RISK_LIMIT_EVALUATION_CONTEXT_CONTRACT = "pmbot_risk_limit_evaluation_context.v1"
RISK_LIMIT_VIOLATION_CONTRACT = "pmbot_risk_limit_violation.v1"
RISK_LIMIT_HALT_REASON_CONTRACT = "pmbot_risk_limit_halt_reason.v1"
RISK_LIMIT_DECISION_CONTRACT = "pmbot_risk_limit_decision.v1"
RISK_LIMIT_DECISION_SUMMARY_CONTRACT = "pmbot_risk_limit_decision_summary.v1"
RISK_CONTROL_PLANE_SUMMARY_CONTRACT = "pmbot_risk_control_plane_summary.v1"

DECISION_ALLOW_DRY_RUN = "ALLOW_DRY_RUN"
DECISION_BLOCK = "BLOCK"
DECISION_HALT = "HALT"
DECISION_REVIEW_ONLY = "REVIEW_ONLY"

POLICY_MODES = {
    "paper_only",
    "dry_run",
    "future_tiny_live_canary",
    "supervised_live_disabled",
}

DEFAULT_ALLOWED_MARKET_IDS = ("btc-one-market-demo-market",)
DEFAULT_ALLOWED_MARKET_SLUGS = ("btc-one-market-demo",)
DEFAULT_ALLOWED_MARKET_TAGS = ("BTC", "BITCOIN")

FORCED_FALSE_EXECUTION_FIELDS = (
    "allowed_for_live",
    "live_execution_approved",
    "canary_executable_now",
    "real_execution_available",
    "live_connector_enabled",
)


@dataclass(frozen=True)
class RiskLimitPolicy:
    policy_id: str
    mode: str
    max_daily_loss_usd: float
    max_total_exposure_usd: float
    max_market_exposure_usd: float
    max_order_notional_usd: float
    max_orders_per_day: int
    max_trades_per_day: int
    max_active_markets: int
    cooldown_after_loss_minutes: int
    halt_on_stale_market_data: bool
    max_market_data_age_seconds: int
    halt_on_audit_mismatch: bool
    halt_on_kill_switch: bool
    halt_on_missing_operator_intent: bool
    halt_on_missing_readiness_evidence: bool
    halt_on_unresolved_critical_blockers: bool
    halt_on_disabled_live_connector: bool
    halt_on_live_execution_not_approved: bool
    halt_on_canary_not_executable: bool
    halt_on_real_execution_unavailable: bool
    allowed_market_ids: tuple[str, ...]
    allowed_market_slugs: tuple[str, ...]
    allowed_market_tags: tuple[str, ...]
    review_only_until_live_gate: bool
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = RISK_LIMIT_POLICY_CONTRACT
        value["allowed_market_ids"] = list(self.allowed_market_ids)
        value["allowed_market_slugs"] = list(self.allowed_market_slugs)
        value["allowed_market_tags"] = list(self.allowed_market_tags)
        value["risk_control_plane_ready"] = True
        value["risk_limits_enforced_for_order_intents"] = True
        value["future_btc_live_demo_supported_by_limits"] = policy_supports_btc_demo(value)
        value.update(_risk_control_safety_flags())
        return value


@dataclass(frozen=True)
class RiskLimitExposureSnapshot:
    total_exposure_usd: float = 0.0
    market_exposure_usd: float = 0.0
    active_market_ids: tuple[str, ...] = ()
    snapshot_reference: str = ""
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = RISK_LIMIT_EXPOSURE_SNAPSHOT_CONTRACT
        value["active_market_ids"] = list(self.active_market_ids)
        value.update(_risk_control_safety_flags())
        return value


@dataclass(frozen=True)
class RiskLimitDailyLossSnapshot:
    realized_loss_usd: float = 0.0
    loss_event_count: int = 0
    minutes_since_last_loss: int | None = None
    last_loss_reference: str = ""
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = RISK_LIMIT_DAILY_LOSS_SNAPSHOT_CONTRACT
        value.update(_risk_control_safety_flags())
        return value


@dataclass(frozen=True)
class RiskLimitState:
    state_id: str
    exposure_snapshot: Mapping[str, Any]
    daily_loss_snapshot: Mapping[str, Any]
    orders_submitted_today: int = 0
    trades_executed_today: int = 0
    market_data_age_seconds: int = 0
    audit_mismatch_detected: bool = False
    kill_switch_active: bool = False
    operator_intent_present: bool = True
    readiness_evidence_present: bool = True
    unresolved_critical_blockers: tuple[str, ...] = ()
    live_connector_enabled: bool = False
    live_execution_approved: bool = False
    canary_executable_now: bool = False
    real_execution_available: bool = False
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = RISK_LIMIT_STATE_CONTRACT
        value["exposure_snapshot"] = dict(self.exposure_snapshot)
        value["daily_loss_snapshot"] = dict(self.daily_loss_snapshot)
        value["unresolved_critical_blockers"] = list(self.unresolved_critical_blockers)
        value.update(_risk_control_safety_flags())
        return value


@dataclass(frozen=True)
class RiskLimitOrderIntent:
    intent_id: str
    market_id: str
    market_slug: str
    market_tag: str
    market_category: str
    side_label: str
    notional_usd: float
    quantity: float
    limit_price: float
    intent_source: str
    created_at: str
    dry_run_only: bool
    operator_intent_reference: str
    readiness_evidence_reference: str
    audit_replay_reference: str
    ui_panel_reference: str = ""

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = RISK_LIMIT_ORDER_INTENT_CONTRACT
        value["order_intent_only"] = True
        value["executable_submission_payload_present"] = False
        value.update(_risk_control_safety_flags())
        return value


@dataclass(frozen=True)
class RiskLimitViolation:
    violation_id: str
    code: str
    field: str
    limit: Any
    actual: Any
    message: str
    severity: str = "block"

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = RISK_LIMIT_VIOLATION_CONTRACT
        return value


@dataclass(frozen=True)
class RiskLimitHaltReason:
    halt_id: str
    code: str
    field: str
    limit: Any
    actual: Any
    message: str
    severity: str = "critical"

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = RISK_LIMIT_HALT_REASON_CONTRACT
        return value


@dataclass(frozen=True)
class RiskLimitEvaluationContext:
    policy: Mapping[str, Any]
    state: Mapping[str, Any]
    order_intent: Mapping[str, Any]
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = RISK_LIMIT_EVALUATION_CONTEXT_CONTRACT
        value["policy"] = dict(self.policy)
        value["state"] = dict(self.state)
        value["order_intent"] = dict(self.order_intent)
        value.update(_risk_control_safety_flags())
        return value


@dataclass(frozen=True)
class RiskLimitDecision:
    decision_id: str
    policy_id: str
    intent_id: str
    decision_status: str
    allowed_for_dry_run: bool
    allowed_for_live: bool
    live_execution_approved: bool
    canary_executable_now: bool
    real_execution_available: bool
    live_connector_enabled: bool
    violations: tuple[Mapping[str, Any], ...]
    halt_reasons: tuple[Mapping[str, Any], ...]
    live_block_reasons: tuple[str, ...]
    remaining_capacity: Mapping[str, Any]
    human_summary: str
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = RISK_LIMIT_DECISION_CONTRACT
        value["violations"] = [dict(row) for row in self.violations]
        value["halt_reasons"] = [dict(row) for row in self.halt_reasons]
        value["live_block_reasons"] = list(self.live_block_reasons)
        value["remaining_capacity"] = dict(self.remaining_capacity)
        value["risk_control_plane_ready"] = True
        value["risk_limits_enforced_for_order_intents"] = True
        value.update(_risk_control_safety_flags())
        return value


def build_default_risk_limit_policy(
    *,
    policy_id: str = "risk-limit-policy-037-default",
    mode: str = "future_tiny_live_canary",
    allowed_market_ids: Sequence[str] | None = DEFAULT_ALLOWED_MARKET_IDS,
    allowed_market_slugs: Sequence[str] | None = DEFAULT_ALLOWED_MARKET_SLUGS,
    allowed_market_tags: Sequence[str] | None = DEFAULT_ALLOWED_MARKET_TAGS,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    policy = RiskLimitPolicy(
        policy_id=clean_text(policy_id),
        mode=clean_text(mode),
        max_daily_loss_usd=5.0,
        max_total_exposure_usd=10.0,
        max_market_exposure_usd=5.0,
        max_order_notional_usd=1.0,
        max_orders_per_day=1,
        max_trades_per_day=1,
        max_active_markets=1,
        cooldown_after_loss_minutes=30,
        halt_on_stale_market_data=True,
        max_market_data_age_seconds=300,
        halt_on_audit_mismatch=True,
        halt_on_kill_switch=True,
        halt_on_missing_operator_intent=True,
        halt_on_missing_readiness_evidence=True,
        halt_on_unresolved_critical_blockers=True,
        halt_on_disabled_live_connector=True,
        halt_on_live_execution_not_approved=True,
        halt_on_canary_not_executable=True,
        halt_on_real_execution_unavailable=True,
        allowed_market_ids=_clean_tuple(allowed_market_ids),
        allowed_market_slugs=_clean_tuple(allowed_market_slugs),
        allowed_market_tags=_clean_tuple(allowed_market_tags),
        review_only_until_live_gate=True,
        generated_at=generated_at,
    ).to_dict()
    validation = validate_risk_limit_policy(policy, generated_at=generated_at)
    policy["validation"] = validation
    if validation.get("valid") is not True:
        raise ValueError("; ".join(validation.get("errors", [])))
    return policy


def build_default_risk_limit_state(
    *,
    exposure_snapshot: Mapping[str, Any] | None = None,
    daily_loss_snapshot: Mapping[str, Any] | None = None,
    unresolved_critical_blockers: Sequence[str] | None = None,
    generated_at: str = GENERATED_AT,
    **overrides: Any,
) -> dict[str, Any]:
    exposure = dict(exposure_snapshot or RiskLimitExposureSnapshot(generated_at=generated_at).to_dict())
    daily_loss = dict(daily_loss_snapshot or RiskLimitDailyLossSnapshot(generated_at=generated_at).to_dict())
    state = RiskLimitState(
        state_id=clean_text(overrides.pop("state_id", "")) or "risk-limit-state-037-default",
        exposure_snapshot=exposure,
        daily_loss_snapshot=daily_loss,
        orders_submitted_today=int(overrides.pop("orders_submitted_today", 0) or 0),
        trades_executed_today=int(overrides.pop("trades_executed_today", 0) or 0),
        market_data_age_seconds=int(overrides.pop("market_data_age_seconds", 0) or 0),
        audit_mismatch_detected=bool(overrides.pop("audit_mismatch_detected", False)),
        kill_switch_active=bool(overrides.pop("kill_switch_active", False)),
        operator_intent_present=overrides.pop("operator_intent_present", True) is True,
        readiness_evidence_present=overrides.pop("readiness_evidence_present", True) is True,
        unresolved_critical_blockers=_clean_tuple(unresolved_critical_blockers),
        live_connector_enabled=False,
        live_execution_approved=False,
        canary_executable_now=False,
        real_execution_available=False,
        generated_at=generated_at,
    ).to_dict()
    return state


def validate_risk_limit_policy(
    policy: RiskLimitPolicy | Mapping[str, Any],
    *,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    value = _mapping(policy)
    errors: list[str] = []
    if value.get("contract_version") != RISK_LIMIT_POLICY_CONTRACT:
        errors.append(f"contract_version must be {RISK_LIMIT_POLICY_CONTRACT}")
    if not clean_text(value.get("policy_id")):
        errors.append("policy_id must be non-empty")
    if clean_text(value.get("mode")) not in POLICY_MODES:
        errors.append(f"mode must be one of {', '.join(sorted(POLICY_MODES))}")
    for field in (
        "max_daily_loss_usd",
        "max_total_exposure_usd",
        "max_market_exposure_usd",
        "max_order_notional_usd",
    ):
        _require_positive_number(value, field, errors)
    for field in (
        "max_orders_per_day",
        "max_trades_per_day",
        "max_active_markets",
        "cooldown_after_loss_minutes",
        "max_market_data_age_seconds",
    ):
        _require_non_negative_integer(value, field, errors)
    for field in (
        "halt_on_stale_market_data",
        "halt_on_audit_mismatch",
        "halt_on_kill_switch",
        "halt_on_missing_operator_intent",
        "halt_on_missing_readiness_evidence",
        "halt_on_unresolved_critical_blockers",
        "halt_on_disabled_live_connector",
        "halt_on_live_execution_not_approved",
        "halt_on_canary_not_executable",
        "halt_on_real_execution_unavailable",
        "review_only_until_live_gate",
    ):
        if not isinstance(value.get(field), bool):
            errors.append(f"{field} must be a boolean")
    for field in ("allowed_market_ids", "allowed_market_slugs", "allowed_market_tags"):
        if not isinstance(value.get(field), list):
            errors.append(f"{field} must be a list")
        elif any(not isinstance(item, str) or not item.strip() for item in value.get(field, [])):
            errors.append(f"{field} must contain only non-empty strings")
    if value.get("review_only_until_live_gate") is not True:
        errors.append("review_only_until_live_gate must be true in this build")
    for field in FORCED_FALSE_EXECUTION_FIELDS[1:]:
        if value.get(field) is not False:
            errors.append(f"{field} must be false in this build")
    valid = not errors
    return {
        "contract_version": "pmbot_risk_limit_policy_validation.v1",
        "validation_id": _stable_id(
            "risk-limit-policy-validation-037",
            {"policy_id": value.get("policy_id"), "errors": errors},
        ),
        "generated_at": generated_at,
        "valid": valid,
        "status": "passed" if valid else "blocked",
        "errors": errors,
        "risk_control_plane_ready": valid,
        "live_execution_approved": False,
        "canary_executable_now": False,
        "real_execution_available": False,
        "live_connector_enabled": False,
    }


def evaluate_risk_limits_for_order_intent(
    order_intent: RiskLimitOrderIntent | Mapping[str, Any],
    state: RiskLimitState | Mapping[str, Any] | None = None,
    policy: RiskLimitPolicy | Mapping[str, Any] | None = None,
    *,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    active_policy = _mapping(policy or build_default_risk_limit_policy(generated_at=generated_at))
    active_state = _mapping(state or build_default_risk_limit_state(generated_at=generated_at))
    intent = _mapping(order_intent)
    exposure = dict(active_state.get("exposure_snapshot", {}))
    daily_loss = dict(active_state.get("daily_loss_snapshot", {}))

    violations: list[dict[str, Any]] = []
    halt_reasons: list[dict[str, Any]] = []

    notional = _number(intent.get("notional_usd"))
    current_total = _number(exposure.get("total_exposure_usd"))
    current_market = _number(exposure.get("market_exposure_usd"))
    projected_total = round(current_total + notional, 2)
    projected_market = round(current_market + notional, 2)
    active_markets = _clean_tuple(exposure.get("active_market_ids"))
    intent_market = clean_text(intent.get("market_id"))
    projected_active_markets = _projected_active_market_count(active_markets, intent_market)
    daily_loss_usd = _number(daily_loss.get("realized_loss_usd"))

    if not _market_allowed(active_policy, intent):
        violations.append(
            _violation(
                "MARKET_NOT_WHITELISTED",
                "market_id",
                {
                    "allowed_market_ids": active_policy.get("allowed_market_ids", []),
                    "allowed_market_slugs": active_policy.get("allowed_market_slugs", []),
                    "allowed_market_tags": active_policy.get("allowed_market_tags", []),
                },
                {"market_id": intent.get("market_id"), "market_slug": intent.get("market_slug")},
                "Order intent market is not in the one-market policy allowlist.",
            )
        )
    if notional > _number(active_policy.get("max_order_notional_usd")):
        violations.append(
            _violation(
                "MAX_ORDER_NOTIONAL_EXCEEDED",
                "notional_usd",
                active_policy.get("max_order_notional_usd"),
                notional,
                "Order intent notional exceeds the policy cap.",
            )
        )
    if projected_total > _number(active_policy.get("max_total_exposure_usd")):
        violations.append(
            _violation(
                "MAX_TOTAL_EXPOSURE_EXCEEDED",
                "projected_total_exposure_usd",
                active_policy.get("max_total_exposure_usd"),
                projected_total,
                "Projected total exposure exceeds the policy cap.",
            )
        )
    if projected_market > _number(active_policy.get("max_market_exposure_usd")):
        violations.append(
            _violation(
                "MAX_MARKET_EXPOSURE_EXCEEDED",
                "projected_market_exposure_usd",
                active_policy.get("max_market_exposure_usd"),
                projected_market,
                "Projected market exposure exceeds the policy cap.",
            )
        )
    if int(active_state.get("orders_submitted_today", 0) or 0) + 1 > int(
        active_policy.get("max_orders_per_day", 0) or 0
    ):
        violations.append(
            _violation(
                "MAX_ORDERS_PER_DAY_EXCEEDED",
                "orders_submitted_today",
                active_policy.get("max_orders_per_day"),
                int(active_state.get("orders_submitted_today", 0) or 0) + 1,
                "Submitting this intent would exceed the daily order count cap.",
            )
        )
    if int(active_state.get("trades_executed_today", 0) or 0) + 1 > int(
        active_policy.get("max_trades_per_day", 0) or 0
    ):
        violations.append(
            _violation(
                "MAX_TRADES_PER_DAY_EXCEEDED",
                "trades_executed_today",
                active_policy.get("max_trades_per_day"),
                int(active_state.get("trades_executed_today", 0) or 0) + 1,
                "Submitting this intent would exceed the daily trade count cap.",
            )
        )
    if projected_active_markets > int(active_policy.get("max_active_markets", 0) or 0):
        violations.append(
            _violation(
                "MAX_ACTIVE_MARKETS_EXCEEDED",
                "active_market_count",
                active_policy.get("max_active_markets"),
                projected_active_markets,
                "Submitting this intent would exceed the active market cap.",
            )
        )
    if active_policy.get("halt_on_missing_operator_intent") is True and (
        not clean_text(intent.get("operator_intent_reference"))
        or active_state.get("operator_intent_present") is not True
    ):
        violations.append(
            _violation(
                "MISSING_OPERATOR_INTENT",
                "operator_intent_reference",
                "present",
                "missing",
                "Operator intent reference is required before even dry-run allowance.",
            )
        )
    if active_policy.get("halt_on_missing_readiness_evidence") is True and (
        not clean_text(intent.get("readiness_evidence_reference"))
        or active_state.get("readiness_evidence_present") is not True
    ):
        violations.append(
            _violation(
                "MISSING_READINESS_EVIDENCE",
                "readiness_evidence_reference",
                "present",
                "missing",
                "Readiness evidence reference is required before even dry-run allowance.",
            )
        )

    if daily_loss_usd >= _number(active_policy.get("max_daily_loss_usd")):
        halt_reasons.append(
            _halt(
                "DAILY_LOSS_LIMIT_BREACHED",
                "realized_loss_usd",
                active_policy.get("max_daily_loss_usd"),
                daily_loss_usd,
                "Daily realized loss is at or above the policy cap.",
            )
        )
    cooldown_minutes = daily_loss.get("minutes_since_last_loss")
    if (
        isinstance(cooldown_minutes, int)
        and not isinstance(cooldown_minutes, bool)
        and cooldown_minutes < int(active_policy.get("cooldown_after_loss_minutes", 0) or 0)
        and daily_loss_usd > 0
    ):
        halt_reasons.append(
            _halt(
                "COOLDOWN_AFTER_LOSS_ACTIVE",
                "minutes_since_last_loss",
                active_policy.get("cooldown_after_loss_minutes"),
                cooldown_minutes,
                "Cooldown after a loss is still active.",
            )
        )
    if active_policy.get("halt_on_stale_market_data") is True and int(
        active_state.get("market_data_age_seconds", 0) or 0
    ) > int(active_policy.get("max_market_data_age_seconds", 0) or 0):
        halt_reasons.append(
            _halt(
                "STALE_MARKET_DATA",
                "market_data_age_seconds",
                active_policy.get("max_market_data_age_seconds"),
                active_state.get("market_data_age_seconds"),
                "Market data age exceeds the policy freshness cap.",
            )
        )
    if active_policy.get("halt_on_audit_mismatch") is True and active_state.get("audit_mismatch_detected") is True:
        halt_reasons.append(
            _halt(
                "AUDIT_MISMATCH_DETECTED",
                "audit_mismatch_detected",
                False,
                True,
                "Audit mismatch is active.",
            )
        )
    if active_policy.get("halt_on_kill_switch") is True and active_state.get("kill_switch_active") is True:
        halt_reasons.append(
            _halt(
                "KILL_SWITCH_ACTIVE",
                "kill_switch_active",
                False,
                True,
                "Kill-switch is active.",
            )
        )
    unresolved = _clean_tuple(active_state.get("unresolved_critical_blockers"))
    if active_policy.get("halt_on_unresolved_critical_blockers") is True and unresolved:
        halt_reasons.append(
            _halt(
                "UNRESOLVED_CRITICAL_BLOCKERS",
                "unresolved_critical_blockers",
                [],
                list(unresolved),
                "Unresolved critical live blockers remain present.",
            )
        )

    live_block_reasons = _live_block_reasons(active_policy, active_state)
    dry_run_only = intent.get("dry_run_only") is True
    if not dry_run_only and active_policy.get("halt_on_disabled_live_connector") is True and (
        active_state.get("live_connector_enabled") is not True
    ):
        halt_reasons.append(
            _halt(
                "LIVE_CONNECTOR_DISABLED",
                "live_connector_enabled",
                True,
                False,
                "Live connector is disabled, so non-dry-run intent cannot continue.",
            )
        )

    if halt_reasons:
        status = DECISION_HALT
    elif violations:
        status = DECISION_BLOCK
    elif dry_run_only:
        status = DECISION_ALLOW_DRY_RUN
    else:
        status = DECISION_REVIEW_ONLY

    allowed_for_dry_run = status == DECISION_ALLOW_DRY_RUN
    capacity = _remaining_capacity(
        policy=active_policy,
        state=active_state,
        exposure=exposure,
        daily_loss=daily_loss,
        notional=notional,
        projected_total=projected_total,
        projected_market=projected_market,
        projected_active_markets=projected_active_markets,
    )
    context = RiskLimitEvaluationContext(
        policy=active_policy,
        state=active_state,
        order_intent=dict(intent),
        generated_at=generated_at,
    ).to_dict()
    decision_id = _stable_id(
        "risk-limit-decision-037",
        {
            "context": context,
            "status": status,
            "violations": violations,
            "halt_reasons": halt_reasons,
            "live_block_reasons": live_block_reasons,
        },
    )
    decision = RiskLimitDecision(
        decision_id=decision_id,
        policy_id=clean_text(active_policy.get("policy_id")),
        intent_id=clean_text(intent.get("intent_id")),
        decision_status=status,
        allowed_for_dry_run=allowed_for_dry_run,
        allowed_for_live=False,
        live_execution_approved=False,
        canary_executable_now=False,
        real_execution_available=False,
        live_connector_enabled=False,
        violations=tuple(violations),
        halt_reasons=tuple(halt_reasons),
        live_block_reasons=tuple(live_block_reasons),
        remaining_capacity=capacity,
        human_summary=_decision_summary(status, violations, halt_reasons, live_block_reasons),
        generated_at=generated_at,
    ).to_dict()
    decision["evaluation_context"] = context
    return decision


def summarize_risk_limit_decision(decision: Mapping[str, Any] | None) -> dict[str, Any]:
    value = dict(decision or {})
    return {
        "contract_version": RISK_LIMIT_DECISION_SUMMARY_CONTRACT,
        "decision_id": clean_text(value.get("decision_id")),
        "policy_id": clean_text(value.get("policy_id")),
        "intent_id": clean_text(value.get("intent_id")),
        "latest_decision_status": clean_text(value.get("decision_status")) or "not_evaluated",
        "allowed_for_dry_run": value.get("allowed_for_dry_run") is True,
        "allowed_for_live": False,
        "latest_violations_count": len(mapping_rows(value.get("violations"))),
        "latest_halt_reasons_count": len(mapping_rows(value.get("halt_reasons"))),
        "live_block_reason_count": len(value.get("live_block_reasons", []))
        if isinstance(value.get("live_block_reasons"), list)
        else 0,
        "human_summary": clean_text(value.get("human_summary")),
        "remaining_capacity": dict(value.get("remaining_capacity", {}))
        if isinstance(value.get("remaining_capacity"), Mapping)
        else {},
        "live_execution_approved": False,
        "canary_executable_now": False,
        "real_execution_available": False,
        "live_connector_enabled": False,
    }


def summarize_risk_limit_policy(policy: Mapping[str, Any] | None) -> dict[str, Any]:
    value = dict(policy or build_default_risk_limit_policy())
    return {
        "contract_version": "pmbot_risk_limit_policy_summary.v1",
        "policy_id": clean_text(value.get("policy_id")),
        "mode": clean_text(value.get("mode")),
        "max_daily_loss_usd": value.get("max_daily_loss_usd"),
        "max_total_exposure_usd": value.get("max_total_exposure_usd"),
        "max_market_exposure_usd": value.get("max_market_exposure_usd"),
        "max_order_notional_usd": value.get("max_order_notional_usd"),
        "max_orders_per_day": value.get("max_orders_per_day"),
        "max_trades_per_day": value.get("max_trades_per_day"),
        "max_active_markets": value.get("max_active_markets"),
        "cooldown_after_loss_minutes": value.get("cooldown_after_loss_minutes"),
        "halt_on_stale_market_data": value.get("halt_on_stale_market_data") is True,
        "max_market_data_age_seconds": value.get("max_market_data_age_seconds"),
        "allowed_market_ids": list(value.get("allowed_market_ids", [])),
        "allowed_market_slugs": list(value.get("allowed_market_slugs", [])),
        "allowed_market_tags": list(value.get("allowed_market_tags", [])),
        "btc_one_market_demo_policy_supported": policy_supports_btc_demo(value),
        "review_only_until_live_gate": value.get("review_only_until_live_gate") is True,
        "live_execution_approved": False,
        "canary_executable_now": False,
        "real_execution_available": False,
        "live_connector_enabled": False,
    }


def build_risk_control_plane_summary(
    *,
    policy: Mapping[str, Any] | None = None,
    latest_decision: Mapping[str, Any] | None = None,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    active_policy = dict(policy or build_default_risk_limit_policy(generated_at=generated_at))
    policy_summary = summarize_risk_limit_policy(active_policy)
    decision_summary = summarize_risk_limit_decision(latest_decision)
    decision_status = decision_summary.get("latest_decision_status")
    if decision_status == DECISION_HALT:
        status = "halted"
    elif decision_status == DECISION_BLOCK:
        status = "blocked"
    elif decision_status == DECISION_ALLOW_DRY_RUN:
        status = "dry_run_allowed"
    elif decision_status == DECISION_REVIEW_ONLY:
        status = "review_only"
    else:
        status = "ready_no_intent_evaluated"
    return {
        "contract_version": RISK_CONTROL_PLANE_SUMMARY_CONTRACT,
        "generated_at": generated_at,
        "risk_control_plane_status": status,
        "risk_control_plane_ready": True,
        "risk_limits_enforced_for_order_intents": True,
        "policy_id": policy_summary["policy_id"],
        "mode": policy_summary["mode"],
        "max_daily_loss_usd": policy_summary["max_daily_loss_usd"],
        "max_total_exposure_usd": policy_summary["max_total_exposure_usd"],
        "max_market_exposure_usd": policy_summary["max_market_exposure_usd"],
        "max_order_notional_usd": policy_summary["max_order_notional_usd"],
        "max_orders_per_day": policy_summary["max_orders_per_day"],
        "max_trades_per_day": policy_summary["max_trades_per_day"],
        "max_active_markets": policy_summary["max_active_markets"],
        "allowed_market_tags": policy_summary["allowed_market_tags"],
        "allowed_market_ids": policy_summary["allowed_market_ids"],
        "allowed_market_slugs": policy_summary["allowed_market_slugs"],
        "btc_one_market_demo_policy_supported": policy_summary["btc_one_market_demo_policy_supported"],
        "future_btc_live_demo_supported_by_limits": policy_summary["btc_one_market_demo_policy_supported"],
        "latest_decision_present": bool(latest_decision),
        "latest_decision_status": decision_summary["latest_decision_status"],
        "latest_violations_count": decision_summary["latest_violations_count"],
        "latest_halt_reasons_count": decision_summary["latest_halt_reasons_count"],
        "allowed_for_dry_run": decision_summary["allowed_for_dry_run"],
        "allowed_for_live": False,
        "live_execution_approved": False,
        "canary_executable_now": False,
        "real_execution_available": False,
        "live_connector_enabled": False,
        "execution_enabling": False,
        "policy_summary": policy_summary,
        "latest_decision_summary": decision_summary,
        "safety_summary": trading_core_safety_summary(),
    }


def is_btc_related_order_intent(order_intent: Mapping[str, Any]) -> bool:
    text = " ".join(
        clean_text(order_intent.get(field)).lower()
        for field in ("market_id", "market_slug", "market_tag", "market_category")
    )
    return "btc" in text or "bitcoin" in text


def policy_supports_btc_demo(policy: Mapping[str, Any]) -> bool:
    tags = {_normalize_market_token(item) for item in policy.get("allowed_market_tags", [])}
    slugs = {_normalize_market_token(item) for item in policy.get("allowed_market_slugs", [])}
    ids = {_normalize_market_token(item) for item in policy.get("allowed_market_ids", [])}
    return bool({"btc", "bitcoin"} & tags or any("btc" in item or "bitcoin" in item for item in slugs | ids))


def restrict_policy_to_one_market(
    policy: Mapping[str, Any],
    *,
    market_id: str = "",
    market_slug: str = "",
) -> dict[str, Any]:
    value = dict(policy)
    if market_id:
        value["allowed_market_ids"] = [clean_text(market_id)]
    if market_slug:
        value["allowed_market_slugs"] = [clean_text(market_slug)]
    validation = validate_risk_limit_policy(value, generated_at=clean_text(value.get("generated_at")) or GENERATED_AT)
    value["validation"] = validation
    if validation.get("valid") is not True:
        raise ValueError("; ".join(validation.get("errors", [])))
    return value


def _market_allowed(policy: Mapping[str, Any], intent: Mapping[str, Any]) -> bool:
    market_id = clean_text(intent.get("market_id"))
    market_slug = clean_text(intent.get("market_slug"))
    allowed_ids = {clean_text(item) for item in policy.get("allowed_market_ids", []) if clean_text(item)}
    allowed_slugs = {clean_text(item) for item in policy.get("allowed_market_slugs", []) if clean_text(item)}
    if allowed_ids or allowed_slugs:
        return market_id in allowed_ids or market_slug in allowed_slugs
    allowed_tags = {_normalize_market_token(item) for item in policy.get("allowed_market_tags", [])}
    if not allowed_tags:
        return True
    intent_tokens = {
        _normalize_market_token(intent.get("market_tag")),
        _normalize_market_token(intent.get("market_category")),
    }
    return bool(intent_tokens & allowed_tags) or is_btc_related_order_intent(intent)


def _live_block_reasons(policy: Mapping[str, Any], state: Mapping[str, Any]) -> list[str]:
    reasons = []
    if policy.get("halt_on_disabled_live_connector") is True and state.get("live_connector_enabled") is not True:
        reasons.append("LIVE_CONNECTOR_DISABLED")
    if policy.get("halt_on_live_execution_not_approved") is True and state.get("live_execution_approved") is not True:
        reasons.append("LIVE_EXECUTION_NOT_APPROVED")
    if policy.get("halt_on_canary_not_executable") is True and state.get("canary_executable_now") is not True:
        reasons.append("CANARY_NOT_EXECUTABLE")
    if policy.get("halt_on_real_execution_unavailable") is True and state.get("real_execution_available") is not True:
        reasons.append("REAL_EXECUTION_UNAVAILABLE")
    return reasons


def _remaining_capacity(
    *,
    policy: Mapping[str, Any],
    state: Mapping[str, Any],
    exposure: Mapping[str, Any],
    daily_loss: Mapping[str, Any],
    notional: float,
    projected_total: float,
    projected_market: float,
    projected_active_markets: int,
) -> dict[str, Any]:
    return {
        "max_daily_loss_remaining_usd": _remaining(_number(policy.get("max_daily_loss_usd")), _number(daily_loss.get("realized_loss_usd"))),
        "max_total_exposure_remaining_before_order_usd": _remaining(
            _number(policy.get("max_total_exposure_usd")),
            _number(exposure.get("total_exposure_usd")),
        ),
        "max_total_exposure_remaining_after_order_usd": _remaining(
            _number(policy.get("max_total_exposure_usd")),
            projected_total,
        ),
        "max_market_exposure_remaining_before_order_usd": _remaining(
            _number(policy.get("max_market_exposure_usd")),
            _number(exposure.get("market_exposure_usd")),
        ),
        "max_market_exposure_remaining_after_order_usd": _remaining(
            _number(policy.get("max_market_exposure_usd")),
            projected_market,
        ),
        "max_order_notional_remaining_usd": _remaining(_number(policy.get("max_order_notional_usd")), notional),
        "orders_remaining_today_before_order": max(
            int(policy.get("max_orders_per_day", 0) or 0) - int(state.get("orders_submitted_today", 0) or 0),
            0,
        ),
        "trades_remaining_today_before_order": max(
            int(policy.get("max_trades_per_day", 0) or 0) - int(state.get("trades_executed_today", 0) or 0),
            0,
        ),
        "active_markets_remaining_after_order": max(
            int(policy.get("max_active_markets", 0) or 0) - projected_active_markets,
            0,
        ),
        "projected_total_exposure_usd": projected_total,
        "projected_market_exposure_usd": projected_market,
        "projected_active_market_count": projected_active_markets,
    }


def _decision_summary(
    status: str,
    violations: Sequence[Mapping[str, Any]],
    halt_reasons: Sequence[Mapping[str, Any]],
    live_block_reasons: Sequence[str],
) -> str:
    if status == DECISION_HALT:
        return "Risk control plane halted the intent: " + ", ".join(row["code"] for row in halt_reasons)
    if status == DECISION_BLOCK:
        return "Risk control plane blocked the intent: " + ", ".join(row["code"] for row in violations)
    if status == DECISION_ALLOW_DRY_RUN:
        return (
            "Risk control plane allowed dry-run evaluation only. "
            f"Live remains unavailable: {', '.join(live_block_reasons)}."
        )
    return (
        "Risk control plane kept the intent review-only because live gates are unavailable: "
        + ", ".join(live_block_reasons)
        + "."
    )


def _violation(code: str, field: str, limit: Any, actual: Any, message: str) -> dict[str, Any]:
    return RiskLimitViolation(
        violation_id=_stable_id(
            "risk-limit-violation-037",
            {"code": code, "field": field, "limit": limit, "actual": actual},
        ),
        code=code,
        field=field,
        limit=limit,
        actual=actual,
        message=message,
    ).to_dict()


def _halt(code: str, field: str, limit: Any, actual: Any, message: str) -> dict[str, Any]:
    return RiskLimitHaltReason(
        halt_id=_stable_id(
            "risk-limit-halt-037",
            {"code": code, "field": field, "limit": limit, "actual": actual},
        ),
        code=code,
        field=field,
        limit=limit,
        actual=actual,
        message=message,
    ).to_dict()


def _risk_control_safety_flags() -> dict[str, Any]:
    return {
        "local_artifact_only": True,
        "static_artifact_only": True,
        "passive_artifact_only": True,
        "dry_run_control_only": True,
        "paper_only": True,
        "execution_enabling": False,
        "environment_inspected": False,
        "environment_secrets_read": False,
        "secrets_read": False,
        "secrets_printed": False,
        "secrets_persisted": False,
        "network_used": False,
        "external_api_calls_performed": False,
        "real_wallet_integration_added": False,
        "real_wallet_access_performed": False,
        "private_key_or_mnemonic_handling_added": False,
        "cryptographic_signing_added": False,
        "cryptographic_signing_performed": False,
        "wallet_signing_added": False,
        "wallet_signing_performed": False,
        "transaction_signing_added": False,
        "transaction_signing_performed": False,
        "real_order_placement_added": False,
        "real_order_placement_performed": False,
        "authenticated_endpoint_added": False,
        "authenticated_endpoint_call_performed": False,
        "browser_automation_added": False,
        "scheduler_or_daemon_added": False,
        "autonomous_live_trading_added": False,
        "allowed_for_live": False,
        "real_execution_available": False,
        "live_execution_approved": False,
        "live_connector_enabled": False,
        "live_execution_allowed": False,
        "live_execution_performed": False,
        "canary_executable_now": False,
        "outcome_resolution_invented": False,
        "pnl_invented": False,
    }


def _projected_active_market_count(active_markets: Sequence[str], intent_market: str) -> int:
    markets = {clean_text(item) for item in active_markets if clean_text(item)}
    if clean_text(intent_market):
        markets.add(clean_text(intent_market))
    return len(markets)


def _remaining(limit: float, actual: float) -> float:
    return round(max(limit - actual, 0.0), 2)


def _number(value: Any) -> float:
    if isinstance(value, bool) or value is None:
        return 0.0
    try:
        return round(float(value), 2)
    except (TypeError, ValueError):
        return 0.0


def _require_positive_number(value: Mapping[str, Any], field: str, errors: list[str]) -> None:
    number = value.get(field)
    if not isinstance(number, (int, float)) or isinstance(number, bool):
        errors.append(f"{field} must be numeric")
    elif number <= 0:
        errors.append(f"{field} must be > 0")


def _require_non_negative_integer(value: Mapping[str, Any], field: str, errors: list[str]) -> None:
    number = value.get(field)
    if not isinstance(number, int) or isinstance(number, bool):
        errors.append(f"{field} must be an integer")
    elif number < 0:
        errors.append(f"{field} must be >= 0")


def _mapping(value: Any) -> dict[str, Any]:
    if hasattr(value, "to_dict"):
        return dict(value.to_dict())
    if isinstance(value, Mapping):
        return dict(value)
    raise TypeError("risk limit value must be a mapping or expose to_dict()")


def _clean_tuple(value: Any) -> tuple[str, ...]:
    if isinstance(value, (list, tuple, set)):
        return tuple(clean_text(item) for item in value if clean_text(item))
    text = clean_text(value)
    return (text,) if text else ()


def _normalize_market_token(value: Any) -> str:
    text = clean_text(value).lower()
    normalized = "".join(ch if ch.isalnum() else "_" for ch in text)
    while "__" in normalized:
        normalized = normalized.replace("__", "_")
    return normalized.strip("_")


def _stable_id(prefix: str, payload: Mapping[str, Any]) -> str:
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()
    return f"{prefix}-{digest[:16]}"
