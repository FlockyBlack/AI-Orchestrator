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
    _is_non_empty_string_list,
    _is_string_list,
    _load_json,
    _normalize_reference,
    _validate_local_reference,
    _write_json,
)

TASK_ID = "PMBOT-CRYPTO-LIVE-003-CRYPTO-SOURCE-EVIDENCE-LINK-MAP-LOCAL-ONLY"
LINK_MAP_CONTRACT_VERSION = "pmbot_crypto_source_evidence_link_map.v1"
LINK_MAP_ID = "pmbot-crypto-source-evidence-link-map-001"
LINK_MAP_RUN_MODE = "local_static_crypto_source_evidence_link_map"
LINK_MAP_CREATED_AT = "2026-05-09T01:10:00Z"
LINK_ROW_STATE = "descriptive_crypto_source_evidence_link"
BUILD_ID_DIGEST_LENGTH = 12

CRYPTO_INVENTORY_CONTRACT_VERSION = "pmbot_crypto_live_data_source_inventory.v1"
CRYPTO_INVENTORY_ID = "pmbot-crypto-live-data-source-inventory-001"
CRYPTO_INVENTORY_RUN_MODE = "local_static_crypto_live_data_source_inventory"

SAMPLE_LINK_MAP_PATH = "pm_bot/source_quality/samples/crypto_source_evidence_link_map.fixture.json"
SAMPLE_OPERATOR_REPORT_PATH = "pm_bot/source_quality/samples/crypto_source_evidence_link_map.fixture.md"

CRYPTO_INVENTORY_FIXTURE_PATH = (
    "pm_bot/tests/fixtures/crypto_live/pmbot_crypto_live_data_source_inventory.valid.json"
)
CRYPTO_INVENTORY_DOCUMENTATION_PATH = (
    "docs/PMBOT_CRYPTO_LIVE_002_CRYPTO_LIVE_DATA_SOURCE_INVENTORY_LOCAL_ONLY.md"
)
CRYPTO_LINK_MAP_DOCUMENTATION_PATH = (
    "docs/PMBOT_CRYPTO_LIVE_003_CRYPTO_SOURCE_EVIDENCE_LINK_MAP_LOCAL_ONLY.md"
)

REQUIRED_VALIDATION_COMMANDS = (
    "python -m compileall pm_bot tests",
    "pytest pm_bot/tests tests/test_codex_queue_pmbot_templates.py",
)

EXPECTED_SOURCE_IDS = (
    "read_only_crypto_data_contract_fixture",
    "crypto_market_class_capture_template",
    "crypto_operator_review_protocol",
    "crypto_paperlive_observation_ledger",
    "crypto_source_quality_capture_surface_sample",
    "static_crypto_reference_snapshot_2026_05_09_btc",
)

EXPECTED_REVIEW_CHECKS = (
    {
        "check_id": "source_record_identity",
        "description": "Confirm source_id and source record id match the crypto live inventory row.",
    },
    {
        "check_id": "artifact_digest",
        "description": "Confirm source artifact reference and digest match local bytes.",
    },
    {
        "check_id": "contract_documentation",
        "description": "Confirm source contract documentation remains a local static file.",
    },
    {
        "check_id": "pending_review_state",
        "description": "Confirm every link remains pending operator review.",
    },
)

OPERATOR_REVIEW_STEPS = (
    "Confirm every crypto source record has a local artifact link, inventory record link, and contract documentation link.",
    "Confirm linked local references remain static and under allowed paths.",
    "Record disputes outside this map before any later readiness status change.",
)

KNOWN_LIMITATIONS = (
    "Static local map only; no external refresh is performed.",
    "Records references and digests only; source values stay in linked artifacts.",
    "Does not authorize execution and is not runtime input.",
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
    "network_calls_allowed": False,
    "operator_review_required": True,
    "order_or_trade_surface_changes_allowed": False,
    "paper_mode_only": True,
    "runtime_or_dispatcher_changes_allowed": False,
    "scheduler_or_worker_allowed": False,
    "transaction_endpoint_calls_allowed": False,
    "value_transform_allowed": False,
    "wallet_or_signing_material_access_allowed": False,
}

SOURCE_CONTRACT_BY_SOURCE_ID = {
    "read_only_crypto_data_contract_fixture": "crypto_live_read_only_crypto_data_contract",
    "crypto_market_class_capture_template": "crypto_market_class_capture_template",
    "crypto_operator_review_protocol": "crypto_operator_review_protocol",
    "crypto_paperlive_observation_ledger": "crypto_paperlive_observation_ledger",
    "crypto_source_quality_capture_surface_sample": "crypto_source_quality_capture_surface",
    "static_crypto_reference_snapshot_2026_05_09_btc": "crypto_paperlive_observation_ledger",
}

