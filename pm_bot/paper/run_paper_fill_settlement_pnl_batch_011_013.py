import argparse
import json
import sys
from decimal import Decimal, InvalidOperation
from pathlib import Path


TASK_ID = "PMBOT-PAPER-BATCH-011-013-FILL-SETTLEMENT-PNL-MVP"
ROOT = Path(__file__).resolve().parents[2]
PAPER_DIR = ROOT / "pm_bot" / "paper"
DOCS_DIR = ROOT / "docs"

DEFAULT_MANUAL_LEDGER = PAPER_DIR / "manual_paper_intent_ledger.v1.json"
DEFAULT_WORKBENCH_PREVIEW = PAPER_DIR / "paper_workbench_preview.v1.json"

DEFAULT_FILL_CONTRACT = PAPER_DIR / "paper_fill_source_contract.v1.json"
DEFAULT_FILL_FIXTURE = PAPER_DIR / "paper_fill_source_fixture.v1.json"
DEFAULT_FILL_REPORT = PAPER_DIR / "paper_fill_source_report.v1.md"
DEFAULT_FILL_ACCEPTED = PAPER_DIR / "paper_fill_sources_accepted.v1.json"
DEFAULT_FILL_REJECTED = PAPER_DIR / "paper_fill_sources_rejected.v1.json"
DEFAULT_FILL_EVENTS = PAPER_DIR / "paper_fill_events.v1.json"
DEFAULT_FILL_EVENTS_EXPECTED = PAPER_DIR / "expected_paper_fill_events.v1.json"
DEFAULT_FILL_EVENTS_REPORT = PAPER_DIR / "paper_fill_events_report.v1.md"

DEFAULT_SETTLEMENT_FIXTURE = PAPER_DIR / "paper_settlement_source_fixture.v1.json"
DEFAULT_SETTLEMENT_ACCEPTED = PAPER_DIR / "paper_settlement_sources_accepted.v1.json"
DEFAULT_SETTLEMENT_REJECTED = PAPER_DIR / "paper_settlement_sources_rejected.v1.json"
DEFAULT_PNL_PREVIEW = PAPER_DIR / "paper_accounting_pnl_preview.v1.json"
DEFAULT_PNL_PREVIEW_EXPECTED = PAPER_DIR / "expected_paper_accounting_pnl_preview.v1.json"
DEFAULT_PNL_PREVIEW_MD = PAPER_DIR / "paper_accounting_pnl_preview.v1.md"
DEFAULT_RESULT = DOCS_DIR / "PMBOT_PAPER_BATCH_011_013_RESULT.json"

ALLOWED_FILL_SOURCE_TYPES = (
    "operator_manual_fill_fixture",
    "no_fill_source_available",
    "blocked_by_policy",
)
ALLOWED_PAPER_FILL_EVENT_STATUSES = (
    "paper_fill_recorded_from_operator_manual_fixture",
    "paper_fill_pending_manual_source",
    "paper_fill_rejected_by_policy",
    "paper_fill_blocked_invalid_fixture",
)
ALLOWED_SETTLEMENT_SOURCE_TYPES = (
    "operator_manual_settlement_fixture",
    "settlement_pending_manual_source",
    "blocked_by_policy",
)
ALLOWED_PAPER_ACCOUNTING_STATUSES = (
    "paper_position_open_pending_settlement",
    "paper_position_settled_from_operator_manual_fixture",
    "paper_position_blocked_invalid_settlement",
    "paper_position_watch_only",
)

FILL_SOURCE_FIELDS = {
    "fill_source_id",
    "market_id",
    "source_manual_intent_id",
    "source_ledger_entry_id",
    "fill_source_type",
    "operator_manual_fill_status",
    "operator_manual_fill_price",
    "operator_manual_fill_size",
    "operator_manual_fill_notes",
    "paper_only",
    "inert_only",
    "generated_by_bot",
    "live_order_created",
    "real_order_created",
}
FILL_REQUIRED_FIELDS = (
    "fill_source_id",
    "market_id",
    "source_manual_intent_id",
    "source_ledger_entry_id",
    "fill_source_type",
    "operator_manual_fill_status",
    "operator_manual_fill_price",
    "operator_manual_fill_size",
    "operator_manual_fill_notes",
    "paper_only",
    "inert_only",
    "generated_by_bot",
    "live_order_created",
    "real_order_created",
)
SETTLEMENT_SOURCE_FIELDS = {
    "settlement_source_id",
    "market_id",
    "source_manual_intent_id",
    "source_ledger_entry_id",
    "source_paper_fill_event_id",
    "settlement_source_type",
    "operator_manual_settlement_status",
    "operator_manual_settlement_outcome",
    "operator_manual_settlement_price",
    "operator_manual_settlement_notes",
    "paper_only",
    "inert_only",
    "generated_by_bot",
    "live_order_created",
    "real_order_created",
}
SETTLEMENT_REQUIRED_FIELDS = (
    "settlement_source_id",
    "market_id",
    "source_manual_intent_id",
    "source_ledger_entry_id",
    "source_paper_fill_event_id",
    "settlement_source_type",
    "operator_manual_settlement_status",
    "operator_manual_settlement_outcome",
    "operator_manual_settlement_price",
    "operator_manual_settlement_notes",
    "paper_only",
    "inert_only",
    "generated_by_bot",
    "live_order_created",
    "real_order_created",
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
    "truth_inference",
    "inferred_truth",
    "api_resolution",
    "live_resolution",
    "market_decision",
    "decision_quality",
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
    "truth inference",
    "infer truth",
    "api resolution",
    "live resolution",
)
FILES_CREATED = [
    "pm_bot/paper/run_paper_fill_settlement_pnl_batch_011_013.py",
    "pm_bot/paper/paper_fill_source_contract.v1.json",
    "pm_bot/paper/paper_fill_source_fixture.v1.json",
    "pm_bot/paper/paper_fill_source_report.v1.md",
    "pm_bot/paper/paper_fill_sources_accepted.v1.json",
    "pm_bot/paper/paper_fill_sources_rejected.v1.json",
    "pm_bot/paper/paper_fill_events.v1.json",
    "pm_bot/paper/paper_fill_events_report.v1.md",
    "pm_bot/paper/paper_settlement_source_fixture.v1.json",
    "pm_bot/paper/paper_settlement_sources_accepted.v1.json",
    "pm_bot/paper/paper_settlement_sources_rejected.v1.json",
    "pm_bot/paper/paper_accounting_pnl_preview.v1.json",
    "pm_bot/paper/paper_accounting_pnl_preview.v1.md",
    "pm_bot/paper/expected_paper_fill_events.v1.json",
    "pm_bot/paper/expected_paper_accounting_pnl_preview.v1.json",
    "pm_bot/paper/tests/test_paper_fill_settlement_pnl_batch_011_013.py",
    "docs/PMBOT_PAPER_BATCH_011_013_RESULT.json",
]


