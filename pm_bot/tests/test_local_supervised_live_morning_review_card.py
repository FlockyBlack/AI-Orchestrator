from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from pm_bot.dashboard.local_supervised_live_morning_review_card import (
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
    SupervisedLiveMorningReviewCardValidationError,
    build_supervised_live_morning_review_card,
    find_forbidden_card_terms,
    load_card_request,
    main,
    render_operator_card,
    validate_card_request,
    validate_supervised_live_morning_review_card,
)


DOC_PATH = Path("docs/PMBOT_OPERATOR_003_SUPERVISED_LIVE_MORNING_REVIEW_CARD_LOCAL_ONLY.md")
REQUEST_PATH = Path("pm_bot/tests/fixtures/operator/supervised_live_morning_review_card_request.valid.json")
SAMPLE_MARKDOWN_PATH = Path(SAMPLE_OPERATOR_REPORT_PATH)

EXPECTED_SECTION_IDS = (
    "readiness_dashboard_section",
    "readiness_evidence_section",
    "safety_boundary_section",
    "validation_replay_section",
)
EXPECTED_REVIEW_ARTIFACT_IDS = (
    "local_supervised_live_readiness_dashboard",
    "supervised_live_readiness_evidence_bundle",
    "read_only_live_data_contract",
    "live_data_source_inventory",
    "operator_approval_gate_record",
    "supervised_live_stop_condition_spec",
    "local_to_supervised_live_gap_matrix",
    "sensitive_path_exclusion_audit",
    "ci_safe_validation_subset",
    "saved_evidence_replay_bundle",
)
EXPECTED_SAFETY_BOUNDARY_IDS = (
    "local_static_source_boundary",
    "sensitive_path_boundary",
    "language_boundary",
    "runtime_transition_boundary",
)
ALLOWED_LOCAL_PREFIXES = ("docs/", "pm_bot/dashboard/", "pm_bot/readiness/", "pm_bot/tests/", "tests/")


def test_builder_output_matches_static_fixture() -> None:
    request = _load_request()
    sample = _load_sample()

    assert build_supervised_live_morning_review_card(request) == sample


def test_static_fixture_has_expected_contract() -> None:
    card = _load_sample()

    assert tuple(card.keys()) == tuple(sorted(card.keys()))
    assert card["task_id"] == TASK_ID
    assert card["card_id"] == "pmbot_supervised_live_morning_review_card_fixture_001"
    assert card["contract_version"] == CARD_CONTRACT_VERSION
    assert card["run_mode"] == LOCAL_RUN_MODE
    assert card["created_at"] == CREATED_AT
    assert card["review_date"] == "2026-05-09"
    assert card["local_only"] is True
    assert card["operator_review_required"] is True
    assert card["operator_review"] == {
        "required": True,
        "reviewed_at": None,
        "reviewed_by": None,
        "status": OPERATOR_REVIEW_STATUS,
    }
    assert card["errors"] == []
    assert card["warnings"] == []
    assert validate_supervised_live_morning_review_card(card).valid is True


def test_card_sections_and_records_are_fixed_local_and_pending_review() -> None:
    card = _load_sample()

    assert tuple(record["section_id"] for record in card["card_sections"]) == EXPECTED_SECTION_IDS
    assert tuple(record["artifact_id"] for record in card["review_records"]) == EXPECTED_REVIEW_ARTIFACT_IDS
    assert tuple(record["boundary_id"] for record in card["safety_records"]) == EXPECTED_SAFETY_BOUNDARY_IDS
    for record in (*card["card_sections"], *card["review_records"], *card["safety_records"], *card["validation_records"]):
        assert record["operator_review_status"] == OPERATOR_REVIEW_STATUS
        assert record["runner_state"] == "ready_for_operator_review"
        for reference_field in ("fixture_reference", "local_reference", "source_reference"):
            if reference_field in record:
                assert "://" not in record[reference_field]
                assert record[reference_field].startswith(ALLOWED_LOCAL_PREFIXES)
                assert Path(record[reference_field]).exists()


