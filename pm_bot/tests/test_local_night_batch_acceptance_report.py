from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from pm_bot.dashboard.local_night_batch_acceptance_report import (
    LOCAL_ONLY_SAFETY_BOUNDARIES,
    LOCAL_RUN_MODE,
    OPERATOR_REVIEW_STATUS,
    REPORT_CONTRACT_VERSION,
    REQUEST_CONTRACT_VERSION,
    REQUIRED_VALIDATION_COMMANDS,
    SAMPLE_REPORT_PATH,
    TASK_ID,
    NightBatchAcceptanceReportValidationError,
    build_acceptance_report,
    find_blocked_output_terms,
    load_acceptance_report_request,
    main,
    render_operator_report,
    validate_acceptance_report,
    validate_acceptance_report_request,
)


DOC_PATH = Path("docs/PMBOT_OPERATOR_002_NIGHT_BATCH_ACCEPTANCE_REPORT_LOCAL_ONLY.md")
REQUEST_PATH = Path("pm_bot/tests/fixtures/operator/night_batch_acceptance_report_request.valid.json")
SAMPLE_MARKDOWN_PATH = Path("pm_bot/dashboard/samples/local_night_batch_acceptance_report.fixture.md")

EXPECTED_SECTION_IDS = (
    "queue_template_section",
    "operator_pack_section",
    "postrun_audit_section",
    "dashboard_surface_section",
    "validation_section",
)
EXPECTED_ACCEPTANCE_IDS = (
    "night_batch_task_inventory",
    "postrun_audit_visibility",
    "morning_pack_visibility",
    "result_packet_contract_visibility",
    "validation_command_visibility",
)
ALLOWED_LOCAL_PREFIXES = ("docs/", "pm_bot/dashboard/", "pm_bot/tests/", "tests/")


def test_builder_output_matches_static_fixture() -> None:
    request = _load_request()
    sample = _load_sample()

    assert build_acceptance_report(request) == sample


def test_static_fixture_has_expected_contract() -> None:
    report = _load_sample()

    assert tuple(report.keys()) == tuple(sorted(report.keys()))
    assert report["task_id"] == TASK_ID
    assert report["acceptance_report_id"] == "pmbot_night_batch_acceptance_report_fixture_001"
    assert report["contract_version"] == REPORT_CONTRACT_VERSION
    assert report["run_mode"] == LOCAL_RUN_MODE
    assert report["created_at"] == "2026-05-09T00:00:00Z"
    assert report["review_date"] == "2026-05-09"
    assert report["local_only"] is True
    assert report["operator_review_required"] is True
    assert report["operator_acceptance"]["status"] == OPERATOR_REVIEW_STATUS
    assert report["operator_acceptance"]["required"] is True
    assert report["errors"] == []
    assert report["warnings"] == []
    assert validate_acceptance_report(report).valid is True


def test_report_sections_and_acceptance_records_are_fixed_local_and_pending_review() -> None:
    report = _load_sample()

    assert tuple(record["section_id"] for record in report["report_sections"]) == EXPECTED_SECTION_IDS
    assert tuple(record["acceptance_id"] for record in report["acceptance_review"]) == EXPECTED_ACCEPTANCE_IDS
    for record in (*report["report_sections"], *report["acceptance_review"], *report["validation_review"]):
        assert record["operator_review_status"] == OPERATOR_REVIEW_STATUS
        assert record["runner_state"] == "ready_for_operator_review"
        for reference_field in ("local_reference", "source_fixture_reference", "evidence_reference"):
            if reference_field in record:
                assert "://" not in record[reference_field]
                assert record[reference_field].startswith(ALLOWED_LOCAL_PREFIXES)


def test_safety_boundaries_are_closed_for_night_batch_acceptance_report() -> None:
    report = _load_sample()

    assert report["safety_boundaries"] == LOCAL_ONLY_SAFETY_BOUNDARIES
    assert report["safety_boundaries"]["local_static_samples_only"] is True
    assert report["safety_boundaries"]["paper_mode_only"] is True
    assert report["safety_boundaries"]["operator_review_required"] is True
    assert all(value is False for key, value in LOCAL_ONLY_SAFETY_BOUNDARIES.items() if key.endswith("_allowed"))


