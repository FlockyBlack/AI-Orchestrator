from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from pm_bot.simulated_decisions.outcome_replay_links import (
    LOCAL_ONLY_SAFETY_BOUNDARIES,
    LOCAL_RUN_MODE,
    OPERATOR_REVIEW_STATUS,
    OUTCOME_REPLAY_LINKS_CONTRACT_VERSION,
    OUTCOME_REPLAY_LINKS_REQUEST_CONTRACT_VERSION,
    OUTCOME_REPLAY_LINKS_SCHEMA_ID,
    OUTCOME_REPLAY_LINKS_SCHEMA_PATH,
    OUTCOME_REPLAY_LINKS_STATE,
    SAMPLE_OUTCOME_REPLAY_LINKS_PATH,
    SimulatedDecisionOutcomeReplayLinksValidationError,
    build_operator_report,
    build_simulated_decision_outcome_replay_links,
    build_simulated_decision_outcome_replay_links_schema,
    example_simulated_decision_outcome_replay_links,
    load_outcome_replay_links_request,
    main,
    validate_outcome_replay_links_request,
    validate_simulated_decision_outcome_replay_links,
)

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "simulated_decisions"
VALID_REQUEST_PATH = FIXTURE_DIR / "simulated_decision_outcome_replay_links_request.valid.json"
STATIC_REPORT_PATH = Path("pm_bot/simulated_decisions/samples/simulated_decision_outcome_replay_links.fixture.md")


def test_valid_fixture_request_builds_simulated_decision_outcome_replay_links() -> None:
    request = load_outcome_replay_links_request(VALID_REQUEST_PATH)
    validation = validate_outcome_replay_links_request(request)
    links = build_simulated_decision_outcome_replay_links(request)

    assert validation.valid is True
    assert validation.errors == ()
    assert links["contract_version"] == OUTCOME_REPLAY_LINKS_CONTRACT_VERSION
    assert links["links_id"] == "simulated_decision_outcome_replay_links_fixture_001"
    assert links["run_mode"] == LOCAL_RUN_MODE
    assert links["links_state"] == OUTCOME_REPLAY_LINKS_STATE
    assert links["local_only"] is True
    assert links["operator_review_required"] is True
    assert links["operator_review"]["status"] == OPERATOR_REVIEW_STATUS
    assert links["summary_counts"] == {
        "decision_to_outcome_links": 1,
        "errors": 0,
        "link_requirements": 3,
        "local_references": 2,
        "outcome_artifacts": 1,
        "source_packets": 1,
        "source_summaries": 1,
        "warnings": 0,
    }
    assert links["source_summary_rows"][0] == {
        "artifact_loaded": True,
        "contract_version": "pmbot_simulated_decision_replay_summary.v1",
        "error_count": 0,
        "local_reference": "pm_bot/simulated_decisions/samples/simulated_decision_replay_summary.fixture.json",
        "local_reference_count": 5,
        "operator_review_status": OPERATOR_REVIEW_STATUS,
        "record_section_row_count": 1,
        "replay_check_count": 3,
        "row_id": "simulated_decision_replay_summary_fixture_001.source_replay_summary",
        "row_state": OUTCOME_REPLAY_LINKS_STATE,
        "source_packet_count": 1,
        "source_summary_id": "simulated_decision_replay_summary_fixture_001",
        "source_summary_label": "Static simulated decision replay summary fixture",
        "summary_state": "recorded_for_operator_review",
        "warning_count": 0,
    }
    assert links["outcome_artifact_rows"][0] == {
        "artifact_loaded": True,
        "artifact_role": "weather_outcome_reconciliation_request",
        "contract_version": "pmbot_weather_outcome_reconciliation_request.v1",
        "error_count": 0,
        "local_reference": "pm_bot/tests/fixtures/weather_outcome_reconciliation_request.valid.json",
        "observation_record_count": 2,
        "operator_review_status": OPERATOR_REVIEW_STATUS,
        "outcome_artifact_id": "weather_outcome_reconciliation_request_fixture_001",
        "outcome_artifact_label": "Static weather outcome reconciliation request fixture",
        "outcome_review_count": 1,
        "row_id": "weather_outcome_reconciliation_request_fixture_001.outcome_artifact",
        "row_state": OUTCOME_REPLAY_LINKS_STATE,
        "warning_count": 0,
    }
    assert links["decision_to_outcome_link_rows"][0] == {
        "decision_record_reference": "pm_bot/simulated_decisions/samples/simulated_decision_packet.fixture.json",
        "link_basis": "market_fixture_and_observation_record_ids",
        "linked_section_ids": ["source_observation_summary"],
        "operator_review_status": OPERATOR_REVIEW_STATUS,
        "outcome_artifact_id": "weather_outcome_reconciliation_request_fixture_001",
        "outcome_artifact_label": "Static weather outcome reconciliation request fixture",
        "outcome_artifact_reference": "pm_bot/tests/fixtures/weather_outcome_reconciliation_request.valid.json",
        "outcome_record_ids": [
            "airport_station_observation_log.2026-05-09.KNYC.daily_high_temperature",
            "official_daily_climate_report.2026-05-09.KNYC.daily_high_temperature",
        ],
        "outcome_review_ids": ["temperature_threshold_operator_review"],
        "row_id": (
            "simulated_decision_replay_summary_fixture_001.simulated_decision_packet_fixture_001."
            "weather_outcome_reconciliation_request_fixture_001.replay_link"
        ),
        "row_state": OUTCOME_REPLAY_LINKS_STATE,
        "source_artifact_ids": ["official_daily_climate_report_snapshot"],
        "source_packet_id": "simulated_decision_packet_fixture_001",
        "source_packet_label": "Static simulated decision packet fixture",
        "source_summary_id": "simulated_decision_replay_summary_fixture_001",
    }
    assert links["safety_boundaries"] == LOCAL_ONLY_SAFETY_BOUNDARIES


