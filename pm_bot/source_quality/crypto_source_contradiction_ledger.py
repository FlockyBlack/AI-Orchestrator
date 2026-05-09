from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
from typing import Any

from pm_bot.source_quality.crypto_source_evidence_link_map import (
    EXPECTED_SAFETY_BOUNDARIES,
    REQUIRED_VALIDATION_COMMANDS,
)
from pm_bot.source_quality.crypto_source_staleness_check_spec import (
    SAMPLE_OPERATOR_REPORT_PATH as SAMPLE_STALENESS_REPORT_PATH,
    SAMPLE_SPEC_PATH,
    SPEC_CONTRACT_VERSION as CRYPTO_STALENESS_SPEC_CONTRACT_VERSION,
    SPEC_ID as CRYPTO_STALENESS_SPEC_ID,
    SPEC_RUN_MODE as CRYPTO_STALENESS_SPEC_RUN_MODE,
    load_crypto_source_staleness_check_spec,
    validate_crypto_source_staleness_check_spec,
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

TASK_ID = "PMBOT-CRYPTO-LIVE-005-CRYPTO-SOURCE-CONTRADICTION-LEDGER-LOCAL-ONLY"
LEDGER_CONTRACT_VERSION = "pmbot_crypto_source_contradiction_ledger.v1"
LEDGER_ID = "pmbot-crypto-source-contradiction-ledger-001"
LEDGER_RUN_MODE = "local_static_crypto_source_contradiction_ledger"
LEDGER_CREATED_AT = "2026-05-09T01:40:00Z"
CONTRADICTION_ROW_STATE = "descriptive_crypto_source_contradiction_review"
BUILD_ID_DIGEST_LENGTH = 12

SAMPLE_LEDGER_PATH = "pm_bot/source_quality/samples/crypto_source_contradiction_ledger.fixture.json"
SAMPLE_OPERATOR_REPORT_PATH = "pm_bot/source_quality/samples/crypto_source_contradiction_ledger.fixture.md"
LEDGER_DOCUMENTATION_PATH = "docs/PMBOT_CRYPTO_LIVE_005_CRYPTO_SOURCE_CONTRADICTION_LEDGER_LOCAL_ONLY.md"

MAPPED_STATIC_FIELD_COPY_REVIEW = "mapped_static_field_copy_review"
MATCHING_STATIC_VALUES = "matching_static_values"
DIFFERENT_STATIC_VALUES_PENDING_REVIEW = "different_static_values_pending_review"
FIELD_UNAVAILABLE_PENDING_REVIEW = "field_unavailable_pending_review"
NO_STATIC_DIFFERENCE_RECORDED = "no_static_difference_recorded"
STATIC_VALUE_DIFFERENCE_PENDING_REVIEW = "static_value_difference_pending_review"
SUBJECT_KEY_DIFFERENCE_PENDING_REVIEW = "subject_key_difference_pending_review"

KNOWN_LIMITATIONS = (
    "Static local ledger only; no crypto data refresh is performed.",
    "Compares selected copied fields from local fixtures and static samples only.",
    "Records descriptive copy differences and pending review state only.",
)

OPERATOR_REVIEW_STEPS = (
    "Confirm each crypto source pair resolves to local static artifacts and expected nested records.",
    "Confirm static copy fields and source keys match or remain pending operator review when they differ.",
    "Record disputes outside this ledger before any later readiness status change.",
)

EXPECTED_REVIEW_CHECKS = (
    {
        "check_id": "source_pair_identity",
        "description": "Confirm left and right source ids, artifacts, and selected records match the fixed crypto source pair.",
    },
    {
        "check_id": "artifact_digest",
        "description": "Confirm source artifact references and digests match local bytes.",
    },
    {
        "check_id": "static_copy_consistency",
        "description": "Confirm mapped static fields are descriptive copy checks only.",
    },
    {
        "check_id": "pending_review_state",
        "description": "Confirm every row remains pending operator review.",
    },
)

SOURCE_RECORD_SELECTORS_BY_SOURCE_ID: dict[str, tuple[str | int, ...]] = {
    "read_only_crypto_data_contract_fixture": ("static_sample_records", 0),
    "crypto_market_class_capture_template": ("sample_records", 0),
    "crypto_operator_review_protocol": ("static_review_records", 0),
    "crypto_paperlive_observation_ledger": ("observation_records", 0),
    "static_crypto_reference_snapshot_2026_05_09_btc": (),
}

COMPARISON_SPECS: tuple[dict[str, Any], ...] = (
    {
        "check_id": "read_only_contract_to_reference_snapshot_static_copy",
        "check_label": "Read-only contract static sample to reference snapshot copy review",
        "left_source_id": "read_only_crypto_data_contract_fixture",
        "right_source_id": "static_crypto_reference_snapshot_2026_05_09_btc",
        "source_domain": "crypto_static_copy_lineage",
        "subject_key_mappings": (
            {"left_field": "asset_symbol", "right_field": "asset_symbol", "semantic_field": "asset_symbol"},
            {"left_field": "metric_type", "right_field": "metric_type", "semantic_field": "metric_type"},
        ),
        "field_mappings": (
            {
                "left_field": "asset_name",
                "right_field": "asset_name",
                "semantic_field": "asset_name",
                "unit_label": "static_text",
            },
            {
                "left_field": "measurement_source_label",
                "right_field": "measurement_source_label",
                "semantic_field": "measurement_source_label",
                "unit_label": "static_text",
            },
            {
                "left_field": "reported_at_utc",
                "right_field": "reported_at_utc",
                "semantic_field": "reported_at_utc",
                "unit_label": "utc_timestamp",
            },
            {
                "left_field": "reported_reference_unit",
                "right_field": "reported_reference_unit",
                "semantic_field": "reported_reference_unit",
                "unit_label": "static_text",
            },
            {
                "left_field": "source_label",
                "right_field": "source_label",
                "semantic_field": "source_label",
                "unit_label": "static_text",
            },
        ),
    },
    {
        "check_id": "market_capture_to_operator_review_static_copy",
        "check_label": "Market capture sample to operator review record copy review",
        "left_source_id": "crypto_market_class_capture_template",
        "right_source_id": "crypto_operator_review_protocol",
        "source_domain": "crypto_static_copy_lineage",
        "subject_key_mappings": (
            {
                "left_field": "record_id",
                "right_field": "source_record_id",
                "semantic_field": "source_record_id",
            },
        ),
        "field_mappings": (
            {"left_field": "market_class", "right_field": "market_class", "semantic_field": "market_class", "unit_label": "static_text"},
            {"left_field": "market_slug", "right_field": "market_slug", "semantic_field": "market_slug", "unit_label": "static_text"},
            {"left_field": "market_title", "right_field": "market_title", "semantic_field": "market_title", "unit_label": "static_text"},
            {"left_field": "asset_symbol", "right_field": "asset_symbol", "semantic_field": "asset_symbol", "unit_label": "static_text"},
            {"left_field": "asset_name", "right_field": "asset_name", "semantic_field": "asset_name", "unit_label": "static_text"},
            {"left_field": "quote_currency", "right_field": "quote_currency", "semantic_field": "quote_currency", "unit_label": "static_text"},
            {"left_field": "metric_type", "right_field": "metric_type", "semantic_field": "metric_type", "unit_label": "static_text"},
            {"left_field": "threshold_value", "right_field": "threshold_value", "semantic_field": "threshold_value", "unit_label": "usd_string"},
            {"left_field": "threshold_unit", "right_field": "threshold_unit", "semantic_field": "threshold_unit", "unit_label": "static_text"},
            {"left_field": "comparison_rule", "right_field": "comparison_rule", "semantic_field": "comparison_rule", "unit_label": "static_text"},
            {"left_field": "deadline_utc", "right_field": "deadline_utc", "semantic_field": "deadline_utc", "unit_label": "utc_timestamp"},
        ),
    },
    {
        "check_id": "operator_review_to_observation_static_copy",
        "check_label": "Operator review record to observation ledger copy review",
        "left_source_id": "crypto_operator_review_protocol",
        "right_source_id": "crypto_paperlive_observation_ledger",
        "source_domain": "crypto_static_copy_lineage",
        "subject_key_mappings": (
            {
                "left_field": "review_record_id",
                "right_field": "source_review_record_id",
                "semantic_field": "source_review_record_id",
            },
        ),
        "field_mappings": (
            {"left_field": "market_class", "right_field": "market_class", "semantic_field": "market_class", "unit_label": "static_text"},
            {"left_field": "market_slug", "right_field": "market_slug", "semantic_field": "market_slug", "unit_label": "static_text"},
            {"left_field": "market_title", "right_field": "market_title", "semantic_field": "market_title", "unit_label": "static_text"},
            {"left_field": "asset_symbol", "right_field": "asset_symbol", "semantic_field": "asset_symbol", "unit_label": "static_text"},
            {"left_field": "asset_name", "right_field": "asset_name", "semantic_field": "asset_name", "unit_label": "static_text"},
            {"left_field": "quote_currency", "right_field": "quote_currency", "semantic_field": "quote_currency", "unit_label": "static_text"},
            {"left_field": "metric_type", "right_field": "metric_type", "semantic_field": "metric_type", "unit_label": "static_text"},
            {"left_field": "threshold_value", "right_field": "threshold_value", "semantic_field": "threshold_value", "unit_label": "usd_string"},
            {"left_field": "threshold_unit", "right_field": "threshold_unit", "semantic_field": "threshold_unit", "unit_label": "static_text"},
            {"left_field": "comparison_rule", "right_field": "comparison_rule", "semantic_field": "comparison_rule", "unit_label": "static_text"},
            {"left_field": "deadline_utc", "right_field": "deadline_utc", "semantic_field": "deadline_utc", "unit_label": "utc_timestamp"},
        ),
    },
    {
        "check_id": "observation_to_reference_snapshot_static_copy",
        "check_label": "Observation ledger to reference snapshot copy review",
        "left_source_id": "crypto_paperlive_observation_ledger",
        "right_source_id": "static_crypto_reference_snapshot_2026_05_09_btc",
        "source_domain": "crypto_static_copy_lineage",
        "subject_key_mappings": (
            {"left_field": "asset_symbol", "right_field": "asset_symbol", "semantic_field": "asset_symbol"},
            {"left_field": "metric_type", "right_field": "metric_type", "semantic_field": "metric_type"},
        ),
        "field_mappings": (
            {"left_field": "asset_name", "right_field": "asset_name", "semantic_field": "asset_name", "unit_label": "static_text"},
            {
                "left_field": "measurement_source_label",
                "right_field": "measurement_source_label",
                "semantic_field": "measurement_source_label",
                "unit_label": "static_text",
            },
            {
                "left_field": "reported_at_utc",
                "right_field": "reported_at_utc",
                "semantic_field": "reported_at_utc",
                "unit_label": "utc_timestamp",
            },
            {
                "left_field": "reported_reference_unit",
                "right_field": "reported_reference_unit",
                "semantic_field": "reported_reference_unit",
                "unit_label": "static_text",
            },
            {
                "left_field": "reported_reference_value",
                "right_field": "reported_reference_value",
                "semantic_field": "reported_reference_value",
                "unit_label": "usd_string",
            },
            {
                "left_field": "observation_source_label",
                "right_field": "source_label",
                "semantic_field": "source_label",
                "unit_label": "static_text",
            },
        ),
    },
)

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


def load_crypto_source_contradiction_ledger(path: str | Path) -> dict[str, Any]:
    reference = str(path)
    errors = _validate_local_reference(reference)
    if errors:
        raise SourceQualityLedgerValidationError(tuple(errors))
    return _load_json(Path(_normalize_reference(reference)))


def build_crypto_source_contradiction_ledger(
    staleness_spec: dict[str, Any] | None = None,
) -> dict[str, Any]:
    staleness_spec = (
        staleness_spec
        if staleness_spec is not None
        else load_crypto_source_staleness_check_spec(SAMPLE_SPEC_PATH)
    )
    validation = validate_crypto_source_staleness_check_spec(staleness_spec)
    if not validation.valid:
        raise SourceQualityLedgerValidationError(validation.errors)

    spec_rows_by_source_id = _source_staleness_rows_by_source_id(staleness_spec)
    warnings: list[str] = []
    rows = [
        _build_contradiction_row(comparison_spec, spec_rows_by_source_id)
        for comparison_spec in COMPARISON_SPECS
    ]
    ledger = {
        "build_id": "",
        "contract_version": LEDGER_CONTRACT_VERSION,
        "created_at": LEDGER_CREATED_AT,
        "documentation": _build_digest_reference(LEDGER_DOCUMENTATION_PATH),
        "errors": [],
        "ledger_id": LEDGER_ID,
        "local_only": True,
        "operator_review": {
            "reviewed_at": None,
            "reviewed_by": None,
            "status": OPERATOR_REVIEW_STATUS,
        },
        "operator_review_required": True,
        "operator_review_steps": list(OPERATOR_REVIEW_STEPS),
        "required_validation_commands": list(REQUIRED_VALIDATION_COMMANDS),
        "run_mode": LEDGER_RUN_MODE,
        "safety_boundaries": dict(EXPECTED_SAFETY_BOUNDARIES),
        "source_contradiction_rows": rows,
        "source_staleness_check_report": _build_digest_reference(SAMPLE_STALENESS_REPORT_PATH),
        "source_staleness_check_spec": _build_staleness_spec_summary(staleness_spec),
        "summary_counts": _summary_counts(rows, warnings),
        "task_id": TASK_ID,
        "warnings": warnings,
    }
    ledger["build_id"] = _build_deterministic_id(ledger)
    return ledger


def validate_crypto_source_contradiction_ledger(ledger: dict[str, Any]) -> SourceQualityLedgerValidation:
    errors: list[str] = []
    if not isinstance(ledger, dict):
        return SourceQualityLedgerValidation(valid=False, errors=("ledger must be an object",))

    required_fields = (
        "build_id",
        "contract_version",
        "created_at",
        "documentation",
        "errors",
        "ledger_id",
        "local_only",
        "operator_review",
        "operator_review_required",
        "operator_review_steps",
        "required_validation_commands",
        "run_mode",
        "safety_boundaries",
        "source_contradiction_rows",
        "source_staleness_check_report",
        "source_staleness_check_spec",
        "summary_counts",
        "task_id",
        "warnings",
    )
    for field in required_fields:
        if field not in ledger:
            errors.append(f"missing required ledger field: {field}")

    if ledger.get("task_id") != TASK_ID:
        errors.append(f"task_id must be {TASK_ID}")
    if ledger.get("contract_version") != LEDGER_CONTRACT_VERSION:
        errors.append(f"contract_version must be {LEDGER_CONTRACT_VERSION}")
    if ledger.get("ledger_id") != LEDGER_ID:
        errors.append(f"ledger_id must be {LEDGER_ID}")
    if ledger.get("run_mode") != LEDGER_RUN_MODE:
        errors.append(f"run_mode must be {LEDGER_RUN_MODE}")
    if ledger.get("created_at") != LEDGER_CREATED_AT:
        errors.append(f"created_at must be {LEDGER_CREATED_AT}")
    if ledger.get("local_only") is not True:
        errors.append("local_only must be true")
    if ledger.get("operator_review_required") is not True:
        errors.append("operator_review_required must be true")
    if ledger.get("errors") != []:
        errors.append("errors must be an empty list")
    if not isinstance(ledger.get("warnings"), list) or not all(isinstance(item, str) for item in ledger.get("warnings", [])):
        errors.append("warnings must be a list of strings")
    if ledger.get("safety_boundaries") != EXPECTED_SAFETY_BOUNDARIES:
        errors.append("safety_boundaries must match the closed crypto source boundary")
    if ledger.get("required_validation_commands") != list(REQUIRED_VALIDATION_COMMANDS):
        errors.append("required_validation_commands must match the local validation contract")
    if ledger.get("operator_review_steps") != list(OPERATOR_REVIEW_STEPS):
        errors.append("operator_review_steps must match fixed crypto contradiction review steps")

    _validate_operator_review(ledger.get("operator_review"), errors)
    _validate_reference_object("documentation", ledger.get("documentation"), errors)
    _validate_reference_object("source_staleness_check_report", ledger.get("source_staleness_check_report"), errors)
    spec = _validate_staleness_spec_summary(ledger.get("source_staleness_check_spec"), errors)
    row_counts = _validate_contradiction_rows(ledger.get("source_contradiction_rows"), spec, errors)
    _validate_build_id(ledger, errors)

    forbidden_paths = _find_forbidden_output_terms(ledger)
    if forbidden_paths:
        errors.append(
            "forbidden crypto contradiction output term detected at: "
            + ", ".join(sorted(forbidden_paths))
        )

    if row_counts is not None:
        warnings = ledger.get("warnings") if isinstance(ledger.get("warnings"), list) else []
        expected_counts = dict(row_counts)
        expected_counts["operator_review_steps"] = len(OPERATOR_REVIEW_STEPS)
        expected_counts["required_validation_commands"] = len(REQUIRED_VALIDATION_COMMANDS)
        expected_counts["warnings"] = len(warnings)
        if ledger.get("summary_counts") != expected_counts:
            errors.append("summary_counts must match crypto source contradiction totals: " + _canonical_json(expected_counts))

    return SourceQualityLedgerValidation(valid=not errors, errors=tuple(errors))


def build_operator_report(ledger: dict[str, Any]) -> str:
    lines: list[str] = [
        "# PMBOT Crypto Source Contradiction Ledger",
        "",
        f"Task: `{ledger['task_id']}`",
        f"Ledger: `{ledger['ledger_id']}`",
        f"Build: `{ledger['build_id']}`",
        f"Contract: `{ledger['contract_version']}`",
        f"Run mode: `{ledger['run_mode']}`",
        f"Operator review: `{ledger['operator_review']['status']}`",
        "",
        "## Summary",
        "",
        f"- Source contradiction rows: {ledger['summary_counts']['source_contradiction_rows']}",
        f"- Source staleness checks: {ledger['summary_counts']['source_staleness_checks']}",
        f"- Source artifact references: {ledger['summary_counts']['source_artifact_references']}",
        f"- Subject key comparisons: {ledger['summary_counts']['subject_key_comparisons']}",
        f"- Subject key differences: {ledger['summary_counts']['subject_key_differences']}",
        f"- Field comparisons: {ledger['summary_counts']['field_comparisons']}",
        f"- Static value differences: {ledger['summary_counts']['different_field_comparisons']}",
        f"- Local references: {ledger['summary_counts']['local_references']}",
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
                f"- `{row['check_id']}` ({row['check_label']})",
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
    for step in ledger["operator_review_steps"]:
        lines.append(f"- {step}")

    lines.extend(
        [
            "",
            "## Safety",
            "",
            "- Local fixture/static input only.",
            "- Makes no network, LLM, market API, endpoint, wallet, order, transaction, runtime, browser, scheduler, or worker calls.",
            "- Records descriptive source copy checks and pending review state only.",
            "- Not execution approval and not runtime input.",
        ]
    )
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a local PMBOT crypto source contradiction ledger.")
    parser.add_argument(
        "--staleness-spec",
        default=SAMPLE_SPEC_PATH,
        help="Local crypto source staleness spec JSON.",
    )
    parser.add_argument("--output-ledger", required=True, help="Output crypto source contradiction ledger JSON path.")
    parser.add_argument("--output-report", required=True, help="Output operator report Markdown path.")
    args = parser.parse_args(argv)

    staleness_spec = load_crypto_source_staleness_check_spec(args.staleness_spec)
    ledger = build_crypto_source_contradiction_ledger(staleness_spec)
    validation = validate_crypto_source_contradiction_ledger(ledger)
    if not validation.valid:
        raise SourceQualityLedgerValidationError(validation.errors)

    _write_json(Path(args.output_ledger), ledger)
    Path(args.output_report).write_text(build_operator_report(ledger), encoding="utf-8")
    return 0


def _build_contradiction_row(
    comparison_spec: dict[str, Any],
    spec_rows_by_source_id: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    left_row = spec_rows_by_source_id[comparison_spec["left_source_id"]]
    right_row = spec_rows_by_source_id[comparison_spec["right_source_id"]]
    left_record = _load_selected_source_record(left_row)
    right_record = _load_selected_source_record(right_row)

    subject_key_comparisons = [
        _build_value_comparison(mapping, left_record, right_record)
        for mapping in comparison_spec["subject_key_mappings"]
    ]
    field_comparisons = [
        _build_field_comparison(mapping, left_record, right_record)
        for mapping in comparison_spec["field_mappings"]
    ]
    return {
        "check_id": comparison_spec["check_id"],
        "check_label": comparison_spec["check_label"],
        "comparison_kind": MAPPED_STATIC_FIELD_COPY_REVIEW,
        "contradiction_state": _contradiction_state(subject_key_comparisons, field_comparisons),
        "field_comparisons": field_comparisons,
        "known_limitations": list(KNOWN_LIMITATIONS),
        "left_source": _build_source_summary(left_row),
        "operator_review_status": OPERATOR_REVIEW_STATUS,
        "review_checks": [
            {
                "check_id": review_check["check_id"],
                "description": review_check["description"],
                "operator_review_status": OPERATOR_REVIEW_STATUS,
            }
            for review_check in EXPECTED_REVIEW_CHECKS
        ],
        "right_source": _build_source_summary(right_row),
        "row_id": f"{LEDGER_ID}.{comparison_spec['check_id']}.crypto_source_contradiction_review",
        "row_state": CONTRADICTION_ROW_STATE,
        "source_domain": comparison_spec["source_domain"],
        "subject_key_comparisons": subject_key_comparisons,
    }


def _build_value_comparison(
    mapping: dict[str, Any],
    left_record: dict[str, Any],
    right_record: dict[str, Any],
) -> dict[str, Any]:
    left_present = mapping["left_field"] in left_record
    right_present = mapping["right_field"] in right_record
    left_value = left_record.get(mapping["left_field"])
    right_value = right_record.get(mapping["right_field"])
    return {
        "left_field": mapping["left_field"],
        "left_field_present": left_present,
        "left_value": left_value,
        "operator_review_status": OPERATOR_REVIEW_STATUS,
        "right_field": mapping["right_field"],
        "right_field_present": right_present,
        "right_value": right_value,
        "semantic_field": mapping["semantic_field"],
        "values_match": left_present and right_present and left_value == right_value,
    }


def _build_field_comparison(
    mapping: dict[str, Any],
    left_record: dict[str, Any],
    right_record: dict[str, Any],
) -> dict[str, Any]:
    comparison = _build_value_comparison(mapping, left_record, right_record)
    comparison["comparison_state"] = _field_comparison_state(comparison)
    comparison["unit_label"] = mapping["unit_label"]
    return comparison


def _field_comparison_state(comparison: dict[str, Any]) -> str:
    if comparison["left_field_present"] is not True or comparison["right_field_present"] is not True:
        return FIELD_UNAVAILABLE_PENDING_REVIEW
    if comparison["values_match"] is True:
        return MATCHING_STATIC_VALUES
    return DIFFERENT_STATIC_VALUES_PENDING_REVIEW


def _contradiction_state(
    subject_key_comparisons: list[dict[str, Any]],
    field_comparisons: list[dict[str, Any]],
) -> str:
    if any(comparison["values_match"] is not True for comparison in subject_key_comparisons):
        return SUBJECT_KEY_DIFFERENCE_PENDING_REVIEW
    if any(comparison["comparison_state"] == FIELD_UNAVAILABLE_PENDING_REVIEW for comparison in field_comparisons):
        return FIELD_UNAVAILABLE_PENDING_REVIEW
    if any(comparison["values_match"] is not True for comparison in field_comparisons):
        return STATIC_VALUE_DIFFERENCE_PENDING_REVIEW
    return NO_STATIC_DIFFERENCE_RECORDED


def _build_source_summary(staleness_row: dict[str, Any]) -> dict[str, Any]:
    source_id = staleness_row["source_id"]
    return {
        "operator_review_status": staleness_row["operator_review_status"],
        "source_artifact": dict(staleness_row["source_artifact"]),
        "source_domain": staleness_row["source_domain"],
        "source_evidence_link_id": staleness_row["source_evidence_link_id"],
        "source_id": source_id,
        "source_label": staleness_row["source_label"],
        "source_record_id": staleness_row["source_record_id"],
        "source_record_selector": _selector_label(SOURCE_RECORD_SELECTORS_BY_SOURCE_ID[source_id]),
        "source_record_status": staleness_row["source_record_status"],
        "source_type": staleness_row["source_type"],
        "staleness_check_id": staleness_row["check_id"],
        "staleness_state": staleness_row["staleness_state"],
        "timestamp_field_path": staleness_row["timestamp_field_path"],
    }


def _build_staleness_spec_summary(spec: dict[str, Any]) -> dict[str, Any]:
    return {
        **_build_digest_reference(SAMPLE_SPEC_PATH),
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


def _load_selected_source_record(staleness_row: dict[str, Any]) -> dict[str, Any]:
    source_id = staleness_row["source_id"]
    selector = SOURCE_RECORD_SELECTORS_BY_SOURCE_ID[source_id]
    artifact_reference = _normalize_reference(staleness_row["source_artifact"]["local_reference"])
    artifact = _load_json(Path(artifact_reference))
    selected = _select_static_record(artifact, selector)
    if not isinstance(selected, dict):
        raise SourceQualityLedgerValidationError((f"{source_id} selected source record must be an object",))
    return selected


def _select_static_record(value: Any, selector: tuple[str | int, ...]) -> Any:
    selected = value
    for part in selector:
        if isinstance(part, str):
            if not isinstance(selected, dict):
                return None
            selected = selected.get(part)
        else:
            if not isinstance(selected, list) or part >= len(selected):
                return None
            selected = selected[part]
    return selected


def _selector_label(selector: tuple[str | int, ...]) -> str:
    label = "$"
    for part in selector:
        label += f".{part}" if isinstance(part, str) else f"[{part}]"
    return label


def _summary_counts(rows: list[dict[str, Any]], warnings: list[str]) -> dict[str, int]:
    local_references = {
        LEDGER_DOCUMENTATION_PATH,
        SAMPLE_SPEC_PATH,
        SAMPLE_STALENESS_REPORT_PATH,
    }
    source_artifact_references: set[str] = set()
    staleness_check_ids: set[str] = set()
    for row in rows:
        for side in ("left_source", "right_source"):
            source = row[side]
            source_artifact_references.add(source["source_artifact"]["local_reference"])
            staleness_check_ids.add(source["staleness_check_id"])
            local_references.add(source["source_artifact"]["local_reference"])

    return {
        "different_field_comparisons": sum(
            1
            for row in rows
            for comparison in row["field_comparisons"]
            if comparison["comparison_state"] == DIFFERENT_STATIC_VALUES_PENDING_REVIEW
        ),
        "field_comparisons": sum(len(row["field_comparisons"]) for row in rows),
        "local_references": len(local_references),
        "matching_field_comparisons": sum(
            1
            for row in rows
            for comparison in row["field_comparisons"]
            if comparison["comparison_state"] == MATCHING_STATIC_VALUES
        ),
        "review_checks": sum(len(row["review_checks"]) for row in rows),
        "source_artifact_references": len(source_artifact_references),
        "source_contradiction_rows": len(rows),
        "source_record_pairs": len(rows),
        "source_staleness_checks": len(staleness_check_ids),
        "subject_key_comparisons": sum(len(row["subject_key_comparisons"]) for row in rows),
        "subject_key_differences": sum(
            1
            for row in rows
            for comparison in row["subject_key_comparisons"]
            if comparison["values_match"] is not True
        ),
        "operator_review_steps": len(OPERATOR_REVIEW_STEPS),
        "required_validation_commands": len(REQUIRED_VALIDATION_COMMANDS),
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
    if value.get("contract_version") != CRYPTO_STALENESS_SPEC_CONTRACT_VERSION:
        errors.append(f"{path}.contract_version must be {CRYPTO_STALENESS_SPEC_CONTRACT_VERSION}")
    if value.get("spec_id") != CRYPTO_STALENESS_SPEC_ID:
        errors.append(f"{path}.spec_id must be {CRYPTO_STALENESS_SPEC_ID}")
    if value.get("run_mode") != CRYPTO_STALENESS_SPEC_RUN_MODE:
        errors.append(f"{path}.run_mode must be {CRYPTO_STALENESS_SPEC_RUN_MODE}")
    if value.get("operator_review_status") != OPERATOR_REVIEW_STATUS:
        errors.append(f"{path}.operator_review_status must be {OPERATOR_REVIEW_STATUS}")
    if not isinstance(value.get("source_staleness_checks"), int) or isinstance(value.get("source_staleness_checks"), bool):
        errors.append(f"{path}.source_staleness_checks must be an integer")

    spec: dict[str, Any] | None = None
    reference = _validate_reference_object(path, value, errors)
    if reference is not None:
        try:
            spec = load_crypto_source_staleness_check_spec(reference)
        except (OSError, SourceQualityLedgerValidationError) as exc:
            errors.append(f"{path}.local_reference must load crypto source staleness spec: {exc}")
        else:
            validation = validate_crypto_source_staleness_check_spec(spec)
            if not validation.valid:
                errors.extend(f"{path}.{error}" for error in validation.errors)
            for field in ("build_id", "contract_version", "run_mode", "spec_id"):
                if value.get(field) != spec.get(field):
                    errors.append(f"{path}.{field} must match crypto source staleness spec")
            if value.get("source_staleness_checks") != len(spec.get("source_staleness_checks", [])):
                errors.append(f"{path}.source_staleness_checks must match crypto source staleness spec")
    return spec


def _validate_contradiction_rows(
    rows: Any,
    spec: dict[str, Any] | None,
    errors: list[str],
) -> dict[str, int] | None:
    if not isinstance(rows, list) or not rows:
        errors.append("source_contradiction_rows must be a non-empty list")
        return None
    if len(rows) != len(COMPARISON_SPECS):
        errors.append("source_contradiction_rows must contain one row per fixed crypto source pair")

    spec_rows_by_source_id = _source_staleness_rows_by_source_id(spec)
    seen_row_ids: set[str] = set()
    seen_check_ids: set[str] = set()
    row_objects: list[dict[str, Any]] = []
    expected_check_ids = tuple(comparison_spec["check_id"] for comparison_spec in COMPARISON_SPECS)
    observed_check_ids = tuple(row.get("check_id") for row in rows if isinstance(row, dict))
    if observed_check_ids != expected_check_ids:
        errors.append("source_contradiction_rows check_id order must match fixed crypto source pairs")

    for index, row in enumerate(rows):
        path = f"source_contradiction_rows[{index}]"
        if not isinstance(row, dict):
            errors.append(f"{path} must be an object")
            continue
        _validate_contradiction_row(
            path,
            row,
            spec_rows_by_source_id,
            seen_row_ids,
            seen_check_ids,
            errors,
        )
        row_objects.append(row)
    if not row_objects:
        return None
    warnings: list[str] = []
    return _summary_counts(row_objects, warnings)


def _validate_contradiction_row(
    path: str,
    row: dict[str, Any],
    spec_rows_by_source_id: dict[str, dict[str, Any]],
    seen_row_ids: set[str],
    seen_check_ids: set[str],
    errors: list[str],
) -> None:
    required_fields = (
        "check_id",
        "check_label",
        "comparison_kind",
        "contradiction_state",
        "field_comparisons",
        "known_limitations",
        "left_source",
        "operator_review_status",
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

    check_id = row.get("check_id")
    row_id = row.get("row_id")
    if isinstance(check_id, str):
        if check_id in seen_check_ids:
            errors.append(f"{path}.check_id duplicates an earlier row")
        seen_check_ids.add(check_id)
    if isinstance(row_id, str):
        if row_id in seen_row_ids:
            errors.append(f"{path}.row_id duplicates an earlier row")
        seen_row_ids.add(row_id)

    comparison_spec = _comparison_specs_by_check_id().get(check_id) if isinstance(check_id, str) else None
    if comparison_spec is None:
        errors.append(f"{path}.check_id must be one of the fixed crypto source pairs")
        return

    if row.get("row_id") != f"{LEDGER_ID}.{comparison_spec['check_id']}.crypto_source_contradiction_review":
        errors.append(f"{path}.row_id must be derived from ledger_id and check_id")
    if row.get("check_label") != comparison_spec["check_label"]:
        errors.append(f"{path}.check_label must match fixed crypto source pair")
    if row.get("comparison_kind") != MAPPED_STATIC_FIELD_COPY_REVIEW:
        errors.append(f"{path}.comparison_kind must be {MAPPED_STATIC_FIELD_COPY_REVIEW}")
    if row.get("row_state") != CONTRADICTION_ROW_STATE:
        errors.append(f"{path}.row_state must be {CONTRADICTION_ROW_STATE}")
    if row.get("source_domain") != comparison_spec["source_domain"]:
        errors.append(f"{path}.source_domain must match fixed crypto source pair")
    if row.get("operator_review_status") != OPERATOR_REVIEW_STATUS:
        errors.append(f"{path}.operator_review_status must be {OPERATOR_REVIEW_STATUS}")
    if row.get("known_limitations") != list(KNOWN_LIMITATIONS):
        errors.append(f"{path}.known_limitations must match fixed crypto contradiction limitations")

    left_row = spec_rows_by_source_id.get(comparison_spec["left_source_id"])
    right_row = spec_rows_by_source_id.get(comparison_spec["right_source_id"])
    left_record = _validate_source_summary(f"{path}.left_source", row.get("left_source"), left_row, errors)
    right_record = _validate_source_summary(f"{path}.right_source", row.get("right_source"), right_row, errors)

    _validate_review_checks(path, row.get("review_checks"), errors)
    if left_record is None or right_record is None:
        return
    _validate_value_comparisons(
        f"{path}.subject_key_comparisons",
        row.get("subject_key_comparisons"),
        comparison_spec["subject_key_mappings"],
        left_record,
        right_record,
        errors,
        include_state=False,
    )
    _validate_value_comparisons(
        f"{path}.field_comparisons",
        row.get("field_comparisons"),
        comparison_spec["field_mappings"],
        left_record,
        right_record,
        errors,
        include_state=True,
    )

    if isinstance(row.get("subject_key_comparisons"), list) and isinstance(row.get("field_comparisons"), list):
        expected_state = _contradiction_state(row["subject_key_comparisons"], row["field_comparisons"])
        if row.get("contradiction_state") != expected_state:
            errors.append(f"{path}.contradiction_state must be {expected_state}")


def _validate_source_summary(
    path: str,
    value: Any,
    staleness_row: dict[str, Any] | None,
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
        "source_record_id",
        "source_record_selector",
        "source_record_status",
        "source_type",
        "staleness_check_id",
        "staleness_state",
        "timestamp_field_path",
    )
    for field in required_fields:
        if field not in value:
            errors.append(f"{path} missing required field: {field}")
    source_id = value.get("source_id")
    if not isinstance(source_id, str) or not source_id:
        errors.append(f"{path}.source_id must be a non-empty string")
        return None
    if source_id not in SOURCE_RECORD_SELECTORS_BY_SOURCE_ID:
        errors.append(f"{path}.source_id must be one of the fixed crypto contradiction source ids")
        return None
    if staleness_row is None:
        errors.append(f"{path}.source_id must exist in crypto source staleness spec")
        return None
    expected_summary = _build_source_summary(staleness_row)
    for field, expected_value in expected_summary.items():
        if field == "source_artifact":
            continue
        if value.get(field) != expected_value:
            errors.append(f"{path}.{field} must match crypto source staleness row")
    _validate_source_artifact(f"{path}.source_artifact", value.get("source_artifact"), staleness_row, errors)
    try:
        return _load_selected_source_record(staleness_row)
    except SourceQualityLedgerValidationError as exc:
        errors.extend(f"{path}.{error}" for error in exc.errors)
        return None


def _validate_source_artifact(
    path: str,
    value: Any,
    staleness_row: dict[str, Any],
    errors: list[str],
) -> str | None:
    reference = _validate_reference_object(path, value, errors)
    if not isinstance(value, dict):
        return reference
    if value != staleness_row.get("source_artifact"):
        errors.append(f"{path} must match crypto source staleness row")
    return reference


def _validate_value_comparisons(
    path: str,
    comparisons: Any,
    expected_mappings: tuple[dict[str, Any], ...],
    left_record: dict[str, Any],
    right_record: dict[str, Any],
    errors: list[str],
    *,
    include_state: bool,
) -> None:
    if not isinstance(comparisons, list) or not comparisons:
        errors.append(f"{path} must be a non-empty list")
        return
    if len(comparisons) != len(expected_mappings):
        errors.append(f"{path} must match fixed crypto source field mappings")
    for index, comparison in enumerate(comparisons):
        item_path = f"{path}[{index}]"
        if not isinstance(comparison, dict):
            errors.append(f"{item_path} must be an object")
            continue
        if index >= len(expected_mappings):
            continue
        expected = expected_mappings[index]
        required_fields = (
            "left_field",
            "left_field_present",
            "left_value",
            "operator_review_status",
            "right_field",
            "right_field_present",
            "right_value",
            "semantic_field",
            "values_match",
        )
        if include_state:
            required_fields = (*required_fields, "comparison_state", "unit_label")
        for field in required_fields:
            if field not in comparison:
                errors.append(f"{item_path} missing required field: {field}")
        for field in ("left_field", "right_field", "semantic_field"):
            if comparison.get(field) != expected[field]:
                errors.append(f"{item_path}.{field} must match fixed crypto source mapping")
        if include_state and comparison.get("unit_label") != expected["unit_label"]:
            errors.append(f"{item_path}.unit_label must match fixed crypto source mapping")
        if comparison.get("operator_review_status") != OPERATOR_REVIEW_STATUS:
            errors.append(f"{item_path}.operator_review_status must be {OPERATOR_REVIEW_STATUS}")

        left_present = expected["left_field"] in left_record
        right_present = expected["right_field"] in right_record
        left_value = left_record.get(expected["left_field"])
        right_value = right_record.get(expected["right_field"])
        values_match = left_present and right_present and left_value == right_value
        if comparison.get("left_field_present") is not left_present:
            errors.append(f"{item_path}.left_field_present must match left source record")
        if comparison.get("right_field_present") is not right_present:
            errors.append(f"{item_path}.right_field_present must match right source record")
        if comparison.get("left_value") != left_value:
            errors.append(f"{item_path}.left_value must match left source record")
        if comparison.get("right_value") != right_value:
            errors.append(f"{item_path}.right_value must match right source record")
        if comparison.get("values_match") is not values_match:
            errors.append(f"{item_path}.values_match must match static source values")
        if include_state:
            expected_state = _field_comparison_state(
                {
                    "left_field_present": left_present,
                    "right_field_present": right_present,
                    "values_match": values_match,
                }
            )
            if comparison.get("comparison_state") != expected_state:
                errors.append(f"{item_path}.comparison_state must be {expected_state}")


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
        errors.append(f"{row_path}.review_checks must match fixed crypto contradiction review checks")
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
                errors.append(f"{path}.check_id must be one of the fixed crypto contradiction review checks")
            elif check.get("description") != expected["description"]:
                errors.append(f"{path}.description must match fixed crypto contradiction review check")
        if check.get("operator_review_status") != OPERATOR_REVIEW_STATUS:
            errors.append(f"{path}.operator_review_status must be {OPERATOR_REVIEW_STATUS}")
    return len(review_checks)


def _comparison_specs_by_check_id() -> dict[str, dict[str, Any]]:
    return {
        comparison_spec["check_id"]: comparison_spec
        for comparison_spec in COMPARISON_SPECS
    }


def _build_deterministic_id(ledger: dict[str, Any]) -> str:
    digest_input = {key: value for key, value in ledger.items() if key != "build_id"}
    digest = hashlib.sha256(_canonical_json(digest_input).encode("utf-8")).hexdigest()[:BUILD_ID_DIGEST_LENGTH]
    return f"{LEDGER_ID}-{digest}"


def _validate_build_id(ledger: dict[str, Any], errors: list[str]) -> None:
    build_id = ledger.get("build_id")
    if not isinstance(build_id, str) or not build_id:
        errors.append("build_id must be a non-empty string")
        return
    prefix = f"{LEDGER_ID}-"
    if not build_id.startswith(prefix):
        errors.append("build_id must start with ledger_id followed by a digest")
        return
    digest = build_id[len(prefix):]
    if len(digest) != BUILD_ID_DIGEST_LENGTH or any(character not in "0123456789abcdef" for character in digest):
        errors.append(f"build_id digest must be {BUILD_ID_DIGEST_LENGTH} lowercase hex characters")
        return
    expected = _build_deterministic_id({**ledger, "build_id": ""})
    if build_id != expected:
        errors.append("build_id must match deterministic crypto source contradiction digest")


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
