import argparse
import importlib.util
import json
import sys
from pathlib import Path


TASK_ID = "PMBOT-INGEST-010-SELECTED-INGEST-DOSSIER-DRAFT-SKELETON-EXPORT"
SCHEMA_VERSION = "selected_ingest_dossier_draft_skeletons.v1"
MARKDOWN_VERSION = "selected_ingest_dossier_draft_skeletons_markdown.v1"
ROOT = Path(__file__).resolve().parents[2]
BASE_EXPORTER_PATH = ROOT / "pm_bot" / "research" / "export_dossier_draft_skeletons.py"
DEFAULT_MERGED_PACKETS = ROOT / "pm_bot" / "research" / "selected_ingest_merged_manual_research_packets.v1.json"
DEFAULT_OPERATOR_REVIEW_QUEUE = ROOT / "pm_bot" / "research" / "selected_ingest_operator_review_queue.v1.json"
DEFAULT_REVIEW_RECORDS_RESULT = ROOT / "pm_bot" / "research" / "selected_ingest_operator_review_records_result.v1.json"
DEFAULT_JSON_OUTPUT = ROOT / "pm_bot" / "research" / "selected_ingest_dossier_draft_skeletons.v1.json"
DEFAULT_MARKDOWN_OUTPUT = ROOT / "pm_bot" / "research" / "selected_ingest_dossier_draft_skeletons.v1.md"
DEFAULT_EXPECTED_JSON_OUTPUT = ROOT / "pm_bot" / "research" / "expected_selected_ingest_dossier_draft_skeletons.v1.json"

SELECTED_MARKET_IDS = ("692258", "824952", "691547", "597964", "598936")
READY_REVIEW_OUTCOME = "ready_for_dossier_drafting"
READY_PACKET_STATUS = "ready_for_operator_review"
DRAFT_STATUS = "dossier_draft_skeleton_only"
SKIP_REASONS = (
    "needs_more_information",
    "watch_only_manual",
    "research_quality_rejected",
    "stub_only",
    "invalid",
    "rejected_record",
)
SKELETON_FIELDS = (
    "market_id",
    "title_question",
    "event_id",
    "event_title",
    "category",
    "packet_type",
    "current_yes_price",
    "liquidity",
    "volume",
    "deadline",
    "resolution_criteria_summary",
    "source_coverage_summary",
    "evidence_inventory",
    "missing_information_reviewed",
    "operator_review_notes",
    "dossier_sections_to_fill",
    "open_questions",
    "draft_status",
    "source_ingest_artifacts",
)


def _load_base_exporter():
    spec = importlib.util.spec_from_file_location("base_dossier_draft_skeleton_exporter", BASE_EXPORTER_PATH)
    module = importlib.util.module_from_spec(spec)
    if spec.loader is None:
        raise RuntimeError(f"Unable to load base exporter from {BASE_EXPORTER_PATH}")
    spec.loader.exec_module(module)
    return module


BASE = _load_base_exporter()
EVIDENCE_SLOTS = tuple(BASE.EVIDENCE_SLOTS)
EVIDENCE_INVENTORY_FIELDS = tuple(BASE.EVIDENCE_INVENTORY_FIELDS)
SECTION_NAMES = tuple(BASE.SECTION_NAMES)


def _parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Export deterministic offline selected-ingest dossier draft skeletons."
    )
    parser.add_argument("--merged-packets", default=str(DEFAULT_MERGED_PACKETS.relative_to(ROOT)))
    parser.add_argument("--operator-review-queue", default=str(DEFAULT_OPERATOR_REVIEW_QUEUE.relative_to(ROOT)))
    parser.add_argument("--review-records-result", default=str(DEFAULT_REVIEW_RECORDS_RESULT.relative_to(ROOT)))
    parser.add_argument("--json-output", default=str(DEFAULT_JSON_OUTPUT.relative_to(ROOT)))
    parser.add_argument("--markdown-output", default=str(DEFAULT_MARKDOWN_OUTPUT.relative_to(ROOT)))
    parser.add_argument("--expected-json-output", default=str(DEFAULT_EXPECTED_JSON_OUTPUT.relative_to(ROOT)))
    return parser.parse_args(argv)


def _resolve_path(path):
    value = Path(path)
    if value.is_absolute():
        return value
    return ROOT / value


def _display_path(path):
    return BASE._display_path(path)


def _load_json(path):
    return BASE._load_json(path)


def _clean_text(value):
    return BASE._clean_text(value)


def _string_list(value):
    return BASE._string_list(value)


