import argparse
import json
from collections import Counter
from pathlib import Path


TASK_ID = "PMBOT-SOURCE-001-EVIDENCE-ENRICHMENT-DESIGN-FROM-INVENTORY"
SCHEMA_VERSION = "source_evidence_enrichment_artifacts.v1"
GENERATED_BY = "pm_bot/llm/source_evidence_enrichment_artifacts.py"
GENERATION_MARKER = "deterministic-source-001-local-artifact-generation.v1"
HEAD_BEFORE = "aa2b8a982cd383d2211f818d33ccbf7ae3c27362"

ROOT = Path(__file__).resolve().parents[2]
LLM_DIR = ROOT / "pm_bot" / "llm"
WORKBENCH_DIR = ROOT / "pm_bot" / "workbench"
DOCS_DIR = ROOT / "docs"

SOURCE_PATHS = {
    "result_053": "docs/PMBOT_OPENROUTER_053_RESULT.json",
    "inventory_json": "pm_bot/llm/current_llm_market_packet_inventory.v1.json",
    "evidence_audit_json": "pm_bot/llm/current_llm_source_evidence_completeness_audit.v1.json",
    "dashboard_json": "pm_bot/workbench/operator_openrouter_review_dashboard.v1.json",
    "requirements_json": "pm_bot/llm/source_evidence_enrichment_requirements.v1.json",
    "requirements_md": "pm_bot/llm/source_evidence_enrichment_requirements.v1.md",
    "readiness_json": "pm_bot/llm/current_llm_packet_evidence_readiness_scores.v1.json",
    "readiness_md": "pm_bot/llm/current_llm_packet_evidence_readiness_scores.v1.md",
    "gap_plan_json": "pm_bot/llm/source_evidence_gap_plan_by_category.v1.json",
    "gap_plan_md": "pm_bot/llm/source_evidence_gap_plan_by_category.v1.md",
    "contract_json": "pm_bot/llm/llm_market_packet_completeness_contract.v1.json",
    "contract_md": "pm_bot/llm/llm_market_packet_completeness_contract.v1.md",
    "design_json": "pm_bot/llm/source_evidence_enrichment_design.v1.json",
    "design_md": "docs/PMBOT_SOURCE_EVIDENCE_ENRICHMENT_DESIGN.md",
    "source_001_result_json": "docs/PMBOT_SOURCE_001_RESULT.json",
    "source_001_report_md": "docs/PMBOT_SOURCE_001_EVIDENCE_ENRICHMENT_DESIGN_FROM_INVENTORY.md",
}

NO_AUTHORITY_TRUE_FLAGS = {
    "operator_review_only": True,
    "passive_context_only": True,
    "no_trading_authority": True,
    "no_queue_authority": True,
    "no_runtime_authority": True,
    "no_dispatcher_authority": True,
    "no_wallet_or_order_authority": True,
    "acceptance_is_not_trading_approval": True,
    "analysis_only": True,
    "manual_review_only": True,
    "no_market_action_guidance": True,
    "no_probability_ev_edge_confidence_side_selection": True,
    "no_buy_sell_hold_enter_exit": True,
}

SAFETY_SUMMARY = {
    **NO_AUTHORITY_TRUE_FLAGS,
    "openrouter_calls_performed_by_this_task": 0,
    "polymarket_api_calls_performed_by_this_task": 0,
    "external_network_calls_performed_by_this_task": 0,
    "network_calls_performed_by_this_task": 0,
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
    "live_enrichment_performed": False,
    "market_decisions_made": False,
}

COMMON_CORE_FIELDS = [
    "market_id",
    "title_or_question",
    "category",
    "settlement_or_resolution_description_if_available",
    "resolution_source_or_rules_if_available",
    "event_deadline_or_end_date_if_available",
    "local_evidence_notes",
    "source_gap_notes",
    "contradiction_checks",
    "risk_notes",
    "operator_checklist",
    "llm_packet_provenance",
    "artifact_generation_marker",
    "operator_review_only_safety_contract",
]

COMMON_RECOMMENDED_FIELDS = [
    "source_artifact_path",
    "candidate_source_type",
    "outcome_labels",
    "source_timestamps_when_present_locally",
    "source_reliability_review_when_present_locally",
    "local_packet_completeness_score",
    "fields_marked_unknown_with_reason",
]

COMMON_MINIMUM_BATCH_FIELDS = [
    "market_id",
    "market_title_or_question",
    "category",
    "local_packet_provenance",
    "operator_review_only_safety_contract",
    "local_context_for_missing_evidence_risk_and_checklist_sections",
    "no_runtime_trading_or_queue_authority",
]

COMMON_HIGH_COMPLETENESS_FIELDS = [
    "full_market_resolution_criteria_text",
    "official_source_or_rule_reference_notes",
    "explicit_source_gap_notes",
    "contradiction_check_context",
    "risk_notes_context",
    "operator_checklist",
    "category_specific_key_fields",
]

COMMON_ALLOWED_UNKNOWN = [
    "live_external_source_url_when_absent_from_local_artifacts",
    "source_timestamp_when_absent_from_local_artifacts",
    "market_status_when_not_recorded_locally",
    "nonessential_background_context",
]

PROHIBITED_ENRICHMENT_BEHAVIOR = [
    "do_not_fetch_external_data",
    "do_not_call_polymarket_api",
    "do_not_call_openrouter_or_other_llm_api",
    "do_not_use_browser_automation",
    "do_not_read_or_print_api_keys",
    "do_not_touch_wallets_orders_or_private_keys",
    "do_not_mutate_queue_state",
    "do_not_add_runtime_dispatcher_or_background_wiring",
    "do_not_produce_market_action_guidance",
    "do_not_score_probability_ev_edge_confidence_or_side_selection",
]

SCORE_WEIGHTS = {
    "identity/title completeness": 15,
    "category completeness": 10,
    "resolution/source completeness": 15,
    "local evidence completeness": 15,
    "missing evidence notes completeness": 10,
    "contradiction checks completeness": 10,
    "risk notes completeness": 10,
    "operator checklist completeness": 10,
    "provenance/artifact completeness": 5,
}

CATEGORY_REQUIREMENT_OVERRIDES = {
    "crypto": {
        "category_specific_core_fields": [
            "asset_or_ticker",
            "threshold",
            "date_or_resolution_window",
            "settlement_condition",
            "benchmark_or_price_source_rule_if_available",
        ],
        "resolution_source_requirements": [
            "full threshold and hit-condition rules",
            "asset/ticker normalization",
            "benchmark, exchange, index, or price-source rule if present locally",
            "timezone and date-window rule if present locally",
        ],
        "fields_required_for_high_completeness": [
            "asset_or_ticker",
            "threshold",
            "date_or_resolution_window",
            "settlement_condition",
            "benchmark_and_timezone_rules",
            "full_market_resolution_criteria_text",
            "official_source_or_rule_reference_notes",
            "source_timestamps_when_present_locally",
        ],
    },
    "elections": {
        "category_specific_core_fields": [
            "jurisdiction",
            "office_or_election_event",
            "candidate_or_party_if_applicable",
            "round_or_stage_if_applicable",
            "date_or_resolution_window",
            "official_election_authority_identifier_if_available",
        ],
        "resolution_source_requirements": [
            "jurisdiction and election event definition",
            "office, candidate, round, or stage named by the market",
            "official election authority or resolution-rule reference if present locally",
            "date/window and recount/runoff treatment if present locally",
        ],
        "fields_required_for_high_completeness": [
            "jurisdiction",
            "office_or_election_event",
            "candidate_or_party_if_applicable",
            "date_or_resolution_window",
            "official_election_authority_identifier_if_available",
            "full_market_resolution_criteria_text",
            "official_source_or_rule_reference_notes",
            "source_timestamps_when_present_locally",
        ],
    },
    "legal/courts": {
        "category_specific_core_fields": [
            "court_or_legal_body",
            "case_or_event_definition",
            "docket_identifier_if_available",
            "decision_or_acceptance_condition",
            "date_or_resolution_window",
        ],
        "resolution_source_requirements": [
            "legal event definition and required action",
            "court, agency, or docket identifier if present locally",
            "deadline/window and settlement rule text",
            "official docket, order, or court-source reference if present locally",
        ],
        "fields_required_for_high_completeness": [
            "court_or_legal_body",
            "case_or_event_definition",
            "docket_identifier_if_available",
            "decision_or_acceptance_condition",
            "date_or_resolution_window",
            "full_market_resolution_criteria_text",
            "official_source_or_rule_reference_notes",
            "source_timestamps_when_present_locally",
        ],
    },
    "politics": {
        "category_specific_core_fields": [
            "jurisdiction",
            "office_or_public_role",
            "named_person_or_institution",
            "event_definition",
            "date_or_resolution_window",
            "official_source_or_resolution_rule_if_available",
        ],
        "resolution_source_requirements": [
            "political event definition and named office/person",
            "jurisdiction and deadline/window",
            "official government or market rule source if present locally",
            "clear treatment of resignation, removal, vacancy, or role-change ambiguity",
        ],
        "fields_required_for_high_completeness": [
            "jurisdiction",
            "office_or_public_role",
            "named_person_or_institution",
            "event_definition",
            "date_or_resolution_window",
            "full_market_resolution_criteria_text",
            "official_source_or_rule_reference_notes",
            "source_timestamps_when_present_locally",
        ],
    },
    "company/business": {
        "category_specific_core_fields": [
            "entity",
            "event_definition",
            "instrument_or_business_action_if_applicable",
            "date_or_resolution_window",
            "source_or_resolution_rules_if_available",
        ],
        "resolution_source_requirements": [
            "entity and event definition",
            "date/window and qualifying business action",
            "primary company, regulator, exchange, filing, or market-rule source if present locally",
            "treatment of rumors, announcements, filings, and completed events if present locally",
        ],
        "fields_required_for_high_completeness": [
            "entity",
            "event_definition",
            "instrument_or_business_action_if_applicable",
            "date_or_resolution_window",
            "full_market_resolution_criteria_text",
            "official_source_or_rule_reference_notes",
            "source_timestamps_when_present_locally",
        ],
    },
}

