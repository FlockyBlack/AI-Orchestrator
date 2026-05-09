from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from copy import deepcopy
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

REQUEST_CONTRACT_VERSION = "pmbot_paper_accounting_ledger_request.v1"
LEDGER_CONTRACT_VERSION = "pmbot_paper_accounting_ledger.v1"
LOCAL_RUN_MODE = "local_paper_only"
OPERATOR_REVIEW_STATUS = "pending_operator_review"
LEDGER_ROW_STATE = "descriptive_paper_accounting_record"
SAMPLE_LEDGER_PATH = Path("pm_bot/paper_accounting/samples/paper_accounting_ledger.fixture.json")

ALLOWED_LOCAL_REFERENCE_PREFIXES = (
    "pm_bot/tests/fixtures/paper_accounting/",
    "pm_bot/paper_accounting/samples/",
)
FORBIDDEN_LOCAL_REFERENCE_PREFIXES = (
    ".env",
    "agent_tasks/running/",
    "dispatcher/",
    "pm_bot/llm/",
    "pm_bot/orders/",
    "pm_bot/trading/",
    "pm_bot/wallet/",
    "run_codex/",
    "runtime/",
)
FORBIDDEN_DECISION_TOKENS = {
    "advice",
    "buy",
    "confidence",
    "edge",
    "enter",
    "ev",
    "exit",
    "forecast",
    "guidance",
    "hold",
    "odds",
    "pick",
    "probability",
    "recommendation",
    "score",
    "scoring",
    "selection",
    "sell",
    "side",
    "stake",
    "wager",
}
LOCAL_ONLY_SAFETY_BOUNDARIES = {
    "account_change_instruction_allowed": False,
    "external_market_api_allowed": False,
    "llm_calls_allowed": False,
    "market_ranking_allowed": False,
    "network_calls_allowed": False,
    "offline_inputs_only": True,
    "operator_review_gate_required": True,
    "real_money_or_signing_allowed": False,
    "runtime_wiring_allowed": False,
    "scheduler_or_worker_allowed": False,
    "transaction_endpoint_allowed": False,
    "wallet_or_order_code_allowed": False,
}


@dataclass(frozen=True)
class ValidationResult:
    valid: bool
    errors: tuple[str, ...] = ()


class PaperAccountingLedgerValidationError(ValueError):
    def __init__(self, errors: tuple[str, ...]):
        super().__init__("; ".join(errors))
        self.errors = errors


def load_accounting_request(path: str | Path) -> dict[str, Any]:
    request_path = Path(path)
    return json.loads(request_path.read_text(encoding="utf-8"))


def validate_accounting_request(request: Any) -> ValidationResult:
    errors: list[str] = []
    if not isinstance(request, dict):
        return ValidationResult(False, ("request must be an object",))

    errors.extend(_find_forbidden_decision_terms(request, "request"))
    _validate_request_top_level(request, errors)

    source_artifacts = request.get("source_artifacts")
    artifact_by_id: dict[str, dict[str, Any]] = {}
    artifact_payloads: dict[str, dict[str, Any]] = {}
    event_by_artifact_id: dict[str, dict[str, dict[str, Any]]] = {}
    if isinstance(source_artifacts, list):
        for artifact_index, artifact in enumerate(source_artifacts):
            _validate_source_artifact(
                artifact,
                artifact_index,
                errors,
                artifact_by_id,
                artifact_payloads,
                event_by_artifact_id,
            )

    entry_specs = request.get("entry_specs")
    if isinstance(entry_specs, list):
        for entry_index, entry_spec in enumerate(entry_specs):
            _validate_entry_spec(entry_spec, entry_index, errors, artifact_by_id, event_by_artifact_id)

    return ValidationResult(not errors, tuple(errors))


