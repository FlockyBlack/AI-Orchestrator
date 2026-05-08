import argparse
import json
from pathlib import Path


TASK_ID = (
    "PMBOT-PAPERLIVE-010W-001-WEATHER-OBSERVATION-LEDGER-FIRST-RUN-NO-TRADE"
)
SCHEMA_VERSION = "paper_live_weather_observation_ledger_entry.v1"
GENERATED_BY = "pm_bot/paper_live/weather_observation_ledger_first_run.py"

ROOT = Path(__file__).resolve().parents[2]

MARKET_ID = "693869"
MARKET_CLASS = "weather"
MARKET_TITLE = (
    "Will the minimum Arctic sea ice extent this summer be less than 4m square "
    "kilometers?"
)
LOCAL_TIMESTAMP = "2026-05-08 Asia/Tbilisi"
HEAD_BEFORE = "1822fd465dfd247df203c60b228fce9c33e3e5a0"
NEXT_RECOMMENDED_ACTION = (
    "PMBOT-PAPERLIVE-010W-002-WEATHER-OUTCOME-SOURCE-MONITORING-PLAN-RUNNER-NO-TRADE"
)

DISCOVERY_DIR = "pm_bot/live_readonly/weather_market_discovery"
RAW_FETCH_PATH = f"{DISCOVERY_DIR}/weather_market_raw_fetch_010a2.v1.json"
NORMALIZED_CANDIDATE_PATH = (
    f"{DISCOVERY_DIR}/weather_market_normalized_candidate_010a2.v1.json"
)
SOURCE_CANDIDATE_PATH = (
    f"{DISCOVERY_DIR}/weather_source_capture_candidate_010a2.v1.json"
)
CHECKLIST_JSON_PATH = (
    f"{DISCOVERY_DIR}/weather_operator_review_checklist_010a2.v1.json"
)
CHECKLIST_MD_PATH = f"{DISCOVERY_DIR}/weather_operator_review_checklist_010a2.v1.md"
REFINEMENT_DIAGNOSTICS_PATH = (
    f"{DISCOVERY_DIR}/weather_discovery_refinement_diagnostics_010a2.v1.json"
)
SOURCE_QUALITY_010A2_JSON_PATH = (
    "pm_bot/llm/source_quality_observation_candidate_weather_010a2.v1.json"
)

CAPTURE_JSON_PATH = (
    "pm_bot/llm/manual_resolution_source_capture/"
    f"{MARKET_ID}_resolution_source_capture.v1.json"
)
CAPTURE_MD_PATH = (
    "pm_bot/llm/manual_resolution_source_capture/"
    f"{MARKET_ID}_resolution_source_capture.v1.md"
)
AUTOFILL_RESULT_PATH = "pm_bot/llm/weather_capture_autofill_result_010b.v1.json"
AUTOFILL_SURFACE_JSON_PATH = (
    "pm_bot/llm/weather_capture_operator_review_surface_010b.v1.json"
)
AUTOFILL_SURFACE_MD_PATH = (
    "pm_bot/llm/weather_capture_operator_review_surface_010b.v1.md"
)
SOURCE_QUALITY_CANDIDATE_JSON_PATH = (
    "pm_bot/llm/source_quality_observation_candidate_693869_010b.v1.json"
)
SOURCE_QUALITY_CANDIDATE_MD_PATH = (
    "pm_bot/llm/source_quality_observation_candidate_693869_010b.v1.md"
)

OPERATOR_SURFACE_JSON_PATH = (
    "pm_bot/llm/weather_operator_review_surface_693869_010c.v1.json"
)
OPERATOR_SURFACE_MD_PATH = (
    "pm_bot/llm/weather_operator_review_surface_693869_010c.v1.md"
)
LEDGER_CONTRACT_JSON_PATH = (
    "pm_bot/paper_live/paper_live_observation_ledger_contract.v1.json"
)
OBSERVATION_PLAN_JSON_PATH = (
    "pm_bot/paper_live/weather_observation_plan_693869_010c.v1.json"
)
OBSERVATION_PLAN_MD_PATH = (
    "pm_bot/paper_live/weather_observation_plan_693869_010c.v1.md"
)
OUTCOME_CONTRACT_JSON_PATH = (
    "pm_bot/paper_live/weather_outcome_tracking_contract_693869_010c.v1.json"
)
OUTCOME_CONTRACT_MD_PATH = (
    "pm_bot/paper_live/weather_outcome_tracking_contract_693869_010c.v1.md"
)
SOURCE_QUALITY_FLOW_JSON_PATH = (
    "pm_bot/llm/weather_source_quality_observation_flow_010c.v1.json"
)
SOURCE_QUALITY_FLOW_MD_PATH = (
    "pm_bot/llm/weather_source_quality_observation_flow_010c.v1.md"
)
PREPARATION_SUMMARY_JSON_PATH = (
    "pm_bot/paper_live/weather_paperlive_preparation_summary_693869_010c.v1.json"
)
PREPARATION_SUMMARY_MD_PATH = (
    "pm_bot/paper_live/weather_paperlive_preparation_summary_693869_010c.v1.md"
)
PREPARATION_SURFACE_JSON_PATH = (
    "pm_bot/workbench/weather_paper_live_preparation_surface_693869_010c.v1.json"
)
PREPARATION_SURFACE_MD_PATH = (
    "pm_bot/workbench/weather_paper_live_preparation_surface_693869_010c.v1.md"
)

READINESS_REPORT_PATH = "pm_bot/llm/post_capture_readiness_report.v1.json"
READINESS_GATE_PATH = "pm_bot/llm/post_capture_batch_readiness_gate.v1.json"
INGEST_RESULT_PATH = "pm_bot/llm/manual_resolution_source_capture_ingest_result.v1.json"
INGEST_OVERLAY_PATH = (
    "pm_bot/llm/manual_resolution_source_capture_ingested_overlay.v1.json"
)

LEDGER_ENTRY_JSON_PATH = (
    "pm_bot/paper_live/weather_observation_ledger_first_run_693869.v1.json"
)
LEDGER_ENTRY_MD_PATH = (
    "pm_bot/paper_live/weather_observation_ledger_first_run_693869.v1.md"
)
RUN_SUMMARY_JSON_PATH = (
    "pm_bot/paper_live/weather_observation_ledger_first_run_summary.v1.json"
)
RUN_SUMMARY_MD_PATH = (
    "pm_bot/paper_live/weather_observation_ledger_first_run_summary.v1.md"
)
SOURCE_QUALITY_PENDING_JSON_PATH = (
    "pm_bot/llm/source_quality_pending_observation_693869_weather_paperlive001.v1.json"
)
SOURCE_QUALITY_PENDING_MD_PATH = (
    "pm_bot/llm/source_quality_pending_observation_693869_weather_paperlive001.v1.md"
)
OUTCOME_PLACEHOLDER_JSON_PATH = (
    "pm_bot/paper_live/weather_outcome_reconciliation_placeholder_693869.v1.json"
)
OUTCOME_PLACEHOLDER_MD_PATH = (
    "pm_bot/paper_live/weather_outcome_reconciliation_placeholder_693869.v1.md"
)
WORKBENCH_SURFACE_JSON_PATH = (
    "pm_bot/workbench/"
    "weather_paper_live_observation_surface_693869_paperlive010w001.v1.json"
)
WORKBENCH_SURFACE_MD_PATH = (
    "pm_bot/workbench/"
    "weather_paper_live_observation_surface_693869_paperlive010w001.v1.md"
)
DOC_RESULT_JSON_PATH = "docs/PMBOT_PAPERLIVE_010W_001_RESULT.json"
DOC_RESULT_MD_PATH = (
    "docs/PMBOT_PAPERLIVE_010W_001_WEATHER_OBSERVATION_LEDGER_FIRST_RUN_NO_TRADE.md"
)


