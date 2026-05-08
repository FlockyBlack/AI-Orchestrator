import argparse
import json
from pathlib import Path


TASK_ID = (
    "PMBOT-PAPERLIVE-006-ESPORTS-SOURCE-QUALITY-PENDING-LEDGER-AND-SUMMARY-NO-TRADE"
)
GENERATED_BY = "pm_bot/llm/source_quality_pending_ledger.py"

ROOT = Path(__file__).resolve().parents[2]

MARKET_ID = "1987056"
MARKET_CLASS = "esports"
MARKET_TITLE = (
    "LoL: JD Gaming vs Anyone's Legend (BO5) - Esports World Cup China Qualifier Phase 2"
)
LOCAL_TIMESTAMP = "2026-05-08 Asia/Tbilisi"

NEXT_WEATHER_TASK = "PMBOT-SOURCE-010A-WEATHER-MARKET-CLASS-PILOT-READONLY-DISCOVERY"
NEXT_ESPORTS_TASK = (
    "PMBOT-PAPERLIVE-007-ESPORTS-FINAL-CONTOUR-SUMMARY-AND-HANDOFF-NO-TRADE"
)

SOURCE_009A_RAW_FETCH_PATH = (
    "pm_bot/live_readonly/esports_market_discovery/"
    "esports_market_raw_fetch_009a.v1.json"
)
SOURCE_009A_NORMALIZED_CANDIDATE_PATH = (
    "pm_bot/live_readonly/esports_market_discovery/"
    "esports_market_normalized_candidate_009a.v1.json"
)
SOURCE_009A_CAPTURE_CANDIDATE_PATH = (
    "pm_bot/live_readonly/esports_market_discovery/"
    "esports_source_capture_candidate_009a.v1.json"
)
SOURCE_009A_OPERATOR_CHECKLIST_PATH = (
    "pm_bot/live_readonly/esports_market_discovery/"
    "esports_operator_review_checklist_009a.v1.json"
)

SOURCE_009B_MANUAL_CAPTURE_PATH = (
    "pm_bot/llm/manual_resolution_source_capture/"
    f"{MARKET_ID}_resolution_source_capture.v1.json"
)
SOURCE_009B_AUTOFILL_RESULT_PATH = (
    "pm_bot/llm/esports_capture_autofill_result_009b.v1.json"
)
SOURCE_009B_OPERATOR_SURFACE_PATH = (
    "pm_bot/llm/esports_capture_operator_review_surface_009b.v1.json"
)
SOURCE_009B_SOURCE_QUALITY_PATH = (
    "pm_bot/llm/source_quality_observation_candidate_1987056_009b.v1.json"
)

SOURCE_009C_OPERATOR_SURFACE_PATH = (
    "pm_bot/llm/esports_operator_review_surface_1987056_009c.v1.json"
)
SOURCE_009C_OBSERVATION_PLAN_PATH = (
    "pm_bot/paper_live/esports_observation_plan_1987056_009c.v1.json"
)
SOURCE_009C_OUTCOME_TRACKING_CONTRACT_PATH = (
    "pm_bot/paper_live/outcome_tracking_contract.v1.json"
)
SOURCE_009C_SOURCE_QUALITY_FLOW_PATH = (
    "pm_bot/llm/source_quality_observation_flow_009c.v1.json"
)
SOURCE_009C_WORKBENCH_SURFACE_PATH = (
    "pm_bot/workbench/esports_paper_live_preparation_surface_1987056_009c.v1.json"
)

PAPERLIVE001_LEDGER_PATH = (
    "pm_bot/paper_live/esports_observation_ledger_first_run_1987056.v1.json"
)
PAPERLIVE001_SOURCE_QUALITY_PATH = (
    "pm_bot/llm/source_quality_pending_observation_1987056_paperlive001.v1.json"
)
PAPERLIVE001_OUTCOME_PLACEHOLDER_PATH = (
    "pm_bot/paper_live/esports_outcome_reconciliation_placeholder_1987056.v1.json"
)
PAPERLIVE001_WORKBENCH_SURFACE_PATH = (
    "pm_bot/workbench/esports_paper_live_observation_surface_1987056_paperlive001.v1.json"
)

PAPERLIVE002_MONITORING_PLAN_PATH = (
    "pm_bot/paper_live/"
    "esports_outcome_source_monitoring_plan_1987056_paperlive002.v1.json"
)
PAPERLIVE002_CHECKLIST_PATH = (
    "pm_bot/paper_live/esports_source_monitoring_checklist_1987056_paperlive002.v1.json"
)
PAPERLIVE002_FUTURE_OUTCOME_CHECK_PATH = (
    "pm_bot/paper_live/esports_future_readonly_outcome_check_request_1987056.v1.json"
)
PAPERLIVE002_SOURCE_QUALITY_UPDATE_PLAN_PATH = (
    "pm_bot/llm/source_quality_update_plan_1987056_paperlive002.v1.json"
)
PAPERLIVE002_WORKBENCH_SURFACE_PATH = (
    "pm_bot/workbench/esports_monitoring_plan_surface_1987056_paperlive002.v1.json"
)

PAPERLIVE003_PROTOCOL_PATH = (
    "pm_bot/paper_live/"
    "esports_readonly_outcome_check_protocol_1987056_paperlive003.v1.json"
)
PAPERLIVE003_RAW_FETCH_CONTRACT_PATH = (
    "pm_bot/paper_live/esports_outcome_raw_fetch_contract_1987056_paperlive003.v1.json"
)
PAPERLIVE003_NORMALIZED_CONTRACT_PATH = (
    "pm_bot/paper_live/"
    "esports_normalized_outcome_evidence_contract_1987056_paperlive003.v1.json"
)
PAPERLIVE003_ALIGNMENT_CONTRACT_PATH = (
    "pm_bot/llm/source_alignment_review_contract_1987056_paperlive003.v1.json"
)
PAPERLIVE003_READINESS_GATE_PATH = (
    "pm_bot/paper_live/"
    "esports_readonly_outcome_check_readiness_gate_1987056_paperlive003.v1.json"
)
PAPERLIVE003_WORKBENCH_SURFACE_PATH = (
    "pm_bot/workbench/"
    "esports_readonly_outcome_check_protocol_surface_1987056_paperlive003.v1.json"
)

PAPERLIVE004_RAW_FETCH_PATH = (
    "pm_bot/paper_live/esports_outcome_raw_fetch_1987056_paperlive004.v1.json"
)
PAPERLIVE004_NORMALIZED_EVIDENCE_PATH = (
    "pm_bot/paper_live/"
    "esports_normalized_outcome_evidence_1987056_paperlive004.v1.json"
)
PAPERLIVE004_CALL_LEDGER_PATH = (
    "pm_bot/paper_live/esports_outcome_fetch_call_ledger_1987056_paperlive004.v1.json"
)
PAPERLIVE004_RECONCILIATION_INPUT_PATH = (
    "pm_bot/paper_live/esports_reconciliation_input_1987056_paperlive004.v1.json"
)
PAPERLIVE004_WORKBENCH_SURFACE_PATH = (
    "pm_bot/workbench/esports_outcome_fetch_surface_1987056_paperlive004.v1.json"
)

PAPERLIVE005_RECONCILIATION_PATH = (
    "pm_bot/paper_live/"
    "esports_outcome_source_reconciliation_1987056_paperlive005.v1.json"
)
PAPERLIVE005_RECONCILIATION_SUMMARY_PATH = (
    "pm_bot/paper_live/esports_outcome_source_reconciliation_summary.v1.json"
)
PAPERLIVE005_ALIGNMENT_PENDING_PATH = (
    "pm_bot/llm/source_alignment_review_pending_1987056_paperlive005.v1.json"
)
PAPERLIVE005_SOURCE_QUALITY_PENDING_UPDATE_PATH = (
    "pm_bot/llm/source_quality_pending_update_1987056_paperlive005.v1.json"
)
PAPERLIVE005_FUTURE_RECONCILIATION_REQUEST_PATH = (
    "pm_bot/paper_live/esports_future_reconciliation_update_request_1987056.v1.json"
)
PAPERLIVE005_WORKBENCH_SURFACE_PATH = (
    "pm_bot/workbench/esports_reconciliation_surface_1987056_paperlive005.v1.json"
)

INGEST_RESULT_PATH = "pm_bot/llm/manual_resolution_source_capture_ingest_result.v1.json"
INGEST_OVERLAY_PATH = "pm_bot/llm/manual_resolution_source_capture_ingested_overlay.v1.json"
READINESS_REPORT_PATH = "pm_bot/llm/post_capture_readiness_report.v1.json"
READINESS_GATE_PATH = "pm_bot/llm/post_capture_batch_readiness_gate.v1.json"

