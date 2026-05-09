from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from pm_bot.dashboard.local_morning_review_pack import (
    LOCAL_ONLY_SAFETY_BOUNDARIES,
    LOCAL_RUN_MODE,
    OPERATOR_REVIEW_STATUS,
    PACK_CONTRACT_VERSION,
    REQUEST_CONTRACT_VERSION,
    REQUIRED_VALIDATION_COMMANDS,
    SAMPLE_PACK_PATH,
    TASK_ID,
    MorningReviewPackValidationError,
    build_morning_review_pack,
    find_blocked_output_terms,
    load_morning_review_request,
    main,
    render_operator_report,
    validate_morning_review_pack,
    validate_morning_review_request,
)


DOC_PATH = Path("docs/PMBOT_OPERATOR_001_MORNING_REVIEW_PACK_LOCAL_ONLY.md")
REQUEST_PATH = Path("pm_bot/tests/fixtures/operator/morning_review_pack_request.valid.json")
SAMPLE_REPORT_PATH = Path("pm_bot/dashboard/samples/local_morning_review_pack.fixture.md")

EXPECTED_QUEUE_TASK_IDS = (
    "PMBOT-OPERATOR-001-MORNING-REVIEW-PACK-LOCAL-ONLY",
    "PMBOT-SAFETY-002-NIGHT-BATCH-POSTRUN-AUDIT-SUMMARY-LOCAL-ONLY",
    "PMBOT-DASHBOARD-002-QUEUE-AND-PAPERLIVE-STATUS-SURFACE",
)
EXPECTED_DASHBOARD_ARTIFACT_IDS = (
    "local_operator_dashboard_summary",
    "queue_paperlive_status_surface",
    "source_quality_dashboard_summary",
    "paper_accounting_dashboard_summary",
)
EXPECTED_SAFETY_BOUNDARY_IDS = (
    "autonomy_gate_checklist",
    "night_batch_postrun_audit",
    "forbidden_action_scan",
)
ALLOWED_LOCAL_PREFIXES = ("docs/", "pm_bot/dashboard/", "pm_bot/tests/", "tests/")


def test_builder_output_matches_static_fixture() -> None:
    request = _load_request()
    sample = _load_sample()

    assert build_morning_review_pack(request) == sample


def test_static_fixture_has_expected_contract() -> None:
    pack = _load_sample()

    assert tuple(pack.keys()) == tuple(sorted(pack.keys()))
    assert pack["task_id"] == TASK_ID
    assert pack["pack_id"] == "pmbot_morning_review_pack_fixture_001"
    assert pack["contract_version"] == PACK_CONTRACT_VERSION
    assert pack["run_mode"] == LOCAL_RUN_MODE
    assert pack["created_at"] == "2026-05-09T00:00:00Z"
    assert pack["review_date"] == "2026-05-09"
    assert pack["local_only"] is True
    assert pack["operator_review_required"] is True
    assert pack["operator_review"]["status"] == OPERATOR_REVIEW_STATUS
    assert pack["errors"] == []
    assert pack["warnings"] == []
    assert validate_morning_review_pack(pack).valid is True


def test_queue_dashboard_safety_records_are_fixed_local_and_pending_review() -> None:
    pack = _load_sample()

    assert tuple(record["task_id"] for record in pack["queue_review"]) == EXPECTED_QUEUE_TASK_IDS
    assert tuple(record["artifact_id"] for record in pack["dashboard_review"]) == EXPECTED_DASHBOARD_ARTIFACT_IDS
    assert tuple(record["boundary_id"] for record in pack["safety_review"]) == EXPECTED_SAFETY_BOUNDARY_IDS
    for record in (*pack["queue_review"], *pack["dashboard_review"], *pack["safety_review"], *pack["validation_review"]):
        assert record["operator_review_status"] == OPERATOR_REVIEW_STATUS
        assert record["runner_state"] == "ready_for_operator_review"
        for reference_field in ("local_reference", "source_fixture_reference"):
            if reference_field in record:
                assert "://" not in record[reference_field]
                assert record[reference_field].startswith(ALLOWED_LOCAL_PREFIXES)


def test_safety_boundaries_are_closed_for_morning_review_pack() -> None:
    pack = _load_sample()

    assert pack["safety_boundaries"] == LOCAL_ONLY_SAFETY_BOUNDARIES
    assert pack["safety_boundaries"]["local_static_samples_only"] is True
    assert pack["safety_boundaries"]["paper_mode_only"] is True
    assert pack["safety_boundaries"]["operator_review_required"] is True
    assert all(value is False for key, value in LOCAL_ONLY_SAFETY_BOUNDARIES.items() if key.endswith("_allowed"))


