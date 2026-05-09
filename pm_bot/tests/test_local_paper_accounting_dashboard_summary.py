from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from pm_bot.dashboard.local_paper_accounting_dashboard_summary import (
    DASHBOARD_CONTRACT_VERSION,
    LOCAL_ONLY_SAFETY_BOUNDARIES,
    LOCAL_RUN_MODE,
    OPERATOR_REVIEW_STATUS,
    REQUEST_CONTRACT_VERSION,
    SAMPLE_DASHBOARD_PATH,
    SAMPLE_OPERATOR_REPORT_PATH,
    PaperAccountingDashboardValidationError,
    build_local_paper_accounting_dashboard_summary,
    build_operator_report,
    load_dashboard_request,
    main,
    validate_dashboard_request,
    validate_local_paper_accounting_dashboard_summary,
)

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "dashboard"
VALID_REQUEST_PATH = FIXTURE_DIR / "local_paper_accounting_dashboard_request.valid.json"
DOC_PATH = Path("docs/PMBOT_DASHBOARD_004_PAPER_ACCOUNTING_DASHBOARD_SUMMARY.md")
TASK_ID = "PMBOT-DASHBOARD-004-PAPER-ACCOUNTING-DASHBOARD-SUMMARY"


def test_valid_fixture_request_builds_paper_accounting_dashboard_summary() -> None:
    request = load_dashboard_request(VALID_REQUEST_PATH)
    validation = validate_dashboard_request(request)
    dashboard = build_local_paper_accounting_dashboard_summary(request)

    assert validation.valid is True
    assert validation.errors == ()
    assert dashboard["contract_version"] == DASHBOARD_CONTRACT_VERSION
    assert dashboard["dashboard_id"] == "local_paper_accounting_dashboard_fixture_001"
    assert dashboard["dashboard_label"] == "PMBOT local paper accounting dashboard"
    assert dashboard["run_mode"] == LOCAL_RUN_MODE
    assert dashboard["local_only"] is True
    assert dashboard["operator_review_required"] is True
    assert dashboard["operator_review"]["status"] == OPERATOR_REVIEW_STATUS
    assert dashboard["summary_counts"] == {
        "balance_assets": 1,
        "failed_validation_checks": 0,
        "input_artifacts": 2,
        "ledger_accounting_entries": 3,
        "operator_review_pending_records": 10,
        "paper_accounting_artifacts": 3,
        "queue_records": 4,
        "reported_source_artifacts": 3,
        "session_rows": 3,
        "validation_checks": 18,
        "validation_records": 2,
        "validation_rows": 6,
        "warnings": 0,
    }
    assert dashboard["queue_summary"][0] == {
        "local_reference": "docs/PMBOT_DASHBOARD_004_PAPER_ACCOUNTING_DASHBOARD_SUMMARY.md",
        "notes": "Static queue coverage includes the paper accounting dashboard summary task identifier.",
        "operator_review_status": OPERATOR_REVIEW_STATUS,
        "queue_group": "next_twenty_template",
        "record_id": f"queue_paper_accounting.{TASK_ID}",
        "runner_state": "ready_for_operator_review",
        "safety_class": "local_only_no_execution",
        "status_label": "template_listed_static_record",
        "task_id": TASK_ID,
        "task_template": "paper_accounting_dashboard_summary",
        "task_title": "PMBOT paper accounting dashboard summary",
        "validation_profile": "pmbot_local_code_tests",
    }
    assert dashboard["paper_accounting_summary"][2] == {
        "artifact_id": "paper_accounting_ledger_fixture_001.paper_accounting_session_summary",
        "artifact_label": "Paper accounting session summary",
        "artifact_type": "paper_accounting_session_summary",
        "balance_assets": 1,
        "contract_version": "pmbot_paper_accounting_session_summary.v1",
        "failed_validation_checks": 0,
        "input_artifacts": 2,
        "ledger_accounting_entries": 0,
        "local_reference": "docs/PMBOT_PAPER_ACCOUNTING_003_PAPER_ONLY_SESSION_SUMMARY_LOCAL_ONLY.md",
        "notes": "Static session summary sample joins the local ledger and validation artifacts for operator review.",
        "operator_review_status": OPERATOR_REVIEW_STATUS,
        "record_id": "paper_accounting_dashboard.paper_accounting_ledger_fixture_001.paper_accounting_session_summary",
        "run_mode": "local_paper_only_session_summary",
        "runner_state": "ready_for_operator_review",
        "sample_reference": "pm_bot/paper_accounting/samples/paper_accounting_session_summary.fixture.json",
        "scope": "paper_accounting_session_summary",
        "session_rows": 3,
        "source_artifacts": 1,
        "status_label": "static_paper_accounting_sample_ready",
        "validation_checks": 0,
        "validation_rows": 3,
        "warning_count": 0,
    }
    assert dashboard["balance_summary"][0] == {
        "asset_code": "USD",
        "entry_count": 3,
        "local_reference": "pm_bot/paper_accounting/samples/paper_accounting_ledger.fixture.json",
        "net_quantity_delta": "992.50",
        "notes": "Static balance total copied from the local paper accounting ledger sample.",
        "operator_review_status": OPERATOR_REVIEW_STATUS,
        "record_id": "paper_accounting_balance.USD",
        "runner_state": "ready_for_operator_review",
    }
    assert dashboard["validation_status_summary"][0]["command_label"] == "python -m compileall pm_bot tests"
    assert dashboard["safety_boundaries"] == LOCAL_ONLY_SAFETY_BOUNDARIES


