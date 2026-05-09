from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REQUEST_CONTRACT_VERSION = "pmbot_unified_source_quality_ledger_request.v1"
LEDGER_CONTRACT_VERSION = "pmbot_unified_source_quality_ledger.v1"
LOCAL_RUN_MODE = "local_fixture_only"
OPERATOR_REVIEW_STATUS = "pending_operator_review"
LEDGER_ROW_STATE = "descriptive_source_review"
BUILD_ID_DIGEST_LENGTH = 12

ALLOWED_REFERENCE_PREFIXES = (
    ("pm_bot", "tests", "fixtures"),
    ("pm_bot", "source_quality", "samples"),
    ("tests", "fixtures"),
    ("docs",),
)

FORBIDDEN_REFERENCE_PREFIXES = (
    (".git",),
    (".codex",),
    ("runtime",),
    ("dispatcher",),
    ("run_codex",),
    ("pm_bot", "llm"),
    ("pm_bot", "wallet"),
    ("pm_bot", "trading"),
    ("pm_bot", "orders"),
    ("agent_tasks", "running"),
)

FORBIDDEN_DECISION_TOKENS = {
    "probability",
    "ev",
    "edge",
    "confidence",
    "side",
    "recommendation",
    "buy",
    "sell",
    "hold",
    "enter",
    "exit",
    "score",
    "scoring",
    "forecast",
    "selection",
    "pick",
    "wager",
    "stake",
    "odds",
}

EXPECTED_LEDGER_SAFETY_BOUNDARIES = {
    "external_market_api_allowed": False,
    "llm_calls_allowed": False,
    "network_calls_allowed": False,
    "offline_inputs_only": True,
    "operator_review_gate_required": True,
    "outcome_resolution_allowed": False,
    "runtime_wiring_allowed": False,
    "scheduler_or_worker_allowed": False,
    "source_preference_output_allowed": False,
    "trade_action_guidance_allowed": False,
    "wallet_or_order_code_allowed": False,
}


@dataclass(frozen=True)
class SourceQualityLedgerValidation:
    valid: bool
    errors: tuple[str, ...]
    warnings: tuple[str, ...] = ()


class SourceQualityLedgerValidationError(ValueError):
    def __init__(self, errors: tuple[str, ...]) -> None:
        super().__init__("; ".join(errors))
        self.errors = errors


def load_ledger_request(path: str | Path) -> dict[str, Any]:
    reference = str(path)
    errors = _validate_local_reference(reference)
    if errors:
        raise SourceQualityLedgerValidationError(tuple(errors))
    return _load_json(Path(_normalize_reference(reference)))


def validate_ledger_request(request: dict[str, Any]) -> SourceQualityLedgerValidation:
    errors: list[str] = []

    required_fields = (
        "contract_version",
        "ledger_id",
        "scope",
        "local_only",
        "operator_review_required",
        "source_artifacts",
        "operator_review_steps",
    )
    for field in required_fields:
        if field not in request:
            errors.append(f"missing required field: {field}")

    if request.get("contract_version") != REQUEST_CONTRACT_VERSION:
        errors.append(f"contract_version must be {REQUEST_CONTRACT_VERSION}")
    if request.get("scope") != "unified_source_quality_ledger":
        errors.append("scope must be unified_source_quality_ledger")
    if request.get("local_only") is not True:
        errors.append("local_only must be true")
    if request.get("operator_review_required") is not True:
        errors.append("operator_review_required must be true")

    forbidden_paths = _find_forbidden_decision_terms(request)
    if forbidden_paths:
        errors.append(
            "forbidden scoring/action field detected at: "
            + ", ".join(sorted(forbidden_paths))
        )

    source_artifacts = request.get("source_artifacts")
    if not isinstance(source_artifacts, list) or not source_artifacts:
        errors.append("source_artifacts must be a non-empty list")
    elif isinstance(source_artifacts, list):
        errors.extend(_validate_source_artifacts(source_artifacts))

    review_steps = request.get("operator_review_steps")
    if not _is_non_empty_string_list(review_steps):
        errors.append("operator_review_steps must be a non-empty list of strings")

    return SourceQualityLedgerValidation(valid=not errors, errors=tuple(errors))


