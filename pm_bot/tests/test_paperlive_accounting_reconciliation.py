from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from pm_bot.paper_accounting.paperlive_accounting_reconciliation import (
    LOCAL_ONLY_RECONCILIATION_SAFETY_BOUNDARIES,
    RECONCILIATION_CONTRACT_VERSION,
    RECONCILIATION_ROW_STATE,
    RECONCILIATION_RUN_MODE,
    SAMPLE_OPERATOR_REPORT_PATH,
    SAMPLE_RECONCILIATION_PATH,
    SAMPLE_REQUEST_PATH,
    PaperliveAccountingReconciliationError,
    build_operator_report,
    build_paperlive_accounting_reconciliation,
    load_reconciliation_artifact,
    main,
    validate_paperlive_accounting_reconciliation,
    validate_reconciliation_request,
)

DOC_PATH = Path("docs/PMBOT_PAPERLIVE_AUDIT_001_PAPERLIVE_TO_ACCOUNTING_RECONCILIATION_LOCAL_ONLY.md")
TASK_ID = "PMBOT-PAPERLIVE-AUDIT-001-PAPERLIVE-TO-ACCOUNTING-RECONCILIATION-LOCAL-ONLY"


def test_static_request_builds_paperlive_accounting_reconciliation() -> None:
    request = load_reconciliation_artifact(SAMPLE_REQUEST_PATH)
    reconciliation = build_paperlive_accounting_reconciliation(request)

    assert reconciliation["contract_version"] == RECONCILIATION_CONTRACT_VERSION
    assert reconciliation["reconciliation_id"] == "paperlive_accounting_reconciliation_fixture_001"
    assert reconciliation["build_id"] == "paperlive_accounting_reconciliation_fixture_001-e515f0da1873"
    assert reconciliation["run_mode"] == RECONCILIATION_RUN_MODE
    assert reconciliation["local_only"] is True
    assert reconciliation["operator_review_required"] is True
    assert reconciliation["operator_review"]["status"] == "pending_operator_review"
    assert reconciliation["summary_counts"] == {
        "accounting_entries_linked": 0,
        "accounting_entries_total": 3,
        "input_artifacts": 4,
        "paperlive_records": 1,
        "reconciliation_rows": 1,
        "warnings": 0,
    }
    assert reconciliation["local_input_artifacts"][0] == {
        "artifact_id": "crypto_paperlive_observation_ledger_001",
        "artifact_role": "crypto_paperlive_observation_ledger",
        "contract_version": "pmbot_crypto_paperlive_observation_ledger.v1",
        "local_reference": (
            "pm_bot/tests/fixtures/crypto_paperlive_observation_ledger/"
            "crypto_paperlive_observation_ledger.valid.json"
        ),
        "operator_review_status": "pending_operator_review",
        "record_count": 1,
        "runner_state": RECONCILIATION_ROW_STATE,
    }
    assert reconciliation["paperlive_reconciliation_rows"][0] == {
        "accounting_entry_count": 0,
        "accounting_entry_ids": [],
        "accounting_handling": "no_accounting_delta_recorded",
        "accounting_ledger_id": "paper_accounting_ledger_fixture_001",
        "accounting_quantity_delta_total": "0.00",
        "accounting_review_status": "pending_operator_review",
        "link_id": "crypto_paperlive_observation_ledger_001.sample.btc_threshold.to.paper_accounting",
        "operator_review_label": "Confirm static observation has no linked accounting entry in the local ledger.",
        "operator_review_status": "pending_operator_review",
        "paperlive_artifact_id": "crypto_paperlive_observation_ledger_001",
        "paperlive_asset_symbol": "BTC",
        "paperlive_metric_type": "spot_index_threshold",
        "paperlive_record_id": "crypto_paperlive_observation_ledger_001.sample.btc_threshold.observation",
        "paperlive_reference_unit": "USD",
        "paperlive_reference_value": "102500.00",
        "paperlive_reported_at_utc": "2026-05-09T00:00:00Z",
        "paperlive_review_status": "pending_operator_review",
        "reconciliation_label": "Static crypto paperlive observation has no accounting entry in the paper ledger sample.",
        "reconciliation_status": "ready_for_operator_review",
        "row_id": (
            "crypto_paperlive_observation_ledger_001.sample.btc_threshold.to.paper_accounting"
            ".paperlive_accounting_reconciliation"
        ),
        "runner_state": RECONCILIATION_ROW_STATE,
        "source_fixture_reference": (
            "pm_bot/tests/fixtures/crypto_paperlive_observation_ledger/"
            "static_crypto_reference_snapshot.valid.json"
        ),
    }
    assert reconciliation["safety_boundaries"] == LOCAL_ONLY_RECONCILIATION_SAFETY_BOUNDARIES


def test_paperlive_accounting_reconciliation_is_deterministic() -> None:
    request = load_reconciliation_artifact(SAMPLE_REQUEST_PATH)

    first = build_paperlive_accounting_reconciliation(request)
    second = build_paperlive_accounting_reconciliation(deepcopy(request))

    assert first == second
    assert first["build_id"] == "paperlive_accounting_reconciliation_fixture_001-e515f0da1873"


def test_static_sample_matches_reconciliation_builder_output() -> None:
    request = load_reconciliation_artifact(SAMPLE_REQUEST_PATH)
    sample = _load_json(SAMPLE_RECONCILIATION_PATH)

    assert build_paperlive_accounting_reconciliation(request) == sample


