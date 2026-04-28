import argparse
import copy
import json
import sys
from pathlib import Path


TASK_ID = "PMBOT-INGEST-011-SELECTED-INGEST-MANUAL-DOSSIER-DRAFT-QUALITY-GATE"
SCHEMA_VERSION = "selected_ingest_manual_dossier_draft_validation_result.v1"
MARKDOWN_VERSION = "selected_ingest_manual_dossier_draft_validation_report.v1"
ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DRAFT_RECORDS = ROOT / "pm_bot" / "research" / "selected_ingest_manual_dossier_drafts_fixture.v1.json"
DEFAULT_DOSSIER_SKELETONS = ROOT / "pm_bot" / "research" / "selected_ingest_dossier_draft_skeletons.v1.json"
DEFAULT_REVIEW_RECORDS_RESULT = ROOT / "pm_bot" / "research" / "selected_ingest_operator_review_records_result.v1.json"
DEFAULT_MERGED_PACKETS = ROOT / "pm_bot" / "research" / "selected_ingest_merged_manual_research_packets.v1.json"
DEFAULT_JSON_RESULT = ROOT / "pm_bot" / "research" / "selected_ingest_manual_dossier_draft_validation_result.v1.json"
DEFAULT_MARKDOWN_REPORT = ROOT / "pm_bot" / "research" / "selected_ingest_manual_dossier_draft_validation_report.v1.md"
DEFAULT_EXPECTED_JSON_RESULT = ROOT / "pm_bot" / "research" / "expected_selected_ingest_manual_dossier_draft_validation_result.v1.json"

SELECTED_MARKET_IDS = ("692258", "824952", "691547", "597964", "598936")
ALLOWED_DRAFT_STATUSES = (
    "draft_incomplete",
    "draft_ready_for_human_review",
    "needs_more_information",
    "draft_rejected",
)
REQUIRED_READY_SECTIONS = (
    "market_context_notes",
    "resolution_criteria_notes",
    "evidence_summary_by_source",
    "uncertainty_register",
    "missing_information_review",
    "operator_review_notes",
)
ALLOWED_NEXT_MANUAL_ACTIONS = (
    "human_review_required",
    "add_missing_information",
    "fix_draft_structure",
    "reject_draft_quality",
)
ALLOWED_DRAFT_FIELDS = {
    "market_id",
    "draft_status",
    "market_context_notes",
    "resolution_criteria_notes",
    "evidence_summary_by_source",
    "uncertainty_register",
    "missing_information_review",
    "operator_review_notes",
    "open_questions",
    "next_manual_action",
}
TEXT_FIELDS = (
    "market_context_notes",
    "resolution_criteria_notes",
    "missing_information_review",
    "operator_review_notes",
)
LIST_FIELDS = (
    "evidence_summary_by_source",
    "uncertainty_register",
    "open_questions",
)
DRAFT_RECORD_METADATA_FIELDS = {
    "schema_version",
    "task_id",
    "deterministic",
    "draft_record_format",
    "instructions",
    "notes",
    "selected_market_ids",
}
PROHIBITED_FIELD_TOKENS = {
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
PROHIBITED_MACHINE_READABLE_LANGUAGE = (
    "completed_dossier",
    "final_dossier",
    "bet_recommendation",
    "trade_recommendation",
    "market_decision",
)
NORMALIZED_ACCEPTED_FIELDS = (
    "record_index",
    "market_id",
    "draft_status",
    "market_context_notes",
    "resolution_criteria_notes",
    "evidence_summary_by_source",
    "uncertainty_register",
    "missing_information_review",
    "operator_review_notes",
    "open_questions",
    "next_manual_action",
)
NORMALIZED_REJECTED_FIELDS = (
    "record_index",
    "market_id",
    "draft_status",
    "next_manual_action",
    "errors",
)
SUMMARY_FIELDS = (
    "draft_records_read",
    "draft_records_accepted",
    "draft_records_rejected",
    "draft_ready_for_human_review",
    "needs_more_information",
    "draft_incomplete",
    "draft_rejected",
)
SAFETY_FLAGS = {
    "live_fetchers": False,
    "network_api_calls": False,
    "credentials": False,
    "wallet_private_keys": False,
    "authenticated_endpoints": False,
    "trading_endpoints": False,
    "real_orders": False,
    "live_trading": False,
    "paper_orders": False,
    "betting_recommendations": False,
    "truth_inference": False,
    "market_scoring": False,
    "probability_estimates": False,
    "expected_value_calculations": False,
    "side_recommendations": False,
    "market_decisions": False,
    "runtime_wiring": False,
    "dispatcher_run_codex_touched": False,
    "prompt_automation": False,
    "codex_copy_roots": False,
    "completed_dossiers": False,
}


def _parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Validate deterministic offline selected-ingest manual dossier draft attempts."
    )
    parser.add_argument("--draft-records", default=str(DEFAULT_DRAFT_RECORDS.relative_to(ROOT)))
    parser.add_argument("--dossier-skeletons", default=str(DEFAULT_DOSSIER_SKELETONS.relative_to(ROOT)))
    parser.add_argument("--review-records-result", default=str(DEFAULT_REVIEW_RECORDS_RESULT.relative_to(ROOT)))
    parser.add_argument("--merged-packets", default=str(DEFAULT_MERGED_PACKETS.relative_to(ROOT)))
    parser.add_argument("--json-output", default=str(DEFAULT_JSON_RESULT.relative_to(ROOT)))
    parser.add_argument("--markdown-output", default=str(DEFAULT_MARKDOWN_REPORT.relative_to(ROOT)))
    parser.add_argument("--expected-json-output", default=str(DEFAULT_EXPECTED_JSON_RESULT.relative_to(ROOT)))
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


