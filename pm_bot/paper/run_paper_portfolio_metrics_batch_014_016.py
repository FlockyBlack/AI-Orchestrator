import argparse
import json
import sys
from decimal import Decimal, InvalidOperation
from pathlib import Path


TASK_ID = "PMBOT-PAPER-BATCH-014-016-PAPER-PORTFOLIO-METRICS-MVP"
ROOT = Path(__file__).resolve().parents[2]
PAPER_DIR = ROOT / "pm_bot" / "paper"
DOCS_DIR = ROOT / "docs"

DEFAULT_PNL_PREVIEW = PAPER_DIR / "paper_accounting_pnl_preview.v1.json"
DEFAULT_FILL_EVENTS = PAPER_DIR / "paper_fill_events.v1.json"
DEFAULT_MANUAL_LEDGER = PAPER_DIR / "manual_paper_intent_ledger.v1.json"

DEFAULT_ACCOUNTING_LEDGER = PAPER_DIR / "paper_accounting_ledger.v1.json"
DEFAULT_ACCOUNTING_LEDGER_MD = PAPER_DIR / "paper_accounting_ledger.v1.md"
DEFAULT_ACCOUNTING_LEDGER_EXPECTED = PAPER_DIR / "expected_paper_accounting_ledger.v1.json"

DEFAULT_PORTFOLIO_SNAPSHOT = PAPER_DIR / "paper_portfolio_snapshot.v1.json"
DEFAULT_PORTFOLIO_SNAPSHOT_MD = PAPER_DIR / "paper_portfolio_snapshot.v1.md"
DEFAULT_PORTFOLIO_SNAPSHOT_EXPECTED = PAPER_DIR / "expected_paper_portfolio_snapshot.v1.json"

DEFAULT_METRICS_REPORT = PAPER_DIR / "paper_metrics_report.v1.json"
DEFAULT_METRICS_REPORT_MD = PAPER_DIR / "paper_metrics_report.v1.md"
DEFAULT_METRICS_REPORT_EXPECTED = PAPER_DIR / "expected_paper_metrics_report.v1.json"

DEFAULT_RESULT = DOCS_DIR / "PMBOT_PAPER_BATCH_014_016_RESULT.json"

ALLOWED_ACCOUNTING_ENTRY_STATUSES = (
    "paper_accounting_entry_recorded",
    "paper_accounting_entry_pending_settlement",
    "paper_accounting_entry_blocked_invalid_source",
)
ALLOWED_PORTFOLIO_STATUSES = (
    "paper_portfolio_snapshot_ready",
    "paper_portfolio_snapshot_empty",
    "paper_portfolio_snapshot_blocked_invalid_ledger",
)
SETTLED_PREVIEW_STATUS = "paper_position_settled_from_operator_manual_fixture"
OPEN_PREVIEW_STATUS = "paper_position_open_pending_settlement"
ALLOWED_PREVIEW_STATUSES = (
    OPEN_PREVIEW_STATUS,
    SETTLED_PREVIEW_STATUS,
    "paper_position_blocked_invalid_settlement",
    "paper_position_watch_only",
)
PROHIBITED_FIELD_NAMES = (
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
    "order",
    "real_order",
    "live_order",
    "wallet",
    "private_key",
    "api_key",
    "auth",
    "trading_endpoint",
)
PROHIBITED_FIELD_TOKENS = set(PROHIBITED_FIELD_NAMES) | {
    "probabilities",
    "expected_values",
    "edges",
    "scores",
    "recommendations",
    "decisions",
    "orders",
    "wallets",
    "private_keys",
    "api_keys",
}
SAFETY_FIELD_EXEMPTIONS = {
    "real_order_created",
    "live_order_created",
    "real_orders_created",
    "live_orders_created",
    "autonomous_paper_orders_created",
}
BLOCKED_VALUE_MARKERS = (
    "bot-generated",
    "bot generated",
    "bot recommendation",
    "recommends",
    "recommendation",
    "live order",
    "real order",
    "place order",
    "execute trade",
    "wallet",
    "private key",
    "api key",
    "trading endpoint",
    "autonomous",
)
FILES_CREATED = [
    "pm_bot/paper/run_paper_portfolio_metrics_batch_014_016.py",
    "pm_bot/paper/paper_accounting_ledger.v1.json",
    "pm_bot/paper/paper_accounting_ledger.v1.md",
    "pm_bot/paper/expected_paper_accounting_ledger.v1.json",
    "pm_bot/paper/paper_portfolio_snapshot.v1.json",
    "pm_bot/paper/paper_portfolio_snapshot.v1.md",
    "pm_bot/paper/expected_paper_portfolio_snapshot.v1.json",
    "pm_bot/paper/paper_metrics_report.v1.json",
    "pm_bot/paper/paper_metrics_report.v1.md",
    "pm_bot/paper/expected_paper_metrics_report.v1.json",
    "pm_bot/paper/tests/test_paper_portfolio_metrics_batch_014_016.py",
    "docs/PMBOT_PAPER_BATCH_014_016_RESULT.json",
]
ZERO_METRICS = {
    "paper_accounting_total_records": 0,
    "paper_accounting_settled_count": 0,
    "paper_accounting_open_count": 0,
    "paper_accounting_win_count": 0,
    "paper_accounting_loss_count": 0,
    "paper_accounting_flat_count": 0,
    "paper_accounting_cumulative_pnl": "0.00",
    "paper_accounting_gross_profit": "0.00",
    "paper_accounting_gross_loss": "0.00",
    "paper_accounting_average_pnl": "0.00",
    "paper_accounting_max_gain": "0.00",
    "paper_accounting_max_loss": "0.00",
}


