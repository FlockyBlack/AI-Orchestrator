import argparse
import json
import sys
from pathlib import Path


TASK_ID = "PMBOT-DASHBOARD-002-PORTFOLIO-AUDIT-STATE-EXPORT"
ROOT = Path(__file__).resolve().parents[2]
DASHBOARD_DIR = ROOT / "pm_bot" / "dashboard"
PAPER_DIR = ROOT / "pm_bot" / "paper"
DOCS_DIR = ROOT / "docs"

DEFAULT_CONTRACT = DASHBOARD_DIR / "portfolio_audit_state_contract.v1.json"
DEFAULT_PREVIEW_JSON = DASHBOARD_DIR / "portfolio_audit_state_preview.v1.json"
DEFAULT_PREVIEW_MD = DASHBOARD_DIR / "portfolio_audit_state_preview.v1.md"
DEFAULT_EXPECTED_PREVIEW_JSON = DASHBOARD_DIR / "expected_portfolio_audit_state_preview.v1.json"

DASHBOARD_001_CONTRACT = DASHBOARD_DIR / "dashboard_state_contract.v1.json"
DASHBOARD_001_PREVIEW_JSON = DASHBOARD_DIR / "dashboard_state_preview.v1.json"
DASHBOARD_001_PREVIEW_MD = DASHBOARD_DIR / "dashboard_state_preview.v1.md"
DASHBOARD_001_RESULT = DOCS_DIR / "PMBOT_DASHBOARD_001_RESULT.json"

PAPER_ACCOUNTING_LEDGER = PAPER_DIR / "paper_accounting_ledger.v1.json"
PAPER_ACCOUNTING_PNL_PREVIEW = PAPER_DIR / "paper_accounting_pnl_preview.v1.json"
PAPER_FILL_EVENTS = PAPER_DIR / "paper_fill_events.v1.json"
MANUAL_PAPER_INTENT_LEDGER = PAPER_DIR / "manual_paper_intent_ledger.v1.json"
PAPER_PORTFOLIO_SNAPSHOT = PAPER_DIR / "paper_portfolio_snapshot.v1.json"
PAPER_METRICS_REPORT = PAPER_DIR / "paper_metrics_report.v1.json"
PAPER_PORTFOLIO_STATE = PAPER_DIR / "paper_portfolio_state.v1.json"
PAPER_PORTFOLIO_STATE_AFTER_INBOX = PAPER_DIR / "paper_portfolio_state_after_inbox.v1.json"
PAPER_PORTFOLIO_STATE_AFTER_SNAPSHOT = PAPER_DIR / "paper_portfolio_state_after_snapshot.v1.json"

PAPER_017_AUDIT = PAPER_DIR / "paper_accounting_reconciliation_audit.v1.json"
PAPER_017_AUDIT_MD = PAPER_DIR / "paper_accounting_reconciliation_audit.v1.md"
PAPER_017_EXPECTED_AUDIT = PAPER_DIR / "expected_paper_accounting_reconciliation_audit.v1.json"
PAPER_017_RESULT = DOCS_DIR / "PMBOT_PAPER_017_RESULT.json"

PAPER_BATCH_011_013_RESULT = DOCS_DIR / "PMBOT_PAPER_BATCH_011_013_RESULT.json"
PAPER_BATCH_014_016_RESULT = DOCS_DIR / "PMBOT_PAPER_BATCH_014_016_RESULT.json"
INTEGRATION_002_RESULT = DOCS_DIR / "PMBOT_INTEGRATION_002_RESULT.json"
INTEGRATION_003_RESULT = DOCS_DIR / "PMBOT_INTEGRATION_003_RESULT.json"
INTEGRATION_006_RESULT = DOCS_DIR / "PMBOT_INTEGRATION_006_RESULT.json"
INFRA_007_RESULT = DOCS_DIR / "PMBOT_INFRA_007_RESULT.json"
INFRA_008_RESULT = DOCS_DIR / "PMBOT_INFRA_008_RESULT.json"
LATEST_STAGE_SUMMARY = DOCS_DIR / "PM_BOT_STAGE_SUMMARY_V55.md"

FUTURE_PAPER_018_RESULT = DOCS_DIR / "PMBOT_PAPER_018_RESULT.json"
FUTURE_BATCH_AUDIT_SUMMARY = PAPER_DIR / "paper_batch_audit_summary.v1.json"
FUTURE_EXPECTED_BATCH_AUDIT_SUMMARY = PAPER_DIR / "expected_paper_batch_audit_summary.v1.json"

