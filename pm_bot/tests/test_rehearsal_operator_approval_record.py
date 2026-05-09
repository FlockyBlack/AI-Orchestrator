from __future__ import annotations

import json
from pathlib import Path


DOC_PATH = Path("docs/PMBOT_REHEARSAL_004_REHEARSAL_OPERATOR_APPROVAL_RECORD_LOCAL_ONLY.md")
FIXTURE_PATH = Path("pm_bot/tests/fixtures/rehearsal/pmbot_rehearsal_operator_approval_record.valid.json")
TASK_ID = "PMBOT-REHEARSAL-004-REHEARSAL-OPERATOR-APPROVAL-RECORD-LOCAL-ONLY"
CONTRACT_ID = "pmbot-rehearsal-operator-approval-record"
CONTRACT_VERSION = "pmbot_rehearsal_operator_approval_record.v1"
APPROVAL_RECORD_ID = "pmbot-rehearsal-operator-approval-record-001"
RUN_MODE = "local_static_rehearsal_operator_approval_record"
OPERATOR_REVIEW_STATUS = "pending_operator_review"
ALLOWED_LOCAL_PREFIXES = ("docs/", "pm_bot/readiness/", "pm_bot/tests/", "tests/")

EXPECTED_APPROVAL_RECORD_FIELDS = (
    "approval_record_id",
    "approval_record_state",
    "approval_state",
    "control_boundary",
    "evidence_required",
    "local_reference",
    "operator_review_status",
    "required_prior_state",
    "transition_state",
)
EXPECTED_APPROVAL_RECORD_IDS = (
    "rehearsal_scenario_contract_review",
    "rehearsal_market_packet_schema_review",
    "rehearsal_source_evidence_bundle_review",
    "local_validation_review",
    "safety_boundary_review",
    "human_approval_record_completion",
)
EXPECTED_CHECK_IDS = (
    "local_reference_review",
    "prior_rehearsal_artifact_review",
    "approval_record_row_review",
    "operator_review_status_review",
    "validation_command_review",
    "sensitive_path_exclusion_check",
    "runtime_boundary_check",
    "endpoint_boundary_check",
    "output_boundary_check",
)
EXPECTED_SECTION_IDS = (
    "record_identity_review",
    "prior_rehearsal_artifacts_review",
    "safety_boundary_review",
    "operator_control_review",
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
    "rehearsal_004_operator_approval_record_test",
    "pmbot_queue_template_validation",
    "safety_forbidden_action_scan_doc",
    "safety_forbidden_language_regression_doc",
)
EXPECTED_LOCAL_REFERENCES = (
    "docs/PMBOT_REHEARSAL_001_READ_ONLY_REHEARSAL_SCENARIO_CONTRACT_LOCAL_ONLY.md",
    "docs/PMBOT_REHEARSAL_002_REHEARSAL_MARKET_PACKET_SCHEMA_LOCAL_ONLY.md",
    "docs/PMBOT_REHEARSAL_003_REHEARSAL_SOURCE_EVIDENCE_BUNDLE_LOCAL_ONLY.md",
    "docs/PMBOT_REHEARSAL_004_REHEARSAL_OPERATOR_APPROVAL_RECORD_LOCAL_ONLY.md",
    "docs/PMBOT_SAFETY_003_FORBIDDEN_ACTION_SCAN_LOCAL_ONLY.md",
    "docs/PMBOT_SAFETY_005_FORBIDDEN_LANGUAGE_REGRESSION_SUITE_LOCAL_ONLY.md",
    "pm_bot/tests/fixtures/rehearsal/pmbot_read_only_rehearsal_scenario_contract.valid.json",
    "pm_bot/tests/fixtures/rehearsal/pmbot_rehearsal_market_packet_schema.valid.json",
    "pm_bot/tests/fixtures/rehearsal/pmbot_rehearsal_operator_approval_record.valid.json",
    "pm_bot/tests/fixtures/rehearsal/pmbot_rehearsal_source_evidence_bundle.valid.json",
    "pm_bot/tests/test_read_only_rehearsal_scenario_contract.py",
    "pm_bot/tests/test_rehearsal_market_packet_schema.py",
    "pm_bot/tests/test_rehearsal_operator_approval_record.py",
    "pm_bot/tests/test_rehearsal_source_evidence_bundle.py",
    "tests/test_codex_queue_pmbot_templates.py",
)
EXPECTED_SAFETY_BOUNDARIES = {
    "authenticated_endpoint_calls_allowed": False,
    "background_process_allowed": False,
    "browser_automation_allowed": False,
    "credential_or_secret_access_allowed": False,
    "descriptive_rehearsal_operator_record_only": True,
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
    "operator_record_status_change_allowed": False,
    "operator_review_required": True,
    "order_or_trade_surface_changes_allowed": False,
    "paper_mode_only": True,
    "polymarket_api_calls_allowed": False,
    "resident_process_allowed": False,
    "run_codex_changes_allowed": False,
    "runtime_or_dispatcher_changes_allowed": False,
    "scheduler_or_worker_allowed": False,
    "supervised_live_transition_allowed": False,
    "trading_endpoint_calls_allowed": False,
    "transaction_endpoint_calls_allowed": False,
    "transition_without_record_allowed": False,
    "wallet_or_signing_material_access_allowed": False,
}