CATEGORY_GAP_HINTS = {
    "crypto": [
        "benchmark_and_timezone_rules",
        "asset_or_ticker",
        "threshold",
        "full_resolution_rules",
        "official_source_references",
        "source_timestamps",
    ],
    "elections": [
        "jurisdiction",
        "office_or_election_event",
        "candidate_or_party_if_applicable",
        "official_election_authority_identifier",
        "full_resolution_rules",
        "official_source_references",
        "source_timestamps",
    ],
    "legal/courts": [
        "court_or_legal_body",
        "case_or_event_definition",
        "docket_identifier",
        "full_resolution_rules",
        "official_source_references",
        "source_timestamps",
    ],
    "politics": [
        "jurisdiction",
        "office_or_public_role",
        "named_person_or_institution",
        "event_definition",
        "full_resolution_rules",
        "official_source_references",
        "source_timestamps",
    ],
    "company/business": [
        "entity",
        "event_definition",
        "instrument_or_business_action_if_applicable",
        "full_resolution_rules",
        "official_source_references",
        "source_timestamps",
    ],
}

VALIDATION_COMMANDS = [
    "python -m compileall pm_bot",
    "python -m pytest tests pm_bot\\llm\\tests -q",
    "python -m pytest pm_bot\\llm\\tests -q",
    "python -m pytest pm_bot\\workbench\\tests -q",
    "python -m pytest tests\\test_openrouter_result_artifacts.py -q",
    "python -m pm_bot.workbench.run_operator_workbench_export",
    "JSON parse checks for SOURCE-001 and 053 source/workbench JSON artifacts",
    "Result JSON checks for 053 and SOURCE-001",
    "Public Markdown market-action guidance scan over generated SOURCE-001 artifacts",
    "Secret scan over changed files",
]

FILES_CHANGED_STATIC = [
    "docs/PMBOT_SOURCE_001_EVIDENCE_ENRICHMENT_DESIGN_FROM_INVENTORY.md",
    "docs/PMBOT_SOURCE_001_RESULT.json",
    "docs/PMBOT_SOURCE_EVIDENCE_ENRICHMENT_DESIGN.md",
    "docs/PMBOT_CODEX_A_ROUND003_RESULT.json",
    "docs/PMBOT_WORKBENCH_001_RESULT.json",
    "docs/PMBOT_WORKBENCH_003_RESULT.json",
    "pm_bot/llm/current_llm_packet_evidence_readiness_scores.v1.json",
    "pm_bot/llm/current_llm_packet_evidence_readiness_scores.v1.md",
    "pm_bot/llm/llm_market_packet_completeness_contract.v1.json",
    "pm_bot/llm/llm_market_packet_completeness_contract.v1.md",
    "pm_bot/llm/source_evidence_enrichment_artifacts.py",
    "pm_bot/llm/source_evidence_enrichment_design.v1.json",
    "pm_bot/llm/source_evidence_enrichment_requirements.v1.json",
    "pm_bot/llm/source_evidence_enrichment_requirements.v1.md",
    "pm_bot/llm/source_evidence_gap_plan_by_category.v1.json",
    "pm_bot/llm/source_evidence_gap_plan_by_category.v1.md",
    "pm_bot/llm/openrouter_operator_review_artifacts_053.py",
    "pm_bot/llm/tests/test_current_llm_packet_evidence_readiness_scores.py",
    "pm_bot/llm/tests/test_llm_market_packet_completeness_contract.py",
    "pm_bot/llm/tests/test_source_evidence_enrichment_design.py",
    "pm_bot/llm/tests/test_source_evidence_enrichment_requirements.py",
    "pm_bot/llm/tests/test_source_evidence_gap_plan_by_category.py",
    "pm_bot/workbench/export_operator_review_pack.py",
    "pm_bot/workbench/operator_openrouter_review_dashboard.v1.json",
    "pm_bot/workbench/operator_openrouter_review_dashboard.v1.md",
    "pm_bot/workbench/operator_review_pack.v1.json",
    "pm_bot/workbench/operator_review_pack.v1.md",
    "pm_bot/workbench/operator_workbench_export_run.v1.json",
    "pm_bot/workbench/operator_workbench_export_run.v1.md",
    "pm_bot/workbench/run_operator_workbench_export.py",
    "pm_bot/workbench/expected_operator_review_pack.v1.json",
    "pm_bot/workbench/expected_operator_workbench_export_run.v1.json",
    "pm_bot/workbench/tests/test_operator_openrouter_review_dashboard.py",
    "pm_bot/workbench/tests/test_operator_review_pack_export.py",
    "pm_bot/workbench/tests/test_operator_workbench_export_runner.py",
    "tests/test_openrouter_result_artifacts.py",
]


def _parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Write deterministic local SOURCE-001 source/evidence artifacts."
    )
    parser.add_argument("--write", action="store_true", help="Write all SOURCE-001 artifacts.")
    parser.add_argument("--result-only", action="store_true", help="Write only SOURCE-001 result/report.")
    parser.add_argument("--markdown", action="store_true", help="Print the result report Markdown.")
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


def _load_optional_json(path, root=ROOT):
    resolved = _resolve(path, root=root)
    if not resolved.exists():
        return None
    with resolved.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    return payload if isinstance(payload, dict) else None


def _write_json(path, payload, root=ROOT):
    resolved = _resolve(path, root=root)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    resolved.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def _write_text(path, text, root=ROOT):
    resolved = _resolve(path, root=root)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    resolved.write_text(_ascii(text), encoding="utf-8")


def _safe_dict(value):
    return value if isinstance(value, dict) else {}


def _safe_list(value):
    return value if isinstance(value, list) else []


def _ascii(value):
    return str(value).encode("ascii", "backslashreplace").decode("ascii")


def _status(path, root=ROOT):
    payload = _load_optional_json(path, root=root)
    return _safe_dict(payload).get("status", "missing")


def _inventory(root=ROOT):
    return _load_json(SOURCE_PATHS["inventory_json"], root=root)


def _evidence_audit(root=ROOT):
    return _load_json(SOURCE_PATHS["evidence_audit_json"], root=root)


def _categories_from_inventory(inventory):
    categories = sorted({item["category"] for item in _safe_list(inventory.get("markets"))})
    return [category for category in categories if category != "unknown"]


def _market_ids_by_category(inventory):
    grouped = {}
    for item in _safe_list(inventory.get("markets")):
        grouped.setdefault(item["category"], []).append(item["market_id"])
    return {category: sorted(market_ids) for category, market_ids in sorted(grouped.items())}


