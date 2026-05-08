import argparse
import json
import re
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


TASK_ID = "PMBOT-PAPERLIVE-004-ESPORTS-CONTROLLED-READONLY-OUTCOME-SOURCE-FETCH-NO-TRADE"
GENERATED_BY = "pm_bot/paper_live/esports_controlled_readonly_outcome_fetch.py"

ROOT = Path(__file__).resolve().parents[2]

MARKET_ID = "1987056"
MARKET_CLASS = "esports"
MARKET_TITLE = (
    "LoL: JD Gaming vs Anyone's Legend (BO5) - Esports World Cup China Qualifier Phase 2"
)
EVENT_SLUG = "lol-jdg-al-2026-05-21"
GAMMA_BASE_URL = "https://gamma-api.polymarket.com"
DEFAULT_TIMEOUT_SECONDS = 10
DEFAULT_MAX_POLYMARKET_API_CALLS = 5
MAX_POLYMARKET_API_CALLS_HARD_CAP = 5
MAX_NON_POLYMARKET_PUBLIC_SOURCE_CALLS = 3
MAX_MARKETS_HARD_CAP = 1
LOCAL_TIMESTAMP = "2026-05-08 Asia/Tbilisi"

PUBLIC_HEADERS = {
    "Accept": "application/json",
    "User-Agent": "PMBOT-PAPERLIVE-004-readonly-outcome-fetch/1.0",
}

DISCOVERY_DIR = "pm_bot/live_readonly/esports_market_discovery"
RAW_FETCH_009A_PATH = f"{DISCOVERY_DIR}/esports_market_raw_fetch_009a.v1.json"
NORMALIZED_CANDIDATE_009A_PATH = (
    f"{DISCOVERY_DIR}/esports_market_normalized_candidate_009a.v1.json"
)
SOURCE_CAPTURE_CANDIDATE_009A_PATH = (
    f"{DISCOVERY_DIR}/esports_source_capture_candidate_009a.v1.json"
)
CAPTURE_009B_PATH = (
    "pm_bot/llm/manual_resolution_source_capture/"
    f"{MARKET_ID}_resolution_source_capture.v1.json"
)
INGEST_RESULT_PATH = "pm_bot/llm/manual_resolution_source_capture_ingest_result.v1.json"
INGEST_OVERLAY_PATH = "pm_bot/llm/manual_resolution_source_capture_ingested_overlay.v1.json"
READINESS_REPORT_PATH = "pm_bot/llm/post_capture_readiness_report.v1.json"
READINESS_GATE_PATH = "pm_bot/llm/post_capture_batch_readiness_gate.v1.json"

PAPERLIVE001_LEDGER_PATH = (
    "pm_bot/paper_live/esports_observation_ledger_first_run_1987056.v1.json"
)
PAPERLIVE001_SOURCE_QUALITY_PATH = (
    "pm_bot/llm/source_quality_pending_observation_1987056_paperlive001.v1.json"
)
PAPERLIVE001_OUTCOME_PLACEHOLDER_PATH = (
    "pm_bot/paper_live/esports_outcome_reconciliation_placeholder_1987056.v1.json"
)

PAPERLIVE002_MONITORING_PLAN_PATH = (
    "pm_bot/paper_live/"
    "esports_outcome_source_monitoring_plan_1987056_paperlive002.v1.json"
)
PAPERLIVE002_CHECKLIST_PATH = (
    "pm_bot/paper_live/"
    "esports_source_monitoring_checklist_1987056_paperlive002.v1.json"
)
PAPERLIVE002_FUTURE_REQUEST_PATH = (
    "pm_bot/paper_live/esports_future_readonly_outcome_check_request_1987056.v1.json"
)
PAPERLIVE002_SOURCE_QUALITY_UPDATE_PLAN_PATH = (
    "pm_bot/llm/source_quality_update_plan_1987056_paperlive002.v1.json"
)

PAPERLIVE003_PROTOCOL_PATH = (
    "pm_bot/paper_live/"
    "esports_readonly_outcome_check_protocol_1987056_paperlive003.v1.json"
)
PAPERLIVE003_RAW_FETCH_CONTRACT_PATH = (
    "pm_bot/paper_live/"
    "esports_outcome_raw_fetch_contract_1987056_paperlive003.v1.json"
)
PAPERLIVE003_NORMALIZED_EVIDENCE_CONTRACT_PATH = (
    "pm_bot/paper_live/"
    "esports_normalized_outcome_evidence_contract_1987056_paperlive003.v1.json"
)
SOURCE_ALIGNMENT_REVIEW_CONTRACT_PATH = (
    "pm_bot/llm/source_alignment_review_contract_1987056_paperlive003.v1.json"
)
PAPERLIVE003_READINESS_GATE_PATH = (
    "pm_bot/paper_live/"
    "esports_readonly_outcome_check_readiness_gate_1987056_paperlive003.v1.json"
)
PAPERLIVE003_WORKBENCH_SURFACE_PATH = (
    "pm_bot/workbench/"
    "esports_readonly_outcome_check_protocol_surface_1987056_paperlive003.v1.json"
)

RAW_FETCH_JSON_PATH = (
    "pm_bot/paper_live/esports_outcome_raw_fetch_1987056_paperlive004.v1.json"
)
RAW_FETCH_MD_PATH = (
    "pm_bot/paper_live/esports_outcome_raw_fetch_1987056_paperlive004.v1.md"
)
NORMALIZED_EVIDENCE_JSON_PATH = (
    "pm_bot/paper_live/"
    "esports_normalized_outcome_evidence_1987056_paperlive004.v1.json"
)
NORMALIZED_EVIDENCE_MD_PATH = (
    "pm_bot/paper_live/"
    "esports_normalized_outcome_evidence_1987056_paperlive004.v1.md"
)
CALL_LEDGER_JSON_PATH = (
    "pm_bot/paper_live/esports_outcome_fetch_call_ledger_1987056_paperlive004.v1.json"
)
CALL_LEDGER_MD_PATH = (
    "pm_bot/paper_live/esports_outcome_fetch_call_ledger_1987056_paperlive004.v1.md"
)
RECONCILIATION_INPUT_JSON_PATH = (
    "pm_bot/paper_live/esports_reconciliation_input_1987056_paperlive004.v1.json"
)
RECONCILIATION_INPUT_MD_PATH = (
    "pm_bot/paper_live/esports_reconciliation_input_1987056_paperlive004.v1.md"
)
WORKBENCH_SURFACE_JSON_PATH = (
    "pm_bot/workbench/esports_outcome_fetch_surface_1987056_paperlive004.v1.json"
)
WORKBENCH_SURFACE_MD_PATH = (
    "pm_bot/workbench/esports_outcome_fetch_surface_1987056_paperlive004.v1.md"
)
RUN_SUMMARY_JSON_PATH = (
    "pm_bot/paper_live/esports_controlled_readonly_outcome_fetch_summary.v1.json"
)
RUN_SUMMARY_MD_PATH = (
    "pm_bot/paper_live/esports_controlled_readonly_outcome_fetch_summary.v1.md"
)
DOC_RESULT_JSON_PATH = "docs/PMBOT_PAPERLIVE_004_RESULT.json"
DOC_RESULT_MD_PATH = (
    "docs/PMBOT_PAPERLIVE_004_ESPORTS_CONTROLLED_READONLY_OUTCOME_SOURCE_FETCH_NO_TRADE.md"
)

