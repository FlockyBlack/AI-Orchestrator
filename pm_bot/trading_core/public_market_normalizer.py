from __future__ import annotations

import json
from typing import Any, Mapping, Sequence

from pm_bot.trading_core.paper_trading_loop_models import MarketSnapshot, stable_id
from pm_bot.trading_core.public_market_evidence_models import (
    FIXTURE_FALLBACK_SOURCE_TYPE,
    NORMALIZED_PUBLIC_MARKET_SNAPSHOT_CONTRACT,
    PUBLIC_GAMMA_SOURCE_TYPE,
    NormalizedPublicMarketSnapshot,
    public_market_safety_flags,
    stable_public_market_id,
)
from pm_bot.trading_core.schemas import GENERATED_AT, clean_text

SUPPORTED_SYMBOL_KEYWORDS = {
    "BTC": ("btc", "bitcoin"),
    "ETH": ("eth", "ethereum", "ether"),
    "SOL": ("sol", "solana"),
    "XRP": ("xrp", "ripple"),
}


def normalize_public_market_result(
    fetch_result: Mapping[str, Any],
    *,
    market: str = "BTC",
    query: str = "",
    slug: str = "",
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    result = dict(fetch_result or {})
    payload = result.get("data")
    source_name = clean_text(result.get("source_name"))
    source_type = clean_text(result.get("source_type"))
    network_used = result.get("network_used") is True
    candidates = _extract_market_candidates(payload)
    if not candidates:
        raise ValueError("public Gamma payload did not contain any market rows")

    market_symbol = clean_text(market).upper() or "BTC"
    selected = _select_candidate(candidates, market=market_symbol, query=query, slug=slug)
    market_payload = dict(selected["market"])
    event_payload = dict(selected.get("event", {}))
    selected_reason = _selected_reason(
        market=market_symbol,
        query=query,
        slug=slug,
        source_type=source_type,
        score=int(selected.get("score", 0)),
    )
    market_snapshot, selected_market, event_summary, comparison_available = _to_market_snapshot(
        market_payload,
        event_payload=event_payload,
        market_symbol=market_symbol,
        source_name=source_name,
        source_type=source_type,
        selected_market_reason=selected_reason,
        network_used=network_used,
        generated_at=generated_at,
    )
    normalized = NormalizedPublicMarketSnapshot(
        market_symbol=market_symbol,
        source_name=source_name,
        source_type=source_type,
        selected_market_reason=selected_reason,
        normalized_market_count=len(candidates),
        market_snapshot=market_snapshot,
        selected_market=selected_market,
        event_summary=event_summary,
        comparison_price_available=comparison_available,
        generated_at=generated_at,
    ).to_dict()
    if normalized.get("contract_version") != NORMALIZED_PUBLIC_MARKET_SNAPSHOT_CONTRACT:
        raise ValueError("normalized public market snapshot contract mismatch")
    return normalized


def summarize_public_market_candidates(payload: Any) -> dict[str, Any]:
    candidates = _extract_market_candidates(payload)
    return {
        "event_count": _count_events(payload),
        "market_count": len(candidates),
        "candidate_slugs": [
            clean_text(dict(row.get("market", {})).get("slug"))
            for row in candidates[:10]
            if clean_text(dict(row.get("market", {})).get("slug"))
        ],
        **public_market_safety_flags(network_used=False),
    }


def _to_market_snapshot(
    market_payload: Mapping[str, Any],
    *,
    event_payload: Mapping[str, Any],
    market_symbol: str,
    source_name: str,
    source_type: str,
    selected_market_reason: str,
    network_used: bool,
    generated_at: str,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], bool]:
    market_value = dict(market_payload)
    event_value = dict(event_payload)
    outcomes = _outcome_labels(market_value)
    outcome_prices = _outcome_prices(market_value)
    token_ids = _token_ids(market_value)
    if len(outcomes) < 2:
        outcomes = ("Yes", "No")
    primary_price = _first_number(
        _list_item(outcome_prices, 0),
        market_value.get("lastPrice"),
        market_value.get("last_price"),
        market_value.get("bestBid"),
        market_value.get("bestAsk"),
    )
    if primary_price is None:
        raise ValueError("selected public Gamma market has no primary outcome price")
    comparison_price = _first_number(
        market_value.get("previousObservedPrice"),
        market_value.get("previous_observed_price"),
        market_value.get("previousPrice"),
        market_value.get("previous_price"),
    )
    comparison_available = comparison_price is not None
    if comparison_price is None:
        comparison_price = primary_price
    market_id = _first_text(market_value.get("market_id"), market_value.get("id"), market_value.get("questionID"))
    market_slug = _first_text(market_value.get("market_slug"), market_value.get("slug"))
    question = _first_text(market_value.get("question"), market_value.get("title"), market_value.get("name"))
    if not market_id:
        market_id = stable_public_market_id("public-market-054", {"question": question, "slug": market_slug})
    if not market_slug:
        market_slug = f"{market_symbol.lower()}-public-market-054"
    snapshot = MarketSnapshot(
        artifact_run_id="pending-public-market-paper-loop-054",
        market_symbol=market_symbol,
        normalized_market_ref=f"{market_id}:{market_slug}",
        market_id=market_id,
        market_slug=market_slug,
        question=question or "Public Gamma market",
        primary_outcome=clean_text(_list_item(outcomes, 0) or "Yes"),
        secondary_outcome=clean_text(_list_item(outcomes, 1) or "No"),
        observed_price=float(primary_price),
        previous_observed_price=float(comparison_price),
        best_bid=_first_number(market_value.get("bestBid"), market_value.get("best_bid")),
        best_ask=_first_number(market_value.get("bestAsk"), market_value.get("best_ask")),
        spread=_first_number(market_value.get("spread")),
        liquidity=_first_number(market_value.get("liquidity"), market_value.get("liquidityNum")),
        fixture_source=source_name,
        fixture_mode=source_type == FIXTURE_FALLBACK_SOURCE_TYPE,
        generated_at=generated_at,
    ).to_dict()
    snapshot.update(
        {
            "snapshot_id": stable_id(
                "public-market-paper-loop-market-snapshot-054",
                {
                    "market_id": market_id,
                    "market_slug": market_slug,
                    "observed_price": primary_price,
                    "previous_observed_price": comparison_price,
                    "generated_at": generated_at,
                },
            ),
            "source_payload_kind": "public_gamma_event_market"
            if source_type == PUBLIC_GAMMA_SOURCE_TYPE
            else "public_gamma_fixture_fallback",
            "market_data_source": source_name,
            "source_name": source_name,
            "source_type": source_type,
            "public_gamma_read_only": source_type == PUBLIC_GAMMA_SOURCE_TYPE,
            "fixture_fallback": source_type == FIXTURE_FALLBACK_SOURCE_TYPE,
            "network_used": network_used,
            "external_api_calls_performed": network_used,
            "event_id": clean_text(event_value.get("id")),
            "event_slug": clean_text(event_value.get("slug")),
            "event_title": clean_text(event_value.get("title") or event_value.get("name")),
            "active": _bool_value(market_value.get("active"), event_value.get("active")),
            "closed": _bool_value(market_value.get("closed"), event_value.get("closed")),
            "outcome_labels": list(outcomes),
            "outcome_prices": list(outcome_prices),
            "public_market_token_ids": list(token_ids),
            "token_ids_are_market_metadata_only": True,
            "volume": _first_number(market_value.get("volume"), market_value.get("volumeNum")),
            "end_date": _first_text(market_value.get("endDate"), market_value.get("end_date")),
            "selected_market_reason": selected_market_reason,
            "comparison_price_available": comparison_available,
            "comparison_price_basis": "public_market_field"
            if comparison_available
            else "not_available_neutral_same_as_observed_for_no_signal",
            "read_only_market_data": True,
        }
    )
    selected_market = {
        "market_id": market_id,
        "market_slug": market_slug,
        "question": question,
        "event_id": clean_text(event_value.get("id")),
        "event_slug": clean_text(event_value.get("slug")),
        "event_title": clean_text(event_value.get("title") or event_value.get("name")),
        "active": snapshot["active"],
        "closed": snapshot["closed"],
        "outcome_labels": list(outcomes),
        "outcome_prices": list(outcome_prices),
        "public_market_token_ids": list(token_ids),
        "token_ids_are_market_metadata_only": True,
        "volume": snapshot.get("volume"),
        "liquidity": snapshot.get("liquidity"),
        "end_date": snapshot.get("end_date"),
        "read_only_market_data": True,
    }
    event_summary = {
        "event_id": clean_text(event_value.get("id")),
        "event_slug": clean_text(event_value.get("slug")),
        "event_title": clean_text(event_value.get("title") or event_value.get("name")),
        "active": _bool_value(event_value.get("active")),
        "closed": _bool_value(event_value.get("closed")),
    }
    return snapshot, selected_market, event_summary, comparison_available


