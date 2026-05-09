from __future__ import annotations

import json
from pathlib import Path


DOC_PATH = Path("docs/PMBOT_REHEARSAL_002_REHEARSAL_MARKET_PACKET_SCHEMA_LOCAL_ONLY.md")
FIXTURE_PATH = Path("pm_bot/tests/fixtures/rehearsal/pmbot_rehearsal_market_packet_schema.valid.json")
TASK_ID = "PMBOT-REHEARSAL-002-REHEARSAL-MARKET-PACKET-SCHEMA-LOCAL-ONLY"
SCHEMA_ID = "pmbot-rehearsal-market-packet-schema"
CONTRACT_VERSION = "pmbot_rehearsal_market_packet_schema.v1"
RUN_MODE = "local_static_rehearsal_market_packet_schema"
OPERATOR_REVIEW_STATUS = "pending_operator_review"
ALLOWED_LOCAL_PREFIXES = ("docs/", "pm_bot/readiness/", "pm_bot/tests/", "tests/")

EXPECTED_MARKET_PACKET_FIELDS = (
    "category_label",
    "close_time_utc",
    "currency_label",
    "description",
    "excluded_fields",
    "local_scenario_contract_reference",
    "market_packet_id",
    "market_packet_state",
    "market_title",
    "operator_review_status",
    "outcome_label_policy",
    "outcome_labels",
    "packet_kind",
    "rehearsal_phase",
    "source_reference_policy",
    "static_source_references",
    "venue_label",
)
EXPECTED_CHECK_IDS = (
    "local_reference_review",
    "schema_field_review",
    "static_sample_review",
    "operator_review_status_review",
    "value_boundary_review",
    "sensitive_path_exclusion_check",
    "runtime_boundary_check",
    "output_boundary_check",
    "validation_replay_check",
)
EXPECTED_SECTION_IDS = (
    "schema_identity_review",
    "scenario_contract_link_review",
    "read_only_source_context_review",
    "operator_gate_boundary_review",
    "validation_review",
)
EXPECTED_SOURCE_ARTIFACT_IDS = (
    "rehearsal_market_packet_schema_doc",
    "rehearsal_market_packet_schema_fixture",
    "rehearsal_market_packet_schema_test",
    "rehearsal_scenario_contract_doc",
    "rehearsal_scenario_contract_fixture",
    "supervised_live_read_only_live_data_contract",
    "supervised_live_data_source_inventory",
    "supervised_live_operator_gate_record",
    "read_only_live_data_contract_fixture",
    "live_data_source_inventory_fixture",
    "operator_approval_gate_record_fixture",
    "pmbot_template_validation",
)
EXPECTED_SAFETY_BOUNDARIES = {
    "authenticated_endpoint_calls_allowed": False,
    "background_process_allowed": False,
    "browser_automation_allowed": False,
    "credential_or_secret_access_allowed": False,
    "descriptive_market_packet_only": True,
    "execution_endpoint_calls_allowed": False,
    "external_service_calls_allowed": False,
    "llm_provider_calls_allowed": False,
    "local_static_samples_only": True,
    "market_api_calls_allowed": False,
    "market_ranking_allowed": False,
    "network_calls_allowed": False,
    "numeric_prediction_metric_allowed": False,
    "openrouter_calls_allowed": False,
    "operator_review_required": True,
    "order_or_trade_surface_changes_allowed": False,
    "paper_mode_only": True,
    "polymarket_api_calls_allowed": False,
    "resident_process_allowed": False,
    "run_codex_changes_allowed": False,
    "runtime_or_dispatcher_changes_allowed": False,
    "scheduler_or_worker_allowed": False,
    "trading_endpoint_calls_allowed": False,
    "transaction_endpoint_calls_allowed": False,
    "wallet_or_signing_material_access_allowed": False,
}


def test_static_rehearsal_market_packet_schema_fixture_has_expected_contract() -> None:
    schema = _load_schema()

    assert tuple(schema.keys()) == tuple(sorted(schema.keys()))
    assert schema["task_id"] == TASK_ID
    assert schema["schema_id"] == SCHEMA_ID
    assert schema["contract_version"] == CONTRACT_VERSION
    assert schema["run_mode"] == RUN_MODE
    assert schema["created_at"] == "2026-05-09T02:10:00Z"
    assert schema["local_only"] is True
    assert schema["operator_review_required"] is True
    assert schema["operator_review"]["status"] == OPERATOR_REVIEW_STATUS
    assert schema["operator_review"]["reviewed_at"] is None
    assert schema["operator_review"]["reviewed_by"] is None
    assert schema["errors"] == []
    assert schema["warnings"] == []


def test_market_packet_fields_and_catalog_are_fixed_descriptive_and_pending_review() -> None:
    schema = _load_schema()

    assert tuple(schema["market_packet_fields"]) == EXPECTED_MARKET_PACKET_FIELDS
    assert tuple(record["field_name"] for record in schema["field_catalog"]) == EXPECTED_MARKET_PACKET_FIELDS
    assert len(schema["field_catalog"]) == len(EXPECTED_MARKET_PACKET_FIELDS)
    for record in schema["field_catalog"]:
        assert tuple(record.keys()) == tuple(sorted(record.keys()))
        assert set(record) == {
            "field_name",
            "field_role",
            "operator_review_status",
            "permitted_value_shape",
            "required",
        }
        assert record["operator_review_status"] == OPERATOR_REVIEW_STATUS
        assert record["required"] is True


