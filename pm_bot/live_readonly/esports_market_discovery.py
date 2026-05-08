import argparse
import json
import re
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


TASK_ID = "PMBOT-SOURCE-009A-ESPORTS-MARKET-CLASS-PILOT-READONLY-DISCOVERY"
ROOT = Path(__file__).resolve().parents[2]

ARTIFACT_DIR = "pm_bot/live_readonly/esports_market_discovery"
RAW_FETCH_JSON = "esports_market_raw_fetch_009a.v1.json"
NORMALIZED_JSON = "esports_market_normalized_candidate_009a.v1.json"
SOURCE_CAPTURE_JSON = "esports_source_capture_candidate_009a.v1.json"
CHECKLIST_JSON = "esports_operator_review_checklist_009a.v1.json"
CHECKLIST_MD = "esports_operator_review_checklist_009a.v1.md"
RESULT_JSON = "docs/PMBOT_SOURCE_009A_RESULT.json"
RESULT_MD = "docs/PMBOT_SOURCE_009A_ESPORTS_MARKET_CLASS_PILOT_READONLY_DISCOVERY.md"

HEAD_BEFORE = "2ba640bf09cbce91e3accef8cfed4d31dd96cd5e"
FETCHED_AT_MARKER = "2026-05-08T00:00:00Z_SOURCE_009A_READONLY_FIELD_TEST"
GAMMA_BASE_URL = "https://gamma-api.polymarket.com"
ESPORTS_TAG_ID = "64"
DEFAULT_PAGE_LIMIT = 100
DEFAULT_MAX_EVENT_PAGES = 5
DEFAULT_TIMEOUT_SECONDS = 10
MAX_MARKETS_HARD_CAP = 1
CURRENT_DATE_MARKER = datetime(2026, 5, 8, tzinfo=timezone.utc)

PUBLIC_HEADERS = {
    "Accept": "application/json",
    "User-Agent": "PMBOT-SOURCE-009A-readonly-discovery/1.0",
}

ESPORTS_MARKERS = (
    "esports",
    "e-sports",
    "league of legends",
    "lol:",
    "counter-strike",
    "cs2",
    "dota 2",
    "dota2",
    "valorant",
    "rainbow six",
    "r6siege",
    "esports world cup",
)

GAME_TITLE_MARKERS = (
    ("lol", "League of Legends"),
    ("league of legends", "League of Legends"),
    ("counter-strike", "Counter-Strike 2"),
    ("cs2", "Counter-Strike 2"),
    ("dota 2", "Dota 2"),
    ("dota2", "Dota 2"),
    ("valorant", "Valorant"),
    ("rainbow six", "Rainbow Six Siege"),
    ("r6siege", "Rainbow Six Siege"),
)


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


def _write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )


def _safe_list(value):
    return value if isinstance(value, list) else []


def _as_text(value):
    if value is None:
        return ""
    return str(value).strip()


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


def _event_text(event):
    fields = [
        event.get("title"),
        event.get("slug"),
        event.get("description"),
        event.get("seriesSlug"),
    ]
    for tag in _safe_list(event.get("tags")):
        fields.extend([tag.get("label"), tag.get("slug")])
    for series in _safe_list(event.get("series")):
        fields.extend([series.get("title"), series.get("slug")])
    for market in _safe_list(event.get("markets")):
        fields.extend([market.get("question"), market.get("slug"), market.get("description")])
    return " ".join(_as_text(item) for item in fields).lower()


def _is_esports_event(event):
    text = _event_text(event)
    if not any(marker in text for marker in ESPORTS_MARKERS):
        return False
    title = _as_text(event.get("title")).lower()
    has_match_shape = " vs " in title and ("bo3" in title or "bo5" in title or "game" in title)
    return has_match_shape and _event_is_not_stale(event)


def _parse_datetime_marker(value):
    text = _as_text(value)
    if not text:
        return None
    normalized = text.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        try:
            parsed = datetime.fromisoformat(normalized.split()[0])
        except ValueError:
            return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _event_is_not_stale(event):
    values = [
        event.get("eventStartTime"),
        event.get("startTime"),
        event.get("eventDate"),
        event.get("endDate"),
    ]
    for market in _safe_list(event.get("markets")):
        values.extend(
            [
                market.get("eventStartTime"),
                market.get("gameStartTime"),
                market.get("endDate"),
            ]
        )
    for value in values:
        parsed = _parse_datetime_marker(value)
        if parsed is not None:
            return parsed >= CURRENT_DATE_MARKER
    return True


