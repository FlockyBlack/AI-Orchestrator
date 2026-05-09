from __future__ import annotations

import json
from pathlib import Path


DOC_PATH = Path("docs/PMBOT_CRYPTO_LIVE_017_CRYPTO_MORNING_REVIEW_CARD_LOCAL_ONLY.md")
CARD_PATH = Path("pm_bot/dashboard/samples/pmbot_crypto_morning_review_card.fixture.json")
REPORT_PATH = Path("pm_bot/dashboard/samples/pmbot_crypto_morning_review_card.fixture.md")
TASK_ID = "PMBOT-CRYPTO-LIVE-017-CRYPTO-MORNING-REVIEW-CARD-LOCAL-ONLY"
CONTRACT_ID = "pmbot-crypto-morning-review-card"
CONTRACT_VERSION = "pmbot_crypto_morning_review_card.v1"
CARD_ID = "pmbot-crypto-morning-review-card-001"
RUN_MODE = "local_static_crypto_morning_review_card"
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
    "crypto_dashboard_readiness_snapshot",
    "crypto_source_review_snapshot",
    "crypto_rehearsal_review_snapshot",
    "crypto_gate_review_snapshot",
    "crypto_validation_review_snapshot",
    "crypto_safety_review_snapshot",
)
EXPECTED_SOURCE_ARTIFACT_IDS = (
    "crypto_morning_review_card_document",
    "crypto_morning_review_card_sample",
    "crypto_morning_review_card_report",
    "crypto_morning_review_card_contract_test",
    "crypto_dashboard_readiness_summary_document",
    "crypto_dashboard_readiness_summary_sample",
    "crypto_dashboard_readiness_summary_report",
    "crypto_dashboard_readiness_summary_contract_test",
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
    "card_section_review",
    "source_artifact_review",
    "dashboard_summary_review",
    "operator_gate_review",
    "validation_review",
    "safety_boundary_review",
    "report_sample_review",
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
    "morning_review_card_runtime_input_allowed": False,
    "network_calls_allowed": False,
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
    "supervised_live_transition_allowed": False,
    "threshold_comparison_output_allowed": False,
    "timed_automation_allowed": False,
    "trade_instruction_allowed": False,
    "transaction_endpoint_calls_allowed": False,
    "wallet_or_signing_material_access_allowed": False,
}


def test_static_crypto_morning_review_card_has_expected_contract() -> None:
    card = _load_card()

    assert tuple(card.keys()) == tuple(sorted(card.keys()))
    assert card["task_id"] == TASK_ID
    assert card["card_id"] == CARD_ID
    assert card["card_label"] == "pmbot-crypto-morning-review-card"
    assert card["contract_id"] == CONTRACT_ID
    assert card["contract_version"] == CONTRACT_VERSION
    assert card["run_mode"] == RUN_MODE
    assert card["created_at"] == "2026-05-09T06:00:00Z"
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


