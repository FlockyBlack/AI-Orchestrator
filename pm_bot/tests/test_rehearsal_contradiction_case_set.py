from __future__ import annotations

import json
from pathlib import Path


DOC_PATH = Path("docs/PMBOT_REHEARSAL_007_REHEARSAL_CONTRADICTION_CASE_SET_LOCAL_ONLY.md")
FIXTURE_PATH = Path("pm_bot/tests/fixtures/rehearsal/pmbot_rehearsal_contradiction_case_set.valid.json")
SOURCE_CONTRADICTION_PATH = Path("pm_bot/source_quality/samples/source_contradiction_ledger.fixture.json")

TASK_ID = "PMBOT-REHEARSAL-007-REHEARSAL-CONTRADICTION-CASE-SET-LOCAL-ONLY"
CONTRACT_ID = "pmbot-rehearsal-contradiction-case-set"
CONTRACT_VERSION = "pmbot_rehearsal_contradiction_case_set.v1"
CASE_SET_ID = "pmbot-rehearsal-contradiction-case-set-001"
RUN_MODE = "local_static_rehearsal_contradiction_case_set"
OPERATOR_REVIEW_STATUS = "pending_operator_review"
ALLOWED_LOCAL_PREFIXES = ("docs/", "pm_bot/readiness/", "pm_bot/source_quality/", "pm_bot/tests/", "tests/")