def test_outcome_replay_links_are_deterministic_for_same_request() -> None:
    request = load_outcome_replay_links_request(VALID_REQUEST_PATH)

    first = build_simulated_decision_outcome_replay_links(request)
    second = build_simulated_decision_outcome_replay_links(deepcopy(request))

    assert first == second
    assert first["build_id"] == "simulated_decision_outcome_replay_links_fixture_001-4a5042fa723e"


def test_static_sample_matches_builder_output() -> None:
    request = load_outcome_replay_links_request(VALID_REQUEST_PATH)
    sample = json.loads(Path(SAMPLE_OUTCOME_REPLAY_LINKS_PATH).read_text(encoding="utf-8"))

    assert build_simulated_decision_outcome_replay_links(request) == sample


def test_static_sample_validates_as_outcome_replay_links_artifact() -> None:
    sample = json.loads(Path(SAMPLE_OUTCOME_REPLAY_LINKS_PATH).read_text(encoding="utf-8"))

    validation = validate_simulated_decision_outcome_replay_links(sample)

    assert validation.valid is True
    assert validation.errors == ()


def test_schema_and_fixture_loaders_return_detached_deterministic_copies() -> None:
    first_schema = build_simulated_decision_outcome_replay_links_schema()
    second_schema = build_simulated_decision_outcome_replay_links_schema()
    first_links = example_simulated_decision_outcome_replay_links()
    second_links = example_simulated_decision_outcome_replay_links()

    assert first_schema == second_schema
    assert first_links == second_links

    first_schema["schema_id"] = "mutated"
    first_links["links_id"] = "mutated"

    assert build_simulated_decision_outcome_replay_links_schema()["schema_id"] == OUTCOME_REPLAY_LINKS_SCHEMA_ID
    assert example_simulated_decision_outcome_replay_links()["links_id"] == (
        "simulated_decision_outcome_replay_links_fixture_001"
    )


def test_static_json_files_match_loader_outputs() -> None:
    schema = json.loads(Path(OUTCOME_REPLAY_LINKS_SCHEMA_PATH).read_text(encoding="utf-8"))
    links = json.loads(Path(SAMPLE_OUTCOME_REPLAY_LINKS_PATH).read_text(encoding="utf-8"))

    assert schema == build_simulated_decision_outcome_replay_links_schema()
    assert links == example_simulated_decision_outcome_replay_links()


def test_static_report_matches_builder_output() -> None:
    request = load_outcome_replay_links_request(VALID_REQUEST_PATH)
    links = build_simulated_decision_outcome_replay_links(request)

    assert STATIC_REPORT_PATH.read_text(encoding="utf-8") == build_operator_report(links)


def test_cli_writes_local_outcome_replay_links_and_operator_report(tmp_path: Path) -> None:
    links_path = tmp_path / "simulated_decision_outcome_replay_links.json"
    report_path = tmp_path / "simulated_decision_outcome_replay_links.md"

    exit_code = main(
        [
            "--request",
            str(VALID_REQUEST_PATH),
            "--output-links",
            str(links_path),
            "--output-report",
            str(report_path),
        ]
    )

    assert exit_code == 0
    links = json.loads(links_path.read_text(encoding="utf-8"))
    report = report_path.read_text(encoding="utf-8")
    assert links["contract_version"] == OUTCOME_REPLAY_LINKS_CONTRACT_VERSION
    assert links["errors"] == []
    assert links["warnings"] == []
    assert "# PMBOT Simulated Decision To Outcome Replay Links" in report
    assert "weather_outcome_reconciliation_request_fixture_001" in report
    assert "Makes no network, LLM, external market API, wallet, order, transaction endpoint, runtime, worker, scheduler, or browser calls." in report
    assert "Leaves any final outcome record outside this artifact." in report


