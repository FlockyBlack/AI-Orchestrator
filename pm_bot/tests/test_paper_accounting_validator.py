from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from pm_bot.paper_accounting.paper_accounting_validator import (
    SAMPLE_LEDGER_PATH,
    SAMPLE_OPERATOR_REPORT_PATH,
    SAMPLE_VALIDATION_PATH,
    VALIDATION_CHECK_IDS,
    VALIDATION_CONTRACT_VERSION,
    VALIDATION_ROW_STATE,
    VALIDATION_RUN_MODE,
    PaperAccountingValidationError,
    build_operator_report,
    build_paper_accounting_validation,
    load_paper_accounting_ledger,
    main,
    validate_paper_accounting_records,
    validate_paper_accounting_validation,
)


def test_static_ledger_builds_paper_accounting_validation_artifact() -> None:
    ledger = load_paper_accounting_ledger(SAMPLE_LEDGER_PATH)
    artifact = build_paper_accounting_validation(ledger)

    assert artifact["contract_version"] == VALIDATION_CONTRACT_VERSION
    assert artifact["validation_id"] == "paper_accounting_ledger_fixture_001.paper_accounting_validation"
    assert artifact["build_id"] == "paper_accounting_ledger_fixture_001-02801beecc93.paper_accounting_validation"
    assert artifact["run_mode"] == VALIDATION_RUN_MODE
    assert artifact["local_only"] is True
    assert artifact["operator_review_required"] is True
    assert artifact["operator_review"]["status"] == "pending_operator_review"
    assert artifact["summary_counts"] == {
        "accounting_entries": 3,
        "failed_checks": 0,
        "source_artifacts": 1,
        "validation_checks": 18,
        "validation_rows": 3,
        "warnings": 0,
    }
    assert artifact["record_validation_rows"][0] == {
        "asset_code": "USD",
        "check_count": 6,
        "checks": [
            {
                "check_id": "required_fields_present",
                "observed_value": "14/14",
                "operator_review_status": "pending_operator_review",
                "status": "passed",
            },
            {
                "check_id": "local_reference_boundary",
                "observed_value": "pm_bot/tests/fixtures/paper_accounting/paper_accounting_events.valid.json",
                "operator_review_status": "pending_operator_review",
                "status": "passed",
            },
            {
                "check_id": "timestamp_utc_format",
                "observed_value": "2026-05-09T12:00:00Z",
                "operator_review_status": "pending_operator_review",
                "status": "passed",
            },
            {
                "check_id": "quantity_delta_canonical",
                "observed_value": "1000.00",
                "operator_review_status": "pending_operator_review",
                "status": "passed",
            },
            {
                "check_id": "operator_review_state",
                "observed_value": "pending_operator_review|descriptive_paper_accounting_record",
                "operator_review_status": "pending_operator_review",
                "status": "passed",
            },
            {
                "check_id": "source_inventory_reference",
                "observed_value": "paper_accounting_events_fixture_001",
                "operator_review_status": "pending_operator_review",
                "status": "passed",
            },
        ],
        "entry_id": "paper_fixture_account_001.2026-05-09.opening_balance",
        "entry_type": "opening_balance",
        "event_id": "paper_event_001",
        "event_timestamp": "2026-05-09T12:00:00Z",
        "failed_check_count": 0,
        "local_reference": "pm_bot/tests/fixtures/paper_accounting/paper_accounting_events.valid.json",
        "operator_review_status": "pending_operator_review",
        "quantity_delta": "1000.00",
        "runner_state": VALIDATION_ROW_STATE,
        "source_artifact_id": "paper_accounting_events_fixture_001",
        "status": "passed",
        "validation_row_id": "paper_fixture_account_001.2026-05-09.opening_balance.paper_accounting_validation",
    }


def test_paper_accounting_validation_is_deterministic_for_same_ledger() -> None:
    ledger = load_paper_accounting_ledger(SAMPLE_LEDGER_PATH)

    first = build_paper_accounting_validation(ledger)
    second = build_paper_accounting_validation(deepcopy(ledger))

    assert first == second
    assert first["build_id"] == "paper_accounting_ledger_fixture_001-02801beecc93.paper_accounting_validation"


def test_static_sample_matches_validation_builder_output() -> None:
    ledger = load_paper_accounting_ledger(SAMPLE_LEDGER_PATH)
    sample = _load_json(SAMPLE_VALIDATION_PATH)

    assert build_paper_accounting_validation(ledger) == sample


