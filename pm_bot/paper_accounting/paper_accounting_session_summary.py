from __future__ import annotations

import argparse
import json
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
    LOCAL_ONLY_SAFETY_BOUNDARIES,
    OPERATOR_REVIEW_STATUS,
    SAMPLE_LEDGER_PATH,
    ValidationResult,
    validate_paper_accounting_ledger,
)
from pm_bot.paper_accounting.paper_accounting_validator import (
    SAMPLE_VALIDATION_PATH,
    VALIDATION_CONTRACT_VERSION,
    validate_paper_accounting_validation,
)

SESSION_SUMMARY_CONTRACT_VERSION = "pmbot_paper_accounting_session_summary.v1"
SESSION_SUMMARY_RUN_MODE = "local_paper_only_session_summary"
SESSION_SUMMARY_ROW_STATE = "descriptive_paper_accounting_session_summary_record"
SAMPLE_SESSION_SUMMARY_PATH = Path("pm_bot/paper_accounting/samples/paper_accounting_session_summary.fixture.json")
SAMPLE_OPERATOR_REPORT_PATH = Path("pm_bot/paper_accounting/samples/paper_accounting_session_summary.fixture.md")


class PaperAccountingSessionSummaryError(ValueError):
    def __init__(self, errors: tuple[str, ...]):
        super().__init__("; ".join(errors))
        self.errors = errors