def build_paper_accounting_ledger(request: dict[str, Any]) -> dict[str, Any]:
    validation = validate_accounting_request(request)
    if not validation.valid:
        raise PaperAccountingLedgerValidationError(validation.errors)

    artifacts = {artifact["artifact_id"]: artifact for artifact in request["source_artifacts"]}
    payloads = {
        artifact["artifact_id"]: _load_local_json_object(artifact["local_reference"])
        for artifact in request["source_artifacts"]
    }
    events = {
        artifact_id: {str(event["event_id"]): event for event in payload["events"]}
        for artifact_id, payload in payloads.items()
    }

    source_inventory = []
    for artifact in request["source_artifacts"]:
        artifact_id = artifact["artifact_id"]
        source_inventory.append(
            {
                "artifact_id": artifact_id,
                "artifact_label": artifact["artifact_label"],
                "artifact_loaded": True,
                "artifact_role": artifact["artifact_role"],
                "entry_count": sum(
                    1 for entry_spec in request["entry_specs"] if entry_spec["source_artifact_id"] == artifact_id
                ),
                "local_reference": artifact["local_reference"],
                "operator_review_status": OPERATOR_REVIEW_STATUS,
                "required_field_count": len(artifact["required_fields"]),
                "runner_state": LEDGER_ROW_STATE,
            }
        )

    accounting_entries = []
    for entry_spec in request["entry_specs"]:
        artifact = artifacts[entry_spec["source_artifact_id"]]
        source_event = events[entry_spec["source_artifact_id"]][entry_spec["event_id"]]
        accounting_entries.append(
            {
                "asset_code": entry_spec["asset_code"],
                "entry_id": entry_spec["entry_id"],
                "entry_type": entry_spec["entry_type"],
                "event_id": entry_spec["event_id"],
                "event_timestamp": source_event["event_timestamp"],
                "local_reference": artifact["local_reference"],
                "memo": source_event["memo"],
                "operator_review_label": entry_spec["operator_review_label"],
                "operator_review_status": OPERATOR_REVIEW_STATUS,
                "quantity_delta": _format_decimal(_decimal_from_string(entry_spec["quantity_delta"])),
                "row_state": LEDGER_ROW_STATE,
                "source_artifact_id": artifact["artifact_id"],
                "source_artifact_label": artifact["artifact_label"],
                "source_artifact_role": artifact["artifact_role"],
            }
        )

    balance_summary = _build_balance_summary(accounting_entries)
    ledger = {
        "account_context": deepcopy(request["account_context"]),
        "accounting_entries": accounting_entries,
        "balance_summary": balance_summary,
        "build_id": f"{request['ledger_id']}-{_stable_digest(request)}",
        "contract_version": LEDGER_CONTRACT_VERSION,
        "errors": [],
        "ledger_id": request["ledger_id"],
        "local_only": True,
        "operator_review": {
            "required": True,
            "review_steps": list(request["operator_review_steps"]),
            "status": OPERATOR_REVIEW_STATUS,
        },
        "operator_review_required": True,
        "run_mode": LOCAL_RUN_MODE,
        "safety_boundaries": dict(LOCAL_ONLY_SAFETY_BOUNDARIES),
        "source_inventory": source_inventory,
        "summary_counts": {
            "accounting_entries": len(accounting_entries),
            "assets": len(balance_summary),
            "source_artifacts": len(source_inventory),
            "warnings": 0,
        },
        "warnings": [],
    }
    return ledger