def test_static_sample_validates_as_paper_accounting_validation_artifact() -> None:
    sample = _load_json(SAMPLE_VALIDATION_PATH)

    validation = validate_paper_accounting_validation(sample)

    assert validation.valid is True
    assert validation.errors == ()


def test_static_markdown_sample_matches_report_builder_output() -> None:
    sample = _load_json(SAMPLE_VALIDATION_PATH)
    sample_report = Path(SAMPLE_OPERATOR_REPORT_PATH).read_text(encoding="utf-8")

    assert build_operator_report(sample) == sample_report


def test_cli_writes_local_validation_artifact_and_operator_report(tmp_path: Path) -> None:
    validation_path = tmp_path / "paper_accounting_validation.json"
    report_path = tmp_path / "paper_accounting_validation.md"

    exit_code = main(
        [
            "--ledger",
            str(SAMPLE_LEDGER_PATH),
            "--output-validation",
            str(validation_path),
            "--output-report",
            str(report_path),
        ]
    )

    artifact = _load_json(validation_path)
    report = report_path.read_text(encoding="utf-8")
    assert exit_code == 0
    assert artifact == _load_json(SAMPLE_VALIDATION_PATH)
    assert artifact["errors"] == []
    assert artifact["warnings"] == []
    assert "# PMBOT Paper Accounting Validation" in report
    assert "paper_accounting_ledger_fixture_001" in report
    assert "Descriptive paper accounting validation only" in report


def test_record_validation_rejects_duplicate_entry_id_and_noncanonical_quantity() -> None:
    ledger = load_paper_accounting_ledger(SAMPLE_LEDGER_PATH)
    ledger["accounting_entries"][1]["entry_id"] = ledger["accounting_entries"][0]["entry_id"]
    ledger["accounting_entries"][2]["quantity_delta"] = "5"

    validation = validate_paper_accounting_records(ledger)

    assert validation.valid is False
    assert any("entry_id must be unique" in error for error in validation.errors)
    assert any("quantity_delta must use canonical two-decimal formatting" in error for error in validation.errors)
    with pytest.raises(PaperAccountingValidationError):
        build_paper_accounting_validation(ledger)


def test_build_rejects_invalid_paper_accounting_ledger_artifact() -> None:
    ledger = load_paper_accounting_ledger(SAMPLE_LEDGER_PATH)
    ledger["summary_counts"]["accounting_entries"] = 99

    with pytest.raises(PaperAccountingValidationError):
        build_paper_accounting_validation(ledger)


def test_validation_artifact_rejects_check_order_status_and_summary_drift() -> None:
    sample = _load_json(SAMPLE_VALIDATION_PATH)
    sample["record_validation_rows"][0]["checks"][0]["check_id"] = "different_local_check"
    sample["record_validation_rows"][0]["checks"][1]["status"] = "needs_review"
    sample["summary_counts"]["validation_rows"] = 99

    validation = validate_paper_accounting_validation(sample)

    assert validation.valid is False
    assert any("checks must use the expected paper accounting validation check order" in error for error in validation.errors)
    assert any("checks[1].status must be passed" in error for error in validation.errors)
    assert any("summary_counts must match validation row totals" in error for error in validation.errors)


def test_validation_artifact_rejects_non_operator_review_state() -> None:
    sample = _load_json(SAMPLE_VALIDATION_PATH)
    sample["record_validation_rows"][0]["operator_review_status"] = "accepted_without_review"

    validation = validate_paper_accounting_validation(sample)

    assert validation.valid is False
    assert any(
        "record_validation_rows[0].operator_review_status must be pending_operator_review" in error
        for error in validation.errors
    )


def test_validation_artifact_rejects_reference_outside_allowed_paths() -> None:
    sample = _load_json(SAMPLE_VALIDATION_PATH)
    sample["record_validation_rows"][0]["local_reference"] = "pm_bot/wallet/paper_accounting_validation.json"

    validation = validate_paper_accounting_validation(sample)

    assert validation.valid is False
    assert any("local_reference must stay under paper accounting allowed local paths" in error for error in validation.errors)


def test_validation_output_contract_has_no_scoring_or_selection_fields() -> None:
    ledger = load_paper_accounting_ledger(SAMPLE_LEDGER_PATH)
    artifact = build_paper_accounting_validation(ledger)

    offending_paths = _find_output_decision_terms(artifact)

    assert offending_paths == []


def test_validation_check_ids_are_explicit_and_stable() -> None:
    assert VALIDATION_CHECK_IDS == (
        "required_fields_present",
        "local_reference_boundary",
        "timestamp_utc_format",
        "quantity_delta_canonical",
        "operator_review_state",
        "source_inventory_reference",
    )


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
