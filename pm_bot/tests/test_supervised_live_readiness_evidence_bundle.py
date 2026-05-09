from __future__ import annotations

import json
from pathlib import Path


DOC_PATH = Path("docs/PMBOT_SUPERVISED_LIVE_005_LIVE_READINESS_EVIDENCE_BUNDLE_LOCAL_ONLY.md")
FIXTURE_PATH = Path("pm_bot/tests/fixtures/readiness/pmbot_supervised_live_readiness_evidence_bundle.valid.json")
TASK_ID = "PMBOT-SUPERVISED-LIVE-005-LIVE-READINESS-EVIDENCE-BUNDLE-LOCAL-ONLY"
CONTRACT_ID = "pmbot-supervised-live-readiness-evidence-bundle"
CONTRACT_VERSION = "pmbot_supervised_live_readiness_evidence_bundle.v1"
BUNDLE_ID = "pmbot-supervised-live-readiness-evidence-bundle-001"
RUN_MODE = "local_static_supervised_live_readiness_evidence_bundle"
OPERATOR_REVIEW_STATUS = "pending_operator_review"

EXPECTED_SECTION_IDS = (
    "read_only_contract_evidence",
    "source_inventory_evidence",
    "operator_gate_evidence",
    "stop_condition_evidence",
)
EXPECTED_RECORD_FIELDS = (
    "record_id",
    "artifact_id",
    "artifact_type",
    "contract_version",
    "local_reference",
    "operator_review_status",
    "required_state",
    "review_material",
    "review_note",
)
EXPECTED_RECORD_IDS = (
    "readiness_evidence_bundle_001.read_only_live_data_contract",
    "readiness_evidence_bundle_001.live_data_source_inventory",
    "readiness_evidence_bundle_001.operator_approval_gate_record",
    "readiness_evidence_bundle_001.supervised_live_stop_condition_spec",
    "readiness_evidence_bundle_001.local_to_supervised_live_gap_matrix",
    "readiness_evidence_bundle_001.autonomy_gate_checklist",
    "readiness_evidence_bundle_001.forbidden_action_scan",
    "readiness_evidence_bundle_001.pmbot_queue_template_validation",
)
EXPECTED_CHECK_IDS = (
    "bundle_reference_review",
    "fixture_presence_review",
    "operator_state_review",
    "sensitive_path_exclusion_check",
    "runtime_boundary_check",
    "output_boundary_check",
    "validation_replay_check",
)
EXPECTED_SOURCE_ARTIFACT_IDS = (
    "read_only_live_data_contract_fixture",
    "live_data_source_inventory_fixture",
    "operator_approval_gate_record_fixture",
    "supervised_live_stop_condition_spec_fixture",
    "readiness_evidence_bundle_fixture",
)
EXPECTED_SAFETY_BOUNDARIES = {
    "artifact_status_change_allowed": False,
    "authenticated_endpoint_calls_allowed": False,
    "automated_restart_allowed": False,
    "background_process_allowed": False,
    "browser_automation_allowed": False,
    "bundle_mutates_source_artifacts_allowed": False,
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
    "supervised_live_transition_allowed": False,
    "trade_instruction_allowed": False,
    "transaction_endpoint_calls_allowed": False,
    "wallet_or_signing_material_access_allowed": False,
}
ALLOWED_LOCAL_PREFIXES = ("docs/", "pm_bot/readiness/", "pm_bot/tests/", "tests/")


def test_static_readiness_evidence_bundle_fixture_has_expected_contract() -> None:
    bundle = _load_bundle()

    assert tuple(bundle.keys()) == tuple(sorted(bundle.keys()))
    assert bundle["task_id"] == TASK_ID
    assert bundle["bundle_id"] == BUNDLE_ID
    assert bundle["contract_id"] == CONTRACT_ID
    assert bundle["contract_version"] == CONTRACT_VERSION
    assert bundle["run_mode"] == RUN_MODE
    assert bundle["created_at"] == "2026-05-09T00:00:00Z"
    assert bundle["local_only"] is True
    assert bundle["operator_review_required"] is True
    assert bundle["operator_review"]["status"] == OPERATOR_REVIEW_STATUS
    assert bundle["operator_review"]["reviewed_at"] is None
    assert bundle["operator_review"]["reviewed_by"] is None
    assert bundle["errors"] == []
    assert bundle["warnings"] == []