LEDGER_ENTRY_JSON_PATH = (
    "pm_bot/llm/source_quality_pending_ledger_1987056_paperlive006.v1.json"
)
LEDGER_ENTRY_MD_PATH = (
    "pm_bot/llm/source_quality_pending_ledger_1987056_paperlive006.v1.md"
)
LEDGER_INDEX_JSON_PATH = "pm_bot/llm/source_quality_pending_ledger_index.v1.json"
LEDGER_INDEX_MD_PATH = "pm_bot/llm/source_quality_pending_ledger_index.v1.md"
CONTOUR_SUMMARY_JSON_PATH = (
    "pm_bot/paper_live/esports_paperlive_contour_summary_1987056.v1.json"
)
CONTOUR_SUMMARY_MD_PATH = (
    "pm_bot/paper_live/esports_paperlive_contour_summary_1987056.v1.md"
)
HANDOFF_JSON_PATH = "pm_bot/paper_live/esports_to_weather_handoff_readiness.v1.json"
HANDOFF_MD_PATH = "pm_bot/paper_live/esports_to_weather_handoff_readiness.v1.md"
WORKBENCH_SURFACE_JSON_PATH = (
    "pm_bot/workbench/"
    "esports_paperlive_contour_summary_surface_1987056_paperlive006.v1.json"
)
WORKBENCH_SURFACE_MD_PATH = (
    "pm_bot/workbench/"
    "esports_paperlive_contour_summary_surface_1987056_paperlive006.v1.md"
)
ROADMAP_JSON_PATH = "docs/PMBOT_CURRENT_ROADMAP_AFTER_PAPERLIVE_006.json"
ROADMAP_MD_PATH = "docs/PMBOT_CURRENT_ROADMAP_AFTER_PAPERLIVE_006.md"
DOC_RESULT_JSON_PATH = "docs/PMBOT_PAPERLIVE_006_RESULT.json"
DOC_RESULT_MD_PATH = (
    "docs/PMBOT_PAPERLIVE_006_ESPORTS_SOURCE_QUALITY_PENDING_LEDGER_"
    "AND_SUMMARY_NO_TRADE.md"
)

INPUT_JSON_PATHS = [
    SOURCE_009A_RAW_FETCH_PATH,
    SOURCE_009A_NORMALIZED_CANDIDATE_PATH,
    SOURCE_009A_CAPTURE_CANDIDATE_PATH,
    SOURCE_009A_OPERATOR_CHECKLIST_PATH,
    SOURCE_009B_MANUAL_CAPTURE_PATH,
    SOURCE_009B_AUTOFILL_RESULT_PATH,
    SOURCE_009B_OPERATOR_SURFACE_PATH,
    SOURCE_009B_SOURCE_QUALITY_PATH,
    SOURCE_009C_OPERATOR_SURFACE_PATH,
    SOURCE_009C_OBSERVATION_PLAN_PATH,
    SOURCE_009C_OUTCOME_TRACKING_CONTRACT_PATH,
    SOURCE_009C_SOURCE_QUALITY_FLOW_PATH,
    SOURCE_009C_WORKBENCH_SURFACE_PATH,
    PAPERLIVE001_LEDGER_PATH,
    PAPERLIVE001_SOURCE_QUALITY_PATH,
    PAPERLIVE001_OUTCOME_PLACEHOLDER_PATH,
    PAPERLIVE001_WORKBENCH_SURFACE_PATH,
    PAPERLIVE002_MONITORING_PLAN_PATH,
    PAPERLIVE002_CHECKLIST_PATH,
    PAPERLIVE002_FUTURE_OUTCOME_CHECK_PATH,
    PAPERLIVE002_SOURCE_QUALITY_UPDATE_PLAN_PATH,
    PAPERLIVE002_WORKBENCH_SURFACE_PATH,
    PAPERLIVE003_PROTOCOL_PATH,
    PAPERLIVE003_RAW_FETCH_CONTRACT_PATH,
    PAPERLIVE003_NORMALIZED_CONTRACT_PATH,
    PAPERLIVE003_ALIGNMENT_CONTRACT_PATH,
    PAPERLIVE003_READINESS_GATE_PATH,
    PAPERLIVE003_WORKBENCH_SURFACE_PATH,
    PAPERLIVE004_RAW_FETCH_PATH,
    PAPERLIVE004_NORMALIZED_EVIDENCE_PATH,
    PAPERLIVE004_CALL_LEDGER_PATH,
    PAPERLIVE004_RECONCILIATION_INPUT_PATH,
    PAPERLIVE004_WORKBENCH_SURFACE_PATH,
    PAPERLIVE005_RECONCILIATION_PATH,
    PAPERLIVE005_RECONCILIATION_SUMMARY_PATH,
    PAPERLIVE005_ALIGNMENT_PENDING_PATH,
    PAPERLIVE005_SOURCE_QUALITY_PENDING_UPDATE_PATH,
    PAPERLIVE005_FUTURE_RECONCILIATION_REQUEST_PATH,
    PAPERLIVE005_WORKBENCH_SURFACE_PATH,
    INGEST_RESULT_PATH,
    INGEST_OVERLAY_PATH,
    READINESS_REPORT_PATH,
    READINESS_GATE_PATH,
]

JSON_OUTPUT_PATHS = [
    LEDGER_ENTRY_JSON_PATH,
    LEDGER_INDEX_JSON_PATH,
    CONTOUR_SUMMARY_JSON_PATH,
    HANDOFF_JSON_PATH,
    WORKBENCH_SURFACE_JSON_PATH,
    ROADMAP_JSON_PATH,
    DOC_RESULT_JSON_PATH,
]

MARKDOWN_OUTPUT_PATHS = [
    LEDGER_ENTRY_MD_PATH,
    LEDGER_INDEX_MD_PATH,
    CONTOUR_SUMMARY_MD_PATH,
    HANDOFF_MD_PATH,
    WORKBENCH_SURFACE_MD_PATH,
    ROADMAP_MD_PATH,
    DOC_RESULT_MD_PATH,
]

OUTPUT_PATHS = [
    LEDGER_ENTRY_JSON_PATH,
    LEDGER_ENTRY_MD_PATH,
    LEDGER_INDEX_JSON_PATH,
    LEDGER_INDEX_MD_PATH,
    CONTOUR_SUMMARY_JSON_PATH,
    CONTOUR_SUMMARY_MD_PATH,
    HANDOFF_JSON_PATH,
    HANDOFF_MD_PATH,
    WORKBENCH_SURFACE_JSON_PATH,
    WORKBENCH_SURFACE_MD_PATH,
    ROADMAP_JSON_PATH,
    ROADMAP_MD_PATH,
    DOC_RESULT_JSON_PATH,
    DOC_RESULT_MD_PATH,
]

SOURCE_QUALITY_INPUT_PATHS = [
    SOURCE_009B_SOURCE_QUALITY_PATH,
    SOURCE_009C_SOURCE_QUALITY_FLOW_PATH,
    PAPERLIVE001_SOURCE_QUALITY_PATH,
    PAPERLIVE002_SOURCE_QUALITY_UPDATE_PLAN_PATH,
    PAPERLIVE005_ALIGNMENT_PENDING_PATH,
    PAPERLIVE005_SOURCE_QUALITY_PENDING_UPDATE_PATH,
]

ALLOWED_FUTURE_METRICS = [
    "resolution_alignment",
    "timeliness",
    "official_source_status",
    "contradiction_count",
    "operator_usefulness_notes",
]

FORBIDDEN_METRICS = [
    "profit_only_score",
    "PnL",
    "ROI",
    "EV",
    "edge",
    "betting confidence",
    "side selection",
    "trade recommendation",
    "autonomous execution score",
]

SOURCE_ROLES = [
    "market_metadata_source",
    "market_rules_source",
    "official_result_source_candidate",
    "tournament_or_match_context_source",
    "unresolved_source",
    "local_capture_source",
    "operator_review_surface",
    "paper_live_observation_source",
    "outcome_fetch_source",
]

PENDING_ALIGNMENT_DIMENSIONS = [
    "match_identity_alignment",
    "tournament_alignment",
    "result_alignment",
    "timeliness_alignment",
    "official_source_status",
    "contradiction_review",
]

PENDING_UPDATE_REQUIREMENTS = [
    "outcome evidence",
    "source alignment review",
    "contradiction review",
    "operator review",
]

BLOCKERS_TO_SCORING = [
    "outcome_known is false",
    "outcome_resolution_status is unresolved",
    "final_outcome_resolved is false",
    "source_alignment_review_performed is false",
    "operator review of final outcome evidence is pending",
]

BLOCKERS_BEFORE_AUTONOMOUS_TRADING = [
    "weather pilot not completed",
    "crypto pilot not completed",
    "simulated decision ledger not completed",
    "risk engine not completed",
    "position sizing not completed",
    "execution mock not completed",
    "supervised micro-execution not completed",
    "wallet isolation not completed",
    "kill switch not completed",
    "audit and reconciliation not completed",
    "limited autonomous mode governance not completed",
]

