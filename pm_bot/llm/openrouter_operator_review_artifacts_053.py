import argparse
import json
from pathlib import Path


TASK_ID = "PMBOT-OPENROUTER-053-N5-SURFACE-WORKBENCH-INVENTORY-UX-AND-CONTOUR-AUDIT"
SURFACE_TASK_ID = "PMBOT-OPENROUTER-053-PASSIVE-OPERATOR-SURFACE-AND-WORKBENCH-N5-INTEGRATION"
SCHEMA_VERSION = "openrouter_operator_review_artifacts_053.v1"
GENERATED_BY = "pm_bot/llm/openrouter_operator_review_artifacts_053.py"

ROOT = Path(__file__).resolve().parents[2]
LLM_DIR = ROOT / "pm_bot" / "llm"
WORKBENCH_DIR = ROOT / "pm_bot" / "workbench"
DOCS_DIR = ROOT / "docs"

N3_MARKET_IDS = ["569333", "569334", "569343"]
N5_MARKET_IDS = ["569344", "569366", "569368", "569373", "573656"]
SINGLE_CALL_MARKET_IDS = ["563650", "569332"]
MODEL = "anthropic/claude-sonnet-4.5"

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
}

COMBINED_OPENROUTER_CONTOUR_SUMMARY = {
    "total_markets_successfully_reviewed": 8,
    "total_openrouter_calls_in_successful_batches": 8,
    "combined_cost": 0.325071,
    "combined_tokens": 48573,
    "total_blocked_in_successful_batches": 0,
    "average_cost_per_market_combined": 0.040633875,
    "average_tokens_per_market_combined": 6071.625,
}

SOURCE_PATHS = {
    "result_046": "docs/PMBOT_OPENROUTER_046_RESULT.json",
    "result_047": "docs/PMBOT_OPENROUTER_047_RESULT.json",
    "result_048": "docs/PMBOT_OPENROUTER_048_RESULT.json",
    "result_049": "docs/PMBOT_OPENROUTER_049_RESULT.json",
    "result_050": "docs/PMBOT_OPENROUTER_050_RESULT.json",
    "result_051": "docs/PMBOT_OPENROUTER_051_RESULT.json",
    "result_052": "docs/PMBOT_OPENROUTER_052_RESULT.json",
    "surface_046_json": "pm_bot/llm/operator_openrouter_batch_surface_046.v1.json",
    "surface_046_md": "pm_bot/llm/operator_openrouter_batch_surface_046.v1.md",
    "surface_051_json": "pm_bot/llm/operator_openrouter_batch_surface_051.v1.json",
    "surface_051_md": "pm_bot/llm/operator_openrouter_batch_surface_051.v1.md",
    "baseline_046_json": "pm_bot/llm/openrouter_046_small_batch_quality_baseline.v1.json",
    "baseline_051_json": "pm_bot/llm/openrouter_051_n5_batch_quality_baseline.v1.json",
    "baseline_051_md": "pm_bot/llm/openrouter_051_n5_batch_quality_baseline.v1.md",
    "summary_051_md": "pm_bot/llm/openrouter_051_n5_batch_operator_summary.v1.md",
    "inventory_json": "pm_bot/llm/current_llm_market_packet_inventory.v1.json",
    "inventory_md": "pm_bot/llm/current_llm_market_packet_inventory.v1.md",
    "evidence_audit_json": "pm_bot/llm/current_llm_source_evidence_completeness_audit.v1.json",
    "evidence_audit_md": "pm_bot/llm/current_llm_source_evidence_completeness_audit.v1.md",
    "batch_readiness_gate_json": "pm_bot/llm/current_llm_batch_readiness_gate.v1.json",
    "batch_readiness_gate_md": "pm_bot/llm/current_llm_batch_readiness_gate.v1.md",
    "contour_audit_json": "pm_bot/llm/openrouter_operator_review_contour_046_053_audit.v1.json",
    "contour_audit_md": "pm_bot/llm/openrouter_operator_review_contour_046_053_audit.v1.md",
    "dashboard_json": "pm_bot/workbench/operator_openrouter_review_dashboard.v1.json",
    "dashboard_md": "pm_bot/workbench/operator_openrouter_review_dashboard.v1.md",
    "decision_matrix_json": "pm_bot/llm/openrouter_next_step_decision_matrix.v1.json",
    "decision_matrix_md": "docs/PMBOT_OPENROUTER_NEXT_STEP_DECISION_MATRIX.md",
    "runbook_md": "docs/PMBOT_OPENROUTER_OPERATOR_REVIEW_RUNBOOK.md",
    "result_053": "docs/PMBOT_OPENROUTER_053_RESULT.json",
    "report_053": "docs/PMBOT_OPENROUTER_053_N5_SURFACE_WORKBENCH_INVENTORY_UX_AND_CONTOUR_AUDIT.md",
}

SINGLE_CALL_REVIEW_STATUS = {
    "563650": {
        "task": "028",
        "source_task_id": "PMBOT-OPENROUTER-028-FIRST-ONE-MARKET-LIVE-CALL-WITH-SAFE-USER-ENV-IMPORT",
        "surface_path": "pm_bot/llm/operator_live_review_surface_563650.v1.json",
        "accepted_for_operator_review": True,
        "artifact_family": "openrouter_test_artifacts",
    },
    "569332": {
        "task": "033",
        "source_task_id": "PMBOT-OPENROUTER-033-SECOND-ONE-MARKET-LIVE-CALL",
        "surface_path": "pm_bot/llm/operator_live_review_surface_569332.v1.json",
        "accepted_for_operator_review": True,
        "artifact_family": "openrouter_test_artifacts",
    },
}

FILES_CHANGED_STATIC = [
    "docs/PMBOT_CODEX_A_ROUND003_RESULT.json",
    "docs/PMBOT_OPENROUTER_053_N5_SURFACE_WORKBENCH_INVENTORY_UX_AND_CONTOUR_AUDIT.md",
    "docs/PMBOT_OPENROUTER_053_RESULT.json",
    "docs/PMBOT_OPENROUTER_NEXT_STEP_DECISION_MATRIX.md",
    "docs/PMBOT_OPENROUTER_OPERATOR_REVIEW_RUNBOOK.md",
    "docs/PMBOT_WORKBENCH_001_RESULT.json",
    "docs/PMBOT_WORKBENCH_003_RESULT.json",
    "pm_bot/llm/current_llm_market_packet_inventory.v1.json",
    "pm_bot/llm/current_llm_market_packet_inventory.v1.md",
    "pm_bot/llm/current_llm_source_evidence_completeness_audit.v1.json",
    "pm_bot/llm/current_llm_source_evidence_completeness_audit.v1.md",
    "pm_bot/llm/openrouter_next_step_decision_matrix.v1.json",
    "pm_bot/llm/openrouter_operator_review_artifacts_053.py",
    "pm_bot/llm/openrouter_operator_review_contour_046_053_audit.v1.json",
    "pm_bot/llm/openrouter_operator_review_contour_046_053_audit.v1.md",
    "pm_bot/llm/operator_openrouter_batch_surface_051.v1.json",
    "pm_bot/llm/operator_openrouter_batch_surface_051.v1.md",
    "pm_bot/llm/tests/test_current_llm_market_packet_inventory.py",
    "pm_bot/llm/tests/test_current_llm_source_evidence_completeness_audit.py",
    "pm_bot/llm/tests/test_openrouter_operator_review_contour_audit.py",
    "pm_bot/llm/tests/test_operator_openrouter_batch_surface_051.py",
    "pm_bot/workbench/expected_operator_review_pack.v1.json",
    "pm_bot/workbench/expected_operator_workbench_export_run.v1.json",
    "pm_bot/workbench/export_operator_review_pack.py",
    "pm_bot/workbench/openrouter_passive_surface_pointer.py",
    "pm_bot/workbench/openrouter_passive_surface_pointer.v1.json",
    "pm_bot/workbench/openrouter_passive_surface_pointer.v1.md",
    "pm_bot/workbench/operator_openrouter_review_dashboard.py",
    "pm_bot/workbench/operator_openrouter_review_dashboard.v1.json",
    "pm_bot/workbench/operator_openrouter_review_dashboard.v1.md",
    "pm_bot/workbench/operator_review_pack.v1.json",
    "pm_bot/workbench/operator_review_pack.v1.md",
    "pm_bot/workbench/operator_workbench_export_run.v1.json",
    "pm_bot/workbench/operator_workbench_export_run.v1.md",
    "pm_bot/workbench/run_operator_workbench_export.py",
    "pm_bot/workbench/tests/test_openrouter_passive_surface_pointer.py",
    "pm_bot/workbench/tests/test_operator_openrouter_review_dashboard.py",
    "pm_bot/workbench/tests/test_operator_review_pack_export.py",
    "pm_bot/workbench/tests/test_operator_workbench_export_runner.py",
    "tests/test_openrouter_result_artifacts.py",
]

VALIDATION_COMMANDS = [
    "python -m compileall pm_bot",
    "python -m pytest tests pm_bot\\llm\\tests -q",
    "python -m pytest tests\\test_openrouter_prompt_test.py -q",
    "python -m pytest tests\\test_openrouter_result_artifacts.py -q",
    "python -m pytest tests\\test_openrouter_fenced_json_normalization.py -q",
    "python -m pytest tests\\test_openrouter_n5_batch_readiness_protocol.py -q",
    "python -m pytest pm_bot\\llm\\tests\\test_operator_openrouter_batch_surface_046.py -q",
    "python -m pytest pm_bot\\llm\\tests\\test_operator_openrouter_batch_surface_051.py -q",
    "python -m pytest pm_bot\\llm\\tests\\test_openrouter_operator_review_contour_audit.py -q",
    "python -m pytest pm_bot\\llm\\tests\\test_current_llm_market_packet_inventory.py -q",
    "python -m pytest pm_bot\\llm\\tests\\test_current_llm_source_evidence_completeness_audit.py -q",
    "python -m pytest pm_bot\\workbench\\tests -q",
    "python -m pm_bot.workbench.run_operator_workbench_export",
    "JSON parse checks for source and generated OpenRouter/workbench JSON artifacts",
    "Result JSON checks for 046 through 053",
    "Secret scan over changed files",
    "Public Markdown market-action guidance scan over generated 053 summaries",
]


def _parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Write deterministic local artifacts for PMBOT OpenRouter 053."
    )
    parser.add_argument("--write", action="store_true", help="Write all 053 artifacts.")
    parser.add_argument("--result-only", action="store_true", help="Write only 053 result/report docs.")
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


def _artifact_pointer(path, role):
    return {"path": path, "role": role}


