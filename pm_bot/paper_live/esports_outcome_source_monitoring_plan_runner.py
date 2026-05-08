import argparse
import json
from pathlib import Path


TASK_ID = "PMBOT-PAPERLIVE-002-ESPORTS-OUTCOME-SOURCE-MONITORING-PLAN-RUNNER-NO-TRADE"
SCHEMA_VERSION = "paper_live_outcome_source_monitoring_plan.v1"
GENERATED_BY = "pm_bot/paper_live/esports_outcome_source_monitoring_plan_runner.py"

ROOT = Path(__file__).resolve().parents[2]

MARKET_ID = "1987056"
MARKET_CLASS = "esports"
MARKET_TITLE = (
    "LoL: JD Gaming vs Anyone's Legend (BO5) - Esports World Cup China Qualifier Phase 2"
)
GAME_TITLE = "League of Legends"
MATCH_FORMAT = "BO5"
LOCAL_TIMESTAMP = "2026-05-08 Asia/Tbilisi"

DISCOVERY_DIR = "pm_bot/live_readonly/esports_market_discovery"
RAW_FETCH_PATH = f"{DISCOVERY_DIR}/esports_market_raw_fetch_009a.v1.json"
NORMALIZED_CANDIDATE_PATH = (
    f"{DISCOVERY_DIR}/esports_market_normalized_candidate_009a.v1.json"
)
SOURCE_CANDIDATE_PATH = (
    f"{DISCOVERY_DIR}/esports_source_capture_candidate_009a.v1.json"
)
SOURCE_009A_CHECKLIST_JSON_PATH = (
    f"{DISCOVERY_DIR}/esports_operator_review_checklist_009a.v1.json"
)
SOURCE_009A_CHECKLIST_MD_PATH = (
    f"{DISCOVERY_DIR}/esports_operator_review_checklist_009a.v1.md"
)

CAPTURE_JSON_PATH = (
    "pm_bot/llm/manual_resolution_source_capture/"
    f"{MARKET_ID}_resolution_source_capture.v1.json"
)
CAPTURE_MD_PATH = (
    "pm_bot/llm/manual_resolution_source_capture/"
    f"{MARKET_ID}_resolution_source_capture.v1.md"
)
CAPTURE_OPERATOR_SURFACE_JSON_PATH = (
    "pm_bot/llm/esports_capture_operator_review_surface_009b.v1.json"
)
CAPTURE_OPERATOR_SURFACE_MD_PATH = (
    "pm_bot/llm/esports_capture_operator_review_surface_009b.v1.md"
)
SOURCE_QUALITY_CANDIDATE_JSON_PATH = (
    "pm_bot/llm/source_quality_observation_candidate_1987056_009b.v1.json"
)
SOURCE_QUALITY_CANDIDATE_MD_PATH = (
    "pm_bot/llm/source_quality_observation_candidate_1987056_009b.v1.md"
)

OPERATOR_SURFACE_JSON_PATH = (
    "pm_bot/llm/esports_operator_review_surface_1987056_009c.v1.json"
)
OPERATOR_SURFACE_MD_PATH = (
    "pm_bot/llm/esports_operator_review_surface_1987056_009c.v1.md"
)
OBSERVATION_PLAN_JSON_PATH = (
    "pm_bot/paper_live/esports_observation_plan_1987056_009c.v1.json"
)
OBSERVATION_PLAN_MD_PATH = (
    "pm_bot/paper_live/esports_observation_plan_1987056_009c.v1.md"
)
OUTCOME_CONTRACT_JSON_PATH = "pm_bot/paper_live/outcome_tracking_contract.v1.json"
OUTCOME_CONTRACT_MD_PATH = "pm_bot/paper_live/outcome_tracking_contract.v1.md"
SOURCE_QUALITY_FLOW_JSON_PATH = (
    "pm_bot/llm/source_quality_observation_flow_009c.v1.json"
)
SOURCE_QUALITY_FLOW_MD_PATH = "pm_bot/llm/source_quality_observation_flow_009c.v1.md"

READINESS_REPORT_PATH = "pm_bot/llm/post_capture_readiness_report.v1.json"
READINESS_GATE_PATH = "pm_bot/llm/post_capture_batch_readiness_gate.v1.json"
INGEST_RESULT_PATH = "pm_bot/llm/manual_resolution_source_capture_ingest_result.v1.json"
INGEST_OVERLAY_PATH = (
    "pm_bot/llm/manual_resolution_source_capture_ingested_overlay.v1.json"
)

PAPERLIVE001_LEDGER_JSON_PATH = (
    "pm_bot/paper_live/esports_observation_ledger_first_run_1987056.v1.json"
)
PAPERLIVE001_LEDGER_SUMMARY_JSON_PATH = (
    "pm_bot/paper_live/esports_observation_ledger_first_run_summary.v1.json"
)
PAPERLIVE001_SOURCE_QUALITY_PENDING_JSON_PATH = (
    "pm_bot/llm/source_quality_pending_observation_1987056_paperlive001.v1.json"
)
PAPERLIVE001_OUTCOME_PLACEHOLDER_JSON_PATH = (
    "pm_bot/paper_live/esports_outcome_reconciliation_placeholder_1987056.v1.json"
)
PAPERLIVE001_WORKBENCH_SURFACE_JSON_PATH = (
    "pm_bot/workbench/"
    "esports_paper_live_observation_surface_1987056_paperlive001.v1.json"
)

MONITORING_PLAN_JSON_PATH = (
    "pm_bot/paper_live/"
    "esports_outcome_source_monitoring_plan_1987056_paperlive002.v1.json"
)
MONITORING_PLAN_MD_PATH = (
    "pm_bot/paper_live/"
    "esports_outcome_source_monitoring_plan_1987056_paperlive002.v1.md"
)
CHECKLIST_JSON_PATH = (
    "pm_bot/paper_live/"
    "esports_source_monitoring_checklist_1987056_paperlive002.v1.json"
)
CHECKLIST_MD_PATH = (
    "pm_bot/paper_live/"
    "esports_source_monitoring_checklist_1987056_paperlive002.v1.md"
)
FUTURE_OUTCOME_CHECK_JSON_PATH = (
    "pm_bot/paper_live/esports_future_readonly_outcome_check_request_1987056.v1.json"
)
FUTURE_OUTCOME_CHECK_MD_PATH = (
    "pm_bot/paper_live/esports_future_readonly_outcome_check_request_1987056.v1.md"
)
SOURCE_QUALITY_UPDATE_PLAN_JSON_PATH = (
    "pm_bot/llm/source_quality_update_plan_1987056_paperlive002.v1.json"
)
SOURCE_QUALITY_UPDATE_PLAN_MD_PATH = (
    "pm_bot/llm/source_quality_update_plan_1987056_paperlive002.v1.md"
)
WORKBENCH_SURFACE_JSON_PATH = (
    "pm_bot/workbench/esports_monitoring_plan_surface_1987056_paperlive002.v1.json"
)
WORKBENCH_SURFACE_MD_PATH = (
    "pm_bot/workbench/esports_monitoring_plan_surface_1987056_paperlive002.v1.md"
)
RUN_SUMMARY_JSON_PATH = (
    "pm_bot/paper_live/esports_outcome_source_monitoring_plan_runner_summary.v1.json"
)
RUN_SUMMARY_MD_PATH = (
    "pm_bot/paper_live/esports_outcome_source_monitoring_plan_runner_summary.v1.md"
)
DOC_RESULT_JSON_PATH = "docs/PMBOT_PAPERLIVE_002_RESULT.json"
DOC_RESULT_MD_PATH = (
    "docs/PMBOT_PAPERLIVE_002_ESPORTS_OUTCOME_SOURCE_MONITORING_PLAN_RUNNER_NO_TRADE.md"
)