def _parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Run deterministic offline PAPER-011 through PAPER-013 fill, settlement, and accounting artifacts."
    )
    parser.add_argument("--manual-ledger", default=str(DEFAULT_MANUAL_LEDGER.relative_to(ROOT)))
    parser.add_argument("--workbench-preview", default=str(DEFAULT_WORKBENCH_PREVIEW.relative_to(ROOT)))
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


def _blocked_keys(record, allowed_fields):
    blocked = []
    for key in _walk_keys(record):
        if key in allowed_fields:
            continue
        if _field_tokens(key) & PROHIBITED_FIELD_TOKENS:
            blocked.append(key)
    return sorted(set(blocked))


def _unexpected_keys(record, allowed_fields):
    return sorted({key for key in _walk_keys(record) if key not in allowed_fields})


def _blocked_value_markers(record):
    markers = []
    for value in _walk_string_values(record):
        lower = value.lower()
        for marker in BLOCKED_VALUE_MARKERS:
            if marker in lower:
                markers.append(marker)
    return sorted(set(markers))


def _count_by_reason(records):
    counts = {}
    for record in records:
        for reason in record.get("rejection_reasons", []):
            counts[reason] = counts.get(reason, 0) + 1
    return dict(sorted(counts.items()))


def _render_list(items, indent="  "):
    if not items:
        return [f"{indent}- none"]
    return [f"{indent}- {item}" for item in items]


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


def _format_accounting_decimal(value):
    return str(value.quantize(Decimal("0.01")))


def _is_valid_price(value):
    number = _decimal_from_value(value)
    return number is not None and Decimal("0") <= number <= Decimal("1")


def _is_positive_number(value):
    number = _decimal_from_value(value)
    return number is not None and number > Decimal("0")


def _ledger_by_market_id(ledger_payload):
    return {
        _clean_text(record.get("market_id")): record
        for record in _records(ledger_payload, "ledger_entries")
        if _clean_text(record.get("market_id"))
    }


def _ledger_by_source_intent_id(ledger_payload):
    return {
        _clean_text(record.get("source_intent_id")): record
        for record in _records(ledger_payload, "ledger_entries")
        if _clean_text(record.get("source_intent_id"))
    }


def _preview_by_market_id(preview_payload):
    return {
        _clean_text(record.get("market_id")): record
        for record in _records(preview_payload, "preview_records")
        if _clean_text(record.get("market_id"))
    }


def _validate_source_artifacts(ledger_payload, preview_payload):
    ledger_entries = _records(ledger_payload, "ledger_entries")
    preview_records = _records(preview_payload, "preview_records")
    if not ledger_entries:
        raise ValueError("manual paper intent ledger contains no ledger_entries")
    if not preview_records:
        raise ValueError("paper workbench preview contains no preview_records")
    if ledger_payload.get("counts", {}).get("real_orders_created") != 0:
        raise ValueError("manual paper intent ledger is inconsistent: real_orders_created must be 0")
    if ledger_payload.get("counts", {}).get("live_orders_created") != 0:
        raise ValueError("manual paper intent ledger is inconsistent: live_orders_created must be 0")
    if ledger_payload.get("counts", {}).get("autonomous_paper_orders_created") != 0:
        raise ValueError("manual paper intent ledger is inconsistent: autonomous_paper_orders_created must be 0")

    ledger_markets = set(_ledger_by_market_id(ledger_payload))
    preview_markets = set(_preview_by_market_id(preview_payload))
    if "824952" not in ledger_markets:
        raise ValueError("manual paper intent ledger does not contain required market_id 824952")
    if "824952" not in preview_markets:
        raise ValueError("paper workbench preview does not contain required market_id 824952")
    if not ledger_markets.issubset(preview_markets):
        raise ValueError("paper workbench preview is missing a market from the manual paper intent ledger")

    for entry in ledger_entries:
        if entry.get("paper_only") is not True:
            raise ValueError("manual paper intent ledger entry must have paper_only true")
        if entry.get("inert_only") is not True:
            raise ValueError("manual paper intent ledger entry must have inert_only true")
        if entry.get("generated_by_bot") is not False:
            raise ValueError("manual paper intent ledger entry must have generated_by_bot false")
        if entry.get("live_order_created") is not False:
            raise ValueError("manual paper intent ledger entry must have live_order_created false")
        if entry.get("real_order_created") is not False:
            raise ValueError("manual paper intent ledger entry must have real_order_created false")


def build_fill_source_contract(
    ledger_payload,
    preview_payload,
    source_ledger_path=DEFAULT_MANUAL_LEDGER,
    source_preview_path=DEFAULT_WORKBENCH_PREVIEW,
):
    ledger_entries = _records(ledger_payload, "ledger_entries")
    preview_records = _records(preview_payload, "preview_records")
    market_ids = sorted(_ledger_by_market_id(ledger_payload))
    return {
        "schema_version": "paper_fill_source_contract.v1",
        "markdown_version": "paper_fill_source_contract_report.v1",
        "task_id": TASK_ID,
        "deterministic": True,
        "source_manual_paper_intent_ledger_path": _display_path(source_ledger_path),
        "source_paper_workbench_preview_path": _display_path(source_preview_path),
        "allowed_fill_source_types": list(ALLOWED_FILL_SOURCE_TYPES),
        "allowed_paper_fill_event_statuses": list(ALLOWED_PAPER_FILL_EVENT_STATUSES),
        "required_fields": list(FILL_REQUIRED_FIELDS),
        "field_contract": {
            "market_id": "required string matching a manual paper intent ledger market",
            "source_manual_intent_id": "required stable link to the source manual paper intent",
            "source_ledger_entry_id": "required stable link to the source manual paper intent ledger entry",
            "fill_source_type": "required local source type from the allowed list",
            "operator_manual_fill_status": "required operator-provided local paper fill status",
            "operator_manual_fill_price": "required operator-provided local paper fill price for operator_manual_fill_fixture",
            "operator_manual_fill_size": "required operator-provided local paper fill size for operator_manual_fill_fixture",
            "operator_manual_fill_notes": "required operator-provided local paper fill notes",
            "paper_only": "required boolean true",
            "inert_only": "required boolean true",
            "generated_by_bot": "required boolean false",
            "live_order_created": "required boolean false",
            "real_order_created": "required boolean false",
        },
        "blank_record": {
            "fill_source_id": "",
            "market_id": "",
            "source_manual_intent_id": "",
            "source_ledger_entry_id": "",
            "fill_source_type": "operator_manual_fill_fixture",
            "operator_manual_fill_status": "",
            "operator_manual_fill_price": None,
            "operator_manual_fill_size": None,
            "operator_manual_fill_notes": "",
            "paper_only": True,
            "inert_only": True,
            "generated_by_bot": False,
            "live_order_created": False,
            "real_order_created": False,
        },
        "validation_rules": [
            "accept_only_market_ids_present_in_manual_paper_intent_ledger",
            "accept_only_operator_manual_fill_fixture_rows_with_valid_local_price_and_size",
            "paper_only_must_be_true",
            "inert_only_must_be_true",
            "generated_by_bot_must_be_false",
            "live_order_created_must_be_false",
            "real_order_created_must_be_false",
            "reject_autonomous_trading_scoring_or_endpoint_fields",
            "external_data_required_false",
            "live_data_required_false",
            "orderbook_data_required_false",
            "api_data_required_false",
        ],
        "blocked_inputs": [
            "orderbook",
            "api_price",
            "live_price",
            "wallet",
            "private_key",
            "api_key",
            "auth",
            "trading_endpoint",
            "generated_side",
            "generated_price",
            "generated_size",
        ],
        "counts": {
            "manual_paper_intent_ledger_entries": len(ledger_entries),
            "paper_workbench_preview_records": len(preview_records),
            "real_orders_created": 0,
            "live_orders_created": 0,
            "autonomous_paper_orders_created": 0,
        },
        "market_ids": market_ids,
        "paper_only": True,
        "inert_only": True,
        "generated_by_bot": False,
        "live_order_created": False,
        "real_order_created": False,
    }


