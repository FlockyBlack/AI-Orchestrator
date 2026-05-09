from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from pm_bot.source_quality.source_evidence_inventory_ledger import (
    EXPECTED_SAFETY_BOUNDARIES,
    OPERATOR_REVIEW_STATUS,
    SourceQualityLedgerValidation,
    SourceQualityLedgerValidationError,
    _find_forbidden_evidence_terms,
)
from pm_bot.source_quality.source_staleness_check_spec import (
    SPEC_CONTRACT_VERSION as SOURCE_STALENESS_SPEC_CONTRACT_VERSION,
    validate_source_staleness_check_spec,
)
from pm_bot.source_quality.unified_source_quality_ledger import (
    _canonical_json,
    _is_non_empty_review_check_list,
    _is_non_empty_string_list,
    _is_string_list,
    _load_json,
    _normalize_reference,
    _validate_local_reference,
    _validate_operator_review_block,
    _write_json,
)

REQUEST_CONTRACT_VERSION = "pmbot_source_contradiction_ledger_request.v1"
LEDGER_CONTRACT_VERSION = "pmbot_source_contradiction_ledger.v1"
LEDGER_SCOPE = "source_contradiction_ledger"
LEDGER_RUN_MODE = "local_static_source_contradiction_ledger"
CONTRADICTION_ROW_STATE = "descriptive_source_contradiction_review"
BUILD_ID_DIGEST_LENGTH = 12
SAMPLE_LEDGER_PATH = "pm_bot/source_quality/samples/source_contradiction_ledger.fixture.json"
SAMPLE_OPERATOR_REPORT_PATH = "pm_bot/source_quality/samples/source_contradiction_ledger.fixture.md"

MAPPED_FIELD_VALUE_COMPARE = "mapped_field_value_compare"
MATCHING_STATIC_VALUES = "matching_static_values"
DIFFERENT_STATIC_VALUES_PENDING_REVIEW = "different_static_values_pending_review"
NO_STATIC_DIFFERENCE_RECORDED = "no_static_difference_recorded"
STATIC_VALUE_DIFFERENCE_PENDING_REVIEW = "static_value_difference_pending_review"
SUBJECT_KEY_DIFFERENCE_PENDING_REVIEW = "subject_key_difference_pending_review"
FIELD_UNAVAILABLE_PENDING_REVIEW = "field_unavailable_pending_review"


def load_source_contradiction_ledger_request(path: str | Path) -> dict[str, Any]:
    reference = str(path)
    errors = _validate_local_reference(reference)
    if errors:
        raise SourceQualityLedgerValidationError(tuple(errors))
    return _load_json(Path(_normalize_reference(reference)))


def build_source_contradiction_ledger(request: dict[str, Any]) -> dict[str, Any]:
    validation = validate_source_contradiction_ledger_request(request)
    if not validation.valid:
        raise SourceQualityLedgerValidationError(validation.errors)

    spec_reference = _normalize_reference(request["source_staleness_check_spec_reference"])
    report_reference = _normalize_reference(request["source_staleness_check_report_reference"])
    documentation_reference = _normalize_reference(request["documentation_reference"])
    spec = _load_json(Path(spec_reference))
    spec_rows_by_source_id = _source_staleness_rows_by_source_id(spec)
    warnings: list[str] = []
    rows = [
        _build_contradiction_row(
            ledger_id=request["ledger_id"],
            check=check,
            spec_rows_by_source_id=spec_rows_by_source_id,
            request=request,
        )
        for check in request["contradiction_checks"]
    ]
    rows = sorted(rows, key=lambda row: row["request_check_id"])
    ledger = {
        "build_id": _build_deterministic_id(request["ledger_id"], request, spec, rows),
        "contract_version": LEDGER_CONTRACT_VERSION,
        "documentation": _build_digest_reference(documentation_reference),
        "errors": [],
        "ledger_id": request["ledger_id"],
        "local_only": True,
        "operator_review": {
            "status": OPERATOR_REVIEW_STATUS,
            "steps": list(request["operator_review_steps"]),
        },
        "operator_review_required": True,
        "run_mode": LEDGER_RUN_MODE,
        "safety_boundaries": dict(EXPECTED_SAFETY_BOUNDARIES),
        "scope": LEDGER_SCOPE,
        "source_contradiction_rows": rows,
        "source_staleness_check_report": _build_digest_reference(report_reference),
        "source_staleness_check_spec": _build_staleness_spec_summary(spec, spec_reference),
        "summary_counts": _summary_counts(
            rows,
            request["operator_review_steps"],
            warnings,
            spec_reference,
            report_reference,
            documentation_reference,
        ),
        "warnings": warnings,
    }
    return ledger