def validate_paper_accounting_ledger(ledger: Any) -> ValidationResult:
    errors: list[str] = []
    if not isinstance(ledger, dict):
        return ValidationResult(False, ("ledger must be an object",))

    errors.extend(_find_forbidden_decision_terms(ledger, "ledger"))
    required_fields = {
        "account_context",
        "accounting_entries",
        "balance_summary",
        "build_id",
        "contract_version",
        "errors",
        "ledger_id",
        "local_only",
        "operator_review",
        "operator_review_required",
        "run_mode",
        "safety_boundaries",
        "source_inventory",
        "summary_counts",
        "warnings",
    }
    _require_keys(ledger, required_fields, "ledger", errors)
    if errors:
        return ValidationResult(False, tuple(errors))

    if ledger["contract_version"] != LEDGER_CONTRACT_VERSION:
        errors.append(f"ledger.contract_version must be {LEDGER_CONTRACT_VERSION}")
    if ledger["run_mode"] != LOCAL_RUN_MODE:
        errors.append(f"ledger.run_mode must be {LOCAL_RUN_MODE}")
    if ledger["local_only"] is not True:
        errors.append("ledger.local_only must be true")
    if ledger["operator_review_required"] is not True:
        errors.append("ledger.operator_review_required must be true")
    if ledger["safety_boundaries"] != LOCAL_ONLY_SAFETY_BOUNDARIES:
        errors.append("ledger.safety_boundaries must match the closed local-only safety boundary contract")

    operator_review = ledger["operator_review"]
    if not isinstance(operator_review, dict):
        errors.append("ledger.operator_review must be an object")
    elif operator_review.get("status") != OPERATOR_REVIEW_STATUS:
        errors.append(f"ledger.operator_review.status must be {OPERATOR_REVIEW_STATUS}")

    accounting_entries = ledger["accounting_entries"]
    if not isinstance(accounting_entries, list):
        errors.append("ledger.accounting_entries must be a list")
        accounting_entries = []
    source_inventory = ledger["source_inventory"]
    if not isinstance(source_inventory, list):
        errors.append("ledger.source_inventory must be a list")
        source_inventory = []
    balance_summary = ledger["balance_summary"]
    if not isinstance(balance_summary, list):
        errors.append("ledger.balance_summary must be a list")
        balance_summary = []

    for entry_index, entry in enumerate(accounting_entries):
        if not isinstance(entry, dict):
            errors.append(f"ledger.accounting_entries[{entry_index}] must be an object")
            continue
        if entry.get("operator_review_status") != OPERATOR_REVIEW_STATUS:
            errors.append(
                f"ledger.accounting_entries[{entry_index}].operator_review_status must be {OPERATOR_REVIEW_STATUS}"
            )
        if entry.get("row_state") != LEDGER_ROW_STATE:
            errors.append(f"ledger.accounting_entries[{entry_index}].row_state must be {LEDGER_ROW_STATE}")
        try:
            _decimal_from_string(entry.get("quantity_delta"))
        except PaperAccountingLedgerValidationError:
            errors.append(f"ledger.accounting_entries[{entry_index}].quantity_delta must be a decimal string")

    summary_counts = ledger["summary_counts"]
    if not isinstance(summary_counts, dict):
        errors.append("ledger.summary_counts must be an object")
    else:
        expected_counts = {
            "accounting_entries": len(accounting_entries),
            "assets": len({entry.get("asset_code") for entry in accounting_entries if isinstance(entry, dict)}),
            "source_artifacts": len(source_inventory),
            "warnings": len(ledger["warnings"]) if isinstance(ledger["warnings"], list) else 0,
        }
        if summary_counts != expected_counts:
            errors.append("ledger.summary_counts must match accounting entry, asset, source, and warning totals")

    expected_balance_summary = _build_balance_summary(accounting_entries)
    if balance_summary != expected_balance_summary:
        errors.append("ledger.balance_summary must match accounting_entries totals")

    inventory_entry_counts = {
        inventory_row.get("artifact_id"): inventory_row.get("entry_count")
        for inventory_row in source_inventory
        if isinstance(inventory_row, dict)
    }
    actual_entry_counts: dict[str, int] = defaultdict(int)
    for entry in accounting_entries:
        if isinstance(entry, dict):
            actual_entry_counts[str(entry.get("source_artifact_id"))] += 1
    for artifact_id, entry_count in inventory_entry_counts.items():
        if actual_entry_counts[str(artifact_id)] != entry_count:
            errors.append("ledger.source_inventory entry_count must match accounting_entries")

    return ValidationResult(not errors, tuple(errors))


