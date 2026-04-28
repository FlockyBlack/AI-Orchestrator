import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib import error, parse, request


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pm_bot.ingest.validate_polymarket_raw_snapshot import (
    build_report_for_payload,
    validate_snapshot,
)


SCHEMA_VERSION = "polymarket_readonly_raw_snapshot.v1"
ARTIFACT_TYPE = "polymarket_public_market_snapshot"
MARKETS_SOURCE_KEY = "markets"
EVENTS_SOURCE_KEY = "events"
MARKETS_SOURCE_NAME = "polymarket_gamma_markets"
EVENTS_SOURCE_NAME = "polymarket_gamma_events"
SOURCE_NAME = EVENTS_SOURCE_NAME
DEFAULT_LIMIT = 25
MAX_LIMIT = 100
DEFAULT_TIMEOUT_SECONDS = 20
DEFAULT_OUTPUT_DIR = ROOT / "pm_bot" / "ingest" / "raw_snapshots"
DEFAULT_QUARANTINE_DIR = ROOT / "pm_bot" / "ingest" / "quarantine"
GAMMA_MARKETS_ENDPOINT = "https://" + "gamma" + "-api" + ".polymarket.com/markets"
GAMMA_EVENTS_ENDPOINT = "https://" + "gamma" + "-api" + ".polymarket.com/events"
SOURCE_CONFIGS = {
    MARKETS_SOURCE_KEY: {
        "endpoint": GAMMA_MARKETS_ENDPOINT,
        "name": MARKETS_SOURCE_NAME,
    },
    EVENTS_SOURCE_KEY: {
        "endpoint": GAMMA_EVENTS_ENDPOINT,
        "name": EVENTS_SOURCE_NAME,
    },
}
DEFAULT_SOURCE = EVENTS_SOURCE_KEY


def utc_now_text():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def canonical_json_bytes(payload):
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def raw_payload_hash(raw_payload):
    return hashlib.sha256(canonical_json_bytes(raw_payload)).hexdigest()


def write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    rendered = json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    path.write_text(rendered, encoding="utf-8")


def clamp_limit(value):
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        parsed = DEFAULT_LIMIT
    return min(MAX_LIMIT, max(1, parsed))


def build_query(limit):
    return {
        "active": "true",
        "closed": "false",
        "limit": str(clamp_limit(limit)),
    }


def build_url(endpoint, query):
    encoded = parse.urlencode(sorted(query.items()))
    return f"{endpoint}?{encoded}"


def resolve_source_config(source_key, source_endpoint=None):
    if source_key not in SOURCE_CONFIGS:
        raise ValueError(f"unsupported source {source_key!r}; expected one of {sorted(SOURCE_CONFIGS)}")
    config = dict(SOURCE_CONFIGS[source_key])
    if source_endpoint is not None:
        config["endpoint"] = source_endpoint
    return config


def fetch_json(url, timeout_seconds):
    http_call = request.Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "PMBOT-readonly-snapshot/1.0",
        },
        method="GET",
    )
    try:
        with request.urlopen(http_call, timeout=timeout_seconds) as response:
            body = response.read()
    except error.URLError as exc:
        raise RuntimeError(f"public read-only market data fetch failed: {exc}") from exc

    try:
        return json.loads(body.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"public read-only market data response was not JSON: {exc}") from exc


def _first_text(mapping, keys):
    for key in keys:
        value = mapping.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
        if isinstance(value, (int, float)):
            return str(value)
    return None


def _coerce_bool(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized == "true":
            return True
        if normalized == "false":
            return False
    return None


def _coerce_number(value):
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return value
    if isinstance(value, str) and value.strip():
        try:
            return float(value)
        except ValueError:
            return None
    return None


def _json_list_or_empty(value):
    if isinstance(value, list):
        return value
    if isinstance(value, str) and value.strip():
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return []
        return parsed if isinstance(parsed, list) else []
    return []


def extract_market_records(raw_payload):
    if isinstance(raw_payload, list):
        return [item for item in raw_payload if isinstance(item, dict)]
    if not isinstance(raw_payload, dict):
        return []
    for key in ("markets", "data", "results"):
        value = raw_payload.get(key)
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]
    return []