def build_unified_source_quality_ledger(request: dict[str, Any]) -> dict[str, Any]:
    validation = validate_ledger_request(request)
    if not validation.valid:
        raise SourceQualityLedgerValidationError(validation.errors)

    artifacts = request["source_artifacts"]
    loaded_artifacts = [
        _load_json(Path(_normalize_reference(str(artifact["local_reference"]))))
        for artifact in artifacts
    ]
    source_rows = [
        _build_source_row(request["ledger_id"], artifact, loaded)
        for artifact, loaded in zip(artifacts, loaded_artifacts)
    ]
    source_inventory = [
        _build_source_inventory_row(row)
        for row in source_rows
    ]
    build_id = _build_deterministic_id(request["ledger_id"], request, loaded_artifacts)
    field_totals = _field_totals(source_rows)

    return {
        "build_id": build_id,
        "contract_version": LEDGER_CONTRACT_VERSION,
        "errors": [],
        "ledger_id": request["ledger_id"],
        "local_only": True,
        "market_context": request.get("market_context", {}),
        "operator_review": {
            "status": OPERATOR_REVIEW_STATUS,
            "steps": list(request["operator_review_steps"]),
        },
        "operator_review_required": True,
        "run_mode": LOCAL_RUN_MODE,
        "safety_boundaries": dict(EXPECTED_LEDGER_SAFETY_BOUNDARIES),
        "scope": "unified_source_quality_ledger",
        "source_inventory": source_inventory,
        "source_quality_rows": source_rows,
        "summary_counts": {
            "fields_declared": field_totals["declared"],
            "fields_missing": field_totals["missing"],
            "fields_present": field_totals["present"],
            "source_artifacts": len(source_rows),
            "source_quality_rows": len(source_rows),
            "warnings": 0,
        },
        "warnings": [],
    }


def validate_unified_source_quality_ledger(ledger: dict[str, Any]) -> SourceQualityLedgerValidation:
    errors: list[str] = []
    if not isinstance(ledger, dict):
        return SourceQualityLedgerValidation(valid=False, errors=("ledger must be an object",))

    required_fields = (
        "build_id",
        "contract_version",
        "errors",
        "ledger_id",
        "local_only",
        "operator_review",
        "operator_review_required",
        "run_mode",
        "safety_boundaries",
        "scope",
        "source_inventory",
        "source_quality_rows",
        "summary_counts",
        "warnings",
    )
    for field in required_fields:
        if field not in ledger:
            errors.append(f"missing required ledger field: {field}")

    if ledger.get("contract_version") != LEDGER_CONTRACT_VERSION:
        errors.append(f"contract_version must be {LEDGER_CONTRACT_VERSION}")
    if ledger.get("scope") != "unified_source_quality_ledger":
        errors.append("scope must be unified_source_quality_ledger")
    if ledger.get("local_only") is not True:
        errors.append("local_only must be true")
    if ledger.get("operator_review_required") is not True:
        errors.append("operator_review_required must be true")
    if ledger.get("run_mode") != LOCAL_RUN_MODE:
        errors.append(f"run_mode must be {LOCAL_RUN_MODE}")
    if ledger.get("errors") != []:
        errors.append("errors must be an empty list")
    if not _is_string_list(ledger.get("warnings")):
        errors.append("warnings must be a list of strings")
    if ledger.get("safety_boundaries") != EXPECTED_LEDGER_SAFETY_BOUNDARIES:
        errors.append("safety_boundaries must match the local-only source quality ledger boundary")

    ledger_id = ledger.get("ledger_id")
    if not isinstance(ledger_id, str) or not ledger_id:
        errors.append("ledger_id must be a non-empty string")
        ledger_id_for_rows = ""
    else:
        ledger_id_for_rows = ledger_id
        _validate_build_id(ledger_id, ledger.get("build_id"), errors)

    _validate_operator_review_block(ledger.get("operator_review"), "operator_review", errors)

    forbidden_paths = _find_forbidden_decision_terms(ledger)
    if forbidden_paths:
        errors.append(
            "forbidden scoring/action field detected in ledger at: "
            + ", ".join(sorted(forbidden_paths))
        )

    source_rows = ledger.get("source_quality_rows")
    source_rows_by_id: dict[str, dict[str, Any]] = {}
    if not isinstance(source_rows, list) or not source_rows:
        errors.append("source_quality_rows must be a non-empty list")
    else:
        for index, row in enumerate(source_rows):
            row_id = _validate_source_quality_ledger_row(ledger_id_for_rows, index, row, errors)
            if row_id:
                if row_id in source_rows_by_id:
                    errors.append(f"duplicate source_quality_rows row_id: {row_id}")
                elif isinstance(row, dict):
                    source_rows_by_id[row_id] = row

    _validate_source_quality_inventory(ledger.get("source_inventory"), source_rows_by_id, errors)
    _validate_source_quality_summary(ledger.get("summary_counts"), source_rows, ledger.get("warnings"), errors)

    return SourceQualityLedgerValidation(valid=not errors, errors=tuple(errors))


