import argparse
import json
import re
import sys
from collections import Counter
from datetime import date, datetime
from pathlib import Path


TASK_ID = "PMBOT-RESEARCH-005-LOWER-RISK-SHORTLIST-TIERING"
SCHEMA_VERSION = "market_research_candidate_queue.v1"
ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SOURCE = ROOT / "local_snapshots" / "polymarket_markets_active_500_001.json"
DEFAULT_TOP_N = 10
DEFAULT_SHORTLIST_N = 10
SNAPSHOT_REVIEW_DATE = date(2026, 4, 27)
SAFETY_FLAGS = {
    "offline_only": True,
    "paper_only": True,
    "live_fetcher_implemented": False,
    "api_used": False,
    "network_used": False,
    "wallet_used": False,
    "real_order_created": False,
    "trading_allowed": False,
    "runtime_wiring_changed": False,
    "dispatcher_touched": False,
    "prompt_automation_added": False,
}

SPORTS_RE = re.compile(
    r"\b(nba|nhl|nfl|mlb|fifa|uefa|world cup|stanley cup|super bowl|finals|championship|"
    r"champions league|masters|wimbledon|team|season|playoffs?)\b",
    re.IGNORECASE,
)
SPORTS_WINNER_RE = re.compile(
    r"\b(win|winner|champion|championship|finals|stanley cup|super bowl|world cup)\b",
    re.IGNORECASE,
)
LEGAL_RE = re.compile(
    r"\b(court|scotus|supreme court|sentenced|prison|trial|lawsuit|sec|doj|convicted|"
    r"indicted|impeached|case|appeal|injunction|verdict)\b",
    re.IGNORECASE,
)
DIPLOMATIC_RE = re.compile(
    r"\b(ceasefire|russia|ukraine|china|taiwan|iran|israel|gaza|hamas|war|peace|nato|"
    r"sanction|tariff|invasion|invade|netanyahu|putin|xi jinping)\b",
    re.IGNORECASE,
)
POLITICAL_RE = re.compile(
    r"\b(trump|biden|president|election|senate|congress|governor|mayor|democrat|"
    r"republican|nomination|presidential|parliament|minister|primary)\b",
    re.IGNORECASE,
)
CRYPTO_RE = re.compile(
    r"\b(btc|eth|bitcoin|ethereum|solana|xrp|dogecoin|crypto|cryptocurrency)\b",
    re.IGNORECASE,
)
ENTERTAINMENT_RE = re.compile(
    r"\b(gta|album|oscar|grammy|movie|film|box office|netflix|drake|rihanna|playboi|"
    r"taylor swift|release|video game)\b",
    re.IGNORECASE,
)
MEME_OR_RELIGIOUS_RE = re.compile(
    r"\b(jesus|christ|god|rapture|messiah|alien|ufo|paranormal|meme|simulation)\b",
    re.IGNORECASE,
)
CELEBRITY_RUMOR_RE = re.compile(
    r"\b(divorce|pregnant|pregnancy|dating|break ?up|engaged|arrested|dead|dies|death|"
    r"rehab|scandal)\b",
    re.IGNORECASE,
)
OFFICIAL_SOURCE_RE = re.compile(
    r"\b(resolve|resolution|official|court|docket|filing|announced|announcement|certified|"
    r"reported|credible media|primary source|source)\b",
    re.IGNORECASE,
)
CLEAR_QUESTION_RE = re.compile(
    r"\b(before|by|on or before|end of|between|less than|more than|above|below|hit|win|"
    r"sentenced|accepted|released|out as|out by)\b",
    re.IGNORECASE,
)
ELECTION_RE = re.compile(r"\b(election|primary|nomination|presidential|midterm|senate|house)\b", re.IGNORECASE)
PRIMARY_RE = re.compile(r"\bprimary\b", re.IGNORECASE)
BEFORE_GTA_VI_RE = re.compile(r"\bbefore\s+gta\s*vi\b|\bgta\s*vi\b", re.IGNORECASE)
GEOPOLITICAL_TAIL_RE = re.compile(
    r"\b(ceasefire|russia|china|ukraine|taiwan|invasion|invade|war|hamas|gaza|iran|israel)\b",
    re.IGNORECASE,
)
WAR_INVASION_CEASEFIRE_RE = re.compile(r"\b(ceasefire|invasion|invades?|invaded|invading|war)\b", re.IGNORECASE)
EVENT_DEPENDENT_RE = re.compile(
    r"\b(before gta\s*vi|out as|out by|out before|resign|impeached|pardon|announced as next|no one announced)\b",
    re.IGNORECASE,
)
SUPPORTED_SHORTLIST_PACKET_TYPES = {
    "crypto_threshold_hit",
    "diplomatic_event",
    "legal_event",
    "political_event",
}


def _parse_args(argv):
    parser = argparse.ArgumentParser(description="Build an offline market research candidate queue from a saved Gamma snapshot.")
    parser.add_argument("--source", default=str(DEFAULT_SOURCE))
    parser.add_argument("--markdown", action="store_true")
    parser.add_argument("--top-n", type=int, default=DEFAULT_TOP_N)
    parser.add_argument("--shortlist-n", type=int, default=DEFAULT_SHORTLIST_N)
    return parser.parse_args(argv[1:])


def _resolve_path(path):
    value = Path(path)
    if value.is_absolute():
        return value
    return ROOT / value


def _load_json(path):
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _json_list(value):
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return []
        return parsed if isinstance(parsed, list) else []
    return []


def _float_or_none(value):
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _clamp(value, low=0.0, high=1.0):
    return max(low, min(high, value))


def _round_score(value):
    return round(_clamp(value), 4)


def _round_number(value):
    if value is None:
        return None
    return round(float(value), 4)


def _market_rows(payload):
    if isinstance(payload, list):
        return payload, "top_level_list"
    if isinstance(payload, dict):
        for key in ("markets", "data", "results"):
            rows = payload.get(key)
            if isinstance(rows, list):
                return rows, f"object_{key}_list"
    return [], "unsupported"


