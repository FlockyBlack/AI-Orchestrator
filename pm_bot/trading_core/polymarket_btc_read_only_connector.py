from __future__ import annotations

import hashlib
import json
import urllib.request
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Callable, Mapping, Sequence

from pm_bot.trading_core.schemas import GENERATED_AT, clean_text, trading_core_safety_summary
from pm_bot.trading_core.secret_boundary_policy import (
    validate_secret_boundary_btc_connector_config,
    validate_secret_boundary_btc_connector_result,
    validate_secret_boundary_btc_market_snapshot,
)

POLYMARKET_BTC_READ_ONLY_CONFIG_CONTRACT = "pmbot_polymarket_btc_read_only_config.v1"
POLYMARKET_BTC_MARKET_STATUS_CONTRACT = "pmbot_polymarket_btc_market_status.v1"
POLYMARKET_BTC_OUTCOME_SNAPSHOT_CONTRACT = "pmbot_polymarket_btc_outcome_snapshot.v1"
POLYMARKET_BTC_PRICE_SNAPSHOT_CONTRACT = "pmbot_polymarket_btc_price_snapshot.v1"
POLYMARKET_BTC_DATA_FRESHNESS_CONTRACT = "pmbot_polymarket_btc_data_freshness.v1"
POLYMARKET_BTC_MARKET_SNAPSHOT_CONTRACT = "pmbot_polymarket_btc_market_snapshot.v1"
POLYMARKET_BTC_CONNECTOR_ERROR_CONTRACT = "pmbot_polymarket_btc_connector_error.v1"
POLYMARKET_BTC_CONNECTOR_RESULT_CONTRACT = "pmbot_polymarket_btc_connector_result.v1"
POLYMARKET_BTC_CONNECTOR_SUMMARY_CONTRACT = "pmbot_polymarket_btc_connector_summary.v1"

READ_ONLY_MODE = "read_only"
MARKET_STATUS_OPEN = "open"
MARKET_STATUS_CLOSED = "closed"
MARKET_STATUS_RESOLVED = "resolved"
MARKET_STATUS_UNKNOWN = "unknown"

PRICE_STATUS_AVAILABLE = "available"
PRICE_STATUS_NOT_AVAILABLE = "not_available"

FRESHNESS_STATUS_FRESH = "fresh"
FRESHNESS_STATUS_STALE = "stale"
FRESHNESS_STATUS_UNKNOWN_AGE = "unknown_age"
FRESHNESS_STATUS_NOT_EVALUATED = "not_evaluated"

RISK_STATUS_FRESH_OPEN_BTC_MARKET = "fresh_open_btc_market"
RISK_STATUS_STALE_MARKET_DATA = "stale_market_data"
RISK_STATUS_CLOSED_MARKET = "closed_market"
RISK_STATUS_RESOLVED_MARKET = "resolved_market"
RISK_STATUS_NOT_BTC_MARKET = "not_btc_market"
RISK_STATUS_UNKNOWN_MARKET_STATUS = "unknown_market_status"

DEFAULT_BTC_MARKET_ID = "btc-one-market-demo-market"
DEFAULT_BTC_MARKET_SLUG = "btc-one-market-demo"
DEFAULT_SOURCE_LABEL = "polymarket_btc_read_only_fixture_038"
DEFAULT_ALLOWED_BTC_TAGS = ("BTC", "BITCOIN")

FetchJSON = Callable[[str], Mapping[str, Any]]
FixtureLoader = Callable[[], Mapping[str, Any]]


@dataclass(frozen=True)
class PolymarketBTCReadOnlyConfig:
    config_id: str
    mode: str
    market_id: str
    market_slug: str
    market_url: str = ""
    allowed_market_tags: tuple[str, ...] = DEFAULT_ALLOWED_BTC_TAGS
    public_endpoint_url: str = "polymarket_public_market_endpoint_placeholder"
    network_enabled: bool = False
    max_snapshot_age_seconds: int = 300
    expected_outcome_count: int | None = None
    require_open_market: bool = True
    require_not_resolved: bool = True
    require_btc_tag: bool = True
    allow_fixture_payloads: bool = True
    source_label: str = DEFAULT_SOURCE_LABEL
    read_only: bool = True
    authenticated: bool = False
    order_submission_supported: bool = False
    wallet_required: bool = False
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = POLYMARKET_BTC_READ_ONLY_CONFIG_CONTRACT
        value["allowed_market_tags"] = list(self.allowed_market_tags)
        value.update(_read_only_safety_flags(network_used=False))
        return value


@dataclass(frozen=True)
class PolymarketBTCMarketStatus:
    status: str
    is_open: bool
    is_closed: bool
    is_resolved: bool

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = POLYMARKET_BTC_MARKET_STATUS_CONTRACT
        return value


@dataclass(frozen=True)
class PolymarketBTCOutcomeSnapshot:
    outcome_id: str
    name: str
    price: float | None = None
    probability: float | None = None
    best_bid: float | None = None
    best_ask: float | None = None
    last_price: float | None = None
    spread: float | None = None
    liquidity: float | None = None
    price_status: str = PRICE_STATUS_NOT_AVAILABLE

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = POLYMARKET_BTC_OUTCOME_SNAPSHOT_CONTRACT
        return value


@dataclass(frozen=True)
class PolymarketBTCPriceSnapshot:
    best_bid: float | None = None
    best_ask: float | None = None
    last_price: float | None = None
    spread: float | None = None
    liquidity: float | None = None
    price_status: str = PRICE_STATUS_NOT_AVAILABLE

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = POLYMARKET_BTC_PRICE_SNAPSHOT_CONTRACT
        return value


