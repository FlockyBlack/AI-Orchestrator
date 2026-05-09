from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from pm_bot.source_quality.unified_source_quality_ledger import (
    LEDGER_CONTRACT_VERSION,
    LEDGER_ROW_STATE,
    LOCAL_RUN_MODE,
    OPERATOR_REVIEW_STATUS,
    REQUEST_CONTRACT_VERSION,
    SourceQualityLedgerValidationError,
    build_operator_report,
    build_unified_source_quality_ledger,
    load_ledger_request,
    main,
    validate_ledger_request,
    validate_unified_source_quality_ledger,
)

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "source_quality"
VALID_REQUEST_PATH = FIXTURE_DIR / "unified_source_quality_ledger_request.valid.json"
SAMPLE_LEDGER_PATH = Path("pm_bot/source_quality/samples/unified_source_quality_ledger.fixture.json")


def test_valid_fixture_request_builds_unified_source_quality_ledger() -> None:
    request = load_ledger_request(VALID_REQUEST_PATH)
    validation = validate_ledger_request(request)
    ledger = build_unified_source_quality_ledger(request)

    assert validation.valid is True
    assert validation.errors == ()
    assert ledger["contract_version"] == LEDGER_CONTRACT_VERSION
    assert ledger["ledger_id"] == "unified_source_quality_ledger_fixture_001"
    assert ledger["run_mode"] == LOCAL_RUN_MODE
    assert ledger["local_only"] is True
    assert ledger["operator_review_required"] is True
    assert ledger["operator_review"]["status"] == OPERATOR_REVIEW_STATUS
    assert ledger["summary_counts"] == {
        "fields_declared": 8,
        "fields_missing": 0,
        "fields_present": 8,
        "source_artifacts": 2,
        "source_quality_rows": 2,
        "warnings": 0,
    }
    assert ledger["source_inventory"][0] == {
        "artifact_loaded": True,
        "artifact_role": "weather_observation_snapshot",
        "field_count": 4,
        "local_reference": "pm_bot/tests/fixtures/weather/official_daily_climate_report_snapshot.json",
        "operator_review_status": OPERATOR_REVIEW_STATUS,
        "row_id": "unified_source_quality_ledger_fixture_001.official_daily_climate_report.source_quality_review",
        "runner_state": LEDGER_ROW_STATE,
        "snapshot_id": "fixture_official_daily_climate_report_2026_05_09",
        "source_id": "official_daily_climate_report",
        "source_label": "Official daily climate report",
        "source_type": "official_record_snapshot",
    }
    assert ledger["source_quality_rows"][0]["field_presence"][0] == {
        "field_name": "observation_date",
        "observed_value_type": "str",
        "operator_review_status": OPERATOR_REVIEW_STATUS,
        "present": True,
    }
    assert ledger["safety_boundaries"] == {
        "external_market_api_allowed": False,
        "llm_calls_allowed": False,
        "network_calls_allowed": False,
        "offline_inputs_only": True,
        "operator_review_gate_required": True,
        "outcome_resolution_allowed": False,
        "runtime_wiring_allowed": False,
        "scheduler_or_worker_allowed": False,
        "source_preference_output_allowed": False,
        "trade_action_guidance_allowed": False,
        "wallet_or_order_code_allowed": False,
    }


def test_unified_source_quality_ledger_is_deterministic_for_same_request() -> None:
    request = load_ledger_request(VALID_REQUEST_PATH)

    first = build_unified_source_quality_ledger(request)
    second = build_unified_source_quality_ledger(deepcopy(request))

    assert first == second
    assert first["build_id"] == "unified_source_quality_ledger_fixture_001-be4cc5453863"


def test_static_sample_matches_builder_output() -> None:
    request = load_ledger_request(VALID_REQUEST_PATH)
    sample = json.loads(SAMPLE_LEDGER_PATH.read_text(encoding="utf-8"))

    assert build_unified_source_quality_ledger(request) == sample


def test_static_sample_validates_as_source_quality_ledger_artifact() -> None:
    sample = json.loads(SAMPLE_LEDGER_PATH.read_text(encoding="utf-8"))

    validation = validate_unified_source_quality_ledger(sample)

    assert validation.valid is True
    assert validation.errors == ()


def test_ledger_artifact_validation_rejects_field_type_drift() -> None:
    request = load_ledger_request(VALID_REQUEST_PATH)
    ledger = build_unified_source_quality_ledger(request)
    ledger["source_quality_rows"][0]["field_presence"][0]["observed_value_type"] = "int"

    validation = validate_unified_source_quality_ledger(ledger)

    assert validation.valid is False
    assert any(
        "source_quality_rows[0].field_presence[0].observed_value_type must match local artifact field type: str"
        in error
        for error in validation.errors
    )


