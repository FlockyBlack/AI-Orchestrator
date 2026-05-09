from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from pm_bot.dashboard.local_rehearsal_readiness_dashboard_card import (
    CARD_CONTRACT_VERSION,
    CREATED_AT,
    LOCAL_ONLY_SAFETY_BOUNDARIES,
    LOCAL_RUN_MODE,
    OPERATOR_REVIEW_STATUS,
    REQUEST_CONTRACT_VERSION,
    REQUIRED_VALIDATION_COMMANDS,
    SAMPLE_CARD_PATH,
    SAMPLE_OPERATOR_REPORT_PATH,
    TASK_ID,
    RehearsalReadinessDashboardCardValidationError,
    build_rehearsal_readiness_dashboard_card,
    find_forbidden_card_terms,
    load_card_request,
    main,
    render_operator_card,
    validate_card_request,
    validate_rehearsal_readiness_dashboard_card,
)


DOC_PATH = Path("docs/PMBOT_REHEARSAL_011_REHEARSAL_READINESS_DASHBOARD_CARD_LOCAL_ONLY.md")
REQUEST_PATH = Path("pm_bot/tests/fixtures/rehearsal/pmbot_rehearsal_readiness_dashboard_card_request.valid.json")
SAMPLE_MARKDOWN_PATH = Path(SAMPLE_OPERATOR_REPORT_PATH)
ALLOWED_LOCAL_PREFIXES = ("docs/", "pm_bot/dashboard/", "pm_bot/readiness/", "pm_bot/tests/", "tests/")

EXPECTED_SECTION_IDS = (
    "rehearsal_control_record_section",
    "source_review_case_section",
    "validation_runner_section",
    "dashboard_context_section",
)
EXPECTED_READINESS_ARTIFACT_IDS = (
    "rehearsal_readiness_dashboard_card_document",
    "rehearsal_readiness_dashboard_card_builder",
    "rehearsal_readiness_dashboard_card_contract_test",
    "queue_template_validation_test",
    "rehearsal_ci_safe_validation_runner",
    "rehearsal_validation_replay_packet",
    "read_only_rehearsal_scenario_contract",
    "rehearsal_market_packet_schema",
    "rehearsal_source_evidence_bundle",
    "rehearsal_operator_approval_record",
    "rehearsal_stop_condition_trigger_matrix",
    "rehearsal_staleness_case_set",
    "rehearsal_contradiction_case_set",
    "rehearsal_evidence_retention_ledger",
    "local_supervised_live_readiness_dashboard_sample",
)
EXPECTED_SAFETY_BOUNDARY_IDS = (
    "local_static_material_boundary",
    "endpoint_and_service_boundary",
    "sensitive_path_boundary",
    "execution_wiring_boundary",
)


def test_builder_output_matches_static_fixture() -> None:
    request = _load_request()
    sample = _load_sample()

    assert build_rehearsal_readiness_dashboard_card(request) == sample


def test_static_fixture_has_expected_contract() -> None:
    card = _load_sample()

    assert tuple(card.keys()) == tuple(sorted(card.keys()))
    assert card["task_id"] == TASK_ID
    assert card["card_id"] == "pmbot-rehearsal-readiness-dashboard-card-001"
    assert card["contract_version"] == CARD_CONTRACT_VERSION
    assert card["run_mode"] == LOCAL_RUN_MODE
    assert card["created_at"] == CREATED_AT
    assert card["review_date"] == "2026-05-09"
    assert card["local_only"] is True
    assert card["operator_review_required"] is True
    assert card["operator_review"] == {
        "reviewed_at": None,
        "reviewed_by": None,
        "status": OPERATOR_REVIEW_STATUS,
    }
    assert card["errors"] == []
    assert card["warnings"] == []
    assert validate_rehearsal_readiness_dashboard_card(card).valid is True


def test_card_rows_are_fixed_local_and_pending_review() -> None:
    card = _load_sample()

    assert tuple(record["section_id"] for record in card["card_sections"]) == EXPECTED_SECTION_IDS
    assert tuple(record["artifact_id"] for record in card["readiness_records"]) == EXPECTED_READINESS_ARTIFACT_IDS
    assert tuple(record["boundary_id"] for record in card["safety_records"]) == EXPECTED_SAFETY_BOUNDARY_IDS
    for record in (*card["card_sections"], *card["readiness_records"], *card["safety_records"], *card["validation_records"]):
        assert record["operator_review_status"] == OPERATOR_REVIEW_STATUS
        assert record["runner_state"] == "ready_for_operator_review"
        for reference_field in ("fixture_reference", "local_reference", "source_reference"):
            if reference_field in record:
                _assert_allowed_existing_local_reference(record[reference_field])


def test_safety_boundaries_are_closed_for_rehearsal_readiness_dashboard_card() -> None:
    card = _load_sample()

    assert card["safety_boundaries"] == LOCAL_ONLY_SAFETY_BOUNDARIES
    assert card["safety_boundaries"]["local_fixtures_only"] is True
    assert card["safety_boundaries"]["local_static_samples_only"] is True
    assert card["safety_boundaries"]["operator_review_required"] is True
    assert card["safety_boundaries"]["paper_mode_only"] is True
    assert all(value is False for key, value in card["safety_boundaries"].items() if key.endswith("_allowed"))


