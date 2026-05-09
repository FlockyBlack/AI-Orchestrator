from __future__ import annotations

import json
from pathlib import Path

from pm_bot.readiness.next_20_task_backlog_generator import (
    BACKLOG_ID,
    BACKLOG_NAME,
    CONTRACT_VERSION,
    OPERATOR_REVIEW_STATUS,
    REQUIRED_VALIDATION_COMMANDS,
    RUN_MODE,
    SAFETY_BOUNDARIES,
    TASK_ID,
    build_next_20_task_backlog,
    find_blocked_output_terms,
    main,
    render_operator_report,
    validate_next_20_task_backlog,
)


DOC_PATH = Path("pm_bot/readiness/PMBOT_ROADMAP_003_NEXT_20_TASK_BACKLOG_GENERATOR.md")
FIXTURE_PATH = Path("pm_bot/tests/fixtures/readiness/pmbot_next_20_task_backlog.valid.json")

EXPECTED_TASK_IDS = (
    "PMBOT-SOURCE-LEDGER-003-SOURCE-QUALITY-REPORT-SUMMARY-LOCAL-ONLY",
    "PMBOT-SOURCE-LEDGER-004-SOURCE-QUALITY-REGRESSION-FIXTURE-LOCAL-ONLY",
    "PMBOT-PAPERLIVE-DECISION-003-SIMULATED-DECISION-AUDIT-LEDGER-NO-RECOMMENDATIONS",
    "PMBOT-PAPERLIVE-DECISION-004-SIMULATED-DECISION-REPLAY-SUMMARY-NO-RECOMMENDATIONS",
    "PMBOT-PAPER-ACCOUNTING-002-PAPER-ONLY-ACCOUNTING-VALIDATOR-LOCAL-ONLY",
    "PMBOT-PAPER-ACCOUNTING-003-PAPER-ONLY-SESSION-SUMMARY-LOCAL-ONLY",
    "PMBOT-CRYPTO-PILOT-001-CRYPTO-MARKET-CLASS-CAPTURE-TEMPLATE-LOCAL-ONLY",
    "PMBOT-CRYPTO-PILOT-002-CRYPTO-OPERATOR-REVIEW-PROTOCOL-LOCAL-ONLY",
    "PMBOT-CRYPTO-PILOT-003-CRYPTO-PAPERLIVE-OBSERVATION-LEDGER-LOCAL-ONLY",
    "PMBOT-CRYPTO-PILOT-004-CRYPTO-SOURCE-QUALITY-CAPTURE-SURFACE-LOCAL-ONLY",
    "PMBOT-DASHBOARD-002-QUEUE-AND-PAPERLIVE-STATUS-SURFACE",
    "PMBOT-DASHBOARD-003-SOURCE-QUALITY-DASHBOARD-SUMMARY",
    "PMBOT-DASHBOARD-004-PAPER-ACCOUNTING-DASHBOARD-SUMMARY",
    "PMBOT-SAFETY-001-AUTONOMY-GATE-CHECKLIST-LOCAL-ONLY",
    "PMBOT-SAFETY-002-NIGHT-BATCH-POSTRUN-AUDIT-SUMMARY-LOCAL-ONLY",
    "PMBOT-SAFETY-003-FORBIDDEN-ACTION-SCAN-LOCAL-ONLY",
    "PMBOT-ROADMAP-002-PMBOT-LOCAL-TO-SUPERVISED-LIVE-GAP-MATRIX",
    "PMBOT-ROADMAP-003-NEXT-20-TASK-BACKLOG-GENERATOR",
    "PMBOT-OPERATOR-001-MORNING-REVIEW-PACK-LOCAL-ONLY",
    "PMBOT-OPERATOR-002-NIGHT-BATCH-ACCEPTANCE-REPORT-LOCAL-ONLY",
)

ALLOWED_LOCAL_PREFIXES = ("docs/", "pm_bot/readiness/", "pm_bot/tests/", "tests/")


def test_builder_output_matches_static_fixture() -> None:
    assert build_next_20_task_backlog() == _load_backlog()


def test_static_backlog_fixture_has_expected_contract() -> None:
    backlog = _load_backlog()

    assert tuple(backlog.keys()) == tuple(sorted(backlog.keys()))
    assert backlog["task_id"] == TASK_ID
    assert backlog["backlog_id"] == BACKLOG_ID
    assert backlog["backlog_name"] == BACKLOG_NAME
    assert backlog["contract_version"] == CONTRACT_VERSION
    assert backlog["run_mode"] == RUN_MODE
    assert backlog["created_at"] == "2026-05-09T00:00:00Z"
    assert backlog["local_only"] is True
    assert backlog["operator_review_required"] is True
    assert backlog["operator_review"]["status"] == OPERATOR_REVIEW_STATUS
    assert backlog["errors"] == []
    assert backlog["warnings"] == []
    assert validate_next_20_task_backlog(backlog).valid is True


def test_task_records_are_fixed_local_and_pending_operator_review() -> None:
    backlog = _load_backlog()

    assert tuple(record["task_id"] for record in backlog["task_records"]) == EXPECTED_TASK_IDS
    assert tuple(record["record_index"] for record in backlog["task_records"]) == tuple(range(1, 21))
    for record in backlog["task_records"]:
        assert set(record) == {
            "artifact_family",
            "local_reference",
            "operator_review_status",
            "record_index",
            "review_note",
            "task_id",
            "workstream",
        }
        assert record["operator_review_status"] == OPERATOR_REVIEW_STATUS
        assert "://" not in record["local_reference"]
        assert record["local_reference"].startswith(ALLOWED_LOCAL_PREFIXES)


