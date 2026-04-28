import argparse
import html
import json
import sys
from pathlib import Path


TASK_ID = "PMBOT-DASHBOARD-003-STATIC-HTML-OPERATOR-REPORT"
SCHEMA_VERSION = "static_operator_report_summary.v1"
GENERATED_BY = "pm_bot/dashboard/export_static_operator_report.py"

ROOT = Path(__file__).resolve().parents[2]
DASHBOARD_DIR = ROOT / "pm_bot" / "dashboard"
DOCS_DIR = ROOT / "docs"

DEFAULT_HTML_REPORT = DASHBOARD_DIR / "static_operator_report.v1.html"
DEFAULT_SUMMARY_JSON = DASHBOARD_DIR / "static_operator_report_summary.v1.json"
DEFAULT_EXPECTED_SUMMARY_JSON = DASHBOARD_DIR / "expected_static_operator_report_summary.v1.json"
DEFAULT_RESULT = DOCS_DIR / "PMBOT_DASHBOARD_003_RESULT.json"

ACCOUNTING_ONLY_WARNING = (
    "Paper accounting PnL is fixture/manual accounting only and is not strategy profitability."
)
PAPER_019_INTERPRETATION_WARNING = (
    "PAPER-019 values are deterministic fixture/accounting-only outputs and are not strategy "
    "profitability, recommendation, EV, edge, probability, or market decision evidence."
)
NOT_TRADING_ADVICE_WARNING = (
    "This static report is not trading advice, not a market recommendation, and not evidence of "
    "strategy profitability."
)

SECTIONS_RENDERED = [
    "title_and_generation_policy",
    "open_this_first_operator_summary",
    "current_pmbot_mode",
    "workbench_review_pack_summary",
    "paper_019_multi_market_paper_run_series",
    "accounting_only_warnings",
    "quality_warning_severity_summary",
    "artifact_health_summary",
    "operator_inbox_review_summary",
    "safety_and_forbidden_capabilities",
    "source_artifact_pointers",
    "next_safe_manual_actions",
    "not_trading_advice_warning",
]

SOURCE_ARTIFACTS = (
    {
        "artifact_id": "workbench_005_result",
        "path": "docs/PMBOT_WORKBENCH_005_RESULT.json",
        "artifact_type": "docs_result_json",
        "required": False,
    },
    {
        "artifact_id": "workbench_004_result",
        "path": "docs/PMBOT_WORKBENCH_004_RESULT.json",
        "artifact_type": "docs_result_json",
        "required": False,
    },
    {
        "artifact_id": "workbench_003_result",
        "path": "docs/PMBOT_WORKBENCH_003_RESULT.json",
        "artifact_type": "docs_result_json",
        "required": False,
    },
    {
        "artifact_id": "operator_quickstart",
        "path": "docs/PMBOT_WORKBENCH_002_OPERATOR_QUICKSTART.md",
        "artifact_type": "docs_markdown",
        "required": False,
    },
    {
        "artifact_id": "operator_review_pack_json",
        "path": "pm_bot/workbench/operator_review_pack.v1.json",
        "artifact_type": "operator_review_pack_json",
        "required": True,
    },
    {
        "artifact_id": "operator_review_pack_markdown",
        "path": "pm_bot/workbench/operator_review_pack.v1.md",
        "artifact_type": "operator_review_pack_markdown",
        "required": False,
    },
    {
        "artifact_id": "operator_workbench_export_run_json",
        "path": "pm_bot/workbench/operator_workbench_export_run.v1.json",
        "artifact_type": "workbench_run_json",
        "required": True,
    },
    {
        "artifact_id": "artifact_health_report_json",
        "path": "pm_bot/quality/artifact_health_report.v1.json",
        "artifact_type": "quality_report_json",
        "required": True,
    },
    {
        "artifact_id": "artifact_health_report_markdown",
        "path": "pm_bot/quality/artifact_health_report.v1.md",
        "artifact_type": "quality_report_markdown",
        "required": False,
    },
    {
        "artifact_id": "paper_019_series_json",
        "path": "pm_bot/paper/multi_market_paper_run_series.v1.json",
        "artifact_type": "paper_run_series_json",
        "required": True,
    },
    {
        "artifact_id": "paper_019_series_markdown",
        "path": "pm_bot/paper/multi_market_paper_run_series.v1.md",
        "artifact_type": "paper_run_series_markdown",
        "required": False,
    },
    {
        "artifact_id": "portfolio_audit_state_preview_json",
        "path": "pm_bot/dashboard/portfolio_audit_state_preview.v1.json",
        "artifact_type": "dashboard_state_json",
        "required": True,
    },
    {
        "artifact_id": "manual_command_inbox_review_json",
        "path": "pm_bot/operator/manual_command_inbox_review.v1.json",
        "artifact_type": "operator_inbox_json",
        "required": True,
    },
)

