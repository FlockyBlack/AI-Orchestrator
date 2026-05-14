from __future__ import annotations

from typing import Any, Mapping

from pm_bot.trading_core.polymarket_market_models import (
    DONOR_REFERENCE_COMMIT,
    DONOR_REFERENCE_LICENSE,
    DONOR_REFERENCE_REPOSITORY,
    normalize_polymarket_market_payload,
    summarize_normalized_polymarket_market,
)
from pm_bot.trading_core.schemas import GENERATED_AT, clean_text

POLYMARKET_PUBLIC_MARKET_DATA_SNAPSHOT_CONTRACT = (
    "pmbot_polymarket_public_market_data_snapshot.v1"
)

DEFAULT_FIXTURE_SOURCE = "local_polymarket_agents_reference_fixture_052"


def load_polymarket_public_market_snapshot(
    *,
    market: str = "BTC",
    network_check: bool = False,
    fetched_at: str = GENERATED_AT,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    market_symbol = clean_text(market).upper() or "BTC"
    if market_symbol != "BTC":
        raise ValueError("paper canary drill currently supports only the BTC fixture market")

    raw_fixture = build_btc_polymarket_style_fixture_payload(fetched_at=fetched_at)
    normalized = normalize_polymarket_market_payload(
        raw_fixture,
        source=DEFAULT_FIXTURE_SOURCE,
        fetched_at=fetched_at,
        fixture_mode=True,
        generated_at=generated_at,
    )
    summary = summarize_normalized_polymarket_market(normalized)
    return {
        "contract_version": POLYMARKET_PUBLIC_MARKET_DATA_SNAPSHOT_CONTRACT,
        "snapshot_status": "fixture_snapshot_ready",
        "market": market_symbol,
        "normalized_market": normalized,
        "normalized_market_summary": summary,
        "btc_connector_fixture_payload": to_btc_connector_fixture_payload(
            normalized,
            fetched_at=fetched_at,
        ),
        "source": DEFAULT_FIXTURE_SOURCE,
        "source_url": "",
        "fetched_at": fetched_at,
        "fixture_mode": True,
        "network_check_requested": network_check is True,
        "network_check_status": "not_implemented_fixture_only" if network_check else "not_requested",
        "network_used": False,
        "external_api_calls_performed": False,
        "authenticated_polymarket_enabled": False,
        "live_connector_enabled": False,
        "order_submission_enabled": False,
        "wallet_signing_enabled": False,
        "signing_enabled": False,
        "signed_payload_generation_enabled": False,
        "signed_order_generation_enabled": False,
        "live_execution_approved": False,
        "canary_executable_now": False,
        "real_execution_available": False,
        "allowed_for_live": False,
        "donor_reference": {
            "repository": DONOR_REFERENCE_REPOSITORY,
            "commit": DONOR_REFERENCE_COMMIT,
            "license": DONOR_REFERENCE_LICENSE,
            "usage": "field-shape and architecture reference only; no live execution code imported",
        },
        "generated_at": generated_at,
    }


def build_btc_polymarket_style_fixture_payload(*, fetched_at: str = GENERATED_AT) -> dict[str, Any]:
    return {
        "id": "pm-agents-052-btc-fixture-market",
        "conditionId": "pm-agents-052-btc-fixture-condition",
        "questionID": "pm-agents-052-btc-fixture-question",
        "question": "Will Bitcoin close above the fixture threshold on the paper canary review date?",
        "slug": "btc-paper-canary-fixture-052",
        "description": (
            "Deterministic local Polymarket-style BTC fixture adapted from public Gamma metadata "
            "field patterns for a PMBOT paper canary drill."
        ),
        "active": True,
        "closed": False,
        "archived": False,
        "restricted": False,
        "funded": True,
        "acceptingOrders": True,
        "enableOrderBook": True,
        "endDate": "2026-05-31T00:00:00Z",
        "liquidity": "2500.00",
        "volume": "12000.00",
        "volume24hr": "321.00",
        "spread": "0.02",
        "outcomes": '["Yes", "No"]',
        "outcomePrices": '["0.52", "0.48"]',
        "clobTokenIds": '["pm-agents-052-btc-yes-token", "pm-agents-052-btc-no-token"]',
        "orderMinSize": "5",
        "orderPriceMinTickSize": "0.01",
        "tags": [{"id": "btc", "label": "BTC", "slug": "btc"}],
        "events": [
            {
                "id": "pm-agents-052-btc-event",
                "ticker": "BTC",
                "slug": "btc-paper-canary-fixture-event-052",
                "title": "BTC paper canary fixture event",
                "active": True,
                "closed": False,
                "archived": False,
                "restricted": False,
                "enableOrderBook": True,
            }
        ],
        "fetched_at": fetched_at,
        "observed_at": fetched_at,
    }


def to_btc_connector_fixture_payload(
    normalized_market: Mapping[str, Any],
    *,
    fetched_at: str = GENERATED_AT,
) -> dict[str, Any]:
    market = dict(normalized_market)
    outcomes = list(market.get("outcomes", []))
    prices = list(market.get("outcome_prices", []))
    token_ids = list(market.get("clob_token_ids", []))
    outcome_rows: list[dict[str, Any]] = []
    for index, outcome in enumerate(outcomes):
        price = prices[index] if index < len(prices) else None
        token_id = token_ids[index] if index < len(token_ids) else f"pm-agents-052-outcome-{index + 1}"
        best_bid = round(float(price) - 0.01, 6) if isinstance(price, (int, float)) else None
        best_ask = round(float(price) + 0.01, 6) if isinstance(price, (int, float)) else None
        outcome_rows.append(
            {
                "id": clean_text(token_id),
                "name": clean_text(outcome),
                "price": price,
                "bestBid": best_bid,
                "bestAsk": best_ask,
                "lastPrice": price,
                "liquidity": market.get("liquidity"),
            }
        )
    return {
        "id": clean_text(market.get("market_id")),
        "conditionId": clean_text(market.get("condition_id")),
        "slug": clean_text(market.get("slug")),
        "question": clean_text(market.get("question")),
        "description": clean_text(market.get("description")),
        "tags": ["BTC", "Bitcoin", "paper-canary-fixture"],
        "active": market.get("active") is True,
        "closed": market.get("closed") is True,
        "archived": market.get("archived") is True,
        "resolved": False,
        "funded": market.get("funded") is True,
        "acceptingOrders": market.get("accepting_orders") is True,
        "enableOrderBook": market.get("enable_order_book") is True,
        "fetched_at": fetched_at,
        "observed_at": fetched_at,
        "outcomes": outcome_rows,
        "outcomePrices": list(prices),
        "clobTokenIds": list(token_ids),
        "bestBid": outcome_rows[0].get("bestBid") if outcome_rows else None,
        "bestAsk": outcome_rows[0].get("bestAsk") if outcome_rows else None,
        "lastPrice": outcome_rows[0].get("lastPrice") if outcome_rows else None,
        "spread": market.get("spread"),
        "liquidity": market.get("liquidity"),
    }