def _non_empty_text(value):
    return isinstance(value, str) and bool(value.strip())


def _error(code, path, message):
    return {"code": code, "path": path, "message": message}


def _append(errors, code, path, message):
    errors.append(_error(code, path, message))


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
    compact = str(key).lower()
    return {token for token in normalized if token} | {compact}


def _walk_prohibited_fields(value, prefix=""):
    findings = []
    if isinstance(value, dict):
        for key, nested in value.items():
            key_text = str(key)
            path = f"{prefix}.{key_text}" if prefix else key_text
            if _field_tokens(key_text) & PROHIBITED_FIELD_TOKENS:
                findings.append(
                    _error(
                        f"prohibited_draft_field:{key_text}",
                        path,
                        "Trading, execution, recommendation, bet, stake, size, price, scoring, signal, probability, EV, wallet, private-key, side, buy/sell, and market-decision fields are prohibited.",
                    )
                )
            findings.extend(_walk_prohibited_fields(nested, path))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            findings.extend(_walk_prohibited_fields(item, f"{prefix}[{index}]"))
    return findings


def _language_key(text):
    return str(text).lower().replace("-", "_").replace(" ", "_")


def _matched_prohibited_language(text):
    normalized = _language_key(text)
    for phrase in PROHIBITED_MACHINE_READABLE_LANGUAGE:
        if phrase in normalized:
            return phrase
    return ""


def _walk_prohibited_language(value, prefix=""):
    findings = []
    if isinstance(value, dict):
        for key, nested in value.items():
            key_text = str(key)
            path = f"{prefix}.{key_text}" if prefix else key_text
            key_phrase = _matched_prohibited_language(key_text)
            if key_phrase:
                findings.append(
                    _error(
                        f"prohibited_dossier_language:{key_phrase}",
                        path,
                        "Completed/final dossier, recommendation, and market-decision language is prohibited in machine-readable manual draft fields.",
                    )
                )
            findings.extend(_walk_prohibited_language(nested, path))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            findings.extend(_walk_prohibited_language(item, f"{prefix}[{index}]"))
    elif isinstance(value, str):
        phrase = _matched_prohibited_language(value)
        if phrase:
            findings.append(
                _error(
                    f"prohibited_dossier_language:{phrase}",
                    prefix,
                    "Completed/final dossier, recommendation, and market-decision language is prohibited in machine-readable manual draft fields.",
                )
            )
    return findings


def _selected_market_ids_from_payload(payload, payload_name):
    selected_market_ids = tuple(str(market_id) for market_id in payload.get("selected_market_ids", ()))
    if selected_market_ids != SELECTED_MARKET_IDS:
        raise ValueError(f"{payload_name} has unexpected selected_market_ids")
    return selected_market_ids


