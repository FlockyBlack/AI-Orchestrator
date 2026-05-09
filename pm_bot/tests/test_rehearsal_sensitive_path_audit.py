from __future__ import annotations

import json
from pathlib import Path


DOC_PATH = Path("docs/PMBOT_REHEARSAL_018_REHEARSAL_SENSITIVE_PATH_AUDIT_LOCAL_ONLY.md")
FIXTURE_PATH = Path("pm_bot/tests/fixtures/rehearsal/pmbot_rehearsal_sensitive_path_audit.valid.json")
TASK_ID = "PMBOT-REHEARSAL-018-REHEARSAL-SENSITIVE-PATH-AUDIT-LOCAL-ONLY"
CONTRACT_ID = "pmbot-rehearsal-sensitive-path-audit"
CONTRACT_VERSION = "pmbot_rehearsal_sensitive_path_audit.v1"
AUDIT_ID = "pmbot-rehearsal-sensitive-path-audit-001"
AUDIT_NAME = "pmbot-rehearsal-sensitive-path-audit"
RUN_MODE = "local_static_rehearsal_sensitive_path_audit"
OPERATOR_REVIEW_STATUS = "pending_operator_review"
ALLOWED_LOCAL_PREFIXES = ("docs/", "pm_bot/tests/", "tests/")

EXPECTED_EXCLUDED_PREFIXES = (
    ".env",
    ".env.*",
    ".git/",
    ".codex/",
    "runtime/",
    "dispatcher/",
    "run_codex/",
    "pm_bot/llm/",
    "pm_bot/wallet/",
    "pm_bot/trading/",
    "pm_bot/orders/",
    "agent_tasks/running/",
)
EXPECTED_INPUT_IDS = (
    "queue_template_rehearsal_task_contract",
    "prior_rehearsal_forbidden_action_scan_document",
    "prior_rehearsal_forbidden_action_scan_fixture",
    "prior_rehearsal_forbidden_action_scan_contract_test",
    "baseline_sensitive_path_exclusion_audit_document",
    "baseline_sensitive_path_exclusion_audit_fixture",
    "baseline_sensitive_path_exclusion_audit_contract_test",
    "rehearsal_sensitive_path_audit_fixture",
    "rehearsal_sensitive_path_audit_contract_test",
)
EXPECTED_SCOPE_RECORD_IDS = (
    "rehearsal_sensitive_path_audit_001.allowed_local_output_scope",
    "rehearsal_sensitive_path_audit_001.excluded_secret_and_metadata_prefixes",
    "rehearsal_sensitive_path_audit_001.excluded_execution_wiring_prefixes",
    "rehearsal_sensitive_path_audit_001.excluded_pmbot_sensitive_modules",
    "rehearsal_sensitive_path_audit_001.rehearsal_static_reference_scope",
    "rehearsal_sensitive_path_audit_001.operator_review_boundary",
)
EXPECTED_CHECK_IDS = (
    "allowed_output_scope",
    "excluded_prefix_registry",
    "environment_file_exclusion",
    "repository_metadata_exclusion",
    "execution_wiring_exclusion",
    "pmbot_llm_exclusion",
    "wallet_signing_exclusion",
    "order_trading_exclusion",
    "validation_command_scope",
    "operator_review_boundary",
)
EXPECTED_SOURCE_ARTIFACT_IDS = (
    "rehearsal_sensitive_path_audit_fixture",
    "rehearsal_sensitive_path_audit_document",
    "rehearsal_sensitive_path_audit_contract_test",
    "rehearsal_forbidden_action_scan_fixture",
    "rehearsal_forbidden_action_scan_document",
    "rehearsal_forbidden_action_scan_contract_test",
    "base_sensitive_path_exclusion_audit_fixture",
    "base_sensitive_path_exclusion_audit_document",
    "base_sensitive_path_exclusion_audit_contract_test",
    "queue_template_validation_test",
)
EXPECTED_SAFETY_BOUNDARIES = {
    "authenticated_endpoint_calls_allowed": False,
    "background_process_allowed": False,
    "browser_automation_allowed": False,
    "core_execution_wiring_changes_allowed": False,
    "credential_or_secret_access_allowed": False,
    "execution_endpoint_calls_allowed": False,
    "external_service_calls_allowed": False,
    "llm_provider_calls_allowed": False,
    "local_fixtures_only": True,
    "local_static_samples_only": True,
    "market_api_calls_allowed": False,
    "market_instruction_output_allowed": False,
    "market_ranking_allowed": False,
    "network_calls_allowed": False,
    "numeric_prediction_metric_allowed": False,
    "operator_review_required": True,
    "order_or_trade_surface_changes_allowed": False,
    "paper_mode_only": True,
    "polymarket_api_calls_allowed": False,
    "runtime_or_dispatcher_changes_allowed": False,
    "scheduler_or_worker_allowed": False,
    "sensitive_path_access_allowed": False,
    "sensitive_path_registry_static_only": True,
    "timed_automation_allowed": False,
    "trade_instruction_allowed": False,
    "transaction_endpoint_calls_allowed": False,
    "wallet_or_signing_material_access_allowed": False,
}