@dataclass(frozen=True)
class PolymarketBTCDataFreshness:
    freshness_status: str
    age_seconds: int | None
    stale: bool
    max_snapshot_age_seconds: int
    observed_at: str
    evaluated_at: str

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = POLYMARKET_BTC_DATA_FRESHNESS_CONTRACT
        return value


@dataclass(frozen=True)
class PolymarketBTCMarketSnapshot:
    snapshot_id: str
    market_id: str
    market_slug: str
    market_title: str
    normalized_market_tags: tuple[str, ...]
    is_btc_related: bool
    status: str
    is_open: bool
    is_closed: bool
    is_resolved: bool
    observed_at: str
    fetched_at: str
    age_seconds: int | None
    stale: bool
    outcomes: tuple[Mapping[str, Any], ...]
    best_bid: float | None
    best_ask: float | None
    last_price: float | None
    spread: float | None
    liquidity: float | None
    price_status: str
    source_label: str
    source_payload_hash: str
    risk_control_market_data_status: str
    ui_summary: Mapping[str, Any]
    freshness: Mapping[str, Any]
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = POLYMARKET_BTC_MARKET_SNAPSHOT_CONTRACT
        value["normalized_market_tags"] = list(self.normalized_market_tags)
        value["outcomes"] = [dict(row) for row in self.outcomes]
        value["ui_summary"] = dict(self.ui_summary)
        value["freshness"] = dict(self.freshness)
        value.update(_read_only_safety_flags(network_used=False))
        return value


@dataclass(frozen=True)
class PolymarketBTCConnectorError:
    error_code: str
    message: str
    retryable: bool = False

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = POLYMARKET_BTC_CONNECTOR_ERROR_CONTRACT
        return value


@dataclass(frozen=True)
class PolymarketBTCConnectorResult:
    result_id: str
    config_id: str
    status: str
    success: bool
    snapshot: Mapping[str, Any] | None = None
    error: Mapping[str, Any] | None = None
    network_attempted: bool = False
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = POLYMARKET_BTC_CONNECTOR_RESULT_CONTRACT
        value["snapshot"] = dict(self.snapshot) if isinstance(self.snapshot, Mapping) else None
        value["error"] = dict(self.error) if isinstance(self.error, Mapping) else None
        value.update(_read_only_safety_flags(network_used=self.network_attempted))
        return value


class PolymarketBTCReadOnlyConnector:
    def __init__(self, config: PolymarketBTCReadOnlyConfig | Mapping[str, Any] | None = None) -> None:
        self.config = _config_from_any(config or build_default_btc_read_only_config())
        validation = validate_btc_read_only_config(self.config)
        if validation.get("valid") is not True:
            raise ValueError("; ".join(validation.get("errors", [])))

    def build_snapshot_from_fixture_payload(
        self,
        payload: Mapping[str, Any],
        *,
        current_time: str | datetime | None = None,
    ) -> dict[str, Any]:
        if self.config.allow_fixture_payloads is not True:
            return _connector_result(
                self.config,
                status="fixture_payloads_disabled",
                error_code="FIXTURE_PAYLOADS_DISABLED",
                message="Fixture payloads are disabled by config.",
            )
        return _snapshot_result_from_payload(self.config, payload, current_time=current_time)

    def build_snapshot_from_fixture_loader(
        self,
        fixture_loader: FixtureLoader,
        *,
        current_time: str | datetime | None = None,
    ) -> dict[str, Any]:
        if self.config.allow_fixture_payloads is not True:
            return _connector_result(
                self.config,
                status="fixture_payloads_disabled",
                error_code="FIXTURE_PAYLOADS_DISABLED",
                message="Fixture payloads are disabled by config.",
            )
        payload = fixture_loader()
        return _snapshot_result_from_payload(self.config, payload, current_time=current_time)

    def fetch_public_market_read_only(
        self,
        *,
        operator_read_only_network_allowed: bool = False,
        fetcher: FetchJSON | None = None,
        current_time: str | datetime | None = None,
    ) -> dict[str, Any]:
        return fetch_public_polymarket_market_read_only(
            self.config,
            operator_read_only_network_allowed=operator_read_only_network_allowed,
            fetcher=fetcher,
            current_time=current_time,
        )