def _extract_market_candidates(payload: Any) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if isinstance(payload, list):
        for index, item in enumerate(payload):
            if isinstance(item, Mapping):
                rows.extend(_candidates_from_mapping(item, index=index))
    elif isinstance(payload, Mapping):
        for key in ("events", "data", "results"):
            nested = payload.get(key)
            if isinstance(nested, list):
                for index, item in enumerate(nested):
                    if isinstance(item, Mapping):
                        rows.extend(_candidates_from_mapping(item, index=index))
                return rows
        rows.extend(_candidates_from_mapping(payload, index=0))
    return rows


def _candidates_from_mapping(value: Mapping[str, Any], *, index: int) -> list[dict[str, Any]]:
    row = dict(value)
    markets = row.get("markets")
    if isinstance(markets, list):
        return [
            {"event": row, "market": dict(market), "index": index + offset}
            for offset, market in enumerate(markets)
            if isinstance(market, Mapping)
        ]
    if any(clean_text(row.get(key)) for key in ("question", "slug", "title")):
        return [{"event": {}, "market": row, "index": index}]
    return []


def _select_candidate(
    candidates: Sequence[Mapping[str, Any]],
    *,
    market: str,
    query: str,
    slug: str,
) -> dict[str, Any]:
    scored: list[dict[str, Any]] = []
    for candidate in candidates:
        value = dict(candidate)
        value["score"] = _candidate_score(value, market=market, query=query, slug=slug)
        scored.append(value)
    scored.sort(key=lambda row: (-int(row.get("score", 0)), int(row.get("index", 0))))
    selected = scored[0]
    if clean_text(slug) and int(selected.get("score", 0)) < 100:
        raise ValueError(f"no public Gamma market matched slug {slug}")
    return selected


