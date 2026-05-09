from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from pm_bot.weather.observation_ledger_refresher import build_observation_ledger, load_refresh_request
from pm_bot.weather.operator_review_surface import (
    LOCAL_RUN_MODE,
    OPERATOR_REVIEW_STATUS,
    OPERATOR_REVIEW_SURFACE_CONTRACT_VERSION,
    SURFACE_STATE,
    OperatorReviewSurfaceValidationError,
    build_operator_report,
    build_operator_review_surface,
    load_review_artifact,
    main,
    validate_review_surface_inputs,
)
from pm_bot.weather.outcome_reconciliation_stub import (
    AUTOMATED_OUTCOME_STATUS,
    build_reconciliation_record,
    load_reconciliation_request,
)

FIXTURE_DIR = Path(__file__).parent / "fixtures"
LEDGER_REQUEST_PATH = FIXTURE_DIR / "weather_observation_ledger_refresh_request.valid.json"
RECONCILIATION_REQUEST_PATH = FIXTURE_DIR / "weather_outcome_reconciliation_request.valid.json"


def test_valid_fixture_artifacts_build_operator_review_surface() -> None:
    ledger, reconciliation_record = _fixture_artifacts()

    validation = validate_review_surface_inputs(ledger, reconciliation_record)
    surface = build_operator_review_surface(ledger, reconciliation_record)

    assert validation.valid is True
    assert validation.errors == ()
    assert surface["contract_version"] == OPERATOR_REVIEW_SURFACE_CONTRACT_VERSION
    assert surface["run_mode"] == LOCAL_RUN_MODE
    assert surface["local_only"] is True
    assert surface["operator_review_required"] is True
    assert surface["operator_review"]["status"] == OPERATOR_REVIEW_STATUS
    assert surface["summary_counts"] == {
        "ledger_records": 2,
        "outcome_review_records": 1,
        "reconciliation_inventory_records": 2,
        "record_links": 2,
        "unlinked_ledger_records": 0,
        "warnings": 0,
    }
    assert surface["source_artifacts"] == {
        "ledger_id": "weather_observation_ledger_fixture_001",
        "ledger_refresh_id": ledger["refresh_id"],
        "reconciliation_id": "weather_outcome_reconciliation_fixture_001",
        "reconciliation_run_id": reconciliation_record["run_id"],
    }
    assert surface["ledger_record_panels"][0] == {
        "inspection_points": [
            "Confirm the local source artifact path is expected.",
            "Confirm the station, date, value, unit, and source timestamp are visible.",
            "Confirm the record remains pending operator review.",
        ],
        "local_reference": "pm_bot/tests/fixtures/weather/official_daily_climate_report_snapshot.json",
        "measurement_name": "daily_high_temperature",
        "observation_date": "2026-05-09",
        "operator_review_status": OPERATOR_REVIEW_STATUS,
        "panel_id": "ledger_record.official_daily_climate_report.2026-05-09.KNYC.daily_high_temperature",
        "record_id": "official_daily_climate_report.2026-05-09.KNYC.daily_high_temperature",
        "referenced_by_review_ids": [
            "weather_outcome_reconciliation_fixture_001.temperature_threshold_operator_review.operator_review"
        ],
        "reported_value": 74,
        "runner_state": SURFACE_STATE,
        "snapshot_id": "fixture_official_daily_climate_report_2026_05_09",
        "source_id": "official_daily_climate_report",
        "source_label": "Official daily climate report",
        "source_timestamp": "2026-05-10T00:05:00Z",
        "source_type": "official_record_snapshot",
        "station_id": "KNYC",
        "unit": "F",
    }
    assert surface["record_link_panels"][0]["reconciliation_inventory_present"] is True
    assert surface["reconciliation_review_panels"][0]["automated_outcome_status"] == AUTOMATED_OUTCOME_STATUS
    assert surface["safety_boundaries"] == {
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
        "weather_outcome_evaluation_allowed": False,
    }


def test_operator_review_surface_is_deterministic_for_same_inputs() -> None:
    ledger, reconciliation_record = _fixture_artifacts()

    first = build_operator_review_surface(ledger, reconciliation_record)
    second = build_operator_review_surface(deepcopy(ledger), deepcopy(reconciliation_record))

    assert first == second
    assert first["surface_id"].startswith(
        "weather_observation_ledger_fixture_001.weather_outcome_reconciliation_fixture_001-"
    )