def validate_source_contradiction_ledger_request(request: dict[str, Any]) -> SourceQualityLedgerValidation:
    errors: list[str] = []
    if not isinstance(request, dict):
        return SourceQualityLedgerValidation(valid=False, errors=("request must be an object",))

    required_fields = (
        "contract_version",
        "contradiction_checks",
        "documentation_reference",
        "known_limitations",
        "ledger_id",
        "local_only",
        "operator_review_required",
        "operator_review_steps",
        "review_checks",
        "scope",
        "source_staleness_check_report_reference",
        "source_staleness_check_spec_reference",
    )
    for field in required_fields:
        if field not in request:
            errors.append(f"missing required request field: {field}")

    if request.get("contract_version") != REQUEST_CONTRACT_VERSION:
        errors.append(f"contract_version must be {REQUEST_CONTRACT_VERSION}")
    if request.get("scope") != LEDGER_SCOPE:
        errors.append(f"scope must be {LEDGER_SCOPE}")
    if request.get("local_only") is not True:
        errors.append("local_only must be true")
    if request.get("operator_review_required") is not True:
        errors.append("operator_review_required must be true")
    if not isinstance(request.get("ledger_id"), str) or not request.get("ledger_id"):
        errors.append("ledger_id must be a non-empty string")
    if not _is_non_empty_string_list(request.get("operator_review_steps")):
        errors.append("operator_review_steps must be a non-empty list of strings")
    if not _is_non_empty_review_check_list(request.get("review_checks")):
        errors.append("review_checks must be a non-empty list of check objects")
    if not _is_string_list(request.get("known_limitations")):
        errors.append("known_limitations must be a list of strings")

    forbidden_paths = _find_forbidden_evidence_terms(request)
    if forbidden_paths:
        errors.append(
            "forbidden source evidence term detected in request at: "
            + ", ".join(sorted(forbidden_paths))
        )

    spec: dict[str, Any] | None = None
    for field in (
        "documentation_reference",
        "source_staleness_check_report_reference",
        "source_staleness_check_spec_reference",
    ):
        reference = request.get(field)
        if not isinstance(reference, str):
            errors.append(f"{field} must be a string")
            continue
        reference_errors = _validate_local_reference(reference)
        errors.extend(f"{field}.{error}" for error in reference_errors)
        if reference_errors:
            continue
        reference_path = Path(_normalize_reference(reference))
        if not reference_path.exists():
            errors.append(f"{field} must exist")
        elif not reference_path.is_file():
            errors.append(f"{field} must be a file")

    spec_reference = request.get("source_staleness_check_spec_reference")
    if isinstance(spec_reference, str) and not _validate_local_reference(spec_reference):
        try:
            spec = _load_json(Path(_normalize_reference(spec_reference)))
        except (OSError, json.JSONDecodeError, SourceQualityLedgerValidationError) as exc:
            errors.append(f"source_staleness_check_spec_reference must load a JSON object: {exc}")
        else:
            spec_validation = validate_source_staleness_check_spec(spec)
            if not spec_validation.valid:
                errors.extend(
                    f"source_staleness_check_spec_reference.{error}"
                    for error in spec_validation.errors
                )
            if spec.get("contract_version") != SOURCE_STALENESS_SPEC_CONTRACT_VERSION:
                errors.append(
                    "source_staleness_check_spec_reference contract_version must be "
                    + SOURCE_STALENESS_SPEC_CONTRACT_VERSION
                )

    checks = request.get("contradiction_checks")
    if not isinstance(checks, list) or not checks:
        errors.append("contradiction_checks must be a non-empty list")
    else:
        errors.extend(_validate_contradiction_check_requests(checks, spec))

    return SourceQualityLedgerValidation(valid=not errors, errors=tuple(errors))


def validate_source_contradiction_ledger(ledger: dict[str, Any]) -> SourceQualityLedgerValidation:
    errors: list[str] = []
    if not isinstance(ledger, dict):
        return SourceQualityLedgerValidation(valid=False, errors=("ledger must be an object",))

    required_fields = (
        "build_id",
        "contract_version",
        "documentation",
        "errors",
        "ledger_id",
        "local_only",
        "operator_review",
        "operator_review_required",
        "run_mode",
        "safety_boundaries",
        "scope",
        "source_contradiction_rows",
        "source_staleness_check_report",
        "source_staleness_check_spec",
        "summary_counts",
        "warnings",
    )
    for field in required_fields:
        if field not in ledger:
            errors.append(f"missing required ledger field: {field}")

    if ledger.get("contract_version") != LEDGER_CONTRACT_VERSION:
        errors.append(f"contract_version must be {LEDGER_CONTRACT_VERSION}")
    if ledger.get("scope") != LEDGER_SCOPE:
        errors.append(f"scope must be {LEDGER_SCOPE}")
    if ledger.get("run_mode") != LEDGER_RUN_MODE:
        errors.append(f"run_mode must be {LEDGER_RUN_MODE}")
    if ledger.get("local_only") is not True:
        errors.append("local_only must be true")
    if ledger.get("operator_review_required") is not True:
        errors.append("operator_review_required must be true")
    if ledger.get("errors") != []:
        errors.append("errors must be an empty list")
    if not _is_string_list(ledger.get("warnings")):
        errors.append("warnings must be a list of strings")
    if ledger.get("safety_boundaries") != EXPECTED_SAFETY_BOUNDARIES:
        errors.append("safety_boundaries must match the local-only source evidence boundary")

    ledger_id = ledger.get("ledger_id")
    if not isinstance(ledger_id, str) or not ledger_id:
        errors.append("ledger_id must be a non-empty string")
        ledger_id_for_rows = ""
    else:
        ledger_id_for_rows = ledger_id
        _validate_build_id(ledger_id, ledger.get("build_id"), errors)

    _validate_operator_review_block(ledger.get("operator_review"), "operator_review", errors)

    forbidden_paths = _find_forbidden_evidence_terms(ledger)
    if forbidden_paths:
        errors.append(
            "forbidden source evidence term detected in ledger at: "
            + ", ".join(sorted(forbidden_paths))
        )

    spec = _validate_staleness_spec_summary(ledger.get("source_staleness_check_spec"), errors)
    _validate_reference_object("source_staleness_check_report", ledger.get("source_staleness_check_report"), errors)
    _validate_reference_object("documentation", ledger.get("documentation"), errors)

    rows = ledger.get("source_contradiction_rows")
    row_counts: dict[str, int] | None = None
    if not isinstance(rows, list) or not rows:
        errors.append("source_contradiction_rows must be a non-empty list")
    else:
        row_counts = _validate_contradiction_rows(ledger_id_for_rows, rows, spec, errors)

    if row_counts is not None:
        operator_review = ledger.get("operator_review")
        operator_steps = operator_review.get("steps") if isinstance(operator_review, dict) else []
        warnings = ledger.get("warnings") if isinstance(ledger.get("warnings"), list) else []
        expected_counts = dict(row_counts)
        expected_counts["local_references"] = _count_ledger_local_references(ledger, expected_counts["local_references"])
        expected_counts["operator_review_steps"] = len(operator_steps) if isinstance(operator_steps, list) else 0
        expected_counts["warnings"] = len(warnings)
        if ledger.get("summary_counts") != expected_counts:
            errors.append("summary_counts must match source_contradiction_rows totals: " + _canonical_json(expected_counts))

    return SourceQualityLedgerValidation(valid=not errors, errors=tuple(errors))


