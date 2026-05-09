from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from pm_bot.dashboard.local_source_quality_dashboard_summary import (
    DASHBOARD_CONTRACT_VERSION,
    LOCAL_ONLY_SAFETY_BOUNDARIES,
    LOCAL_RUN_MODE,
    OPERATOR_REVIEW_STATUS,
    REQUEST_CONTRACT_VERSION,
    SAMPLE_DASHBOARD_PATH,
    SAMPLE_OPERATOR_REPORT_PATH,
    SourceQualityDashboardValidationError,
    build_local_source_quality_dashboard_summary,
    build_operator_report,
    load_dashboard_request,
    main,
    validate_dashboard_request,
    validate_local_source_quality_dashboard_summary,
)

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "dashboard"
VALID_REQUEST_PATH = FIXTURE_DIR / "local_source_quality_dashboard_request.valid.json"
DOC_PATH = Path("docs/PMBOT_DASHBOARD_003_SOURCE_QUALITY_DASHBOARD_SUMMARY.md")
TASK_ID = "PMBOT-DASHBOARD-003-SOURCE-QUALITY-DASHBOARD-SUMMARY"


def test_valid_fixture_request_builds_source_quality_dashboard_summary() -> None:
    request = load_dashboard_request(VALID_REQUEST_PATH)
    validation = validate_dashboard_request(request)
    dashboard = build_local_source_quality_dashboard_summary(request)

    assert validation.valid is True
    assert validation.errors == ()
    assert dashboard["contract_version"] == DASHBOARD_CONTRACT_VERSION
    assert dashboard["dashboard_id"] == "local_source_quality_dashboard_fixture_001"
    assert dashboard["dashboard_label"] == "PMBOT local source quality dashboard"
    assert dashboard["run_mode"] == LOCAL_RUN_MODE
    assert dashboard["local_only"] is True
    assert dashboard["operator_review_required"] is True
    assert dashboard["operator_review"]["status"] == OPERATOR_REVIEW_STATUS
    assert dashboard["summary_counts"] == {
        "fields_declared": 59,
        "fields_missing": 0,
        "fields_present": 59,
        "known_limitations": 12,
        "operator_review_pending_records": 11,
        "queue_records": 5,
        "review_assertions": 11,
        "review_checks": 28,
        "source_artifacts": 10,
        "source_quality_artifacts": 4,
        "source_quality_rows": 10,
        "validation_records": 2,
        "warnings": 0,
    }
    assert dashboard["queue_summary"][0] == {
        "local_reference": "docs/PMBOT_DASHBOARD_003_SOURCE_QUALITY_DASHBOARD_SUMMARY.md",
        "notes": "Static queue coverage includes the source quality dashboard summary task identifier.",
        "operator_review_status": OPERATOR_REVIEW_STATUS,
        "queue_group": "next_twenty_template",
        "record_id": f"queue_source_quality.{TASK_ID}",
        "runner_state": "ready_for_operator_review",
        "safety_class": "local_only_no_execution",
        "status_label": "template_listed_static_record",
        "task_id": TASK_ID,
        "task_template": "source_quality_dashboard_summary",
        "task_title": "PMBOT source quality dashboard summary",
        "validation_profile": "pmbot_local_code_tests",
    }
    assert dashboard["source_quality_summary"][3] == {
        "artifact_id": "crypto_source_quality_capture_surface_001",
        "artifact_label": "Crypto source quality capture surface",
        "artifact_type": "crypto_source_quality_capture_surface",
        "contract_version": "pmbot_crypto_source_quality_capture_surface.v1",
        "fields_declared": 35,
        "fields_missing": 0,
        "fields_present": 35,
        "known_limitations": 0,
        "local_reference": "docs/PMBOT_CRYPTO_PILOT_004_CRYPTO_SOURCE_QUALITY_CAPTURE_SURFACE_LOCAL_ONLY.md",
        "notes": "Static crypto capture sample records required field visibility across local crypto pilot fixtures.",
        "operator_review_status": OPERATOR_REVIEW_STATUS,
        "record_id": "source_quality_dashboard.crypto_source_quality_capture_surface_001",
        "review_assertions": 0,
        "review_checks": 16,
        "run_mode": "local_descriptive_crypto_source_quality_capture_surface",
        "runner_state": "ready_for_operator_review",
        "scope": "crypto_source_quality_capture_surface",
        "source_artifacts": 4,
        "source_fixture_reference": "pm_bot/source_quality/samples/crypto_source_quality_capture_surface.fixture.json",
        "source_quality_rows": 4,
        "status_label": "static_source_quality_sample_ready",
    }
    assert dashboard["validation_status_summary"][0]["command_label"] == "python -m compileall pm_bot tests"
    assert dashboard["safety_boundaries"] == LOCAL_ONLY_SAFETY_BOUNDARIES


def test_source_quality_dashboard_summary_is_deterministic_for_same_request() -> None:
    request = load_dashboard_request(VALID_REQUEST_PATH)

    first = build_local_source_quality_dashboard_summary(request)
    second = build_local_source_quality_dashboard_summary(deepcopy(request))

    assert first == second
    assert first["build_id"] == "local_source_quality_dashboard_fixture_001-ebfa452f14b1"