def build_operator_report(ledger: dict[str, Any]) -> str:
    lines: list[str] = [
        "# PMBOT Unified Source Quality Ledger",
        "",
        f"Ledger: `{ledger['ledger_id']}`",
        f"Build: `{ledger['build_id']}`",
        f"Run mode: `{ledger['run_mode']}`",
        f"Operator review: `{ledger['operator_review']['status']}`",
        "",
        "## Summary",
        "",
        f"- Source artifacts: {ledger['summary_counts']['source_artifacts']}",
        f"- Declared fields: {ledger['summary_counts']['fields_declared']}",
        f"- Present fields: {ledger['summary_counts']['fields_present']}",
        f"- Missing fields: {ledger['summary_counts']['fields_missing']}",
        "",
        "## Source Rows",
        "",
    ]
    for row in ledger["source_quality_rows"]:
        lines.extend(
            [
                f"- `{row['source_id']}` ({row['source_label']})",
                f"  - Local artifact: `{row['local_reference']}`",
                f"  - Snapshot: `{row['snapshot_id']}`",
                f"  - Artifact role: `{row['artifact_role']}`",
                f"  - Fields present: {row['field_summary']['present']}/{row['field_summary']['declared']}",
                f"  - Review checks: {len(row['review_checks'])} pending operator review",
            ]
        )
        if row["known_limitations"]:
            lines.append("  - Known limitations:")
            for limitation in row["known_limitations"]:
                lines.append(f"    - {limitation}")

    lines.extend(["", "## Operator Review Steps", ""])
    for step in ledger["operator_review"]["steps"]:
        lines.append(f"- {step}")

    lines.extend(
        [
            "",
            "## Safety",
            "",
            "- Makes no network, LLM, market API, wallet, order, or runtime calls.",
            "- Descriptive source review only.",
            "- Does not resolve outcomes or provide trade action guidance.",
        ]
    )
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a local PMBOT source quality ledger.")
    parser.add_argument("--request", required=True, help="Local source quality ledger request JSON.")
    parser.add_argument("--output-ledger", required=True, help="Output ledger JSON path.")
    parser.add_argument("--output-report", required=True, help="Output operator report Markdown path.")
    args = parser.parse_args(argv)

    request = load_ledger_request(args.request)
    ledger = build_unified_source_quality_ledger(request)
    report = build_operator_report(ledger)

    _write_json(Path(args.output_ledger), ledger)
    Path(args.output_report).write_text(report, encoding="utf-8")
    return 0


def _validate_source_artifacts(source_artifacts: list[Any]) -> list[str]:
    errors: list[str] = []
    seen_ids: set[str] = set()
    required_fields = (
        "source_id",
        "source_label",
        "source_type",
        "artifact_role",
        "local_reference",
        "snapshot_id",
        "fields_available",
        "review_checks",
        "known_limitations",
    )
    for index, artifact in enumerate(source_artifacts):
        if not isinstance(artifact, dict):
            errors.append(f"source_artifacts[{index}] must be an object")
            continue
        for field in required_fields:
            if field not in artifact:
                errors.append(f"source_artifacts[{index}] missing required field: {field}")

        source_id = artifact.get("source_id")
        if not isinstance(source_id, str) or not source_id:
            errors.append(f"source_artifacts[{index}].source_id must be a non-empty string")
        elif source_id in seen_ids:
            errors.append(f"duplicate source_id: {source_id}")
        else:
            seen_ids.add(source_id)

        local_reference = artifact.get("local_reference")
        if isinstance(local_reference, str):
            reference_errors = _validate_local_reference(local_reference)
            errors.extend(f"source_artifacts[{index}].{error}" for error in reference_errors)
            if not reference_errors:
                errors.extend(_validate_declared_fields(index, artifact, local_reference))
        else:
            errors.append(f"source_artifacts[{index}].local_reference must be a string")

        if not _is_non_empty_string_list(artifact.get("fields_available")):
            errors.append(f"source_artifacts[{index}].fields_available must be a non-empty list of strings")
        if not _is_non_empty_review_check_list(artifact.get("review_checks")):
            errors.append(f"source_artifacts[{index}].review_checks must be a non-empty list of check objects")
        if not _is_string_list(artifact.get("known_limitations")):
            errors.append(f"source_artifacts[{index}].known_limitations must be a list of strings")

    return errors