PREVIEW_SCHEMA_VERSION = "portfolio_audit_state_preview.v1"
CONTRACT_SCHEMA_VERSION = "portfolio_audit_state_contract.v1"
DASHBOARD_STATE_EXPORT_VERSION = "v2"
GENERATED_BY = "pm_bot/dashboard/export_portfolio_audit_state.py"
NOT_STRATEGY_PROFITABILITY_WARNING = (
    "Paper accounting PnL is fixture/manual accounting only and is not strategy profitability."
)

SAFETY_FLAGS = {
    "dashboard_runtime": False,
    "server": False,
    "frontend": False,
    "browser_automation": False,
    "runtime_wiring": False,
    "network_api": False,
    "authenticated_data": False,
    "credentials": False,
    "wallet": False,
    "trading": False,
    "real_orders": False,
    "live_trading": False,
    "autonomous_paper_orders": False,
    "scoring_probability_ev_edge": False,
    "truth_inference": False,
    "recommendations": False,
    "market_decisions": False,
}

FORBIDDEN_CAPABILITIES = [
    "dashboard server or hosted runtime",
    "frontend application or browser automation",
    "network/API calls or live fetch results",
    "authenticated endpoints or authenticated data",
    "credentials, API keys, wallet access, private keys, or signing",
    "trading endpoints, real orders, live trading, or autonomous paper orders",
    "betting recommendations or market side recommendations",
    "probability estimates, EV calculations, edge calculations, or market scoring",
    "truth inference, live resolution, or market decisions",
    "dispatcher, run_codex, prompt automation, or runtime wiring changes",
]


def _parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Export deterministic local PMBOT portfolio/accounting/audit dashboard state artifacts."
    )
    parser.add_argument("--write", action="store_true", help="Write contract, preview JSON, Markdown, and fixture.")
    parser.add_argument("--markdown", action="store_true", help="Print the Markdown preview.")
    parser.add_argument("--contract", action="store_true", help="Print the JSON contract instead of the preview.")
    return parser.parse_args(argv)


def _display_path(path):
    resolved = Path(path).resolve()
    try:
        return str(resolved.relative_to(ROOT.resolve())).replace("\\", "/")
    except ValueError:
        return str(resolved).replace("\\", "/")


def _load_json(path):
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _load_json_if_present(path):
    if not Path(path).exists():
        return None
    return _load_json(path)


