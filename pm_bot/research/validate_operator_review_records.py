import argparse
import copy
import importlib.util
import json
import sys
from pathlib import Path


TASK_ID = "PMBOT-RESEARCH-011-OPERATOR-REVIEW-RECORD-GATE"
SCHEMA_VERSION = "operator_review_records_result.v1"
MARKDOWN_VERSION = "operator_review_records_report.v1"
ROOT = Path(__file__).resolve().parents[2]
DEFAULT_REVIEW_RECORDS = ROOT / "pm_bot" / "research" / "operator_review_records_fixture.v1.json"
DEFAULT_OPERATOR_REVIEW_QUEUE = ROOT / "pm_bot" / "research" / "operator_review_queue.v1.json"
DEFAULT_MERGED_PACKETS = ROOT / "pm_bot" / "research" / "merged_manual_research_packets.v1.json"
DEFAULT_JSON_RESULT = ROOT / "pm_bot" / "research" / "operator_review_records_result.v1.json"
DEFAULT_MARKDOWN_REPORT = ROOT / "pm_bot" / "research" / "operator_review_records_report.v1.md"
DEFAULT_EXPECTED_JSON_RESULT = ROOT / "pm_bot" / "research" / "expected_operator_review_records_result.v1.json"
VALIDATOR_PATH = ROOT / "pm_bot" / "research" / "validate_manual_research_packets.py"


ALLOWED_REVIEW_STATUSES = (
    "not_reviewed",
    "review_completed",
    "needs_more_information",
    "review_rejected",
)
ALLOWED_REVIEW_OUTCOMES = (
    "ready_for_dossier_drafting",
    "needs_more_information",
    "research_quality_rejected",
    "watch_only_manual",
)
REQUIRED_READY_REVIEW_CHECKS = (
    "resolution_criteria_checked",
    "evidence_structure_checked",
    "source_coverage_checked",
    "missing_information_reviewed",
    "no_trading_recommendation_present",
)
ALLOWED_REVIEW_RECORD_FIELDS = {
    "market_id",
    "review_status",
    "review_outcome",
    "reviewer_notes",
    "review_checks",
    "requested_followup_information",
    "quality_flags",
}
REVIEW_RECORD_METADATA_FIELDS = {
    "schema_version",
    "task_id",
    "deterministic",
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
    "side",
    "sides",
}
PROHIBITED_FIELD_EXCEPTIONS = {"no_trading_recommendation_present"}
NORMALIZED_ACCEPTED_FIELDS = (
    "market_id",
    "review_status",
    "review_outcome",
    "reviewer_notes",
    "review_checks",
    "requested_followup_information",
    "quality_flags",
    "queue_group",
    "packet_completion_status",
)
NORMALIZED_REJECTED_FIELDS = (
    "market_id",
    "review_status",
    "review_outcome",
    "queue_group",
    "packet_completion_status",
    "errors",
)
SUMMARY_FIELDS = (
    "review_records_read",
    "review_records_accepted",
    "review_records_rejected",
    "ready_for_dossier_drafting",
    "needs_more_information",
    "research_quality_rejected",
    "watch_only_manual",
)
SAFETY_FLAGS = {
    "offline_only": True,
    "live_fetchers": False,
    "network_api_calls": False,
    "credentials": False,
    "wallet_private_keys": False,
    "real_orders": False,
    "live_trading": False,
    "runtime_wiring": False,
    "dispatcher_run_codex_touched": False,
    "prompt_automation": False,
    "codex_copy_roots": False,
    "completed_dossiers": False,
    "paper_orders": False,
    "betting_recommendations": False,
    "truth_inference": False,
    "market_scoring": False,
}


def _parse_args(argv):
    parser = argparse.ArgumentParser(description="Validate deterministic offline PMBOT operator review records.")
    parser.add_argument("--review-records", default=str(DEFAULT_REVIEW_RECORDS.relative_to(ROOT)))
    parser.add_argument("--operator-review-queue", default=str(DEFAULT_OPERATOR_REVIEW_QUEUE.relative_to(ROOT)))
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


