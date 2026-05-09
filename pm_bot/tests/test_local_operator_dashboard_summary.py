from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from pm_bot.dashboard.local_operator_dashboard_summary import (
    DASHBOARD_CONTRACT_VERSION,
    LOCAL_ONLY_SAFETY_BOUNDARIES,
    LOCAL_RUN_MODE,
    OPERATOR_REVIEW_STATUS,
    REQUEST_CONTRACT_VERSION,
    SAMPLE_DASHBOARD_PATH,
    LocalOperatorDashboardValidationError,
    build_local_operator_dashboard_summary,
    build_operator_report,
    load_dashboard_request,
    main,
    validate_dashboard_request,
    validate_local_operator_dashboard_summary,
)

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "dashboard"
VALID_REQUEST_PATH = FIXTURE_DIR / "local_operator_dashboard_request.valid.json"


def test_valid_fixture_request_builds_local_dashboard_summary() -> None:
    request = load_dashboard_request(VALID_REQUEST_PATH)
    validation = validate_dashboard_request(request)
    dashboard = build_local_operator_dashboard_summary(request)

    assert validation.valid is True
    assert validation.errors == ()
    assert dashboard["contract_version"] == DASHBOARD_CONTRACT_VERSION
    assert dashboard["dashboard_id"] == "local_operator_dashboard_fixture_001"
    assert dashboard["run_mode"] == LOCAL_RUN_MODE
    assert dashboard["local_only"] is True
    assert dashboard["operator_review_required"] is True
    assert dashboard["operator_review"]["status"] == OPERATOR_REVIEW_STATUS
    assert dashboard["summary_counts"] == {
        "ledger_records": 3,
        "operator_review_pending_records": 9,
        "queue_records": 4,
        "validation_records": 2,
        "warnings": 0,
    }
    assert dashboard["queue_summary"][0] == {
        "local_reference": "tests/test_codex_queue_pmbot_templates.py",
        "notes": "Static queue coverage includes the dashboard summary task identifier.",
        "operator_review_status": OPERATOR_REVIEW_STATUS,
        "queue_bucket": "planned_template",
        "record_id": "queue.PMBOT-DASHBOARD-001-LOCAL-OPERATOR-DASHBOARD-SUMMARY",
        "runner_state": "ready_for_operator_review",
        "safety_class": "local_only_no_execution",
        "task_id": "PMBOT-DASHBOARD-001-LOCAL-OPERATOR-DASHBOARD-SUMMARY",
        "task_template": "local_operator_dashboard_summary",
        "task_title": "PMBOT local operator dashboard summary",
        "validation_profile": "pmbot_local_code_tests",
    }
    assert dashboard["ledger_summary"][2] == {
        "contract_version": "pmbot_paper_accounting_ledger.v1",
        "ledger_id": "paper_accounting_ledger_fixture_001",
        "ledger_type": "paper_accounting",
        "local_reference": "pm_bot/tests/fixtures/paper_accounting/paper_accounting_ledger_request.valid.json",
        "notes": "Static paper accounting ledger request fixture.",
        "operator_review_status": OPERATOR_REVIEW_STATUS,
        "record_count": 3,
        "record_id": "ledger.paper_accounting_ledger_fixture_001",
        "runner_state": "ready_for_operator_review",
        "summary_label": "Paper accounting entries",
    }
    assert dashboard["validation_status_summary"][0] == {
        "command_label": "python -m compileall pm_bot tests",
        "local_reference": "tests/test_codex_queue_pmbot_templates.py",
        "notes": "Acceptance command listed for operator-run validation.",
        "operator_review_status": OPERATOR_REVIEW_STATUS,
        "record_id": "validation.compileall.pm_bot.tests",
        "runner_state": "ready_for_operator_review",
        "status": "not_run_static_record",
        "validation_id": "compileall.pm_bot.tests",
    }
    assert dashboard["safety_boundaries"] == LOCAL_ONLY_SAFETY_BOUNDARIES


def test_dashboard_summary_is_deterministic_for_same_request() -> None:
    request = load_dashboard_request(VALID_REQUEST_PATH)

    first = build_local_operator_dashboard_summary(request)
    second = build_local_operator_dashboard_summary(deepcopy(request))

    assert first == second
    assert first["build_id"].startswith("local_operator_dashboard_fixture_001-")
    assert len(first["build_id"]) == len("local_operator_dashboard_fixture_001-") + 12


def test_static_sample_matches_builder_output() -> None:
    request = load_dashboard_request(VALID_REQUEST_PATH)
    sample = json.loads(Path(SAMPLE_DASHBOARD_PATH).read_text(encoding="utf-8"))

    assert build_local_operator_dashboard_summary(request) == sample


