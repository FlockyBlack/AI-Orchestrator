import argparse
import json
from pathlib import Path


TASK_ID = "PMBOT-PAPERLIVE-003-ESPORTS-READONLY-OUTCOME-CHECK-PROTOCOL-NO-TRADE"
GENERATED_BY = "pm_bot/paper_live/esports_readonly_outcome_check_protocol.py"

ROOT = Path(__file__).resolve().parents[2]

MARKET_ID = "1987056"
MARKET_CLASS = "esports"
MARKET_TITLE = (
    "LoL: JD Gaming vs Anyone's Legend (BO5) - Esports World Cup China Qualifier Phase 2"
)
LOCAL_TIMESTAMP = "2026-05-08 Asia/Tbilisi"

DISCOVERY_DIR = "pm_bot/live_readonly/esports_market_discovery"
RAW_FETCH_009A_PATH = f"{DISCOVERY_DIR}/esports_market_raw_fetch_009a.v1.json"
NORMALIZED_CANDIDATE_009A_PATH = (
    f"{DISCOVERY_DIR}/esports_market_normalized_candidate_009a.v1.json"
)
SOURCE_CAPTURE_CANDIDATE_009A_PATH = (
    f"{DISCOVERY_DIR}/esports_source_capture_candidate_009a.v1.json"
)
CAPTURE_009B_PATH = (
    "pm_bot/llm/manual_resolution_source_capture/"
    f"{MARKET_ID}_resolution_source_capture.v1.json"
)
OPERATOR_SURFACE_009C_PATH = (
    "pm_bot/llm/esports_operator_review_surface_1987056_009c.v1.json"
)
OBSERVATION_PLAN_009C_PATH = (
    "pm_bot/paper_live/esports_observation_plan_1987056_009c.v1.json"
)
OUTCOME_TRACKING_CONTRACT_009C_PATH = "pm_bot/paper_live/outcome_tracking_contract.v1.json"
SOURCE_QUALITY_FLOW_009C_PATH = (
    "pm_bot/llm/source_quality_observation_flow_009c.v1.json"
)

INGEST_RESULT_PATH = "pm_bot/llm/manual_resolution_source_capture_ingest_result.v1.json"
INGEST_OVERLAY_PATH = "pm_bot/llm/manual_resolution_source_capture_ingested_overlay.v1.json"
READINESS_REPORT_PATH = "pm_bot/llm/post_capture_readiness_report.v1.json"
READINESS_GATE_PATH = "pm_bot/llm/post_capture_batch_readiness_gate.v1.json"

PAPERLIVE001_LEDGER_PATH = (
    "pm_bot/paper_live/esports_observation_ledger_first_run_1987056.v1.json"
)
PAPERLIVE001_SOURCE_QUALITY_PATH = (
    "pm_bot/llm/source_quality_pending_observation_1987056_paperlive001.v1.json"
)
PAPERLIVE001_OUTCOME_PLACEHOLDER_PATH = (
    "pm_bot/paper_live/esports_outcome_reconciliation_placeholder_1987056.v1.json"
)

PAPERLIVE002_MONITORING_PLAN_PATH = (
    "pm_bot/paper_live/"
    "esports_outcome_source_monitoring_plan_1987056_paperlive002.v1.json"
)
PAPERLIVE002_CHECKLIST_PATH = (
    "pm_bot/paper_live/"
    "esports_source_monitoring_checklist_1987056_paperlive002.v1.json"
)
PAPERLIVE002_FUTURE_REQUEST_PATH = (
    "pm_bot/paper_live/esports_future_readonly_outcome_check_request_1987056.v1.json"
)
PAPERLIVE002_SOURCE_QUALITY_UPDATE_PLAN_PATH = (
    "pm_bot/llm/source_quality_update_plan_1987056_paperlive002.v1.json"
)
PAPERLIVE002_WORKBENCH_SURFACE_PATH = (
    "pm_bot/workbench/esports_monitoring_plan_surface_1987056_paperlive002.v1.json"
)

PROTOCOL_JSON_PATH = (
    "pm_bot/paper_live/"
    "esports_readonly_outcome_check_protocol_1987056_paperlive003.v1.json"
)
PROTOCOL_MD_PATH = (
    "pm_bot/paper_live/"
    "esports_readonly_outcome_check_protocol_1987056_paperlive003.v1.md"
)
RAW_FETCH_CONTRACT_JSON_PATH = (
    "pm_bot/paper_live/"
    "esports_outcome_raw_fetch_contract_1987056_paperlive003.v1.json"
)
RAW_FETCH_CONTRACT_MD_PATH = (
    "pm_bot/paper_live/"
    "esports_outcome_raw_fetch_contract_1987056_paperlive003.v1.md"
)
NORMALIZED_EVIDENCE_CONTRACT_JSON_PATH = (
    "pm_bot/paper_live/"
    "esports_normalized_outcome_evidence_contract_1987056_paperlive003.v1.json"
)
NORMALIZED_EVIDENCE_CONTRACT_MD_PATH = (
    "pm_bot/paper_live/"
    "esports_normalized_outcome_evidence_contract_1987056_paperlive003.v1.md"
)
SOURCE_ALIGNMENT_REVIEW_CONTRACT_JSON_PATH = (
    "pm_bot/llm/source_alignment_review_contract_1987056_paperlive003.v1.json"
)
SOURCE_ALIGNMENT_REVIEW_CONTRACT_MD_PATH = (
    "pm_bot/llm/source_alignment_review_contract_1987056_paperlive003.v1.md"
)
READINESS_GATE_JSON_PATH = (
    "pm_bot/paper_live/"
    "esports_readonly_outcome_check_readiness_gate_1987056_paperlive003.v1.json"
)
READINESS_GATE_MD_PATH = (
    "pm_bot/paper_live/"
    "esports_readonly_outcome_check_readiness_gate_1987056_paperlive003.v1.md"
)
WORKBENCH_SURFACE_JSON_PATH = (
    "pm_bot/workbench/"
    "esports_readonly_outcome_check_protocol_surface_1987056_paperlive003.v1.json"
)
WORKBENCH_SURFACE_MD_PATH = (
    "pm_bot/workbench/"
    "esports_readonly_outcome_check_protocol_surface_1987056_paperlive003.v1.md"
)
RUN_SUMMARY_JSON_PATH = (
    "pm_bot/paper_live/esports_readonly_outcome_check_protocol_summary.v1.json"
)
RUN_SUMMARY_MD_PATH = (
    "pm_bot/paper_live/esports_readonly_outcome_check_protocol_summary.v1.md"
)
DOC_RESULT_JSON_PATH = "docs/PMBOT_PAPERLIVE_003_RESULT.json"
DOC_RESULT_MD_PATH = (
    "docs/PMBOT_PAPERLIVE_003_ESPORTS_READONLY_OUTCOME_CHECK_PROTOCOL_NO_TRADE.md"
)

