import argparse
import json
import sys
from pathlib import Path


TASK_ID = "PMBOT-INGEST-014-SELECTED-INGEST-FINAL-DOSSIER-DRAFT-EXPORT"
SCHEMA_VERSION = "selected_ingest_final_dossier_drafts.v1"
MARKDOWN_VERSION = "selected_ingest_final_dossier_drafts_markdown.v1"
ROOT = Path(__file__).resolve().parents[2]
DEFAULT_REVIEW_PACK = ROOT / "pm_bot" / "research" / "selected_ingest_dossier_human_review_pack.v1.json"
DEFAULT_REVIEW_RECORDS_RESULT = (
    ROOT / "pm_bot" / "research" / "selected_ingest_dossier_human_review_records_result.v1.json"
)
DEFAULT_VALIDATION_RESULT = (
    ROOT / "pm_bot" / "research" / "selected_ingest_manual_dossier_draft_validation_result.v1.json"
)
DEFAULT_DOSSIER_SKELETONS = ROOT / "pm_bot" / "research" / "selected_ingest_dossier_draft_skeletons.v1.json"
DEFAULT_MERGED_PACKETS = ROOT / "pm_bot" / "research" / "selected_ingest_merged_manual_research_packets.v1.json"
DEFAULT_JSON_OUTPUT = ROOT / "pm_bot" / "research" / "selected_ingest_final_dossier_drafts.v1.json"
DEFAULT_MARKDOWN_OUTPUT = ROOT / "pm_bot" / "research" / "selected_ingest_final_dossier_drafts.v1.md"
DEFAULT_EXPECTED_JSON_OUTPUT = (
    ROOT / "pm_bot" / "research" / "expected_selected_ingest_final_dossier_drafts.v1.json"
)


SELECTED_MARKET_IDS = ("692258", "824952", "691547", "597964", "598936")
APPROVED_OUTCOME = "approved_for_final_dossier_draft"
FINAL_DRAFT_STATUS = "final_dossier_draft_only"
FINAL_DRAFT_FIELDS = (
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
    "human_review_notes",
    "open_questions",
    "final_draft_sections",
    "final_draft_status",
    "source_ingest_artifacts",
)
FINAL_DRAFT_SECTION_FIELDS = (
    "market_overview",
    "resolution_rules",
    "evidence_inventory",
    "uncertainty_notes",
    "source_coverage_notes",
    "unresolved_questions",
    "human_review_summary",
)
SOURCE_COVERAGE_FIELDS = (
    "official_sources_to_check",
    "credible_news_sources_to_check",
    "official_sources_checked",
    "credible_news_sources_checked",
    "official_sources_checked_count",
    "credible_news_sources_checked_count",
    "evidence_inventory_count",
)
SUMMARY_FIELDS = (
    "approved_review_records_seen",
    "final_dossier_drafts_exported",
    "review_records_skipped",
    "completed_dossiers_created",
)
PROHIBITED_FINAL_DRAFT_FIELD_TOKENS = {
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
    "hold",
    "market_decision",
}
PROHIBITED_FINAL_DRAFT_PHRASES = (
    "bet recommendation",
    "trade recommendation",
    "recommendation",
    "probability estimate",
    "expected value",
    "market decision",
    "side recommendation",
    "completed dossier",
    "completed-dossier",
    "paper order",
    "real order",
)


def _parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Export deterministic offline selected-ingest PMBOT final dossier drafts for human reading."
    )
    parser.add_argument("--review-pack", default=str(DEFAULT_REVIEW_PACK.relative_to(ROOT)))
    parser.add_argument("--review-records-result", default=str(DEFAULT_REVIEW_RECORDS_RESULT.relative_to(ROOT)))
    parser.add_argument("--validation-result", default=str(DEFAULT_VALIDATION_RESULT.relative_to(ROOT)))
    parser.add_argument("--dossier-skeletons", default=str(DEFAULT_DOSSIER_SKELETONS.relative_to(ROOT)))
    parser.add_argument("--merged-packets", default=str(DEFAULT_MERGED_PACKETS.relative_to(ROOT)))
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


