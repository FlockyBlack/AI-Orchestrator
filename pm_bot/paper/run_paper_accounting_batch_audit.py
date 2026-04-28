import argparse
import json
import sys
from decimal import Decimal, InvalidOperation
from pathlib import Path


TASK_ID = "PMBOT-PAPER-018-MULTI-RECORD-PAPER-ACCOUNTING-BATCH-AUDIT"
ROOT = Path(__file__).resolve().parents[2]
PAPER_DIR = ROOT / "pm_bot" / "paper"
DOCS_DIR = ROOT / "docs"

DEFAULT_AUDIT = PAPER_DIR / "paper_accounting_batch_audit.v1.json"
DEFAULT_AUDIT_MD = PAPER_DIR / "paper_accounting_batch_audit.v1.md"
DEFAULT_AUDIT_EXPECTED = PAPER_DIR / "expected_paper_accounting_batch_audit.v1.json"
DEFAULT_RESULT = DOCS_DIR / "PMBOT_PAPER_018_RESULT.json"
DEFAULT_LANE_RESULT = DOCS_DIR / "PMBOT_CODEX_A_ROUND002_RESULT.json"

OPTIONAL_DOCS = (
    "docs/PMBOT_INFRA_008_RESULT.json",
    "docs/PMBOT_INFRA_008_ABC_ROUND002_SCOPE_AND_WORKTREE_PLAN.md",
)

SOURCE_ARTIFACTS = (
    ("paper_fill_events", "pm_bot/paper/paper_fill_events.v1.json", "paper_fill_events"),
    ("paper_settlement_sources_accepted", "pm_bot/paper/paper_settlement_sources_accepted.v1.json", "records"),
    ("paper_accounting_pnl_preview", "pm_bot/paper/paper_accounting_pnl_preview.v1.json", "paper_accounting_records"),
    ("paper_accounting_ledger", "pm_bot/paper/paper_accounting_ledger.v1.json", "paper_accounting_ledger_entries"),
    ("paper_portfolio_snapshot", "pm_bot/paper/paper_portfolio_snapshot.v1.json", "positions"),
    ("paper_metrics_report", "pm_bot/paper/paper_metrics_report.v1.json", None),
    (
        "paper_accounting_reconciliation_audit",
        "pm_bot/paper/paper_accounting_reconciliation_audit.v1.json",
        None,
    ),
)

EXPECTED_SOURCE_POINTERS = (
    (
        "paper_fill_events",
        ("source_fill_sources_accepted_path",),
        "pm_bot/paper/paper_fill_sources_accepted.v1.json",
    ),
    (
        "paper_settlement_sources_accepted",
        ("source_paper_fill_events_path",),
        "pm_bot/paper/paper_fill_events.v1.json",
    ),
    (
        "paper_settlement_sources_accepted",
        ("input_path",),
        "pm_bot/paper/paper_settlement_source_fixture.v1.json",
    ),
    (
        "paper_accounting_pnl_preview",
        ("source_paper_fill_events_path",),
        "pm_bot/paper/paper_fill_events.v1.json",
    ),
    (
        "paper_accounting_pnl_preview",
        ("source_paper_settlement_sources_accepted_path",),
        "pm_bot/paper/paper_settlement_sources_accepted.v1.json",
    ),
    (
        "paper_accounting_ledger",
        ("source_paper_accounting_pnl_preview_path",),
        "pm_bot/paper/paper_accounting_pnl_preview.v1.json",
    ),
    (
        "paper_accounting_ledger",
        ("source_paper_fill_events_path",),
        "pm_bot/paper/paper_fill_events.v1.json",
    ),
    (
        "paper_accounting_ledger",
        ("source_manual_paper_intent_ledger_path",),
        "pm_bot/paper/manual_paper_intent_ledger.v1.json",
    ),
    (
        "paper_portfolio_snapshot",
        ("source_paper_accounting_ledger_path",),
        "pm_bot/paper/paper_accounting_ledger.v1.json",
    ),
    (
        "paper_metrics_report",
        ("source_paper_accounting_ledger_path",),
        "pm_bot/paper/paper_accounting_ledger.v1.json",
    ),
    (
        "paper_metrics_report",
        ("source_paper_portfolio_snapshot_path",),
        "pm_bot/paper/paper_portfolio_snapshot.v1.json",
    ),
)

EXPECTED_BATCH_POINTERS = {
    "source_paper_fill_events_path": "pm_bot/paper/paper_fill_events.v1.json",
    "source_paper_settlement_sources_accepted_path": "pm_bot/paper/paper_settlement_sources_accepted.v1.json",
    "source_paper_accounting_pnl_preview_path": "pm_bot/paper/paper_accounting_pnl_preview.v1.json",
    "source_paper_accounting_ledger_path": "pm_bot/paper/paper_accounting_ledger.v1.json",
    "source_paper_portfolio_snapshot_path": "pm_bot/paper/paper_portfolio_snapshot.v1.json",
    "source_paper_metrics_report_path": "pm_bot/paper/paper_metrics_report.v1.json",
    "source_paper_accounting_reconciliation_audit_path": (
        "pm_bot/paper/paper_accounting_reconciliation_audit.v1.json"
    ),
}

REQUIRED_RECORD_FLAGS = {
    "paper_only": True,
    "inert_only": True,
    "paper_accounting_only": True,
    "generated_by_bot": False,
    "live_order_created": False,
    "real_order_created": False,
}

REQUIRED_SAFETY_FLAGS = (
    "paper_only",
    "inert_only",
    "paper_accounting_only",
    "operator_manual_source_lineage",
    "no_live_execution",
    "no_real_execution",
    "no_credential_or_endpoint_use",
)

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
    "real_order_created",
    "live_order_created",
    "real_orders_created",
    "live_orders_created",
    "autonomous_paper_orders_created",
}

FILES_CREATED = [
    "pm_bot/paper/run_paper_accounting_batch_audit.py",
    "pm_bot/paper/paper_accounting_batch_audit.v1.json",
    "pm_bot/paper/paper_accounting_batch_audit.v1.md",
    "pm_bot/paper/expected_paper_accounting_batch_audit.v1.json",
    "pm_bot/paper/tests/test_paper_accounting_batch_audit.py",
    "docs/PMBOT_PAPER_018_RESULT.json",
    "docs/PMBOT_CODEX_A_ROUND002_RESULT.json",
]