JSON_OUTPUT_PATHS = [
    MONITORING_PLAN_JSON_PATH,
    CHECKLIST_JSON_PATH,
    FUTURE_OUTCOME_CHECK_JSON_PATH,
    SOURCE_QUALITY_UPDATE_PLAN_JSON_PATH,
    WORKBENCH_SURFACE_JSON_PATH,
    RUN_SUMMARY_JSON_PATH,
    DOC_RESULT_JSON_PATH,
]

MARKDOWN_OUTPUT_PATHS = [
    MONITORING_PLAN_MD_PATH,
    CHECKLIST_MD_PATH,
    FUTURE_OUTCOME_CHECK_MD_PATH,
    SOURCE_QUALITY_UPDATE_PLAN_MD_PATH,
    WORKBENCH_SURFACE_MD_PATH,
    RUN_SUMMARY_MD_PATH,
    DOC_RESULT_MD_PATH,
]

OUTPUT_PATHS = [
    MONITORING_PLAN_JSON_PATH,
    MONITORING_PLAN_MD_PATH,
    CHECKLIST_JSON_PATH,
    CHECKLIST_MD_PATH,
    FUTURE_OUTCOME_CHECK_JSON_PATH,
    FUTURE_OUTCOME_CHECK_MD_PATH,
    SOURCE_QUALITY_UPDATE_PLAN_JSON_PATH,
    SOURCE_QUALITY_UPDATE_PLAN_MD_PATH,
    WORKBENCH_SURFACE_JSON_PATH,
    WORKBENCH_SURFACE_MD_PATH,
    RUN_SUMMARY_JSON_PATH,
    RUN_SUMMARY_MD_PATH,
    DOC_RESULT_JSON_PATH,
    DOC_RESULT_MD_PATH,
]


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
    "queue_items_created": 0,
    "queue_state_mutated": False,
    "runtime_wiring_added": False,
    "dispatcher_changed": False,
    "background_workers_added": False,
    "browser_automation_used": False,
    "market_decisions_made": False,
    "outcome_checked": False,
    "outcome_known": False,
    "source_scoring_performed": False,
    "source_ranking_updated": False,
    "profit_or_pnl_recorded": False,
    "canonical_packets_mutated": False,
}


def _parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Create a local-only esports outcome/source monitoring plan."
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


def _exists(path, root=ROOT):
    return _resolve(path, root=root).exists()


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
    return {
        "real_ingested_template_count": (
            readiness.get("real_ingested_template_count")
            if readiness.get("real_ingested_template_count") is not None
            else ingest.get("real_ingested_template_count")
        ),
        "draft_ingested_template_count": readiness.get("draft_ingested_template_count"),
        "ready_ingested_template_count": readiness.get("ready_ingested_template_count"),
        "future_live_002_allowed": gate.get("future_live_002_allowed"),
        "canonical_packets_mutated": bool(
            readiness.get("canonical_packets_mutated")
            or gate.get("canonical_packets_mutated")
            or ingest.get("canonical_packets_mutated")
        ),
    }


def _load_inputs(root=ROOT):
    return {
        "raw_fetch": _load_optional_json(RAW_FETCH_PATH, root=root) or {},
        "normalized": _load_optional_json(NORMALIZED_CANDIDATE_PATH, root=root) or {},
        "source_candidate": _load_optional_json(SOURCE_CANDIDATE_PATH, root=root) or {},
        "capture": _load_optional_json(CAPTURE_JSON_PATH, root=root) or {},
        "capture_operator_surface": (
            _load_optional_json(CAPTURE_OPERATOR_SURFACE_JSON_PATH, root=root) or {}
        ),
        "source_quality_candidate": (
            _load_optional_json(SOURCE_QUALITY_CANDIDATE_JSON_PATH, root=root) or {}
        ),
        "operator_surface": _load_optional_json(OPERATOR_SURFACE_JSON_PATH, root=root)
        or {},
        "observation_plan": _load_optional_json(OBSERVATION_PLAN_JSON_PATH, root=root)
        or {},
        "outcome_contract": _load_optional_json(OUTCOME_CONTRACT_JSON_PATH, root=root)
        or {},
        "source_quality_flow": _load_optional_json(SOURCE_QUALITY_FLOW_JSON_PATH, root=root)
        or {},
        "paperlive001_ledger": _load_optional_json(PAPERLIVE001_LEDGER_JSON_PATH, root=root)
        or {},
        "paperlive001_summary": (
            _load_optional_json(PAPERLIVE001_LEDGER_SUMMARY_JSON_PATH, root=root) or {}
        ),
        "paperlive001_source_quality": (
            _load_optional_json(PAPERLIVE001_SOURCE_QUALITY_PENDING_JSON_PATH, root=root)
            or {}
        ),
        "paperlive001_outcome": (
            _load_optional_json(PAPERLIVE001_OUTCOME_PLACEHOLDER_JSON_PATH, root=root)
            or {}
        ),
        "paperlive001_workbench": (
            _load_optional_json(PAPERLIVE001_WORKBENCH_SURFACE_JSON_PATH, root=root)
            or {}
        ),
    }


def _rules_text(source_candidate, capture):
    return (
        source_candidate.get("full_resolution_rules")
        or capture.get("resolution_rules")
        or capture.get("full_resolution_rules")
        or capture.get("rules_text")
    )


def _rules_complete(source_candidate, capture):
    return bool(
        source_candidate.get("direct_rules_text_captured")
        and _as_text(_rules_text(source_candidate, capture))
    )


def _known_fields(inputs):
    normalized = inputs["normalized"]
    operator_surface = inputs["operator_surface"]
    known = _safe_dict(operator_surface.get("known_fields"))
    source_candidate = inputs["source_candidate"]
    capture = inputs["capture"]
    rules_text = _rules_text(source_candidate, capture)
    official_source = (
        known.get("official_result_source_from_market_metadata")
        or normalized.get("resolution_source_text")
        or source_candidate.get("official_result_source")
    )
    return {
        "title_or_question": normalized.get("title_or_question") or MARKET_TITLE,
        "game_title": known.get("game_title") or normalized.get("game_title") or GAME_TITLE,
        "event_or_tournament": (
            known.get("event_or_tournament")
            or normalized.get("event_or_tournament")
            or "unknown"
        ),
        "teams_or_players": (
            known.get("teams_or_players")
            or normalized.get("teams_or_players")
            or ["JD Gaming", "Anyone's Legend"]
        ),
        "match_format": known.get("match_format") or MATCH_FORMAT,
        "scheduled_time_timezone": (
            known.get("scheduled_time_utc")
            or normalized.get("scheduled_time_if_available")
            or "unknown"
        ),
        "official_result_source_from_existing_artifacts": official_source,
        "fallback_source_rule": known.get("fallback_source_rule"),
        "exact_rules_text_present": bool(_as_text(rules_text)),
        "exact_rules_text_complete_pending_operator_review": _rules_complete(
            source_candidate, capture
        ),
        "exact_rules_text_source": SOURCE_CANDIDATE_PATH if _as_text(rules_text) else None,
        "cancellation_reschedule_forfeit_rule_present": _rules_rule_present(rules_text),
    }