SAFETY_SUMMARY = {
    "no_market_action_guidance": True,
    "operator_review_only": True,
    "analysis_only": True,
    "local_only": True,
    "passive_context_only": True,
    "manual_review_only": True,
    "no_trading_authority": True,
    "no_execution_authority": True,
    "no_queue_authority": True,
    "no_runtime_authority": True,
    "no_wallet_or_order_authority": True,
    "no_dispatcher_authority": True,
    "no_browser_automation": True,
    "no_probability_ev_edge_confidence_side_selection": True,
    "openrouter_calls_performed": 0,
    "polymarket_api_calls_performed": 0,
    "external_network_calls_performed": 0,
    "network_calls_performed": 0,
    "authenticated_endpoints_used": False,
    "api_key_accessed": False,
    "api_key_value_printed": False,
    "api_key_value_written": False,
    "api_key_leaked": False,
    "wallet_or_private_key_accessed": False,
    "orders_created": 0,
    "simulated_trade_created": False,
    "selected_side": None,
    "stake_amount": None,
    "position_sizing_created": False,
    "outcome_checked": False,
    "outcome_known": False,
    "source_scoring_performed": False,
    "source_ranking_updated": False,
    "profit_or_pnl_recorded": False,
    "trading_profit_used_for_scoring": False,
    "queue_items_created": 0,
    "queue_state_mutated": False,
    "runtime_wiring_added": False,
    "dispatcher_changed": False,
    "background_workers_added": False,
    "browser_automation_used": False,
    "market_decisions_made": False,
    "market_action_guidance_generated": False,
    "probability_ev_edge_confidence_generated": False,
    "side_selection_generated": False,
    "canonical_packets_mutated": False,
    "ready_for_autonomous_trading": False,
}

OUTPUT_PATHS = [
    LEDGER_ENTRY_JSON_PATH,
    LEDGER_ENTRY_MD_PATH,
    RUN_SUMMARY_JSON_PATH,
    RUN_SUMMARY_MD_PATH,
    SOURCE_QUALITY_PENDING_JSON_PATH,
    SOURCE_QUALITY_PENDING_MD_PATH,
    OUTCOME_PLACEHOLDER_JSON_PATH,
    OUTCOME_PLACEHOLDER_MD_PATH,
    WORKBENCH_SURFACE_JSON_PATH,
    WORKBENCH_SURFACE_MD_PATH,
    DOC_RESULT_JSON_PATH,
    DOC_RESULT_MD_PATH,
]

ALLOWED_SOURCE_ROLES = {
    "market_metadata_source",
    "market_rules_source",
    "official_weather_source_candidate",
    "station_or_dataset_source_candidate",
    "fallback_weather_source_candidate",
    "unresolved_source",
    "local_capture_source",
    "operator_review_surface",
    "paper_live_observation_source",
}


def _parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Create the first local paper-live weather observation ledger entry."
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="Build artifacts in memory only.")
    mode.add_argument("--write", action="store_true", help="Write passive local artifacts.")
    mode.add_argument(
        "--summary-only",
        action="store_true",
        help="Print a concise summary from local artifacts without writing.",
    )
    return parser.parse_args(argv)


def _resolve(path, root=ROOT):
    value = Path(path)
    return value if value.is_absolute() else Path(root) / value


def _load_json(path, root=ROOT):
    with _resolve(path, root=root).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _load_optional_json(path, root=ROOT):
    resolved = _resolve(path, root=root)
    if not resolved.exists():
        return None
    return _load_json(path, root=root)