def build_operator_report(ledger: dict[str, Any]) -> str:
    lines: list[str] = [
        "# PMBOT Source Contradiction Ledger",
        "",
        f"Ledger: `{ledger['ledger_id']}`",
        f"Build: `{ledger['build_id']}`",
        f"Run mode: `{ledger['run_mode']}`",
        f"Operator review: `{ledger['operator_review']['status']}`",
        "",
        "## Summary Counts",
        "",
        f"- Source contradiction rows: {ledger['summary_counts']['source_contradiction_rows']}",
        f"- Source staleness checks: {ledger['summary_counts']['source_staleness_checks']}",
        f"- Source artifact references: {ledger['summary_counts']['source_artifact_references']}",
        f"- Subject key comparisons: {ledger['summary_counts']['subject_key_comparisons']}",
        f"- Subject key differences: {ledger['summary_counts']['subject_key_differences']}",
        f"- Field comparisons: {ledger['summary_counts']['field_comparisons']}",
        f"- Static value differences: {ledger['summary_counts']['different_field_comparisons']}",
        f"- Local references: {ledger['summary_counts']['local_references']}",
        f"- Review checks: {ledger['summary_counts']['review_checks']}",
        "",
        "## Source Staleness Spec",
        "",
        f"- Spec: `{ledger['source_staleness_check_spec']['local_reference']}`",
        f"- Spec id: `{ledger['source_staleness_check_spec']['spec_id']}`",
        f"- Build: `{ledger['source_staleness_check_spec']['build_id']}`",
        f"- Rows: {ledger['source_staleness_check_spec']['source_staleness_checks']}",
        "",
        "## Source Contradiction Rows",
        "",
    ]
    for row in ledger["source_contradiction_rows"]:
        lines.extend(
            [
                f"- `{row['request_check_id']}` ({row['check_label']})",
                f"  - Left source: `{row['left_source']['source_id']}` -> `{row['left_source']['source_artifact']['local_reference']}`",
                f"  - Right source: `{row['right_source']['source_id']}` -> `{row['right_source']['source_artifact']['local_reference']}`",
                f"  - Contradiction state: `{row['contradiction_state']}`",
                f"  - Review checks: {len(row['review_checks'])} pending operator review",
            ]
        )
        for comparison in row["field_comparisons"]:
            lines.append(
                "  - "
                + f"{comparison['semantic_field']}: "
                + f"`{comparison['left_field']}`=`{comparison['left_value']}`; "
                + f"`{comparison['right_field']}`=`{comparison['right_value']}`; "
                + f"state `{comparison['comparison_state']}`"
            )

    lines.extend(["", "## Operator Review Steps", ""])
    for step in ledger["operator_review"]["steps"]:
        lines.append(f"- {step}")

    lines.extend(
        [
            "",
            "## Safety",
            "",
            "- Local fixture/static input only.",
            "- Makes no network, LLM, endpoint, wallet, order, runtime, browser, scheduler, or worker calls.",
            "- Records local static source differences and pending review state only.",
            "- Does not authorize execution and is not runtime input.",
        ]
    )
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a local PMBOT source contradiction ledger.")
    parser.add_argument("--request", required=True, help="Local source contradiction ledger request JSON.")
    parser.add_argument("--output-ledger", required=True, help="Output source contradiction ledger JSON path.")
    parser.add_argument("--output-report", required=True, help="Output operator report Markdown path.")
    args = parser.parse_args(argv)

    request = load_source_contradiction_ledger_request(args.request)
    ledger = build_source_contradiction_ledger(request)
    report = build_operator_report(ledger)

    _write_json(Path(args.output_ledger), ledger)
    Path(args.output_report).write_text(report, encoding="utf-8")
    return 0


def _validate_contradiction_check_requests(
    checks: list[Any],
    spec: dict[str, Any] | None,
) -> list[str]:
    errors: list[str] = []
    seen_check_ids: set[str] = set()
    spec_rows_by_source_id = _source_staleness_rows_by_source_id(spec) if isinstance(spec, dict) else {}
    for index, check in enumerate(checks):
        path = f"contradiction_checks[{index}]"
        if not isinstance(check, dict):
            errors.append(f"{path} must be an object")
            continue
        required_fields = (
            "check_id",
            "check_label",
            "comparison_kind",
            "field_mappings",
            "left_source_id",
            "right_source_id",
            "source_domain",
            "subject_key_fields",
        )
        for field in required_fields:
            if field not in check:
                errors.append(f"{path} missing required field: {field}")

        check_id = check.get("check_id")
        if not isinstance(check_id, str) or not check_id:
            errors.append(f"{path}.check_id must be a non-empty string")
        elif check_id in seen_check_ids:
            errors.append(f"{path}.check_id duplicates an earlier check")
        else:
            seen_check_ids.add(check_id)

        for field in ("check_label", "comparison_kind", "left_source_id", "right_source_id", "source_domain"):
            if not isinstance(check.get(field), str) or not check.get(field):
                errors.append(f"{path}.{field} must be a non-empty string")
        if check.get("comparison_kind") != MAPPED_FIELD_VALUE_COMPARE:
            errors.append(f"{path}.comparison_kind must be {MAPPED_FIELD_VALUE_COMPARE}")
        if check.get("left_source_id") == check.get("right_source_id"):
            errors.append(f"{path}.left_source_id and right_source_id must be different")

        subject_key_fields = check.get("subject_key_fields")
        if not _is_non_empty_string_list(subject_key_fields):
            errors.append(f"{path}.subject_key_fields must be a non-empty list of strings")
        field_mappings = check.get("field_mappings")
        if not isinstance(field_mappings, list) or not field_mappings:
            errors.append(f"{path}.field_mappings must be a non-empty list")
        else:
            errors.extend(_validate_field_mapping_requests(path, field_mappings))

        if not spec_rows_by_source_id:
            continue
        left_source_id = check.get("left_source_id")
        right_source_id = check.get("right_source_id")
        if isinstance(left_source_id, str) and left_source_id not in spec_rows_by_source_id:
            errors.append(f"{path}.left_source_id must exist in source staleness spec")
        if isinstance(right_source_id, str) and right_source_id not in spec_rows_by_source_id:
            errors.append(f"{path}.right_source_id must exist in source staleness spec")
        if left_source_id not in spec_rows_by_source_id or right_source_id not in spec_rows_by_source_id:
            continue

        left_row = spec_rows_by_source_id[left_source_id]
        right_row = spec_rows_by_source_id[right_source_id]
        if check.get("source_domain") != left_row.get("source_domain"):
            errors.append(f"{path}.source_domain must match left source staleness row")
        if check.get("source_domain") != right_row.get("source_domain"):
            errors.append(f"{path}.source_domain must match right source staleness row")

        left_artifact = _load_source_artifact(left_row)
        right_artifact = _load_source_artifact(right_row)
        if left_artifact is None or right_artifact is None:
            continue
        for field in subject_key_fields if _is_non_empty_string_list(subject_key_fields) else []:
            if field not in left_artifact:
                errors.append(f"{path}.subject_key_fields field missing from left source artifact: {field}")
            if field not in right_artifact:
                errors.append(f"{path}.subject_key_fields field missing from right source artifact: {field}")
        if isinstance(field_mappings, list):
            for mapping_index, mapping in enumerate(field_mappings):
                if not isinstance(mapping, dict):
                    continue
                left_field = mapping.get("left_field")
                right_field = mapping.get("right_field")
                if isinstance(left_field, str) and left_field not in left_artifact:
                    errors.append(f"{path}.field_mappings[{mapping_index}].left_field missing from left source artifact")
                if isinstance(right_field, str) and right_field not in right_artifact:
                    errors.append(f"{path}.field_mappings[{mapping_index}].right_field missing from right source artifact")

    return errors


