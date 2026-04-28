import argparse
import json
import sys
from pathlib import Path


TASK_ID = "PMBOT-INGEST-005-SELECTED-CANDIDATE-RESEARCH-STUB-BRIDGE"
SCHEMA_VERSION = "selected_ingest_research_packet_stubs.v1"
ARTIFACT_TYPE = "polymarket_selected_ingest_research_packet_stubs"
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pm_bot.ingest.export_operator_candidate_selection_pack import (
    OperatorSelectionPackError,
    validate_overlay_payload,
)

DEFAULT_SELECTION_INDEX = ROOT / "pm_bot" / "ingest" / "operator_candidate_selection_index.v1.json"
DEFAULT_SELECTION_OVERLAY = ROOT / "pm_bot" / "ingest" / "operator_candidate_selection_overlay_selected_first5.v1.json"
DEFAULT_NORMALIZED_PREVIEW = ROOT / "pm_bot" / "ingest" / "normalized_market_preview.v1.json"
DEFAULT_OUTPUT_JSON = ROOT / "pm_bot" / "research" / "selected_ingest_research_packet_stubs.v1.json"
DEFAULT_OUTPUT_MD = ROOT / "pm_bot" / "research" / "selected_ingest_research_packet_stubs.v1.md"
DEFAULT_EXPECTED_JSON = ROOT / "pm_bot" / "research" / "expected_selected_ingest_research_packet_stubs.v1.json"

SELECTION_INDEX_SCHEMA_VERSION = "operator_candidate_selection_index.v1"
SELECTION_INDEX_ARTIFACT_TYPE = "polymarket_operator_candidate_selection_index"
NORMALIZED_PREVIEW_SCHEMA_VERSION = "normalized_market_preview.v1"
NORMALIZED_PREVIEW_ARTIFACT_TYPE = "polymarket_normalized_market_preview"

EVIDENCE_SLOT_NAMES = (
    "official_resolution_criteria",
    "official_yes_evidence",
    "official_no_evidence",
    "credible_news_yes_evidence",
    "credible_news_no_evidence",
    "uncertainty_factors",
    "source_reliability_notes",
)


