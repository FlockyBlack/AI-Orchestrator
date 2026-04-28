import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

SELECTION_INDEX_SCHEMA_VERSION = "operator_candidate_selection_index.v1"
SELECTION_INDEX_ARTIFACT_TYPE = "polymarket_operator_candidate_selection_index"
OVERLAY_SCHEMA_VERSION = "operator_candidate_selection_overlay.v1"
OVERLAY_ARTIFACT_TYPE = "polymarket_operator_candidate_selection_overlay"
CANDIDATE_PREVIEW_SCHEMA_VERSION = "candidate_intake_preview.v1"
CANDIDATE_PREVIEW_ARTIFACT_TYPE = "polymarket_candidate_intake_preview"
DEFAULT_INPUT_JSON = ROOT / "pm_bot" / "ingest" / "candidate_intake_preview.v1.json"
DEFAULT_OUTPUT_MD = ROOT / "pm_bot" / "ingest" / "operator_candidate_selection_pack.v1.md"
DEFAULT_OUTPUT_INDEX_JSON = ROOT / "pm_bot" / "ingest" / "operator_candidate_selection_index.v1.json"
DEFAULT_OUTPUT_OVERLAY_JSON = ROOT / "pm_bot" / "ingest" / "operator_candidate_selection_overlay_template.v1.json"

USABLE_BUCKET = "usable_for_research_preview"
RESEARCH_PACKETS_CREATED = 0
SELECTION_FIELDS = (
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
OVERLAY_SELECTION_FIELDS = (
    "market_id",
    "selected_for_research_stub",
    "operator_reason",
    "operator_priority",
    "operator_notes",
)
ALLOWED_OPERATOR_PRIORITIES = ("", "low", "medium", "high")
PROHIBITED_OVERLAY_FIELDS = {
    "bet",
    "execution",
    "expected_value",
    "market_decision",
    "order",
    "probability",
    "recommendation",
    "score",
    "side",
    "signal",
    "stake",
    "trade",
}


class OperatorSelectionPackError(Exception):
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


def _reject_unsupported_input(path, payload):
    if not isinstance(payload, dict):
        raise OperatorSelectionPackError(
            "unsupported_input_artifact",
            "Input must be a candidate-intake preview JSON object.",
            {"input_path": _display_file_path(path)},
        )
    artifact_type = payload.get("artifact_type")
    schema_version = payload.get("schema_version")
    if artifact_type != CANDIDATE_PREVIEW_ARTIFACT_TYPE or schema_version != CANDIDATE_PREVIEW_SCHEMA_VERSION:
        raise OperatorSelectionPackError(
            "unsupported_input_artifact",
            "Input must be candidate_intake_preview.v1 JSON.",
            {
                "artifact_type": artifact_type,
                "input_path": _display_file_path(path),
                "schema_version": schema_version,
            },
        )
    buckets = payload.get("buckets")
    if not isinstance(buckets, dict):
        raise OperatorSelectionPackError(
            "candidate_buckets_missing_or_malformed",
            "Candidate-intake preview must contain a buckets object.",
            {"input_path": _display_file_path(path)},
        )
    usable = buckets.get(USABLE_BUCKET)
    if not isinstance(usable, list):
        raise OperatorSelectionPackError(
            "usable_bucket_missing_or_malformed",
            "Candidate-intake preview must contain a usable_for_research_preview list.",
            {"input_path": _display_file_path(path)},
        )


def _candidate_item(candidate):
    if not isinstance(candidate, dict):
        raise OperatorSelectionPackError(
            "usable_candidate_malformed",
            "Every usable candidate must be a JSON object.",
        )
    item = {field: candidate.get(field) for field in SELECTION_FIELDS}
    item["bucket"] = USABLE_BUCKET
    return item


def _overlay_selection_item(candidate):
    return {
        "market_id": candidate.get("market_id"),
        "selected_for_research_stub": False,
        "operator_reason": "",
        "operator_priority": "",
        "operator_notes": "",
    }


def build_selection_index_payload(candidate_preview, candidate_preview_path):
    path = Path(candidate_preview_path)
    _reject_unsupported_input(path, candidate_preview)
    usable_candidates = candidate_preview["buckets"][USABLE_BUCKET]
    candidates = [_candidate_item(candidate) for candidate in usable_candidates]
    summary = {
        "candidates_exported": len(candidates),
        "research_packets_created": RESEARCH_PACKETS_CREATED,
        "selection_overlay_template_created": True,
        "usable_candidates_seen": len(usable_candidates),
    }
    return {
        "artifact_type": SELECTION_INDEX_ARTIFACT_TYPE,
        "candidates": candidates,
        "schema_version": SELECTION_INDEX_SCHEMA_VERSION,
        "source_candidate_intake_preview_path": _display_file_path(path),
        "summary": summary,
    }


def build_selection_index(candidate_preview_path=DEFAULT_INPUT_JSON):
    path = Path(candidate_preview_path)
    try:
        candidate_preview = _load_json(path)
    except Exception as exc:
        raise OperatorSelectionPackError(
            "input_load_failed",
            f"{type(exc).__name__}: {exc}",
            {"input_path": _display_file_path(path)},
        ) from exc
    return build_selection_index_payload(candidate_preview, path)


def build_overlay_template(index_payload, index_path=DEFAULT_OUTPUT_INDEX_JSON):
    selections = [_overlay_selection_item(candidate) for candidate in index_payload["candidates"]]
    return {
        "artifact_type": OVERLAY_ARTIFACT_TYPE,
        "schema_version": OVERLAY_SCHEMA_VERSION,
        "selections": selections,
        "source_selection_index_path": _display_file_path(index_path),
    }


def _format_value(value):
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, list):
        return ", ".join(str(item) for item in value)
    return str(value)


