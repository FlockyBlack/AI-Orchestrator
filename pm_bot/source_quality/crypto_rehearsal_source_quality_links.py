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

TASK_ID = "PMBOT-CRYPTO-LIVE-019-CRYPTO-REHEARSAL-TO-SOURCE-QUALITY-LINKS-LOCAL-ONLY"
LINKS_CONTRACT_VERSION = "pmbot_crypto_rehearsal_source_quality_links.v1"
LINK_SET_ID = "pmbot-crypto-rehearsal-source-quality-links-001"
LINKS_RUN_MODE = "local_static_crypto_rehearsal_source_quality_links"
LINKS_CREATED_AT = "2026-05-09T07:30:00Z"
LINK_ROW_STATE = "descriptive_rehearsal_source_quality_link"
BUILD_ID_DIGEST_LENGTH = 12

SAMPLE_LINKS_PATH = "pm_bot/source_quality/samples/crypto_rehearsal_source_quality_links.fixture.json"
SAMPLE_OPERATOR_REPORT_PATH = "pm_bot/source_quality/samples/crypto_rehearsal_source_quality_links.fixture.md"

DOCUMENTATION_PATH = "docs/PMBOT_CRYPTO_LIVE_019_CRYPTO_REHEARSAL_TO_SOURCE_QUALITY_LINKS_LOCAL_ONLY.md"
REHEARSAL_PACKET_DOCUMENTATION_PATH = (
    "docs/PMBOT_CRYPTO_LIVE_006_CRYPTO_PAPERLIVE_REHEARSAL_PACKET_LOCAL_ONLY.md"
)
REHEARSAL_PACKET_FIXTURE_PATH = (
    "pm_bot/tests/fixtures/crypto_live/pmbot_crypto_paperlive_rehearsal_packet.valid.json"
)
SOURCE_QUALITY_CAPTURE_SURFACE_PATH = (
    "pm_bot/source_quality/samples/crypto_source_quality_capture_surface.fixture.json"
)
SOURCE_EVIDENCE_LINK_MAP_PATH = "pm_bot/source_quality/samples/crypto_source_evidence_link_map.fixture.json"
SOURCE_STALENESS_CHECK_SPEC_PATH = "pm_bot/source_quality/samples/crypto_source_staleness_check_spec.fixture.json"
SOURCE_CONTRADICTION_LEDGER_PATH = "pm_bot/source_quality/samples/crypto_source_contradiction_ledger.fixture.json"

REQUIRED_VALIDATION_COMMANDS = (
    "python -m compileall pm_bot tests",
    "pytest pm_bot/tests tests/test_codex_queue_pmbot_templates.py",
)

OPERATOR_REVIEW_STEPS = (
    "Confirm the rehearsal packet record resolves to the listed source quality records.",
    "Confirm every source quality record remains local, static, and pending operator review.",
    "Confirm source value fields remain in referenced artifacts and are not copied into this link set.",
)

EXPECTED_SAFETY_BOUNDARIES = {
    "authenticated_endpoint_calls_allowed": False,
    "background_process_allowed": False,
    "browser_automation_allowed": False,
    "credential_or_secret_access_allowed": False,
    "crypto_data_refresh_allowed": False,
    "execution_endpoint_calls_allowed": False,
    "external_service_calls_allowed": False,
    "llm_provider_calls_allowed": False,
    "local_static_samples_only": True,
    "market_api_calls_allowed": False,
    "market_ranking_allowed": False,
    "network_calls_allowed": False,
    "numeric_prediction_metric_allowed": False,
    "operator_review_required": True,
    "order_or_trade_surface_changes_allowed": False,
    "paper_mode_only": True,
    "paperlive_execution_allowed": False,
    "runtime_or_dispatcher_changes_allowed": False,
    "scheduler_or_worker_allowed": False,
    "threshold_comparison_output_allowed": False,
    "trade_instruction_allowed": False,
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
    "packet_record_id",
    "rehearsal_packet_reference",
    "rehearsal_source_field",
    "rehearsal_source_record_id",
    "review_checks",
    "source_id",
    "source_quality_artifact_ids",
    "source_quality_record_ids",
    "value_policy",
)

REVIEW_CHECKS = (
    {
        "check_id": "rehearsal_record_identity",
        "description": "Confirm the rehearsal record and source field match the static packet.",
    },
    {
        "check_id": "source_quality_record_presence",
        "description": "Confirm each linked source quality record exists in the named local artifact.",
    },
    {
        "check_id": "local_reference_digest",
        "description": "Confirm linked local artifact byte counts and digests match current local bytes.",
    },
    {
        "check_id": "pending_review_state",
        "description": "Confirm the rehearsal link and source quality records remain pending operator review.",
    },
)

