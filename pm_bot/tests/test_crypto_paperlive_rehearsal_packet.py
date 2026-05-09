from __future__ import annotations

import hashlib
import json
from pathlib import Path


DOC_PATH = Path("docs/PMBOT_CRYPTO_LIVE_006_CRYPTO_PAPERLIVE_REHEARSAL_PACKET_LOCAL_ONLY.md")
FIXTURE_PATH = Path("pm_bot/tests/fixtures/crypto_live/pmbot_crypto_paperlive_rehearsal_packet.valid.json")
CAPTURE_FIXTURE_PATH = Path(
    "pm_bot/tests/fixtures/crypto_market_class_capture/crypto_market_class_capture_template.valid.json"
)
PROTOCOL_FIXTURE_PATH = Path(
    "pm_bot/tests/fixtures/crypto_operator_review_protocol/crypto_operator_review_protocol.valid.json"
)
LEDGER_FIXTURE_PATH = Path(
    "pm_bot/tests/fixtures/crypto_paperlive_observation_ledger/crypto_paperlive_observation_ledger.valid.json"
)
SNAPSHOT_FIXTURE_PATH = Path(
    "pm_bot/tests/fixtures/crypto_paperlive_observation_ledger/static_crypto_reference_snapshot.valid.json"
)
TASK_ID = "PMBOT-CRYPTO-LIVE-006-CRYPTO-PAPERLIVE-REHEARSAL-PACKET-LOCAL-ONLY"
PACKET_ID = "pmbot-crypto-paperlive-rehearsal-packet-001"
CONTRACT_VERSION = "pmbot_crypto_paperlive_rehearsal_packet.v1"
RUN_MODE = "local_static_crypto_paperlive_rehearsal_packet"
OPERATOR_REVIEW_STATUS = "pending_operator_review"
ALLOWED_LOCAL_PREFIXES = ("docs/", "pm_bot/readiness/", "pm_bot/tests/", "tests/")

EXPECTED_PACKET_RECORD_FIELDS = (
    "asset_name",
    "asset_symbol",
    "deadline_utc",
    "local_observation_fixture_reference",
    "local_snapshot_reference",
    "market_class",
    "market_slug",
    "market_title",
    "metric_type",
    "observation_record_id",
    "operator_review_status",
    "packet_record_id",
    "packet_state",
    "quote_currency",
    "reference_field_policy",
    "source_capture_record_id",
    "source_review_record_id",
    "static_copy_checks",
    "value_fields_retained_in_source_artifacts",
)
EXPECTED_CHECK_IDS = (
    "local_reference_check",
    "source_record_presence_check",
    "static_copy_check",
    "value_retention_check",
    "safety_boundary_check",
    "validation_check",
)
EXPECTED_SOURCE_ARTIFACT_IDS = (
    "crypto_live_001_read_only_contract_doc",
    "crypto_live_002_data_source_inventory_doc",
    "crypto_live_003_source_evidence_link_map_doc",
    "crypto_live_004_source_staleness_check_spec_doc",
    "crypto_live_005_source_contradiction_ledger_doc",
    "read_only_crypto_data_contract_fixture",
    "crypto_live_data_source_inventory_fixture",
    "crypto_market_class_capture_template",
    "crypto_operator_review_protocol",
    "crypto_paperlive_observation_ledger",
    "static_crypto_reference_snapshot_2026_05_09_btc",
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
    "paper_mode_only": True,
    "paperlive_execution_allowed": False,
    "runtime_or_dispatcher_changes_allowed": False,
    "scheduler_or_worker_allowed": False,
    "threshold_comparison_allowed": False,
    "trade_instruction_allowed": False,
    "transaction_endpoint_calls_allowed": False,
    "value_transform_allowed": False,
    "wallet_or_signing_material_access_allowed": False,
}


def test_static_crypto_paperlive_rehearsal_packet_fixture_has_expected_contract() -> None:
    packet = _load_packet()

    assert tuple(packet.keys()) == tuple(sorted(packet.keys()))
    assert packet["task_id"] == TASK_ID
    assert packet["packet_id"] == PACKET_ID
    assert packet["contract_version"] == CONTRACT_VERSION
    assert packet["run_mode"] == RUN_MODE
    assert packet["created_at"] == "2026-05-09T01:50:00Z"
    assert packet["local_only"] is True
    assert packet["operator_review_required"] is True
    assert packet["operator_review"]["status"] == OPERATOR_REVIEW_STATUS
    assert packet["errors"] == []
    assert packet["warnings"] == []


def test_packet_record_fields_are_fixed_static_and_pending_review() -> None:
    packet = _load_packet()
    record = packet["paperlive_rehearsal_records"][0]

    assert tuple(packet["packet_record_fields"]) == EXPECTED_PACKET_RECORD_FIELDS
    assert tuple(record.keys()) == EXPECTED_PACKET_RECORD_FIELDS
    assert record["packet_record_id"] == f"{PACKET_ID}.sample.btc_threshold.rehearsal"
    assert record["packet_state"] == "packet_only_static_sample"
    assert record["operator_review_status"] == OPERATOR_REVIEW_STATUS
    assert record["reference_field_policy"] == "numeric_source_values_retained_in_local_fixtures"
    assert record["value_fields_retained_in_source_artifacts"] == [
        "threshold_value",
        "reported_reference_value",
    ]


