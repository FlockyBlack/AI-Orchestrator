from __future__ import annotations

import json
from pathlib import Path

from pm_bot.tests.rehearsal_ci_safe_validation_runner import run_rehearsal_ci_safe_validation


DOC_PATH = Path("docs/PMBOT_REHEARSAL_010_REHEARSAL_CI_SAFE_VALIDATION_RUNNER_LOCAL_ONLY.md")
FIXTURE_PATH = Path("pm_bot/tests/fixtures/rehearsal/pmbot_rehearsal_ci_safe_validation_runner.valid.json")
RUNNER_PATH = Path("pm_bot/tests/rehearsal_ci_safe_validation_runner.py")

TASK_ID = "PMBOT-REHEARSAL-010-REHEARSAL-CI-SAFE-VALIDATION-RUNNER-LOCAL-ONLY"
CONTRACT_ID = "pmbot-rehearsal-ci-safe-validation-runner"
CONTRACT_VERSION = "pmbot_rehearsal_ci_safe_validation_runner.v1"
RUNNER_ID = "pmbot-rehearsal-ci-safe-validation-runner-001"
RUNNER_NAME = "pmbot-rehearsal-ci-safe-validation-runner"
RUN_MODE = "local_static_rehearsal_ci_safe_validation_runner"
OPERATOR_REVIEW_STATUS = "pending_operator_review"
ALLOWED_LOCAL_PREFIXES = ("docs/", "pm_bot/tests/", "tests/")

EXPECTED_TARGET_FIELDS = (
    "artifact_id",
    "artifact_role",
    "artifact_type",
    "contract_version",
    "expected_state",
    "local_reference",
    "operator_review_status",
    "runner_stage",
    "source_task_id",
    "target_id",
    "target_label",
)
EXPECTED_TARGET_IDS = (
    "rehearsal_ci_safe_validation_runner_001.runner_fixture",
    "rehearsal_ci_safe_validation_runner_001.runner_document",
    "rehearsal_ci_safe_validation_runner_001.runner_module",
    "rehearsal_ci_safe_validation_runner_001.runner_contract_test",
    "rehearsal_ci_safe_validation_runner_001.validation_replay_packet_document",
    "rehearsal_ci_safe_validation_runner_001.validation_replay_packet_fixture",
    "rehearsal_ci_safe_validation_runner_001.rehearsal_scenario_contract_fixture",
    "rehearsal_ci_safe_validation_runner_001.rehearsal_market_packet_fixture",
    "rehearsal_ci_safe_validation_runner_001.rehearsal_source_evidence_fixture",
    "rehearsal_ci_safe_validation_runner_001.rehearsal_operator_record_fixture",
    "rehearsal_ci_safe_validation_runner_001.rehearsal_stop_condition_fixture",
    "rehearsal_ci_safe_validation_runner_001.rehearsal_staleness_fixture",
    "rehearsal_ci_safe_validation_runner_001.rehearsal_contradiction_fixture",
    "rehearsal_ci_safe_validation_runner_001.rehearsal_retention_ledger_fixture",
    "rehearsal_ci_safe_validation_runner_001.validation_replay_packet_contract_test",
    "rehearsal_ci_safe_validation_runner_001.queue_template_validation_test",
)
EXPECTED_CHECK_IDS = (
    "local_reference_resolution",
    "prior_artifact_operator_review_state",
    "static_fixture_read",
    "validation_command_record",
    "closed_boundary_confirmation",
    "deterministic_output_confirmation",
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
    "credential_or_secret_access_allowed": False,
    "execution_endpoint_calls_allowed": False,
    "external_service_calls_allowed": False,
    "llm_provider_calls_allowed": False,
    "local_fixtures_only": True,
    "local_static_samples_only": True,
    "market_api_calls_allowed": False,
    "market_instruction_allowed": False,
    "market_ranking_allowed": False,
    "network_calls_allowed": False,
    "numeric_prediction_metric_allowed": False,
    "openrouter_calls_allowed": False,
    "operator_review_required": True,
    "order_or_trade_surface_changes_allowed": False,
    "paper_mode_only": True,
    "polymarket_api_calls_allowed": False,
    "run_codex_changes_allowed": False,
    "runner_executes_validation_commands_allowed": False,
    "runner_mutates_source_artifacts_allowed": False,
    "runtime_or_dispatcher_changes_allowed": False,
    "scheduler_or_worker_allowed": False,
    "sensitive_path_access_allowed": False,
    "timed_automation_allowed": False,
    "transaction_endpoint_calls_allowed": False,
    "wallet_or_signing_material_access_allowed": False,
}