def _validate_field_mapping_requests(path: str, field_mappings: list[Any]) -> list[str]:
    errors: list[str] = []
    seen_semantic_fields: set[str] = set()
    for index, mapping in enumerate(field_mappings):
        mapping_path = f"{path}.field_mappings[{index}]"
        if not isinstance(mapping, dict):
            errors.append(f"{mapping_path} must be an object")
            continue
        required_fields = ("left_field", "right_field", "semantic_field", "unit_label")
        for field in required_fields:
            if field not in mapping:
                errors.append(f"{mapping_path} missing required field: {field}")
            elif not isinstance(mapping.get(field), str) or not mapping.get(field):
                errors.append(f"{mapping_path}.{field} must be a non-empty string")
        semantic_field = mapping.get("semantic_field")
        if isinstance(semantic_field, str):
            if semantic_field in seen_semantic_fields:
                errors.append(f"{mapping_path}.semantic_field duplicates an earlier mapping")
            seen_semantic_fields.add(semantic_field)
    return errors


def _build_contradiction_row(
    ledger_id: str,
    check: dict[str, Any],
    spec_rows_by_source_id: dict[str, dict[str, Any]],
    request: dict[str, Any],
) -> dict[str, Any]:
    left_row = spec_rows_by_source_id[check["left_source_id"]]
    right_row = spec_rows_by_source_id[check["right_source_id"]]
    left_artifact = _load_source_artifact(left_row)
    right_artifact = _load_source_artifact(right_row)
    if left_artifact is None or right_artifact is None:
        raise SourceQualityLedgerValidationError(("source artifact could not be loaded",))

    subject_key_comparisons = [
        _build_subject_key_comparison(field, left_artifact, right_artifact)
        for field in check["subject_key_fields"]
    ]
    field_comparisons = [
        _build_field_comparison(mapping, left_artifact, right_artifact)
        for mapping in check["field_mappings"]
    ]
    return {
        "check_label": check["check_label"],
        "comparison_kind": check["comparison_kind"],
        "contradiction_state": _contradiction_state(subject_key_comparisons, field_comparisons),
        "known_limitations": list(request["known_limitations"]),
        "left_source": _build_source_summary(left_row),
        "operator_review_status": OPERATOR_REVIEW_STATUS,
        "request_check_id": check["check_id"],
        "review_checks": [
            {
                "check_id": review_check["check_id"],
                "description": review_check["description"],
                "operator_review_status": OPERATOR_REVIEW_STATUS,
            }
            for review_check in request["review_checks"]
        ],
        "right_source": _build_source_summary(right_row),
        "row_id": f"{ledger_id}.{check['check_id']}.source_contradiction_review",
        "row_state": CONTRADICTION_ROW_STATE,
        "source_domain": check["source_domain"],
        "subject_key_comparisons": subject_key_comparisons,
        "field_comparisons": field_comparisons,
    }


def _build_subject_key_comparison(
    field: str,
    left_artifact: dict[str, Any],
    right_artifact: dict[str, Any],
) -> dict[str, Any]:
    left_value = left_artifact.get(field)
    right_value = right_artifact.get(field)
    return {
        "field_name": field,
        "left_value": left_value,
        "operator_review_status": OPERATOR_REVIEW_STATUS,
        "right_value": right_value,
        "values_match": left_value == right_value,
    }


def _build_field_comparison(
    mapping: dict[str, Any],
    left_artifact: dict[str, Any],
    right_artifact: dict[str, Any],
) -> dict[str, Any]:
    left_value = left_artifact.get(mapping["left_field"])
    right_value = right_artifact.get(mapping["right_field"])
    values_match = left_value == right_value
    return {
        "comparison_state": MATCHING_STATIC_VALUES if values_match else DIFFERENT_STATIC_VALUES_PENDING_REVIEW,
        "left_field": mapping["left_field"],
        "left_value": left_value,
        "operator_review_status": OPERATOR_REVIEW_STATUS,
        "right_field": mapping["right_field"],
        "right_value": right_value,
        "semantic_field": mapping["semantic_field"],
        "unit_label": mapping["unit_label"],
        "values_match": values_match,
    }


def _contradiction_state(
    subject_key_comparisons: list[dict[str, Any]],
    field_comparisons: list[dict[str, Any]],
) -> str:
    if any(comparison["values_match"] is not True for comparison in subject_key_comparisons):
        return SUBJECT_KEY_DIFFERENCE_PENDING_REVIEW
    if any("left_value" not in comparison or "right_value" not in comparison for comparison in field_comparisons):
        return FIELD_UNAVAILABLE_PENDING_REVIEW
    if any(comparison["values_match"] is not True for comparison in field_comparisons):
        return STATIC_VALUE_DIFFERENCE_PENDING_REVIEW
    return NO_STATIC_DIFFERENCE_RECORDED


def _build_source_summary(staleness_row: dict[str, Any]) -> dict[str, Any]:
    return {
        "operator_review_status": staleness_row["operator_review_status"],
        "source_artifact": dict(staleness_row["source_artifact"]),
        "source_domain": staleness_row["source_domain"],
        "source_evidence_link_id": staleness_row["source_evidence_link_id"],
        "source_id": staleness_row["source_id"],
        "source_label": staleness_row["source_label"],
        "source_type": staleness_row["source_type"],
        "staleness_check_id": staleness_row["check_id"],
        "staleness_state": staleness_row["staleness_state"],
        "timestamp_field": staleness_row["timestamp_field"],
    }


def _build_staleness_spec_summary(spec: dict[str, Any], reference: str) -> dict[str, Any]:
    return {
        **_build_digest_reference(reference),
        "build_id": spec["build_id"],
        "contract_version": spec["contract_version"],
        "operator_review_status": spec["operator_review"]["status"],
        "run_mode": spec["run_mode"],
        "source_staleness_checks": len(spec["source_staleness_checks"]),
        "spec_id": spec["spec_id"],
    }


