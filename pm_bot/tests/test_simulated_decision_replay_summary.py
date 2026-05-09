from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from pm_bot.simulated_decisions.replay_summary import (
    LOCAL_ONLY_SAFETY_BOUNDARIES,
    LOCAL_RUN_MODE,
    OPERATOR_REVIEW_STATUS,
    REPLAY_SUMMARY_CONTRACT_VERSION,
    REPLAY_SUMMARY_REQUEST_CONTRACT_VERSION,
    REPLAY_SUMMARY_SCHEMA_ID,
    REPLAY_SUMMARY_SCHEMA_PATH,
    REPLAY_SUMMARY_STATE,
    SAMPLE_REPLAY_SUMMARY_PATH,
    SimulatedDecisionReplaySummaryValidationError,
    build_operator_report,
    build_simulated_decision_replay_summary,
    build_simulated_decision_replay_summary_schema,
    example_simulated_decision_replay_summary,
    load_replay_summary_request,
    main,
    validate_replay_summary_request,
    validate_simulated_decision_replay_summary,
)

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "simulated_decisions"
VALID_REQUEST_PATH = FIXTURE_DIR / "simulated_decision_replay_summary_request.valid.json"


def test_valid_fixture_request_builds_simulated_decision_replay_summary() -> None:
    request = load_replay_summary_request(VALID_REQUEST_PATH)
    validation = validate_replay_summary_request(request)
    summary = build_simulated_decision_replay_summary(request)

    assert validation.valid is True
    assert validation.errors == ()
    assert summary["contract_version"] == REPLAY_SUMMARY_CONTRACT_VERSION
    assert summary["summary_id"] == "simulated_decision_replay_summary_fixture_001"
    assert summary["run_mode"] == LOCAL_RUN_MODE
    assert summary["summary_state"] == REPLAY_SUMMARY_STATE
    assert summary["local_only"] is True
    assert summary["operator_review_required"] is True
    assert summary["operator_review"]["status"] == OPERATOR_REVIEW_STATUS
    assert summary["summary_counts"] == {
        "errors": 0,
        "local_references": 5,
        "record_section_rows": 1,
        "replay_checks": 3,
        "source_ledgers": 1,
        "source_packets": 1,
        "warnings": 0,
    }
    assert summary["source_ledger_rows"][0] == {
        "artifact_loaded": True,
        "audit_row_count": 3,
        "contract_version": "pmbot_simulated_decision_audit_ledger.v1",
        "error_count": 0,
        "ledger_state": "recorded_for_operator_review",
        "local_reference": "pm_bot/simulated_decisions/samples/simulated_decision_audit_ledger.fixture.json",
        "operator_review_status": OPERATOR_REVIEW_STATUS,
        "record_section_row_count": 1,
        "row_id": "simulated_decision_audit_ledger_fixture_001.source_audit_ledger",
        "row_state": REPLAY_SUMMARY_STATE,
        "source_ledger_id": "simulated_decision_audit_ledger_fixture_001",
        "source_ledger_label": "Static simulated decision audit ledger fixture",
        "source_packet_count": 1,
        "warning_count": 0,
    }
    assert summary["source_packet_rows"][0] == {
        "artifact_loaded": True,
        "contract_version": "pmbot_simulated_decision_packet.v1",
        "error_count": 0,
        "local_reference": "pm_bot/simulated_decisions/samples/simulated_decision_packet.fixture.json",
        "observation_count": 1,
        "operator_review_status": OPERATOR_REVIEW_STATUS,
        "packet_state": "recorded_for_operator_review",
        "record_section_count": 1,
        "row_id": "simulated_decision_audit_ledger_fixture_001.simulated_decision_packet_fixture_001.source_packet",
        "row_state": REPLAY_SUMMARY_STATE,
        "source_ledger_id": "simulated_decision_audit_ledger_fixture_001",
        "source_packet_id": "simulated_decision_packet_fixture_001",
        "source_packet_label": "Static simulated decision packet fixture",
        "warning_count": 0,
    }
    assert summary["record_section_rows"][0] == {
        "local_reference": "pm_bot/simulated_decisions/samples/simulated_decision_packet.fixture.json",
        "observation_count": 1,
        "operator_review_status": OPERATOR_REVIEW_STATUS,
        "row_id": (
            "simulated_decision_audit_ledger_fixture_001."
            "simulated_decision_packet_fixture_001.source_observation_summary"
        ),
        "row_state": REPLAY_SUMMARY_STATE,
        "section_id": "source_observation_summary",
        "section_label": "Source observation summary",
        "source_artifact_ids": ["official_daily_climate_report_snapshot"],
        "source_ledger_id": "simulated_decision_audit_ledger_fixture_001",
        "source_packet_id": "simulated_decision_packet_fixture_001",
    }
    assert summary["safety_boundaries"] == LOCAL_ONLY_SAFETY_BOUNDARIES


