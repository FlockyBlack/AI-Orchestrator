import argparse
import json
import sys
from decimal import Decimal, InvalidOperation
from pathlib import Path


TASK_ID = "PMBOT-PAPER-019-MULTI-MARKET-PAPER-RUN-SERIES"
SCHEMA_VERSION = "multi_market_paper_run_series.v1"
MARKDOWN_VERSION = "multi_market_paper_run_series_markdown.v1"
GENERATED_BY = "pm_bot/paper/run_multi_market_paper_run_series.py"
RUN_MODE = "deterministic_offline_fixture"

ROOT = Path(__file__).resolve().parents[2]
PAPER_DIR = ROOT / "pm_bot" / "paper"
DOCS_DIR = ROOT / "docs"

DEFAULT_FIXTURE = PAPER_DIR / "paper_run_series_fixture.v1.json"
DEFAULT_OUTPUT = PAPER_DIR / "multi_market_paper_run_series.v1.json"
DEFAULT_OUTPUT_MD = PAPER_DIR / "multi_market_paper_run_series.v1.md"
DEFAULT_EXPECTED = PAPER_DIR / "expected_multi_market_paper_run_series.v1.json"
DEFAULT_RESULT = DOCS_DIR / "PMBOT_PAPER_019_RESULT.json"

FILES_CREATED = [
    "pm_bot/paper/paper_run_series_fixture.v1.json",
    "pm_bot/paper/run_multi_market_paper_run_series.py",
    "pm_bot/paper/multi_market_paper_run_series.v1.json",
    "pm_bot/paper/multi_market_paper_run_series.v1.md",
    "pm_bot/paper/expected_multi_market_paper_run_series.v1.json",
    "pm_bot/paper/tests/test_multi_market_paper_run_series.py",
    "docs/PMBOT_PAPER_019_RESULT.json",
]

ALLOWED_PROCESSING_STATUSES = {
    "accepted_accounting_record",
    "manual_review_only",
    "blocked_fixture_record",
}
ALLOWED_LIFECYCLE_STATES = {"settled", "open", "blocked"}
PROCESSABLE_STATUSES = {"accepted_accounting_record", "manual_review_only"}

REQUIRED_TRUE_RECORD_FLAGS = {
    "paper_only",
    "inert_only",
    "paper_accounting_only",
    "operator_manual_source_lineage",
}
REQUIRED_FALSE_RECORD_FLAGS = {
    "generated_by_bot",
    "live_order_created",
    "real_order_created",
    "autonomous_paper_order_created",
    "network_used",
    "api_used",
    "wallet_used",
}

PROHIBITED_ACTIVE_FIELD_NAMES = {
    "probability",
    "implied_probability",
    "fair_probability",
    "ev",
    "expected_value",
    "edge",
    "score",
    "confidence_score",
    "sharpe",
    "kelly",
    "recommendation",
    "trade_recommendation",
    "decision",
    "trade_decision",
    "bot_decision",
    "generated_side",
    "generated_outcome",
    "generated_price",
    "generated_size",
    "auto_side",
    "auto_outcome",
    "auto_price",
    "auto_size",
    "orderbook",
    "api_price",
    "live_price",
    "wallet",
    "private_key",
    "api_key",
    "auth",
    "trading_endpoint",
    "market_decision",
}

SAFETY_FIELD_EXEMPTIONS = {
    "api_used",
    "autonomous_decisions",
    "autonomous_paper_order_created",
    "autonomous_paper_orders",
    "commands_executed",
    "live_order_created",
    "network_calls",
    "network_used",
    "paper_orders_created",
    "real_order_created",
    "real_orders_created",
    "wallet_used",
}

SAFETY_FLAGS = {
    "offline_only": True,
    "deterministic": True,
    "fixture_only": True,
    "paper_only": True,
    "manual_review_only": True,
    "paper_accounting_only": True,
    "local_file_reads_only": True,
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
}