def _selected_sort_key(item):
    market_id = _clean_text(item.get("market_id")) if isinstance(item, dict) else _clean_text(item)
    try:
        market_index = SELECTED_MARKET_IDS.index(market_id)
    except ValueError:
        market_index = len(SELECTED_MARKET_IDS)
    title = ""
    if isinstance(item, dict):
        title = _clean_text(item.get("title_question") or item.get("title") or item.get("question"))
    return (market_index, market_id, title)


def _load_selected_packets(path):
    payload = _load_json(path)
    if not isinstance(payload, dict):
        raise ValueError("selected ingest merged packet payload must be a JSON object")
    selected_market_ids = tuple(_clean_text(market_id) for market_id in payload.get("selected_market_ids", ()))
    if selected_market_ids != SELECTED_MARKET_IDS:
        raise ValueError("selected ingest merged packet payload has unexpected selected_market_ids")
    packets = payload.get("packets")
    if not isinstance(packets, list):
        raise ValueError("selected ingest merged packet payload must contain a packets list")
    if tuple(_clean_text(packet.get("market_id")) for packet in packets if isinstance(packet, dict)) != SELECTED_MARKET_IDS:
        raise ValueError("selected ingest merged packet order does not match selected_market_ids")
    return payload, sorted(packets, key=_selected_sort_key)


def _queue_groups(queue_payload):
    return BASE._queue_groups(queue_payload)


def _accepted_review_records(review_records_result_payload):
    records = BASE._accepted_review_records(review_records_result_payload)
    return sorted(records, key=_selected_sort_key)


def _accepted_review_record_by_market_id(accepted_records):
    return BASE._accepted_review_record_by_market_id(accepted_records)


def _rejected_review_records(review_records_result_payload):
    records = review_records_result_payload.get("rejected_review_records")
    if not isinstance(records, list):
        return []
    normalized = []
    for record in records:
        if isinstance(record, dict) and _clean_text(record.get("market_id")):
            normalized.append(record)
    return sorted(normalized, key=_selected_sort_key)


def _ready_review_market_ids(accepted_records):
    return {
        _clean_text(record.get("market_id"))
        for record in accepted_records
        if _clean_text(record.get("review_outcome")) == READY_REVIEW_OUTCOME
    }


def _review_records_read(review_records_result_payload, accepted_records, rejected_records):
    summary = review_records_result_payload.get("review_summary")
    if isinstance(summary, dict) and isinstance(summary.get("review_records_read"), int):
        return summary["review_records_read"]
    return len(accepted_records) + len(rejected_records)


def _can_export(packet, queue_group, accepted_record):
    return (
        accepted_record is not None
        and _clean_text(accepted_record.get("review_outcome")) == READY_REVIEW_OUTCOME
        and _clean_text(packet.get("completion_status")) == READY_PACKET_STATUS
        and queue_group == READY_PACKET_STATUS
    )


def _skip_reason_for_packet(packet, queue_group, accepted_record, rejected_market_ids):
    review_outcome = _clean_text(accepted_record.get("review_outcome")) if accepted_record else ""
    if review_outcome in {"needs_more_information", "watch_only_manual", "research_quality_rejected"}:
        return review_outcome

    status = _clean_text(packet.get("completion_status"))
    if status == "stub_only":
        return "stub_only"
    if queue_group == "invalid" or status == "invalid":
        return "invalid"
    if _clean_text(packet.get("market_id")) in rejected_market_ids:
        return "rejected_record"
    return "invalid"


def _empty_skipped():
    return {reason: [] for reason in SKIP_REASONS}


def _empty_skipped_counts():
    return {reason: 0 for reason in SKIP_REASONS}


def _source_ingest_artifacts(packet):
    artifacts = packet.get("source_ingest_artifacts")
    if not isinstance(artifacts, dict):
        return {}
    return {str(key): artifacts[key] for key in sorted(artifacts)}


def _dossier_skeleton(packet, accepted_record):
    title = _clean_text(packet.get("title") or packet.get("question"))
    question = _clean_text(packet.get("question") or title)
    skeleton = {
        "market_id": _clean_text(packet.get("market_id")),
        "title_question": question or title,
        "event_id": _clean_text(packet.get("event_id")),
        "event_title": _clean_text(packet.get("event_title")),
        "category": _clean_text(packet.get("category")),
        "packet_type": _clean_text(packet.get("packet_type")),
        "current_yes_price": packet.get("current_yes_price"),
        "liquidity": packet.get("liquidity"),
        "volume": packet.get("volume"),
        "deadline": _clean_text(packet.get("deadline")),
        "resolution_criteria_summary": _clean_text(packet.get("resolution_criteria_summary")),
        "source_coverage_summary": BASE._source_coverage_summary(packet),
        "evidence_inventory": BASE._evidence_inventory(packet),
        "missing_information_reviewed": BASE._missing_information_reviewed(packet, accepted_record),
        "operator_review_notes": _clean_text(accepted_record.get("reviewer_notes")),
        "dossier_sections_to_fill": list(SECTION_NAMES),
        "open_questions": BASE._open_questions(packet, accepted_record),
        "draft_status": DRAFT_STATUS,
        "source_ingest_artifacts": _source_ingest_artifacts(packet),
    }
    return {field: skeleton[field] for field in SKELETON_FIELDS}


