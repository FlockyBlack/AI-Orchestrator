from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from pm_bot.dashboard.local_supervised_live_readiness_dashboard import (
    DASHBOARD_CONTRACT_VERSION,
    LOCAL_ONLY_SAFETY_BOUNDARIES,
    LOCAL_RUN_MODE,
    OPERATOR_REVIEW_STATUS,
    REQUEST_CONTRACT_VERSION,
    SAMPLE_DASHBOARD_PATH,
    SAMPLE_OPERATOR_REPORT_PATH,
    SupervisedLiveReadinessDashboardValidationError,
    build_local_supervised_live_readiness_dashboard,
    build_operator_report,
    load_dashboard_request,
    main,
    validate_dashboard_request,
    validate_local_supervised_live_readiness_dashboard,
)

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "dashboard"
VALID_REQUEST_PATH = FIXTURE_DIR / "local_supervised_live_readiness_dashboard_request.valid.json"
DOC_PATH = Path("docs/PMBOT_DASHBOARD_005_SUPERVISED_LIVE_READINESS_DASHBOARD_LOCAL_ONLY.md")
TASK_ID = "PMBOT-DASHBOARD-005-SUPERVISED-LIVE-READINESS-DASHBOARD-LOCAL-ONLY"


def test_valid_fixture_request_builds_supervised_live_readiness_dashboard() -> None:
    request = load_dashboard_request(VALID_REQUEST_PATH)
    validation = validate_dashboard_request(request)
    dashboard = build_local_supervised_live_readiness_dashboard(request)

    assert validation.valid is True
    assert validation.errors == ()
    assert dashboard["contract_version"] == DASHBOARD_CONTRACT_VERSION
    assert dashboard["dashboard_id"] == "local_supervised_live_readiness_dashboard_fixture_001"
    assert dashboard["dashboard_label"] == "PMBOT local supervised-live readiness dashboard"
    assert dashboard["run_mode"] == LOCAL_RUN_MODE
    assert dashboard["local_only"] is True
    assert dashboard["operator_review_required"] is True
    assert dashboard["operator_review"]["status"] == OPERATOR_REVIEW_STATUS
    assert dashboard["summary_counts"] == {
        "operator_review_checks": 28,
        "operator_review_pending_records": 15,
        "queue_records": 7,
        "readiness_artifacts": 6,
        "readiness_rows": 38,
        "supporting_artifacts": 21,
        "validation_commands": 12,
        "validation_records": 2,
        "warnings": 0,
    }
    assert dashboard["queue_summary"][0] == {
        "local_reference": "docs/PMBOT_DASHBOARD_005_SUPERVISED_LIVE_READINESS_DASHBOARD_LOCAL_ONLY.md",
        "notes": "Static queue coverage includes the supervised-live readiness dashboard task identifier.",
        "operator_review_status": OPERATOR_REVIEW_STATUS,
        "queue_group": "supervised_live_readiness_template",
        "record_id": f"queue_supervised_live_readiness.{TASK_ID}",
        "runner_state": "ready_for_operator_review",
        "safety_class": "local_only_no_execution",
        "status_label": "template_listed_static_record",
        "task_id": TASK_ID,
        "task_template": "supervised_live_readiness_dashboard",
        "task_title": "PMBOT supervised live readiness dashboard",
        "validation_profile": "pmbot_local_code_tests",
    }
    assert dashboard["readiness_summary"][4] == {
        "artifact_id": "supervised_live_readiness_evidence_bundle",
        "artifact_label": "Supervised-live readiness evidence bundle",
        "artifact_type": "supervised_live_readiness_evidence_bundle",
        "contract_version": "pmbot_supervised_live_readiness_evidence_bundle.v1",
        "fixture_reference": "pm_bot/tests/fixtures/readiness/pmbot_supervised_live_readiness_evidence_bundle.valid.json",
        "local_reference": "docs/PMBOT_SUPERVISED_LIVE_005_LIVE_READINESS_EVIDENCE_BUNDLE_LOCAL_ONLY.md",
        "notes": "Static bundle fixture groups local readiness evidence for operator review.",
        "operator_review_checks": 7,
        "operator_review_status": OPERATOR_REVIEW_STATUS,
        "readiness_rows": 8,
        "record_id": "supervised_live_readiness_dashboard.supervised_live_readiness_evidence_bundle",
        "required_state": OPERATOR_REVIEW_STATUS,
        "run_mode": "local_static_supervised_live_readiness_evidence_bundle",
        "runner_state": "ready_for_operator_review",
        "scope": "supervised_live_readiness_evidence_bundle",
        "status_label": "static_readiness_sample_ready",
        "supporting_artifacts": 5,
        "validation_commands": 2,
    }
    assert dashboard["validation_status_summary"][0]["command_label"] == "python -m compileall pm_bot tests"
    assert dashboard["safety_boundaries"] == LOCAL_ONLY_SAFETY_BOUNDARIES
    _assert_references_exist(dashboard)