def _parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Run deterministic offline PMBOT PAPER-019 multi-market paper run series."
    )
    parser.add_argument("--fixture", default=str(DEFAULT_FIXTURE))
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


def _decimal_from_value(value):
    if value is None or isinstance(value, bool):
        return None
    try:
        number = Decimal(str(value).strip())
    except (InvalidOperation, ValueError, AttributeError):
        return None
    if not number.is_finite():
        return None
    return number


def _format_decimal(value):
    number = Decimal(value).quantize(Decimal("0.01"))
    if number == Decimal("-0.00"):
        number = Decimal("0.00")
    return format(number, ".2f")


def _field_tokens(key):
    lower = str(key).lower()
    parts = [part for part in lower.replace("-", "_").replace("/", "_").split("_") if part]
    tokens = {lower}
    tokens.update(parts)
    for index in range(len(parts) - 1):
        tokens.add(f"{parts[index]}_{parts[index + 1]}")
    for index in range(len(parts) - 2):
        tokens.add(f"{parts[index]}_{parts[index + 1]}_{parts[index + 2]}")
    return tokens


def _walk_keys(value, prefix=""):
    if isinstance(value, dict):
        for key, nested in value.items():
            key_text = str(key)
            path = f"{prefix}.{key_text}" if prefix else key_text
            yield key_text, path
            yield from _walk_keys(nested, path)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from _walk_keys(item, f"{prefix}[{index}]")


def _find_prohibited_active_fields(payload):
    blocked = []
    for key, path in _walk_keys(payload):
        if key in SAFETY_FIELD_EXEMPTIONS:
            continue
        if path.startswith("safety_flags.") or ".safety_flags." in path:
            continue
        if PROHIBITED_ACTIVE_FIELD_NAMES.intersection(_field_tokens(key)):
            blocked.append(path)
    return sorted(blocked)


def _fixture_records(fixture):
    records = fixture.get("records")
    if not isinstance(records, list):
        return []
    return sorted(
        [record for record in records if isinstance(record, dict)],
        key=lambda record: (record.get("sequence", 0), str(record.get("record_id", ""))),
    )


def _count_by(records, field):
    counts = {}
    for record in records:
        value = str(record.get(field))
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items()))


def _market_ids(records):
    return sorted({str(record.get("market_id")) for record in records if record.get("market_id")})


def _processable_records(records):
    return [record for record in records if record.get("processing_status") in PROCESSABLE_STATUSES]


def _blocked_records(records):
    return [record for record in records if record.get("processing_status") not in PROCESSABLE_STATUSES]


def _record_summary(record, accounting_included):
    row = {
        "record_id": record.get("record_id"),
        "market_id": record.get("market_id"),
        "processing_status": record.get("processing_status"),
        "lifecycle_state": record.get("lifecycle_state"),
        "accounting_outcome": record.get("accounting_outcome"),
        "paper_position_status": record.get("paper_position_status"),
        "accounting_included": accounting_included,
        "paper_orders_created": 0,
        "real_orders_created": 0,
        "network_calls": 0,
        "commands_executed": 0,
        "autonomous_decisions": 0,
    }
    if record.get("blocked_reason_codes") is not None:
        row["blocked_reason_codes"] = list(record.get("blocked_reason_codes") or [])
    if accounting_included:
        row["cost_basis"] = _format_decimal(_decimal_from_value(record.get("cost_basis")) or Decimal("0"))
        row["settlement_value"] = _format_decimal(
            _decimal_from_value(record.get("settlement_value")) or Decimal("0")
        )
        row["paper_accounting_pnl"] = _format_decimal(
            _decimal_from_value(record.get("paper_accounting_pnl")) or Decimal("0")
        )
    return row


