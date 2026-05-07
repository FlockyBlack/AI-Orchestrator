import argparse
import json
import sys
from pathlib import Path


TASK_ID = "PMBOT-WORKBENCH-001-OPERATOR-REVIEW-PACK-EXPORT"
CODEX_LANE = "CODEX_A"
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pm_bot.llm import summarize_actual_manual_llm_response_trial as actual_llm_response_surface  # noqa: E402
from pm_bot.llm import export_manual_llm_review_queue as manual_llm_review_queue_surface  # noqa: E402
from pm_bot.workbench import operator_openrouter_review_dashboard  # noqa: E402
from pm_bot.workbench import openrouter_passive_surface_pointer  # noqa: E402

WORKBENCH_DIR = ROOT / "pm_bot" / "workbench"
DOCS_DIR = ROOT / "docs"

DEFAULT_PACK_JSON = WORKBENCH_DIR / "operator_review_pack.v1.json"
DEFAULT_PACK_MD = WORKBENCH_DIR / "operator_review_pack.v1.md"
DEFAULT_EXPECTED_PACK_JSON = WORKBENCH_DIR / "expected_operator_review_pack.v1.json"
DEFAULT_RESULT = DOCS_DIR / "PMBOT_WORKBENCH_001_RESULT.json"
DEFAULT_LANE_RESULT = DOCS_DIR / "PMBOT_CODEX_A_ROUND003_RESULT.json"
QUALITY_REPORT_PATH = "pm_bot/quality/artifact_health_report.v1.json"
PAPER_019_SERIES_ARTIFACT_PATH = "pm_bot/paper/multi_market_paper_run_series.v1.json"
PAPER_019_SECTION_ID = "paper_019_multi_market_run_series"
PAPER_020_RESULT_ARTIFACT_PATH = "docs/PMBOT_PAPER_020_RESULT.json"
PAPER_020_POSTMORTEM_ARTIFACT_PATH = "pm_bot/paper/paper_run_series_postmortem.v1.json"
PAPER_020_SECTION_ID = "paper_020_paper_run_series_postmortem"
MANUAL_LLM_REVIEW_ARTIFACT_PATH = "pm_bot/llm/manual_llm_paste_in_review.v1.json"
MANUAL_LLM_REVIEW_SECTION_ID = "manual_llm_review"
MANUAL_LLM_QUALITY_GATE_ARTIFACT_PATH = "pm_bot/llm/manual_llm_review_quality_gate.v1.json"
MANUAL_LLM_QUALITY_GATE_SECTION_ID = "manual_llm_review_quality_gate"
MANUAL_LLM_REVIEW_QUEUE_ARTIFACT_PATH = "pm_bot/llm/manual_llm_review_queue.v1.json"
MANUAL_LLM_REVIEW_QUEUE_SECTION_ID = "manual_llm_review_queue"
ACTUAL_MANUAL_LLM_RESPONSE_TRIAL_ARTIFACT_PATH = (
    "pm_bot/llm/actual_manual_llm_response_trial.v1.json"
)
ACTUAL_MANUAL_LLM_RESPONSE_TRIAL_SECTION_ID = "actual_manual_llm_response_trial"
OPENROUTER_PASSIVE_SURFACE_POINTER_ARTIFACT_PATH = (
    "pm_bot/workbench/openrouter_passive_surface_pointer.v1.json"
)
OPENROUTER_PASSIVE_SURFACE_POINTER_MARKDOWN_PATH = (
    "pm_bot/workbench/openrouter_passive_surface_pointer.v1.md"
)
OPENROUTER_PASSIVE_SURFACE_SECTION_ID = "openrouter_passive_surface"
OPENROUTER_REVIEW_DASHBOARD_ARTIFACT_PATH = (
    "pm_bot/workbench/operator_openrouter_review_dashboard.v1.json"
)
OPENROUTER_REVIEW_DASHBOARD_MARKDOWN_PATH = (
    "pm_bot/workbench/operator_openrouter_review_dashboard.v1.md"
)
OPENROUTER_REVIEW_DASHBOARD_SECTION_ID = "openrouter_review_dashboard"
PACKET_COMPLETENESS_GATE_ARTIFACT_PATH = (
    "pm_bot/llm/current_llm_batch_readiness_gate.v1.json"
)
PACKET_COMPLETENESS_GATE_MARKDOWN_PATH = (
    "pm_bot/llm/current_llm_batch_readiness_gate.v1.md"
)
PACKET_COMPLETENESS_GATE_SECTION_ID = "packet_completeness_readiness_gate"
RESOLUTION_SOURCE_AUDIT_ARTIFACT_PATH = (
    "pm_bot/llm/current_llm_resolution_source_normalization_audit.v1.json"
)
RESOLUTION_SOURCE_AUDIT_MARKDOWN_PATH = (
    "pm_bot/llm/current_llm_resolution_source_normalization_audit.v1.md"
)
RESOLUTION_SOURCE_AUDIT_SECTION_ID = "resolution_source_normalization_audit"
READINESS_AFTER_SOURCE_NORMALIZATION_ARTIFACT_PATH = (
    "pm_bot/llm/"
    "current_llm_packet_evidence_readiness_scores_after_source_normalization.v1.json"
)
READINESS_AFTER_SOURCE_NORMALIZATION_MARKDOWN_PATH = (
    "pm_bot/llm/"
    "current_llm_packet_evidence_readiness_scores_after_source_normalization.v1.md"
)
READINESS_AFTER_SOURCE_NORMALIZATION_SECTION_ID = "readiness_after_source_normalization"
BATCH_GATE_AFTER_SOURCE_NORMALIZATION_ARTIFACT_PATH = (
    "pm_bot/llm/current_llm_batch_readiness_gate_after_source_normalization.v1.json"
)
BATCH_GATE_AFTER_SOURCE_NORMALIZATION_MARKDOWN_PATH = (
    "pm_bot/llm/current_llm_batch_readiness_gate_after_source_normalization.v1.md"
)
BATCH_GATE_AFTER_SOURCE_NORMALIZATION_SECTION_ID = (
    "batch_readiness_gate_after_source_normalization"
)
LOCAL_SOURCE_ENRICHMENT_ACTION_PLAN_ARTIFACT_PATH = (
    "pm_bot/llm/local_source_enrichment_action_plan.v1.json"
)
LOCAL_SOURCE_ENRICHMENT_ACTION_PLAN_MARKDOWN_PATH = (
    "pm_bot/llm/local_source_enrichment_action_plan.v1.md"
)
LOCAL_SOURCE_ENRICHMENT_ACTION_PLAN_SECTION_ID = "local_source_enrichment_action_plan"
MANUAL_RESOLUTION_SOURCE_CAPTURE_SCHEMA_ARTIFACT_PATH = (
    "pm_bot/llm/manual_resolution_source_capture_schema.v1.json"
)
MANUAL_RESOLUTION_SOURCE_CAPTURE_SCHEMA_MARKDOWN_PATH = (
    "pm_bot/llm/manual_resolution_source_capture_schema.v1.md"
)
MANUAL_RESOLUTION_SOURCE_CAPTURE_MANIFEST_ARTIFACT_PATH = (
    "pm_bot/llm/manual_resolution_source_capture_manifest.v1.json"
)
MANUAL_RESOLUTION_SOURCE_CAPTURE_MANIFEST_MARKDOWN_PATH = (
    "pm_bot/llm/manual_resolution_source_capture_manifest.v1.md"
)
MANUAL_RESOLUTION_SOURCE_CAPTURE_VALIDATION_ARTIFACT_PATH = (
    "pm_bot/llm/manual_resolution_source_capture_validation.v1.json"
)
MANUAL_RESOLUTION_SOURCE_CAPTURE_VALIDATION_MARKDOWN_PATH = (
    "pm_bot/llm/manual_resolution_source_capture_validation.v1.md"
)
MANUAL_RESOLUTION_SOURCE_CAPTURE_OPERATOR_GUIDE_PATH = (
    "docs/PMBOT_SOURCE_004B_MANUAL_CAPTURE_OPERATOR_FILL_GUIDE.md"
)
MANUAL_RESOLUTION_SOURCE_CAPTURE_OPERATOR_CHECKLIST_ARTIFACT_PATH = (
    "pm_bot/llm/manual_resolution_source_capture_operator_checklist.v1.json"
)
MANUAL_RESOLUTION_SOURCE_CAPTURE_OPERATOR_CHECKLIST_MARKDOWN_PATH = (
    "pm_bot/llm/manual_resolution_source_capture_operator_checklist.v1.md"
)
MANUAL_RESOLUTION_SOURCE_CAPTURE_PROGRESS_ARTIFACT_PATH = (
    "pm_bot/llm/manual_resolution_source_capture_progress.v1.json"
)
MANUAL_RESOLUTION_SOURCE_CAPTURE_PROGRESS_MARKDOWN_PATH = (
    "pm_bot/llm/manual_resolution_source_capture_progress.v1.md"
)
MANUAL_RESOLUTION_SOURCE_CAPTURE_SECTION_ID = "manual_resolution_source_capture"

SCHEMA_VERSION = "operator_review_pack.v1"
GENERATED_BY = "pm_bot/workbench/export_operator_review_pack.py"
PRODUCT_DIRECTION = "operator_workbench_review_pack_v1"
BASE_COMMIT = "21edc9af372e9d1736afb0eccd3c016f23f2c144"

ACCOUNTING_ONLY_WARNING = (
    "Paper accounting PnL is fixture/manual accounting only and is not strategy profitability."
)
PAPER_019_INTERPRETATION_WARNING = (
    "PAPER-019 values are deterministic fixture/accounting-only outputs and are not strategy "
    "profitability, recommendation, EV, edge, probability, or market decision evidence."
)
PAPER_020_ACCOUNTING_ONLY_WARNING = (
    "PAPER-019 PnL is accounting-only fixture output, not strategy profitability; "
    "it is not a recommendation, edge, EV, probability estimate, market score, "
    "or market truth evidence."
)
NO_RECOMMENDATIONS_OR_DECISIONS_STATEMENT = (
    "This operator review pack does not recommend markets, sides, prices, sizes, orders, trades, "
    "paper orders, or decisions."
)
MANUAL_LLM_REVIEW_ANALYSIS_ONLY_WARNING = (
    "Manual LLM review is analysis-only and not trading advice; it does not authorize orders, "
    "paper orders, market decisions, side selection, probability estimates, EV, edge, or scoring."
)
MANUAL_LLM_QUALITY_GATE_WARNING = (
    "Manual LLM review quality gate is a deterministic offline quality gate only; it is not "
    "truth evaluation, probability, EV, edge, side, or trading advice."
)
MANUAL_LLM_REVIEW_QUEUE_WARNING = (
    "Manual LLM review queue is an offline local index only; it is not truth, "
    "not trading advice, and not execution authority."
)
ACTUAL_MANUAL_LLM_RESPONSE_TRIAL_WARNING = (
    "Actual manual LLM response trial surface is offline review context only; it is not truth, "
    "not trading advice, and not execution authority."
)
OPENROUTER_PASSIVE_SURFACE_WARNING = (
    "OpenRouter passive surface is read-only operator context; it creates no queue item, "
    "runtime hook, API call, wallet/order access, or authority."
)
MANUAL_LLM_QUALITY_GATE_VALIDATION_STATUSES = {
    "quality_passed",
    "quality_passed_with_warnings",
    "quality_failed",
}

SAFETY_FLAGS = {
    "operator_review_only": True,
    "passive_context_only": True,
    "analysis_only": True,
    "manual_review_only": True,
    "no_trading_authority": True,
    "no_queue_authority": True,
    "no_runtime_authority": True,
    "no_dispatcher_authority": True,
    "no_wallet_or_order_authority": True,
    "acceptance_is_not_trading_approval": True,
    "no_market_action_guidance": True,
    "offline_only": True,
    "deterministic_output": True,
    "local_file_reads_only": True,
    "runtime_wiring": False,
    "network_api": False,
    "credentials": False,
    "wallet": False,
    "trading": False,
    "real_orders": False,
    "live_trading": False,
    "autonomous_paper_orders": False,
    "recommendations": False,
    "truth_inference": False,
    "scoring_probability_ev_edge": False,
    "market_decisions": False,
    "command_execution": False,
    "dispatcher_run_codex_changes": False,
}

FORBIDDEN_CAPABILITIES = [
    "live fetchers, network/API calls, authenticated endpoints, or live data refresh",
    "credentials, API keys, wallet access, private keys, or signing",
    "trading endpoints, real orders, live trading, or autonomous paper orders",
    "betting recommendations, side recommendations, size recommendations, or market selection",
    "truth inference, probability estimates, EV calculations, edge calculations, or market scoring",
    "command execution, prompt automation, dispatcher changes, run_codex changes, or runtime wiring",
    "dashboard server, frontend runtime, Telegram runtime, token handling, webhooks, or polling",
]

QUALITY_SEVERITY_INTERPRETATION = {
    "blocking": "blocking means stop and repair before relying on the package.",
    "action_required": "action_required means review before relying on the package.",
    "review_needed": "review_needed means inspect but not necessarily block.",
    "informational": "informational means low-priority context.",
}
QUALITY_WARNING_OWNERS = ("code", "fixture", "schema", "data", "unknown")
QUALITY_WARNING_ACTION_TYPES = ("fix_required", "review_required", "ignore_allowed")

