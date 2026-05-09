from __future__ import annotations

import json
from pathlib import Path


DOC_PATH = Path("docs/PMBOT_REHEARSAL_006_REHEARSAL_STALENESS_CASE_SET_LOCAL_ONLY.md")
FIXTURE_PATH = Path("pm_bot/tests/fixtures/rehearsal/pmbot_rehearsal_staleness_case_set.valid.json")
SOURCE_STALENESS_PATH = Path("pm_bot/source_quality/samples/source_staleness_check_spec.fixture.json")

TASK_ID = "PMBOT-REHEARSAL-006-REHEARSAL-STALENESS-CASE-SET-LOCAL-ONLY"
CONTRACT_ID = "pmbot-rehearsal-staleness-case-set"
CONTRACT_VERSION = "pmbot_rehearsal_staleness_case_set.v1"
CASE_SET_ID = "pmbot-rehearsal-staleness-case-set-001"
RUN_MODE = "local_static_rehearsal_staleness_case_set"
OPERATOR_REVIEW_STATUS = "pending_operator_review"
REFERENCE_TIMESTAMP = "2026-05-10T00:30:00Z"
ALLOWED_LOCAL_PREFIXES = ("docs/", "pm_bot/readiness/", "pm_bot/source_quality/", "pm_bot/tests/", "tests/")