def _write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def _write_text(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _artifact_pointer(path, artifact_type, required=True):
    return {
        "path": _display_path(path),
        "artifact_type": artifact_type,
        "required": required,
        "present": Path(path).exists(),
    }


def _doc_status(path, payload):
    if payload is None:
        return {
            "source_path": _display_path(path),
            "present": False,
            "task_id": None,
            "status": "not_available",
        }
    return {
        "source_path": _display_path(path),
        "present": True,
        "task_id": payload.get("task_id"),
        "status": payload.get("status"),
        "integration_verdict": payload.get("integration_verdict"),
    }


def _parse_stage_summary(path=LATEST_STAGE_SUMMARY):
    if not Path(path).exists():
        return {
            "source_path": _display_path(path),
            "present": False,
            "task": None,
            "status": "not_available",
        }
    task = None
    status = None
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.startswith("Task: "):
            task = line.removeprefix("Task: ").strip()
        elif line.startswith("Status: "):
            status = line.removeprefix("Status: ").strip()
    return {
        "source_path": _display_path(path),
        "present": True,
        "task": task,
        "status": status,
    }


def _market_ids_from_payload(value):
    if isinstance(value, dict):
        for key, nested in value.items():
            if key == "market_ids" and isinstance(nested, list):
                for market_id in nested:
                    if isinstance(market_id, (str, int)):
                        yield str(market_id)
            elif key == "market_id" and isinstance(nested, (str, int)):
                yield str(nested)
            else:
                yield from _market_ids_from_payload(nested)
    elif isinstance(value, list):
        for item in value:
            yield from _market_ids_from_payload(item)


def _counts(payload):
    counts = payload.get("counts")
    if isinstance(counts, dict):
        return counts
    return {}


def _count(payload, key):
    value = _counts(payload).get(key)
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    return None


def _market_ids_from_artifact_summaries(audit):
    market_ids = set()
    if not isinstance(audit, dict):
        return []
    for item in audit.get("artifacts_checked", []):
        if not isinstance(item, dict):
            continue
        for market_id in item.get("market_ids", []):
            if isinstance(market_id, (str, int)):
                market_ids.add(str(market_id))
    return sorted(market_ids)


def _paper_state_summary(path, payload):
    if payload is None:
        return {
            "source_path": _display_path(path),
            "present": False,
            "state_id": None,
            "position_count": 0,
            "exposure_summary": {},
            "safety_flags": {},
        }
    positions = payload.get("paper_positions", [])
    if not isinstance(positions, list):
        positions = []
    exposure = payload.get("exposure_summary")
    if not isinstance(exposure, dict):
        exposure = {}
    return {
        "source_path": _display_path(path),
        "present": True,
        "state_id": payload.get("state_id"),
        "fixture_only": payload.get("fixture_only"),
        "paper_only": payload.get("paper_only"),
        "position_count": len(positions),
        "exposure_summary": {
            "open_positions": exposure.get("open_positions"),
            "settled_positions": exposure.get("settled_positions"),
            "total_paper_notional": exposure.get("total_paper_notional"),
            "open_paper_notional": exposure.get("open_paper_notional"),
            "realized_paper_pnl": exposure.get("realized_paper_pnl"),
            "unrealized_paper_pnl": exposure.get("unrealized_paper_pnl"),
        },
        "safety_flags": {
            "offline_only": payload.get("offline_only"),
            "paper_only": payload.get("paper_only"),
            "live_fetcher_implemented": payload.get("live_fetcher_implemented"),
            "execution_allowed": payload.get("execution_allowed"),
            "trading_allowed": payload.get("trading_allowed"),
            "real_order_created": payload.get("real_order_created"),
            "wallet_used": payload.get("wallet_used"),
            "api_used": payload.get("api_used"),
            "network_used": payload.get("network_used"),
        },
    }


def _audit_summary_existing(paper_017_result, paper_017_audit):
    if paper_017_result is None and paper_017_audit is None:
        return {
            "present": False,
            "source_result_path": _display_path(PAPER_017_RESULT),
            "source_audit_path": _display_path(PAPER_017_AUDIT),
            "task_id": None,
            "status": None,
            "audit_status": None,
            "market_id": None,
            "counts": {
                "artifacts_checked": 0,
                "checks_total": 0,
                "checks_passed": 0,
                "checks_warning": 0,
                "checks_failed": 0,
            },
            "audit_artifact_market_ids": [],
            "mismatches_count": 0,
            "warnings_count": 0,
            "paper_orders_created": 0,
            "autonomous_actions_created": 0,
            "next_action": "not_available",
        }

    result_counts = {}
    if isinstance(paper_017_result, dict) and isinstance(paper_017_result.get("counts"), dict):
        result_counts = paper_017_result["counts"]
    checks = paper_017_audit.get("checks", []) if isinstance(paper_017_audit, dict) else []
    if not isinstance(checks, list):
        checks = []
    mismatches = paper_017_audit.get("mismatches", []) if isinstance(paper_017_audit, dict) else []
    warnings = paper_017_audit.get("warnings", []) if isinstance(paper_017_audit, dict) else []
    if not isinstance(mismatches, list):
        mismatches = []
    if not isinstance(warnings, list):
        warnings = []

    return {
        "present": True,
        "source_result_path": _display_path(PAPER_017_RESULT),
        "source_audit_path": _display_path(PAPER_017_AUDIT),
        "task_id": paper_017_result.get("task_id") if isinstance(paper_017_result, dict) else paper_017_audit.get("task_id"),
        "status": paper_017_result.get("status") if isinstance(paper_017_result, dict) else None,
        "audit_status": paper_017_audit.get("audit_status") if isinstance(paper_017_audit, dict) else paper_017_result.get("audit_status"),
        "market_id": paper_017_audit.get("market_id") if isinstance(paper_017_audit, dict) else paper_017_result.get("market_id"),
        "counts": {
            "artifacts_checked": result_counts.get("artifacts_checked", len(paper_017_audit.get("artifacts_checked", []))),
            "checks_total": result_counts.get("checks_total", len(checks)),
            "checks_passed": result_counts.get(
                "checks_passed",
                sum(1 for check in checks if isinstance(check, dict) and check.get("status") == "pass"),
            ),
            "checks_warning": result_counts.get(
                "checks_warning",
                sum(1 for check in checks if isinstance(check, dict) and check.get("status") == "warning"),
            ),
            "checks_failed": result_counts.get(
                "checks_failed",
                sum(1 for check in checks if isinstance(check, dict) and check.get("status") == "fail"),
            ),
        },
        "audit_artifact_market_ids": _market_ids_from_artifact_summaries(paper_017_audit),
        "mismatches_count": len(mismatches),
        "warnings_count": len(warnings),
        "paper_orders_created": paper_017_audit.get("paper_orders_created", result_counts.get("paper_orders_created")),
        "autonomous_actions_created": paper_017_audit.get(
            "autonomous_actions_created", result_counts.get("autonomous_actions_created")
        ),
        "next_action": paper_017_result.get("next_action") if isinstance(paper_017_result, dict) else paper_017_audit.get("next_safe_action"),
    }


def _future_batch_audit_placeholder():
    optional_paths = [
        FUTURE_PAPER_018_RESULT,
        FUTURE_BATCH_AUDIT_SUMMARY,
        FUTURE_EXPECTED_BATCH_AUDIT_SUMMARY,
    ]
    return {
        "schema_version": "future_batch_audit_placeholder.v1",
        "paper_018_required": False,
        "paper_018_present": FUTURE_PAPER_018_RESULT.exists(),
        "source_paths": [_display_path(path) for path in optional_paths],
        "batch_audit_status": None,
        "batch_ids": [],
        "batch_audit_summary": {},
        "warnings": [],
        "integration_required_before_use": True,
    }


def _artifact_pointers():
    return {
        "portfolio_audit_contract": _artifact_pointer(DEFAULT_CONTRACT, "json_contract"),
        "portfolio_audit_preview_json": _artifact_pointer(DEFAULT_PREVIEW_JSON, "json_preview"),
        "portfolio_audit_preview_markdown": _artifact_pointer(DEFAULT_PREVIEW_MD, "markdown_preview"),
        "portfolio_audit_expected_preview_json": _artifact_pointer(DEFAULT_EXPECTED_PREVIEW_JSON, "json_expected_fixture"),
        "dashboard_001_contract": _artifact_pointer(DASHBOARD_001_CONTRACT, "json_contract"),
        "dashboard_001_preview_json": _artifact_pointer(DASHBOARD_001_PREVIEW_JSON, "json_preview"),
        "dashboard_001_preview_markdown": _artifact_pointer(DASHBOARD_001_PREVIEW_MD, "markdown_preview"),
        "paper_accounting_ledger_json": _artifact_pointer(PAPER_ACCOUNTING_LEDGER, "paper_accounting_json"),
        "paper_accounting_pnl_preview_json": _artifact_pointer(PAPER_ACCOUNTING_PNL_PREVIEW, "paper_accounting_json"),
        "paper_fill_events_json": _artifact_pointer(PAPER_FILL_EVENTS, "paper_fill_json"),
        "manual_paper_intent_ledger_json": _artifact_pointer(MANUAL_PAPER_INTENT_LEDGER, "paper_manual_fixture_json"),
        "paper_portfolio_snapshot_json": _artifact_pointer(PAPER_PORTFOLIO_SNAPSHOT, "paper_portfolio_json"),
        "paper_metrics_report_json": _artifact_pointer(PAPER_METRICS_REPORT, "paper_metrics_json"),
        "paper_portfolio_state_json": _artifact_pointer(PAPER_PORTFOLIO_STATE, "paper_portfolio_json", required=False),
        "paper_portfolio_state_after_inbox_json": _artifact_pointer(
            PAPER_PORTFOLIO_STATE_AFTER_INBOX, "paper_portfolio_json", required=False
        ),
        "paper_portfolio_state_after_snapshot_json": _artifact_pointer(
            PAPER_PORTFOLIO_STATE_AFTER_SNAPSHOT, "paper_portfolio_json", required=False
        ),
        "paper_017_reconciliation_audit_json": _artifact_pointer(PAPER_017_AUDIT, "paper_audit_json", required=False),
        "paper_017_reconciliation_audit_markdown": _artifact_pointer(PAPER_017_AUDIT_MD, "paper_audit_markdown", required=False),
        "paper_017_expected_reconciliation_audit_json": _artifact_pointer(
            PAPER_017_EXPECTED_AUDIT, "json_expected_fixture", required=False
        ),
        "paper_017_result": _artifact_pointer(PAPER_017_RESULT, "docs_result_json", required=False),
        "paper_batch_011_013_result": _artifact_pointer(PAPER_BATCH_011_013_RESULT, "docs_result_json"),
        "paper_batch_014_016_result": _artifact_pointer(PAPER_BATCH_014_016_RESULT, "docs_result_json"),
        "integration_002_result": _artifact_pointer(INTEGRATION_002_RESULT, "docs_result_json"),
        "integration_003_result": _artifact_pointer(INTEGRATION_003_RESULT, "docs_result_json"),
        "integration_006_result": _artifact_pointer(INTEGRATION_006_RESULT, "docs_result_json", required=False),
        "infra_007_result": _artifact_pointer(INFRA_007_RESULT, "docs_result_json", required=False),
        "infra_008_result": _artifact_pointer(INFRA_008_RESULT, "docs_result_json", required=False),
        "dashboard_001_result": _artifact_pointer(DASHBOARD_001_RESULT, "docs_result_json", required=False),
        "latest_stage_summary": _artifact_pointer(LATEST_STAGE_SUMMARY, "docs_markdown", required=False),
        "future_paper_018_result": _artifact_pointer(FUTURE_PAPER_018_RESULT, "future_optional_docs_result_json", required=False),
        "future_batch_audit_summary_json": _artifact_pointer(
            FUTURE_BATCH_AUDIT_SUMMARY, "future_optional_paper_audit_json", required=False
        ),
    }


def build_portfolio_audit_state_contract():
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "PMBOT_PORTFOLIO_AUDIT_STATE_CONTRACT.v1",
        "title": "PMBOT Portfolio Audit Dashboard State Contract v1",
        "description": (
            "Schema-like local contract for dashboard state export v2 focused on "
            "portfolio, accounting, and audit state. The contract defines static "
            "local artifacts only and no dashboard runtime."
        ),
        "type": "object",
        "additionalProperties": False,
        "required": [
            "schema_version",
            "dashboard_state_export_version",
            "generated_by",
            "generated_at_policy",
            "product_stage_summary",
            "portfolio_accounting_summary",
            "known_market_ids",
            "artifact_pointers",
            "audit_summary_existing",
            "future_batch_audit_placeholder",
            "safety_flags",
            "forbidden_capabilities",
            "interpretation_warnings",
            "operator_next_actions",
        ],
        "properties": {
            "schema_version": {"const": PREVIEW_SCHEMA_VERSION},
            "dashboard_state_export_version": {"const": DASHBOARD_STATE_EXPORT_VERSION},
            "generated_by": {"const": GENERATED_BY},
            "generated_at_policy": {
                "type": "object",
                "required": ["wall_clock_time_used", "policy", "fixed_value"],
                "properties": {
                    "wall_clock_time_used": {"const": False},
                    "policy": {"type": "string"},
                    "fixed_value": {"type": "string"},
                },
            },
            "product_stage_summary": {"type": "object"},
            "portfolio_accounting_summary": {"type": "object"},
            "known_market_ids": {"type": "array", "items": {"type": "string"}},
            "artifact_pointers": {"type": "object"},
            "audit_summary_existing": {"type": "object"},
            "future_batch_audit_placeholder": {"type": "object"},
            "safety_flags": {"type": "object"},
            "forbidden_capabilities": {"type": "array", "items": {"type": "string"}},
            "interpretation_warnings": {"type": "array", "items": {"type": "string"}},
            "operator_next_actions": {"type": "array", "items": {"type": "object"}},
        },
        "contract_boundary": {
            "local_file_reads_only": True,
            "deterministic_output": True,
            "stable_ordering": True,
            "dashboard_runtime_defined": False,
            "server_defined": False,
            "frontend_defined": False,
            "browser_automation_defined": False,
            "network_or_api_defined": False,
            "wallet_or_auth_defined": False,
            "trading_or_ordering_defined": False,
            "autonomous_paper_ordering_defined": False,
            "scoring_probability_ev_edge_defined": False,
            "truth_inference_or_market_decision_defined": False,
        },
        "source_artifact_requirements": [
            _display_path(PAPER_ACCOUNTING_LEDGER),
            _display_path(PAPER_ACCOUNTING_PNL_PREVIEW),
            _display_path(PAPER_PORTFOLIO_SNAPSHOT),
            _display_path(PAPER_METRICS_REPORT),
            _display_path(PAPER_017_AUDIT),
            _display_path(PAPER_017_RESULT),
        ],
        "optional_future_artifacts": [
            _display_path(FUTURE_PAPER_018_RESULT),
            _display_path(FUTURE_BATCH_AUDIT_SUMMARY),
            _display_path(FUTURE_EXPECTED_BATCH_AUDIT_SUMMARY),
        ],
    }