def test_paper_accounting_dashboard_summary_is_deterministic_for_same_request() -> None:
    request = load_dashboard_request(VALID_REQUEST_PATH)

    first = build_local_paper_accounting_dashboard_summary(request)
    second = build_local_paper_accounting_dashboard_summary(deepcopy(request))

    assert first == second
    assert first["build_id"] == "local_paper_accounting_dashboard_fixture_001-9d977b7f5bc0"


def test_static_sample_matches_builder_output() -> None:
    request = load_dashboard_request(VALID_REQUEST_PATH)
    sample = _load_json(Path(SAMPLE_DASHBOARD_PATH))

    assert build_local_paper_accounting_dashboard_summary(request) == sample


def test_static_sample_validates_as_paper_accounting_dashboard_artifact() -> None:
    sample = _load_json(Path(SAMPLE_DASHBOARD_PATH))

    validation = validate_local_paper_accounting_dashboard_summary(sample)

    assert validation.valid is True
    assert validation.errors == ()


def test_static_markdown_sample_matches_report_builder_output() -> None:
    sample_dashboard = _load_json(Path(SAMPLE_DASHBOARD_PATH))
    sample_report = Path(SAMPLE_OPERATOR_REPORT_PATH).read_text(encoding="utf-8")

    assert build_operator_report(sample_dashboard) == sample_report


def test_cli_writes_local_paper_accounting_dashboard_summary_and_operator_report(tmp_path: Path) -> None:
    dashboard_path = tmp_path / "local_paper_accounting_dashboard_summary.json"
    report_path = tmp_path / "local_paper_accounting_dashboard_summary.md"

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

    dashboard = _load_json(dashboard_path)
    report = report_path.read_text(encoding="utf-8")
    assert exit_code == 0
    assert dashboard == _load_json(Path(SAMPLE_DASHBOARD_PATH))
    assert dashboard["errors"] == []
    assert dashboard["warnings"] == []
    assert "# PMBOT Paper Accounting Dashboard Summary" in report
    assert TASK_ID in report
    assert "paper_accounting_ledger_fixture_001.paper_accounting_session_summary" in report
    assert "pytest pm_bot/tests tests/test_codex_queue_pmbot_templates.py" in report
    assert "Descriptive paper accounting dashboard only" in report