def build_fill_source_fixture(
    ledger_payload,
    source_contract_path=DEFAULT_FILL_CONTRACT,
    source_ledger_path=DEFAULT_MANUAL_LEDGER,
):
    entry = _ledger_by_market_id(ledger_payload)["824952"]
    return {
        "schema_version": "paper_fill_source_fixture.v1",
        "task_id": TASK_ID,
        "deterministic": True,
        "source_fill_source_contract_path": _display_path(source_contract_path),
        "source_manual_paper_intent_ledger_path": _display_path(source_ledger_path),
        "records": [
            {
                "fill_source_id": "paper-fill-source-operator-manual-001",
                "market_id": entry["market_id"],
                "source_manual_intent_id": entry["source_intent_id"],
                "source_ledger_entry_id": entry["ledger_entry_id"],
                "fill_source_type": "operator_manual_fill_fixture",
                "operator_manual_fill_status": "operator_manual_fill_recorded",
                "operator_manual_fill_price": 0.4,
                "operator_manual_fill_size": 10,
                "operator_manual_fill_notes": "Operator-entered local paper fill fixture.",
                "paper_only": True,
                "inert_only": True,
                "generated_by_bot": False,
                "live_order_created": False,
                "real_order_created": False,
            },
            {
                "fill_source_id": "paper-fill-source-rejected-unknown-market",
                "market_id": "000000",
                "source_manual_intent_id": "manual-intent-unknown",
                "source_ledger_entry_id": "manual-paper-intent-ledger-unknown",
                "fill_source_type": "operator_manual_fill_fixture",
                "operator_manual_fill_status": "operator_manual_fill_recorded",
                "operator_manual_fill_price": 0.5,
                "operator_manual_fill_size": 2,
                "operator_manual_fill_notes": "Invalid fixture row: market is absent from the manual paper intent ledger.",
                "paper_only": True,
                "inert_only": True,
                "generated_by_bot": False,
                "live_order_created": False,
                "real_order_created": False,
            },
            {
                "fill_source_id": "paper-fill-source-rejected-live-bot",
                "market_id": entry["market_id"],
                "source_manual_intent_id": entry["source_intent_id"],
                "source_ledger_entry_id": entry["ledger_entry_id"],
                "fill_source_type": "operator_manual_fill_fixture",
                "operator_manual_fill_status": "operator_manual_fill_recorded",
                "operator_manual_fill_price": 0.39,
                "operator_manual_fill_size": 5,
                "operator_manual_fill_notes": "Invalid fixture row implies live order, wallet, API key, trading endpoint, and bot recommendation.",
                "paper_only": True,
                "inert_only": True,
                "generated_by_bot": True,
                "live_order_created": True,
                "real_order_created": False,
                "wallet": "blocked_fixture_value",
                "api_key": "blocked_fixture_value",
                "trading_endpoint": "blocked_fixture_value",
                "bot_decision": "blocked_fixture_value",
                "recommendation": "blocked_fixture_value",
            },
        ],
    }


def _fill_rejection_record(record, reasons, blocked_keys, unexpected_keys, blocked_markers):
    return {
        "fill_source_id": _clean_text(record.get("fill_source_id")),
        "market_id": _clean_text(record.get("market_id")),
        "source_manual_intent_id": _clean_text(record.get("source_manual_intent_id")),
        "source_ledger_entry_id": _clean_text(record.get("source_ledger_entry_id")),
        "fill_source_type": _clean_text(record.get("fill_source_type")),
        "fill_source_status": "rejected",
        "rejection_reasons": reasons,
        "blocked_keys": blocked_keys,
        "unexpected_keys": unexpected_keys,
        "blocked_language_markers": blocked_markers,
    }


def _accepted_fill_record(record):
    return {
        "fill_source_id": _clean_text(record.get("fill_source_id")),
        "market_id": _clean_text(record.get("market_id")),
        "source_manual_intent_id": _clean_text(record.get("source_manual_intent_id")),
        "source_ledger_entry_id": _clean_text(record.get("source_ledger_entry_id")),
        "fill_source_type": _clean_text(record.get("fill_source_type")),
        "fill_source_status": "accepted_for_paper_fill_event_processing",
        "operator_manual_fill_status": _clean_text(record.get("operator_manual_fill_status")),
        "operator_manual_fill_price": record.get("operator_manual_fill_price"),
        "operator_manual_fill_size": record.get("operator_manual_fill_size"),
        "operator_manual_fill_notes": _clean_text(record.get("operator_manual_fill_notes")),
        "paper_only": True,
        "inert_only": True,
        "generated_by_bot": False,
        "live_order_created": False,
        "real_order_created": False,
    }