def _looks_like_gamma_rows(rows):
    for row in rows:
        if not isinstance(row, dict):
            continue
        has_identity = row.get("id") is not None or row.get("conditionId") is not None
        has_market_shape = any(key in row for key in ("question", "title", "outcomes", "outcomePrices"))
        if has_identity and has_market_shape:
            return True
    return False


def _market_id(row):
    value = row.get("id") or row.get("marketId") or row.get("market_id") or row.get("conditionId") or row.get("condition_id")
    return str(value) if value is not None else "unknown"


def _title(row):
    value = row.get("question") or row.get("title") or row.get("slug") or ""
    return str(value).strip()


def _category(row):
    value = row.get("category")
    if value:
        return str(value).strip()
    for event in _json_list(row.get("events")):
        if isinstance(event, dict):
            title = event.get("title") or event.get("slug")
            if title:
                return str(title).strip()
    return None


def _tags(row):
    tags = []
    for tag in _json_list(row.get("tags")):
        if isinstance(tag, dict):
            value = tag.get("label") or tag.get("name") or tag.get("slug") or tag.get("id")
            if value:
                tags.append(str(value).strip())
        elif tag:
            tags.append(str(tag).strip())
    return tags


def _text_parts(row):
    parts = []
    for key in ("question", "title", "slug", "description", "category", "resolutionSource"):
        value = row.get(key) if isinstance(row, dict) else None
        if value:
            parts.append(str(value))
    for tag in _tags(row):
        parts.append(tag)
    for event in _json_list(row.get("events") if isinstance(row, dict) else None):
        if isinstance(event, dict):
            for key in ("title", "slug", "description"):
                value = event.get(key)
                if value:
                    parts.append(str(value))
    return " ".join(parts)


def _outcome_names(row):
    return [str(item).strip() for item in _json_list(row.get("outcomes")) if str(item).strip()]


def _outcome_prices(row):
    return [_float_or_none(item) for item in _json_list(row.get("outcomePrices"))]


def _outcome_shape(row):
    names = [name.lower() for name in _outcome_names(row)]
    if len(names) > 2:
        return "multi_outcome"
    if len(names) == 2 and set(names) == {"yes", "no"}:
        return "yes_no"
    if len(names) == 2 and set(names) == {"up", "down"}:
        return "up_down"
    if len(names) == 2:
        return "binary_non_yes_no"
    return "unknown"


def _yes_price(row):
    names = [name.lower() for name in _outcome_names(row)]
    prices = _outcome_prices(row)
    for index, name in enumerate(names):
        if name == "yes" and index < len(prices):
            return _round_number(prices[index])
    return None


def _liquidity(row):
    for key in ("liquidityNum", "liquidity", "liquidityClob"):
        value = _float_or_none(row.get(key))
        if value is not None:
            return _round_number(value)
    return None


def _parse_date(value):
    if not value:
        return None
    text = str(value).strip()
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).date()
    except ValueError:
        try:
            return date.fromisoformat(text[:10])
        except ValueError:
            return None


def _deadline(row):
    value = row.get("endDate") or row.get("endDateIso")
    parsed = _parse_date(value)
    if parsed is None:
        return None, None
    return parsed.isoformat(), (parsed - SNAPSHOT_REVIEW_DATE).days


def _detect_topic(text):
    if MEME_OR_RELIGIOUS_RE.search(text):
        return "unclear_meme_or_religious"
    political_hit = POLITICAL_RE.search(text) is not None
    legal_hit = LEGAL_RE.search(text) is not None
    election_hit = re.search(r"\b(election|primary|nomination|presidential)\b", text, re.IGNORECASE) is not None
    if legal_hit and not (political_hit and election_hit):
        return "legal_event"
    if SPORTS_RE.search(text):
        return "sports_event"
    if DIPLOMATIC_RE.search(text):
        return "diplomatic_event"
    if political_hit:
        return "political_event"
    if CRYPTO_RE.search(text):
        return "crypto_numeric_threshold"
    if ENTERTAINMENT_RE.search(text):
        return "entertainment_event"
    if CELEBRITY_RUMOR_RE.search(text):
        return "celebrity_rumor"
    return "unsupported_or_unclear"


def _packet_type(topic, is_long_horizon_sports):
    if is_long_horizon_sports:
        return "sports_long_horizon"
    if topic == "political_event":
        return "political_event"
    if topic == "diplomatic_event":
        return "diplomatic_event"
    if topic == "legal_event":
        return "legal_event"
    if topic == "crypto_numeric_threshold":
        return "crypto_threshold_hit"
    if topic == "entertainment_event":
        return "entertainment_event"
    return "unsupported"


def _resolution_clarity_score(row, text, outcome_shape, deadline_value, topic):
    score = 0.12
    if outcome_shape == "yes_no":
        score += 0.18
    elif outcome_shape == "binary_non_yes_no":
        score += 0.1
    description = str(row.get("description") or "")
    if OFFICIAL_SOURCE_RE.search(description):
        score += 0.28
    elif OFFICIAL_SOURCE_RE.search(text):
        score += 0.18
    if CLEAR_QUESTION_RE.search(_title(row)):
        score += 0.18
    if deadline_value is not None:
        score += 0.1
    if topic in ("diplomatic_event", "legal_event", "political_event", "crypto_numeric_threshold"):
        score += 0.12
    elif topic == "entertainment_event":
        score += 0.05
    elif topic == "unclear_meme_or_religious":
        score -= 0.45
    if len(description.strip()) < 80:
        score -= 0.08
    return _round_score(score)


def _liquidity_score(liquidity):
    if liquidity is None:
        return 0.2
    if liquidity < 1000:
        return 0.0
    if liquidity < 5000:
        return 0.2
    if liquidity < 10000:
        return 0.45
    if liquidity < 50000:
        return 0.7
    if liquidity < 250000:
        return 0.9
    return 1.0