INPUT_JSON_PATHS = [
    PAPERLIVE002_MONITORING_PLAN_PATH,
    PAPERLIVE002_CHECKLIST_PATH,
    PAPERLIVE002_FUTURE_REQUEST_PATH,
    PAPERLIVE002_SOURCE_QUALITY_UPDATE_PLAN_PATH,
    PAPERLIVE002_WORKBENCH_SURFACE_PATH,
    PAPERLIVE001_LEDGER_PATH,
    PAPERLIVE001_SOURCE_QUALITY_PATH,
    PAPERLIVE001_OUTCOME_PLACEHOLDER_PATH,
    OPERATOR_SURFACE_009C_PATH,
    OBSERVATION_PLAN_009C_PATH,
    OUTCOME_TRACKING_CONTRACT_009C_PATH,
    SOURCE_QUALITY_FLOW_009C_PATH,
    CAPTURE_009B_PATH,
    RAW_FETCH_009A_PATH,
    NORMALIZED_CANDIDATE_009A_PATH,
    SOURCE_CAPTURE_CANDIDATE_009A_PATH,
    INGEST_RESULT_PATH,
    INGEST_OVERLAY_PATH,
    READINESS_REPORT_PATH,
    READINESS_GATE_PATH,
]

JSON_OUTPUT_PATHS = [
    PROTOCOL_JSON_PATH,
    RAW_FETCH_CONTRACT_JSON_PATH,
    NORMALIZED_EVIDENCE_CONTRACT_JSON_PATH,
    SOURCE_ALIGNMENT_REVIEW_CONTRACT_JSON_PATH,
    READINESS_GATE_JSON_PATH,
    WORKBENCH_SURFACE_JSON_PATH,
    RUN_SUMMARY_JSON_PATH,
    DOC_RESULT_JSON_PATH,
]

MARKDOWN_OUTPUT_PATHS = [
    PROTOCOL_MD_PATH,
    RAW_FETCH_CONTRACT_MD_PATH,
    NORMALIZED_EVIDENCE_CONTRACT_MD_PATH,
    SOURCE_ALIGNMENT_REVIEW_CONTRACT_MD_PATH,
    READINESS_GATE_MD_PATH,
    WORKBENCH_SURFACE_MD_PATH,
    RUN_SUMMARY_MD_PATH,
    DOC_RESULT_MD_PATH,
]

OUTPUT_PATHS = [
    PROTOCOL_JSON_PATH,
    PROTOCOL_MD_PATH,
    RAW_FETCH_CONTRACT_JSON_PATH,
    RAW_FETCH_CONTRACT_MD_PATH,
    NORMALIZED_EVIDENCE_CONTRACT_JSON_PATH,
    NORMALIZED_EVIDENCE_CONTRACT_MD_PATH,
    SOURCE_ALIGNMENT_REVIEW_CONTRACT_JSON_PATH,
    SOURCE_ALIGNMENT_REVIEW_CONTRACT_MD_PATH,
    READINESS_GATE_JSON_PATH,
    READINESS_GATE_MD_PATH,
    WORKBENCH_SURFACE_JSON_PATH,
    WORKBENCH_SURFACE_MD_PATH,
    RUN_SUMMARY_JSON_PATH,
    RUN_SUMMARY_MD_PATH,
    DOC_RESULT_JSON_PATH,
    DOC_RESULT_MD_PATH,
]

ALLOWED_FUTURE_SOURCE_CATEGORIES = [
    "public read-only Polymarket/Gamma market metadata or resolution status",
    "official tournament/match result source, if available",
    "fallback credible match result source, if official result source unavailable",
    "local PMBOT artifacts already captured",
]

ALLOWED_FUTURE_ENDPOINT_OR_URL_CATEGORIES = [
    "public read-only market metadata or resolution status URL for the allowlisted market",
    "public official tournament or match result URL for the same match identity",
    "public fallback credible result URL only if official result source is unavailable",
    "local PMBOT artifact paths already present in this repository",
]