def _load_skeleton_context(path):
    payload = _load_json(path)
    if not isinstance(payload, dict):
        raise ValueError("selected-ingest dossier skeleton payload must be a JSON object")
    selected_market_ids = _selected_market_ids_from_payload(payload, "selected-ingest dossier skeleton payload")
    skeletons = payload.get("dossier_draft_skeletons")
    if not isinstance(skeletons, list):
        raise ValueError("selected-ingest dossier skeleton payload must contain dossier_draft_skeletons list")

    exported_market_ids = payload.get("exported_market_ids")
    exported_market_id_set = {
        _clean_text(market_id)
        for market_id in exported_market_ids
        if _clean_text(market_id)
    } if isinstance(exported_market_ids, list) else set()

    skeleton_by_market_id = {}
    for skeleton in skeletons:
        if not isinstance(skeleton, dict) or not _non_empty_text(skeleton.get("market_id")):
            continue
        market_id = _clean_text(skeleton.get("market_id"))
        if not exported_market_id_set or market_id in exported_market_id_set:
            skeleton_by_market_id[market_id] = skeleton

    skeleton_fields = payload.get("skeleton_fields")
    if not isinstance(skeleton_fields, list):
        skeleton_fields = sorted({str(field) for skeleton in skeletons if isinstance(skeleton, dict) for field in skeleton})
    immutable_fields = sorted(set(str(field) for field in skeleton_fields) - ALLOWED_DRAFT_FIELDS)
    return payload, selected_market_ids, skeleton_by_market_id, immutable_fields


def _load_selected_review_result(path):
    payload = _load_json(path)
    if not isinstance(payload, dict):
        raise ValueError("selected-ingest operator review result payload must be a JSON object")
    _selected_market_ids_from_payload(payload, "selected-ingest operator review result payload")
    return payload


def _load_selected_merged_packets(path):
    payload = _load_json(path)
    if not isinstance(payload, dict):
        raise ValueError("selected-ingest merged packet payload must be a JSON object")
    _selected_market_ids_from_payload(payload, "selected-ingest merged packet payload")
    if not isinstance(payload.get("packets"), list):
        raise ValueError("selected-ingest merged packet payload must contain packets list")
    return payload


def _draft_record_entries(payload):
    if isinstance(payload, list):
        return payload, None
    if not isinstance(payload, dict):
        return None, _error(
            "draft_records_payload_not_object_or_list",
            "draft_records",
            "Selected-ingest manual dossier draft JSON must be an object or a list.",
        )

    for field in ("draft_records", "drafts", "records"):
        if field in payload:
            if not isinstance(payload[field], list):
                return None, _error("draft_records_not_list", field, f"{field} must be a list.")
            return payload[field], None

    entries = []
    for market_id, value in payload.items():
        if market_id in DRAFT_RECORD_METADATA_FIELDS:
            continue
        if isinstance(value, dict):
            entry = copy.deepcopy(value)
            entry.setdefault("market_id", str(market_id))
            entries.append(entry)
        else:
            entries.append({"market_id": str(market_id), "__invalid_draft_record__": value})
    return entries, None


def _draft_market_id(record, index):
    if isinstance(record, dict) and _non_empty_text(record.get("market_id")):
        return record["market_id"].strip()
    return f"draft_record_index_{index}"


def _validate_string_list(value, path, errors):
    if not isinstance(value, list):
        _append(errors, "draft_field_not_list", path, f"{path} must be a list of non-empty strings.")
        return []
    normalized = []
    seen = set()
    for index, item in enumerate(value):
        item_path = f"{path}[{index}]"
        if not isinstance(item, str):
            _append(errors, "draft_list_item_not_string", item_path, f"{item_path} must be a string.")
            continue
        cleaned = item.strip()
        if not cleaned:
            _append(errors, "draft_list_item_empty", item_path, f"{item_path} must be a non-empty string.")
            continue
        if cleaned in seen:
            _append(errors, "draft_list_item_duplicate", item_path, f"{item_path} duplicates an earlier item.")
            continue
        seen.add(cleaned)
        normalized.append(cleaned)
    return normalized


