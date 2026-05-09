from __future__ import annotations

import json
from pathlib import Path


DOC_PATH = Path("docs/PMBOT_SAFETY_001_AUTONOMY_GATE_CHECKLIST_LOCAL_ONLY.md")
FIXTURE_PATH = Path("pm_bot/tests/fixtures/safety/autonomy_gate_checklist.valid.json")
TASK_ID = "PMBOT-SAFETY-001-AUTONOMY-GATE-CHECKLIST-LOCAL-ONLY"
CONTRACT_VERSION = "pmbot_autonomy_gate_checklist.v1"
RUN_MODE = "local_static_operator_gate_checklist"
CHECKLIST_NAME = "pmbot-autonomy-gate-checklist"
OPERATOR_REVIEW_STATUS = "pending_operator_review"

EXPECTED_ENTRY_IDS = (
    "scope_boundary_check",
    "forbidden_path_check",
    "local_reference_check",
    "endpoint_isolation_check",
    "descriptive_output_check",
    "validation_command_check",
    "human_review_check",
)

EXPECTED_SAFETY_BOUNDARIES = {
    "authenticated_endpoint_calls_allowed": False,
    "background_process_allowed": False,
    "browser_automation_allowed": False,
    "credential_or_secret_access_allowed": False,
    "execution_endpoint_calls_allowed": False,
    "external_service_calls_allowed": False,
    "local_static_samples_only": True,
    "network_calls_allowed": False,
    "operator_review_required": True,
    "runtime_or_dispatcher_changes_allowed": False,
    "scheduler_or_worker_allowed": False,
    "transaction_endpoint_calls_allowed": False,
    "wallet_or_signing_material_access_allowed": False,
}


def test_static_autonomy_gate_checklist_fixture_has_expected_contract() -> None:
    checklist = _load_checklist()

    assert tuple(checklist.keys()) == tuple(sorted(checklist.keys()))
    assert checklist["task_id"] == TASK_ID
    assert checklist["checklist_name"] == CHECKLIST_NAME
    assert checklist["contract_version"] == CONTRACT_VERSION
    assert checklist["run_mode"] == RUN_MODE
    assert checklist["created_at"] == "2026-05-09T00:00:00Z"
    assert checklist["local_only"] is True
    assert checklist["operator_review_required"] is True
    assert checklist["operator_review"]["status"] == OPERATOR_REVIEW_STATUS
    assert checklist["errors"] == []
    assert checklist["warnings"] == []


def test_gate_entries_are_fixed_local_and_pending_operator_review() -> None:
    checklist = _load_checklist()

    assert tuple(entry["entry_id"] for entry in checklist["checklist_entries"]) == EXPECTED_ENTRY_IDS
    for entry in checklist["checklist_entries"]:
        assert set(entry) == {
            "entry_id",
            "expected_state",
            "inspection_label",
            "local_reference",
            "operator_review_status",
        }
        assert entry["operator_review_status"] == OPERATOR_REVIEW_STATUS
        assert "://" not in entry["local_reference"]
        assert entry["local_reference"].startswith(("docs/", "pm_bot/tests/", "tests/"))


def test_safety_boundaries_are_closed_for_local_autonomy_gate_checklist() -> None:
    checklist = _load_checklist()

    assert checklist["safety_boundaries"] == EXPECTED_SAFETY_BOUNDARIES


def test_validation_commands_are_recorded_for_operator_run_local_checks() -> None:
    checklist = _load_checklist()

    assert checklist["required_validation_commands"] == [
        "python -m compileall pm_bot tests",
        "pytest pm_bot/tests tests/test_codex_queue_pmbot_templates.py",
    ]


def test_summary_counts_match_checklist_content() -> None:
    checklist = _load_checklist()

    assert checklist["summary_counts"] == {
        "checklist_entries": len(checklist["checklist_entries"]),
        "local_references": len({entry["local_reference"] for entry in checklist["checklist_entries"]}),
        "required_validation_commands": len(checklist["required_validation_commands"]),
        "warnings": len(checklist["warnings"]),
    }


def test_fixture_has_no_guidance_scoring_or_selection_terms() -> None:
    checklist = _load_checklist()

    assert _find_disallowed_terms(checklist) == []


def test_documentation_registers_autonomy_gate_fixture_and_safety_boundary() -> None:
    document = DOC_PATH.read_text(encoding="utf-8")

    assert f"Task: `{TASK_ID}`" in document
    assert f"Checklist: `{CHECKLIST_NAME}`" in document
    assert f"Contract: `{CONTRACT_VERSION}`" in document
    assert str(FIXTURE_PATH).replace("\\", "/") in document
    assert "No forecast scoring, action guidance, market ranking, or selection advice." in document
    assert "This checklist is not execution approval and is not runtime input." in document


def _load_checklist() -> dict:
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
