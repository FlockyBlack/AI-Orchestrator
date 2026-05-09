from __future__ import annotations

import json
from pathlib import Path


DOC_PATH = Path("docs/PMBOT_CRYPTO_LIVE_020_CRYPTO_READINESS_NEXT_ACTION_BACKLOG_LOCAL_ONLY.md")
FIXTURE_PATH = Path("pm_bot/tests/fixtures/crypto_live/pmbot_crypto_readiness_next_action_backlog.valid.json")
TASK_ID = "PMBOT-CRYPTO-LIVE-020-CRYPTO-READINESS-NEXT-ACTION-BACKLOG-LOCAL-ONLY"
CONTRACT_ID = "pmbot-crypto-readiness-next-action-backlog"
CONTRACT_VERSION = "pmbot_crypto_readiness_next_action_backlog.v1"
BACKLOG_ID = "pmbot-crypto-readiness-next-action-backlog-001"
BACKLOG_NAME = "pmbot-crypto-readiness-next-action-backlog"
RUN_MODE = "local_static_crypto_readiness_next_action_backlog"
OPERATOR_REVIEW_STATUS = "pending_operator_review"
ALLOWED_LOCAL_PREFIXES = ("docs/", "pm_bot/readiness/", "pm_bot/tests/", "tests/")

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
EXPECTED_BACKLOG_RECORD_IDS = (
    "crypto_next_action_backlog_001.supervised_gap_matrix_review",
    "crypto_next_action_backlog_001.operator_gate_review",
    "crypto_next_action_backlog_001.stop_condition_review",
    "crypto_next_action_backlog_001.validation_replay_review",
    "crypto_next_action_backlog_001.ci_subset_review",
    "crypto_next_action_backlog_001.sensitive_path_review",
    "crypto_next_action_backlog_001.night_batch_report_review",
    "crypto_next_action_backlog_001.source_quality_link_review",
    "crypto_next_action_backlog_001.backlog_fixture_review",
)
EXPECTED_SOURCE_ARTIFACT_IDS = (
    "crypto_readiness_next_action_backlog_fixture",
    "crypto_readiness_next_action_backlog_document",
    "crypto_readiness_next_action_backlog_contract_test",
    "crypto_supervised_live_gap_matrix_document",
    "crypto_supervised_live_gap_matrix_fixture",
    "crypto_operator_gate_fixture",
    "crypto_stop_condition_mapping_fixture",
    "crypto_validation_replay_bundle_fixture",
    "crypto_ci_safe_validation_subset_fixture",
    "crypto_sensitive_path_exclusion_audit_fixture",
    "crypto_night_batch_acceptance_report_document",
    "crypto_rehearsal_source_quality_links_document",
    "queue_template_validation_test",
)
EXPECTED_SAFETY_BOUNDARIES = {
    "authenticated_endpoint_calls_allowed": False,
    "background_process_allowed": False,
    "browser_automation_allowed": False,
    "core_execution_wiring_changes_allowed": False,
    "credential_or_secret_access_allowed": False,
    "crypto_data_refresh_allowed": False,
    "decision_metric_output_allowed": False,
    "execution_endpoint_calls_allowed": False,
    "external_service_calls_allowed": False,
    "llm_provider_calls_allowed": False,
    "local_fixtures_only": True,
    "local_static_samples_only": True,
    "market_api_calls_allowed": False,
    "market_ranking_allowed": False,
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
    "status_mutation_allowed": False,
    "supervised_live_transition_allowed": False,
    "threshold_comparison_output_allowed": False,
    "timed_automation_allowed": False,
    "trade_instruction_allowed": False,
    "transaction_endpoint_calls_allowed": False,
    "wallet_or_signing_material_access_allowed": False,
}


def test_static_crypto_readiness_next_action_backlog_fixture_has_expected_contract() -> None:
    backlog = _load_backlog()

    assert tuple(backlog.keys()) == tuple(sorted(backlog.keys()))
    assert backlog["task_id"] == TASK_ID
    assert backlog["backlog_id"] == BACKLOG_ID
    assert backlog["backlog_name"] == BACKLOG_NAME
    assert backlog["contract_id"] == CONTRACT_ID
    assert backlog["contract_version"] == CONTRACT_VERSION
    assert backlog["run_mode"] == RUN_MODE
    assert backlog["created_at"] == "2026-05-09T08:00:00Z"
    assert backlog["local_only"] is True
    assert backlog["operator_review_required"] is True
    assert backlog["operator_review"] == {
        "reviewed_at": None,
        "reviewed_by": None,
        "status": OPERATOR_REVIEW_STATUS,
    }
    assert backlog["errors"] == []
    assert backlog["warnings"] == []


