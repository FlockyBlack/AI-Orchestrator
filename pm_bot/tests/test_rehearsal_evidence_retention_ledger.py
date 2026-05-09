from __future__ import annotations

import json
from pathlib import Path


DOC_PATH = Path("docs/PMBOT_REHEARSAL_008_REHEARSAL_EVIDENCE_RETENTION_LEDGER_LOCAL_ONLY.md")
FIXTURE_PATH = Path("pm_bot/tests/fixtures/rehearsal/pmbot_rehearsal_evidence_retention_ledger.valid.json")

TASK_ID = "PMBOT-REHEARSAL-008-REHEARSAL-EVIDENCE-RETENTION-LEDGER-LOCAL-ONLY"
CONTRACT_ID = "pmbot-rehearsal-evidence-retention-ledger"
CONTRACT_VERSION = "pmbot_rehearsal_evidence_retention_ledger.v1"
LEDGER_ID = "pmbot-rehearsal-evidence-retention-ledger-001"
RUN_MODE = "local_static_rehearsal_evidence_retention_ledger"
OPERATOR_REVIEW_STATUS = "pending_operator_review"
ALLOWED_LOCAL_PREFIXES = ("docs/", "pm_bot/readiness/", "pm_bot/source_quality/", "pm_bot/tests/", "tests/")

EXPECTED_RETENTION_RECORD_FIELDS = (
    "evidence_record_id",
    "evidence_record_state",
    "local_references",
    "operator_review_status",
    "publication_boundary",
    "required_prior_state",
    "retention_class",
    "retention_reason",
    "retention_record_id",
    "retention_status",
)
EXPECTED_EVIDENCE_RECORD_IDS = (
    "rehearsal_001_scenario_contract_review_record",
    "rehearsal_002_market_packet_schema_review_record",
    "rehearsal_003_source_evidence_bundle_review_record",
    "rehearsal_004_operator_approval_record_review_record",
    "rehearsal_005_stop_condition_matrix_review_record",
    "rehearsal_006_staleness_case_set_review_record",
    "rehearsal_007_contradiction_case_set_review_record",
    "local_validation_and_safety_review_record",
)
EXPECTED_CHECK_IDS = (
    "ledger_identity_review",
    "local_reference_review",
    "retention_record_review",
    "prior_review_state_review",
    "retention_status_review",
    "safety_boundary_review",
    "endpoint_boundary_check",
    "runtime_boundary_check",
    "validation_command_review",
)
EXPECTED_RULE_IDS = (
    "local_static_inputs_only",
    "descriptive_retention_only",
    "local_reference_required",
    "operator_review_status_preserved",
    "no_automatic_cleanup",
    "closed_endpoint_boundary",
    "closed_process_boundary",
)
EXPECTED_SECTION_IDS = (
    "ledger_identity_review",
    "prior_rehearsal_control_records_review",
    "rehearsal_case_records_review",
    "validation_and_safety_review",
    "retention_policy_review",
)
EXPECTED_LOCAL_REFERENCES = (
    "docs/PMBOT_REHEARSAL_001_READ_ONLY_REHEARSAL_SCENARIO_CONTRACT_LOCAL_ONLY.md",
    "docs/PMBOT_REHEARSAL_002_REHEARSAL_MARKET_PACKET_SCHEMA_LOCAL_ONLY.md",
    "docs/PMBOT_REHEARSAL_003_REHEARSAL_SOURCE_EVIDENCE_BUNDLE_LOCAL_ONLY.md",
    "docs/PMBOT_REHEARSAL_004_REHEARSAL_OPERATOR_APPROVAL_RECORD_LOCAL_ONLY.md",
    "docs/PMBOT_REHEARSAL_005_REHEARSAL_STOP_CONDITION_TRIGGER_MATRIX_LOCAL_ONLY.md",
    "docs/PMBOT_REHEARSAL_006_REHEARSAL_STALENESS_CASE_SET_LOCAL_ONLY.md",
    "docs/PMBOT_REHEARSAL_007_REHEARSAL_CONTRADICTION_CASE_SET_LOCAL_ONLY.md",
    "docs/PMBOT_REHEARSAL_008_REHEARSAL_EVIDENCE_RETENTION_LEDGER_LOCAL_ONLY.md",
    "docs/PMBOT_SAFETY_003_FORBIDDEN_ACTION_SCAN_LOCAL_ONLY.md",
    "docs/PMBOT_SAFETY_005_FORBIDDEN_LANGUAGE_REGRESSION_SUITE_LOCAL_ONLY.md",
    "pm_bot/tests/fixtures/rehearsal/pmbot_read_only_rehearsal_scenario_contract.valid.json",
    "pm_bot/tests/fixtures/rehearsal/pmbot_rehearsal_contradiction_case_set.valid.json",
    "pm_bot/tests/fixtures/rehearsal/pmbot_rehearsal_evidence_retention_ledger.valid.json",
    "pm_bot/tests/fixtures/rehearsal/pmbot_rehearsal_market_packet_schema.valid.json",
    "pm_bot/tests/fixtures/rehearsal/pmbot_rehearsal_operator_approval_record.valid.json",
    "pm_bot/tests/fixtures/rehearsal/pmbot_rehearsal_source_evidence_bundle.valid.json",
    "pm_bot/tests/fixtures/rehearsal/pmbot_rehearsal_staleness_case_set.valid.json",
    "pm_bot/tests/fixtures/rehearsal/pmbot_rehearsal_stop_condition_trigger_matrix.valid.json",
    "pm_bot/tests/test_read_only_rehearsal_scenario_contract.py",
    "pm_bot/tests/test_rehearsal_contradiction_case_set.py",
    "pm_bot/tests/test_rehearsal_evidence_retention_ledger.py",
    "pm_bot/tests/test_rehearsal_market_packet_schema.py",
    "pm_bot/tests/test_rehearsal_operator_approval_record.py",
    "pm_bot/tests/test_rehearsal_source_evidence_bundle.py",
    "pm_bot/tests/test_rehearsal_staleness_case_set.py",
    "pm_bot/tests/test_rehearsal_stop_condition_trigger_matrix.py",
    "tests/test_codex_queue_pmbot_templates.py",
)
EXPECTED_SAFETY_BOUNDARIES = {
    "authenticated_endpoint_calls_allowed": False,
    "background_process_allowed": False,
    "browser_automation_allowed": False,
    "credential_or_secret_access_allowed": False,
    "descriptive_rehearsal_evidence_retention_ledger_only": True,
    "destructive_cleanup_allowed": False,
    "execution_endpoint_calls_allowed": False,
    "external_service_calls_allowed": False,
    "file_deletion_allowed": False,
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
    "retention_automation_allowed": False,
    "run_codex_changes_allowed": False,
    "runtime_or_dispatcher_changes_allowed": False,
    "scheduler_or_worker_allowed": False,
    "trading_endpoint_calls_allowed": False,
    "transaction_endpoint_calls_allowed": False,
    "wallet_or_signing_material_access_allowed": False,
}