def test_validation_commands_are_recorded_for_operator_run_local_checks() -> None:
    report = _load_sample()

    assert report["required_validation_commands"] == list(REQUIRED_VALIDATION_COMMANDS)
    assert report["required_validation_commands"] == [
        "python -m compileall pm_bot tests",
        "pytest pm_bot/tests tests/test_codex_queue_pmbot_templates.py",
    ]
    assert [record["command_label"] for record in report["validation_review"]] == list(REQUIRED_VALIDATION_COMMANDS)


def test_summary_counts_match_report_content() -> None:
    report = _load_sample()
    local_references = set()
    for record in (*report["report_sections"], *report["acceptance_review"], *report["validation_review"]):
        for reference_field in ("local_reference", "source_fixture_reference", "evidence_reference"):
            if reference_field in record:
                local_references.add(record[reference_field])

    assert report["summary_counts"] == {
        "acceptance_records": len(report["acceptance_review"]),
        "local_references": len(local_references),
        "operator_review_pending_records": sum(
            1
            for record in (*report["report_sections"], *report["acceptance_review"], *report["validation_review"])
            if record["operator_review_status"] == OPERATOR_REVIEW_STATUS
        ),
        "report_sections": len(report["report_sections"]),
        "required_validation_commands": len(report["required_validation_commands"]),
        "validation_records": len(report["validation_review"]),
        "warnings": len(report["warnings"]),
    }


def test_request_report_and_markdown_have_no_blocked_output_terms() -> None:
    request = _load_request()
    report = _load_sample()
    markdown = render_operator_report(report)

    assert find_blocked_output_terms(request) == []
    assert find_blocked_output_terms(report) == []
    assert find_blocked_output_terms(markdown) == []


def test_operator_report_matches_static_sample_and_is_deterministic() -> None:
    report = _load_sample()

    first = render_operator_report(report)
    second = render_operator_report(deepcopy(report))

    assert first == second
    assert first == SAMPLE_MARKDOWN_PATH.read_text(encoding="utf-8")
    assert "# PMBOT Night Batch Acceptance Report" in first
    assert f"Task: `{TASK_ID}`" in first
    assert "Descriptive operator review material only." in first


def test_cli_writes_local_acceptance_report_and_markdown(tmp_path: Path) -> None:
    report_path = tmp_path / "local_night_batch_acceptance_report.json"
    markdown_path = tmp_path / "local_night_batch_acceptance_report.md"

    exit_code = main(
        [
            "--request",
            str(REQUEST_PATH),
            "--output-report",
            str(report_path),
            "--output-markdown",
            str(markdown_path),
        ]
    )

    assert exit_code == 0
    report = json.loads(report_path.read_text(encoding="utf-8"))
    markdown = markdown_path.read_text(encoding="utf-8")
    assert report == build_acceptance_report(_load_request())
    assert markdown == render_operator_report(report)
    assert validate_acceptance_report(report).valid is True


def test_request_validation_rejects_external_reference() -> None:
    request = _load_request()
    request["acceptance_records"][0]["local_reference"] = "https://example.invalid/pmbot"

    validation = validate_acceptance_report_request(request)

    assert validation.valid is False
    assert any("acceptance_records[0].local_reference must be a local path" in error for error in validation.errors)
    with pytest.raises(NightBatchAcceptanceReportValidationError):
        build_acceptance_report(request)


def test_request_validation_rejects_blocked_review_terms() -> None:
    request = _load_request()
    request["section_records"][0]["score_label"] = "blocked"

    validation = validate_acceptance_report_request(request)

    assert validation.valid is False
    assert any("blocked review term detected" in error for error in validation.errors)


def test_request_contract_version_is_explicit() -> None:
    request = _load_request()

    assert request["contract_version"] == REQUEST_CONTRACT_VERSION


def test_documentation_registers_acceptance_report_fixture_and_safety_boundary() -> None:
    document = DOC_PATH.read_text(encoding="utf-8")

    assert f"Task: `{TASK_ID}`" in document
    assert "Report: `pmbot_night_batch_acceptance_report_fixture_001`" in document
    assert f"Contract: `{REPORT_CONTRACT_VERSION}`" in document
    assert str(REQUEST_PATH).replace("\\", "/") in document
    assert SAMPLE_REPORT_PATH in document
    assert str(SAMPLE_MARKDOWN_PATH).replace("\\", "/") in document
    assert "No forecast scoring, action guidance, or selection advice." in document
    assert "This report is not execution approval and is not runtime input." in document


def _load_request() -> dict:
    return load_acceptance_report_request(REQUEST_PATH)


def _load_sample() -> dict:
    return json.loads(Path(SAMPLE_REPORT_PATH).read_text(encoding="utf-8"))
