from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Callable, Mapping
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from pm_bot.trading_core.public_market_evidence_models import (
    FIXTURE_FALLBACK_SOURCE_NAME,
    FIXTURE_FALLBACK_SOURCE_TYPE,
    PUBLIC_GAMMA_SOURCE_NAME,
    PUBLIC_GAMMA_SOURCE_TYPE,
    PublicGammaRequestEvidence,
    PublicGammaResponseEvidence,
    hash_response_payload,
    sanitize_query,
)
from pm_bot.trading_core.schemas import GENERATED_AT, clean_text, load_json_object

PMBOT_GAMMA_BASE_URL_ENV = "PMBOT_GAMMA_BASE_URL"
DEFAULT_GAMMA_BASE_URL = "https://gamma-api.polymarket.com"
DEFAULT_TIMEOUT_SECONDS = 10.0
READ_ONLY_METHOD = "GET"

Transport = Callable[[str, float], tuple[int | None, Any]]


class PublicGammaFetchError(RuntimeError):
    def __init__(self, message: str, *, error_payload: Mapping[str, Any]) -> None:
        super().__init__(message)
        self.error_payload = dict(error_payload)


class PublicGammaMarketClient:
    """Read-only Gamma client for public market discovery."""

    def __init__(
        self,
        *,
        base_url: str | None = None,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
        transport: Transport | None = None,
    ) -> None:
        configured_base_url = clean_text(base_url) or clean_text(os.environ.get(PMBOT_GAMMA_BASE_URL_ENV))
        self.base_url = (configured_base_url or DEFAULT_GAMMA_BASE_URL).rstrip("/")
        self.timeout_seconds = float(timeout_seconds or DEFAULT_TIMEOUT_SECONDS)
        self._transport = transport

    def fetch_active_events(
        self,
        *,
        query: str = "",
        tag_id: str = "",
        limit: int = 20,
        timeout_seconds: float | None = None,
        generated_at: str = GENERATED_AT,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {
            "active": "true",
            "closed": "false",
            "limit": _safe_limit(limit),
        }
        if clean_text(query):
            params["q"] = clean_text(query)
        if clean_text(tag_id):
            params["tag_id"] = clean_text(tag_id)
        return self._fetch_public_json(
            endpoint_path="/events",
            query=params,
            timeout_seconds=timeout_seconds,
            generated_at=generated_at,
        )

    def fetch_markets(
        self,
        *,
        query: str = "",
        slug: str = "",
        tag_id: str = "",
        limit: int = 20,
        timeout_seconds: float | None = None,
        generated_at: str = GENERATED_AT,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {
            "active": "true",
            "closed": "false",
            "limit": _safe_limit(limit),
        }
        if clean_text(query):
            params["q"] = clean_text(query)
        if clean_text(slug):
            params["slug"] = clean_text(slug)
        if clean_text(tag_id):
            params["tag_id"] = clean_text(tag_id)
        return self._fetch_public_json(
            endpoint_path="/markets",
            query=params,
            timeout_seconds=timeout_seconds,
            generated_at=generated_at,
        )

    def search_public_markets(
        self,
        *,
        market: str = "BTC",
        query: str = "",
        slug: str = "",
        tag_id: str = "",
        limit: int = 20,
        timeout_seconds: float | None = None,
        generated_at: str = GENERATED_AT,
    ) -> dict[str, Any]:
        search_text = clean_text(query) or clean_text(market).upper()
        if clean_text(slug):
            return self.fetch_markets(
                query=search_text,
                slug=slug,
                tag_id=tag_id,
                limit=limit,
                timeout_seconds=timeout_seconds,
                generated_at=generated_at,
            )
        return self.fetch_active_events(
            query=search_text,
            tag_id=tag_id,
            limit=limit,
            timeout_seconds=timeout_seconds,
            generated_at=generated_at,
        )

    def load_fixture_fallback(
        self,
        *,
        market: str = "BTC",
        query: str = "",
        slug: str = "",
        tag_id: str = "",
        limit: int = 20,
        fixture_path: str | Path | None = None,
        fixture_payload: Mapping[str, Any] | None = None,
        generated_at: str = GENERATED_AT,
    ) -> dict[str, Any]:
        payload = (
            dict(fixture_payload)
            if fixture_payload is not None
            else load_json_object(fixture_path, label="public Gamma fixture fallback")
            if fixture_path
            else build_default_public_gamma_fixture(market=market, generated_at=generated_at)
        )
        sanitized = sanitize_query(
            {
                "market": clean_text(market).upper() or "BTC",
                "query": clean_text(query),
                "slug": clean_text(slug),
                "tag_id": clean_text(tag_id),
                "limit": _safe_limit(limit),
                "fixture": "fallback",
            }
        )
        request = PublicGammaRequestEvidence(
            source_name=FIXTURE_FALLBACK_SOURCE_NAME,
            source_type=FIXTURE_FALLBACK_SOURCE_TYPE,
            base_url=self.base_url,
            endpoint_path="fixture_fallback",
            sanitized_query=sanitized,
            request_method=READ_ONLY_METHOD,
            request_timestamp_utc=generated_at,
            network_used=False,
            generated_at=generated_at,
        ).to_dict()
        response_hash = hash_response_payload(payload)
        response = PublicGammaResponseEvidence(
            source_name=FIXTURE_FALLBACK_SOURCE_NAME,
            source_type=FIXTURE_FALLBACK_SOURCE_TYPE,
            base_url=self.base_url,
            endpoint_path="fixture_fallback",
            response_timestamp_utc=generated_at,
            status_code=None,
            network_used=False,
            normalized_market_count=_count_markets(payload),
            raw_response_hash=response_hash,
            response_snapshot_hash=response_hash,
            selected_market_reason="deterministic fixture fallback loaded for public market paper review",
            generated_at=generated_at,
        ).to_dict()
        return {
            "source_name": FIXTURE_FALLBACK_SOURCE_NAME,
            "source_type": FIXTURE_FALLBACK_SOURCE_TYPE,
            "base_url": self.base_url,
            "endpoint_path": "fixture_fallback",
            "sanitized_query": sanitized,
            "data": payload,
            "request_evidence": request,
            "response_evidence": response,
            "network_used": False,
        }

    def _fetch_public_json(
        self,
        *,
        endpoint_path: str,
        query: Mapping[str, Any],
        timeout_seconds: float | None,
        generated_at: str,
    ) -> dict[str, Any]:
        sanitized = sanitize_query(query)
        url = _build_url(self.base_url, endpoint_path, sanitized)
        request = PublicGammaRequestEvidence(
            source_name=PUBLIC_GAMMA_SOURCE_NAME,
            source_type=PUBLIC_GAMMA_SOURCE_TYPE,
            base_url=self.base_url,
            endpoint_path=endpoint_path,
            sanitized_query=sanitized,
            request_method=READ_ONLY_METHOD,
            request_timestamp_utc=generated_at,
            network_used=True,
            generated_at=generated_at,
        ).to_dict()
        timeout = float(timeout_seconds or self.timeout_seconds)
        try:
            status_code, payload = self._transport(url, timeout) if self._transport else _default_get_json(url, timeout)
        except (HTTPError, URLError, TimeoutError, OSError, ValueError) as exc:
            raise PublicGammaFetchError(
                "public Gamma read-only fetch failed",
                error_payload={
                    "contract_version": "pmbot_public_gamma_fetch_error_054.v1",
                    "source_name": PUBLIC_GAMMA_SOURCE_NAME,
                    "source_type": PUBLIC_GAMMA_SOURCE_TYPE,
                    "base_url": self.base_url,
                    "endpoint_path": endpoint_path,
                    "sanitized_query": sanitized,
                    "request_method": READ_ONLY_METHOD,
                    "network_used": True,
                    "error_type": type(exc).__name__,
                    "message": clean_text(exc),
                    "generated_at": generated_at,
                },
            ) from exc
        response_hash = hash_response_payload(payload)
        response = PublicGammaResponseEvidence(
            source_name=PUBLIC_GAMMA_SOURCE_NAME,
            source_type=PUBLIC_GAMMA_SOURCE_TYPE,
            base_url=self.base_url,
            endpoint_path=endpoint_path,
            response_timestamp_utc=generated_at,
            status_code=status_code,
            network_used=True,
            normalized_market_count=_count_markets(payload),
            raw_response_hash=response_hash,
            response_snapshot_hash=response_hash,
            selected_market_reason="selection pending normalization",
            generated_at=generated_at,
        ).to_dict()
        return {
            "source_name": PUBLIC_GAMMA_SOURCE_NAME,
            "source_type": PUBLIC_GAMMA_SOURCE_TYPE,
            "base_url": self.base_url,
            "endpoint_path": endpoint_path,
            "sanitized_query": sanitized,
            "data": payload,
            "request_evidence": request,
            "response_evidence": response,
            "network_used": True,
        }


def build_default_public_gamma_fixture(
    *,
    market: str = "BTC",
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    symbol = clean_text(market).upper() or "BTC"
    title = _symbol_title(symbol)
    slug_symbol = symbol.lower()
    primary_price = 0.52 if symbol in {"BTC", "ETH", "SOL", "XRP"} else 0.51
    previous_price = 0.49 if symbol in {"BTC", "ETH", "SOL", "XRP"} else 0.50
    return {
        "events": [
            {
                "id": f"public-gamma-fixture-{slug_symbol}-event-054",
                "slug": f"{slug_symbol}-public-gamma-fixture-event-054",
                "title": f"{title} public Gamma fixture event",
                "active": True,
                "closed": False,
                "markets": [
                    {
                        "id": f"public-gamma-fixture-{slug_symbol}-market-054",
                        "conditionId": f"public-gamma-fixture-{slug_symbol}-condition-054",
                        "question": f"Will {title} close above the public fixture threshold?",
                        "slug": f"{slug_symbol}-public-gamma-fixture-market-054",
                        "active": True,
                        "closed": False,
                        "archived": False,
                        "restricted": False,
                        "endDate": "2026-05-31T00:00:00Z",
                        "liquidity": "2500.00",
                        "volume": "12000.00",
                        "spread": "0.02",
                        "outcomes": json.dumps(["Yes", "No"]),
                        "outcomePrices": json.dumps([primary_price, round(1.0 - primary_price, 6)]),
                        "previousObservedPrice": previous_price,
                        "clobTokenIds": json.dumps(
                            [
                                f"public-gamma-fixture-{slug_symbol}-yes-token",
                                f"public-gamma-fixture-{slug_symbol}-no-token",
                            ]
                        ),
                        "tags": [{"id": slug_symbol, "label": symbol, "slug": slug_symbol}],
                    }
                ],
            }
        ],
        "fixture_source": FIXTURE_FALLBACK_SOURCE_NAME,
        "generated_at": generated_at,
    }


def _default_get_json(url: str, timeout_seconds: float) -> tuple[int | None, Any]:
    request = Request(url, method=READ_ONLY_METHOD, headers={"User-Agent": "PMBOT-public-gamma-read-only-054"})
    with urlopen(request, timeout=timeout_seconds) as response:
        status_code = getattr(response, "status", None)
        body = response.read().decode("utf-8")
    return status_code, json.loads(body)


def _build_url(base_url: str, endpoint_path: str, query: Mapping[str, Any]) -> str:
    path = clean_text(endpoint_path)
    if not path.startswith("/"):
        path = "/" + path
    encoded = urlencode({key: value for key, value in dict(query).items() if clean_text(value)})
    return f"{base_url.rstrip('/')}{path}?{encoded}" if encoded else f"{base_url.rstrip('/')}{path}"


def _safe_limit(limit: int) -> int:
    try:
        value = int(limit)
    except (TypeError, ValueError):
        value = 20
    return max(1, min(value, 100))


def _count_markets(payload: Any) -> int:
    if isinstance(payload, list):
        if any(isinstance(row, Mapping) and "markets" in row for row in payload):
            return sum(len(row.get("markets", [])) for row in payload if isinstance(row, Mapping))
        return len([row for row in payload if isinstance(row, Mapping)])
    if isinstance(payload, Mapping):
        if isinstance(payload.get("markets"), list):
            return len(payload.get("markets", []))
        if isinstance(payload.get("events"), list):
            return sum(
                len(row.get("markets", []))
                for row in payload.get("events", [])
                if isinstance(row, Mapping)
            )
        for key in ("data", "results"):
            nested = payload.get(key)
            if isinstance(nested, (list, Mapping)):
                return _count_markets(nested)
    return 0


def _symbol_title(symbol: str) -> str:
    return {
        "BTC": "Bitcoin",
        "ETH": "Ethereum",
        "SOL": "Solana",
        "XRP": "XRP",
    }.get(clean_text(symbol).upper(), clean_text(symbol).upper() or "Generic market")