def _load_validator_contract():
    spec = importlib.util.spec_from_file_location("manual_research_packet_validator_contract", VALIDATOR_PATH)
    module = importlib.util.module_from_spec(spec)
    if spec.loader is None:
        raise RuntimeError(f"Unable to load validator contract from {VALIDATOR_PATH}")
    spec.loader.exec_module(module)
    return {"module": module, "schema_version": module.SCHEMA_VERSION}


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
                        f"prohibited_review_field:{key_text}",
                        path,
                        "Trading, execution, recommendation, bet, stake, target, scoring, probability, signal, wallet, private-key, and side fields are prohibited in operator review records.",
                    )
                )
            findings.extend(_walk_prohibited_fields(nested, path))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            findings.extend(_walk_prohibited_fields(item, f"{prefix}[{index}]"))
    return findings


def _packet_sort_key(packet):
    rank = packet.get("shortlist_rank")
    rank_key = rank if isinstance(rank, int) else 10**9
    return (rank_key, _clean_text(packet.get("market_id")), _clean_text(packet.get("title") or packet.get("question")))


def _load_merged_packets(merged_packets_path):
    payload = _load_json(merged_packets_path)
    packets = payload.get("packets")
    if not isinstance(packets, list):
        raise ValueError("merged packet payload must contain a packets list")
    return payload, sorted(packets, key=_packet_sort_key)


def _queue_items(queue_payload):
    groups = queue_payload.get("groups")
    if not isinstance(groups, dict):
        raise ValueError("operator review queue payload must contain groups")
    for group_name in sorted(groups):
        group_items = groups[group_name]
        if not isinstance(group_items, list):
            continue
        for item in group_items:
            if isinstance(item, dict):
                yield group_name, item


def _build_market_context(queue_payload, packets):
    packets_by_market_id = {
        packet["market_id"]: packet
        for packet in packets
        if isinstance(packet, dict) and _non_empty_text(packet.get("market_id"))
    }
    contexts = {}
    for group_name, item in _queue_items(queue_payload):
        market_id = _clean_text(item.get("market_id"))
        if not market_id:
            continue
        packet = packets_by_market_id.get(market_id)
        contexts[market_id] = {
            "queue_group": group_name,
            "queue_item": item,
            "packet": packet,
            "packet_completion_status": _clean_text(packet.get("completion_status")) if isinstance(packet, dict) else "",
        }
    return contexts


def _immutable_packet_fields(packets, queue_payload):
    fields = set()
    for packet in packets:
        if isinstance(packet, dict):
            fields.update(str(field) for field in packet)
    for _, item in _queue_items(queue_payload):
        fields.update(str(field) for field in item)
    fields.discard("market_id")
    return fields


def _review_record_entries(review_records_payload):
    if isinstance(review_records_payload, list):
        return review_records_payload, None
    if not isinstance(review_records_payload, dict):
        return None, _error("review_records_payload_not_object_or_list", "review_records", "Review records JSON must be an object or a list.")

    for field in ("review_records", "records"):
        if field in review_records_payload:
            if not isinstance(review_records_payload[field], list):
                return None, _error("review_records_not_list", field, f"{field} must be a list.")
            return review_records_payload[field], None

    entries = []
    for market_id, value in review_records_payload.items():
        if market_id in REVIEW_RECORD_METADATA_FIELDS:
            continue
        if isinstance(value, dict):
            entry = copy.deepcopy(value)
            entry.setdefault("market_id", str(market_id))
            entries.append(entry)
        else:
            entries.append({"market_id": str(market_id), "__invalid_review_record__": value})
    return entries, None


def _review_record_market_id(record, index):
    if isinstance(record, dict) and _non_empty_text(record.get("market_id")):
        return record["market_id"].strip()
    return f"review_record_index_{index}"


def _validate_string_list(value, path, errors, required_non_empty_items=True):
    if not isinstance(value, list):
        _append(errors, "review_field_not_list", path, f"{path} must be a list.")
        return []
    normalized = []
    seen = set()
    for index, item in enumerate(value):
        item_path = f"{path}[{index}]"
        if not isinstance(item, str):
            _append(errors, "review_list_item_not_string", item_path, f"{item_path} must be a string.")
            continue
        cleaned = item.strip()
        if required_non_empty_items and not cleaned:
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


def _required_ready_checks_are_true(review_checks, errors):
    if not isinstance(review_checks, dict):
        return
    for check_name in REQUIRED_READY_REVIEW_CHECKS:
        if review_checks.get(check_name) is not True:
            _append(
                errors,
                f"required_ready_review_check_not_true:{check_name}",
                f"review_checks.{check_name}",
                f"review_checks.{check_name} must be true before ready_for_dossier_drafting can be accepted.",
            )


