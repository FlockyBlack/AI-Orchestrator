from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from pm_bot.weather.observation_ledger_refresher import (
    LEDGER_RECORD_STATE,
    LOCAL_RUN_MODE,
    OBSERVATION_LEDGER_CONTRACT_VERSION,
    OPERATOR_REVIEW_STATUS,
    REFRESH_REQUEST_CONTRACT_VERSION,
    LedgerRefreshValidationError,
    build_observation_ledger,
    build_operator_report,
    load_refresh_request,
    main,
    validate_refresh_request,
)

FIXTURE_DIR = Path(__file__).parent / "fixtures"
VALID_REQUEST_PATH = FIXTURE_DIR / "weather_observation_ledger_refresh_request.valid.json"


def test_valid_fixture_request_builds_observation_ledger() -> None:
    request = load_refresh_request(VALID_REQUEST_PATH)
    validation = validate_refresh_request(request)
    ledger = build_observation_ledger(request)

    assert validation.valid is True
    assert validation.errors == ()
    assert ledger["contract_version"] == OBSERVATION_LEDGER_CONTRACT_VERSION
    assert ledger["ledger_id"] == "weather_observation_ledger_fixture_001"
    assert ledger["run_mode"] == LOCAL_RUN_MODE
    assert ledger["local_only"] is True
    assert ledger["operator_review_required"] is True
    assert ledger["summary_counts"] == {
        "ledger_records": 2,
        "source_snapshots": 2,
        "warnings": 0,
    }
    assert ledger["source_inventory"][0]["snapshot_loaded"] is True
    assert ledger["source_inventory"][0]["operator_review_status"] == OPERATOR_REVIEW_STATUS
    assert ledger["records"][0] == {
        "local_reference": "pm_bot/tests/fixtures/weather/official_daily_climate_report_snapshot.json",
        "measurement_name": "daily_high_temperature",
        "observation_date": "2026-05-09",
        "operator_review_label": "Official daily high temperature field",
        "operator_review_status": OPERATOR_REVIEW_STATUS,
        "record_id": "official_daily_climate_report.2026-05-09.KNYC.daily_high_temperature",
        "reported_value": 74,
        "runner_state": LEDGER_RECORD_STATE,
        "snapshot_id": "fixture_official_daily_climate_report_2026_05_09",
        "source_id": "official_daily_climate_report",
        "source_label": "Official daily climate report",
        "source_timestamp": "2026-05-10T00:05:00Z",
        "source_type": "official_record_snapshot",
        "station_id": "KNYC",
        "unit": "F",
        "value_field": "high_temperature_f",
    }
    assert ledger["safety_boundaries"] == {
        "external_market_api_allowed": False,
        "llm_calls_allowed": False,
        "network_calls_allowed": False,
        "offline_inputs_only": True,
        "operator_review_gate_required": True,
        "runtime_wiring_allowed": False,
        "scheduler_or_worker_allowed": False,
        "trade_action_guidance_allowed": False,
        "wallet_or_order_code_allowed": False,
        "weather_outcome_evaluation_allowed": False,
    }


def test_observation_ledger_refresh_is_deterministic_for_same_request() -> None:
    request = load_refresh_request(VALID_REQUEST_PATH)

    first = build_observation_ledger(request)
    second = build_observation_ledger(deepcopy(request))

    assert first == second
    assert first["refresh_id"].startswith("weather_observation_ledger_fixture_001-")
    assert len(first["refresh_id"]) == len("weather_observation_ledger_fixture_001-") + 12


def test_cli_writes_local_ledger_and_operator_report(tmp_path: Path) -> None:
    ledger_path = tmp_path / "weather_observation_ledger.json"
    report_path = tmp_path / "weather_observation_ledger_report.md"

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
    assert ledger["contract_version"] == OBSERVATION_LEDGER_CONTRACT_VERSION
    assert ledger["errors"] == []
    assert ledger["warnings"] == []
    assert "# PMBOT Weather Observation Ledger Refresh" in report
    assert "official_daily_climate_report.2026-05-09.KNYC.daily_high_temperature" in report
    assert "Makes no network, LLM, market API, wallet, order, or runtime calls." in report


def test_operator_report_is_deterministic() -> None:
    request = load_refresh_request(VALID_REQUEST_PATH)
    ledger = build_observation_ledger(request)

    first = build_operator_report(ledger)
    second = build_operator_report(deepcopy(ledger))

    assert first == second
    assert "Operator review: `pending_operator_review`" in first
    assert "Does not evaluate weather outcomes or provide trade action guidance." in first


def test_request_rejects_network_like_snapshot_reference() -> None:
    request = load_refresh_request(VALID_REQUEST_PATH)
    request["source_snapshots"][0]["local_reference"] = "https://example.invalid/weather.json"

    validation = validate_refresh_request(request)

    assert validation.valid is False
    assert any("local_reference must point to a local fixture or static artifact" in error for error in validation.errors)
    with pytest.raises(LedgerRefreshValidationError):
        build_observation_ledger(request)


def test_request_rejects_snapshot_reference_outside_allowed_local_paths() -> None:
    request = load_refresh_request(VALID_REQUEST_PATH)
    request["source_snapshots"][0]["local_reference"] = "pm_bot/weather/local_snapshot.json"

    validation = validate_refresh_request(request)

    assert validation.valid is False
    assert any("local_reference must stay under an allowed local fixture/static path" in error for error in validation.errors)


def test_refresh_rejects_missing_snapshot_required_field() -> None:
    request = load_refresh_request(VALID_REQUEST_PATH)
    request["source_snapshots"][0]["required_fields"].append("missing_fixture_field")

    with pytest.raises(LedgerRefreshValidationError) as exc_info:
        build_observation_ledger(request)

    assert any("missing required fields: missing_fixture_field" in error for error in exc_info.value.errors)


def test_refresh_rejects_record_field_missing_from_snapshot() -> None:
    request = load_refresh_request(VALID_REQUEST_PATH)
    request["record_specs"][0]["value_field"] = "missing_fixture_field"

    with pytest.raises(LedgerRefreshValidationError) as exc_info:
        build_observation_ledger(request)

    assert any("references missing snapshot fields: missing_fixture_field" in error for error in exc_info.value.errors)


def test_request_rejects_scoring_or_action_fields() -> None:
    request = load_refresh_request(VALID_REQUEST_PATH)
    request["record_specs"][0]["forecast_score"] = "not allowed in local observation ledgers"

    validation = validate_refresh_request(request)

    assert validation.valid is False
    assert any("forbidden scoring/action field detected" in error for error in validation.errors)


def test_output_contract_has_no_scoring_or_selection_fields() -> None:
    request = load_refresh_request(VALID_REQUEST_PATH)
    ledger = build_observation_ledger(request)

    offending_paths = _find_output_decision_terms(ledger)

    assert offending_paths == []


def test_refresh_request_contract_version_is_explicit() -> None:
    request = load_refresh_request(VALID_REQUEST_PATH)

    assert request["contract_version"] == REFRESH_REQUEST_CONTRACT_VERSION


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
