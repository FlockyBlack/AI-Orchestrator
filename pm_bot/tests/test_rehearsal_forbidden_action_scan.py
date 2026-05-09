from __future__ import annotations

import json
from pathlib import Path


DOC_PATH = Path("docs/PMBOT_REHEARSAL_017_REHEARSAL_FORBIDDEN_ACTION_SCAN_LOCAL_ONLY.md")
FIXTURE_PATH = Path("pm_bot/tests/fixtures/rehearsal/pmbot_rehearsal_forbidden_action_scan.valid.json")
TASK_ID = "PMBOT-REHEARSAL-017-REHEARSAL-FORBIDDEN-ACTION-SCAN-LOCAL-ONLY"
CONTRACT_VERSION = "pmbot_rehearsal_forbidden_action_scan.v1"
RUN_MODE = "local_static_rehearsal_forbidden_action_scan"
SCAN_ID = "pmbot-rehearsal-forbidden-action-scan-001"
OPERATOR_REVIEW_STATUS = "pending_operator_review"
ALLOWED_LOCAL_PREFIXES = ("docs/", "pm_bot/tests/", "tests/")

EXPECTED_EXCLUDED_PREFIXES = (
    ".env",
    ".env.*",
    ".git/",
    ".codex/",
    "runtime/",
    "dispatcher/",
    "run_codex/",
    "pm_bot/llm/",
    "pm_bot/wallet/",
    "pm_bot/trading/",
    "pm_bot/orders/",
    "agent_tasks/running/",
)

EXPECTED_SCAN_INPUT_IDS = (
    "queue_template_rehearsal_task_contract",
    "prior_rehearsal_simulated_decision_links_document",
    "baseline_forbidden_action_scan_document",
    "baseline_forbidden_action_scan_fixture",
    "rehearsal_validation_replay_packet_fixture",
    "rehearsal_ci_safe_validation_runner_fixture",
    "rehearsal_forbidden_action_scan_fixture",
    "rehearsal_forbidden_action_scan_contract_test",
)

EXPECTED_SCAN_ROW_IDS = (
    "local_material_boundary_closed",
    "network_boundary_closed",
    "openrouter_boundary_closed",
    "polymarket_api_boundary_closed",
    "authenticated_endpoint_boundary_closed",
    "credential_and_secret_boundary_closed",
    "wallet_and_signing_boundary_closed",
    "order_and_trading_boundary_closed",
    "runtime_dispatcher_run_codex_boundary_closed",
    "scheduler_worker_browser_boundary_closed",
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
    "openrouter_calls_allowed": False,
    "operator_review_required": True,
    "order_or_trade_surface_changes_allowed": False,
    "paper_mode_only": True,
    "polymarket_api_calls_allowed": False,
    "runtime_or_dispatcher_changes_allowed": False,
    "scheduler_or_worker_allowed": False,
    "sensitive_path_access_allowed": False,
    "transaction_endpoint_calls_allowed": False,
    "wallet_or_signing_material_access_allowed": False,
}


def test_static_rehearsal_forbidden_action_scan_has_expected_contract() -> None:
    scan = _load_scan()

    assert tuple(scan.keys()) == tuple(sorted(scan.keys()))
    assert scan["task_id"] == TASK_ID
    assert scan["forbidden_action_scan_id"] == SCAN_ID
    assert scan["contract_version"] == CONTRACT_VERSION
    assert scan["run_mode"] == RUN_MODE
    assert scan["created_at"] == "2026-05-09T11:00:00Z"
    assert scan["local_only"] is True
    assert scan["operator_review_required"] is True
    assert scan["operator_review"] == {
        "reviewed_at": None,
        "reviewed_by": None,
        "status": OPERATOR_REVIEW_STATUS,
    }
    assert scan["errors"] == []
    assert scan["warnings"] == []


def test_allowed_and_excluded_path_prefixes_are_fixed() -> None:
    scan = _load_scan()

    assert tuple(scan["allowed_path_prefixes"]) == ALLOWED_LOCAL_PREFIXES
    assert tuple(scan["excluded_path_prefixes"]) == EXPECTED_EXCLUDED_PREFIXES


def test_scan_inputs_are_local_existing_references_pending_operator_review() -> None:
    scan = _load_scan()

    assert tuple(item["input_id"] for item in scan["scan_inputs"]) == EXPECTED_SCAN_INPUT_IDS
    for item in scan["scan_inputs"]:
        assert tuple(item.keys()) == (
            "input_id",
            "local_reference",
            "observed_state",
            "operator_review_status",
        )
        assert item["operator_review_status"] == OPERATOR_REVIEW_STATUS
        _assert_allowed_existing_local_reference(item["local_reference"])