def test_static_rehearsal_sensitive_path_audit_fixture_has_expected_contract() -> None:
    audit = _load_audit()

    assert tuple(audit.keys()) == tuple(sorted(audit.keys()))
    assert audit["task_id"] == TASK_ID
    assert audit["audit_id"] == AUDIT_ID
    assert audit["audit_name"] == AUDIT_NAME
    assert audit["contract_id"] == CONTRACT_ID
    assert audit["contract_version"] == CONTRACT_VERSION
    assert audit["run_mode"] == RUN_MODE
    assert audit["created_at"] == "2026-05-09T11:30:00Z"
    assert audit["local_only"] is True
    assert audit["operator_review_required"] is True
    assert audit["operator_review"] == {
        "reviewed_at": None,
        "reviewed_by": None,
        "status": OPERATOR_REVIEW_STATUS,
    }
    assert audit["errors"] == []
    assert audit["warnings"] == []


def test_allowed_and_excluded_prefixes_match_rehearsal_sensitive_path_audit_scope() -> None:
    audit = _load_audit()

    assert tuple(audit["allowed_path_prefixes"]) == ALLOWED_LOCAL_PREFIXES
    assert tuple(audit["excluded_path_prefixes"]) == EXPECTED_EXCLUDED_PREFIXES
    for prefix in audit["excluded_path_prefixes"]:
        assert not prefix.startswith(ALLOWED_LOCAL_PREFIXES)


def test_audit_inputs_are_fixed_local_allowed_references() -> None:
    audit = _load_audit()

    assert tuple(item["input_id"] for item in audit["audit_inputs"]) == EXPECTED_INPUT_IDS
    for item in audit["audit_inputs"]:
        assert tuple(item.keys()) == (
            "input_id",
            "local_reference",
            "observed_state",
            "operator_review_status",
        )
        assert item["operator_review_status"] == OPERATOR_REVIEW_STATUS
        _assert_allowed_existing_local_reference(item["local_reference"])


def test_audit_scope_records_are_fixed_local_allowed_references() -> None:
    audit = _load_audit()

    assert tuple(record["record_id"] for record in audit["audit_scope_records"]) == EXPECTED_SCOPE_RECORD_IDS
    for record in audit["audit_scope_records"]:
        assert tuple(record.keys()) == (
            "local_reference",
            "operator_review_status",
            "record_id",
            "record_label",
            "record_type",
            "review_state",
            "source_task_id",
        )
        assert record["operator_review_status"] == OPERATOR_REVIEW_STATUS
        assert record["source_task_id"]
        assert record["record_type"] in {
            "allowed_path_scope",
            "excluded_path_scope",
            "local_reference_scope",
            "operator_review_scope",
        }
        _assert_allowed_existing_local_reference(record["local_reference"])


def test_audit_checks_are_fixed_local_and_pending_operator_review() -> None:
    audit = _load_audit()

    assert tuple(check["check_id"] for check in audit["audit_checks"]) == EXPECTED_CHECK_IDS
    for check in audit["audit_checks"]:
        assert tuple(check.keys()) == tuple(sorted(check.keys()))
        assert set(check) == {
            "check_id",
            "expected_state",
            "local_reference",
            "operator_review_status",
            "review_label",
        }
        assert check["operator_review_status"] == OPERATOR_REVIEW_STATUS
        _assert_allowed_existing_local_reference(check["local_reference"])


def test_source_artifacts_are_allowed_existing_local_references() -> None:
    audit = _load_audit()

    assert tuple(item["artifact_id"] for item in audit["source_artifacts"]) == EXPECTED_SOURCE_ARTIFACT_IDS
    for item in audit["source_artifacts"]:
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
    audit = _load_audit()

    assert audit["required_validation_commands"] == [
        "python -m compileall pm_bot tests",
        "pytest pm_bot/tests tests/test_codex_queue_pmbot_templates.py",
    ]
    assert [record["command_label"] for record in audit["validation_command_records"]] == audit[
        "required_validation_commands"
    ]
    for record in audit["validation_command_records"]:
        assert tuple(record.keys()) == tuple(sorted(record.keys()))
        assert record["operator_review_status"] == OPERATOR_REVIEW_STATUS
        assert record["status"] == "not_run_static_record"
        _assert_allowed_existing_local_reference(record["local_reference"])


