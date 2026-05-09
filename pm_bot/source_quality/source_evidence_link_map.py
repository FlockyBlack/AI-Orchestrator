from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from pm_bot.source_quality.source_evidence_inventory_ledger import (
    EXPECTED_SAFETY_BOUNDARIES,
    LEDGER_CONTRACT_VERSION as SOURCE_EVIDENCE_INVENTORY_CONTRACT_VERSION,
    OPERATOR_REVIEW_STATUS,
    SourceQualityLedgerValidation,
    SourceQualityLedgerValidationError,
    _find_forbidden_evidence_terms,
    validate_source_evidence_inventory_ledger,
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

REQUEST_CONTRACT_VERSION = "pmbot_source_evidence_link_map_request.v1"
LINK_MAP_CONTRACT_VERSION = "pmbot_source_evidence_link_map.v1"
LINK_MAP_SCOPE = "source_evidence_link_map"
LINK_MAP_RUN_MODE = "local_static_source_evidence_link_map"
LINK_ROW_STATE = "descriptive_source_evidence_link"
BUILD_ID_DIGEST_LENGTH = 12
SAMPLE_LINK_MAP_PATH = "pm_bot/source_quality/samples/source_evidence_link_map.fixture.json"
SAMPLE_OPERATOR_REPORT_PATH = "pm_bot/source_quality/samples/source_evidence_link_map.fixture.md"


def load_source_evidence_link_map_request(path: str | Path) -> dict[str, Any]:
    reference = str(path)
    errors = _validate_local_reference(reference)
    if errors:
        raise SourceQualityLedgerValidationError(tuple(errors))
    return _load_json(Path(_normalize_reference(reference)))


def build_source_evidence_link_map(request: dict[str, Any]) -> dict[str, Any]:
    validation = validate_source_evidence_link_map_request(request)
    if not validation.valid:
        raise SourceQualityLedgerValidationError(validation.errors)

    inventory = _load_json(Path(_normalize_reference(request["source_inventory_ledger_reference"])))
    inventory_reference = _normalize_reference(request["source_inventory_ledger_reference"])
    report_reference = _normalize_reference(request["source_inventory_report_reference"])
    documentation_reference = _normalize_reference(request["documentation_reference"])
    warnings: list[str] = []
    rows = [
        _build_link_row(
            map_id=request["map_id"],
            inventory=inventory,
            inventory_reference=inventory_reference,
            report_reference=report_reference,
            documentation_reference=documentation_reference,
            source_row=source_row,
            request=request,
        )
        for source_row in inventory["source_evidence_rows"]
    ]
    rows = sorted(rows, key=lambda row: row["source_id"])
    link_map = {
        "build_id": _build_deterministic_id(request["map_id"], request, inventory, rows),
        "contract_version": LINK_MAP_CONTRACT_VERSION,
        "documentation_reference": documentation_reference,
        "errors": [],
        "local_only": True,
        "map_id": request["map_id"],
        "operator_review": {
            "status": OPERATOR_REVIEW_STATUS,
            "steps": list(request["operator_review_steps"]),
        },
        "operator_review_required": True,
        "run_mode": LINK_MAP_RUN_MODE,
        "safety_boundaries": dict(EXPECTED_SAFETY_BOUNDARIES),
        "scope": LINK_MAP_SCOPE,
        "source_evidence_links": rows,
        "source_inventory": _build_source_inventory_summary(inventory, inventory_reference),
        "summary_counts": _summary_counts(rows, request["operator_review_steps"], warnings),
        "warnings": warnings,
    }
    return link_map


def validate_source_evidence_link_map_request(request: dict[str, Any]) -> SourceQualityLedgerValidation:
    errors: list[str] = []
    if not isinstance(request, dict):
        return SourceQualityLedgerValidation(valid=False, errors=("request must be an object",))

    required_fields = (
        "contract_version",
        "documentation_reference",
        "known_limitations",
        "local_only",
        "map_id",
        "operator_review_required",
        "operator_review_steps",
        "review_checks",
        "scope",
        "source_inventory_ledger_reference",
        "source_inventory_report_reference",
    )
    for field in required_fields:
        if field not in request:
            errors.append(f"missing required request field: {field}")

    if request.get("contract_version") != REQUEST_CONTRACT_VERSION:
        errors.append(f"contract_version must be {REQUEST_CONTRACT_VERSION}")
    if request.get("scope") != LINK_MAP_SCOPE:
        errors.append(f"scope must be {LINK_MAP_SCOPE}")
    if request.get("local_only") is not True:
        errors.append("local_only must be true")
    if request.get("operator_review_required") is not True:
        errors.append("operator_review_required must be true")
    if not isinstance(request.get("map_id"), str) or not request.get("map_id"):
        errors.append("map_id must be a non-empty string")
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

    for field in (
        "documentation_reference",
        "source_inventory_ledger_reference",
        "source_inventory_report_reference",
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

    inventory_reference = request.get("source_inventory_ledger_reference")
    if isinstance(inventory_reference, str) and not _validate_local_reference(inventory_reference):
        try:
            inventory = _load_json(Path(_normalize_reference(inventory_reference)))
        except (OSError, json.JSONDecodeError, SourceQualityLedgerValidationError) as exc:
            errors.append(f"source_inventory_ledger_reference must load a JSON object: {exc}")
        else:
            inventory_validation = validate_source_evidence_inventory_ledger(inventory)
            if not inventory_validation.valid:
                errors.extend(
                    f"source_inventory_ledger_reference.{error}"
                    for error in inventory_validation.errors
                )
            if inventory.get("contract_version") != SOURCE_EVIDENCE_INVENTORY_CONTRACT_VERSION:
                errors.append(
                    "source_inventory_ledger_reference contract_version must be "
                    + SOURCE_EVIDENCE_INVENTORY_CONTRACT_VERSION
                )

    return SourceQualityLedgerValidation(valid=not errors, errors=tuple(errors))


def validate_source_evidence_link_map(link_map: dict[str, Any]) -> SourceQualityLedgerValidation:
    errors: list[str] = []
    if not isinstance(link_map, dict):
        return SourceQualityLedgerValidation(valid=False, errors=("link_map must be an object",))

    required_fields = (
        "build_id",
        "contract_version",
        "documentation_reference",
        "errors",
        "local_only",
        "map_id",
        "operator_review",
        "operator_review_required",
        "run_mode",
        "safety_boundaries",
        "scope",
        "source_evidence_links",
        "source_inventory",
        "summary_counts",
        "warnings",
    )
    for field in required_fields:
        if field not in link_map:
            errors.append(f"missing required link map field: {field}")

    if link_map.get("contract_version") != LINK_MAP_CONTRACT_VERSION:
        errors.append(f"contract_version must be {LINK_MAP_CONTRACT_VERSION}")
    if link_map.get("scope") != LINK_MAP_SCOPE:
        errors.append(f"scope must be {LINK_MAP_SCOPE}")
    if link_map.get("run_mode") != LINK_MAP_RUN_MODE:
        errors.append(f"run_mode must be {LINK_MAP_RUN_MODE}")
    if link_map.get("local_only") is not True:
        errors.append("local_only must be true")
    if link_map.get("operator_review_required") is not True:
        errors.append("operator_review_required must be true")
    if link_map.get("errors") != []:
        errors.append("errors must be an empty list")
    if not _is_string_list(link_map.get("warnings")):
        errors.append("warnings must be a list of strings")
    if link_map.get("safety_boundaries") != EXPECTED_SAFETY_BOUNDARIES:
        errors.append("safety_boundaries must match the local-only source evidence boundary")

    map_id = link_map.get("map_id")
    if not isinstance(map_id, str) or not map_id:
        errors.append("map_id must be a non-empty string")
        map_id_for_rows = ""
    else:
        map_id_for_rows = map_id
        _validate_build_id(map_id, link_map.get("build_id"), errors)

    _validate_operator_review_block(link_map.get("operator_review"), "operator_review", errors)

    forbidden_paths = _find_forbidden_evidence_terms(link_map)
    if forbidden_paths:
        errors.append(
            "forbidden source evidence term detected in link_map at: "
            + ", ".join(sorted(forbidden_paths))
        )

    inventory = _validate_source_inventory_summary(link_map.get("source_inventory"), errors)
    rows = link_map.get("source_evidence_links")
    row_counts: dict[str, int] | None = None
    if not isinstance(rows, list) or not rows:
        errors.append("source_evidence_links must be a non-empty list")
    else:
        row_counts = _validate_link_rows(map_id_for_rows, rows, inventory, errors)

    documentation_reference = link_map.get("documentation_reference")
    if isinstance(documentation_reference, str):
        _validate_digest_reference("documentation_reference", documentation_reference, None, None, errors)
    else:
        errors.append("documentation_reference must be a string")

    if row_counts is not None:
        operator_review = link_map.get("operator_review")
        operator_steps = operator_review.get("steps") if isinstance(operator_review, dict) else []
        warnings = link_map.get("warnings") if isinstance(link_map.get("warnings"), list) else []
        expected_counts = dict(row_counts)
        expected_counts["operator_review_steps"] = len(operator_steps) if isinstance(operator_steps, list) else 0
        expected_counts["warnings"] = len(warnings)
        if link_map.get("summary_counts") != expected_counts:
            errors.append("summary_counts must match source_evidence_links totals: " + _canonical_json(expected_counts))

    return SourceQualityLedgerValidation(valid=not errors, errors=tuple(errors))


def build_operator_report(link_map: dict[str, Any]) -> str:
    lines: list[str] = [
        "# PMBOT Source Evidence Link Map",
        "",
        f"Map: `{link_map['map_id']}`",
        f"Build: `{link_map['build_id']}`",
        f"Run mode: `{link_map['run_mode']}`",
        f"Operator review: `{link_map['operator_review']['status']}`",
        "",
        "## Summary Counts",
        "",
        f"- Source evidence links: {link_map['summary_counts']['source_evidence_links']}",
        f"- Source artifact references: {link_map['summary_counts']['source_artifact_references']}",
        f"- Inventory rows linked: {link_map['summary_counts']['inventory_rows_linked']}",
        f"- Local references: {link_map['summary_counts']['local_references']}",
        f"- Review checks: {link_map['summary_counts']['review_checks']}",
        "",
        "## Source Inventory",
        "",
        f"- Ledger: `{link_map['source_inventory']['local_reference']}`",
        f"- Inventory: `{link_map['source_inventory']['inventory_id']}`",
        f"- Build: `{link_map['source_inventory']['build_id']}`",
        f"- Rows: {link_map['source_inventory']['source_evidence_rows']}",
        "",
        "## Source Evidence Links",
        "",
    ]
    for row in link_map["source_evidence_links"]:
        lines.extend(
            [
                f"- `{row['source_id']}` ({row['source_label']})",
                f"  - Source artifact: `{row['source_artifact']['local_reference']}`",
                f"  - Source evidence row: `{row['source_evidence_record_id']}`",
                f"  - Inventory ledger: `{row['inventory_ledger']['local_reference']}`",
                f"  - Operator report: `{row['operator_report']['local_reference']}`",
                f"  - Documentation: `{row['documentation']['local_reference']}`",
                f"  - Review checks: {len(row['review_checks'])} pending operator review",
            ]
        )

    lines.extend(["", "## Operator Review Steps", ""])
    for step in link_map["operator_review"]["steps"]:
        lines.append(f"- {step}")

    lines.extend(
        [
            "",
            "## Safety",
            "",
            "- Local fixture/static input only.",
            "- Makes no network, LLM, endpoint, wallet, order, runtime, browser, scheduler, or worker calls.",
            "- Records local references, byte counts, digests, and pending review state only.",
            "- Does not authorize execution and is not runtime input.",
        ]
    )
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a local PMBOT source evidence link map.")
    parser.add_argument("--request", required=True, help="Local source evidence link map request JSON.")
    parser.add_argument("--output-map", required=True, help="Output source evidence link map JSON path.")
    parser.add_argument("--output-report", required=True, help="Output operator report Markdown path.")
    args = parser.parse_args(argv)

    request = load_source_evidence_link_map_request(args.request)
    link_map = build_source_evidence_link_map(request)
    report = build_operator_report(link_map)

    _write_json(Path(args.output_map), link_map)
    Path(args.output_report).write_text(report, encoding="utf-8")
    return 0


def _build_link_row(
    map_id: str,
    inventory: dict[str, Any],
    inventory_reference: str,
    report_reference: str,
    documentation_reference: str,
    source_row: dict[str, Any],
    request: dict[str, Any],
) -> dict[str, Any]:
    source_artifact_reference = _normalize_reference(source_row["local_reference"])
    return {
        "documentation": _build_digest_reference(documentation_reference),
        "inventory_ledger": {
            **_build_digest_reference(inventory_reference),
            "build_id": inventory["build_id"],
            "contract_version": inventory["contract_version"],
            "inventory_id": inventory["inventory_id"],
            "row_present": True,
        },
        "known_limitations": list(request["known_limitations"]),
        "link_id": f"{map_id}.{source_row['source_id']}.source_evidence_link",
        "link_kind": "local_static_source_evidence_review_link",
        "link_state": LINK_ROW_STATE,
        "operator_report": _build_digest_reference(report_reference),
        "operator_review_status": OPERATOR_REVIEW_STATUS,
        "review_checks": [
            {
                "check_id": check["check_id"],
                "description": check["description"],
                "operator_review_status": OPERATOR_REVIEW_STATUS,
            }
            for check in request["review_checks"]
        ],
        "source_artifact": {
            **_build_digest_reference(source_artifact_reference),
            "artifact_format": source_row["artifact_format"],
            "source_artifact_present": True,
        },
        "source_domain": source_row["source_domain"],
        "source_evidence_record_id": source_row["record_id"],
        "source_evidence_status": source_row["operator_review_status"],
        "source_id": source_row["source_id"],
        "source_label": source_row["source_label"],
        "source_type": source_row["source_type"],
    }


def _build_source_inventory_summary(inventory: dict[str, Any], inventory_reference: str) -> dict[str, Any]:
    return {
        **_build_digest_reference(inventory_reference),
        "build_id": inventory["build_id"],
        "contract_version": inventory["contract_version"],
        "inventory_id": inventory["inventory_id"],
        "operator_review_status": inventory["operator_review"]["status"],
        "run_mode": inventory["run_mode"],
        "source_evidence_rows": len(inventory["source_evidence_rows"]),
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


def _validate_source_inventory_summary(value: Any, errors: list[str]) -> dict[str, Any] | None:
    path = "source_inventory"
    if not isinstance(value, dict):
        errors.append(f"{path} must be an object")
        return None

    required_fields = (
        "build_id",
        "byte_count",
        "content_sha256",
        "contract_version",
        "inventory_id",
        "local_reference",
        "operator_review_status",
        "present",
        "run_mode",
        "source_evidence_rows",
    )
    for field in required_fields:
        if field not in value:
            errors.append(f"{path} missing required field: {field}")

    for field in (
        "build_id",
        "content_sha256",
        "contract_version",
        "inventory_id",
        "local_reference",
        "operator_review_status",
        "run_mode",
    ):
        if not isinstance(value.get(field), str) or not value.get(field):
            errors.append(f"{path}.{field} must be a non-empty string")

    if value.get("present") is not True:
        errors.append(f"{path}.present must be true")
    if value.get("operator_review_status") != OPERATOR_REVIEW_STATUS:
        errors.append(f"{path}.operator_review_status must be {OPERATOR_REVIEW_STATUS}")
    if value.get("contract_version") != SOURCE_EVIDENCE_INVENTORY_CONTRACT_VERSION:
        errors.append(f"{path}.contract_version must be {SOURCE_EVIDENCE_INVENTORY_CONTRACT_VERSION}")
    if not isinstance(value.get("source_evidence_rows"), int) or isinstance(value.get("source_evidence_rows"), bool):
        errors.append(f"{path}.source_evidence_rows must be an integer")

    inventory: dict[str, Any] | None = None
    reference = value.get("local_reference")
    if isinstance(reference, str):
        _validate_digest_reference(path, reference, value.get("byte_count"), value.get("content_sha256"), errors)
        try:
            inventory = _load_json(Path(_normalize_reference(reference)))
        except (OSError, json.JSONDecodeError, SourceQualityLedgerValidationError) as exc:
            errors.append(f"{path}.local_reference must load a JSON object: {exc}")
        else:
            validation = validate_source_evidence_inventory_ledger(inventory)
            if not validation.valid:
                errors.extend(f"{path}.{error}" for error in validation.errors)
            if value.get("inventory_id") != inventory.get("inventory_id"):
                errors.append(f"{path}.inventory_id must match local source inventory")
            if value.get("build_id") != inventory.get("build_id"):
                errors.append(f"{path}.build_id must match local source inventory")
            if value.get("run_mode") != inventory.get("run_mode"):
                errors.append(f"{path}.run_mode must match local source inventory")
            if isinstance(value.get("source_evidence_rows"), int) and value.get("source_evidence_rows") != len(
                inventory.get("source_evidence_rows", [])
            ):
                errors.append(f"{path}.source_evidence_rows must match local source inventory")
    return inventory


def _validate_link_rows(
    map_id: str,
    rows: list[Any],
    inventory: dict[str, Any] | None,
    errors: list[str],
) -> dict[str, int]:
    seen_link_ids: set[str] = set()
    seen_source_ids: set[str] = set()
    local_references: set[str] = set()
    counts = {
        "inventory_rows_linked": 0,
        "local_references": 0,
        "review_checks": 0,
        "source_artifact_references": 0,
        "source_evidence_links": 0,
    }
    inventory_rows_by_source_id = {}
    if inventory is not None:
        inventory_rows_by_source_id = {
            row["source_id"]: row
            for row in inventory.get("source_evidence_rows", [])
            if isinstance(row, dict) and isinstance(row.get("source_id"), str)
        }

    for index, row in enumerate(rows):
        path = f"source_evidence_links[{index}]"
        if not isinstance(row, dict):
            errors.append(f"{path} must be an object")
            continue
        row_counts = _validate_link_row(
            path,
            map_id,
            row,
            inventory_rows_by_source_id,
            seen_link_ids,
            seen_source_ids,
            errors,
        )
        counts["inventory_rows_linked"] += row_counts["inventory_rows_linked"]
        counts["review_checks"] += row_counts["review_checks"]
        counts["source_artifact_references"] += row_counts["source_artifact_references"]
        counts["source_evidence_links"] += 1
        for reference in row_counts["local_references"]:
            local_references.add(reference)
    counts["local_references"] = len(local_references)
    return counts


def _validate_link_row(
    path: str,
    map_id: str,
    row: dict[str, Any],
    inventory_rows_by_source_id: dict[str, dict[str, Any]],
    seen_link_ids: set[str],
    seen_source_ids: set[str],
    errors: list[str],
) -> dict[str, Any]:
    required_fields = (
        "documentation",
        "inventory_ledger",
        "known_limitations",
        "link_id",
        "link_kind",
        "link_state",
        "operator_report",
        "operator_review_status",
        "review_checks",
        "source_artifact",
        "source_domain",
        "source_evidence_record_id",
        "source_evidence_status",
        "source_id",
        "source_label",
        "source_type",
    )
    for field in required_fields:
        if field not in row:
            errors.append(f"{path} missing required field: {field}")

    for field in (
        "link_id",
        "link_kind",
        "link_state",
        "source_domain",
        "source_evidence_record_id",
        "source_evidence_status",
        "source_id",
        "source_label",
        "source_type",
    ):
        if not isinstance(row.get(field), str) or not row.get(field):
            errors.append(f"{path}.{field} must be a non-empty string")

    if row.get("link_state") != LINK_ROW_STATE:
        errors.append(f"{path}.link_state must be {LINK_ROW_STATE}")
    if row.get("operator_review_status") != OPERATOR_REVIEW_STATUS:
        errors.append(f"{path}.operator_review_status must be {OPERATOR_REVIEW_STATUS}")
    if row.get("source_evidence_status") != OPERATOR_REVIEW_STATUS:
        errors.append(f"{path}.source_evidence_status must be {OPERATOR_REVIEW_STATUS}")
    if not _is_string_list(row.get("known_limitations")):
        errors.append(f"{path}.known_limitations must be a list of strings")

    link_id = row.get("link_id")
    source_id = row.get("source_id")
    if isinstance(link_id, str):
        if link_id in seen_link_ids:
            errors.append(f"{path}.link_id duplicates an earlier row")
        seen_link_ids.add(link_id)
    if isinstance(source_id, str):
        if source_id in seen_source_ids:
            errors.append(f"{path}.source_id duplicates an earlier row")
        seen_source_ids.add(source_id)
        if link_id != f"{map_id}.{source_id}.source_evidence_link":
            errors.append(f"{path}.link_id must be derived from map_id and source_id")

    review_check_count = _validate_review_checks(path, row.get("review_checks"), errors)
    local_references: set[str] = set()
    reference_objects = (
        ("documentation", row.get("documentation")),
        ("inventory_ledger", row.get("inventory_ledger")),
        ("operator_report", row.get("operator_report")),
        ("source_artifact", row.get("source_artifact")),
    )
    for reference_name, reference_value in reference_objects:
        reference = _validate_reference_object(f"{path}.{reference_name}", reference_value, errors)
        if reference is not None:
            local_references.add(reference)

    inventory_row = inventory_rows_by_source_id.get(source_id) if isinstance(source_id, str) else None
    inventory_rows_linked = 0
    source_artifact_references = 0
    if inventory_row is None:
        errors.append(f"{path}.source_id must exist in source inventory")
    else:
        inventory_rows_linked = 1
        if row.get("source_evidence_record_id") != inventory_row.get("record_id"):
            errors.append(f"{path}.source_evidence_record_id must match source inventory row")
        if row.get("source_domain") != inventory_row.get("source_domain"):
            errors.append(f"{path}.source_domain must match source inventory row")
        if row.get("source_label") != inventory_row.get("source_label"):
            errors.append(f"{path}.source_label must match source inventory row")
        if row.get("source_type") != inventory_row.get("source_type"):
            errors.append(f"{path}.source_type must match source inventory row")
        source_artifact = row.get("source_artifact")
        if isinstance(source_artifact, dict):
            source_artifact_references = 1
            if source_artifact.get("local_reference") != inventory_row.get("local_reference"):
                errors.append(f"{path}.source_artifact.local_reference must match source inventory row")
            if source_artifact.get("content_sha256") != inventory_row.get("content_sha256"):
                errors.append(f"{path}.source_artifact.content_sha256 must match source inventory row")
            if source_artifact.get("byte_count") != inventory_row.get("byte_count"):
                errors.append(f"{path}.source_artifact.byte_count must match source inventory row")
            if source_artifact.get("artifact_format") != inventory_row.get("artifact_format"):
                errors.append(f"{path}.source_artifact.artifact_format must match source inventory row")
            if source_artifact.get("source_artifact_present") is not True:
                errors.append(f"{path}.source_artifact.source_artifact_present must be true")

    return {
        "inventory_rows_linked": inventory_rows_linked,
        "local_references": local_references,
        "review_checks": review_check_count,
        "source_artifact_references": source_artifact_references,
    }


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
) -> dict[str, int]:
    local_references = set()
    for row in rows:
        local_references.update(
            {
                row["documentation"]["local_reference"],
                row["inventory_ledger"]["local_reference"],
                row["operator_report"]["local_reference"],
                row["source_artifact"]["local_reference"],
            }
        )
    return {
        "inventory_rows_linked": len(rows),
        "local_references": len(local_references),
        "operator_review_steps": len(operator_review_steps),
        "review_checks": sum(len(row["review_checks"]) for row in rows),
        "source_artifact_references": len({row["source_artifact"]["local_reference"] for row in rows}),
        "source_evidence_links": len(rows),
        "warnings": len(warnings),
    }


def _build_deterministic_id(
    map_id: str,
    request: dict[str, Any],
    inventory: dict[str, Any],
    rows: list[dict[str, Any]],
) -> str:
    digest_input = {
        "inventory": inventory,
        "map_id": map_id,
        "request": request,
        "rows": rows,
    }
    digest = hashlib.sha256(_canonical_json(digest_input).encode("utf-8")).hexdigest()[:BUILD_ID_DIGEST_LENGTH]
    return f"{map_id}-{digest}"


def _validate_build_id(map_id: str, build_id: Any, errors: list[str]) -> None:
    if not isinstance(build_id, str) or not build_id:
        errors.append("build_id must be a non-empty string")
        return
    prefix = f"{map_id}-"
    if not build_id.startswith(prefix):
        errors.append("build_id must start with map_id followed by a digest")
        return
    digest = build_id[len(prefix):]
    if len(digest) != BUILD_ID_DIGEST_LENGTH or any(character not in "0123456789abcdef" for character in digest):
        errors.append(f"build_id digest must be {BUILD_ID_DIGEST_LENGTH} lowercase hex characters")


if __name__ == "__main__":
    raise SystemExit(main())