def test_static_sample_matches_builder_output() -> None:
    request = load_dashboard_request(VALID_REQUEST_PATH)
    sample = json.loads(Path(SAMPLE_DASHBOARD_PATH).read_text(encoding="utf-8"))

    assert build_local_source_quality_dashboard_summary(request) == sample


def test_static_sample_validates_as_source_quality_dashboard_artifact() -> None:
    sample = json.loads(Path(SAMPLE_DASHBOARD_PATH).read_text(encoding="utf-8"))

    validation = validate_local_source_quality_dashboard_summary(sample)

    assert validation.valid is True
    assert validation.errors == ()


def test_static_markdown_sample_matches_report_builder_output() -> None:
    sample_dashboard = json.loads(Path(SAMPLE_DASHBOARD_PATH).read_text(encoding="utf-8"))
    sample_report = Path(SAMPLE_OPERATOR_REPORT_PATH).read_text(encoding="utf-8")

    assert build_operator_report(sample_dashboard) == sample_report


def test_cli_writes_local_source_quality_dashboard_summary_and_operator_report(tmp_path: Path) -> None:
    dashboard_path = tmp_path / "local_source_quality_dashboard_summary.json"
    report_path = tmp_path / "local_source_quality_dashboard_summary.md"

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
    assert "# PMBOT Source Quality Dashboard Summary" in report
    assert TASK_ID in report
    assert "crypto_source_quality_capture_surface_001" in report
    assert "pytest pm_bot/tests tests/test_codex_queue_pmbot_templates.py" in report
    assert "Descriptive source quality dashboard only" in report


def test_operator_report_is_deterministic() -> None:
    request = load_dashboard_request(VALID_REQUEST_PATH)
    dashboard = build_local_source_quality_dashboard_summary(request)

    first = build_operator_report(dashboard)
    second = build_operator_report(deepcopy(dashboard))

    assert first == second
    assert "Operator review: `pending_operator_review`" in first
    assert "Source quality artifacts: 4" in first


def test_request_rejects_network_like_local_reference() -> None:
    request = load_dashboard_request(VALID_REQUEST_PATH)
    request["source_quality_records"][0]["source_fixture_reference"] = "https://example.invalid/source.json"

    validation = validate_dashboard_request(request)

    assert validation.valid is False
    assert any("source_fixture_reference must be a local reference" in error for error in validation.errors)
    with pytest.raises(SourceQualityDashboardValidationError):
        build_local_source_quality_dashboard_summary(request)


def test_request_rejects_reference_outside_allowed_local_paths() -> None:
    request = load_dashboard_request(VALID_REQUEST_PATH)
    request["queue_records"][0]["local_reference"] = "pm_bot/trading/source_quality_dashboard.json"

    validation = validate_dashboard_request(request)

    assert validation.valid is False
    assert any("local_reference is outside the source quality dashboard boundary" in error for error in validation.errors)


def test_request_rejects_scoring_or_selection_fields() -> None:
    request = load_dashboard_request(VALID_REQUEST_PATH)
    request["source_quality_records"][0]["forecast_score"] = "not allowed in local dashboard summaries"

    validation = validate_dashboard_request(request)

    assert validation.valid is False
    assert any("forbidden source quality dashboard decision field detected" in error for error in validation.errors)


def test_source_quality_dashboard_rejects_summary_count_drift() -> None:
    request = load_dashboard_request(VALID_REQUEST_PATH)
    dashboard = build_local_source_quality_dashboard_summary(request)
    dashboard["summary_counts"]["fields_present"] = 99

    validation = validate_local_source_quality_dashboard_summary(dashboard)

    assert validation.valid is False
    assert any("summary_counts must match source quality dashboard rows" in error for error in validation.errors)


def test_source_quality_dashboard_rejects_field_count_drift() -> None:
    request = load_dashboard_request(VALID_REQUEST_PATH)
    dashboard = build_local_source_quality_dashboard_summary(request)
    dashboard["source_quality_summary"][0]["fields_present"] = 7

    validation = validate_local_source_quality_dashboard_summary(dashboard)

    assert validation.valid is False
    assert any("fields_declared must equal present plus missing fields" in error for error in validation.errors)


def test_output_contract_has_no_scoring_or_selection_fields() -> None:
    request = load_dashboard_request(VALID_REQUEST_PATH)
    dashboard = build_local_source_quality_dashboard_summary(request)

    offending_paths = _find_output_decision_terms(dashboard)

    assert offending_paths == []


def test_source_quality_dashboard_request_contract_version_is_explicit() -> None:
    request = load_dashboard_request(VALID_REQUEST_PATH)

    assert request["contract_version"] == REQUEST_CONTRACT_VERSION


def test_documentation_registers_dashboard_contract_fixtures_and_safety_boundary() -> None:
    document = DOC_PATH.read_text(encoding="utf-8")

    assert f"Task: `{TASK_ID}`" in document
    assert f"Contract: `{DASHBOARD_CONTRACT_VERSION}`" in document
    assert "pm_bot/dashboard/samples/local_source_quality_dashboard_summary.fixture.json" in document
    assert "pm_bot/tests/fixtures/dashboard/local_source_quality_dashboard_request.valid.json" in document
    assert "No forecast scoring, action guidance, or selection advice." in document
    assert "This dashboard summary is not execution approval and is not runtime input." in document


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
