from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from pm_bot.source_quality.unified_source_quality_ledger import (
    EXPECTED_LEDGER_SAFETY_BOUNDARIES,
    OPERATOR_REVIEW_STATUS,
    SourceQualityLedgerValidation,
    SourceQualityLedgerValidationError,
    _canonical_json,
    _find_forbidden_decision_terms,
    _is_non_empty_string_list,
    _is_string_list,
    _load_json,
    _normalize_reference,
    _validate_local_reference,
    _validate_operator_review_block,
    _write_json,
    validate_unified_source_quality_ledger,
)

REPORT_SUMMARY_CONTRACT_VERSION = "pmbot_source_quality_report_summary.v1"
REPORT_SUMMARY_RUN_MODE = "local_source_quality_report_summary"
REPORT_SUMMARY_SCOPE = "source_quality_report_summary"
REPORT_SUMMARY_ROW_STATE = "descriptive_source_quality_report_summary"
REPORT_SUMMARY_BUILD_SUFFIX = "source_quality_report_summary"
SAMPLE_REPORT_SUMMARY_PATH = "pm_bot/source_quality/samples/source_quality_report_summary.fixture.json"
SAMPLE_OPERATOR_REPORT_PATH = "pm_bot/source_quality/samples/source_quality_report_summary.fixture.md"


def load_source_quality_ledger(path: str | Path) -> dict[str, Any]:
    reference = str(path)
    errors = _validate_local_reference(reference)
    if errors:
        raise SourceQualityLedgerValidationError(tuple(errors))
    return _load_json(Path(_normalize_reference(reference)))


def build_source_quality_report_summary(ledger: dict[str, Any]) -> dict[str, Any]:
    validation = validate_unified_source_quality_ledger(ledger)
    if not validation.valid:
        raise SourceQualityLedgerValidationError(validation.errors)

    report_rows = [_build_report_row(row) for row in ledger["source_quality_rows"]]
    operator_steps = list(ledger["operator_review"]["steps"])
    warnings = list(ledger["warnings"])

    return {
        "build_id": f"{ledger['build_id']}.{REPORT_SUMMARY_BUILD_SUFFIX}",
        "contract_version": REPORT_SUMMARY_CONTRACT_VERSION,
        "errors": [],
        "ledger_build_id": ledger["build_id"],
        "ledger_id": ledger["ledger_id"],
        "local_only": True,
        "operator_review": {
            "status": OPERATOR_REVIEW_STATUS,
            "steps": operator_steps,
        },
        "operator_review_required": True,
        "report_summary_id": f"{ledger['ledger_id']}.{REPORT_SUMMARY_SCOPE}",
        "report_summary_rows": report_rows,
        "run_mode": REPORT_SUMMARY_RUN_MODE,
        "safety_boundaries": dict(EXPECTED_LEDGER_SAFETY_BOUNDARIES),
        "scope": REPORT_SUMMARY_SCOPE,
        "summary_counts": _summary_counts(report_rows, operator_steps, warnings),
        "warnings": warnings,
    }


