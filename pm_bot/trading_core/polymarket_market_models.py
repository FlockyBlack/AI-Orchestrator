from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

from pm_bot.trading_core.schemas import GENERATED_AT, clean_text, trading_core_safety_summary

POLYMARKET_NORMALIZED_MARKET_CONTRACT = "pmbot_polymarket_normalized_market.v1"
POLYMARKET_NORMALIZED_MARKET_VALIDATION_CONTRACT = (
    "pmbot_polymarket_normalized_market_validation.v1"
)
POLYMARKET_NORMALIZED_MARKET_SUMMARY_CONTRACT = (
    "pmbot_polymarket_normalized_market_summary.v1"
)

DONOR_REFERENCE_REPOSITORY = "https://github.com/Polymarket/agents"
DONOR_REFERENCE_COMMIT = "081f2b5594c37edeb9d3780a778c084d5b6f2743"
DONOR_REFERENCE_LICENSE = "MIT"

PAPER_FILTER_PASSED = "paper_filter_passed"
PAPER_FILTER_BLOCKED = "paper_filter_blocked"

FORCED_FALSE_EXECUTION_FIELDS = (
    "live_execution_approved",
    "canary_executable_now",
    "real_execution_available",
    "order_submission_enabled",
    "wallet_signing_enabled",
    "signing_enabled",
    "signed_payload_generation_enabled",
    "signed_order_generation_enabled",
    "authenticated_polymarket_enabled",
    "live_connector_enabled",
    "allowed_for_live",
)


@dataclass(frozen=True)
class PolymarketNormalizedMarket:
    market_id: str
    condition_id: str
    question: str
    slug: str
    description: str
    active: bool
    closed: bool
    archived: bool
    restricted: bool
    funded: bool
    accepting_orders: bool
    enable_order_book: bool
    end_date: str
    liquidity: float | None
    volume: float | None
    volume_24h: float | None
    spread: float | None
    outcomes: tuple[str, ...]
    outcome_prices: tuple[float | None, ...]
    clob_token_ids: tuple[str, ...]
    order_min_size: float | None
    order_price_min_tick_size: float | None
    source: str
    fetched_at: str
    fixture_mode: bool
    source_url: str = ""
    raw_source_kind: str = "local_fixture"
    donor_reference_repository: str = DONOR_REFERENCE_REPOSITORY
    donor_reference_commit: str = DONOR_REFERENCE_COMMIT
    donor_reference_license: str = DONOR_REFERENCE_LICENSE
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = POLYMARKET_NORMALIZED_MARKET_CONTRACT
        value["outcomes"] = list(self.outcomes)
        value["outcome_prices"] = list(self.outcome_prices)
        value["clob_token_ids"] = list(self.clob_token_ids)
        value["paper_tradeable_filter_status"] = paper_tradeable_filter_status(value)
        value["normalization_basis"] = (
            "Field-shape adaptation from public Polymarket Gamma market metadata patterns; "
            "no live execution, wallet, signing, or order code is imported."
        )
        value.update(_paper_market_safety_flags())
        return value


