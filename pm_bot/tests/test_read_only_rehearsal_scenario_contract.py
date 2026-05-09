from __future__ import annotations

import json
from pathlib import Path


DOC_PATH = Path("docs/PMBOT_REHEARSAL_001_READ_ONLY_REHEARSAL_SCENARIO_CONTRACT_LOCAL_ONLY.md")
FIXTURE_PATH = Path("pm_bot/tests/fixtures/rehearsal/pmbot_read_only_rehearsal_scenario_contract.valid.json")
TASK_ID = "PMBOT-REHEARSAL-001-READ-ONLY-REHEARSAL-SCENARIO-CONTRACT-LOCAL-ONLY"
CONTRACT_ID = "pmbot-read-only-rehearsal-scenario-contract"
CONTRACT_VERSION = "pmbot_read_only_rehearsal_scenario_contract.v1"
RUN_MODE = "local_static_read_only_rehearsal_scenario_contract"
OPERATOR_REVIEW_STATUS = "pending_operator_review"
ALLOWED_LOCAL_PREFIXES = ("docs/", "pm_bot/readiness/", "pm_bot/tests/", "tests/")

EXPECTED_SCENARIO_RECORD_FIELDS = (
    "excluded_operations",
    "input_mode",
    "operator_gate_reference",
    "operator_review_status",
    "operator_review_steps",
    "scenario_record_id",
    "scenario_state",
    "source_snapshot_references",
    "stop_condition_reference",
    "supervised_rehearsal_phase",
    "validation_reference",
)
EXPECTED_CHECK_IDS = (
    "local_reference_review",
    "scenario_scope_review",
    "static_sample_review",
    "operator_gate_review",
    "stop_condition_review",
    "sensitive_path_exclusion_check",
    "runtime_boundary_check",
    "output_boundary_check",
    "validation_replay_check",
)
EXPECTED_SECTION_IDS = (
    "contract_identity_review",
    "read_only_source_review",
    "operator_gate_review",
    "stop_condition_review",
    "validation_review",
)
EXPECTED_SOURCE_ARTIFACT_IDS = (
    "rehearsal_scenario_contract_doc",
    "rehearsal_scenario_contract_fixture",
    "supervised_live_read_only_live_data_contract",
    "supervised_live_data_source_inventory",
    "supervised_live_operator_gate_record",
    "supervised_live_stop_condition_spec",
    "supervised_live_readiness_evidence_bundle",
    "local_to_supervised_live_gap_matrix",
    "forbidden_action_scan",
    "forbidden_language_regression_suite",
    "pmbot_template_validation",
    "read_only_live_data_contract_fixture",
    "live_data_source_inventory_fixture",
    "operator_approval_gate_record_fixture",
    "supervised_live_stop_condition_fixture",
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
    "resident_process_allowed": False,
    "run_codex_changes_allowed": False,
    "runtime_or_dispatcher_changes_allowed": False,
    "scheduler_or_worker_allowed": False,
    "trading_endpoint_calls_allowed": False,
    "transaction_endpoint_calls_allowed": False,
    "wallet_or_signing_material_access_allowed": False,
}


def test_static_rehearsal_scenario_contract_fixture_has_expected_contract() -> None:
    contract = _load_contract()

    assert tuple(contract.keys()) == tuple(sorted(contract.keys()))
    assert contract["task_id"] == TASK_ID
    assert contract["contract_id"] == CONTRACT_ID
    assert contract["contract_version"] == CONTRACT_VERSION
    assert contract["run_mode"] == RUN_MODE
    assert contract["created_at"] == "2026-05-09T02:00:00Z"
    assert contract["local_only"] is True
    assert contract["operator_review_required"] is True
    assert contract["operator_review"]["status"] == OPERATOR_REVIEW_STATUS
    assert contract["operator_review"]["reviewed_at"] is None
    assert contract["operator_review"]["reviewed_by"] is None
    assert contract["errors"] == []
    assert contract["warnings"] == []


def test_scenario_record_is_fixed_local_and_pending_review() -> None:
    contract = _load_contract()

    assert tuple(contract["scenario_record_fields"]) == EXPECTED_SCENARIO_RECORD_FIELDS
    assert len(contract["scenario_records"]) == 1
    record = contract["scenario_records"][0]

    assert tuple(record.keys()) == EXPECTED_SCENARIO_RECORD_FIELDS
    assert record["scenario_record_id"] == (
        "read_only_rehearsal_scenario_contract_001.first_supervised_live_read_only_rehearsal"
    )
    assert record["scenario_state"] == "scenario_contract_only_pending_operator_review"
    assert record["supervised_rehearsal_phase"] == "first_read_only_supervised_live_rehearsal"
    assert record["input_mode"] == "local_fixtures_and_static_samples_only"
    assert record["operator_review_status"] == OPERATOR_REVIEW_STATUS
    assert record["operator_review_steps"] == [
        "confirm_local_fixture_presence",
        "confirm_static_sample_labels",
        "confirm_operator_gate_pending",
        "confirm_stop_conditions_pending",
        "record_validation_result_for_human_review",
    ]
    assert record["excluded_operations"] == [
        "authenticated_request",
        "background_process_start",
        "browser_automation",
        "credential_lookup",
        "network_endpoint_fetch",
        "openrouter_request",
        "order_submission",
        "polymarket_api_request",
        "private_key_lookup",
        "runtime_dispatch",
        "scheduler_start",
        "trading_endpoint_call",
        "transaction_preparation",
        "wallet_balance_read",
    ]
    _assert_allowed_existing_local_reference(record["operator_gate_reference"])
    _assert_allowed_existing_local_reference(record["stop_condition_reference"])
    _assert_allowed_existing_local_reference(record["validation_reference"])
    for local_reference in record["source_snapshot_references"]:
        _assert_allowed_existing_local_reference(local_reference)


