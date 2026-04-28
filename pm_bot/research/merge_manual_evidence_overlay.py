import argparse
import copy
import importlib.util
import json
import sys
from pathlib import Path


TASK_ID = "PMBOT-RESEARCH-009-MANUAL-EVIDENCE-OVERLAY-MERGE"
SCHEMA_VERSION = "merged_manual_research_packets.v1"
REPORT_SCHEMA_VERSION = "manual_evidence_overlay_merge_report.v1"
ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PACKET_STUBS = ROOT / "pm_bot" / "research" / "expected_research_packet_stubs.v1.json"
DEFAULT_WORKPACK_INDEX = ROOT / "pm_bot" / "research" / "operator_research_workpack_index.v1.json"
DEFAULT_OVERLAY = ROOT / "pm_bot" / "research" / "manual_evidence_overlay_fixture.v1.json"
DEFAULT_OUTPUT = ROOT / "pm_bot" / "research" / "merged_manual_research_packets.v1.json"
DEFAULT_EXPECTED_OUTPUT = ROOT / "pm_bot" / "research" / "expected_merged_manual_research_packets.v1.json"
DEFAULT_REPORT = ROOT / "pm_bot" / "research" / "expected_manual_evidence_overlay_merge_report.v1.json"
VALIDATOR_PATH = ROOT / "pm_bot" / "research" / "validate_manual_research_packets.py"


IMMUTABLE_STUB_FIELDS = {
    "shortlist_rank",
    "market_id",
    "title",
    "question",
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
}
ALLOWED_OVERLAY_FIELDS = {
    "market_id",
    "completion_status",
    "official_sources_checked",
    "credible_news_sources_checked",
    "evidence_slots",
    "missing_information",
    "operator_notes",
}
PROHIBITED_FIELD_TOKENS = {
    "order",
    "orders",
    "trade",
    "trades",
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
    "betting_recommendation",
    "betting_recommendations",
    "stake",
    "stakes",
    "size",
    "sizes",
    "price_target",
    "price_targets",
    "score",
    "scores",
    "signal",
    "signals",
}
OVERLAY_METADATA_FIELDS = {
    "schema_version",
    "task_id",
    "deterministic",
    "overlay_format",
    "instructions",
    "notes",
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
    "truth_inference": False,
    "market_scoring": False,
}


def _parse_args(argv):
    parser = argparse.ArgumentParser(description="Merge local manual evidence overlays into PMBOT research packet stubs.")
    parser.add_argument("--packet-stubs", default=str(DEFAULT_PACKET_STUBS.relative_to(ROOT)))
    parser.add_argument("--workpack-index", default=str(DEFAULT_WORKPACK_INDEX.relative_to(ROOT)))
    parser.add_argument("--overlay", default=str(DEFAULT_OVERLAY.relative_to(ROOT)))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT.relative_to(ROOT)))
    parser.add_argument("--expected-output", default=str(DEFAULT_EXPECTED_OUTPUT.relative_to(ROOT)))
    parser.add_argument("--report-output", default=str(DEFAULT_REPORT.relative_to(ROOT)))
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
        "module": module,
        "schema_version": module.SCHEMA_VERSION,
        "allowed_completion_statuses": set(module.ALLOWED_COMPLETION_STATUSES),
        "expected_evidence_slots": tuple(module.EXPECTED_EVIDENCE_SLOTS),
        "required_evidence_fields": tuple(module.REQUIRED_EVIDENCE_FIELDS),
    }


def _non_empty_text(value):
    return isinstance(value, str) and bool(value.strip())


def _clean_text(value):
    if value is None:
        return ""
    return str(value).strip()


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
                        f"prohibited_overlay_field:{key_text}",
                        path,
                        "Trading, wallet, execution, recommendation, stake, target, scoring, and signal fields are prohibited in manual evidence overlays.",
                    )
                )
            findings.extend(_walk_prohibited_fields(nested, path))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            findings.extend(_walk_prohibited_fields(item, f"{prefix}[{index}]"))
    return findings


