import argparse
import json
import sys
from decimal import Decimal, InvalidOperation
from pathlib import Path


TASK_ID = "PMBOT-PAPER-017-PAPER-ACCOUNTING-RECONCILIATION-LIFECYCLE-AUDIT"
MARKET_ID = "824952"
ROOT = Path(__file__).resolve().parents[2]
PAPER_DIR = ROOT / "pm_bot" / "paper"
DOCS_DIR = ROOT / "docs"

DEFAULT_AUDIT = PAPER_DIR / "paper_accounting_reconciliation_audit.v1.json"
DEFAULT_AUDIT_MD = PAPER_DIR / "paper_accounting_reconciliation_audit.v1.md"
DEFAULT_AUDIT_EXPECTED = PAPER_DIR / "expected_paper_accounting_reconciliation_audit.v1.json"
DEFAULT_RESULT = DOCS_DIR / "PMBOT_PAPER_017_RESULT.json"

OPTIONAL_DOCS = (
    "docs/PMBOT_INFRA_006_RESULT.json",
)

ARTIFACTS = (
    ("manual_paper_intents_accepted", "pm_bot/paper/manual_paper_intents_accepted.v1.json", "records"),
    ("manual_paper_intent_ledger", "pm_bot/paper/manual_paper_intent_ledger.v1.json", "ledger_entries"),
    ("paper_workbench_preview", "pm_bot/paper/paper_workbench_preview.v1.json", "preview_records"),
    ("paper_fill_source_fixture", "pm_bot/paper/paper_fill_source_fixture.v1.json", "records"),
    ("paper_fill_sources_accepted", "pm_bot/paper/paper_fill_sources_accepted.v1.json", "records"),
    ("paper_fill_sources_rejected", "pm_bot/paper/paper_fill_sources_rejected.v1.json", "records"),
    ("paper_fill_events", "pm_bot/paper/paper_fill_events.v1.json", "paper_fill_events"),
    ("paper_settlement_source_fixture", "pm_bot/paper/paper_settlement_source_fixture.v1.json", "records"),
    ("paper_settlement_sources_accepted", "pm_bot/paper/paper_settlement_sources_accepted.v1.json", "records"),
    ("paper_settlement_sources_rejected", "pm_bot/paper/paper_settlement_sources_rejected.v1.json", "records"),
    ("paper_accounting_pnl_preview", "pm_bot/paper/paper_accounting_pnl_preview.v1.json", "paper_accounting_records"),
    ("paper_accounting_ledger", "pm_bot/paper/paper_accounting_ledger.v1.json", "paper_accounting_ledger_entries"),
    ("paper_portfolio_snapshot", "pm_bot/paper/paper_portfolio_snapshot.v1.json", "positions"),
    ("paper_metrics_report", "pm_bot/paper/paper_metrics_report.v1.json", None),
)

ACTIVE_LIFECYCLE_ARTIFACTS = (
    "manual_paper_intents_accepted",
    "manual_paper_intent_ledger",
    "paper_workbench_preview",
    "paper_fill_sources_accepted",
    "paper_fill_events",
    "paper_settlement_sources_accepted",
    "paper_accounting_pnl_preview",
    "paper_accounting_ledger",
    "paper_portfolio_snapshot",
    "paper_metrics_report",
)

EXPECTED_POINTERS = (
    ("manual_paper_intent_ledger", ("source_accepted_manual_intents_path",), "pm_bot/paper/manual_paper_intents_accepted.v1.json"),
    ("paper_workbench_preview", ("source_manual_paper_intent_ledger_path",), "pm_bot/paper/manual_paper_intent_ledger.v1.json"),
    ("paper_fill_source_fixture", ("source_manual_paper_intent_ledger_path",), "pm_bot/paper/manual_paper_intent_ledger.v1.json"),
    ("paper_fill_sources_accepted", ("source_manual_paper_intent_ledger_path",), "pm_bot/paper/manual_paper_intent_ledger.v1.json"),
    ("paper_fill_sources_accepted", ("input_path",), "pm_bot/paper/paper_fill_source_fixture.v1.json"),
    ("paper_fill_sources_rejected", ("source_manual_paper_intent_ledger_path",), "pm_bot/paper/manual_paper_intent_ledger.v1.json"),
    ("paper_fill_sources_rejected", ("input_path",), "pm_bot/paper/paper_fill_source_fixture.v1.json"),
    ("paper_fill_events", ("source_fill_sources_accepted_path",), "pm_bot/paper/paper_fill_sources_accepted.v1.json"),
    ("paper_settlement_source_fixture", ("source_paper_fill_events_path",), "pm_bot/paper/paper_fill_events.v1.json"),
    ("paper_settlement_sources_accepted", ("source_paper_fill_events_path",), "pm_bot/paper/paper_fill_events.v1.json"),
    ("paper_settlement_sources_accepted", ("input_path",), "pm_bot/paper/paper_settlement_source_fixture.v1.json"),
    ("paper_settlement_sources_rejected", ("source_paper_fill_events_path",), "pm_bot/paper/paper_fill_events.v1.json"),
    ("paper_settlement_sources_rejected", ("input_path",), "pm_bot/paper/paper_settlement_source_fixture.v1.json"),
    ("paper_accounting_pnl_preview", ("source_paper_fill_events_path",), "pm_bot/paper/paper_fill_events.v1.json"),
    ("paper_accounting_pnl_preview", ("source_paper_settlement_sources_accepted_path",), "pm_bot/paper/paper_settlement_sources_accepted.v1.json"),
    ("paper_accounting_ledger", ("source_paper_accounting_pnl_preview_path",), "pm_bot/paper/paper_accounting_pnl_preview.v1.json"),
    ("paper_accounting_ledger", ("source_paper_fill_events_path",), "pm_bot/paper/paper_fill_events.v1.json"),
    ("paper_accounting_ledger", ("source_manual_paper_intent_ledger_path",), "pm_bot/paper/manual_paper_intent_ledger.v1.json"),
    ("paper_portfolio_snapshot", ("source_paper_accounting_ledger_path",), "pm_bot/paper/paper_accounting_ledger.v1.json"),
    ("paper_metrics_report", ("source_paper_accounting_ledger_path",), "pm_bot/paper/paper_accounting_ledger.v1.json"),
    ("paper_metrics_report", ("source_paper_portfolio_snapshot_path",), "pm_bot/paper/paper_portfolio_snapshot.v1.json"),
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
    "pm_bot/paper/run_paper_accounting_reconciliation_audit.py",
    "pm_bot/paper/paper_accounting_reconciliation_audit.v1.json",
    "pm_bot/paper/paper_accounting_reconciliation_audit.v1.md",
    "pm_bot/paper/expected_paper_accounting_reconciliation_audit.v1.json",
    "pm_bot/paper/tests/test_paper_accounting_reconciliation_audit.py",
    "docs/PMBOT_PAPER_017_RESULT.json",
    "docs/PMBOT_CODEX_A_ROUND001_RESULT.json",
]


