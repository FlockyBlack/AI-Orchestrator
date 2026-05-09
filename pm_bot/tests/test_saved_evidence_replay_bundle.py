from __future__ import annotations

import json
from pathlib import Path


DOC_PATH = Path("docs/PMBOT_VALIDATION_001_SAVED_EVIDENCE_REPLAY_BUNDLE_LOCAL_ONLY.md")
FIXTURE_PATH = Path("pm_bot/tests/fixtures/validation/pmbot_saved_evidence_replay_bundle.valid.json")
TASK_ID = "PMBOT-VALIDATION-001-SAVED-EVIDENCE-REPLAY-BUNDLE-LOCAL-ONLY"
CONTRACT_ID = "pmbot-saved-evidence-replay-bundle"
CONTRACT_VERSION = "pmbot_saved_evidence_replay_bundle.v1"
BUNDLE_ID = "pmbot-saved-evidence-replay-bundle-001"
RUN_MODE = "local_static_saved_evidence_replay_bundle"
OPERATOR_REVIEW_STATUS = "pending_operator_review"

EXPECTED_RECORD_FIELDS = (
    "record_id",
    "artifact_id",
    "artifact_role",
    "artifact_type",
    "contract_version",
    "local_reference",
    "operator_review_status",
    "expected_state",
    "replay_note",
)
EXPECTED_RECORD_IDS = (
    "saved_evidence_replay_bundle_001.saved_evidence_replay_bundle_fixture",
    "saved_evidence_replay_bundle_001.saved_evidence_replay_bundle_doc",
    "saved_evidence_replay_bundle_001.supervised_live_readiness_bundle_fixture",
    "saved_evidence_replay_bundle_001.supervised_live_readiness_bundle_doc",
    "saved_evidence_replay_bundle_001.local_to_supervised_live_gap_matrix_fixture",
    "saved_evidence_replay_bundle_001.simulated_decision_replay_summary_sample",
    "saved_evidence_replay_bundle_001.simulated_decision_replay_request_fixture",
    "saved_evidence_replay_bundle_001.simulated_decision_audit_ledger_sample",
    "saved_evidence_replay_bundle_001.simulated_decision_packet_sample",
    "saved_evidence_replay_bundle_001.pmbot_queue_template_validation_test",
)
EXPECTED_SECTION_IDS = (
    "bundle_identity_replay",
    "readiness_evidence_replay",
    "simulated_decision_record_replay",
    "queue_template_validation_replay",
)
EXPECTED_CHECK_IDS = (
    "local_reference_replay",
    "static_artifact_replay",
    "review_state_replay",
    "safety_boundary_replay",
    "output_boundary_replay",
)
EXPECTED_SAFETY_BOUNDARIES = {
    "authenticated_endpoint_calls_allowed": False,
    "background_process_allowed": False,
    "browser_automation_allowed": False,
    "credential_or_secret_access_allowed": False,
    "execution_endpoint_calls_allowed": False,
    "external_service_calls_allowed": False,
    "llm_provider_calls_allowed": False,
    "local_static_artifacts_only": True,
    "market_api_calls_allowed": False,
    "market_instruction_allowed": False,
    "network_calls_allowed": False,
    "numeric_prediction_metric_allowed": False,
    "operator_review_required": True,
    "order_or_trade_surface_changes_allowed": False,
    "paper_mode_only": True,
    "replay_mutates_source_artifacts_allowed": False,
    "runtime_or_dispatcher_changes_allowed": False,
    "scheduler_or_worker_allowed": False,
    "transaction_endpoint_calls_allowed": False,
    "wallet_or_signing_material_access_allowed": False,
}
ALLOWED_LOCAL_PREFIXES = ("docs/", "pm_bot/readiness/", "pm_bot/simulated_decisions/", "pm_bot/tests/", "tests/")


def test_static_saved_evidence_replay_bundle_fixture_has_expected_contract() -> None:
    bundle = _load_bundle()

    assert tuple(bundle.keys()) == tuple(sorted(bundle.keys()))
    assert bundle["task_id"] == TASK_ID
    assert bundle["bundle_id"] == BUNDLE_ID
    assert bundle["contract_id"] == CONTRACT_ID
    assert bundle["contract_version"] == CONTRACT_VERSION
    assert bundle["run_mode"] == RUN_MODE
    assert bundle["created_at"] == "2026-05-09T00:30:00Z"
    assert bundle["local_only"] is True
    assert bundle["operator_review_required"] is True
    assert bundle["operator_review"]["status"] == OPERATOR_REVIEW_STATUS
    assert bundle["operator_review"]["reviewed_at"] is None
    assert bundle["operator_review"]["reviewed_by"] is None
    assert bundle["errors"] == []
    assert bundle["warnings"] == []


