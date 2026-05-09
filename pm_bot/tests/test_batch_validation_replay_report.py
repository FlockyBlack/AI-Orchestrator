from __future__ import annotations

import json
from pathlib import Path


DOC_PATH = Path("docs/PMBOT_VALIDATION_003_BATCH_VALIDATION_REPLAY_REPORT_LOCAL_ONLY.md")
FIXTURE_PATH = Path("pm_bot/tests/fixtures/validation/pmbot_batch_validation_replay_report.valid.json")
TASK_ID = "PMBOT-VALIDATION-003-BATCH-VALIDATION-REPLAY-REPORT-LOCAL-ONLY"
CONTRACT_ID = "pmbot-batch-validation-replay-report"
CONTRACT_VERSION = "pmbot_batch_validation_replay_report.v1"
REPORT_ID = "pmbot-batch-validation-replay-report-001"
REPORT_NAME = "pmbot-batch-validation-replay-report"
RUN_MODE = "local_static_batch_validation_replay_report"
OPERATOR_REVIEW_STATUS = "pending_operator_review"

EXPECTED_SECTION_IDS = (
    "batch_validation_replay_identity",
    "saved_evidence_replay_bundle_section",
    "ci_safe_validation_subset_section",
    "simulated_decision_replay_summary_section",
    "queue_template_validation_section",
    "validation_command_section",
)
EXPECTED_REPLAY_RECORD_IDS = (
    "batch_validation_replay_report_001.report_fixture",
    "batch_validation_replay_report_001.report_document",
    "batch_validation_replay_report_001.saved_evidence_replay_bundle",
    "batch_validation_replay_report_001.ci_safe_validation_subset",
    "batch_validation_replay_report_001.simulated_decision_replay_summary",
    "batch_validation_replay_report_001.simulated_decision_audit_ledger",
    "batch_validation_replay_report_001.simulated_decision_packet",
    "batch_validation_replay_report_001.queue_template_boundary_test",
    "batch_validation_replay_report_001.report_contract_test",
)
EXPECTED_OPERATOR_CHECK_IDS = (
    "local_reference_check",
    "static_fixture_check",
    "validation_command_check",
    "closed_boundary_check",
    "human_review_check",
)
EXPECTED_EXCLUDED_PREFIXES = (
    ".env",
    ".env.*",
    ".git/",
    ".codex/",
    "runtime/",
    "dispatcher/",
    "run_codex/",
    "pm_bot/llm/",
    "pm_bot/wallet/",
    "pm_bot/trading/",
    "pm_bot/orders/",
    "agent_tasks/running/",
)
EXPECTED_SAFETY_BOUNDARIES = {
    "authenticated_endpoint_calls_allowed": False,
    "background_process_allowed": False,
    "browser_automation_allowed": False,
    "credential_or_secret_access_allowed": False,
    "execution_endpoint_calls_allowed": False,
    "external_service_calls_allowed": False,
    "llm_provider_calls_allowed": False,
    "local_fixtures_only": True,
    "local_static_samples_only": True,
    "market_api_calls_allowed": False,
    "market_instruction_fields_allowed": False,
    "network_calls_allowed": False,
    "operator_review_required": True,
    "order_or_trade_surface_changes_allowed": False,
    "paper_mode_only": True,
    "report_mutates_source_artifacts_allowed": False,
    "runtime_or_dispatcher_changes_allowed": False,
    "scheduler_or_worker_allowed": False,
    "sensitive_path_access_allowed": False,
    "timed_automation_allowed": False,
    "transaction_endpoint_calls_allowed": False,
    "wallet_or_signing_material_access_allowed": False,
}
ALLOWED_LOCAL_PREFIXES = ("docs/", "pm_bot/readiness/", "pm_bot/simulated_decisions/", "pm_bot/tests/", "tests/")


