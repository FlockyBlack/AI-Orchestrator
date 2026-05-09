from __future__ import annotations

import json
from pathlib import Path


DOC_PATH = Path("docs/PMBOT_REHEARSAL_005_REHEARSAL_STOP_CONDITION_TRIGGER_MATRIX_LOCAL_ONLY.md")
FIXTURE_PATH = Path("pm_bot/tests/fixtures/rehearsal/pmbot_rehearsal_stop_condition_trigger_matrix.valid.json")
TASK_ID = "PMBOT-REHEARSAL-005-REHEARSAL-STOP-CONDITION-TRIGGER-MATRIX-LOCAL-ONLY"
CONTRACT_ID = "pmbot-rehearsal-stop-condition-trigger-matrix"
CONTRACT_VERSION = "pmbot_rehearsal_stop_condition_trigger_matrix.v1"
MATRIX_ID = "pmbot-rehearsal-stop-condition-trigger-matrix-001"
RUN_MODE = "local_static_rehearsal_stop_condition_trigger_matrix"
OPERATOR_REVIEW_STATUS = "pending_operator_review"
ALLOWED_LOCAL_PREFIXES = ("docs/", "pm_bot/readiness/", "pm_bot/tests/", "tests/")

EXPECTED_TRIGGER_MATRIX_FIELDS = (
    "blocked_operations",
    "condition_class",
    "condition_id",
    "condition_label",
    "manual_record_required",
    "operator_review_status",
    "required_operator_record_id",
    "trigger_evidence_reference",
    "trigger_matrix_row_id",
    "trigger_review_mode",
    "trigger_source",
    "trigger_state_after_match",
)
EXPECTED_CONDITION_IDS = (
    "operator_manual_stop_request",
    "rehearsal_local_artifact_boundary_breach",
    "rehearsal_forbidden_operation_request_detected",
    "rehearsal_validation_command_failed",
    "rehearsal_source_evidence_mismatch",
    "rehearsal_operator_approval_record_missing",
    "rehearsal_review_status_changed_without_record",
    "rehearsal_output_boundary_breach",
)
EXPECTED_BLOCKED_OPERATIONS = (
    "network_call",
    "openrouter_call",
    "polymarket_api_call",
    "authenticated_request",
    "credential_lookup",
    "wallet_or_signing_material_access",
    "transaction_endpoint_call",
    "order_or_trade_endpoint_call",
    "runtime_or_dispatcher_change",
    "run_codex_wiring_change",
    "browser_automation",
    "scheduler_or_background_worker_start",
)
EXPECTED_REQUIRED_RECORD_FIELDS = (
    "record_id",
    "condition_id",
    "trigger_matrix_row_id",
    "observed_at_utc",
    "observed_by",
    "local_evidence_reference",
    "prior_rehearsal_state",
    "new_rehearsal_state",
    "operator_review_status",
    "unresolved_blockers",
)
EXPECTED_CHECK_IDS = (
    "matrix_identity_review",
    "trigger_row_review",
    "trigger_source_review",
    "trigger_state_review",
    "manual_record_review",
    "sensitive_path_exclusion_check",
    "endpoint_boundary_check",
    "runtime_boundary_check",
    "output_boundary_check",
    "validation_command_review",
)
EXPECTED_RULE_IDS = (
    "manual_stop_precedence",
    "local_static_evidence_required",
    "closed_endpoint_boundary",
    "closed_process_boundary",
    "manual_record_required_before_later_review",
    "operator_review_status_preserved",
    "no_runtime_mutation",
)
EXPECTED_SECTION_IDS = (
    "matrix_identity_review",
    "prior_rehearsal_control_review",
    "trigger_source_review",
    "safety_boundary_review",
    "validation_review",
)
EXPECTED_SOURCE_ARTIFACT_IDS = (
    "rehearsal_001_scenario_contract_doc",
    "rehearsal_001_scenario_contract_fixture",
    "rehearsal_002_market_packet_schema_doc",
    "rehearsal_002_market_packet_schema_fixture",
    "rehearsal_003_source_evidence_bundle_doc",
    "rehearsal_003_source_evidence_bundle_fixture",
    "rehearsal_004_operator_approval_record_doc",
    "rehearsal_004_operator_approval_record_fixture",
    "rehearsal_005_stop_condition_trigger_matrix_doc",
    "rehearsal_005_stop_condition_trigger_matrix_fixture",
    "rehearsal_005_stop_condition_trigger_matrix_test",
    "pmbot_queue_template_validation",
    "safety_forbidden_action_scan_doc",
    "safety_forbidden_language_regression_doc",
)
EXPECTED_LOCAL_REFERENCES = (
    "docs/PMBOT_REHEARSAL_001_READ_ONLY_REHEARSAL_SCENARIO_CONTRACT_LOCAL_ONLY.md",
    "docs/PMBOT_REHEARSAL_002_REHEARSAL_MARKET_PACKET_SCHEMA_LOCAL_ONLY.md",
    "docs/PMBOT_REHEARSAL_003_REHEARSAL_SOURCE_EVIDENCE_BUNDLE_LOCAL_ONLY.md",
    "docs/PMBOT_REHEARSAL_004_REHEARSAL_OPERATOR_APPROVAL_RECORD_LOCAL_ONLY.md",
    "docs/PMBOT_REHEARSAL_005_REHEARSAL_STOP_CONDITION_TRIGGER_MATRIX_LOCAL_ONLY.md",
    "docs/PMBOT_SAFETY_003_FORBIDDEN_ACTION_SCAN_LOCAL_ONLY.md",
    "docs/PMBOT_SAFETY_005_FORBIDDEN_LANGUAGE_REGRESSION_SUITE_LOCAL_ONLY.md",
    "pm_bot/tests/fixtures/rehearsal/pmbot_read_only_rehearsal_scenario_contract.valid.json",
    "pm_bot/tests/fixtures/rehearsal/pmbot_rehearsal_market_packet_schema.valid.json",
    "pm_bot/tests/fixtures/rehearsal/pmbot_rehearsal_operator_approval_record.valid.json",
    "pm_bot/tests/fixtures/rehearsal/pmbot_rehearsal_source_evidence_bundle.valid.json",
    "pm_bot/tests/fixtures/rehearsal/pmbot_rehearsal_stop_condition_trigger_matrix.valid.json",
    "pm_bot/tests/test_read_only_rehearsal_scenario_contract.py",
    "pm_bot/tests/test_rehearsal_market_packet_schema.py",
    "pm_bot/tests/test_rehearsal_operator_approval_record.py",
    "pm_bot/tests/test_rehearsal_source_evidence_bundle.py",
    "pm_bot/tests/test_rehearsal_stop_condition_trigger_matrix.py",
    "tests/test_codex_queue_pmbot_templates.py",
)
EXPECTED_SAFETY_BOUNDARIES = {
    "authenticated_endpoint_calls_allowed": False,
    "background_process_allowed": False,
    "browser_automation_allowed": False,
    "condition_trigger_automation_allowed": False,
    "credential_or_secret_access_allowed": False,
    "descriptive_rehearsal_trigger_matrix_only": True,
    "execution_endpoint_calls_allowed": False,
    "external_service_calls_allowed": False,
    "live_data_refresh_allowed": False,
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
    "stop_condition_mutates_runtime_allowed": False,
    "supervised_live_transition_allowed": False,
    "trading_endpoint_calls_allowed": False,
    "transaction_endpoint_calls_allowed": False,
    "transition_without_record_allowed": False,
    "wallet_or_signing_material_access_allowed": False,
}


