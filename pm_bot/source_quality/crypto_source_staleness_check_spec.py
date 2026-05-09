from __future__ import annotations

import argparse
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pm_bot.source_quality.crypto_source_evidence_link_map import (
    EXPECTED_SAFETY_BOUNDARIES,
    EXPECTED_SOURCE_IDS,
    LINK_MAP_CONTRACT_VERSION,
    LINK_MAP_ID,
    LINK_MAP_RUN_MODE,
    REQUIRED_VALIDATION_COMMANDS,
    SAMPLE_LINK_MAP_PATH,
    SAMPLE_OPERATOR_REPORT_PATH as SAMPLE_LINK_MAP_REPORT_PATH,
    load_crypto_source_evidence_link_map,
    validate_crypto_source_evidence_link_map,
)
from pm_bot.source_quality.unified_source_quality_ledger import (
    OPERATOR_REVIEW_STATUS,
    SourceQualityLedgerValidation,
    SourceQualityLedgerValidationError,
    _canonical_json,
    _load_json,
    _normalize_reference,
    _validate_local_reference,
    _write_json,
)

TASK_ID = "PMBOT-CRYPTO-LIVE-004-CRYPTO-SOURCE-STALENESS-CHECK-SPEC-LOCAL-ONLY"
SPEC_CONTRACT_VERSION = "pmbot_crypto_source_staleness_check_spec.v1"
SPEC_ID = "pmbot-crypto-source-staleness-check-spec-001"
SPEC_RUN_MODE = "local_static_crypto_source_staleness_check_spec"
SPEC_CREATED_AT = "2026-05-09T01:20:00Z"
REFERENCE_TIMESTAMP_UTC = "2026-05-09T01:30:00Z"
REFERENCE_CLOCK_SOURCE = "static_fixture_reference_time"
CHECK_ROW_STATE = "descriptive_crypto_source_staleness_check"
BUILD_ID_DIGEST_LENGTH = 12

SAMPLE_SPEC_PATH = "pm_bot/source_quality/samples/crypto_source_staleness_check_spec.fixture.json"
SAMPLE_OPERATOR_REPORT_PATH = "pm_bot/source_quality/samples/crypto_source_staleness_check_spec.fixture.md"
SPEC_DOCUMENTATION_PATH = "docs/PMBOT_CRYPTO_LIVE_004_CRYPTO_SOURCE_STALENESS_CHECK_SPEC_LOCAL_ONLY.md"

WITHIN_STATIC_REVIEW_WINDOW = "within_static_review_window"
OUTSIDE_STATIC_REVIEW_WINDOW = "outside_static_review_window"
TIMESTAMP_AFTER_REFERENCE_CLOCK = "timestamp_after_reference_clock"
TIMESTAMP_FIELD_MISSING = "timestamp_field_missing"

KNOWN_LIMITATIONS = (
    "Static local spec only; no crypto data refresh is performed.",
    "Uses a fixed fixture reference timestamp instead of the system clock.",
    "Records descriptive age windows and pending review state only.",
)

OPERATOR_REVIEW_STEPS = (
    "Confirm every crypto source evidence link row has one local staleness check row.",
    "Confirm timestamp field paths, age windows, and digests match local static artifacts.",
    "Record disputes outside this spec before any later readiness status change.",
)

EXPECTED_REVIEW_CHECKS = (
    {
        "check_id": "crypto_source_link_identity",
        "description": "Confirm source identity and source evidence link row match the crypto link map.",
    },
    {
        "check_id": "artifact_digest",
        "description": "Confirm source artifact reference and digest match local bytes.",
    },
    {
        "check_id": "static_timestamp_window",
        "description": "Confirm timestamp field path and computed age use the fixed fixture reference time.",
    },
    {
        "check_id": "pending_review_state",
        "description": "Confirm every check remains pending operator review.",
    },
)

SOURCE_STALENESS_RULES_BY_SOURCE_ID: dict[str, dict[str, Any]] = {
    "read_only_crypto_data_contract_fixture": {
        "maximum_age_seconds": 172800,
        "rule_id": "read_only_crypto_data_contract_created_at_window",
        "timestamp_field_path": "$.created_at",
        "timestamp_required": True,
        "window_label": "crypto_static_contract_two_day_window",
    },
    "crypto_market_class_capture_template": {
        "maximum_age_seconds": 172800,
        "rule_id": "crypto_market_class_capture_template_created_at_window",
        "timestamp_field_path": "$.created_at",
        "timestamp_required": True,
        "window_label": "crypto_static_template_two_day_window",
    },
    "crypto_operator_review_protocol": {
        "maximum_age_seconds": 172800,
        "rule_id": "crypto_operator_review_protocol_created_at_window",
        "timestamp_field_path": "$.created_at",
        "timestamp_required": True,
        "window_label": "crypto_static_protocol_two_day_window",
    },
    "crypto_paperlive_observation_ledger": {
        "maximum_age_seconds": 172800,
        "rule_id": "crypto_paperlive_observation_ledger_created_at_window",
        "timestamp_field_path": "$.created_at",
        "timestamp_required": True,
        "window_label": "crypto_static_observation_ledger_two_day_window",
    },
    "crypto_source_quality_capture_surface_sample": {
        "maximum_age_seconds": 172800,
        "rule_id": "crypto_source_quality_capture_surface_created_at_window",
        "timestamp_field_path": "$.created_at",
        "timestamp_required": True,
        "window_label": "crypto_static_source_quality_two_day_window",
    },
    "static_crypto_reference_snapshot_2026_05_09_btc": {
        "maximum_age_seconds": 172800,
        "rule_id": "static_crypto_reference_snapshot_reported_at_window",
        "timestamp_field_path": "$.reported_at_utc",
        "timestamp_required": True,
        "window_label": "crypto_static_reference_two_day_window",
    },
}