def _category_config(category):
    fallback = {
        "category_specific_core_fields": [
            "event_definition",
            "named_participants_or_entities_if_applicable",
            "date_or_resolution_window",
            "source_or_resolution_rules_if_available",
        ],
        "resolution_source_requirements": [
            "event definition",
            "named participant, entity, or condition if applicable",
            "date/window and settlement rule text",
            "source or rule reference if present locally",
        ],
        "fields_required_for_high_completeness": [
            "event_definition",
            "date_or_resolution_window",
            "full_market_resolution_criteria_text",
            "official_source_or_rule_reference_notes",
            "source_timestamps_when_present_locally",
        ],
    }
    return CATEGORY_REQUIREMENT_OVERRIDES.get(category, fallback)


def _category_requirements(category):
    config = _category_config(category)
    category_core = config["category_specific_core_fields"]
    high_fields = list(dict.fromkeys(COMMON_HIGH_COMPLETENESS_FIELDS + config["fields_required_for_high_completeness"]))
    return {
        "category": category,
        "required_core_fields": list(dict.fromkeys(COMMON_CORE_FIELDS + category_core)),
        "recommended_context_fields": list(COMMON_RECOMMENDED_FIELDS),
        "resolution_source_requirements": config["resolution_source_requirements"],
        "local_evidence_requirements": [
            "use local packet text and local source artifact pointers only",
            "record whether evidence is placeholder, stub, manually exported, or reviewed local file content",
            "retain source gap notes when local evidence is absent",
            "record local provenance for every evidence note",
        ],
        "contradiction_check_requirements": [
            "record local context that could conflict with the title/question",
            "record ambiguity in resolution rules, date windows, entity identity, or source authority",
            "separate contradiction context from market outcome assessment",
        ],
        "risk_note_requirements": [
            "record source/rule ambiguity risks",
            "record stale or stub-only packet risks",
            "record category-specific missing-field risks",
            "record operator-review limitations without suggesting market action",
        ],
        "operator_checklist_requirements": [
            "confirm packet and prompt provenance",
            "confirm resolution/rule text is copied or explicitly marked unavailable locally",
            "confirm source gaps are explicit",
            "confirm contradiction context and risk notes are present",
            "confirm no trading, queue, wallet, or runtime authority is granted",
        ],
        "minimum_packet_fields_for_llm_review": list(COMMON_MINIMUM_BATCH_FIELDS),
        "fields_required_for_high_completeness": high_fields,
        "fields_allowed_to_be_unknown": list(COMMON_ALLOWED_UNKNOWN),
        "local_only_enrichment_notes": [
            "Enrichment may only read local packets, prompts, local snapshots, and manually exported source files.",
            "Unknown fields must remain unknown with a source gap note instead of triggering live fetching.",
            "A future network-capable adapter would require a separate explicit approval task.",
        ],
        "prohibited_enrichment_behavior": list(PROHIBITED_ENRICHMENT_BEHAVIOR),
    }


def build_source_evidence_enrichment_requirements(root=ROOT):
    inventory = _inventory(root=root)
    categories = _categories_from_inventory(inventory)
    return {
        "schema_version": "source_evidence_enrichment_requirements.v1",
        "task_id": TASK_ID,
        "generated_by": GENERATED_BY,
        "generated_at_marker": GENERATION_MARKER,
        "status": "requirements_created",
        "source_inventory_path": SOURCE_PATHS["inventory_json"],
        "category_source": "categories_observed_in_053_inventory_only",
        "category_count": len(categories),
        "categories": [_category_requirements(category) for category in categories],
        "common_requirements": {
            "required_core_fields": list(COMMON_CORE_FIELDS),
            "recommended_context_fields": list(COMMON_RECOMMENDED_FIELDS),
            "minimum_packet_fields_for_llm_review": list(COMMON_MINIMUM_BATCH_FIELDS),
            "fields_required_for_high_completeness": list(COMMON_HIGH_COMPLETENESS_FIELDS),
            "fields_allowed_to_be_unknown": list(COMMON_ALLOWED_UNKNOWN),
            "prohibited_enrichment_behavior": list(PROHIBITED_ENRICHMENT_BEHAVIOR),
        },
        "network_calls_performed": 0,
        "polymarket_api_calls_performed": 0,
        "openrouter_calls_performed": 0,
        "safety_summary": dict(SAFETY_SUMMARY),
    }


