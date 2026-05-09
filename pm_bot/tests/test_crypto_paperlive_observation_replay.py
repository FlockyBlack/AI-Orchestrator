from __future__ import annotations

import hashlib
import json
from pathlib import Path


DOC_PATH = Path("docs/PMBOT_CRYPTO_LIVE_007_CRYPTO_PAPERLIVE_OBSERVATION_REPLAY_LOCAL_ONLY.md")
FIXTURE_PATH = Path("pm_bot/tests/fixtures/crypto_live/pmbot_crypto_paperlive_observation_replay.valid.json")
REHEARSAL_FIXTURE_PATH = Path("pm_bot/tests/fixtures/crypto_live/pmbot_crypto_paperlive_rehearsal_packet.valid.json")
LEDGER_FIXTURE_PATH = Path(
    "pm_bot/tests/fixtures/crypto_paperlive_observation_ledger/crypto_paperlive_observation_ledger.valid.json"
)
SNAPSHOT_FIXTURE_PATH = Path(
    "pm_bot/tests/fixtures/crypto_paperlive_observation_ledger/static_crypto_reference_snapshot.valid.json"
)
CAPTURE_FIXTURE_PATH = Path(
    "pm_bot/tests/fixtures/crypto_market_class_capture/crypto_market_class_capture_template.valid.json"
)
PROTOCOL_FIXTURE_PATH = Path(
    "pm_bot/tests/fixtures/crypto_operator_review_protocol/crypto_operator_review_protocol.valid.json"
)
TASK_ID = "PMBOT-CRYPTO-LIVE-007-CRYPTO-PAPERLIVE-OBSERVATION-REPLAY-LOCAL-ONLY"
REPLAY_ID = "pmbot-crypto-paperlive-observation-replay-001"
CONTRACT_VERSION = "pmbot_crypto_paperlive_observation_replay.v1"
RUN_MODE = "local_static_crypto_paperlive_observation_replay"
OPERATOR_REVIEW_STATUS = "pending_operator_review"
ALLOWED_LOCAL_PREFIXES = ("docs/", "pm_bot/readiness/", "pm_bot/tests/", "tests/")

EXPECTED_REPLAY_RECORD_FIELDS = (
    "replay_record_id",
    "source_packet_record_id",
    "source_observation_record_id",
    "source_review_record_id",
    "source_capture_record_id",
    "market_class",
    "market_slug",
    "market_title",
    "asset_symbol",
    "asset_name",
    "quote_currency",
    "metric_type",
    "deadline_utc",
    "local_rehearsal_packet_reference",
    "local_observation_fixture_reference",
    "local_snapshot_reference",
    "replay_state",
    "operator_review_status",
    "static_copy_checks",
    "value_field_policy",
)
EXPECTED_CHECK_IDS = (
    "local_replay_source_check",
    "record_chain_check",
    "descriptive_field_check",
    "value_retention_check",
    "safety_boundary_check",
    "validation_check",
)
EXPECTED_SOURCE_ARTIFACT_IDS = (
    "crypto_live_006_rehearsal_packet_doc",
    "crypto_live_006_rehearsal_packet_fixture",
    "crypto_pilot_003_observation_ledger_doc",
    "crypto_paperlive_observation_ledger_fixture",
    "static_crypto_reference_snapshot_2026_05_09_btc",
    "crypto_market_class_capture_template",
    "crypto_operator_review_protocol",
)
EXPECTED_STEP_IDS = (
    "rehearsal_packet_presence_check",
    "observation_record_presence_check",
    "static_snapshot_presence_check",
    "operator_review_record_presence_check",
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
    "threshold_comparison_output_allowed": False,
    "trade_instruction_allowed": False,
    "transaction_endpoint_calls_allowed": False,
    "value_transform_allowed": False,
    "wallet_or_signing_material_access_allowed": False,
}


