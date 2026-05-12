from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

from pm_bot.trading_core.live_credentials_auth_boundary import (
    evaluate_live_auth_boundary_for_tiny_canary,
    summarize_live_credentials_status,
)
from pm_bot.trading_core.polymarket_btc_read_only_connector import (
    MARKET_STATUS_CLOSED,
    MARKET_STATUS_OPEN,
    MARKET_STATUS_RESOLVED,
    MARKET_STATUS_UNKNOWN,
    PRICE_STATUS_AVAILABLE,
    summarize_btc_market_snapshot,
)
from pm_bot.trading_core.risk_limit_control_plane import (
    DECISION_ALLOW_DRY_RUN,
    RiskLimitDailyLossSnapshot,
    RiskLimitExposureSnapshot,
    RiskLimitOrderIntent,
    build_default_risk_limit_policy,
    build_default_risk_limit_state,
    build_risk_control_plane_summary,
    evaluate_risk_limits_for_order_intent,
    summarize_risk_limit_decision,
)
from pm_bot.trading_core.schemas import GENERATED_AT, clean_text, trading_core_safety_summary
from pm_bot.trading_core.secret_boundary_policy import (
    validate_secret_boundary_btc_analysis_config,
    validate_secret_boundary_btc_analysis_result,
    validate_secret_boundary_btc_dry_run_order_intent_plan,
    validate_secret_boundary_btc_dry_run_order_intent_result,
    validate_secret_boundary_btc_risk_decision_summary,
)

BTC_MARKET_ANALYSIS_CONFIG_CONTRACT = "pmbot_btc_market_analysis_config.v1"
BTC_MARKET_ANALYSIS_INPUT_CONTRACT = "pmbot_btc_market_analysis_input.v1"
BTC_MARKET_SIGNAL_OBSERVATION_CONTRACT = "pmbot_btc_market_signal_observation.v1"
BTC_MARKET_ANALYSIS_WARNING_CONTRACT = "pmbot_btc_market_analysis_warning.v1"
BTC_MARKET_ANALYSIS_RESULT_CONTRACT = "pmbot_btc_market_analysis_result.v1"
BTC_DRY_RUN_ORDER_INTENT_PLAN_CONTRACT = "pmbot_btc_dry_run_order_intent_plan.v1"
BTC_ORDER_INTENT_DRY_RUN_RESULT_CONTRACT = "pmbot_btc_order_intent_dry_run_result.v1"
BTC_ANALYSIS_RISK_DECISION_SUMMARY_CONTRACT = "pmbot_btc_analysis_risk_decision_summary.v1"
BTC_ANALYSIS_ORDER_INTENT_SUMMARY_CONTRACT = "pmbot_btc_analysis_order_intent_summary.v1"

MODE_DRY_RUN_ORDER_INTENT = "dry_run_order_intent"
INTENT_SOURCE_BTC_MARKET_ANALYSIS_DRY_RUN = "btc_market_analysis_dry_run"

ANALYSIS_READY_FOR_DRY_RUN_INTENT = "analysis_ready_for_dry_run_intent"
BLOCKED_STALE_MARKET_DATA = "blocked_stale_market_data"
BLOCKED_CLOSED_OR_RESOLVED_MARKET = "blocked_closed_or_resolved_market"
BLOCKED_NOT_BTC_MARKET = "blocked_not_btc_market"
BLOCKED_MISSING_REQUIRED_PRICES = "blocked_missing_required_prices"
BLOCKED_SPREAD_TOO_WIDE = "blocked_spread_too_wide"
BLOCKED_LIQUIDITY_TOO_LOW = "blocked_liquidity_too_low"
INSUFFICIENT_DATA_FOR_INTENT = "insufficient_data_for_intent"

INTENT_CANDIDATE_READY = "dry_run_intent_candidate_ready"
INTENT_CANDIDATE_BLOCKED_BY_ANALYSIS = "blocked_by_analysis"
INTENT_CANDIDATE_BLOCKED_MISSING_LIMIT_PRICE = "blocked_missing_limit_price"

DEFAULT_ALLOWED_BTC_TAGS = ("BTC", "BITCOIN")
FORCED_FALSE_EXECUTION_FIELDS = (
    "allowed_for_live",
    "live_execution_approved",
    "canary_executable_now",
    "real_execution_available",
    "live_connector_enabled",
)


@dataclass(frozen=True)
class BTCMarketAnalysisConfig:
    config_id: str
    mode: str
    allowed_market_tags: tuple[str, ...]
    require_btc_related: bool
    require_open_market: bool
    require_not_resolved: bool
    require_fresh_snapshot: bool
    max_snapshot_age_seconds: int
    min_liquidity_usd: float | None
    max_spread: float
    min_best_bid: float | None
    max_best_ask: float | None
    default_dry_run_notional_usd: float
    dry_run_only: bool
    analysis_is_not_live_recommendation: bool
    order_intent_is_not_order_submission: bool
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = BTC_MARKET_ANALYSIS_CONFIG_CONTRACT
        value["allowed_market_tags"] = list(self.allowed_market_tags)
        value.update(_analysis_safety_flags())
        return value


@dataclass(frozen=True)
class BTCMarketAnalysisInput:
    input_id: str
    snapshot: Mapping[str, Any]
    config: Mapping[str, Any]
    operator_intent_reference: str
    readiness_evidence_reference: str
    audit_replay_reference: str
    ui_panel_reference: str
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = BTC_MARKET_ANALYSIS_INPUT_CONTRACT
        value["snapshot"] = dict(self.snapshot)
        value["config"] = dict(self.config)
        value.update(_analysis_safety_flags())
        return value


@dataclass(frozen=True)
class BTCMarketSignalObservation:
    observation_id: str
    signal_key: str
    value: Any
    status: str
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = BTC_MARKET_SIGNAL_OBSERVATION_CONTRACT
        return value