def build_fill_source_outputs(ledger_payload, fill_fixture_payload, fill_fixture_path=DEFAULT_FILL_FIXTURE):
    ledger_by_market = _ledger_by_market_id(ledger_payload)
    ledger_by_intent = _ledger_by_source_intent_id(ledger_payload)
    accepted = []
    rejected = []

    for record in _records(fill_fixture_payload, "records"):
        market_id = _clean_text(record.get("market_id"))
        source_manual_intent_id = _clean_text(record.get("source_manual_intent_id"))
        source_ledger_entry_id = _clean_text(record.get("source_ledger_entry_id"))
        fill_source_type = _clean_text(record.get("fill_source_type"))
        reasons = []
        blocked_keys = _blocked_keys(record, FILL_SOURCE_FIELDS)
        unexpected_keys = _unexpected_keys(record, FILL_SOURCE_FIELDS)
        blocked_markers = _blocked_value_markers(record)

        for field in FILL_REQUIRED_FIELDS:
            if field not in record:
                reasons.append(f"{field}_required")
        ledger_entry = ledger_by_market.get(market_id)
        if market_id not in ledger_by_market:
            reasons.append("unknown_market_id")
        elif source_manual_intent_id != _clean_text(ledger_entry.get("source_intent_id")):
            reasons.append("source_manual_intent_id_mismatch")
        elif source_ledger_entry_id != _clean_text(ledger_entry.get("ledger_entry_id")):
            reasons.append("source_ledger_entry_id_mismatch")
        if source_manual_intent_id and source_manual_intent_id not in ledger_by_intent:
            if "unknown_source_manual_intent_id" not in reasons:
                reasons.append("unknown_source_manual_intent_id")
        if fill_source_type not in ALLOWED_FILL_SOURCE_TYPES:
            reasons.append("unknown_fill_source_type")
        if record.get("paper_only") is not True:
            reasons.append("paper_only_true_required")
        if record.get("inert_only") is not True:
            reasons.append("inert_only_true_required")
        if record.get("generated_by_bot") is not False:
            reasons.append("generated_by_bot_false_required")
        if record.get("live_order_created") is not False:
            reasons.append("live_order_created_false_required")
        if record.get("real_order_created") is not False:
            reasons.append("real_order_created_false_required")
        if fill_source_type == "operator_manual_fill_fixture":
            if not _clean_text(record.get("operator_manual_fill_status")):
                reasons.append("operator_manual_fill_status_required")
            if not _is_valid_price(record.get("operator_manual_fill_price")):
                reasons.append("operator_manual_fill_price_invalid")
            if not _is_positive_number(record.get("operator_manual_fill_size")):
                reasons.append("operator_manual_fill_size_invalid")
        elif fill_source_type == "blocked_by_policy":
            reasons.append("blocked_by_policy")
        if blocked_keys:
            reasons.append("prohibited_or_execution_field_present")
        if unexpected_keys:
            reasons.append("unexpected_field_present")
        if blocked_markers:
            reasons.append("blocked_language_present")

        reasons = list(dict.fromkeys(reasons))
        if reasons:
            rejected.append(_fill_rejection_record(record, reasons, blocked_keys, unexpected_keys, blocked_markers))
            continue
        accepted.append(_accepted_fill_record(record))

    accepted.sort(key=lambda item: (item["market_id"], item["fill_source_id"]))
    rejected.sort(key=lambda item: item["fill_source_id"])

    common = {
        "task_id": TASK_ID,
        "deterministic": True,
        "source_manual_paper_intent_ledger_path": _display_path(DEFAULT_MANUAL_LEDGER),
        "input_path": _display_path(fill_fixture_path),
    }
    accepted_payload = {
        "schema_version": "paper_fill_sources_accepted.v1",
        **common,
        "counts": {
            "records_read": len(_records(fill_fixture_payload, "records")),
            "records_accepted": len(accepted),
        },
        "records": accepted,
    }
    rejected_payload = {
        "schema_version": "paper_fill_sources_rejected.v1",
        **common,
        "counts": {
            "records_read": len(_records(fill_fixture_payload, "records")),
            "records_rejected": len(rejected),
            "rejection_reason_counts": _count_by_reason(rejected),
        },
        "records": rejected,
    }
    fill_events_payload = build_paper_fill_events(ledger_payload, accepted_payload, DEFAULT_FILL_ACCEPTED)
    return accepted_payload, rejected_payload, fill_events_payload


def build_paper_fill_events(ledger_payload, accepted_fill_payload, source_accepted_path=DEFAULT_FILL_ACCEPTED):
    ledger_by_market = _ledger_by_market_id(ledger_payload)
    events = []
    for index, record in enumerate(_records(accepted_fill_payload, "records"), start=1):
        ledger_entry = ledger_by_market[record["market_id"]]
        events.append(
            {
                "paper_fill_event_id": f"paper-fill-event-{index:03d}",
                "source_fill_source_id": record["fill_source_id"],
                "source_manual_intent_id": record["source_manual_intent_id"],
                "source_ledger_entry_id": record["source_ledger_entry_id"],
                "market_id": record["market_id"],
                "paper_fill_event_status": "paper_fill_recorded_from_operator_manual_fixture",
                "fill_source_type": record["fill_source_type"],
                "operator_manual_outcome": ledger_entry["operator_manual_outcome"],
                "operator_manual_side": ledger_entry["operator_manual_side"],
                "operator_manual_limit_price": ledger_entry["operator_manual_limit_price"],
                "operator_manual_size": ledger_entry["operator_manual_size"],
                "operator_manual_fill_status": record["operator_manual_fill_status"],
                "operator_manual_fill_price": record["operator_manual_fill_price"],
                "operator_manual_fill_size": record["operator_manual_fill_size"],
                "operator_manual_fill_notes": record["operator_manual_fill_notes"],
                "paper_only": True,
                "inert_only": True,
                "generated_by_bot": False,
                "live_order_created": False,
                "real_order_created": False,
                "safety_flags": [
                    "paper_only",
                    "inert_only",
                    "operator_manual_fill_fixture",
                    "no_live_execution",
                    "no_real_execution",
                    "no_credential_or_endpoint_use",
                ],
            }
        )
    events.sort(key=lambda item: (item["market_id"], item["paper_fill_event_id"]))
    return {
        "schema_version": "paper_fill_events.v1",
        "markdown_version": "paper_fill_events_report.v1",
        "task_id": TASK_ID,
        "deterministic": True,
        "source_fill_sources_accepted_path": _display_path(source_accepted_path),
        "allowed_paper_fill_event_statuses": list(ALLOWED_PAPER_FILL_EVENT_STATUSES),
        "counts": {
            "fill_source_records_accepted": len(_records(accepted_fill_payload, "records")),
            "paper_fill_events_written": len(events),
            "real_orders_created": 0,
            "live_orders_created": 0,
            "autonomous_paper_orders_created": 0,
        },
        "market_ids": [record["market_id"] for record in events],
        "paper_fill_events": events,
        "limitations": [
            "Fill events are local paper accounting records only.",
            "Fill events preserve operator-provided manual fields and create no executable artifact.",
        ],
    }


