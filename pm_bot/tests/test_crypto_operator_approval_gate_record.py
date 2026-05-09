from __future__ import annotations

import json
from pathlib import Path


DOC_PATH = Path("docs/PMBOT_CRYPTO_LIVE_009_CRYPTO_OPERATOR_APPROVAL_GATE_RECORD_LOCAL_ONLY.md")
FIXTURE_PATH = Path("pm_bot/tests/fixtures/crypto_live/pmbot_crypto_operator_approval_gate_record.valid.json")
TASK_ID = "PMBOT-CRYPTO-LIVE-009-CRYPTO-OPERATOR-APPROVAL-GATE-RECORD-LOCAL-ONLY"
CONTRACT_ID = "pmbot-crypto-operator-approval-gate-record"
CONTRACT_VERSION = "pmbot_crypto_operator_approval_gate_record.v1"
APPROVAL_GATE_ID = "pmbot-crypto-operator-approval-gate-record-001"
RUN_MODE = "local_static_crypto_operator_approval_gate_record"
OPERATOR_REVIEW_STATUS = "pending_operator_review"
ALLOWED_LOCAL_PREFIXES = ("docs/", "pm_bot/readiness/", "pm_bot/tests/", "tests/")

EXPECTED_GATE_IDS = (
    "read_only_crypto_data_contract_review",
    "crypto_live_data_source_inventory_review",
    "crypto_source_evidence_link_map_review",
    "crypto_source_staleness_check_spec_review",
    "crypto_source_contradiction_ledger_review",
    "crypto_paperlive_rehearsal_packet_review",
    "crypto_paperlive_observation_replay_review",
    "crypto_outcome_evidence_bundle_review",
    "human_approval_record_completion",
)
EXPECTED_SOURCE_ARTIFACT_IDS = (
    "crypto_live_001_read_only_contract_doc",
    "read_only_crypto_data_contract_fixture",
    "crypto_live_002_data_source_inventory_doc",
    "crypto_live_data_source_inventory_fixture",
    "crypto_live_003_source_evidence_link_map_doc",
    "crypto_live_004_source_staleness_check_spec_doc",
    "crypto_live_005_source_contradiction_ledger_doc",
    "crypto_live_006_rehearsal_packet_doc",
    "crypto_live_006_rehearsal_packet_fixture",
    "crypto_live_007_observation_replay_doc",
    "crypto_live_007_observation_replay_fixture",
    "crypto_live_008_outcome_evidence_bundle_doc",
    "crypto_live_008_outcome_evidence_bundle_fixture",
    "pmbot_queue_template_validation",
)
EXPECTED_LOCAL_REFERENCES = (
    "docs/PMBOT_CRYPTO_LIVE_001_READ_ONLY_CRYPTO_DATA_CONTRACT_LOCAL_ONLY.md",
    "docs/PMBOT_CRYPTO_LIVE_002_CRYPTO_LIVE_DATA_SOURCE_INVENTORY_LOCAL_ONLY.md",
    "docs/PMBOT_CRYPTO_LIVE_003_CRYPTO_SOURCE_EVIDENCE_LINK_MAP_LOCAL_ONLY.md",
    "docs/PMBOT_CRYPTO_LIVE_004_CRYPTO_SOURCE_STALENESS_CHECK_SPEC_LOCAL_ONLY.md",
    "docs/PMBOT_CRYPTO_LIVE_005_CRYPTO_SOURCE_CONTRADICTION_LEDGER_LOCAL_ONLY.md",
    "docs/PMBOT_CRYPTO_LIVE_006_CRYPTO_PAPERLIVE_REHEARSAL_PACKET_LOCAL_ONLY.md",
    "docs/PMBOT_CRYPTO_LIVE_007_CRYPTO_PAPERLIVE_OBSERVATION_REPLAY_LOCAL_ONLY.md",
    "docs/PMBOT_CRYPTO_LIVE_008_CRYPTO_OUTCOME_EVIDENCE_BUNDLE_LOCAL_ONLY.md",
    str(FIXTURE_PATH).replace("\\", "/"),
    "pm_bot/tests/fixtures/crypto_live/pmbot_crypto_live_data_source_inventory.valid.json",
    "pm_bot/tests/fixtures/crypto_live/pmbot_crypto_outcome_evidence_bundle.valid.json",
    "pm_bot/tests/fixtures/crypto_live/pmbot_crypto_paperlive_observation_replay.valid.json",
    "pm_bot/tests/fixtures/crypto_live/pmbot_crypto_paperlive_rehearsal_packet.valid.json",
    "pm_bot/tests/fixtures/crypto_live/pmbot_read_only_crypto_data_contract.valid.json",
    "tests/test_codex_queue_pmbot_templates.py",
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
    "supervised_live_transition_allowed": False,
    "threshold_comparison_output_allowed": False,
    "trade_instruction_allowed": False,
    "transaction_endpoint_calls_allowed": False,
    "transition_without_record_allowed": False,
    "value_transform_allowed": False,
    "wallet_or_signing_material_access_allowed": False,
}


