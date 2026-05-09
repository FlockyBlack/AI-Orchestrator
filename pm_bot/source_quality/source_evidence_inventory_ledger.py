from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from pm_bot.source_quality.unified_source_quality_ledger import (
    OPERATOR_REVIEW_STATUS,
    SourceQualityLedgerValidation,
    SourceQualityLedgerValidationError,
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

REQUEST_CONTRACT_VERSION = "pmbot_source_evidence_inventory_ledger_request.v1"
LEDGER_CONTRACT_VERSION = "pmbot_source_evidence_inventory_ledger.v1"
LEDGER_SCOPE = "source_evidence_inventory_ledger"
LEDGER_RUN_MODE = "local_static_source_evidence_inventory"
LEDGER_ROW_STATE = "descriptive_source_evidence_inventory"
BUILD_ID_DIGEST_LENGTH = 12
SAMPLE_LEDGER_PATH = "pm_bot/source_quality/samples/source_evidence_inventory_ledger.fixture.json"
SAMPLE_OPERATOR_REPORT_PATH = "pm_bot/source_quality/samples/source_evidence_inventory_ledger.fixture.md"

EXPECTED_SAFETY_BOUNDARIES = {
    "authenticated_endpoint_calls_allowed": False,
    "background_process_allowed": False,
    "browser_automation_allowed": False,
    "credential_or_secret_access_allowed": False,
    "execution_endpoint_calls_allowed": False,
    "external_service_calls_allowed": False,
    "llm_provider_calls_allowed": False,
    "local_static_inputs_only": True,
    "network_calls_allowed": False,
    "operator_review_required": True,
    "order_or_trade_surface_changes_allowed": False,
    "runtime_or_dispatcher_changes_allowed": False,
    "scheduler_or_worker_allowed": False,
    "transaction_endpoint_calls_allowed": False,
    "wallet_or_signing_material_access_allowed": False,
}

FORBIDDEN_EVIDENCE_TERMS = {
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


def load_source_evidence_inventory_request(path: str | Path) -> dict[str, Any]:
    reference = str(path)
    errors = _validate_local_reference(reference)
    if errors:
        raise SourceQualityLedgerValidationError(tuple(errors))
    return _load_json(Path(_normalize_reference(reference)))


def build_source_evidence_inventory_ledger(request: dict[str, Any]) -> dict[str, Any]:
    validation = validate_source_evidence_inventory_request(request)
    if not validation.valid:
        raise SourceQualityLedgerValidationError(validation.errors)

    rows = [_build_evidence_row(request["inventory_id"], artifact) for artifact in request["source_artifacts"]]
    rows = sorted(rows, key=lambda row: row["source_id"])
    warnings: list[str] = []
    ledger = {
        "build_id": _build_deterministic_id(request["inventory_id"], request, rows),
        "contract_version": LEDGER_CONTRACT_VERSION,
        "errors": [],
        "inventory_id": request["inventory_id"],
        "local_only": True,
        "operator_review": {
            "status": OPERATOR_REVIEW_STATUS,
            "steps": list(request["operator_review_steps"]),
        },
        "operator_review_required": True,
        "run_mode": LEDGER_RUN_MODE,
        "safety_boundaries": dict(EXPECTED_SAFETY_BOUNDARIES),
        "scope": LEDGER_SCOPE,
        "source_evidence_rows": rows,
        "summary_counts": _summary_counts(rows, request["operator_review_steps"], warnings),
        "warnings": warnings,
    }
    return ledger


def validate_source_evidence_inventory_request(request: dict[str, Any]) -> SourceQualityLedgerValidation:
    errors: list[str] = []
    if not isinstance(request, dict):
        return SourceQualityLedgerValidation(valid=False, errors=("request must be an object",))

    required_fields = (
        "contract_version",
        "inventory_id",
        "local_only",
        "operator_review_required",
        "operator_review_steps",
        "scope",
        "source_artifacts",
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
    if not _is_non_empty_string_list(request.get("operator_review_steps")):
        errors.append("operator_review_steps must be a non-empty list of strings")

    forbidden_paths = _find_forbidden_evidence_terms(request)
    if forbidden_paths:
        errors.append(
            "forbidden source evidence term detected in request at: "
            + ", ".join(sorted(forbidden_paths))
        )

    source_artifacts = request.get("source_artifacts")
    if not isinstance(source_artifacts, list) or not source_artifacts:
        errors.append("source_artifacts must be a non-empty list")
    else:
        errors.extend(_validate_source_artifacts(source_artifacts))

    return SourceQualityLedgerValidation(valid=not errors, errors=tuple(errors))


def validate_source_evidence_inventory_ledger(ledger: dict[str, Any]) -> SourceQualityLedgerValidation:
    errors: list[str] = []
    if not isinstance(ledger, dict):
        return SourceQualityLedgerValidation(valid=False, errors=("ledger must be an object",))

    required_fields = (
        "build_id",
        "contract_version",
        "errors",
        "inventory_id",
        "local_only",
        "operator_review",
        "operator_review_required",
        "run_mode",
        "safety_boundaries",
        "scope",
        "source_evidence_rows",
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

    inventory_id = ledger.get("inventory_id")
    if not isinstance(inventory_id, str) or not inventory_id:
        errors.append("inventory_id must be a non-empty string")
        inventory_id_for_rows = ""
    else:
        inventory_id_for_rows = inventory_id
        _validate_build_id(inventory_id, ledger.get("build_id"), errors)

    _validate_operator_review_block(ledger.get("operator_review"), "operator_review", errors)

    forbidden_paths = _find_forbidden_evidence_terms(ledger)
    if forbidden_paths:
        errors.append(
            "forbidden source evidence term detected in ledger at: "
            + ", ".join(sorted(forbidden_paths))
        )

    rows = ledger.get("source_evidence_rows")
    row_counts: dict[str, int] | None = None
    if not isinstance(rows, list) or not rows:
        errors.append("source_evidence_rows must be a non-empty list")
    else:
        row_counts = _validate_evidence_rows(inventory_id_for_rows, rows, errors)

    if row_counts is not None:
        operator_review = ledger.get("operator_review")
        operator_steps = operator_review.get("steps") if isinstance(operator_review, dict) else []
        warnings = ledger.get("warnings") if isinstance(ledger.get("warnings"), list) else []
        expected_counts = dict(row_counts)
        expected_counts["operator_review_steps"] = len(operator_steps) if isinstance(operator_steps, list) else 0
        expected_counts["warnings"] = len(warnings)
        if ledger.get("summary_counts") != expected_counts:
            errors.append("summary_counts must match source_evidence_rows totals: " + _canonical_json(expected_counts))

    return SourceQualityLedgerValidation(valid=not errors, errors=tuple(errors))


def build_operator_report(ledger: dict[str, Any]) -> str:
    lines: list[str] = [
        "# PMBOT Source Evidence Inventory Ledger",
        "",
        f"Inventory: `{ledger['inventory_id']}`",
        f"Build: `{ledger['build_id']}`",
        f"Run mode: `{ledger['run_mode']}`",
        f"Operator review: `{ledger['operator_review']['status']}`",
        "",
        "## Summary Counts",
        "",
        f"- Source evidence rows: {ledger['summary_counts']['source_evidence_rows']}",
        f"- Local references: {ledger['summary_counts']['local_references']}",
        f"- Declared fields: {ledger['summary_counts']['fields_declared']}",
        f"- Present fields: {ledger['summary_counts']['fields_present']}",
        f"- Missing fields: {ledger['summary_counts']['fields_missing']}",
        f"- Review checks: {ledger['summary_counts']['review_checks']}",
        "",
        "## Source Evidence Rows",
        "",
    ]
    for row in ledger["source_evidence_rows"]:
        lines.extend(
            [
                f"- `{row['source_id']}` ({row['source_label']})",
                f"  - Local artifact: `{row['local_reference']}`",
                f"  - Snapshot: `{row['snapshot_id']}`",
                f"  - Role: `{row['evidence_role']}`",
                f"  - Digest: `{row['content_sha256']}`",
                f"  - Fields present: {row['field_summary']['present']}/{row['field_summary']['declared']}",
                f"  - Review checks: {len(row['review_checks'])} pending operator review",
            ]
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
            "- Records file presence, digests, field names, and review state only.",
            "- Not execution approval and not runtime input.",
        ]
    )
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a local PMBOT source evidence inventory ledger.")
    parser.add_argument("--request", required=True, help="Local source evidence inventory request JSON.")
    parser.add_argument("--output-ledger", required=True, help="Output source evidence inventory ledger JSON path.")
    parser.add_argument("--output-report", required=True, help="Output operator report Markdown path.")
    args = parser.parse_args(argv)

    request = load_source_evidence_inventory_request(args.request)
    ledger = build_source_evidence_inventory_ledger(request)
    report = build_operator_report(ledger)

    _write_json(Path(args.output_ledger), ledger)
    Path(args.output_report).write_text(report, encoding="utf-8")
    return 0


def _validate_source_artifacts(source_artifacts: list[Any]) -> list[str]:
    errors: list[str] = []
    seen_source_ids: set[str] = set()
    required_fields = (
        "evidence_role",
        "expected_contract_version",
        "expected_top_level_fields",
        "known_limitations",
        "local_reference",
        "review_checks",
        "snapshot_id",
        "source_domain",
        "source_id",
        "source_label",
        "source_type",
    )
    for index, artifact in enumerate(source_artifacts):
        path = f"source_artifacts[{index}]"
        if not isinstance(artifact, dict):
            errors.append(f"{path} must be an object")
            continue
        for field in required_fields:
            if field not in artifact:
                errors.append(f"{path} missing required field: {field}")

        source_id = artifact.get("source_id")
        if not isinstance(source_id, str) or not source_id:
            errors.append(f"{path}.source_id must be a non-empty string")
        elif source_id in seen_source_ids:
            errors.append(f"duplicate source_id: {source_id}")
        else:
            seen_source_ids.add(source_id)

        for field in (
            "evidence_role",
            "expected_contract_version",
            "snapshot_id",
            "source_domain",
            "source_label",
            "source_type",
        ):
            if not isinstance(artifact.get(field), str) or not artifact.get(field):
                errors.append(f"{path}.{field} must be a non-empty string")

        if not _is_non_empty_string_list(artifact.get("expected_top_level_fields")):
            errors.append(f"{path}.expected_top_level_fields must be a non-empty list of strings")
        if not _is_non_empty_review_check_list(artifact.get("review_checks")):
            errors.append(f"{path}.review_checks must be a non-empty list of check objects")
        if not _is_string_list(artifact.get("known_limitations")):
            errors.append(f"{path}.known_limitations must be a list of strings")

        local_reference = artifact.get("local_reference")
        if not isinstance(local_reference, str):
            errors.append(f"{path}.local_reference must be a string")
            continue

        reference_errors = _validate_local_reference(local_reference)
        errors.extend(f"{path}.{error}" for error in reference_errors)
        if reference_errors:
            continue

        artifact_path = Path(_normalize_reference(local_reference))
        if not artifact_path.exists():
            errors.append(f"{path}.local_reference must exist")
            continue
        try:
            loaded = _load_json(artifact_path)
        except (OSError, json.JSONDecodeError, SourceQualityLedgerValidationError) as exc:
            errors.append(f"{path}.local_reference must load a JSON object: {exc}")
            continue

        expected_contract = artifact.get("expected_contract_version")
        if isinstance(expected_contract, str) and loaded.get("contract_version") != expected_contract:
            errors.append(f"{path}.expected_contract_version must match local artifact contract_version")

        expected_fields = artifact.get("expected_top_level_fields")
        if _is_non_empty_string_list(expected_fields):
            missing = [field for field in expected_fields if field not in loaded]
            if missing:
                errors.append(f"{path} references fields missing from local artifact: " + ", ".join(sorted(missing)))

    return errors


def _build_evidence_row(inventory_id: str, artifact: dict[str, Any]) -> dict[str, Any]:
    reference = _normalize_reference(str(artifact["local_reference"]))
    artifact_path = Path(reference)
    loaded = _load_json(artifact_path)
    content = artifact_path.read_bytes()
    field_inventory = [
        {
            "field_name": field,
            "observed_value_type": type(loaded[field]).__name__,
            "operator_review_status": OPERATOR_REVIEW_STATUS,
            "present": field in loaded,
        }
        for field in artifact["expected_top_level_fields"]
    ]
    return {
        "artifact_format": "json_object",
        "byte_count": len(content),
        "content_sha256": hashlib.sha256(content).hexdigest(),
        "contract_version": loaded["contract_version"],
        "evidence_role": artifact["evidence_role"],
        "field_inventory": field_inventory,
        "field_summary": {
            "declared": len(field_inventory),
            "missing": sum(1 for field in field_inventory if not field["present"]),
            "present": sum(1 for field in field_inventory if field["present"]),
        },
        "known_limitations": list(artifact["known_limitations"]),
        "local_reference": reference,
        "operator_review_status": OPERATOR_REVIEW_STATUS,
        "record_id": f"{inventory_id}.{artifact['source_id']}.source_evidence",
        "review_checks": [
            {
                "check_id": check["check_id"],
                "description": check["description"],
                "operator_review_status": OPERATOR_REVIEW_STATUS,
            }
            for check in artifact["review_checks"]
        ],
        "runner_state": LEDGER_ROW_STATE,
        "snapshot_id": artifact["snapshot_id"],
        "source_domain": artifact["source_domain"],
        "source_id": artifact["source_id"],
        "source_label": artifact["source_label"],
        "source_type": artifact["source_type"],
    }


def _validate_evidence_rows(
    inventory_id: str,
    rows: list[Any],
    errors: list[str],
) -> dict[str, int]:
    seen_record_ids: set[str] = set()
    seen_source_ids: set[str] = set()
    local_references: set[str] = set()
    counts = {
        "fields_declared": 0,
        "fields_missing": 0,
        "fields_present": 0,
        "local_references": 0,
        "review_checks": 0,
        "source_evidence_rows": 0,
    }
    for index, row in enumerate(rows):
        path = f"source_evidence_rows[{index}]"
        if not isinstance(row, dict):
            errors.append(f"{path} must be an object")
            continue
        row_counts = _validate_evidence_row(path, inventory_id, row, seen_record_ids, seen_source_ids, errors)
        counts["fields_declared"] += row_counts["declared"]
        counts["fields_missing"] += row_counts["missing"]
        counts["fields_present"] += row_counts["present"]
        counts["review_checks"] += row_counts["review_checks"]
        counts["source_evidence_rows"] += 1
        local_reference = row.get("local_reference")
        if isinstance(local_reference, str):
            local_references.add(local_reference)
    counts["local_references"] = len(local_references)
    return counts


def _validate_evidence_row(
    path: str,
    inventory_id: str,
    row: dict[str, Any],
    seen_record_ids: set[str],
    seen_source_ids: set[str],
    errors: list[str],
) -> dict[str, int]:
    required_fields = (
        "artifact_format",
        "byte_count",
        "content_sha256",
        "contract_version",
        "evidence_role",
        "field_inventory",
        "field_summary",
        "known_limitations",
        "local_reference",
        "operator_review_status",
        "record_id",
        "review_checks",
        "runner_state",
        "snapshot_id",
        "source_domain",
        "source_id",
        "source_label",
        "source_type",
    )
    for field in required_fields:
        if field not in row:
            errors.append(f"{path} missing required field: {field}")

    for field in (
        "artifact_format",
        "content_sha256",
        "contract_version",
        "evidence_role",
        "local_reference",
        "record_id",
        "runner_state",
        "snapshot_id",
        "source_domain",
        "source_id",
        "source_label",
        "source_type",
    ):
        if not isinstance(row.get(field), str) or not row.get(field):
            errors.append(f"{path}.{field} must be a non-empty string")

    if row.get("artifact_format") != "json_object":
        errors.append(f"{path}.artifact_format must be json_object")
    if row.get("operator_review_status") != OPERATOR_REVIEW_STATUS:
        errors.append(f"{path}.operator_review_status must be {OPERATOR_REVIEW_STATUS}")
    if row.get("runner_state") != LEDGER_ROW_STATE:
        errors.append(f"{path}.runner_state must be {LEDGER_ROW_STATE}")
    if not _is_string_list(row.get("known_limitations")):
        errors.append(f"{path}.known_limitations must be a list of strings")

    record_id = row.get("record_id")
    source_id = row.get("source_id")
    if isinstance(record_id, str):
        if record_id in seen_record_ids:
            errors.append(f"{path}.record_id duplicates an earlier row")
        seen_record_ids.add(record_id)
    if isinstance(source_id, str):
        if source_id in seen_source_ids:
            errors.append(f"{path}.source_id duplicates an earlier row")
        seen_source_ids.add(source_id)
        if record_id != f"{inventory_id}.{source_id}.source_evidence":
            errors.append(f"{path}.record_id must be derived from inventory_id and source_id")

    loaded_artifact: dict[str, Any] | None = None
    local_reference = row.get("local_reference")
    if isinstance(local_reference, str):
        reference_errors = _validate_local_reference(local_reference)
        errors.extend(f"{path}.{error}" for error in reference_errors)
        if not reference_errors:
            artifact_path = Path(_normalize_reference(local_reference))
            try:
                loaded_artifact = _load_json(artifact_path)
                content = artifact_path.read_bytes()
                if row.get("byte_count") != len(content):
                    errors.append(f"{path}.byte_count must match local artifact bytes")
                if row.get("content_sha256") != hashlib.sha256(content).hexdigest():
                    errors.append(f"{path}.content_sha256 must match local artifact bytes")
                if row.get("contract_version") != loaded_artifact.get("contract_version"):
                    errors.append(f"{path}.contract_version must match local artifact contract_version")
            except (OSError, json.JSONDecodeError, SourceQualityLedgerValidationError) as exc:
                errors.append(f"{path}.local_reference must load a JSON object: {exc}")

    field_counts = _validate_field_inventory(path, row.get("field_inventory"), loaded_artifact, errors)
    field_summary = row.get("field_summary")
    if not isinstance(field_summary, dict):
        errors.append(f"{path}.field_summary must be an object")
    elif field_summary != field_counts:
        errors.append(f"{path}.field_summary must match field_inventory totals: " + _canonical_json(field_counts))

    review_check_count = _validate_review_checks(path, row.get("review_checks"), errors)
    return {
        "declared": field_counts["declared"],
        "missing": field_counts["missing"],
        "present": field_counts["present"],
        "review_checks": review_check_count,
    }


def _validate_field_inventory(
    row_path: str,
    field_inventory: Any,
    loaded_artifact: dict[str, Any] | None,
    errors: list[str],
) -> dict[str, int]:
    counts = {"declared": 0, "missing": 0, "present": 0}
    if not isinstance(field_inventory, list) or not field_inventory:
        errors.append(f"{row_path}.field_inventory must be a non-empty list")
        return counts

    seen_fields: set[str] = set()
    for index, field_record in enumerate(field_inventory):
        path = f"{row_path}.field_inventory[{index}]"
        counts["declared"] += 1
        if not isinstance(field_record, dict):
            errors.append(f"{path} must be an object")
            continue

        field_name = field_record.get("field_name")
        if not isinstance(field_name, str) or not field_name:
            errors.append(f"{path}.field_name must be a non-empty string")
        elif field_name in seen_fields:
            errors.append(f"{path}.field_name duplicates an earlier field")
        else:
            seen_fields.add(field_name)

        if field_record.get("operator_review_status") != OPERATOR_REVIEW_STATUS:
            errors.append(f"{path}.operator_review_status must be {OPERATOR_REVIEW_STATUS}")
        if not isinstance(field_record.get("observed_value_type"), str) or not field_record.get("observed_value_type"):
            errors.append(f"{path}.observed_value_type must be a non-empty string")

        present_value = field_record.get("present")
        if present_value is True:
            counts["present"] += 1
        elif present_value is False:
            counts["missing"] += 1
            errors.append(f"{path}.present must be true for local source evidence artifacts")
        else:
            errors.append(f"{path}.present must be a boolean")

        if loaded_artifact is None or not isinstance(field_name, str) or not field_name:
            continue
        expected_present = field_name in loaded_artifact
        if present_value != expected_present:
            errors.append(f"{path}.present must match presence in the local artifact")
        if expected_present and field_record.get("observed_value_type") != type(loaded_artifact[field_name]).__name__:
            errors.append(f"{path}.observed_value_type must match local artifact field type")

    return counts


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
) -> dict[str, int]:
    return {
        "fields_declared": sum(row["field_summary"]["declared"] for row in rows),
        "fields_missing": sum(row["field_summary"]["missing"] for row in rows),
        "fields_present": sum(row["field_summary"]["present"] for row in rows),
        "local_references": len({row["local_reference"] for row in rows}),
        "operator_review_steps": len(operator_review_steps),
        "review_checks": sum(len(row["review_checks"]) for row in rows),
        "source_evidence_rows": len(rows),
        "warnings": len(warnings),
    }


def _build_deterministic_id(inventory_id: str, request: dict[str, Any], rows: list[dict[str, Any]]) -> str:
    digest_input = {
        "inventory_id": inventory_id,
        "request": request,
        "rows": rows,
    }
    digest = hashlib.sha256(_canonical_json(digest_input).encode("utf-8")).hexdigest()[:BUILD_ID_DIGEST_LENGTH]
    return f"{inventory_id}-{digest}"


def _validate_build_id(inventory_id: str, build_id: Any, errors: list[str]) -> None:
    if not isinstance(build_id, str) or not build_id:
        errors.append("build_id must be a non-empty string")
        return
    prefix = f"{inventory_id}-"
    if not build_id.startswith(prefix):
        errors.append("build_id must start with inventory_id followed by a digest")
        return
    digest = build_id[len(prefix):]
    if len(digest) != BUILD_ID_DIGEST_LENGTH or any(character not in "0123456789abcdef" for character in digest):
        errors.append(f"build_id digest must be {BUILD_ID_DIGEST_LENGTH} lowercase hex characters")


def _find_forbidden_evidence_terms(value: Any, path: str = "$") -> list[str]:
    hits: list[str] = []
    if isinstance(value, dict):
        for key, nested_value in value.items():
            key_path = f"{path}.{key}"
            if _has_forbidden_evidence_token(str(key)):
                hits.append(key_path)
            hits.extend(_find_forbidden_evidence_terms(nested_value, key_path))
    elif isinstance(value, list):
        for index, nested_value in enumerate(value):
            hits.extend(_find_forbidden_evidence_terms(nested_value, f"{path}[{index}]"))
    elif isinstance(value, str) and _has_forbidden_evidence_token(value):
        hits.append(path)
    return hits


def _has_forbidden_evidence_token(value: str) -> bool:
    normalized = "".join(character if character.isalnum() else "_" for character in value.lower())
    tokens = {token for token in normalized.split("_") if token}
    return bool(tokens & FORBIDDEN_EVIDENCE_TERMS)


if __name__ == "__main__":
    raise SystemExit(main())