def extract_event_records(raw_payload):
    if isinstance(raw_payload, list):
        return [item for item in raw_payload if isinstance(item, dict)]
    if not isinstance(raw_payload, dict):
        return []
    for key in ("events", "data", "results"):
        value = raw_payload.get(key)
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]
    return []


def extract_nested_market_records(raw_payload):
    markets = []
    for event in extract_event_records(raw_payload):
        nested_markets = event.get("markets")
        if isinstance(nested_markets, list):
            markets.extend(item for item in nested_markets if isinstance(item, dict))
    return markets


def is_active_open_market(market):
    return _coerce_bool(market.get("active")) is True and _coerce_bool(market.get("closed")) is False


def summarize_market(market):
    outcomes = _json_list_or_empty(market.get("outcomes"))
    return {
        "active": _coerce_bool(market.get("active")),
        "archived": _coerce_bool(market.get("archived")),
        "closed": _coerce_bool(market.get("closed")),
        "condition_id": _first_text(market, ("conditionId", "condition_id")),
        "end_date": _first_text(market, ("endDate", "end_date", "endDateIso")),
        "id": _first_text(market, ("id", "marketId", "market_id", "conditionId")),
        "liquidity": _coerce_number(market.get("liquidity")),
        "outcome_count": len(outcomes),
        "question": _first_text(market, ("question", "title")),
        "slug": _first_text(market, ("slug",)),
        "volume": _coerce_number(market.get("volume")),
    }


def summarize_event(event):
    nested_markets = [item for item in event.get("markets", []) if isinstance(item, dict)]
    return {
        "active": _coerce_bool(event.get("active")),
        "active_open_nested_market_count": sum(1 for market in nested_markets if is_active_open_market(market)),
        "closed": _coerce_bool(event.get("closed")),
        "id": _first_text(event, ("id", "eventId", "event_id")),
        "nested_market_count": len(nested_markets),
        "slug": _first_text(event, ("slug",)),
        "title": _first_text(event, ("title", "question", "name")),
    }


def build_markets_normalized_summary(raw_payload):
    markets = [summarize_market(market) for market in extract_market_records(raw_payload)]
    markets.sort(key=lambda item: ((item.get("id") or ""), (item.get("question") or "")))
    market_ids = [item["id"] for item in markets if item.get("id")]
    return {
        "active_non_closed_filter": {
            "active": True,
            "closed": False,
        },
        "market_count": len(markets),
        "market_ids": market_ids,
        "markets": markets,
    }


def build_events_normalized_summary(raw_payload):
    events = [summarize_event(event) for event in extract_event_records(raw_payload)]
    events.sort(key=lambda item: ((item.get("id") or ""), (item.get("title") or "")))
    event_ids = [item["id"] for item in events if item.get("id")]
    nested_markets = extract_nested_market_records(raw_payload)
    return {
        "active_non_closed_filter": {
            "active": True,
            "closed": False,
        },
        "active_open_nested_markets_count": sum(1 for market in nested_markets if is_active_open_market(market)),
        "event_ids": event_ids,
        "events": events,
        "events_count": len(events),
        "nested_markets_count": len(nested_markets),
        "payload_shape": "events_with_nested_markets",
    }


def build_normalized_summary(raw_payload, source_name):
    if source_name == EVENTS_SOURCE_NAME:
        return build_events_normalized_summary(raw_payload)
    return build_markets_normalized_summary(raw_payload)


def artifact_filename(snapshot):
    timestamp = snapshot["fetched_at"].replace(":", "").replace("-", "")
    timestamp = timestamp.replace("Z", "Z").replace("+0000", "Z")
    source_name = snapshot["source"]["name"]
    return f"{source_name}_{timestamp}_{snapshot['raw_payload_sha256'][:12]}.json"


