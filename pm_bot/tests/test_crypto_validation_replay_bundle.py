from __future__ import annotations

import json
from pathlib import Path


DOC_PATH = Path("docs/PMBOT_CRYPTO_LIVE_012_CRYPTO_VALIDATION_REPLAY_BUNDLE_LOCAL_ONLY.md")
FIXTURE_PATH = Path("pm_bot/tests/fixtures/crypto_live/pmbot_crypto_validation_replay_bundle.valid.json")
TASK_ID = "PMBOT-CRYPTO-LIVE-012-CRYPTO-VALIDATION-REPLAY-BUNDLE-LOCAL-ONLY"
BUNDLE_ID = "pmbot-crypto-validation-replay-bundle-001"
BUNDLE_NAME = "pmbot-crypto-validation-replay-bundle"
CONTRACT_ID = "pmbot-crypto-validation-replay-bundle"
CONTRACT_VERSION = "pmbot_crypto_validation_replay_bundle.v1"
RUN_MODE = "local_static_crypto_validation_replay_bundle"
OPERATOR_REVIEW_STATUS = "pending_operator_review"
ALLOWED_LOCAL_PREFIXES = ("docs/", "pm_bot/readiness/", "pm_bot/simulated_decisions/", "pm_bot/tests/", "tests/")