def test_market_packet_record_is_static_local_and_pending_review() -> None:
    schema = _load_schema()

    assert len(schema["market_packet_records"]) == 1
    record = schema["market_packet_records"][0]

    assert tuple(record.keys()) == EXPECTED_MARKET_PACKET_FIELDS
    assert record["market_packet_id"] == "rehearsal_market_packet_schema_001.static_local_packet_shape"
    assert record["market_packet_state"] == "schema_only_static_sample_pending_operator_review"
    assert record["operator_review_status"] == OPERATOR_REVIEW_STATUS
    assert record["source_reference_policy"] == "local_static_reference_list_only"
    assert record["outcome_label_policy"] == "labels_only_no_numeric_metrics"
    assert record["outcome_labels"] == ["option_label_a", "option_label_b"]
    assert record["excluded_fields"] == [
        "credential_reference",
        "endpoint_payload",
        "execution_payload",
        "market_ranking",
        "numeric_prediction_metric",
        "order_payload",
        "runtime_dispatch_reference",
        "trade_instruction",
        "wallet_reference",
    ]
    _assert_allowed_existing_local_reference(record["local_scenario_contract_reference"])
    for local_reference in record["static_source_references"]:
        _assert_allowed_existing_local_reference(local_reference)


def test_review_sections_and_source_artifacts_reference_existing_local_files() -> None:
    schema = _load_schema()

    assert tuple(section["section_id"] for section in schema["review_sections"]) == EXPECTED_SECTION_IDS
    for section in schema["review_sections"]:
        assert tuple(section.keys()) == tuple(sorted(section.keys()))
        assert set(section) == {
            "local_references",
            "operator_review_status",
            "section_id",
            "section_label",
            "section_role",
        }
        assert section["operator_review_status"] == OPERATOR_REVIEW_STATUS
        for local_reference in section["local_references"]:
            _assert_allowed_existing_local_reference(local_reference)

    assert tuple(record["artifact_id"] for record in schema["source_artifacts"]) == EXPECTED_SOURCE_ARTIFACT_IDS
    for record in schema["source_artifacts"]:
        assert tuple(record.keys()) == tuple(sorted(record.keys()))
        assert set(record) == {
            "artifact_id",
            "artifact_type",
            "contract_version",
            "local_reference",
            "operator_review_status",
            "required_state",
            "source_role",
        }
        assert record["operator_review_status"] == OPERATOR_REVIEW_STATUS
        _assert_allowed_existing_local_reference(record["local_reference"])


def test_operator_checks_schema_rules_and_validation_commands_remain_pending_or_active() -> None:
    schema = _load_schema()

    assert tuple(check["check_id"] for check in schema["operator_review_checklist"]) == EXPECTED_CHECK_IDS
    assert all(check["status"] == OPERATOR_REVIEW_STATUS for check in schema["operator_review_checklist"])
    assert [rule["status"] for rule in schema["schema_rules"]] == ["active"] * 6
    assert [rule["rule_id"] for rule in schema["schema_rules"]] == [
        "local_static_inputs_only",
        "descriptive_packet_fields_only",
        "operator_review_status_preserved",
        "numeric_metric_boundary",
        "closed_endpoint_boundary",
        "closed_process_boundary",
    ]
    assert schema["required_validation_commands"] == [
        "python -m compileall pm_bot tests",
        "pytest pm_bot/tests tests/test_codex_queue_pmbot_templates.py",
    ]


def test_safety_boundaries_are_closed_for_rehearsal_market_packet_schema() -> None:
    schema = _load_schema()

    assert schema["safety_boundaries"] == EXPECTED_SAFETY_BOUNDARIES
    assert schema["safety_boundaries"]["local_static_samples_only"] is True
    assert schema["safety_boundaries"]["operator_review_required"] is True
    assert schema["safety_boundaries"]["paper_mode_only"] is True
    assert all(value is False for key, value in schema["safety_boundaries"].items() if key.endswith("_allowed"))


def test_summary_counts_match_rehearsal_market_packet_schema_content() -> None:
    schema = _load_schema()
    local_references = {
        *(reference for section in schema["review_sections"] for reference in section["local_references"]),
        *(record["local_reference"] for record in schema["source_artifacts"]),
        schema["market_packet_records"][0]["local_scenario_contract_reference"],
        *schema["market_packet_records"][0]["static_source_references"],
    }

    assert schema["summary_counts"] == {
        "field_catalog_items": len(schema["field_catalog"]),
        "local_references": len(local_references),
        "market_packet_records": len(schema["market_packet_records"]),
        "operator_review_checklist_items": len(schema["operator_review_checklist"]),
        "required_validation_commands": len(schema["required_validation_commands"]),
        "review_sections": len(schema["review_sections"]),
        "schema_rules": len(schema["schema_rules"]),
        "source_artifacts": len(schema["source_artifacts"]),
        "warnings": len(schema["warnings"]),
    }


def test_fixture_has_no_decision_scoring_or_selection_terms() -> None:
    schema = _load_schema()

    assert _find_disallowed_terms(schema) == []


def test_documentation_registers_rehearsal_market_packet_schema_fixture_and_safety_boundary() -> None:
    document = DOC_PATH.read_text(encoding="utf-8")

    assert f"Task: `{TASK_ID}`" in document
    assert f"Schema: `{CONTRACT_VERSION}`" in document
    assert f"Run mode: `{RUN_MODE}`" in document
    assert "descriptive PMBOT rehearsal market packets" in document
    assert str(FIXTURE_PATH).replace("\\", "/") in document
    assert "No market recommendation, forecast scoring, action guidance, or selection advice." in document
    assert "No probability, EV, edge, or confidence scoring." in document
    assert "This schema is not execution approval and is not runtime input." in document


def _load_schema() -> dict:
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
            if key in {
                "local_reference",
                "local_references",
                "local_scenario_contract_reference",
                "static_source_references",
            }:
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