FORBIDDEN_FUTURE_ACTIONS = [
    "auth",
    "wallet",
    "private key",
    "orders",
    "trading",
    "CLOB execution",
    "browser automation",
    "market action recommendation",
    "probability/EV/edge/confidence generation",
    "side selection",
    "source scoring by profit",
]

SAFETY_SUMMARY = {
    "no_market_action_guidance": True,
    "operator_review_only": True,
    "analysis_only": True,
    "protocol_only": True,
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
    "dispatcher_changed": False,
    "background_workers_added": False,
    "browser_automation_used": False,
    "market_decisions_made": False,
    "outcome_checked": False,
    "outcome_known": False,
    "source_alignment_review_performed": False,
    "source_scoring_performed": False,
    "source_ranking_updated": False,
    "profit_or_pnl_recorded": False,
    "canonical_packets_mutated": False,
}


def _parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Create local-only esports readonly outcome check protocol artifacts."
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--protocol-only",
        action="store_true",
        help="Build the protocol package in memory only.",
    )
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


def _artifact_reference(path, role, root=ROOT):
    return {
        "path": path,
        "role": role,
        "exists": _exists(path, root=root),
    }


def _source_references(root=ROOT):
    return [
        _artifact_reference(
            RAW_FETCH_009A_PATH,
            "SOURCE-009A public read-only raw market metadata snapshot",
            root=root,
        ),
        _artifact_reference(
            NORMALIZED_CANDIDATE_009A_PATH,
            "SOURCE-009A normalized market candidate",
            root=root,
        ),
        _artifact_reference(
            SOURCE_CAPTURE_CANDIDATE_009A_PATH,
            "SOURCE-009A stored source/rules capture candidate",
            root=root,
        ),
        _artifact_reference(
            CAPTURE_009B_PATH,
            "SOURCE-009B manual resolution source capture draft",
            root=root,
        ),
        _artifact_reference(
            OPERATOR_SURFACE_009C_PATH,
            "SOURCE-009C operator review surface",
            root=root,
        ),
        _artifact_reference(
            OBSERVATION_PLAN_009C_PATH,
            "SOURCE-009C paper-live observation plan",
            root=root,
        ),
        _artifact_reference(
            OUTCOME_TRACKING_CONTRACT_009C_PATH,
            "SOURCE-009C outcome tracking contract",
            root=root,
        ),
        _artifact_reference(
            SOURCE_QUALITY_FLOW_009C_PATH,
            "SOURCE-009C source quality observation flow",
            root=root,
        ),
        _artifact_reference(
            PAPERLIVE001_LEDGER_PATH,
            "PAPERLIVE-001 observation ledger",
            root=root,
        ),
        _artifact_reference(
            PAPERLIVE001_SOURCE_QUALITY_PATH,
            "PAPERLIVE-001 source quality pending observation",
            root=root,
        ),
        _artifact_reference(
            PAPERLIVE001_OUTCOME_PLACEHOLDER_PATH,
            "PAPERLIVE-001 outcome reconciliation placeholder",
            root=root,
        ),
        _artifact_reference(
            PAPERLIVE002_MONITORING_PLAN_PATH,
            "PAPERLIVE-002 monitoring plan",
            root=root,
        ),
        _artifact_reference(
            PAPERLIVE002_CHECKLIST_PATH,
            "PAPERLIVE-002 source monitoring checklist",
            root=root,
        ),
        _artifact_reference(
            PAPERLIVE002_FUTURE_REQUEST_PATH,
            "PAPERLIVE-002 future readonly outcome check request",
            root=root,
        ),
        _artifact_reference(
            PAPERLIVE002_SOURCE_QUALITY_UPDATE_PLAN_PATH,
            "PAPERLIVE-002 source quality update plan",
            root=root,
        ),
    ]


def build_protocol(root=ROOT):
    return {
        "schema_version": "paper_live_readonly_outcome_check_protocol.v1",
        "task_id": TASK_ID,
        "generated_by": GENERATED_BY,
        "generated_at_marker": LOCAL_TIMESTAMP,
        "market_id": MARKET_ID,
        "market_class": MARKET_CLASS,
        "title_or_question": MARKET_TITLE,
        "protocol_mode": "protocol_only_no_fetch",
        "outcome_checked": False,
        "outcome_known": False,
        "future_fetch_required": True,
        "explicit_network_approval_required": True,
        "allowed_future_source_categories": list(ALLOWED_FUTURE_SOURCE_CATEGORIES),
        "allowed_future_endpoint_or_url_categories": list(
            ALLOWED_FUTURE_ENDPOINT_OR_URL_CATEGORIES
        ),
        "forbidden_future_actions": list(FORBIDDEN_FUTURE_ACTIONS),
        "future_fetch_limits": {
            "max_markets": 1,
            "market_id_allowlist": [MARKET_ID],
            "market_class_allowlist": [MARKET_CLASS],
            "public_readonly_only": True,
            "no_auth_headers": True,
            "timeout_required": True,
            "raw_response_preserved": True,
            "normalized_evidence_required": True,
        },
        "future_artifact_contracts": {
            "raw_fetch_contract": RAW_FETCH_CONTRACT_JSON_PATH,
            "normalized_outcome_evidence_contract": NORMALIZED_EVIDENCE_CONTRACT_JSON_PATH,
            "source_alignment_review_contract": SOURCE_ALIGNMENT_REVIEW_CONTRACT_JSON_PATH,
            "readiness_gate": READINESS_GATE_JSON_PATH,
        },
        "source_quality_update_plan_reference": PAPERLIVE002_SOURCE_QUALITY_UPDATE_PLAN_PATH,
        "source_alignment_review_required_later": True,
        "source_quality_update_planned_not_performed": True,
        "operator_review_required": True,
        "source_references": _source_references(root=root),
        "safety_summary": dict(SAFETY_SUMMARY),
        "openrouter_calls_performed": 0,
        "polymarket_api_calls_performed": 0,
        "external_network_calls_performed": 0,
    }