EXPECTED_RECORD_FIELDS = (
    "artifact_id",
    "artifact_role",
    "artifact_type",
    "contract_version",
    "expected_state",
    "local_reference",
    "operator_review_status",
    "record_id",
    "record_label",
    "source_task_id",
)
EXPECTED_RECORD_IDS = (
    "crypto_validation_replay_bundle_001.bundle_fixture",
    "crypto_validation_replay_bundle_001.bundle_document",
    "crypto_validation_replay_bundle_001.crypto_supervised_live_gap_matrix_document",
    "crypto_validation_replay_bundle_001.crypto_supervised_live_gap_matrix_fixture",
    "crypto_validation_replay_bundle_001.crypto_operator_gate_fixture",
    "crypto_validation_replay_bundle_001.crypto_stop_condition_mapping_fixture",
    "crypto_validation_replay_bundle_001.crypto_outcome_evidence_bundle_fixture",
    "crypto_validation_replay_bundle_001.crypto_observation_replay_fixture",
    "crypto_validation_replay_bundle_001.crypto_rehearsal_packet_fixture",
    "crypto_validation_replay_bundle_001.simulated_decision_replay_summary_sample",
    "crypto_validation_replay_bundle_001.queue_template_validation_test",
    "crypto_validation_replay_bundle_001.bundle_contract_test",
)
EXPECTED_SECTION_IDS = (
    "bundle_identity_replay",
    "crypto_readiness_gate_replay",
    "crypto_evidence_chain_replay",
    "simulated_decision_static_replay",
    "queue_template_validation_replay",
    "validation_command_replay",
)
EXPECTED_CHECK_IDS = (
    "local_reference_replay",
    "crypto_readiness_record_replay",
    "static_fixture_replay",
    "validation_command_replay",
    "closed_boundary_replay",
    "human_review_replay",
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
    "replay_mutates_source_artifacts_allowed": False,
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


def test_static_crypto_validation_replay_bundle_fixture_has_expected_contract() -> None:
    bundle = _load_bundle()

    assert tuple(bundle.keys()) == tuple(sorted(bundle.keys()))
    assert bundle["task_id"] == TASK_ID
    assert bundle["bundle_id"] == BUNDLE_ID
    assert bundle["bundle_name"] == BUNDLE_NAME
    assert bundle["contract_id"] == CONTRACT_ID
    assert bundle["contract_version"] == CONTRACT_VERSION
    assert bundle["run_mode"] == RUN_MODE
    assert bundle["created_at"] == "2026-05-09T04:30:00Z"
    assert bundle["local_only"] is True
    assert bundle["operator_review_required"] is True
    assert bundle["operator_review"] == {
        "reviewed_at": None,
        "reviewed_by": None,
        "status": OPERATOR_REVIEW_STATUS,
    }
    assert bundle["errors"] == []
    assert bundle["warnings"] == []


def test_replay_records_are_fixed_local_and_pending_operator_review() -> None:
    bundle = _load_bundle()

    assert tuple(bundle["replay_record_fields"]) == EXPECTED_RECORD_FIELDS
    assert tuple(record["record_id"] for record in bundle["replay_records"]) == EXPECTED_RECORD_IDS
    for record in bundle["replay_records"]:
        assert tuple(record.keys()) == EXPECTED_RECORD_FIELDS
        assert record["operator_review_status"] == OPERATOR_REVIEW_STATUS
        assert record["expected_state"] in {
            "local_validation_reference",
            "pending_operator_review",
            "recorded_for_operator_review",
        }
        assert record["source_task_id"]
        _assert_allowed_existing_local_reference(record["local_reference"])


def test_replay_sections_reference_declared_replay_records() -> None:
    bundle = _load_bundle()
    record_ids = {record["record_id"] for record in bundle["replay_records"]}

    assert tuple(section["section_id"] for section in bundle["replay_sections"]) == EXPECTED_SECTION_IDS
    for section in bundle["replay_sections"]:
        assert tuple(section.keys()) == tuple(sorted(section.keys()))
        assert set(section) == {
            "operator_review_status",
            "replay_role",
            "section_id",
            "section_label",
            "source_record_ids",
        }
        assert section["operator_review_status"] == OPERATOR_REVIEW_STATUS
        assert section["source_record_ids"]
        assert set(section["source_record_ids"]) <= record_ids


def test_replay_checklist_and_validation_command_records_remain_pending() -> None:
    bundle = _load_bundle()

    assert tuple(check["check_id"] for check in bundle["replay_checklist"]) == EXPECTED_CHECK_IDS
    for check in bundle["replay_checklist"]:
        assert tuple(check.keys()) == tuple(sorted(check.keys()))
        assert set(check) == {"check_id", "description", "required_evidence", "status"}
        assert check["status"] == OPERATOR_REVIEW_STATUS

    assert bundle["required_validation_commands"] == [
        "python -m compileall pm_bot tests",
        "pytest pm_bot/tests tests/test_codex_queue_pmbot_templates.py",
    ]
    assert [record["command_label"] for record in bundle["validation_command_records"]] == bundle[
        "required_validation_commands"
    ]
    for record in bundle["validation_command_records"]:
        assert tuple(record.keys()) == tuple(sorted(record.keys()))
        assert record["operator_review_status"] == OPERATOR_REVIEW_STATUS
        assert record["status"] == "not_run_static_record"
        _assert_allowed_existing_local_reference(record["local_reference"])


def test_excluded_prefixes_match_sensitive_and_execution_boundaries() -> None:
    bundle = _load_bundle()

    assert tuple(bundle["excluded_path_prefixes"]) == EXPECTED_EXCLUDED_PREFIXES


def test_safety_boundaries_are_closed_for_crypto_validation_replay_bundle() -> None:
    bundle = _load_bundle()

    assert bundle["safety_boundaries"] == EXPECTED_SAFETY_BOUNDARIES
    assert bundle["safety_boundaries"]["local_fixtures_only"] is True
    assert bundle["safety_boundaries"]["local_static_samples_only"] is True
    assert bundle["safety_boundaries"]["operator_review_required"] is True
    assert bundle["safety_boundaries"]["paper_mode_only"] is True
    assert all(value is False for key, value in bundle["safety_boundaries"].items() if key.endswith("_allowed"))


def test_summary_counts_match_crypto_validation_replay_bundle_content() -> None:
    bundle = _load_bundle()
    local_references = {record["local_reference"] for record in bundle["replay_records"]}
    local_references.update(record["local_reference"] for record in bundle["validation_command_records"])

    assert bundle["summary_counts"] == {
        "errors": len(bundle["errors"]),
        "excluded_path_prefixes": len(bundle["excluded_path_prefixes"]),
        "local_references": len(local_references),
        "replay_checklist_items": len(bundle["replay_checklist"]),
        "replay_records": len(bundle["replay_records"]),
        "replay_records_pending_operator_review": sum(
            1 for record in bundle["replay_records"] if record["operator_review_status"] == OPERATOR_REVIEW_STATUS
        ),
        "replay_sections": len(bundle["replay_sections"]),
        "replay_sections_pending_operator_review": sum(
            1 for section in bundle["replay_sections"] if section["operator_review_status"] == OPERATOR_REVIEW_STATUS
        ),
        "required_validation_commands": len(bundle["required_validation_commands"]),
        "validation_command_records": len(bundle["validation_command_records"]),
        "warnings": len(bundle["warnings"]),
    }


def test_fixture_references_only_allowed_local_static_material() -> None:
    bundle = _load_bundle()
    references = sorted({record["local_reference"] for record in bundle["replay_records"]})

    assert references == [
        "docs/PMBOT_CRYPTO_LIVE_011_CRYPTO_SUPERVISED_LIVE_GAP_MATRIX_LOCAL_ONLY.md",
        "docs/PMBOT_CRYPTO_LIVE_012_CRYPTO_VALIDATION_REPLAY_BUNDLE_LOCAL_ONLY.md",
        "pm_bot/simulated_decisions/samples/simulated_decision_replay_summary.fixture.json",
        "pm_bot/tests/fixtures/crypto_live/pmbot_crypto_operator_approval_gate_record.valid.json",
        "pm_bot/tests/fixtures/crypto_live/pmbot_crypto_outcome_evidence_bundle.valid.json",
        "pm_bot/tests/fixtures/crypto_live/pmbot_crypto_paperlive_observation_replay.valid.json",
        "pm_bot/tests/fixtures/crypto_live/pmbot_crypto_paperlive_rehearsal_packet.valid.json",
        "pm_bot/tests/fixtures/crypto_live/pmbot_crypto_stop_condition_mapping.valid.json",
        "pm_bot/tests/fixtures/crypto_live/pmbot_crypto_supervised_live_gap_matrix.valid.json",
        "pm_bot/tests/fixtures/crypto_live/pmbot_crypto_validation_replay_bundle.valid.json",
        "pm_bot/tests/test_crypto_validation_replay_bundle.py",
        "tests/test_codex_queue_pmbot_templates.py",
    ]
    for reference in references:
        _assert_allowed_existing_local_reference(reference)


def test_fixture_has_no_decision_scoring_or_selection_terms() -> None:
    bundle = _load_bundle()

    assert _find_disallowed_terms(bundle) == []


def test_documentation_registers_crypto_validation_replay_bundle_and_safety_boundary() -> None:
    document = DOC_PATH.read_text(encoding="utf-8")

    assert f"Task: `{TASK_ID}`" in document
    assert f"Bundle: `{BUNDLE_ID}`" in document
    assert f"Contract: `{CONTRACT_VERSION}`" in document
    assert f"Run mode: `{RUN_MODE}`" in document
    assert str(FIXTURE_PATH).replace("\\", "/") in document
    assert "No forecast scoring, action guidance, market ranking" in document
    assert "This bundle is not execution approval and is not runtime input." in document


def _load_bundle() -> dict:
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
