from __future__ import annotations

import json
from pathlib import Path


DOC_PATH = Path("docs/PMBOT_REHEARSAL_019_REHEARSAL_FAILURE_AND_ROLLBACK_PLAYBOOK_LOCAL_ONLY.md")
FIXTURE_PATH = Path("pm_bot/tests/fixtures/rehearsal/pmbot_rehearsal_failure_and_rollback_playbook.valid.json")
TASK_ID = "PMBOT-REHEARSAL-019-REHEARSAL-FAILURE-AND-ROLLBACK-PLAYBOOK-LOCAL-ONLY"
CONTRACT_ID = "pmbot-rehearsal-failure-and-rollback-playbook"
CONTRACT_VERSION = "pmbot_rehearsal_failure_and_rollback_playbook.v1"
PLAYBOOK_ID = "pmbot-rehearsal-failure-and-rollback-playbook-001"
PLAYBOOK_NAME = "pmbot-rehearsal-failure-and-rollback-playbook"
RUN_MODE = "local_static_rehearsal_failure_and_rollback_playbook"
OPERATOR_REVIEW_STATUS = "pending_operator_review"
ALLOWED_LOCAL_PREFIXES = ("docs/", "pm_bot/tests/", "tests/")

EXPECTED_FAILURE_CLASS_IDS = (
    "operator_manual_stop",
    "validation_command_failure",
    "local_artifact_boundary_breach",
    "forbidden_operation_request",
    "sensitive_path_contact",
    "source_evidence_mismatch",
    "review_record_missing",
    "output_boundary_breach",
)
EXPECTED_FAILURE_CLASS_FIELDS = (
    "blocked_operations",
    "failure_class_id",
    "failure_label",
    "local_evidence_reference",
    "operator_record_required",
    "operator_review_status",
    "post_failure_state",
    "rollback_record_id",
    "rollback_target",
    "source_trigger_reference",
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
EXPECTED_ROLLBACK_STEP_IDS = (
    "identify_fixed_failure_class",
    "freeze_rehearsal_review_status",
    "verify_allowed_local_artifact_scope",
    "confirm_closed_boundaries",
    "restore_pending_operator_review_posture",
    "record_validation_outcome",
)
EXPECTED_BOUNDARY_IDS = (
    "local_static_material_boundary",
    "endpoint_boundary",
    "sensitive_access_boundary",
    "process_boundary",
    "output_boundary",
    "operator_review_boundary",
)
EXPECTED_SECTION_IDS = (
    "playbook_identity_review",
    "failure_class_review",
    "rollback_boundary_review",
    "validation_review",
    "operator_record_review",
)
EXPECTED_SOURCE_ARTIFACT_IDS = (
    "rehearsal_failure_and_rollback_playbook_fixture",
    "rehearsal_failure_and_rollback_playbook_document",
    "rehearsal_failure_and_rollback_playbook_contract_test",
    "rehearsal_operator_approval_record_fixture",
    "rehearsal_operator_approval_record_document",
    "rehearsal_stop_condition_trigger_matrix_fixture",
    "rehearsal_stop_condition_trigger_matrix_document",
    "rehearsal_validation_replay_packet_fixture",
    "rehearsal_validation_replay_packet_document",
    "rehearsal_acceptance_report_document",
    "rehearsal_forbidden_action_scan_fixture",
    "rehearsal_forbidden_action_scan_document",
    "rehearsal_sensitive_path_audit_fixture",
    "rehearsal_sensitive_path_audit_document",
    "queue_template_validation_test",
)
EXPECTED_LOCAL_REFERENCES = (
    "docs/PMBOT_REHEARSAL_004_REHEARSAL_OPERATOR_APPROVAL_RECORD_LOCAL_ONLY.md",
    "docs/PMBOT_REHEARSAL_005_REHEARSAL_STOP_CONDITION_TRIGGER_MATRIX_LOCAL_ONLY.md",
    "docs/PMBOT_REHEARSAL_009_REHEARSAL_VALIDATION_REPLAY_PACKET_LOCAL_ONLY.md",
    "docs/PMBOT_REHEARSAL_013_REHEARSAL_ACCEPTANCE_REPORT_LOCAL_ONLY.md",
    "docs/PMBOT_REHEARSAL_017_REHEARSAL_FORBIDDEN_ACTION_SCAN_LOCAL_ONLY.md",
    "docs/PMBOT_REHEARSAL_018_REHEARSAL_SENSITIVE_PATH_AUDIT_LOCAL_ONLY.md",
    "docs/PMBOT_REHEARSAL_019_REHEARSAL_FAILURE_AND_ROLLBACK_PLAYBOOK_LOCAL_ONLY.md",
    "pm_bot/tests/fixtures/rehearsal/pmbot_rehearsal_failure_and_rollback_playbook.valid.json",
    "pm_bot/tests/fixtures/rehearsal/pmbot_rehearsal_forbidden_action_scan.valid.json",
    "pm_bot/tests/fixtures/rehearsal/pmbot_rehearsal_operator_approval_record.valid.json",
    "pm_bot/tests/fixtures/rehearsal/pmbot_rehearsal_sensitive_path_audit.valid.json",
    "pm_bot/tests/fixtures/rehearsal/pmbot_rehearsal_stop_condition_trigger_matrix.valid.json",
    "pm_bot/tests/fixtures/rehearsal/pmbot_rehearsal_validation_replay_packet.valid.json",
    "pm_bot/tests/test_rehearsal_failure_and_rollback_playbook.py",
    "pm_bot/tests/test_rehearsal_operator_approval_record.py",
    "pm_bot/tests/test_rehearsal_stop_condition_trigger_matrix.py",
    "pm_bot/tests/test_rehearsal_validation_replay_packet.py",
    "tests/test_codex_queue_pmbot_templates.py",
)
EXPECTED_SAFETY_BOUNDARIES = {
    "authenticated_endpoint_calls_allowed": False,
    "background_process_allowed": False,
    "browser_automation_allowed": False,
    "credential_or_secret_access_allowed": False,
    "descriptive_playbook_only": True,
    "execution_endpoint_calls_allowed": False,
    "external_service_calls_allowed": False,
    "live_data_refresh_allowed": False,
    "llm_provider_calls_allowed": False,
    "local_fixtures_only": True,
    "local_static_samples_only": True,
    "market_api_calls_allowed": False,
    "market_instruction_output_allowed": False,
    "market_ranking_allowed": False,
    "network_calls_allowed": False,
    "numeric_prediction_metric_allowed": False,
    "openrouter_calls_allowed": False,
    "operator_review_required": True,
    "order_or_trade_surface_changes_allowed": False,
    "paper_mode_only": True,
    "polymarket_api_calls_allowed": False,
    "resident_process_allowed": False,
    "rollback_automation_allowed": False,
    "rollback_execution_allowed": False,
    "rollback_mutates_runtime_allowed": False,
    "run_codex_changes_allowed": False,
    "runtime_or_dispatcher_changes_allowed": False,
    "scheduler_or_worker_allowed": False,
    "sensitive_path_access_allowed": False,
    "timed_automation_allowed": False,
    "trade_instruction_allowed": False,
    "transaction_endpoint_calls_allowed": False,
    "wallet_or_signing_material_access_allowed": False,
}


def test_static_rehearsal_failure_and_rollback_playbook_fixture_has_expected_contract() -> None:
    playbook = _load_playbook()

    assert tuple(playbook.keys()) == tuple(sorted(playbook.keys()))
    assert playbook["task_id"] == TASK_ID
    assert playbook["contract_id"] == CONTRACT_ID
    assert playbook["contract_version"] == CONTRACT_VERSION
    assert playbook["playbook_id"] == PLAYBOOK_ID
    assert playbook["playbook_name"] == PLAYBOOK_NAME
    assert playbook["run_mode"] == RUN_MODE
    assert playbook["created_at"] == "2026-05-09T12:15:00Z"
    assert playbook["local_only"] is True
    assert playbook["operator_review_required"] is True
    assert playbook["operator_review"] == {
        "reviewed_at": None,
        "reviewed_by": None,
        "status": OPERATOR_REVIEW_STATUS,
    }
    assert playbook["errors"] == []
    assert playbook["warnings"] == []


def test_failure_classes_are_fixed_local_pending_and_manual() -> None:
    playbook = _load_playbook()

    assert tuple(item["failure_class_id"] for item in playbook["failure_classes"]) == EXPECTED_FAILURE_CLASS_IDS
    for item in playbook["failure_classes"]:
        assert tuple(item.keys()) == EXPECTED_FAILURE_CLASS_FIELDS
        assert tuple(item["blocked_operations"]) == EXPECTED_BLOCKED_OPERATIONS
        assert item["operator_record_required"] is True
        assert item["operator_review_status"] == OPERATOR_REVIEW_STATUS
        assert item["post_failure_state"].startswith("stopped_pending_")
        assert item["rollback_record_id"] == f"{PLAYBOOK_ID}.rollback.{item['failure_class_id']}"
        assert item["rollback_target"].startswith("return_to_")
        _assert_allowed_existing_local_reference(item["local_evidence_reference"])
        _assert_allowed_existing_local_reference(item["source_trigger_reference"])


def test_rollback_steps_are_ordered_static_operator_review_records() -> None:
    playbook = _load_playbook()

    assert tuple(item["rollback_step_id"] for item in playbook["rollback_steps"]) == EXPECTED_ROLLBACK_STEP_IDS
    assert tuple(item["step_order"] for item in playbook["rollback_steps"]) == tuple(range(1, 7))
    for item in playbook["rollback_steps"]:
        assert tuple(item.keys()) == tuple(sorted(item.keys()))
        assert item["operator_review_status"] == OPERATOR_REVIEW_STATUS
        assert item["verification_record_required"] is True
        assert item["step_state"].startswith("pending_")
        _assert_allowed_existing_local_reference(item["local_reference"])


def test_rollback_boundaries_remain_closed_static_and_operator_reviewed() -> None:
    playbook = _load_playbook()

    assert tuple(item["boundary_id"] for item in playbook["rollback_boundary_records"]) == EXPECTED_BOUNDARY_IDS
    for item in playbook["rollback_boundary_records"]:
        assert tuple(item.keys()) == tuple(sorted(item.keys()))
        assert item["operator_review_status"] == OPERATOR_REVIEW_STATUS
        assert item["required_record_id"].endswith("_record")
        assert item["closed_state"]
        _assert_allowed_existing_local_reference(item["local_reference"])


def test_review_sections_and_source_artifacts_reference_allowed_local_material() -> None:
    playbook = _load_playbook()

    assert tuple(item["section_id"] for item in playbook["review_sections"]) == EXPECTED_SECTION_IDS
    for item in playbook["review_sections"]:
        assert tuple(item.keys()) == tuple(sorted(item.keys()))
        assert item["operator_review_status"] == OPERATOR_REVIEW_STATUS
        assert item["review_mode"] == "manual_operator_review_only"
        for local_reference in item["local_references"]:
            _assert_allowed_existing_local_reference(local_reference)

    assert tuple(item["artifact_id"] for item in playbook["source_artifacts"]) == EXPECTED_SOURCE_ARTIFACT_IDS
    for item in playbook["source_artifacts"]:
        assert tuple(item.keys()) == (
            "artifact_id",
            "artifact_role",
            "artifact_type",
            "local_reference",
            "operator_review_status",
            "source_task_id",
        )
        assert item["operator_review_status"] == OPERATOR_REVIEW_STATUS
        assert item["source_task_id"]
        _assert_allowed_existing_local_reference(item["local_reference"])


def test_validation_commands_and_records_are_static_local_records() -> None:
    playbook = _load_playbook()

    assert playbook["required_validation_commands"] == [
        "python -m compileall pm_bot tests",
        "pytest pm_bot/tests tests/test_codex_queue_pmbot_templates.py",
    ]
    assert [record["command_label"] for record in playbook["validation_command_records"]] == playbook[
        "required_validation_commands"
    ]
    for record in playbook["validation_command_records"]:
        assert tuple(record.keys()) == tuple(sorted(record.keys()))
        assert record["operator_review_status"] == OPERATOR_REVIEW_STATUS
        assert record["status"] == "not_run_static_record"
        _assert_allowed_existing_local_reference(record["local_reference"])


def test_safety_boundaries_are_closed_for_rehearsal_failure_and_rollback_playbook() -> None:
    playbook = _load_playbook()

    assert playbook["safety_boundaries"] == EXPECTED_SAFETY_BOUNDARIES
    assert playbook["safety_boundaries"]["descriptive_playbook_only"] is True
    assert playbook["safety_boundaries"]["local_fixtures_only"] is True
    assert playbook["safety_boundaries"]["local_static_samples_only"] is True
    assert playbook["safety_boundaries"]["operator_review_required"] is True
    assert playbook["safety_boundaries"]["paper_mode_only"] is True
    assert all(value is False for key, value in playbook["safety_boundaries"].items() if key.endswith("_allowed"))


def test_summary_counts_match_rehearsal_failure_and_rollback_playbook_content() -> None:
    playbook = _load_playbook()
    local_references = set(_collect_values_for_key(playbook, "local_reference"))
    local_references.update(_collect_values_for_key(playbook, "local_evidence_reference"))
    local_references.update(_collect_values_for_key(playbook, "source_trigger_reference"))
    for local_references_list in _collect_values_for_key(playbook, "local_references"):
        local_references.add(local_references_list)

    assert playbook["summary_counts"] == {
        "errors": len(playbook["errors"]),
        "failure_classes": len(playbook["failure_classes"]),
        "failure_classes_pending_operator_review": sum(
            1 for item in playbook["failure_classes"] if item["operator_review_status"] == OPERATOR_REVIEW_STATUS
        ),
        "local_references": len(local_references),
        "required_validation_commands": len(playbook["required_validation_commands"]),
        "review_sections": len(playbook["review_sections"]),
        "rollback_boundary_records": len(playbook["rollback_boundary_records"]),
        "rollback_boundary_records_pending_operator_review": sum(
            1
            for item in playbook["rollback_boundary_records"]
            if item["operator_review_status"] == OPERATOR_REVIEW_STATUS
        ),
        "rollback_steps": len(playbook["rollback_steps"]),
        "rollback_steps_pending_operator_review": sum(
            1 for item in playbook["rollback_steps"] if item["operator_review_status"] == OPERATOR_REVIEW_STATUS
        ),
        "source_artifacts": len(playbook["source_artifacts"]),
        "validation_command_records": len(playbook["validation_command_records"]),
        "warnings": len(playbook["warnings"]),
    }


def test_fixture_references_only_expected_allowed_local_static_material() -> None:
    playbook = _load_playbook()
    references = set(_collect_values_for_key(playbook, "local_reference"))
    references.update(_collect_values_for_key(playbook, "local_evidence_reference"))
    references.update(_collect_values_for_key(playbook, "source_trigger_reference"))
    for item in _collect_values_for_key(playbook, "local_references"):
        references.add(item)

    assert sorted(references) == sorted(EXPECTED_LOCAL_REFERENCES)
    for reference in references:
        _assert_allowed_existing_local_reference(reference)


def test_fixture_has_no_decision_scoring_or_selection_terms() -> None:
    playbook = _load_playbook()

    assert _find_disallowed_terms(playbook) == []


def test_documentation_registers_failure_and_rollback_playbook_and_safety_boundary() -> None:
    document = DOC_PATH.read_text(encoding="utf-8")

    assert f"Task: `{TASK_ID}`" in document
    assert f"Playbook: `{PLAYBOOK_ID}`" in document
    assert f"Contract: `{CONTRACT_VERSION}`" in document
    assert f"Run mode: `{RUN_MODE}`" in document
    assert str(FIXTURE_PATH).replace("\\", "/") in document
    assert "No network calls." in document
    assert "No OpenRouter calls." in document
    assert "No Polymarket API calls." in document
    assert "No market recommendation, forecast scoring, action guidance, or selection advice." in document
    assert "No probability, EV, edge, or confidence scoring." in document
    assert "This playbook is not execution approval and is not runtime input." in document


def _load_playbook() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def _assert_allowed_existing_local_reference(local_reference: str) -> None:
    assert "://" not in local_reference
    assert local_reference.startswith(ALLOWED_LOCAL_PREFIXES)
    assert Path(local_reference).exists()


def _collect_values_for_key(value: object, key: str) -> list[str]:
    matches: list[str] = []
    if isinstance(value, dict):
        for nested_key, nested_value in value.items():
            if nested_key == key:
                if isinstance(nested_value, list):
                    matches.extend(str(item) for item in nested_value)
                elif key != "local_references":
                    matches.append(str(nested_value))
            matches.extend(_collect_values_for_key(nested_value, key))
    elif isinstance(value, list):
        for nested_value in value:
            matches.extend(_collect_values_for_key(nested_value, key))
    return matches


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
                "blocked_operations",
                "command_label",
                "local_evidence_reference",
                "local_reference",
                "local_references",
                "required_validation_commands",
                "source_task_id",
                "source_trigger_reference",
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