def _accounting_summary(records):
    processed = _processable_records(records)
    settled = [record for record in processed if record.get("lifecycle_state") == "settled"]
    open_records = [record for record in processed if record.get("lifecycle_state") == "open"]
    cost_basis = [_decimal_from_value(record.get("cost_basis")) or Decimal("0") for record in processed]
    settlement_values = [
        _decimal_from_value(record.get("settlement_value")) or Decimal("0") for record in processed
    ]
    pnl_values = [
        _decimal_from_value(record.get("paper_accounting_pnl")) or Decimal("0") for record in processed
    ]
    settled_pnl = [
        _decimal_from_value(record.get("paper_accounting_pnl")) or Decimal("0") for record in settled
    ]
    positive = [value for value in pnl_values if value > 0]
    negative = [value for value in pnl_values if value < 0]
    settled_flat = [
        record
        for record in settled
        if (_decimal_from_value(record.get("paper_accounting_pnl")) or Decimal("0")) == Decimal("0")
    ]
    average_settled = sum(settled_pnl, Decimal("0")) / Decimal(len(settled_pnl)) if settled_pnl else Decimal("0")
    return {
        "paper_accounting_total_records": len(processed),
        "paper_accounting_settled_count": len(settled),
        "paper_accounting_open_count": len(open_records),
        "paper_accounting_win_count": len([value for value in settled_pnl if value > 0]),
        "paper_accounting_loss_count": len([value for value in settled_pnl if value < 0]),
        "paper_accounting_flat_count": len(settled_flat),
        "paper_accounting_total_cost_basis": _format_decimal(sum(cost_basis, Decimal("0"))),
        "paper_accounting_settled_cost_basis": _format_decimal(
            sum((_decimal_from_value(record.get("cost_basis")) or Decimal("0")) for record in settled)
        ),
        "paper_accounting_open_cost_basis": _format_decimal(
            sum((_decimal_from_value(record.get("cost_basis")) or Decimal("0")) for record in open_records)
        ),
        "paper_accounting_total_settlement_value": _format_decimal(
            sum(settlement_values, Decimal("0"))
        ),
        "paper_accounting_cumulative_pnl": _format_decimal(sum(pnl_values, Decimal("0"))),
        "paper_accounting_average_settled_pnl": _format_decimal(average_settled),
        "paper_accounting_gross_profit": _format_decimal(sum(positive, Decimal("0"))),
        "paper_accounting_gross_loss": _format_decimal(sum(negative, Decimal("0"))),
        "paper_accounting_max_gain": _format_decimal(max(pnl_values) if pnl_values else Decimal("0")),
        "paper_accounting_max_loss": _format_decimal(min(pnl_values) if pnl_values else Decimal("0")),
    }


def _portfolio_summary(records):
    processed = _processable_records(records)
    settled = [record for record in processed if record.get("lifecycle_state") == "settled"]
    open_records = [record for record in processed if record.get("lifecycle_state") == "open"]
    realized = sum(
        (_decimal_from_value(record.get("paper_accounting_pnl")) or Decimal("0")) for record in settled
    )
    unrealized = sum(
        (_decimal_from_value(record.get("paper_accounting_pnl")) or Decimal("0")) for record in open_records
    )
    return {
        "portfolio_summary_status": "deterministic_fixture_accounting_summary_ready",
        "paper_positions_seen": len(processed),
        "open_paper_positions": len(open_records),
        "settled_paper_positions": len(settled),
        "blocked_records_not_in_portfolio": len(_blocked_records(records)),
        "realized_paper_pnl": _format_decimal(realized),
        "unrealized_paper_pnl": _format_decimal(unrealized),
        "paper_orders_created": 0,
        "real_orders_created": 0,
    }


def _check(status, check_id, summary, expected=None, actual=None):
    return {
        "check_id": check_id,
        "status": status,
        "summary": summary,
        "expected": expected,
        "actual": actual,
    }


