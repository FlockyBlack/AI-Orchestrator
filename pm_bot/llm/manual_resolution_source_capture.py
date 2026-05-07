import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path


TASK_ID = "PMBOT-SOURCE-004-LOCAL-MANUAL-RESOLUTION-SOURCE-CAPTURE-PACKETS"
SCHEMA_VERSION = "manual_resolution_source_capture_schema.v1"
CONTRACT_VERSION = "manual_resolution_source_capture.v1"
MANIFEST_VERSION = "manual_resolution_source_capture_manifest.v1"
GENERATED_BY = "pm_bot/llm/manual_resolution_source_capture.py"
GENERATION_MARKER = "deterministic-source-004-local-manual-capture.v1"

ROOT = Path(__file__).resolve().parents[2]

CAPTURE_STATUS_VALUES = (
    "not_started",
    "draft",
    "ready_for_local_review",
    "reviewed",
    "needs_revision",
)

CAPTURE_FIELDS = (
    "market_id",
    "market_title_or_question",
    "category",
    "capture_status",
    "full_market_resolution_criteria_text",
    "full_resolution_rules",
    "official_source_references",
    "official_source_urls_or_rule_references",
    "source_timestamps",
    "source_reliability_review",
    "reviewed_local_evidence_references",
    "non_placeholder_evidence_notes",
    "jurisdiction",
    "candidate_or_party_if_applicable",
    "manual_operator_notes",
    "unresolved_source_questions",
    "source_capture_author_or_operator",
    "source_capture_timestamp_local",
    "source_capture_provenance",
    "no_market_action_guidance",
    "operator_review_only",
    "no_trading_authority",
    "no_queue_authority",
    "no_runtime_authority",
    "no_wallet_or_order_authority",
)

FIELDS_REQUIRED_FOR_HIGH_COMPLETENESS = (
    "full_market_resolution_criteria_text",
    "full_resolution_rules",
    "official_source_references",
    "official_source_urls_or_rule_references",
)

FIELDS_RECOMMENDED_BEFORE_OPENROUTER_REVIEW = (
    "source_reliability_review",
    "reviewed_local_evidence_references",
)

RECOMMENDED_OPERATOR_FILL_ORDER = (
    "full_market_resolution_criteria_text",
    "full_resolution_rules",
    "official_source_references",
    "official_source_urls_or_rule_references",
    "source_timestamps",
    "source_reliability_review",
    "reviewed_local_evidence_references",
    "non_placeholder_evidence_notes",
)

NO_AUTHORITY_FLAGS = {
    "no_market_action_guidance": True,
    "operator_review_only": True,
    "no_trading_authority": True,
    "no_queue_authority": True,
    "no_runtime_authority": True,
    "no_wallet_or_order_authority": True,
}

SAFETY_SUMMARY = {
    **NO_AUTHORITY_FLAGS,
    "local_only": True,
    "passive_context_only": True,
    "manual_review_only": True,
    "analysis_only": True,
    "no_dispatcher_authority": True,
    "no_browser_automation": True,
    "no_probability_ev_edge_confidence_side_selection": True,
    "openrouter_calls_performed": 0,
    "polymarket_api_calls_performed": 0,
    "external_network_calls_performed": 0,
    "network_calls_performed": 0,
    "api_key_accessed": False,
    "api_key_value_printed": False,
    "api_key_value_written": False,
    "api_key_leaked": False,
    "wallet_or_private_key_accessed": False,
    "orders_created": 0,
    "queue_items_created": 0,
    "queue_state_mutated": False,
    "runtime_wiring_added": False,
    "dispatcher_changed": False,
    "background_workers_added": False,
    "browser_automation_used": False,
    "market_decisions_made": False,
}

