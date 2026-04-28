import argparse
import copy
import json
import sys
from pathlib import Path


TASK_ID = "PMBOT-INGEST-013-SELECTED-INGEST-DOSSIER-HUMAN-REVIEW-RECORD-GATE"
SCHEMA_VERSION = "selected_ingest_dossier_human_review_records_result.v1"
MARKDOWN_VERSION = "selected_ingest_dossier_human_review_records_report.v1"
ROOT = Path(__file__).resolve().parents[2]
DEFAULT_REVIEW_RECORDS = ROOT / "pm_bot" / "research" / "selected_ingest_dossier_human_review_records_fixture.v1.json"
DEFAULT_REVIEW_PACK = ROOT / "pm_bot" / "research" / "selected_ingest_dossier_human_review_pack.v1.json"
DEFAULT_VALIDATION_RESULT = ROOT / "pm_bot" / "research" / "selected_ingest_manual_dossier_draft_validation_result.v1.json"
DEFAULT_DOSSIER_SKELETONS = ROOT / "pm_bot" / "research" / "selected_ingest_dossier_draft_skeletons.v1.json"
DEFAULT_JSON_RESULT = ROOT / "pm_bot" / "research" / "selected_ingest_dossier_human_review_records_result.v1.json"
DEFAULT_MARKDOWN_REPORT = ROOT / "pm_bot" / "research" / "selected_ingest_dossier_human_review_records_report.v1.md"
DEFAULT_EXPECTED_JSON_RESULT = ROOT / "pm_bot" / "research" / "expected_selected_ingest_dossier_human_review_records_result.v1.json"