def test_ledger_artifact_validation_rejects_summary_and_inventory_mismatch() -> None:
    request = load_ledger_request(VALID_REQUEST_PATH)
    ledger = build_unified_source_quality_ledger(request)
    ledger["summary_counts"]["fields_present"] = 99
    ledger["source_inventory"][0]["field_count"] = 99

    validation = validate_unified_source_quality_ledger(ledger)

    assert validation.valid is False
    assert any("summary_counts must match source_quality_rows totals" in error for error in validation.errors)
    assert any("field_count must match source_quality_rows row" in error for error in validation.errors)


def test_ledger_artifact_validation_rejects_non_operator_review_state() -> None:
    request = load_ledger_request(VALID_REQUEST_PATH)
    ledger = build_unified_source_quality_ledger(request)
    ledger["source_quality_rows"][0]["operator_review_status"] = "accepted_without_review"

    validation = validate_unified_source_quality_ledger(ledger)

    assert validation.valid is False
    assert any(
        "source_quality_rows[0].operator_review_status must be pending_operator_review" in error
        for error in validation.errors
    )


def test_ledger_artifact_validation_rejects_scoring_or_action_fields() -> None:
    request = load_ledger_request(VALID_REQUEST_PATH)
    ledger = build_unified_source_quality_ledger(request)
    ledger["source_quality_rows"][0]["forecast_score"] = "not allowed in local source quality ledgers"

    validation = validate_unified_source_quality_ledger(ledger)

    assert validation.valid is False
    assert any("forbidden scoring/action field detected in ledger" in error for error in validation.errors)


def test_cli_writes_local_ledger_and_operator_report(tmp_path: Path) -> None:
    ledger_path = tmp_path / "unified_source_quality_ledger.json"
    report_path = tmp_path / "unified_source_quality_ledger.md"

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
    assert "# PMBOT Unified Source Quality Ledger" in report
    assert "official_daily_climate_report" in report
    assert "Makes no network, LLM, market API, wallet, order, or runtime calls." in report
    assert "Does not resolve outcomes or provide trade action guidance." in report


def test_operator_report_is_deterministic() -> None:
    request = load_ledger_request(VALID_REQUEST_PATH)
    ledger = build_unified_source_quality_ledger(request)

    first = build_operator_report(ledger)
    second = build_operator_report(deepcopy(ledger))

    assert first == second
    assert "Operator review: `pending_operator_review`" in first
    assert "Descriptive source review only." in first


def test_request_rejects_network_like_source_reference() -> None:
    request = load_ledger_request(VALID_REQUEST_PATH)
    request["source_artifacts"][0]["local_reference"] = "https://example.invalid/source.json"

    validation = validate_ledger_request(request)

    assert validation.valid is False
    assert any("local_reference must point to a local fixture or static artifact" in error for error in validation.errors)
    with pytest.raises(SourceQualityLedgerValidationError):
        build_unified_source_quality_ledger(request)


def test_request_rejects_reference_outside_allowed_local_paths() -> None:
    request = load_ledger_request(VALID_REQUEST_PATH)
    request["source_artifacts"][0]["local_reference"] = "pm_bot/llm/source_quality.json"

    validation = validate_ledger_request(request)

    assert validation.valid is False
    assert any("local_reference is outside the source quality ledger boundary" in error for error in validation.errors)


def test_request_rejects_missing_declared_field() -> None:
    request = load_ledger_request(VALID_REQUEST_PATH)
    request["source_artifacts"][0]["fields_available"].append("missing_fixture_field")

    validation = validate_ledger_request(request)

    assert validation.valid is False
    assert any("references fields missing from local artifact: missing_fixture_field" in error for error in validation.errors)
    with pytest.raises(SourceQualityLedgerValidationError):
        build_unified_source_quality_ledger(request)


def test_request_rejects_scoring_or_action_fields() -> None:
    request = load_ledger_request(VALID_REQUEST_PATH)
    request["source_artifacts"][0]["forecast_score"] = "not allowed in local source quality ledgers"

    validation = validate_ledger_request(request)

    assert validation.valid is False
    assert any("forbidden scoring/action field detected" in error for error in validation.errors)


def test_output_contract_has_no_scoring_or_selection_fields() -> None:
    request = load_ledger_request(VALID_REQUEST_PATH)
    ledger = build_unified_source_quality_ledger(request)

    offending_paths = _find_output_decision_terms(ledger)

    assert offending_paths == []


def test_ledger_request_contract_version_is_explicit() -> None:
    request = load_ledger_request(VALID_REQUEST_PATH)

    assert request["contract_version"] == REQUEST_CONTRACT_VERSION


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