def _parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Run deterministic offline PAPER-014 through PAPER-016 paper portfolio metrics artifacts."
    )
    parser.add_argument("--pnl-preview", default=str(DEFAULT_PNL_PREVIEW.relative_to(ROOT)))
    parser.add_argument("--fill-events", default=str(DEFAULT_FILL_EVENTS.relative_to(ROOT)))
    parser.add_argument("--manual-ledger", default=str(DEFAULT_MANUAL_LEDGER.relative_to(ROOT)))
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


def _clean_text(value):
    if value is None:
        return ""
    return str(value).strip()


def _records(payload, field):
    records = payload.get(field)
    if not isinstance(records, list):
        raise ValueError(f"payload must contain {field} list")
    return [record for record in records if isinstance(record, dict)]


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
    quantized = Decimal(value).quantize(Decimal("0.01"))
    if quantized == Decimal("-0.00"):
        quantized = Decimal("0.00")
    return format(quantized, ".2f")


def _field_tokens(key):
    lower = str(key).lower()
    normalized_chars = []
    previous_was_separator = False
    for char in lower:
        if char.isalnum():
            normalized_chars.append(char)
            previous_was_separator = False
        elif not previous_was_separator:
            normalized_chars.append("_")
            previous_was_separator = True
    normalized_key = "".join(normalized_chars).strip("_")
    parts = [part for part in normalized_key.split("_") if part]
    tokens = {lower, normalized_key}
    tokens.update(parts)
    for index in range(len(parts) - 1):
        tokens.add(f"{parts[index]}_{parts[index + 1]}")
    for index in range(len(parts) - 2):
        tokens.add(f"{parts[index]}_{parts[index + 1]}_{parts[index + 2]}")
    return {token for token in tokens if token}


def _walk_keys(value):
    if isinstance(value, dict):
        for key, nested in value.items():
            yield str(key)
            yield from _walk_keys(nested)
    elif isinstance(value, list):
        for item in value:
            yield from _walk_keys(item)


def _walk_string_values(value):
    if isinstance(value, dict):
        for nested in value.values():
            yield from _walk_string_values(nested)
    elif isinstance(value, list):
        for item in value:
            yield from _walk_string_values(item)
    elif isinstance(value, str):
        yield value


def _blocked_keys(record):
    blocked = []
    for key in _walk_keys(record):
        if key in SAFETY_FIELD_EXEMPTIONS:
            continue
        if _field_tokens(key) & PROHIBITED_FIELD_TOKENS:
            blocked.append(key)
    return sorted(set(blocked))


def _blocked_value_markers(record):
    markers = []
    for value in _walk_string_values(record):
        lower = value.lower()
        for marker in BLOCKED_VALUE_MARKERS:
            if marker in lower:
                markers.append(marker)
    return sorted(set(markers))


def _preview_by_record_id(preview_payload):
    return {
        _clean_text(record.get("paper_accounting_record_id")): record
        for record in _records(preview_payload, "paper_accounting_records")
        if _clean_text(record.get("paper_accounting_record_id"))
    }


def _fill_events_by_id(fill_events_payload):
    return {
        _clean_text(record.get("paper_fill_event_id")): record
        for record in _records(fill_events_payload, "paper_fill_events")
        if _clean_text(record.get("paper_fill_event_id"))
    }


def _manual_entries_by_id(manual_ledger_payload):
    return {
        _clean_text(record.get("ledger_entry_id")): record
        for record in _records(manual_ledger_payload, "ledger_entries")
        if _clean_text(record.get("ledger_entry_id"))
    }


def _manual_entries_by_intent_id(manual_ledger_payload):
    return {
        _clean_text(record.get("source_intent_id")): record
        for record in _records(manual_ledger_payload, "ledger_entries")
        if _clean_text(record.get("source_intent_id"))
    }


def _validate_zero_execution_counts(payload, label):
    counts = payload.get("counts", {})
    for field in ("real_orders_created", "live_orders_created", "autonomous_paper_orders_created"):
        if counts.get(field, 0) != 0:
            raise ValueError(f"{label} is inconsistent: {field} must be 0")


