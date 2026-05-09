from __future__ import annotations

import json
from pathlib import Path


DOC_PATH = Path("docs/PMBOT_SAFETY_006_AUTONOMY_REVIEW_RECORD_LOCAL_ONLY.md")
FIXTURE_PATH = Path("pm_bot/tests/fixtures/safety/autonomy_review_record.valid.json")
TASK_ID = "PMBOT-SAFETY-006-AUTONOMY-REVIEW-RECORD-LOCAL-ONLY"
CONTRACT_VERSION = "pmbot_autonomy_review_record.v1"
RUN_MODE = "local_static_autonomy_review_record"
RECORD_ID = "pmbot_autonomy_review_record_001"
RECORD_NAME = "pmbot-autonomy-review-record"
OPERATOR_REVIEW_STATUS = "pending_operator_review"

EXPECTED_ALLOWED_PREFIXES = (
    "docs/",
    "pm_bot/tests/",
    "tests/",
)
EXPECTED_INPUT_IDS = (
    "queue_template_safety_contract",
    "autonomy_gate_checklist",
    "night_batch_postrun_audit_summary",
    "forbidden_action_scan",
    "sensitive_path_exclusion_audit",
    "forbidden_language_regression_suite",
    "static_review_record_fixture",
)
EXPECTED_ITEM_IDS = (
    "allowed_path_scope",
    "source_basis",
    "prior_safety_records",
    "endpoint_boundary",
    "sensitive_path_boundary",
    "language_boundary",
    "validation_commands",
    "operator_status",
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
    "market_instruction_output_allowed": False,
    "network_calls_allowed": False,
    "operator_review_required": True,
    "order_or_trade_surface_changes_allowed": False,
    "paper_mode_only": True,
    "runtime_or_dispatcher_changes_allowed": False,
    "scheduler_or_worker_allowed": False,
    "sensitive_path_access_allowed": False,
    "timed_automation_allowed": False,
    "transaction_endpoint_calls_allowed": False,
    "wallet_or_signing_material_access_allowed": False,
}


def test_static_autonomy_review_record_fixture_has_expected_contract() -> None:
    record = _load_record()

    assert tuple(record.keys()) == tuple(sorted(record.keys()))
    assert record["task_id"] == TASK_ID
    assert record["record_id"] == RECORD_ID
    assert record["record_name"] == RECORD_NAME
    assert record["contract_version"] == CONTRACT_VERSION
    assert record["run_mode"] == RUN_MODE
    assert record["created_at"] == "2026-05-09T04:00:00Z"
    assert record["local_only"] is True
    assert record["operator_review_required"] is True
    assert record["operator_review"] == {
        "reviewed_at": None,
        "reviewed_by": None,
        "status": OPERATOR_REVIEW_STATUS,
    }
    assert record["errors"] == []
    assert record["warnings"] == []


def test_review_inputs_are_fixed_local_allowed_references() -> None:
    record = _load_record()

    assert tuple(record["allowed_path_prefixes"]) == EXPECTED_ALLOWED_PREFIXES
    assert tuple(item["input_id"] for item in record["review_inputs"]) == EXPECTED_INPUT_IDS
    for item in record["review_inputs"]:
        assert set(item) == {
            "input_id",
            "local_reference",
            "observed_state",
            "operator_review_status",
        }
        assert item["operator_review_status"] == OPERATOR_REVIEW_STATUS
        _assert_allowed_existing_local_reference(item["local_reference"])


def test_review_items_are_fixed_local_and_pending_operator_review() -> None:
    record = _load_record()

    assert tuple(item["item_id"] for item in record["review_items"]) == EXPECTED_ITEM_IDS
    for item in record["review_items"]:
        assert set(item) == {
            "item_id",
            "local_reference",
            "operator_review_status",
            "review_label",
            "review_state",
        }
        assert item["operator_review_status"] == OPERATOR_REVIEW_STATUS
        _assert_allowed_existing_local_reference(item["local_reference"])


def test_safety_boundaries_close_autonomy_review_record_surfaces() -> None:
    record = _load_record()

    assert record["safety_boundaries"] == EXPECTED_SAFETY_BOUNDARIES
    assert record["safety_boundaries"]["local_static_samples_only"] is True
    assert record["safety_boundaries"]["operator_review_required"] is True
    assert record["safety_boundaries"]["paper_mode_only"] is True
    assert all(value is False for key, value in record["safety_boundaries"].items() if key.endswith("_allowed"))


def test_validation_commands_are_recorded_for_operator_run_local_checks() -> None:
    record = _load_record()

    assert record["required_validation_commands"] == [
        "python -m compileall pm_bot tests",
        "pytest pm_bot/tests tests/test_codex_queue_pmbot_templates.py",
    ]


def test_summary_counts_match_autonomy_review_record_content() -> None:
    record = _load_record()
    local_references = {
        *(item["local_reference"] for item in record["review_inputs"]),
        *(item["local_reference"] for item in record["review_items"]),
    }

    assert record["summary_counts"] == {
        "allowed_path_prefixes": len(record["allowed_path_prefixes"]),
        "errors": len(record["errors"]),
        "local_references": len(local_references),
        "required_validation_commands": len(record["required_validation_commands"]),
        "review_inputs": len(record["review_inputs"]),
        "review_items": len(record["review_items"]),
        "review_items_pending_operator_review": sum(
            1 for item in record["review_items"] if item["operator_review_status"] == OPERATOR_REVIEW_STATUS
        ),
        "warnings": len(record["warnings"]),
    }


def test_fixture_has_no_guidance_scoring_or_selection_terms() -> None:
    record = _load_record()

    assert _find_disallowed_terms(record) == []


def test_documentation_registers_autonomy_review_record_and_safety_boundary() -> None:
    document = DOC_PATH.read_text(encoding="utf-8")

    assert f"Task: `{TASK_ID}`" in document
    assert f"Record: `{RECORD_NAME}`" in document
    assert f"Contract: `{CONTRACT_VERSION}`" in document
    assert f"Run mode: `{RUN_MODE}`" in document
    assert str(FIXTURE_PATH).replace("\\", "/") in document
    assert "No forecast scoring, action guidance, or selection advice." in document
    assert "This record is not execution approval and is not runtime input." in document


def _load_record() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def _assert_allowed_existing_local_reference(local_reference: str) -> None:
    assert "://" not in local_reference
    assert local_reference.startswith(EXPECTED_ALLOWED_PREFIXES)
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