def _deadline_score(days_until_deadline):
    if days_until_deadline is None:
        return 0.25
    if days_until_deadline < 0:
        return 0.0
    if days_until_deadline <= 3:
        return 0.55
    if days_until_deadline <= 30:
        return 1.0
    if days_until_deadline <= 120:
        return 0.85
    if days_until_deadline <= 365:
        return 0.55
    if days_until_deadline <= 730:
        return 0.25
    return 0.1


def _source_availability_likelihood(row, text, topic):
    by_topic = {
        "diplomatic_event": 0.88,
        "legal_event": 0.92,
        "political_event": 0.82,
        "crypto_numeric_threshold": 0.86,
        "sports_event": 0.62,
        "entertainment_event": 0.58,
        "celebrity_rumor": 0.25,
        "unclear_meme_or_religious": 0.08,
        "unsupported_or_unclear": 0.35,
    }
    score = by_topic.get(topic, 0.35)
    description = str(row.get("description") or "")
    if OFFICIAL_SOURCE_RE.search(description):
        score += 0.08
    elif OFFICIAL_SOURCE_RE.search(text):
        score += 0.04
    if CELEBRITY_RUMOR_RE.search(text):
        score -= 0.18
    return _round_score(score)


def _market_price_research_value(yes_price, days_until_deadline, source_score):
    if yes_price is None:
        return 0.2
    distance = abs(yes_price - 0.5)
    if distance <= 0.15:
        return 1.0
    if distance <= 0.3:
        return 0.75
    if distance <= 0.42:
        return 0.45
    near_term_verifiable = days_until_deadline is not None and 0 <= days_until_deadline <= 21 and source_score >= 0.75
    return 0.4 if near_term_verifiable else 0.08


def _risk_penalty(topic, text, liquidity, yes_price, days_until_deadline, is_long_horizon_sports, outcome_shape):
    penalty = 0.0
    if topic == "unclear_meme_or_religious":
        penalty += 0.7
    if topic == "celebrity_rumor" or CELEBRITY_RUMOR_RE.search(text):
        penalty += 0.35
    if is_long_horizon_sports:
        penalty += 0.42
    elif topic == "sports_event" and SPORTS_WINNER_RE.search(text):
        penalty += 0.25
    if liquidity is None:
        penalty += 0.18
    elif liquidity < 1000:
        penalty += 0.5
    elif liquidity < 5000:
        penalty += 0.35
    elif liquidity < 10000:
        penalty += 0.15
    if yes_price is None:
        penalty += 0.2
    elif yes_price <= 0.03 or yes_price >= 0.97:
        penalty += 0.28
    elif yes_price <= 0.08 or yes_price >= 0.92:
        penalty += 0.18
    if days_until_deadline is None:
        penalty += 0.12
    elif days_until_deadline < 0:
        penalty += 0.55
    elif days_until_deadline > 730:
        penalty += 0.16
    elif days_until_deadline > 365:
        penalty += 0.1
    if outcome_shape not in ("yes_no", "binary_non_yes_no"):
        penalty += 0.25
    return round(penalty, 4)


def _priority(score, topic, liquidity, days_until_deadline, outcome_shape):
    if topic == "unclear_meme_or_religious":
        return "reject"
    if liquidity is not None and liquidity < 5000:
        return "reject"
    if days_until_deadline is not None and days_until_deadline < 0:
        return "reject"
    if outcome_shape not in ("yes_no", "binary_non_yes_no"):
        return "reject"
    if score >= 0.72:
        return "high"
    if score >= 0.55:
        return "medium"
    if score >= 0.3:
        return "low"
    return "reject"


def _reason_codes(
    row,
    topic,
    outcome_shape,
    liquidity,
    yes_price,
    days_until_deadline,
    clarity_score,
    liquidity_score,
    source_score,
    price_value,
    is_long_horizon_sports,
    priority,
):
    codes = []
    if outcome_shape == "yes_no":
        codes.append("clear_yes_no_market")
    elif outcome_shape in ("multi_outcome", "unknown"):
        codes.append("unsupported_outcome_shape")
    if clarity_score >= 0.78:
        codes.append("clear_resolution_criteria")
    else:
        codes.append("limited_resolution_detail")
    if source_score >= 0.75:
        codes.append("identifiable_official_or_news_sources_likely")
    elif source_score <= 0.3:
        codes.append("weak_source_availability")
    if liquidity is None:
        codes.append("missing_liquidity")
    elif liquidity < 5000:
        codes.append("low_liquidity")
    elif liquidity_score < 0.7:
        codes.append("thin_liquidity")
    else:
        codes.append("sufficient_liquidity")
    if days_until_deadline is None:
        codes.append("missing_deadline")
    elif days_until_deadline < 0:
        codes.append("deadline_in_past")
    elif days_until_deadline <= 30:
        codes.append("near_term_deadline")
    elif days_until_deadline <= 120:
        codes.append("medium_horizon_deadline")
    else:
        codes.append("long_horizon_deadline")
    if yes_price is None:
        codes.append("missing_yes_price")
    elif price_value >= 0.75:
        codes.append("market_price_research_value")
    elif yes_price <= 0.08 or yes_price >= 0.92:
        codes.append("extreme_price_downranked")
    if is_long_horizon_sports:
        codes.append("sports_long_horizon_downranked")
    elif topic == "sports_event" and SPORTS_WINNER_RE.search(_text_parts(row)):
        codes.append("sports_future_downranked")
    if topic == "unclear_meme_or_religious":
        codes.append("unclear_meme_or_religious_rejected")
    if CELEBRITY_RUMOR_RE.search(_text_parts(row)):
        codes.append("celebrity_rumor_downranked")
    if priority == "reject":
        codes.append("research_rejected")
    else:
        codes.append("research_queue_candidate")
    return codes