def test_static_rehearsal_ci_safe_validation_runner_fixture_has_expected_contract() -> None:
    runner = _load_runner_fixture()

    assert tuple(runner.keys()) == tuple(sorted(runner.keys()))
    assert runner["task_id"] == TASK_ID
    assert runner["contract_id"] == CONTRACT_ID
    assert runner["contract_version"] == CONTRACT_VERSION
    assert runner["runner_id"] == RUNNER_ID
    assert runner["runner_name"] == RUNNER_NAME
    assert runner["run_mode"] == RUN_MODE
    assert runner["created_at"] == "2026-05-09T06:30:00Z"
    assert runner["local_only"] is True
    assert runner["operator_review_required"] is True
    assert runner["operator_review"] == {
        "reviewed_at": None,
        "reviewed_by": None,
        "status": OPERATOR_REVIEW_STATUS,
    }
    assert runner["errors"] == []
    assert runner["warnings"] == []


def test_runner_targets_are_fixed_local_allowed_paths() -> None:
    runner = _load_runner_fixture()

    assert tuple(target["target_id"] for target in runner["runner_targets"]) == EXPECTED_TARGET_IDS
    for target in runner["runner_targets"]:
        assert tuple(target.keys()) == EXPECTED_TARGET_FIELDS
        assert target["operator_review_status"] == OPERATOR_REVIEW_STATUS
        assert target["expected_state"] in {"local_validation_reference", OPERATOR_REVIEW_STATUS}
        assert target["source_task_id"]
        _assert_allowed_existing_local_reference(target["local_reference"])


def test_runner_checklist_and_validation_command_records_are_pending_review() -> None:
    runner = _load_runner_fixture()

    assert tuple(check["check_id"] for check in runner["runner_checklist"]) == EXPECTED_CHECK_IDS
    for check in runner["runner_checklist"]:
        assert tuple(check.keys()) == tuple(sorted(check.keys()))
        assert set(check) == {"check_id", "description", "required_evidence", "status"}
        assert check["status"] == OPERATOR_REVIEW_STATUS

    assert runner["required_validation_commands"] == [
        "python -m compileall pm_bot tests",
        "pytest pm_bot/tests tests/test_codex_queue_pmbot_templates.py",
    ]
    assert [record["command_label"] for record in runner["validation_command_records"]] == runner[
        "required_validation_commands"
    ]
    for record in runner["validation_command_records"]:
        assert tuple(record.keys()) == tuple(sorted(record.keys()))
        assert set(record) == {
            "command_label",
            "local_reference",
            "operator_review_status",
            "record_id",
            "status",
        }
        assert record["operator_review_status"] == OPERATOR_REVIEW_STATUS
        assert record["status"] == "not_run_static_record"
        _assert_allowed_existing_local_reference(record["local_reference"])


def test_prior_rehearsal_fixture_review_states_remain_pending() -> None:
    runner = _load_runner_fixture()

    fixture_references = sorted(
        {
            target["local_reference"]
            for target in runner["runner_targets"]
            if target["artifact_type"] == "json_fixture"
        }
    )
    assert len(fixture_references) == 10
    for reference in fixture_references:
        fixture = _load_json(Path(reference))
        assert fixture["operator_review"] == {
            "reviewed_at": None,
            "reviewed_by": None,
            "status": OPERATOR_REVIEW_STATUS,
        }


def test_safety_boundaries_are_closed_for_rehearsal_ci_safe_runner() -> None:
    runner = _load_runner_fixture()

    assert runner["safety_boundaries"] == EXPECTED_SAFETY_BOUNDARIES
    assert runner["safety_boundaries"]["local_fixtures_only"] is True
    assert runner["safety_boundaries"]["local_static_samples_only"] is True
    assert runner["safety_boundaries"]["operator_review_required"] is True
    assert runner["safety_boundaries"]["paper_mode_only"] is True
    assert all(value is False for key, value in runner["safety_boundaries"].items() if key.endswith("_allowed"))