def _rules_rule_present(rules_text):
    lowered = _as_text(rules_text).lower()
    required_terms = ["cancel", "delay", "forfeit"]
    return all(term in lowered for term in required_terms)


def _artifact_status(path, root=ROOT):
    return "available" if _exists(path, root=root) else "missing"


def _known_sources_from_existing_artifacts(root=ROOT):
    return [
        {
            "artifact_group": "SOURCE-009A",
            "source_role": "public_readonly_market_metadata_snapshot",
            "status": _artifact_status(NORMALIZED_CANDIDATE_PATH, root=root),
            "reference": NORMALIZED_CANDIDATE_PATH,
            "notes": "Stored local artifact from prior public read-only discovery.",
        },
        {
            "artifact_group": "SOURCE-009A",
            "source_role": "stored_market_rules_and_source_capture_candidate",
            "status": _artifact_status(SOURCE_CANDIDATE_PATH, root=root),
            "reference": SOURCE_CANDIDATE_PATH,
            "notes": "Stored local rules text and source candidate; operator review remains required.",
        },
        {
            "artifact_group": "SOURCE-009B",
            "source_role": "manual_resolution_source_capture_draft",
            "status": _artifact_status(CAPTURE_JSON_PATH, root=root),
            "reference": CAPTURE_JSON_PATH,
            "notes": "Draft manual capture, not ready or reviewed.",
        },
        {
            "artifact_group": "SOURCE-009B",
            "source_role": "capture_operator_review_surface",
            "status": _artifact_status(CAPTURE_OPERATOR_SURFACE_JSON_PATH, root=root),
            "reference": CAPTURE_OPERATOR_SURFACE_JSON_PATH,
            "notes": "Passive operator review surface.",
        },
        {
            "artifact_group": "SOURCE-009B",
            "source_role": "source_quality_observation_candidate",
            "status": _artifact_status(SOURCE_QUALITY_CANDIDATE_JSON_PATH, root=root),
            "reference": SOURCE_QUALITY_CANDIDATE_JSON_PATH,
            "notes": "Candidate only; no source scoring performed here.",
        },
        {
            "artifact_group": "SOURCE-009C",
            "source_role": "operator_review_surface",
            "status": _artifact_status(OPERATOR_SURFACE_JSON_PATH, root=root),
            "reference": OPERATOR_SURFACE_JSON_PATH,
            "notes": "Consolidated operator review surface.",
        },
        {
            "artifact_group": "SOURCE-009C",
            "source_role": "observation_plan",
            "status": _artifact_status(OBSERVATION_PLAN_JSON_PATH, root=root),
            "reference": OBSERVATION_PLAN_JSON_PATH,
            "notes": "Prior paper-live preparation plan.",
        },
        {
            "artifact_group": "SOURCE-009C",
            "source_role": "outcome_tracking_contract",
            "status": _artifact_status(OUTCOME_CONTRACT_JSON_PATH, root=root),
            "reference": OUTCOME_CONTRACT_JSON_PATH,
            "notes": "Local outcome tracking contract.",
        },
        {
            "artifact_group": "SOURCE-009C",
            "source_role": "source_quality_observation_flow",
            "status": _artifact_status(SOURCE_QUALITY_FLOW_JSON_PATH, root=root),
            "reference": SOURCE_QUALITY_FLOW_JSON_PATH,
            "notes": "Local source quality update flow; no update performed here.",
        },
        {
            "artifact_group": "PAPERLIVE-001",
            "source_role": "first_observation_ledger_entry",
            "status": _artifact_status(PAPERLIVE001_LEDGER_JSON_PATH, root=root),
            "reference": PAPERLIVE001_LEDGER_JSON_PATH,
            "notes": "Observation-only ledger entry preserved.",
        },
        {
            "artifact_group": "PAPERLIVE-001",
            "source_role": "source_quality_pending_observation",
            "status": _artifact_status(PAPERLIVE001_SOURCE_QUALITY_PENDING_JSON_PATH, root=root),
            "reference": PAPERLIVE001_SOURCE_QUALITY_PENDING_JSON_PATH,
            "notes": "Pending source quality observation; no scoring here.",
        },
        {
            "artifact_group": "PAPERLIVE-001",
            "source_role": "outcome_reconciliation_placeholder",
            "status": _artifact_status(PAPERLIVE001_OUTCOME_PLACEHOLDER_JSON_PATH, root=root),
            "reference": PAPERLIVE001_OUTCOME_PLACEHOLDER_JSON_PATH,
            "notes": "Outcome remains pending and not checked by PAPERLIVE-002.",
        },
    ]


def _monitored_facts(fields):
    return [
        {
            "fact_id": "match_identity",
            "description": "Confirm the stored market identity maps to the intended match.",
            "current_status": "known",
            "current_value": fields["title_or_question"],
            "source_reference_if_known": NORMALIZED_CANDIDATE_PATH,
            "requires_operator_review": True,
        },
        {
            "fact_id": "game_title",
            "description": "Confirm the game title.",
            "current_status": "known",
            "current_value": fields["game_title"],
            "source_reference_if_known": OPERATOR_SURFACE_JSON_PATH,
            "requires_operator_review": True,
        },
        {
            "fact_id": "tournament_identity",
            "description": "Confirm the tournament identity and phase.",
            "current_status": "known",
            "current_value": fields["event_or_tournament"],
            "source_reference_if_known": OPERATOR_SURFACE_JSON_PATH,
            "requires_operator_review": True,
        },
        {
            "fact_id": "teams_or_players_identity",
            "description": "Confirm the participant identities.",
            "current_status": "known",
            "current_value": fields["teams_or_players"],
            "source_reference_if_known": NORMALIZED_CANDIDATE_PATH,
            "requires_operator_review": True,
        },
        {
            "fact_id": "match_format",
            "description": "Confirm the match format.",
            "current_status": "known",
            "current_value": fields["match_format"],
            "source_reference_if_known": OPERATOR_SURFACE_JSON_PATH,
            "requires_operator_review": True,
        },
        {
            "fact_id": "scheduled_time_timezone",
            "description": "Confirm scheduled time and timezone.",
            "current_status": "known",
            "current_value": fields["scheduled_time_timezone"],
            "source_reference_if_known": NORMALIZED_CANDIDATE_PATH,
            "requires_operator_review": True,
        },
        {
            "fact_id": "official_result_source",
            "description": "Identify a direct official match or tournament result source later.",
            "current_status": "ambiguous",
            "current_value": fields["official_result_source_from_existing_artifacts"],
            "source_reference_if_known": OPERATOR_SURFACE_JSON_PATH,
            "requires_operator_review": True,
        },
        {
            "fact_id": "cancellation_reschedule_forfeit_handling",
            "description": "Confirm cancellation, reschedule, and forfeit rules from stored rules.",
            "current_status": (
                "known"
                if fields["cancellation_reschedule_forfeit_rule_present"]
                else "missing"
            ),
            "current_value": "stored_rules_text_review_required",
            "source_reference_if_known": fields["exact_rules_text_source"],
            "requires_operator_review": True,
        },
        {
            "fact_id": "final_match_result",
            "description": "Final result evidence for later outcome reconciliation.",
            "current_status": "pending_future_readonly_check",
            "current_value": None,
            "source_reference_if_known": None,
            "requires_operator_review": True,
        },
        {
            "fact_id": "exact_polymarket_rules_description_completeness",
            "description": "Confirm that direct market rules text is complete.",
            "current_status": (
                "ambiguous"
                if fields["exact_rules_text_complete_pending_operator_review"]
                else "missing"
            ),
            "current_value": fields["exact_rules_text_complete_pending_operator_review"],
            "source_reference_if_known": fields["exact_rules_text_source"],
            "requires_operator_review": True,
        },
        {
            "fact_id": "polymarket_resolution_status",
            "description": "Resolution status may be checked later only with explicit approval.",
            "current_status": "pending_future_readonly_check",
            "current_value": None,
            "source_reference_if_known": None,
            "requires_operator_review": True,
        },
    ]