def build_snapshot(raw_payload, fetched_at, source_url, query, source_config):
    payload_hash = raw_payload_hash(raw_payload)
    timestamp_fragment = fetched_at.replace(":", "").replace("-", "")
    source_name = source_config["name"]
    return {
        "artifact_id": f"{source_name}_{timestamp_fragment}_{payload_hash[:12]}",
        "artifact_type": ARTIFACT_TYPE,
        "fetched_at": fetched_at,
        "network_boundary": {
            "authenticated_endpoints_used": False,
            "credentials_required": False,
            "public_readonly_polymarket_only": True,
            "trading_endpoints_used": False,
            "wallet_required": False,
        },
        "normalized_summary": build_normalized_summary(raw_payload, source_name),
        "query": query,
        "raw_payload": raw_payload,
        "raw_payload_sha256": payload_hash,
        "schema_version": SCHEMA_VERSION,
        "source": {
            "endpoint": source_url.split("?", 1)[0],
            "method": "GET",
            "name": source_name,
            "network_mode": "public_readonly",
            "source_url": source_url,
            "url": source_url,
        },
        "validation": {
            "finding_count": 0,
            "findings": [],
            "passed": None,
            "validated_at": fetched_at,
        },
    }


def finalize_validation(snapshot):
    findings = validate_snapshot(snapshot)
    snapshot["validation"] = {
        "finding_count": len(findings),
        "findings": findings,
        "passed": not findings,
        "validated_at": snapshot["fetched_at"],
    }
    return findings


def capture_polymarket_snapshot(
    limit=DEFAULT_LIMIT,
    output_dir=DEFAULT_OUTPUT_DIR,
    quarantine_dir=DEFAULT_QUARANTINE_DIR,
    timeout_seconds=DEFAULT_TIMEOUT_SECONDS,
    fetch_json_func=fetch_json,
    now_func=utc_now_text,
    source=DEFAULT_SOURCE,
    source_endpoint=None,
):
    source_config = resolve_source_config(source, source_endpoint)
    query = build_query(limit)
    source_url = build_url(source_config["endpoint"], query)
    fetched_at = now_func()
    raw_payload = fetch_json_func(source_url, timeout_seconds)
    snapshot = build_snapshot(raw_payload, fetched_at, source_url, query, source_config)
    findings = finalize_validation(snapshot)

    target_dir = Path(output_dir if not findings else quarantine_dir)
    snapshot_path = target_dir / artifact_filename(snapshot)
    write_json(snapshot_path, snapshot)

    report = build_report_for_payload(snapshot, str(snapshot_path))
    report_path = snapshot_path.with_suffix(".validation.json")
    write_json(report_path, report)

    summary = snapshot["normalized_summary"]
    return {
        "artifact_path": str(snapshot_path),
        "active_open_nested_markets_count": summary.get("active_open_nested_markets_count"),
        "events_count": summary.get("events_count"),
        "market_count": summary.get("market_count"),
        "nested_markets_count": summary.get("nested_markets_count"),
        "quarantine_path": str(snapshot_path) if findings else None,
        "report_path": str(report_path),
        "source": source_config["name"],
        "source_url": source_url,
        "validation_passed": not findings,
    }


def _parse_args(argv):
    parser = argparse.ArgumentParser(description="Capture a read-only public Polymarket Gamma snapshot.")
    parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT)
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--quarantine-dir", default=str(DEFAULT_QUARANTINE_DIR))
    parser.add_argument("--source", choices=sorted(SOURCE_CONFIGS), default=DEFAULT_SOURCE)
    parser.add_argument("--timeout-seconds", type=int, default=DEFAULT_TIMEOUT_SECONDS)
    return parser.parse_args(argv)


def _resolve_path(path_text):
    path = Path(path_text)
    if path.is_absolute():
        return path
    return (ROOT / path).resolve()


def main(argv):
    args = _parse_args(argv)
    try:
        result = capture_polymarket_snapshot(
            limit=args.limit,
            output_dir=_resolve_path(args.output_dir),
            quarantine_dir=_resolve_path(args.quarantine_dir),
            source=args.source,
            timeout_seconds=args.timeout_seconds,
        )
    except RuntimeError as exc:
        result = {
            "error": str(exc),
            "source": SOURCE_CONFIGS[args.source]["name"],
            "validation_passed": False,
        }
        print(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True))
        return 1

    print(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True))
    return 0 if result["validation_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
