import argparse
import json
import sys
from pathlib import Path


TASK_ID = "PMBOT-RESEARCH-012-DOSSIER-DRAFT-SKELETON-EXPORT"
SCHEMA_VERSION = "dossier_draft_skeletons.v1"
MARKDOWN_VERSION = "dossier_draft_skeletons_markdown.v1"
ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MERGED_PACKETS = ROOT / "pm_bot" / "research" / "merged_manual_research_packets.v1.json"
DEFAULT_OPERATOR_REVIEW_QUEUE = ROOT / "pm_bot" / "research" / "operator_review_queue.v1.json"
DEFAULT_REVIEW_RECORDS_RESULT = ROOT / "pm_bot" / "research" / "operator_review_records_result.v1.json"
DEFAULT_JSON_OUTPUT = ROOT / "pm_bot" / "research" / "dossier_draft_skeletons.v1.json"
DEFAULT_MARKDOWN_OUTPUT = ROOT / "pm_bot" / "research" / "dossier_draft_skeletons.v1.md"
DEFAULT_EXPECTED_JSON_OUTPUT = ROOT / "pm_bot" / "research" / "expected_dossier_draft_skeletons.v1.json"


READY_REVIEW_OUTCOME = "ready_for_dossier_drafting"
READY_PACKET_STATUS = "ready_for_operator_review"
DRAFT_STATUS = "dossier_draft_skeleton_only"
EVIDENCE_SLOTS = (
    "official_resolution_criteria",
    "official_yes_evidence",
    "official_no_evidence",
    "credible_news_yes_evidence",
    "credible_news_no_evidence",
    "uncertainty_factors",
    "source_reliability_notes",
)
EVIDENCE_INVENTORY_FIELDS = (
    "source_name",
    "source_type",
    "source_url_or_reference",
    "captured_claim",
    "relevance_to_resolution",
    "operator_notes",
)
SKELETON_FIELDS = (
    "market_id",
    "title_question",
    "category",
    "packet_type",
    "current_yes_price",
    "liquidity",
    "deadline",
    "resolution_criteria_summary",
    "source_coverage_summary",
    "evidence_inventory",
    "missing_information_reviewed",
    "operator_review_notes",
    "dossier_sections_to_fill",
    "open_questions",
    "draft_status",
)
SECTION_NAMES = (
    "market_overview",
    "resolution_criteria",
    "source_coverage",
    "evidence_inventory",
    "missing_information_review",
    "operator_notes",
    "open_questions",
)
SKIP_REASONS = (
    "stub_only",
    "needs_more_information",
    "manual_evidence_added_without_accepted_ready_review",
    "watch_only_manual",
    "research_quality_rejected",
    "invalid",
)


def _parse_args(argv):
    parser = argparse.ArgumentParser(description="Export deterministic offline PMBOT dossier draft skeletons.")
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
    resolved = Path(path).resolve()
    try:
        return str(resolved.relative_to(ROOT.resolve())).replace("\\", "/")
    except ValueError:
        return str(resolved).replace("\\", "/")


def _load_json(path):
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _clean_text(value):
    if value is None:
        return ""
    return str(value).strip()


def _string_list(value):
    if not isinstance(value, list):
        return []
    return [_clean_text(item) for item in value if _clean_text(item)]


def _packet_sort_key(packet):
    rank = packet.get("shortlist_rank")
    rank_key = rank if isinstance(rank, int) else 10**9
    return (rank_key, _clean_text(packet.get("market_id")), _clean_text(packet.get("title") or packet.get("question")))


def _load_packets(path):
    payload = _load_json(path)
    packets = payload.get("packets")
    if not isinstance(packets, list):
        raise ValueError("merged packet payload must contain a packets list")
    return payload, sorted(packets, key=_packet_sort_key)


def _queue_groups(queue_payload):
    groups = queue_payload.get("groups")
    if not isinstance(groups, dict):
        raise ValueError("operator review queue payload must contain groups")
    market_groups = {}
    for group_name in sorted(groups):
        items = groups[group_name]
        if not isinstance(items, list):
            continue
        for item in items:
            if isinstance(item, dict) and _clean_text(item.get("market_id")):
                market_groups[_clean_text(item.get("market_id"))] = group_name
    return market_groups


def _accepted_review_records(review_records_result_payload):
    records = review_records_result_payload.get("accepted_review_records")
    if not isinstance(records, list):
        raise ValueError("operator review records result must contain accepted_review_records")

    normalized = []
    for record in records:
        if isinstance(record, dict) and _clean_text(record.get("market_id")):
            normalized.append(record)
    return sorted(
        normalized,
        key=lambda record: (
            _clean_text(record.get("market_id")),
            _clean_text(record.get("review_outcome")),
            _clean_text(record.get("review_status")),
        ),
    )


