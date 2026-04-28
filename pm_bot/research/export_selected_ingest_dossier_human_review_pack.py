import argparse
import json
import sys
from pathlib import Path


TASK_ID = "PMBOT-INGEST-012-SELECTED-INGEST-DOSSIER-HUMAN-REVIEW-PACK"
SCHEMA_VERSION = "selected_ingest_dossier_human_review_pack.v1"
MARKDOWN_VERSION = "selected_ingest_dossier_human_review_pack_markdown.v1"
ROOT = Path(__file__).resolve().parents[2]
DEFAULT_VALIDATION_RESULT = ROOT / "pm_bot" / "research" / "selected_ingest_manual_dossier_draft_validation_result.v1.json"
DEFAULT_DOSSIER_SKELETONS = ROOT / "pm_bot" / "research" / "selected_ingest_dossier_draft_skeletons.v1.json"
DEFAULT_MERGED_PACKETS = ROOT / "pm_bot" / "research" / "selected_ingest_merged_manual_research_packets.v1.json"
DEFAULT_REVIEW_RECORDS_RESULT = ROOT / "pm_bot" / "research" / "selected_ingest_operator_review_records_result.v1.json"
DEFAULT_JSON_OUTPUT = ROOT / "pm_bot" / "research" / "selected_ingest_dossier_human_review_pack.v1.json"
DEFAULT_MARKDOWN_OUTPUT = ROOT / "pm_bot" / "research" / "selected_ingest_dossier_human_review_pack.v1.md"
DEFAULT_EXPECTED_JSON_OUTPUT = ROOT / "pm_bot" / "research" / "expected_selected_ingest_dossier_human_review_pack.v1.json"

SELECTED_MARKET_IDS = ("692258", "824952", "691547", "597964", "598936")
READY_DRAFT_STATUS = "draft_ready_for_human_review"
REVIEW_PACK_STATUS = "human_review_pack_only"
HUMAN_REVIEW_CHECKLIST = (
    "evidence_matches_resolution_criteria",
    "uncertainty_register_reviewed",
    "missing_information_reviewed",
    "no_trading_recommendation_present",
    "no_probability_or_ev_present",
    "no_side_recommendation_present",
    "no_market_decision_present",
)
ALLOWED_REVIEW_OUTCOMES = (
    "approved_for_final_dossier_draft",
    "needs_draft_revision",
    "rejected_for_research_quality",
    "watch_only",
)
PROHIBITED_REVIEW_OUTPUTS = (
    "bet recommendation",
    "trade recommendation",
    "YES/NO side selection",
    "probability estimate",
    "expected value calculation",
    "score/signal",
    "market decision",
    "order/paper order",
)
PROHIBITED_ACCEPTED_DRAFT_FIELD_TOKENS = {
    "order",
    "orders",
    "trade",
    "trades",
    "trading",
    "wallet",
    "wallets",
    "private_key",
    "private_keys",
    "execution",
    "executions",
    "recommendation",
    "recommendations",
    "bet",
    "bets",
    "betting",
    "stake",
    "stakes",
    "size",
    "sizes",
    "entry_price",
    "entry_prices",
    "limit_price",
    "limit_prices",
    "price_target",
    "price_targets",
    "score",
    "scores",
    "signal",
    "signals",
    "probability",
    "probabilities",
    "expected_value",
    "expected_values",
    "ev",
    "side",
    "sides",
    "yes_no_decision",
    "buy",
    "sell",
    "market_decision",
    "market_decisions",
}
PACK_ITEM_FIELDS = (
    "market_id",
    "title_question",
    "event_id",
    "event_title",
    "category",
    "packet_type",
    "deadline",
    "current_yes_price",
    "liquidity",
    "volume",
    "resolution_criteria_summary",
    "market_context_notes",
    "resolution_criteria_notes",
    "evidence_summary_by_source",
    "uncertainty_register",
    "missing_information_review",
    "operator_review_notes",
    "open_questions",
    "human_review_checklist",
    "allowed_review_outcomes",
    "prohibited_review_outputs",
    "review_pack_status",
    "source_ingest_artifacts",
)
SUMMARY_FIELDS = (
    "accepted_drafts_seen",
    "human_review_packs_exported",
    "draft_records_skipped",
    "completed_dossiers_created",
)
def _parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Export deterministic offline selected-ingest dossier human-review packs."
    )
    parser.add_argument("--validation-result", default=str(DEFAULT_VALIDATION_RESULT.relative_to(ROOT)))
    parser.add_argument("--dossier-skeletons", default=str(DEFAULT_DOSSIER_SKELETONS.relative_to(ROOT)))
    parser.add_argument("--merged-packets", default=str(DEFAULT_MERGED_PACKETS.relative_to(ROOT)))
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
    normalized = []
    seen = set()
    for item in value:
        cleaned = _clean_text(item)
        if not cleaned or cleaned in seen:
            continue
        seen.add(cleaned)
        normalized.append(cleaned)
    return normalized