def _has_near_term_catalyst(row):
    days_until_deadline = row["days_until_deadline"]
    if days_until_deadline is not None and 0 <= days_until_deadline <= 120:
        return True
    text = f"{row['title']} {row.get('category') or ''}"
    return bool(CLEAR_QUESTION_RE.search(text) and days_until_deadline is not None and days_until_deadline <= 180)


def _uncertainty_reason_codes(
    row,
    text,
    topic,
    outcome_shape,
    liquidity,
    yes_price,
    days_until_deadline,
    clarity_score,
    source_score,
    is_long_horizon_sports,
    priority,
):
    codes = []
    title_and_category = f"{_title(row)} {_category(row) or ''}"
    election_or_primary = ELECTION_RE.search(title_and_category) is not None
    primary_market = PRIMARY_RE.search(title_and_category) is not None

    if BEFORE_GTA_VI_RE.search(text):
        codes.append("before_gta_vi_meta_event")
        codes.append("event_dependent_resolution")
    if GEOPOLITICAL_TAIL_RE.search(text):
        codes.append("geopolitical_tail_risk")
    if WAR_INVASION_CEASEFIRE_RE.search(text):
        codes.append("war_invasion_or_ceasefire_tail_risk")
    if EVENT_DEPENDENT_RE.search(text):
        if "event_dependent_resolution" not in codes:
            codes.append("event_dependent_resolution")
    if primary_market:
        codes.append("primary_market_uncertainty")
    if election_or_primary and days_until_deadline is not None and days_until_deadline > 120:
        codes.append("long_horizon_election_or_primary")
    if election_or_primary and not primary_market and days_until_deadline is not None and days_until_deadline > 180:
        codes.append("long_horizon_election_uncertainty")
    if topic == "political_event" and election_or_primary:
        codes.append("election_candidate_field_uncertainty")
    if outcome_shape not in ("yes_no", "binary_non_yes_no"):
        codes.append("unsupported_outcome_shape_uncertainty")
    if clarity_score < 0.78:
        codes.append("resolution_ambiguity_uncertainty")
    if source_score < 0.75:
        codes.append("source_availability_uncertainty")
    if liquidity is None:
        codes.append("missing_liquidity_uncertainty")
    elif liquidity < 10000:
        codes.append("low_liquidity_uncertainty")
    elif liquidity < 50000:
        codes.append("thin_liquidity_uncertainty")
    if days_until_deadline is None:
        codes.append("missing_deadline_uncertainty")
    elif days_until_deadline < 0:
        codes.append("past_deadline_uncertainty")
    elif days_until_deadline > 365:
        codes.append("long_horizon_uncertainty")
    if yes_price is None:
        codes.append("missing_yes_price_uncertainty")
    elif yes_price <= 0.08 or yes_price >= 0.92:
        codes.append("extreme_price_uncertainty")
    if is_long_horizon_sports:
        codes.append("sports_long_horizon_uncertainty")
    elif topic == "sports_event" and SPORTS_WINNER_RE.search(text):
        codes.append("sports_future_uncertainty")
    if topic == "unclear_meme_or_religious":
        codes.append("meme_or_religious_uncertainty")
    if topic == "celebrity_rumor" or CELEBRITY_RUMOR_RE.search(text):
        codes.append("celebrity_rumor_uncertainty")
    if topic == "unsupported_or_unclear":
        codes.append("unsupported_topic_uncertainty")
    if priority == "reject":
        codes.append("research_reject_uncertainty")
    return codes


def _risk_tier(uncertainty_codes):
    points = 0
    point_weights = {
        "before_gta_vi_meta_event": 3,
        "event_dependent_resolution": 2,
        "geopolitical_tail_risk": 2,
        "war_invasion_or_ceasefire_tail_risk": 3,
        "primary_market_uncertainty": 2,
        "long_horizon_election_or_primary": 2,
        "long_horizon_election_uncertainty": 2,
        "election_candidate_field_uncertainty": 1,
        "unsupported_outcome_shape_uncertainty": 2,
        "resolution_ambiguity_uncertainty": 2,
        "source_availability_uncertainty": 2,
        "missing_liquidity_uncertainty": 2,
        "low_liquidity_uncertainty": 2,
        "thin_liquidity_uncertainty": 1,
        "missing_deadline_uncertainty": 2,
        "past_deadline_uncertainty": 3,
        "long_horizon_uncertainty": 2,
        "missing_yes_price_uncertainty": 2,
        "extreme_price_uncertainty": 2,
        "sports_long_horizon_uncertainty": 3,
        "sports_future_uncertainty": 2,
        "meme_or_religious_uncertainty": 4,
        "celebrity_rumor_uncertainty": 3,
        "unsupported_topic_uncertainty": 2,
        "research_reject_uncertainty": 2,
    }
    for code in uncertainty_codes:
        points += point_weights.get(code, 1)
    if points >= 8:
        return "extreme"
    if points >= 4:
        return "high"
    if points >= 2:
        return "medium"
    return "low"


def _shortlist_deadline_score(days_until_deadline):
    if days_until_deadline is None or days_until_deadline < 0:
        return 0.0
    if days_until_deadline <= 3:
        return 0.65
    if days_until_deadline <= 45:
        return 1.0
    if days_until_deadline <= 120:
        return 0.9
    if days_until_deadline <= 180:
        return 0.58
    if days_until_deadline <= 365:
        return 0.32
    if days_until_deadline <= 730:
        return 0.08
    return 0.0


def _shortlist_deadline_reason(days_until_deadline):
    if days_until_deadline is None:
        return "shortlist_missing_deadline"
    if days_until_deadline < 0:
        return "shortlist_deadline_in_past"
    if days_until_deadline <= 45:
        return "shortlist_near_term_deadline"
    if days_until_deadline <= 120:
        return "shortlist_medium_deadline"
    return "shortlist_long_horizon_deadline"