def _has_non_empty_field(record, field):
    value = record.get(field)
    if field in TEXT_FIELDS:
        return _non_empty_text(value)
    if field in LIST_FIELDS:
        return isinstance(value, list) and bool([item for item in value if _non_empty_text(item)])
    return False


def _validate_record(record, index, selected_market_ids, skeleton_market_ids, immutable_fields):
    market_id = _draft_market_id(record, index)
    errors = []
    if not isinstance(record, dict):
        return market_id, [_error("draft_record_not_object", f"draft_records[{index}]", "Each selected-ingest manual dossier draft record must be an object.")]

    errors.extend(_walk_prohibited_fields(record))
    errors.extend(_walk_prohibited_language(record))

    if not _non_empty_text(record.get("market_id")):
        _append(errors, "missing_draft_market_id", "market_id", "Selected-ingest manual dossier draft must include a non-empty market_id.")
    elif market_id not in selected_market_ids:
        _append(errors, "unknown_market_id", "market_id", "Selected-ingest manual dossier draft market_id is absent from selected_ingest_dossier_draft_skeletons.v1.json selected_market_ids.")
    elif market_id not in skeleton_market_ids:
        _append(errors, "non_skeleton_market_id", "market_id", "Selected-ingest manual dossier draft market_id was selected but was not exported as a dossier draft skeleton.")

    for field in sorted(set(record) - ALLOWED_DRAFT_FIELDS):
        if field in immutable_fields:
            _append(errors, f"immutable_skeleton_field_override:{field}", field, f"{field} is immutable skeleton content and cannot be supplied by a manual dossier draft.")
        else:
            _append(errors, f"unexpected_draft_field:{field}", field, f"{field} is not an allowed selected-ingest manual dossier draft field.")

    draft_status = record.get("draft_status")
    if "draft_status" not in record:
        _append(errors, "missing_draft_status", "draft_status", "draft_status is required.")
    elif draft_status not in ALLOWED_DRAFT_STATUSES:
        _append(errors, "invalid_draft_status", "draft_status", "draft_status is not in the allowed status set.")

    next_manual_action = record.get("next_manual_action")
    if "next_manual_action" not in record:
        _append(errors, "missing_next_manual_action", "next_manual_action", "next_manual_action is required.")
    elif next_manual_action not in ALLOWED_NEXT_MANUAL_ACTIONS:
        _append(errors, "invalid_next_manual_action", "next_manual_action", "next_manual_action is not in the allowed manual action set.")

    for field in TEXT_FIELDS:
        if field in record and not isinstance(record[field], str):
            _append(errors, "draft_field_not_string", field, f"{field} must be a string.")

    for field in LIST_FIELDS:
        if field in record:
            _validate_string_list(record[field], field, errors)

    if draft_status == "draft_ready_for_human_review":
        for field in REQUIRED_READY_SECTIONS:
            if not _has_non_empty_field(record, field):
                _append(errors, f"required_ready_section_empty:{field}", field, f"{field} is required and must be non-empty for draft_ready_for_human_review.")

    errors.sort(key=lambda item: (item["path"], item["code"], item["message"]))
    return market_id, errors


def _normalized_string_list(value):
    if not isinstance(value, list):
        return []
    normalized = []
    seen = set()
    for item in value:
        if not isinstance(item, str):
            continue
        cleaned = item.strip()
        if not cleaned or cleaned in seen:
            continue
        seen.add(cleaned)
        normalized.append(cleaned)
    return normalized


def _normalized_accepted_record(record, index, market_id):
    normalized = {
        "record_index": index,
        "market_id": market_id,
        "draft_status": _clean_text(record.get("draft_status")),
        "market_context_notes": _clean_text(record.get("market_context_notes")),
        "resolution_criteria_notes": _clean_text(record.get("resolution_criteria_notes")),
        "evidence_summary_by_source": _normalized_string_list(record.get("evidence_summary_by_source")),
        "uncertainty_register": _normalized_string_list(record.get("uncertainty_register")),
        "missing_information_review": _clean_text(record.get("missing_information_review")),
        "operator_review_notes": _clean_text(record.get("operator_review_notes")),
        "open_questions": _normalized_string_list(record.get("open_questions")),
        "next_manual_action": _clean_text(record.get("next_manual_action")),
    }
    return {field: normalized[field] for field in NORMALIZED_ACCEPTED_FIELDS}