def _write_json(path, payload, root=ROOT):
    resolved = _resolve(path, root=root)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    resolved.write_text(
        json.dumps(payload, indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )


def _ascii(value):
    return str(value).encode("ascii", "backslashreplace").decode("ascii")


def _strip_trailing_whitespace(text):
    return "\n".join(line.rstrip() for line in str(text).splitlines())


def _write_text(path, text, root=ROOT):
    resolved = _resolve(path, root=root)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    resolved.write_text(_ascii(_strip_trailing_whitespace(text)) + "\n", encoding="utf-8")


def _safe_dict(value):
    return value if isinstance(value, dict) else {}


def _safe_list(value):
    return value if isinstance(value, list) else []


def _as_text(value):
    if value is None:
        return ""
    return str(value).strip()


def _dedupe(values):
    output = []
    seen = set()
    for value in values:
        text = _as_text(value)
        if text and text not in seen:
            output.append(text)
            seen.add(text)
    return output


def _pipeline_snapshot(root=ROOT):
    ingest = _load_optional_json(INGEST_RESULT_PATH, root=root) or {}
    readiness = _load_optional_json(READINESS_REPORT_PATH, root=root) or {}
    gate = _load_optional_json(READINESS_GATE_PATH, root=root) or {}
    preparation = _load_optional_json(PREPARATION_SUMMARY_JSON_PATH, root=root) or {}
    return {
        "real_filled_template_count": (
            readiness.get("real_filled_template_count")
            if readiness.get("real_filled_template_count") is not None
            else ingest.get("real_filled_template_count")
        ),
        "real_ingested_template_count": (
            readiness.get("real_ingested_template_count")
            if readiness.get("real_ingested_template_count") is not None
            else ingest.get("real_ingested_template_count")
        ),
        "draft_ingested_template_count": readiness.get("draft_ingested_template_count"),
        "ready_ingested_template_count": readiness.get("ready_ingested_template_count"),
        "future_live_002_allowed": gate.get("future_live_002_allowed"),
        "ready_for_autonomous_trading": bool(
            preparation.get("ready_for_autonomous_trading", False)
            or _safe_dict(preparation.get("safety_summary")).get(
                "ready_for_autonomous_trading", False
            )
        ),
        "canonical_packets_mutated": bool(
            readiness.get("canonical_packets_mutated")
            or gate.get("canonical_packets_mutated")
            or ingest.get("canonical_packets_mutated")
        ),
    }


def _load_inputs(root=ROOT):
    return {
        "raw_fetch": _load_json(RAW_FETCH_PATH, root=root),
        "normalized": _load_json(NORMALIZED_CANDIDATE_PATH, root=root),
        "source_candidate": _load_json(SOURCE_CANDIDATE_PATH, root=root),
        "capture": _load_json(CAPTURE_JSON_PATH, root=root),
        "source_quality_candidate": _load_json(
            SOURCE_QUALITY_CANDIDATE_JSON_PATH, root=root
        ),
        "operator_surface": _load_json(OPERATOR_SURFACE_JSON_PATH, root=root),
        "ledger_contract": _load_json(LEDGER_CONTRACT_JSON_PATH, root=root),
        "observation_plan": _load_json(OBSERVATION_PLAN_JSON_PATH, root=root),
        "outcome_contract": _load_json(OUTCOME_CONTRACT_JSON_PATH, root=root),
        "source_quality_flow": _load_json(SOURCE_QUALITY_FLOW_JSON_PATH, root=root),
        "preparation_surface": _load_json(PREPARATION_SURFACE_JSON_PATH, root=root),
        "preparation_summary": _load_json(PREPARATION_SUMMARY_JSON_PATH, root=root),
    }


def _known_weather_fields(inputs):
    normalized = inputs["normalized"]
    capture = inputs["capture"]
    operator_surface = inputs["operator_surface"]
    outcome_contract = inputs["outcome_contract"]
    known = _safe_dict(operator_surface.get("known_fields"))
    return {
        "weather_metric": (
            known.get("weather_metric")
            or capture.get("weather_metric")
            or outcome_contract.get("weather_metric")
            or normalized.get("weather_metric")
        ),
        "threshold_or_condition": (
            known.get("threshold_or_condition")
            or capture.get("threshold_or_condition")
            or outcome_contract.get("threshold_or_condition")
            or normalized.get("threshold_or_condition")
        ),
        "unit": (
            known.get("unit")
            or capture.get("unit")
            or outcome_contract.get("unit")
            or normalized.get("unit")
        ),
        "date_or_time_window": (
            known.get("date_or_time_window")
            or capture.get("date_or_time_window")
            or outcome_contract.get("date_or_time_window")
            or normalized.get("date_or_time_window")
        ),
        "official_weather_source": (
            known.get("official_weather_source")
            or capture.get("official_weather_source")
            or outcome_contract.get("official_dataset_or_source")
        ),
        "official_weather_source_url": (
            known.get("official_weather_source_url")
            or capture.get("official_weather_source_url")
            or normalized.get("official_weather_source_candidate")
        ),
        "station_or_source_hierarchy": (
            known.get("station_or_source_hierarchy")
            or capture.get("station_or_source_hierarchy")
            or outcome_contract.get("station_or_source_hierarchy")
            or normalized.get("station_or_source_hierarchy")
        ),
        "fallback_source": (
            known.get("fallback_source")
            or capture.get("fallback_source_candidate")
            or normalized.get("fallback_source_candidate")
        ),
        "timezone": known.get("timezone") or capture.get("timezone") or "",
    }


def _input_references():
    return {
        "source_010a2": {
            "raw_fetch": RAW_FETCH_PATH,
            "normalized_candidate": NORMALIZED_CANDIDATE_PATH,
            "source_capture_candidate": SOURCE_CANDIDATE_PATH,
            "operator_checklist_json": CHECKLIST_JSON_PATH,
            "operator_checklist_md": CHECKLIST_MD_PATH,
            "refinement_diagnostics": REFINEMENT_DIAGNOSTICS_PATH,
            "source_quality_candidate_json": SOURCE_QUALITY_010A2_JSON_PATH,
        },
        "source_010b": {
            "manual_capture_json": CAPTURE_JSON_PATH,
            "manual_capture_md": CAPTURE_MD_PATH,
            "autofill_result_json": AUTOFILL_RESULT_PATH,
            "operator_surface_json": AUTOFILL_SURFACE_JSON_PATH,
            "operator_surface_md": AUTOFILL_SURFACE_MD_PATH,
            "source_quality_candidate_json": SOURCE_QUALITY_CANDIDATE_JSON_PATH,
            "source_quality_candidate_md": SOURCE_QUALITY_CANDIDATE_MD_PATH,
        },
        "source_010c": {
            "operator_surface_json": OPERATOR_SURFACE_JSON_PATH,
            "operator_surface_md": OPERATOR_SURFACE_MD_PATH,
            "ledger_contract_json": LEDGER_CONTRACT_JSON_PATH,
            "observation_plan_json": OBSERVATION_PLAN_JSON_PATH,
            "observation_plan_md": OBSERVATION_PLAN_MD_PATH,
            "outcome_contract_json": OUTCOME_CONTRACT_JSON_PATH,
            "outcome_contract_md": OUTCOME_CONTRACT_MD_PATH,
            "source_quality_flow_json": SOURCE_QUALITY_FLOW_JSON_PATH,
            "source_quality_flow_md": SOURCE_QUALITY_FLOW_MD_PATH,
            "preparation_summary_json": PREPARATION_SUMMARY_JSON_PATH,
            "preparation_summary_md": PREPARATION_SUMMARY_MD_PATH,
            "preparation_surface_json": PREPARATION_SURFACE_JSON_PATH,
            "preparation_surface_md": PREPARATION_SURFACE_MD_PATH,
        },
        "readiness": {
            "ingest_result": INGEST_RESULT_PATH,
            "ingested_overlay": INGEST_OVERLAY_PATH,
            "readiness_report": READINESS_REPORT_PATH,
            "readiness_gate": READINESS_GATE_PATH,
        },
    }


def _source_capture_references():
    return {
        "manual_capture_json": CAPTURE_JSON_PATH,
        "manual_capture_md": CAPTURE_MD_PATH,
        "source_capture_candidate_json": SOURCE_CANDIDATE_PATH,
        "source_quality_candidate_json": SOURCE_QUALITY_CANDIDATE_JSON_PATH,
    }


def _operator_review_references():
    return {
        "source_010a2_operator_checklist_json": CHECKLIST_JSON_PATH,
        "source_010a2_operator_checklist_md": CHECKLIST_MD_PATH,
        "source_010b_operator_surface_json": AUTOFILL_SURFACE_JSON_PATH,
        "source_010b_operator_surface_md": AUTOFILL_SURFACE_MD_PATH,
        "source_010c_operator_surface_json": OPERATOR_SURFACE_JSON_PATH,
        "source_010c_operator_surface_md": OPERATOR_SURFACE_MD_PATH,
    }


def build_observation_ledger_entry(root=ROOT):
    inputs = _load_inputs(root=root)
    normalized = inputs["normalized"]
    source_candidate = inputs["source_candidate"]
    capture = inputs["capture"]
    operator_surface = inputs["operator_surface"]
    observation_plan = inputs["observation_plan"]
    fields = _known_weather_fields(inputs)
    direct_rules_captured = bool(
        source_candidate.get("direct_rules_text_captured")
        and _as_text(source_candidate.get("full_resolution_rules"))
    )
    official_source_identified = bool(
        source_candidate.get("official_weather_source_identified")
        and fields["official_weather_source"]
    )
    hierarchy_identified = bool(
        source_candidate.get("station_or_source_hierarchy_identified")
        and fields["station_or_source_hierarchy"]
    )
    exact_time_window = fields["date_or_time_window"]
    missing_sources = _dedupe(
        [
            *observation_plan.get("missing_sources", []),
            None
            if official_source_identified
            else "official sea ice extent source is not operator-confirmed",
            None
            if hierarchy_identified
            else "exact source hierarchy is not operator-confirmed",
            "final official minimum extent value",
            "exact time window if timezone remains ambiguous",
            "Polymarket resolution status, later",
        ]
    )
    unresolved = _dedupe(
        [
            *observation_plan.get("unresolved_questions", []),
            *operator_surface.get("unresolved_source_questions", []),
            "What timezone or date basis applies to the market window?",
            "What timestamp should be attached to the future final measurement record?",
            "How should any post-publication measurement revision be documented?",
        ]
    )
    monitored_facts = [
        {
            "fact_id": "exact_market_identity",
            "status": "captured_from_local_artifacts_pending_operator_review",
            "value": {"market_id": MARKET_ID, "title_or_question": MARKET_TITLE},
            "source_reference": NORMALIZED_CANDIDATE_PATH,
        },
        {
            "fact_id": "arctic_sea_ice_extent_metric",
            "status": "captured_from_local_artifacts_pending_operator_review",
            "value": fields["weather_metric"],
            "source_reference": CAPTURE_JSON_PATH,
        },
        {
            "fact_id": "minimum_extent_value",
            "status": "pending_future_outcome_review",
            "value": None,
            "source_reference": OUTCOME_PLACEHOLDER_JSON_PATH,
        },
        {
            "fact_id": "threshold_less_than_4_million_square_kilometers",
            "status": "captured_from_local_artifacts_pending_operator_review",
            "value": fields["threshold_or_condition"],
            "source_reference": CAPTURE_JSON_PATH,
        },
        {
            "fact_id": "unit_million_square_kilometers",
            "status": "captured_from_local_artifacts_pending_operator_review",
            "value": fields["unit"],
            "source_reference": CAPTURE_JSON_PATH,
        },
        {
            "fact_id": "relevant_summer_time_window",
            "status": "captured_from_local_artifacts_timezone_pending_operator_review",
            "value": exact_time_window,
            "source_reference": OUTCOME_CONTRACT_JSON_PATH,
        },
        {
            "fact_id": "official_dataset_source_candidate",
            "status": "candidate_from_stored_metadata_pending_operator_review",
            "value": {
                "source": fields["official_weather_source"],
                "url_or_reference": fields["official_weather_source_url"],
            },
            "source_reference": SOURCE_CANDIDATE_PATH,
        },
        {
            "fact_id": "station_dataset_source_hierarchy",
            "status": "candidate_from_stored_metadata_pending_operator_review",
            "value": fields["station_or_source_hierarchy"],
            "source_reference": OUTCOME_CONTRACT_JSON_PATH,
        },
        {
            "fact_id": "final_official_minimum_extent_value",
            "status": "pending_future_outcome_review",
            "value": None,
            "source_reference": OUTCOME_PLACEHOLDER_JSON_PATH,
        },
        {
            "fact_id": "polymarket_exact_rules_description_completeness",
            "status": (
                "captured_from_source_010a2_local_metadata_pending_operator_review"
                if direct_rules_captured
                else "missing"
            ),
            "value": bool(direct_rules_captured),
            "source_reference": SOURCE_CANDIDATE_PATH,
        },
        {
            "fact_id": "measurement_publication_timing",
            "status": "captured_from_rules_text_pending_operator_review",
            "value": "data published for October 1, 2026 before resolution timing",
            "source_reference": SOURCE_CANDIDATE_PATH,
        },
        {
            "fact_id": "measurement_revision_risk",
            "status": "captured_from_rules_text_pending_operator_review",
            "value": (
                "stored rules say revisions recorded after data is published for "
                "October 1, 2026 are not considered"
            ),
            "source_reference": SOURCE_CANDIDATE_PATH,
        },
    ]
    required_sources = [
        {
            "source_role": "market_metadata_source",
            "status": "available_from_source_010a2_local_artifact",
            "reference": NORMALIZED_CANDIDATE_PATH,
            "notes": "Stored public read-only Polymarket/Gamma metadata from SOURCE-010A2.",
        },
        {
            "source_role": "market_rules_source",
            "status": "available_from_source_010a2_local_artifact_pending_operator_review",
            "reference": SOURCE_CANDIDATE_PATH,
            "notes": "Stored rules and description text are present but capture remains draft.",
        },
        {
            "source_role": "official_weather_source_candidate",
            "status": "candidate_available_from_stored_metadata_pending_operator_review",
            "reference": fields["official_weather_source_url"],
            "notes": fields["official_weather_source"],
        },
        {
            "source_role": "station_or_dataset_source_candidate",
            "status": "candidate_available_from_stored_metadata_pending_operator_review",
            "reference": fields["station_or_source_hierarchy"],
            "notes": "Operator must verify the dataset and tab hierarchy before any promotion.",
        },
        {
            "source_role": "fallback_weather_source_candidate",
            "status": "generic_clause_available_pending_operator_review",
            "reference": fields["fallback_source"],
            "notes": "Fallback can only be reviewed if the named source later becomes unavailable.",
        },
        {
            "source_role": "local_capture_source",
            "status": "available_draft",
            "reference": CAPTURE_JSON_PATH,
            "notes": "Manual source capture remains draft.",
        },
        {
            "source_role": "operator_review_surface",
            "status": "available_operator_review_required",
            "reference": OPERATOR_SURFACE_JSON_PATH,
            "notes": "SOURCE-010C consolidated operator surface remains unchecked.",
        },
    ]
    next_operator_actions = [
        "Review the paper-live weather observation ledger entry.",
        "Verify exact stored Polymarket/Gamma rules text against approved local evidence.",
        "Verify NSIDC source identity, Sea Ice Index Daily Extent dataset, and NH-Daily-Extent tab.",
        "Record the exact time window basis before future outcome reconciliation.",
        "Keep outcome reconciliation pending until final official measurement evidence exists.",
    ]
    return {
        "schema_version": SCHEMA_VERSION,
        "task_id": TASK_ID,
        "generated_by": GENERATED_BY,
        "generated_at_marker": LOCAL_TIMESTAMP,
        "market_id": MARKET_ID,
        "market_class": MARKET_CLASS,
        "title_or_question": normalized.get("title_or_question") or MARKET_TITLE,
        "observation_mode": "source_and_weather_outcome_tracking_only",
        "paper_live_mode": "observation_only",
        "observation_status": "created",
        "source_capture_status": "draft",
        "capture_status": capture.get("capture_status", "draft"),
        "operator_review_required": True,
        "ready_for_simulated_decision": False,
        "simulated_trade_created": False,
        "selected_side": None,
        "stake_amount": None,
        "order_created": False,
        "wallet_used": False,
        "position_sizing_created": False,
        "outcome_checked": False,
        "outcome_known": False,
        "source_scoring_performed": False,
        "source_ranking_updated": False,
        "market_action_guidance_generated": False,
        "probability_ev_edge_confidence_generated": False,
        "side_selection_generated": False,
        "ready_for_autonomous_trading": False,
        "monitored_facts": monitored_facts,
        "required_sources": required_sources,
        "missing_sources": missing_sources,
        "unresolved_questions": unresolved,
        "source_capture_references": _source_capture_references(),
        "operator_review_references": _operator_review_references(),
        "weather_outcome_tracking_contract_reference": OUTCOME_CONTRACT_JSON_PATH,
        "outcome_tracking_contract_reference": OUTCOME_CONTRACT_JSON_PATH,
        "source_quality_tracking_reference": SOURCE_QUALITY_PENDING_JSON_PATH,
        "future_reconciliation_required": True,
        "future_reconciliation_placeholder_reference": OUTCOME_PLACEHOLDER_JSON_PATH,
        "next_operator_actions": next_operator_actions,
        "input_artifact_references": _input_references(),
        "pipeline_snapshot": _pipeline_snapshot(root=root),
        "safety_summary": dict(SAFETY_SUMMARY),
        "openrouter_calls_performed": 0,
        "polymarket_api_calls_performed": 0,
        "external_network_calls_performed": 0,
        "network_calls_performed": 0,
        "canonical_packets_mutated": False,
    }


def render_ledger_markdown(entry):
    lines = [
        "# PMBOT PAPERLIVE-010W-001 Weather Observation Ledger Entry",
        "",
        f"- task_id: {entry['task_id']}",
        f"- schema_version: {entry['schema_version']}",
        f"- market_id: {entry['market_id']}",
        f"- market_class: {entry['market_class']}",
        f"- title_or_question: {entry['title_or_question']}",
        f"- observation_mode: {entry['observation_mode']}",
        f"- paper_live_mode: {entry['paper_live_mode']}",
        f"- observation_status: {entry['observation_status']}",
        f"- source_capture_status: {entry['source_capture_status']}",
        "- operator_review_required: true",
        "- ready_for_simulated_decision: false",
        "- simulated_trade_created: false",
        "- selected_side: null",
        "- stake_amount: null",
        "- order_created: false",
        "- wallet_used: false",
        "- position_sizing_created: false",
        "- outcome_checked: false",
        "- outcome_known: false",
        "- source_scoring_performed: false",
        "- source_ranking_updated: false",
        "- market_action_guidance_generated: false",
        "- probability_ev_edge_confidence_generated: false",
        "- side_selection_generated: false",
        "",
        "## Monitored Facts",
        "",
    ]
    for item in entry["monitored_facts"]:
        lines.append(
            f"- {item['fact_id']}: {item['status']} "
            f"(source: {item['source_reference']})"
        )
    lines.extend(["", "## Required Sources", ""])
    for item in entry["required_sources"]:
        lines.append(
            f"- {item['source_role']}: {item['status']} "
            f"(reference: {item['reference']})"
        )
    lines.extend(["", "## Missing Sources", ""])
    for item in entry["missing_sources"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Unresolved Questions", ""])
    for item in entry["unresolved_questions"]:
        lines.append(f"- {item}")
    lines.extend(["", "## References", ""])
    lines.append(
        "- weather_outcome_tracking_contract_reference: "
        f"{entry['weather_outcome_tracking_contract_reference']}"
    )
    lines.append(
        f"- source_quality_tracking_reference: {entry['source_quality_tracking_reference']}"
    )
    lines.append(
        "- future_reconciliation_placeholder_reference: "
        f"{entry['future_reconciliation_placeholder_reference']}"
    )
    lines.extend(["", "## Next Operator Actions", ""])
    for item in entry["next_operator_actions"]:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## Safety Summary",
            "",
            "- local-only observation ledger entry",
            "- operator review only",
            "- analysis only",
            "- no market action guidance",
            "- no trading authority",
            "- no execution authority",
            "- no queue authority",
            "- no runtime authority",
            "- no wallet or order authority",
            "- no dispatcher authority",
            "- no browser automation",
            "- no probability, EV, edge, confidence, or side selection generated",
            "- no OpenRouter calls",
            "- no Polymarket API calls",
            "- no external network calls",
            "- no canonical packet mutation",
            "",
        ]
    )
    return "\n".join(lines)


