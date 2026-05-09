from __future__ import annotations

import json
from pathlib import Path


DOC_PATH = Path("docs/PMBOT_VALIDATION_002_CI_SAFE_VALIDATION_SUBSET_LOCAL_ONLY.md")
FIXTURE_PATH = Path("pm_bot/tests/fixtures/validation/pmbot_ci_safe_validation_subset.valid.json")
TASK_ID = "PMBOT-VALIDATION-002-CI-SAFE-VALIDATION-SUBSET-LOCAL-ONLY"
CONTRACT_ID = "pmbot-ci-safe-validation-subset"
CONTRACT_VERSION = "pmbot_ci_safe_validation_subset.v1"
SUBSET_ID = "pmbot-ci-safe-validation-subset-001"
SUBSET_NAME = "pmbot-ci-safe-validation-subset"
RUN_MODE = "local_static_ci_safe_validation_subset"
OPERATOR_REVIEW_STATUS = "pending_operator_review"

EXPECTED_TARGET_IDS = (
    "ci_safe_validation_subset_001.fixture",
    "ci_safe_validation_subset_001.document",
    "ci_safe_validation_subset_001.contract_test",
    "ci_safe_validation_subset_001.saved_evidence_fixture",
    "ci_safe_validation_subset_001.saved_evidence_test",
    "ci_safe_validation_subset_001.safety_gate_test",
    "ci_safe_validation_subset_001.queue_template_test",
)
EXPECTED_CHECK_IDS = (
    "local_reference_scope",
    "static_fixture_scope",
    "validation_command_scope",
    "external_call_boundary",
    "sensitive_path_boundary",
    "execution_wiring_boundary",
    "human_review_boundary",
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
EXPECTED_SAFETY_BOUNDARIES = {
    "authenticated_endpoint_calls_allowed": False,
    "background_process_allowed": False,
    "browser_automation_allowed": False,
    "ci_subset_mutates_runtime_allowed": False,
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
ALLOWED_LOCAL_PREFIXES = ("docs/", "pm_bot/tests/", "tests/")


def test_static_ci_safe_validation_subset_fixture_has_expected_contract() -> None:
    subset = _load_subset()

    assert tuple(subset.keys()) == tuple(sorted(subset.keys()))
    assert subset["task_id"] == TASK_ID
    assert subset["subset_id"] == SUBSET_ID
    assert subset["subset_name"] == SUBSET_NAME
    assert subset["contract_id"] == CONTRACT_ID
    assert subset["contract_version"] == CONTRACT_VERSION
    assert subset["run_mode"] == RUN_MODE
    assert subset["created_at"] == "2026-05-09T01:00:00Z"
    assert subset["local_only"] is True
    assert subset["operator_review_required"] is True
    assert subset["operator_review"]["status"] == OPERATOR_REVIEW_STATUS
    assert subset["operator_review"]["reviewed_at"] is None
    assert subset["operator_review"]["reviewed_by"] is None
    assert subset["errors"] == []
    assert subset["warnings"] == []


def test_validation_targets_are_fixed_local_allowed_paths() -> None:
    subset = _load_subset()

    assert tuple(target["target_id"] for target in subset["validation_targets"]) == EXPECTED_TARGET_IDS
    for target in subset["validation_targets"]:
        assert tuple(target.keys()) == tuple(sorted(target.keys()))
        assert set(target) == {
            "artifact_role",
            "artifact_type",
            "expected_state",
            "local_reference",
            "operator_review_status",
            "target_id",
        }
        assert target["operator_review_status"] == OPERATOR_REVIEW_STATUS
        assert target["expected_state"] in {
            "local_validation_reference",
            "pending_operator_review",
        }
        _assert_allowed_existing_local_reference(target["local_reference"])


def test_subset_checks_are_fixed_local_and_pending_review() -> None:
    subset = _load_subset()

    assert tuple(check["check_id"] for check in subset["subset_checks"]) == EXPECTED_CHECK_IDS
    for check in subset["subset_checks"]:
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


def test_safety_boundaries_close_non_local_surfaces_for_ci_safe_subset() -> None:
    subset = _load_subset()

    assert subset["safety_boundaries"] == EXPECTED_SAFETY_BOUNDARIES
    assert subset["safety_boundaries"]["local_fixtures_only"] is True
    assert subset["safety_boundaries"]["operator_review_required"] is True
    assert subset["safety_boundaries"]["paper_mode_only"] is True
    assert all(value is False for key, value in subset["safety_boundaries"].items() if key.endswith("_allowed"))


def test_excluded_prefixes_match_sensitive_and_execution_boundaries() -> None:
    subset = _load_subset()

    assert tuple(subset["excluded_path_prefixes"]) == EXPECTED_EXCLUDED_PREFIXES


def test_required_validation_commands_are_recorded_for_operator_run_local_checks() -> None:
    subset = _load_subset()

    assert subset["required_validation_commands"] == [
        "python -m compileall pm_bot tests",
        "pytest pm_bot/tests tests/test_codex_queue_pmbot_templates.py",
    ]


def test_summary_counts_match_ci_safe_validation_subset_content() -> None:
    subset = _load_subset()
    local_references = {
        *(target["local_reference"] for target in subset["validation_targets"]),
        *(check["local_reference"] for check in subset["subset_checks"]),
    }

    assert subset["summary_counts"] == {
        "errors": len(subset["errors"]),
        "excluded_path_prefixes": len(subset["excluded_path_prefixes"]),
        "local_references": len(local_references),
        "required_validation_commands": len(subset["required_validation_commands"]),
        "subset_checks": len(subset["subset_checks"]),
        "subset_checks_pending_operator_review": sum(
            1 for check in subset["subset_checks"] if check["operator_review_status"] == OPERATOR_REVIEW_STATUS
        ),
        "validation_targets": len(subset["validation_targets"]),
        "warnings": len(subset["warnings"]),
    }


def test_fixture_has_no_decision_scoring_or_selection_terms() -> None:
    subset = _load_subset()

    assert _find_disallowed_terms(subset) == []


def test_documentation_registers_ci_safe_validation_subset_and_safety_boundary() -> None:
    document = DOC_PATH.read_text(encoding="utf-8")

    assert f"Task: `{TASK_ID}`" in document
    assert f"Subset: `{SUBSET_ID}`" in document
    assert f"Contract: `{CONTRACT_VERSION}`" in document
    assert f"Run mode: `{RUN_MODE}`" in document
    assert str(FIXTURE_PATH).replace("\\", "/") in document
    assert "No forecast scoring, action guidance, or selection advice." in document
    assert "This subset is not execution approval and is not runtime input." in document


def _load_subset() -> dict:
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