def _validate_string_list(value, path, errors, required_non_empty_items=True):
    if not isinstance(value, list):
        _append(errors, "overlay_field_not_list", path, f"{path} must be a list.")
        return
    seen = set()
    for index, item in enumerate(value):
        item_path = f"{path}[{index}]"
        if not isinstance(item, str):
            _append(errors, "overlay_list_item_not_string", item_path, f"{item_path} must be a string.")
            continue
        normalized = item.strip()
        if required_non_empty_items and not normalized:
            _append(errors, "overlay_list_item_empty", item_path, f"{item_path} must be a non-empty string.")
            continue
        if normalized in seen:
            _append(errors, "overlay_list_item_duplicate", item_path, f"{item_path} duplicates an earlier item.")
        seen.add(normalized)


def _validate_evidence_item(item, slot_name, index, required_evidence_fields, errors):
    path = f"evidence_slots.{slot_name}[{index}]"
    if not isinstance(item, dict):
        _append(errors, "overlay_evidence_item_not_object", path, f"{path} must be an object.")
        return

    keys = set(item)
    required = set(required_evidence_fields)
    for field in required_evidence_fields:
        field_path = f"{path}.{field}"
        if field not in item:
            _append(errors, f"missing_overlay_evidence_field:{slot_name}:{index}:{field}", field_path, f"{field_path} is required.")
        elif not _non_empty_text(item[field]):
            _append(errors, f"empty_overlay_evidence_field:{slot_name}:{index}:{field}", field_path, f"{field_path} must be a non-empty string.")

    for field in sorted(keys - required):
        _append(errors, f"unexpected_overlay_evidence_field:{slot_name}:{index}:{field}", f"{path}.{field}", f"{path}.{field} is not part of the evidence item contract.")


def _validate_evidence_slots(value, expected_evidence_slots, required_evidence_fields, errors):
    if not isinstance(value, dict):
        _append(errors, "overlay_evidence_slots_not_object", "evidence_slots", "evidence_slots must be an object.")
        return

    expected = set(expected_evidence_slots)
    for slot_name, slot_value in value.items():
        path = f"evidence_slots.{slot_name}"
        if slot_name not in expected:
            _append(errors, f"unexpected_overlay_evidence_slot:{slot_name}", path, f"{path} is not part of the validator evidence slot contract.")
            continue
        if not isinstance(slot_value, list):
            _append(errors, f"overlay_evidence_slot_not_list:{slot_name}", path, f"{path} must be a list.")
            continue
        for index, item in enumerate(slot_value):
            _validate_evidence_item(item, slot_name, index, required_evidence_fields, errors)


def _packet_sort_key(packet):
    rank = packet.get("shortlist_rank")
    rank_key = rank if isinstance(rank, int) else 10**9
    return (rank_key, _clean_text(packet.get("market_id")), _clean_text(packet.get("title") or packet.get("question")))


def _load_packet_stubs(packet_stubs_path):
    payload = _load_json(packet_stubs_path)
    packet_stubs = payload.get("packet_stubs")
    if not isinstance(packet_stubs, list):
        raise ValueError("packet stubs payload must contain a packet_stubs list")
    ordered = sorted(packet_stubs, key=_packet_sort_key)
    return payload, ordered


def _load_workpack_index(workpack_index_path):
    payload = _load_json(workpack_index_path)
    market_ids = payload.get("market_ids")
    if not isinstance(market_ids, list):
        market_ids = []
    return payload, [_clean_text(market_id) for market_id in market_ids]


def _overlay_entries(overlay_payload):
    if isinstance(overlay_payload, list):
        return overlay_payload, None
    if not isinstance(overlay_payload, dict):
        return None, _error("overlay_payload_not_object_or_list", "overlay", "Overlay JSON must be an object or a list.")

    for field in ("market_overlays", "overlays"):
        if field in overlay_payload:
            if not isinstance(overlay_payload[field], list):
                return None, _error("overlay_entries_not_list", field, f"{field} must be a list.")
            return overlay_payload[field], None

    entries = []
    for market_id, value in overlay_payload.items():
        if market_id in OVERLAY_METADATA_FIELDS:
            continue
        if isinstance(value, dict):
            entry = copy.deepcopy(value)
            entry.setdefault("market_id", str(market_id))
            entries.append(entry)
        else:
            entries.append({"market_id": str(market_id), "__invalid_overlay_entry__": value})
    return entries, None