SAFETY_SUMMARY = {
    "no_market_action_guidance": True,
    "operator_review_only": True,
    "analysis_only": True,
    "local_only": True,
    "local_evidence_assessment_only": True,
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
    "auth_headers_used": False,
    "api_key_accessed": False,
    "api_key_value_printed": False,
    "api_key_value_written": False,
    "api_key_leaked": False,
    "wallet_or_private_key_accessed": False,
    "orders_created": False,
    "orders_created_count": 0,
    "simulated_trade_created": False,
    "selected_side": None,
    "stake_amount": None,
    "position_sizing_created": False,
    "queue_items_created": 0,
    "queue_state_mutated": False,
    "runtime_wiring_added": False,
    "trading_runtime_changed": False,
    "dispatcher_changed": False,
    "background_worker_created": False,
    "background_workers_added": False,
    "browser_automation_used": False,
    "market_decisions_made": False,
    "outcome_checked": True,
    "outcome_known": False,
    "outcome_resolution_status": "unresolved",
    "final_outcome_resolved": False,
    "source_alignment_review_performed": False,
    "source_quality_update_performed": False,
    "source_scoring_performed": False,
    "source_ranking_updated": False,
    "profit_or_pnl_recorded": False,
    "profit_or_pnl_used_for_scoring": False,
    "canonical_packets_mutated": False,
    "market_action_guidance_generated": False,
    "probability_ev_edge_confidence_generated": False,
    "side_selection_generated": False,
    "ready_for_autonomous_trading": False,
}


def _parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Create local-only PAPERLIVE-006 source-quality pending ledger artifacts."
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


def _safe_list(value):
    return value if isinstance(value, list) else []


def _artifact_reference(path, role, stage=None, root=ROOT):
    payload = {
        "path": path,
        "role": role,
        "exists": _exists(path, root=root),
    }
    if stage is not None:
        payload["stage"] = stage
    return payload


def _artifact_references(root=ROOT):
    return [
        _artifact_reference(
            SOURCE_009A_RAW_FETCH_PATH,
            "public read-only raw market metadata snapshot",
            "009A",
            root=root,
        ),
        _artifact_reference(
            SOURCE_009A_NORMALIZED_CANDIDATE_PATH,
            "normalized market candidate",
            "009A",
            root=root,
        ),
        _artifact_reference(
            SOURCE_009A_CAPTURE_CANDIDATE_PATH,
            "source and rules capture candidate",
            "009A",
            root=root,
        ),
        _artifact_reference(
            SOURCE_009A_OPERATOR_CHECKLIST_PATH,
            "operator review checklist",
            "009A",
            root=root,
        ),
        _artifact_reference(
            SOURCE_009B_MANUAL_CAPTURE_PATH,
            "manual resolution source capture draft",
            "009B",
            root=root,
        ),
        _artifact_reference(
            SOURCE_009B_AUTOFILL_RESULT_PATH,
            "draft capture autofill result",
            "009B",
            root=root,
        ),
        _artifact_reference(
            SOURCE_009B_OPERATOR_SURFACE_PATH,
            "draft capture operator review surface",
            "009B",
            root=root,
        ),
        _artifact_reference(
            SOURCE_009B_SOURCE_QUALITY_PATH,
            "source-quality observation candidate",
            "009B",
            root=root,
        ),
        _artifact_reference(
            SOURCE_009C_OPERATOR_SURFACE_PATH,
            "operator review preparation surface",
            "009C",
            root=root,
        ),
        _artifact_reference(
            SOURCE_009C_OBSERVATION_PLAN_PATH,
            "paper-live observation plan",
            "009C",
            root=root,
        ),
        _artifact_reference(
            SOURCE_009C_OUTCOME_TRACKING_CONTRACT_PATH,
            "outcome tracking contract",
            "009C",
            root=root,
        ),
        _artifact_reference(
            SOURCE_009C_SOURCE_QUALITY_FLOW_PATH,
            "source-quality observation flow",
            "009C",
            root=root,
        ),
        _artifact_reference(
            SOURCE_009C_WORKBENCH_SURFACE_PATH,
            "paper-live preparation workbench surface",
            "009C",
            root=root,
        ),
        _artifact_reference(
            PAPERLIVE001_LEDGER_PATH,
            "paper-live observation ledger first run",
            "PAPERLIVE-001",
            root=root,
        ),
        _artifact_reference(
            PAPERLIVE001_SOURCE_QUALITY_PATH,
            "source-quality pending observation",
            "PAPERLIVE-001",
            root=root,
        ),
        _artifact_reference(
            PAPERLIVE001_OUTCOME_PLACEHOLDER_PATH,
            "outcome reconciliation placeholder",
            "PAPERLIVE-001",
            root=root,
        ),
        _artifact_reference(
            PAPERLIVE001_WORKBENCH_SURFACE_PATH,
            "paper-live observation workbench surface",
            "PAPERLIVE-001",
            root=root,
        ),
        _artifact_reference(
            PAPERLIVE002_MONITORING_PLAN_PATH,
            "outcome and source monitoring plan",
            "PAPERLIVE-002",
            root=root,
        ),
        _artifact_reference(
            PAPERLIVE002_CHECKLIST_PATH,
            "source monitoring checklist",
            "PAPERLIVE-002",
            root=root,
        ),
        _artifact_reference(
            PAPERLIVE002_FUTURE_OUTCOME_CHECK_PATH,
            "future read-only outcome check request",
            "PAPERLIVE-002",
            root=root,
        ),
        _artifact_reference(
            PAPERLIVE002_SOURCE_QUALITY_UPDATE_PLAN_PATH,
            "source-quality update plan",
            "PAPERLIVE-002",
            root=root,
        ),
        _artifact_reference(
            PAPERLIVE002_WORKBENCH_SURFACE_PATH,
            "monitoring plan workbench surface",
            "PAPERLIVE-002",
            root=root,
        ),
        _artifact_reference(
            PAPERLIVE003_PROTOCOL_PATH,
            "read-only outcome check protocol",
            "PAPERLIVE-003",
            root=root,
        ),
        _artifact_reference(
            PAPERLIVE003_RAW_FETCH_CONTRACT_PATH,
            "raw outcome fetch contract",
            "PAPERLIVE-003",
            root=root,
        ),
        _artifact_reference(
            PAPERLIVE003_NORMALIZED_CONTRACT_PATH,
            "normalized outcome evidence contract",
            "PAPERLIVE-003",
            root=root,
        ),
        _artifact_reference(
            PAPERLIVE003_ALIGNMENT_CONTRACT_PATH,
            "source alignment review contract",
            "PAPERLIVE-003",
            root=root,
        ),
        _artifact_reference(
            PAPERLIVE003_READINESS_GATE_PATH,
            "read-only outcome check readiness gate",
            "PAPERLIVE-003",
            root=root,
        ),
        _artifact_reference(
            PAPERLIVE003_WORKBENCH_SURFACE_PATH,
            "read-only outcome protocol workbench surface",
            "PAPERLIVE-003",
            root=root,
        ),
        _artifact_reference(
            PAPERLIVE004_RAW_FETCH_PATH,
            "controlled read-only outcome fetch evidence",
            "PAPERLIVE-004",
            root=root,
        ),
        _artifact_reference(
            PAPERLIVE004_NORMALIZED_EVIDENCE_PATH,
            "normalized outcome evidence",
            "PAPERLIVE-004",
            root=root,
        ),
        _artifact_reference(
            PAPERLIVE004_CALL_LEDGER_PATH,
            "outcome fetch call ledger",
            "PAPERLIVE-004",
            root=root,
        ),
        _artifact_reference(
            PAPERLIVE004_RECONCILIATION_INPUT_PATH,
            "reconciliation input",
            "PAPERLIVE-004",
            root=root,
        ),
        _artifact_reference(
            PAPERLIVE004_WORKBENCH_SURFACE_PATH,
            "outcome fetch workbench surface",
            "PAPERLIVE-004",
            root=root,
        ),
        _artifact_reference(
            PAPERLIVE005_RECONCILIATION_PATH,
            "outcome/source reconciliation assessment",
            "PAPERLIVE-005",
            root=root,
        ),
        _artifact_reference(
            PAPERLIVE005_RECONCILIATION_SUMMARY_PATH,
            "outcome/source reconciliation summary",
            "PAPERLIVE-005",
            root=root,
        ),
        _artifact_reference(
            PAPERLIVE005_ALIGNMENT_PENDING_PATH,
            "source alignment review pending artifact",
            "PAPERLIVE-005",
            root=root,
        ),
        _artifact_reference(
            PAPERLIVE005_SOURCE_QUALITY_PENDING_UPDATE_PATH,
            "source-quality pending update artifact",
            "PAPERLIVE-005",
            root=root,
        ),
        _artifact_reference(
            PAPERLIVE005_FUTURE_RECONCILIATION_REQUEST_PATH,
            "future reconciliation update request",
            "PAPERLIVE-005",
            root=root,
        ),
        _artifact_reference(
            PAPERLIVE005_WORKBENCH_SURFACE_PATH,
            "reconciliation workbench surface",
            "PAPERLIVE-005",
            root=root,
        ),
        _artifact_reference(
            INGEST_RESULT_PATH,
            "manual source capture ingest result",
            "readiness",
            root=root,
        ),
        _artifact_reference(
            INGEST_OVERLAY_PATH,
            "manual source capture ingested overlay",
            "readiness",
            root=root,
        ),
        _artifact_reference(
            READINESS_REPORT_PATH,
            "post-capture readiness report",
            "readiness",
            root=root,
        ),
        _artifact_reference(
            READINESS_GATE_PATH,
            "post-capture batch readiness gate",
            "readiness",
            root=root,
        ),
    ]


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


