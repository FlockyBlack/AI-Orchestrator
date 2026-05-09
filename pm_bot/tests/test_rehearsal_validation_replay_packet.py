from __future__ import annotations

import json
from pathlib import Path


DOC_PATH = Path("docs/PMBOT_REHEARSAL_009_REHEARSAL_VALIDATION_REPLAY_PACKET_LOCAL_ONLY.md")
FIXTURE_PATH = Path("pm_bot/tests/fixtures/rehearsal/pmbot_rehearsal_validation_replay_packet.valid.json")

TASK_ID = "PMBOT-REHEARSAL-009-REHEARSAL-VALIDATION-REPLAY-PACKET-LOCAL-ONLY"
CONTRACT_ID = "pmbot-rehearsal-validation-replay-packet"
CONTRACT_VERSION = "pmbot_rehearsal_validation_replay_packet.v1"
PACKET_ID = "pmbot-rehearsal-validation-replay-packet-001"
PACKET_NAME = "pmbot-rehearsal-validation-replay-packet"
RUN_MODE = "local_static_rehearsal_validation_replay_packet"
OPERATOR_REVIEW_STATUS = "pending_operator_review"
ALLOWED_LOCAL_PREFIXES = ("docs/", "pm_bot/readiness/", "pm_bot/simulated_decisions/", "pm_bot/tests/", "tests/")

EXPECTED_RECORD_FIELDS = (
    "artifact_id",
    "artifact_role",
    "artifact_type",
    "contract_version",
    "expected_state",
    "local_reference",
    "operator_review_status",
    "record_id",
    "record_label",
    "source_task_id",
)
EXPECTED_RECORD_IDS = (
    "rehearsal_validation_replay_packet_001.packet_fixture",
    "rehearsal_validation_replay_packet_001.packet_document",
    "rehearsal_validation_replay_packet_001.rehearsal_scenario_contract_fixture",
    "rehearsal_validation_replay_packet_001.rehearsal_market_packet_fixture",
    "rehearsal_validation_replay_packet_001.rehearsal_source_evidence_fixture",
    "rehearsal_validation_replay_packet_001.rehearsal_operator_record_fixture",
    "rehearsal_validation_replay_packet_001.rehearsal_stop_condition_fixture",
    "rehearsal_validation_replay_packet_001.rehearsal_staleness_fixture",
    "rehearsal_validation_replay_packet_001.rehearsal_contradiction_fixture",
    "rehearsal_validation_replay_packet_001.rehearsal_retention_ledger_fixture",
    "rehearsal_validation_replay_packet_001.queue_template_validation_test",
    "rehearsal_validation_replay_packet_001.packet_contract_test",
)
EXPECTED_SECTION_IDS = (
    "packet_identity_replay",
    "prior_rehearsal_control_replay",
    "prior_rehearsal_case_replay",
    "retention_and_validation_replay",
    "validation_command_replay",
)
EXPECTED_CHECK_IDS = (
    "local_reference_replay",
    "prior_rehearsal_state_replay",
    "static_fixture_replay",
    "retention_record_replay",
    "validation_command_replay",
    "closed_boundary_replay",
    "human_review_replay",
)
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
EXPECTED_LOCAL_REFERENCES = (
    "docs/PMBOT_REHEARSAL_009_REHEARSAL_VALIDATION_REPLAY_PACKET_LOCAL_ONLY.md",
    "pm_bot/tests/fixtures/rehearsal/pmbot_read_only_rehearsal_scenario_contract.valid.json",
    "pm_bot/tests/fixtures/rehearsal/pmbot_rehearsal_contradiction_case_set.valid.json",
    "pm_bot/tests/fixtures/rehearsal/pmbot_rehearsal_evidence_retention_ledger.valid.json",
    "pm_bot/tests/fixtures/rehearsal/pmbot_rehearsal_market_packet_schema.valid.json",
    "pm_bot/tests/fixtures/rehearsal/pmbot_rehearsal_operator_approval_record.valid.json",
    "pm_bot/tests/fixtures/rehearsal/pmbot_rehearsal_source_evidence_bundle.valid.json",
    "pm_bot/tests/fixtures/rehearsal/pmbot_rehearsal_staleness_case_set.valid.json",
    "pm_bot/tests/fixtures/rehearsal/pmbot_rehearsal_stop_condition_trigger_matrix.valid.json",
    "pm_bot/tests/fixtures/rehearsal/pmbot_rehearsal_validation_replay_packet.valid.json",
    "pm_bot/tests/test_rehearsal_validation_replay_packet.py",
    "tests/test_codex_queue_pmbot_templates.py",
)
EXPECTED_SAFETY_BOUNDARIES = {
    "authenticated_endpoint_calls_allowed": False,
    "background_process_allowed": False,
    "browser_automation_allowed": False,
    "credential_or_secret_access_allowed": False,
    "execution_endpoint_calls_allowed": False,
    "external_service_calls_allowed": False,
    "llm_provider_calls_allowed": False,
    "local_fixtures_only": True,
    "local_static_samples_only": True,
    "market_api_calls_allowed": False,
    "market_instruction_allowed": False,
    "market_ranking_allowed": False,
    "network_calls_allowed": False,
    "numeric_prediction_metric_allowed": False,
    "openrouter_calls_allowed": False,
    "operator_review_required": True,
    "order_or_trade_surface_changes_allowed": False,
    "paper_mode_only": True,
    "polymarket_api_calls_allowed": False,
    "replay_mutates_source_artifacts_allowed": False,
    "run_codex_changes_allowed": False,
    "runtime_or_dispatcher_changes_allowed": False,
    "scheduler_or_worker_allowed": False,
    "sensitive_path_access_allowed": False,
    "timed_automation_allowed": False,
    "transaction_endpoint_calls_allowed": False,
    "wallet_or_signing_material_access_allowed": False,
}