def render_fill_source_markdown(contract_payload, fixture_payload):
    lines = [
        "# PAPER-011 Fill Source Contract",
        "",
        f"- task_id: {contract_payload['task_id']}",
        f"- source_manual_paper_intent_ledger_path: {contract_payload['source_manual_paper_intent_ledger_path']}",
        f"- source_paper_workbench_preview_path: {contract_payload['source_paper_workbench_preview_path']}",
        f"- market_ids: {','.join(contract_payload['market_ids'])}",
        f"- fixture_records: {len(fixture_payload['records'])}",
        "",
        "## Allowed Fill Source Types",
        "",
    ]
    lines.extend(_render_list(contract_payload["allowed_fill_source_types"], indent=""))
    lines.extend(
        [
            "",
            "## Required Fields",
            "",
        ]
    )
    lines.extend(_render_list(contract_payload["required_fields"], indent=""))
    lines.extend(
        [
            "",
            "## Safety",
            "",
            "- Contract requires local operator manual fill fixture fields only.",
            "- Contract requires paper_only true and inert_only true.",
            "- Contract requires generated_by_bot false, live_order_created false, and real_order_created false.",
            "- Contract has no external data requirement.",
            "",
        ]
    )
    return "\n".join(lines)


def render_fill_events_markdown(accepted_payload, rejected_payload, fill_events_payload):
    lines = [
        "# PAPER-012 Paper Fill Simulation From Manual Fixture",
        "",
        f"- task_id: {fill_events_payload['task_id']}",
        f"- fill_source_records_accepted: {accepted_payload['counts']['records_accepted']}",
        f"- fill_source_records_rejected: {rejected_payload['counts']['records_rejected']}",
        f"- paper_fill_events_written: {fill_events_payload['counts']['paper_fill_events_written']}",
        f"- real_orders_created: {fill_events_payload['counts']['real_orders_created']}",
        f"- live_orders_created: {fill_events_payload['counts']['live_orders_created']}",
        "",
        "## Accepted Fill Sources",
        "",
    ]
    if not accepted_payload["records"]:
        lines.append("- none")
    else:
        for record in accepted_payload["records"]:
            lines.append(
                f"- {record['fill_source_id']}: market_id={record['market_id']} type={record['fill_source_type']}"
            )
    lines.extend(["", "## Rejected Fill Sources", ""])
    if not rejected_payload["records"]:
        lines.append("- none")
    else:
        for record in rejected_payload["records"]:
            lines.append(
                f"- {record['fill_source_id']}: market_id={record['market_id']} reasons={','.join(record['rejection_reasons'])}"
            )
    lines.extend(["", "## Paper Fill Events", ""])
    if not fill_events_payload["paper_fill_events"]:
        lines.append("- none")
    else:
        for record in fill_events_payload["paper_fill_events"]:
            lines.append(
                f"- {record['paper_fill_event_id']}: market_id={record['market_id']} status={record['paper_fill_event_status']} fill_price={record['operator_manual_fill_price']} fill_size={record['operator_manual_fill_size']}"
            )
    lines.extend(
        [
            "",
            "## Safety",
            "",
            "- Fill events are generated only from accepted operator manual fill fixtures.",
            "- No real, live, or autonomous paper order artifact is created.",
            "",
        ]
    )
    return "\n".join(lines)


def build_settlement_source_fixture(fill_events_payload, source_fill_events_path=DEFAULT_FILL_EVENTS):
    fill_event = _records(fill_events_payload, "paper_fill_events")[0]
    return {
        "schema_version": "paper_settlement_source_fixture.v1",
        "task_id": TASK_ID,
        "deterministic": True,
        "source_paper_fill_events_path": _display_path(source_fill_events_path),
        "allowed_settlement_source_types": list(ALLOWED_SETTLEMENT_SOURCE_TYPES),
        "required_fields": list(SETTLEMENT_REQUIRED_FIELDS),
        "field_contract": {
            "market_id": "required string matching a recorded paper fill event market",
            "source_paper_fill_event_id": "required stable link to a recorded paper fill event",
            "operator_manual_settlement_status": "required operator-provided local paper settlement status",
            "operator_manual_settlement_outcome": "required operator-provided local paper settlement outcome label",
            "operator_manual_settlement_price": "required operator-provided local paper settlement payout value",
            "operator_manual_settlement_notes": "required operator-provided local paper settlement notes",
            "paper_only": "required boolean true",
            "inert_only": "required boolean true",
            "generated_by_bot": "required boolean false",
            "live_order_created": "required boolean false",
            "real_order_created": "required boolean false",
        },
        "records": [
            {
                "settlement_source_id": "paper-settlement-source-operator-manual-001",
                "market_id": fill_event["market_id"],
                "source_manual_intent_id": fill_event["source_manual_intent_id"],
                "source_ledger_entry_id": fill_event["source_ledger_entry_id"],
                "source_paper_fill_event_id": fill_event["paper_fill_event_id"],
                "settlement_source_type": "operator_manual_settlement_fixture",
                "operator_manual_settlement_status": "operator_manual_settlement_recorded",
                "operator_manual_settlement_outcome": "operator_fixture_outcome_settled",
                "operator_manual_settlement_price": 1.0,
                "operator_manual_settlement_notes": "Operator-entered local paper settlement fixture.",
                "paper_only": True,
                "inert_only": True,
                "generated_by_bot": False,
                "live_order_created": False,
                "real_order_created": False,
            },
            {
                "settlement_source_id": "paper-settlement-source-rejected-unknown-market",
                "market_id": "000000",
                "source_manual_intent_id": "manual-intent-unknown",
                "source_ledger_entry_id": "manual-paper-intent-ledger-unknown",
                "source_paper_fill_event_id": "paper-fill-event-unknown",
                "settlement_source_type": "operator_manual_settlement_fixture",
                "operator_manual_settlement_status": "operator_manual_settlement_recorded",
                "operator_manual_settlement_outcome": "operator_fixture_outcome_settled",
                "operator_manual_settlement_price": 1.0,
                "operator_manual_settlement_notes": "Invalid fixture row: market is absent from the paper fill events.",
                "paper_only": True,
                "inert_only": True,
                "generated_by_bot": False,
                "live_order_created": False,
                "real_order_created": False,
            },
            {
                "settlement_source_id": "paper-settlement-source-rejected-api-truth",
                "market_id": fill_event["market_id"],
                "source_manual_intent_id": fill_event["source_manual_intent_id"],
                "source_ledger_entry_id": fill_event["source_ledger_entry_id"],
                "source_paper_fill_event_id": fill_event["paper_fill_event_id"],
                "settlement_source_type": "operator_manual_settlement_fixture",
                "operator_manual_settlement_status": "operator_manual_settlement_recorded",
                "operator_manual_settlement_outcome": "operator_fixture_outcome_settled",
                "operator_manual_settlement_price": 1.0,
                "operator_manual_settlement_notes": "Invalid fixture row implies truth inference, API resolution, live resolution, and recommendation.",
                "paper_only": True,
                "inert_only": True,
                "generated_by_bot": True,
                "live_order_created": False,
                "real_order_created": False,
                "truth_inference": "blocked_fixture_value",
                "api_resolution": "blocked_fixture_value",
                "live_price": "blocked_fixture_value",
                "recommendation": "blocked_fixture_value",
            },
        ],
    }


