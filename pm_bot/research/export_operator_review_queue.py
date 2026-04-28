import argparse
import importlib.util
import json
import sys
from pathlib import Path


TASK_ID = "PMBOT-RESEARCH-010-OPERATOR-REVIEW-QUEUE-EXPORT"
SCHEMA_VERSION = "operator_review_queue.v1"
MARKDOWN_VERSION = "operator_review_queue_markdown.v1"
ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MERGED_PACKETS = ROOT / "pm_bot" / "research" / "merged_manual_research_packets.v1.json"
DEFAULT_JSON_QUEUE = ROOT / "pm_bot" / "research" / "operator_review_queue.v1.json"
DEFAULT_MARKDOWN_QUEUE = ROOT / "pm_bot" / "research" / "operator_review_queue.v1.md"
DEFAULT_EXPECTED_JSON_QUEUE = ROOT / "pm_bot" / "research" / "expected_operator_review_queue.v1.json"
VALIDATOR_PATH = ROOT / "pm_bot" / "research" / "validate_manual_research_packets.py"


GROUPS = (
    "ready_for_operator_review",
    "needs_more_information",
    "manual_evidence_added",
    "stub_only",
    "invalid",
)

QUEUE_ITEM_FIELDS = (
    "market_id",
    "title_question",
    "category",
    "packet_type",
    "current_yes_price",
    "liquidity",
    "deadline",
    "completion_status",
    "evidence_item_count",
    "official_sources_checked_count",
    "credible_news_sources_checked_count",
    "missing_information_count",
    "missing_information",
    "validation_errors",
    "next_manual_action",
)


def _parse_args(argv):
    parser = argparse.ArgumentParser(description="Export a deterministic offline PMBOT operator review queue.")
    parser.add_argument("--merged-packets", default=str(DEFAULT_MERGED_PACKETS.relative_to(ROOT)))
    parser.add_argument("--json-output", default=str(DEFAULT_JSON_QUEUE.relative_to(ROOT)))
    parser.add_argument("--markdown-output", default=str(DEFAULT_MARKDOWN_QUEUE.relative_to(ROOT)))
    parser.add_argument("--expected-json-output", default=str(DEFAULT_EXPECTED_JSON_QUEUE.relative_to(ROOT)))
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


def _load_validator_contract():
    spec = importlib.util.spec_from_file_location("manual_research_packet_validator_contract", VALIDATOR_PATH)
    module = importlib.util.module_from_spec(spec)
    if spec.loader is None:
        raise RuntimeError(f"Unable to load validator contract from {VALIDATOR_PATH}")
    spec.loader.exec_module(module)
    return {
        "module": module,
        "schema_version": module.SCHEMA_VERSION,
        "expected_evidence_slots": tuple(module.EXPECTED_EVIDENCE_SLOTS),
    }


def _clean_text(value):
    if value is None:
        return ""
    return str(value).strip()


def _packet_sort_key(packet):
    rank = packet.get("shortlist_rank")
    rank_key = rank if isinstance(rank, int) else 10**9
    return (rank_key, _clean_text(packet.get("market_id")), _clean_text(packet.get("title") or packet.get("question")))


def _load_packets(merged_packets_path):
    payload = _load_json(merged_packets_path)
    packets = payload.get("packets")
    if not isinstance(packets, list):
        raise ValueError("merged packet payload must contain a packets list")
    return payload, sorted(packets, key=_packet_sort_key)


def _count_list(value):
    if isinstance(value, list):
        return len(value)
    return 0


def _evidence_item_count(packet, evidence_slot_names):
    evidence_slots = packet.get("evidence_slots")
    if not isinstance(evidence_slots, dict):
        return 0
    total = 0
    for slot_name in evidence_slot_names:
        slot_value = evidence_slots.get(slot_name)
        if isinstance(slot_value, list):
            total += len(slot_value)
    return total


def _missing_information(packet):
    value = packet.get("missing_information")
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _next_manual_action(group_name):
    if group_name == "invalid":
        return "fix_validation_errors"
    if group_name == "needs_more_information":
        return "add_missing_information"
    if group_name == "stub_only":
        return "fill_stub_evidence"
    return "operator_review_required"