def _normalized_rejected_record(record, index, market_id, errors):
    normalized = {
        "record_index": index,
        "market_id": market_id,
        "draft_status": _clean_text(record.get("draft_status")) if isinstance(record, dict) else "",
        "next_manual_action": _clean_text(record.get("next_manual_action")) if isinstance(record, dict) else "",
        "errors": errors,
    }
    return {field: normalized[field] for field in NORMALIZED_REJECTED_FIELDS}


def _summary(draft_records_read, accepted_records, rejected_records):
    status_counts = {status: 0 for status in ALLOWED_DRAFT_STATUSES}
    for record in accepted_records:
        status_counts[record["draft_status"]] += 1
    return {
        "draft_records_read": draft_records_read,
        "draft_records_accepted": len(accepted_records),
        "draft_records_rejected": len(rejected_records),
        "draft_ready_for_human_review": status_counts["draft_ready_for_human_review"],
        "needs_more_information": status_counts["needs_more_information"],
        "draft_incomplete": status_counts["draft_incomplete"],
        "draft_rejected": status_counts["draft_rejected"],
    }


def _errors_by_market_id(rejected_records):
    errors = {}
    for record in rejected_records:
        errors.setdefault(record["market_id"], []).extend(record["errors"])
    return {market_id: errors[market_id] for market_id in sorted(errors)}


def _selected_sort_key(record):
    market_id = record["market_id"]
    try:
        selected_index = SELECTED_MARKET_IDS.index(market_id)
    except ValueError:
        selected_index = len(SELECTED_MARKET_IDS)
    return (selected_index, market_id, record.get("record_index", 0))


