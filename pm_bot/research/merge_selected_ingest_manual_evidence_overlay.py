import argparse
import copy
import importlib.util
import json
import sys
from pathlib import Path


TASK_ID = "PMBOT-INGEST-007-SELECTED-STUBS-MANUAL-EVIDENCE-OVERLAY-MERGE"
SCHEMA_VERSION = "selected_ingest_merged_manual_research_packets.v1"
REPORT_VERSION = "selected_ingest_manual_evidence_overlay_merge_report.v1"
ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PACKET_STUBS = ROOT / "pm_bot" / "research" / "selected_ingest_research_packet_stubs.v1.json"
DEFAULT_TEMPLATE = ROOT / "pm_bot" / "research" / "selected_ingest_manual_evidence_overlay_template.v1.json"
DEFAULT_OVERLAY = ROOT / "pm_bot" / "research" / "selected_ingest_manual_evidence_overlay_fixture.v1.json"
DEFAULT_OUTPUT = ROOT / "pm_bot" / "research" / "selected_ingest_merged_manual_research_packets.v1.json"
DEFAULT_EXPECTED_OUTPUT = ROOT / "pm_bot" / "research" / "expected_selected_ingest_merged_manual_research_packets.v1.json"
DEFAULT_REPORT = ROOT / "pm_bot" / "research" / "selected_ingest_manual_evidence_overlay_merge_report.v1.md"
VALIDATOR_PATH = ROOT / "pm_bot" / "research" / "validate_manual_research_packets.py"

SELECTED_MARKET_IDS = ("692258", "824952", "691547", "597964", "598936")

ALLOWED_OVERLAY_FIELDS = {
    "market_id",
    "completion_status",
    "official_sources_checked",
    "credible_news_sources_checked",
    "evidence_slots",
    "missing_information",
    "operator_notes",
}
EVIDENCE_ITEM_FIELDS = (
    "source_name",
    "source_type",
    "source_url_or_reference",
    "captured_claim",
    "relevance_to_resolution",
    "operator_notes",
)
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
    "yes_no_decisions",
    "buy",
    "sell",
    "market_decision",
    "market_decisions",
}
OVERLAY_METADATA_FIELDS = {
    "schema_version",
    "task_id",
    "deterministic",
    "overlay_format",
    "selected_market_ids",
    "required_evidence_fields",
    "blank_evidence_entry_template",
    "instructions",
    "notes",
}


class SelectedIngestOverlayError(ValueError):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code


def _parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Merge deterministic offline manual evidence overlays into selected live-ingest PMBOT research stubs."
    )
    parser.add_argument("--packet-stubs", default=str(DEFAULT_PACKET_STUBS.relative_to(ROOT)))
    parser.add_argument("--template", default=str(DEFAULT_TEMPLATE.relative_to(ROOT)))
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


def _write_json(path, payload):
    rendered = json.dumps(payload, indent=2, ensure_ascii=True) + "\n"
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(rendered, encoding="utf-8")
    return rendered


def _load_validator_contract():
    spec = importlib.util.spec_from_file_location("selected_ingest_manual_packet_validator", VALIDATOR_PATH)
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
                        "Trading, wallet, execution, recommendation, stake, size, price, scoring, probability, expected value, side, buy/sell, and market decision fields are prohibited.",
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

    required = set(required_evidence_fields)
    keys = set(item)
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


def _load_selected_packet_stubs(packet_stubs_path):
    payload = _load_json(packet_stubs_path)
    if payload.get("selected_market_ids") != list(SELECTED_MARKET_IDS):
        raise SelectedIngestOverlayError(
            "selected_market_ids_mismatch",
            "Selected packet stubs must contain exactly the PMBOT-INGEST-005 selected market IDs.",
        )
    packet_stubs = payload.get("packet_stubs")
    if not isinstance(packet_stubs, list):
        raise SelectedIngestOverlayError("packet_stubs_not_list", "Packet stubs payload must contain a packet_stubs list.")
    if [stub.get("market_id") for stub in packet_stubs] != list(SELECTED_MARKET_IDS):
        raise SelectedIngestOverlayError(
            "packet_stub_order_mismatch",
            "Packet stubs must remain in selected market ID order.",
        )
    return payload, packet_stubs