def _queue_item(packet, validation_errors, group_name, evidence_slot_names):
    title = _clean_text(packet.get("title") or packet.get("question"))
    question = _clean_text(packet.get("question") or title)
    missing_information = _missing_information(packet)
    return {
        "market_id": _clean_text(packet.get("market_id")),
        "title_question": question or title,
        "category": _clean_text(packet.get("category")),
        "packet_type": _clean_text(packet.get("packet_type")),
        "current_yes_price": packet.get("current_yes_price"),
        "liquidity": packet.get("liquidity"),
        "deadline": _clean_text(packet.get("deadline")),
        "completion_status": _clean_text(packet.get("completion_status")),
        "evidence_item_count": _evidence_item_count(packet, evidence_slot_names),
        "official_sources_checked_count": _count_list(packet.get("official_sources_checked")),
        "credible_news_sources_checked_count": _count_list(packet.get("credible_news_sources_checked")),
        "missing_information_count": len(missing_information),
        "missing_information": missing_information,
        "validation_errors": validation_errors,
        "next_manual_action": _next_manual_action(group_name),
    }


def _empty_groups():
    return {group: [] for group in GROUPS}


def _queue_summary(groups):
    return {
        "packets_total": sum(len(items) for items in groups.values()),
        "ready_for_operator_review": len(groups["ready_for_operator_review"]),
        "needs_more_information": len(groups["needs_more_information"]),
        "manual_evidence_added": len(groups["manual_evidence_added"]),
        "stub_only": len(groups["stub_only"]),
        "invalid": len(groups["invalid"]),
    }


def _market_ids_by_group(groups):
    return {group: [item["market_id"] for item in groups[group]] for group in GROUPS}


def _assert_item_fields(groups):
    expected = list(QUEUE_ITEM_FIELDS)
    for group in GROUPS:
        for item in groups[group]:
            if list(item) != expected:
                raise ValueError(f"queue item field order mismatch for {item.get('market_id', '')}")


def build_operator_review_queue(
    merged_packets_path=DEFAULT_MERGED_PACKETS,
    json_output_path=DEFAULT_JSON_QUEUE,
    markdown_output_path=DEFAULT_MARKDOWN_QUEUE,
):
    merged_packets_path = _resolve_path(merged_packets_path)
    json_output_path = _resolve_path(json_output_path)
    markdown_output_path = _resolve_path(markdown_output_path)
    merged_payload, packets = _load_packets(merged_packets_path)
    validator_contract = _load_validator_contract()
    groups = _empty_groups()

    for packet in packets:
        validation_errors = validator_contract["module"].validate_packet(packet)
        completion_status = _clean_text(packet.get("completion_status"))
        group_name = "invalid" if validation_errors else completion_status
        if group_name not in groups:
            group_name = "invalid"
        groups[group_name].append(
            _queue_item(packet, validation_errors, group_name, validator_contract["expected_evidence_slots"])
        )

    for group_name in GROUPS:
        groups[group_name].sort(key=lambda item: (item["market_id"], item["title_question"]))

    _assert_item_fields(groups)
    summary = _queue_summary(groups)
    return {
        "schema_version": SCHEMA_VERSION,
        "markdown_version": MARKDOWN_VERSION,
        "task_id": TASK_ID,
        "deterministic": True,
        "source_merged_packets_path": _display_path(merged_packets_path),
        "source_merged_packets_schema_version": merged_payload.get("schema_version"),
        "validator_contract_path": _display_path(VALIDATOR_PATH),
        "validator_contract_schema_version": validator_contract["schema_version"],
        "json_queue_path": _display_path(json_output_path),
        "markdown_queue_path": _display_path(markdown_output_path),
        "queue_item_fields": list(QUEUE_ITEM_FIELDS),
        "queue_summary": summary,
        "market_ids_by_group": _market_ids_by_group(groups),
        "groups": groups,
        "limitations": [
            "Reads only local merged manual research packets.",
            "Groups packets by structural status and validator errors only.",
            "Does not fetch sources, infer outcomes, or create runtime actions.",
        ],
    }


def _render_scalar(value):
    if value is None:
        return ""
    return str(value)