def build_portfolio_audit_state_preview():
    accounting_ledger = _load_json(PAPER_ACCOUNTING_LEDGER)
    pnl_preview = _load_json(PAPER_ACCOUNTING_PNL_PREVIEW)
    portfolio_snapshot = _load_json(PAPER_PORTFOLIO_SNAPSHOT)
    metrics_report = _load_json(PAPER_METRICS_REPORT)

    dashboard_001_result = _load_json_if_present(DASHBOARD_001_RESULT)
    paper_017_result = _load_json_if_present(PAPER_017_RESULT)
    paper_017_audit = _load_json_if_present(PAPER_017_AUDIT)
    paper_batch_011_013 = _load_json_if_present(PAPER_BATCH_011_013_RESULT)
    paper_batch_014_016 = _load_json_if_present(PAPER_BATCH_014_016_RESULT)
    integration_002 = _load_json_if_present(INTEGRATION_002_RESULT)
    integration_003 = _load_json_if_present(INTEGRATION_003_RESULT)
    integration_006 = _load_json_if_present(INTEGRATION_006_RESULT)
    infra_007 = _load_json_if_present(INFRA_007_RESULT)
    infra_008 = _load_json_if_present(INFRA_008_RESULT)

    paper_portfolio_state = _load_json_if_present(PAPER_PORTFOLIO_STATE)
    paper_portfolio_state_after_inbox = _load_json_if_present(PAPER_PORTFOLIO_STATE_AFTER_INBOX)
    paper_portfolio_state_after_snapshot = _load_json_if_present(PAPER_PORTFOLIO_STATE_AFTER_SNAPSHOT)

    known_market_ids = sorted(
        set(_market_ids_from_payload(accounting_ledger))
        | set(_market_ids_from_payload(pnl_preview))
        | set(_market_ids_from_payload(portfolio_snapshot))
        | set(_market_ids_from_payload(metrics_report))
        | set(_market_ids_from_payload(paper_portfolio_state or {}))
        | set(_market_ids_from_payload(paper_portfolio_state_after_inbox or {}))
        | set(_market_ids_from_payload(paper_portfolio_state_after_snapshot or {}))
    )

    metrics = metrics_report.get("paper_accounting_metrics", {})
    return {
        "schema_version": PREVIEW_SCHEMA_VERSION,
        "dashboard_state_export_version": DASHBOARD_STATE_EXPORT_VERSION,
        "generated_by": GENERATED_BY,
        "generated_at_policy": {
            "wall_clock_time_used": False,
            "policy": "deterministic_static_snapshot_no_current_time",
            "fixed_value": "not_emitted",
        },
        "product_stage_summary": {
            "dashboard_scope": TASK_ID,
            "dashboard_001": _doc_status(DASHBOARD_001_RESULT, dashboard_001_result),
            "paper_017": _doc_status(PAPER_017_RESULT, paper_017_result),
            "paper_batch_011_013": _doc_status(PAPER_BATCH_011_013_RESULT, paper_batch_011_013),
            "paper_batch_014_016": _doc_status(PAPER_BATCH_014_016_RESULT, paper_batch_014_016),
            "integration_002": _doc_status(INTEGRATION_002_RESULT, integration_002),
            "integration_003": _doc_status(INTEGRATION_003_RESULT, integration_003),
            "integration_006": _doc_status(INTEGRATION_006_RESULT, integration_006),
            "infra_007": _doc_status(INFRA_007_RESULT, infra_007),
            "infra_008": _doc_status(INFRA_008_RESULT, infra_008),
            "latest_overall_stage": _parse_stage_summary(),
            "current_known_portfolio_audit_status": "paper_017_reconciliation_available_with_dashboard_002_static_export",
            "implementation_boundary": {
                "dashboard_runtime": False,
                "server": False,
                "frontend": False,
                "network_api": False,
                "runtime_wiring": False,
            },
        },
        "portfolio_accounting_summary": {
            "summary_status": "portfolio_accounting_state_ready",
            "accepted_accounting_market_ids": sorted(set(_market_ids_from_payload(metrics_report))),
            "source_artifact_status": {
                "paper_accounting_ledger_status": accounting_ledger.get("paper_accounting_ledger_status"),
                "paper_accounting_pnl_preview_schema": pnl_preview.get("schema_version"),
                "paper_portfolio_snapshot_status": portfolio_snapshot.get("paper_portfolio_status"),
                "paper_metrics_report_status": metrics_report.get("paper_metrics_report_status"),
            },
            "counts": {
                "paper_accounting_preview_records_read": _count(accounting_ledger, "paper_accounting_preview_records_read"),
                "paper_accounting_ledger_entries": _count(accounting_ledger, "paper_accounting_ledger_entries"),
                "paper_accounting_settled_count": _count(accounting_ledger, "paper_accounting_settled_count"),
                "paper_accounting_open_count": _count(accounting_ledger, "paper_accounting_open_count"),
                "paper_accounting_blocked_count": _count(accounting_ledger, "paper_accounting_blocked_count"),
                "paper_portfolio_snapshot_records": _count(portfolio_snapshot, "paper_portfolio_snapshot_records"),
                "paper_metrics_report_records": _count(metrics_report, "paper_metrics_report_records"),
                "real_orders_created": 0,
                "live_orders_created": 0,
                "autonomous_paper_orders_created": 0,
            },
            "paper_accounting_totals": pnl_preview.get("paper_accounting_totals", {}),
            "paper_accounting_metrics": {
                "paper_accounting_total_records": metrics.get("paper_accounting_total_records"),
                "paper_accounting_settled_count": metrics.get("paper_accounting_settled_count"),
                "paper_accounting_open_count": metrics.get("paper_accounting_open_count"),
                "paper_accounting_win_count": metrics.get("paper_accounting_win_count"),
                "paper_accounting_loss_count": metrics.get("paper_accounting_loss_count"),
                "paper_accounting_flat_count": metrics.get("paper_accounting_flat_count"),
                "paper_accounting_cumulative_pnl": metrics.get("paper_accounting_cumulative_pnl"),
                "paper_accounting_average_pnl": metrics.get("paper_accounting_average_pnl"),
                "paper_accounting_gross_profit": metrics.get("paper_accounting_gross_profit"),
                "paper_accounting_gross_loss": metrics.get("paper_accounting_gross_loss"),
                "paper_accounting_max_gain": metrics.get("paper_accounting_max_gain"),
                "paper_accounting_max_loss": metrics.get("paper_accounting_max_loss"),
            },
            "latest_portfolio_snapshot": {
                "paper_accounting_position_count": portfolio_snapshot.get("paper_accounting_position_count"),
                "paper_accounting_settled_count": portfolio_snapshot.get("paper_accounting_settled_count"),
                "paper_accounting_open_count": portfolio_snapshot.get("paper_accounting_open_count"),
                "paper_accounting_cumulative_pnl": portfolio_snapshot.get("paper_accounting_cumulative_pnl"),
                "paper_accounting_gross_profit": portfolio_snapshot.get("paper_accounting_gross_profit"),
                "paper_accounting_gross_loss": portfolio_snapshot.get("paper_accounting_gross_loss"),
            },
            "fixture_portfolio_state_summary": [
                _paper_state_summary(PAPER_PORTFOLIO_STATE, paper_portfolio_state),
                _paper_state_summary(PAPER_PORTFOLIO_STATE_AFTER_INBOX, paper_portfolio_state_after_inbox),
                _paper_state_summary(PAPER_PORTFOLIO_STATE_AFTER_SNAPSHOT, paper_portfolio_state_after_snapshot),
            ],
            "accounting_boundary": {
                "paper_accounting_only": True,
                "operator_manual_fixture_source": True,
                "strategy_profitability": False,
                "live_resolution": False,
                "warning": NOT_STRATEGY_PROFITABILITY_WARNING,
            },
        },
        "known_market_ids": known_market_ids,
        "artifact_pointers": _artifact_pointers(),
        "audit_summary_existing": _audit_summary_existing(paper_017_result, paper_017_audit),
        "future_batch_audit_placeholder": _future_batch_audit_placeholder(),
        "safety_flags": SAFETY_FLAGS,
        "forbidden_capabilities": FORBIDDEN_CAPABILITIES,
        "interpretation_warnings": [
            NOT_STRATEGY_PROFITABILITY_WARNING,
            "Audit pass/fail state reflects deterministic local artifact consistency only, not truth inference.",
            "This snapshot does not recommend a side, size, price, market, or trade.",
            "This snapshot does not contain probability estimates, EV, edge, market scoring, live prices, or live fetch results.",
            "This snapshot reads local artifacts only and does not create executable orders or autonomous paper orders.",
            "Future batch audit fields are placeholders unless their optional local artifacts are present and integration-reviewed.",
        ],
        "operator_next_actions": [
            {
                "action_id": "review_portfolio_audit_state_contract",
                "description": "Review the static JSON and Markdown portfolio/audit dashboard state artifacts.",
                "non_trading_action": True,
                "requires_runtime": False,
            },
            {
                "action_id": "run_focused_dashboard_and_paper_tests",
                "description": "Run local dashboard and paper test suites before integration review.",
                "non_trading_action": True,
                "requires_runtime": False,
            },
            {
                "action_id": "integration_review_only",
                "description": "Use this export as a reviewed static contract input for future dashboard work.",
                "non_trading_action": True,
                "requires_runtime": False,
            },
        ],
    }


