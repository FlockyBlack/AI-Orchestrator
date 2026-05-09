from __future__ import annotations

import json
from pathlib import Path


DOC_PATH = Path("docs/PMBOT_CRYPTO_LIVE_018_CRYPTO_NIGHT_BATCH_ACCEPTANCE_REPORT_LOCAL_ONLY.md")
REPORT_PATH = Path("pm_bot/dashboard/samples/pmbot_crypto_night_batch_acceptance_report.fixture.json")
MARKDOWN_PATH = Path("pm_bot/dashboard/samples/pmbot_crypto_night_batch_acceptance_report.fixture.md")
TASK_ID = "PMBOT-CRYPTO-LIVE-018-CRYPTO-NIGHT-BATCH-ACCEPTANCE-REPORT-LOCAL-ONLY"
CONTRACT_ID = "pmbot-crypto-night-batch-acceptance-report"
CONTRACT_VERSION = "pmbot_crypto_night_batch_acceptance_report.v1"
REPORT_ID = "pmbot-crypto-night-batch-acceptance-report-001"
RUN_MODE = "local_static_crypto_night_batch_acceptance_report"
OPERATOR_REVIEW_STATUS = "pending_operator_review"
ALLOWED_LOCAL_PREFIXES = ("docs/", "pm_bot/dashboard/", "pm_bot/readiness/", "pm_bot/tests/", "tests/")

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
EXPECTED_SECTION_IDS = (
    "crypto_night_batch_inventory_review",
    "crypto_dashboard_readiness_review",
    "crypto_morning_card_review",
    "crypto_rehearsal_and_gate_review",
    "crypto_validation_review",
    "crypto_safety_review",
)
EXPECTED_SOURCE_ARTIFACT_IDS = (
    "crypto_night_batch_acceptance_report_document",
    "crypto_night_batch_acceptance_report_sample",
    "crypto_night_batch_acceptance_report_markdown",
    "crypto_night_batch_acceptance_report_contract_test",
    "crypto_dashboard_readiness_summary_document",
    "crypto_dashboard_readiness_summary_sample",
    "crypto_dashboard_readiness_summary_report",
    "crypto_dashboard_readiness_summary_contract_test",
    "crypto_morning_review_card_document",
    "crypto_morning_review_card_sample",
    "crypto_morning_review_card_report",
    "crypto_morning_review_card_contract_test",
    "crypto_live_001_read_only_contract_document",
    "crypto_live_002_source_inventory_document",
    "crypto_live_003_source_evidence_link_document",
    "crypto_live_004_source_staleness_spec_document",
    "crypto_live_005_source_contradiction_ledger_document",
    "crypto_live_006_rehearsal_packet_fixture",
    "crypto_live_007_observation_replay_fixture",
    "crypto_live_008_outcome_evidence_bundle_fixture",
    "crypto_live_009_operator_gate_fixture",
    "crypto_live_010_stop_condition_mapping_fixture",
    "crypto_live_011_gap_matrix_fixture",
    "crypto_live_012_validation_bundle_fixture",
    "crypto_live_013_ci_subset_fixture",
    "crypto_live_014_language_regression_fixture",
    "crypto_live_015_sensitive_path_audit_fixture",
    "queue_template_validation_test",
)
EXPECTED_CHECK_IDS = (
    "acceptance_section_review",
    "source_artifact_review",
    "dashboard_summary_review",
    "morning_card_review",
    "rehearsal_gate_review",
    "validation_record_review",
    "safety_boundary_review",
    "markdown_report_review",
)
EXPECTED_SAFETY_BOUNDARIES = {
    "authenticated_endpoint_calls_allowed": False,
    "background_process_allowed": False,
    "browser_automation_allowed": False,
    "core_execution_wiring_changes_allowed": False,
    "credential_or_secret_access_allowed": False,
    "crypto_data_refresh_allowed": False,
    "execution_endpoint_calls_allowed": False,
    "external_service_calls_allowed": False,
    "llm_provider_calls_allowed": False,
    "local_fixtures_only": True,
    "local_static_samples_only": True,
    "market_api_calls_allowed": False,
    "market_instruction_output_allowed": False,
    "market_ranking_allowed": False,
    "network_calls_allowed": False,
    "night_batch_runtime_input_allowed": False,
    "numeric_prediction_metric_allowed": False,
    "operator_review_required": True,
    "order_or_trade_surface_changes_allowed": False,
    "outcome_resolution_allowed": False,
    "paper_mode_only": True,
    "paperlive_execution_allowed": False,
    "resident_process_allowed": False,
    "runtime_or_dispatcher_changes_allowed": False,
    "scheduler_or_worker_allowed": False,
    "sensitive_path_access_allowed": False,
    "status_mutation_allowed": False,
    "supervised_live_transition_allowed": False,
    "threshold_comparison_output_allowed": False,
    "timed_automation_allowed": False,
    "trade_instruction_allowed": False,
    "transaction_endpoint_calls_allowed": False,
    "wallet_or_signing_material_access_allowed": False,
}