def _validate_source_artifacts(pnl_payload, fill_events_payload, manual_ledger_payload):
    accounting_records = _records(pnl_payload, "paper_accounting_records")
    fill_events = _records(fill_events_payload, "paper_fill_events")
    manual_entries = _records(manual_ledger_payload, "ledger_entries")
    if not accounting_records:
        raise ValueError("paper accounting PnL preview contains no paper_accounting_records")
    if not fill_events:
        raise ValueError("paper fill events artifact contains no paper_fill_events")
    if not manual_entries:
        raise ValueError("manual paper intent ledger contains no ledger_entries")

    _validate_zero_execution_counts(pnl_payload, "paper accounting PnL preview")
    _validate_zero_execution_counts(fill_events_payload, "paper fill events artifact")
    _validate_zero_execution_counts(manual_ledger_payload, "manual paper intent ledger")

    accounting_markets = {_clean_text(record.get("market_id")) for record in accounting_records}
    fill_markets = {_clean_text(record.get("market_id")) for record in fill_events}
    manual_markets = {_clean_text(record.get("market_id")) for record in manual_entries}
    if "824952" not in accounting_markets:
        raise ValueError("paper accounting PnL preview does not contain required market_id 824952")
    if "824952" not in fill_markets:
        raise ValueError("paper fill events artifact does not contain required market_id 824952")
    if "824952" not in manual_markets:
        raise ValueError("manual paper intent ledger does not contain required market_id 824952")

    fill_events_by_id = _fill_events_by_id(fill_events_payload)
    manual_by_entry_id = _manual_entries_by_id(manual_ledger_payload)
    manual_by_intent_id = _manual_entries_by_intent_id(manual_ledger_payload)
    total_cost_basis = Decimal("0")
    total_settlement_value = Decimal("0")
    total_pnl = Decimal("0")

    for record in accounting_records:
        status = _clean_text(record.get("paper_accounting_status"))
        if status not in ALLOWED_PREVIEW_STATUSES:
            raise ValueError("paper accounting PnL preview contains unsupported paper_accounting_status")
        if record.get("paper_only") is not True:
            raise ValueError("paper accounting PnL preview record must have paper_only true")
        if record.get("inert_only") is not True:
            raise ValueError("paper accounting PnL preview record must have inert_only true")
        if record.get("generated_by_bot") is not False:
            raise ValueError("paper accounting PnL preview record must have generated_by_bot false")
        if record.get("live_order_created") is not False:
            raise ValueError("paper accounting PnL preview record must have live_order_created false")
        if record.get("real_order_created") is not False:
            raise ValueError("paper accounting PnL preview record must have real_order_created false")

        fill_event_id = _clean_text(record.get("source_paper_fill_event_id"))
        fill_event = fill_events_by_id.get(fill_event_id)
        if fill_event is None:
            raise ValueError("paper accounting PnL preview references an unknown paper fill event")
        if _clean_text(fill_event.get("market_id")) != _clean_text(record.get("market_id")):
            raise ValueError("paper accounting PnL preview market_id does not match source fill event")

        source_entry_id = _clean_text(record.get("source_ledger_entry_id"))
        source_intent_id = _clean_text(record.get("source_manual_intent_id"))
        if source_entry_id and source_entry_id not in manual_by_entry_id:
            raise ValueError("paper accounting PnL preview references an unknown manual ledger entry")
        if source_intent_id and source_intent_id not in manual_by_intent_id:
            raise ValueError("paper accounting PnL preview references an unknown manual intent")

        if status == SETTLED_PREVIEW_STATUS:
            cost_basis = _decimal_from_value(record.get("paper_accounting_cost_basis"))
            settlement_value = _decimal_from_value(record.get("paper_accounting_settlement_value"))
            pnl = _decimal_from_value(record.get("paper_accounting_pnl"))
            if cost_basis is None or settlement_value is None or pnl is None:
                raise ValueError("settled paper accounting PnL preview record has invalid decimal fields")
            if settlement_value - cost_basis != pnl:
                raise ValueError("settled paper accounting PnL preview record has inconsistent PnL")
            total_cost_basis += cost_basis
            total_settlement_value += settlement_value
            total_pnl += pnl

    totals = pnl_payload.get("paper_accounting_totals", {})
    if _format_decimal(total_cost_basis) != totals.get("paper_accounting_total_cost_basis"):
        raise ValueError("paper accounting PnL preview total cost basis is inconsistent")
    if _format_decimal(total_settlement_value) != totals.get("paper_accounting_total_settlement_value"):
        raise ValueError("paper accounting PnL preview total settlement value is inconsistent")
    if _format_decimal(total_pnl) != totals.get("paper_accounting_total_pnl"):
        raise ValueError("paper accounting PnL preview total PnL is inconsistent")

    required = _preview_by_record_id(pnl_payload).get("paper-accounting-pnl-001")
    if required is None:
        raise ValueError("paper accounting PnL preview is missing paper-accounting-pnl-001")
    if _clean_text(required.get("market_id")) != "824952":
        raise ValueError("paper-accounting-pnl-001 must be market_id 824952")
    if required.get("paper_accounting_cost_basis") != "4.00":
        raise ValueError("paper-accounting-pnl-001 cost basis must be 4.00")
    if required.get("paper_accounting_settlement_value") != "10.00":
        raise ValueError("paper-accounting-pnl-001 settlement value must be 10.00")
    if required.get("paper_accounting_pnl") != "6.00":
        raise ValueError("paper-accounting-pnl-001 PnL must be 6.00")


