import argparse
import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCHEMA_VERSION = "polymarket_readonly_raw_snapshot.v1"
ARTIFACT_TYPE = "polymarket_public_market_snapshot"
VALIDATION_SCHEMA_VERSION = "polymarket_raw_snapshot_validation.v1"
MARKETS_SOURCE_NAME = "polymarket_gamma_markets"
EVENTS_SOURCE_NAME = "polymarket_gamma_events"
SOURCE_NAME = MARKETS_SOURCE_NAME
MARKETS_ENDPOINT = "https://" + "gamma" + "-api" + ".polymarket.com/markets"
EVENTS_ENDPOINT = "https://" + "gamma" + "-api" + ".polymarket.com/events"
SUPPORTED_SOURCES = {
    MARKETS_SOURCE_NAME: {
        "endpoint": MARKETS_ENDPOINT,
        "payload_shape": "markets",
    },
    EVENTS_SOURCE_NAME: {
        "endpoint": EVENTS_ENDPOINT,
        "payload_shape": "events",
    },
}
FORBIDDEN_KEYS = {
    "api_key",
    "api_secret",
    "authorization",
    "authorization_header",
    "cancel_order",
    "execute_trade",
    "place_order",
    "private_key",
    "seed_phrase",
    "signer",
    "signature",
    "submit_order",
}
EXPECTED_NETWORK_BOUNDARY = {
    "authenticated_endpoints_used": False,
    "credentials_required": False,
    "public_readonly_polymarket_only": True,
    "trading_endpoints_used": False,
    "wallet_required": False,
}


def canonical_json_bytes(payload):
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _finding(file_path, severity, code, message):
    return {
        "code": code,
        "file": str(file_path).replace("\\", "/"),
        "message": message,
        "severity": severity,
    }


def _append(findings, file_path, severity, code, message):
    findings.append(_finding(file_path, severity, code, message))


def _non_empty_text(value):
    return isinstance(value, str) and bool(value.strip())


def _parse_timestamp(value):
    if not _non_empty_text(value):
        return None
    normalized = value.strip().replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(normalized)
    except ValueError:
        return None