def _parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Run deterministic offline PMBOT PAPER-018 paper accounting batch audit."
    )
    return parser.parse_args(argv)


def _resolve_path(path):
    value = Path(path)
    if value.is_absolute():
        return value
    return ROOT / value


def _display_path(path):
    resolved = Path(path).resolve()
    try:
        return str(resolved.relative_to(ROOT.resolve())).replace("\\", "/")
    except ValueError:
        return str(resolved).replace("\\", "/")


def _load_json(path):
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def _write_text(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _records(payload, field):
    if field is None:
        return []
    records = payload.get(field)
    if not isinstance(records, list):
        return []
    return [record for record in records if isinstance(record, dict)]


def _load_artifacts():
    artifacts = {}
    for artifact_id, path, record_field in SOURCE_ARTIFACTS:
        resolved = _resolve_path(path)
        if not resolved.exists():
            raise FileNotFoundError(f"missing required paper artifact: {path}")
        artifacts[artifact_id] = {
            "artifact_id": artifact_id,
            "path": path,
            "record_field": record_field,
            "payload": _load_json(resolved),
        }
    return artifacts


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


def _nested(payload, path):
    value = payload
    for part in path:
        if isinstance(part, int):
            if not isinstance(value, list) or part >= len(value):
                return None
            value = value[part]
        else:
            if not isinstance(value, dict) or part not in value:
                return None
            value = value[part]
    return value


def _counts(payload):
    counts = payload.get("counts")
    if isinstance(counts, dict):
        return counts
    return {}


def _source_records(artifacts, artifact_id):
    artifact = artifacts[artifact_id]
    return _records(artifact["payload"], artifact["record_field"])


def _first_source_record(artifacts, artifact_id):
    records = _source_records(artifacts, artifact_id)
    if not records:
        raise ValueError(f"required source artifact has no records: {artifact_id}")
    return records[0]


def _safe_decimal_string(value, default="0.00"):
    number = _decimal_from_value(value)
    if number is None:
        return default
    return _format_decimal(number)


def _paper_accounting_record(
    batch_record_id,
    market_id,
    source_origin,
    source_manual_intent_id,
    source_ledger_entry_id,
    paper_fill_event_id,
    settlement_source_id,
    paper_accounting_record_id,
    paper_accounting_ledger_entry_id,
    operator_manual_fill_price,
    operator_manual_fill_size,
    operator_manual_settlement_price,
    paper_accounting_status,
    paper_accounting_entry_status,
    paper_position_status,
    cost_basis,
    settlement_value,
    pnl,
    cumulative_pnl,
):
    settlement_market_id = market_id if settlement_source_id is not None else None
    return {
        "batch_record_id": batch_record_id,
        "market_id": market_id,
        "source_origin": source_origin,
        "fill_market_id": market_id,
        "settlement_market_id": settlement_market_id,
        "accounting_market_id": market_id,
        "ledger_market_id": market_id,
        "portfolio_market_id": market_id,
        "source_manual_intent_id": source_manual_intent_id,
        "source_ledger_entry_id": source_ledger_entry_id,
        "paper_fill_event_id": paper_fill_event_id,
        "settlement_source_id": settlement_source_id,
        "paper_accounting_record_id": paper_accounting_record_id,
        "paper_accounting_ledger_entry_id": paper_accounting_ledger_entry_id,
        "portfolio_source_paper_accounting_ledger_entry_id": paper_accounting_ledger_entry_id,
        "accounting_source_paper_fill_event_id": paper_fill_event_id,
        "accounting_source_settlement_id": settlement_source_id,
        "ledger_source_paper_fill_event_id": paper_fill_event_id,
        "ledger_source_settlement_id": settlement_source_id,
        "ledger_source_paper_accounting_record_id": paper_accounting_record_id,
        "operator_manual_fill_price": _format_decimal(operator_manual_fill_price),
        "operator_manual_fill_size": _format_decimal(operator_manual_fill_size),
        "operator_manual_settlement_price": (
            _format_decimal(operator_manual_settlement_price)
            if operator_manual_settlement_price is not None
            else None
        ),
        "paper_accounting_status": paper_accounting_status,
        "paper_accounting_entry_status": paper_accounting_entry_status,
        "paper_position_status": paper_position_status,
        "paper_accounting_cost_basis": _format_decimal(cost_basis),
        "paper_accounting_settlement_value": _format_decimal(settlement_value),
        "paper_accounting_pnl": _format_decimal(pnl),
        "paper_accounting_cumulative_pnl": _format_decimal(cumulative_pnl),
        "source_references": dict(EXPECTED_BATCH_POINTERS),
        "paper_accounting_only": True,
        "paper_only": True,
        "inert_only": True,
        "generated_by_bot": False,
        "live_order_created": False,
        "real_order_created": False,
        "safety_flags": list(REQUIRED_SAFETY_FLAGS),
    }


def _build_batch_input(artifacts):
    fill = _first_source_record(artifacts, "paper_fill_events")
    settlement = _first_source_record(artifacts, "paper_settlement_sources_accepted")
    preview = _first_source_record(artifacts, "paper_accounting_pnl_preview")
    ledger = _first_source_record(artifacts, "paper_accounting_ledger")

    record_001 = _paper_accounting_record(
        batch_record_id="paper-accounting-batch-record-001",
        market_id=str(preview["market_id"]),
        source_origin="existing_paper_017_record",
        source_manual_intent_id=str(preview["source_manual_intent_id"]),
        source_ledger_entry_id=str(preview["source_ledger_entry_id"]),
        paper_fill_event_id=str(preview["source_paper_fill_event_id"]),
        settlement_source_id=str(preview["source_settlement_id"]),
        paper_accounting_record_id=str(preview["paper_accounting_record_id"]),
        paper_accounting_ledger_entry_id=str(ledger["paper_accounting_ledger_entry_id"]),
        operator_manual_fill_price=_decimal_from_value(fill["operator_manual_fill_price"]),
        operator_manual_fill_size=_decimal_from_value(fill["operator_manual_fill_size"]),
        operator_manual_settlement_price=_decimal_from_value(settlement["operator_manual_settlement_price"]),
        paper_accounting_status=str(preview["paper_accounting_status"]),
        paper_accounting_entry_status=str(ledger["paper_accounting_entry_status"]),
        paper_position_status=str(ledger["paper_position_status"]),
        cost_basis=_decimal_from_value(preview["paper_accounting_cost_basis"]),
        settlement_value=_decimal_from_value(preview["paper_accounting_settlement_value"]),
        pnl=_decimal_from_value(preview["paper_accounting_pnl"]),
        cumulative_pnl=_decimal_from_value(ledger["paper_accounting_cumulative_pnl"]),
    )

    record_002 = _paper_accounting_record(
        batch_record_id="paper-accounting-batch-record-002",
        market_id="paper-batch-market-settled-loss-002",
        source_origin="synthetic_paper_accounting_batch_fixture",
        source_manual_intent_id="paper-batch-manual-intent-002",
        source_ledger_entry_id="paper-batch-manual-ledger-002",
        paper_fill_event_id="paper-batch-fill-event-002",
        settlement_source_id="paper-batch-settlement-source-002",
        paper_accounting_record_id="paper-batch-accounting-pnl-002",
        paper_accounting_ledger_entry_id="paper-batch-accounting-ledger-entry-002",
        operator_manual_fill_price=Decimal("0.70"),
        operator_manual_fill_size=Decimal("10"),
        operator_manual_settlement_price=Decimal("0.00"),
        paper_accounting_status="paper_position_settled_from_operator_manual_fixture",
        paper_accounting_entry_status="paper_accounting_entry_recorded",
        paper_position_status="paper_position_settled",
        cost_basis=Decimal("7.00"),
        settlement_value=Decimal("0.00"),
        pnl=Decimal("-7.00"),
        cumulative_pnl=Decimal("-1.00"),
    )

    record_003 = _paper_accounting_record(
        batch_record_id="paper-accounting-batch-record-003",
        market_id="paper-batch-market-open-003",
        source_origin="synthetic_paper_accounting_batch_fixture",
        source_manual_intent_id="paper-batch-manual-intent-003",
        source_ledger_entry_id="paper-batch-manual-ledger-003",
        paper_fill_event_id="paper-batch-fill-event-003",
        settlement_source_id=None,
        paper_accounting_record_id="paper-batch-accounting-pnl-003",
        paper_accounting_ledger_entry_id="paper-batch-accounting-ledger-entry-003",
        operator_manual_fill_price=Decimal("0.25"),
        operator_manual_fill_size=Decimal("20"),
        operator_manual_settlement_price=None,
        paper_accounting_status="paper_position_open_pending_settlement",
        paper_accounting_entry_status="paper_accounting_entry_pending_settlement",
        paper_position_status="paper_position_open",
        cost_basis=Decimal("5.00"),
        settlement_value=Decimal("0.00"),
        pnl=Decimal("0.00"),
        cumulative_pnl=Decimal("-1.00"),
    )

    records = sorted([record_001, record_002, record_003], key=lambda item: item["batch_record_id"])
    return {
        "schema_version": "paper_accounting_batch_input.v1",
        "task_id": TASK_ID,
        "deterministic": True,
        "offline_only": True,
        "local_file_reads_only": True,
        "fixture_mode": "existing_local_record_plus_deterministic_synthetic_batch_rows",
        "source_artifact_pointers": dict(EXPECTED_BATCH_POINTERS),
        "counts": {
            "existing_source_records_read": 1,
            "synthetic_fixture_records": 2,
            "paper_accounting_batch_records": len(records),
            "paper_orders_created": 0,
            "autonomous_actions_created": 0,
            "real_orders_created": 0,
            "live_orders_created": 0,
            "autonomous_paper_orders_created": 0,
        },
        "paper_accounting_totals": {
            "paper_accounting_total_records": 3,
            "paper_accounting_settled_count": 2,
            "paper_accounting_open_count": 1,
            "paper_accounting_win_count": 1,
            "paper_accounting_loss_count": 1,
            "paper_accounting_flat_count": 0,
            "paper_accounting_total_cost_basis": "16.00",
            "paper_accounting_total_settlement_value": "10.00",
            "paper_accounting_cumulative_pnl": "-1.00",
            "paper_accounting_average_pnl": "-0.50",
            "paper_accounting_gross_profit": "6.00",
            "paper_accounting_gross_loss": "-7.00",
            "paper_accounting_max_gain": "6.00",
            "paper_accounting_max_loss": "-7.00",
        },
        "paper_accounting_records": records,
    }


def _artifact_summaries(artifacts):
    summaries = []
    for artifact_id, path, record_field in SOURCE_ARTIFACTS:
        payload = artifacts[artifact_id]["payload"]
        records = _records(payload, record_field)
        record_count = len(records)
        if artifact_id == "paper_metrics_report":
            record_count = _counts(payload).get("paper_metrics_report_records", 0)
        if artifact_id == "paper_accounting_reconciliation_audit":
            record_count = 1 if payload.get("audit_status") is not None else 0
        summaries.append(
            {
                "artifact_id": artifact_id,
                "path": path,
                "schema_version": payload.get("schema_version"),
                "deterministic": payload.get("deterministic"),
                "record_count": record_count,
            }
        )
    return summaries


def _records_seen(artifacts, batch_input):
    return {
        "source_artifacts_loaded": len(artifacts),
        "source_fill_events": len(_source_records(artifacts, "paper_fill_events")),
        "source_settlement_records": len(_source_records(artifacts, "paper_settlement_sources_accepted")),
        "source_accounting_preview_records": len(_source_records(artifacts, "paper_accounting_pnl_preview")),
        "source_accounting_ledger_entries": len(_source_records(artifacts, "paper_accounting_ledger")),
        "source_portfolio_positions": len(_source_records(artifacts, "paper_portfolio_snapshot")),
        "source_metrics_report_records": _counts(artifacts["paper_metrics_report"]["payload"]).get(
            "paper_metrics_report_records"
        ),
        "source_reconciliation_audit_records": 1
        if artifacts["paper_accounting_reconciliation_audit"]["payload"].get("audit_status") is not None
        else 0,
        "existing_source_records_read": _counts(batch_input).get("existing_source_records_read"),
        "synthetic_fixture_records": _counts(batch_input).get("synthetic_fixture_records"),
        "batch_accounting_records": len(_records(batch_input, "paper_accounting_records")),
    }


def _market_ids(records):
    return sorted({str(record.get("market_id")) for record in records if record.get("market_id") is not None})


def _check(status, check_id, summary, expected=None, actual=None, records=None):
    payload = {
        "check_id": check_id,
        "status": status,
        "summary": summary,
    }
    if expected is not None:
        payload["expected"] = expected
    if actual is not None:
        payload["actual"] = actual
    if records is not None:
        payload["records"] = records
    return payload


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


def _find_prohibited_active_fields(artifacts, batch_input):
    blocked = []
    active_values = [batch_input]
    active_values.extend(artifacts[artifact_id]["payload"] for artifact_id, _path, _field in SOURCE_ARTIFACTS)
    for value_index, value in enumerate(active_values):
        source_name = "paper_accounting_batch_input" if value_index == 0 else SOURCE_ARTIFACTS[value_index - 1][0]
        for key, path in _walk_keys(value):
            if key in SAFETY_FIELD_EXEMPTIONS:
                continue
            if path.startswith("safety.") or path.startswith("safety_flags."):
                continue
            if PROHIBITED_ACTIVE_FIELD_NAMES.intersection(_field_tokens(key)):
                blocked.append(f"{source_name}:{path}")
    return sorted(blocked)


def _source_artifact_checks(artifacts):
    summaries = _artifact_summaries(artifacts)
    missing_schema = [item["artifact_id"] for item in summaries if item.get("schema_version") is None]
    deterministic_failures = [
        item["artifact_id"]
        for item in summaries
        if item["artifact_id"] != "paper_accounting_reconciliation_audit" and item.get("deterministic") is not True
    ]
    reconciliation = artifacts["paper_accounting_reconciliation_audit"]["payload"]
    reconciliation_status = reconciliation.get("audit_status")
    return [
        _check(
            "pass" if not missing_schema else "fail",
            "source_artifacts_loaded",
            "Required local paper accounting artifacts were loaded.",
            expected=[],
            actual=missing_schema,
        ),
        _check(
            "pass" if not deterministic_failures else "fail",
            "source_artifacts_deterministic",
            "Source paper accounting artifacts declare deterministic output.",
            expected=[],
            actual=deterministic_failures,
        ),
        _check(
            "pass" if reconciliation_status == "reconciliation_passed" else "fail",
            "paper_017_reconciliation_anchor",
            "Existing PAPER-017 reconciliation audit is present and passed before batch audit expansion.",
            expected="reconciliation_passed",
            actual=reconciliation_status,
        ),
    ]


def _records_seen_check(records_seen):
    failures = []
    if records_seen["batch_accounting_records"] < 2:
        failures.append("batch_accounting_records is below multi-record threshold")
    if records_seen["existing_source_records_read"] != 1:
        failures.append("existing_source_records_read is not 1")
    if records_seen["synthetic_fixture_records"] != 2:
        failures.append("synthetic_fixture_records is not 2")
    if records_seen["batch_accounting_records"] != (
        records_seen["existing_source_records_read"] + records_seen["synthetic_fixture_records"]
    ):
        failures.append("batch records do not equal existing plus synthetic fixture records")
    return _check(
        "pass" if not failures else "fail",
        "record_count_consistency",
        "Batch accounting record counts match the deterministic multi-record audit scope.",
        expected={
            "existing_source_records_read": 1,
            "synthetic_fixture_records": 2,
            "batch_accounting_records": 3,
        },
        actual=records_seen,
    )


def _existing_record_anchor_mismatches(artifacts, records):
    first = records[0] if records else {}
    fill = _first_source_record(artifacts, "paper_fill_events")
    settlement = _first_source_record(artifacts, "paper_settlement_sources_accepted")
    preview = _first_source_record(artifacts, "paper_accounting_pnl_preview")
    ledger = _first_source_record(artifacts, "paper_accounting_ledger")
    comparisons = {
        "market_id": str(preview.get("market_id")),
        "paper_fill_event_id": str(fill.get("paper_fill_event_id")),
        "settlement_source_id": str(settlement.get("settlement_source_id")),
        "paper_accounting_record_id": str(preview.get("paper_accounting_record_id")),
        "paper_accounting_ledger_entry_id": str(ledger.get("paper_accounting_ledger_entry_id")),
        "paper_accounting_status": str(preview.get("paper_accounting_status")),
        "paper_accounting_entry_status": str(ledger.get("paper_accounting_entry_status")),
        "paper_position_status": str(ledger.get("paper_position_status")),
        "paper_accounting_cost_basis": _safe_decimal_string(preview.get("paper_accounting_cost_basis")),
        "paper_accounting_settlement_value": _safe_decimal_string(preview.get("paper_accounting_settlement_value")),
        "paper_accounting_pnl": _safe_decimal_string(preview.get("paper_accounting_pnl")),
    }
    mismatches = []
    for field, expected in comparisons.items():
        if first.get(field) != expected:
            mismatches.append({"field": field, "expected": expected, "actual": first.get(field)})
    return mismatches


def _market_consistency_mismatches(records):
    mismatches = []
    market_fields = (
        "fill_market_id",
        "settlement_market_id",
        "accounting_market_id",
        "ledger_market_id",
        "portfolio_market_id",
    )
    for record in records:
        expected = record.get("market_id")
        for field in market_fields:
            actual = record.get(field)
            if field == "settlement_market_id" and record.get("settlement_source_id") is None:
                if actual is not None:
                    mismatches.append(f"{record['batch_record_id']} {field} expected null for open record")
                continue
            if actual != expected:
                mismatches.append(f"{record['batch_record_id']} {field} does not match market_id")
    return sorted(mismatches)


def _linkage_mismatches(records):
    mismatches = []
    for record in records:
        record_id = record["batch_record_id"]
        expected_fill = record.get("paper_fill_event_id")
        expected_settlement = record.get("settlement_source_id")
        expected_accounting = record.get("paper_accounting_record_id")
        expected_ledger = record.get("paper_accounting_ledger_entry_id")
        if record.get("accounting_source_paper_fill_event_id") != expected_fill:
            mismatches.append(f"{record_id} accounting fill source does not match fill event")
        if record.get("ledger_source_paper_fill_event_id") != expected_fill:
            mismatches.append(f"{record_id} ledger fill source does not match fill event")
        if record.get("accounting_source_settlement_id") != expected_settlement:
            mismatches.append(f"{record_id} accounting settlement source does not match settlement record")
        if record.get("ledger_source_settlement_id") != expected_settlement:
            mismatches.append(f"{record_id} ledger settlement source does not match settlement record")
        if record.get("ledger_source_paper_accounting_record_id") != expected_accounting:
            mismatches.append(f"{record_id} ledger accounting source does not match accounting record")
        if record.get("portfolio_source_paper_accounting_ledger_entry_id") != expected_ledger:
            mismatches.append(f"{record_id} portfolio source does not match accounting ledger entry")
        for field in ("source_manual_intent_id", "source_ledger_entry_id"):
            if not record.get(field):
                mismatches.append(f"{record_id} missing {field}")
    return sorted(mismatches)


def _status_mismatches(records):
    mismatches = []
    for record in records:
        record_id = record["batch_record_id"]
        status = record.get("paper_position_status")
        accounting_status = record.get("paper_accounting_status")
        entry_status = record.get("paper_accounting_entry_status")
        settlement_id = record.get("settlement_source_id")
        settlement_price = record.get("operator_manual_settlement_price")
        if status == "paper_position_settled":
            if accounting_status != "paper_position_settled_from_operator_manual_fixture":
                mismatches.append(f"{record_id} settled position has unexpected accounting status")
            if entry_status != "paper_accounting_entry_recorded":
                mismatches.append(f"{record_id} settled position has unexpected ledger entry status")
            if settlement_id is None or settlement_price is None:
                mismatches.append(f"{record_id} settled position is missing settlement linkage")
        elif status == "paper_position_open":
            if accounting_status != "paper_position_open_pending_settlement":
                mismatches.append(f"{record_id} open position has unexpected accounting status")
            if entry_status != "paper_accounting_entry_pending_settlement":
                mismatches.append(f"{record_id} open position has unexpected ledger entry status")
            if settlement_id is not None or settlement_price is not None:
                mismatches.append(f"{record_id} open position should not have settlement linkage")
        else:
            mismatches.append(f"{record_id} has unsupported paper_position_status {status}")
    return sorted(mismatches)


def _computed_totals(records):
    total_cost_basis = Decimal("0.00")
    total_settlement_value = Decimal("0.00")
    settled_pnl_values = []
    settled_count = 0
    open_count = 0
    for record in records:
        cost_basis = _decimal_from_value(record.get("paper_accounting_cost_basis")) or Decimal("0.00")
        settlement_value = _decimal_from_value(record.get("paper_accounting_settlement_value")) or Decimal("0.00")
        total_cost_basis += cost_basis
        total_settlement_value += settlement_value
        if record.get("paper_position_status") == "paper_position_settled":
            settled_count += 1
            pnl = _decimal_from_value(record.get("paper_accounting_pnl"))
            if pnl is not None:
                settled_pnl_values.append(pnl)
        else:
            open_count += 1
    cumulative_pnl = sum(settled_pnl_values, Decimal("0.00"))
    gross_profit = sum((value for value in settled_pnl_values if value > Decimal("0.00")), Decimal("0.00"))
    gross_loss = sum((value for value in settled_pnl_values if value < Decimal("0.00")), Decimal("0.00"))
    average_pnl = cumulative_pnl / Decimal(len(settled_pnl_values)) if settled_pnl_values else Decimal("0.00")
    gains = [value for value in settled_pnl_values if value > Decimal("0.00")]
    losses = [value for value in settled_pnl_values if value < Decimal("0.00")]
    return {
        "paper_accounting_total_records": len(records),
        "paper_accounting_settled_count": settled_count,
        "paper_accounting_open_count": open_count,
        "paper_accounting_win_count": sum(1 for value in settled_pnl_values if value > Decimal("0.00")),
        "paper_accounting_loss_count": sum(1 for value in settled_pnl_values if value < Decimal("0.00")),
        "paper_accounting_flat_count": sum(1 for value in settled_pnl_values if value == Decimal("0.00")),
        "paper_accounting_total_cost_basis": _format_decimal(total_cost_basis),
        "paper_accounting_total_settlement_value": _format_decimal(total_settlement_value),
        "paper_accounting_cumulative_pnl": _format_decimal(cumulative_pnl),
        "paper_accounting_average_pnl": _format_decimal(average_pnl),
        "paper_accounting_gross_profit": _format_decimal(gross_profit),
        "paper_accounting_gross_loss": _format_decimal(gross_loss),
        "paper_accounting_max_gain": _format_decimal(max(gains) if gains else Decimal("0.00")),
        "paper_accounting_max_loss": _format_decimal(min(losses) if losses else Decimal("0.00")),
    }


def _pnl_value_mismatches(records):
    mismatches = []
    cumulative = Decimal("0.00")
    for record in records:
        record_id = record["batch_record_id"]
        fill_price = _decimal_from_value(record.get("operator_manual_fill_price"))
        fill_size = _decimal_from_value(record.get("operator_manual_fill_size"))
        settlement_price = _decimal_from_value(record.get("operator_manual_settlement_price"))
        if fill_price is None or fill_size is None:
            mismatches.append(f"{record_id} fill price or size is not decimal")
            continue
        expected_cost = fill_price * fill_size
        expected_settlement = Decimal("0.00")
        expected_pnl = Decimal("0.00")
        if record.get("paper_position_status") == "paper_position_settled":
            if settlement_price is None:
                mismatches.append(f"{record_id} settled record has no settlement price")
                continue
            expected_settlement = settlement_price * fill_size
            expected_pnl = expected_settlement - expected_cost
            cumulative += expected_pnl
        comparisons = {
            "paper_accounting_cost_basis": expected_cost,
            "paper_accounting_settlement_value": expected_settlement,
            "paper_accounting_pnl": expected_pnl,
            "paper_accounting_cumulative_pnl": cumulative,
        }
        for field, expected in comparisons.items():
            if record.get(field) != _format_decimal(expected):
                mismatches.append(
                    f"{record_id} {field} expected {_format_decimal(expected)} got {record.get(field)}"
                )
    return sorted(mismatches)


def _declared_totals_mismatches(batch_input, computed_totals):
    declared = batch_input.get("paper_accounting_totals")
    if not isinstance(declared, dict):
        return ["paper_accounting_totals is missing or not an object"]
    mismatches = []
    for key, expected in computed_totals.items():
        actual = declared.get(key)
        if actual != expected:
            mismatches.append(f"{key} expected {expected} from records, got {actual}")
    return sorted(mismatches)


def _artifact_pointer_mismatches(artifacts, batch_input, records):
    mismatches = []
    for artifact_id, path, expected in EXPECTED_SOURCE_POINTERS:
        actual = _nested(artifacts[artifact_id]["payload"], path)
        if actual != expected:
            mismatches.append(
                {
                    "artifact_id": artifact_id,
                    "field_path": ".".join(str(part) for part in path),
                    "expected": expected,
                    "actual": actual,
                }
            )
    pointers = batch_input.get("source_artifact_pointers")
    if not isinstance(pointers, dict):
        mismatches.append(
            {
                "artifact_id": "paper_accounting_batch_input",
                "field_path": "source_artifact_pointers",
                "expected": "dict",
                "actual": type(pointers).__name__,
            }
        )
    else:
        for field, expected in EXPECTED_BATCH_POINTERS.items():
            actual = pointers.get(field)
            if actual != expected:
                mismatches.append(
                    {
                        "artifact_id": "paper_accounting_batch_input",
                        "field_path": f"source_artifact_pointers.{field}",
                        "expected": expected,
                        "actual": actual,
                    }
                )
    for record in records:
        references = record.get("source_references")
        if not isinstance(references, dict):
            mismatches.append(
                {
                    "artifact_id": record.get("batch_record_id"),
                    "field_path": "source_references",
                    "expected": "dict",
                    "actual": type(references).__name__,
                }
            )
            continue
        for field, expected in EXPECTED_BATCH_POINTERS.items():
            actual = references.get(field)
            if actual != expected:
                mismatches.append(
                    {
                        "artifact_id": record["batch_record_id"],
                        "field_path": f"source_references.{field}",
                        "expected": expected,
                        "actual": actual,
                    }
                )
    return mismatches


def _safety_mismatches(artifacts, batch_input, records):
    mismatches = []
    for key in (
        "paper_orders_created",
        "autonomous_actions_created",
        "real_orders_created",
        "live_orders_created",
        "autonomous_paper_orders_created",
    ):
        if _counts(batch_input).get(key) != 0:
            mismatches.append(f"batch input count {key} is not zero")
    for artifact_id, _path, _field in SOURCE_ARTIFACTS:
        counts = _counts(artifacts[artifact_id]["payload"])
        for key in ("real_orders_created", "live_orders_created", "autonomous_paper_orders_created"):
            if key in counts and counts.get(key) != 0:
                mismatches.append(f"{artifact_id} count {key} is not zero")
    for record in records:
        record_id = record["batch_record_id"]
        for key, expected in REQUIRED_RECORD_FLAGS.items():
            if record.get(key) is not expected:
                mismatches.append(f"{record_id} {key} is not {expected}")
        safety_flags = record.get("safety_flags")
        if not isinstance(safety_flags, list):
            mismatches.append(f"{record_id} safety_flags is not a list")
            continue
        for flag in REQUIRED_SAFETY_FLAGS:
            if flag not in safety_flags:
                mismatches.append(f"{record_id} missing safety flag {flag}")
    return sorted(mismatches)


def _audit_status(checks):
    if any(check["status"] == "fail" for check in checks):
        return "batch_audit_failed"
    if any(check["status"] == "warning" for check in checks):
        return "batch_audit_passed_with_warnings"
    return "batch_audit_passed"


def build_batch_audit(artifacts):
    batch_input = _build_batch_input(artifacts)
    records = _records(batch_input, "paper_accounting_records")
    records_seen = _records_seen(artifacts, batch_input)
    computed_totals = _computed_totals(records)

    lifecycle_checks = []
    lifecycle_checks.extend(_source_artifact_checks(artifacts))
    lifecycle_checks.append(_records_seen_check(records_seen))

    anchor_mismatches = _existing_record_anchor_mismatches(artifacts, records)
    lifecycle_checks.append(
        _check(
            "pass" if not anchor_mismatches else "fail",
            "existing_record_anchor_consistency",
            "The first batch record remains anchored to the existing local PAPER-017 accounting record.",
            expected=[],
            actual=anchor_mismatches,
            records=["paper-accounting-batch-record-001"],
        )
    )

    market_mismatches = _market_consistency_mismatches(records)
    lifecycle_checks.append(
        _check(
            "pass" if not market_mismatches else "fail",
            "market_id_consistency",
            "Each batch record keeps the same market_id across fill, settlement, accounting, ledger, and portfolio fields.",
            expected=[],
            actual=market_mismatches,
        )
    )

    linkage_mismatches = _linkage_mismatches(records)
    lifecycle_checks.append(
        _check(
            "pass" if not linkage_mismatches else "fail",
            "fill_settlement_accounting_linkage",
            "Fill, settlement, accounting, ledger, and portfolio identifiers link within each batch record.",
            expected=[],
            actual=linkage_mismatches,
        )
    )

    status_mismatches = _status_mismatches(records)
    lifecycle_checks.append(
        _check(
            "pass" if not status_mismatches else "fail",
            "open_settled_status_consistency",
            "Open and settled records carry status-compatible settlement and ledger fields.",
            expected=[],
            actual=status_mismatches,
        )
    )

    pnl_mismatches = _pnl_value_mismatches(records)
    lifecycle_checks.append(
        _check(
            "pass" if not pnl_mismatches else "fail",
            "per_record_pnl_consistency",
            "Each batch record PnL reconciles from local paper fill and settlement values.",
            expected=[],
            actual=pnl_mismatches,
        )
    )

    total_mismatches = _declared_totals_mismatches(batch_input, computed_totals)
    lifecycle_checks.append(
        _check(
            "pass" if not total_mismatches else "fail",
            "pnl_aggregation_consistency",
            "Declared batch accounting totals match deterministic aggregation across audited records.",
            expected=computed_totals,
            actual=batch_input.get("paper_accounting_totals"),
        )
    )

    pointer_mismatches = _artifact_pointer_mismatches(artifacts, batch_input, records)
    artifact_pointer_checks = [
        _check(
            "pass" if not pointer_mismatches else "fail",
            "artifact_pointer_consistency",
            "Batch source pointers and record source references point to the expected local paper artifacts.",
            expected=[],
            actual=pointer_mismatches,
        )
    ]

    safety_mismatches = _safety_mismatches(artifacts, batch_input, records)
    prohibited_fields = _find_prohibited_active_fields(artifacts, batch_input)
    safety_checks = [
        _check(
            "pass" if not safety_mismatches else "fail",
            "safety_flag_consistency",
            "Batch records and source artifact counts remain paper-only, inert, local, and non-executable.",
            expected=[],
            actual=safety_mismatches,
        ),
        _check(
            "pass" if not prohibited_fields else "fail",
            "no_scoring_probability_ev_edge_or_market_decision_fields",
            "Audited batch and active source artifacts contain no scoring, probability, EV, edge, recommendation, or market-decision fields.",
            expected=[],
            actual=prohibited_fields,
        ),
    ]

    all_checks = lifecycle_checks + artifact_pointer_checks + safety_checks
    mismatches = [check for check in all_checks if check["status"] == "fail"]
    warnings = [check for check in all_checks if check["status"] == "warning"]
    status = _audit_status(all_checks)
    return {
        "schema_version": "paper_accounting_batch_audit.v1",
        "markdown_version": "paper_accounting_batch_audit_markdown.v1",
        "task_id": TASK_ID,
        "audit_scope": {
            "mode": "deterministic_offline_multi_record_paper_accounting_batch_audit",
            "source_artifacts": [path for _artifact_id, path, _record_field in SOURCE_ARTIFACTS],
            "fixture_mode": batch_input["fixture_mode"],
            "local_file_reads_only": True,
            "runtime_wiring": False,
        },
        "records_seen": records_seen,
        "records_audited": len(records),
        "market_ids": _market_ids(records),
        "accounting_totals": computed_totals,
        "lifecycle_consistency_checks": lifecycle_checks,
        "artifact_pointer_checks": artifact_pointer_checks,
        "safety_checks": safety_checks,
        "mismatches": mismatches,
        "warnings": warnings,
        "audit_status": status,
        "deterministic": True,
        "source_artifacts_checked": _artifact_summaries(artifacts),
        "audited_record_summaries": [
            {
                "batch_record_id": record["batch_record_id"],
                "market_id": record["market_id"],
                "source_origin": record["source_origin"],
                "paper_position_status": record["paper_position_status"],
                "paper_accounting_pnl": record["paper_accounting_pnl"],
            }
            for record in records
        ],
        "safety_flags": {
            "offline_only": True,
            "local_file_reads_only": True,
            "runtime_wiring": False,
            "network_api": False,
            "wallet": False,
            "trading": False,
            "autonomous_paper_orders": False,
            "scoring_probability_ev_edge": False,
            "market_decisions": False,
        },
        "paper_orders_created": 0,
        "autonomous_actions_created": 0,
        "next_safe_action": "ready_for_integration_review"
        if status != "batch_audit_failed"
        else "requires_operator_review",
    }


def render_audit_markdown(audit):
    totals = audit["accounting_totals"]
    lines = [
        "# PMBOT PAPER-018 Accounting Batch Audit",
        "",
        f"- Task ID: `{audit['task_id']}`",
        f"- Audit status: `{audit['audit_status']}`",
        f"- Records audited: `{audit['records_audited']}`",
        f"- Market IDs: `{', '.join(audit['market_ids'])}`",
        f"- Paper orders created: `{audit['paper_orders_created']}`",
        f"- Autonomous actions created: `{audit['autonomous_actions_created']}`",
        f"- Next safe action: `{audit['next_safe_action']}`",
        "",
        "## Accounting Totals",
        "",
        "| Metric | Value |",
        "| --- | ---: |",
    ]
    for key in (
        "paper_accounting_total_records",
        "paper_accounting_settled_count",
        "paper_accounting_open_count",
        "paper_accounting_win_count",
        "paper_accounting_loss_count",
        "paper_accounting_flat_count",
        "paper_accounting_total_cost_basis",
        "paper_accounting_total_settlement_value",
        "paper_accounting_cumulative_pnl",
        "paper_accounting_average_pnl",
        "paper_accounting_gross_profit",
        "paper_accounting_gross_loss",
        "paper_accounting_max_gain",
        "paper_accounting_max_loss",
    ):
        lines.append(f"| `{key}` | `{totals.get(key)}` |")
    lines.extend(
        [
            "",
            "## Records",
            "",
            "| Record | Market | Status | PnL | Source |",
            "| --- | --- | --- | ---: | --- |",
        ]
    )
    for record in audit["audited_record_summaries"]:
        lines.append(
            "| "
            f"`{record['batch_record_id']}` | "
            f"`{record['market_id']}` | "
            f"`{record['paper_position_status']}` | "
            f"`{record['paper_accounting_pnl']}` | "
            f"`{record['source_origin']}` |"
        )
    lines.extend(
        [
            "",
            "## Checks",
            "",
            "| Check | Status | Summary |",
            "| --- | --- | --- |",
        ]
    )
    for check in (
        audit["lifecycle_consistency_checks"]
        + audit["artifact_pointer_checks"]
        + audit["safety_checks"]
    ):
        lines.append(f"| `{check['check_id']}` | `{check['status']}` | {check['summary']} |")
    lines.extend(
        [
            "",
            "## Safety",
            "",
            "| Flag | Value |",
            "| --- | --- |",
        ]
    )
    for key, value in audit["safety_flags"].items():
        lines.append(f"| `{key}` | `{str(value).lower()}` |")
    lines.append("")
    return "\n".join(lines)


def _missing_optional_docs():
    return [path for path in OPTIONAL_DOCS if not _resolve_path(path).exists()]


def _result_payload(audit, missing_optional_docs):
    completed = audit["audit_status"] != "batch_audit_failed"
    checks = (
        audit["lifecycle_consistency_checks"]
        + audit["artifact_pointer_checks"]
        + audit["safety_checks"]
    )
    return {
        "task_id": TASK_ID,
        "status": "completed_ready_for_review" if completed else "blocked",
        "summary": (
            "Implemented deterministic offline multi-record paper accounting batch audit."
            if completed
            else "Paper accounting batch audit found structural mismatches."
        ),
        "audit_status": audit["audit_status"],
        "records_seen": audit["records_seen"],
        "records_audited": audit["records_audited"],
        "market_ids": audit["market_ids"],
        "counts": {
            "source_artifacts_checked": len(audit["source_artifacts_checked"]),
            "checks_total": len(checks),
            "checks_passed": sum(1 for check in checks if check["status"] == "pass"),
            "checks_warning": sum(1 for check in checks if check["status"] == "warning"),
            "checks_failed": sum(1 for check in checks if check["status"] == "fail"),
            "paper_orders_created": audit["paper_orders_created"],
            "autonomous_actions_created": audit["autonomous_actions_created"],
        },
        "accounting_totals": audit["accounting_totals"],
        "files_created": list(FILES_CREATED),
        "files_modified": [],
        "tests": [],
        "warnings": audit["warnings"],
        "missing_optional_docs": missing_optional_docs,
        "safety": {
            "offline_only": True,
            "network_api_calls": False,
            "credentials": False,
            "wallet_private_keys": False,
            "authenticated_endpoints": False,
            "trading_endpoints": False,
            "real_orders": False,
            "live_trading": False,
            "autonomous_paper_orders": False,
            "betting_recommendations": False,
            "truth_inference": False,
            "market_scoring": False,
            "probability_estimates": False,
            "ev_calculations": False,
            "edge_calculations": False,
            "side_recommendations": False,
            "market_decisions": False,
            "runtime_wiring": False,
            "dispatcher_run_codex_changes": False,
            "prompt_automation": False,
            "codex_copy_roots": False,
            "completed_dossiers": False,
            "broad_refactor": False,
        },
        "paper_orders_created": 0,
        "autonomous_actions_created": 0,
        "blockers": [] if completed else ["audit structural mismatches must be reviewed before integration"],
        "next_action": "ready_for_integration_review" if completed else "requires_operator_review",
    }


def write_paper_accounting_batch_audit():
    artifacts = _load_artifacts()
    audit = build_batch_audit(artifacts)
    missing_optional_docs = _missing_optional_docs()
    result = _result_payload(audit, missing_optional_docs)
    _write_json(DEFAULT_AUDIT, audit)
    _write_json(DEFAULT_AUDIT_EXPECTED, audit)
    _write_text(DEFAULT_AUDIT_MD, render_audit_markdown(audit))
    _write_json(DEFAULT_RESULT, result)
    _write_json(DEFAULT_LANE_RESULT, result)
    return {
        "task_id": TASK_ID,
        "audit_status": audit["audit_status"],
        "records_audited": audit["records_audited"],
        "checks_total": result["counts"]["checks_total"],
        "checks_failed": result["counts"]["checks_failed"],
        "warnings": result["counts"]["checks_warning"],
        "missing_optional_docs": missing_optional_docs,
        "result_path": _display_path(DEFAULT_RESULT),
    }


def _blocked_result(exc):
    missing_optional_docs = _missing_optional_docs()
    return {
        "task_id": TASK_ID,
        "status": "blocked",
        "summary": "Blocked before completing deterministic offline multi-record paper accounting batch audit.",
        "audit_status": "batch_audit_failed",
        "records_seen": {},
        "records_audited": 0,
        "market_ids": [],
        "counts": {
            "source_artifacts_checked": 0,
            "checks_total": 0,
            "checks_passed": 0,
            "checks_warning": 0,
            "checks_failed": 1,
            "paper_orders_created": 0,
            "autonomous_actions_created": 0,
        },
        "accounting_totals": {},
        "files_created": [],
        "files_modified": [],
        "tests": [],
        "warnings": [],
        "missing_optional_docs": missing_optional_docs,
        "safety": {
            "offline_only": True,
            "network_api_calls": False,
            "credentials": False,
            "wallet_private_keys": False,
            "authenticated_endpoints": False,
            "trading_endpoints": False,
            "real_orders": False,
            "live_trading": False,
            "autonomous_paper_orders": False,
            "betting_recommendations": False,
            "truth_inference": False,
            "market_scoring": False,
            "probability_estimates": False,
            "ev_calculations": False,
            "edge_calculations": False,
            "side_recommendations": False,
            "market_decisions": False,
            "runtime_wiring": False,
            "dispatcher_run_codex_changes": False,
            "prompt_automation": False,
            "codex_copy_roots": False,
            "completed_dossiers": False,
            "broad_refactor": False,
        },
        "paper_orders_created": 0,
        "autonomous_actions_created": 0,
        "blockers": [str(exc)],
        "next_action": "requires_operator_review",
    }


def main(argv):
    _parse_args(argv)
    try:
        summary = write_paper_accounting_batch_audit()
    except Exception as exc:
        blocked = _blocked_result(exc)
        _write_json(DEFAULT_RESULT, blocked)
        _write_json(DEFAULT_LANE_RESULT, blocked)
        print(
            json.dumps(
                {"task_id": TASK_ID, "status": "blocked", "blockers": [str(exc)]},
                indent=2,
                ensure_ascii=True,
            )
        )
        return 2
    print(json.dumps(summary, indent=2, ensure_ascii=True))
    return 0 if summary["audit_status"] != "batch_audit_failed" else 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