def _source_record_blockers(accounting_record, fill_event, manual_entry):
    blocked = []
    markers = []
    for record in (accounting_record, fill_event, manual_entry):
        if record is None:
            continue
        blocked.extend(_blocked_keys(record))
        markers.extend(_blocked_value_markers(record))
    return sorted(set(blocked)), sorted(set(markers))


def _source_references(accounting_record, source_pnl_path, source_fill_events_path, source_manual_ledger_path):
    return {
        "source_manual_paper_intent_ledger_path": _display_path(source_manual_ledger_path),
        "source_manual_intent_id": _clean_text(accounting_record.get("source_manual_intent_id")),
        "source_ledger_entry_id": _clean_text(accounting_record.get("source_ledger_entry_id")),
        "source_paper_fill_events_path": _display_path(source_fill_events_path),
        "source_paper_fill_event_id": _clean_text(accounting_record.get("source_paper_fill_event_id")),
        "source_settlement_id": _clean_text(accounting_record.get("source_settlement_id")),
        "source_paper_accounting_pnl_preview_path": _display_path(source_pnl_path),
        "source_paper_accounting_record_id": _clean_text(accounting_record.get("paper_accounting_record_id")),
    }


def build_accounting_ledger(
    pnl_payload,
    fill_events_payload,
    manual_ledger_payload,
    source_pnl_path=DEFAULT_PNL_PREVIEW,
    source_fill_events_path=DEFAULT_FILL_EVENTS,
    source_manual_ledger_path=DEFAULT_MANUAL_LEDGER,
):
    fill_events_by_id = _fill_events_by_id(fill_events_payload)
    manual_by_entry_id = _manual_entries_by_id(manual_ledger_payload)
    ledger_entries = []
    cumulative_pnl = Decimal("0")

    accounting_records = sorted(
        _records(pnl_payload, "paper_accounting_records"),
        key=lambda item: (_clean_text(item.get("market_id")), _clean_text(item.get("paper_accounting_record_id"))),
    )
    for index, record in enumerate(accounting_records, start=1):
        fill_event = fill_events_by_id.get(_clean_text(record.get("source_paper_fill_event_id")))
        manual_entry = manual_by_entry_id.get(_clean_text(record.get("source_ledger_entry_id")))
        blocked_keys, blocked_markers = _source_record_blockers(record, fill_event, manual_entry)
        source_references = _source_references(record, source_pnl_path, source_fill_events_path, source_manual_ledger_path)
        source_missing = fill_event is None or (
            _clean_text(record.get("source_ledger_entry_id")) and manual_entry is None
        )
        status = _clean_text(record.get("paper_accounting_status"))

        entry = {
            "paper_accounting_ledger_entry_id": f"paper-accounting-ledger-entry-{index:03d}",
            "market_id": _clean_text(record.get("market_id")),
            "paper_accounting_source": "paper/accounting-only",
            "source_references": source_references,
            "paper_accounting_only": True,
            "paper_only": True,
            "inert_only": True,
            "generated_by_bot": False,
            "live_order_created": False,
            "real_order_created": False,
            "safety_flags": [
                "paper_only",
                "inert_only",
                "paper_accounting_only",
                "operator_manual_source_lineage",
                "no_live_execution",
                "no_real_execution",
                "no_credential_or_endpoint_use",
            ],
        }

        if blocked_keys or blocked_markers or source_missing:
            entry.update(
                {
                    "paper_accounting_entry_status": "paper_accounting_entry_blocked_invalid_source",
                    "paper_position_status": "paper_position_blocked_invalid_source",
                    "blocked_keys": blocked_keys,
                    "blocked_value_markers": blocked_markers,
                    "source_missing": source_missing,
                    "paper_accounting_cumulative_pnl": _format_decimal(cumulative_pnl),
                }
            )
        elif status == OPEN_PREVIEW_STATUS:
            entry.update(
                {
                    "paper_accounting_entry_status": "paper_accounting_entry_pending_settlement",
                    "paper_position_status": "paper_position_open_pending_settlement",
                    "paper_accounting_cumulative_pnl": _format_decimal(cumulative_pnl),
                }
            )
        elif status == SETTLED_PREVIEW_STATUS:
            pnl = _decimal_from_value(record.get("paper_accounting_pnl"))
            cumulative_pnl += pnl
            entry.update(
                {
                    "paper_accounting_entry_status": "paper_accounting_entry_recorded",
                    "paper_position_status": "paper_position_settled",
                    "paper_accounting_cost_basis": _format_decimal(
                        _decimal_from_value(record.get("paper_accounting_cost_basis"))
                    ),
                    "paper_accounting_settlement_value": _format_decimal(
                        _decimal_from_value(record.get("paper_accounting_settlement_value"))
                    ),
                    "paper_accounting_pnl": _format_decimal(pnl),
                    "paper_accounting_cumulative_pnl": _format_decimal(cumulative_pnl),
                }
            )
        else:
            entry.update(
                {
                    "paper_accounting_entry_status": "paper_accounting_entry_blocked_invalid_source",
                    "paper_position_status": "paper_position_blocked_invalid_source",
                    "blocked_keys": [],
                    "blocked_value_markers": [],
                    "source_missing": False,
                    "paper_accounting_cumulative_pnl": _format_decimal(cumulative_pnl),
                }
            )
        ledger_entries.append(entry)

    settled_count = sum(
        1 for entry in ledger_entries if entry["paper_accounting_entry_status"] == "paper_accounting_entry_recorded"
    )
    open_count = sum(
        1
        for entry in ledger_entries
        if entry["paper_accounting_entry_status"] == "paper_accounting_entry_pending_settlement"
    )
    blocked_count = sum(
        1
        for entry in ledger_entries
        if entry["paper_accounting_entry_status"] == "paper_accounting_entry_blocked_invalid_source"
    )
    return {
        "schema_version": "paper_accounting_ledger.v1",
        "markdown_version": "paper_accounting_ledger_report.v1",
        "task_id": TASK_ID,
        "deterministic": True,
        "source_paper_accounting_pnl_preview_path": _display_path(source_pnl_path),
        "source_paper_fill_events_path": _display_path(source_fill_events_path),
        "source_manual_paper_intent_ledger_path": _display_path(source_manual_ledger_path),
        "allowed_paper_accounting_entry_statuses": list(ALLOWED_ACCOUNTING_ENTRY_STATUSES),
        "counts": {
            "paper_accounting_preview_records_read": len(accounting_records),
            "paper_accounting_ledger_entries": len(ledger_entries),
            "paper_accounting_settled_count": settled_count,
            "paper_accounting_open_count": open_count,
            "paper_accounting_blocked_count": blocked_count,
            "real_orders_created": 0,
            "live_orders_created": 0,
            "autonomous_paper_orders_created": 0,
        },
        "market_ids": sorted({entry["market_id"] for entry in ledger_entries if entry["market_id"]}),
        "paper_accounting_ledger_status": "paper_accounting_ledger_history_ready"
        if blocked_count == 0
        else "paper_accounting_ledger_history_blocked_invalid_source",
        "paper_accounting_ledger_entries": ledger_entries,
        "limitations": [
            "Ledger entries are derived only from local paper accounting artifacts.",
            "Operator manual fields are preserved only as source lineage references.",
        ],
    }


