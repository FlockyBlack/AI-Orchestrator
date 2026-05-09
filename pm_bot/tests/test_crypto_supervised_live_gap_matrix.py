from __future__ import annotations

import json
from pathlib import Path


DOC_PATH = Path("docs/PMBOT_CRYPTO_LIVE_011_CRYPTO_SUPERVISED_LIVE_GAP_MATRIX_LOCAL_ONLY.md")
FIXTURE_PATH = Path("pm_bot/tests/fixtures/crypto_live/pmbot_crypto_supervised_live_gap_matrix.valid.json")
OPERATOR_GATE_FIXTURE_PATH = Path("pm_bot/tests/fixtures/crypto_live/pmbot_crypto_operator_approval_gate_record.valid.json")
STOP_CONDITION_FIXTURE_PATH = Path("pm_bot/tests/fixtures/crypto_live/pmbot_crypto_stop_condition_mapping.valid.json")
TASK_ID = "PMBOT-CRYPTO-LIVE-011-CRYPTO-SUPERVISED-LIVE-GAP-MATRIX-LOCAL-ONLY"
CONTRACT_ID = "pmbot-crypto-supervised-live-gap-matrix"
CONTRACT_VERSION = "pmbot_crypto_supervised_live_gap_matrix.v1"
MATRIX_ID = "pmbot-crypto-supervised-live-gap-matrix-001"
RUN_MODE = "local_static_crypto_supervised_live_gap_matrix"
OPERATOR_REVIEW_STATUS = "pending_operator_review"
ALLOWED_LOCAL_PREFIXES = ("docs/", "pm_bot/readiness/", "pm_bot/tests/", "tests/")