def test_static_batch_validation_replay_report_fixture_has_expected_contract() -> None:
    report = _load_report()

    assert tuple(report.keys()) == tuple(sorted(report.keys()))
    assert report["task_id"] == TASK_ID
    assert report["report_id"] == REPORT_ID
    assert report["report_name"] == REPORT_NAME
    assert report["contract_id"] == CONTRACT_ID
    assert report["contract_version"] == CONTRACT_VERSION
    assert report["run_mode"] == RUN_MODE
    assert report["created_at"] == "2026-05-09T01:30:00Z"
    assert report["local_only"] is True
    assert report["operator_review_required"] is True
    assert report["operator_review"]["status"] == OPERATOR_REVIEW_STATUS
    assert report["operator_review"]["reviewed_at"] is None
    assert report["operator_review"]["reviewed_by"] is None
    assert report["errors"] == []
    assert report["warnings"] == []


def test_report_sections_are_fixed_local_and_pending_review() -> None:
    report = _load_report()

    assert tuple(section["section_id"] for section in report["report_sections"]) == EXPECTED_SECTION_IDS
    for section in report["report_sections"]:
        assert tuple(section.keys()) == tuple(sorted(section.keys()))
        assert set(section) == {
            "local_reference",
            "observed_state",
            "operator_review_status",
            "record_count",
            "section_id",
            "section_label",
            "section_role",
            "source_fixture_reference",
        }
        assert section["operator_review_status"] == OPERATOR_REVIEW_STATUS
        assert section["record_count"] > 0
        _assert_allowed_existing_local_reference(section["local_reference"])
        _assert_allowed_existing_local_reference(section["source_fixture_reference"])


def test_replay_records_are_fixed_local_and_do_not_change_source_state() -> None:
    report = _load_report()

    assert tuple(record["record_id"] for record in report["replay_records"]) == EXPECTED_REPLAY_RECORD_IDS
    for record in report["replay_records"]:
        assert tuple(record.keys()) == tuple(sorted(record.keys()))
        assert set(record) == {
            "contract_version",
            "expected_state",
            "local_reference",
            "operator_review_status",
            "record_id",
            "record_label",
            "record_role",
            "source_fixture_reference",
        }
        assert record["operator_review_status"] == OPERATOR_REVIEW_STATUS
        assert record["expected_state"] in {
            "local_validation_reference",
            "pending_operator_review",
            "recorded_for_operator_review",
        }
        _assert_allowed_existing_local_reference(record["local_reference"])
        _assert_allowed_existing_local_reference(record["source_fixture_reference"])


def test_operator_checks_and_validation_commands_are_local_review_records() -> None:
    report = _load_report()

    assert tuple(check["check_id"] for check in report["operator_review_checks"]) == EXPECTED_OPERATOR_CHECK_IDS
    for check in report["operator_review_checks"]:
        assert tuple(check.keys()) == tuple(sorted(check.keys()))
        assert set(check) == {
            "check_id",
            "local_reference",
            "operator_review_status",
            "required_evidence",
            "review_label",
        }
        assert check["operator_review_status"] == OPERATOR_REVIEW_STATUS
        _assert_allowed_existing_local_reference(check["local_reference"])

    assert report["required_validation_commands"] == [
        "python -m compileall pm_bot tests",
        "pytest pm_bot/tests tests/test_codex_queue_pmbot_templates.py",
    ]
    assert [record["command_label"] for record in report["validation_command_records"]] == report[
        "required_validation_commands"
    ]
    for record in report["validation_command_records"]:
        assert tuple(record.keys()) == tuple(sorted(record.keys()))
        assert set(record) == {
            "command_label",
            "local_reference",
            "operator_review_status",
            "record_id",
            "status",
        }
        assert record["operator_review_status"] == OPERATOR_REVIEW_STATUS
        assert record["status"] == "not_run_static_record"
        _assert_allowed_existing_local_reference(record["local_reference"])