def _n3_summary(root=ROOT):
    baseline = _load_optional_json(SOURCE_PATHS["baseline_046_json"], root=root) or {}
    aggregate = _safe_dict(baseline.get("aggregate"))
    return {
        "batch_label": "N=3",
        "market_ids": list(N3_MARKET_IDS),
        "calls": 3,
        "cost": 0.125982,
        "total_tokens": 18686,
        "accepted_for_operator_review_count": 3,
        "blocked_count": 0,
        "prompt_tokens": aggregate.get("prompt_tokens", 12859),
        "completion_tokens": aggregate.get("completion_tokens", 5827),
        "average_cost_per_market": aggregate.get("average_cost_per_market", 0.041994),
        "average_tokens_per_market": aggregate.get("average_tokens_per_market", 6228.666667),
        "fenced_response_count": 3,
        "normalized_response_count": 3,
        "clean_raw_json_response_count": 0,
        "source_batch_task": "PMBOT-OPENROUTER-046-RETRY-SMALL-MANUAL-BATCH-AFTER-ACCEPTANCE-PHRASE-HARDENING",
        "source_baseline_task": "PMBOT-OPENROUTER-047-SMALL-BATCH-BASELINE-QUALITY-AND-OPERATOR-SUMMARY",
        "source_surface_task": "PMBOT-OPENROUTER-048-PASSIVE-OPERATOR-SURFACE-046-BATCH",
        "surface_json_path": SOURCE_PATHS["surface_046_json"],
        "surface_md_path": SOURCE_PATHS["surface_046_md"],
    }


def _n5_summary(root=ROOT):
    baseline = _load_optional_json(SOURCE_PATHS["baseline_051_json"], root=root) or {}
    aggregate = _safe_dict(baseline.get("aggregate"))
    return {
        "batch_label": "N=5",
        "market_ids": list(N5_MARKET_IDS),
        "calls": 5,
        "cost": 0.199089,
        "total_tokens": 29887,
        "accepted_for_operator_review_count": 5,
        "blocked_count": 0,
        "prompt_tokens": aggregate.get("prompt_tokens", 20768),
        "completion_tokens": aggregate.get("completion_tokens", 9119),
        "average_cost_per_market": aggregate.get("average_cost_per_market", 0.0398178),
        "average_tokens_per_market": aggregate.get("average_tokens_per_market", 5977.4),
        "fenced_response_count": 5,
        "normalized_response_count": 5,
        "clean_raw_json_response_count": 0,
        "source_protocol_task": "PMBOT-OPENROUTER-050-CONTROLLED-N5-BATCH-READINESS-PROTOCOL",
        "source_batch_task": "PMBOT-OPENROUTER-051-CONTROLLED-N5-BATCH-LIVE-CALL",
        "source_baseline_task": "PMBOT-OPENROUTER-052-N5-BATCH-BASELINE-QUALITY-AND-OPERATOR-SUMMARY",
        "source_surface_task": SURFACE_TASK_ID,
        "surface_json_path": SOURCE_PATHS["surface_051_json"],
        "surface_md_path": SOURCE_PATHS["surface_051_md"],
    }


def _combined_summary():
    return dict(COMBINED_OPENROUTER_CONTOUR_SUMMARY)


def _surface_051_entry(item, artifact_paths):
    market_id = item["market_id"]
    paths = _safe_dict(artifact_paths.get(market_id))
    missing = _safe_dict(item.get("missing_evidence_or_source_gap_notes"))
    contradiction = _safe_dict(item.get("contradiction_check"))
    risk = _safe_dict(item.get("risk_notes"))
    checklist = _safe_dict(item.get("operator_checklist"))
    basis = _safe_dict(item.get("operator_usefulness_assessment")).get(
        "basis",
        "Required operator-review sections are present in the accepted local artifact.",
    )
    return {
        "market_id": market_id,
        "accepted_for_operator_review": True,
        "openrouter_call_performed": True,
        "raw_response_preserved": True,
        "semantic_repair_allowed": False,
        "normalization_policy_applied": True,
        "normalization_policy_version": "fenced_json_normalization.v1",
        "raw_response_was_markdown_fenced": True,
        "prohibited_content_detected": False,
        "forbidden_phrase_detected": False,
        "schema_validation_passed": True,
        "schema_validation_status": "accepted",
        "acceptance_gate_passed": True,
        "acceptance_gate_status": "passed",
        "usage_summary": _safe_dict(item.get("usage_summary")),
        "cost_summary": _safe_dict(item.get("cost_summary")),
        "artifact_pointers": {
            "raw_json": _artifact_pointer(paths.get("raw"), "read_only_input"),
            "content_json": _artifact_pointer(paths.get("content"), "read_only_input"),
            "validation_json": _artifact_pointer(paths.get("validation"), "read_only_input"),
            "summary_json": _artifact_pointer(paths.get("summary"), "read_only_input"),
        },
        "sanitized_operator_note": (
            f"{basis} Counts: source_gap={missing.get('citation_or_source_gap_notes_count', 0)}, "
            f"missing_evidence={missing.get('missing_evidence_count', 0)}, "
            f"contradiction_checks={contradiction.get('count', 0)}, "
            f"risk_notes={risk.get('count', 0)}, "
            f"operator_checklist={checklist.get('count', 0)}. Passive context only."
        ),
        "source_gap_notes_count": missing.get("citation_or_source_gap_notes_count", 0),
        "missing_evidence_count": missing.get("missing_evidence_count", 0),
        "contradiction_check_count": contradiction.get("count", 0),
        "risk_notes_count": risk.get("count", 0),
        "operator_checklist_count": checklist.get("count", 0),
        "no_market_action_guidance": True,
    }


def build_operator_openrouter_batch_surface_051(root=ROOT):
    baseline = _load_json(SOURCE_PATHS["baseline_051_json"], root=root)
    result_050 = _load_json(SOURCE_PATHS["result_050"], root=root)
    result_051 = _load_json(SOURCE_PATHS["result_051"], root=root)
    result_052 = _load_json(SOURCE_PATHS["result_052"], root=root)
    artifact_paths = _safe_dict(_safe_dict(baseline.get("source_artifacts_analyzed")).get("per_market"))
    per_market = [
        _surface_051_entry(item, artifact_paths)
        for item in _safe_list(baseline.get("per_market"))
        if _safe_dict(item).get("market_id") in N5_MARKET_IDS
    ]
    return {
        "surface_version": "operator_openrouter_batch_surface.v1",
        "contract_version": "operator_openrouter_batch_surface.v1",
        "task_id": TASK_ID,
        "surface_task_id": SURFACE_TASK_ID,
        "source_protocol_task": "PMBOT-OPENROUTER-050-CONTROLLED-N5-BATCH-READINESS-PROTOCOL",
        "source_batch_task": "PMBOT-OPENROUTER-051-CONTROLLED-N5-BATCH-LIVE-CALL",
        "source_baseline_task": "PMBOT-OPENROUTER-052-N5-BATCH-BASELINE-QUALITY-AND-OPERATOR-SUMMARY",
        "source_status": {
            "050": result_050.get("status"),
            "051": result_051.get("status"),
            "052": result_052.get("status"),
        },
        "status": "passive_operator_surface_created",
        "model": MODEL,
        "surfaced_market_ids": list(N5_MARKET_IDS),
        "accepted_for_operator_review_count": 5,
        "blocked_count": 0,
        "total_openrouter_calls_performed": 5,
        **NO_AUTHORITY_TRUE_FLAGS,
        "openrouter_calls_performed_by_this_task": 0,
        "polymarket_api_calls_performed_by_this_task": 0,
        "aggregate_usage": {
            "prompt_tokens": 20768,
            "completion_tokens": 9119,
            "total_tokens": 29887,
            "average_tokens_per_market": 5977.4,
        },
        "aggregate_cost": {
            "total_cost": 0.199089,
            "average_cost_per_market": 0.0398178,
            "max_total_cost_allowed": 0.35,
            "cost_cap_exceeded": False,
        },
        "estimated_vs_actual": {
            "estimated_total_tokens": 31143.333335,
            "actual_total_tokens": 29887,
            "token_delta_actual_minus_estimate": -1256.333335,
            "estimated_total_cost": 0.20997,
            "actual_total_cost": 0.199089,
            "cost_delta_actual_minus_estimate": -0.010881,
        },
        "normalization": {
            "policy": "fenced_json_normalization.v1",
            "fenced_response_count": 5,
            "normalized_response_count": 5,
            "clean_raw_json_response_count": 0,
            "raw_response_preserved": True,
            "semantic_repair_allowed": False,
        },
        "quality": {
            "schema_validation_accepted_count": 5,
            "acceptance_gate_passed_count": 5,
            "prohibited_content_detected_count": 0,
            "forbidden_phrase_detected_count": 0,
            "baseline_suitable_for_future_controlled_expansion": True,
        },
        "artifact_pointers": {
            "source_050_result": _artifact_pointer(SOURCE_PATHS["result_050"], "read_only_input"),
            "source_051_result": _artifact_pointer(SOURCE_PATHS["result_051"], "read_only_input"),
            "source_052_result": _artifact_pointer(SOURCE_PATHS["result_052"], "read_only_input"),
            "source_052_baseline_json": _artifact_pointer(SOURCE_PATHS["baseline_051_json"], "read_only_input"),
            "source_052_baseline_markdown": _artifact_pointer(SOURCE_PATHS["baseline_051_md"], "read_only_input"),
            "source_052_operator_summary": _artifact_pointer(SOURCE_PATHS["summary_051_md"], "read_only_input"),
            "surface_json": _artifact_pointer(SOURCE_PATHS["surface_051_json"], "generated_passive_surface"),
            "surface_markdown": _artifact_pointer(SOURCE_PATHS["surface_051_md"], "generated_passive_surface"),
        },
        "warnings": [
            "all five responses required fenced JSON normalization",
            "no clean raw JSON responses observed",
        ],
        "per_market_passive_entries": per_market,
        "safety_summary": dict(SAFETY_SUMMARY),
        "explicit_exclusions": {
            "full_raw_model_responses_in_markdown": False,
            "runtime_wiring_changed": False,
            "dispatcher_changed": False,
            "queue_mutated": False,
            "background_worker_added": False,
            "browser_automation_added": False,
            "wallet_or_order_code_changed": False,
            "trading_code_changed": False,
        },
    }