def test_scan_rows_are_fixed_closed_or_pending_records() -> None:
    scan = _load_scan()

    assert tuple(row["forbidden_action_id"] for row in scan["scan_rows"]) == EXPECTED_SCAN_ROW_IDS
    for row in scan["scan_rows"]:
        assert tuple(row.keys()) == (
            "category",
            "forbidden_action_id",
            "inspection_label",
            "local_reference",
            "observed_state",
            "operator_review_status",
            "required_state",
        )
        assert row["operator_review_status"] == OPERATOR_REVIEW_STATUS
        assert row["required_state"] in {"closed", OPERATOR_REVIEW_STATUS}
        _assert_allowed_existing_local_reference(row["local_reference"])

    assert scan["scan_rows"][-1]["required_state"] == OPERATOR_REVIEW_STATUS
    assert all(row["required_state"] == "closed" for row in scan["scan_rows"][:-1])


def test_safety_boundaries_are_closed_for_rehearsal_forbidden_action_scan() -> None:
    scan = _load_scan()

    assert scan["safety_boundaries"] == EXPECTED_SAFETY_BOUNDARIES
    assert scan["safety_boundaries"]["local_static_samples_only"] is True
    assert scan["safety_boundaries"]["operator_review_required"] is True
    assert scan["safety_boundaries"]["paper_mode_only"] is True
    assert all(value is False for key, value in scan["safety_boundaries"].items() if key.endswith("_allowed"))


def test_validation_commands_and_records_are_static_local_records() -> None:
    scan = _load_scan()

    assert scan["required_validation_commands"] == [
        "python -m compileall pm_bot tests",
        "pytest pm_bot/tests tests/test_codex_queue_pmbot_templates.py",
    ]
    assert [record["command_label"] for record in scan["validation_command_records"]] == scan[
        "required_validation_commands"
    ]
    for record in scan["validation_command_records"]:
        assert tuple(record.keys()) == (
            "command_label",
            "local_reference",
            "operator_review_status",
            "status",
            "validation_id",
        )
        assert record["operator_review_status"] == OPERATOR_REVIEW_STATUS
        assert record["status"] == "not_run_static_record"
        _assert_allowed_existing_local_reference(record["local_reference"])


def test_summary_counts_match_rehearsal_forbidden_action_scan_content() -> None:
    scan = _load_scan()
    local_references = set(_collect_values_for_key(scan, "local_reference"))

    assert scan["summary_counts"] == {
        "allowed_path_prefixes": len(scan["allowed_path_prefixes"]),
        "errors": len(scan["errors"]),
        "excluded_path_prefixes": len(scan["excluded_path_prefixes"]),
        "local_references": len(local_references),
        "required_validation_commands": len(scan["required_validation_commands"]),
        "scan_inputs": len(scan["scan_inputs"]),
        "scan_rows": len(scan["scan_rows"]),
        "scan_rows_pending_operator_review": sum(
            1 for row in scan["scan_rows"] if row["operator_review_status"] == OPERATOR_REVIEW_STATUS
        ),
        "validation_command_records": len(scan["validation_command_records"]),
        "warnings": len(scan["warnings"]),
    }


def test_fixture_has_no_decision_scoring_or_selection_terms() -> None:
    scan = _load_scan()

    assert _find_disallowed_terms(scan) == []


def test_documentation_registers_rehearsal_forbidden_action_scan_and_safety_boundary() -> None:
    document = DOC_PATH.read_text(encoding="utf-8")

    assert f"Task: `{TASK_ID}`" in document
    assert f"Scan: `{SCAN_ID}`" in document
    assert f"Contract: `{CONTRACT_VERSION}`" in document
    assert f"Run mode: `{RUN_MODE}`" in document
    assert str(FIXTURE_PATH).replace("\\", "/") in document
    assert "No network calls." in document
    assert "No OpenRouter calls." in document
    assert "No Polymarket API calls." in document
    assert "No market recommendation, forecast scoring, action guidance, or selection advice." in document
    assert "No probability, EV, edge, or confidence scoring." in document
    assert "This scan is not execution approval and is not runtime input." in document


def _load_scan() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def _assert_allowed_existing_local_reference(local_reference: str) -> None:
    assert "://" not in local_reference
    assert local_reference.startswith(ALLOWED_LOCAL_PREFIXES)
    assert Path(local_reference).exists()


def _collect_values_for_key(value: object, key: str) -> list[str]:
    matches: list[str] = []
    if isinstance(value, dict):
        for nested_key, nested_value in value.items():
            if nested_key == key:
                matches.append(str(nested_value))
            matches.extend(_collect_values_for_key(nested_value, key))
    elif isinstance(value, list):
        for nested_value in value:
            matches.extend(_collect_values_for_key(nested_value, key))
    return matches


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
            if key in {"command_label", "local_reference", "required_validation_commands"}:
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
