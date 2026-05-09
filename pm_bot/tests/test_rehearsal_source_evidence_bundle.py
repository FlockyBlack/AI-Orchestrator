from __future__ import annotations

import hashlib
import json
from pathlib import Path


DOC_PATH = Path("docs/PMBOT_REHEARSAL_003_REHEARSAL_SOURCE_EVIDENCE_BUNDLE_LOCAL_ONLY.md")
FIXTURE_PATH = Path("pm_bot/tests/fixtures/rehearsal/pmbot_rehearsal_source_evidence_bundle.valid.json")
MARKET_PACKET_FIXTURE_PATH = Path("pm_bot/tests/fixtures/rehearsal/pmbot_rehearsal_market_packet_schema.valid.json")
SOURCE_INVENTORY_PATH = Path("pm_bot/source_quality/samples/source_evidence_inventory_ledger.fixture.json")
SOURCE_LINK_MAP_PATH = Path("pm_bot/source_quality/samples/source_evidence_link_map.fixture.json")
SOURCE_STALENESS_PATH = Path("pm_bot/source_quality/samples/source_staleness_check_spec.fixture.json")
SOURCE_CONTRADICTION_PATH = Path("pm_bot/source_quality/samples/source_contradiction_ledger.fixture.json")

TASK_ID = "PMBOT-REHEARSAL-003-REHEARSAL-SOURCE-EVIDENCE-BUNDLE-LOCAL-ONLY"
BUNDLE_ID = "pmbot-rehearsal-source-evidence-bundle-001"
CONTRACT_VERSION = "pmbot_rehearsal_source_evidence_bundle.v1"
RUN_MODE = "local_static_rehearsal_source_evidence_bundle"
OPERATOR_REVIEW_STATUS = "pending_operator_review"
ALLOWED_LOCAL_PREFIXES = ("docs/", "pm_bot/readiness/", "pm_bot/source_quality/", "pm_bot/tests/", "tests/")

EXPECTED_BUNDLE_RECORD_FIELDS = (
    "bundle_record_id",
    "bundle_record_state",
    "evidence_reference_policy",
    "linked_market_packet_id",
    "local_market_packet_reference",
    "operator_review_status",
    "rehearsal_phase",
    "source_evidence_artifact_ids",
    "source_evidence_record_ids",
    "source_value_policy",
)
EXPECTED_CHECK_IDS = (
    "local_reference_review",
    "bundle_record_review",
    "source_artifact_digest_review",
    "source_record_identifier_review",
    "operator_review_status_review",
    "source_value_boundary_review",
    "sensitive_path_exclusion_check",
    "runtime_boundary_check",
    "validation_replay_check",
)
EXPECTED_SECTION_IDS = (
    "bundle_identity_review",
    "rehearsal_packet_context_review",
    "source_evidence_link_review",
    "source_state_review",
    "validation_review",
)
EXPECTED_SOURCE_EVIDENCE_ARTIFACT_IDS = (
    "source_evidence_inventory_ledger_doc",
    "source_evidence_inventory_ledger_fixture",
    "source_evidence_inventory_ledger_report",
    "source_evidence_link_map_doc",
    "source_evidence_link_map_fixture",
    "source_evidence_link_map_report",
    "source_staleness_check_spec_doc",
    "source_staleness_check_spec_fixture",
    "source_staleness_check_spec_report",
    "source_contradiction_ledger_doc",
    "source_contradiction_ledger_fixture",
    "source_contradiction_ledger_report",
)
EXPECTED_SAFETY_BOUNDARIES = {
    "authenticated_endpoint_calls_allowed": False,
    "background_process_allowed": False,
    "browser_automation_allowed": False,
    "credential_or_secret_access_allowed": False,
    "descriptive_source_evidence_bundle_only": True,
    "execution_endpoint_calls_allowed": False,
    "external_service_calls_allowed": False,
    "llm_provider_calls_allowed": False,
    "local_static_samples_only": True,
    "market_api_calls_allowed": False,
    "market_ranking_allowed": False,
    "network_calls_allowed": False,
    "numeric_prediction_metric_allowed": False,
    "openrouter_calls_allowed": False,
    "operator_review_required": True,
    "order_or_trade_surface_changes_allowed": False,
    "paper_mode_only": True,
    "polymarket_api_calls_allowed": False,
    "resident_process_allowed": False,
    "run_codex_changes_allowed": False,
    "runtime_or_dispatcher_changes_allowed": False,
    "scheduler_or_worker_allowed": False,
    "trading_endpoint_calls_allowed": False,
    "transaction_endpoint_calls_allowed": False,
    "wallet_or_signing_material_access_allowed": False,
}