def test_static_rehearsal_operator_approval_record_fixture_has_expected_contract() -> None:
    record = _load_record()

    assert tuple(record.keys()) == tuple(sorted(record.keys()))
    assert record["task_id"] == TASK_ID
    assert record["approval_record_id"] == APPROVAL_RECORD_ID
    assert record["contract_id"] == CONTRACT_ID
    assert record["contract_version"] == CONTRACT_VERSION
    assert record["run_mode"] == RUN_MODE
    assert record["created_at"] == "2026-05-09T02:30:00Z"
    assert record["gate_result"] == "blocked_until_operator_record_complete"
    assert record["local_only"] is True
    assert record["operator_review_required"] is True
    assert record["operator_review"] == {
        "reviewed_at": None,
        "reviewed_by": None,
        "status": OPERATOR_REVIEW_STATUS,
    }
    assert record["errors"] == []
    assert record["warnings"] == []


def test_approval_records_are_fixed_local_pending_and_not_approved() -> None:
    record = _load_record()

    assert tuple(record["approval_record_fields"]) == EXPECTED_APPROVAL_RECORD_FIELDS
    assert tuple(row["approval_record_id"] for row in record["approval_records"]) == EXPECTED_APPROVAL_RECORD_IDS
    for row in record["approval_records"]:
        assert tuple(row.keys()) == EXPECTED_APPROVAL_RECORD_FIELDS
        assert row["approval_state"] == "not_approved"
        assert row["operator_review_status"] == OPERATOR_REVIEW_STATUS
        assert row["required_prior_state"] == OPERATOR_REVIEW_STATUS
        assert row["transition_state"] == "blocked_until_record_complete"
        _assert_allowed_existing_local_reference(row["local_reference"])


def test_source_artifacts_reference_only_local_review_material() -> None:
    record = _load_record()

    assert tuple(artifact["artifact_id"] for artifact in record["source_artifacts"]) == EXPECTED_SOURCE_ARTIFACT_IDS
    for artifact in record["source_artifacts"]:
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


