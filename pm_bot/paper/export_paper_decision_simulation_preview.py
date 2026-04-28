import argparse
import json
import sys
from pathlib import Path


TASK_ID = "PMBOT-PAPER-003-PAPER-DECISION-SIMULATION-PREVIEW"
SCHEMA_VERSION = "paper_decision_simulation_preview.v1"
MARKDOWN_VERSION = "paper_decision_simulation_preview_report.v1"
ROOT = Path(__file__).resolve().parents[2]
DEFAULT_POLICY_REVIEW_RESULT = ROOT / "pm_bot" / "paper" / "paper_policy_review_result.v1.json"
DEFAULT_READINESS_RESULT = ROOT / "pm_bot" / "paper" / "final_dossier_paper_readiness_result.v1.json"
DEFAULT_FINAL_DOSSIER_DRAFTS = ROOT / "pm_bot" / "research" / "selected_ingest_final_dossier_drafts.v1.json"
DEFAULT_JSON_OUTPUT = ROOT / "pm_bot" / "paper" / "paper_decision_simulation_preview.v1.json"
DEFAULT_MARKDOWN_OUTPUT = ROOT / "pm_bot" / "paper" / "paper_decision_simulation_preview.v1.md"
DEFAULT_EXPECTED_JSON_OUTPUT = ROOT / "pm_bot" / "paper" / "expected_paper_decision_simulation_preview.v1.json"

ELIGIBLE_POLICY_STATUS = "eligible_for_future_paper_decision_simulation"
ELIGIBLE_READINESS_STATUS = "eligible_for_future_paper_policy_review"
READY_STATUS = "ready_for_future_paper_decision_policy_design"
NEEDS_MORE_STATUS = "needs_more_manual_review"
BLOCKED_STATUS = "blocked_by_policy"
ALLOWED_SIMULATION_PREVIEW_STATUSES = (
    READY_STATUS,
    NEEDS_MORE_STATUS,
    BLOCKED_STATUS,
)
NEXT_MANUAL_ACTIONS = {
    READY_STATUS: "design_paper_decision_policy",
    NEEDS_MORE_STATUS: "add_manual_review",
    BLOCKED_STATUS: "stop_policy_blocked",
}
PROHIBITED_FIELD_NAMES = (
    "order",
    "trade",
    "wallet",
    "private_key",
    "execution",
    "recommendation",
    "bet",
    "stake",
    "size",
    "entry_price",
    "limit_price",
    "price_target",
    "score",
    "signal",
    "probability",
    "expected_value",
    "ev",
    "side",
    "yes_no_decision",
    "buy",
    "sell",
    "market_decision",
)
PROHIBITED_FIELD_TOKENS = set(PROHIBITED_FIELD_NAMES) | {
    "orders",
    "trades",
    "trading",
    "wallets",
    "private_keys",
    "executions",
    "recommendations",
    "bets",
    "betting",
    "stakes",
    "sizes",
    "entry_prices",
    "limit_prices",
    "price_targets",
    "scores",
    "signals",
    "probabilities",
    "expected_values",
    "sides",
    "market_decisions",
}
PREVIEW_ITEM_FIELDS = (
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
    "evidence_inventory_summary",
    "uncertainty_register_summary",
    "missing_information_review",
    "open_questions",
    "human_review_summary",
    "paper_readiness_status",
    "paper_policy_status",
    "simulation_preview_status",
    "blocked_reasons",
    "next_manual_action",
)
SUMMARY_FIELDS = (
    "policy_records_read",
    "preview_records_written",
    READY_STATUS,
    NEEDS_MORE_STATUS,
    BLOCKED_STATUS,
    "paper_orders_created",
)


def _parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Export a deterministic offline paper decision simulation preview."
    )
    parser.add_argument("--policy-review-result", default=str(DEFAULT_POLICY_REVIEW_RESULT.relative_to(ROOT)))
    parser.add_argument("--readiness-result", default=str(DEFAULT_READINESS_RESULT.relative_to(ROOT)))
    parser.add_argument("--final-dossier-drafts", default=str(DEFAULT_FINAL_DOSSIER_DRAFTS.relative_to(ROOT)))
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