SOURCE_PATHS = {
    "source_003_result_json": "docs/PMBOT_SOURCE_003_RESULT.json",
    "inventory_json": "pm_bot/llm/current_llm_market_packet_inventory.v1.json",
    "source_003_audit_json": (
        "pm_bot/llm/current_llm_resolution_source_normalization_audit.v1.json"
    ),
    "readiness_scores_after_source_json": (
        "pm_bot/llm/"
        "current_llm_packet_evidence_readiness_scores_after_source_normalization.v1.json"
    ),
    "readiness_gate_after_source_json": (
        "pm_bot/llm/current_llm_batch_readiness_gate_after_source_normalization.v1.json"
    ),
    "schema_json": "pm_bot/llm/manual_resolution_source_capture_schema.v1.json",
    "schema_md": "pm_bot/llm/manual_resolution_source_capture_schema.v1.md",
    "capture_dir": "pm_bot/llm/manual_resolution_source_capture",
    "manifest_json": "pm_bot/llm/manual_resolution_source_capture_manifest.v1.json",
    "manifest_md": "pm_bot/llm/manual_resolution_source_capture_manifest.v1.md",
}


def _parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Export local manual PMBOT resolution/source capture templates."
    )
    parser.add_argument("--write", action="store_true", help="Write schema, packets, and manifest.")
    parser.add_argument("--markdown", action="store_true", help="Print manifest Markdown instead of JSON.")
    return parser.parse_args(argv)


def _resolve(path, root=ROOT):
    value = Path(path)
    return value if value.is_absolute() else Path(root) / value


def _display_path(path, root=ROOT):
    resolved = Path(path).resolve()
    try:
        value = resolved.relative_to(Path(root).resolve())
    except ValueError:
        value = resolved
    return str(value).replace("\\", "/")


def _load_json(path, root=ROOT):
    with _resolve(path, root=root).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _write_json(path, payload, root=ROOT):
    resolved = _resolve(path, root=root)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    resolved.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def _ascii(value):
    return str(value).encode("ascii", "backslashreplace").decode("ascii")


def _write_text(path, text, root=ROOT):
    resolved = _resolve(path, root=root)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    resolved.write_text(_ascii(text), encoding="utf-8")


def _safe_list(value):
    return value if isinstance(value, list) else []


def _safe_dict(value):
    return value if isinstance(value, dict) else {}


def _field_definition(name):
    type_by_field = {
        "market_id": "string",
        "market_title_or_question": "string_or_null",
        "category": "string_or_null",
        "capture_status": "enum",
        "full_market_resolution_criteria_text": "string",
        "full_resolution_rules": "string",
        "official_source_references": "array",
        "official_source_urls_or_rule_references": "array",
        "source_timestamps": "array",
        "source_reliability_review": "string",
        "reviewed_local_evidence_references": "array",
        "non_placeholder_evidence_notes": "string",
        "jurisdiction": "string_or_null",
        "candidate_or_party_if_applicable": "string_or_null",
        "manual_operator_notes": "string",
        "unresolved_source_questions": "array",
        "source_capture_author_or_operator": "string_or_null",
        "source_capture_timestamp_local": "string_or_null",
        "source_capture_provenance": "string",
    }
    return {
        "field": name,
        "type": type_by_field.get(name, "boolean"),
        "required_template_field": True,
        "required_for_high_completeness": name in FIELDS_REQUIRED_FOR_HIGH_COMPLETENESS,
        "recommended_before_openrouter_review": (
            name in FIELDS_RECOMMENDED_BEFORE_OPENROUTER_REVIEW
        ),
        "may_be_empty_in_not_started_template": name in RECOMMENDED_OPERATOR_FILL_ORDER,
        "empty_allowed_statuses": ["not_started", "draft"]
        if name in FIELDS_REQUIRED_FOR_HIGH_COMPLETENESS
        else CAPTURE_STATUS_VALUES,
    }