def test_static_crypto_paperlive_observation_replay_fixture_has_expected_contract() -> None:
    replay = _load_replay()

    assert tuple(replay.keys()) == tuple(sorted(replay.keys()))
    assert replay["task_id"] == TASK_ID
    assert replay["replay_id"] == REPLAY_ID
    assert replay["contract_version"] == CONTRACT_VERSION
    assert replay["run_mode"] == RUN_MODE
    assert replay["created_at"] == "2026-05-09T02:30:00Z"
    assert replay["local_only"] is True
    assert replay["operator_review_required"] is True
    assert replay["operator_review"]["status"] == OPERATOR_REVIEW_STATUS
    assert replay["errors"] == []
    assert replay["warnings"] == []


def test_replay_record_fields_are_fixed_static_and_pending_review() -> None:
    replay = _load_replay()
    record = replay["observation_replay_records"][0]

    assert tuple(replay["replay_record_fields"]) == EXPECTED_REPLAY_RECORD_FIELDS
    assert tuple(record.keys()) == EXPECTED_REPLAY_RECORD_FIELDS
    assert record["replay_record_id"] == f"{REPLAY_ID}.sample.btc_threshold.replay"
    assert record["replay_state"] == "reconstructed_from_local_static_artifacts"
    assert record["operator_review_status"] == OPERATOR_REVIEW_STATUS
    assert record["value_field_policy"] == "numeric_source_values_remain_in_local_source_artifacts"


def test_replay_record_links_existing_static_crypto_records_without_values() -> None:
    replay = _load_replay()
    rehearsal = _load_json(REHEARSAL_FIXTURE_PATH)
    ledger = _load_json(LEDGER_FIXTURE_PATH)
    snapshot = _load_json(SNAPSHOT_FIXTURE_PATH)
    capture = _load_json(CAPTURE_FIXTURE_PATH)
    protocol = _load_json(PROTOCOL_FIXTURE_PATH)
    record = replay["observation_replay_records"][0]
    packet_record = rehearsal["paperlive_rehearsal_records"][0]
    observation_record = ledger["observation_records"][0]
    capture_record = capture["sample_records"][0]
    review_record = protocol["static_review_records"][0]
    serialized_replay = json.dumps(replay, sort_keys=True)

    assert record["source_packet_record_id"] == packet_record["packet_record_id"]
    assert record["source_observation_record_id"] == observation_record["record_id"]
    assert record["source_review_record_id"] == review_record["review_record_id"]
    assert record["source_capture_record_id"] == capture_record["record_id"]
    assert record["local_rehearsal_packet_reference"] == str(REHEARSAL_FIXTURE_PATH).replace("\\", "/")
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
        assert record[field] == packet_record[field]
        assert record[field] == observation_record[field]
    assert record["asset_name"] == snapshot["asset_name"]
    assert record["asset_symbol"] == snapshot["asset_symbol"]
    assert capture_record["threshold_value"] not in serialized_replay
    assert snapshot["reported_reference_value"] not in serialized_replay


def test_source_artifact_records_reference_existing_local_files_with_matching_digests() -> None:
    replay = _load_replay()

    assert tuple(record["source_artifact_id"] for record in replay["replay_source_artifacts"]) == (
        EXPECTED_SOURCE_ARTIFACT_IDS
    )
    for record in replay["replay_source_artifacts"]:
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


def test_replay_steps_checks_and_validation_commands_remain_pending() -> None:
    replay = _load_replay()

    assert tuple(step["step_id"] for step in replay["replay_steps"]) == EXPECTED_STEP_IDS
    assert tuple(check["check_id"] for check in replay["operator_review_checklist"]) == EXPECTED_CHECK_IDS
    assert all(step["operator_review_status"] == OPERATOR_REVIEW_STATUS for step in replay["replay_steps"])
    assert all(check["status"] == OPERATOR_REVIEW_STATUS for check in replay["operator_review_checklist"])
    assert replay["required_validation_commands"] == [
        "python -m compileall pm_bot tests",
        "pytest pm_bot/tests tests/test_codex_queue_pmbot_templates.py",
    ]


