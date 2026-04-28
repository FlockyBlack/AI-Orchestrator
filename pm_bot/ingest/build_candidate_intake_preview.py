import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


PREVIEW_SCHEMA_VERSION = "candidate_intake_preview.v1"
PREVIEW_ARTIFACT_TYPE = "polymarket_candidate_intake_preview"
NORMALIZED_SCHEMA_VERSION = "normalized_market_preview.v1"
NORMALIZED_ARTIFACT_TYPE = "polymarket_normalized_market_preview"
DEFAULT_INPUT_JSON = ROOT / "pm_bot" / "ingest" / "normalized_market_preview.v1.json"
DEFAULT_OUTPUT_JSON = ROOT / "pm_bot" / "ingest" / "candidate_intake_preview.v1.json"
DEFAULT_OUTPUT_MD = ROOT / "pm_bot" / "ingest" / "candidate_intake_preview.v1.md"

BUCKETS = (
    "usable_for_research_preview",
    "missing_required_fields",
    "closed_or_not_accepting",
    "unsupported_or_malformed",
    "watch_only_structure",
)

NEXT_MANUAL_ACTIONS = {
    "usable_for_research_preview": "eligible_for_manual_research_packet_preview",
    "missing_required_fields": "fix_or_inspect_missing_fields",
    "closed_or_not_accepting": "skip_closed_or_not_accepting",
    "unsupported_or_malformed": "inspect_unsupported_structure",
    "watch_only_structure": "watch_only_manual",
}

ITEM_FIELDS = (
    "market_id",
    "question",
    "event_id",
    "event_title",
    "category_or_tags",
    "active",
    "closed",
    "accepting_orders",
    "end_date",
    "liquidity",
    "volume",
    "outcomes_count",
    "outcome_prices_count",
    "has_description",
    "bucket",
    "structural_findings",
    "next_manual_action",
)


class CandidateIntakePreviewError(Exception):
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


def _has_text(value):
    return isinstance(value, str) and bool(value.strip())


def _has_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _count_list(value):
    if isinstance(value, list):
        return len(value)
    return 0


def _has_description_or_resolution_text(record):
    return any(
        _has_text(record.get(key))
        for key in (
            "description",
            "resolution_criteria",
            "resolution_criteria_text",
        )
    )


def _empty_item(bucket, findings):
    item = {
        "market_id": None,
        "question": None,
        "event_id": None,
        "event_title": None,
        "category_or_tags": [],
        "active": None,
        "closed": None,
        "accepting_orders": None,
        "end_date": None,
        "liquidity": None,
        "volume": None,
        "outcomes_count": 0,
        "outcome_prices_count": 0,
        "has_description": False,
        "bucket": bucket,
        "structural_findings": findings,
        "next_manual_action": NEXT_MANUAL_ACTIONS[bucket],
    }
    return {field: item[field] for field in ITEM_FIELDS}


def _base_item(record):
    outcomes = record.get("outcomes")
    outcome_prices = record.get("outcome_prices")
    category_or_tags = record.get("category_or_tags")
    if not isinstance(category_or_tags, list):
        category_or_tags = []

    item = {
        "market_id": record.get("market_id"),
        "question": record.get("question"),
        "event_id": record.get("event_id"),
        "event_title": record.get("event_title"),
        "category_or_tags": category_or_tags,
        "active": record.get("active"),
        "closed": record.get("closed"),
        "accepting_orders": record.get("accepting_orders"),
        "end_date": record.get("end_date"),
        "liquidity": record.get("liquidity"),
        "volume": record.get("volume"),
        "outcomes_count": _count_list(outcomes),
        "outcome_prices_count": _count_list(outcome_prices),
        "has_description": _has_description_or_resolution_text(record),
        "bucket": None,
        "structural_findings": [],
        "next_manual_action": None,
    }
    return item