def build_raw_fetch_contract(root=ROOT):
    return {
        "contract_version": "esports_outcome_raw_fetch_contract.paperlive003.v1",
        "task_id": TASK_ID,
        "generated_by": GENERATED_BY,
        "market_id": MARKET_ID,
        "market_class": MARKET_CLASS,
        "fetch_status": "not_performed_protocol_only",
        "fetch_performed": False,
        "network_allowed_explicitly": False,
        "explicit_network_approval_reference": None,
        "endpoint_or_url_used": None,
        "source_category": None,
        "source_name": None,
        "fetched_at_marker": None,
        "raw_payload": None,
        "raw_text_excerpt": None,
        "http_status_if_applicable": None,
        "network_call_count": 0,
        "authenticated_endpoints_used": False,
        "auth_headers_used": False,
        "wallet_or_private_key_accessed": False,
        "orders_created": False,
        "browser_automation_used": False,
        "no_market_action_guidance": True,
        "no_trading_authority": True,
        "safety_summary": dict(SAFETY_SUMMARY),
        "allowed_future_source_categories": list(ALLOWED_FUTURE_SOURCE_CATEGORIES),
        "market_id_allowlist": [MARKET_ID],
    }


def build_normalized_evidence_contract(root=ROOT):
    return {
        "contract_version": "esports_normalized_outcome_evidence_contract.paperlive003.v1",
        "task_id": TASK_ID,
        "generated_by": GENERATED_BY,
        "market_id": MARKET_ID,
        "market_class": MARKET_CLASS,
        "outcome_evidence_status": "contract_defined_not_populated",
        "outcome_known": False,
        "result_source_type": None,
        "result_source_name": None,
        "result_source_reference": None,
        "match_identity_confirmed": False,
        "teams_or_players_confirmed": False,
        "tournament_confirmed": False,
        "match_format_confirmed": False,
        "final_result_text": None,
        "result_timestamp": None,
        "cancellation_or_forfeit_detected": None,
        "reschedule_detected": None,
        "contradiction_flags": [],
        "unresolved_questions": [
            "No outcome source has been fetched in PAPERLIVE-003.",
            "Future PAPERLIVE-004 needs explicit public read-only network approval.",
            "Operator review is required before outcome reconciliation.",
        ],
        "operator_review_required": True,
        "source_alignment_review_required": True,
        "no_market_action_guidance": True,
        "no_trading_authority": True,
    }


def build_source_alignment_review_contract(root=ROOT):
    return {
        "contract_version": "source_alignment_review_contract.paperlive003.v1",
        "task_id": TASK_ID,
        "generated_by": GENERATED_BY,
        "market_id": MARKET_ID,
        "market_class": MARKET_CLASS,
        "review_status": "contract_defined_not_performed",
        "outcome_known": False,
        "source_alignment_review_performed": False,
        "sources_to_review": _source_references(root=root),
        "source_roles": [
            "market_metadata_source",
            "market_rules_source",
            "manual_resolution_source_capture",
            "operator_review_surface",
            "paper_live_observation_ledger",
            "outcome_monitoring_plan",
            "future_raw_outcome_source",
            "future_normalized_outcome_evidence",
        ],
        "alignment_dimensions": [
            "match_identity_alignment",
            "tournament_alignment",
            "result_alignment",
            "timeliness_alignment",
            "official_source_status",
            "contradiction_review",
        ],
        "allowed_future_source_quality_updates": [
            "resolution_alignment",
            "timeliness",
            "official_source_status",
            "contradiction_count",
            "operator_usefulness_notes",
        ],
        "forbidden_updates": [
            "profit_only_score",
            "PnL",
            "ROI",
            "EV",
            "edge",
            "betting confidence",
            "side selection",
        ],
        "operator_review_required": True,
        "no_market_action_guidance": True,
        "no_trading_authority": True,
        "safety_summary": dict(SAFETY_SUMMARY),
    }


def build_readiness_gate(root=ROOT):
    required_existing = {
        "observation_ledger_exists": _exists(PAPERLIVE001_LEDGER_PATH, root=root),
        "monitoring_plan_exists": _exists(PAPERLIVE002_MONITORING_PLAN_PATH, root=root),
        "future_outcome_check_request_exists": _exists(
            PAPERLIVE002_FUTURE_REQUEST_PATH, root=root
        ),
        "source_quality_update_plan_exists": _exists(
            PAPERLIVE002_SOURCE_QUALITY_UPDATE_PLAN_PATH, root=root
        ),
    }
    contracts_defined = {
        "raw_fetch_contract_exists": True,
        "normalized_evidence_contract_exists": True,
        "source_alignment_review_contract_exists": True,
    }
    safety_protocol_satisfied = all(required_existing.values()) and all(
        contracts_defined.values()
    )
    return {
        "schema_version": "esports_readonly_outcome_check_readiness_gate.paperlive003.v1",
        "task_id": TASK_ID,
        "generated_by": GENERATED_BY,
        "market_id": MARKET_ID,
        "market_class": MARKET_CLASS,
        "readiness_status": "protocol_ready_waiting_for_explicit_network_approval",
        "future_paperlive_004_allowed_without_network_approval": False,
        "future_paperlive_004_requires_explicit_network_approval": True,
        "market_id_allowlisted": True,
        "market_class_allowlisted": True,
        **required_existing,
        **contracts_defined,
        "safety_protocol_satisfied": safety_protocol_satisfied,
        "blockers": [
            "explicit public read-only network approval is not present for PAPERLIVE-004",
            "outcome check is not performed in PAPERLIVE-003",
        ],
        "warnings": [
            "operator review is still required",
            "source alignment review is defined, not performed",
            "source quality update is planned, not performed",
        ],
        "no_market_action_guidance": True,
        "no_trading_authority": True,
        "safety_summary": dict(SAFETY_SUMMARY),
    }