def test_operator_report_is_deterministic() -> None:
    request = load_outcome_replay_links_request(VALID_REQUEST_PATH)
    links = build_simulated_decision_outcome_replay_links(request)

    first = build_operator_report(links)
    second = build_operator_report(deepcopy(links))

    assert first == second
    assert "Operator review: `pending_operator_review`" in first
    assert "Local fixture/static input only." in first


def test_request_rejects_network_like_outcome_reference() -> None:
    request = load_outcome_replay_links_request(VALID_REQUEST_PATH)
    request["outcome_artifacts"][0]["local_reference"] = "https://example.invalid/static.json"

    validation = validate_outcome_replay_links_request(request)

    assert validation.valid is False
    assert any("local repository-relative reference" in error for error in validation.errors)
    with pytest.raises(SimulatedDecisionOutcomeReplayLinksValidationError):
        build_simulated_decision_outcome_replay_links(request)


def test_request_rejects_reference_outside_allowed_local_paths() -> None:
    request = load_outcome_replay_links_request(VALID_REQUEST_PATH)
    request["source_replay_summaries"][0]["local_reference"] = "pm_bot/wallet/simulated_decision_replay_summary.json"

    validation = validate_outcome_replay_links_request(request)

    assert validation.valid is False
    assert any("allowed local paths" in error for error in validation.errors)


def test_request_rejects_operator_review_bypass_state() -> None:
    request = load_outcome_replay_links_request(VALID_REQUEST_PATH)
    request["link_requirements"][0]["operator_review_status"] = "accepted_without_review"

    validation = validate_outcome_replay_links_request(request)

    assert validation.valid is False
    assert any("operator_review_status must be 'pending_operator_review'" in error for error in validation.errors)


def test_builder_rejects_source_summary_identity_mismatch() -> None:
    request = load_outcome_replay_links_request(VALID_REQUEST_PATH)
    request["source_replay_summaries"][0]["source_summary_id"] = "simulated_decision_replay_summary_fixture_mismatch"

    validation = validate_outcome_replay_links_request(request)

    assert validation.valid is True
    with pytest.raises(SimulatedDecisionOutcomeReplayLinksValidationError):
        build_simulated_decision_outcome_replay_links(request)


def test_builder_rejects_outcome_artifact_contract_mismatch() -> None:
    request = load_outcome_replay_links_request(VALID_REQUEST_PATH)
    request["outcome_artifacts"][0]["expected_contract_version"] = "pmbot_static_artifact.v1"

    validation = validate_outcome_replay_links_request(request)

    assert validation.valid is True
    with pytest.raises(SimulatedDecisionOutcomeReplayLinksValidationError):
        build_simulated_decision_outcome_replay_links(request)


def test_outcome_replay_links_validation_rejects_summary_and_review_drift() -> None:
    request = load_outcome_replay_links_request(VALID_REQUEST_PATH)
    links = build_simulated_decision_outcome_replay_links(request)
    links["summary_counts"]["outcome_artifacts"] = 99
    links["outcome_artifact_rows"][0]["operator_review_status"] = "accepted_without_review"

    validation = validate_simulated_decision_outcome_replay_links(links)

    assert validation.valid is False
    assert any("$.summary_counts.outcome_artifacts must match outcome replay links content: 1" in error for error in validation.errors)
    assert any("outcome_artifact_rows[0].operator_review_status must be 'pending_operator_review'" in error for error in validation.errors)


def test_outcome_replay_links_validation_rejects_safety_boundary_drift() -> None:
    request = load_outcome_replay_links_request(VALID_REQUEST_PATH)
    links = build_simulated_decision_outcome_replay_links(request)
    links["safety_boundaries"]["network_calls_allowed"] = True

    validation = validate_simulated_decision_outcome_replay_links(links)

    assert validation.valid is False
    assert any("closed local-only safety boundary contract" in error for error in validation.errors)


def test_request_rejects_scoring_or_selection_fields() -> None:
    request = load_outcome_replay_links_request(VALID_REQUEST_PATH)
    request["outcome_artifacts"][0]["forecast_score"] = "not allowed"

    validation = validate_outcome_replay_links_request(request)

    assert validation.valid is False
    assert any("forbidden output field detected" in error for error in validation.errors)


def test_output_contract_has_no_scoring_or_selection_fields() -> None:
    request = load_outcome_replay_links_request(VALID_REQUEST_PATH)
    links = build_simulated_decision_outcome_replay_links(request)

    assert _find_output_decision_terms(request) == []
    assert _find_output_decision_terms(links) == []


def test_request_contract_version_is_explicit() -> None:
    request = load_outcome_replay_links_request(VALID_REQUEST_PATH)

    assert request["contract_version"] == OUTCOME_REPLAY_LINKS_REQUEST_CONTRACT_VERSION


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
