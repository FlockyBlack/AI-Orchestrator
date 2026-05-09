from __future__ import annotations

import json
from pathlib import Path


DOC_PATH = Path("docs/PMBOT_CRYPTO_LIVE_013_CRYPTO_CI_SAFE_VALIDATION_SUBSET_LOCAL_ONLY.md")
FIXTURE_PATH = Path("pm_bot/tests/fixtures/crypto_live/pmbot_crypto_ci_safe_validation_subset.valid.json")
TASK_ID = "PMBOT-CRYPTO-LIVE-013-CRYPTO-CI-SAFE-VALIDATION-SUBSET-LOCAL-ONLY"
CONTRACT_ID = "pmbot-crypto-ci-safe-validation-subset"
CONTRACT_VERSION = "pmbot_crypto_ci_safe_validation_subset.v1"
SUBSET_ID = "pmbot-crypto-ci-safe-validation-subset-001"
SUBSET_NAME = "pmbot-crypto-ci-safe-validation-subset"
RUN_MODE = "local_static_crypto_ci_safe_validation_subset"
OPERATOR_REVIEW_STATUS = "pending_operator_review"
ALLOWED_LOCAL_PREFIXES = ("docs/", "pm_bot/tests/", "tests/")

EXPECTED_TARGET_FIELDS = (
    "artifact_id",
    "artifact_role",
    "artifact_type",
    "contract_version",
    "expected_state",
    "local_reference",
    "operator_review_status",
    "source_task_id",
    "target_id",
    "target_label",
)
EXPECTED_TARGET_IDS = (
    "crypto_ci_safe_validation_subset_001.subset_fixture",
    "crypto_ci_safe_validation_subset_001.subset_document",
    "crypto_ci_safe_validation_subset_001.subset_contract_test",
    "crypto_ci_safe_validation_subset_001.crypto_validation_replay_bundle_fixture",
    "crypto_ci_safe_validation_subset_001.crypto_supervised_live_gap_matrix_fixture",
    "crypto_ci_safe_validation_subset_001.crypto_operator_gate_fixture",
    "crypto_ci_safe_validation_subset_001.crypto_stop_condition_mapping_fixture",
    "crypto_ci_safe_validation_subset_001.crypto_outcome_evidence_bundle_fixture",
    "crypto_ci_safe_validation_subset_001.crypto_observation_replay_fixture",
    "crypto_ci_safe_validation_subset_001.crypto_rehearsal_packet_fixture",
    "crypto_ci_safe_validation_subset_001.queue_template_validation_test",
)
EXPECTED_SECTION_IDS = (
    "subset_identity_review",
    "crypto_readiness_gate_review",
    "crypto_replay_chain_review",
    "queue_template_validation_review",
    "validation_command_review",
    "closed_boundary_review",
)
EXPECTED_CHECK_IDS = (
    "local_reference_scope",
    "static_fixture_scope",
    "validation_command_scope",
    "crypto_readiness_gate_scope",
    "closed_boundary_scope",
    "sensitive_path_boundary",
    "human_review_boundary",
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
    "ci_subset_mutates_source_artifacts_allowed": False,
    "credential_or_secret_access_allowed": False,
    "crypto_data_refresh_allowed": False,
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
    "runtime_or_dispatcher_changes_allowed": False,
    "scheduler_or_worker_allowed": False,
    "sensitive_path_access_allowed": False,
    "supervised_live_transition_allowed": False,
    "threshold_comparison_output_allowed": False,
    "timed_automation_allowed": False,
    "trade_instruction_allowed": False,
    "transaction_endpoint_calls_allowed": False,
    "value_transform_allowed": False,
    "wallet_or_signing_material_access_allowed": False,
}