def build_operator_report(ledger: dict[str, Any]) -> str:
    lines = [
        "# PMBOT Paper Accounting Ledger",
        "",
        f"Ledger ID: `{ledger['ledger_id']}`",
        f"Build ID: `{ledger['build_id']}`",
        f"Run mode: `{ledger['run_mode']}`",
        f"Operator review: `{ledger['operator_review']['status']}`",
        "",
        "## Summary",
        "",
        f"- Accounting entries: {ledger['summary_counts']['accounting_entries']}",
        f"- Source artifacts: {ledger['summary_counts']['source_artifacts']}",
        f"- Assets: {ledger['summary_counts']['assets']}",
        f"- Warnings: {ledger['summary_counts']['warnings']}",
        "",
        "## Balance Summary",
        "",
    ]
    for balance in ledger["balance_summary"]:
        lines.append(
            f"- `{balance['asset_code']}` net quantity delta `{balance['net_quantity_delta']}` "
            f"from {balance['entry_count']} entries."
        )
    lines.extend(["", "## Accounting Entries", ""])
    for entry in ledger["accounting_entries"]:
        lines.append(
            f"- `{entry['entry_id']}`: `{entry['asset_code']}` delta `{entry['quantity_delta']}` "
            f"from `{entry['source_artifact_id']}`. Review `{entry['operator_review_label']}`."
        )
    lines.extend(
        [
            "",
            "## Safety",
            "",
            "- Local fixture/static input only.",
            "- Makes no network, LLM, external market API, wallet, order, transaction endpoint, or runtime calls.",
            "- Descriptive paper accounting only; it is not an approval record for execution.",
            "- Operator review remains required before using these records outside this local artifact.",
            "",
        ]
    )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a local-only PMBOT paper accounting ledger.")
    parser.add_argument("--request", required=True, help="Path to the local paper accounting ledger request JSON.")
    parser.add_argument("--output-ledger", required=True, help="Path where the JSON ledger should be written.")
    parser.add_argument("--output-report", required=True, help="Path where the Markdown operator report should be written.")
    args = parser.parse_args(argv)

    request = load_accounting_request(args.request)
    ledger = build_paper_accounting_ledger(request)
    ledger_validation = validate_paper_accounting_ledger(ledger)
    if not ledger_validation.valid:
        raise PaperAccountingLedgerValidationError(ledger_validation.errors)

    output_ledger = Path(args.output_ledger)
    output_report = Path(args.output_report)
    output_ledger.parent.mkdir(parents=True, exist_ok=True)
    output_report.parent.mkdir(parents=True, exist_ok=True)
    output_ledger.write_text(json.dumps(ledger, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    output_report.write_text(build_operator_report(ledger), encoding="utf-8")
    return 0


def _validate_request_top_level(request: dict[str, Any], errors: list[str]) -> None:
    required_fields = {
        "account_context",
        "contract_version",
        "entry_specs",
        "ledger_id",
        "local_only",
        "operator_review_required",
        "operator_review_steps",
        "scope",
        "source_artifacts",
    }
    _require_keys(request, required_fields, "request", errors)
    if request.get("contract_version") != REQUEST_CONTRACT_VERSION:
        errors.append(f"request.contract_version must be {REQUEST_CONTRACT_VERSION}")
    if request.get("scope") != "paper_accounting_ledger":
        errors.append("request.scope must be paper_accounting_ledger")
    if request.get("local_only") is not True:
        errors.append("request.local_only must be true")
    if request.get("operator_review_required") is not True:
        errors.append("request.operator_review_required must be true")
    if not isinstance(request.get("account_context"), dict):
        errors.append("request.account_context must be an object")
    if not isinstance(request.get("source_artifacts"), list) or not request.get("source_artifacts"):
        errors.append("request.source_artifacts must be a non-empty list")
    if not isinstance(request.get("entry_specs"), list) or not request.get("entry_specs"):
        errors.append("request.entry_specs must be a non-empty list")
    if not isinstance(request.get("operator_review_steps"), list) or not request.get("operator_review_steps"):
        errors.append("request.operator_review_steps must be a non-empty list")


def _validate_source_artifact(
    artifact: Any,
    artifact_index: int,
    errors: list[str],
    artifact_by_id: dict[str, dict[str, Any]],
    artifact_payloads: dict[str, dict[str, Any]],
    event_by_artifact_id: dict[str, dict[str, dict[str, Any]]],
) -> None:
    path = f"request.source_artifacts[{artifact_index}]"
    if not isinstance(artifact, dict):
        errors.append(f"{path} must be an object")
        return
    required_fields = {
        "artifact_id",
        "artifact_label",
        "artifact_role",
        "local_reference",
        "required_fields",
        "review_checks",
        "known_limitations",
    }
    _require_keys(artifact, required_fields, path, errors)
    artifact_id = artifact.get("artifact_id")
    if not isinstance(artifact_id, str) or not artifact_id:
        errors.append(f"{path}.artifact_id must be a non-empty string")
        return
    if artifact_id in artifact_by_id:
        errors.append(f"{path}.artifact_id duplicates {artifact_id}")
        return
    artifact_by_id[artifact_id] = artifact

    local_reference = artifact.get("local_reference")
    if not _is_allowed_local_reference(local_reference):
        errors.append(f"{path}.local_reference must stay under paper accounting allowed local paths")
        return

    try:
        payload = _load_local_json_object(str(local_reference))
    except PaperAccountingLedgerValidationError as exc:
        errors.extend(f"{path}: {error}" for error in exc.errors)
        return
    artifact_payloads[artifact_id] = payload

    declared_fields = artifact.get("required_fields")
    if not isinstance(declared_fields, list) or not declared_fields:
        errors.append(f"{path}.required_fields must be a non-empty list")
        declared_fields = []
    missing_fields = [field for field in declared_fields if isinstance(field, str) and field not in payload]
    if missing_fields:
        errors.append(f"{path}.required_fields references missing local artifact fields: {', '.join(missing_fields)}")

    events = payload.get("events")
    if not isinstance(events, list) or not events:
        errors.append(f"{path}.local_reference events must be a non-empty list")
        return
    event_index: dict[str, dict[str, Any]] = {}
    for event_position, event in enumerate(events):
        event_path = f"{path}.local_reference.events[{event_position}]"
        if not isinstance(event, dict):
            errors.append(f"{event_path} must be an object")
            continue
        _require_keys(
            event,
            {"asset_code", "event_id", "event_timestamp", "event_type", "memo", "quantity_delta"},
            event_path,
            errors,
        )
        event_id = event.get("event_id")
        if isinstance(event_id, str) and event_id:
            event_index[event_id] = event
        try:
            _decimal_from_string(event.get("quantity_delta"))
        except PaperAccountingLedgerValidationError:
            errors.append(f"{event_path}.quantity_delta must be a decimal string")
    event_by_artifact_id[artifact_id] = event_index


def _validate_entry_spec(
    entry_spec: Any,
    entry_index: int,
    errors: list[str],
    artifact_by_id: dict[str, dict[str, Any]],
    event_by_artifact_id: dict[str, dict[str, dict[str, Any]]],
) -> None:
    path = f"request.entry_specs[{entry_index}]"
    if not isinstance(entry_spec, dict):
        errors.append(f"{path} must be an object")
        return
    required_fields = {
        "asset_code",
        "entry_id",
        "entry_type",
        "event_id",
        "operator_review_label",
        "quantity_delta",
        "source_artifact_id",
    }
    _require_keys(entry_spec, required_fields, path, errors)
    source_artifact_id = entry_spec.get("source_artifact_id")
    event_id = entry_spec.get("event_id")
    if source_artifact_id not in artifact_by_id:
        errors.append(f"{path}.source_artifact_id must reference a declared source artifact")
        return
    artifact_events = event_by_artifact_id.get(str(source_artifact_id), {})
    source_event = artifact_events.get(str(event_id))
    if source_event is None:
        errors.append(f"{path}.event_id must reference an event in the local artifact")
        return

    try:
        entry_quantity_delta = _decimal_from_string(entry_spec.get("quantity_delta"))
    except PaperAccountingLedgerValidationError:
        errors.append(f"{path}.quantity_delta must be a decimal string")
        return
    try:
        event_quantity_delta = _decimal_from_string(source_event.get("quantity_delta"))
    except PaperAccountingLedgerValidationError:
        errors.append(f"{path}.event_id source event quantity_delta must be a decimal string")
        return
    if entry_quantity_delta != event_quantity_delta:
        errors.append(f"{path}.quantity_delta must match the local artifact event quantity_delta")
    if entry_spec.get("asset_code") != source_event.get("asset_code"):
        errors.append(f"{path}.asset_code must match the local artifact event asset_code")
    if entry_spec.get("entry_type") != source_event.get("event_type"):
        errors.append(f"{path}.entry_type must match the local artifact event_type")


def _build_balance_summary(accounting_entries: list[Any]) -> list[dict[str, Any]]:
    totals: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))
    counts: dict[str, int] = defaultdict(int)
    for entry in accounting_entries:
        if not isinstance(entry, dict):
            continue
        asset_code = str(entry.get("asset_code"))
        try:
            quantity_delta = _decimal_from_string(entry.get("quantity_delta"))
        except PaperAccountingLedgerValidationError:
            continue
        totals[asset_code] += quantity_delta
        counts[asset_code] += 1
    return [
        {
            "asset_code": asset_code,
            "entry_count": counts[asset_code],
            "net_quantity_delta": _format_decimal(totals[asset_code]),
            "operator_review_status": OPERATOR_REVIEW_STATUS,
        }
        for asset_code in sorted(totals)
    ]