def build_default_btc_read_only_config(
    *,
    config_id: str = "polymarket-btc-read-only-config-038-default",
    market_id: str = DEFAULT_BTC_MARKET_ID,
    market_slug: str = DEFAULT_BTC_MARKET_SLUG,
    market_url: str = "",
    public_endpoint_url: str = "polymarket_public_market_endpoint_placeholder",
    network_enabled: bool = False,
    max_snapshot_age_seconds: int = 300,
    expected_outcome_count: int | None = 2,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    config = PolymarketBTCReadOnlyConfig(
        config_id=clean_text(config_id),
        mode=READ_ONLY_MODE,
        market_id=clean_text(market_id),
        market_slug=clean_text(market_slug),
        market_url=clean_text(market_url),
        public_endpoint_url=clean_text(public_endpoint_url),
        network_enabled=network_enabled is True,
        max_snapshot_age_seconds=int(max_snapshot_age_seconds),
        expected_outcome_count=expected_outcome_count,
        generated_at=generated_at,
    ).to_dict()
    validation = validate_btc_read_only_config(config, generated_at=generated_at)
    config["validation"] = validation
    if validation.get("valid") is not True:
        raise ValueError("; ".join(validation.get("errors", [])))
    return config


def validate_btc_read_only_config(
    config: PolymarketBTCReadOnlyConfig | Mapping[str, Any],
    *,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    value = _mapping(config)
    errors: list[str] = []
    if value.get("contract_version") != POLYMARKET_BTC_READ_ONLY_CONFIG_CONTRACT:
        errors.append(f"contract_version must be {POLYMARKET_BTC_READ_ONLY_CONFIG_CONTRACT}")
    if clean_text(value.get("mode")) != READ_ONLY_MODE:
        errors.append("mode must be read_only")
    for field in ("config_id", "market_id", "market_slug", "source_label"):
        if not clean_text(value.get(field)):
            errors.append(f"{field} must be non-empty")
    for field in (
        "network_enabled",
        "require_open_market",
        "require_not_resolved",
        "require_btc_tag",
        "allow_fixture_payloads",
    ):
        if not isinstance(value.get(field), bool):
            errors.append(f"{field} must be a boolean")
    if value.get("read_only") is not True:
        errors.append("read_only must be true")
    for field in ("authenticated", "order_submission_supported", "wallet_required"):
        if value.get(field) is not False:
            errors.append(f"{field} must be false")
    if not isinstance(value.get("allowed_market_tags"), list):
        errors.append("allowed_market_tags must be a list")
    elif any(not clean_text(item) for item in value.get("allowed_market_tags", [])):
        errors.append("allowed_market_tags must contain only non-empty strings")
    max_age = value.get("max_snapshot_age_seconds")
    if not isinstance(max_age, int) or isinstance(max_age, bool) or max_age < 0:
        errors.append("max_snapshot_age_seconds must be a non-negative integer")
    expected_count = value.get("expected_outcome_count")
    if expected_count is not None and (
        not isinstance(expected_count, int) or isinstance(expected_count, bool) or expected_count <= 0
    ):
        errors.append("expected_outcome_count must be a positive integer or null")
    if value.get("require_btc_tag") is True and not _config_looks_btc_related(value):
        errors.append("config must identify a BTC or Bitcoin market when require_btc_tag is true")
    boundary_validation = validate_secret_boundary_btc_connector_config(value, generated_at=generated_at)
    if boundary_validation.get("valid") is not True:
        errors.append("config violates BTC connector secret boundary")
    valid = not errors
    return {
        "contract_version": "pmbot_polymarket_btc_read_only_config_validation.v1",
        "validation_id": _stable_id(
            "polymarket-btc-read-only-config-validation-038",
            {"config_id": value.get("config_id"), "errors": errors},
        ),
        "generated_at": generated_at,
        "valid": valid,
        "status": "passed" if valid else "blocked",
        "errors": errors,
        "config_secret_boundary_validation": boundary_validation,
        "read_only": True,
        "network_enabled": value.get("network_enabled") is True,
        "authenticated_requests_supported": False,
        "order_submission_supported": False,
        "wallet_required": False,
        "live_execution_approved": False,
        "canary_executable_now": False,
        "real_execution_available": False,
        "live_connector_enabled": False,
    }


def normalize_polymarket_btc_market_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, Mapping):
        raise ValueError("payload must be a JSON object")
    market = payload.get("market")
    value = dict(market) if isinstance(market, Mapping) else dict(payload)
    market_id = _first_text(
        value.get("market_id"),
        value.get("id"),
        value.get("condition_id"),
        value.get("conditionId"),
        value.get("question_id"),
        value.get("questionID"),
    )
    market_slug = _first_text(value.get("market_slug"), value.get("slug"), value.get("marketSlug"))
    market_title = _first_text(
        value.get("market_title"),
        value.get("title"),
        value.get("question"),
        value.get("name"),
        value.get("description"),
    )
    if not market_id and not market_slug:
        raise ValueError("payload must include market id or slug")
    if not market_title:
        raise ValueError("payload must include market title or question")
    tags = _normalize_tags(
        _collect_tag_values(value.get("tags"))
        + _collect_tag_values(value.get("market_tags"))
        + _collect_tag_values(value.get("categories"))
        + _collect_tag_values(value.get("category"))
        + _collect_tag_values(value.get("events"))
    )
    outcome_names = _parse_outcome_names(value.get("outcomes"))
    if not outcome_names:
        raise ValueError("payload outcomes must be a non-empty list or JSON list string")
    outcome_prices = _parse_json_list(value.get("outcomePrices") or value.get("outcome_prices"))
    outcome_probabilities = _parse_json_list(value.get("probabilities") or value.get("outcome_probabilities"))
    token_ids = _parse_json_list(value.get("clobTokenIds") or value.get("token_ids") or value.get("outcome_ids"))
    outcomes = []
    for index, row in enumerate(outcome_names):
        row_mapping = row if isinstance(row, Mapping) else {}
        name = _first_text(row_mapping.get("name"), row_mapping.get("title"), row_mapping.get("outcome"), row)
        if not name:
            raise ValueError(f"payload outcomes[{index}] must include a name")
        best_bid = _first_number(
            row_mapping.get("best_bid"),
            row_mapping.get("bestBid"),
            row_mapping.get("bid"),
        )
        best_ask = _first_number(
            row_mapping.get("best_ask"),
            row_mapping.get("bestAsk"),
            row_mapping.get("ask"),
        )
        price = _first_number(
            row_mapping.get("price"),
            row_mapping.get("probability"),
            outcome_prices[index] if index < len(outcome_prices) else None,
            outcome_probabilities[index] if index < len(outcome_probabilities) else None,
        )
        probability = _first_number(
            row_mapping.get("probability"),
            row_mapping.get("prob"),
            outcome_probabilities[index] if index < len(outcome_probabilities) else None,
            price,
        )
        last_price = _first_number(row_mapping.get("last_price"), row_mapping.get("lastPrice"), price)
        liquidity = _first_number(row_mapping.get("liquidity"), row_mapping.get("liquidity_num"))
        spread = _spread(best_bid, best_ask)
        price_status = PRICE_STATUS_AVAILABLE if any(
            value is not None for value in (price, probability, best_bid, best_ask, last_price, liquidity)
        ) else PRICE_STATUS_NOT_AVAILABLE
        outcome_id = _first_text(
            row_mapping.get("outcome_id"),
            row_mapping.get("id"),
            token_ids[index] if index < len(token_ids) else "",
            f"outcome-{index + 1}",
        )
        outcomes.append(
            {
                "outcome_id": outcome_id,
                "name": name,
                "price": price,
                "probability": probability,
                "best_bid": best_bid,
                "best_ask": best_ask,
                "last_price": last_price,
                "spread": spread,
                "liquidity": liquidity,
                "price_status": price_status,
            }
        )
    status = _market_status(value)
    normalized = {
        "market_id": market_id,
        "market_slug": market_slug,
        "market_title": market_title,
        "normalized_market_tags": tags,
        "status": status["status"],
        "is_open": status["is_open"],
        "is_closed": status["is_closed"],
        "is_resolved": status["is_resolved"],
        "observed_at": _first_text(
            value.get("observed_at"),
            value.get("fetched_at"),
            value.get("updated_at"),
            value.get("last_updated_at"),
            value.get("lastUpdated"),
            value.get("created_at"),
            value.get("timestamp"),
            GENERATED_AT,
        ),
        "fetched_at": _first_text(value.get("fetched_at"), value.get("observed_at"), GENERATED_AT),
        "outcomes": outcomes,
        "best_bid": _first_number(value.get("best_bid"), value.get("bestBid"), _first_outcome_number(outcomes, "best_bid")),
        "best_ask": _first_number(value.get("best_ask"), value.get("bestAsk"), _first_outcome_number(outcomes, "best_ask")),
        "last_price": _first_number(
            value.get("last_price"),
            value.get("lastPrice"),
            value.get("lastTradePrice"),
            _first_outcome_number(outcomes, "last_price"),
        ),
        "liquidity": _first_number(
            value.get("liquidity"),
            value.get("liquidity_num"),
            value.get("liquidityNum"),
            value.get("liquidity_usd"),
        ),
        "raw_payload": _json_safe(value),
    }
    normalized["spread"] = _first_number(value.get("spread"), _spread(normalized["best_bid"], normalized["best_ask"]))
    normalized["price_status"] = PRICE_STATUS_AVAILABLE if any(
        normalized.get(field) is not None for field in ("best_bid", "best_ask", "last_price", "spread", "liquidity")
    ) else PRICE_STATUS_NOT_AVAILABLE
    return normalized


def build_btc_market_snapshot_from_payload(
    payload: Mapping[str, Any],
    config: PolymarketBTCReadOnlyConfig | Mapping[str, Any] | None = None,
    *,
    current_time: str | datetime | None = None,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    active_config = _config_from_any(config or build_default_btc_read_only_config(generated_at=generated_at))
    normalized = normalize_polymarket_btc_market_payload(payload)
    market_id = normalized["market_id"] or active_config.market_id
    market_slug = normalized["market_slug"] or active_config.market_slug
    if active_config.market_id and market_id and clean_text(market_id) != active_config.market_id:
        raise ValueError("payload market_id does not match BTC read-only config")
    if active_config.market_slug and market_slug and clean_text(market_slug) != active_config.market_slug:
        raise ValueError("payload market_slug does not match BTC read-only config")
    outcomes = tuple(
        PolymarketBTCOutcomeSnapshot(**dict(row)).to_dict() for row in normalized["outcomes"]
    )
    if active_config.expected_outcome_count is not None and len(outcomes) != active_config.expected_outcome_count:
        raise ValueError("payload outcome count does not match expected_outcome_count")
    tags = tuple(normalized["normalized_market_tags"])
    is_btc_related = _is_btc_related(
        market_id=market_id,
        market_slug=market_slug,
        market_title=normalized["market_title"],
        tags=tags,
    )
    if active_config.require_btc_tag and not is_btc_related:
        raise ValueError("payload is not BTC or Bitcoin related")
    if active_config.require_not_resolved and normalized["is_resolved"]:
        raise ValueError("payload market is resolved but config requires unresolved market")
    freshness = evaluate_btc_market_snapshot_freshness(
        {
            "observed_at": normalized["observed_at"],
            "status": normalized["status"],
            "is_btc_related": is_btc_related,
            "is_open": normalized["is_open"],
            "is_resolved": normalized["is_resolved"],
        },
        config=active_config.to_dict(),
        current_time=current_time,
        generated_at=generated_at,
    )
    if active_config.require_open_market and normalized["status"] != MARKET_STATUS_OPEN:
        risk_status = _risk_status(
            is_btc_related=is_btc_related,
            market_status=normalized["status"],
            stale=freshness["stale"],
        )
    else:
        risk_status = _risk_status(
            is_btc_related=is_btc_related,
            market_status=normalized["status"],
            stale=freshness["stale"],
        )
    price = PolymarketBTCPriceSnapshot(
        best_bid=normalized["best_bid"],
        best_ask=normalized["best_ask"],
        last_price=normalized["last_price"],
        spread=normalized["spread"],
        liquidity=normalized["liquidity"],
        price_status=normalized["price_status"],
    ).to_dict()
    payload_hash = _stable_payload_hash(normalized["raw_payload"])
    ui_summary = {
        "contract_version": "pmbot_polymarket_btc_market_ui_summary.v1",
        "btc_market_connector_status": "fixture_snapshot_validated_read_only",
        "market_id": market_id,
        "market_slug": market_slug,
        "market_title": normalized["market_title"],
        "is_btc_related": is_btc_related,
        "market_status": normalized["status"],
        "is_open": normalized["is_open"],
        "is_resolved": normalized["is_resolved"],
        "stale": freshness["stale"],
        "snapshot_age_seconds": freshness["age_seconds"],
        "best_bid": price["best_bid"],
        "best_ask": price["best_ask"],
        "last_price": price["last_price"],
        "spread": price["spread"],
        "liquidity": price["liquidity"],
        "price_status": price["price_status"],
        "risk_control_market_data_status": risk_status,
        "read_only_network_enabled": active_config.network_enabled,
        "read_only": True,
        "execution_enabling": False,
    }
    snapshot_id = _stable_id(
        "polymarket-btc-market-snapshot-038",
        {
            "market_id": market_id,
            "market_slug": market_slug,
            "observed_at": normalized["observed_at"],
            "payload_hash": payload_hash,
            "freshness": freshness,
        },
    )
    snapshot = PolymarketBTCMarketSnapshot(
        snapshot_id=snapshot_id,
        market_id=market_id,
        market_slug=market_slug,
        market_title=normalized["market_title"],
        normalized_market_tags=tags,
        is_btc_related=is_btc_related,
        status=normalized["status"],
        is_open=normalized["is_open"],
        is_closed=normalized["is_closed"],
        is_resolved=normalized["is_resolved"],
        observed_at=normalized["observed_at"],
        fetched_at=normalized["fetched_at"],
        age_seconds=freshness["age_seconds"],
        stale=freshness["stale"],
        outcomes=outcomes,
        best_bid=price["best_bid"],
        best_ask=price["best_ask"],
        last_price=price["last_price"],
        spread=price["spread"],
        liquidity=price["liquidity"],
        price_status=price["price_status"],
        source_label=active_config.source_label,
        source_payload_hash=payload_hash,
        risk_control_market_data_status=risk_status,
        ui_summary=ui_summary,
        freshness=freshness,
        generated_at=generated_at,
    ).to_dict()
    boundary_validation = validate_secret_boundary_btc_market_snapshot(snapshot, generated_at=generated_at)
    snapshot["snapshot_secret_boundary_validation"] = boundary_validation
    if boundary_validation.get("valid") is not True:
        raise ValueError("snapshot violates BTC market secret boundary")
    return snapshot


def evaluate_btc_market_snapshot_freshness(
    snapshot_or_payload: Mapping[str, Any],
    config: PolymarketBTCReadOnlyConfig | Mapping[str, Any] | None = None,
    *,
    current_time: str | datetime | None = None,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    active_config = _config_from_any(config or build_default_btc_read_only_config(generated_at=generated_at))
    observed_at = _first_text(snapshot_or_payload.get("observed_at"), snapshot_or_payload.get("fetched_at"), generated_at)
    evaluated_at = _datetime_to_text(_coerce_datetime(current_time) or _coerce_datetime(generated_at) or datetime.now(timezone.utc))
    observed_dt = _coerce_datetime(observed_at)
    evaluated_dt = _coerce_datetime(evaluated_at)
    age_seconds: int | None = None
    if observed_dt is not None and evaluated_dt is not None:
        age_seconds = max(int((evaluated_dt - observed_dt).total_seconds()), 0)
    stale = age_seconds is not None and age_seconds > active_config.max_snapshot_age_seconds
    if age_seconds is None:
        status = FRESHNESS_STATUS_UNKNOWN_AGE
    elif stale:
        status = FRESHNESS_STATUS_STALE
    else:
        status = FRESHNESS_STATUS_FRESH
    return PolymarketBTCDataFreshness(
        freshness_status=status if current_time is not None else FRESHNESS_STATUS_NOT_EVALUATED,
        age_seconds=age_seconds,
        stale=stale,
        max_snapshot_age_seconds=active_config.max_snapshot_age_seconds,
        observed_at=observed_at,
        evaluated_at=evaluated_at,
    ).to_dict()


def summarize_btc_market_snapshot(snapshot: Mapping[str, Any] | None) -> dict[str, Any]:
    value = dict(snapshot or {})
    ui_summary = dict(value.get("ui_summary", {}))
    freshness = dict(value.get("freshness", {}))
    return {
        "contract_version": POLYMARKET_BTC_CONNECTOR_SUMMARY_CONTRACT,
        "btc_market_connector_status": clean_text(
            ui_summary.get("btc_market_connector_status") or "not_available"
        ),
        "snapshot_id": clean_text(value.get("snapshot_id")),
        "market_id": clean_text(value.get("market_id")),
        "market_slug": clean_text(value.get("market_slug")),
        "market_title": clean_text(value.get("market_title")),
        "normalized_market_tags": list(value.get("normalized_market_tags", [])),
        "is_btc_related": value.get("is_btc_related") is True,
        "market_status": clean_text(value.get("status") or MARKET_STATUS_UNKNOWN),
        "is_open": value.get("is_open") is True,
        "is_closed": value.get("is_closed") is True,
        "is_resolved": value.get("is_resolved") is True,
        "stale": value.get("stale") is True,
        "snapshot_age_seconds": value.get("age_seconds"),
        "best_bid": value.get("best_bid"),
        "best_ask": value.get("best_ask"),
        "last_price": value.get("last_price"),
        "spread": value.get("spread"),
        "liquidity": value.get("liquidity"),
        "price_status": clean_text(value.get("price_status") or PRICE_STATUS_NOT_AVAILABLE),
        "outcome_count": len(value.get("outcomes", [])) if isinstance(value.get("outcomes"), list) else 0,
        "outcome_price_statuses": [
            clean_text(row.get("price_status") or PRICE_STATUS_NOT_AVAILABLE)
            for row in value.get("outcomes", [])
            if isinstance(row, Mapping)
        ],
        "observed_at": clean_text(value.get("observed_at")),
        "fetched_at": clean_text(value.get("fetched_at")),
        "source_label": clean_text(value.get("source_label")),
        "source_payload_hash": clean_text(value.get("source_payload_hash")),
        "freshness_status": clean_text(freshness.get("freshness_status") or FRESHNESS_STATUS_NOT_EVALUATED),
        "risk_control_market_data_status": clean_text(
            value.get("risk_control_market_data_status") or RISK_STATUS_UNKNOWN_MARKET_STATUS
        ),
        "read_only": True,
        "read_only_network_enabled": ui_summary.get("read_only_network_enabled") is True,
        "execution_enabling": False,
        "allowed_for_live": False,
        "canary_executable_now": False,
        "live_execution_approved": False,
        "real_execution_available": False,
        "live_connector_enabled": False,
    }


def fetch_public_polymarket_market_read_only(
    config: PolymarketBTCReadOnlyConfig | Mapping[str, Any],
    *,
    operator_read_only_network_allowed: bool = False,
    fetcher: FetchJSON | None = None,
    current_time: str | datetime | None = None,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    active_config = _config_from_any(config)
    validation = validate_btc_read_only_config(active_config, generated_at=generated_at)
    if validation.get("valid") is not True:
        return _connector_result(
            active_config,
            status="config_invalid",
            error_code="CONFIG_INVALID",
            message="; ".join(validation.get("errors", [])),
            generated_at=generated_at,
        )
    if active_config.network_enabled is not True:
        return _connector_result(
            active_config,
            status="network_disabled",
            error_code="NETWORK_DISABLED",
            message="Read-only public network fetch is disabled by default.",
            generated_at=generated_at,
        )
    if operator_read_only_network_allowed is not True:
        return _connector_result(
            active_config,
            status="operator_network_not_allowed",
            error_code="OPERATOR_NETWORK_NOT_ALLOWED",
            message="Explicit operator read-only network allowance is required.",
            generated_at=generated_at,
        )
    endpoint = clean_text(active_config.public_endpoint_url)
    if not endpoint.startswith("https://"):
        return _connector_result(
            active_config,
            status="endpoint_not_public_https",
            error_code="ENDPOINT_NOT_PUBLIC_HTTPS",
            message="Public read-only endpoint must be an https URL when network is enabled.",
            generated_at=generated_at,
        )
    if _looks_like_forbidden_endpoint(endpoint):
        return _connector_result(
            active_config,
            status="endpoint_forbidden",
            error_code="ENDPOINT_FORBIDDEN",
            message="Endpoint shape appears to target an auth, order, wallet, or CLOB submission boundary.",
            generated_at=generated_at,
        )
    payload_fetcher = fetcher or _default_public_get_json
    try:
        payload = payload_fetcher(endpoint)
        return _snapshot_result_from_payload(
            active_config,
            payload,
            current_time=current_time,
            network_attempted=True,
            generated_at=generated_at,
        )
    except Exception as exc:
        return _connector_result(
            active_config,
            status="read_only_fetch_failed",
            error_code="READ_ONLY_FETCH_FAILED",
            message=str(exc),
            retryable=True,
            network_attempted=True,
            generated_at=generated_at,
        )


def build_default_btc_fixture_market_payload(*, observed_at: str = GENERATED_AT) -> dict[str, Any]:
    return {
        "id": DEFAULT_BTC_MARKET_ID,
        "slug": DEFAULT_BTC_MARKET_SLUG,
        "question": "Will Bitcoin close above the demo threshold on the fixture date?",
        "tags": ["BTC", "Bitcoin"],
        "active": True,
        "closed": False,
        "resolved": False,
        "fetched_at": observed_at,
        "observed_at": observed_at,
        "outcomes": [
            {
                "id": "btc-demo-yes",
                "name": "Yes",
                "price": 0.52,
                "bestBid": 0.51,
                "bestAsk": 0.53,
                "lastPrice": 0.52,
                "liquidity": 2500.0,
            },
            {
                "id": "btc-demo-no",
                "name": "No",
                "price": 0.48,
                "bestBid": 0.47,
                "bestAsk": 0.49,
                "lastPrice": 0.48,
                "liquidity": 2500.0,
            },
        ],
        "bestBid": 0.51,
        "bestAsk": 0.53,
        "lastPrice": 0.52,
        "liquidity": 2500.0,
    }


def _snapshot_result_from_payload(
    config: PolymarketBTCReadOnlyConfig,
    payload: Mapping[str, Any],
    *,
    current_time: str | datetime | None = None,
    network_attempted: bool = False,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    try:
        snapshot = build_btc_market_snapshot_from_payload(
            payload,
            config,
            current_time=current_time,
            generated_at=generated_at,
        )
        result = PolymarketBTCConnectorResult(
            result_id=_stable_id(
                "polymarket-btc-connector-result-038",
                {"config_id": config.config_id, "snapshot_id": snapshot.get("snapshot_id")},
            ),
            config_id=config.config_id,
            status="snapshot_ready",
            success=True,
            snapshot=snapshot,
            error=None,
            network_attempted=network_attempted,
            generated_at=generated_at,
        ).to_dict()
    except Exception as exc:
        result = _connector_result(
            config,
            status="payload_rejected",
            error_code="PAYLOAD_REJECTED",
            message=str(exc),
            network_attempted=network_attempted,
            generated_at=generated_at,
        )
    validation = validate_secret_boundary_btc_connector_result(result, generated_at=generated_at)
    result["result_secret_boundary_validation"] = validation
    if validation.get("valid") is not True:
        result["success"] = False
        result["status"] = "secret_boundary_blocked"
        result["error"] = PolymarketBTCConnectorError(
            error_code="SECRET_BOUNDARY_BLOCKED",
            message="Connector result violates BTC secret boundary.",
        ).to_dict()
    return result


def _connector_result(
    config: PolymarketBTCReadOnlyConfig,
    *,
    status: str,
    error_code: str,
    message: str,
    retryable: bool = False,
    network_attempted: bool = False,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    error = PolymarketBTCConnectorError(error_code=error_code, message=message, retryable=retryable).to_dict()
    result = PolymarketBTCConnectorResult(
        result_id=_stable_id(
            "polymarket-btc-connector-result-038",
            {"config_id": config.config_id, "status": status, "error_code": error_code, "message": message},
        ),
        config_id=config.config_id,
        status=status,
        success=False,
        snapshot=None,
        error=error,
        network_attempted=network_attempted,
        generated_at=generated_at,
    ).to_dict()
    result["result_secret_boundary_validation"] = validate_secret_boundary_btc_connector_result(
        result,
        generated_at=generated_at,
    )
    return result


def _config_from_any(value: PolymarketBTCReadOnlyConfig | Mapping[str, Any]) -> PolymarketBTCReadOnlyConfig:
    if isinstance(value, PolymarketBTCReadOnlyConfig):
        return value
    mapping = dict(value)
    return PolymarketBTCReadOnlyConfig(
        config_id=clean_text(mapping.get("config_id")),
        mode=clean_text(mapping.get("mode")),
        market_id=clean_text(mapping.get("market_id")),
        market_slug=clean_text(mapping.get("market_slug")),
        market_url=clean_text(mapping.get("market_url")),
        allowed_market_tags=tuple(clean_text(item) for item in mapping.get("allowed_market_tags", []) if clean_text(item)),
        public_endpoint_url=clean_text(mapping.get("public_endpoint_url")),
        network_enabled=mapping.get("network_enabled") is True,
        max_snapshot_age_seconds=int(mapping.get("max_snapshot_age_seconds", 0) or 0),
        expected_outcome_count=(
            int(mapping["expected_outcome_count"])
            if mapping.get("expected_outcome_count") is not None
            else None
        ),
        require_open_market=mapping.get("require_open_market") is True,
        require_not_resolved=mapping.get("require_not_resolved") is True,
        require_btc_tag=mapping.get("require_btc_tag") is True,
        allow_fixture_payloads=mapping.get("allow_fixture_payloads") is True,
        source_label=clean_text(mapping.get("source_label")),
        read_only=mapping.get("read_only") is True,
        authenticated=mapping.get("authenticated") is True,
        order_submission_supported=mapping.get("order_submission_supported") is True,
        wallet_required=mapping.get("wallet_required") is True,
        generated_at=clean_text(mapping.get("generated_at")) or GENERATED_AT,
    )


def _mapping(value: Any) -> dict[str, Any]:
    if hasattr(value, "to_dict"):
        return dict(value.to_dict())
    if isinstance(value, Mapping):
        return dict(value)
    raise TypeError("BTC read-only connector value must be a mapping or expose to_dict()")


def _market_status(value: Mapping[str, Any]) -> dict[str, Any]:
    resolved = _first_bool(value.get("resolved"), value.get("is_resolved"), value.get("outcomeResolved"))
    closed = _first_bool(value.get("closed"), value.get("is_closed"), value.get("archived"))
    open_flag = _first_bool(value.get("open"), value.get("is_open"))
    active = _first_bool(value.get("active"), value.get("is_active"), value.get("enabled"))
    status_text = clean_text(value.get("status") or value.get("market_status")).lower()
    if status_text in {MARKET_STATUS_RESOLVED, "final", "settled"}:
        resolved = True
    if status_text in {MARKET_STATUS_CLOSED, "inactive"}:
        closed = True
    if status_text in {MARKET_STATUS_OPEN, "active", "trading"}:
        open_flag = True
    is_resolved = resolved is True
    is_closed = closed is True or (active is False and open_flag is not True)
    is_open = open_flag is True or (active is True and not is_closed and not is_resolved)
    if is_resolved:
        status = MARKET_STATUS_RESOLVED
    elif is_closed:
        status = MARKET_STATUS_CLOSED
    elif is_open:
        status = MARKET_STATUS_OPEN
    else:
        status = MARKET_STATUS_UNKNOWN
    return PolymarketBTCMarketStatus(
        status=status,
        is_open=status == MARKET_STATUS_OPEN,
        is_closed=status == MARKET_STATUS_CLOSED,
        is_resolved=status == MARKET_STATUS_RESOLVED,
    ).to_dict()


def _risk_status(*, is_btc_related: bool, market_status: str, stale: bool) -> str:
    if not is_btc_related:
        return RISK_STATUS_NOT_BTC_MARKET
    if stale:
        return RISK_STATUS_STALE_MARKET_DATA
    if market_status == MARKET_STATUS_RESOLVED:
        return RISK_STATUS_RESOLVED_MARKET
    if market_status == MARKET_STATUS_CLOSED:
        return RISK_STATUS_CLOSED_MARKET
    if market_status == MARKET_STATUS_OPEN:
        return RISK_STATUS_FRESH_OPEN_BTC_MARKET
    return RISK_STATUS_UNKNOWN_MARKET_STATUS


def _is_btc_related(*, market_id: str, market_slug: str, market_title: str, tags: Sequence[str]) -> bool:
    text = " ".join([market_id, market_slug, market_title, *tags]).lower()
    tokens = {_normalize_token(item) for item in [market_id, market_slug, market_title, *tags]}
    return "bitcoin" in text or "btc" in tokens or any("btc" in token or "bitcoin" in token for token in tokens)


def _config_looks_btc_related(value: Mapping[str, Any]) -> bool:
    return _is_btc_related(
        market_id=clean_text(value.get("market_id")),
        market_slug=clean_text(value.get("market_slug")),
        market_title=clean_text(value.get("market_title") or value.get("market_url")),
        tags=[clean_text(item) for item in value.get("allowed_market_tags", [])],
    )


def _collect_tag_values(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        parsed = _try_json(value)
        if isinstance(parsed, list):
            return _collect_tag_values(parsed)
        return [value]
    if isinstance(value, Mapping):
        return [
            _first_text(value.get("label"), value.get("name"), value.get("slug"), value.get("id"))
        ]
    if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray)):
        rows = []
        for item in value:
            rows.extend(_collect_tag_values(item))
        return rows
    return [clean_text(value)]


def _normalize_tags(values: Sequence[str]) -> tuple[str, ...]:
    tags: list[str] = []
    for value in values:
        text = clean_text(value)
        if not text:
            continue
        upper = text.upper()
        if upper not in tags:
            tags.append(upper)
    return tuple(tags)


def _parse_outcome_names(value: Any) -> list[Any]:
    parsed = _parse_json_list(value)
    return parsed


def _parse_json_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, str):
        parsed = _try_json(value)
        if isinstance(parsed, list):
            return parsed
        if clean_text(value):
            return [value]
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return []


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


def _first_number(*values: Any) -> float | None:
    for value in values:
        number = _number_or_none(value)
        if number is not None:
            return number
    return None


def _number_or_none(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return round(float(value), 6)
    try:
        text = clean_text(value).replace("%", "")
        if not text:
            return None
        number = float(text)
        if "%" in clean_text(value):
            number = number / 100.0
        return round(number, 6)
    except (TypeError, ValueError):
        return None


def _first_bool(*values: Any) -> bool | None:
    for value in values:
        parsed = _bool_or_none(value)
        if parsed is not None:
            return parsed
    return None


def _bool_or_none(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    text = clean_text(value).lower()
    if text in {"true", "1", "yes", "y", "open", "active"}:
        return True
    if text in {"false", "0", "no", "n", "closed", "inactive"}:
        return False
    return None


def _spread(best_bid: float | None, best_ask: float | None) -> float | None:
    if best_bid is None or best_ask is None:
        return None
    return round(max(best_ask - best_bid, 0.0), 6)


def _first_outcome_number(outcomes: Sequence[Mapping[str, Any]], field: str) -> float | None:
    for outcome in outcomes:
        number = _number_or_none(outcome.get(field))
        if number is not None:
            return number
    return None


def _coerce_datetime(value: str | datetime | None) -> datetime | None:
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)
    text = clean_text(value)
    if not text:
        return None
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _datetime_to_text(value: datetime) -> str:
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


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


def _stable_payload_hash(payload: Any) -> str:
    return hashlib.sha256(json.dumps(_json_safe(payload), sort_keys=True).encode("utf-8")).hexdigest()


def _stable_id(prefix: str, payload: Mapping[str, Any]) -> str:
    digest = hashlib.sha256(json.dumps(_json_safe(payload), sort_keys=True).encode("utf-8")).hexdigest()
    return f"{prefix}-{digest[:16]}"


def _normalize_token(value: Any) -> str:
    normalized = "".join(ch if ch.isalnum() else "_" for ch in clean_text(value).lower())
    while "__" in normalized:
        normalized = normalized.replace("__", "_")
    return normalized.strip("_")


def _looks_like_forbidden_endpoint(url: str) -> bool:
    normalized = url.lower()
    forbidden_tokens = (
        "/orders",
        "/order",
        "/submit",
        "/trade",
        "/trades",
        "/sign",
        "/wallet",
        "/auth",
        "/login",
        "clob",
    )
    return any(token in normalized for token in forbidden_tokens)


def _default_public_get_json(url: str) -> Mapping[str, Any]:
    request = urllib.request.Request(url, method="GET", headers={"Accept": "application/json"})
    with urllib.request.urlopen(request, timeout=10) as response:
        body = response.read().decode("utf-8")
    value = json.loads(body)
    if not isinstance(value, Mapping):
        raise ValueError("public read-only response JSON must be an object")
    return value


def _read_only_safety_flags(*, network_used: bool) -> dict[str, Any]:
    value = {
        "local_artifact_only": not network_used,
        "static_artifact_only": not network_used,
        "passive_artifact_only": True,
        "read_only": True,
        "dry_run_control_only": True,
        "paper_only": True,
        "execution_enabling": False,
        "network_used": network_used,
        "external_api_calls_performed": network_used,
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
        "authenticated_endpoint_call_performed": False,
        "browser_automation_added": False,
        "scheduler_or_daemon_added": False,
        "autonomous_live_trading_added": False,
        "allowed_for_live": False,
        "canary_executable_now": False,
        "live_execution_approved": False,
        "real_execution_available": False,
        "live_connector_enabled": False,
        "outcome_resolution_invented": False,
        "price_data_invented": False,
        "pnl_invented": False,
    }
    value["safety_summary"] = trading_core_safety_summary()
    return value