def normalize_polymarket_market_payload(
    payload: Mapping[str, Any],
    *,
    source: str,
    fetched_at: str = GENERATED_AT,
    fixture_mode: bool = True,
    source_url: str = "",
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    if not isinstance(payload, Mapping):
        raise ValueError("payload must be a mapping")
    value = dict(payload)
    market_id = _first_text(value.get("market_id"), value.get("id"), value.get("questionID"))
    condition_id = _first_text(value.get("condition_id"), value.get("conditionId"), value.get("conditionID"))
    question = _first_text(value.get("question"), value.get("title"), value.get("name"))
    slug = _first_text(value.get("slug"), value.get("market_slug"), value.get("marketSlug"))
    description = _first_text(value.get("description"), question)
    outcomes = tuple(_clean_list(_parse_list(value.get("outcomes") or value.get("outcome"))))
    outcome_prices = tuple(_number_or_none(item) for item in _parse_list(value.get("outcomePrices") or value.get("outcome_prices")))
    clob_token_ids = tuple(
        _clean_list(_parse_list(value.get("clobTokenIds") or value.get("clob_token_ids") or value.get("token_ids")))
    )
    if not market_id:
        market_id = _stable_id("polymarket-market-052", {"condition_id": condition_id, "question": question})
    normalized = PolymarketNormalizedMarket(
        market_id=market_id,
        condition_id=condition_id,
        question=question,
        slug=slug,
        description=description,
        active=_bool_or_false(value.get("active")),
        closed=_bool_or_false(value.get("closed")),
        archived=_bool_or_false(value.get("archived")),
        restricted=_bool_or_false(value.get("restricted")),
        funded=_bool_or_false(value.get("funded"), default=True),
        accepting_orders=_bool_or_false(value.get("acceptingOrders"), value.get("accepting_orders"), default=True),
        enable_order_book=_bool_or_false(value.get("enableOrderBook"), value.get("enable_order_book"), default=True),
        end_date=_first_text(value.get("endDate"), value.get("end_date"), value.get("endDateIso")),
        liquidity=_number_or_none(value.get("liquidity"), value.get("liquidityNum"), value.get("liquidity_num")),
        volume=_number_or_none(value.get("volume"), value.get("volumeNum"), value.get("volume_num")),
        volume_24h=_number_or_none(value.get("volume24hr"), value.get("volume24h"), value.get("volume_24h")),
        spread=_number_or_none(value.get("spread")),
        outcomes=outcomes,
        outcome_prices=outcome_prices,
        clob_token_ids=clob_token_ids,
        order_min_size=_number_or_none(value.get("orderMinSize"), value.get("order_min_size")),
        order_price_min_tick_size=_number_or_none(
            value.get("orderPriceMinTickSize"),
            value.get("order_price_min_tick_size"),
        ),
        source=clean_text(source),
        fetched_at=clean_text(fetched_at) or generated_at,
        fixture_mode=fixture_mode is True,
        source_url=clean_text(source_url),
        raw_source_kind="local_fixture" if fixture_mode else "public_read_only",
        generated_at=generated_at,
    ).to_dict()
    validation = validate_normalized_polymarket_market(normalized, generated_at=generated_at)
    normalized["validation"] = validation
    if validation.get("valid") is not True:
        raise ValueError("; ".join(validation.get("errors", [])))
    return normalized


def validate_normalized_polymarket_market(
    market: Mapping[str, Any],
    *,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    value = dict(market or {})
    errors: list[str] = []
    if value.get("contract_version") != POLYMARKET_NORMALIZED_MARKET_CONTRACT:
        errors.append(f"contract_version must be {POLYMARKET_NORMALIZED_MARKET_CONTRACT}")
    for field in ("market_id", "question", "slug", "source", "fetched_at"):
        if not clean_text(value.get(field)):
            errors.append(f"{field} must be non-empty")
    if not isinstance(value.get("outcomes"), list) or len(value.get("outcomes", [])) < 2:
        errors.append("outcomes must contain at least two labels")
    if not isinstance(value.get("outcome_prices"), list):
        errors.append("outcome_prices must be a list")
    if not isinstance(value.get("clob_token_ids"), list):
        errors.append("clob_token_ids must be a list")
    for field in (
        "active",
        "closed",
        "archived",
        "restricted",
        "funded",
        "accepting_orders",
        "enable_order_book",
        "fixture_mode",
    ):
        if not isinstance(value.get(field), bool):
            errors.append(f"{field} must be boolean")
    for field in FORCED_FALSE_EXECUTION_FIELDS:
        if value.get(field) is not False:
            errors.append(f"{field} must be false")
    if value.get("network_used") is not False:
        errors.append("network_used must be false for fixture normalization")
    valid = not errors
    return {
        "contract_version": POLYMARKET_NORMALIZED_MARKET_VALIDATION_CONTRACT,
        "validation_id": _stable_id(
            "polymarket-normalized-market-validation-052",
            {"market_id": value.get("market_id"), "errors": errors},
        ),
        "generated_at": generated_at,
        "valid": valid,
        "status": "passed" if valid else "blocked",
        "errors": errors,
        **_paper_market_safety_flags(),
    }


def summarize_normalized_polymarket_market(market: Mapping[str, Any]) -> dict[str, Any]:
    value = dict(market or {})
    return {
        "contract_version": POLYMARKET_NORMALIZED_MARKET_SUMMARY_CONTRACT,
        "summary_id": _stable_id(
            "polymarket-normalized-market-summary-052",
            {
                "market_id": value.get("market_id"),
                "slug": value.get("slug"),
                "fetched_at": value.get("fetched_at"),
            },
        ),
        "market_id": clean_text(value.get("market_id")),
        "condition_id": clean_text(value.get("condition_id")),
        "question": clean_text(value.get("question")),
        "slug": clean_text(value.get("slug")),
        "active": value.get("active") is True,
        "closed": value.get("closed") is True,
        "archived": value.get("archived") is True,
        "restricted": value.get("restricted") is True,
        "funded": value.get("funded") is True,
        "accepting_orders": value.get("accepting_orders") is True,
        "enable_order_book": value.get("enable_order_book") is True,
        "end_date": clean_text(value.get("end_date")),
        "liquidity": value.get("liquidity"),
        "volume": value.get("volume"),
        "volume_24h": value.get("volume_24h"),
        "spread": value.get("spread"),
        "outcome_count": len(value.get("outcomes", [])) if isinstance(value.get("outcomes"), list) else 0,
        "clob_token_count": len(value.get("clob_token_ids", []))
        if isinstance(value.get("clob_token_ids"), list)
        else 0,
        "paper_tradeable_filter_status": paper_tradeable_filter_status(value),
        "source": clean_text(value.get("source")),
        "fetched_at": clean_text(value.get("fetched_at")),
        "fixture_mode": value.get("fixture_mode") is True,
        **_paper_market_safety_flags(),
    }


def paper_tradeable_filter_status(market: Mapping[str, Any]) -> str:
    value = dict(market or {})
    passed = (
        value.get("active") is True
        and value.get("closed") is False
        and value.get("archived") is False
        and value.get("restricted") is False
        and value.get("funded") is True
        and value.get("accepting_orders") is True
        and value.get("enable_order_book") is True
    )
    return PAPER_FILTER_PASSED if passed else PAPER_FILTER_BLOCKED


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


def _clean_list(values: Sequence[Any]) -> list[str]:
    return [clean_text(item) for item in values if clean_text(item)]


def _try_json(value: str) -> Any:
    try:
        return json.loads(value)
    except (TypeError, ValueError):
        return None


def _first_text(*values: Any) -> str:
    for value in values:
        text = clean_text(value)
        if text:
            return text
    return ""


def _number_or_none(*values: Any) -> float | None:
    for value in values:
        if value is None or isinstance(value, bool):
            continue
        try:
            return round(float(value), 6)
        except (TypeError, ValueError):
            continue
    return None


def _bool_or_false(*values: Any, default: bool = False) -> bool:
    for value in values:
        if isinstance(value, bool):
            return value
        text = clean_text(value).lower()
        if text in {"true", "1", "yes", "y", "active", "open"}:
            return True
        if text in {"false", "0", "no", "n", "inactive", "closed"}:
            return False
    return default


def _stable_id(prefix: str, payload: Mapping[str, Any]) -> str:
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()
    return f"{prefix}-{digest[:16]}"


def _paper_market_safety_flags() -> dict[str, Any]:
    value = {
        "execution_mode": "paper",
        "review_only": True,
        "paper_only": True,
        "local_artifact_only": True,
        "static_artifact_only": True,
        "passive_artifact_only": True,
        "execution_enabling": False,
        "network_used": False,
        "external_api_calls_performed": False,
        "environment_inspected": False,
        "environment_secrets_read": False,
        "secrets_read": False,
        "secrets_printed": False,
        "secrets_persisted": False,
        "live_execution_approved": False,
        "canary_executable_now": False,
        "real_execution_available": False,
        "order_submission_enabled": False,
        "wallet_signing_enabled": False,
        "signing_enabled": False,
        "signed_payload_generation_enabled": False,
        "signed_order_generation_enabled": False,
        "authenticated_polymarket_enabled": False,
        "live_connector_enabled": False,
        "allowed_for_live": False,
        "resolved_blocker_count": 0,
        "real_order_submitted": False,
        "wallet_used": False,
        "cryptographic_signing_performed": False,
        "authenticated_endpoint_call_performed": False,
        "browser_automation_added": False,
        "scheduler_or_daemon_added": False,
        "autonomous_live_trading_added": False,
        "outcome_resolution_invented": False,
        "price_data_invented": False,
        "pnl_invented": False,
    }
    value["safety_summary"] = trading_core_safety_summary()
    return value