def test_static_rehearsal_evidence_retention_ledger_fixture_has_expected_contract() -> None:
    ledger = _load_ledger()

    assert tuple(ledger.keys()) == tuple(sorted(ledger.keys()))
    assert ledger["task_id"] == TASK_ID
    assert ledger["contract_id"] == CONTRACT_ID
    assert ledger["contract_version"] == CONTRACT_VERSION
    assert ledger["ledger_id"] == LEDGER_ID
    assert ledger["run_mode"] == RUN_MODE
    assert ledger["created_at"] == "2026-05-09T05:45:00Z"
    assert ledger["local_only"] is True
    assert ledger["operator_review_required"] is True
    assert ledger["operator_review"] == {
        "reviewed_at": None,
        "reviewed_by": None,
        "status": OPERATOR_REVIEW_STATUS,
    }
    assert ledger["errors"] == []
    assert ledger["warnings"] == []


def test_retention_records_are_fixed_local_pending_and_retained() -> None:
    ledger = _load_ledger()

    assert tuple(ledger["retention_record_fields"]) == EXPECTED_RETENTION_RECORD_FIELDS
    assert tuple(row["evidence_record_id"] for row in ledger["retention_records"]) == EXPECTED_EVIDENCE_RECORD_IDS
    for row in ledger["retention_records"]:
        assert tuple(row.keys()) == EXPECTED_RETENTION_RECORD_FIELDS
        assert row["evidence_record_state"] == "local_review_record_present"
        assert row["operator_review_status"] == OPERATOR_REVIEW_STATUS
        assert row["publication_boundary"] == "local_operator_review_only"
        assert row["retention_status"] == "retained_for_operator_review"
        assert row["retention_record_id"].startswith(f"{LEDGER_ID}.record.")
        assert row["required_prior_state"] in {OPERATOR_REVIEW_STATUS, "local_validation_reference"}
        for local_reference in row["local_references"]:
            _assert_allowed_existing_local_reference(local_reference)


def test_prior_rehearsal_fixture_review_states_remain_pending() -> None:
    ledger = _load_ledger()

    fixture_references = sorted(
        {
            reference
            for row in ledger["retention_records"]
            for reference in row["local_references"]
            if reference.startswith("pm_bot/tests/fixtures/rehearsal/")
        }
    )
    assert len(fixture_references) == 7
    for reference in fixture_references:
        fixture = _load_json(Path(reference))
        assert fixture["operator_review"] == {
            "reviewed_at": None,
            "reviewed_by": None,
            "status": OPERATOR_REVIEW_STATUS,
        }