def _source_artifact_label(path):
    resolved = Path(path).resolve()
    if resolved == DEFAULT_POLICY_REVIEW_RESULT.resolve():
        return "pm_bot/paper paper-policy-review result artifact"
    if resolved == DEFAULT_READINESS_RESULT.resolve():
        return "pm_bot/paper final dossier paper-readiness result artifact"
    if resolved == DEFAULT_FINAL_DOSSIER_DRAFTS.resolve():
        return "pm_bot/research selected-ingest final dossier drafts artifact"
    return _display_path(path)


def _load_json(path):
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _clean_text(value):
    if value is None:
        return ""
    return str(value).strip()


def _records_list(payload, field):
    records = payload.get(field)
    if not isinstance(records, list):
        raise ValueError(f"payload must contain {field} list")
    return [record for record in records if isinstance(record, dict)]


def _by_market_id(records):
    by_market_id = {}
    for record in records:
        market_id = _clean_text(record.get("market_id"))
        if market_id:
            by_market_id[market_id] = record
    return by_market_id


def _list_field(value):
    if isinstance(value, list):
        return list(value)
    return []


def _string_list(value):
    if isinstance(value, list):
        return [_clean_text(item) for item in value if _clean_text(item)]
    if _clean_text(value):
        return [_clean_text(value)]
    return []


def _field_tokens(key):
    lower = str(key).lower()
    normalized_chars = []
    previous_was_separator = False
    for char in lower:
        if char.isalnum():
            normalized_chars.append(char)
            previous_was_separator = False
        elif not previous_was_separator:
            normalized_chars.append("_")
            previous_was_separator = True
    normalized_key = "".join(normalized_chars).strip("_")
    parts = [part for part in normalized_key.split("_") if part]
    tokens = {lower, normalized_key}
    tokens.update(parts)
    for index in range(len(parts) - 1):
        tokens.add(f"{parts[index]}_{parts[index + 1]}")
    for index in range(len(parts) - 2):
        tokens.add(f"{parts[index]}_{parts[index + 1]}_{parts[index + 2]}")
    return {token for token in tokens if token}


def _matched_prohibited_tokens(key):
    return sorted(_field_tokens(key) & PROHIBITED_FIELD_TOKENS)


def _walk_prohibited_fields(value, prefix=""):
    findings = []
    if isinstance(value, dict):
        for key, nested in value.items():
            key_text = str(key)
            path = f"{prefix}.{key_text}" if prefix else key_text
            for token in _matched_prohibited_tokens(key_text):
                findings.append(
                    {
                        "path": path,
                        "field": key_text,
                        "matched_token": token,
                    }
                )
            findings.extend(_walk_prohibited_fields(nested, path))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            findings.extend(_walk_prohibited_fields(item, f"{prefix}[{index}]"))
    return sorted(findings, key=lambda item: (item["path"], item["matched_token"], item["field"]))


def _paper_policy_status(policy_record):
    for field in ("policy_status", "future_policy_status", "paper_policy_status"):
        status = _clean_text(policy_record.get(field))
        if status:
            return status
    return ""


def _title_question(draft):
    sections = draft.get("final_draft_sections")
    if isinstance(sections, dict):
        overview = sections.get("market_overview")
        if isinstance(overview, dict) and _clean_text(overview.get("title_question")):
            return _clean_text(overview.get("title_question"))
    for field in ("title_question", "question", "title"):
        value = _clean_text(draft.get(field))
        if value:
            return value
    return ""


def _market_overview_field(draft, field):
    sections = draft.get("final_draft_sections")
    if isinstance(sections, dict):
        overview = sections.get("market_overview")
        if isinstance(overview, dict) and field in overview:
            return overview.get(field)
    return draft.get(field)


def _human_review_summary(draft):
    sections = draft.get("final_draft_sections")
    if isinstance(sections, dict):
        summary = sections.get("human_review_summary")
        if isinstance(summary, dict) and _clean_text(summary.get("human_review_notes")):
            return _clean_text(summary.get("human_review_notes"))
    return _clean_text(draft.get("human_review_notes"))