def _load_source_quality_inputs(root=ROOT):
    inputs = []
    for path in SOURCE_QUALITY_INPUT_PATHS:
        payload = _load_optional_json(path, root=root) or {}
        inputs.append(
            {
                "path": path,
                "schema_version": payload.get("schema_version"),
                "task_id": payload.get("task_id"),
                "market_id": payload.get("market_id"),
                "market_class": payload.get("market_class"),
                "status": (
                    payload.get("source_quality_status")
                    or payload.get("review_status")
                    or payload.get("update_status")
                    or "pending_artifact"
                ),
                "outcome_known": bool(payload.get("outcome_known", False)),
                "source_scoring_performed": bool(
                    payload.get("source_scoring_performed", False)
                ),
                "source_ranking_updated": bool(
                    payload.get("source_ranking_updated", False)
                ),
                "operator_review_required": bool(
                    payload.get("operator_review_required", True)
                ),
            }
        )
    return inputs


def _observed_sources(root=ROOT):
    source_quality_009b = _load_optional_json(SOURCE_009B_SOURCE_QUALITY_PATH, root=root) or {}
    source_quality_001 = _load_optional_json(PAPERLIVE001_SOURCE_QUALITY_PATH, root=root) or {}
    reconciliation_005 = _load_optional_json(PAPERLIVE005_RECONCILIATION_PATH, root=root) or {}
    source_ids = []
    source_ids.extend(_safe_list(source_quality_009b.get("source_ids_observed")))
    source_ids.extend(_safe_list(source_quality_001.get("source_ids_observed")))
    source_ids.extend(
        _safe_list(
            (
                reconciliation_005.get("normalized_evidence_summary", {})
                .get("result_source_reference", {})
                .get("metadata_urls")
            )
        )
    )
    source_ids.extend(
        _safe_list(
            (
                reconciliation_005.get("normalized_evidence_summary", {})
                .get("result_source_reference", {})
                .get("official_source_references_prepared", {})
                .get("public_urls")
            )
        )
    )
    source_ids.extend(
        [
            PAPERLIVE004_RAW_FETCH_PATH,
            PAPERLIVE004_NORMALIZED_EVIDENCE_PATH,
            PAPERLIVE005_RECONCILIATION_PATH,
        ]
    )

    role_map = {
        "source_009a_gamma_market_metadata_1987056": [
            "market_metadata_source",
            "market_rules_source",
        ],
        "source_009a_polymarket_gamma_rules_text_1987056": ["market_rules_source"],
        "https://gol.gg/esports/home": ["official_result_source_candidate"],
        "https://www.douyu.com/424559": ["tournament_or_match_context_source"],
        SOURCE_009B_MANUAL_CAPTURE_PATH: ["local_capture_source"],
        SOURCE_009C_OPERATOR_SURFACE_PATH: ["operator_review_surface"],
        PAPERLIVE001_LEDGER_PATH: ["paper_live_observation_source"],
        PAPERLIVE004_RAW_FETCH_PATH: ["outcome_fetch_source"],
        PAPERLIVE004_NORMALIZED_EVIDENCE_PATH: ["outcome_fetch_source"],
        PAPERLIVE005_RECONCILIATION_PATH: ["outcome_fetch_source", "unresolved_source"],
    }

    observed = []
    seen = set()
    for source_id in source_ids:
        if not isinstance(source_id, str) or source_id in seen:
            continue
        seen.add(source_id)
        observed.append(
            {
                "source_id": source_id,
                "roles": role_map.get(source_id, ["unresolved_source"]),
                "source_quality_status": "pending_outcome_resolution",
                "scoring_performed": False,
                "ranking_updated": False,
            }
        )
    return observed


def _reconciliation_snapshot(root=ROOT):
    reconciliation = _load_optional_json(PAPERLIVE005_RECONCILIATION_PATH, root=root) or {}
    summary = _load_optional_json(PAPERLIVE005_RECONCILIATION_SUMMARY_PATH, root=root) or {}
    normalized = _load_optional_json(PAPERLIVE004_NORMALIZED_EVIDENCE_PATH, root=root) or {}
    return {
        "outcome_checked": bool(
            reconciliation.get("outcome_checked", summary.get("outcome_checked", True))
        ),
        "outcome_known": bool(
            reconciliation.get("outcome_known", normalized.get("outcome_known", False))
        ),
        "outcome_resolution_status": (
            reconciliation.get("outcome_resolution_status")
            or normalized.get("outcome_resolution_status")
            or "unresolved"
        ),
        "final_outcome_resolved": bool(
            reconciliation.get("final_outcome_resolved", False)
        ),
        "source_alignment_review_performed": bool(
            reconciliation.get("source_alignment_review_performed", False)
        ),
        "source_quality_update_performed": bool(
            reconciliation.get("source_quality_update_performed", False)
        ),
        "source_scoring_performed": bool(
            reconciliation.get("source_scoring_performed", False)
        ),
        "source_ranking_updated": bool(
            reconciliation.get("source_ranking_updated", False)
        ),
        "profit_or_pnl_recorded": bool(
            reconciliation.get("profit_or_pnl_recorded", False)
        ),
        "future_reconciliation_required": bool(
            reconciliation.get("future_reconciliation_required", True)
        ),
        "future_outcome_check_required": bool(
            reconciliation.get("future_readonly_fetch_required", True)
        ),
    }


def _source_capture_status(pipeline):
    if (
        pipeline.get("real_ingested_template_count", 0) >= 2
        and pipeline.get("draft_ingested_template_count", 0) >= 2
        and pipeline.get("ready_ingested_template_count") == 0
    ):
        return "real_and_draft_templates_ingested_no_ready_templates"
    return "readiness_artifacts_present_pending_operator_review"


def _required_reusable_components_available(root=ROOT):
    return {
        "market_class_taxonomy": _exists(
            "pm_bot/llm/market_class_pilot_taxonomy.v1.json", root=root
        ),
        "read_only_discovery_pattern": _exists(
            SOURCE_009A_NORMALIZED_CANDIDATE_PATH, root=root
        ),
        "draft_capture_autofill_pattern": _exists(SOURCE_009B_AUTOFILL_RESULT_PATH, root=root),
        "paper_live_observation_pattern": _exists(PAPERLIVE001_LEDGER_PATH, root=root),
        "monitoring_plan_pattern": _exists(PAPERLIVE002_MONITORING_PLAN_PATH, root=root),
        "outcome_protocol_pattern": _exists(PAPERLIVE003_PROTOCOL_PATH, root=root),
        "controlled_fetch_pattern": _exists(PAPERLIVE004_RAW_FETCH_PATH, root=root),
        "reconciliation_pending_pattern": _exists(PAPERLIVE005_RECONCILIATION_PATH, root=root),
        "source_quality_pending_ledger_pattern": True,
    }


def _ready_for_weather(root=ROOT):
    reusable = _required_reusable_components_available(root=root)
    required_keys = [
        "market_class_taxonomy",
        "read_only_discovery_pattern",
        "draft_capture_autofill_pattern",
        "paper_live_observation_pattern",
        "monitoring_plan_pattern",
        "outcome_protocol_pattern",
        "controlled_fetch_pattern",
        "reconciliation_pending_pattern",
        "source_quality_pending_ledger_pattern",
    ]
    return all(bool(reusable.get(key)) for key in required_keys)


