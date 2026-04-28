import argparse
import importlib.util
import json
import sys
from pathlib import Path


TASK_ID = "PMBOT-RESEARCH-008-OPERATOR-RESEARCH-WORKPACK-EXPORT"
SCHEMA_VERSION = "operator_research_workpack_index.v1"
WORKPACK_VERSION = "operator_research_workpack.v1"
ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PACKET_STUBS = ROOT / "pm_bot" / "research" / "expected_research_packet_stubs.v1.json"
DEFAULT_MARKDOWN_WORKPACK = ROOT / "pm_bot" / "research" / "operator_research_workpack.v1.md"
DEFAULT_JSON_INDEX = ROOT / "pm_bot" / "research" / "operator_research_workpack_index.v1.json"
DEFAULT_EXPECTED_JSON_INDEX = ROOT / "pm_bot" / "research" / "expected_operator_research_workpack_index.v1.json"
VALIDATOR_PATH = ROOT / "pm_bot" / "research" / "validate_manual_research_packets.py"


REQUIRED_OPERATOR_FIELDS = (
    "market_id",
    "title_question",
    "category",
    "packet_type",
    "current_yes_price",
    "liquidity",
    "deadline",
    "resolution_criteria_summary",
    "why_selected_for_research",
    "why_not_bet_yet",
    "source_plan",
    "search_queries",
    "official_sources_to_check",
    "credible_news_sources_to_check",
    "blank_evidence_capture_template",
    "missing_information_checklist",
    "completion_status",
)

OPERATOR_SAFE_TEXT_REPLACEMENTS = (
    ("official_docket_or_order_identifier", "official_docket_identifier"),
    ("filings or orders", "filings or docket entries"),
    ("orders matching", "docket entries matching"),
    ("order lists", "docket lists"),
    ("order list", "docket list"),
)


def _parse_args(argv):
    parser = argparse.ArgumentParser(description="Export deterministic offline PMBOT operator research workpack artifacts.")
    parser.add_argument("--packet-stubs", default=str(DEFAULT_PACKET_STUBS.relative_to(ROOT)))
    parser.add_argument("--markdown-output", default=str(DEFAULT_MARKDOWN_WORKPACK.relative_to(ROOT)))
    parser.add_argument("--json-index-output", default=str(DEFAULT_JSON_INDEX.relative_to(ROOT)))
    parser.add_argument("--expected-json-index-output", default=str(DEFAULT_EXPECTED_JSON_INDEX.relative_to(ROOT)))
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
        "schema_version": module.SCHEMA_VERSION,
        "allowed_completion_statuses": sorted(module.ALLOWED_COMPLETION_STATUSES),
        "expected_evidence_slots": list(module.EXPECTED_EVIDENCE_SLOTS),
        "required_evidence_fields": list(module.REQUIRED_EVIDENCE_FIELDS),
    }


def _blank_evidence_template(required_evidence_fields):
    return {field: "" for field in required_evidence_fields}


def _operator_safe_text(value):
    if value is None:
        return None
    text = str(value)
    for old, new in OPERATOR_SAFE_TEXT_REPLACEMENTS:
        text = text.replace(old, new)
    return text


def _operator_safe_list(items):
    return [_operator_safe_text(item) for item in items]


def _packet_sort_key(packet):
    rank = packet.get("shortlist_rank")
    rank_key = rank if isinstance(rank, int) else 10**9
    return (rank_key, str(packet.get("market_id") or ""), str(packet.get("title") or packet.get("question") or ""))


def _load_packet_stubs(packet_stubs_path):
    payload = _load_json(packet_stubs_path)
    packet_stubs = payload.get("packet_stubs")
    if not isinstance(packet_stubs, list):
        raise ValueError("packet stubs payload must contain a packet_stubs list")
    return payload, sorted(packet_stubs, key=_packet_sort_key)


def _market_entry(packet, required_evidence_fields):
    title = str(packet.get("title") or packet.get("question") or "").strip()
    question = str(packet.get("question") or title).strip()
    title_question = question or title
    return {
        "shortlist_rank": packet.get("shortlist_rank"),
        "market_id": str(packet.get("market_id") or "").strip(),
        "heading": f"## Market {str(packet.get('market_id') or '').strip()}",
        "title_question": _operator_safe_text(title_question),
        "category": _operator_safe_text(packet.get("category")),
        "packet_type": _operator_safe_text(packet.get("packet_type")),
        "current_yes_price": packet.get("current_yes_price"),
        "liquidity": packet.get("liquidity"),
        "deadline": _operator_safe_text(packet.get("deadline")),
        "resolution_criteria_summary": _operator_safe_text(packet.get("resolution_criteria_summary")),
        "why_selected_for_research": _operator_safe_text(packet.get("why_selected_for_research")),
        "why_not_bet_yet": _operator_safe_text(packet.get("why_not_bet_yet")),
        "source_plan": _operator_safe_text(packet.get("source_plan")),
        "search_queries": _operator_safe_list(packet.get("search_queries") or []),
        "official_sources_to_check": _operator_safe_list(packet.get("official_sources_to_check") or []),
        "credible_news_sources_to_check": _operator_safe_list(packet.get("credible_news_sources_to_check") or []),
        "blank_evidence_capture_template": _blank_evidence_template(required_evidence_fields),
        "missing_information_checklist": _operator_safe_list(packet.get("missing_information") or []),
        "completion_status": _operator_safe_text(packet.get("completion_status")),
    }


