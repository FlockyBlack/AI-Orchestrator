import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pm_bot.ingest.validate_polymarket_raw_snapshot import (  # noqa: E402
    EVENTS_SOURCE_NAME,
    extract_event_records,
    validate_snapshot,
)


PREVIEW_SCHEMA_VERSION = "normalized_market_preview.v1"
PREVIEW_ARTIFACT_TYPE = "polymarket_normalized_market_preview"
DEFAULT_OUTPUT_JSON = ROOT / "pm_bot" / "ingest" / "normalized_market_preview.v1.json"
DEFAULT_OUTPUT_MD = ROOT / "pm_bot" / "ingest" / "normalized_market_preview.v1.md"
RECORD_FIELDS = (
    "source_snapshot_artifact_id",
    "source_snapshot_path",
    "source_name",
    "event_id",
    "event_slug",
    "event_title",
    "event_active",
    "event_closed",
    "market_id",
    "question",
    "market_slug",
    "category_or_tags",
    "active",
    "closed",
    "accepting_orders",
    "end_date",
    "start_date",
    "description",
    "outcomes",
    "outcome_prices",
    "liquidity",
    "volume",
    "condition_id",
    "clob_token_ids",
    "enable_order_book",
    "restricted",
    "raw_market_updated_at",
)


class NormalizationPreviewError(Exception):
    def __init__(self, code, message, details=None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details or {}


def _load_json(path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    rendered = json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    path.write_text(rendered, encoding="utf-8")


def _write_text(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _display_file_path(file_path):
    path = Path(file_path)
    if path.is_absolute():
        try:
            return str(path.resolve().relative_to(ROOT.resolve())).replace("\\", "/")
        except ValueError:
            return str(path).replace("\\", "/")
    return str(file_path).replace("\\", "/")


def _resolve_path(path_text):
    path = Path(path_text)
    if path.is_absolute():
        return path
    return (ROOT / path).resolve()


def _first_text(mapping, keys):
    for key in keys:
        value = mapping.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return str(value)
    return None


def _first_present(mapping, keys):
    for key in keys:
        if key in mapping:
            return key, mapping[key]
    return None, None


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


def _warning(code, field, event, event_index, market, market_index, message):
    return {
        "code": code,
        "event_id": _first_text(event, ("id", "eventId", "event_id")),
        "event_index": event_index,
        "field": field,
        "market_id": _first_text(market, ("id", "marketId", "market_id", "conditionId")),
        "market_index": market_index,
        "message": message,
    }


def _parse_json_list_field(mapping, keys, event, event_index, market_index, warnings):
    source_key, value = _first_present(mapping, keys)
    output_key = keys[0]
    if source_key is None or value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        if not value.strip():
            warnings.append(
                _warning(
                    "json_string_empty",
                    source_key,
                    event,
                    event_index,
                    mapping,
                    market_index,
                    "Expected a JSON list string; using an empty list.",
                )
            )
            return []
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            warnings.append(
                _warning(
                    "json_list_parse_failed",
                    source_key,
                    event,
                    event_index,
                    mapping,
                    market_index,
                    "Expected a JSON list string; using an empty list.",
                )
            )
            return []
        if isinstance(parsed, list):
            return parsed
        warnings.append(
            _warning(
                "json_value_not_list",
                source_key,
                event,
                event_index,
                mapping,
                market_index,
                "Expected a JSON list value; using an empty list.",
            )
        )
        return []
    warnings.append(
        _warning(
            "json_value_not_list",
            output_key,
            event,
            event_index,
            mapping,
            market_index,
            "Expected a list or JSON list string; using an empty list.",
        )
    )
    return []


def _normalize_tags_value(value):
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    if not isinstance(value, list):
        return []
    tags = []
    for item in value:
        if isinstance(item, str) and item.strip():
            tags.append(item.strip())
        elif isinstance(item, dict):
            tag_text = _first_text(item, ("label", "name", "slug", "id"))
            if tag_text:
                tags.append(tag_text)
    return tags


def _category_or_tags(event, market):
    for value in (
        market.get("tags"),
        event.get("tags"),
        market.get("category"),
        event.get("category"),
    ):
        normalized = _normalize_tags_value(value)
        if normalized:
            return normalized
    return []


def _active_open(record):
    return record["active"] is True and record["closed"] is False


def _normalize_event_market(snapshot, source_path, event, event_index, market, market_index, warnings):
    record = {
        "source_snapshot_artifact_id": snapshot.get("artifact_id"),
        "source_snapshot_path": source_path,
        "source_name": snapshot["source"]["name"],
        "event_id": _first_text(event, ("id", "eventId", "event_id")),
        "event_slug": _first_text(event, ("slug",)),
        "event_title": _first_text(event, ("title", "question", "name")),
        "event_active": _coerce_bool(event.get("active")),
        "event_closed": _coerce_bool(event.get("closed")),
        "market_id": _first_text(market, ("id", "marketId", "market_id", "conditionId")),
        "question": _first_text(market, ("question", "title")),
        "market_slug": _first_text(market, ("slug",)),
        "category_or_tags": _category_or_tags(event, market),
        "active": _coerce_bool(market.get("active")),
        "closed": _coerce_bool(market.get("closed")),
        "accepting_orders": _coerce_bool(market.get("acceptingOrders", market.get("accepting_orders"))),
        "end_date": _first_text(market, ("endDate", "end_date", "endDateIso")),
        "start_date": _first_text(market, ("startDate", "start_date", "startDateIso")),
        "description": _first_text(market, ("description",)),
        "outcomes": _parse_json_list_field(market, ("outcomes",), event, event_index, market_index, warnings),
        "outcome_prices": _parse_json_list_field(
            market,
            ("outcomePrices", "outcome_prices"),
            event,
            event_index,
            market_index,
            warnings,
        ),
        "liquidity": _coerce_number(market.get("liquidity")),
        "volume": _coerce_number(market.get("volume", market.get("volumeNum"))),
        "condition_id": _first_text(market, ("conditionId", "condition_id")),
        "clob_token_ids": _parse_json_list_field(
            market,
            ("clobTokenIds", "clob_token_ids"),
            event,
            event_index,
            market_index,
            warnings,
        ),
        "enable_order_book": _coerce_bool(market.get("enableOrderBook", market.get("enable_order_book"))),
        "restricted": _coerce_bool(market.get("restricted")),
        "raw_market_updated_at": _first_text(market, ("updatedAt", "updated_at")),
    }
    return {field: record[field] for field in RECORD_FIELDS}


def _sorted_records(records):
    return sorted(
        records,
        key=lambda item: (
            item.get("event_id") or "",
            item.get("market_id") or "",
            item.get("question") or "",
        ),
    )


def _sorted_warnings(warnings):
    return sorted(
        warnings,
        key=lambda item: (
            item["event_index"],
            item["market_index"],
            item["field"],
            item["code"],
            item["message"],
        ),
    )


def build_normalized_preview(snapshot_path):
    snapshot_path = Path(snapshot_path)
    if snapshot_path.name.endswith(".validation.json"):
        raise NormalizationPreviewError(
            "validation_report_input_rejected",
            "Input must be a raw snapshot artifact, not a validation report.",
            {"source_snapshot_path": _display_file_path(snapshot_path)},
        )

    display_path = _display_file_path(snapshot_path)
    try:
        snapshot = _load_json(snapshot_path)
    except Exception as exc:
        raise NormalizationPreviewError(
            "snapshot_load_failed",
            f"{type(exc).__name__}: {exc}",
            {"source_snapshot_path": display_path},
        ) from exc

    findings = validate_snapshot(snapshot, display_path)
    if findings:
        raise NormalizationPreviewError(
            "invalid_raw_snapshot",
            "Raw snapshot validation failed.",
            {
                "finding_count": len(findings),
                "findings": findings,
                "source_snapshot_path": display_path,
            },
        )

    source_name = snapshot["source"]["name"]
    if source_name != EVENTS_SOURCE_NAME:
        raise NormalizationPreviewError(
            "unsupported_source_shape",
            "Only polymarket_gamma_events snapshots with nested markets are supported by this preview.",
            {
                "source_name": source_name,
                "source_snapshot_path": display_path,
                "supported_source_name": EVENTS_SOURCE_NAME,
            },
        )

    events = extract_event_records(snapshot["raw_payload"])
    records = []
    warnings = []
    nested_markets_seen = 0
    for event_index, event in enumerate(events):
        nested_markets = event.get("markets")
        if not isinstance(nested_markets, list):
            continue
        for market_index, market in enumerate(nested_markets):
            if not isinstance(market, dict):
                continue
            nested_markets_seen += 1
            records.append(
                _normalize_event_market(
                    snapshot,
                    display_path,
                    event,
                    event_index,
                    market,
                    market_index,
                    warnings,
                )
            )

    records = _sorted_records(records)
    warnings = _sorted_warnings(warnings)
    summary = {
        "source_snapshot_path": display_path,
        "source_name": source_name,
        "events_seen": len(events),
        "nested_markets_seen": nested_markets_seen,
        "normalized_records_written": len(records),
        "active_open_records": sum(1 for record in records if _active_open(record)),
        "closed_records": sum(1 for record in records if record["closed"] is True),
        "parse_warning_count": len(warnings),
    }
    return {
        "artifact_type": PREVIEW_ARTIFACT_TYPE,
        "parse_warnings": warnings,
        "records": records,
        "schema_version": PREVIEW_SCHEMA_VERSION,
        "summary": summary,
    }


def render_markdown_report(preview):
    summary = preview["summary"]
    lines = [
        "# Polymarket Raw Snapshot Normalization Preview",
        "",
        "Preview/export only. No downstream feed is enabled.",
        "",
        "## Summary",
        f"- source_snapshot_path: `{summary['source_snapshot_path']}`",
        f"- source_name: `{summary['source_name']}`",
        f"- events_seen: {summary['events_seen']}",
        f"- nested_markets_seen: {summary['nested_markets_seen']}",
        f"- normalized_records_written: {summary['normalized_records_written']}",
        f"- active_open_records: {summary['active_open_records']}",
        f"- closed_records: {summary['closed_records']}",
        f"- parse_warning_count: {summary['parse_warning_count']}",
        "",
        "## Parse Warnings",
    ]
    if preview["parse_warnings"]:
        for warning in preview["parse_warnings"]:
            lines.append(
                "- "
                f"{warning['code']} "
                f"event_index={warning['event_index']} "
                f"market_index={warning['market_index']} "
                f"field=`{warning['field']}` "
                f"market_id=`{warning['market_id']}`: "
                f"{warning['message']}"
            )
    else:
        lines.append("- none")
    lines.extend(
        [
            "",
            "## Safety",
            "- live_fetchers: false",
            "- network_api_calls: false",
            "- downstream_feed_enabled: false",
        ]
    )
    return "\n".join(lines) + "\n"


def write_preview_artifacts(snapshot_path, output_json=DEFAULT_OUTPUT_JSON, output_md=DEFAULT_OUTPUT_MD):
    preview = build_normalized_preview(snapshot_path)
    _write_json(Path(output_json), preview)
    _write_text(Path(output_md), render_markdown_report(preview))
    return preview


def _parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Build an offline normalized market preview from a validated Polymarket raw snapshot."
    )
    parser.add_argument("snapshot_path")
    parser.add_argument("--output-json", default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument("--output-md", default=str(DEFAULT_OUTPUT_MD))
    return parser.parse_args(argv)


def _error_payload(exc):
    return {
        "error": {
            "code": exc.code,
            "details": exc.details,
            "message": exc.message,
        },
        "schema_version": PREVIEW_SCHEMA_VERSION,
        "validation_passed": False,
    }


def main(argv):
    args = _parse_args(argv)
    try:
        preview = write_preview_artifacts(
            _resolve_path(args.snapshot_path),
            _resolve_path(args.output_json),
            _resolve_path(args.output_md),
        )
    except NormalizationPreviewError as exc:
        print(json.dumps(_error_payload(exc), indent=2, ensure_ascii=False, sort_keys=True))
        return 1

    result = {
        "output_json": _display_file_path(_resolve_path(args.output_json)),
        "output_md": _display_file_path(_resolve_path(args.output_md)),
        "summary": preview["summary"],
        "validation_passed": True,
    }
    print(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