def _selected_sort_key(value):
    if isinstance(value, dict):
        market_id = _clean_text(value.get("market_id"))
        title = _clean_text(value.get("title_question") or value.get("title") or value.get("question"))
        record_index = value.get("record_index", 0)
    else:
        market_id = _clean_text(value)
        title = ""
        record_index = 0
    try:
        selected_index = SELECTED_MARKET_IDS.index(market_id)
    except ValueError:
        selected_index = len(SELECTED_MARKET_IDS)
    return (selected_index, market_id, title, record_index)


def _selected_market_ids_from_payload(payload, payload_name):
    selected_market_ids = tuple(_clean_text(market_id) for market_id in payload.get("selected_market_ids", ()))
    if selected_market_ids != SELECTED_MARKET_IDS:
        raise ValueError(f"{payload_name} has unexpected selected_market_ids")
    return selected_market_ids


def _field_tokens(key):
    normalized = []
    current = []
    for char in str(key).lower():
        if char.isalnum() or char == "_":
            current.append(char)
        else:
            if current:
                normalized.extend("".join(current).split("_"))
                current = []
    if current:
        normalized.extend("".join(current).split("_"))
    return {token for token in normalized if token} | {str(key).lower()}


def _walk_prohibited_accepted_draft_fields(value, prefix=""):
    findings = []
    if isinstance(value, dict):
        for key, nested in value.items():
            key_text = str(key)
            path = f"{prefix}.{key_text}" if prefix else key_text
            if _field_tokens(key_text) & PROHIBITED_ACCEPTED_DRAFT_FIELD_TOKENS:
                findings.append(path)
            findings.extend(_walk_prohibited_accepted_draft_fields(nested, path))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            findings.extend(_walk_prohibited_accepted_draft_fields(item, f"{prefix}[{index}]"))
    return findings


def _assert_no_prohibited_accepted_draft_fields(accepted_records):
    findings = []
    for index, record in enumerate(accepted_records):
        market_id = _clean_text(record.get("market_id")) if isinstance(record, dict) else ""
        for path in _walk_prohibited_accepted_draft_fields(record):
            findings.append((market_id, index, path))
    if findings:
        rendered = "; ".join(f"{market_id or index}:{path}" for market_id, index, path in sorted(findings))
        raise ValueError(f"accepted draft records contain prohibited fields: {rendered}")


def _records_list(payload, field, payload_name):
    records = payload.get(field)
    if not isinstance(records, list):
        raise ValueError(f"{payload_name} must contain {field} list")
    return [record for record in records if isinstance(record, dict)]


def _skeletons_by_market_id(payload):
    _selected_market_ids_from_payload(payload, "selected-ingest dossier skeleton payload")
    skeletons = payload.get("dossier_draft_skeletons")
    if not isinstance(skeletons, list):
        raise ValueError("selected-ingest dossier skeleton payload must contain dossier_draft_skeletons list")

    by_market_id = {}
    for skeleton in skeletons:
        if isinstance(skeleton, dict) and _clean_text(skeleton.get("market_id")):
            market_id = _clean_text(skeleton.get("market_id"))
            if market_id in by_market_id:
                raise ValueError(f"duplicate selected-ingest skeleton market_id: {market_id}")
            by_market_id[market_id] = skeleton
    return by_market_id