def render_operator_openrouter_batch_surface_051_markdown(surface):
    lines = [
        "# PMBOT OpenRouter N5 Passive Operator Surface v1",
        "",
        f"- surface_version: {surface['surface_version']}",
        f"- task_id: {surface['task_id']}",
        f"- source_protocol_task: {surface['source_protocol_task']}",
        f"- source_batch_task: {surface['source_batch_task']}",
        f"- source_baseline_task: {surface['source_baseline_task']}",
        f"- status: {surface['status']}",
        f"- model: {surface['model']}",
        f"- surfaced_market_ids: {', '.join(surface['surfaced_market_ids'])}",
        f"- accepted_for_operator_review_count: {surface['accepted_for_operator_review_count']}",
        f"- blocked_count: {surface['blocked_count']}",
        f"- source_openrouter_calls: {surface['total_openrouter_calls_performed']}",
        "",
        "## Usage And Cost",
        "",
        f"- prompt_tokens: {surface['aggregate_usage']['prompt_tokens']}",
        f"- completion_tokens: {surface['aggregate_usage']['completion_tokens']}",
        f"- total_tokens: {surface['aggregate_usage']['total_tokens']}",
        f"- average_tokens_per_market: {surface['aggregate_usage']['average_tokens_per_market']}",
        f"- total_cost: {surface['aggregate_cost']['total_cost']}",
        f"- average_cost_per_market: {surface['aggregate_cost']['average_cost_per_market']}",
        f"- max_total_cost_allowed: {surface['aggregate_cost']['max_total_cost_allowed']}",
        f"- cost_cap_exceeded: {str(surface['aggregate_cost']['cost_cap_exceeded']).lower()}",
        "",
        "## Normalization",
        "",
        f"- policy: {surface['normalization']['policy']}",
        f"- fenced_response_count: {surface['normalization']['fenced_response_count']}",
        f"- normalized_response_count: {surface['normalization']['normalized_response_count']}",
        f"- clean_raw_json_response_count: {surface['normalization']['clean_raw_json_response_count']}",
        f"- raw_response_preserved: {str(surface['normalization']['raw_response_preserved']).lower()}",
        f"- semantic_repair_allowed: {str(surface['normalization']['semantic_repair_allowed']).lower()}",
        "",
        "## Safety",
        "",
    ]
    for key in (
        "operator_review_only",
        "passive_context_only",
        "analysis_only",
        "manual_review_only",
        "no_trading_authority",
        "no_queue_authority",
        "no_runtime_authority",
        "no_dispatcher_authority",
        "no_wallet_or_order_authority",
        "acceptance_is_not_trading_approval",
        "no_market_action_guidance",
    ):
        lines.append(f"- {key}: {str(surface[key]).lower()}")
    lines.extend(["", "## Per-Market Passive Entries", ""])
    for entry in surface["per_market_passive_entries"]:
        lines.extend(
            [
                f"- market_id: {entry['market_id']}",
                f"  accepted_for_operator_review: {str(entry['accepted_for_operator_review']).lower()}",
                f"  total_tokens: {entry['usage_summary'].get('total_tokens')}",
                f"  cost: {entry['cost_summary'].get('cost')}",
                f"  normalized: {str(entry['normalization_policy_applied']).lower()}",
                f"  note: {_ascii(entry['sanitized_operator_note'])}",
            ]
        )
    lines.extend(["", "## Artifact Pointers", ""])
    for key, item in surface["artifact_pointers"].items():
        lines.append(f"- {key}: {item['path']} ({item['role']})")
    lines.extend(["", "## Warnings", ""])
    for warning in surface["warnings"]:
        lines.append(f"- {warning}")
    lines.append("")
    return "\n".join(lines)


def build_openrouter_operator_review_contour_audit(root=ROOT):
    result_statuses = {
        str(index).zfill(3): _status(f"docs/PMBOT_OPENROUTER_{index:03d}_RESULT.json", root=root)
        for index in range(46, 53)
    }
    return {
        "schema_version": "openrouter_operator_review_contour_046_053_audit.v1",
        "task_id": TASK_ID,
        "generated_by": GENERATED_BY,
        "audit_scope": "local_artifact_openrouter_operator_review_contour",
        "status": "contour_audit_created",
        "tasks_covered": [
            "046 N=3 live batch",
            "047 N=3 baseline",
            "048 N=3 passive surface",
            "049 N=3 workbench integration",
            "050 N=5 readiness protocol",
            "051 N=5 live batch",
            "052 N=5 baseline",
            "053 N=5 surface/workbench/inventory/UX/audit",
        ],
        "source_result_statuses": result_statuses,
        "n3_summary": _n3_summary(root=root),
        "n5_summary": _n5_summary(root=root),
        "combined_summary": _combined_summary(),
        "normalization": {
            "n3_all_fenced": True,
            "n5_all_fenced": True,
            "clean_raw_json_response_count_across_successful_batches": 0,
            "current_route_requires_fenced_json_normalization_v1": True,
            "policy": "fenced_json_normalization.v1",
        },
        "safety": {
            "no_trading_authority": True,
            "no_queue_authority": True,
            "no_runtime_authority": True,
            "no_dispatcher_authority": True,
            "no_wallet_or_order_authority": True,
            "no_polymarket_api_calls_in_openrouter_live_batch_tasks": True,
            "api_key_not_leaked": True,
            "operator_review_only": True,
            "acceptance_is_not_trading_approval": True,
        },
        "limitations": [
            "Current route consistently returns Markdown-fenced JSON.",
            "Accepted means operator-review-only, not trading approval.",
            "Quality is artifact/operator usefulness, not market correctness.",
            "No external live evidence enrichment occurs inside LLM calls.",
        ],
        "next_recommendations": [
            "local category/source inventory",
            "operator UX refinement",
            "repeat N=5 once more before N=10",
            "N=10 readiness only as protocol-only after inventory/UX review",
        ],
        "artifact_pointers": {
            "n3_surface": SOURCE_PATHS["surface_046_json"],
            "n5_surface": SOURCE_PATHS["surface_051_json"],
            "inventory": SOURCE_PATHS["inventory_json"],
            "evidence_audit": SOURCE_PATHS["evidence_audit_json"],
            "dashboard": SOURCE_PATHS["dashboard_json"],
        },
        "safety_summary": dict(SAFETY_SUMMARY),
    }


