from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from pm_bot.trading_core.paper_trading_loop_models import MarketSnapshot, stable_id
from pm_bot.trading_core.polymarket_public_market_data import (
    load_polymarket_public_market_snapshot,
)
from pm_bot.trading_core.schemas import GENERATED_AT, clean_text, load_json_object, normalize_path


class PaperMockMarketClient:
    """Read-only fixture client for one operator-triggered paper loop pass."""

    def __init__(self, *, fixture_path: str | Path | None = None) -> None:
        self.fixture_path = Path(fixture_path) if fixture_path else None

    def load_market_snapshot(
        self,
        *,
        market: str,
        artifact_run_id: str,
        generated_at: str = GENERATED_AT,
    ) -> dict[str, Any]:
        market_symbol = clean_text(market).upper() or "BTC"
        if self.fixture_path:
            payload = load_json_object(self.fixture_path, label="paper trading loop fixture")
            return self._snapshot_from_fixture_payload(
                payload,
                market_symbol=market_symbol,
                artifact_run_id=artifact_run_id,
                fixture_source=normalize_path(self.fixture_path),
                generated_at=generated_at,
            )
        if market_symbol != "BTC":
            raise ValueError("paper trading loop currently supports the BTC fixture market")
        public_snapshot = load_polymarket_public_market_snapshot(
            market=market_symbol,
            network_check=False,
            fetched_at=generated_at,
            generated_at=generated_at,
        )
        normalized = dict(public_snapshot["normalized_market"])
        connector_payload = dict(public_snapshot["btc_connector_fixture_payload"])
        return self._snapshot_from_normalized_fixture(
            normalized_market=normalized,
            connector_payload=connector_payload,
            market_symbol=market_symbol,
            artifact_run_id=artifact_run_id,
            fixture_source=clean_text(public_snapshot.get("source")),
            generated_at=generated_at,
        )

    def _snapshot_from_fixture_payload(
        self,
        payload: Mapping[str, Any],
        *,
        market_symbol: str,
        artifact_run_id: str,
        fixture_source: str,
        generated_at: str,
    ) -> dict[str, Any]:
        value = dict(payload)
        normalized = dict(value.get("normalized_market", {})) if isinstance(value.get("normalized_market"), Mapping) else {}
        connector_payload = (
            dict(value.get("btc_connector_fixture_payload", {}))
            if isinstance(value.get("btc_connector_fixture_payload"), Mapping)
            else {}
        )
        if normalized:
            return self._snapshot_from_normalized_fixture(
                normalized_market=normalized,
                connector_payload=connector_payload or value,
                market_symbol=market_symbol,
                artifact_run_id=artifact_run_id,
                fixture_source=fixture_source,
                generated_at=generated_at,
                previous_price_override=_number_or_none(value.get("previous_observed_price")),
                observed_price_override=_number_or_none(value.get("observed_price")),
            )
        return self._snapshot_from_flat_fixture(
            value,
            market_symbol=market_symbol,
            artifact_run_id=artifact_run_id,
            fixture_source=fixture_source,
            generated_at=generated_at,
        )

    def _snapshot_from_normalized_fixture(
        self,
        *,
        normalized_market: Mapping[str, Any],
        connector_payload: Mapping[str, Any],
        market_symbol: str,
        artifact_run_id: str,
        fixture_source: str,
        generated_at: str,
        previous_price_override: float | None = None,
        observed_price_override: float | None = None,
    ) -> dict[str, Any]:
        market = dict(normalized_market)
        payload = dict(connector_payload)
        outcomes = _mapping_rows(payload.get("outcomes"))
        if not outcomes:
            outcomes = [
                {"name": name, "price": price}
                for name, price in zip(
                    list(market.get("outcomes", [])),
                    list(market.get("outcome_prices", [])),
                )
            ]
        primary = dict(outcomes[0]) if outcomes else {}
        secondary = dict(outcomes[1]) if len(outcomes) > 1 else {}
        observed_price = _first_number(
            observed_price_override,
            primary.get("lastPrice"),
            primary.get("last_price"),
            primary.get("price"),
            _first_list_number(market.get("outcome_prices"), 0),
        )
        if observed_price is None:
            raise ValueError("paper trading fixture must provide a primary observed price")
        previous_price = _first_number(
            previous_price_override,
            payload.get("previous_observed_price"),
            market.get("previous_observed_price"),
            round(observed_price - 0.03, 6),
        )
        snapshot = MarketSnapshot(
            artifact_run_id=artifact_run_id,
            market_symbol=market_symbol,
            normalized_market_ref=_normalized_ref(market),
            market_id=clean_text(market.get("market_id") or payload.get("id")),
            market_slug=clean_text(market.get("slug") or payload.get("slug")),
            question=clean_text(market.get("question") or payload.get("question")),
            primary_outcome=clean_text(primary.get("name") or _first_list_text(market.get("outcomes"), 0) or "Yes"),
            secondary_outcome=clean_text(
                secondary.get("name") or _first_list_text(market.get("outcomes"), 1) or "No"
            ),
            observed_price=float(observed_price),
            previous_observed_price=float(previous_price if previous_price is not None else observed_price),
            best_bid=_first_number(primary.get("bestBid"), primary.get("best_bid"), payload.get("bestBid")),
            best_ask=_first_number(primary.get("bestAsk"), primary.get("best_ask"), payload.get("bestAsk")),
            spread=_first_number(primary.get("spread"), payload.get("spread")),
            liquidity=_first_number(primary.get("liquidity"), payload.get("liquidity"), market.get("liquidity")),
            fixture_source=clean_text(fixture_source),
            generated_at=generated_at,
        ).to_dict()
        snapshot["snapshot_id"] = stable_id(
            "paper-trading-loop-market-snapshot-053",
            {
                "artifact_run_id": artifact_run_id,
                "market_id": snapshot.get("market_id"),
                "observed_price": snapshot.get("observed_price"),
                "previous_observed_price": snapshot.get("previous_observed_price"),
            },
        )
        snapshot["source_payload_kind"] = "normalized_polymarket_fixture"
        return snapshot

    def _snapshot_from_flat_fixture(
        self,
        payload: Mapping[str, Any],
        *,
        market_symbol: str,
        artifact_run_id: str,
        fixture_source: str,
        generated_at: str,
    ) -> dict[str, Any]:
        value = dict(payload)
        outcomes = _mapping_rows(value.get("outcomes"))
        primary = dict(outcomes[0]) if outcomes else {}
        secondary = dict(outcomes[1]) if len(outcomes) > 1 else {}
        observed_price = _first_number(
            value.get("observed_price"),
            value.get("lastPrice"),
            value.get("last_price"),
            primary.get("price"),
        )
        if observed_price is None:
            raise ValueError("paper trading fixture must provide observed_price or outcome price")
        previous_price = _first_number(value.get("previous_observed_price"), observed_price)
        market_id = clean_text(value.get("market_id") or value.get("id")) or stable_id(
            "paper-fixture-market-053",
            {"market_symbol": market_symbol, "question": value.get("question")},
        )
        market_slug = clean_text(value.get("market_slug") or value.get("slug")) or f"{market_symbol.lower()}-paper-fixture-053"
        snapshot = MarketSnapshot(
            artifact_run_id=artifact_run_id,
            market_symbol=market_symbol,
            normalized_market_ref=f"{market_id}:{market_slug}",
            market_id=market_id,
            market_slug=market_slug,
            question=clean_text(value.get("question") or "Paper trading loop fixture"),
            primary_outcome=clean_text(primary.get("name") or value.get("primary_outcome") or "Yes"),
            secondary_outcome=clean_text(secondary.get("name") or value.get("secondary_outcome") or "No"),
            observed_price=float(observed_price),
            previous_observed_price=float(previous_price if previous_price is not None else observed_price),
            best_bid=_first_number(value.get("best_bid"), value.get("bestBid"), primary.get("bestBid")),
            best_ask=_first_number(value.get("best_ask"), value.get("bestAsk"), primary.get("bestAsk")),
            spread=_first_number(value.get("spread"), primary.get("spread")),
            liquidity=_first_number(value.get("liquidity"), primary.get("liquidity")),
            fixture_source=clean_text(fixture_source),
            generated_at=generated_at,
        ).to_dict()
        snapshot["snapshot_id"] = stable_id(
            "paper-trading-loop-market-snapshot-053",
            {
                "artifact_run_id": artifact_run_id,
                "market_id": snapshot.get("market_id"),
                "observed_price": snapshot.get("observed_price"),
                "previous_observed_price": snapshot.get("previous_observed_price"),
            },
        )
        snapshot["source_payload_kind"] = "operator_supplied_flat_fixture"
        return snapshot


def _normalized_ref(market: Mapping[str, Any]) -> str:
    market_id = clean_text(market.get("market_id"))
    slug = clean_text(market.get("slug"))
    return f"{market_id}:{slug}" if market_id or slug else "not_available"


def _mapping_rows(value: Any) -> list[Mapping[str, Any]]:
    if not isinstance(value, list):
        return []
    return [row for row in value if isinstance(row, Mapping)]


def _first_number(*values: Any) -> float | None:
    for value in values:
        number = _number_or_none(value)
        if number is not None:
            return number
    return None


def _number_or_none(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        return round(float(value), 6)
    except (TypeError, ValueError):
        return None


def _first_list_number(value: Any, index: int) -> float | None:
    if not isinstance(value, list) or index >= len(value):
        return None
    return _number_or_none(value[index])


def _first_list_text(value: Any, index: int) -> str:
    if not isinstance(value, list) or index >= len(value):
        return ""
    return clean_text(value[index])