def build_workbench_surface(root=ROOT):
    return {
        "schema_version": "esports_readonly_outcome_check_protocol_surface.paperlive003.v1",
        "task_id": TASK_ID,
        "generated_by": GENERATED_BY,
        "market_id": MARKET_ID,
        "market_class": MARKET_CLASS,
        "protocol_available": True,
        "protocol_path": PROTOCOL_JSON_PATH,
        "raw_fetch_contract_available": True,
        "raw_fetch_contract_path": RAW_FETCH_CONTRACT_JSON_PATH,
        "normalized_evidence_contract_available": True,
        "normalized_evidence_contract_path": NORMALIZED_EVIDENCE_CONTRACT_JSON_PATH,
        "source_alignment_review_contract_available": True,
        "source_alignment_review_contract_path": SOURCE_ALIGNMENT_REVIEW_CONTRACT_JSON_PATH,
        "readiness_gate_available": True,
        "readiness_gate_path": READINESS_GATE_JSON_PATH,
        "future_network_required": True,
        "explicit_network_approval_required": True,
        "outcome_checked": False,
        "simulated_trade_created": False,
        "selected_side": None,
        "stake_amount": None,
        "next_operator_actions": [
            "Review PAPERLIVE-003 protocol artifacts locally.",
            "Keep outcome reconciliation pending until PAPERLIVE-004 has explicit public read-only network approval.",
            "Use the raw fetch and normalized evidence contracts as the future PAPERLIVE-004 artifact shape.",
            "Perform source alignment review only after future outcome evidence exists.",
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
    }


def build_run_summary(root=ROOT, artifacts_created=False):
    pipeline = _pipeline_snapshot(root=root)
    return {
        "schema_version": "esports_readonly_outcome_check_protocol_summary.v1",
        "task_id": TASK_ID,
        "generated_by": GENERATED_BY,
        "status": "completed_local" if artifacts_created else "dry_run_no_write",
        "dry_run": not artifacts_created,
        "market_id": MARKET_ID,
        "market_class": MARKET_CLASS,
        "readonly_outcome_check_protocol_created": bool(artifacts_created),
        "raw_fetch_contract_created": bool(artifacts_created),
        "normalized_outcome_evidence_contract_created": bool(artifacts_created),
        "source_alignment_review_contract_created": bool(artifacts_created),
        "paperlive004_readiness_gate_created": bool(artifacts_created),
        "passive_workbench_surface_created": bool(artifacts_created),
        "future_paperlive004_requires_explicit_network_approval": True,
        "future_paperlive004_allowed_without_network_approval": False,
        "outcome_checked": False,
        "outcome_known": False,
        "source_alignment_review_performed": False,
        "source_scoring_performed": False,
        "source_ranking_updated": False,
        "profit_or_pnl_recorded": False,
        "simulated_trade_created": False,
        "selected_side": None,
        "stake_amount": None,
        "position_sizing_created": False,
        "market_action_guidance_generated": False,
        "probability_ev_edge_confidence_generated": False,
        "side_selection_generated": False,
        "openrouter_calls_performed": 0,
        "polymarket_api_calls_performed": 0,
        "external_network_calls_performed": 0,
        "network_calls_performed": 0,
        "authenticated_endpoints_used": False,
        "wallet_or_private_key_accessed": False,
        "orders_created": False,
        "trading_runtime_changed": False,
        "dispatcher_changed": False,
        "background_worker_created": False,
        "queue_mutated": False,
        "browser_automation_used": False,
        "canonical_packets_mutated": False,
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
        "files_written": OUTPUT_PATHS if artifacts_created else [],
        "safety_summary": dict(SAFETY_SUMMARY),
        "next_recommended_action": (
            "PMBOT-PAPERLIVE-004-ESPORTS-CONTROLLED-READONLY-OUTCOME-SOURCE-FETCH-"
            "NO-TRADE with explicit public read-only network approval"
        ),
    }


def build_docs_result(root=ROOT, artifacts_created=False):
    summary = build_run_summary(root=root, artifacts_created=artifacts_created)
    result = dict(summary)
    result["schema_version"] = "pmbot_paperlive_003_result.v1"
    result["status"] = (
        "completed_local_validation_pending_commit"
        if artifacts_created
        else "dry_run_no_write"
    )
    result["head_before"] = "71fc0d9e2a066829f3c24a2461e719924feee55d"
    result["head_after"] = "reported_in_final_response_after_commit"
    result["pushed"] = False
    result["tests_run"] = []
    result["tests_passed"] = []
    result["tests_failed"] = []
    result["files_created"] = OUTPUT_PATHS if artifacts_created else []
    result["files_modified"] = []
    return result


def render_protocol_markdown(protocol):
    lines = [
        "# PMBOT PAPERLIVE-003 Readonly Outcome Check Protocol",
        "",
        "PAPERLIVE-003 is local-only/protocol-only and does not check outcome.",
        "",
        f"- task_id: {protocol['task_id']}",
        f"- market_id: {protocol['market_id']}",
        f"- market_class: {protocol['market_class']}",
        f"- protocol_mode: {protocol['protocol_mode']}",
        "- outcome_checked: false",
        "- outcome_known: false",
        "- future_fetch_required: true",
        "- explicit_network_approval_required: true",
        "",
        "## Allowed Future Source Categories",
        "",
    ]
    for item in protocol["allowed_future_source_categories"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Allowed Future Endpoint Or URL Categories", ""])
    for item in protocol["allowed_future_endpoint_or_url_categories"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Forbidden Future Actions", ""])
    for item in protocol["forbidden_future_actions"]:
        lines.append(f"- forbidden: {item}")
    lines.extend(
        [
            "",
            "## Future Fetch Limits",
            "",
            "- max_markets: 1",
            "- market_id_allowlist: 1987056",
            "- market_class_allowlist: esports",
            "- public_readonly_only: true",
            "- no_auth_headers: true",
            "- timeout_required: true",
            "- raw_response_preserved: true",
            "- normalized_evidence_required: true",
            "",
            "## Safety Summary",
            "",
            "- no OpenRouter calls",
            "- no Polymarket API calls",
            "- no external network calls in PAPERLIVE-003",
            "- no authenticated endpoints",
            "- no wallet or private key access",
            "- no orders",
            "- no simulated trade",
            "- no selected side",
            "- no stake",
            "- no runtime changes, no dispatcher changes, no background worker changes, no browser automation, no queue changes, and no canonical packet changes",
            "- no probability, EV, edge, confidence, or side selection guidance",
            "- no market action guidance",
        ]
    )
    return "\n".join(lines)


def render_raw_fetch_contract_markdown(contract):
    return "\n".join(
        [
            "# PMBOT PAPERLIVE-003 Raw Outcome Fetch Contract",
            "",
            "This contract defines the future PAPERLIVE-004 raw read-only fetch artifact shape.",
            "",
            f"- task_id: {contract['task_id']}",
            f"- market_id: {contract['market_id']}",
            "- fetch_performed: false",
            "- network_allowed_explicitly: false",
            "- endpoint_or_url_used: null",
            "- raw_payload: null",
            "- network_call_count: 0",
            "- authenticated_endpoints_used: false",
            "- auth_headers_used: false",
            "- wallet_or_private_key_accessed: false",
            "- orders_created: false",
            "- browser_automation_used: false",
            "- no_market_action_guidance: true",
            "- no_trading_authority: true",
            "",
            "## Future Boundary",
            "",
            "- future PAPERLIVE-004 must have explicit public read-only network approval",
            "- future PAPERLIVE-004 must preserve raw response data",
            "- future PAPERLIVE-004 must emit normalized evidence separately",
        ]
    )


def render_normalized_evidence_contract_markdown(contract):
    return "\n".join(
        [
            "# PMBOT PAPERLIVE-003 Normalized Outcome Evidence Contract",
            "",
            "This contract defines the future normalized evidence shape; it is not populated here.",
            "",
            f"- task_id: {contract['task_id']}",
            f"- market_id: {contract['market_id']}",
            "- outcome_evidence_status: contract_defined_not_populated",
            "- outcome_known: false",
            "- final_result_text: null",
            "- result_timestamp: null",
            "- operator_review_required: true",
            "- source_alignment_review_required: true",
            "- no_market_action_guidance: true",
            "- no_trading_authority: true",
            "",
            "## Boundary",
            "",
            "- does not include winner-as-trade-side",
            "- does not include probability, EV, edge, confidence, or side selection guidance",
            "- does not include market action recommendation",
        ]
    )


def render_source_alignment_review_contract_markdown(contract):
    lines = [
        "# PMBOT PAPERLIVE-003 Source Alignment Review Contract",
        "",
        "This contract defines future source alignment review; review is not performed here.",
        "",
        f"- task_id: {contract['task_id']}",
        f"- market_id: {contract['market_id']}",
        "- outcome_known: false",
        "- source_alignment_review_performed: false",
        "- operator_review_required: true",
        "- no_market_action_guidance: true",
        "- no_trading_authority: true",
        "",
        "## Alignment Dimensions",
        "",
    ]
    for item in contract["alignment_dimensions"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Allowed Future Source Quality Updates", ""])
    for item in contract["allowed_future_source_quality_updates"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Forbidden Updates", ""])
    for item in contract["forbidden_updates"]:
        lines.append(f"- forbidden update: {item}")
    return "\n".join(lines)


def render_readiness_gate_markdown(gate):
    lines = [
        "# PMBOT PAPERLIVE-003 PAPERLIVE-004 Readiness Gate",
        "",
        "The readiness state is protocol_ready_waiting_for_explicit_network_approval.",
        "",
        f"- task_id: {gate['task_id']}",
        f"- market_id: {gate['market_id']}",
        "- future_paperlive_004_allowed_without_network_approval: false",
        "- future_paperlive_004_requires_explicit_network_approval: true",
        "- market_id_allowlisted: true",
        "- market_class_allowlisted: true",
        f"- observation_ledger_exists: {str(gate['observation_ledger_exists']).lower()}",
        f"- monitoring_plan_exists: {str(gate['monitoring_plan_exists']).lower()}",
        (
            "- future_outcome_check_request_exists: "
            f"{str(gate['future_outcome_check_request_exists']).lower()}"
        ),
        "- raw_fetch_contract_exists: true",
        "- normalized_evidence_contract_exists: true",
        "- source_alignment_review_contract_exists: true",
        (
            "- source_quality_update_plan_exists: "
            f"{str(gate['source_quality_update_plan_exists']).lower()}"
        ),
        f"- safety_protocol_satisfied: {str(gate['safety_protocol_satisfied']).lower()}",
        "- no_market_action_guidance: true",
        "- no_trading_authority: true",
        "",
        "## Blockers",
        "",
    ]
    for item in gate["blockers"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Warnings", ""])
    for item in gate["warnings"]:
        lines.append(f"- {item}")
    return "\n".join(lines)


def render_workbench_surface_markdown(surface):
    lines = [
        "# PMBOT PAPERLIVE-003 Passive Protocol Surface",
        "",
        f"- task_id: {surface['task_id']}",
        f"- market_id: {surface['market_id']}",
        "- protocol_available: true",
        "- raw_fetch_contract_available: true",
        "- normalized_evidence_contract_available: true",
        "- source_alignment_review_contract_available: true",
        "- readiness_gate_available: true",
        "- future_network_required: true",
        "- explicit_network_approval_required: true",
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
            "- no queue mutation",
            "- no runtime wiring change",
            "- no dispatcher change",
            "- no browser automation",
            "- no canonical packet mutation",
        ]
    )
    return "\n".join(lines)


def render_run_summary_markdown(summary):
    return "\n".join(
        [
            "# PMBOT PAPERLIVE-003 Readonly Outcome Check Protocol Summary",
            "",
            f"- task_id: {summary['task_id']}",
            f"- status: {summary['status']}",
            f"- market_id: {summary['market_id']}",
            "- readonly_outcome_check_protocol_created: true",
            "- raw_fetch_contract_created: true",
            "- normalized_outcome_evidence_contract_created: true",
            "- source_alignment_review_contract_created: true",
            "- paperlive004_readiness_gate_created: true",
            "- future_paperlive004_requires_explicit_network_approval: true",
            "- future_paperlive004_allowed_without_network_approval: false",
            "- outcome_checked: false",
            "- outcome_known: false",
            "- source_alignment_review_performed: false",
            "- simulated_trade_created: false",
            "- selected_side: null",
            "- stake_amount: null",
            "- no_market_action_guidance: true",
            "- no_trading_authority: true",
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
            "- no OpenRouter calls",
            "- no Polymarket API calls",
            "- no external network calls in PAPERLIVE-003",
            "- no authenticated endpoints",
            "- no wallet or private key access",
            "- no orders",
            "- no simulated trade",
            "- no selected side",
            "- no stake",
            "- no outcome check",
            "- no source scoring",
            "- no runtime changes, no dispatcher changes, no background worker changes, no browser automation, no queue changes, and no canonical packet changes",
            "- no probability, EV, edge, confidence, or side selection guidance",
        ]
    )


def render_docs_markdown(result):
    return "\n".join(
        [
            "# PMBOT PAPERLIVE-003 Esports Readonly Outcome Check Protocol No Trade",
            "",
            "PAPERLIVE-003 is local-only/protocol-only.",
            "",
            "## Boundary",
            "",
            "- It does not check outcome.",
            "- It does not call network or API.",
            "- It prepares future PAPERLIVE-004 only.",
            "- Future PAPERLIVE-004 requires explicit network approval.",
            "- It does not create simulated trade.",
            "- It does not choose side.",
            "- It does not create stake.",
            "- It does not compute probability, EV, edge, or confidence.",
            "- It does not create orders.",
            "- It does not use wallet.",
            "- It does not mutate runtime, queue, or canonical packets.",
            "- Source alignment review is defined, not performed.",
            "- Source quality update is planned, not performed.",
            "- Operator review is still required.",
            "",
            "## Created Artifacts",
            "",
            f"- protocol: {PROTOCOL_JSON_PATH}",
            f"- raw_fetch_contract: {RAW_FETCH_CONTRACT_JSON_PATH}",
            f"- normalized_outcome_evidence_contract: {NORMALIZED_EVIDENCE_CONTRACT_JSON_PATH}",
            f"- source_alignment_review_contract: {SOURCE_ALIGNMENT_REVIEW_CONTRACT_JSON_PATH}",
            f"- readiness_gate: {READINESS_GATE_JSON_PATH}",
            f"- passive_workbench_surface: {WORKBENCH_SURFACE_JSON_PATH}",
            "",
            "## Safety Summary",
            "",
            "- no OpenRouter calls",
            "- no Polymarket API calls",
            "- no external network calls in PAPERLIVE-003",
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
        ]
    )


def write_artifacts(root=ROOT):
    protocol = build_protocol(root=root)
    raw_contract = build_raw_fetch_contract(root=root)
    evidence_contract = build_normalized_evidence_contract(root=root)
    alignment_contract = build_source_alignment_review_contract(root=root)
    readiness_gate = build_readiness_gate(root=root)
    workbench_surface = build_workbench_surface(root=root)
    summary = build_run_summary(root=root, artifacts_created=True)
    docs_result = build_docs_result(root=root, artifacts_created=True)

    _write_json(PROTOCOL_JSON_PATH, protocol, root=root)
    _write_text(PROTOCOL_MD_PATH, render_protocol_markdown(protocol), root=root)
    _write_json(RAW_FETCH_CONTRACT_JSON_PATH, raw_contract, root=root)
    _write_text(
        RAW_FETCH_CONTRACT_MD_PATH,
        render_raw_fetch_contract_markdown(raw_contract),
        root=root,
    )
    _write_json(NORMALIZED_EVIDENCE_CONTRACT_JSON_PATH, evidence_contract, root=root)
    _write_text(
        NORMALIZED_EVIDENCE_CONTRACT_MD_PATH,
        render_normalized_evidence_contract_markdown(evidence_contract),
        root=root,
    )
    _write_json(SOURCE_ALIGNMENT_REVIEW_CONTRACT_JSON_PATH, alignment_contract, root=root)
    _write_text(
        SOURCE_ALIGNMENT_REVIEW_CONTRACT_MD_PATH,
        render_source_alignment_review_contract_markdown(alignment_contract),
        root=root,
    )
    _write_json(READINESS_GATE_JSON_PATH, readiness_gate, root=root)
    _write_text(
        READINESS_GATE_MD_PATH,
        render_readiness_gate_markdown(readiness_gate),
        root=root,
    )
    _write_json(WORKBENCH_SURFACE_JSON_PATH, workbench_surface, root=root)
    _write_text(
        WORKBENCH_SURFACE_MD_PATH,
        render_workbench_surface_markdown(workbench_surface),
        root=root,
    )
    _write_json(RUN_SUMMARY_JSON_PATH, summary, root=root)
    _write_text(RUN_SUMMARY_MD_PATH, render_run_summary_markdown(summary), root=root)
    _write_json(DOC_RESULT_JSON_PATH, docs_result, root=root)
    _write_text(DOC_RESULT_MD_PATH, render_docs_markdown(docs_result), root=root)
    return summary


def build_dry_run(root=ROOT, protocol_only=False):
    protocol = build_protocol(root=root)
    summary = build_run_summary(root=root, artifacts_created=False)
    return {
        "schema_version": "esports_readonly_outcome_check_protocol_dry_run.v1",
        "task_id": TASK_ID,
        "status": "protocol_only_no_write" if protocol_only else "dry_run_no_write",
        "dry_run": True,
        "protocol_only": bool(protocol_only),
        "market_id": MARKET_ID,
        "market_class": MARKET_CLASS,
        "planned_protocol_path": PROTOCOL_JSON_PATH,
        "planned_raw_fetch_contract_path": RAW_FETCH_CONTRACT_JSON_PATH,
        "planned_normalized_evidence_contract_path": NORMALIZED_EVIDENCE_CONTRACT_JSON_PATH,
        "planned_source_alignment_review_contract_path": (
            SOURCE_ALIGNMENT_REVIEW_CONTRACT_JSON_PATH
        ),
        "planned_readiness_gate_path": READINESS_GATE_JSON_PATH,
        "planned_workbench_surface_path": WORKBENCH_SURFACE_JSON_PATH,
        "protocol_mode": protocol["protocol_mode"],
        "outcome_checked": False,
        "outcome_known": False,
        "future_fetch_required": True,
        "explicit_network_approval_required": True,
        "simulated_trade_created": False,
        "selected_side": None,
        "stake_amount": None,
        "files_written": [],
        "summary": summary,
        "safety_summary": dict(SAFETY_SUMMARY),
        "openrouter_calls_performed": 0,
        "polymarket_api_calls_performed": 0,
        "external_network_calls_performed": 0,
    }


def build_summary_only(root=ROOT):
    summary = _load_optional_json(RUN_SUMMARY_JSON_PATH, root=root)
    protocol = _load_optional_json(PROTOCOL_JSON_PATH, root=root)
    raw_contract = _load_optional_json(RAW_FETCH_CONTRACT_JSON_PATH, root=root)
    evidence_contract = _load_optional_json(
        NORMALIZED_EVIDENCE_CONTRACT_JSON_PATH, root=root
    )
    alignment_contract = _load_optional_json(
        SOURCE_ALIGNMENT_REVIEW_CONTRACT_JSON_PATH, root=root
    )
    readiness_gate = _load_optional_json(READINESS_GATE_JSON_PATH, root=root)
    surface = _load_optional_json(WORKBENCH_SURFACE_JSON_PATH, root=root)
    pipeline = _pipeline_snapshot(root=root)
    return {
        "schema_version": "esports_readonly_outcome_check_protocol_summary_only.v1",
        "task_id": TASK_ID,
        "status": "summary_only",
        "market_id": MARKET_ID,
        "market_class": MARKET_CLASS,
        "protocol_exists": protocol is not None,
        "raw_fetch_contract_exists": raw_contract is not None,
        "normalized_evidence_contract_exists": evidence_contract is not None,
        "source_alignment_review_contract_exists": alignment_contract is not None,
        "readiness_gate_exists": readiness_gate is not None,
        "passive_workbench_surface_exists": surface is not None,
        "summary_exists": summary is not None,
        "outcome_checked": False,
        "outcome_known": False,
        "source_alignment_review_performed": False,
        "future_paperlive004_requires_explicit_network_approval": True,
        "future_paperlive004_allowed_without_network_approval": False,
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
    elif args.protocol_only:
        payload = build_dry_run(ROOT, protocol_only=True)
    else:
        payload = build_dry_run(ROOT, protocol_only=False)
    print(json.dumps(payload, indent=2, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(__import__("sys").argv[1:]))