def build_capture_schema():
    return {
        "schema_version": SCHEMA_VERSION,
        "contract_version": CONTRACT_VERSION,
        "task_id": TASK_ID,
        "generated_by": GENERATED_BY,
        "generated_at_marker": GENERATION_MARKER,
        "status": "manual_resolution_source_capture_schema_created",
        "schema_scope": "local_manual_source_evidence_capture_only",
        "capture_status_values": list(CAPTURE_STATUS_VALUES),
        "field_order": list(CAPTURE_FIELDS),
        "field_definitions": {field: _field_definition(field) for field in CAPTURE_FIELDS},
        "fields_required_for_high_completeness": list(
            FIELDS_REQUIRED_FOR_HIGH_COMPLETENESS
        ),
        "fields_recommended_before_openrouter_review": list(
            FIELDS_RECOMMENDED_BEFORE_OPENROUTER_REVIEW
        ),
        "recommended_operator_fill_order": list(RECOMMENDED_OPERATOR_FILL_ORDER),
        "operator_safety_rules": [
            "Do not include trading recommendations.",
            "Do not include market predictions.",
            "Do not include probability, EV, edge, confidence, or side selection.",
            "Do not include buy/sell/hold/enter/exit language.",
            "Capture is for source/evidence completeness only.",
        ],
        **NO_AUTHORITY_FLAGS,
        "safety_summary": dict(SAFETY_SUMMARY),
    }


def render_capture_schema_markdown(schema):
    lines = [
        "# PMBOT Manual Resolution Source Capture Schema v1",
        "",
        f"- schema_version: {schema['schema_version']}",
        f"- contract_version: {schema['contract_version']}",
        f"- task_id: {schema['task_id']}",
        f"- status: {schema['status']}",
        f"- schema_scope: {schema['schema_scope']}",
        "",
        "## Safety Rules",
        "",
    ]
    for rule in schema["operator_safety_rules"]:
        lines.append(f"- {rule}")
    lines.extend(
        [
            "",
            "## Capture Status Values",
            "",
        ]
    )
    for status in schema["capture_status_values"]:
        lines.append(f"- {status}")
    lines.extend(["", "## Fields", ""])
    for field in schema["field_order"]:
        definition = schema["field_definitions"][field]
        lines.append(
            "- "
            f"{field}: type={definition['type']}, "
            f"required_template_field={str(definition['required_template_field']).lower()}, "
            "required_for_high_completeness="
            f"{str(definition['required_for_high_completeness']).lower()}, "
            "recommended_before_openrouter_review="
            f"{str(definition['recommended_before_openrouter_review']).lower()}"
        )
    lines.extend(["", "## Required For High Completeness", ""])
    for field in schema["fields_required_for_high_completeness"]:
        lines.append(f"- {field}")
    lines.extend(["", "## Recommended Before OpenRouter Review", ""])
    for field in schema["fields_recommended_before_openrouter_review"]:
        lines.append(f"- {field}")
    lines.extend(["", "## No Authority Flags", ""])
    for key in sorted(NO_AUTHORITY_FLAGS):
        lines.append(f"- {key}: {str(schema[key]).lower()}")
    lines.append("")
    return "\n".join(lines)


def _by_market(items):
    return {str(item.get("market_id")): item for item in items if item.get("market_id")}


def _review_status(inventory_record):
    if inventory_record.get("already_reviewed_by_openrouter") is True:
        if inventory_record.get("accepted_for_operator_review") is True:
            return "reviewed_accepted"
        return "reviewed_blocked"
    if inventory_record.get("already_reviewed_by_openrouter") is False:
        return "not_reviewed"
    return "unknown"


def _ordered_missing_fields(*field_lists):
    seen = set()
    ordered = []
    for field in RECOMMENDED_OPERATOR_FILL_ORDER:
        if any(field in fields for fields in field_lists):
            ordered.append(field)
            seen.add(field)
    for fields in field_lists:
        for field in fields:
            if field not in seen:
                ordered.append(field)
                seen.add(field)
    return ordered


def _capture_packet_path(market_id):
    return (
        f"{SOURCE_PATHS['capture_dir']}/"
        f"{market_id}_resolution_source_capture.v1.json"
    )


def _capture_markdown_path(market_id):
    return (
        f"{SOURCE_PATHS['capture_dir']}/"
        f"{market_id}_resolution_source_capture.v1.md"
    )