def test_review_sections_checks_rules_and_validation_commands_are_fixed() -> None:
    ledger = _load_ledger()

    assert tuple(rule["rule_id"] for rule in ledger["ledger_rules"]) == EXPECTED_RULE_IDS
    assert all(tuple(rule.keys()) == ("rule_id", "rule_text", "status") for rule in ledger["ledger_rules"])
    assert all(rule["status"] == "active" for rule in ledger["ledger_rules"])
    assert tuple(check["check_id"] for check in ledger["operator_review_checklist"]) == EXPECTED_CHECK_IDS
    assert all(check["status"] == OPERATOR_REVIEW_STATUS for check in ledger["operator_review_checklist"])
    assert tuple(section["section_id"] for section in ledger["review_sections"]) == EXPECTED_SECTION_IDS
    for section in ledger["review_sections"]:
        assert tuple(section.keys()) == tuple(sorted(section.keys()))
        assert section["operator_review_status"] == OPERATOR_REVIEW_STATUS
        for local_reference in section["local_references"]:
            _assert_allowed_existing_local_reference(local_reference)
    assert ledger["required_validation_commands"] == [
        "python -m compileall pm_bot tests",
        "pytest pm_bot/tests tests/test_codex_queue_pmbot_templates.py",
    ]


def test_safety_boundaries_are_closed_for_rehearsal_evidence_retention_ledger() -> None:
    ledger = _load_ledger()

    assert ledger["safety_boundaries"] == EXPECTED_SAFETY_BOUNDARIES
    assert ledger["safety_boundaries"]["local_static_samples_only"] is True
    assert ledger["safety_boundaries"]["operator_review_required"] is True
    assert ledger["safety_boundaries"]["paper_mode_only"] is True
    assert all(value is False for key, value in ledger["safety_boundaries"].items() if key.endswith("_allowed"))


def test_summary_counts_match_rehearsal_evidence_retention_ledger_content() -> None:
    ledger = _load_ledger()
    local_references = {
        *(reference for row in ledger["retention_records"] for reference in row["local_references"]),
        *(reference for section in ledger["review_sections"] for reference in section["local_references"]),
    }

    assert ledger["summary_counts"] == {
        "ledger_rules": len(ledger["ledger_rules"]),
        "local_references": len(local_references),
        "operator_review_checklist_items": len(ledger["operator_review_checklist"]),
        "required_validation_commands": len(ledger["required_validation_commands"]),
        "retention_record_fields": len(ledger["retention_record_fields"]),
        "retention_records": len(ledger["retention_records"]),
        "retention_records_pending_operator_review": sum(
            1 for row in ledger["retention_records"] if row["operator_review_status"] == OPERATOR_REVIEW_STATUS
        ),
        "review_sections": len(ledger["review_sections"]),
        "safety_references": 2,
        "validation_references": 1,
        "warnings": len(ledger["warnings"]),
    }


def test_rehearsal_evidence_retention_ledger_references_only_expected_local_static_paths() -> None:
    ledger = _load_ledger()
    references = sorted(
        {
            *(reference for row in ledger["retention_records"] for reference in row["local_references"]),
            *(reference for section in ledger["review_sections"] for reference in section["local_references"]),
        }
    )

    assert references == sorted(EXPECTED_LOCAL_REFERENCES)
    for reference in references:
        _assert_allowed_existing_local_reference(reference)


def test_fixture_has_no_decision_scoring_or_selection_terms() -> None:
    ledger = _load_ledger()

    assert _find_disallowed_terms(ledger) == []


def test_documentation_registers_rehearsal_evidence_retention_ledger_and_safety_boundary() -> None:
    document = DOC_PATH.read_text(encoding="utf-8")

    assert f"Task: `{TASK_ID}`" in document
    assert f"Ledger: `{LEDGER_ID}`" in document
    assert f"Contract: `{CONTRACT_VERSION}`" in document
    assert f"Run mode: `{RUN_MODE}`" in document
    assert str(FIXTURE_PATH).replace("\\", "/") in document
    assert "retained for local operator review" in document
    assert "No market recommendation, forecast scoring, action guidance, or selection advice." in document
    assert "No probability, EV, edge, or confidence scoring." in document
    assert "No destructive cleanup or automated retention process." in document
    assert "This ledger is not execution approval and is not runtime input." in document


def _load_ledger() -> dict:
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
            if key in {
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
