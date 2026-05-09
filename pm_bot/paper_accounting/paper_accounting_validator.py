from __future__ import annotations

import argparse
import json
from collections import Counter
from copy import deepcopy
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from pm_bot.paper_accounting.paper_accounting_ledger import (
    ALLOWED_LOCAL_REFERENCE_PREFIXES,
    FORBIDDEN_DECISION_TOKENS,
    FORBIDDEN_LOCAL_REFERENCE_PREFIXES,
    LEDGER_CONTRACT_VERSION,
    LEDGER_ROW_STATE,
    LOCAL_ONLY_SAFETY_BOUNDARIES,
    OPERATOR_REVIEW_STATUS,
    SAMPLE_LEDGER_PATH,
    ValidationResult,
    validate_paper_accounting_ledger,
)

VALIDATION_CONTRACT_VERSION = "pmbot_paper_accounting_validation.v1"
VALIDATION_RUN_MODE = "local_paper_only_validation"
VALIDATION_ROW_STATE = "descriptive_paper_accounting_validation_record"
SAMPLE_VALIDATION_PATH = Path("pm_bot/paper_accounting/samples/paper_accounting_validation.fixture.json")
SAMPLE_OPERATOR_REPORT_PATH = Path("pm_bot/paper_accounting/samples/paper_accounting_validation.fixture.md")

REQUIRED_ACCOUNTING_ENTRY_FIELDS = {
    "asset_code",
    "entry_id",
    "entry_type",
    "event_id",
    "event_timestamp",
    "local_reference",
    "memo",
    "operator_review_label",
    "operator_review_status",
    "quantity_delta",
    "row_state",
    "source_artifact_id",
    "source_artifact_label",
    "source_artifact_role",
}
VALIDATION_CHECK_IDS = (
    "required_fields_present",
    "local_reference_boundary",
    "timestamp_utc_format",
    "quantity_delta_canonical",
    "operator_review_state",
    "source_inventory_reference",
)


class PaperAccountingValidationError(ValueError):
    def __init__(self, errors: tuple[str, ...]):
        super().__init__("; ".join(errors))
        self.errors = errors