def test_static_crypto_night_batch_acceptance_report_has_expected_contract() -> None:
    report = _load_report()

    assert tuple(report.keys()) == tuple(sorted(report.keys()))
    assert report["task_id"] == TASK_ID
    assert report["acceptance_report_id"] == REPORT_ID
    assert report["acceptance_report_label"] == CONTRACT_ID
    assert report["contract_id"] == CONTRACT_ID
    assert report["contract_version"] == CONTRACT_VERSION
    assert report["run_mode"] == RUN_MODE
    assert report["created_at"] == "2026-05-09T07:00:00Z"
    assert report["review_date"] == "2026-05-09"
    assert report["local_only"] is True
    assert report["operator_review_required"] is True
    assert report["operator_review"] == {
        "reviewed_at": None,
        "reviewed_by": None,
        "status": OPERATOR_REVIEW_STATUS,
    }
    assert report["errors"] == []
    assert report["warnings"] == []


def test_acceptance_sections_are_fixed_local_pending_records() -> None:
    report = _load_report()
    source_artifact_ids = {artifact["artifact_id"] for artifact in report["source_artifacts"]}

    assert tuple(section["acceptance_section_id"] for section in report["acceptance_sections"]) == EXPECTED_SECTION_IDS
    for section in report["acceptance_sections"]:
        assert tuple(section.keys()) == (
            "acceptance_section_id",
            "artifact_type",
            "local_reference",
            "operator_review_status",
            "primary_artifact_id",
            "readiness_record_count",
            "reference_group",
            "review_label",
            "run_mode",
            "source_artifact_ids",
            "status_label",
            "supporting_artifacts",
        )
        assert section["operator_review_status"] == OPERATOR_REVIEW_STATUS
        assert section["status_label"] == "static_report_ready"
        assert section["primary_artifact_id"] in source_artifact_ids
        assert set(section["source_artifact_ids"]) <= source_artifact_ids
        assert section["supporting_artifacts"] == len(section["source_artifact_ids"])
        assert section["readiness_record_count"] >= 2
        _assert_allowed_existing_local_reference(section["local_reference"])


def test_source_artifacts_are_allowed_existing_local_references() -> None:
    report = _load_report()

    assert tuple(report["allowed_path_prefixes"]) == ALLOWED_LOCAL_PREFIXES
    assert tuple(artifact["artifact_id"] for artifact in report["source_artifacts"]) == EXPECTED_SOURCE_ARTIFACT_IDS
    for artifact in report["source_artifacts"]:
        assert tuple(artifact.keys()) == (
            "artifact_id",
            "artifact_role",
            "artifact_type",
            "local_reference",
            "operator_review_status",
            "source_task_id",
        )
        assert artifact["operator_review_status"] == OPERATOR_REVIEW_STATUS
        assert artifact["source_task_id"]
        _assert_allowed_existing_local_reference(artifact["local_reference"])


def test_operator_review_checklist_and_validation_records_remain_pending() -> None:
    report = _load_report()

    assert tuple(check["check_id"] for check in report["operator_review_checklist"]) == EXPECTED_CHECK_IDS
    for check in report["operator_review_checklist"]:
        assert tuple(check.keys()) == (
            "check_id",
            "local_reference",
            "operator_review_status",
            "required_state",
            "review_label",
        )
        assert check["operator_review_status"] == OPERATOR_REVIEW_STATUS
        assert check["required_state"] == OPERATOR_REVIEW_STATUS
        _assert_allowed_existing_local_reference(check["local_reference"])

    assert report["required_validation_commands"] == [
        "python -m compileall pm_bot tests",
        "pytest pm_bot/tests tests/test_codex_queue_pmbot_templates.py",
    ]
    assert [record["command_label"] for record in report["validation_command_records"]] == report[
        "required_validation_commands"
    ]
    for record in report["validation_command_records"]:
        assert tuple(record.keys()) == ("command_label", "local_reference", "operator_review_status", "status")
        assert record["operator_review_status"] == OPERATOR_REVIEW_STATUS
        assert record["status"] == "not_run_static_record"
        _assert_allowed_existing_local_reference(record["local_reference"])