FORBIDDEN_OUTPUT_TOKENS = {
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
    "recommendations",
    "score",
    "scoring",
    "selection",
    "sell",
    "side",
    "stake",
    "wager",
}


def load_crypto_source_staleness_check_spec(path: str | Path) -> dict[str, Any]:
    reference = str(path)
    errors = _validate_local_reference(reference)
    if errors:
        raise SourceQualityLedgerValidationError(tuple(errors))
    return _load_json(Path(_normalize_reference(reference)))


def build_crypto_source_staleness_check_spec(link_map: dict[str, Any] | None = None) -> dict[str, Any]:
    link_map = link_map if link_map is not None else load_crypto_source_evidence_link_map(SAMPLE_LINK_MAP_PATH)
    validation = validate_crypto_source_evidence_link_map(link_map)
    if not validation.valid:
        raise SourceQualityLedgerValidationError(validation.errors)

    rows = [_build_check_row(row) for row in link_map["source_evidence_links"]]
    warnings: list[str] = []
    spec = {
        "build_id": "",
        "contract_version": SPEC_CONTRACT_VERSION,
        "created_at": SPEC_CREATED_AT,
        "documentation": _build_digest_reference(SPEC_DOCUMENTATION_PATH),
        "errors": [],
        "local_only": True,
        "operator_review": {
            "reviewed_at": None,
            "reviewed_by": None,
            "status": OPERATOR_REVIEW_STATUS,
        },
        "operator_review_required": True,
        "operator_review_steps": list(OPERATOR_REVIEW_STEPS),
        "reference_clock": {
            "reference_source": REFERENCE_CLOCK_SOURCE,
            "reference_timestamp_utc": REFERENCE_TIMESTAMP_UTC,
            "system_clock_used": False,
        },
        "required_validation_commands": list(REQUIRED_VALIDATION_COMMANDS),
        "run_mode": SPEC_RUN_MODE,
        "safety_boundaries": dict(EXPECTED_SAFETY_BOUNDARIES),
        "source_evidence_link_map": _build_link_map_summary(link_map),
        "source_evidence_link_report": _build_digest_reference(SAMPLE_LINK_MAP_REPORT_PATH),
        "source_staleness_checks": rows,
        "spec_id": SPEC_ID,
        "summary_counts": _summary_counts(rows, warnings),
        "task_id": TASK_ID,
        "warnings": warnings,
    }
    spec["build_id"] = _build_deterministic_id(spec)
    return spec