def _missing_preview_fields(preview_item):
    missing = []
    for field in PREVIEW_ITEM_FIELDS:
        if field in {"blocked_reasons", "open_questions", "simulation_preview_status", "next_manual_action"}:
            continue
        value = preview_item.get(field)
        if field in {"evidence_inventory_summary", "uncertainty_register_summary"}:
            if not isinstance(value, list) or not value:
                missing.append(field)
            continue
        if value is None or _clean_text(value) == "":
            missing.append(field)
    if not isinstance(preview_item.get("open_questions"), list):
        missing.append("open_questions")
    if not isinstance(preview_item.get("blocked_reasons"), list):
        missing.append("blocked_reasons")
    return sorted(missing)


def _blocked_reasons(policy_record, readiness_record, draft, policy_status):
    reasons = []
    if policy_status != ELIGIBLE_POLICY_STATUS:
        reasons.append("paper_policy_status_not_eligible")
    if _clean_text(policy_record.get("record_validation_status")) != "accepted":
        reasons.append("paper_policy_record_not_accepted")
    if not isinstance(readiness_record, dict):
        reasons.append("paper_readiness_record_missing")
    elif _clean_text(readiness_record.get("readiness_status")) != ELIGIBLE_READINESS_STATUS:
        reasons.append("paper_readiness_status_not_eligible")
    if not isinstance(draft, dict):
        reasons.append("final_dossier_draft_missing")
    if _walk_prohibited_fields(policy_record):
        reasons.append("prohibited_field_name_in_policy_record")
    if isinstance(draft, dict) and _walk_prohibited_fields(draft):
        reasons.append("prohibited_field_name_in_final_dossier_draft")
    return sorted(set(reasons))


def _preview_status(policy_record, readiness_record, draft, preview_item, policy_status):
    blocked_reasons = _blocked_reasons(policy_record, readiness_record, draft, policy_status)
    if blocked_reasons:
        return BLOCKED_STATUS, blocked_reasons
    missing_fields = _missing_preview_fields(preview_item)
    if missing_fields:
        return NEEDS_MORE_STATUS, [f"missing_preview_field:{field}" for field in missing_fields]
    return READY_STATUS, []


def _preview_item(policy_record, readiness_record, draft):
    policy_status = _paper_policy_status(policy_record)
    if not isinstance(draft, dict):
        draft = {}
    item = {
        "market_id": _clean_text(policy_record.get("market_id")),
        "title_question": _title_question(draft),
        "event_id": _clean_text(_market_overview_field(draft, "event_id")),
        "event_title": _clean_text(_market_overview_field(draft, "event_title")),
        "category": _clean_text(_market_overview_field(draft, "category")),
        "packet_type": _clean_text(_market_overview_field(draft, "packet_type")),
        "deadline": _clean_text(_market_overview_field(draft, "deadline")),
        "current_yes_price": _market_overview_field(draft, "current_yes_price"),
        "liquidity": _market_overview_field(draft, "liquidity"),
        "volume": _market_overview_field(draft, "volume"),
        "resolution_criteria_summary": _clean_text(draft.get("resolution_criteria_summary")),
        "evidence_inventory_summary": _string_list(draft.get("evidence_summary_by_source")),
        "uncertainty_register_summary": _string_list(draft.get("uncertainty_register")),
        "missing_information_review": _clean_text(draft.get("missing_information_review")),
        "open_questions": _list_field(draft.get("open_questions")),
        "human_review_summary": _human_review_summary(draft),
        "paper_readiness_status": (
            _clean_text(readiness_record.get("readiness_status")) if isinstance(readiness_record, dict) else ""
        ),
        "paper_policy_status": policy_status,
        "simulation_preview_status": "",
        "blocked_reasons": [],
        "next_manual_action": "",
    }
    status, blocked_reasons = _preview_status(policy_record, readiness_record, draft, item, policy_status)
    item["simulation_preview_status"] = status
    item["blocked_reasons"] = blocked_reasons
    item["next_manual_action"] = NEXT_MANUAL_ACTIONS[status]
    return item


