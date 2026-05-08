import argparse
import json
import re
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


TASK_ID = "PMBOT-SOURCE-010A-WEATHER-MARKET-CLASS-PILOT-READONLY-DISCOVERY"
ROOT = Path(__file__).resolve().parents[2]

ARTIFACT_DIR = "pm_bot/live_readonly/weather_market_discovery"
RAW_FETCH_JSON = "weather_market_raw_fetch_010a.v1.json"
RAW_FETCH_MD = "weather_market_raw_fetch_010a.v1.md"
NORMALIZED_JSON = "weather_market_normalized_candidate_010a.v1.json"
NORMALIZED_MD = "weather_market_normalized_candidate_010a.v1.md"
SOURCE_CAPTURE_JSON = "weather_source_capture_candidate_010a.v1.json"
SOURCE_CAPTURE_MD = "weather_source_capture_candidate_010a.v1.md"
CHECKLIST_JSON = "weather_operator_review_checklist_010a.v1.json"
CHECKLIST_MD = "weather_operator_review_checklist_010a.v1.md"
SOURCE_QUALITY_JSON = "pm_bot/llm/source_quality_observation_candidate_weather_010a.v1.json"
SOURCE_QUALITY_MD = "pm_bot/llm/source_quality_observation_candidate_weather_010a.v1.md"
WORKBENCH_JSON = "pm_bot/workbench/weather_market_discovery_surface_010a.v1.json"
WORKBENCH_MD = "pm_bot/workbench/weather_market_discovery_surface_010a.v1.md"
RESULT_JSON = "docs/PMBOT_SOURCE_010A_RESULT.json"
RESULT_MD = "docs/PMBOT_SOURCE_010A_WEATHER_MARKET_CLASS_PILOT_READONLY_DISCOVERY.md"

HEAD_BEFORE = "b08602399880b89fe9d3798231cc8d9ce3f25d83"
FETCHED_AT_MARKER = "2026-05-08T00:00:00Z_SOURCE_010A_READONLY_FIELD_TEST"
GAMMA_BASE_URL = "https://gamma-api.polymarket.com"
DEFAULT_PAGE_LIMIT = 500
DEFAULT_TIMEOUT_SECONDS = 10
DEFAULT_MAX_CALLS = 5
MAX_CALLS_HARD_CAP = 5
MAX_MARKETS_HARD_CAP = 1

PUBLIC_HEADERS = {
    "Accept": "application/json",
    "User-Agent": "PMBOT-SOURCE-010A-weather-readonly-discovery/1.0",
}

WEATHER_STRONG_MARKERS = (
    "weather.gov",
    "noaa",
    "national weather service",
    "temperature",
    "temperatures",
    "fahrenheit",
    "celsius",
    "precipitation",
    "rainfall",
    "snowfall",
    "heat index",
    "wind speed",
    "wind gust",
    "tropical storm",
    "storm surge",
)

WEATHER_WORD_MARKERS = (
    "rain",
    "snow",
    "hurricane",
    "storm",
    "degrees",
    "degree",
)

WEATHER_WEAK_MARKERS = (
    "heat",
    "cold",
    "wind",
)

FALSE_POSITIVE_MARKERS = (
    "carolina hurricanes",
    "miami heat",
    "stanley cup",
    "nhl",
    "nba",
    "jonas wind",
    "top goal scorer",
    "wind be the top",
)

KNOWN_LOCATION_MARKERS = (
    ("new york city", "New York City"),
    ("nyc", "New York City"),
    ("central park", "Central Park, New York City"),
    ("los angeles", "Los Angeles"),
    ("chicago", "Chicago"),
    ("miami", "Miami"),
    ("phoenix", "Phoenix"),
    ("las vegas", "Las Vegas"),
    ("washington dc", "Washington, DC"),
    ("washington, dc", "Washington, DC"),
    ("boston", "Boston"),
    ("philadelphia", "Philadelphia"),
    ("san francisco", "San Francisco"),
    ("seattle", "Seattle"),
    ("dallas", "Dallas"),
    ("houston", "Houston"),
    ("austin", "Austin"),
    ("denver", "Denver"),
    ("atlanta", "Atlanta"),
)

WEATHER_CHECKLIST_ITEMS = [
    ("verify_exact_polymarket_rules_text", "Verify exact Polymarket rules text."),
    ("verify_location", "Verify location."),
    ("verify_weather_metric", "Verify weather metric."),
    ("verify_unit", "Verify unit."),
    ("verify_threshold_or_condition", "Verify threshold or condition."),
    ("verify_date_or_time_window", "Verify date or time window."),
    ("verify_timezone", "Verify timezone."),
    ("verify_official_weather_source", "Verify official weather source."),
    ("verify_station_or_source_hierarchy", "Verify station or source hierarchy."),
    ("verify_fallback_source", "Verify fallback source."),
    (
        "verify_source_capture_promotion_readiness",
        "Verify whether source capture can be promoted to ready_for_local_review.",
    ),
    ("no_trading_decision", "No trading decision."),
]


class ApiCallCapExceeded(Exception):
    pass


class PublicGammaFetcher:
    def __init__(self, timeout_seconds=DEFAULT_TIMEOUT_SECONDS):
        self.timeout_seconds = timeout_seconds

    def fetch_json(self, url):
        request = urllib.request.Request(url, headers=PUBLIC_HEADERS, method="GET")
        with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
            raw = response.read()
            text = raw.decode("utf-8")
            return json.loads(text)


def _resolve(path, root=ROOT):
    value = Path(path)
    return value if value.is_absolute() else Path(root) / value