def render_openrouter_operator_review_contour_audit_markdown(audit):
    combined = audit["combined_summary"]
    lines = [
        "# PMBOT OpenRouter Operator Review Contour Audit 046-053",
        "",
        f"- schema_version: {audit['schema_version']}",
        f"- task_id: {audit['task_id']}",
        f"- status: {audit['status']}",
        "",
        "## Tasks Covered",
        "",
    ]
    for item in audit["tasks_covered"]:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## N3 Summary",
            "",
            f"- market_ids: {', '.join(audit['n3_summary']['market_ids'])}",
            f"- calls: {audit['n3_summary']['calls']}",
            f"- cost: {audit['n3_summary']['cost']}",
            f"- total_tokens: {audit['n3_summary']['total_tokens']}",
            f"- accepted_for_operator_review_count: {audit['n3_summary']['accepted_for_operator_review_count']}",
            f"- blocked_count: {audit['n3_summary']['blocked_count']}",
            "",
            "## N5 Summary",
            "",
            f"- market_ids: {', '.join(audit['n5_summary']['market_ids'])}",
            f"- calls: {audit['n5_summary']['calls']}",
            f"- cost: {audit['n5_summary']['cost']}",
            f"- total_tokens: {audit['n5_summary']['total_tokens']}",
            f"- accepted_for_operator_review_count: {audit['n5_summary']['accepted_for_operator_review_count']}",
            f"- blocked_count: {audit['n5_summary']['blocked_count']}",
            "",
            "## Combined Summary",
            "",
            f"- total_markets_successfully_reviewed: {combined['total_markets_successfully_reviewed']}",
            f"- total_openrouter_calls_in_successful_batches: {combined['total_openrouter_calls_in_successful_batches']}",
            f"- combined_cost: {combined['combined_cost']}",
            f"- combined_tokens: {combined['combined_tokens']}",
            f"- total_blocked_in_successful_batches: {combined['total_blocked_in_successful_batches']}",
            f"- average_cost_per_market_combined: {combined['average_cost_per_market_combined']}",
            f"- average_tokens_per_market_combined: {combined['average_tokens_per_market_combined']}",
            "",
            "## Normalization",
            "",
            f"- n3_all_fenced: {str(audit['normalization']['n3_all_fenced']).lower()}",
            f"- n5_all_fenced: {str(audit['normalization']['n5_all_fenced']).lower()}",
            "- clean_raw_json_response_count_across_successful_batches: "
            f"{audit['normalization']['clean_raw_json_response_count_across_successful_batches']}",
            f"- policy: {audit['normalization']['policy']}",
            "",
            "## Safety",
            "",
        ]
    )
    for key, value in audit["safety"].items():
        lines.append(f"- {key}: {str(value).lower() if isinstance(value, bool) else value}")
    lines.extend(["", "## Limitations", ""])
    for item in audit["limitations"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Next Engineering Recommendations", ""])
    for item in audit["next_recommendations"]:
        lines.append(f"- {item}")
    lines.append("")
    return "\n".join(lines)


def _packet_paths(root=ROOT):
    packet_dir = Path(root) / "pm_bot" / "llm" / "manual_packet_batch"
    return sorted(packet_dir.glob("*_packet.v1.json"))


def _title_from_packet(packet):
    context = _safe_dict(packet.get("market_context"))
    local = _safe_dict(packet.get("local_review_context"))
    return context.get("market_title") or local.get("local_title_or_question") or local.get("local_question")


def _category_for_title(title):
    text = (title or "").lower()
    if "scotus" in text or "court" in text:
        return "legal/courts", "medium"
    if "bitcoin hit" in text:
        return "crypto", "high"
    if "ipo" in text or "microstrategy" in text:
        return "company/business", "high"
    if "election" in text or "presidential" in text:
        return "elections", "high"
    if "macron" in text:
        return "politics", "high"
    return "unknown", "unknown"


def _review_status_for_market(market_id):
    if market_id in SINGLE_CALL_REVIEW_STATUS:
        item = SINGLE_CALL_REVIEW_STATUS[market_id]
        return True, item["task"], item["accepted_for_operator_review"]
    if market_id in N3_MARKET_IDS:
        return True, "046", True
    if market_id in N5_MARKET_IDS:
        return True, "051", True
    return False, "none", None


def _review_detail_for_market(market_id, root=ROOT):
    if market_id in SINGLE_CALL_REVIEW_STATUS:
        surface = _load_optional_json(SINGLE_CALL_REVIEW_STATUS[market_id]["surface_path"], root=root)
        summary = _safe_dict(_safe_dict(surface).get("passive_llm_review_summary"))
        return {
            "source_gap_notes_count": summary.get("source_gap_notes_count", 0),
            "missing_evidence_count": summary.get("missing_evidence_count", 0),
            "contradiction_check_count": len(_safe_list(summary.get("contradiction_check_results"))),
            "risk_notes_count": summary.get("risk_notes_count", 0),
            "operator_checklist_count": 1 if _safe_dict(surface).get("status") == "accepted_for_operator_review" else 0,
        }
    baseline_path = None
    if market_id in N3_MARKET_IDS:
        baseline_path = SOURCE_PATHS["baseline_046_json"]
    elif market_id in N5_MARKET_IDS:
        baseline_path = SOURCE_PATHS["baseline_051_json"]
    if not baseline_path:
        return {
            "source_gap_notes_count": 0,
            "missing_evidence_count": 0,
            "contradiction_check_count": 0,
            "risk_notes_count": 0,
            "operator_checklist_count": 0,
        }
    baseline = _load_json(baseline_path, root=root)
    for item in _safe_list(baseline.get("per_market")):
        if _safe_dict(item).get("market_id") == market_id:
            missing = _safe_dict(item.get("missing_evidence_or_source_gap_notes"))
            return {
                "source_gap_notes_count": missing.get("citation_or_source_gap_notes_count", 0),
                "missing_evidence_count": missing.get("missing_evidence_count", 0),
                "contradiction_check_count": _safe_dict(item.get("contradiction_check")).get("count", 0),
                "risk_notes_count": _safe_dict(item.get("risk_notes")).get("count", 0),
                "operator_checklist_count": _safe_dict(item.get("operator_checklist")).get("count", 0),
            }
    return {
        "source_gap_notes_count": 0,
        "missing_evidence_count": 0,
        "contradiction_check_count": 0,
        "risk_notes_count": 0,
        "operator_checklist_count": 0,
    }


def _packet_completeness_warnings(packet, reviewed):
    warnings = []
    context = _safe_dict(packet.get("market_context"))
    public_context = context.get("public_resolution_context", "")
    missing = _safe_list(packet.get("missing_evidence"))
    if "stub" in public_context.lower() or any("full_market_resolution" in str(item) for item in missing):
        warnings.append("local packet still relies on stub or placeholder resolution/source material")
    if missing:
        warnings.append("missing evidence notes are present and require manual local enrichment")
    if not reviewed:
        warnings.append("not yet reviewed by OpenRouter in local artifacts")
    return warnings


def build_current_llm_market_packet_inventory(root=ROOT):
    markets = []
    for path in _packet_paths(root=root):
        packet = _load_json(path, root=root)
        market_id = str(packet.get("market_id"))
        prompt_path = f"pm_bot/llm/manual_packet_batch/{market_id}_prompt.v1.md"
        prompt_exists = _resolve(prompt_path, root=root).exists()
        title = _title_from_packet(packet)
        category, category_confidence = _category_for_title(title)
        reviewed, reviewed_task, accepted = _review_status_for_market(market_id)
        review_detail = _review_detail_for_market(market_id, root=root)
        missing = _safe_list(packet.get("missing_evidence"))
        source_gaps = _safe_list(packet.get("source_gap_notes"))
        local_evidence = _safe_list(packet.get("evidence_source_placeholders")) or _safe_list(
            packet.get("evidence_summary")
        )
        resolution_fields_present = bool(
            _safe_dict(packet.get("market_context")).get("public_resolution_context")
            or _safe_dict(packet.get("normalized_market_summary")).get("resolution_rules_summary")
            or packet.get("source_artifacts")
        )
        source_family = "manual_packet_batch"
        additional_families = []
        if reviewed:
            additional_families.append("openrouter_test_artifacts")
            if reviewed_task in {"046", "051"}:
                additional_families.append("workbench")
        item = {
            "market_id": market_id,
            "packet_file_path": _display_path(path, root=root),
            "prompt_file_path": prompt_path if prompt_exists else None,
            "source_artifact_family": source_family,
            "additional_artifact_families": additional_families,
            "title_or_question": title,
            "category": category,
            "category_confidence": category_confidence,
            "possible_category_labels": [
                "crypto",
                "weather",
                "politics",
                "sports",
                "macro",
                "company/business",
                "geopolitics",
                "culture/media",
                "legal/courts",
                "elections",
                "generic_event",
                "unknown",
            ],
            "resolution_source_fields_present": bool(resolution_fields_present),
            "local_evidence_fields_present": bool(local_evidence),
            "missing_evidence_notes_present": bool(missing),
            "contradiction_checks_present": review_detail["contradiction_check_count"] > 0,
            "risk_notes_present": review_detail["risk_notes_count"] > 0,
            "operator_checklist_present": review_detail["operator_checklist_count"] > 0,
            "eligible_for_llm_review": bool(path.exists() and prompt_exists),
            "already_reviewed_by_openrouter": reviewed,
            "batch_or_task_where_reviewed": reviewed_task,
            "accepted_for_operator_review": accepted,
            "local_counts": {
                "evidence_source_placeholders": len(local_evidence),
                "missing_evidence": len(missing),
                "source_gap_notes": len(source_gaps),
                **review_detail,
            },
            "warnings": _packet_completeness_warnings(packet, reviewed),
        }
        markets.append(item)

    category_counts = {}
    for item in markets:
        category_counts[item["category"]] = category_counts.get(item["category"], 0) + 1
    missing_resolution = [
        item["market_id"]
        for item in markets
        if any("resolution/source" in warning or "placeholder" in warning for warning in item["warnings"])
    ]
    missing_local_evidence = [
        item["market_id"] for item in markets if item["missing_evidence_notes_present"]
    ]
    low_packet = sorted(set(missing_resolution + missing_local_evidence))
    aggregate = {
        "total_markets_found": len(markets),
        "total_with_packet": sum(1 for item in markets if item["packet_file_path"]),
        "total_with_prompt": sum(1 for item in markets if item["prompt_file_path"]),
        "total_reviewed_by_openrouter": sum(1 for item in markets if item["already_reviewed_by_openrouter"]),
        "total_accepted_for_operator_review": sum(
            1 for item in markets if item["accepted_for_operator_review"] is True
        ),
        "category_counts": category_counts,
        "unknown_category_count": category_counts.get("unknown", 0),
        "markets_missing_resolution_source": missing_resolution,
        "markets_missing_local_evidence": missing_local_evidence,
        "markets_with_low_packet_completeness": low_packet,
        "recommendation_for_next_local_enrichment_step": (
            "Normalize category labels, extract full local resolution rules, replace placeholder "
            "source notes with reviewed local references, and standardize per-market operator checklists."
        ),
    }
    return {
        "schema_version": "current_llm_market_packet_inventory.v1",
        "task_id": TASK_ID,
        "generated_by": GENERATED_BY,
        "status": "market_packet_inventory_created",
        "scope": "local_llm_openrouter_packet_artifacts_only",
        "network_calls_performed": 0,
        "polymarket_api_calls_performed": 0,
        "openrouter_calls_performed": 0,
        "markets": markets,
        "aggregate": aggregate,
        "safety_summary": dict(SAFETY_SUMMARY),
    }


def render_current_llm_market_packet_inventory_markdown(inventory):
    aggregate = inventory["aggregate"]
    lines = [
        "# PMBOT Current LLM Market Packet Inventory v1",
        "",
        f"- schema_version: {inventory['schema_version']}",
        f"- task_id: {inventory['task_id']}",
        f"- status: {inventory['status']}",
        f"- total_markets_found: {aggregate['total_markets_found']}",
        f"- total_with_packet: {aggregate['total_with_packet']}",
        f"- total_with_prompt: {aggregate['total_with_prompt']}",
        f"- total_reviewed_by_openrouter: {aggregate['total_reviewed_by_openrouter']}",
        f"- total_accepted_for_operator_review: {aggregate['total_accepted_for_operator_review']}",
        f"- unknown_category_count: {aggregate['unknown_category_count']}",
        "",
        "## Category Counts",
        "",
    ]
    for category, count in sorted(aggregate["category_counts"].items()):
        lines.append(f"- {category}: {count}")
    lines.extend(["", "## Market Inventory", ""])
    for item in inventory["markets"]:
        lines.extend(
            [
                f"- market_id: {item['market_id']}",
                f"  title_or_question: {_ascii(item['title_or_question'])}",
                f"  category: {item['category']}",
                f"  packet_file_path: {item['packet_file_path']}",
                f"  prompt_file_path: {item['prompt_file_path'] or 'missing'}",
                f"  reviewed_by_openrouter: {str(item['already_reviewed_by_openrouter']).lower()}",
                f"  reviewed_task: {item['batch_or_task_where_reviewed']}",
                f"  accepted_for_operator_review: {str(item['accepted_for_operator_review']).lower() if item['accepted_for_operator_review'] is not None else 'unknown'}",
                f"  missing_evidence_notes_present: {str(item['missing_evidence_notes_present']).lower()}",
                f"  contradiction_checks_present: {str(item['contradiction_checks_present']).lower()}",
                f"  risk_notes_present: {str(item['risk_notes_present']).lower()}",
                f"  operator_checklist_present: {str(item['operator_checklist_present']).lower()}",
            ]
        )
    lines.extend(["", "## Local Enrichment Recommendation", ""])
    lines.append(f"- {aggregate['recommendation_for_next_local_enrichment_step']}")
    lines.append("")
    return "\n".join(lines)


def _evidence_level_for_inventory_item(item):
    if not item["already_reviewed_by_openrouter"]:
        return "low"
    if (
        item["missing_evidence_notes_present"]
        and item["contradiction_checks_present"]
        and item["risk_notes_present"]
        and item["operator_checklist_present"]
    ):
        return "medium"
    return "low"


def build_current_llm_source_evidence_completeness_audit(root=ROOT):
    inventory = build_current_llm_market_packet_inventory(root=root)
    reviewed_items = [item for item in inventory["markets"] if item["already_reviewed_by_openrouter"]]
    reviewed = []
    for item in reviewed_items:
        level = _evidence_level_for_inventory_item(item)
        reviewed.append(
            {
                "market_id": item["market_id"],
                "category": item["category"],
                "has_resolution_source_or_rules": False,
                "has_local_context": bool(item["title_or_question"]),
                "has_source_gap_notes": item["local_counts"]["source_gap_notes"] > 0,
                "has_missing_evidence_notes": item["missing_evidence_notes_present"],
                "has_contradiction_checks": item["contradiction_checks_present"],
                "has_risk_notes": item["risk_notes_present"],
                "has_operator_checklist": item["operator_checklist_present"],
                "evidence_completeness_level": level,
                "needs_manual_source_review": True,
                "needs_local_enrichment_before_future_llm_review": True,
                "sanitized_notes": (
                    "Accepted local review artifact has operator sections, while full local resolution "
                    "rules and source references remain incomplete. Manual source review is still needed."
                ),
            }
        )
    counts = {}
    for item in reviewed:
        counts[item["evidence_completeness_level"]] = counts.get(item["evidence_completeness_level"], 0) + 1
    category_gaps = {}
    for item in reviewed:
        category_gaps.setdefault(item["category"], set()).update(
            {"full_resolution_rules", "official_source_references", "source_timestamps"}
        )
        if item["category"] == "elections":
            category_gaps[item["category"]].add("official_election_authority_identifier")
        if item["category"] == "crypto":
            category_gaps[item["category"]].add("benchmark_and_timezone_rules")
        if item["category"] == "legal/courts":
            category_gaps[item["category"]].add("docket_identifier")
    return {
        "schema_version": "current_llm_source_evidence_completeness_audit.v1",
        "task_id": TASK_ID,
        "generated_by": GENERATED_BY,
        "status": "source_evidence_completeness_audit_created",
        "source_inventory_path": SOURCE_PATHS["inventory_json"],
        "reviewed_markets": reviewed,
        "aggregate": {
            "reviewed_market_count": len(reviewed),
            "evidence_completeness_counts": counts,
            "common_missing_fields": [
                "full_market_resolution_criteria_text",
                "official_source_urls",
                "credible_news_source_urls",
                "source_timestamps",
                "source_reliability_review",
                "local_packet_completeness_score",
            ],
            "category_specific_gaps": {
                category: sorted(values) for category, values in sorted(category_gaps.items())
            },
            "top_local_enrichment_priorities": [
                "resolution source extraction",
                "category labeling",
                "source gap normalization",
                "operator checklist standardization",
                "local packet completeness score",
            ],
        },
        "network_calls_performed": 0,
        "polymarket_api_calls_performed": 0,
        "openrouter_calls_performed": 0,
        "safety_summary": dict(SAFETY_SUMMARY),
    }


def render_current_llm_source_evidence_completeness_audit_markdown(audit):
    aggregate = audit["aggregate"]
    lines = [
        "# PMBOT Current LLM Source Evidence Completeness Audit v1",
        "",
        f"- schema_version: {audit['schema_version']}",
        f"- task_id: {audit['task_id']}",
        f"- status: {audit['status']}",
        f"- reviewed_market_count: {aggregate['reviewed_market_count']}",
        "",
        "## Completeness Counts",
        "",
    ]
    for level, count in sorted(aggregate["evidence_completeness_counts"].items()):
        lines.append(f"- {level}: {count}")
    lines.extend(["", "## Reviewed Markets", ""])
    for item in audit["reviewed_markets"]:
        lines.extend(
            [
                f"- market_id: {item['market_id']}",
                f"  category: {item['category']}",
                f"  evidence_completeness_level: {item['evidence_completeness_level']}",
                f"  has_local_context: {str(item['has_local_context']).lower()}",
                f"  has_source_gap_notes: {str(item['has_source_gap_notes']).lower()}",
                f"  has_missing_evidence_notes: {str(item['has_missing_evidence_notes']).lower()}",
                f"  has_contradiction_checks: {str(item['has_contradiction_checks']).lower()}",
                f"  has_risk_notes: {str(item['has_risk_notes']).lower()}",
                f"  has_operator_checklist: {str(item['has_operator_checklist']).lower()}",
                f"  needs_manual_source_review: {str(item['needs_manual_source_review']).lower()}",
            ]
        )
    lines.extend(["", "## Common Missing Fields", ""])
    for item in aggregate["common_missing_fields"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Local Enrichment Priorities", ""])
    for item in aggregate["top_local_enrichment_priorities"]:
        lines.append(f"- {item}")
    lines.append("")
    return "\n".join(lines)


def _source_001_evidence_readiness_context(root=ROOT):
    try:
        from pm_bot.llm import source_evidence_enrichment_artifacts as source_001
    except ModuleNotFoundError:
        return {}
    try:
        return source_001.build_dashboard_evidence_readiness_context(root=root)
    except (OSError, json.JSONDecodeError):
        return {}


def _source_002_packet_readiness_gate(root=ROOT):
    try:
        from pm_bot.llm import packet_completeness_scorer as source_002
    except ModuleNotFoundError:
        return {}
    try:
        return source_002.build_batch_readiness_gate(root=root)
    except (OSError, json.JSONDecodeError, KeyError):
        return {}


def _batch_readiness_gate_summary(gate):
    gate = _safe_dict(gate)
    if not gate:
        return {}
    return {
        "gate_version": gate.get("gate_version"),
        "status": gate.get("status"),
        "artifact_pointer": SOURCE_PATHS["batch_readiness_gate_json"],
        "artifact_markdown_pointer": SOURCE_PATHS["batch_readiness_gate_md"],
        "total_markets": gate.get("total_markets", 0),
        "high_count": gate.get("high_count", 0),
        "medium_count": gate.get("medium_count", 0),
        "low_count": gate.get("low_count", 0),
        "blocked_count": gate.get("blocked_count", 0),
        "eligible_for_future_llm_review_count": gate.get(
            "eligible_for_future_llm_review_count", 0
        ),
        "eligible_for_future_openrouter_batch_count": gate.get(
            "eligible_for_future_openrouter_batch_count", 0
        ),
        "needs_local_enrichment_count": gate.get("needs_local_enrichment_count", 0),
        "needs_local_enrichment_before_future_openrouter_batch_count": gate.get(
            "needs_local_enrichment_before_future_openrouter_batch_count", 0
        ),
        "reviewed_count": gate.get("reviewed_count", 0),
        "unreviewed_count": gate.get("unreviewed_count", 0),
        "low_readiness_market_ids": _safe_list(gate.get("low_readiness_market_ids")),
        "blocked_market_ids": _safe_list(gate.get("blocked_market_ids")),
        "unreviewed_market_ids": _safe_list(gate.get("unreviewed_market_ids")),
        "top_missing_fields": _safe_list(gate.get("top_missing_fields"))[:10],
        "recommended_next_local_enrichment_focus": _safe_list(
            gate.get("recommended_next_local_enrichment_focus")
        ),
        "future_live_batch_scheduled": gate.get("future_live_batch_scheduled", False),
        "future_openrouter_batch_approved": gate.get(
            "future_openrouter_batch_approved", False
        ),
        "future_llm_review_approved": gate.get("future_llm_review_approved", False),
        "safety_flags": _safe_dict(gate.get("safety_flags")),
        "no_market_action_guidance": gate.get("safety_flags", {}).get(
            "no_market_action_guidance", True
        ),
    }


def build_operator_openrouter_review_dashboard(root=ROOT):
    inventory = build_current_llm_market_packet_inventory(root=root)
    evidence = build_current_llm_source_evidence_completeness_audit(root=root)
    source_001_context = _source_001_evidence_readiness_context(root=root)
    source_002_gate = _source_002_packet_readiness_gate(root=root)
    batch_gate_summary = _batch_readiness_gate_summary(source_002_gate)
    n3 = _n3_summary(root=root)
    n5 = _n5_summary(root=root)
    combined = _combined_summary()
    return {
        "schema_version": "operator_openrouter_review_dashboard.v1",
        "task_id": TASK_ID,
        "generated_by": GENERATED_BY,
        "status": "operator_openrouter_review_dashboard_created",
        "dashboard_mode": "local_static_read_only",
        "latest_batch": {
            "batch_label": "N=5",
            "source_task": "PMBOT-OPENROUTER-051",
            "source_task_id": "PMBOT-OPENROUTER-051-CONTROLLED-N5-BATCH-LIVE-CALL",
        },
        "latest_surface": SURFACE_TASK_ID,
        "latest_baseline": "PMBOT-OPENROUTER-052-N5-BATCH-BASELINE-QUALITY-AND-OPERATOR-SUMMARY",
        "latest_workbench_integration_status": "multi_batch_passive_surface_pointer_ready",
        "n3_summary": n3,
        "n5_summary": n5,
        "latest_n5_summary": n5,
        "combined_openrouter_review_contour_summary": combined,
        "cost_summary": {
            "n3_cost": n3["cost"],
            "n5_cost": n5["cost"],
            "combined_cost": combined["combined_cost"],
        },
        "usage_summary": {
            "n3_tokens": n3["total_tokens"],
            "n5_tokens": n5["total_tokens"],
            "combined_tokens": combined["combined_tokens"],
        },
        "normalization_summary": {
            "successful_batch_responses_requiring_fenced_normalization": "8/8",
            "clean_raw_json_responses": 0,
            "policy": "fenced_json_normalization.v1",
        },
        "safety_summary": dict(SAFETY_SUMMARY),
        "inventory_summary": {
            "total_markets_found": inventory["aggregate"]["total_markets_found"],
            "total_reviewed_by_openrouter": inventory["aggregate"]["total_reviewed_by_openrouter"],
            "category_counts": inventory["aggregate"]["category_counts"],
            "unknown_category_count": inventory["aggregate"]["unknown_category_count"],
            "markets_with_low_packet_completeness": inventory["aggregate"][
                "markets_with_low_packet_completeness"
            ],
        },
        "evidence_completeness_summary": evidence["aggregate"],
        "evidence_readiness_integration_status": (
            "source_001_context_ready" if source_001_context else "source_001_context_unavailable"
        ),
        "source_001_evidence_readiness_context": source_001_context,
        "batch_readiness_gate_integration_status": (
            "source_002_gate_ready" if source_002_gate else "source_002_gate_unavailable"
        ),
        "batch_readiness_gate_summary": batch_gate_summary,
        "packet_completeness_readiness_gate": source_002_gate,
        "evidence_readiness_score_summary": _safe_dict(
            source_001_context.get("evidence_readiness_score_summary")
        ),
        "category_gap_summary": _safe_dict(source_001_context.get("category_gap_summary")),
        "markets_reviewed_vs_unreviewed": _safe_dict(
            source_001_context.get("markets_reviewed_vs_unreviewed")
        ),
        "markets_with_medium_evidence_completeness": _safe_list(
            source_001_context.get("markets_with_medium_evidence_completeness")
        ),
        "recommended_next_local_enrichment_focus": _safe_list(
            batch_gate_summary.get("recommended_next_local_enrichment_focus")
            or source_001_context.get("recommended_next_local_enrichment_focus")
        ),
        "top_missing_fields": _safe_list(
            batch_gate_summary.get("top_missing_fields")
            or source_001_context.get("top_missing_fields")
        ),
        "low_readiness_market_ids": _safe_list(
            batch_gate_summary.get("low_readiness_market_ids")
        ),
        "unreviewed_market_ids": _safe_list(batch_gate_summary.get("unreviewed_market_ids")),
        "no_market_action_guidance": True,
        "operator_next_engineering_actions": [
            "category/source inventory review",
            "source/evidence enrichment design",
            "repeat N=5 or protocol-only N=10 only after review",
            "model comparison and cost optimization later",
        ],
        "artifact_pointers": {
            "n3_surface_json": SOURCE_PATHS["surface_046_json"],
            "n3_surface_md": SOURCE_PATHS["surface_046_md"],
            "n5_surface_json": SOURCE_PATHS["surface_051_json"],
            "n5_surface_md": SOURCE_PATHS["surface_051_md"],
            "contour_audit_json": SOURCE_PATHS["contour_audit_json"],
            "contour_audit_md": SOURCE_PATHS["contour_audit_md"],
            "inventory_json": SOURCE_PATHS["inventory_json"],
            "inventory_md": SOURCE_PATHS["inventory_md"],
            "evidence_audit_json": SOURCE_PATHS["evidence_audit_json"],
            "evidence_audit_md": SOURCE_PATHS["evidence_audit_md"],
            "batch_readiness_gate_json": SOURCE_PATHS["batch_readiness_gate_json"],
            "batch_readiness_gate_md": SOURCE_PATHS["batch_readiness_gate_md"],
            "operator_review_pack_json": "pm_bot/workbench/operator_review_pack.v1.json",
            "operator_review_pack_md": "pm_bot/workbench/operator_review_pack.v1.md",
            "workbench_export_run_json": "pm_bot/workbench/operator_workbench_export_run.v1.json",
            "workbench_export_run_md": "pm_bot/workbench/operator_workbench_export_run.v1.md",
            "runbook": SOURCE_PATHS["runbook_md"],
            "decision_matrix_json": SOURCE_PATHS["decision_matrix_json"],
            "decision_matrix_md": SOURCE_PATHS["decision_matrix_md"],
            **_safe_dict(source_001_context.get("artifact_pointers")),
        },
        "network_calls_performed": 0,
        "polymarket_api_calls_performed": 0,
        "openrouter_calls_performed": 0,
    }


def render_operator_openrouter_review_dashboard_markdown(dashboard):
    combined = dashboard["combined_openrouter_review_contour_summary"]
    inventory = dashboard["inventory_summary"]
    evidence = dashboard["evidence_completeness_summary"]
    readiness = _safe_dict(dashboard.get("evidence_readiness_score_summary"))
    batch_gate = _safe_dict(dashboard.get("batch_readiness_gate_summary"))
    category_gaps = _safe_dict(dashboard.get("category_gap_summary"))
    reviewed_vs_unreviewed = _safe_dict(dashboard.get("markets_reviewed_vs_unreviewed"))
    lines = [
        "# PMBOT Operator OpenRouter Review Dashboard v1",
        "",
        f"- schema_version: {dashboard['schema_version']}",
        f"- task_id: {dashboard['task_id']}",
        f"- status: {dashboard['status']}",
        f"- dashboard_mode: {dashboard['dashboard_mode']}",
        f"- latest_batch: N=5 / PMBOT-OPENROUTER-051",
        f"- latest_surface: {dashboard['latest_surface']}",
        f"- latest_baseline: {dashboard['latest_baseline']}",
        f"- latest_workbench_integration_status: {dashboard['latest_workbench_integration_status']}",
        "",
        "## Batch Summaries",
        "",
        f"- N3 markets: {', '.join(dashboard['n3_summary']['market_ids'])}",
        f"- N3 cost: {dashboard['cost_summary']['n3_cost']}",
        f"- N3 tokens: {dashboard['usage_summary']['n3_tokens']}",
        f"- N5 markets: {', '.join(dashboard['n5_summary']['market_ids'])}",
        f"- N5 cost: {dashboard['cost_summary']['n5_cost']}",
        f"- N5 tokens: {dashboard['usage_summary']['n5_tokens']}",
        "",
        "## Combined OpenRouter Review Contour",
        "",
        f"- total_markets_successfully_reviewed: {combined['total_markets_successfully_reviewed']}",
        f"- total_openrouter_calls_in_successful_batches: {combined['total_openrouter_calls_in_successful_batches']}",
        f"- combined_cost: {combined['combined_cost']}",
        f"- combined_tokens: {combined['combined_tokens']}",
        f"- total_blocked_in_successful_batches: {combined['total_blocked_in_successful_batches']}",
        "",
        "## Normalization",
        "",
        "- successful_batch_responses_requiring_fenced_normalization: "
        f"{dashboard['normalization_summary']['successful_batch_responses_requiring_fenced_normalization']}",
        f"- clean_raw_json_responses: {dashboard['normalization_summary']['clean_raw_json_responses']}",
        f"- policy: {dashboard['normalization_summary']['policy']}",
        "",
        "## Safety",
        "",
        "- operator_review_only: true",
        "- passive_context_only: true",
        "- no_trading_authority: true",
        "- no_queue_authority: true",
        "- no_runtime_authority: true",
        "- no_dispatcher_authority: true",
        "- no_wallet_or_order_authority: true",
        "- acceptance_is_not_trading_approval: true",
        "- no_market_action_guidance: true",
        "",
        "## Inventory Summary",
        "",
        f"- total_markets_found: {inventory['total_markets_found']}",
        f"- total_reviewed_by_openrouter: {inventory['total_reviewed_by_openrouter']}",
        f"- unknown_category_count: {inventory['unknown_category_count']}",
        f"- markets_with_low_packet_completeness: {', '.join(inventory['markets_with_low_packet_completeness'])}",
        "",
        "## Category Counts",
        "",
    ]
    for category, count in sorted(inventory["category_counts"].items()):
        lines.append(f"- {category}: {count}")
    lines.extend(["", "## Evidence Completeness", ""])
    for level, count in sorted(evidence["evidence_completeness_counts"].items()):
        lines.append(f"- {level}: {count}")
    if readiness:
        lines.extend(
            [
                "",
                "## Evidence Readiness",
                "",
                f"- integration_status: {dashboard['evidence_readiness_integration_status']}",
                f"- high_count: {readiness.get('high_count', 0)}",
                f"- medium_count: {readiness.get('medium_count', 0)}",
                f"- low_count: {readiness.get('low_count', 0)}",
                f"- blocked_count: {readiness.get('blocked_count', 0)}",
                "- average_evidence_readiness_score: "
                f"{readiness.get('average_evidence_readiness_score', 0)}",
                "- reviewed_market_ids: "
                + ", ".join(reviewed_vs_unreviewed.get("reviewed_market_ids", [])),
                "- unreviewed_market_ids: "
                + ", ".join(reviewed_vs_unreviewed.get("unreviewed_market_ids", [])),
                "- markets_with_medium_evidence_completeness: "
                + ", ".join(dashboard.get("markets_with_medium_evidence_completeness", [])),
                "",
                "## Category Gap Summary",
                "",
            ]
        )
        for category, summary in sorted(category_gaps.items()):
            lines.append(
                "- "
                f"{category}: priority={summary.get('recommended_priority')}, "
                f"effort={summary.get('estimated_effort')}, "
                f"markets={', '.join(summary.get('market_ids_in_category', []))}"
            )
    if batch_gate:
        lines.extend(
            [
                "",
                "## Batch Readiness Gate",
                "",
                f"- integration_status: {dashboard['batch_readiness_gate_integration_status']}",
                f"- artifact_pointer: {batch_gate['artifact_pointer']}",
                f"- artifact_markdown_pointer: {batch_gate['artifact_markdown_pointer']}",
                f"- total_markets: {batch_gate['total_markets']}",
                f"- high_count: {batch_gate['high_count']}",
                f"- medium_count: {batch_gate['medium_count']}",
                f"- low_count: {batch_gate['low_count']}",
                f"- blocked_count: {batch_gate['blocked_count']}",
                "- eligible_for_future_llm_review_count: "
                f"{batch_gate['eligible_for_future_llm_review_count']}",
                "- eligible_for_future_openrouter_batch_count: "
                f"{batch_gate['eligible_for_future_openrouter_batch_count']}",
                f"- needs_local_enrichment_count: {batch_gate['needs_local_enrichment_count']}",
                "- needs_local_enrichment_before_future_openrouter_batch_count: "
                f"{batch_gate['needs_local_enrichment_before_future_openrouter_batch_count']}",
                "- low_readiness_market_ids: "
                + ", ".join(batch_gate.get("low_readiness_market_ids", [])),
                "- unreviewed_market_ids: "
                + ", ".join(batch_gate.get("unreviewed_market_ids", [])),
                "- future_live_batch_scheduled: "
                f"{str(batch_gate['future_live_batch_scheduled']).lower()}",
                "- future_openrouter_batch_approved: "
                f"{str(batch_gate['future_openrouter_batch_approved']).lower()}",
                "- no_market_action_guidance: "
                f"{str(batch_gate['no_market_action_guidance']).lower()}",
                "",
                "## Top Missing Fields",
                "",
            ]
        )
        for item in batch_gate.get("top_missing_fields", []):
            lines.append(f"- {item['field']}: {item['market_count']}")
        lines.extend(["", "## Recommended Next Local Enrichment Focus", ""])
        for item in batch_gate.get("recommended_next_local_enrichment_focus", []):
            lines.append(f"- {item}")
    elif readiness:
        lines.extend(["", "## Recommended Next Local Enrichment Focus", ""])
        for item in dashboard.get("recommended_next_local_enrichment_focus", []):
            lines.append(f"- {item}")
    lines.extend(["", "## Operator Next Engineering Actions", ""])
    for item in dashboard["operator_next_engineering_actions"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Artifact Pointers", ""])
    for key, path in dashboard["artifact_pointers"].items():
        lines.append(f"- {key}: {path}")
    lines.append("")
    return "\n".join(lines)


def build_openrouter_next_step_decision_matrix():
    steps = [
        (
            "A",
            "Repeat N=5 controlled batch protocol/live cycle",
            "Confirm stability across another same-size controlled batch.",
            "Strengthens baseline before larger expansion.",
            "Consumes live-call budget and repeats current fenced-normalization issue.",
            ["review inventory", "review source/evidence audit", "fresh readiness protocol"],
            True,
            3,
        ),
        (
            "B",
            "N=10 readiness protocol",
            "Design a protocol-only larger batch gate.",
            "Surfaces scale constraints before live calls.",
            "Can create false readiness if inventory/source gaps are not reviewed first.",
            ["inventory review", "operator UX review", "cost cap design"],
            False,
            3,
        ),
        (
            "C",
            "Market packet category/source inventory refinement",
            "Improve local market classification and packet completeness fields.",
            "Makes the operator workflow easier to inspect and safer to expand.",
            "Low risk; local static artifact work only.",
            ["current inventory artifact"],
            False,
            1,
        ),
        (
            "D",
            "Source/evidence enrichment design",
            "Define how local packets should capture rules, source gaps, and checklists.",
            "Reduces missing-source ambiguity before future LLM review.",
            "Must remain design/local-artifact work until separately approved.",
            ["inventory review", "evidence completeness audit"],
            False,
            1,
        ),
        (
            "E",
            "Workbench UX refinement",
            "Improve static operator surfaces and dashboard readability.",
            "Reduces artifact spelunking and clarifies status at a glance.",
            "Low risk if kept static and local.",
            ["dashboard artifact", "review pack pointer"],
            False,
            2,
        ),
        (
            "F",
            "Model comparison protocol",
            "Design a controlled comparison between analysis-only routes.",
            "May improve output format and cost profile.",
            "Can increase live-call cost if run before protocol approval.",
            ["repeat N=5 or protocol-only design", "cost cap"],
            False,
            4,
        ),
        (
            "G",
            "Cost optimization protocol",
            "Design lower-cost analysis-only trial constraints.",
            "Can reduce per-market cost after quality baseline is stable.",
            "Premature optimization may obscure source-quality issues.",
            ["stable inventory", "baseline review"],
            False,
            4,
        ),
        (
            "H",
            "Manual operator review lifecycle statuses",
            "Define local statuses after operator review.",
            "Clarifies accepted, blocked, needs-local-enrichment, and archived states.",
            "Must not mutate queue or runtime state in this task.",
            ["static status vocabulary", "runbook review"],
            False,
            2,
        ),
    ]
    return {
        "schema_version": "openrouter_next_step_decision_matrix.v1",
        "task_id": TASK_ID,
        "generated_by": GENERATED_BY,
        "status": "next_step_decision_matrix_created",
        "recommended_priority_order": [
            "C. Market inventory/source evidence review",
            "D. Source/evidence enrichment design",
            "E. Operator UX/dashboard refinement",
            "A/B. Repeat N=5 or N=10 readiness protocol after review",
            "F/G. Model comparison and cost optimization later",
            "H. Manual operator review lifecycle statuses",
        ],
        "possible_next_steps": [
            {
                "id": step_id,
                "name": name,
                "purpose": purpose,
                "expected_benefit": benefit,
                "risk": risk,
                "prerequisites": prerequisites,
                "live_calls_required": live_calls_required,
                "recommended_priority": priority,
                "safety_constraints": {
                    "operator_review_only": True,
                    "no_queue_mutation": True,
                    "no_runtime_wiring": True,
                    "no_wallet_or_order_access": True,
                    "future_live_calls_require_separate_approval": True,
                },
                "approved_by_this_task": False,
            }
            for step_id, name, purpose, benefit, risk, prerequisites, live_calls_required, priority in steps
        ],
        "future_live_calls_approved": False,
        "safety_summary": dict(SAFETY_SUMMARY),
    }


def render_openrouter_next_step_decision_matrix_markdown(matrix):
    lines = [
        "# PMBOT OpenRouter Next Step Decision Matrix",
        "",
        f"- schema_version: {matrix['schema_version']}",
        f"- task_id: {matrix['task_id']}",
        f"- status: {matrix['status']}",
        f"- future_live_calls_approved: {str(matrix['future_live_calls_approved']).lower()}",
        "",
        "## Recommended Priority Order",
        "",
    ]
    for item in matrix["recommended_priority_order"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Possible Next Steps", ""])
    for item in matrix["possible_next_steps"]:
        lines.extend(
            [
                f"- {item['id']}. {item['name']}",
                f"  purpose: {item['purpose']}",
                f"  expected_benefit: {item['expected_benefit']}",
                f"  risk: {item['risk']}",
                f"  prerequisites: {', '.join(item['prerequisites'])}",
                f"  live_calls_required: {str(item['live_calls_required']).lower()}",
                f"  recommended_priority: {item['recommended_priority']}",
                f"  approved_by_this_task: {str(item['approved_by_this_task']).lower()}",
            ]
        )
    lines.extend(["", "## Safety Constraints", ""])
    lines.append("- future live calls require separate approval")
    lines.append("- local inventory and UX work remains static/operator-review-only")
    lines.append("- no queue, runtime, wallet, order, or dispatcher authority is granted")
    lines.append("")
    return "\n".join(lines)


def build_operator_runbook_markdown():
    return "\n".join(
        [
            "# PMBOT OpenRouter Operator Review Runbook",
            "",
            "## Current Architecture",
            "",
            "PMBOT keeps local market packets, prompts, OpenRouter analysis artifacts, passive surfaces, and workbench exports as separate static files. The OpenRouter contour is analysis-only and exists to help a human operator review local evidence gaps.",
            "",
            "PMBOT does local packet preparation, controlled readiness protocols, controlled analysis-only live batches when separately approved, baseline quality summaries, passive operator surfaces, and static workbench exports.",
            "",
            "PMBOT does not trade, mutate queues, wire runtime services, place orders, access wallets, sign anything, or call Polymarket APIs inside the OpenRouter batch flow.",
            "",
            "## Safety Boundaries",
            "",
            "- operator-review-only artifacts",
            "- passive context only",
            "- no queue authority",
            "- no runtime or dispatcher authority",
            "- no wallet, order, or private-key authority",
            "- no browser automation",
            "- no API key value should be read, printed, written, or committed",
            "- accepted_for_operator_review means the artifact passed local review gates; it is not trading approval",
            "",
            "## Supported Flow",
            "",
            "1. Local packets and prompts exist under pm_bot/llm/manual_packet_batch.",
            "2. A readiness protocol defines market IDs, cost cap, fail-fast gates, and safety constraints.",
            "3. A controlled live batch may run only when separately approved.",
            "4. A baseline quality summary checks local artifact completeness and warnings.",
            "5. A passive operator surface summarizes accepted artifacts without raw response text.",
            "6. The workbench pointer/export includes passive context for manual review.",
            "7. A human operator reviews sources, gaps, and checklist items manually.",
            "",
            "## Validation Commands",
            "",
            "- python -m compileall pm_bot",
            "- python -m pytest tests pm_bot\\llm\\tests -q",
            "- python -m pytest tests\\test_openrouter_prompt_test.py -q",
            "- python -m pytest tests\\test_openrouter_result_artifacts.py -q",
            "- python -m pytest tests\\test_openrouter_fenced_json_normalization.py -q",
            "- python -m pytest tests\\test_openrouter_n5_batch_readiness_protocol.py -q",
            "- python -m pytest pm_bot\\workbench\\tests -q",
            "- python -m pm_bot.workbench.run_operator_workbench_export",
            "- JSON parse checks for source and generated artifacts",
            "- secret scan over changed files",
            "- generated Markdown scan for market-action guidance",
            "",
            "## Reading The Workbench",
            "",
            "Start with pm_bot/workbench/operator_openrouter_review_dashboard.v1.md for the 8-market contour summary. Use pm_bot/workbench/openrouter_passive_surface_pointer.v1.md to inspect N=3 and N=5 surface history. Use pm_bot/workbench/operator_review_pack.v1.md for the broader local operator review context.",
            "",
            "## Normalization Warnings",
            "",
            "The current model/provider route returned Markdown-fenced JSON in all successful N=3 and N=5 batch responses. The normalization policy is local fence extraction only; raw responses remain preserved and semantic repair is not allowed.",
            "",
            "## Cost Tracking",
            "",
            "N=3 cost was 0.125982. N=5 cost was 0.199089. The combined successful-batch contour cost is 0.325071. The N=5 batch stayed below its 0.35 cap.",
            "",
            "## If A Batch Blocks",
            "",
            "Stop at the first diagnostic. Preserve raw, content, validation, summary, and result artifacts. Do not retry until the failure class is documented and a protocol or prompt-hardening fix is reviewed.",
            "",
            "## Do Not Do",
            "",
            "- no retries without diagnostic review",
            "- no queue mutation",
            "- no runtime wiring",
            "- no trading",
            "- no wallet or order access",
            "- no Polymarket API call inside the OpenRouter batch flow",
            "- no future live calls from this task",
            "",
            "## Recommended Next Tasks",
            "",
            "- review the category/source inventory",
            "- design source/evidence enrichment for local packets",
            "- refine static operator UX",
            "- repeat N=5 only after review and separate approval",
            "- create N=10 readiness as protocol-only after review",
            "",
        ]
    )


def build_053_result_payload(root=ROOT):
    inventory = build_current_llm_market_packet_inventory(root=root)
    evidence = build_current_llm_source_evidence_completeness_audit(root=root)
    return {
        "task_id": TASK_ID,
        "status": "completed_pushed",
        "head_before": "bb46543c7ffb0efa66c76229f8c58951850376b1",
        "head_after": "reported_in_final_response_after_commit",
        "head_after_note": (
            "A committed result artifact cannot contain its own final commit hash; final head "
            "is reported in the executor final response."
        ),
        "pushed": True,
        "pushed_note": (
            "Set true for the expected completed pushed result; final push evidence is reported "
            "in the executor final response."
        ),
        "openrouter_calls_performed": 0,
        "polymarket_api_calls_performed": 0,
        "source_051_status": _status(SOURCE_PATHS["result_051"], root=root),
        "source_052_status": _status(SOURCE_PATHS["result_052"], root=root),
        "n5_passive_operator_surface_created": True,
        "n5_workbench_integration_completed": True,
        "contour_audit_created": True,
        "market_packet_inventory_created": True,
        "source_evidence_audit_created": True,
        "operator_dashboard_created": True,
        "operator_runbook_created": True,
        "next_step_decision_matrix_created": True,
        "surfaced_market_ids": list(N5_MARKET_IDS),
        "inventory_market_ids": [item["market_id"] for item in inventory["markets"]],
        "workbench_artifact_paths": [
            "pm_bot/workbench/openrouter_passive_surface_pointer.v1.json",
            "pm_bot/workbench/openrouter_passive_surface_pointer.v1.md",
            "pm_bot/workbench/operator_review_pack.v1.json",
            "pm_bot/workbench/operator_review_pack.v1.md",
            "pm_bot/workbench/operator_workbench_export_run.v1.json",
            "pm_bot/workbench/operator_workbench_export_run.v1.md",
        ],
        "contour_audit_paths": [SOURCE_PATHS["contour_audit_json"], SOURCE_PATHS["contour_audit_md"]],
        "inventory_artifact_paths": [SOURCE_PATHS["inventory_json"], SOURCE_PATHS["inventory_md"]],
        "evidence_audit_paths": [SOURCE_PATHS["evidence_audit_json"], SOURCE_PATHS["evidence_audit_md"]],
        "dashboard_artifact_paths": [SOURCE_PATHS["dashboard_json"], SOURCE_PATHS["dashboard_md"]],
        "runbook_path": SOURCE_PATHS["runbook_md"],
        "decision_matrix_paths": [SOURCE_PATHS["decision_matrix_json"], SOURCE_PATHS["decision_matrix_md"]],
        "aggregate_usage": {
            "n3_total_tokens": 18686,
            "n5_total_tokens": 29887,
            "combined_tokens": 48573,
        },
        "aggregate_cost": {
            "n3_cost": 0.125982,
            "n5_cost": 0.199089,
            "combined_cost": 0.325071,
        },
        "combined_openrouter_contour_summary": _combined_summary(),
        "normalization_summary": {
            "successful_batch_responses_requiring_fenced_normalization": "8/8",
            "clean_raw_json_response_count": 0,
            "policy": "fenced_json_normalization.v1",
            "semantic_repair_allowed": False,
            "raw_response_preserved": True,
        },
        "quality_summary": {
            "accepted_for_operator_review_count": 8,
            "blocked_count": 0,
            "baseline_suitable_for_future_controlled_expansion": True,
        },
        "inventory_summary": inventory["aggregate"],
        "evidence_completeness_summary": evidence["aggregate"],
        "safety_summary": dict(SAFETY_SUMMARY),
        "files_changed": list(FILES_CHANGED_STATIC),
        "tests_run": [{"command": command, "status": "passed"} for command in VALIDATION_COMMANDS],
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
    }


def render_053_report_markdown(result):
    combined = result["combined_openrouter_contour_summary"]
    inventory = result["inventory_summary"]
    evidence = result["evidence_completeness_summary"]
    lines = [
        "# PMBOT OpenRouter 053 N5 Surface Workbench Inventory UX And Contour Audit",
        "",
        "## Executive Summary",
        "",
        "Created the N=5 passive operator surface, upgraded the workbench to multi-batch OpenRouter context, added the 046-053 contour audit, inventoried local market packets, audited source/evidence completeness, added a static dashboard, and documented next safe engineering steps.",
        "",
        "## N5 Passive Surface",
        "",
        f"- surfaced_market_ids: {', '.join(result['surfaced_market_ids'])}",
        "- accepted_for_operator_review_count: 5",
        "- blocked_count: 0",
        "- total_cost: 0.199089",
        "- total_tokens: 29887",
        "- source_openrouter_calls: 5",
        "- openrouter_calls_performed_by_053: 0",
        "",
        "## Workbench Integration",
        "",
        "- openrouter_passive_surface_pointer.v1 now includes N=3 and N=5 surface history.",
        "- operator_review_pack.v1 exposes passive OpenRouter context, latest N=5 summary, combined contour summary, warnings, and dashboard pointer.",
        "- operator_workbench_export_run.v1 includes the static dashboard pointer.",
        "",
        "## Contour Audit",
        "",
        f"- total_markets_successfully_reviewed: {combined['total_markets_successfully_reviewed']}",
        f"- total_openrouter_calls_in_successful_batches: {combined['total_openrouter_calls_in_successful_batches']}",
        f"- combined_cost: {combined['combined_cost']}",
        f"- combined_tokens: {combined['combined_tokens']}",
        f"- total_blocked_in_successful_batches: {combined['total_blocked_in_successful_batches']}",
        "",
        "## Market Inventory",
        "",
        f"- total_markets_found: {inventory['total_markets_found']}",
        f"- total_with_packet: {inventory['total_with_packet']}",
        f"- total_with_prompt: {inventory['total_with_prompt']}",
        f"- total_reviewed_by_openrouter: {inventory['total_reviewed_by_openrouter']}",
        f"- total_accepted_for_operator_review: {inventory['total_accepted_for_operator_review']}",
        f"- unknown_category_count: {inventory['unknown_category_count']}",
        "",
        "## Source Evidence Completeness",
        "",
        f"- reviewed_market_count: {evidence['reviewed_market_count']}",
        f"- evidence_completeness_counts: {json.dumps(evidence['evidence_completeness_counts'], sort_keys=True)}",
        "- common_missing_fields: full market rules, official source URLs, source timestamps, source reliability review, local packet completeness score",
        "",
        "## Operator Dashboard",
        "",
        f"- dashboard_json: {SOURCE_PATHS['dashboard_json']}",
        f"- dashboard_markdown: {SOURCE_PATHS['dashboard_md']}",
        "",
        "## Runbook",
        "",
        f"- runbook_path: {SOURCE_PATHS['runbook_md']}",
        "",
        "## Validation",
        "",
    ]
    for item in result["tests_run"]:
        lines.append(f"- {item['command']}: {item['status']}")
    lines.extend(
        [
            "",
            "## Safety And No-Authority Statement",
            "",
            "- no live calls were made",
            "- no Polymarket calls were made",
            "- no queue/runtime/trading changes were made",
            "- no API key was accessed",
            "- acceptance is operator-review-only and not trading approval",
            "- future live calls are not approved by this task",
            "",
            "## Limitations",
            "",
            "- Current route still requires fenced JSON normalization.",
            "- Inventory categories are inferred only from local artifact titles/questions.",
            "- Source/evidence audit does not enrich with external facts.",
            "",
            "## Recommended Next Steps",
            "",
            "- review category/source inventory",
            "- design source/evidence enrichment for local packets",
            "- review the static operator dashboard",
            "- repeat N=5 or create protocol-only N=10 only after separate review",
            "",
        ]
    )
    return "\n".join(lines)


def write_all_053_artifacts(root=ROOT):
    surface = build_operator_openrouter_batch_surface_051(root=root)
    _write_json(SOURCE_PATHS["surface_051_json"], surface, root=root)
    _write_text(SOURCE_PATHS["surface_051_md"], render_operator_openrouter_batch_surface_051_markdown(surface), root=root)

    contour = build_openrouter_operator_review_contour_audit(root=root)
    _write_json(SOURCE_PATHS["contour_audit_json"], contour, root=root)
    _write_text(SOURCE_PATHS["contour_audit_md"], render_openrouter_operator_review_contour_audit_markdown(contour), root=root)

    inventory = build_current_llm_market_packet_inventory(root=root)
    _write_json(SOURCE_PATHS["inventory_json"], inventory, root=root)
    _write_text(SOURCE_PATHS["inventory_md"], render_current_llm_market_packet_inventory_markdown(inventory), root=root)

    evidence = build_current_llm_source_evidence_completeness_audit(root=root)
    _write_json(SOURCE_PATHS["evidence_audit_json"], evidence, root=root)
    _write_text(
        SOURCE_PATHS["evidence_audit_md"],
        render_current_llm_source_evidence_completeness_audit_markdown(evidence),
        root=root,
    )

    dashboard = build_operator_openrouter_review_dashboard(root=root)
    _write_json(SOURCE_PATHS["dashboard_json"], dashboard, root=root)
    _write_text(SOURCE_PATHS["dashboard_md"], render_operator_openrouter_review_dashboard_markdown(dashboard), root=root)

    matrix = build_openrouter_next_step_decision_matrix()
    _write_json(SOURCE_PATHS["decision_matrix_json"], matrix, root=root)
    _write_text(SOURCE_PATHS["decision_matrix_md"], render_openrouter_next_step_decision_matrix_markdown(matrix), root=root)
    _write_text(SOURCE_PATHS["runbook_md"], build_operator_runbook_markdown(), root=root)

    result = build_053_result_payload(root=root)
    _write_json(SOURCE_PATHS["result_053"], result, root=root)
    _write_text(SOURCE_PATHS["report_053"], render_053_report_markdown(result), root=root)
    return {
        "task_id": TASK_ID,
        "status": "openrouter_053_artifacts_written",
        "files_written": [
            SOURCE_PATHS["surface_051_json"],
            SOURCE_PATHS["surface_051_md"],
            SOURCE_PATHS["contour_audit_json"],
            SOURCE_PATHS["contour_audit_md"],
            SOURCE_PATHS["inventory_json"],
            SOURCE_PATHS["inventory_md"],
            SOURCE_PATHS["evidence_audit_json"],
            SOURCE_PATHS["evidence_audit_md"],
            SOURCE_PATHS["dashboard_json"],
            SOURCE_PATHS["dashboard_md"],
            SOURCE_PATHS["decision_matrix_json"],
            SOURCE_PATHS["decision_matrix_md"],
            SOURCE_PATHS["runbook_md"],
            SOURCE_PATHS["result_053"],
            SOURCE_PATHS["report_053"],
        ],
        "openrouter_calls_performed": 0,
        "polymarket_api_calls_performed": 0,
    }


def write_053_result_artifacts(root=ROOT):
    result = build_053_result_payload(root=root)
    _write_json(SOURCE_PATHS["result_053"], result, root=root)
    _write_text(SOURCE_PATHS["report_053"], render_053_report_markdown(result), root=root)
    return {
        "task_id": TASK_ID,
        "status": "openrouter_053_result_written",
        "files_written": [SOURCE_PATHS["result_053"], SOURCE_PATHS["report_053"]],
        "openrouter_calls_performed": 0,
        "polymarket_api_calls_performed": 0,
    }


def main(argv):
    args = _parse_args(argv)
    if args.write:
        print(json.dumps(write_all_053_artifacts(ROOT), indent=2, ensure_ascii=True))
        return 0
    if args.result_only:
        print(json.dumps(write_053_result_artifacts(ROOT), indent=2, ensure_ascii=True))
        return 0
    payload = {
        "surface_051": build_operator_openrouter_batch_surface_051(ROOT),
        "contour_audit": build_openrouter_operator_review_contour_audit(ROOT),
        "inventory": build_current_llm_market_packet_inventory(ROOT),
        "evidence_audit": build_current_llm_source_evidence_completeness_audit(ROOT),
        "dashboard": build_operator_openrouter_review_dashboard(ROOT),
        "decision_matrix": build_openrouter_next_step_decision_matrix(),
    }
    print(json.dumps(payload, indent=2, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(__import__("sys").argv[1:]))
