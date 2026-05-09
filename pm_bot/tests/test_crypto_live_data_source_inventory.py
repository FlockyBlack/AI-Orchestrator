from __future__ import annotations

import json
from pathlib import Path


DOC_PATH = Path("docs/PMBOT_CRYPTO_LIVE_002_CRYPTO_LIVE_DATA_SOURCE_INVENTORY_LOCAL_ONLY.md")
FIXTURE_PATH = Path("pm_bot/tests/fixtures/crypto_live/pmbot_crypto_live_data_source_inventory.valid.json")
READ_ONLY_CONTRACT_FIXTURE_PATH = Path("pm_bot/tests/fixtures/crypto_live/pmbot_read_only_crypto_data_contract.valid.json")
CAPTURE_FIXTURE_PATH = Path(
    "pm_bot/tests/fixtures/crypto_market_class_capture/crypto_market_class_capture_template.valid.json"
)
PROTOCOL_FIXTURE_PATH = Path(
    "pm_bot/tests/fixtures/crypto_operator_review_protocol/crypto_operator_review_protocol.valid.json"
)
LEDGER_FIXTURE_PATH = Path(
    "pm_bot/tests/fixtures/crypto_paperlive_observation_ledger/crypto_paperlive_observation_ledger.valid.json"
)
SNAPSHOT_FIXTURE_PATH = Path(
    "pm_bot/tests/fixtures/crypto_paperlive_observation_ledger/static_crypto_reference_snapshot.valid.json"
)
SOURCE_QUALITY_FIXTURE_PATH = Path("pm_bot/source_quality/samples/crypto_source_quality_capture_surface.fixture.json")
TASK_ID = "PMBOT-CRYPTO-LIVE-002-CRYPTO-LIVE-DATA-SOURCE-INVENTORY-LOCAL-ONLY"
CONTRACT_ID = "pmbot-crypto-live-data-source-inventory"
CONTRACT_VERSION = "pmbot_crypto_live_data_source_inventory.v1"
INVENTORY_ID = "pmbot-crypto-live-data-source-inventory-001"
RUN_MODE = "local_static_crypto_live_data_source_inventory"
OPERATOR_REVIEW_STATUS = "pending_operator_review"

EXPECTED_SOURCE_RECORD_FIELDS = (
    "captured_at_utc",
    "contract_version",
    "excluded_operations",
    "freshness_label",
    "included_fields",
    "local_reference",
    "notes",
    "operator_review_status",
    "record_id",
    "source_access_mode",
    "source_class",
    "source_domain",
    "source_id",
    "source_label",
    "snapshot_id",
)
EXPECTED_SOURCE_IDS = (
    "read_only_crypto_data_contract_fixture",
    "crypto_market_class_capture_template",
    "crypto_operator_review_protocol",
    "crypto_paperlive_observation_ledger",
    "crypto_source_quality_capture_surface_sample",
    "static_crypto_reference_snapshot_2026_05_09_btc",
)
EXPECTED_CHECK_IDS = (
    "local_reference_review",
    "static_record_scope_review",
    "field_inventory_review",
    "currentness_label_review",
    "sensitive_path_exclusion_check",
    "runtime_boundary_check",
    "output_boundary_check",
    "validation_replay_check",
)
EXPECTED_CONTRACT_IDS = (
    "crypto_live_read_only_crypto_data_contract",
    "crypto_market_class_capture_template",
    "crypto_operator_review_protocol",
    "crypto_paperlive_observation_ledger",
    "crypto_source_quality_capture_surface",
    "supervised_live_data_source_inventory_pattern",
)
EXPECTED_EXCLUDED_OPERATIONS = (
    "network_endpoint_fetch",
    "authenticated_request",
    "credential_lookup",
    "wallet_balance_read",
    "transaction_preparation",
    "order_submission",
    "runtime_dispatch",
    "browser_automation",
    "background_process_start",
    "currentness_claim",
    "threshold_comparison",
    "market_ranking",
    "execution_instruction",
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
    "runtime_or_dispatcher_changes_allowed": False,
    "scheduler_or_worker_allowed": False,
    "source_record_ordering_output_allowed": False,
    "threshold_comparison_allowed": False,
    "trade_instruction_allowed": False,
    "transaction_endpoint_calls_allowed": False,
    "value_transform_allowed": False,
    "wallet_or_signing_material_access_allowed": False,
}
ALLOWED_LOCAL_PREFIXES = ("docs/", "pm_bot/readiness/", "pm_bot/source_quality/", "pm_bot/tests/", "tests/")