def _string_map(value):
    if not isinstance(value, dict):
        return {}
    normalized = {}
    for key in sorted(value):
        cleaned_key = _clean_text(key)
        cleaned_value = _clean_text(value.get(key))
        if cleaned_key:
            normalized[cleaned_key] = cleaned_value
    return normalized


def _records_list(payload, field):
    records = payload.get(field)
    if not isinstance(records, list):
        raise ValueError(f"payload must contain {field} list")
    return [record for record in records if isinstance(record, dict)]


def _by_market_id(records, source_name):
    by_market_id = {}
    for record in records:
        market_id = _clean_text(record.get("market_id"))
        if not market_id:
            continue
        if market_id in by_market_id:
            raise ValueError(f"duplicate {source_name} market_id: {market_id}")
        by_market_id[market_id] = record
    return by_market_id


def _selected_market_ids_from_payload(payload):
    selected_market_ids = _string_list(payload.get("selected_market_ids"))
    if selected_market_ids:
        return selected_market_ids
    return list(SELECTED_MARKET_IDS)


def _selected_sort_key(market_id):
    normalized = _clean_text(market_id)
    try:
        return (0, SELECTED_MARKET_IDS.index(normalized), normalized)
    except ValueError:
        return (1, len(SELECTED_MARKET_IDS), normalized)


def _human_review_pack_by_market_id(payload):
    return _by_market_id(_records_list(payload, "human_review_packs"), "selected-ingest human review pack")


def _accepted_review_records(payload):
    records = _records_list(payload, "accepted_human_review_records")
    return sorted(
        records,
        key=lambda record: (
            _selected_sort_key(record.get("market_id")),
            record.get("record_index", 0),
            _clean_text(record.get("human_review_outcome")),
        ),
    )


def _validation_records_by_market_id(payload):
    accepted = _records_list(payload, "accepted_draft_records")
    return _by_market_id(accepted, "selected-ingest accepted draft validation record")


def _skeletons_by_market_id(payload):
    return _by_market_id(_records_list(payload, "dossier_draft_skeletons"), "selected-ingest dossier skeleton")


def _merged_packets_by_market_id(payload):
    return _by_market_id(_records_list(payload, "packets"), "selected-ingest merged research packet")


def _review_records_read(review_payload, accepted_records):
    summary = review_payload.get("review_summary")
    if isinstance(summary, dict) and isinstance(summary.get("review_records_read"), int):
        return summary["review_records_read"]
    rejected_records = review_payload.get("rejected_human_review_records")
    if isinstance(rejected_records, list):
        return len(accepted_records) + len(rejected_records)
    return len(accepted_records)


def _field_tokens(key):
    lower = str(key).lower()
    normalized_chars = []
    current = []
    for char in lower:
        if char.isalnum():
            current.append(char)
            normalized_chars.append(char)
        elif char == "_":
            if current:
                normalized_chars.append("_")
            current = []
        else:
            if current:
                normalized_chars.append("_")
            current = []

    normalized_key = "".join(normalized_chars).strip("_")
    tokens = {lower, normalized_key}
    tokens.update(token for token in normalized_key.split("_") if token)
    return {token for token in tokens if token}


def _walk_keys(value):
    if isinstance(value, dict):
        for key, nested in value.items():
            yield key
            yield from _walk_keys(nested)
    elif isinstance(value, list):
        for item in value:
            yield from _walk_keys(item)


def _walk_strings(value):
    if isinstance(value, dict):
        for nested in value.values():
            yield from _walk_strings(nested)
    elif isinstance(value, list):
        for item in value:
            yield from _walk_strings(item)
    elif isinstance(value, str):
        yield value


def _assert_no_prohibited_final_draft_fields(drafts):
    findings = []
    for draft in drafts:
        market_id = _clean_text(draft.get("market_id")) if isinstance(draft, dict) else ""
        for key in _walk_keys(draft):
            if _field_tokens(key) & PROHIBITED_FINAL_DRAFT_FIELD_TOKENS:
                findings.append((market_id, key))
    if findings:
        rendered = "; ".join(f"{market_id}:{key}" for market_id, key in sorted(findings))
        raise ValueError(f"final dossier drafts contain prohibited fields: {rendered}")