def _build_summary(policy_records_read, preview_records):
    summary = {
        "policy_records_read": policy_records_read,
        "preview_records_written": len(preview_records),
        READY_STATUS: 0,
        NEEDS_MORE_STATUS: 0,
        BLOCKED_STATUS: 0,
        "paper_orders_created": 0,
    }
    for record in preview_records:
        status = record["simulation_preview_status"]
        if status in ALLOWED_SIMULATION_PREVIEW_STATUSES:
            summary[status] += 1
    return summary


def build_paper_decision_simulation_preview(
    policy_review_result_path=DEFAULT_POLICY_REVIEW_RESULT,
    readiness_result_path=DEFAULT_READINESS_RESULT,
    final_dossier_drafts_path=DEFAULT_FINAL_DOSSIER_DRAFTS,
    json_output_path=DEFAULT_JSON_OUTPUT,
    markdown_output_path=DEFAULT_MARKDOWN_OUTPUT,
    expected_json_output_path=DEFAULT_EXPECTED_JSON_OUTPUT,
):
    policy_review_result_path = _resolve_path(policy_review_result_path)
    readiness_result_path = _resolve_path(readiness_result_path)
    final_dossier_drafts_path = _resolve_path(final_dossier_drafts_path)
    json_output_path = _resolve_path(json_output_path)
    markdown_output_path = _resolve_path(markdown_output_path)
    expected_json_output_path = _resolve_path(expected_json_output_path)

    policy_payload = _load_json(policy_review_result_path)
    readiness_payload = _load_json(readiness_result_path)
    drafts_payload = _load_json(final_dossier_drafts_path)

    policy_records = _records_list(policy_payload, "policy_records")
    readiness_by_market_id = _by_market_id(_records_list(readiness_payload, "readiness_records"))
    drafts_by_market_id = _by_market_id(_records_list(drafts_payload, "final_dossier_drafts"))

    preview_records = []
    for policy_record in policy_records:
        if _paper_policy_status(policy_record) != ELIGIBLE_POLICY_STATUS:
            continue
        market_id = _clean_text(policy_record.get("market_id"))
        preview_records.append(
            _preview_item(
                policy_record,
                readiness_by_market_id.get(market_id),
                drafts_by_market_id.get(market_id),
            )
        )
    preview_records.sort(key=lambda item: item["market_id"])
    summary = _build_summary(len(policy_records), preview_records)
    market_ids = sorted(
        record["market_id"]
        for record in preview_records
        if record["market_id"] and record["simulation_preview_status"] == READY_STATUS
    )

    return {
        "schema_version": SCHEMA_VERSION,
        "markdown_version": MARKDOWN_VERSION,
        "task_id": TASK_ID,
        "deterministic": True,
        "source_policy_review_result_path": _source_artifact_label(policy_review_result_path),
        "source_policy_review_result_schema_version": _clean_text(policy_payload.get("schema_version")),
        "source_readiness_result_path": _source_artifact_label(readiness_result_path),
        "source_readiness_result_schema_version": _clean_text(readiness_payload.get("schema_version")),
        "source_final_dossier_drafts_path": _source_artifact_label(final_dossier_drafts_path),
        "source_final_dossier_drafts_schema_version": _clean_text(drafts_payload.get("schema_version")),
        "json_output_path": _display_path(json_output_path),
        "markdown_output_path": _display_path(markdown_output_path),
        "expected_json_output_path": _display_path(expected_json_output_path),
        "accepted_paper_policy_status": ELIGIBLE_POLICY_STATUS,
        "allowed_simulation_preview_statuses": list(ALLOWED_SIMULATION_PREVIEW_STATUSES),
        "allowed_next_manual_actions": [NEXT_MANUAL_ACTIONS[status] for status in ALLOWED_SIMULATION_PREVIEW_STATUSES],
        "preview_item_fields": list(PREVIEW_ITEM_FIELDS),
        "preview_summary": summary,
        "market_ids": market_ids,
        "preview_records": preview_records,
        "limitations": [
            "Reads only local paper-policy-review, paper-readiness, and selected-ingest final dossier draft artifacts.",
            "ready_for_future_paper_decision_policy_design only means a future paper-only policy module may be designed.",
            "This preview does not create a paper decision, choose YES or NO, recommend any action, score the market, calculate probability, calculate expected value, or create paper orders.",
        ],
    }