def test_supervised_live_readiness_dashboard_is_deterministic_for_same_request() -> None:
    request = load_dashboard_request(VALID_REQUEST_PATH)

    first = build_local_supervised_live_readiness_dashboard(request)
    second = build_local_supervised_live_readiness_dashboard(deepcopy(request))

    assert first == second
    assert first["build_id"] == "local_supervised_live_readiness_dashboard_fixture_001-94f18392f00c"


def test_static_sample_matches_builder_output() -> None:
    request = load_dashboard_request(VALID_REQUEST_PATH)
    sample = _load_json(Path(SAMPLE_DASHBOARD_PATH))

    assert build_local_supervised_live_readiness_dashboard(request) == sample


def test_static_sample_validates_as_supervised_live_readiness_dashboard() -> None:
    sample = _load_json(Path(SAMPLE_DASHBOARD_PATH))

    validation = validate_local_supervised_live_readiness_dashboard(sample)

    assert validation.valid is True
    assert validation.errors == ()


def test_static_markdown_sample_matches_report_builder_output() -> None:
    sample_dashboard = _load_json(Path(SAMPLE_DASHBOARD_PATH))
    sample_report = Path(SAMPLE_OPERATOR_REPORT_PATH).read_text(encoding="utf-8")

    assert build_operator_report(sample_dashboard) == sample_report


def test_cli_writes_local_supervised_live_readiness_dashboard_and_operator_report(tmp_path: Path) -> None:
    dashboard_path = tmp_path / "local_supervised_live_readiness_dashboard.json"
    report_path = tmp_path / "local_supervised_live_readiness_dashboard.md"

    exit_code = main(
        [
            "--request",
            str(VALID_REQUEST_PATH),
            "--output-dashboard",
            str(dashboard_path),
            "--output-report",
            str(report_path),
        ]
    )

    dashboard = _load_json(dashboard_path)
    report = report_path.read_text(encoding="utf-8")
    assert exit_code == 0
    assert dashboard == _load_json(Path(SAMPLE_DASHBOARD_PATH))
    assert dashboard["errors"] == []
    assert dashboard["warnings"] == []
    assert "# PMBOT Supervised Live Readiness Dashboard" in report
    assert TASK_ID in report
    assert "supervised_live_readiness_evidence_bundle" in report
    assert "pytest pm_bot/tests tests/test_codex_queue_pmbot_templates.py" in report
    assert "Descriptive readiness dashboard only" in report


def test_operator_report_is_deterministic() -> None:
    request = load_dashboard_request(VALID_REQUEST_PATH)
    dashboard = build_local_supervised_live_readiness_dashboard(request)

    first = build_operator_report(dashboard)
    second = build_operator_report(deepcopy(dashboard))

    assert first == second
    assert "Operator review: `pending_operator_review`" in first
    assert "Readiness artifacts: 6" in first


