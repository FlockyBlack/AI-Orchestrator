from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from pm_bot.weather.source_monitoring_plan_runner import (
    LOCAL_RUN_MODE,
    OPERATOR_REVIEW_STATE,
    PLAN_CONTRACT_VERSION,
    RUN_REPORT_CONTRACT_VERSION,
    RUNNER_VERDICT,
    PlanValidationError,
    build_run_report,
    load_plan,
    main,
    validate_plan,
)

FIXTURE_DIR = Path(__file__).parent / "fixtures"
VALID_PLAN_PATH = FIXTURE_DIR / "weather_source_monitoring_plan.valid.json"
UNKNOWN_SOURCE_PLAN_PATH = FIXTURE_DIR / "weather_source_monitoring_plan.unknown_source.json"
CLI_OUTPUT_PATH = FIXTURE_DIR / "weather_source_monitoring_run.cli_output.json"


def test_valid_fixture_plan_builds_operator_review_report() -> None:
    plan = load_plan(VALID_PLAN_PATH)
    validation = validate_plan(plan)
    report = build_run_report(plan)

    assert validation.valid is True
    assert validation.errors == ()
    assert report["contract_version"] == RUN_REPORT_CONTRACT_VERSION
    assert report["plan_id"] == "weather_source_monitoring_fixture_001"
    assert report["run_mode"] == LOCAL_RUN_MODE
    assert report["local_only"] is True
    assert report["operator_review_required"] is True
    assert report["summary_counts"] == {"monitoring_items": 1, "sources": 2}
    assert report["source_inventory"][0]["operator_review_status"] == OPERATOR_REVIEW_STATE
    assert report["outcome_monitoring_items"][0]["runner_verdict"] == RUNNER_VERDICT
    assert report["outcome_monitoring_items"][0]["operator_review_status"] == OPERATOR_REVIEW_STATE
    assert report["safety_boundaries"] == {
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


def test_run_report_is_deterministic_for_same_plan() -> None:
    plan = load_plan(VALID_PLAN_PATH)

    first = build_run_report(plan)
    second = build_run_report(deepcopy(plan))

    assert first == second
    assert first["run_id"] == "weather_source_monitoring_fixture_001-9c51b89977c8"


def test_cli_writes_local_report() -> None:
    exit_code = main(["--plan", str(VALID_PLAN_PATH), "--output", str(CLI_OUTPUT_PATH)])

    assert exit_code == 0
    report = json.loads(CLI_OUTPUT_PATH.read_text(encoding="utf-8"))
    assert report["contract_version"] == RUN_REPORT_CONTRACT_VERSION
    assert report["run_mode"] == LOCAL_RUN_MODE
    assert report["errors"] == []
    assert report["warnings"] == []


def test_plan_rejects_network_like_source_reference() -> None:
    plan = load_plan(VALID_PLAN_PATH)
    plan["sources"][0]["local_reference"] = "https://example.invalid/weather.json"

    validation = validate_plan(plan)

    assert validation.valid is False
    assert any("local_reference must point to a local fixture or static artifact" in error for error in validation.errors)
    with pytest.raises(PlanValidationError):
        build_run_report(plan)


def test_plan_rejects_unknown_outcome_source_reference() -> None:
    plan = load_plan(UNKNOWN_SOURCE_PLAN_PATH)

    validation = validate_plan(plan)

    assert validation.valid is False
    assert any("references unknown sources: missing_station_log" in error for error in validation.errors)


def test_plan_rejects_scoring_or_action_fields() -> None:
    plan = load_plan(VALID_PLAN_PATH)
    plan["outcome_checks"][0]["confidence_score"] = "not allowed in local monitoring plans"

    validation = validate_plan(plan)

    assert validation.valid is False
    assert any("forbidden decision/action field detected" in error for error in validation.errors)


def test_output_contract_has_no_scoring_or_action_fields() -> None:
    plan = load_plan(VALID_PLAN_PATH)
    report = build_run_report(plan)

    offending_paths = _find_output_decision_terms(report)

    assert offending_paths == []


def test_plan_contract_version_is_explicit() -> None:
    plan = load_plan(VALID_PLAN_PATH)

    assert plan["contract_version"] == PLAN_CONTRACT_VERSION


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