@dataclass(frozen=True)
class BTCMarketAnalysisWarning:
    warning_id: str
    warning_code: str
    severity: str
    message: str

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = BTC_MARKET_ANALYSIS_WARNING_CONTRACT
        return value


@dataclass(frozen=True)
class BTCMarketAnalysisResult:
    analysis_id: str
    config_id: str
    market_id: str
    market_slug: str
    market_title: str
    is_btc_related: bool
    market_status: str
    stale: bool
    best_bid: float | None
    best_ask: float | None
    last_price: float | None
    spread: float | None
    liquidity: float | None
    observations: tuple[Mapping[str, Any], ...]
    warnings: tuple[Mapping[str, Any], ...]
    analysis_status: str
    snapshot_id: str = ""
    price_status: str = ""
    snapshot_age_seconds: int | None = None
    analysis_is_not_live_recommendation: bool = True
    live_execution_approved: bool = False
    allowed_for_live: bool = False
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = BTC_MARKET_ANALYSIS_RESULT_CONTRACT
        value["observations"] = [dict(row) for row in self.observations]
        value["warnings"] = [dict(row) for row in self.warnings]
        value["analysis_ready_for_dry_run_intent"] = self.analysis_status == ANALYSIS_READY_FOR_DRY_RUN_INTENT
        value["btc_market_analysis_ready"] = self.analysis_status == ANALYSIS_READY_FOR_DRY_RUN_INTENT
        value.update(_analysis_safety_flags())
        return value


@dataclass(frozen=True)
class BTCDryRunOrderIntentPlan:
    intent_plan_id: str
    analysis_id: str
    intent_plan_status: str
    dry_run_order_intent_status: str
    order_intent: Mapping[str, Any] | None
    blocked_reason_codes: tuple[str, ...]
    readiness_evidence_reference: str
    operator_intent_reference: str
    audit_replay_reference: str
    btc_market_snapshot_reference: str
    dry_run_only: bool = True
    order_intent_is_not_order_submission: bool = True
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = BTC_DRY_RUN_ORDER_INTENT_PLAN_CONTRACT
        value["order_intent"] = dict(self.order_intent) if isinstance(self.order_intent, Mapping) else None
        value["blocked_reason_codes"] = list(self.blocked_reason_codes)
        value["btc_order_intent_dry_run_ready"] = self.intent_plan_status == INTENT_CANDIDATE_READY
        value["intent_candidate_status"] = self.intent_plan_status
        value["executable_submission_payload_present"] = False
        value.update(_analysis_safety_flags())
        return value


@dataclass(frozen=True)
class BTCAnalysisRiskDecisionSummary:
    summary_id: str
    analysis_id: str
    intent_id: str
    risk_decision_id: str
    risk_decision_status: str
    allowed_for_dry_run: bool
    allowed_for_live: bool
    latest_violations_count: int
    latest_halt_reasons_count: int
    live_execution_approved: bool = False
    canary_executable_now: bool = False
    real_execution_available: bool = False
    live_connector_enabled: bool = False
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = BTC_ANALYSIS_RISK_DECISION_SUMMARY_CONTRACT
        value["risk_checked_order_intent_ready"] = self.risk_decision_status == DECISION_ALLOW_DRY_RUN
        value.update(_analysis_safety_flags())
        return value


@dataclass(frozen=True)
class BTCOrderIntentDryRunResult:
    result_id: str
    analysis: Mapping[str, Any]
    order_intent_plan: Mapping[str, Any]
    risk_decision: Mapping[str, Any] | None
    risk_decision_summary: Mapping[str, Any]
    risk_control_plane_summary: Mapping[str, Any]
    summary: Mapping[str, Any]
    dry_run_only: bool = True
    analysis_is_not_live_recommendation: bool = True
    order_intent_is_not_order_submission: bool = True
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = BTC_ORDER_INTENT_DRY_RUN_RESULT_CONTRACT
        value["analysis"] = dict(self.analysis)
        value["order_intent_plan"] = dict(self.order_intent_plan)
        value["risk_decision"] = dict(self.risk_decision) if isinstance(self.risk_decision, Mapping) else None
        value["risk_decision_summary"] = dict(self.risk_decision_summary)
        value["risk_control_plane_summary"] = dict(self.risk_control_plane_summary)
        value["summary"] = dict(self.summary)
        value["btc_market_analysis_ready"] = self.analysis.get("analysis_ready_for_dry_run_intent") is True
        value["btc_order_intent_dry_run_ready"] = (
            self.order_intent_plan.get("btc_order_intent_dry_run_ready") is True
        )
        value["risk_checked_order_intent_ready"] = (
            self.risk_decision_summary.get("risk_checked_order_intent_ready") is True
        )
        value.update(_analysis_safety_flags())
        return value