def test_request_rejects_network_like_local_reference() -> None:
    request = load_dashboard_request(VALID_REQUEST_PATH)
    request["readiness_records"][0]["fixture_reference"] = "https://example.invalid/readiness.json"

    validation = validate_dashboard_request(request)

    assert validation.valid is False
    assert any("fixture_reference must be a local reference" in error for error in validation.errors)
    with pytest.raises(SupervisedLiveReadinessDashboardValidationError):
        build_local_supervised_live_readiness_dashboard(request)


def test_request_rejects_reference_outside_allowed_local_paths() -> None:
    request = load_dashboard_request(VALID_REQUEST_PATH)
    request["queue_records"][0]["local_reference"] = "pm_bot/wallet/readiness_dashboard.json"

    validation = validate_dashboard_request(request)

    assert validation.valid is False
    assert any("local_reference is outside the supervised-live readiness dashboard boundary" in error for error in validation.errors)


def test_request_rejects_scoring_or_selection_fields() -> None:
    request = load_dashboard_request(VALID_REQUEST_PATH)
    request["readiness_records"][0]["forecast_score"] = "not allowed in local readiness dashboard summaries"

    validation = validate_dashboard_request(request)

    assert validation.valid is False
    assert any("forbidden supervised-live readiness dashboard decision field detected" in error for error in validation.errors)


def test_supervised_live_readiness_dashboard_rejects_summary_count_drift() -> None:
    request = load_dashboard_request(VALID_REQUEST_PATH)
    dashboard = build_local_supervised_live_readiness_dashboard(request)
    dashboard["summary_counts"]["readiness_rows"] = 99

    validation = validate_local_supervised_live_readiness_dashboard(dashboard)

    assert validation.valid is False
    assert any("summary_counts must match supervised-live readiness dashboard rows" in error for error in validation.errors)


def test_supervised_live_readiness_dashboard_rejects_unreviewed_state_change() -> None:
    request = load_dashboard_request(VALID_REQUEST_PATH)
    dashboard = build_local_supervised_live_readiness_dashboard(request)
    dashboard["readiness_summary"][0]["required_state"] = "complete"

    validation = validate_local_supervised_live_readiness_dashboard(dashboard)

    assert validation.valid is False
    assert any("required_state must be pending_operator_review" in error for error in validation.errors)


def test_output_contract_has_no_scoring_or_selection_fields() -> None:
    request = load_dashboard_request(VALID_REQUEST_PATH)
    dashboard = build_local_supervised_live_readiness_dashboard(request)

    offending_paths = _find_output_decision_terms(dashboard)

    assert offending_paths == []


def test_supervised_live_readiness_dashboard_request_contract_version_is_explicit() -> None:
    request = load_dashboard_request(VALID_REQUEST_PATH)

    assert request["contract_version"] == REQUEST_CONTRACT_VERSION


def test_documentation_registers_dashboard_contract_fixtures_and_safety_boundary() -> None:
    document = DOC_PATH.read_text(encoding="utf-8")

    assert f"Task: `{TASK_ID}`" in document
    assert f"Contract: `{DASHBOARD_CONTRACT_VERSION}`" in document
    assert "pm_bot/dashboard/samples/local_supervised_live_readiness_dashboard.fixture.json" in document
    assert "pm_bot/tests/fixtures/dashboard/local_supervised_live_readiness_dashboard_request.valid.json" in document
    assert "No forecast scoring, action guidance, market ranking, numeric prediction metric" in document
    assert "This dashboard is not execution approval and is not runtime input." in document


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _assert_references_exist(dashboard: dict) -> None:
    for row in [*dashboard["queue_summary"], *dashboard["readiness_summary"], *dashboard["validation_status_summary"]]:
        for field_name in ("fixture_reference", "local_reference"):
            if field_name in row:
                assert Path(row[field_name]).exists()


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
        "recommendations",
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
