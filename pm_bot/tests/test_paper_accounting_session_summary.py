from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from pm_bot.paper_accounting.paper_accounting_session_summary import (
    SAMPLE_OPERATOR_REPORT_PATH,
    SAMPLE_SESSION_SUMMARY_PATH,
    SESSION_SUMMARY_CONTRACT_VERSION,
    SESSION_SUMMARY_ROW_STATE,
    SESSION_SUMMARY_RUN_MODE,
    PaperAccountingSessionSummaryError,
    build_operator_report,
    build_paper_accounting_session_summary,
    load_paper_accounting_artifact,
    main,
    validate_paper_accounting_session_inputs,
    validate_paper_accounting_session_summary,
)
from pm_bot.paper_accounting.paper_accounting_validator import SAMPLE_LEDGER_PATH, SAMPLE_VALIDATION_PATH


def test_static_ledger_and_validation_build_session_summary_artifact() -> None:
    ledger = load_paper_accounting_artifact(SAMPLE_LEDGER_PATH)
    validation_artifact = load_paper_accounting_artifact(SAMPLE_VALIDATION_PATH)
    summary = build_paper_accounting_session_summary(ledger, validation_artifact)

    assert summary["contract_version"] == SESSION_SUMMARY_CONTRACT_VERSION
    assert summary["session_id"] == "paper_accounting_ledger_fixture_001.paper_accounting_session_summary"
    assert summary["build_id"] == "paper_accounting_ledger_fixture_001-02801beecc93.paper_accounting_session_summary"
    assert summary["run_mode"] == SESSION_SUMMARY_RUN_MODE
    assert summary["local_only"] is True
    assert summary["operator_review_required"] is True
    assert summary["operator_review"]["status"] == "pending_operator_review"
    assert summary["summary_counts"] == {
        "accounting_entries": 3,
        "assets": 1,
        "failed_validation_checks": 0,
        "input_artifacts": 2,
        "source_artifacts": 1,
        "validation_rows": 3,
        "warnings": 0,
    }
    assert summary["local_input_artifacts"] == [
        {
            "artifact_id": "paper_accounting_ledger_fixture_001",
            "artifact_role": "paper_accounting_ledger",
            "build_id": "paper_accounting_ledger_fixture_001-02801beecc93",
            "contract_version": "pmbot_paper_accounting_ledger.v1",
            "local_reference": "pm_bot/paper_accounting/samples/paper_accounting_ledger.fixture.json",
            "operator_review_status": "pending_operator_review",
            "runner_state": SESSION_SUMMARY_ROW_STATE,
        },
        {
            "artifact_id": "paper_accounting_ledger_fixture_001.paper_accounting_validation",
            "artifact_role": "paper_accounting_validation",
            "build_id": "paper_accounting_ledger_fixture_001-02801beecc93.paper_accounting_validation",
            "contract_version": "pmbot_paper_accounting_validation.v1",
            "local_reference": "pm_bot/paper_accounting/samples/paper_accounting_validation.fixture.json",
            "operator_review_status": "pending_operator_review",
            "runner_state": SESSION_SUMMARY_ROW_STATE,
        },
    ]
    assert summary["session_review_rows"][0] == {
        "asset_code": "USD",
        "entry_id": "paper_fixture_account_001.2026-05-09.opening_balance",
        "entry_type": "opening_balance",
        "event_id": "paper_event_001",
        "event_timestamp": "2026-05-09T12:00:00Z",
        "ledger_quantity_delta": "1000.00",
        "local_reference": "pm_bot/tests/fixtures/paper_accounting/paper_accounting_events.valid.json",
        "operator_review_label": "Opening paper cash balance",
        "operator_review_status": "pending_operator_review",
        "runner_state": SESSION_SUMMARY_ROW_STATE,
        "source_artifact_id": "paper_accounting_events_fixture_001",
        "validation_check_count": 6,
        "validation_failed_check_count": 0,
        "validation_row_id": "paper_fixture_account_001.2026-05-09.opening_balance.paper_accounting_validation",
        "validation_status": "passed",
    }


def test_paper_accounting_session_summary_is_deterministic() -> None:
    ledger = load_paper_accounting_artifact(SAMPLE_LEDGER_PATH)
    validation_artifact = load_paper_accounting_artifact(SAMPLE_VALIDATION_PATH)

    first = build_paper_accounting_session_summary(ledger, validation_artifact)
    second = build_paper_accounting_session_summary(deepcopy(ledger), deepcopy(validation_artifact))

    assert first == second
    assert first["build_id"] == "paper_accounting_ledger_fixture_001-02801beecc93.paper_accounting_session_summary"