def _eligible_entries(ledger_payload):
    return [
        entry
        for entry in _records(ledger_payload, "paper_accounting_ledger_entries")
        if entry.get("paper_accounting_entry_status")
        in ("paper_accounting_entry_recorded", "paper_accounting_entry_pending_settlement")
    ]


def _settled_entries(ledger_payload):
    return [
        entry
        for entry in _records(ledger_payload, "paper_accounting_ledger_entries")
        if entry.get("paper_accounting_entry_status") == "paper_accounting_entry_recorded"
    ]


def calculate_accounting_metrics(ledger_payload):
    eligible = _eligible_entries(ledger_payload)
    settled = _settled_entries(ledger_payload)
    pnl_values = [_decimal_from_value(entry.get("paper_accounting_pnl")) for entry in settled]
    pnl_values = [value for value in pnl_values if value is not None]
    cumulative_pnl = sum(pnl_values, Decimal("0"))
    gross_profit = sum((value for value in pnl_values if value > 0), Decimal("0"))
    gross_loss = sum((value for value in pnl_values if value < 0), Decimal("0"))
    average_pnl = cumulative_pnl / len(pnl_values) if pnl_values else Decimal("0")
    gains = [value for value in pnl_values if value > 0]
    losses = [value for value in pnl_values if value < 0]
    return {
        "paper_accounting_total_records": len(eligible),
        "paper_accounting_settled_count": len(settled),
        "paper_accounting_open_count": sum(
            1
            for entry in eligible
            if entry.get("paper_accounting_entry_status") == "paper_accounting_entry_pending_settlement"
        ),
        "paper_accounting_win_count": sum(1 for value in pnl_values if value > 0),
        "paper_accounting_loss_count": sum(1 for value in pnl_values if value < 0),
        "paper_accounting_flat_count": sum(1 for value in pnl_values if value == 0),
        "paper_accounting_cumulative_pnl": _format_decimal(cumulative_pnl),
        "paper_accounting_average_pnl": _format_decimal(average_pnl),
        "paper_accounting_gross_profit": _format_decimal(gross_profit),
        "paper_accounting_gross_loss": _format_decimal(gross_loss),
        "paper_accounting_max_gain": _format_decimal(max(gains) if gains else Decimal("0")),
        "paper_accounting_max_loss": _format_decimal(min(losses) if losses else Decimal("0")),
    }


