from __future__ import annotations

from typing import Any, Mapping

from pm_bot.trading_core.paper_trading_loop_models import (
    REQUIRED_FALSE_FLAGS,
    PaperExecutionRisk,
    paper_trading_safety_flags,
)
from pm_bot.trading_core.schemas import GENERATED_AT, clean_text


def evaluate_paper_execution_risk(
    *,
    signal: Mapping[str, Any] | None,
    artifact_run_id: str,
    strategy_name: str,
    market_symbol: str,
    dry_run: bool,
    execution_mode: str = "paper",
    live_execution_approved: bool = False,
    authenticated_polymarket_enabled: bool = False,
    wallet_signing_enabled: bool = False,
    signing_enabled: bool = False,
    order_submission_enabled: bool = False,
    payload_generation_enabled: bool = False,
    order_generation_enabled: bool = False,
    confidence_threshold: float = 0.65,
    price_min: float = 0.01,
    price_max: float = 0.99,
    size_min: float = 0.1,
    size_max: float = 2.0,
    notional_cap: float = 1.0,
    max_paper_intents_per_run: int = 1,
    paper_intents_this_run: int = 0,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    blockers: list[str] = []
    if dry_run is not True:
        blockers.append("dry_run must be true; live behavior is not available")
    if clean_text(execution_mode) != "paper":
        blockers.append("execution_mode must be paper")

    requested_flags = paper_trading_safety_flags()
    requested_flags["live_execution_approved"] = live_execution_approved is True
    requested_flags["authenticated_polymarket_enabled"] = authenticated_polymarket_enabled is True
    requested_flags["wallet_signing_enabled"] = wallet_signing_enabled is True
    requested_flags["signing_enabled"] = signing_enabled is True
    requested_flags["order_submission_enabled"] = order_submission_enabled is True
    requested_flags["signed_" + "payload_generation_enabled"] = payload_generation_enabled is True
    requested_flags["signed_" + "order_generation_enabled"] = order_generation_enabled is True
    for field in REQUIRED_FALSE_FLAGS:
        if requested_flags.get(field) is not False:
            blockers.append(f"{field} must remain false")

    if signal is None:
        blockers.append("strategy produced no signal")
        signal_value: dict[str, Any] = {}
    else:
        signal_value = dict(signal)
        confidence = _number(signal_value.get("confidence"))
        limit_price = _number(signal_value.get("limit_price"))
        size = _number(signal_value.get("size"))
        notional = _number(signal_value.get("notional"))
        if confidence is None or confidence < confidence_threshold:
            blockers.append(f"confidence must be at least {confidence_threshold}")
        if limit_price is None or limit_price < price_min or limit_price > price_max:
            blockers.append(f"limit_price must be between {price_min} and {price_max}")
        if size is None or size < size_min or size > size_max:
            blockers.append(f"size must be between {size_min} and {size_max}")
        if notional is None or notional <= 0 or notional > notional_cap:
            blockers.append(f"notional must be greater than 0 and no more than {notional_cap}")

    if paper_intents_this_run >= max_paper_intents_per_run:
        blockers.append("max paper intents per run reached")

    approved = not blockers
    risk = PaperExecutionRisk(
        artifact_run_id=artifact_run_id,
        strategy_name=clean_text(strategy_name),
        market_symbol=clean_text(market_symbol).upper(),
        risk_decision="APPROVED_FOR_PAPER_INTENT" if approved else "BLOCKED",
        approved_for_paper_intent=approved,
        risk_blockers=tuple(blockers),
        operator_summary=_operator_summary(approved=approved, blockers=blockers),
        confidence_threshold=confidence_threshold,
        price_min=price_min,
        price_max=price_max,
        size_min=size_min,
        size_max=size_max,
        notional_cap=notional_cap,
        max_paper_intents_per_run=max_paper_intents_per_run,
        paper_intents_this_run=paper_intents_this_run,
        generated_at=generated_at,
    ).to_dict()
    risk["signal_ref"] = clean_text(signal_value.get("artifact_run_id") or artifact_run_id)
    risk["risk_gate_status"] = "review_ready" if approved else "halted_for_operator_review"
    return risk


def _operator_summary(*, approved: bool, blockers: list[str]) -> str:
    if approved:
        return (
            "Paper risk gate approved one review-only paper intent. "
            "Live execution remains blocked and no execution state is changed."
        )
    return "Paper risk gate blocked intent: " + "; ".join(blockers)


def _number(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