def validate_crypto_source_staleness_check_spec(spec: dict[str, Any]) -> SourceQualityLedgerValidation:
    errors: list[str] = []
    if not isinstance(spec, dict):
        return SourceQualityLedgerValidation(valid=False, errors=("spec must be an object",))

    required_fields = (
        "build_id",
        "contract_version",
        "created_at",
        "documentation",
        "errors",
        "local_only",
        "operator_review",
        "operator_review_required",
        "operator_review_steps",
        "reference_clock",
        "required_validation_commands",
        "run_mode",
        "safety_boundaries",
        "source_evidence_link_map",
        "source_evidence_link_report",
        "source_staleness_checks",
        "spec_id",
        "summary_counts",
        "task_id",
        "warnings",
    )
    for field in required_fields:
        if field not in spec:
            errors.append(f"missing required spec field: {field}")

    if spec.get("task_id") != TASK_ID:
        errors.append(f"task_id must be {TASK_ID}")
    if spec.get("contract_version") != SPEC_CONTRACT_VERSION:
        errors.append(f"contract_version must be {SPEC_CONTRACT_VERSION}")
    if spec.get("spec_id") != SPEC_ID:
        errors.append(f"spec_id must be {SPEC_ID}")
    if spec.get("run_mode") != SPEC_RUN_MODE:
        errors.append(f"run_mode must be {SPEC_RUN_MODE}")
    if spec.get("created_at") != SPEC_CREATED_AT:
        errors.append(f"created_at must be {SPEC_CREATED_AT}")
    if spec.get("local_only") is not True:
        errors.append("local_only must be true")
    if spec.get("operator_review_required") is not True:
        errors.append("operator_review_required must be true")
    if spec.get("errors") != []:
        errors.append("errors must be an empty list")
    if spec.get("safety_boundaries") != EXPECTED_SAFETY_BOUNDARIES:
        errors.append("safety_boundaries must match the closed crypto source boundary")
    if spec.get("required_validation_commands") != list(REQUIRED_VALIDATION_COMMANDS):
        errors.append("required_validation_commands must match the local validation contract")
    if spec.get("operator_review_steps") != list(OPERATOR_REVIEW_STEPS):
        errors.append("operator_review_steps must match fixed crypto staleness review steps")
    if not isinstance(spec.get("warnings"), list) or not all(isinstance(item, str) for item in spec.get("warnings", [])):
        errors.append("warnings must be a list of strings")

    _validate_operator_review(spec.get("operator_review"), errors)
    _validate_reference_clock(spec.get("reference_clock"), errors)
    _validate_reference_object("documentation", spec.get("documentation"), errors)
    _validate_reference_object("source_evidence_link_report", spec.get("source_evidence_link_report"), errors)
    link_map = _validate_link_map_summary(spec.get("source_evidence_link_map"), errors)
    row_counts = _validate_check_rows(spec.get("source_staleness_checks"), link_map, errors)
    _validate_build_id(spec, errors)

    forbidden_paths = _find_forbidden_output_terms(spec)
    if forbidden_paths:
        errors.append(
            "forbidden crypto staleness output term detected at: "
            + ", ".join(sorted(forbidden_paths))
        )

    if row_counts is not None:
        warnings = spec.get("warnings") if isinstance(spec.get("warnings"), list) else []
        expected_counts = dict(row_counts)
        expected_counts["operator_review_steps"] = len(OPERATOR_REVIEW_STEPS)
        expected_counts["required_validation_commands"] = len(REQUIRED_VALIDATION_COMMANDS)
        expected_counts["warnings"] = len(warnings)
        if spec.get("summary_counts") != expected_counts:
            errors.append("summary_counts must match crypto source staleness totals: " + _canonical_json(expected_counts))

    return SourceQualityLedgerValidation(valid=not errors, errors=tuple(errors))