def _merged_market_ids(payload):
    _selected_market_ids_from_payload(payload, "selected-ingest merged packet payload")
    packets = payload.get("packets")
    if not isinstance(packets, list):
        raise ValueError("selected-ingest merged packet payload must contain packets list")
    return {
        _clean_text(packet.get("market_id"))
        for packet in packets
        if isinstance(packet, dict) and _clean_text(packet.get("market_id"))
    }


def _review_market_ids(payload):
    _selected_market_ids_from_payload(payload, "selected-ingest operator review result payload")
    records = payload.get("accepted_review_records")
    if not isinstance(records, list):
        raise ValueError("selected-ingest operator review result must contain accepted_review_records list")
    return {
        _clean_text(record.get("market_id"))
        for record in records
        if isinstance(record, dict) and _clean_text(record.get("market_id"))
    }


def _draft_records_read(validation_payload, accepted_records, rejected_records):
    summary = validation_payload.get("draft_validation_summary")
    if isinstance(summary, dict) and isinstance(summary.get("draft_records_read"), int):
        return summary["draft_records_read"]
    return len(accepted_records) + len(rejected_records)


def _source_ingest_artifacts(skeleton):
    artifacts = skeleton.get("source_ingest_artifacts")
    if not isinstance(artifacts, dict):
        return {}
    return {str(key): artifacts[key] for key in sorted(artifacts)}


def _pack_item(record, skeleton):
    item = {
        "market_id": _clean_text(record.get("market_id")),
        "title_question": _clean_text(skeleton.get("title_question")),
        "event_id": _clean_text(skeleton.get("event_id")),
        "event_title": _clean_text(skeleton.get("event_title")),
        "category": _clean_text(skeleton.get("category")),
        "packet_type": _clean_text(skeleton.get("packet_type")),
        "deadline": _clean_text(skeleton.get("deadline")),
        "current_yes_price": skeleton.get("current_yes_price"),
        "liquidity": skeleton.get("liquidity"),
        "volume": skeleton.get("volume"),
        "resolution_criteria_summary": _clean_text(skeleton.get("resolution_criteria_summary")),
        "market_context_notes": _clean_text(record.get("market_context_notes")),
        "resolution_criteria_notes": _clean_text(record.get("resolution_criteria_notes")),
        "evidence_summary_by_source": _string_list(record.get("evidence_summary_by_source")),
        "uncertainty_register": _string_list(record.get("uncertainty_register")),
        "missing_information_review": _clean_text(record.get("missing_information_review")),
        "operator_review_notes": _clean_text(record.get("operator_review_notes")),
        "open_questions": _string_list(record.get("open_questions")),
        "human_review_checklist": list(HUMAN_REVIEW_CHECKLIST),
        "allowed_review_outcomes": list(ALLOWED_REVIEW_OUTCOMES),
        "prohibited_review_outputs": list(PROHIBITED_REVIEW_OUTPUTS),
        "review_pack_status": REVIEW_PACK_STATUS,
        "source_ingest_artifacts": _source_ingest_artifacts(skeleton),
    }
    return {field: item[field] for field in PACK_ITEM_FIELDS}


def _assert_pack_fields(pack_items):
    expected = list(PACK_ITEM_FIELDS)
    for item in pack_items:
        if list(item) != expected:
            raise ValueError(f"selected-ingest human review pack field sequence mismatch for {item.get('market_id', '')}")
        if item["review_pack_status"] != REVIEW_PACK_STATUS:
            raise ValueError(f"invalid review pack status for {item.get('market_id', '')}")


def _build_summary(draft_records_read, accepted_records, pack_items):
    return {
        "accepted_drafts_seen": len(accepted_records),
        "human_review_packs_exported": len(pack_items),
        "draft_records_skipped": draft_records_read - len(pack_items),
        "completed_dossiers_created": 0,
    }