EXPECTED_CASE_RECORD_FIELDS = (
    "case_id",
    "case_label",
    "case_record_state",
    "case_source",
    "comparison_role",
    "expected_review_class",
    "left_field",
    "left_field_present",
    "left_source_id",
    "left_static_value",
    "linked_source_contradiction_row_id",
    "local_evidence_reference",
    "operator_review_status",
    "right_field",
    "right_field_present",
    "right_source_id",
    "right_static_value",
    "semantic_field",
    "subject_keys_match",
    "values_match",
)
EXPECTED_CASE_IDS = (
    "pmbot-rehearsal-contradiction-case-set-001.case.weather_static_value_difference",
    "pmbot-rehearsal-contradiction-case-set-001.case.subject_key_station_id_match",
    "pmbot-rehearsal-contradiction-case-set-001.case.subject_key_observation_date_match",
    "pmbot-rehearsal-contradiction-case-set-001.case.subject_key_difference_boundary",
    "pmbot-rehearsal-contradiction-case-set-001.case.field_unavailable_boundary",
    "pmbot-rehearsal-contradiction-case-set-001.case.matching_static_value_boundary",
)
EXPECTED_REVIEW_CLASSES = (
    "static_value_difference_pending_review",
    "no_static_difference_recorded",
    "no_static_difference_recorded",
    "subject_key_difference_pending_review",
    "field_unavailable_pending_review",
    "no_static_difference_recorded",
)
EXPECTED_CHECK_IDS = (
    "case_set_identity_review",
    "case_row_review",
    "source_contradiction_link_review",
    "static_value_boundary_review",
    "subject_key_boundary_review",
    "field_availability_review",
    "sensitive_path_exclusion_check",
    "endpoint_boundary_check",
    "runtime_boundary_check",
    "validation_command_review",
)
EXPECTED_RULE_IDS = (
    "local_static_cases_only",
    "source_contradiction_link_required",
    "operator_review_status_preserved",
    "descriptive_source_review_only",
    "field_presence_boundary_recorded",
    "closed_endpoint_boundary",
    "closed_process_boundary",
)
EXPECTED_SECTION_IDS = (
    "case_set_identity_review",
    "prior_rehearsal_source_review",
    "source_contradiction_ledger_review",
    "contradiction_case_review",
    "safety_boundary_review",
    "validation_review",
)
EXPECTED_SOURCE_ARTIFACT_IDS = (
    "rehearsal_003_source_evidence_bundle_doc",
    "rehearsal_003_source_evidence_bundle_fixture",
    "rehearsal_006_staleness_case_set_doc",
    "rehearsal_006_staleness_case_set_fixture",
    "source_staleness_check_spec_doc",
    "source_staleness_check_spec_fixture",
    "source_contradiction_ledger_doc",
    "source_contradiction_ledger_fixture",
    "source_contradiction_ledger_report",
    "rehearsal_007_contradiction_case_set_doc",
    "rehearsal_007_contradiction_case_set_fixture",
    "rehearsal_007_contradiction_case_set_test",
    "pmbot_queue_template_validation",
)
EXPECTED_SAFETY_BOUNDARIES = {
    "authenticated_endpoint_calls_allowed": False,
    "background_process_allowed": False,
    "browser_automation_allowed": False,
    "case_automation_allowed": False,
    "credential_or_secret_access_allowed": False,
    "descriptive_rehearsal_contradiction_case_set_only": True,
    "execution_endpoint_calls_allowed": False,
    "external_service_calls_allowed": False,
    "live_data_refresh_allowed": False,
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


def test_static_rehearsal_contradiction_case_set_fixture_has_expected_contract() -> None:
    case_set = _load_case_set()

    assert tuple(case_set.keys()) == tuple(sorted(case_set.keys()))
    assert case_set["task_id"] == TASK_ID
    assert case_set["contract_id"] == CONTRACT_ID
    assert case_set["contract_version"] == CONTRACT_VERSION
    assert case_set["case_set_id"] == CASE_SET_ID
    assert case_set["run_mode"] == RUN_MODE
    assert case_set["created_at"] == "2026-05-09T05:15:00Z"
    assert case_set["local_only"] is True
    assert case_set["operator_review_required"] is True
    assert case_set["operator_review"] == {
        "reviewed_at": None,
        "reviewed_by": None,
        "status": OPERATOR_REVIEW_STATUS,
    }
    assert case_set["errors"] == []
    assert case_set["warnings"] == []


def test_case_records_are_fixed_local_pending_and_classified() -> None:
    case_set = _load_case_set()

    assert tuple(case_set["case_record_fields"]) == EXPECTED_CASE_RECORD_FIELDS
    assert tuple(row["case_id"] for row in case_set["case_records"]) == EXPECTED_CASE_IDS
    assert tuple(row["expected_review_class"] for row in case_set["case_records"]) == EXPECTED_REVIEW_CLASSES

    for row in case_set["case_records"]:
        assert tuple(row.keys()) == EXPECTED_CASE_RECORD_FIELDS
        assert row["case_record_state"] == "contradiction_case_pending_operator_review"
        assert row["case_source"] in {"source_contradiction_ledger_row", "static_boundary_case"}
        assert row["comparison_role"] in {"field_value", "subject_key"}
        assert row["operator_review_status"] == OPERATOR_REVIEW_STATUS
        assert row["expected_review_class"] == _expected_review_class(row)
        _assert_allowed_existing_local_reference(row["local_evidence_reference"])


def test_case_records_link_to_existing_local_source_contradiction_rows() -> None:
    case_set = _load_case_set()
    source_contradiction = _load_json(SOURCE_CONTRADICTION_PATH)
    rows_by_id = {row["row_id"]: row for row in source_contradiction["source_contradiction_rows"]}

    for row in case_set["case_records"]:
        linked_row = rows_by_id[row["linked_source_contradiction_row_id"]]
        assert row["left_source_id"] == linked_row["left_source"]["source_id"]
        assert row["right_source_id"] == linked_row["right_source"]["source_id"]
        assert row["local_evidence_reference"] == str(SOURCE_CONTRADICTION_PATH).replace("\\", "/")

    copied_value_case = case_set["case_records"][0]
    linked_row = rows_by_id[copied_value_case["linked_source_contradiction_row_id"]]
    comparison = linked_row["field_comparisons"][0]
    assert copied_value_case["left_static_value"] == comparison["left_value"]
    assert copied_value_case["right_static_value"] == comparison["right_value"]
    assert copied_value_case["values_match"] is comparison["values_match"]


def test_review_sections_checks_rules_and_validation_commands_are_fixed() -> None:
    case_set = _load_case_set()

    assert tuple(rule["rule_id"] for rule in case_set["case_set_rules"]) == EXPECTED_RULE_IDS
    assert all(tuple(rule.keys()) == ("rule_id", "rule_text", "status") for rule in case_set["case_set_rules"])
    assert all(rule["status"] == "active" for rule in case_set["case_set_rules"])
    assert tuple(check["check_id"] for check in case_set["operator_review_checklist"]) == EXPECTED_CHECK_IDS
    assert all(check["status"] == OPERATOR_REVIEW_STATUS for check in case_set["operator_review_checklist"])
    assert tuple(section["section_id"] for section in case_set["review_sections"]) == EXPECTED_SECTION_IDS
    for section in case_set["review_sections"]:
        assert tuple(section.keys()) == tuple(sorted(section.keys()))
        assert section["operator_review_status"] == OPERATOR_REVIEW_STATUS
        for local_reference in section["local_references"]:
            _assert_allowed_existing_local_reference(local_reference)
    assert case_set["required_validation_commands"] == [
        "python -m compileall pm_bot tests",
        "pytest pm_bot/tests tests/test_codex_queue_pmbot_templates.py",
    ]


def test_source_artifacts_reference_only_allowed_existing_local_review_material() -> None:
    case_set = _load_case_set()

    assert tuple(artifact["artifact_id"] for artifact in case_set["source_artifacts"]) == EXPECTED_SOURCE_ARTIFACT_IDS
    for artifact in case_set["source_artifacts"]:
        assert tuple(artifact.keys()) == tuple(sorted(artifact.keys()))
        assert set(artifact) == {
            "artifact_id",
            "contract_version",
            "local_reference",
            "required_state",
        }
        assert artifact["required_state"] in {
            OPERATOR_REVIEW_STATUS,
            "local_validation_reference",
        }
        _assert_allowed_existing_local_reference(artifact["local_reference"])


def test_safety_boundaries_are_closed_for_rehearsal_contradiction_case_set() -> None:
    case_set = _load_case_set()

    assert case_set["safety_boundaries"] == EXPECTED_SAFETY_BOUNDARIES
    assert case_set["safety_boundaries"]["local_static_samples_only"] is True
    assert case_set["safety_boundaries"]["operator_review_required"] is True
    assert case_set["safety_boundaries"]["paper_mode_only"] is True
    assert all(value is False for key, value in case_set["safety_boundaries"].items() if key.endswith("_allowed"))


def test_summary_counts_match_rehearsal_contradiction_case_set_content() -> None:
    case_set = _load_case_set()
    local_references = {
        *(row["local_evidence_reference"] for row in case_set["case_records"]),
        *(artifact["local_reference"] for artifact in case_set["source_artifacts"]),
        *(reference for section in case_set["review_sections"] for reference in section["local_references"]),
    }
    linked_row_ids = {row["linked_source_contradiction_row_id"] for row in case_set["case_records"]}
    review_classes = {row["expected_review_class"] for row in case_set["case_records"]}

    assert case_set["summary_counts"] == {
        "case_record_fields": len(case_set["case_record_fields"]),
        "case_records": len(case_set["case_records"]),
        "case_records_pending_operator_review": sum(
            1 for row in case_set["case_records"] if row["operator_review_status"] == OPERATOR_REVIEW_STATUS
        ),
        "case_set_rules": len(case_set["case_set_rules"]),
        "contradiction_review_classes": len(review_classes),
        "field_unavailable_cases": sum(
            1
            for row in case_set["case_records"]
            if not row["left_field_present"] or not row["right_field_present"]
        ),
        "linked_source_contradiction_row_ids": len(linked_row_ids),
        "local_references": len(local_references),
        "operator_review_checklist_items": len(case_set["operator_review_checklist"]),
        "required_validation_commands": len(case_set["required_validation_commands"]),
        "review_sections": len(case_set["review_sections"]),
        "source_artifacts": len(case_set["source_artifacts"]),
        "static_value_difference_cases": sum(
            1
            for row in case_set["case_records"]
            if row["comparison_role"] == "field_value"
            and row["left_field_present"]
            and row["right_field_present"]
            and not row["values_match"]
        ),
        "subject_key_difference_cases": sum(
            1
            for row in case_set["case_records"]
            if row["comparison_role"] == "subject_key" and not row["values_match"]
        ),
        "warnings": len(case_set["warnings"]),
    }


def test_fixture_has_no_decision_scoring_or_selection_terms() -> None:
    case_set = _load_case_set()

    assert _find_disallowed_terms(case_set) == []


def test_documentation_registers_rehearsal_contradiction_case_set_and_safety_boundary() -> None:
    document = DOC_PATH.read_text(encoding="utf-8")

    assert f"Task: `{TASK_ID}`" in document
    assert f"Case set: `{CASE_SET_ID}`" in document
    assert f"Contract: `{CONTRACT_VERSION}`" in document
    assert f"Run mode: `{RUN_MODE}`" in document
    assert str(FIXTURE_PATH).replace("\\", "/") in document
    assert "pm_bot/source_quality/samples/source_contradiction_ledger.fixture.json" in document
    assert "static value difference" in document
    assert "subject key difference" in document
    assert "field unavailable" in document
    assert "No market recommendation, forecast scoring, action guidance, or selection advice." in document
    assert "No probability, EV, edge, or confidence scoring." in document
    assert "This case set is not execution approval and is not runtime input." in document


def _load_case_set() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _expected_review_class(row: dict) -> str:
    if not row["left_field_present"] or not row["right_field_present"]:
        return "field_unavailable_pending_review"
    if row["comparison_role"] == "subject_key" and not row["values_match"]:
        return "subject_key_difference_pending_review"
    if not row["subject_keys_match"]:
        return "subject_key_difference_pending_review"
    if not row["values_match"]:
        return "static_value_difference_pending_review"
    return "no_static_difference_recorded"


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
                "local_evidence_reference",
                "local_reference",
                "local_references",
                "required_validation_commands",
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