def _parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Run deterministic offline PMBOT PAPER-017 paper accounting reconciliation audit."
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


def _artifact_definitions():
    return [
        {
            "artifact_id": artifact_id,
            "path": path,
            "record_field": record_field,
        }
        for artifact_id, path, record_field in ARTIFACTS
    ]


def _load_artifacts():
    artifacts = {}
    for definition in _artifact_definitions():
        path = _resolve_path(definition["path"])
        if not path.exists():
            raise FileNotFoundError(f"missing required paper artifact: {definition['path']}")
        artifacts[definition["artifact_id"]] = {
            "path": definition["path"],
            "record_field": definition["record_field"],
            "payload": _load_json(path),
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


def _market_ids(records, payload=None):
    if payload is not None and isinstance(payload.get("market_ids"), list):
        return sorted({str(value) for value in payload["market_ids"]})
    return sorted({str(record.get("market_id")) for record in records if record.get("market_id") is not None})


def _counts(payload):
    counts = payload.get("counts")
    if isinstance(counts, dict):
        return counts
    return {}


def _count_value(payload, key):
    value = _counts(payload).get(key)
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    return None


def _by_id(records, key):
    return {str(record.get(key)): record for record in records if record.get(key) is not None}


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


def _find_prohibited_active_fields(artifacts):
    blocked = []
    for artifact_id in ACTIVE_LIFECYCLE_ARTIFACTS:
        payload = artifacts[artifact_id]["payload"]
        for key, path in _walk_keys(payload):
            if key in SAFETY_FIELD_EXEMPTIONS:
                continue
            if PROHIBITED_ACTIVE_FIELD_NAMES.intersection(_field_tokens(key)):
                blocked.append(f"{artifact_id}:{path}")
    return sorted(blocked)


def _records_for(artifacts, artifact_id):
    artifact = artifacts[artifact_id]
    return _records(artifact["payload"], artifact["record_field"])


def _artifact_summaries(artifacts):
    summaries = []
    for artifact_id, _path, _field in ARTIFACTS:
        artifact = artifacts[artifact_id]
        payload = artifact["payload"]
        records = _records(payload, artifact["record_field"])
        counts = _counts(payload)
        record_count = len(records)
        if artifact_id == "paper_metrics_report":
            record_count = counts.get("paper_metrics_report_records", 0)
        summaries.append(
            {
                "artifact_id": artifact_id,
                "path": artifact["path"],
                "schema_version": payload.get("schema_version"),
                "deterministic": payload.get("deterministic"),
                "record_count": record_count,
                "market_ids": _market_ids(records, payload),
            }
        )
    return summaries


def _check(status, check_id, summary, expected=None, actual=None, artifacts=None):
    payload = {
        "check_id": check_id,
        "status": status,
        "summary": summary,
    }
    if expected is not None:
        payload["expected"] = expected
    if actual is not None:
        payload["actual"] = actual
    if artifacts is not None:
        payload["artifacts"] = artifacts
    return payload


def _pointer_mismatches(artifacts):
    mismatches = []
    for artifact_id, path, expected in EXPECTED_POINTERS:
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
    ledger_entries = _records_for(artifacts, "paper_accounting_ledger")
    for index, entry in enumerate(ledger_entries):
        references = entry.get("source_references")
        if not isinstance(references, dict):
            mismatches.append(
                {
                    "artifact_id": "paper_accounting_ledger",
                    "field_path": f"paper_accounting_ledger_entries[{index}].source_references",
                    "expected": "dict",
                    "actual": type(references).__name__,
                }
            )
            continue
        expected_refs = {
            "source_manual_paper_intent_ledger_path": "pm_bot/paper/manual_paper_intent_ledger.v1.json",
            "source_paper_fill_events_path": "pm_bot/paper/paper_fill_events.v1.json",
            "source_paper_accounting_pnl_preview_path": "pm_bot/paper/paper_accounting_pnl_preview.v1.json",
        }
        for field, expected in expected_refs.items():
            actual = references.get(field)
            if actual != expected:
                mismatches.append(
                    {
                        "artifact_id": "paper_accounting_ledger",
                        "field_path": f"paper_accounting_ledger_entries[{index}].source_references.{field}",
                        "expected": expected,
                        "actual": actual,
                    }
                )
    return mismatches


def _active_chain_market_sets(artifacts):
    return {
        artifact_id: _market_ids(_records_for(artifacts, artifact_id), artifacts[artifact_id]["payload"])
        for artifact_id in ACTIVE_LIFECYCLE_ARTIFACTS
    }


def _manual_count_ok(artifacts):
    accepted = artifacts["manual_paper_intents_accepted"]["payload"]
    ledger = artifacts["manual_paper_intent_ledger"]["payload"]
    accepted_records = _records_for(artifacts, "manual_paper_intents_accepted")
    ledger_entries = _records_for(artifacts, "manual_paper_intent_ledger")
    return (
        _count_value(accepted, "records_accepted") == len(accepted_records)
        and _count_value(ledger, "manual_paper_intent_ledger_entries") == len(ledger_entries)
        and len(accepted_records) == len(ledger_entries)
    )


def _fixture_partition_summary(artifacts, prefix):
    fixture_id = f"paper_{prefix}_source_fixture"
    accepted_id = f"paper_{prefix}_sources_accepted"
    rejected_id = f"paper_{prefix}_sources_rejected"
    fixture_payload = artifacts[fixture_id]["payload"]
    accepted_payload = artifacts[accepted_id]["payload"]
    rejected_payload = artifacts[rejected_id]["payload"]
    fixture_records = _records_for(artifacts, fixture_id)
    accepted_records = _records_for(artifacts, accepted_id)
    rejected_records = _records_for(artifacts, rejected_id)
    accepted_count_key = "records_accepted"
    rejected_count_key = "records_rejected"
    read_count = len(fixture_records)
    if _count_value(accepted_payload, "records_read") is not None:
        read_count = _count_value(accepted_payload, "records_read")
    return {
        "fixture_records": len(fixture_records),
        "records_read": read_count,
        "accepted_records": len(accepted_records),
        "rejected_records": len(rejected_records),
        "accepted_count": _count_value(accepted_payload, accepted_count_key),
        "rejected_count": _count_value(rejected_payload, rejected_count_key),
        "partition_total": len(accepted_records) + len(rejected_records),
    }


def _fixture_partition_ok(summary):
    return (
        summary["fixture_records"] == summary["records_read"]
        and summary["accepted_records"] == summary["accepted_count"]
        and summary["rejected_records"] == summary["rejected_count"]
        and summary["partition_total"] == summary["fixture_records"]
    )


def _record_count_summary(artifacts):
    return {
        "manual_intents_accepted": len(_records_for(artifacts, "manual_paper_intents_accepted")),
        "manual_ledger_entries": len(_records_for(artifacts, "manual_paper_intent_ledger")),
        "fill_sources_accepted": len(_records_for(artifacts, "paper_fill_sources_accepted")),
        "fill_events": len(_records_for(artifacts, "paper_fill_events")),
        "settlement_sources_accepted": len(_records_for(artifacts, "paper_settlement_sources_accepted")),
        "pnl_records": len(_records_for(artifacts, "paper_accounting_pnl_preview")),
        "accounting_ledger_entries": len(_records_for(artifacts, "paper_accounting_ledger")),
        "portfolio_positions": len(_records_for(artifacts, "paper_portfolio_snapshot")),
        "metrics_records": _counts(artifacts["paper_metrics_report"]["payload"]).get("paper_metrics_report_records"),
    }


def _record_counts_ok(summary):
    values = list(summary.values())
    return values and all(value == values[0] for value in values)


def _linkage_mismatches(artifacts):
    mismatches = []
    manual_accepted = _by_id(_records_for(artifacts, "manual_paper_intents_accepted"), "intent_id")
    manual_ledger = _by_id(_records_for(artifacts, "manual_paper_intent_ledger"), "ledger_entry_id")
    fill_accepted = _by_id(_records_for(artifacts, "paper_fill_sources_accepted"), "fill_source_id")
    fill_events = _by_id(_records_for(artifacts, "paper_fill_events"), "paper_fill_event_id")
    settlements = _by_id(_records_for(artifacts, "paper_settlement_sources_accepted"), "settlement_source_id")
    pnl_records = _by_id(_records_for(artifacts, "paper_accounting_pnl_preview"), "paper_accounting_record_id")
    ledger_entries = _by_id(_records_for(artifacts, "paper_accounting_ledger"), "paper_accounting_ledger_entry_id")
    positions = _records_for(artifacts, "paper_portfolio_snapshot")

    for ledger_id, entry in manual_ledger.items():
        if entry.get("source_intent_id") not in manual_accepted:
            mismatches.append(f"manual ledger {ledger_id} source_intent_id not in accepted intents")

    for fill_id, record in fill_accepted.items():
        if record.get("source_manual_intent_id") not in manual_accepted:
            mismatches.append(f"fill source {fill_id} source_manual_intent_id not in accepted intents")
        if record.get("source_ledger_entry_id") not in manual_ledger:
            mismatches.append(f"fill source {fill_id} source_ledger_entry_id not in manual ledger")

    for event_id, record in fill_events.items():
        source_fill_id = record.get("source_fill_source_id")
        source_fill = fill_accepted.get(source_fill_id)
        if source_fill is None:
            mismatches.append(f"fill event {event_id} source_fill_source_id not in accepted fill sources")
            continue
        for field in ("market_id", "source_manual_intent_id", "source_ledger_entry_id"):
            if record.get(field) != source_fill.get(field):
                mismatches.append(f"fill event {event_id} {field} does not match accepted fill source")

    for settlement_id, record in settlements.items():
        fill_event = fill_events.get(record.get("source_paper_fill_event_id"))
        if fill_event is None:
            mismatches.append(f"settlement {settlement_id} source_paper_fill_event_id not in fill events")
            continue
        for field in ("market_id", "source_manual_intent_id", "source_ledger_entry_id"):
            if record.get(field) != fill_event.get(field):
                mismatches.append(f"settlement {settlement_id} {field} does not match fill event")

    for pnl_id, record in pnl_records.items():
        if record.get("source_paper_fill_event_id") not in fill_events:
            mismatches.append(f"accounting record {pnl_id} source_paper_fill_event_id not in fill events")
        if record.get("source_settlement_id") not in settlements:
            mismatches.append(f"accounting record {pnl_id} source_settlement_id not in accepted settlements")

    for ledger_id, entry in ledger_entries.items():
        references = entry.get("source_references") if isinstance(entry.get("source_references"), dict) else {}
        if references.get("source_paper_accounting_record_id") not in pnl_records:
            mismatches.append(f"accounting ledger entry {ledger_id} source accounting record not in PnL preview")
        if references.get("source_paper_fill_event_id") not in fill_events:
            mismatches.append(f"accounting ledger entry {ledger_id} source fill event not in fill events")
        if references.get("source_settlement_id") not in settlements:
            mismatches.append(f"accounting ledger entry {ledger_id} source settlement not in accepted settlements")
        if references.get("source_ledger_entry_id") not in manual_ledger:
            mismatches.append(f"accounting ledger entry {ledger_id} source ledger entry not in manual ledger")

    for position in positions:
        source_entry_id = position.get("source_paper_accounting_ledger_entry_id")
        if source_entry_id not in ledger_entries:
            mismatches.append(f"portfolio position {position.get('market_id')} source ledger entry not in accounting ledger")

    return sorted(mismatches)


def _computed_pnl_rows(artifacts):
    fill_events = _by_id(_records_for(artifacts, "paper_fill_events"), "paper_fill_event_id")
    settlements = _by_id(_records_for(artifacts, "paper_settlement_sources_accepted"), "settlement_source_id")
    pnl_records = _records_for(artifacts, "paper_accounting_pnl_preview")
    rows = []
    for record in pnl_records:
        fill_event = fill_events.get(record.get("source_paper_fill_event_id"))
        settlement = settlements.get(record.get("source_settlement_id"))
        fill_price = _decimal_from_value(fill_event.get("operator_manual_fill_price")) if fill_event else None
        fill_size = _decimal_from_value(fill_event.get("operator_manual_fill_size")) if fill_event else None
        settlement_price = (
            _decimal_from_value(settlement.get("operator_manual_settlement_price")) if settlement else None
        )
        if fill_price is None or fill_size is None or settlement_price is None:
            rows.append({"record_id": record.get("paper_accounting_record_id"), "valid": False})
            continue
        cost_basis = fill_price * fill_size
        settlement_value = settlement_price * fill_size
        pnl = settlement_value - cost_basis
        rows.append(
            {
                "record_id": record.get("paper_accounting_record_id"),
                "valid": True,
                "cost_basis": _format_decimal(cost_basis),
                "settlement_value": _format_decimal(settlement_value),
                "pnl": _format_decimal(pnl),
                "record_cost_basis": record.get("paper_accounting_cost_basis"),
                "record_settlement_value": record.get("paper_accounting_settlement_value"),
                "record_pnl": record.get("paper_accounting_pnl"),
            }
        )
    return rows


def _pnl_value_mismatches(artifacts):
    mismatches = []
    computed_rows = _computed_pnl_rows(artifacts)
    pnl_records = _by_id(_records_for(artifacts, "paper_accounting_pnl_preview"), "paper_accounting_record_id")
    ledger_entries = _records_for(artifacts, "paper_accounting_ledger")
    portfolio_positions = _records_for(artifacts, "paper_portfolio_snapshot")

    for row in computed_rows:
        if not row["valid"]:
            mismatches.append(f"accounting record {row['record_id']} cannot be recomputed from local fill and settlement")
            continue
        for computed_key, record_key in (
            ("cost_basis", "record_cost_basis"),
            ("settlement_value", "record_settlement_value"),
            ("pnl", "record_pnl"),
        ):
            if row[computed_key] != row[record_key]:
                mismatches.append(f"accounting record {row['record_id']} {computed_key} mismatch")

    for entry in ledger_entries:
        references = entry.get("source_references") if isinstance(entry.get("source_references"), dict) else {}
        source_record = pnl_records.get(references.get("source_paper_accounting_record_id"))
        if source_record is None:
            continue
        for field in (
            "paper_accounting_cost_basis",
            "paper_accounting_settlement_value",
            "paper_accounting_pnl",
        ):
            if entry.get(field) != source_record.get(field):
                mismatches.append(f"ledger entry {entry.get('paper_accounting_ledger_entry_id')} {field} mismatch")

    ledger_by_id = _by_id(ledger_entries, "paper_accounting_ledger_entry_id")
    for position in portfolio_positions:
        entry = ledger_by_id.get(position.get("source_paper_accounting_ledger_entry_id"))
        if entry is None:
            continue
        for field in (
            "paper_accounting_cost_basis",
            "paper_accounting_settlement_value",
            "paper_accounting_pnl",
            "paper_accounting_cumulative_pnl",
        ):
            if position.get(field) != entry.get(field):
                mismatches.append(f"portfolio position {position.get('market_id')} {field} mismatch")

    return sorted(mismatches)


def _computed_metrics_from_ledger(artifacts):
    ledger_entries = _records_for(artifacts, "paper_accounting_ledger")
    pnl_values = []
    settled_count = 0
    open_count = 0
    for entry in ledger_entries:
        if entry.get("paper_position_status") == "paper_position_settled":
            settled_count += 1
        else:
            open_count += 1
        pnl = _decimal_from_value(entry.get("paper_accounting_pnl"))
        if pnl is not None:
            pnl_values.append(pnl)
    total = len(ledger_entries)
    cumulative = sum(pnl_values, Decimal("0.00"))
    wins = sum(1 for value in pnl_values if value > Decimal("0.00"))
    losses = sum(1 for value in pnl_values if value < Decimal("0.00"))
    flats = sum(1 for value in pnl_values if value == Decimal("0.00"))
    gross_profit = sum((value for value in pnl_values if value > Decimal("0.00")), Decimal("0.00"))
    gross_loss = sum((value for value in pnl_values if value < Decimal("0.00")), Decimal("0.00"))
    average = cumulative / Decimal(total) if total else Decimal("0.00")
    max_gain = max(pnl_values) if pnl_values else Decimal("0.00")
    max_loss = min(pnl_values) if pnl_values else Decimal("0.00")
    if max_gain < Decimal("0.00"):
        max_gain = Decimal("0.00")
    if max_loss > Decimal("0.00"):
        max_loss = Decimal("0.00")
    return {
        "paper_accounting_total_records": total,
        "paper_accounting_settled_count": settled_count,
        "paper_accounting_open_count": open_count,
        "paper_accounting_win_count": wins,
        "paper_accounting_loss_count": losses,
        "paper_accounting_flat_count": flats,
        "paper_accounting_cumulative_pnl": _format_decimal(cumulative),
        "paper_accounting_average_pnl": _format_decimal(average),
        "paper_accounting_gross_profit": _format_decimal(gross_profit),
        "paper_accounting_gross_loss": _format_decimal(gross_loss),
        "paper_accounting_max_gain": _format_decimal(max_gain),
        "paper_accounting_max_loss": _format_decimal(max_loss),
    }


def _metrics_mismatches(artifacts):
    metrics_payload = artifacts["paper_metrics_report"]["payload"]
    portfolio_payload = artifacts["paper_portfolio_snapshot"]["payload"]
    actual_metrics = metrics_payload.get("paper_accounting_metrics")
    if not isinstance(actual_metrics, dict):
        return ["paper metrics report missing paper_accounting_metrics"]
    computed = _computed_metrics_from_ledger(artifacts)
    mismatches = []
    for key, expected in computed.items():
        if actual_metrics.get(key) != expected:
            mismatches.append(f"metrics report {key} mismatch")
    portfolio_expected = {
        "paper_accounting_settled_count": computed["paper_accounting_settled_count"],
        "paper_accounting_open_count": computed["paper_accounting_open_count"],
        "paper_accounting_position_count": computed["paper_accounting_total_records"],
        "paper_accounting_cumulative_pnl": computed["paper_accounting_cumulative_pnl"],
        "paper_accounting_gross_profit": computed["paper_accounting_gross_profit"],
        "paper_accounting_gross_loss": computed["paper_accounting_gross_loss"],
    }
    for key, expected in portfolio_expected.items():
        if portfolio_payload.get(key) != expected:
            mismatches.append(f"portfolio snapshot {key} mismatch")
    return sorted(mismatches)


def _status_mismatches(artifacts):
    ledger_payload = artifacts["paper_accounting_ledger"]["payload"]
    portfolio_payload = artifacts["paper_portfolio_snapshot"]["payload"]
    metrics_payload = artifacts["paper_metrics_report"]["payload"]
    ledger_entries = _records_for(artifacts, "paper_accounting_ledger")
    settled_count = sum(1 for entry in ledger_entries if entry.get("paper_position_status") == "paper_position_settled")
    open_count = sum(1 for entry in ledger_entries if entry.get("paper_position_status") != "paper_position_settled")
    metrics = metrics_payload.get("paper_accounting_metrics") if isinstance(metrics_payload.get("paper_accounting_metrics"), dict) else {}
    expected = {
        "ledger_settled": _count_value(ledger_payload, "paper_accounting_settled_count"),
        "ledger_open": _count_value(ledger_payload, "paper_accounting_open_count"),
        "portfolio_settled": portfolio_payload.get("paper_accounting_settled_count"),
        "portfolio_open": portfolio_payload.get("paper_accounting_open_count"),
        "metrics_settled": metrics.get("paper_accounting_settled_count"),
        "metrics_open": metrics.get("paper_accounting_open_count"),
    }
    mismatches = []
    for key, actual in expected.items():
        target = settled_count if key.endswith("settled") else open_count
        if actual != target:
            mismatches.append(f"{key} expected {target} from accounting ledger, got {actual}")
    return sorted(mismatches)


def _safety_mismatches(artifacts):
    mismatches = []
    for artifact_id in ACTIVE_LIFECYCLE_ARTIFACTS:
        payload = artifacts[artifact_id]["payload"]
        counts = _counts(payload)
        for key in ("real_orders_created", "live_orders_created", "autonomous_paper_orders_created"):
            if key in counts and counts.get(key) != 0:
                mismatches.append(f"{artifact_id} count {key} is not zero")
        for record in _records_for(artifacts, artifact_id):
            for key, expected in (
                ("paper_only", True),
                ("inert_only", True),
                ("generated_by_bot", False),
                ("live_order_created", False),
                ("real_order_created", False),
            ):
                if key in record and record.get(key) is not expected:
                    mismatches.append(f"{artifact_id} record {record.get('market_id')} {key} is not {expected}")
    for artifact_id in ("paper_portfolio_snapshot", "paper_metrics_report"):
        flags = artifacts[artifact_id]["payload"].get("safety_flags")
        if not isinstance(flags, list):
            mismatches.append(f"{artifact_id} missing safety_flags list")
            continue
        for flag in ("paper_only", "inert_only", "paper_accounting_only", "no_live_execution", "no_real_execution"):
            if flag not in flags:
                mismatches.append(f"{artifact_id} missing safety flag {flag}")
    return sorted(mismatches)


def _accounting_summary(artifacts):
    metrics = artifacts["paper_metrics_report"]["payload"].get("paper_accounting_metrics", {})
    return {
        "paper_accounting_total_records": metrics.get("paper_accounting_total_records"),
        "settled_count": metrics.get("paper_accounting_settled_count"),
        "open_count": metrics.get("paper_accounting_open_count"),
        "win_count": metrics.get("paper_accounting_win_count"),
        "loss_count": metrics.get("paper_accounting_loss_count"),
        "flat_count": metrics.get("paper_accounting_flat_count"),
        "cumulative_pnl": metrics.get("paper_accounting_cumulative_pnl"),
        "gross_profit": metrics.get("paper_accounting_gross_profit"),
        "gross_loss": metrics.get("paper_accounting_gross_loss"),
        "average_pnl": metrics.get("paper_accounting_average_pnl"),
        "max_gain": metrics.get("paper_accounting_max_gain"),
        "max_loss": metrics.get("paper_accounting_max_loss"),
    }


def _audit_status(checks):
    if any(check["status"] == "fail" for check in checks):
        return "reconciliation_failed"
    if any(check["status"] == "warning" for check in checks):
        return "reconciliation_passed_with_warnings"
    return "reconciliation_passed"


def build_reconciliation_audit(artifacts):
    checks = []

    artifact_summaries = _artifact_summaries(artifacts)
    missing_artifacts = [item["path"] for item in artifact_summaries if item["schema_version"] is None]
    checks.append(
        _check(
            "pass" if not missing_artifacts else "fail",
            "required_artifacts_present",
            "All required local paper artifacts were loaded." if not missing_artifacts else "Required paper artifacts are missing.",
            expected=[],
            actual=missing_artifacts,
            artifacts=[item["path"] for item in artifact_summaries],
        )
    )

    deterministic_failures = [
        item["artifact_id"] for item in artifact_summaries if item.get("deterministic") is not True
    ]
    checks.append(
        _check(
            "pass" if not deterministic_failures else "fail",
            "deterministic_flags",
            "All checked artifacts declare deterministic output."
            if not deterministic_failures
            else "One or more checked artifacts do not declare deterministic output.",
            expected=[],
            actual=deterministic_failures,
        )
    )

    active_markets = _active_chain_market_sets(artifacts)
    market_mismatches = {
        artifact_id: values for artifact_id, values in active_markets.items() if values != [MARKET_ID]
    }
    checks.append(
        _check(
            "pass" if not market_mismatches else "fail",
            "market_id_consistency",
            "Accepted lifecycle artifacts consistently reference market 824952."
            if not market_mismatches
            else "Accepted lifecycle artifact market ids differ from the expected market.",
            expected={artifact_id: [MARKET_ID] for artifact_id in active_markets},
            actual=active_markets,
        )
    )

    checks.append(
        _check(
            "pass" if _manual_count_ok(artifacts) else "fail",
            "manual_intent_ledger_count_consistency",
            "Accepted manual intent count matches inert manual paper ledger entries.",
            expected={"accepted_intents": 1, "ledger_entries": 1},
            actual={
                "accepted_intents": len(_records_for(artifacts, "manual_paper_intents_accepted")),
                "ledger_entries": len(_records_for(artifacts, "manual_paper_intent_ledger")),
            },
        )
    )

    fill_partition = _fixture_partition_summary(artifacts, "fill")
    checks.append(
        _check(
            "pass" if _fixture_partition_ok(fill_partition) else "fail",
            "fill_fixture_partition_consistency",
            "Manual fill fixture records partition into accepted and rejected fill source artifacts.",
            expected={"partition_total_equals_fixture_records": True},
            actual=fill_partition,
        )
    )

    settlement_partition = _fixture_partition_summary(artifacts, "settlement")
    checks.append(
        _check(
            "pass" if _fixture_partition_ok(settlement_partition) else "fail",
            "settlement_fixture_partition_consistency",
            "Manual settlement fixture records partition into accepted and rejected settlement source artifacts.",
            expected={"partition_total_equals_fixture_records": True},
            actual=settlement_partition,
        )
    )

    record_counts = _record_count_summary(artifacts)
    checks.append(
        _check(
            "pass" if _record_counts_ok(record_counts) else "fail",
            "accepted_lifecycle_record_count_consistency",
            "Accepted lifecycle artifacts each carry one reconciled accounting record.",
            expected={"all_active_record_counts": 1},
            actual=record_counts,
        )
    )

    pointer_mismatches = _pointer_mismatches(artifacts)
    checks.append(
        _check(
            "pass" if not pointer_mismatches else "fail",
            "artifact_pointer_consistency",
            "Artifact pointer fields reference the expected local paper artifacts.",
            expected=[],
            actual=pointer_mismatches,
        )
    )

    linkage_mismatches = _linkage_mismatches(artifacts)
    checks.append(
        _check(
            "pass" if not linkage_mismatches else "fail",
            "fill_settlement_accounting_linkage",
            "Manual intent, fill, settlement, accounting, ledger, and portfolio ids link across artifacts.",
            expected=[],
            actual=linkage_mismatches,
        )
    )

    status_mismatches = _status_mismatches(artifacts)
    checks.append(
        _check(
            "pass" if not status_mismatches else "fail",
            "closed_open_status_consistency",
            "Closed and open position counts match accounting ledger, portfolio, and metrics artifacts.",
            expected=[],
            actual=status_mismatches,
        )
    )

    pnl_mismatches = _pnl_value_mismatches(artifacts)
    checks.append(
        _check(
            "pass" if not pnl_mismatches else "fail",
            "pnl_value_consistency",
            "Accounting PnL values reconcile from local manual fill and settlement fixture values.",
            expected=[],
            actual=pnl_mismatches,
        )
    )

    metric_mismatches = _metrics_mismatches(artifacts)
    checks.append(
        _check(
            "pass" if not metric_mismatches else "fail",
            "portfolio_metrics_consistency",
            "Portfolio snapshot and metrics report values match the accounting ledger.",
            expected=_computed_metrics_from_ledger(artifacts),
            actual=artifacts["paper_metrics_report"]["payload"].get("paper_accounting_metrics"),
        )
    )

    safety_mismatches = _safety_mismatches(artifacts)
    checks.append(
        _check(
            "pass" if not safety_mismatches else "fail",
            "safety_flag_consistency",
            "Accepted lifecycle artifacts remain paper-only, inert, local, and non-executable.",
            expected=[],
            actual=safety_mismatches,
        )
    )

    prohibited_active_fields = _find_prohibited_active_fields(artifacts)
    checks.append(
        _check(
            "pass" if not prohibited_active_fields else "fail",
            "no_scoring_probability_ev_edge_or_recommendation_fields",
            "Accepted lifecycle artifacts contain no scoring, probability, EV, edge, recommendation, or market-decision fields.",
            expected=[],
            actual=prohibited_active_fields,
        )
    )

    mismatches = [check for check in checks if check["status"] == "fail"]
    warnings = [check for check in checks if check["status"] == "warning"]
    status = _audit_status(checks)
    return {
        "schema_version": "paper_accounting_reconciliation_audit.v1",
        "markdown_version": "paper_accounting_reconciliation_audit_markdown.v1",
        "task_id": TASK_ID,
        "market_id": MARKET_ID,
        "audit_status": status,
        "deterministic": True,
        "artifacts_checked": artifact_summaries,
        "checks": checks,
        "mismatches": mismatches,
        "warnings": warnings,
        "accounting_summary": _accounting_summary(artifacts),
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
            "truth_inference": False,
            "recommendations": False,
        },
        "paper_orders_created": 0,
        "autonomous_actions_created": 0,
        "next_safe_action": "ready_for_integration_review"
        if status != "reconciliation_failed"
        else "requires_operator_review",
    }