def test_static_crypto_live_data_source_inventory_fixture_has_expected_contract() -> None:
    inventory = _load_inventory()

    assert tuple(inventory.keys()) == tuple(sorted(inventory.keys()))
    assert inventory["task_id"] == TASK_ID
    assert inventory["contract_id"] == CONTRACT_ID
    assert inventory["contract_version"] == CONTRACT_VERSION
    assert inventory["inventory_id"] == INVENTORY_ID
    assert inventory["run_mode"] == RUN_MODE
    assert inventory["created_at"] == "2026-05-09T01:00:00Z"
    assert inventory["local_only"] is True
    assert inventory["operator_review_required"] is True
    assert inventory["operator_review"]["status"] == OPERATOR_REVIEW_STATUS
    assert inventory["errors"] == []
    assert inventory["warnings"] == []


def test_source_record_fields_and_rows_are_fixed_local_and_pending_review() -> None:
    inventory = _load_inventory()

    assert tuple(inventory["source_record_fields"]) == EXPECTED_SOURCE_RECORD_FIELDS
    assert tuple(record["source_id"] for record in inventory["source_records"]) == EXPECTED_SOURCE_IDS

    for record in inventory["source_records"]:
        assert tuple(record.keys()) == tuple(sorted(record.keys()))
        assert set(record) == set(EXPECTED_SOURCE_RECORD_FIELDS)
        assert record["operator_review_status"] == OPERATOR_REVIEW_STATUS
        assert record["source_access_mode"] == "local_fixture_copy"
        assert record["freshness_label"] in {
            "static_contract_timestamp_only",
            "static_fixture_timestamp_only",
        }
        assert "://" not in record["local_reference"]
        assert record["local_reference"].startswith(ALLOWED_LOCAL_PREFIXES)
        assert Path(record["local_reference"]).is_file()
        assert tuple(record["excluded_operations"]) == EXPECTED_EXCLUDED_OPERATIONS


def test_source_records_inventory_local_crypto_fixture_fields_without_copying_values() -> None:
    inventory = _load_inventory()
    records_by_id = {record["source_id"]: record for record in inventory["source_records"]}

    assert records_by_id["read_only_crypto_data_contract_fixture"]["included_fields"] == [
        "crypto_data_observation_fields",
        "static_sample_records",
        "field_handling_rules",
        "source_artifacts",
        "source_contracts",
        "operator_review",
        "summary_counts",
    ]
    assert records_by_id["crypto_market_class_capture_template"]["included_fields"] == [
        "capture_fields",
        "market_class_catalog",
        "sample_records",
        "operator_review",
        "summary_counts",
    ]
    assert records_by_id["crypto_operator_review_protocol"]["included_fields"] == [
        "review_record_fields",
        "protocol_steps",
        "static_review_records",
        "operator_review",
        "summary_counts",
    ]
    assert records_by_id["crypto_paperlive_observation_ledger"]["included_fields"] == [
        "ledger_record_fields",
        "observation_source_catalog",
        "observation_records",
        "source_contracts",
        "operator_review",
        "summary_counts",
    ]
    assert records_by_id["crypto_source_quality_capture_surface_sample"]["included_fields"] == [
        "capture_surface_fields",
        "input_artifacts",
        "quality_capture_records",
        "operator_review",
        "summary_counts",
    ]
    assert records_by_id["static_crypto_reference_snapshot_2026_05_09_btc"]["included_fields"] == [
        "asset_symbol",
        "asset_name",
        "metric_type",
        "measurement_source_label",
        "reported_reference_value",
        "reported_reference_unit",
        "reported_at_utc",
        "source_label",
    ]
    serialized_inventory = json.dumps(inventory, sort_keys=True)
    assert "102500.00" not in serialized_inventory
    assert "150000.00" not in serialized_inventory