def _load_local_json_object(local_reference: str) -> dict[str, Any]:
    path = Path(_normalize_local_reference(local_reference))
    if not path.exists():
        raise PaperAccountingLedgerValidationError((f"local_reference does not exist: {local_reference}",))
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise PaperAccountingLedgerValidationError((f"local_reference must contain a JSON object: {local_reference}",))
    return payload


def _is_allowed_local_reference(local_reference: Any) -> bool:
    if not isinstance(local_reference, str) or not local_reference:
        return False
    normalized = _normalize_local_reference(local_reference)
    if "://" in normalized or normalized.startswith("/") or Path(normalized).is_absolute():
        return False
    parts = [part for part in normalized.split("/") if part]
    if ".." in parts:
        return False
    if any(normalized == prefix.rstrip("/") or normalized.startswith(prefix) for prefix in FORBIDDEN_LOCAL_REFERENCE_PREFIXES):
        return False
    return any(normalized.startswith(prefix) for prefix in ALLOWED_LOCAL_REFERENCE_PREFIXES)


def _normalize_local_reference(local_reference: str) -> str:
    return local_reference.replace("\\", "/")


def _decimal_from_string(value: Any) -> Decimal:
    if not isinstance(value, str) or not value:
        raise PaperAccountingLedgerValidationError(("value must be a decimal string",))
    try:
        return Decimal(value)
    except InvalidOperation as exc:
        raise PaperAccountingLedgerValidationError(("value must be a decimal string",)) from exc


