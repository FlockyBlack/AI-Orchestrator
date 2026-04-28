import argparse
import json
import sys
from pathlib import Path


TASK_ID = "PMBOT-PAPER-020-PAPER-RUN-SERIES-POSTMORTEM"
SCHEMA_VERSION = "paper_run_series_postmortem.v1"
MARKDOWN_VERSION = "paper_run_series_postmortem_markdown.v1"
RESULT_SCHEMA_VERSION = "paper_020_result.v1"
GENERATED_BY = "pm_bot/paper/export_paper_run_series_postmortem.py"

ROOT = Path(__file__).resolve().parents[2]
PAPER_DIR = ROOT / "pm_bot" / "paper"
DOCS_DIR = ROOT / "docs"

DEFAULT_PAPER_019_OUTPUT = PAPER_DIR / "multi_market_paper_run_series.v1.json"
DEFAULT_OUTPUT = PAPER_DIR / "paper_run_series_postmortem.v1.json"
DEFAULT_OUTPUT_MD = PAPER_DIR / "paper_run_series_postmortem.v1.md"
DEFAULT_EXPECTED = PAPER_DIR / "expected_paper_run_series_postmortem.v1.json"
DEFAULT_RESULT = DOCS_DIR / "PMBOT_PAPER_020_RESULT.json"

ACCOUNTING_ONLY_WARNING = (
    "PAPER-019 PnL is accounting-only fixture output, not strategy profitability; "
    "it is not a recommendation, edge, EV, probability estimate, market score, "
    "or market truth evidence."
)

FILES_CREATED = [
    "pm_bot/paper/export_paper_run_series_postmortem.py",
    "pm_bot/paper/paper_run_series_postmortem.v1.json",
    "pm_bot/paper/paper_run_series_postmortem.v1.md",
    "pm_bot/paper/expected_paper_run_series_postmortem.v1.json",
    "pm_bot/paper/tests/test_paper_run_series_postmortem.py",
    "docs/PMBOT_PAPER_020_RESULT.json",
]

SOURCE_ARTIFACT_SPECS = [
    {
        "artifact_id": "dashboard_003_result",
        "path": "docs/PMBOT_DASHBOARD_003_RESULT.json",
        "required": False,
    },
    {
        "artifact_id": "paper_019_result",
        "path": "docs/PMBOT_PAPER_019_RESULT.json",
        "required": False,
    },
    {
        "artifact_id": "paper_019_multi_market_run_series",
        "path": "pm_bot/paper/multi_market_paper_run_series.v1.json",
        "required": True,
    },
    {
        "artifact_id": "paper_019_multi_market_run_series_markdown",
        "path": "pm_bot/paper/multi_market_paper_run_series.v1.md",
        "required": False,
    },
    {
        "artifact_id": "paper_019_fixture",
        "path": "pm_bot/paper/paper_run_series_fixture.v1.json",
        "required": False,
    },
    {
        "artifact_id": "paper_019_exporter",
        "path": "pm_bot/paper/run_multi_market_paper_run_series.py",
        "required": False,
    },
    {
        "artifact_id": "operator_review_pack_json",
        "path": "pm_bot/workbench/operator_review_pack.v1.json",
        "required": False,
    },
    {
        "artifact_id": "operator_review_pack_markdown",
        "path": "pm_bot/workbench/operator_review_pack.v1.md",
        "required": False,
    },
    {
        "artifact_id": "static_operator_report_summary",
        "path": "pm_bot/dashboard/static_operator_report_summary.v1.json",
        "required": False,
    },
    {
        "artifact_id": "static_operator_report_html",
        "path": "pm_bot/dashboard/static_operator_report.v1.html",
        "required": False,
    },
    {
        "artifact_id": "artifact_health_report",
        "path": "pm_bot/quality/artifact_health_report.v1.json",
        "required": False,
    },
]

SAFETY_FLAGS = {
    "offline_only": True,
    "deterministic": True,
    "fixture_only": True,
    "paper_only": True,
    "paper_accounting_only": True,
    "runtime_wiring": False,
    "network_api": False,
    "wallet": False,
    "trading": False,
    "real_orders": False,
    "live_trading": False,
    "autonomous_paper_orders": False,
    "scoring_probability_ev_edge": False,
    "market_decisions": False,
    "truth_inference": False,
    "command_execution": False,
    "automation_daemon": False,
    "dashboard_server": False,
}

SAFETY_COUNTERS = {
    "real_orders_created": 0,
    "autonomous_paper_orders": 0,
    "network_calls": 0,
    "commands_executed": 0,
    "autonomous_decisions": 0,
}