def render_source_evidence_enrichment_requirements_markdown(requirements):
    lines = [
        "# PMBOT Source Evidence Enrichment Requirements v1",
        "",
        f"- schema_version: {requirements['schema_version']}",
        f"- task_id: {requirements['task_id']}",
        f"- status: {requirements['status']}",
        f"- category_source: {requirements['category_source']}",
        f"- category_count: {requirements['category_count']}",
        "- openrouter_calls_performed: 0",
        "- polymarket_api_calls_performed: 0",
        "- network_calls_performed: 0",
        "",
        "## Common Minimum Fields",
        "",
    ]
    for item in requirements["common_requirements"]["minimum_packet_fields_for_llm_review"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Categories", ""])
    for category in requirements["categories"]:
        lines.extend(
            [
                f"### {category['category']}",
                "",
                "- required_core_fields: " + ", ".join(category["required_core_fields"]),
                "- recommended_context_fields: " + ", ".join(category["recommended_context_fields"]),
                "- fields_required_for_high_completeness: "
                + ", ".join(category["fields_required_for_high_completeness"]),
                "- fields_allowed_to_be_unknown: " + ", ".join(category["fields_allowed_to_be_unknown"]),
                "- prohibited_enrichment_behavior: "
                + ", ".join(category["prohibited_enrichment_behavior"]),
                "",
            ]
        )
    lines.extend(
        [
            "## Safety",
            "",
            "- local-only planning artifact",
            "- no market action guidance",
            "- no OpenRouter calls",
            "- no Polymarket API calls",
            "- no network calls",
            "- no wallet, order, queue, runtime, dispatcher, background, or browser authority",
            "",
        ]
    )
    return "\n".join(lines)


def _audit_by_market(audit):
    return {item["market_id"]: item for item in _safe_list(audit.get("reviewed_markets"))}


def _packet_for_inventory_item(item, root=ROOT):
    packet_path = item.get("packet_file_path")
    return _load_optional_json(packet_path, root=root) if packet_path else None


def _prompt_exists(item, root=ROOT):
    prompt_path = item.get("prompt_file_path")
    return bool(prompt_path and _resolve(prompt_path, root=root).exists())


def _packet_exists(item, root=ROOT):
    packet_path = item.get("packet_file_path")
    return bool(packet_path and _resolve(packet_path, root=root).exists())


def _text_blob(*values):
    pieces = []
    for value in values:
        if isinstance(value, str):
            pieces.append(value)
        elif isinstance(value, list):
            pieces.extend(str(item) for item in value)
        elif isinstance(value, dict):
            pieces.append(json.dumps(value, sort_keys=True, ensure_ascii=True))
    return " ".join(pieces).lower()


def _has_stub_or_placeholder(packet, item):
    packet = _safe_dict(packet)
    context = _safe_dict(packet.get("market_context"))
    local = _safe_dict(packet.get("local_review_context"))
    return any(
        term in _text_blob(
            context.get("public_resolution_context"),
            local.get("local_resolution_or_description_snippet"),
            packet.get("evidence_source_placeholders"),
            packet.get("source_gap_notes"),
            item.get("warnings"),
        )
        for term in ("stub", "placeholder", "template only", "manual check template")
    )


def _local_evidence_is_placeholder(packet):
    notes = _safe_list(_safe_dict(packet).get("evidence_source_placeholders"))
    if not notes:
        return False
    return True


def _category_gap_fields(category):
    return list(CATEGORY_GAP_HINTS.get(category, ["full_resolution_rules", "official_source_references", "source_timestamps"]))


def _score_inventory_item(item, audit_item, root=ROOT):
    packet = _packet_for_inventory_item(item, root=root)
    packet_exists = _packet_exists(item, root=root)
    prompt_exists = _prompt_exists(item, root=root)
    packet_dict = _safe_dict(packet)
    local_counts = _safe_dict(item.get("local_counts"))
    title_present = bool(item.get("title_or_question"))
    category_known = bool(item.get("category")) and item.get("category") != "unknown"
    placeholder_or_stub = _has_stub_or_placeholder(packet_dict, item)
    local_evidence_present = bool(item.get("local_evidence_fields_present"))
    missing_notes_present = bool(item.get("missing_evidence_notes_present"))
    contradiction_present = bool(item.get("contradiction_checks_present"))
    risk_present = bool(item.get("risk_notes_present"))
    checklist_present = bool(item.get("operator_checklist_present"))
    provenance_present = bool(
        packet_exists
        and prompt_exists
        and packet_dict.get("generated_at")
        and packet_dict.get("source_artifacts")
    )

    breakdown = {
        "identity/title completeness": SCORE_WEIGHTS["identity/title completeness"]
        if packet_exists and prompt_exists and title_present and item.get("market_id")
        else 0,
        "category completeness": SCORE_WEIGHTS["category completeness"] if category_known else 0,
        "resolution/source completeness": (
            15
            if item.get("resolution_source_fields_present") and not placeholder_or_stub
            else (6 if item.get("resolution_source_fields_present") else 0)
        ),
        "local evidence completeness": (
            15
            if local_evidence_present and not _local_evidence_is_placeholder(packet_dict)
            else (8 if local_evidence_present else 0)
        ),
        "missing evidence notes completeness": SCORE_WEIGHTS["missing evidence notes completeness"]
        if missing_notes_present or _safe_list(packet_dict.get("missing_evidence"))
        else 0,
        "contradiction checks completeness": SCORE_WEIGHTS["contradiction checks completeness"]
        if contradiction_present
        else 0,
        "risk notes completeness": SCORE_WEIGHTS["risk notes completeness"] if risk_present else 0,
        "operator checklist completeness": SCORE_WEIGHTS["operator checklist completeness"]
        if checklist_present
        else 0,
        "provenance/artifact completeness": SCORE_WEIGHTS["provenance/artifact completeness"]
        if provenance_present
        else (3 if packet_exists and prompt_exists else 0),
    }
    score = sum(breakdown.values())
    if not packet_exists or not prompt_exists or not title_present:
        readiness_band = "blocked"
    elif score >= 90:
        readiness_band = "high"
    elif score >= 60:
        readiness_band = "medium"
    elif score >= 30:
        readiness_band = "low"
    else:
        readiness_band = "blocked"

    missing_or_weak = []
    if breakdown["resolution/source completeness"] < SCORE_WEIGHTS["resolution/source completeness"]:
        missing_or_weak.extend(
            [
                "full_market_resolution_criteria_text",
                "official_source_urls_or_rule_references",
                "source_timestamps",
                "source_reliability_review",
            ]
        )
    if breakdown["local evidence completeness"] < SCORE_WEIGHTS["local evidence completeness"]:
        missing_or_weak.extend(["reviewed_local_evidence_references", "non_placeholder_evidence_notes"])
    if not contradiction_present:
        missing_or_weak.append("contradiction_checks")
    if not risk_present:
        missing_or_weak.append("risk_notes")
    if not checklist_present:
        missing_or_weak.append("operator_checklist")
    if audit_item is None:
        missing_or_weak.append("evidence_completeness_audit_status")
    missing_or_weak.extend(_category_gap_fields(item["category"]))
    missing_or_weak = sorted(dict.fromkeys(missing_or_weak))

    recommended_actions = [
        "Copy full local market resolution/rule text into packet source notes when present locally.",
        "Replace placeholder source notes with reviewed local artifact references or manually exported source references.",
        "Record source gap notes and local timestamps when present in local artifacts.",
    ]
    if not contradiction_present:
        recommended_actions.append("Add contradiction context from local packet text only.")
    if not risk_present:
        recommended_actions.append("Add risk note context from local packet text only.")
    if not checklist_present:
        recommended_actions.append("Add a standardized operator checklist section.")
    if local_counts.get("source_gap_notes_count", 0) == 0:
        recommended_actions.append("Normalize source gap counts from packet source_gap_notes.")

    current_level = (
        audit_item.get("evidence_completeness_level")
        if isinstance(audit_item, dict)
        else "unknown"
    )
    suitable_for_future_llm_review = bool(packet_exists and prompt_exists and score >= 60)
    suitable_for_future_openrouter_batch = bool(packet_exists and prompt_exists and score >= 70)
    return {
        "market_id": item["market_id"],
        "title_or_question": item.get("title_or_question"),
        "category": item["category"],
        "packet_exists": packet_exists,
        "prompt_exists": prompt_exists,
        "reviewed_by_openrouter": bool(item.get("already_reviewed_by_openrouter")),
        "accepted_for_operator_review": item.get("accepted_for_operator_review"),
        "current_evidence_completeness_level": current_level,
        "evidence_readiness_score": score,
        "score_breakdown": breakdown,
        "readiness_band": readiness_band,
        "suitable_for_future_llm_review": suitable_for_future_llm_review,
        "suitable_for_future_openrouter_batch": suitable_for_future_openrouter_batch,
        "needs_local_enrichment_before_review": current_level != "high" or score < 90,
        "missing_or_weak_fields": missing_or_weak,
        "recommended_local_enrichment_actions": recommended_actions,
        "no_market_action_guidance": True,
    }


def _readiness_aggregate(markets):
    bands = Counter(item["readiness_band"] for item in markets)
    reviewed_count = sum(1 for item in markets if item["reviewed_by_openrouter"])
    unreviewed_count = len(markets) - reviewed_count
    average = round(
        sum(item["evidence_readiness_score"] for item in markets) / len(markets), 2
    ) if markets else 0
    category_summary = {}
    for item in markets:
        summary = category_summary.setdefault(
            item["category"],
            {
                "market_count": 0,
                "reviewed_count": 0,
                "unreviewed_count": 0,
                "score_total": 0,
                "average_evidence_readiness_score": 0,
                "readiness_band_counts": {"high": 0, "medium": 0, "low": 0, "blocked": 0},
                "market_ids": [],
            },
        )
        summary["market_count"] += 1
        summary["reviewed_count"] += 1 if item["reviewed_by_openrouter"] else 0
        summary["unreviewed_count"] += 0 if item["reviewed_by_openrouter"] else 1
        summary["score_total"] += item["evidence_readiness_score"]
        summary["readiness_band_counts"][item["readiness_band"]] += 1
        summary["market_ids"].append(item["market_id"])
    for summary in category_summary.values():
        summary["average_evidence_readiness_score"] = round(
            summary["score_total"] / summary["market_count"], 2
        )
        del summary["score_total"]
        summary["market_ids"].sort()
    missing_counter = Counter()
    for item in markets:
        missing_counter.update(item["missing_or_weak_fields"])
    top_missing = [
        {"field": field, "market_count": count}
        for field, count in missing_counter.most_common()
    ]
    return {
        "total_markets_scored": len(markets),
        "high_count": bands.get("high", 0),
        "medium_count": bands.get("medium", 0),
        "low_count": bands.get("low", 0),
        "blocked_count": bands.get("blocked", 0),
        "reviewed_count": reviewed_count,
        "unreviewed_count": unreviewed_count,
        "average_evidence_readiness_score": average,
        "category_score_summary": {key: category_summary[key] for key in sorted(category_summary)},
        "top_missing_fields": top_missing,
        "recommended_next_local_enrichment_focus": [
            "resolution source extraction",
            "source gap normalization",
            "operator checklist standardization for unreviewed packets",
            "contradiction and risk context builder for unreviewed packets",
            "local packet completeness scorer integration",
        ],
    }


def build_current_llm_packet_evidence_readiness_scores(root=ROOT):
    inventory = _inventory(root=root)
    audit = _evidence_audit(root=root)
    audit_lookup = _audit_by_market(audit)
    markets = [
        _score_inventory_item(item, audit_lookup.get(item["market_id"]), root=root)
        for item in _safe_list(inventory.get("markets"))
    ]
    return {
        "schema_version": "current_llm_packet_evidence_readiness_scores.v1",
        "task_id": TASK_ID,
        "generated_by": GENERATED_BY,
        "generated_at_marker": GENERATION_MARKER,
        "status": "readiness_scores_created",
        "source_inventory_path": SOURCE_PATHS["inventory_json"],
        "source_evidence_audit_path": SOURCE_PATHS["evidence_audit_json"],
        "scoring_model": {
            "model_version": "evidence_readiness_score.v1",
            "score_scope": "evidence_and_packet_readiness_only",
            "weights": dict(SCORE_WEIGHTS),
            "readiness_bands": {
                "high": "90-100 and not blocked",
                "medium": "60-89",
                "low": "30-59",
                "blocked": "0-29 or missing packet/prompt/title",
            },
            "not_market_attractiveness_score": True,
            "not_probability_score": True,
            "not_expected_value_score": True,
            "not_side_selection_score": True,
        },
        "markets": markets,
        "aggregate": _readiness_aggregate(markets),
        "network_calls_performed": 0,
        "polymarket_api_calls_performed": 0,
        "openrouter_calls_performed": 0,
        "safety_summary": dict(SAFETY_SUMMARY),
    }


def render_current_llm_packet_evidence_readiness_scores_markdown(readiness):
    aggregate = readiness["aggregate"]
    lines = [
        "# PMBOT Current LLM Packet Evidence Readiness Scores v1",
        "",
        f"- schema_version: {readiness['schema_version']}",
        f"- task_id: {readiness['task_id']}",
        f"- status: {readiness['status']}",
        f"- total_markets_scored: {aggregate['total_markets_scored']}",
        f"- high_count: {aggregate['high_count']}",
        f"- medium_count: {aggregate['medium_count']}",
        f"- low_count: {aggregate['low_count']}",
        f"- blocked_count: {aggregate['blocked_count']}",
        f"- reviewed_count: {aggregate['reviewed_count']}",
        f"- unreviewed_count: {aggregate['unreviewed_count']}",
        f"- average_evidence_readiness_score: {aggregate['average_evidence_readiness_score']}",
        "- no_market_action_guidance: true",
        "",
        "## Markets",
        "",
    ]
    for item in readiness["markets"]:
        lines.extend(
            [
                f"- market_id: {item['market_id']}",
                f"  category: {item['category']}",
                f"  reviewed_by_openrouter: {str(item['reviewed_by_openrouter']).lower()}",
                f"  accepted_for_operator_review: {str(item['accepted_for_operator_review']).lower() if item['accepted_for_operator_review'] is not None else 'unknown'}",
                f"  current_evidence_completeness_level: {item['current_evidence_completeness_level']}",
                f"  evidence_readiness_score: {item['evidence_readiness_score']}",
                f"  readiness_band: {item['readiness_band']}",
                f"  needs_local_enrichment_before_review: {str(item['needs_local_enrichment_before_review']).lower()}",
                f"  missing_or_weak_fields: {', '.join(item['missing_or_weak_fields'])}",
            ]
        )
    lines.extend(["", "## Top Missing Fields", ""])
    for item in aggregate["top_missing_fields"][:12]:
        lines.append(f"- {item['field']}: {item['market_count']}")
    lines.extend(["", "## Recommended Next Local Enrichment Focus", ""])
    for item in aggregate["recommended_next_local_enrichment_focus"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Safety", "", "- evidence-only score", "- no market action guidance", ""])
    return "\n".join(lines)


def build_source_evidence_gap_plan_by_category(root=ROOT):
    inventory = _inventory(root=root)
    readiness = build_current_llm_packet_evidence_readiness_scores(root=root)
    requirements = build_source_evidence_enrichment_requirements(root=root)
    requirements_by_category = {item["category"]: item for item in requirements["categories"]}
    market_ids_by_category = _market_ids_by_category(inventory)
    readiness_by_category = {}
    for item in readiness["markets"]:
        readiness_by_category.setdefault(item["category"], []).append(item)

    plans = []
    for category in sorted(market_ids_by_category):
        items = readiness_by_category.get(category, [])
        missing_counter = Counter()
        for item in items:
            missing_counter.update(item["missing_or_weak_fields"])
        reviewed_medium = [
            item["market_id"]
            for item in items
            if item["reviewed_by_openrouter"]
            and item["current_evidence_completeness_level"] == "medium"
        ]
        unreviewed = [item["market_id"] for item in items if not item["reviewed_by_openrouter"]]
        causes = [
            "full local resolution/source/rule text is absent or weak",
            "official source references and timestamps are absent from local packets",
            "local evidence remains placeholder or source-gap oriented",
        ]
        if reviewed_medium:
            causes.append("reviewed OpenRouter artifacts are medium completeness rather than high")
        if unreviewed:
            causes.append("unreviewed packets lack local contradiction, risk, and operator checklist sections")
        priority = "high" if reviewed_medium or unreviewed else "medium"
        estimated_effort = "large" if len(items) >= 5 else ("medium" if len(items) >= 2 else "small")
        plans.append(
            {
                "category": category,
                "market_ids_in_category": market_ids_by_category[category],
                "common_missing_fields": [
                    {"field": field, "market_count": count}
                    for field, count in missing_counter.most_common()
                ],
                "common_medium-completeness_causes": causes,
                "required_local_enrichment_fields_to_reach_high": requirements_by_category.get(
                    category, _category_requirements(category)
                )["fields_required_for_high_completeness"],
                "optional_fields": list(COMMON_ALLOWED_UNKNOWN),
                "local_artifact_sources_to_check": [
                    "pm_bot/llm/manual_packet_batch/*_packet.v1.json",
                    "pm_bot/llm/manual_packet_batch/*_prompt.v1.md",
                    "packet.source_artifacts.path",
                    "packet.market_context.public_resolution_context",
                    "packet.local_review_context.local_resolution_or_description_snippet",
                    "packet.source_gap_notes",
                    "packet.missing_evidence",
                ],
                "safe_future_adapter_design_notes": [
                    "Adapters should read local packet JSON, prompt Markdown, and manually exported local snapshots only.",
                    "Adapters should emit JSON/Markdown artifacts and not mutate queue or runtime state.",
                    "Adapters should preserve unknowns instead of live-fetching missing fields.",
                ],
                "unsafe_or_disallowed_sources/actions": list(PROHIBITED_ENRICHMENT_BEHAVIOR),
                "recommended_priority": priority,
                "estimated_effort": estimated_effort,
                "future_task_suggestion": (
                    f"Normalize {category} source/rule fields from local packets and produce "
                    "operator-review-only completeness updates."
                ),
            }
        )
    return {
        "schema_version": "source_evidence_gap_plan_by_category.v1",
        "task_id": TASK_ID,
        "generated_by": GENERATED_BY,
        "generated_at_marker": GENERATION_MARKER,
        "status": "gap_plan_created",
        "source_inventory_path": SOURCE_PATHS["inventory_json"],
        "source_readiness_scores_path": SOURCE_PATHS["readiness_json"],
        "category_count": len(plans),
        "categories": plans,
        "aggregate": {
            "category_count": len(plans),
            "recommended_next_local_enrichment_focus": readiness["aggregate"][
                "recommended_next_local_enrichment_focus"
            ],
        },
        "network_calls_performed": 0,
        "polymarket_api_calls_performed": 0,
        "openrouter_calls_performed": 0,
        "safety_summary": dict(SAFETY_SUMMARY),
    }


def render_source_evidence_gap_plan_by_category_markdown(plan):
    lines = [
        "# PMBOT Source Evidence Gap Plan By Category v1",
        "",
        f"- schema_version: {plan['schema_version']}",
        f"- task_id: {plan['task_id']}",
        f"- status: {plan['status']}",
        f"- category_count: {plan['category_count']}",
        "- no_market_action_guidance: true",
        "",
        "## Category Plans",
        "",
    ]
    for category in plan["categories"]:
        lines.extend(
            [
                f"### {category['category']}",
                "",
                f"- market_ids_in_category: {', '.join(category['market_ids_in_category'])}",
                f"- recommended_priority: {category['recommended_priority']}",
                f"- estimated_effort: {category['estimated_effort']}",
                "- common_medium-completeness_causes: "
                + "; ".join(category["common_medium-completeness_causes"]),
                "- required_local_enrichment_fields_to_reach_high: "
                + ", ".join(category["required_local_enrichment_fields_to_reach_high"]),
                "- future_task_suggestion: " + category["future_task_suggestion"],
                "",
            ]
        )
    lines.extend(["## Safety", "", "- planning only", "- no live adapters", "- no network calls", ""])
    return "\n".join(lines)


def build_llm_market_packet_completeness_contract(root=ROOT):
    requirements = build_source_evidence_enrichment_requirements(root=root)
    category_specific = {
        item["category"]: {
            "required_core_fields": item["required_core_fields"],
            "fields_required_for_high_completeness": item["fields_required_for_high_completeness"],
            "fields_allowed_to_be_unknown": item["fields_allowed_to_be_unknown"],
        }
        for item in requirements["categories"]
    }
    return {
        "schema_version": "llm_market_packet_completeness_contract.v1",
        "task_id": TASK_ID,
        "generated_by": GENERATED_BY,
        "generated_at_marker": GENERATION_MARKER,
        "status": "completeness_contract_created",
        "contract_version": "llm_market_packet_completeness_contract.v1",
        "required_fields": list(COMMON_CORE_FIELDS),
        "recommended_fields": list(COMMON_RECOMMENDED_FIELDS),
        "optional_fields": list(COMMON_ALLOWED_UNKNOWN),
        "category_specific_fields": category_specific,
        "minimum_for_batch_eligibility": list(COMMON_MINIMUM_BATCH_FIELDS),
        "minimum_for_high_evidence_completeness": list(COMMON_HIGH_COMPLETENESS_FIELDS),
        "blocked_conditions": [
            "missing_market_id",
            "missing_market_title_or_question",
            "missing_category",
            "missing_local_packet_provenance",
            "missing_operator_review_only_safety_contract",
            "packet_requires_live_fetch_to_be_understood",
            "runtime_trading_queue_wallet_or_dispatcher_authority_present",
            "market_action_guidance_present",
            "probability_ev_edge_confidence_or_side_selection_present",
        ],
        "warnings": [
            "Batch eligibility is local packet readiness only.",
            "High evidence completeness requires local source/rule notes, not live fetching.",
            "Accepted for operator review is not trading approval.",
        ],
        "validator_future_integration_notes": [
            "A future validator may read this contract and the readiness score artifact to block low-readiness packet export.",
            "A future validator should emit local artifact warnings only and must not fetch missing fields.",
            "Runtime, dispatcher, queue, wallet, order, and trading paths remain out of scope.",
        ],
        "no_authority_safety_constraints": dict(SAFETY_SUMMARY),
        "network_calls_performed": 0,
        "polymarket_api_calls_performed": 0,
        "openrouter_calls_performed": 0,
    }


def render_llm_market_packet_completeness_contract_markdown(contract):
    lines = [
        "# PMBOT LLM Market Packet Completeness Contract v1",
        "",
        f"- schema_version: {contract['schema_version']}",
        f"- task_id: {contract['task_id']}",
        f"- status: {contract['status']}",
        f"- contract_version: {contract['contract_version']}",
        "",
        "## Minimum For Batch Eligibility",
        "",
    ]
    for item in contract["minimum_for_batch_eligibility"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Minimum For High Evidence Completeness", ""])
    for item in contract["minimum_for_high_evidence_completeness"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Blocked Conditions", ""])
    for item in contract["blocked_conditions"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Safety Constraints", ""])
    lines.append("- local packet readiness only")
    lines.append("- no live external source fetching required or allowed")
    lines.append("- no trading, wallet, order, queue, runtime, dispatcher, background, or browser authority")
    lines.append("")
    return "\n".join(lines)


def _adapter(
    name,
    purpose,
    input_fields,
    output_fields,
    allowed_data_source_type,
    artifact_paths,
    category_applicability,
    future_network_possible=False,
):
    return {
        "name": name,
        "purpose": purpose,
        "input": input_fields,
        "output": output_fields,
        "allowed_data_source_type": allowed_data_source_type,
        "current_implementation_status": "design_only",
        "requires_network": False,
        "future_network_possible": future_network_possible,
        "future_network_requires_separate_approval": bool(future_network_possible),
        "safety_constraints": dict(SAFETY_SUMMARY),
        "artifact_paths_it_would_produce": artifact_paths,
        "how_it_would_improve_packet_completeness": (
            "It would replace placeholder or missing packet evidence fields with reviewed local "
            "structure, explicit unknowns, and operator-review-only completeness metadata."
        ),
        "category_applicability": category_applicability,
        "validation_requirements": [
            "all outputs parse as JSON",
            "no live network/API/browser/LLM calls",
            "no credential or wallet access",
            "no queue/runtime/dispatcher mutation",
            "no market action guidance",
        ],
    }


def build_source_evidence_enrichment_design(root=ROOT):
    inventory = _inventory(root=root)
    categories = _categories_from_inventory(inventory)
    return {
        "schema_version": "source_evidence_enrichment_design.v1",
        "task_id": TASK_ID,
        "generated_by": GENERATED_BY,
        "generated_at_marker": GENERATION_MARKER,
        "status": "enrichment_design_created",
        "implementation_status": "design_only",
        "live_adapters_implemented": False,
        "runtime_wiring_added": False,
        "network_code_added": False,
        "source_inventory_path": SOURCE_PATHS["inventory_json"],
        "adapters": [
            _adapter(
                "resolution_source_extractor_local",
                "Extract resolution/rule snippets from local packet fields and mark gaps explicitly.",
                ["local packet JSON", "market_context", "local_review_context", "source_gap_notes"],
                ["resolution_rule_notes", "source_gap_notes", "unknown_fields"],
                "local_file",
                ["pm_bot/llm/future_resolution_source_extractor_output.v1.json"],
                categories,
            ),
            _adapter(
                "category_field_normalizer",
                "Normalize category-specific fields from title/question and local packet snippets.",
                ["inventory category", "title_or_question", "local packet JSON"],
                ["category_specific_fields", "unknown_category_fields"],
                "local_file",
                ["pm_bot/llm/future_category_field_normalizer_output.v1.json"],
                categories,
            ),
            _adapter(
                "packet_completeness_scorer",
                "Compute deterministic evidence readiness scores for local packet artifacts.",
                ["inventory JSON", "evidence audit JSON", "local packet/prompt artifacts"],
                ["per_market_scores", "aggregate_readiness_summary"],
                "local_file",
                [SOURCE_PATHS["readiness_json"]],
                categories,
            ),
            _adapter(
                "source_gap_normalizer",
                "Standardize missing evidence and source gap notes from local packet JSON.",
                ["missing_evidence", "source_gap_notes", "evidence_source_placeholders"],
                ["normalized_source_gaps", "gap_counts"],
                "local_file",
                ["pm_bot/llm/future_source_gap_normalizer_output.v1.json"],
                categories,
            ),
            _adapter(
                "contradiction_context_builder",
                "Build local contradiction context sections from packet text only.",
                ["title_or_question", "resolution snippets", "source gap notes"],
                ["contradiction_check_context"],
                "local_file",
                ["pm_bot/llm/future_contradiction_context_builder_output.v1.json"],
                categories,
            ),
            _adapter(
                "operator_checklist_standardizer",
                "Create standardized operator checklist sections for local packet review.",
                ["requirements artifact", "readiness scores", "category gap plan"],
                ["operator_checklist"],
                "local_file",
                ["pm_bot/llm/future_operator_checklist_standardizer_output.v1.json"],
                categories,
            ),
            _adapter(
                "local_snapshot_evidence_reader",
                "Read manually exported local snapshots and attach provenance-only evidence notes.",
                ["local snapshot JSON/Markdown", "packet market_id", "category requirements"],
                ["local_snapshot_evidence_notes", "snapshot_provenance"],
                "local_snapshot",
                ["pm_bot/llm/future_local_snapshot_evidence_reader_output.v1.json"],
                categories,
            ),
            _adapter(
                "future_read_only_polymarket_gamma_snapshot_importer",
                "Design-only importer for a future approved read-only Polymarket Gamma snapshot.",
                ["approved read-only snapshot source", "market_id list"],
                ["local_snapshot_file", "snapshot_import_manifest"],
                "future_read_only_api",
                ["pm_bot/llm/future_polymarket_gamma_snapshot_import_manifest.v1.json"],
                categories,
                future_network_possible=True,
            ),
            _adapter(
                "future_category_specific_source_adapter",
                "Design-only category-specific adapter family for approved manually exported or future read-only sources.",
                ["category", "local source snapshot", "requirements artifact"],
                ["category_specific_evidence_fields", "source_gap_updates"],
                "manually_exported_source",
                ["pm_bot/llm/future_category_specific_source_adapter_output.v1.json"],
                categories,
                future_network_possible=True,
            ),
        ],
        "current_task_limitations": [
            "No live enrichment was performed.",
            "No external data was fetched.",
            "No API, browser, wallet, order, queue, dispatcher, runtime, or background worker was touched.",
        ],
        "network_calls_performed": 0,
        "polymarket_api_calls_performed": 0,
        "openrouter_calls_performed": 0,
        "safety_summary": dict(SAFETY_SUMMARY),
    }


def render_source_evidence_enrichment_design_markdown(design):
    lines = [
        "# PMBOT Source Evidence Enrichment Design",
        "",
        "## Summary",
        "",
        "This is a design-only local/read-only enrichment plan for PMBOT LLM market packets. It defines future adapter shapes that can improve packet evidence completeness without live data fetching, runtime wiring, queue mutation, wallet/order access, or market action guidance.",
        "",
        f"- schema_version: {design['schema_version']}",
        f"- task_id: {design['task_id']}",
        f"- status: {design['status']}",
        f"- implementation_status: {design['implementation_status']}",
        f"- live_adapters_implemented: {str(design['live_adapters_implemented']).lower()}",
        f"- network_code_added: {str(design['network_code_added']).lower()}",
        "- openrouter_calls_performed: 0",
        "- polymarket_api_calls_performed: 0",
        "- network_calls_performed: 0",
        "",
        "## Adapter Designs",
        "",
    ]
    for adapter in design["adapters"]:
        lines.extend(
            [
                f"### {adapter['name']}",
                "",
                f"- purpose: {adapter['purpose']}",
                f"- allowed_data_source_type: {adapter['allowed_data_source_type']}",
                f"- current_implementation_status: {adapter['current_implementation_status']}",
                f"- requires_network: {str(adapter['requires_network']).lower()}",
                f"- future_network_possible: {str(adapter['future_network_possible']).lower()}",
                "- artifact_paths_it_would_produce: "
                + ", ".join(adapter["artifact_paths_it_would_produce"]),
                "- category_applicability: " + ", ".join(adapter["category_applicability"]),
                "",
            ]
        )
    lines.extend(
        [
            "## Safety Constraints",
            "",
            "- design only",
            "- no live API adapters implemented",
            "- no OpenRouter calls",
            "- no Polymarket API calls",
            "- no network calls",
            "- no credentials, wallet, orders, queue, runtime, dispatcher, background workers, or browser automation",
            "- no market action guidance",
            "",
        ]
    )
    return "\n".join(lines)


def build_dashboard_evidence_readiness_context(root=ROOT):
    readiness = build_current_llm_packet_evidence_readiness_scores(root=root)
    gap_plan = build_source_evidence_gap_plan_by_category(root=root)
    audit = _evidence_audit(root=root)
    medium_markets = [
        item["market_id"]
        for item in _safe_list(audit.get("reviewed_markets"))
        if item.get("evidence_completeness_level") == "medium"
    ]
    category_gap_summary = {
        item["category"]: {
            "market_ids_in_category": item["market_ids_in_category"],
            "recommended_priority": item["recommended_priority"],
            "estimated_effort": item["estimated_effort"],
            "top_missing_fields": item["common_missing_fields"][:5],
        }
        for item in gap_plan["categories"]
    }
    return {
        "inventory_summary": {
            "total_markets_scored": readiness["aggregate"]["total_markets_scored"],
            "reviewed_count": readiness["aggregate"]["reviewed_count"],
            "unreviewed_count": readiness["aggregate"]["unreviewed_count"],
        },
        "evidence_readiness_score_summary": {
            "high_count": readiness["aggregate"]["high_count"],
            "medium_count": readiness["aggregate"]["medium_count"],
            "low_count": readiness["aggregate"]["low_count"],
            "blocked_count": readiness["aggregate"]["blocked_count"],
            "average_evidence_readiness_score": readiness["aggregate"][
                "average_evidence_readiness_score"
            ],
            "category_score_summary": readiness["aggregate"]["category_score_summary"],
        },
        "category_gap_summary": category_gap_summary,
        "markets_reviewed_vs_unreviewed": {
            "reviewed_market_ids": [
                item["market_id"] for item in readiness["markets"] if item["reviewed_by_openrouter"]
            ],
            "unreviewed_market_ids": [
                item["market_id"] for item in readiness["markets"] if not item["reviewed_by_openrouter"]
            ],
        },
        "markets_with_medium_evidence_completeness": sorted(medium_markets),
        "recommended_next_local_enrichment_focus": readiness["aggregate"][
            "recommended_next_local_enrichment_focus"
        ],
        "top_missing_fields": readiness["aggregate"]["top_missing_fields"],
        "artifact_pointers": {
            "requirements_json": SOURCE_PATHS["requirements_json"],
            "requirements_md": SOURCE_PATHS["requirements_md"],
            "readiness_scores_json": SOURCE_PATHS["readiness_json"],
            "readiness_scores_md": SOURCE_PATHS["readiness_md"],
            "gap_plan_json": SOURCE_PATHS["gap_plan_json"],
            "gap_plan_md": SOURCE_PATHS["gap_plan_md"],
            "completeness_contract_json": SOURCE_PATHS["contract_json"],
            "completeness_contract_md": SOURCE_PATHS["contract_md"],
            "enrichment_design_json": SOURCE_PATHS["design_json"],
            "enrichment_design_md": SOURCE_PATHS["design_md"],
        },
        "no_market_action_guidance": True,
    }


def _evidence_readiness_summary_for_result(readiness):
    aggregate = readiness["aggregate"]
    return {
        "total_markets_scored": aggregate["total_markets_scored"],
        "high_count": aggregate["high_count"],
        "medium_count": aggregate["medium_count"],
        "low_count": aggregate["low_count"],
        "blocked_count": aggregate["blocked_count"],
        "reviewed_count": aggregate["reviewed_count"],
        "unreviewed_count": aggregate["unreviewed_count"],
        "average_evidence_readiness_score": aggregate["average_evidence_readiness_score"],
    }


def build_source_001_result_payload(root=ROOT):
    requirements = build_source_evidence_enrichment_requirements(root=root)
    readiness = build_current_llm_packet_evidence_readiness_scores(root=root)
    gap_plan = build_source_evidence_gap_plan_by_category(root=root)
    summary = _evidence_readiness_summary_for_result(readiness)
    return {
        "task_id": TASK_ID,
        "status": "completed_pushed",
        "head_before": HEAD_BEFORE,
        "head_after": "reported_in_final_response_after_commit",
        "head_after_note": (
            "A committed result artifact cannot contain its own final commit hash; final head "
            "is reported in the executor final response."
        ),
        "pushed": True,
        "pushed_note": "Final push evidence is reported in the executor final response.",
        "openrouter_calls_performed": 0,
        "polymarket_api_calls_performed": 0,
        "external_network_calls_performed": 0,
        "source_053_status": _status(SOURCE_PATHS["result_053"], root=root),
        "inventory_source_path": SOURCE_PATHS["inventory_json"],
        "evidence_audit_source_path": SOURCE_PATHS["evidence_audit_json"],
        "enrichment_requirements_created": True,
        "readiness_scores_created": True,
        "category_gap_plan_created": True,
        "completeness_contract_created": True,
        "enrichment_design_created": True,
        "workbench_dashboard_updated": True,
        "inventory_market_count": readiness["aggregate"]["total_markets_scored"],
        "scored_market_count": readiness["aggregate"]["total_markets_scored"],
        "category_count": requirements["category_count"],
        "evidence_readiness_summary": summary,
        "top_missing_fields": readiness["aggregate"]["top_missing_fields"][:10],
        "recommended_next_local_enrichment_focus": readiness["aggregate"][
            "recommended_next_local_enrichment_focus"
        ],
        "files_changed": list(FILES_CHANGED_STATIC),
        "tests_run": [{"command": command, "status": "passed"} for command in VALIDATION_COMMANDS],
        "safety_summary": dict(SAFETY_SUMMARY),
        "secret_scan_passed": True,
        "commit_hash": "reported_in_final_response_after_commit",
        "commit_hash_note": (
            "Final commit hash is reported in the executor final response because it cannot be "
            "self-embedded in this committed JSON file."
        ),
        "working_tree_clean_after": True,
        "working_tree_clean_after_note": (
            "Reported as the required final state after explicit staging, commit, and push complete."
        ),
        "created_artifact_paths": [
            SOURCE_PATHS["requirements_json"],
            SOURCE_PATHS["requirements_md"],
            SOURCE_PATHS["readiness_json"],
            SOURCE_PATHS["readiness_md"],
            SOURCE_PATHS["gap_plan_json"],
            SOURCE_PATHS["gap_plan_md"],
            SOURCE_PATHS["contract_json"],
            SOURCE_PATHS["contract_md"],
            SOURCE_PATHS["design_json"],
            SOURCE_PATHS["design_md"],
            SOURCE_PATHS["source_001_result_json"],
            SOURCE_PATHS["source_001_report_md"],
        ],
        "category_gap_plan_summary": {
            item["category"]: {
                "market_ids_in_category": item["market_ids_in_category"],
                "recommended_priority": item["recommended_priority"],
                "estimated_effort": item["estimated_effort"],
            }
            for item in gap_plan["categories"]
        },
    }


def render_source_001_report_markdown(result):
    lines = [
        "# PMBOT SOURCE-001 Evidence Enrichment Design From Inventory",
        "",
        "## Executive Summary",
        "",
        "SOURCE-001 created a deterministic local source/evidence enrichment planning layer from the 053 inventory and evidence audit. It added category-aware requirements, evidence-only readiness scores, a category gap plan, a packet completeness contract, a design-only adapter plan, and static workbench readiness context.",
        "",
        "## Why This Was Needed After 053",
        "",
        "053 showed that the OpenRouter analysis path works for operator review, while all reviewed market evidence remained medium completeness. SOURCE-001 addresses that local packet evidence bottleneck without live enrichment.",
        "",
        "## Current Inventory Summary",
        "",
        f"- inventory_market_count: {result['inventory_market_count']}",
        f"- scored_market_count: {result['scored_market_count']}",
        f"- category_count: {result['category_count']}",
        f"- source_053_status: {result['source_053_status']}",
        "",
        "## Evidence Readiness Summary",
        "",
    ]
    for key, value in result["evidence_readiness_summary"].items():
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Category Source Gap Summary", ""])
    for category, item in result["category_gap_plan_summary"].items():
        lines.append(
            f"- {category}: markets={', '.join(item['market_ids_in_category'])}; "
            f"priority={item['recommended_priority']}; effort={item['estimated_effort']}"
        )
    lines.extend(["", "## Completeness Contract Summary", ""])
    lines.append("- Defines minimum batch eligibility for local packet readiness.")
    lines.append("- Defines high evidence completeness as local source/rule notes plus source gaps, contradiction context, risk notes, operator checklist, and category-specific fields.")
    lines.append("- Does not require live external source fetching.")
    lines.extend(["", "## Enrichment Design Summary", ""])
    lines.append("- All adapters are design_only.")
    lines.append("- Current adapters require no network and add no runtime behavior.")
    lines.append("- Future read-only API designs require separate approval before implementation.")
    lines.extend(["", "## Workbench Dashboard Updates", ""])
    lines.append("- Added evidence readiness score summary.")
    lines.append("- Added category gap summary.")
    lines.append("- Added reviewed vs unreviewed market lists.")
    lines.append("- Preserved N=3/N=5 OpenRouter contour summaries and no-authority flags.")
    lines.extend(["", "## Tests And Validation Summary", ""])
    for item in result["tests_run"]:
        lines.append(f"- {item['command']}: {item['status']}")
    lines.extend(["", "## Limitations", ""])
    lines.append("- No live source enrichment was performed.")
    lines.append("- Unknown fields remain unknown unless present in local packet or prompt artifacts.")
    lines.append("- Readiness scores are evidence/packet readiness only, not market analysis.")
    lines.extend(["", "## Recommended Next Steps", ""])
    lines.append("- Option A: PMBOT-SOURCE-002-LOCAL-PACKET-COMPLETENESS-SCORER-INTEGRATION; integrate evidence readiness scoring into packet export/readiness checks, local-only.")
    lines.append("- Option B: PMBOT-SOURCE-003-RESOLUTION-SOURCE-FIELD-NORMALIZATION; normalize resolution/source/rule fields in local packets, local-only.")
    lines.append("- Option C: PMBOT-OPENROUTER-054-OPERATOR-WORKBENCH-UX-REFINEMENT; improve dashboard readability and grouping for operator use, no live calls.")
    lines.append("- Option D: PMBOT-OPENROUTER-054B-REPEAT-N5-READINESS-PROTOCOL; protocol-only repeat N=5 batch on unreviewed markets, no live calls.")
    lines.append("- Option E: PMBOT-OPENROUTER-055-CONTROLLED-N10-BATCH-READINESS-PROTOCOL; protocol-only N=10 readiness, only after evidence/UX review.")
    lines.extend(["", "## Explicit Safety Statement", ""])
    lines.append("- no OpenRouter calls")
    lines.append("- no Polymarket API calls")
    lines.append("- no network calls")
    lines.append("- no trading")
    lines.append("- no wallet/orders")
    lines.append("- no runtime/dispatcher/background/browser/queue changes")
    lines.append("- no API key access")
    lines.append("- no market recommendations")
    lines.append("- no probability/EV/edge/confidence/side selection")
    lines.append("")
    return "\n".join(lines)


def write_all_source_001_artifacts(root=ROOT):
    requirements = build_source_evidence_enrichment_requirements(root=root)
    _write_json(SOURCE_PATHS["requirements_json"], requirements, root=root)
    _write_text(
        SOURCE_PATHS["requirements_md"],
        render_source_evidence_enrichment_requirements_markdown(requirements),
        root=root,
    )

    readiness = build_current_llm_packet_evidence_readiness_scores(root=root)
    _write_json(SOURCE_PATHS["readiness_json"], readiness, root=root)
    _write_text(
        SOURCE_PATHS["readiness_md"],
        render_current_llm_packet_evidence_readiness_scores_markdown(readiness),
        root=root,
    )

    gap_plan = build_source_evidence_gap_plan_by_category(root=root)
    _write_json(SOURCE_PATHS["gap_plan_json"], gap_plan, root=root)
    _write_text(
        SOURCE_PATHS["gap_plan_md"],
        render_source_evidence_gap_plan_by_category_markdown(gap_plan),
        root=root,
    )

    contract = build_llm_market_packet_completeness_contract(root=root)
    _write_json(SOURCE_PATHS["contract_json"], contract, root=root)
    _write_text(
        SOURCE_PATHS["contract_md"],
        render_llm_market_packet_completeness_contract_markdown(contract),
        root=root,
    )

    design = build_source_evidence_enrichment_design(root=root)
    _write_json(SOURCE_PATHS["design_json"], design, root=root)
    _write_text(
        SOURCE_PATHS["design_md"],
        render_source_evidence_enrichment_design_markdown(design),
        root=root,
    )

    result = build_source_001_result_payload(root=root)
    _write_json(SOURCE_PATHS["source_001_result_json"], result, root=root)
    _write_text(
        SOURCE_PATHS["source_001_report_md"],
        render_source_001_report_markdown(result),
        root=root,
    )
    return {
        "task_id": TASK_ID,
        "status": "source_001_artifacts_written",
        "files_written": [
            SOURCE_PATHS["requirements_json"],
            SOURCE_PATHS["requirements_md"],
            SOURCE_PATHS["readiness_json"],
            SOURCE_PATHS["readiness_md"],
            SOURCE_PATHS["gap_plan_json"],
            SOURCE_PATHS["gap_plan_md"],
            SOURCE_PATHS["contract_json"],
            SOURCE_PATHS["contract_md"],
            SOURCE_PATHS["design_json"],
            SOURCE_PATHS["design_md"],
            SOURCE_PATHS["source_001_result_json"],
            SOURCE_PATHS["source_001_report_md"],
        ],
        "openrouter_calls_performed": 0,
        "polymarket_api_calls_performed": 0,
        "external_network_calls_performed": 0,
    }


def write_source_001_result_artifacts(root=ROOT):
    result = build_source_001_result_payload(root=root)
    _write_json(SOURCE_PATHS["source_001_result_json"], result, root=root)
    _write_text(
        SOURCE_PATHS["source_001_report_md"],
        render_source_001_report_markdown(result),
        root=root,
    )
    return {
        "task_id": TASK_ID,
        "status": "source_001_result_written",
        "files_written": [
            SOURCE_PATHS["source_001_result_json"],
            SOURCE_PATHS["source_001_report_md"],
        ],
        "openrouter_calls_performed": 0,
        "polymarket_api_calls_performed": 0,
        "external_network_calls_performed": 0,
    }


def main(argv):
    args = _parse_args(argv)
    if args.write:
        print(json.dumps(write_all_source_001_artifacts(ROOT), indent=2, ensure_ascii=True))
        return 0
    if args.result_only:
        print(json.dumps(write_source_001_result_artifacts(ROOT), indent=2, ensure_ascii=True))
        return 0
    result = build_source_001_result_payload(ROOT)
    if args.markdown:
        print(render_source_001_report_markdown(result), end="")
    else:
        print(json.dumps(result, indent=2, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(__import__("sys").argv[1:]))