def test_static_rehearsal_stop_condition_trigger_matrix_fixture_has_expected_contract() -> None:
    matrix = _load_matrix()

    assert tuple(matrix.keys()) == tuple(sorted(matrix.keys()))
    assert matrix["task_id"] == TASK_ID
    assert matrix["contract_id"] == CONTRACT_ID
    assert matrix["contract_version"] == CONTRACT_VERSION
    assert matrix["matrix_id"] == MATRIX_ID
    assert matrix["run_mode"] == RUN_MODE
    assert matrix["created_at"] == "2026-05-09T04:05:00Z"
    assert matrix["local_only"] is True
    assert matrix["operator_review_required"] is True
    assert matrix["operator_review"] == {
        "reviewed_at": None,
        "reviewed_by": None,
        "status": OPERATOR_REVIEW_STATUS,
    }
    assert matrix["errors"] == []
    assert matrix["warnings"] == []


def test_trigger_matrix_rows_are_fixed_local_pending_and_manual() -> None:
    matrix = _load_matrix()

    assert tuple(matrix["trigger_matrix_fields"]) == EXPECTED_TRIGGER_MATRIX_FIELDS
    assert tuple(row["condition_id"] for row in matrix["trigger_matrix_records"]) == EXPECTED_CONDITION_IDS

    for row in matrix["trigger_matrix_records"]:
        assert tuple(row.keys()) == EXPECTED_TRIGGER_MATRIX_FIELDS
        assert row["manual_record_required"] is True
        assert row["operator_review_status"] == OPERATOR_REVIEW_STATUS
        assert row["trigger_review_mode"] == "manual_operator_review_only"
        assert row["trigger_matrix_row_id"] == f"{MATRIX_ID}.row.{row['condition_id']}"
        assert row["trigger_state_after_match"] in {
            "blocked_until_operator_record_complete",
            "stopped_pending_artifact_review",
            "stopped_pending_operator_record",
            "stopped_pending_output_review",
            "stopped_pending_review_status_record",
            "stopped_pending_safety_review",
            "stopped_pending_source_review",
            "stopped_pending_validation_review",
        }
        assert tuple(row["blocked_operations"]) == EXPECTED_BLOCKED_OPERATIONS
        _assert_allowed_existing_local_reference(row["trigger_evidence_reference"])