SOURCE_QUALITY_ARTIFACT_SPECS: tuple[dict[str, Any], ...] = (
    {
        "artifact_id": "crypto_source_quality_capture_surface_sample",
        "contract_version": "pmbot_crypto_source_quality_capture_surface.v1",
        "input_key": "capture_surface",
        "local_reference": SOURCE_QUALITY_CAPTURE_SURFACE_PATH,
        "record_collection": "quality_capture_records",
    },
    {
        "artifact_id": "crypto_source_evidence_link_map_sample",
        "contract_version": "pmbot_crypto_source_evidence_link_map.v1",
        "input_key": "evidence_link_map",
        "local_reference": SOURCE_EVIDENCE_LINK_MAP_PATH,
        "record_collection": "source_evidence_links",
    },
    {
        "artifact_id": "crypto_source_staleness_check_spec_sample",
        "contract_version": "pmbot_crypto_source_staleness_check_spec.v1",
        "input_key": "staleness_check_spec",
        "local_reference": SOURCE_STALENESS_CHECK_SPEC_PATH,
        "record_collection": "source_staleness_checks",
    },
    {
        "artifact_id": "crypto_source_contradiction_ledger_sample",
        "contract_version": "pmbot_crypto_source_contradiction_ledger.v1",
        "input_key": "contradiction_ledger",
        "local_reference": SOURCE_CONTRADICTION_LEDGER_PATH,
        "record_collection": "source_contradiction_rows",
    },
)

REHEARSAL_SOURCE_LINK_SPECS: tuple[dict[str, Any], ...] = (
    {
        "capture_record_id": "crypto_source_quality_capture_surface_001.crypto_market_class_capture_template_001.quality_capture",
        "contradiction_row_ids": (
            "pmbot-crypto-source-contradiction-ledger-001.market_capture_to_operator_review_static_copy.crypto_source_contradiction_review",
        ),
        "evidence_link_id": "pmbot-crypto-source-evidence-link-map-001.crypto_market_class_capture_template.crypto_source_evidence_link",
        "link_subject": "market_capture",
        "rehearsal_source_field": "source_capture_record_id",
        "source_id": "crypto_market_class_capture_template",
        "staleness_check_id": "pmbot-crypto-source-staleness-check-spec-001.crypto_market_class_capture_template.crypto_source_staleness_check",
    },
    {
        "capture_record_id": "crypto_source_quality_capture_surface_001.crypto_operator_review_protocol_001.quality_capture",
        "contradiction_row_ids": (
            "pmbot-crypto-source-contradiction-ledger-001.market_capture_to_operator_review_static_copy.crypto_source_contradiction_review",
            "pmbot-crypto-source-contradiction-ledger-001.operator_review_to_observation_static_copy.crypto_source_contradiction_review",
        ),
        "evidence_link_id": "pmbot-crypto-source-evidence-link-map-001.crypto_operator_review_protocol.crypto_source_evidence_link",
        "link_subject": "operator_review_protocol",
        "rehearsal_source_field": "source_review_record_id",
        "source_id": "crypto_operator_review_protocol",
        "staleness_check_id": "pmbot-crypto-source-staleness-check-spec-001.crypto_operator_review_protocol.crypto_source_staleness_check",
    },
    {
        "capture_record_id": "crypto_source_quality_capture_surface_001.crypto_paperlive_observation_ledger_001.quality_capture",
        "contradiction_row_ids": (
            "pmbot-crypto-source-contradiction-ledger-001.operator_review_to_observation_static_copy.crypto_source_contradiction_review",
            "pmbot-crypto-source-contradiction-ledger-001.observation_to_reference_snapshot_static_copy.crypto_source_contradiction_review",
        ),
        "evidence_link_id": "pmbot-crypto-source-evidence-link-map-001.crypto_paperlive_observation_ledger.crypto_source_evidence_link",
        "link_subject": "paperlive_observation_ledger",
        "rehearsal_source_field": "observation_record_id",
        "source_id": "crypto_paperlive_observation_ledger",
        "staleness_check_id": "pmbot-crypto-source-staleness-check-spec-001.crypto_paperlive_observation_ledger.crypto_source_staleness_check",
    },
    {
        "capture_record_id": "crypto_source_quality_capture_surface_001.static_crypto_reference_snapshot_2026_05_09_btc.quality_capture",
        "contradiction_row_ids": (
            "pmbot-crypto-source-contradiction-ledger-001.read_only_contract_to_reference_snapshot_static_copy.crypto_source_contradiction_review",
            "pmbot-crypto-source-contradiction-ledger-001.observation_to_reference_snapshot_static_copy.crypto_source_contradiction_review",
        ),
        "evidence_link_id": (
            "pmbot-crypto-source-evidence-link-map-001."
            "static_crypto_reference_snapshot_2026_05_09_btc.crypto_source_evidence_link"
        ),
        "link_subject": "static_reference_snapshot",
        "rehearsal_source_field": "local_snapshot_reference",
        "source_artifact_id": "static_crypto_reference_snapshot_2026_05_09_btc",
        "source_id": "static_crypto_reference_snapshot_2026_05_09_btc",
        "staleness_check_id": (
            "pmbot-crypto-source-staleness-check-spec-001."
            "static_crypto_reference_snapshot_2026_05_09_btc.crypto_source_staleness_check"
        ),
    },
)


