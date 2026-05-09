from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from pm_bot.source_quality.source_quality_report_summary import (
    REPORT_SUMMARY_CONTRACT_VERSION,
    REPORT_SUMMARY_RUN_MODE,
    SAMPLE_OPERATOR_REPORT_PATH,
    SAMPLE_REPORT_SUMMARY_PATH,
    SourceQualityLedgerValidationError,
    build_operator_report,
    build_source_quality_report_summary,
    load_source_quality_ledger,
    main,
    validate_source_quality_report_summary,
)

SAMPLE_LEDGER_PATH = Path("pm_bot/source_quality/samples/unified_source_quality_ledger.fixture.json")


def test_static_ledger_builds_source_quality_report_summary() -> None:
    ledger = load_source_quality_ledger(SAMPLE_LEDGER_PATH)
    summary = build_source_quality_report_summary(ledger)

    assert summary["contract_version"] == REPORT_SUMMARY_CONTRACT_VERSION
    assert summary["report_summary_id"] == "unified_source_quality_ledger_fixture_001.source_quality_report_summary"
    assert summary["run_mode"] == REPORT_SUMMARY_RUN_MODE
    assert summary["local_only"] is True
    assert summary["operator_review_required"] is True
    assert summary["operator_review"]["status"] == "pending_operator_review"
    assert summary["summary_counts"] == {
        "fields_declared": 8,
        "fields_missing": 0,
        "fields_present": 8,
        "known_limitations": 4,
        "operator_review_steps": 3,
        "report_summary_rows": 2,
        "review_checks": 4,
        "source_artifacts": 2,
        "warnings": 0,
    }
    assert summary["report_summary_rows"][0] == {
        "artifact_role": "weather_observation_snapshot",
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
        "local_reference": "pm_bot/tests/fixtures/weather/official_daily_climate_report_snapshot.json",
        "operator_review_status": "pending_operator_review",
        "report_row_id": "unified_source_quality_ledger_fixture_001.official_daily_climate_report.source_quality_review.source_quality_report_summary",
        "review_check_count": 2,
        "row_id": "unified_source_quality_ledger_fixture_001.official_daily_climate_report.source_quality_review",
        "runner_state": "descriptive_source_quality_report_summary",
        "snapshot_id": "fixture_official_daily_climate_report_2026_05_09",
        "source_id": "official_daily_climate_report",
        "source_label": "Official daily climate report",
        "source_type": "official_record_snapshot",
    }


def test_source_quality_report_summary_is_deterministic_for_same_ledger() -> None:
    ledger = load_source_quality_ledger(SAMPLE_LEDGER_PATH)

    first = build_source_quality_report_summary(ledger)
    second = build_source_quality_report_summary(deepcopy(ledger))

    assert first == second
    assert first["build_id"] == "unified_source_quality_ledger_fixture_001-be4cc5453863.source_quality_report_summary"


def test_static_sample_matches_report_summary_builder_output() -> None:
    ledger = load_source_quality_ledger(SAMPLE_LEDGER_PATH)
    sample = json.loads(Path(SAMPLE_REPORT_SUMMARY_PATH).read_text(encoding="utf-8"))

    assert build_source_quality_report_summary(ledger) == sample


def test_static_sample_validates_as_report_summary_artifact() -> None:
    sample = json.loads(Path(SAMPLE_REPORT_SUMMARY_PATH).read_text(encoding="utf-8"))

    validation = validate_source_quality_report_summary(sample)

    assert validation.valid is True
    assert validation.errors == ()


def test_static_markdown_sample_matches_report_builder_output() -> None:
    sample_summary = json.loads(Path(SAMPLE_REPORT_SUMMARY_PATH).read_text(encoding="utf-8"))
    sample_report = Path(SAMPLE_OPERATOR_REPORT_PATH).read_text(encoding="utf-8")

    assert build_operator_report(sample_summary) == sample_report


def test_cli_writes_local_source_quality_summary_and_operator_report(tmp_path: Path) -> None:
    summary_path = tmp_path / "source_quality_report_summary.json"
    report_path = tmp_path / "source_quality_report_summary.md"

    exit_code = main(
        [
            "--ledger",
            str(SAMPLE_LEDGER_PATH),
            "--output-summary",
            str(summary_path),
            "--output-report",
            str(report_path),
        ]
    )

    assert exit_code == 0
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    report = report_path.read_text(encoding="utf-8")
    assert summary["contract_version"] == REPORT_SUMMARY_CONTRACT_VERSION
    assert summary["errors"] == []
    assert summary["warnings"] == []
    assert "# PMBOT Source Quality Report Summary" in report
    assert "unified_source_quality_ledger_fixture_001" in report
    assert "official_daily_climate_report" in report
    assert "Descriptive report summary only" in report


def test_report_summary_validation_rejects_count_drift() -> None:
    sample = json.loads(Path(SAMPLE_REPORT_SUMMARY_PATH).read_text(encoding="utf-8"))
    sample["summary_counts"]["fields_present"] = 99

    validation = validate_source_quality_report_summary(sample)

    assert validation.valid is False
    assert any("summary_counts must match report_summary_rows totals" in error for error in validation.errors)


def test_report_summary_validation_rejects_non_operator_review_state() -> None:
    sample = json.loads(Path(SAMPLE_REPORT_SUMMARY_PATH).read_text(encoding="utf-8"))
    sample["report_summary_rows"][0]["operator_review_status"] = "accepted_without_review"

    validation = validate_source_quality_report_summary(sample)

    assert validation.valid is False
    assert any(
        "report_summary_rows[0].operator_review_status must be pending_operator_review" in error
        for error in validation.errors
    )


def test_report_summary_validation_rejects_scoring_or_action_fields() -> None:
    sample = json.loads(Path(SAMPLE_REPORT_SUMMARY_PATH).read_text(encoding="utf-8"))
    sample["report_summary_rows"][0]["forecast_score"] = "not allowed in local report summaries"

    validation = validate_source_quality_report_summary(sample)

    assert validation.valid is False
    assert any("forbidden scoring/action field detected in report summary" in error for error in validation.errors)


def test_build_rejects_invalid_source_quality_ledger() -> None:
    ledger = load_source_quality_ledger(SAMPLE_LEDGER_PATH)
    ledger["summary_counts"]["fields_present"] = 99

    with pytest.raises(SourceQualityLedgerValidationError):
        build_source_quality_report_summary(ledger)


def test_report_summary_output_contract_has_no_scoring_or_selection_fields() -> None:
    ledger = load_source_quality_ledger(SAMPLE_LEDGER_PATH)
    summary = build_source_quality_report_summary(ledger)

    offending_paths = _find_output_decision_terms(summary)

    assert offending_paths == []


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