def _overlay_market_id(overlay, index):
    if isinstance(overlay, dict) and _non_empty_text(overlay.get("market_id")):
        return overlay["market_id"].strip()
    return f"overlay_index_{index}"


def _validate_overlay(overlay, index, stubs_by_market_id, validator_contract):
    errors = []
    market_id = _overlay_market_id(overlay, index)
    if not isinstance(overlay, dict):
        return market_id, [_error("overlay_not_object", f"overlays[{index}]", "Each overlay entry must be an object.")]

    errors.extend(_walk_prohibited_fields(overlay))

    if not _non_empty_text(overlay.get("market_id")):
        _append(errors, "missing_overlay_market_id", "market_id", "Overlay entry must include a non-empty market_id.")
    elif market_id not in stubs_by_market_id:
        _append(errors, "unknown_market_id", "market_id", "Overlay market_id is not present in the source packet stubs.")

    for field in sorted(set(overlay) - ALLOWED_OVERLAY_FIELDS):
        if field in IMMUTABLE_STUB_FIELDS:
            _append(errors, f"immutable_field_override:{field}", field, f"{field} is immutable and must remain sourced from the packet stub.")
        else:
            _append(errors, f"unexpected_overlay_field:{field}", field, f"{field} is not an allowed manual evidence overlay field.")

    status = overlay.get("completion_status")
    if "completion_status" in overlay and status not in validator_contract["allowed_completion_statuses"]:
        _append(errors, "invalid_completion_status", "completion_status", "completion_status is not in the validator's allowed status set.")

    for field in ("official_sources_checked", "credible_news_sources_checked", "missing_information"):
        if field in overlay:
            _validate_string_list(overlay[field], field, errors, required_non_empty_items=True)

    if "operator_notes" in overlay and not isinstance(overlay["operator_notes"], str):
        _append(errors, "operator_notes_not_string", "operator_notes", "operator_notes must be a string.")

    if "evidence_slots" in overlay:
        _validate_evidence_slots(
            overlay["evidence_slots"],
            validator_contract["expected_evidence_slots"],
            validator_contract["required_evidence_fields"],
            errors,
        )

    errors.sort(key=lambda item: (item["path"], item["code"], item["message"]))
    return market_id, errors


def _base_manual_packet(stub, expected_evidence_slots):
    packet = copy.deepcopy(stub)
    evidence_slots = copy.deepcopy(packet.get("evidence_slots") or {})
    for slot in expected_evidence_slots:
        evidence_slots.setdefault(slot, [])
    packet["evidence_slots"] = {slot: evidence_slots[slot] for slot in expected_evidence_slots}
    packet.setdefault("missing_information", [])
    packet.setdefault("completion_status", "stub_only")
    packet["official_sources_checked"] = []
    packet["credible_news_sources_checked"] = []
    packet["operator_notes"] = ""
    return packet


def _apply_overlay(packet, overlay, expected_evidence_slots):
    merged = copy.deepcopy(packet)
    for field in ("completion_status", "official_sources_checked", "credible_news_sources_checked", "missing_information", "operator_notes"):
        if field in overlay:
            merged[field] = copy.deepcopy(overlay[field])
    if "evidence_slots" in overlay:
        for slot in expected_evidence_slots:
            if slot in overlay["evidence_slots"]:
                merged["evidence_slots"][slot] = copy.deepcopy(overlay["evidence_slots"][slot])
    return merged


def _add_errors(errors_by_market_id, market_id, errors):
    if errors:
        errors_by_market_id.setdefault(market_id, []).extend(errors)