def test_required_record_fields_rules_checks_and_sections_are_deterministic() -> None:
    matrix = _load_matrix()

    assert tuple(matrix["required_operator_record_fields"]) == EXPECTED_REQUIRED_RECORD_FIELDS
    assert tuple(rule["rule_id"] for rule in matrix["trigger_matrix_rules"]) == EXPECTED_RULE_IDS
    assert all(tuple(rule.keys()) == ("rule_id", "rule_text", "status") for rule in matrix["trigger_matrix_rules"])
    assert all(rule["status"] == "active" for rule in matrix["trigger_matrix_rules"])
    assert tuple(check["check_id"] for check in matrix["operator_review_checklist"]) == EXPECTED_CHECK_IDS
    assert all(check["status"] == OPERATOR_REVIEW_STATUS for check in matrix["operator_review_checklist"])
    assert tuple(section["section_id"] for section in matrix["review_sections"]) == EXPECTED_SECTION_IDS
    for section in matrix["review_sections"]:
        assert tuple(section.keys()) == tuple(sorted(section.keys()))
        assert section["operator_review_status"] == OPERATOR_REVIEW_STATUS
        for local_reference in section["local_references"]:
            _assert_allowed_existing_local_reference(local_reference)


def test_source_artifacts_reference_only_allowed_existing_local_review_material() -> None:
    matrix = _load_matrix()

    assert tuple(artifact["artifact_id"] for artifact in matrix["source_artifacts"]) == EXPECTED_SOURCE_ARTIFACT_IDS
    for artifact in matrix["source_artifacts"]:
        assert tuple(artifact.keys()) == tuple(sorted(artifact.keys()))
        assert set(artifact) == {
            "artifact_id",
            "contract_version",
            "local_reference",
            "required_state",
        }
        assert artifact["required_state"] in {
            OPERATOR_REVIEW_STATUS,
            "local_safety_reference",
            "local_validation_reference",
        }
        _assert_allowed_existing_local_reference(artifact["local_reference"])


