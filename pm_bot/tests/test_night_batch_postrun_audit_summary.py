from __future__ import annotations

import json
from pathlib import Path


DOC_PATH = Path("docs/PMBOT_SAFETY_002_NIGHT_BATCH_POSTRUN_AUDIT_SUMMARY_LOCAL_ONLY.md")
FIXTURE_PATH = Path("pm_bot/tests/fixtures/safety/night_batch_postrun_audit_summary.valid.json")
TASK_ID = "PMBOT-SAFETY-002-NIGHT-BATCH-POSTRUN-AUDIT-SUMMARY-LOCAL-ONLY"
CONTRACT_VERSION = "pmbot_night_batch_postrun_audit_summary.v1"
RUN_MODE = "local_static_night_batch_postrun_audit_summary"
SUMMARY_ID = "pmbot_night_batch_postrun_audit_summary_001"
OPERATOR_REVIEW_STATUS = "pending_operator_review"

EXPECTED_AUDIT_RECORD_IDS = (
    "night_batch_task_inventory",
    "batch_runner_guardrail_record",
    "postprocess_summary_contract",
    "result_packet_shape",
    "safety_gate_carryover",
    "validation_command_record",
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

ALLOWED_LOCAL_PREFIXES = ("docs/", "pm_bot/tests/", "tests/")


def test_static_night_batch_postrun_audit_summary_fixture_has_expected_contract() -> None:
    summary = _load_summary()

    assert tuple(summary.keys()) == tuple(sorted(summary.keys()))
    assert summary["task_id"] == TASK_ID
    assert summary["summary_id"] == SUMMARY_ID
    assert summary["contract_version"] == CONTRACT_VERSION
    assert summary["run_mode"] == RUN_MODE
    assert summary["created_at"] == "2026-05-09T00:00:00Z"
    assert summary["local_only"] is True
    assert summary["operator_review_required"] is True
    assert summary["operator_review"]["status"] == OPERATOR_REVIEW_STATUS
    assert summary["errors"] == []
    assert summary["warnings"] == []


def test_audit_records_are_fixed_local_and_pending_operator_review() -> None:
    summary = _load_summary()

    assert tuple(record["audit_record_id"] for record in summary["audit_records"]) == EXPECTED_AUDIT_RECORD_IDS
    for record in summary["audit_records"]:
        assert set(record) == {
            "audit_record_id",
            "inspection_label",
            "local_reference",
            "observed_state",
            "operator_review_status",
            "record_type",
        }
        assert record["operator_review_status"] == OPERATOR_REVIEW_STATUS
        assert "://" not in record["local_reference"]
        assert record["local_reference"].startswith(ALLOWED_LOCAL_PREFIXES)


def test_source_batch_is_local_static_and_operator_review_scoped() -> None:
    summary = _load_summary()

    assert summary["source_batch"] == {
        "batch_label": "pmbot-night-batch-postrun-static-record-set",
        "local_reference": "docs/CODEX_CLI_BATCH_RUNNER_NIGHT_MODE.md",
        "record_scope": "night_batch_postrun_records",
        "run_identifier": "2026-05-09-local-night-batch-postrun-audit",
        "run_state": "records_ready_for_operator_review",
    }
    assert summary["source_batch"]["local_reference"].startswith(ALLOWED_LOCAL_PREFIXES)


def test_safety_boundaries_are_closed_for_night_batch_postrun_audit_summary() -> None:
    summary = _load_summary()

    assert summary["safety_boundaries"] == EXPECTED_SAFETY_BOUNDARIES


def test_validation_commands_are_recorded_for_operator_run_local_checks() -> None:
    summary = _load_summary()

    assert summary["required_validation_commands"] == [
        "python -m compileall pm_bot tests",
        "pytest pm_bot/tests tests/test_codex_queue_pmbot_templates.py",
    ]


def test_summary_counts_match_audit_content() -> None:
    summary = _load_summary()
    audit_records = summary["audit_records"]
    local_references = {summary["source_batch"]["local_reference"]}
    local_references.update(record["local_reference"] for record in audit_records)

    assert summary["summary_counts"] == {
        "audit_records": len(audit_records),
        "audit_records_pending_operator_review": sum(
            1 for record in audit_records if record["operator_review_status"] == OPERATOR_REVIEW_STATUS
        ),
        "local_references": len(local_references),
        "required_validation_commands": len(summary["required_validation_commands"]),
        "warnings": len(summary["warnings"]),
    }


def test_fixture_has_no_guidance_scoring_or_selection_terms() -> None:
    summary = _load_summary()

    assert _find_disallowed_terms(summary) == []


def test_documentation_registers_postrun_audit_fixture_and_safety_boundary() -> None:
    document = DOC_PATH.read_text(encoding="utf-8")

    assert f"Task: `{TASK_ID}`" in document
    assert "Summary: `pmbot-night-batch-postrun-audit-summary`" in document
    assert f"Contract: `{CONTRACT_VERSION}`" in document
    assert str(FIXTURE_PATH).replace("\\", "/") in document
    assert "No forecast scoring, action guidance, or selection advice." in document
    assert "This summary is not execution approval and is not runtime input." in document


def _load_summary() -> dict:
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
