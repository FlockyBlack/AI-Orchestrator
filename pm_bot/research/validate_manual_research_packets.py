import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PACKET_FILE = ROOT / "pm_bot" / "research" / "manual_research_packets_fixture.v1.json"
SCHEMA_VERSION = "manual_research_packet_validation.v1"
ALLOWED_COMPLETION_STATUSES = {
    "stub_only",
    "manual_evidence_added",
    "ready_for_operator_review",
    "needs_more_information",
}
EXPECTED_EVIDENCE_SLOTS = (
    "official_resolution_criteria",
    "official_yes_evidence",
    "official_no_evidence",
    "credible_news_yes_evidence",
    "credible_news_no_evidence",
    "uncertainty_factors",
    "source_reliability_notes",
)
REQUIRED_EVIDENCE_FIELDS = (
    "source_name",
    "source_type",
    "source_url_or_reference",
    "captured_claim",
    "relevance_to_resolution",
    "operator_notes",
)
FORBIDDEN_FIELD_TOKENS = {
    "order",
    "orders",
    "trade",
    "trades",
    "wallet",
    "wallets",
    "execution",
    "executions",
    "private_key",
    "private_keys",
    "api_key",
    "api_keys",
    "credentials",
}
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
}


def _parse_args(argv):
    parser = argparse.ArgumentParser(description="Validate local manually completed PMBOT research packets.")
    parser.add_argument("--packets", default=str(DEFAULT_PACKET_FILE.relative_to(ROOT)))
    parser.add_argument("--write-report")
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


def _walk_forbidden_fields(value, prefix=""):
    findings = []
    if isinstance(value, dict):
        for key, nested in value.items():
            key_text = str(key)
            path = f"{prefix}.{key_text}" if prefix else key_text
            if _field_tokens(key_text) & FORBIDDEN_FIELD_TOKENS:
                findings.append(_error(f"forbidden_field:{key_text}", path, "Order, trade, wallet, credential, and execution fields are not allowed."))
            findings.extend(_walk_forbidden_fields(nested, path))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            findings.extend(_walk_forbidden_fields(item, f"{prefix}[{index}]"))
    return findings


def _validate_string_list(packet, field, errors, required_non_empty=True):
    value = packet.get(field)
    if not isinstance(value, list):
        _append(errors, f"{field}_not_list", field, f"{field} must be a list.")
        return []
    if required_non_empty and not value:
        _append(errors, f"{field}_empty", field, f"{field} must contain at least one item.")
    seen = set()
    for index, item in enumerate(value):
        path = f"{field}[{index}]"
        if not _non_empty_text(item):
            _append(errors, f"{field}_invalid_item:{index}", path, f"{path} must be a non-empty string.")
            continue
        normalized = item.strip()
        if normalized in seen:
            _append(errors, f"{field}_duplicate_item:{index}", path, f"{path} duplicates an earlier item.")
        seen.add(normalized)
    return value


def _validate_evidence_item(item, slot_name, index, errors):
    path = f"evidence_slots.{slot_name}[{index}]"
    if not isinstance(item, dict):
        _append(errors, "evidence_item_not_object", path, f"{path} must be an object.")
        return

    keys = set(item)
    required = set(REQUIRED_EVIDENCE_FIELDS)
    for field in REQUIRED_EVIDENCE_FIELDS:
        field_path = f"{path}.{field}"
        if field not in item:
            _append(errors, f"missing_evidence_field:{slot_name}:{index}:{field}", field_path, f"{field_path} is required.")
        elif not _non_empty_text(item[field]):
            _append(errors, f"empty_evidence_field:{slot_name}:{index}:{field}", field_path, f"{field_path} must be a non-empty string.")

    for field in sorted(keys - required):
        _append(errors, f"unexpected_evidence_field:{slot_name}:{index}:{field}", f"{path}.{field}", f"{path}.{field} is not part of the manual evidence item contract.")