def build_portfolio_snapshot(ledger_payload, source_ledger_path=DEFAULT_ACCOUNTING_LEDGER):
    ledger_entries = _records(ledger_payload, "paper_accounting_ledger_entries")
    blocked_count = sum(
        1
        for entry in ledger_entries
        if entry.get("paper_accounting_entry_status") == "paper_accounting_entry_blocked_invalid_source"
    )
    metrics = calculate_accounting_metrics(ledger_payload)
    if not ledger_entries:
        portfolio_status = "paper_portfolio_snapshot_empty"
    elif blocked_count:
        portfolio_status = "paper_portfolio_snapshot_blocked_invalid_ledger"
    else:
        portfolio_status = "paper_portfolio_snapshot_ready"

    positions = []
    for entry in _eligible_entries(ledger_payload):
        position = {
            "market_id": entry["market_id"],
            "paper_position_status": entry["paper_position_status"],
            "source_paper_accounting_ledger_entry_id": entry["paper_accounting_ledger_entry_id"],
            "paper_accounting_cumulative_pnl": entry["paper_accounting_cumulative_pnl"],
        }
        if entry.get("paper_accounting_entry_status") == "paper_accounting_entry_recorded":
            position.update(
                {
                    "paper_accounting_cost_basis": entry["paper_accounting_cost_basis"],
                    "paper_accounting_settlement_value": entry["paper_accounting_settlement_value"],
                    "paper_accounting_pnl": entry["paper_accounting_pnl"],
                }
            )
        positions.append(position)

    return {
        "schema_version": "paper_portfolio_snapshot.v1",
        "markdown_version": "paper_portfolio_snapshot_report.v1",
        "task_id": TASK_ID,
        "deterministic": True,
        "source_paper_accounting_ledger_path": _display_path(source_ledger_path),
        "paper_portfolio_status": portfolio_status,
        "allowed_paper_portfolio_statuses": list(ALLOWED_PORTFOLIO_STATUSES),
        "counts": {
            "paper_accounting_ledger_entries_read": len(ledger_entries),
            "paper_portfolio_snapshot_records": 1 if ledger_entries else 0,
            "paper_accounting_position_count": len(_eligible_entries(ledger_payload)),
            "paper_accounting_blocked_count": blocked_count,
            "real_orders_created": 0,
            "live_orders_created": 0,
            "autonomous_paper_orders_created": 0,
        },
        "market_ids": sorted({entry["market_id"] for entry in _eligible_entries(ledger_payload)}),
        "paper_accounting_settled_count": metrics["paper_accounting_settled_count"],
        "paper_accounting_open_count": metrics["paper_accounting_open_count"],
        "paper_accounting_position_count": metrics["paper_accounting_total_records"],
        "paper_accounting_cumulative_pnl": metrics["paper_accounting_cumulative_pnl"],
        "paper_accounting_gross_profit": metrics["paper_accounting_gross_profit"],
        "paper_accounting_gross_loss": metrics["paper_accounting_gross_loss"],
        "positions": positions,
        "source_artifacts": [
            _display_path(source_ledger_path),
            ledger_payload["source_paper_accounting_pnl_preview_path"],
            ledger_payload["source_paper_fill_events_path"],
            ledger_payload["source_manual_paper_intent_ledger_path"],
        ],
        "safety_flags": [
            "paper_only",
            "inert_only",
            "paper_accounting_only",
            "no_live_execution",
            "no_real_execution",
            "no_credential_or_endpoint_use",
        ],
    }


def build_metrics_report(
    ledger_payload,
    portfolio_snapshot_payload,
    source_ledger_path=DEFAULT_ACCOUNTING_LEDGER,
    source_snapshot_path=DEFAULT_PORTFOLIO_SNAPSHOT,
):
    metrics = calculate_accounting_metrics(ledger_payload)
    return {
        "schema_version": "paper_metrics_report.v1",
        "markdown_version": "paper_metrics_report_markdown.v1",
        "task_id": TASK_ID,
        "deterministic": True,
        "source_paper_accounting_ledger_path": _display_path(source_ledger_path),
        "source_paper_portfolio_snapshot_path": _display_path(source_snapshot_path),
        "paper_metrics_report_status": "paper_metrics_report_ready",
        "counts": {
            "paper_metrics_report_records": 1,
            "real_orders_created": 0,
            "live_orders_created": 0,
            "autonomous_paper_orders_created": 0,
        },
        "market_ids": portfolio_snapshot_payload.get("market_ids", []),
        "paper_accounting_metrics": metrics,
        "source_artifacts": [
            _display_path(source_ledger_path),
            _display_path(source_snapshot_path),
        ],
        "safety_flags": [
            "paper_only",
            "inert_only",
            "paper_accounting_only",
            "no_live_execution",
            "no_real_execution",
            "no_credential_or_endpoint_use",
        ],
    }


def render_accounting_ledger_markdown(ledger_payload):
    lines = [
        "# PAPER-014 Paper Accounting Ledger History",
        "",
        f"- task_id: {ledger_payload['task_id']}",
        f"- paper_accounting_ledger_entries: {ledger_payload['counts']['paper_accounting_ledger_entries']}",
        f"- paper_accounting_settled_count: {ledger_payload['counts']['paper_accounting_settled_count']}",
        f"- paper_accounting_open_count: {ledger_payload['counts']['paper_accounting_open_count']}",
        f"- paper_accounting_blocked_count: {ledger_payload['counts']['paper_accounting_blocked_count']}",
        "",
        "## Ledger Entries",
        "",
    ]
    if not ledger_payload["paper_accounting_ledger_entries"]:
        lines.append("- none")
    else:
        for entry in ledger_payload["paper_accounting_ledger_entries"]:
            if entry["paper_accounting_entry_status"] == "paper_accounting_entry_recorded":
                lines.append(
                    f"- {entry['paper_accounting_ledger_entry_id']}: market_id={entry['market_id']} "
                    f"status={entry['paper_accounting_entry_status']} "
                    f"paper_accounting_pnl={entry['paper_accounting_pnl']} "
                    f"paper_accounting_cumulative_pnl={entry['paper_accounting_cumulative_pnl']}"
                )
            else:
                lines.append(
                    f"- {entry['paper_accounting_ledger_entry_id']}: market_id={entry['market_id']} "
                    f"status={entry['paper_accounting_entry_status']}"
                )
    lines.extend(
        [
            "",
            "## Safety",
            "",
            "- Ledger entries are paper/accounting-only and derived from local artifacts.",
            "- No executable artifact is created.",
            "",
        ]
    )
    return "\n".join(lines)