def _validate_declared_fields(index: int, artifact: dict[str, Any], local_reference: str) -> list[str]:
    fields_available = artifact.get("fields_available")
    if not _is_non_empty_string_list(fields_available):
        return []
    errors: list[str] = []
    try:
        loaded = _load_json(Path(_normalize_reference(local_reference)))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"source_artifacts[{index}].local_reference cannot be loaded as JSON: {exc}"]
    if not isinstance(loaded, dict):
        return [f"source_artifacts[{index}].local_reference must load a JSON object"]
    missing = [field for field in fields_available if field not in loaded]
    if missing:
        errors.append(
            f"source_artifacts[{index}] references fields missing from local artifact: "
            + ", ".join(sorted(missing))
        )
    return errors


def _validate_source_quality_ledger_row(
    ledger_id: str,
    index: int,
    row: Any,
    errors: list[str],
) -> str | None:
    path = f"source_quality_rows[{index}]"
    if not isinstance(row, dict):
        errors.append(f"{path} must be an object")
        return None

    required_fields = (
        "artifact_role",
        "field_presence",
        "field_summary",
        "known_limitations",
        "local_reference",
        "operator_review_status",
        "review_checks",
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
    if row.get("runner_state") != LEDGER_ROW_STATE:
        errors.append(f"{path}.runner_state must be {LEDGER_ROW_STATE}")

    source_id = row.get("source_id")
    row_id = row.get("row_id")
    if isinstance(source_id, str) and source_id and isinstance(row_id, str):
        expected_row_id = f"{ledger_id}.{source_id}.source_quality_review"
        if row_id != expected_row_id:
            errors.append(f"{path}.row_id must be {expected_row_id}")

    loaded_artifact: dict[str, Any] | None = None
    local_reference = row.get("local_reference")
    if isinstance(local_reference, str):
        reference_errors = _validate_local_reference(local_reference)
        errors.extend(f"{path}.{error}" for error in reference_errors)
        if not reference_errors:
            try:
                loaded_artifact = _load_json(Path(_normalize_reference(local_reference)))
            except (OSError, json.JSONDecodeError, SourceQualityLedgerValidationError) as exc:
                errors.append(f"{path}.local_reference cannot be loaded as JSON: {exc}")
    else:
        errors.append(f"{path}.local_reference must be a string")

    field_totals = _validate_field_presence(path, row.get("field_presence"), loaded_artifact, errors)
    field_summary = row.get("field_summary")
    if not isinstance(field_summary, dict):
        errors.append(f"{path}.field_summary must be an object")
    elif field_totals is not None and field_summary != field_totals:
        errors.append(
            f"{path}.field_summary must match field_presence totals: "
            + _canonical_json(field_totals)
        )

    if not _is_string_list(row.get("known_limitations")):
        errors.append(f"{path}.known_limitations must be a list of strings")

    _validate_review_checks(path, row.get("review_checks"), errors)
    return row_id if isinstance(row_id, str) and row_id else None


def _validate_field_presence(
    row_path: str,
    field_presence: Any,
    loaded_artifact: dict[str, Any] | None,
    errors: list[str],
) -> dict[str, int] | None:
    if not isinstance(field_presence, list) or not field_presence:
        errors.append(f"{row_path}.field_presence must be a non-empty list")
        return None

    seen_fields: set[str] = set()
    present_count = 0
    missing_count = 0
    for index, field_record in enumerate(field_presence):
        path = f"{row_path}.field_presence[{index}]"
        if not isinstance(field_record, dict):
            errors.append(f"{path} must be an object")
            continue

        field_name = field_record.get("field_name")
        if not isinstance(field_name, str) or not field_name:
            errors.append(f"{path}.field_name must be a non-empty string")
        elif field_name in seen_fields:
            errors.append(f"{path}.field_name duplicates an earlier field: {field_name}")
        else:
            seen_fields.add(field_name)

        if not isinstance(field_record.get("observed_value_type"), str) or not field_record.get("observed_value_type"):
            errors.append(f"{path}.observed_value_type must be a non-empty string")
        if field_record.get("operator_review_status") != OPERATOR_REVIEW_STATUS:
            errors.append(f"{path}.operator_review_status must be {OPERATOR_REVIEW_STATUS}")

        present_value = field_record.get("present")
        if present_value is True:
            present_count += 1
        elif present_value is False:
            missing_count += 1
            errors.append(f"{path}.present must be true for local source quality ledger artifacts")
        else:
            errors.append(f"{path}.present must be a boolean")

        if loaded_artifact is None or not isinstance(field_name, str) or not field_name:
            continue

        expected_present = field_name in loaded_artifact
        if present_value != expected_present:
            errors.append(f"{path}.present must match presence in the local artifact")
        if not expected_present:
            errors.append(f"{path}.field_name is missing from the local artifact")
            continue

        expected_type = type(loaded_artifact[field_name]).__name__
        if field_record.get("observed_value_type") != expected_type:
            errors.append(f"{path}.observed_value_type must match local artifact field type: {expected_type}")

    return {
        "declared": len(field_presence),
        "missing": missing_count,
        "present": present_count,
    }


def _validate_review_checks(row_path: str, review_checks: Any, errors: list[str]) -> None:
    if not _is_non_empty_review_check_list(review_checks):
        errors.append(f"{row_path}.review_checks must be a non-empty list of check objects")
        return

    seen_check_ids: set[str] = set()
    for index, check in enumerate(review_checks):
        path = f"{row_path}.review_checks[{index}]"
        check_id = check["check_id"]
        if check_id in seen_check_ids:
            errors.append(f"{path}.check_id duplicates an earlier review check: {check_id}")
        else:
            seen_check_ids.add(check_id)
        if check.get("operator_review_status") != OPERATOR_REVIEW_STATUS:
            errors.append(f"{path}.operator_review_status must be {OPERATOR_REVIEW_STATUS}")


def _validate_source_quality_inventory(
    source_inventory: Any,
    source_rows_by_id: dict[str, dict[str, Any]],
    errors: list[str],
) -> None:
    if not isinstance(source_inventory, list):
        errors.append("source_inventory must be a list")
        return
    if len(source_inventory) != len(source_rows_by_id):
        errors.append("source_inventory must contain one entry per source_quality_rows row")

    seen_row_ids: set[str] = set()
    for index, inventory_row in enumerate(source_inventory):
        path = f"source_inventory[{index}]"
        if not isinstance(inventory_row, dict):
            errors.append(f"{path} must be an object")
            continue

        required_fields = (
            "artifact_loaded",
            "artifact_role",
            "field_count",
            "local_reference",
            "operator_review_status",
            "row_id",
            "runner_state",
            "snapshot_id",
            "source_id",
            "source_label",
            "source_type",
        )
        for field in required_fields:
            if field not in inventory_row:
                errors.append(f"{path} missing required field: {field}")

        if inventory_row.get("artifact_loaded") is not True:
            errors.append(f"{path}.artifact_loaded must be true")
        if inventory_row.get("operator_review_status") != OPERATOR_REVIEW_STATUS:
            errors.append(f"{path}.operator_review_status must be {OPERATOR_REVIEW_STATUS}")
        if inventory_row.get("runner_state") != LEDGER_ROW_STATE:
            errors.append(f"{path}.runner_state must be {LEDGER_ROW_STATE}")

        row_id = inventory_row.get("row_id")
        if not isinstance(row_id, str) or not row_id:
            errors.append(f"{path}.row_id must be a non-empty string")
            continue
        if row_id in seen_row_ids:
            errors.append(f"{path}.row_id duplicates an earlier inventory row: {row_id}")
        else:
            seen_row_ids.add(row_id)

        source_row = source_rows_by_id.get(row_id)
        if source_row is None:
            errors.append(f"{path}.row_id must reference a source_quality_rows row")
            continue

        for field in (
            "artifact_role",
            "local_reference",
            "operator_review_status",
            "row_id",
            "runner_state",
            "snapshot_id",
            "source_id",
            "source_label",
            "source_type",
        ):
            if inventory_row.get(field) != source_row.get(field):
                errors.append(f"{path}.{field} must match source_quality_rows row {row_id}")

        field_summary = source_row.get("field_summary")
        if isinstance(field_summary, dict) and inventory_row.get("field_count") != field_summary.get("declared"):
            errors.append(f"{path}.field_count must match source_quality_rows row {row_id} declared field count")


def _validate_source_quality_summary(
    summary_counts: Any,
    source_rows: Any,
    warnings: Any,
    errors: list[str],
) -> None:
    if not isinstance(summary_counts, dict):
        errors.append("summary_counts must be an object")
        return

    row_objects = [row for row in source_rows if isinstance(row, dict)] if isinstance(source_rows, list) else []
    expected_summary = {
        "fields_declared": sum(_field_summary_count(row, "declared") for row in row_objects),
        "fields_missing": sum(_field_summary_count(row, "missing") for row in row_objects),
        "fields_present": sum(_field_summary_count(row, "present") for row in row_objects),
        "source_artifacts": len(row_objects),
        "source_quality_rows": len(row_objects),
        "warnings": len(warnings) if isinstance(warnings, list) else 0,
    }
    if summary_counts != expected_summary:
        errors.append("summary_counts must match source_quality_rows totals: " + _canonical_json(expected_summary))


def _field_summary_count(row: dict[str, Any], key: str) -> int:
    field_summary = row.get("field_summary")
    value = field_summary.get(key) if isinstance(field_summary, dict) else None
    return value if isinstance(value, int) and not isinstance(value, bool) else 0


def _validate_operator_review_block(block: Any, path: str, errors: list[str]) -> None:
    if not isinstance(block, dict):
        errors.append(f"{path} must be an object")
        return
    if block.get("status") != OPERATOR_REVIEW_STATUS:
        errors.append(f"{path}.status must be {OPERATOR_REVIEW_STATUS}")
    if not _is_non_empty_string_list(block.get("steps")):
        errors.append(f"{path}.steps must be a non-empty list of strings")


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


def _validate_local_reference(reference: str) -> list[str]:
    errors: list[str] = []
    normalized = _normalize_reference(reference)
    parts = _reference_parts(normalized)

    if not normalized:
        return ["local_reference must be a non-empty relative local path"]
    if "://" in normalized or ":" in normalized:
        errors.append("local_reference must point to a local fixture or static artifact")
    if normalized.startswith("/") or normalized.startswith("\\"):
        errors.append("local_reference must be relative")
    if any(part == ".." for part in parts):
        errors.append("local_reference must not contain path traversal")
    if _is_env_reference(normalized):
        errors.append("local_reference is outside the source quality ledger boundary")
    if any(_has_prefix(parts, forbidden) for forbidden in FORBIDDEN_REFERENCE_PREFIXES):
        errors.append("local_reference is outside the source quality ledger boundary")
    if parts and not any(_has_prefix(parts, allowed) for allowed in ALLOWED_REFERENCE_PREFIXES):
        errors.append("local_reference must stay under an allowed local fixture/static path")
    return errors


def _build_source_row(ledger_id: str, artifact: dict[str, Any], loaded: dict[str, Any]) -> dict[str, Any]:
    field_presence = [
        {
            "field_name": field,
            "observed_value_type": type(loaded[field]).__name__,
            "operator_review_status": OPERATOR_REVIEW_STATUS,
            "present": field in loaded,
        }
        for field in artifact["fields_available"]
    ]
    return {
        "artifact_role": artifact["artifact_role"],
        "field_presence": field_presence,
        "field_summary": {
            "declared": len(field_presence),
            "missing": sum(1 for field in field_presence if not field["present"]),
            "present": sum(1 for field in field_presence if field["present"]),
        },
        "known_limitations": list(artifact["known_limitations"]),
        "local_reference": _normalize_reference(str(artifact["local_reference"])),
        "operator_review_status": OPERATOR_REVIEW_STATUS,
        "review_checks": [
            {
                "check_id": check["check_id"],
                "description": check["description"],
                "operator_review_status": OPERATOR_REVIEW_STATUS,
            }
            for check in artifact["review_checks"]
        ],
        "row_id": f"{ledger_id}.{artifact['source_id']}.source_quality_review",
        "runner_state": LEDGER_ROW_STATE,
        "snapshot_id": artifact["snapshot_id"],
        "source_id": artifact["source_id"],
        "source_label": artifact["source_label"],
        "source_type": artifact["source_type"],
    }


def _build_source_inventory_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "artifact_loaded": True,
        "artifact_role": row["artifact_role"],
        "field_count": row["field_summary"]["declared"],
        "local_reference": row["local_reference"],
        "operator_review_status": row["operator_review_status"],
        "row_id": row["row_id"],
        "runner_state": row["runner_state"],
        "snapshot_id": row["snapshot_id"],
        "source_id": row["source_id"],
        "source_label": row["source_label"],
        "source_type": row["source_type"],
    }