def _normalize_source_role(role):
    if role == "station_or_measurement_source_candidate":
        return "station_or_dataset_source_candidate"
    if role == "official_result_source_candidate":
        return "official_weather_source_candidate"
    if role == "fallback_credible_result_source":
        return "fallback_weather_source_candidate"
    return role


def build_source_quality_pending_observation(root=ROOT):
    inputs = _load_inputs(root=root)
    candidate = inputs["source_quality_candidate"]
    source_roles = []
    for item in _safe_list(candidate.get("source_roles")):
        roles = []
        for role in _safe_list(item.get("roles")):
            normalized_role = _normalize_source_role(role)
            if normalized_role in ALLOWED_SOURCE_ROLES:
                roles.append(normalized_role)
        if roles:
            source_roles.append({"source_id": item.get("source_id"), "roles": _dedupe(roles)})
    source_roles.extend(
        [
            {
                "source_id": CAPTURE_JSON_PATH,
                "roles": ["local_capture_source"],
            },
            {
                "source_id": OPERATOR_SURFACE_JSON_PATH,
                "roles": ["operator_review_surface"],
            },
            {
                "source_id": LEDGER_ENTRY_JSON_PATH,
                "roles": ["paper_live_observation_source"],
            },
        ]
    )
    source_ids = _dedupe(
        [
            *candidate.get("source_ids_observed", []),
            CAPTURE_JSON_PATH,
            OPERATOR_SURFACE_JSON_PATH,
            LEDGER_ENTRY_JSON_PATH,
        ]
    )
    roles_observed = _dedupe(
        role for item in source_roles for role in _safe_list(item.get("roles"))
    )
    return {
        "schema_version": "source_quality_pending_observation_weather_paperlive001.v1",
        "task_id": TASK_ID,
        "generated_by": GENERATED_BY,
        "market_id": MARKET_ID,
        "market_class": MARKET_CLASS,
        "observation_ledger_entry_path": LEDGER_ENTRY_JSON_PATH,
        "source_quality_candidate_reference": SOURCE_QUALITY_CANDIDATE_JSON_PATH,
        "source_quality_flow_reference": SOURCE_QUALITY_FLOW_JSON_PATH,
        "outcome_tracking_contract_reference": OUTCOME_CONTRACT_JSON_PATH,
        "source_ids_observed": source_ids,
        "source_roles_observed": roles_observed,
        "source_roles": source_roles,
        "source_quality_status": "pending_outcome_and_operator_review",
        "outcome_known": False,
        "source_scoring_performed": False,
        "source_ranking_updated": False,
        "trading_profit_used_for_scoring": False,
        "profit_or_pnl_recorded": False,
        "operator_review_required": True,
        "future_update_allowed_only_after_outcome_review": True,
        "notes": [
            "Pending observation only; no source score is assigned.",
            "Outcome is not known in PAPERLIVE-010W-001.",
            "Future update requires operator review of final weather evidence and source alignment.",
            "This record is connected to the weather paper-live observation ledger entry.",
        ],
        "safety_summary": dict(SAFETY_SUMMARY),
        "openrouter_calls_performed": 0,
        "polymarket_api_calls_performed": 0,
        "external_network_calls_performed": 0,
    }