def validate_source_quality_report_summary(summary: dict[str, Any]) -> SourceQualityLedgerValidation:
    errors: list[str] = []
    if not isinstance(summary, dict):
        return SourceQualityLedgerValidation(valid=False, errors=("summary must be an object",))

    required_fields = (
        "build_id",
        "contract_version",
        "errors",
        "ledger_build_id",
        "ledger_id",
        "local_only",
        "operator_review",
        "operator_review_required",
        "report_summary_id",
        "report_summary_rows",
        "run_mode",
        "safety_boundaries",
        "scope",
        "summary_counts",
        "warnings",
    )
    for field in required_fields:
        if field not in summary:
            errors.append(f"missing required report summary field: {field}")

    if summary.get("contract_version") != REPORT_SUMMARY_CONTRACT_VERSION:
        errors.append(f"contract_version must be {REPORT_SUMMARY_CONTRACT_VERSION}")
    if summary.get("scope") != REPORT_SUMMARY_SCOPE:
        errors.append(f"scope must be {REPORT_SUMMARY_SCOPE}")
    if summary.get("run_mode") != REPORT_SUMMARY_RUN_MODE:
        errors.append(f"run_mode must be {REPORT_SUMMARY_RUN_MODE}")
    if summary.get("local_only") is not True:
        errors.append("local_only must be true")
    if summary.get("operator_review_required") is not True:
        errors.append("operator_review_required must be true")
    if summary.get("errors") != []:
        errors.append("errors must be an empty list")
    if not _is_string_list(summary.get("warnings")):
        errors.append("warnings must be a list of strings")
    if summary.get("safety_boundaries") != EXPECTED_LEDGER_SAFETY_BOUNDARIES:
        errors.append("safety_boundaries must match the local-only source quality boundary")

    ledger_id = summary.get("ledger_id")
    ledger_build_id = summary.get("ledger_build_id")
    build_id = summary.get("build_id")
    report_summary_id = summary.get("report_summary_id")
    if not isinstance(ledger_id, str) or not ledger_id:
        errors.append("ledger_id must be a non-empty string")
    if not isinstance(ledger_build_id, str) or not ledger_build_id:
        errors.append("ledger_build_id must be a non-empty string")
    elif build_id != f"{ledger_build_id}.{REPORT_SUMMARY_BUILD_SUFFIX}":
        errors.append("build_id must be derived from ledger_build_id and report summary suffix")
    if isinstance(ledger_id, str) and ledger_id and report_summary_id != f"{ledger_id}.{REPORT_SUMMARY_SCOPE}":
        errors.append("report_summary_id must be derived from ledger_id and report summary scope")

    _validate_operator_review_block(summary.get("operator_review"), "operator_review", errors)

    forbidden_paths = _find_forbidden_decision_terms(summary)
    if forbidden_paths:
        errors.append(
            "forbidden scoring/action field detected in report summary at: "
            + ", ".join(sorted(forbidden_paths))
        )

    rows = summary.get("report_summary_rows")
    row_counts: dict[str, int] | None = None
    if not isinstance(rows, list) or not rows:
        errors.append("report_summary_rows must be a non-empty list")
    else:
        row_counts = _validate_report_rows(rows, errors)

    if isinstance(row_counts, dict):
        expected_counts = dict(row_counts)
        operator_review = summary.get("operator_review")
        steps = operator_review.get("steps") if isinstance(operator_review, dict) else None
        expected_counts["operator_review_steps"] = len(steps) if isinstance(steps, list) else 0
        expected_counts["warnings"] = len(summary["warnings"]) if isinstance(summary.get("warnings"), list) else 0
        if summary.get("summary_counts") != expected_counts:
            errors.append("summary_counts must match report_summary_rows totals: " + _canonical_json(expected_counts))

    return SourceQualityLedgerValidation(valid=not errors, errors=tuple(errors))