def build_operator_report(spec: dict[str, Any]) -> str:
    lines: list[str] = [
        "# PMBOT Crypto Source Staleness Check Spec",
        "",
        f"Task: `{spec['task_id']}`",
        f"Spec: `{spec['spec_id']}`",
        f"Build: `{spec['build_id']}`",
        f"Contract: `{spec['contract_version']}`",
        f"Run mode: `{spec['run_mode']}`",
        f"Operator review: `{spec['operator_review']['status']}`",
        "",
        "## Static Reference Clock",
        "",
        f"- Reference timestamp: `{spec['reference_clock']['reference_timestamp_utc']}`",
        f"- Reference source: `{spec['reference_clock']['reference_source']}`",
        f"- System clock used: `{str(spec['reference_clock']['system_clock_used']).lower()}`",
        "",
        "## Summary",
        "",
        f"- Source staleness checks: {spec['summary_counts']['source_staleness_checks']}",
        f"- Source evidence links: {spec['summary_counts']['source_evidence_links']}",
        f"- Source artifacts: {spec['summary_counts']['source_artifact_references']}",
        f"- Source contracts: {spec['summary_counts']['source_contract_references']}",
        f"- Timestamp fields present: {spec['summary_counts']['timestamp_fields_present']}",
        f"- Timestamp fields missing: {spec['summary_counts']['timestamp_fields_missing']}",
        f"- Local references: {spec['summary_counts']['local_references']}",
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
        age_seconds = row["age_seconds"] if row["age_seconds"] is not None else "not recorded"
        lines.extend(
            [
                f"- `{row['source_id']}` ({row['source_label']})",
                f"  - Source artifact: `{row['source_artifact']['local_reference']}`",
                f"  - Source evidence link: `{row['source_evidence_link_id']}`",
                f"  - Timestamp field path: `{row['timestamp_field_path']}`",
                f"  - Observed timestamp: `{row['observed_timestamp_utc']}`",
                f"  - Age seconds: `{age_seconds}`",
                f"  - Staleness state: `{row['staleness_state']}`",
                f"  - Review checks: {len(row['review_checks'])} pending operator review",
            ]
        )

    lines.extend(["", "## Operator Review Steps", ""])
    for step in spec["operator_review_steps"]:
        lines.append(f"- {step}")

    lines.extend(
        [
            "",
            "## Safety",
            "",
            "- Local fixture/static input only.",
            "- Uses the fixed fixture reference timestamp, not the system clock.",
            "- Makes no network, LLM, market API, endpoint, wallet, order, transaction, runtime, browser, scheduler, or worker calls.",
            "- Records descriptive age windows, digests, and pending review state only.",
            "- Does not authorize execution and is not runtime input.",
        ]
    )
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a local PMBOT crypto source staleness check spec.")
    parser.add_argument(
        "--link-map",
        default=SAMPLE_LINK_MAP_PATH,
        help="Local crypto source evidence link map JSON.",
    )
    parser.add_argument("--output-spec", required=True, help="Output crypto source staleness spec JSON path.")
    parser.add_argument("--output-report", required=True, help="Output operator report Markdown path.")
    args = parser.parse_args(argv)

    link_map = load_crypto_source_evidence_link_map(args.link_map)
    spec = build_crypto_source_staleness_check_spec(link_map)
    validation = validate_crypto_source_staleness_check_spec(spec)
    if not validation.valid:
        raise SourceQualityLedgerValidationError(validation.errors)

    _write_json(Path(args.output_spec), spec)
    Path(args.output_report).write_text(build_operator_report(spec), encoding="utf-8")
    return 0


def _build_check_row(link_row: dict[str, Any]) -> dict[str, Any]:
    source_id = link_row["source_id"]
    rule = SOURCE_STALENESS_RULES_BY_SOURCE_ID[source_id]
    artifact_reference = _normalize_reference(link_row["source_artifact"]["local_reference"])
    artifact = _load_json(Path(artifact_reference))
    observed_timestamp = _read_timestamp_path(artifact, rule["timestamp_field_path"])
    age_seconds = _age_seconds(observed_timestamp, REFERENCE_TIMESTAMP_UTC) if isinstance(observed_timestamp, str) else None
    return {
        "age_seconds": age_seconds,
        "check_id": f"{SPEC_ID}.{source_id}.crypto_source_staleness_check",
        "check_kind": "local_static_crypto_source_staleness_review",
        "check_state": CHECK_ROW_STATE,
        "known_limitations": list(KNOWN_LIMITATIONS),
        "maximum_age_seconds": rule["maximum_age_seconds"],
        "observed_timestamp_utc": observed_timestamp,
        "operator_review_status": OPERATOR_REVIEW_STATUS,
        "reference_timestamp_utc": REFERENCE_TIMESTAMP_UTC,
        "review_checks": [
            {
                "check_id": check["check_id"],
                "description": check["description"],
                "operator_review_status": OPERATOR_REVIEW_STATUS,
            }
            for check in EXPECTED_REVIEW_CHECKS
        ],
        "rule_id": rule["rule_id"],
        "source_artifact": {
            "artifact_format": link_row["source_artifact"]["artifact_format"],
            **_build_digest_reference(artifact_reference),
            "source_artifact_present": True,
        },
        "source_contract": dict(link_row["source_contract"]),
        "source_domain": link_row["source_domain"],
        "source_evidence_link_id": link_row["link_id"],
        "source_id": source_id,
        "source_inventory": dict(link_row["source_inventory"]),
        "source_label": link_row["source_label"],
        "source_record_id": link_row["source_record_id"],
        "source_record_status": link_row["source_record_status"],
        "source_type": link_row["source_type"],
        "staleness_state": _staleness_state(
            timestamp_required=rule["timestamp_required"],
            observed_timestamp=observed_timestamp,
            age_seconds=age_seconds,
            maximum_age_seconds=rule["maximum_age_seconds"],
        ),
        "timestamp_field_path": rule["timestamp_field_path"],
        "timestamp_field_present": isinstance(observed_timestamp, str),
        "timestamp_required": rule["timestamp_required"],
        "window_label": rule["window_label"],
    }


def _build_link_map_summary(link_map: dict[str, Any]) -> dict[str, Any]:
    return {
        **_build_digest_reference(SAMPLE_LINK_MAP_PATH),
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


def _summary_counts(rows: list[dict[str, Any]], warnings: list[str]) -> dict[str, int]:
    local_references = {
        SPEC_DOCUMENTATION_PATH,
        SAMPLE_LINK_MAP_PATH,
        SAMPLE_LINK_MAP_REPORT_PATH,
    }
    for row in rows:
        local_references.update(
            {
                row["source_artifact"]["local_reference"],
                row["source_contract"]["local_reference"],
                row["source_inventory"]["local_reference"],
            }
        )
    return {
        "local_references": len(local_references),
        "operator_review_steps": len(OPERATOR_REVIEW_STEPS),
        "required_validation_commands": len(REQUIRED_VALIDATION_COMMANDS),
        "review_checks": sum(len(row["review_checks"]) for row in rows),
        "source_artifact_references": len(rows),
        "source_contract_references": len(rows),
        "source_evidence_links": len(rows),
        "source_inventory_records": len(rows),
        "source_staleness_checks": len(rows),
        "timestamp_fields_missing": sum(1 for row in rows if not row["timestamp_field_present"]),
        "timestamp_fields_present": sum(1 for row in rows if row["timestamp_field_present"]),
        "warnings": len(warnings),
    }


def _validate_operator_review(value: Any, errors: list[str]) -> None:
    if not isinstance(value, dict):
        errors.append("operator_review must be an object")
        return
    if value.get("status") != OPERATOR_REVIEW_STATUS:
        errors.append(f"operator_review.status must be {OPERATOR_REVIEW_STATUS}")
    if value.get("reviewed_at") is not None:
        errors.append("operator_review.reviewed_at must be null before operator review")
    if value.get("reviewed_by") is not None:
        errors.append("operator_review.reviewed_by must be null before operator review")


def _validate_reference_clock(value: Any, errors: list[str]) -> None:
    if not isinstance(value, dict):
        errors.append("reference_clock must be an object")
        return
    expected = {
        "reference_source": REFERENCE_CLOCK_SOURCE,
        "reference_timestamp_utc": REFERENCE_TIMESTAMP_UTC,
        "system_clock_used": False,
    }
    if value != expected:
        errors.append("reference_clock must match the fixed crypto staleness reference clock")
    _parse_utc_timestamp("reference_clock.reference_timestamp_utc", str(value.get("reference_timestamp_utc")), errors)


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
    if value.get("contract_version") != LINK_MAP_CONTRACT_VERSION:
        errors.append(f"{path}.contract_version must be {LINK_MAP_CONTRACT_VERSION}")
    if value.get("map_id") != LINK_MAP_ID:
        errors.append(f"{path}.map_id must be {LINK_MAP_ID}")
    if value.get("run_mode") != LINK_MAP_RUN_MODE:
        errors.append(f"{path}.run_mode must be {LINK_MAP_RUN_MODE}")
    if value.get("operator_review_status") != OPERATOR_REVIEW_STATUS:
        errors.append(f"{path}.operator_review_status must be {OPERATOR_REVIEW_STATUS}")
    if value.get("source_evidence_links") != len(EXPECTED_SOURCE_IDS):
        errors.append(f"{path}.source_evidence_links must match fixed crypto source count")

    link_map: dict[str, Any] | None = None
    reference = _validate_reference_object(path, value, errors)
    if reference is not None:
        try:
            link_map = load_crypto_source_evidence_link_map(reference)
        except (OSError, SourceQualityLedgerValidationError) as exc:
            errors.append(f"{path}.local_reference must load crypto source evidence link map: {exc}")
        else:
            validation = validate_crypto_source_evidence_link_map(link_map)
            if not validation.valid:
                errors.extend(f"{path}.{error}" for error in validation.errors)
            if value.get("build_id") != link_map.get("build_id"):
                errors.append(f"{path}.build_id must match crypto source evidence link map")
            if value.get("source_evidence_links") != len(link_map.get("source_evidence_links", [])):
                errors.append(f"{path}.source_evidence_links must match crypto source evidence link map")
    return link_map


def _validate_check_rows(
    rows: Any,
    link_map: dict[str, Any] | None,
    errors: list[str],
) -> dict[str, int] | None:
    if not isinstance(rows, list) or not rows:
        errors.append("source_staleness_checks must be a non-empty list")
        return None
    if len(rows) != len(EXPECTED_SOURCE_IDS):
        errors.append("source_staleness_checks must contain one row per fixed crypto source")

    link_rows_by_source_id: dict[str, dict[str, Any]] = {}
    if link_map is not None:
        link_rows_by_source_id = {
            row["source_id"]: row
            for row in link_map.get("source_evidence_links", [])
            if isinstance(row, dict) and isinstance(row.get("source_id"), str)
        }

    seen_check_ids: set[str] = set()
    seen_source_ids: set[str] = set()
    local_references = {
        SPEC_DOCUMENTATION_PATH,
        SAMPLE_LINK_MAP_PATH,
        SAMPLE_LINK_MAP_REPORT_PATH,
    }
    counts = {
        "local_references": 0,
        "review_checks": 0,
        "source_artifact_references": 0,
        "source_contract_references": 0,
        "source_evidence_links": 0,
        "source_inventory_records": 0,
        "source_staleness_checks": 0,
        "timestamp_fields_missing": 0,
        "timestamp_fields_present": 0,
    }

    for index, row in enumerate(rows):
        row_counts = _validate_check_row(
            f"source_staleness_checks[{index}]",
            row,
            link_rows_by_source_id,
            seen_check_ids,
            seen_source_ids,
            errors,
        )
        for key in counts:
            if key == "local_references":
                continue
            counts[key] += row_counts[key]
        local_references.update(row_counts["local_references"])

    if tuple(row.get("source_id") for row in rows if isinstance(row, dict)) != EXPECTED_SOURCE_IDS:
        errors.append("source_staleness_checks source_id order must match fixed crypto source ids")

    counts["local_references"] = len(local_references)
    return counts


def _validate_check_row(
    path: str,
    row: Any,
    link_rows_by_source_id: dict[str, dict[str, Any]],
    seen_check_ids: set[str],
    seen_source_ids: set[str],
    errors: list[str],
) -> dict[str, Any]:
    counts = {
        "local_references": set(),
        "review_checks": 0,
        "source_artifact_references": 0,
        "source_contract_references": 0,
        "source_evidence_links": 0,
        "source_inventory_records": 0,
        "source_staleness_checks": 0,
        "timestamp_fields_missing": 0,
        "timestamp_fields_present": 0,
    }
    if not isinstance(row, dict):
        errors.append(f"{path} must be an object")
        return counts

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
        "source_contract",
        "source_domain",
        "source_evidence_link_id",
        "source_id",
        "source_inventory",
        "source_label",
        "source_record_id",
        "source_record_status",
        "source_type",
        "staleness_state",
        "timestamp_field_path",
        "timestamp_field_present",
        "timestamp_required",
        "window_label",
    )
    for field in required_fields:
        if field not in row:
            errors.append(f"{path} missing required field: {field}")

    source_id = row.get("source_id")
    check_id = row.get("check_id")
    if isinstance(check_id, str):
        if check_id in seen_check_ids:
            errors.append(f"{path}.check_id duplicates an earlier row")
        seen_check_ids.add(check_id)
    if isinstance(source_id, str):
        if source_id in seen_source_ids:
            errors.append(f"{path}.source_id duplicates an earlier row")
        seen_source_ids.add(source_id)
        if check_id != f"{SPEC_ID}.{source_id}.crypto_source_staleness_check":
            errors.append(f"{path}.check_id must be derived from spec_id and source_id")
    else:
        errors.append(f"{path}.source_id must be a non-empty string")

    if row.get("check_kind") != "local_static_crypto_source_staleness_review":
        errors.append(f"{path}.check_kind must be local_static_crypto_source_staleness_review")
    if row.get("check_state") != CHECK_ROW_STATE:
        errors.append(f"{path}.check_state must be {CHECK_ROW_STATE}")
    if row.get("operator_review_status") != OPERATOR_REVIEW_STATUS:
        errors.append(f"{path}.operator_review_status must be {OPERATOR_REVIEW_STATUS}")
    if row.get("source_record_status") != OPERATOR_REVIEW_STATUS:
        errors.append(f"{path}.source_record_status must be {OPERATOR_REVIEW_STATUS}")
    if row.get("reference_timestamp_utc") != REFERENCE_TIMESTAMP_UTC:
        errors.append(f"{path}.reference_timestamp_utc must match fixed reference timestamp")
    if row.get("known_limitations") != list(KNOWN_LIMITATIONS):
        errors.append(f"{path}.known_limitations must match fixed crypto staleness limitations")

    counts["review_checks"] = _validate_review_checks(path, row.get("review_checks"), errors)
    source_artifact_reference = _validate_source_artifact(f"{path}.source_artifact", row.get("source_artifact"), errors)
    source_contract_reference = _validate_reference_object(f"{path}.source_contract", row.get("source_contract"), errors)
    source_inventory_reference = _validate_reference_object(f"{path}.source_inventory", row.get("source_inventory"), errors)
    for reference in (source_artifact_reference, source_contract_reference, source_inventory_reference):
        if reference is not None:
            counts["local_references"].add(reference)

    if isinstance(source_id, str) and source_id in SOURCE_STALENESS_RULES_BY_SOURCE_ID:
        _validate_timestamp_fields(path, row, SOURCE_STALENESS_RULES_BY_SOURCE_ID[source_id], errors)
    else:
        errors.append(f"{path}.source_id must be one of the fixed crypto source ids")

    if row.get("timestamp_field_present") is True:
        counts["timestamp_fields_present"] = 1
    elif row.get("timestamp_field_present") is False:
        counts["timestamp_fields_missing"] = 1
    else:
        errors.append(f"{path}.timestamp_field_present must be a boolean")

    link_row = link_rows_by_source_id.get(source_id) if isinstance(source_id, str) else None
    if link_row is None:
        errors.append(f"{path}.source_id must exist in crypto source evidence link map")
    else:
        counts["source_evidence_links"] = 1
        counts["source_artifact_references"] = 1 if isinstance(row.get("source_artifact"), dict) else 0
        counts["source_contract_references"] = 1 if isinstance(row.get("source_contract"), dict) else 0
        counts["source_inventory_records"] = 1 if isinstance(row.get("source_inventory"), dict) else 0
        _validate_link_row_alignment(path, row, link_row, errors)

    counts["source_staleness_checks"] = 1
    return counts


def _validate_timestamp_fields(path: str, row: dict[str, Any], rule: dict[str, Any], errors: list[str]) -> None:
    if row.get("rule_id") != rule["rule_id"]:
        errors.append(f"{path}.rule_id must match fixed crypto staleness rule")
    if row.get("timestamp_field_path") != rule["timestamp_field_path"]:
        errors.append(f"{path}.timestamp_field_path must match fixed crypto staleness rule")
    if row.get("timestamp_required") is not rule["timestamp_required"]:
        errors.append(f"{path}.timestamp_required must match fixed crypto staleness rule")
    if row.get("maximum_age_seconds") != rule["maximum_age_seconds"]:
        errors.append(f"{path}.maximum_age_seconds must match fixed crypto staleness rule")
    if row.get("window_label") != rule["window_label"]:
        errors.append(f"{path}.window_label must match fixed crypto staleness rule")

    observed_timestamp = row.get("observed_timestamp_utc")
    age_seconds = row.get("age_seconds")
    if not isinstance(observed_timestamp, str) or not observed_timestamp:
        errors.append(f"{path}.observed_timestamp_utc must be a non-empty string")
    else:
        _parse_utc_timestamp(f"{path}.observed_timestamp_utc", observed_timestamp, errors)
    if not isinstance(age_seconds, int) or isinstance(age_seconds, bool):
        errors.append(f"{path}.age_seconds must be an integer")
    elif isinstance(observed_timestamp, str):
        expected_age_seconds = _age_seconds(observed_timestamp, REFERENCE_TIMESTAMP_UTC)
        if age_seconds != expected_age_seconds:
            errors.append(f"{path}.age_seconds must match observed timestamp and fixed reference clock")

    expected_state = _staleness_state(
        timestamp_required=rule["timestamp_required"],
        observed_timestamp=observed_timestamp if isinstance(observed_timestamp, str) else None,
        age_seconds=age_seconds if isinstance(age_seconds, int) and not isinstance(age_seconds, bool) else None,
        maximum_age_seconds=rule["maximum_age_seconds"],
    )
    if row.get("staleness_state") != expected_state:
        errors.append(f"{path}.staleness_state must be {expected_state}")


def _validate_link_row_alignment(path: str, row: dict[str, Any], link_row: dict[str, Any], errors: list[str]) -> None:
    field_pairs = (
        ("source_domain", "source_domain"),
        ("source_evidence_link_id", "link_id"),
        ("source_label", "source_label"),
        ("source_record_id", "source_record_id"),
        ("source_record_status", "source_record_status"),
        ("source_type", "source_type"),
    )
    for row_field, link_field in field_pairs:
        if row.get(row_field) != link_row.get(link_field):
            errors.append(f"{path}.{row_field} must match crypto source evidence link map")
    for nested_field in ("source_contract", "source_inventory"):
        if row.get(nested_field) != link_row.get(nested_field):
            errors.append(f"{path}.{nested_field} must match crypto source evidence link map")
    source_artifact = row.get("source_artifact")
    link_artifact = link_row.get("source_artifact")
    if isinstance(source_artifact, dict) and isinstance(link_artifact, dict):
        for field in ("artifact_format", "byte_count", "content_sha256", "local_reference", "present", "source_artifact_present"):
            if source_artifact.get(field) != link_artifact.get(field):
                errors.append(f"{path}.source_artifact.{field} must match crypto source evidence link map")


def _validate_source_artifact(path: str, value: Any, errors: list[str]) -> str | None:
    reference = _validate_reference_object(path, value, errors)
    if not isinstance(value, dict):
        return reference
    if value.get("artifact_format") != "json_object":
        errors.append(f"{path}.artifact_format must be json_object")
    if value.get("source_artifact_present") is not True:
        errors.append(f"{path}.source_artifact_present must be true")
    return reference


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
    if not isinstance(value.get("byte_count"), int) or isinstance(value.get("byte_count"), bool):
        errors.append(f"{path}.byte_count must be an integer")
    if not isinstance(value.get("content_sha256"), str) or not value.get("content_sha256"):
        errors.append(f"{path}.content_sha256 must be a non-empty string")
    reference = value.get("local_reference")
    if not isinstance(reference, str):
        errors.append(f"{path}.local_reference must be a string")
        return None
    reference_errors = _validate_local_reference(reference)
    errors.extend(f"{path}.{error}" for error in reference_errors)
    if reference_errors:
        return None
    normalized = _normalize_reference(reference)
    try:
        content = Path(normalized).read_bytes()
    except OSError as exc:
        errors.append(f"{path}.local_reference must be readable: {exc}")
        return normalized
    if isinstance(value.get("byte_count"), int) and value["byte_count"] != len(content):
        errors.append(f"{path}.byte_count must match local bytes")
    if isinstance(value.get("content_sha256"), str) and value["content_sha256"] != hashlib.sha256(content).hexdigest():
        errors.append(f"{path}.content_sha256 must match local bytes")
    return normalized


def _validate_review_checks(row_path: str, review_checks: Any, errors: list[str]) -> int:
    if not isinstance(review_checks, list) or not review_checks:
        errors.append(f"{row_path}.review_checks must be a non-empty list")
        return 0
    if len(review_checks) != len(EXPECTED_REVIEW_CHECKS):
        errors.append(f"{row_path}.review_checks must match fixed crypto staleness review checks")
    expected_by_id = {check["check_id"]: check for check in EXPECTED_REVIEW_CHECKS}
    seen_check_ids: set[str] = set()
    for index, check in enumerate(review_checks):
        path = f"{row_path}.review_checks[{index}]"
        if not isinstance(check, dict):
            errors.append(f"{path} must be an object")
            continue
        for field in ("check_id", "description", "operator_review_status"):
            if not isinstance(check.get(field), str) or not check.get(field):
                errors.append(f"{path}.{field} must be a non-empty string")
        check_id = check.get("check_id")
        if isinstance(check_id, str):
            if check_id in seen_check_ids:
                errors.append(f"{path}.check_id duplicates an earlier review check")
            seen_check_ids.add(check_id)
            expected = expected_by_id.get(check_id)
            if expected is None:
                errors.append(f"{path}.check_id must be one of the fixed crypto staleness review checks")
            elif check.get("description") != expected["description"]:
                errors.append(f"{path}.description must match fixed crypto staleness review check")
        if check.get("operator_review_status") != OPERATOR_REVIEW_STATUS:
            errors.append(f"{path}.operator_review_status must be {OPERATOR_REVIEW_STATUS}")
    return len(review_checks)


def _build_deterministic_id(spec: dict[str, Any]) -> str:
    digest_input = {key: value for key, value in spec.items() if key != "build_id"}
    digest = hashlib.sha256(_canonical_json(digest_input).encode("utf-8")).hexdigest()[:BUILD_ID_DIGEST_LENGTH]
    return f"{SPEC_ID}-{digest}"


def _validate_build_id(spec: dict[str, Any], errors: list[str]) -> None:
    build_id = spec.get("build_id")
    if not isinstance(build_id, str) or not build_id:
        errors.append("build_id must be a non-empty string")
        return
    prefix = f"{SPEC_ID}-"
    if not build_id.startswith(prefix):
        errors.append("build_id must start with spec_id followed by a digest")
        return
    digest = build_id[len(prefix):]
    if len(digest) != BUILD_ID_DIGEST_LENGTH or any(character not in "0123456789abcdef" for character in digest):
        errors.append(f"build_id digest must be {BUILD_ID_DIGEST_LENGTH} lowercase hex characters")
        return
    expected = _build_deterministic_id({**spec, "build_id": ""})
    if build_id != expected:
        errors.append("build_id must match deterministic crypto source staleness digest")


def _read_timestamp_path(artifact: dict[str, Any], timestamp_field_path: str) -> Any:
    if not timestamp_field_path.startswith("$.") or "." in timestamp_field_path[2:]:
        return None
    return artifact.get(timestamp_field_path[2:])


def _age_seconds(observed_timestamp: str, reference_timestamp: str) -> int:
    observed = _parse_utc_timestamp_for_build(observed_timestamp)
    reference = _parse_utc_timestamp_for_build(reference_timestamp)
    return int((reference - observed).total_seconds())


def _staleness_state(
    timestamp_required: bool,
    observed_timestamp: str | None,
    age_seconds: int | None,
    maximum_age_seconds: int | None,
) -> str:
    if timestamp_required and observed_timestamp is None:
        return TIMESTAMP_FIELD_MISSING
    if age_seconds is None:
        return TIMESTAMP_FIELD_MISSING
    if age_seconds < 0:
        return TIMESTAMP_AFTER_REFERENCE_CLOCK
    if maximum_age_seconds is not None and age_seconds <= maximum_age_seconds:
        return WITHIN_STATIC_REVIEW_WINDOW
    return OUTSIDE_STATIC_REVIEW_WINDOW


def _parse_utc_timestamp(path: str, value: str, errors: list[str]) -> datetime | None:
    try:
        return _parse_utc_timestamp_for_build(value)
    except ValueError as exc:
        errors.append(f"{path} must be an ISO-8601 UTC timestamp ending in Z: {exc}")
        return None


def _parse_utc_timestamp_for_build(value: str) -> datetime:
    if not value.endswith("Z"):
        raise ValueError("missing Z suffix")
    parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    if parsed.tzinfo is None:
        raise ValueError("missing timezone")
    return parsed.astimezone(timezone.utc)


def _find_forbidden_output_terms(value: Any, path: str = "$") -> list[str]:
    hits: list[str] = []
    if isinstance(value, dict):
        for key, nested_value in value.items():
            key_path = f"{path}.{key}"
            if _has_forbidden_output_token(str(key)):
                hits.append(key_path)
            hits.extend(_find_forbidden_output_terms(nested_value, key_path))
    elif isinstance(value, list):
        for index, nested_value in enumerate(value):
            hits.extend(_find_forbidden_output_terms(nested_value, f"{path}[{index}]"))
    elif isinstance(value, str) and _has_forbidden_output_token(value):
        hits.append(path)
    return hits


def _has_forbidden_output_token(value: str) -> bool:
    normalized = "".join(character if character.isalnum() else "_" for character in value.lower())
    tokens = {token for token in normalized.split("_") if token}
    return bool(tokens & FORBIDDEN_OUTPUT_TOKENS)


if __name__ == "__main__":
    raise SystemExit(main())
