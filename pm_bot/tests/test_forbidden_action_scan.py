from __future__ import annotations

import json
from pathlib import Path


DOC_PATH = Path("docs/PMBOT_SAFETY_003_FORBIDDEN_ACTION_SCAN_LOCAL_ONLY.md")
FIXTURE_PATH = Path("pm_bot/tests/fixtures/safety/forbidden_action_scan.valid.json")
TASK_ID = "PMBOT-SAFETY-003-FORBIDDEN-ACTION-SCAN-LOCAL-ONLY"
CONTRACT_VERSION = "pmbot_forbidden_action_scan.v1"
RUN_MODE = "local_static_forbidden_action_scan"
SCAN_ID = "pmbot_forbidden_action_scan_001"
SCAN_NAME = "pmbot-forbidden-action-scan"
OPERATOR_REVIEW_STATUS = "pending_operator_review"

EXPECTED_SCAN_INPUT_IDS = (
    "queue_template_safety_contract",
    "autonomy_gate_record",
    "postrun_audit_record",
    "static_scan_fixture",
)

EXPECTED_FINDING_IDS = (
    "credential_boundary_closed",
    "endpoint_boundary_closed",
    "wallet_boundary_closed",
    "runtime_boundary_closed",
    "scheduler_boundary_closed",
    "network_boundary_closed",
    "descriptive_output_boundary_closed",
    "human_review_boundary_pending",
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
    "runtime_or_dispatcher_changes_allowed": False,
    "scheduler_or_worker_allowed": False,
    "transaction_endpoint_calls_allowed": False,
    "wallet_or_signing_material_access_allowed": False,
}

ALLOWED_LOCAL_PREFIXES = ("docs/", "pm_bot/tests/", "tests/")


def test_static_forbidden_action_scan_fixture_has_expected_contract() -> None:
    scan = _load_scan()

    assert tuple(scan.keys()) == tuple(sorted(scan.keys()))
    assert scan["task_id"] == TASK_ID
    assert scan["forbidden_action_scan_id"] == SCAN_ID
    assert scan["scan_name"] == SCAN_NAME
    assert scan["contract_version"] == CONTRACT_VERSION
    assert scan["run_mode"] == RUN_MODE
    assert scan["created_at"] == "2026-05-09T00:00:00Z"
    assert scan["local_only"] is True
    assert scan["operator_review_required"] is True
    assert scan["operator_review"]["status"] == OPERATOR_REVIEW_STATUS
    assert scan["errors"] == []
    assert scan["warnings"] == []


def test_scan_inputs_are_fixed_local_and_pending_operator_review() -> None:
    scan = _load_scan()

    assert tuple(item["input_id"] for item in scan["scan_inputs"]) == EXPECTED_SCAN_INPUT_IDS
    for item in scan["scan_inputs"]:
        assert set(item) == {
            "input_id",
            "local_reference",
            "observed_state",
            "operator_review_status",
        }
        assert item["operator_review_status"] == OPERATOR_REVIEW_STATUS
        assert "://" not in item["local_reference"]
        assert item["local_reference"].startswith(ALLOWED_LOCAL_PREFIXES)


def test_scan_findings_are_fixed_local_and_pending_operator_review() -> None:
    scan = _load_scan()

    assert tuple(finding["finding_id"] for finding in scan["scan_findings"]) == EXPECTED_FINDING_IDS
    for finding in scan["scan_findings"]:
        assert set(finding) == {
            "category",
            "finding_id",
            "inspection_label",
            "local_reference",
            "observed_state",
            "operator_review_status",
        }
        assert finding["operator_review_status"] == OPERATOR_REVIEW_STATUS
        assert "://" not in finding["local_reference"]
        assert finding["local_reference"].startswith(ALLOWED_LOCAL_PREFIXES)


def test_safety_boundaries_are_closed_for_forbidden_action_scan() -> None:
    scan = _load_scan()

    assert scan["safety_boundaries"] == EXPECTED_SAFETY_BOUNDARIES


def test_validation_commands_are_recorded_for_operator_run_local_checks() -> None:
    scan = _load_scan()

    assert scan["required_validation_commands"] == [
        "python -m compileall pm_bot tests",
        "pytest pm_bot/tests tests/test_codex_queue_pmbot_templates.py",
    ]


def test_summary_counts_match_scan_content() -> None:
    scan = _load_scan()
    local_references = {item["local_reference"] for item in scan["scan_inputs"]}
    local_references.update(finding["local_reference"] for finding in scan["scan_findings"])

    assert scan["summary_counts"] == {
        "local_references": len(local_references),
        "required_validation_commands": len(scan["required_validation_commands"]),
        "scan_findings": len(scan["scan_findings"]),
        "scan_findings_pending_operator_review": sum(
            1 for finding in scan["scan_findings"] if finding["operator_review_status"] == OPERATOR_REVIEW_STATUS
        ),
        "scan_inputs": len(scan["scan_inputs"]),
        "warnings": len(scan["warnings"]),
    }


def test_fixture_has_no_guidance_scoring_or_selection_terms() -> None:
    scan = _load_scan()

    assert _find_disallowed_terms(scan) == []


def test_documentation_registers_forbidden_action_scan_fixture_and_safety_boundary() -> None:
    document = DOC_PATH.read_text(encoding="utf-8")

    assert f"Task: `{TASK_ID}`" in document
    assert f"Scan: `{SCAN_NAME}`" in document
    assert f"Contract: `{CONTRACT_VERSION}`" in document
    assert str(FIXTURE_PATH).replace("\\", "/") in document
    assert "No forecast scoring, action guidance, or selection advice." in document
    assert "This scan is not execution approval and is not runtime input." in document


def _load_scan() -> dict:
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