def test_static_crypto_operator_approval_gate_record_fixture_has_expected_contract() -> None:
    record = _load_record()

    assert tuple(record.keys()) == tuple(sorted(record.keys()))
    assert record["task_id"] == TASK_ID
    assert record["approval_gate_id"] == APPROVAL_GATE_ID
    assert record["contract_id"] == CONTRACT_ID
    assert record["contract_version"] == CONTRACT_VERSION
    assert record["run_mode"] == RUN_MODE
    assert record["created_at"] == "2026-05-09T03:30:00Z"
    assert record["gate_result"] == "blocked_until_operator_record_complete"
    assert record["local_only"] is True
    assert record["operator_review_required"] is True
    assert record["operator_review"] == {
        "reviewed_at": None,
        "reviewed_by": None,
        "status": OPERATOR_REVIEW_STATUS,
    }
    assert record["errors"] == []
    assert record["warnings"] == []


def test_gate_records_are_fixed_local_pending_and_not_approved() -> None:
    record = _load_record()

    assert tuple(gate["gate_id"] for gate in record["gate_records"]) == EXPECTED_GATE_IDS
    for gate in record["gate_records"]:
        assert tuple(gate.keys()) == tuple(sorted(gate.keys()))
        assert set(gate) == {
            "approval_state",
            "evidence_required",
            "gate_id",
            "gate_label",
            "local_reference",
            "operator_review_status",
            "required_prior_state",
            "scope_boundary",
            "transition_state",
        }
        assert gate["approval_state"] == "not_approved"
        assert gate["operator_review_status"] == OPERATOR_REVIEW_STATUS
        assert gate["required_prior_state"] == OPERATOR_REVIEW_STATUS
        assert gate["transition_state"] == "blocked_until_record_complete"
        _assert_allowed_existing_local_reference(gate["local_reference"])


def test_source_artifacts_reference_only_local_review_material() -> None:
    record = _load_record()

    assert tuple(artifact["artifact_id"] for artifact in record["source_artifacts"]) == EXPECTED_SOURCE_ARTIFACT_IDS
    for artifact in record["source_artifacts"]:
        assert tuple(artifact.keys()) == tuple(sorted(artifact.keys()))
        assert set(artifact) == {
            "artifact_id",
            "contract_version",
            "local_reference",
            "required_state",
        }
        assert artifact["required_state"] in {OPERATOR_REVIEW_STATUS, "local_validation_reference"}
        _assert_allowed_existing_local_reference(artifact["local_reference"])


def test_safety_boundaries_are_closed_for_crypto_operator_approval_gate_record() -> None:
    record = _load_record()

    assert record["safety_boundaries"] == EXPECTED_SAFETY_BOUNDARIES
    assert record["safety_boundaries"]["local_static_samples_only"] is True
    assert record["safety_boundaries"]["operator_review_required"] is True
    assert record["safety_boundaries"]["paper_mode_only"] is True
    assert all(value is False for key, value in record["safety_boundaries"].items() if key.endswith("_allowed"))


def test_validation_commands_are_recorded_for_local_crypto_operator_run_checks() -> None:
    record = _load_record()

    assert record["required_validation_commands"] == [
        "python -m compileall pm_bot tests",
        "pytest pm_bot/tests tests/test_codex_queue_pmbot_templates.py",
    ]


def test_summary_counts_match_crypto_operator_approval_gate_record_content() -> None:
    record = _load_record()
    gate_records = record["gate_records"]
    local_references = {
        *(gate["local_reference"] for gate in gate_records),
        *(artifact["local_reference"] for artifact in record["source_artifacts"]),
    }

    assert record["summary_counts"] == {
        "gate_records": len(gate_records),
        "gate_records_pending_operator_review": sum(
            1 for gate in gate_records if gate["operator_review_status"] == OPERATOR_REVIEW_STATUS
        ),
        "local_references": len(local_references),
        "required_validation_commands": len(record["required_validation_commands"]),
        "source_artifacts": len(record["source_artifacts"]),
        "warnings": len(record["warnings"]),
    }


def test_crypto_operator_gate_references_only_expected_local_static_paths() -> None:
    record = _load_record()
    references = sorted(
        {
            *(gate["local_reference"] for gate in record["gate_records"]),
            *(artifact["local_reference"] for artifact in record["source_artifacts"]),
        }
    )

    assert references == sorted(EXPECTED_LOCAL_REFERENCES)
    for reference in references:
        _assert_allowed_existing_local_reference(reference)


def test_fixture_has_no_decision_scoring_or_selection_terms() -> None:
    record = _load_record()

    assert _find_disallowed_terms(record) == []


def test_documentation_registers_crypto_operator_gate_fixture_and_safety_boundary() -> None:
    document = DOC_PATH.read_text(encoding="utf-8")

    assert f"Task: `{TASK_ID}`" in document
    assert f"Gate: `{APPROVAL_GATE_ID}`" in document
    assert f"Contract: `{CONTRACT_VERSION}`" in document
    assert f"Run mode: `{RUN_MODE}`" in document
    assert str(FIXTURE_PATH).replace("\\", "/") in document
    assert "No forecast scoring, action guidance, market ranking" in document
    assert "This record is not execution approval and is not runtime input." in document


def _load_record() -> dict:
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