def _build_digest_reference(reference: str) -> dict[str, Any]:
    normalized = _normalize_reference(reference)
    content = Path(normalized).read_bytes()
    return {
        "byte_count": len(content),
        "content_sha256": hashlib.sha256(content).hexdigest(),
        "local_reference": normalized,
        "present": True,
    }


def _source_staleness_rows_by_source_id(spec: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
    if not isinstance(spec, dict):
        return {}
    rows = spec.get("source_staleness_checks")
    if not isinstance(rows, list):
        return {}
    return {
        row["source_id"]: row
        for row in rows
        if isinstance(row, dict) and isinstance(row.get("source_id"), str)
    }


def _load_source_artifact(staleness_row: dict[str, Any]) -> dict[str, Any] | None:
    source_artifact = staleness_row.get("source_artifact")
    if not isinstance(source_artifact, dict) or not isinstance(source_artifact.get("local_reference"), str):
        return None
    return _load_json(Path(_normalize_reference(source_artifact["local_reference"])))


def _validate_staleness_spec_summary(value: Any, errors: list[str]) -> dict[str, Any] | None:
    path = "source_staleness_check_spec"
    if not isinstance(value, dict):
        errors.append(f"{path} must be an object")
        return None
    required_fields = (
        "build_id",
        "byte_count",
        "content_sha256",
        "contract_version",
        "local_reference",
        "operator_review_status",
        "present",
        "run_mode",
        "source_staleness_checks",
        "spec_id",
    )
    for field in required_fields:
        if field not in value:
            errors.append(f"{path} missing required field: {field}")
    for field in ("build_id", "content_sha256", "contract_version", "local_reference", "operator_review_status", "run_mode", "spec_id"):
        if not isinstance(value.get(field), str) or not value.get(field):
            errors.append(f"{path}.{field} must be a non-empty string")
    if value.get("present") is not True:
        errors.append(f"{path}.present must be true")
    if value.get("operator_review_status") != OPERATOR_REVIEW_STATUS:
        errors.append(f"{path}.operator_review_status must be {OPERATOR_REVIEW_STATUS}")
    if value.get("contract_version") != SOURCE_STALENESS_SPEC_CONTRACT_VERSION:
        errors.append(f"{path}.contract_version must be {SOURCE_STALENESS_SPEC_CONTRACT_VERSION}")
    if not isinstance(value.get("source_staleness_checks"), int) or isinstance(value.get("source_staleness_checks"), bool):
        errors.append(f"{path}.source_staleness_checks must be an integer")

    spec: dict[str, Any] | None = None
    reference = value.get("local_reference")
    if isinstance(reference, str):
        _validate_digest_reference(path, reference, value.get("byte_count"), value.get("content_sha256"), errors)
        try:
            spec = _load_json(Path(_normalize_reference(reference)))
        except (OSError, json.JSONDecodeError, SourceQualityLedgerValidationError) as exc:
            errors.append(f"{path}.local_reference must load a JSON object: {exc}")
        else:
            validation = validate_source_staleness_check_spec(spec)
            if not validation.valid:
                errors.extend(f"{path}.{error}" for error in validation.errors)
            for field in ("build_id", "contract_version", "run_mode", "spec_id"):
                if value.get(field) != spec.get(field):
                    errors.append(f"{path}.{field} must match local source staleness spec")
            if isinstance(value.get("source_staleness_checks"), int) and value.get("source_staleness_checks") != len(
                spec.get("source_staleness_checks", [])
            ):
                errors.append(f"{path}.source_staleness_checks must match local source staleness spec")
    return spec


def _validate_contradiction_rows(
    ledger_id: str,
    rows: list[Any],
    spec: dict[str, Any] | None,
    errors: list[str],
) -> dict[str, int]:
    seen_row_ids: set[str] = set()
    seen_request_check_ids: set[str] = set()
    local_references: set[str] = set()
    counts = {
        "different_field_comparisons": 0,
        "field_comparisons": 0,
        "local_references": 0,
        "matching_field_comparisons": 0,
        "review_checks": 0,
        "source_artifact_references": 0,
        "source_contradiction_rows": 0,
        "source_staleness_checks": 0,
        "subject_key_comparisons": 0,
        "subject_key_differences": 0,
    }
    spec_rows_by_source_id = _source_staleness_rows_by_source_id(spec)
    staleness_check_ids: set[str] = set()
    source_artifact_references: set[str] = set()
    for index, row in enumerate(rows):
        path = f"source_contradiction_rows[{index}]"
        if not isinstance(row, dict):
            errors.append(f"{path} must be an object")
            continue
        row_counts = _validate_contradiction_row(
            path,
            ledger_id,
            row,
            spec_rows_by_source_id,
            seen_row_ids,
            seen_request_check_ids,
            errors,
        )
        counts["different_field_comparisons"] += row_counts["different_field_comparisons"]
        counts["field_comparisons"] += row_counts["field_comparisons"]
        counts["matching_field_comparisons"] += row_counts["matching_field_comparisons"]
        counts["review_checks"] += row_counts["review_checks"]
        counts["source_contradiction_rows"] += 1
        counts["subject_key_comparisons"] += row_counts["subject_key_comparisons"]
        counts["subject_key_differences"] += row_counts["subject_key_differences"]
        local_references.update(row_counts["local_references"])
        source_artifact_references.update(row_counts["source_artifact_references"])
        staleness_check_ids.update(row_counts["source_staleness_checks"])
    counts["local_references"] = len(local_references)
    counts["source_artifact_references"] = len(source_artifact_references)
    counts["source_staleness_checks"] = len(staleness_check_ids)
    return counts


def _validate_contradiction_row(
    path: str,
    ledger_id: str,
    row: dict[str, Any],
    spec_rows_by_source_id: dict[str, dict[str, Any]],
    seen_row_ids: set[str],
    seen_request_check_ids: set[str],
    errors: list[str],
) -> dict[str, Any]:
    required_fields = (
        "check_label",
        "comparison_kind",
        "contradiction_state",
        "field_comparisons",
        "known_limitations",
        "left_source",
        "operator_review_status",
        "request_check_id",
        "review_checks",
        "right_source",
        "row_id",
        "row_state",
        "source_domain",
        "subject_key_comparisons",
    )
    for field in required_fields:
        if field not in row:
            errors.append(f"{path} missing required field: {field}")
    for field in ("check_label", "comparison_kind", "contradiction_state", "request_check_id", "row_id", "row_state", "source_domain"):
        if not isinstance(row.get(field), str) or not row.get(field):
            errors.append(f"{path}.{field} must be a non-empty string")
    if row.get("comparison_kind") != MAPPED_FIELD_VALUE_COMPARE:
        errors.append(f"{path}.comparison_kind must be {MAPPED_FIELD_VALUE_COMPARE}")
    if row.get("row_state") != CONTRADICTION_ROW_STATE:
        errors.append(f"{path}.row_state must be {CONTRADICTION_ROW_STATE}")
    if row.get("operator_review_status") != OPERATOR_REVIEW_STATUS:
        errors.append(f"{path}.operator_review_status must be {OPERATOR_REVIEW_STATUS}")
    if not _is_string_list(row.get("known_limitations")):
        errors.append(f"{path}.known_limitations must be a list of strings")

    row_id = row.get("row_id")
    request_check_id = row.get("request_check_id")
    if isinstance(row_id, str):
        if row_id in seen_row_ids:
            errors.append(f"{path}.row_id duplicates an earlier row")
        seen_row_ids.add(row_id)
    if isinstance(request_check_id, str):
        if request_check_id in seen_request_check_ids:
            errors.append(f"{path}.request_check_id duplicates an earlier row")
        seen_request_check_ids.add(request_check_id)
        if row_id != f"{ledger_id}.{request_check_id}.source_contradiction_review":
            errors.append(f"{path}.row_id must be derived from ledger_id and request_check_id")

    left_artifact = _validate_source_summary(f"{path}.left_source", row.get("left_source"), spec_rows_by_source_id, errors)
    right_artifact = _validate_source_summary(f"{path}.right_source", row.get("right_source"), spec_rows_by_source_id, errors)
    left_source = row.get("left_source") if isinstance(row.get("left_source"), dict) else {}
    right_source = row.get("right_source") if isinstance(row.get("right_source"), dict) else {}
    if row.get("source_domain") != left_source.get("source_domain"):
        errors.append(f"{path}.source_domain must match left_source.source_domain")
    if row.get("source_domain") != right_source.get("source_domain"):
        errors.append(f"{path}.source_domain must match right_source.source_domain")

    subject_counts = _validate_subject_key_comparisons(
        path,
        row.get("subject_key_comparisons"),
        left_artifact,
        right_artifact,
        errors,
    )
    field_counts = _validate_field_comparisons(
        path,
        row.get("field_comparisons"),
        left_artifact,
        right_artifact,
        errors,
    )
    expected_state = _contradiction_state_from_counts(subject_counts, field_counts)
    if row.get("contradiction_state") != expected_state:
        errors.append(f"{path}.contradiction_state must be {expected_state}")

    review_check_count = _validate_review_checks(path, row.get("review_checks"), errors)
    local_references: set[str] = set()
    source_artifact_references: set[str] = set()
    staleness_check_ids: set[str] = set()
    for source in (left_source, right_source):
        source_artifact = source.get("source_artifact") if isinstance(source, dict) else None
        if isinstance(source_artifact, dict) and isinstance(source_artifact.get("local_reference"), str):
            reference = _normalize_reference(source_artifact["local_reference"])
            local_references.add(reference)
            source_artifact_references.add(reference)
        staleness_check_id = source.get("staleness_check_id") if isinstance(source, dict) else None
        if isinstance(staleness_check_id, str):
            staleness_check_ids.add(staleness_check_id)

    return {
        "different_field_comparisons": field_counts["different"],
        "field_comparisons": field_counts["total"],
        "local_references": local_references,
        "matching_field_comparisons": field_counts["matching"],
        "review_checks": review_check_count,
        "source_artifact_references": source_artifact_references,
        "source_staleness_checks": staleness_check_ids,
        "subject_key_comparisons": subject_counts["total"],
        "subject_key_differences": subject_counts["different"],
    }


def _validate_source_summary(
    path: str,
    value: Any,
    spec_rows_by_source_id: dict[str, dict[str, Any]],
    errors: list[str],
) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        errors.append(f"{path} must be an object")
        return None
    required_fields = (
        "operator_review_status",
        "source_artifact",
        "source_domain",
        "source_evidence_link_id",
        "source_id",
        "source_label",
        "source_type",
        "staleness_check_id",
        "staleness_state",
        "timestamp_field",
    )
    for field in required_fields:
        if field not in value:
            errors.append(f"{path} missing required field: {field}")
    for field in ("operator_review_status", "source_domain", "source_evidence_link_id", "source_id", "source_label", "source_type", "staleness_check_id", "staleness_state"):
        if not isinstance(value.get(field), str) or not value.get(field):
            errors.append(f"{path}.{field} must be a non-empty string")
    if value.get("operator_review_status") != OPERATOR_REVIEW_STATUS:
        errors.append(f"{path}.operator_review_status must be {OPERATOR_REVIEW_STATUS}")
    if value.get("timestamp_field") is not None and (not isinstance(value.get("timestamp_field"), str) or not value.get("timestamp_field")):
        errors.append(f"{path}.timestamp_field must be a non-empty string or null")

    artifact_reference = _validate_source_artifact(path, value.get("source_artifact"), errors)
    source_id = value.get("source_id")
    spec_row = spec_rows_by_source_id.get(source_id) if isinstance(source_id, str) else None
    if spec_row is None:
        errors.append(f"{path}.source_id must exist in source staleness spec")
    else:
        field_pairs = (
            ("source_domain", "source_domain"),
            ("source_evidence_link_id", "source_evidence_link_id"),
            ("source_label", "source_label"),
            ("source_type", "source_type"),
            ("staleness_check_id", "check_id"),
            ("staleness_state", "staleness_state"),
            ("timestamp_field", "timestamp_field"),
        )
        for value_field, spec_field in field_pairs:
            if value.get(value_field) != spec_row.get(spec_field):
                errors.append(f"{path}.{value_field} must match source staleness spec row")
        source_artifact = value.get("source_artifact")
        spec_artifact = spec_row.get("source_artifact")
        if isinstance(source_artifact, dict) and isinstance(spec_artifact, dict):
            for field in ("artifact_format", "byte_count", "content_sha256", "local_reference", "present", "source_artifact_present"):
                if source_artifact.get(field) != spec_artifact.get(field):
                    errors.append(f"{path}.source_artifact.{field} must match source staleness spec row")

    if artifact_reference is None:
        return None
    try:
        return _load_json(Path(artifact_reference))
    except (OSError, json.JSONDecodeError, SourceQualityLedgerValidationError) as exc:
        errors.append(f"{path}.source_artifact.local_reference must load a JSON object: {exc}")
        return None


def _validate_source_artifact(path: str, value: Any, errors: list[str]) -> str | None:
    artifact_path = f"{path}.source_artifact"
    if not isinstance(value, dict):
        errors.append(f"{artifact_path} must be an object")
        return None
    required_fields = (
        "artifact_format",
        "byte_count",
        "content_sha256",
        "local_reference",
        "present",
        "source_artifact_present",
    )
    for field in required_fields:
        if field not in value:
            errors.append(f"{artifact_path} missing required field: {field}")
    if value.get("artifact_format") != "json_object":
        errors.append(f"{artifact_path}.artifact_format must be json_object")
    if value.get("source_artifact_present") is not True:
        errors.append(f"{artifact_path}.source_artifact_present must be true")
    return _validate_reference_object(artifact_path, value, errors)


def _validate_subject_key_comparisons(
    row_path: str,
    comparisons: Any,
    left_artifact: dict[str, Any] | None,
    right_artifact: dict[str, Any] | None,
    errors: list[str],
) -> dict[str, int]:
    counts = {"different": 0, "total": 0}
    if not isinstance(comparisons, list) or not comparisons:
        errors.append(f"{row_path}.subject_key_comparisons must be a non-empty list")
        return counts
    seen_fields: set[str] = set()
    for index, comparison in enumerate(comparisons):
        path = f"{row_path}.subject_key_comparisons[{index}]"
        counts["total"] += 1
        if not isinstance(comparison, dict):
            errors.append(f"{path} must be an object")
            continue
        required_fields = ("field_name", "left_value", "operator_review_status", "right_value", "values_match")
        for field in required_fields:
            if field not in comparison:
                errors.append(f"{path} missing required field: {field}")
        field_name = comparison.get("field_name")
        if not isinstance(field_name, str) or not field_name:
            errors.append(f"{path}.field_name must be a non-empty string")
        elif field_name in seen_fields:
            errors.append(f"{path}.field_name duplicates an earlier subject key")
        else:
            seen_fields.add(field_name)
        if comparison.get("operator_review_status") != OPERATOR_REVIEW_STATUS:
            errors.append(f"{path}.operator_review_status must be {OPERATOR_REVIEW_STATUS}")
        if comparison.get("values_match") not in (True, False):
            errors.append(f"{path}.values_match must be a boolean")
        elif comparison.get("values_match") is False:
            counts["different"] += 1
        if left_artifact is None or right_artifact is None or not isinstance(field_name, str):
            continue
        if field_name not in left_artifact:
            errors.append(f"{path}.field_name must exist in left source artifact")
            continue
        if field_name not in right_artifact:
            errors.append(f"{path}.field_name must exist in right source artifact")
            continue
        expected_left = left_artifact[field_name]
        expected_right = right_artifact[field_name]
        if comparison.get("left_value") != expected_left:
            errors.append(f"{path}.left_value must match left source artifact")
        if comparison.get("right_value") != expected_right:
            errors.append(f"{path}.right_value must match right source artifact")
        if comparison.get("values_match") != (expected_left == expected_right):
            errors.append(f"{path}.values_match must match local source artifact values")
    return counts


def _validate_field_comparisons(
    row_path: str,
    comparisons: Any,
    left_artifact: dict[str, Any] | None,
    right_artifact: dict[str, Any] | None,
    errors: list[str],
) -> dict[str, int]:
    counts = {"different": 0, "matching": 0, "total": 0}
    if not isinstance(comparisons, list) or not comparisons:
        errors.append(f"{row_path}.field_comparisons must be a non-empty list")
        return counts
    seen_semantic_fields: set[str] = set()
    for index, comparison in enumerate(comparisons):
        path = f"{row_path}.field_comparisons[{index}]"
        counts["total"] += 1
        if not isinstance(comparison, dict):
            errors.append(f"{path} must be an object")
            continue
        required_fields = (
            "comparison_state",
            "left_field",
            "left_value",
            "operator_review_status",
            "right_field",
            "right_value",
            "semantic_field",
            "unit_label",
            "values_match",
        )
        for field in required_fields:
            if field not in comparison:
                errors.append(f"{path} missing required field: {field}")
        for field in ("comparison_state", "left_field", "operator_review_status", "right_field", "semantic_field", "unit_label"):
            if not isinstance(comparison.get(field), str) or not comparison.get(field):
                errors.append(f"{path}.{field} must be a non-empty string")
        semantic_field = comparison.get("semantic_field")
        if isinstance(semantic_field, str):
            if semantic_field in seen_semantic_fields:
                errors.append(f"{path}.semantic_field duplicates an earlier field comparison")
            seen_semantic_fields.add(semantic_field)
        if comparison.get("operator_review_status") != OPERATOR_REVIEW_STATUS:
            errors.append(f"{path}.operator_review_status must be {OPERATOR_REVIEW_STATUS}")
        if comparison.get("values_match") not in (True, False):
            errors.append(f"{path}.values_match must be a boolean")
        elif comparison.get("values_match") is True:
            counts["matching"] += 1
        else:
            counts["different"] += 1
        expected_state = MATCHING_STATIC_VALUES if comparison.get("values_match") is True else DIFFERENT_STATIC_VALUES_PENDING_REVIEW
        if comparison.get("comparison_state") != expected_state:
            errors.append(f"{path}.comparison_state must be {expected_state}")

        left_field = comparison.get("left_field")
        right_field = comparison.get("right_field")
        if left_artifact is None or right_artifact is None:
            continue
        if not isinstance(left_field, str) or left_field not in left_artifact:
            errors.append(f"{path}.left_field must exist in left source artifact")
            continue
        if not isinstance(right_field, str) or right_field not in right_artifact:
            errors.append(f"{path}.right_field must exist in right source artifact")
            continue
        expected_left = left_artifact[left_field]
        expected_right = right_artifact[right_field]
        if comparison.get("left_value") != expected_left:
            errors.append(f"{path}.left_value must match left source artifact")
        if comparison.get("right_value") != expected_right:
            errors.append(f"{path}.right_value must match right source artifact")
        if comparison.get("values_match") != (expected_left == expected_right):
            errors.append(f"{path}.values_match must match local source artifact values")
    return counts


def _contradiction_state_from_counts(subject_counts: dict[str, int], field_counts: dict[str, int]) -> str:
    if subject_counts["different"]:
        return SUBJECT_KEY_DIFFERENCE_PENDING_REVIEW
    if field_counts["different"]:
        return STATIC_VALUE_DIFFERENCE_PENDING_REVIEW
    return NO_STATIC_DIFFERENCE_RECORDED


def _validate_reference_object(path: str, value: Any, errors: list[str]) -> str | None:
    if not isinstance(value, dict):
        errors.append(f"{path} must be an object")
        return None
    required_fields = ("byte_count", "content_sha256", "local_reference", "present")
    for field in required_fields:
        if field not in value:
            errors.append(f"{path} missing required field: {field}")
    if value.get("present") is not True:
        errors.append(f"{path}.present must be true")
    reference = value.get("local_reference")
    if not isinstance(reference, str):
        errors.append(f"{path}.local_reference must be a string")
        return None
    _validate_digest_reference(path, reference, value.get("byte_count"), value.get("content_sha256"), errors)
    return _normalize_reference(reference)


def _validate_digest_reference(
    path: str,
    reference: str,
    byte_count: Any,
    content_sha256: Any,
    errors: list[str],
) -> None:
    reference_errors = _validate_local_reference(reference)
    errors.extend(f"{path}.{error}" for error in reference_errors)
    if reference_errors:
        return
    local_path = Path(_normalize_reference(reference))
    try:
        content = local_path.read_bytes()
    except OSError as exc:
        errors.append(f"{path}.local_reference must be readable: {exc}")
        return
    if byte_count is not None and byte_count != len(content):
        errors.append(f"{path}.byte_count must match local bytes")
    if content_sha256 is not None and content_sha256 != hashlib.sha256(content).hexdigest():
        errors.append(f"{path}.content_sha256 must match local bytes")


def _validate_review_checks(row_path: str, review_checks: Any, errors: list[str]) -> int:
    if not _is_non_empty_review_check_list(review_checks):
        errors.append(f"{row_path}.review_checks must be a non-empty list of check objects")
        return 0
    seen_check_ids: set[str] = set()
    for index, check in enumerate(review_checks):
        path = f"{row_path}.review_checks[{index}]"
        check_id = check["check_id"]
        if check_id in seen_check_ids:
            errors.append(f"{path}.check_id duplicates an earlier review check")
        seen_check_ids.add(check_id)
        if check.get("operator_review_status") != OPERATOR_REVIEW_STATUS:
            errors.append(f"{path}.operator_review_status must be {OPERATOR_REVIEW_STATUS}")
    return len(review_checks)


def _summary_counts(
    rows: list[dict[str, Any]],
    operator_review_steps: list[str],
    warnings: list[str],
    spec_reference: str,
    report_reference: str,
    documentation_reference: str,
) -> dict[str, int]:
    local_references = {
        spec_reference,
        report_reference,
        documentation_reference,
    }
    source_artifact_references: set[str] = set()
    staleness_check_ids: set[str] = set()
    for row in rows:
        for source_key in ("left_source", "right_source"):
            source = row[source_key]
            reference = source["source_artifact"]["local_reference"]
            local_references.add(reference)
            source_artifact_references.add(reference)
            staleness_check_ids.add(source["staleness_check_id"])
    return {
        "different_field_comparisons": sum(
            1
            for row in rows
            for comparison in row["field_comparisons"]
            if comparison["values_match"] is False
        ),
        "field_comparisons": sum(len(row["field_comparisons"]) for row in rows),
        "local_references": len(local_references),
        "matching_field_comparisons": sum(
            1
            for row in rows
            for comparison in row["field_comparisons"]
            if comparison["values_match"] is True
        ),
        "operator_review_steps": len(operator_review_steps),
        "review_checks": sum(len(row["review_checks"]) for row in rows),
        "source_artifact_references": len(source_artifact_references),
        "source_contradiction_rows": len(rows),
        "source_staleness_checks": len(staleness_check_ids),
        "subject_key_comparisons": sum(len(row["subject_key_comparisons"]) for row in rows),
        "subject_key_differences": sum(
            1
            for row in rows
            for comparison in row["subject_key_comparisons"]
            if comparison["values_match"] is False
        ),
        "warnings": len(warnings),
    }


def _count_ledger_local_references(ledger: dict[str, Any], row_local_reference_count: int) -> int:
    local_references: set[str] = set()
    for field in ("documentation", "source_staleness_check_report", "source_staleness_check_spec"):
        value = ledger.get(field)
        if isinstance(value, dict) and isinstance(value.get("local_reference"), str):
            local_references.add(_normalize_reference(value["local_reference"]))
    row_references: set[str] = set()
    rows = ledger.get("source_contradiction_rows")
    if isinstance(rows, list):
        for row in rows:
            if not isinstance(row, dict):
                continue
            for source_key in ("left_source", "right_source"):
                source = row.get(source_key)
                if not isinstance(source, dict):
                    continue
                source_artifact = source.get("source_artifact")
                if isinstance(source_artifact, dict) and isinstance(source_artifact.get("local_reference"), str):
                    row_references.add(_normalize_reference(source_artifact["local_reference"]))
    if not row_references and row_local_reference_count:
        return len(local_references) + row_local_reference_count
    local_references.update(row_references)
    return len(local_references)


def _build_deterministic_id(
    ledger_id: str,
    request: dict[str, Any],
    spec: dict[str, Any],
    rows: list[dict[str, Any]],
) -> str:
    digest_input = {
        "ledger_id": ledger_id,
        "request": request,
        "rows": rows,
        "source_staleness_check_spec": spec,
    }
    digest = hashlib.sha256(_canonical_json(digest_input).encode("utf-8")).hexdigest()[:BUILD_ID_DIGEST_LENGTH]
    return f"{ledger_id}-{digest}"


def _validate_build_id(ledger_id: str, build_id: Any, errors: list[str]) -> None:
    if not isinstance(build_id, str) or not build_id:
        errors.append("build_id must be a non-empty string")
        return
    prefix = f"{ledger_id}-"
    if not build_id.startswith(prefix):
        errors.append("build_id must start with ledger_id followed by a digest")
        return
    digest = build_id[len(prefix):]
    if len(digest) != BUILD_ID_DIGEST_LENGTH or any(character not in "0123456789abcdef" for character in digest):
        errors.append(f"build_id digest must be {BUILD_ID_DIGEST_LENGTH} lowercase hex characters")


if __name__ == "__main__":
    raise SystemExit(main())