def test_validation_commands_are_recorded_for_operator_run_local_checks() -> None:
    pack = _load_sample()

    assert pack["required_validation_commands"] == list(REQUIRED_VALIDATION_COMMANDS)
    assert pack["required_validation_commands"] == [
        "python -m compileall pm_bot tests",
        "pytest pm_bot/tests tests/test_codex_queue_pmbot_templates.py",
    ]
    assert [record["command_label"] for record in pack["validation_review"]] == list(REQUIRED_VALIDATION_COMMANDS)


def test_summary_counts_match_pack_content() -> None:
    pack = _load_sample()
    local_references = set()
    for record in (*pack["queue_review"], *pack["dashboard_review"], *pack["safety_review"], *pack["validation_review"]):
        local_references.add(record["local_reference"])
        if "source_fixture_reference" in record:
            local_references.add(record["source_fixture_reference"])

    assert pack["summary_counts"] == {
        "dashboard_records": len(pack["dashboard_review"]),
        "local_references": len(local_references),
        "operator_review_pending_records": sum(
            1
            for record in (*pack["queue_review"], *pack["dashboard_review"], *pack["safety_review"], *pack["validation_review"])
            if record["operator_review_status"] == OPERATOR_REVIEW_STATUS
        ),
        "queue_records": len(pack["queue_review"]),
        "required_validation_commands": len(pack["required_validation_commands"]),
        "safety_records": len(pack["safety_review"]),
        "validation_records": len(pack["validation_review"]),
        "warnings": len(pack["warnings"]),
    }


def test_request_and_pack_have_no_blocked_output_terms() -> None:
    request = _load_request()
    pack = _load_sample()

    assert find_blocked_output_terms(request) == []
    assert find_blocked_output_terms(pack) == []


def test_operator_report_matches_static_sample_and_is_deterministic() -> None:
    pack = _load_sample()

    first = render_operator_report(pack)
    second = render_operator_report(deepcopy(pack))

    assert first == second
    assert first == SAMPLE_REPORT_PATH.read_text(encoding="utf-8")
    assert "# PMBOT Morning Review Pack" in first
    assert f"Task: `{TASK_ID}`" in first
    assert "Descriptive operator review material only." in first


def test_cli_writes_local_morning_review_pack_and_report(tmp_path: Path) -> None:
    pack_path = tmp_path / "local_morning_review_pack.json"
    report_path = tmp_path / "local_morning_review_pack.md"

    exit_code = main(
        [
            "--request",
            str(REQUEST_PATH),
            "--output-pack",
            str(pack_path),
            "--output-report",
            str(report_path),
        ]
    )

    assert exit_code == 0
    pack = json.loads(pack_path.read_text(encoding="utf-8"))
    report = report_path.read_text(encoding="utf-8")
    assert pack == build_morning_review_pack(_load_request())
    assert report == render_operator_report(pack)
    assert validate_morning_review_pack(pack).valid is True


def test_request_validation_rejects_external_reference() -> None:
    request = _load_request()
    request["queue_records"][0]["local_reference"] = "https://example.invalid/pmbot"

    validation = validate_morning_review_request(request)

    assert validation.valid is False
    assert any("queue_records[0].local_reference must be a local path" in error for error in validation.errors)
    with pytest.raises(MorningReviewPackValidationError):
        build_morning_review_pack(request)


def test_request_validation_rejects_blocked_review_terms() -> None:
    request = _load_request()
    request["dashboard_records"][0]["score_label"] = "blocked"

    validation = validate_morning_review_request(request)

    assert validation.valid is False
    assert any("blocked review term detected" in error for error in validation.errors)


def test_dashboard_request_contract_version_is_explicit() -> None:
    request = _load_request()

    assert request["contract_version"] == REQUEST_CONTRACT_VERSION


def test_documentation_registers_morning_review_pack_fixture_and_safety_boundary() -> None:
    document = DOC_PATH.read_text(encoding="utf-8")

    assert f"Task: `{TASK_ID}`" in document
    assert "Pack: `pmbot_morning_review_pack_fixture_001`" in document
    assert f"Contract: `{PACK_CONTRACT_VERSION}`" in document
    assert str(REQUEST_PATH).replace("\\", "/") in document
    assert SAMPLE_PACK_PATH in document
    assert str(SAMPLE_REPORT_PATH).replace("\\", "/") in document
    assert "No forecast scoring, action guidance, or selection advice." in document
    assert "This pack is not execution approval and is not runtime input." in document


def _load_request() -> dict:
    return load_morning_review_request(REQUEST_PATH)


def _load_sample() -> dict:
    return json.loads(Path(SAMPLE_PACK_PATH).read_text(encoding="utf-8"))