def load_paper_accounting_artifact(path: str | Path) -> dict[str, Any]:
    artifact_path = Path(path)
    payload = json.loads(artifact_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise PaperAccountingSessionSummaryError(("paper accounting artifact must be a JSON object",))
    return payload


def validate_paper_accounting_session_inputs(
    ledger: Any,
    validation_artifact: Any,
    ledger_reference: str | Path = SAMPLE_LEDGER_PATH,
    validation_reference: str | Path = SAMPLE_VALIDATION_PATH,
) -> ValidationResult:
    errors: list[str] = []
    if not isinstance(ledger, dict):
        return ValidationResult(False, ("ledger must be an object",))
    if not isinstance(validation_artifact, dict):
        return ValidationResult(False, ("paper accounting validation artifact must be an object",))

    ledger_validation = validate_paper_accounting_ledger(ledger)
    errors.extend(f"ledger: {error}" for error in ledger_validation.errors)
    validation_result = validate_paper_accounting_validation(validation_artifact)
    errors.extend(f"validation: {error}" for error in validation_result.errors)

    ledger_ref = _normalize_local_reference(str(ledger_reference))
    validation_ref = _normalize_local_reference(str(validation_reference))
    if not _is_allowed_local_reference(ledger_ref):
        errors.append("ledger_reference must stay under paper accounting allowed local paths")
    if not _is_allowed_local_reference(validation_ref):
        errors.append("validation_reference must stay under paper accounting allowed local paths")

    if validation_artifact.get("ledger_id") != ledger.get("ledger_id"):
        errors.append("validation.ledger_id must match ledger.ledger_id")
    if validation_artifact.get("ledger_build_id") != ledger.get("build_id"):
        errors.append("validation.ledger_build_id must match ledger.build_id")
    if validation_artifact.get("ledger_contract_version") != ledger.get("contract_version"):
        errors.append("validation.ledger_contract_version must match ledger.contract_version")

    accounting_entries = ledger.get("accounting_entries")
    validation_rows = validation_artifact.get("record_validation_rows")
    if isinstance(accounting_entries, list) and isinstance(validation_rows, list):
        rows_by_entry_id = {
            row.get("entry_id"): row for row in validation_rows if isinstance(row, dict) and row.get("entry_id")
        }
        if len(rows_by_entry_id) != len(validation_rows):
            errors.append("validation.record_validation_rows must have unique entry_id values")
        for entry_index, entry in enumerate(accounting_entries):
            path = f"ledger.accounting_entries[{entry_index}]"
            if not isinstance(entry, dict):
                continue
            row = rows_by_entry_id.get(entry.get("entry_id"))
            if row is None:
                errors.append(f"{path}.entry_id must have a matching validation row")
                continue
            _validate_entry_matches_validation_row(entry, row, path, errors)

    return ValidationResult(not errors, tuple(errors))


def build_paper_accounting_session_summary(
    ledger: dict[str, Any],
    validation_artifact: dict[str, Any],
    ledger_reference: str | Path = SAMPLE_LEDGER_PATH,
    validation_reference: str | Path = SAMPLE_VALIDATION_PATH,
) -> dict[str, Any]:
    validation = validate_paper_accounting_session_inputs(
        ledger,
        validation_artifact,
        ledger_reference,
        validation_reference,
    )
    if not validation.valid:
        raise PaperAccountingSessionSummaryError(validation.errors)

    rows_by_entry_id = {
        row["entry_id"]: row for row in validation_artifact["record_validation_rows"] if isinstance(row, dict)
    }
    session_rows = [
        _build_session_review_row(entry, rows_by_entry_id[entry["entry_id"]])
        for entry in ledger["accounting_entries"]
    ]
    failed_validation_checks = sum(row["validation_failed_check_count"] for row in session_rows)

    local_input_artifacts = [
        {
            "artifact_id": ledger["ledger_id"],
            "artifact_role": "paper_accounting_ledger",
            "build_id": ledger["build_id"],
            "contract_version": ledger["contract_version"],
            "local_reference": _normalize_local_reference(str(ledger_reference)),
            "operator_review_status": OPERATOR_REVIEW_STATUS,
            "runner_state": SESSION_SUMMARY_ROW_STATE,
        },
        {
            "artifact_id": validation_artifact["validation_id"],
            "artifact_role": "paper_accounting_validation",
            "build_id": validation_artifact["build_id"],
            "contract_version": validation_artifact["contract_version"],
            "local_reference": _normalize_local_reference(str(validation_reference)),
            "operator_review_status": OPERATOR_REVIEW_STATUS,
            "runner_state": SESSION_SUMMARY_ROW_STATE,
        },
    ]

    return {
        "account_context": deepcopy(ledger["account_context"]),
        "balance_summary": deepcopy(ledger["balance_summary"]),
        "build_id": f"{ledger['build_id']}.paper_accounting_session_summary",
        "contract_version": SESSION_SUMMARY_CONTRACT_VERSION,
        "errors": [],
        "ledger_build_id": ledger["build_id"],
        "ledger_contract_version": ledger["contract_version"],
        "ledger_id": ledger["ledger_id"],
        "local_input_artifacts": local_input_artifacts,
        "local_only": True,
        "operator_review": {
            "required": True,
            "review_steps": [
                "Confirm ledger and validation build identifiers match the local samples.",
                "Confirm session rows mirror the accounting entries and validation rows.",
                "Record accounting disputes outside this session summary artifact.",
            ],
            "status": OPERATOR_REVIEW_STATUS,
        },
        "operator_review_required": True,
        "run_mode": SESSION_SUMMARY_RUN_MODE,
        "safety_boundaries": dict(LOCAL_ONLY_SAFETY_BOUNDARIES),
        "session_id": f"{ledger['ledger_id']}.paper_accounting_session_summary",
        "session_review_rows": session_rows,
        "summary_counts": {
            "accounting_entries": len(session_rows),
            "assets": len(ledger["balance_summary"]),
            "failed_validation_checks": failed_validation_checks,
            "input_artifacts": len(local_input_artifacts),
            "source_artifacts": len({row["source_artifact_id"] for row in session_rows}),
            "validation_rows": len(validation_artifact["record_validation_rows"]),
            "warnings": 0,
        },
        "validation_build_id": validation_artifact["build_id"],
        "validation_contract_version": validation_artifact["contract_version"],
        "validation_id": validation_artifact["validation_id"],
        "warnings": [],
    }


def validate_paper_accounting_session_summary(summary: Any) -> ValidationResult:
    errors: list[str] = []
    if not isinstance(summary, dict):
        return ValidationResult(False, ("paper accounting session summary must be an object",))

    errors.extend(_find_forbidden_decision_terms(summary, "paper_accounting_session_summary"))
    required_fields = {
        "account_context",
        "balance_summary",
        "build_id",
        "contract_version",
        "errors",
        "ledger_build_id",
        "ledger_contract_version",
        "ledger_id",
        "local_input_artifacts",
        "local_only",
        "operator_review",
        "operator_review_required",
        "run_mode",
        "safety_boundaries",
        "session_id",
        "session_review_rows",
        "summary_counts",
        "validation_build_id",
        "validation_contract_version",
        "validation_id",
        "warnings",
    }
    _require_keys(summary, required_fields, "paper_accounting_session_summary", errors)
    if errors:
        return ValidationResult(False, tuple(errors))

    if summary["contract_version"] != SESSION_SUMMARY_CONTRACT_VERSION:
        errors.append(f"paper_accounting_session_summary.contract_version must be {SESSION_SUMMARY_CONTRACT_VERSION}")
    if summary["ledger_contract_version"] != LEDGER_CONTRACT_VERSION:
        errors.append(f"paper_accounting_session_summary.ledger_contract_version must be {LEDGER_CONTRACT_VERSION}")
    if summary["validation_contract_version"] != VALIDATION_CONTRACT_VERSION:
        errors.append(
            f"paper_accounting_session_summary.validation_contract_version must be {VALIDATION_CONTRACT_VERSION}"
        )
    if summary["run_mode"] != SESSION_SUMMARY_RUN_MODE:
        errors.append(f"paper_accounting_session_summary.run_mode must be {SESSION_SUMMARY_RUN_MODE}")
    if summary["local_only"] is not True:
        errors.append("paper_accounting_session_summary.local_only must be true")
    if summary["operator_review_required"] is not True:
        errors.append("paper_accounting_session_summary.operator_review_required must be true")
    if summary["safety_boundaries"] != LOCAL_ONLY_SAFETY_BOUNDARIES:
        errors.append("paper_accounting_session_summary.safety_boundaries must match local-only safety boundaries")
    if summary["session_id"] != f"{summary['ledger_id']}.paper_accounting_session_summary":
        errors.append("paper_accounting_session_summary.session_id must be derived from ledger_id")
    if summary["build_id"] != f"{summary['ledger_build_id']}.paper_accounting_session_summary":
        errors.append("paper_accounting_session_summary.build_id must be derived from ledger_build_id")

    operator_review = summary["operator_review"]
    if not isinstance(operator_review, dict):
        errors.append("paper_accounting_session_summary.operator_review must be an object")
    elif operator_review.get("status") != OPERATOR_REVIEW_STATUS:
        errors.append(f"paper_accounting_session_summary.operator_review.status must be {OPERATOR_REVIEW_STATUS}")

    input_artifacts = summary["local_input_artifacts"]
    if not isinstance(input_artifacts, list):
        errors.append("paper_accounting_session_summary.local_input_artifacts must be a list")
        input_artifacts = []
    for artifact_index, artifact in enumerate(input_artifacts):
        _validate_local_input_artifact(artifact, artifact_index, errors)
    observed_roles = tuple(
        artifact.get("artifact_role") for artifact in input_artifacts if isinstance(artifact, dict)
    )
    if observed_roles != ("paper_accounting_ledger", "paper_accounting_validation"):
        errors.append("paper_accounting_session_summary.local_input_artifacts must list ledger then validation")

    balance_summary = summary["balance_summary"]
    if not isinstance(balance_summary, list):
        errors.append("paper_accounting_session_summary.balance_summary must be a list")
        balance_summary = []

    session_rows = summary["session_review_rows"]
    if not isinstance(session_rows, list):
        errors.append("paper_accounting_session_summary.session_review_rows must be a list")
        session_rows = []

    failed_validation_checks = 0
    for row_index, row in enumerate(session_rows):
        failed_validation_checks += _validate_session_review_row(row, row_index, errors)

    summary_counts = summary["summary_counts"]
    if not isinstance(summary_counts, dict):
        errors.append("paper_accounting_session_summary.summary_counts must be an object")
    else:
        expected_counts = {
            "accounting_entries": len(session_rows),
            "assets": len(balance_summary),
            "failed_validation_checks": failed_validation_checks,
            "input_artifacts": len(input_artifacts),
            "source_artifacts": len(
                {
                    row.get("source_artifact_id")
                    for row in session_rows
                    if isinstance(row, dict) and row.get("source_artifact_id")
                }
            ),
            "validation_rows": len(session_rows),
            "warnings": len(summary["warnings"]) if isinstance(summary["warnings"], list) else 0,
        }
        if summary_counts != expected_counts:
            errors.append("paper_accounting_session_summary.summary_counts must match session row totals")

    if not isinstance(summary["errors"], list):
        errors.append("paper_accounting_session_summary.errors must be a list")
    if not isinstance(summary["warnings"], list):
        errors.append("paper_accounting_session_summary.warnings must be a list")

    return ValidationResult(not errors, tuple(errors))


def build_operator_report(summary: dict[str, Any]) -> str:
    lines = [
        "# PMBOT Paper Accounting Session Summary",
        "",
        f"Session ID: `{summary['session_id']}`",
        f"Build ID: `{summary['build_id']}`",
        f"Ledger ID: `{summary['ledger_id']}`",
        f"Ledger build ID: `{summary['ledger_build_id']}`",
        f"Validation ID: `{summary['validation_id']}`",
        f"Validation build ID: `{summary['validation_build_id']}`",
        f"Run mode: `{summary['run_mode']}`",
        f"Operator review: `{summary['operator_review']['status']}`",
        "",
        "## Summary",
        "",
        f"- Accounting entries: {summary['summary_counts']['accounting_entries']}",
        f"- Input artifacts: {summary['summary_counts']['input_artifacts']}",
        f"- Validation rows: {summary['summary_counts']['validation_rows']}",
        f"- Failed validation checks: {summary['summary_counts']['failed_validation_checks']}",
        f"- Warnings: {summary['summary_counts']['warnings']}",
        "",
        "## Balance Summary",
        "",
    ]
    for balance in summary["balance_summary"]:
        lines.append(
            f"- `{balance['asset_code']}` net quantity delta `{balance['net_quantity_delta']}` "
            f"from {balance['entry_count']} entries."
        )
    lines.extend(["", "## Session Review Rows", ""])
    for row in summary["session_review_rows"]:
        lines.append(
            f"- `{row['entry_id']}`: `{row['asset_code']}` delta `{row['ledger_quantity_delta']}` "
            f"with validation row `{row['validation_status']}`."
        )
    lines.extend(
        [
            "",
            "## Safety",
            "",
            "- Local fixture/static ledger and validation inputs only.",
            "- Makes no network, LLM, external market API, wallet, order, transaction endpoint, or runtime calls.",
            "- Descriptive paper accounting session summary only; it is not an approval record for execution.",
            "- Operator review remains required before using these records outside this local artifact.",
            "",
        ]
    )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a local-only PMBOT paper accounting session summary.")
    parser.add_argument("--ledger", default=str(SAMPLE_LEDGER_PATH), help="Path to the local paper accounting ledger JSON.")
    parser.add_argument(
        "--validation",
        default=str(SAMPLE_VALIDATION_PATH),
        help="Path to the local paper accounting validation JSON.",
    )
    parser.add_argument("--output-summary", required=True, help="Path where the JSON session summary should be written.")
    parser.add_argument("--output-report", required=True, help="Path where the Markdown operator report should be written.")
    args = parser.parse_args(argv)

    ledger = load_paper_accounting_artifact(args.ledger)
    validation_artifact = load_paper_accounting_artifact(args.validation)
    summary = build_paper_accounting_session_summary(
        ledger,
        validation_artifact,
        args.ledger,
        args.validation,
    )
    summary_validation = validate_paper_accounting_session_summary(summary)
    if not summary_validation.valid:
        raise PaperAccountingSessionSummaryError(summary_validation.errors)

    output_summary = Path(args.output_summary)
    output_report = Path(args.output_report)
    output_summary.parent.mkdir(parents=True, exist_ok=True)
    output_report.parent.mkdir(parents=True, exist_ok=True)
    output_summary.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    output_report.write_text(build_operator_report(summary), encoding="utf-8")
    return 0


def _build_session_review_row(entry: dict[str, Any], validation_row: dict[str, Any]) -> dict[str, Any]:
    return {
        "asset_code": entry["asset_code"],
        "entry_id": entry["entry_id"],
        "entry_type": entry["entry_type"],
        "event_id": entry["event_id"],
        "event_timestamp": entry["event_timestamp"],
        "ledger_quantity_delta": entry["quantity_delta"],
        "local_reference": entry["local_reference"],
        "operator_review_label": entry["operator_review_label"],
        "operator_review_status": OPERATOR_REVIEW_STATUS,
        "runner_state": SESSION_SUMMARY_ROW_STATE,
        "source_artifact_id": entry["source_artifact_id"],
        "validation_check_count": validation_row["check_count"],
        "validation_failed_check_count": validation_row["failed_check_count"],
        "validation_row_id": validation_row["validation_row_id"],
        "validation_status": validation_row["status"],
    }


def _validate_entry_matches_validation_row(
    entry: dict[str, Any],
    row: dict[str, Any],
    path: str,
    errors: list[str],
) -> None:
    field_pairs = (
        ("entry_id", "entry_id"),
        ("event_id", "event_id"),
        ("asset_code", "asset_code"),
        ("quantity_delta", "quantity_delta"),
        ("local_reference", "local_reference"),
        ("source_artifact_id", "source_artifact_id"),
    )
    for entry_field, row_field in field_pairs:
        if entry.get(entry_field) != row.get(row_field):
            errors.append(f"{path}.{entry_field} must match validation row {row_field}")


def _validate_local_input_artifact(artifact: Any, artifact_index: int, errors: list[str]) -> None:
    path = f"paper_accounting_session_summary.local_input_artifacts[{artifact_index}]"
    if not isinstance(artifact, dict):
        errors.append(f"{path} must be an object")
        return
    required_fields = {
        "artifact_id",
        "artifact_role",
        "build_id",
        "contract_version",
        "local_reference",
        "operator_review_status",
        "runner_state",
    }
    _require_keys(artifact, required_fields, path, errors)
    if required_fields - set(artifact):
        return
    if not _is_allowed_local_reference(artifact.get("local_reference")):
        errors.append(f"{path}.local_reference must stay under paper accounting allowed local paths")
    if artifact.get("operator_review_status") != OPERATOR_REVIEW_STATUS:
        errors.append(f"{path}.operator_review_status must be {OPERATOR_REVIEW_STATUS}")
    if artifact.get("runner_state") != SESSION_SUMMARY_ROW_STATE:
        errors.append(f"{path}.runner_state must be {SESSION_SUMMARY_ROW_STATE}")


def _validate_session_review_row(row: Any, row_index: int, errors: list[str]) -> int:
    path = f"paper_accounting_session_summary.session_review_rows[{row_index}]"
    if not isinstance(row, dict):
        errors.append(f"{path} must be an object")
        return 0
    required_fields = {
        "asset_code",
        "entry_id",
        "entry_type",
        "event_id",
        "event_timestamp",
        "ledger_quantity_delta",
        "local_reference",
        "operator_review_label",
        "operator_review_status",
        "runner_state",
        "source_artifact_id",
        "validation_check_count",
        "validation_failed_check_count",
        "validation_row_id",
        "validation_status",
    }
    _require_keys(row, required_fields, path, errors)
    if required_fields - set(row):
        return 0

    for field in sorted(required_fields - {"validation_check_count", "validation_failed_check_count"}):
        if not isinstance(row.get(field), str) or not row.get(field):
            errors.append(f"{path}.{field} must be a non-empty string")
    if not _is_allowed_local_reference(row.get("local_reference")):
        errors.append(f"{path}.local_reference must stay under paper accounting allowed local paths")
    if row.get("operator_review_status") != OPERATOR_REVIEW_STATUS:
        errors.append(f"{path}.operator_review_status must be {OPERATOR_REVIEW_STATUS}")
    if row.get("runner_state") != SESSION_SUMMARY_ROW_STATE:
        errors.append(f"{path}.runner_state must be {SESSION_SUMMARY_ROW_STATE}")
    if row.get("validation_status") != "passed":
        errors.append(f"{path}.validation_status must be passed")
    if row.get("validation_row_id") != f"{row.get('entry_id')}.paper_accounting_validation":
        errors.append(f"{path}.validation_row_id must be derived from entry_id")
    try:
        quantity_delta = _decimal_from_string(row.get("ledger_quantity_delta"))
    except PaperAccountingSessionSummaryError:
        errors.append(f"{path}.ledger_quantity_delta must be a decimal string")
    else:
        if _format_decimal(quantity_delta) != row.get("ledger_quantity_delta"):
            errors.append(f"{path}.ledger_quantity_delta must use canonical two-decimal formatting")
    if not _is_utc_timestamp(row.get("event_timestamp")):
        errors.append(f"{path}.event_timestamp must be an ISO-8601 UTC timestamp ending in Z")

    if not isinstance(row.get("validation_check_count"), int) or row["validation_check_count"] < 0:
        errors.append(f"{path}.validation_check_count must be a non-negative integer")
    failed_count = row.get("validation_failed_check_count")
    if not isinstance(failed_count, int) or failed_count < 0:
        errors.append(f"{path}.validation_failed_check_count must be a non-negative integer")
        return 0
    return failed_count


def _require_keys(value: dict[str, Any], required_fields: set[str], path: str, errors: list[str]) -> None:
    missing = sorted(required_fields - set(value))
    if missing:
        errors.append(f"{path} missing required fields: {', '.join(missing)}")


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
        raise PaperAccountingSessionSummaryError(("value must be a decimal string",))
    try:
        return Decimal(value)
    except InvalidOperation as exc:
        raise PaperAccountingSessionSummaryError(("value must be a decimal string",)) from exc


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