def _shortlist_score_and_reasons(row):
    codes = []
    topic = row["detected_topic_category_type"]
    packet_type = row["suggested_research_packet_type"]
    days_until_deadline = row["days_until_deadline"]
    yes_price = row["yes_price"]
    liquidity = row["liquidity"]
    source_score = row["source_availability_likelihood_score"]
    near_term_verifiable = days_until_deadline is not None and 0 <= days_until_deadline <= 21 and source_score >= 0.75
    uncertainty_codes = set(row["uncertainty_reason_codes"])
    near_term_catalyst = _has_near_term_catalyst(row)

    if row["research_priority"] == "reject":
        codes.append("shortlist_research_rejected_excluded")
    if row["risk_tier"] in ("low", "medium"):
        codes.append(f"shortlist_{row['risk_tier']}_risk_candidate")
    else:
        codes.append(f"shortlist_{row['risk_tier']}_risk_excluded")
    if packet_type in SUPPORTED_SHORTLIST_PACKET_TYPES:
        codes.append("shortlist_supported_packet_type")
    else:
        codes.append("shortlist_unsupported_packet_type")
    if row["outcome_shape"] == "yes_no":
        codes.append("shortlist_clear_yes_no_market")
    else:
        codes.append("shortlist_unsupported_outcome_shape")
    if row["resolution_clarity_score"] >= 0.78:
        codes.append("shortlist_clear_resolution_criteria")
    else:
        codes.append("shortlist_limited_resolution_detail")
    if source_score >= 0.75:
        codes.append("shortlist_official_or_news_sources_likely")
    else:
        codes.append("shortlist_weak_source_availability")
    if liquidity is None:
        codes.append("shortlist_missing_liquidity")
    elif liquidity < 10000:
        codes.append("shortlist_low_liquidity_excluded")
    elif liquidity < 50000:
        codes.append("shortlist_thin_liquidity")
    else:
        codes.append("shortlist_sufficient_liquidity")
    codes.append(_shortlist_deadline_reason(days_until_deadline))
    if yes_price is None:
        codes.append("shortlist_missing_yes_price")
    elif yes_price <= 0.03 or yes_price >= 0.97:
        codes.append("shortlist_extreme_price_near_verifiable" if near_term_verifiable else "shortlist_extreme_price_excluded")
    elif yes_price <= 0.08 or yes_price >= 0.92:
        codes.append("shortlist_extreme_price_downranked")
    else:
        codes.append("shortlist_price_researchable")
    if "before_gta_vi_meta_event" in uncertainty_codes:
        codes.append("shortlist_meta_event_excluded")
    if "war_invasion_or_ceasefire_tail_risk" in uncertainty_codes:
        codes.append("shortlist_war_invasion_or_ceasefire_excluded")
    elif "geopolitical_tail_risk" in uncertainty_codes:
        codes.append("shortlist_geopolitical_tail_risk_downranked")
    if "event_dependent_resolution" in uncertainty_codes:
        codes.append("shortlist_event_dependent_resolution_downranked")
    if "primary_market_uncertainty" in uncertainty_codes:
        codes.append("shortlist_primary_market_near_term_catalyst" if near_term_catalyst else "shortlist_primary_market_no_near_term_catalyst")
    if "long_horizon_election_or_primary" in uncertainty_codes:
        codes.append("shortlist_long_horizon_primary_or_election_downranked")

    score = (
        (row["resolution_clarity_score"] * 0.24)
        + (row["source_availability_likelihood_score"] * 0.22)
        + (_shortlist_deadline_score(days_until_deadline) * 0.2)
        + (row["liquidity_score"] * 0.16)
        + (row["market_price_research_value_score"] * 0.1)
        + (0.04 if row["outcome_shape"] == "yes_no" else 0.0)
        + (0.04 if packet_type in SUPPORTED_SHORTLIST_PACKET_TYPES else 0.0)
    )
    if topic in ("diplomatic_event", "legal_event"):
        score += 0.04
    elif topic == "crypto_numeric_threshold":
        score += 0.03

    if row["research_priority"] == "medium":
        score -= 0.05
    elif row["research_priority"] == "low":
        score -= 0.15
    elif row["research_priority"] == "reject":
        score -= 0.6
    if packet_type not in SUPPORTED_SHORTLIST_PACKET_TYPES:
        score -= 0.42
    if topic == "sports_event" or "sports_future_downranked" in row["reason_codes"]:
        score -= 0.45
        codes.append("shortlist_sports_future_excluded")
    if "sports_long_horizon_downranked" in row["reason_codes"]:
        score -= 0.25
        codes.append("shortlist_sports_long_horizon_excluded")
    if row["risk_tier"] == "medium":
        score -= 0.08
    elif row["risk_tier"] == "high":
        score -= 0.45
    elif row["risk_tier"] == "extreme":
        score -= 0.75
    if "before_gta_vi_meta_event" in uncertainty_codes:
        score -= 0.7
    if "war_invasion_or_ceasefire_tail_risk" in uncertainty_codes:
        score -= 0.65
    elif "geopolitical_tail_risk" in uncertainty_codes:
        score -= 0.25
    if "event_dependent_resolution" in uncertainty_codes:
        score -= 0.25
    if "primary_market_uncertainty" in uncertainty_codes:
        score -= 0.65 if near_term_catalyst else 0.75
    if topic == "political_event":
        if not _has_near_term_catalyst(row):
            score -= 0.08
            codes.append("shortlist_no_near_term_political_catalyst")
        if days_until_deadline is None or days_until_deadline > 120:
            score -= 0.14
            codes.append("shortlist_long_horizon_political_downranked")
        if ELECTION_RE.search(f"{row['title']} {row.get('category') or ''}") and (
            days_until_deadline is None or days_until_deadline > 120
        ):
            score -= 0.16
            codes.append("shortlist_long_horizon_election_downranked")
    if days_until_deadline is None:
        score -= 0.18
    elif days_until_deadline > 365:
        score -= 0.28
    elif days_until_deadline > 180:
        score -= 0.1
    if liquidity is None:
        score -= 0.25
    elif liquidity < 10000:
        score -= 0.35
    elif liquidity < 25000:
        score -= 0.08
    if yes_price is None:
        score -= 0.2
    elif yes_price <= 0.03 or yes_price >= 0.97:
        score -= 0.08 if near_term_verifiable else 0.38
    elif yes_price <= 0.08 or yes_price >= 0.92:
        score -= 0.08 if near_term_verifiable else 0.22

    return _round_score(score), codes