def render_portfolio_snapshot_markdown(snapshot_payload):
    lines = [
        "# PAPER-015 Paper Portfolio Snapshot",
        "",
        f"- task_id: {snapshot_payload['task_id']}",
        f"- paper_portfolio_status: {snapshot_payload['paper_portfolio_status']}",
        f"- paper_accounting_position_count: {snapshot_payload['paper_accounting_position_count']}",
        f"- paper_accounting_settled_count: {snapshot_payload['paper_accounting_settled_count']}",
        f"- paper_accounting_open_count: {snapshot_payload['paper_accounting_open_count']}",
        f"- paper_accounting_cumulative_pnl: {snapshot_payload['paper_accounting_cumulative_pnl']}",
        f"- paper_accounting_gross_profit: {snapshot_payload['paper_accounting_gross_profit']}",
        f"- paper_accounting_gross_loss: {snapshot_payload['paper_accounting_gross_loss']}",
        "",
        "## Positions",
        "",
    ]
    if not snapshot_payload["positions"]:
        lines.append("- none")
    else:
        for position in snapshot_payload["positions"]:
            lines.append(
                f"- market_id={position['market_id']} status={position['paper_position_status']} "
                f"paper_accounting_cumulative_pnl={position['paper_accounting_cumulative_pnl']}"
            )
    lines.extend(
        [
            "",
            "## Safety",
            "",
            "- Portfolio snapshot is paper/accounting-only and local.",
            "- No executable artifact is created.",
            "",
        ]
    )
    return "\n".join(lines)


def render_metrics_report_markdown(metrics_payload):
    metrics = metrics_payload["paper_accounting_metrics"]
    lines = [
        "# PAPER-016 Paper Metrics Report",
        "",
        f"- task_id: {metrics_payload['task_id']}",
        f"- paper_accounting_total_records: {metrics['paper_accounting_total_records']}",
        f"- paper_accounting_settled_count: {metrics['paper_accounting_settled_count']}",
        f"- paper_accounting_open_count: {metrics['paper_accounting_open_count']}",
        f"- paper_accounting_win_count: {metrics['paper_accounting_win_count']}",
        f"- paper_accounting_loss_count: {metrics['paper_accounting_loss_count']}",
        f"- paper_accounting_flat_count: {metrics['paper_accounting_flat_count']}",
        f"- paper_accounting_cumulative_pnl: {metrics['paper_accounting_cumulative_pnl']}",
        f"- paper_accounting_average_pnl: {metrics['paper_accounting_average_pnl']}",
        f"- paper_accounting_gross_profit: {metrics['paper_accounting_gross_profit']}",
        f"- paper_accounting_gross_loss: {metrics['paper_accounting_gross_loss']}",
        f"- paper_accounting_max_gain: {metrics['paper_accounting_max_gain']}",
        f"- paper_accounting_max_loss: {metrics['paper_accounting_max_loss']}",
        "",
        "## Safety",
        "",
        "- Metrics are paper/accounting-only and local.",
        "- No executable artifact is created.",
        "",
    ]
    return "\n".join(lines)


def _result_payload(
    counts,
    accounting_metrics,
    status="completed_ready_for_review",
    blockers=None,
    tests=None,
):
    return {
        "task_id": TASK_ID,
        "status": status,
        "summary": (
            "Implemented deterministic offline PAPER-014 through PAPER-016 paper accounting ledger, portfolio snapshot, and metrics report artifacts."
        )
        if status == "completed_ready_for_review"
        else "Blocked before completing deterministic offline paper portfolio metrics artifacts.",
        "market_ids": ["824952"] if status == "completed_ready_for_review" else [],
        "stages_completed": {
            "paper_014_accounting_ledger_history": status == "completed_ready_for_review",
            "paper_015_portfolio_snapshot": status == "completed_ready_for_review",
            "paper_016_metrics_report": status == "completed_ready_for_review",
        },
        "counts": counts,
        "accounting_metrics": accounting_metrics,
        "files_created": FILES_CREATED if status == "completed_ready_for_review" else [],
        "files_modified": [],
        "tests": tests or [],
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
            "strategy_ranking": False,
            "runtime_wiring": False,
            "dispatcher_run_codex_changes": False,
            "prompt_automation": False,
            "codex_copy_roots": False,
            "completed_dossiers": False,
            "broad_refactor": False,
        },
        "scope_expansion": {
            "paper_accounting_ledger_introduced": status == "completed_ready_for_review",
            "paper_portfolio_snapshot_introduced": status == "completed_ready_for_review",
            "paper_metrics_report_introduced": status == "completed_ready_for_review",
            "accounting_metrics_only": True,
            "strategy_metrics": False,
            "bot_generated_side_size_price": False,
        },
        "blockers": blockers or [],
    }


