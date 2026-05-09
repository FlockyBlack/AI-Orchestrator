from __future__ import annotations

import json
from pathlib import Path


DOC_PATH = Path("docs/PMBOT_CRYPTO_LIVE_001_READ_ONLY_CRYPTO_DATA_CONTRACT_LOCAL_ONLY.md")
FIXTURE_PATH = Path("pm_bot/tests/fixtures/crypto_live/pmbot_read_only_crypto_data_contract.valid.json")
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
TASK_ID = "PMBOT-CRYPTO-LIVE-001-READ-ONLY-CRYPTO-DATA-CONTRACT-LOCAL-ONLY"
CONTRACT_ID = "pmbot-crypto-live-read-only-crypto-data-contract"
CONTRACT_VERSION = "pmbot_crypto_live_read_only_crypto_data_contract.v1"
RUN_MODE = "local_static_read_only_crypto_data_contract"
OPERATOR_REVIEW_STATUS = "pending_operator_review"

EXPECTED_CRYPTO_DATA_OBSERVATION_FIELDS = (
    "record_id",
    "source_label",
    "source_class",
    "source_access_mode",
    "captured_at_utc",
    "asset_symbol",
    "asset_name",
    "metric_type",
    "measurement_source_label",
    "reported_at_utc",
    "reported_reference_unit",
    "local_snapshot_reference",
    "included_static_fields",
    "allowed_handling",
    "freshness_label",
    "operator_review_status",
    "excluded_operations",
    "notes",
)
EXPECTED_FIELD_RULES = (
    "asset_symbol",
    "asset_name",
    "metric_type",
    "measurement_source_label",
    "reported_reference_value",
    "reported_reference_unit",
    "reported_at_utc",
    "source_label",
)
EXPECTED_CHECK_IDS = (
    "local_reference_review",
    "static_crypto_snapshot_review",
    "field_name_inventory_review",
    "static_timestamp_review",
    "sensitive_path_exclusion_check",
    "runtime_boundary_check",
    "output_boundary_check",
    "validation_replay_check",
)
EXPECTED_RULE_IDS = (
    "local_fixture_input_only",
    "descriptive_crypto_records_only",
    "static_value_copy_boundary",
    "local_references_only",
    "endpoint_and_process_boundary_closed",
    "execution_instruction_boundary_closed",
)
EXPECTED_SOURCE_ARTIFACT_IDS = (
    "crypto_market_class_capture_template",
    "crypto_operator_review_protocol",
    "crypto_paperlive_observation_ledger",
    "static_crypto_reference_snapshot",
)
EXPECTED_SOURCE_CONTRACT_IDS = (
    "crypto_market_class_capture_template",
    "crypto_operator_review_protocol",
    "crypto_paperlive_observation_ledger",
    "crypto_source_quality_capture_surface",
    "supervised_read_only_live_data_contract",
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
ALLOWED_LOCAL_PREFIXES = ("docs/", "pm_bot/readiness/", "pm_bot/tests/", "tests/")


def test_static_read_only_crypto_data_contract_fixture_has_expected_contract() -> None:
    contract = _load_contract()

    assert tuple(contract.keys()) == tuple(sorted(contract.keys()))
    assert contract["task_id"] == TASK_ID
    assert contract["contract_id"] == CONTRACT_ID
    assert contract["contract_version"] == CONTRACT_VERSION
    assert contract["run_mode"] == RUN_MODE
    assert contract["created_at"] == "2026-05-09T00:40:00Z"
    assert contract["local_only"] is True
    assert contract["operator_review_required"] is True
    assert contract["operator_review"]["status"] == OPERATOR_REVIEW_STATUS
    assert contract["errors"] == []
    assert contract["warnings"] == []


def test_crypto_data_fields_and_static_sample_are_fixed_local_and_read_only() -> None:
    contract = _load_contract()

    assert tuple(contract["crypto_data_observation_fields"]) == EXPECTED_CRYPTO_DATA_OBSERVATION_FIELDS
    assert len(contract["static_sample_records"]) == 1
    sample = contract["static_sample_records"][0]

    assert tuple(sample.keys()) == tuple(sorted(sample.keys()))
    assert set(sample) == set(EXPECTED_CRYPTO_DATA_OBSERVATION_FIELDS)
    assert sample["record_id"] == "read_only_crypto_data_contract.sample_001"
    assert sample["source_access_mode"] == "local_fixture_copy"
    assert sample["operator_review_status"] == OPERATOR_REVIEW_STATUS
    assert sample["freshness_label"] == "static_sample_no_currentness_claim"
    assert "://" not in sample["local_snapshot_reference"]
    assert sample["local_snapshot_reference"] == str(SNAPSHOT_FIXTURE_PATH).replace("\\", "/")
    assert tuple(sample["excluded_operations"]) == EXPECTED_EXCLUDED_OPERATIONS
    assert sample["included_static_fields"] == [
        "asset_symbol",
        "asset_name",
        "metric_type",
        "measurement_source_label",
        "reported_reference_value",
        "reported_reference_unit",
        "reported_at_utc",
        "source_label",
    ]
    assert "reported_reference_value" not in sample


def test_static_sample_copies_labels_but_not_source_values_from_crypto_snapshot() -> None:
    contract = _load_contract()
    snapshot = _load_json(SNAPSHOT_FIXTURE_PATH)
    sample = contract["static_sample_records"][0]
    serialized_contract = json.dumps(contract, sort_keys=True)

    assert sample["asset_symbol"] == snapshot["asset_symbol"]
    assert sample["asset_name"] == snapshot["asset_name"]
    assert sample["metric_type"] == snapshot["metric_type"]
    assert sample["measurement_source_label"] == snapshot["measurement_source_label"]
    assert sample["reported_reference_unit"] == snapshot["reported_reference_unit"]
    assert sample["reported_at_utc"] == snapshot["reported_at_utc"]
    assert sample["source_label"] == snapshot["source_label"]
    assert snapshot["reported_reference_value"] not in serialized_contract
    assert "150000.00" not in serialized_contract


def test_field_handling_rules_keep_source_values_in_referenced_fixture() -> None:
    contract = _load_contract()

    assert tuple(rule["field_name"] for rule in contract["field_handling_rules"]) == EXPECTED_FIELD_RULES
    assert all(rule["operator_review_status"] == OPERATOR_REVIEW_STATUS for rule in contract["field_handling_rules"])
    value_rule = next(rule for rule in contract["field_handling_rules"] if rule["field_name"] == "reported_reference_value")

    assert value_rule["handling_class"] == "source_value_not_copied_into_contract"
    assert value_rule["allowed_handling"] == "retain_in_referenced_local_fixture"
    assert value_rule["excluded_handling"] == [
        "current_external_state_claim",
        "threshold_comparison",
        "market_ranking",
        "execution_instruction",
        "runtime_input",
    ]


def test_source_artifacts_reference_existing_local_crypto_fixtures() -> None:
    contract = _load_contract()
    expected_paths = [
        str(CAPTURE_FIXTURE_PATH).replace("\\", "/"),
        str(PROTOCOL_FIXTURE_PATH).replace("\\", "/"),
        str(LEDGER_FIXTURE_PATH).replace("\\", "/"),
        str(SNAPSHOT_FIXTURE_PATH).replace("\\", "/"),
    ]

    assert tuple(source["source_artifact_id"] for source in contract["source_artifacts"]) == EXPECTED_SOURCE_ARTIFACT_IDS
    assert [source["fixture_reference"] for source in contract["source_artifacts"]] == expected_paths
    for source in contract["source_artifacts"]:
        assert set(source) == {
            "contract_version",
            "fixture_reference",
            "included_fields",
            "required_state",
            "source_artifact_id",
        }
        assert "://" not in source["fixture_reference"]
        assert source["fixture_reference"].startswith("pm_bot/tests/fixtures/")
        loaded = _load_json(Path(source["fixture_reference"]))
        assert loaded["contract_version"] == source["contract_version"]
        assert set(source["included_fields"]).issubset(loaded)


def test_source_contracts_reference_only_local_review_artifacts() -> None:
    contract = _load_contract()

    assert tuple(source["source_contract_id"] for source in contract["source_contracts"]) == EXPECTED_SOURCE_CONTRACT_IDS
    for source in contract["source_contracts"]:
        assert set(source) == {
            "contract_version",
            "local_reference",
            "required_state",
            "source_contract_id",
        }
        assert "://" not in source["local_reference"]
        assert source["local_reference"].startswith(ALLOWED_LOCAL_PREFIXES)


def test_read_only_rules_and_operator_checks_remain_pending_review() -> None:
    contract = _load_contract()

    assert tuple(rule["rule_id"] for rule in contract["read_only_rules"]) == EXPECTED_RULE_IDS
    assert all(rule["status"] == "active" for rule in contract["read_only_rules"])
    assert tuple(check["check_id"] for check in contract["operator_review_checklist"]) == EXPECTED_CHECK_IDS
    assert all(check["status"] == OPERATOR_REVIEW_STATUS for check in contract["operator_review_checklist"])


def test_safety_boundaries_are_closed_for_read_only_crypto_data_contract() -> None:
    contract = _load_contract()

    assert contract["safety_boundaries"] == EXPECTED_SAFETY_BOUNDARIES


def test_validation_commands_are_recorded_for_operator_run_local_checks() -> None:
    contract = _load_contract()

    assert contract["required_validation_commands"] == [
        "python -m compileall pm_bot tests",
        "pytest pm_bot/tests tests/test_codex_queue_pmbot_templates.py",
    ]


def test_summary_counts_match_contract_content() -> None:
    contract = _load_contract()

    assert contract["summary_counts"] == {
        "field_handling_rules": len(contract["field_handling_rules"]),
        "operator_review_checklist_items": len(contract["operator_review_checklist"]),
        "read_only_rules": len(contract["read_only_rules"]),
        "required_validation_commands": len(contract["required_validation_commands"]),
        "source_artifacts": len(contract["source_artifacts"]),
        "source_contracts": len(contract["source_contracts"]),
        "static_sample_records": len(contract["static_sample_records"]),
        "warnings": len(contract["warnings"]),
    }


def test_fixture_has_no_decision_scoring_or_selection_terms() -> None:
    contract = _load_contract()

    assert _find_disallowed_terms(contract) == []


def test_documentation_registers_contract_fixture_and_safety_boundary() -> None:
    document = DOC_PATH.read_text(encoding="utf-8")

    assert f"Task: `{TASK_ID}`" in document
    assert f"Contract: `{CONTRACT_VERSION}`" in document
    assert f"Run mode: `{RUN_MODE}`" in document
    assert str(FIXTURE_PATH).replace("\\", "/") in document
    assert "does not fetch crypto data, call endpoints, approve execution, compare thresholds" in document
    assert "No forecast scoring, action guidance, market ranking, numeric prediction metric" in document
    assert "This contract is not execution approval and is not runtime input." in document


def _load_contract() -> dict:
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
            if key in {"fixture_reference", "local_reference", "local_snapshot_reference"}:
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