def _write_json(path, payload, root=ROOT):
    resolved = _resolve(path, root=root)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    resolved.write_text(
        json.dumps(payload, indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )


def _ascii(value):
    return str(value).encode("ascii", "backslashreplace").decode("ascii")


def _strip_trailing_whitespace(text):
    return "\n".join(line.rstrip() for line in str(text).splitlines())


def _write_text(path, text, root=ROOT):
    resolved = _resolve(path, root=root)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    resolved.write_text(_ascii(_strip_trailing_whitespace(text)) + "\n", encoding="utf-8")


def _load_optional_json(path, root=ROOT):
    resolved = _resolve(path, root=root)
    if not resolved.exists():
        return None
    with resolved.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _safe_list(value):
    return value if isinstance(value, list) else []


def _as_text(value):
    if value is None:
        return ""
    return str(value).strip()


def _dedupe_text_values(values):
    deduped = []
    seen = set()
    for value in values:
        text = _as_text(value)
        if text and text not in seen:
            deduped.append(text)
            seen.add(text)
    return deduped


def _parse_outcomes(value):
    if isinstance(value, list):
        return [_as_text(item) for item in value if _as_text(item)]
    if isinstance(value, str) and value.strip():
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return [value]
        if isinstance(parsed, list):
            return [_as_text(item) for item in parsed if _as_text(item)]
    return []


def _extract_urls(*values):
    urls = []
    seen = set()
    for value in values:
        text = _as_text(value)
        for match in re.findall(r"https?://[^\s)]+", text):
            cleaned = match.rstrip(".,")
            if cleaned not in seen:
                urls.append(cleaned)
                seen.add(cleaned)
    return urls


def _market_text(market):
    fields = [
        market.get("question"),
        market.get("slug"),
        market.get("description"),
        market.get("resolutionSource"),
        market.get("groupItemTitle"),
    ]
    for event in _safe_list(market.get("events")):
        fields.extend(
            [
                event.get("title"),
                event.get("slug"),
                event.get("description"),
                event.get("resolutionSource"),
            ]
        )
        for tag in _safe_list(event.get("tags")):
            if isinstance(tag, dict):
                fields.extend([tag.get("label"), tag.get("slug")])
    return " ".join(_as_text(item) for item in fields)


def _contains_word(text, word):
    return re.search(rf"\b{re.escape(word)}\b", text) is not None


def _looks_like_non_weather_false_positive(lowered):
    return any(marker in lowered for marker in FALSE_POSITIVE_MARKERS)


def _has_weather_marker(lowered):
    if any(marker in lowered for marker in WEATHER_STRONG_MARKERS):
        return True
    if any(_contains_word(lowered, marker) for marker in WEATHER_WORD_MARKERS):
        return True
    if any(_contains_word(lowered, marker) for marker in WEATHER_WEAK_MARKERS):
        return any(
            marker in lowered
            for marker in (
                "weather",
                "temperature",
                "degrees",
                "fahrenheit",
                "celsius",
                "mph",
                "gust",
                "precipitation",
                "rain",
                "snow",
                "storm",
                "hurricane",
                "noaa",
                "nws",
            )
        )
    return False


def _extract_location(title, text):
    lowered = text.lower()
    for marker, location in KNOWN_LOCATION_MARKERS:
        if re.search(rf"\b{re.escape(marker)}\b", lowered):
            return location

    for source_text in (title, text):
        for pattern in (
            r"\bin\s+([A-Z][A-Za-z .'-]{2,60}?)(?:\s+(?:on|by|from|between|during|before|after)\b|[?,.:;\n]|$)",
            r"\bfor\s+([A-Z][A-Za-z .'-]{2,60}?)(?:\s+(?:on|by|from|between|during|before|after)\b|[?,.:;\n]|$)",
            r"\bat\s+([A-Z][A-Za-z .'-]{2,80}?)(?:\s+(?:weather station|station|on|by|from|between|during)\b|[?,.:;\n]|$)",
        ):
            match = re.search(pattern, source_text)
            if match:
                candidate = match.group(1).strip()
                if not candidate.lower().startswith(("least", "most", "any", "the")):
                    return candidate
    return ""


def _extract_metric(text):
    lowered = text.lower()
    if any(marker in lowered for marker in ("temperature", "temperatures", "degrees", "fahrenheit", "celsius", "heat index")):
        return "temperature"
    if any(marker in lowered for marker in ("rainfall", "rain", "precipitation")):
        return "precipitation"
    if any(marker in lowered for marker in ("snowfall", "snow")):
        return "snowfall"
    if any(marker in lowered for marker in ("hurricane", "tropical storm", "storm surge")):
        return "storm_event"
    if any(marker in lowered for marker in ("wind speed", "wind gust", "mph")):
        return "wind"
    if "weather" in lowered:
        return "weather_condition"
    return ""


def _extract_unit(text, metric):
    lowered = text.lower()
    if "fahrenheit" in lowered or "°f" in lowered:
        return "degrees_fahrenheit"
    if "celsius" in lowered or "°c" in lowered:
        return "degrees_celsius"
    if metric == "temperature" and re.search(r"\bdegrees?\b", lowered):
        return "degrees_unspecified_operator_must_verify"
    if metric in {"precipitation", "snowfall"}:
        if re.search(r"\bin(?:ch|ches)?\b", lowered) or "inches" in lowered:
            return "inches"
        if re.search(r"\bmm\b|millimeters?", lowered):
            return "millimeters"
    if metric == "wind" and re.search(r"\bmph\b|miles per hour", lowered):
        return "mph"
    if metric == "storm_event":
        return "event_occurrence"
    return ""


def _extract_threshold_or_condition(text):
    patterns = (
        r"(?:at least|at or above|above|over|greater than|more than|exceed(?:s|ed)?|reach(?:es|ed)?|hit(?:s)?)\s+\d+(?:\.\d+)?\s*(?:degrees?|fahrenheit|celsius|°f|°c|inches|inch|mm|mph)?",
        r"(?:below|under|less than|at or below)\s+\d+(?:\.\d+)?\s*(?:degrees?|fahrenheit|celsius|°f|°c|inches|inch|mm|mph)?",
        r"\d+(?:\.\d+)?\s*(?:degrees?|fahrenheit|celsius|°f|°c|inches|inch|mm|mph)\s*(?:or more|or less|or higher|or lower)?",
        r"(?:category|cat\.?)\s+\d+",
        r"(?:will|does|do)\s+.+?\s+(?:rain|snow|make landfall|form|hit|reach)",
    )
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return _as_text(match.group(0))
    return ""


def _extract_date_or_time_window(text):
    patterns = (
        r"\b(?:on|by|before|after)\s+[A-Z][a-z]+\s+\d{1,2}(?:,\s*\d{4})?(?:\s+at\s+\d{1,2}(?::\d{2})?\s*(?:AM|PM|ET|PT|CT|MT|UTC)?)?",
        r"\b(?:on|by|before|after)\s+\d{4}-\d{2}-\d{2}",
        r"\bbetween\s+.+?\s+and\s+.+?(?:[?.;,\n]|$)",
        r"\bfrom\s+.+?\s+to\s+.+?(?:[?.;,\n]|$)",
        r"\b(?:through|until)\s+[A-Z][a-z]+\s+\d{1,2}(?:,\s*\d{4})?",
        r"\b\d{1,2}:\d{2}\s*(?:AM|PM|ET|PT|CT|MT|UTC)\b",
        r"\b(?:end of|end-of)\s+[A-Z][a-z]+(?:\s+\d{4})?",
    )
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return _as_text(match.group(0))
    return ""


def _extract_timezone(text):
    match = re.search(r"\b(UTC|ET|EDT|EST|CT|CDT|CST|MT|MDT|MST|PT|PDT|PST)\b", text)
    if match:
        return match.group(1)
    if re.search(r"\blocal time\b", text, flags=re.IGNORECASE):
        return "local_time_operator_must_verify"
    return ""


def _extract_official_weather_source(text):
    urls = _extract_urls(text)
    weather_urls = [
        url
        for url in urls
        if any(marker in url.lower() for marker in ("weather.gov", "noaa.gov", "nws"))
    ]
    if weather_urls:
        return weather_urls[0]
    for marker in ("National Weather Service", "NOAA", "NWS", "weather.gov"):
        if re.search(rf"\b{re.escape(marker)}\b", text, flags=re.IGNORECASE):
            return marker
    return ""


def _extract_station_or_source_hierarchy(text):
    patterns = (
        r"(?:weather station|station)\s+[A-Za-z0-9 .,'-]{2,80}",
        r"(?:as measured by|according to)\s+[A-Za-z0-9 .,'/-]{2,100}",
        r"(?:National Weather Service|NOAA|NWS)\s+[A-Za-z0-9 .,'/-]{0,80}",
        r"Central Park(?: weather station)?",
    )
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return _as_text(match.group(0))
    return ""


def _extract_fallback_source(text):
    match = re.search(
        r"(?:fallback|if .*? unavailable|if .*? not available).{0,160}",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if match:
        return " ".join(_as_text(match.group(0)).split())
    return ""


def _extract_weather_fields(market):
    title = _as_text(market.get("question"))
    description = _as_text(market.get("description"))
    resolution_source = _as_text(market.get("resolutionSource"))
    text = "\n".join(part for part in [title, description, resolution_source] if part)
    metric = _extract_metric(text)
    return {
        "location": _extract_location(title, text),
        "weather_metric": metric,
        "unit": _extract_unit(text, metric),
        "threshold_or_condition": _extract_threshold_or_condition(text),
        "date_or_time_window": _extract_date_or_time_window(text),
        "timezone": _extract_timezone(text),
        "official_weather_source_candidate": _extract_official_weather_source(text),
        "station_or_source_hierarchy": _extract_station_or_source_hierarchy(text),
        "fallback_source_candidate": _extract_fallback_source(text),
        "source_urls_or_references": _extract_urls(description, resolution_source),
    }


def _basic_missing_weather_fields(fields):
    required = [
        "location",
        "weather_metric",
        "threshold_or_condition",
        "date_or_time_window",
    ]
    return [field for field in required if fields.get(field) in ("", None, [])]


def _normalized_missing_weather_fields(candidate):
    required = [
        "market_id",
        "title_or_question",
        "description",
        "rules_text",
        "outcomes",
        "location",
        "weather_metric",
        "unit",
        "threshold_or_condition",
        "date_or_time_window",
        "timezone",
        "official_weather_source_candidate",
        "station_or_source_hierarchy",
    ]
    return [field for field in required if candidate.get(field) in ("", None, [])]


def _inspect_market(market):
    title = _as_text(market.get("question"))
    text = _market_text(market)
    lowered = text.lower()
    fields = _extract_weather_fields(market)
    active = market.get("active") is True
    closed = market.get("closed") is True
    weather_marker = _has_weather_marker(lowered)
    false_positive = _looks_like_non_weather_false_positive(lowered)
    missing_basic = _basic_missing_weather_fields(fields)

    if not active or closed:
        reason = "market_not_active_or_closed"
    elif not title:
        reason = "missing_title_or_question"
    elif not weather_marker:
        reason = "no_weather_marker"
    elif false_positive:
        reason = "weather_word_false_positive_or_sports_context"
    elif missing_basic:
        reason = "weather_marker_but_missing_basic_fields"
    else:
        reason = "suitable_weather_market_candidate"

    return {
        "market_id": _as_text(market.get("id")) or None,
        "market_slug": _as_text(market.get("slug")) or None,
        "market_title_or_question": title or None,
        "active": active,
        "closed": closed,
        "reason": reason,
        "weather_marker_detected": weather_marker,
        "missing_basic_fields": missing_basic,
        "extracted_weather_fields": fields,
    }


def _is_suitable_inspection(inspection):
    return inspection["reason"] == "suitable_weather_market_candidate"


def _market_list_url(offset, limit=DEFAULT_PAGE_LIMIT):
    query = urllib.parse.urlencode(
        {
            "active": "true",
            "closed": "false",
            "limit": str(limit),
            "offset": str(offset),
        }
    )
    return f"{GAMMA_BASE_URL}/markets?{query}"


def _empty_safety_summary(network_allowed, network_call_count):
    return {
        "network_allowed_explicitly": network_allowed,
        "public_readonly_only": True,
        "network_calls_performed": network_call_count,
        "polymarket_api_calls_performed": network_call_count,
        "non_polymarket_public_source_calls_performed": 0,
        "openrouter_calls_performed": 0,
        "authenticated_endpoints_used": False,
        "auth_headers_used": False,
        "wallet_or_private_key_accessed": False,
        "orders_created": False,
        "simulated_trade_created": False,
        "selected_side": None,
        "stake_amount": None,
        "position_sizing_created": False,
        "outcome_checked": False,
        "outcome_known": False,
        "source_scoring_performed": False,
        "source_ranking_updated": False,
        "profit_or_pnl_recorded": False,
        "trading_runtime_changed": False,
        "dispatcher_changed": False,
        "background_worker_created": False,
        "queue_mutated": False,
        "browser_automation_used": False,
        "canonical_packets_mutated": False,
        "market_action_guidance_generated": False,
        "probability_ev_edge_confidence_generated": False,
        "side_selection_generated": False,
        "operator_review_required": True,
        "no_trading_authority": True,
        "no_market_action_guidance": True,
        "ready_for_autonomous_trading": False,
    }


def build_dry_run_status(max_markets=MAX_MARKETS_HARD_CAP, max_calls=DEFAULT_MAX_CALLS):
    _validate_max_markets(max_markets)
    _validate_max_calls(max_calls)
    return {
        "schema_version": "weather_market_discovery_dry_run.v1",
        "task_id": TASK_ID,
        "status": "dry_run_no_network",
        "mode": "dry_run",
        "network_allowed_explicitly": False,
        "network_calls_performed": 0,
        "polymarket_api_calls_performed": 0,
        "fetch_performed": False,
        "max_markets": max_markets,
        "max_markets_hard_cap": MAX_MARKETS_HARD_CAP,
        "max_calls": max_calls,
        "max_calls_hard_cap": MAX_CALLS_HARD_CAP,
        "planned_public_readonly_endpoints": [f"{GAMMA_BASE_URL}/markets"],
        "write_scope": "none_unless_fetch_one_and_write_are_passed",
        "operator_review_required": True,
        "planned_capture_status": "draft",
        "auto_promote_to_ready_for_local_review": False,
        "safety_summary": _empty_safety_summary(False, 0),
    }


def build_summary_only(root=ROOT):
    result = _load_optional_json(RESULT_JSON, root=root)
    if result is None:
        return {
            "schema_version": "weather_market_discovery_summary_only.v1",
            "task_id": TASK_ID,
            "status": "summary_only_no_artifacts",
            "network_calls_performed": 0,
            "polymarket_api_calls_performed": 0,
            "openrouter_calls_performed": 0,
            "operator_review_required": True,
        }
    return {
        "schema_version": "weather_market_discovery_summary_only.v1",
        "task_id": TASK_ID,
        "status": "summary_only",
        "network_calls_performed": 0,
        "polymarket_api_calls_performed": 0,
        "selected_market_id": result.get("selected_market_id"),
        "selected_market_title_or_question": result.get("selected_market_title_or_question"),
        "fetch_status": result.get("fetch_status"),
        "source_capture_candidate_created": result.get("source_capture_candidate_created"),
        "operator_review_required": result.get("operator_review_required"),
    }


def _validate_max_markets(max_markets):
    if max_markets != MAX_MARKETS_HARD_CAP:
        raise ValueError("SOURCE-010A max_markets hard cap is exactly 1")


def _validate_max_calls(max_calls):
    if max_calls < 1 or max_calls > MAX_CALLS_HARD_CAP:
        raise ValueError("SOURCE-010A max_calls must be between 1 and 5")


def _validate_page_limit(page_limit):
    if page_limit < 1 or page_limit > DEFAULT_PAGE_LIMIT:
        raise ValueError(f"--page-limit must be between 1 and {DEFAULT_PAGE_LIMIT}")


def _fetch_logged(fetcher, url, log, max_calls):
    if log["network_call_count"] >= max_calls:
        raise ApiCallCapExceeded("SOURCE-010A Polymarket/Gamma API call cap reached")
    log["network_call_count"] += 1
    log["endpoint_or_url_used"].append(url)
    return fetcher.fetch_json(url)


def discover_one_weather_market(
    fetcher=None,
    max_markets=MAX_MARKETS_HARD_CAP,
    max_calls=DEFAULT_MAX_CALLS,
    page_limit=DEFAULT_PAGE_LIMIT,
):
    _validate_max_markets(max_markets)
    _validate_max_calls(max_calls)
    _validate_page_limit(page_limit)
    fetcher = fetcher or PublicGammaFetcher()
    log = {"network_call_count": 0, "endpoint_or_url_used": []}
    inspected = []
    inspected_market_count = 0
    reason_counts = {}

    try:
        page_index = 0
        while log["network_call_count"] < max_calls:
            offset = page_index * page_limit
            url = _market_list_url(offset=offset, limit=page_limit)
            markets = _fetch_logged(fetcher, url, log, max_calls)
            if not isinstance(markets, list):
                return _blocked_result(
                    log,
                    "Gamma markets endpoint returned a non-list payload.",
                    inspected,
                )
            if not markets:
                break
            for market in markets:
                inspection = _inspect_market(market)
                inspected_market_count += 1
                reason = inspection["reason"]
                reason_counts[reason] = reason_counts.get(reason, 0) + 1
                if inspection["weather_marker_detected"] or reason != "no_weather_marker":
                    inspected.append(inspection)
                if not _is_suitable_inspection(inspection):
                    continue
                return {
                    "status": "selected",
                    "fetch_status": "selected",
                    "raw_market_payload": market,
                    "selected_market": market,
                    "selection_reason": (
                        "Open public Gamma market metadata contains weather markers and "
                        "basic location, metric, threshold or condition, and time-window fields."
                    ),
                    "inspected_candidates": inspected,
                    "inspected_market_count": inspected_market_count,
                    "inspected_candidate_reason_counts": reason_counts,
                    **log,
                }
            if len(markets) < page_limit:
                break
            page_index += 1
        return {
            "status": "no_suitable_weather_market_found",
            "fetch_status": "no_suitable_weather_market_found",
            "raw_market_payload": None,
            "selected_market": None,
            "selection_reason": "No inspected market met the basic weather pilot criteria.",
            "inspected_candidates": inspected,
            "inspected_market_count": inspected_market_count,
            "inspected_candidate_reason_counts": reason_counts,
            **log,
        }
    except ApiCallCapExceeded as exc:
        return _blocked_result(log, str(exc), inspected)
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError) as exc:
        return _blocked_result(log, f"{exc.__class__.__name__}: {exc}", inspected)


def _blocked_result(log, reason, inspected):
    return {
        "status": "blocked_or_unavailable",
        "fetch_status": "blocked_or_unavailable",
        "blocked_reason": reason,
        "raw_market_payload": None,
        "selected_market": None,
        "selection_reason": reason,
        "inspected_candidates": inspected,
        "inspected_market_count": len(inspected),
        "inspected_candidate_reason_counts": {"blocked_or_unavailable": 1},
        **log,
    }


def _sanitize_raw_market_payload(value):
    if isinstance(value, dict):
        sanitized = {}
        for key, item in value.items():
            if key == "context_description":
                sanitized[key] = "[removed_platform_context_not_used_for_source_rules_capture]"
            elif key == "eventMetadata" and isinstance(item, dict):
                sanitized[key] = _sanitize_raw_market_payload(item)
            else:
                sanitized[key] = _sanitize_raw_market_payload(item)
        return sanitized
    if isinstance(value, list):
        return [_sanitize_raw_market_payload(item) for item in value]
    return value


def build_raw_fetch_artifact(discovery):
    selected_market = discovery.get("selected_market") or {}
    selected_market_id = _as_text(selected_market.get("id")) or None
    selected_slug = _as_text(selected_market.get("slug")) or None
    selected_title = _as_text(selected_market.get("question")) or None
    network_count = discovery.get("network_call_count", 0)
    raw_payload = discovery.get("raw_market_payload")
    if raw_payload is None:
        raw_payload = {
            "inspected_candidate_summaries": discovery.get("inspected_candidates", []),
            "note": "No selected weather market raw payload because no suitable candidate was found.",
        }
    return {
        "schema_version": "weather_market_raw_fetch_010a.v1",
        "task_id": TASK_ID,
        "fetch_status": discovery.get("fetch_status"),
        "fetched_at_marker": FETCHED_AT_MARKER,
        "network_allowed_explicitly": True,
        "public_readonly_only": True,
        "authenticated_endpoints_used": False,
        "auth_headers_used": False,
        "wallet_or_private_key_accessed": False,
        "orders_created": False,
        "endpoint_or_url_used": discovery.get("endpoint_or_url_used", []),
        "network_call_count": network_count,
        "polymarket_api_calls_performed": network_count,
        "raw_market_payload": _sanitize_raw_market_payload(raw_payload),
        "raw_market_payload_redactions": [
            "platform context_description fields removed; not used for source/rules capture"
        ],
        "selected_market_id": selected_market_id,
        "selected_market_slug": selected_slug,
        "selected_market_title_or_question": selected_title,
        "selection_reason": discovery.get("selection_reason"),
        "inspected_candidate_count": discovery.get(
            "inspected_market_count",
            len(discovery.get("inspected_candidates", [])),
        ),
        "inspected_weather_candidate_summary_count": len(
            discovery.get("inspected_candidates", [])
        ),
        "inspected_candidate_reason_counts": discovery.get(
            "inspected_candidate_reason_counts",
            {},
        ),
        "inspected_candidates": discovery.get("inspected_candidates", []),
        "blocked_reason": discovery.get("blocked_reason"),
        "no_market_action_guidance": True,
        "safety_summary": _empty_safety_summary(True, network_count),
    }


def build_normalized_candidate(discovery):
    market = discovery.get("selected_market") or {}
    description = _as_text(market.get("description"))
    resolution_source = _as_text(market.get("resolutionSource"))
    fields = _extract_weather_fields(market)
    candidate = {
        "schema_version": "weather_market_normalized_candidate_010a.v1",
        "task_id": TASK_ID,
        "market_id": _as_text(market.get("id")) or None,
        "market_class": "weather",
        "title_or_question": _as_text(market.get("question")) or None,
        "description": description,
        "rules_text": description,
        "resolution_source_text": resolution_source,
        "outcomes": _parse_outcomes(market.get("outcomes")),
        "location": fields["location"],
        "weather_metric": fields["weather_metric"],
        "unit": fields["unit"],
        "threshold_or_condition": fields["threshold_or_condition"],
        "date_or_time_window": fields["date_or_time_window"],
        "timezone": fields["timezone"],
        "official_weather_source_candidate": fields["official_weather_source_candidate"],
        "station_or_source_hierarchy": fields["station_or_source_hierarchy"],
        "fallback_source_candidate": fields["fallback_source_candidate"],
        "source_urls_or_references": fields["source_urls_or_references"],
        "unresolved_source_questions": [],
        "missing_fields": [],
        "operator_review_required": True,
        "planned_capture_status": "draft",
        "auto_promote_to_ready_for_local_review": False,
        "no_market_action_guidance": True,
        "no_trading_authority": True,
    }
    candidate["missing_fields"] = _normalized_missing_weather_fields(candidate)
    candidate["unresolved_source_questions"] = _unresolved_source_questions(candidate)
    return candidate


def build_empty_normalized_candidate(discovery):
    candidate = {
        "schema_version": "weather_market_normalized_candidate_010a.v1",
        "task_id": TASK_ID,
        "market_id": None,
        "market_class": "weather",
        "title_or_question": None,
        "description": "",
        "rules_text": "",
        "resolution_source_text": "",
        "outcomes": [],
        "location": "",
        "weather_metric": "",
        "unit": "",
        "threshold_or_condition": "",
        "date_or_time_window": "",
        "timezone": "",
        "official_weather_source_candidate": "",
        "station_or_source_hierarchy": "",
        "fallback_source_candidate": "",
        "source_urls_or_references": [],
        "unresolved_source_questions": [
            "No suitable public read-only weather market candidate was selected.",
            discovery.get("blocked_reason", "") or "No matching market met pilot criteria.",
        ],
        "missing_fields": [
            "market_id",
            "title_or_question",
            "description",
            "rules_text",
            "resolution_source_text",
            "outcomes",
            "location",
            "weather_metric",
            "unit",
            "threshold_or_condition",
            "date_or_time_window",
            "timezone",
            "official_weather_source_candidate",
            "station_or_source_hierarchy",
        ],
        "operator_review_required": True,
        "planned_capture_status": "draft",
        "auto_promote_to_ready_for_local_review": False,
        "no_market_action_guidance": True,
        "no_trading_authority": True,
    }
    return candidate


def _unresolved_source_questions(candidate):
    questions = []
    missing = set(candidate["missing_fields"])
    if "unit" in missing:
        questions.append("Operator must verify the measurement unit from exact market rules.")
    if "timezone" in missing:
        questions.append("Operator must verify the market time window timezone.")
    if "official_weather_source_candidate" in missing:
        questions.append("Operator must identify the official weather source before promotion.")
    if "station_or_source_hierarchy" in missing:
        questions.append("Operator must verify station or source hierarchy.")
    if not candidate["fallback_source_candidate"]:
        questions.append("Operator must verify fallback source or cancellation handling if applicable.")
    return questions


def build_source_capture_candidate(normalized, raw_path):
    source_references = _dedupe_text_values(
        [
            normalized["resolution_source_text"],
            normalized["official_weather_source_candidate"],
            normalized["station_or_source_hierarchy"],
            normalized["fallback_source_candidate"],
            *normalized["source_urls_or_references"],
        ]
    )
    return {
        "contract_version": "weather_source_capture_candidate_010a.v1",
        "task_id": TASK_ID,
        "market_id": normalized["market_id"],
        "market_class": "weather",
        "full_market_resolution_criteria_text": normalized["rules_text"],
        "full_resolution_rules": normalized["rules_text"],
        "official_source_references": source_references,
        "official_source_urls_or_rule_references": normalized["source_urls_or_references"],
        "source_timestamps": {
            "fetched_at_marker": FETCHED_AT_MARKER,
            "market_date_or_time_window": normalized["date_or_time_window"],
        },
        "source_reliability_review": (
            "candidate_only_operator_must_verify_direct_polymarket_rules_and_weather_source"
        ),
        "reviewed_local_evidence_references": [raw_path],
        "non_placeholder_evidence_notes": [
            "Public Gamma metadata captured for operator source/rules review only."
        ],
        "unresolved_source_questions": normalized["unresolved_source_questions"],
        "planned_source_capture_status": "draft",
        "planned_capture_status": "draft",
        "operator_review_required": True,
        "direct_rules_text_captured": bool(normalized["rules_text"]),
        "official_weather_source_identified": bool(
            normalized["official_weather_source_candidate"]
        ),
        "station_or_source_hierarchy_identified": bool(
            normalized["station_or_source_hierarchy"]
        ),
        "auto_fill_allowed_only_as_draft": True,
        "auto_promote_to_ready_for_local_review": False,
        "no_market_action_guidance": True,
        "no_trading_authority": True,
    }


def build_operator_checklist(normalized):
    return {
        "contract_version": "weather_operator_review_checklist_010a.v1",
        "task_id": TASK_ID,
        "market_id": normalized["market_id"],
        "market_class": "weather",
        "title_or_question": normalized["title_or_question"],
        "operator_review_required": True,
        "planned_capture_status": "draft",
        "auto_promote_to_ready_for_local_review": False,
        "checklist": [
            {
                "check_id": check_id,
                "review_prompt": prompt,
                "required": True,
                "status": "unchecked",
            }
            for check_id, prompt in WEATHER_CHECKLIST_ITEMS
        ],
        "no_market_action_guidance": True,
        "no_trading_authority": True,
    }


def build_source_quality_observation_candidate(normalized):
    source_ids = []
    source_types = []
    source_roles = []

    if normalized["market_id"]:
        source_ids.append(f"gamma_market_metadata:{normalized['market_id']}")
        source_types.append("public_polymarket_gamma_metadata")
        source_roles.append(
            {
                "source_id": f"gamma_market_metadata:{normalized['market_id']}",
                "roles": ["market_metadata_source"],
            }
        )
    if normalized["rules_text"]:
        source_ids.append(f"gamma_market_rules:{normalized['market_id']}")
        source_types.append("public_polymarket_market_description")
        source_roles.append(
            {
                "source_id": f"gamma_market_rules:{normalized['market_id']}",
                "roles": ["market_rules_source"],
            }
        )
    if normalized["official_weather_source_candidate"]:
        source_ids.append(normalized["official_weather_source_candidate"])
        source_types.append("official_weather_source_candidate")
        source_roles.append(
            {
                "source_id": normalized["official_weather_source_candidate"],
                "roles": ["official_weather_source_candidate"],
            }
        )
    if normalized["station_or_source_hierarchy"]:
        source_ids.append(normalized["station_or_source_hierarchy"])
        source_types.append("station_or_measurement_source_candidate")
        source_roles.append(
            {
                "source_id": normalized["station_or_source_hierarchy"],
                "roles": ["station_or_measurement_source_candidate"],
            }
        )
    if normalized["fallback_source_candidate"]:
        source_ids.append(normalized["fallback_source_candidate"])
        source_types.append("fallback_weather_source_candidate")
        source_roles.append(
            {
                "source_id": normalized["fallback_source_candidate"],
                "roles": ["fallback_weather_source_candidate"],
            }
        )
    if normalized["unresolved_source_questions"] or not source_roles:
        source_ids.append("unresolved_weather_source_questions")
        source_types.append("unresolved_source")
        source_roles.append(
            {
                "source_id": "unresolved_weather_source_questions",
                "roles": ["unresolved_source"],
            }
        )

    return {
        "schema_version": "source_quality_observation_candidate_weather_010a.v1",
        "task_id": TASK_ID,
        "market_id": normalized["market_id"],
        "market_class": "weather",
        "source_ids_observed": _dedupe_text_values(source_ids),
        "source_types_observed": _dedupe_text_values(source_types),
        "source_roles": source_roles,
        "source_quality_status": "pending_future_capture_and_outcome_review",
        "outcome_known": False,
        "source_scoring_performed": False,
        "source_ranking_updated": False,
        "trading_profit_used_for_scoring": False,
        "operator_review_required": True,
        "notes": [
            "Weather source-quality observation is candidate-only until SOURCE-010B and future outcome review.",
            "No source scoring or ranking is performed in SOURCE-010A.",
        ],
    }


def build_workbench_surface(normalized, result, artifacts):
    return {
        "schema_version": "weather_market_discovery_surface_010a.v1",
        "task_id": TASK_ID,
        "market_class": "weather",
        "selected_market_id": normalized["market_id"],
        "selected_market_title_or_question": normalized["title_or_question"],
        "discovery_status": result["fetch_status"],
        "normalized_candidate_available": bool(normalized["market_id"]),
        "source_capture_candidate_available": bool(normalized["market_id"]),
        "operator_checklist_available": artifacts.get("operator_checklist") is not None,
        "source_quality_observation_candidate_available": bool(normalized["market_id"]),
        "operator_review_required": True,
        "next_operator_actions": _next_operator_actions(normalized, result),
        "no_market_action_guidance": True,
        "no_trading_authority": True,
    }


def _next_operator_actions(normalized, result):
    if normalized["market_id"]:
        return [
            "Review exact Polymarket rules text.",
            "Verify weather location, metric, unit, threshold or condition, time window, and timezone.",
            "Verify official weather source, station hierarchy, fallback source, and unresolved source questions.",
            "Prepare SOURCE-010B draft capture only after operator review.",
        ]
    return [
        "Review inspected candidate reasons.",
        "Retry weather discovery later if the operator still wants a weather pilot candidate.",
        f"Current fetch_status: {result['fetch_status']}.",
    ]


def _pipeline_snapshot(root=ROOT):
    gate = _load_optional_json("pm_bot/llm/post_capture_batch_readiness_gate.v1.json", root=root)
    ingest = _load_optional_json(
        "pm_bot/llm/manual_resolution_source_capture_ingest_result.v1.json",
        root=root,
    )
    gate = gate or {}
    ingest = ingest or {}
    return {
        "real_ingested_template_count": gate.get(
            "real_ingested_template_count",
            ingest.get("real_ingested_template_count"),
        ),
        "draft_ingested_template_count": gate.get(
            "draft_ingested_template_count",
            ingest.get("draft_ingested_template_count"),
        ),
        "ready_ingested_template_count": gate.get("ready_ingested_template_count"),
        "future_live_002_allowed": gate.get("future_live_002_allowed"),
    }


def build_result_doc(discovery, normalized, files_created, root=ROOT):
    selected = discovery.get("selected_market") or {}
    fetch_status = discovery.get("fetch_status")
    if fetch_status == "selected":
        status = "completed_local"
    elif fetch_status == "no_suitable_weather_market_found":
        status = "completed_no_suitable_weather_market_found"
    else:
        status = "blocked_or_unavailable"
    pipeline = _pipeline_snapshot(root=root)
    return {
        "task_id": TASK_ID,
        "status": status,
        "head_before": HEAD_BEFORE,
        "head_after": "reported_in_final_response_after_commit_or_push",
        "selected_market_id": _as_text(selected.get("id")) or None,
        "selected_market_title_or_question": _as_text(selected.get("question")) or None,
        "market_class": "weather",
        "fetch_status": fetch_status,
        "network_allowed_explicitly": True,
        "polymarket_api_calls_performed": discovery.get("network_call_count", 0),
        "non_polymarket_public_source_calls_performed": 0,
        "authenticated_endpoints_used": False,
        "auth_headers_used": False,
        "wallet_or_private_key_accessed": False,
        "orders_created": False,
        "openrouter_calls_performed": 0,
        "simulated_trade_created": False,
        "selected_side": None,
        "stake_amount": None,
        "position_sizing_created": False,
        "outcome_checked": False,
        "outcome_known": False,
        "source_scoring_performed": False,
        "source_ranking_updated": False,
        "profit_or_pnl_recorded": False,
        "trading_runtime_changed": False,
        "dispatcher_changed": False,
        "background_worker_created": False,
        "queue_mutated": False,
        "browser_automation_used": False,
        "canonical_packets_mutated": False,
        "market_action_guidance_generated": False,
        "probability_ev_edge_confidence_generated": False,
        "side_selection_generated": False,
        "source_capture_candidate_created": bool(normalized["market_id"]),
        "operator_review_required": True,
        "source_quality_observation_candidate_created": bool(normalized["market_id"]),
        "future_live_002_allowed": False,
        "ready_for_autonomous_trading": False,
        "real_ingested_template_count_preserved_or_after": pipeline.get(
            "real_ingested_template_count"
        ),
        "draft_ingested_template_count_preserved_or_after": pipeline.get(
            "draft_ingested_template_count"
        ),
        "ready_ingested_template_count_after": pipeline.get("ready_ingested_template_count"),
        "tests_passed": [],
        "tests_failed": [],
        "files_created": files_created,
        "files_modified": [],
        "next_recommended_action": (
            "PMBOT-SOURCE-010B-WEATHER-DRAFT-CAPTURE-AUTOFILL-FROM-READONLY-CANDIDATE"
            if normalized["market_id"]
            else "retry weather discovery if no suitable market was found"
        ),
    }


def render_raw_fetch_md(raw):
    return "\n".join(
        [
            "# PMBOT SOURCE-010A Weather Raw Fetch",
            "",
            f"- task_id: {raw['task_id']}",
            f"- fetch_status: {raw['fetch_status']}",
            f"- selected_market_id: {raw['selected_market_id']}",
            f"- selected_market_title_or_question: {raw['selected_market_title_or_question']}",
            f"- network_call_count: {raw['network_call_count']}",
            f"- inspected_candidate_count: {raw['inspected_candidate_count']}",
            "- network_allowed_explicitly: true",
            "- public_readonly_only: true",
            "- authenticated_endpoints_used: false",
            "- auth_headers_used: false",
            "- wallet_or_private_key_accessed: false",
            "- orders_created: false",
            "- no_market_action_guidance: true",
            "",
            "## Endpoints",
            "",
            *[f"- {url}" for url in raw["endpoint_or_url_used"]],
            "",
            "## Safety",
            "",
            "- no trading decision",
            "- no probability, EV, edge, confidence, or side selection guidance",
            "- no wallet, order, runtime, dispatcher, background worker, queue, browser, or canonical packet changes",
        ]
    )


def render_normalized_md(candidate):
    return "\n".join(
        [
            "# PMBOT SOURCE-010A Weather Normalized Candidate",
            "",
            f"- task_id: {candidate['task_id']}",
            f"- market_id: {candidate['market_id']}",
            f"- market_class: {candidate['market_class']}",
            f"- title_or_question: {candidate['title_or_question']}",
            f"- location: {candidate['location']}",
            f"- weather_metric: {candidate['weather_metric']}",
            f"- unit: {candidate['unit']}",
            f"- threshold_or_condition: {candidate['threshold_or_condition']}",
            f"- date_or_time_window: {candidate['date_or_time_window']}",
            f"- timezone: {candidate['timezone']}",
            f"- official_weather_source_candidate: {candidate['official_weather_source_candidate']}",
            f"- station_or_source_hierarchy: {candidate['station_or_source_hierarchy']}",
            f"- planned_capture_status: {candidate['planned_capture_status']}",
            "- operator_review_required: true",
            "- auto_promote_to_ready_for_local_review: false",
            "",
            "## Missing Fields",
            "",
            *[f"- {field}" for field in candidate["missing_fields"]],
            "",
            "## Unresolved Source Questions",
            "",
            *[f"- {question}" for question in candidate["unresolved_source_questions"]],
            "",
            "## Safety",
            "",
            "- no market action guidance",
            "- no trading authority",
        ]
    )


def render_source_capture_md(candidate):
    return "\n".join(
        [
            "# PMBOT SOURCE-010A Weather Source Capture Candidate",
            "",
            f"- task_id: {candidate['task_id']}",
            f"- market_id: {candidate['market_id']}",
            f"- market_class: {candidate['market_class']}",
            f"- planned_source_capture_status: {candidate['planned_source_capture_status']}",
            f"- planned_capture_status: {candidate['planned_capture_status']}",
            f"- direct_rules_text_captured: {str(candidate['direct_rules_text_captured']).lower()}",
            f"- official_weather_source_identified: {str(candidate['official_weather_source_identified']).lower()}",
            f"- station_or_source_hierarchy_identified: {str(candidate['station_or_source_hierarchy_identified']).lower()}",
            "- operator_review_required: true",
            "- auto_fill_allowed_only_as_draft: true",
            "- auto_promote_to_ready_for_local_review: false",
            "",
            "## Reviewed Local Evidence",
            "",
            *[f"- {path}" for path in candidate["reviewed_local_evidence_references"]],
            "",
            "## Unresolved Source Questions",
            "",
            *[f"- {question}" for question in candidate["unresolved_source_questions"]],
            "",
            "## Safety",
            "",
            "- no market action guidance",
            "- no trading authority",
        ]
    )


def render_operator_checklist_md(checklist):
    lines = [
        "# PMBOT SOURCE-010A Weather Operator Review Checklist",
        "",
        f"- task_id: {checklist['task_id']}",
        f"- market_id: {checklist['market_id']}",
        f"- market_class: {checklist['market_class']}",
        f"- planned_capture_status: {checklist['planned_capture_status']}",
        "- operator_review_required: true",
        "- auto_promote_to_ready_for_local_review: false",
        "",
        "## Checklist",
        "",
    ]
    for item in checklist["checklist"]:
        lines.append(f"- [ ] {item['review_prompt']}")
    lines.extend(
        [
            "",
            "## Safety Boundary",
            "",
            "- no market action guidance",
            "- no trading decision",
            "- no execution authority",
        ]
    )
    return "\n".join(lines)


def render_source_quality_md(candidate):
    lines = [
        "# PMBOT SOURCE-010A Weather Source Quality Observation Candidate",
        "",
        f"- task_id: {candidate['task_id']}",
        f"- market_id: {candidate['market_id']}",
        f"- market_class: {candidate['market_class']}",
        f"- source_quality_status: {candidate['source_quality_status']}",
        "- outcome_known: false",
        "- source_scoring_performed: false",
        "- source_ranking_updated: false",
        "- trading_profit_used_for_scoring: false",
        "- operator_review_required: true",
        "",
        "## Source Roles",
        "",
    ]
    for source in candidate["source_roles"]:
        lines.append(f"- {source['source_id']}: {', '.join(source['roles'])}")
    lines.extend(
        [
            "",
            "## Notes",
            "",
            *[f"- {note}" for note in candidate["notes"]],
        ]
    )
    return "\n".join(lines)


def render_workbench_md(surface):
    return "\n".join(
        [
            "# PMBOT SOURCE-010A Weather Discovery Workbench Surface",
            "",
            f"- task_id: {surface['task_id']}",
            f"- market_class: {surface['market_class']}",
            f"- selected_market_id: {surface['selected_market_id']}",
            f"- selected_market_title_or_question: {surface['selected_market_title_or_question']}",
            f"- discovery_status: {surface['discovery_status']}",
            f"- normalized_candidate_available: {str(surface['normalized_candidate_available']).lower()}",
            f"- source_capture_candidate_available: {str(surface['source_capture_candidate_available']).lower()}",
            f"- operator_checklist_available: {str(surface['operator_checklist_available']).lower()}",
            f"- source_quality_observation_candidate_available: {str(surface['source_quality_observation_candidate_available']).lower()}",
            "- operator_review_required: true",
            "- no_market_action_guidance: true",
            "- no_trading_authority: true",
            "",
            "## Next Operator Actions",
            "",
            *[f"- {action}" for action in surface["next_operator_actions"]],
        ]
    )


def render_result_md(result, normalized):
    return "\n".join(
        [
            "# PMBOT SOURCE-010A Weather Market Class Pilot Read-Only Discovery",
            "",
            f"- task_id: {result['task_id']}",
            f"- status: {result['status']}",
            f"- fetch_status: {result['fetch_status']}",
            f"- selected_market_id: {result['selected_market_id']}",
            f"- selected_market_title_or_question: {result['selected_market_title_or_question']}",
            f"- market_class: {result['market_class']}",
            f"- polymarket_api_calls_performed: {result['polymarket_api_calls_performed']}",
            "- non_polymarket_public_source_calls_performed: 0",
            "- network_allowed_explicitly: true",
            "- authenticated_endpoints_used: false",
            "- auth_headers_used: false",
            "- wallet_or_private_key_accessed: false",
            "- orders_created: false",
            "- openrouter_calls_performed: 0",
            "- simulated_trade_created: false",
            "- selected_side: null",
            "- stake_amount: null",
            "- canonical_packets_mutated: false",
            "- planned_capture_status: draft",
            "- operator_review_required: true",
            "",
            "## Candidate Summary",
            "",
            f"- location: {normalized['location']}",
            f"- weather_metric: {normalized['weather_metric']}",
            f"- unit: {normalized['unit']}",
            f"- threshold_or_condition: {normalized['threshold_or_condition']}",
            f"- date_or_time_window: {normalized['date_or_time_window']}",
            f"- timezone: {normalized['timezone']}",
            f"- official_weather_source_candidate: {normalized['official_weather_source_candidate']}",
            f"- station_or_source_hierarchy: {normalized['station_or_source_hierarchy']}",
            "- source_capture_candidate_created: "
            + str(result["source_capture_candidate_created"]).lower(),
            "- source_quality_observation_candidate_created: "
            + str(result["source_quality_observation_candidate_created"]).lower(),
            "",
            "## Safety Boundary",
            "",
            "- source/rules discovery only",
            "- no market action guidance",
            "- no probability, EV, edge, confidence scoring, or side selection",
            "- no trading runtime, dispatcher, background worker, queue, wallet, order, or browser changes",
            "- no official weather source fetch beyond metadata embedded in the market payload",
        ]
    )


def write_artifacts(discovery, root=ROOT):
    raw_path = f"{ARTIFACT_DIR}/{RAW_FETCH_JSON}"
    normalized_path = f"{ARTIFACT_DIR}/{NORMALIZED_JSON}"
    source_capture_path = f"{ARTIFACT_DIR}/{SOURCE_CAPTURE_JSON}"
    checklist_json_path = f"{ARTIFACT_DIR}/{CHECKLIST_JSON}"
    checklist_md_path = f"{ARTIFACT_DIR}/{CHECKLIST_MD}"

    raw = build_raw_fetch_artifact(discovery)
    if discovery.get("selected_market"):
        normalized = build_normalized_candidate(discovery)
    else:
        normalized = build_empty_normalized_candidate(discovery)
    source_capture = build_source_capture_candidate(normalized, raw_path)
    checklist = build_operator_checklist(normalized)
    source_quality = build_source_quality_observation_candidate(normalized)

    files_created = [
        "pm_bot/live_readonly/weather_market_discovery.py",
        raw_path,
        f"{ARTIFACT_DIR}/{RAW_FETCH_MD}",
        normalized_path,
        f"{ARTIFACT_DIR}/{NORMALIZED_MD}",
        source_capture_path,
        f"{ARTIFACT_DIR}/{SOURCE_CAPTURE_MD}",
        checklist_json_path,
        checklist_md_path,
        SOURCE_QUALITY_JSON,
        SOURCE_QUALITY_MD,
        WORKBENCH_JSON,
        WORKBENCH_MD,
        RESULT_JSON,
        RESULT_MD,
        "tests/test_weather_market_discovery_readonly.py",
    ]
    result = build_result_doc(discovery, normalized, files_created, root=root)
    artifacts = {
        "raw_fetch": raw,
        "normalized_candidate": normalized,
        "source_capture_candidate": source_capture,
        "operator_checklist": checklist,
        "source_quality_observation_candidate": source_quality,
        "result": result,
    }
    workbench = build_workbench_surface(normalized, result, artifacts)
    artifacts["workbench_surface"] = workbench

    _write_json(raw_path, raw, root=root)
    _write_text(f"{ARTIFACT_DIR}/{RAW_FETCH_MD}", render_raw_fetch_md(raw), root=root)
    _write_json(normalized_path, normalized, root=root)
    _write_text(
        f"{ARTIFACT_DIR}/{NORMALIZED_MD}",
        render_normalized_md(normalized),
        root=root,
    )
    _write_json(source_capture_path, source_capture, root=root)
    _write_text(
        f"{ARTIFACT_DIR}/{SOURCE_CAPTURE_MD}",
        render_source_capture_md(source_capture),
        root=root,
    )
    _write_json(checklist_json_path, checklist, root=root)
    _write_text(checklist_md_path, render_operator_checklist_md(checklist), root=root)
    _write_json(SOURCE_QUALITY_JSON, source_quality, root=root)
    _write_text(SOURCE_QUALITY_MD, render_source_quality_md(source_quality), root=root)
    _write_json(WORKBENCH_JSON, workbench, root=root)
    _write_text(WORKBENCH_MD, render_workbench_md(workbench), root=root)
    _write_json(RESULT_JSON, result, root=root)
    _write_text(RESULT_MD, render_result_md(result, normalized), root=root)
    return artifacts


def run_fetch_one(
    write=False,
    max_markets=MAX_MARKETS_HARD_CAP,
    max_calls=DEFAULT_MAX_CALLS,
    page_limit=DEFAULT_PAGE_LIMIT,
    fetcher=None,
    root=ROOT,
):
    discovery = discover_one_weather_market(
        fetcher=fetcher,
        max_markets=max_markets,
        max_calls=max_calls,
        page_limit=page_limit,
    )
    payload = {
        "schema_version": "weather_market_discovery_run_result.v1",
        "task_id": TASK_ID,
        "status": discovery["status"],
        "fetch_status": discovery["fetch_status"],
        "network_allowed_explicitly": True,
        "public_readonly_only": True,
        "network_call_count": discovery["network_call_count"],
        "polymarket_api_calls_performed": discovery["network_call_count"],
        "non_polymarket_public_source_calls_performed": 0,
        "endpoint_or_url_used": discovery["endpoint_or_url_used"],
        "selected_market_id": _as_text((discovery.get("selected_market") or {}).get("id"))
        or None,
        "selected_market_title_or_question": _as_text(
            (discovery.get("selected_market") or {}).get("question")
        )
        or None,
        "inspected_candidate_count": discovery.get(
            "inspected_market_count",
            len(discovery.get("inspected_candidates", [])),
        ),
        "inspected_weather_candidate_summary_count": len(
            discovery.get("inspected_candidates", [])
        ),
        "inspected_candidate_reason_counts": discovery.get(
            "inspected_candidate_reason_counts",
            {},
        ),
        "operator_review_required": True,
        "planned_capture_status": "draft",
        "auto_promote_to_ready_for_local_review": False,
        "no_market_action_guidance": True,
        "no_trading_authority": True,
        "authenticated_endpoints_used": False,
        "auth_headers_used": False,
        "wallet_or_private_key_accessed": False,
        "orders_created": False,
        "openrouter_calls_performed": 0,
        "simulated_trade_created": False,
        "selected_side": None,
        "stake_amount": None,
    }
    if write:
        written = write_artifacts(discovery, root=root)
        payload["artifacts_written"] = True
        payload["result"] = written["result"]
    else:
        payload["artifacts_written"] = False
    return payload


def _parse_args(argv):
    parser = argparse.ArgumentParser(
        description="SOURCE-010A public read-only weather market discovery pilot."
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--fetch-one", action="store_true")
    mode.add_argument("--summary-only", action="store_true")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--max-markets", type=int, default=MAX_MARKETS_HARD_CAP)
    parser.add_argument("--max-calls", type=int, default=DEFAULT_MAX_CALLS)
    parser.add_argument("--page-limit", type=int, default=DEFAULT_PAGE_LIMIT)
    return parser.parse_args(argv)


def main(argv):
    args = _parse_args(argv)
    try:
        _validate_max_markets(args.max_markets)
        _validate_max_calls(args.max_calls)
        _validate_page_limit(args.page_limit)
    except ValueError as exc:
        raise SystemExit(str(exc))
    if args.summary_only:
        payload = build_summary_only()
    elif args.fetch_one:
        payload = run_fetch_one(
            write=args.write,
            max_markets=args.max_markets,
            max_calls=args.max_calls,
            page_limit=args.page_limit,
        )
    else:
        if args.write:
            raise SystemExit("--write is only valid with --fetch-one")
        payload = build_dry_run_status(
            max_markets=args.max_markets,
            max_calls=args.max_calls,
        )
    print(json.dumps(payload, indent=2, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(__import__("sys").argv[1:]))
