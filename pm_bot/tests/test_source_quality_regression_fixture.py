from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from pm_bot.source_quality.source_quality_regression_fixture import (
    REGRESSION_FIXTURE_CONTRACT_VERSION,
    REGRESSION_FIXTURE_RUN_MODE,
    SAMPLE_LEDGER_PATH,
    SAMPLE_REGRESSION_FIXTURE_PATH,
    SAMPLE_REPORT_SUMMARY_PATH,
    SourceQualityLedgerValidationError,
    build_source_quality_regression_fixture,
    load_source_quality_regression_fixture,
    main,
    validate_source_quality_regression_fixture,
)


def test_static_samples_build_source_quality_regression_fixture() -> None:
    ledger = _load_json(Path(SAMPLE_LEDGER_PATH))
    report_summary = _load_json(Path(SAMPLE_REPORT_SUMMARY_PATH))

    fixture = build_source_quality_regression_fixture(ledger, report_summary)

    assert fixture["contract_version"] == REGRESSION_FIXTURE_CONTRACT_VERSION
    assert fixture["fixture_id"] == "source_quality_regression_fixture_001"
    assert fixture["build_id"] == "source_quality_regression_fixture_001-fc3b9f978335"
    assert fixture["run_mode"] == REGRESSION_FIXTURE_RUN_MODE
    assert fixture["local_only"] is True
    assert fixture["operator_review_required"] is True
    assert fixture["operator_review"]["status"] == "pending_operator_review"
    assert fixture["summary_counts"] == {
        "artifact_references": 2,
        "fields_declared": 8,
        "fields_missing": 0,
        "fields_present": 8,
        "known_limitations": 4,
        "regression_fixture_rows": 2,
        "review_assertions": 11,
        "review_checks": 4,
        "source_artifacts": 2,
        "warnings": 0,
    }
    assert fixture["regression_fixture_rows"][0] == {
        "declared_fields": [
            "observation_date",
            "station_id",
            "high_temperature_f",
            "report_timestamp",
        ],
        "field_summary": {
            "declared": 4,
            "missing": 0,
            "present": 4,
        },
        "known_limitation_count": 2,
        "ledger_row_id": "unified_source_quality_ledger_fixture_001.official_daily_climate_report.source_quality_review",
        "local_reference": "pm_bot/tests/fixtures/weather/official_daily_climate_report_snapshot.json",
        "operator_review_status": "pending_operator_review",
        "report_row_id": "unified_source_quality_ledger_fixture_001.official_daily_climate_report.source_quality_review.source_quality_report_summary",
        "review_check_count": 2,
        "runner_state": "descriptive_source_quality_regression_review",
        "snapshot_id": "fixture_official_daily_climate_report_2026_05_09",
        "source_id": "official_daily_climate_report",
        "source_label": "Official daily climate report",
        "source_type": "official_record_snapshot",
    }


def test_source_quality_regression_fixture_is_deterministic_for_same_artifacts() -> None:
    ledger = _load_json(Path(SAMPLE_LEDGER_PATH))
    report_summary = _load_json(Path(SAMPLE_REPORT_SUMMARY_PATH))

    first = build_source_quality_regression_fixture(ledger, report_summary)
    second = build_source_quality_regression_fixture(deepcopy(ledger), deepcopy(report_summary))

    assert first == second
    assert first["build_id"] == "source_quality_regression_fixture_001-fc3b9f978335"


def test_static_sample_matches_regression_fixture_builder_output() -> None:
    ledger = _load_json(Path(SAMPLE_LEDGER_PATH))
    report_summary = _load_json(Path(SAMPLE_REPORT_SUMMARY_PATH))
    sample = _load_json(Path(SAMPLE_REGRESSION_FIXTURE_PATH))

    assert build_source_quality_regression_fixture(ledger, report_summary) == sample


def test_static_sample_validates_as_regression_fixture_artifact() -> None:
    sample = load_source_quality_regression_fixture(SAMPLE_REGRESSION_FIXTURE_PATH)

    validation = validate_source_quality_regression_fixture(sample)

    assert validation.valid is True
    assert validation.errors == ()


def test_builder_rejects_misaligned_report_summary() -> None:
    ledger = _load_json(Path(SAMPLE_LEDGER_PATH))
    report_summary = _load_json(Path(SAMPLE_REPORT_SUMMARY_PATH))
    report_summary["ledger_build_id"] = "different-local-build"

    with pytest.raises(SourceQualityLedgerValidationError):
        build_source_quality_regression_fixture(ledger, report_summary)


def test_regression_fixture_validation_rejects_assertion_drift() -> None:
    sample = load_source_quality_regression_fixture(SAMPLE_REGRESSION_FIXTURE_PATH)
    sample["review_assertions"][0]["observed_value"] = "changed-local-contract"

    validation = validate_source_quality_regression_fixture(sample)

    assert validation.valid is False
    assert any("observed_value must match expected_value" in error for error in validation.errors)


def test_regression_fixture_validation_rejects_non_operator_review_state() -> None:
    sample = load_source_quality_regression_fixture(SAMPLE_REGRESSION_FIXTURE_PATH)
    sample["regression_fixture_rows"][0]["operator_review_status"] = "accepted_without_review"

    validation = validate_source_quality_regression_fixture(sample)

    assert validation.valid is False
    assert any(
        "regression_fixture_rows[0].operator_review_status must be pending_operator_review" in error
        for error in validation.errors
    )


def test_regression_fixture_validation_rejects_scoring_or_action_fields() -> None:
    sample = load_source_quality_regression_fixture(SAMPLE_REGRESSION_FIXTURE_PATH)
    sample["review_assertions"][0]["forecast_score"] = "not allowed in local regression fixtures"

    validation = validate_source_quality_regression_fixture(sample)

    assert validation.valid is False
    assert any("forbidden scoring/action field detected in regression fixture" in error for error in validation.errors)


def test_cli_writes_local_source_quality_regression_fixture(tmp_path: Path) -> None:
    fixture_path = tmp_path / "source_quality_regression.fixture.json"

    exit_code = main(
        [
            "--ledger",
            SAMPLE_LEDGER_PATH,
            "--report-summary",
            SAMPLE_REPORT_SUMMARY_PATH,
            "--output-fixture",
            str(fixture_path),
        ]
    )

    fixture = _load_json(fixture_path)
    sample = _load_json(Path(SAMPLE_REGRESSION_FIXTURE_PATH))
    assert exit_code == 0
    assert fixture == sample
    assert fixture["errors"] == []
    assert fixture["warnings"] == []


def test_regression_fixture_output_contract_has_no_scoring_or_selection_fields() -> None:
    ledger = _load_json(Path(SAMPLE_LEDGER_PATH))
    report_summary = _load_json(Path(SAMPLE_REPORT_SUMMARY_PATH))
    fixture = build_source_quality_regression_fixture(ledger, report_summary)

    offending_paths = _find_output_decision_terms(fixture)

    assert offending_paths == []


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _find_output_decision_terms(value: object, path: str = "$") -> list[str]:
    forbidden_tokens = {
        "probability",
        "ev",
        "edge",
        "confidence",
        "side",
        "recommendation",
        "buy",
        "sell",
        "hold",
        "enter",
        "exit",
        "score",
        "scoring",
        "forecast",
        "selection",
        "pick",
        "wager",
        "stake",
        "odds",
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