def test_safety_boundaries_are_closed_for_rehearsal_sensitive_path_audit() -> None:
    audit = _load_audit()

    assert audit["safety_boundaries"] == EXPECTED_SAFETY_BOUNDARIES
    assert audit["safety_boundaries"]["local_fixtures_only"] is True
    assert audit["safety_boundaries"]["local_static_samples_only"] is True
    assert audit["safety_boundaries"]["operator_review_required"] is True
    assert audit["safety_boundaries"]["paper_mode_only"] is True
    assert audit["safety_boundaries"]["sensitive_path_registry_static_only"] is True
    assert all(value is False for key, value in audit["safety_boundaries"].items() if key.endswith("_allowed"))


def test_summary_counts_match_rehearsal_sensitive_path_audit_content() -> None:
    audit = _load_audit()
    local_references = set(_collect_values_for_key(audit, "local_reference"))

    assert audit["summary_counts"] == {
        "allowed_path_prefixes": len(audit["allowed_path_prefixes"]),
        "audit_checks": len(audit["audit_checks"]),
        "audit_checks_pending_operator_review": sum(
            1 for check in audit["audit_checks"] if check["operator_review_status"] == OPERATOR_REVIEW_STATUS
        ),
        "audit_inputs": len(audit["audit_inputs"]),
        "audit_scope_records": len(audit["audit_scope_records"]),
        "audit_scope_records_pending_operator_review": sum(
            1 for record in audit["audit_scope_records"] if record["operator_review_status"] == OPERATOR_REVIEW_STATUS
        ),
        "errors": len(audit["errors"]),
        "excluded_path_prefixes": len(audit["excluded_path_prefixes"]),
        "local_references": len(local_references),
        "required_validation_commands": len(audit["required_validation_commands"]),
        "source_artifacts": len(audit["source_artifacts"]),
        "validation_command_records": len(audit["validation_command_records"]),
        "warnings": len(audit["warnings"]),
    }


def test_fixture_references_only_allowed_local_static_material() -> None:
    audit = _load_audit()
    references = sorted(set(_collect_values_for_key(audit, "local_reference")))

    assert references == [
        "docs/PMBOT_REHEARSAL_017_REHEARSAL_FORBIDDEN_ACTION_SCAN_LOCAL_ONLY.md",
        "docs/PMBOT_REHEARSAL_018_REHEARSAL_SENSITIVE_PATH_AUDIT_LOCAL_ONLY.md",
        "docs/PMBOT_SAFETY_004_SENSITIVE_PATH_EXCLUSION_AUDIT_LOCAL_ONLY.md",
        "pm_bot/tests/fixtures/rehearsal/pmbot_rehearsal_forbidden_action_scan.valid.json",
        "pm_bot/tests/fixtures/rehearsal/pmbot_rehearsal_sensitive_path_audit.valid.json",
        "pm_bot/tests/fixtures/safety/sensitive_path_exclusion_audit.valid.json",
        "pm_bot/tests/test_rehearsal_forbidden_action_scan.py",
        "pm_bot/tests/test_rehearsal_sensitive_path_audit.py",
        "pm_bot/tests/test_sensitive_path_exclusion_audit.py",
        "tests/test_codex_queue_pmbot_templates.py",
    ]
    for reference in references:
        _assert_allowed_existing_local_reference(reference)


def test_fixture_has_no_decision_scoring_or_selection_terms() -> None:
    audit = _load_audit()

    assert _find_disallowed_terms(audit) == []


def test_documentation_registers_rehearsal_sensitive_path_audit_and_safety_boundary() -> None:
    document = DOC_PATH.read_text(encoding="utf-8")

    assert f"Task: `{TASK_ID}`" in document
    assert f"Audit: `{AUDIT_ID}`" in document
    assert f"Contract: `{CONTRACT_VERSION}`" in document
    assert f"Run mode: `{RUN_MODE}`" in document
    assert str(FIXTURE_PATH).replace("\\", "/") in document
    assert "No network calls." in document
    assert "No OpenRouter calls." in document
    assert "No Polymarket API calls." in document
    assert "No market recommendation, forecast scoring, action guidance, or selection advice." in document
    assert "No probability, EV, edge, or confidence scoring." in document
    assert "This audit is not execution approval and is not runtime input." in document


def _load_audit() -> dict:
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
            if key in {"command_label", "excluded_path_prefixes", "local_reference", "source_task_id"}:
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
