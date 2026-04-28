import argparse
import json
import sys
from pathlib import Path


TASK_ID = "PMBOT-INGEST-006-SELECTED-STUBS-OPERATOR-WORKPACK"
SCHEMA_VERSION = "selected_ingest_operator_workpack_index.v1"
WORKPACK_VERSION = "selected_ingest_operator_workpack.v1"
OVERLAY_SCHEMA_VERSION = "selected_ingest_manual_evidence_overlay_template.v1"
ROOT = Path(__file__).resolve().parents[2]

DEFAULT_STUBS = ROOT / "pm_bot" / "research" / "selected_ingest_research_packet_stubs.v1.json"
DEFAULT_MARKDOWN = ROOT / "pm_bot" / "research" / "selected_ingest_operator_workpack.v1.md"
DEFAULT_INDEX = ROOT / "pm_bot" / "research" / "selected_ingest_operator_workpack_index.v1.json"
DEFAULT_OVERLAY = ROOT / "pm_bot" / "research" / "selected_ingest_manual_evidence_overlay_template.v1.json"
DEFAULT_EXPECTED_INDEX = ROOT / "pm_bot" / "research" / "expected_selected_ingest_operator_workpack_index.v1.json"

EXPECTED_SELECTED_MARKET_IDS = ("692258", "824952", "691547", "597964", "598936")
REQUIRED_EVIDENCE_FIELDS = (
    "source_name",
    "source_type",
    "source_url_or_reference",
    "captured_claim",
    "relevance_to_resolution",
    "operator_notes",
)
REQUIRED_WORKPACK_ITEM_FIELDS = (
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
    "why_selected_for_research",
    "why_not_bet_yet",
    "source_plan",
    "search_queries",
    "official_sources_to_check",
    "credible_news_sources_to_check",
    "blank_evidence_capture_template",
    "missing_information",
    "completion_status",
)


def _parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Export a deterministic offline operator workpack for selected ingest research stubs."
    )
    parser.add_argument("--stubs", default=str(DEFAULT_STUBS.relative_to(ROOT)))
    parser.add_argument("--markdown-output", default=str(DEFAULT_MARKDOWN.relative_to(ROOT)))
    parser.add_argument("--index-output", default=str(DEFAULT_INDEX.relative_to(ROOT)))
    parser.add_argument("--overlay-output", default=str(DEFAULT_OVERLAY.relative_to(ROOT)))
    parser.add_argument("--expected-index-output", default=str(DEFAULT_EXPECTED_INDEX.relative_to(ROOT)))
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


def _write_json(path, payload):
    output_path = _resolve_path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def _write_text(path, text):
    output_path = _resolve_path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(text, encoding="utf-8")


def _text(value):
    if value is None:
        return ""
    return str(value).strip()


def _string_list(value):
    if not isinstance(value, list):
        return []
    return [str(item) for item in value]


def blank_evidence_capture_template():
    return {field: "" for field in REQUIRED_EVIDENCE_FIELDS}


def _require_selected_stubs_payload(payload):
    if not isinstance(payload, dict):
        raise ValueError("selected ingest stubs payload must be a JSON object")
    if payload.get("schema_version") != "selected_ingest_research_packet_stubs.v1":
        raise ValueError("selected ingest stubs schema_version is invalid")
    packet_stubs = payload.get("packet_stubs")
    if not isinstance(packet_stubs, list):
        raise ValueError("selected ingest stubs payload must contain packet_stubs")
    selected_market_ids = payload.get("selected_market_ids")
    if not isinstance(selected_market_ids, list):
        raise ValueError("selected ingest stubs payload must contain selected_market_ids")
    if len(packet_stubs) != len(EXPECTED_SELECTED_MARKET_IDS):
        raise ValueError("selected ingest stubs payload must contain exactly five packet stubs")

    packet_market_ids = [_text(packet.get("market_id")) for packet in packet_stubs if isinstance(packet, dict)]
    if tuple(packet_market_ids) != EXPECTED_SELECTED_MARKET_IDS:
        raise ValueError("selected ingest packet_stubs market_ids do not match the selected ingest task")
    if tuple(str(market_id) for market_id in selected_market_ids) != EXPECTED_SELECTED_MARKET_IDS:
        raise ValueError("selected ingest selected_market_ids do not match the selected ingest task")
    return packet_stubs


def load_selected_stub_packets(stubs_path=DEFAULT_STUBS):
    stubs_path = _resolve_path(stubs_path)
    payload = _load_json(stubs_path)
    packet_stubs = _require_selected_stubs_payload(payload)
    return payload, packet_stubs