def test_static_crypto_ci_safe_validation_subset_fixture_has_expected_contract() -> None:
    subset = _load_subset()

    assert tuple(subset.keys()) == tuple(sorted(subset.keys()))
    assert subset["task_id"] == TASK_ID
    assert subset["subset_id"] == SUBSET_ID
    assert subset["subset_name"] == SUBSET_NAME
    assert subset["contract_id"] == CONTRACT_ID
    assert subset["contract_version"] == CONTRACT_VERSION
    assert subset["run_mode"] == RUN_MODE
    assert subset["created_at"] == "2026-05-09T04:45:00Z"
    assert subset["local_only"] is True
    assert subset["operator_review_required"] is True
    assert subset["operator_review"] == {
        "reviewed_at": None,
        "reviewed_by": None,
        "status": OPERATOR_REVIEW_STATUS,
    }
    assert subset["errors"] == []
    assert subset["warnings"] == []


def test_validation_targets_are_fixed_local_allowed_paths() -> None:
    subset = _load_subset()

    assert tuple(subset["validation_target_fields"]) == EXPECTED_TARGET_FIELDS
    assert tuple(target["target_id"] for target in subset["validation_targets"]) == EXPECTED_TARGET_IDS
    for target in subset["validation_targets"]:
        assert tuple(target.keys()) == EXPECTED_TARGET_FIELDS
        assert target["operator_review_status"] == OPERATOR_REVIEW_STATUS
        assert target["expected_state"] in {
            "local_validation_reference",
            "pending_operator_review",
        }
        assert target["source_task_id"]
        _assert_allowed_existing_local_reference(target["local_reference"])


def test_subset_sections_reference_declared_validation_targets() -> None:
    subset = _load_subset()
    target_ids = {target["target_id"] for target in subset["validation_targets"]}

    assert tuple(section["section_id"] for section in subset["subset_sections"]) == EXPECTED_SECTION_IDS
    for section in subset["subset_sections"]:
        assert tuple(section.keys()) == tuple(sorted(section.keys()))
        assert set(section) == {
            "operator_review_status",
            "section_id",
            "section_label",
            "section_role",
            "source_target_ids",
        }
        assert section["operator_review_status"] == OPERATOR_REVIEW_STATUS
        assert section["source_target_ids"]
        assert set(section["source_target_ids"]) <= target_ids


def test_subset_checks_and_validation_command_records_remain_pending() -> None:
    subset = _load_subset()

    assert tuple(check["check_id"] for check in subset["subset_checks"]) == EXPECTED_CHECK_IDS
    for check in subset["subset_checks"]:
        assert tuple(check.keys()) == tuple(sorted(check.keys()))
        assert set(check) == {
            "check_id",
            "expected_state",
            "local_reference",
            "operator_review_status",
            "review_label",
        }
        assert check["operator_review_status"] == OPERATOR_REVIEW_STATUS
        _assert_allowed_existing_local_reference(check["local_reference"])

    assert subset["required_validation_commands"] == [
        "python -m compileall pm_bot tests",
        "pytest pm_bot/tests tests/test_codex_queue_pmbot_templates.py",
    ]
    assert [record["command_label"] for record in subset["validation_command_records"]] == subset[
        "required_validation_commands"
    ]
    for record in subset["validation_command_records"]:
        assert tuple(record.keys()) == tuple(sorted(record.keys()))
        assert record["operator_review_status"] == OPERATOR_REVIEW_STATUS
        assert record["status"] == "not_run_static_record"
        _assert_allowed_existing_local_reference(record["local_reference"])


def test_excluded_prefixes_match_sensitive_and_execution_boundaries() -> None:
    subset = _load_subset()

    assert tuple(subset["excluded_path_prefixes"]) == EXPECTED_EXCLUDED_PREFIXES


def test_safety_boundaries_are_closed_for_crypto_ci_safe_validation_subset() -> None:
    subset = _load_subset()

    assert subset["safety_boundaries"] == EXPECTED_SAFETY_BOUNDARIES
    assert subset["safety_boundaries"]["local_fixtures_only"] is True
    assert subset["safety_boundaries"]["local_static_samples_only"] is True
    assert subset["safety_boundaries"]["operator_review_required"] is True
    assert subset["safety_boundaries"]["paper_mode_only"] is True
    assert all(value is False for key, value in subset["safety_boundaries"].items() if key.endswith("_allowed"))