INPUT_JSON_PATHS = [
    PAPERLIVE003_PROTOCOL_PATH,
    PAPERLIVE003_RAW_FETCH_CONTRACT_PATH,
    PAPERLIVE003_NORMALIZED_EVIDENCE_CONTRACT_PATH,
    SOURCE_ALIGNMENT_REVIEW_CONTRACT_PATH,
    PAPERLIVE003_READINESS_GATE_PATH,
    PAPERLIVE003_WORKBENCH_SURFACE_PATH,
    PAPERLIVE002_MONITORING_PLAN_PATH,
    PAPERLIVE002_CHECKLIST_PATH,
    PAPERLIVE002_FUTURE_REQUEST_PATH,
    PAPERLIVE002_SOURCE_QUALITY_UPDATE_PLAN_PATH,
    PAPERLIVE001_LEDGER_PATH,
    PAPERLIVE001_SOURCE_QUALITY_PATH,
    PAPERLIVE001_OUTCOME_PLACEHOLDER_PATH,
    RAW_FETCH_009A_PATH,
    NORMALIZED_CANDIDATE_009A_PATH,
    SOURCE_CAPTURE_CANDIDATE_009A_PATH,
    CAPTURE_009B_PATH,
    INGEST_RESULT_PATH,
    INGEST_OVERLAY_PATH,
    READINESS_REPORT_PATH,
    READINESS_GATE_PATH,
]

JSON_OUTPUT_PATHS = [
    RAW_FETCH_JSON_PATH,
    NORMALIZED_EVIDENCE_JSON_PATH,
    CALL_LEDGER_JSON_PATH,
    RECONCILIATION_INPUT_JSON_PATH,
    WORKBENCH_SURFACE_JSON_PATH,
    RUN_SUMMARY_JSON_PATH,
    DOC_RESULT_JSON_PATH,
]

MARKDOWN_OUTPUT_PATHS = [
    RAW_FETCH_MD_PATH,
    NORMALIZED_EVIDENCE_MD_PATH,
    CALL_LEDGER_MD_PATH,
    RECONCILIATION_INPUT_MD_PATH,
    WORKBENCH_SURFACE_MD_PATH,
    RUN_SUMMARY_MD_PATH,
    DOC_RESULT_MD_PATH,
]

OUTPUT_PATHS = [
    RAW_FETCH_JSON_PATH,
    RAW_FETCH_MD_PATH,
    NORMALIZED_EVIDENCE_JSON_PATH,
    NORMALIZED_EVIDENCE_MD_PATH,
    CALL_LEDGER_JSON_PATH,
    CALL_LEDGER_MD_PATH,
    RECONCILIATION_INPUT_JSON_PATH,
    RECONCILIATION_INPUT_MD_PATH,
    WORKBENCH_SURFACE_JSON_PATH,
    WORKBENCH_SURFACE_MD_PATH,
    RUN_SUMMARY_JSON_PATH,
    RUN_SUMMARY_MD_PATH,
    DOC_RESULT_JSON_PATH,
    DOC_RESULT_MD_PATH,
]

def _base_safety_summary(network_count=0, polymarket_count=0, non_polymarket_count=0):
    return {
        "no_market_action_guidance": True,
        "operator_review_only": True,
        "analysis_only": True,
        "public_readonly_only": True,
        "passive_context_only": True,
        "manual_review_only": True,
        "no_trading_authority": True,
        "no_execution_authority": True,
        "no_queue_authority": True,
        "no_runtime_authority": True,
        "no_wallet_or_order_authority": True,
        "no_dispatcher_authority": True,
        "no_browser_automation": True,
        "no_probability_ev_edge_confidence_side_selection": True,
        "openrouter_calls_performed": 0,
        "polymarket_api_calls_performed": polymarket_count,
        "non_polymarket_public_source_calls_performed": non_polymarket_count,
        "external_network_calls_performed": network_count,
        "network_calls_performed": network_count,
        "authenticated_endpoints_used": False,
        "auth_headers_used": False,
        "api_key_accessed": False,
        "api_key_value_printed": False,
        "api_key_value_written": False,
        "api_key_leaked": False,
        "wallet_or_private_key_accessed": False,
        "orders_created": False,
        "orders_created_count": 0,
        "simulated_trade_created": False,
        "selected_side": None,
        "stake_amount": None,
        "position_sizing_created": False,
        "queue_items_created": 0,
        "queue_state_mutated": False,
        "runtime_wiring_added": False,
        "dispatcher_changed": False,
        "background_workers_added": False,
        "browser_automation_used": False,
        "market_decisions_made": False,
        "outcome_checked": network_count > 0,
        "outcome_known": False,
        "source_alignment_review_performed": False,
        "source_scoring_performed": False,
        "source_ranking_updated": False,
        "profit_or_pnl_recorded": False,
        "canonical_packets_mutated": False,
        "market_action_guidance_generated": False,
        "probability_ev_edge_confidence_generated": False,
        "side_selection_generated": False,
    }