def _workpack_item(packet):
    if not isinstance(packet, dict):
        raise ValueError("selected ingest packet stub must be a JSON object")
    title_question = _text(packet.get("question") or packet.get("title"))
    item = {
        "market_id": _text(packet.get("market_id")),
        "title_question": title_question,
        "event_id": _text(packet.get("event_id")),
        "event_title": _text(packet.get("event_title")),
        "category": _text(packet.get("category")),
        "packet_type": _text(packet.get("packet_type")),
        "current_yes_price": packet.get("current_yes_price"),
        "liquidity": packet.get("liquidity"),
        "volume": packet.get("volume"),
        "deadline": _text(packet.get("deadline")),
        "resolution_criteria_summary": _text(packet.get("resolution_criteria_summary")),
        "why_selected_for_research": _text(packet.get("why_selected_for_research")),
        "why_not_bet_yet": _text(packet.get("why_not_bet_yet")),
        "source_plan": _text(packet.get("source_plan")),
        "search_queries": _string_list(packet.get("search_queries")),
        "official_sources_to_check": _string_list(packet.get("official_sources_to_check")),
        "credible_news_sources_to_check": _string_list(packet.get("credible_news_sources_to_check")),
        "blank_evidence_capture_template": blank_evidence_capture_template(),
        "missing_information": _string_list(packet.get("missing_information")),
        "completion_status": _text(packet.get("completion_status")),
    }
    if item["completion_status"] != "stub_only":
        raise ValueError(f"selected ingest packet {item['market_id']} is not stub_only")
    return item


def build_workpack_index(
    stubs_path=DEFAULT_STUBS,
    markdown_output=DEFAULT_MARKDOWN,
    index_output=DEFAULT_INDEX,
    overlay_output=DEFAULT_OVERLAY,
):
    stubs_path = _resolve_path(stubs_path)
    markdown_output = _resolve_path(markdown_output)
    index_output = _resolve_path(index_output)
    overlay_output = _resolve_path(overlay_output)
    stubs_payload, packet_stubs = load_selected_stub_packets(stubs_path)
    items = [_workpack_item(packet) for packet in packet_stubs]
    selected_market_ids = [item["market_id"] for item in items]
    completion_statuses = sorted({item["completion_status"] for item in items})

    return {
        "schema_version": SCHEMA_VERSION,
        "workpack_version": WORKPACK_VERSION,
        "task_id": TASK_ID,
        "deterministic": True,
        "source_stub_packets_path": _display_path(stubs_path),
        "source_stub_packets_schema_version": stubs_payload.get("schema_version"),
        "markdown_workpack_path": _display_path(markdown_output),
        "json_index_path": _display_path(index_output),
        "manual_evidence_overlay_template_path": _display_path(overlay_output),
        "selected_stub_packets_read": len(packet_stubs),
        "operator_workpack_items_exported": len(items),
        "selected_market_ids": selected_market_ids,
        "completion_statuses": completion_statuses,
        "required_evidence_fields": list(REQUIRED_EVIDENCE_FIELDS),
        "required_workpack_item_fields": list(REQUIRED_WORKPACK_ITEM_FIELDS),
        "workpack_items": items,
        "boundary_notes": [
            "Offline manual research preparation only.",
            "No source lookup is performed by this exporter.",
            "No final research packet is created by this exporter.",
            "No downstream flow is changed by this exporter.",
        ],
    }


def build_manual_evidence_overlay_template(index):
    entries = {}
    for market_id in index["selected_market_ids"]:
        entries[market_id] = {
            "completion_status": "stub_only",
            "manual_evidence_entries": [],
            "missing_information": [],
            "operator_notes": "",
        }
    return {
        "schema_version": OVERLAY_SCHEMA_VERSION,
        "task_id": TASK_ID,
        "deterministic": True,
        "source_workpack_index_path": index["json_index_path"],
        "selected_market_ids": list(index["selected_market_ids"]),
        "required_evidence_fields": list(REQUIRED_EVIDENCE_FIELDS),
        "blank_evidence_entry_template": blank_evidence_capture_template(),
        "manual_entries_by_market_id": entries,
        "notes": [
            "Blank template for future manual evidence collection.",
            "Keep evidence entries empty until a human operator adds sourced claims.",
        ],
    }


def _render_list(items):
    if not items:
        return ["- "]
    return [f"- {item}" for item in items]


def _render_blank_template(template):
    return [f"- {field}: {template[field]}" for field in REQUIRED_EVIDENCE_FIELDS]