def build_merge_artifacts(packet_stubs_path=DEFAULT_PACKET_STUBS, workpack_index_path=DEFAULT_WORKPACK_INDEX, overlay_path=DEFAULT_OVERLAY, output_path=DEFAULT_OUTPUT):
    packet_stubs_path = _resolve_path(packet_stubs_path)
    workpack_index_path = _resolve_path(workpack_index_path)
    overlay_path = _resolve_path(overlay_path)
    output_path = _resolve_path(output_path)
    validator_contract = _load_validator_contract()
    stubs_payload, stubs = _load_packet_stubs(packet_stubs_path)
    workpack_index, workpack_market_ids = _load_workpack_index(workpack_index_path)
    overlay_payload = _load_json(overlay_path)
    entries, payload_error = _overlay_entries(overlay_payload)
    stubs_by_market_id = {stub["market_id"]: stub for stub in stubs if _non_empty_text(stub.get("market_id"))}
    stub_market_ids = [stub["market_id"] for stub in stubs]
    base_packets = {
        market_id: _base_manual_packet(stub, validator_contract["expected_evidence_slots"])
        for market_id, stub in stubs_by_market_id.items()
    }
    accepted_overlays = {}
    rejected_market_ids = []
    errors_by_market_id = {}
    seen_overlay_market_ids = set()

    if payload_error is not None:
        entries = []
        rejected_market_ids.append("payload")
        _add_errors(errors_by_market_id, "payload", [payload_error])

    for index, overlay in enumerate(entries or []):
        market_id, errors = _validate_overlay(overlay, index, stubs_by_market_id, validator_contract)
        if market_id in seen_overlay_market_ids:
            errors.append(_error("duplicate_overlay_market_id", "market_id", "Only one overlay entry per market_id is allowed."))
            errors.sort(key=lambda item: (item["path"], item["code"], item["message"]))
        seen_overlay_market_ids.add(market_id)

        if errors:
            rejected_market_ids.append(market_id)
            _add_errors(errors_by_market_id, market_id, errors)
            continue

        candidate_packet = _apply_overlay(base_packets[market_id], overlay, validator_contract["expected_evidence_slots"])
        validation_errors = validator_contract["module"].validate_packet(candidate_packet)
        if validation_errors:
            rejected_market_ids.append(market_id)
            _add_errors(
                errors_by_market_id,
                market_id,
                [
                    _error(
                        "merged_packet_failed_validator",
                        "packet",
                        "Merged packet failed the existing manual research packet validator.",
                    )
                ]
                + validation_errors,
            )
            continue

        accepted_overlays[market_id] = candidate_packet

    packets = []
    for market_id in stub_market_ids:
        packets.append(copy.deepcopy(accepted_overlays.get(market_id, base_packets[market_id])))

    validation_errors_by_market_id = {}
    ready_market_ids = []
    needs_more_information_market_ids = []
    for packet in packets:
        market_id = packet["market_id"]
        validation_errors = validator_contract["module"].validate_packet(packet)
        if validation_errors:
            validation_errors_by_market_id[market_id] = validation_errors
        if packet.get("completion_status") == "ready_for_operator_review":
            ready_market_ids.append(market_id)
        if packet.get("completion_status") == "needs_more_information":
            needs_more_information_market_ids.append(market_id)

    accepted_market_ids = [market_id for market_id in stub_market_ids if market_id in accepted_overlays]
    rejected_market_ids = sorted(rejected_market_ids)
    errors_by_market_id = {market_id: errors_by_market_id[market_id] for market_id in sorted(errors_by_market_id)}
    validation_errors_by_market_id = {
        market_id: validation_errors_by_market_id[market_id] for market_id in sorted(validation_errors_by_market_id)
    }

    merged_payload = {
        "schema_version": SCHEMA_VERSION,
        "task_id": TASK_ID,
        "deterministic": True,
        "source_packet_stubs_path": _display_path(packet_stubs_path),
        "source_packet_stubs_schema_version": stubs_payload.get("schema_version"),
        "source_workpack_index_path": _display_path(workpack_index_path),
        "source_workpack_index_schema_version": workpack_index.get("schema_version"),
        "source_overlay_path": _display_path(overlay_path),
        "validator_contract_path": _display_path(VALIDATOR_PATH),
        "validator_contract_schema_version": validator_contract["schema_version"],
        "packet_count": len(packets),
        "accepted_overlay_market_ids": accepted_market_ids,
        "rejected_overlay_market_ids": rejected_market_ids,
        "packets": packets,
        "safety_flags": SAFETY_FLAGS,
        "limitations": [
            "Reads only local JSON artifacts.",
            "Applies only operator-provided evidence and status overlay fields.",
            "Rejected overlays are reported and are not applied to normalized packet output.",
            "Does not infer truth, score markets, recommend bets, create paper orders, create real orders, or touch runtime wiring.",
        ],
    }
    report = {
        "schema_version": REPORT_SCHEMA_VERSION,
        "artifact_type": "manual_evidence_overlay_merge_report",
        "task_id": TASK_ID,
        "deterministic": True,
        "source_packet_stubs_path": _display_path(packet_stubs_path),
        "source_workpack_index_path": _display_path(workpack_index_path),
        "source_overlay_path": _display_path(overlay_path),
        "output_path": _display_path(output_path),
        "validator_contract_path": _display_path(VALIDATOR_PATH),
        "overlays_read": len(entries or []),
        "overlays_accepted": len(accepted_market_ids),
        "overlays_rejected": len(rejected_market_ids),
        "packets_written": len(packets),
        "ready_for_operator_review": len(ready_market_ids),
        "needs_more_information": len(needs_more_information_market_ids),
        "accepted_market_ids": accepted_market_ids,
        "rejected_market_ids": rejected_market_ids,
        "ready_for_operator_review_market_ids": sorted(ready_market_ids),
        "needs_more_information_market_ids": sorted(needs_more_information_market_ids),
        "errors_by_market_id": errors_by_market_id,
        "merged_packet_validation_errors_by_market_id": validation_errors_by_market_id,
        "merged_packets_validation_passed": not validation_errors_by_market_id,
        "workpack_index_market_ids_match_stubs": workpack_market_ids == stub_market_ids,
        "safety_flags": SAFETY_FLAGS,
    }
    return merged_payload, report