def _field_totals(source_rows: list[dict[str, Any]]) -> dict[str, int]:
    return {
        "declared": sum(row["field_summary"]["declared"] for row in source_rows),
        "missing": sum(row["field_summary"]["missing"] for row in source_rows),
        "present": sum(row["field_summary"]["present"] for row in source_rows),
    }


def _build_deterministic_id(
    ledger_id: str,
    request: dict[str, Any],
    loaded_artifacts: list[dict[str, Any]],
) -> str:
    digest_input = {
        "loaded_artifacts": loaded_artifacts,
        "request": request,
    }
    digest = hashlib.sha256(_canonical_json(digest_input).encode("utf-8")).hexdigest()[:12]
    return f"{ledger_id}-{digest}"


def _find_forbidden_decision_terms(value: Any, path: str = "$") -> list[str]:
    hits: list[str] = []
    if isinstance(value, dict):
        for key, nested_value in value.items():
            key_path = f"{path}.{key}"
            if _has_forbidden_token(str(key)):
                hits.append(key_path)
            hits.extend(_find_forbidden_decision_terms(nested_value, key_path))
    elif isinstance(value, list):
        for index, nested_value in enumerate(value):
            hits.extend(_find_forbidden_decision_terms(nested_value, f"{path}[{index}]"))
    elif isinstance(value, str) and _has_forbidden_token(value):
        hits.append(path)
    return hits