def _skipped_review_records(accepted_records, rejected_records, exported_market_ids):
    skipped = _empty_skipped()
    for record in accepted_records:
        market_id = _clean_text(record.get("market_id"))
        if market_id in exported_market_ids:
            continue
        reason = _clean_text(record.get("review_outcome"))
        if reason not in skipped:
            reason = "invalid"
        skipped[reason].append(market_id)
    for record in rejected_records:
        skipped["rejected_record"].append(_clean_text(record.get("market_id")))
    for reason in SKIP_REASONS:
        skipped[reason].sort(key=lambda market_id: _selected_sort_key(market_id))
    return skipped


def _export_summary(review_records_read, ready_review_market_ids, skeletons, skipped_review_records):
    skipped_counts = _empty_skipped_counts()
    for reason in SKIP_REASONS:
        skipped_counts[reason] = len(skipped_review_records[reason])
    return {
        "ready_review_records_seen": len(ready_review_market_ids),
        "dossier_draft_skeletons_exported": len(skeletons),
        "records_skipped": review_records_read - len(skeletons),
        "completed_dossiers_created": 0,
        "skipped_record_counts": skipped_counts,
    }


def _assert_skeleton_fields(skeletons):
    expected = list(SKELETON_FIELDS)
    for skeleton in skeletons:
        if list(skeleton) != expected:
            raise ValueError(f"skeleton field sequence mismatch for {skeleton.get('market_id', '')}")
        for item in skeleton["evidence_inventory"]:
            if list(item) != list(EVIDENCE_INVENTORY_FIELDS):
                raise ValueError(f"evidence inventory field sequence mismatch for {skeleton.get('market_id', '')}")


def build_selected_ingest_dossier_draft_skeleton_export(
    merged_packets_path=DEFAULT_MERGED_PACKETS,
    operator_review_queue_path=DEFAULT_OPERATOR_REVIEW_QUEUE,
    review_records_result_path=DEFAULT_REVIEW_RECORDS_RESULT,
    json_output_path=DEFAULT_JSON_OUTPUT,
    markdown_output_path=DEFAULT_MARKDOWN_OUTPUT,
    expected_json_output_path=DEFAULT_EXPECTED_JSON_OUTPUT,
):
    merged_packets_path = _resolve_path(merged_packets_path)
    operator_review_queue_path = _resolve_path(operator_review_queue_path)
    review_records_result_path = _resolve_path(review_records_result_path)
    json_output_path = _resolve_path(json_output_path)
    markdown_output_path = _resolve_path(markdown_output_path)
    expected_json_output_path = _resolve_path(expected_json_output_path)

    merged_payload, packets = _load_selected_packets(merged_packets_path)
    queue_payload = _load_json(operator_review_queue_path)
    review_records_result_payload = _load_json(review_records_result_path)
    queue_group_by_market_id = _queue_groups(queue_payload)
    accepted_records = _accepted_review_records(review_records_result_payload)
    rejected_records = _rejected_review_records(review_records_result_payload)
    accepted_by_market_id = _accepted_review_record_by_market_id(accepted_records)
    rejected_market_ids = {_clean_text(record.get("market_id")) for record in rejected_records}
    ready_review_market_ids = _ready_review_market_ids(accepted_records)
    skipped_packets = _empty_skipped()
    skeletons = []

    for packet in packets:
        market_id = _clean_text(packet.get("market_id"))
        queue_group = queue_group_by_market_id.get(market_id, "invalid")
        accepted_record = accepted_by_market_id.get(market_id)
        if _can_export(packet, queue_group, accepted_record):
            skeletons.append(_dossier_skeleton(packet, accepted_record))
            continue
        skipped_packets[_skip_reason_for_packet(packet, queue_group, accepted_record, rejected_market_ids)].append(market_id)

    skeletons.sort(key=_selected_sort_key)
    for reason in SKIP_REASONS:
        skipped_packets[reason].sort(key=lambda market_id: _selected_sort_key(market_id))
    _assert_skeleton_fields(skeletons)

    exported_market_ids = [skeleton["market_id"] for skeleton in skeletons]
    skipped_records = _skipped_review_records(accepted_records, rejected_records, set(exported_market_ids))
    review_records_read = _review_records_read(review_records_result_payload, accepted_records, rejected_records)
    summary = _export_summary(review_records_read, ready_review_market_ids, skeletons, skipped_records)

    return {
        "schema_version": SCHEMA_VERSION,
        "markdown_version": MARKDOWN_VERSION,
        "task_id": TASK_ID,
        "deterministic": True,
        "source_merged_packets_path": _display_path(merged_packets_path),
        "source_merged_packets_schema_version": merged_payload.get("schema_version"),
        "source_operator_review_queue_path": _display_path(operator_review_queue_path),
        "source_operator_review_queue_schema_version": queue_payload.get("schema_version"),
        "source_review_records_result_path": _display_path(review_records_result_path),
        "source_review_records_result_schema_version": review_records_result_payload.get("schema_version"),
        "json_output_path": _display_path(json_output_path),
        "markdown_output_path": _display_path(markdown_output_path),
        "expected_json_output_path": _display_path(expected_json_output_path),
        "selected_market_ids": list(SELECTED_MARKET_IDS),
        "skeleton_fields": list(SKELETON_FIELDS),
        "evidence_inventory_fields": list(EVIDENCE_INVENTORY_FIELDS),
        "export_summary": summary,
        "exported_market_ids": exported_market_ids,
        "skipped_market_ids_by_reason": skipped_records,
        "skipped_packet_market_ids_by_reason": skipped_packets,
        "dossier_draft_skeletons": skeletons,
    }