def render_audit_markdown(audit):
    summary = audit["accounting_summary"]
    lines = [
        "# PMBOT PAPER-017 Accounting Reconciliation Audit",
        "",
        f"- Task ID: `{audit['task_id']}`",
        f"- Market ID: `{audit['market_id']}`",
        f"- Audit status: `{audit['audit_status']}`",
        f"- Paper orders created: `{audit['paper_orders_created']}`",
        f"- Autonomous actions created: `{audit['autonomous_actions_created']}`",
        f"- Next safe action: `{audit['next_safe_action']}`",
        "",
        "## Accounting Summary",
        "",
        "| Metric | Value |",
        "| --- | ---: |",
    ]
    for key in (
        "paper_accounting_total_records",
        "settled_count",
        "open_count",
        "win_count",
        "loss_count",
        "flat_count",
        "cumulative_pnl",
        "gross_profit",
        "gross_loss",
        "average_pnl",
        "max_gain",
        "max_loss",
    ):
        lines.append(f"| `{key}` | `{summary.get(key)}` |")
    lines.extend(
        [
            "",
            "## Artifacts Checked",
            "",
            "| Artifact | Records | Market IDs | Path |",
            "| --- | ---: | --- | --- |",
        ]
    )
    for artifact in audit["artifacts_checked"]:
        market_ids = ", ".join(artifact["market_ids"])
        lines.append(
            f"| `{artifact['artifact_id']}` | `{artifact['record_count']}` | `{market_ids}` | `{artifact['path']}` |"
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
    for check in audit["checks"]:
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


def _paper_017_result(audit, missing_optional_docs):
    completed = audit["audit_status"] != "reconciliation_failed"
    return {
        "task_id": TASK_ID,
        "status": "completed_ready_for_review" if completed else "blocked",
        "summary": (
            "Implemented deterministic offline paper accounting reconciliation lifecycle audit."
            if completed
            else "Paper accounting reconciliation lifecycle audit found structural mismatches."
        ),
        "market_id": MARKET_ID,
        "audit_status": audit["audit_status"],
        "counts": {
            "artifacts_checked": len(audit["artifacts_checked"]),
            "checks_total": len(audit["checks"]),
            "checks_passed": sum(1 for check in audit["checks"] if check["status"] == "pass"),
            "checks_warning": sum(1 for check in audit["checks"] if check["status"] == "warning"),
            "checks_failed": sum(1 for check in audit["checks"] if check["status"] == "fail"),
            "paper_orders_created": audit["paper_orders_created"],
            "autonomous_actions_created": audit["autonomous_actions_created"],
        },
        "accounting_summary": audit["accounting_summary"],
        "files_created": FILES_CREATED,
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
        "blockers": [] if completed else ["audit structural mismatches must be reviewed before integration"],
        "next_action": "ready_for_integration_review" if completed else "requires_operator_review",
    }


def write_paper_accounting_reconciliation_audit():
    artifacts = _load_artifacts()
    audit = build_reconciliation_audit(artifacts)
    missing_optional_docs = _missing_optional_docs()
    _write_json(DEFAULT_AUDIT, audit)
    _write_json(DEFAULT_AUDIT_EXPECTED, audit)
    _write_text(DEFAULT_AUDIT_MD, render_audit_markdown(audit))
    _write_json(DEFAULT_RESULT, _paper_017_result(audit, missing_optional_docs))
    return {
        "task_id": TASK_ID,
        "market_id": MARKET_ID,
        "audit_status": audit["audit_status"],
        "checks_total": len(audit["checks"]),
        "checks_failed": len(audit["mismatches"]),
        "warnings": len(audit["warnings"]),
        "missing_optional_docs": missing_optional_docs,
        "result_path": _display_path(DEFAULT_RESULT),
    }


def main(argv):
    _parse_args(argv)
    try:
        summary = write_paper_accounting_reconciliation_audit()
    except Exception as exc:
        blocked = {
            "task_id": TASK_ID,
            "status": "blocked",
            "summary": "Blocked before completing deterministic offline paper accounting reconciliation audit.",
            "market_id": MARKET_ID,
            "audit_status": "reconciliation_failed",
            "counts": {
                "artifacts_checked": 0,
                "checks_total": 0,
                "checks_passed": 0,
                "checks_warning": 0,
                "checks_failed": 1,
                "paper_orders_created": 0,
                "autonomous_actions_created": 0,
            },
            "accounting_summary": {},
            "files_created": [],
            "files_modified": [],
            "tests": [],
            "warnings": [],
            "missing_optional_docs": _missing_optional_docs(),
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
            "blockers": [str(exc)],
            "next_action": "requires_operator_review",
        }
        _write_json(DEFAULT_RESULT, blocked)
        print(json.dumps({"task_id": TASK_ID, "status": "blocked", "blockers": [str(exc)]}, indent=2, ensure_ascii=True))
        return 2
    print(json.dumps(summary, indent=2, ensure_ascii=True))
    return 0 if summary["audit_status"] != "reconciliation_failed" else 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