def load_paper_accounting_ledger(path: str | Path) -> dict[str, Any]:
    ledger_path = Path(path)
    payload = json.loads(ledger_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise PaperAccountingValidationError(("paper accounting ledger must be a JSON object",))
    return payload


def validate_paper_accounting_records(ledger: Any) -> ValidationResult:
    errors: list[str] = []
    if not isinstance(ledger, dict):
        return ValidationResult(False, ("ledger must be an object",))

    ledger_validation = validate_paper_accounting_ledger(ledger)
    errors.extend(f"ledger: {error}" for error in ledger_validation.errors)

    accounting_entries = ledger.get("accounting_entries")
    if not isinstance(accounting_entries, list):
        errors.append("ledger.accounting_entries must be a list")
        return ValidationResult(False, tuple(errors))

    source_inventory = ledger.get("source_inventory")
    source_artifact_ids = (
        {row.get("artifact_id") for row in source_inventory if isinstance(row, dict)}
        if isinstance(source_inventory, list)
        else set()
    )
    entry_ids = Counter(
        entry.get("entry_id") for entry in accounting_entries if isinstance(entry, dict) and entry.get("entry_id")
    )

    for entry_index, entry in enumerate(accounting_entries):
        path = f"ledger.accounting_entries[{entry_index}]"
        if not isinstance(entry, dict):
            errors.append(f"{path} must be an object")
            continue
        _validate_accounting_entry(entry, path, source_artifact_ids, entry_ids, errors)

    return ValidationResult(not errors, tuple(errors))


def build_paper_accounting_validation(ledger: dict[str, Any]) -> dict[str, Any]:
    validation = validate_paper_accounting_records(ledger)
    if not validation.valid:
        raise PaperAccountingValidationError(validation.errors)

    accounting_entries = list(ledger["accounting_entries"])
    validation_rows = [_build_validation_row(entry) for entry in accounting_entries]
    validation_check_count = sum(row["check_count"] for row in validation_rows)
    failed_check_count = sum(row["failed_check_count"] for row in validation_rows)

    return {
        "account_context": deepcopy(ledger["account_context"]),
        "build_id": f"{ledger['build_id']}.paper_accounting_validation",
        "contract_version": VALIDATION_CONTRACT_VERSION,
        "errors": [],
        "ledger_build_id": ledger["build_id"],
        "ledger_contract_version": ledger["contract_version"],
        "ledger_id": ledger["ledger_id"],
        "local_only": True,
        "operator_review": {
            "required": True,
            "review_steps": [
                "Confirm every validation row maps to one local paper accounting entry.",
                "Confirm each local reference remains inside the paper accounting fixture or static sample boundary.",
                "Record any accounting disputes outside this validation artifact.",
            ],
            "status": OPERATOR_REVIEW_STATUS,
        },
        "operator_review_required": True,
        "record_validation_rows": validation_rows,
        "run_mode": VALIDATION_RUN_MODE,
        "safety_boundaries": dict(LOCAL_ONLY_SAFETY_BOUNDARIES),
        "summary_counts": {
            "accounting_entries": len(accounting_entries),
            "failed_checks": failed_check_count,
            "source_artifacts": len(ledger["source_inventory"]),
            "validation_checks": validation_check_count,
            "validation_rows": len(validation_rows),
            "warnings": 0,
        },
        "validation_id": f"{ledger['ledger_id']}.paper_accounting_validation",
        "warnings": [],
    }


def validate_paper_accounting_validation(validation_artifact: Any) -> ValidationResult:
    errors: list[str] = []
    if not isinstance(validation_artifact, dict):
        return ValidationResult(False, ("paper accounting validation artifact must be an object",))

    errors.extend(_find_forbidden_decision_terms(validation_artifact, "paper_accounting_validation"))
    required_fields = {
        "account_context",
        "build_id",
        "contract_version",
        "errors",
        "ledger_build_id",
        "ledger_contract_version",
        "ledger_id",
        "local_only",
        "operator_review",
        "operator_review_required",
        "record_validation_rows",
        "run_mode",
        "safety_boundaries",
        "summary_counts",
        "validation_id",
        "warnings",
    }
    _require_keys(validation_artifact, required_fields, "paper_accounting_validation", errors)
    if errors:
        return ValidationResult(False, tuple(errors))

    if validation_artifact["contract_version"] != VALIDATION_CONTRACT_VERSION:
        errors.append(f"paper_accounting_validation.contract_version must be {VALIDATION_CONTRACT_VERSION}")
    if validation_artifact["ledger_contract_version"] != LEDGER_CONTRACT_VERSION:
        errors.append(f"paper_accounting_validation.ledger_contract_version must be {LEDGER_CONTRACT_VERSION}")
    if validation_artifact["run_mode"] != VALIDATION_RUN_MODE:
        errors.append(f"paper_accounting_validation.run_mode must be {VALIDATION_RUN_MODE}")
    if validation_artifact["local_only"] is not True:
        errors.append("paper_accounting_validation.local_only must be true")
    if validation_artifact["operator_review_required"] is not True:
        errors.append("paper_accounting_validation.operator_review_required must be true")
    if validation_artifact["safety_boundaries"] != LOCAL_ONLY_SAFETY_BOUNDARIES:
        errors.append("paper_accounting_validation.safety_boundaries must match local-only safety boundaries")

    operator_review = validation_artifact["operator_review"]
    if not isinstance(operator_review, dict):
        errors.append("paper_accounting_validation.operator_review must be an object")
    elif operator_review.get("status") != OPERATOR_REVIEW_STATUS:
        errors.append(f"paper_accounting_validation.operator_review.status must be {OPERATOR_REVIEW_STATUS}")

    validation_rows = validation_artifact["record_validation_rows"]
    if not isinstance(validation_rows, list):
        errors.append("paper_accounting_validation.record_validation_rows must be a list")
        validation_rows = []

    total_checks = 0
    total_failed_checks = 0
    for row_index, row in enumerate(validation_rows):
        if not isinstance(row, dict):
            errors.append(f"paper_accounting_validation.record_validation_rows[{row_index}] must be an object")
            continue
        row_total, row_failed = _validate_validation_row(row, row_index, errors)
        total_checks += row_total
        total_failed_checks += row_failed

    summary_counts = validation_artifact["summary_counts"]
    if not isinstance(summary_counts, dict):
        errors.append("paper_accounting_validation.summary_counts must be an object")
    else:
        expected_counts = {
            "accounting_entries": len(validation_rows),
            "failed_checks": total_failed_checks,
            "source_artifacts": len(
                {
                    row.get("source_artifact_id")
                    for row in validation_rows
                    if isinstance(row, dict) and row.get("source_artifact_id")
                }
            ),
            "validation_checks": total_checks,
            "validation_rows": len(validation_rows),
            "warnings": len(validation_artifact["warnings"]) if isinstance(validation_artifact["warnings"], list) else 0,
        }
        if summary_counts != expected_counts:
            errors.append("paper_accounting_validation.summary_counts must match validation row totals")

    if not isinstance(validation_artifact["errors"], list):
        errors.append("paper_accounting_validation.errors must be a list")
    if not isinstance(validation_artifact["warnings"], list):
        errors.append("paper_accounting_validation.warnings must be a list")

    return ValidationResult(not errors, tuple(errors))


def build_operator_report(validation_artifact: dict[str, Any]) -> str:
    lines = [
        "# PMBOT Paper Accounting Validation",
        "",
        f"Validation ID: `{validation_artifact['validation_id']}`",
        f"Build ID: `{validation_artifact['build_id']}`",
        f"Ledger ID: `{validation_artifact['ledger_id']}`",
        f"Ledger build ID: `{validation_artifact['ledger_build_id']}`",
        f"Run mode: `{validation_artifact['run_mode']}`",
        f"Operator review: `{validation_artifact['operator_review']['status']}`",
        "",
        "## Summary",
        "",
        f"- Accounting entries: {validation_artifact['summary_counts']['accounting_entries']}",
        f"- Validation rows: {validation_artifact['summary_counts']['validation_rows']}",
        f"- Validation checks: {validation_artifact['summary_counts']['validation_checks']}",
        f"- Failed checks: {validation_artifact['summary_counts']['failed_checks']}",
        f"- Warnings: {validation_artifact['summary_counts']['warnings']}",
        "",
        "## Record Validation Rows",
        "",
    ]
    for row in validation_artifact["record_validation_rows"]:
        lines.append(
            f"- `{row['entry_id']}`: {row['check_count']} checks `{row['status']}` "
            f"for `{row['asset_code']}` delta `{row['quantity_delta']}`."
        )
    lines.extend(
        [
            "",
            "## Safety",
            "",
            "- Local fixture/static ledger input only.",
            "- Makes no network, LLM, external market API, wallet, order, transaction endpoint, or runtime calls.",
            "- Descriptive paper accounting validation only; it is not an approval record for execution.",
            "- Operator review remains required before using these records outside this local artifact.",
            "",
        ]
    )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a local-only PMBOT paper accounting validation artifact.")
    parser.add_argument("--ledger", default=str(SAMPLE_LEDGER_PATH), help="Path to the local paper accounting ledger JSON.")
    parser.add_argument("--output-validation", required=True, help="Path where the JSON validation artifact should be written.")
    parser.add_argument("--output-report", required=True, help="Path where the Markdown operator report should be written.")
    args = parser.parse_args(argv)

    ledger = load_paper_accounting_ledger(args.ledger)
    validation_artifact = build_paper_accounting_validation(ledger)
    artifact_validation = validate_paper_accounting_validation(validation_artifact)
    if not artifact_validation.valid:
        raise PaperAccountingValidationError(artifact_validation.errors)

    output_validation = Path(args.output_validation)
    output_report = Path(args.output_report)
    output_validation.parent.mkdir(parents=True, exist_ok=True)
    output_report.parent.mkdir(parents=True, exist_ok=True)
    output_validation.write_text(json.dumps(validation_artifact, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    output_report.write_text(build_operator_report(validation_artifact), encoding="utf-8")
    return 0


def _validate_accounting_entry(
    entry: dict[str, Any],
    path: str,
    source_artifact_ids: set[Any],
    entry_ids: Counter[Any],
    errors: list[str],
) -> None:
    _require_keys(entry, REQUIRED_ACCOUNTING_ENTRY_FIELDS, path, errors)
    if REQUIRED_ACCOUNTING_ENTRY_FIELDS - set(entry):
        return

    for field in sorted(REQUIRED_ACCOUNTING_ENTRY_FIELDS):
        if field == "quantity_delta":
            continue
        if not isinstance(entry.get(field), str) or not entry.get(field):
            errors.append(f"{path}.{field} must be a non-empty string")

    entry_id = entry.get("entry_id")
    if entry_ids[entry_id] > 1:
        errors.append(f"{path}.entry_id must be unique within the paper accounting ledger")
    if not _is_allowed_local_reference(entry.get("local_reference")):
        errors.append(f"{path}.local_reference must stay under paper accounting allowed local paths")
    if not _is_utc_timestamp(entry.get("event_timestamp")):
        errors.append(f"{path}.event_timestamp must be an ISO-8601 UTC timestamp ending in Z")
    try:
        quantity_delta = _decimal_from_string(entry.get("quantity_delta"))
    except PaperAccountingValidationError:
        errors.append(f"{path}.quantity_delta must be a decimal string")
    else:
        if _format_decimal(quantity_delta) != entry.get("quantity_delta"):
            errors.append(f"{path}.quantity_delta must use canonical two-decimal formatting")
    if entry.get("operator_review_status") != OPERATOR_REVIEW_STATUS:
        errors.append(f"{path}.operator_review_status must be {OPERATOR_REVIEW_STATUS}")
    if entry.get("row_state") != LEDGER_ROW_STATE:
        errors.append(f"{path}.row_state must be {LEDGER_ROW_STATE}")
    if entry.get("source_artifact_id") not in source_artifact_ids:
        errors.append(f"{path}.source_artifact_id must match a source_inventory artifact_id")


def _build_validation_row(entry: dict[str, Any]) -> dict[str, Any]:
    checks = [
        _passed_check("required_fields_present", f"{len(REQUIRED_ACCOUNTING_ENTRY_FIELDS)}/{len(REQUIRED_ACCOUNTING_ENTRY_FIELDS)}"),
        _passed_check("local_reference_boundary", entry["local_reference"]),
        _passed_check("timestamp_utc_format", entry["event_timestamp"]),
        _passed_check("quantity_delta_canonical", entry["quantity_delta"]),
        _passed_check("operator_review_state", f"{entry['operator_review_status']}|{entry['row_state']}"),
        _passed_check("source_inventory_reference", entry["source_artifact_id"]),
    ]
    return {
        "asset_code": entry["asset_code"],
        "check_count": len(checks),
        "checks": checks,
        "entry_id": entry["entry_id"],
        "entry_type": entry["entry_type"],
        "event_id": entry["event_id"],
        "event_timestamp": entry["event_timestamp"],
        "failed_check_count": 0,
        "local_reference": entry["local_reference"],
        "operator_review_status": OPERATOR_REVIEW_STATUS,
        "quantity_delta": entry["quantity_delta"],
        "runner_state": VALIDATION_ROW_STATE,
        "source_artifact_id": entry["source_artifact_id"],
        "status": "passed",
        "validation_row_id": f"{entry['entry_id']}.paper_accounting_validation",
    }


def _passed_check(check_id: str, observed_value: str) -> dict[str, Any]:
    return {
        "check_id": check_id,
        "operator_review_status": OPERATOR_REVIEW_STATUS,
        "observed_value": observed_value,
        "status": "passed",
    }


def _validate_validation_row(row: dict[str, Any], row_index: int, errors: list[str]) -> tuple[int, int]:
    path = f"paper_accounting_validation.record_validation_rows[{row_index}]"
    required_fields = {
        "asset_code",
        "check_count",
        "checks",
        "entry_id",
        "entry_type",
        "event_id",
        "event_timestamp",
        "failed_check_count",
        "local_reference",
        "operator_review_status",
        "quantity_delta",
        "runner_state",
        "source_artifact_id",
        "status",
        "validation_row_id",
    }
    _require_keys(row, required_fields, path, errors)
    if required_fields - set(row):
        return (0, 0)

    if row.get("operator_review_status") != OPERATOR_REVIEW_STATUS:
        errors.append(f"{path}.operator_review_status must be {OPERATOR_REVIEW_STATUS}")
    if row.get("runner_state") != VALIDATION_ROW_STATE:
        errors.append(f"{path}.runner_state must be {VALIDATION_ROW_STATE}")
    if row.get("status") != "passed":
        errors.append(f"{path}.status must be passed")
    if row.get("validation_row_id") != f"{row.get('entry_id')}.paper_accounting_validation":
        errors.append(f"{path}.validation_row_id must be derived from entry_id")
    if not _is_allowed_local_reference(row.get("local_reference")):
        errors.append(f"{path}.local_reference must stay under paper accounting allowed local paths")
    try:
        quantity_delta = _decimal_from_string(row.get("quantity_delta"))
    except PaperAccountingValidationError:
        errors.append(f"{path}.quantity_delta must be a decimal string")
    else:
        if _format_decimal(quantity_delta) != row.get("quantity_delta"):
            errors.append(f"{path}.quantity_delta must use canonical two-decimal formatting")
    if not _is_utc_timestamp(row.get("event_timestamp")):
        errors.append(f"{path}.event_timestamp must be an ISO-8601 UTC timestamp ending in Z")

    checks = row.get("checks")
    if not isinstance(checks, list):
        errors.append(f"{path}.checks must be a list")
        checks = []
    observed_check_ids: list[str] = []
    failed_checks = 0
    for check_index, check in enumerate(checks):
        check_path = f"{path}.checks[{check_index}]"
        if not isinstance(check, dict):
            errors.append(f"{check_path} must be an object")
            continue
        _require_keys(check, {"check_id", "operator_review_status", "observed_value", "status"}, check_path, errors)
        observed_check_ids.append(str(check.get("check_id")))
        if check.get("operator_review_status") != OPERATOR_REVIEW_STATUS:
            errors.append(f"{check_path}.operator_review_status must be {OPERATOR_REVIEW_STATUS}")
        if check.get("status") != "passed":
            errors.append(f"{check_path}.status must be passed")
            failed_checks += 1
        if not isinstance(check.get("observed_value"), str) or not check.get("observed_value"):
            errors.append(f"{check_path}.observed_value must be a non-empty string")

    if tuple(observed_check_ids) != VALIDATION_CHECK_IDS:
        errors.append(f"{path}.checks must use the expected paper accounting validation check order")
    if row.get("check_count") != len(checks):
        errors.append(f"{path}.check_count must match checks length")
    if row.get("failed_check_count") != failed_checks:
        errors.append(f"{path}.failed_check_count must match failed check total")
    return (len(checks), failed_checks)


def _require_keys(value: dict[str, Any], required_fields: set[str], path: str, errors: list[str]) -> None:
    missing = sorted(required_fields - set(value))
    if missing:
        errors.append(f"{path} missing required fields: {', '.join(missing)}")


def _is_allowed_local_reference(local_reference: Any) -> bool:
    if not isinstance(local_reference, str) or not local_reference:
        return False
    normalized = local_reference.replace("\\", "/")
    if "://" in normalized or normalized.startswith("/") or Path(normalized).is_absolute():
        return False
    parts = [part for part in normalized.split("/") if part]
    if ".." in parts:
        return False
    if any(normalized == prefix.rstrip("/") or normalized.startswith(prefix) for prefix in FORBIDDEN_LOCAL_REFERENCE_PREFIXES):
        return False
    return any(normalized.startswith(prefix) for prefix in ALLOWED_LOCAL_REFERENCE_PREFIXES)


def _is_utc_timestamp(value: Any) -> bool:
    if not isinstance(value, str) or not value.endswith("Z"):
        return False
    try:
        datetime.fromisoformat(value.removesuffix("Z") + "+00:00")
    except ValueError:
        return False
    return True


def _decimal_from_string(value: Any) -> Decimal:
    if not isinstance(value, str) or not value:
        raise PaperAccountingValidationError(("value must be a decimal string",))
    try:
        return Decimal(value)
    except InvalidOperation as exc:
        raise PaperAccountingValidationError(("value must be a decimal string",)) from exc


def _format_decimal(value: Decimal) -> str:
    return f"{value.quantize(Decimal('0.01')):.2f}"


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