def test_saved_evidence_records_are_fixed_local_and_pending_review() -> None:
    bundle = _load_bundle()

    assert tuple(bundle["replay_record_fields"]) == EXPECTED_RECORD_FIELDS
    assert tuple(record["record_id"] for record in bundle["saved_evidence_records"]) == EXPECTED_RECORD_IDS
    for record in bundle["saved_evidence_records"]:
        assert tuple(record.keys()) == tuple(sorted(record.keys()))
        assert set(record) == set(EXPECTED_RECORD_FIELDS)
        assert record["operator_review_status"] == OPERATOR_REVIEW_STATUS
        assert record["expected_state"] in {
            "local_validation_reference",
            "pending_operator_review",
            "recorded_for_operator_review",
        }
        _assert_allowed_existing_local_reference(record["local_reference"])


def test_replay_sections_reference_declared_saved_evidence_records() -> None:
    bundle = _load_bundle()
    record_ids = {record["record_id"] for record in bundle["saved_evidence_records"]}

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


def test_operator_checks_are_local_review_records() -> None:
    bundle = _load_bundle()

    assert tuple(check["check_id"] for check in bundle["replay_checklist"]) == EXPECTED_CHECK_IDS
    for check in bundle["replay_checklist"]:
        assert tuple(check.keys()) == tuple(sorted(check.keys()))
        assert set(check) == {"check_id", "description", "required_evidence", "status"}
        assert check["status"] == OPERATOR_REVIEW_STATUS


def test_safety_boundaries_are_closed_for_saved_evidence_replay_bundle() -> None:
    bundle = _load_bundle()

    assert bundle["safety_boundaries"] == EXPECTED_SAFETY_BOUNDARIES
    assert bundle["safety_boundaries"]["local_static_artifacts_only"] is True
    assert bundle["safety_boundaries"]["operator_review_required"] is True
    assert bundle["safety_boundaries"]["paper_mode_only"] is True
    assert all(value is False for key, value in bundle["safety_boundaries"].items() if key.endswith("_allowed"))


def test_validation_commands_are_recorded_for_operator_run_local_checks() -> None:
    bundle = _load_bundle()

    assert bundle["required_validation_commands"] == [
        "python -m compileall pm_bot tests",
        "pytest pm_bot/tests tests/test_codex_queue_pmbot_templates.py",
    ]


def test_summary_counts_match_saved_evidence_replay_bundle_content() -> None:
    bundle = _load_bundle()
    local_references = {record["local_reference"] for record in bundle["saved_evidence_records"]}

    assert bundle["summary_counts"] == {
        "errors": len(bundle["errors"]),
        "local_references": len(local_references),
        "replay_checklist_items": len(bundle["replay_checklist"]),
        "replay_sections": len(bundle["replay_sections"]),
        "required_validation_commands": len(bundle["required_validation_commands"]),
        "saved_evidence_records": len(bundle["saved_evidence_records"]),
        "saved_evidence_records_pending_operator_review": sum(
            1
            for record in bundle["saved_evidence_records"]
            if record["operator_review_status"] == OPERATOR_REVIEW_STATUS
        ),
        "warnings": len(bundle["warnings"]),
    }


def test_fixture_has_no_decision_scoring_or_selection_terms() -> None:
    bundle = _load_bundle()

    assert _find_disallowed_terms(bundle) == []


def test_documentation_registers_saved_evidence_bundle_fixture_and_safety_boundary() -> None:
    document = DOC_PATH.read_text(encoding="utf-8")

    assert f"Task: `{TASK_ID}`" in document
    assert f"Bundle: `{BUNDLE_ID}`" in document
    assert f"Contract: `{CONTRACT_VERSION}`" in document
    assert f"Run mode: `{RUN_MODE}`" in document
    assert str(FIXTURE_PATH).replace("\\", "/") in document
    assert "No forecast scoring, action guidance, market ranking, numeric prediction metric" in document
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
