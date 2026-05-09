from __future__ import annotations

import json
from pathlib import Path


DOC_PATH = Path("docs/PMBOT_CRYPTO_LIVE_010_CRYPTO_STOP_CONDITION_MAPPING_LOCAL_ONLY.md")
FIXTURE_PATH = Path("pm_bot/tests/fixtures/crypto_live/pmbot_crypto_stop_condition_mapping.valid.json")
OPERATOR_GATE_FIXTURE_PATH = Path("pm_bot/tests/fixtures/crypto_live/pmbot_crypto_operator_approval_gate_record.valid.json")
TASK_ID = "PMBOT-CRYPTO-LIVE-010-CRYPTO-STOP-CONDITION-MAPPING-LOCAL-ONLY"
CONTRACT_ID = "pmbot-crypto-stop-condition-mapping"
CONTRACT_VERSION = "pmbot_crypto_stop_condition_mapping.v1"
MAPPING_ID = "pmbot-crypto-stop-condition-mapping-001"
RUN_MODE = "local_static_crypto_stop_condition_mapping"
OPERATOR_REVIEW_STATUS = "pending_operator_review"
ALLOWED_LOCAL_PREFIXES = ("docs/", "pm_bot/readiness/", "pm_bot/tests/", "tests/")

EXPECTED_STOP_CONDITION_FIELDS = (
    "condition_class",
    "condition_id",
    "condition_label",
    "excluded_operations",
    "manual_record_required",
    "mapped_gate_id",
    "mapped_source_artifact_id",
    "operator_review_status",
    "required_operator_record",
    "stop_state",
    "trigger_evidence_reference",
    "trigger_source",
)
EXPECTED_CONDITION_IDS = (
    "operator_manual_stop_request",
    "crypto_local_artifact_boundary_breach",
    "crypto_forbidden_operation_request_detected",
    "crypto_validation_command_failed",
    "crypto_source_record_label_dispute",
    "crypto_rehearsal_record_mismatch",
    "crypto_observation_replay_chain_mismatch",
    "crypto_outcome_state_changed_without_record",
    "crypto_operator_gate_record_missing",
)
EXPECTED_EXCLUDED_OPERATIONS = (
    "network_endpoint_fetch",
    "authenticated_request",
    "credential_lookup",
    "wallet_balance_read",
    "transaction_preparation",
    "order_submission",
    "runtime_dispatch",
    "browser_automation",
    "background_process_start",
    "automated_session_restart",
)
EXPECTED_REQUIRED_RECORD_FIELDS = (
    "record_id",
    "condition_id",
    "observed_at_utc",
    "observed_by",
    "local_evidence_reference",
    "prior_pilot_state",
    "new_pilot_state",
    "operator_review_status",
    "unresolved_blockers",
)
EXPECTED_CHECK_IDS = (
    "condition_catalog_review",
    "trigger_evidence_review",
    "mapped_gate_review",
    "operator_record_field_review",
    "sensitive_path_exclusion_check",
    "runtime_boundary_check",
    "output_boundary_check",
    "validation_replay_check",
)
EXPECTED_RULE_IDS = (
    "manual_stop_precedence",
    "closed_boundary_precedence",
    "local_evidence_required",
    "validation_failure_stop",
    "no_restart_without_operator_record",
    "no_transition_from_pending_mapping",
)
EXPECTED_SOURCE_ARTIFACT_IDS = (
    "crypto_live_001_read_only_contract_doc",
    "crypto_live_002_data_source_inventory_doc",
    "crypto_live_003_source_evidence_link_map_doc",
    "crypto_live_004_source_staleness_check_spec_doc",
    "crypto_live_005_source_contradiction_ledger_doc",
    "crypto_live_006_rehearsal_packet_doc",
    "crypto_live_006_rehearsal_packet_fixture",
    "crypto_live_007_observation_replay_doc",
    "crypto_live_007_observation_replay_fixture",
    "crypto_live_008_outcome_evidence_bundle_doc",
    "crypto_live_008_outcome_evidence_bundle_fixture",
    "crypto_live_009_operator_gate_doc",
    "crypto_live_009_operator_gate_fixture",
    "pmbot_queue_template_validation",
)
EXPECTED_SAFETY_BOUNDARIES = {
    "authenticated_endpoint_calls_allowed": False,
    "automated_restart_allowed": False,
    "background_process_allowed": False,
    "browser_automation_allowed": False,
    "condition_trigger_automation_allowed": False,
    "credential_or_secret_access_allowed": False,
    "crypto_data_refresh_allowed": False,
    "execution_endpoint_calls_allowed": False,
    "external_service_calls_allowed": False,
    "llm_provider_calls_allowed": False,
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
    "stop_condition_mutates_runtime_allowed": False,
    "supervised_live_transition_allowed": False,
    "threshold_comparison_output_allowed": False,
    "trade_instruction_allowed": False,
    "transaction_endpoint_calls_allowed": False,
    "transition_without_record_allowed": False,
    "value_transform_allowed": False,
    "wallet_or_signing_material_access_allowed": False,
}