def render_source_quality_markdown(observation):
    lines = [
        "# PMBOT PAPERLIVE-010W-001 Source Quality Pending Observation",
        "",
        f"- task_id: {observation['task_id']}",
        f"- market_id: {observation['market_id']}",
        f"- market_class: {observation['market_class']}",
        f"- observation_ledger_entry_path: {observation['observation_ledger_entry_path']}",
        f"- source_quality_status: {observation['source_quality_status']}",
        "- outcome_known: false",
        "- source_scoring_performed: false",
        "- source_ranking_updated: false",
        "- trading_profit_used_for_scoring: false",
        "- profit_or_pnl_recorded: false",
        "- operator_review_required: true",
        "- future_update_allowed_only_after_outcome_review: true",
        "",
        "## Source IDs Observed",
        "",
    ]
    for item in observation["source_ids_observed"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Source Roles Observed", ""])
    for item in observation["source_roles"]:
        lines.append(f"- {item['source_id']}: {', '.join(item['roles'])}")
    lines.extend(["", "## Notes", ""])
    for item in observation["notes"]:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## Safety Summary",
            "",
            "- pending source-quality observation only",
            "- no source scoring",
            "- no source ranking update",
            "- no profit or PnL recorded",
            "- no market action guidance",
            "- no probability, EV, edge, confidence, or side selection generated",
            "",
        ]
    )
    return "\n".join(lines)