def test_source_artifacts_are_fixed_local_and_pending_operator_review() -> None:
    backlog = _load_backlog()

    assert tuple(artifact["artifact_id"] for artifact in backlog["source_artifacts"]) == (
        "queue_template_task_source",
        "roadmap_gap_matrix",
        "real_wallet_blocker_matrix",
        "forbidden_action_boundary",
    )
    for artifact in backlog["source_artifacts"]:
        assert set(artifact) == {"artifact_id", "local_reference", "operator_review_status", "record_role", "record_state"}
        assert artifact["operator_review_status"] == OPERATOR_REVIEW_STATUS
        assert "://" not in artifact["local_reference"]
        assert artifact["local_reference"].startswith(ALLOWED_LOCAL_PREFIXES)


def test_safety_boundaries_are_closed_for_next_20_backlog() -> None:
    backlog = _load_backlog()

    assert backlog["safety_boundaries"] == SAFETY_BOUNDARIES
    assert all(value is False for key, value in SAFETY_BOUNDARIES.items() if key.endswith("_allowed"))
    assert backlog["safety_boundaries"]["local_static_samples_only"] is True
    assert backlog["safety_boundaries"]["operator_review_required"] is True
    assert backlog["safety_boundaries"]["paper_mode_only"] is True


def test_validation_commands_are_recorded_for_operator_run_local_checks() -> None:
    backlog = _load_backlog()

    assert backlog["required_validation_commands"] == list(REQUIRED_VALIDATION_COMMANDS)
    assert backlog["required_validation_commands"] == [
        "python -m compileall pm_bot tests",
        "pytest pm_bot/tests tests/test_codex_queue_pmbot_templates.py",
    ]


def test_summary_counts_match_backlog_content() -> None:
    backlog = _load_backlog()
    local_references = {artifact["local_reference"] for artifact in backlog["source_artifacts"]}
    local_references.update(record["local_reference"] for record in backlog["task_records"])

    assert backlog["summary_counts"] == {
        "local_references": len(local_references),
        "required_validation_commands": len(backlog["required_validation_commands"]),
        "source_artifacts": len(backlog["source_artifacts"]),
        "task_records": len(backlog["task_records"]),
        "task_records_pending_operator_review": sum(
            1 for record in backlog["task_records"] if record["operator_review_status"] == OPERATOR_REVIEW_STATUS
        ),
        "warnings": len(backlog["warnings"]),
    }


def test_backlog_output_has_no_blocked_terms_outside_task_ids_or_local_paths() -> None:
    backlog = _load_backlog()

    assert find_blocked_output_terms(backlog) == []


def test_operator_report_renders_descriptive_local_backlog() -> None:
    backlog = _load_backlog()
    report = render_operator_report(backlog)

    assert "# PMBOT Next 20 Task Backlog" in report
    assert f"Task: `{TASK_ID}`" in report
    assert f"Contract: `{CONTRACT_VERSION}`" in report
    assert "PMBOT-ROADMAP-003-NEXT-20-TASK-BACKLOG-GENERATOR" in report
    assert "No forecast scoring, action guidance, or selection advice." in report
    assert "This backlog is not execution approval and is not runtime input." in report


def test_cli_writes_local_backlog_and_operator_report(tmp_path: Path) -> None:
    backlog_path = tmp_path / "pmbot_next_20_task_backlog.json"
    report_path = tmp_path / "pmbot_next_20_task_backlog.md"

    exit_code = main(["--output-backlog", str(backlog_path), "--output-report", str(report_path)])

    assert exit_code == 0
    backlog = json.loads(backlog_path.read_text(encoding="utf-8"))
    report = report_path.read_text(encoding="utf-8")
    assert backlog == build_next_20_task_backlog()
    assert "# PMBOT Next 20 Task Backlog" in report
    assert validate_next_20_task_backlog(backlog).valid is True


def test_validation_rejects_external_reference() -> None:
    backlog = build_next_20_task_backlog()
    backlog["task_records"][0]["local_reference"] = "https://example.invalid/pmbot"

    validation = validate_next_20_task_backlog(backlog)

    assert validation.valid is False
    assert any("task_records[0].local_reference must be a local path" in error for error in validation.errors)


def test_validation_rejects_blocked_output_field() -> None:
    backlog = build_next_20_task_backlog()
    backlog["task_records"][0]["forecast_metric"] = "blocked"

    validation = validate_next_20_task_backlog(backlog)

    assert validation.valid is False
    assert any("task_records[0] keys must match the task record contract" in error for error in validation.errors)
    assert any("blocked guidance/scoring term detected" in error for error in validation.errors)


def test_documentation_registers_generator_fixture_and_safety_boundary() -> None:
    document = DOC_PATH.read_text(encoding="utf-8")

    assert f"Task: `{TASK_ID}`" in document
    assert f"Backlog: `{BACKLOG_NAME}`" in document
    assert f"Contract: `{CONTRACT_VERSION}`" in document
    assert str(FIXTURE_PATH).replace("\\", "/") in document
    assert "No forecast scoring, action guidance, market ranking, numeric prediction metric" in document
    assert "This backlog is not execution approval and is not runtime input." in document


def _load_backlog() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