def test_excluded_prefixes_and_safety_boundaries_are_closed() -> None:
    report = _load_report()

    assert tuple(report["excluded_path_prefixes"]) == EXPECTED_EXCLUDED_PREFIXES
    assert report["safety_boundaries"] == EXPECTED_SAFETY_BOUNDARIES
    assert report["safety_boundaries"]["local_fixtures_only"] is True
    assert report["safety_boundaries"]["local_static_samples_only"] is True
    assert report["safety_boundaries"]["operator_review_required"] is True
    assert report["safety_boundaries"]["paper_mode_only"] is True
    assert all(value is False for key, value in report["safety_boundaries"].items() if key.endswith("_allowed"))


def test_summary_counts_match_crypto_night_batch_acceptance_report_content() -> None:
    report = _load_report()
    local_references = {
        *(section["local_reference"] for section in report["acceptance_sections"]),
        *(artifact["local_reference"] for artifact in report["source_artifacts"]),
        *(check["local_reference"] for check in report["operator_review_checklist"]),
        *(record["local_reference"] for record in report["validation_command_records"]),
    }

    assert report["summary_counts"] == {
        "acceptance_sections": len(report["acceptance_sections"]),
        "acceptance_sections_pending_operator_review": sum(
            1
            for section in report["acceptance_sections"]
            if section["operator_review_status"] == OPERATOR_REVIEW_STATUS
        ),
        "allowed_path_prefixes": len(report["allowed_path_prefixes"]),
        "errors": len(report["errors"]),
        "excluded_path_prefixes": len(report["excluded_path_prefixes"]),
        "local_references": len(local_references),
        "operator_review_checks": len(report["operator_review_checklist"]),
        "operator_review_checks_pending_operator_review": sum(
            1
            for check in report["operator_review_checklist"]
            if check["operator_review_status"] == OPERATOR_REVIEW_STATUS
        ),
        "readiness_record_count": sum(section["readiness_record_count"] for section in report["acceptance_sections"]),
        "required_validation_commands": len(report["required_validation_commands"]),
        "source_artifacts": len(report["source_artifacts"]),
        "supporting_artifacts": sum(section["supporting_artifacts"] for section in report["acceptance_sections"]),
        "validation_command_records": len(report["validation_command_records"]),
        "warnings": len(report["warnings"]),
    }


def test_report_has_no_decision_scoring_or_selection_terms() -> None:
    report = _load_report()

    assert _find_disallowed_terms(report["acceptance_sections"]) == []
    assert _find_disallowed_terms(report["operator_review_checklist"]) == []


def test_markdown_report_registers_static_report_for_operator_review() -> None:
    markdown = MARKDOWN_PATH.read_text(encoding="utf-8")

    assert f"Report: `{REPORT_ID}`" in markdown
    assert f"Run mode: `{RUN_MODE}`" in markdown
    assert f"Operator review: `{OPERATOR_REVIEW_STATUS}`" in markdown
    for section_id in EXPECTED_SECTION_IDS:
        assert section_id in markdown
    assert "Acceptance sections: 6" in markdown
    assert "Readiness records: 25" in markdown
    assert "Source artifacts: 28" in markdown
    assert "pytest pm_bot/tests tests/test_codex_queue_pmbot_templates.py" in markdown
    assert "Not execution approval and not runtime input." in markdown


def test_documentation_registers_crypto_night_batch_acceptance_report_and_safety_boundary() -> None:
    document = DOC_PATH.read_text(encoding="utf-8")

    assert f"Task: `{TASK_ID}`" in document
    assert f"Report: `{REPORT_ID}`" in document
    assert f"Contract: `{CONTRACT_VERSION}`" in document
    assert f"Run mode: `{RUN_MODE}`" in document
    assert str(REPORT_PATH).replace("\\", "/") in document
    assert str(MARKDOWN_PATH).replace("\\", "/") in document
    assert "No forecast scoring, action guidance, market ranking" in document
    assert "This report is not execution approval and is not runtime input." in document


def _load_report() -> dict:
    return json.loads(REPORT_PATH.read_text(encoding="utf-8"))


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
            if key == "local_reference":
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