def render_markdown_pack(index_payload):
    summary = index_payload["summary"]
    lines = [
        "# Polymarket Operator Candidate Selection Pack",
        "",
        "Offline operator selection pack from candidate-intake preview.",
        "",
        "## Summary",
        f"- source_candidate_intake_preview_path: `{index_payload['source_candidate_intake_preview_path']}`",
        f"- usable_candidates_seen: {summary['usable_candidates_seen']}",
        f"- candidates_exported: {summary['candidates_exported']}",
        f"- selection_overlay_template_created: {str(summary['selection_overlay_template_created']).lower()}",
        f"- research_packets_created: {summary['research_packets_created']}",
        "",
        "## Output Boundary",
        "- live_fetchers: false",
        "- network_api_calls: false",
        "- downstream_feed_enabled: false",
        "- research_packets_created: 0",
        "",
        "## Candidates",
    ]
    for candidate in index_payload["candidates"]:
        lines.extend(
            [
                "",
                f"### market_id: `{_format_value(candidate['market_id'])}`",
                f"- question: {_format_value(candidate['question'])}",
                f"- event_id: `{_format_value(candidate['event_id'])}`",
                f"- event_title: {_format_value(candidate['event_title'])}",
                f"- category_or_tags: {_format_value(candidate['category_or_tags'])}",
                f"- active: {_format_value(candidate['active'])}",
                f"- closed: {_format_value(candidate['closed'])}",
                f"- accepting_orders: {_format_value(candidate['accepting_orders'])}",
                f"- end_date: {_format_value(candidate['end_date'])}",
                f"- liquidity: {_format_value(candidate['liquidity'])}",
                f"- volume: {_format_value(candidate['volume'])}",
                f"- outcomes_count: {_format_value(candidate['outcomes_count'])}",
                f"- outcome_prices_count: {_format_value(candidate['outcome_prices_count'])}",
                f"- has_description: {_format_value(candidate['has_description'])}",
                f"- bucket: `{_format_value(candidate['bucket'])}`",
                f"- structural_findings: {_format_value(candidate['structural_findings'])}",
                f"- next_manual_action: `{_format_value(candidate['next_manual_action'])}`",
            ]
        )
    return "\n".join(lines) + "\n"


def _iter_overlay_keys(payload):
    if isinstance(payload, dict):
        for key, value in payload.items():
            yield str(key)
            yield from _iter_overlay_keys(value)
    elif isinstance(payload, list):
        for item in payload:
            yield from _iter_overlay_keys(item)


def _market_ids_from_index(index_payload):
    return {candidate.get("market_id") for candidate in index_payload.get("candidates", [])}


