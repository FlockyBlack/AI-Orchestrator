from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from pm_bot.source_quality.source_contradiction_ledger import (
    CONTRADICTION_ROW_STATE,
    DIFFERENT_STATIC_VALUES_PENDING_REVIEW,
    EXPECTED_SAFETY_BOUNDARIES,
    LEDGER_CONTRACT_VERSION,
    LEDGER_RUN_MODE,
    OPERATOR_REVIEW_STATUS,
    REQUEST_CONTRACT_VERSION,
    SAMPLE_LEDGER_PATH,
    SAMPLE_OPERATOR_REPORT_PATH,
    STATIC_VALUE_DIFFERENCE_PENDING_REVIEW,
    SourceQualityLedgerValidationError,
    build_operator_report,
    build_source_contradiction_ledger,
    load_source_contradiction_ledger_request,
    main,
    validate_source_contradiction_ledger,
    validate_source_contradiction_ledger_request,
)

DOC_PATH = Path("docs/PMBOT_SOURCE_EVIDENCE_004_SOURCE_CONTRADICTION_LEDGER_LOCAL_ONLY.md")
VALID_REQUEST_REFERENCE = "pm_bot/tests/fixtures/source_quality/source_contradiction_ledger_request.valid.json"
VALID_REQUEST_PATH = Path(VALID_REQUEST_REFERENCE)


def test_valid_request_builds_source_contradiction_ledger() -> None:
    request = load_source_contradiction_ledger_request(VALID_REQUEST_PATH)
    validation = validate_source_contradiction_ledger_request(request)
    ledger = build_source_contradiction_ledger(request)

    assert validation.valid is True
    assert validation.errors == ()
    assert ledger["contract_version"] == LEDGER_CONTRACT_VERSION
    assert ledger["ledger_id"] == "source_contradiction_ledger_fixture_001"
    assert ledger["run_mode"] == LEDGER_RUN_MODE
    assert ledger["local_only"] is True
    assert ledger["operator_review_required"] is True
    assert ledger["operator_review"]["status"] == OPERATOR_REVIEW_STATUS
    assert ledger["safety_boundaries"] == EXPECTED_SAFETY_BOUNDARIES
    assert ledger["summary_counts"] == {
        "different_field_comparisons": 1,
        "field_comparisons": 1,
        "local_references": 5,
        "matching_field_comparisons": 0,
        "operator_review_steps": 3,
        "review_checks": 4,
        "source_artifact_references": 2,
        "source_contradiction_rows": 1,
        "source_staleness_checks": 2,
        "subject_key_comparisons": 2,
        "subject_key_differences": 0,
        "warnings": 0,
    }

    row = ledger["source_contradiction_rows"][0]
    assert row["row_id"] == (
        "source_contradiction_ledger_fixture_001."
        "weather_daily_high_temperature_static_compare.source_contradiction_review"
    )
    assert row["row_state"] == CONTRADICTION_ROW_STATE
    assert row["contradiction_state"] == STATIC_VALUE_DIFFERENCE_PENDING_REVIEW
    assert row["left_source"]["source_id"] == "official_daily_climate_report"
    assert row["right_source"]["source_id"] == "airport_station_observation_log"
    assert row["subject_key_comparisons"] == [
        {
            "field_name": "station_id",
            "left_value": "KNYC",
            "operator_review_status": OPERATOR_REVIEW_STATUS,
            "right_value": "KNYC",
            "values_match": True,
        },
        {
            "field_name": "observation_date",
            "left_value": "2026-05-09",
            "operator_review_status": OPERATOR_REVIEW_STATUS,
            "right_value": "2026-05-09",
            "values_match": True,
        },
    ]
    assert row["field_comparisons"] == [
        {
            "comparison_state": DIFFERENT_STATIC_VALUES_PENDING_REVIEW,
            "left_field": "high_temperature_f",
            "left_value": 74,
            "operator_review_status": OPERATOR_REVIEW_STATUS,
            "right_field": "observed_high_temperature_f",
            "right_value": 73,
            "semantic_field": "daily_high_temperature_f",
            "unit_label": "fahrenheit",
            "values_match": False,
        }
    ]
    assert len(row["review_checks"]) == 4
    assert all(check["operator_review_status"] == OPERATOR_REVIEW_STATUS for check in row["review_checks"])


def test_source_contradiction_ledger_is_deterministic_for_same_request() -> None:
    request = load_source_contradiction_ledger_request(VALID_REQUEST_PATH)

    first = build_source_contradiction_ledger(request)
    second = build_source_contradiction_ledger(deepcopy(request))

    assert first == second
    assert first["build_id"] == "source_contradiction_ledger_fixture_001-5d1565a70e0d"