def test_rehearsal_record_links_existing_static_crypto_source_records_without_values() -> None:
    packet = _load_packet()
    capture = _load_json(CAPTURE_FIXTURE_PATH)
    protocol = _load_json(PROTOCOL_FIXTURE_PATH)
    ledger = _load_json(LEDGER_FIXTURE_PATH)
    snapshot = _load_json(SNAPSHOT_FIXTURE_PATH)
    record = packet["paperlive_rehearsal_records"][0]
    capture_record = capture["sample_records"][0]
    review_record = protocol["static_review_records"][0]
    observation_record = ledger["observation_records"][0]
    serialized_packet = json.dumps(packet, sort_keys=True)

    assert record["source_capture_record_id"] == capture_record["record_id"]
    assert record["source_review_record_id"] == review_record["review_record_id"]
    assert record["observation_record_id"] == observation_record["record_id"]
    assert record["local_observation_fixture_reference"] == str(LEDGER_FIXTURE_PATH).replace("\\", "/")
    assert record["local_snapshot_reference"] == str(SNAPSHOT_FIXTURE_PATH).replace("\\", "/")
    for field in (
        "asset_name",
        "asset_symbol",
        "deadline_utc",
        "market_class",
        "market_slug",
        "market_title",
        "metric_type",
        "quote_currency",
    ):
        assert record[field] == observation_record[field]
        assert record[field] == review_record[field]
    assert record["asset_name"] == snapshot["asset_name"]
    assert record["asset_symbol"] == snapshot["asset_symbol"]
    assert record["metric_type"] == snapshot["metric_type"]
    assert capture_record["threshold_value"] not in serialized_packet
    assert snapshot["reported_reference_value"] not in serialized_packet


def test_source_artifact_records_reference_existing_local_files_with_matching_digests() -> None:
    packet = _load_packet()

    assert tuple(record["source_artifact_id"] for record in packet["source_artifact_records"]) == (
        EXPECTED_SOURCE_ARTIFACT_IDS
    )
    for record in packet["source_artifact_records"]:
        path = Path(record["local_reference"])
        data = path.read_bytes()

        assert set(record) == {
            "artifact_kind",
            "content_byte_count",
            "content_sha256",
            "contract_version",
            "local_reference",
            "operator_review_status",
            "required_state",
            "selected_record_id",
            "source_artifact_id",
        }
        assert record["operator_review_status"] == OPERATOR_REVIEW_STATUS
        assert "://" not in record["local_reference"]
        assert record["local_reference"].startswith(ALLOWED_LOCAL_PREFIXES)
        assert path.exists()
        assert record["content_byte_count"] == len(data)
        assert record["content_sha256"] == hashlib.sha256(data).hexdigest()


def test_operator_review_sections_checks_and_validation_commands_remain_pending() -> None:
    packet = _load_packet()

    assert tuple(check["check_id"] for check in packet["operator_review_checklist"]) == EXPECTED_CHECK_IDS
    assert all(check["status"] == OPERATOR_REVIEW_STATUS for check in packet["operator_review_checklist"])
    assert all(section["operator_review_status"] == OPERATOR_REVIEW_STATUS for section in packet["review_sections"])
    assert packet["required_validation_commands"] == [
        "python -m compileall pm_bot tests",
        "pytest pm_bot/tests tests/test_codex_queue_pmbot_templates.py",
    ]


def test_value_copy_policy_retains_numeric_source_values_in_local_fixtures() -> None:
    packet = _load_packet()

    assert packet["value_copy_policy"] == {
        "copied_into_packet": [
            "asset_name",
            "asset_symbol",
            "deadline_utc",
            "market_class",
            "market_slug",
            "market_title",
            "metric_type",
            "quote_currency",
        ],
        "policy_id": "local_fixture_value_retention",
        "retained_in_source_artifacts": [
            "threshold_value",
            "reported_reference_value",
        ],
        "status": "active",
    }


def test_safety_boundaries_are_closed_for_crypto_rehearsal_packet() -> None:
    packet = _load_packet()

    assert packet["safety_boundaries"] == EXPECTED_SAFETY_BOUNDARIES


def test_summary_counts_match_crypto_rehearsal_packet_content() -> None:
    packet = _load_packet()
    local_references = set(
        _collect_values_for_key(packet, "local_reference")
        + _collect_values_for_key(packet, "local_observation_fixture_reference")
        + _collect_values_for_key(packet, "local_snapshot_reference")
    )

    assert packet["summary_counts"] == {
        "local_references": len(local_references),
        "operator_review_checklist_items": len(packet["operator_review_checklist"]),
        "packet_records": len(packet["paperlive_rehearsal_records"]),
        "required_validation_commands": len(packet["required_validation_commands"]),
        "review_sections": len(packet["review_sections"]),
        "source_artifact_records": len(packet["source_artifact_records"]),
        "value_fields_retained_in_source_artifacts": len(
            packet["value_copy_policy"]["retained_in_source_artifacts"]
        ),
        "warnings": len(packet["warnings"]),
    }


def test_fixture_has_no_decision_scoring_or_selection_terms() -> None:
    packet = _load_packet()

    assert _find_disallowed_terms(packet) == []


def test_documentation_registers_crypto_rehearsal_packet_fixture_and_safety_boundary() -> None:
    document = DOC_PATH.read_text(encoding="utf-8")

    assert f"Task: `{TASK_ID}`" in document
    assert f"Packet: `{PACKET_ID}`" in document
    assert f"Contract: `{CONTRACT_VERSION}`" in document
    assert f"Run mode: `{RUN_MODE}`" in document
    assert str(FIXTURE_PATH).replace("\\", "/") in document
    assert str(LEDGER_FIXTURE_PATH).replace("\\", "/") in document
    assert str(SNAPSHOT_FIXTURE_PATH).replace("\\", "/") in document
    assert "No forecast scoring, action guidance, market ranking" in document
    assert "This packet is not execution approval and is not runtime input." in document


def _load_packet() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


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
            if key in {
                "local_reference",
                "local_observation_fixture_reference",
                "local_snapshot_reference",
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
