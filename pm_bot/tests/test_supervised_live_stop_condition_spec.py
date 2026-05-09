from __future__ import annotations

import json
from pathlib import Path


DOC_PATH = Path("docs/PMBOT_SUPERVISED_LIVE_004_SUPERVISED_LIVE_STOP_CONDITION_SPEC_LOCAL_ONLY.md")
FIXTURE_PATH = Path("pm_bot/tests/fixtures/readiness/pmbot_supervised_live_stop_condition_spec.valid.json")
TASK_ID = "PMBOT-SUPERVISED-LIVE-004-SUPERVISED-LIVE-STOP-CONDITION-SPEC-LOCAL-ONLY"
CONTRACT_ID = "pmbot-supervised-live-stop-condition-spec"
CONTRACT_VERSION = "pmbot_supervised_live_stop_condition_spec.v1"
RUN_MODE = "local_static_supervised_live_stop_condition_spec"
SPEC_ID = "pmbot-supervised-live-stop-condition-spec-001"
OPERATOR_REVIEW_STATUS = "pending_operator_review"

EXPECTED_CONDITION_FIELDS = (
    "condition_id",
    "condition_label",
    "condition_class",
    "trigger_source",
    "trigger_evidence_reference",
    "operator_review_status",
    "manual_record_required",
    "session_state_after_trigger",
    "excluded_operations",
    "notes",
)
EXPECTED_CONDITION_IDS = (
    "operator_manual_stop_request",
    "local_artifact_boundary_breach",
    "forbidden_operation_request_detected",
    "local_validation_command_failed",
    "source_record_label_dispute",
    "missing_operator_gate_record",
)
EXPECTED_CHECK_IDS = (
    "condition_catalog_review",
    "trigger_evidence_review",
    "manual_record_review",
    "sensitive_path_exclusion_check",
    "runtime_boundary_check",
    "output_boundary_check",
    "validation_replay_check",
)
EXPECTED_RULE_IDS = (
    "manual_stop_precedence",
    "closed_boundary_precedence",
    "local_artifact_evidence_required",
    "validation_failure_stop",
    "no_restart_without_operator_record",
)
EXPECTED_SOURCE_ARTIFACT_IDS = (
    "read_only_live_data_contract",
    "live_data_source_inventory",
    "operator_approval_gate_record",
    "local_to_supervised_live_gap_matrix",
    "forbidden_action_scan",
)
EXPECTED_RECORD_FIELDS = (
    "record_id",
    "condition_id",
    "observed_at_utc",
    "observed_by",
    "local_evidence_reference",
    "prior_session_state",
    "new_session_state",
    "operator_review_status",
    "unresolved_blockers",
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
EXPECTED_SAFETY_BOUNDARIES = {
    "authenticated_endpoint_calls_allowed": False,
    "automated_restart_allowed": False,
    "background_process_allowed": False,
    "browser_automation_allowed": False,
    "condition_trigger_automation_allowed": False,
    "credential_or_secret_access_allowed": False,
    "execution_endpoint_calls_allowed": False,
    "external_service_calls_allowed": False,
    "live_data_refresh_allowed": False,
    "llm_provider_calls_allowed": False,
    "local_static_samples_only": True,
    "market_api_calls_allowed": False,
    "market_ranking_allowed": False,
    "network_calls_allowed": False,
    "numeric_prediction_metric_allowed": False,
    "operator_review_required": True,
    "order_or_trade_surface_changes_allowed": False,
    "paper_mode_only": True,
    "runtime_or_dispatcher_changes_allowed": False,
    "scheduler_or_worker_allowed": False,
    "session_restart_without_operator_record_allowed": False,
    "stop_condition_mutates_runtime_allowed": False,
    "supervised_live_transition_allowed": False,
    "trade_instruction_allowed": False,
    "transaction_endpoint_calls_allowed": False,
    "transition_without_record_allowed": False,
    "wallet_or_signing_material_access_allowed": False,
}
ALLOWED_LOCAL_PREFIXES = ("docs/", "pm_bot/readiness/", "pm_bot/tests/", "tests/")


def test_static_stop_condition_spec_fixture_has_expected_contract() -> None:
    spec = _load_spec()

    assert tuple(spec.keys()) == tuple(sorted(spec.keys()))
    assert spec["task_id"] == TASK_ID
    assert spec["contract_id"] == CONTRACT_ID
    assert spec["contract_version"] == CONTRACT_VERSION
    assert spec["spec_id"] == SPEC_ID
    assert spec["run_mode"] == RUN_MODE
    assert spec["created_at"] == "2026-05-09T00:00:00Z"
    assert spec["local_only"] is True
    assert spec["operator_review_required"] is True
    assert spec["operator_review"]["status"] == OPERATOR_REVIEW_STATUS
    assert spec["operator_review"]["reviewed_at"] is None
    assert spec["operator_review"]["reviewed_by"] is None
    assert spec["errors"] == []
    assert spec["warnings"] == []


def test_stop_condition_records_are_fixed_local_pending_and_manual() -> None:
    spec = _load_spec()

    assert tuple(spec["stop_condition_fields"]) == EXPECTED_CONDITION_FIELDS
    assert tuple(record["condition_id"] for record in spec["stop_condition_records"]) == EXPECTED_CONDITION_IDS

    for record in spec["stop_condition_records"]:
        assert tuple(record.keys()) == tuple(sorted(record.keys()))
        assert set(record) == set(EXPECTED_CONDITION_FIELDS)
        assert record["manual_record_required"] is True
        assert record["operator_review_status"] == OPERATOR_REVIEW_STATUS
        assert record["session_state_after_trigger"] in {
            "blocked_until_gate_record_complete",
            "stopped_pending_artifact_review",
            "stopped_pending_operator_record",
            "stopped_pending_safety_review",
            "stopped_pending_source_review",
            "stopped_pending_validation_review",
        }
        assert "://" not in record["trigger_evidence_reference"]
        assert record["trigger_evidence_reference"].startswith(ALLOWED_LOCAL_PREFIXES)
        assert tuple(record["excluded_operations"]) == EXPECTED_EXCLUDED_OPERATIONS


def test_required_operator_record_fields_and_rules_are_deterministic() -> None:
    spec = _load_spec()

    assert tuple(spec["required_operator_record_fields"]) == EXPECTED_RECORD_FIELDS
    assert tuple(rule["rule_id"] for rule in spec["stop_condition_rules"]) == EXPECTED_RULE_IDS
    assert all(rule["status"] == "active" for rule in spec["stop_condition_rules"])
    assert tuple(check["check_id"] for check in spec["operator_review_checklist"]) == EXPECTED_CHECK_IDS
    assert all(check["status"] == OPERATOR_REVIEW_STATUS for check in spec["operator_review_checklist"])


def test_source_artifacts_reference_only_local_review_material() -> None:
    spec = _load_spec()

    assert tuple(artifact["artifact_id"] for artifact in spec["source_artifacts"]) == EXPECTED_SOURCE_ARTIFACT_IDS
    for artifact in spec["source_artifacts"]:
        assert tuple(artifact.keys()) == tuple(sorted(artifact.keys()))
        assert set(artifact) == {
            "artifact_id",
            "contract_version",
            "local_reference",
            "required_state",
        }
        assert artifact["required_state"] == OPERATOR_REVIEW_STATUS
        assert "://" not in artifact["local_reference"]
        assert artifact["local_reference"].startswith(ALLOWED_LOCAL_PREFIXES)


def test_safety_boundaries_are_closed_for_stop_condition_spec() -> None:
    spec = _load_spec()

    assert spec["safety_boundaries"] == EXPECTED_SAFETY_BOUNDARIES
    assert spec["safety_boundaries"]["local_static_samples_only"] is True
    assert spec["safety_boundaries"]["operator_review_required"] is True
    assert spec["safety_boundaries"]["paper_mode_only"] is True
    assert all(value is False for key, value in spec["safety_boundaries"].items() if key.endswith("_allowed"))


def test_validation_commands_are_recorded_for_operator_run_local_checks() -> None:
    spec = _load_spec()

    assert spec["required_validation_commands"] == [
        "python -m compileall pm_bot tests",
        "pytest pm_bot/tests tests/test_codex_queue_pmbot_templates.py",
    ]


def test_summary_counts_match_stop_condition_spec_content() -> None:
    spec = _load_spec()
    local_references = {
        *(record["trigger_evidence_reference"] for record in spec["stop_condition_records"]),
        *(artifact["local_reference"] for artifact in spec["source_artifacts"]),
    }

    assert spec["summary_counts"] == {
        "local_references": len(local_references),
        "operator_review_checklist_items": len(spec["operator_review_checklist"]),
        "required_operator_record_fields": len(spec["required_operator_record_fields"]),
        "required_validation_commands": len(spec["required_validation_commands"]),
        "source_artifacts": len(spec["source_artifacts"]),
        "stop_condition_records": len(spec["stop_condition_records"]),
        "stop_condition_records_pending_operator_review": sum(
            1 for record in spec["stop_condition_records"] if record["operator_review_status"] == OPERATOR_REVIEW_STATUS
        ),
        "stop_condition_rules": len(spec["stop_condition_rules"]),
        "warnings": len(spec["warnings"]),
    }


def test_fixture_has_no_decision_scoring_or_selection_terms() -> None:
    spec = _load_spec()

    assert _find_disallowed_terms(spec) == []


def test_documentation_registers_stop_condition_fixture_and_safety_boundary() -> None:
    document = DOC_PATH.read_text(encoding="utf-8")

    assert f"Task: `{TASK_ID}`" in document
    assert f"Spec: `{SPEC_ID}`" in document
    assert f"Contract: `{CONTRACT_VERSION}`" in document
    assert f"Run mode: `{RUN_MODE}`" in document
    assert str(FIXTURE_PATH).replace("\\", "/") in document
    assert "No forecast scoring, action guidance, market ranking, numeric prediction metric" in document
    assert "This specification is not execution approval and is not runtime input." in document


def _load_spec() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


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
            if key in {"local_reference", "trigger_evidence_reference"}:
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