def test_static_sample_matches_source_contradiction_ledger_builder_output() -> None:
    request = load_source_contradiction_ledger_request(VALID_REQUEST_PATH)
    sample = json.loads(Path(SAMPLE_LEDGER_PATH).read_text(encoding="utf-8"))

    assert build_source_contradiction_ledger(request) == sample


def test_static_sample_validates_as_source_contradiction_ledger() -> None:
    sample = json.loads(Path(SAMPLE_LEDGER_PATH).read_text(encoding="utf-8"))

    validation = validate_source_contradiction_ledger(sample)

    assert validation.valid is True
    assert validation.errors == ()


def test_static_markdown_sample_matches_report_builder_output() -> None:
    sample = json.loads(Path(SAMPLE_LEDGER_PATH).read_text(encoding="utf-8"))
    sample_report = Path(SAMPLE_OPERATOR_REPORT_PATH).read_text(encoding="utf-8")

    assert build_operator_report(sample) == sample_report


def test_cli_writes_local_source_contradiction_ledger_and_operator_report(tmp_path: Path) -> None:
    ledger_path = tmp_path / "source_contradiction_ledger.json"
    report_path = tmp_path / "source_contradiction_ledger.md"

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
    assert "# PMBOT Source Contradiction Ledger" in report
    assert "weather_daily_high_temperature_static_compare" in report
    assert "Records local static source differences and pending review state only." in report
    assert "Does not authorize execution and is not runtime input." in report


def test_request_rejects_network_like_staleness_spec_reference() -> None:
    request = load_source_contradiction_ledger_request(VALID_REQUEST_PATH)
    request["source_staleness_check_spec_reference"] = "https://example.invalid/source_staleness_check_spec.json"

    validation = validate_source_contradiction_ledger_request(request)

    assert validation.valid is False
    assert any("local_reference must point to a local fixture or static artifact" in error for error in validation.errors)
    with pytest.raises(SourceQualityLedgerValidationError):
        build_source_contradiction_ledger(request)


def test_request_rejects_unknown_source() -> None:
    request = load_source_contradiction_ledger_request(VALID_REQUEST_PATH)
    request["contradiction_checks"][0]["right_source_id"] = "missing_source"

    validation = validate_source_contradiction_ledger_request(request)

    assert validation.valid is False
    assert any("right_source_id must exist in source staleness spec" in error for error in validation.errors)


def test_request_rejects_missing_mapped_field() -> None:
    request = load_source_contradiction_ledger_request(VALID_REQUEST_PATH)
    request["contradiction_checks"][0]["field_mappings"][0]["left_field"] = "missing_left_field"

    validation = validate_source_contradiction_ledger_request(request)

    assert validation.valid is False
    assert any("left_field missing from left source artifact" in error for error in validation.errors)


def test_ledger_validation_rejects_digest_or_value_drift() -> None:
    sample = json.loads(Path(SAMPLE_LEDGER_PATH).read_text(encoding="utf-8"))
    row = sample["source_contradiction_rows"][0]
    row["left_source"]["source_artifact"]["content_sha256"] = "0" * 64
    row["field_comparisons"][0]["left_value"] = 75

    validation = validate_source_contradiction_ledger(sample)

    assert validation.valid is False
    assert any("content_sha256" in error for error in validation.errors)
    assert any("left_value must match left source artifact" in error for error in validation.errors)


def test_output_contract_has_no_forecast_scoring_or_selection_terms() -> None:
    request = load_source_contradiction_ledger_request(VALID_REQUEST_PATH)
    ledger = build_source_contradiction_ledger(request)

    assert _find_output_decision_terms(ledger) == []


def test_source_contradiction_ledger_documentation_registers_local_artifacts() -> None:
    document = DOC_PATH.read_text(encoding="utf-8")

    assert "Task: `PMBOT-SOURCE-EVIDENCE-004-SOURCE-CONTRADICTION-LEDGER-LOCAL-ONLY`" in document
    assert f"Contract: `{LEDGER_CONTRACT_VERSION}`" in document
    assert f"Run mode: `{LEDGER_RUN_MODE}`" in document
    assert VALID_REQUEST_REFERENCE in document
    assert SAMPLE_LEDGER_PATH in document
    assert SAMPLE_OPERATOR_REPORT_PATH in document
    assert "This ledger is not execution approval and is not runtime input." in document


def test_request_contract_version_is_explicit() -> None:
    request = load_source_contradiction_ledger_request(VALID_REQUEST_PATH)

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