def _fixture_metadata_failures(fixture):
    failures = []
    if fixture.get("schema_version") != "paper_run_series_fixture.v1":
        failures.append("schema_version")
    if fixture.get("task_id") != TASK_ID:
        failures.append("task_id")
    if fixture.get("run_mode") != RUN_MODE:
        failures.append("run_mode")
    for key in ("deterministic", "fixture_only", "offline_only", "paper_only", "paper_accounting_only"):
        if fixture.get(key) is not True:
            failures.append(key)
    safety = fixture.get("safety_flags")
    if not isinstance(safety, dict):
        failures.append("safety_flags")
    else:
        for key, expected in SAFETY_FLAGS.items():
            if safety.get(key) is not expected:
                failures.append(f"safety_flags.{key}")
    return failures


def _record_shape_failures(records):
    failures = []
    seen_ids = set()
    for index, record in enumerate(records):
        label = record.get("record_id") or f"records[{index}]"
        record_id = record.get("record_id")
        if not record_id or record_id in seen_ids:
            failures.append(f"{label}:record_id")
        seen_ids.add(record_id)
        if not record.get("market_id"):
            failures.append(f"{label}:market_id")
        if record.get("processing_status") not in ALLOWED_PROCESSING_STATUSES:
            failures.append(f"{label}:processing_status")
        if record.get("lifecycle_state") not in ALLOWED_LIFECYCLE_STATES:
            failures.append(f"{label}:lifecycle_state")
        for key in REQUIRED_TRUE_RECORD_FLAGS:
            if record.get(key) is not True:
                failures.append(f"{label}:{key}")
        for key in REQUIRED_FALSE_RECORD_FLAGS:
            if record.get(key) is not False:
                failures.append(f"{label}:{key}")
        if record.get("commands_executed") != 0:
            failures.append(f"{label}:commands_executed")
    return sorted(failures)


def _accounting_failures(records):
    failures = []
    for record in _processable_records(records):
        label = record["record_id"]
        cost = _decimal_from_value(record.get("cost_basis"))
        settlement = _decimal_from_value(record.get("settlement_value"))
        pnl = _decimal_from_value(record.get("paper_accounting_pnl"))
        if cost is None or settlement is None or pnl is None:
            failures.append(f"{label}:accounting_value_missing_or_invalid")
            continue
        if cost < 0 or settlement < 0:
            failures.append(f"{label}:negative_cost_or_settlement")
        if record.get("lifecycle_state") == "settled":
            expected_pnl = settlement - cost
            if pnl != expected_pnl:
                failures.append(f"{label}:settled_pnl_mismatch")
        elif record.get("lifecycle_state") == "open":
            if settlement != Decimal("0") or pnl != Decimal("0"):
                failures.append(f"{label}:open_record_not_flat_accounting")
        else:
            failures.append(f"{label}:processable_record_not_open_or_settled")
    for record in _blocked_records(records):
        if record.get("cost_basis") is not None or record.get("paper_accounting_pnl") is not None:
            failures.append(f"{record.get('record_id')}:blocked_record_has_accounting_values")
    return sorted(failures)


def _coverage_failures(records, accounting):
    failures = []
    market_count = len(_market_ids(records))
    status_counts = _count_by(records, "processing_status")
    lifecycle_counts = _count_by(records, "lifecycle_state")
    if market_count < 3:
        failures.append("markets_seen_below_3")
    for status in ("accepted_accounting_record", "manual_review_only", "blocked_fixture_record"):
        if status_counts.get(status, 0) < 1:
            failures.append(f"missing_status:{status}")
    for state in ("settled", "open", "blocked"):
        if lifecycle_counts.get(state, 0) < 1:
            failures.append(f"missing_lifecycle:{state}")
    if accounting["paper_accounting_win_count"] < 1:
        failures.append("missing_positive_accounting_example")
    if accounting["paper_accounting_loss_count"] + accounting["paper_accounting_flat_count"] < 1:
        failures.append("missing_negative_or_flat_accounting_example")
    return failures