def _has_forbidden_token(value: str) -> bool:
    normalized = "".join(character if character.isalnum() else "_" for character in value.lower())
    tokens = {token for token in normalized.split("_") if token}
    return bool(tokens & FORBIDDEN_DECISION_TOKENS)


def _is_non_empty_review_check_list(value: Any) -> bool:
    if not isinstance(value, list) or not value:
        return False
    for item in value:
        if not isinstance(item, dict):
            return False
        if not isinstance(item.get("check_id"), str) or not item["check_id"]:
            return False
        if not isinstance(item.get("description"), str) or not item["description"]:
            return False
    return True


def _is_non_empty_string_list(value: Any) -> bool:
    return isinstance(value, list) and bool(value) and all(isinstance(item, str) and item for item in value)


def _is_string_list(value: Any) -> bool:
    return isinstance(value, list) and all(isinstance(item, str) for item in value)


def _has_prefix(parts: tuple[str, ...], prefix: tuple[str, ...]) -> bool:
    return len(parts) >= len(prefix) and parts[: len(prefix)] == prefix


def _is_env_reference(reference: str) -> bool:
    first_part = _reference_parts(reference)[0] if _reference_parts(reference) else ""
    return first_part == ".env" or first_part.startswith(".env.")


def _reference_parts(reference: str) -> tuple[str, ...]:
    return tuple(part for part in reference.split("/") if part)


def _normalize_reference(reference: str) -> str:
    raw_reference = reference.strip()
    path = Path(raw_reference)
    if path.is_absolute():
        try:
            return path.resolve().relative_to(Path.cwd().resolve()).as_posix()
        except ValueError:
            return raw_reference.replace("\\", "/")
    return raw_reference.replace("\\", "/")


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise SourceQualityLedgerValidationError(("local JSON artifact must be an object",))
    return value


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