def test_safety_boundaries_close_non_local_surfaces_for_batch_validation_report() -> None:
    report = _load_report()

    assert report["safety_boundaries"] == EXPECTED_SAFETY_BOUNDARIES
    assert report["safety_boundaries"]["local_fixtures_only"] is True
    assert report["safety_boundaries"]["local_static_samples_only"] is True
    assert report["safety_boundaries"]["operator_review_required"] is True
    assert report["safety_boundaries"]["paper_mode_only"] is True
    assert all(value is False for key, value in report["safety_boundaries"].items() if key.endswith("_allowed"))


def test_excluded_prefixes_match_sensitive_and_execution_boundaries() -> None:
    report = _load_report()

    assert tuple(report["excluded_path_prefixes"]) == EXPECTED_EXCLUDED_PREFIXES


def test_summary_counts_match_batch_validation_replay_content() -> None:
    report = _load_report()
    local_references = {report["source_batch"]["local_reference"]}

    for collection_name in (
        "operator_review_checks",
        "replay_records",
        "report_sections",
        "validation_command_records",
    ):
        for record in report[collection_name]:
            for reference_field in ("local_reference", "source_fixture_reference"):
                if reference_field in record:
                    local_references.add(record[reference_field])

    assert report["summary_counts"] == {
        "errors": len(report["errors"]),
        "excluded_path_prefixes": len(report["excluded_path_prefixes"]),
        "local_references": len(local_references),
        "operator_review_checks": len(report["operator_review_checks"]),
        "operator_review_checks_pending_operator_review": sum(
            1 for check in report["operator_review_checks"] if check["operator_review_status"] == OPERATOR_REVIEW_STATUS
        ),
        "replay_records": len(report["replay_records"]),
        "replay_records_pending_operator_review": sum(
            1 for record in report["replay_records"] if record["operator_review_status"] == OPERATOR_REVIEW_STATUS
        ),
        "report_sections": len(report["report_sections"]),
        "report_sections_pending_operator_review": sum(
            1 for section in report["report_sections"] if section["operator_review_status"] == OPERATOR_REVIEW_STATUS
        ),
        "required_validation_commands": len(report["required_validation_commands"]),
        "validation_command_records": len(report["validation_command_records"]),
        "warnings": len(report["warnings"]),
    }


def test_fixture_has_no_decision_scoring_or_selection_terms() -> None:
    report = _load_report()

    assert _find_disallowed_terms(report) == []


def test_documentation_registers_batch_validation_report_and_safety_boundary() -> None:
    document = DOC_PATH.read_text(encoding="utf-8")

    assert f"Task: `{TASK_ID}`" in document
    assert f"Report: `{REPORT_ID}`" in document
    assert f"Contract: `{CONTRACT_VERSION}`" in document
    assert f"Run mode: `{RUN_MODE}`" in document
    assert str(FIXTURE_PATH).replace("\\", "/") in document
    assert "No forecast scoring, action guidance, or selection advice." in document
    assert "This report is not execution approval and is not runtime input." in document


def _load_report() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def _assert_allowed_existing_local_reference(local_reference: str) -> None:
    assert "://" not in local_reference
    assert local_reference.startswith(ALLOWED_LOCAL_PREFIXES)
    assert Path(local_reference).exists()


def _find_disallowed_terms(value: object, path: str = "$") -> list[str]:
    disallowed_tokens = {
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
            if _has_token(str(key), disallowed_tokens):
                hits.append(key_path)
            if key == "excluded_path_prefixes":
                continue
            hits.extend(_find_disallowed_terms(nested_value, key_path))
    elif isinstance(value, list):
        for index, nested_value in enumerate(value):
            hits.extend(_find_disallowed_terms(nested_value, f"{path}[{index}]"))
    elif isinstance(value, str) and _has_token(value, disallowed_tokens):
        hits.append(path)
    return hits


def _has_token(value: str, disallowed_tokens: set[str]) -> bool:
    normalized = "".join(character if character.isalnum() else "_" for character in value.lower())
    tokens = {token for token in normalized.split("_") if token}
    return bool(tokens & disallowed_tokens)