def build_source_quality_pending_ledger_entry(root=ROOT):
    reconciliation = _reconciliation_snapshot(root=root)
    return {
        "schema_version": "source_quality_pending_ledger_entry.v1",
        "task_id": TASK_ID,
        "generated_by": GENERATED_BY,
        "generated_at_marker": LOCAL_TIMESTAMP,
        "market_id": MARKET_ID,
        "market_class": MARKET_CLASS,
        "title_or_question": MARKET_TITLE,
        "ledger_mode": "pending_only_no_scoring",
        "outcome_known": False,
        "outcome_resolution_status": "unresolved",
        "source_quality_status": "pending_outcome_resolution",
        "source_scoring_performed": False,
        "source_ranking_updated": False,
        "profit_or_pnl_recorded": False,
        "profit_or_pnl_used_for_scoring": False,
        "source_alignment_review_performed": False,
        "source_quality_update_performed": False,
        "simulated_trade_created": False,
        "selected_side": None,
        "stake_amount": None,
        "order_created": False,
        "orders_created": False,
        "wallet_used": False,
        "wallet_or_private_key_accessed": False,
        "position_sizing_created": False,
        "observed_sources": _observed_sources(root=root),
        "source_roles": list(SOURCE_ROLES),
        "pending_alignment_dimensions": list(PENDING_ALIGNMENT_DIMENSIONS),
        "pending_update_requirements": list(PENDING_UPDATE_REQUIREMENTS),
        "blockers_to_scoring": list(BLOCKERS_TO_SCORING),
        "allowed_future_metrics": list(ALLOWED_FUTURE_METRICS),
        "forbidden_metrics": list(FORBIDDEN_METRICS),
        "source_quality_pending_inputs": _load_source_quality_inputs(root=root),
        "artifact_references": _artifact_references(root=root),
        "operator_review_required": True,
        "next_recommended_action": NEXT_WEATHER_TASK,
        "paperlive005_state_preserved": {
            "outcome_checked": reconciliation["outcome_checked"],
            "outcome_known": reconciliation["outcome_known"],
            "outcome_resolution_status": reconciliation["outcome_resolution_status"],
            "final_outcome_resolved": reconciliation["final_outcome_resolved"],
            "source_alignment_review_performed": reconciliation[
                "source_alignment_review_performed"
            ],
            "source_quality_update_performed": reconciliation[
                "source_quality_update_performed"
            ],
        },
        "no_market_action_guidance": True,
        "no_trading_authority": True,
        "safety_summary": dict(SAFETY_SUMMARY),
        "openrouter_calls_performed": 0,
        "polymarket_api_calls_performed": 0,
        "external_network_calls_performed": 0,
    }


def build_source_quality_pending_ledger_index(root=ROOT):
    return {
        "schema_version": "source_quality_pending_ledger_index.v1",
        "task_id": TASK_ID,
        "generated_by": GENERATED_BY,
        "generated_at_marker": LOCAL_TIMESTAMP,
        "status": "source_quality_scoring_pending_outcome_resolution",
        "pending_ledger_entries_count": 1,
        "markets": [
            {
                "market_id": MARKET_ID,
                "market_class": MARKET_CLASS,
                "source_quality_status": "pending_outcome_resolution",
                "outcome_known": False,
                "source_scoring_performed": False,
                "source_ranking_updated": False,
                "pending_update_reason": (
                    "outcome unresolved; source alignment review and source-quality "
                    "update remain pending"
                ),
                "ledger_entry_path": LEDGER_ENTRY_JSON_PATH,
            }
        ],
        "source_scoring_ready_count": 0,
        "source_scoring_pending_count": 1,
        "source_scoring_blocked_reasons": list(BLOCKERS_TO_SCORING),
        "no_market_action_guidance": True,
        "no_trading_authority": True,
        "safety_summary": dict(SAFETY_SUMMARY),
    }


def build_esports_contour_summary(root=ROOT):
    pipeline = _pipeline_snapshot(root=root)
    reconciliation = _reconciliation_snapshot(root=root)
    ready_for_weather = _ready_for_weather(root=root)
    return {
        "schema_version": "esports_paperlive_contour_summary.v1",
        "task_id": TASK_ID,
        "generated_by": GENERATED_BY,
        "generated_at_marker": LOCAL_TIMESTAMP,
        "market_id": MARKET_ID,
        "market_class": MARKET_CLASS,
        "title_or_question": MARKET_TITLE,
        "contour_status": (
            "esports_paperlive_observation_contour_established_"
            "pending_outcome_resolution"
        ),
        "stages_completed": [
            {
                "stage_id": "009A",
                "stage_name": "discovery",
                "status": "completed_local_artifact_available",
                "artifact_paths": [
                    SOURCE_009A_RAW_FETCH_PATH,
                    SOURCE_009A_NORMALIZED_CANDIDATE_PATH,
                    SOURCE_009A_CAPTURE_CANDIDATE_PATH,
                    SOURCE_009A_OPERATOR_CHECKLIST_PATH,
                ],
            },
            {
                "stage_id": "009B",
                "stage_name": "draft capture",
                "status": "completed_local_artifact_available",
                "artifact_paths": [
                    SOURCE_009B_MANUAL_CAPTURE_PATH,
                    SOURCE_009B_AUTOFILL_RESULT_PATH,
                    SOURCE_009B_OPERATOR_SURFACE_PATH,
                    SOURCE_009B_SOURCE_QUALITY_PATH,
                ],
            },
            {
                "stage_id": "009C",
                "stage_name": "operator review preparation",
                "status": "completed_local_artifact_available",
                "artifact_paths": [
                    SOURCE_009C_OPERATOR_SURFACE_PATH,
                    SOURCE_009C_OBSERVATION_PLAN_PATH,
                    SOURCE_009C_OUTCOME_TRACKING_CONTRACT_PATH,
                    SOURCE_009C_SOURCE_QUALITY_FLOW_PATH,
                    SOURCE_009C_WORKBENCH_SURFACE_PATH,
                ],
            },
            {
                "stage_id": "PAPERLIVE-001",
                "stage_name": "paper-live observation ledger",
                "status": "completed_local_artifact_available",
                "artifact_paths": [
                    PAPERLIVE001_LEDGER_PATH,
                    PAPERLIVE001_SOURCE_QUALITY_PATH,
                    PAPERLIVE001_OUTCOME_PLACEHOLDER_PATH,
                    PAPERLIVE001_WORKBENCH_SURFACE_PATH,
                ],
            },
            {
                "stage_id": "PAPERLIVE-002",
                "stage_name": "monitoring plan",
                "status": "completed_local_artifact_available",
                "artifact_paths": [
                    PAPERLIVE002_MONITORING_PLAN_PATH,
                    PAPERLIVE002_CHECKLIST_PATH,
                    PAPERLIVE002_FUTURE_OUTCOME_CHECK_PATH,
                    PAPERLIVE002_SOURCE_QUALITY_UPDATE_PLAN_PATH,
                    PAPERLIVE002_WORKBENCH_SURFACE_PATH,
                ],
            },
            {
                "stage_id": "PAPERLIVE-003",
                "stage_name": "readonly outcome protocol",
                "status": "completed_local_artifact_available",
                "artifact_paths": [
                    PAPERLIVE003_PROTOCOL_PATH,
                    PAPERLIVE003_RAW_FETCH_CONTRACT_PATH,
                    PAPERLIVE003_NORMALIZED_CONTRACT_PATH,
                    PAPERLIVE003_ALIGNMENT_CONTRACT_PATH,
                    PAPERLIVE003_READINESS_GATE_PATH,
                    PAPERLIVE003_WORKBENCH_SURFACE_PATH,
                ],
            },
            {
                "stage_id": "PAPERLIVE-004",
                "stage_name": "controlled readonly outcome fetch",
                "status": "completed_local_artifact_available",
                "artifact_paths": [
                    PAPERLIVE004_RAW_FETCH_PATH,
                    PAPERLIVE004_NORMALIZED_EVIDENCE_PATH,
                    PAPERLIVE004_CALL_LEDGER_PATH,
                    PAPERLIVE004_RECONCILIATION_INPUT_PATH,
                    PAPERLIVE004_WORKBENCH_SURFACE_PATH,
                ],
            },
            {
                "stage_id": "PAPERLIVE-005",
                "stage_name": "reconciliation assessment",
                "status": "completed_pending_outcome_resolution",
                "artifact_paths": [
                    PAPERLIVE005_RECONCILIATION_PATH,
                    PAPERLIVE005_RECONCILIATION_SUMMARY_PATH,
                    PAPERLIVE005_ALIGNMENT_PENDING_PATH,
                    PAPERLIVE005_SOURCE_QUALITY_PENDING_UPDATE_PATH,
                    PAPERLIVE005_FUTURE_RECONCILIATION_REQUEST_PATH,
                    PAPERLIVE005_WORKBENCH_SURFACE_PATH,
                ],
            },
            {
                "stage_id": "PAPERLIVE-006",
                "stage_name": "source-quality pending ledger",
                "status": "completed_by_this_task_when_written",
                "artifact_paths": [
                    LEDGER_ENTRY_JSON_PATH,
                    LEDGER_INDEX_JSON_PATH,
                    CONTOUR_SUMMARY_JSON_PATH,
                    HANDOFF_JSON_PATH,
                    WORKBENCH_SURFACE_JSON_PATH,
                ],
            },
        ],
        "stages_pending": [
            {
                "stage_id": "future_outcome_resolution_check",
                "status": "pending_explicit_future_approval",
                "reason": "outcome_known is false and outcome_resolution_status is unresolved",
            },
            {
                "stage_id": "future_source_alignment_review",
                "status": "pending_outcome_resolution",
                "reason": "source alignment review requires known final outcome evidence",
            },
            {
                "stage_id": "future_source_quality_update",
                "status": "pending_outcome_resolution",
                "reason": "source scoring and ranking are blocked while outcome is unresolved",
            },
        ],
        "discovery": "009A artifacts established a public read-only esports market candidate.",
        "draft_capture": "009B artifacts prepared local source/rules capture drafts.",
        "ingest_readiness": "Readiness artifacts preserve real and draft ingest counts without ready promotion.",
        "operator_review_preparation": "009C prepared operator review and paper-live observation surfaces.",
        "paper_live_observation_ledger": "PAPERLIVE-001 created the first observation ledger entry.",
        "monitoring_plan": "PAPERLIVE-002 created source/outcome monitoring plans.",
        "readonly_outcome_protocol": "PAPERLIVE-003 created a read-only outcome check protocol.",
        "controlled_readonly_outcome_fetch": "PAPERLIVE-004 captured local outcome evidence state.",
        "reconciliation_assessment": "PAPERLIVE-005 preserved unresolved reconciliation state.",
        "source_quality_pending_ledger": "PAPERLIVE-006 records pending source quality state without scoring.",
        "remaining_blockers": list(BLOCKERS_TO_SCORING),
        "next_recommended_action": NEXT_WEATHER_TASK,
        "outcome_checked": reconciliation["outcome_checked"],
        "outcome_known": False,
        "outcome_resolution_status": "unresolved",
        "final_outcome_resolved": False,
        "source_capture_status": _source_capture_status(pipeline),
        "real_ingested_template_count": pipeline.get("real_ingested_template_count"),
        "draft_ingested_template_count": pipeline.get("draft_ingested_template_count"),
        "ready_ingested_template_count": pipeline.get("ready_ingested_template_count"),
        "simulated_trade_created": False,
        "selected_side": None,
        "stake_amount": None,
        "source_scoring_performed": False,
        "source_ranking_updated": False,
        "market_action_guidance_generated": False,
        "probability_ev_edge_confidence_generated": False,
        "side_selection_generated": False,
        "future_reconciliation_required": reconciliation["future_reconciliation_required"],
        "future_outcome_check_required": reconciliation["future_outcome_check_required"],
        "ready_for_weather_pilot": ready_for_weather,
        "ready_for_autonomous_trading": False,
        "blockers_before_autonomous_trading": list(BLOCKERS_BEFORE_AUTONOMOUS_TRADING),
        "no_market_action_guidance": True,
        "no_trading_authority": True,
        "safety_summary": dict(SAFETY_SUMMARY),
    }