def test_static_sample_matches_session_summary_builder_output() -> None:
    ledger = load_paper_accounting_artifact(SAMPLE_LEDGER_PATH)
    validation_artifact = load_paper_accounting_artifact(SAMPLE_VALIDATION_PATH)
    sample = _load_json(SAMPLE_SESSION_SUMMARY_PATH)

    assert build_paper_accounting_session_summary(ledger, validation_artifact) == sample


def test_static_sample_validates_as_session_summary_artifact() -> None:
    sample = _load_json(SAMPLE_SESSION_SUMMARY_PATH)

    validation = validate_paper_accounting_session_summary(sample)

    assert validation.valid is True
    assert validation.errors == ()


def test_static_markdown_sample_matches_report_builder_output() -> None:
    sample = _load_json(SAMPLE_SESSION_SUMMARY_PATH)
    sample_report = Path(SAMPLE_OPERATOR_REPORT_PATH).read_text(encoding="utf-8")

    assert build_operator_report(sample) == sample_report


def test_cli_writes_local_session_summary_and_operator_report(tmp_path: Path) -> None:
    summary_path = tmp_path / "paper_accounting_session_summary.json"
    report_path = tmp_path / "paper_accounting_session_summary.md"

    exit_code = main(
        [
            "--ledger",
            str(SAMPLE_LEDGER_PATH),
            "--validation",
            str(SAMPLE_VALIDATION_PATH),
            "--output-summary",
            str(summary_path),
            "--output-report",
            str(report_path),
        ]
    )

    summary = _load_json(summary_path)
    report = report_path.read_text(encoding="utf-8")
    assert exit_code == 0
    assert summary == _load_json(SAMPLE_SESSION_SUMMARY_PATH)
    assert summary["errors"] == []
    assert summary["warnings"] == []
    assert "# PMBOT Paper Accounting Session Summary" in report
    assert "paper_accounting_ledger_fixture_001.paper_accounting_session_summary" in report
    assert "Descriptive paper accounting session summary only" in report


def test_session_input_validation_rejects_mismatched_validation_artifact() -> None:
    ledger = load_paper_accounting_artifact(SAMPLE_LEDGER_PATH)
    validation_artifact = load_paper_accounting_artifact(SAMPLE_VALIDATION_PATH)
    validation_artifact["ledger_build_id"] = "different-local-build"

    validation = validate_paper_accounting_session_inputs(ledger, validation_artifact)

    assert validation.valid is False
    assert any("validation.ledger_build_id must match ledger.build_id" in error for error in validation.errors)
    with pytest.raises(PaperAccountingSessionSummaryError):
        build_paper_accounting_session_summary(ledger, validation_artifact)


def test_session_summary_validation_rejects_summary_drift_and_non_review_state() -> None:
    sample = _load_json(SAMPLE_SESSION_SUMMARY_PATH)
    sample["summary_counts"]["accounting_entries"] = 99
    sample["session_review_rows"][0]["operator_review_status"] = "accepted_without_review"

    validation = validate_paper_accounting_session_summary(sample)

    assert validation.valid is False
    assert any("summary_counts must match session row totals" in error for error in validation.errors)
    assert any(
        "session_review_rows[0].operator_review_status must be pending_operator_review" in error
        for error in validation.errors
    )


def test_session_summary_rejects_reference_outside_allowed_paths() -> None:
    sample = _load_json(SAMPLE_SESSION_SUMMARY_PATH)
    sample["local_input_artifacts"][0]["local_reference"] = "pm_bot/wallet/paper_accounting_session_summary.json"

    validation = validate_paper_accounting_session_summary(sample)

    assert validation.valid is False
    assert any("local_reference must stay under paper accounting allowed local paths" in error for error in validation.errors)


def test_session_summary_output_contract_has_no_scoring_or_selection_fields() -> None:
    ledger = load_paper_accounting_artifact(SAMPLE_LEDGER_PATH)
    validation_artifact = load_paper_accounting_artifact(SAMPLE_VALIDATION_PATH)
    summary = build_paper_accounting_session_summary(ledger, validation_artifact)

    offending_paths = _find_output_decision_terms(summary)

    assert offending_paths == []


def _load_json(path: Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


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