def _market_matches_event(event, market):
    if market.get("active") is not True or market.get("closed") is True:
        return False
    question = _as_text(market.get("question")).lower()
    if not question:
        return False
    if " vs " not in question:
        return False
    if not _as_text(market.get("description")):
        return False
    market_type = _as_text(market.get("sportsMarketType")).lower()
    if market_type == "moneyline":
        return True
    return question == _as_text(event.get("title")).lower()


def _select_market_from_event(event):
    markets = _safe_list(event.get("markets"))
    event_title = _as_text(event.get("title")).lower()
    for market in markets:
        if market.get("active") is True and market.get("closed") is not True:
            if _as_text(market.get("question")).lower() == event_title:
                return market
    for market in markets:
        if _market_matches_event(event, market):
            return market
    for market in markets:
        if market.get("active") is True and market.get("closed") is not True:
            question = _as_text(market.get("question")).lower()
            if " vs " in question and _as_text(market.get("description")):
                return market
    return None


def _event_list_url(offset, limit=DEFAULT_PAGE_LIMIT):
    query = urllib.parse.urlencode(
        {
            "active": "true",
            "closed": "false",
            "limit": str(limit),
            "offset": str(offset),
            "tag_id": ESPORTS_TAG_ID,
        }
    )
    return f"{GAMMA_BASE_URL}/events?{query}"


def _event_detail_url(slug):
    quoted_slug = urllib.parse.quote(slug, safe="")
    return f"{GAMMA_BASE_URL}/events/slug/{quoted_slug}"


def _empty_safety_summary(network_allowed, network_call_count):
    return {
        "network_allowed_explicitly": network_allowed,
        "public_readonly_only": True,
        "network_calls_performed": network_call_count,
        "polymarket_api_calls_performed": network_call_count,
        "openrouter_calls_performed": 0,
        "authenticated_endpoints_used": False,
        "wallet_or_private_key_accessed": False,
        "orders_created": False,
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
    }


def build_dry_run_status(max_markets=MAX_MARKETS_HARD_CAP):
    _validate_max_markets(max_markets)
    return {
        "schema_version": "esports_market_discovery_dry_run.v1",
        "task_id": TASK_ID,
        "status": "dry_run_no_network",
        "mode": "dry_run",
        "network_allowed_explicitly": False,
        "network_calls_performed": 0,
        "polymarket_api_calls_performed": 0,
        "fetch_performed": False,
        "max_markets": max_markets,
        "max_markets_hard_cap": MAX_MARKETS_HARD_CAP,
        "planned_public_readonly_endpoints": [
            f"{GAMMA_BASE_URL}/events",
            f"{GAMMA_BASE_URL}/events/slug/<slug>",
        ],
        "write_scope": "none_unless_fetch_one_and_write_are_passed",
        "operator_review_required": True,
        "planned_capture_status": "draft",
        "auto_promote_to_ready_for_local_review": False,
        "safety_summary": _empty_safety_summary(False, 0),
    }