def build_operator_report(summary: dict[str, Any]) -> str:
    lines: list[str] = [
        "# PMBOT Source Quality Report Summary",
        "",
        f"Summary: `{summary['report_summary_id']}`",
        f"Build: `{summary['build_id']}`",
        f"Ledger: `{summary['ledger_id']}`",
        f"Ledger build: `{summary['ledger_build_id']}`",
        f"Run mode: `{summary['run_mode']}`",
        f"Operator review: `{summary['operator_review']['status']}`",
        "",
        "## Summary Counts",
        "",
        f"- Source artifacts: {summary['summary_counts']['source_artifacts']}",
        f"- Report summary rows: {summary['summary_counts']['report_summary_rows']}",
        f"- Declared fields: {summary['summary_counts']['fields_declared']}",
        f"- Present fields: {summary['summary_counts']['fields_present']}",
        f"- Missing fields: {summary['summary_counts']['fields_missing']}",
        f"- Review checks: {summary['summary_counts']['review_checks']}",
        f"- Known limitations: {summary['summary_counts']['known_limitations']}",
        "",
        "## Source Report Rows",
        "",
    ]
    for row in summary["report_summary_rows"]:
        lines.extend(
            [
                f"- `{row['source_id']}` ({row['source_label']})",
                f"  - Local artifact: `{row['local_reference']}`",
                f"  - Snapshot: `{row['snapshot_id']}`",
                f"  - Artifact role: `{row['artifact_role']}`",
                f"  - Fields present: {row['field_summary']['present']}/{row['field_summary']['declared']}",
                f"  - Review checks: {row['review_check_count']} pending operator review",
                f"  - Known limitations: {row['known_limitation_count']}",
            ]
        )

    lines.extend(["", "## Operator Review Steps", ""])
    for step in summary["operator_review"]["steps"]:
        lines.append(f"- {step}")

    lines.extend(
        [
            "",
            "## Safety",
            "",
            "- Local fixture/static input only.",
            "- Makes no network, LLM, external market API, wallet, order, transaction endpoint, runtime, browser, scheduler, or worker calls.",
            "- Descriptive report summary only; no outcome resolution or trade instruction output.",
            "- Not execution approval and not runtime input.",
        ]
    )
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a local PMBOT source quality report summary.")
    parser.add_argument("--ledger", required=True, help="Local source quality ledger JSON.")
    parser.add_argument("--output-summary", required=True, help="Output report summary JSON path.")
    parser.add_argument("--output-report", required=True, help="Output operator report Markdown path.")
    args = parser.parse_args(argv)

    ledger = load_source_quality_ledger(args.ledger)
    summary = build_source_quality_report_summary(ledger)
    report = build_operator_report(summary)

    _write_json(Path(args.output_summary), summary)
    Path(args.output_report).write_text(report, encoding="utf-8")
    return 0


def _build_report_row(row: dict[str, Any]) -> dict[str, Any]:
    declared_fields = [field["field_name"] for field in row["field_presence"]]
    return {
        "artifact_role": row["artifact_role"],
        "declared_fields": declared_fields,
        "field_summary": dict(row["field_summary"]),
        "known_limitation_count": len(row["known_limitations"]),
        "local_reference": row["local_reference"],
        "operator_review_status": OPERATOR_REVIEW_STATUS,
        "report_row_id": f"{row['row_id']}.{REPORT_SUMMARY_SCOPE}",
        "review_check_count": len(row["review_checks"]),
        "row_id": row["row_id"],
        "runner_state": REPORT_SUMMARY_ROW_STATE,
        "snapshot_id": row["snapshot_id"],
        "source_id": row["source_id"],
        "source_label": row["source_label"],
        "source_type": row["source_type"],
    }


def _summary_counts(
    rows: list[dict[str, Any]],
    operator_review_steps: list[str],
    warnings: list[str],
) -> dict[str, int]:
    return {
        "fields_declared": sum(row["field_summary"]["declared"] for row in rows),
        "fields_missing": sum(row["field_summary"]["missing"] for row in rows),
        "fields_present": sum(row["field_summary"]["present"] for row in rows),
        "known_limitations": sum(row["known_limitation_count"] for row in rows),
        "operator_review_steps": len(operator_review_steps),
        "report_summary_rows": len(rows),
        "review_checks": sum(row["review_check_count"] for row in rows),
        "source_artifacts": len(rows),
        "warnings": len(warnings),
    }


def _validate_report_rows(rows: list[Any], errors: list[str]) -> dict[str, int]:
    seen_report_row_ids: set[str] = set()
    counts = {
        "fields_declared": 0,
        "fields_missing": 0,
        "fields_present": 0,
        "known_limitations": 0,
        "report_summary_rows": 0,
        "review_checks": 0,
        "source_artifacts": 0,
    }
    for index, row in enumerate(rows):
        path = f"report_summary_rows[{index}]"
        if not isinstance(row, dict):
            errors.append(f"{path} must be an object")
            continue
        _validate_report_row(path, row, seen_report_row_ids, counts, errors)
    return counts