def _structural_findings(record):
    malformed = []
    closed_or_not_accepting = []
    missing = []

    for field in ("active", "closed"):
        value = record.get(field)
        if field not in record or value is None:
            missing.append(f"missing_{field}")
        elif not isinstance(value, bool):
            malformed.append(f"malformed_{field}")

    accepting_orders = record.get("accepting_orders")
    if accepting_orders is not None and not isinstance(accepting_orders, bool):
        malformed.append("malformed_accepting_orders")

    outcomes = record.get("outcomes")
    outcome_prices = record.get("outcome_prices")
    if not isinstance(outcomes, list):
        malformed.append("malformed_outcomes")
    elif len(outcomes) < 2:
        missing.append("outcomes_count_lt_2")

    if not isinstance(outcome_prices, list):
        malformed.append("malformed_outcome_prices")
    elif isinstance(outcomes, list) and len(outcome_prices) != len(outcomes):
        missing.append("outcome_prices_count_mismatch")

    if malformed:
        return malformed, closed_or_not_accepting, missing

    if record.get("active") is False:
        closed_or_not_accepting.append("inactive")
    if record.get("closed") is True:
        closed_or_not_accepting.append("closed")
    if accepting_orders is False:
        closed_or_not_accepting.append("not_accepting_orders")

    if not _has_text(record.get("market_id")):
        missing.append("missing_market_id")
    if not _has_text(record.get("question")):
        missing.append("missing_question")
    if not (_has_text(record.get("event_title")) or _has_text(record.get("event_id"))):
        missing.append("missing_event_title_or_event_id")
    if not _has_text(record.get("end_date")):
        missing.append("missing_end_date")
    if not (_has_number(record.get("liquidity")) or _has_number(record.get("volume"))):
        missing.append("missing_liquidity_or_volume")
    if not _has_description_or_resolution_text(record):
        missing.append("missing_description_or_resolution_criteria")

    return malformed, closed_or_not_accepting, missing


def classify_record(record):
    if not isinstance(record, dict):
        return _empty_item("unsupported_or_malformed", ["record_not_object"])

    item = _base_item(record)
    malformed, closed_or_not_accepting, missing = _structural_findings(record)
    if malformed:
        bucket = "unsupported_or_malformed"
        findings = malformed
    elif closed_or_not_accepting:
        bucket = "closed_or_not_accepting"
        findings = closed_or_not_accepting
    elif missing:
        bucket = "missing_required_fields"
        findings = missing
    elif item["accepting_orders"] is not True:
        bucket = "watch_only_structure"
        findings = ["accepting_orders_unknown"]
    else:
        bucket = "usable_for_research_preview"
        findings = []

    item["bucket"] = bucket
    item["structural_findings"] = findings
    item["next_manual_action"] = NEXT_MANUAL_ACTIONS[bucket]
    return {field: item[field] for field in ITEM_FIELDS}


def _sort_key(item):
    return (
        item.get("event_id") or "",
        item.get("market_id") or "",
        item.get("question") or "",
        item.get("bucket") or "",
    )


def _reject_unsupported_input(path, payload):
    if path.name.endswith(".validation.json"):
        raise CandidateIntakePreviewError(
            "validation_report_input_rejected",
            "Input must be a normalized market preview artifact, not a validation report.",
            {"input_path": _display_file_path(path)},
        )

    if not isinstance(payload, dict):
        raise CandidateIntakePreviewError(
            "unsupported_input_artifact",
            "Input must be a normalized market preview JSON object.",
            {"input_path": _display_file_path(path)},
        )

    artifact_type = payload.get("artifact_type")
    schema_version = payload.get("schema_version")
    if artifact_type == "polymarket_public_market_snapshot" or schema_version == "polymarket_readonly_raw_snapshot.v1":
        raise CandidateIntakePreviewError(
            "raw_snapshot_input_rejected",
            "Input must be a normalized market preview artifact, not a raw snapshot.",
            {"input_path": _display_file_path(path)},
        )

    if artifact_type != NORMALIZED_ARTIFACT_TYPE or schema_version != NORMALIZED_SCHEMA_VERSION:
        raise CandidateIntakePreviewError(
            "unsupported_input_artifact",
            "Input must be normalized_market_preview.v1 JSON.",
            {
                "artifact_type": artifact_type,
                "input_path": _display_file_path(path),
                "schema_version": schema_version,
            },
        )

    records = payload.get("records")
    if not isinstance(records, list):
        raise CandidateIntakePreviewError(
            "normalized_records_missing_or_malformed",
            "Normalized market preview must contain a records list.",
            {"input_path": _display_file_path(path)},
        )