def _validate_record(record, index, market_contexts, immutable_fields, seen_market_ids):
    market_id = _review_record_market_id(record, index)
    errors = []
    if not isinstance(record, dict):
        return market_id, [_error("review_record_not_object", f"review_records[{index}]", "Each review record must be an object.")]

    errors.extend(_walk_prohibited_fields(record))

    if not _non_empty_text(record.get("market_id")):
        _append(errors, "missing_review_market_id", "market_id", "Review record must include a non-empty market_id.")
    elif market_id not in market_contexts:
        _append(errors, "unknown_market_id", "market_id", "Review record market_id is not present in the operator review queue and merged packet set.")

    if market_id in seen_market_ids:
        _append(errors, "duplicate_review_market_id", "market_id", "Only one operator review record per market_id is allowed.")
    seen_market_ids.add(market_id)

    for field in sorted(set(record) - ALLOWED_REVIEW_RECORD_FIELDS):
        if field in immutable_fields:
            _append(errors, f"immutable_packet_field_override:{field}", field, f"{field} is immutable packet or queue content and cannot be supplied by an operator review record.")
        else:
            _append(errors, f"unexpected_review_field:{field}", field, f"{field} is not an allowed operator review record field.")

    review_status = record.get("review_status")
    if "review_status" not in record:
        _append(errors, "missing_review_status", "review_status", "review_status is required.")
    elif review_status not in ALLOWED_REVIEW_STATUSES:
        _append(errors, "invalid_review_status", "review_status", "review_status is not in the allowed status set.")

    review_outcome = record.get("review_outcome")
    if "review_outcome" not in record:
        _append(errors, "missing_review_outcome", "review_outcome", "review_outcome is required.")
    elif review_outcome not in ALLOWED_REVIEW_OUTCOMES:
        _append(errors, "invalid_review_outcome", "review_outcome", "review_outcome is not in the allowed outcome set.")

    if "reviewer_notes" in record and not isinstance(record["reviewer_notes"], str):
        _append(errors, "reviewer_notes_not_string", "reviewer_notes", "reviewer_notes must be a string.")

    review_checks = {}
    if "review_checks" in record:
        review_checks = _validate_review_checks(record["review_checks"], errors)
    elif review_outcome == "ready_for_dossier_drafting":
        _append(errors, "missing_review_checks", "review_checks", "review_checks is required for ready_for_dossier_drafting.")

    requested_followup_information = []
    if "requested_followup_information" in record:
        requested_followup_information = _validate_string_list(record["requested_followup_information"], "requested_followup_information", errors)
    if review_outcome == "needs_more_information" and not requested_followup_information:
        _append(
            errors,
            "needs_more_information_requires_followup",
            "requested_followup_information",
            "review_outcome needs_more_information requires non-empty requested_followup_information.",
        )

    if "quality_flags" in record:
        _validate_string_list(record["quality_flags"], "quality_flags", errors)

    context = market_contexts.get(market_id)
    if review_outcome == "ready_for_dossier_drafting":
        if context is None or context["queue_group"] != "ready_for_operator_review":
            group = context["queue_group"] if context else "unknown"
            _append(
                errors,
                "ready_outcome_requires_ready_queue_group",
                "review_outcome",
                f"ready_for_dossier_drafting is allowed only for queue group ready_for_operator_review; current group is {group}.",
            )
        _required_ready_checks_are_true(review_checks, errors)

    errors.sort(key=lambda item: (item["path"], item["code"], item["message"]))
    return market_id, errors


def _normalized_check_map(value):
    if not isinstance(value, dict):
        return {}
    ordered = {}
    for key in REQUIRED_READY_REVIEW_CHECKS:
        if key in value and isinstance(value[key], bool):
            ordered[key] = value[key]
    for key in sorted(set(value) - set(REQUIRED_READY_REVIEW_CHECKS)):
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


def _normalized_accepted_record(record, market_id, context):
    normalized = {
        "market_id": market_id,
        "review_status": _clean_text(record.get("review_status")),
        "review_outcome": _clean_text(record.get("review_outcome")),
        "reviewer_notes": _clean_text(record.get("reviewer_notes")),
        "review_checks": _normalized_check_map(record.get("review_checks")),
        "requested_followup_information": _normalized_string_list(record.get("requested_followup_information")),
        "quality_flags": _normalized_string_list(record.get("quality_flags")),
        "queue_group": context["queue_group"],
        "packet_completion_status": context["packet_completion_status"],
    }
    return {field: normalized[field] for field in NORMALIZED_ACCEPTED_FIELDS}