def _validate_report_row(
    path: str,
    row: dict[str, Any],
    seen_report_row_ids: set[str],
    counts: dict[str, int],
    errors: list[str],
) -> None:
    required_fields = (
        "artifact_role",
        "declared_fields",
        "field_summary",
        "known_limitation_count",
        "local_reference",
        "operator_review_status",
        "report_row_id",
        "review_check_count",
        "row_id",
        "runner_state",
        "snapshot_id",
        "source_id",
        "source_label",
        "source_type",
    )
    for field in required_fields:
        if field not in row:
            errors.append(f"{path} missing required field: {field}")

    for field in (
        "artifact_role",
        "local_reference",
        "report_row_id",
        "row_id",
        "runner_state",
        "snapshot_id",
        "source_id",
        "source_label",
        "source_type",
    ):
        if not isinstance(row.get(field), str) or not row.get(field):
            errors.append(f"{path}.{field} must be a non-empty string")

    if row.get("operator_review_status") != OPERATOR_REVIEW_STATUS:
        errors.append(f"{path}.operator_review_status must be {OPERATOR_REVIEW_STATUS}")
    if row.get("runner_state") != REPORT_SUMMARY_ROW_STATE:
        errors.append(f"{path}.runner_state must be {REPORT_SUMMARY_ROW_STATE}")

    report_row_id = row.get("report_row_id")
    if isinstance(report_row_id, str) and report_row_id:
        if report_row_id in seen_report_row_ids:
            errors.append(f"{path}.report_row_id duplicates an earlier report row")
        seen_report_row_ids.add(report_row_id)

    row_id = row.get("row_id")
    if isinstance(row_id, str) and row_id and report_row_id != f"{row_id}.{REPORT_SUMMARY_SCOPE}":
        errors.append(f"{path}.report_row_id must be derived from row_id and report summary scope")

    reference_errors = _validate_local_reference(row["local_reference"]) if isinstance(row.get("local_reference"), str) else []
    errors.extend(f"{path}.{error}" for error in reference_errors)

    if not _is_non_empty_string_list(row.get("declared_fields")):
        errors.append(f"{path}.declared_fields must be a non-empty list of strings")
        declared_field_count = 0
    else:
        declared_field_count = len(row["declared_fields"])

    field_summary = row.get("field_summary")
    if not isinstance(field_summary, dict):
        errors.append(f"{path}.field_summary must be an object")
        declared = present = missing = 0
    else:
        declared = _non_bool_int(field_summary.get("declared"))
        present = _non_bool_int(field_summary.get("present"))
        missing = _non_bool_int(field_summary.get("missing"))
        if declared is None or present is None or missing is None:
            errors.append(f"{path}.field_summary values must be integers")
            declared = present = missing = 0
        elif declared != present + missing:
            errors.append(f"{path}.field_summary declared count must equal present plus missing")
        if declared_field_count and declared != declared_field_count:
            errors.append(f"{path}.field_summary declared count must match declared_fields length")

    review_check_count = _non_bool_int(row.get("review_check_count"))
    known_limitation_count = _non_bool_int(row.get("known_limitation_count"))
    if review_check_count is None:
        errors.append(f"{path}.review_check_count must be an integer")
        review_check_count = 0
    if known_limitation_count is None:
        errors.append(f"{path}.known_limitation_count must be an integer")
        known_limitation_count = 0

    counts["fields_declared"] += declared
    counts["fields_missing"] += missing
    counts["fields_present"] += present
    counts["known_limitations"] += known_limitation_count
    counts["report_summary_rows"] += 1
    counts["review_checks"] += review_check_count
    counts["source_artifacts"] += 1


def _non_bool_int(value: Any) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int):
        return None
    return value


if __name__ == "__main__":
    raise SystemExit(main())
