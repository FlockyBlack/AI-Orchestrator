from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from pm_bot.paper_accounting.paper_accounting_ledger import (
    LEDGER_CONTRACT_VERSION,
    LEDGER_ROW_STATE,
    LOCAL_ONLY_SAFETY_BOUNDARIES,
    LOCAL_RUN_MODE,
    OPERATOR_REVIEW_STATUS,
    REQUEST_CONTRACT_VERSION,
    SAMPLE_LEDGER_PATH,
    PaperAccountingLedgerValidationError,
    build_operator_report,
    build_paper_accounting_ledger,
    load_accounting_request,
    main,
    validate_accounting_request,
    validate_paper_accounting_ledger,
)

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "paper_accounting"
VALID_REQUEST_PATH = FIXTURE_DIR / "paper_accounting_ledger_request.valid.json"


def test_valid_fixture_request_builds_paper_accounting_ledger() -> None:
    request = load_accounting_request(VALID_REQUEST_PATH)
    validation = validate_accounting_request(request)
    ledger = build_paper_accounting_ledger(request)

    assert validation.valid is True
    assert validation.errors == ()
    assert ledger["contract_version"] == LEDGER_CONTRACT_VERSION
    assert ledger["ledger_id"] == "paper_accounting_ledger_fixture_001"
    assert ledger["run_mode"] == LOCAL_RUN_MODE
    assert ledger["local_only"] is True
    assert ledger["operator_review_required"] is True
    assert ledger["operator_review"]["status"] == OPERATOR_REVIEW_STATUS
    assert ledger["summary_counts"] == {
        "accounting_entries": 3,
        "assets": 1,
        "source_artifacts": 1,
        "warnings": 0,
    }
    assert ledger["source_inventory"][0] == {
        "artifact_id": "paper_accounting_events_fixture_001",
        "artifact_label": "Static paper accounting event register",
        "artifact_loaded": True,
        "artifact_role": "paper_accounting_event_register",
        "entry_count": 3,
        "local_reference": "pm_bot/tests/fixtures/paper_accounting/paper_accounting_events.valid.json",
        "operator_review_status": OPERATOR_REVIEW_STATUS,
        "required_field_count": 3,
        "runner_state": LEDGER_ROW_STATE,
    }
    assert ledger["accounting_entries"][0] == {
        "asset_code": "USD",
        "entry_id": "paper_fixture_account_001.2026-05-09.opening_balance",
        "entry_type": "opening_balance",
        "event_id": "paper_event_001",
        "event_timestamp": "2026-05-09T12:00:00Z",
        "local_reference": "pm_bot/tests/fixtures/paper_accounting/paper_accounting_events.valid.json",
        "memo": "Opening paper balance recorded from static operator worksheet.",
        "operator_review_label": "Opening paper cash balance",
        "operator_review_status": OPERATOR_REVIEW_STATUS,
        "quantity_delta": "1000.00",
        "row_state": LEDGER_ROW_STATE,
        "source_artifact_id": "paper_accounting_events_fixture_001",
        "source_artifact_label": "Static paper accounting event register",
        "source_artifact_role": "paper_accounting_event_register",
    }
    assert ledger["balance_summary"] == [
        {
            "asset_code": "USD",
            "entry_count": 3,
            "net_quantity_delta": "992.50",
            "operator_review_status": OPERATOR_REVIEW_STATUS,
        }
    ]
    assert ledger["safety_boundaries"] == LOCAL_ONLY_SAFETY_BOUNDARIES


def test_paper_accounting_ledger_is_deterministic_for_same_request() -> None:
    request = load_accounting_request(VALID_REQUEST_PATH)

    first = build_paper_accounting_ledger(request)
    second = build_paper_accounting_ledger(deepcopy(request))

    assert first == second
    assert first["build_id"].startswith("paper_accounting_ledger_fixture_001-")
    assert len(first["build_id"]) == len("paper_accounting_ledger_fixture_001-") + 12


def test_static_sample_matches_builder_output() -> None:
    request = load_accounting_request(VALID_REQUEST_PATH)
    sample = json.loads(Path(SAMPLE_LEDGER_PATH).read_text(encoding="utf-8"))

    assert build_paper_accounting_ledger(request) == sample


def test_static_sample_validates_as_paper_accounting_ledger_artifact() -> None:
    sample = json.loads(Path(SAMPLE_LEDGER_PATH).read_text(encoding="utf-8"))

    validation = validate_paper_accounting_ledger(sample)

    assert validation.valid is True
    assert validation.errors == ()