def build_selected_ingest_manual_dossier_draft_validation_result(
    draft_records_path=DEFAULT_DRAFT_RECORDS,
    dossier_skeletons_path=DEFAULT_DOSSIER_SKELETONS,
    review_records_result_path=DEFAULT_REVIEW_RECORDS_RESULT,
    merged_packets_path=DEFAULT_MERGED_PACKETS,
    json_output_path=DEFAULT_JSON_RESULT,
    markdown_output_path=DEFAULT_MARKDOWN_REPORT,
    expected_json_output_path=DEFAULT_EXPECTED_JSON_RESULT,
):
    draft_records_path = _resolve_path(draft_records_path)
    dossier_skeletons_path = _resolve_path(dossier_skeletons_path)
    review_records_result_path = _resolve_path(review_records_result_path)
    merged_packets_path = _resolve_path(merged_packets_path)
    json_output_path = _resolve_path(json_output_path)
    markdown_output_path = _resolve_path(markdown_output_path)
    expected_json_output_path = _resolve_path(expected_json_output_path)

    draft_payload = _load_json(draft_records_path)
    skeleton_payload, selected_market_ids, skeleton_by_market_id, immutable_fields = _load_skeleton_context(dossier_skeletons_path)
    review_payload = _load_selected_review_result(review_records_result_path)
    merged_payload = _load_selected_merged_packets(merged_packets_path)
    skeleton_market_ids = set(skeleton_by_market_id)
    entries, payload_error = _draft_record_entries(draft_payload)
    accepted_records = []
    rejected_records = []

    if payload_error is not None:
        rejected_records.append(_normalized_rejected_record({}, 0, "payload", [payload_error]))
        entries = []

    for index, record in enumerate(entries or []):
        market_id, errors = _validate_record(
            record=record,
            index=index,
            selected_market_ids=set(selected_market_ids),
            skeleton_market_ids=skeleton_market_ids,
            immutable_fields=immutable_fields,
        )
        if errors:
            rejected_records.append(_normalized_rejected_record(record, index, market_id, errors))
            continue
        accepted_records.append(_normalized_accepted_record(record, index, market_id))

    accepted_records.sort(key=_selected_sort_key)
    rejected_records.sort(key=_selected_sort_key)
    errors_by_market_id = _errors_by_market_id(rejected_records)
    summary = _summary(len(entries or []), accepted_records, rejected_records)

    return {
        "schema_version": SCHEMA_VERSION,
        "markdown_version": MARKDOWN_VERSION,
        "task_id": TASK_ID,
        "deterministic": True,
        "source_draft_records_path": _display_path(draft_records_path),
        "source_draft_records_schema_version": draft_payload.get("schema_version") if isinstance(draft_payload, dict) else None,
        "source_dossier_skeletons_path": _display_path(dossier_skeletons_path),
        "source_dossier_skeletons_schema_version": skeleton_payload.get("schema_version"),
        "source_review_records_result_path": _display_path(review_records_result_path),
        "source_review_records_result_schema_version": review_payload.get("schema_version"),
        "source_merged_packets_path": _display_path(merged_packets_path),
        "source_merged_packets_schema_version": merged_payload.get("schema_version"),
        "json_result_path": _display_path(json_output_path),
        "markdown_report_path": _display_path(markdown_output_path),
        "expected_json_result_path": _display_path(expected_json_output_path),
        "selected_market_ids": list(selected_market_ids),
        "exported_skeleton_market_ids": [market_id for market_id in selected_market_ids if market_id in skeleton_market_ids],
        "allowed_draft_statuses": list(ALLOWED_DRAFT_STATUSES),
        "allowed_next_manual_actions": list(ALLOWED_NEXT_MANUAL_ACTIONS),
        "required_ready_sections": list(REQUIRED_READY_SECTIONS),
        "allowed_draft_fields": sorted(ALLOWED_DRAFT_FIELDS),
        "immutable_skeleton_fields": immutable_fields,
        "accepted_record_fields": list(NORMALIZED_ACCEPTED_FIELDS),
        "rejected_record_fields": list(NORMALIZED_REJECTED_FIELDS),
        "draft_validation_summary": summary,
        "errors_by_market_id": errors_by_market_id,
        "accepted_draft_records": accepted_records,
        "rejected_draft_records": rejected_records,
        "safety_flags": SAFETY_FLAGS,
        "limitations": [
            "Reads only local selected-ingest manual draft, selected-ingest skeleton, selected-ingest review-result, and selected-ingest merged-packet artifacts.",
            "Validates manual draft structure and next-action labels only.",
            "Does not infer outcomes, score markets, estimate probabilities, calculate expected value, choose sides, create dossiers, create orders, or route runtime work.",
        ],
    }


def render_markdown_report(result):
    summary = result["draft_validation_summary"]
    lines = [
        "# Selected Ingest Manual Dossier Draft Validation v1",
        "",
        "## Summary",
        "",
        f"- task_id: {result['task_id']}",
        f"- source_draft_records_path: {result['source_draft_records_path']}",
        f"- source_dossier_skeletons_path: {result['source_dossier_skeletons_path']}",
        f"- source_review_records_result_path: {result['source_review_records_result_path']}",
        f"- source_merged_packets_path: {result['source_merged_packets_path']}",
    ]
    for field in SUMMARY_FIELDS:
        lines.append(f"- {field}: {summary[field]}")
    lines.extend(["- errors_by_market_id:"])
    if not result["errors_by_market_id"]:
        lines.append("  - none")
    else:
        for market_id, errors in result["errors_by_market_id"].items():
            lines.append(f"  - {market_id}: {len(errors)}")

    lines.extend(["", "## Selected Market IDs", ""])
    lines.extend(f"- {market_id}" for market_id in result["selected_market_ids"])

    lines.extend(["", "## Exported Dossier Draft Skeleton Market IDs", ""])
    if result["exported_skeleton_market_ids"]:
        lines.extend(f"- {market_id}" for market_id in result["exported_skeleton_market_ids"])
    else:
        lines.append("- none")

    lines.extend(["", "## Accepted Draft Records", ""])
    if not result["accepted_draft_records"]:
        lines.extend(["- none", ""])
    else:
        for record in result["accepted_draft_records"]:
            lines.extend(
                [
                    f"### record {record['record_index']}: {record['market_id']}",
                    f"- draft_status: {record['draft_status']}",
                    f"- next_manual_action: {record['next_manual_action']}",
                    f"- evidence_summary_by_source_count: {len(record['evidence_summary_by_source'])}",
                    f"- uncertainty_register_count: {len(record['uncertainty_register'])}",
                    f"- open_questions_count: {len(record['open_questions'])}",
                    "",
                ]
            )

    lines.extend(["## Rejected Draft Records", ""])
    if not result["rejected_draft_records"]:
        lines.extend(["- none", ""])
    else:
        for record in result["rejected_draft_records"]:
            lines.extend(
                [
                    f"### record {record['record_index']}: {record['market_id']}",
                    f"- draft_status: {record['draft_status']}",
                    f"- next_manual_action: {record['next_manual_action']}",
                    "- errors:",
                ]
            )
            for error in record["errors"]:
                lines.append(f"  - {error['path']}: {error['code']} - {error['message']}")
            lines.append("")

    lines.extend(["## Errors By Market ID", ""])
    if not result["errors_by_market_id"]:
        lines.extend(["- none", ""])
    else:
        for market_id, errors in result["errors_by_market_id"].items():
            lines.append(f"### {market_id}")
            for error in errors:
                lines.append(f"- {error['path']}: {error['code']} - {error['message']}")
            lines.append("")

    lines.extend(["## Safety Boundary", ""])
    for key in sorted(result["safety_flags"]):
        lines.append(f"- {key}: {str(result['safety_flags'][key]).lower()}")

    lines.extend(["", "## Limitations", ""])
    for limitation in result["limitations"]:
        lines.append(f"- {limitation}")
    return "\n".join(lines).rstrip() + "\n"