SELECTED_MARKET_IDS = ("692258", "824952", "691547", "597964", "598936")
ALLOWED_REVIEW_STATUSES = (
    "not_reviewed",
    "review_completed",
    "needs_revision",
    "review_rejected",
)
ALLOWED_REVIEW_OUTCOMES = (
    "approved_for_final_dossier_draft",
    "needs_draft_revision",
    "rejected_for_research_quality",
    "watch_only",
)
REQUIRED_APPROVAL_REVIEW_CHECKS = (
    "evidence_matches_resolution_criteria",
    "uncertainty_register_reviewed",
    "missing_information_reviewed",
    "no_trading_recommendation_present",
    "no_probability_or_ev_present",
    "no_side_recommendation_present",
    "no_market_decision_present",
)
ALLOWED_REVIEW_RECORD_FIELDS = {
    "market_id",
    "human_review_status",
    "human_review_outcome",
    "reviewer_notes",
    "review_checks",
    "requested_revision_items",
    "quality_flags",
    "next_manual_action",
}
REVIEW_RECORD_METADATA_FIELDS = {
    "schema_version",
    "task_id",
    "deterministic",
    "human_review_record_format",
    "review_record_format",
    "instructions",
    "notes",
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
PROHIBITED_FIELD_EXCEPTIONS = set(REQUIRED_APPROVAL_REVIEW_CHECKS)
PROHIBITED_MACHINE_READABLE_LANGUAGE = (
    "completed_dossier",
    "final_dossier",
    "bet_recommendation",
    "trade_recommendation",
    "market_decision",
)
PROHIBITED_LANGUAGE_VALUE_EXCEPTIONS = {"approved_for_final_dossier_draft"}
PROHIBITED_LANGUAGE_KEY_EXCEPTIONS = set(REQUIRED_APPROVAL_REVIEW_CHECKS)
NORMALIZED_ACCEPTED_FIELDS = (
    "record_index",
    "market_id",
    "human_review_status",
    "human_review_outcome",
    "reviewer_notes",
    "review_checks",
    "requested_revision_items",
    "quality_flags",
    "next_manual_action",
    "review_pack_status",
)
NORMALIZED_REJECTED_FIELDS = (
    "record_index",
    "market_id",
    "human_review_status",
    "human_review_outcome",
    "review_pack_status",
    "errors",
)
SUMMARY_FIELDS = (
    "review_records_read",
    "review_records_accepted",
    "review_records_rejected",
    "approved_for_final_dossier_draft",
    "needs_draft_revision",
    "rejected_for_research_quality",
    "watch_only",
)
SAFETY_FLAGS = {
    "offline_only": True,
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
    "final_dossier_drafts": False,
    "completed_dossiers": False,
}


def _parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Validate deterministic offline selected-ingest dossier human review records."
    )
    parser.add_argument("--review-records", default=str(DEFAULT_REVIEW_RECORDS.relative_to(ROOT)))
    parser.add_argument("--review-pack", default=str(DEFAULT_REVIEW_PACK.relative_to(ROOT)))
    parser.add_argument("--validation-result", default=str(DEFAULT_VALIDATION_RESULT.relative_to(ROOT)))
    parser.add_argument("--dossier-skeletons", default=str(DEFAULT_DOSSIER_SKELETONS.relative_to(ROOT)))
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
            if key_text not in PROHIBITED_FIELD_EXCEPTIONS and _field_tokens(key_text) & PROHIBITED_FIELD_TOKENS:
                findings.append(
                    _error(
                        f"prohibited_human_review_field:{key_text}",
                        path,
                        "Trading, execution, recommendation, bet, stake, size, price, scoring, signal, probability, EV, wallet, private-key, side, buy/sell, and market-decision fields are prohibited in selected-ingest dossier human review records.",
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
            if key_text not in PROHIBITED_LANGUAGE_KEY_EXCEPTIONS:
                key_phrase = _matched_prohibited_language(key_text)
                if key_phrase:
                    findings.append(
                        _error(
                            f"prohibited_dossier_language:{key_phrase}",
                            path,
                            "Completed/final dossier, recommendation, and market-decision language is prohibited in machine-readable human review record fields.",
                        )
                    )
            findings.extend(_walk_prohibited_language(nested, path))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            findings.extend(_walk_prohibited_language(item, f"{prefix}[{index}]"))
    elif isinstance(value, str):
        cleaned = value.strip()
        if cleaned not in PROHIBITED_LANGUAGE_VALUE_EXCEPTIONS:
            phrase = _matched_prohibited_language(cleaned)
            if phrase:
                findings.append(
                    _error(
                        f"prohibited_dossier_language:{phrase}",
                        prefix,
                        "Completed/final dossier, recommendation, and market-decision language is prohibited in machine-readable human review record fields.",
                    )
                )
    return findings


def _review_record_entries(payload):
    if isinstance(payload, list):
        return payload, None
    if not isinstance(payload, dict):
        return None, _error(
            "review_records_payload_not_object_or_list",
            "human_review_records",
            "Selected-ingest human review records JSON must be an object or a list.",
        )

    for field in ("human_review_records", "review_records", "records"):
        if field in payload:
            if not isinstance(payload[field], list):
                return None, _error("review_records_not_list", field, f"{field} must be a list.")
            return payload[field], None

    entries = []
    for market_id, value in payload.items():
        if market_id in REVIEW_RECORD_METADATA_FIELDS:
            continue
        if isinstance(value, dict):
            entry = copy.deepcopy(value)
            entry.setdefault("market_id", str(market_id))
            entries.append(entry)
        else:
            entries.append({"market_id": str(market_id), "__invalid_human_review_record__": value})
    return entries, None


def _review_market_id(record, index):
    if isinstance(record, dict) and _non_empty_text(record.get("market_id")):
        return record["market_id"].strip()
    return f"human_review_record_index_{index}"


def _selected_market_ids_from_payload(payload, path_label):
    selected = payload.get("selected_market_ids")
    if tuple(str(market_id) for market_id in selected or ()) != SELECTED_MARKET_IDS:
        raise ValueError(f"{path_label} has unexpected selected_market_ids")
    return set(str(market_id) for market_id in selected)


def _load_review_pack_context(path):
    payload = _load_json(path)
    if not isinstance(payload, dict):
        raise ValueError("selected-ingest dossier human review pack payload must be a JSON object")
    selected_market_ids = _selected_market_ids_from_payload(payload, "selected-ingest dossier human review pack")
    packs = payload.get("human_review_packs")
    if not isinstance(packs, list):
        raise ValueError("selected-ingest dossier human review pack payload must contain human_review_packs list")

    exported_market_ids = payload.get("exported_market_ids")
    exported_market_id_set = {
        _clean_text(market_id)
        for market_id in exported_market_ids
        if _clean_text(market_id)
    } if isinstance(exported_market_ids, list) else set()

    pack_by_market_id = {}
    for pack in packs:
        if isinstance(pack, dict) and _non_empty_text(pack.get("market_id")):
            market_id = _clean_text(pack.get("market_id"))
            if not exported_market_id_set or market_id in exported_market_id_set:
                pack_by_market_id[market_id] = pack

    pack_fields = payload.get("human_review_pack_item_fields")
    if not isinstance(pack_fields, list):
        pack_fields = sorted({str(field) for pack in packs if isinstance(pack, dict) for field in pack})
    immutable_fields = sorted(set(str(field) for field in pack_fields) - ALLOWED_REVIEW_RECORD_FIELDS)
    return payload, selected_market_ids, pack_by_market_id, immutable_fields


def _market_ids_from_records(payload, fields):
    market_ids = set()
    for field in fields:
        records = payload.get(field)
        if not isinstance(records, list):
            continue
        for record in records:
            if isinstance(record, dict) and _non_empty_text(record.get("market_id")):
                market_ids.add(_clean_text(record.get("market_id")))
    return market_ids


def _market_ids_from_skeletons(payload):
    skeletons = payload.get("dossier_draft_skeletons")
    if not isinstance(skeletons, list):
        raise ValueError("selected-ingest dossier skeleton payload must contain dossier_draft_skeletons list")
    return {
        _clean_text(skeleton.get("market_id"))
        for skeleton in skeletons
        if isinstance(skeleton, dict) and _non_empty_text(skeleton.get("market_id"))
    }


def _validate_string_list(value, path, errors):
    if not isinstance(value, list):
        _append(errors, "review_field_not_list", path, f"{path} must be a list of non-empty strings.")
        return []
    normalized = []
    seen = set()
    for index, item in enumerate(value):
        item_path = f"{path}[{index}]"
        if not isinstance(item, str):
            _append(errors, "review_list_item_not_string", item_path, f"{item_path} must be a string.")
            continue
        cleaned = item.strip()
        if not cleaned:
            _append(errors, "review_list_item_empty", item_path, f"{item_path} must be a non-empty string.")
            continue
        if cleaned in seen:
            _append(errors, "review_list_item_duplicate", item_path, f"{item_path} duplicates an earlier item.")
            continue
        seen.add(cleaned)
        normalized.append(cleaned)
    return normalized


def _validate_review_checks(value, errors):
    if not isinstance(value, dict):
        _append(errors, "review_checks_not_object", "review_checks", "review_checks must be an object when provided.")
        return {}
    normalized = {}
    for key in sorted(value):
        path = f"review_checks.{key}"
        if not isinstance(value[key], bool):
            _append(errors, "review_check_not_boolean", path, f"{path} must be a boolean.")
            continue
        normalized[str(key)] = value[key]
    return normalized


def _required_approval_checks_are_true(review_checks, errors):
    if not isinstance(review_checks, dict):
        return
    for check_name in REQUIRED_APPROVAL_REVIEW_CHECKS:
        if review_checks.get(check_name) is not True:
            _append(
                errors,
                f"required_approval_review_check_not_true:{check_name}",
                f"review_checks.{check_name}",
                f"review_checks.{check_name} must be true before approved_for_final_dossier_draft can be accepted.",
            )


def _validate_record(record, index, review_pack_market_ids, selected_market_ids, immutable_fields):
    market_id = _review_market_id(record, index)
    errors = []
    if not isinstance(record, dict):
        return market_id, [_error("human_review_record_not_object", f"human_review_records[{index}]", "Each human review record must be an object.")]

    errors.extend(_walk_prohibited_fields(record))
    errors.extend(_walk_prohibited_language(record))

    if not _non_empty_text(record.get("market_id")):
        _append(errors, "missing_human_review_market_id", "market_id", "Human review record must include a non-empty market_id.")
    elif market_id not in review_pack_market_ids:
        if market_id in selected_market_ids:
            _append(
                errors,
                "selected_market_id_not_in_review_pack",
                "market_id",
                "Human review record market_id was selected but is not present in selected_ingest_dossier_human_review_pack.v1.json.",
            )
        else:
            _append(
                errors,
                "unknown_market_id",
                "market_id",
                "Human review record market_id is absent from the local selected-ingest review pack, draft validation, and skeleton artifacts.",
            )

    for field in sorted(set(record) - ALLOWED_REVIEW_RECORD_FIELDS):
        if field in immutable_fields:
            _append(
                errors,
                f"immutable_review_pack_field_override:{field}",
                field,
                f"{field} is immutable review pack content and cannot be supplied by a human review record.",
            )
        else:
            _append(errors, f"unexpected_human_review_field:{field}", field, f"{field} is not an allowed selected-ingest human review record field.")

    review_status = record.get("human_review_status")
    if "human_review_status" not in record:
        _append(errors, "missing_human_review_status", "human_review_status", "human_review_status is required.")
    elif review_status not in ALLOWED_REVIEW_STATUSES:
        _append(errors, "invalid_human_review_status", "human_review_status", "human_review_status is not in the allowed status set.")

    review_outcome = record.get("human_review_outcome")
    if "human_review_outcome" not in record:
        _append(errors, "missing_human_review_outcome", "human_review_outcome", "human_review_outcome is required.")
    elif review_outcome not in ALLOWED_REVIEW_OUTCOMES:
        _append(errors, "invalid_human_review_outcome", "human_review_outcome", "human_review_outcome is not in the allowed outcome set.")

    if "reviewer_notes" in record and not isinstance(record["reviewer_notes"], str):
        _append(errors, "reviewer_notes_not_string", "reviewer_notes", "reviewer_notes must be a string.")

    if "next_manual_action" in record and not isinstance(record["next_manual_action"], str):
        _append(errors, "next_manual_action_not_string", "next_manual_action", "next_manual_action must be a string when provided.")

    review_checks = {}
    if "review_checks" in record:
        review_checks = _validate_review_checks(record["review_checks"], errors)
    elif review_outcome == "approved_for_final_dossier_draft":
        _append(errors, "missing_review_checks", "review_checks", "review_checks is required for approved_for_final_dossier_draft.")

    requested_revision_items = []
    if "requested_revision_items" in record:
        requested_revision_items = _validate_string_list(record["requested_revision_items"], "requested_revision_items", errors)
    if review_outcome == "needs_draft_revision" and not requested_revision_items:
        _append(
            errors,
            "needs_draft_revision_requires_requested_revision_items",
            "requested_revision_items",
            "human_review_outcome needs_draft_revision requires non-empty requested_revision_items.",
        )

    if "quality_flags" in record:
        _validate_string_list(record["quality_flags"], "quality_flags", errors)

    if review_outcome == "approved_for_final_dossier_draft":
        _required_approval_checks_are_true(review_checks, errors)

    if review_outcome == "rejected_for_research_quality" and not _non_empty_text(record.get("reviewer_notes")):
        _append(
            errors,
            "rejected_for_research_quality_requires_reviewer_notes",
            "reviewer_notes",
            "human_review_outcome rejected_for_research_quality requires non-empty reviewer_notes.",
        )

    errors.sort(key=lambda item: (item["path"], item["code"], item["message"]))
    return market_id, errors


def _normalized_check_map(value):
    if not isinstance(value, dict):
        return {}
    ordered = {}
    for key in REQUIRED_APPROVAL_REVIEW_CHECKS:
        if key in value and isinstance(value[key], bool):
            ordered[key] = value[key]
    for key in sorted(set(value) - set(REQUIRED_APPROVAL_REVIEW_CHECKS)):
        if isinstance(value[key], bool):
            ordered[str(key)] = value[key]
    return ordered


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


def _normalized_accepted_record(record, index, market_id, pack):
    normalized = {
        "record_index": index,
        "market_id": market_id,
        "human_review_status": _clean_text(record.get("human_review_status")),
        "human_review_outcome": _clean_text(record.get("human_review_outcome")),
        "reviewer_notes": _clean_text(record.get("reviewer_notes")),
        "review_checks": _normalized_check_map(record.get("review_checks")),
        "requested_revision_items": _normalized_string_list(record.get("requested_revision_items")),
        "quality_flags": _normalized_string_list(record.get("quality_flags")),
        "next_manual_action": _clean_text(record.get("next_manual_action")),
        "review_pack_status": _clean_text(pack.get("review_pack_status")) if isinstance(pack, dict) else "",
    }
    return {field: normalized[field] for field in NORMALIZED_ACCEPTED_FIELDS}


def _normalized_rejected_record(record, index, market_id, pack, errors):
    normalized = {
        "record_index": index,
        "market_id": market_id,
        "human_review_status": _clean_text(record.get("human_review_status")) if isinstance(record, dict) else "",
        "human_review_outcome": _clean_text(record.get("human_review_outcome")) if isinstance(record, dict) else "",
        "review_pack_status": _clean_text(pack.get("review_pack_status")) if isinstance(pack, dict) else "",
        "errors": errors,
    }
    return {field: normalized[field] for field in NORMALIZED_REJECTED_FIELDS}


def _summary(review_records_read, accepted_records, rejected_records):
    outcome_counts = {outcome: 0 for outcome in ALLOWED_REVIEW_OUTCOMES}
    for record in accepted_records:
        outcome_counts[record["human_review_outcome"]] += 1
    return {
        "review_records_read": review_records_read,
        "review_records_accepted": len(accepted_records),
        "review_records_rejected": len(rejected_records),
        "approved_for_final_dossier_draft": outcome_counts["approved_for_final_dossier_draft"],
        "needs_draft_revision": outcome_counts["needs_draft_revision"],
        "rejected_for_research_quality": outcome_counts["rejected_for_research_quality"],
        "watch_only": outcome_counts["watch_only"],
    }


def _errors_by_market_id(rejected_records):
    errors = {}
    for record in rejected_records:
        errors.setdefault(record["market_id"], []).extend(record["errors"])
    return {market_id: errors[market_id] for market_id in sorted(errors)}


def _selected_sort_key(record):
    market_id = record["market_id"]
    try:
        market_index = SELECTED_MARKET_IDS.index(market_id)
    except ValueError:
        market_index = len(SELECTED_MARKET_IDS)
    return (market_index, market_id, record.get("record_index", -1))


def build_selected_ingest_dossier_human_review_record_result(
    review_records_path=DEFAULT_REVIEW_RECORDS,
    review_pack_path=DEFAULT_REVIEW_PACK,
    validation_result_path=DEFAULT_VALIDATION_RESULT,
    dossier_skeletons_path=DEFAULT_DOSSIER_SKELETONS,
    json_output_path=DEFAULT_JSON_RESULT,
    markdown_output_path=DEFAULT_MARKDOWN_REPORT,
    expected_json_output_path=DEFAULT_EXPECTED_JSON_RESULT,
):
    review_records_path = _resolve_path(review_records_path)
    review_pack_path = _resolve_path(review_pack_path)
    validation_result_path = _resolve_path(validation_result_path)
    dossier_skeletons_path = _resolve_path(dossier_skeletons_path)
    json_output_path = _resolve_path(json_output_path)
    markdown_output_path = _resolve_path(markdown_output_path)
    expected_json_output_path = _resolve_path(expected_json_output_path)

    review_records_payload = _load_json(review_records_path)
    review_pack_payload, selected_market_ids, pack_by_market_id, immutable_fields = _load_review_pack_context(review_pack_path)
    validation_payload = _load_json(validation_result_path)
    skeleton_payload = _load_json(dossier_skeletons_path)
    _selected_market_ids_from_payload(validation_payload, "selected-ingest manual dossier draft validation result")
    _selected_market_ids_from_payload(skeleton_payload, "selected-ingest dossier draft skeletons")

    review_pack_market_ids = set(pack_by_market_id)
    _market_ids_from_records(validation_payload, ("accepted_draft_records", "rejected_draft_records"))
    _market_ids_from_skeletons(skeleton_payload)
    entries, payload_error = _review_record_entries(review_records_payload)
    accepted_records = []
    rejected_records = []

    if payload_error is not None:
        rejected_records.append(_normalized_rejected_record({}, 0, "payload", None, [payload_error]))
        entries = []

    for index, record in enumerate(entries or []):
        market_id, errors = _validate_record(
            record,
            index,
            review_pack_market_ids,
            selected_market_ids,
            immutable_fields,
        )
        pack = pack_by_market_id.get(market_id)
        if errors:
            rejected_records.append(_normalized_rejected_record(record, index, market_id, pack, errors))
            continue
        accepted_records.append(_normalized_accepted_record(record, index, market_id, pack))

    accepted_records.sort(key=_selected_sort_key)
    rejected_records.sort(key=_selected_sort_key)
    errors_by_market_id = _errors_by_market_id(rejected_records)
    summary = _summary(len(entries or []), accepted_records, rejected_records)

    return {
        "schema_version": SCHEMA_VERSION,
        "markdown_version": MARKDOWN_VERSION,
        "task_id": TASK_ID,
        "deterministic": True,
        "source_review_records_path": _display_path(review_records_path),
        "source_review_records_schema_version": review_records_payload.get("schema_version") if isinstance(review_records_payload, dict) else None,
        "source_review_pack_path": _display_path(review_pack_path),
        "source_review_pack_schema_version": review_pack_payload.get("schema_version"),
        "source_validation_result_path": _display_path(validation_result_path),
        "source_validation_result_schema_version": validation_payload.get("schema_version"),
        "source_dossier_skeletons_path": _display_path(dossier_skeletons_path),
        "source_dossier_skeletons_schema_version": skeleton_payload.get("schema_version"),
        "json_result_path": _display_path(json_output_path),
        "markdown_report_path": _display_path(markdown_output_path),
        "expected_json_result_path": _display_path(expected_json_output_path),
        "selected_market_ids": list(SELECTED_MARKET_IDS),
        "review_pack_market_ids": sorted(review_pack_market_ids),
        "allowed_human_review_statuses": list(ALLOWED_REVIEW_STATUSES),
        "allowed_human_review_outcomes": list(ALLOWED_REVIEW_OUTCOMES),
        "required_approval_review_checks": list(REQUIRED_APPROVAL_REVIEW_CHECKS),
        "allowed_review_record_fields": sorted(ALLOWED_REVIEW_RECORD_FIELDS),
        "immutable_review_pack_fields": immutable_fields,
        "accepted_record_fields": list(NORMALIZED_ACCEPTED_FIELDS),
        "rejected_record_fields": list(NORMALIZED_REJECTED_FIELDS),
        "review_summary": summary,
        "errors_by_market_id": errors_by_market_id,
        "accepted_human_review_records": accepted_records,
        "rejected_human_review_records": rejected_records,
        "safety_flags": SAFETY_FLAGS,
        "limitations": [
            "Reads only local selected-ingest human review records, selected-ingest dossier review packs, draft validation, and skeleton artifacts.",
            "Validates human review record structure and operational review labels only.",
            "Does not create final dossier drafts, completed dossiers, recommendations, scores, probabilities, EV calculations, side choices, orders, paper orders, runtime actions, or market decisions.",
        ],
    }


def render_markdown_report(result):
    summary = result["review_summary"]
    lines = [
        "# Selected Ingest Dossier Human Review Records v1",
        "",
        "## Summary",
        "",
        f"- task_id: {result['task_id']}",
        f"- source_review_records_path: {result['source_review_records_path']}",
        f"- source_review_pack_path: {result['source_review_pack_path']}",
        f"- source_validation_result_path: {result['source_validation_result_path']}",
        f"- source_dossier_skeletons_path: {result['source_dossier_skeletons_path']}",
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

    lines.extend(["", "## Review Pack Market IDs", ""])
    if result["review_pack_market_ids"]:
        lines.extend(f"- {market_id}" for market_id in result["review_pack_market_ids"])
    else:
        lines.append("- none")

    lines.extend(["", "## Accepted Human Review Records", ""])
    if not result["accepted_human_review_records"]:
        lines.extend(["- none", ""])
    else:
        for record in result["accepted_human_review_records"]:
            lines.extend(
                [
                    f"### record {record['record_index']}: {record['market_id']}",
                    f"- human_review_status: {record['human_review_status']}",
                    f"- human_review_outcome: {record['human_review_outcome']}",
                    f"- review_pack_status: {record['review_pack_status']}",
                    f"- requested_revision_items_count: {len(record['requested_revision_items'])}",
                    f"- quality_flags_count: {len(record['quality_flags'])}",
                    "",
                ]
            )

    lines.extend(["## Rejected Human Review Records", ""])
    if not result["rejected_human_review_records"]:
        lines.extend(["- none", ""])
    else:
        for record in result["rejected_human_review_records"]:
            lines.extend(
                [
                    f"### record {record['record_index']}: {record['market_id']}",
                    f"- human_review_status: {record['human_review_status']}",
                    f"- human_review_outcome: {record['human_review_outcome']}",
                    f"- review_pack_status: {record['review_pack_status']}",
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


def write_selected_ingest_dossier_human_review_record_artifacts(
    review_records_path=DEFAULT_REVIEW_RECORDS,
    review_pack_path=DEFAULT_REVIEW_PACK,
    validation_result_path=DEFAULT_VALIDATION_RESULT,
    dossier_skeletons_path=DEFAULT_DOSSIER_SKELETONS,
    json_output_path=DEFAULT_JSON_RESULT,
    markdown_output_path=DEFAULT_MARKDOWN_REPORT,
    expected_json_output_path=DEFAULT_EXPECTED_JSON_RESULT,
):
    json_output_path = _resolve_path(json_output_path)
    markdown_output_path = _resolve_path(markdown_output_path)
    expected_json_output_path = _resolve_path(expected_json_output_path)
    result = build_selected_ingest_dossier_human_review_record_result(
        review_records_path=review_records_path,
        review_pack_path=review_pack_path,
        validation_result_path=validation_result_path,
        dossier_skeletons_path=dossier_skeletons_path,
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
        "review_pack_market_ids": result["review_pack_market_ids"],
        "review_summary": result["review_summary"],
    }


def main(argv):
    args = _parse_args(argv)
    summary = write_selected_ingest_dossier_human_review_record_artifacts(
        review_records_path=args.review_records,
        review_pack_path=args.review_pack,
        validation_result_path=args.validation_result,
        dossier_skeletons_path=args.dossier_skeletons,
        json_output_path=args.json_output,
        markdown_output_path=args.markdown_output,
        expected_json_output_path=args.expected_json_output,
    )
    print(json.dumps(summary, indent=2, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