def test_safety_boundaries_are_closed_for_rehearsal_stop_condition_trigger_matrix() -> None:
    matrix = _load_matrix()

    assert matrix["safety_boundaries"] == EXPECTED_SAFETY_BOUNDARIES
    assert matrix["safety_boundaries"]["local_static_samples_only"] is True
    assert matrix["safety_boundaries"]["operator_review_required"] is True
    assert matrix["safety_boundaries"]["paper_mode_only"] is True
    assert all(value is False for key, value in matrix["safety_boundaries"].items() if key.endswith("_allowed"))


def test_validation_commands_are_recorded_for_local_rehearsal_matrix_checks() -> None:
    matrix = _load_matrix()

    assert matrix["required_validation_commands"] == [
        "python -m compileall pm_bot tests",
        "pytest pm_bot/tests tests/test_codex_queue_pmbot_templates.py",
    ]


def test_summary_counts_match_rehearsal_stop_condition_trigger_matrix_content() -> None:
    matrix = _load_matrix()
    local_references = {
        *(row["trigger_evidence_reference"] for row in matrix["trigger_matrix_records"]),
        *(artifact["local_reference"] for artifact in matrix["source_artifacts"]),
        *(reference for section in matrix["review_sections"] for reference in section["local_references"]),
    }

    assert matrix["summary_counts"] == {
        "local_references": len(local_references),
        "operator_review_checklist_items": len(matrix["operator_review_checklist"]),
        "required_operator_record_fields": len(matrix["required_operator_record_fields"]),
        "required_validation_commands": len(matrix["required_validation_commands"]),
        "review_sections": len(matrix["review_sections"]),
        "source_artifacts": len(matrix["source_artifacts"]),
        "trigger_matrix_records": len(matrix["trigger_matrix_records"]),
        "trigger_matrix_records_pending_operator_review": sum(
            1 for row in matrix["trigger_matrix_records"] if row["operator_review_status"] == OPERATOR_REVIEW_STATUS
        ),
        "trigger_matrix_rules": len(matrix["trigger_matrix_rules"]),
        "warnings": len(matrix["warnings"]),
    }


def test_rehearsal_stop_condition_trigger_matrix_references_only_expected_local_static_paths() -> None:
    matrix = _load_matrix()
    references = sorted(
        {
            *(row["trigger_evidence_reference"] for row in matrix["trigger_matrix_records"]),
            *(artifact["local_reference"] for artifact in matrix["source_artifacts"]),
            *(reference for section in matrix["review_sections"] for reference in section["local_references"]),
        }
    )

    assert references == sorted(EXPECTED_LOCAL_REFERENCES)
    for reference in references:
        _assert_allowed_existing_local_reference(reference)


def test_fixture_has_no_decision_scoring_or_selection_terms() -> None:
    matrix = _load_matrix()

    assert _find_disallowed_terms(matrix) == []


def test_documentation_registers_rehearsal_stop_condition_trigger_matrix_and_safety_boundary() -> None:
    document = DOC_PATH.read_text(encoding="utf-8")

    assert f"Task: `{TASK_ID}`" in document
    assert f"Matrix: `{MATRIX_ID}`" in document
    assert f"Contract: `{CONTRACT_VERSION}`" in document
    assert f"Run mode: `{RUN_MODE}`" in document
    assert "read-only rehearsal control" in document
    assert str(FIXTURE_PATH).replace("\\", "/") in document
    assert "No market recommendation, forecast scoring, action guidance, or selection advice." in document
    assert "No probability, EV, edge, or confidence scoring." in document
    assert "This matrix is not execution approval and is not runtime input." in document


def _load_matrix() -> dict:
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
                "required_validation_commands",
                "trigger_evidence_reference",
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
