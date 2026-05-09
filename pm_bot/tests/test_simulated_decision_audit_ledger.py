from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from pm_bot.simulated_decisions.audit_ledger import (
    AUDIT_LEDGER_CONTRACT_VERSION,
    AUDIT_LEDGER_REQUEST_CONTRACT_VERSION,
    AUDIT_LEDGER_SCHEMA_ID,
    AUDIT_LEDGER_SCHEMA_PATH,
    AUDIT_LEDGER_STATE,
    LOCAL_ONLY_SAFETY_BOUNDARIES,
    LOCAL_RUN_MODE,
    OPERATOR_REVIEW_STATUS,
    SAMPLE_AUDIT_LEDGER_PATH,
    SimulatedDecisionAuditLedgerValidationError,
    build_operator_report,
    build_simulated_decision_audit_ledger,
    build_simulated_decision_audit_ledger_schema,
    example_simulated_decision_audit_ledger,
    load_audit_request,
    main,
    validate_audit_request,
    validate_simulated_decision_audit_ledger,
)

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "simulated_decisions"
VALID_REQUEST_PATH = FIXTURE_DIR / "simulated_decision_audit_ledger_request.valid.json"


def test_valid_fixture_request_builds_simulated_decision_audit_ledger() -> None:
    request = load_audit_request(VALID_REQUEST_PATH)
    validation = validate_audit_request(request)
    ledger = build_simulated_decision_audit_ledger(request)

    assert validation.valid is True
    assert validation.errors == ()
    assert ledger["contract_version"] == AUDIT_LEDGER_CONTRACT_VERSION
    assert ledger["ledger_id"] == "simulated_decision_audit_ledger_fixture_001"
    assert ledger["run_mode"] == LOCAL_RUN_MODE
    assert ledger["ledger_state"] == AUDIT_LEDGER_STATE
    assert ledger["local_only"] is True
    assert ledger["operator_review_required"] is True
    assert ledger["operator_review"]["status"] == OPERATOR_REVIEW_STATUS
    assert ledger["summary_counts"] == {
        "audit_requirements": 3,
        "audit_rows": 3,
        "errors": 0,
        "local_references": 4,
        "record_section_rows": 1,
        "source_packets": 1,
        "warnings": 0,
    }
    assert ledger["source_inventory"][0] == {
        "artifact_loaded": True,
        "contract_version": "pmbot_simulated_decision_packet.v1",
        "error_count": 0,
        "local_reference": "pm_bot/simulated_decisions/samples/simulated_decision_packet.fixture.json",
        "observation_count": 1,
        "operator_review_status": OPERATOR_REVIEW_STATUS,
        "packet_state": "recorded_for_operator_review",
        "record_section_count": 1,
        "row_state": AUDIT_LEDGER_STATE,
        "source_packet_id": "simulated_decision_packet_fixture_001",
        "source_packet_label": "Static simulated decision packet fixture",
        "warning_count": 0,
    }
    assert ledger["record_section_rows"][0] == {
        "local_reference": "pm_bot/simulated_decisions/samples/simulated_decision_packet.fixture.json",
        "observation_count": 1,
        "operator_review_status": OPERATOR_REVIEW_STATUS,
        "row_id": "simulated_decision_packet_fixture_001.source_observation_summary",
        "row_state": AUDIT_LEDGER_STATE,
        "section_id": "source_observation_summary",
        "section_label": "Source observation summary",
        "source_artifact_ids": ["official_daily_climate_report_snapshot"],
        "source_packet_id": "simulated_decision_packet_fixture_001",
    }
    assert ledger["safety_boundaries"] == LOCAL_ONLY_SAFETY_BOUNDARIES


def test_audit_ledger_is_deterministic_for_same_request() -> None:
    request = load_audit_request(VALID_REQUEST_PATH)

    first = build_simulated_decision_audit_ledger(request)
    second = build_simulated_decision_audit_ledger(deepcopy(request))

    assert first == second
    assert first["build_id"] == "simulated_decision_audit_ledger_fixture_001-1c53006b42b2"


def test_static_sample_matches_builder_output() -> None:
    request = load_audit_request(VALID_REQUEST_PATH)
    sample = json.loads(Path(SAMPLE_AUDIT_LEDGER_PATH).read_text(encoding="utf-8"))

    assert build_simulated_decision_audit_ledger(request) == sample


def test_static_sample_validates_as_audit_ledger_artifact() -> None:
    sample = json.loads(Path(SAMPLE_AUDIT_LEDGER_PATH).read_text(encoding="utf-8"))

    validation = validate_simulated_decision_audit_ledger(sample)

    assert validation.valid is True
    assert validation.errors == ()


def test_schema_and_fixture_loaders_return_detached_deterministic_copies() -> None:
    first_schema = build_simulated_decision_audit_ledger_schema()
    second_schema = build_simulated_decision_audit_ledger_schema()
    first_ledger = example_simulated_decision_audit_ledger()
    second_ledger = example_simulated_decision_audit_ledger()

    assert first_schema == second_schema
    assert first_ledger == second_ledger

    first_schema["schema_id"] = "mutated"
    first_ledger["ledger_id"] = "mutated"

    assert build_simulated_decision_audit_ledger_schema()["schema_id"] == AUDIT_LEDGER_SCHEMA_ID
    assert example_simulated_decision_audit_ledger()["ledger_id"] == "simulated_decision_audit_ledger_fixture_001"


