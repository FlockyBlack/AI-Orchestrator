from __future__ import annotations

import json
from pathlib import Path


DOC_PATH = Path("docs/PMBOT_SAFETY_004_SENSITIVE_PATH_EXCLUSION_AUDIT_LOCAL_ONLY.md")
FIXTURE_PATH = Path("pm_bot/tests/fixtures/safety/sensitive_path_exclusion_audit.valid.json")
TASK_ID = "PMBOT-SAFETY-004-SENSITIVE-PATH-EXCLUSION-AUDIT-LOCAL-ONLY"
CONTRACT_VERSION = "pmbot_sensitive_path_exclusion_audit.v1"
RUN_MODE = "local_static_sensitive_path_exclusion_audit"
AUDIT_ID = "pmbot_sensitive_path_exclusion_audit_001"
AUDIT_NAME = "pmbot-sensitive-path-exclusion-audit"
OPERATOR_REVIEW_STATUS = "pending_operator_review"

EXPECTED_ALLOWED_PREFIXES = (
    "docs/",
    "pm_bot/tests/",
    "tests/",
)
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
    "queue_template_safety_contract",
    "ci_safe_validation_subset",
    "forbidden_action_scan",
    "static_audit_fixture",
)
EXPECTED_CHECK_IDS = (
    "allowed_path_scope",
    "excluded_path_registry",
    "environment_file_exclusion",
    "codex_metadata_exclusion",
    "execution_wiring_exclusion",
    "pmbot_sensitive_module_exclusion",
    "running_task_exclusion",
    "operator_review_boundary",
)
EXPECTED_SAFETY_BOUNDARIES = {
    "authenticated_endpoint_calls_allowed": False,
    "background_process_allowed": False,
    "browser_automation_allowed": False,
    "credential_or_secret_access_allowed": False,
    "execution_endpoint_calls_allowed": False,
    "external_service_calls_allowed": False,
    "llm_provider_calls_allowed": False,
    "local_fixtures_only": True,
    "market_api_calls_allowed": False,
    "market_instruction_fields_allowed": False,
    "network_calls_allowed": False,
    "operator_review_required": True,
    "order_or_trade_surface_changes_allowed": False,
    "paper_mode_only": True,
    "runtime_or_dispatcher_changes_allowed": False,
    "scheduler_or_worker_allowed": False,
    "sensitive_path_access_allowed": False,
    "timed_automation_allowed": False,
    "transaction_endpoint_calls_allowed": False,
    "wallet_or_signing_material_access_allowed": False,
}


def test_static_sensitive_path_exclusion_audit_fixture_has_expected_contract() -> None:
    audit = _load_audit()

    assert tuple(audit.keys()) == tuple(sorted(audit.keys()))
    assert audit["task_id"] == TASK_ID
    assert audit["audit_id"] == AUDIT_ID
    assert audit["audit_name"] == AUDIT_NAME
    assert audit["contract_version"] == CONTRACT_VERSION
    assert audit["run_mode"] == RUN_MODE
    assert audit["created_at"] == "2026-05-09T02:00:00Z"
    assert audit["local_only"] is True
    assert audit["operator_review_required"] is True
    assert audit["operator_review"]["status"] == OPERATOR_REVIEW_STATUS
    assert audit["operator_review"]["reviewed_at"] is None
    assert audit["operator_review"]["reviewed_by"] is None
    assert audit["errors"] == []
    assert audit["warnings"] == []


def test_allowed_and_excluded_prefixes_match_sensitive_path_audit_scope() -> None:
    audit = _load_audit()

    assert tuple(audit["allowed_path_prefixes"]) == EXPECTED_ALLOWED_PREFIXES
    assert tuple(audit["excluded_path_prefixes"]) == EXPECTED_EXCLUDED_PREFIXES
    for prefix in audit["excluded_path_prefixes"]:
        assert not prefix.startswith(EXPECTED_ALLOWED_PREFIXES)