def test_static_crypto_stop_condition_mapping_fixture_has_expected_contract() -> None:
    mapping = _load_mapping()

    assert tuple(mapping.keys()) == tuple(sorted(mapping.keys()))
    assert mapping["task_id"] == TASK_ID
    assert mapping["contract_id"] == CONTRACT_ID
    assert mapping["contract_version"] == CONTRACT_VERSION
    assert mapping["mapping_id"] == MAPPING_ID
    assert mapping["run_mode"] == RUN_MODE
    assert mapping["created_at"] == "2026-05-09T03:50:00Z"
    assert mapping["local_only"] is True
    assert mapping["operator_review_required"] is True
    assert mapping["operator_review"] == {
        "reviewed_at": None,
        "reviewed_by": None,
        "status": OPERATOR_REVIEW_STATUS,
    }
    assert mapping["errors"] == []
    assert mapping["warnings"] == []


def test_stop_condition_rows_are_fixed_local_pending_and_manual() -> None:
    mapping = _load_mapping()

    assert tuple(mapping["stop_condition_fields"]) == EXPECTED_STOP_CONDITION_FIELDS
    assert tuple(record["condition_id"] for record in mapping["stop_condition_records"]) == EXPECTED_CONDITION_IDS

    for record in mapping["stop_condition_records"]:
        assert tuple(record.keys()) == tuple(sorted(record.keys()))
        assert set(record) == set(EXPECTED_STOP_CONDITION_FIELDS)
        assert record["manual_record_required"] is True
        assert record["operator_review_status"] == OPERATOR_REVIEW_STATUS
        assert record["stop_state"] in {
            "blocked_until_gate_record_complete",
            "stopped_pending_artifact_review",
            "stopped_pending_operator_record",
            "stopped_pending_outcome_review",
            "stopped_pending_rehearsal_review",
            "stopped_pending_replay_review",
            "stopped_pending_safety_review",
            "stopped_pending_source_review",
            "stopped_pending_validation_review",
        }
        assert tuple(record["excluded_operations"]) == EXPECTED_EXCLUDED_OPERATIONS
        _assert_allowed_existing_local_reference(record["trigger_evidence_reference"])


def test_stop_condition_rows_map_to_operator_gate_records_and_source_artifacts() -> None:
    mapping = _load_mapping()
    operator_gate = _load_json(OPERATOR_GATE_FIXTURE_PATH)
    gate_ids = {record["gate_id"] for record in operator_gate["gate_records"]}
    artifact_ids = {artifact["artifact_id"] for artifact in mapping["source_artifacts"]}

    for record in mapping["stop_condition_records"]:
        assert record["mapped_gate_id"] in gate_ids
        assert record["mapped_source_artifact_id"] in artifact_ids


