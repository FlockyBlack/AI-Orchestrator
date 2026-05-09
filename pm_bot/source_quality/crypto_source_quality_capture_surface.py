from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
from typing import Any

from pm_bot.source_quality.unified_source_quality_ledger import (
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
    _write_json,
)

TASK_ID = "PMBOT-CRYPTO-PILOT-004-CRYPTO-SOURCE-QUALITY-CAPTURE-SURFACE-LOCAL-ONLY"
CAPTURE_SURFACE_CONTRACT_VERSION = "pmbot_crypto_source_quality_capture_surface.v1"
CAPTURE_SURFACE_ID = "crypto_source_quality_capture_surface_001"
CAPTURE_SURFACE_RUN_MODE = "local_descriptive_crypto_source_quality_capture_surface"
CAPTURE_SURFACE_RECORD_STATE = "surface_only_static_sample"
CAPTURE_SURFACE_ROW_STATE = "descriptive_crypto_source_quality_capture"
CAPTURE_SURFACE_CREATED_AT = "2026-05-09T00:30:00Z"
CAPTURE_SURFACE_DIGEST_LENGTH = 12

SAMPLE_CAPTURE_SURFACE_PATH = "pm_bot/source_quality/samples/crypto_source_quality_capture_surface.fixture.json"
SAMPLE_OPERATOR_REPORT_PATH = "pm_bot/source_quality/samples/crypto_source_quality_capture_surface.fixture.md"

CRYPTO_CAPTURE_FIXTURE_PATH = (
    "pm_bot/tests/fixtures/crypto_market_class_capture/crypto_market_class_capture_template.valid.json"
)
CRYPTO_PROTOCOL_FIXTURE_PATH = (
    "pm_bot/tests/fixtures/crypto_operator_review_protocol/crypto_operator_review_protocol.valid.json"
)
CRYPTO_OBSERVATION_LEDGER_FIXTURE_PATH = (
    "pm_bot/tests/fixtures/crypto_paperlive_observation_ledger/crypto_paperlive_observation_ledger.valid.json"
)
CRYPTO_REFERENCE_SNAPSHOT_FIXTURE_PATH = (
    "pm_bot/tests/fixtures/crypto_paperlive_observation_ledger/static_crypto_reference_snapshot.valid.json"
)

EXPECTED_CAPTURE_SURFACE_FIELDS = (
    "record_id",
    "source_artifact_id",
    "source_artifact_label",
    "source_artifact_role",
    "contract_version",
    "local_reference",
    "required_fields",
    "present_fields",
    "missing_fields",
    "field_presence_check",
    "contract_check",
    "local_reference_check",
    "copy_lineage_check",
    "operator_notes",
    "operator_review_status",
)

EXPECTED_CAPTURE_SURFACE_SAFETY_BOUNDARIES = {
    "authenticated_endpoint_calls_allowed": False,
    "background_process_allowed": False,
    "browser_automation_allowed": False,
    "external_market_api_calls_allowed": False,
    "local_static_samples_only": True,
    "network_calls_allowed": False,
    "operator_review_required": True,
    "paperlive_execution_allowed": False,
    "runtime_or_dispatcher_changes_allowed": False,
    "transaction_endpoint_calls_allowed": False,
    "wallet_or_signing_material_access_allowed": False,
}