def _candidate_score(candidate: Mapping[str, Any], *, market: str, query: str, slug: str) -> int:
    market_value = dict(candidate.get("market", {}))
    event_value = dict(candidate.get("event", {}))
    haystack = " ".join(
        clean_text(item).lower()
        for item in (
            market_value.get("question"),
            market_value.get("title"),
            market_value.get("name"),
            market_value.get("slug"),
            event_value.get("title"),
            event_value.get("name"),
            event_value.get("slug"),
            json.dumps(market_value.get("tags", ""), sort_keys=True, default=str),
        )
    )
    score = 0
    requested_slug = clean_text(slug).lower()
    if requested_slug and requested_slug in haystack:
        score += 120
    for keyword in SUPPORTED_SYMBOL_KEYWORDS.get(clean_text(market).upper(), (clean_text(market).lower(),)):
        if keyword and keyword in haystack:
            score += 50
    for term in clean_text(query).lower().split():
        if term and term in haystack:
            score += 10
    if _bool_value(market_value.get("active"), event_value.get("active")) is True:
        score += 5
    if _bool_value(market_value.get("closed"), event_value.get("closed")) is False:
        score += 5
    if _outcome_prices(market_value):
        score += 5
    return score


def _selected_reason(*, market: str, query: str, slug: str, source_type: str, score: int) -> str:
    if source_type == FIXTURE_FALLBACK_SOURCE_TYPE:
        return f"selected deterministic fixture fallback market for {market}"
    if clean_text(slug):
        return f"selected public Gamma market by slug {clean_text(slug)}"
    if clean_text(query):
        return f"selected public Gamma market for {market} using query {clean_text(query)} with score {score}"
    return f"selected public Gamma market for {market} using active open market discovery with score {score}"


def _outcome_labels(market: Mapping[str, Any]) -> tuple[str, ...]:
    raw = _parse_list(market.get("outcomes") or market.get("outcome"))
    labels: list[str] = []
    for item in raw:
        if isinstance(item, Mapping):
            labels.append(_first_text(item.get("name"), item.get("label"), item.get("outcome")))
        else:
            labels.append(clean_text(item))
    return tuple(label for label in labels if label)


def _outcome_prices(market: Mapping[str, Any]) -> tuple[float | None, ...]:
    raw = _parse_list(market.get("outcomePrices") or market.get("outcome_prices"))
    if not raw:
        outcomes = _parse_list(market.get("outcomes"))
        if outcomes and all(isinstance(item, Mapping) for item in outcomes):
            raw = [
                dict(item).get("price") or dict(item).get("lastPrice") or dict(item).get("last_price")
                for item in outcomes
            ]
    return tuple(_number_or_none(item) for item in raw)


def _token_ids(market: Mapping[str, Any]) -> tuple[str, ...]:
    raw = _parse_list(market.get("clobTokenIds") or market.get("tokenIds") or market.get("token_ids"))
    token_ids: list[str] = []
    for item in raw:
        if isinstance(item, Mapping):
            token_ids.append(_first_text(item.get("token_id"), item.get("id")))
        else:
            token_ids.append(clean_text(item))
    return tuple(item for item in token_ids if item)


def _parse_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, str):
        parsed = _try_json(value)
        if isinstance(parsed, list):
            return parsed
        text = clean_text(value)
        return [text] if text else []
    if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray)):
        return list(value)
    return [value]


def _try_json(value: str) -> Any:
    try:
        return json.loads(value)
    except (TypeError, ValueError):
        return None


def _list_item(value: Sequence[Any], index: int) -> Any:
    if index < 0 or index >= len(value):
        return None
    return value[index]


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


def _first_text(*values: Any) -> str:
    for value in values:
        text = clean_text(value)
        if text:
            return text
    return ""


def _bool_value(*values: Any) -> bool:
    for value in values:
        if isinstance(value, bool):
            return value
        text = clean_text(value).lower()
        if text in {"true", "1", "yes", "open", "active"}:
            return True
        if text in {"false", "0", "no", "closed", "inactive"}:
            return False
    return False


def _count_events(payload: Any) -> int:
    if isinstance(payload, list):
        return len([row for row in payload if isinstance(row, Mapping) and isinstance(row.get("markets"), list)])
    if isinstance(payload, Mapping) and isinstance(payload.get("events"), list):
        return len(payload.get("events", []))
    return 0