def _validate_evidence_slots(packet, errors):
    evidence_slots = packet.get("evidence_slots")
    if not isinstance(evidence_slots, dict):
        _append(errors, "evidence_slots_not_object", "evidence_slots", "evidence_slots must be an object.")
        return {slot: [] for slot in EXPECTED_EVIDENCE_SLOTS}

    slot_values = {}
    for slot in EXPECTED_EVIDENCE_SLOTS:
        path = f"evidence_slots.{slot}"
        if slot not in evidence_slots:
            _append(errors, f"missing_evidence_slot:{slot}", path, f"{path} is required.")
            slot_values[slot] = []
            continue
        value = evidence_slots[slot]
        if not isinstance(value, list):
            _append(errors, f"evidence_slot_not_list:{slot}", path, f"{path} must be a list.")
            slot_values[slot] = []
            continue
        slot_values[slot] = value
        for index, item in enumerate(value):
            _validate_evidence_item(item, slot, index, errors)

    for slot in sorted(set(evidence_slots) - set(EXPECTED_EVIDENCE_SLOTS)):
        _append(errors, f"unexpected_evidence_slot:{slot}", f"evidence_slots.{slot}", f"evidence_slots.{slot} is not part of the manual packet contract.")

    return slot_values


def _filled_evidence_count(slot_values, slot_names):
    return sum(len(slot_values.get(slot, [])) for slot in slot_names)


def _validate_status_requirements(status, missing_information, slot_values, errors):
    total_evidence = _filled_evidence_count(slot_values, EXPECTED_EVIDENCE_SLOTS)

    if status == "stub_only":
        if total_evidence != 0:
            _append(errors, "stub_only_has_evidence", "completion_status", "stub_only packets must keep all evidence slots empty.")
        if not missing_information:
            _append(errors, "stub_only_missing_information_empty", "missing_information", "stub_only packets must preserve a deterministic missing_information checklist.")
        return

    if status == "manual_evidence_added" and total_evidence == 0:
        _append(errors, "manual_evidence_added_without_evidence", "evidence_slots", "manual_evidence_added packets must contain at least one manual evidence item.")

    if status == "needs_more_information" and not missing_information:
        _append(errors, "needs_more_information_missing_checklist_empty", "missing_information", "needs_more_information packets must list the remaining missing information.")

    if status != "ready_for_operator_review":
        return

    if missing_information:
        _append(errors, "ready_for_operator_review_has_missing_information", "missing_information", "ready_for_operator_review packets must have an empty missing_information list.")
    if _filled_evidence_count(slot_values, ("official_resolution_criteria",)) == 0:
        _append(errors, "ready_for_operator_review_insufficient_evidence:official_resolution_criteria", "evidence_slots.official_resolution_criteria", "ready_for_operator_review requires at least one official resolution criteria evidence item.")
    if _filled_evidence_count(slot_values, ("official_yes_evidence", "official_no_evidence")) == 0:
        _append(errors, "ready_for_operator_review_insufficient_evidence:official_evidence", "evidence_slots", "ready_for_operator_review requires at least one official yes/no evidence item.")
    if _filled_evidence_count(slot_values, ("credible_news_yes_evidence", "credible_news_no_evidence")) == 0:
        _append(errors, "ready_for_operator_review_insufficient_evidence:credible_news", "evidence_slots", "ready_for_operator_review requires at least one credible news evidence item.")
    if _filled_evidence_count(slot_values, ("source_reliability_notes",)) == 0:
        _append(errors, "ready_for_operator_review_insufficient_evidence:source_reliability_notes", "evidence_slots.source_reliability_notes", "ready_for_operator_review requires at least one source reliability note.")


def validate_packet(packet):
    errors = []
    if not isinstance(packet, dict):
        return [_error("packet_not_object", "packet", "Each packet must be an object.")]

    errors.extend(_walk_forbidden_fields(packet))

    if not _non_empty_text(packet.get("market_id")):
        _append(errors, "missing_market_id", "market_id", "market_id must be a non-empty string.")
    if not (_non_empty_text(packet.get("title")) or _non_empty_text(packet.get("question"))):
        _append(errors, "missing_title_or_question", "title", "At least one of title or question must be a non-empty string.")
    if not _non_empty_text(packet.get("packet_type")):
        _append(errors, "missing_packet_type", "packet_type", "packet_type must be a non-empty string.")

    status = packet.get("completion_status")
    if status not in ALLOWED_COMPLETION_STATUSES:
        _append(errors, "invalid_completion_status", "completion_status", "completion_status is not in the allowed status set.")

    _validate_string_list(packet, "official_sources_to_check", errors)
    _validate_string_list(packet, "credible_news_sources_to_check", errors)
    missing_information = _validate_string_list(packet, "missing_information", errors, required_non_empty=False)
    slot_values = _validate_evidence_slots(packet, errors)

    if status in ALLOWED_COMPLETION_STATUSES:
        _validate_status_requirements(status, missing_information, slot_values, errors)

    errors.sort(key=lambda item: (item["path"], item["code"], item["message"]))
    return errors