def _expected_summary_failures(fixture, summary):
    expected = fixture.get("expected_summary")
    if not isinstance(expected, dict):
        return ["expected_summary_missing"]
    failures = []
    for key in ("markets_seen", "records_seen", "records_processed", "records_by_status"):
        if expected.get(key) != summary.get(key):
            failures.append(key)
    if expected.get("accounting_summary") != summary.get("accounting_summary"):
        failures.append("accounting_summary")
    return failures


def _build_checks(fixture, records, summary):
    prohibited_fields = _find_prohibited_active_fields(fixture)
    metadata_failures = _fixture_metadata_failures(fixture)
    shape_failures = _record_shape_failures(records)
    accounting_failures = _accounting_failures(records)
    coverage_failures = _coverage_failures(records, summary["accounting_summary"])
    expected_failures = _expected_summary_failures(fixture, summary)
    return [
        _check(
            "pass" if not metadata_failures else "fail",
            "fixture_metadata_safety",
            "Fixture metadata and safety flags remain deterministic, offline, and paper-only.",
            expected=[],
            actual=metadata_failures,
        ),
        _check(
            "pass" if not shape_failures else "fail",
            "record_shape_and_safety",
            "Series records use allowed statuses and preserve inert per-record safety flags.",
            expected=[],
            actual=shape_failures,
        ),
        _check(
            "pass" if not coverage_failures else "fail",
            "multi_market_lifecycle_coverage",
            "Fixture covers multiple markets, accepted/manual/blocked paths, and open/settled accounting examples.",
            expected=[],
            actual=coverage_failures,
        ),
        _check(
            "pass" if not accounting_failures else "fail",
            "fixture_accounting_consistency",
            "Accounting totals are computed from explicit fixture cost, settlement, and PnL fields only.",
            expected=[],
            actual=accounting_failures,
        ),
        _check(
            "pass" if not prohibited_fields else "fail",
            "no_scoring_probability_ev_edge_or_market_decision_fields",
            "Series fixture contains no active scoring, probability, EV, edge, recommendation, or market-decision fields.",
            expected=[],
            actual=prohibited_fields,
        ),
        _check(
            "pass" if not expected_failures else "fail",
            "fixture_expected_summary_alignment",
            "Fixture-declared expected summary matches the deterministic computed series output.",
            expected=[],
            actual=expected_failures,
        ),
    ]


def build_multi_market_paper_run_series(fixture, fixture_path=DEFAULT_FIXTURE):
    records = _fixture_records(fixture)
    processed = _processable_records(records)
    blocked = _blocked_records(records)
    accounting = _accounting_summary(records)
    status_counts = _count_by(records, "processing_status")
    lifecycle_counts = _count_by(records, "lifecycle_state")
    summary = {
        "markets_seen": len(_market_ids(records)),
        "records_seen": len(records),
        "records_processed": len(processed),
        "records_by_status": status_counts,
        "accounting_summary": accounting,
    }
    checks = _build_checks(fixture, records, summary)
    failed_checks = [check for check in checks if check["status"] == "fail"]
    warnings = []
    if blocked:
        warnings.append("Blocked fixture records were retained as inert non-accounting records.")
    series_status = "series_run_passed" if not failed_checks else "series_run_blocked"
    return {
        "schema_version": SCHEMA_VERSION,
        "markdown_version": MARKDOWN_VERSION,
        "task_id": TASK_ID,
        "generated_by": GENERATED_BY,
        "run_mode": RUN_MODE,
        "fixture_path": _display_path(fixture_path),
        "fixture_id": fixture.get("fixture_id"),
        "series_status": series_status,
        "markets_seen": summary["markets_seen"],
        "market_ids": _market_ids(records),
        "records_seen": summary["records_seen"],
        "records_processed": summary["records_processed"],
        "records_by_status": status_counts,
        "accounting_summary": accounting,
        "portfolio_summary": _portfolio_summary(records),
        "lifecycle_summary": {
            "records_by_lifecycle_state": lifecycle_counts,
            "settled_records": lifecycle_counts.get("settled", 0),
            "open_records": lifecycle_counts.get("open", 0),
            "blocked_records": lifecycle_counts.get("blocked", 0),
            "accepted_records": status_counts.get("accepted_accounting_record", 0),
            "manual_review_only_records": status_counts.get("manual_review_only", 0),
            "blocked_or_rejected_records": len(blocked),
        },
        "record_summaries": [_record_summary(record, record in processed) for record in records],
        "rejected_or_blocked_records": [_record_summary(record, False) for record in blocked],
        "checks": checks,
        "mismatches": failed_checks,
        "warnings": warnings,
        "safety_flags": dict(SAFETY_FLAGS),
        "paper_orders_created": 0,
        "real_orders_created": 0,
        "network_calls": 0,
        "commands_executed": 0,
        "autonomous_decisions": 0,
        "next_safe_action": (
            "ready_for_operator_workbench_visibility_review"
            if series_status == "series_run_passed"
            else "requires_operator_review"
        ),
    }