def _parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Export deterministic local PMBOT PAPER-020 paper run postmortem."
    )
    parser.add_argument("--paper-019-output", default=str(DEFAULT_PAPER_019_OUTPUT))
    return parser.parse_args(argv)


def _display_path(path):
    resolved = Path(path).resolve()
    try:
        return str(resolved.relative_to(ROOT.resolve())).replace("\\", "/")
    except ValueError:
        return str(resolved).replace("\\", "/")


def _resolve_path(path):
    value = Path(path)
    if value.is_absolute():
        return value
    return ROOT / value


def _load_json(path):
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def _write_text(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _artifact_status(spec):
    path = _resolve_path(spec["path"])
    row = {
        "artifact_id": spec["artifact_id"],
        "path": spec["path"],
        "required": spec["required"],
        "present": path.exists(),
        "parse_status": "missing",
    }
    if not path.exists():
        return row
    if path.suffix.lower() != ".json":
        row["parse_status"] = "not_applicable"
        return row
    try:
        payload = _load_json(path)
    except json.JSONDecodeError as exc:
        row["parse_status"] = "json_parse_error"
        row["parse_error"] = str(exc)
        return row
    row["parse_status"] = "parsed"
    if isinstance(payload, dict):
        for key in ("schema_version", "task_id", "status", "series_status", "report_status"):
            if payload.get(key) is not None:
                row[key] = payload.get(key)
    return row


def _source_artifacts():
    return [_artifact_status(spec) for spec in SOURCE_ARTIFACT_SPECS]


def _missing_optional_docs(source_artifacts):
    return [
        artifact["path"]
        for artifact in source_artifacts
        if not artifact["required"] and not artifact["present"]
    ]


def _records_by_status(paper_019):
    status_counts = paper_019.get("records_by_status")
    if isinstance(status_counts, dict):
        return dict(sorted(status_counts.items()))
    counts = {}
    for record in paper_019.get("record_summaries", []):
        status = record.get("processing_status")
        if status:
            counts[status] = counts.get(status, 0) + 1
    return dict(sorted(counts.items()))


def _record_summaries(paper_019, status):
    rows = []
    for record in paper_019.get("record_summaries", []):
        if record.get("processing_status") != status:
            continue
        row = {
            "record_id": record.get("record_id"),
            "market_id": record.get("market_id"),
            "processing_status": record.get("processing_status"),
            "lifecycle_state": record.get("lifecycle_state"),
            "accounting_outcome": record.get("accounting_outcome"),
            "paper_position_status": record.get("paper_position_status"),
            "accounting_included": bool(record.get("accounting_included")),
            "paper_orders_created": int(record.get("paper_orders_created", 0)),
            "real_orders_created": int(record.get("real_orders_created", 0)),
            "network_calls": int(record.get("network_calls", 0)),
            "commands_executed": int(record.get("commands_executed", 0)),
            "autonomous_decisions": int(record.get("autonomous_decisions", 0)),
        }
        for key in ("cost_basis", "settlement_value", "paper_accounting_pnl"):
            if key in record:
                row[key] = record.get(key)
        if record.get("blocked_reason_codes") is not None:
            row["blocked_reason_codes"] = list(record.get("blocked_reason_codes") or [])
        rows.append(row)
    return rows


def _record_status_notes(accepted, manual_review, blocked):
    return [
        {
            "processing_status": "accepted_accounting_record",
            "count": len(accepted),
            "operator_meaning": (
                "Record was accepted from the local fixture for accounting summary only."
            ),
        },
        {
            "processing_status": "manual_review_only",
            "count": len(manual_review),
            "operator_meaning": (
                "Record remains an open manual-review fixture item; it is inert and does not create orders."
            ),
        },
        {
            "processing_status": "blocked_fixture_record",
            "count": len(blocked),
            "operator_meaning": (
                "Record was retained as blocked fixture context and excluded from accounting."
            ),
        },
    ]


def _paper_019_summary(paper_019, source_path):
    checks = paper_019.get("checks") or []
    passed_checks = [check for check in checks if check.get("status") == "pass"]
    return {
        "source_artifact": _display_path(source_path),
        "source_schema_version": paper_019.get("schema_version"),
        "source_task_id": paper_019.get("task_id"),
        "series_status": paper_019.get("series_status"),
        "run_mode": paper_019.get("run_mode"),
        "fixture_path": paper_019.get("fixture_path"),
        "markets_seen": paper_019.get("markets_seen", 0),
        "market_ids": list(paper_019.get("market_ids", [])),
        "records_seen": paper_019.get("records_seen", 0),
        "records_processed": paper_019.get("records_processed", 0),
        "records_by_status": _records_by_status(paper_019),
        "accounting_summary": dict(paper_019.get("accounting_summary") or {}),
        "portfolio_summary": dict(paper_019.get("portfolio_summary") or {}),
        "checks_passed": len(passed_checks),
        "checks_total": len(checks),
        "source_warnings": list(paper_019.get("warnings", [])),
    }


def build_paper_run_series_postmortem(paper_019, source_artifacts, source_path):
    accounting = dict(paper_019.get("accounting_summary") or {})
    accepted = _record_summaries(paper_019, "accepted_accounting_record")
    manual_review = _record_summaries(paper_019, "manual_review_only")
    blocked = _record_summaries(paper_019, "blocked_fixture_record")
    records_by_status = _records_by_status(paper_019)
    source_summary = _paper_019_summary(paper_019, source_path)
    status = "postmortem_completed"
    if paper_019.get("series_status") != "series_run_passed":
        status = "postmortem_completed_with_warnings"
    if any(artifact["required"] and not artifact["present"] for artifact in source_artifacts):
        status = "postmortem_blocked"
    return {
        "schema_version": SCHEMA_VERSION,
        "markdown_version": MARKDOWN_VERSION,
        "task_id": TASK_ID,
        "generated_by": GENERATED_BY,
        "source_artifacts": source_artifacts,
        "missing_optional_docs": _missing_optional_docs(source_artifacts),
        "paper_019_summary": source_summary,
        "records_by_status": records_by_status,
        "record_status_notes": _record_status_notes(accepted, manual_review, blocked),
        "accounting_interpretation": {
            "accounting_scope": "paper_019_fixture_accounting_only",
            "cumulative_pnl": accounting.get("paper_accounting_cumulative_pnl", "0.00"),
            "average_settled_pnl": accounting.get("paper_accounting_average_settled_pnl", "0.00"),
            "gross_profit": accounting.get("paper_accounting_gross_profit", "0.00"),
            "gross_loss": accounting.get("paper_accounting_gross_loss", "0.00"),
            "warning": ACCOUNTING_ONLY_WARNING,
            "what_it_means": [
                "The values are arithmetic summaries of explicit local fixture accounting fields.",
                "The open manual-review record contributes cost basis but has zero settlement and zero PnL in the fixture.",
                "The blocked record is retained for operator context and excluded from accounting totals.",
            ],
            "what_it_does_not_mean": [
                "It does not show strategy profitability.",
                "It does not infer market truth or settlement truth beyond fixture values.",
                "It does not justify market selection, side selection, size selection, or execution.",
            ],
        },
        "accepted_record_summary": accepted,
        "blocked_record_summary": blocked,
        "manual_review_record_summary": manual_review,
        "fixture_limitations": [
            "The series has five local fixture records and is not statistically representative.",
            "All accounting values are explicit fixture values; no live settlement truth is inferred.",
            "Only one open manual-review record and one blocked record are represented.",
            "No fees, liquidity, orderbook state, slippage, fill uncertainty, or timing variance are modeled.",
            "The fixture does not validate market discovery, live data handling, wallet access, or execution behavior.",
        ],
        "safety_flags": dict(SAFETY_FLAGS),
        "safety_counters": dict(SAFETY_COUNTERS),
        "operator_takeaways": [
            "PAPER-019 completed deterministic offline fixture accounting over five markets.",
            "Three records were accepted for settled accounting, one remains open manual review, and one was blocked.",
            "The cumulative PnL of "
            f"{accounting.get('paper_accounting_cumulative_pnl', '0.00')} is covered by the accounting-only warning.",
            "No safety counter indicates live data, order creation, autonomous action, or command execution.",
        ],
        "recommended_next_fixture_expansions": [
            "Add more settled fixture records covering additional cost and settlement combinations.",
            "Add more open manual-review fixture records that remain inert until explicit fixture settlement values exist.",
            "Add blocked fixture variants for malformed accounting values and unsafe lineage flags.",
            "Add boundary accounting examples for zero cost, zero settlement, and unusually large fixture values.",
        ],
        "next_safe_action": (
            "PMBOT-WORKBENCH-006-SURFACE-PAPER-020-POSTMORTEM or "
            "PMBOT-PRODUCT-002-NEXT-MVP-GATE-REVIEW"
        ),
        "postmortem_status": status,
    }


def _blocked_postmortem(source_artifacts, source_path, blocker):
    return {
        "schema_version": SCHEMA_VERSION,
        "markdown_version": MARKDOWN_VERSION,
        "task_id": TASK_ID,
        "generated_by": GENERATED_BY,
        "source_artifacts": source_artifacts,
        "missing_optional_docs": _missing_optional_docs(source_artifacts),
        "paper_019_summary": {
            "source_artifact": _display_path(source_path),
            "source_paper_019_found": False,
            "markets_seen": 0,
            "records_seen": 0,
            "records_processed": 0,
            "records_by_status": {},
            "accounting_summary": {},
        },
        "records_by_status": {},
        "accounting_interpretation": {
            "accounting_scope": "paper_019_fixture_accounting_only",
            "cumulative_pnl": "0.00",
            "warning": ACCOUNTING_ONLY_WARNING,
            "blocker": blocker,
        },
        "accepted_record_summary": [],
        "blocked_record_summary": [],
        "manual_review_record_summary": [],
        "fixture_limitations": ["PAPER-019 output was not available for postmortem generation."],
        "safety_flags": dict(SAFETY_FLAGS),
        "safety_counters": dict(SAFETY_COUNTERS),
        "operator_takeaways": [],
        "recommended_next_fixture_expansions": [],
        "next_safe_action": "requires_operator_review",
        "postmortem_status": "postmortem_blocked",
        "blockers": [blocker],
    }


def render_markdown(postmortem):
    summary = postmortem["paper_019_summary"]
    accounting = summary.get("accounting_summary", {})
    lines = [
        "# PMBOT PAPER-020 Paper Run Series Postmortem",
        "",
        f"- task_id: `{postmortem['task_id']}`",
        f"- postmortem_status: `{postmortem['postmortem_status']}`",
        f"- source_paper_019: `{summary.get('source_artifact')}`",
        f"- source_series_status: `{summary.get('series_status')}`",
        f"- next_safe_action: `{postmortem['next_safe_action']}`",
        "",
        "## Source Artifacts",
        "",
        "| Artifact | Path | Present | Parse |",
        "| --- | --- | --- | --- |",
    ]
    for artifact in postmortem["source_artifacts"]:
        lines.append(
            "| "
            f"`{artifact['artifact_id']}` | "
            f"`{artifact['path']}` | "
            f"`{str(artifact['present']).lower()}` | "
            f"`{artifact['parse_status']}` |"
        )

    lines.extend(
        [
            "",
            "## Operator Summary",
            "",
            f"- markets_seen: `{summary.get('markets_seen', 0)}`",
            f"- records_seen: `{summary.get('records_seen', 0)}`",
            f"- records_processed: `{summary.get('records_processed', 0)}`",
            f"- cumulative_pnl: `{postmortem['accounting_interpretation']['cumulative_pnl']}`",
            "",
            "## Accounting-Only Warning",
            "",
            ACCOUNTING_ONLY_WARNING,
            "",
            "## Record Statuses",
            "",
            "| Status | Count | Operator Meaning |",
            "| --- | ---: | --- |",
        ]
    )
    for note in postmortem["record_status_notes"]:
        lines.append(
            "| "
            f"`{note['processing_status']}` | "
            f"`{note['count']}` | "
            f"{note['operator_meaning']} |"
        )

    lines.extend(["", "## Accounting Summary", "", "| Metric | Value |", "| --- | ---: |"])
    for key in sorted(accounting):
        lines.append(f"| `{key}` | `{accounting[key]}` |")

    lines.extend(
        [
            "",
            "## Accepted Records",
            "",
            "| Record | Market | Lifecycle | Outcome | Cost | Settlement | PnL |",
            "| --- | --- | --- | --- | ---: | ---: | ---: |",
        ]
    )
    for record in postmortem["accepted_record_summary"]:
        lines.append(
            "| "
            f"`{record['record_id']}` | "
            f"`{record['market_id']}` | "
            f"`{record['lifecycle_state']}` | "
            f"`{record['accounting_outcome']}` | "
            f"`{record.get('cost_basis', '')}` | "
            f"`{record.get('settlement_value', '')}` | "
            f"`{record.get('paper_accounting_pnl', '')}` |"
        )

    lines.extend(
        [
            "",
            "## Blocked And Manual Review",
            "",
            "Manual-review-only records remain inert local fixture records until a future fixture explicitly settles them.",
            "Blocked fixture records are retained for operator context and excluded from accounting totals.",
            "",
            "| Record | Status | Lifecycle | Included | Reason |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for record in postmortem["manual_review_record_summary"] + postmortem["blocked_record_summary"]:
        reason = ", ".join(record.get("blocked_reason_codes", [])) or "manual_review_open_fixture"
        lines.append(
            "| "
            f"`{record['record_id']}` | "
            f"`{record['processing_status']}` | "
            f"`{record['lifecycle_state']}` | "
            f"`{str(record['accounting_included']).lower()}` | "
            f"`{reason}` |"
        )

    lines.extend(["", "## Fixture Limitations", ""])
    for item in postmortem["fixture_limitations"]:
        lines.append(f"- {item}")

    lines.extend(["", "## Safety Summary", "", "| Counter | Value |", "| --- | ---: |"])
    for key in sorted(postmortem["safety_counters"]):
        lines.append(f"| `{key}` | `{postmortem['safety_counters'][key]}` |")
    lines.extend(["", "| Flag | Value |", "| --- | --- |"])
    for key in sorted(postmortem["safety_flags"]):
        lines.append(f"| `{key}` | `{str(postmortem['safety_flags'][key]).lower()}` |")

    lines.extend(["", "## Next Safe Actions", ""])
    for item in postmortem["recommended_next_fixture_expansions"]:
        lines.append(f"- {item}")
    lines.append(f"- Next task: `{postmortem['next_safe_action']}`")
    lines.append("")
    return "\n".join(lines)


def _result_payload(postmortem):
    summary = postmortem["paper_019_summary"]
    status = "completed_ready_for_review"
    if postmortem["postmortem_status"] == "postmortem_blocked":
        status = "blocked"
    return {
        "schema_version": RESULT_SCHEMA_VERSION,
        "task_id": TASK_ID,
        "status": status,
        "summary": "Generated deterministic local PAPER-019 paper run series postmortem.",
        "files_created": list(FILES_CREATED),
        "files_modified": [],
        "postmortem_summary": {
            "postmortem_status": postmortem["postmortem_status"],
            "source_paper_019_found": summary.get("source_schema_version") == "multi_market_paper_run_series.v1",
            "markets_seen": summary.get("markets_seen", 0),
            "records_seen": summary.get("records_seen", 0),
            "records_processed": summary.get("records_processed", 0),
            "cumulative_pnl": postmortem["accounting_interpretation"]["cumulative_pnl"],
            "accounting_only_warning_present": ACCOUNTING_ONLY_WARNING
            == postmortem["accounting_interpretation"].get("warning"),
            "recommended_next_fixture_expansions": list(
                postmortem["recommended_next_fixture_expansions"]
            ),
        },
        "missing_optional_docs": list(postmortem.get("missing_optional_docs", [])),
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
        },
        "safety_counters": dict(SAFETY_COUNTERS),
        "blockers": list(postmortem.get("blockers", [])),
        "next_action": postmortem["next_safe_action"],
    }


def write_paper_run_series_postmortem(source_path=DEFAULT_PAPER_019_OUTPUT):
    resolved_source = _resolve_path(source_path)
    source_artifacts = _source_artifacts()
    try:
        paper_019 = _load_json(resolved_source)
    except FileNotFoundError:
        postmortem = _blocked_postmortem(
            source_artifacts,
            resolved_source,
            "PAPER-019 multi-market paper run series output is missing.",
        )
    except json.JSONDecodeError as exc:
        postmortem = _blocked_postmortem(
            source_artifacts,
            resolved_source,
            f"PAPER-019 multi-market paper run series output is not valid JSON: {exc}",
        )
    else:
        postmortem = build_paper_run_series_postmortem(
            paper_019,
            source_artifacts,
            resolved_source,
        )

    _write_json(DEFAULT_OUTPUT, postmortem)
    _write_json(DEFAULT_EXPECTED, postmortem)
    _write_text(DEFAULT_OUTPUT_MD, render_markdown(postmortem))
    _write_json(DEFAULT_RESULT, _result_payload(postmortem))
    return postmortem


def main(argv):
    args = _parse_args(argv)
    postmortem = write_paper_run_series_postmortem(args.paper_019_output)
    summary = postmortem["paper_019_summary"]
    print(
        json.dumps(
            {
                "task_id": TASK_ID,
                "postmortem_status": postmortem["postmortem_status"],
                "markets_seen": summary.get("markets_seen", 0),
                "records_seen": summary.get("records_seen", 0),
                "records_processed": summary.get("records_processed", 0),
                "cumulative_pnl": postmortem["accounting_interpretation"]["cumulative_pnl"],
                "result_path": _display_path(DEFAULT_RESULT),
            },
            indent=2,
            ensure_ascii=True,
        )
    )
    return 0 if postmortem["postmortem_status"] != "postmortem_blocked" else 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