def _packets_from_payload(payload):
    if isinstance(payload, dict) and isinstance(payload.get("packets"), list):
        return payload["packets"]
    if isinstance(payload, dict) and isinstance(payload.get("packet_stubs"), list):
        return payload["packet_stubs"]
    if isinstance(payload, list):
        return payload
    return None


def _market_key(packet, index):
    if isinstance(packet, dict) and _non_empty_text(packet.get("market_id")):
        return packet["market_id"].strip()
    return f"packet_index_{index}"


def build_validation_report(packet_file=DEFAULT_PACKET_FILE):
    packet_file = _resolve_path(packet_file)
    payload = _load_json(packet_file)
    packets = _packets_from_payload(payload)
    if packets is None:
        errors_by_market_id = {
            "payload": [
                _error("packets_not_list", "packets", "Input JSON must be a list, contain packets, or contain packet_stubs.")
            ]
        }
        return {
            "schema_version": SCHEMA_VERSION,
            "artifact_type": "manual_research_packet_validation_report",
            "deterministic": True,
            "source_path": _display_path(packet_file),
            "total_packets_checked": 0,
            "valid_packets": 0,
            "invalid_packets": 1,
            "ready_for_operator_review": 0,
            "needs_more_information": 0,
            "valid_market_ids": [],
            "invalid_market_ids": ["payload"],
            "ready_for_operator_review_market_ids": [],
            "needs_more_information_market_ids": [],
            "validation_errors_by_market_id": errors_by_market_id,
            "validation_passed": False,
            "safety_flags": SAFETY_FLAGS,
        }

    valid_market_ids = []
    invalid_market_ids = []
    ready_market_ids = []
    needs_more_information_market_ids = []
    errors_by_market_id = {}

    for index, packet in enumerate(packets):
        market_id = _market_key(packet, index)
        errors = validate_packet(packet)
        if errors:
            invalid_market_ids.append(market_id)
            errors_by_market_id[market_id] = errors
            continue

        valid_market_ids.append(market_id)
        status = packet["completion_status"]
        if status == "ready_for_operator_review":
            ready_market_ids.append(market_id)
        if status == "needs_more_information":
            needs_more_information_market_ids.append(market_id)

    invalid_market_ids.sort()
    valid_market_ids.sort()
    ready_market_ids.sort()
    needs_more_information_market_ids.sort()
    errors_by_market_id = {market_id: errors_by_market_id[market_id] for market_id in sorted(errors_by_market_id)}

    return {
        "schema_version": SCHEMA_VERSION,
        "artifact_type": "manual_research_packet_validation_report",
        "deterministic": True,
        "source_path": _display_path(packet_file),
        "total_packets_checked": len(packets),
        "valid_packets": len(valid_market_ids),
        "invalid_packets": len(invalid_market_ids),
        "ready_for_operator_review": len(ready_market_ids),
        "needs_more_information": len(needs_more_information_market_ids),
        "valid_market_ids": valid_market_ids,
        "invalid_market_ids": invalid_market_ids,
        "ready_for_operator_review_market_ids": ready_market_ids,
        "needs_more_information_market_ids": needs_more_information_market_ids,
        "validation_errors_by_market_id": errors_by_market_id,
        "validation_passed": not invalid_market_ids,
        "safety_flags": SAFETY_FLAGS,
    }


def main(argv):
    args = _parse_args(argv)
    report = build_validation_report(args.packets)
    rendered = json.dumps(report, indent=2, ensure_ascii=True) + "\n"
    if args.write_report:
        output_path = _resolve_path(args.write_report)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0 if report["validation_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
