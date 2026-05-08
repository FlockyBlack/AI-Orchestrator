import argparse
import json
from pathlib import Path


TASK_ID = "PMBOT-PAPERLIVE-005-ESPORTS-OUTCOME-SOURCE-RECONCILIATION-NO-TRADE"
GENERATED_BY = "pm_bot/paper_live/esports_outcome_source_reconciliation.py"

ROOT = Path(__file__).resolve().parents[2]

MARKET_ID = "1987056"
MARKET_CLASS = "esports"
MARKET_TITLE = (
    "LoL: JD Gaming vs Anyone's Legend (BO5) - Esports World Cup China Qualifier Phase 2"
)
LOCAL_TIMESTAMP = "2026-05-08 Asia/Tbilisi"
NEXT_RECOMMENDED_ACTION = (
    "PMBOT-PAPERLIVE-006-ESPORTS-SOURCE-QUALITY-PENDING-LEDGER-AND-SUMMARY-NO-TRADE"
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

PAPERLIVE003_PROTOCOL_PATH = (
    "pm_bot/paper_live/"
    "esports_readonly_outcome_check_protocol_1987056_paperlive003.v1.json"
)
SOURCE_ALIGNMENT_REVIEW_CONTRACT_PATH = (
    "pm_bot/llm/source_alignment_review_contract_1987056_paperlive003.v1.json"
)
PAPERLIVE003_READINESS_GATE_PATH = (
    "pm_bot/paper_live/"
    "esports_readonly_outcome_check_readiness_gate_1987056_paperlive003.v1.json"
)

PAPERLIVE002_MONITORING_PLAN_PATH = (
    "pm_bot/paper_live/"
    "esports_outcome_source_monitoring_plan_1987056_paperlive002.v1.json"
)
PAPERLIVE002_CHECKLIST_PATH = (
    "pm_bot/paper_live/esports_source_monitoring_checklist_1987056_paperlive002.v1.json"
)
PAPERLIVE002_SOURCE_QUALITY_UPDATE_PLAN_PATH = (
    "pm_bot/llm/source_quality_update_plan_1987056_paperlive002.v1.json"
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

CAPTURE_009B_PATH = (
    "pm_bot/llm/manual_resolution_source_capture/"
    f"{MARKET_ID}_resolution_source_capture.v1.json"
)

INGEST_RESULT_PATH = "pm_bot/llm/manual_resolution_source_capture_ingest_result.v1.json"
INGEST_OVERLAY_PATH = "pm_bot/llm/manual_resolution_source_capture_ingested_overlay.v1.json"
READINESS_REPORT_PATH = "pm_bot/llm/post_capture_readiness_report.v1.json"
READINESS_GATE_PATH = "pm_bot/llm/post_capture_batch_readiness_gate.v1.json"

RECONCILIATION_JSON_PATH = (
    "pm_bot/paper_live/"
    "esports_outcome_source_reconciliation_1987056_paperlive005.v1.json"
)
RECONCILIATION_MD_PATH = (
    "pm_bot/paper_live/"
    "esports_outcome_source_reconciliation_1987056_paperlive005.v1.md"
)
PENDING_ALIGNMENT_JSON_PATH = (
    "pm_bot/llm/source_alignment_review_pending_1987056_paperlive005.v1.json"
)
PENDING_ALIGNMENT_MD_PATH = (
    "pm_bot/llm/source_alignment_review_pending_1987056_paperlive005.v1.md"
)
FUTURE_RECONCILIATION_REQUEST_JSON_PATH = (
    "pm_bot/paper_live/esports_future_reconciliation_update_request_1987056.v1.json"
)
FUTURE_RECONCILIATION_REQUEST_MD_PATH = (
    "pm_bot/paper_live/esports_future_reconciliation_update_request_1987056.v1.md"
)
SOURCE_QUALITY_PENDING_UPDATE_JSON_PATH = (
    "pm_bot/llm/source_quality_pending_update_1987056_paperlive005.v1.json"
)
SOURCE_QUALITY_PENDING_UPDATE_MD_PATH = (
    "pm_bot/llm/source_quality_pending_update_1987056_paperlive005.v1.md"
)
WORKBENCH_SURFACE_JSON_PATH = (
    "pm_bot/workbench/esports_reconciliation_surface_1987056_paperlive005.v1.json"
)
WORKBENCH_SURFACE_MD_PATH = (
    "pm_bot/workbench/esports_reconciliation_surface_1987056_paperlive005.v1.md"
)
RUN_SUMMARY_JSON_PATH = (
    "pm_bot/paper_live/esports_outcome_source_reconciliation_summary.v1.json"
)
RUN_SUMMARY_MD_PATH = (
    "pm_bot/paper_live/esports_outcome_source_reconciliation_summary.v1.md"
)
DOC_RESULT_JSON_PATH = "docs/PMBOT_PAPERLIVE_005_RESULT.json"
DOC_RESULT_MD_PATH = (
    "docs/PMBOT_PAPERLIVE_005_ESPORTS_OUTCOME_SOURCE_RECONCILIATION_NO_TRADE.md"
)

INPUT_JSON_PATHS = [
    PAPERLIVE004_RAW_FETCH_PATH,
    PAPERLIVE004_NORMALIZED_EVIDENCE_PATH,
    PAPERLIVE004_CALL_LEDGER_PATH,
    PAPERLIVE004_RECONCILIATION_INPUT_PATH,
    PAPERLIVE004_WORKBENCH_SURFACE_PATH,
    PAPERLIVE003_PROTOCOL_PATH,
    SOURCE_ALIGNMENT_REVIEW_CONTRACT_PATH,
    PAPERLIVE003_READINESS_GATE_PATH,
    PAPERLIVE002_MONITORING_PLAN_PATH,
    PAPERLIVE002_CHECKLIST_PATH,
    PAPERLIVE002_SOURCE_QUALITY_UPDATE_PLAN_PATH,
    PAPERLIVE001_LEDGER_PATH,
    PAPERLIVE001_SOURCE_QUALITY_PATH,
    PAPERLIVE001_OUTCOME_PLACEHOLDER_PATH,
    CAPTURE_009B_PATH,
    INGEST_RESULT_PATH,
    INGEST_OVERLAY_PATH,
    READINESS_REPORT_PATH,
    READINESS_GATE_PATH,
]

JSON_OUTPUT_PATHS = [
    RECONCILIATION_JSON_PATH,
    PENDING_ALIGNMENT_JSON_PATH,
    FUTURE_RECONCILIATION_REQUEST_JSON_PATH,
    SOURCE_QUALITY_PENDING_UPDATE_JSON_PATH,
    WORKBENCH_SURFACE_JSON_PATH,
    RUN_SUMMARY_JSON_PATH,
    DOC_RESULT_JSON_PATH,
]

MARKDOWN_OUTPUT_PATHS = [
    RECONCILIATION_MD_PATH,
    PENDING_ALIGNMENT_MD_PATH,
    FUTURE_RECONCILIATION_REQUEST_MD_PATH,
    SOURCE_QUALITY_PENDING_UPDATE_MD_PATH,
    WORKBENCH_SURFACE_MD_PATH,
    RUN_SUMMARY_MD_PATH,
    DOC_RESULT_MD_PATH,
]

OUTPUT_PATHS = [
    RECONCILIATION_JSON_PATH,
    RECONCILIATION_MD_PATH,
    PENDING_ALIGNMENT_JSON_PATH,
    PENDING_ALIGNMENT_MD_PATH,
    FUTURE_RECONCILIATION_REQUEST_JSON_PATH,
    FUTURE_RECONCILIATION_REQUEST_MD_PATH,
    SOURCE_QUALITY_PENDING_UPDATE_JSON_PATH,
    SOURCE_QUALITY_PENDING_UPDATE_MD_PATH,
    WORKBENCH_SURFACE_JSON_PATH,
    WORKBENCH_SURFACE_MD_PATH,
    RUN_SUMMARY_JSON_PATH,
    RUN_SUMMARY_MD_PATH,
    DOC_RESULT_JSON_PATH,
    DOC_RESULT_MD_PATH,
]

ALLOWED_FUTURE_UPDATES = [
    "resolution_alignment",
    "timeliness",
    "official_source_status",
    "contradiction_count",
    "operator_usefulness_notes",
]

FORBIDDEN_SOURCE_UPDATES = [
    "profit_only_score",
    "PnL",
    "ROI",
    "EV",
    "edge",
    "betting confidence",
    "side selection",
    "trade recommendation",
]

REQUIRED_FUTURE_INPUTS = [
    "updated Polymarket/Gamma resolution status",
    "official/fallback result source",
    "final result text",
    "result timestamp",
    "contradiction notes",
    "operator review notes",
]

FORBIDDEN_FUTURE_ACTIONS = [
    "auth",
    "wallet",
    "orders",
    "trading",
    "browser automation",
    "market action recommendation",
    "probability/EV/edge/confidence",
    "side selection",
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
    "canonical_packets_mutated": False,
    "market_action_guidance_generated": False,
    "probability_ev_edge_confidence_generated": False,
    "side_selection_generated": False,
}


def _parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Create local-only PAPERLIVE-005 esports reconciliation artifacts."
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


def _input_artifacts(root=ROOT):
    return [
        _artifact_reference(
            PAPERLIVE004_RAW_FETCH_PATH,
            "PAPERLIVE-004 raw outcome fetch evidence",
            root=root,
        ),
        _artifact_reference(
            PAPERLIVE004_NORMALIZED_EVIDENCE_PATH,
            "PAPERLIVE-004 normalized outcome evidence",
            root=root,
        ),
        _artifact_reference(
            PAPERLIVE004_CALL_LEDGER_PATH,
            "PAPERLIVE-004 outcome fetch call ledger",
            root=root,
        ),
        _artifact_reference(
            PAPERLIVE004_RECONCILIATION_INPUT_PATH,
            "PAPERLIVE-004 reconciliation input",
            root=root,
        ),
        _artifact_reference(
            PAPERLIVE004_WORKBENCH_SURFACE_PATH,
            "PAPERLIVE-004 passive outcome fetch surface",
            root=root,
        ),
        _artifact_reference(
            PAPERLIVE003_PROTOCOL_PATH,
            "PAPERLIVE-003 read-only outcome check protocol",
            root=root,
        ),
        _artifact_reference(
            SOURCE_ALIGNMENT_REVIEW_CONTRACT_PATH,
            "PAPERLIVE-003 source alignment review contract",
            root=root,
        ),
        _artifact_reference(
            PAPERLIVE003_READINESS_GATE_PATH,
            "PAPERLIVE-003 readiness gate",
            root=root,
        ),
        _artifact_reference(
            PAPERLIVE002_MONITORING_PLAN_PATH,
            "PAPERLIVE-002 outcome/source monitoring plan",
            root=root,
        ),
        _artifact_reference(
            PAPERLIVE002_CHECKLIST_PATH,
            "PAPERLIVE-002 source monitoring checklist",
            root=root,
        ),
        _artifact_reference(
            PAPERLIVE002_SOURCE_QUALITY_UPDATE_PLAN_PATH,
            "PAPERLIVE-002 source quality update plan",
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
            CAPTURE_009B_PATH,
            "SOURCE-009B manual resolution source capture",
            root=root,
        ),
        _artifact_reference(
            INGEST_RESULT_PATH,
            "manual source capture ingest result",
            root=root,
        ),
        _artifact_reference(
            INGEST_OVERLAY_PATH,
            "manual source capture ingested overlay",
            root=root,
        ),
        _artifact_reference(
            READINESS_REPORT_PATH,
            "post-capture readiness report",
            root=root,
        ),
        _artifact_reference(
            READINESS_GATE_PATH,
            "post-capture batch readiness gate",
            root=root,
        ),
    ]


def _load_inputs(root=ROOT):
    return {
        "raw_fetch": _load_optional_json(PAPERLIVE004_RAW_FETCH_PATH, root=root) or {},
        "normalized_evidence": (
            _load_optional_json(PAPERLIVE004_NORMALIZED_EVIDENCE_PATH, root=root) or {}
        ),
        "call_ledger": _load_optional_json(PAPERLIVE004_CALL_LEDGER_PATH, root=root) or {},
        "reconciliation_input": (
            _load_optional_json(PAPERLIVE004_RECONCILIATION_INPUT_PATH, root=root) or {}
        ),
        "paperlive004_surface": (
            _load_optional_json(PAPERLIVE004_WORKBENCH_SURFACE_PATH, root=root) or {}
        ),
        "alignment_contract": (
            _load_optional_json(SOURCE_ALIGNMENT_REVIEW_CONTRACT_PATH, root=root) or {}
        ),
        "source_quality_update_plan": (
            _load_optional_json(PAPERLIVE002_SOURCE_QUALITY_UPDATE_PLAN_PATH, root=root)
            or {}
        ),
        "paperlive001_source_quality": (
            _load_optional_json(PAPERLIVE001_SOURCE_QUALITY_PATH, root=root) or {}
        ),
    }


def _assess_reconciliation_status(normalized_evidence, reconciliation_input):
    if not normalized_evidence or not reconciliation_input:
        return "blocked_missing_outcome"
    outcome_known = bool(normalized_evidence.get("outcome_known"))
    outcome_resolution_status = normalized_evidence.get("outcome_resolution_status")
    if not outcome_known and outcome_resolution_status == "unresolved":
        return "pending_unresolved"
    if outcome_known:
        return "evidence_available_pending_review"
    return "blocked_missing_outcome"


def _normalized_evidence_summary(normalized_evidence):
    return {
        "outcome_evidence_status": normalized_evidence.get("outcome_evidence_status"),
        "outcome_known": bool(normalized_evidence.get("outcome_known", False)),
        "outcome_resolution_status": normalized_evidence.get(
            "outcome_resolution_status"
        ),
        "result_source_type": normalized_evidence.get("result_source_type"),
        "result_source_name": normalized_evidence.get("result_source_name"),
        "result_source_reference": normalized_evidence.get("result_source_reference"),
        "match_identity_confirmed": bool(
            normalized_evidence.get("match_identity_confirmed", False)
        ),
        "teams_or_players_confirmed": bool(
            normalized_evidence.get("teams_or_players_confirmed", False)
        ),
        "tournament_confirmed": bool(
            normalized_evidence.get("tournament_confirmed", False)
        ),
        "match_format_confirmed": bool(
            normalized_evidence.get("match_format_confirmed", False)
        ),
        "final_result_text": normalized_evidence.get("final_result_text"),
        "result_timestamp": normalized_evidence.get("result_timestamp"),
        "contradiction_flags": _safe_list(
            normalized_evidence.get("contradiction_flags")
        ),
        "unresolved_questions": _safe_list(
            normalized_evidence.get("unresolved_questions")
        ),
    }


def _sources_to_review(alignment_contract, root=ROOT):
    sources = list(_safe_list(alignment_contract.get("sources_to_review")))
    sources.extend(
        [
            _artifact_reference(
                PAPERLIVE004_RAW_FETCH_PATH,
                "PAPERLIVE-004 raw outcome fetch evidence",
                root=root,
            ),
            _artifact_reference(
                PAPERLIVE004_NORMALIZED_EVIDENCE_PATH,
                "PAPERLIVE-004 normalized outcome evidence",
                root=root,
            ),
            _artifact_reference(
                PAPERLIVE004_RECONCILIATION_INPUT_PATH,
                "PAPERLIVE-004 reconciliation input",
                root=root,
            ),
        ]
    )
    return sources


def _source_roles(alignment_contract, paperlive001_source_quality):
    roles = list(_safe_list(alignment_contract.get("source_roles")))
    roles.extend(_safe_list(paperlive001_source_quality.get("source_roles_observed")))
    output = []
    seen = set()
    for role in roles:
        if isinstance(role, str) and role not in seen:
            output.append(role)
            seen.add(role)
    return output


def build_reconciliation(root=ROOT):
    inputs = _load_inputs(root=root)
    raw_fetch = inputs["raw_fetch"]
    normalized = inputs["normalized_evidence"]
    reconciliation_input = inputs["reconciliation_input"]
    status = _assess_reconciliation_status(normalized, reconciliation_input)
    outcome_checked = bool(raw_fetch.get("outcome_checked", True))
    outcome_known = bool(normalized.get("outcome_known", False))
    outcome_resolution_status = normalized.get("outcome_resolution_status") or "unresolved"
    future_required = not outcome_known
    return {
        "schema_version": "paper_live_esports_outcome_source_reconciliation.v1",
        "task_id": TASK_ID,
        "generated_by": GENERATED_BY,
        "generated_at_marker": LOCAL_TIMESTAMP,
        "market_id": MARKET_ID,
        "market_class": MARKET_CLASS,
        "title_or_question": MARKET_TITLE,
        "reconciliation_mode": "local_evidence_assessment_only",
        "reconciliation_status": status,
        "outcome_checked": outcome_checked,
        "outcome_known": outcome_known,
        "outcome_resolution_status": outcome_resolution_status,
        "final_outcome_resolved": False,
        "source_alignment_review_performed": False,
        "source_quality_update_performed": False,
        "source_scoring_performed": False,
        "source_ranking_updated": False,
        "profit_or_pnl_recorded": False,
        "simulated_trade_created": False,
        "selected_side": None,
        "stake_amount": None,
        "order_created": False,
        "orders_created": False,
        "wallet_used": False,
        "wallet_or_private_key_accessed": False,
        "position_sizing_created": False,
        "input_artifacts": _input_artifacts(root=root),
        "normalized_evidence_summary": _normalized_evidence_summary(normalized),
        "reconciliation_findings": [
            "PAPERLIVE-004 normalized evidence is available for local assessment.",
            "The prior outcome check did not find a final resolved outcome.",
            "Outcome resolution status remains unresolved in the local evidence.",
            "Final source alignment review is pending until outcome evidence is known.",
            "Source quality update is pending; no scoring or ranking is performed.",
        ],
        "unresolved_questions": _safe_list(normalized.get("unresolved_questions"))
        + [
            "Final result text is still unavailable.",
            "Result timestamp is still unavailable.",
            "Operator review remains required before any final reconciliation update.",
        ],
        "blockers_to_final_reconciliation": [
            "outcome_known is false",
            "outcome_resolution_status is unresolved",
            "final_result_text is null",
            "final result source has not been reviewed by an operator",
            "source alignment review is blocked until outcome evidence is known",
        ],
        "future_reconciliation_required": future_required,
        "future_readonly_fetch_required": future_required,
        "operator_review_required": True,
        "next_recommended_action": NEXT_RECOMMENDED_ACTION,
        "no_market_action_guidance": True,
        "no_trading_authority": True,
        "safety_summary": dict(SAFETY_SUMMARY),
        "openrouter_calls_performed": 0,
        "polymarket_api_calls_performed": 0,
        "external_network_calls_performed": 0,
    }


def build_pending_source_alignment_review(root=ROOT):
    inputs = _load_inputs(root=root)
    contract = inputs["alignment_contract"]
    return {
        "schema_version": "source_alignment_review_pending_paperlive005.v1",
        "task_id": TASK_ID,
        "generated_by": GENERATED_BY,
        "generated_at_marker": LOCAL_TIMESTAMP,
        "market_id": MARKET_ID,
        "market_class": MARKET_CLASS,
        "review_status": "pending_outcome_resolution",
        "outcome_known": False,
        "source_alignment_review_performed": False,
        "sources_to_review": _sources_to_review(contract, root=root),
        "source_roles": _source_roles(contract, inputs["paperlive001_source_quality"]),
        "alignment_dimensions": _safe_list(contract.get("alignment_dimensions")),
        "blockers": [
            "outcome_known is false",
            "outcome_resolution_status is unresolved",
            "final result text is unavailable",
            "operator review has not approved final outcome evidence",
        ],
        "allowed_future_updates": list(ALLOWED_FUTURE_UPDATES),
        "forbidden_updates": list(FORBIDDEN_SOURCE_UPDATES),
        "operator_review_required": True,
        "no_market_action_guidance": True,
        "no_trading_authority": True,
        "safety_summary": dict(SAFETY_SUMMARY),
        "openrouter_calls_performed": 0,
        "polymarket_api_calls_performed": 0,
        "external_network_calls_performed": 0,
    }


def build_future_reconciliation_update_request(root=ROOT):
    return {
        "schema_version": "paper_live_esports_future_reconciliation_update_request.v1",
        "task_id": TASK_ID,
        "generated_by": GENERATED_BY,
        "generated_at_marker": LOCAL_TIMESTAMP,
        "market_id": MARKET_ID,
        "market_class": MARKET_CLASS,
        "request_status": "prepared_not_executed",
        "outcome_known_now": False,
        "future_update_required": True,
        "future_network_required": True,
        "explicit_network_approval_required": True,
        "required_future_inputs": list(REQUIRED_FUTURE_INPUTS),
        "forbidden_future_actions": list(FORBIDDEN_FUTURE_ACTIONS),
        "operator_review_required": True,
        "no_market_action_guidance": True,
        "no_trading_authority": True,
        "simulated_trade_created": False,
        "selected_side": None,
        "stake_amount": None,
        "safety_summary": dict(SAFETY_SUMMARY),
        "openrouter_calls_performed": 0,
        "polymarket_api_calls_performed": 0,
        "external_network_calls_performed": 0,
    }


def build_source_quality_pending_update(root=ROOT):
    inputs = _load_inputs(root=root)
    plan = inputs["source_quality_update_plan"]
    return {
        "schema_version": "source_quality_pending_update_paperlive005.v1",
        "task_id": TASK_ID,
        "generated_by": GENERATED_BY,
        "generated_at_marker": LOCAL_TIMESTAMP,
        "market_id": MARKET_ID,
        "market_class": MARKET_CLASS,
        "update_status": "pending_outcome_resolution",
        "outcome_known": False,
        "source_scoring_performed": False,
        "source_ranking_updated": False,
        "profit_or_pnl_used": False,
        "update_blockers": [
            "outcome_known is false",
            "source alignment review is not performed",
            "operator review of final outcome evidence is pending",
        ],
        "future_update_requires": _safe_list(plan.get("future_update_requires"))
        or [
            "outcome evidence",
            "source alignment review",
            "contradiction review",
            "operator review",
        ],
        "allowed_future_metrics": list(ALLOWED_FUTURE_UPDATES),
        "forbidden_metrics": [
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
        "simulated_trade_created": False,
        "selected_side": None,
        "stake_amount": None,
        "safety_summary": dict(SAFETY_SUMMARY),
        "openrouter_calls_performed": 0,
        "polymarket_api_calls_performed": 0,
        "external_network_calls_performed": 0,
    }


def build_workbench_surface(reconciliation, root=ROOT):
    return {
        "schema_version": "paper_live_esports_reconciliation_surface.v1",
        "task_id": TASK_ID,
        "generated_by": GENERATED_BY,
        "generated_at_marker": LOCAL_TIMESTAMP,
        "market_id": MARKET_ID,
        "market_class": MARKET_CLASS,
        "reconciliation_artifact_available": True,
        "reconciliation_status": reconciliation["reconciliation_status"],
        "outcome_checked": reconciliation["outcome_checked"],
        "outcome_known": reconciliation["outcome_known"],
        "source_alignment_review_performed": False,
        "source_quality_update_performed": False,
        "future_reconciliation_update_request_available": True,
        "operator_review_required": True,
        "simulated_trade_created": False,
        "selected_side": None,
        "stake_amount": None,
        "next_operator_actions": [
            "Review PAPERLIVE-005 pending reconciliation report.",
            "Keep final source alignment review pending while outcome remains unresolved.",
            "Use future update request only after explicit network approval is granted.",
        ],
        "queue_mutated": False,
        "runtime_wiring_changed": False,
        "trading_runtime_changed": False,
        "dispatcher_changed": False,
        "background_worker_created": False,
        "browser_automation_used": False,
        "canonical_packets_mutated": False,
        "no_queue_authority": True,
        "no_runtime_authority": True,
        "no_dispatcher_authority": True,
        "no_market_action_guidance": True,
        "no_trading_authority": True,
    }


def build_run_summary(reconciliation, root=ROOT, artifacts_created=False):
    pipeline = _pipeline_snapshot(root=root)
    return {
        "schema_version": "paper_live_esports_outcome_source_reconciliation_summary.v1",
        "task_id": TASK_ID,
        "generated_by": GENERATED_BY,
        "generated_at_marker": LOCAL_TIMESTAMP,
        "status": "completed_local" if artifacts_created else "dry_run_no_write",
        "market_id": MARKET_ID,
        "market_class": MARKET_CLASS,
        "reconciliation_status": reconciliation["reconciliation_status"],
        "outcome_checked": reconciliation["outcome_checked"],
        "outcome_known": reconciliation["outcome_known"],
        "outcome_resolution_status": reconciliation["outcome_resolution_status"],
        "final_outcome_resolved": False,
        "source_alignment_reviews_performed_count": 0,
        "source_quality_updates_performed_count": 0,
        "source_scoring_performed": False,
        "source_ranking_updated": False,
        "profit_or_pnl_recorded": False,
        "simulated_trades_created_count": 0,
        "orders_created_count": 0,
        "selected_side_count": 0,
        "stake_amount_count": 0,
        "operator_review_required_count": 5,
        "reconciliation_artifact_created": bool(artifacts_created),
        "pending_source_alignment_review_created": bool(artifacts_created),
        "future_reconciliation_update_request_created": bool(artifacts_created),
        "source_quality_pending_update_created": bool(artifacts_created),
        "passive_workbench_surface_created": bool(artifacts_created),
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
        "no_market_action_guidance": True,
        "safety_summary": dict(SAFETY_SUMMARY),
        "next_recommended_action": NEXT_RECOMMENDED_ACTION,
        "files_created": OUTPUT_PATHS if artifacts_created else [],
        "files_modified": [],
        "openrouter_calls_performed": 0,
        "polymarket_api_calls_performed": 0,
        "external_network_calls_performed": 0,
    }


def build_docs_result(reconciliation, root=ROOT, artifacts_created=False):
    pipeline = _pipeline_snapshot(root=root)
    return {
        "schema_version": "paperlive005_result.v1",
        "task_id": TASK_ID,
        "status": "completed_local" if artifacts_created else "dry_run_no_write",
        "market_id": MARKET_ID,
        "market_class": MARKET_CLASS,
        "reconciliation_status": reconciliation["reconciliation_status"],
        "outcome_checked": reconciliation["outcome_checked"],
        "outcome_known": reconciliation["outcome_known"],
        "outcome_resolution_status": reconciliation["outcome_resolution_status"],
        "final_outcome_resolved": False,
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
        "source_alignment_review_performed": False,
        "source_quality_update_performed": False,
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
        "reconciliation_artifact_created": bool(artifacts_created),
        "pending_source_alignment_review_created": bool(artifacts_created),
        "future_reconciliation_update_request_created": bool(artifacts_created),
        "source_quality_pending_update_created": bool(artifacts_created),
        "passive_workbench_surface_created": bool(artifacts_created),
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
        "next_recommended_action": NEXT_RECOMMENDED_ACTION,
        "safety_summary": dict(SAFETY_SUMMARY),
    }


def build_artifacts(root=ROOT, artifacts_created=False):
    reconciliation = build_reconciliation(root=root)
    return {
        "reconciliation": reconciliation,
        "pending_alignment": build_pending_source_alignment_review(root=root),
        "future_request": build_future_reconciliation_update_request(root=root),
        "source_quality_pending_update": build_source_quality_pending_update(root=root),
        "workbench_surface": build_workbench_surface(reconciliation, root=root),
        "run_summary": build_run_summary(
            reconciliation, root=root, artifacts_created=artifacts_created
        ),
        "docs_result": build_docs_result(
            reconciliation, root=root, artifacts_created=artifacts_created
        ),
    }


def render_reconciliation_markdown(reconciliation):
    lines = [
        "# PMBOT PAPERLIVE-005 Outcome Source Reconciliation",
        "",
        "PAPERLIVE-005 is local-only and consumes existing PAPERLIVE-004 evidence.",
        "",
        f"- task_id: {reconciliation['task_id']}",
        f"- market_id: {reconciliation['market_id']}",
        f"- market_class: {reconciliation['market_class']}",
        f"- reconciliation_status: {reconciliation['reconciliation_status']}",
        f"- outcome_checked: {str(reconciliation['outcome_checked']).lower()}",
        f"- outcome_known: {str(reconciliation['outcome_known']).lower()}",
        f"- outcome_resolution_status: {reconciliation['outcome_resolution_status']}",
        "- final_outcome_resolved: false",
        "- source_alignment_review_performed: false",
        "- source_quality_update_performed: false",
        "- source_scoring_performed: false",
        "- source_ranking_updated: false",
        "- simulated_trade_created: false",
        "- selected_side: null",
        "- stake_amount: null",
        "- order_created: false",
        "- wallet_used: false",
        "- no_market_action_guidance: true",
        "- no_trading_authority: true",
        "",
        "## Findings",
        "",
    ]
    for item in reconciliation["reconciliation_findings"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Blockers", ""])
    for item in reconciliation["blockers_to_final_reconciliation"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Future Work", ""])
    lines.append("- future_reconciliation_required: true")
    lines.append("- future_readonly_fetch_required: true")
    lines.append("- operator_review_required: true")
    lines.append("- explicit network approval is required before any future fetch")
    lines.extend(["", "## Safety", ""])
    lines.extend(
        [
            "- no OpenRouter calls",
            "- no Polymarket API calls in PAPERLIVE-005",
            "- no external network calls in PAPERLIVE-005",
            "- no authenticated endpoints",
            "- no wallet or private key access",
            "- no orders",
            "- no simulated trade",
            "- no selected side",
            "- no stake",
            "- no probability, EV, edge, confidence, or side selection guidance",
            "- no source scoring or source ranking update",
            "- no runtime changes, no dispatcher changes, no background worker changes, no queue changes, no browser automation, and no canonical packet changes",
        ]
    )
    return "\n".join(lines)


def render_pending_alignment_markdown(pending):
    lines = [
        "# PMBOT PAPERLIVE-005 Pending Source Alignment Review",
        "",
        "This artifact prepares future source alignment review; review is not performed while outcome is unresolved.",
        "",
        f"- task_id: {pending['task_id']}",
        f"- market_id: {pending['market_id']}",
        f"- review_status: {pending['review_status']}",
        "- outcome_known: false",
        "- source_alignment_review_performed: false",
        "- operator_review_required: true",
        "- no_market_action_guidance: true",
        "- no_trading_authority: true",
        "",
        "## Alignment Dimensions",
        "",
    ]
    for item in pending["alignment_dimensions"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Allowed Future Updates", ""])
    for item in pending["allowed_future_updates"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Forbidden Updates", ""])
    for item in pending["forbidden_updates"]:
        lines.append(f"- forbidden update: {item}")
    lines.extend(["", "## Blockers", ""])
    for item in pending["blockers"]:
        lines.append(f"- {item}")
    return "\n".join(lines)


def render_future_request_markdown(request):
    lines = [
        "# PMBOT PAPERLIVE-005 Future Reconciliation Update Request",
        "",
        "This request is prepared only and is not executed in PAPERLIVE-005.",
        "",
        f"- task_id: {request['task_id']}",
        f"- market_id: {request['market_id']}",
        f"- request_status: {request['request_status']}",
        "- outcome_known_now: false",
        "- future_update_required: true",
        "- future_network_required: true",
        "- explicit_network_approval_required: true",
        "- operator_review_required: true",
        "- no_market_action_guidance: true",
        "- no_trading_authority: true",
        "",
        "## Required Future Inputs",
        "",
    ]
    for item in request["required_future_inputs"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Forbidden Future Actions", ""])
    for item in request["forbidden_future_actions"]:
        lines.append(f"- forbidden action: {item}")
    return "\n".join(lines)


def render_source_quality_pending_update_markdown(update):
    lines = [
        "# PMBOT PAPERLIVE-005 Source Quality Pending Update",
        "",
        "Source quality update remains pending because outcome evidence is unresolved.",
        "",
        f"- task_id: {update['task_id']}",
        f"- market_id: {update['market_id']}",
        f"- update_status: {update['update_status']}",
        "- outcome_known: false",
        "- source_scoring_performed: false",
        "- source_ranking_updated: false",
        "- profit_or_pnl_used: false",
        "- operator_review_required: true",
        "- no_market_action_guidance: true",
        "- no_trading_authority: true",
        "",
        "## Future Update Requires",
        "",
    ]
    for item in update["future_update_requires"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Allowed Future Metrics", ""])
    for item in update["allowed_future_metrics"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Forbidden Metrics", ""])
    for item in update["forbidden_metrics"]:
        lines.append(f"- forbidden metric: {item}")
    lines.extend(["", "## Update Blockers", ""])
    for item in update["update_blockers"]:
        lines.append(f"- {item}")
    return "\n".join(lines)


def render_workbench_surface_markdown(surface):
    lines = [
        "# PMBOT PAPERLIVE-005 Passive Reconciliation Surface",
        "",
        f"- task_id: {surface['task_id']}",
        f"- market_id: {surface['market_id']}",
        "- reconciliation_artifact_available: true",
        f"- reconciliation_status: {surface['reconciliation_status']}",
        f"- outcome_checked: {str(surface['outcome_checked']).lower()}",
        f"- outcome_known: {str(surface['outcome_known']).lower()}",
        "- source_alignment_review_performed: false",
        "- source_quality_update_performed: false",
        "- future_reconciliation_update_request_available: true",
        "- operator_review_required: true",
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
            "## Safety",
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
            "# PMBOT PAPERLIVE-005 Outcome Source Reconciliation Summary",
            "",
            f"- task_id: {summary['task_id']}",
            f"- status: {summary['status']}",
            f"- market_id: {summary['market_id']}",
            f"- market_class: {summary['market_class']}",
            f"- reconciliation_status: {summary['reconciliation_status']}",
            f"- outcome_checked: {str(summary['outcome_checked']).lower()}",
            f"- outcome_known: {str(summary['outcome_known']).lower()}",
            f"- outcome_resolution_status: {summary['outcome_resolution_status']}",
            "- final_outcome_resolved: false",
            "- source_alignment_reviews_performed_count: 0",
            "- source_quality_updates_performed_count: 0",
            "- simulated_trades_created_count: 0",
            "- orders_created_count: 0",
            "- selected_side_count: 0",
            "- stake_amount_count: 0",
            f"- operator_review_required_count: {summary['operator_review_required_count']}",
            "- no_market_action_guidance: true",
            "",
            "## Safety",
            "",
            "- local-only",
            "- no OpenRouter calls",
            "- no Polymarket API calls in PAPERLIVE-005",
            "- no external network calls in PAPERLIVE-005",
            "- no authenticated endpoints",
            "- no wallet or private key access",
            "- no orders",
            "- no simulated trade",
            "- no selected side",
            "- no stake",
            "- no source scoring or source ranking update",
            "- no probability, EV, edge, confidence, or side selection guidance",
            "- no runtime changes, no dispatcher changes, no background worker changes, no browser automation, no queue changes, and no canonical packet changes",
        ]
    )


def render_docs_markdown(result):
    return "\n".join(
        [
            "# PMBOT PAPERLIVE-005 Esports Outcome Source Reconciliation No Trade",
            "",
            "PAPERLIVE-005 is local-only and does not call network or APIs. It consumes PAPERLIVE-004 evidence for market `1987056`.",
            "",
            "## Result",
            "",
            f"- reconciliation_status: {result['reconciliation_status']}",
            "- outcome_checked: true",
            "- outcome_known: false",
            "- outcome_resolution_status: unresolved",
            "- final_outcome_resolved: false",
            "- operator_review_required: true",
            "",
            "## Boundary",
            "",
            "- outcome is unresolved, so reconciliation remains pending",
            "- source alignment review is not performed while outcome_known is false",
            "- source quality update is not performed while outcome_known is false",
            "- future reconciliation update requires explicit network approval if outcome remains unresolved",
            "- no OpenRouter calls",
            "- no Polymarket API calls in PAPERLIVE-005",
            "- no external network calls in PAPERLIVE-005",
            "- no simulated trade",
            "- no side chosen",
            "- no stake",
            "- no probability, EV, edge, or confidence",
            "- no orders",
            "- no wallet use",
            "- no runtime mutation, no queue mutation, and no canonical packet mutation",
            "- no source scoring or source ranking update",
        ]
    )


def write_artifacts(root=ROOT):
    artifacts = build_artifacts(root=root, artifacts_created=True)
    _write_json(RECONCILIATION_JSON_PATH, artifacts["reconciliation"], root=root)
    _write_text(
        RECONCILIATION_MD_PATH,
        render_reconciliation_markdown(artifacts["reconciliation"]),
        root=root,
    )
    _write_json(PENDING_ALIGNMENT_JSON_PATH, artifacts["pending_alignment"], root=root)
    _write_text(
        PENDING_ALIGNMENT_MD_PATH,
        render_pending_alignment_markdown(artifacts["pending_alignment"]),
        root=root,
    )
    _write_json(
        FUTURE_RECONCILIATION_REQUEST_JSON_PATH,
        artifacts["future_request"],
        root=root,
    )
    _write_text(
        FUTURE_RECONCILIATION_REQUEST_MD_PATH,
        render_future_request_markdown(artifacts["future_request"]),
        root=root,
    )
    _write_json(
        SOURCE_QUALITY_PENDING_UPDATE_JSON_PATH,
        artifacts["source_quality_pending_update"],
        root=root,
    )
    _write_text(
        SOURCE_QUALITY_PENDING_UPDATE_MD_PATH,
        render_source_quality_pending_update_markdown(
            artifacts["source_quality_pending_update"]
        ),
        root=root,
    )
    _write_json(WORKBENCH_SURFACE_JSON_PATH, artifacts["workbench_surface"], root=root)
    _write_text(
        WORKBENCH_SURFACE_MD_PATH,
        render_workbench_surface_markdown(artifacts["workbench_surface"]),
        root=root,
    )
    _write_json(RUN_SUMMARY_JSON_PATH, artifacts["run_summary"], root=root)
    _write_text(
        RUN_SUMMARY_MD_PATH,
        render_run_summary_markdown(artifacts["run_summary"]),
        root=root,
    )
    _write_json(DOC_RESULT_JSON_PATH, artifacts["docs_result"], root=root)
    _write_text(DOC_RESULT_MD_PATH, render_docs_markdown(artifacts["docs_result"]), root=root)
    return artifacts["run_summary"]


def build_dry_run(root=ROOT):
    artifacts = build_artifacts(root=root, artifacts_created=False)
    return {
        "schema_version": "paper_live_esports_outcome_source_reconciliation_dry_run.v1",
        "task_id": TASK_ID,
        "status": "dry_run_no_write",
        "dry_run": True,
        "market_id": MARKET_ID,
        "market_class": MARKET_CLASS,
        "planned_reconciliation_path": RECONCILIATION_JSON_PATH,
        "planned_pending_alignment_path": PENDING_ALIGNMENT_JSON_PATH,
        "planned_future_reconciliation_update_request_path": (
            FUTURE_RECONCILIATION_REQUEST_JSON_PATH
        ),
        "planned_source_quality_pending_update_path": (
            SOURCE_QUALITY_PENDING_UPDATE_JSON_PATH
        ),
        "planned_workbench_surface_path": WORKBENCH_SURFACE_JSON_PATH,
        "reconciliation_status": artifacts["reconciliation"]["reconciliation_status"],
        "outcome_checked": artifacts["reconciliation"]["outcome_checked"],
        "outcome_known": artifacts["reconciliation"]["outcome_known"],
        "final_outcome_resolved": False,
        "source_alignment_review_performed": False,
        "source_quality_update_performed": False,
        "simulated_trade_created": False,
        "selected_side": None,
        "stake_amount": None,
        "files_written": [],
        "summary": artifacts["run_summary"],
        "safety_summary": dict(SAFETY_SUMMARY),
        "openrouter_calls_performed": 0,
        "polymarket_api_calls_performed": 0,
        "external_network_calls_performed": 0,
    }


def build_summary_only(root=ROOT):
    summary = _load_optional_json(RUN_SUMMARY_JSON_PATH, root=root)
    reconciliation = _load_optional_json(RECONCILIATION_JSON_PATH, root=root)
    pending = _load_optional_json(PENDING_ALIGNMENT_JSON_PATH, root=root)
    future_request = _load_optional_json(
        FUTURE_RECONCILIATION_REQUEST_JSON_PATH, root=root
    )
    source_quality = _load_optional_json(
        SOURCE_QUALITY_PENDING_UPDATE_JSON_PATH, root=root
    )
    surface = _load_optional_json(WORKBENCH_SURFACE_JSON_PATH, root=root)
    pipeline = _pipeline_snapshot(root=root)
    return {
        "schema_version": "paper_live_esports_outcome_source_reconciliation_summary_only.v1",
        "task_id": TASK_ID,
        "status": "summary_only",
        "market_id": MARKET_ID,
        "market_class": MARKET_CLASS,
        "reconciliation_artifact_exists": reconciliation is not None,
        "pending_source_alignment_review_exists": pending is not None,
        "future_reconciliation_update_request_exists": future_request is not None,
        "source_quality_pending_update_exists": source_quality is not None,
        "passive_workbench_surface_exists": surface is not None,
        "summary_exists": summary is not None,
        "reconciliation_status": (summary or {}).get("reconciliation_status"),
        "outcome_checked": bool((summary or {}).get("outcome_checked", False)),
        "outcome_known": bool((summary or {}).get("outcome_known", False)),
        "final_outcome_resolved": False,
        "source_alignment_reviews_performed_count": (summary or {}).get(
            "source_alignment_reviews_performed_count",
            0,
        ),
        "source_quality_updates_performed_count": (summary or {}).get(
            "source_quality_updates_performed_count",
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