def test_static_rehearsal_source_evidence_bundle_fixture_has_expected_contract() -> None:
    bundle = _load_bundle()

    assert tuple(bundle.keys()) == tuple(sorted(bundle.keys()))
    assert bundle["task_id"] == TASK_ID
    assert bundle["bundle_id"] == BUNDLE_ID
    assert bundle["contract_version"] == CONTRACT_VERSION
    assert bundle["run_mode"] == RUN_MODE
    assert bundle["created_at"] == "2026-05-09T02:20:00Z"
    assert bundle["local_only"] is True
    assert bundle["operator_review_required"] is True
    assert bundle["operator_review"]["status"] == OPERATOR_REVIEW_STATUS
    assert bundle["operator_review"]["reviewed_at"] is None
    assert bundle["operator_review"]["reviewed_by"] is None
    assert bundle["errors"] == []
    assert bundle["warnings"] == []


def test_bundle_record_links_market_packet_to_source_evidence_records() -> None:
    bundle = _load_bundle()
    market_packet = _load_json(MARKET_PACKET_FIXTURE_PATH)
    record = bundle["bundle_records"][0]
    source_ids = record["source_evidence_record_ids"]

    assert tuple(bundle["bundle_record_fields"]) == EXPECTED_BUNDLE_RECORD_FIELDS
    assert len(bundle["bundle_records"]) == 1
    assert tuple(record.keys()) == EXPECTED_BUNDLE_RECORD_FIELDS
    assert record["bundle_record_id"] == f"{BUNDLE_ID}.static_local_rehearsal_source_evidence"
    assert record["bundle_record_state"] == "source_evidence_bundle_pending_operator_review"
    assert record["linked_market_packet_id"] == market_packet["market_packet_records"][0]["market_packet_id"]
    assert record["local_market_packet_reference"] == str(MARKET_PACKET_FIXTURE_PATH).replace("\\", "/")
    assert record["operator_review_status"] == OPERATOR_REVIEW_STATUS
    assert record["evidence_reference_policy"] == "local_static_artifact_references_only"
    assert record["source_value_policy"] == "source_values_remain_in_referenced_local_artifacts"
    assert tuple(record["source_evidence_artifact_ids"]) == EXPECTED_SOURCE_EVIDENCE_ARTIFACT_IDS
    assert len(source_ids["inventory_record_ids"]) == 4
    assert len(source_ids["link_map_row_ids"]) == 4
    assert len(source_ids["staleness_check_ids"]) == 4
    assert len(source_ids["contradiction_row_ids"]) == 1
    _assert_allowed_existing_local_reference(record["local_market_packet_reference"])


def test_source_evidence_artifacts_reference_existing_local_files_with_matching_digests() -> None:
    bundle = _load_bundle()

    assert tuple(artifact["artifact_id"] for artifact in bundle["source_evidence_artifacts"]) == (
        EXPECTED_SOURCE_EVIDENCE_ARTIFACT_IDS
    )
    for artifact in bundle["source_evidence_artifacts"]:
        assert tuple(artifact.keys()) == (
            "artifact_id",
            "artifact_role",
            "artifact_type",
            "byte_count",
            "content_sha256",
            "contract_version",
            "local_reference",
            "operator_review_status",
            "source_group",
        )
        assert artifact["operator_review_status"] == OPERATOR_REVIEW_STATUS
        _assert_allowed_existing_local_reference(artifact["local_reference"])
        data = Path(artifact["local_reference"]).read_bytes()
        assert artifact["byte_count"] == len(data)
        assert artifact["content_sha256"] == hashlib.sha256(data).hexdigest()


def test_review_sections_checks_rules_and_validation_commands_are_fixed() -> None:
    bundle = _load_bundle()

    assert tuple(section["section_id"] for section in bundle["review_sections"]) == EXPECTED_SECTION_IDS
    for section in bundle["review_sections"]:
        assert tuple(section.keys()) == tuple(sorted(section.keys()))
        assert section["operator_review_status"] == OPERATOR_REVIEW_STATUS
        for local_reference in section["local_references"]:
            _assert_allowed_existing_local_reference(local_reference)

    assert tuple(check["check_id"] for check in bundle["operator_review_checklist"]) == EXPECTED_CHECK_IDS
    assert all(check["status"] == OPERATOR_REVIEW_STATUS for check in bundle["operator_review_checklist"])
    assert [rule["status"] for rule in bundle["source_bundle_rules"]] == ["active"] * 6
    assert [rule["rule_id"] for rule in bundle["source_bundle_rules"]] == [
        "local_static_inputs_only",
        "descriptive_evidence_only",
        "operator_review_status_preserved",
        "source_value_boundary",
        "closed_endpoint_boundary",
        "closed_process_boundary",
    ]
    assert bundle["required_validation_commands"] == [
        "python -m compileall pm_bot tests",
        "pytest pm_bot/tests tests/test_codex_queue_pmbot_templates.py",
    ]