def _render_missing_information(items):
    if not items:
        return ["  - none"]
    return [f"  - {item}" for item in items]


def _render_validation_errors(errors):
    if not errors:
        return ["  - none"]
    return [f"  - {error['path']}: {error['code']} - {error['message']}" for error in errors]


def render_markdown_queue(queue):
    summary = queue["queue_summary"]
    lines = [
        "# PMBOT Operator Review Queue v1",
        "",
        f"- task_id: {queue['task_id']}",
        f"- source_merged_packets_path: {queue['source_merged_packets_path']}",
        f"- validator_contract_path: {queue['validator_contract_path']}",
        f"- packets_total: {summary['packets_total']}",
        f"- ready_for_operator_review: {summary['ready_for_operator_review']}",
        f"- needs_more_information: {summary['needs_more_information']}",
        f"- manual_evidence_added: {summary['manual_evidence_added']}",
        f"- stub_only: {summary['stub_only']}",
        f"- invalid: {summary['invalid']}",
        "",
        "This offline queue contains structural operator metadata only.",
        "",
    ]

    for group_name in GROUPS:
        items = queue["groups"][group_name]
        lines.extend([f"## {group_name} ({len(items)})", ""])
        if not items:
            lines.extend(["- none", ""])
            continue
        for item in items:
            lines.extend(
                [
                    f"### {item['market_id']}",
                    f"- title/question: {item['title_question']}",
                    f"- category: {item['category']}",
                    f"- packet_type: {item['packet_type']}",
                    f"- current_yes_price: {_render_scalar(item['current_yes_price'])}",
                    f"- liquidity: {_render_scalar(item['liquidity'])}",
                    f"- deadline: {item['deadline']}",
                    f"- completion_status: {item['completion_status']}",
                    f"- evidence_item_count: {item['evidence_item_count']}",
                    f"- official_sources_checked_count: {item['official_sources_checked_count']}",
                    f"- credible_news_sources_checked_count: {item['credible_news_sources_checked_count']}",
                    f"- missing_information_count: {item['missing_information_count']}",
                    f"- next_manual_action: {item['next_manual_action']}",
                    "- missing_information:",
                ]
            )
            lines.extend(_render_missing_information(item["missing_information"]))
            lines.append("- validation_errors:")
            lines.extend(_render_validation_errors(item["validation_errors"]))
            lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def write_operator_review_queue_artifacts(
    merged_packets_path=DEFAULT_MERGED_PACKETS,
    json_output_path=DEFAULT_JSON_QUEUE,
    markdown_output_path=DEFAULT_MARKDOWN_QUEUE,
    expected_json_output_path=DEFAULT_EXPECTED_JSON_QUEUE,
):
    json_output_path = _resolve_path(json_output_path)
    markdown_output_path = _resolve_path(markdown_output_path)
    expected_json_output_path = _resolve_path(expected_json_output_path)
    queue = build_operator_review_queue(merged_packets_path, json_output_path, markdown_output_path)
    rendered_queue = json.dumps(queue, indent=2, ensure_ascii=True) + "\n"
    rendered_markdown = render_markdown_queue(queue)

    json_output_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_output_path.parent.mkdir(parents=True, exist_ok=True)
    expected_json_output_path.parent.mkdir(parents=True, exist_ok=True)
    json_output_path.write_text(rendered_queue, encoding="utf-8")
    markdown_output_path.write_text(rendered_markdown, encoding="utf-8")
    expected_json_output_path.write_text(rendered_queue, encoding="utf-8")
    return {
        "task_id": TASK_ID,
        "json_queue_path": _display_path(json_output_path),
        "markdown_queue_path": _display_path(markdown_output_path),
        "expected_json_queue_path": _display_path(expected_json_output_path),
        "queue_summary": queue["queue_summary"],
    }


def main(argv):
    args = _parse_args(argv)
    summary = write_operator_review_queue_artifacts(
        merged_packets_path=args.merged_packets,
        json_output_path=args.json_output,
        markdown_output_path=args.markdown_output,
        expected_json_output_path=args.expected_json_output,
    )
    print(json.dumps(summary, indent=2, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