def write_merge_artifacts(
    packet_stubs_path=DEFAULT_PACKET_STUBS,
    workpack_index_path=DEFAULT_WORKPACK_INDEX,
    overlay_path=DEFAULT_OVERLAY,
    output_path=DEFAULT_OUTPUT,
    expected_output_path=DEFAULT_EXPECTED_OUTPUT,
    report_output_path=DEFAULT_REPORT,
):
    output_path = _resolve_path(output_path)
    expected_output_path = _resolve_path(expected_output_path)
    report_output_path = _resolve_path(report_output_path)
    merged_payload, report = build_merge_artifacts(packet_stubs_path, workpack_index_path, overlay_path, output_path)
    rendered_packets = json.dumps(merged_payload, indent=2, ensure_ascii=True) + "\n"
    rendered_report = json.dumps(report, indent=2, ensure_ascii=True) + "\n"

    output_path.parent.mkdir(parents=True, exist_ok=True)
    expected_output_path.parent.mkdir(parents=True, exist_ok=True)
    report_output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(rendered_packets, encoding="utf-8")
    expected_output_path.write_text(rendered_packets, encoding="utf-8")
    report_output_path.write_text(rendered_report, encoding="utf-8")
    return {
        "task_id": TASK_ID,
        "packets_written": report["packets_written"],
        "overlays_read": report["overlays_read"],
        "overlays_accepted": report["overlays_accepted"],
        "overlays_rejected": report["overlays_rejected"],
        "ready_for_operator_review": report["ready_for_operator_review"],
        "needs_more_information": report["needs_more_information"],
        "output_path": _display_path(output_path),
        "expected_output_path": _display_path(expected_output_path),
        "report_output_path": _display_path(report_output_path),
        "merged_packets_validation_passed": report["merged_packets_validation_passed"],
    }


def main(argv):
    args = _parse_args(argv)
    summary = write_merge_artifacts(
        packet_stubs_path=args.packet_stubs,
        workpack_index_path=args.workpack_index,
        overlay_path=args.overlay,
        output_path=args.output,
        expected_output_path=args.expected_output,
        report_output_path=args.report_output,
    )
    print(json.dumps(summary, indent=2, ensure_ascii=True))
    return 0 if summary["merged_packets_validation_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