class SelectedIngestResearchStubError(Exception):
    def __init__(self, code, message, details=None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details or {}


def _resolve_path(path):
    value = Path(path)
    if value.is_absolute():
        return value
    return ROOT / value


def _display_path(path):
    resolved = Path(path).resolve()
    try:
        return str(resolved.relative_to(ROOT.resolve())).replace("\\", "/")
    except ValueError:
        return str(resolved).replace("\\", "/")


def _load_json(path):
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _write_json(path, payload):
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _write_text(path, text):
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(text, encoding="utf-8")


def _text(value):
    if value is None:
        return ""
    return str(value).strip()


def _number_or_none(value):
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _require_artifact(payload, artifact_type, schema_version, artifact_name):
    if not isinstance(payload, dict):
        raise SelectedIngestResearchStubError(
            f"{artifact_name}_malformed",
            f"{artifact_name} must be a JSON object.",
        )
    if payload.get("artifact_type") != artifact_type:
        raise SelectedIngestResearchStubError(
            f"{artifact_name}_artifact_type_invalid",
            f"{artifact_name} artifact type is invalid.",
            {"artifact_type": payload.get("artifact_type")},
        )
    if payload.get("schema_version") != schema_version:
        raise SelectedIngestResearchStubError(
            f"{artifact_name}_schema_version_invalid",
            f"{artifact_name} schema version is invalid.",
            {"schema_version": payload.get("schema_version")},
        )


def _records_by_market_id(records, artifact_name):
    if not isinstance(records, list):
        raise SelectedIngestResearchStubError(
            f"{artifact_name}_records_malformed",
            f"{artifact_name} records must be a list.",
        )
    by_market_id = {}
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            raise SelectedIngestResearchStubError(
                f"{artifact_name}_record_malformed",
                f"{artifact_name} record must be an object.",
                {"index": index},
            )
        market_id = record.get("market_id")
        if not isinstance(market_id, str) or not market_id.strip():
            raise SelectedIngestResearchStubError(
                f"{artifact_name}_market_id_missing",
                f"{artifact_name} record market_id must be a non-empty string.",
                {"index": index},
            )
        if market_id in by_market_id:
            raise SelectedIngestResearchStubError(
                f"{artifact_name}_market_id_duplicate",
                f"{artifact_name} contains duplicate market_id values.",
                {"market_id": market_id},
            )
        by_market_id[market_id] = record
    return by_market_id


def _selected_overlay_rows(overlay_payload):
    selections = overlay_payload.get("selections")
    selected = [row for row in selections if row.get("selected_for_research_stub") is True]
    seen = set()
    for row in selected:
        market_id = row["market_id"]
        if market_id in seen:
            raise SelectedIngestResearchStubError(
                "selected_market_id_duplicate",
                "Selected overlay contains duplicate selected market_id values.",
                {"market_id": market_id},
            )
        seen.add(market_id)
    return selected


def _category_text(record):
    category = record.get("category_or_tags")
    if isinstance(category, list):
        return " / ".join(str(item) for item in category)
    return _text(category)


def _first_description_paragraph(record):
    description = _text(record.get("description"))
    if not description:
        return ""
    paragraphs = [line.strip() for line in description.splitlines() if line.strip()]
    return paragraphs[0] if paragraphs else ""


def _current_yes_price(record):
    outcomes = record.get("outcomes")
    prices = record.get("outcome_prices")
    if not isinstance(outcomes, list) or not isinstance(prices, list):
        return None, "current_yes_price_unavailable_or_ambiguous"
    if len(outcomes) != len(prices):
        return None, "current_yes_price_unavailable_or_ambiguous"
    yes_indexes = [index for index, outcome in enumerate(outcomes) if _text(outcome).casefold() == "yes"]
    if len(yes_indexes) != 1:
        return None, "current_yes_price_unavailable_or_ambiguous"
    parsed = _number_or_none(prices[yes_indexes[0]])
    if parsed is None:
        return None, "current_yes_price_unavailable_or_ambiguous"
    return parsed, None


def _evidence_slots():
    return {slot: [] for slot in EVIDENCE_SLOT_NAMES}


def _missing_information(record, yes_price_missing_reason):
    missing = [
        "manual_research_not_started",
        "full_market_resolution_criteria_review",
        "official_source_references",
        "credible_news_source_references",
        "empty_evidence_slots",
        "operator_human_review_required",
    ]
    if not _text(record.get("description")):
        missing.append("local_market_description_missing")
    if yes_price_missing_reason:
        missing.append(yes_price_missing_reason)
    return missing


def _resolution_criteria_summary(record):
    title = _text(record.get("question")) or _text(record.get("event_title")) or _text(record.get("market_id"))
    first_paragraph = _first_description_paragraph(record)
    if first_paragraph:
        return (
            f"Stub-only local market description excerpt for '{title}': {first_paragraph} "
            "Manual completion must review the full local criteria before use."
        )
    return (
        f"Stub-only summary placeholder for '{title}': local description text is unavailable; "
        "manual completion must add criteria from approved local or manually checked sources."
    )


def _source_plan(record):
    title = _text(record.get("question")) or _text(record.get("event_title")) or _text(record.get("market_id"))
    return (
        f"Template only: review the local market rules for '{title}', then manually check official primary sources "
        "and credible news coverage. This stub does not fetch or verify sources."
    )


def _search_queries(record):
    title = _text(record.get("question")) or _text(record.get("event_title")) or _text(record.get("market_id"))
    event_title = _text(record.get("event_title"))
    deadline = _text(record.get("end_date"))
    market_id = _text(record.get("market_id"))
    category = _category_text(record)
    return [
        f'Template only: "{title}" "resolution criteria"',
        f'Template only: "{title}" "{deadline}" official source',
        f'Template only: "Polymarket" "{market_id}" "{title}"',
        f'Template only: "{event_title}" "{title}" credible reporting',
        f'Template only: "{category}" "{title}" primary source',
    ]


def _official_sources_to_check(record):
    title = _text(record.get("question")) or _text(record.get("event_title")) or _text(record.get("market_id"))
    market_id = _text(record.get("market_id"))
    return [
        f"Manual check template: local Polymarket rules and resolution criteria for market_id {market_id}",
        f"Manual check template: official primary source named in the local market description for '{title}'",
        f"Manual check template: original issuer, government, court, exchange, or company source relevant to '{title}'",
    ]


def _credible_news_sources_to_check(record):
    title = _text(record.get("question")) or _text(record.get("event_title")) or _text(record.get("market_id"))
    category = _category_text(record)
    return [
        f"Manual check template: Reuters coverage query for '{title}'",
        f"Manual check template: Associated Press coverage query for '{title}'",
        f"Manual check template: major credible outlet query for '{category}' and '{title}'",
    ]


def _why_selected_for_research(selection):
    notes = _text(selection.get("operator_notes"))
    priority = _text(selection.get("operator_priority")) or "unspecified"
    if notes:
        return (
            "Selected by validated operator overlay for deterministic first-five research-stub bridge testing; "
            f"operator_priority={priority}; operator_notes={notes}"
        )
    return (
        "Selected by validated operator overlay for deterministic first-five research-stub bridge testing; "
        f"operator_priority={priority}."
    )


def _packet_stub(selection, index_candidate, normalized_record, source_paths):
    yes_price, yes_price_missing_reason = _current_yes_price(normalized_record)
    title = _text(normalized_record.get("question")) or _text(index_candidate.get("question"))
    deadline = normalized_record.get("end_date")
    return {
        "market_id": _text(normalized_record.get("market_id")),
        "title": title,
        "question": title,
        "event_id": _text(normalized_record.get("event_id")),
        "event_title": _text(normalized_record.get("event_title")),
        "category": _category_text(normalized_record),
        "packet_type": "selected_ingest_market_research_stub",
        "current_yes_price": yes_price,
        "liquidity": _number_or_none(normalized_record.get("liquidity")),
        "volume": _number_or_none(normalized_record.get("volume")),
        "deadline": deadline,
        "resolution_criteria_summary": _resolution_criteria_summary(normalized_record),
        "why_selected_for_research": _why_selected_for_research(selection),
        "why_not_bet_yet": "Stub only: no source evidence has been gathered, evidence slots are empty, and manual review has not happened.",
        "source_plan": _source_plan(normalized_record),
        "search_queries": _search_queries(normalized_record),
        "official_sources_to_check": _official_sources_to_check(normalized_record),
        "credible_news_sources_to_check": _credible_news_sources_to_check(normalized_record),
        "evidence_slots": _evidence_slots(),
        "missing_information": _missing_information(normalized_record, yes_price_missing_reason),
        "completion_status": "stub_only",
        "source_ingest_artifacts": {
            "operator_candidate_selection_index": source_paths["selection_index"],
            "operator_candidate_selection_overlay": source_paths["selection_overlay"],
            "normalized_market_preview": source_paths["normalized_preview"],
            "normalized_source_snapshot_artifact_id": normalized_record.get("source_snapshot_artifact_id"),
            "normalized_source_snapshot_path": normalized_record.get("source_snapshot_path"),
        },
    }


def build_selected_ingest_research_packet_stubs_payload(
    index_payload,
    overlay_payload,
    normalized_preview_payload,
    index_path=DEFAULT_SELECTION_INDEX,
    overlay_path=DEFAULT_SELECTION_OVERLAY,
    normalized_preview_path=DEFAULT_NORMALIZED_PREVIEW,
):
    _require_artifact(
        index_payload,
        SELECTION_INDEX_ARTIFACT_TYPE,
        SELECTION_INDEX_SCHEMA_VERSION,
        "selection_index",
    )
    _require_artifact(
        normalized_preview_payload,
        NORMALIZED_PREVIEW_ARTIFACT_TYPE,
        NORMALIZED_PREVIEW_SCHEMA_VERSION,
        "normalized_preview",
    )
    overlay_validation = validate_overlay_payload(overlay_payload, index_payload)

    index_by_market_id = _records_by_market_id(index_payload.get("candidates"), "selection_index")
    normalized_by_market_id = _records_by_market_id(normalized_preview_payload.get("records"), "normalized_preview")
    selected_rows = _selected_overlay_rows(overlay_payload)
    source_paths = {
        "selection_index": _display_path(index_path),
        "selection_overlay": _display_path(overlay_path),
        "normalized_preview": _display_path(normalized_preview_path),
    }

    packet_stubs = []
    for selection in selected_rows:
        market_id = selection["market_id"]
        if market_id not in index_by_market_id:
            raise SelectedIngestResearchStubError(
                "selected_market_id_missing_from_selection_index",
                "Selected market_id is missing from the selection index.",
                {"market_id": market_id},
            )
        if market_id not in normalized_by_market_id:
            raise SelectedIngestResearchStubError(
                "selected_market_id_missing_from_normalized_preview",
                "Selected market_id is missing from the normalized market preview.",
                {"market_id": market_id},
            )
        packet_stubs.append(
            _packet_stub(
                selection,
                index_by_market_id[market_id],
                normalized_by_market_id[market_id],
                source_paths,
            )
        )

    selected_market_ids = [stub["market_id"] for stub in packet_stubs]
    return {
        "artifact_type": ARTIFACT_TYPE,
        "schema_version": SCHEMA_VERSION,
        "task_id": TASK_ID,
        "deterministic": True,
        "selection_source": "validated_operator_selection_overlay",
        "source_ingest_artifacts": source_paths,
        "overlay_validation": overlay_validation,
        "summary": {
            "selected_market_ids_read": len(selected_market_ids),
            "research_packet_stubs_created": len(packet_stubs),
            "completion_status_all_stub_only": all(
                stub["completion_status"] == "stub_only" for stub in packet_stubs
            ),
        },
        "selected_market_ids": selected_market_ids,
        "packet_stubs": packet_stubs,
        "bridge_boundary": {
            "offline_only": True,
            "manual_invocation_only": True,
            "stub_only": True,
            "external_fetch_performed": False,
            "downstream_wiring_changed": False,
        },
        "limitations": [
            "Reads only saved local PMBOT ingest artifacts.",
            "Creates empty research packet stubs only.",
            "Does not fetch, verify, conclude, or trigger downstream actions.",
        ],
    }


def build_selected_ingest_research_packet_stubs(
    index_path=DEFAULT_SELECTION_INDEX,
    overlay_path=DEFAULT_SELECTION_OVERLAY,
    normalized_preview_path=DEFAULT_NORMALIZED_PREVIEW,
):
    index_path = _resolve_path(index_path)
    overlay_path = _resolve_path(overlay_path)
    normalized_preview_path = _resolve_path(normalized_preview_path)
    return build_selected_ingest_research_packet_stubs_payload(
        _load_json(index_path),
        _load_json(overlay_path),
        _load_json(normalized_preview_path),
        index_path=index_path,
        overlay_path=overlay_path,
        normalized_preview_path=normalized_preview_path,
    )


def _format_value(value):
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, list):
        return ", ".join(str(item) for item in value)
    return str(value)