def _missing_sources(fields):
    missing = [
        "official match/tournament result source",
        "final result source",
        "result timestamp",
        "Polymarket resolution status if available later",
    ]
    if not fields["exact_rules_text_complete_pending_operator_review"]:
        missing.append("exact direct Polymarket rules text")
    else:
        missing.append("operator-confirmed exact direct Polymarket rules text completeness")
    if not fields["cancellation_reschedule_forfeit_rule_present"]:
        missing.append("cancellation/forfeit/reschedule rule")
    else:
        missing.append("operator-confirmed cancellation/forfeit/reschedule rule handling")
    return missing


def _source_fetch_required_later():
    return [
        {
            "fetch_id": "future_public_readonly_market_resolution_status",
            "source_scope": "public read-only Polymarket/Gamma market or resolution status",
            "required": True,
            "explicit_network_approval_required": True,
            "performed_in_this_task": False,
        },
        {
            "fetch_id": "future_official_match_result_source",
            "source_scope": "official tournament or match result source if available",
            "required": True,
            "explicit_network_approval_required": True,
            "performed_in_this_task": False,
        },
        {
            "fetch_id": "future_fallback_credible_result_source",
            "source_scope": "fallback credible match result source only if official source is unavailable",
            "required": False,
            "explicit_network_approval_required": True,
            "performed_in_this_task": False,
        },
    ]


def _outcome_reconciliation_steps():
    return [
        "Obtain explicit approval before any future readonly network check.",
        "Collect official result evidence, or fallback evidence only if the stored rules allow it.",
        "Record source URL or reference, source type, result timestamp, and retrieval timestamp.",
        "Compare result evidence with stored market rules and stored match identity facts.",
        "Record any source contradiction without resolving it automatically.",
        "Capture public read-only Polymarket resolution status later if explicitly approved.",
        "Submit the evidence package for operator review before any status promotion.",
    ]


def _source_quality_update_steps():
    return [
        "Wait until outcome evidence exists and operator review is ready.",
        "Compare each stored source role against the reviewed outcome evidence.",
        "Update only allowed metrics: resolution alignment, timeliness, official source status, contradiction count, and operator notes.",
        "Do not use profit, PnL, ROI, EV, edge, betting confidence, or side selection as source quality metrics.",
        "Keep source ranking unchanged until a separate reviewed update task approves it.",
    ]


def _operator_review_steps():
    return [
        "Review monitored facts and mark missing or ambiguous source gaps.",
        "Confirm exact market rules text completeness from local artifacts.",
        "Confirm participant, tournament, format, schedule, and timezone fields.",
        "Confirm how cancellation, reschedule, forfeit, delay, and fallback rules should be used later.",
        "Approve or reject any future readonly outcome check request in a separate task.",
    ]


def _input_references():
    return {
        "paperlive001": {
            "observation_ledger": PAPERLIVE001_LEDGER_JSON_PATH,
            "observation_summary": PAPERLIVE001_LEDGER_SUMMARY_JSON_PATH,
            "source_quality_pending_observation": PAPERLIVE001_SOURCE_QUALITY_PENDING_JSON_PATH,
            "outcome_reconciliation_placeholder": PAPERLIVE001_OUTCOME_PLACEHOLDER_JSON_PATH,
            "workbench_surface": PAPERLIVE001_WORKBENCH_SURFACE_JSON_PATH,
        },
        "source_009c": {
            "operator_surface_json": OPERATOR_SURFACE_JSON_PATH,
            "operator_surface_md": OPERATOR_SURFACE_MD_PATH,
            "observation_plan_json": OBSERVATION_PLAN_JSON_PATH,
            "observation_plan_md": OBSERVATION_PLAN_MD_PATH,
            "outcome_contract_json": OUTCOME_CONTRACT_JSON_PATH,
            "outcome_contract_md": OUTCOME_CONTRACT_MD_PATH,
            "source_quality_flow_json": SOURCE_QUALITY_FLOW_JSON_PATH,
            "source_quality_flow_md": SOURCE_QUALITY_FLOW_MD_PATH,
        },
        "source_009b": {
            "manual_capture_json": CAPTURE_JSON_PATH,
            "manual_capture_md": CAPTURE_MD_PATH,
            "operator_surface_json": CAPTURE_OPERATOR_SURFACE_JSON_PATH,
            "operator_surface_md": CAPTURE_OPERATOR_SURFACE_MD_PATH,
            "source_quality_candidate_json": SOURCE_QUALITY_CANDIDATE_JSON_PATH,
            "source_quality_candidate_md": SOURCE_QUALITY_CANDIDATE_MD_PATH,
        },
        "source_009a": {
            "raw_fetch": RAW_FETCH_PATH,
            "normalized_candidate": NORMALIZED_CANDIDATE_PATH,
            "source_capture_candidate": SOURCE_CANDIDATE_PATH,
            "operator_checklist_json": SOURCE_009A_CHECKLIST_JSON_PATH,
            "operator_checklist_md": SOURCE_009A_CHECKLIST_MD_PATH,
        },
        "readiness": {
            "ingest_result": INGEST_RESULT_PATH,
            "ingested_overlay": INGEST_OVERLAY_PATH,
            "readiness_report": READINESS_REPORT_PATH,
            "readiness_gate": READINESS_GATE_PATH,
        },
    }