def build_summary_only(root=ROOT):
    result_path = _resolve(RESULT_JSON, root=root)
    if not result_path.exists():
        return {
            "schema_version": "esports_market_discovery_summary_only.v1",
            "task_id": TASK_ID,
            "status": "summary_only_no_artifacts",
            "network_calls_performed": 0,
            "polymarket_api_calls_performed": 0,
            "openrouter_calls_performed": 0,
            "operator_review_required": True,
        }
    with result_path.open("r", encoding="utf-8") as handle:
        result = json.load(handle)
    return {
        "schema_version": "esports_market_discovery_summary_only.v1",
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
        raise ValueError("SOURCE-009A max_markets hard cap is exactly 1")


def _fetch_logged(fetcher, url, log):
    log["network_call_count"] += 1
    log["endpoint_or_url_used"].append(url)
    return fetcher.fetch_json(url)


def discover_one_esports_market(
    fetcher=None,
    max_markets=MAX_MARKETS_HARD_CAP,
    max_event_pages=DEFAULT_MAX_EVENT_PAGES,
    page_limit=DEFAULT_PAGE_LIMIT,
):
    _validate_max_markets(max_markets)
    fetcher = fetcher or PublicGammaFetcher()
    log = {"network_call_count": 0, "endpoint_or_url_used": []}
    inspected = []

    try:
        for page_index in range(max_event_pages):
            offset = page_index * page_limit
            url = _event_list_url(offset=offset, limit=page_limit)
            events = _fetch_logged(fetcher, url, log)
            if not isinstance(events, list):
                return _blocked_result(
                    log,
                    "Gamma events endpoint returned a non-list payload.",
                    inspected,
                )
            if not events:
                break
            for event in events:
                inspected.append(
                    {
                        "event_id": _as_text(event.get("id")),
                        "event_slug": _as_text(event.get("slug")),
                        "event_title": _as_text(event.get("title")),
                        "reason": "inspected_for_esports_match_shape",
                    }
                )
                if not _is_esports_event(event):
                    continue
                selected_market = _select_market_from_event(event)
                if not selected_market:
                    inspected[-1]["reason"] = "esports_event_without_suitable_open_market"
                    continue
                detail_url = _event_detail_url(_as_text(event.get("slug")))
                event_detail = _fetch_logged(fetcher, detail_url, log)
                if not isinstance(event_detail, dict):
                    return _blocked_result(
                        log,
                        "Gamma event detail endpoint returned a non-object payload.",
                        inspected,
                    )
                detail_market = _find_market_by_id(event_detail, selected_market.get("id"))
                selected_market = detail_market or selected_market
                return {
                    "status": "selected",
                    "fetch_status": "selected",
                    "event_payload": event_detail,
                    "selected_market": selected_market,
                    "inspected_candidates": inspected,
                    **log,
                }
        return {
            "status": "no_suitable_esports_market_found",
            "fetch_status": "no_suitable_esports_market_found",
            "event_payload": None,
            "selected_market": None,
            "inspected_candidates": inspected,
            **log,
        }
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError) as exc:
        return _blocked_result(log, f"{exc.__class__.__name__}: {exc}", inspected)


def _blocked_result(log, reason, inspected):
    return {
        "status": "blocked_or_unavailable",
        "fetch_status": "blocked_or_unavailable",
        "blocked_reason": reason,
        "event_payload": None,
        "selected_market": None,
        "inspected_candidates": inspected,
        **log,
    }


def _find_market_by_id(event, market_id):
    market_id = _as_text(market_id)
    for market in _safe_list(event.get("markets")):
        if _as_text(market.get("id")) == market_id:
            return market
    return None


def _game_title(event, market):
    text = " ".join(
        [
            _as_text(event.get("title")),
            _as_text(event.get("seriesSlug")),
            _as_text(market.get("question")),
        ]
    ).lower()
    for marker, title in GAME_TITLE_MARKERS:
        if marker in text:
            return title
    for series in _safe_list(event.get("series")):
        title = _as_text(series.get("title"))
        if title:
            return title
    return ""


def _teams_or_players(event, market):
    teams = [
        _as_text(item.get("name"))
        for item in _safe_list(event.get("teams"))
        if isinstance(item, dict) and _as_text(item.get("name"))
    ]
    if teams:
        return teams
    for text in (_as_text(event.get("title")), _as_text(market.get("question"))):
        match = re.search(r":\s*(.+?)\s+vs\.?\s+(.+?)(?:\s+\(|\s+-|$)", text)
        if match:
            return [match.group(1).strip(), match.group(2).strip()]
    return []


def _event_or_tournament(event):
    metadata = event.get("eventMetadata") if isinstance(event.get("eventMetadata"), dict) else {}
    parts = [
        _as_text(metadata.get("league")),
        _as_text(metadata.get("serie")),
        _as_text(metadata.get("tournament")),
    ]
    value = " / ".join(part for part in parts if part)
    if value:
        return value
    return _as_text(event.get("title"))


def _scheduled_time(event, market):
    for key in ("eventStartTime", "gameStartTime", "startTime", "eventDate"):
        value = _as_text(event.get(key))
        if value:
            return value
    for key in ("eventStartTime", "gameStartTime", "endDate", "startDate"):
        value = _as_text(market.get(key))
        if value:
            return value
    return ""