def build_capture_packet(inventory_record, audit_record, readiness_record):
    market_id = str(inventory_record["market_id"])
    audit_missing = _safe_list(audit_record.get("missing_resolution_source_fields"))
    readiness_missing = _safe_list(
        readiness_record.get("missing_or_weak_fields_after_source_normalization")
    )
    missing_fields = _ordered_missing_fields(audit_missing, readiness_missing)
    title = inventory_record.get("title_or_question") or audit_record.get("title_or_question")
    category = inventory_record.get("category") or audit_record.get("category")
    status = _review_status(inventory_record)
    readiness_band = readiness_record.get("updated_readiness_band") or "unknown"
    packet = {
        "contract_version": CONTRACT_VERSION,
        "schema_version": SCHEMA_VERSION,
        "task_id": TASK_ID,
        "generated_by": GENERATED_BY,
        "generated_at_marker": GENERATION_MARKER,
        "market_id": market_id,
        "category": category,
        "market_title_or_question": title,
        "current_openrouter_review_status": status,
        "current_readiness_band": readiness_band,
        "source_capture_status": "not_started",
        "capture_status": "not_started",
        "full_market_resolution_criteria_text": "",
        "full_resolution_rules": "",
        "official_source_references": [],
        "official_source_urls_or_rule_references": [],
        "source_timestamps": [],
        "source_reliability_review": "",
        "reviewed_local_evidence_references": [],
        "non_placeholder_evidence_notes": "",
        "jurisdiction": audit_record.get("jurisdiction"),
        "candidate_or_party_if_applicable": audit_record.get(
            "candidate_or_party_if_applicable"
        ),
        "manual_operator_notes": "",
        "unresolved_source_questions": [],
        "source_capture_author_or_operator": None,
        "source_capture_timestamp_local": None,
        "source_capture_provenance": "local_manual_operator_input_only_not_fetched_by_codex",
        **NO_AUTHORITY_FLAGS,
        "missing_fields_prefilled_from_source_003": missing_fields,
        "source_003_audit_reference": {
            "artifact_path": SOURCE_PATHS["source_003_audit_json"],
            "market_id": market_id,
            "packet_file_path": audit_record.get("packet_file_path"),
            "prompt_file_path": audit_record.get("prompt_file_path"),
            "missing_resolution_source_fields": audit_missing,
            "normalization_warnings": _safe_list(audit_record.get("normalization_warnings")),
            "safe_next_local_action": audit_record.get("safe_next_local_action"),
        },
        "packet_inventory_reference": {
            "artifact_path": SOURCE_PATHS["inventory_json"],
            "market_id": market_id,
            "packet_file_path": inventory_record.get("packet_file_path"),
            "prompt_file_path": inventory_record.get("prompt_file_path"),
            "warnings": _safe_list(inventory_record.get("warnings")),
        },
        "readiness_gate_reference": {
            "artifact_path": SOURCE_PATHS["readiness_gate_after_source_json"],
            "readiness_scores_path": SOURCE_PATHS["readiness_scores_after_source_json"],
            "market_id": market_id,
            "current_readiness_band": readiness_band,
            "suitable_for_future_openrouter_batch": readiness_record.get(
                "suitable_for_future_openrouter_batch"
            ),
        },
        "operator_instructions": [
            "Paste or summarize official resolution criteria if available locally.",
            "Add source/rule references only if manually verified.",
            "Add source timestamp.",
            "Add reliability note.",
            "Do not add predictions or trading guidance.",
        ],
        "safety_summary": dict(SAFETY_SUMMARY),
    }
    return packet