SOURCE_CONTRACT_COVERAGE_BY_SOURCE_ID = {
    "read_only_crypto_data_contract_fixture": "direct_contract_documentation",
    "crypto_market_class_capture_template": "direct_contract_documentation",
    "crypto_operator_review_protocol": "direct_contract_documentation",
    "crypto_paperlive_observation_ledger": "direct_contract_documentation",
    "crypto_source_quality_capture_surface_sample": "direct_contract_documentation",
    "static_crypto_reference_snapshot_2026_05_09_btc": "static_reference_snapshot_covered_by_observation_ledger_contract",
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


def load_crypto_source_evidence_link_map(path: str | Path) -> dict[str, Any]:
    reference = str(path)
    errors = _validate_local_reference(reference)
    if errors:
        raise SourceQualityLedgerValidationError(tuple(errors))
    return _load_json(Path(_normalize_reference(reference)))


def load_crypto_live_data_source_inventory(
    path: str | Path = CRYPTO_INVENTORY_FIXTURE_PATH,
) -> dict[str, Any]:
    reference = str(path)
    errors = _validate_local_reference(reference)
    if errors:
        raise SourceQualityLedgerValidationError(tuple(errors))
    inventory = _load_json(Path(_normalize_reference(reference)))
    validation_errors = _validate_crypto_inventory_payload(inventory)
    if validation_errors:
        raise SourceQualityLedgerValidationError(tuple(validation_errors))
    return inventory


def build_crypto_source_evidence_link_map(inventory: dict[str, Any] | None = None) -> dict[str, Any]:
    inventory = inventory if inventory is not None else load_crypto_live_data_source_inventory()
    validation_errors = _validate_crypto_inventory_payload(inventory)
    if validation_errors:
        raise SourceQualityLedgerValidationError(tuple(validation_errors))

    contract_rows = _contract_rows_by_id(inventory)
    rows = [
        _build_link_row(record, index, inventory, contract_rows)
        for index, record in enumerate(inventory["source_records"])
    ]
    warnings: list[str] = []
    link_map = {
        "build_id": "",
        "contract_version": LINK_MAP_CONTRACT_VERSION,
        "created_at": LINK_MAP_CREATED_AT,
        "documentation": _build_digest_reference(CRYPTO_LINK_MAP_DOCUMENTATION_PATH),
        "errors": [],
        "local_only": True,
        "map_id": LINK_MAP_ID,
        "operator_review": {
            "reviewed_at": None,
            "reviewed_by": None,
            "status": OPERATOR_REVIEW_STATUS,
        },
        "operator_review_required": True,
        "operator_review_steps": list(OPERATOR_REVIEW_STEPS),
        "required_validation_commands": list(REQUIRED_VALIDATION_COMMANDS),
        "run_mode": LINK_MAP_RUN_MODE,
        "safety_boundaries": dict(EXPECTED_SAFETY_BOUNDARIES),
        "source_evidence_links": rows,
        "source_inventory": _build_source_inventory_summary(inventory),
        "source_inventory_documentation": _build_digest_reference(CRYPTO_INVENTORY_DOCUMENTATION_PATH),
        "summary_counts": _summary_counts(rows, warnings),
        "task_id": TASK_ID,
        "warnings": warnings,
    }
    link_map["build_id"] = _build_deterministic_id(link_map)
    return link_map


def validate_crypto_source_evidence_link_map(link_map: dict[str, Any]) -> SourceQualityLedgerValidation:
    errors: list[str] = []
    if not isinstance(link_map, dict):
        return SourceQualityLedgerValidation(valid=False, errors=("link_map must be an object",))

    required_fields = (
        "build_id",
        "contract_version",
        "created_at",
        "documentation",
        "errors",
        "local_only",
        "map_id",
        "operator_review",
        "operator_review_required",
        "operator_review_steps",
        "required_validation_commands",
        "run_mode",
        "safety_boundaries",
        "source_evidence_links",
        "source_inventory",
        "source_inventory_documentation",
        "summary_counts",
        "task_id",
        "warnings",
    )
    for field in required_fields:
        if field not in link_map:
            errors.append(f"missing required link map field: {field}")

    if link_map.get("task_id") != TASK_ID:
        errors.append(f"task_id must be {TASK_ID}")
    if link_map.get("contract_version") != LINK_MAP_CONTRACT_VERSION:
        errors.append(f"contract_version must be {LINK_MAP_CONTRACT_VERSION}")
    if link_map.get("map_id") != LINK_MAP_ID:
        errors.append(f"map_id must be {LINK_MAP_ID}")
    if link_map.get("run_mode") != LINK_MAP_RUN_MODE:
        errors.append(f"run_mode must be {LINK_MAP_RUN_MODE}")
    if link_map.get("created_at") != LINK_MAP_CREATED_AT:
        errors.append(f"created_at must be {LINK_MAP_CREATED_AT}")
    if link_map.get("local_only") is not True:
        errors.append("local_only must be true")
    if link_map.get("operator_review_required") is not True:
        errors.append("operator_review_required must be true")
    if link_map.get("errors") != []:
        errors.append("errors must be an empty list")
    if not _is_string_list(link_map.get("warnings")):
        errors.append("warnings must be a list of strings")
    if link_map.get("safety_boundaries") != EXPECTED_SAFETY_BOUNDARIES:
        errors.append("safety_boundaries must match the crypto link map boundary")
    if link_map.get("required_validation_commands") != list(REQUIRED_VALIDATION_COMMANDS):
        errors.append("required_validation_commands must match the local validation contract")
    if tuple(link_map.get("operator_review_steps", ())) != OPERATOR_REVIEW_STEPS:
        errors.append("operator_review_steps must match the fixed crypto link map review steps")

    _validate_operator_review(link_map.get("operator_review"), errors)
    _validate_reference_object("documentation", link_map.get("documentation"), errors)
    _validate_reference_object(
        "source_inventory_documentation",
        link_map.get("source_inventory_documentation"),
        errors,
    )

    source_inventory = _validate_source_inventory_summary(link_map.get("source_inventory"), errors)
    row_counts = _validate_link_rows(link_map.get("source_evidence_links"), source_inventory, errors)
    _validate_build_id(link_map, errors)

    forbidden_paths = _find_forbidden_output_terms(link_map)
    if forbidden_paths:
        errors.append(
            "forbidden crypto link map output term detected at: "
            + ", ".join(sorted(forbidden_paths))
        )

    if row_counts is not None:
        warnings = link_map.get("warnings") if isinstance(link_map.get("warnings"), list) else []
        expected_counts = dict(row_counts)
        expected_counts["operator_review_steps"] = len(OPERATOR_REVIEW_STEPS)
        expected_counts["required_validation_commands"] = len(REQUIRED_VALIDATION_COMMANDS)
        expected_counts["warnings"] = len(warnings)
        if link_map.get("summary_counts") != expected_counts:
            errors.append("summary_counts must match crypto source evidence link totals: " + _canonical_json(expected_counts))

    return SourceQualityLedgerValidation(valid=not errors, errors=tuple(errors))


def build_operator_report(link_map: dict[str, Any]) -> str:
    lines: list[str] = [
        "# PMBOT Crypto Source Evidence Link Map",
        "",
        f"Task: `{link_map['task_id']}`",
        f"Map: `{link_map['map_id']}`",
        f"Build: `{link_map['build_id']}`",
        f"Contract: `{link_map['contract_version']}`",
        f"Run mode: `{link_map['run_mode']}`",
        f"Operator review: `{link_map['operator_review']['status']}`",
        "",
        "## Summary",
        "",
        f"- Source evidence links: {link_map['summary_counts']['source_evidence_links']}",
        f"- Source artifacts: {link_map['summary_counts']['source_artifact_references']}",
        f"- Source contracts: {link_map['summary_counts']['source_contract_references']}",
        f"- Inventory records linked: {link_map['summary_counts']['inventory_records_linked']}",
        f"- Local references: {link_map['summary_counts']['local_references']}",
        "",
        "## Source Inventory",
        "",
        f"- Inventory: `{link_map['source_inventory']['inventory_id']}`",
        f"- Fixture: `{link_map['source_inventory']['local_reference']}`",
        f"- Documentation: `{link_map['source_inventory_documentation']['local_reference']}`",
        f"- Source records: {link_map['source_inventory']['source_records']}",
        "",
        "## Source Evidence Links",
        "",
    ]
    for row in link_map["source_evidence_links"]:
        lines.extend(
            [
                f"- `{row['source_id']}` ({row['source_label']})",
                f"  - Source artifact: `{row['source_artifact']['local_reference']}`",
                f"  - Source record: `{row['source_record_id']}`",
                f"  - Source contract: `{row['source_contract']['source_contract_id']}`",
                f"  - Contract documentation: `{row['source_contract']['local_reference']}`",
                f"  - Review checks: {len(row['review_checks'])} pending operator review",
            ]
        )

    lines.extend(["", "## Operator Review Steps", ""])
    for step in link_map["operator_review_steps"]:
        lines.append(f"- {step}")

    lines.extend(
        [
            "",
            "## Safety",
            "",
            "- Local fixture/static input only.",
            "- Makes no network, LLM, market API, endpoint, wallet, order, transaction, runtime, browser, scheduler, or worker calls.",
            "- Records local references, byte counts, digests, and pending review state only.",
            "- Does not authorize execution and is not runtime input.",
        ]
    )
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a local PMBOT crypto source evidence link map.")
    parser.add_argument(
        "--inventory",
        default=CRYPTO_INVENTORY_FIXTURE_PATH,
        help="Local crypto live data source inventory fixture.",
    )
    parser.add_argument("--output-map", required=True, help="Output crypto source evidence link map JSON path.")
    parser.add_argument("--output-report", required=True, help="Output operator report Markdown path.")
    args = parser.parse_args(argv)

    inventory = load_crypto_live_data_source_inventory(args.inventory)
    link_map = build_crypto_source_evidence_link_map(inventory)
    validation = validate_crypto_source_evidence_link_map(link_map)
    if not validation.valid:
        raise SourceQualityLedgerValidationError(validation.errors)

    _write_json(Path(args.output_map), link_map)
    Path(args.output_report).write_text(build_operator_report(link_map), encoding="utf-8")
    return 0


def _validate_crypto_inventory_payload(inventory: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if not isinstance(inventory, dict):
        return ["crypto inventory must be an object"]
    if inventory.get("contract_version") != CRYPTO_INVENTORY_CONTRACT_VERSION:
        errors.append(f"crypto inventory contract_version must be {CRYPTO_INVENTORY_CONTRACT_VERSION}")
    if inventory.get("inventory_id") != CRYPTO_INVENTORY_ID:
        errors.append(f"crypto inventory inventory_id must be {CRYPTO_INVENTORY_ID}")
    if inventory.get("run_mode") != CRYPTO_INVENTORY_RUN_MODE:
        errors.append(f"crypto inventory run_mode must be {CRYPTO_INVENTORY_RUN_MODE}")
    if inventory.get("local_only") is not True:
        errors.append("crypto inventory local_only must be true")
    if inventory.get("operator_review_required") is not True:
        errors.append("crypto inventory operator_review_required must be true")

    operator_review = inventory.get("operator_review")
    if not isinstance(operator_review, dict) or operator_review.get("status") != OPERATOR_REVIEW_STATUS:
        errors.append(f"crypto inventory operator_review.status must be {OPERATOR_REVIEW_STATUS}")

    records = inventory.get("source_records")
    if not isinstance(records, list) or not records:
        errors.append("crypto inventory source_records must be a non-empty list")
    else:
        source_ids = tuple(record.get("source_id") for record in records if isinstance(record, dict))
        if source_ids != EXPECTED_SOURCE_IDS:
            errors.append("crypto inventory source_records must match the expected crypto source ids")
        for index, record in enumerate(records):
            _validate_inventory_record(f"crypto inventory source_records[{index}]", record, errors)

    source_contracts = inventory.get("source_contracts")
    if not isinstance(source_contracts, list) or not source_contracts:
        errors.append("crypto inventory source_contracts must be a non-empty list")
    else:
        contract_ids = {
            contract.get("source_contract_id")
            for contract in source_contracts
            if isinstance(contract, dict)
        }
        missing_contracts = set(SOURCE_CONTRACT_BY_SOURCE_ID.values()) - contract_ids
        if missing_contracts:
            errors.append("crypto inventory source_contracts missing ids: " + ", ".join(sorted(missing_contracts)))
        for index, contract in enumerate(source_contracts):
            _validate_inventory_contract(f"crypto inventory source_contracts[{index}]", contract, errors)
    return errors


def _validate_inventory_record(path: str, record: Any, errors: list[str]) -> None:
    if not isinstance(record, dict):
        errors.append(f"{path} must be an object")
        return
    required_fields = (
        "contract_version",
        "local_reference",
        "operator_review_status",
        "record_id",
        "source_class",
        "source_domain",
        "source_id",
        "source_label",
        "snapshot_id",
    )
    for field in required_fields:
        if not isinstance(record.get(field), str) or not record.get(field):
            errors.append(f"{path}.{field} must be a non-empty string")
    if record.get("operator_review_status") != OPERATOR_REVIEW_STATUS:
        errors.append(f"{path}.operator_review_status must be {OPERATOR_REVIEW_STATUS}")
    reference = record.get("local_reference")
    if isinstance(reference, str):
        reference_errors = _validate_local_reference(reference)
        errors.extend(f"{path}.{error}" for error in reference_errors)
        if not reference_errors and not Path(_normalize_reference(reference)).is_file():
            errors.append(f"{path}.local_reference must exist")


def _validate_inventory_contract(path: str, contract: Any, errors: list[str]) -> None:
    if not isinstance(contract, dict):
        errors.append(f"{path} must be an object")
        return
    required_fields = ("contract_version", "local_reference", "required_state", "source_contract_id")
    for field in required_fields:
        if not isinstance(contract.get(field), str) or not contract.get(field):
            errors.append(f"{path}.{field} must be a non-empty string")
    reference = contract.get("local_reference")
    if isinstance(reference, str):
        reference_errors = _validate_local_reference(reference)
        errors.extend(f"{path}.{error}" for error in reference_errors)
        if not reference_errors and not Path(_normalize_reference(reference)).is_file():
            errors.append(f"{path}.local_reference must exist")


def _build_link_row(
    record: dict[str, Any],
    index: int,
    inventory: dict[str, Any],
    contract_rows: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    source_id = record["source_id"]
    contract_id = SOURCE_CONTRACT_BY_SOURCE_ID[source_id]
    contract = contract_rows[contract_id]
    return {
        "known_limitations": list(KNOWN_LIMITATIONS),
        "link_id": f"{LINK_MAP_ID}.{source_id}.crypto_source_evidence_link",
        "link_kind": "local_static_crypto_source_evidence_review_link",
        "link_state": LINK_ROW_STATE,
        "operator_review_status": OPERATOR_REVIEW_STATUS,
        "review_checks": [
            {
                "check_id": check["check_id"],
                "description": check["description"],
                "operator_review_status": OPERATOR_REVIEW_STATUS,
            }
            for check in EXPECTED_REVIEW_CHECKS
        ],
        "source_artifact": {
            **_build_digest_reference(record["local_reference"]),
            "artifact_format": "json_object",
            "source_artifact_present": True,
        },
        "source_contract": {
            **_build_digest_reference(contract["local_reference"]),
            "contract_coverage": SOURCE_CONTRACT_COVERAGE_BY_SOURCE_ID[source_id],
            "contract_version": contract["contract_version"],
            "required_state": contract["required_state"],
            "source_contract_id": contract["source_contract_id"],
            "source_record_contract_version": record["contract_version"],
        },
        "source_domain": record["source_domain"],
        "source_id": source_id,
        "source_inventory": {
            **_build_digest_reference(CRYPTO_INVENTORY_FIXTURE_PATH),
            "contract_version": inventory["contract_version"],
            "inventory_id": inventory["inventory_id"],
            "record_id": record["record_id"],
            "record_present": True,
            "source_record_index": index,
        },
        "source_label": record["source_label"],
        "source_record_id": record["record_id"],
        "source_record_snapshot_id": record["snapshot_id"],
        "source_record_status": record["operator_review_status"],
        "source_type": record["source_class"],
    }


def _contract_rows_by_id(inventory: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        contract["source_contract_id"]: contract
        for contract in inventory["source_contracts"]
        if isinstance(contract, dict) and isinstance(contract.get("source_contract_id"), str)
    }


def _build_source_inventory_summary(inventory: dict[str, Any]) -> dict[str, Any]:
    return {
        **_build_digest_reference(CRYPTO_INVENTORY_FIXTURE_PATH),
        "contract_version": inventory["contract_version"],
        "inventory_id": inventory["inventory_id"],
        "operator_review_status": inventory["operator_review"]["status"],
        "run_mode": inventory["run_mode"],
        "source_records": len(inventory["source_records"]),
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


def _validate_source_inventory_summary(value: Any, errors: list[str]) -> dict[str, Any] | None:
    path = "source_inventory"
    if not isinstance(value, dict):
        errors.append(f"{path} must be an object")
        return None
    required_fields = (
        "byte_count",
        "content_sha256",
        "contract_version",
        "inventory_id",
        "local_reference",
        "operator_review_status",
        "present",
        "run_mode",
        "source_records",
    )
    for field in required_fields:
        if field not in value:
            errors.append(f"{path} missing required field: {field}")
    for field in (
        "content_sha256",
        "contract_version",
        "inventory_id",
        "local_reference",
        "operator_review_status",
        "run_mode",
    ):
        if not isinstance(value.get(field), str) or not value.get(field):
            errors.append(f"{path}.{field} must be a non-empty string")
    if value.get("contract_version") != CRYPTO_INVENTORY_CONTRACT_VERSION:
        errors.append(f"{path}.contract_version must be {CRYPTO_INVENTORY_CONTRACT_VERSION}")
    if value.get("inventory_id") != CRYPTO_INVENTORY_ID:
        errors.append(f"{path}.inventory_id must be {CRYPTO_INVENTORY_ID}")
    if value.get("run_mode") != CRYPTO_INVENTORY_RUN_MODE:
        errors.append(f"{path}.run_mode must be {CRYPTO_INVENTORY_RUN_MODE}")
    if value.get("operator_review_status") != OPERATOR_REVIEW_STATUS:
        errors.append(f"{path}.operator_review_status must be {OPERATOR_REVIEW_STATUS}")
    if value.get("present") is not True:
        errors.append(f"{path}.present must be true")
    if not isinstance(value.get("source_records"), int) or isinstance(value.get("source_records"), bool):
        errors.append(f"{path}.source_records must be an integer")

    inventory: dict[str, Any] | None = None
    reference = value.get("local_reference")
    if isinstance(reference, str):
        _validate_reference_object(path, value, errors)
        try:
            inventory = _load_json(Path(_normalize_reference(reference)))
        except (OSError, SourceQualityLedgerValidationError) as exc:
            errors.append(f"{path}.local_reference must load a JSON object: {exc}")
        else:
            inventory_errors = _validate_crypto_inventory_payload(inventory)
            errors.extend(f"{path}.{error}" for error in inventory_errors)
            if isinstance(value.get("source_records"), int) and value["source_records"] != len(inventory.get("source_records", [])):
                errors.append(f"{path}.source_records must match local crypto inventory")
    return inventory


def _validate_link_rows(
    rows: Any,
    inventory: dict[str, Any] | None,
    errors: list[str],
) -> dict[str, int] | None:
    if not isinstance(rows, list) or not rows:
        errors.append("source_evidence_links must be a non-empty list")
        return None

    inventory_records_by_source_id: dict[str, dict[str, Any]] = {}
    contract_rows_by_id: dict[str, dict[str, Any]] = {}
    if inventory is not None:
        inventory_records_by_source_id = {
            record["source_id"]: record
            for record in inventory.get("source_records", [])
            if isinstance(record, dict) and isinstance(record.get("source_id"), str)
        }
        contract_rows_by_id = _contract_rows_by_id(inventory)

    seen_link_ids: set[str] = set()
    seen_source_ids: set[str] = set()
    local_references: set[str] = {
        CRYPTO_LINK_MAP_DOCUMENTATION_PATH,
        CRYPTO_INVENTORY_DOCUMENTATION_PATH,
        CRYPTO_INVENTORY_FIXTURE_PATH,
    }
    counts = {
        "inventory_records_linked": 0,
        "local_references": 0,
        "review_checks": 0,
        "source_artifact_references": 0,
        "source_contract_references": 0,
        "source_evidence_links": 0,
    }
    for index, row in enumerate(rows):
        path = f"source_evidence_links[{index}]"
        if not isinstance(row, dict):
            errors.append(f"{path} must be an object")
            continue
        row_counts = _validate_link_row(
            path,
            row,
            index,
            inventory_records_by_source_id,
            contract_rows_by_id,
            seen_link_ids,
            seen_source_ids,
            errors,
        )
        counts["inventory_records_linked"] += row_counts["inventory_records_linked"]
        counts["review_checks"] += row_counts["review_checks"]
        counts["source_artifact_references"] += row_counts["source_artifact_references"]
        counts["source_contract_references"] += row_counts["source_contract_references"]
        counts["source_evidence_links"] += 1
        local_references.update(row_counts["local_references"])
    counts["local_references"] = len(local_references)
    return counts


def _validate_link_row(
    path: str,
    row: dict[str, Any],
    index: int,
    inventory_records_by_source_id: dict[str, dict[str, Any]],
    contract_rows_by_id: dict[str, dict[str, Any]],
    seen_link_ids: set[str],
    seen_source_ids: set[str],
    errors: list[str],
) -> dict[str, Any]:
    required_fields = (
        "known_limitations",
        "link_id",
        "link_kind",
        "link_state",
        "operator_review_status",
        "review_checks",
        "source_artifact",
        "source_contract",
        "source_domain",
        "source_id",
        "source_inventory",
        "source_label",
        "source_record_id",
        "source_record_snapshot_id",
        "source_record_status",
        "source_type",
    )
    for field in required_fields:
        if field not in row:
            errors.append(f"{path} missing required field: {field}")
    for field in (
        "link_id",
        "link_kind",
        "link_state",
        "operator_review_status",
        "source_domain",
        "source_id",
        "source_label",
        "source_record_id",
        "source_record_snapshot_id",
        "source_record_status",
        "source_type",
    ):
        if not isinstance(row.get(field), str) or not row.get(field):
            errors.append(f"{path}.{field} must be a non-empty string")
    if row.get("link_state") != LINK_ROW_STATE:
        errors.append(f"{path}.link_state must be {LINK_ROW_STATE}")
    if row.get("operator_review_status") != OPERATOR_REVIEW_STATUS:
        errors.append(f"{path}.operator_review_status must be {OPERATOR_REVIEW_STATUS}")
    if row.get("source_record_status") != OPERATOR_REVIEW_STATUS:
        errors.append(f"{path}.source_record_status must be {OPERATOR_REVIEW_STATUS}")
    if row.get("known_limitations") != list(KNOWN_LIMITATIONS):
        errors.append(f"{path}.known_limitations must match fixed crypto link map limitations")

    source_id = row.get("source_id")
    link_id = row.get("link_id")
    if isinstance(link_id, str):
        if link_id in seen_link_ids:
            errors.append(f"{path}.link_id duplicates an earlier row")
        seen_link_ids.add(link_id)
    if isinstance(source_id, str):
        if source_id in seen_source_ids:
            errors.append(f"{path}.source_id duplicates an earlier row")
        seen_source_ids.add(source_id)
        if source_id not in EXPECTED_SOURCE_IDS:
            errors.append(f"{path}.source_id must be one of the fixed crypto source ids")
        if link_id != f"{LINK_MAP_ID}.{source_id}.crypto_source_evidence_link":
            errors.append(f"{path}.link_id must be derived from map_id and source_id")

    review_check_count = _validate_review_checks(path, row.get("review_checks"), errors)
    local_references: set[str] = set()
    source_artifact_reference = _validate_reference_object(f"{path}.source_artifact", row.get("source_artifact"), errors)
    source_contract_reference = _validate_source_contract(
        f"{path}.source_contract",
        row.get("source_contract"),
        source_id if isinstance(source_id, str) else "",
        contract_rows_by_id,
        errors,
    )
    source_inventory_reference = _validate_source_inventory_row(
        f"{path}.source_inventory",
        row.get("source_inventory"),
        index,
        errors,
    )
    for reference in (source_artifact_reference, source_contract_reference, source_inventory_reference):
        if reference is not None:
            local_references.add(reference)

    inventory_records_linked = 0
    source_artifact_references = 0
    source_contract_references = 0
    inventory_record = inventory_records_by_source_id.get(source_id) if isinstance(source_id, str) else None
    if inventory_record is None:
        errors.append(f"{path}.source_id must exist in crypto live inventory")
    else:
        inventory_records_linked = 1
        if row.get("source_record_id") != inventory_record.get("record_id"):
            errors.append(f"{path}.source_record_id must match crypto live inventory")
        if row.get("source_record_snapshot_id") != inventory_record.get("snapshot_id"):
            errors.append(f"{path}.source_record_snapshot_id must match crypto live inventory")
        if row.get("source_domain") != inventory_record.get("source_domain"):
            errors.append(f"{path}.source_domain must match crypto live inventory")
        if row.get("source_label") != inventory_record.get("source_label"):
            errors.append(f"{path}.source_label must match crypto live inventory")
        if row.get("source_type") != inventory_record.get("source_class"):
            errors.append(f"{path}.source_type must match crypto live inventory source_class")
        source_artifact = row.get("source_artifact")
        if isinstance(source_artifact, dict):
            source_artifact_references = 1
            if source_artifact.get("local_reference") != inventory_record.get("local_reference"):
                errors.append(f"{path}.source_artifact.local_reference must match crypto live inventory")
        source_contract = row.get("source_contract")
        if isinstance(source_contract, dict):
            source_contract_references = 1
            if source_contract.get("source_record_contract_version") != inventory_record.get("contract_version"):
                errors.append(f"{path}.source_contract.source_record_contract_version must match crypto live inventory")

    return {
        "inventory_records_linked": inventory_records_linked,
        "local_references": local_references,
        "review_checks": review_check_count,
        "source_artifact_references": source_artifact_references,
        "source_contract_references": source_contract_references,
    }


def _validate_source_contract(
    path: str,
    value: Any,
    source_id: str,
    contract_rows_by_id: dict[str, dict[str, Any]],
    errors: list[str],
) -> str | None:
    reference = _validate_reference_object(path, value, errors)
    if not isinstance(value, dict):
        return reference
    required_fields = (
        "contract_coverage",
        "contract_version",
        "required_state",
        "source_contract_id",
        "source_record_contract_version",
    )
    for field in required_fields:
        if not isinstance(value.get(field), str) or not value.get(field):
            errors.append(f"{path}.{field} must be a non-empty string")

    expected_contract_id = SOURCE_CONTRACT_BY_SOURCE_ID.get(source_id)
    if expected_contract_id is not None and value.get("source_contract_id") != expected_contract_id:
        errors.append(f"{path}.source_contract_id must match fixed crypto source contract mapping")
    expected_coverage = SOURCE_CONTRACT_COVERAGE_BY_SOURCE_ID.get(source_id)
    if expected_coverage is not None and value.get("contract_coverage") != expected_coverage:
        errors.append(f"{path}.contract_coverage must match fixed crypto source contract coverage")

    contract = contract_rows_by_id.get(value.get("source_contract_id"))
    if contract is None:
        errors.append(f"{path}.source_contract_id must exist in crypto live inventory source_contracts")
    else:
        if value.get("contract_version") != contract.get("contract_version"):
            errors.append(f"{path}.contract_version must match crypto live inventory source_contracts")
        if value.get("required_state") != contract.get("required_state"):
            errors.append(f"{path}.required_state must match crypto live inventory source_contracts")
        if value.get("local_reference") != contract.get("local_reference"):
            errors.append(f"{path}.local_reference must match crypto live inventory source_contracts")
    return reference


def _validate_source_inventory_row(
    path: str,
    value: Any,
    index: int,
    errors: list[str],
) -> str | None:
    reference = _validate_reference_object(path, value, errors)
    if not isinstance(value, dict):
        return reference
    required_fields = (
        "contract_version",
        "inventory_id",
        "record_id",
        "record_present",
        "source_record_index",
    )
    for field in required_fields:
        if field not in value:
            errors.append(f"{path} missing required field: {field}")
    for field in ("contract_version", "inventory_id", "record_id"):
        if not isinstance(value.get(field), str) or not value.get(field):
            errors.append(f"{path}.{field} must be a non-empty string")
    if value.get("contract_version") != CRYPTO_INVENTORY_CONTRACT_VERSION:
        errors.append(f"{path}.contract_version must be {CRYPTO_INVENTORY_CONTRACT_VERSION}")
    if value.get("inventory_id") != CRYPTO_INVENTORY_ID:
        errors.append(f"{path}.inventory_id must be {CRYPTO_INVENTORY_ID}")
    if value.get("record_present") is not True:
        errors.append(f"{path}.record_present must be true")
    if value.get("source_record_index") != index:
        errors.append(f"{path}.source_record_index must match row index")
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


def _validate_review_checks(row_path: str, review_checks: Any, errors: list[str]) -> int:
    if not isinstance(review_checks, list) or not review_checks:
        errors.append(f"{row_path}.review_checks must be a non-empty list")
        return 0
    if len(review_checks) != len(EXPECTED_REVIEW_CHECKS):
        errors.append(f"{row_path}.review_checks must match fixed crypto review checks")
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
                errors.append(f"{path}.check_id must be one of the fixed crypto review checks")
            elif check.get("description") != expected["description"]:
                errors.append(f"{path}.description must match fixed crypto review check")
        if check.get("operator_review_status") != OPERATOR_REVIEW_STATUS:
            errors.append(f"{path}.operator_review_status must be {OPERATOR_REVIEW_STATUS}")
    return len(review_checks)


def _summary_counts(rows: list[dict[str, Any]], warnings: list[str]) -> dict[str, int]:
    local_references = {
        CRYPTO_LINK_MAP_DOCUMENTATION_PATH,
        CRYPTO_INVENTORY_DOCUMENTATION_PATH,
        CRYPTO_INVENTORY_FIXTURE_PATH,
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
        "inventory_records_linked": len(rows),
        "local_references": len(local_references),
        "operator_review_steps": len(OPERATOR_REVIEW_STEPS),
        "required_validation_commands": len(REQUIRED_VALIDATION_COMMANDS),
        "review_checks": sum(len(row["review_checks"]) for row in rows),
        "source_artifact_references": len(rows),
        "source_contract_references": len(rows),
        "source_evidence_links": len(rows),
        "warnings": len(warnings),
    }


def _build_deterministic_id(link_map: dict[str, Any]) -> str:
    digest_input = {key: value for key, value in link_map.items() if key != "build_id"}
    digest = hashlib.sha256(_canonical_json(digest_input).encode("utf-8")).hexdigest()[:BUILD_ID_DIGEST_LENGTH]
    return f"{LINK_MAP_ID}-{digest}"


def _validate_build_id(link_map: dict[str, Any], errors: list[str]) -> None:
    build_id = link_map.get("build_id")
    if not isinstance(build_id, str) or not build_id:
        errors.append("build_id must be a non-empty string")
        return
    prefix = f"{LINK_MAP_ID}-"
    if not build_id.startswith(prefix):
        errors.append("build_id must start with map_id followed by a digest")
        return
    digest = build_id[len(prefix):]
    if len(digest) != BUILD_ID_DIGEST_LENGTH or any(character not in "0123456789abcdef" for character in digest):
        errors.append(f"build_id digest must be {BUILD_ID_DIGEST_LENGTH} lowercase hex characters")
        return
    if all(field in link_map for field in ("source_evidence_links", "source_inventory", "documentation")):
        expected = _build_deterministic_id({**link_map, "build_id": ""})
        if build_id != expected:
            errors.append("build_id must match deterministic crypto source evidence link map digest")


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