def _accepted_review_record_by_market_id(accepted_records):
    records_by_market_id = {}
    for record in accepted_records:
        records_by_market_id[_clean_text(record.get("market_id"))] = record
    return records_by_market_id


def _ready_review_market_ids(accepted_records):
    return {
        _clean_text(record.get("market_id"))
        for record in accepted_records
        if _clean_text(record.get("review_outcome")) == READY_REVIEW_OUTCOME
    }


def _can_export(packet, queue_group, accepted_record):
    return (
        accepted_record is not None
        and _clean_text(accepted_record.get("review_outcome")) == READY_REVIEW_OUTCOME
        and _clean_text(packet.get("completion_status")) == READY_PACKET_STATUS
        and queue_group == READY_PACKET_STATUS
    )


def _skip_reason(packet, queue_group, accepted_record):
    review_outcome = _clean_text(accepted_record.get("review_outcome")) if accepted_record else ""
    if review_outcome in {"needs_more_information", "watch_only_manual", "research_quality_rejected"}:
        return review_outcome

    status = _clean_text(packet.get("completion_status"))
    if queue_group == "invalid":
        return "invalid"
    if status == "stub_only":
        return "stub_only"
    if status == "needs_more_information":
        return "needs_more_information"
    if status == "manual_evidence_added":
        return "manual_evidence_added_without_accepted_ready_review"
    return "invalid"


def _source_coverage_summary(packet):
    official_checked = _string_list(packet.get("official_sources_checked"))
    credible_checked = _string_list(packet.get("credible_news_sources_checked"))
    official_to_check = _string_list(packet.get("official_sources_to_check"))
    credible_to_check = _string_list(packet.get("credible_news_sources_to_check"))
    evidence_inventory = _evidence_inventory(packet)
    return {
        "official_sources_to_check": official_to_check,
        "credible_news_sources_to_check": credible_to_check,
        "official_sources_checked": official_checked,
        "credible_news_sources_checked": credible_checked,
        "official_sources_checked_count": len(official_checked),
        "credible_news_sources_checked_count": len(credible_checked),
        "evidence_inventory_count": len(evidence_inventory),
    }


def _evidence_inventory(packet):
    evidence_slots = packet.get("evidence_slots")
    if not isinstance(evidence_slots, dict):
        return []

    inventory = []
    for slot_name in EVIDENCE_SLOTS:
        items = evidence_slots.get(slot_name)
        if not isinstance(items, list):
            continue
        for item in items:
            if not isinstance(item, dict):
                continue
            normalized = {field: _clean_text(item.get(field)) for field in EVIDENCE_INVENTORY_FIELDS}
            inventory.append(normalized)
    return inventory


def _missing_information_reviewed(packet, accepted_record):
    return {
        "packet_missing_information": _string_list(packet.get("missing_information")),
        "requested_followup_information": _string_list(accepted_record.get("requested_followup_information")),
    }


def _open_questions(packet, accepted_record):
    questions = []
    questions.extend(_string_list(packet.get("missing_information")))
    questions.extend(_string_list(accepted_record.get("requested_followup_information")))
    seen = set()
    normalized = []
    for question in questions:
        if question in seen:
            continue
        seen.add(question)
        normalized.append(question)
    return normalized


def _dossier_skeleton(packet, accepted_record):
    title = _clean_text(packet.get("title") or packet.get("question"))
    question = _clean_text(packet.get("question") or title)
    skeleton = {
        "market_id": _clean_text(packet.get("market_id")),
        "title_question": question or title,
        "category": _clean_text(packet.get("category")),
        "packet_type": _clean_text(packet.get("packet_type")),
        "current_yes_price": packet.get("current_yes_price"),
        "liquidity": packet.get("liquidity"),
        "deadline": _clean_text(packet.get("deadline")),
        "resolution_criteria_summary": _clean_text(packet.get("resolution_criteria_summary")),
        "source_coverage_summary": _source_coverage_summary(packet),
        "evidence_inventory": _evidence_inventory(packet),
        "missing_information_reviewed": _missing_information_reviewed(packet, accepted_record),
        "operator_review_notes": _clean_text(accepted_record.get("reviewer_notes")),
        "dossier_sections_to_fill": list(SECTION_NAMES),
        "open_questions": _open_questions(packet, accepted_record),
        "draft_status": DRAFT_STATUS,
    }
    return {field: skeleton[field] for field in SKELETON_FIELDS}


def _empty_skipped():
    return {reason: [] for reason in SKIP_REASONS}


def _empty_skipped_counts():
    return {reason: 0 for reason in SKIP_REASONS}


def _export_summary(packets, accepted_records, ready_review_market_ids, skeletons, skipped):
    skipped_counts = _empty_skipped_counts()
    for reason in SKIP_REASONS:
        skipped_counts[reason] = len(skipped[reason])
    return {
        "packets_read": len(packets),
        "accepted_review_records_seen": len(accepted_records),
        "ready_review_records_seen": len(ready_review_market_ids),
        "dossier_draft_skeletons_exported": len(skeletons),
        "packets_skipped": sum(skipped_counts.values()),
        "skipped_packet_counts": skipped_counts,
    }