def build_esports_to_weather_handoff_readiness(root=ROOT):
    reusable = _required_reusable_components_available(root=root)
    ready_for_weather = _ready_for_weather(root=root)
    blockers = []
    if not ready_for_weather:
        blockers.append("one or more reusable paper-live contour components are missing")
    return {
        "schema_version": "esports_to_weather_handoff_readiness.v1",
        "task_id": TASK_ID,
        "generated_by": GENERATED_BY,
        "generated_at_marker": LOCAL_TIMESTAMP,
        "esports_market_id": MARKET_ID,
        "esports_contour_status": (
            "esports_paperlive_observation_contour_established_"
            "pending_outcome_resolution"
        ),
        "outcome_known": False,
        "source_quality_scoring_completed": False,
        "source_quality_scoring_required_before_weather": False,
        "weather_pilot_allowed": ready_for_weather,
        "recommended_next_weather_task": NEXT_WEATHER_TASK,
        "recommended_if_operator_wants_to_finish_esports_first": NEXT_ESPORTS_TASK,
        "required_reusable_components_available": reusable,
        "blockers": blockers,
        "warnings": [
            "esports outcome remains unresolved",
            "source quality scoring remains pending and must not be used for market action",
            "weather pilot remains read-only and manual-first",
        ],
        "no_market_action_guidance": True,
        "no_trading_authority": True,
        "ready_for_autonomous_trading": False,
        "safety_summary": dict(SAFETY_SUMMARY),
    }


def build_workbench_surface(root=ROOT):
    handoff = build_esports_to_weather_handoff_readiness(root=root)
    return {
        "schema_version": "esports_paperlive_contour_summary_surface_paperlive006.v1",
        "task_id": TASK_ID,
        "generated_by": GENERATED_BY,
        "generated_at_marker": LOCAL_TIMESTAMP,
        "market_id": MARKET_ID,
        "market_class": MARKET_CLASS,
        "contour_summary_available": True,
        "source_quality_pending_ledger_available": True,
        "handoff_readiness_available": True,
        "outcome_known": False,
        "source_scoring_performed": False,
        "source_ranking_updated": False,
        "source_alignment_review_performed": False,
        "source_quality_update_performed": False,
        "simulated_trade_created": False,
        "selected_side": None,
        "stake_amount": None,
        "ready_for_weather_pilot": handoff["weather_pilot_allowed"],
        "next_operator_actions": [
            f"review {LEDGER_ENTRY_JSON_PATH}",
            f"review {CONTOUR_SUMMARY_JSON_PATH}",
            f"start {NEXT_WEATHER_TASK} if operator accepts weather handoff",
            f"or start {NEXT_ESPORTS_TASK} if operator wants an esports-only handoff first",
        ],
        "queue_mutated": False,
        "runtime_wiring_changed": False,
        "trading_runtime_changed": False,
        "dispatcher_changed": False,
        "background_worker_created": False,
        "browser_automation_used": False,
        "canonical_packets_mutated": False,
        "no_market_action_guidance": True,
        "no_trading_authority": True,
        "safety_summary": dict(SAFETY_SUMMARY),
    }


def build_roadmap(root=ROOT):
    handoff = build_esports_to_weather_handoff_readiness(root=root)
    return {
        "schema_version": "pmbot_current_roadmap_after_paperlive006.v1",
        "task_id": TASK_ID,
        "generated_by": GENERATED_BY,
        "generated_at_marker": LOCAL_TIMESTAMP,
        "current_completed_esports_contour_status": (
            "paperlive contour established through source-quality pending ledger; "
            "outcome remains unresolved"
        ),
        "remaining_esports_tasks": [
            {
                "task_id": NEXT_ESPORTS_TASK,
                "status": "optional_next_if_operator_wants_to_finish_esports_first",
            },
            {
                "task_id": "future_outcome_resolution_reconciliation",
                "status": "pending_actual_outcome_resolution_and_explicit_future_approval",
            },
        ],
        "next_weather_pilot_task": NEXT_WEATHER_TASK,
        "weather_pilot_allowed_after_paperlive006": handoff["weather_pilot_allowed"],
        "rough_task_count_to_finish_esports_contour": (
            "1 task if only final summary/handoff is needed; more if waiting for actual outcome resolution"
        ),
        "rough_task_count_to_start_weather_pilot": "0-1 tasks after PAPERLIVE-006",
        "rough_task_count_to_autonomous_wallet_enabled_trading": "11-19 major tasks",
        "major_tasks_before_autonomous_wallet_enabled_trading": [
            "weather pilot",
            "crypto pilot",
            "simulated decision ledger",
            "risk engine",
            "position sizing",
            "execution mock",
            "supervised micro-execution",
            "wallet isolation",
            "kill switch",
            "audit/reconciliation",
            "limited autonomous mode",
        ],
        "ready_for_autonomous_trading": False,
        "no_market_action_guidance": True,
        "no_trading_authority": True,
        "safety_summary": dict(SAFETY_SUMMARY),
    }


def build_docs_result(root=ROOT, artifacts_created=False):
    pipeline = _pipeline_snapshot(root=root)
    handoff = build_esports_to_weather_handoff_readiness(root=root)
    return {
        "schema_version": "paperlive006_result.v1",
        "task_id": TASK_ID,
        "status": "completed_local" if artifacts_created else "dry_run_no_write",
        "market_id": MARKET_ID,
        "market_class": MARKET_CLASS,
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
        "outcome_checked": True,
        "outcome_known": False,
        "outcome_resolution_status": "unresolved",
        "final_outcome_resolved": False,
        "source_alignment_review_performed": False,
        "source_quality_update_performed": False,
        "source_scoring_performed": False,
        "source_ranking_updated": False,
        "profit_or_pnl_recorded": False,
        "profit_or_pnl_used_for_scoring": False,
        "trading_runtime_changed": False,
        "dispatcher_changed": False,
        "background_worker_created": False,
        "queue_mutated": False,
        "browser_automation_used": False,
        "canonical_packets_mutated": False,
        "market_action_guidance_generated": False,
        "probability_ev_edge_confidence_generated": False,
        "side_selection_generated": False,
        "source_quality_pending_ledger_entry_created": bool(artifacts_created),
        "source_quality_pending_ledger_index_created": bool(artifacts_created),
        "esports_contour_summary_created": bool(artifacts_created),
        "esports_to_weather_handoff_readiness_created": bool(artifacts_created),
        "passive_workbench_surface_created": bool(artifacts_created),
        "roadmap_updated": bool(artifacts_created),
        "ready_for_weather_pilot": handoff["weather_pilot_allowed"],
        "ready_for_autonomous_trading": False,
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
        "tests_passed": [],
        "tests_failed": [],
        "files_created": OUTPUT_PATHS if artifacts_created else [],
        "files_modified": [],
        "next_recommended_action": NEXT_WEATHER_TASK,
        "safety_summary": dict(SAFETY_SUMMARY),
    }


