import argparse
import json
import re
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


TASK_ID = "PMBOT-SOURCE-010A-WEATHER-MARKET-CLASS-PILOT-READONLY-DISCOVERY"
REFINED_TASK_ID = (
    "PMBOT-SOURCE-010A2-WEATHER-DISCOVERY-QUERY-REFINEMENT-AND-SECOND-READONLY-ATTEMPT"
)
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

REFINED_RAW_FETCH_JSON = "weather_market_raw_fetch_010a2.v1.json"
REFINED_RAW_FETCH_MD = "weather_market_raw_fetch_010a2.v1.md"
REFINED_NORMALIZED_JSON = "weather_market_normalized_candidate_010a2.v1.json"
REFINED_NORMALIZED_MD = "weather_market_normalized_candidate_010a2.v1.md"
REFINED_SOURCE_CAPTURE_JSON = "weather_source_capture_candidate_010a2.v1.json"
REFINED_SOURCE_CAPTURE_MD = "weather_source_capture_candidate_010a2.v1.md"
REFINED_CHECKLIST_JSON = "weather_operator_review_checklist_010a2.v1.json"
REFINED_CHECKLIST_MD = "weather_operator_review_checklist_010a2.v1.md"
REFINED_DIAGNOSTICS_JSON = "weather_discovery_refinement_diagnostics_010a2.v1.json"
REFINED_DIAGNOSTICS_MD = "weather_discovery_refinement_diagnostics_010a2.v1.md"
REFINED_SOURCE_QUALITY_JSON = (
    "pm_bot/llm/source_quality_observation_candidate_weather_010a2.v1.json"
)
REFINED_SOURCE_QUALITY_MD = (
    "pm_bot/llm/source_quality_observation_candidate_weather_010a2.v1.md"
)
REFINED_WORKBENCH_JSON = "pm_bot/workbench/weather_market_discovery_surface_010a2.v1.json"
REFINED_WORKBENCH_MD = "pm_bot/workbench/weather_market_discovery_surface_010a2.v1.md"
REFINED_RESULT_JSON = "docs/PMBOT_SOURCE_010A2_RESULT.json"
REFINED_RESULT_MD = (
    "docs/PMBOT_SOURCE_010A2_WEATHER_DISCOVERY_QUERY_REFINEMENT_AND_SECOND_READONLY_ATTEMPT.md"
)
PREVIOUS_ATTEMPT_RESULT_PATH = RESULT_JSON
PREVIOUS_ATTEMPT_RAW_FETCH_PATH = f"{ARTIFACT_DIR}/{RAW_FETCH_JSON}"

HEAD_BEFORE = "b08602399880b89fe9d3798231cc8d9ce3f25d83"
REFINED_HEAD_BEFORE = "e76f0d2adddfc129d8d32286fd55deaf65323ffd"
FETCHED_AT_MARKER = "2026-05-08T00:00:00Z_SOURCE_010A_READONLY_FIELD_TEST"
REFINED_FETCHED_AT_MARKER = "2026-05-08T00:00:00Z_SOURCE_010A2_REFINED_READONLY_ATTEMPT"
GAMMA_BASE_URL = "https://gamma-api.polymarket.com"
DEFAULT_PAGE_LIMIT = 500
REFINED_SEARCH_PAGE_LIMIT = 100
DEFAULT_TIMEOUT_SECONDS = 10
DEFAULT_MAX_CALLS = 5
MAX_CALLS_HARD_CAP = 5
REFINED_DEFAULT_MAX_CALLS = 15
REFINED_MAX_CALLS_HARD_CAP = 15
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
    "named storm",
    "wildfire smoke",
    "air quality",
    "aqi",
    "drought",
    "freeze",
    "sea ice extent",
    "arctic sea ice",
    "square kilometers",
)

WEATHER_WORD_MARKERS = (
    "rain",
    "rainfall",
    "precipitation",
    "snow",
    "snowfall",
    "hurricane",
    "storm",
    "degrees",
    "degree",
    "landfall",
)

WEATHER_WEAK_MARKERS = (
    "heat",
    "cold",
    "wind",
    "climate",
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
    "miami heat",
    "heat vs",
    "heat win",
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
    ("florida", "Florida"),
    ("texas", "Texas"),
    ("california", "California"),
    ("arctic", "Arctic"),
    ("atlantic", "Atlantic basin"),
    ("caribbean", "Caribbean"),
    ("gulf of mexico", "Gulf of Mexico"),
    ("united states", "United States"),
    ("u.s.", "United States"),
    ("us ", "United States"),
)

REFINED_WEATHER_SEARCH_TERMS = (
    "weather",
    "temperature",
    "rain",
    "rainfall",
    "precipitation",
    "snow",
    "snowfall",
    "hurricane",
    "tropical storm",
    "storm",
    "wind",
    "heat",
    "cold",
    "freeze",
    "drought",
    "wildfire smoke",
    "air quality",
    "AQI",
    "climate event",
    "landfall",
)