def render_markdown_report(payload):
    summary = payload["summary"]
    lines = [
        "# Selected Ingest Research Packet Stubs",
        "",
        "Deterministic offline bridge from validated ingest-selected candidates to empty research packet stubs.",
        "",
        "## Summary",
        f"- selected_market_ids_read: {summary['selected_market_ids_read']}",
        f"- research_packet_stubs_created: {summary['research_packet_stubs_created']}",
        f"- completion_status_all_stub_only: {str(summary['completion_status_all_stub_only']).lower()}",
        "",
        "## Source Artifacts",
        f"- selection_index: `{payload['source_ingest_artifacts']['selection_index']}`",
        f"- selection_overlay: `{payload['source_ingest_artifacts']['selection_overlay']}`",
        f"- normalized_preview: `{payload['source_ingest_artifacts']['normalized_preview']}`",
        "",
        "## Safety Boundary",
        "- offline_only: true",
        "- manual_invocation_only: true",
        "- stub_only: true",
        "- external_fetch_performed: false",
        "- downstream_wiring_changed: false",
        "",
        "## Selected Market IDs",
    ]
    lines.extend(f"- `{market_id}`" for market_id in payload["selected_market_ids"])
    lines.extend(["", "## Packet Stubs"])
    for stub in payload["packet_stubs"]:
        lines.extend(
            [
                "",
                f"### market_id: `{stub['market_id']}`",
                f"- title: {_format_value(stub['title'])}",
                f"- event_id: `{_format_value(stub['event_id'])}`",
                f"- event_title: {_format_value(stub['event_title'])}",
                f"- category: {_format_value(stub['category'])}",
                f"- packet_type: `{_format_value(stub['packet_type'])}`",
                f"- current_yes_price: {_format_value(stub['current_yes_price'])}",
                f"- liquidity: {_format_value(stub['liquidity'])}",
                f"- volume: {_format_value(stub['volume'])}",
                f"- deadline: {_format_value(stub['deadline'])}",
                f"- completion_status: `{_format_value(stub['completion_status'])}`",
                f"- missing_information_count: {len(stub['missing_information'])}",
            ]
        )
    return "\n".join(lines) + "\n"