def _missing_fields(candidate):
    required = [
        "market_id",
        "title_or_question",
        "description",
        "rules_text",
        "resolution_source_text",
        "outcomes",
        "event_or_tournament",
        "teams_or_players",
        "game_title",
        "scheduled_time_if_available",
        "source_urls_or_references",
    ]
    missing = []
    for field in required:
        value = candidate.get(field)
        if value in ("", None, []):
            missing.append(field)
    return missing


def build_raw_fetch_artifact(discovery):
    selected_market = discovery.get("selected_market") or {}
    event_payload = discovery.get("event_payload")
    selected_market_id = _as_text(selected_market.get("id")) or None
    selected_slug = _as_text(selected_market.get("slug")) or None
    selected_title = _as_text(selected_market.get("question")) or None
    network_count = discovery.get("network_call_count", 0)
    return {
        "schema_version": "esports_market_raw_fetch_009a.v1",
        "task_id": TASK_ID,
        "fetch_status": discovery.get("fetch_status"),
        "fetched_at_marker": FETCHED_AT_MARKER,
        "network_allowed_explicitly": True,
        "public_readonly_only": True,
        "authenticated_endpoints_used": False,
        "wallet_or_private_key_accessed": False,
        "orders_created": False,
        "endpoint_or_url_used": discovery.get("endpoint_or_url_used", []),
        "network_call_count": network_count,
        "raw_market_payload": _sanitize_raw_market_payload(event_payload),
        "raw_market_payload_redactions": [
            "platform context_description fields removed; not used for source/rules capture"
        ],
        "selected_market_id": selected_market_id,
        "selected_market_slug": selected_slug,
        "selected_market_title_or_question": selected_title,
        "inspected_candidate_count": len(discovery.get("inspected_candidates", [])),
        "inspected_candidates": discovery.get("inspected_candidates", []),
        "blocked_reason": discovery.get("blocked_reason"),
        "no_market_action_guidance": True,
        "safety_summary": _empty_safety_summary(True, network_count),
    }


def _sanitize_raw_market_payload(value):
    if isinstance(value, dict):
        sanitized = {}
        for key, item in value.items():
            if key == "context_description":
                sanitized[key] = "[removed_platform_context_not_used_for_source_rules_capture]"
            else:
                sanitized[key] = _sanitize_raw_market_payload(item)
        return sanitized
    if isinstance(value, list):
        return [_sanitize_raw_market_payload(item) for item in value]
    return value


def build_normalized_candidate(discovery):
    event = discovery.get("event_payload") or {}
    market = discovery.get("selected_market") or {}
    description = _as_text(market.get("description")) or _as_text(event.get("description"))
    resolution_source = _as_text(market.get("resolutionSource")) or _as_text(
        event.get("resolutionSource")
    )
    urls = _extract_urls(resolution_source, description, event.get("description"))
    candidate = {
        "schema_version": "esports_market_normalized_candidate_009a.v1",
        "task_id": TASK_ID,
        "market_id": _as_text(market.get("id")) or None,
        "market_class": "esports",
        "title_or_question": _as_text(market.get("question")) or None,
        "description": description,
        "rules_text": description,
        "resolution_source_text": resolution_source,
        "outcomes": _parse_outcomes(market.get("outcomes")),
        "event_or_tournament": _event_or_tournament(event),
        "teams_or_players": _teams_or_players(event, market),
        "game_title": _game_title(event, market),
        "scheduled_time_if_available": _scheduled_time(event, market),
        "source_urls_or_references": urls,
        "unresolved_source_questions": [],
        "missing_fields": [],
        "operator_review_required": True,
        "planned_capture_status": "draft",
        "auto_promote_to_ready_for_local_review": False,
        "no_market_action_guidance": True,
        "no_trading_authority": True,
    }
    missing = _missing_fields(candidate)
    unresolved = []
    if "resolution_source_text" in missing and "source_urls_or_references" in missing:
        unresolved.append("Operator must identify the official result source before promotion.")
    if "teams_or_players" in missing:
        unresolved.append("Operator must verify teams or players from direct market text.")
    if "scheduled_time_if_available" in missing:
        unresolved.append("Operator must verify match time and timezone.")
    unresolved.append(
        "Operator must verify cancellation, reschedule, forfeit, and walkover handling."
    )
    candidate["missing_fields"] = missing
    candidate["unresolved_source_questions"] = unresolved
    return candidate