def write_paper_portfolio_metrics_artifacts(
    pnl_preview_path=DEFAULT_PNL_PREVIEW,
    fill_events_path=DEFAULT_FILL_EVENTS,
    manual_ledger_path=DEFAULT_MANUAL_LEDGER,
):
    pnl_preview_path = _resolve_path(pnl_preview_path)
    fill_events_path = _resolve_path(fill_events_path)
    manual_ledger_path = _resolve_path(manual_ledger_path)
    if not pnl_preview_path.exists():
        raise FileNotFoundError(f"missing paper accounting PnL preview: {_display_path(pnl_preview_path)}")
    if not fill_events_path.exists():
        raise FileNotFoundError(f"missing paper fill events artifact: {_display_path(fill_events_path)}")
    if not manual_ledger_path.exists():
        raise FileNotFoundError(f"missing manual paper intent ledger: {_display_path(manual_ledger_path)}")

    pnl_payload = _load_json(pnl_preview_path)
    fill_events_payload = _load_json(fill_events_path)
    manual_ledger_payload = _load_json(manual_ledger_path)
    _validate_source_artifacts(pnl_payload, fill_events_payload, manual_ledger_payload)

    accounting_ledger = build_accounting_ledger(
        pnl_payload,
        fill_events_payload,
        manual_ledger_payload,
        pnl_preview_path,
        fill_events_path,
        manual_ledger_path,
    )
    portfolio_snapshot = build_portfolio_snapshot(accounting_ledger, DEFAULT_ACCOUNTING_LEDGER)
    metrics_report = build_metrics_report(accounting_ledger, portfolio_snapshot)
    accounting_metrics = metrics_report["paper_accounting_metrics"]
    completed = (
        accounting_ledger["counts"]["paper_accounting_blocked_count"] == 0
        and portfolio_snapshot["paper_portfolio_status"] == "paper_portfolio_snapshot_ready"
    )
    status = "completed_ready_for_review" if completed else "blocked"

    _write_json(DEFAULT_ACCOUNTING_LEDGER, accounting_ledger)
    _write_json(DEFAULT_ACCOUNTING_LEDGER_EXPECTED, accounting_ledger)
    _write_text(DEFAULT_ACCOUNTING_LEDGER_MD, render_accounting_ledger_markdown(accounting_ledger))

    _write_json(DEFAULT_PORTFOLIO_SNAPSHOT, portfolio_snapshot)
    _write_json(DEFAULT_PORTFOLIO_SNAPSHOT_EXPECTED, portfolio_snapshot)
    _write_text(DEFAULT_PORTFOLIO_SNAPSHOT_MD, render_portfolio_snapshot_markdown(portfolio_snapshot))

    _write_json(DEFAULT_METRICS_REPORT, metrics_report)
    _write_json(DEFAULT_METRICS_REPORT_EXPECTED, metrics_report)
    _write_text(DEFAULT_METRICS_REPORT_MD, render_metrics_report_markdown(metrics_report))

    counts = {
        "paper_accounting_ledger_entries": accounting_ledger["counts"]["paper_accounting_ledger_entries"],
        "paper_portfolio_snapshot_records": portfolio_snapshot["counts"]["paper_portfolio_snapshot_records"],
        "paper_metrics_report_records": metrics_report["counts"]["paper_metrics_report_records"],
        "real_orders_created": 0,
        "live_orders_created": 0,
        "autonomous_paper_orders_created": 0,
    }
    blockers = [] if completed else ["paper accounting ledger contains blocked invalid source records"]
    result_payload = _result_payload(counts, accounting_metrics, status=status, blockers=blockers)
    _write_json(DEFAULT_RESULT, result_payload)
    return {
        "task_id": TASK_ID,
        "status": status,
        "market_ids": result_payload["market_ids"],
        "counts": counts,
        "accounting_metrics": accounting_metrics,
        "result_path": _display_path(DEFAULT_RESULT),
        "blockers": blockers,
    }


def main(argv):
    args = _parse_args(argv)
    try:
        summary = write_paper_portfolio_metrics_artifacts(args.pnl_preview, args.fill_events, args.manual_ledger)
    except Exception as exc:
        blocked_counts = {
            "paper_accounting_ledger_entries": 0,
            "paper_portfolio_snapshot_records": 0,
            "paper_metrics_report_records": 0,
            "real_orders_created": 0,
            "live_orders_created": 0,
            "autonomous_paper_orders_created": 0,
        }
        _write_json(DEFAULT_RESULT, _result_payload(blocked_counts, ZERO_METRICS, status="blocked", blockers=[str(exc)]))
        print(json.dumps({"task_id": TASK_ID, "status": "blocked", "blockers": [str(exc)]}, indent=2, ensure_ascii=True))
        return 2
    print(json.dumps(summary, indent=2, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