def write_selected_ingest_research_packet_stub_artifacts(
    index_path=DEFAULT_SELECTION_INDEX,
    overlay_path=DEFAULT_SELECTION_OVERLAY,
    normalized_preview_path=DEFAULT_NORMALIZED_PREVIEW,
    output_json=DEFAULT_OUTPUT_JSON,
    output_md=DEFAULT_OUTPUT_MD,
    expected_json=DEFAULT_EXPECTED_JSON,
):
    payload = build_selected_ingest_research_packet_stubs(
        index_path=index_path,
        overlay_path=overlay_path,
        normalized_preview_path=normalized_preview_path,
    )
    _write_json(_resolve_path(output_json), payload)
    _write_text(_resolve_path(output_md), render_markdown_report(payload))
    if expected_json:
        _write_json(_resolve_path(expected_json), payload)
    return payload


def _parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Build deterministic offline research packet stubs from selected local ingest candidates."
    )
    parser.add_argument("--selection-index", default=str(DEFAULT_SELECTION_INDEX.relative_to(ROOT)))
    parser.add_argument("--selection-overlay", default=str(DEFAULT_SELECTION_OVERLAY.relative_to(ROOT)))
    parser.add_argument("--normalized-preview", default=str(DEFAULT_NORMALIZED_PREVIEW.relative_to(ROOT)))
    parser.add_argument("--output-json", default=str(DEFAULT_OUTPUT_JSON.relative_to(ROOT)))
    parser.add_argument("--output-md", default=str(DEFAULT_OUTPUT_MD.relative_to(ROOT)))
    parser.add_argument("--expected-json", default=str(DEFAULT_EXPECTED_JSON.relative_to(ROOT)))
    return parser.parse_args(argv)


def _error_payload(exc):
    return {
        "input_accepted": False,
        "error": {
            "code": exc.code,
            "message": exc.message,
            "details": exc.details,
        },
        "schema_version": SCHEMA_VERSION,
    }


def main(argv):
    args = _parse_args(argv)
    try:
        payload = write_selected_ingest_research_packet_stub_artifacts(
            index_path=args.selection_index,
            overlay_path=args.selection_overlay,
            normalized_preview_path=args.normalized_preview,
            output_json=args.output_json,
            output_md=args.output_md,
            expected_json=args.expected_json,
        )
    except (SelectedIngestResearchStubError, OperatorSelectionPackError) as exc:
        print(json.dumps(_error_payload(exc), indent=2, ensure_ascii=False, sort_keys=True))
        return 1

    result = {
        "input_accepted": True,
        "output_json": _display_path(_resolve_path(args.output_json)),
        "output_md": _display_path(_resolve_path(args.output_md)),
        "expected_json": _display_path(_resolve_path(args.expected_json)),
        "summary": payload["summary"],
        "selected_market_ids": payload["selected_market_ids"],
    }
    print(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