ARTIFACT_SPECS: tuple[dict[str, Any], ...] = (
    {
        "artifact_key": "market_class_capture_template",
        "artifact_id_field": "template_id",
        "contract_version": "pmbot_crypto_market_class_capture_template.v1",
        "copy_lineage_check": "static_capture_fixture_retained",
        "local_reference": CRYPTO_CAPTURE_FIXTURE_PATH,
        "record_state": "template_only_static_sample",
        "required_fields": (
            "contract_version",
            "template_id",
            "template_name",
            "capture_fields",
            "market_class_catalog",
            "sample_records",
            "operator_review",
            "summary_counts",
        ),
        "source_artifact_label": "Crypto market class capture template",
        "source_artifact_role": "market_class_capture_template",
    },
    {
        "artifact_key": "operator_review_protocol",
        "artifact_id_field": "protocol_id",
        "contract_version": "pmbot_crypto_operator_review_protocol.v1",
        "copy_lineage_check": "static_protocol_fixture_retained",
        "local_reference": CRYPTO_PROTOCOL_FIXTURE_PATH,
        "record_state": "protocol_only_static_sample",
        "required_fields": (
            "contract_version",
            "protocol_id",
            "protocol_name",
            "input_contracts",
            "protocol_steps",
            "review_record_fields",
            "static_review_records",
            "operator_review",
            "summary_counts",
        ),
        "source_artifact_label": "Crypto operator review protocol",
        "source_artifact_role": "operator_review_protocol",
    },
    {
        "artifact_key": "paperlive_observation_ledger",
        "artifact_id_field": "ledger_id",
        "contract_version": "pmbot_crypto_paperlive_observation_ledger.v1",
        "copy_lineage_check": "static_observation_ledger_retained",
        "local_reference": CRYPTO_OBSERVATION_LEDGER_FIXTURE_PATH,
        "record_state": "ledger_only_static_sample",
        "required_fields": (
            "contract_version",
            "ledger_id",
            "ledger_record_fields",
            "observation_records",
            "observation_source_catalog",
            "source_contracts",
            "operator_review",
            "summary_counts",
        ),
        "source_artifact_label": "Crypto paperlive observation ledger",
        "source_artifact_role": "paperlive_observation_ledger",
    },
    {
        "artifact_key": "static_reference_snapshot",
        "artifact_id_field": "snapshot_id",
        "contract_version": "pmbot_static_crypto_reference_snapshot.v1",
        "copy_lineage_check": "static_reference_snapshot_retained",
        "local_reference": CRYPTO_REFERENCE_SNAPSHOT_FIXTURE_PATH,
        "record_state": "static_reference_snapshot",
        "required_fields": (
            "contract_version",
            "snapshot_id",
            "asset_symbol",
            "asset_name",
            "metric_type",
            "measurement_source_label",
            "reported_reference_value",
            "reported_reference_unit",
            "reported_at_utc",
            "source_label",
        ),
        "source_artifact_label": "Static crypto reference snapshot",
        "source_artifact_role": "static_reference_snapshot",
    },
)


def load_crypto_source_artifacts() -> dict[str, dict[str, Any]]:
    artifacts: dict[str, dict[str, Any]] = {}
    for spec in ARTIFACT_SPECS:
        reference = str(spec["local_reference"])
        errors = _validate_local_reference(reference)
        if errors:
            raise SourceQualityLedgerValidationError(tuple(errors))
        artifacts[str(spec["artifact_key"])] = _load_json(Path(_normalize_reference(reference)))
    return artifacts


def load_crypto_source_quality_capture_surface(path: str | Path) -> dict[str, Any]:
    reference = str(path)
    errors = _validate_local_reference(reference)
    if errors:
        raise SourceQualityLedgerValidationError(tuple(errors))
    return _load_json(Path(_normalize_reference(reference)))


