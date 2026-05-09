from __future__ import annotations

import json
from pathlib import Path


DOC_PATH = Path("docs/PMBOT_SUPERVISED_LIVE_001_READ_ONLY_LIVE_DATA_CONTRACT_LOCAL_ONLY.md")
FIXTURE_PATH = Path("pm_bot/tests/fixtures/readiness/pmbot_read_only_live_data_contract.valid.json")
TASK_ID = "PMBOT-SUPERVISED-LIVE-001-READ-ONLY-LIVE-DATA-CONTRACT-LOCAL-ONLY"
CONTRACT_ID = "pmbot-supervised-live-read-only-live-data-contract"
CONTRACT_VERSION = "pmbot_supervised_live_read_only_live_data_contract.v1"
RUN_MODE = "local_static_read_only_live_data_contract"
OPERATOR_REVIEW_STATUS = "pending_operator_review"

EXPECTED_OBSERVATION_FIELDS = (
    "record_id",
    "source_label",
    "source_class",
    "capture_mode",
    "captured_at_utc",
    "local_snapshot_reference",
    "read_only_use",
    "source_freshness_label",
    "operator_review_status",
    "excluded_operations",
    "notes",
)
EXPECTED_CHECK_IDS = (
    "local_reference_review",
    "static_sample_review",
    "freshness_label_review",
    "sensitive_path_exclusion_check",
    "runtime_boundary_check",
    "output_boundary_check",
    "validation_replay_check",
)
EXPECTED_RULE_IDS = (
    "local_fixture_input_only",
    "descriptive_records_only",
    "local_references_only",
    "endpoint_and_process_boundary_closed",
    "execution_instruction_boundary_closed",
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
    "operator_review_required": True,
    "order_or_trade_surface_changes_allowed": False,
    "paper_mode_only": True,
    "runtime_or_dispatcher_changes_allowed": False,
    "scheduler_or_worker_allowed": False,
    "transaction_endpoint_calls_allowed": False,
    "wallet_or_signing_material_access_allowed": False,
}
ALLOWED_LOCAL_PREFIXES = ("docs/", "pm_bot/readiness/", "pm_bot/tests/", "tests/")


def test_static_read_only_live_data_contract_fixture_has_expected_contract() -> None:
    contract = _load_contract()

    assert tuple(contract.keys()) == tuple(sorted(contract.keys()))
    assert contract["task_id"] == TASK_ID
    assert contract["contract_id"] == CONTRACT_ID
    assert contract["contract_version"] == CONTRACT_VERSION
    assert contract["run_mode"] == RUN_MODE
    assert contract["created_at"] == "2026-05-09T00:00:00Z"
    assert contract["local_only"] is True
    assert contract["operator_review_required"] is True
    assert contract["operator_review"]["status"] == OPERATOR_REVIEW_STATUS
    assert contract["errors"] == []
    assert contract["warnings"] == []


def test_observation_fields_and_static_samples_are_fixed_local_and_read_only() -> None:
    contract = _load_contract()

    assert tuple(contract["live_data_observation_fields"]) == EXPECTED_OBSERVATION_FIELDS
    assert len(contract["static_sample_records"]) == 1
    sample = contract["static_sample_records"][0]

    assert tuple(sample.keys()) == tuple(sorted(sample.keys()))
    assert set(sample) == set(EXPECTED_OBSERVATION_FIELDS)
    assert sample["record_id"] == "read_only_live_data_snapshot.sample_001"
    assert sample["capture_mode"] == "manual_copy_to_local_fixture"
    assert sample["operator_review_status"] == OPERATOR_REVIEW_STATUS
    assert sample["read_only_use"] == "descriptive_presence_only"
    assert sample["source_freshness_label"] == "static_sample_no_currentness_claim"
    assert "://" not in sample["local_snapshot_reference"]
    assert sample["local_snapshot_reference"].startswith(ALLOWED_LOCAL_PREFIXES)
    assert sample["excluded_operations"] == [
        "network_endpoint_fetch",
        "authenticated_request",
        "credential_lookup",
        "wallet_balance_read",
        "transaction_preparation",
        "order_submission",
        "runtime_dispatch",
    ]


def test_source_contracts_reference_only_local_review_artifacts() -> None:
    contract = _load_contract()

    assert [source["source_contract_id"] for source in contract["source_contracts"]] == [
        "local_to_supervised_live_gap_matrix",
        "real_wallet_readiness_blocker_matrix",
        "simulated_decision_packet_boundary",
    ]
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


def test_safety_boundaries_are_closed_for_read_only_live_data_contract() -> None:
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
        "operator_review_checklist_items": len(contract["operator_review_checklist"]),
        "read_only_rules": len(contract["read_only_rules"]),
        "required_validation_commands": len(contract["required_validation_commands"]),
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
    assert "No forecast scoring, action guidance, market ranking, numeric prediction metric" in document
    assert "This contract is not execution approval and is not runtime input." in document


def _load_contract() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


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
            if key in {"local_reference", "local_snapshot_reference"}:
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