def validate_overlay_payload(overlay_payload, index_payload):
    if not isinstance(overlay_payload, dict):
        raise OperatorSelectionPackError(
            "overlay_malformed",
            "Selection overlay must be a JSON object.",
        )
    if overlay_payload.get("artifact_type") != OVERLAY_ARTIFACT_TYPE:
        raise OperatorSelectionPackError(
            "overlay_artifact_type_invalid",
            "Selection overlay artifact type is invalid.",
            {"artifact_type": overlay_payload.get("artifact_type")},
        )
    if overlay_payload.get("schema_version") != OVERLAY_SCHEMA_VERSION:
        raise OperatorSelectionPackError(
            "overlay_schema_version_invalid",
            "Selection overlay schema version is invalid.",
            {"schema_version": overlay_payload.get("schema_version")},
        )

    prohibited = sorted(
        key
        for key in _iter_overlay_keys(overlay_payload)
        if key.lower() in PROHIBITED_OVERLAY_FIELDS
    )
    if prohibited:
        raise OperatorSelectionPackError(
            "overlay_prohibited_fields",
            "Selection overlay contains prohibited fields.",
            {"fields": prohibited},
        )

    selections = overlay_payload.get("selections")
    if not isinstance(selections, list):
        raise OperatorSelectionPackError(
            "overlay_selections_malformed",
            "Selection overlay must contain a selections list.",
        )

    valid_market_ids = _market_ids_from_index(index_payload)
    for selection in selections:
        if not isinstance(selection, dict):
            raise OperatorSelectionPackError(
                "overlay_selection_malformed",
                "Every selection overlay item must be a JSON object.",
            )
        fields = set(selection.keys())
        expected_fields = set(OVERLAY_SELECTION_FIELDS)
        if fields != expected_fields:
            raise OperatorSelectionPackError(
                "overlay_selection_fields_invalid",
                "Selection overlay item fields are invalid.",
                {
                    "extra_fields": sorted(fields - expected_fields),
                    "missing_fields": sorted(expected_fields - fields),
                },
            )

        market_id = selection.get("market_id")
        if market_id not in valid_market_ids:
            raise OperatorSelectionPackError(
                "overlay_market_id_unknown",
                "Selection overlay market_id is not present in usable candidates.",
                {"market_id": market_id},
            )

        selected = selection.get("selected_for_research_stub")
        if not isinstance(selected, bool):
            raise OperatorSelectionPackError(
                "overlay_selected_flag_invalid",
                "selected_for_research_stub must be true or false.",
                {"market_id": market_id},
            )

        priority = selection.get("operator_priority")
        if priority not in ALLOWED_OPERATOR_PRIORITIES:
            raise OperatorSelectionPackError(
                "overlay_priority_invalid",
                "operator_priority must be blank, low, medium, or high.",
                {"market_id": market_id, "operator_priority": priority},
            )

        reason = selection.get("operator_reason")
        if selected and not (isinstance(reason, str) and reason.strip()):
            raise OperatorSelectionPackError(
                "overlay_selected_reason_required",
                "operator_reason is required when selected_for_research_stub is true.",
                {"market_id": market_id},
            )

        notes = selection.get("operator_notes")
        if not isinstance(reason, str) or not isinstance(notes, str):
            raise OperatorSelectionPackError(
                "overlay_text_fields_invalid",
                "operator_reason and operator_notes must be strings.",
                {"market_id": market_id},
            )
    return {
        "overlay_valid": True,
        "selections_checked": len(selections),
    }


def validate_overlay_file(overlay_path, index_path=DEFAULT_OUTPUT_INDEX_JSON):
    try:
        overlay_payload = _load_json(Path(overlay_path))
        index_payload = _load_json(Path(index_path))
    except Exception as exc:
        raise OperatorSelectionPackError(
            "validation_load_failed",
            f"{type(exc).__name__}: {exc}",
        ) from exc
    return validate_overlay_payload(overlay_payload, index_payload)


def write_selection_pack_artifacts(
    candidate_preview_path=DEFAULT_INPUT_JSON,
    output_md=DEFAULT_OUTPUT_MD,
    output_index_json=DEFAULT_OUTPUT_INDEX_JSON,
    output_overlay_json=DEFAULT_OUTPUT_OVERLAY_JSON,
):
    index_payload = build_selection_index(candidate_preview_path)
    overlay_payload = build_overlay_template(index_payload, output_index_json)
    _write_json(Path(output_index_json), index_payload)
    _write_json(Path(output_overlay_json), overlay_payload)
    _write_text(Path(output_md), render_markdown_pack(index_payload))
    return {
        "index": index_payload,
        "overlay": overlay_payload,
    }


def _parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Export an offline operator candidate selection pack from candidate-intake preview."
    )
    parser.add_argument("candidate_preview_path", nargs="?", default=str(DEFAULT_INPUT_JSON))
    parser.add_argument("--output-md", default=str(DEFAULT_OUTPUT_MD))
    parser.add_argument("--output-index-json", default=str(DEFAULT_OUTPUT_INDEX_JSON))
    parser.add_argument("--output-overlay-json", default=str(DEFAULT_OUTPUT_OVERLAY_JSON))
    parser.add_argument("--validate-overlay")
    parser.add_argument("--validate-index-json", default=str(DEFAULT_OUTPUT_INDEX_JSON))
    return parser.parse_args(argv)


def _error_payload(exc):
    return {
        "error": {
            "code": exc.code,
            "details": exc.details,
            "message": exc.message,
        },
        "input_accepted": False,
        "schema_version": SELECTION_INDEX_SCHEMA_VERSION,
    }


def main(argv):
    args = _parse_args(argv)
    try:
        if args.validate_overlay:
            validation = validate_overlay_file(
                _resolve_path(args.validate_overlay),
                _resolve_path(args.validate_index_json),
            )
            print(json.dumps(validation, indent=2, ensure_ascii=False, sort_keys=True))
            return 0

        artifacts = write_selection_pack_artifacts(
            _resolve_path(args.candidate_preview_path),
            _resolve_path(args.output_md),
            _resolve_path(args.output_index_json),
            _resolve_path(args.output_overlay_json),
        )
    except OperatorSelectionPackError as exc:
        print(json.dumps(_error_payload(exc), indent=2, ensure_ascii=False, sort_keys=True))
        return 1

    result = {
        "input_accepted": True,
        "output_index_json": _display_file_path(_resolve_path(args.output_index_json)),
        "output_md": _display_file_path(_resolve_path(args.output_md)),
        "output_overlay_json": _display_file_path(_resolve_path(args.output_overlay_json)),
        "summary": artifacts["index"]["summary"],
    }
    print(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