def build_empty_normalized_candidate(discovery):
    return {
        "schema_version": "esports_market_normalized_candidate_009a.v1",
        "task_id": TASK_ID,
        "market_id": None,
        "market_class": "esports",
        "title_or_question": None,
        "description": "",
        "rules_text": "",
        "resolution_source_text": "",
        "outcomes": [],
        "event_or_tournament": "",
        "teams_or_players": [],
        "game_title": "",
        "scheduled_time_if_available": "",
        "source_urls_or_references": [],
        "unresolved_source_questions": [
            "No suitable public read-only esports market candidate was selected.",
            discovery.get("blocked_reason", "") or "No matching event met pilot criteria.",
        ],
        "missing_fields": [
            "market_id",
            "title_or_question",
            "description",
            "rules_text",
            "resolution_source_text",
            "outcomes",
            "event_or_tournament",
            "teams_or_players",
            "game_title",
            "scheduled_time_if_available",
            "source_urls_or_references",
        ],
        "operator_review_required": True,
        "planned_capture_status": "draft",
        "auto_promote_to_ready_for_local_review": False,
        "no_market_action_guidance": True,
        "no_trading_authority": True,
    }


def build_source_capture_candidate(normalized, raw_path):
    rules_text = normalized["rules_text"]
    urls = normalized["source_urls_or_references"]
    source_identified = bool(urls or normalized["resolution_source_text"])
    direct_rules = bool(rules_text and "resolve" in rules_text.lower())
    return {
        "contract_version": "esports_source_capture_candidate_009a.v1",
        "task_id": TASK_ID,
        "market_id": normalized["market_id"],
        "market_class": "esports",
        "full_market_resolution_criteria_text": rules_text,
        "full_resolution_rules": rules_text,
        "official_source_references": _dedupe_text_values(
            [normalized["resolution_source_text"], *urls]
        ),
        "official_source_urls_or_rule_references": urls,
        "source_timestamps": {
            "fetched_at_marker": FETCHED_AT_MARKER,
            "scheduled_time_if_available": normalized["scheduled_time_if_available"],
        },
        "source_reliability_review": (
            "candidate_only_operator_must_verify_direct_polymarket_rules_and_official_source"
        ),
        "reviewed_local_evidence_references": [raw_path],
        "non_placeholder_evidence_notes": [
            "Public Gamma metadata captured for operator source/rules review only."
        ],
        "unresolved_source_questions": normalized["unresolved_source_questions"],
        "planned_source_capture_status": "draft",
        "planned_capture_status": "draft",
        "operator_review_required": True,
        "direct_rules_text_captured": direct_rules,
        "official_result_source_identified": source_identified,
        "auto_fill_allowed_only_as_draft": True,
        "no_market_action_guidance": True,
    }


def _dedupe_text_values(values):
    deduped = []
    seen = set()
    for value in values:
        text = _as_text(value)
        if text and text not in seen:
            deduped.append(text)
            seen.add(text)
    return deduped


def build_operator_checklist(normalized):
    items = [
        ("verify_exact_polymarket_rules_text", "Verify exact Polymarket rules text."),
        ("verify_match_tournament_game_identity", "Verify match, tournament, and game identity."),
        ("verify_teams_or_players", "Verify teams or players."),
        ("verify_official_result_source", "Verify official result source."),
        (
            "verify_cancellation_reschedule_forfeit_handling",
            "Verify cancellation, reschedule, forfeit, walkover, and delay handling.",
        ),
        ("verify_timezone_deadline", "Verify timezone and deadline."),
        (
            "verify_source_capture_promotion_readiness",
            "Verify whether source capture can be promoted to ready_for_local_review.",
        ),
        ("no_trading_decision", "No trading decision."),
    ]
    return {
        "contract_version": "esports_operator_review_checklist_009a.v1",
        "task_id": TASK_ID,
        "market_id": normalized["market_id"],
        "market_class": "esports",
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
            for check_id, prompt in items
        ],
        "no_market_action_guidance": True,
        "no_trading_authority": True,
    }