EXPECTED_CASE_RECORD_FIELDS = (
    "age_seconds",
    "case_id",
    "case_label",
    "case_record_state",
    "case_source",
    "expected_review_class",
    "linked_source_staleness_check_id",
    "local_evidence_reference",
    "maximum_age_seconds",
    "observed_timestamp_utc",
    "operator_review_status",
    "reference_timestamp_utc",
    "timestamp_field_present",
    "timestamp_required",
)
EXPECTED_CASE_IDS = (
    "pmbot-rehearsal-staleness-case-set-001.case.within_window_station_observation",
    "pmbot-rehearsal-staleness-case-set-001.case.within_window_crypto_reference",
    "pmbot-rehearsal-staleness-case-set-001.case.at_limit_weather_boundary",
    "pmbot-rehearsal-staleness-case-set-001.case.outside_window_weather_boundary",
    "pmbot-rehearsal-staleness-case-set-001.case.missing_required_weather_timestamp",
    "pmbot-rehearsal-staleness-case-set-001.case.timestamp_not_required_source_quality_sample",
)
EXPECTED_REVIEW_CLASSES = (
    "within_static_review_window",
    "within_static_review_window",
    "at_static_review_window_limit",
    "outside_static_review_window",
    "timestamp_required_but_missing",
    "timestamp_not_required_by_rule",
)
EXPECTED_CHECK_IDS = (
    "case_set_identity_review",
    "case_row_review",
    "source_staleness_link_review",
    "timestamp_boundary_review",
    "missing_timestamp_review",
    "sensitive_path_exclusion_check",
    "endpoint_boundary_check",
    "runtime_boundary_check",
    "validation_command_review",
)
EXPECTED_RULE_IDS = (
    "local_static_cases_only",
    "source_staleness_link_required",
    "static_reference_clock_only",
    "operator_review_status_preserved",
    "descriptive_source_review_only",
    "closed_endpoint_boundary",
    "closed_process_boundary",
)
EXPECTED_SECTION_IDS = (
    "case_set_identity_review",
    "prior_rehearsal_source_review",
    "staleness_case_review",
    "safety_boundary_review",
    "validation_review",
)
EXPECTED_SOURCE_ARTIFACT_IDS = (
    "rehearsal_003_source_evidence_bundle_doc",
    "rehearsal_003_source_evidence_bundle_fixture",
    "source_staleness_check_spec_doc",
    "source_staleness_check_spec_fixture",
    "source_staleness_check_spec_report",
    "rehearsal_006_staleness_case_set_doc",
    "rehearsal_006_staleness_case_set_fixture",
    "rehearsal_006_staleness_case_set_test",
    "pmbot_queue_template_validation",
)
EXPECTED_SAFETY_BOUNDARIES = {
    "authenticated_endpoint_calls_allowed": False,
    "background_process_allowed": False,
    "browser_automation_allowed": False,
    "case_automation_allowed": False,
    "credential_or_secret_access_allowed": False,
    "descriptive_rehearsal_staleness_case_set_only": True,
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


def test_static_rehearsal_staleness_case_set_fixture_has_expected_contract() -> None:
    case_set = _load_case_set()

    assert tuple(case_set.keys()) == tuple(sorted(case_set.keys()))
    assert case_set["task_id"] == TASK_ID
    assert case_set["contract_id"] == CONTRACT_ID
    assert case_set["contract_version"] == CONTRACT_VERSION
    assert case_set["case_set_id"] == CASE_SET_ID
    assert case_set["run_mode"] == RUN_MODE
    assert case_set["created_at"] == "2026-05-09T04:40:00Z"
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
        assert row["case_record_state"] == "staleness_case_pending_operator_review"
        assert row["case_source"] in {"source_staleness_spec_row", "static_boundary_case"}
        assert row["operator_review_status"] == OPERATOR_REVIEW_STATUS
        assert row["reference_timestamp_utc"] == REFERENCE_TIMESTAMP
        assert row["expected_review_class"] == _expected_review_class(row)
        _assert_allowed_existing_local_reference(row["local_evidence_reference"])


def test_case_records_link_to_existing_local_source_staleness_checks() -> None:
    case_set = _load_case_set()
    source_spec = _load_json(SOURCE_STALENESS_PATH)
    checks_by_id = {row["check_id"]: row for row in source_spec["source_staleness_checks"]}

    for row in case_set["case_records"]:
        linked_check = checks_by_id[row["linked_source_staleness_check_id"]]
        if row["case_source"] == "source_staleness_spec_row":
            assert row["age_seconds"] == linked_check["age_seconds"]
            assert row["maximum_age_seconds"] == linked_check["maximum_age_seconds"]
            assert row["observed_timestamp_utc"] == linked_check["observed_timestamp_utc"]
            assert row["timestamp_field_present"] == linked_check["timestamp_field_present"]
            assert row["timestamp_required"] == linked_check["timestamp_required"]
            assert row["expected_review_class"] == linked_check["staleness_state"]


def test_review_sections_checks_rules_and_validation_commands_are_fixed() -> None:
    case_set = _load_case_set()

    assert case_set["reference_clock"] == {
        "reference_source": "source_staleness_check_spec_fixture_static_value",
        "reference_timestamp_utc": REFERENCE_TIMESTAMP,
        "system_clock_used": False,
    }
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


def test_safety_boundaries_are_closed_for_rehearsal_staleness_case_set() -> None:
    case_set = _load_case_set()

    assert case_set["safety_boundaries"] == EXPECTED_SAFETY_BOUNDARIES
    assert case_set["safety_boundaries"]["local_static_samples_only"] is True
    assert case_set["safety_boundaries"]["operator_review_required"] is True
    assert case_set["safety_boundaries"]["paper_mode_only"] is True
    assert all(value is False for key, value in case_set["safety_boundaries"].items() if key.endswith("_allowed"))


def test_summary_counts_match_rehearsal_staleness_case_set_content() -> None:
    case_set = _load_case_set()
    local_references = {
        *(row["local_evidence_reference"] for row in case_set["case_records"]),
        *(artifact["local_reference"] for artifact in case_set["source_artifacts"]),
        *(reference for section in case_set["review_sections"] for reference in section["local_references"]),
    }
    linked_check_ids = {row["linked_source_staleness_check_id"] for row in case_set["case_records"]}
    review_classes = {row["expected_review_class"] for row in case_set["case_records"]}

    assert case_set["summary_counts"] == {
        "case_record_fields": len(case_set["case_record_fields"]),
        "case_records": len(case_set["case_records"]),
        "case_set_rules": len(case_set["case_set_rules"]),
        "local_references": len(local_references),
        "operator_review_checklist_items": len(case_set["operator_review_checklist"]),
        "required_validation_commands": len(case_set["required_validation_commands"]),
        "review_sections": len(case_set["review_sections"]),
        "source_artifacts": len(case_set["source_artifacts"]),
        "source_staleness_check_ids": len(linked_check_ids),
        "staleness_review_classes": len(review_classes),
        "warnings": len(case_set["warnings"]),
    }


def test_fixture_has_no_decision_scoring_or_selection_terms() -> None:
    case_set = _load_case_set()

    assert _find_disallowed_terms(case_set) == []


def test_documentation_registers_rehearsal_staleness_case_set_and_safety_boundary() -> None:
    document = DOC_PATH.read_text(encoding="utf-8")

    assert f"Task: `{TASK_ID}`" in document
    assert f"Case set: `{CASE_SET_ID}`" in document
    assert f"Contract: `{CONTRACT_VERSION}`" in document
    assert f"Run mode: `{RUN_MODE}`" in document
    assert str(FIXTURE_PATH).replace("\\", "/") in document
    assert "pm_bot/source_quality/samples/source_staleness_check_spec.fixture.json" in document
    assert "within-window station observation" in document
    assert "missing required timestamp" in document
    assert "No market recommendation, forecast scoring, action guidance, or selection advice." in document
    assert "No probability, EV, edge, or confidence scoring." in document
    assert "This case set is not execution approval and is not runtime input." in document


def _load_case_set() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _expected_review_class(row: dict) -> str:
    if not row["timestamp_required"]:
        return "timestamp_not_required_by_rule"
    if not row["timestamp_field_present"]:
        return "timestamp_required_but_missing"
    if row["age_seconds"] < row["maximum_age_seconds"]:
        return "within_static_review_window"
    if row["age_seconds"] == row["maximum_age_seconds"]:
        return "at_static_review_window_limit"
    return "outside_static_review_window"


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
