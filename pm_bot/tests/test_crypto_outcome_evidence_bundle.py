from __future__ import annotations

import hashlib
import json
from pathlib import Path


DOC_PATH = Path("docs/PMBOT_CRYPTO_LIVE_008_CRYPTO_OUTCOME_EVIDENCE_BUNDLE_LOCAL_ONLY.md")
FIXTURE_PATH = Path("pm_bot/tests/fixtures/crypto_live/pmbot_crypto_outcome_evidence_bundle.valid.json")
REPLAY_FIXTURE_PATH = Path("pm_bot/tests/fixtures/crypto_live/pmbot_crypto_paperlive_observation_replay.valid.json")
REHEARSAL_FIXTURE_PATH = Path("pm_bot/tests/fixtures/crypto_live/pmbot_crypto_paperlive_rehearsal_packet.valid.json")
LEDGER_FIXTURE_PATH = Path(
    "pm_bot/tests/fixtures/crypto_paperlive_observation_ledger/crypto_paperlive_observation_ledger.valid.json"
)
SNAPSHOT_FIXTURE_PATH = Path(
    "pm_bot/tests/fixtures/crypto_paperlive_observation_ledger/static_crypto_reference_snapshot.valid.json"
)
TASK_ID = "PMBOT-CRYPTO-LIVE-008-CRYPTO-OUTCOME-EVIDENCE-BUNDLE-LOCAL-ONLY"
BUNDLE_ID = "pmbot-crypto-outcome-evidence-bundle-001"
CONTRACT_VERSION = "pmbot_crypto_outcome_evidence_bundle.v1"
RUN_MODE = "local_static_crypto_outcome_evidence_bundle"
OPERATOR_REVIEW_STATUS = "pending_operator_review"
ALLOWED_LOCAL_PREFIXES = ("docs/", "pm_bot/readiness/", "pm_bot/source_quality/", "pm_bot/tests/", "tests/")