SOURCE_ARTIFACTS = (
    {
        "artifact_id": "product_001_result",
        "path": "docs/PMBOT_PRODUCT_001_RESULT.json",
        "category": "product_direction",
        "artifact_type": "docs_result_json",
        "required": True,
    },
    {
        "artifact_id": "integration_008_result",
        "path": "docs/PMBOT_INTEGRATION_008_RESULT.json",
        "category": "integration",
        "artifact_type": "docs_result_json",
        "required": True,
    },
    {
        "artifact_id": "paper_017_result",
        "path": "docs/PMBOT_PAPER_017_RESULT.json",
        "category": "paper_accounting",
        "artifact_type": "docs_result_json",
        "required": False,
    },
    {
        "artifact_id": "paper_018_result",
        "path": "docs/PMBOT_PAPER_018_RESULT.json",
        "category": "paper_accounting",
        "artifact_type": "docs_result_json",
        "required": True,
    },
    {
        "artifact_id": "paper_019_result",
        "path": "docs/PMBOT_PAPER_019_RESULT.json",
        "category": "paper_run_series",
        "artifact_type": "docs_result_json",
        "required": False,
    },
    {
        "artifact_id": PAPER_019_SECTION_ID,
        "path": PAPER_019_SERIES_ARTIFACT_PATH,
        "category": "paper_run_series",
        "artifact_type": "paper_run_series_json",
        "required": False,
    },
    {
        "artifact_id": "paper_020_result",
        "path": PAPER_020_RESULT_ARTIFACT_PATH,
        "category": "paper_run_series_postmortem",
        "artifact_type": "docs_result_json",
        "required": False,
    },
    {
        "artifact_id": PAPER_020_SECTION_ID,
        "path": PAPER_020_POSTMORTEM_ARTIFACT_PATH,
        "category": "paper_run_series_postmortem",
        "artifact_type": "paper_run_series_postmortem_json",
        "required": False,
    },
    {
        "artifact_id": "dashboard_002_result",
        "path": "docs/PMBOT_DASHBOARD_002_RESULT.json",
        "category": "dashboard_state",
        "artifact_type": "docs_result_json",
        "required": True,
    },
    {
        "artifact_id": "operator_002_result",
        "path": "docs/PMBOT_OPERATOR_002_RESULT.json",
        "category": "operator_inbox",
        "artifact_type": "docs_result_json",
        "required": True,
    },
    {
        "artifact_id": "infra_009_result",
        "path": "docs/PMBOT_INFRA_009_RESULT.json",
        "category": "infrastructure_optional",
        "artifact_type": "docs_result_json",
        "required": False,
    },
    {
        "artifact_id": "infra_009_report",
        "path": "docs/PMBOT_INFRA_009_ABC_ROUND003_WORKTREE_MATERIALIZATION.md",
        "category": "infrastructure_optional",
        "artifact_type": "docs_markdown",
        "required": False,
    },
    {
        "artifact_id": "paper_accounting_reconciliation_audit",
        "path": "pm_bot/paper/paper_accounting_reconciliation_audit.v1.json",
        "category": "paper_audit",
        "artifact_type": "paper_audit_json",
        "required": True,
    },
    {
        "artifact_id": "paper_accounting_batch_audit",
        "path": "pm_bot/paper/paper_accounting_batch_audit.v1.json",
        "category": "paper_audit",
        "artifact_type": "paper_audit_json",
        "required": True,
    },
    {
        "artifact_id": "paper_accounting_ledger",
        "path": "pm_bot/paper/paper_accounting_ledger.v1.json",
        "category": "portfolio_accounting",
        "artifact_type": "paper_accounting_json",
        "required": True,
    },
    {
        "artifact_id": "paper_accounting_pnl_preview",
        "path": "pm_bot/paper/paper_accounting_pnl_preview.v1.json",
        "category": "portfolio_accounting",
        "artifact_type": "paper_accounting_json",
        "required": True,
    },
    {
        "artifact_id": "paper_portfolio_snapshot",
        "path": "pm_bot/paper/paper_portfolio_snapshot.v1.json",
        "category": "portfolio_accounting",
        "artifact_type": "paper_portfolio_json",
        "required": True,
    },
    {
        "artifact_id": "paper_metrics_report",
        "path": "pm_bot/paper/paper_metrics_report.v1.json",
        "category": "portfolio_accounting",
        "artifact_type": "paper_metrics_json",
        "required": True,
    },
    {
        "artifact_id": "portfolio_audit_state_preview",
        "path": "pm_bot/dashboard/portfolio_audit_state_preview.v1.json",
        "category": "dashboard_state",
        "artifact_type": "dashboard_state_json",
        "required": True,
    },
    {
        "artifact_id": "manual_command_inbox_review",
        "path": "pm_bot/operator/manual_command_inbox_review.v1.json",
        "category": "operator_inbox",
        "artifact_type": "operator_inbox_json",
        "required": True,
    },
    {
        "artifact_id": MANUAL_LLM_REVIEW_SECTION_ID,
        "path": MANUAL_LLM_REVIEW_ARTIFACT_PATH,
        "category": "manual_llm_review",
        "artifact_type": "manual_llm_review_json",
        "required": False,
    },
    {
        "artifact_id": MANUAL_LLM_QUALITY_GATE_SECTION_ID,
        "path": MANUAL_LLM_QUALITY_GATE_ARTIFACT_PATH,
        "category": "manual_llm_review_quality_gate",
        "artifact_type": "manual_llm_review_quality_gate_json",
        "required": False,
    },
    {
        "artifact_id": MANUAL_LLM_REVIEW_QUEUE_SECTION_ID,
        "path": MANUAL_LLM_REVIEW_QUEUE_ARTIFACT_PATH,
        "category": "manual_llm_review_queue",
        "artifact_type": "manual_llm_review_queue_json",
        "required": False,
    },
    {
        "artifact_id": ACTUAL_MANUAL_LLM_RESPONSE_TRIAL_SECTION_ID,
        "path": ACTUAL_MANUAL_LLM_RESPONSE_TRIAL_ARTIFACT_PATH,
        "category": "manual_llm_actual_response_trial",
        "artifact_type": "actual_manual_llm_response_trial_json",
        "required": False,
    },
    {
        "artifact_id": OPENROUTER_PASSIVE_SURFACE_SECTION_ID,
        "path": OPENROUTER_PASSIVE_SURFACE_POINTER_ARTIFACT_PATH,
        "category": "openrouter_passive_surface",
        "artifact_type": "openrouter_passive_surface_pointer_json",
        "required": False,
    },
    {
        "artifact_id": OPENROUTER_REVIEW_DASHBOARD_SECTION_ID,
        "path": OPENROUTER_REVIEW_DASHBOARD_ARTIFACT_PATH,
        "category": "openrouter_review_dashboard",
        "artifact_type": "openrouter_review_dashboard_json",
        "required": False,
    },
    {
        "artifact_id": PACKET_COMPLETENESS_GATE_SECTION_ID,
        "path": PACKET_COMPLETENESS_GATE_ARTIFACT_PATH,
        "category": "packet_completeness_readiness",
        "artifact_type": "packet_completeness_readiness_gate_json",
        "required": False,
    },
    {
        "artifact_id": RESOLUTION_SOURCE_AUDIT_SECTION_ID,
        "path": RESOLUTION_SOURCE_AUDIT_ARTIFACT_PATH,
        "category": "resolution_source_normalization",
        "artifact_type": "resolution_source_normalization_audit_json",
        "required": False,
    },
    {
        "artifact_id": READINESS_AFTER_SOURCE_NORMALIZATION_SECTION_ID,
        "path": READINESS_AFTER_SOURCE_NORMALIZATION_ARTIFACT_PATH,
        "category": "resolution_source_normalization",
        "artifact_type": "readiness_after_source_normalization_json",
        "required": False,
    },
    {
        "artifact_id": BATCH_GATE_AFTER_SOURCE_NORMALIZATION_SECTION_ID,
        "path": BATCH_GATE_AFTER_SOURCE_NORMALIZATION_ARTIFACT_PATH,
        "category": "resolution_source_normalization",
        "artifact_type": "batch_gate_after_source_normalization_json",
        "required": False,
    },
    {
        "artifact_id": LOCAL_SOURCE_ENRICHMENT_ACTION_PLAN_SECTION_ID,
        "path": LOCAL_SOURCE_ENRICHMENT_ACTION_PLAN_ARTIFACT_PATH,
        "category": "resolution_source_normalization",
        "artifact_type": "local_source_enrichment_action_plan_json",
        "required": False,
    },
    {
        "artifact_id": "manual_resolution_source_capture_schema",
        "path": MANUAL_RESOLUTION_SOURCE_CAPTURE_SCHEMA_ARTIFACT_PATH,
        "category": MANUAL_RESOLUTION_SOURCE_CAPTURE_SECTION_ID,
        "artifact_type": "manual_resolution_source_capture_schema_json",
        "required": False,
    },
    {
        "artifact_id": MANUAL_RESOLUTION_SOURCE_CAPTURE_SECTION_ID,
        "path": MANUAL_RESOLUTION_SOURCE_CAPTURE_MANIFEST_ARTIFACT_PATH,
        "category": MANUAL_RESOLUTION_SOURCE_CAPTURE_SECTION_ID,
        "artifact_type": "manual_resolution_source_capture_manifest_json",
        "required": False,
    },
    {
        "artifact_id": "manual_resolution_source_capture_validation",
        "path": MANUAL_RESOLUTION_SOURCE_CAPTURE_VALIDATION_ARTIFACT_PATH,
        "category": MANUAL_RESOLUTION_SOURCE_CAPTURE_SECTION_ID,
        "artifact_type": "manual_resolution_source_capture_validation_json",
        "required": False,
    },
    {
        "artifact_id": "manual_resolution_source_capture_operator_checklist",
        "path": MANUAL_RESOLUTION_SOURCE_CAPTURE_OPERATOR_CHECKLIST_ARTIFACT_PATH,
        "category": MANUAL_RESOLUTION_SOURCE_CAPTURE_SECTION_ID,
        "artifact_type": "manual_resolution_source_capture_operator_checklist_json",
        "required": False,
    },
    {
        "artifact_id": "manual_resolution_source_capture_progress",
        "path": MANUAL_RESOLUTION_SOURCE_CAPTURE_PROGRESS_ARTIFACT_PATH,
        "category": MANUAL_RESOLUTION_SOURCE_CAPTURE_SECTION_ID,
        "artifact_type": "manual_resolution_source_capture_progress_json",
        "required": False,
    },
)


def _parse_args(argv):
    parser = argparse.ArgumentParser(description="Export deterministic local PMBOT operator review pack.")
    parser.add_argument("--write", action="store_true", help="Write JSON, Markdown, expected fixture, and result docs.")
    parser.add_argument("--markdown", action="store_true", help="Print Markdown instead of JSON.")
    return parser.parse_args(argv)


def _resolve_path(path, root=ROOT):
    value = Path(path)
    if value.is_absolute():
        return value
    return Path(root) / value


def _display_path(path, root=ROOT):
    resolved = Path(path).resolve()
    try:
        value = resolved.relative_to(Path(root).resolve())
    except ValueError:
        value = resolved
    return str(value).replace("\\", "/")


def _is_json_artifact(artifact):
    return artifact["artifact_type"].endswith("_json") or artifact["path"].endswith(".json")


def _load_json(path):
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _load_optional_json(path):
    value = Path(path)
    if not value.exists():
        return None, "missing"
    try:
        payload = _load_json(value)
    except (OSError, json.JSONDecodeError) as exc:
        return None, type(exc).__name__
    if not isinstance(payload, dict):
        return None, "top_level_not_object"
    return payload, "parsed"