def build_crypto_source_quality_capture_surface(
    artifacts: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    errors = _validate_input_artifact_payloads(artifacts)
    if errors:
        raise SourceQualityLedgerValidationError(tuple(errors))

    input_artifacts = [_build_input_artifact(spec, artifacts[str(spec["artifact_key"])]) for spec in ARTIFACT_SPECS]
    records = [_build_capture_record(input_artifact, spec) for input_artifact, spec in zip(input_artifacts, ARTIFACT_SPECS)]
    operator_review_steps = [
        "Confirm each listed local fixture opens as a static JSON artifact.",
        "Confirm required fields are visible in each artifact.",
        "Confirm every capture row remains pending operator review.",
    ]
    surface = {
        "build_id": _build_deterministic_id(input_artifacts, records),
        "capture_surface_fields": list(EXPECTED_CAPTURE_SURFACE_FIELDS),
        "capture_surface_id": CAPTURE_SURFACE_ID,
        "contract_version": CAPTURE_SURFACE_CONTRACT_VERSION,
        "created_at": CAPTURE_SURFACE_CREATED_AT,
        "errors": [],
        "input_artifacts": input_artifacts,
        "local_only": True,
        "operator_review": {
            "reviewed_at": None,
            "reviewed_by": None,
            "status": OPERATOR_REVIEW_STATUS,
        },
        "operator_review_required": True,
        "operator_review_steps": operator_review_steps,
        "quality_capture_records": records,
        "record_state": CAPTURE_SURFACE_RECORD_STATE,
        "run_mode": CAPTURE_SURFACE_RUN_MODE,
        "safety_boundaries": dict(EXPECTED_CAPTURE_SURFACE_SAFETY_BOUNDARIES),
        "summary_counts": _summary_counts(input_artifacts, records, operator_review_steps),
        "task_id": TASK_ID,
        "warnings": [],
    }
    return surface


def validate_crypto_source_quality_capture_surface(surface: dict[str, Any]) -> SourceQualityLedgerValidation:
    errors: list[str] = []
    if not isinstance(surface, dict):
        return SourceQualityLedgerValidation(valid=False, errors=("surface must be an object",))

    required_fields = (
        "build_id",
        "capture_surface_fields",
        "capture_surface_id",
        "contract_version",
        "created_at",
        "errors",
        "input_artifacts",
        "local_only",
        "operator_review",
        "operator_review_required",
        "operator_review_steps",
        "quality_capture_records",
        "record_state",
        "run_mode",
        "safety_boundaries",
        "summary_counts",
        "task_id",
        "warnings",
    )
    for field in required_fields:
        if field not in surface:
            errors.append(f"missing required capture surface field: {field}")

    if surface.get("task_id") != TASK_ID:
        errors.append(f"task_id must be {TASK_ID}")
    if surface.get("contract_version") != CAPTURE_SURFACE_CONTRACT_VERSION:
        errors.append(f"contract_version must be {CAPTURE_SURFACE_CONTRACT_VERSION}")
    if surface.get("capture_surface_id") != CAPTURE_SURFACE_ID:
        errors.append(f"capture_surface_id must be {CAPTURE_SURFACE_ID}")
    if surface.get("run_mode") != CAPTURE_SURFACE_RUN_MODE:
        errors.append(f"run_mode must be {CAPTURE_SURFACE_RUN_MODE}")
    if surface.get("record_state") != CAPTURE_SURFACE_RECORD_STATE:
        errors.append(f"record_state must be {CAPTURE_SURFACE_RECORD_STATE}")
    if surface.get("created_at") != CAPTURE_SURFACE_CREATED_AT:
        errors.append(f"created_at must be {CAPTURE_SURFACE_CREATED_AT}")
    if surface.get("local_only") is not True:
        errors.append("local_only must be true")
    if surface.get("operator_review_required") is not True:
        errors.append("operator_review_required must be true")
    if surface.get("errors") != []:
        errors.append("errors must be an empty list")
    if not _is_string_list(surface.get("warnings")):
        errors.append("warnings must be a list of strings")
    if surface.get("safety_boundaries") != EXPECTED_CAPTURE_SURFACE_SAFETY_BOUNDARIES:
        errors.append("safety_boundaries must match the closed crypto source quality boundary")
    if tuple(surface.get("capture_surface_fields", ())) != EXPECTED_CAPTURE_SURFACE_FIELDS:
        errors.append("capture_surface_fields must match the fixed crypto source quality contract")

    _validate_operator_review(surface.get("operator_review"), errors)
    if not _is_non_empty_string_list(surface.get("operator_review_steps")):
        errors.append("operator_review_steps must be a non-empty list of strings")

    forbidden_paths = _find_forbidden_decision_terms(surface)
    if forbidden_paths:
        errors.append(
            "forbidden scoring/action field detected in crypto source quality surface at: "
            + ", ".join(sorted(forbidden_paths))
        )

    input_artifact_counts = _validate_input_artifacts(surface.get("input_artifacts"), errors)
    record_counts = _validate_capture_records(surface.get("quality_capture_records"), errors)
    _validate_artifact_record_alignment(surface.get("input_artifacts"), surface.get("quality_capture_records"), errors)
    _validate_build_id(surface.get("build_id"), surface.get("input_artifacts"), surface.get("quality_capture_records"), errors)

    if input_artifact_counts is not None and record_counts is not None:
        operator_steps = surface.get("operator_review_steps")
        expected_counts = {
            "capture_surface_fields": len(EXPECTED_CAPTURE_SURFACE_FIELDS),
            "input_artifacts": input_artifact_counts["input_artifacts"],
            "missing_fields": record_counts["missing_fields"],
            "operator_review_steps": len(operator_steps) if isinstance(operator_steps, list) else 0,
            "present_fields": record_counts["present_fields"],
            "quality_capture_records": record_counts["quality_capture_records"],
            "required_fields": record_counts["required_fields"],
            "warnings": len(surface["warnings"]) if isinstance(surface.get("warnings"), list) else 0,
        }
        if surface.get("summary_counts") != expected_counts:
            errors.append("summary_counts must match capture surface totals: " + _canonical_json(expected_counts))

    return SourceQualityLedgerValidation(valid=not errors, errors=tuple(errors))


def build_operator_report(surface: dict[str, Any]) -> str:
    lines: list[str] = [
        "# PMBOT Crypto Source Quality Capture Surface",
        "",
        f"Task: `{surface['task_id']}`",
        f"Surface: `{surface['capture_surface_id']}`",
        f"Build: `{surface['build_id']}`",
        f"Contract: `{surface['contract_version']}`",
        f"Run mode: `{surface['run_mode']}`",
        f"Operator review: `{surface['operator_review']['status']}`",
        "",
        "## Summary",
        "",
        f"- Input artifacts: {surface['summary_counts']['input_artifacts']}",
        f"- Capture records: {surface['summary_counts']['quality_capture_records']}",
        f"- Required fields: {surface['summary_counts']['required_fields']}",
        f"- Present fields: {surface['summary_counts']['present_fields']}",
        f"- Missing fields: {surface['summary_counts']['missing_fields']}",
        "",
        "## Capture Records",
        "",
    ]
    for record in surface["quality_capture_records"]:
        lines.extend(
            [
                f"- `{record['source_artifact_id']}` ({record['source_artifact_label']})",
                f"  - Role: `{record['source_artifact_role']}`",
                f"  - Local artifact: `{record['local_reference']}`",
                f"  - Contract: `{record['contract_version']}`",
                f"  - Required fields visible: {len(record['present_fields'])}/{len(record['required_fields'])}",
                f"  - Review status: `{record['operator_review_status']}`",
            ]
        )

    lines.extend(["", "## Operator Review Steps", ""])
    for step in surface["operator_review_steps"]:
        lines.append(f"- {step}")

    lines.extend(
        [
            "",
            "## Safety",
            "",
            "- Local fixture/static input only.",
            "- Makes no network, LLM, external market API, wallet, order, transaction endpoint, runtime, browser, scheduler, or worker calls.",
            "- Descriptive source quality capture only; no outcome resolution or trade instruction output.",
            "- Not execution approval and not runtime input.",
        ]
    )
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a local PMBOT crypto source quality capture surface.")
    parser.add_argument("--output-surface", required=True, help="Output crypto source quality capture JSON path.")
    parser.add_argument("--output-report", required=True, help="Output operator report Markdown path.")
    args = parser.parse_args(argv)

    artifacts = load_crypto_source_artifacts()
    surface = build_crypto_source_quality_capture_surface(artifacts)
    validation = validate_crypto_source_quality_capture_surface(surface)
    if not validation.valid:
        raise SourceQualityLedgerValidationError(validation.errors)

    _write_json(Path(args.output_surface), surface)
    Path(args.output_report).write_text(build_operator_report(surface), encoding="utf-8")
    return 0


def _validate_input_artifact_payloads(artifacts: dict[str, dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    if not isinstance(artifacts, dict):
        return ["artifacts must be an object keyed by artifact name"]

    for spec in ARTIFACT_SPECS:
        key = str(spec["artifact_key"])
        artifact = artifacts.get(key)
        if not isinstance(artifact, dict):
            errors.append(f"artifacts.{key} must be an object")
            continue

        if artifact.get("contract_version") != spec["contract_version"]:
            errors.append(f"artifacts.{key}.contract_version must be {spec['contract_version']}")

        artifact_id_field = str(spec["artifact_id_field"])
        if not isinstance(artifact.get(artifact_id_field), str) or not artifact.get(artifact_id_field):
            errors.append(f"artifacts.{key}.{artifact_id_field} must be a non-empty string")

        record_state = spec.get("record_state")
        if "record_state" in artifact and artifact["record_state"] != record_state:
            errors.append(f"artifacts.{key}.record_state must be {record_state}")

        missing = [field for field in spec["required_fields"] if field not in artifact]
        if missing:
            errors.append(f"artifacts.{key} missing required fields: " + ", ".join(sorted(missing)))

    return errors


def _build_input_artifact(spec: dict[str, Any], artifact: dict[str, Any]) -> dict[str, Any]:
    artifact_id = artifact[str(spec["artifact_id_field"])]
    required_fields = list(spec["required_fields"])
    return {
        "contract_version": artifact["contract_version"],
        "local_reference": str(spec["local_reference"]),
        "record_state": str(spec["record_state"]),
        "required_fields": required_fields,
        "source_artifact_id": artifact_id,
        "source_artifact_label": str(spec["source_artifact_label"]),
        "source_artifact_role": str(spec["source_artifact_role"]),
    }


def _build_capture_record(input_artifact: dict[str, Any], spec: dict[str, Any]) -> dict[str, Any]:
    required_fields = list(input_artifact["required_fields"])
    return {
        "contract_check": "expected_contract_visible",
        "contract_version": input_artifact["contract_version"],
        "copy_lineage_check": str(spec["copy_lineage_check"]),
        "field_presence_check": "all_required_fields_visible",
        "local_reference": input_artifact["local_reference"],
        "local_reference_check": "relative_local_fixture_path",
        "missing_fields": [],
        "operator_notes": "Static sample for source quality capture surface only.",
        "operator_review_status": OPERATOR_REVIEW_STATUS,
        "present_fields": required_fields,
        "record_id": f"{CAPTURE_SURFACE_ID}.{input_artifact['source_artifact_id']}.quality_capture",
        "required_fields": required_fields,
        "source_artifact_id": input_artifact["source_artifact_id"],
        "source_artifact_label": input_artifact["source_artifact_label"],
        "source_artifact_role": input_artifact["source_artifact_role"],
    }


def _summary_counts(
    input_artifacts: list[dict[str, Any]],
    records: list[dict[str, Any]],
    operator_review_steps: list[str],
) -> dict[str, int]:
    return {
        "capture_surface_fields": len(EXPECTED_CAPTURE_SURFACE_FIELDS),
        "input_artifacts": len(input_artifacts),
        "missing_fields": sum(len(record["missing_fields"]) for record in records),
        "operator_review_steps": len(operator_review_steps),
        "present_fields": sum(len(record["present_fields"]) for record in records),
        "quality_capture_records": len(records),
        "required_fields": sum(len(record["required_fields"]) for record in records),
        "warnings": 0,
    }


def _build_deterministic_id(
    input_artifacts: list[dict[str, Any]],
    records: list[dict[str, Any]],
) -> str:
    digest_input = {
        "capture_surface_id": CAPTURE_SURFACE_ID,
        "input_artifacts": input_artifacts,
        "quality_capture_records": records,
    }
    digest = hashlib.sha256(_canonical_json(digest_input).encode("utf-8")).hexdigest()[:CAPTURE_SURFACE_DIGEST_LENGTH]
    return f"{CAPTURE_SURFACE_ID}-{digest}"


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


def _validate_input_artifacts(value: Any, errors: list[str]) -> dict[str, int] | None:
    if not isinstance(value, list) or not value:
        errors.append("input_artifacts must be a non-empty list")
        return None

    seen_ids: set[str] = set()
    for index, artifact in enumerate(value):
        path = f"input_artifacts[{index}]"
        if not isinstance(artifact, dict):
            errors.append(f"{path} must be an object")
            continue
        for field in (
            "contract_version",
            "local_reference",
            "record_state",
            "required_fields",
            "source_artifact_id",
            "source_artifact_label",
            "source_artifact_role",
        ):
            if field not in artifact:
                errors.append(f"{path} missing required field: {field}")
        for field in (
            "contract_version",
            "local_reference",
            "record_state",
            "source_artifact_id",
            "source_artifact_label",
            "source_artifact_role",
        ):
            if not isinstance(artifact.get(field), str) or not artifact.get(field):
                errors.append(f"{path}.{field} must be a non-empty string")
        artifact_id = artifact.get("source_artifact_id")
        if isinstance(artifact_id, str):
            if artifact_id in seen_ids:
                errors.append(f"{path}.source_artifact_id duplicates an earlier artifact")
            seen_ids.add(artifact_id)
        if not _is_non_empty_string_list(artifact.get("required_fields")):
            errors.append(f"{path}.required_fields must be a non-empty list of strings")
        if isinstance(artifact.get("local_reference"), str):
            reference_errors = _validate_local_reference(artifact["local_reference"])
            errors.extend(f"{path}.{error}" for error in reference_errors)

    return {"input_artifacts": len(value)}


def _validate_capture_records(value: Any, errors: list[str]) -> dict[str, int] | None:
    if not isinstance(value, list) or not value:
        errors.append("quality_capture_records must be a non-empty list")
        return None

    counts = {
        "missing_fields": 0,
        "present_fields": 0,
        "quality_capture_records": 0,
        "required_fields": 0,
    }
    seen_record_ids: set[str] = set()
    for index, record in enumerate(value):
        path = f"quality_capture_records[{index}]"
        if not isinstance(record, dict):
            errors.append(f"{path} must be an object")
            continue
        _validate_capture_record(path, record, seen_record_ids, counts, errors)
    return counts


def _validate_capture_record(
    path: str,
    record: dict[str, Any],
    seen_record_ids: set[str],
    counts: dict[str, int],
    errors: list[str],
) -> None:
    if set(record) != set(EXPECTED_CAPTURE_SURFACE_FIELDS):
        errors.append(f"{path} fields must match the fixed crypto source quality capture fields")

    for field in (
        "contract_check",
        "contract_version",
        "copy_lineage_check",
        "field_presence_check",
        "local_reference",
        "local_reference_check",
        "operator_notes",
        "operator_review_status",
        "record_id",
        "source_artifact_id",
        "source_artifact_label",
        "source_artifact_role",
    ):
        if not isinstance(record.get(field), str) or not record.get(field):
            errors.append(f"{path}.{field} must be a non-empty string")

    if record.get("operator_review_status") != OPERATOR_REVIEW_STATUS:
        errors.append(f"{path}.operator_review_status must be {OPERATOR_REVIEW_STATUS}")
    if record.get("field_presence_check") != "all_required_fields_visible":
        errors.append(f"{path}.field_presence_check must be all_required_fields_visible")
    if record.get("contract_check") != "expected_contract_visible":
        errors.append(f"{path}.contract_check must be expected_contract_visible")
    if record.get("local_reference_check") != "relative_local_fixture_path":
        errors.append(f"{path}.local_reference_check must be relative_local_fixture_path")

    record_id = record.get("record_id")
    source_artifact_id = record.get("source_artifact_id")
    if isinstance(record_id, str) and record_id:
        if record_id in seen_record_ids:
            errors.append(f"{path}.record_id duplicates an earlier record")
        seen_record_ids.add(record_id)
    if isinstance(source_artifact_id, str) and source_artifact_id and record_id != f"{CAPTURE_SURFACE_ID}.{source_artifact_id}.quality_capture":
        errors.append(f"{path}.record_id must be derived from capture surface id and source artifact id")

    if isinstance(record.get("local_reference"), str):
        reference_errors = _validate_local_reference(record["local_reference"])
        errors.extend(f"{path}.{error}" for error in reference_errors)

    required_fields = record.get("required_fields")
    present_fields = record.get("present_fields")
    missing_fields = record.get("missing_fields")
    if not _is_non_empty_string_list(required_fields):
        errors.append(f"{path}.required_fields must be a non-empty list of strings")
        required_count = 0
    else:
        required_count = len(required_fields)
    if not _is_non_empty_string_list(present_fields):
        errors.append(f"{path}.present_fields must be a non-empty list of strings")
        present_count = 0
    else:
        present_count = len(present_fields)
    if not _is_string_list(missing_fields):
        errors.append(f"{path}.missing_fields must be a list of strings")
        missing_count = 0
    else:
        missing_count = len(missing_fields)

    if isinstance(required_fields, list) and isinstance(present_fields, list) and present_fields != required_fields:
        errors.append(f"{path}.present_fields must match required_fields for local static artifacts")
    if missing_fields != []:
        errors.append(f"{path}.missing_fields must be empty for the static local sample")

    counts["missing_fields"] += missing_count
    counts["present_fields"] += present_count
    counts["quality_capture_records"] += 1
    counts["required_fields"] += required_count


def _validate_artifact_record_alignment(input_artifacts: Any, records: Any, errors: list[str]) -> None:
    if not isinstance(input_artifacts, list) or not isinstance(records, list):
        return

    artifacts_by_id = {
        artifact["source_artifact_id"]: artifact
        for artifact in input_artifacts
        if isinstance(artifact, dict) and isinstance(artifact.get("source_artifact_id"), str)
    }
    if len(records) != len(artifacts_by_id):
        errors.append("quality_capture_records must contain one row per input_artifacts entry")

    for index, record in enumerate(records):
        if not isinstance(record, dict):
            continue
        path = f"quality_capture_records[{index}]"
        source_artifact_id = record.get("source_artifact_id")
        if not isinstance(source_artifact_id, str) or not source_artifact_id:
            continue
        artifact = artifacts_by_id.get(source_artifact_id)
        if artifact is None:
            errors.append(f"{path}.source_artifact_id must reference an input_artifacts entry")
            continue
        for field in (
            "contract_version",
            "local_reference",
            "required_fields",
            "source_artifact_label",
            "source_artifact_role",
        ):
            if record.get(field) != artifact.get(field):
                errors.append(f"{path}.{field} must match input_artifacts row {source_artifact_id}")


def _validate_build_id(
    build_id: Any,
    input_artifacts: Any,
    records: Any,
    errors: list[str],
) -> None:
    if not isinstance(build_id, str) or not build_id:
        errors.append("build_id must be a non-empty string")
        return
    prefix = f"{CAPTURE_SURFACE_ID}-"
    if not build_id.startswith(prefix):
        errors.append("build_id must start with capture_surface_id followed by a digest")
        return
    digest = build_id[len(prefix):]
    if len(digest) != CAPTURE_SURFACE_DIGEST_LENGTH or any(character not in "0123456789abcdef" for character in digest):
        errors.append(f"build_id digest must be {CAPTURE_SURFACE_DIGEST_LENGTH} lowercase hex characters")
    if isinstance(input_artifacts, list) and isinstance(records, list):
        expected = _build_deterministic_id(input_artifacts, records)
        if build_id != expected:
            errors.append("build_id must match deterministic input artifact and capture record digest")


if __name__ == "__main__":
    raise SystemExit(main())