def build_artifacts(root=ROOT, artifacts_created=False):
    ledger_entry = build_source_quality_pending_ledger_entry(root=root)
    ledger_index = build_source_quality_pending_ledger_index(root=root)
    contour_summary = build_esports_contour_summary(root=root)
    handoff = build_esports_to_weather_handoff_readiness(root=root)
    workbench_surface = build_workbench_surface(root=root)
    roadmap = build_roadmap(root=root)
    docs_result = build_docs_result(root=root, artifacts_created=artifacts_created)
    return {
        "ledger_entry": ledger_entry,
        "ledger_index": ledger_index,
        "contour_summary": contour_summary,
        "handoff": handoff,
        "workbench_surface": workbench_surface,
        "roadmap": roadmap,
        "docs_result": docs_result,
    }


def _render_list(lines, items):
    for item in items:
        lines.append(f"- {item}")


def render_ledger_entry_markdown(entry):
    lines = [
        "# PMBOT PAPERLIVE-006 Source Quality Pending Ledger Entry",
        "",
        "PAPERLIVE-006 is local-only and records a pending source-quality ledger entry. It does not score or rank sources because the outcome is unresolved.",
        "",
        f"- task_id: {entry['task_id']}",
        f"- market_id: {entry['market_id']}",
        f"- market_class: {entry['market_class']}",
        f"- title_or_question: {entry['title_or_question']}",
        f"- ledger_mode: {entry['ledger_mode']}",
        "- outcome_known: false",
        "- outcome_resolution_status: unresolved",
        "- source_quality_status: pending_outcome_resolution",
        "- source_scoring_performed: false",
        "- source_ranking_updated: false",
        "- profit_or_pnl_recorded: false",
        "- profit_or_pnl_used_for_scoring: false",
        "- source_alignment_review_performed: false",
        "- source_quality_update_performed: false",
        "- simulated_trade_created: false",
        "- selected_side: null",
        "- stake_amount: null",
        "- order_created: false",
        "- wallet_used: false",
        "- position_sizing_created: false",
        "",
        "## Observed Sources",
        "",
    ]
    for source in entry["observed_sources"]:
        roles = ", ".join(source["roles"])
        lines.append(f"- {source['source_id']} ({roles})")
    lines.extend(["", "## Source Roles", ""])
    _render_list(lines, entry["source_roles"])
    lines.extend(["", "## Pending Alignment Dimensions", ""])
    _render_list(lines, entry["pending_alignment_dimensions"])
    lines.extend(["", "## Pending Update Requirements", ""])
    _render_list(lines, entry["pending_update_requirements"])
    lines.extend(["", "## Blockers To Scoring", ""])
    _render_list(lines, entry["blockers_to_scoring"])
    lines.extend(["", "## Allowed Future Metrics", ""])
    _render_list(lines, entry["allowed_future_metrics"])
    lines.extend(["", "## Forbidden Metrics", ""])
    for item in entry["forbidden_metrics"]:
        lines.append(f"- forbidden metric: {item}")
    lines.extend(
        [
            "",
            "## Operator Review",
            "",
            "- operator_review_required: true",
            f"- next_recommended_action: {entry['next_recommended_action']}",
            "",
            "## Safety",
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
            "- no probability, EV, edge, confidence, or side selection guidance",
            "- no source scoring or source ranking",
            "- no runtime change, no dispatcher change, no background worker change, no queue mutation, no browser automation, and no canonical packet changes",
        ]
    )
    return "\n".join(lines)


def render_ledger_index_markdown(index):
    lines = [
        "# PMBOT PAPERLIVE-006 Source Quality Pending Ledger Index",
        "",
        f"- task_id: {index['task_id']}",
        f"- status: {index['status']}",
        f"- pending_ledger_entries_count: {index['pending_ledger_entries_count']}",
        "- source_scoring_ready_count: 0",
        f"- source_scoring_pending_count: {index['source_scoring_pending_count']}",
        "- no_market_action_guidance: true",
        "- no_trading_authority: true",
        "",
        "## Markets",
        "",
    ]
    for market in index["markets"]:
        lines.append(
            "- "
            f"{market['market_id']} {market['market_class']} "
            f"{market['source_quality_status']} "
            f"ledger={market['ledger_entry_path']}"
        )
    lines.extend(["", "## Blocked Reasons", ""])
    _render_list(lines, index["source_scoring_blocked_reasons"])
    return "\n".join(lines)


def render_contour_summary_markdown(summary):
    lines = [
        "# PMBOT PAPERLIVE-006 Esports Paper-Live Contour Summary",
        "",
        "This contour summary covers 009A through PAPERLIVE-005 and adds the PAPERLIVE-006 pending ledger. It does not resolve the outcome.",
        "",
        f"- task_id: {summary['task_id']}",
        f"- market_id: {summary['market_id']}",
        f"- market_class: {summary['market_class']}",
        f"- title_or_question: {summary['title_or_question']}",
        f"- contour_status: {summary['contour_status']}",
        "- outcome_checked: true",
        "- outcome_known: false",
        "- outcome_resolution_status: unresolved",
        "- final_outcome_resolved: false",
        f"- source_capture_status: {summary['source_capture_status']}",
        f"- real_ingested_template_count: {summary['real_ingested_template_count']}",
        f"- draft_ingested_template_count: {summary['draft_ingested_template_count']}",
        f"- ready_ingested_template_count: {summary['ready_ingested_template_count']}",
        "- simulated_trade_created: false",
        "- selected_side: null",
        "- stake_amount: null",
        "- source_scoring_performed: false",
        "- source_ranking_updated: false",
        "- market_action_guidance_generated: false",
        "- probability_ev_edge_confidence_generated: false",
        "- side_selection_generated: false",
        f"- future_reconciliation_required: {str(summary['future_reconciliation_required']).lower()}",
        f"- future_outcome_check_required: {str(summary['future_outcome_check_required']).lower()}",
        f"- ready_for_weather_pilot: {str(summary['ready_for_weather_pilot']).lower()}",
        "- ready_for_autonomous_trading: false",
        "",
        "## Stages Completed",
        "",
    ]
    for stage in summary["stages_completed"]:
        lines.append(f"- {stage['stage_id']}: {stage['stage_name']} ({stage['status']})")
    lines.extend(["", "## Stages Pending", ""])
    for stage in summary["stages_pending"]:
        lines.append(f"- {stage['stage_id']}: {stage['status']} because {stage['reason']}")
    lines.extend(["", "## Remaining Blockers", ""])
    _render_list(lines, summary["remaining_blockers"])
    lines.extend(["", "## Next", "", f"- next_recommended_action: {summary['next_recommended_action']}"])
    lines.extend(
        [
            "",
            "## Safety",
            "",
            "- local-only",
            "- no network/API calls",
            "- no source scoring or source ranking while outcome is unresolved",
            "- no profit or PnL scoring",
            "- no simulated trade, no selected side, no stake, no orders, no wallet use, no runtime mutation, no queue mutation, and no canonical packet mutation",
        ]
    )
    return "\n".join(lines)


def render_handoff_markdown(handoff):
    lines = [
        "# PMBOT PAPERLIVE-006 Esports To Weather Handoff Readiness",
        "",
        "This artifact decides whether the read-only weather pilot can start while the esports outcome remains pending.",
        "",
        f"- task_id: {handoff['task_id']}",
        f"- esports_market_id: {handoff['esports_market_id']}",
        f"- esports_contour_status: {handoff['esports_contour_status']}",
        "- outcome_known: false",
        "- source_quality_scoring_completed: false",
        "- source_quality_scoring_required_before_weather: false",
        f"- weather_pilot_allowed: {str(handoff['weather_pilot_allowed']).lower()}",
        f"- recommended_next_weather_task: {handoff['recommended_next_weather_task']}",
        "- no_market_action_guidance: true",
        "- no_trading_authority: true",
        "",
        "## Reusable Components",
        "",
    ]
    for key, value in handoff["required_reusable_components_available"].items():
        lines.append(f"- {key}: {str(value).lower()}")
    lines.extend(["", "## Blockers", ""])
    if handoff["blockers"]:
        _render_list(lines, handoff["blockers"])
    else:
        lines.append("- none for read-only weather pilot handoff")
    lines.extend(["", "## Warnings", ""])
    _render_list(lines, handoff["warnings"])
    lines.extend(
        [
            "",
            "## Alternate Next Step",
            "",
            f"- if operator wants to finish esports first: {handoff['recommended_if_operator_wants_to_finish_esports_first']}",
        ]
    )
    return "\n".join(lines)