def _parse_args(argv):
    parser = argparse.ArgumentParser(
        description="PAPERLIVE-004 controlled public read-only esports outcome/source fetch."
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--fetch", action="store_true")
    mode.add_argument("--summary-only", action="store_true")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--market-id", default=MARKET_ID)
    parser.add_argument("--max-calls", type=int, default=DEFAULT_MAX_POLYMARKET_API_CALLS)
    parser.add_argument("--max-markets", type=int, default=MAX_MARKETS_HARD_CAP)
    return parser.parse_args(argv)


def _resolve(path, root=ROOT):
    value = Path(path)
    return value if value.is_absolute() else Path(root) / value


def _load_json(path, root=ROOT):
    with _resolve(path, root=root).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _load_optional_json(path, root=ROOT):
    resolved = _resolve(path, root=root)
    if not resolved.exists():
        return None
    return _load_json(path, root=root)


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


def _as_text(value):
    if value is None:
        return ""
    return str(value).strip()


def _safe_dict(value):
    return value if isinstance(value, dict) else {}


def _safe_list(value):
    return value if isinstance(value, list) else []


def _dedupe(values):
    output = []
    seen = set()
    for value in values:
        text = _as_text(value)
        if text and text not in seen:
            output.append(text)
            seen.add(text)
    return output


def _parse_json_list(value):
    if isinstance(value, list):
        return value
    if isinstance(value, str) and value.strip():
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return []
        if isinstance(parsed, list):
            return parsed
    return []


def _extract_urls(*values):
    urls = []
    for value in values:
        text = _as_text(value)
        for match in re.findall(r"https?://[^\s)]+", text):
            urls.append(match.rstrip(".,"))
    return _dedupe(urls)


def _validate_market_id(market_id):
    if _as_text(market_id) != MARKET_ID:
        raise ValueError("PAPERLIVE-004 fetch is allowlisted only for market_id 1987056")


def _validate_max_markets(max_markets):
    if int(max_markets) != MAX_MARKETS_HARD_CAP:
        raise ValueError("PAPERLIVE-004 max target markets hard cap is exactly 1")


def _validate_max_calls(max_calls):
    if int(max_calls) < 0:
        raise ValueError("--max-calls must be non-negative")
    if int(max_calls) > MAX_POLYMARKET_API_CALLS_HARD_CAP:
        raise ValueError("--max-calls cannot exceed the PAPERLIVE-004 hard cap of 5")


def _event_detail_url():
    quoted_slug = urllib.parse.quote(EVENT_SLUG, safe="")
    return f"{GAMMA_BASE_URL}/events/slug/{quoted_slug}"


def _market_detail_url(market_id=MARKET_ID):
    quoted_market_id = urllib.parse.quote(_as_text(market_id), safe="")
    return f"{GAMMA_BASE_URL}/markets/{quoted_market_id}"


def _fetched_at_marker():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class FetchResponse:
    def __init__(self, status, http_status, text, payload, error=None):
        self.status = status
        self.http_status = http_status
        self.text = text
        self.payload = payload
        self.error = error


class PublicReadOnlyHttpFetcher:
    def fetch(self, url, timeout_seconds=DEFAULT_TIMEOUT_SECONDS):
        request = urllib.request.Request(url, headers=PUBLIC_HEADERS, method="GET")
        try:
            with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
                raw = response.read()
                text = raw.decode("utf-8", errors="replace")
                return FetchResponse(
                    "success",
                    getattr(response, "status", None),
                    text,
                    _parse_payload(text),
                )
        except urllib.error.HTTPError as exc:
            raw = exc.read()
            text = raw.decode("utf-8", errors="replace")
            return FetchResponse("failed", exc.code, text, _parse_payload(text), str(exc))
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            return FetchResponse("failed", None, "", None, f"{exc.__class__.__name__}: {exc}")


def _parse_payload(text):
    if not text:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


class CallLedger:
    def __init__(self, max_polymarket_api_calls, root=ROOT):
        _validate_max_calls(max_polymarket_api_calls)
        self.max_polymarket_api_calls = int(max_polymarket_api_calls)
        self.root = root
        self.calls = []
        self.total_network_call_count = 0
        self.polymarket_api_call_count = 0
        self.non_polymarket_public_source_call_count = 0
        self.cap_exceeded = False
        self.raw_payloads = []
        self.endpoint_or_url_used = []

    def fetch_polymarket_json(self, fetcher, url, source_category):
        if self.polymarket_api_call_count >= self.max_polymarket_api_calls:
            self.cap_exceeded = True
            self.calls.append(
                self._call_record(
                    source_category=source_category,
                    endpoint_or_url=url,
                    status="skipped",
                    http_status=None,
                    bytes_or_chars_recorded=0,
                    raw_preserved_path=None,
                )
            )
            return None
        response = fetcher.fetch(url, timeout_seconds=DEFAULT_TIMEOUT_SECONDS)
        self.total_network_call_count += 1
        self.polymarket_api_call_count += 1
        self.endpoint_or_url_used.append(url)
        text_length = len(response.text or "")
        raw_entry = {
            "source_category": source_category,
            "endpoint_or_url": url,
            "status": response.status,
            "http_status_if_available": response.http_status,
            "payload": response.payload,
            "raw_text_excerpt": _short_excerpt(response.text),
            "error": response.error,
        }
        self.raw_payloads.append(raw_entry)
        self.calls.append(
            self._call_record(
                source_category=source_category,
                endpoint_or_url=url,
                status=response.status,
                http_status=response.http_status,
                bytes_or_chars_recorded=text_length,
                raw_preserved_path=RAW_FETCH_JSON_PATH,
            )
        )
        return response

    def add_skipped_public_source(self, url, source_category, reason):
        self.calls.append(
            {
                "call_index": len(self.calls) + 1,
                "source_category": source_category,
                "endpoint_or_url": url,
                "method": "GET",
                "auth_used": False,
                "timeout_seconds": DEFAULT_TIMEOUT_SECONDS,
                "status": "skipped",
                "http_status_if_available": None,
                "bytes_or_chars_recorded": 0,
                "raw_preserved_path": None,
                "skip_reason": reason,
            }
        )

    def _call_record(
        self,
        source_category,
        endpoint_or_url,
        status,
        http_status,
        bytes_or_chars_recorded,
        raw_preserved_path,
    ):
        return {
            "call_index": len(self.calls) + 1,
            "source_category": source_category,
            "endpoint_or_url": endpoint_or_url,
            "method": "GET",
            "auth_used": False,
            "timeout_seconds": DEFAULT_TIMEOUT_SECONDS,
            "status": status,
            "http_status_if_available": http_status,
            "bytes_or_chars_recorded": bytes_or_chars_recorded,
            "raw_preserved_path": raw_preserved_path,
        }


def _short_excerpt(text, limit=600):
    value = _as_text(text).replace("\r", " ").replace("\n", " ")
    if len(value) <= limit:
        return value
    return value[:limit] + "...[truncated]"


def _pipeline_snapshot(root=ROOT):
    ingest = _load_optional_json(INGEST_RESULT_PATH, root=root) or {}
    readiness = _load_optional_json(READINESS_REPORT_PATH, root=root) or {}
    gate = _load_optional_json(READINESS_GATE_PATH, root=root) or {}
    return {
        "real_ingested_template_count": (
            readiness.get("real_ingested_template_count")
            if readiness.get("real_ingested_template_count") is not None
            else ingest.get("real_ingested_template_count")
        ),
        "draft_ingested_template_count": readiness.get("draft_ingested_template_count"),
        "ready_ingested_template_count": readiness.get("ready_ingested_template_count"),
        "future_live_002_allowed": gate.get("future_live_002_allowed"),
        "canonical_packets_mutated": bool(
            readiness.get("canonical_packets_mutated")
            or gate.get("canonical_packets_mutated")
            or ingest.get("canonical_packets_mutated")
        ),
    }


def _input_snapshot(root=ROOT):
    return {
        "normalized_candidate": _load_optional_json(
            NORMALIZED_CANDIDATE_009A_PATH, root=root
        )
        or {},
        "source_capture_candidate": _load_optional_json(
            SOURCE_CAPTURE_CANDIDATE_009A_PATH, root=root
        )
        or {},
        "manual_capture": _load_optional_json(CAPTURE_009B_PATH, root=root) or {},
        "monitoring_plan": _load_optional_json(PAPERLIVE002_MONITORING_PLAN_PATH, root=root)
        or {},
        "paperlive003_protocol": _load_optional_json(PAPERLIVE003_PROTOCOL_PATH, root=root)
        or {},
    }


def _find_market_payload(payload, market_id=MARKET_ID):
    wanted = _as_text(market_id)
    if isinstance(payload, dict):
        if _as_text(payload.get("id")) == wanted and (
            "question" in payload or "conditionId" in payload
        ):
            return payload
        for market in _safe_list(payload.get("markets")):
            if isinstance(market, dict) and _as_text(market.get("id")) == wanted:
                return market
    if isinstance(payload, list):
        for item in payload:
            found = _find_market_payload(item, market_id=market_id)
            if found:
                return found
    return None


def _event_payload_from_raw(raw_payloads):
    for entry in raw_payloads:
        payload = entry.get("payload")
        if isinstance(payload, dict) and payload.get("markets"):
            return payload
    return {}


def _market_status(market):
    if not market:
        return {
            "outcome_resolution_status": "unknown",
            "resolution_status_from_payload": None,
            "outcome_status_from_payload": None,
            "outcome_known": False,
            "final_result_text": None,
        }
    resolution_candidates = [
        market.get("resolutionStatus"),
        market.get("resolution_status"),
        market.get("umaResolutionStatus"),
        market.get("status"),
    ]
    uma_statuses = _parse_json_list(market.get("umaResolutionStatuses"))
    if uma_statuses:
        resolution_candidates.extend(_as_text(item) for item in uma_statuses)
    resolution_status = next((_as_text(item) for item in resolution_candidates if _as_text(item)), None)

    outcome_candidates = [
        market.get("winningOutcome"),
        market.get("winning_outcome"),
        market.get("winner"),
        market.get("resolvedOutcome"),
        market.get("resolved_outcome"),
        market.get("finalOutcome"),
        market.get("result"),
    ]
    final_result = next((_as_text(item) for item in outcome_candidates if _as_text(item)), None)
    outcome_known = bool(final_result)

    closed = market.get("closed") is True
    active = market.get("active") is True
    archived = market.get("archived") is True
    lowered_status = _as_text(resolution_status).lower()
    if outcome_known or lowered_status in {"resolved", "final", "settled"}:
        normalized_resolution_status = "resolved"
    elif closed or archived or lowered_status in {"unresolved", "pending", "proposed"}:
        normalized_resolution_status = "unresolved"
    elif active:
        normalized_resolution_status = "unresolved"
    else:
        normalized_resolution_status = "unknown"

    return {
        "outcome_resolution_status": normalized_resolution_status,
        "resolution_status_from_payload": resolution_status,
        "outcome_status_from_payload": final_result,
        "outcome_known": outcome_known,
        "final_result_text": final_result,
    }


def _official_source_references(market, event, inputs):
    description = _as_text(market.get("description")) or _as_text(event.get("description"))
    references = _extract_urls(
        market.get("resolutionSource"),
        event.get("resolutionSource"),
        description,
        inputs["normalized_candidate"].get("resolution_source_text"),
        " ".join(_safe_list(inputs["manual_capture"].get("official_source_references"))),
        " ".join(
            _safe_list(inputs["manual_capture"].get("official_source_urls_or_rule_references"))
        ),
    )
    local_refs = [
        NORMALIZED_CANDIDATE_009A_PATH,
        SOURCE_CAPTURE_CANDIDATE_009A_PATH,
        CAPTURE_009B_PATH,
    ]
    return {
        "public_urls": references,
        "local_artifact_references": local_refs,
    }


def _teams_or_players(market, event, inputs):
    normalized = inputs["normalized_candidate"]
    teams = normalized.get("teams_or_players")
    if isinstance(teams, list) and teams:
        return teams
    for text in (_as_text(market.get("question")), _as_text(event.get("title"))):
        match = re.search(r":\s*(.+?)\s+vs\.?\s+(.+?)(?:\s+\(|\s+-|$)", text)
        if match:
            return [match.group(1).strip(), match.group(2).strip()]
    return []


def _identity_flags(market, event, inputs):
    title = _as_text(market.get("question")) or _as_text(event.get("title"))
    teams = _teams_or_players(market, event, inputs)
    tournament_text = " ".join(
        [
            title,
            _as_text(inputs["normalized_candidate"].get("event_or_tournament")),
            _as_text(event.get("title")),
        ]
    ).lower()
    return {
        "match_identity_confirmed": bool(_as_text(market.get("id")) == MARKET_ID and title),
        "teams_or_players_confirmed": bool(teams),
        "tournament_confirmed": "esports world cup" in tournament_text
        and "china qualifier" in tournament_text,
        "match_format_confirmed": "bo5" in title.lower(),
    }


def _contradiction_flags(market, event):
    flags = []
    if market and _as_text(market.get("id")) != MARKET_ID:
        flags.append("market_id_mismatch")
    if event and _as_text(event.get("slug")) not in {"", EVENT_SLUG}:
        flags.append("event_slug_mismatch")
    return flags


def perform_controlled_fetch(
    market_id=MARKET_ID,
    max_calls=DEFAULT_MAX_POLYMARKET_API_CALLS,
    max_markets=MAX_MARKETS_HARD_CAP,
    fetcher=None,
    root=ROOT,
):
    _validate_market_id(market_id)
    _validate_max_markets(max_markets)
    _validate_max_calls(max_calls)

    fetcher = fetcher or PublicReadOnlyHttpFetcher()
    ledger = CallLedger(max_polymarket_api_calls=max_calls, root=root)
    inputs = _input_snapshot(root=root)

    event_response = ledger.fetch_polymarket_json(
        fetcher,
        _event_detail_url(),
        "polymarket_gamma_event_market_metadata",
    )
    market_payload = None
    event_payload = {}
    if event_response and event_response.status == "success":
        event_payload = _safe_dict(event_response.payload)
        market_payload = _find_market_payload(event_response.payload, market_id=market_id)

    if market_payload is None and not ledger.cap_exceeded:
        market_response = ledger.fetch_polymarket_json(
            fetcher,
            _market_detail_url(market_id),
            "polymarket_gamma_market_metadata_fallback",
        )
        if market_response and market_response.status == "success":
            market_payload = _find_market_payload(market_response.payload, market_id=market_id)

    if not event_payload:
        event_payload = _event_payload_from_raw(ledger.raw_payloads)

    official_refs = _official_source_references(market_payload or {}, event_payload, inputs)
    if official_refs["public_urls"]:
        ledger.add_skipped_public_source(
            official_refs["public_urls"][0],
            "official_tournament_source_reference",
            "official source reference prepared only; metadata did not require extra public source fetch",
        )

    status = _market_status(market_payload or {})
    if ledger.cap_exceeded:
        fetch_status = "blocked_or_unavailable"
    elif ledger.total_network_call_count == 0:
        fetch_status = "failed_safe"
    elif not market_payload:
        fetch_status = "blocked_or_unavailable"
    elif status["outcome_known"]:
        fetch_status = "completed"
    else:
        fetch_status = "completed_no_outcome_available"

    raw_fetch = build_raw_fetch_artifact(
        fetch_status=fetch_status,
        ledger=ledger,
        market_payload=market_payload or {},
        status=status,
        official_refs=official_refs,
    )
    normalized = build_normalized_evidence_artifact(
        fetch_status=fetch_status,
        ledger=ledger,
        market_payload=market_payload or {},
        event_payload=event_payload,
        status=status,
        official_refs=official_refs,
        inputs=inputs,
    )
    call_ledger = build_call_ledger_artifact(ledger)
    reconciliation = build_reconciliation_input_artifact(normalized)
    workbench = build_workbench_surface_artifact(normalized)
    summary = build_run_summary_artifact(fetch_status, ledger, normalized, root=root)
    docs_result = build_docs_result_artifact(fetch_status, ledger, normalized, root=root)
    return {
        "raw_fetch": raw_fetch,
        "normalized_evidence": normalized,
        "call_ledger": call_ledger,
        "reconciliation_input": reconciliation,
        "workbench_surface": workbench,
        "run_summary": summary,
        "docs_result": docs_result,
    }


def build_raw_fetch_artifact(fetch_status, ledger, market_payload, status, official_refs):
    safety = _base_safety_summary(
        network_count=ledger.total_network_call_count,
        polymarket_count=ledger.polymarket_api_call_count,
        non_polymarket_count=ledger.non_polymarket_public_source_call_count,
    )
    safety["outcome_known"] = status["outcome_known"]
    return {
        "schema_version": "paper_live_esports_outcome_raw_fetch.v1",
        "task_id": TASK_ID,
        "generated_by": GENERATED_BY,
        "generated_at_marker": LOCAL_TIMESTAMP,
        "fetched_at_marker": _fetched_at_marker(),
        "market_id": MARKET_ID,
        "market_class": MARKET_CLASS,
        "fetch_status": fetch_status,
        "network_allowed_explicitly": True,
        "public_readonly_only": True,
        "fetch_performed": ledger.total_network_call_count > 0,
        "network_call_count": ledger.total_network_call_count,
        "polymarket_api_calls_performed": ledger.polymarket_api_call_count,
        "non_polymarket_public_source_calls_performed": (
            ledger.non_polymarket_public_source_call_count
        ),
        "authenticated_endpoints_used": False,
        "auth_headers_used": False,
        "wallet_or_private_key_accessed": False,
        "orders_created": False,
        "browser_automation_used": False,
        "endpoint_or_url_used": list(ledger.endpoint_or_url_used),
        "official_source_references_prepared": official_refs,
        "raw_payloads": ledger.raw_payloads,
        "raw_market_payload": market_payload or None,
        "raw_text_excerpt": _short_excerpt(
            " ".join(_as_text(entry.get("raw_text_excerpt")) for entry in ledger.raw_payloads)
        ),
        "outcome_status_from_payload": status["outcome_status_from_payload"],
        "resolution_status_from_payload": status["resolution_status_from_payload"],
        "outcome_known_from_raw_payload": status["outcome_known"],
        "operator_review_required": True,
        "no_market_action_guidance": True,
        "no_trading_authority": True,
        "safety_summary": safety,
    }


def build_normalized_evidence_artifact(
    fetch_status,
    ledger,
    market_payload,
    event_payload,
    status,
    official_refs,
    inputs,
):
    identity = _identity_flags(market_payload, event_payload, inputs) if market_payload else {}
    outcome_known = status["outcome_known"]
    if outcome_known:
        evidence_status = "evidence_available"
        result_source_type = "polymarket_metadata"
        result_source_name = "Polymarket Gamma public metadata"
        result_source_reference = list(ledger.endpoint_or_url_used)
    elif market_payload:
        evidence_status = "evidence_unavailable"
        result_source_type = "polymarket_metadata"
        result_source_name = "Polymarket Gamma public metadata"
        result_source_reference = {
            "metadata_urls": list(ledger.endpoint_or_url_used),
            "official_source_references_prepared": official_refs,
        }
    else:
        evidence_status = "source_unavailable"
        result_source_type = "unavailable"
        result_source_name = None
        result_source_reference = None

    unresolved_questions = []
    if not outcome_known:
        unresolved_questions.append(
            "No final result or explicit resolved outcome was available in fetched public metadata."
        )
    if official_refs["public_urls"]:
        unresolved_questions.append(
            "Official result source reference is prepared for later operator review."
        )
    if fetch_status in {"blocked_or_unavailable", "failed_safe"}:
        unresolved_questions.append("Public metadata fetch did not produce usable market payload.")

    return {
        "schema_version": "paper_live_esports_normalized_outcome_evidence.v1",
        "task_id": TASK_ID,
        "generated_by": GENERATED_BY,
        "generated_at_marker": LOCAL_TIMESTAMP,
        "market_id": MARKET_ID,
        "market_class": MARKET_CLASS,
        "outcome_evidence_status": evidence_status,
        "outcome_known": outcome_known,
        "outcome_resolution_status": status["outcome_resolution_status"],
        "result_source_type": result_source_type,
        "result_source_name": result_source_name,
        "result_source_reference": result_source_reference,
        "match_identity_confirmed": identity.get("match_identity_confirmed"),
        "teams_or_players_confirmed": identity.get("teams_or_players_confirmed"),
        "tournament_confirmed": identity.get("tournament_confirmed"),
        "match_format_confirmed": identity.get("match_format_confirmed"),
        "final_result_text": status["final_result_text"],
        "result_timestamp": None,
        "cancellation_or_forfeit_detected": None,
        "reschedule_detected": None,
        "contradiction_flags": _contradiction_flags(market_payload, event_payload),
        "unresolved_questions": unresolved_questions,
        "operator_review_required": True,
        "source_alignment_review_required": outcome_known,
        "source_quality_update_allowed_now": False,
        "source_scoring_performed": False,
        "source_ranking_updated": False,
        "trading_profit_used_for_scoring": False,
        "source_alignment_review_performed": False,
        "no_market_action_guidance": True,
        "no_trading_authority": True,
        "simulated_trade_created": False,
        "selected_side": None,
        "stake_amount": None,
        "orders_created": False,
        "wallet_or_private_key_accessed": False,
    }


def build_call_ledger_artifact(ledger):
    safety = _base_safety_summary(
        network_count=ledger.total_network_call_count,
        polymarket_count=ledger.polymarket_api_call_count,
        non_polymarket_count=ledger.non_polymarket_public_source_call_count,
    )
    return {
        "schema_version": "paper_live_esports_outcome_fetch_call_ledger.v1",
        "task_id": TASK_ID,
        "generated_by": GENERATED_BY,
        "generated_at_marker": LOCAL_TIMESTAMP,
        "market_id": MARKET_ID,
        "allowed_market_id": MARKET_ID,
        "network_allowed_explicitly": True,
        "total_network_call_count": ledger.total_network_call_count,
        "polymarket_api_call_count": ledger.polymarket_api_call_count,
        "non_polymarket_public_source_call_count": (
            ledger.non_polymarket_public_source_call_count
        ),
        "max_polymarket_api_calls": ledger.max_polymarket_api_calls,
        "max_non_polymarket_public_source_calls": MAX_NON_POLYMARKET_PUBLIC_SOURCE_CALLS,
        "calls": list(ledger.calls),
        "cap_exceeded": ledger.cap_exceeded,
        "safety_summary": safety,
    }


def build_reconciliation_input_artifact(normalized):
    outcome_known = normalized["outcome_known"]
    blockers = []
    if not outcome_known:
        blockers.append("outcome evidence is unavailable")
    if normalized["outcome_evidence_status"] != "evidence_available":
        blockers.append("normalized outcome evidence is not evidence_available")
    return {
        "schema_version": "paper_live_esports_reconciliation_input.v1",
        "task_id": TASK_ID,
        "generated_by": GENERATED_BY,
        "generated_at_marker": LOCAL_TIMESTAMP,
        "market_id": MARKET_ID,
        "market_class": MARKET_CLASS,
        "raw_fetch_artifact_path": RAW_FETCH_JSON_PATH,
        "normalized_outcome_evidence_path": NORMALIZED_EVIDENCE_JSON_PATH,
        "source_alignment_review_contract_path": SOURCE_ALIGNMENT_REVIEW_CONTRACT_PATH,
        "source_quality_update_plan_path": PAPERLIVE002_SOURCE_QUALITY_UPDATE_PLAN_PATH,
        "reconciliation_ready": bool(outcome_known and not blockers),
        "outcome_known": outcome_known,
        "source_alignment_review_performed": False,
        "source_quality_update_performed": False,
        "operator_review_required": True,
        "blockers": blockers,
        "no_market_action_guidance": True,
        "no_trading_authority": True,
    }


def build_workbench_surface_artifact(normalized):
    if normalized["outcome_known"]:
        next_actions = [
            "Review normalized outcome evidence.",
            "Run PAPERLIVE-005 reconciliation only after operator approval.",
        ]
    else:
        next_actions = [
            "Review fetched metadata and prepared source references.",
            "Repeat controlled read-only evidence collection later if the market remains unresolved.",
        ]
    return {
        "schema_version": "paper_live_esports_outcome_fetch_surface.v1",
        "task_id": TASK_ID,
        "generated_by": GENERATED_BY,
        "generated_at_marker": LOCAL_TIMESTAMP,
        "market_id": MARKET_ID,
        "market_class": MARKET_CLASS,
        "raw_fetch_available": True,
        "normalized_outcome_evidence_available": True,
        "call_ledger_available": True,
        "reconciliation_input_available": True,
        "outcome_known": normalized["outcome_known"],
        "outcome_resolution_status": normalized["outcome_resolution_status"],
        "operator_review_required": True,
        "simulated_trade_created": False,
        "selected_side": None,
        "stake_amount": None,
        "next_operator_actions": next_actions,
        "queue_mutated": False,
        "runtime_wiring_changed": False,
        "dispatcher_changed": False,
        "background_worker_created": False,
        "browser_automation_used": False,
        "canonical_packets_mutated": False,
        "no_queue_authority": True,
        "no_runtime_authority": True,
        "no_dispatcher_authority": True,
        "no_market_action_guidance": True,
        "no_trading_authority": True,
    }


def build_run_summary_artifact(fetch_status, ledger, normalized, root=ROOT):
    pipeline = _pipeline_snapshot(root=root)
    safety = _base_safety_summary(
        network_count=ledger.total_network_call_count,
        polymarket_count=ledger.polymarket_api_call_count,
        non_polymarket_count=ledger.non_polymarket_public_source_call_count,
    )
    safety["outcome_known"] = normalized["outcome_known"]
    return {
        "schema_version": "paper_live_esports_controlled_readonly_outcome_fetch_summary.v1",
        "task_id": TASK_ID,
        "generated_by": GENERATED_BY,
        "generated_at_marker": LOCAL_TIMESTAMP,
        "status": "completed_local"
        if fetch_status in {"completed", "completed_no_outcome_available"}
        else fetch_status,
        "market_id": MARKET_ID,
        "market_class": MARKET_CLASS,
        "fetch_performed": ledger.total_network_call_count > 0,
        "fetch_status": fetch_status,
        "network_allowed_explicitly": True,
        "total_network_call_count": ledger.total_network_call_count,
        "polymarket_api_calls_performed": ledger.polymarket_api_call_count,
        "non_polymarket_public_source_calls_performed": (
            ledger.non_polymarket_public_source_call_count
        ),
        "outcome_known": normalized["outcome_known"],
        "outcome_checked": ledger.total_network_call_count > 0,
        "outcome_resolution_status": normalized["outcome_resolution_status"],
        "source_alignment_review_performed": False,
        "source_scoring_performed": False,
        "source_ranking_updated": False,
        "simulated_trades_created_count": 0,
        "orders_created_count": 0,
        "selected_side_count": 0,
        "stake_amount_count": 0,
        "operator_review_required": True,
        "no_market_action_guidance": True,
        "safety_summary": safety,
        "next_recommended_action": (
            "PMBOT-PAPERLIVE-005-ESPORTS-OUTCOME-SOURCE-RECONCILIATION-NO-TRADE"
        ),
        "real_ingested_template_count_preserved_or_after": pipeline.get(
            "real_ingested_template_count"
        ),
        "draft_ingested_template_count_preserved_or_after": pipeline.get(
            "draft_ingested_template_count"
        ),
        "ready_ingested_template_count_after": pipeline.get("ready_ingested_template_count"),
        "future_live_002_allowed": pipeline.get("future_live_002_allowed"),
    }


def build_docs_result_artifact(fetch_status, ledger, normalized, root=ROOT):
    pipeline = _pipeline_snapshot(root=root)
    return {
        "task_id": TASK_ID,
        "status": "completed_local"
        if fetch_status in {"completed", "completed_no_outcome_available"}
        else fetch_status,
        "head_before": "79488d75f02d312ed39801e27f635e4489def66d",
        "head_after": "reported_in_final_response_after_commit",
        "pushed": False,
        "network_allowed_explicitly": True,
        "openrouter_calls_performed": 0,
        "polymarket_api_calls_performed": ledger.polymarket_api_call_count,
        "non_polymarket_public_source_calls_performed": (
            ledger.non_polymarket_public_source_call_count
        ),
        "external_network_calls_performed": "public_readonly_only",
        "authenticated_endpoints_used": False,
        "auth_headers_used": False,
        "wallet_or_private_key_accessed": False,
        "orders_created": False,
        "simulated_trade_created": False,
        "selected_side": None,
        "stake_amount": None,
        "position_sizing_created": False,
        "outcome_checked": ledger.total_network_call_count > 0,
        "outcome_known": normalized["outcome_known"],
        "outcome_resolution_status": normalized["outcome_resolution_status"],
        "source_alignment_review_performed": False,
        "source_scoring_performed": False,
        "source_ranking_updated": False,
        "profit_or_pnl_recorded": False,
        "trading_runtime_changed": False,
        "dispatcher_changed": False,
        "background_worker_created": False,
        "queue_mutated": False,
        "browser_automation_used": False,
        "canonical_packets_mutated": False,
        "no_queue_authority": True,
        "no_runtime_authority": True,
        "no_dispatcher_authority": True,
        "market_action_guidance_generated": False,
        "probability_ev_edge_confidence_generated": False,
        "side_selection_generated": False,
        "market_id": MARKET_ID,
        "market_class": MARKET_CLASS,
        "raw_fetch_artifact_created": True,
        "normalized_outcome_evidence_created": True,
        "call_ledger_created": True,
        "reconciliation_input_created": True,
        "passive_workbench_surface_created": True,
        "real_ingested_template_count_preserved_or_after": pipeline.get(
            "real_ingested_template_count"
        ),
        "draft_ingested_template_count_preserved_or_after": pipeline.get(
            "draft_ingested_template_count"
        ),
        "ready_ingested_template_count_after": pipeline.get("ready_ingested_template_count"),
        "future_live_002_allowed": pipeline.get("future_live_002_allowed"),
        "tests_passed": [],
        "tests_failed": [],
        "files_created": OUTPUT_PATHS,
        "files_modified": [],
        "next_recommended_action": (
            "PMBOT-PAPERLIVE-005-ESPORTS-OUTCOME-SOURCE-RECONCILIATION-NO-TRADE"
        ),
    }


def render_raw_fetch_markdown(raw):
    return "\n".join(
        [
            "# PMBOT PAPERLIVE-004 Raw Outcome Fetch",
            "",
            f"- task_id: {raw['task_id']}",
            f"- market_id: {raw['market_id']}",
            f"- market_class: {raw['market_class']}",
            f"- fetch_status: {raw['fetch_status']}",
            f"- fetch_performed: {str(raw['fetch_performed']).lower()}",
            f"- network_call_count: {raw['network_call_count']}",
            (
                "- polymarket_api_calls_performed: "
                f"{raw['polymarket_api_calls_performed']}"
            ),
            "- non_polymarket_public_source_calls_performed: "
            f"{raw['non_polymarket_public_source_calls_performed']}",
            "- public_readonly_only: true",
            "- authenticated_endpoints_used: false",
            "- auth_headers_used: false",
            "- wallet_or_private_key_accessed: false",
            "- orders_created: false",
            "- browser_automation_used: false",
            (
                "- outcome_known_from_raw_payload: "
                f"{str(raw['outcome_known_from_raw_payload']).lower()}"
            ),
            "- operator_review_required: true",
            "- no_market_action_guidance: true",
            "- no_trading_authority: true",
        ]
    )


def render_normalized_evidence_markdown(evidence):
    return "\n".join(
        [
            "# PMBOT PAPERLIVE-004 Normalized Outcome Evidence",
            "",
            f"- task_id: {evidence['task_id']}",
            f"- market_id: {evidence['market_id']}",
            f"- outcome_evidence_status: {evidence['outcome_evidence_status']}",
            f"- outcome_known: {str(evidence['outcome_known']).lower()}",
            f"- outcome_resolution_status: {evidence['outcome_resolution_status']}",
            f"- result_source_type: {evidence['result_source_type']}",
            f"- final_result_text: {evidence['final_result_text']}",
            "- operator_review_required: true",
            (
                "- source_alignment_review_required: "
                f"{str(evidence['source_alignment_review_required']).lower()}"
            ),
            "- source_quality_update_allowed_now: false",
            "- source_scoring_performed: false",
            "- source_ranking_updated: false",
            "- trading_profit_used_for_scoring: false",
            "- no_market_action_guidance: true",
            "- no_trading_authority: true",
            "",
            "## Boundary",
            "",
            "- final result evidence, when present, is evidence only",
            "- no probability, EV, edge, confidence, or side selection guidance",
            "- no market action guidance",
        ]
    )


def render_call_ledger_markdown(ledger):
    lines = [
        "# PMBOT PAPERLIVE-004 Outcome Fetch Call Ledger",
        "",
        f"- task_id: {ledger['task_id']}",
        f"- market_id: {ledger['market_id']}",
        f"- total_network_call_count: {ledger['total_network_call_count']}",
        f"- polymarket_api_call_count: {ledger['polymarket_api_call_count']}",
        (
            "- non_polymarket_public_source_call_count: "
            f"{ledger['non_polymarket_public_source_call_count']}"
        ),
        f"- max_polymarket_api_calls: {ledger['max_polymarket_api_calls']}",
        f"- cap_exceeded: {str(ledger['cap_exceeded']).lower()}",
        "",
        "## Calls",
        "",
    ]
    for call in ledger["calls"]:
        lines.append(
            "- call_index: "
            f"{call['call_index']}; source_category: {call['source_category']}; "
            f"status: {call['status']}; auth_used: false"
        )
    lines.extend(
        [
            "",
            "## Safety",
            "",
            "- no authenticated endpoints",
            "- no wallet or private key access",
            "- no orders",
            "- no browser automation",
        ]
    )
    return "\n".join(lines)


def render_reconciliation_input_markdown(reconciliation):
    lines = [
        "# PMBOT PAPERLIVE-004 Reconciliation Input",
        "",
        f"- task_id: {reconciliation['task_id']}",
        f"- market_id: {reconciliation['market_id']}",
        f"- reconciliation_ready: {str(reconciliation['reconciliation_ready']).lower()}",
        f"- outcome_known: {str(reconciliation['outcome_known']).lower()}",
        "- source_alignment_review_performed: false",
        "- source_quality_update_performed: false",
        "- operator_review_required: true",
        "- no_market_action_guidance: true",
        "- no_trading_authority: true",
        "",
        "## Blockers",
        "",
    ]
    for blocker in reconciliation["blockers"]:
        lines.append(f"- {blocker}")
    if not reconciliation["blockers"]:
        lines.append("- none recorded")
    return "\n".join(lines)


def render_workbench_surface_markdown(surface):
    lines = [
        "# PMBOT PAPERLIVE-004 Passive Outcome Fetch Surface",
        "",
        f"- task_id: {surface['task_id']}",
        f"- market_id: {surface['market_id']}",
        "- raw_fetch_available: true",
        "- normalized_outcome_evidence_available: true",
        "- call_ledger_available: true",
        "- reconciliation_input_available: true",
        f"- outcome_known: {str(surface['outcome_known']).lower()}",
        f"- outcome_resolution_status: {surface['outcome_resolution_status']}",
        "- operator_review_required: true",
        "- simulated_trade_created: false",
        "- selected_side: null",
        "- stake_amount: null",
        "- no_market_action_guidance: true",
        "- no_trading_authority: true",
        "",
        "## Next Operator Actions",
        "",
    ]
    for action in surface["next_operator_actions"]:
        lines.append(f"- {action}")
    lines.extend(
        [
            "",
            "## Safety",
            "",
            "- no queue mutation",
            "- no runtime wiring change",
            "- no dispatcher change",
            "- no browser automation",
            "- no canonical packet mutation",
        ]
    )
    return "\n".join(lines)


def render_run_summary_markdown(summary):
    return "\n".join(
        [
            "# PMBOT PAPERLIVE-004 Controlled Readonly Outcome Fetch Summary",
            "",
            f"- task_id: {summary['task_id']}",
            f"- status: {summary['status']}",
            f"- market_id: {summary['market_id']}",
            f"- fetch_status: {summary['fetch_status']}",
            f"- fetch_performed: {str(summary['fetch_performed']).lower()}",
            f"- total_network_call_count: {summary['total_network_call_count']}",
            (
                "- polymarket_api_calls_performed: "
                f"{summary['polymarket_api_calls_performed']}"
            ),
            "- non_polymarket_public_source_calls_performed: "
            f"{summary['non_polymarket_public_source_calls_performed']}",
            f"- outcome_known: {str(summary['outcome_known']).lower()}",
            f"- outcome_checked: {str(summary['outcome_checked']).lower()}",
            f"- outcome_resolution_status: {summary['outcome_resolution_status']}",
            "- source_alignment_review_performed: false",
            "- source_scoring_performed: false",
            "- source_ranking_updated: false",
            "- simulated_trades_created_count: 0",
            "- orders_created_count: 0",
            "- selected_side_count: 0",
            "- stake_amount_count: 0",
            "- operator_review_required: true",
            "- no_market_action_guidance: true",
            "",
            "## Safety Summary",
            "",
            "- public read-only network only",
            "- no OpenRouter calls",
            "- no authenticated endpoints",
            "- no wallet or private key access",
            "- no orders",
            "- no simulated trade",
            "- no selected side",
            "- no stake",
            "- no probability, EV, edge, or confidence scoring",
            "- no source scoring",
            "- no source ranking update",
            "- no profit or PnL recorded",
            "- no runtime changes, no dispatcher changes, no background worker changes, no queue changes, no browser automation, and no canonical packet changes",
        ]
    )


def render_docs_markdown(result):
    return "\n".join(
        [
            "# PMBOT PAPERLIVE-004 Esports Controlled Readonly Outcome Source Fetch No Trade",
            "",
            "PAPERLIVE-004 performs controlled public read-only evidence collection only when `--fetch` is used.",
            "",
            "## Boundary",
            "",
            "- no auth",
            "- no wallet",
            "- no orders",
            "- no trading",
            "- no simulated trade",
            "- no side selected",
            "- no stake",
            "- no probability, EV, edge, or confidence",
            "- no source scoring",
            "- no source ranking",
            "- no profit or PnL",
            "- no runtime mutation, no queue mutation, and no canonical packet mutation",
            "- reconciliation is prepared for PAPERLIVE-005 and is not performed in this task",
            "- operator review is still required",
            "",
            "## Artifacts",
            "",
            f"- raw_fetch_artifact_created: {str(result['raw_fetch_artifact_created']).lower()}",
            (
                "- normalized_outcome_evidence_created: "
                f"{str(result['normalized_outcome_evidence_created']).lower()}"
            ),
            f"- call_ledger_created: {str(result['call_ledger_created']).lower()}",
            (
                "- reconciliation_input_created: "
                f"{str(result['reconciliation_input_created']).lower()}"
            ),
            (
                "- passive_workbench_surface_created: "
                f"{str(result['passive_workbench_surface_created']).lower()}"
            ),
            f"- outcome_known: {str(result['outcome_known']).lower()}",
            f"- outcome_resolution_status: {result['outcome_resolution_status']}",
        ]
    )


def write_artifacts(artifacts, root=ROOT):
    _write_json(RAW_FETCH_JSON_PATH, artifacts["raw_fetch"], root=root)
    _write_text(RAW_FETCH_MD_PATH, render_raw_fetch_markdown(artifacts["raw_fetch"]), root=root)
    _write_json(NORMALIZED_EVIDENCE_JSON_PATH, artifacts["normalized_evidence"], root=root)
    _write_text(
        NORMALIZED_EVIDENCE_MD_PATH,
        render_normalized_evidence_markdown(artifacts["normalized_evidence"]),
        root=root,
    )
    _write_json(CALL_LEDGER_JSON_PATH, artifacts["call_ledger"], root=root)
    _write_text(
        CALL_LEDGER_MD_PATH,
        render_call_ledger_markdown(artifacts["call_ledger"]),
        root=root,
    )
    _write_json(RECONCILIATION_INPUT_JSON_PATH, artifacts["reconciliation_input"], root=root)
    _write_text(
        RECONCILIATION_INPUT_MD_PATH,
        render_reconciliation_input_markdown(artifacts["reconciliation_input"]),
        root=root,
    )
    _write_json(WORKBENCH_SURFACE_JSON_PATH, artifacts["workbench_surface"], root=root)
    _write_text(
        WORKBENCH_SURFACE_MD_PATH,
        render_workbench_surface_markdown(artifacts["workbench_surface"]),
        root=root,
    )
    _write_json(RUN_SUMMARY_JSON_PATH, artifacts["run_summary"], root=root)
    _write_text(
        RUN_SUMMARY_MD_PATH,
        render_run_summary_markdown(artifacts["run_summary"]),
        root=root,
    )
    _write_json(DOC_RESULT_JSON_PATH, artifacts["docs_result"], root=root)
    _write_text(DOC_RESULT_MD_PATH, render_docs_markdown(artifacts["docs_result"]), root=root)
    return artifacts["run_summary"]


def build_dry_run(
    market_id=MARKET_ID,
    max_calls=DEFAULT_MAX_POLYMARKET_API_CALLS,
    max_markets=MAX_MARKETS_HARD_CAP,
):
    _validate_market_id(market_id)
    _validate_max_markets(max_markets)
    _validate_max_calls(max_calls)
    return {
        "schema_version": "paper_live_esports_controlled_readonly_outcome_fetch_dry_run.v1",
        "task_id": TASK_ID,
        "status": "dry_run_no_write",
        "dry_run": True,
        "fetch_performed": False,
        "market_id": MARKET_ID,
        "market_class": MARKET_CLASS,
        "network_allowed_explicitly": True,
        "planned_public_readonly_endpoints": [_event_detail_url(), _market_detail_url()],
        "max_polymarket_api_calls": int(max_calls),
        "max_non_polymarket_public_source_calls": MAX_NON_POLYMARKET_PUBLIC_SOURCE_CALLS,
        "max_markets": MAX_MARKETS_HARD_CAP,
        "files_written": [],
        "operator_review_required": True,
        "simulated_trade_created": False,
        "selected_side": None,
        "stake_amount": None,
        "no_market_action_guidance": True,
        "no_trading_authority": True,
        "safety_summary": _base_safety_summary(),
    }


def build_summary_only(root=ROOT):
    summary = _load_optional_json(RUN_SUMMARY_JSON_PATH, root=root)
    raw = _load_optional_json(RAW_FETCH_JSON_PATH, root=root)
    normalized = _load_optional_json(NORMALIZED_EVIDENCE_JSON_PATH, root=root)
    call_ledger = _load_optional_json(CALL_LEDGER_JSON_PATH, root=root)
    reconciliation = _load_optional_json(RECONCILIATION_INPUT_JSON_PATH, root=root)
    workbench = _load_optional_json(WORKBENCH_SURFACE_JSON_PATH, root=root)
    pipeline = _pipeline_snapshot(root=root)
    return {
        "schema_version": "paper_live_esports_controlled_readonly_outcome_fetch_summary_only.v1",
        "task_id": TASK_ID,
        "status": "summary_only",
        "market_id": MARKET_ID,
        "market_class": MARKET_CLASS,
        "raw_fetch_available": raw is not None,
        "normalized_outcome_evidence_available": normalized is not None,
        "call_ledger_available": call_ledger is not None,
        "reconciliation_input_available": reconciliation is not None,
        "passive_workbench_surface_available": workbench is not None,
        "summary_exists": summary is not None,
        "fetch_status": (summary or {}).get("fetch_status"),
        "fetch_performed": bool((summary or {}).get("fetch_performed", False)),
        "outcome_checked": bool((summary or {}).get("outcome_checked", False)),
        "outcome_known": bool((summary or {}).get("outcome_known", False)),
        "outcome_resolution_status": (summary or {}).get("outcome_resolution_status"),
        "total_network_call_count": (summary or {}).get("total_network_call_count", 0),
        "polymarket_api_calls_performed": (summary or {}).get(
            "polymarket_api_calls_performed", 0
        ),
        "non_polymarket_public_source_calls_performed": (summary or {}).get(
            "non_polymarket_public_source_calls_performed", 0
        ),
        "source_alignment_review_performed": False,
        "source_scoring_performed": False,
        "source_ranking_updated": False,
        "real_ingested_template_count": pipeline.get("real_ingested_template_count"),
        "draft_ingested_template_count": pipeline.get("draft_ingested_template_count"),
        "ready_ingested_template_count": pipeline.get("ready_ingested_template_count"),
        "future_live_002_allowed": pipeline.get("future_live_002_allowed"),
        "openrouter_calls_performed": 0,
    }


def run_fetch(
    write=False,
    market_id=MARKET_ID,
    max_calls=DEFAULT_MAX_POLYMARKET_API_CALLS,
    max_markets=MAX_MARKETS_HARD_CAP,
    fetcher=None,
    root=ROOT,
):
    artifacts = perform_controlled_fetch(
        market_id=market_id,
        max_calls=max_calls,
        max_markets=max_markets,
        fetcher=fetcher,
        root=root,
    )
    payload = {
        "schema_version": "paper_live_esports_controlled_readonly_outcome_fetch_run.v1",
        "task_id": TASK_ID,
        "status": artifacts["run_summary"]["status"],
        "fetch_status": artifacts["run_summary"]["fetch_status"],
        "market_id": MARKET_ID,
        "market_class": MARKET_CLASS,
        "fetch_performed": artifacts["run_summary"]["fetch_performed"],
        "artifacts_written": bool(write),
        "network_allowed_explicitly": True,
        "total_network_call_count": artifacts["run_summary"]["total_network_call_count"],
        "polymarket_api_calls_performed": artifacts["run_summary"][
            "polymarket_api_calls_performed"
        ],
        "non_polymarket_public_source_calls_performed": artifacts["run_summary"][
            "non_polymarket_public_source_calls_performed"
        ],
        "outcome_checked": artifacts["run_summary"]["outcome_checked"],
        "outcome_known": artifacts["run_summary"]["outcome_known"],
        "outcome_resolution_status": artifacts["run_summary"]["outcome_resolution_status"],
        "operator_review_required": True,
        "no_market_action_guidance": True,
        "no_trading_authority": True,
    }
    if write:
        write_artifacts(artifacts, root=root)
        payload["files_written"] = OUTPUT_PATHS
    else:
        payload["files_written"] = []
    return payload


def main(argv):
    args = _parse_args(argv)
    if args.summary_only:
        if args.write:
            raise SystemExit("--write is not valid with --summary-only")
        payload = build_summary_only(ROOT)
    elif args.fetch:
        payload = run_fetch(
            write=args.write,
            market_id=args.market_id,
            max_calls=args.max_calls,
            max_markets=args.max_markets,
            root=ROOT,
        )
    else:
        if args.write:
            raise SystemExit("--write is only valid with --fetch")
        payload = build_dry_run(
            market_id=args.market_id,
            max_calls=args.max_calls,
            max_markets=args.max_markets,
        )
    print(json.dumps(payload, indent=2, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(__import__("sys").argv[1:]))