def render_markdown_workpack(index):
    lines = [
        "# Selected Ingest Operator Workpack v1",
        "",
        "Deterministic offline manual evidence collection workpack for selected live-ingest research stubs.",
        "",
        "## Summary",
        f"- task_id: {index['task_id']}",
        f"- selected_stub_packets_read: {index['selected_stub_packets_read']}",
        f"- operator_workpack_items_exported: {index['operator_workpack_items_exported']}",
        "- completion_status: stub_only",
        f"- manual_evidence_overlay_template: {index['manual_evidence_overlay_template_path']}",
        "",
        "## Source Artifact",
        f"- selected_ingest_research_packet_stubs: {index['source_stub_packets_path']}",
        f"- source_schema_version: {index['source_stub_packets_schema_version']}",
        "",
        "## Safety Boundary",
        "- offline_manual_preparation_only: true",
        "- source_lookup_performed: false",
        "- final_research_output_created: false",
        "- downstream_flow_changed: false",
        "",
        "## Selected Market IDs",
    ]
    lines.extend(f"- {market_id}" for market_id in index["selected_market_ids"])
    lines.extend(["", "## Workpack Items"])

    for item in index["workpack_items"]:
        lines.extend(
            [
                "",
                f"### Market {item['market_id']}",
                "",
                "#### Market Details",
                f"- market_id: {item['market_id']}",
                f"- title/question: {item['title_question']}",
                f"- event_id: {item['event_id']}",
                f"- event_title: {item['event_title']}",
                f"- category: {item['category']}",
                f"- packet_type: {item['packet_type']}",
                f"- current_yes_price: {item['current_yes_price']}",
                f"- liquidity: {item['liquidity']}",
                f"- volume: {item['volume']}",
                f"- deadline: {item['deadline']}",
                f"- completion_status: {item['completion_status']}",
                "",
                "#### Resolution Criteria Summary",
                item["resolution_criteria_summary"],
                "",
                "#### Why Selected For Research",
                item["why_selected_for_research"],
                "",
                "#### Why Not Bet Yet",
                item["why_not_bet_yet"],
                "",
                "#### Source Plan",
                item["source_plan"],
                "",
                "#### Search Queries",
            ]
        )
        lines.extend(_render_list(item["search_queries"]))
        lines.extend(["", "#### Official Sources To Check"])
        lines.extend(_render_list(item["official_sources_to_check"]))
        lines.extend(["", "#### Credible News Sources To Check"])
        lines.extend(_render_list(item["credible_news_sources_to_check"]))
        lines.extend(["", "#### Blank Evidence Capture Template"])
        lines.extend(_render_blank_template(item["blank_evidence_capture_template"]))
        lines.extend(["", "#### Missing Information"])
        lines.extend(_render_list(item["missing_information"]))

    return "\n".join(lines).rstrip() + "\n"


def write_workpack_artifacts(
    stubs_path=DEFAULT_STUBS,
    markdown_output=DEFAULT_MARKDOWN,
    index_output=DEFAULT_INDEX,
    overlay_output=DEFAULT_OVERLAY,
    expected_index_output=DEFAULT_EXPECTED_INDEX,
):
    index = build_workpack_index(stubs_path, markdown_output, index_output, overlay_output)
    overlay = build_manual_evidence_overlay_template(index)

    _write_text(markdown_output, render_markdown_workpack(index))
    _write_json(index_output, index)
    _write_json(overlay_output, overlay)
    _write_json(expected_index_output, index)

    return {
        "task_id": TASK_ID,
        "selected_stub_packets_read": index["selected_stub_packets_read"],
        "operator_workpack_items_exported": index["operator_workpack_items_exported"],
        "manual_evidence_overlay_template_created": True,
        "markdown_workpack_path": _display_path(_resolve_path(markdown_output)),
        "json_index_path": _display_path(_resolve_path(index_output)),
        "manual_evidence_overlay_template_path": _display_path(_resolve_path(overlay_output)),
        "expected_json_index_path": _display_path(_resolve_path(expected_index_output)),
        "selected_market_ids": index["selected_market_ids"],
        "all_completion_statuses_stub_only": index["completion_statuses"] == ["stub_only"],
    }


def main(argv):
    args = _parse_args(argv)
    summary = write_workpack_artifacts(
        stubs_path=args.stubs,
        markdown_output=args.markdown_output,
        index_output=args.index_output,
        overlay_output=args.overlay_output,
        expected_index_output=args.expected_index_output,
    )
    print(json.dumps(summary, indent=2, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