def render_workbench_surface_markdown(surface):
    lines = [
        "# PMBOT PAPERLIVE-006 Passive Workbench Summary Surface",
        "",
        f"- task_id: {surface['task_id']}",
        f"- market_id: {surface['market_id']}",
        f"- market_class: {surface['market_class']}",
        "- contour_summary_available: true",
        "- source_quality_pending_ledger_available: true",
        "- handoff_readiness_available: true",
        "- outcome_known: false",
        "- source_scoring_performed: false",
        "- simulated_trade_created: false",
        "- selected_side: null",
        "- stake_amount: null",
        f"- ready_for_weather_pilot: {str(surface['ready_for_weather_pilot']).lower()}",
        "- no_market_action_guidance: true",
        "- no_trading_authority: true",
        "",
        "## Next Operator Actions",
        "",
    ]
    _render_list(lines, surface["next_operator_actions"])
    lines.extend(
        [
            "",
            "## Safety",
            "",
            "- no queue mutation",
            "- no runtime change",
            "- no dispatcher change",
            "- no browser automation",
            "- no canonical packet mutation",
        ]
    )
    return "\n".join(lines)


def render_roadmap_markdown(roadmap):
    lines = [
        "# PMBOT Current Roadmap After PAPERLIVE-006",
        "",
        f"- task_id: {roadmap['task_id']}",
        f"- current_completed_esports_contour_status: {roadmap['current_completed_esports_contour_status']}",
        f"- next_weather_pilot_task: {roadmap['next_weather_pilot_task']}",
        f"- weather_pilot_allowed_after_paperlive006: {str(roadmap['weather_pilot_allowed_after_paperlive006']).lower()}",
        f"- rough_task_count_to_finish_esports_contour: {roadmap['rough_task_count_to_finish_esports_contour']}",
        f"- rough_task_count_to_start_weather_pilot: {roadmap['rough_task_count_to_start_weather_pilot']}",
        f"- rough_task_count_to_autonomous_wallet_enabled_trading: {roadmap['rough_task_count_to_autonomous_wallet_enabled_trading']}",
        "- ready_for_autonomous_trading: false",
        "- no_market_action_guidance: true",
        "- no_trading_authority: true",
        "",
        "## Remaining Esports Tasks",
        "",
    ]
    for task in roadmap["remaining_esports_tasks"]:
        lines.append(f"- {task['task_id']}: {task['status']}")
    lines.extend(["", "## Major Tasks Before Autonomous Wallet-Enabled Trading", ""])
    _render_list(lines, roadmap["major_tasks_before_autonomous_wallet_enabled_trading"])
    return "\n".join(lines)


def render_docs_markdown(result):
    return "\n".join(
        [
            "# PMBOT PAPERLIVE-006 Esports Source Quality Pending Ledger And Summary No Trade",
            "",
            "PAPERLIVE-006 is local-only. It consumes 009A through PAPERLIVE-005 artifacts and creates passive pending ledger, contour summary, handoff, workbench, roadmap, and result artifacts.",
            "",
            "## Result",
            "",
            "- outcome_checked: true",
            "- outcome_known: false",
            "- outcome_resolution_status: unresolved",
            "- source_quality_status: pending_outcome_resolution",
            "- source_quality_pending_ledger_entry_created: true",
            "- source_quality_pending_ledger_index_created: true",
            "- esports_contour_summary_created: true",
            f"- ready_for_weather_pilot: {str(result['ready_for_weather_pilot']).lower()}",
            "- ready_for_autonomous_trading: false",
            "",
            "## Boundaries",
            "",
            "- no network/API calls",
            "- no OpenRouter calls",
            "- no Polymarket API calls",
            "- no source scoring or source ranking while outcome is unresolved",
            "- no profit or PnL use",
            "- no simulated trade",
            "- no side chosen",
            "- no stake",
            "- no probability, EV, edge, or confidence",
            "- no orders",
            "- no wallet use",
            "- no runtime mutation, no queue mutation, and no canonical packet mutation",
            "- weather pilot can start if handoff readiness allows it",
            "- autonomous trading remains not ready",
        ]
    )


def write_artifacts(root=ROOT):
    artifacts = build_artifacts(root=root, artifacts_created=True)
    _write_json(LEDGER_ENTRY_JSON_PATH, artifacts["ledger_entry"], root=root)
    _write_text(
        LEDGER_ENTRY_MD_PATH,
        render_ledger_entry_markdown(artifacts["ledger_entry"]),
        root=root,
    )
    _write_json(LEDGER_INDEX_JSON_PATH, artifacts["ledger_index"], root=root)
    _write_text(
        LEDGER_INDEX_MD_PATH,
        render_ledger_index_markdown(artifacts["ledger_index"]),
        root=root,
    )
    _write_json(CONTOUR_SUMMARY_JSON_PATH, artifacts["contour_summary"], root=root)
    _write_text(
        CONTOUR_SUMMARY_MD_PATH,
        render_contour_summary_markdown(artifacts["contour_summary"]),
        root=root,
    )
    _write_json(HANDOFF_JSON_PATH, artifacts["handoff"], root=root)
    _write_text(HANDOFF_MD_PATH, render_handoff_markdown(artifacts["handoff"]), root=root)
    _write_json(WORKBENCH_SURFACE_JSON_PATH, artifacts["workbench_surface"], root=root)
    _write_text(
        WORKBENCH_SURFACE_MD_PATH,
        render_workbench_surface_markdown(artifacts["workbench_surface"]),
        root=root,
    )
    _write_json(ROADMAP_JSON_PATH, artifacts["roadmap"], root=root)
    _write_text(ROADMAP_MD_PATH, render_roadmap_markdown(artifacts["roadmap"]), root=root)
    _write_json(DOC_RESULT_JSON_PATH, artifacts["docs_result"], root=root)
    _write_text(DOC_RESULT_MD_PATH, render_docs_markdown(artifacts["docs_result"]), root=root)
    return artifacts["docs_result"]


def build_dry_run(root=ROOT):
    artifacts = build_artifacts(root=root, artifacts_created=False)
    return {
        "schema_version": "source_quality_pending_ledger_dry_run.v1",
        "task_id": TASK_ID,
        "status": "dry_run_no_write",
        "dry_run": True,
        "market_id": MARKET_ID,
        "market_class": MARKET_CLASS,
        "planned_output_paths": list(OUTPUT_PATHS),
        "files_written": [],
        "outcome_known": False,
        "outcome_resolution_status": "unresolved",
        "source_scoring_performed": False,
        "source_ranking_updated": False,
        "ready_for_weather_pilot": artifacts["handoff"]["weather_pilot_allowed"],
        "summary": artifacts["docs_result"],
        "safety_summary": dict(SAFETY_SUMMARY),
        "openrouter_calls_performed": 0,
        "polymarket_api_calls_performed": 0,
        "external_network_calls_performed": 0,
    }


def build_summary_only(root=ROOT):
    ledger = _load_optional_json(LEDGER_ENTRY_JSON_PATH, root=root)
    index = _load_optional_json(LEDGER_INDEX_JSON_PATH, root=root)
    contour = _load_optional_json(CONTOUR_SUMMARY_JSON_PATH, root=root)
    handoff = _load_optional_json(HANDOFF_JSON_PATH, root=root)
    surface = _load_optional_json(WORKBENCH_SURFACE_JSON_PATH, root=root)
    roadmap = _load_optional_json(ROADMAP_JSON_PATH, root=root)
    docs_result = _load_optional_json(DOC_RESULT_JSON_PATH, root=root)
    pipeline = _pipeline_snapshot(root=root)
    return {
        "schema_version": "source_quality_pending_ledger_summary_only.v1",
        "task_id": TASK_ID,
        "status": "summary_only",
        "market_id": MARKET_ID,
        "market_class": MARKET_CLASS,
        "source_quality_pending_ledger_entry_exists": ledger is not None,
        "source_quality_pending_ledger_index_exists": index is not None,
        "esports_contour_summary_exists": contour is not None,
        "esports_to_weather_handoff_readiness_exists": handoff is not None,
        "passive_workbench_surface_exists": surface is not None,
        "roadmap_exists": roadmap is not None,
        "docs_result_exists": docs_result is not None,
        "outcome_checked": True,
        "outcome_known": False,
        "outcome_resolution_status": "unresolved",
        "source_scoring_ready_count": (index or {}).get("source_scoring_ready_count"),
        "source_scoring_pending_count": (index or {}).get("source_scoring_pending_count"),
        "ready_for_weather_pilot": (handoff or {}).get("weather_pilot_allowed"),
        "ready_for_autonomous_trading": False,
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
