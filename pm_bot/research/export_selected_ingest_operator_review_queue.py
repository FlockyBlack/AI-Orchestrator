import argparse
import importlib.util
import json
import sys
from pathlib import Path


TASK_ID = "PMBOT-INGEST-008-SELECTED-INGEST-OPERATOR-REVIEW-QUEUE"
SCHEMA_VERSION = "selected_ingest_operator_review_queue.v1"
MARKDOWN_VERSION = "selected_ingest_operator_review_queue_markdown.v1"
ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MERGED_PACKETS = ROOT / "pm_bot" / "research" / "selected_ingest_merged_manual_research_packets.v1.json"
DEFAULT_JSON_QUEUE = ROOT / "pm_bot" / "research" / "selected_ingest_operator_review_queue.v1.json"
DEFAULT_MARKDOWN_QUEUE = ROOT / "pm_bot" / "research" / "selected_ingest_operator_review_queue.v1.md"
DEFAULT_EXPECTED_JSON_QUEUE = ROOT / "pm_bot" / "research" / "expected_selected_ingest_operator_review_queue.v1.json"
VALIDATOR_PATH = ROOT / "pm_bot" / "research" / "validate_manual_research_packets.py"

SELECTED_MARKET_IDS = ("692258", "824952", "691547", "597964", "598936")
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
    "event_id",
    "event_title",
    "category",
    "packet_type",
    "current_yes_price",
    "liquidity",
    "volume",
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
    parser = argparse.ArgumentParser(
        description="Export a deterministic offline selected-ingest operator review queue."
    )
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
    spec = importlib.util.spec_from_file_location("selected_ingest_manual_packet_validator", VALIDATOR_PATH)
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


def _count_list(value):
    if isinstance(value, list):
        return len(value)
    return 0


def _string_list(value):
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


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


def _selected_sort_key(item):
    market_id = item["market_id"] if isinstance(item, dict) else _clean_text(item.get("market_id"))
    try:
        market_index = SELECTED_MARKET_IDS.index(market_id)
    except ValueError:
        market_index = len(SELECTED_MARKET_IDS)
    return (market_index, market_id, _clean_text(item.get("title_question") or item.get("title") or item.get("question")))


def _load_selected_packets(merged_packets_path):
    payload = _load_json(merged_packets_path)
    if not isinstance(payload, dict):
        raise ValueError("selected ingest merged packet payload must be a JSON object")
    if tuple(str(market_id) for market_id in payload.get("selected_market_ids", ())) != SELECTED_MARKET_IDS:
        raise ValueError("selected ingest merged packet payload has unexpected selected_market_ids")
    packets = payload.get("packets")
    if not isinstance(packets, list):
        raise ValueError("selected ingest merged packet payload must contain a packets list")
    if len(packets) != len(SELECTED_MARKET_IDS):
        raise ValueError("selected ingest merged packet payload must contain exactly five packets")
    if tuple(_clean_text(packet.get("market_id")) for packet in packets if isinstance(packet, dict)) != SELECTED_MARKET_IDS:
        raise ValueError("selected ingest merged packet order does not match selected_market_ids")
    return payload, packets


def _next_manual_action(group_name):
    if group_name == "invalid":
        return "fix_validation_errors"
    if group_name == "needs_more_information":
        return "add_missing_information"
    if group_name == "stub_only":
        return "fill_stub_evidence"
    return "operator_review_required"


def _queue_item(packet, validation_errors, group_name, evidence_slot_names):
    title_question = _clean_text(packet.get("question") or packet.get("title"))
    missing_information = _string_list(packet.get("missing_information"))
    return {
        "market_id": _clean_text(packet.get("market_id")),
        "title_question": title_question,
        "event_id": _clean_text(packet.get("event_id")),
        "event_title": _clean_text(packet.get("event_title")),
        "category": _clean_text(packet.get("category")),
        "packet_type": _clean_text(packet.get("packet_type")),
        "current_yes_price": packet.get("current_yes_price"),
        "liquidity": packet.get("liquidity"),
        "volume": packet.get("volume"),
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
    for group_name in GROUPS:
        for item in groups[group_name]:
            if list(item) != expected:
                raise ValueError(f"queue item field order mismatch for {item.get('market_id', '')}")


def build_selected_ingest_operator_review_queue(
    merged_packets_path=DEFAULT_MERGED_PACKETS,
    json_output_path=DEFAULT_JSON_QUEUE,
    markdown_output_path=DEFAULT_MARKDOWN_QUEUE,
):
    merged_packets_path = _resolve_path(merged_packets_path)
    json_output_path = _resolve_path(json_output_path)
    markdown_output_path = _resolve_path(markdown_output_path)
    merged_payload, packets = _load_selected_packets(merged_packets_path)
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
        groups[group_name].sort(key=_selected_sort_key)

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
        "selected_market_ids": list(SELECTED_MARKET_IDS),
        "queue_item_fields": list(QUEUE_ITEM_FIELDS),
        "queue_summary": summary,
        "market_ids_by_group": _market_ids_by_group(groups),
        "groups": groups,
        "limitations": [
            "Reads only local selected-ingest merged manual research packets.",
            "Groups packets by structural status and validator errors only.",
            "No source lookup, outcome inference, market evaluation, or runtime automation is performed.",
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
        "# Selected Ingest Operator Review Queue v1",
        "",
        "## Summary",
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
        "## Selected Market IDs",
    ]
    lines.extend(f"- {market_id}" for market_id in queue["selected_market_ids"])
    lines.extend(
        [
            "",
            "## Safety Boundary",
            "- offline_local_artifact_only: true",
            "- source_lookup_performed: false",
            "- outcome_inference_performed: false",
            "- runtime_automation_changed: false",
            "",
        ]
    )

    for group_name in GROUPS:
        items = queue["groups"][group_name]
        lines.extend([f"## {group_name} ({len(items)})", ""])
        if not items:
            lines.extend(["- none", ""])
            continue
        for item in items:
            lines.extend(
                [
                    f"### Market {item['market_id']}",
                    f"- market_id: {item['market_id']}",
                    f"- title/question: {item['title_question']}",
                    f"- event_id: {item['event_id']}",
                    f"- event_title: {item['event_title']}",
                    f"- category: {item['category']}",
                    f"- packet_type: {item['packet_type']}",
                    f"- current_yes_price: {_render_scalar(item['current_yes_price'])}",
                    f"- liquidity: {_render_scalar(item['liquidity'])}",
                    f"- volume: {_render_scalar(item['volume'])}",
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


def write_selected_ingest_operator_review_queue_artifacts(
    merged_packets_path=DEFAULT_MERGED_PACKETS,
    json_output_path=DEFAULT_JSON_QUEUE,
    markdown_output_path=DEFAULT_MARKDOWN_QUEUE,
    expected_json_output_path=DEFAULT_EXPECTED_JSON_QUEUE,
):
    json_output_path = _resolve_path(json_output_path)
    markdown_output_path = _resolve_path(markdown_output_path)
    expected_json_output_path = _resolve_path(expected_json_output_path)
    queue = build_selected_ingest_operator_review_queue(merged_packets_path, json_output_path, markdown_output_path)
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
        "selected_market_ids": queue["selected_market_ids"],
    }


def main(argv):
    args = _parse_args(argv)
    summary = write_selected_ingest_operator_review_queue_artifacts(
        merged_packets_path=args.merged_packets,
        json_output_path=args.json_output,
        markdown_output_path=args.markdown_output,
        expected_json_output_path=args.expected_json_output,
    )
    print(json.dumps(summary, indent=2, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