def _render_nested_list(items):
    if not items:
        return ["  - none"]
    return [f"  - {item}" for item in items]


def render_markdown_report(payload):
    summary = payload["preview_summary"]
    lines = [
        "# PMBOT Paper Decision Simulation Preview v1",
        "",
        "## Summary",
        "",
        f"- task_id: {payload['task_id']}",
        f"- source_policy_review_result_path: {payload['source_policy_review_result_path']}",
        f"- source_readiness_result_path: {payload['source_readiness_result_path']}",
        f"- source_final_dossier_drafts_path: {payload['source_final_dossier_drafts_path']}",
    ]
    for field in SUMMARY_FIELDS:
        lines.append(f"- {field}: {summary[field]}")
    lines.extend(["- market_ids:"])
    lines.extend(_render_nested_list(payload["market_ids"]))
    lines.extend(
        [
            "- interpretation: ready_for_future_paper_decision_policy_design only permits future paper-policy design and does not authorize paper orders or a market decision.",
            "",
            "## Preview Records",
            "",
        ]
    )

    if not payload["preview_records"]:
        lines.extend(["- none", ""])
    else:
        for record in payload["preview_records"]:
            lines.extend(
                [
                    f"### {record['market_id'] or 'missing-market-id'}",
                    f"- title_question: {record['title_question']}",
                    f"- event_id: {record['event_id']}",
                    f"- event_title: {record['event_title']}",
                    f"- category: {record['category']}",
                    f"- packet_type: {record['packet_type']}",
                    f"- deadline: {record['deadline']}",
                    f"- current_yes_price: {record['current_yes_price']}",
                    f"- liquidity: {record['liquidity']}",
                    f"- volume: {record['volume']}",
                    f"- paper_readiness_status: {record['paper_readiness_status']}",
                    f"- paper_policy_status: {record['paper_policy_status']}",
                    f"- simulation_preview_status: {record['simulation_preview_status']}",
                    f"- next_manual_action: {record['next_manual_action']}",
                    "- blocked_reasons:",
                ]
            )
            lines.extend(_render_nested_list(record["blocked_reasons"]))
            lines.extend(["- open_questions:"])
            lines.extend(_render_nested_list(record["open_questions"]))
            lines.append("")

    lines.extend(["## Limitations", ""])
    for item in payload["limitations"]:
        lines.append(f"- {item}")
    return "\n".join(lines).rstrip() + "\n"


def write_paper_decision_simulation_preview_artifacts(
    policy_review_result_path=DEFAULT_POLICY_REVIEW_RESULT,
    readiness_result_path=DEFAULT_READINESS_RESULT,
    final_dossier_drafts_path=DEFAULT_FINAL_DOSSIER_DRAFTS,
    json_output_path=DEFAULT_JSON_OUTPUT,
    markdown_output_path=DEFAULT_MARKDOWN_OUTPUT,
    expected_json_output_path=DEFAULT_EXPECTED_JSON_OUTPUT,
):
    json_output_path = _resolve_path(json_output_path)
    markdown_output_path = _resolve_path(markdown_output_path)
    expected_json_output_path = _resolve_path(expected_json_output_path)
    payload = build_paper_decision_simulation_preview(
        policy_review_result_path=policy_review_result_path,
        readiness_result_path=readiness_result_path,
        final_dossier_drafts_path=final_dossier_drafts_path,
        json_output_path=json_output_path,
        markdown_output_path=markdown_output_path,
        expected_json_output_path=expected_json_output_path,
    )
    rendered_json = json.dumps(payload, indent=2, ensure_ascii=True) + "\n"
    rendered_markdown = render_markdown_report(payload)

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
        "preview_summary": payload["preview_summary"],
        "market_ids": payload["market_ids"],
    }


def main(argv):
    args = _parse_args(argv)
    summary = write_paper_decision_simulation_preview_artifacts(
        policy_review_result_path=args.policy_review_result,
        readiness_result_path=args.readiness_result,
        final_dossier_drafts_path=args.final_dossier_drafts,
        json_output_path=args.json_output,
        markdown_output_path=args.markdown_output,
        expected_json_output_path=args.expected_json_output,
    )
    print(json.dumps(summary, indent=2, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
