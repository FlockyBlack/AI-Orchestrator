import argparse
import json
import sys
from pathlib import Path


TASK_ID = "PMBOT-WORKBENCH-001-OPERATOR-REVIEW-PACK-EXPORT"
CODEX_LANE = "CODEX_A"
ROOT = Path(__file__).resolve().parents[2]
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

SAFETY_FLAGS = {
    "operator_review_only": True,
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


def _inventory_item(inventory, artifact_id):
    for item in inventory["artifacts"]:
        if item["artifact_id"] == artifact_id:
            return item
    return {}


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
            "warning_categories": _safe_list(summary.get("warning_categories")),
            "top_warning_categories": _safe_list(summary.get("top_warning_categories")),
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
        "warning_categories": [],
        "top_warning_categories": [],
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
    warnings = (
        _warnings(payloads)
        + _paper_019_warnings(paper_019_summary)
        + _paper_020_warnings(paper_020_summary)
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