def build_selected_ingest_dossier_human_review_pack_export(
    validation_result_path=DEFAULT_VALIDATION_RESULT,
    dossier_skeletons_path=DEFAULT_DOSSIER_SKELETONS,
    merged_packets_path=DEFAULT_MERGED_PACKETS,
    review_records_result_path=DEFAULT_REVIEW_RECORDS_RESULT,
    json_output_path=DEFAULT_JSON_OUTPUT,
    markdown_output_path=DEFAULT_MARKDOWN_OUTPUT,
    expected_json_output_path=DEFAULT_EXPECTED_JSON_OUTPUT,
):
    validation_result_path = _resolve_path(validation_result_path)
    dossier_skeletons_path = _resolve_path(dossier_skeletons_path)
    merged_packets_path = _resolve_path(merged_packets_path)
    review_records_result_path = _resolve_path(review_records_result_path)
    json_output_path = _resolve_path(json_output_path)
    markdown_output_path = _resolve_path(markdown_output_path)
    expected_json_output_path = _resolve_path(expected_json_output_path)

    validation_payload = _load_json(validation_result_path)
    skeleton_payload = _load_json(dossier_skeletons_path)
    merged_payload = _load_json(merged_packets_path)
    review_payload = _load_json(review_records_result_path)

    _selected_market_ids_from_payload(validation_payload, "selected-ingest draft validation payload")
    accepted_records = _records_list(validation_payload, "accepted_draft_records", "selected-ingest draft validation payload")
    rejected_records = _records_list(validation_payload, "rejected_draft_records", "selected-ingest draft validation payload")
    _assert_no_prohibited_accepted_draft_fields(accepted_records)
    skeleton_by_market_id = _skeletons_by_market_id(skeleton_payload)
    merged_market_ids = _merged_market_ids(merged_payload)
    review_market_ids = _review_market_ids(review_payload)
    draft_records_read = _draft_records_read(validation_payload, accepted_records, rejected_records)

    pack_items = []
    for record in sorted(accepted_records, key=_selected_sort_key):
        if _clean_text(record.get("draft_status")) != READY_DRAFT_STATUS:
            continue
        market_id = _clean_text(record.get("market_id"))
        if market_id not in skeleton_by_market_id:
            raise ValueError(f"ready accepted selected-ingest draft is missing dossier skeleton context: {market_id}")
        if market_id not in merged_market_ids:
            raise ValueError(f"ready accepted selected-ingest draft is missing merged packet context: {market_id}")
        if market_id not in review_market_ids:
            raise ValueError(f"ready accepted selected-ingest draft is missing operator review context: {market_id}")
        pack_items.append(_pack_item(record, skeleton_by_market_id[market_id]))

    pack_items.sort(key=_selected_sort_key)
    _assert_pack_fields(pack_items)
    summary = _build_summary(draft_records_read, accepted_records, pack_items)

    return {
        "schema_version": SCHEMA_VERSION,
        "markdown_version": MARKDOWN_VERSION,
        "task_id": TASK_ID,
        "deterministic": True,
        "source_validation_result_path": _display_path(validation_result_path),
        "source_validation_result_schema_version": validation_payload.get("schema_version"),
        "source_dossier_skeletons_path": _display_path(dossier_skeletons_path),
        "source_dossier_skeletons_schema_version": skeleton_payload.get("schema_version"),
        "source_merged_packets_path": _display_path(merged_packets_path),
        "source_merged_packets_schema_version": merged_payload.get("schema_version"),
        "source_review_records_result_path": _display_path(review_records_result_path),
        "source_review_records_result_schema_version": review_payload.get("schema_version"),
        "json_output_path": _display_path(json_output_path),
        "markdown_output_path": _display_path(markdown_output_path),
        "expected_json_output_path": _display_path(expected_json_output_path),
        "selected_market_ids": list(SELECTED_MARKET_IDS),
        "human_review_pack_item_fields": list(PACK_ITEM_FIELDS),
        "human_review_checklist": list(HUMAN_REVIEW_CHECKLIST),
        "allowed_review_outcomes": list(ALLOWED_REVIEW_OUTCOMES),
        "prohibited_review_outputs": list(PROHIBITED_REVIEW_OUTPUTS),
        "export_summary": summary,
        "exported_market_ids": [item["market_id"] for item in pack_items],
        "human_review_packs": pack_items,
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
    lines = [
        "# Selected Ingest Dossier Human Review Pack v1",
        "",
        "## Summary",
        "",
        f"- task_id: {export_payload['task_id']}",
        f"- source_validation_result_path: {export_payload['source_validation_result_path']}",
        f"- source_dossier_skeletons_path: {export_payload['source_dossier_skeletons_path']}",
        f"- source_merged_packets_path: {export_payload['source_merged_packets_path']}",
        f"- source_review_records_result_path: {export_payload['source_review_records_result_path']}",
    ]
    for field in SUMMARY_FIELDS:
        lines.append(f"- {field}: {summary[field]}")
    lines.extend(["- exported_market_ids:"])
    lines.extend(_render_nested_list(export_payload["exported_market_ids"]))

    lines.extend(["", "## Selected Market IDs", ""])
    lines.extend(_render_list(export_payload["selected_market_ids"]))

    lines.extend(["", "## Human Review Packs", ""])
    if not export_payload["human_review_packs"]:
        lines.extend(["- none", ""])
    else:
        for item in export_payload["human_review_packs"]:
            lines.extend(
                [
                    f"### {item['market_id']}",
                    f"- title/question: {item['title_question']}",
                    f"- event_id: {item['event_id']}",
                    f"- event_title: {item['event_title']}",
                    f"- category: {item['category']}",
                    f"- packet_type: {item['packet_type']}",
                    f"- deadline: {item['deadline']}",
                    f"- current_yes_price: {_render_scalar(item['current_yes_price'])}",
                    f"- liquidity: {_render_scalar(item['liquidity'])}",
                    f"- volume: {_render_scalar(item['volume'])}",
                    f"- resolution_criteria_summary: {item['resolution_criteria_summary']}",
                    f"- review_pack_status: {item['review_pack_status']}",
                    "",
                    "#### Review Notes",
                    "",
                    f"- market_context_notes: {item['market_context_notes']}",
                    f"- resolution_criteria_notes: {item['resolution_criteria_notes']}",
                    f"- missing_information_review: {item['missing_information_review']}",
                    f"- operator_review_notes: {item['operator_review_notes']}",
                    "",
                    "#### Evidence Summary By Source",
                    "",
                ]
            )
            lines.extend(_render_list(item["evidence_summary_by_source"]))
            lines.extend(["", "#### Uncertainty Register", ""])
            lines.extend(_render_list(item["uncertainty_register"]))
            lines.extend(["", "#### Open Questions", ""])
            lines.extend(_render_list(item["open_questions"]))
            lines.extend(["", "#### Human Review Checklist", ""])
            lines.extend(_render_list(item["human_review_checklist"]))
            lines.extend(["", "#### Allowed Review Outcomes", ""])
            lines.extend(_render_list(item["allowed_review_outcomes"]))
            lines.extend(["", "#### Prohibited Review Outputs", ""])
            lines.extend(_render_list(item["prohibited_review_outputs"]))
            lines.extend(["", "#### Source Ingest Artifacts", ""])
            if not item["source_ingest_artifacts"]:
                lines.extend(["- none", ""])
            else:
                for key, value in item["source_ingest_artifacts"].items():
                    lines.append(f"- {key}: {value}")
                lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def write_selected_ingest_dossier_human_review_pack_artifacts(
    validation_result_path=DEFAULT_VALIDATION_RESULT,
    dossier_skeletons_path=DEFAULT_DOSSIER_SKELETONS,
    merged_packets_path=DEFAULT_MERGED_PACKETS,
    review_records_result_path=DEFAULT_REVIEW_RECORDS_RESULT,
    json_output_path=DEFAULT_JSON_OUTPUT,
    markdown_output_path=DEFAULT_MARKDOWN_OUTPUT,
    expected_json_output_path=DEFAULT_EXPECTED_JSON_OUTPUT,
):
    json_output_path = _resolve_path(json_output_path)
    markdown_output_path = _resolve_path(markdown_output_path)
    expected_json_output_path = _resolve_path(expected_json_output_path)
    export_payload = build_selected_ingest_dossier_human_review_pack_export(
        validation_result_path=validation_result_path,
        dossier_skeletons_path=dossier_skeletons_path,
        merged_packets_path=merged_packets_path,
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
    summary = write_selected_ingest_dossier_human_review_pack_artifacts(
        validation_result_path=args.validation_result,
        dossier_skeletons_path=args.dossier_skeletons,
        merged_packets_path=args.merged_packets,
        review_records_result_path=args.review_records_result,
        json_output_path=args.json_output,
        markdown_output_path=args.markdown_output,
        expected_json_output_path=args.expected_json_output,
    )
    print(json.dumps(summary, indent=2, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