def build_monitoring_plan(root=ROOT):
    inputs = _load_inputs(root=root)
    fields = _known_fields(inputs)
    pipeline = _pipeline_snapshot(root=root)
    missing_sources = _missing_sources(fields)
    return {
        "schema_version": SCHEMA_VERSION,
        "task_id": TASK_ID,
        "generated_by": GENERATED_BY,
        "generated_at_marker": LOCAL_TIMESTAMP,
        "market_id": MARKET_ID,
        "market_class": MARKET_CLASS,
        "title_or_question": fields["title_or_question"],
        "monitoring_mode": "source_and_outcome_monitoring_plan_only",
        "outcome_checked": False,
        "outcome_known": False,
        "outcome_resolution_status": "pending_not_checked",
        "simulated_trade_created": False,
        "selected_side": None,
        "stake_amount": None,
        "order_created": False,
        "wallet_used": False,
        "position_sizing_created": False,
        "market_action_guidance_generated": False,
        "probability_ev_edge_confidence_generated": False,
        "side_selection_generated": False,
        "monitored_facts": _monitored_facts(fields),
        "known_sources_from_existing_artifacts": _known_sources_from_existing_artifacts(
            root=root
        ),
        "missing_sources": missing_sources,
        "source_fetch_required_later": _source_fetch_required_later(),
        "future_readonly_fetch_allowed_only_with_explicit_approval": True,
        "outcome_reconciliation_steps": _outcome_reconciliation_steps(),
        "source_quality_update_steps": _source_quality_update_steps(),
        "operator_review_steps": _operator_review_steps(),
        "blockers_before_outcome_reconciliation": [
            "explicit future readonly network approval is missing",
            "official match/tournament result source is missing",
            "final result source is missing",
            "result timestamp is missing",
            "operator review is incomplete",
        ],
        "blockers_before_any_simulated_decision": [
            "this task has no simulated decision authority",
            "operator review is incomplete",
            "outcome evidence is missing",
            "governance, risk, execution, and wallet controls are out of scope",
        ],
        "references": _input_references(),
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
        "safety_summary": dict(SAFETY_SUMMARY),
        "openrouter_calls_performed": 0,
        "polymarket_api_calls_performed": 0,
        "external_network_calls_performed": 0,
        "network_calls_performed": 0,
        "canonical_packets_mutated": False,
    }


def _checklist_item(
    item_id,
    description,
    current_status,
    source_reference_if_known,
    future_action_required,
    requires_network_later,
):
    return {
        "item_id": item_id,
        "description": description,
        "current_status": current_status,
        "source_reference_if_known": source_reference_if_known,
        "future_action_required": future_action_required,
        "requires_network_later": bool(requires_network_later),
        "requires_operator_review": True,
        "no_trading_authority": True,
    }


def build_source_monitoring_checklist(root=ROOT):
    fields = _known_fields(_load_inputs(root=root))
    sections = [
        {
            "section_id": "polymarket_market_rules_source",
            "title": "Polymarket market/rules source",
            "items": [
                _checklist_item(
                    "pm_rules_text",
                    "Confirm exact direct market rules text from stored local artifacts.",
                    (
                        "ambiguous"
                        if fields["exact_rules_text_complete_pending_operator_review"]
                        else "missing"
                    ),
                    fields["exact_rules_text_source"],
                    "Operator must confirm completeness before later outcome reconciliation.",
                    False,
                )
            ],
        },
        {
            "section_id": "official_tournament_match_source",
            "title": "Official tournament/match source",
            "items": [
                _checklist_item(
                    "official_result_source",
                    "Identify direct official result source for this match or tournament.",
                    "ambiguous",
                    OPERATOR_SURFACE_JSON_PATH,
                    "Future readonly check requires explicit approval.",
                    True,
                )
            ],
        },
        {
            "section_id": "team_player_identity_check",
            "title": "Team/player identity check",
            "items": [
                _checklist_item(
                    "teams_or_players_identity",
                    "Confirm both participant names and any alias handling.",
                    "known",
                    NORMALIZED_CANDIDATE_PATH,
                    "Operator review required.",
                    False,
                )
            ],
        },
        {
            "section_id": "match_format_check",
            "title": "Match format check",
            "items": [
                _checklist_item(
                    "match_format",
                    "Confirm BO5 match format against stored rules and event context.",
                    "known",
                    OPERATOR_SURFACE_JSON_PATH,
                    "Operator review required.",
                    False,
                )
            ],
        },
        {
            "section_id": "schedule_timezone_check",
            "title": "Schedule/timezone check",
            "items": [
                _checklist_item(
                    "scheduled_time_timezone",
                    "Confirm scheduled time and timezone.",
                    "known",
                    NORMALIZED_CANDIDATE_PATH,
                    "Operator review required.",
                    False,
                )
            ],
        },
        {
            "section_id": "cancellation_reschedule_forfeit_rule_check",
            "title": "Cancellation/reschedule/forfeit rule check",
            "items": [
                _checklist_item(
                    "cancellation_reschedule_forfeit_rule",
                    "Confirm cancellation, reschedule, delay, and forfeit handling.",
                    (
                        "ambiguous"
                        if fields["cancellation_reschedule_forfeit_rule_present"]
                        else "missing"
                    ),
                    fields["exact_rules_text_source"],
                    "Operator must confirm rule handling before outcome reconciliation.",
                    False,
                )
            ],
        },
        {
            "section_id": "final_result_source_check",
            "title": "Final result source check",
            "items": [
                _checklist_item(
                    "final_result_source",
                    "Collect final result source evidence later.",
                    "pending_future_readonly_check",
                    None,
                    "Future readonly check requires explicit approval.",
                    True,
                )
            ],
        },
        {
            "section_id": "outcome_reconciliation_readiness",
            "title": "Outcome reconciliation readiness",
            "items": [
                _checklist_item(
                    "outcome_reconciliation_inputs",
                    "Verify that official source, result timestamp, and operator notes exist.",
                    "pending_future_readonly_check",
                    PAPERLIVE001_OUTCOME_PLACEHOLDER_JSON_PATH,
                    "Do not reconcile until future evidence and operator review exist.",
                    True,
                )
            ],
        },
        {
            "section_id": "source_quality_update_readiness",
            "title": "Source quality update readiness",
            "items": [
                _checklist_item(
                    "source_quality_update_inputs",
                    "Verify source alignment inputs before any source quality update.",
                    "pending_future_readonly_check",
                    PAPERLIVE001_SOURCE_QUALITY_PENDING_JSON_PATH,
                    "Use reviewed outcome evidence later; do not use profit or PnL.",
                    False,
                )
            ],
        },
        {
            "section_id": "operator_review_required",
            "title": "Operator review required",
            "items": [
                _checklist_item(
                    "operator_review_required",
                    "Operator must review every gap before status promotion.",
                    "pending_future_readonly_check",
                    OPERATOR_SURFACE_JSON_PATH,
                    "Keep artifacts passive until reviewed.",
                    False,
                )
            ],
        },
    ]
    return {
        "schema_version": "esports_source_monitoring_checklist_paperlive002.v1",
        "task_id": TASK_ID,
        "generated_by": GENERATED_BY,
        "market_id": MARKET_ID,
        "market_class": MARKET_CLASS,
        "title_or_question": fields["title_or_question"],
        "sections": sections,
        "operator_review_required": True,
        "outcome_checked": False,
        "simulated_trade_created": False,
        "selected_side": None,
        "stake_amount": None,
        "no_market_action_guidance": True,
        "no_trading_authority": True,
        "safety_summary": dict(SAFETY_SUMMARY),
        "openrouter_calls_performed": 0,
        "polymarket_api_calls_performed": 0,
        "external_network_calls_performed": 0,
    }