def test_static_rehearsal_validation_replay_packet_fixture_has_expected_contract() -> None:
    packet = _load_packet()

    assert tuple(packet.keys()) == tuple(sorted(packet.keys()))
    assert packet["task_id"] == TASK_ID
    assert packet["contract_id"] == CONTRACT_ID
    assert packet["contract_version"] == CONTRACT_VERSION
    assert packet["packet_id"] == PACKET_ID
    assert packet["packet_name"] == PACKET_NAME
    assert packet["run_mode"] == RUN_MODE
    assert packet["created_at"] == "2026-05-09T06:00:00Z"
    assert packet["local_only"] is True
    assert packet["operator_review_required"] is True
    assert packet["operator_review"] == {
        "reviewed_at": None,
        "reviewed_by": None,
        "status": OPERATOR_REVIEW_STATUS,
    }
    assert packet["errors"] == []
    assert packet["warnings"] == []


def test_replay_records_are_fixed_local_and_pending_operator_review() -> None:
    packet = _load_packet()

    assert tuple(packet["replay_record_fields"]) == EXPECTED_RECORD_FIELDS
    assert tuple(record["record_id"] for record in packet["replay_records"]) == EXPECTED_RECORD_IDS
    for record in packet["replay_records"]:
        assert tuple(record.keys()) == EXPECTED_RECORD_FIELDS
        assert record["operator_review_status"] == OPERATOR_REVIEW_STATUS
        assert record["expected_state"] in {"local_validation_reference", OPERATOR_REVIEW_STATUS}
        assert record["source_task_id"]
        _assert_allowed_existing_local_reference(record["local_reference"])


def test_prior_rehearsal_fixture_review_states_remain_pending() -> None:
    packet = _load_packet()

    fixture_references = sorted(
        {
            record["local_reference"]
            for record in packet["replay_records"]
            if record["local_reference"].startswith("pm_bot/tests/fixtures/rehearsal/")
            and record["local_reference"] != str(FIXTURE_PATH).replace("\\", "/")
        }
    )
    assert len(fixture_references) == 8
    for reference in fixture_references:
        fixture = _load_json(Path(reference))
        assert fixture["operator_review"] == {
            "reviewed_at": None,
            "reviewed_by": None,
            "status": OPERATOR_REVIEW_STATUS,
        }


def test_replay_sections_reference_declared_records() -> None:
    packet = _load_packet()
    record_ids = {record["record_id"] for record in packet["replay_records"]}

    assert tuple(section["section_id"] for section in packet["replay_sections"]) == EXPECTED_SECTION_IDS
    for section in packet["replay_sections"]:
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