def test_value_replay_policy_retains_numeric_source_values_in_local_fixtures() -> None:
    replay = _load_replay()

    assert replay["field_replay_policy"] == {
        "copied_into_replay": [
            "asset_name",
            "asset_symbol",
            "deadline_utc",
            "market_class",
            "market_slug",
            "market_title",
            "metric_type",
            "quote_currency",
        ],
        "policy_id": "local_static_observation_replay_value_retention",
        "retained_in_source_artifacts": [
            "threshold_value",
            "reported_reference_value",
        ],
        "status": "active",
    }


def test_safety_boundaries_are_closed_for_crypto_observation_replay() -> None:
    replay = _load_replay()

    assert replay["safety_boundaries"] == EXPECTED_SAFETY_BOUNDARIES


def test_summary_counts_match_crypto_observation_replay_content() -> None:
    replay = _load_replay()
    local_references = set(
        _collect_values_for_key(replay, "local_reference")
        + _collect_values_for_key(replay, "local_rehearsal_packet_reference")
        + _collect_values_for_key(replay, "local_observation_fixture_reference")
        + _collect_values_for_key(replay, "local_snapshot_reference")
    )

    assert replay["summary_counts"] == {
        "local_references": len(local_references),
        "observation_replay_records": len(replay["observation_replay_records"]),
        "operator_review_checklist_items": len(replay["operator_review_checklist"]),
        "replay_source_artifacts": len(replay["replay_source_artifacts"]),
        "replay_steps": len(replay["replay_steps"]),
        "required_validation_commands": len(replay["required_validation_commands"]),
        "value_fields_retained_in_source_artifacts": len(
            replay["field_replay_policy"]["retained_in_source_artifacts"]
        ),
        "warnings": len(replay["warnings"]),
    }


def test_replay_references_only_local_static_fixture_paths() -> None:
    replay = _load_replay()
    references = sorted(
        set(
            _collect_values_for_key(replay, "local_reference")
            + _collect_values_for_key(replay, "local_rehearsal_packet_reference")
            + _collect_values_for_key(replay, "local_observation_fixture_reference")
            + _collect_values_for_key(replay, "local_snapshot_reference")
        )
    )

    assert references == [
        "docs/PMBOT_CRYPTO_LIVE_006_CRYPTO_PAPERLIVE_REHEARSAL_PACKET_LOCAL_ONLY.md",
        "docs/PMBOT_CRYPTO_PILOT_003_CRYPTO_PAPERLIVE_OBSERVATION_LEDGER_LOCAL_ONLY.md",
        str(REHEARSAL_FIXTURE_PATH).replace("\\", "/"),
        str(CAPTURE_FIXTURE_PATH).replace("\\", "/"),
        str(PROTOCOL_FIXTURE_PATH).replace("\\", "/"),
        str(LEDGER_FIXTURE_PATH).replace("\\", "/"),
        str(SNAPSHOT_FIXTURE_PATH).replace("\\", "/"),
    ]
    for reference in references:
        assert "://" not in reference
        assert reference.startswith(ALLOWED_LOCAL_PREFIXES)


def test_fixture_has_no_decision_scoring_or_selection_terms() -> None:
    replay = _load_replay()

    assert _find_disallowed_terms(replay) == []


def test_documentation_registers_crypto_observation_replay_fixture_and_safety_boundary() -> None:
    document = DOC_PATH.read_text(encoding="utf-8")

    assert f"Task: `{TASK_ID}`" in document
    assert f"Replay: `{REPLAY_ID}`" in document
    assert f"Contract: `{CONTRACT_VERSION}`" in document
    assert f"Run mode: `{RUN_MODE}`" in document
    assert str(FIXTURE_PATH).replace("\\", "/") in document
    assert str(REHEARSAL_FIXTURE_PATH).replace("\\", "/") in document
    assert str(LEDGER_FIXTURE_PATH).replace("\\", "/") in document
    assert str(SNAPSHOT_FIXTURE_PATH).replace("\\", "/") in document
    assert "No forecast scoring, action guidance, market ranking" in document
    assert "This replay is not execution approval and is not runtime input." in document


def _load_replay() -> dict:
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
                "local_rehearsal_packet_reference",
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
