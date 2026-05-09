from __future__ import annotations

import json
from pathlib import Path


DOC_PATH = Path("pm_bot/readiness/PMBOT_ROADMAP_002_PMBOT_LOCAL_TO_SUPERVISED_LIVE_GAP_MATRIX.md")
FIXTURE_PATH = Path("pm_bot/tests/fixtures/readiness/pmbot_local_to_supervised_live_gap_matrix.valid.json")
TASK_ID = "PMBOT-ROADMAP-002-PMBOT-LOCAL-TO-SUPERVISED-LIVE-GAP-MATRIX"
CONTRACT_VERSION = "pmbot_local_to_supervised_live_gap_matrix.v1"
RUN_MODE = "local_static_supervised_live_gap_matrix"
MATRIX_NAME = "pmbot-local-to-supervised-live-gap-matrix"
OPERATOR_REVIEW_STATUS = "pending_operator_review"

EXPECTED_GATE_IDS = (
    "source_inventory_gate",
    "static_sample_boundary_gate",
    "source_quality_evidence_gate",
    "paper_accounting_reconciliation_gate",
    "simulated_decision_audit_gate",
    "autonomy_status_gate",
    "runtime_boundary_gate",
    "sensitive_access_boundary_gate",
    "validation_replay_gate",
)

EXPECTED_SAFETY_BOUNDARIES = {
    "authenticated_endpoint_calls_allowed": False,
    "background_process_allowed": False,
    "browser_automation_allowed": False,
    "credential_or_secret_access_allowed": False,
    "execution_endpoint_calls_allowed": False,
    "external_service_calls_allowed": False,
    "llm_provider_calls_allowed": False,
    "local_static_samples_only": True,
    "market_api_calls_allowed": False,
    "network_calls_allowed": False,
    "operator_review_required": True,
    "order_or_trade_surface_changes_allowed": False,
    "paper_mode_only": True,
    "runtime_or_dispatcher_changes_allowed": False,
    "scheduler_or_worker_allowed": False,
    "transaction_endpoint_calls_allowed": False,
    "wallet_or_signing_material_access_allowed": False,
}

ALLOWED_LOCAL_PREFIXES = ("docs/", "pm_bot/readiness/", "pm_bot/tests/", "tests/")


def test_static_gap_matrix_fixture_has_expected_contract() -> None:
    matrix = _load_matrix()

    assert tuple(matrix.keys()) == tuple(sorted(matrix.keys()))
    assert matrix["task_id"] == TASK_ID
    assert matrix["gap_matrix_name"] == MATRIX_NAME
    assert matrix["contract_version"] == CONTRACT_VERSION
    assert matrix["run_mode"] == RUN_MODE
    assert matrix["created_at"] == "2026-05-09T00:00:00Z"
    assert matrix["local_only"] is True
    assert matrix["operator_review_required"] is True
    assert matrix["operator_review"]["status"] == OPERATOR_REVIEW_STATUS
    assert matrix["errors"] == []
    assert matrix["warnings"] == []


def test_matrix_rows_are_fixed_local_and_pending_operator_review() -> None:
    matrix = _load_matrix()

    assert tuple(row["gate_id"] for row in matrix["matrix_rows"]) == EXPECTED_GATE_IDS
    for row in matrix["matrix_rows"]:
        assert set(row) == {
            "current_local_state",
            "gate_id",
            "local_reference",
            "operator_review_status",
            "required_review_evidence",
            "supervised_live_gap",
        }
        assert row["operator_review_status"] == OPERATOR_REVIEW_STATUS
        assert "://" not in row["local_reference"]
        assert row["local_reference"].startswith(ALLOWED_LOCAL_PREFIXES)


def test_safety_boundaries_are_closed_for_gap_matrix() -> None:
    matrix = _load_matrix()

    assert matrix["safety_boundaries"] == EXPECTED_SAFETY_BOUNDARIES


def test_validation_commands_are_recorded_for_operator_run_local_checks() -> None:
    matrix = _load_matrix()

    assert matrix["required_validation_commands"] == [
        "python -m compileall pm_bot tests",
        "pytest pm_bot/tests tests/test_codex_queue_pmbot_templates.py",
    ]


def test_summary_counts_match_gap_matrix_content() -> None:
    matrix = _load_matrix()
    local_references = {row["local_reference"] for row in matrix["matrix_rows"]}

    assert matrix["summary_counts"] == {
        "local_references": len(local_references),
        "matrix_rows": len(matrix["matrix_rows"]),
        "matrix_rows_pending_operator_review": sum(
            1 for row in matrix["matrix_rows"] if row["operator_review_status"] == OPERATOR_REVIEW_STATUS
        ),
        "required_validation_commands": len(matrix["required_validation_commands"]),
        "warnings": len(matrix["warnings"]),
    }


def test_fixture_has_no_guidance_scoring_or_selection_terms() -> None:
    matrix = _load_matrix()

    assert _find_disallowed_terms(matrix) == []


def test_documentation_registers_gap_matrix_fixture_and_safety_boundary() -> None:
    document = DOC_PATH.read_text(encoding="utf-8")

    assert f"Task: `{TASK_ID}`" in document
    assert f"Matrix: `{MATRIX_NAME}`" in document
    assert f"Contract: `{CONTRACT_VERSION}`" in document
    assert str(FIXTURE_PATH).replace("\\", "/") in document
    assert "No forecast scoring, action guidance, market ranking, numeric prediction metric" in document
    assert "This matrix is not execution approval and is not runtime input." in document


def _load_matrix() -> dict:
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