def test_replay_checklist_and_validation_command_records_remain_pending() -> None:
    packet = _load_packet()

    assert tuple(check["check_id"] for check in packet["replay_checklist"]) == EXPECTED_CHECK_IDS
    for check in packet["replay_checklist"]:
        assert tuple(check.keys()) == tuple(sorted(check.keys()))
        assert set(check) == {"check_id", "description", "required_evidence", "status"}
        assert check["status"] == OPERATOR_REVIEW_STATUS

    assert packet["required_validation_commands"] == [
        "python -m compileall pm_bot tests",
        "pytest pm_bot/tests tests/test_codex_queue_pmbot_templates.py",
    ]
    assert [record["command_label"] for record in packet["validation_command_records"]] == packet[
        "required_validation_commands"
    ]
    for record in packet["validation_command_records"]:
        assert tuple(record.keys()) == tuple(sorted(record.keys()))
        assert record["operator_review_status"] == OPERATOR_REVIEW_STATUS
        assert record["status"] == "not_run_static_record"
        _assert_allowed_existing_local_reference(record["local_reference"])


def test_excluded_prefixes_match_sensitive_and_execution_boundaries() -> None:
    packet = _load_packet()

    assert tuple(packet["excluded_path_prefixes"]) == EXPECTED_EXCLUDED_PREFIXES


def test_safety_boundaries_are_closed_for_rehearsal_validation_replay_packet() -> None:
    packet = _load_packet()

    assert packet["safety_boundaries"] == EXPECTED_SAFETY_BOUNDARIES
    assert packet["safety_boundaries"]["local_fixtures_only"] is True
    assert packet["safety_boundaries"]["local_static_samples_only"] is True
    assert packet["safety_boundaries"]["operator_review_required"] is True
    assert packet["safety_boundaries"]["paper_mode_only"] is True
    assert all(value is False for key, value in packet["safety_boundaries"].items() if key.endswith("_allowed"))


def test_summary_counts_match_rehearsal_validation_replay_packet_content() -> None:
    packet = _load_packet()
    local_references = {record["local_reference"] for record in packet["replay_records"]}
    local_references.update(record["local_reference"] for record in packet["validation_command_records"])

    assert packet["summary_counts"] == {
        "errors": len(packet["errors"]),
        "excluded_path_prefixes": len(packet["excluded_path_prefixes"]),
        "local_references": len(local_references),
        "replay_checklist_items": len(packet["replay_checklist"]),
        "replay_records": len(packet["replay_records"]),
        "replay_records_pending_operator_review": sum(
            1 for record in packet["replay_records"] if record["operator_review_status"] == OPERATOR_REVIEW_STATUS
        ),
        "replay_sections": len(packet["replay_sections"]),
        "replay_sections_pending_operator_review": sum(
            1 for section in packet["replay_sections"] if section["operator_review_status"] == OPERATOR_REVIEW_STATUS
        ),
        "required_validation_commands": len(packet["required_validation_commands"]),
        "validation_command_records": len(packet["validation_command_records"]),
        "warnings": len(packet["warnings"]),
    }


def test_fixture_references_only_allowed_local_static_material() -> None:
    packet = _load_packet()
    references = sorted({record["local_reference"] for record in packet["replay_records"]})

    assert references == sorted(EXPECTED_LOCAL_REFERENCES)
    for reference in references:
        _assert_allowed_existing_local_reference(reference)


def test_fixture_has_no_decision_scoring_or_selection_terms() -> None:
    packet = _load_packet()

    assert _find_disallowed_terms(packet) == []


def test_documentation_registers_rehearsal_validation_replay_packet_and_safety_boundary() -> None:
    document = DOC_PATH.read_text(encoding="utf-8")

    assert f"Task: `{TASK_ID}`" in document
    assert f"Packet: `{PACKET_ID}`" in document
    assert f"Contract: `{CONTRACT_VERSION}`" in document
    assert f"Run mode: `{RUN_MODE}`" in document
    assert str(FIXTURE_PATH).replace("\\", "/") in document
    assert "No forecast scoring, action guidance, market ranking" in document
    assert "No probability, EV, edge, or confidence scoring." in document
    assert "This packet is not execution approval and is not runtime input." in document


def _load_packet() -> dict:
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
            if key in {
                "excluded_path_prefixes",
                "local_reference",
                "required_validation_commands",
            }:
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