def test_audit_inputs_are_fixed_local_allowed_references() -> None:
    audit = _load_audit()

    assert tuple(item["input_id"] for item in audit["audit_inputs"]) == EXPECTED_INPUT_IDS
    for item in audit["audit_inputs"]:
        assert set(item) == {
            "input_id",
            "local_reference",
            "observed_state",
            "operator_review_status",
        }
        assert item["operator_review_status"] == OPERATOR_REVIEW_STATUS
        _assert_allowed_existing_local_reference(item["local_reference"])


def test_audit_checks_are_fixed_local_and_pending_operator_review() -> None:
    audit = _load_audit()

    assert tuple(check["check_id"] for check in audit["audit_checks"]) == EXPECTED_CHECK_IDS
    for check in audit["audit_checks"]:
        assert set(check) == {
            "check_id",
            "expected_state",
            "local_reference",
            "operator_review_status",
            "review_label",
        }
        assert check["operator_review_status"] == OPERATOR_REVIEW_STATUS
        _assert_allowed_existing_local_reference(check["local_reference"])


def test_safety_boundaries_close_sensitive_path_exclusion_audit_surfaces() -> None:
    audit = _load_audit()

    assert audit["safety_boundaries"] == EXPECTED_SAFETY_BOUNDARIES
    assert audit["safety_boundaries"]["local_fixtures_only"] is True
    assert audit["safety_boundaries"]["operator_review_required"] is True
    assert audit["safety_boundaries"]["paper_mode_only"] is True
    assert all(value is False for key, value in audit["safety_boundaries"].items() if key.endswith("_allowed"))


def test_validation_commands_are_recorded_for_operator_run_local_checks() -> None:
    audit = _load_audit()

    assert audit["required_validation_commands"] == [
        "python -m compileall pm_bot tests",
        "pytest pm_bot/tests tests/test_codex_queue_pmbot_templates.py",
    ]


def test_summary_counts_match_sensitive_path_exclusion_audit_content() -> None:
    audit = _load_audit()
    local_references = {
        *(item["local_reference"] for item in audit["audit_inputs"]),
        *(check["local_reference"] for check in audit["audit_checks"]),
    }

    assert audit["summary_counts"] == {
        "allowed_path_prefixes": len(audit["allowed_path_prefixes"]),
        "audit_checks": len(audit["audit_checks"]),
        "audit_checks_pending_operator_review": sum(
            1 for check in audit["audit_checks"] if check["operator_review_status"] == OPERATOR_REVIEW_STATUS
        ),
        "audit_inputs": len(audit["audit_inputs"]),
        "errors": len(audit["errors"]),
        "excluded_path_prefixes": len(audit["excluded_path_prefixes"]),
        "local_references": len(local_references),
        "required_validation_commands": len(audit["required_validation_commands"]),
        "warnings": len(audit["warnings"]),
    }


def test_fixture_has_no_guidance_scoring_or_selection_terms() -> None:
    audit = _load_audit()

    assert _find_disallowed_terms(audit) == []


def test_documentation_registers_sensitive_path_exclusion_audit_and_safety_boundary() -> None:
    document = DOC_PATH.read_text(encoding="utf-8")

    assert f"Task: `{TASK_ID}`" in document
    assert f"Audit: `{AUDIT_NAME}`" in document
    assert f"Contract: `{CONTRACT_VERSION}`" in document
    assert f"Run mode: `{RUN_MODE}`" in document
    assert str(FIXTURE_PATH).replace("\\", "/") in document
    assert "No forecast scoring, action guidance, or selection advice." in document
    assert "This audit is not execution approval and is not runtime input." in document


def _load_audit() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def _assert_allowed_existing_local_reference(local_reference: str) -> None:
    assert "://" not in local_reference
    assert local_reference.startswith(EXPECTED_ALLOWED_PREFIXES)
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
            if key == "excluded_path_prefixes":
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