def test_source_records_reference_existing_local_crypto_fixtures() -> None:
    inventory = _load_inventory()
    expected_paths = {
        str(READ_ONLY_CONTRACT_FIXTURE_PATH).replace("\\", "/"),
        str(CAPTURE_FIXTURE_PATH).replace("\\", "/"),
        str(PROTOCOL_FIXTURE_PATH).replace("\\", "/"),
        str(LEDGER_FIXTURE_PATH).replace("\\", "/"),
        str(SOURCE_QUALITY_FIXTURE_PATH).replace("\\", "/"),
        str(SNAPSHOT_FIXTURE_PATH).replace("\\", "/"),
    }

    assert {record["local_reference"] for record in inventory["source_records"]} == expected_paths
    for record in inventory["source_records"]:
        loaded = _load_json(Path(record["local_reference"]))
        assert loaded["contract_version"] == record["contract_version"]
        assert set(record["included_fields"]).issubset(loaded)


def test_source_contracts_reference_only_local_review_artifacts() -> None:
    inventory = _load_inventory()

    assert tuple(source["source_contract_id"] for source in inventory["source_contracts"]) == EXPECTED_CONTRACT_IDS
    for source in inventory["source_contracts"]:
        assert set(source) == {
            "contract_version",
            "local_reference",
            "required_state",
            "source_contract_id",
        }
        assert "://" not in source["local_reference"]
        assert source["local_reference"].startswith(ALLOWED_LOCAL_PREFIXES)
        assert Path(source["local_reference"]).is_file()


def test_review_checks_safety_boundaries_and_validation_commands_are_closed() -> None:
    inventory = _load_inventory()

    assert tuple(check["check_id"] for check in inventory["operator_review_checklist"]) == EXPECTED_CHECK_IDS
    assert all(check["status"] == OPERATOR_REVIEW_STATUS for check in inventory["operator_review_checklist"])
    assert inventory["safety_boundaries"] == EXPECTED_SAFETY_BOUNDARIES
    assert inventory["required_validation_commands"] == [
        "python -m compileall pm_bot tests",
        "pytest pm_bot/tests tests/test_codex_queue_pmbot_templates.py",
    ]


def test_summary_counts_match_inventory_content() -> None:
    inventory = _load_inventory()
    local_references = {record["local_reference"] for record in inventory["source_records"]}

    assert inventory["summary_counts"] == {
        "local_references": len(local_references),
        "operator_review_checklist_items": len(inventory["operator_review_checklist"]),
        "required_validation_commands": len(inventory["required_validation_commands"]),
        "source_contracts": len(inventory["source_contracts"]),
        "source_records": len(inventory["source_records"]),
        "warnings": len(inventory["warnings"]),
    }


def test_fixture_has_no_decision_scoring_or_selection_terms() -> None:
    inventory = _load_inventory()

    assert _find_disallowed_terms(inventory) == []


def test_documentation_registers_inventory_fixture_and_safety_boundary() -> None:
    document = DOC_PATH.read_text(encoding="utf-8")

    assert f"Task: `{TASK_ID}`" in document
    assert f"Inventory: `{INVENTORY_ID}`" in document
    assert f"Contract: `{CONTRACT_VERSION}`" in document
    assert f"Run mode: `{RUN_MODE}`" in document
    assert str(FIXTURE_PATH).replace("\\", "/") in document
    assert "does not fetch crypto data, call endpoints, approve execution, compare thresholds" in document
    assert "No forecast scoring, action guidance, market ranking, numeric prediction metric" in document
    assert "This inventory is not execution approval and is not runtime input." in document


def _load_inventory() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _find_disallowed_terms(value: object, path: str = "$") -> list[str]:
    disallowed_tokens = {
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
    hits: list[str] = []
    if isinstance(value, dict):
        for key, nested_value in value.items():
            key_path = f"{path}.{key}"
            if _has_token(str(key), disallowed_tokens):
                hits.append(key_path)
            if key == "local_reference":
                continue
            hits.extend(_find_disallowed_terms(nested_value, key_path))
    elif isinstance(value, list):
        for index, nested_value in enumerate(value):
            hits.extend(_find_disallowed_terms(nested_value, f"{path}[{index}]"))
    elif isinstance(value, str) and _has_token(value, disallowed_tokens):
        hits.append(path)
    return hits


def _has_token(value: str, disallowed_tokens: set[str]) -> bool:
    normalized = "".join(character if character.isalnum() else "_" for character in value.lower())
    tokens = {token for token in normalized.split("_") if token}
    return bool(tokens & disallowed_tokens)