def test_validation_commands_are_recorded_for_operator_run_local_checks() -> None:
    card = _load_sample()

    assert card["required_validation_commands"] == list(REQUIRED_VALIDATION_COMMANDS)
    assert card["required_validation_commands"] == [
        "python -m compileall pm_bot tests",
        "pytest pm_bot/tests tests/test_codex_queue_pmbot_templates.py",
    ]
    assert [record["command_label"] for record in card["validation_records"]] == list(REQUIRED_VALIDATION_COMMANDS)
    for record in card["validation_records"]:
        assert record["status"] == "not_run_static_record"
        _assert_allowed_existing_local_reference(record["local_reference"])


def test_summary_counts_match_card_content() -> None:
    card = _load_sample()
    local_references = set()
    for record in (*card["card_sections"], *card["readiness_records"], *card["safety_records"], *card["validation_records"]):
        for reference_field in ("fixture_reference", "local_reference", "source_reference"):
            if reference_field in record:
                local_references.add(record[reference_field])

    assert card["summary_counts"] == {
        "card_sections": len(card["card_sections"]),
        "local_references": len(local_references),
        "operator_review_pending_records": sum(
            1
            for record in (*card["card_sections"], *card["readiness_records"], *card["safety_records"], *card["validation_records"])
            if record["operator_review_status"] == OPERATOR_REVIEW_STATUS
        ),
        "readiness_records": len(card["readiness_records"]),
        "required_validation_commands": len(card["required_validation_commands"]),
        "safety_records": len(card["safety_records"]),
        "validation_records": len(card["validation_records"]),
        "warnings": len(card["warnings"]),
    }


def test_request_card_and_markdown_have_no_forbidden_output_terms() -> None:
    request = _load_request()
    card = _load_sample()
    markdown = render_operator_card(card)

    assert find_forbidden_card_terms(request) == []
    assert find_forbidden_card_terms(card) == []
    assert find_forbidden_card_terms(markdown) == []


def test_operator_card_matches_static_sample_and_is_deterministic() -> None:
    card = _load_sample()

    first = render_operator_card(card)
    second = render_operator_card(deepcopy(card))

    assert first == second
    assert first == SAMPLE_MARKDOWN_PATH.read_text(encoding="utf-8")
    assert "# PMBOT Rehearsal Readiness Dashboard Card" in first
    assert f"Task: `{TASK_ID}`" in first
    assert "Descriptive readiness dashboard card only" in first


def test_cli_writes_rehearsal_readiness_dashboard_card_and_report(tmp_path: Path) -> None:
    card_path = tmp_path / "rehearsal_readiness_dashboard_card.json"
    report_path = tmp_path / "rehearsal_readiness_dashboard_card.md"

    exit_code = main(
        [
            "--request",
            str(REQUEST_PATH),
            "--output-card",
            str(card_path),
            "--output-report",
            str(report_path),
        ]
    )

    assert exit_code == 0
    card = json.loads(card_path.read_text(encoding="utf-8"))
    report = report_path.read_text(encoding="utf-8")
    assert card == build_rehearsal_readiness_dashboard_card(_load_request())
    assert report == render_operator_card(card)
    assert validate_rehearsal_readiness_dashboard_card(card).valid is True


def test_request_validation_rejects_external_reference() -> None:
    request = _load_request()
    request["readiness_records"][0]["local_reference"] = "https://example.invalid/pmbot"

    validation = validate_card_request(request)

    assert validation.valid is False
    assert any("readiness_records[0].local_reference must be a local path" in error for error in validation.errors)
    with pytest.raises(RehearsalReadinessDashboardCardValidationError):
        build_rehearsal_readiness_dashboard_card(request)


def test_request_validation_rejects_forbidden_output_terms() -> None:
    request = _load_request()
    request["readiness_records"][0]["forecast_score"] = "not allowed in a local card"

    validation = validate_card_request(request)

    assert validation.valid is False
    assert any("forbidden rehearsal readiness dashboard card field detected" in error for error in validation.errors)


def test_request_contract_version_is_explicit() -> None:
    request = _load_request()

    assert request["contract_version"] == REQUEST_CONTRACT_VERSION


def test_documentation_registers_card_fixture_and_safety_boundary() -> None:
    document = DOC_PATH.read_text(encoding="utf-8")

    assert f"Task: `{TASK_ID}`" in document
    assert "Card: `pmbot-rehearsal-readiness-dashboard-card-001`" in document
    assert f"Contract: `{CARD_CONTRACT_VERSION}`" in document
    assert str(REQUEST_PATH).replace("\\", "/") in document
    assert SAMPLE_CARD_PATH in document
    assert str(SAMPLE_MARKDOWN_PATH).replace("\\", "/") in document
    assert "No market recommendation, forecast scoring, action guidance, or selection advice." in document
    assert "No probability, EV, edge, or confidence scoring." in document
    assert "This card is not execution approval and is not runtime input." in document


def _load_request() -> dict:
    return load_card_request(REQUEST_PATH)


def _load_sample() -> dict:
    return json.loads(Path(SAMPLE_CARD_PATH).read_text(encoding="utf-8"))


def _assert_allowed_existing_local_reference(local_reference: str) -> None:
    assert "://" not in local_reference
    assert local_reference.startswith(ALLOWED_LOCAL_PREFIXES)
    assert Path(local_reference).exists()