def build_future_outcome_check_request(root=ROOT):
    fields = _known_fields(_load_inputs(root=root))
    return {
        "schema_version": "esports_future_readonly_outcome_check_request.v1",
        "task_id": TASK_ID,
        "generated_by": GENERATED_BY,
        "market_id": MARKET_ID,
        "market_class": MARKET_CLASS,
        "title_or_question": fields["title_or_question"],
        "request_status": "prepared_not_executed",
        "network_calls_performed": 0,
        "future_network_required": True,
        "explicit_network_approval_required": True,
        "allowed_future_sources": [
            "public read-only Polymarket/Gamma market/resolution status",
            "official tournament/match result source if available",
            "fallback credible match result source if official source unavailable",
        ],
        "forbidden_future_actions": [
            "auth",
            "wallet",
            "orders",
            "trading",
            "browser automation",
            "market action recommendation",
            "probability/EV/edge/confidence",
            "side selection",
        ],
        "expected_future_outputs": [
            "raw outcome source fetch",
            "normalized outcome evidence",
            "source alignment review",
            "source quality pending update",
        ],
        "operator_review_required": True,
        "outcome_checked": False,
        "outcome_known": False,
        "simulated_trade_created": False,
        "selected_side": None,
        "stake_amount": None,
        "no_market_action_guidance": True,
        "no_trading_authority": True,
        "safety_summary": dict(SAFETY_SUMMARY),
        "openrouter_calls_performed": 0,
        "polymarket_api_calls_performed": 0,
        "external_network_calls_performed": 0,
    }


def build_source_quality_update_plan(root=ROOT):
    fields = _known_fields(_load_inputs(root=root))
    return {
        "schema_version": "source_quality_update_plan_paperlive002.v1",
        "task_id": TASK_ID,
        "generated_by": GENERATED_BY,
        "market_id": MARKET_ID,
        "market_class": MARKET_CLASS,
        "title_or_question": fields["title_or_question"],
        "update_status": "planned_not_performed",
        "outcome_known": False,
        "source_scoring_performed": False,
        "source_ranking_updated": False,
        "profit_or_pnl_used": False,
        "future_update_requires": [
            "outcome evidence",
            "source alignment review",
            "contradiction review",
            "operator review",
        ],
        "allowed_future_metrics": [
            "resolution_alignment",
            "timeliness",
            "official_source_status",
            "contradiction_count",
            "operator_usefulness_notes",
        ],
        "forbidden_metrics": [
            "profit_only_score",
            "PnL",
            "ROI",
            "EV",
            "edge",
            "betting confidence",
            "side selection",
        ],
        "no_market_action_guidance": True,
        "no_trading_authority": True,
        "operator_review_required": True,
        "simulated_trade_created": False,
        "selected_side": None,
        "stake_amount": None,
        "safety_summary": dict(SAFETY_SUMMARY),
        "openrouter_calls_performed": 0,
        "polymarket_api_calls_performed": 0,
        "external_network_calls_performed": 0,
    }