def test_static_sample_validates_as_paperlive_accounting_reconciliation() -> None:
    sample = _load_json(SAMPLE_RECONCILIATION_PATH)

    validation = validate_paperlive_accounting_reconciliation(sample)

    assert validation.valid is True
    assert validation.errors == ()


def test_static_markdown_sample_matches_report_builder_output() -> None:
    sample = _load_json(SAMPLE_RECONCILIATION_PATH)
    sample_report = SAMPLE_OPERATOR_REPORT_PATH.read_text(encoding="utf-8")

    assert build_operator_report(sample) == sample_report


def test_cli_writes_local_reconciliation_and_operator_report(tmp_path: Path) -> None:
    reconciliation_path = tmp_path / "paperlive_accounting_reconciliation.json"
    report_path = tmp_path / "paperlive_accounting_reconciliation.md"

    exit_code = main(
        [
            "--request",
            str(SAMPLE_REQUEST_PATH),
            "--output-reconciliation",
            str(reconciliation_path),
            "--output-report",
            str(report_path),
        ]
    )

    reconciliation = _load_json(reconciliation_path)
    report = report_path.read_text(encoding="utf-8")
    assert exit_code == 0
    assert reconciliation == _load_json(SAMPLE_RECONCILIATION_PATH)
    assert reconciliation["errors"] == []
    assert reconciliation["warnings"] == []
    assert "# PMBOT Paperlive To Accounting Reconciliation" in report
    assert "paperlive_accounting_reconciliation_fixture_001" in report
    assert "Descriptive paperlive to accounting reconciliation only" in report


def test_reconciliation_request_rejects_missing_paperlive_record() -> None:
    request = load_reconciliation_artifact(SAMPLE_REQUEST_PATH)
    request["record_links"][0]["paperlive_record_id"] = "missing-local-paperlive-record"

    validation = validate_reconciliation_request(request)

    assert validation.valid is False
    assert any("paperlive_record_id must reference a loaded paperlive record" in error for error in validation.errors)
    with pytest.raises(PaperliveAccountingReconciliationError):
        build_paperlive_accounting_reconciliation(request)


def test_reconciliation_request_rejects_unknown_accounting_entry() -> None:
    request = load_reconciliation_artifact(SAMPLE_REQUEST_PATH)
    request["record_links"][0]["accounting_entry_ids"] = ["missing-local-accounting-entry"]

    validation = validate_reconciliation_request(request)

    assert validation.valid is False
    assert any("must reference a loaded accounting entry" in error for error in validation.errors)


def test_reconciliation_request_rejects_reference_outside_allowed_paths() -> None:
    request = load_reconciliation_artifact(SAMPLE_REQUEST_PATH)
    request["paperlive_artifacts"][0]["local_reference"] = "pm_bot/wallet/paperlive_accounting.json"

    validation = validate_reconciliation_request(request)

    assert validation.valid is False
    assert any("local_reference must stay under allowed local reconciliation paths" in error for error in validation.errors)


def test_reconciliation_artifact_rejects_summary_drift_and_non_review_state() -> None:
    sample = _load_json(SAMPLE_RECONCILIATION_PATH)
    sample["summary_counts"]["paperlive_records"] = 99
    sample["paperlive_reconciliation_rows"][0]["operator_review_status"] = "accepted_without_review"

    validation = validate_paperlive_accounting_reconciliation(sample)

    assert validation.valid is False
    assert any("summary_counts must match reconciliation rows" in error for error in validation.errors)
    assert any(
        "paperlive_reconciliation_rows[0].operator_review_status must be pending_operator_review" in error
        for error in validation.errors
    )


def test_reconciliation_artifact_rejects_row_local_reference_outside_allowed_paths() -> None:
    sample = _load_json(SAMPLE_RECONCILIATION_PATH)
    sample["paperlive_reconciliation_rows"][0]["source_fixture_reference"] = "runtime/paperlive_source.json"

    validation = validate_paperlive_accounting_reconciliation(sample)

    assert validation.valid is False
    assert any("source_fixture_reference must stay under allowed local reconciliation paths" in error for error in validation.errors)


def test_reconciliation_output_contract_has_no_scoring_or_selection_fields() -> None:
    request = load_reconciliation_artifact(SAMPLE_REQUEST_PATH)
    reconciliation = build_paperlive_accounting_reconciliation(request)

    offending_paths = _find_output_decision_terms(reconciliation)

    assert offending_paths == []


def test_documentation_registers_reconciliation_contract_samples_and_safety_boundary() -> None:
    document = DOC_PATH.read_text(encoding="utf-8")

    assert f"Task: `{TASK_ID}`" in document
    assert "Artifact: `pmbot-paperlive-accounting-reconciliation`" in document
    assert f"Contract: `{RECONCILIATION_CONTRACT_VERSION}`" in document
    assert str(SAMPLE_REQUEST_PATH).replace("\\", "/") in document
    assert str(SAMPLE_RECONCILIATION_PATH).replace("\\", "/") in document
    assert str(SAMPLE_OPERATOR_REPORT_PATH).replace("\\", "/") in document
    assert "No forecast scoring, action guidance, market ranking, or selection advice." in document
    assert "This artifact is not execution approval and is not runtime input." in document


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
