from __future__ import annotations

from typing import Any, Mapping

from pm_bot.trading_core.paper_trading_loop_models import PaperOrderIntent, stable_id
from pm_bot.trading_core.schemas import GENERATED_AT, clean_text


def build_paper_order_intent(
    *,
    signal: Mapping[str, Any],
    risk: Mapping[str, Any],
    artifact_run_id: str,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any] | None:
    signal_value = dict(signal or {})
    risk_value = dict(risk or {})
    if risk_value.get("approved_for_paper_intent") is not True:
        return None
    ref = stable_id(
        "paper-intent-ref-053",
        {
            "artifact_run_id": artifact_run_id,
            "strategy": signal_value.get("strategy_name"),
            "market": signal_value.get("market_symbol"),
            "outcome": signal_value.get("outcome"),
            "limit_price": signal_value.get("limit_price"),
            "size": signal_value.get("size"),
        },
    )
    intent = PaperOrderIntent(
        artifact_run_id=artifact_run_id,
        paper_intent_ref=ref,
        strategy_name=clean_text(signal_value.get("strategy_name")),
        market_symbol=clean_text(signal_value.get("market_symbol")).upper(),
        normalized_market_ref=clean_text(signal_value.get("normalized_market_ref")),
        market=clean_text(signal_value.get("market_symbol")).upper(),
        outcome=clean_text(signal_value.get("outcome")),
        side=clean_text(signal_value.get("side") or "paper_track_outcome"),
        limit_price=float(signal_value.get("limit_price")),
        size=float(signal_value.get("size")),
        notional=float(signal_value.get("notional")),
        confidence=float(signal_value.get("confidence")),
        signal_reason=clean_text(signal_value.get("reason")),
        risk_decision=clean_text(risk_value.get("risk_decision")),
        generated_at=generated_at,
    ).to_dict()
    intent["risk_operator_summary"] = clean_text(risk_value.get("operator_summary"))
    return intent