def build_workbench_surface(root=ROOT):
    fields = _known_fields(_load_inputs(root=root))
    return {
        "schema_version": "esports_monitoring_plan_surface_paperlive002.v1",
        "task_id": TASK_ID,
        "generated_by": GENERATED_BY,
        "market_id": MARKET_ID,
        "market_class": MARKET_CLASS,
        "title_or_question": fields["title_or_question"],
        "monitoring_plan_available": True,
        "monitoring_plan_path": MONITORING_PLAN_JSON_PATH,
        "source_monitoring_checklist_available": True,
        "source_monitoring_checklist_path": CHECKLIST_JSON_PATH,
        "future_outcome_check_request_available": True,
        "future_outcome_check_request_path": FUTURE_OUTCOME_CHECK_JSON_PATH,
        "source_quality_update_plan_available": True,
        "source_quality_update_plan_path": SOURCE_QUALITY_UPDATE_PLAN_JSON_PATH,
        "operator_review_required": True,
        "outcome_checked": False,
        "simulated_trade_created": False,
        "selected_side": None,
        "stake_amount": None,
        "next_operator_actions": [
            "Review the monitoring plan and checklist.",
            "Keep outcome reconciliation pending until an explicitly approved future readonly check.",
            "Review source quality update plan after outcome evidence exists.",
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


def build_run_summary(root=ROOT, artifacts_created=False):
    pipeline = _pipeline_snapshot(root=root)
    return {
        "schema_version": "esports_outcome_source_monitoring_plan_runner_summary.v1",
        "task_id": TASK_ID,
        "generated_by": GENERATED_BY,
        "status": "completed_local" if artifacts_created else "dry_run_no_write",
        "market_id": MARKET_ID,
        "market_class": MARKET_CLASS,
        "monitoring_plans_created_count": 1 if artifacts_created else 0,
        "source_monitoring_checklists_created_count": 1 if artifacts_created else 0,
        "future_outcome_check_requests_created_count": 1 if artifacts_created else 0,
        "source_quality_update_plans_created_count": 1 if artifacts_created else 0,
        "outcome_checks_performed_count": 0,
        "simulated_trades_created_count": 0,
        "orders_created_count": 0,
        "selected_side_count": 0,
        "stake_amount_count": 0,
        "source_scoring_updates_performed_count": 0,
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
        "next_recommended_action": (
            "PMBOT-PAPERLIVE-003-ESPORTS-READONLY-OUTCOME-CHECK-PROTOCOL-NO-TRADE"
        ),
        "openrouter_calls_performed": 0,
        "polymarket_api_calls_performed": 0,
        "external_network_calls_performed": 0,
        "network_calls_performed": 0,
        "canonical_packets_mutated": False,
    }


def build_docs_result(root=ROOT, artifacts_created=True):
    summary = build_run_summary(root=root, artifacts_created=artifacts_created)
    return {
        "task_id": TASK_ID,
        "status": "completed_local_validation_pending_commit",
        "head_before": "0672a41ac8b9f2d39cd946c9e7a97be1cb982d23",
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
        "source_scoring_performed": False,
        "source_ranking_updated": False,
        "profit_or_pnl_recorded": False,
        "trading_runtime_changed": False,
        "dispatcher_changed": False,
        "background_worker_created": False,
        "queue_mutated": False,
        "browser_automation_used": False,
        "canonical_packets_mutated": False,
        "market_action_guidance_generated": False,
        "probability_ev_edge_confidence_generated": False,
        "side_selection_generated": False,
        "market_id": MARKET_ID,
        "market_class": MARKET_CLASS,
        "monitoring_plan_created": artifacts_created,
        "source_monitoring_checklist_created": artifacts_created,
        "future_readonly_outcome_check_request_created": artifacts_created,
        "source_quality_update_plan_created": artifacts_created,
        "passive_workbench_surface_created": artifacts_created,
        "monitoring_plans_created_count": summary["monitoring_plans_created_count"],
        "outcome_checks_performed_count": summary["outcome_checks_performed_count"],
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


def render_monitoring_plan_markdown(plan):
    lines = [
        "# PMBOT PAPERLIVE-002 Esports Outcome/Source Monitoring Plan",
        "",
        f"- task_id: {plan['task_id']}",
        f"- market_id: {plan['market_id']}",
        f"- market_class: {plan['market_class']}",
        f"- monitoring_mode: {plan['monitoring_mode']}",
        "- outcome_checked: false",
        "- outcome_known: false",
        "- outcome_resolution_status: pending_not_checked",
        "- simulated_trade_created: false",
        "- selected_side: null",
        "- stake_amount: null",
        "- order_created: false",
        "- wallet_used: false",
        "- position_sizing_created: false",
        "- no_market_action_guidance: true",
        "- no probability, EV, edge, confidence, or side selection guidance",
        "",
        "## Monitored Facts",
        "",
    ]
    for fact in plan["monitored_facts"]:
        lines.append(
            f"- {fact['fact_id']}: {fact['current_status']} "
            f"(source: {fact['source_reference_if_known']})"
        )
    lines.extend(["", "## Known Sources From Existing Artifacts", ""])
    for source in plan["known_sources_from_existing_artifacts"]:
        lines.append(
            f"- {source['artifact_group']} / {source['source_role']}: "
            f"{source['status']} ({source['reference']})"
        )
    lines.extend(["", "## Missing Sources", ""])
    for item in plan["missing_sources"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Future Readonly Checks", ""])
    lines.append("- future readonly fetch allowed only with explicit approval")
    lines.append("- outcome reconciliation is not performed in this task")
    lines.append("- source quality update is planned, not performed")
    lines.extend(["", "## Outcome Reconciliation Steps", ""])
    for item in plan["outcome_reconciliation_steps"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Source Quality Update Steps", ""])
    for item in plan["source_quality_update_steps"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Operator Review Steps", ""])
    for item in plan["operator_review_steps"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Safety Summary", ""])
    lines.extend(
        [
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
            "- no runtime changes, no dispatcher changes, no background worker changes, no browser automation, and no queue changes",
            "- no canonical packet mutation",
            "- no market action guidance",
        ]
    )
    return "\n".join(lines)


def render_checklist_markdown(checklist):
    lines = [
        "# PMBOT PAPERLIVE-002 Source Monitoring Checklist",
        "",
        f"- task_id: {checklist['task_id']}",
        f"- market_id: {checklist['market_id']}",
        "- outcome_checked: false",
        "- simulated_trade_created: false",
        "- selected_side: null",
        "- stake_amount: null",
        "- no_market_action_guidance: true",
        "- no_trading_authority: true",
        "",
    ]
    for section in checklist["sections"]:
        lines.extend([f"## {section['title']}", ""])
        for item in section["items"]:
            lines.append(f"- item_id: {item['item_id']}")
            lines.append(f"  - current_status: {item['current_status']}")
            lines.append(f"  - source_reference_if_known: {item['source_reference_if_known']}")
            lines.append(f"  - requires_network_later: {str(item['requires_network_later']).lower()}")
            lines.append("  - requires_operator_review: true")
            lines.append("  - no_trading_authority: true")
        lines.append("")
    return "\n".join(lines)


def render_future_outcome_check_markdown(request):
    lines = [
        "# PMBOT PAPERLIVE-002 Future Readonly Outcome Check Request",
        "",
        f"- task_id: {request['task_id']}",
        f"- market_id: {request['market_id']}",
        f"- request_status: {request['request_status']}",
        "- network_calls_performed: 0",
        "- future_network_required: true",
        "- explicit_network_approval_required: true",
        "- outcome_checked: false",
        "- outcome_known: false",
        "- simulated_trade_created: false",
        "- selected_side: null",
        "- stake_amount: null",
        "",
        "## Allowed Future Sources",
        "",
    ]
    for item in request["allowed_future_sources"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Forbidden Future Actions", ""])
    for item in request["forbidden_future_actions"]:
        lines.append(f"- forbidden: {item}")
    lines.extend(["", "## Expected Future Outputs", ""])
    for item in request["expected_future_outputs"]:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## Safety Summary",
            "",
            "- prepared only, not executed",
            "- no network calls in this task",
            "- no market action recommendation",
            "- no probability, EV, edge, confidence, or side selection guidance",
            "- no wallet, orders, trading, auth, or browser automation",
        ]
    )
    return "\n".join(lines)


def render_source_quality_update_plan_markdown(plan):
    lines = [
        "# PMBOT PAPERLIVE-002 Source Quality Update Plan",
        "",
        f"- task_id: {plan['task_id']}",
        f"- market_id: {plan['market_id']}",
        f"- update_status: {plan['update_status']}",
        "- outcome_known: false",
        "- source_scoring_performed: false",
        "- source_ranking_updated: false",
        "- profit_or_pnl_used: false",
        "- no_market_action_guidance: true",
        "- no_trading_authority: true",
        "",
        "## Future Update Requires",
        "",
    ]
    for item in plan["future_update_requires"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Allowed Future Metrics", ""])
    for item in plan["allowed_future_metrics"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Forbidden Metrics", ""])
    for item in plan["forbidden_metrics"]:
        lines.append(f"- forbidden metric: {item}")
    lines.extend(
        [
            "",
            "## Safety Summary",
            "",
            "- planned only, not performed",
            "- no profit-only score",
            "- no PnL, ROI, EV, edge, betting confidence, or side selection metric",
            "- no market action guidance",
            "- no trading authority",
        ]
    )
    return "\n".join(lines)


def render_workbench_surface_markdown(surface):
    lines = [
        "# PMBOT PAPERLIVE-002 Passive Monitoring Plan Surface",
        "",
        f"- task_id: {surface['task_id']}",
        f"- market_id: {surface['market_id']}",
        "- monitoring_plan_available: true",
        "- source_monitoring_checklist_available: true",
        "- future_outcome_check_request_available: true",
        "- source_quality_update_plan_available: true",
        "- operator_review_required: true",
        "- outcome_checked: false",
        "- simulated_trade_created: false",
        "- selected_side: null",
        "- stake_amount: null",
        "- no_market_action_guidance: true",
        "- no_trading_authority: true",
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
            "- passive surface only",
            "- no queue mutation",
            "- no runtime wiring change",
            "- no dispatcher change",
            "- no browser automation",
            "- no canonical packet mutation",
        ]
    )
    return "\n".join(lines)


def render_run_summary_markdown(summary):
    lines = [
        "# PMBOT PAPERLIVE-002 Monitoring Plan Runner Summary",
        "",
        f"- task_id: {summary['task_id']}",
        f"- status: {summary['status']}",
        f"- market_id: {summary['market_id']}",
        f"- market_class: {summary['market_class']}",
        f"- monitoring_plans_created_count: {summary['monitoring_plans_created_count']}",
        (
            "- source_monitoring_checklists_created_count: "
            f"{summary['source_monitoring_checklists_created_count']}"
        ),
        (
            "- future_outcome_check_requests_created_count: "
            f"{summary['future_outcome_check_requests_created_count']}"
        ),
        (
            "- source_quality_update_plans_created_count: "
            f"{summary['source_quality_update_plans_created_count']}"
        ),
        "- outcome_checks_performed_count: 0",
        "- simulated_trades_created_count: 0",
        "- orders_created_count: 0",
        "- selected_side_count: 0",
        "- stake_amount_count: 0",
        "- source_scoring_updates_performed_count: 0",
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
        "- no outcome check",
        "- no source scoring update",
        "- no runtime changes, no dispatcher changes, no background worker changes, no browser automation, and no queue changes",
        "- no canonical packet mutation",
        "",
        "## Next Recommended Action",
        "",
        f"`{summary['next_recommended_action']}`",
    ]
    return "\n".join(lines)


def render_docs_markdown(result):
    return "\n".join(
        [
            "# PMBOT PAPERLIVE-002 Esports Outcome/Source Monitoring Plan Runner No Trade",
            "",
            "PAPERLIVE-002 is local-only. It creates monitoring plan artifacts only for esports market `1987056`.",
            "",
            "## Outcome",
            "",
            f"- monitoring_plan_created: {str(result['monitoring_plan_created']).lower()}",
            (
                "- source_monitoring_checklist_created: "
                f"{str(result['source_monitoring_checklist_created']).lower()}"
            ),
            (
                "- future_readonly_outcome_check_request_created: "
                f"{str(result['future_readonly_outcome_check_request_created']).lower()}"
            ),
            (
                "- source_quality_update_plan_created: "
                f"{str(result['source_quality_update_plan_created']).lower()}"
            ),
            (
                "- passive_workbench_surface_created: "
                f"{str(result['passive_workbench_surface_created']).lower()}"
            ),
            "- operator_review_required: true",
            "- outcome_checked: false",
            "- outcome_known: false",
            "",
            "## Boundary",
            "",
            "- It does not check outcome.",
            "- It does not call network or API.",
            "- It does not create a simulated trade.",
            "- It does not choose a side.",
            "- It does not create a stake.",
            "- It does not compute probability, EV, edge, or confidence.",
            "- It does not create orders.",
            "- It does not use a wallet.",
            "- It does not mutate runtime, queue, or canonical packets.",
            "- Source quality update is planned, not performed.",
            "- Future outcome check requires explicit network approval.",
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
            "- no runtime changes, no dispatcher changes, no background worker changes, no browser automation, and no queue changes",
            "- no canonical packet mutation",
            "",
            "## Next Recommended Action",
            "",
            f"`{result['next_recommended_action']}`",
        ]
    )


def write_artifacts(root=ROOT):
    plan = build_monitoring_plan(root=root)
    checklist = build_source_monitoring_checklist(root=root)
    future_request = build_future_outcome_check_request(root=root)
    quality_plan = build_source_quality_update_plan(root=root)
    workbench = build_workbench_surface(root=root)
    summary = build_run_summary(root=root, artifacts_created=True)
    docs_result = build_docs_result(root=root, artifacts_created=True)

    _write_json(MONITORING_PLAN_JSON_PATH, plan, root=root)
    _write_text(MONITORING_PLAN_MD_PATH, render_monitoring_plan_markdown(plan), root=root)
    _write_json(CHECKLIST_JSON_PATH, checklist, root=root)
    _write_text(CHECKLIST_MD_PATH, render_checklist_markdown(checklist), root=root)
    _write_json(FUTURE_OUTCOME_CHECK_JSON_PATH, future_request, root=root)
    _write_text(
        FUTURE_OUTCOME_CHECK_MD_PATH,
        render_future_outcome_check_markdown(future_request),
        root=root,
    )
    _write_json(SOURCE_QUALITY_UPDATE_PLAN_JSON_PATH, quality_plan, root=root)
    _write_text(
        SOURCE_QUALITY_UPDATE_PLAN_MD_PATH,
        render_source_quality_update_plan_markdown(quality_plan),
        root=root,
    )
    _write_json(WORKBENCH_SURFACE_JSON_PATH, workbench, root=root)
    _write_text(
        WORKBENCH_SURFACE_MD_PATH,
        render_workbench_surface_markdown(workbench),
        root=root,
    )
    _write_json(RUN_SUMMARY_JSON_PATH, summary, root=root)
    _write_text(RUN_SUMMARY_MD_PATH, render_run_summary_markdown(summary), root=root)
    _write_json(DOC_RESULT_JSON_PATH, docs_result, root=root)
    _write_text(DOC_RESULT_MD_PATH, render_docs_markdown(docs_result), root=root)
    return summary


def build_dry_run(root=ROOT):
    plan = build_monitoring_plan(root=root)
    summary = build_run_summary(root=root, artifacts_created=False)
    return {
        "schema_version": "esports_outcome_source_monitoring_plan_runner_dry_run.v1",
        "task_id": TASK_ID,
        "status": "dry_run_no_write",
        "dry_run": True,
        "market_id": MARKET_ID,
        "market_class": MARKET_CLASS,
        "planned_monitoring_plan_path": MONITORING_PLAN_JSON_PATH,
        "planned_source_monitoring_checklist_path": CHECKLIST_JSON_PATH,
        "planned_future_outcome_check_request_path": FUTURE_OUTCOME_CHECK_JSON_PATH,
        "planned_source_quality_update_plan_path": SOURCE_QUALITY_UPDATE_PLAN_JSON_PATH,
        "planned_workbench_surface_path": WORKBENCH_SURFACE_JSON_PATH,
        "monitoring_mode": plan["monitoring_mode"],
        "outcome_checked": False,
        "outcome_known": False,
        "simulated_trade_created": False,
        "selected_side": None,
        "stake_amount": None,
        "order_created": False,
        "wallet_used": False,
        "files_written": [],
        "summary": summary,
        "safety_summary": dict(SAFETY_SUMMARY),
        "openrouter_calls_performed": 0,
        "polymarket_api_calls_performed": 0,
        "external_network_calls_performed": 0,
    }


def build_summary_only(root=ROOT):
    summary = _load_optional_json(RUN_SUMMARY_JSON_PATH, root=root)
    plan = _load_optional_json(MONITORING_PLAN_JSON_PATH, root=root)
    checklist = _load_optional_json(CHECKLIST_JSON_PATH, root=root)
    future_request = _load_optional_json(FUTURE_OUTCOME_CHECK_JSON_PATH, root=root)
    quality_plan = _load_optional_json(SOURCE_QUALITY_UPDATE_PLAN_JSON_PATH, root=root)
    workbench = _load_optional_json(WORKBENCH_SURFACE_JSON_PATH, root=root)
    pipeline = _pipeline_snapshot(root=root)
    return {
        "schema_version": "esports_outcome_source_monitoring_plan_runner_summary_only.v1",
        "task_id": TASK_ID,
        "status": "summary_only",
        "market_id": MARKET_ID,
        "market_class": MARKET_CLASS,
        "monitoring_plan_exists": plan is not None,
        "source_monitoring_checklist_exists": checklist is not None,
        "future_outcome_check_request_exists": future_request is not None,
        "source_quality_update_plan_exists": quality_plan is not None,
        "passive_workbench_surface_exists": workbench is not None,
        "summary_exists": summary is not None,
        "monitoring_plans_created_count": (summary or {}).get(
            "monitoring_plans_created_count"
        ),
        "outcome_checks_performed_count": (summary or {}).get(
            "outcome_checks_performed_count",
            0,
        ),
        "simulated_trades_created_count": (summary or {}).get(
            "simulated_trades_created_count",
            0,
        ),
        "orders_created_count": (summary or {}).get("orders_created_count", 0),
        "selected_side_count": (summary or {}).get("selected_side_count", 0),
        "stake_amount_count": (summary or {}).get("stake_amount_count", 0),
        "real_ingested_template_count": pipeline.get("real_ingested_template_count"),
        "draft_ingested_template_count": pipeline.get("draft_ingested_template_count"),
        "ready_ingested_template_count": pipeline.get("ready_ingested_template_count"),
        "future_live_002_allowed": pipeline.get("future_live_002_allowed"),
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