def _assert_no_prohibited_final_draft_phrases(drafts):
    findings = []
    for draft in drafts:
        market_id = _clean_text(draft.get("market_id")) if isinstance(draft, dict) else ""
        for text in _walk_strings(draft):
            normalized = text.lower().replace("_", " ")
            for phrase in PROHIBITED_FINAL_DRAFT_PHRASES:
                if phrase in normalized:
                    findings.append((market_id, phrase))
    if findings:
        rendered = "; ".join(f"{market_id}:{phrase}" for market_id, phrase in sorted(set(findings)))
        raise ValueError(f"final dossier drafts contain prohibited language: {rendered}")


def _source_coverage_notes(skeleton, merged_packet):
    skeleton_summary = skeleton.get("source_coverage_summary")
    if not isinstance(skeleton_summary, dict):
        skeleton_summary = {}
    notes = {
        "official_sources_to_check": _string_list(
            skeleton_summary.get("official_sources_to_check") or merged_packet.get("official_sources_to_check")
        ),
        "credible_news_sources_to_check": _string_list(
            skeleton_summary.get("credible_news_sources_to_check") or merged_packet.get("credible_news_sources_to_check")
        ),
        "official_sources_checked": _string_list(
            skeleton_summary.get("official_sources_checked") or merged_packet.get("official_sources_checked")
        ),
        "credible_news_sources_checked": _string_list(
            skeleton_summary.get("credible_news_sources_checked") or merged_packet.get("credible_news_sources_checked")
        ),
        "official_sources_checked_count": skeleton_summary.get("official_sources_checked_count"),
        "credible_news_sources_checked_count": skeleton_summary.get("credible_news_sources_checked_count"),
        "evidence_inventory_count": skeleton_summary.get("evidence_inventory_count"),
    }
    for count_field in (
        "official_sources_checked_count",
        "credible_news_sources_checked_count",
        "evidence_inventory_count",
    ):
        if not isinstance(notes[count_field], int):
            notes[count_field] = 0
    return {field: notes[field] for field in SOURCE_COVERAGE_FIELDS}


def _final_draft_sections(pack, review_record, skeleton, merged_packet):
    sections = {
        "market_overview": {
            "title_question": _clean_text(pack.get("title_question")),
            "event_id": _clean_text(pack.get("event_id")),
            "event_title": _clean_text(pack.get("event_title")),
            "category": _clean_text(pack.get("category")),
            "packet_type": _clean_text(pack.get("packet_type")),
            "deadline": _clean_text(pack.get("deadline")),
            "current_yes_price": pack.get("current_yes_price"),
            "liquidity": pack.get("liquidity"),
            "volume": pack.get("volume"),
            "market_context_notes": _clean_text(pack.get("market_context_notes")),
        },
        "resolution_rules": {
            "resolution_criteria_summary": _clean_text(pack.get("resolution_criteria_summary")),
            "resolution_criteria_notes": _clean_text(pack.get("resolution_criteria_notes")),
        },
        "evidence_inventory": _string_list(pack.get("evidence_summary_by_source")),
        "uncertainty_notes": _string_list(pack.get("uncertainty_register")),
        "source_coverage_notes": _source_coverage_notes(skeleton, merged_packet),
        "unresolved_questions": {
            "missing_information_review": _clean_text(pack.get("missing_information_review")),
            "open_questions": _string_list(pack.get("open_questions")),
        },
        "human_review_summary": {
            "human_review_notes": _clean_text(review_record.get("reviewer_notes")),
        },
    }
    return {field: sections[field] for field in FINAL_DRAFT_SECTION_FIELDS}