def _paper_fill_events_by_id(fill_events_payload):
    return {
        _clean_text(record.get("paper_fill_event_id")): record
        for record in _records(fill_events_payload, "paper_fill_events")
        if _clean_text(record.get("paper_fill_event_id"))
    }


def _paper_fill_events_by_market_id(fill_events_payload):
    return {
        _clean_text(record.get("market_id")): record
        for record in _records(fill_events_payload, "paper_fill_events")
        if _clean_text(record.get("market_id"))
    }


def _settlement_rejection_record(record, reasons, blocked_keys, unexpected_keys, blocked_markers):
    return {
        "settlement_source_id": _clean_text(record.get("settlement_source_id")),
        "market_id": _clean_text(record.get("market_id")),
        "source_manual_intent_id": _clean_text(record.get("source_manual_intent_id")),
        "source_paper_fill_event_id": _clean_text(record.get("source_paper_fill_event_id")),
        "settlement_source_type": _clean_text(record.get("settlement_source_type")),
        "settlement_source_status": "rejected",
        "rejection_reasons": reasons,
        "blocked_keys": blocked_keys,
        "unexpected_keys": unexpected_keys,
        "blocked_language_markers": blocked_markers,
    }


def _accepted_settlement_record(record):
    return {
        "settlement_source_id": _clean_text(record.get("settlement_source_id")),
        "market_id": _clean_text(record.get("market_id")),
        "source_manual_intent_id": _clean_text(record.get("source_manual_intent_id")),
        "source_ledger_entry_id": _clean_text(record.get("source_ledger_entry_id")),
        "source_paper_fill_event_id": _clean_text(record.get("source_paper_fill_event_id")),
        "settlement_source_type": _clean_text(record.get("settlement_source_type")),
        "settlement_source_status": "accepted_for_paper_accounting_processing",
        "operator_manual_settlement_status": _clean_text(record.get("operator_manual_settlement_status")),
        "operator_manual_settlement_outcome": _clean_text(record.get("operator_manual_settlement_outcome")),
        "operator_manual_settlement_price": record.get("operator_manual_settlement_price"),
        "operator_manual_settlement_notes": _clean_text(record.get("operator_manual_settlement_notes")),
        "paper_only": True,
        "inert_only": True,
        "generated_by_bot": False,
        "live_order_created": False,
        "real_order_created": False,
    }


def build_settlement_outputs(fill_events_payload, settlement_fixture_payload, settlement_fixture_path=DEFAULT_SETTLEMENT_FIXTURE):
    fill_events_by_id = _paper_fill_events_by_id(fill_events_payload)
    fill_events_by_market = _paper_fill_events_by_market_id(fill_events_payload)
    accepted = []
    rejected = []

    for record in _records(settlement_fixture_payload, "records"):
        market_id = _clean_text(record.get("market_id"))
        source_event_id = _clean_text(record.get("source_paper_fill_event_id"))
        settlement_source_type = _clean_text(record.get("settlement_source_type"))
        reasons = []
        blocked_keys = _blocked_keys(record, SETTLEMENT_SOURCE_FIELDS)
        unexpected_keys = _unexpected_keys(record, SETTLEMENT_SOURCE_FIELDS)
        blocked_markers = _blocked_value_markers(record)

        for field in SETTLEMENT_REQUIRED_FIELDS:
            if field not in record:
                reasons.append(f"{field}_required")
        fill_event = fill_events_by_id.get(source_event_id)
        if market_id not in fill_events_by_market:
            reasons.append("unknown_market_id")
        if source_event_id not in fill_events_by_id:
            reasons.append("unknown_source_paper_fill_event_id")
        elif fill_event and market_id != fill_event.get("market_id"):
            reasons.append("source_paper_fill_event_market_mismatch")
        if settlement_source_type not in ALLOWED_SETTLEMENT_SOURCE_TYPES:
            reasons.append("unknown_settlement_source_type")
        if record.get("paper_only") is not True:
            reasons.append("paper_only_true_required")
        if record.get("inert_only") is not True:
            reasons.append("inert_only_true_required")
        if record.get("generated_by_bot") is not False:
            reasons.append("generated_by_bot_false_required")
        if record.get("live_order_created") is not False:
            reasons.append("live_order_created_false_required")
        if record.get("real_order_created") is not False:
            reasons.append("real_order_created_false_required")
        if settlement_source_type == "operator_manual_settlement_fixture":
            if not _clean_text(record.get("operator_manual_settlement_status")):
                reasons.append("operator_manual_settlement_status_required")
            if not _clean_text(record.get("operator_manual_settlement_outcome")):
                reasons.append("operator_manual_settlement_outcome_required")
            if not _is_valid_price(record.get("operator_manual_settlement_price")):
                reasons.append("operator_manual_settlement_price_invalid")
        elif settlement_source_type == "blocked_by_policy":
            reasons.append("blocked_by_policy")
        if blocked_keys:
            reasons.append("prohibited_or_resolution_field_present")
        if unexpected_keys:
            reasons.append("unexpected_field_present")
        if blocked_markers:
            reasons.append("blocked_language_present")

        reasons = list(dict.fromkeys(reasons))
        if reasons:
            rejected.append(_settlement_rejection_record(record, reasons, blocked_keys, unexpected_keys, blocked_markers))
            continue
        accepted.append(_accepted_settlement_record(record))

    accepted.sort(key=lambda item: (item["market_id"], item["settlement_source_id"]))
    rejected.sort(key=lambda item: item["settlement_source_id"])

    common = {
        "task_id": TASK_ID,
        "deterministic": True,
        "source_paper_fill_events_path": _display_path(DEFAULT_FILL_EVENTS),
        "input_path": _display_path(settlement_fixture_path),
    }
    accepted_payload = {
        "schema_version": "paper_settlement_sources_accepted.v1",
        **common,
        "counts": {
            "records_read": len(_records(settlement_fixture_payload, "records")),
            "records_accepted": len(accepted),
        },
        "records": accepted,
    }
    rejected_payload = {
        "schema_version": "paper_settlement_sources_rejected.v1",
        **common,
        "counts": {
            "records_read": len(_records(settlement_fixture_payload, "records")),
            "records_rejected": len(rejected),
            "rejection_reason_counts": _count_by_reason(rejected),
        },
        "records": rejected,
    }
    return accepted_payload, rejected_payload