def test_excluded_prefixes_match_sensitive_and_execution_boundaries() -> None:
    runner = _load_runner_fixture()

    assert tuple(runner["excluded_path_prefixes"]) == EXPECTED_EXCLUDED_PREFIXES


def test_summary_counts_match_rehearsal_ci_safe_runner_content() -> None:
    runner = _load_runner_fixture()
    local_references = {target["local_reference"] for target in runner["runner_targets"]}
    local_references.update(record["local_reference"] for record in runner["validation_command_records"])

    assert runner["summary_counts"] == {
        "errors": len(runner["errors"]),
        "excluded_path_prefixes": len(runner["excluded_path_prefixes"]),
        "local_references": len(local_references),
        "required_validation_commands": len(runner["required_validation_commands"]),
        "runner_checklist_items": len(runner["runner_checklist"]),
        "runner_targets": len(runner["runner_targets"]),
        "runner_targets_pending_operator_review": sum(
            1 for target in runner["runner_targets"] if target["operator_review_status"] == OPERATOR_REVIEW_STATUS
        ),
        "validation_command_records": len(runner["validation_command_records"]),
        "warnings": len(runner["warnings"]),
    }


def test_runner_output_is_deterministic_and_local_review_only() -> None:
    first = run_rehearsal_ci_safe_validation(Path("."))
    second = run_rehearsal_ci_safe_validation(Path("."))

    assert first == second
    assert first["task_id"] == TASK_ID
    assert first["contract_id"] == CONTRACT_ID
    assert first["contract_version"] == CONTRACT_VERSION
    assert first["runner_id"] == RUNNER_ID
    assert first["run_mode"] == RUN_MODE
    assert first["operator_review"]["status"] == OPERATOR_REVIEW_STATUS
    assert first["errors"] == []
    assert first["warnings"] == []
    assert tuple(check["check_id"] for check in first["checks"]) == (
        "local_reference_resolution",
        "prior_artifact_operator_review_state",
        "validation_command_record_consistency",
        "closed_safety_boundary_confirmation",
        "human_review_boundary_confirmation",
    )
    assert all(check["status"] == "passed" for check in first["checks"])
    assert first["summary_counts"] == {
        "checks": 5,
        "checks_passed": 5,
        "errors": 0,
        "runner_targets": 16,
        "validation_command_records": 2,
        "warnings": 0,
    }


def test_runner_module_avoids_network_subprocess_and_external_service_terms() -> None:
    source = RUNNER_PATH.read_text(encoding="utf-8").lower()

    for forbidden_snippet in (
        "requests",
        "urllib",
        "httpx",
        "socket",
        "subprocess",
        "webbrowser",
        "openrouter",
        "polymarket",
    ):
        assert forbidden_snippet not in source


def test_fixture_and_runner_output_have_no_decision_scoring_or_selection_terms() -> None:
    runner = _load_runner_fixture()
    output = run_rehearsal_ci_safe_validation(Path("."))

    assert _find_disallowed_terms(runner) == []
    assert _find_disallowed_terms(output) == []


def test_documentation_registers_rehearsal_ci_safe_runner_and_safety_boundary() -> None:
    document = DOC_PATH.read_text(encoding="utf-8")

    assert f"Task: `{TASK_ID}`" in document
    assert f"Runner: `{RUNNER_ID}`" in document
    assert f"Contract: `{CONTRACT_VERSION}`" in document
    assert f"Run mode: `{RUN_MODE}`" in document
    assert str(FIXTURE_PATH).replace("\\", "/") in document
    assert str(RUNNER_PATH).replace("\\", "/") in document
    assert "No validation command subprocess execution by this runner." in document
    assert "No market recommendation, forecast scoring, action guidance, or selection advice." in document
    assert "No probability, EV, edge, or confidence scoring." in document
    assert "This runner is not execution approval and is not runtime input." in document


def _load_runner_fixture() -> dict:
    return _load_json(FIXTURE_PATH)


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


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
                "excluded_path_prefixes",
                "local_reference",
                "required_validation_commands",
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