EXPECTED_MATRIX_COLUMNS = (
    "gate_id",
    "current_local_state",
    "supervised_live_gap",
    "local_reference",
    "required_review_evidence",
    "mapped_source_artifact_id",
    "operator_review_status",
)
EXPECTED_GATE_IDS = (
    "crypto_read_only_contract_gate",
    "crypto_live_source_inventory_gate",
    "crypto_source_evidence_link_gate",
    "crypto_source_staleness_gate",
    "crypto_source_contradiction_gate",
    "crypto_paperlive_rehearsal_gate",
    "crypto_observation_replay_gate",
    "crypto_outcome_evidence_gate",
    "crypto_operator_approval_gate",
    "crypto_stop_condition_gate",
    "crypto_validation_replay_gate",
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
    "crypto_live_009_operator_gate_doc",
    "crypto_live_009_operator_gate_fixture",
    "crypto_live_010_stop_condition_mapping_doc",
    "crypto_live_010_stop_condition_mapping_fixture",
    "pmbot_queue_template_validation",
)
EXPECTED_CHECK_IDS = (
    "matrix_row_review",
    "source_artifact_review",
    "operator_gate_review",
    "stop_condition_review",
    "sensitive_path_exclusion_check",
    "runtime_boundary_check",
    "validation_check",
)
EXPECTED_SAFETY_BOUNDARIES = {
    "authenticated_endpoint_calls_allowed": False,
    "automated_restart_allowed": False,
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


def test_static_crypto_supervised_live_gap_matrix_fixture_has_expected_contract() -> None:
    matrix = _load_matrix()

    assert tuple(matrix.keys()) == tuple(sorted(matrix.keys()))
    assert matrix["task_id"] == TASK_ID
    assert matrix["contract_id"] == CONTRACT_ID
    assert matrix["contract_version"] == CONTRACT_VERSION
    assert matrix["gap_matrix_id"] == MATRIX_ID
    assert matrix["run_mode"] == RUN_MODE
    assert matrix["created_at"] == "2026-05-09T04:10:00Z"
    assert matrix["local_only"] is True
    assert matrix["operator_review_required"] is True
    assert matrix["operator_review"] == {
        "reviewed_at": None,
        "reviewed_by": None,
        "status": OPERATOR_REVIEW_STATUS,
    }
    assert matrix["errors"] == []
    assert matrix["warnings"] == []


def test_matrix_rows_are_fixed_local_pending_and_map_to_source_artifacts() -> None:
    matrix = _load_matrix()
    source_artifact_ids = {artifact["artifact_id"] for artifact in matrix["source_artifacts"]}

    assert tuple(matrix["matrix_columns"]) == EXPECTED_MATRIX_COLUMNS
    assert tuple(row["gate_id"] for row in matrix["matrix_rows"]) == EXPECTED_GATE_IDS
    for row in matrix["matrix_rows"]:
        assert tuple(row.keys()) == tuple(sorted(row.keys()))
        assert set(row) == set(EXPECTED_MATRIX_COLUMNS)
        assert row["operator_review_status"] == OPERATOR_REVIEW_STATUS
        assert row["mapped_source_artifact_id"] in source_artifact_ids
        _assert_allowed_existing_local_reference(row["local_reference"])


def test_matrix_references_operator_gate_and_stop_condition_static_fixtures() -> None:
    matrix = _load_matrix()
    operator_gate = _load_json(OPERATOR_GATE_FIXTURE_PATH)
    stop_mapping = _load_json(STOP_CONDITION_FIXTURE_PATH)
    rows_by_id = {row["gate_id"]: row for row in matrix["matrix_rows"]}

    assert rows_by_id["crypto_operator_approval_gate"]["local_reference"] == str(OPERATOR_GATE_FIXTURE_PATH).replace(
        "\\", "/"
    )
    assert rows_by_id["crypto_stop_condition_gate"]["local_reference"] == str(STOP_CONDITION_FIXTURE_PATH).replace(
        "\\", "/"
    )
    assert operator_gate["gate_result"] == "blocked_until_operator_record_complete"
    assert all(record["approval_state"] == "not_approved" for record in operator_gate["gate_records"])
    assert all(record["operator_review_status"] == OPERATOR_REVIEW_STATUS for record in operator_gate["gate_records"])
    assert all(record["manual_record_required"] is True for record in stop_mapping["stop_condition_records"])
    assert all(
        record["operator_review_status"] == OPERATOR_REVIEW_STATUS
        for record in stop_mapping["stop_condition_records"]
    )


def test_source_artifacts_reference_only_allowed_existing_local_review_material() -> None:
    matrix = _load_matrix()

    assert tuple(artifact["artifact_id"] for artifact in matrix["source_artifacts"]) == EXPECTED_SOURCE_ARTIFACT_IDS
    for artifact in matrix["source_artifacts"]:
        assert tuple(artifact.keys()) == tuple(sorted(artifact.keys()))
        assert set(artifact) == {
            "artifact_id",
            "contract_version",
            "local_reference",
            "required_state",
        }
        assert artifact["required_state"] in {OPERATOR_REVIEW_STATUS, "local_validation_reference"}
        _assert_allowed_existing_local_reference(artifact["local_reference"])


def test_operator_checklist_and_validation_commands_remain_pending() -> None:
    matrix = _load_matrix()

    assert tuple(check["check_id"] for check in matrix["operator_review_checklist"]) == EXPECTED_CHECK_IDS
    for check in matrix["operator_review_checklist"]:
        assert tuple(check.keys()) == tuple(sorted(check.keys()))
        assert check["status"] == OPERATOR_REVIEW_STATUS
    assert matrix["required_validation_commands"] == [
        "python -m compileall pm_bot tests",
        "pytest pm_bot/tests tests/test_codex_queue_pmbot_templates.py",
    ]


def test_safety_boundaries_are_closed_for_crypto_supervised_live_gap_matrix() -> None:
    matrix = _load_matrix()

    assert matrix["safety_boundaries"] == EXPECTED_SAFETY_BOUNDARIES
    assert matrix["safety_boundaries"]["local_static_samples_only"] is True
    assert matrix["safety_boundaries"]["operator_review_required"] is True
    assert matrix["safety_boundaries"]["paper_mode_only"] is True
    assert all(value is False for key, value in matrix["safety_boundaries"].items() if key.endswith("_allowed"))


def test_summary_counts_match_crypto_gap_matrix_content() -> None:
    matrix = _load_matrix()
    local_references = {
        *(row["local_reference"] for row in matrix["matrix_rows"]),
        *(artifact["local_reference"] for artifact in matrix["source_artifacts"]),
    }

    assert matrix["summary_counts"] == {
        "gap_rows": len(matrix["matrix_rows"]),
        "gap_rows_pending_operator_review": sum(
            1 for row in matrix["matrix_rows"] if row["operator_review_status"] == OPERATOR_REVIEW_STATUS
        ),
        "local_references": len(local_references),
        "operator_review_checklist_items": len(matrix["operator_review_checklist"]),
        "required_validation_commands": len(matrix["required_validation_commands"]),
        "source_artifacts": len(matrix["source_artifacts"]),
        "warnings": len(matrix["warnings"]),
    }


def test_fixture_has_no_decision_scoring_or_selection_terms() -> None:
    matrix = _load_matrix()

    assert _find_disallowed_terms(matrix) == []


def test_documentation_registers_crypto_gap_matrix_fixture_and_safety_boundary() -> None:
    document = DOC_PATH.read_text(encoding="utf-8")

    assert f"Task: `{TASK_ID}`" in document
    assert f"Matrix: `{MATRIX_ID}`" in document
    assert f"Contract: `{CONTRACT_VERSION}`" in document
    assert f"Run mode: `{RUN_MODE}`" in document
    assert str(FIXTURE_PATH).replace("\\", "/") in document
    assert str(OPERATOR_GATE_FIXTURE_PATH).replace("\\", "/") in document
    assert str(STOP_CONDITION_FIXTURE_PATH).replace("\\", "/") in document
    assert "No forecast scoring, action guidance, market ranking" in document
    assert "This matrix is not execution approval and is not runtime input." in document


def _load_matrix() -> dict:
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