def test_summary_counts_match_crypto_ci_safe_validation_subset_content() -> None:
    subset = _load_subset()
    local_references = {target["local_reference"] for target in subset["validation_targets"]}
    local_references.update(check["local_reference"] for check in subset["subset_checks"])
    local_references.update(record["local_reference"] for record in subset["validation_command_records"])

    assert subset["summary_counts"] == {
        "errors": len(subset["errors"]),
        "excluded_path_prefixes": len(subset["excluded_path_prefixes"]),
        "local_references": len(local_references),
        "required_validation_commands": len(subset["required_validation_commands"]),
        "subset_checks": len(subset["subset_checks"]),
        "subset_checks_pending_operator_review": sum(
            1 for check in subset["subset_checks"] if check["operator_review_status"] == OPERATOR_REVIEW_STATUS
        ),
        "subset_sections": len(subset["subset_sections"]),
        "subset_sections_pending_operator_review": sum(
            1 for section in subset["subset_sections"] if section["operator_review_status"] == OPERATOR_REVIEW_STATUS
        ),
        "validation_command_records": len(subset["validation_command_records"]),
        "validation_targets": len(subset["validation_targets"]),
        "validation_targets_pending_operator_review": sum(
            1 for target in subset["validation_targets"] if target["operator_review_status"] == OPERATOR_REVIEW_STATUS
        ),
        "warnings": len(subset["warnings"]),
    }


def test_fixture_references_only_allowed_local_static_material() -> None:
    subset = _load_subset()
    references = sorted(
        {
            *(target["local_reference"] for target in subset["validation_targets"]),
            *(check["local_reference"] for check in subset["subset_checks"]),
            *(record["local_reference"] for record in subset["validation_command_records"]),
        }
    )

    assert references == [
        "docs/PMBOT_CRYPTO_LIVE_013_CRYPTO_CI_SAFE_VALIDATION_SUBSET_LOCAL_ONLY.md",
        "pm_bot/tests/fixtures/crypto_live/pmbot_crypto_ci_safe_validation_subset.valid.json",
        "pm_bot/tests/fixtures/crypto_live/pmbot_crypto_operator_approval_gate_record.valid.json",
        "pm_bot/tests/fixtures/crypto_live/pmbot_crypto_outcome_evidence_bundle.valid.json",
        "pm_bot/tests/fixtures/crypto_live/pmbot_crypto_paperlive_observation_replay.valid.json",
        "pm_bot/tests/fixtures/crypto_live/pmbot_crypto_paperlive_rehearsal_packet.valid.json",
        "pm_bot/tests/fixtures/crypto_live/pmbot_crypto_stop_condition_mapping.valid.json",
        "pm_bot/tests/fixtures/crypto_live/pmbot_crypto_supervised_live_gap_matrix.valid.json",
        "pm_bot/tests/fixtures/crypto_live/pmbot_crypto_validation_replay_bundle.valid.json",
        "pm_bot/tests/test_crypto_ci_safe_validation_subset.py",
        "pm_bot/tests/test_sensitive_path_exclusion_audit.py",
        "tests/test_codex_queue_pmbot_templates.py",
    ]
    for reference in references:
        _assert_allowed_existing_local_reference(reference)


def test_fixture_has_no_decision_scoring_or_selection_terms() -> None:
    subset = _load_subset()

    assert _find_disallowed_terms(subset) == []


def test_documentation_registers_crypto_ci_safe_validation_subset_and_safety_boundary() -> None:
    document = DOC_PATH.read_text(encoding="utf-8")

    assert f"Task: `{TASK_ID}`" in document
    assert f"Subset: `{SUBSET_ID}`" in document
    assert f"Contract: `{CONTRACT_VERSION}`" in document
    assert f"Run mode: `{RUN_MODE}`" in document
    assert str(FIXTURE_PATH).replace("\\", "/") in document
    assert "No forecast scoring, action guidance, market ranking" in document
    assert "This subset is not execution approval and is not runtime input." in document


def _load_subset() -> dict:
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
            if key in {"excluded_path_prefixes", "local_reference"}:
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
