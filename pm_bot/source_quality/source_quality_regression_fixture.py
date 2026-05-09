from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
from typing import Any

from pm_bot.source_quality.source_quality_report_summary import (
    REPORT_SUMMARY_CONTRACT_VERSION,
    REPORT_SUMMARY_SCOPE,
    validate_source_quality_report_summary,
)
from pm_bot.source_quality.unified_source_quality_ledger import (
    EXPECTED_LEDGER_SAFETY_BOUNDARIES,
    LEDGER_CONTRACT_VERSION,
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

REGRESSION_FIXTURE_CONTRACT_VERSION = "pmbot_source_quality_regression_fixture.v1"
REGRESSION_FIXTURE_ID = "source_quality_regression_fixture_001"
REGRESSION_FIXTURE_RUN_MODE = "local_source_quality_regression_fixture"
REGRESSION_FIXTURE_SCOPE = "source_quality_regression_fixture"
REGRESSION_FIXTURE_ROW_STATE = "descriptive_source_quality_regression_review"
REGRESSION_DIGEST_LENGTH = 12

SAMPLE_LEDGER_PATH = "pm_bot/source_quality/samples/unified_source_quality_ledger.fixture.json"
SAMPLE_REPORT_SUMMARY_PATH = "pm_bot/source_quality/samples/source_quality_report_summary.fixture.json"
SAMPLE_REGRESSION_FIXTURE_PATH = "pm_bot/source_quality/samples/source_quality_regression.fixture.json"


def load_source_quality_regression_fixture(path: str | Path) -> dict[str, Any]:
    reference = str(path)
    errors = _validate_local_reference(reference)
    if errors:
        raise SourceQualityLedgerValidationError(tuple(errors))
    return _load_json(Path(_normalize_reference(reference)))


def build_source_quality_regression_fixture(
    ledger: dict[str, Any],
    report_summary: dict[str, Any],
) -> dict[str, Any]:
    errors = _source_artifact_errors(ledger, report_summary)
    if errors:
        raise SourceQualityLedgerValidationError(tuple(errors))

    fixture_rows = _build_fixture_rows(ledger, report_summary)
    review_assertions = _build_review_assertions(ledger, report_summary, fixture_rows)
    summary_counts = _summary_counts(fixture_rows, review_assertions)
    fixture = {
        "artifact_references": [
            {
                "build_id": ledger["build_id"],
                "contract_version": LEDGER_CONTRACT_VERSION,
                "local_reference": SAMPLE_LEDGER_PATH,
                "reference_role": "unified_source_quality_ledger_sample",
            },
            {
                "build_id": report_summary["build_id"],
                "contract_version": REPORT_SUMMARY_CONTRACT_VERSION,
                "local_reference": SAMPLE_REPORT_SUMMARY_PATH,
                "reference_role": "source_quality_report_summary_sample",
            },
        ],
        "baseline": {
            "ledger_build_id": ledger["build_id"],
            "ledger_id": ledger["ledger_id"],
            "report_summary_build_id": report_summary["build_id"],
            "report_summary_id": report_summary["report_summary_id"],
            "report_summary_ledger_build_id": report_summary["ledger_build_id"],
        },
        "build_id": _build_deterministic_id(ledger, report_summary, fixture_rows, review_assertions),
        "contract_version": REGRESSION_FIXTURE_CONTRACT_VERSION,
        "errors": [],
        "fixture_id": REGRESSION_FIXTURE_ID,
        "local_only": True,
        "operator_review": {
            "status": OPERATOR_REVIEW_STATUS,
            "steps": [
                "Confirm the ledger sample and report summary sample are the static local artifacts named in artifact_references.",
                "Confirm review assertions describe structural parity only.",
                "Record any source artifact dispute outside this regression fixture.",
            ],
        },
        "operator_review_required": True,
        "regression_fixture_rows": fixture_rows,
        "review_assertions": review_assertions,
        "run_mode": REGRESSION_FIXTURE_RUN_MODE,
        "safety_boundaries": dict(EXPECTED_LEDGER_SAFETY_BOUNDARIES),
        "scope": REGRESSION_FIXTURE_SCOPE,
        "summary_counts": summary_counts,
        "warnings": [],
    }
    return fixture


def validate_source_quality_regression_fixture(fixture: dict[str, Any]) -> SourceQualityLedgerValidation:
    errors: list[str] = []
    if not isinstance(fixture, dict):
        return SourceQualityLedgerValidation(valid=False, errors=("fixture must be an object",))

    required_fields = (
        "artifact_references",
        "baseline",
        "build_id",
        "contract_version",
        "errors",
        "fixture_id",
        "local_only",
        "operator_review",
        "operator_review_required",
        "regression_fixture_rows",
        "review_assertions",
        "run_mode",
        "safety_boundaries",
        "scope",
        "summary_counts",
        "warnings",
    )
    for field in required_fields:
        if field not in fixture:
            errors.append(f"missing required regression fixture field: {field}")

    if fixture.get("contract_version") != REGRESSION_FIXTURE_CONTRACT_VERSION:
        errors.append(f"contract_version must be {REGRESSION_FIXTURE_CONTRACT_VERSION}")
    if fixture.get("fixture_id") != REGRESSION_FIXTURE_ID:
        errors.append(f"fixture_id must be {REGRESSION_FIXTURE_ID}")
    if fixture.get("scope") != REGRESSION_FIXTURE_SCOPE:
        errors.append(f"scope must be {REGRESSION_FIXTURE_SCOPE}")
    if fixture.get("run_mode") != REGRESSION_FIXTURE_RUN_MODE:
        errors.append(f"run_mode must be {REGRESSION_FIXTURE_RUN_MODE}")
    if fixture.get("local_only") is not True:
        errors.append("local_only must be true")
    if fixture.get("operator_review_required") is not True:
        errors.append("operator_review_required must be true")
    if fixture.get("errors") != []:
        errors.append("errors must be an empty list")
    if not _is_string_list(fixture.get("warnings")):
        errors.append("warnings must be a list of strings")
    if fixture.get("safety_boundaries") != EXPECTED_LEDGER_SAFETY_BOUNDARIES:
        errors.append("safety_boundaries must match the local-only source quality boundary")

    _validate_build_id(fixture.get("build_id"), errors)
    _validate_operator_review_block(fixture.get("operator_review"), "operator_review", errors)
    _validate_artifact_references(fixture.get("artifact_references"), errors)
    _validate_baseline(fixture.get("baseline"), errors)

    forbidden_paths = _find_forbidden_decision_terms(fixture)
    if forbidden_paths:
        errors.append(
            "forbidden scoring/action field detected in regression fixture at: "
            + ", ".join(sorted(forbidden_paths))
        )

    rows = fixture.get("regression_fixture_rows")
    row_counts: dict[str, int] | None = None
    if not isinstance(rows, list) or not rows:
        errors.append("regression_fixture_rows must be a non-empty list")
    else:
        row_counts = _validate_fixture_rows(rows, errors)

    assertions = fixture.get("review_assertions")
    assertion_count = 0
    if not isinstance(assertions, list) or not assertions:
        errors.append("review_assertions must be a non-empty list")
    else:
        assertion_count = _validate_review_assertions(assertions, errors)

    if row_counts is not None:
        expected_counts = dict(row_counts)
        expected_counts["artifact_references"] = (
            len(fixture["artifact_references"]) if isinstance(fixture.get("artifact_references"), list) else 0
        )
        expected_counts["review_assertions"] = assertion_count
        expected_counts["warnings"] = len(fixture["warnings"]) if isinstance(fixture.get("warnings"), list) else 0
        if fixture.get("summary_counts") != expected_counts:
            errors.append("summary_counts must match regression fixture totals: " + _canonical_json(expected_counts))

    return SourceQualityLedgerValidation(valid=not errors, errors=tuple(errors))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a local PMBOT source quality regression fixture.")
    parser.add_argument("--ledger", required=True, help="Local unified source quality ledger sample JSON.")
    parser.add_argument("--report-summary", required=True, help="Local source quality report summary sample JSON.")
    parser.add_argument("--output-fixture", required=True, help="Output regression fixture JSON path.")
    args = parser.parse_args(argv)

    ledger = _load_json(Path(_normalize_reference(args.ledger)))
    report_summary = _load_json(Path(_normalize_reference(args.report_summary)))
    fixture = build_source_quality_regression_fixture(ledger, report_summary)
    _write_json(Path(args.output_fixture), fixture)
    return 0


def _source_artifact_errors(ledger: dict[str, Any], report_summary: dict[str, Any]) -> list[str]:
    errors: list[str] = []

    ledger_validation = validate_unified_source_quality_ledger(ledger)
    if not ledger_validation.valid:
        errors.extend(f"ledger: {error}" for error in ledger_validation.errors)

    summary_validation = validate_source_quality_report_summary(report_summary)
    if not summary_validation.valid:
        errors.extend(f"report_summary: {error}" for error in summary_validation.errors)

    if errors:
        return errors

    if report_summary["ledger_id"] != ledger["ledger_id"]:
        errors.append("report_summary ledger_id must match ledger ledger_id")
    if report_summary["ledger_build_id"] != ledger["build_id"]:
        errors.append("report_summary ledger_build_id must match ledger build_id")

    ledger_counts = ledger["summary_counts"]
    summary_counts = report_summary["summary_counts"]
    count_pairs = (
        ("source_artifacts", "source_artifacts"),
        ("fields_declared", "fields_declared"),
        ("fields_present", "fields_present"),
        ("fields_missing", "fields_missing"),
        ("warnings", "warnings"),
    )
    for ledger_key, summary_key in count_pairs:
        if ledger_counts[ledger_key] != summary_counts[summary_key]:
            errors.append(f"summary count mismatch for {ledger_key}")

    ledger_rows = {row["row_id"]: row for row in ledger["source_quality_rows"]}
    summary_rows = {row["row_id"]: row for row in report_summary["report_summary_rows"]}
    if set(ledger_rows) != set(summary_rows):
        errors.append("report_summary row_id set must match ledger source_quality_rows row_id set")
    for row_id, ledger_row in ledger_rows.items():
        summary_row = summary_rows.get(row_id)
        if summary_row is None:
            continue
        if summary_row["field_summary"] != ledger_row["field_summary"]:
            errors.append(f"field summary mismatch for row_id {row_id}")
        if summary_row["local_reference"] != ledger_row["local_reference"]:
            errors.append(f"local_reference mismatch for row_id {row_id}")
        if summary_row["report_row_id"] != f"{row_id}.{REPORT_SUMMARY_SCOPE}":
            errors.append(f"report_row_id must be derived from row_id for {row_id}")

    return errors


def _build_fixture_rows(
    ledger: dict[str, Any],
    report_summary: dict[str, Any],
) -> list[dict[str, Any]]:
    report_rows = {row["row_id"]: row for row in report_summary["report_summary_rows"]}
    fixture_rows: list[dict[str, Any]] = []
    for ledger_row in ledger["source_quality_rows"]:
        report_row = report_rows[ledger_row["row_id"]]
        fixture_rows.append(
            {
                "declared_fields": list(report_row["declared_fields"]),
                "field_summary": dict(ledger_row["field_summary"]),
                "known_limitation_count": report_row["known_limitation_count"],
                "ledger_row_id": ledger_row["row_id"],
                "local_reference": ledger_row["local_reference"],
                "operator_review_status": OPERATOR_REVIEW_STATUS,
                "report_row_id": report_row["report_row_id"],
                "review_check_count": report_row["review_check_count"],
                "runner_state": REGRESSION_FIXTURE_ROW_STATE,
                "snapshot_id": ledger_row["snapshot_id"],
                "source_id": ledger_row["source_id"],
                "source_label": ledger_row["source_label"],
                "source_type": ledger_row["source_type"],
            }
        )
    return fixture_rows


def _build_review_assertions(
    ledger: dict[str, Any],
    report_summary: dict[str, Any],
    fixture_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    ledger_counts = ledger["summary_counts"]
    summary_counts = report_summary["summary_counts"]
    return [
        _assertion(
            "ledger_contract_version",
            "Ledger sample uses the expected local contract version.",
            LEDGER_CONTRACT_VERSION,
            ledger["contract_version"],
        ),
        _assertion(
            "report_summary_contract_version",
            "Report summary sample uses the expected local contract version.",
            REPORT_SUMMARY_CONTRACT_VERSION,
            report_summary["contract_version"],
        ),
        _assertion(
            "ledger_to_report_summary_build",
            "Report summary sample references the ledger sample build.",
            ledger["build_id"],
            report_summary["ledger_build_id"],
        ),
        _assertion(
            "source_artifact_total",
            "Ledger and report summary retain the same source artifact total.",
            ledger_counts["source_artifacts"],
            summary_counts["source_artifacts"],
        ),
        _assertion(
            "declared_field_total",
            "Ledger and report summary retain the same declared field total.",
            ledger_counts["fields_declared"],
            summary_counts["fields_declared"],
        ),
        _assertion(
            "present_field_total",
            "Ledger and report summary retain the same present field total.",
            ledger_counts["fields_present"],
            summary_counts["fields_present"],
        ),
        _assertion(
            "missing_field_total",
            "Ledger and report summary retain the same missing field total.",
            ledger_counts["fields_missing"],
            summary_counts["fields_missing"],
        ),
        _assertion(
            "warning_total",
            "Ledger and report summary retain the same warning total.",
            ledger_counts["warnings"],
            summary_counts["warnings"],
        ),
        _assertion(
            "row_identity_alignment",
            "Regression rows preserve source row and report row identity alignment.",
            [row["ledger_row_id"] for row in fixture_rows],
            [
                row["report_row_id"].removesuffix(f".{REPORT_SUMMARY_SCOPE}")
                for row in fixture_rows
            ],
        ),
        _assertion(
            "operator_review_state",
            "Regression rows remain pending operator review.",
            [OPERATOR_REVIEW_STATUS],
            sorted({row["operator_review_status"] for row in fixture_rows}),
        ),
        _assertion(
            "local_safety_boundary",
            "Local-only safety boundary remains unchanged.",
            EXPECTED_LEDGER_SAFETY_BOUNDARIES,
            ledger["safety_boundaries"],
        ),
    ]


def _assertion(
    assertion_id: str,
    description: str,
    expected_value: Any,
    observed_value: Any,
) -> dict[str, Any]:
    return {
        "assertion_id": assertion_id,
        "description": description,
        "expected_value": expected_value,
        "observed_value": observed_value,
        "operator_review_status": OPERATOR_REVIEW_STATUS,
    }


def _summary_counts(
    rows: list[dict[str, Any]],
    assertions: list[dict[str, Any]],
) -> dict[str, int]:
    return {
        "artifact_references": 2,
        "fields_declared": sum(row["field_summary"]["declared"] for row in rows),
        "fields_missing": sum(row["field_summary"]["missing"] for row in rows),
        "fields_present": sum(row["field_summary"]["present"] for row in rows),
        "known_limitations": sum(row["known_limitation_count"] for row in rows),
        "regression_fixture_rows": len(rows),
        "review_assertions": len(assertions),
        "review_checks": sum(row["review_check_count"] for row in rows),
        "source_artifacts": len(rows),
        "warnings": 0,
    }


def _build_deterministic_id(
    ledger: dict[str, Any],
    report_summary: dict[str, Any],
    fixture_rows: list[dict[str, Any]],
    review_assertions: list[dict[str, Any]],
) -> str:
    digest_input = {
        "fixture_id": REGRESSION_FIXTURE_ID,
        "fixture_rows": fixture_rows,
        "ledger_build_id": ledger["build_id"],
        "report_summary_build_id": report_summary["build_id"],
        "review_assertions": review_assertions,
    }
    digest = hashlib.sha256(_canonical_json(digest_input).encode("utf-8")).hexdigest()[:REGRESSION_DIGEST_LENGTH]
    return f"{REGRESSION_FIXTURE_ID}-{digest}"


def _validate_build_id(build_id: Any, errors: list[str]) -> None:
    if not isinstance(build_id, str) or not build_id:
        errors.append("build_id must be a non-empty string")
        return
    prefix = f"{REGRESSION_FIXTURE_ID}-"
    if not build_id.startswith(prefix):
        errors.append("build_id must start with fixture_id followed by a digest")
        return
    digest = build_id[len(prefix):]
    if len(digest) != REGRESSION_DIGEST_LENGTH or any(character not in "0123456789abcdef" for character in digest):
        errors.append(f"build_id digest must be {REGRESSION_DIGEST_LENGTH} lowercase hex characters")


def _validate_artifact_references(value: Any, errors: list[str]) -> None:
    if not isinstance(value, list) or not value:
        errors.append("artifact_references must be a non-empty list")
        return
    seen_roles: set[str] = set()
    for index, reference in enumerate(value):
        path = f"artifact_references[{index}]"
        if not isinstance(reference, dict):
            errors.append(f"{path} must be an object")
            continue
        for field in ("build_id", "contract_version", "local_reference", "reference_role"):
            if not isinstance(reference.get(field), str) or not reference.get(field):
                errors.append(f"{path}.{field} must be a non-empty string")
        role = reference.get("reference_role")
        if isinstance(role, str):
            if role in seen_roles:
                errors.append(f"{path}.reference_role duplicates an earlier artifact reference")
            seen_roles.add(role)
        local_reference = reference.get("local_reference")
        if isinstance(local_reference, str):
            reference_errors = _validate_local_reference(local_reference)
            errors.extend(f"{path}.{error}" for error in reference_errors)


def _validate_baseline(value: Any, errors: list[str]) -> None:
    if not isinstance(value, dict):
        errors.append("baseline must be an object")
        return
    for field in (
        "ledger_build_id",
        "ledger_id",
        "report_summary_build_id",
        "report_summary_id",
        "report_summary_ledger_build_id",
    ):
        if not isinstance(value.get(field), str) or not value.get(field):
            errors.append(f"baseline.{field} must be a non-empty string")
    if (
        isinstance(value.get("ledger_build_id"), str)
        and isinstance(value.get("report_summary_ledger_build_id"), str)
        and value["ledger_build_id"] != value["report_summary_ledger_build_id"]
    ):
        errors.append("baseline.report_summary_ledger_build_id must match baseline.ledger_build_id")


def _validate_fixture_rows(rows: list[Any], errors: list[str]) -> dict[str, int]:
    seen_source_ids: set[str] = set()
    seen_ledger_row_ids: set[str] = set()
    counts = {
        "fields_declared": 0,
        "fields_missing": 0,
        "fields_present": 0,
        "known_limitations": 0,
        "regression_fixture_rows": 0,
        "review_checks": 0,
        "source_artifacts": 0,
    }
    for index, row in enumerate(rows):
        path = f"regression_fixture_rows[{index}]"
        if not isinstance(row, dict):
            errors.append(f"{path} must be an object")
            continue
        _validate_fixture_row(path, row, seen_source_ids, seen_ledger_row_ids, counts, errors)
    return counts


def _validate_fixture_row(
    path: str,
    row: dict[str, Any],
    seen_source_ids: set[str],
    seen_ledger_row_ids: set[str],
    counts: dict[str, int],
    errors: list[str],
) -> None:
    required_fields = (
        "declared_fields",
        "field_summary",
        "known_limitation_count",
        "ledger_row_id",
        "local_reference",
        "operator_review_status",
        "report_row_id",
        "review_check_count",
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
        "ledger_row_id",
        "local_reference",
        "report_row_id",
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
    if row.get("runner_state") != REGRESSION_FIXTURE_ROW_STATE:
        errors.append(f"{path}.runner_state must be {REGRESSION_FIXTURE_ROW_STATE}")

    source_id = row.get("source_id")
    if isinstance(source_id, str):
        if source_id in seen_source_ids:
            errors.append(f"{path}.source_id duplicates an earlier regression fixture row")
        seen_source_ids.add(source_id)

    ledger_row_id = row.get("ledger_row_id")
    report_row_id = row.get("report_row_id")
    if isinstance(ledger_row_id, str):
        if ledger_row_id in seen_ledger_row_ids:
            errors.append(f"{path}.ledger_row_id duplicates an earlier regression fixture row")
        seen_ledger_row_ids.add(ledger_row_id)
        if isinstance(report_row_id, str) and report_row_id != f"{ledger_row_id}.{REPORT_SUMMARY_SCOPE}":
            errors.append(f"{path}.report_row_id must be derived from ledger_row_id and report summary scope")

    local_reference = row.get("local_reference")
    if isinstance(local_reference, str):
        reference_errors = _validate_local_reference(local_reference)
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
    counts["regression_fixture_rows"] += 1
    counts["review_checks"] += review_check_count
    counts["source_artifacts"] += 1


def _validate_review_assertions(assertions: list[Any], errors: list[str]) -> int:
    seen_assertion_ids: set[str] = set()
    valid_count = 0
    for index, assertion in enumerate(assertions):
        path = f"review_assertions[{index}]"
        if not isinstance(assertion, dict):
            errors.append(f"{path} must be an object")
            continue
        for field in ("assertion_id", "description", "operator_review_status"):
            if not isinstance(assertion.get(field), str) or not assertion.get(field):
                errors.append(f"{path}.{field} must be a non-empty string")
        for field in ("expected_value", "observed_value"):
            if field not in assertion:
                errors.append(f"{path} missing required field: {field}")
        assertion_id = assertion.get("assertion_id")
        if isinstance(assertion_id, str):
            if assertion_id in seen_assertion_ids:
                errors.append(f"{path}.assertion_id duplicates an earlier review assertion")
            seen_assertion_ids.add(assertion_id)
        if assertion.get("operator_review_status") != OPERATOR_REVIEW_STATUS:
            errors.append(f"{path}.operator_review_status must be {OPERATOR_REVIEW_STATUS}")
        if assertion.get("expected_value") != assertion.get("observed_value"):
            errors.append(f"{path}.observed_value must match expected_value")
        valid_count += 1
    return valid_count


def _non_bool_int(value: Any) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int):
        return None
    return value


if __name__ == "__main__":
    raise SystemExit(main())