def test_replay_summary_is_deterministic_for_same_request() -> None:
    request = load_replay_summary_request(VALID_REQUEST_PATH)

    first = build_simulated_decision_replay_summary(request)
    second = build_simulated_decision_replay_summary(deepcopy(request))

    assert first == second
    assert first["build_id"] == "simulated_decision_replay_summary_fixture_001-7ecf9880131d"


def test_static_sample_matches_builder_output() -> None:
    request = load_replay_summary_request(VALID_REQUEST_PATH)
    sample = json.loads(Path(SAMPLE_REPLAY_SUMMARY_PATH).read_text(encoding="utf-8"))

    assert build_simulated_decision_replay_summary(request) == sample


def test_static_sample_validates_as_replay_summary_artifact() -> None:
    sample = json.loads(Path(SAMPLE_REPLAY_SUMMARY_PATH).read_text(encoding="utf-8"))

    validation = validate_simulated_decision_replay_summary(sample)

    assert validation.valid is True
    assert validation.errors == ()


def test_schema_and_fixture_loaders_return_detached_deterministic_copies() -> None:
    first_schema = build_simulated_decision_replay_summary_schema()
    second_schema = build_simulated_decision_replay_summary_schema()
    first_summary = example_simulated_decision_replay_summary()
    second_summary = example_simulated_decision_replay_summary()

    assert first_schema == second_schema
    assert first_summary == second_summary

    first_schema["schema_id"] = "mutated"
    first_summary["summary_id"] = "mutated"

    assert build_simulated_decision_replay_summary_schema()["schema_id"] == REPLAY_SUMMARY_SCHEMA_ID
    assert example_simulated_decision_replay_summary()["summary_id"] == "simulated_decision_replay_summary_fixture_001"


def test_static_json_files_match_loader_outputs() -> None:
    schema = json.loads(Path(REPLAY_SUMMARY_SCHEMA_PATH).read_text(encoding="utf-8"))
    summary = json.loads(Path(SAMPLE_REPLAY_SUMMARY_PATH).read_text(encoding="utf-8"))

    assert schema == build_simulated_decision_replay_summary_schema()
    assert summary == example_simulated_decision_replay_summary()


def test_cli_writes_local_replay_summary_and_operator_report(tmp_path: Path) -> None:
    summary_path = tmp_path / "simulated_decision_replay_summary.json"
    report_path = tmp_path / "simulated_decision_replay_summary.md"

    exit_code = main(
        [
            "--request",
            str(VALID_REQUEST_PATH),
            "--output-summary",
            str(summary_path),
            "--output-report",
            str(report_path),
        ]
    )

    assert exit_code == 0
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    report = report_path.read_text(encoding="utf-8")
    assert summary["contract_version"] == REPLAY_SUMMARY_CONTRACT_VERSION
    assert summary["errors"] == []
    assert summary["warnings"] == []
    assert "# PMBOT Simulated Decision Replay Summary" in report
    assert "simulated_decision_audit_ledger_fixture_001" in report
    assert "Makes no network, LLM, external market API, wallet, order, transaction endpoint, runtime, worker, scheduler, or browser calls." in report
    assert "Descriptive simulated record replay only" in report