def render_capture_packet_markdown(packet):
    lines = [
        f"# Manual Resolution Source Capture - {packet['market_id']}",
        "",
        f"- contract_version: {packet['contract_version']}",
        f"- market_id: {packet['market_id']}",
        f"- market_title_or_question: {packet['market_title_or_question'] or 'TODO'}",
        f"- local_category: {packet['category'] or 'TODO'}",
        f"- current_openrouter_review_status: {packet['current_openrouter_review_status']}",
        f"- current_readiness_band: {packet['current_readiness_band']}",
        f"- source_capture_status: {packet['source_capture_status']}",
        "",
        "## Safety",
        "",
        "- This packet is for local source/evidence completeness only.",
        "- No trading, wallet, order, runtime, dispatcher, browser, or queue authority.",
        "- Do not add predictions, market guidance, side selection, or action language.",
        "",
        "## Fields To Fill",
        "",
    ]
    field_labels = [
        ("full_market_resolution_criteria_text", "TODO: paste or summarize local criteria"),
        ("full_resolution_rules", "TODO: paste or summarize local rules"),
        ("official_source_references", "TODO: add manually verified references"),
        (
            "official_source_urls_or_rule_references",
            "TODO: add manually verified URL or rule references",
        ),
        ("source_timestamps", "TODO: add timestamp for each source checked"),
        ("source_reliability_review", "TODO: add reliability note"),
        (
            "reviewed_local_evidence_references",
            "TODO: list local files or packet sections reviewed",
        ),
        ("non_placeholder_evidence_notes", "TODO: add non-placeholder evidence notes"),
        ("jurisdiction", packet.get("jurisdiction") or "TODO"),
        (
            "candidate_or_party_if_applicable",
            packet.get("candidate_or_party_if_applicable") or "TODO or not applicable",
        ),
        ("manual_operator_notes", "TODO"),
        ("unresolved_source_questions", "TODO"),
        ("source_capture_author_or_operator", "TODO"),
        ("source_capture_timestamp_local", "TODO"),
    ]
    for field, placeholder in field_labels:
        lines.append(f"- {field}: {placeholder}")
    lines.extend(["", "## SOURCE-003 Warnings", ""])
    warnings = packet["source_003_audit_reference"].get("normalization_warnings", [])
    if warnings:
        for warning in warnings:
            lines.append(f"- {warning}")
    else:
        lines.append("- none")
    lines.extend(["", "## Missing Fields Prefilled From SOURCE-003", ""])
    for field in packet["missing_fields_prefilled_from_source_003"]:
        lines.append(f"- {field}")
    lines.extend(
        [
            "",
            "## Operator Instructions",
            "",
            "1. Paste or summarize official resolution criteria if available locally.",
            "2. Add source/rule references if manually verified.",
            "3. Add source timestamp.",
            "4. Add reliability note.",
            "5. Do not add predictions or trading guidance.",
            "",
            "## References",
            "",
            f"- source_003_audit: {packet['source_003_audit_reference']['artifact_path']}",
            f"- packet_inventory: {packet['packet_inventory_reference']['artifact_path']}",
            f"- readiness_gate: {packet['readiness_gate_reference']['artifact_path']}",
            "",
            "## No Authority Flags",
            "",
        ]
    )
    for key in sorted(NO_AUTHORITY_FLAGS):
        lines.append(f"- {key}: {str(packet[key]).lower()}")
    lines.append("")
    return "\n".join(lines)


def _source_records(root=ROOT):
    inventory = _load_json(SOURCE_PATHS["inventory_json"], root=root)
    audit = _load_json(SOURCE_PATHS["source_003_audit_json"], root=root)
    readiness = _load_json(SOURCE_PATHS["readiness_scores_after_source_json"], root=root)
    return (
        _safe_list(inventory.get("markets")),
        _by_market(_safe_list(audit.get("markets"))),
        _by_market(_safe_list(readiness.get("markets"))),
    )


def build_capture_packets(root=ROOT):
    inventory_records, audit_by_market, readiness_by_market = _source_records(root=root)
    packets = []
    for record in inventory_records:
        market_id = str(record["market_id"])
        packets.append(
            build_capture_packet(
                record,
                _safe_dict(audit_by_market.get(market_id)),
                _safe_dict(readiness_by_market.get(market_id)),
            )
        )
    return packets