def build_pnl_preview(
    fill_events_payload,
    accepted_settlement_payload,
    source_fill_events_path=DEFAULT_FILL_EVENTS,
    source_settlement_path=DEFAULT_SETTLEMENT_ACCEPTED,
):
    settlements_by_event = {
        record["source_paper_fill_event_id"]: record
        for record in _records(accepted_settlement_payload, "records")
    }
    accounting_records = []
    total_cost_basis = Decimal("0")
    total_settlement_value = Decimal("0")
    total_pnl = Decimal("0")

    for index, fill_event in enumerate(_records(fill_events_payload, "paper_fill_events"), start=1):
        settlement = settlements_by_event.get(fill_event["paper_fill_event_id"])
        fill_price = _decimal_from_value(fill_event["operator_manual_fill_price"])
        fill_size = _decimal_from_value(fill_event["operator_manual_fill_size"])
        if settlement is None:
            accounting_records.append(
                {
                    "paper_accounting_record_id": f"paper-accounting-pnl-{index:03d}",
                    "market_id": fill_event["market_id"],
                    "source_paper_fill_event_id": fill_event["paper_fill_event_id"],
                    "paper_accounting_status": "paper_position_open_pending_settlement",
                    "paper_only": True,
                    "inert_only": True,
                    "generated_by_bot": False,
                    "live_order_created": False,
                    "real_order_created": False,
                }
            )
            continue

        settlement_price = _decimal_from_value(settlement["operator_manual_settlement_price"])
        cost_basis = fill_price * fill_size
        settlement_value = settlement_price * fill_size
        pnl = settlement_value - cost_basis
        total_cost_basis += cost_basis
        total_settlement_value += settlement_value
        total_pnl += pnl

        accounting_records.append(
            {
                "paper_accounting_record_id": f"paper-accounting-pnl-{index:03d}",
                "market_id": fill_event["market_id"],
                "source_paper_fill_event_id": fill_event["paper_fill_event_id"],
                "source_settlement_id": settlement["settlement_source_id"],
                "source_manual_intent_id": fill_event["source_manual_intent_id"],
                "source_ledger_entry_id": fill_event["source_ledger_entry_id"],
                "paper_accounting_status": "paper_position_settled_from_operator_manual_fixture",
                "operator_manual_fill_price": fill_event["operator_manual_fill_price"],
                "operator_manual_fill_size": fill_event["operator_manual_fill_size"],
                "operator_manual_settlement_outcome": settlement["operator_manual_settlement_outcome"],
                "operator_manual_settlement_price": settlement["operator_manual_settlement_price"],
                "paper_accounting_cost_basis": _format_accounting_decimal(cost_basis),
                "paper_accounting_settlement_value": _format_accounting_decimal(settlement_value),
                "paper_accounting_pnl": _format_accounting_decimal(pnl),
                "paper_accounting_only": True,
                "paper_only": True,
                "inert_only": True,
                "generated_by_bot": False,
                "live_order_created": False,
                "real_order_created": False,
                "safety_flags": [
                    "paper_only",
                    "inert_only",
                    "operator_manual_fill_fixture",
                    "operator_manual_settlement_fixture",
                    "paper_accounting_only",
                    "no_live_execution",
                    "no_real_execution",
                    "no_credential_or_endpoint_use",
                ],
            }
        )

    accounting_records.sort(key=lambda item: (item["market_id"], item["paper_accounting_record_id"]))
    return {
        "schema_version": "paper_accounting_pnl_preview.v1",
        "markdown_version": "paper_accounting_pnl_preview_report.v1",
        "task_id": TASK_ID,
        "deterministic": True,
        "source_paper_fill_events_path": _display_path(source_fill_events_path),
        "source_paper_settlement_sources_accepted_path": _display_path(source_settlement_path),
        "allowed_paper_accounting_statuses": list(ALLOWED_PAPER_ACCOUNTING_STATUSES),
        "counts": {
            "paper_fill_events_read": len(_records(fill_events_payload, "paper_fill_events")),
            "settlement_records_accepted": len(_records(accepted_settlement_payload, "records")),
            "paper_accounting_pnl_records": len(accounting_records),
            "real_orders_created": 0,
            "live_orders_created": 0,
            "autonomous_paper_orders_created": 0,
        },
        "market_ids": [record["market_id"] for record in accounting_records],
        "paper_accounting_totals": {
            "paper_accounting_total_cost_basis": _format_accounting_decimal(total_cost_basis),
            "paper_accounting_total_settlement_value": _format_accounting_decimal(total_settlement_value),
            "paper_accounting_total_pnl": _format_accounting_decimal(total_pnl),
        },
        "paper_accounting_records": accounting_records,
        "limitations": [
            "Accounting preview uses only local operator manual fixture fill and settlement values.",
            "Accounting preview is paper-only and inert.",
        ],
    }


def render_pnl_preview_markdown(pnl_payload):
    lines = [
        "# PAPER-013 Paper Settlement And PnL Accounting Preview",
        "",
        f"- task_id: {pnl_payload['task_id']}",
        f"- paper_accounting_pnl_records: {pnl_payload['counts']['paper_accounting_pnl_records']}",
        f"- paper_accounting_total_cost_basis: {pnl_payload['paper_accounting_totals']['paper_accounting_total_cost_basis']}",
        f"- paper_accounting_total_settlement_value: {pnl_payload['paper_accounting_totals']['paper_accounting_total_settlement_value']}",
        f"- paper_accounting_total_pnl: {pnl_payload['paper_accounting_totals']['paper_accounting_total_pnl']}",
        f"- real_orders_created: {pnl_payload['counts']['real_orders_created']}",
        f"- live_orders_created: {pnl_payload['counts']['live_orders_created']}",
        "",
        "## Accounting Records",
        "",
    ]
    if not pnl_payload["paper_accounting_records"]:
        lines.append("- none")
    else:
        for record in pnl_payload["paper_accounting_records"]:
            if record["paper_accounting_status"] == "paper_position_open_pending_settlement":
                lines.append(
                    f"- {record['paper_accounting_record_id']}: market_id={record['market_id']} status={record['paper_accounting_status']}"
                )
            else:
                lines.append(
                    f"- {record['paper_accounting_record_id']}: market_id={record['market_id']} status={record['paper_accounting_status']} paper_accounting_pnl={record['paper_accounting_pnl']}"
                )
    lines.extend(
        [
            "",
            "## Safety",
            "",
            "- PnL is paper accounting only from operator manual fixture values.",
            "- No real, live, or autonomous paper order artifact is created.",
            "",
        ]
    )
    return "\n".join(lines)


