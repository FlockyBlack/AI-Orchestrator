from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
from typing import Any

from pm_bot.source_quality.source_contradiction_ledger import validate_source_contradiction_ledger
from pm_bot.source_quality.source_evidence_link_map import validate_source_evidence_link_map
from pm_bot.source_quality.source_quality_regression_fixture import validate_source_quality_regression_fixture
from pm_bot.source_quality.source_quality_report_summary import validate_source_quality_report_summary
from pm_bot.source_quality.source_staleness_check_spec import validate_source_staleness_check_spec
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
    validate_unified_source_quality_ledger,
)

TASK_ID = "PMBOT-REHEARSAL-014-REHEARSAL-SOURCE-QUALITY-LINKS-LOCAL-ONLY"
LINKS_CONTRACT_VERSION = "pmbot_rehearsal_source_quality_links.v1"
LINK_SET_ID = "pmbot-rehearsal-source-quality-links-001"
LINKS_RUN_MODE = "local_static_rehearsal_source_quality_links"
LINKS_CREATED_AT = "2026-05-09T09:30:00Z"
LINK_ROW_STATE = "descriptive_rehearsal_source_quality_link"
BUILD_ID_DIGEST_LENGTH = 12

SAMPLE_LINKS_PATH = "pm_bot/source_quality/samples/rehearsal_source_quality_links.fixture.json"
SAMPLE_OPERATOR_REPORT_PATH = "pm_bot/source_quality/samples/rehearsal_source_quality_links.fixture.md"

DOCUMENTATION_PATH = "docs/PMBOT_REHEARSAL_014_REHEARSAL_SOURCE_QUALITY_LINKS_LOCAL_ONLY.md"
REHEARSAL_SOURCE_EVIDENCE_BUNDLE_PATH = (
    "pm_bot/tests/fixtures/rehearsal/pmbot_rehearsal_source_evidence_bundle.valid.json"
)
REHEARSAL_STALENESS_CASE_SET_PATH = (
    "pm_bot/tests/fixtures/rehearsal/pmbot_rehearsal_staleness_case_set.valid.json"
)
REHEARSAL_CONTRADICTION_CASE_SET_PATH = (
    "pm_bot/tests/fixtures/rehearsal/pmbot_rehearsal_contradiction_case_set.valid.json"
)
SOURCE_QUALITY_LEDGER_PATH = "pm_bot/source_quality/samples/unified_source_quality_ledger.fixture.json"
SOURCE_QUALITY_REPORT_SUMMARY_PATH = "pm_bot/source_quality/samples/source_quality_report_summary.fixture.json"
SOURCE_QUALITY_REGRESSION_FIXTURE_PATH = "pm_bot/source_quality/samples/source_quality_regression.fixture.json"
SOURCE_EVIDENCE_LINK_MAP_PATH = "pm_bot/source_quality/samples/source_evidence_link_map.fixture.json"
SOURCE_STALENESS_CHECK_SPEC_PATH = "pm_bot/source_quality/samples/source_staleness_check_spec.fixture.json"
SOURCE_CONTRADICTION_LEDGER_PATH = "pm_bot/source_quality/samples/source_contradiction_ledger.fixture.json"

REQUIRED_VALIDATION_COMMANDS = (
    "python -m compileall pm_bot tests",
    "pytest pm_bot/tests tests/test_codex_queue_pmbot_templates.py",
)

OPERATOR_REVIEW_STEPS = (
    "Confirm each rehearsal artifact row resolves to local source quality record identifiers.",
    "Confirm source quality artifact byte counts and SHA-256 digests match current local bytes.",
    "Confirm values remain in referenced local artifacts and link rows stay pending operator review.",
)

EXPECTED_SAFETY_BOUNDARIES = {
    "authenticated_endpoint_calls_allowed": False,
    "background_process_allowed": False,
    "browser_automation_allowed": False,
    "credential_or_secret_access_allowed": False,
    "execution_endpoint_calls_allowed": False,
    "external_service_calls_allowed": False,
    "llm_provider_calls_allowed": False,
    "local_static_samples_only": True,
    "market_api_calls_allowed": False,
    "market_ranking_allowed": False,
    "network_calls_allowed": False,
    "numeric_prediction_metric_allowed": False,
    "openrouter_calls_allowed": False,
    "operator_review_required": True,
    "order_or_trade_surface_changes_allowed": False,
    "paper_mode_only": True,
    "polymarket_api_calls_allowed": False,
    "rehearsal_link_runtime_input_allowed": False,
    "resident_process_allowed": False,
    "run_codex_changes_allowed": False,
    "runtime_or_dispatcher_changes_allowed": False,
    "scheduler_or_worker_allowed": False,
    "trading_endpoint_calls_allowed": False,
    "transaction_endpoint_calls_allowed": False,
    "value_transform_allowed": False,
    "wallet_or_signing_material_access_allowed": False,
}

EXPECTED_LINK_FIELDS = (
    "link_id",
    "link_kind",
    "link_state",
    "local_reference_policy",
    "operator_review_status",
    "rehearsal_artifact_ids",
    "rehearsal_record_ids",
    "review_checks",
    "source_id",
    "source_quality_artifact_ids",
    "source_quality_record_ids",
    "value_policy",
)

EXPECTED_REHEARSAL_RECORD_ID_FIELDS = (
    "contradiction_case_ids",
    "source_evidence_bundle_record_id",
    "staleness_case_ids",
)

EXPECTED_SOURCE_QUALITY_RECORD_ID_FIELDS = (
    "source_contradiction_row_ids",
    "source_evidence_link_id",
    "source_quality_ledger_row_id",
    "source_quality_regression_ledger_row_id",
    "source_quality_report_row_id",
    "source_staleness_check_id",
)

REVIEW_CHECKS = (
    {
        "check_id": "rehearsal_record_presence",
        "description": "Confirm rehearsal record identifiers resolve in local rehearsal fixtures.",
    },
    {
        "check_id": "source_quality_record_presence",
        "description": "Confirm source quality record identifiers exist in named local artifacts.",
    },
    {
        "check_id": "local_reference_digest",
        "description": "Confirm linked local artifact byte counts and digests match current local bytes.",
    },
    {
        "check_id": "pending_review_state",
        "description": "Confirm links and source quality artifacts remain pending operator review.",
    },
)