def _shortlist_eligible(row):
    if row["research_priority"] == "reject":
        return False
    if row["risk_tier"] in ("high", "extreme"):
        return False
    if row["suggested_research_packet_type"] not in SUPPORTED_SHORTLIST_PACKET_TYPES:
        return False
    if row["outcome_shape"] != "yes_no":
        return False
    if row["resolution_clarity_score"] < 0.78:
        return False
    if row["source_availability_likelihood_score"] < 0.75:
        return False
    if row["liquidity"] is None or row["liquidity"] < 10000:
        return False
    if row["days_until_deadline"] is None or row["days_until_deadline"] < 0 or row["days_until_deadline"] > 365:
        return False
    if "shortlist_sports_future_excluded" in row["shortlist_reason_codes"]:
        return False
    if "shortlist_sports_long_horizon_excluded" in row["shortlist_reason_codes"]:
        return False
    if "shortlist_meta_event_excluded" in row["shortlist_reason_codes"]:
        return False
    if "shortlist_war_invasion_or_ceasefire_excluded" in row["shortlist_reason_codes"]:
        return False
    if (
        "primary_market_uncertainty" in row["uncertainty_reason_codes"]
        and "shortlist_primary_market_no_near_term_catalyst" in row["shortlist_reason_codes"]
    ):
        return False
    return row["shortlist_score"] >= 0.33


def _why_selected_for_research(row):
    return (
        f"{row['research_tier']} candidate with {row['research_priority']} research priority: "
        f"{row['outcome_shape']} market, {row['suggested_research_packet_type']} packet type, "
        f"liquidity={row['liquidity']}, deadline={row['deadline']}, "
        f"source_likelihood={row['source_availability_likelihood_score']}, risk_tier={row['risk_tier']}."
    )


def _why_not_lower_risk(row):
    if row["research_tier"] == "lower_risk_operator_shortlist":
        return "Selected for the lower-risk operator shortlist after passing clarity, source, liquidity, deadline, and risk-tier checks."
    if row["research_tier"] == "reject":
        return "Rejected from the research queue by baseline market suitability checks."
    if row["risk_tier"] in ("high", "extreme"):
        return f"Not lower-risk because uncertainty codes include: {', '.join(row['uncertainty_reason_codes'])}."
    if row["shortlist_score"] < 0.55:
        return f"Not lower-risk because shortlist_score={row['shortlist_score']} is below the lower-risk threshold."
    return "Not lower-risk because it was outside the capped operator shortlist after deterministic ranking."


def _why_not_bet_yet(row):
    if row["operator_shortlist"]:
        return "Lower-risk shortlist only: build a local research packet and edge/risk review before any paper-only workflow."
    if row["research_tier"] == "researchable_high_uncertainty":
        return "High-uncertainty research queue only: requires a local research packet, edge review, and risk review before any paper-only workflow."
    return "Watch-only research queue: not in the lower-risk operator shortlist and still needs local review before any paper-only workflow."


def _annotate_shortlist(ranked, shortlist_n):
    shortlist_n = max(0, int(shortlist_n))
    for row in ranked:
        score, reason_codes = _shortlist_score_and_reasons(row)
        row["operator_shortlist"] = False
        row["shortlist_rank"] = None
        row["shortlist_score"] = score
        row["shortlist_reason_codes"] = reason_codes
        row["research_tier"] = "watch_only"
        row["why_selected_for_research"] = "pending tier calibration"
        row["why_not_lower_risk"] = "pending tier calibration"
        row["why_not_bet_yet"] = "pending shortlist calibration"

    eligible = [row for row in ranked if _shortlist_eligible(row)]
    eligible.sort(key=lambda row: (-row["shortlist_score"], row["rank"], row["market_id"], row["title"]))
    selected = eligible[:shortlist_n]
    for index, row in enumerate(selected, start=1):
        row["operator_shortlist"] = True
        row["shortlist_rank"] = index
        row["research_tier"] = "lower_risk_operator_shortlist"
        row["shortlist_reason_codes"] = [*row["shortlist_reason_codes"], "operator_shortlist_candidate"]

    for row in ranked:
        if not row["operator_shortlist"]:
            row["shortlist_reason_codes"] = [*row["shortlist_reason_codes"], "researchable_not_operator_shortlist"]
            if row["risk_tier"] in ("high", "extreme"):
                row["research_tier"] = "researchable_high_uncertainty"
            else:
                row["research_tier"] = "watch_only"
        row["why_selected_for_research"] = _why_selected_for_research(row)
        row["why_not_lower_risk"] = _why_not_lower_risk(row)
        row["why_not_bet_yet"] = _why_not_bet_yet(row)

    return selected, shortlist_n


def _shortlist_example(row):
    return {
        "shortlist_rank": row["shortlist_rank"],
        "market_id": row["market_id"],
        "title": row["title"],
        "research_tier": row["research_tier"],
        "risk_tier": row["risk_tier"],
        "research_priority": row["research_priority"],
        "shortlist_score": row["shortlist_score"],
        "suggested_research_packet_type": row["suggested_research_packet_type"],
        "shortlist_reason_codes": row["shortlist_reason_codes"],
    }


def _high_uncertainty_example(row):
    return {
        "rank": row["rank"],
        "market_id": row["market_id"],
        "title": row["title"],
        "research_tier": row["research_tier"],
        "risk_tier": row["risk_tier"],
        "research_priority": row["research_priority"],
        "suggested_research_packet_type": row["suggested_research_packet_type"],
        "uncertainty_reason_codes": row["uncertainty_reason_codes"],
        "why_not_lower_risk": row["why_not_lower_risk"],
    }