def render_operator_checklist_md(checklist):
    lines = [
        "# PMBOT SOURCE-009A Esports Operator Review Checklist",
        "",
        f"- task_id: {checklist['task_id']}",
        f"- market_id: {checklist['market_id']}",
        f"- market_class: {checklist['market_class']}",
        f"- planned_capture_status: {checklist['planned_capture_status']}",
        "- operator_review_required: true",
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
            "",
        ]
    )
    return "\n".join(lines)


def build_result_doc(discovery, normalized, source_capture_created, files_created):
    selected = discovery.get("selected_market") or {}
    status = (
        "completed_no_suitable_market_found"
        if discovery.get("fetch_status") == "no_suitable_esports_market_found"
        else "completed_local"
        if discovery.get("fetch_status") == "selected"
        else "blocked_or_unavailable"
    )
    return {
        "task_id": TASK_ID,
        "status": status,
        "head_before": HEAD_BEFORE,
        "head_after": "reported_in_final_response_after_commit_or_push",
        "selected_market_id": _as_text(selected.get("id")) or None,
        "selected_market_title_or_question": _as_text(selected.get("question")) or None,
        "fetch_status": discovery.get("fetch_status"),
        "network_allowed_explicitly": True,
        "polymarket_api_calls_performed": discovery.get("network_call_count", 0),
        "authenticated_endpoints_used": False,
        "wallet_or_private_key_accessed": False,
        "orders_created": False,
        "openrouter_calls_performed": 0,
        "trading_runtime_changed": False,
        "dispatcher_changed": False,
        "background_worker_created": False,
        "queue_mutated": False,
        "browser_automation_used": False,
        "canonical_packets_mutated": False,
        "market_action_guidance_generated": False,
        "probability_ev_edge_confidence_generated": False,
        "side_selection_generated": False,
        "source_capture_candidate_created": source_capture_created,
        "operator_review_required": True,
        "future_live_002_allowed": False,
        "tests_passed": [],
        "tests_failed": [],
        "files_created": files_created,
        "files_modified": [],
        "next_recommended_action": (
            "Operator review of the draft esports source/rules capture candidate."
            if normalized["market_id"]
            else "Re-run a public read-only esports discovery task when suitable metadata is available."
        ),
    }


def render_result_md(result, normalized):
    return "\n".join(
        [
            "# PMBOT SOURCE-009A Esports Market Class Pilot Read-Only Discovery",
            "",
            f"- task_id: {result['task_id']}",
            f"- status: {result['status']}",
            f"- fetch_status: {result['fetch_status']}",
            f"- selected_market_id: {result['selected_market_id']}",
            f"- selected_market_title_or_question: {result['selected_market_title_or_question']}",
            f"- polymarket_api_calls_performed: {result['polymarket_api_calls_performed']}",
            "- network_allowed_explicitly: true",
            "- authenticated_endpoints_used: false",
            "- wallet_or_private_key_accessed: false",
            "- orders_created: false",
            "- openrouter_calls_performed: 0",
            "- canonical_packets_mutated: false",
            "- planned_capture_status: draft",
            "- operator_review_required: true",
            "",
            "## Candidate Summary",
            "",
            f"- market_class: {normalized['market_class']}",
            f"- game_title: {normalized['game_title']}",
            f"- event_or_tournament: {normalized['event_or_tournament']}",
            f"- scheduled_time_if_available: {normalized['scheduled_time_if_available']}",
            "- source_capture_candidate_created: "
            + str(result["source_capture_candidate_created"]).lower(),
            "",
            "## Safety Boundary",
            "",
            "- source/rules discovery only",
            "- no market action guidance",
            "- no probability, EV, edge, confidence scoring, or side selection",
            "- no trading runtime, dispatcher, background worker, queue, wallet, order, or browser changes",
            "",
        ]
    )