REFINED_BROAD_SCAN_OFFSETS = (0, 500, 1000, 1500, 2000)

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
    if any(marker in lowered for marker in ("sea ice extent", "arctic sea ice")):
        return "sea_ice_extent"
    if any(marker in lowered for marker in ("air quality", "aqi", "wildfire smoke")):
        return "air_quality"
    if "drought" in lowered:
        return "drought_condition"
    if any(marker in lowered for marker in ("temperature", "temperatures", "degrees", "fahrenheit", "celsius", "heat index")):
        return "temperature"
    if any(marker in lowered for marker in ("rainfall", "rain", "precipitation")):
        return "precipitation"
    if any(marker in lowered for marker in ("snowfall", "snow")):
        return "snowfall"
    if any(marker in lowered for marker in ("hurricane", "tropical storm", "storm surge", "landfall", "named storm")):
        return "storm_event"
    if any(marker in lowered for marker in ("wind speed", "wind gust", "mph", "km/h")):
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
    if metric == "sea_ice_extent":
        if re.search(r"(?:\d+(?:\.\d+)?m|\bmillion)\s*square kilometers?\b", lowered):
            return "million_square_kilometers"
        if re.search(r"\bsquare kilometers?\b", lowered):
            return "square_kilometers"
    if metric == "air_quality":
        if re.search(r"\baqi\b|air quality index", lowered):
            return "AQI"
    if metric == "temperature" and re.search(r"\bdegrees?\b", lowered):
        return "degrees_unspecified_operator_must_verify"
    if metric in {"precipitation", "snowfall"}:
        if re.search(r"\bin(?:ch|ches)?\b", lowered) or "inches" in lowered:
            return "inches"
        if re.search(r"\bmm\b|millimeters?", lowered):
            return "millimeters"
    if metric == "wind" and re.search(r"\bmph\b|miles per hour", lowered):
        return "mph"
    if metric == "wind" and re.search(r"\bkm/h\b|kilometers per hour", lowered):
        return "km/h"
    if metric == "storm_event":
        if re.search(r"(?:category|cat\.?)\s+\d+", lowered):
            return "saffir_simpson_category"
        return "event_occurrence"
    if metric == "drought_condition":
        return "drought_status"
    return ""


def _extract_threshold_or_condition(text):
    patterns = (
        r"\bbetween\s+\d+(?:\.\d+)?\s*(?:m|million)?\s*(?:&|and)\s+\d+(?:\.\d+)?\s*(?:m|million)?\s*(?:square kilometers?|degrees?|fahrenheit|celsius|°f|°c|inches|inch|mm|mph|aqi)?",
        r"(?:at least|at or above|above|over|greater than|more than|exceed(?:s|ed)?|reach(?:es|ed)?|hit(?:s)?)\s+\d+(?:\.\d+)?\s*(?:degrees?|fahrenheit|celsius|°f|°c|inches|inch|mm|mph)?",
        r"(?:below|under|less than|at or below)\s+\d+(?:\.\d+)?\s*(?:degrees?|fahrenheit|celsius|°f|°c|inches|inch|mm|mph)?",
        r"\d+(?:\.\d+)?\s*(?:m|million)?\s*(?:square kilometers?|degrees?|fahrenheit|celsius|°f|°c|inches|inch|mm|mph|aqi)\s*(?:or more|or less|or higher|or lower)?",
        r"(?:category|cat\.?)\s+\d+",
        r"(?:will|does|do)\s+.+?\s+(?:rain|snow|make landfall|form|hit|reach|be named)",
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
        if any(
            marker in url.lower()
            for marker in ("weather.gov", "noaa.gov", "nws", "nhc.noaa.gov", "nsidc.org")
        )
    ]
    if weather_urls:
        return weather_urls[0]
    for marker in (
        "National Weather Service",
        "NOAA",
        "NWS",
        "weather.gov",
        "National Hurricane Center",
        "NSIDC",
        "National Snow and Ice Data Center",
    ):
        if re.search(rf"\b{re.escape(marker)}\b", text, flags=re.IGNORECASE):
            return marker
    return ""