def write_selected_ingest_manual_dossier_draft_validation_artifacts(
    draft_records_path=DEFAULT_DRAFT_RECORDS,
    dossier_skeletons_path=DEFAULT_DOSSIER_SKELETONS,
    review_records_result_path=DEFAULT_REVIEW_RECORDS_RESULT,
    merged_packets_path=DEFAULT_MERGED_PACKETS,
    json_output_path=DEFAULT_JSON_RESULT,
    markdown_output_path=DEFAULT_MARKDOWN_REPORT,
    expected_json_output_path=DEFAULT_EXPECTED_JSON_RESULT,
):
    json_output_path = _resolve_path(json_output_path)
    markdown_output_path = _resolve_path(markdown_output_path)
    expected_json_output_path = _resolve_path(expected_json_output_path)
    result = build_selected_ingest_manual_dossier_draft_validation_result(
        draft_records_path=draft_records_path,
        dossier_skeletons_path=dossier_skeletons_path,
        review_records_result_path=review_records_result_path,
        merged_packets_path=merged_packets_path,
        json_output_path=json_output_path,
        markdown_output_path=markdown_output_path,
        expected_json_output_path=expected_json_output_path,
    )
    rendered_result = json.dumps(result, indent=2, ensure_ascii=True) + "\n"
    rendered_markdown = render_markdown_report(result)

    json_output_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_output_path.parent.mkdir(parents=True, exist_ok=True)
    expected_json_output_path.parent.mkdir(parents=True, exist_ok=True)
    json_output_path.write_text(rendered_result, encoding="utf-8")
    markdown_output_path.write_text(rendered_markdown, encoding="utf-8")
    expected_json_output_path.write_text(rendered_result, encoding="utf-8")
    return {
        "task_id": TASK_ID,
        "json_result_path": _display_path(json_output_path),
        "markdown_report_path": _display_path(markdown_output_path),
        "expected_json_result_path": _display_path(expected_json_output_path),
        "selected_market_ids": list(SELECTED_MARKET_IDS),
        "draft_validation_summary": result["draft_validation_summary"],
    }


def main(argv):
    args = _parse_args(argv)
    summary = write_selected_ingest_manual_dossier_draft_validation_artifacts(
        draft_records_path=args.draft_records,
        dossier_skeletons_path=args.dossier_skeletons,
        review_records_result_path=args.review_records_result,
        merged_packets_path=args.merged_packets,
        json_output_path=args.json_output,
        markdown_output_path=args.markdown_output,
        expected_json_output_path=args.expected_json_output,
    )
    print(json.dumps(summary, indent=2, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