def _render_scalar(value):
    return BASE._render_scalar(value)


def _render_list(items):
    return BASE._render_list(items)


def _render_nested_list(items):
    return BASE._render_nested_list(items)


def render_markdown_report(export_payload):
    summary = export_payload["export_summary"]
    skipped_counts = summary["skipped_record_counts"]
    lines = [
        "# Selected Ingest Dossier Draft Skeletons v1",
        "",
        "## Summary",
        "",
        f"- task_id: {export_payload['task_id']}",
        f"- source_merged_packets_path: {export_payload['source_merged_packets_path']}",
        f"- source_operator_review_queue_path: {export_payload['source_operator_review_queue_path']}",
        f"- source_review_records_result_path: {export_payload['source_review_records_result_path']}",
        f"- ready_review_records_seen: {summary['ready_review_records_seen']}",
        f"- dossier_draft_skeletons_exported: {summary['dossier_draft_skeletons_exported']}",
        f"- records_skipped: {summary['records_skipped']}",
        f"- completed_dossiers_created: {summary['completed_dossiers_created']}",
    ]
    for reason in SKIP_REASONS:
        lines.append(f"- skipped_{reason}: {skipped_counts[reason]}")
    lines.extend(["- exported_market_ids:"])
    lines.extend(_render_nested_list(export_payload["exported_market_ids"]))
    lines.extend(["", "## Selected Market IDs", ""])
    lines.extend(_render_list(export_payload["selected_market_ids"]))
    lines.extend(["", "## Draft Skeletons", ""])

    if not export_payload["dossier_draft_skeletons"]:
        lines.extend(["- none", ""])
    else:
        for skeleton in export_payload["dossier_draft_skeletons"]:
            coverage = skeleton["source_coverage_summary"]
            missing = skeleton["missing_information_reviewed"]
            lines.extend(
                [
                    f"### {skeleton['market_id']}",
                    f"- title/question: {skeleton['title_question']}",
                    f"- event_id: {skeleton['event_id']}",
                    f"- event_title: {skeleton['event_title']}",
                    f"- category: {skeleton['category']}",
                    f"- packet_type: {skeleton['packet_type']}",
                    f"- current_yes_price: {_render_scalar(skeleton['current_yes_price'])}",
                    f"- liquidity: {_render_scalar(skeleton['liquidity'])}",
                    f"- volume: {_render_scalar(skeleton['volume'])}",
                    f"- deadline: {skeleton['deadline']}",
                    f"- draft_status: {skeleton['draft_status']}",
                    f"- resolution_criteria_summary: {skeleton['resolution_criteria_summary']}",
                    "",
                    "#### Source Coverage Summary",
                    "",
                    f"- official_sources_checked_count: {coverage['official_sources_checked_count']}",
                    f"- credible_news_sources_checked_count: {coverage['credible_news_sources_checked_count']}",
                    f"- evidence_inventory_count: {coverage['evidence_inventory_count']}",
                    "- official_sources_checked:",
                ]
            )
            lines.extend(_render_nested_list(coverage["official_sources_checked"]))
            lines.append("- credible_news_sources_checked:")
            lines.extend(_render_nested_list(coverage["credible_news_sources_checked"]))
            lines.extend(["", "#### Evidence Inventory", ""])
            if not skeleton["evidence_inventory"]:
                lines.extend(["- none", ""])
            else:
                for index, item in enumerate(skeleton["evidence_inventory"], start=1):
                    lines.extend(
                        [
                            f"- item {index}",
                            f"  - source_name: {item['source_name']}",
                            f"  - source_type: {item['source_type']}",
                            f"  - source_url_or_reference: {item['source_url_or_reference']}",
                            f"  - captured_claim: {item['captured_claim']}",
                            f"  - relevance_to_resolution: {item['relevance_to_resolution']}",
                            f"  - operator_notes: {item['operator_notes']}",
                        ]
                    )
                lines.append("")
            lines.extend(["#### Missing Information Reviewed", ""])
            lines.append("- packet_missing_information:")
            lines.extend(_render_nested_list(missing["packet_missing_information"]))
            lines.append("- requested_followup_information:")
            lines.extend(_render_nested_list(missing["requested_followup_information"]))
            lines.extend(["", "#### Operator Review Notes", ""])
            lines.extend(_render_list([skeleton["operator_review_notes"]] if skeleton["operator_review_notes"] else []))
            lines.extend(["", "#### Sections To Fill", ""])
            lines.extend(_render_list(skeleton["dossier_sections_to_fill"]))
            lines.extend(["", "#### Open Questions", ""])
            lines.extend(_render_list(skeleton["open_questions"]))
            lines.extend(["", "#### Source Ingest Artifacts", ""])
            if not skeleton["source_ingest_artifacts"]:
                lines.extend(["- none", ""])
            else:
                for key, value in skeleton["source_ingest_artifacts"].items():
                    lines.append(f"- {key}: {value}")
                lines.append("")

    lines.extend(["## Skipped Records", ""])
    for reason in SKIP_REASONS:
        market_ids = export_payload["skipped_market_ids_by_reason"][reason]
        lines.extend([f"### {reason} ({len(market_ids)})", ""])
        lines.extend(_render_list(market_ids))
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def write_selected_ingest_dossier_draft_skeleton_artifacts(
    merged_packets_path=DEFAULT_MERGED_PACKETS,
    operator_review_queue_path=DEFAULT_OPERATOR_REVIEW_QUEUE,
    review_records_result_path=DEFAULT_REVIEW_RECORDS_RESULT,
    json_output_path=DEFAULT_JSON_OUTPUT,
    markdown_output_path=DEFAULT_MARKDOWN_OUTPUT,
    expected_json_output_path=DEFAULT_EXPECTED_JSON_OUTPUT,
):
    json_output_path = _resolve_path(json_output_path)
    markdown_output_path = _resolve_path(markdown_output_path)
    expected_json_output_path = _resolve_path(expected_json_output_path)
    export_payload = build_selected_ingest_dossier_draft_skeleton_export(
        merged_packets_path=merged_packets_path,
        operator_review_queue_path=operator_review_queue_path,
        review_records_result_path=review_records_result_path,
        json_output_path=json_output_path,
        markdown_output_path=markdown_output_path,
        expected_json_output_path=expected_json_output_path,
    )
    rendered_json = json.dumps(export_payload, indent=2, ensure_ascii=True) + "\n"
    rendered_markdown = render_markdown_report(export_payload)

    json_output_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_output_path.parent.mkdir(parents=True, exist_ok=True)
    expected_json_output_path.parent.mkdir(parents=True, exist_ok=True)
    json_output_path.write_text(rendered_json, encoding="utf-8")
    markdown_output_path.write_text(rendered_markdown, encoding="utf-8")
    expected_json_output_path.write_text(rendered_json, encoding="utf-8")
    return {
        "task_id": TASK_ID,
        "json_output_path": _display_path(json_output_path),
        "markdown_output_path": _display_path(markdown_output_path),
        "expected_json_output_path": _display_path(expected_json_output_path),
        "selected_market_ids": list(SELECTED_MARKET_IDS),
        "export_summary": export_payload["export_summary"],
    }


def main(argv):
    args = _parse_args(argv)
    summary = write_selected_ingest_dossier_draft_skeleton_artifacts(
        merged_packets_path=args.merged_packets,
        operator_review_queue_path=args.operator_review_queue,
        review_records_result_path=args.review_records_result,
        json_output_path=args.json_output,
        markdown_output_path=args.markdown_output,
        expected_json_output_path=args.expected_json_output,
    )
    print(json.dumps(summary, indent=2, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