REHEARSAL_ARTIFACT_SPECS: tuple[dict[str, Any], ...] = (
    {
        "artifact_id": "rehearsal_source_evidence_bundle_fixture",
        "contract_version": "pmbot_rehearsal_source_evidence_bundle.v1",
        "input_key": "rehearsal_source_evidence_bundle",
        "local_reference": REHEARSAL_SOURCE_EVIDENCE_BUNDLE_PATH,
        "record_collection": "bundle_records",
    },
    {
        "artifact_id": "rehearsal_staleness_case_set_fixture",
        "contract_version": "pmbot_rehearsal_staleness_case_set.v1",
        "input_key": "rehearsal_staleness_case_set",
        "local_reference": REHEARSAL_STALENESS_CASE_SET_PATH,
        "record_collection": "case_records",
    },
    {
        "artifact_id": "rehearsal_contradiction_case_set_fixture",
        "contract_version": "pmbot_rehearsal_contradiction_case_set.v1",
        "input_key": "rehearsal_contradiction_case_set",
        "local_reference": REHEARSAL_CONTRADICTION_CASE_SET_PATH,
        "record_collection": "case_records",
    },
)

SOURCE_QUALITY_ARTIFACT_SPECS: tuple[dict[str, Any], ...] = (
    {
        "artifact_id": "unified_source_quality_ledger_sample",
        "contract_version": "pmbot_unified_source_quality_ledger.v1",
        "input_key": "unified_source_quality_ledger",
        "local_reference": SOURCE_QUALITY_LEDGER_PATH,
        "record_collection": "source_quality_rows",
    },
    {
        "artifact_id": "source_quality_report_summary_sample",
        "contract_version": "pmbot_source_quality_report_summary.v1",
        "input_key": "source_quality_report_summary",
        "local_reference": SOURCE_QUALITY_REPORT_SUMMARY_PATH,
        "record_collection": "report_summary_rows",
    },
    {
        "artifact_id": "source_quality_regression_fixture_sample",
        "contract_version": "pmbot_source_quality_regression_fixture.v1",
        "input_key": "source_quality_regression_fixture",
        "local_reference": SOURCE_QUALITY_REGRESSION_FIXTURE_PATH,
        "record_collection": "regression_fixture_rows",
    },
    {
        "artifact_id": "source_evidence_link_map_sample",
        "contract_version": "pmbot_source_evidence_link_map.v1",
        "input_key": "source_evidence_link_map",
        "local_reference": SOURCE_EVIDENCE_LINK_MAP_PATH,
        "record_collection": "source_evidence_links",
    },
    {
        "artifact_id": "source_staleness_check_spec_sample",
        "contract_version": "pmbot_source_staleness_check_spec.v1",
        "input_key": "source_staleness_check_spec",
        "local_reference": SOURCE_STALENESS_CHECK_SPEC_PATH,
        "record_collection": "source_staleness_checks",
    },
    {
        "artifact_id": "source_contradiction_ledger_sample",
        "contract_version": "pmbot_source_contradiction_ledger.v1",
        "input_key": "source_contradiction_ledger",
        "local_reference": SOURCE_CONTRADICTION_LEDGER_PATH,
        "record_collection": "source_contradiction_rows",
    },
)

SOURCE_LINK_SPECS = (
    {"source_id": "official_daily_climate_report"},
    {"source_id": "airport_station_observation_log"},
)


def load_rehearsal_source_quality_links(path: str | Path) -> dict[str, Any]:
    reference = str(path)
    errors = _validate_local_reference(reference)
    if errors:
        raise SourceQualityLedgerValidationError(tuple(errors))
    return _load_json(Path(_normalize_reference(reference)))


def load_rehearsal_source_quality_link_inputs() -> dict[str, dict[str, Any]]:
    inputs: dict[str, dict[str, Any]] = {}
    for spec in REHEARSAL_ARTIFACT_SPECS + SOURCE_QUALITY_ARTIFACT_SPECS:
        inputs[str(spec["input_key"])] = _load_local_json(str(spec["local_reference"]))
    return inputs