def write_artifacts(discovery, root=ROOT):
    artifact_root = _resolve(ARTIFACT_DIR, root=root)
    raw_path = artifact_root / RAW_FETCH_JSON
    normalized_path = artifact_root / NORMALIZED_JSON
    source_capture_path = artifact_root / SOURCE_CAPTURE_JSON
    checklist_json_path = artifact_root / CHECKLIST_JSON
    checklist_md_path = artifact_root / CHECKLIST_MD
    result_json_path = _resolve(RESULT_JSON, root=root)
    result_md_path = _resolve(RESULT_MD, root=root)

    raw = build_raw_fetch_artifact(discovery)
    if discovery.get("selected_market"):
        normalized = build_normalized_candidate(discovery)
    else:
        normalized = build_empty_normalized_candidate(discovery)
    source_capture = build_source_capture_candidate(
        normalized,
        f"{ARTIFACT_DIR}/{RAW_FETCH_JSON}",
    )
    checklist = build_operator_checklist(normalized)

    _write_json(raw_path, raw)
    _write_json(normalized_path, normalized)
    _write_json(source_capture_path, source_capture)
    _write_json(checklist_json_path, checklist)
    checklist_md_path.write_text(render_operator_checklist_md(checklist), encoding="utf-8")

    files_created = [
        f"{ARTIFACT_DIR}/{RAW_FETCH_JSON}",
        f"{ARTIFACT_DIR}/{NORMALIZED_JSON}",
        f"{ARTIFACT_DIR}/{SOURCE_CAPTURE_JSON}",
        f"{ARTIFACT_DIR}/{CHECKLIST_JSON}",
        f"{ARTIFACT_DIR}/{CHECKLIST_MD}",
        RESULT_JSON,
        RESULT_MD,
    ]
    result = build_result_doc(
        discovery,
        normalized,
        bool(discovery.get("selected_market")),
        files_created,
    )
    _write_json(result_json_path, result)
    result_md_path.write_text(render_result_md(result, normalized), encoding="utf-8")
    return {
        "raw_fetch": raw,
        "normalized_candidate": normalized,
        "source_capture_candidate": source_capture,
        "operator_checklist": checklist,
        "result": result,
    }


def run_fetch_one(
    write=False,
    max_markets=MAX_MARKETS_HARD_CAP,
    fetcher=None,
    root=ROOT,
    max_event_pages=DEFAULT_MAX_EVENT_PAGES,
):
    discovery = discover_one_esports_market(
        fetcher=fetcher,
        max_markets=max_markets,
        max_event_pages=max_event_pages,
    )
    payload = {
        "schema_version": "esports_market_discovery_run_result.v1",
        "task_id": TASK_ID,
        "status": discovery["status"],
        "fetch_status": discovery["fetch_status"],
        "network_allowed_explicitly": True,
        "public_readonly_only": True,
        "network_call_count": discovery["network_call_count"],
        "polymarket_api_calls_performed": discovery["network_call_count"],
        "endpoint_or_url_used": discovery["endpoint_or_url_used"],
        "selected_market_id": _as_text((discovery.get("selected_market") or {}).get("id"))
        or None,
        "selected_market_title_or_question": _as_text(
            (discovery.get("selected_market") or {}).get("question")
        )
        or None,
        "operator_review_required": True,
        "planned_capture_status": "draft",
        "auto_promote_to_ready_for_local_review": False,
        "no_market_action_guidance": True,
        "no_trading_authority": True,
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
        description="SOURCE-009A public read-only esports market discovery pilot."
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--fetch-one", action="store_true")
    mode.add_argument("--summary-only", action="store_true")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--max-markets", type=int, default=MAX_MARKETS_HARD_CAP)
    parser.add_argument("--max-event-pages", type=int, default=DEFAULT_MAX_EVENT_PAGES)
    return parser.parse_args(argv)


def main(argv):
    args = _parse_args(argv)
    try:
        _validate_max_markets(args.max_markets)
    except ValueError as exc:
        raise SystemExit(str(exc))
    if args.max_event_pages < 1 or args.max_event_pages > DEFAULT_MAX_EVENT_PAGES:
        raise SystemExit(f"--max-event-pages must be between 1 and {DEFAULT_MAX_EVENT_PAGES}")
    if args.summary_only:
        payload = build_summary_only()
    elif args.fetch_one:
        payload = run_fetch_one(
            write=args.write,
            max_markets=args.max_markets,
            max_event_pages=args.max_event_pages,
        )
    else:
        if args.write:
            raise SystemExit("--write is only valid with --fetch-one")
        payload = build_dry_run_status(max_markets=args.max_markets)
    print(json.dumps(payload, indent=2, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(__import__("sys").argv[1:]))