def render_markdown(report):
    accounting = report["accounting_summary"]
    portfolio = report["portfolio_summary"]
    lines = [
        "# PMBOT PAPER-019 Multi-Market Paper Run Series",
        "",
        f"- task_id: `{report['task_id']}`",
        f"- series_status: `{report['series_status']}`",
        f"- run_mode: `{report['run_mode']}`",
        f"- fixture_path: `{report['fixture_path']}`",
        f"- markets_seen: `{report['markets_seen']}`",
        f"- records_seen: `{report['records_seen']}`",
        f"- records_processed: `{report['records_processed']}`",
        f"- paper_orders_created: `{report['paper_orders_created']}`",
        f"- real_orders_created: `{report['real_orders_created']}`",
        f"- network_calls: `{report['network_calls']}`",
        f"- commands_executed: `{report['commands_executed']}`",
        f"- autonomous_decisions: `{report['autonomous_decisions']}`",
        f"- next_safe_action: `{report['next_safe_action']}`",
        "",
        "## Accounting Summary",
        "",
        "| Metric | Value |",
        "| --- | ---: |",
    ]
    for key in sorted(accounting):
        lines.append(f"| `{key}` | `{accounting[key]}` |")
    lines.extend(
        [
            "",
            "## Portfolio Summary",
            "",
            "| Metric | Value |",
            "| --- | ---: |",
        ]
    )
    for key in sorted(portfolio):
        lines.append(f"| `{key}` | `{portfolio[key]}` |")
    lines.extend(
        [
            "",
            "## Records",
            "",
            "| Record | Market | Status | Lifecycle | Outcome | Included | PnL |",
            "| --- | --- | --- | --- | --- | --- | ---: |",
        ]
    )
    for record in report["record_summaries"]:
        lines.append(
            "| "
            f"`{record['record_id']}` | "
            f"`{record['market_id']}` | "
            f"`{record['processing_status']}` | "
            f"`{record['lifecycle_state']}` | "
            f"`{record['accounting_outcome']}` | "
            f"`{str(record['accounting_included']).lower()}` | "
            f"`{record.get('paper_accounting_pnl', '')}` |"
        )
    lines.extend(
        [
            "",
            "## Checks",
            "",
            "| Check | Status | Details |",
            "| --- | --- | --- |",
        ]
    )
    for check in report["checks"]:
        details = "none" if not check["actual"] else json.dumps(check["actual"], sort_keys=True)
        lines.append(f"| `{check['check_id']}` | `{check['status']}` | `{details}` |")
    lines.extend(
        [
            "",
            "## Safety",
            "",
            "| Flag | Value |",
            "| --- | --- |",
        ]
    )
    for key in sorted(report["safety_flags"]):
        lines.append(f"| `{key}` | `{str(report['safety_flags'][key]).lower()}` |")
    lines.append("")
    return "\n".join(lines)


