from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pm_bot.source_quality.source_evidence_inventory_ledger import (
    EXPECTED_SAFETY_BOUNDARIES,
    OPERATOR_REVIEW_STATUS,
    SourceQualityLedgerValidation,
    SourceQualityLedgerValidationError,
    _find_forbidden_evidence_terms,
)
from pm_bot.source_quality.source_evidence_link_map import (
    LINK_MAP_CONTRACT_VERSION as SOURCE_EVIDENCE_LINK_MAP_CONTRACT_VERSION,
    validate_source_evidence_link_map,
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

REQUEST_CONTRACT_VERSION = "pmbot_source_staleness_check_spec_request.v1"
SPEC_CONTRACT_VERSION = "pmbot_source_staleness_check_spec.v1"
SPEC_SCOPE = "source_staleness_check_spec"
SPEC_RUN_MODE = "local_static_source_staleness_check_spec"
CHECK_ROW_STATE = "descriptive_source_staleness_check"
BUILD_ID_DIGEST_LENGTH = 12
SAMPLE_SPEC_PATH = "pm_bot/source_quality/samples/source_staleness_check_spec.fixture.json"
SAMPLE_OPERATOR_REPORT_PATH = "pm_bot/source_quality/samples/source_staleness_check_spec.fixture.md"

REFERENCE_CLOCK_SOURCE = "request_fixture_static_value"
WITHIN_STATIC_REVIEW_WINDOW = "within_static_review_window"
OUTSIDE_STATIC_REVIEW_WINDOW = "outside_static_review_window"
TIMESTAMP_AFTER_REFERENCE_CLOCK = "timestamp_after_reference_clock"
TIMESTAMP_FIELD_MISSING = "timestamp_field_missing"
TIMESTAMP_NOT_REQUIRED_BY_RULE = "timestamp_not_required_by_rule"


def load_source_staleness_check_spec_request(path: str | Path) -> dict[str, Any]:
    reference = str(path)
    errors = _validate_local_reference(reference)
    if errors:
        raise SourceQualityLedgerValidationError(tuple(errors))
    return _load_json(Path(_normalize_reference(reference)))


def build_source_staleness_check_spec(request: dict[str, Any]) -> dict[str, Any]:
    validation = validate_source_staleness_check_spec_request(request)
    if not validation.valid:
        raise SourceQualityLedgerValidationError(validation.errors)

    link_map_reference = _normalize_reference(request["source_evidence_link_map_reference"])
    link_report_reference = _normalize_reference(request["source_evidence_link_report_reference"])
    documentation_reference = _normalize_reference(request["documentation_reference"])
    link_map = _load_json(Path(link_map_reference))
    rules_by_source_id = {
        rule["source_id"]: rule
        for rule in request["source_staleness_rules"]
    }
    reference_timestamp = request["reference_timestamp_utc"]
    warnings: list[str] = []
    rows = [
        _build_check_row(
            spec_id=request["spec_id"],
            link_row=link_row,
            rule=rules_by_source_id[link_row["source_id"]],
            reference_timestamp=reference_timestamp,
            request=request,
        )
        for link_row in link_map["source_evidence_links"]
    ]
    rows = sorted(rows, key=lambda row: row["source_id"])
    spec = {
        "build_id": _build_deterministic_id(request["spec_id"], request, link_map, rows),
        "contract_version": SPEC_CONTRACT_VERSION,
        "documentation": _build_digest_reference(documentation_reference),
        "errors": [],
        "local_only": True,
        "operator_review": {
            "status": OPERATOR_REVIEW_STATUS,
            "steps": list(request["operator_review_steps"]),
        },
        "operator_review_required": True,
        "reference_clock": {
            "reference_source": REFERENCE_CLOCK_SOURCE,
            "reference_timestamp_utc": reference_timestamp,
            "system_clock_used": False,
        },
        "run_mode": SPEC_RUN_MODE,
        "safety_boundaries": dict(EXPECTED_SAFETY_BOUNDARIES),
        "scope": SPEC_SCOPE,
        "source_evidence_link_map": _build_link_map_summary(link_map, link_map_reference),
        "source_evidence_link_report": _build_digest_reference(link_report_reference),
        "source_staleness_checks": rows,
        "spec_id": request["spec_id"],
        "summary_counts": _summary_counts(
            rows,
            request["operator_review_steps"],
            warnings,
            link_map_reference,
            link_report_reference,
            documentation_reference,
        ),
        "warnings": warnings,
    }
    return spec


def validate_source_staleness_check_spec_request(request: dict[str, Any]) -> SourceQualityLedgerValidation:
    errors: list[str] = []
    if not isinstance(request, dict):
        return SourceQualityLedgerValidation(valid=False, errors=("request must be an object",))

    required_fields = (
        "contract_version",
        "documentation_reference",
        "known_limitations",
        "local_only",
        "operator_review_required",
        "operator_review_steps",
        "reference_timestamp_utc",
        "review_checks",
        "scope",
        "source_evidence_link_map_reference",
        "source_evidence_link_report_reference",
        "source_staleness_rules",
        "spec_id",
    )
    for field in required_fields:
        if field not in request:
            errors.append(f"missing required request field: {field}")

    if request.get("contract_version") != REQUEST_CONTRACT_VERSION:
        errors.append(f"contract_version must be {REQUEST_CONTRACT_VERSION}")
    if request.get("scope") != SPEC_SCOPE:
        errors.append(f"scope must be {SPEC_SCOPE}")
    if request.get("local_only") is not True:
        errors.append("local_only must be true")
    if request.get("operator_review_required") is not True:
        errors.append("operator_review_required must be true")
    if not isinstance(request.get("spec_id"), str) or not request.get("spec_id"):
        errors.append("spec_id must be a non-empty string")
    if not _is_non_empty_string_list(request.get("operator_review_steps")):
        errors.append("operator_review_steps must be a non-empty list of strings")
    if not _is_non_empty_review_check_list(request.get("review_checks")):
        errors.append("review_checks must be a non-empty list of check objects")
    if not _is_string_list(request.get("known_limitations")):
        errors.append("known_limitations must be a list of strings")

    reference_timestamp = request.get("reference_timestamp_utc")
    if not isinstance(reference_timestamp, str) or not reference_timestamp:
        errors.append("reference_timestamp_utc must be a non-empty string")
    else:
        _parse_utc_timestamp("reference_timestamp_utc", reference_timestamp, errors)

    forbidden_paths = _find_forbidden_evidence_terms(request)
    if forbidden_paths:
        errors.append(
            "forbidden source evidence term detected in request at: "
            + ", ".join(sorted(forbidden_paths))
        )

    link_map: dict[str, Any] | None = None
    for field in (
        "documentation_reference",
        "source_evidence_link_map_reference",
        "source_evidence_link_report_reference",
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

    link_map_reference = request.get("source_evidence_link_map_reference")
    if isinstance(link_map_reference, str) and not _validate_local_reference(link_map_reference):
        try:
            link_map = _load_json(Path(_normalize_reference(link_map_reference)))
        except (OSError, json.JSONDecodeError, SourceQualityLedgerValidationError) as exc:
            errors.append(f"source_evidence_link_map_reference must load a JSON object: {exc}")
        else:
            link_map_validation = validate_source_evidence_link_map(link_map)
            if not link_map_validation.valid:
                errors.extend(
                    f"source_evidence_link_map_reference.{error}"
                    for error in link_map_validation.errors
                )
            if link_map.get("contract_version") != SOURCE_EVIDENCE_LINK_MAP_CONTRACT_VERSION:
                errors.append(
                    "source_evidence_link_map_reference contract_version must be "
                    + SOURCE_EVIDENCE_LINK_MAP_CONTRACT_VERSION
                )

    rules = request.get("source_staleness_rules")
    if not isinstance(rules, list) or not rules:
        errors.append("source_staleness_rules must be a non-empty list")
    else:
        errors.extend(_validate_source_staleness_rules(rules, link_map))

    return SourceQualityLedgerValidation(valid=not errors, errors=tuple(errors))


def validate_source_staleness_check_spec(spec: dict[str, Any]) -> SourceQualityLedgerValidation:
    errors: list[str] = []
    if not isinstance(spec, dict):
        return SourceQualityLedgerValidation(valid=False, errors=("spec must be an object",))

    required_fields = (
        "build_id",
        "contract_version",
        "documentation",
        "errors",
        "local_only",
        "operator_review",
        "operator_review_required",
        "reference_clock",
        "run_mode",
        "safety_boundaries",
        "scope",
        "source_evidence_link_map",
        "source_evidence_link_report",
        "source_staleness_checks",
        "spec_id",
        "summary_counts",
        "warnings",
    )
    for field in required_fields:
        if field not in spec:
            errors.append(f"missing required spec field: {field}")

    if spec.get("contract_version") != SPEC_CONTRACT_VERSION:
        errors.append(f"contract_version must be {SPEC_CONTRACT_VERSION}")
    if spec.get("scope") != SPEC_SCOPE:
        errors.append(f"scope must be {SPEC_SCOPE}")
    if spec.get("run_mode") != SPEC_RUN_MODE:
        errors.append(f"run_mode must be {SPEC_RUN_MODE}")
    if spec.get("local_only") is not True:
        errors.append("local_only must be true")
    if spec.get("operator_review_required") is not True:
        errors.append("operator_review_required must be true")
    if spec.get("errors") != []:
        errors.append("errors must be an empty list")
    if not _is_string_list(spec.get("warnings")):
        errors.append("warnings must be a list of strings")
    if spec.get("safety_boundaries") != EXPECTED_SAFETY_BOUNDARIES:
        errors.append("safety_boundaries must match the local-only source evidence boundary")

    spec_id = spec.get("spec_id")
    if not isinstance(spec_id, str) or not spec_id:
        errors.append("spec_id must be a non-empty string")
        spec_id_for_rows = ""
    else:
        spec_id_for_rows = spec_id
        _validate_build_id(spec_id, spec.get("build_id"), errors)

    _validate_operator_review_block(spec.get("operator_review"), "operator_review", errors)

    forbidden_paths = _find_forbidden_evidence_terms(spec)
    if forbidden_paths:
        errors.append(
            "forbidden source evidence term detected in spec at: "
            + ", ".join(sorted(forbidden_paths))
        )

    reference_timestamp = _validate_reference_clock(spec.get("reference_clock"), errors)
    link_map = _validate_link_map_summary(spec.get("source_evidence_link_map"), errors)
    _validate_reference_object("source_evidence_link_report", spec.get("source_evidence_link_report"), errors)
    _validate_reference_object("documentation", spec.get("documentation"), errors)

    rows = spec.get("source_staleness_checks")
    row_counts: dict[str, int] | None = None
    if not isinstance(rows, list) or not rows:
        errors.append("source_staleness_checks must be a non-empty list")
    else:
        row_counts = _validate_check_rows(spec_id_for_rows, rows, reference_timestamp, link_map, errors)

    if row_counts is not None:
        operator_review = spec.get("operator_review")
        operator_steps = operator_review.get("steps") if isinstance(operator_review, dict) else []
        warnings = spec.get("warnings") if isinstance(spec.get("warnings"), list) else []
        expected_counts = dict(row_counts)
        expected_counts["local_references"] = _count_spec_local_references(spec, expected_counts["local_references"])
        expected_counts["operator_review_steps"] = len(operator_steps) if isinstance(operator_steps, list) else 0
        expected_counts["warnings"] = len(warnings)
        if spec.get("summary_counts") != expected_counts:
            errors.append("summary_counts must match source_staleness_checks totals: " + _canonical_json(expected_counts))

    return SourceQualityLedgerValidation(valid=not errors, errors=tuple(errors))


def build_operator_report(spec: dict[str, Any]) -> str:
    lines: list[str] = [
        "# PMBOT Source Staleness Check Spec",
        "",
        f"Spec: `{spec['spec_id']}`",
        f"Build: `{spec['build_id']}`",
        f"Run mode: `{spec['run_mode']}`",
        f"Operator review: `{spec['operator_review']['status']}`",
        "",
        "## Static Reference Clock",
        "",
        f"- Reference timestamp: `{spec['reference_clock']['reference_timestamp_utc']}`",
        f"- Reference source: `{spec['reference_clock']['reference_source']}`",
        f"- System clock used: `{str(spec['reference_clock']['system_clock_used']).lower()}`",
        "",
        "## Summary Counts",
        "",
        f"- Source staleness checks: {spec['summary_counts']['source_staleness_checks']}",
        f"- Source evidence links: {spec['summary_counts']['source_evidence_links']}",
        f"- Source artifact references: {spec['summary_counts']['source_artifact_references']}",
        f"- Timestamp fields present: {spec['summary_counts']['timestamp_fields_present']}",
        f"- Timestamp fields missing: {spec['summary_counts']['timestamp_fields_missing']}",
        f"- Local references: {spec['summary_counts']['local_references']}",
        f"- Review checks: {spec['summary_counts']['review_checks']}",
        "",
        "## Source Evidence Link Map",
        "",
        f"- Link map: `{spec['source_evidence_link_map']['local_reference']}`",
        f"- Map: `{spec['source_evidence_link_map']['map_id']}`",
        f"- Build: `{spec['source_evidence_link_map']['build_id']}`",
        f"- Rows: {spec['source_evidence_link_map']['source_evidence_links']}",
        "",
        "## Source Staleness Checks",
        "",
    ]
    for row in spec["source_staleness_checks"]:
        timestamp_field = row["timestamp_field"] if row["timestamp_field"] is not None else "not required by rule"
        age_seconds = row["age_seconds"] if row["age_seconds"] is not None else "not recorded"
        lines.extend(
            [
                f"- `{row['source_id']}` ({row['source_label']})",
                f"  - Source artifact: `{row['source_artifact']['local_reference']}`",
                f"  - Source evidence link: `{row['source_evidence_link_id']}`",
                f"  - Timestamp field: `{timestamp_field}`",
                f"  - Age seconds: `{age_seconds}`",
                f"  - Staleness state: `{row['staleness_state']}`",
                f"  - Review checks: {len(row['review_checks'])} pending operator review",
            ]
        )

    lines.extend(["", "## Operator Review Steps", ""])
    for step in spec["operator_review"]["steps"]:
        lines.append(f"- {step}")

    lines.extend(
        [
            "",
            "## Safety",
            "",
            "- Local fixture/static input only.",
            "- Uses the request fixture reference timestamp, not the system clock.",
            "- Makes no network, LLM, endpoint, wallet, order, runtime, browser, scheduler, or worker calls.",
            "- Records descriptive age windows, digests, and pending review state only.",
            "- Does not authorize execution and is not runtime input.",
        ]
    )
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a local PMBOT source staleness check spec.")
    parser.add_argument("--request", required=True, help="Local source staleness check spec request JSON.")
    parser.add_argument("--output-spec", required=True, help="Output source staleness check spec JSON path.")
    parser.add_argument("--output-report", required=True, help="Output operator report Markdown path.")
    args = parser.parse_args(argv)

    request = load_source_staleness_check_spec_request(args.request)
    spec = build_source_staleness_check_spec(request)
    report = build_operator_report(spec)

    _write_json(Path(args.output_spec), spec)
    Path(args.output_report).write_text(report, encoding="utf-8")
    return 0


def _validate_source_staleness_rules(
    rules: list[Any],
    link_map: dict[str, Any] | None,
) -> list[str]:
    errors: list[str] = []
    seen_rule_ids: set[str] = set()
    seen_source_ids: set[str] = set()
    required_fields = (
        "maximum_age_seconds",
        "rule_id",
        "source_id",
        "threshold_label",
        "timestamp_field_candidates",
        "timestamp_required",
    )
    for index, rule in enumerate(rules):
        path = f"source_staleness_rules[{index}]"
        if not isinstance(rule, dict):
            errors.append(f"{path} must be an object")
            continue
        for field in required_fields:
            if field not in rule:
                errors.append(f"{path} missing required field: {field}")

        rule_id = rule.get("rule_id")
        source_id = rule.get("source_id")
        for field in ("rule_id", "source_id", "threshold_label"):
            if not isinstance(rule.get(field), str) or not rule.get(field):
                errors.append(f"{path}.{field} must be a non-empty string")

        if isinstance(rule_id, str):
            if rule_id in seen_rule_ids:
                errors.append(f"{path}.rule_id duplicates an earlier rule")
            seen_rule_ids.add(rule_id)
        if isinstance(source_id, str):
            if source_id in seen_source_ids:
                errors.append(f"{path}.source_id duplicates an earlier rule")
            seen_source_ids.add(source_id)

        if rule.get("timestamp_required") not in (True, False):
            errors.append(f"{path}.timestamp_required must be a boolean")
        candidates = rule.get("timestamp_field_candidates")
        if not isinstance(candidates, list) or not all(isinstance(item, str) and item for item in candidates):
            errors.append(f"{path}.timestamp_field_candidates must be a list of strings")
        if rule.get("timestamp_required") is True and not candidates:
            errors.append(f"{path}.timestamp_field_candidates must be non-empty when timestamp_required is true")

        maximum_age_seconds = rule.get("maximum_age_seconds")
        if rule.get("timestamp_required") is True:
            if not isinstance(maximum_age_seconds, int) or isinstance(maximum_age_seconds, bool) or maximum_age_seconds <= 0:
                errors.append(f"{path}.maximum_age_seconds must be a positive integer when timestamp_required is true")
        elif maximum_age_seconds is not None:
            errors.append(f"{path}.maximum_age_seconds must be null when timestamp_required is false")

    if link_map is not None:
        expected_source_ids = {
            row["source_id"]
            for row in link_map.get("source_evidence_links", [])
            if isinstance(row, dict) and isinstance(row.get("source_id"), str)
        }
        if seen_source_ids != expected_source_ids:
            errors.append(
                "source_staleness_rules source_id set must match source_evidence_link_map sources: "
                + ", ".join(sorted(expected_source_ids))
            )

    return errors


def _build_check_row(
    spec_id: str,
    link_row: dict[str, Any],
    rule: dict[str, Any],
    reference_timestamp: str,
    request: dict[str, Any],
) -> dict[str, Any]:
    artifact_reference = _normalize_reference(link_row["source_artifact"]["local_reference"])
    artifact = _load_json(Path(artifact_reference))
    timestamp_field = _select_timestamp_field(artifact, rule["timestamp_field_candidates"])
    observed_timestamp = artifact[timestamp_field] if timestamp_field is not None else None
    age_seconds: int | None = None
    if isinstance(observed_timestamp, str):
        age_seconds = _age_seconds(observed_timestamp, reference_timestamp)
    return {
        "age_seconds": age_seconds,
        "check_id": f"{spec_id}.{link_row['source_id']}.source_staleness_check",
        "check_kind": "local_static_source_staleness_review",
        "check_state": CHECK_ROW_STATE,
        "known_limitations": list(request["known_limitations"]),
        "maximum_age_seconds": rule["maximum_age_seconds"],
        "observed_timestamp_utc": observed_timestamp,
        "operator_review_status": OPERATOR_REVIEW_STATUS,
        "reference_timestamp_utc": reference_timestamp,
        "review_checks": [
            {
                "check_id": check["check_id"],
                "description": check["description"],
                "operator_review_status": OPERATOR_REVIEW_STATUS,
            }
            for check in request["review_checks"]
        ],
        "rule_id": rule["rule_id"],
        "source_artifact": {
            "artifact_format": link_row["source_artifact"]["artifact_format"],
            **_build_digest_reference(artifact_reference),
            "source_artifact_present": True,
        },
        "source_domain": link_row["source_domain"],
        "source_evidence_link_id": link_row["link_id"],
        "source_id": link_row["source_id"],
        "source_label": link_row["source_label"],
        "source_type": link_row["source_type"],
        "staleness_state": _staleness_state(
            timestamp_required=rule["timestamp_required"],
            timestamp_field=timestamp_field,
            age_seconds=age_seconds,
            maximum_age_seconds=rule["maximum_age_seconds"],
        ),
        "threshold_label": rule["threshold_label"],
        "timestamp_field": timestamp_field,
        "timestamp_field_candidates": list(rule["timestamp_field_candidates"]),
        "timestamp_field_present": timestamp_field is not None,
        "timestamp_required": rule["timestamp_required"],
    }


def _build_link_map_summary(link_map: dict[str, Any], reference: str) -> dict[str, Any]:
    return {
        **_build_digest_reference(reference),
        "build_id": link_map["build_id"],
        "contract_version": link_map["contract_version"],
        "map_id": link_map["map_id"],
        "operator_review_status": link_map["operator_review"]["status"],
        "run_mode": link_map["run_mode"],
        "source_evidence_links": len(link_map["source_evidence_links"]),
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


def _select_timestamp_field(artifact: dict[str, Any], candidates: list[str]) -> str | None:
    for candidate in candidates:
        if candidate in artifact:
            return candidate
    return None


def _age_seconds(observed_timestamp: str, reference_timestamp: str) -> int:
    observed = _parse_utc_timestamp_for_build(observed_timestamp)
    reference = _parse_utc_timestamp_for_build(reference_timestamp)
    return int((reference - observed).total_seconds())


def _staleness_state(
    timestamp_required: bool,
    timestamp_field: str | None,
    age_seconds: int | None,
    maximum_age_seconds: int | None,
) -> str:
    if not timestamp_required:
        return TIMESTAMP_NOT_REQUIRED_BY_RULE
    if timestamp_field is None or age_seconds is None:
        return TIMESTAMP_FIELD_MISSING
    if age_seconds < 0:
        return TIMESTAMP_AFTER_REFERENCE_CLOCK
    if maximum_age_seconds is not None and age_seconds <= maximum_age_seconds:
        return WITHIN_STATIC_REVIEW_WINDOW
    return OUTSIDE_STATIC_REVIEW_WINDOW


def _validate_reference_clock(value: Any, errors: list[str]) -> str | None:
    path = "reference_clock"
    if not isinstance(value, dict):
        errors.append(f"{path} must be an object")
        return None
    required_fields = ("reference_source", "reference_timestamp_utc", "system_clock_used")
    for field in required_fields:
        if field not in value:
            errors.append(f"{path} missing required field: {field}")
    if value.get("reference_source") != REFERENCE_CLOCK_SOURCE:
        errors.append(f"{path}.reference_source must be {REFERENCE_CLOCK_SOURCE}")
    if value.get("system_clock_used") is not False:
        errors.append(f"{path}.system_clock_used must be false")
    reference_timestamp = value.get("reference_timestamp_utc")
    if not isinstance(reference_timestamp, str) or not reference_timestamp:
        errors.append(f"{path}.reference_timestamp_utc must be a non-empty string")
        return None
    _parse_utc_timestamp(f"{path}.reference_timestamp_utc", reference_timestamp, errors)
    return reference_timestamp


def _validate_link_map_summary(value: Any, errors: list[str]) -> dict[str, Any] | None:
    path = "source_evidence_link_map"
    if not isinstance(value, dict):
        errors.append(f"{path} must be an object")
        return None
    required_fields = (
        "build_id",
        "byte_count",
        "content_sha256",
        "contract_version",
        "local_reference",
        "map_id",
        "operator_review_status",
        "present",
        "run_mode",
        "source_evidence_links",
    )
    for field in required_fields:
        if field not in value:
            errors.append(f"{path} missing required field: {field}")

    for field in ("build_id", "content_sha256", "contract_version", "local_reference", "map_id", "operator_review_status", "run_mode"):
        if not isinstance(value.get(field), str) or not value.get(field):
            errors.append(f"{path}.{field} must be a non-empty string")
    if value.get("present") is not True:
        errors.append(f"{path}.present must be true")
    if value.get("contract_version") != SOURCE_EVIDENCE_LINK_MAP_CONTRACT_VERSION:
        errors.append(f"{path}.contract_version must be {SOURCE_EVIDENCE_LINK_MAP_CONTRACT_VERSION}")
    if value.get("operator_review_status") != OPERATOR_REVIEW_STATUS:
        errors.append(f"{path}.operator_review_status must be {OPERATOR_REVIEW_STATUS}")
    if not isinstance(value.get("source_evidence_links"), int) or isinstance(value.get("source_evidence_links"), bool):
        errors.append(f"{path}.source_evidence_links must be an integer")

    link_map: dict[str, Any] | None = None
    reference = value.get("local_reference")
    if isinstance(reference, str):
        _validate_digest_reference(path, reference, value.get("byte_count"), value.get("content_sha256"), errors)
        try:
            link_map = _load_json(Path(_normalize_reference(reference)))
        except (OSError, json.JSONDecodeError, SourceQualityLedgerValidationError) as exc:
            errors.append(f"{path}.local_reference must load a JSON object: {exc}")
        else:
            validation = validate_source_evidence_link_map(link_map)
            if not validation.valid:
                errors.extend(f"{path}.{error}" for error in validation.errors)
            if value.get("map_id") != link_map.get("map_id"):
                errors.append(f"{path}.map_id must match local source evidence link map")
            if value.get("build_id") != link_map.get("build_id"):
                errors.append(f"{path}.build_id must match local source evidence link map")
            if value.get("run_mode") != link_map.get("run_mode"):
                errors.append(f"{path}.run_mode must match local source evidence link map")
            if isinstance(value.get("source_evidence_links"), int) and value.get("source_evidence_links") != len(
                link_map.get("source_evidence_links", [])
            ):
                errors.append(f"{path}.source_evidence_links must match local source evidence link map")
    return link_map


def _validate_check_rows(
    spec_id: str,
    rows: list[Any],
    reference_timestamp: str | None,
    link_map: dict[str, Any] | None,
    errors: list[str],
) -> dict[str, int]:
    seen_check_ids: set[str] = set()
    seen_source_ids: set[str] = set()
    local_references: set[str] = set()
    counts = {
        "local_references": 0,
        "review_checks": 0,
        "source_artifact_references": 0,
        "source_evidence_links": 0,
        "source_staleness_checks": 0,
        "timestamp_fields_missing": 0,
        "timestamp_fields_present": 0,
    }
    link_rows_by_source_id = {}
    if link_map is not None:
        link_rows_by_source_id = {
            row["source_id"]: row
            for row in link_map.get("source_evidence_links", [])
            if isinstance(row, dict) and isinstance(row.get("source_id"), str)
        }

    for index, row in enumerate(rows):
        path = f"source_staleness_checks[{index}]"
        if not isinstance(row, dict):
            errors.append(f"{path} must be an object")
            continue
        row_counts = _validate_check_row(
            path,
            spec_id,
            row,
            reference_timestamp,
            link_rows_by_source_id,
            seen_check_ids,
            seen_source_ids,
            errors,
        )
        counts["review_checks"] += row_counts["review_checks"]
        counts["source_artifact_references"] += row_counts["source_artifact_references"]
        counts["source_evidence_links"] += row_counts["source_evidence_links"]
        counts["source_staleness_checks"] += 1
        counts["timestamp_fields_missing"] += row_counts["timestamp_fields_missing"]
        counts["timestamp_fields_present"] += row_counts["timestamp_fields_present"]
        for reference in row_counts["local_references"]:
            local_references.add(reference)
    counts["local_references"] = len(local_references)
    return counts


def _count_spec_local_references(spec: dict[str, Any], row_local_reference_count: int) -> int:
    local_references: set[str] = set()
    for field in ("documentation", "source_evidence_link_map", "source_evidence_link_report"):
        value = spec.get(field)
        if isinstance(value, dict) and isinstance(value.get("local_reference"), str):
            local_references.add(_normalize_reference(value["local_reference"]))
    row_references: set[str] = set()
    rows = spec.get("source_staleness_checks")
    if isinstance(rows, list):
        for row in rows:
            if not isinstance(row, dict):
                continue
            source_artifact = row.get("source_artifact")
            if isinstance(source_artifact, dict) and isinstance(source_artifact.get("local_reference"), str):
                row_references.add(_normalize_reference(source_artifact["local_reference"]))
    if not row_references and row_local_reference_count:
        return len(local_references) + row_local_reference_count
    local_references.update(row_references)
    return len(local_references)


def _validate_check_row(
    path: str,
    spec_id: str,
    row: dict[str, Any],
    reference_timestamp: str | None,
    link_rows_by_source_id: dict[str, dict[str, Any]],
    seen_check_ids: set[str],
    seen_source_ids: set[str],
    errors: list[str],
) -> dict[str, Any]:
    required_fields = (
        "age_seconds",
        "check_id",
        "check_kind",
        "check_state",
        "known_limitations",
        "maximum_age_seconds",
        "observed_timestamp_utc",
        "operator_review_status",
        "reference_timestamp_utc",
        "review_checks",
        "rule_id",
        "source_artifact",
        "source_domain",
        "source_evidence_link_id",
        "source_id",
        "source_label",
        "source_type",
        "staleness_state",
        "threshold_label",
        "timestamp_field",
        "timestamp_field_candidates",
        "timestamp_field_present",
        "timestamp_required",
    )
    for field in required_fields:
        if field not in row:
            errors.append(f"{path} missing required field: {field}")

    for field in (
        "check_id",
        "check_kind",
        "check_state",
        "reference_timestamp_utc",
        "rule_id",
        "source_domain",
        "source_evidence_link_id",
        "source_id",
        "source_label",
        "source_type",
        "staleness_state",
        "threshold_label",
    ):
        if not isinstance(row.get(field), str) or not row.get(field):
            errors.append(f"{path}.{field} must be a non-empty string")

    if row.get("check_state") != CHECK_ROW_STATE:
        errors.append(f"{path}.check_state must be {CHECK_ROW_STATE}")
    if row.get("operator_review_status") != OPERATOR_REVIEW_STATUS:
        errors.append(f"{path}.operator_review_status must be {OPERATOR_REVIEW_STATUS}")
    if not _is_string_list(row.get("known_limitations")):
        errors.append(f"{path}.known_limitations must be a list of strings")
    if not isinstance(row.get("timestamp_field_candidates"), list) or not all(
        isinstance(item, str) and item for item in row.get("timestamp_field_candidates", [])
    ):
        errors.append(f"{path}.timestamp_field_candidates must be a list of strings")
    if row.get("timestamp_required") not in (True, False):
        errors.append(f"{path}.timestamp_required must be a boolean")
    if row.get("timestamp_field_present") not in (True, False):
        errors.append(f"{path}.timestamp_field_present must be a boolean")

    check_id = row.get("check_id")
    source_id = row.get("source_id")
    if isinstance(check_id, str):
        if check_id in seen_check_ids:
            errors.append(f"{path}.check_id duplicates an earlier row")
        seen_check_ids.add(check_id)
    if isinstance(source_id, str):
        if source_id in seen_source_ids:
            errors.append(f"{path}.source_id duplicates an earlier row")
        seen_source_ids.add(source_id)
        if check_id != f"{spec_id}.{source_id}.source_staleness_check":
            errors.append(f"{path}.check_id must be derived from spec_id and source_id")

    source_artifact_reference = _validate_source_artifact(path, row.get("source_artifact"), errors)
    review_check_count = _validate_review_checks(path, row.get("review_checks"), errors)

    timestamp_count = _validate_timestamp_fields(path, row, reference_timestamp, errors)

    source_evidence_links = 0
    source_artifact_references = 0
    link_row = link_rows_by_source_id.get(source_id) if isinstance(source_id, str) else None
    if link_row is None:
        errors.append(f"{path}.source_id must exist in source evidence link map")
    else:
        source_evidence_links = 1
        if row.get("source_evidence_link_id") != link_row.get("link_id"):
            errors.append(f"{path}.source_evidence_link_id must match source evidence link map row")
        if row.get("source_domain") != link_row.get("source_domain"):
            errors.append(f"{path}.source_domain must match source evidence link map row")
        if row.get("source_label") != link_row.get("source_label"):
            errors.append(f"{path}.source_label must match source evidence link map row")
        if row.get("source_type") != link_row.get("source_type"):
            errors.append(f"{path}.source_type must match source evidence link map row")
        if isinstance(row.get("source_artifact"), dict):
            source_artifact_references = 1
            source_artifact = row["source_artifact"]
            link_artifact = link_row["source_artifact"]
            if source_artifact.get("local_reference") != link_artifact.get("local_reference"):
                errors.append(f"{path}.source_artifact.local_reference must match source evidence link map row")
            if source_artifact.get("content_sha256") != link_artifact.get("content_sha256"):
                errors.append(f"{path}.source_artifact.content_sha256 must match source evidence link map row")
            if source_artifact.get("byte_count") != link_artifact.get("byte_count"):
                errors.append(f"{path}.source_artifact.byte_count must match source evidence link map row")
            if source_artifact.get("artifact_format") != link_artifact.get("artifact_format"):
                errors.append(f"{path}.source_artifact.artifact_format must match source evidence link map row")
            if source_artifact.get("source_artifact_present") is not True:
                errors.append(f"{path}.source_artifact.source_artifact_present must be true")

    local_references = set()
    if source_artifact_reference is not None:
        local_references.add(source_artifact_reference)

    return {
        "local_references": local_references,
        "review_checks": review_check_count,
        "source_artifact_references": source_artifact_references,
        "source_evidence_links": source_evidence_links,
        "timestamp_fields_missing": timestamp_count["missing"],
        "timestamp_fields_present": timestamp_count["present"],
    }


def _validate_timestamp_fields(
    path: str,
    row: dict[str, Any],
    reference_timestamp: str | None,
    errors: list[str],
) -> dict[str, int]:
    counts = {"missing": 0, "present": 0}
    timestamp_required = row.get("timestamp_required")
    timestamp_field = row.get("timestamp_field")
    timestamp_field_present = row.get("timestamp_field_present")
    observed_timestamp = row.get("observed_timestamp_utc")
    age_seconds = row.get("age_seconds")
    maximum_age_seconds = row.get("maximum_age_seconds")
    candidates = row.get("timestamp_field_candidates")

    if timestamp_field_present is True:
        counts["present"] = 1
    elif timestamp_field_present is False:
        counts["missing"] = 1

    if timestamp_field is not None and (not isinstance(timestamp_field, str) or not timestamp_field):
        errors.append(f"{path}.timestamp_field must be a non-empty string or null")
    if isinstance(timestamp_field, str) and isinstance(candidates, list) and timestamp_field not in candidates:
        errors.append(f"{path}.timestamp_field must be one of timestamp_field_candidates")

    if timestamp_required is True:
        if not isinstance(maximum_age_seconds, int) or isinstance(maximum_age_seconds, bool) or maximum_age_seconds <= 0:
            errors.append(f"{path}.maximum_age_seconds must be a positive integer when timestamp_required is true")
    elif maximum_age_seconds is not None:
        errors.append(f"{path}.maximum_age_seconds must be null when timestamp_required is false")

    if timestamp_field_present is True:
        if not isinstance(observed_timestamp, str) or not observed_timestamp:
            errors.append(f"{path}.observed_timestamp_utc must be a non-empty string when timestamp_field_present is true")
        else:
            _parse_utc_timestamp(f"{path}.observed_timestamp_utc", observed_timestamp, errors)
        if not isinstance(age_seconds, int) or isinstance(age_seconds, bool):
            errors.append(f"{path}.age_seconds must be an integer when timestamp_field_present is true")
    else:
        if observed_timestamp is not None:
            errors.append(f"{path}.observed_timestamp_utc must be null when timestamp_field_present is false")
        if age_seconds is not None:
            errors.append(f"{path}.age_seconds must be null when timestamp_field_present is false")

    if reference_timestamp is not None and row.get("reference_timestamp_utc") != reference_timestamp:
        errors.append(f"{path}.reference_timestamp_utc must match reference_clock.reference_timestamp_utc")

    if isinstance(observed_timestamp, str) and isinstance(reference_timestamp, str) and isinstance(age_seconds, int):
        expected_age_seconds = _age_seconds(observed_timestamp, reference_timestamp)
        if age_seconds != expected_age_seconds:
            errors.append(f"{path}.age_seconds must match observed and reference timestamps")

    expected_state = _staleness_state(
        timestamp_required=timestamp_required is True,
        timestamp_field=timestamp_field if isinstance(timestamp_field, str) else None,
        age_seconds=age_seconds if isinstance(age_seconds, int) and not isinstance(age_seconds, bool) else None,
        maximum_age_seconds=maximum_age_seconds if isinstance(maximum_age_seconds, int) and not isinstance(maximum_age_seconds, bool) else None,
    )
    if row.get("staleness_state") != expected_state:
        errors.append(f"{path}.staleness_state must be {expected_state}")

    return counts


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
    link_map_reference: str,
    link_report_reference: str,
    documentation_reference: str,
) -> dict[str, int]:
    local_references = {
        link_map_reference,
        link_report_reference,
        documentation_reference,
    }
    local_references.update(row["source_artifact"]["local_reference"] for row in rows)
    return {
        "local_references": len(local_references),
        "operator_review_steps": len(operator_review_steps),
        "review_checks": sum(len(row["review_checks"]) for row in rows),
        "source_artifact_references": len({row["source_artifact"]["local_reference"] for row in rows}),
        "source_evidence_links": len(rows),
        "source_staleness_checks": len(rows),
        "timestamp_fields_missing": sum(1 for row in rows if not row["timestamp_field_present"]),
        "timestamp_fields_present": sum(1 for row in rows if row["timestamp_field_present"]),
        "warnings": len(warnings),
    }


def _build_deterministic_id(
    spec_id: str,
    request: dict[str, Any],
    link_map: dict[str, Any],
    rows: list[dict[str, Any]],
) -> str:
    digest_input = {
        "link_map": link_map,
        "request": request,
        "rows": rows,
        "spec_id": spec_id,
    }
    digest = hashlib.sha256(_canonical_json(digest_input).encode("utf-8")).hexdigest()[:BUILD_ID_DIGEST_LENGTH]
    return f"{spec_id}-{digest}"


def _validate_build_id(spec_id: str, build_id: Any, errors: list[str]) -> None:
    if not isinstance(build_id, str) or not build_id:
        errors.append("build_id must be a non-empty string")
        return
    prefix = f"{spec_id}-"
    if not build_id.startswith(prefix):
        errors.append("build_id must start with spec_id followed by a digest")
        return
    digest = build_id[len(prefix):]
    if len(digest) != BUILD_ID_DIGEST_LENGTH or any(character not in "0123456789abcdef" for character in digest):
        errors.append(f"build_id digest must be {BUILD_ID_DIGEST_LENGTH} lowercase hex characters")


def _parse_utc_timestamp(path: str, value: str, errors: list[str]) -> datetime | None:
    try:
        parsed = _parse_utc_timestamp_for_build(value)
    except ValueError as exc:
        errors.append(f"{path} must be an ISO-8601 UTC timestamp ending in Z: {exc}")
        return None
    return parsed


def _parse_utc_timestamp_for_build(value: str) -> datetime:
    if not value.endswith("Z"):
        raise ValueError("missing Z suffix")
    parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    if parsed.tzinfo is None:
        raise ValueError("missing timezone")
    return parsed.astimezone(timezone.utc)


if __name__ == "__main__":
    raise SystemExit(main())