def test_cli_writes_local_ledger_and_operator_report(tmp_path: Path) -> None:
    ledger_path = tmp_path / "paper_accounting_ledger.json"
    report_path = tmp_path / "paper_accounting_ledger.md"

    exit_code = main(
        [
            "--request",
            str(VALID_REQUEST_PATH),
            "--output-ledger",
            str(ledger_path),
            "--output-report",
            str(report_path),
        ]
    )

    assert exit_code == 0
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    report = report_path.read_text(encoding="utf-8")
    assert ledger["contract_version"] == LEDGER_CONTRACT_VERSION
    assert ledger["errors"] == []
    assert ledger["warnings"] == []
    assert "# PMBOT Paper Accounting Ledger" in report
    assert "paper_fixture_account_001.2026-05-09.opening_balance" in report
    assert "Makes no network, LLM, external market API, wallet, order, transaction endpoint, or runtime calls." in report
    assert "Descriptive paper accounting only" in report


def test_operator_report_is_deterministic() -> None:
    request = load_accounting_request(VALID_REQUEST_PATH)
    ledger = build_paper_accounting_ledger(request)

    first = build_operator_report(ledger)
    second = build_operator_report(deepcopy(ledger))

    assert first == second
    assert "Operator review: `pending_operator_review`" in first
    assert "Local fixture/static input only." in first


def test_request_rejects_network_like_source_reference() -> None:
    request = load_accounting_request(VALID_REQUEST_PATH)
    request["source_artifacts"][0]["local_reference"] = "https://example.invalid/paper-accounting.json"

    validation = validate_accounting_request(request)

    assert validation.valid is False
    assert any("local_reference must stay under paper accounting allowed local paths" in error for error in validation.errors)
    with pytest.raises(PaperAccountingLedgerValidationError):
        build_paper_accounting_ledger(request)


def test_request_rejects_reference_outside_allowed_local_paths() -> None:
    request = load_accounting_request(VALID_REQUEST_PATH)
    request["source_artifacts"][0]["local_reference"] = "pm_bot/wallet/paper_accounting.json"

    validation = validate_accounting_request(request)

    assert validation.valid is False
    assert any("local_reference must stay under paper accounting allowed local paths" in error for error in validation.errors)


def test_request_rejects_missing_event_reference() -> None:
    request = load_accounting_request(VALID_REQUEST_PATH)
    request["entry_specs"][0]["event_id"] = "missing_event"

    validation = validate_accounting_request(request)

    assert validation.valid is False
    assert any("event_id must reference an event in the local artifact" in error for error in validation.errors)
    with pytest.raises(PaperAccountingLedgerValidationError):
        build_paper_accounting_ledger(request)


def test_request_rejects_quantity_delta_drift_from_local_event() -> None:
    request = load_accounting_request(VALID_REQUEST_PATH)
    request["entry_specs"][1]["quantity_delta"] = "-10.00"

    validation = validate_accounting_request(request)

    assert validation.valid is False
    assert any("quantity_delta must match the local artifact event quantity_delta" in error for error in validation.errors)


def test_request_rejects_scoring_or_action_fields() -> None:
    request = load_accounting_request(VALID_REQUEST_PATH)
    request["entry_specs"][0]["forecast_score"] = "not allowed in local paper accounting ledgers"

    validation = validate_accounting_request(request)

    assert validation.valid is False
    assert any("forbidden scoring/action field detected" in error for error in validation.errors)


def test_ledger_artifact_validation_rejects_summary_and_balance_drift() -> None:
    request = load_accounting_request(VALID_REQUEST_PATH)
    ledger = build_paper_accounting_ledger(request)
    ledger["summary_counts"]["accounting_entries"] = 99
    ledger["balance_summary"][0]["net_quantity_delta"] = "1.00"

    validation = validate_paper_accounting_ledger(ledger)

    assert validation.valid is False
    assert any("summary_counts must match" in error for error in validation.errors)
    assert any("balance_summary must match" in error for error in validation.errors)


def test_ledger_artifact_validation_rejects_operator_review_bypass_state() -> None:
    request = load_accounting_request(VALID_REQUEST_PATH)
    ledger = build_paper_accounting_ledger(request)
    ledger["accounting_entries"][0]["operator_review_status"] = "accepted_without_review"

    validation = validate_paper_accounting_ledger(ledger)

    assert validation.valid is False
    assert any(
        "accounting_entries[0].operator_review_status must be pending_operator_review" in error
        for error in validation.errors
    )


def test_output_contract_has_no_scoring_or_selection_fields() -> None:
    request = load_accounting_request(VALID_REQUEST_PATH)
    ledger = build_paper_accounting_ledger(request)

    offending_paths = _find_output_decision_terms(ledger)

    assert offending_paths == []


def test_accounting_request_contract_version_is_explicit() -> None:
    request = load_accounting_request(VALID_REQUEST_PATH)

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