def _load_template_contract(template_path):
    payload = _load_json(template_path)
    if payload.get("selected_market_ids") != list(SELECTED_MARKET_IDS):
        raise SelectedIngestOverlayError(
            "template_selected_market_ids_mismatch",
            "Manual overlay template must contain exactly the selected market IDs.",
        )
    if tuple(payload.get("required_evidence_fields", ())) != EVIDENCE_ITEM_FIELDS:
        raise SelectedIngestOverlayError(
            "template_required_evidence_fields_mismatch",
            "Manual overlay template evidence fields do not match the selected-ingest contract.",
        )
    return payload


def _overlay_entries(overlay_payload):
    if isinstance(overlay_payload, list):
        return overlay_payload, None
    if not isinstance(overlay_payload, dict):
        return None, _error("overlay_payload_not_object_or_list", "overlay", "Overlay JSON must be an object or list.")

    for field in ("market_overlays", "overlays"):
        if field in overlay_payload:
            if not isinstance(overlay_payload[field], list):
                return None, _error("overlay_entries_not_list", field, f"{field} must be a list.")
            return overlay_payload[field], None

    entries = []
    keyed_entries = overlay_payload.get("manual_entries_by_market_id")
    if isinstance(keyed_entries, dict):
        for market_id, value in keyed_entries.items():
            if isinstance(value, dict):
                entry = copy.deepcopy(value)
                entry.setdefault("market_id", str(market_id))
                entries.append(entry)
            else:
                entries.append({"market_id": str(market_id), "__invalid_overlay_entry__": value})
        return entries, None

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


def _immutable_stub_fields(stubs_by_market_id):
    fields = set()
    for stub in stubs_by_market_id.values():
        fields.update(stub)
    return fields - ALLOWED_OVERLAY_FIELDS


def _validate_overlay(overlay, index, selected_market_ids, stubs_by_market_id, immutable_fields, validator_contract):
    market_id = _overlay_market_id(overlay, index)
    errors = []
    if not isinstance(overlay, dict):
        return market_id, [_error("overlay_not_object", f"overlays[{index}]", "Each overlay entry must be an object.")]

    errors.extend(_walk_prohibited_fields(overlay))

    if not _non_empty_text(overlay.get("market_id")):
        _append(errors, "missing_overlay_market_id", "market_id", "Overlay entry must include a non-empty market_id.")
    elif market_id not in selected_market_ids:
        _append(errors, "unknown_market_id", "market_id", "Overlay market_id is not one of the five selected live-ingest market IDs.")

    for field in sorted(set(overlay) - ALLOWED_OVERLAY_FIELDS):
        if field in immutable_fields:
            _append(errors, f"immutable_field_override:{field}", field, f"{field} is immutable and must remain sourced from the selected ingest stub.")
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

    if market_id in stubs_by_market_id and market_id not in selected_market_ids:
        _append(errors, "unselected_market_id", "market_id", "Overlay market_id is present in stubs but not selected for this merge.")

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
    for field in (
        "completion_status",
        "official_sources_checked",
        "credible_news_sources_checked",
        "missing_information",
        "operator_notes",
    ):
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


def _status_market_ids(packets, status):
    return sorted(packet["market_id"] for packet in packets if packet.get("completion_status") == status)