def test_backlog_records_are_fixed_local_descriptive_and_pending_operator_review() -> None:
    backlog = _load_backlog()
    source_artifact_ids = {artifact["artifact_id"] for artifact in backlog["source_artifacts"]}

    assert tuple(record["backlog_record_id"] for record in backlog["backlog_records"]) == EXPECTED_BACKLOG_RECORD_IDS
    assert tuple(record["record_index"] for record in backlog["backlog_records"]) == tuple(range(1, 10))
    for record in backlog["backlog_records"]:
        assert tuple(record.keys()) == (
            "backlog_record_id",
            "evidence_state",
            "local_reference",
            "operator_review_status",
            "record_index",
            "review_checkpoint",
            "review_group",
            "source_artifact_ids",
        )
        assert record["evidence_state"] == "local_static_record_present_pending_review"
        assert record["operator_review_status"] == OPERATOR_REVIEW_STATUS
        assert set(record["source_artifact_ids"]) <= source_artifact_ids
        _assert_allowed_existing_local_reference(record["local_reference"])


def test_source_artifacts_reference_allowed_existing_local_material() -> None:
    backlog = _load_backlog()

    assert tuple(backlog["allowed_path_prefixes"]) == ALLOWED_LOCAL_PREFIXES
    assert tuple(artifact["artifact_id"] for artifact in backlog["source_artifacts"]) == EXPECTED_SOURCE_ARTIFACT_IDS
    for artifact in backlog["source_artifacts"]:
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


def test_validation_command_records_match_required_local_checks() -> None:
    backlog = _load_backlog()

    assert backlog["required_validation_commands"] == [
        "python -m compileall pm_bot tests",
        "pytest pm_bot/tests tests/test_codex_queue_pmbot_templates.py",
    ]
    assert [record["command_label"] for record in backlog["validation_command_records"]] == backlog[
        "required_validation_commands"
    ]
    for record in backlog["validation_command_records"]:
        assert tuple(record.keys()) == (
            "command_label",
            "local_reference",
            "operator_review_status",
            "status",
        )
        assert record["operator_review_status"] == OPERATOR_REVIEW_STATUS
        assert record["status"] == "not_run_static_record"
        _assert_allowed_existing_local_reference(record["local_reference"])


def test_excluded_prefixes_and_safety_boundaries_are_closed() -> None:
    backlog = _load_backlog()

    assert tuple(backlog["excluded_path_prefixes"]) == EXPECTED_EXCLUDED_PREFIXES
    assert backlog["safety_boundaries"] == EXPECTED_SAFETY_BOUNDARIES
    assert backlog["safety_boundaries"]["local_fixtures_only"] is True
    assert backlog["safety_boundaries"]["local_static_samples_only"] is True
    assert backlog["safety_boundaries"]["operator_review_required"] is True
    assert backlog["safety_boundaries"]["paper_mode_only"] is True
    assert all(value is False for key, value in backlog["safety_boundaries"].items() if key.endswith("_allowed"))


def test_summary_counts_match_crypto_readiness_backlog_content() -> None:
    backlog = _load_backlog()
    local_references = {
        *(record["local_reference"] for record in backlog["backlog_records"]),
        *(artifact["local_reference"] for artifact in backlog["source_artifacts"]),
        *(record["local_reference"] for record in backlog["validation_command_records"]),
    }

    assert backlog["summary_counts"] == {
        "allowed_path_prefixes": len(backlog["allowed_path_prefixes"]),
        "backlog_records": len(backlog["backlog_records"]),
        "backlog_records_pending_operator_review": sum(
            1 for record in backlog["backlog_records"] if record["operator_review_status"] == OPERATOR_REVIEW_STATUS
        ),
        "errors": len(backlog["errors"]),
        "excluded_path_prefixes": len(backlog["excluded_path_prefixes"]),
        "local_references": len(local_references),
        "required_validation_commands": len(backlog["required_validation_commands"]),
        "source_artifacts": len(backlog["source_artifacts"]),
        "validation_command_records": len(backlog["validation_command_records"]),
        "warnings": len(backlog["warnings"]),
    }


def test_backlog_has_no_decision_scoring_or_selection_terms() -> None:
    backlog = _load_backlog()

    assert _find_disallowed_terms(backlog["backlog_records"]) == []
    assert _find_disallowed_terms(backlog["source_artifacts"]) == []
    assert _find_disallowed_terms(backlog["validation_command_records"]) == []


def test_documentation_registers_crypto_readiness_next_action_backlog_and_safety_boundary() -> None:
    document = DOC_PATH.read_text(encoding="utf-8")

    assert f"Task: `{TASK_ID}`" in document
    assert f"Backlog: `{BACKLOG_ID}`" in document
    assert f"Contract: `{CONTRACT_VERSION}`" in document
    assert f"Run mode: `{RUN_MODE}`" in document
    assert str(FIXTURE_PATH).replace("\\", "/") in document
    assert "No forecast scoring, action guidance, market ranking" in document
    assert "This backlog is not execution approval and is not runtime input." in document


def _load_backlog() -> dict:
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
            if key in {"local_reference", "source_task_id"}:
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