def _assert_skeleton_fields(skeletons):
    expected = list(SKELETON_FIELDS)
    for skeleton in skeletons:
        if list(skeleton) != expected:
            raise ValueError(f"skeleton field sequence mismatch for {skeleton.get('market_id', '')}")
        for item in skeleton["evidence_inventory"]:
            if list(item) != list(EVIDENCE_INVENTORY_FIELDS):
                raise ValueError(f"evidence inventory field sequence mismatch for {skeleton.get('market_id', '')}")


def build_dossier_draft_skeleton_export(
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

    merged_payload, packets = _load_packets(merged_packets_path)
    queue_payload = _load_json(operator_review_queue_path)
    review_records_result_payload = _load_json(review_records_result_path)
    queue_group_by_market_id = _queue_groups(queue_payload)
    accepted_records = _accepted_review_records(review_records_result_payload)
    accepted_by_market_id = _accepted_review_record_by_market_id(accepted_records)
    ready_review_market_ids = _ready_review_market_ids(accepted_records)
    skipped = _empty_skipped()
    skeletons = []

    for packet in packets:
        market_id = _clean_text(packet.get("market_id"))
        queue_group = queue_group_by_market_id.get(market_id, "invalid")
        accepted_record = accepted_by_market_id.get(market_id)
        if _can_export(packet, queue_group, accepted_record):
            skeletons.append(_dossier_skeleton(packet, accepted_record))
            continue
        skipped[_skip_reason(packet, queue_group, accepted_record)].append(market_id)

    skeletons.sort(key=lambda item: (item["market_id"], item["title_question"]))
    for reason in SKIP_REASONS:
        skipped[reason].sort()
    _assert_skeleton_fields(skeletons)
    summary = _export_summary(packets, accepted_records, ready_review_market_ids, skeletons, skipped)

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
        "skeleton_fields": list(SKELETON_FIELDS),
        "evidence_inventory_fields": list(EVIDENCE_INVENTORY_FIELDS),
        "export_summary": summary,
        "exported_market_ids": [skeleton["market_id"] for skeleton in skeletons],
        "skipped_market_ids_by_reason": skipped,
        "dossier_draft_skeletons": skeletons,
    }


def _render_scalar(value):
    if value is None:
        return ""
    return str(value)


def _render_list(items):
    if not items:
        return ["- none"]
    return [f"- {item}" for item in items]


def _render_nested_list(items):
    if not items:
        return ["  - none"]
    return [f"  - {item}" for item in items]


def render_markdown_report(export_payload):
    summary = export_payload["export_summary"]
    skipped_counts = summary["skipped_packet_counts"]
    lines = [
        "# PMBOT Dossier Draft Skeletons v1",
        "",
        "## Summary",
        "",
        f"- task_id: {export_payload['task_id']}",
        f"- source_merged_packets_path: {export_payload['source_merged_packets_path']}",
        f"- source_operator_review_queue_path: {export_payload['source_operator_review_queue_path']}",
        f"- source_review_records_result_path: {export_payload['source_review_records_result_path']}",
        f"- packets_read: {summary['packets_read']}",
        f"- accepted_review_records_seen: {summary['accepted_review_records_seen']}",
        f"- ready_review_records_seen: {summary['ready_review_records_seen']}",
        f"- dossier_draft_skeletons_exported: {summary['dossier_draft_skeletons_exported']}",
        f"- packets_skipped: {summary['packets_skipped']}",
    ]
    for reason in SKIP_REASONS:
        lines.append(f"- skipped_{reason}: {skipped_counts[reason]}")
    lines.extend(["- exported_market_ids:"])
    lines.extend(_render_nested_list(export_payload["exported_market_ids"]))
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
                    f"- category: {skeleton['category']}",
                    f"- packet_type: {skeleton['packet_type']}",
                    f"- current_yes_price: {_render_scalar(skeleton['current_yes_price'])}",
                    f"- liquidity: {_render_scalar(skeleton['liquidity'])}",
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
            lines.append("")

    lines.extend(["## Skipped Packets", ""])
    for reason in SKIP_REASONS:
        market_ids = export_payload["skipped_market_ids_by_reason"][reason]
        lines.extend([f"### {reason} ({len(market_ids)})", ""])
        lines.extend(_render_list(market_ids))
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def write_dossier_draft_skeleton_artifacts(
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
    export_payload = build_dossier_draft_skeleton_export(
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
        "export_summary": export_payload["export_summary"],
    }


def main(argv):
    args = _parse_args(argv)
    summary = write_dossier_draft_skeleton_artifacts(
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