def _score_market(row):
    text = _text_parts(row)
    title = _title(row)
    topic = _detect_topic(text)
    outcome_shape = _outcome_shape(row)
    yes_price = _yes_price(row)
    liquidity = _liquidity(row)
    deadline_value, days_until_deadline = _deadline(row)
    is_long_horizon_sports = (
        topic == "sports_event"
        and SPORTS_WINNER_RE.search(text) is not None
        and (days_until_deadline is None or days_until_deadline > 45)
    )
    clarity_score = _resolution_clarity_score(row, text, outcome_shape, deadline_value, topic)
    liquidity_score = _liquidity_score(liquidity)
    deadline_score = _deadline_score(days_until_deadline)
    source_score = _source_availability_likelihood(row, text, topic)
    price_value = _market_price_research_value(yes_price, days_until_deadline, source_score)
    risk_penalty = _risk_penalty(topic, text, liquidity, yes_price, days_until_deadline, is_long_horizon_sports, outcome_shape)
    final_score = _round_score(
        (clarity_score * 0.3)
        + (liquidity_score * 0.2)
        + (deadline_score * 0.2)
        + (source_score * 0.2)
        + (price_value * 0.1)
        - risk_penalty
    )
    priority = _priority(final_score, topic, liquidity, days_until_deadline, outcome_shape)
    category = _category(row)
    packet_type = _packet_type(topic, is_long_horizon_sports)
    reason_codes = _reason_codes(
        row,
        topic,
        outcome_shape,
        liquidity,
        yes_price,
        days_until_deadline,
        clarity_score,
        liquidity_score,
        source_score,
        price_value,
        is_long_horizon_sports,
        priority,
    )
    uncertainty_reason_codes = _uncertainty_reason_codes(
        row,
        text,
        topic,
        outcome_shape,
        liquidity,
        yes_price,
        days_until_deadline,
        clarity_score,
        source_score,
        is_long_horizon_sports,
        priority,
    )
    risk_tier = _risk_tier(uncertainty_reason_codes)
    return {
        "market_id": _market_id(row),
        "title": title,
        "question": title,
        "category": category,
        "yes_price": yes_price,
        "liquidity": liquidity,
        "deadline": deadline_value,
        "days_until_deadline": days_until_deadline,
        "outcome_shape": outcome_shape,
        "detected_topic_category_type": topic,
        "resolution_clarity_score": clarity_score,
        "liquidity_score": _round_score(liquidity_score),
        "deadline_score": _round_score(deadline_score),
        "source_availability_likelihood_score": source_score,
        "market_price_research_value_score": _round_score(price_value),
        "risk_penalty": risk_penalty,
        "final_research_priority_score": final_score,
        "research_priority": priority,
        "research_tier": "reject" if priority == "reject" else "watch_only",
        "risk_tier": risk_tier,
        "reason_codes": reason_codes,
        "uncertainty_reason_codes": uncertainty_reason_codes,
        "suggested_research_packet_type": packet_type,
    }


def build_candidate_queue(source_path=None, top_n=DEFAULT_TOP_N, shortlist_n=DEFAULT_SHORTLIST_N):
    source_file = _resolve_path(source_path) if source_path else DEFAULT_SOURCE
    payload = _load_json(source_file)
    rows, top_level_shape = _market_rows(payload)
    scored = [_score_market(row) for row in rows if isinstance(row, dict)]
    scored.sort(
        key=lambda row: (
            -row["final_research_priority_score"],
            row["research_priority"],
            row["market_id"],
            row["title"],
        )
    )

    ranked = [row for row in scored if row["research_priority"] != "reject"]
    for index, row in enumerate(ranked, start=1):
        row["rank"] = index
    operator_shortlist, shortlist_top_n = _annotate_shortlist(ranked, shortlist_n)
    priority_counts = Counter(row["research_priority"] for row in scored)
    research_tier_counts = Counter(row["research_tier"] for row in scored)
    risk_tier_counts = Counter(row["risk_tier"] for row in scored)
    reason_counts = Counter()
    for row in scored:
        reason_counts.update(row["reason_codes"])
        reason_counts.update(row["uncertainty_reason_codes"])
    shortlist_reason_counts = Counter()
    for row in ranked:
        shortlist_reason_counts.update(row["shortlist_reason_codes"])
    high_uncertainty = [row for row in ranked if row["research_tier"] == "researchable_high_uncertainty"]
    top_n = max(0, int(top_n))
    return {
        "schema_version": SCHEMA_VERSION,
        "task_id": TASK_ID,
        "deterministic": True,
        "snapshot_review_date": SNAPSHOT_REVIEW_DATE.isoformat(),
        "source_path": str(source_file),
        "source_shape": "polymarket_gamma_markets_response" if _looks_like_gamma_rows(rows) else "unsupported",
        "top_level_shape": top_level_shape,
        "top_n": top_n,
        "shortlist_top_n": shortlist_top_n,
        "markets_seen": len(rows),
        "total_markets_seen": len(rows),
        "candidates_ranked": len(ranked),
        "high_priority_count": priority_counts["high"],
        "medium_priority_count": priority_counts["medium"],
        "low_priority_count": priority_counts["low"],
        "rejected_count": priority_counts["reject"],
        "researchable_high_uncertainty_count": research_tier_counts["researchable_high_uncertainty"],
        "lower_risk_operator_shortlist_count": research_tier_counts["lower_risk_operator_shortlist"],
        "watch_only_count": research_tier_counts["watch_only"],
        "operator_shortlist_count": len(operator_shortlist),
        "research_tier_counts": dict(sorted(research_tier_counts.items())),
        "risk_tier_counts": dict(sorted(risk_tier_counts.items())),
        "top_n_candidates": ranked[:top_n],
        "operator_shortlist_candidates": operator_shortlist,
        "shortlist_candidate_examples": [_shortlist_example(row) for row in operator_shortlist[:5]],
        "lower_risk_shortlist_examples": [_shortlist_example(row) for row in operator_shortlist[:5]],
        "high_uncertainty_examples": [_high_uncertainty_example(row) for row in high_uncertainty[:5]],
        "reason_code_counts": dict(sorted(reason_counts.items())),
        "shortlist_reason_code_counts": dict(sorted(shortlist_reason_counts.items())),
        "safety_flags": SAFETY_FLAGS,
        "limitations": [
            "Reads only a saved local Polymarket Gamma snapshot.",
            "Ranks research suitability only; scores are not betting advice and do not create research packets.",
            "Does not fetch sources, call APIs, use credentials, touch wallets, create orders, trade, write workspace state, or connect to paper order planning.",
        ],
    }