def build_workpack_index(packet_stubs_path=DEFAULT_PACKET_STUBS, markdown_output_path=DEFAULT_MARKDOWN_WORKPACK, json_index_output_path=DEFAULT_JSON_INDEX):
    packet_stubs_path = _resolve_path(packet_stubs_path)
    markdown_output_path = _resolve_path(markdown_output_path)
    json_index_output_path = _resolve_path(json_index_output_path)
    stubs_payload, packet_stubs = _load_packet_stubs(packet_stubs_path)
    validator_contract = _load_validator_contract()
    required_evidence_fields = validator_contract["required_evidence_fields"]
    markets = [_market_entry(packet, required_evidence_fields) for packet in packet_stubs]
    market_ids = [market["market_id"] for market in markets]
    completion_statuses = sorted({market["completion_status"] for market in markets})

    return {
        "schema_version": SCHEMA_VERSION,
        "workpack_version": WORKPACK_VERSION,
        "task_id": TASK_ID,
        "deterministic": True,
        "source_packet_stubs_path": _display_path(packet_stubs_path),
        "source_packet_stubs_schema_version": stubs_payload.get("schema_version"),
        "validator_contract_path": _display_path(VALIDATOR_PATH),
        "validator_contract_schema_version": validator_contract["schema_version"],
        "allowed_completion_statuses": validator_contract["allowed_completion_statuses"],
        "expected_evidence_slots": validator_contract["expected_evidence_slots"],
        "required_evidence_fields": required_evidence_fields,
        "required_operator_fields": list(REQUIRED_OPERATOR_FIELDS),
        "markdown_workpack_path": _display_path(markdown_output_path),
        "json_index_path": _display_path(json_index_output_path),
        "export_count": len(markets),
        "market_ids": market_ids,
        "completion_statuses": completion_statuses,
        "markets": markets,
    }


def _render_list(items):
    if not items:
        return ["- "]
    return [f"- {item}" for item in items]


def _render_blank_evidence_template(template):
    return [f"- {field}: {value}" for field, value in template.items()]


def render_markdown_workpack(index):
    lines = [
        "# PMBOT Operator Research Workpack v1",
        "",
        f"- task_id: {index['task_id']}",
        f"- source_packet_stubs_path: {index['source_packet_stubs_path']}",
        f"- validator_contract_path: {index['validator_contract_path']}",
        f"- packets_exported: {index['export_count']}",
        "- completion_status: stub_only",
        f"- evidence_template_fields: {', '.join(index['required_evidence_fields'])}",
        "",
        "Evidence templates are intentionally blank. This workpack is for manual collection only and does not contain completed dossiers, scoring, truth inference, live data collection, or runtime changes.",
        "",
    ]

    for market in index["markets"]:
        lines.extend(
            [
                market["heading"],
                "",
                "### Market Details",
                f"- market_id: {market['market_id']}",
                f"- title/question: {market['title_question']}",
                f"- category: {market['category']}",
                f"- packet_type: {market['packet_type']}",
                f"- current_yes_price: {market['current_yes_price']}",
                f"- liquidity: {market['liquidity']}",
                f"- deadline: {market['deadline']}",
                f"- completion_status: {market['completion_status']}",
                "",
                "### Resolution Criteria Summary",
                str(market["resolution_criteria_summary"] or ""),
                "",
                "### Why Selected For Research",
                str(market["why_selected_for_research"] or ""),
                "",
                "### Why Not Bet Yet",
                str(market["why_not_bet_yet"] or ""),
                "",
                "### Source Plan",
                str(market["source_plan"] or ""),
                "",
                "### Search Queries",
            ]
        )
        lines.extend(_render_list(market["search_queries"]))
        lines.extend(["", "### Official Sources To Check"])
        lines.extend(_render_list(market["official_sources_to_check"]))
        lines.extend(["", "### Credible News Sources To Check"])
        lines.extend(_render_list(market["credible_news_sources_to_check"]))
        lines.extend(["", "### Blank Evidence Capture Template"])
        lines.extend(_render_blank_evidence_template(market["blank_evidence_capture_template"]))
        lines.extend(["", "### Missing Information Checklist"])
        lines.extend([f"- [ ] {item}" for item in market["missing_information_checklist"]])
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def write_workpack_artifacts(packet_stubs_path=DEFAULT_PACKET_STUBS, markdown_output_path=DEFAULT_MARKDOWN_WORKPACK, json_index_output_path=DEFAULT_JSON_INDEX, expected_json_index_output_path=DEFAULT_EXPECTED_JSON_INDEX):
    markdown_output_path = _resolve_path(markdown_output_path)
    json_index_output_path = _resolve_path(json_index_output_path)
    expected_json_index_output_path = _resolve_path(expected_json_index_output_path)
    index = build_workpack_index(packet_stubs_path, markdown_output_path, json_index_output_path)
    rendered_index = json.dumps(index, indent=2, ensure_ascii=True) + "\n"
    rendered_markdown = render_markdown_workpack(index)

    markdown_output_path.parent.mkdir(parents=True, exist_ok=True)
    json_index_output_path.parent.mkdir(parents=True, exist_ok=True)
    expected_json_index_output_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_output_path.write_text(rendered_markdown, encoding="utf-8")
    json_index_output_path.write_text(rendered_index, encoding="utf-8")
    expected_json_index_output_path.write_text(rendered_index, encoding="utf-8")
    return {
        "task_id": TASK_ID,
        "packets_exported": index["export_count"],
        "markdown_workpack_path": _display_path(markdown_output_path),
        "json_index_path": _display_path(json_index_output_path),
        "expected_json_index_path": _display_path(expected_json_index_output_path),
        "all_completion_statuses_stub_only": index["completion_statuses"] == ["stub_only"],
    }


def main(argv):
    args = _parse_args(argv)
    summary = write_workpack_artifacts(
        packet_stubs_path=args.packet_stubs,
        markdown_output_path=args.markdown_output,
        json_index_output_path=args.json_index_output,
        expected_json_index_output_path=args.expected_json_index_output,
    )
    print(json.dumps(summary, indent=2, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