def render_portfolio_audit_state_markdown(preview_payload):
    accounting = preview_payload["portfolio_accounting_summary"]
    metrics = accounting["paper_accounting_metrics"]
    audit = preview_payload["audit_summary_existing"]
    pointers = preview_payload["artifact_pointers"]
    placeholder = preview_payload["future_batch_audit_placeholder"]
    product = preview_payload["product_stage_summary"]
    lines = [
        "# PMBOT Portfolio Audit State Preview v1",
        "",
        f"- schema_version: {preview_payload['schema_version']}",
        f"- dashboard_state_export_version: {preview_payload['dashboard_state_export_version']}",
        f"- generated_by: {preview_payload['generated_by']}",
        f"- generated_at_policy: {preview_payload['generated_at_policy']['policy']}",
        f"- known_market_ids: {', '.join(preview_payload['known_market_ids'])}",
        "",
        "## Product Stage",
        "",
        f"- dashboard_scope: {product['dashboard_scope']}",
        f"- dashboard_001_status: {product['dashboard_001']['status']}",
        f"- paper_017_status: {product['paper_017']['status']}",
        f"- integration_006_verdict: {product['integration_006']['integration_verdict']}",
        f"- infra_008_present: {str(product['infra_008']['present']).lower()}",
        f"- current_known_portfolio_audit_status: {product['current_known_portfolio_audit_status']}",
        "",
        "## Portfolio Accounting Summary",
        "",
        f"- summary_status: {accounting['summary_status']}",
        f"- accepted_accounting_market_ids: {', '.join(accounting['accepted_accounting_market_ids'])}",
        f"- paper_accounting_ledger_entries: {accounting['counts']['paper_accounting_ledger_entries']}",
        f"- paper_accounting_settled_count: {accounting['counts']['paper_accounting_settled_count']}",
        f"- paper_accounting_open_count: {accounting['counts']['paper_accounting_open_count']}",
        f"- paper_portfolio_snapshot_records: {accounting['counts']['paper_portfolio_snapshot_records']}",
        f"- paper_metrics_report_records: {accounting['counts']['paper_metrics_report_records']}",
        f"- paper_accounting_cumulative_pnl: {metrics['paper_accounting_cumulative_pnl']}",
        f"- paper_accounting_gross_profit: {metrics['paper_accounting_gross_profit']}",
        f"- paper_accounting_gross_loss: {metrics['paper_accounting_gross_loss']}",
        "",
        "## Existing Audit Summary",
        "",
        f"- present: {str(audit['present']).lower()}",
        f"- audit_status: {audit['audit_status']}",
        f"- checks_total: {audit['counts']['checks_total']}",
        f"- checks_passed: {audit['counts']['checks_passed']}",
        f"- checks_failed: {audit['counts']['checks_failed']}",
        f"- mismatches_count: {audit['mismatches_count']}",
        f"- warnings_count: {audit['warnings_count']}",
        "",
        "## Future Batch Audit Placeholder",
        "",
        f"- paper_018_required: {str(placeholder['paper_018_required']).lower()}",
        f"- paper_018_present: {str(placeholder['paper_018_present']).lower()}",
        f"- batch_audit_status: {placeholder['batch_audit_status']}",
        f"- batch_ids: {', '.join(placeholder['batch_ids']) if placeholder['batch_ids'] else '(none)'}",
        "",
        "## Artifact Pointers",
        "",
    ]
    for key in sorted(pointers):
        pointer = pointers[key]
        lines.append(f"- {key}: {pointer['path']} (present={str(pointer['present']).lower()})")
    lines.extend(
        [
            "",
            "## Safety",
            "",
        ]
    )
    for key in sorted(preview_payload["safety_flags"]):
        lines.append(f"- {key}: {str(preview_payload['safety_flags'][key]).lower()}")
    lines.extend(
        [
            "",
            "## Interpretation Warnings",
            "",
        ]
    )
    for warning in preview_payload["interpretation_warnings"]:
        lines.append(f"- {warning}")
    lines.append("")
    return "\n".join(lines)