def test_static_sample_validates_as_dashboard_summary_artifact() -> None:
    sample = json.loads(Path(SAMPLE_DASHBOARD_PATH).read_text(encoding="utf-8"))

    validation = validate_local_operator_dashboard_summary(sample)

    assert validation.valid is True
    assert validation.errors == ()


def test_cli_writes_local_dashboard_summary_and_operator_report(tmp_path: Path) -> None:
    dashboard_path = tmp_path / "local_operator_dashboard_summary.json"
    report_path = tmp_path / "local_operator_dashboard_summary.md"

    exit_code = main(
        [
            "--request",
            str(VALID_REQUEST_PATH),
            "--output-dashboard",
            str(dashboard_path),
            "--output-report",
            str(report_path),
        ]
    )

    assert exit_code == 0
    dashboard = json.loads(dashboard_path.read_text(encoding="utf-8"))
    report = report_path.read_text(encoding="utf-8")
    assert dashboard["contract_version"] == DASHBOARD_CONTRACT_VERSION
    assert dashboard["errors"] == []
    assert dashboard["warnings"] == []
    assert "# PMBOT Local Operator Dashboard Summary" in report
    assert "PMBOT-DASHBOARD-001-LOCAL-OPERATOR-DASHBOARD-SUMMARY" in report
    assert "paper_accounting_ledger_fixture_001" in report
    assert "pytest pm_bot/tests tests/test_codex_queue_pmbot_templates.py" in report
    assert "Makes no network, LLM, external market API, wallet, order, transaction endpoint, runtime, browser, scheduler, or worker calls." in report


def test_operator_report_is_deterministic() -> None:
    request = load_dashboard_request(VALID_REQUEST_PATH)
    dashboard = build_local_operator_dashboard_summary(request)

    first = build_operator_report(dashboard)
    second = build_operator_report(deepcopy(dashboard))

    assert first == second
    assert "Operator review: `pending_operator_review`" in first
    assert "Descriptive dashboard status only" in first


def test_request_rejects_network_like_local_reference() -> None:
    request = load_dashboard_request(VALID_REQUEST_PATH)
    request["queue_records"][0]["local_reference"] = "https://example.invalid/dashboard.json"

    validation = validate_dashboard_request(request)

    assert validation.valid is False
    assert any("local_reference must be a local reference" in error for error in validation.errors)
    with pytest.raises(LocalOperatorDashboardValidationError):
        build_local_operator_dashboard_summary(request)


def test_request_rejects_reference_outside_allowed_local_paths() -> None:
    request = load_dashboard_request(VALID_REQUEST_PATH)
    request["ledger_records"][0]["local_reference"] = "pm_bot/llm/openrouter_dashboard_status.json"

    validation = validate_dashboard_request(request)

    assert validation.valid is False
    assert any("local_reference is outside the dashboard boundary" in error for error in validation.errors)


def test_request_rejects_scoring_or_advice_fields() -> None:
    request = load_dashboard_request(VALID_REQUEST_PATH)
    request["validation_records"][0]["forecast_score"] = "not allowed in local dashboard summaries"

    validation = validate_dashboard_request(request)

    assert validation.valid is False
    assert any("forbidden dashboard decision field detected" in error for error in validation.errors)


def test_dashboard_artifact_validation_rejects_summary_count_drift() -> None:
    request = load_dashboard_request(VALID_REQUEST_PATH)
    dashboard = build_local_operator_dashboard_summary(request)
    dashboard["summary_counts"]["queue_records"] = 99

    validation = validate_local_operator_dashboard_summary(dashboard)

    assert validation.valid is False
    assert any("summary_counts must match dashboard rows" in error for error in validation.errors)


def test_output_contract_has_no_scoring_or_selection_fields() -> None:
    request = load_dashboard_request(VALID_REQUEST_PATH)
    dashboard = build_local_operator_dashboard_summary(request)

    offending_paths = _find_output_decision_terms(dashboard)

    assert offending_paths == []


def test_dashboard_request_contract_version_is_explicit() -> None:
    request = load_dashboard_request(VALID_REQUEST_PATH)

    assert request["contract_version"] == REQUEST_CONTRACT_VERSION


def _find_output_decision_terms(value: object, path: str = "$") -> list[str]:
    forbidden_tokens = {
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
            if _has_token(str(key), forbidden_tokens):
                hits.append(key_path)
            hits.extend(_find_output_decision_terms(nested_value, key_path))
    elif isinstance(value, list):
        for index, nested_value in enumerate(value):
            hits.extend(_find_output_decision_terms(nested_value, f"{path}[{index}]"))
    elif isinstance(value, str) and _has_token(value, forbidden_tokens):
        hits.append(path)
    return hits


def _has_token(value: str, forbidden_tokens: set[str]) -> bool:
    normalized = "".join(character if character.isalnum() else "_" for character in value.lower())
    tokens = {token for token in normalized.split("_") if token}
    return bool(tokens & forbidden_tokens)