def test_review_sections_and_source_artifacts_reference_existing_local_files() -> None:
    contract = _load_contract()

    assert tuple(section["section_id"] for section in contract["review_sections"]) == EXPECTED_SECTION_IDS
    for section in contract["review_sections"]:
        assert tuple(section.keys()) == tuple(sorted(section.keys()))
        assert set(section) == {
            "local_references",
            "operator_review_status",
            "section_id",
            "section_label",
            "section_role",
        }
        assert section["operator_review_status"] == OPERATOR_REVIEW_STATUS
        for local_reference in section["local_references"]:
            _assert_allowed_existing_local_reference(local_reference)

    assert tuple(record["artifact_id"] for record in contract["source_artifacts"]) == EXPECTED_SOURCE_ARTIFACT_IDS
    for record in contract["source_artifacts"]:
        assert tuple(record.keys()) == tuple(sorted(record.keys()))
        assert set(record) == {
            "artifact_id",
            "artifact_type",
            "contract_version",
            "local_reference",
            "operator_review_status",
            "required_state",
            "source_role",
        }
        assert record["operator_review_status"] == OPERATOR_REVIEW_STATUS
        _assert_allowed_existing_local_reference(record["local_reference"])


def test_operator_checks_and_scenario_rules_remain_pending_or_active() -> None:
    contract = _load_contract()

    assert tuple(check["check_id"] for check in contract["operator_review_checklist"]) == EXPECTED_CHECK_IDS
    assert all(check["status"] == OPERATOR_REVIEW_STATUS for check in contract["operator_review_checklist"])
    assert [rule["status"] for rule in contract["scenario_rules"]] == ["active"] * 6
    assert [rule["rule_id"] for rule in contract["scenario_rules"]] == [
        "local_static_inputs_only",
        "descriptive_output_only",
        "operator_review_status_preserved",
        "closed_endpoint_boundary",
        "closed_process_boundary",
        "validation_result_human_review",
    ]


def test_safety_boundaries_are_closed_for_rehearsal_scenario_contract() -> None:
    contract = _load_contract()

    assert contract["safety_boundaries"] == EXPECTED_SAFETY_BOUNDARIES
    assert contract["safety_boundaries"]["local_static_samples_only"] is True
    assert contract["safety_boundaries"]["operator_review_required"] is True
    assert contract["safety_boundaries"]["paper_mode_only"] is True
    assert all(value is False for key, value in contract["safety_boundaries"].items() if key.endswith("_allowed"))


def test_validation_commands_are_recorded_for_operator_run_local_checks() -> None:
    contract = _load_contract()

    assert contract["required_validation_commands"] == [
        "python -m compileall pm_bot tests",
        "pytest pm_bot/tests tests/test_codex_queue_pmbot_templates.py",
    ]


def test_summary_counts_match_rehearsal_scenario_contract_content() -> None:
    contract = _load_contract()
    local_references = {
        *(reference for section in contract["review_sections"] for reference in section["local_references"]),
        *(record["local_reference"] for record in contract["source_artifacts"]),
        contract["scenario_records"][0]["operator_gate_reference"],
        contract["scenario_records"][0]["stop_condition_reference"],
        contract["scenario_records"][0]["validation_reference"],
        *contract["scenario_records"][0]["source_snapshot_references"],
    }

    assert contract["summary_counts"] == {
        "local_references": len(local_references),
        "operator_review_checklist_items": len(contract["operator_review_checklist"]),
        "required_validation_commands": len(contract["required_validation_commands"]),
        "review_sections": len(contract["review_sections"]),
        "scenario_records": len(contract["scenario_records"]),
        "scenario_rules": len(contract["scenario_rules"]),
        "source_artifacts": len(contract["source_artifacts"]),
        "warnings": len(contract["warnings"]),
    }


def test_fixture_has_no_decision_scoring_or_selection_terms() -> None:
    contract = _load_contract()

    assert _find_disallowed_terms(contract) == []


def test_documentation_registers_rehearsal_contract_fixture_and_safety_boundary() -> None:
    document = DOC_PATH.read_text(encoding="utf-8")

    assert f"Task: `{TASK_ID}`" in document
    assert f"Contract: `{CONTRACT_VERSION}`" in document
    assert f"Run mode: `{RUN_MODE}`" in document
    assert "first PMBOT read-only supervised-live rehearsal" in document
    assert str(FIXTURE_PATH).replace("\\", "/") in document
    assert "No market recommendation, forecast scoring, action guidance, or selection advice." in document
    assert "No probability, EV, edge, or confidence scoring." in document
    assert "This contract is not execution approval and is not runtime input." in document


def _load_contract() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def _assert_allowed_existing_local_reference(local_reference: str) -> None:
    assert "://" not in local_reference
    assert local_reference.startswith(ALLOWED_LOCAL_PREFIXES)
    assert Path(local_reference).exists()


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
            if key in {
                "local_reference",
                "local_references",
                "operator_gate_reference",
                "source_snapshot_references",
                "stop_condition_reference",
                "validation_reference",
            }:
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