EXPECTED_EVIDENCE_RECORD_FIELDS = (
    "record_id",
    "source_replay_record_id",
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
    "local_replay_fixture_reference",
    "local_rehearsal_packet_reference",
    "local_observation_fixture_reference",
    "local_snapshot_reference",
    "evidence_state",
    "operator_review_status",
    "static_copy_checks",
    "value_field_policy",
)
EXPECTED_SECTION_IDS = (
    "observation_replay_evidence",
    "paperlive_rehearsal_evidence",
    "observation_source_evidence",
    "source_quality_evidence",
    "validation_evidence",
)
EXPECTED_CHECK_IDS = (
    "local_reference_digest_check",
    "record_chain_check",
    "descriptive_field_check",
    "value_retention_check",
    "unresolved_outcome_state_check",
    "safety_boundary_check",
    "validation_check",
)
EXPECTED_SOURCE_ARTIFACT_IDS = (
    "crypto_live_007_observation_replay_doc",
    "crypto_live_007_observation_replay_fixture",
    "crypto_live_006_rehearsal_packet_doc",
    "crypto_live_006_rehearsal_packet_fixture",
    "crypto_pilot_003_observation_ledger_doc",
    "crypto_paperlive_observation_ledger_fixture",
    "static_crypto_reference_snapshot_2026_05_09_btc",
    "crypto_source_evidence_link_map_sample",
    "crypto_source_staleness_check_spec_sample",
    "crypto_source_contradiction_ledger_sample",
    "pmbot_queue_template_validation",
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
    "outcome_resolution_allowed": False,
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


def test_static_crypto_outcome_evidence_bundle_fixture_has_expected_contract() -> None:
    bundle = _load_bundle()

    assert tuple(bundle.keys()) == tuple(sorted(bundle.keys()))
    assert bundle["task_id"] == TASK_ID
    assert bundle["bundle_id"] == BUNDLE_ID
    assert bundle["contract_version"] == CONTRACT_VERSION
    assert bundle["run_mode"] == RUN_MODE
    assert bundle["created_at"] == "2026-05-09T03:10:00Z"
    assert bundle["local_only"] is True
    assert bundle["operator_review_required"] is True
    assert bundle["operator_review"]["status"] == OPERATOR_REVIEW_STATUS
    assert bundle["errors"] == []
    assert bundle["warnings"] == []


def test_outcome_evidence_record_links_replay_chain_without_copying_source_values() -> None:
    bundle = _load_bundle()
    replay = _load_json(REPLAY_FIXTURE_PATH)
    ledger = _load_json(LEDGER_FIXTURE_PATH)
    snapshot = _load_json(SNAPSHOT_FIXTURE_PATH)
    record = bundle["outcome_evidence_records"][0]
    replay_record = replay["observation_replay_records"][0]
    ledger_record = ledger["observation_records"][0]
    serialized_bundle = json.dumps(bundle, sort_keys=True)

    assert tuple(bundle["evidence_record_fields"]) == EXPECTED_EVIDENCE_RECORD_FIELDS
    assert tuple(record.keys()) == EXPECTED_EVIDENCE_RECORD_FIELDS
    assert record["record_id"] == f"{BUNDLE_ID}.sample.btc_threshold.evidence"
    assert record["evidence_state"] == "outcome_not_resolved_by_bundle"
    assert record["operator_review_status"] == OPERATOR_REVIEW_STATUS
    assert record["value_field_policy"] == "numeric_source_values_remain_in_local_source_artifacts"
    assert record["source_replay_record_id"] == replay_record["replay_record_id"]
    assert record["source_packet_record_id"] == replay_record["source_packet_record_id"]
    assert record["source_observation_record_id"] == replay_record["source_observation_record_id"]
    assert record["source_review_record_id"] == replay_record["source_review_record_id"]
    assert record["source_capture_record_id"] == replay_record["source_capture_record_id"]
    assert record["local_replay_fixture_reference"] == str(REPLAY_FIXTURE_PATH).replace("\\", "/")
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
        assert record[field] == replay_record[field]
        assert record[field] == ledger_record[field]
    assert record["asset_name"] == snapshot["asset_name"]
    assert record["asset_symbol"] == snapshot["asset_symbol"]
    assert ledger_record["threshold_value"] not in serialized_bundle
    assert ledger_record["reported_reference_value"] not in serialized_bundle
    assert snapshot["reported_reference_value"] not in serialized_bundle


def test_evidence_artifact_records_reference_existing_local_files_with_matching_digests() -> None:
    bundle = _load_bundle()

    assert tuple(record["source_artifact_id"] for record in bundle["evidence_artifact_records"]) == (
        EXPECTED_SOURCE_ARTIFACT_IDS
    )
    for record in bundle["evidence_artifact_records"]:
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


def test_bundle_sections_checks_and_validation_commands_remain_pending() -> None:
    bundle = _load_bundle()

    assert tuple(section["section_id"] for section in bundle["evidence_bundle_sections"]) == EXPECTED_SECTION_IDS
    for section in bundle["evidence_bundle_sections"]:
        assert tuple(section.keys()) == tuple(sorted(section.keys()))
        assert section["operator_review_status"] == OPERATOR_REVIEW_STATUS
        assert section["section_state"] == OPERATOR_REVIEW_STATUS
        assert section["local_references"]
        for local_reference in section["local_references"]:
            _assert_allowed_existing_local_reference(local_reference)
    assert tuple(check["check_id"] for check in bundle["operator_review_checklist"]) == EXPECTED_CHECK_IDS
    assert all(check["status"] == OPERATOR_REVIEW_STATUS for check in bundle["operator_review_checklist"])
    assert bundle["required_validation_commands"] == [
        "python -m compileall pm_bot tests",
        "pytest pm_bot/tests tests/test_codex_queue_pmbot_templates.py",
    ]


def test_source_chain_policy_retains_numeric_source_values_in_local_fixtures() -> None:
    bundle = _load_bundle()

    assert bundle["source_chain_policy"] == {
        "copied_into_bundle": [
            "asset_name",
            "asset_symbol",
            "deadline_utc",
            "market_class",
            "market_slug",
            "market_title",
            "metric_type",
            "quote_currency",
            "source_capture_record_id",
            "source_observation_record_id",
            "source_packet_record_id",
            "source_replay_record_id",
            "source_review_record_id",
        ],
        "policy_id": "local_static_outcome_evidence_value_retention",
        "retained_in_source_artifacts": [
            "threshold_value",
            "reported_reference_value",
        ],
        "status": "active",
    }


def test_safety_boundaries_are_closed_for_crypto_outcome_evidence_bundle() -> None:
    bundle = _load_bundle()

    assert bundle["safety_boundaries"] == EXPECTED_SAFETY_BOUNDARIES
    assert bundle["safety_boundaries"]["local_static_samples_only"] is True
    assert bundle["safety_boundaries"]["operator_review_required"] is True
    assert bundle["safety_boundaries"]["paper_mode_only"] is True
    assert all(value is False for key, value in bundle["safety_boundaries"].items() if key.endswith("_allowed"))


def test_summary_counts_match_crypto_outcome_evidence_bundle_content() -> None:
    bundle = _load_bundle()
    local_references = set(
        _collect_values_for_key(bundle, "local_reference")
        + _collect_values_for_key(bundle, "local_replay_fixture_reference")
        + _collect_values_for_key(bundle, "local_rehearsal_packet_reference")
        + _collect_values_for_key(bundle, "local_observation_fixture_reference")
        + _collect_values_for_key(bundle, "local_snapshot_reference")
    )

    assert bundle["summary_counts"] == {
        "evidence_artifact_records": len(bundle["evidence_artifact_records"]),
        "evidence_bundle_sections": len(bundle["evidence_bundle_sections"]),
        "local_references": len(local_references),
        "operator_review_checklist_items": len(bundle["operator_review_checklist"]),
        "outcome_evidence_records": len(bundle["outcome_evidence_records"]),
        "required_validation_commands": len(bundle["required_validation_commands"]),
        "value_fields_retained_in_source_artifacts": len(
            bundle["source_chain_policy"]["retained_in_source_artifacts"]
        ),
        "warnings": len(bundle["warnings"]),
    }


def test_bundle_references_only_local_static_fixture_paths() -> None:
    bundle = _load_bundle()
    references = sorted(
        set(
            _collect_values_for_key(bundle, "local_reference")
            + _collect_values_for_key(bundle, "local_replay_fixture_reference")
            + _collect_values_for_key(bundle, "local_rehearsal_packet_reference")
            + _collect_values_for_key(bundle, "local_observation_fixture_reference")
            + _collect_values_for_key(bundle, "local_snapshot_reference")
        )
    )

    assert references == [
        "docs/PMBOT_CRYPTO_LIVE_006_CRYPTO_PAPERLIVE_REHEARSAL_PACKET_LOCAL_ONLY.md",
        "docs/PMBOT_CRYPTO_LIVE_007_CRYPTO_PAPERLIVE_OBSERVATION_REPLAY_LOCAL_ONLY.md",
        "docs/PMBOT_CRYPTO_PILOT_003_CRYPTO_PAPERLIVE_OBSERVATION_LEDGER_LOCAL_ONLY.md",
        "pm_bot/source_quality/samples/crypto_source_contradiction_ledger.fixture.json",
        "pm_bot/source_quality/samples/crypto_source_evidence_link_map.fixture.json",
        "pm_bot/source_quality/samples/crypto_source_staleness_check_spec.fixture.json",
        str(REPLAY_FIXTURE_PATH).replace("\\", "/"),
        str(REHEARSAL_FIXTURE_PATH).replace("\\", "/"),
        str(LEDGER_FIXTURE_PATH).replace("\\", "/"),
        str(SNAPSHOT_FIXTURE_PATH).replace("\\", "/"),
        "tests/test_codex_queue_pmbot_templates.py",
    ]
    for reference in references:
        _assert_allowed_existing_local_reference(reference)


def test_fixture_has_no_decision_scoring_or_selection_terms() -> None:
    bundle = _load_bundle()

    assert _find_disallowed_terms(bundle) == []


def test_documentation_registers_crypto_outcome_bundle_fixture_and_safety_boundary() -> None:
    document = DOC_PATH.read_text(encoding="utf-8")

    assert f"Task: `{TASK_ID}`" in document
    assert f"Bundle: `{BUNDLE_ID}`" in document
    assert f"Contract: `{CONTRACT_VERSION}`" in document
    assert f"Run mode: `{RUN_MODE}`" in document
    assert str(FIXTURE_PATH).replace("\\", "/") in document
    assert str(REPLAY_FIXTURE_PATH).replace("\\", "/") in document
    assert str(REHEARSAL_FIXTURE_PATH).replace("\\", "/") in document
    assert str(LEDGER_FIXTURE_PATH).replace("\\", "/") in document
    assert str(SNAPSHOT_FIXTURE_PATH).replace("\\", "/") in document
    assert "No forecast scoring, action guidance, market ranking" in document
    assert "This bundle is not execution approval and is not runtime input." in document


def _load_bundle() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


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
            if key in {
                "local_reference",
                "local_observation_fixture_reference",
                "local_rehearsal_packet_reference",
                "local_replay_fixture_reference",
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