def write_portfolio_audit_state_artifacts():
    contract = build_portfolio_audit_state_contract()
    _write_json(DEFAULT_CONTRACT, contract)

    # Write twice so self-referential artifact pointers are true in fresh checkouts.
    preview = build_portfolio_audit_state_preview()
    _write_json(DEFAULT_PREVIEW_JSON, preview)
    _write_json(DEFAULT_EXPECTED_PREVIEW_JSON, preview)
    _write_text(DEFAULT_PREVIEW_MD, render_portfolio_audit_state_markdown(preview))

    preview = build_portfolio_audit_state_preview()
    _write_json(DEFAULT_PREVIEW_JSON, preview)
    _write_json(DEFAULT_EXPECTED_PREVIEW_JSON, preview)
    _write_text(DEFAULT_PREVIEW_MD, render_portfolio_audit_state_markdown(preview))
    return {
        "task_id": TASK_ID,
        "status": "portfolio_audit_state_exported",
        "files_written": [
            _display_path(DEFAULT_CONTRACT),
            _display_path(DEFAULT_PREVIEW_JSON),
            _display_path(DEFAULT_PREVIEW_MD),
            _display_path(DEFAULT_EXPECTED_PREVIEW_JSON),
        ],
        "known_market_ids": preview["known_market_ids"],
        "audit_status": preview["audit_summary_existing"]["audit_status"],
        "future_batch_audit_present": preview["future_batch_audit_placeholder"]["paper_018_present"],
        "safety_flags": SAFETY_FLAGS,
    }


def main(argv):
    args = _parse_args(argv)
    if args.write:
        print(json.dumps(write_portfolio_audit_state_artifacts(), indent=2, ensure_ascii=True))
        return 0
    if args.contract:
        print(json.dumps(build_portfolio_audit_state_contract(), indent=2, ensure_ascii=True))
        return 0
    preview = build_portfolio_audit_state_preview()
    if args.markdown:
        print(render_portfolio_audit_state_markdown(preview), end="")
    else:
        print(json.dumps(preview, indent=2, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