def build_outcome_reconciliation_placeholder(root=ROOT):
    return {
        "schema_version": "weather_outcome_reconciliation_placeholder.v1",
        "task_id": TASK_ID,
        "generated_by": GENERATED_BY,
        "market_id": MARKET_ID,
        "market_class": MARKET_CLASS,
        "observation_ledger_entry_path": LEDGER_ENTRY_JSON_PATH,
        "outcome_known": False,
        "outcome_resolution_status": "pending",
        "outcome_source_required": True,
        "official_weather_source_required": True,
        "official_dataset_or_source_required": True,
        "final_measurement_required": True,
        "unit_required": True,
        "time_window_required": True,
        "reconciliation_not_performed_reason": "outcome_not_checked_in_this_task",
        "future_reconciliation_inputs_required": [
            "final official minimum Arctic sea ice extent value",
            "exact result source URL or reference",
            "measurement publication timestamp",
            "time window confirmation",
            "Polymarket resolution if available",
            "contradiction notes if any",
            "operator review notes",
        ],
        "source_alignment_review_pending": True,
        "source_quality_update_pending": True,
        "trading_profit_used_for_source_scoring": False,
        "operator_review_required": True,
        "no_market_action_guidance": True,
        "no_trading_authority": True,
        "safety_summary": dict(SAFETY_SUMMARY),
        "openrouter_calls_performed": 0,
        "polymarket_api_calls_performed": 0,
        "external_network_calls_performed": 0,
    }


def render_outcome_placeholder_markdown(placeholder):
    lines = [
        "# PMBOT PAPERLIVE-010W-001 Weather Outcome Reconciliation Placeholder",
        "",
        f"- task_id: {placeholder['task_id']}",
        f"- market_id: {placeholder['market_id']}",
        f"- market_class: {placeholder['market_class']}",
        "- outcome_known: false",
        f"- outcome_resolution_status: {placeholder['outcome_resolution_status']}",
        "- outcome_source_required: true",
        "- official_weather_source_required: true",
        "- official_dataset_or_source_required: true",
        "- final_measurement_required: true",
        "- unit_required: true",
        "- time_window_required: true",
        f"- reconciliation_not_performed_reason: {placeholder['reconciliation_not_performed_reason']}",
        "- source_alignment_review_pending: true",
        "- source_quality_update_pending: true",
        "- trading_profit_used_for_source_scoring: false",
        "- operator_review_required: true",
        "- no_market_action_guidance: true",
        "- no_trading_authority: true",
        "",
        "## Future Reconciliation Inputs Required",
        "",
    ]
    for item in placeholder["future_reconciliation_inputs_required"]:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## Safety Summary",
            "",
            "- outcome reconciliation is pending",
            "- no outcome is resolved in this task",
            "- no market action guidance",
            "- no trading authority",
            "- no profit-based source scoring",
            "",
        ]
    )
    return "\n".join(lines)


def build_workbench_surface(root=ROOT):
    return {
        "schema_version": "weather_paper_live_observation_surface_paperlive010w001.v1",
        "task_id": TASK_ID,
        "generated_by": GENERATED_BY,
        "market_id": MARKET_ID,
        "market_class": MARKET_CLASS,
        "observation_ledger_entry_available": True,
        "observation_ledger_entry_path": LEDGER_ENTRY_JSON_PATH,
        "source_quality_pending_observation_available": True,
        "source_quality_pending_observation_path": SOURCE_QUALITY_PENDING_JSON_PATH,
        "outcome_reconciliation_placeholder_available": True,
        "outcome_reconciliation_placeholder_path": OUTCOME_PLACEHOLDER_JSON_PATH,
        "operator_review_required": True,
        "simulated_trade_created": False,
        "selected_side": None,
        "stake_amount": None,
        "outcome_checked": False,
        "outcome_known": False,
        "next_operator_actions": [
            "Review the weather paper-live observation ledger entry.",
            "Verify source capture, NSIDC source, dataset hierarchy, and time window basis.",
            "Keep future reconciliation pending until official measurement evidence is reviewed.",
        ],
        "no_market_action_guidance": True,
        "no_trading_authority": True,
        "no_execution_authority": True,
        "queue_mutated": False,
        "runtime_wiring_changed": False,
        "dispatcher_changed": False,
        "background_worker_created": False,
        "browser_automation_used": False,
        "canonical_packets_mutated": False,
        "safety_summary": dict(SAFETY_SUMMARY),
        "openrouter_calls_performed": 0,
        "polymarket_api_calls_performed": 0,
        "external_network_calls_performed": 0,
    }


def render_workbench_markdown(surface):
    lines = [
        "# PMBOT PAPERLIVE-010W-001 Passive Weather Observation Surface",
        "",
        f"- task_id: {surface['task_id']}",
        f"- market_id: {surface['market_id']}",
        f"- market_class: {surface['market_class']}",
        "- observation_ledger_entry_available: true",
        "- source_quality_pending_observation_available: true",
        "- outcome_reconciliation_placeholder_available: true",
        "- operator_review_required: true",
        "- simulated_trade_created: false",
        "- selected_side: null",
        "- stake_amount: null",
        "- outcome_checked: false",
        "- outcome_known: false",
        "- no_market_action_guidance: true",
        "- no_trading_authority: true",
        "",
        "## Artifact Paths",
        "",
        f"- observation_ledger_entry_path: {surface['observation_ledger_entry_path']}",
        f"- source_quality_pending_observation_path: {surface['source_quality_pending_observation_path']}",
        f"- outcome_reconciliation_placeholder_path: {surface['outcome_reconciliation_placeholder_path']}",
        "",
        "## Next Operator Actions",
        "",
    ]
    for item in surface["next_operator_actions"]:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## Safety Summary",
            "",
            "- passive workbench surface only",
            "- no queue mutation",
            "- no runtime wiring change",
            "- no dispatcher change",
            "- no market action guidance",
            "- no trading authority",
            "",
        ]
    )
    return "\n".join(lines)