def test_cli_writes_local_surface_and_operator_report(tmp_path: Path) -> None:
    ledger, reconciliation_record = _fixture_artifacts()
    ledger_path = tmp_path / "weather_observation_ledger.json"
    reconciliation_path = tmp_path / "weather_outcome_reconciliation_record.json"
    surface_path = tmp_path / "weather_operator_review_surface.json"
    report_path = tmp_path / "weather_operator_review_surface.md"
    _write_json(ledger_path, ledger)
    _write_json(reconciliation_path, reconciliation_record)

    exit_code = main(
        [
            "--ledger",
            str(ledger_path),
            "--reconciliation-record",
            str(reconciliation_path),
            "--output-surface",
            str(surface_path),
            "--output-report",
            str(report_path),
        ]
    )

    assert exit_code == 0
    surface = json.loads(surface_path.read_text(encoding="utf-8"))
    report = report_path.read_text(encoding="utf-8")
    assert surface["contract_version"] == OPERATOR_REVIEW_SURFACE_CONTRACT_VERSION
    assert surface["errors"] == []
    assert surface["warnings"] == []
    assert "# PMBOT Weather Operator Review Surface" in report
    assert "official_daily_climate_report.2026-05-09.KNYC.daily_high_temperature" in report
    assert "temperature_threshold_operator_review.operator_review" in report
    assert "Makes no network, LLM, market API, wallet, order, or runtime calls." in report


def test_operator_report_is_deterministic() -> None:
    ledger, reconciliation_record = _fixture_artifacts()
    surface = build_operator_review_surface(ledger, reconciliation_record)

    first = build_operator_report(surface)
    second = build_operator_report(deepcopy(surface))

    assert first == second
    assert "Operator review: `pending_operator_review`" in first
    assert "Does not evaluate weather outcomes or provide trade action guidance." in first


def test_surface_rejects_reconciliation_record_value_that_differs_from_ledger() -> None:
    ledger, reconciliation_record = _fixture_artifacts()
    reconciliation_record["record_inventory"][0]["reported_value"] = 72

    validation = validate_review_surface_inputs(ledger, reconciliation_record)

    assert validation.valid is False
    assert any(
        "differs between ledger and reconciliation: reported_value" in error
        for error in validation.errors
    )
    with pytest.raises(OperatorReviewSurfaceValidationError):
        build_operator_review_surface(ledger, reconciliation_record)


def test_surface_rejects_reconciliation_record_missing_from_ledger() -> None:
    ledger, reconciliation_record = _fixture_artifacts()
    reconciliation_record["record_inventory"][0]["record_id"] = "missing_weather_observation_record"

    validation = validate_review_surface_inputs(ledger, reconciliation_record)

    assert validation.valid is False
    assert any(
        "record_inventory references records missing from ledger: missing_weather_observation_record" in error
        for error in validation.errors
    )


def test_surface_rejects_network_like_artifact_path() -> None:
    with pytest.raises(OperatorReviewSurfaceValidationError) as exc_info:
        load_review_artifact("https://example.invalid/weather_observation_ledger.json")

    assert exc_info.value.errors == ("artifact path must be local",)


def test_surface_rejects_forbidden_artifact_path_before_reading() -> None:
    with pytest.raises(OperatorReviewSurfaceValidationError) as exc_info:
        load_review_artifact(".env")

    assert exc_info.value.errors == ("artifact path is outside the weather review surface boundary",)


def test_surface_output_contract_has_no_scoring_or_selection_fields() -> None:
    ledger, reconciliation_record = _fixture_artifacts()
    surface = build_operator_review_surface(ledger, reconciliation_record)

    offending_paths = _find_output_decision_terms(surface)

    assert offending_paths == []


def _fixture_artifacts() -> tuple[dict, dict]:
    ledger_request = load_refresh_request(LEDGER_REQUEST_PATH)
    reconciliation_request = load_reconciliation_request(RECONCILIATION_REQUEST_PATH)
    return build_observation_ledger(ledger_request), build_reconciliation_record(reconciliation_request)


def _write_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


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