def load_crypto_rehearsal_source_quality_links(path: str | Path) -> dict[str, Any]:
    reference = str(path)
    errors = _validate_local_reference(reference)
    if errors:
        raise SourceQualityLedgerValidationError(tuple(errors))
    return _load_json(Path(_normalize_reference(reference)))


def load_crypto_rehearsal_link_inputs() -> dict[str, dict[str, Any]]:
    inputs: dict[str, dict[str, Any]] = {
        "rehearsal_packet": _load_local_json(REHEARSAL_PACKET_FIXTURE_PATH),
    }
    for spec in SOURCE_QUALITY_ARTIFACT_SPECS:
        inputs[str(spec["input_key"])] = _load_local_json(str(spec["local_reference"]))
    return inputs


def build_crypto_rehearsal_source_quality_links(
    inputs: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    inputs = inputs if inputs is not None else load_crypto_rehearsal_link_inputs()
    validation_errors = _validate_input_payloads(inputs)
    if validation_errors:
        raise SourceQualityLedgerValidationError(tuple(validation_errors))

    packet = inputs["rehearsal_packet"]
    rehearsal_record = packet["paperlive_rehearsal_records"][0]
    source_quality_artifacts = [
        _build_source_quality_artifact(spec, inputs[str(spec["input_key"])])
        for spec in SOURCE_QUALITY_ARTIFACT_SPECS
    ]
    source_quality_record_indexes = _source_quality_record_indexes(inputs)
    link_rows = [
        _build_link_row(packet, rehearsal_record, spec, source_quality_record_indexes)
        for spec in REHEARSAL_SOURCE_LINK_SPECS
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
        "rehearsal_packet": _build_rehearsal_packet_reference(packet),
        "rehearsal_packet_documentation": _build_digest_reference(REHEARSAL_PACKET_DOCUMENTATION_PATH),
        "rehearsal_source_quality_links": link_rows,
        "required_validation_commands": list(REQUIRED_VALIDATION_COMMANDS),
        "run_mode": LINKS_RUN_MODE,
        "safety_boundaries": dict(EXPECTED_SAFETY_BOUNDARIES),
        "source_quality_artifacts": source_quality_artifacts,
        "summary_counts": _summary_counts(source_quality_artifacts, link_rows, warnings),
        "task_id": TASK_ID,
        "warnings": warnings,
    }
    link_set["build_id"] = _build_deterministic_id(link_set)
    return link_set


def validate_crypto_rehearsal_source_quality_links(link_set: dict[str, Any]) -> SourceQualityLedgerValidation:
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
        "rehearsal_packet",
        "rehearsal_packet_documentation",
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
    packet = _validate_rehearsal_packet_reference(link_set.get("rehearsal_packet"), errors)
    _validate_reference_object("rehearsal_packet_documentation", link_set.get("rehearsal_packet_documentation"), errors)
    artifacts = _validate_source_quality_artifacts(link_set.get("source_quality_artifacts"), errors)
    link_counts = _validate_link_rows(link_set.get("rehearsal_source_quality_links"), packet, artifacts, errors)
    _validate_build_id(link_set, errors)

    forbidden_paths = _find_forbidden_decision_terms(link_set)
    if forbidden_paths:
        errors.append(
            "forbidden decision/action term detected in rehearsal source quality links at: "
            + ", ".join(sorted(forbidden_paths))
        )

    if artifacts is not None and link_counts is not None:
        warnings = link_set.get("warnings") if isinstance(link_set.get("warnings"), list) else []
        expected_counts = _summary_counts(list(artifacts.values()), link_set["rehearsal_source_quality_links"], warnings)
        if link_set.get("summary_counts") != expected_counts:
            errors.append("summary_counts must match rehearsal source quality link totals: " + _canonical_json(expected_counts))

    return SourceQualityLedgerValidation(valid=not errors, errors=tuple(errors))


def build_operator_report(link_set: dict[str, Any]) -> str:
    lines: list[str] = [
        "# PMBOT Crypto Rehearsal To Source Quality Links",
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
        f"- Rehearsal source links: {link_set['summary_counts']['rehearsal_source_quality_links']}",
        f"- Source quality artifacts: {link_set['summary_counts']['source_quality_artifacts']}",
        f"- Source quality record links: {link_set['summary_counts']['source_quality_record_links']}",
        f"- Local references: {link_set['summary_counts']['local_references']}",
        "",
        "## Rehearsal Packet",
        "",
        f"- Packet: `{link_set['rehearsal_packet']['packet_id']}`",
        f"- Fixture: `{link_set['rehearsal_packet']['local_reference']}`",
        f"- Records: {link_set['rehearsal_packet']['paperlive_rehearsal_records']}",
        "",
        "## Link Rows",
        "",
    ]
    for row in link_set["rehearsal_source_quality_links"]:
        record_ids = row["source_quality_record_ids"]
        lines.extend(
            [
                f"- `{row['source_id']}`",
                f"  - Rehearsal source field: `{row['rehearsal_source_field']}`",
                f"  - Rehearsal source record: `{row['rehearsal_source_record_id']}`",
                f"  - Capture record: `{record_ids['quality_capture_record_id']}`",
                f"  - Evidence link: `{record_ids['source_evidence_link_id']}`",
                f"  - Staleness check: `{record_ids['source_staleness_check_id']}`",
                f"  - Contradiction rows: {len(record_ids['source_contradiction_row_ids'])}",
                f"  - Review checks: {len(row['review_checks'])} pending operator review",
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
            "- Makes no network, LLM, market API, endpoint, wallet, order, transaction, runtime, browser, scheduler, or worker calls.",
            "- Records local links and pending review state only; source values remain in referenced artifacts.",
            "- No forecast scoring, action guidance, market ranking, outcome resolution, selection advice, or trade instruction output.",
            "- Not execution approval and not runtime input.",
        ]
    )
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build local PMBOT crypto rehearsal to source quality links.")
    parser.add_argument("--output-links", required=True, help="Output rehearsal source quality links JSON path.")
    parser.add_argument("--output-report", required=True, help="Output operator report Markdown path.")
    args = parser.parse_args(argv)

    link_set = build_crypto_rehearsal_source_quality_links()
    validation = validate_crypto_rehearsal_source_quality_links(link_set)
    if not validation.valid:
        raise SourceQualityLedgerValidationError(validation.errors)

    _write_json(Path(args.output_links), link_set)
    Path(args.output_report).write_text(build_operator_report(link_set), encoding="utf-8")
    return 0


def _load_local_json(reference: str) -> dict[str, Any]:
    errors = _validate_local_reference(reference)
    if errors:
        raise SourceQualityLedgerValidationError(tuple(errors))
    return _load_json(Path(_normalize_reference(reference)))


def _validate_input_payloads(inputs: dict[str, dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    if not isinstance(inputs, dict):
        return ["inputs must be an object keyed by local artifact name"]

    packet = inputs.get("rehearsal_packet")
    if not isinstance(packet, dict):
        errors.append("inputs.rehearsal_packet must be an object")
    else:
        if packet.get("contract_version") != "pmbot_crypto_paperlive_rehearsal_packet.v1":
            errors.append("inputs.rehearsal_packet has unexpected contract_version")
        if packet.get("operator_review", {}).get("status") != OPERATOR_REVIEW_STATUS:
            errors.append(f"inputs.rehearsal_packet operator_review.status must be {OPERATOR_REVIEW_STATUS}")
        records = packet.get("paperlive_rehearsal_records")
        if not isinstance(records, list) or len(records) != 1:
            errors.append("inputs.rehearsal_packet must contain exactly one paperlive rehearsal record")

    for spec in SOURCE_QUALITY_ARTIFACT_SPECS:
        key = str(spec["input_key"])
        artifact = inputs.get(key)
        if not isinstance(artifact, dict):
            errors.append(f"inputs.{key} must be an object")
            continue
        if artifact.get("contract_version") != spec["contract_version"]:
            errors.append(f"inputs.{key}.contract_version must be {spec['contract_version']}")
        if artifact.get("operator_review", {}).get("status") != OPERATOR_REVIEW_STATUS:
            errors.append(f"inputs.{key} operator_review.status must be {OPERATOR_REVIEW_STATUS}")
        records = artifact.get(spec["record_collection"])
        if not isinstance(records, list) or not records:
            errors.append(f"inputs.{key}.{spec['record_collection']} must be a non-empty list")
    return errors


def _build_source_quality_artifact(spec: dict[str, Any], artifact: dict[str, Any]) -> dict[str, Any]:
    reference = str(spec["local_reference"])
    digest_reference = _build_digest_reference(reference)
    records = artifact[str(spec["record_collection"])]
    return {
        "artifact_id": str(spec["artifact_id"]),
        "byte_count": digest_reference["byte_count"],
        "content_sha256": digest_reference["content_sha256"],
        "contract_version": artifact["contract_version"],
        "local_reference": reference,
        "operator_review_status": OPERATOR_REVIEW_STATUS,
        "present": True,
        "record_collection": str(spec["record_collection"]),
        "record_count": len(records),
        "record_ids": [_record_identifier(record) for record in records],
    }


def _build_rehearsal_packet_reference(packet: dict[str, Any]) -> dict[str, Any]:
    digest_reference = _build_digest_reference(REHEARSAL_PACKET_FIXTURE_PATH)
    return {
        "byte_count": digest_reference["byte_count"],
        "content_sha256": digest_reference["content_sha256"],
        "contract_version": packet["contract_version"],
        "local_reference": REHEARSAL_PACKET_FIXTURE_PATH,
        "operator_review_status": OPERATOR_REVIEW_STATUS,
        "packet_id": packet["packet_id"],
        "paperlive_rehearsal_records": len(packet["paperlive_rehearsal_records"]),
        "present": True,
        "run_mode": packet["run_mode"],
    }


def _build_link_row(
    packet: dict[str, Any],
    rehearsal_record: dict[str, Any],
    spec: dict[str, Any],
    record_indexes: dict[str, set[str]],
) -> dict[str, Any]:
    source_field = str(spec["rehearsal_source_field"])
    if source_field == "local_snapshot_reference":
        source_record_id = _selected_source_artifact_record_id(packet, str(spec["source_artifact_id"]))
    else:
        source_record_id = str(rehearsal_record[source_field])

    source_quality_record_ids = {
        "quality_capture_record_id": str(spec["capture_record_id"]),
        "source_contradiction_row_ids": list(spec["contradiction_row_ids"]),
        "source_evidence_link_id": str(spec["evidence_link_id"]),
        "source_staleness_check_id": str(spec["staleness_check_id"]),
    }
    _assert_record_ids_known(source_quality_record_ids, record_indexes)
    return {
        "link_id": f"{LINK_SET_ID}.{spec['link_subject']}.rehearsal_source_quality_link",
        "link_kind": "local_static_rehearsal_source_quality_record_link",
        "link_state": LINK_ROW_STATE,
        "local_reference_policy": "local_static_references_only",
        "operator_review_status": OPERATOR_REVIEW_STATUS,
        "packet_record_id": rehearsal_record["packet_record_id"],
        "rehearsal_packet_reference": REHEARSAL_PACKET_FIXTURE_PATH,
        "rehearsal_source_field": source_field,
        "rehearsal_source_record_id": source_record_id,
        "review_checks": [
            {
                "check_id": check["check_id"],
                "description": check["description"],
                "operator_review_status": OPERATOR_REVIEW_STATUS,
            }
            for check in REVIEW_CHECKS
        ],
        "source_id": str(spec["source_id"]),
        "source_quality_artifact_ids": [
            "crypto_source_quality_capture_surface_sample",
            "crypto_source_evidence_link_map_sample",
            "crypto_source_staleness_check_spec_sample",
            "crypto_source_contradiction_ledger_sample",
        ],
        "source_quality_record_ids": source_quality_record_ids,
        "value_policy": "record_identifiers_only_source_values_remain_in_local_artifacts",
    }


def _selected_source_artifact_record_id(packet: dict[str, Any], source_artifact_id: str) -> str:
    for artifact in packet["source_artifact_records"]:
        if artifact.get("source_artifact_id") == source_artifact_id:
            return str(artifact["selected_record_id"])
    raise SourceQualityLedgerValidationError((f"missing source_artifact_records row: {source_artifact_id}",))


def _source_quality_record_indexes(inputs: dict[str, dict[str, Any]]) -> dict[str, set[str]]:
    indexes: dict[str, set[str]] = {}
    for spec in SOURCE_QUALITY_ARTIFACT_SPECS:
        records = inputs[str(spec["input_key"])][str(spec["record_collection"])]
        indexes[str(spec["artifact_id"])] = {_record_identifier(record) for record in records}
    return indexes


def _assert_record_ids_known(record_ids: dict[str, Any], indexes: dict[str, set[str]]) -> None:
    required = {
        "crypto_source_quality_capture_surface_sample": [record_ids["quality_capture_record_id"]],
        "crypto_source_evidence_link_map_sample": [record_ids["source_evidence_link_id"]],
        "crypto_source_staleness_check_spec_sample": [record_ids["source_staleness_check_id"]],
        "crypto_source_contradiction_ledger_sample": list(record_ids["source_contradiction_row_ids"]),
    }
    missing = [
        f"{artifact_id}:{record_id}"
        for artifact_id, ids in required.items()
        for record_id in ids
        if record_id not in indexes.get(artifact_id, set())
    ]
    if missing:
        raise SourceQualityLedgerValidationError(("missing source quality record ids: " + ", ".join(missing),))


def _record_identifier(record: dict[str, Any]) -> str:
    for field in ("record_id", "row_id", "link_id", "check_id"):
        value = record.get(field)
        if isinstance(value, str) and value:
            return value
    raise SourceQualityLedgerValidationError(("source quality record is missing a supported record identifier",))


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
    artifacts: list[dict[str, Any]],
    link_rows: list[dict[str, Any]],
    warnings: list[str],
) -> dict[str, int]:
    local_references = {
        DOCUMENTATION_PATH,
        REHEARSAL_PACKET_DOCUMENTATION_PATH,
        REHEARSAL_PACKET_FIXTURE_PATH,
        *(artifact["local_reference"] for artifact in artifacts),
        *(row["rehearsal_packet_reference"] for row in link_rows),
    }
    source_quality_record_links = 0
    for row in link_rows:
        record_ids = row["source_quality_record_ids"]
        source_quality_record_links += 3 + len(record_ids["source_contradiction_row_ids"])
    return {
        "link_fields": len(EXPECTED_LINK_FIELDS),
        "local_references": len(local_references),
        "operator_review_steps": len(OPERATOR_REVIEW_STEPS),
        "packet_records": 1,
        "required_validation_commands": len(REQUIRED_VALIDATION_COMMANDS),
        "review_checks": sum(len(row["review_checks"]) for row in link_rows),
        "rehearsal_source_quality_links": len(link_rows),
        "source_quality_artifacts": len(artifacts),
        "source_quality_record_links": source_quality_record_links,
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


def _validate_rehearsal_packet_reference(value: Any, errors: list[str]) -> dict[str, Any] | None:
    reference = _validate_reference_object("rehearsal_packet", value, errors)
    if not isinstance(value, dict) or reference is None:
        return None
    for field in (
        "contract_version",
        "operator_review_status",
        "packet_id",
        "paperlive_rehearsal_records",
        "run_mode",
    ):
        if field not in value:
            errors.append(f"rehearsal_packet missing required field: {field}")
    if value.get("contract_version") != "pmbot_crypto_paperlive_rehearsal_packet.v1":
        errors.append("rehearsal_packet.contract_version must match the rehearsal packet contract")
    if value.get("operator_review_status") != OPERATOR_REVIEW_STATUS:
        errors.append(f"rehearsal_packet.operator_review_status must be {OPERATOR_REVIEW_STATUS}")
    if value.get("packet_id") != "pmbot-crypto-paperlive-rehearsal-packet-001":
        errors.append("rehearsal_packet.packet_id must match the static rehearsal packet")
    if value.get("paperlive_rehearsal_records") != 1:
        errors.append("rehearsal_packet.paperlive_rehearsal_records must be 1")
    try:
        packet = _load_json(Path(reference))
    except (OSError, SourceQualityLedgerValidationError) as exc:
        errors.append(f"rehearsal_packet.local_reference must load a JSON object: {exc}")
        return None
    if packet.get("operator_review", {}).get("status") != OPERATOR_REVIEW_STATUS:
        errors.append(f"rehearsal_packet source operator_review.status must be {OPERATOR_REVIEW_STATUS}")
    return packet


def _validate_source_quality_artifacts(value: Any, errors: list[str]) -> dict[str, dict[str, Any]] | None:
    if not isinstance(value, list) or not value:
        errors.append("source_quality_artifacts must be a non-empty list")
        return None
    expected_ids = tuple(spec["artifact_id"] for spec in SOURCE_QUALITY_ARTIFACT_SPECS)
    observed_ids = tuple(artifact.get("artifact_id") for artifact in value if isinstance(artifact, dict))
    if observed_ids != expected_ids:
        errors.append("source_quality_artifacts must match the fixed source quality artifact ids")

    artifacts_by_id: dict[str, dict[str, Any]] = {}
    spec_by_id = {spec["artifact_id"]: spec for spec in SOURCE_QUALITY_ARTIFACT_SPECS}
    for index, artifact in enumerate(value):
        path = f"source_quality_artifacts[{index}]"
        if not isinstance(artifact, dict):
            errors.append(f"{path} must be an object")
            continue
        for field in (
            "artifact_id",
            "contract_version",
            "local_reference",
            "operator_review_status",
            "record_collection",
            "record_count",
            "record_ids",
        ):
            if field not in artifact:
                errors.append(f"{path} missing required field: {field}")
        reference = _validate_reference_object(path, artifact, errors)
        artifact_id = artifact.get("artifact_id")
        if isinstance(artifact_id, str):
            artifacts_by_id[artifact_id] = artifact
        spec = spec_by_id.get(artifact_id)
        if spec is None:
            errors.append(f"{path}.artifact_id must be one of the fixed source quality artifacts")
            continue
        if artifact.get("contract_version") != spec["contract_version"]:
            errors.append(f"{path}.contract_version must be {spec['contract_version']}")
        if artifact.get("local_reference") != spec["local_reference"]:
            errors.append(f"{path}.local_reference must match the fixed source quality artifact path")
        if artifact.get("operator_review_status") != OPERATOR_REVIEW_STATUS:
            errors.append(f"{path}.operator_review_status must be {OPERATOR_REVIEW_STATUS}")
        if artifact.get("record_collection") != spec["record_collection"]:
            errors.append(f"{path}.record_collection must be {spec['record_collection']}")
        if not _is_non_empty_string_list(artifact.get("record_ids")):
            errors.append(f"{path}.record_ids must be a non-empty list of strings")
        if reference is not None:
            loaded = _load_json(Path(reference))
            records = loaded.get(spec["record_collection"])
            if not isinstance(records, list) or not records:
                errors.append(f"{path}.local_reference must contain {spec['record_collection']}")
            else:
                expected_record_ids = [_record_identifier(record) for record in records]
                if artifact.get("record_count") != len(records):
                    errors.append(f"{path}.record_count must match local artifact records")
                if artifact.get("record_ids") != expected_record_ids:
                    errors.append(f"{path}.record_ids must match local artifact record ids")
    return artifacts_by_id


def _validate_link_rows(
    value: Any,
    packet: dict[str, Any] | None,
    artifacts: dict[str, dict[str, Any]] | None,
    errors: list[str],
) -> dict[str, int] | None:
    if not isinstance(value, list) or not value:
        errors.append("rehearsal_source_quality_links must be a non-empty list")
        return None
    if len(value) != len(REHEARSAL_SOURCE_LINK_SPECS):
        errors.append("rehearsal_source_quality_links must match the fixed link spec count")

    packet_record: dict[str, Any] | None = None
    if packet is not None:
        records = packet.get("paperlive_rehearsal_records")
        if isinstance(records, list) and records and isinstance(records[0], dict):
            packet_record = records[0]

    seen_ids: set[str] = set()
    for index, row in enumerate(value):
        path = f"rehearsal_source_quality_links[{index}]"
        if not isinstance(row, dict):
            errors.append(f"{path} must be an object")
            continue
        spec = REHEARSAL_SOURCE_LINK_SPECS[index] if index < len(REHEARSAL_SOURCE_LINK_SPECS) else None
        _validate_link_row(path, row, spec, packet_record, artifacts, seen_ids, errors)
    return {"rehearsal_source_quality_links": len(value)}


def _validate_link_row(
    path: str,
    row: dict[str, Any],
    spec: dict[str, Any] | None,
    packet_record: dict[str, Any] | None,
    artifacts: dict[str, dict[str, Any]] | None,
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
        "packet_record_id",
        "rehearsal_packet_reference",
        "rehearsal_source_field",
        "rehearsal_source_record_id",
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
    if row.get("rehearsal_packet_reference") != REHEARSAL_PACKET_FIXTURE_PATH:
        errors.append(f"{path}.rehearsal_packet_reference must match the rehearsal packet fixture path")
    if isinstance(row.get("rehearsal_packet_reference"), str):
        errors.extend(f"{path}.{error}" for error in _validate_local_reference(row["rehearsal_packet_reference"]))

    if spec is not None:
        expected_link_id = f"{LINK_SET_ID}.{spec['link_subject']}.rehearsal_source_quality_link"
        if row.get("link_id") != expected_link_id:
            errors.append(f"{path}.link_id must match the fixed link subject")
        if row.get("rehearsal_source_field") != spec["rehearsal_source_field"]:
            errors.append(f"{path}.rehearsal_source_field must match the fixed link spec")
        if row.get("source_id") != spec["source_id"]:
            errors.append(f"{path}.source_id must match the fixed link spec")

    if packet_record is not None:
        if row.get("packet_record_id") != packet_record.get("packet_record_id"):
            errors.append(f"{path}.packet_record_id must match the rehearsal packet record")
        source_field = row.get("rehearsal_source_field")
        if isinstance(source_field, str) and source_field != "local_snapshot_reference":
            if row.get("rehearsal_source_record_id") != packet_record.get(source_field):
                errors.append(f"{path}.rehearsal_source_record_id must match rehearsal packet source field")

    _validate_review_checks(path, row.get("review_checks"), errors)
    _validate_link_artifact_ids(path, row.get("source_quality_artifact_ids"), artifacts, errors)
    _validate_link_record_ids(path, row.get("source_quality_record_ids"), spec, artifacts, errors)


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
    value: Any,
    artifacts: dict[str, dict[str, Any]] | None,
    errors: list[str],
) -> None:
    expected_ids = [spec["artifact_id"] for spec in SOURCE_QUALITY_ARTIFACT_SPECS]
    if value != expected_ids:
        errors.append(f"{path}.source_quality_artifact_ids must match the fixed source quality artifact ids")
    if artifacts is not None and isinstance(value, list):
        missing = [artifact_id for artifact_id in value if artifact_id not in artifacts]
        if missing:
            errors.append(f"{path}.source_quality_artifact_ids missing source_quality_artifacts rows: " + ", ".join(missing))


def _validate_link_record_ids(
    path: str,
    value: Any,
    spec: dict[str, Any] | None,
    artifacts: dict[str, dict[str, Any]] | None,
    errors: list[str],
) -> None:
    if not isinstance(value, dict):
        errors.append(f"{path}.source_quality_record_ids must be an object")
        return
    required_fields = (
        "quality_capture_record_id",
        "source_contradiction_row_ids",
        "source_evidence_link_id",
        "source_staleness_check_id",
    )
    if tuple(value.keys()) != required_fields:
        errors.append(f"{path}.source_quality_record_ids fields must match the fixed contract")
    for field in ("quality_capture_record_id", "source_evidence_link_id", "source_staleness_check_id"):
        if not isinstance(value.get(field), str) or not value.get(field):
            errors.append(f"{path}.source_quality_record_ids.{field} must be a non-empty string")
    if not _is_non_empty_string_list(value.get("source_contradiction_row_ids")):
        errors.append(f"{path}.source_quality_record_ids.source_contradiction_row_ids must be a non-empty list of strings")

    if spec is not None:
        expected = {
            "quality_capture_record_id": spec["capture_record_id"],
            "source_evidence_link_id": spec["evidence_link_id"],
            "source_staleness_check_id": spec["staleness_check_id"],
        }
        for field, expected_value in expected.items():
            if value.get(field) != expected_value:
                errors.append(f"{path}.source_quality_record_ids.{field} must match the fixed link spec")
        if value.get("source_contradiction_row_ids") != list(spec["contradiction_row_ids"]):
            errors.append(f"{path}.source_quality_record_ids.source_contradiction_row_ids must match the fixed link spec")

    if artifacts is not None:
        checks = {
            "crypto_source_quality_capture_surface_sample": [value.get("quality_capture_record_id")],
            "crypto_source_evidence_link_map_sample": [value.get("source_evidence_link_id")],
            "crypto_source_staleness_check_spec_sample": [value.get("source_staleness_check_id")],
            "crypto_source_contradiction_ledger_sample": value.get("source_contradiction_row_ids"),
        }
        for artifact_id, record_ids in checks.items():
            artifact = artifacts.get(artifact_id)
            if artifact is None or not isinstance(record_ids, list):
                continue
            known_ids = set(artifact.get("record_ids", []))
            for record_id in record_ids:
                if isinstance(record_id, str) and record_id not in known_ids:
                    errors.append(f"{path}.source_quality_record_ids {record_id} must exist in {artifact_id}")


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