def _load_json(path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _display_file_path(file_path):
    path = Path(file_path)
    if path.is_absolute():
        try:
            return str(path.resolve().relative_to(ROOT.resolve())).replace("\\", "/")
        except ValueError:
            return str(path).replace("\\", "/")
    return str(file_path).replace("\\", "/")


def _iter_keys(payload):
    if isinstance(payload, dict):
        for key, value in payload.items():
            yield str(key)
            yield from _iter_keys(value)
    elif isinstance(payload, list):
        for item in payload:
            yield from _iter_keys(item)


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


def _first_text(mapping, keys):
    for key in keys:
        value = mapping.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
        if isinstance(value, (int, float)):
            return str(value)
    return None


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


def _is_active_open_market(market):
    return _coerce_bool(market.get("active")) is True and _coerce_bool(market.get("closed")) is False


def _validate_source(source, file_path, findings):
    if not isinstance(source, dict):
        _append(findings, file_path, "blocking", "source_not_object", "source must be an object.")
        return None
    source_name = source.get("name")
    if source_name not in SUPPORTED_SOURCES:
        _append(
            findings,
            file_path,
            "blocking",
            "invalid_source:name",
            f"source.name must be one of {sorted(SUPPORTED_SOURCES)!r}.",
        )
        return None
    expected_endpoint = SUPPORTED_SOURCES[source_name]["endpoint"]
    expected = {
        "endpoint": expected_endpoint,
        "method": "GET",
        "network_mode": "public_readonly",
    }
    for key, value in expected.items():
        if source.get(key) != value:
            _append(findings, file_path, "blocking", f"invalid_source:{key}", f"source.{key} must equal {value!r}.")
    url = source.get("url")
    source_url = source.get("source_url")
    if not _non_empty_text(url) or not url.startswith(expected_endpoint + "?"):
        _append(findings, file_path, "blocking", "invalid_source:url", "source.url must be a supported Gamma URL with query parameters.")
    if source_url is not None:
        if source_url != url:
            _append(findings, file_path, "blocking", "invalid_source:source_url", "source.source_url must match source.url.")
        elif not source_url.startswith(expected_endpoint + "?"):
            _append(findings, file_path, "blocking", "invalid_source:source_url", "source.source_url must be a supported Gamma URL with query parameters.")
    return source_name


def _validate_query(query, file_path, findings):
    if not isinstance(query, dict):
        _append(findings, file_path, "blocking", "query_not_object", "query must be an object.")
        return
    expected = {
        "active": "true",
        "closed": "false",
    }
    for key, value in expected.items():
        if query.get(key) != value:
            _append(findings, file_path, "blocking", f"invalid_query:{key}", f"query.{key} must equal {value!r}.")
    try:
        limit = int(query.get("limit"))
    except (TypeError, ValueError):
        limit = None
    if limit is None or limit < 1 or limit > 100:
        _append(findings, file_path, "blocking", "invalid_query:limit", "query.limit must be an integer string from 1 through 100.")


def _validate_network_boundary(boundary, file_path, findings):
    if not isinstance(boundary, dict):
        _append(findings, file_path, "blocking", "network_boundary_not_object", "network_boundary must be an object.")
        return
    for key, expected in EXPECTED_NETWORK_BOUNDARY.items():
        if key not in boundary:
            _append(findings, file_path, "blocking", f"missing_network_boundary:{key}", f"network_boundary.{key} is required.")
            continue
        value = boundary[key]
        if not isinstance(value, bool):
            _append(findings, file_path, "blocking", f"invalid_network_boundary:{key}", f"network_boundary.{key} must be boolean.")
        elif value != expected:
            _append(findings, file_path, "blocking", f"unsafe_network_boundary:{key}", f"network_boundary.{key} must equal {expected}.")


def _validate_raw_payload(payload, payload_hash, source_name, file_path, findings):
    if not isinstance(payload, (dict, list)):
        _append(findings, file_path, "blocking", "raw_payload_bad_type", "raw_payload must be a JSON object or list.")
        return {
            "events": [],
            "markets": [],
            "nested_markets": [],
        }
    expected_hash = hashlib.sha256(canonical_json_bytes(payload)).hexdigest()
    if payload_hash != expected_hash:
        _append(findings, file_path, "blocking", "raw_payload_hash_mismatch", "raw_payload_sha256 does not match raw_payload.")
    events = []
    markets = []
    nested_markets = []
    if source_name == EVENTS_SOURCE_NAME:
        events = extract_event_records(payload)
        nested_markets = extract_nested_market_records(payload)
        if not events:
            _append(findings, file_path, "blocking", "raw_payload_no_events", "raw_payload must contain at least one event object.")
        if not nested_markets:
            _append(findings, file_path, "blocking", "raw_payload_no_nested_markets", "events raw_payload must contain at least one nested market object.")
    else:
        markets = extract_market_records(payload)
        if not markets:
            _append(findings, file_path, "blocking", "raw_payload_no_markets", "raw_payload must contain at least one market object.")
    return {
        "events": events,
        "markets": markets,
        "nested_markets": nested_markets,
    }


def _validate_markets_summary(summary, market_count, file_path, findings):
    markets = summary.get("markets")
    if not isinstance(markets, list):
        _append(findings, file_path, "blocking", "summary_markets_not_list", "normalized_summary.markets must be a list.")
        markets = []
    if summary.get("market_count") != len(markets) or summary.get("market_count") != market_count:
        _append(findings, file_path, "blocking", "summary_market_count_mismatch", "normalized_summary.market_count must match raw and summary market counts.")
    expected_ids = []
    for index, market in enumerate(markets):
        prefix = f"normalized_summary.markets[{index}]"
        if not isinstance(market, dict):
            _append(findings, file_path, "blocking", "summary_market_not_object", f"{prefix} must be an object.")
            continue
        market_id = market.get("id")
        question = market.get("question")
        if not _non_empty_text(market_id):
            _append(findings, file_path, "blocking", f"summary_market_missing_id:{index}", f"{prefix}.id must be a non-empty string.")
        else:
            expected_ids.append(market_id)
        if not _non_empty_text(question):
            _append(findings, file_path, "blocking", f"summary_market_missing_question:{index}", f"{prefix}.question must be a non-empty string.")
        if market.get("active") is not True:
            _append(findings, file_path, "blocking", f"summary_market_not_active:{index}", f"{prefix}.active must be true.")
        if market.get("closed") is not False:
            _append(findings, file_path, "blocking", f"summary_market_closed:{index}", f"{prefix}.closed must be false.")
        outcome_count = market.get("outcome_count")
        if not isinstance(outcome_count, int) or outcome_count < 1:
            _append(findings, file_path, "blocking", f"summary_market_bad_outcome_count:{index}", f"{prefix}.outcome_count must be a positive integer.")
    if summary.get("market_ids") != expected_ids:
        _append(findings, file_path, "blocking", "summary_market_ids_mismatch", "normalized_summary.market_ids must match summary market ids in order.")


def _validate_events_summary(summary, raw_counts, file_path, findings):
    events = raw_counts["events"]
    nested_markets = raw_counts["nested_markets"]
    active_open_count = sum(1 for market in nested_markets if _is_active_open_market(market))
    if summary.get("payload_shape") != "events_with_nested_markets":
        _append(findings, file_path, "blocking", "summary_payload_shape_mismatch", "normalized_summary.payload_shape must describe events with nested markets.")
    if summary.get("events_count") != len(events):
        _append(findings, file_path, "blocking", "summary_events_count_mismatch", "normalized_summary.events_count must match raw event count.")
    if summary.get("nested_markets_count") != len(nested_markets):
        _append(findings, file_path, "blocking", "summary_nested_markets_count_mismatch", "normalized_summary.nested_markets_count must match nested market count.")
    if summary.get("active_open_nested_markets_count") != active_open_count:
        _append(findings, file_path, "blocking", "summary_active_open_nested_markets_count_mismatch", "normalized_summary.active_open_nested_markets_count must match nested active/open market count.")
    if active_open_count < 1:
        _append(findings, file_path, "blocking", "raw_payload_no_active_open_nested_markets", "events raw_payload must contain at least one active non-closed nested market.")
    expected_event_ids = []
    sorted_events = sorted(events, key=lambda item: ((_first_text(item, ("id", "eventId", "event_id")) or ""), (_first_text(item, ("title", "question", "name")) or "")))
    for event in sorted_events:
        event_id = _first_text(event, ("id", "eventId", "event_id"))
        if event_id:
            expected_event_ids.append(event_id)
    if summary.get("event_ids") != expected_event_ids:
        _append(findings, file_path, "blocking", "summary_event_ids_mismatch", "normalized_summary.event_ids must match raw event ids in order.")
    summary_events = summary.get("events")
    if not isinstance(summary_events, list):
        _append(findings, file_path, "blocking", "summary_events_not_list", "normalized_summary.events must be a list.")
        return
    if len(summary_events) != len(events):
        _append(findings, file_path, "blocking", "summary_events_length_mismatch", "normalized_summary.events length must match raw event count.")
    for index, event in enumerate(summary_events):
        prefix = f"normalized_summary.events[{index}]"
        if not isinstance(event, dict):
            _append(findings, file_path, "blocking", "summary_event_not_object", f"{prefix} must be an object.")
            continue
        nested_count = event.get("nested_market_count")
        if not isinstance(nested_count, int) or nested_count < 1:
            _append(findings, file_path, "blocking", f"summary_event_bad_nested_market_count:{index}", f"{prefix}.nested_market_count must be a positive integer.")
        active_open_nested_count = event.get("active_open_nested_market_count")
        if not isinstance(active_open_nested_count, int) or active_open_nested_count < 1:
            _append(findings, file_path, "blocking", f"summary_event_bad_active_open_nested_market_count:{index}", f"{prefix}.active_open_nested_market_count must be a positive integer.")


def _validate_normalized_summary(summary, raw_counts, source_name, file_path, findings):
    if not isinstance(summary, dict):
        _append(findings, file_path, "blocking", "normalized_summary_not_object", "normalized_summary must be an object.")
        return
    filter_spec = summary.get("active_non_closed_filter")
    if filter_spec != {"active": True, "closed": False}:
        _append(findings, file_path, "blocking", "invalid_active_non_closed_filter", "normalized_summary must preserve active=true and closed=false filter metadata.")
    if source_name == EVENTS_SOURCE_NAME:
        _validate_events_summary(summary, raw_counts, file_path, findings)
    else:
        _validate_markets_summary(summary, len(raw_counts["markets"]), file_path, findings)


def validate_snapshot(payload, file_path="<memory>"):
    findings = []
    if not isinstance(payload, dict):
        _append(findings, file_path, "blocking", "snapshot_not_object", "Snapshot root must be a JSON object.")
        return findings

    required_fields = (
        "artifact_id",
        "artifact_type",
        "fetched_at",
        "network_boundary",
        "normalized_summary",
        "query",
        "raw_payload",
        "raw_payload_sha256",
        "schema_version",
        "source",
    )
    for field in required_fields:
        if field not in payload:
            _append(findings, file_path, "blocking", f"missing_required_field:{field}", f"Missing required field '{field}'.")

    if payload.get("schema_version") != SCHEMA_VERSION:
        _append(findings, file_path, "blocking", "bad_schema_version", f"schema_version must equal {SCHEMA_VERSION!r}.")
    if payload.get("artifact_type") != ARTIFACT_TYPE:
        _append(findings, file_path, "blocking", "bad_artifact_type", f"artifact_type must equal {ARTIFACT_TYPE!r}.")
    if not _non_empty_text(payload.get("artifact_id")):
        _append(findings, file_path, "blocking", "empty_artifact_id", "artifact_id must be a non-empty string.")
    if _parse_timestamp(payload.get("fetched_at")) is None:
        _append(findings, file_path, "blocking", "invalid_fetched_at", "fetched_at must be an ISO-like timestamp string.")

    prohibited_keys_seen = sorted({key for key in _iter_keys(payload) if key.lower() in FORBIDDEN_KEYS})
    if prohibited_keys_seen:
        _append(findings, file_path, "blocking", "prohibited_key_seen", f"Snapshot includes prohibited keys: {', '.join(prohibited_keys_seen)}.")

    source_name = _validate_source(payload.get("source"), file_path, findings)
    _validate_query(payload.get("query"), file_path, findings)
    _validate_network_boundary(payload.get("network_boundary"), file_path, findings)
    raw_counts = _validate_raw_payload(payload.get("raw_payload"), payload.get("raw_payload_sha256"), source_name, file_path, findings)
    _validate_normalized_summary(payload.get("normalized_summary"), raw_counts, source_name, file_path, findings)

    validation = payload.get("validation")
    if validation is not None:
        if not isinstance(validation, dict):
            _append(findings, file_path, "blocking", "validation_not_object", "validation must be an object when present.")
        elif "passed" in validation and not isinstance(validation["passed"], bool) and validation["passed"] is not None:
            _append(findings, file_path, "blocking", "validation_passed_bad_type", "validation.passed must be boolean or null.")

    findings.sort(key=lambda item: (item["file"], item["severity"], item["code"], item["message"]))
    return findings


def build_report_for_payload(payload, file_path):
    display_file = _display_file_path(file_path)
    findings = validate_snapshot(payload, display_file)
    return {
        "downstream_feed_allowed": False,
        "finding_count": len(findings),
        "findings": findings,
        "network_boundary": {
            "authenticated_endpoints_used": False,
            "credentials_required": False,
            "public_readonly_polymarket_only": True,
            "trading_endpoints_used": False,
            "wallet_required": False,
        },
        "quarantine_required": bool(findings),
        "schema_version": VALIDATION_SCHEMA_VERSION,
        "validated_file": display_file,
        "validation_passed": not findings,
    }


def build_validation_report(snapshot_path):
    snapshot_path = Path(snapshot_path)
    try:
        payload = _load_json(snapshot_path)
    except Exception as exc:
        display_file = _display_file_path(snapshot_path)
        findings = [
            _finding(
                display_file,
                "blocking",
                "snapshot_load_failed",
                f"{type(exc).__name__}: {exc}",
            )
        ]
        return {
            "downstream_feed_allowed": False,
            "finding_count": len(findings),
            "findings": findings,
            "network_boundary": EXPECTED_NETWORK_BOUNDARY,
            "quarantine_required": True,
            "schema_version": VALIDATION_SCHEMA_VERSION,
            "validated_file": display_file,
            "validation_passed": False,
        }
    return build_report_for_payload(payload, str(snapshot_path))


def _parse_args(argv):
    parser = argparse.ArgumentParser(description="Validate a captured read-only Polymarket raw snapshot.")
    parser.add_argument("snapshot_path")
    parser.add_argument("--write-report")
    return parser.parse_args(argv)


def _resolve_path(path_text):
    path = Path(path_text)
    if path.is_absolute():
        return path
    return (ROOT / path).resolve()


def main(argv):
    args = _parse_args(argv)
    report = build_validation_report(_resolve_path(args.snapshot_path))
    rendered = json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    if args.write_report:
        output_path = _resolve_path(args.write_report)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0 if report["validation_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