def _result_payload(report):
    completed = report["series_status"] == "series_run_passed"
    return {
        "schema_version": "paper_019_result.v1",
        "task_id": TASK_ID,
        "status": "completed_ready_for_review" if completed else "blocked",
        "summary": (
            "Implemented deterministic offline multi-market paper run series."
            if completed
            else "Multi-market paper run series found fixture or safety mismatches."
        ),
        "series_status": report["series_status"],
        "files_created": list(FILES_CREATED),
        "files_modified": [],
        "series_summary": {
            "markets_seen": report["markets_seen"],
            "records_seen": report["records_seen"],
            "records_processed": report["records_processed"],
            "records_by_status": report["records_by_status"],
            "accounting_summary": report["accounting_summary"],
        },
        "tests": [],
        "warnings": report["warnings"],
        "missing_optional_docs": [],
        "safety": {
            "offline_only": True,
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
        },
        "paper_orders_created": 0,
        "real_orders_created": 0,
        "network_calls": 0,
        "commands_executed": 0,
        "autonomous_decisions": 0,
        "blockers": [] if completed else ["fixture or safety mismatches require operator review"],
        "next_action": report["next_safe_action"],
    }


def write_multi_market_paper_run_series(fixture_path=DEFAULT_FIXTURE):
    resolved_fixture = _resolve_path(fixture_path)
    fixture = _load_json(resolved_fixture)
    report = build_multi_market_paper_run_series(fixture, resolved_fixture)
    _write_json(DEFAULT_OUTPUT, report)
    _write_json(DEFAULT_EXPECTED, report)
    _write_text(DEFAULT_OUTPUT_MD, render_markdown(report))
    _write_json(DEFAULT_RESULT, _result_payload(report))
    return report


def _blocked_result(exc, fixture_path):
    return {
        "schema_version": "paper_019_result.v1",
        "task_id": TASK_ID,
        "status": "blocked",
        "summary": "Blocked before completing deterministic offline multi-market paper run series.",
        "series_status": "series_run_blocked",
        "fixture_path": _display_path(fixture_path),
        "files_created": list(FILES_CREATED),
        "files_modified": [],
        "series_summary": {
            "markets_seen": 0,
            "records_seen": 0,
            "records_processed": 0,
            "records_by_status": {},
            "accounting_summary": {},
        },
        "tests": [],
        "warnings": [],
        "missing_optional_docs": [],
        "safety": {
            "offline_only": True,
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
        },
        "paper_orders_created": 0,
        "real_orders_created": 0,
        "network_calls": 0,
        "commands_executed": 0,
        "autonomous_decisions": 0,
        "blockers": [str(exc)],
        "next_action": "requires_operator_review",
    }


def main(argv):
    args = _parse_args(argv)
    fixture_path = _resolve_path(args.fixture)
    try:
        report = write_multi_market_paper_run_series(fixture_path)
    except Exception as exc:
        blocked = _blocked_result(exc, fixture_path)
        _write_json(DEFAULT_RESULT, blocked)
        print(json.dumps({"task_id": TASK_ID, "status": "blocked", "blockers": [str(exc)]}, indent=2))
        return 2
    print(
        json.dumps(
            {
                "task_id": TASK_ID,
                "series_status": report["series_status"],
                "markets_seen": report["markets_seen"],
                "records_seen": report["records_seen"],
                "records_processed": report["records_processed"],
                "paper_orders_created": report["paper_orders_created"],
                "real_orders_created": report["real_orders_created"],
                "network_calls": report["network_calls"],
                "commands_executed": report["commands_executed"],
                "autonomous_decisions": report["autonomous_decisions"],
                "result_path": _display_path(DEFAULT_RESULT),
            },
            indent=2,
            ensure_ascii=True,
        )
    )
    return 0 if report["series_status"] == "series_run_passed" else 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