def build_run_summary(root=ROOT, artifacts_created=False):
    pipeline = _pipeline_snapshot(root=root)
    return {
        "schema_version": "weather_observation_ledger_first_run_summary.v1",
        "task_id": TASK_ID,
        "generated_by": GENERATED_BY,
        "status": "completed_local" if artifacts_created else "dry_run_no_write",
        "market_id": MARKET_ID,
        "market_class": MARKET_CLASS,
        "observation_entries_created_count": 1 if artifacts_created else 0,
        "simulated_trades_created_count": 0,
        "orders_created_count": 0,
        "selected_side_count": 0,
        "stake_amount_count": 0,
        "source_quality_pending_observations_created_count": (
            1 if artifacts_created else 0
        ),
        "outcome_reconciliation_placeholders_created_count": 1 if artifacts_created else 0,
        "operator_review_required_count": 1,
        "no_market_action_guidance": True,
        "safety_summary": dict(SAFETY_SUMMARY),
        "pipeline_snapshot": pipeline,
        "real_ingested_template_count_preserved_or_after": pipeline.get(
            "real_ingested_template_count"
        ),
        "draft_ingested_template_count_preserved_or_after": pipeline.get(
            "draft_ingested_template_count"
        ),
        "ready_ingested_template_count_after": pipeline.get(
            "ready_ingested_template_count"
        ),
        "future_live_002_allowed": pipeline.get("future_live_002_allowed"),
        "ready_for_autonomous_trading": False,
        "next_recommended_action": NEXT_RECOMMENDED_ACTION,
        "openrouter_calls_performed": 0,
        "polymarket_api_calls_performed": 0,
        "external_network_calls_performed": 0,
        "network_calls_performed": 0,
        "canonical_packets_mutated": False,
    }


def render_run_summary_markdown(summary):
    lines = [
        "# PMBOT PAPERLIVE-010W-001 Weather Observation Ledger First Run Summary",
        "",
        f"- task_id: {summary['task_id']}",
        f"- status: {summary['status']}",
        f"- market_id: {summary['market_id']}",
        f"- market_class: {summary['market_class']}",
        f"- observation_entries_created_count: {summary['observation_entries_created_count']}",
        "- simulated_trades_created_count: 0",
        "- orders_created_count: 0",
        "- selected_side_count: 0",
        "- stake_amount_count: 0",
        (
            "- source_quality_pending_observations_created_count: "
            f"{summary['source_quality_pending_observations_created_count']}"
        ),
        (
            "- outcome_reconciliation_placeholders_created_count: "
            f"{summary['outcome_reconciliation_placeholders_created_count']}"
        ),
        f"- operator_review_required_count: {summary['operator_review_required_count']}",
        "- no_market_action_guidance: true",
        "",
        "## Preserved Readiness Counts",
        "",
        (
            "- real_ingested_template_count_preserved_or_after: "
            f"{summary['real_ingested_template_count_preserved_or_after']}"
        ),
        (
            "- draft_ingested_template_count_preserved_or_after: "
            f"{summary['draft_ingested_template_count_preserved_or_after']}"
        ),
        f"- ready_ingested_template_count_after: {summary['ready_ingested_template_count_after']}",
        f"- future_live_002_allowed: {str(summary['future_live_002_allowed']).lower()}",
        "- ready_for_autonomous_trading: false",
        "",
        "## Safety Summary",
        "",
        "- local-only",
        "- no OpenRouter calls",
        "- no Polymarket API calls",
        "- no external network calls",
        "- no authenticated endpoints",
        "- no wallet or private key access",
        "- no orders",
        "- no simulated trade",
        "- no selected side",
        "- no stake",
        "- no probability, EV, edge, or confidence computation",
        "- no runtime, dispatcher, background worker, browser, or queue changes",
        "- no canonical packet mutation",
        "",
        "## Next Recommended Action",
        "",
        f"`{summary['next_recommended_action']}`",
        "",
    ]
    return "\n".join(lines)


def build_docs_result(root=ROOT, artifacts_created=True):
    summary = build_run_summary(root=root, artifacts_created=artifacts_created)
    return {
        "task_id": TASK_ID,
        "status": "completed_local_validation_pending_commit",
        "head_before": HEAD_BEFORE,
        "head_after": "reported_in_final_response_after_commit",
        "pushed": False,
        "openrouter_calls_performed": 0,
        "polymarket_api_calls_performed": 0,
        "external_network_calls_performed": 0,
        "authenticated_endpoints_used": False,
        "wallet_or_private_key_accessed": False,
        "orders_created": False,
        "simulated_trade_created": False,
        "selected_side": None,
        "stake_amount": None,
        "position_sizing_created": False,
        "outcome_checked": False,
        "outcome_known": False,
        "trading_runtime_changed": False,
        "dispatcher_changed": False,
        "background_worker_created": False,
        "queue_mutated": False,
        "browser_automation_used": False,
        "canonical_packets_mutated": False,
        "market_action_guidance_generated": False,
        "probability_ev_edge_confidence_generated": False,
        "side_selection_generated": False,
        "profit_or_pnl_recorded": False,
        "source_scoring_performed": False,
        "source_ranking_updated": False,
        "ready_for_autonomous_trading": False,
        "market_id": MARKET_ID,
        "market_class": MARKET_CLASS,
        "observation_ledger_entry_created": artifacts_created,
        "source_quality_pending_observation_created": artifacts_created,
        "outcome_reconciliation_placeholder_created": artifacts_created,
        "passive_workbench_surface_created": artifacts_created,
        "observation_entries_created_count": (
            summary["observation_entries_created_count"]
        ),
        "real_ingested_template_count_preserved_or_after": summary[
            "real_ingested_template_count_preserved_or_after"
        ],
        "draft_ingested_template_count_preserved_or_after": summary[
            "draft_ingested_template_count_preserved_or_after"
        ],
        "ready_ingested_template_count_after": summary[
            "ready_ingested_template_count_after"
        ],
        "future_live_002_allowed": summary["future_live_002_allowed"],
        "tests_run": [],
        "files_created": OUTPUT_PATHS,
        "files_modified": [],
        "next_recommended_action": summary["next_recommended_action"],
        "safety_summary": dict(SAFETY_SUMMARY),
    }