def _normalized_rejected_record(record, market_id, context, errors):
    normalized = {
        "market_id": market_id,
        "review_status": _clean_text(record.get("review_status")) if isinstance(record, dict) else "",
        "review_outcome": _clean_text(record.get("review_outcome")) if isinstance(record, dict) else "",
        "queue_group": context["queue_group"] if context else "",
        "packet_completion_status": context["packet_completion_status"] if context else "",
        "errors": errors,
    }
    return {field: normalized[field] for field in NORMALIZED_REJECTED_FIELDS}


def _summary(review_records_read, accepted_records, rejected_records):
    outcome_counts = {outcome: 0 for outcome in ALLOWED_REVIEW_OUTCOMES}
    for record in accepted_records:
        outcome_counts[record["review_outcome"]] += 1
    return {
        "review_records_read": review_records_read,
        "review_records_accepted": len(accepted_records),
        "review_records_rejected": len(rejected_records),
        "ready_for_dossier_drafting": outcome_counts["ready_for_dossier_drafting"],
        "needs_more_information": outcome_counts["needs_more_information"],
        "research_quality_rejected": outcome_counts["research_quality_rejected"],
        "watch_only_manual": outcome_counts["watch_only_manual"],
    }


def _errors_by_market_id(rejected_records):
    errors = {}
    for record in rejected_records:
        errors.setdefault(record["market_id"], []).extend(record["errors"])
    return {market_id: errors[market_id] for market_id in sorted(errors)}


def build_operator_review_record_result(
    review_records_path=DEFAULT_REVIEW_RECORDS,
    operator_review_queue_path=DEFAULT_OPERATOR_REVIEW_QUEUE,
    merged_packets_path=DEFAULT_MERGED_PACKETS,
    json_output_path=DEFAULT_JSON_RESULT,
    markdown_output_path=DEFAULT_MARKDOWN_REPORT,
):
    review_records_path = _resolve_path(review_records_path)
    operator_review_queue_path = _resolve_path(operator_review_queue_path)
    merged_packets_path = _resolve_path(merged_packets_path)
    json_output_path = _resolve_path(json_output_path)
    markdown_output_path = _resolve_path(markdown_output_path)
    review_records_payload = _load_json(review_records_path)
    queue_payload = _load_json(operator_review_queue_path)
    merged_payload, packets = _load_merged_packets(merged_packets_path)
    validator_contract = _load_validator_contract()
    market_contexts = _build_market_context(queue_payload, packets)
    immutable_fields = _immutable_packet_fields(packets, queue_payload)
    entries, payload_error = _review_record_entries(review_records_payload)
    accepted_records = []
    rejected_records = []
    seen_market_ids = set()

    if payload_error is not None:
        rejected_records.append(
            _normalized_rejected_record({}, "payload", None, [payload_error])
        )
        entries = []

    for index, record in enumerate(entries or []):
        market_id, errors = _validate_record(record, index, market_contexts, immutable_fields, seen_market_ids)
        context = market_contexts.get(market_id)
        if errors:
            rejected_records.append(_normalized_rejected_record(record, market_id, context, errors))
            continue
        accepted_records.append(_normalized_accepted_record(record, market_id, context))

    accepted_records.sort(key=lambda item: (item["market_id"], item["review_outcome"], item["review_status"]))
    rejected_records.sort(key=lambda item: (item["market_id"], item["review_outcome"], item["review_status"]))
    errors_by_market_id = _errors_by_market_id(rejected_records)
    summary = _summary(len(entries or []), accepted_records, rejected_records)

    return {
        "schema_version": SCHEMA_VERSION,
        "markdown_version": MARKDOWN_VERSION,
        "task_id": TASK_ID,
        "deterministic": True,
        "source_review_records_path": _display_path(review_records_path),
        "source_review_records_schema_version": review_records_payload.get("schema_version") if isinstance(review_records_payload, dict) else None,
        "source_operator_review_queue_path": _display_path(operator_review_queue_path),
        "source_operator_review_queue_schema_version": queue_payload.get("schema_version"),
        "source_merged_packets_path": _display_path(merged_packets_path),
        "source_merged_packets_schema_version": merged_payload.get("schema_version"),
        "validator_contract_path": _display_path(VALIDATOR_PATH),
        "validator_contract_schema_version": validator_contract["schema_version"],
        "json_result_path": _display_path(json_output_path),
        "markdown_report_path": _display_path(markdown_output_path),
        "allowed_review_statuses": list(ALLOWED_REVIEW_STATUSES),
        "allowed_review_outcomes": list(ALLOWED_REVIEW_OUTCOMES),
        "required_ready_review_checks": list(REQUIRED_READY_REVIEW_CHECKS),
        "accepted_record_fields": list(NORMALIZED_ACCEPTED_FIELDS),
        "rejected_record_fields": list(NORMALIZED_REJECTED_FIELDS),
        "review_summary": summary,
        "errors_by_market_id": errors_by_market_id,
        "accepted_review_records": accepted_records,
        "rejected_review_records": rejected_records,
        "merged_packet_validation_errors_by_market_id": _merged_packet_validation_errors(packets, validator_contract["module"]),
        "safety_flags": SAFETY_FLAGS,
        "limitations": [
            "Reads only local operator review records, operator review queue, and merged manual research packets.",
            "Records structural operator review outcomes only.",
            "Does not create dossiers, scores, recommendations, orders, runtime actions, or market conclusions.",
        ],
    }


