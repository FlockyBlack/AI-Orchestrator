from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Mapping

from pm_bot.trading_core.paper_trading_loop_models import StrategySignal
from pm_bot.trading_core.schemas import GENERATED_AT, clean_text


class BasePaperStrategy(ABC):
    name = "base-paper-strategy"

    @abstractmethod
    def evaluate(
        self,
        snapshot: Mapping[str, Any],
        *,
        artifact_run_id: str,
        generated_at: str = GENERATED_AT,
    ) -> StrategySignal | None:
        raise NotImplementedError

    def no_signal_reason(self, snapshot: Mapping[str, Any]) -> str:
        return "strategy produced no paper signal for this fixture snapshot"


class TinyMomentumPaperStrategy(BasePaperStrategy):
    name = "tiny-momentum"

    def __init__(
        self,
        *,
        min_price_delta: float = 0.01,
        default_size: float = 1.0,
    ) -> None:
        self.min_price_delta = float(min_price_delta)
        self.default_size = float(default_size)

    def evaluate(
        self,
        snapshot: Mapping[str, Any],
        *,
        artifact_run_id: str,
        generated_at: str = GENERATED_AT,
    ) -> StrategySignal | None:
        observed_price = _float_or_none(snapshot.get("observed_price"))
        previous_price = _float_or_none(snapshot.get("previous_observed_price"))
        if observed_price is None or previous_price is None:
            return None
        price_delta = round(observed_price - previous_price, 6)
        if price_delta < self.min_price_delta:
            return None
        if observed_price <= 0 or observed_price >= 1:
            return None
        size = self.default_size
        notional = round(observed_price * size, 6)
        confidence = round(min(0.95, 0.6 + min(price_delta, 0.05) * 4), 6)
        return StrategySignal(
            artifact_run_id=artifact_run_id,
            strategy_name=self.name,
            market_symbol=clean_text(snapshot.get("market_symbol")).upper(),
            normalized_market_ref=clean_text(snapshot.get("normalized_market_ref")),
            outcome=clean_text(snapshot.get("primary_outcome") or "Yes"),
            side="paper_track_outcome",
            limit_price=observed_price,
            size=size,
            notional=notional,
            confidence=confidence,
            reason=(
                f"Fixture primary outcome price moved by {price_delta:.4f}; "
                "one-shot paper review signal created for risk gating."
            ),
            price_delta=price_delta,
            generated_at=generated_at,
        )

    def no_signal_reason(self, snapshot: Mapping[str, Any]) -> str:
        observed_price = _float_or_none(snapshot.get("observed_price"))
        previous_price = _float_or_none(snapshot.get("previous_observed_price"))
        if observed_price is None or previous_price is None:
            return "fixture snapshot has no comparable primary outcome prices"
        price_delta = round(observed_price - previous_price, 6)
        return (
            f"Fixture primary outcome price delta {price_delta:.4f} is below "
            f"tiny-momentum threshold {self.min_price_delta:.4f}."
        )


def build_paper_strategy(strategy: str) -> BasePaperStrategy:
    name = clean_text(strategy).lower() or TinyMomentumPaperStrategy.name
    if name == TinyMomentumPaperStrategy.name:
        return TinyMomentumPaperStrategy()
    raise ValueError(f"unsupported paper strategy: {strategy}")


def _float_or_none(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