def test_source_record_identifiers_exist_in_referenced_local_artifacts() -> None:
    bundle = _load_bundle()
    record_ids = bundle["bundle_records"][0]["source_evidence_record_ids"]

    inventory_ids = _ids(_load_json(SOURCE_INVENTORY_PATH)["source_evidence_rows"], "record_id")
    link_ids = _ids(_load_json(SOURCE_LINK_MAP_PATH)["source_evidence_links"], "link_id")
    staleness_ids = _ids(_load_json(SOURCE_STALENESS_PATH)["source_staleness_checks"], "check_id")
    contradiction_ids = _ids(_load_json(SOURCE_CONTRADICTION_PATH)["source_contradiction_rows"], "row_id")

    assert set(record_ids["inventory_record_ids"]) <= inventory_ids
    assert set(record_ids["link_map_row_ids"]) <= link_ids
    assert set(record_ids["staleness_check_ids"]) <= staleness_ids
    assert set(record_ids["contradiction_row_ids"]) <= contradiction_ids


def test_safety_boundaries_are_closed_for_rehearsal_source_evidence_bundle() -> None:
    bundle = _load_bundle()

    assert bundle["safety_boundaries"] == EXPECTED_SAFETY_BOUNDARIES
    assert bundle["safety_boundaries"]["local_static_samples_only"] is True
    assert bundle["safety_boundaries"]["operator_review_required"] is True
    assert bundle["safety_boundaries"]["paper_mode_only"] is True
    assert all(value is False for key, value in bundle["safety_boundaries"].items() if key.endswith("_allowed"))


def test_summary_counts_match_rehearsal_source_evidence_bundle_content() -> None:
    bundle = _load_bundle()
    record_ids = bundle["bundle_records"][0]["source_evidence_record_ids"]
    local_references = {
        *(reference for section in bundle["review_sections"] for reference in section["local_references"]),
        *(artifact["local_reference"] for artifact in bundle["source_evidence_artifacts"]),
        bundle["bundle_records"][0]["local_market_packet_reference"],
    }

    assert bundle["summary_counts"] == {
        "bundle_record_fields": len(bundle["bundle_record_fields"]),
        "bundle_records": len(bundle["bundle_records"]),
        "local_references": len(local_references),
        "operator_review_checklist_items": len(bundle["operator_review_checklist"]),
        "required_validation_commands": len(bundle["required_validation_commands"]),
        "review_sections": len(bundle["review_sections"]),
        "source_bundle_rules": len(bundle["source_bundle_rules"]),
        "source_contradiction_rows": len(record_ids["contradiction_row_ids"]),
        "source_evidence_artifacts": len(bundle["source_evidence_artifacts"]),
        "source_evidence_link_rows": len(record_ids["link_map_row_ids"]),
        "source_inventory_records": len(record_ids["inventory_record_ids"]),
        "source_staleness_checks": len(record_ids["staleness_check_ids"]),
        "warnings": len(bundle["warnings"]),
    }


def test_fixture_has_no_decision_scoring_or_selection_terms() -> None:
    bundle = _load_bundle()

    assert _find_disallowed_terms(bundle) == []


def test_documentation_registers_rehearsal_source_evidence_bundle_and_safety_boundary() -> None:
    document = DOC_PATH.read_text(encoding="utf-8")

    assert f"Task: `{TASK_ID}`" in document
    assert f"Bundle: `{BUNDLE_ID}`" in document
    assert f"Contract: `{CONTRACT_VERSION}`" in document
    assert f"Run mode: `{RUN_MODE}`" in document
    assert str(FIXTURE_PATH).replace("\\", "/") in document
    assert "pm_bot/source_quality/samples/source_evidence_inventory_ledger.fixture.json" in document
    assert "pm_bot/source_quality/samples/source_evidence_link_map.fixture.json" in document
    assert "pm_bot/source_quality/samples/source_staleness_check_spec.fixture.json" in document
    assert "pm_bot/source_quality/samples/source_contradiction_ledger.fixture.json" in document
    assert "No market recommendation, forecast scoring, action guidance, or selection advice." in document
    assert "No probability, EV, edge, or confidence scoring." in document
    assert "This bundle is not execution approval and is not runtime input." in document


def _load_bundle() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _ids(records: list[dict], key: str) -> set[str]:
    return {record[key] for record in records}


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
                "local_market_packet_reference",
                "local_reference",
                "local_references",
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