def test_safety_boundaries_are_closed_for_supervised_live_morning_review_card() -> None:
    card = _load_sample()

    assert card["safety_boundaries"] == LOCAL_ONLY_SAFETY_BOUNDARIES
    assert card["safety_boundaries"]["local_static_samples_only"] is True
    assert card["safety_boundaries"]["paper_mode_only"] is True
    assert card["safety_boundaries"]["operator_review_required"] is True
    assert all(value is False for key, value in LOCAL_ONLY_SAFETY_BOUNDARIES.items() if key.endswith("_allowed"))


def test_validation_commands_are_recorded_for_operator_run_local_checks() -> None:
    card = _load_sample()

    assert card["required_validation_commands"] == list(REQUIRED_VALIDATION_COMMANDS)
    assert card["required_validation_commands"] == [
        "python -m compileall pm_bot tests",
        "pytest pm_bot/tests tests/test_codex_queue_pmbot_templates.py",
    ]
    assert [record["command_label"] for record in card["validation_records"]] == list(REQUIRED_VALIDATION_COMMANDS)


def test_summary_counts_match_card_content() -> None:
    card = _load_sample()
    local_references = set()
    for record in (*card["card_sections"], *card["review_records"], *card["safety_records"], *card["validation_records"]):
        for reference_field in ("fixture_reference", "local_reference", "source_reference"):
            if reference_field in record:
                local_references.add(record[reference_field])

    assert card["summary_counts"] == {
        "card_sections": len(card["card_sections"]),
        "local_references": len(local_references),
        "operator_review_pending_records": sum(
            1
            for record in (*card["card_sections"], *card["review_records"], *card["safety_records"], *card["validation_records"])
            if record["operator_review_status"] == OPERATOR_REVIEW_STATUS
        ),
        "required_validation_commands": len(card["required_validation_commands"]),
        "review_records": len(card["review_records"]),
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
    assert "# PMBOT Supervised Live Morning Review Card" in first
    assert f"Task: `{TASK_ID}`" in first
    assert "Descriptive operator review card only" in first


def test_cli_writes_local_supervised_live_morning_review_card_and_report(tmp_path: Path) -> None:
    card_path = tmp_path / "local_supervised_live_morning_review_card.json"
    report_path = tmp_path / "local_supervised_live_morning_review_card.md"

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
    assert card == build_supervised_live_morning_review_card(_load_request())
    assert report == render_operator_card(card)
    assert validate_supervised_live_morning_review_card(card).valid is True


def test_request_validation_rejects_external_reference() -> None:
    request = _load_request()
    request["review_records"][0]["fixture_reference"] = "https://example.invalid/pmbot"

    validation = validate_card_request(request)

    assert validation.valid is False
    assert any("review_records[0].fixture_reference must be a local path" in error for error in validation.errors)
    with pytest.raises(SupervisedLiveMorningReviewCardValidationError):
        build_supervised_live_morning_review_card(request)


def test_request_validation_rejects_forbidden_output_terms() -> None:
    request = _load_request()
    request["review_records"][0]["forecast_score"] = "not allowed in a local card"

    validation = validate_card_request(request)

    assert validation.valid is False
    assert any("forbidden supervised-live morning review card field detected" in error for error in validation.errors)


def test_request_contract_version_is_explicit() -> None:
    request = _load_request()

    assert request["contract_version"] == REQUEST_CONTRACT_VERSION


def test_documentation_registers_card_fixture_and_safety_boundary() -> None:
    document = DOC_PATH.read_text(encoding="utf-8")

    assert f"Task: `{TASK_ID}`" in document
    assert "Card: `pmbot_supervised_live_morning_review_card_fixture_001`" in document
    assert f"Contract: `{CARD_CONTRACT_VERSION}`" in document
    assert str(REQUEST_PATH).replace("\\", "/") in document
    assert SAMPLE_CARD_PATH in document
    assert str(SAMPLE_MARKDOWN_PATH).replace("\\", "/") in document
    assert "No forecast scoring, action guidance, market ranking, numeric prediction metric" in document
    assert "This card is not execution approval and is not runtime input." in document


def _load_request() -> dict:
    return load_card_request(REQUEST_PATH)


def _load_sample() -> dict:
    return json.loads(Path(SAMPLE_CARD_PATH).read_text(encoding="utf-8"))