def render_docs_markdown(result):
    return "\n".join(
        [
            "# PMBOT PAPERLIVE-010W-001 Weather Observation Ledger First Run No Trade",
            "",
            "PAPERLIVE-010W-001 is local-only. It creates the first weather paper-live observation ledger entry for market `693869` using stored SOURCE-010A2, SOURCE-010B, and SOURCE-010C artifacts.",
            "",
            "## Outcome",
            "",
            f"- market_id: {result['market_id']}",
            f"- market_class: {result['market_class']}",
            f"- observation_ledger_entry_created: {str(result['observation_ledger_entry_created']).lower()}",
            f"- source_quality_pending_observation_created: {str(result['source_quality_pending_observation_created']).lower()}",
            f"- outcome_reconciliation_placeholder_created: {str(result['outcome_reconciliation_placeholder_created']).lower()}",
            f"- passive_workbench_surface_created: {str(result['passive_workbench_surface_created']).lower()}",
            "- operator_review_required: true",
            f"- real_ingested_template_count_preserved_or_after: {result['real_ingested_template_count_preserved_or_after']}",
            f"- draft_ingested_template_count_preserved_or_after: {result['draft_ingested_template_count_preserved_or_after']}",
            f"- ready_ingested_template_count_after: {result['ready_ingested_template_count_after']}",
            f"- future_live_002_allowed: {str(result['future_live_002_allowed']).lower()}",
            "- ready_for_autonomous_trading: false",
            "",
            "## Boundary",
            "",
            "- It does not check the outcome.",
            "- It does not create a simulated trade.",
            "- It does not choose a side.",
            "- It does not create a stake.",
            "- It does not compute probability, EV, edge, or confidence.",
            "- It does not create orders.",
            "- It does not use a wallet.",
            "- It does not mutate runtime, queue, dispatcher, or canonical packets.",
            "- Source quality observation is pending, not scored.",
            "- Outcome reconciliation is pending, not resolved.",
            "- Operator review is still required.",
            "",
            "## Safety Summary",
            "",
            "- no OpenRouter calls",
            "- no Polymarket API calls",
            "- no external network calls",
            "- no authenticated endpoints",
            "- no wallet or private key access",
            "- no orders",
            "- no simulated trade",
            "- no selected side",
            "- no stake",
            "- no source scoring",
            "- no source ranking update",
            "- no runtime, dispatcher, background worker, browser, or queue changes",
            "- no canonical packet mutation",
            "",
            "## Next Recommended Action",
            "",
            f"`{result['next_recommended_action']}`",
            "",
        ]
    )


def write_artifacts(root=ROOT):
    ledger = build_observation_ledger_entry(root=root)
    source_quality = build_source_quality_pending_observation(root=root)
    outcome = build_outcome_reconciliation_placeholder(root=root)
    workbench = build_workbench_surface(root=root)
    summary = build_run_summary(root=root, artifacts_created=True)
    docs_result = build_docs_result(root=root, artifacts_created=True)

    _write_json(LEDGER_ENTRY_JSON_PATH, ledger, root=root)
    _write_text(LEDGER_ENTRY_MD_PATH, render_ledger_markdown(ledger), root=root)
    _write_json(SOURCE_QUALITY_PENDING_JSON_PATH, source_quality, root=root)
    _write_text(
        SOURCE_QUALITY_PENDING_MD_PATH,
        render_source_quality_markdown(source_quality),
        root=root,
    )
    _write_json(OUTCOME_PLACEHOLDER_JSON_PATH, outcome, root=root)
    _write_text(
        OUTCOME_PLACEHOLDER_MD_PATH,
        render_outcome_placeholder_markdown(outcome),
        root=root,
    )
    _write_json(WORKBENCH_SURFACE_JSON_PATH, workbench, root=root)
    _write_text(WORKBENCH_SURFACE_MD_PATH, render_workbench_markdown(workbench), root=root)
    _write_json(RUN_SUMMARY_JSON_PATH, summary, root=root)
    _write_text(RUN_SUMMARY_MD_PATH, render_run_summary_markdown(summary), root=root)
    _write_json(DOC_RESULT_JSON_PATH, docs_result, root=root)
    _write_text(DOC_RESULT_MD_PATH, render_docs_markdown(docs_result), root=root)
    return summary


def build_dry_run(root=ROOT):
    ledger = build_observation_ledger_entry(root=root)
    summary = build_run_summary(root=root, artifacts_created=False)
    return {
        "schema_version": "weather_observation_ledger_first_run_dry_run.v1",
        "task_id": TASK_ID,
        "status": "dry_run_no_write",
        "dry_run": True,
        "market_id": MARKET_ID,
        "market_class": MARKET_CLASS,
        "planned_observation_entry_path": LEDGER_ENTRY_JSON_PATH,
        "planned_source_quality_pending_observation_path": SOURCE_QUALITY_PENDING_JSON_PATH,
        "planned_outcome_reconciliation_placeholder_path": OUTCOME_PLACEHOLDER_JSON_PATH,
        "planned_workbench_surface_path": WORKBENCH_SURFACE_JSON_PATH,
        "observation_mode": ledger["observation_mode"],
        "paper_live_mode": ledger["paper_live_mode"],
        "simulated_trade_created": False,
        "selected_side": None,
        "stake_amount": None,
        "order_created": False,
        "wallet_used": False,
        "outcome_checked": False,
        "outcome_known": False,
        "files_written": [],
        "summary": summary,
        "safety_summary": dict(SAFETY_SUMMARY),
        "openrouter_calls_performed": 0,
        "polymarket_api_calls_performed": 0,
        "external_network_calls_performed": 0,
    }


def build_summary_only(root=ROOT):
    summary = _load_optional_json(RUN_SUMMARY_JSON_PATH, root=root)
    ledger = _load_optional_json(LEDGER_ENTRY_JSON_PATH, root=root)
    source_quality = _load_optional_json(SOURCE_QUALITY_PENDING_JSON_PATH, root=root)
    outcome = _load_optional_json(OUTCOME_PLACEHOLDER_JSON_PATH, root=root)
    workbench = _load_optional_json(WORKBENCH_SURFACE_JSON_PATH, root=root)
    pipeline = _pipeline_snapshot(root=root)
    return {
        "schema_version": "weather_observation_ledger_first_run_summary_only.v1",
        "task_id": TASK_ID,
        "status": "summary_only",
        "market_id": MARKET_ID,
        "market_class": MARKET_CLASS,
        "observation_ledger_entry_exists": ledger is not None,
        "source_quality_pending_observation_exists": source_quality is not None,
        "outcome_reconciliation_placeholder_exists": outcome is not None,
        "passive_workbench_surface_exists": workbench is not None,
        "summary_exists": summary is not None,
        "observation_entries_created_count": (
            summary or {}
        ).get("observation_entries_created_count"),
        "simulated_trades_created_count": (
            summary or {}
        ).get("simulated_trades_created_count", 0),
        "orders_created_count": (summary or {}).get("orders_created_count", 0),
        "selected_side_count": (summary or {}).get("selected_side_count", 0),
        "stake_amount_count": (summary or {}).get("stake_amount_count", 0),
        "outcome_checked": (ledger or {}).get("outcome_checked", False),
        "outcome_known": (ledger or {}).get("outcome_known", False),
        "real_ingested_template_count": pipeline.get("real_ingested_template_count"),
        "draft_ingested_template_count": pipeline.get("draft_ingested_template_count"),
        "ready_ingested_template_count": pipeline.get("ready_ingested_template_count"),
        "future_live_002_allowed": pipeline.get("future_live_002_allowed"),
        "ready_for_autonomous_trading": False,
        "openrouter_calls_performed": 0,
        "polymarket_api_calls_performed": 0,
        "external_network_calls_performed": 0,
    }


def main(argv):
    args = _parse_args(argv)
    if args.summary_only:
        payload = build_summary_only(ROOT)
    elif args.write:
        payload = write_artifacts(ROOT)
    else:
        payload = build_dry_run(ROOT)
    print(json.dumps(payload, indent=2, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(__import__("sys").argv[1:]))