def _result_payload(counts, status="completed_ready_for_review", blockers=None, tests=None):
    return {
        "task_id": TASK_ID,
        "status": status,
        "summary": (
            "Implemented deterministic offline PAPER-011 through PAPER-013 fill source, paper fill event, settlement, and paper accounting PnL preview artifacts."
        )
        if status == "completed_ready_for_review"
        else "Blocked before completing deterministic offline paper fill, settlement, and accounting artifacts.",
        "market_ids": ["824952"] if status == "completed_ready_for_review" else [],
        "stages_completed": {
            "paper_011_fill_source_contract": status == "completed_ready_for_review",
            "paper_012_paper_fill_simulation": status == "completed_ready_for_review",
            "paper_013_paper_settlement_pnl_accounting_preview": status == "completed_ready_for_review",
        },
        "counts": counts,
        "accounting": {
            "paper_accounting_pnl_calculated": status == "completed_ready_for_review",
            "pnl_source": "operator_manual_fill_and_settlement_fixtures_only",
            "ev_calculated": False,
            "probability_calculated": False,
            "score_calculated": False,
            "edge_calculated": False,
            "recommendation_generated": False,
        },
        "files_created": FILES_CREATED,
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
            "runtime_wiring": False,
            "dispatcher_run_codex_changes": False,
            "prompt_automation": False,
            "codex_copy_roots": False,
            "completed_dossiers": False,
            "broad_refactor": False,
        },
        "scope_expansion": {
            "manual_operator_fill_fields_introduced": status == "completed_ready_for_review",
            "manual_operator_settlement_fields_introduced": status == "completed_ready_for_review",
            "manual_fields_are_operator_provided_only": True,
            "bot_generated_side_size_price": False,
            "paper_only_inert_fill_events": status == "completed_ready_for_review",
            "paper_accounting_only_pnl": status == "completed_ready_for_review",
        },
        "blockers": blockers or [],
    }


def write_paper_fill_settlement_pnl_artifacts(
    manual_ledger_path=DEFAULT_MANUAL_LEDGER,
    workbench_preview_path=DEFAULT_WORKBENCH_PREVIEW,
):
    manual_ledger_path = _resolve_path(manual_ledger_path)
    workbench_preview_path = _resolve_path(workbench_preview_path)
    if not manual_ledger_path.exists():
        raise FileNotFoundError(f"missing manual paper intent ledger: {_display_path(manual_ledger_path)}")
    if not workbench_preview_path.exists():
        raise FileNotFoundError(f"missing paper workbench preview: {_display_path(workbench_preview_path)}")

    ledger_payload = _load_json(manual_ledger_path)
    preview_payload = _load_json(workbench_preview_path)
    _validate_source_artifacts(ledger_payload, preview_payload)

    fill_contract = build_fill_source_contract(ledger_payload, preview_payload, manual_ledger_path, workbench_preview_path)
    _write_json(DEFAULT_FILL_CONTRACT, fill_contract)
    fill_fixture = build_fill_source_fixture(ledger_payload, DEFAULT_FILL_CONTRACT, manual_ledger_path)
    _write_json(DEFAULT_FILL_FIXTURE, fill_fixture)
    _write_text(DEFAULT_FILL_REPORT, render_fill_source_markdown(fill_contract, fill_fixture))

    accepted_fill, rejected_fill, fill_events = build_fill_source_outputs(ledger_payload, fill_fixture, DEFAULT_FILL_FIXTURE)
    _write_json(DEFAULT_FILL_ACCEPTED, accepted_fill)
    _write_json(DEFAULT_FILL_REJECTED, rejected_fill)
    _write_json(DEFAULT_FILL_EVENTS, fill_events)
    _write_json(DEFAULT_FILL_EVENTS_EXPECTED, fill_events)
    _write_text(DEFAULT_FILL_EVENTS_REPORT, render_fill_events_markdown(accepted_fill, rejected_fill, fill_events))

    settlement_fixture = build_settlement_source_fixture(fill_events, DEFAULT_FILL_EVENTS)
    _write_json(DEFAULT_SETTLEMENT_FIXTURE, settlement_fixture)
    accepted_settlement, rejected_settlement = build_settlement_outputs(
        fill_events,
        settlement_fixture,
        DEFAULT_SETTLEMENT_FIXTURE,
    )
    _write_json(DEFAULT_SETTLEMENT_ACCEPTED, accepted_settlement)
    _write_json(DEFAULT_SETTLEMENT_REJECTED, rejected_settlement)

    pnl_preview = build_pnl_preview(fill_events, accepted_settlement, DEFAULT_FILL_EVENTS, DEFAULT_SETTLEMENT_ACCEPTED)
    _write_json(DEFAULT_PNL_PREVIEW, pnl_preview)
    _write_json(DEFAULT_PNL_PREVIEW_EXPECTED, pnl_preview)
    _write_text(DEFAULT_PNL_PREVIEW_MD, render_pnl_preview_markdown(pnl_preview))

    counts = {
        "fill_source_records_accepted": accepted_fill["counts"]["records_accepted"],
        "fill_source_records_rejected": rejected_fill["counts"]["records_rejected"],
        "paper_fill_events_written": fill_events["counts"]["paper_fill_events_written"],
        "settlement_records_accepted": accepted_settlement["counts"]["records_accepted"],
        "settlement_records_rejected": rejected_settlement["counts"]["records_rejected"],
        "paper_accounting_pnl_records": pnl_preview["counts"]["paper_accounting_pnl_records"],
        "real_orders_created": 0,
        "live_orders_created": 0,
        "autonomous_paper_orders_created": 0,
    }
    result_payload = _result_payload(counts)
    _write_json(DEFAULT_RESULT, result_payload)
    return {
        "task_id": TASK_ID,
        "status": "completed_ready_for_review",
        "market_ids": ["824952"],
        "counts": counts,
        "accounting": result_payload["accounting"],
        "result_path": _display_path(DEFAULT_RESULT),
    }


def main(argv):
    args = _parse_args(argv)
    try:
        summary = write_paper_fill_settlement_pnl_artifacts(args.manual_ledger, args.workbench_preview)
    except Exception as exc:
        blocked_counts = {
            "fill_source_records_accepted": 0,
            "fill_source_records_rejected": 0,
            "paper_fill_events_written": 0,
            "settlement_records_accepted": 0,
            "settlement_records_rejected": 0,
            "paper_accounting_pnl_records": 0,
            "real_orders_created": 0,
            "live_orders_created": 0,
            "autonomous_paper_orders_created": 0,
        }
        _write_json(DEFAULT_RESULT, _result_payload(blocked_counts, status="blocked", blockers=[str(exc)]))
        print(json.dumps({"task_id": TASK_ID, "status": "blocked", "blockers": [str(exc)]}, indent=2, ensure_ascii=True))
        return 2
    print(json.dumps(summary, indent=2, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