def _final_draft_item(pack, review_record, skeleton, merged_packet):
    item = {
        "market_id": _clean_text(pack.get("market_id")),
        "title_question": _clean_text(pack.get("title_question")),
        "event_id": _clean_text(pack.get("event_id")),
        "event_title": _clean_text(pack.get("event_title")),
        "category": _clean_text(pack.get("category")),
        "packet_type": _clean_text(pack.get("packet_type")),
        "deadline": _clean_text(pack.get("deadline")),
        "current_yes_price": pack.get("current_yes_price"),
        "liquidity": pack.get("liquidity"),
        "volume": pack.get("volume"),
        "resolution_criteria_summary": _clean_text(pack.get("resolution_criteria_summary")),
        "market_context_notes": _clean_text(pack.get("market_context_notes")),
        "resolution_criteria_notes": _clean_text(pack.get("resolution_criteria_notes")),
        "evidence_summary_by_source": _string_list(pack.get("evidence_summary_by_source")),
        "uncertainty_register": _string_list(pack.get("uncertainty_register")),
        "missing_information_review": _clean_text(pack.get("missing_information_review")),
        "operator_review_notes": _clean_text(pack.get("operator_review_notes")),
        "human_review_notes": _clean_text(review_record.get("reviewer_notes")),
        "open_questions": _string_list(pack.get("open_questions")),
        "final_draft_sections": _final_draft_sections(pack, review_record, skeleton, merged_packet),
        "final_draft_status": FINAL_DRAFT_STATUS,
        "source_ingest_artifacts": _string_map(pack.get("source_ingest_artifacts")),
    }
    return {field: item[field] for field in FINAL_DRAFT_FIELDS}


def _assert_final_draft_shape(drafts):
    item_fields = list(FINAL_DRAFT_FIELDS)
    section_fields = list(FINAL_DRAFT_SECTION_FIELDS)
    for draft in drafts:
        if list(draft) != item_fields:
            raise ValueError(f"final draft field sequence mismatch for {draft.get('market_id', '')}")
        if draft["final_draft_status"] != FINAL_DRAFT_STATUS:
            raise ValueError(f"invalid final draft status for {draft.get('market_id', '')}")
        if list(draft["final_draft_sections"]) != section_fields:
            raise ValueError(f"final draft section sequence mismatch for {draft.get('market_id', '')}")


def _build_summary(review_records_read, approved_records, drafts):
    return {
        "approved_review_records_seen": len(approved_records),
        "final_dossier_drafts_exported": len(drafts),
        "review_records_skipped": review_records_read - len(drafts),
        "completed_dossiers_created": 0,
    }