def _md(value):
    if value is None:
        return ""
    text = str(value).encode("ascii", "backslashreplace").decode("ascii")
    return text.replace("|", "\\|").replace("\n", " ")


def render_markdown(report):
    lines = [
        "# Market Research Candidate Queue",
        "",
        f"- Task ID: {report['task_id']}",
        f"- Source: {report['source_path']}",
        f"- Snapshot review date: {report['snapshot_review_date']}",
        f"- Total markets seen: {report['total_markets_seen']}",
        f"- Candidates ranked: {report['candidates_ranked']}",
        f"- High priority count: {report['high_priority_count']}",
        f"- Medium priority count: {report['medium_priority_count']}",
        f"- Low priority count: {report['low_priority_count']}",
        f"- Rejected count: {report['rejected_count']}",
        f"- Lower-risk operator shortlist count: {report['lower_risk_operator_shortlist_count']}",
        f"- Researchable high-uncertainty count: {report['researchable_high_uncertainty_count']}",
        f"- Watch-only count: {report['watch_only_count']}",
        f"- Shortlist top N: {report['shortlist_top_n']}",
        "",
        "## Research Tier Counts",
        "",
    ]
    for tier, count in report["research_tier_counts"].items():
        lines.append(f"- {tier}: {count}")
    lines.extend(["", "## Risk Tier Counts", ""])
    for tier, count in report["risk_tier_counts"].items():
        lines.append(f"- {tier}: {count}")
    lines.extend(
        [
            "",
        "## Reason Code Counts",
        "",
        ]
    )
    for reason, count in report["reason_code_counts"].items():
        lines.append(f"- {reason}: {count}")
    lines.extend(["", "## Shortlist Reason Code Counts", ""])
    for reason, count in report["shortlist_reason_code_counts"].items():
        lines.append(f"- {reason}: {count}")
    lines.extend(
        [
            "",
            "## Operator Shortlist",
            "",
            "| shortlist_rank | market_id | research_tier | risk_tier | priority | shortlist_score | packet_type | yes_price | liquidity | deadline | shortlist_reason_codes | title |",
            "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for row in report["operator_shortlist_candidates"]:
        lines.append(
            f"| {_md(row['shortlist_rank'])} | {_md(row['market_id'])} | {_md(row['research_tier'])} | "
            f"{_md(row['risk_tier'])} | {_md(row['research_priority'])} | "
            f"{_md(row['shortlist_score'])} | {_md(row['suggested_research_packet_type'])} | "
            f"{_md(row['yes_price'])} | {_md(row['liquidity'])} | {_md(row['deadline'])} | "
            f"{_md(json.dumps(row['shortlist_reason_codes'], sort_keys=True))} | {_md(row['title'])} |"
        )
    lines.extend(
        [
            "",
            "## High-Uncertainty Examples",
            "",
            "| rank | market_id | risk_tier | priority | packet_type | uncertainty_reason_codes | title |",
            "| --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for row in report["high_uncertainty_examples"]:
        lines.append(
            f"| {_md(row['rank'])} | {_md(row['market_id'])} | {_md(row['risk_tier'])} | "
            f"{_md(row['research_priority'])} | {_md(row['suggested_research_packet_type'])} | "
            f"{_md(json.dumps(row['uncertainty_reason_codes'], sort_keys=True))} | {_md(row['title'])} |"
        )
    lines.extend(
        [
            "",
            "## Top Candidates",
            "",
            "| rank | shortlist_rank | operator_shortlist | market_id | research_tier | risk_tier | priority | score | shortlist_score | packet_type | topic | yes_price | liquidity | deadline | uncertainty_reason_codes | reason_codes | title |",
            "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for row in report["top_n_candidates"]:
        lines.append(
            f"| {_md(row['rank'])} | {_md(row['shortlist_rank'])} | {_md(str(row['operator_shortlist']).lower())} | "
            f"{_md(row['market_id'])} | {_md(row['research_tier'])} | {_md(row['risk_tier'])} | "
            f"{_md(row['research_priority'])} | {_md(row['final_research_priority_score'])} | "
            f"{_md(row['shortlist_score'])} | {_md(row['suggested_research_packet_type'])} | "
            f"{_md(row['detected_topic_category_type'])} | {_md(row['yes_price'])} | {_md(row['liquidity'])} | "
            f"{_md(row['deadline'])} | {_md(json.dumps(row['uncertainty_reason_codes'], sort_keys=True))} | "
            f"{_md(json.dumps(row['reason_codes'], sort_keys=True))} | {_md(row['title'])} |"
        )
    lines.extend(
        [
            "",
            "## Safety",
            "",
            "- offline_only=true; paper_only=true; live_fetcher_implemented=false; api_used=false; network_used=false; wallet_used=false; real_order_created=false; trading_allowed=false; runtime_wiring_changed=false; dispatcher_touched=false; prompt_automation_added=false",
            "",
        ]
    )
    return "\n".join(lines)


def main(argv):
    args = _parse_args(argv)
    report = build_candidate_queue(args.source, args.top_n, args.shortlist_n)
    if args.markdown:
        print(render_markdown(report), end="")
    else:
        print(json.dumps(report, indent=2, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