def test_bundle_sections_are_fixed_local_and_pending_review() -> None:
    bundle = _load_bundle()

    assert tuple(section["section_id"] for section in bundle["bundle_sections"]) == EXPECTED_SECTION_IDS
    for section in bundle["bundle_sections"]:
        assert tuple(section.keys()) == tuple(sorted(section.keys()))
        assert set(section) == {
            "local_references",
            "operator_review_status",
            "section_id",
            "section_label",
            "section_role",
        }
        assert section["operator_review_status"] == OPERATOR_REVIEW_STATUS
        assert section["local_references"]
        for local_reference in section["local_references"]:
            _assert_allowed_existing_local_reference(local_reference)


def test_evidence_records_are_fixed_local_and_pending_review() -> None:
    bundle = _load_bundle()

    assert tuple(bundle["evidence_record_fields"]) == EXPECTED_RECORD_FIELDS
    assert tuple(record["record_id"] for record in bundle["evidence_records"]) == EXPECTED_RECORD_IDS
    for record in bundle["evidence_records"]:
        assert tuple(record.keys()) == tuple(sorted(record.keys()))
        assert set(record) == set(EXPECTED_RECORD_FIELDS)
        assert record["operator_review_status"] == OPERATOR_REVIEW_STATUS
        assert record["review_material"] in {
            "local_markdown_and_fixture",
            "local_readiness_markdown_and_fixture",
            "local_test_file",
        }
        _assert_allowed_existing_local_reference(record["local_reference"])


def test_operator_checks_and_source_artifacts_are_local_review_records() -> None:
    bundle = _load_bundle()

    assert tuple(check["check_id"] for check in bundle["operator_review_checklist"]) == EXPECTED_CHECK_IDS
    assert all(check["status"] == OPERATOR_REVIEW_STATUS for check in bundle["operator_review_checklist"])
    assert tuple(artifact["artifact_id"] for artifact in bundle["source_artifacts"]) == EXPECTED_SOURCE_ARTIFACT_IDS
    for artifact in bundle["source_artifacts"]:
        assert tuple(artifact.keys()) == tuple(sorted(artifact.keys()))
        assert set(artifact) == {
            "artifact_id",
            "contract_version",
            "local_reference",
            "required_state",
        }
        assert artifact["required_state"] == OPERATOR_REVIEW_STATUS
        _assert_allowed_existing_local_reference(artifact["local_reference"])


def test_safety_boundaries_are_closed_for_readiness_evidence_bundle() -> None:
    bundle = _load_bundle()

    assert bundle["safety_boundaries"] == EXPECTED_SAFETY_BOUNDARIES
    assert bundle["safety_boundaries"]["local_static_samples_only"] is True
    assert bundle["safety_boundaries"]["operator_review_required"] is True
    assert bundle["safety_boundaries"]["paper_mode_only"] is True
    assert all(value is False for key, value in bundle["safety_boundaries"].items() if key.endswith("_allowed"))


def test_validation_commands_are_recorded_for_operator_run_local_checks() -> None:
    bundle = _load_bundle()

    assert bundle["required_validation_commands"] == [
        "python -m compileall pm_bot tests",
        "pytest pm_bot/tests tests/test_codex_queue_pmbot_templates.py",
    ]


def test_summary_counts_match_readiness_evidence_bundle_content() -> None:
    bundle = _load_bundle()
    local_references = {
        *(reference for section in bundle["bundle_sections"] for reference in section["local_references"]),
        *(record["local_reference"] for record in bundle["evidence_records"]),
        *(artifact["local_reference"] for artifact in bundle["source_artifacts"]),
    }

    assert bundle["summary_counts"] == {
        "bundle_sections": len(bundle["bundle_sections"]),
        "evidence_records": len(bundle["evidence_records"]),
        "evidence_records_pending_operator_review": sum(
            1 for record in bundle["evidence_records"] if record["operator_review_status"] == OPERATOR_REVIEW_STATUS
        ),
        "local_references": len(local_references),
        "operator_review_checklist_items": len(bundle["operator_review_checklist"]),
        "required_validation_commands": len(bundle["required_validation_commands"]),
        "source_artifacts": len(bundle["source_artifacts"]),
        "warnings": len(bundle["warnings"]),
    }


def test_fixture_has_no_decision_scoring_or_selection_terms() -> None:
    bundle = _load_bundle()

    assert _find_disallowed_terms(bundle) == []


def test_documentation_registers_bundle_fixture_and_safety_boundary() -> None:
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