def test_operator_report_is_deterministic() -> None:
    request = load_replay_summary_request(VALID_REQUEST_PATH)
    summary = build_simulated_decision_replay_summary(request)

    first = build_operator_report(summary)
    second = build_operator_report(deepcopy(summary))

    assert first == second
    assert "Operator review: `pending_operator_review`" in first
    assert "Local fixture/static input only." in first


def test_request_rejects_network_like_source_reference() -> None:
    request = load_replay_summary_request(VALID_REQUEST_PATH)
    request["source_audit_ledgers"][0]["local_reference"] = "https://example.invalid/static.json"

    validation = validate_replay_summary_request(request)

    assert validation.valid is False
    assert any("local repository-relative reference" in error for error in validation.errors)
    with pytest.raises(SimulatedDecisionReplaySummaryValidationError):
        build_simulated_decision_replay_summary(request)


def test_request_rejects_reference_outside_allowed_local_paths() -> None:
    request = load_replay_summary_request(VALID_REQUEST_PATH)
    request["source_audit_ledgers"][0]["local_reference"] = "pm_bot/wallet/simulated_decision_audit_ledger.json"

    validation = validate_replay_summary_request(request)

    assert validation.valid is False
    assert any("allowed local paths" in error for error in validation.errors)


def test_request_rejects_operator_review_bypass_state() -> None:
    request = load_replay_summary_request(VALID_REQUEST_PATH)
    request["replay_checks"][0]["operator_review_status"] = "accepted_without_review"

    validation = validate_replay_summary_request(request)

    assert validation.valid is False
    assert any("operator_review_status must be 'pending_operator_review'" in error for error in validation.errors)


def test_builder_rejects_source_ledger_identity_mismatch() -> None:
    request = load_replay_summary_request(VALID_REQUEST_PATH)
    request["source_audit_ledgers"][0]["source_ledger_id"] = "simulated_decision_audit_ledger_fixture_mismatch"

    validation = validate_replay_summary_request(request)

    assert validation.valid is True
    with pytest.raises(SimulatedDecisionReplaySummaryValidationError):
        build_simulated_decision_replay_summary(request)


def test_replay_summary_artifact_validation_rejects_summary_and_review_drift() -> None:
    request = load_replay_summary_request(VALID_REQUEST_PATH)
    summary = build_simulated_decision_replay_summary(request)
    summary["summary_counts"]["source_packets"] = 99
    summary["source_packet_rows"][0]["operator_review_status"] = "accepted_without_review"

    validation = validate_simulated_decision_replay_summary(summary)

    assert validation.valid is False
    assert any("$.summary_counts.source_packets must match replay summary content: 1" in error for error in validation.errors)
    assert any("source_packet_rows[0].operator_review_status must be 'pending_operator_review'" in error for error in validation.errors)


def test_replay_summary_artifact_validation_rejects_safety_boundary_drift() -> None:
    request = load_replay_summary_request(VALID_REQUEST_PATH)
    summary = build_simulated_decision_replay_summary(request)
    summary["safety_boundaries"]["network_calls_allowed"] = True

    validation = validate_simulated_decision_replay_summary(summary)

    assert validation.valid is False
    assert any("closed local-only safety boundary contract" in error for error in validation.errors)


def test_output_contract_has_no_scoring_or_selection_fields() -> None:
    request = load_replay_summary_request(VALID_REQUEST_PATH)
    summary = build_simulated_decision_replay_summary(request)

    assert _find_output_decision_terms(request) == []
    assert _find_output_decision_terms(summary) == []


def test_request_contract_version_is_explicit() -> None:
    request = load_replay_summary_request(VALID_REQUEST_PATH)

    assert request["contract_version"] == REPLAY_SUMMARY_REQUEST_CONTRACT_VERSION


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