def build_rehearsal_source_quality_links(
    inputs: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    inputs = inputs if inputs is not None else load_rehearsal_source_quality_link_inputs()
    validation_errors = _validate_input_payloads(inputs)
    if validation_errors:
        raise SourceQualityLedgerValidationError(tuple(validation_errors))

    rehearsal_artifacts = [
        _build_artifact_reference(spec, inputs[str(spec["input_key"])])
        for spec in REHEARSAL_ARTIFACT_SPECS
    ]
    source_quality_artifacts = [
        _build_artifact_reference(spec, inputs[str(spec["input_key"])])
        for spec in SOURCE_QUALITY_ARTIFACT_SPECS
    ]
    indexes = _build_source_link_indexes(inputs)
    link_rows = [
        _build_link_row(str(spec["source_id"]), indexes)
        for spec in SOURCE_LINK_SPECS
    ]
    warnings: list[str] = []
    link_set = {
        "build_id": "",
        "contract_version": LINKS_CONTRACT_VERSION,
        "created_at": LINKS_CREATED_AT,
        "documentation": _build_digest_reference(DOCUMENTATION_PATH),
        "errors": [],
        "link_fields": list(EXPECTED_LINK_FIELDS),
        "link_set_id": LINK_SET_ID,
        "local_only": True,
        "operator_review": {
            "reviewed_at": None,
            "reviewed_by": None,
            "status": OPERATOR_REVIEW_STATUS,
        },
        "operator_review_required": True,
        "operator_review_steps": list(OPERATOR_REVIEW_STEPS),
        "rehearsal_artifacts": rehearsal_artifacts,
        "rehearsal_source_quality_links": link_rows,
        "required_validation_commands": list(REQUIRED_VALIDATION_COMMANDS),
        "run_mode": LINKS_RUN_MODE,
        "safety_boundaries": dict(EXPECTED_SAFETY_BOUNDARIES),
        "source_quality_artifacts": source_quality_artifacts,
        "summary_counts": _summary_counts(rehearsal_artifacts, source_quality_artifacts, link_rows, warnings),
        "task_id": TASK_ID,
        "warnings": warnings,
    }
    link_set["build_id"] = _build_deterministic_id(link_set)
    return link_set


def validate_rehearsal_source_quality_links(link_set: dict[str, Any]) -> SourceQualityLedgerValidation:
    errors: list[str] = []
    if not isinstance(link_set, dict):
        return SourceQualityLedgerValidation(valid=False, errors=("link_set must be an object",))

    required_fields = (
        "build_id",
        "contract_version",
        "created_at",
        "documentation",
        "errors",
        "link_fields",
        "link_set_id",
        "local_only",
        "operator_review",
        "operator_review_required",
        "operator_review_steps",
        "rehearsal_artifacts",
        "rehearsal_source_quality_links",
        "required_validation_commands",
        "run_mode",
        "safety_boundaries",
        "source_quality_artifacts",
        "summary_counts",
        "task_id",
        "warnings",
    )
    for field in required_fields:
        if field not in link_set:
            errors.append(f"missing required rehearsal source quality link field: {field}")

    if link_set.get("task_id") != TASK_ID:
        errors.append(f"task_id must be {TASK_ID}")
    if link_set.get("contract_version") != LINKS_CONTRACT_VERSION:
        errors.append(f"contract_version must be {LINKS_CONTRACT_VERSION}")
    if link_set.get("link_set_id") != LINK_SET_ID:
        errors.append(f"link_set_id must be {LINK_SET_ID}")
    if link_set.get("run_mode") != LINKS_RUN_MODE:
        errors.append(f"run_mode must be {LINKS_RUN_MODE}")
    if link_set.get("created_at") != LINKS_CREATED_AT:
        errors.append(f"created_at must be {LINKS_CREATED_AT}")
    if link_set.get("local_only") is not True:
        errors.append("local_only must be true")
    if link_set.get("operator_review_required") is not True:
        errors.append("operator_review_required must be true")
    if link_set.get("errors") != []:
        errors.append("errors must be an empty list")
    if not _is_string_list(link_set.get("warnings")):
        errors.append("warnings must be a list of strings")
    if tuple(link_set.get("link_fields", ())) != EXPECTED_LINK_FIELDS:
        errors.append("link_fields must match the fixed rehearsal source quality link contract")
    if tuple(link_set.get("operator_review_steps", ())) != OPERATOR_REVIEW_STEPS:
        errors.append("operator_review_steps must match the fixed review steps")
    if link_set.get("required_validation_commands") != list(REQUIRED_VALIDATION_COMMANDS):
        errors.append("required_validation_commands must match the local validation contract")
    if link_set.get("safety_boundaries") != EXPECTED_SAFETY_BOUNDARIES:
        errors.append("safety_boundaries must match the closed rehearsal source quality boundary")

    _validate_operator_review(link_set.get("operator_review"), errors)
    _validate_reference_object("documentation", link_set.get("documentation"), errors)
    rehearsal_artifacts = _validate_artifacts(
        "rehearsal_artifacts",
        link_set.get("rehearsal_artifacts"),
        REHEARSAL_ARTIFACT_SPECS,
        errors,
    )
    source_quality_artifacts = _validate_artifacts(
        "source_quality_artifacts",
        link_set.get("source_quality_artifacts"),
        SOURCE_QUALITY_ARTIFACT_SPECS,
        errors,
    )
    link_counts = _validate_link_rows(
        link_set.get("rehearsal_source_quality_links"),
        rehearsal_artifacts,
        source_quality_artifacts,
        errors,
    )
    _validate_build_id(link_set, errors)

    forbidden_paths = _find_forbidden_decision_terms(link_set)
    if forbidden_paths:
        errors.append(
            "forbidden decision/action term detected in rehearsal source quality links at: "
            + ", ".join(sorted(forbidden_paths))
        )

    if rehearsal_artifacts is not None and source_quality_artifacts is not None and link_counts is not None:
        warnings = link_set.get("warnings") if isinstance(link_set.get("warnings"), list) else []
        expected_counts = _summary_counts(
            list(rehearsal_artifacts.values()),
            list(source_quality_artifacts.values()),
            link_set["rehearsal_source_quality_links"],
            warnings,
        )
        if link_set.get("summary_counts") != expected_counts:
            errors.append("summary_counts must match rehearsal source quality link totals: " + _canonical_json(expected_counts))

    return SourceQualityLedgerValidation(valid=not errors, errors=tuple(errors))


def build_operator_report(link_set: dict[str, Any]) -> str:
    lines: list[str] = [
        "# PMBOT Rehearsal Source Quality Links",
        "",
        f"Task: `{link_set['task_id']}`",
        f"Link set: `{link_set['link_set_id']}`",
        f"Build: `{link_set['build_id']}`",
        f"Contract: `{link_set['contract_version']}`",
        f"Run mode: `{link_set['run_mode']}`",
        f"Operator review: `{link_set['operator_review']['status']}`",
        "",
        "## Summary",
        "",
        f"- Rehearsal source quality links: {link_set['summary_counts']['rehearsal_source_quality_links']}",
        f"- Rehearsal artifacts: {link_set['summary_counts']['rehearsal_artifacts']}",
        f"- Source quality artifacts: {link_set['summary_counts']['source_quality_artifacts']}",
        f"- Source quality record links: {link_set['summary_counts']['source_quality_record_links']}",
        f"- Rehearsal record links: {link_set['summary_counts']['rehearsal_record_links']}",
        f"- Local references: {link_set['summary_counts']['local_references']}",
        "",
        "## Rehearsal Artifacts",
        "",
    ]
    for artifact in link_set["rehearsal_artifacts"]:
        lines.append(
            f"- `{artifact['artifact_id']}` -> `{artifact['local_reference']}` "
            f"({artifact['record_count']} records)"
        )

    lines.extend(["", "## Source Quality Artifacts", ""])
    for artifact in link_set["source_quality_artifacts"]:
        lines.append(
            f"- `{artifact['artifact_id']}` -> `{artifact['local_reference']}` "
            f"({artifact['record_count']} records)"
        )

    lines.extend(["", "## Link Rows", ""])
    for row in link_set["rehearsal_source_quality_links"]:
        source_record_ids = row["source_quality_record_ids"]
        rehearsal_record_ids = row["rehearsal_record_ids"]
        lines.extend(
            [
                f"- `{row['source_id']}`",
                f"  - Source quality ledger row: `{source_record_ids['source_quality_ledger_row_id']}`",
                f"  - Source quality report row: `{source_record_ids['source_quality_report_row_id']}`",
                f"  - Source quality regression row: `{source_record_ids['source_quality_regression_ledger_row_id']}`",
                f"  - Source evidence link: `{source_record_ids['source_evidence_link_id']}`",
                f"  - Source staleness check: `{source_record_ids['source_staleness_check_id']}`",
                f"  - Source contradiction rows: {len(source_record_ids['source_contradiction_row_ids'])}",
                f"  - Rehearsal staleness cases: {len(rehearsal_record_ids['staleness_case_ids'])}",
                f"  - Rehearsal contradiction cases: {len(rehearsal_record_ids['contradiction_case_ids'])}",
            ]
        )

    lines.extend(["", "## Operator Review Steps", ""])
    for step in link_set["operator_review_steps"]:
        lines.append(f"- {step}")

    lines.extend(
        [
            "",
            "## Safety",
            "",
            "- Local files, local fixtures, and static samples only.",
            "- Makes no network, OpenRouter, Polymarket, LLM, external service, authenticated endpoint, wallet, order, transaction, runtime, browser, scheduler, or worker calls.",
            "- Records local links and pending review state only; source values remain in referenced artifacts.",
            "- No forecast scoring, action guidance, market ranking, outcome resolution, selection advice, or trade instruction output.",
            "- Not execution approval and not runtime input.",
        ]
    )
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build local PMBOT rehearsal source quality links.")
    parser.add_argument("--output-links", required=True, help="Output rehearsal source quality links JSON path.")
    parser.add_argument("--output-report", required=True, help="Output operator report Markdown path.")
    args = parser.parse_args(argv)

    link_set = build_rehearsal_source_quality_links()
    validation = validate_rehearsal_source_quality_links(link_set)
    if not validation.valid:
        raise SourceQualityLedgerValidationError(validation.errors)

    _write_json(Path(args.output_links), link_set)
    Path(args.output_report).write_text(build_operator_report(link_set), encoding="utf-8")
    return 0


def _validate_input_payloads(inputs: dict[str, dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    for spec in REHEARSAL_ARTIFACT_SPECS:
        key = str(spec["input_key"])
        payload = inputs.get(key)
        if not isinstance(payload, dict):
            errors.append(f"{key} input must be an object")
            continue
        if payload.get("contract_version") != spec["contract_version"]:
            errors.append(f"{key}.contract_version must be {spec['contract_version']}")
        if payload.get("local_only") is not True:
            errors.append(f"{key}.local_only must be true")
        if _operator_review_status(payload) != OPERATOR_REVIEW_STATUS:
            errors.append(f"{key}.operator_review.status must be {OPERATOR_REVIEW_STATUS}")
        records = payload.get(spec["record_collection"])
        if not isinstance(records, list) or not records:
            errors.append(f"{key}.{spec['record_collection']} must be a non-empty list")

    source_validators = {
        "unified_source_quality_ledger": validate_unified_source_quality_ledger,
        "source_quality_report_summary": validate_source_quality_report_summary,
        "source_quality_regression_fixture": validate_source_quality_regression_fixture,
        "source_evidence_link_map": validate_source_evidence_link_map,
        "source_staleness_check_spec": validate_source_staleness_check_spec,
        "source_contradiction_ledger": validate_source_contradiction_ledger,
    }
    for spec in SOURCE_QUALITY_ARTIFACT_SPECS:
        key = str(spec["input_key"])
        payload = inputs.get(key)
        if not isinstance(payload, dict):
            errors.append(f"{key} input must be an object")
            continue
        validation = source_validators[key](payload)
        if not validation.valid:
            errors.extend(f"{key}.{error}" for error in validation.errors)
        if payload.get("contract_version") != spec["contract_version"]:
            errors.append(f"{key}.contract_version must be {spec['contract_version']}")
        records = payload.get(spec["record_collection"])
        if not isinstance(records, list) or not records:
            errors.append(f"{key}.{spec['record_collection']} must be a non-empty list")

    if not errors:
        errors.extend(_validate_source_link_coverage(inputs))
    return errors


def _validate_source_link_coverage(inputs: dict[str, dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    indexes = _build_source_link_indexes(inputs)
    bundle_record = indexes["source_evidence_bundle_record"]
    bundle_record_ids = bundle_record.get("source_evidence_record_ids", {}) if isinstance(bundle_record, dict) else {}
    bundle_staleness_ids = set(bundle_record_ids.get("staleness_check_ids", []))
    bundle_contradiction_ids = set(bundle_record_ids.get("contradiction_row_ids", []))
    bundle_link_ids = set(bundle_record_ids.get("link_map_row_ids", []))

    for spec in SOURCE_LINK_SPECS:
        source_id = str(spec["source_id"])
        expected = _expected_ids_for_source(source_id, indexes)
        for collection_name, index_key in (
            ("source quality ledger", "source_quality_ledger_rows"),
            ("source quality report", "source_quality_report_rows"),
            ("source quality regression", "source_quality_regression_rows"),
            ("source evidence link map", "source_evidence_links"),
            ("source staleness checks", "source_staleness_checks"),
        ):
            if source_id not in indexes[index_key]:
                errors.append(f"{source_id} missing from {collection_name}")
        if not expected["source_quality_record_ids"]["source_contradiction_row_ids"]:
            errors.append(f"{source_id} must have at least one source contradiction row")
        if not expected["rehearsal_record_ids"]["staleness_case_ids"]:
            errors.append(f"{source_id} must have at least one rehearsal staleness case")
        if not expected["rehearsal_record_ids"]["contradiction_case_ids"]:
            errors.append(f"{source_id} must have at least one rehearsal contradiction case")
        if expected["source_quality_record_ids"]["source_evidence_link_id"] not in bundle_link_ids:
            errors.append(f"{source_id} source evidence link must be listed in the rehearsal source bundle")
        if expected["source_quality_record_ids"]["source_staleness_check_id"] not in bundle_staleness_ids:
            errors.append(f"{source_id} source staleness check must be listed in the rehearsal source bundle")
        for row_id in expected["source_quality_record_ids"]["source_contradiction_row_ids"]:
            if row_id not in bundle_contradiction_ids:
                errors.append(f"{source_id} source contradiction row must be listed in the rehearsal source bundle")
    return errors


def _build_artifact_reference(spec: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    records = payload[spec["record_collection"]]
    return {
        **_build_digest_reference(str(spec["local_reference"])),
        "artifact_id": spec["artifact_id"],
        "contract_version": spec["contract_version"],
        "operator_review_status": _operator_review_status(payload),
        "record_collection": spec["record_collection"],
        "record_count": len(records),
        "record_ids": [_record_identifier(record) for record in records],
    }


def _build_link_row(source_id: str, indexes: dict[str, Any]) -> dict[str, Any]:
    expected = _expected_ids_for_source(source_id, indexes)
    return {
        "link_id": f"{LINK_SET_ID}.{source_id}.rehearsal_source_quality_link",
        "link_kind": "local_rehearsal_artifact_to_source_quality_record_link",
        "link_state": LINK_ROW_STATE,
        "local_reference_policy": "local_static_references_only",
        "operator_review_status": OPERATOR_REVIEW_STATUS,
        "rehearsal_artifact_ids": [spec["artifact_id"] for spec in REHEARSAL_ARTIFACT_SPECS],
        "rehearsal_record_ids": expected["rehearsal_record_ids"],
        "review_checks": [
            {
                "check_id": check["check_id"],
                "description": check["description"],
                "operator_review_status": OPERATOR_REVIEW_STATUS,
            }
            for check in REVIEW_CHECKS
        ],
        "source_id": source_id,
        "source_quality_artifact_ids": [spec["artifact_id"] for spec in SOURCE_QUALITY_ARTIFACT_SPECS],
        "source_quality_record_ids": expected["source_quality_record_ids"],
        "value_policy": "record_identifiers_only_source_values_remain_in_local_artifacts",
    }


def _build_source_link_indexes(inputs: dict[str, dict[str, Any]]) -> dict[str, Any]:
    staleness_checks = _index_by_source_id(inputs["source_staleness_check_spec"]["source_staleness_checks"])
    contradiction_rows_by_source: dict[str, list[dict[str, Any]]] = {}
    for row in inputs["source_contradiction_ledger"]["source_contradiction_rows"]:
        row_sources = []
        for source_key in ("left_source", "right_source"):
            source = row.get(source_key) if isinstance(row, dict) else None
            source_id = source.get("source_id") if isinstance(source, dict) else None
            if isinstance(source_id, str) and source_id not in row_sources:
                row_sources.append(source_id)
        for source_id in row_sources:
            contradiction_rows_by_source.setdefault(source_id, []).append(row)

    staleness_cases_by_source: dict[str, list[dict[str, Any]]] = {}
    for source_id, check in staleness_checks.items():
        check_id = check["check_id"]
        staleness_cases_by_source[source_id] = [
            case
            for case in inputs["rehearsal_staleness_case_set"]["case_records"]
            if case.get("linked_source_staleness_check_id") == check_id
        ]

    contradiction_cases_by_source: dict[str, list[dict[str, Any]]] = {}
    for case in inputs["rehearsal_contradiction_case_set"]["case_records"]:
        for field in ("left_source_id", "right_source_id"):
            source_id = case.get(field)
            if isinstance(source_id, str):
                contradiction_cases_by_source.setdefault(source_id, []).append(case)

    return {
        "source_contradiction_rows_by_source": contradiction_rows_by_source,
        "source_evidence_bundle_record": inputs["rehearsal_source_evidence_bundle"]["bundle_records"][0],
        "source_evidence_links": _index_by_source_id(inputs["source_evidence_link_map"]["source_evidence_links"]),
        "source_quality_ledger_rows": _index_by_source_id(inputs["unified_source_quality_ledger"]["source_quality_rows"]),
        "source_quality_regression_rows": _index_by_source_id(inputs["source_quality_regression_fixture"]["regression_fixture_rows"]),
        "source_quality_report_rows": _index_by_source_id(inputs["source_quality_report_summary"]["report_summary_rows"]),
        "source_staleness_checks": staleness_checks,
        "rehearsal_contradiction_cases_by_source": contradiction_cases_by_source,
        "rehearsal_staleness_cases_by_source": staleness_cases_by_source,
    }


def _expected_ids_for_source(source_id: str, indexes: dict[str, Any]) -> dict[str, Any]:
    return {
        "rehearsal_record_ids": {
            "contradiction_case_ids": [
                case["case_id"]
                for case in indexes["rehearsal_contradiction_cases_by_source"].get(source_id, [])
            ],
            "source_evidence_bundle_record_id": indexes["source_evidence_bundle_record"]["bundle_record_id"],
            "staleness_case_ids": [
                case["case_id"]
                for case in indexes["rehearsal_staleness_cases_by_source"].get(source_id, [])
            ],
        },
        "source_quality_record_ids": {
            "source_contradiction_row_ids": [
                row["row_id"]
                for row in indexes["source_contradiction_rows_by_source"].get(source_id, [])
            ],
            "source_evidence_link_id": indexes["source_evidence_links"][source_id]["link_id"],
            "source_quality_ledger_row_id": indexes["source_quality_ledger_rows"][source_id]["row_id"],
            "source_quality_regression_ledger_row_id": indexes["source_quality_regression_rows"][source_id]["ledger_row_id"],
            "source_quality_report_row_id": indexes["source_quality_report_rows"][source_id]["report_row_id"],
            "source_staleness_check_id": indexes["source_staleness_checks"][source_id]["check_id"],
        },
    }


def _index_by_source_id(records: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {
        record["source_id"]: record
        for record in records
        if isinstance(record, dict) and isinstance(record.get("source_id"), str)
    }


def _operator_review_status(payload: dict[str, Any]) -> str | None:
    operator_review = payload.get("operator_review")
    if isinstance(operator_review, dict):
        status = operator_review.get("status")
        return status if isinstance(status, str) else None
    status = payload.get("operator_review_status")
    return status if isinstance(status, str) else None


def _load_local_json(reference: str) -> dict[str, Any]:
    errors = _validate_local_reference(reference)
    if errors:
        raise SourceQualityLedgerValidationError(tuple(errors))
    return _load_json(Path(_normalize_reference(reference)))


def _build_digest_reference(reference: str) -> dict[str, Any]:
    errors = _validate_local_reference(reference)
    if errors:
        raise SourceQualityLedgerValidationError(tuple(errors))
    path = Path(_normalize_reference(reference))
    content = path.read_bytes()
    return {
        "byte_count": len(content),
        "content_sha256": hashlib.sha256(content).hexdigest(),
        "local_reference": _normalize_reference(reference),
        "present": True,
    }


def _summary_counts(
    rehearsal_artifacts: list[dict[str, Any]],
    source_quality_artifacts: list[dict[str, Any]],
    link_rows: list[dict[str, Any]],
    warnings: list[str],
) -> dict[str, int]:
    local_references = {
        DOCUMENTATION_PATH,
        *(artifact["local_reference"] for artifact in rehearsal_artifacts),
        *(artifact["local_reference"] for artifact in source_quality_artifacts),
    }
    return {
        "link_fields": len(EXPECTED_LINK_FIELDS),
        "local_references": len(local_references),
        "operator_review_steps": len(OPERATOR_REVIEW_STEPS),
        "rehearsal_artifacts": len(rehearsal_artifacts),
        "rehearsal_record_links": sum(
            1
            + len(row["rehearsal_record_ids"]["staleness_case_ids"])
            + len(row["rehearsal_record_ids"]["contradiction_case_ids"])
            for row in link_rows
        ),
        "rehearsal_source_quality_links": len(link_rows),
        "required_validation_commands": len(REQUIRED_VALIDATION_COMMANDS),
        "review_checks": sum(len(row["review_checks"]) for row in link_rows),
        "source_quality_artifacts": len(source_quality_artifacts),
        "source_quality_record_links": sum(
            5 + len(row["source_quality_record_ids"]["source_contradiction_row_ids"])
            for row in link_rows
        ),
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


def _validate_reference_object(path: str, value: Any, errors: list[str]) -> str | None:
    if not isinstance(value, dict):
        errors.append(f"{path} must be an object")
        return None
    for field in ("byte_count", "content_sha256", "local_reference", "present"):
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
    local_path = Path(_normalize_reference(reference))
    try:
        content = local_path.read_bytes()
    except OSError as exc:
        errors.append(f"{path}.local_reference must be readable: {exc}")
        return _normalize_reference(reference)
    if isinstance(value.get("byte_count"), int) and value["byte_count"] != len(content):
        errors.append(f"{path}.byte_count must match local bytes")
    if isinstance(value.get("content_sha256"), str) and value["content_sha256"] != hashlib.sha256(content).hexdigest():
        errors.append(f"{path}.content_sha256 must match local bytes")
    return _normalize_reference(reference)


def _validate_artifacts(
    path: str,
    value: Any,
    specs: tuple[dict[str, Any], ...],
    errors: list[str],
) -> dict[str, dict[str, Any]] | None:
    if not isinstance(value, list) or not value:
        errors.append(f"{path} must be a non-empty list")
        return None
    expected_ids = tuple(spec["artifact_id"] for spec in specs)
    observed_ids = tuple(artifact.get("artifact_id") for artifact in value if isinstance(artifact, dict))
    if observed_ids != expected_ids:
        errors.append(f"{path} must match the fixed artifact ids")

    artifacts_by_id: dict[str, dict[str, Any]] = {}
    spec_by_id = {spec["artifact_id"]: spec for spec in specs}
    for index, artifact in enumerate(value):
        artifact_path = f"{path}[{index}]"
        if not isinstance(artifact, dict):
            errors.append(f"{artifact_path} must be an object")
            continue
        for field in (
            "artifact_id",
            "byte_count",
            "content_sha256",
            "contract_version",
            "local_reference",
            "operator_review_status",
            "present",
            "record_collection",
            "record_count",
            "record_ids",
        ):
            if field not in artifact:
                errors.append(f"{artifact_path} missing required field: {field}")
        _validate_reference_object(artifact_path, artifact, errors)
        artifact_id = artifact.get("artifact_id")
        if isinstance(artifact_id, str):
            artifacts_by_id[artifact_id] = artifact
        spec = spec_by_id.get(artifact_id)
        if spec is None:
            errors.append(f"{artifact_path}.artifact_id must be one of the fixed artifacts")
            continue
        if artifact.get("contract_version") != spec["contract_version"]:
            errors.append(f"{artifact_path}.contract_version must be {spec['contract_version']}")
        if artifact.get("local_reference") != spec["local_reference"]:
            errors.append(f"{artifact_path}.local_reference must match the fixed artifact path")
        if artifact.get("operator_review_status") != OPERATOR_REVIEW_STATUS:
            errors.append(f"{artifact_path}.operator_review_status must be {OPERATOR_REVIEW_STATUS}")
        if artifact.get("record_collection") != spec["record_collection"]:
            errors.append(f"{artifact_path}.record_collection must be {spec['record_collection']}")
        if not _is_non_empty_string_list(artifact.get("record_ids")):
            errors.append(f"{artifact_path}.record_ids must be a non-empty list of strings")
            continue
        loaded = _load_json(Path(_normalize_reference(str(spec["local_reference"]))))
        records = loaded.get(spec["record_collection"])
        if not isinstance(records, list) or not records:
            errors.append(f"{artifact_path}.local_reference must contain {spec['record_collection']}")
            continue
        expected_record_ids = [_record_identifier(record) for record in records]
        if artifact.get("record_count") != len(records):
            errors.append(f"{artifact_path}.record_count must match local artifact records")
        if artifact.get("record_ids") != expected_record_ids:
            errors.append(f"{artifact_path}.record_ids must match local artifact record ids")
    return artifacts_by_id


def _validate_link_rows(
    value: Any,
    rehearsal_artifacts: dict[str, dict[str, Any]] | None,
    source_quality_artifacts: dict[str, dict[str, Any]] | None,
    errors: list[str],
) -> dict[str, int] | None:
    if not isinstance(value, list) or not value:
        errors.append("rehearsal_source_quality_links must be a non-empty list")
        return None
    if len(value) != len(SOURCE_LINK_SPECS):
        errors.append("rehearsal_source_quality_links must match the fixed link spec count")

    inputs = load_rehearsal_source_quality_link_inputs()
    indexes = _build_source_link_indexes(inputs)
    expected_source_ids = tuple(spec["source_id"] for spec in SOURCE_LINK_SPECS)
    observed_source_ids = tuple(row.get("source_id") for row in value if isinstance(row, dict))
    if observed_source_ids != expected_source_ids:
        errors.append("rehearsal_source_quality_links must match the fixed source id order")

    seen_ids: set[str] = set()
    for index, row in enumerate(value):
        path = f"rehearsal_source_quality_links[{index}]"
        if not isinstance(row, dict):
            errors.append(f"{path} must be an object")
            continue
        _validate_link_row(path, row, rehearsal_artifacts, source_quality_artifacts, indexes, seen_ids, errors)
    return {"rehearsal_source_quality_links": len(value)}


def _validate_link_row(
    path: str,
    row: dict[str, Any],
    rehearsal_artifacts: dict[str, dict[str, Any]] | None,
    source_quality_artifacts: dict[str, dict[str, Any]] | None,
    indexes: dict[str, Any],
    seen_ids: set[str],
    errors: list[str],
) -> None:
    if tuple(row.keys()) != EXPECTED_LINK_FIELDS:
        errors.append(f"{path} fields must match the fixed rehearsal source quality link contract")
    for field in (
        "link_id",
        "link_kind",
        "link_state",
        "local_reference_policy",
        "operator_review_status",
        "source_id",
        "value_policy",
    ):
        if not isinstance(row.get(field), str) or not row.get(field):
            errors.append(f"{path}.{field} must be a non-empty string")
    link_id = row.get("link_id")
    if isinstance(link_id, str):
        if link_id in seen_ids:
            errors.append(f"{path}.link_id duplicates an earlier link")
        seen_ids.add(link_id)
    if row.get("link_state") != LINK_ROW_STATE:
        errors.append(f"{path}.link_state must be {LINK_ROW_STATE}")
    if row.get("operator_review_status") != OPERATOR_REVIEW_STATUS:
        errors.append(f"{path}.operator_review_status must be {OPERATOR_REVIEW_STATUS}")
    if row.get("local_reference_policy") != "local_static_references_only":
        errors.append(f"{path}.local_reference_policy must be local_static_references_only")
    if row.get("value_policy") != "record_identifiers_only_source_values_remain_in_local_artifacts":
        errors.append(f"{path}.value_policy must keep source values in local artifacts")

    source_id = row.get("source_id")
    if isinstance(source_id, str):
        expected_link_id = f"{LINK_SET_ID}.{source_id}.rehearsal_source_quality_link"
        if row.get("link_id") != expected_link_id:
            errors.append(f"{path}.link_id must be derived from link_set_id and source_id")
    else:
        return
    if source_id not in {spec["source_id"] for spec in SOURCE_LINK_SPECS}:
        errors.append(f"{path}.source_id must match a fixed source link spec")
        return

    _validate_review_checks(path, row.get("review_checks"), errors)
    _validate_link_artifact_ids(
        path,
        "rehearsal_artifact_ids",
        row.get("rehearsal_artifact_ids"),
        REHEARSAL_ARTIFACT_SPECS,
        rehearsal_artifacts,
        errors,
    )
    _validate_link_artifact_ids(
        path,
        "source_quality_artifact_ids",
        row.get("source_quality_artifact_ids"),
        SOURCE_QUALITY_ARTIFACT_SPECS,
        source_quality_artifacts,
        errors,
    )
    expected = _expected_ids_for_source(source_id, indexes)
    _validate_rehearsal_record_ids(path, row.get("rehearsal_record_ids"), expected["rehearsal_record_ids"], errors)
    _validate_source_quality_record_ids(
        path,
        row.get("source_quality_record_ids"),
        expected["source_quality_record_ids"],
        indexes,
        errors,
    )


def _validate_review_checks(path: str, value: Any, errors: list[str]) -> None:
    if not isinstance(value, list) or len(value) != len(REVIEW_CHECKS):
        errors.append(f"{path}.review_checks must match the fixed review checks")
        return
    expected_by_id = {check["check_id"]: check for check in REVIEW_CHECKS}
    seen: set[str] = set()
    for index, check in enumerate(value):
        check_path = f"{path}.review_checks[{index}]"
        if not isinstance(check, dict):
            errors.append(f"{check_path} must be an object")
            continue
        for field in ("check_id", "description", "operator_review_status"):
            if not isinstance(check.get(field), str) or not check.get(field):
                errors.append(f"{check_path}.{field} must be a non-empty string")
        check_id = check.get("check_id")
        if isinstance(check_id, str):
            if check_id in seen:
                errors.append(f"{check_path}.check_id duplicates an earlier check")
            seen.add(check_id)
            expected = expected_by_id.get(check_id)
            if expected is None:
                errors.append(f"{check_path}.check_id must be one of the fixed review checks")
            elif check.get("description") != expected["description"]:
                errors.append(f"{check_path}.description must match the fixed review check")
        if check.get("operator_review_status") != OPERATOR_REVIEW_STATUS:
            errors.append(f"{check_path}.operator_review_status must be {OPERATOR_REVIEW_STATUS}")


def _validate_link_artifact_ids(
    path: str,
    field: str,
    value: Any,
    specs: tuple[dict[str, Any], ...],
    artifact_rows: dict[str, dict[str, Any]] | None,
    errors: list[str],
) -> None:
    expected_ids = [spec["artifact_id"] for spec in specs]
    if value != expected_ids:
        errors.append(f"{path}.{field} must match the fixed artifact ids")
    if artifact_rows is not None and isinstance(value, list):
        missing = [artifact_id for artifact_id in value if artifact_id not in artifact_rows]
        if missing:
            errors.append(f"{path}.{field} missing artifact rows: " + ", ".join(missing))


def _validate_rehearsal_record_ids(
    path: str,
    value: Any,
    expected: dict[str, Any],
    errors: list[str],
) -> None:
    record_path = f"{path}.rehearsal_record_ids"
    if not isinstance(value, dict):
        errors.append(f"{record_path} must be an object")
        return
    if tuple(value.keys()) != EXPECTED_REHEARSAL_RECORD_ID_FIELDS:
        errors.append(f"{record_path} fields must match the fixed contract")
    if value != expected:
        errors.append(f"{record_path} must match fixed local rehearsal record ids")
    if not _is_non_empty_string_list(value.get("contradiction_case_ids")):
        errors.append(f"{record_path}.contradiction_case_ids must be a non-empty list of strings")
    if not isinstance(value.get("source_evidence_bundle_record_id"), str) or not value.get("source_evidence_bundle_record_id"):
        errors.append(f"{record_path}.source_evidence_bundle_record_id must be a non-empty string")
    if not _is_non_empty_string_list(value.get("staleness_case_ids")):
        errors.append(f"{record_path}.staleness_case_ids must be a non-empty list of strings")


def _validate_source_quality_record_ids(
    path: str,
    value: Any,
    expected: dict[str, Any],
    indexes: dict[str, Any],
    errors: list[str],
) -> None:
    record_path = f"{path}.source_quality_record_ids"
    if not isinstance(value, dict):
        errors.append(f"{record_path} must be an object")
        return
    if tuple(value.keys()) != EXPECTED_SOURCE_QUALITY_RECORD_ID_FIELDS:
        errors.append(f"{record_path} fields must match the fixed contract")
    if value != expected:
        errors.append(f"{record_path} must match fixed local source quality record ids")
    for field in (
        "source_evidence_link_id",
        "source_quality_ledger_row_id",
        "source_quality_regression_ledger_row_id",
        "source_quality_report_row_id",
        "source_staleness_check_id",
    ):
        if not isinstance(value.get(field), str) or not value.get(field):
            errors.append(f"{record_path}.{field} must be a non-empty string")
    if not _is_non_empty_string_list(value.get("source_contradiction_row_ids")):
        errors.append(f"{record_path}.source_contradiction_row_ids must be a non-empty list of strings")

    known_ids = {
        "source_evidence_link_id": {
            row["link_id"] for row in indexes["source_evidence_links"].values()
        },
        "source_quality_ledger_row_id": {
            row["row_id"] for row in indexes["source_quality_ledger_rows"].values()
        },
        "source_quality_regression_ledger_row_id": {
            row["ledger_row_id"] for row in indexes["source_quality_regression_rows"].values()
        },
        "source_quality_report_row_id": {
            row["report_row_id"] for row in indexes["source_quality_report_rows"].values()
        },
        "source_staleness_check_id": {
            row["check_id"] for row in indexes["source_staleness_checks"].values()
        },
    }
    for field, record_ids in known_ids.items():
        observed = value.get(field)
        if isinstance(observed, str) and observed not in record_ids:
            errors.append(f"{record_path}.{field} must exist in local source quality artifacts")

    contradiction_ids = {
        row["row_id"]
        for rows in indexes["source_contradiction_rows_by_source"].values()
        for row in rows
    }
    for observed in value.get("source_contradiction_row_ids", []):
        if isinstance(observed, str) and observed not in contradiction_ids:
            errors.append(f"{record_path}.source_contradiction_row_ids entry must exist in local source quality artifacts")


def _record_identifier(record: dict[str, Any]) -> str:
    for field in (
        "bundle_record_id",
        "case_id",
        "link_id",
        "check_id",
        "ledger_row_id",
        "report_row_id",
        "row_id",
        "record_id",
    ):
        value = record.get(field)
        if isinstance(value, str) and value:
            return value
    raise SourceQualityLedgerValidationError(("record does not contain a supported record identifier",))


def _build_deterministic_id(link_set: dict[str, Any]) -> str:
    digest_input = {key: value for key, value in link_set.items() if key != "build_id"}
    digest = hashlib.sha256(_canonical_json(digest_input).encode("utf-8")).hexdigest()[:BUILD_ID_DIGEST_LENGTH]
    return f"{LINK_SET_ID}-{digest}"


def _validate_build_id(link_set: dict[str, Any], errors: list[str]) -> None:
    build_id = link_set.get("build_id")
    if not isinstance(build_id, str) or not build_id:
        errors.append("build_id must be a non-empty string")
        return
    prefix = f"{LINK_SET_ID}-"
    if not build_id.startswith(prefix):
        errors.append("build_id must start with link_set_id followed by a digest")
        return
    digest = build_id[len(prefix):]
    if len(digest) != BUILD_ID_DIGEST_LENGTH or any(character not in "0123456789abcdef" for character in digest):
        errors.append(f"build_id digest must be {BUILD_ID_DIGEST_LENGTH} lowercase hex characters")
        return
    if all(field in link_set for field in ("documentation", "rehearsal_source_quality_links", "source_quality_artifacts")):
        expected = _build_deterministic_id({**link_set, "build_id": ""})
        if build_id != expected:
            errors.append("build_id must match deterministic rehearsal source quality link digest")


if __name__ == "__main__":
    raise SystemExit(main())