def _format_decimal(value: Decimal) -> str:
    return f"{value.quantize(Decimal('0.01')):.2f}"


def _stable_digest(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()[:12]


def _require_keys(value: dict[str, Any], required_fields: set[str], path: str, errors: list[str]) -> None:
    missing = sorted(required_fields - set(value))
    if missing:
        errors.append(f"{path} missing required fields: {', '.join(missing)}")


def _find_forbidden_decision_terms(value: Any, path: str) -> list[str]:
    hits: list[str] = []
    if isinstance(value, dict):
        for key, nested_value in value.items():
            key_path = f"{path}.{key}"
            if _has_forbidden_token(str(key)):
                hits.append(f"forbidden scoring/action field detected at {key_path}")
            hits.extend(_find_forbidden_decision_terms(nested_value, key_path))
    elif isinstance(value, list):
        for index, nested_value in enumerate(value):
            hits.extend(_find_forbidden_decision_terms(nested_value, f"{path}[{index}]"))
    elif isinstance(value, str) and _has_forbidden_token(value):
        hits.append(f"forbidden scoring/action text detected at {path}")
    return hits


def _has_forbidden_token(value: str) -> bool:
    normalized = "".join(character if character.isalnum() else "_" for character in value.lower())
    tokens = {token for token in normalized.split("_") if token}
    return bool(tokens & FORBIDDEN_DECISION_TOKENS)


if __name__ == "__main__":
    raise SystemExit(main())