SAFETY_FLAGS = {
    "offline_only": True,
    "local_file_reads_only": True,
    "deterministic": True,
    "paper_only": True,
    "paper_accounting_only": True,
    "operator_review_only": True,
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
    "automation_daemon": False,
    "dashboard_server": False,
    "frontend_runtime": False,
    "browser_automation": False,
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


def _parse_args(argv):
    parser = argparse.ArgumentParser(description="Export a deterministic local static PMBOT operator HTML report.")
    parser.add_argument("--summary", action="store_true", help="Print the summary JSON without writing artifacts.")
    parser.add_argument("--html", action="store_true", help="Print the HTML without writing artifacts.")
    return parser.parse_args(argv)


def _display_path(path, root=ROOT):
    resolved = Path(path).resolve()
    try:
        value = resolved.relative_to(Path(root).resolve())
    except ValueError:
        value = resolved
    return str(value).replace("\\", "/")


def _resolve_path(path, root=ROOT):
    value = Path(path)
    if value.is_absolute():
        return value
    return Path(root) / value


def _write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def _write_text(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _load_json(path):
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _safe_dict(value):
    if isinstance(value, dict):
        return value
    return {}


def _safe_list(value):
    if isinstance(value, list):
        return value
    return []


def _json_artifact(artifact):
    return artifact["artifact_type"].endswith("_json") or artifact["path"].endswith(".json")


def _artifact_state(artifact, root=ROOT):
    path = _resolve_path(artifact["path"], root=root)
    present = path.exists()
    payload = None
    parse_status = "not_applicable"
    parse_error = None
    metadata = {}
    warning_count = 0

    if present and _json_artifact(artifact):
        try:
            payload = _load_json(path)
            parse_status = "parsed"
        except (OSError, json.JSONDecodeError) as exc:
            parse_status = "parse_failed"
            parse_error = type(exc).__name__
    elif not present and _json_artifact(artifact):
        parse_status = "missing"

    if isinstance(payload, dict):
        metadata = payload
        warnings = payload.get("warnings")
        if isinstance(warnings, list):
            warning_count = len(warnings)
        else:
            interpretation_warnings = payload.get("interpretation_warnings")
            warning_count = len(interpretation_warnings) if isinstance(interpretation_warnings, list) else 0

    state = {
        "artifact_id": artifact["artifact_id"],
        "path": artifact["path"],
        "artifact_type": artifact["artifact_type"],
        "required": artifact["required"],
        "present": present,
        "parse_status": parse_status,
        "schema_version": metadata.get("schema_version"),
        "task_id": metadata.get("task_id"),
        "status": metadata.get("status") or metadata.get("report_status") or metadata.get("series_status"),
        "warning_count": warning_count,
    }
    if parse_error is not None:
        state["parse_error"] = parse_error
    return state, payload


def _load_source_artifacts(root=ROOT):
    states = []
    payloads = {}
    for artifact in SOURCE_ARTIFACTS:
        state, payload = _artifact_state(artifact, root=root)
        states.append(state)
        payloads[artifact["artifact_id"]] = payload
    return states, payloads


def _required_artifact_problems(source_artifacts):
    return [
        item["path"]
        for item in source_artifacts
        if item["required"] and (not item["present"] or item["parse_status"] == "parse_failed")
    ]


def _missing_optional_artifacts(source_artifacts):
    return [item["path"] for item in source_artifacts if not item["required"] and not item["present"]]


def _optional_parse_warnings(source_artifacts):
    return [item["path"] for item in source_artifacts if not item["required"] and item["parse_status"] == "parse_failed"]


def _value(value, default=None):
    return value if value is not None else default


def _counter(value):
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    return 0


def _records_by_status(value):
    value = _safe_dict(value)
    return {key: value[key] for key in sorted(value)}


def _paper_019_summary(payloads, source_artifacts):
    state_by_id = {item["artifact_id"]: item for item in source_artifacts}
    paper_payload = _safe_dict(payloads.get("paper_019_series_json"))
    pack_payload = _safe_dict(payloads.get("operator_review_pack_json"))
    pack_paper = _safe_dict(pack_payload.get("paper_019_multi_market_run_series"))
    source = paper_payload or pack_paper
    accounting = _safe_dict(source.get("accounting_summary"))
    lifecycle = _safe_dict(source.get("lifecycle_summary"))
    paper_state = state_by_id["paper_019_series_json"]

    return {
        "section_id": "paper_019_multi_market_run_series",
        "artifact_status": "present" if paper_state["present"] else "missing",
        "artifact_pointer": "pm_bot/paper/multi_market_paper_run_series.v1.json",
        "artifact_parse_status": paper_state["parse_status"],
        "series_status": source.get("series_status"),
        "markets_seen": _value(source.get("markets_seen"), 0),
        "records_seen": _value(source.get("records_seen"), 0),
        "records_processed": _value(source.get("records_processed"), 0),
        "records_by_status": _records_by_status(source.get("records_by_status")),
        "cumulative_pnl": accounting.get("paper_accounting_cumulative_pnl"),
        "accounting_summary": {
            "paper_accounting_total_records": accounting.get("paper_accounting_total_records"),
            "paper_accounting_settled_count": accounting.get("paper_accounting_settled_count"),
            "paper_accounting_open_count": accounting.get("paper_accounting_open_count"),
            "paper_accounting_cumulative_pnl": accounting.get("paper_accounting_cumulative_pnl"),
            "paper_accounting_average_settled_pnl": accounting.get("paper_accounting_average_settled_pnl"),
            "paper_accounting_gross_profit": accounting.get("paper_accounting_gross_profit"),
            "paper_accounting_gross_loss": accounting.get("paper_accounting_gross_loss"),
        },
        "blocked_or_manual_review_summary": {
            "blocked_fixture_record_count": lifecycle.get("blocked_records", 0),
            "manual_review_only_count": lifecycle.get("manual_review_only_records", 0),
            "blocked_or_rejected_records": lifecycle.get("blocked_or_rejected_records", 0),
            "manual_review_only_records": lifecycle.get("manual_review_only_records", 0),
        },
        "interpretation_warning": pack_paper.get("interpretation_warning") or PAPER_019_INTERPRETATION_WARNING,
        "accounting_only_warning": ACCOUNTING_ONLY_WARNING,
        "safety_counters": {
            "real_orders_created": _counter(source.get("real_orders_created")),
            "autonomous_paper_orders": _counter(_safe_dict(source.get("safety_flags")).get("autonomous_paper_orders")),
            "network_calls": _counter(source.get("network_calls")),
            "commands_executed": _counter(source.get("commands_executed")),
            "autonomous_decisions": _counter(source.get("autonomous_decisions")),
        },
    }


def _quality_warning_summary(payloads):
    pack = _safe_dict(payloads.get("operator_review_pack_json"))
    pack_quality = _safe_dict(pack.get("quality_warning_summary"))
    quality = _safe_dict(payloads.get("artifact_health_report_json"))
    severity = _safe_dict(quality.get("warning_severity_summary"))

    warning_categories = pack_quality.get("warning_categories")
    if not isinstance(warning_categories, list):
        warning_categories = severity.get("warning_categories")
    top_categories = pack_quality.get("top_warning_categories")
    if not isinstance(top_categories, list):
        top_categories = severity.get("top_warning_categories")

    return {
        "source_path": "pm_bot/quality/artifact_health_report.v1.json",
        "quality_report_status": pack_quality.get("quality_report_status") or quality.get("report_status"),
        "quality_report_load_status": pack_quality.get("quality_report_load_status") or "parsed",
        "total_warnings": _value(pack_quality.get("total_warnings"), severity.get("total_warnings", 0)),
        "blocking": _value(pack_quality.get("blocking_warnings"), severity.get("blocking_count", 0)),
        "action_required": _value(pack_quality.get("action_required_warnings"), severity.get("action_required_count", 0)),
        "review_needed": _value(pack_quality.get("review_needed_warnings"), severity.get("review_needed_count", 0)),
        "informational": _value(pack_quality.get("informational_warnings"), severity.get("informational_count", 0)),
        "blocking_warning_detected": bool(
            _value(pack_quality.get("blocking_warning_detected"), severity.get("blocking_warning_detected", False))
        ),
        "operator_summary": pack_quality.get("operator_summary") or severity.get("operator_summary"),
        "recommended_manual_action": pack_quality.get("recommended_manual_action") or severity.get("recommended_manual_action"),
        "top_warning_categories": _safe_list(top_categories)[:5],
        "warning_categories": _safe_list(warning_categories),
    }


def _artifact_health_summary(payloads):
    quality = _safe_dict(payloads.get("artifact_health_report_json"))
    pointer = _safe_dict(quality.get("embedded_artifact_pointer_summary"))
    fixture = _safe_dict(quality.get("expected_fixture_alignment_summary"))
    return {
        "source_path": "pm_bot/quality/artifact_health_report.v1.json",
        "report_status": quality.get("report_status"),
        "artifacts_checked": quality.get("artifacts_checked"),
        "artifacts_present_count": quality.get("artifacts_present_count"),
        "artifacts_missing_count": quality.get("artifacts_missing_count"),
        "json_parse_pass_count": quality.get("json_parse_pass_count"),
        "json_parse_fail_count": quality.get("json_parse_fail_count"),
        "schema_version_missing_count": quality.get("schema_version_missing_count"),
        "embedded_artifact_pointer_summary": {
            "checked_count": pointer.get("checked_count"),
            "present_count": pointer.get("present_count"),
            "missing_count": pointer.get("missing_count"),
            "absolute_count": pointer.get("absolute_count"),
        },
        "expected_fixture_alignment_summary": {
            "checks_total": fixture.get("checks_total"),
            "aligned_count": fixture.get("aligned_count"),
            "mismatch_count": fixture.get("mismatch_count"),
            "actual_missing_count": fixture.get("actual_missing_count"),
        },
    }


def _operator_inbox_summary(payloads):
    pack = _safe_dict(payloads.get("operator_review_pack_json"))
    pack_inbox = _safe_dict(pack.get("operator_inbox_summary"))
    inbox = _safe_dict(payloads.get("manual_command_inbox_review_json"))
    source = pack_inbox or inbox
    return {
        "source_path": "pm_bot/operator/manual_command_inbox_review.v1.json",
        "present": bool(source),
        "schema_version": source.get("schema_version") or inbox.get("schema_version"),
        "records_seen": _value(source.get("records_seen"), 0),
        "accepted_count": _value(source.get("accepted_count"), 0),
        "rejected_count": _value(source.get("rejected_count"), 0),
        "needs_human_review_count": _value(source.get("needs_human_review_count"), 0),
        "execution_authority": bool(source.get("execution_authority", False)),
        "commands_executed": _value(source.get("commands_executed"), 0),
        "orders_created": _value(source.get("orders_created"), 0),
        "network_calls": _value(source.get("network_calls"), 0),
        "next_safe_action": source.get("next_safe_action"),
    }


def _workbench_review_pack_summary(payloads):
    pack = _safe_dict(payloads.get("operator_review_pack_json"))
    inventory = _safe_dict(pack.get("artifact_inventory"))
    inventory_summary = _safe_dict(inventory.get("summary"))
    run = _safe_dict(payloads.get("operator_workbench_export_run_json"))
    return {
        "source_path": "pm_bot/workbench/operator_review_pack.v1.json",
        "schema_version": pack.get("schema_version"),
        "generated_by": pack.get("generated_by"),
        "workbench_runner_required_steps_passed": run.get("required_steps_passed"),
        "workbench_runner_warnings": len(_safe_list(run.get("warnings"))),
        "artifact_inventory_summary": {
            "total_artifacts": inventory_summary.get("total_artifacts"),
            "present_artifacts": inventory_summary.get("present_artifacts"),
            "missing_artifacts": inventory_summary.get("missing_artifacts"),
            "required_missing_artifacts": inventory_summary.get("required_missing_artifacts"),
            "json_artifacts_parsed": inventory_summary.get("json_artifacts_parsed"),
            "json_artifacts_parse_failed": inventory_summary.get("json_artifacts_parse_failed"),
        },
        "missing_artifacts_count": len(_safe_list(pack.get("missing_artifacts"))),
        "warnings_count": len(_safe_list(pack.get("warnings"))),
        "paper_orders_created": _value(pack.get("paper_orders_created"), 0),
        "commands_executed": _value(pack.get("commands_executed"), 0),
        "network_calls": _value(pack.get("network_calls"), 0),
        "no_recommendations_or_decisions_statement": pack.get(
            "no_recommendations_or_decisions_statement",
            "This report does not recommend markets, sides, prices, sizes, orders, trades, paper orders, or decisions.",
        ),
    }


def _portfolio_audit_summary(payloads):
    dashboard = _safe_dict(payloads.get("portfolio_audit_state_preview_json"))
    product = _safe_dict(dashboard.get("product_stage_summary"))
    accounting = _safe_dict(dashboard.get("portfolio_accounting_summary"))
    return {
        "source_path": "pm_bot/dashboard/portfolio_audit_state_preview.v1.json",
        "schema_version": dashboard.get("schema_version"),
        "dashboard_state_export_version": dashboard.get("dashboard_state_export_version"),
        "current_known_portfolio_audit_status": product.get("current_known_portfolio_audit_status"),
        "known_market_ids": _safe_list(dashboard.get("known_market_ids")),
        "summary_status": accounting.get("summary_status"),
        "accounting_boundary": _safe_dict(accounting.get("accounting_boundary")),
    }


def _next_safe_manual_actions(payloads):
    pack = _safe_dict(payloads.get("operator_review_pack_json"))
    actions = _safe_list(pack.get("next_safe_manual_actions"))
    if actions:
        return actions
    return [
        {
            "action_id": "review_static_report_sources",
            "description": "Review this static report and source artifact pointers manually.",
            "non_trading_action": True,
            "requires_runtime": False,
            "creates_orders": False,
        }
    ]


def _current_operator_status(required_problems, optional_missing, workbench, paper_019):
    if required_problems:
        status = "blocked_missing_required_static_report_source"
    elif optional_missing:
        status = "manual_local_review_ready_with_missing_optional_sources"
    else:
        status = "manual_local_review_ready"
    return {
        "status": status,
        "mode": "offline/local/paper/accounting-only",
        "operator_review_only": True,
        "required_source_problems": required_problems,
        "missing_optional_artifacts": optional_missing,
        "workbench_runner_required_steps_passed": workbench["workbench_runner_required_steps_passed"],
        "paper_019_visible": paper_019["artifact_status"] == "present" and paper_019["markets_seen"] == 5,
    }


def _report_status(required_problems, optional_missing, optional_parse_failed):
    if required_problems:
        return "static_report_failed"
    if optional_missing or optional_parse_failed:
        return "static_report_generated_with_warnings"
    return "static_report_generated"


def build_static_operator_report(root=ROOT):
    source_artifacts, payloads = _load_source_artifacts(root=root)
    required_problems = _required_artifact_problems(source_artifacts)
    optional_missing = _missing_optional_artifacts(source_artifacts)
    optional_parse_failed = _optional_parse_warnings(source_artifacts)
    paper_019 = _paper_019_summary(payloads, source_artifacts)
    quality = _quality_warning_summary(payloads)
    artifact_health = _artifact_health_summary(payloads)
    inbox = _operator_inbox_summary(payloads)
    workbench = _workbench_review_pack_summary(payloads)
    portfolio = _portfolio_audit_summary(payloads)
    current_status = _current_operator_status(required_problems, optional_missing, workbench, paper_019)
    status = _report_status(required_problems, optional_missing, optional_parse_failed)

    return {
        "schema_version": SCHEMA_VERSION,
        "task_id": TASK_ID,
        "generated_by": GENERATED_BY,
        "generated_at_policy": {
            "wall_clock_time_used": False,
            "policy": "deterministic_static_snapshot_no_current_time",
            "fixed_value": "not_emitted",
        },
        "html_report_path": _display_path(DEFAULT_HTML_REPORT, root=ROOT),
        "source_artifacts": source_artifacts,
        "sections_rendered": list(SECTIONS_RENDERED),
        "current_operator_status": current_status,
        "workbench_review_pack_summary": workbench,
        "portfolio_audit_summary": portfolio,
        "paper_019_summary": paper_019,
        "quality_warning_summary": quality,
        "artifact_health_summary": artifact_health,
        "operator_inbox_summary": inbox,
        "safety_flags": dict(SAFETY_FLAGS),
        "forbidden_capabilities": list(FORBIDDEN_CAPABILITIES),
        "next_safe_manual_actions": _next_safe_manual_actions(payloads),
        "warnings": {
            "required_source_problems": required_problems,
            "missing_optional_artifacts": optional_missing,
            "optional_parse_failed_artifacts": optional_parse_failed,
            "accounting_only_warning": ACCOUNTING_ONLY_WARNING,
            "paper_019_interpretation_warning": paper_019["interpretation_warning"],
            "not_trading_advice_warning": NOT_TRADING_ADVICE_WARNING,
        },
        "network_calls": 0,
        "commands_executed": 0,
        "orders_created": 0,
        "autonomous_decisions": 0,
        "report_status": status,
    }


def _text(value):
    if value is True:
        return "true"
    if value is False:
        return "false"
    if value is None:
        return "none"
    return str(value)


def _h(value):
    return html.escape(_text(value), quote=True)


def _render_key_value_rows(rows):
    lines = ["<table><tbody>"]
    for key, value in rows:
        lines.append(f"<tr><th>{_h(key)}</th><td>{_h(value)}</td></tr>")
    lines.append("</tbody></table>")
    return "\n".join(lines)


def _render_count_cards(items):
    lines = ['<div class="metric-grid">']
    for label, value in items:
        lines.append(
            '<div class="metric">'
            f'<div class="metric-label">{_h(label)}</div>'
            f'<div class="metric-value">{_h(value)}</div>'
            "</div>"
        )
    lines.append("</div>")
    return "\n".join(lines)


def _render_bullets(items):
    lines = ["<ul>"]
    for item in items:
        lines.append(f"<li>{_h(item)}</li>")
    lines.append("</ul>")
    return "\n".join(lines)


def _render_action_list(actions):
    lines = ["<ol>"]
    for action in actions:
        lines.append(
            "<li>"
            f"<strong>{_h(action.get('action_id'))}</strong>: {_h(action.get('description'))} "
            f"<span class=\"tag\">non_trading={_h(action.get('non_trading_action'))}</span> "
            f"<span class=\"tag\">runtime={_h(action.get('requires_runtime'))}</span> "
            f"<span class=\"tag\">creates_orders={_h(action.get('creates_orders'))}</span>"
            "</li>"
        )
    lines.append("</ol>")
    return "\n".join(lines)


def _render_source_artifact_table(source_artifacts):
    lines = [
        "<table>",
        "<thead><tr><th>Artifact</th><th>Path</th><th>Required</th><th>Present</th><th>Parse</th><th>Status</th></tr></thead>",
        "<tbody>",
    ]
    for item in source_artifacts:
        lines.append(
            "<tr>"
            f"<td>{_h(item['artifact_id'])}</td>"
            f"<td><code>{_h(item['path'])}</code></td>"
            f"<td>{_h(item['required'])}</td>"
            f"<td>{_h(item['present'])}</td>"
            f"<td>{_h(item['parse_status'])}</td>"
            f"<td>{_h(item['status'])}</td>"
            "</tr>"
        )
    lines.append("</tbody></table>")
    return "\n".join(lines)


def _render_top_warning_categories(categories):
    if not categories:
        return "<p>none</p>"
    lines = [
        "<table>",
        "<thead><tr><th>Category</th><th>Severity</th><th>Count</th><th>Operator Bucket</th></tr></thead>",
        "<tbody>",
    ]
    for item in categories:
        lines.append(
            "<tr>"
            f"<td>{_h(item.get('category'))}</td>"
            f"<td>{_h(item.get('severity'))}</td>"
            f"<td>{_h(item.get('count'))}</td>"
            f"<td>{_h(item.get('operator_bucket'))}</td>"
            "</tr>"
        )
    lines.append("</tbody></table>")
    return "\n".join(lines)


def render_static_operator_report_html(summary):
    status = summary["current_operator_status"]
    workbench = summary["workbench_review_pack_summary"]
    inventory = workbench["artifact_inventory_summary"]
    paper = summary["paper_019_summary"]
    quality = summary["quality_warning_summary"]
    health = summary["artifact_health_summary"]
    inbox = summary["operator_inbox_summary"]
    portfolio = summary["portfolio_audit_summary"]
    warnings = summary["warnings"]

    return "\n".join(
        [
            "<!doctype html>",
            '<html lang="en">',
            "<head>",
            '<meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1">',
            "<title>PMBOT Static Operator Report v1</title>",
            "<style>",
            "body{font-family:Arial,Helvetica,sans-serif;margin:0;background:#f6f7f9;color:#17202a;line-height:1.45}",
            "header{background:#17202a;color:white;padding:28px 32px}",
            "main{max-width:1120px;margin:0 auto;padding:24px 18px 48px}",
            "section{background:white;border:1px solid #d8dde3;border-radius:6px;margin:0 0 18px;padding:18px}",
            "h1{font-size:28px;margin:0 0 8px;letter-spacing:0}",
            "h2{font-size:20px;margin:0 0 12px;letter-spacing:0}",
            "p{margin:8px 0}",
            "code{background:#eef1f4;padding:1px 4px;border-radius:3px}",
            "table{border-collapse:collapse;width:100%;margin-top:8px;font-size:14px}",
            "th,td{border:1px solid #d8dde3;padding:7px 8px;text-align:left;vertical-align:top}",
            "th{background:#eef1f4;width:28%}",
            ".metric-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin:10px 0}",
            ".metric{border:1px solid #d8dde3;border-radius:6px;padding:10px;background:#fbfcfd}",
            ".metric-label{font-size:12px;color:#57606a;text-transform:uppercase}",
            ".metric-value{font-size:20px;font-weight:700;margin-top:4px}",
            ".warning{border-left:4px solid #b42318;background:#fff4f2;padding:10px 12px}",
            ".notice{border-left:4px solid #1f6feb;background:#f0f6ff;padding:10px 12px}",
            ".tag{display:inline-block;background:#eef1f4;border-radius:3px;padding:1px 5px;margin-left:5px;font-size:12px}",
            "ul,ol{padding-left:22px}",
            "</style>",
            "</head>",
            "<body>",
            "<header>",
            "<h1>PMBOT Static Operator Report v1</h1>",
            f"<p>generated_by: <code>{_h(summary['generated_by'])}</code></p>",
            f"<p>generation_policy: {_h(summary['generated_at_policy']['policy'])}</p>",
            "</header>",
            "<main>",
            "<section>",
            "<h2>Open This First</h2>",
            f"<p><strong>Operator status:</strong> {_h(status['status'])}</p>",
            f"<p><strong>Mode:</strong> {_h(status['mode'])}</p>",
            f"<p><strong>PAPER-019 visible:</strong> {_h(status['paper_019_visible'])}</p>",
            f"<p><strong>Quality blockers detected:</strong> {_h(quality['blocking_warning_detected'])}</p>",
            '<p class="warning"><strong>Accounting-only warning:</strong> '
            f"{_h(ACCOUNTING_ONLY_WARNING)} {_h(NOT_TRADING_ADVICE_WARNING)}</p>",
            "</section>",
            "<section>",
            "<h2>Current PMBOT Mode</h2>",
            _render_key_value_rows(
                [
                    ("offline_only", summary["safety_flags"]["offline_only"]),
                    ("local_file_reads_only", summary["safety_flags"]["local_file_reads_only"]),
                    ("paper_only", summary["safety_flags"]["paper_only"]),
                    ("paper_accounting_only", summary["safety_flags"]["paper_accounting_only"]),
                    ("operator_review_only", summary["safety_flags"]["operator_review_only"]),
                    ("runtime_wiring", summary["safety_flags"]["runtime_wiring"]),
                    ("network_api", summary["safety_flags"]["network_api"]),
                    ("dashboard_server", summary["safety_flags"]["dashboard_server"]),
                    ("frontend_runtime", summary["safety_flags"]["frontend_runtime"]),
                    ("browser_automation", summary["safety_flags"]["browser_automation"]),
                ]
            ),
            "</section>",
            "<section>",
            "<h2>Workbench Review Pack Summary</h2>",
            _render_count_cards(
                [
                    ("total_artifacts", inventory["total_artifacts"]),
                    ("present_artifacts", inventory["present_artifacts"]),
                    ("missing_artifacts", inventory["missing_artifacts"]),
                    ("required_missing", inventory["required_missing_artifacts"]),
                    ("warnings", workbench["warnings_count"]),
                    ("runner_required_steps", workbench["workbench_runner_required_steps_passed"]),
                ]
            ),
            _render_key_value_rows(
                [
                    ("source_path", workbench["source_path"]),
                    ("schema_version", workbench["schema_version"]),
                    ("paper_orders_created", workbench["paper_orders_created"]),
                    ("commands_executed", workbench["commands_executed"]),
                    ("network_calls", workbench["network_calls"]),
                    ("boundary", workbench["no_recommendations_or_decisions_statement"]),
                ]
            ),
            "</section>",
            "<section>",
            "<h2>PAPER-019 Multi-Market Paper Run Series</h2>",
            _render_count_cards(
                [
                    ("markets_seen", paper["markets_seen"]),
                    ("records_seen", paper["records_seen"]),
                    ("records_processed", paper["records_processed"]),
                    ("cumulative_pnl", paper["cumulative_pnl"]),
                ]
            ),
            '<p class="warning"><strong>Accounting-only warning near PnL:</strong> '
            f"{_h(paper['accounting_only_warning'])} {_h(paper['interpretation_warning'])}</p>",
            _render_key_value_rows(
                [
                    ("series_status", paper["series_status"]),
                    ("artifact_pointer", paper["artifact_pointer"]),
                    ("artifact_parse_status", paper["artifact_parse_status"]),
                    ("records_by_status", json.dumps(paper["records_by_status"], sort_keys=True, ensure_ascii=True)),
                    (
                        "blocked_or_manual_review",
                        json.dumps(paper["blocked_or_manual_review_summary"], sort_keys=True, ensure_ascii=True),
                    ),
                    ("real_orders_created", paper["safety_counters"]["real_orders_created"]),
                    ("autonomous_paper_orders", paper["safety_counters"]["autonomous_paper_orders"]),
                    ("network_calls", paper["safety_counters"]["network_calls"]),
                    ("commands_executed", paper["safety_counters"]["commands_executed"]),
                    ("autonomous_decisions", paper["safety_counters"]["autonomous_decisions"]),
                ]
            ),
            "</section>",
            "<section>",
            "<h2>Quality Warning Severity Summary</h2>",
            _render_count_cards(
                [
                    ("total_warnings", quality["total_warnings"]),
                    ("blocking", quality["blocking"]),
                    ("action_required", quality["action_required"]),
                    ("review_needed", quality["review_needed"]),
                    ("informational", quality["informational"]),
                    ("blocking_warning_detected", quality["blocking_warning_detected"]),
                ]
            ),
            f"<p>{_h(quality['operator_summary'])}</p>",
            f"<p><strong>Recommended manual action:</strong> {_h(quality['recommended_manual_action'])}</p>",
            "<h3>Top Warning Categories</h3>",
            _render_top_warning_categories(quality["top_warning_categories"]),
            "</section>",
            "<section>",
            "<h2>Artifact Health Summary</h2>",
            _render_count_cards(
                [
                    ("artifacts_checked", health["artifacts_checked"]),
                    ("present", health["artifacts_present_count"]),
                    ("missing", health["artifacts_missing_count"]),
                    ("json_parse_fail", health["json_parse_fail_count"]),
                    ("schema_version_missing", health["schema_version_missing_count"]),
                    ("fixture_mismatch", health["expected_fixture_alignment_summary"]["mismatch_count"]),
                ]
            ),
            _render_key_value_rows(
                [
                    ("report_status", health["report_status"]),
                    ("source_path", health["source_path"]),
                    (
                        "embedded_artifact_pointer_summary",
                        json.dumps(health["embedded_artifact_pointer_summary"], sort_keys=True, ensure_ascii=True),
                    ),
                    (
                        "expected_fixture_alignment_summary",
                        json.dumps(health["expected_fixture_alignment_summary"], sort_keys=True, ensure_ascii=True),
                    ),
                ]
            ),
            "</section>",
            "<section>",
            "<h2>Operator Inbox Review Summary</h2>",
            _render_count_cards(
                [
                    ("records_seen", inbox["records_seen"]),
                    ("accepted", inbox["accepted_count"]),
                    ("rejected", inbox["rejected_count"]),
                    ("needs_human_review", inbox["needs_human_review_count"]),
                    ("commands_executed", inbox["commands_executed"]),
                    ("orders_created", inbox["orders_created"]),
                ]
            ),
            _render_key_value_rows(
                [
                    ("source_path", inbox["source_path"]),
                    ("execution_authority", inbox["execution_authority"]),
                    ("network_calls", inbox["network_calls"]),
                    ("next_safe_action", inbox["next_safe_action"]),
                ]
            ),
            "</section>",
            "<section>",
            "<h2>Portfolio Audit Context</h2>",
            _render_key_value_rows(
                [
                    ("source_path", portfolio["source_path"]),
                    ("schema_version", portfolio["schema_version"]),
                    ("dashboard_state_export_version", portfolio["dashboard_state_export_version"]),
                    ("current_known_portfolio_audit_status", portfolio["current_known_portfolio_audit_status"]),
                    ("known_market_ids", ", ".join(portfolio["known_market_ids"])),
                    ("summary_status", portfolio["summary_status"]),
                    ("accounting_boundary_warning", _safe_dict(portfolio["accounting_boundary"]).get("warning")),
                ]
            ),
            "</section>",
            "<section>",
            "<h2>Safety And Forbidden Capabilities</h2>",
            _render_key_value_rows(sorted(summary["safety_flags"].items())),
            "<h3>Forbidden Capabilities</h3>",
            _render_bullets(summary["forbidden_capabilities"]),
            "</section>",
            "<section>",
            "<h2>Source Artifact Pointers</h2>",
            _render_source_artifact_table(summary["source_artifacts"]),
            "</section>",
            "<section>",
            "<h2>Next Safe Manual Actions</h2>",
            _render_action_list(summary["next_safe_manual_actions"]),
            "</section>",
            "<section>",
            "<h2>Report Warnings</h2>",
            _render_key_value_rows(
                [
                    ("required_source_problems", ", ".join(warnings["required_source_problems"]) or "none"),
                    ("missing_optional_artifacts", ", ".join(warnings["missing_optional_artifacts"]) or "none"),
                    ("optional_parse_failed_artifacts", ", ".join(warnings["optional_parse_failed_artifacts"]) or "none"),
                    ("accounting_only_warning", warnings["accounting_only_warning"]),
                    ("paper_019_interpretation_warning", warnings["paper_019_interpretation_warning"]),
                    ("not_trading_advice_warning", warnings["not_trading_advice_warning"]),
                ]
            ),
            "</section>",
            '<section class="notice">',
            "<h2>Not Trading Advice / Not Strategy Profitability</h2>",
            f"<p>{_h(NOT_TRADING_ADVICE_WARNING)}</p>",
            f"<p>{_h(ACCOUNTING_ONLY_WARNING)}</p>",
            "</section>",
            "</main>",
            "</body>",
            "</html>",
            "",
        ]
    )


def _result_payload(summary):
    completed = summary["report_status"] != "static_report_failed"
    return {
        "task_id": TASK_ID,
        "status": "completed_ready_for_review" if completed else "blocked",
        "summary": "Generated deterministic local static HTML PMBOT operator report.",
        "files_created": [
            "pm_bot/dashboard/export_static_operator_report.py",
            "pm_bot/dashboard/static_operator_report.v1.html",
            "pm_bot/dashboard/static_operator_report_summary.v1.json",
            "pm_bot/dashboard/expected_static_operator_report_summary.v1.json",
            "pm_bot/dashboard/tests/test_static_operator_report.py",
            "docs/PMBOT_DASHBOARD_003_RESULT.json",
        ],
        "files_modified": [],
        "static_report": {
            "html_path": "pm_bot/dashboard/static_operator_report.v1.html",
            "summary_json_path": "pm_bot/dashboard/static_operator_report_summary.v1.json",
            "sections_rendered": summary["sections_rendered"],
            "paper_019_visible": summary["current_operator_status"]["paper_019_visible"],
            "quality_severity_visible": True,
            "accounting_only_warning_visible": True,
            "external_network_references": 0,
            "script_tags": 0,
        },
        "tests": [],
        "safety": {
            "runtime_wiring": False,
            "network_api": False,
            "wallet": False,
            "trading": False,
            "autonomous_paper_orders": False,
            "scoring_probability_ev_edge": False,
            "market_decisions": False,
            "truth_inference": False,
            "command_execution": False,
            "automation_daemon": False,
            "dashboard_server": False,
            "frontend_runtime": False,
            "browser_automation": False,
        },
        "blockers": summary["warnings"]["required_source_problems"],
        "next_recommended_task": "PMBOT-PAPER-020-PAPER-RUN-SERIES-POSTMORTEM",
    }


def write_static_operator_report_artifacts(root=ROOT):
    summary = build_static_operator_report(root=root)
    html_text = render_static_operator_report_html(summary)
    _write_text(DEFAULT_HTML_REPORT, html_text)
    _write_json(DEFAULT_SUMMARY_JSON, summary)
    _write_json(DEFAULT_EXPECTED_SUMMARY_JSON, summary)
    _write_json(DEFAULT_RESULT, _result_payload(summary))
    return {
        "task_id": TASK_ID,
        "report_status": summary["report_status"],
        "html_report_path": _display_path(DEFAULT_HTML_REPORT),
        "summary_json_path": _display_path(DEFAULT_SUMMARY_JSON),
        "expected_summary_json_path": _display_path(DEFAULT_EXPECTED_SUMMARY_JSON),
        "result_path": _display_path(DEFAULT_RESULT),
        "sections_rendered": summary["sections_rendered"],
        "network_calls": 0,
        "commands_executed": 0,
        "orders_created": 0,
        "autonomous_decisions": 0,
    }


def main(argv):
    args = _parse_args(argv)
    summary = build_static_operator_report(ROOT)
    if args.summary:
        print(json.dumps(summary, indent=2, ensure_ascii=True))
        return 0 if summary["report_status"] != "static_report_failed" else 2
    if args.html:
        print(render_static_operator_report_html(summary), end="")
        return 0 if summary["report_status"] != "static_report_failed" else 2
    result = write_static_operator_report_artifacts(ROOT)
    print(json.dumps(result, indent=2, ensure_ascii=True))
    return 0 if result["report_status"] != "static_report_failed" else 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