def test_operator_report_is_deterministic() -> None:
    request = load_dashboard_request(VALID_REQUEST_PATH)
    dashboard = build_local_paper_accounting_dashboard_summary(request)

    first = build_operator_report(dashboard)
    second = build_operator_report(deepcopy(dashboard))

    assert first == second
    assert "Operator review: `pending_operator_review`" in first
    assert "Ledger accounting entries: 3" in first


def test_request_rejects_network_like_local_reference() -> None:
    request = load_dashboard_request(VALID_REQUEST_PATH)
    request["paper_accounting_records"][0]["sample_reference"] = "https://example.invalid/static.json"

    validation = validate_dashboard_request(request)

    assert validation.valid is False
    assert any("sample_reference must be a local reference" in error for error in validation.errors)
    with pytest.raises(PaperAccountingDashboardValidationError):
        build_local_paper_accounting_dashboard_summary(request)


def test_request_rejects_reference_outside_allowed_local_paths() -> None:
    request = load_dashboard_request(VALID_REQUEST_PATH)
    request["queue_records"][0]["local_reference"] = "pm_bot/wallet/paper_accounting_dashboard.json"

    validation = validate_dashboard_request(request)

    assert validation.valid is False
    assert any("local_reference is outside the paper accounting dashboard boundary" in error for error in validation.errors)


def test_request_rejects_scoring_or_selection_fields() -> None:
    request = load_dashboard_request(VALID_REQUEST_PATH)
    request["paper_accounting_records"][0]["forecast_score"] = "not allowed in local dashboard summaries"

    validation = validate_dashboard_request(request)

    assert validation.valid is False
    assert any("forbidden paper accounting dashboard decision field detected" in error for error in validation.errors)


def test_paper_accounting_dashboard_rejects_summary_count_drift() -> None:
    request = load_dashboard_request(VALID_REQUEST_PATH)
    dashboard = build_local_paper_accounting_dashboard_summary(request)
    dashboard["summary_counts"]["ledger_accounting_entries"] = 99

    validation = validate_local_paper_accounting_dashboard_summary(dashboard)

    assert validation.valid is False
    assert any("summary_counts must match paper accounting dashboard rows" in error for error in validation.errors)


def test_paper_accounting_dashboard_rejects_invalid_balance_quantity() -> None:
    request = load_dashboard_request(VALID_REQUEST_PATH)
    dashboard = build_local_paper_accounting_dashboard_summary(request)
    dashboard["balance_summary"][0]["net_quantity_delta"] = "not-a-decimal"

    validation = validate_local_paper_accounting_dashboard_summary(dashboard)

    assert validation.valid is False
    assert any("net_quantity_delta must be a decimal string" in error for error in validation.errors)


def test_output_contract_has_no_scoring_or_selection_fields() -> None:
    request = load_dashboard_request(VALID_REQUEST_PATH)
    dashboard = build_local_paper_accounting_dashboard_summary(request)

    offending_paths = _find_output_decision_terms(dashboard)

    assert offending_paths == []


def test_paper_accounting_dashboard_request_contract_version_is_explicit() -> None:
    request = load_dashboard_request(VALID_REQUEST_PATH)

    assert request["contract_version"] == REQUEST_CONTRACT_VERSION


def test_documentation_registers_dashboard_contract_fixtures_and_safety_boundary() -> None:
    document = DOC_PATH.read_text(encoding="utf-8")

    assert f"Task: `{TASK_ID}`" in document
    assert f"Contract: `{DASHBOARD_CONTRACT_VERSION}`" in document
    assert "pm_bot/dashboard/samples/local_paper_accounting_dashboard_summary.fixture.json" in document
    assert "pm_bot/tests/fixtures/dashboard/local_paper_accounting_dashboard_request.valid.json" in document
    assert "No forecast scoring, action guidance, or selection advice." in document
    assert "This dashboard summary is not execution approval and is not runtime input." in document


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


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