def test_static_json_files_match_loader_outputs() -> None:
    schema = json.loads(Path(AUDIT_LEDGER_SCHEMA_PATH).read_text(encoding="utf-8"))
    ledger = json.loads(Path(SAMPLE_AUDIT_LEDGER_PATH).read_text(encoding="utf-8"))

    assert schema == build_simulated_decision_audit_ledger_schema()
    assert ledger == example_simulated_decision_audit_ledger()


def test_cli_writes_local_audit_ledger_and_operator_report(tmp_path: Path) -> None:
    ledger_path = tmp_path / "simulated_decision_audit_ledger.json"
    report_path = tmp_path / "simulated_decision_audit_ledger.md"

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
    assert ledger["contract_version"] == AUDIT_LEDGER_CONTRACT_VERSION
    assert ledger["errors"] == []
    assert ledger["warnings"] == []
    assert "# PMBOT Simulated Decision Audit Ledger" in report
    assert "simulated_decision_packet_fixture_001" in report
    assert "Makes no network, LLM, external market API, wallet, order, transaction endpoint, runtime, worker, scheduler, or browser calls." in report
    assert "Descriptive simulated record audit only" in report


def test_operator_report_is_deterministic() -> None:
    request = load_audit_request(VALID_REQUEST_PATH)
    ledger = build_simulated_decision_audit_ledger(request)

    first = build_operator_report(ledger)
    second = build_operator_report(deepcopy(ledger))

    assert first == second
    assert "Operator review: `pending_operator_review`" in first
    assert "Local fixture/static input only." in first


def test_request_rejects_network_like_source_reference() -> None:
    request = load_audit_request(VALID_REQUEST_PATH)
    request["source_packets"][0]["local_reference"] = "https://example.invalid/static.json"

    validation = validate_audit_request(request)

    assert validation.valid is False
    assert any("local repository-relative reference" in error for error in validation.errors)
    with pytest.raises(SimulatedDecisionAuditLedgerValidationError):
        build_simulated_decision_audit_ledger(request)


def test_request_rejects_reference_outside_allowed_local_paths() -> None:
    request = load_audit_request(VALID_REQUEST_PATH)
    request["source_packets"][0]["local_reference"] = "pm_bot/wallet/simulated_decision_packet.json"

    validation = validate_audit_request(request)

    assert validation.valid is False
    assert any("allowed local paths" in error for error in validation.errors)


def test_request_rejects_operator_review_bypass_state() -> None:
    request = load_audit_request(VALID_REQUEST_PATH)
    request["audit_requirements"][0]["operator_review_status"] = "accepted_without_review"

    validation = validate_audit_request(request)

    assert validation.valid is False
    assert any("operator_review_status must be 'pending_operator_review'" in error for error in validation.errors)


def test_builder_rejects_source_packet_identity_mismatch() -> None:
    request = load_audit_request(VALID_REQUEST_PATH)
    request["source_packets"][0]["source_packet_id"] = "simulated_decision_packet_fixture_mismatch"

    validation = validate_audit_request(request)

    assert validation.valid is True
    with pytest.raises(SimulatedDecisionAuditLedgerValidationError):
        build_simulated_decision_audit_ledger(request)


def test_ledger_artifact_validation_rejects_summary_and_review_drift() -> None:
    request = load_audit_request(VALID_REQUEST_PATH)
    ledger = build_simulated_decision_audit_ledger(request)
    ledger["summary_counts"]["audit_rows"] = 99
    ledger["audit_rows"][0]["operator_review_status"] = "accepted_without_review"

    validation = validate_simulated_decision_audit_ledger(ledger)

    assert validation.valid is False
    assert any("$.summary_counts.audit_rows must match ledger content: 3" in error for error in validation.errors)
    assert any("audit_rows[0].operator_review_status must be 'pending_operator_review'" in error for error in validation.errors)


def test_ledger_artifact_validation_rejects_safety_boundary_drift() -> None:
    request = load_audit_request(VALID_REQUEST_PATH)
    ledger = build_simulated_decision_audit_ledger(request)
    ledger["safety_boundaries"]["network_calls_allowed"] = True

    validation = validate_simulated_decision_audit_ledger(ledger)

    assert validation.valid is False
    assert any("closed local-only safety boundary contract" in error for error in validation.errors)


def test_output_contract_has_no_scoring_or_selection_fields() -> None:
    request = load_audit_request(VALID_REQUEST_PATH)
    ledger = build_simulated_decision_audit_ledger(request)

    assert _find_output_decision_terms(request) == []
    assert _find_output_decision_terms(ledger) == []


def test_request_contract_version_is_explicit() -> None:
    request = load_audit_request(VALID_REQUEST_PATH)

    assert request["contract_version"] == AUDIT_LEDGER_REQUEST_CONTRACT_VERSION


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