def _fields_missing_counts(packets):
    counts = Counter()
    for packet in packets:
        for field in RECOMMENDED_OPERATOR_FILL_ORDER:
            value = packet.get(field)
            if value in (None, "") or value == [] or value == {}:
                counts[field] += 1
    return [
        {"field": field, "market_count": counts[field]}
        for field in RECOMMENDED_OPERATOR_FILL_ORDER
        if counts[field]
    ]


def build_capture_manifest(root=ROOT):
    packets = build_capture_packets(root=root)
    markets_by_category = defaultdict(list)
    reviewed_counts = Counter()
    readiness_counts = Counter()
    capture_counts = Counter()
    packet_paths = []
    markdown_paths = []
    for packet in packets:
        market_id = packet["market_id"]
        markets_by_category[packet.get("category") or "unknown"].append(market_id)
        reviewed_counts[packet["current_openrouter_review_status"]] += 1
        readiness_counts[packet["current_readiness_band"]] += 1
        capture_counts[packet["source_capture_status"]] += 1
        packet_paths.append(_capture_packet_path(market_id))
        markdown_paths.append(_capture_markdown_path(market_id))
    reviewed_market_ids = [
        packet["market_id"]
        for packet in packets
        if packet["current_openrouter_review_status"] == "reviewed_accepted"
    ]
    unreviewed_market_ids = [
        packet["market_id"]
        for packet in packets
        if packet["current_openrouter_review_status"] == "not_reviewed"
    ]
    return {
        "schema_version": MANIFEST_VERSION,
        "contract_version": CONTRACT_VERSION,
        "task_id": TASK_ID,
        "generated_by": GENERATED_BY,
        "generated_at_marker": GENERATION_MARKER,
        "status": "manual_resolution_source_capture_manifest_created",
        "total_capture_packets": len(packets),
        "packet_paths": packet_paths,
        "markdown_paths": markdown_paths,
        "markets_by_category": {
            category: sorted(market_ids)
            for category, market_ids in sorted(markets_by_category.items())
        },
        "reviewed_vs_unreviewed": {
            "reviewed_accepted": reviewed_counts.get("reviewed_accepted", 0),
            "reviewed_blocked": reviewed_counts.get("reviewed_blocked", 0),
            "not_reviewed": reviewed_counts.get("not_reviewed", 0),
            "unknown": reviewed_counts.get("unknown", 0),
            "reviewed_market_ids": reviewed_market_ids,
            "unreviewed_market_ids": unreviewed_market_ids,
        },
        "readiness_band_counts": dict(sorted(readiness_counts.items())),
        "capture_status_counts": {
            status: capture_counts.get(status, 0) for status in CAPTURE_STATUS_VALUES
        },
        "fields_missing_across_all_packets": _fields_missing_counts(packets),
        "fields_required_for_high_completeness": list(
            FIELDS_REQUIRED_FOR_HIGH_COMPLETENESS
        ),
        "recommended_operator_fill_order": list(RECOMMENDED_OPERATOR_FILL_ORDER),
        "safety_summary": dict(SAFETY_SUMMARY),
        **NO_AUTHORITY_FLAGS,
    }