def build_merge_artifacts(
    packet_stubs_path=DEFAULT_PACKET_STUBS,
    template_path=DEFAULT_TEMPLATE,
    overlay_path=DEFAULT_OVERLAY,
    output_path=DEFAULT_OUTPUT,
):
    packet_stubs_path = _resolve_path(packet_stubs_path)
    template_path = _resolve_path(template_path)
    overlay_path = _resolve_path(overlay_path)
    output_path = _resolve_path(output_path)
    validator_contract = _load_validator_contract()
    stubs_payload, stubs = _load_selected_packet_stubs(packet_stubs_path)
    template_payload = _load_template_contract(template_path)
    overlay_payload = _load_json(overlay_path)
    entries, payload_error = _overlay_entries(overlay_payload)
    selected_market_ids = list(SELECTED_MARKET_IDS)
    stubs_by_market_id = {stub["market_id"]: stub for stub in stubs}
    immutable_fields = _immutable_stub_fields(stubs_by_market_id)
    base_packets = {
        market_id: _base_manual_packet(stubs_by_market_id[market_id], validator_contract["expected_evidence_slots"])
        for market_id in selected_market_ids
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
        market_id, errors = _validate_overlay(
            overlay,
            index,
            selected_market_ids,
            stubs_by_market_id,
            immutable_fields,
            validator_contract,
        )
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

    packets = [copy.deepcopy(accepted_overlays.get(market_id, base_packets[market_id])) for market_id in selected_market_ids]

    validation_errors_by_market_id = {}
    for packet in packets:
        validation_errors = validator_contract["module"].validate_packet(packet)
        if validation_errors:
            validation_errors_by_market_id[packet["market_id"]] = validation_errors

    accepted_market_ids = [market_id for market_id in selected_market_ids if market_id in accepted_overlays]
    rejected_market_ids = sorted(rejected_market_ids)
    ready_market_ids = _status_market_ids(packets, "ready_for_operator_review")
    needs_more_information_market_ids = _status_market_ids(packets, "needs_more_information")
    errors_by_market_id = {market_id: errors_by_market_id[market_id] for market_id in sorted(errors_by_market_id)}
    validation_errors_by_market_id = {
        market_id: validation_errors_by_market_id[market_id] for market_id in sorted(validation_errors_by_market_id)
    }
    summary = {
        "overlays_read": len(entries or []),
        "overlays_accepted": len(accepted_market_ids),
        "overlays_rejected": len(rejected_market_ids),
        "packets_written": len(packets),
        "ready_for_operator_review": len(ready_market_ids),
        "needs_more_information": len(needs_more_information_market_ids),
        "errors_by_market_id": errors_by_market_id,
    }

    merged_payload = {
        "schema_version": SCHEMA_VERSION,
        "task_id": TASK_ID,
        "deterministic": True,
        "source_packet_stubs_path": _display_path(packet_stubs_path),
        "source_packet_stubs_schema_version": stubs_payload.get("schema_version"),
        "source_overlay_template_path": _display_path(template_path),
        "source_overlay_template_schema_version": template_payload.get("schema_version"),
        "source_overlay_path": _display_path(overlay_path),
        "selected_market_ids": selected_market_ids,
        "accepted_overlay_market_ids": accepted_market_ids,
        "rejected_overlay_market_ids": rejected_market_ids,
        "ready_for_operator_review_market_ids": ready_market_ids,
        "needs_more_information_market_ids": needs_more_information_market_ids,
        "merge_summary": summary,
        "packets": packets,
        "merged_packets_validation_passed": not validation_errors_by_market_id,
        "merged_packet_validation_errors_by_market_id": validation_errors_by_market_id,
        "limitations": [
            "Reads only local selected-ingest research stubs and manual overlay JSON.",
            "Copies only operator-provided evidence structures into selected packet stubs.",
            "Rejected overlays are reported and are not applied.",
            "Does not fetch sources, infer truth, score markets, recommend actions, create dossiers, create paper orders, or wire runtime automation.",
        ],
    }
    report = {
        "schema_version": REPORT_VERSION,
        "task_id": TASK_ID,
        "deterministic": True,
        "source_packet_stubs_path": _display_path(packet_stubs_path),
        "source_overlay_template_path": _display_path(template_path),
        "source_overlay_path": _display_path(overlay_path),
        "output_path": _display_path(output_path),
        "selected_market_ids": selected_market_ids,
        "accepted_market_ids": accepted_market_ids,
        "rejected_market_ids": rejected_market_ids,
        "ready_for_operator_review_market_ids": ready_market_ids,
        "needs_more_information_market_ids": needs_more_information_market_ids,
        "summary": summary,
        "merged_packets_validation_passed": not validation_errors_by_market_id,
        "merged_packet_validation_errors_by_market_id": validation_errors_by_market_id,
    }
    return merged_payload, report


def render_markdown_report(report):
    summary = report["summary"]
    lines = [
        "# Selected Ingest Manual Evidence Overlay Merge Report v1",
        "",
        "## Summary",
        f"- overlays_read: {summary['overlays_read']}",
        f"- overlays_accepted: {summary['overlays_accepted']}",
        f"- overlays_rejected: {summary['overlays_rejected']}",
        f"- packets_written: {summary['packets_written']}",
        f"- ready_for_operator_review: {summary['ready_for_operator_review']}",
        f"- needs_more_information: {summary['needs_more_information']}",
        f"- merged_packets_validation_passed: {str(report['merged_packets_validation_passed']).lower()}",
        "",
        "## Source Artifacts",
        f"- packet_stubs: `{report['source_packet_stubs_path']}`",
        f"- overlay_template: `{report['source_overlay_template_path']}`",
        f"- overlay: `{report['source_overlay_path']}`",
        f"- output: `{report['output_path']}`",
        "",
        "## Selected Market IDs",
    ]
    lines.extend(f"- `{market_id}`" for market_id in report["selected_market_ids"])
    lines.extend(["", "## Accepted Overlays"])
    if report["accepted_market_ids"]:
        lines.extend(f"- `{market_id}`" for market_id in report["accepted_market_ids"])
    else:
        lines.append("- none")
    lines.extend(["", "## Rejected Overlays"])
    if report["rejected_market_ids"]:
        lines.extend(f"- `{market_id}`" for market_id in report["rejected_market_ids"])
    else:
        lines.append("- none")
    lines.extend(["", "## Status Counts"])
    lines.append(f"- ready_for_operator_review_market_ids: {', '.join(report['ready_for_operator_review_market_ids']) or 'none'}")
    lines.append(f"- needs_more_information_market_ids: {', '.join(report['needs_more_information_market_ids']) or 'none'}")
    lines.extend(["", "## Errors By Market ID"])
    if not summary["errors_by_market_id"]:
        lines.append("- none")
    else:
        for market_id, errors in summary["errors_by_market_id"].items():
            lines.append(f"### `{market_id}`")
            for error in errors:
                lines.append(f"- {error['code']} at `{error['path']}`: {error['message']}")
    lines.extend(
        [
            "",
            "## Safety Boundary",
            "- offline_only: true",
            "- live_fetchers: false",
            "- network_api_calls: false",
            "- credentials: false",
            "- wallet_private_keys: false",
            "- authenticated_endpoints: false",
            "- trading_endpoints: false",
            "- real_orders: false",
            "- live_trading: false",
            "- paper_orders: false",
            "- betting_recommendations: false",
            "- truth_inference: false",
            "- market_scoring: false",
            "- probability_estimates: false",
            "- expected_value_calculations: false",
            "- side_recommendations: false",
            "- market_decisions: false",
            "- runtime_wiring: false",
            "- dispatcher_run_codex_touched: false",
            "- prompt_automation: false",
            "- codex_copy_roots: false",
            "- completed_dossiers: false",
            "",
        ]
    )
    return "\n".join(lines)


def write_merge_artifacts(
    packet_stubs_path=DEFAULT_PACKET_STUBS,
    template_path=DEFAULT_TEMPLATE,
    overlay_path=DEFAULT_OVERLAY,
    output_path=DEFAULT_OUTPUT,
    expected_output_path=DEFAULT_EXPECTED_OUTPUT,
    report_output_path=DEFAULT_REPORT,
):
    output_path = _resolve_path(output_path)
    expected_output_path = _resolve_path(expected_output_path)
    report_output_path = _resolve_path(report_output_path)
    merged_payload, report = build_merge_artifacts(packet_stubs_path, template_path, overlay_path, output_path)
    rendered_packets = _write_json(output_path, merged_payload)
    rendered_expected = _write_json(expected_output_path, merged_payload)
    markdown = render_markdown_report(report)
    report_output_path.parent.mkdir(parents=True, exist_ok=True)
    report_output_path.write_text(markdown, encoding="utf-8")
    return {
        "task_id": TASK_ID,
        "overlays_read": report["summary"]["overlays_read"],
        "overlays_accepted": report["summary"]["overlays_accepted"],
        "overlays_rejected": report["summary"]["overlays_rejected"],
        "packets_written": report["summary"]["packets_written"],
        "ready_for_operator_review": report["summary"]["ready_for_operator_review"],
        "needs_more_information": report["summary"]["needs_more_information"],
        "output_path": _display_path(output_path),
        "expected_output_path": _display_path(expected_output_path),
        "report_output_path": _display_path(report_output_path),
        "merged_packets_validation_passed": report["merged_packets_validation_passed"],
        "output_json_matches_expected": rendered_packets == rendered_expected,
    }


def main(argv):
    args = _parse_args(argv)
    summary = write_merge_artifacts(
        packet_stubs_path=args.packet_stubs,
        template_path=args.template,
        overlay_path=args.overlay,
        output_path=args.output,
        expected_output_path=args.expected_output,
        report_output_path=args.report_output,
    )
    print(json.dumps(summary, indent=2, ensure_ascii=True))
    return 0 if summary["merged_packets_validation_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
