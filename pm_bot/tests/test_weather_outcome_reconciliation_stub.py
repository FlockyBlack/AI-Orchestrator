from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from pm_bot.weather.outcome_reconciliation_stub import (
    AUTOMATED_OUTCOME_STATUS,
    LOCAL_RUN_MODE,
    OPERATOR_REVIEW_STATUS,
    RECONCILIATION_RECORD_CONTRACT_VERSION,
    RECONCILIATION_RECORD_STATE,
    RECONCILIATION_REQUEST_CONTRACT_VERSION,
    ReconciliationValidationError,
    build_operator_report,
    build_reconciliation_record,
    load_reconciliation_request,
    main,
    validate_reconciliation_request,
)

FIXTURE_DIR = Path(__file__).parent / "fixtures"
VALID_REQUEST_PATH = FIXTURE_DIR / "weather_outcome_reconciliation_request.valid.json"


def test_valid_fixture_request_builds_operator_review_reconciliation_record() -> None:
    request = load_reconciliation_request(VALID_REQUEST_PATH)
    validation = validate_reconciliation_request(request)
    record = build_reconciliation_record(request)

    assert validation.valid is True
    assert validation.errors == ()
    assert record["contract_version"] == RECONCILIATION_RECORD_CONTRACT_VERSION
    assert record["reconciliation_id"] == "weather_outcome_reconciliation_fixture_001"
    assert record["run_mode"] == LOCAL_RUN_MODE
    assert record["local_only"] is True
    assert record["operator_review_required"] is True
    assert record["summary_counts"] == {
        "observation_records": 2,
        "outcome_reviews": 1,
        "warnings": 0,
    }
    assert record["record_inventory"][0] == {
        "local_reference": "pm_bot/tests/fixtures/weather/official_daily_climate_report_snapshot.json",
        "measurement_name": "daily_high_temperature",
        "observation_date": "2026-05-09",
        "operator_review_status": OPERATOR_REVIEW_STATUS,
        "record_id": "official_daily_climate_report.2026-05-09.KNYC.daily_high_temperature",
        "reported_value": 74,
        "runner_state": RECONCILIATION_RECORD_STATE,
        "snapshot_id": "fixture_official_daily_climate_report_2026_05_09",
        "source_id": "official_daily_climate_report",
        "source_label": "Official daily climate report",
        "source_timestamp": "2026-05-10T00:05:00Z",
        "source_type": "official_record_snapshot",
        "station_id": "KNYC",
        "unit": "F",
    }
    review_record = record["outcome_review_records"][0]
    assert review_record["review_record_id"] == (
        "weather_outcome_reconciliation_fixture_001."
        "temperature_threshold_operator_review.operator_review"
    )
    assert review_record["automated_outcome_status"] == AUTOMATED_OUTCOME_STATUS
    assert review_record["operator_review_status"] == OPERATOR_REVIEW_STATUS
    assert [item["reported_value"] for item in review_record["referenced_records"]] == [74, 73]
    assert record["safety_boundaries"] == {
        "automated_outcome_resolution_allowed": False,
        "external_market_api_allowed": False,
        "llm_calls_allowed": False,
        "network_calls_allowed": False,
        "offline_inputs_only": True,
        "operator_review_gate_required": True,
        "runtime_wiring_allowed": False,
        "scheduler_or_worker_allowed": False,
        "trade_action_guidance_allowed": False,
        "wallet_or_order_code_allowed": False,
    }


def test_reconciliation_record_is_deterministic_for_same_request() -> None:
    request = load_reconciliation_request(VALID_REQUEST_PATH)

    first = build_reconciliation_record(request)
    second = build_reconciliation_record(deepcopy(request))

    assert first == second
    assert first["run_id"].startswith("weather_outcome_reconciliation_fixture_001-")
    assert len(first["run_id"]) == len("weather_outcome_reconciliation_fixture_001-") + 12


def test_cli_writes_local_reconciliation_record_and_operator_report(tmp_path: Path) -> None:
    record_path = tmp_path / "weather_outcome_reconciliation_record.json"
    report_path = tmp_path / "weather_outcome_reconciliation_report.md"

    exit_code = main(
        [
            "--request",
            str(VALID_REQUEST_PATH),
            "--output-record",
            str(record_path),
            "--output-report",
            str(report_path),
        ]
    )

    assert exit_code == 0
    record = json.loads(record_path.read_text(encoding="utf-8"))
    report = report_path.read_text(encoding="utf-8")
    assert record["contract_version"] == RECONCILIATION_RECORD_CONTRACT_VERSION
    assert record["errors"] == []
    assert record["warnings"] == []
    assert "# PMBOT Weather Outcome Reconciliation Placeholder" in report
    assert "temperature_threshold_operator_review.operator_review" in report
    assert "Makes no network, LLM, market API, wallet, order, or runtime calls." in report
    assert "Includes no market instruction." in report


def test_operator_report_is_deterministic() -> None:
    request = load_reconciliation_request(VALID_REQUEST_PATH)
    record = build_reconciliation_record(request)

    first = build_operator_report(record)
    second = build_operator_report(deepcopy(record))

    assert first == second
    assert "Operator review: `pending_operator_review`" in first
    assert "Leaves final weather outcome status outside this artifact." in first


def test_request_rejects_network_like_record_reference() -> None:
    request = load_reconciliation_request(VALID_REQUEST_PATH)
    request["observation_records"][0]["local_reference"] = "https://example.invalid/weather.json"

    validation = validate_reconciliation_request(request)

    assert validation.valid is False
    assert any("local_reference must point to a local fixture or static artifact" in error for error in validation.errors)
    with pytest.raises(ReconciliationValidationError):
        build_reconciliation_record(request)


def test_request_rejects_record_reference_outside_allowed_local_paths() -> None:
    request = load_reconciliation_request(VALID_REQUEST_PATH)
    request["observation_records"][0]["local_reference"] = "pm_bot/weather/local_snapshot.json"

    validation = validate_reconciliation_request(request)

    assert validation.valid is False
    assert any("local_reference must stay under an allowed local fixture/static path" in error for error in validation.errors)


def test_request_rejects_unknown_outcome_review_record_reference() -> None:
    request = load_reconciliation_request(VALID_REQUEST_PATH)
    request["outcome_reviews"][0]["record_ids"].append("missing_weather_observation_record")

    validation = validate_reconciliation_request(request)

    assert validation.valid is False
    assert any("references unknown records: missing_weather_observation_record" in error for error in validation.errors)


def test_request_rejects_scoring_or_selection_fields() -> None:
    request = load_reconciliation_request(VALID_REQUEST_PATH)
    request["outcome_reviews"][0]["forecast_score"] = "not allowed in local reconciliation placeholders"

    validation = validate_reconciliation_request(request)

    assert validation.valid is False
    assert any("forbidden scoring/action field detected" in error for error in validation.errors)


def test_output_contract_has_no_scoring_or_selection_fields() -> None:
    request = load_reconciliation_request(VALID_REQUEST_PATH)
    record = build_reconciliation_record(request)

    offending_paths = _find_output_decision_terms(record)

    assert offending_paths == []


def test_reconciliation_request_contract_version_is_explicit() -> None:
    request = load_reconciliation_request(VALID_REQUEST_PATH)

    assert request["contract_version"] == RECONCILIATION_REQUEST_CONTRACT_VERSION


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