def _merged_packet_validation_errors(packets, validator_module):
    errors = {}
    for packet in packets:
        market_id = _clean_text(packet.get("market_id")) if isinstance(packet, dict) else "packet"
        validation_errors = validator_module.validate_packet(packet)
        if validation_errors:
            errors[market_id] = validation_errors
    return {market_id: errors[market_id] for market_id in sorted(errors)}


def render_markdown_report(result):
    summary = result["review_summary"]
    lines = [
        "# PMBOT Operator Review Records v1",
        "",
        "## Summary",
        "",
        f"- task_id: {result['task_id']}",
        f"- source_review_records_path: {result['source_review_records_path']}",
        f"- source_operator_review_queue_path: {result['source_operator_review_queue_path']}",
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

    lines.extend(["", "## Accepted Review Records", ""])
    if not result["accepted_review_records"]:
        lines.extend(["- none", ""])
    else:
        for record in result["accepted_review_records"]:
            lines.extend(
                [
                    f"### {record['market_id']}",
                    f"- review_status: {record['review_status']}",
                    f"- review_outcome: {record['review_outcome']}",
                    f"- queue_group: {record['queue_group']}",
                    f"- packet_completion_status: {record['packet_completion_status']}",
                    "",
                ]
            )

    lines.extend(["## Rejected Review Records", ""])
    if not result["rejected_review_records"]:
        lines.extend(["- none", ""])
    else:
        for record in result["rejected_review_records"]:
            lines.extend(
                [
                    f"### {record['market_id']}",
                    f"- review_status: {record['review_status']}",
                    f"- review_outcome: {record['review_outcome']}",
                    f"- queue_group: {record['queue_group']}",
                    f"- packet_completion_status: {record['packet_completion_status']}",
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

    lines.extend(
        [
            "## Limitations",
            "",
        ]
    )
    for limitation in result["limitations"]:
        lines.append(f"- {limitation}")
    return "\n".join(lines).rstrip() + "\n"


def write_operator_review_record_artifacts(
    review_records_path=DEFAULT_REVIEW_RECORDS,
    operator_review_queue_path=DEFAULT_OPERATOR_REVIEW_QUEUE,
    merged_packets_path=DEFAULT_MERGED_PACKETS,
    json_output_path=DEFAULT_JSON_RESULT,
    markdown_output_path=DEFAULT_MARKDOWN_REPORT,
    expected_json_output_path=DEFAULT_EXPECTED_JSON_RESULT,
):
    json_output_path = _resolve_path(json_output_path)
    markdown_output_path = _resolve_path(markdown_output_path)
    expected_json_output_path = _resolve_path(expected_json_output_path)
    result = build_operator_review_record_result(
        review_records_path=review_records_path,
        operator_review_queue_path=operator_review_queue_path,
        merged_packets_path=merged_packets_path,
        json_output_path=json_output_path,
        markdown_output_path=markdown_output_path,
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
        "review_summary": result["review_summary"],
    }


def main(argv):
    args = _parse_args(argv)
    summary = write_operator_review_record_artifacts(
        review_records_path=args.review_records,
        operator_review_queue_path=args.operator_review_queue,
        merged_packets_path=args.merged_packets,
        json_output_path=args.json_output,
        markdown_output_path=args.markdown_output,
        expected_json_output_path=args.expected_json_output,
    )
    print(json.dumps(summary, indent=2, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