def render_capture_manifest_markdown(manifest):
    lines = [
        "# PMBOT Manual Resolution Source Capture Manifest v1",
        "",
        f"- schema_version: {manifest['schema_version']}",
        f"- contract_version: {manifest['contract_version']}",
        f"- task_id: {manifest['task_id']}",
        f"- status: {manifest['status']}",
        f"- total_capture_packets: {manifest['total_capture_packets']}",
        f"- no_market_action_guidance: {str(manifest['no_market_action_guidance']).lower()}",
        "",
        "## Capture Status Counts",
        "",
    ]
    for status, count in manifest["capture_status_counts"].items():
        lines.append(f"- {status}: {count}")
    lines.extend(["", "## Readiness Band Counts", ""])
    for band, count in manifest["readiness_band_counts"].items():
        lines.append(f"- {band}: {count}")
    lines.extend(["", "## Reviewed vs Unreviewed", ""])
    reviewed = manifest["reviewed_vs_unreviewed"]
    for key in ("reviewed_accepted", "reviewed_blocked", "not_reviewed", "unknown"):
        lines.append(f"- {key}: {reviewed[key]}")
    lines.append("- reviewed_market_ids: " + ", ".join(reviewed["reviewed_market_ids"]))
    lines.append("- unreviewed_market_ids: " + ", ".join(reviewed["unreviewed_market_ids"]))
    lines.extend(["", "## Markets By Category", ""])
    for category, market_ids in manifest["markets_by_category"].items():
        lines.append(f"- {category}: {', '.join(market_ids)}")
    lines.extend(["", "## Fields Missing Across All Packets", ""])
    for item in manifest["fields_missing_across_all_packets"]:
        lines.append(f"- {item['field']}: {item['market_count']}")
    lines.extend(["", "## Required For High Completeness", ""])
    for field in manifest["fields_required_for_high_completeness"]:
        lines.append(f"- {field}")
    lines.extend(["", "## Recommended Operator Fill Order", ""])
    for index, field in enumerate(manifest["recommended_operator_fill_order"], start=1):
        lines.append(f"{index}. {field}")
    lines.extend(
        [
            "",
            "## Safety Summary",
            "",
            "- no OpenRouter calls",
            "- no Polymarket API calls",
            "- no network calls",
            "- no trading",
            "- no wallet/orders",
            "- no runtime/dispatcher/background/browser/queue changes",
            "- no API key access",
            "- no market recommendations",
            "- no probability, EV, edge, confidence, or side selection",
            "",
            "## Packet Paths",
            "",
        ]
    )
    for path in manifest["packet_paths"]:
        lines.append(f"- {path}")
    lines.extend(["", "## Markdown Paths", ""])
    for path in manifest["markdown_paths"]:
        lines.append(f"- {path}")
    lines.append("")
    return "\n".join(lines)


def write_manual_resolution_source_capture_artifacts(root=ROOT):
    schema = build_capture_schema()
    _write_json(SOURCE_PATHS["schema_json"], schema, root=root)
    _write_text(
        SOURCE_PATHS["schema_md"],
        render_capture_schema_markdown(schema),
        root=root,
    )

    packets = build_capture_packets(root=root)
    files_written = [SOURCE_PATHS["schema_json"], SOURCE_PATHS["schema_md"]]
    for packet in packets:
        json_path = _capture_packet_path(packet["market_id"])
        md_path = _capture_markdown_path(packet["market_id"])
        _write_json(json_path, packet, root=root)
        _write_text(md_path, render_capture_packet_markdown(packet), root=root)
        files_written.extend([json_path, md_path])

    manifest = build_capture_manifest(root=root)
    _write_json(SOURCE_PATHS["manifest_json"], manifest, root=root)
    _write_text(
        SOURCE_PATHS["manifest_md"],
        render_capture_manifest_markdown(manifest),
        root=root,
    )
    files_written.extend([SOURCE_PATHS["manifest_json"], SOURCE_PATHS["manifest_md"]])
    return {
        "task_id": TASK_ID,
        "status": "manual_resolution_source_capture_artifacts_written",
        "files_written": files_written,
        "capture_packet_count": len(packets),
        "capture_json_template_count": len(packets),
        "capture_markdown_template_count": len(packets),
        "openrouter_calls_performed": 0,
        "polymarket_api_calls_performed": 0,
        "external_network_calls_performed": 0,
    }


def main(argv):
    args = _parse_args(argv)
    if args.write:
        print(
            json.dumps(
                write_manual_resolution_source_capture_artifacts(ROOT),
                indent=2,
                ensure_ascii=True,
            )
        )
        return 0
    manifest = build_capture_manifest(ROOT)
    if args.markdown:
        print(render_capture_manifest_markdown(manifest), end="")
    else:
        print(json.dumps(manifest, indent=2, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(__import__("sys").argv[1:]))