def build_default_btc_market_analysis_config(
    *,
    config_id: str = "btc-market-analysis-order-intent-039-default",
    max_snapshot_age_seconds: int = 300,
    min_liquidity_usd: float | None = 100.0,
    max_spread: float = 0.05,
    min_best_bid: float | None = None,
    max_best_ask: float | None = None,
    default_dry_run_notional_usd: float = 1.0,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    config = BTCMarketAnalysisConfig(
        config_id=clean_text(config_id),
        mode=MODE_DRY_RUN_ORDER_INTENT,
        allowed_market_tags=DEFAULT_ALLOWED_BTC_TAGS,
        require_btc_related=True,
        require_open_market=True,
        require_not_resolved=True,
        require_fresh_snapshot=True,
        max_snapshot_age_seconds=int(max_snapshot_age_seconds),
        min_liquidity_usd=_optional_float(min_liquidity_usd),
        max_spread=float(max_spread),
        min_best_bid=_optional_float(min_best_bid),
        max_best_ask=_optional_float(max_best_ask),
        default_dry_run_notional_usd=round(float(default_dry_run_notional_usd), 2),
        dry_run_only=True,
        analysis_is_not_live_recommendation=True,
        order_intent_is_not_order_submission=True,
        generated_at=generated_at,
    ).to_dict()
    validation = validate_btc_market_analysis_config(config, generated_at=generated_at)
    config["validation"] = validation
    if validation.get("valid") is not True:
        raise ValueError("; ".join(validation.get("errors", [])))
    return config


def validate_btc_market_analysis_config(
    config: BTCMarketAnalysisConfig | Mapping[str, Any],
    *,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    value = _mapping(config)
    errors: list[str] = []
    if value.get("contract_version") != BTC_MARKET_ANALYSIS_CONFIG_CONTRACT:
        errors.append(f"contract_version must be {BTC_MARKET_ANALYSIS_CONFIG_CONTRACT}")
    if not clean_text(value.get("config_id")):
        errors.append("config_id must be non-empty")
    if clean_text(value.get("mode")) != MODE_DRY_RUN_ORDER_INTENT:
        errors.append(f"mode must be {MODE_DRY_RUN_ORDER_INTENT}")
    if not isinstance(value.get("allowed_market_tags"), list) or not value.get("allowed_market_tags"):
        errors.append("allowed_market_tags must be a non-empty list")
    elif not _config_has_btc_tag(value.get("allowed_market_tags", [])):
        errors.append("allowed_market_tags must include BTC or Bitcoin")
    for field in (
        "require_btc_related",
        "require_open_market",
        "require_not_resolved",
        "require_fresh_snapshot",
        "dry_run_only",
        "analysis_is_not_live_recommendation",
        "order_intent_is_not_order_submission",
    ):
        if not isinstance(value.get(field), bool):
            errors.append(f"{field} must be a boolean")
    for field in ("dry_run_only", "analysis_is_not_live_recommendation", "order_intent_is_not_order_submission"):
        if value.get(field) is not True:
            errors.append(f"{field} must be true")
    if _int_or_none(value.get("max_snapshot_age_seconds")) is None or int(value.get("max_snapshot_age_seconds")) < 0:
        errors.append("max_snapshot_age_seconds must be a non-negative integer")
    for field in ("max_spread", "default_dry_run_notional_usd"):
        number = _number_or_none(value.get(field))
        if number is None or number <= 0:
            errors.append(f"{field} must be a positive number")
    for field in ("min_liquidity_usd", "min_best_bid", "max_best_ask"):
        number = _number_or_none(value.get(field))
        if value.get(field) is not None and (number is None or number < 0):
            errors.append(f"{field} must be a non-negative number or null")
    default_policy = build_default_risk_limit_policy(generated_at=generated_at)
    notional = _number_or_none(value.get("default_dry_run_notional_usd")) or 0.0
    if notional > float(default_policy.get("max_order_notional_usd", 0) or 0):
        errors.append("default_dry_run_notional_usd must not exceed the default risk policy order cap")
    boundary_validation = validate_secret_boundary_btc_analysis_config(value, generated_at=generated_at)
    if boundary_validation.get("valid") is not True:
        errors.append("config violates BTC analysis secret boundary")
    valid = not errors
    return {
        "contract_version": "pmbot_btc_market_analysis_config_validation.v1",
        "validation_id": _stable_id(
            "btc-market-analysis-config-validation-039",
            {"config_id": value.get("config_id"), "errors": errors},
        ),
        "generated_at": generated_at,
        "valid": valid,
        "status": "passed" if valid else "blocked",
        "errors": errors,
        "config_secret_boundary_validation": boundary_validation,
        "dry_run_only": True,
        "analysis_is_not_live_recommendation": True,
        "order_intent_is_not_order_submission": True,
        "allowed_for_live": False,
        "live_execution_approved": False,
        "canary_executable_now": False,
        "real_execution_available": False,
        "live_connector_enabled": False,
    }


def analyze_btc_market_snapshot(
    snapshot: Mapping[str, Any],
    config: BTCMarketAnalysisConfig | Mapping[str, Any] | None = None,
    *,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    active_config = _mapping(config or build_default_btc_market_analysis_config(generated_at=generated_at))
    validation = validate_btc_market_analysis_config(active_config, generated_at=generated_at)
    if validation.get("valid") is not True:
        raise ValueError("; ".join(validation.get("errors", [])))

    value = dict(snapshot or {})
    snapshot_summary = summarize_btc_market_snapshot(value)
    market_id = clean_text(snapshot_summary.get("market_id"))
    market_slug = clean_text(snapshot_summary.get("market_slug"))
    market_title = clean_text(snapshot_summary.get("market_title"))
    tags = [clean_text(item) for item in snapshot_summary.get("normalized_market_tags", [])]
    is_btc_related = snapshot_summary.get("is_btc_related") is True or _looks_btc_related(
        market_id=market_id,
        market_slug=market_slug,
        market_title=market_title,
        tags=tags,
    )
    market_status = clean_text(snapshot_summary.get("market_status") or MARKET_STATUS_UNKNOWN)
    stale = _is_stale(snapshot_summary, active_config)
    best_bid = _number_or_none(snapshot_summary.get("best_bid"))
    best_ask = _number_or_none(snapshot_summary.get("best_ask"))
    last_price = _number_or_none(snapshot_summary.get("last_price"))
    spread = _number_or_none(snapshot_summary.get("spread"))
    if spread is None and best_bid is not None and best_ask is not None:
        spread = round(max(best_ask - best_bid, 0.0), 6)
    liquidity = _number_or_none(snapshot_summary.get("liquidity"))
    price_status = clean_text(snapshot_summary.get("price_status"))

    observations = [
        _observation("btc_related", is_btc_related, "passed" if is_btc_related else "blocked"),
        _observation("market_status", market_status, "passed" if market_status == MARKET_STATUS_OPEN else "blocked"),
        _observation("snapshot_freshness", "fresh" if not stale else "stale", "passed" if not stale else "blocked"),
        _observation(
            "price_availability",
            {"best_bid": best_bid, "best_ask": best_ask, "last_price": last_price},
            "passed" if best_bid is not None and best_ask is not None else "blocked",
        ),
        _observation("spread", spread, "passed" if spread is not None and spread <= float(active_config["max_spread"]) else "blocked"),
        _observation(
            "liquidity",
            liquidity,
            "passed" if _liquidity_passes(liquidity, active_config) else "blocked",
        ),
    ]
    warnings: list[dict[str, Any]] = []
    analysis_status = ANALYSIS_READY_FOR_DRY_RUN_INTENT

    if active_config.get("require_btc_related") is True and not is_btc_related:
        analysis_status = BLOCKED_NOT_BTC_MARKET
        warnings.append(_warning("NOT_BTC_MARKET", "Snapshot is not tagged or titled as BTC/Bitcoin."))
    elif (
        active_config.get("require_open_market") is True
        and market_status != MARKET_STATUS_OPEN
        or active_config.get("require_not_resolved") is True
        and market_status == MARKET_STATUS_RESOLVED
    ):
        analysis_status = BLOCKED_CLOSED_OR_RESOLVED_MARKET
        warnings.append(_warning("CLOSED_OR_RESOLVED_MARKET", "Snapshot market status is not open and unresolved."))
    elif active_config.get("require_fresh_snapshot") is True and stale:
        analysis_status = BLOCKED_STALE_MARKET_DATA
        warnings.append(_warning("STALE_MARKET_DATA", "Snapshot is stale under the analysis freshness policy."))
    elif best_bid is None or best_ask is None:
        analysis_status = BLOCKED_MISSING_REQUIRED_PRICES
        warnings.append(_warning("MISSING_REQUIRED_PRICES", "Best bid and best ask are required for dry-run intent."))
    elif spread is None:
        analysis_status = INSUFFICIENT_DATA_FOR_INTENT
        warnings.append(_warning("INSUFFICIENT_SPREAD_DATA", "Spread could not be computed deterministically."))
    elif spread > float(active_config["max_spread"]):
        analysis_status = BLOCKED_SPREAD_TOO_WIDE
        warnings.append(_warning("SPREAD_TOO_WIDE", "Snapshot spread exceeds the dry-run analysis policy."))
    elif not _liquidity_passes(liquidity, active_config):
        analysis_status = BLOCKED_LIQUIDITY_TOO_LOW
        warnings.append(_warning("LIQUIDITY_TOO_LOW", "Snapshot liquidity is below the configured dry-run floor."))
    elif active_config.get("min_best_bid") is not None and best_bid < float(active_config["min_best_bid"]):
        analysis_status = INSUFFICIENT_DATA_FOR_INTENT
        warnings.append(_warning("BEST_BID_BELOW_MINIMUM", "Best bid is below the configured dry-run floor."))
    elif active_config.get("max_best_ask") is not None and best_ask > float(active_config["max_best_ask"]):
        analysis_status = INSUFFICIENT_DATA_FOR_INTENT
        warnings.append(_warning("BEST_ASK_ABOVE_MAXIMUM", "Best ask is above the configured dry-run ceiling."))
    elif price_status and price_status != PRICE_STATUS_AVAILABLE:
        analysis_status = INSUFFICIENT_DATA_FOR_INTENT
        warnings.append(_warning("PRICE_STATUS_NOT_AVAILABLE", "Snapshot price status is not available."))

    analysis_id = _stable_id(
        "btc-market-analysis-039",
        {
            "config_id": active_config.get("config_id"),
            "snapshot_id": snapshot_summary.get("snapshot_id"),
            "market_id": market_id,
            "market_slug": market_slug,
            "analysis_status": analysis_status,
            "best_bid": best_bid,
            "best_ask": best_ask,
            "spread": spread,
            "liquidity": liquidity,
        },
    )
    result = BTCMarketAnalysisResult(
        analysis_id=analysis_id,
        config_id=clean_text(active_config.get("config_id")),
        market_id=market_id,
        market_slug=market_slug,
        market_title=market_title,
        is_btc_related=is_btc_related,
        market_status=market_status,
        stale=stale,
        best_bid=best_bid,
        best_ask=best_ask,
        last_price=last_price,
        spread=spread,
        liquidity=liquidity,
        observations=tuple(observations),
        warnings=tuple(warnings),
        analysis_status=analysis_status,
        snapshot_id=clean_text(snapshot_summary.get("snapshot_id")),
        price_status=price_status,
        snapshot_age_seconds=_int_or_none(snapshot_summary.get("snapshot_age_seconds")),
        generated_at=generated_at,
    ).to_dict()
    boundary_validation = validate_secret_boundary_btc_analysis_result(result, generated_at=generated_at)
    result["analysis_secret_boundary_validation"] = boundary_validation
    if boundary_validation.get("valid") is not True:
        result["analysis_status"] = INSUFFICIENT_DATA_FOR_INTENT
        result["analysis_ready_for_dry_run_intent"] = False
        result["btc_market_analysis_ready"] = False
    return result


def build_btc_dry_run_order_intent(
    analysis: Mapping[str, Any],
    config: BTCMarketAnalysisConfig | Mapping[str, Any] | None = None,
    *,
    operator_intent_reference: str = "live_canary_operator_intent_packet-034:review-only",
    readiness_evidence_reference: str = "live_canary_readiness_evidence_bundle-035:review-only",
    audit_replay_reference: str = "live_connector_audit_replay-032:review-only",
    ui_panel_reference: str = "operator_ui_panel_v1-036:review-only",
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    active_config = _mapping(config or build_default_btc_market_analysis_config(generated_at=generated_at))
    value = dict(analysis)
    blocked_reasons: list[str] = []
    intent: dict[str, Any] | None = None
    status = INTENT_CANDIDATE_BLOCKED_BY_ANALYSIS
    if value.get("analysis_status") != ANALYSIS_READY_FOR_DRY_RUN_INTENT:
        blocked_reasons.append(clean_text(value.get("analysis_status")) or INSUFFICIENT_DATA_FOR_INTENT)
    else:
        limit_price = _intent_limit_price(value)
        if limit_price is None or limit_price <= 0:
            status = INTENT_CANDIDATE_BLOCKED_MISSING_LIMIT_PRICE
            blocked_reasons.append(BLOCKED_MISSING_REQUIRED_PRICES)
        else:
            notional = round(float(active_config.get("default_dry_run_notional_usd", 1.0) or 1.0), 2)
            quantity = round(notional / limit_price, 6)
            risk_intent = RiskLimitOrderIntent(
                intent_id=_stable_id(
                    "btc-dry-run-order-intent-039",
                    {
                        "analysis_id": value.get("analysis_id"),
                        "market_id": value.get("market_id"),
                        "market_slug": value.get("market_slug"),
                        "notional_usd": notional,
                        "limit_price": limit_price,
                    },
                ),
                market_id=clean_text(value.get("market_id")),
                market_slug=clean_text(value.get("market_slug")),
                market_tag="BTC",
                market_category="bitcoin",
                side_label=_side_label(value),
                notional_usd=notional,
                quantity=quantity,
                limit_price=limit_price,
                intent_source=INTENT_SOURCE_BTC_MARKET_ANALYSIS_DRY_RUN,
                created_at=generated_at,
                dry_run_only=True,
                operator_intent_reference=clean_text(operator_intent_reference),
                readiness_evidence_reference=clean_text(readiness_evidence_reference),
                audit_replay_reference=clean_text(audit_replay_reference),
                ui_panel_reference=clean_text(ui_panel_reference),
            ).to_dict()
            risk_intent.update(
                {
                    "analysis_reference": clean_text(value.get("analysis_id")),
                    "readiness_evidence_reference": clean_text(readiness_evidence_reference),
                    "operator_intent_reference": clean_text(operator_intent_reference),
                    "audit_replay_reference": clean_text(audit_replay_reference),
                    "btc_market_snapshot_reference": clean_text(value.get("snapshot_id")),
                    "market_title": clean_text(value.get("market_title")),
                    "analysis_is_not_live_recommendation": True,
                    "order_intent_is_not_order_submission": True,
                    "dry_run_only": True,
                    "execution_enabling": False,
                    "allowed_for_live": False,
                    "live_execution_approved": False,
                    "canary_executable_now": False,
                    "real_execution_available": False,
                    "live_connector_enabled": False,
                }
            )
            intent = risk_intent
            status = INTENT_CANDIDATE_READY
    plan = BTCDryRunOrderIntentPlan(
        intent_plan_id=_stable_id(
            "btc-dry-run-order-intent-plan-039",
            {
                "analysis_id": value.get("analysis_id"),
                "status": status,
                "blocked_reasons": blocked_reasons,
                "intent": intent,
            },
        ),
        analysis_id=clean_text(value.get("analysis_id")),
        intent_plan_status=status,
        dry_run_order_intent_status=status,
        order_intent=intent,
        blocked_reason_codes=tuple(blocked_reasons),
        readiness_evidence_reference=clean_text(readiness_evidence_reference),
        operator_intent_reference=clean_text(operator_intent_reference),
        audit_replay_reference=clean_text(audit_replay_reference),
        btc_market_snapshot_reference=clean_text(value.get("snapshot_id")),
        generated_at=generated_at,
    ).to_dict()
    boundary_validation = validate_secret_boundary_btc_dry_run_order_intent_plan(plan, generated_at=generated_at)
    plan["order_intent_plan_secret_boundary_validation"] = boundary_validation
    if boundary_validation.get("valid") is not True:
        plan["intent_plan_status"] = "secret_boundary_blocked"
        plan["dry_run_order_intent_status"] = "secret_boundary_blocked"
        plan["btc_order_intent_dry_run_ready"] = False
        plan["order_intent"] = None
    return plan


def evaluate_btc_analysis_to_order_intent(
    snapshot: Mapping[str, Any],
    config: BTCMarketAnalysisConfig | Mapping[str, Any] | None = None,
    *,
    policy: Mapping[str, Any] | None = None,
    risk_state: Mapping[str, Any] | None = None,
    operator_intent_reference: str = "live_canary_operator_intent_packet-034:review-only",
    readiness_evidence_reference: str = "live_canary_readiness_evidence_bundle-035:review-only",
    audit_replay_reference: str = "live_connector_audit_replay-032:review-only",
    ui_panel_reference: str = "operator_ui_panel_v1-036:review-only",
    latest_btc_analysis_path: str = "",
    latest_btc_order_intent_path: str = "",
    latest_btc_risk_decision_path: str = "",
    live_auth_boundary_decision: Mapping[str, Any] | None = None,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    active_config = _mapping(config or build_default_btc_market_analysis_config(generated_at=generated_at))
    active_policy = dict(policy or build_default_risk_limit_policy(generated_at=generated_at))
    active_live_auth_decision = dict(
        live_auth_boundary_decision or evaluate_live_auth_boundary_for_tiny_canary(generated_at=generated_at)
    )
    live_auth_summary = summarize_live_credentials_status(active_live_auth_decision, generated_at=generated_at)
    analysis = analyze_btc_market_snapshot(snapshot, active_config, generated_at=generated_at)
    intent_plan = build_btc_dry_run_order_intent(
        analysis,
        active_config,
        operator_intent_reference=operator_intent_reference,
        readiness_evidence_reference=readiness_evidence_reference,
        audit_replay_reference=audit_replay_reference,
        ui_panel_reference=ui_panel_reference,
        generated_at=generated_at,
    )
    risk_intent = intent_plan.get("order_intent")
    if not isinstance(risk_intent, Mapping):
        risk_intent = _risk_check_only_intent_from_analysis(
            analysis,
            active_config,
            operator_intent_reference=operator_intent_reference,
            readiness_evidence_reference=readiness_evidence_reference,
            audit_replay_reference=audit_replay_reference,
        ui_panel_reference=ui_panel_reference,
        generated_at=generated_at,
    )
    state = _risk_state_with_live_auth_boundary(
        risk_state=risk_state,
        snapshot=snapshot,
        live_auth_summary=live_auth_summary,
        generated_at=generated_at,
    )
    risk_decision = evaluate_risk_limits_for_order_intent(
        risk_intent,
        state=state,
        policy=active_policy,
        generated_at=generated_at,
    )
    risk_decision_summary = _build_btc_risk_decision_summary(
        analysis=analysis,
        risk_decision=risk_decision,
        generated_at=generated_at,
    )
    risk_control_summary = build_risk_control_plane_summary(
        policy=active_policy,
        latest_decision=risk_decision,
        btc_market_snapshot=snapshot,
        generated_at=generated_at,
    )
    summary = summarize_btc_analysis_order_intent(
        analysis=analysis,
        order_intent_plan=intent_plan,
        risk_decision_summary=risk_decision_summary,
        risk_control_plane_summary=risk_control_summary,
        latest_btc_analysis_path=latest_btc_analysis_path,
        latest_btc_order_intent_path=latest_btc_order_intent_path,
        latest_btc_risk_decision_path=latest_btc_risk_decision_path,
        live_credentials_auth_boundary_summary=live_auth_summary,
        generated_at=generated_at,
    )
    result = BTCOrderIntentDryRunResult(
        result_id=_stable_id(
            "btc-order-intent-dry-run-result-039",
            {
                "analysis_id": analysis.get("analysis_id"),
                "intent_plan_id": intent_plan.get("intent_plan_id"),
                "risk_decision_id": risk_decision.get("decision_id"),
            },
        ),
        analysis=analysis,
        order_intent_plan=intent_plan,
        risk_decision=risk_decision,
        risk_decision_summary=risk_decision_summary,
        risk_control_plane_summary=risk_control_summary,
        summary=summary,
        generated_at=generated_at,
    ).to_dict()
    result["live_credentials_boundary_status"] = live_auth_summary
    result["live_auth_ready_for_future_tiny_canary_review"] = (
        live_auth_summary.get("live_auth_ready_for_future_tiny_canary_review") is True
    )
    result["allowed_for_live"] = False
    result["canary_executable_now"] = False
    result["live_execution_approved"] = False
    result["real_execution_available"] = False
    result["live_connector_enabled"] = False
    boundary_validation = validate_secret_boundary_btc_dry_run_order_intent_result(result, generated_at=generated_at)
    result["result_secret_boundary_validation"] = boundary_validation
    if boundary_validation.get("valid") is not True:
        result["btc_order_intent_dry_run_ready"] = False
        result["risk_checked_order_intent_ready"] = False
    return result


def summarize_btc_analysis_order_intent(
    result: Mapping[str, Any] | None = None,
    *,
    analysis: Mapping[str, Any] | None = None,
    order_intent_plan: Mapping[str, Any] | None = None,
    risk_decision_summary: Mapping[str, Any] | None = None,
    risk_control_plane_summary: Mapping[str, Any] | None = None,
    latest_btc_analysis_path: str = "",
    latest_btc_order_intent_path: str = "",
    latest_btc_risk_decision_path: str = "",
    live_credentials_auth_boundary_summary: Mapping[str, Any] | None = None,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    value = dict(result or {})
    active_analysis = dict(analysis or value.get("analysis", {}))
    active_plan = dict(order_intent_plan or value.get("order_intent_plan", {}))
    active_risk_summary = dict(risk_decision_summary or value.get("risk_decision_summary", {}))
    active_risk_control = dict(risk_control_plane_summary or value.get("risk_control_plane_summary", {}))
    active_live_auth = dict(
        live_credentials_auth_boundary_summary
        or value.get("live_credentials_boundary_status", {})
        or active_risk_control
    )
    order_intent = active_plan.get("order_intent")
    intent = dict(order_intent) if isinstance(order_intent, Mapping) else {}
    summary = {
        "contract_version": BTC_ANALYSIS_ORDER_INTENT_SUMMARY_CONTRACT,
        "summary_id": _stable_id(
            "btc-analysis-order-intent-summary-039",
            {
                "analysis_id": active_analysis.get("analysis_id"),
                "intent_plan_id": active_plan.get("intent_plan_id"),
                "risk_summary_id": active_risk_summary.get("summary_id"),
            },
        ),
        "generated_at": generated_at,
        "btc_market_analysis_status": clean_text(active_analysis.get("analysis_status") or "not_evaluated"),
        "btc_intent_candidate_status": clean_text(active_plan.get("intent_candidate_status") or "not_evaluated"),
        "dry_run_order_intent_status": clean_text(active_plan.get("dry_run_order_intent_status") or "not_evaluated"),
        "intent_market_id": clean_text(intent.get("market_id") or active_analysis.get("market_id")),
        "intent_market_slug": clean_text(intent.get("market_slug") or active_analysis.get("market_slug")),
        "intent_notional_usd": intent.get("notional_usd"),
        "intent_limit_price": intent.get("limit_price"),
        "risk_decision_status": clean_text(
            active_risk_summary.get("risk_decision_status")
            or active_risk_control.get("latest_decision_status")
            or "not_evaluated"
        ),
        "allowed_for_dry_run": active_risk_summary.get("allowed_for_dry_run") is True,
        "allowed_for_live": False,
        "analysis_is_not_live_recommendation": True,
        "order_intent_is_not_order_submission": True,
        "latest_btc_analysis_path": clean_text(latest_btc_analysis_path),
        "latest_btc_order_intent_path": clean_text(latest_btc_order_intent_path),
        "latest_btc_risk_decision_path": clean_text(latest_btc_risk_decision_path),
        "live_credentials_boundary_status": (
            clean_text(
                active_live_auth.get("live_credentials_boundary_status")
                or active_live_auth.get("decision_status")
            )
            or "not_evaluated"
        ),
        "live_credentials_configured": active_live_auth.get("live_credentials_configured") is True,
        "live_auth_ready_for_future_tiny_canary_review": (
            active_live_auth.get("live_auth_ready_for_future_tiny_canary_review") is True
        ),
        "authenticated_endpoints_enabled": False,
        "signing_enabled": False,
        "cryptographic_signing_enabled": False,
        "wallet_signing_enabled": False,
        "order_submission_enabled": False,
        "execution_enabling": False,
        "live_execution_approved": False,
        "canary_executable_now": False,
        "real_execution_available": False,
        "live_connector_enabled": False,
    }
    summary.update(_analysis_safety_flags())
    return summary


def _risk_state_with_live_auth_boundary(
    *,
    risk_state: Mapping[str, Any] | None,
    snapshot: Mapping[str, Any],
    live_auth_summary: Mapping[str, Any],
    generated_at: str,
) -> dict[str, Any]:
    if isinstance(risk_state, Mapping):
        state = dict(risk_state)
    else:
        state = build_default_risk_limit_state(
            exposure_snapshot=RiskLimitExposureSnapshot(generated_at=generated_at).to_dict(),
            daily_loss_snapshot=RiskLimitDailyLossSnapshot(generated_at=generated_at).to_dict(),
            btc_market_snapshot=snapshot,
            operator_intent_present=True,
            readiness_evidence_present=True,
            generated_at=generated_at,
        )
    state.update(
        {
            "live_credentials_boundary_status": (
                clean_text(
                    live_auth_summary.get("live_credentials_boundary_status")
                    or live_auth_summary.get("decision_status")
                )
                or "not_evaluated"
            ),
            "live_credentials_configured": live_auth_summary.get("live_credentials_configured") is True,
            "live_mode_explicitly_requested": live_auth_summary.get("live_mode_explicitly_requested") is True,
            "live_auth_ready_for_future_tiny_canary_review": (
                live_auth_summary.get("live_auth_ready_for_future_tiny_canary_review") is True
            ),
            "authenticated_endpoints_enabled": False,
            "order_submission_enabled": False,
            "cryptographic_signing_enabled": False,
            "wallet_signing_enabled": False,
            "allowed_for_live": False,
            "canary_executable_now": False,
            "live_execution_approved": False,
            "real_execution_available": False,
            "live_connector_enabled": False,
        }
    )
    return state


def _build_btc_risk_decision_summary(
    *,
    analysis: Mapping[str, Any],
    risk_decision: Mapping[str, Any],
    generated_at: str,
) -> dict[str, Any]:
    summarized = summarize_risk_limit_decision(risk_decision)
    result = BTCAnalysisRiskDecisionSummary(
        summary_id=_stable_id(
            "btc-analysis-risk-decision-summary-039",
            {
                "analysis_id": analysis.get("analysis_id"),
                "decision_id": risk_decision.get("decision_id"),
                "decision_status": risk_decision.get("decision_status"),
            },
        ),
        analysis_id=clean_text(analysis.get("analysis_id")),
        intent_id=clean_text(risk_decision.get("intent_id")),
        risk_decision_id=clean_text(risk_decision.get("decision_id")),
        risk_decision_status=clean_text(summarized.get("latest_decision_status")),
        allowed_for_dry_run=summarized.get("allowed_for_dry_run") is True,
        allowed_for_live=False,
        latest_violations_count=int(summarized.get("latest_violations_count", 0) or 0),
        latest_halt_reasons_count=int(summarized.get("latest_halt_reasons_count", 0) or 0),
        generated_at=generated_at,
    ).to_dict()
    boundary_validation = validate_secret_boundary_btc_risk_decision_summary(result, generated_at=generated_at)
    result["risk_decision_summary_secret_boundary_validation"] = boundary_validation
    return result


def _risk_check_only_intent_from_analysis(
    analysis: Mapping[str, Any],
    config: Mapping[str, Any],
    *,
    operator_intent_reference: str,
    readiness_evidence_reference: str,
    audit_replay_reference: str,
    ui_panel_reference: str,
    generated_at: str,
) -> dict[str, Any]:
    limit_price = _intent_limit_price(analysis) or 0.01
    notional = round(float(config.get("default_dry_run_notional_usd", 1.0) or 1.0), 2)
    return RiskLimitOrderIntent(
        intent_id=_stable_id(
            "btc-risk-check-only-intent-039",
            {
                "analysis_id": analysis.get("analysis_id"),
                "analysis_status": analysis.get("analysis_status"),
                "market_id": analysis.get("market_id"),
                "market_slug": analysis.get("market_slug"),
            },
        ),
        market_id=clean_text(analysis.get("market_id")),
        market_slug=clean_text(analysis.get("market_slug")),
        market_tag="BTC" if analysis.get("is_btc_related") is True else "NON_BTC",
        market_category="bitcoin" if analysis.get("is_btc_related") is True else "not_btc",
        side_label="risk_check_only",
        notional_usd=notional,
        quantity=round(notional / limit_price, 6) if limit_price > 0 else 0.0,
        limit_price=limit_price,
        intent_source="btc_market_analysis_risk_check_only",
        created_at=generated_at,
        dry_run_only=True,
        operator_intent_reference=clean_text(operator_intent_reference),
        readiness_evidence_reference=clean_text(readiness_evidence_reference),
        audit_replay_reference=clean_text(audit_replay_reference),
        ui_panel_reference=clean_text(ui_panel_reference),
    ).to_dict()


def _intent_limit_price(analysis: Mapping[str, Any]) -> float | None:
    return _number_or_none(analysis.get("best_ask"), analysis.get("last_price"), analysis.get("best_bid"))


def _side_label(analysis: Mapping[str, Any]) -> str:
    if clean_text(analysis.get("market_status")) == MARKET_STATUS_OPEN:
        return "track_primary_outcome"
    return "risk_check_only"


def _is_stale(snapshot_summary: Mapping[str, Any], config: Mapping[str, Any]) -> bool:
    if snapshot_summary.get("stale") is True:
        return True
    age = _int_or_none(snapshot_summary.get("snapshot_age_seconds"))
    max_age = _int_or_none(config.get("max_snapshot_age_seconds"))
    return age is not None and max_age is not None and age > max_age


def _liquidity_passes(liquidity: float | None, config: Mapping[str, Any]) -> bool:
    min_liquidity = _number_or_none(config.get("min_liquidity_usd"))
    if min_liquidity is None:
        return True
    return liquidity is not None and liquidity >= min_liquidity


def _observation(signal_key: str, value: Any, status: str, notes: str = "") -> dict[str, Any]:
    return BTCMarketSignalObservation(
        observation_id=_stable_id(
            "btc-market-signal-observation-039",
            {"signal_key": signal_key, "value": _json_safe(value), "status": status},
        ),
        signal_key=signal_key,
        value=value,
        status=status,
        notes=notes,
    ).to_dict()


def _warning(warning_code: str, message: str, *, severity: str = "block") -> dict[str, Any]:
    return BTCMarketAnalysisWarning(
        warning_id=_stable_id(
            "btc-market-analysis-warning-039",
            {"warning_code": warning_code, "message": message, "severity": severity},
        ),
        warning_code=warning_code,
        severity=severity,
        message=message,
    ).to_dict()


def _looks_btc_related(*, market_id: str, market_slug: str, market_title: str, tags: Sequence[str]) -> bool:
    text = " ".join([market_id, market_slug, market_title, *tags]).lower()
    tokens = {_normalize_token(item) for item in [market_id, market_slug, market_title, *tags]}
    return "bitcoin" in text or "btc" in tokens or any("btc" in token or "bitcoin" in token for token in tokens)


def _config_has_btc_tag(tags: Sequence[Any]) -> bool:
    normalized = {_normalize_token(item) for item in tags}
    return "btc" in normalized or "bitcoin" in normalized


def _optional_float(value: Any) -> float | None:
    number = _number_or_none(value)
    return number if number is not None else None


def _number_or_none(*values: Any) -> float | None:
    for value in values:
        if value is None or isinstance(value, bool):
            continue
        try:
            return round(float(value), 6)
        except (TypeError, ValueError):
            continue
    return None


def _int_or_none(value: Any) -> int | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _mapping(value: Any) -> dict[str, Any]:
    if hasattr(value, "to_dict"):
        return dict(value.to_dict())
    if isinstance(value, Mapping):
        return dict(value)
    raise TypeError("BTC market analysis value must be a mapping or expose to_dict()")


def _json_safe(value: Any) -> Any:
    try:
        json.dumps(value, sort_keys=True)
        return value
    except TypeError:
        if isinstance(value, Mapping):
            return {clean_text(key): _json_safe(nested) for key, nested in value.items()}
        if isinstance(value, list):
            return [_json_safe(item) for item in value]
        return clean_text(value)


def _normalize_token(value: Any) -> str:
    normalized = "".join(ch if ch.isalnum() else "_" for ch in clean_text(value).lower())
    while "__" in normalized:
        normalized = normalized.replace("__", "_")
    return normalized.strip("_")


def _stable_id(prefix: str, payload: Mapping[str, Any]) -> str:
    digest = hashlib.sha256(json.dumps(_json_safe(payload), sort_keys=True).encode("utf-8")).hexdigest()
    return f"{prefix}-{digest[:16]}"


def _analysis_safety_flags() -> dict[str, Any]:
    value = {
        "local_artifact_only": True,
        "static_artifact_only": True,
        "passive_artifact_only": True,
        "dry_run_only": True,
        "dry_run_control_only": True,
        "paper_only": True,
        "analysis_is_not_live_recommendation": True,
        "order_intent_is_not_order_submission": True,
        "execution_enabling": False,
        "network_used": False,
        "external_api_calls_performed": False,
        "environment_inspected": False,
        "environment_secrets_read": False,
        "secrets_read": False,
        "secrets_printed": False,
        "secrets_persisted": False,
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
        "authenticated_endpoints_enabled": False,
        "authenticated_endpoint_call_performed": False,
        "order_submission_enabled": False,
        "cryptographic_signing_enabled": False,
        "wallet_signing_enabled": False,
        "browser_automation_added": False,
        "scheduler_or_daemon_added": False,
        "autonomous_live_trading_added": False,
        "allowed_for_live": False,
        "canary_executable_now": False,
        "live_execution_approved": False,
        "real_execution_available": False,
        "live_connector_enabled": False,
        "live_execution_allowed": False,
        "live_execution_performed": False,
        "outcome_resolution_invented": False,
        "price_data_invented": False,
        "pnl_invented": False,
    }
    value["safety_summary"] = trading_core_safety_summary()
    return value