def _write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def _write_text(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _safe_list(value):
    if isinstance(value, list):
        return value
    return []


def _safe_dict(value):
    if isinstance(value, dict):
        return value
    return {}


def _warning_count(payload):
    if not isinstance(payload, dict):
        return 0
    warnings = payload.get("warnings")
    if isinstance(warnings, list):
        return len(warnings)
    interpretation = payload.get("interpretation_warnings")
    if isinstance(interpretation, list):
        return len(interpretation)
    return 0


def _artifact_state(artifact, root=ROOT):
    path = _resolve_path(artifact["path"], root=root)
    present = path.exists()
    payload = None
    parse_status = "not_applicable"
    parse_error = None

    if present and _is_json_artifact(artifact):
        try:
            payload = _load_json(path)
            parse_status = "parsed"
        except (OSError, json.JSONDecodeError) as exc:
            parse_status = "parse_failed"
            parse_error = type(exc).__name__
    elif not present and _is_json_artifact(artifact):
        parse_status = "not_applicable"

    metadata = _safe_dict(payload)
    item = {
        "artifact_id": artifact["artifact_id"],
        "path": artifact["path"],
        "category": artifact["category"],
        "artifact_type": artifact["artifact_type"],
        "required": artifact["required"],
        "present": present,
        "parse_status": parse_status,
        "schema_version": metadata.get("schema_version"),
        "task_id": metadata.get("task_id"),
        "status": metadata.get("status"),
        "audit_status": metadata.get("audit_status"),
        "deterministic": metadata.get("deterministic"),
        "warning_count": _warning_count(payload),
    }
    if parse_error is not None:
        item["parse_error"] = parse_error
    return item, payload


def _artifact_inventory(root=ROOT):
    artifacts = []
    payloads = {}
    for artifact in SOURCE_ARTIFACTS:
        item, payload = _artifact_state(artifact, root=root)
        artifacts.append(item)
        payloads[artifact["artifact_id"]] = payload

    summary = {
        "total_artifacts": len(artifacts),
        "present_artifacts": sum(1 for item in artifacts if item["present"]),
        "missing_artifacts": sum(1 for item in artifacts if not item["present"]),
        "required_missing_artifacts": sum(1 for item in artifacts if item["required"] and not item["present"]),
        "json_artifacts_parsed": sum(1 for item in artifacts if item["parse_status"] == "parsed"),
        "json_artifacts_parse_failed": sum(1 for item in artifacts if item["parse_status"] == "parse_failed"),
    }
    return {"summary": summary, "artifacts": artifacts}, payloads


def _source_doc_status(path, payload):
    payload = _safe_dict(payload)
    return {
        "source_path": path,
        "present": bool(payload),
        "task_id": payload.get("task_id"),
        "status": payload.get("status") if payload else "missing",
        "integration_verdict": payload.get("integration_verdict"),
    }


def _product_stage_summary(payloads):
    product = _safe_dict(payloads.get("product_001_result"))
    return {
        "product_direction": product.get("recommended_direction") or PRODUCT_DIRECTION,
        "task_id": TASK_ID,
        "base_commit": BASE_COMMIT,
        "product_result": _source_doc_status("docs/PMBOT_PRODUCT_001_RESULT.json", payloads.get("product_001_result")),
        "integration_008_result": _source_doc_status(
            "docs/PMBOT_INTEGRATION_008_RESULT.json", payloads.get("integration_008_result")
        ),
        "paper_018_result": _source_doc_status("docs/PMBOT_PAPER_018_RESULT.json", payloads.get("paper_018_result")),
        "dashboard_002_result": _source_doc_status(
            "docs/PMBOT_DASHBOARD_002_RESULT.json", payloads.get("dashboard_002_result")
        ),
        "operator_002_result": _source_doc_status(
            "docs/PMBOT_OPERATOR_002_RESULT.json", payloads.get("operator_002_result")
        ),
        "stage_boundary": {
            "operator_review_pack_export_only": True,
            "offline_only": True,
            "deterministic_only": True,
            "runtime_wiring": False,
            "live_data": False,
            "recommendations_or_decisions": False,
        },
    }


def _checks_from(payload, field):
    checks = _safe_dict(payload).get(field)
    return [check for check in _safe_list(checks) if isinstance(check, dict)]


def _check_counts(checks):
    return {
        "checks_total": len(checks),
        "checks_passed": sum(1 for check in checks if check.get("status") == "pass"),
        "checks_warning": sum(1 for check in checks if check.get("status") == "warning"),
        "checks_failed": sum(1 for check in checks if check.get("status") == "fail"),
    }


def _audit_warning_count(payload):
    warnings = _safe_dict(payload).get("warnings")
    return len(warnings) if isinstance(warnings, list) else 0


def _paper_audit_entry(artifact_id, path, payload, checks, extra_counts=None):
    payload = _safe_dict(payload)
    mismatches = _safe_list(payload.get("mismatches"))
    counts = _check_counts(checks)
    if isinstance(extra_counts, dict):
        counts = {**counts, **extra_counts}
    return {
        "artifact_id": artifact_id,
        "source_path": path,
        "present": bool(payload),
        "schema_version": payload.get("schema_version"),
        "task_id": payload.get("task_id"),
        "audit_status": payload.get("audit_status"),
        "counts": counts,
        "warnings_count": _audit_warning_count(payload),
        "mismatches_count": len(mismatches),
        "paper_orders_created": payload.get("paper_orders_created", 0),
        "autonomous_actions_created": payload.get("autonomous_actions_created", 0),
        "next_safe_action": payload.get("next_safe_action"),
    }


def _paper_audit_summary(payloads):
    reconciliation = _safe_dict(payloads.get("paper_accounting_reconciliation_audit"))
    batch = _safe_dict(payloads.get("paper_accounting_batch_audit"))
    reconciliation_checks = _checks_from(reconciliation, "checks")
    batch_checks = (
        _checks_from(batch, "lifecycle_consistency_checks")
        + _checks_from(batch, "artifact_pointer_checks")
        + _checks_from(batch, "safety_checks")
    )

    reconciliation_entry = _paper_audit_entry(
        "paper_accounting_reconciliation_audit",
        "pm_bot/paper/paper_accounting_reconciliation_audit.v1.json",
        reconciliation,
        reconciliation_checks,
        {"artifacts_checked": len(_safe_list(reconciliation.get("artifacts_checked")))},
    )
    batch_entry = _paper_audit_entry(
        "paper_accounting_batch_audit",
        "pm_bot/paper/paper_accounting_batch_audit.v1.json",
        batch,
        batch_checks,
        {"records_audited": batch.get("records_audited", 0)},
    )

    passed_audits = []
    if reconciliation_entry["audit_status"] == "reconciliation_passed":
        passed_audits.append(
            {
                "artifact_id": "paper_accounting_reconciliation_audit",
                "audit_status": reconciliation_entry["audit_status"],
            }
        )
    if batch_entry["audit_status"] == "batch_audit_passed":
        passed_audits.append(
            {
                "artifact_id": "paper_accounting_batch_audit",
                "audit_status": batch_entry["audit_status"],
            }
        )

    return {
        "summary_scope": "paper_accounting_audits_only",
        "reconciliation_audit": reconciliation_entry,
        "batch_audit": batch_entry,
        "audits_passed": passed_audits,
        "audit_warnings_count": reconciliation_entry["warnings_count"] + batch_entry["warnings_count"],
        "audit_mismatches_count": reconciliation_entry["mismatches_count"] + batch_entry["mismatches_count"],
        "accounting_only_interpretation_warning": ACCOUNTING_ONLY_WARNING,
    }


def _portfolio_accounting_summary(payloads):
    dashboard = _safe_dict(payloads.get("portfolio_audit_state_preview"))
    accounting = _safe_dict(dashboard.get("portfolio_accounting_summary"))
    batch = _safe_dict(payloads.get("paper_accounting_batch_audit"))
    return {
        "source_path": "pm_bot/dashboard/portfolio_audit_state_preview.v1.json",
        "summary_status": accounting.get("summary_status"),
        "accepted_accounting_market_ids": _safe_list(accounting.get("accepted_accounting_market_ids")),
        "counts": _safe_dict(accounting.get("counts")),
        "paper_accounting_totals": _safe_dict(accounting.get("paper_accounting_totals")),
        "paper_accounting_metrics": _safe_dict(accounting.get("paper_accounting_metrics")),
        "batch_accounting_totals": _safe_dict(batch.get("accounting_totals")),
        "interpretation_boundary": {
            "paper_accounting_only": True,
            "operator_manual_fixture_source": True,
            "strategy_profitability": False,
            "live_resolution": False,
            "warning": ACCOUNTING_ONLY_WARNING,
        },
    }


def _dashboard_state_summary(payloads):
    dashboard = _safe_dict(payloads.get("portfolio_audit_state_preview"))
    product = _safe_dict(dashboard.get("product_stage_summary"))
    return {
        "source_path": "pm_bot/dashboard/portfolio_audit_state_preview.v1.json",
        "present": bool(dashboard),
        "schema_version": dashboard.get("schema_version"),
        "dashboard_state_export_version": dashboard.get("dashboard_state_export_version"),
        "known_market_ids": _safe_list(dashboard.get("known_market_ids")),
        "current_known_portfolio_audit_status": product.get("current_known_portfolio_audit_status"),
        "interpretation_warning_count": len(_safe_list(dashboard.get("interpretation_warnings"))),
        "implementation_boundary": {
            "dashboard_runtime": False,
            "server": False,
            "frontend": False,
            "browser_automation": False,
            "network_api": False,
            "runtime_wiring": False,
        },
    }


def _operator_inbox_summary(payloads):
    inbox = _safe_dict(payloads.get("manual_command_inbox_review"))
    accepted = _safe_list(inbox.get("accepted_records"))
    rejected = _safe_list(inbox.get("rejected_records"))
    needs_review = _safe_list(inbox.get("needs_human_review_records"))
    return {
        "source_path": "pm_bot/operator/manual_command_inbox_review.v1.json",
        "present": bool(inbox),
        "schema_version": inbox.get("schema_version"),
        "records_seen": inbox.get("records_seen", 0),
        "accepted_count": inbox.get("accepted_count", 0),
        "rejected_count": inbox.get("rejected_count", 0),
        "needs_human_review_count": inbox.get("needs_human_review_count", 0),
        "accepted_command_ids": [record.get("command_id") for record in accepted if isinstance(record, dict)],
        "rejected_command_ids": [record.get("command_id") for record in rejected if isinstance(record, dict)],
        "needs_human_review_command_ids": [
            record.get("command_id") for record in needs_review if isinstance(record, dict)
        ],
        "execution_authority": inbox.get("execution_authority", False),
        "commands_executed": inbox.get("commands_executed", 0),
        "orders_created": inbox.get("orders_created", 0),
        "network_calls": inbox.get("network_calls", 0),
        "next_safe_action": inbox.get("next_safe_action"),
    }


def _manual_llm_review_forbidden_content_summary(review):
    forbidden = _safe_dict(review.get("forbidden_content_detected"))
    return {
        "detected": bool(forbidden.get("detected", False)),
        "findings_count": len(_safe_list(forbidden.get("findings"))),
    }


def _manual_llm_review_base(artifact):
    return {
        "section_id": MANUAL_LLM_REVIEW_SECTION_ID,
        "artifact_pointer": MANUAL_LLM_REVIEW_ARTIFACT_PATH,
        "artifact_parse_status": artifact.get("parse_status"),
        "errors_count": 0,
        "warnings_count": 0,
        "accepted_sections": [],
        "missing_sections": [],
        "forbidden_content_detected": {
            "detected": False,
            "findings_count": 0,
        },
        "next_safe_operator_action": "not_available",
        "analysis_only_warning": MANUAL_LLM_REVIEW_ANALYSIS_ONLY_WARNING,
        "safe_error_summary": [],
        "surface_only": True,
        "llm_text_generated": False,
        "llm_api_calls_added": False,
        "browser_automation_added": False,
        "runtime_integration_added": False,
    }


def _manual_llm_review_summary(payloads, inventory):
    artifact = _inventory_item(inventory, MANUAL_LLM_REVIEW_SECTION_ID)
    base = _manual_llm_review_base(artifact)

    if not artifact.get("present"):
        return {
            **base,
            "artifact_status": "missing",
            "validation_status": "not_available",
            "safe_error_summary": ["Manual LLM paste-in review artifact is not available locally."],
        }

    raw_review = payloads.get(MANUAL_LLM_REVIEW_SECTION_ID)
    review = _safe_dict(raw_review)
    if artifact.get("parse_status") != "parsed":
        parse_error = artifact.get("parse_error", artifact.get("parse_status") or "unreadable")
        return {
            **base,
            "artifact_status": "invalid",
            "validation_status": "rejected_or_unreadable",
            "safe_error_summary": [
                f"Manual LLM paste-in review artifact could not be read safely: {parse_error}."
            ],
        }

    if not isinstance(raw_review, dict) or not review:
        return {
            **base,
            "artifact_status": "invalid",
            "validation_status": "rejected_or_unreadable",
            "safe_error_summary": [
                "Manual LLM paste-in review artifact parsed but is not a non-empty JSON object."
            ],
        }

    validation_status = review.get("validation_status")
    if validation_status not in {"accepted", "rejected"}:
        return {
            **base,
            "artifact_status": "invalid",
            "validation_status": "rejected_or_unreadable",
            "safe_error_summary": [
                "Manual LLM paste-in review artifact parsed but does not expose accepted/rejected validation_status."
            ],
        }

    next_action = review.get("next_safe_operator_action")
    if not isinstance(next_action, str) or not next_action:
        next_action = "Review the manual LLM artifact status and local source artifacts manually."

    return {
        **base,
        "artifact_status": "present",
        "validation_status": validation_status,
        "errors_count": len(_safe_list(review.get("errors"))),
        "warnings_count": len(_safe_list(review.get("warnings"))),
        "accepted_sections": list(_safe_list(review.get("accepted_sections"))),
        "missing_sections": list(_safe_list(review.get("missing_sections"))),
        "forbidden_content_detected": _manual_llm_review_forbidden_content_summary(review),
        "next_safe_operator_action": next_action,
    }


def _quality_gate_count_summary(payload):
    counts = _safe_dict(payload.get("quality_counts"))
    errors = _safe_list(payload.get("errors"))
    warnings = _safe_list(payload.get("warnings"))
    return {
        "checks_total": _safe_int(counts.get("checks_total")),
        "checks_passed": _safe_int(counts.get("checks_passed")),
        "checks_with_warnings": _safe_int(counts.get("checks_with_warnings")),
        "checks_failed": _safe_int(counts.get("checks_failed")),
        "errors_count": _safe_int(counts.get("errors_count")) if "errors_count" in counts else len(errors),
        "warnings_count": _safe_int(counts.get("warnings_count")) if "warnings_count" in counts else len(warnings),
    }


def _quality_gate_required_sections_summary(payload):
    check = _safe_dict(payload.get("required_sections_check"))
    return {
        "status": check.get("status", "not_available"),
        "required_sections_count": len(_safe_list(check.get("required_sections"))),
        "present_sections_count": len(_safe_list(check.get("present_sections"))),
        "missing_sections_count": len(_safe_list(check.get("missing_sections"))),
        "empty_sections_count": len(_safe_list(check.get("empty_sections"))),
        "errors_count": len(_safe_list(check.get("errors"))),
        "warnings_count": len(_safe_list(check.get("warnings"))),
    }


def _quality_gate_minimum_content_summary(payload):
    check = _safe_dict(payload.get("minimum_content_check"))
    return {
        "status": check.get("status", "not_available"),
        "required_minimum_useful_items": dict(_safe_dict(check.get("required_minimum_useful_items"))),
        "observed_useful_items": dict(_safe_dict(check.get("observed_useful_items"))),
        "errors_count": len(_safe_list(check.get("errors"))),
        "warnings_count": len(_safe_list(check.get("warnings"))),
    }


def _quality_gate_generic_or_placeholder_summary(payload):
    check = _safe_dict(payload.get("generic_or_placeholder_text_check"))
    return {
        "status": check.get("status", "not_available"),
        "placeholder_findings_count": len(_safe_list(check.get("placeholder_findings"))),
        "repeated_cannot_determine_paths_count": len(
            _safe_list(check.get("repeated_cannot_determine_paths"))
        ),
        "errors_count": len(_safe_list(check.get("errors"))),
        "warnings_count": len(_safe_list(check.get("warnings"))),
    }


def _quality_gate_unsafe_certainty_summary(payload):
    check = _safe_dict(payload.get("unsafe_certainty_check"))
    return {
        "status": check.get("status", "not_available"),
        "unsafe_certainty_detected": bool(check.get("unsafe_certainty_detected", False)),
        "findings_count": len(_safe_list(check.get("findings"))),
        "errors_count": len(_safe_list(check.get("errors"))),
        "warnings_count": len(_safe_list(check.get("warnings"))),
    }


def _quality_gate_forbidden_content_summary(payload):
    check = _safe_dict(payload.get("forbidden_content_check"))
    return {
        "status": check.get("status", "not_available"),
        "forbidden_content_detected": bool(check.get("forbidden_content_detected", False)),
        "findings_count": len(_safe_list(check.get("findings"))),
        "errors_count": len(_safe_list(check.get("errors"))),
        "warnings_count": len(_safe_list(check.get("warnings"))),
    }


def _manual_llm_quality_gate_base(artifact):
    empty_payload = {}
    return {
        "section_id": MANUAL_LLM_QUALITY_GATE_SECTION_ID,
        "artifact_pointer": MANUAL_LLM_QUALITY_GATE_ARTIFACT_PATH,
        "artifact_parse_status": artifact.get("parse_status"),
        "validation_status": "not_available",
        "base_validator_status": "not_available",
        "quality_counts": _quality_gate_count_summary(empty_payload),
        "required_sections_check": _quality_gate_required_sections_summary(empty_payload),
        "minimum_content_check": _quality_gate_minimum_content_summary(empty_payload),
        "generic_or_placeholder_text_check": _quality_gate_generic_or_placeholder_summary(empty_payload),
        "unsafe_certainty_check": _quality_gate_unsafe_certainty_summary(empty_payload),
        "forbidden_content_check": _quality_gate_forbidden_content_summary(empty_payload),
        "next_safe_operator_action": "not_available",
        "deterministic_quality_gate_warning": MANUAL_LLM_QUALITY_GATE_WARNING,
        "safe_error_summary": [],
        "surface_only": True,
        "llm_text_generated": False,
        "llm_api_calls_added": False,
        "browser_automation_added": False,
        "runtime_integration_added": False,
    }


def _manual_llm_quality_gate_missing_check_names(payload):
    required_checks = (
        "required_sections_check",
        "minimum_content_check",
        "generic_or_placeholder_text_check",
        "unsafe_certainty_check",
        "forbidden_content_check",
    )
    return [name for name in required_checks if not isinstance(payload.get(name), dict)]


def _manual_llm_quality_gate_summary(payloads, inventory):
    artifact = _inventory_item(inventory, MANUAL_LLM_QUALITY_GATE_SECTION_ID)
    base = _manual_llm_quality_gate_base(artifact)

    if not artifact.get("present"):
        return {
            **base,
            "artifact_status": "missing",
            "validation_status": "not_available",
            "safe_error_summary": ["Manual LLM review quality gate artifact is not available locally."],
        }

    raw_gate = payloads.get(MANUAL_LLM_QUALITY_GATE_SECTION_ID)
    gate = _safe_dict(raw_gate)
    if artifact.get("parse_status") != "parsed":
        parse_error = artifact.get("parse_error", artifact.get("parse_status") or "unreadable")
        return {
            **base,
            "artifact_status": "invalid",
            "validation_status": "rejected_or_unreadable",
            "safe_error_summary": [
                f"Manual LLM review quality gate artifact could not be read safely: {parse_error}."
            ],
        }

    if not isinstance(raw_gate, dict) or not gate:
        return {
            **base,
            "artifact_status": "invalid",
            "validation_status": "rejected_or_unreadable",
            "safe_error_summary": [
                "Manual LLM review quality gate artifact parsed but is not a non-empty JSON object."
            ],
        }

    validation_status = gate.get("validation_status")
    base_validator_status = gate.get("base_validator_status")
    missing_checks = _manual_llm_quality_gate_missing_check_names(gate)
    if (
        validation_status not in MANUAL_LLM_QUALITY_GATE_VALIDATION_STATUSES
        or not isinstance(base_validator_status, str)
        or missing_checks
    ):
        error_summary = [
            "Manual LLM review quality gate artifact parsed but does not match the expected compact surface contract."
        ]
        if missing_checks:
            error_summary.append(f"Missing quality gate check summaries: {', '.join(missing_checks)}.")
        return {
            **base,
            "artifact_status": "invalid",
            "validation_status": "rejected_or_unreadable",
            "safe_error_summary": error_summary,
        }

    next_action = gate.get("next_safe_operator_action")
    if not isinstance(next_action, str) or not next_action:
        next_action = "Review the quality gate artifact status and local source artifacts manually."

    return {
        **base,
        "artifact_status": "present",
        "validation_status": validation_status,
        "base_validator_status": base_validator_status,
        "quality_counts": _quality_gate_count_summary(gate),
        "required_sections_check": _quality_gate_required_sections_summary(gate),
        "minimum_content_check": _quality_gate_minimum_content_summary(gate),
        "generic_or_placeholder_text_check": _quality_gate_generic_or_placeholder_summary(gate),
        "unsafe_certainty_check": _quality_gate_unsafe_certainty_summary(gate),
        "forbidden_content_check": _quality_gate_forbidden_content_summary(gate),
        "next_safe_operator_action": next_action,
    }


def _actual_manual_llm_response_trial_summary(root=ROOT):
    summary = actual_llm_response_surface.summarize_actual_manual_llm_response_trial(root=root)
    return {
        **summary,
        "section_id": ACTUAL_MANUAL_LLM_RESPONSE_TRIAL_SECTION_ID,
        "artifact_pointer": ACTUAL_MANUAL_LLM_RESPONSE_TRIAL_ARTIFACT_PATH,
        "offline_review_warning": ACTUAL_MANUAL_LLM_RESPONSE_TRIAL_WARNING,
    }


def _manual_llm_review_queue_summary(root=ROOT):
    summary = manual_llm_review_queue_surface.summarize_manual_llm_review_queue(root=root)
    return {
        **summary,
        "section_id": MANUAL_LLM_REVIEW_QUEUE_SECTION_ID,
        "artifact_pointer": MANUAL_LLM_REVIEW_QUEUE_ARTIFACT_PATH,
        "offline_review_warning": MANUAL_LLM_REVIEW_QUEUE_WARNING,
    }


def _inventory_item(inventory, artifact_id):
    for item in inventory["artifacts"]:
        if item["artifact_id"] == artifact_id:
            return item
    return {}


def _openrouter_passive_surface_base(artifact):
    return {
        "section_id": OPENROUTER_PASSIVE_SURFACE_SECTION_ID,
        "artifact_status": "missing" if not artifact.get("present") else "invalid",
        "artifact_pointer": OPENROUTER_PASSIVE_SURFACE_POINTER_ARTIFACT_PATH,
        "artifact_markdown_pointer": OPENROUTER_PASSIVE_SURFACE_POINTER_MARKDOWN_PATH,
        "artifact_parse_status": artifact.get("parse_status", "not_available"),
        "latest_surface_source_batch_task": "PMBOT-OPENROUTER-051-CONTROLLED-N5-BATCH-LIVE-CALL",
        "latest_surface_task": "PMBOT-OPENROUTER-053-PASSIVE-OPERATOR-SURFACE-AND-WORKBENCH-N5-INTEGRATION",
        "source_batch_task": "PMBOT-OPENROUTER-051-CONTROLLED-N5-BATCH-LIVE-CALL",
        "source_baseline_task": "PMBOT-OPENROUTER-052-N5-BATCH-BASELINE-QUALITY-AND-OPERATOR-SUMMARY",
        "source_surface_task": "PMBOT-OPENROUTER-053-PASSIVE-OPERATOR-SURFACE-AND-WORKBENCH-N5-INTEGRATION",
        "source_048_status": "not_available",
        "source_052_status": "not_available",
        "surfaced_market_ids": [],
        "model": "not_available",
        "total_calls": 0,
        "aggregate_usage": {},
        "aggregate_cost": {},
        "normalization_summary": {},
        "quality_summary": {},
        "surface_history": [],
        "n3_summary": {},
        "n5_summary": {},
        "latest_n5_summary": {},
        "combined_openrouter_review_contour_summary": {},
        "combined_aggregate_usage": {},
        "combined_aggregate_cost": {},
        "required_flag_status": {},
        "safety_summary": {
            **openrouter_passive_surface_pointer.SAFETY_TRUE_FLAGS,
            **openrouter_passive_surface_pointer.SAFETY_FALSE_FLAGS,
            "openrouter_calls_performed": 0,
            "polymarket_api_calls_performed": 0,
            "network_calls": 0,
            "orders_created": 0,
        },
        "artifact_pointers": {},
        "source_artifact_pointers": {},
        "warnings_count": 0,
        "known_warnings": [],
        "dashboard_pointer": OPENROUTER_REVIEW_DASHBOARD_ARTIFACT_PATH,
        "dashboard_markdown_pointer": OPENROUTER_REVIEW_DASHBOARD_MARKDOWN_PATH,
        "offline_review_warning": OPENROUTER_PASSIVE_SURFACE_WARNING,
        "openrouter_calls_performed": 0,
        "polymarket_api_calls_performed": 0,
        "network_calls": 0,
        "orders_created": 0,
        "queue_items_created": 0,
    }


def _openrouter_passive_surface_summary(payloads, inventory):
    artifact = _inventory_item(inventory, OPENROUTER_PASSIVE_SURFACE_SECTION_ID)
    base = _openrouter_passive_surface_base(artifact)
    pointer = payloads.get(OPENROUTER_PASSIVE_SURFACE_SECTION_ID)
    if not isinstance(pointer, dict):
        return base

    required_flag_status = _safe_dict(pointer.get("required_flag_status"))
    flags_passed = bool(required_flag_status) and all(required_flag_status.values())
    artifact_status = (
        "present"
        if artifact.get("parse_status") == "parsed"
        and pointer.get("status") == "passive_surface_pointer_ready"
        and flags_passed
        else "invalid"
    )

    return {
        **base,
        "artifact_status": artifact_status,
        "latest_surface_source_batch_task": pointer.get("latest_surface_source_batch_task")
        or base["latest_surface_source_batch_task"],
        "latest_surface_task": pointer.get("latest_surface_task") or base["latest_surface_task"],
        "source_batch_task": pointer.get("source_batch_task") or base["source_batch_task"],
        "source_baseline_task": pointer.get("source_baseline_task") or base["source_baseline_task"],
        "source_surface_task": pointer.get("source_surface_task") or base["source_surface_task"],
        "source_048_status": pointer.get("source_048_status") or base["source_048_status"],
        "source_052_status": pointer.get("source_052_status") or base["source_052_status"],
        "surfaced_market_ids": _safe_list(pointer.get("surfaced_market_ids")),
        "model": pointer.get("model") or base["model"],
        "total_calls": pointer.get("total_calls", 0),
        "aggregate_usage": _safe_dict(pointer.get("aggregate_usage")),
        "aggregate_cost": _safe_dict(pointer.get("aggregate_cost")),
        "normalization_summary": _safe_dict(pointer.get("normalization_summary")),
        "quality_summary": _safe_dict(pointer.get("quality_summary")),
        "surface_history": _safe_list(pointer.get("surface_history")),
        "n3_summary": _safe_dict(pointer.get("n3_summary")),
        "n5_summary": _safe_dict(pointer.get("n5_summary")),
        "latest_n5_summary": _safe_dict(pointer.get("latest_n5_summary")),
        "combined_openrouter_review_contour_summary": _safe_dict(
            pointer.get("combined_openrouter_review_contour_summary")
        ),
        "combined_aggregate_usage": _safe_dict(pointer.get("combined_aggregate_usage")),
        "combined_aggregate_cost": _safe_dict(pointer.get("combined_aggregate_cost")),
        "required_flag_status": required_flag_status,
        "safety_summary": _safe_dict(pointer.get("safety_summary")),
        "artifact_pointers": _safe_dict(pointer.get("artifact_pointers")),
        "source_artifact_pointers": _safe_dict(pointer.get("source_artifact_pointers")),
        "warnings_count": len(_safe_list(pointer.get("warnings"))),
        "known_warnings": _safe_list(pointer.get("warnings")),
    }


def _safe_int(value):
    if isinstance(value, bool):
        return 0
    if isinstance(value, int):
        return value
    return 0


def _paper_019_record_summary(record):
    item = {
        "record_id": record.get("record_id"),
        "market_id": record.get("market_id"),
        "processing_status": record.get("processing_status"),
        "lifecycle_state": record.get("lifecycle_state"),
        "accounting_included": record.get("accounting_included", False),
        "paper_orders_created": _safe_int(record.get("paper_orders_created")),
        "real_orders_created": _safe_int(record.get("real_orders_created")),
        "network_calls": _safe_int(record.get("network_calls")),
        "commands_executed": _safe_int(record.get("commands_executed")),
        "autonomous_decisions": _safe_int(record.get("autonomous_decisions")),
    }
    blocked_reason_codes = _safe_list(record.get("blocked_reason_codes"))
    if blocked_reason_codes:
        item["blocked_reason_codes"] = blocked_reason_codes
    return item


def _paper_019_blocked_or_manual_review_summary(series):
    records_by_status = _safe_dict(series.get("records_by_status"))
    lifecycle = _safe_dict(series.get("lifecycle_summary"))
    selected_records = []
    for record in _safe_list(series.get("record_summaries")):
        if not isinstance(record, dict):
            continue
        if record.get("processing_status") in {"blocked_fixture_record", "manual_review_only"}:
            selected_records.append(_paper_019_record_summary(record))
    return {
        "blocked_fixture_record_count": _safe_int(records_by_status.get("blocked_fixture_record")),
        "manual_review_only_count": _safe_int(records_by_status.get("manual_review_only")),
        "blocked_or_rejected_records": _safe_int(lifecycle.get("blocked_or_rejected_records")),
        "manual_review_only_records": _safe_int(lifecycle.get("manual_review_only_records")),
        "records": selected_records,
    }


def _paper_019_safety_counters(series):
    return {
        "real_orders_created": _safe_int(series.get("real_orders_created")),
        "autonomous_paper_orders": 0,
        "network_calls": _safe_int(series.get("network_calls")),
        "commands_executed": _safe_int(series.get("commands_executed")),
        "autonomous_decisions": _safe_int(series.get("autonomous_decisions")),
    }


def _paper_019_multi_market_run_series_summary(payloads, inventory):
    artifact = _inventory_item(inventory, PAPER_019_SECTION_ID)
    series = _safe_dict(payloads.get(PAPER_019_SECTION_ID))
    artifact_status = "present" if artifact.get("present") else "missing"
    return {
        "section_id": PAPER_019_SECTION_ID,
        "artifact_status": artifact_status,
        "artifact_pointer": PAPER_019_SERIES_ARTIFACT_PATH,
        "artifact_parse_status": artifact.get("parse_status"),
        "series_status": series.get("series_status"),
        "markets_seen": _safe_int(series.get("markets_seen")),
        "records_seen": _safe_int(series.get("records_seen")),
        "records_processed": _safe_int(series.get("records_processed")),
        "records_by_status": _safe_dict(series.get("records_by_status")),
        "accounting_summary": _safe_dict(series.get("accounting_summary")),
        "blocked_or_manual_review_summary": _paper_019_blocked_or_manual_review_summary(series),
        "interpretation_warning": PAPER_019_INTERPRETATION_WARNING,
        "safety_counters": _paper_019_safety_counters(series),
    }


def _paper_020_status_note_summary(postmortem):
    notes = []
    for item in _safe_list(postmortem.get("record_status_notes")):
        if isinstance(item, dict):
            notes.append(
                {
                    "processing_status": item.get("processing_status"),
                    "count": _safe_int(item.get("count")),
                    "operator_meaning": item.get("operator_meaning"),
                }
            )
    return notes


def _paper_020_safety_counters(postmortem):
    counters = _safe_dict(postmortem.get("safety_counters"))
    return {
        "real_orders_created": _safe_int(counters.get("real_orders_created")),
        "autonomous_paper_orders": _safe_int(counters.get("autonomous_paper_orders")),
        "network_calls": _safe_int(counters.get("network_calls")),
        "commands_executed": _safe_int(counters.get("commands_executed")),
        "autonomous_decisions": _safe_int(counters.get("autonomous_decisions")),
    }


def _paper_020_postmortem_summary(payloads, inventory):
    artifact = _inventory_item(inventory, PAPER_020_SECTION_ID)
    postmortem = _safe_dict(payloads.get(PAPER_020_SECTION_ID))
    paper_019 = _safe_dict(postmortem.get("paper_019_summary"))
    accounting = _safe_dict(postmortem.get("accounting_interpretation"))
    warning = accounting.get("warning") or PAPER_020_ACCOUNTING_ONLY_WARNING
    artifact_status = "present" if artifact.get("present") else "missing"
    return {
        "section_id": PAPER_020_SECTION_ID,
        "artifact_status": artifact_status,
        "artifact_pointer": PAPER_020_POSTMORTEM_ARTIFACT_PATH,
        "artifact_parse_status": artifact.get("parse_status"),
        "postmortem_status": postmortem.get("postmortem_status"),
        "source_paper_019_found": paper_019.get("source_schema_version") == "multi_market_paper_run_series.v1",
        "source_paper_019": {
            "source_artifact": paper_019.get("source_artifact"),
            "series_status": paper_019.get("series_status"),
            "markets_seen": _safe_int(paper_019.get("markets_seen")),
            "records_seen": _safe_int(paper_019.get("records_seen")),
            "records_processed": _safe_int(paper_019.get("records_processed")),
        },
        "records_by_status": _safe_dict(postmortem.get("records_by_status")),
        "record_status_notes": _paper_020_status_note_summary(postmortem),
        "cumulative_pnl": accounting.get("cumulative_pnl", "0.00"),
        "accounting_only_warning": warning,
        "accounting_only_warning_present": warning == PAPER_020_ACCOUNTING_ONLY_WARNING,
        "fixture_limitations": _safe_list(postmortem.get("fixture_limitations")),
        "recommended_next_fixture_expansions": _safe_list(
            postmortem.get("recommended_next_fixture_expansions")
        ),
        "safety_counters": _paper_020_safety_counters(postmortem),
        "next_safe_action": postmortem.get("next_safe_action"),
    }


def _quality_report_payload(root=ROOT):
    return _load_optional_json(_resolve_path(QUALITY_REPORT_PATH, root=root))


def _quality_warning_summary(quality_report, load_status):
    summary = _safe_dict(_safe_dict(quality_report).get("warning_severity_summary"))
    if summary:
        warnings_by_owner = _safe_dict(summary.get("warnings_by_owner"))
        warnings_by_action_type = _safe_dict(summary.get("warnings_by_action_type"))
        return {
            "source_path": QUALITY_REPORT_PATH,
            "quality_report_status": _safe_dict(quality_report).get("report_status"),
            "quality_report_load_status": load_status,
            "total_warnings": summary.get("total_warnings", 0),
            "blocking_warnings": summary.get("blocking_count", 0),
            "action_required_warnings": summary.get("action_required_count", 0),
            "review_needed_warnings": summary.get("review_needed_count", 0),
            "informational_warnings": summary.get("informational_count", 0),
            "blocking_warning_detected": summary.get("blocking_warning_detected", False),
            "warnings_by_owner": {owner: warnings_by_owner.get(owner, 0) for owner in QUALITY_WARNING_OWNERS},
            "warnings_by_action_type": {
                action_type: warnings_by_action_type.get(action_type, 0)
                for action_type in QUALITY_WARNING_ACTION_TYPES
            },
            "warning_categories": _safe_list(summary.get("warning_categories")),
            "top_warning_categories": _safe_list(summary.get("top_warning_categories")),
            "top_action_items": _safe_list(summary.get("top_action_items")),
            "severity_interpretation": dict(QUALITY_SEVERITY_INTERPRETATION),
            "operator_summary": summary.get("operator_summary"),
            "recommended_manual_action": summary.get("recommended_manual_action"),
        }

    warning_count = _warning_count(quality_report)
    return {
        "source_path": QUALITY_REPORT_PATH,
        "quality_report_status": "quality_report_unavailable" if load_status != "parsed" else "summary_missing",
        "quality_report_load_status": load_status,
        "total_warnings": warning_count,
        "blocking_warnings": 0,
        "action_required_warnings": warning_count,
        "review_needed_warnings": 0,
        "informational_warnings": 0,
        "blocking_warning_detected": False,
        "warnings_by_owner": {owner: 0 for owner in QUALITY_WARNING_OWNERS},
        "warnings_by_action_type": {action_type: 0 for action_type in QUALITY_WARNING_ACTION_TYPES},
        "warning_categories": [],
        "top_warning_categories": [],
        "top_action_items": [],
        "severity_interpretation": dict(QUALITY_SEVERITY_INTERPRETATION),
        "operator_summary": "Quality warning severity summary is unavailable; inspect quality report details manually.",
        "recommended_manual_action": "Regenerate the artifact health report before relying on the operator review pack.",
    }


def _source_warning_items(artifact_id, path, payload):
    warnings = _safe_dict(payload).get("warnings")
    items = []
    for index, warning in enumerate(_safe_list(warnings)):
        if isinstance(warning, dict):
            message = (
                warning.get("summary")
                or warning.get("message")
                or warning.get("warning_id")
                or json.dumps(warning, sort_keys=True, ensure_ascii=True)
            )
        else:
            message = str(warning)
        items.append(
            {
                "warning_id": f"{artifact_id}_warning_{index + 1}",
                "source_path": path,
                "category": "source_artifact_warning",
                "message": message,
            }
        )
    return items


def _warnings(payloads):
    items = [
        {
            "warning_id": "accounting_only_interpretation",
            "source_path": None,
            "category": "interpretation_boundary",
            "message": ACCOUNTING_ONLY_WARNING,
        },
        {
            "warning_id": "audit_status_not_truth_inference",
            "source_path": None,
            "category": "interpretation_boundary",
            "message": "Audit pass/fail state reflects deterministic local artifact consistency only, not truth inference.",
        },
        {
            "warning_id": "no_recommendations_or_decisions",
            "source_path": None,
            "category": "operator_boundary",
            "message": NO_RECOMMENDATIONS_OR_DECISIONS_STATEMENT,
        },
        {
            "warning_id": "local_artifacts_only",
            "source_path": None,
            "category": "data_boundary",
            "message": "This pack reads local artifacts only and contains no live prices, live fetch results, or API results.",
        },
    ]
    items.extend(
        _source_warning_items(
            "paper_accounting_reconciliation_audit",
            "pm_bot/paper/paper_accounting_reconciliation_audit.v1.json",
            payloads.get("paper_accounting_reconciliation_audit"),
        )
    )
    items.extend(
        _source_warning_items(
            "paper_accounting_batch_audit",
            "pm_bot/paper/paper_accounting_batch_audit.v1.json",
            payloads.get("paper_accounting_batch_audit"),
        )
    )
    return items


def _paper_019_warnings(paper_019_summary):
    if paper_019_summary["artifact_status"] != "missing":
        return []
    return [
        {
            "warning_id": "paper_019_multi_market_run_series_missing",
            "source_path": PAPER_019_SERIES_ARTIFACT_PATH,
            "category": "optional_artifact_missing",
            "message": "PAPER-019 multi-market paper run series artifact is missing; review pack generation continued.",
        }
    ]


def _paper_020_warnings(paper_020_summary):
    if paper_020_summary["artifact_status"] != "missing":
        return []
    return [
        {
            "warning_id": "paper_020_paper_run_series_postmortem_missing",
            "source_path": PAPER_020_POSTMORTEM_ARTIFACT_PATH,
            "category": "optional_artifact_missing",
            "message": "PAPER-020 paper run series postmortem artifact is missing; review pack generation continued.",
        }
    ]


def _actual_manual_llm_response_trial_warnings(summary):
    artifact_status = summary.get("artifact_status")
    run_status = summary.get("run_status")
    if artifact_status == "missing":
        return [
            {
                "warning_id": "actual_manual_llm_response_trial_missing",
                "source_path": ACTUAL_MANUAL_LLM_RESPONSE_TRIAL_ARTIFACT_PATH,
                "category": "optional_artifact_missing",
                "message": (
                    "Actual manual LLM response trial artifact is missing; review pack generation continued."
                ),
            }
        ]
    if artifact_status == "invalid":
        return [
            {
                "warning_id": "actual_manual_llm_response_trial_invalid",
                "source_path": ACTUAL_MANUAL_LLM_RESPONSE_TRIAL_ARTIFACT_PATH,
                "category": "optional_artifact_invalid",
                "message": (
                    "Actual manual LLM response trial artifact is present but invalid or unreadable; "
                    "review pack generation continued."
                ),
            }
        ]
    if run_status in {"actual_response_rejected", "actual_response_blocked"}:
        return [
            {
                "warning_id": "actual_manual_llm_response_trial_not_accepted",
                "source_path": ACTUAL_MANUAL_LLM_RESPONSE_TRIAL_ARTIFACT_PATH,
                "category": "optional_artifact_status",
                "message": (
                    "Actual manual LLM response trial artifact is present but not accepted; "
                    "surface it as offline review context only."
                ),
            }
        ]
    return []


def _manual_llm_review_queue_warnings(summary):
    artifact_status = summary.get("artifact_status")
    errors_count = _safe_int(summary.get("errors_count"))
    if artifact_status == "missing":
        return [
            {
                "warning_id": "manual_llm_review_queue_missing",
                "source_path": MANUAL_LLM_REVIEW_QUEUE_ARTIFACT_PATH,
                "category": "optional_artifact_missing",
                "message": "Manual LLM review queue artifact is missing; review pack generation continued.",
            }
        ]
    if artifact_status == "invalid":
        return [
            {
                "warning_id": "manual_llm_review_queue_invalid",
                "source_path": MANUAL_LLM_REVIEW_QUEUE_ARTIFACT_PATH,
                "category": "optional_artifact_invalid",
                "message": (
                    "Manual LLM review queue artifact is present but invalid or unreadable; "
                    "review pack generation continued."
                ),
            }
        ]
    if errors_count:
        return [
            {
                "warning_id": "manual_llm_review_queue_has_errors",
                "source_path": MANUAL_LLM_REVIEW_QUEUE_ARTIFACT_PATH,
                "category": "optional_artifact_status",
                "message": "Manual LLM review queue reports local errors; inspect the queue artifact.",
            }
        ]
    return []


def _openrouter_passive_surface_warnings(summary):
    artifact_status = summary.get("artifact_status")
    if artifact_status == "missing":
        return [
            {
                "warning_id": "openrouter_passive_surface_pointer_missing",
                "source_path": OPENROUTER_PASSIVE_SURFACE_POINTER_ARTIFACT_PATH,
                "category": "optional_artifact_missing",
                "message": "OpenRouter passive surface pointer is missing; review pack generation continued.",
            }
        ]
    if artifact_status == "invalid":
        return [
            {
                "warning_id": "openrouter_passive_surface_pointer_invalid",
                "source_path": OPENROUTER_PASSIVE_SURFACE_POINTER_ARTIFACT_PATH,
                "category": "optional_artifact_invalid",
                "message": (
                    "OpenRouter passive surface pointer is present but invalid or incomplete; "
                    "review pack generation continued."
                ),
            }
        ]
    return []


def _openrouter_review_dashboard_summary(payloads, inventory):
    artifact = _inventory_item(inventory, OPENROUTER_REVIEW_DASHBOARD_SECTION_ID)
    dashboard = _safe_dict(payloads.get(OPENROUTER_REVIEW_DASHBOARD_SECTION_ID))
    artifact_status = (
        "present"
        if artifact.get("parse_status") == "parsed"
        and dashboard.get("status") == "operator_openrouter_review_dashboard_created"
        else ("missing" if not artifact.get("present") else "invalid")
    )
    return {
        "section_id": OPENROUTER_REVIEW_DASHBOARD_SECTION_ID,
        "artifact_status": artifact_status,
        "artifact_pointer": OPENROUTER_REVIEW_DASHBOARD_ARTIFACT_PATH,
        "artifact_markdown_pointer": OPENROUTER_REVIEW_DASHBOARD_MARKDOWN_PATH,
        "artifact_parse_status": artifact.get("parse_status", "not_available"),
        "latest_batch": _safe_dict(dashboard.get("latest_batch")),
        "latest_surface": dashboard.get("latest_surface"),
        "latest_baseline": dashboard.get("latest_baseline"),
        "latest_workbench_integration_status": dashboard.get("latest_workbench_integration_status"),
        "n3_summary": _safe_dict(dashboard.get("n3_summary")),
        "n5_summary": _safe_dict(dashboard.get("n5_summary")),
        "combined_openrouter_review_contour_summary": _safe_dict(
            dashboard.get("combined_openrouter_review_contour_summary")
        ),
        "cost_summary": _safe_dict(dashboard.get("cost_summary")),
        "usage_summary": _safe_dict(dashboard.get("usage_summary")),
        "normalization_summary": _safe_dict(dashboard.get("normalization_summary")),
        "inventory_summary": _safe_dict(dashboard.get("inventory_summary")),
        "evidence_completeness_summary": _safe_dict(dashboard.get("evidence_completeness_summary")),
        "evidence_readiness_integration_status": dashboard.get(
            "evidence_readiness_integration_status"
        ),
        "evidence_readiness_score_summary": _safe_dict(
            dashboard.get("evidence_readiness_score_summary")
        ),
        "category_gap_summary": _safe_dict(dashboard.get("category_gap_summary")),
        "markets_reviewed_vs_unreviewed": _safe_dict(
            dashboard.get("markets_reviewed_vs_unreviewed")
        ),
        "markets_with_medium_evidence_completeness": _safe_list(
            dashboard.get("markets_with_medium_evidence_completeness")
        ),
        "recommended_next_local_enrichment_focus": _safe_list(
            dashboard.get("recommended_next_local_enrichment_focus")
        ),
        "top_missing_fields": _safe_list(dashboard.get("top_missing_fields")),
        "no_market_action_guidance": dashboard.get("no_market_action_guidance", True),
        "operator_next_engineering_actions": _safe_list(
            dashboard.get("operator_next_engineering_actions")
        ),
        "artifact_pointers": _safe_dict(dashboard.get("artifact_pointers")),
        "safety_summary": _safe_dict(dashboard.get("safety_summary")),
        "openrouter_calls_performed": dashboard.get("openrouter_calls_performed", 0),
        "polymarket_api_calls_performed": dashboard.get("polymarket_api_calls_performed", 0),
        "network_calls_performed": dashboard.get("network_calls_performed", 0),
    }


def _packet_completeness_gate_summary(payloads, inventory):
    artifact = _inventory_item(inventory, PACKET_COMPLETENESS_GATE_SECTION_ID)
    gate = _safe_dict(payloads.get(PACKET_COMPLETENESS_GATE_SECTION_ID))
    artifact_status = (
        "present"
        if artifact.get("parse_status") == "parsed"
        and gate.get("status") == "batch_readiness_gate_created"
        else ("missing" if not artifact.get("present") else "invalid")
    )
    return {
        "section_id": PACKET_COMPLETENESS_GATE_SECTION_ID,
        "artifact_status": artifact_status,
        "artifact_pointer": PACKET_COMPLETENESS_GATE_ARTIFACT_PATH,
        "artifact_markdown_pointer": PACKET_COMPLETENESS_GATE_MARKDOWN_PATH,
        "artifact_parse_status": artifact.get("parse_status", "not_available"),
        "gate_version": gate.get("gate_version"),
        "status": gate.get("status"),
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
        "openrouter_calls_performed": gate.get("openrouter_calls_performed", 0),
        "polymarket_api_calls_performed": gate.get("polymarket_api_calls_performed", 0),
        "network_calls_performed": gate.get("network_calls_performed", 0),
        "no_market_action_guidance": _safe_dict(gate.get("safety_flags")).get(
            "no_market_action_guidance", True
        ),
    }


def _resolution_source_normalization_summary(payloads, inventory):
    audit_item = _inventory_item(inventory, RESOLUTION_SOURCE_AUDIT_SECTION_ID)
    scores_item = _inventory_item(inventory, READINESS_AFTER_SOURCE_NORMALIZATION_SECTION_ID)
    gate_item = _inventory_item(inventory, BATCH_GATE_AFTER_SOURCE_NORMALIZATION_SECTION_ID)
    plan_item = _inventory_item(inventory, LOCAL_SOURCE_ENRICHMENT_ACTION_PLAN_SECTION_ID)
    audit = _safe_dict(payloads.get(RESOLUTION_SOURCE_AUDIT_SECTION_ID))
    scores = _safe_dict(payloads.get(READINESS_AFTER_SOURCE_NORMALIZATION_SECTION_ID))
    gate = _safe_dict(payloads.get(BATCH_GATE_AFTER_SOURCE_NORMALIZATION_SECTION_ID))
    plan = _safe_dict(payloads.get(LOCAL_SOURCE_ENRICHMENT_ACTION_PLAN_SECTION_ID))

    def _status(item, payload, expected_status):
        if item.get("parse_status") == "parsed" and payload.get("status") == expected_status:
            return "present"
        return "missing" if not item.get("present") else "invalid"

    audit_aggregate = _safe_dict(audit.get("aggregate"))
    score_aggregate = _safe_dict(scores.get("aggregate"))
    plan_aggregate = _safe_dict(plan.get("aggregate"))
    return {
        "section_id": "resolution_source_normalization",
        "audit_artifact_status": _status(
            audit_item, audit, "resolution_source_normalization_audit_created"
        ),
        "audit_artifact_pointer": RESOLUTION_SOURCE_AUDIT_ARTIFACT_PATH,
        "audit_artifact_markdown_pointer": RESOLUTION_SOURCE_AUDIT_MARKDOWN_PATH,
        "audit_artifact_parse_status": audit_item.get("parse_status", "not_available"),
        "readiness_artifact_status": _status(
            scores_item,
            scores,
            "after_source_normalization_readiness_scores_created",
        ),
        "readiness_artifact_pointer": READINESS_AFTER_SOURCE_NORMALIZATION_ARTIFACT_PATH,
        "readiness_artifact_markdown_pointer": (
            READINESS_AFTER_SOURCE_NORMALIZATION_MARKDOWN_PATH
        ),
        "batch_gate_artifact_status": _status(
            gate_item, gate, "batch_readiness_gate_after_source_normalization_created"
        ),
        "batch_gate_artifact_pointer": BATCH_GATE_AFTER_SOURCE_NORMALIZATION_ARTIFACT_PATH,
        "batch_gate_artifact_markdown_pointer": (
            BATCH_GATE_AFTER_SOURCE_NORMALIZATION_MARKDOWN_PATH
        ),
        "action_plan_artifact_status": _status(
            plan_item, plan, "local_source_enrichment_action_plan_created"
        ),
        "action_plan_artifact_pointer": LOCAL_SOURCE_ENRICHMENT_ACTION_PLAN_ARTIFACT_PATH,
        "action_plan_artifact_markdown_pointer": (
            LOCAL_SOURCE_ENRICHMENT_ACTION_PLAN_MARKDOWN_PATH
        ),
        "total_markets_audited": audit_aggregate.get("total_markets_audited", 0),
        "markets_missing_resolution_criteria_text": audit_aggregate.get(
            "markets_missing_resolution_criteria_text", 0
        ),
        "markets_missing_full_resolution_rules": audit_aggregate.get(
            "markets_missing_full_resolution_rules", 0
        ),
        "markets_missing_official_source_references": audit_aggregate.get(
            "markets_missing_official_source_references", 0
        ),
        "markets_needing_manual_resolution_source_review": audit_aggregate.get(
            "markets_needing_manual_resolution_source_review", 0
        ),
        "top_resolution_source_gaps": _safe_list(
            audit_aggregate.get("top_resolution_source_gaps")
        )[:10],
        "markets_missing_full_resolution_criteria_ids": _safe_list(
            audit_aggregate.get("markets_missing_full_resolution_criteria_ids")
        ),
        "markets_missing_full_resolution_rules_ids": _safe_list(
            audit_aggregate.get("markets_missing_full_resolution_rules_ids")
        ),
        "markets_missing_official_source_references_ids": _safe_list(
            audit_aggregate.get("markets_missing_official_source_references_ids")
        ),
        "markets_needing_manual_resolution_source_review_ids": _safe_list(
            audit_aggregate.get("markets_needing_manual_resolution_source_review_ids")
        ),
        "previous_readiness_summary": {
            "high_count": score_aggregate.get("previous_high_count", 0),
            "medium_count": score_aggregate.get("previous_medium_count", 0),
            "low_count": score_aggregate.get("previous_low_count", 0),
            "blocked_count": score_aggregate.get("previous_blocked_count", 0),
            "average_score": score_aggregate.get("previous_average_score", 0),
        },
        "updated_readiness_summary": {
            "high_count": score_aggregate.get("updated_high_count", 0),
            "medium_count": score_aggregate.get("updated_medium_count", 0),
            "low_count": score_aggregate.get("updated_low_count", 0),
            "blocked_count": score_aggregate.get("updated_blocked_count", 0),
            "average_score": score_aggregate.get("updated_average_score", 0),
            "score_delta_average": score_aggregate.get("score_delta_average", 0),
        },
        "markets_improved_by_source_normalization": _safe_list(
            score_aggregate.get("markets_with_source_fields_improved")
        ),
        "remaining_top_missing_fields": _safe_list(
            score_aggregate.get("remaining_top_missing_fields")
        )[:10],
        "batch_gate_total_markets": gate.get("total_markets", 0),
        "batch_gate_low_count": gate.get("low_count", 0),
        "batch_gate_medium_count": gate.get("medium_count", 0),
        "batch_gate_eligible_for_future_openrouter_batch_count": gate.get(
            "eligible_for_future_openrouter_batch_count", 0
        ),
        "markets_still_missing_resolution_sources": _safe_list(
            gate.get("markets_still_missing_resolution_sources")
        ),
        "manual_review_needed_markets": _safe_list(gate.get("manual_review_needed_markets")),
        "future_openrouter_batch_approved": gate.get(
            "future_openrouter_batch_approved", False
        ),
        "fields_to_fix_first": _safe_list(plan_aggregate.get("fields_to_fix_first")),
        "high_priority_local_actions": plan_aggregate.get("high_priority_local_actions", 0),
        "medium_priority_local_actions": plan_aggregate.get("medium_priority_local_actions", 0),
        "low_priority_local_actions": plan_aggregate.get("low_priority_local_actions", 0),
        "passive_only": plan.get("plan_type") == "passive_local_proposal_not_runtime_queue",
        "queue_items_created": 0,
        "queue_state_mutated": plan.get("queue_mutation_performed", False),
        "no_market_action_guidance": True,
    }


def _manual_resolution_source_capture_summary(payloads, inventory):
    schema_item = _inventory_item(inventory, "manual_resolution_source_capture_schema")
    manifest_item = _inventory_item(inventory, MANUAL_RESOLUTION_SOURCE_CAPTURE_SECTION_ID)
    validation_item = _inventory_item(
        inventory, "manual_resolution_source_capture_validation"
    )
    checklist_item = _inventory_item(
        inventory, "manual_resolution_source_capture_operator_checklist"
    )
    progress_item = _inventory_item(
        inventory, "manual_resolution_source_capture_progress"
    )
    manifest = _safe_dict(payloads.get(MANUAL_RESOLUTION_SOURCE_CAPTURE_SECTION_ID))
    validation = _safe_dict(payloads.get("manual_resolution_source_capture_validation"))
    checklist = _safe_dict(
        payloads.get("manual_resolution_source_capture_operator_checklist")
    )
    progress = _safe_dict(payloads.get("manual_resolution_source_capture_progress"))
    status_counts = _safe_dict(manifest.get("capture_status_counts"))
    return {
        "section_id": MANUAL_RESOLUTION_SOURCE_CAPTURE_SECTION_ID,
        "guide_pointer": MANUAL_RESOLUTION_SOURCE_CAPTURE_OPERATOR_GUIDE_PATH,
        "checklist_pointer": (
            MANUAL_RESOLUTION_SOURCE_CAPTURE_OPERATOR_CHECKLIST_ARTIFACT_PATH
        ),
        "checklist_markdown_pointer": (
            MANUAL_RESOLUTION_SOURCE_CAPTURE_OPERATOR_CHECKLIST_MARKDOWN_PATH
        ),
        "progress_pointer": MANUAL_RESOLUTION_SOURCE_CAPTURE_PROGRESS_ARTIFACT_PATH,
        "progress_markdown_pointer": (
            MANUAL_RESOLUTION_SOURCE_CAPTURE_PROGRESS_MARKDOWN_PATH
        ),
        "target_capture_directory": "pm_bot/llm/manual_resolution_source_capture",
        "schema_artifact_status": (
            "present"
            if schema_item.get("parse_status") == "parsed"
            else ("missing" if not schema_item.get("present") else "invalid")
        ),
        "schema_pointer": MANUAL_RESOLUTION_SOURCE_CAPTURE_SCHEMA_ARTIFACT_PATH,
        "schema_markdown_pointer": MANUAL_RESOLUTION_SOURCE_CAPTURE_SCHEMA_MARKDOWN_PATH,
        "manifest_artifact_status": (
            "present"
            if manifest_item.get("parse_status") == "parsed"
            and manifest.get("status")
            == "manual_resolution_source_capture_manifest_created"
            else ("missing" if not manifest_item.get("present") else "invalid")
        ),
        "manifest_pointer": MANUAL_RESOLUTION_SOURCE_CAPTURE_MANIFEST_ARTIFACT_PATH,
        "manifest_markdown_pointer": (
            MANUAL_RESOLUTION_SOURCE_CAPTURE_MANIFEST_MARKDOWN_PATH
        ),
        "manifest_parse_status": manifest_item.get("parse_status", "not_available"),
        "validation_artifact_status": (
            "present"
            if validation_item.get("parse_status") == "parsed"
            and validation.get("status")
            == "manual_resolution_source_capture_validation_passed"
            else ("missing" if not validation_item.get("present") else "invalid")
        ),
        "validation_pointer": MANUAL_RESOLUTION_SOURCE_CAPTURE_VALIDATION_ARTIFACT_PATH,
        "validation_markdown_pointer": (
            MANUAL_RESOLUTION_SOURCE_CAPTURE_VALIDATION_MARKDOWN_PATH
        ),
        "validation_parse_status": validation_item.get("parse_status", "not_available"),
        "checklist_artifact_status": (
            "present"
            if checklist_item.get("parse_status") == "parsed"
            else ("missing" if not checklist_item.get("present") else "invalid")
        ),
        "checklist_parse_status": checklist_item.get("parse_status", "not_available"),
        "progress_artifact_status": (
            "present"
            if progress_item.get("parse_status") == "parsed"
            else ("missing" if not progress_item.get("present") else "invalid")
        ),
        "progress_parse_status": progress_item.get("parse_status", "not_available"),
        "total_capture_packets": manifest.get("total_capture_packets", 0),
        "total_templates": checklist.get(
            "total_templates", manifest.get("total_capture_packets", 0)
        ),
        "capture_status_counts": status_counts,
        "current_status_counts": status_counts,
        "packets_created": manifest.get("total_capture_packets", 0),
        "packets_not_started": status_counts.get("not_started", 0),
        "packets_ready_for_local_review": status_counts.get("ready_for_local_review", 0),
        "fields_missing_across_all_packets": _safe_list(
            manifest.get("fields_missing_across_all_packets")
        ),
        "fields_required_for_high_completeness": _safe_list(
            manifest.get("fields_required_for_high_completeness")
        ),
        "recommended_operator_fill_order": _safe_list(
            manifest.get("recommended_operator_fill_order")
        ),
        "validation_command": checklist.get(
            "validation_command",
            "python -m pm_bot.llm.manual_resolution_source_capture_validator --write",
        ),
        "next_operator_action": progress.get(
            "recommended_operator_next_action",
            "Fill one not_started template from manual local review, set both status fields to draft, then rerun validation.",
        ),
        "markets_by_category": _safe_dict(manifest.get("markets_by_category")),
        "reviewed_vs_unreviewed": _safe_dict(manifest.get("reviewed_vs_unreviewed")),
        "readiness_band_counts": _safe_dict(manifest.get("readiness_band_counts")),
        "validation_valid_count": validation.get("valid_count", 0),
        "validation_invalid_count": validation.get("invalid_count", 0),
        "packets_with_market_action_guidance": _safe_list(
            validation.get("packets_with_market_action_guidance")
        ),
        "safety_summary": _safe_dict(manifest.get("safety_summary")),
        "no_market_action_guidance": manifest.get("no_market_action_guidance", True),
        "operator_review_only": manifest.get("operator_review_only", True),
        "no_trading_authority": manifest.get("no_trading_authority", True),
        "no_queue_authority": manifest.get("no_queue_authority", True),
        "no_runtime_authority": manifest.get("no_runtime_authority", True),
        "no_wallet_or_order_authority": manifest.get(
            "no_wallet_or_order_authority", True
        ),
    }


def _openrouter_review_dashboard_warnings(summary):
    if summary.get("artifact_status") == "missing":
        return [
            {
                "warning_id": "openrouter_review_dashboard_missing",
                "source_path": OPENROUTER_REVIEW_DASHBOARD_ARTIFACT_PATH,
                "category": "optional_artifact_missing",
                "message": "OpenRouter review dashboard artifact is missing; review pack generation continued.",
            }
        ]
    if summary.get("artifact_status") == "invalid":
        return [
            {
                "warning_id": "openrouter_review_dashboard_invalid",
                "source_path": OPENROUTER_REVIEW_DASHBOARD_ARTIFACT_PATH,
                "category": "optional_artifact_invalid",
                "message": "OpenRouter review dashboard artifact is present but invalid; inspect dashboard artifacts.",
            }
        ]
    return []


def _missing_artifacts(inventory):
    return [
        {
            "artifact_id": item["artifact_id"],
            "path": item["path"],
            "category": item["category"],
            "required": item["required"],
        }
        for item in inventory["artifacts"]
        if not item["present"]
    ]


def _parse_warnings(inventory):
    return [
        {
            "warning_id": f"{item['artifact_id']}_parse_failed",
            "source_path": item["path"],
            "category": "artifact_parse",
            "message": f"Artifact is present but JSON parse failed: {item.get('parse_error', 'unknown_error')}",
        }
        for item in inventory["artifacts"]
        if item["parse_status"] == "parse_failed"
    ]


def _next_safe_manual_actions():
    return [
        {
            "action_id": "review_pack_inventory_and_warnings",
            "description": "Review artifact_inventory, missing_artifacts, and warnings in this local pack.",
            "non_trading_action": True,
            "requires_runtime": False,
            "creates_orders": False,
        },
        {
            "action_id": "review_paper_accounting_audit_artifacts",
            "description": "Inspect the existing paper reconciliation and batch audit artifacts for local consistency status.",
            "non_trading_action": True,
            "requires_runtime": False,
            "creates_orders": False,
        },
        {
            "action_id": "review_operator_inbox_queue",
            "description": "Review accepted, rejected, and needs-human-review inbox records without executing commands.",
            "non_trading_action": True,
            "requires_runtime": False,
            "creates_orders": False,
        },
        {
            "action_id": "review_manual_llm_review_queue",
            "description": "Review manual LLM queue status for local packet and response readiness.",
            "non_trading_action": True,
            "requires_runtime": False,
            "creates_orders": False,
        },
        {
            "action_id": "review_actual_manual_llm_response_trial_surface",
            "description": (
                "Review actual manual LLM response trial status as offline local context only."
            ),
            "non_trading_action": True,
            "requires_runtime": False,
            "creates_orders": False,
        },
        {
            "action_id": "review_openrouter_passive_surface_pointer",
            "description": "Review OpenRouter batch surface pointer as read-only local context.",
            "non_trading_action": True,
            "requires_runtime": False,
            "creates_orders": False,
        },
        {
            "action_id": "fill_manual_resolution_source_capture_templates",
            "description": (
                "Use the SOURCE-004B guide and checklist to fill not_started local "
                "source capture templates, then rerun the validator."
            ),
            "non_trading_action": True,
            "requires_runtime": False,
            "creates_orders": False,
        },
        {
            "action_id": "integration_review_only",
            "description": "Use this pack as a static input for human integration review only.",
            "non_trading_action": True,
            "requires_runtime": False,
            "creates_orders": False,
        },
    ]


def build_operator_review_pack(root=ROOT):
    inventory, payloads = _artifact_inventory(root=root)
    quality_report, quality_load_status = _quality_report_payload(root=root)
    paper_019_summary = _paper_019_multi_market_run_series_summary(payloads, inventory)
    paper_020_summary = _paper_020_postmortem_summary(payloads, inventory)
    manual_llm_review = _manual_llm_review_summary(payloads, inventory)
    manual_llm_quality_gate = _manual_llm_quality_gate_summary(payloads, inventory)
    manual_llm_review_queue = _manual_llm_review_queue_summary(root=root)
    actual_manual_llm_response_trial = _actual_manual_llm_response_trial_summary(root=root)
    openrouter_passive_surface = _openrouter_passive_surface_summary(payloads, inventory)
    openrouter_review_dashboard = _openrouter_review_dashboard_summary(payloads, inventory)
    packet_completeness_gate = _packet_completeness_gate_summary(payloads, inventory)
    resolution_source_normalization = _resolution_source_normalization_summary(
        payloads, inventory
    )
    manual_resolution_source_capture = _manual_resolution_source_capture_summary(
        payloads, inventory
    )
    warnings = (
        _warnings(payloads)
        + _paper_019_warnings(paper_019_summary)
        + _paper_020_warnings(paper_020_summary)
        + _manual_llm_review_queue_warnings(manual_llm_review_queue)
        + _actual_manual_llm_response_trial_warnings(actual_manual_llm_response_trial)
        + _openrouter_passive_surface_warnings(openrouter_passive_surface)
        + _openrouter_review_dashboard_warnings(openrouter_review_dashboard)
        + _parse_warnings(inventory)
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_by": GENERATED_BY,
        "generated_at_policy": {
            "wall_clock_time_used": False,
            "policy": "deterministic_static_snapshot_no_current_time",
            "fixed_value": "not_emitted",
        },
        "product_stage_summary": _product_stage_summary(payloads),
        "artifact_inventory": inventory,
        "paper_audit_summary": _paper_audit_summary(payloads),
        "portfolio_accounting_summary": _portfolio_accounting_summary(payloads),
        "paper_019_multi_market_run_series": paper_019_summary,
        "paper_020_paper_run_series_postmortem": paper_020_summary,
        "dashboard_state_summary": _dashboard_state_summary(payloads),
        "operator_inbox_summary": _operator_inbox_summary(payloads),
        "manual_llm_review": manual_llm_review,
        "manual_llm_review_quality_gate": manual_llm_quality_gate,
        "manual_llm_review_queue": manual_llm_review_queue,
        "actual_manual_llm_response_trial": actual_manual_llm_response_trial,
        "openrouter_passive_surface": openrouter_passive_surface,
        "openrouter_review_dashboard": openrouter_review_dashboard,
        "packet_completeness_readiness_gate": packet_completeness_gate,
        "resolution_source_normalization": resolution_source_normalization,
        "manual_resolution_source_capture": manual_resolution_source_capture,
        "quality_warning_summary": _quality_warning_summary(quality_report, quality_load_status),
        "warnings": warnings,
        "missing_artifacts": _missing_artifacts(inventory),
        "safety_flags": dict(SAFETY_FLAGS),
        "forbidden_capabilities": list(FORBIDDEN_CAPABILITIES),
        "next_safe_manual_actions": _next_safe_manual_actions(),
        "accounting_only_interpretation_warning": ACCOUNTING_ONLY_WARNING,
        "no_recommendations_or_decisions_statement": NO_RECOMMENDATIONS_OR_DECISIONS_STATEMENT,
        "paper_orders_created": 0,
        "commands_executed": 0,
        "network_calls": 0,
    }


def render_operator_review_pack_markdown(pack):
    inventory = pack["artifact_inventory"]
    quality = pack["quality_warning_summary"]
    paper = pack["paper_audit_summary"]
    portfolio = pack["portfolio_accounting_summary"]
    paper_019 = pack["paper_019_multi_market_run_series"]
    paper_020 = pack["paper_020_paper_run_series_postmortem"]
    dashboard = pack["dashboard_state_summary"]
    inbox = pack["operator_inbox_summary"]
    manual_llm = pack["manual_llm_review"]
    manual_llm_quality_gate = pack["manual_llm_review_quality_gate"]
    manual_llm_review_queue = pack["manual_llm_review_queue"]
    actual_manual_llm_response_trial = pack["actual_manual_llm_response_trial"]
    openrouter_passive_surface = pack["openrouter_passive_surface"]
    openrouter_review_dashboard = pack["openrouter_review_dashboard"]
    packet_completeness_gate = pack["packet_completeness_readiness_gate"]
    resolution_source_normalization = pack["resolution_source_normalization"]
    manual_resolution_source_capture = pack["manual_resolution_source_capture"]
    lines = [
        "# PMBOT Operator Review Pack v1",
        "",
        f"- schema_version: {pack['schema_version']}",
        f"- generated_by: {pack['generated_by']}",
        f"- generated_at_policy: {pack['generated_at_policy']['policy']}",
        f"- product_direction: {pack['product_stage_summary']['product_direction']}",
        f"- paper_orders_created: {pack['paper_orders_created']}",
        f"- commands_executed: {pack['commands_executed']}",
        f"- network_calls: {pack['network_calls']}",
        "",
        "## Quality Warning Summary",
        "",
        f"- quality_report_status: {quality['quality_report_status']}",
        f"- total_warnings: {quality['total_warnings']}",
        f"- blocking_warnings: {quality['blocking_warnings']}",
        f"- action_required_warnings: {quality['action_required_warnings']}",
        f"- review_needed_warnings: {quality['review_needed_warnings']}",
        f"- informational_warnings: {quality['informational_warnings']}",
        f"- blocking_warning_detected: {str(quality['blocking_warning_detected']).lower()}",
        f"- operator_summary: {quality['operator_summary']}",
        f"- recommended_manual_action: {quality['recommended_manual_action']}",
        "",
        "## Quality Warning Interpretation",
        "",
    ]
    for severity in ("blocking", "action_required", "review_needed", "informational"):
        lines.append(f"- {severity}: {quality['severity_interpretation'][severity]}")
    lines.extend(
        [
            "",
            "## Top Quality Warning Categories",
            "",
        ]
    )
    if quality["top_warning_categories"]:
        for item in quality["top_warning_categories"]:
            lines.append(
                "- "
                f"{item['category']}: count={item['count']}, severity={item['severity']}, "
                f"bucket={item['operator_bucket']}"
            )
    else:
        lines.append("- none")
    lines.extend(
        [
            "",
            "## Quality Warnings By Owner",
            "",
        ]
    )
    by_owner = _safe_dict(quality.get("warnings_by_owner"))
    for owner in QUALITY_WARNING_OWNERS:
        lines.append(f"- {owner}: {by_owner.get(owner, 0)}")
    lines.extend(
        [
            "",
            "## Quality Warnings By Action Type",
            "",
        ]
    )
    by_action_type = _safe_dict(quality.get("warnings_by_action_type"))
    for action_type in QUALITY_WARNING_ACTION_TYPES:
        lines.append(f"- {action_type}: {by_action_type.get(action_type, 0)}")
    lines.extend(
        [
            "",
            "## Top Quality Action Items",
            "",
        ]
    )
    if quality["top_action_items"]:
        for item in quality["top_action_items"]:
            lines.append(
                "- "
                f"{item['recommended_action']}: count={item['count']}, owner={item['owner']}, "
                f"action_type={item['action_type']}, severity={item['severity']}"
            )
    else:
        lines.append("- none")
    lines.extend(
        [
            "",
            "## Artifact Inventory",
            "",
            f"- total_artifacts: {inventory['summary']['total_artifacts']}",
            f"- present_artifacts: {inventory['summary']['present_artifacts']}",
            f"- missing_artifacts: {inventory['summary']['missing_artifacts']}",
            f"- required_missing_artifacts: {inventory['summary']['required_missing_artifacts']}",
            "",
        ]
    )
    for item in inventory["artifacts"]:
        lines.append(
            "- "
            f"{item['artifact_id']}: {item['path']} "
            f"(present={str(item['present']).lower()}, required={str(item['required']).lower()}, "
            f"parse_status={item['parse_status']})"
        )

    lines.extend(
        [
            "",
            "## Paper Audits",
            "",
            f"- reconciliation_audit_status: {paper['reconciliation_audit']['audit_status']}",
            f"- reconciliation_checks_passed: {paper['reconciliation_audit']['counts']['checks_passed']}",
            f"- batch_audit_status: {paper['batch_audit']['audit_status']}",
            f"- batch_records_audited: {paper['batch_audit']['counts']['records_audited']}",
            f"- batch_checks_passed: {paper['batch_audit']['counts']['checks_passed']}",
            f"- audit_warnings_count: {paper['audit_warnings_count']}",
            f"- audit_mismatches_count: {paper['audit_mismatches_count']}",
            "",
            "## PAPER-019 Multi-Market Run Series",
            "",
            f"- section_id: {paper_019['section_id']}",
            f"- artifact_status: {paper_019['artifact_status']}",
            f"- artifact_pointer: {paper_019['artifact_pointer']}",
            f"- artifact_parse_status: {paper_019['artifact_parse_status']}",
            f"- series_status: {paper_019['series_status']}",
            f"- markets_seen: {paper_019['markets_seen']}",
            f"- records_seen: {paper_019['records_seen']}",
            f"- records_processed: {paper_019['records_processed']}",
            "",
            "## PAPER-019 Records By Status",
            "",
        ]
    )
    if paper_019["records_by_status"]:
        for status, count in paper_019["records_by_status"].items():
            lines.append(f"- {status}: {count}")
    else:
        lines.append("- none")
    lines.extend(
        [
            "",
            "## PAPER-019 Accounting-Only Summary",
            "",
        ]
    )
    if paper_019["accounting_summary"]:
        for key, value in paper_019["accounting_summary"].items():
            lines.append(f"- {key}: {value}")
    else:
        lines.append("- none")
    blocked_manual = paper_019["blocked_or_manual_review_summary"]
    lines.extend(
        [
            "",
            "## PAPER-019 Blocked Or Manual Review Summary",
            "",
            f"- blocked_fixture_record_count: {blocked_manual['blocked_fixture_record_count']}",
            f"- manual_review_only_count: {blocked_manual['manual_review_only_count']}",
            f"- blocked_or_rejected_records: {blocked_manual['blocked_or_rejected_records']}",
            f"- manual_review_only_records: {blocked_manual['manual_review_only_records']}",
        ]
    )
    if blocked_manual["records"]:
        for record in blocked_manual["records"]:
            lines.append(
                "- "
                f"{record['record_id']}: market_id={record['market_id']}, "
                f"processing_status={record['processing_status']}, lifecycle_state={record['lifecycle_state']}, "
                f"accounting_included={str(record['accounting_included']).lower()}"
            )
    else:
        lines.append("- records: none")
    lines.extend(
        [
            "",
            "## PAPER-019 Interpretation Warning",
            "",
            f"- {paper_019['interpretation_warning']}",
            "",
            "## PAPER-019 Safety Counters",
            "",
        ]
    )
    for key in (
        "real_orders_created",
        "autonomous_paper_orders",
        "network_calls",
        "commands_executed",
        "autonomous_decisions",
    ):
        lines.append(f"- {key}: {paper_019['safety_counters'][key]}")

    lines.extend(
        [
            "",
            "## PAPER-020 Paper Run Series Postmortem",
            "",
            f"- section_id: {paper_020['section_id']}",
            f"- artifact_status: {paper_020['artifact_status']}",
            f"- artifact_pointer: {paper_020['artifact_pointer']}",
            f"- artifact_parse_status: {paper_020['artifact_parse_status']}",
            f"- postmortem_status: {paper_020['postmortem_status']}",
            f"- source_paper_019_found: {str(paper_020['source_paper_019_found']).lower()}",
            f"- source_paper_019_series_status: {paper_020['source_paper_019']['series_status']}",
            f"- markets_seen: {paper_020['source_paper_019']['markets_seen']}",
            f"- records_seen: {paper_020['source_paper_019']['records_seen']}",
            f"- records_processed: {paper_020['source_paper_019']['records_processed']}",
            "",
            "## PAPER-020 Accounting-Only PnL Warning",
            "",
            f"- cumulative_pnl: {paper_020['cumulative_pnl']}",
            f"- accounting_only_warning_present: {str(paper_020['accounting_only_warning_present']).lower()}",
            f"- {paper_020['accounting_only_warning']}",
            "",
            "## PAPER-020 Record Status Summary",
            "",
        ]
    )
    if paper_020["record_status_notes"]:
        for item in paper_020["record_status_notes"]:
            lines.append(
                "- "
                f"{item['processing_status']}: count={item['count']}, "
                f"operator_meaning={item['operator_meaning']}"
            )
    else:
        lines.append("- none")
    lines.extend(["", "## PAPER-020 Fixture Limitations", ""])
    if paper_020["fixture_limitations"]:
        for item in paper_020["fixture_limitations"]:
            lines.append(f"- {item}")
    else:
        lines.append("- none")
    lines.extend(["", "## PAPER-020 Recommended Next Fixture Expansions", ""])
    if paper_020["recommended_next_fixture_expansions"]:
        for item in paper_020["recommended_next_fixture_expansions"]:
            lines.append(f"- {item}")
    else:
        lines.append("- none")
    lines.extend(["", "## PAPER-020 Safety Counters", ""])
    for key in (
        "real_orders_created",
        "autonomous_paper_orders",
        "network_calls",
        "commands_executed",
        "autonomous_decisions",
    ):
        lines.append(f"- {key}: {paper_020['safety_counters'][key]}")
    lines.extend(
        [
            "",
            "## PAPER-020 Next Safe Action",
            "",
            f"- {paper_020['next_safe_action']}",
        ]
    )

    lines.extend(
        [
            "",
            "## Portfolio Accounting",
            "",
            f"- summary_status: {portfolio['summary_status']}",
            f"- accepted_accounting_market_ids: {', '.join(portfolio['accepted_accounting_market_ids'])}",
            f"- paper_accounting_cumulative_pnl: {portfolio['paper_accounting_metrics'].get('paper_accounting_cumulative_pnl')}",
            f"- batch_accounting_cumulative_pnl: {portfolio['batch_accounting_totals'].get('paper_accounting_cumulative_pnl')}",
            f"- accounting_boundary_warning: {portfolio['interpretation_boundary']['warning']}",
            "",
            "## Dashboard State",
            "",
            f"- present: {str(dashboard['present']).lower()}",
            f"- schema_version: {dashboard['schema_version']}",
            f"- dashboard_state_export_version: {dashboard['dashboard_state_export_version']}",
            f"- known_market_ids: {', '.join(dashboard['known_market_ids'])}",
            f"- current_known_portfolio_audit_status: {dashboard['current_known_portfolio_audit_status']}",
            "",
            "## Operator Inbox",
            "",
            f"- records_seen: {inbox['records_seen']}",
            f"- accepted_count: {inbox['accepted_count']}",
            f"- rejected_count: {inbox['rejected_count']}",
            f"- needs_human_review_count: {inbox['needs_human_review_count']}",
            f"- execution_authority: {str(inbox['execution_authority']).lower()}",
            f"- commands_executed: {inbox['commands_executed']}",
            f"- network_calls: {inbox['network_calls']}",
            "",
            "## Manual LLM Review",
            "",
            f"- section_id: {manual_llm['section_id']}",
            f"- artifact_status: {manual_llm['artifact_status']}",
            f"- artifact_pointer: {manual_llm['artifact_pointer']}",
            f"- artifact_parse_status: {manual_llm['artifact_parse_status']}",
            f"- validation_status: {manual_llm['validation_status']}",
            f"- errors_count: {manual_llm['errors_count']}",
            f"- warnings_count: {manual_llm['warnings_count']}",
            "- forbidden_content_detected: "
            f"detected={str(manual_llm['forbidden_content_detected']['detected']).lower()}, "
            f"findings_count={manual_llm['forbidden_content_detected']['findings_count']}",
            f"- next_safe_operator_action: {manual_llm['next_safe_operator_action']}",
            f"- analysis_only_warning: {manual_llm['analysis_only_warning']}",
            f"- llm_text_generated: {str(manual_llm['llm_text_generated']).lower()}",
            f"- llm_api_calls_added: {str(manual_llm['llm_api_calls_added']).lower()}",
            f"- browser_automation_added: {str(manual_llm['browser_automation_added']).lower()}",
            f"- runtime_integration_added: {str(manual_llm['runtime_integration_added']).lower()}",
            "",
            "## Manual LLM Accepted Sections",
            "",
        ]
    )
    if manual_llm["accepted_sections"]:
        for section in manual_llm["accepted_sections"]:
            lines.append(f"- {section}")
    else:
        lines.append("- none")
    lines.extend(["", "## Manual LLM Missing Sections", ""])
    if manual_llm["missing_sections"]:
        for section in manual_llm["missing_sections"]:
            lines.append(f"- {section}")
    else:
        lines.append("- none")
    lines.extend(["", "## Manual LLM Safe Error Summary", ""])
    if manual_llm["safe_error_summary"]:
        for item in manual_llm["safe_error_summary"]:
            lines.append(f"- {item}")
    else:
        lines.append("- none")

    gate_counts = manual_llm_quality_gate["quality_counts"]
    required_check = manual_llm_quality_gate["required_sections_check"]
    minimum_check = manual_llm_quality_gate["minimum_content_check"]
    placeholder_check = manual_llm_quality_gate["generic_or_placeholder_text_check"]
    unsafe_certainty_check = manual_llm_quality_gate["unsafe_certainty_check"]
    forbidden_content_check = manual_llm_quality_gate["forbidden_content_check"]
    lines.extend(
        [
            "",
            "## Manual LLM Review Quality Gate",
            "",
            f"- section_id: {manual_llm_quality_gate['section_id']}",
            f"- artifact_status: {manual_llm_quality_gate['artifact_status']}",
            f"- artifact_pointer: {manual_llm_quality_gate['artifact_pointer']}",
            f"- artifact_parse_status: {manual_llm_quality_gate['artifact_parse_status']}",
            f"- validation_status: {manual_llm_quality_gate['validation_status']}",
            f"- base_validator_status: {manual_llm_quality_gate['base_validator_status']}",
            f"- checks_total: {gate_counts['checks_total']}",
            f"- checks_passed: {gate_counts['checks_passed']}",
            f"- checks_with_warnings: {gate_counts['checks_with_warnings']}",
            f"- checks_failed: {gate_counts['checks_failed']}",
            f"- errors_count: {gate_counts['errors_count']}",
            f"- warnings_count: {gate_counts['warnings_count']}",
            f"- next_safe_operator_action: {manual_llm_quality_gate['next_safe_operator_action']}",
            f"- deterministic_quality_gate_warning: {manual_llm_quality_gate['deterministic_quality_gate_warning']}",
            f"- llm_text_generated: {str(manual_llm_quality_gate['llm_text_generated']).lower()}",
            f"- llm_api_calls_added: {str(manual_llm_quality_gate['llm_api_calls_added']).lower()}",
            f"- browser_automation_added: {str(manual_llm_quality_gate['browser_automation_added']).lower()}",
            f"- runtime_integration_added: {str(manual_llm_quality_gate['runtime_integration_added']).lower()}",
            "",
            "## Manual LLM Quality Gate Check Summaries",
            "",
            "- required_sections_check: "
            f"status={required_check['status']}, "
            f"required_sections_count={required_check['required_sections_count']}, "
            f"present_sections_count={required_check['present_sections_count']}, "
            f"missing_sections_count={required_check['missing_sections_count']}, "
            f"empty_sections_count={required_check['empty_sections_count']}, "
            f"errors_count={required_check['errors_count']}, "
            f"warnings_count={required_check['warnings_count']}",
            "- minimum_content_check: "
            f"status={minimum_check['status']}, "
            f"errors_count={minimum_check['errors_count']}, "
            f"warnings_count={minimum_check['warnings_count']}",
            "- generic_or_placeholder_text_check: "
            f"status={placeholder_check['status']}, "
            f"placeholder_findings_count={placeholder_check['placeholder_findings_count']}, "
            "repeated_cannot_determine_paths_count="
            f"{placeholder_check['repeated_cannot_determine_paths_count']}, "
            f"errors_count={placeholder_check['errors_count']}, "
            f"warnings_count={placeholder_check['warnings_count']}",
            "- unsafe_certainty_check: "
            f"status={unsafe_certainty_check['status']}, "
            f"unsafe_certainty_detected={str(unsafe_certainty_check['unsafe_certainty_detected']).lower()}, "
            f"findings_count={unsafe_certainty_check['findings_count']}, "
            f"errors_count={unsafe_certainty_check['errors_count']}, "
            f"warnings_count={unsafe_certainty_check['warnings_count']}",
            "- forbidden_content_check: "
            f"status={forbidden_content_check['status']}, "
            "forbidden_content_detected="
            f"{str(forbidden_content_check['forbidden_content_detected']).lower()}, "
            f"findings_count={forbidden_content_check['findings_count']}, "
            f"errors_count={forbidden_content_check['errors_count']}, "
            f"warnings_count={forbidden_content_check['warnings_count']}",
            "",
            "## Manual LLM Quality Gate Safe Error Summary",
            "",
        ]
    )
    if manual_llm_quality_gate["safe_error_summary"]:
        for item in manual_llm_quality_gate["safe_error_summary"]:
            lines.append(f"- {item}")
    else:
        lines.append("- none")

    lines.extend(
        [
            "",
            "## Manual LLM Review Queue",
            "",
            f"- section_id: {manual_llm_review_queue['section_id']}",
            f"- artifact_status: {manual_llm_review_queue['artifact_status']}",
            f"- artifact_pointer: {manual_llm_review_queue['artifact_pointer']}",
            f"- parse_status: {manual_llm_review_queue['parse_status']}",
            f"- queue_items_total: {manual_llm_review_queue['queue_items_total']}",
            "- additional_ready_candidates_found: "
            f"{manual_llm_review_queue['additional_ready_candidates_found']}",
            f"- errors_count: {manual_llm_review_queue['errors_count']}",
            f"- warnings_count: {manual_llm_review_queue['warnings_count']}",
            "- offline_manual_only: "
            f"{str(manual_llm_review_queue['offline_manual_only']).lower()}",
            f"- not_truth_source: {str(manual_llm_review_queue['not_truth_source']).lower()}",
            f"- not_trading_advice: {str(manual_llm_review_queue['not_trading_advice']).lower()}",
            "- not_execution_authority: "
            f"{str(manual_llm_review_queue['not_execution_authority']).lower()}",
            f"- offline_review_warning: {manual_llm_review_queue['offline_review_warning']}",
            f"- llm_api_calls_added: {str(manual_llm_review_queue['llm_api_calls_added']).lower()}",
            "- browser_automation_added: "
            f"{str(manual_llm_review_queue['browser_automation_added']).lower()}",
            "- runtime_integration_added: "
            f"{str(manual_llm_review_queue['runtime_integration_added']).lower()}",
            "",
            "## Manual LLM Review Queue Status Counts",
            "",
        ]
    )
    for status, count in manual_llm_review_queue["queue_status_counts"].items():
        lines.append(f"- {status}: {count}")
    lines.extend(["", "## Manual LLM Review Queue Items", ""])
    if manual_llm_review_queue["items"]:
        for item in manual_llm_review_queue["items"]:
            lines.append(
                "- "
                f"market_id={item['market_id']}, "
                f"status={item['review_queue_status']}, "
                f"response_present={str(item['response_present']).lower()}, "
                f"validation_status={item['validation_status']}, "
                f"quality_gate_status={item['quality_gate_status']}, "
                f"operator_surface_review_status={item['operator_surface_review_status']}"
            )
    else:
        lines.append("- none")
    lines.extend(["", "## Manual LLM Review Queue Safe Error Summary", ""])
    if manual_llm_review_queue["safe_error_summary"]:
        for item in manual_llm_review_queue["safe_error_summary"]:
            lines.append(f"- {item}")
    else:
        lines.append("- none")

    lines.extend(
        [
            "",
            "## Actual Manual LLM Response Trial",
            "",
            f"- section_id: {actual_manual_llm_response_trial['section_id']}",
            f"- artifact_status: {actual_manual_llm_response_trial['artifact_status']}",
            f"- artifact_path: {actual_manual_llm_response_trial['artifact_path']}",
            f"- artifact_present: {str(actual_manual_llm_response_trial['artifact_present']).lower()}",
            f"- parse_status: {actual_manual_llm_response_trial['parse_status']}",
            f"- operator_response_path: {actual_manual_llm_response_trial['operator_response_path']}",
            "- operator_response_present: "
            f"{str(actual_manual_llm_response_trial['operator_response_present']).lower()}",
            "- trial_artifact_operator_response_present: "
            f"{str(actual_manual_llm_response_trial['trial_artifact_operator_response_present']).lower()}",
            f"- response_source_type: {actual_manual_llm_response_trial['response_source_type'] or 'not_available'}",
            f"- market_id: {actual_manual_llm_response_trial['market_id'] or 'not_available'}",
            f"- source_artifact_path: {actual_manual_llm_response_trial['source_artifact_path'] or 'not_available'}",
            "- trial_packet_source_type: "
            f"{actual_manual_llm_response_trial['trial_packet_source_type'] or 'not_available'}",
            f"- run_status: {actual_manual_llm_response_trial['run_status']}",
            f"- acceptance_status: {actual_manual_llm_response_trial['acceptance_status']}",
            "- response_validation_status: "
            f"{actual_manual_llm_response_trial['response_validation_status']}",
            f"- manual_review_status: {actual_manual_llm_response_trial['manual_review_status']}",
            f"- quality_gate_status: {actual_manual_llm_response_trial['quality_gate_status']}",
            f"- errors_count: {actual_manual_llm_response_trial['errors_count']}",
            f"- warnings_count: {actual_manual_llm_response_trial['warnings_count']}",
            "- next_safe_operator_action: "
            f"{actual_manual_llm_response_trial['next_safe_operator_action']}",
            "- offline_review_context_only: "
            f"{str(actual_manual_llm_response_trial['offline_review_context_only']).lower()}",
            f"- not_truth_source: {str(actual_manual_llm_response_trial['not_truth_source']).lower()}",
            f"- not_trading_advice: {str(actual_manual_llm_response_trial['not_trading_advice']).lower()}",
            "- not_execution_authority: "
            f"{str(actual_manual_llm_response_trial['not_execution_authority']).lower()}",
            f"- explicit_warning: {actual_manual_llm_response_trial['explicit_operator_warning']}",
            "",
            "## Actual Manual LLM Response Trial Safety Flags",
            "",
        ]
    )
    for key in sorted(actual_manual_llm_response_trial["safety_flags"]):
        lines.append(
            f"- {key}: {str(actual_manual_llm_response_trial['safety_flags'][key]).lower()}"
        )

    lines.extend(
        [
            "",
            "## OpenRouter Passive Surface",
            "",
            f"- section_id: {openrouter_passive_surface['section_id']}",
            f"- artifact_status: {openrouter_passive_surface['artifact_status']}",
            f"- artifact_pointer: {openrouter_passive_surface['artifact_pointer']}",
            "- artifact_markdown_pointer: "
            f"{openrouter_passive_surface['artifact_markdown_pointer']}",
            f"- artifact_parse_status: {openrouter_passive_surface['artifact_parse_status']}",
            "- latest_surface_source_batch_task: "
            f"{openrouter_passive_surface['latest_surface_source_batch_task']}",
            f"- latest_surface_task: {openrouter_passive_surface['latest_surface_task']}",
            f"- source_batch_task: {openrouter_passive_surface['source_batch_task']}",
            f"- source_baseline_task: {openrouter_passive_surface['source_baseline_task']}",
            f"- source_surface_task: {openrouter_passive_surface['source_surface_task']}",
            f"- source_048_status: {openrouter_passive_surface['source_048_status']}",
            f"- source_052_status: {openrouter_passive_surface['source_052_status']}",
            f"- surfaced_market_ids: {', '.join(openrouter_passive_surface['surfaced_market_ids'])}",
            f"- model: {openrouter_passive_surface['model']}",
            f"- total_calls: {openrouter_passive_surface['total_calls']}",
            "- prompt_tokens: "
            f"{openrouter_passive_surface['aggregate_usage'].get('prompt_tokens', 0)}",
            "- completion_tokens: "
            f"{openrouter_passive_surface['aggregate_usage'].get('completion_tokens', 0)}",
            "- total_tokens: "
            f"{openrouter_passive_surface['aggregate_usage'].get('total_tokens', 0)}",
            "- total_cost: "
            f"{openrouter_passive_surface['aggregate_cost'].get('total_cost', 0)}",
            "- average_cost_per_market: "
            f"{openrouter_passive_surface['aggregate_cost'].get('average_cost_per_market', 0)}",
            "- fenced_response_count: "
            f"{openrouter_passive_surface['normalization_summary'].get('fenced_response_count', 0)}",
            "- normalized_response_count: "
            f"{openrouter_passive_surface['normalization_summary'].get('normalized_response_count', 0)}",
            "- clean_raw_json_response_count: "
            f"{openrouter_passive_surface['normalization_summary'].get('clean_raw_json_response_count', 0)}",
            "- accepted_for_operator_review_count: "
            f"{openrouter_passive_surface['quality_summary'].get('accepted_for_operator_review_count', 0)}",
            f"- blocked_count: {openrouter_passive_surface['quality_summary'].get('blocked_count', 0)}",
            f"- offline_review_warning: {openrouter_passive_surface['offline_review_warning']}",
            "",
            "## OpenRouter Passive Surface History",
            "",
        ]
    )
    for entry in openrouter_passive_surface["surface_history"]:
        lines.append(
            "- "
            f"{entry['batch_label']}: calls={entry['total_calls']}, "
            f"markets={', '.join(entry['surfaced_market_ids'])}, "
            f"tokens={entry['aggregate_usage'].get('total_tokens', 0)}, "
            f"cost={entry['aggregate_cost'].get('total_cost', 0)}"
        )
    combined_openrouter = openrouter_passive_surface["combined_openrouter_review_contour_summary"]
    lines.extend(
        [
            "",
            "## OpenRouter Combined Review Contour",
            "",
            "- total_markets_successfully_reviewed: "
            f"{combined_openrouter.get('total_markets_successfully_reviewed', 0)}",
            "- total_openrouter_calls_in_successful_batches: "
            f"{combined_openrouter.get('total_openrouter_calls_in_successful_batches', 0)}",
            f"- combined_cost: {combined_openrouter.get('combined_cost', 0)}",
            f"- combined_tokens: {combined_openrouter.get('combined_tokens', 0)}",
            "- total_blocked_in_successful_batches: "
            f"{combined_openrouter.get('total_blocked_in_successful_batches', 0)}",
            "",
            "## OpenRouter Passive Surface Safety Flags",
            "",
        ]
    )
    for key in openrouter_passive_surface_pointer.REQUIRED_TRUE_FLAGS:
        lines.append(
            f"- {key}: {str(openrouter_passive_surface['safety_summary'][key]).lower()}"
        )
    lines.extend(["", "## OpenRouter Passive Surface Artifact Pointers", ""])
    if openrouter_passive_surface["artifact_pointers"]:
        for key, item in openrouter_passive_surface["artifact_pointers"].items():
            lines.append(f"- {key}: {item['path']} ({item['role']})")
    else:
        lines.append("- none")

    lines.extend(
        [
            "",
            "## Packet Completeness Readiness Gate",
            "",
            f"- section_id: {packet_completeness_gate['section_id']}",
            f"- artifact_status: {packet_completeness_gate['artifact_status']}",
            f"- artifact_pointer: {packet_completeness_gate['artifact_pointer']}",
            "- artifact_markdown_pointer: "
            f"{packet_completeness_gate['artifact_markdown_pointer']}",
            f"- artifact_parse_status: {packet_completeness_gate['artifact_parse_status']}",
            f"- gate_version: {packet_completeness_gate['gate_version']}",
            f"- total_markets: {packet_completeness_gate['total_markets']}",
            f"- high_count: {packet_completeness_gate['high_count']}",
            f"- medium_count: {packet_completeness_gate['medium_count']}",
            f"- low_count: {packet_completeness_gate['low_count']}",
            f"- blocked_count: {packet_completeness_gate['blocked_count']}",
            "- eligible_for_future_llm_review_count: "
            f"{packet_completeness_gate['eligible_for_future_llm_review_count']}",
            "- eligible_for_future_openrouter_batch_count: "
            f"{packet_completeness_gate['eligible_for_future_openrouter_batch_count']}",
            "- needs_local_enrichment_count: "
            f"{packet_completeness_gate['needs_local_enrichment_count']}",
            "- needs_local_enrichment_before_future_openrouter_batch_count: "
            f"{packet_completeness_gate['needs_local_enrichment_before_future_openrouter_batch_count']}",
            "- low_readiness_market_ids: "
            f"{', '.join(packet_completeness_gate['low_readiness_market_ids'])}",
            "- unreviewed_market_ids: "
            f"{', '.join(packet_completeness_gate['unreviewed_market_ids'])}",
            "- future_live_batch_scheduled: "
            f"{str(packet_completeness_gate['future_live_batch_scheduled']).lower()}",
            "- future_openrouter_batch_approved: "
            f"{str(packet_completeness_gate['future_openrouter_batch_approved']).lower()}",
            "- no_market_action_guidance: "
            f"{str(packet_completeness_gate['no_market_action_guidance']).lower()}",
            "",
            "## Packet Completeness Top Missing Fields",
            "",
        ]
    )
    for item in packet_completeness_gate["top_missing_fields"]:
        lines.append(f"- {item['field']}: {item['market_count']}")
    lines.extend(["", "## Packet Completeness Next Local Focus", ""])
    for item in packet_completeness_gate["recommended_next_local_enrichment_focus"]:
        lines.append(f"- {item}")

    lines.extend(
        [
            "",
            "## Resolution Source Normalization",
            "",
            f"- section_id: {resolution_source_normalization['section_id']}",
            "- audit_artifact_status: "
            f"{resolution_source_normalization['audit_artifact_status']}",
            "- audit_artifact_pointer: "
            f"{resolution_source_normalization['audit_artifact_pointer']}",
            "- audit_artifact_markdown_pointer: "
            f"{resolution_source_normalization['audit_artifact_markdown_pointer']}",
            "- readiness_artifact_pointer: "
            f"{resolution_source_normalization['readiness_artifact_pointer']}",
            "- batch_gate_artifact_pointer: "
            f"{resolution_source_normalization['batch_gate_artifact_pointer']}",
            "- action_plan_artifact_pointer: "
            f"{resolution_source_normalization['action_plan_artifact_pointer']}",
            "- total_markets_audited: "
            f"{resolution_source_normalization['total_markets_audited']}",
            "- markets_missing_resolution_criteria_text: "
            f"{resolution_source_normalization['markets_missing_resolution_criteria_text']}",
            "- markets_missing_full_resolution_rules: "
            f"{resolution_source_normalization['markets_missing_full_resolution_rules']}",
            "- markets_missing_official_source_references: "
            f"{resolution_source_normalization['markets_missing_official_source_references']}",
            "- markets_needing_manual_resolution_source_review: "
            f"{resolution_source_normalization['markets_needing_manual_resolution_source_review']}",
            "- previous_average_score: "
            f"{resolution_source_normalization['previous_readiness_summary']['average_score']}",
            "- updated_average_score: "
            f"{resolution_source_normalization['updated_readiness_summary']['average_score']}",
            "- score_delta_average: "
            f"{resolution_source_normalization['updated_readiness_summary']['score_delta_average']}",
            "- markets_improved_by_source_normalization: "
            + ", ".join(
                resolution_source_normalization["markets_improved_by_source_normalization"]
            ),
            "- markets_still_missing_resolution_sources: "
            + ", ".join(
                resolution_source_normalization["markets_still_missing_resolution_sources"]
            ),
            "- future_openrouter_batch_approved: "
            f"{str(resolution_source_normalization['future_openrouter_batch_approved']).lower()}",
            "- passive_only: "
            f"{str(resolution_source_normalization['passive_only']).lower()}",
            "- queue_items_created: "
            f"{resolution_source_normalization['queue_items_created']}",
            "- queue_state_mutated: "
            f"{str(resolution_source_normalization['queue_state_mutated']).lower()}",
            "- no_market_action_guidance: "
            f"{str(resolution_source_normalization['no_market_action_guidance']).lower()}",
            "",
            "## Resolution Source Top Gaps",
            "",
        ]
    )
    for item in resolution_source_normalization["top_resolution_source_gaps"]:
        lines.append(f"- {item['field']}: {item['market_count']}")

    lines.extend(
        [
            "",
            "## Manual Resolution Source Capture",
            "",
            f"- section_id: {manual_resolution_source_capture['section_id']}",
            "- guide_pointer: "
            f"{manual_resolution_source_capture['guide_pointer']}",
            "- checklist_pointer: "
            f"{manual_resolution_source_capture['checklist_pointer']}",
            "- checklist_markdown_pointer: "
            f"{manual_resolution_source_capture['checklist_markdown_pointer']}",
            "- progress_pointer: "
            f"{manual_resolution_source_capture['progress_pointer']}",
            "- progress_markdown_pointer: "
            f"{manual_resolution_source_capture['progress_markdown_pointer']}",
            "- target_capture_directory: "
            f"{manual_resolution_source_capture['target_capture_directory']}",
            "- schema_pointer: "
            f"{manual_resolution_source_capture['schema_pointer']}",
            "- manifest_pointer: "
            f"{manual_resolution_source_capture['manifest_pointer']}",
            "- manifest_markdown_pointer: "
            f"{manual_resolution_source_capture['manifest_markdown_pointer']}",
            "- validation_pointer: "
            f"{manual_resolution_source_capture['validation_pointer']}",
            "- validation_markdown_pointer: "
            f"{manual_resolution_source_capture['validation_markdown_pointer']}",
            "- total_capture_packets: "
            f"{manual_resolution_source_capture['total_capture_packets']}",
            "- total_templates: "
            f"{manual_resolution_source_capture['total_templates']}",
            "- packets_created: "
            f"{manual_resolution_source_capture['packets_created']}",
            "- packets_not_started: "
            f"{manual_resolution_source_capture['packets_not_started']}",
            "- packets_ready_for_local_review: "
            f"{manual_resolution_source_capture['packets_ready_for_local_review']}",
            "- validation_valid_count: "
            f"{manual_resolution_source_capture['validation_valid_count']}",
            "- validation_invalid_count: "
            f"{manual_resolution_source_capture['validation_invalid_count']}",
            "- validation_command: "
            f"{manual_resolution_source_capture['validation_command']}",
            "- next_operator_action: "
            f"{manual_resolution_source_capture['next_operator_action']}",
            "- no_market_action_guidance: "
            f"{str(manual_resolution_source_capture['no_market_action_guidance']).lower()}",
            "- no_trading_authority: "
            f"{str(manual_resolution_source_capture['no_trading_authority']).lower()}",
            "- no_queue_authority: "
            f"{str(manual_resolution_source_capture['no_queue_authority']).lower()}",
            "- no_runtime_authority: "
            f"{str(manual_resolution_source_capture['no_runtime_authority']).lower()}",
            "- no_wallet_or_order_authority: "
            f"{str(manual_resolution_source_capture['no_wallet_or_order_authority']).lower()}",
            "",
            "## Manual Capture Recommended Fill Order",
            "",
        ]
    )
    for index, field in enumerate(
        manual_resolution_source_capture["recommended_operator_fill_order"], start=1
    ):
        lines.append(f"{index}. {field}")
    lines.extend(["", "## Manual Capture Status Counts", ""])
    for status, count in manual_resolution_source_capture["current_status_counts"].items():
        lines.append(f"- {status}: {count}")

    lines.extend(
        [
            "",
            "## OpenRouter Review Dashboard",
            "",
            f"- section_id: {openrouter_review_dashboard['section_id']}",
            f"- artifact_status: {openrouter_review_dashboard['artifact_status']}",
            f"- artifact_pointer: {openrouter_review_dashboard['artifact_pointer']}",
            "- artifact_markdown_pointer: "
            f"{openrouter_review_dashboard['artifact_markdown_pointer']}",
            f"- latest_surface: {openrouter_review_dashboard['latest_surface']}",
            f"- latest_baseline: {openrouter_review_dashboard['latest_baseline']}",
            "- latest_workbench_integration_status: "
            f"{openrouter_review_dashboard['latest_workbench_integration_status']}",
            "- combined_cost: "
            f"{openrouter_review_dashboard['cost_summary'].get('combined_cost', 0)}",
            "- combined_tokens: "
            f"{openrouter_review_dashboard['usage_summary'].get('combined_tokens', 0)}",
            "- total_markets_found: "
            f"{openrouter_review_dashboard['inventory_summary'].get('total_markets_found', 0)}",
            "- total_reviewed_by_openrouter: "
            f"{openrouter_review_dashboard['inventory_summary'].get('total_reviewed_by_openrouter', 0)}",
            "- evidence_readiness_integration_status: "
            f"{openrouter_review_dashboard['evidence_readiness_integration_status']}",
            "- evidence_readiness_low_count: "
            f"{openrouter_review_dashboard['evidence_readiness_score_summary'].get('low_count', 0)}",
            "- average_evidence_readiness_score: "
            f"{openrouter_review_dashboard['evidence_readiness_score_summary'].get('average_evidence_readiness_score', 0)}",
            "- markets_with_medium_evidence_completeness: "
            f"{', '.join(openrouter_review_dashboard['markets_with_medium_evidence_completeness'])}",
            "- recommended_next_local_enrichment_focus: "
            f"{', '.join(openrouter_review_dashboard['recommended_next_local_enrichment_focus'])}",
            "- no_market_action_guidance: "
            f"{str(openrouter_review_dashboard['no_market_action_guidance']).lower()}",
        ]
    )

    lines.extend(
        [
            "",
            "## Missing Artifacts",
            "",
        ]
    )
    if pack["missing_artifacts"]:
        for item in pack["missing_artifacts"]:
            lines.append(f"- {item['path']} (required={str(item['required']).lower()})")
    else:
        lines.append("- none")

    lines.extend(["", "## Warnings", ""])
    for warning in pack["warnings"]:
        lines.append(f"- {warning['warning_id']}: {warning['message']}")

    lines.extend(["", "## Safety Flags", ""])
    for key in sorted(pack["safety_flags"]):
        lines.append(f"- {key}: {str(pack['safety_flags'][key]).lower()}")

    lines.extend(["", "## Next Safe Manual Actions", ""])
    for action in pack["next_safe_manual_actions"]:
        lines.append(f"- {action['action_id']}: {action['description']}")
    lines.extend(["", f"- {pack['no_recommendations_or_decisions_statement']}", ""])
    return "\n".join(lines)


def _result_payload(pack):
    required_missing = [item["path"] for item in pack["missing_artifacts"] if item["required"]]
    parse_failed = [
        item["path"]
        for item in pack["artifact_inventory"]["artifacts"]
        if item["required"] and item["parse_status"] == "parse_failed"
    ]
    blockers = []
    if required_missing:
        blockers.append(f"missing required artifacts: {', '.join(required_missing)}")
    if parse_failed:
        blockers.append(f"required JSON artifacts failed to parse: {', '.join(parse_failed)}")
    completed = not blockers
    return {
        "task_id": TASK_ID,
        "codex_lane": CODEX_LANE,
        "status": "completed_ready_for_review" if completed else "blocked",
        "summary": (
            "Implemented deterministic local operator review pack export."
            if completed
            else "Operator review pack export found missing or unparsable required artifacts."
        ),
        "branch": "codex/a-operator-review-pack-round003",
        "worktree_path": "C:\\Users\\OpenC\\Documents\\AI-Orchestrator-worktrees\\CODEX_A_round003_operator_review_pack",
        "base_commit": BASE_COMMIT,
        "product_direction": PRODUCT_DIRECTION,
        "files_created": [
            "pm_bot/workbench/export_operator_review_pack.py",
            "pm_bot/workbench/operator_review_pack.v1.json",
            "pm_bot/workbench/operator_review_pack.v1.md",
            "pm_bot/workbench/expected_operator_review_pack.v1.json",
            "pm_bot/workbench/tests/test_operator_review_pack_export.py",
            "docs/PMBOT_WORKBENCH_001_RESULT.json",
            "docs/PMBOT_CODEX_A_ROUND003_RESULT.json",
        ],
        "files_modified": [],
        "tests": [],
        "artifact_inventory_summary": pack["artifact_inventory"]["summary"],
        "actual_manual_llm_response_trial": {
            "artifact_present": pack["actual_manual_llm_response_trial"]["artifact_present"],
            "operator_response_present": pack["actual_manual_llm_response_trial"][
                "operator_response_present"
            ],
            "run_status": pack["actual_manual_llm_response_trial"]["run_status"],
            "acceptance_status": pack["actual_manual_llm_response_trial"]["acceptance_status"],
            "offline_review_context_only": pack["actual_manual_llm_response_trial"][
                "offline_review_context_only"
            ],
            "not_truth_source": pack["actual_manual_llm_response_trial"]["not_truth_source"],
            "not_trading_advice": pack["actual_manual_llm_response_trial"]["not_trading_advice"],
            "not_execution_authority": pack["actual_manual_llm_response_trial"][
                "not_execution_authority"
            ],
        },
        "manual_llm_review_queue": {
            "artifact_present": pack["manual_llm_review_queue"]["artifact_present"],
            "queue_items_total": pack["manual_llm_review_queue"]["queue_items_total"],
            "queue_status_counts": pack["manual_llm_review_queue"]["queue_status_counts"],
            "offline_manual_only": pack["manual_llm_review_queue"]["offline_manual_only"],
            "not_truth_source": pack["manual_llm_review_queue"]["not_truth_source"],
            "not_trading_advice": pack["manual_llm_review_queue"]["not_trading_advice"],
            "not_execution_authority": pack["manual_llm_review_queue"]["not_execution_authority"],
        },
        "openrouter_passive_surface": {
            "artifact_status": pack["openrouter_passive_surface"]["artifact_status"],
            "artifact_pointer": pack["openrouter_passive_surface"]["artifact_pointer"],
            "latest_surface_source_batch_task": pack["openrouter_passive_surface"][
                "latest_surface_source_batch_task"
            ],
            "latest_surface_task": pack["openrouter_passive_surface"]["latest_surface_task"],
            "source_048_status": pack["openrouter_passive_surface"]["source_048_status"],
            "source_052_status": pack["openrouter_passive_surface"]["source_052_status"],
            "surfaced_market_ids": pack["openrouter_passive_surface"]["surfaced_market_ids"],
            "model": pack["openrouter_passive_surface"]["model"],
            "total_calls": pack["openrouter_passive_surface"]["total_calls"],
            "aggregate_usage": pack["openrouter_passive_surface"]["aggregate_usage"],
            "aggregate_cost": pack["openrouter_passive_surface"]["aggregate_cost"],
            "normalization_summary": pack["openrouter_passive_surface"]["normalization_summary"],
            "quality_summary": pack["openrouter_passive_surface"]["quality_summary"],
            "surface_history": pack["openrouter_passive_surface"]["surface_history"],
            "combined_openrouter_review_contour_summary": pack["openrouter_passive_surface"][
                "combined_openrouter_review_contour_summary"
            ],
            "safety_summary": pack["openrouter_passive_surface"]["safety_summary"],
        },
        "openrouter_review_dashboard": {
            "artifact_status": pack["openrouter_review_dashboard"]["artifact_status"],
            "artifact_pointer": pack["openrouter_review_dashboard"]["artifact_pointer"],
            "latest_surface": pack["openrouter_review_dashboard"]["latest_surface"],
            "latest_baseline": pack["openrouter_review_dashboard"]["latest_baseline"],
            "combined_openrouter_review_contour_summary": pack["openrouter_review_dashboard"][
                "combined_openrouter_review_contour_summary"
            ],
            "inventory_summary": pack["openrouter_review_dashboard"]["inventory_summary"],
            "evidence_completeness_summary": pack["openrouter_review_dashboard"][
                "evidence_completeness_summary"
            ],
            "evidence_readiness_score_summary": pack["openrouter_review_dashboard"][
                "evidence_readiness_score_summary"
            ],
            "category_gap_summary": pack["openrouter_review_dashboard"]["category_gap_summary"],
            "markets_reviewed_vs_unreviewed": pack["openrouter_review_dashboard"][
                "markets_reviewed_vs_unreviewed"
            ],
            "markets_with_medium_evidence_completeness": pack["openrouter_review_dashboard"][
                "markets_with_medium_evidence_completeness"
            ],
            "recommended_next_local_enrichment_focus": pack["openrouter_review_dashboard"][
                "recommended_next_local_enrichment_focus"
            ],
            "no_market_action_guidance": pack["openrouter_review_dashboard"][
                "no_market_action_guidance"
            ],
        },
        "packet_completeness_readiness_gate": {
            "artifact_status": pack["packet_completeness_readiness_gate"]["artifact_status"],
            "artifact_pointer": pack["packet_completeness_readiness_gate"]["artifact_pointer"],
            "artifact_markdown_pointer": pack["packet_completeness_readiness_gate"][
                "artifact_markdown_pointer"
            ],
            "total_markets": pack["packet_completeness_readiness_gate"]["total_markets"],
            "high_count": pack["packet_completeness_readiness_gate"]["high_count"],
            "medium_count": pack["packet_completeness_readiness_gate"]["medium_count"],
            "low_count": pack["packet_completeness_readiness_gate"]["low_count"],
            "blocked_count": pack["packet_completeness_readiness_gate"]["blocked_count"],
            "eligible_for_future_llm_review_count": pack[
                "packet_completeness_readiness_gate"
            ]["eligible_for_future_llm_review_count"],
            "eligible_for_future_openrouter_batch_count": pack[
                "packet_completeness_readiness_gate"
            ]["eligible_for_future_openrouter_batch_count"],
            "needs_local_enrichment_count": pack["packet_completeness_readiness_gate"][
                "needs_local_enrichment_count"
            ],
            "low_readiness_market_ids": pack["packet_completeness_readiness_gate"][
                "low_readiness_market_ids"
            ],
            "unreviewed_market_ids": pack["packet_completeness_readiness_gate"][
                "unreviewed_market_ids"
            ],
            "top_missing_fields": pack["packet_completeness_readiness_gate"][
                "top_missing_fields"
            ],
            "recommended_next_local_enrichment_focus": pack[
                "packet_completeness_readiness_gate"
            ]["recommended_next_local_enrichment_focus"],
            "future_live_batch_scheduled": pack["packet_completeness_readiness_gate"][
                "future_live_batch_scheduled"
            ],
            "future_openrouter_batch_approved": pack[
                "packet_completeness_readiness_gate"
            ]["future_openrouter_batch_approved"],
            "no_market_action_guidance": pack["packet_completeness_readiness_gate"][
                "no_market_action_guidance"
            ],
        },
        "resolution_source_normalization": {
            "audit_artifact_status": pack["resolution_source_normalization"][
                "audit_artifact_status"
            ],
            "audit_artifact_pointer": pack["resolution_source_normalization"][
                "audit_artifact_pointer"
            ],
            "readiness_artifact_pointer": pack["resolution_source_normalization"][
                "readiness_artifact_pointer"
            ],
            "batch_gate_artifact_pointer": pack["resolution_source_normalization"][
                "batch_gate_artifact_pointer"
            ],
            "action_plan_artifact_pointer": pack["resolution_source_normalization"][
                "action_plan_artifact_pointer"
            ],
            "total_markets_audited": pack["resolution_source_normalization"][
                "total_markets_audited"
            ],
            "markets_missing_resolution_criteria_text": pack[
                "resolution_source_normalization"
            ]["markets_missing_resolution_criteria_text"],
            "markets_missing_full_resolution_rules": pack["resolution_source_normalization"][
                "markets_missing_full_resolution_rules"
            ],
            "markets_missing_official_source_references": pack[
                "resolution_source_normalization"
            ]["markets_missing_official_source_references"],
            "previous_readiness_summary": pack["resolution_source_normalization"][
                "previous_readiness_summary"
            ],
            "updated_readiness_summary": pack["resolution_source_normalization"][
                "updated_readiness_summary"
            ],
            "markets_improved_by_source_normalization": pack[
                "resolution_source_normalization"
            ]["markets_improved_by_source_normalization"],
            "future_openrouter_batch_approved": pack["resolution_source_normalization"][
                "future_openrouter_batch_approved"
            ],
            "passive_only": pack["resolution_source_normalization"]["passive_only"],
            "queue_items_created": pack["resolution_source_normalization"][
                "queue_items_created"
            ],
            "queue_state_mutated": pack["resolution_source_normalization"][
                "queue_state_mutated"
            ],
            "no_market_action_guidance": pack["resolution_source_normalization"][
                "no_market_action_guidance"
            ],
        },
        "manual_resolution_source_capture": {
            "guide_pointer": pack["manual_resolution_source_capture"]["guide_pointer"],
            "checklist_pointer": pack["manual_resolution_source_capture"][
                "checklist_pointer"
            ],
            "progress_pointer": pack["manual_resolution_source_capture"][
                "progress_pointer"
            ],
            "schema_pointer": pack["manual_resolution_source_capture"]["schema_pointer"],
            "manifest_pointer": pack["manual_resolution_source_capture"][
                "manifest_pointer"
            ],
            "validation_pointer": pack["manual_resolution_source_capture"][
                "validation_pointer"
            ],
            "total_capture_packets": pack["manual_resolution_source_capture"][
                "total_capture_packets"
            ],
            "total_templates": pack["manual_resolution_source_capture"][
                "total_templates"
            ],
            "capture_status_counts": pack["manual_resolution_source_capture"][
                "capture_status_counts"
            ],
            "packets_created": pack["manual_resolution_source_capture"][
                "packets_created"
            ],
            "packets_not_started": pack["manual_resolution_source_capture"][
                "packets_not_started"
            ],
            "packets_ready_for_local_review": pack[
                "manual_resolution_source_capture"
            ]["packets_ready_for_local_review"],
            "fields_required_for_high_completeness": pack[
                "manual_resolution_source_capture"
            ]["fields_required_for_high_completeness"],
            "recommended_operator_fill_order": pack[
                "manual_resolution_source_capture"
            ]["recommended_operator_fill_order"],
            "validation_command": pack["manual_resolution_source_capture"][
                "validation_command"
            ],
            "next_operator_action": pack["manual_resolution_source_capture"][
                "next_operator_action"
            ],
            "validation_valid_count": pack["manual_resolution_source_capture"][
                "validation_valid_count"
            ],
            "validation_invalid_count": pack["manual_resolution_source_capture"][
                "validation_invalid_count"
            ],
            "no_market_action_guidance": pack["manual_resolution_source_capture"][
                "no_market_action_guidance"
            ],
            "no_trading_authority": pack["manual_resolution_source_capture"][
                "no_trading_authority"
            ],
            "no_queue_authority": pack["manual_resolution_source_capture"][
                "no_queue_authority"
            ],
            "no_runtime_authority": pack["manual_resolution_source_capture"][
                "no_runtime_authority"
            ],
            "no_wallet_or_order_authority": pack["manual_resolution_source_capture"][
                "no_wallet_or_order_authority"
            ],
        },
        "missing_artifacts": pack["missing_artifacts"],
        "warnings_count": len(pack["warnings"]),
        "safety_flags": pack["safety_flags"],
        "paper_orders_created": 0,
        "commands_executed": 0,
        "network_calls": 0,
        "forbidden_changes_detected": False,
        "blockers": blockers,
        "next_action": "ready_for_integration_review" if completed else "requires_operator_review",
    }


def write_operator_review_pack_artifacts():
    openrouter_passive_surface_pointer.write_openrouter_passive_surface_pointer_artifacts()
    operator_openrouter_review_dashboard.write_operator_openrouter_review_dashboard_artifacts()
    pack = build_operator_review_pack()
    result = _result_payload(pack)
    _write_json(DEFAULT_PACK_JSON, pack)
    _write_json(DEFAULT_EXPECTED_PACK_JSON, pack)
    _write_text(DEFAULT_PACK_MD, render_operator_review_pack_markdown(pack))
    _write_json(DEFAULT_RESULT, result)
    _write_json(DEFAULT_LANE_RESULT, result)
    return {
        "task_id": TASK_ID,
        "status": result["status"],
        "files_written": [
            _display_path(DEFAULT_PACK_JSON),
            _display_path(DEFAULT_PACK_MD),
            _display_path(DEFAULT_EXPECTED_PACK_JSON),
            _display_path(DEFAULT_RESULT),
            _display_path(DEFAULT_LANE_RESULT),
        ],
        "present_artifacts": pack["artifact_inventory"]["summary"]["present_artifacts"],
        "missing_artifacts": pack["artifact_inventory"]["summary"]["missing_artifacts"],
        "required_missing_artifacts": pack["artifact_inventory"]["summary"]["required_missing_artifacts"],
        "warnings_count": len(pack["warnings"]),
        "paper_orders_created": 0,
        "commands_executed": 0,
        "network_calls": 0,
    }


def main(argv):
    args = _parse_args(argv)
    if args.write:
        print(json.dumps(write_operator_review_pack_artifacts(), indent=2, ensure_ascii=True))
        return 0
    pack = build_operator_review_pack()
    if args.markdown:
        print(render_operator_review_pack_markdown(pack), end="")
    else:
        print(json.dumps(pack, indent=2, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