def _extract_station_or_source_hierarchy(text):
    patterns = (
        r"(?:weather station|station)\s+[A-Za-z0-9 .,'-]{2,80}",
        r"(?:as measured by|according to)\s+[A-Za-z0-9 .,'/-]{2,100}",
        r"(?:National Weather Service|NOAA|NWS)\s+[A-Za-z0-9 .,'/-]{0,80}",
        r"(?:National Hurricane Center|NHC)\s+[A-Za-z0-9 .,'/-]{0,80}",
        r"(?:National Snow and Ice Data Center|NSIDC)\s+[A-Za-z0-9 .,'/-]{0,80}",
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


def _is_long_horizon_or_policy_climate_market(lowered):
    policy_markers = (
        "carbon",
        "emissions",
        "climate policy",
        "paris agreement",
        "tax credit",
        "election",
        "bill pass",
    )
    if any(marker in lowered for marker in policy_markers):
        return True
    climate_rank_markers = (
        "hottest year on record",
        "second-hottest year",
        "third-hottest year",
        "fourth-hottest year",
        "fifth-hottest year",
        "rank as the sixth-hottest",
    )
    return any(marker in lowered for marker in climate_rank_markers)


def _refined_missing_weather_fields(fields):
    required = [
        "location",
        "weather_metric",
        "threshold_or_condition",
        "date_or_time_window",
    ]
    return [field for field in required if fields.get(field) in ("", None, [])]


def _metadata_completeness_count(fields):
    optional_fields = [
        "location",
        "weather_metric",
        "unit",
        "threshold_or_condition",
        "date_or_time_window",
        "timezone",
        "official_weather_source_candidate",
        "station_or_source_hierarchy",
        "fallback_source_candidate",
    ]
    return sum(1 for field in optional_fields if fields.get(field) not in ("", None, []))


def _is_direct_weather_metric(metric):
    return metric in {
        "temperature",
        "precipitation",
        "snowfall",
        "storm_event",
        "wind",
        "air_quality",
        "drought_condition",
        "weather_condition",
    }


def _inspect_market_refined(market, query_or_filter=None):
    inspection = _inspect_market(market)
    title = _as_text(market.get("question"))
    text = _market_text(market)
    lowered = text.lower()
    fields = _extract_weather_fields(market)
    active = market.get("active") is True
    closed = market.get("closed") is True
    weather_marker = _has_weather_marker(lowered)
    false_positive = _looks_like_non_weather_false_positive(lowered)
    missing_refined = _refined_missing_weather_fields(fields)
    climate_or_policy = _is_long_horizon_or_policy_climate_market(lowered)

    if not active or closed:
        reason = "market_not_active_or_closed"
    elif not title:
        reason = "missing_title_or_question"
    elif not weather_marker:
        reason = "no_weather_marker"
    elif false_positive:
        reason = "weather_word_false_positive_or_sports_context"
    elif climate_or_policy and fields["weather_metric"] != "sea_ice_extent":
        reason = "long_horizon_climate_or_policy_not_direct_weather_pilot"
    elif missing_refined:
        reason = "weather_marker_but_missing_refined_required_fields"
    else:
        reason = "suitable_weather_market_candidate"

    inspection.update(
        {
            "reason": reason,
            "query_or_filter": query_or_filter,
            "weather_marker_detected": weather_marker,
            "missing_basic_fields": missing_refined,
            "extracted_weather_fields": fields,
            "metadata_completeness_count": _metadata_completeness_count(fields),
            "direct_weather_metric": _is_direct_weather_metric(fields["weather_metric"]),
            "climate_or_policy_rejected": reason
            == "long_horizon_climate_or_policy_not_direct_weather_pilot",
        }
    )
    return inspection


def _refined_candidate_sort_key(item):
    inspection = item["inspection"]
    fields = inspection["extracted_weather_fields"]
    title = _as_text(item["market"].get("question")).lower()
    long_horizon = 1 if "2027" in title or "2030" in title else 0
    return (
        1 if inspection["direct_weather_metric"] else 0,
        inspection["metadata_completeness_count"],
        1 if fields["official_weather_source_candidate"] else 0,
        1 if fields["station_or_source_hierarchy"] else 0,
        -long_horizon,
    )


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


def _market_search_url(term, limit=REFINED_SEARCH_PAGE_LIMIT):
    query = urllib.parse.urlencode(
        {
            "active": "true",
            "closed": "false",
            "limit": str(limit),
            "offset": "0",
            "search": term,
        }
    )
    return f"{GAMMA_BASE_URL}/markets?{query}"


def _extract_market_list_payload(payload):
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        for key in ("markets", "data", "results"):
            value = payload.get(key)
            if isinstance(value, list):
                return value
    return None


def _refined_query_plan(max_calls, page_limit=DEFAULT_PAGE_LIMIT):
    broad_limit = min(page_limit, DEFAULT_PAGE_LIMIT)
    search_limit = min(page_limit, REFINED_SEARCH_PAGE_LIMIT)
    plan = [
        {
            "kind": "broad_active_market_page",
            "term": None,
            "url": _market_list_url(offset=offset, limit=broad_limit),
        }
        for offset in REFINED_BROAD_SCAN_OFFSETS
    ]
    plan.extend(
        {
            "kind": "keyword_active_market_search",
            "term": term,
            "url": _market_search_url(term=term, limit=search_limit),
        }
        for term in REFINED_WEATHER_SEARCH_TERMS
    )
    return plan[:max_calls]


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


def build_dry_run_status(
    max_markets=MAX_MARKETS_HARD_CAP,
    max_calls=DEFAULT_MAX_CALLS,
    refined_search=False,
):
    _validate_max_markets(max_markets)
    _validate_max_calls(max_calls, refined_search=refined_search)
    task_id = REFINED_TASK_ID if refined_search else TASK_ID
    hard_cap = REFINED_MAX_CALLS_HARD_CAP if refined_search else MAX_CALLS_HARD_CAP
    planned_endpoints = [f"{GAMMA_BASE_URL}/markets"]
    if refined_search:
        planned_endpoints = [item["url"] for item in _refined_query_plan(max_calls)]
    return {
        "schema_version": "weather_market_discovery_dry_run.v1",
        "task_id": task_id,
        "status": "dry_run_no_network",
        "mode": "dry_run",
        "refinement_attempt": refined_search,
        "network_allowed_explicitly": False,
        "network_calls_performed": 0,
        "polymarket_api_calls_performed": 0,
        "fetch_performed": False,
        "max_markets": max_markets,
        "max_markets_hard_cap": MAX_MARKETS_HARD_CAP,
        "max_calls": max_calls,
        "max_calls_hard_cap": hard_cap,
        "planned_public_readonly_endpoints": planned_endpoints,
        "write_scope": "none_unless_fetch_one_and_write_are_passed",
        "operator_review_required": True,
        "planned_capture_status": "draft",
        "auto_promote_to_ready_for_local_review": False,
        "safety_summary": _empty_safety_summary(False, 0),
    }


def build_summary_only(root=ROOT, refined_search=False):
    result_path = REFINED_RESULT_JSON if refined_search else RESULT_JSON
    task_id = REFINED_TASK_ID if refined_search else TASK_ID
    result = _load_optional_json(result_path, root=root)
    if result is None:
        return {
            "schema_version": "weather_market_discovery_summary_only.v1",
            "task_id": task_id,
            "status": "summary_only_no_artifacts",
            "network_calls_performed": 0,
            "polymarket_api_calls_performed": 0,
            "openrouter_calls_performed": 0,
            "operator_review_required": True,
        }
    return {
        "schema_version": "weather_market_discovery_summary_only.v1",
        "task_id": result.get("task_id", task_id),
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


def _validate_max_calls(max_calls, refined_search=False):
    hard_cap = REFINED_MAX_CALLS_HARD_CAP if refined_search else MAX_CALLS_HARD_CAP
    task_label = "SOURCE-010A2" if refined_search else "SOURCE-010A"
    if max_calls < 1 or max_calls > hard_cap:
        raise ValueError(f"{task_label} max_calls must be between 1 and {hard_cap}")


def _validate_page_limit(page_limit):
    if page_limit < 1 or page_limit > DEFAULT_PAGE_LIMIT:
        raise ValueError(f"--page-limit must be between 1 and {DEFAULT_PAGE_LIMIT}")


def _fetch_logged(fetcher, url, log, max_calls, task_label="SOURCE-010A"):
    if log["network_call_count"] >= max_calls:
        raise ApiCallCapExceeded(f"{task_label} Polymarket/Gamma API call cap reached")
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


def discover_one_weather_market_refined(
    fetcher=None,
    max_markets=MAX_MARKETS_HARD_CAP,
    max_calls=REFINED_DEFAULT_MAX_CALLS,
    page_limit=DEFAULT_PAGE_LIMIT,
):
    _validate_max_markets(max_markets)
    _validate_max_calls(max_calls, refined_search=True)
    _validate_page_limit(page_limit)
    fetcher = fetcher or PublicGammaFetcher()
    log = {"network_call_count": 0, "endpoint_or_url_used": []}
    inspected_by_key = {}
    reason_counts = {}
    suitable = []
    raw_weather_payloads = []
    response_summaries = []
    blocked_reason = None

    try:
        for plan in _refined_query_plan(max_calls=max_calls, page_limit=page_limit):
            payload = _fetch_logged(
                fetcher,
                plan["url"],
                log,
                max_calls,
                task_label="SOURCE-010A2",
            )
            markets = _extract_market_list_payload(payload)
            if markets is None:
                blocked_reason = "Gamma markets endpoint returned a non-list payload."
                break
            response_summaries.append(
                {
                    "query_or_filter": plan["term"] or plan["kind"],
                    "endpoint_or_url_used": plan["url"],
                    "payload_kind": "list",
                    "market_count": len(markets),
                }
            )
            for market in markets:
                key = (
                    _as_text(market.get("id"))
                    or _as_text(market.get("slug"))
                    or _as_text(market.get("question"))
                )
                if not key or key in inspected_by_key:
                    continue
                inspection = _inspect_market_refined(
                    market,
                    query_or_filter=plan["term"] or plan["kind"],
                )
                inspected_by_key[key] = inspection
                reason = inspection["reason"]
                reason_counts[reason] = reason_counts.get(reason, 0) + 1
                if inspection["weather_marker_detected"] or reason != "no_weather_marker":
                    raw_weather_payloads.append(
                        {
                            "inspection": inspection,
                            "raw_market_payload": _sanitize_raw_market_payload(market),
                        }
                    )
                if _is_suitable_inspection(inspection):
                    suitable.append({"inspection": inspection, "market": market})
    except ApiCallCapExceeded as exc:
        blocked_reason = str(exc)
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError) as exc:
        blocked_reason = f"{exc.__class__.__name__}: {exc}"

    inspected = list(inspected_by_key.values())
    weather_like_count = sum(1 for item in inspected if item["weather_marker_detected"])
    if blocked_reason:
        return {
            "status": "blocked_or_unavailable",
            "fetch_status": "blocked_or_unavailable",
            "blocked_reason": blocked_reason,
            "raw_market_payload": None,
            "raw_market_payloads_or_candidate_summaries": raw_weather_payloads,
            "raw_response_summaries": response_summaries,
            "selected_market": None,
            "selection_reason": blocked_reason,
            "inspected_candidates": inspected,
            "inspected_market_count": len(inspected),
            "weather_like_candidate_count": weather_like_count,
            "inspected_candidate_reason_counts": reason_counts,
            "queries_or_filters_used": _refined_queries_or_filters_used(max_calls, page_limit),
            **log,
        }

    if suitable:
        selected_item = sorted(suitable, key=_refined_candidate_sort_key, reverse=True)[0]
        selected_market = selected_item["market"]
        selected_inspection = selected_item["inspection"]
        return {
            "status": "selected",
            "fetch_status": "selected",
            "raw_market_payload": selected_market,
            "raw_market_payloads_or_candidate_summaries": raw_weather_payloads,
            "raw_response_summaries": response_summaries,
            "selected_market": selected_market,
            "selected_inspection": selected_inspection,
            "selection_reason": (
                "Refined public Gamma metadata discovery found a weather-like market "
                "with clear region or location, metric or condition, threshold, and "
                "time-window fields. Selection used metadata completeness only."
            ),
            "inspected_candidates": inspected,
            "inspected_market_count": len(inspected),
            "weather_like_candidate_count": weather_like_count,
            "inspected_candidate_reason_counts": reason_counts,
            "queries_or_filters_used": _refined_queries_or_filters_used(max_calls, page_limit),
            **log,
        }

    return {
        "status": "no_suitable_weather_market_found_after_refinement",
        "fetch_status": "no_suitable_weather_market_found_after_refinement",
        "raw_market_payload": None,
        "raw_market_payloads_or_candidate_summaries": raw_weather_payloads,
        "raw_response_summaries": response_summaries,
        "selected_market": None,
        "selection_reason": (
            "No inspected market met refined weather pilot criteria after broader "
            "active-market scans and keyword searches."
        ),
        "inspected_candidates": inspected,
        "inspected_market_count": len(inspected),
        "weather_like_candidate_count": weather_like_count,
        "inspected_candidate_reason_counts": reason_counts,
        "queries_or_filters_used": _refined_queries_or_filters_used(max_calls, page_limit),
        **log,
    }


def _refined_queries_or_filters_used(max_calls, page_limit=DEFAULT_PAGE_LIMIT):
    return {
        "attempted_strategy": [
            "reuse_010a_active_open_markets_pagination",
            "keyword_search_over_active_open_markets",
            "local_weather_keyword_filtering_over_titles_descriptions_slugs_tags",
            "metadata_completeness_selection_without_price_liquidity_or_profit_inputs",
        ],
        "primary_weather_terms_considered": list(REFINED_WEATHER_SEARCH_TERMS),
        "location_or_metric_indicators_considered": [
            "city_names",
            "state_country_region_names",
            "degrees",
            "fahrenheit_celsius",
            "inches_mm",
            "mph_kmh",
            "category_landfall_named_storm",
            "above_below_threshold",
            "sea_ice_extent",
            "AQI",
        ],
        "query_plan_used": [
            {
                "kind": item["kind"],
                "term": item["term"],
                "endpoint_or_url": item["url"],
            }
            for item in _refined_query_plan(max_calls=max_calls, page_limit=page_limit)
        ],
    }


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


def _previous_attempt_status(root=ROOT):
    previous = _load_optional_json(PREVIOUS_ATTEMPT_RESULT_PATH, root=root) or {}
    return previous.get("status") or "unknown"


def build_refined_raw_fetch_artifact(discovery, root=ROOT):
    selected_market = discovery.get("selected_market") or {}
    selected_market_id = _as_text(selected_market.get("id")) or None
    selected_slug = _as_text(selected_market.get("slug")) or None
    selected_title = _as_text(selected_market.get("question")) or None
    network_count = discovery.get("network_call_count", 0)
    inspected = discovery.get("inspected_candidates", [])
    rejection_reasons = [
        {
            "market_id": item.get("market_id"),
            "market_slug": item.get("market_slug"),
            "market_title_or_question": item.get("market_title_or_question"),
            "reason": item.get("reason"),
            "missing_fields": item.get("missing_basic_fields", []),
        }
        for item in inspected
        if item.get("market_id") != selected_market_id and item.get("reason") != "no_weather_marker"
    ]
    return {
        "schema_version": "weather_market_raw_fetch_010a2.v1",
        "task_id": REFINED_TASK_ID,
        "fetch_status": discovery.get("fetch_status"),
        "refinement_attempt": True,
        "previous_attempt_reference": {
            "task_id": TASK_ID,
            "result_path": PREVIOUS_ATTEMPT_RESULT_PATH,
            "raw_fetch_path": PREVIOUS_ATTEMPT_RAW_FETCH_PATH,
            "status": _previous_attempt_status(root=root),
        },
        "fetched_at_marker": REFINED_FETCHED_AT_MARKER,
        "network_allowed_explicitly": True,
        "public_readonly_only": True,
        "authenticated_endpoints_used": False,
        "auth_headers_used": False,
        "wallet_or_private_key_accessed": False,
        "orders_created": False,
        "endpoint_or_url_used": discovery.get("endpoint_or_url_used", []),
        "network_call_count": network_count,
        "polymarket_api_calls_performed": network_count,
        "raw_market_payloads_or_candidate_summaries": discovery.get(
            "raw_market_payloads_or_candidate_summaries",
            [{"inspected_candidate_summaries": inspected}],
        ),
        "raw_response_summaries": discovery.get("raw_response_summaries", []),
        "inspected_candidate_count": discovery.get("inspected_market_count", len(inspected)),
        "weather_like_candidate_count": discovery.get("weather_like_candidate_count", 0),
        "selected_market_id": selected_market_id,
        "selected_market_slug": selected_slug,
        "selected_market_title_or_question": selected_title,
        "selection_reason": discovery.get("selection_reason"),
        "rejection_reasons_by_candidate": rejection_reasons,
        "inspected_candidate_reason_counts": discovery.get(
            "inspected_candidate_reason_counts",
            {},
        ),
        "queries_or_filters_used": discovery.get("queries_or_filters_used", {}),
        "blocked_reason": discovery.get("blocked_reason"),
        "no_market_action_guidance": True,
        "safety_summary": _empty_safety_summary(True, network_count),
    }


def build_refined_normalized_candidate(discovery):
    if discovery.get("selected_market"):
        candidate = build_normalized_candidate(discovery)
        candidate["schema_version"] = "weather_market_normalized_candidate_010a2.v1"
        candidate["task_id"] = REFINED_TASK_ID
        candidate["status"] = "selected"
        return candidate

    candidate = build_empty_normalized_candidate(discovery)
    candidate["schema_version"] = "weather_market_normalized_candidate_010a2.v1"
    candidate["task_id"] = REFINED_TASK_ID
    candidate["status"] = "no_suitable_weather_market_found_after_refinement"
    candidate["unresolved_source_questions"] = [
        "No suitable public read-only weather market candidate was selected after refined search.",
        discovery.get("blocked_reason", "")
        or "No matching market met refined weather pilot criteria.",
    ]
    return candidate


def build_refined_source_capture_candidate(normalized, raw_path):
    candidate = build_source_capture_candidate(normalized, raw_path)
    candidate["contract_version"] = "weather_source_capture_candidate_010a2.v1"
    candidate["task_id"] = REFINED_TASK_ID
    if normalized["market_id"] is None:
        candidate["status"] = "no_candidate"
        candidate["market_id"] = None
    else:
        candidate["status"] = "selected_candidate_pending_operator_review"
    return candidate


def build_refined_operator_checklist(normalized):
    checklist = build_operator_checklist(normalized)
    checklist["contract_version"] = "weather_operator_review_checklist_010a2.v1"
    checklist["task_id"] = REFINED_TASK_ID
    return checklist


def build_refined_diagnostics(discovery, root=ROOT):
    selected = discovery.get("selected_market") or {}
    fetch_status = discovery.get("fetch_status")
    if_no_selection = []
    if fetch_status != "selected":
        if_no_selection.append(discovery.get("selection_reason"))
        if discovery.get("blocked_reason"):
            if_no_selection.append(discovery["blocked_reason"])
        for reason, count in sorted(discovery.get("inspected_candidate_reason_counts", {}).items()):
            if_no_selection.append(f"{reason}: {count}")
    return {
        "schema_version": "weather_discovery_refinement_diagnostics_010a2.v1",
        "task_id": REFINED_TASK_ID,
        "previous_attempt_result_path": PREVIOUS_ATTEMPT_RESULT_PATH,
        "previous_attempt_status": _previous_attempt_status(root=root),
        "refined_strategy_summary": [
            "Reused 010A active/open Gamma market pagination.",
            "Added keyword searches for weather, temperature, rain, snow, storms, wind, heat, cold, drought, air quality, and climate-event terms.",
            "Expanded local filtering for weather-adjacent direct measurement markets, including named storms, AQI, drought, and Arctic sea ice extent.",
            "Selected at most one candidate using weather metadata completeness only.",
        ],
        "queries_or_filters_used": discovery.get("queries_or_filters_used", {}),
        "endpoints_or_urls_used": discovery.get("endpoint_or_url_used", []),
        "inspected_candidate_count": discovery.get("inspected_market_count", 0),
        "weather_like_candidate_count": discovery.get("weather_like_candidate_count", 0),
        "selected_market_id": _as_text(selected.get("id")) or None,
        "selected_market_title_or_question": _as_text(selected.get("question")) or None,
        "if_no_selection_reasons": [reason for reason in if_no_selection if reason],
        "recommended_next_action": (
            "PMBOT-SOURCE-010B-WEATHER-DRAFT-CAPTURE-AUTOFILL-FROM-READONLY-CANDIDATE"
            if selected
            else "PMBOT-SOURCE-011A-CRYPTO-MARKET-CLASS-PILOT-READONLY-DISCOVERY or manual weather candidate selection."
        ),
        "no_market_action_guidance": True,
        "no_trading_authority": True,
    }


def build_refined_source_quality_observation_candidate(normalized):
    if normalized["market_id"] is None:
        return {
            "schema_version": "source_quality_observation_candidate_weather_010a2.v1",
            "task_id": REFINED_TASK_ID,
            "market_id": None,
            "market_class": "weather",
            "status": "no_weather_candidate_selected",
            "source_quality_status": "no_weather_candidate_selected",
            "source_ids_observed": [],
            "source_types_observed": [],
            "source_roles": [],
            "outcome_known": False,
            "source_scoring_performed": False,
            "source_ranking_updated": False,
            "trading_profit_used_for_scoring": False,
            "operator_review_required": True,
            "notes": [
                "No source-quality observation can be attached to a weather market until a candidate is selected.",
                "No source scoring or ranking is performed in SOURCE-010A2.",
            ],
        }
    candidate = build_source_quality_observation_candidate(normalized)
    candidate["schema_version"] = "source_quality_observation_candidate_weather_010a2.v1"
    candidate["task_id"] = REFINED_TASK_ID
    candidate["status"] = "pending_future_capture_and_outcome_review"
    candidate["source_quality_status"] = "pending_future_capture_and_outcome_review"
    candidate["notes"] = [
        "Weather source-quality observation is candidate-only until SOURCE-010B and future outcome review.",
        "No source scoring or ranking is performed in SOURCE-010A2.",
    ]
    return candidate


def build_refined_workbench_surface(normalized, result, artifacts):
    return {
        "schema_version": "weather_market_discovery_surface_010a2.v1",
        "task_id": REFINED_TASK_ID,
        "market_class": "weather",
        "discovery_status": result["fetch_status"],
        "selected_market_id": normalized["market_id"],
        "selected_market_title_or_question": normalized["title_or_question"],
        "normalized_candidate_available": bool(normalized["market_id"]),
        "source_capture_candidate_available": bool(normalized["market_id"]),
        "operator_checklist_available": artifacts.get("operator_checklist") is not None,
        "source_quality_observation_candidate_available": artifacts.get(
            "source_quality_observation_candidate"
        )
        is not None,
        "diagnostics_available": artifacts.get("diagnostics") is not None,
        "operator_review_required": True,
        "next_operator_actions": _next_operator_actions(normalized, result),
        "no_market_action_guidance": True,
        "no_trading_authority": True,
    }


def build_refined_result_doc(discovery, normalized, files_created, root=ROOT):
    selected = discovery.get("selected_market") or {}
    fetch_status = discovery.get("fetch_status")
    if fetch_status == "selected":
        status = "completed_local"
    elif fetch_status == "no_suitable_weather_market_found_after_refinement":
        status = "completed_no_suitable_weather_market_found_after_refinement"
    else:
        status = "blocked_or_unavailable"
    pipeline = _pipeline_snapshot(root=root)
    artifacts_created = True
    return {
        "task_id": REFINED_TASK_ID,
        "status": status,
        "head_before": REFINED_HEAD_BEFORE,
        "head_after": "reported_in_final_response_after_commit_or_push",
        "previous_attempt_status": _previous_attempt_status(root=root),
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
        "normalized_weather_candidate_created": artifacts_created,
        "source_capture_candidate_created": artifacts_created,
        "operator_checklist_created": artifacts_created,
        "source_quality_observation_candidate_created": artifacts_created,
        "diagnostics_created": artifacts_created,
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
        "files_modified": ["pm_bot/live_readonly/weather_market_discovery.py"],
        "next_recommended_action": (
            "PMBOT-SOURCE-010B-WEATHER-DRAFT-CAPTURE-AUTOFILL-FROM-READONLY-CANDIDATE"
            if normalized["market_id"]
            else "PMBOT-SOURCE-011A-CRYPTO-MARKET-CLASS-PILOT-READONLY-DISCOVERY or manual weather candidate selection."
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


def render_refined_raw_fetch_md(raw):
    return "\n".join(
        [
            "# PMBOT SOURCE-010A2 Weather Refined Raw Fetch",
            "",
            f"- task_id: {raw['task_id']}",
            f"- fetch_status: {raw['fetch_status']}",
            "- refinement_attempt: true",
            f"- previous_attempt_status: {raw['previous_attempt_reference']['status']}",
            f"- selected_market_id: {raw['selected_market_id']}",
            f"- selected_market_title_or_question: {raw['selected_market_title_or_question']}",
            f"- network_call_count: {raw['network_call_count']}",
            f"- inspected_candidate_count: {raw['inspected_candidate_count']}",
            f"- weather_like_candidate_count: {raw['weather_like_candidate_count']}",
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
            "## Rejection Reasons",
            "",
            *[
                f"- {item['market_id']}: {item['reason']}"
                for item in raw["rejection_reasons_by_candidate"][:50]
            ],
            "",
            "## Safety",
            "",
            "- source/rules discovery only",
            "- no trading decision",
            "- no probability, EV, edge, confidence, or side selection guidance",
            "- no wallet, order, runtime, dispatcher, background worker, queue, browser, or canonical packet changes",
        ]
    )


def render_refined_normalized_md(candidate):
    lines = [
        "# PMBOT SOURCE-010A2 Weather Refined Normalized Candidate",
        "",
        f"- task_id: {candidate['task_id']}",
        f"- status: {candidate.get('status')}",
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
    ]
    lines.extend(f"- {field}" for field in candidate["missing_fields"])
    lines.extend(["", "## Unresolved Source Questions", ""])
    lines.extend(f"- {question}" for question in candidate["unresolved_source_questions"])
    lines.extend(
        [
            "",
            "## Safety",
            "",
            "- no market action guidance",
            "- no trading authority",
        ]
    )
    return "\n".join(lines)


def render_refined_source_capture_md(candidate):
    return "\n".join(
        [
            "# PMBOT SOURCE-010A2 Weather Source Capture Candidate",
            "",
            f"- task_id: {candidate['task_id']}",
            f"- status: {candidate.get('status')}",
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


def render_refined_operator_checklist_md(checklist):
    lines = [
        "# PMBOT SOURCE-010A2 Weather Operator Review Checklist",
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


def render_refined_diagnostics_md(diagnostics):
    lines = [
        "# PMBOT SOURCE-010A2 Weather Discovery Refinement Diagnostics",
        "",
        f"- task_id: {diagnostics['task_id']}",
        f"- previous_attempt_status: {diagnostics['previous_attempt_status']}",
        f"- inspected_candidate_count: {diagnostics['inspected_candidate_count']}",
        f"- weather_like_candidate_count: {diagnostics['weather_like_candidate_count']}",
        f"- selected_market_id: {diagnostics['selected_market_id']}",
        f"- selected_market_title_or_question: {diagnostics['selected_market_title_or_question']}",
        f"- recommended_next_action: {diagnostics['recommended_next_action']}",
        "- no_market_action_guidance: true",
        "- no_trading_authority: true",
        "",
        "## Refined Strategy",
        "",
    ]
    lines.extend(f"- {item}" for item in diagnostics["refined_strategy_summary"])
    lines.extend(["", "## Endpoints", ""])
    lines.extend(f"- {url}" for url in diagnostics["endpoints_or_urls_used"])
    if diagnostics["if_no_selection_reasons"]:
        lines.extend(["", "## If No Selection Reasons", ""])
        lines.extend(f"- {reason}" for reason in diagnostics["if_no_selection_reasons"])
    return "\n".join(lines)


def render_refined_source_quality_md(candidate):
    lines = [
        "# PMBOT SOURCE-010A2 Weather Source Quality Observation Candidate",
        "",
        f"- task_id: {candidate['task_id']}",
        f"- market_id: {candidate['market_id']}",
        f"- market_class: {candidate['market_class']}",
        f"- status: {candidate['status']}",
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
    lines.extend(["", "## Notes", ""])
    lines.extend(f"- {note}" for note in candidate["notes"])
    return "\n".join(lines)


def render_refined_workbench_md(surface):
    return "\n".join(
        [
            "# PMBOT SOURCE-010A2 Weather Discovery Workbench Surface",
            "",
            f"- task_id: {surface['task_id']}",
            f"- market_class: {surface['market_class']}",
            f"- discovery_status: {surface['discovery_status']}",
            f"- selected_market_id: {surface['selected_market_id']}",
            f"- selected_market_title_or_question: {surface['selected_market_title_or_question']}",
            f"- normalized_candidate_available: {str(surface['normalized_candidate_available']).lower()}",
            f"- source_capture_candidate_available: {str(surface['source_capture_candidate_available']).lower()}",
            f"- operator_checklist_available: {str(surface['operator_checklist_available']).lower()}",
            f"- source_quality_observation_candidate_available: {str(surface['source_quality_observation_candidate_available']).lower()}",
            f"- diagnostics_available: {str(surface['diagnostics_available']).lower()}",
            "- operator_review_required: true",
            "- no_market_action_guidance: true",
            "- no_trading_authority: true",
            "",
            "## Next Operator Actions",
            "",
            *[f"- {action}" for action in surface["next_operator_actions"]],
        ]
    )


def render_refined_result_md(result, normalized):
    return "\n".join(
        [
            "# PMBOT SOURCE-010A2 Weather Discovery Query Refinement and Second Read-Only Attempt",
            "",
            f"- task_id: {result['task_id']}",
            f"- status: {result['status']}",
            f"- previous_attempt_status: {result['previous_attempt_status']}",
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
            "- normalized_weather_candidate_created: "
            + str(result["normalized_weather_candidate_created"]).lower(),
            "- source_capture_candidate_created: "
            + str(result["source_capture_candidate_created"]).lower(),
            "- source_quality_observation_candidate_created: "
            + str(result["source_quality_observation_candidate_created"]).lower(),
            "- diagnostics_created: " + str(result["diagnostics_created"]).lower(),
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


def write_refined_artifacts(discovery, root=ROOT):
    raw_path = f"{ARTIFACT_DIR}/{REFINED_RAW_FETCH_JSON}"
    normalized_path = f"{ARTIFACT_DIR}/{REFINED_NORMALIZED_JSON}"
    source_capture_path = f"{ARTIFACT_DIR}/{REFINED_SOURCE_CAPTURE_JSON}"
    checklist_json_path = f"{ARTIFACT_DIR}/{REFINED_CHECKLIST_JSON}"
    checklist_md_path = f"{ARTIFACT_DIR}/{REFINED_CHECKLIST_MD}"
    diagnostics_json_path = f"{ARTIFACT_DIR}/{REFINED_DIAGNOSTICS_JSON}"
    diagnostics_md_path = f"{ARTIFACT_DIR}/{REFINED_DIAGNOSTICS_MD}"

    raw = build_refined_raw_fetch_artifact(discovery, root=root)
    normalized = build_refined_normalized_candidate(discovery)
    source_capture = build_refined_source_capture_candidate(normalized, raw_path)
    checklist = build_refined_operator_checklist(normalized)
    diagnostics = build_refined_diagnostics(discovery, root=root)
    source_quality = build_refined_source_quality_observation_candidate(normalized)

    files_created = [
        raw_path,
        f"{ARTIFACT_DIR}/{REFINED_RAW_FETCH_MD}",
        normalized_path,
        f"{ARTIFACT_DIR}/{REFINED_NORMALIZED_MD}",
        source_capture_path,
        f"{ARTIFACT_DIR}/{REFINED_SOURCE_CAPTURE_MD}",
        checklist_json_path,
        checklist_md_path,
        diagnostics_json_path,
        diagnostics_md_path,
        REFINED_SOURCE_QUALITY_JSON,
        REFINED_SOURCE_QUALITY_MD,
        REFINED_WORKBENCH_JSON,
        REFINED_WORKBENCH_MD,
        REFINED_RESULT_JSON,
        REFINED_RESULT_MD,
        "tests/test_weather_market_discovery_refinement.py",
    ]
    result = build_refined_result_doc(discovery, normalized, files_created, root=root)
    artifacts = {
        "raw_fetch": raw,
        "normalized_candidate": normalized,
        "source_capture_candidate": source_capture,
        "operator_checklist": checklist,
        "diagnostics": diagnostics,
        "source_quality_observation_candidate": source_quality,
        "result": result,
    }
    workbench = build_refined_workbench_surface(normalized, result, artifacts)
    artifacts["workbench_surface"] = workbench

    _write_json(raw_path, raw, root=root)
    _write_text(
        f"{ARTIFACT_DIR}/{REFINED_RAW_FETCH_MD}",
        render_refined_raw_fetch_md(raw),
        root=root,
    )
    _write_json(normalized_path, normalized, root=root)
    _write_text(
        f"{ARTIFACT_DIR}/{REFINED_NORMALIZED_MD}",
        render_refined_normalized_md(normalized),
        root=root,
    )
    _write_json(source_capture_path, source_capture, root=root)
    _write_text(
        f"{ARTIFACT_DIR}/{REFINED_SOURCE_CAPTURE_MD}",
        render_refined_source_capture_md(source_capture),
        root=root,
    )
    _write_json(checklist_json_path, checklist, root=root)
    _write_text(
        checklist_md_path,
        render_refined_operator_checklist_md(checklist),
        root=root,
    )
    _write_json(diagnostics_json_path, diagnostics, root=root)
    _write_text(diagnostics_md_path, render_refined_diagnostics_md(diagnostics), root=root)
    _write_json(REFINED_SOURCE_QUALITY_JSON, source_quality, root=root)
    _write_text(
        REFINED_SOURCE_QUALITY_MD,
        render_refined_source_quality_md(source_quality),
        root=root,
    )
    _write_json(REFINED_WORKBENCH_JSON, workbench, root=root)
    _write_text(REFINED_WORKBENCH_MD, render_refined_workbench_md(workbench), root=root)
    _write_json(REFINED_RESULT_JSON, result, root=root)
    _write_text(REFINED_RESULT_MD, render_refined_result_md(result, normalized), root=root)
    return artifacts


def run_fetch_one(
    write=False,
    max_markets=MAX_MARKETS_HARD_CAP,
    max_calls=DEFAULT_MAX_CALLS,
    page_limit=DEFAULT_PAGE_LIMIT,
    fetcher=None,
    root=ROOT,
    refined_search=False,
):
    if refined_search:
        return run_fetch_one_refined(
            write=write,
            max_markets=max_markets,
            max_calls=max_calls,
            page_limit=page_limit,
            fetcher=fetcher,
            root=root,
        )
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


def run_fetch_one_refined(
    write=False,
    max_markets=MAX_MARKETS_HARD_CAP,
    max_calls=REFINED_DEFAULT_MAX_CALLS,
    page_limit=DEFAULT_PAGE_LIMIT,
    fetcher=None,
    root=ROOT,
):
    discovery = discover_one_weather_market_refined(
        fetcher=fetcher,
        max_markets=max_markets,
        max_calls=max_calls,
        page_limit=page_limit,
    )
    selected = discovery.get("selected_market") or {}
    payload = {
        "schema_version": "weather_market_discovery_refined_run_result.v1",
        "task_id": REFINED_TASK_ID,
        "status": discovery["status"],
        "fetch_status": discovery["fetch_status"],
        "refinement_attempt": True,
        "previous_attempt_reference": {
            "task_id": TASK_ID,
            "result_path": PREVIOUS_ATTEMPT_RESULT_PATH,
            "status": _previous_attempt_status(root=root),
        },
        "network_allowed_explicitly": True,
        "public_readonly_only": True,
        "network_call_count": discovery["network_call_count"],
        "polymarket_api_calls_performed": discovery["network_call_count"],
        "non_polymarket_public_source_calls_performed": 0,
        "endpoint_or_url_used": discovery["endpoint_or_url_used"],
        "selected_market_id": _as_text(selected.get("id")) or None,
        "selected_market_title_or_question": _as_text(selected.get("question")) or None,
        "inspected_candidate_count": discovery.get("inspected_market_count", 0),
        "weather_like_candidate_count": discovery.get("weather_like_candidate_count", 0),
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
        written = write_refined_artifacts(discovery, root=root)
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
    parser.add_argument("--refined-search", action="store_true")
    return parser.parse_args(argv)


def main(argv):
    args = _parse_args(argv)
    try:
        _validate_max_markets(args.max_markets)
        _validate_max_calls(args.max_calls, refined_search=args.refined_search)
        _validate_page_limit(args.page_limit)
    except ValueError as exc:
        raise SystemExit(str(exc))
    if args.summary_only:
        payload = build_summary_only(refined_search=args.refined_search)
    elif args.fetch_one:
        payload = run_fetch_one(
            write=args.write,
            max_markets=args.max_markets,
            max_calls=args.max_calls,
            page_limit=args.page_limit,
            refined_search=args.refined_search,
        )
    else:
        if args.write:
            raise SystemExit("--write is only valid with --fetch-one")
        payload = build_dry_run_status(
            max_markets=args.max_markets,
            max_calls=args.max_calls,
            refined_search=args.refined_search,
        )
    print(json.dumps(payload, indent=2, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(__import__("sys").argv[1:]))