def test_required_operator_record_fields_rules_and_checks_are_deterministic() -> None:
    mapping = _load_mapping()

    assert tuple(mapping["required_operator_record_fields"]) == EXPECTED_REQUIRED_RECORD_FIELDS
    assert tuple(rule["rule_id"] for rule in mapping["stop_condition_rules"]) == EXPECTED_RULE_IDS
    assert all(tuple(rule.keys()) == tuple(sorted(rule.keys())) for rule in mapping["stop_condition_rules"])
    assert all(rule["status"] == "active" for rule in mapping["stop_condition_rules"])
    assert tuple(check["check_id"] for check in mapping["operator_review_checklist"]) == EXPECTED_CHECK_IDS
    for check in mapping["operator_review_checklist"]:
        assert tuple(check.keys()) == tuple(sorted(check.keys()))
        assert check["status"] == OPERATOR_REVIEW_STATUS


def test_source_artifacts_reference_only_allowed_existing_local_review_material() -> None:
    mapping = _load_mapping()

    assert tuple(artifact["artifact_id"] for artifact in mapping["source_artifacts"]) == EXPECTED_SOURCE_ARTIFACT_IDS
    for artifact in mapping["source_artifacts"]:
        assert tuple(artifact.keys()) == tuple(sorted(artifact.keys()))
        assert set(artifact) == {
            "artifact_id",
            "contract_version",
            "local_reference",
            "required_state",
        }
        assert artifact["required_state"] in {OPERATOR_REVIEW_STATUS, "local_validation_reference"}
        _assert_allowed_existing_local_reference(artifact["local_reference"])


def test_safety_boundaries_are_closed_for_crypto_stop_condition_mapping() -> None:
    mapping = _load_mapping()

    assert mapping["safety_boundaries"] == EXPECTED_SAFETY_BOUNDARIES
    assert mapping["safety_boundaries"]["local_static_samples_only"] is True
    assert mapping["safety_boundaries"]["operator_review_required"] is True
    assert mapping["safety_boundaries"]["paper_mode_only"] is True
    assert all(value is False for key, value in mapping["safety_boundaries"].items() if key.endswith("_allowed"))


def test_validation_commands_are_recorded_for_local_crypto_mapping_checks() -> None:
    mapping = _load_mapping()

    assert mapping["required_validation_commands"] == [
        "python -m compileall pm_bot tests",
        "pytest pm_bot/tests tests/test_codex_queue_pmbot_templates.py",
    ]


def test_summary_counts_match_crypto_stop_condition_mapping_content() -> None:
    mapping = _load_mapping()
    local_references = {
        *(record["trigger_evidence_reference"] for record in mapping["stop_condition_records"]),
        *(artifact["local_reference"] for artifact in mapping["source_artifacts"]),
    }

    assert mapping["summary_counts"] == {
        "local_references": len(local_references),
        "operator_review_checklist_items": len(mapping["operator_review_checklist"]),
        "required_operator_record_fields": len(mapping["required_operator_record_fields"]),
        "required_validation_commands": len(mapping["required_validation_commands"]),
        "source_artifacts": len(mapping["source_artifacts"]),
        "stop_condition_records": len(mapping["stop_condition_records"]),
        "stop_condition_records_pending_operator_review": sum(
            1 for record in mapping["stop_condition_records"] if record["operator_review_status"] == OPERATOR_REVIEW_STATUS
        ),
        "stop_condition_rules": len(mapping["stop_condition_rules"]),
        "warnings": len(mapping["warnings"]),
    }


def test_fixture_has_no_decision_scoring_or_selection_terms() -> None:
    mapping = _load_mapping()

    assert _find_disallowed_terms(mapping) == []


def test_documentation_registers_crypto_stop_condition_fixture_and_safety_boundary() -> None:
    document = DOC_PATH.read_text(encoding="utf-8")

    assert f"Task: `{TASK_ID}`" in document
    assert f"Mapping: `{MAPPING_ID}`" in document
    assert f"Contract: `{CONTRACT_VERSION}`" in document
    assert f"Run mode: `{RUN_MODE}`" in document
    assert str(FIXTURE_PATH).replace("\\", "/") in document
    assert "No forecast scoring, action guidance, market ranking" in document
    assert "This mapping is not execution approval and is not runtime input." in document


def _load_mapping() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


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
            if key == "local_reference" or key == "trigger_evidence_reference":
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