def build_selected_ingest_final_dossier_drafts_export(
    review_pack_path=DEFAULT_REVIEW_PACK,
    review_records_result_path=DEFAULT_REVIEW_RECORDS_RESULT,
    validation_result_path=DEFAULT_VALIDATION_RESULT,
    dossier_skeletons_path=DEFAULT_DOSSIER_SKELETONS,
    merged_packets_path=DEFAULT_MERGED_PACKETS,
    json_output_path=DEFAULT_JSON_OUTPUT,
    markdown_output_path=DEFAULT_MARKDOWN_OUTPUT,
    expected_json_output_path=DEFAULT_EXPECTED_JSON_OUTPUT,
):
    review_pack_path = _resolve_path(review_pack_path)
    review_records_result_path = _resolve_path(review_records_result_path)
    validation_result_path = _resolve_path(validation_result_path)
    dossier_skeletons_path = _resolve_path(dossier_skeletons_path)
    merged_packets_path = _resolve_path(merged_packets_path)
    json_output_path = _resolve_path(json_output_path)
    markdown_output_path = _resolve_path(markdown_output_path)
    expected_json_output_path = _resolve_path(expected_json_output_path)

    review_pack_payload = _load_json(review_pack_path)
    review_payload = _load_json(review_records_result_path)
    validation_payload = _load_json(validation_result_path)
    skeleton_payload = _load_json(dossier_skeletons_path)
    merged_payload = _load_json(merged_packets_path)

    selected_market_ids = _selected_market_ids_from_payload(review_pack_payload)
    pack_by_market_id = _human_review_pack_by_market_id(review_pack_payload)
    accepted_records = _accepted_review_records(review_payload)
    approved_records = [
        record
        for record in accepted_records
        if _clean_text(record.get("human_review_outcome")) == APPROVED_OUTCOME
    ]
    validation_by_market_id = _validation_records_by_market_id(validation_payload)
    skeleton_by_market_id = _skeletons_by_market_id(skeleton_payload)
    merged_by_market_id = _merged_packets_by_market_id(merged_payload)
    review_records_read = _review_records_read(review_payload, accepted_records)

    drafts = []
    for record in approved_records:
        market_id = _clean_text(record.get("market_id"))
        if market_id not in selected_market_ids:
            raise ValueError(f"approved human review record is not in selected-ingest market ids: {market_id}")
        if market_id not in pack_by_market_id:
            raise ValueError(f"approved human review record is missing human review pack context: {market_id}")
        if market_id not in validation_by_market_id:
            raise ValueError(f"approved human review record is missing validated manual draft context: {market_id}")
        if market_id not in skeleton_by_market_id:
            raise ValueError(f"approved human review record is missing dossier skeleton context: {market_id}")
        if market_id not in merged_by_market_id:
            raise ValueError(f"approved human review record is missing merged packet context: {market_id}")
        drafts.append(
            _final_draft_item(
                pack_by_market_id[market_id],
                record,
                skeleton_by_market_id[market_id],
                merged_by_market_id[market_id],
            )
        )

    drafts.sort(key=lambda item: (_selected_sort_key(item["market_id"]), item["title_question"]))
    _assert_final_draft_shape(drafts)
    _assert_no_prohibited_final_draft_fields(drafts)
    _assert_no_prohibited_final_draft_phrases(drafts)
    summary = _build_summary(review_records_read, approved_records, drafts)

    return {
        "schema_version": SCHEMA_VERSION,
        "markdown_version": MARKDOWN_VERSION,
        "task_id": TASK_ID,
        "deterministic": True,
        "source_review_pack_path": _display_path(review_pack_path),
        "source_review_pack_schema_version": review_pack_payload.get("schema_version"),
        "source_review_records_result_path": _display_path(review_records_result_path),
        "source_review_records_result_schema_version": review_payload.get("schema_version"),
        "source_validation_result_path": _display_path(validation_result_path),
        "source_validation_result_schema_version": validation_payload.get("schema_version"),
        "source_dossier_skeletons_path": _display_path(dossier_skeletons_path),
        "source_dossier_skeletons_schema_version": skeleton_payload.get("schema_version"),
        "source_merged_packets_path": _display_path(merged_packets_path),
        "source_merged_packets_schema_version": merged_payload.get("schema_version"),
        "json_output_path": _display_path(json_output_path),
        "markdown_output_path": _display_path(markdown_output_path),
        "expected_json_output_path": _display_path(expected_json_output_path),
        "selected_market_ids": selected_market_ids,
        "approved_human_review_outcome": APPROVED_OUTCOME,
        "final_draft_status": FINAL_DRAFT_STATUS,
        "final_dossier_draft_item_fields": list(FINAL_DRAFT_FIELDS),
        "final_draft_section_fields": list(FINAL_DRAFT_SECTION_FIELDS),
        "export_summary": summary,
        "exported_market_ids": [item["market_id"] for item in drafts],
        "final_dossier_drafts": drafts,
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


def _render_string_map(items):
    if not items:
        return ["- none"]
    return [f"- {key}: {items[key]}" for key in sorted(items)]


def _render_source_coverage(notes):
    lines = []
    for field in SOURCE_COVERAGE_FIELDS:
        value = notes[field]
        if isinstance(value, list):
            lines.append(f"- {field}:")
            lines.extend(_render_nested_list(value))
        else:
            lines.append(f"- {field}: {_render_scalar(value)}")
    return lines


def render_markdown_report(export_payload):
    summary = export_payload["export_summary"]
    lines = [
        "# PMBOT Selected-Ingest Final Dossier Drafts v1",
        "",
        "## Summary",
        "",
        f"- task_id: {export_payload['task_id']}",
        f"- source_review_pack_path: {export_payload['source_review_pack_path']}",
        f"- source_review_records_result_path: {export_payload['source_review_records_result_path']}",
        f"- source_validation_result_path: {export_payload['source_validation_result_path']}",
        f"- source_dossier_skeletons_path: {export_payload['source_dossier_skeletons_path']}",
        f"- source_merged_packets_path: {export_payload['source_merged_packets_path']}",
        "- selected_market_ids:",
    ]
    lines.extend(_render_nested_list(export_payload["selected_market_ids"]))
    for field in SUMMARY_FIELDS:
        lines.append(f"- {field}: {summary[field]}")
    lines.extend(["- exported_market_ids:"])
    lines.extend(_render_nested_list(export_payload["exported_market_ids"]))
    lines.extend(["", "## Final Dossier Drafts", ""])

    if not export_payload["final_dossier_drafts"]:
        lines.extend(["- none", ""])
    else:
        for item in export_payload["final_dossier_drafts"]:
            sections = item["final_draft_sections"]
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
                    f"- final_draft_status: {item['final_draft_status']}",
                    "",
                    "#### Market Overview",
                    "",
                    f"- market_context_notes: {item['market_context_notes']}",
                    "",
                    "#### Resolution Rules",
                    "",
                    f"- resolution_criteria_summary: {item['resolution_criteria_summary']}",
                    f"- resolution_criteria_notes: {item['resolution_criteria_notes']}",
                    "",
                    "#### Evidence Inventory",
                    "",
                ]
            )
            lines.extend(_render_list(sections["evidence_inventory"]))
            lines.extend(["", "#### Uncertainty Notes", ""])
            lines.extend(_render_list(sections["uncertainty_notes"]))
            lines.extend(["", "#### Source Coverage Notes", ""])
            lines.extend(_render_source_coverage(sections["source_coverage_notes"]))
            lines.extend(["", "#### Unresolved Questions", ""])
            lines.append(f"- missing_information_review: {sections['unresolved_questions']['missing_information_review']}")
            lines.extend(_render_list(sections["unresolved_questions"]["open_questions"]))
            lines.extend(["", "#### Human Review Summary", ""])
            lines.append(f"- human_review_notes: {sections['human_review_summary']['human_review_notes']}")
            lines.extend(["", "#### Source Ingest Artifacts", ""])
            lines.extend(_render_string_map(item["source_ingest_artifacts"]))
            lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def write_selected_ingest_final_dossier_draft_artifacts(
    review_pack_path=DEFAULT_REVIEW_PACK,
    review_records_result_path=DEFAULT_REVIEW_RECORDS_RESULT,
    validation_result_path=DEFAULT_VALIDATION_RESULT,
    dossier_skeletons_path=DEFAULT_DOSSIER_SKELETONS,
    merged_packets_path=DEFAULT_MERGED_PACKETS,
    json_output_path=DEFAULT_JSON_OUTPUT,
    markdown_output_path=DEFAULT_MARKDOWN_OUTPUT,
    expected_json_output_path=DEFAULT_EXPECTED_JSON_OUTPUT,
):
    json_output_path = _resolve_path(json_output_path)
    markdown_output_path = _resolve_path(markdown_output_path)
    expected_json_output_path = _resolve_path(expected_json_output_path)
    export_payload = build_selected_ingest_final_dossier_drafts_export(
        review_pack_path=review_pack_path,
        review_records_result_path=review_records_result_path,
        validation_result_path=validation_result_path,
        dossier_skeletons_path=dossier_skeletons_path,
        merged_packets_path=merged_packets_path,
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
    summary = write_selected_ingest_final_dossier_draft_artifacts(
        review_pack_path=args.review_pack,
        review_records_result_path=args.review_records_result,
        validation_result_path=args.validation_result,
        dossier_skeletons_path=args.dossier_skeletons,
        merged_packets_path=args.merged_packets,
        json_output_path=args.json_output,
        markdown_output_path=args.markdown_output,
        expected_json_output_path=args.expected_json_output,
    )
    print(json.dumps(summary, indent=2, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