def build_candidate_intake_preview_payload(normalized_preview, normalized_preview_path):
    path = Path(normalized_preview_path)
    _reject_unsupported_input(path, normalized_preview)
    records = normalized_preview["records"]

    buckets = {bucket: [] for bucket in BUCKETS}
    for record in records:
        item = classify_record(record)
        buckets[item["bucket"]].append(item)

    for bucket in BUCKETS:
        buckets[bucket] = sorted(buckets[bucket], key=_sort_key)

    summary = {"normalized_records_read": len(records)}
    for bucket in BUCKETS:
        summary[bucket] = len(buckets[bucket])

    return {
        "artifact_type": PREVIEW_ARTIFACT_TYPE,
        "buckets": buckets,
        "schema_version": PREVIEW_SCHEMA_VERSION,
        "source_normalized_preview_path": _display_file_path(path),
        "summary": summary,
    }


def build_candidate_intake_preview(normalized_preview_path=DEFAULT_INPUT_JSON):
    path = Path(normalized_preview_path)
    if path.name.endswith(".validation.json"):
        raise CandidateIntakePreviewError(
            "validation_report_input_rejected",
            "Input must be a normalized market preview artifact, not a validation report.",
            {"input_path": _display_file_path(path)},
        )
    try:
        normalized_preview = _load_json(path)
    except Exception as exc:
        raise CandidateIntakePreviewError(
            "input_load_failed",
            f"{type(exc).__name__}: {exc}",
            {"input_path": _display_file_path(path)},
        ) from exc
    return build_candidate_intake_preview_payload(normalized_preview, path)


def render_markdown_report(preview):
    summary = preview["summary"]
    lines = [
        "# Polymarket Candidate Intake Preview",
        "",
        "Offline structure-only preview. No downstream feed is enabled.",
        "",
        "## Summary",
        f"- source_normalized_preview_path: `{preview['source_normalized_preview_path']}`",
        f"- normalized_records_read: {summary['normalized_records_read']}",
        f"- usable_for_research_preview: {summary['usable_for_research_preview']}",
        f"- missing_required_fields: {summary['missing_required_fields']}",
        f"- closed_or_not_accepting: {summary['closed_or_not_accepting']}",
        f"- unsupported_or_malformed: {summary['unsupported_or_malformed']}",
        f"- watch_only_structure: {summary['watch_only_structure']}",
        "",
        "## Buckets",
    ]
    for bucket in BUCKETS:
        lines.append(f"- {bucket}: {summary[bucket]}")
    lines.extend(
        [
            "",
            "## Output Boundary",
            "- research_packets_created: false",
            "- downstream_feed_enabled: false",
            "- live_fetchers: false",
            "- network_api_calls: false",
        ]
    )
    return "\n".join(lines) + "\n"


def write_preview_artifacts(
    normalized_preview_path=DEFAULT_INPUT_JSON,
    output_json=DEFAULT_OUTPUT_JSON,
    output_md=DEFAULT_OUTPUT_MD,
):
    preview = build_candidate_intake_preview(normalized_preview_path)
    _write_json(Path(output_json), preview)
    _write_text(Path(output_md), render_markdown_report(preview))
    return preview


def _parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Build an offline candidate-intake preview from normalized Polymarket market records."
    )
    parser.add_argument("normalized_preview_path", nargs="?", default=str(DEFAULT_INPUT_JSON))
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
        "input_accepted": False,
    }


def main(argv):
    args = _parse_args(argv)
    try:
        preview = write_preview_artifacts(
            _resolve_path(args.normalized_preview_path),
            _resolve_path(args.output_json),
            _resolve_path(args.output_md),
        )
    except CandidateIntakePreviewError as exc:
        print(json.dumps(_error_payload(exc), indent=2, ensure_ascii=False, sort_keys=True))
        return 1

    result = {
        "input_accepted": True,
        "output_json": _display_file_path(_resolve_path(args.output_json)),
        "output_md": _display_file_path(_resolve_path(args.output_md)),
        "summary": preview["summary"],
    }
    print(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