def test_review_sections_checks_rules_and_validation_commands_are_fixed() -> None:
    record = _load_record()

    assert tuple(section["section_id"] for section in record["review_sections"]) == EXPECTED_SECTION_IDS
    for section in record["review_sections"]:
        assert tuple(section.keys()) == tuple(sorted(section.keys()))
        assert section["operator_review_status"] == OPERATOR_REVIEW_STATUS
        for local_reference in section["local_references"]:
            _assert_allowed_existing_local_reference(local_reference)

    assert tuple(check["check_id"] for check in record["operator_review_checklist"]) == EXPECTED_CHECK_IDS
    assert all(check["status"] == OPERATOR_REVIEW_STATUS for check in record["operator_review_checklist"])
    assert [rule["status"] for rule in record["record_rules"]] == ["active"] * 6
    assert [rule["rule_id"] for rule in record["record_rules"]] == [
        "local_static_inputs_only",
        "descriptive_control_only",
        "operator_review_status_preserved",
        "no_implicit_approval",
        "closed_endpoint_boundary",
        "closed_process_boundary",
    ]
    assert record["required_validation_commands"] == [
        "python -m compileall pm_bot tests",
        "pytest pm_bot/tests tests/test_codex_queue_pmbot_templates.py",
    ]


def test_safety_boundaries_are_closed_for_rehearsal_operator_approval_record() -> None:
    record = _load_record()

    assert record["safety_boundaries"] == EXPECTED_SAFETY_BOUNDARIES
    assert record["safety_boundaries"]["local_static_samples_only"] is True
    assert record["safety_boundaries"]["operator_review_required"] is True
    assert record["safety_boundaries"]["paper_mode_only"] is True
    assert all(value is False for key, value in record["safety_boundaries"].items() if key.endswith("_allowed"))


def test_summary_counts_match_rehearsal_operator_approval_record_content() -> None:
    record = _load_record()
    local_references = {
        *(row["local_reference"] for row in record["approval_records"]),
        *(artifact["local_reference"] for artifact in record["source_artifacts"]),
        *(reference for section in record["review_sections"] for reference in section["local_references"]),
    }

    assert record["summary_counts"] == {
        "approval_record_fields": len(record["approval_record_fields"]),
        "approval_records": len(record["approval_records"]),
        "approval_records_pending_operator_review": sum(
            1 for row in record["approval_records"] if row["operator_review_status"] == OPERATOR_REVIEW_STATUS
        ),
        "local_references": len(local_references),
        "operator_review_checklist_items": len(record["operator_review_checklist"]),
        "record_rules": len(record["record_rules"]),
        "required_validation_commands": len(record["required_validation_commands"]),
        "review_sections": len(record["review_sections"]),
        "source_artifacts": len(record["source_artifacts"]),
        "warnings": len(record["warnings"]),
    }


def test_rehearsal_operator_approval_record_references_only_expected_local_static_paths() -> None:
    record = _load_record()
    references = sorted(
        {
            *(row["local_reference"] for row in record["approval_records"]),
            *(artifact["local_reference"] for artifact in record["source_artifacts"]),
            *(reference for section in record["review_sections"] for reference in section["local_references"]),
        }
    )

    assert references == sorted(EXPECTED_LOCAL_REFERENCES)
    for reference in references:
        _assert_allowed_existing_local_reference(reference)


def test_fixture_has_no_decision_scoring_or_selection_terms() -> None:
    record = _load_record()

    assert _find_disallowed_terms(record) == []


def test_documentation_registers_rehearsal_operator_record_fixture_and_safety_boundary() -> None:
    document = DOC_PATH.read_text(encoding="utf-8")

    assert f"Task: `{TASK_ID}`" in document
    assert f"Record: `{APPROVAL_RECORD_ID}`" in document
    assert f"Contract: `{CONTRACT_VERSION}`" in document
    assert f"Run mode: `{RUN_MODE}`" in document
    assert "read-only rehearsal control" in document
    assert str(FIXTURE_PATH).replace("\\", "/") in document
    assert "No market recommendation, forecast scoring, action guidance, or selection advice." in document
    assert "No probability, EV, edge, or confidence scoring." in document
    assert "This record is not execution approval and is not runtime input." in document


def _load_record() -> dict:
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
            if key in {"local_reference", "local_references", "required_validation_commands"}:
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