def test_card_sections_are_fixed_local_pending_records() -> None:
    card = _load_card()
    source_artifact_ids = {artifact["artifact_id"] for artifact in card["source_artifacts"]}

    assert tuple(section["card_section_id"] for section in card["card_sections"]) == EXPECTED_SECTION_IDS
    for section in card["card_sections"]:
        assert tuple(section.keys()) == (
            "artifact_type",
            "card_section_id",
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
        assert section["status_label"] == "static_card_ready"
        assert section["primary_artifact_id"] in source_artifact_ids
        assert set(section["source_artifact_ids"]) <= source_artifact_ids
        assert section["supporting_artifacts"] == len(section["source_artifact_ids"])
        assert section["readiness_record_count"] >= 2
        _assert_allowed_existing_local_reference(section["local_reference"])


def test_source_artifacts_are_allowed_existing_local_references() -> None:
    card = _load_card()

    assert tuple(card["allowed_path_prefixes"]) == ALLOWED_LOCAL_PREFIXES
    assert tuple(card["source_artifacts"][index]["artifact_id"] for index in range(24)) == EXPECTED_SOURCE_ARTIFACT_IDS
    for artifact in card["source_artifacts"]:
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
    card = _load_card()

    assert tuple(check["check_id"] for check in card["operator_review_checklist"]) == EXPECTED_CHECK_IDS
    for check in card["operator_review_checklist"]:
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

    assert card["required_validation_commands"] == [
        "python -m compileall pm_bot tests",
        "pytest pm_bot/tests tests/test_codex_queue_pmbot_templates.py",
    ]
    assert [record["command_label"] for record in card["validation_command_records"]] == card[
        "required_validation_commands"
    ]
    for record in card["validation_command_records"]:
        assert tuple(record.keys()) == ("command_label", "local_reference", "operator_review_status", "status")
        assert record["operator_review_status"] == OPERATOR_REVIEW_STATUS
        assert record["status"] == "not_run_static_record"
        _assert_allowed_existing_local_reference(record["local_reference"])


def test_excluded_prefixes_and_safety_boundaries_are_closed() -> None:
    card = _load_card()

    assert tuple(card["excluded_path_prefixes"]) == EXPECTED_EXCLUDED_PREFIXES
    assert card["safety_boundaries"] == EXPECTED_SAFETY_BOUNDARIES
    assert card["safety_boundaries"]["local_fixtures_only"] is True
    assert card["safety_boundaries"]["local_static_samples_only"] is True
    assert card["safety_boundaries"]["operator_review_required"] is True
    assert card["safety_boundaries"]["paper_mode_only"] is True
    assert all(value is False for key, value in card["safety_boundaries"].items() if key.endswith("_allowed"))


def test_summary_counts_match_crypto_morning_review_card_content() -> None:
    card = _load_card()
    local_references = {
        *(section["local_reference"] for section in card["card_sections"]),
        *(artifact["local_reference"] for artifact in card["source_artifacts"]),
        *(check["local_reference"] for check in card["operator_review_checklist"]),
        *(record["local_reference"] for record in card["validation_command_records"]),
    }

    assert card["summary_counts"] == {
        "allowed_path_prefixes": len(card["allowed_path_prefixes"]),
        "card_sections": len(card["card_sections"]),
        "card_sections_pending_operator_review": sum(
            1
            for section in card["card_sections"]
            if section["operator_review_status"] == OPERATOR_REVIEW_STATUS
        ),
        "errors": len(card["errors"]),
        "excluded_path_prefixes": len(card["excluded_path_prefixes"]),
        "local_references": len(local_references),
        "operator_review_checks": len(card["operator_review_checklist"]),
        "operator_review_checks_pending_operator_review": sum(
            1
            for check in card["operator_review_checklist"]
            if check["operator_review_status"] == OPERATOR_REVIEW_STATUS
        ),
        "readiness_record_count": sum(section["readiness_record_count"] for section in card["card_sections"]),
        "required_validation_commands": len(card["required_validation_commands"]),
        "source_artifacts": len(card["source_artifacts"]),
        "supporting_artifacts": sum(section["supporting_artifacts"] for section in card["card_sections"]),
        "validation_command_records": len(card["validation_command_records"]),
        "warnings": len(card["warnings"]),
    }


def test_card_has_no_decision_scoring_or_selection_terms() -> None:
    card = _load_card()

    assert _find_disallowed_terms(card["card_sections"]) == []
    assert _find_disallowed_terms(card["operator_review_checklist"]) == []


def test_markdown_report_registers_static_card_for_operator_review() -> None:
    report = REPORT_PATH.read_text(encoding="utf-8")

    assert f"Card: `{CARD_ID}`" in report
    assert f"Run mode: `{RUN_MODE}`" in report
    assert f"Operator review: `{OPERATOR_REVIEW_STATUS}`" in report
    for section_id in EXPECTED_SECTION_IDS:
        assert section_id in report
    assert "Card sections: 6" in report
    assert "Readiness records: 20" in report
    assert "Source artifacts: 24" in report
    assert "pytest pm_bot/tests tests/test_codex_queue_pmbot_templates.py" in report
    assert "Not execution approval and not runtime input." in report


def test_documentation_registers_crypto_morning_review_card_and_safety_boundary() -> None:
    document = DOC_PATH.read_text(encoding="utf-8")

    assert f"Task: `{TASK_ID}`" in document
    assert f"Card: `{CARD_ID}`" in document
    assert f"Contract: `{CONTRACT_VERSION}`" in document
    assert f"Run mode: `{RUN_MODE}`" in document
    assert str(CARD_PATH).replace("\\", "/") in document
    assert str(REPORT_PATH).replace("\\", "/") in document
    assert "No forecast scoring, action guidance, market ranking" in document
    assert "This card is not execution approval and is not runtime input." in document


def _load_card() -> dict:
    return json.loads(CARD_PATH.read_text(encoding="utf-8"))


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
