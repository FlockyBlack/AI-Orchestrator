from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from pm_bot.source_quality.crypto_source_evidence_link_map import (
    CRYPTO_INVENTORY_FIXTURE_PATH,
    CRYPTO_LINK_MAP_DOCUMENTATION_PATH,
    EXPECTED_SAFETY_BOUNDARIES,
    EXPECTED_SOURCE_IDS,
    LINK_MAP_CONTRACT_VERSION,
    LINK_MAP_ID,
    LINK_MAP_RUN_MODE,
    LINK_ROW_STATE,
    OPERATOR_REVIEW_STATUS,
    REQUIRED_VALIDATION_COMMANDS,
    SAMPLE_LINK_MAP_PATH,
    SAMPLE_OPERATOR_REPORT_PATH,
    TASK_ID,
    SourceQualityLedgerValidationError,
    build_crypto_source_evidence_link_map,
    build_operator_report,
    load_crypto_live_data_source_inventory,
    load_crypto_source_evidence_link_map,
    main,
    validate_crypto_source_evidence_link_map,
)

DOC_PATH = Path(CRYPTO_LINK_MAP_DOCUMENTATION_PATH)
SAMPLE_LINK_MAP = Path(SAMPLE_LINK_MAP_PATH)
SAMPLE_OPERATOR_REPORT = Path(SAMPLE_OPERATOR_REPORT_PATH)


def test_crypto_source_evidence_link_map_builds_from_local_inventory() -> None:
    inventory = load_crypto_live_data_source_inventory(CRYPTO_INVENTORY_FIXTURE_PATH)
    link_map = build_crypto_source_evidence_link_map(inventory)
    validation = validate_crypto_source_evidence_link_map(link_map)

    assert validation.valid is True
    assert validation.errors == ()
    assert link_map["task_id"] == TASK_ID
    assert link_map["contract_version"] == LINK_MAP_CONTRACT_VERSION
    assert link_map["map_id"] == LINK_MAP_ID
    assert link_map["run_mode"] == LINK_MAP_RUN_MODE
    assert link_map["created_at"] == "2026-05-09T01:10:00Z"
    assert link_map["local_only"] is True
    assert link_map["operator_review_required"] is True
    assert link_map["operator_review"]["status"] == OPERATOR_REVIEW_STATUS
    assert link_map["safety_boundaries"] == EXPECTED_SAFETY_BOUNDARIES
    assert link_map["required_validation_commands"] == list(REQUIRED_VALIDATION_COMMANDS)
    assert link_map["summary_counts"] == {
        "inventory_records_linked": 6,
        "local_references": 14,
        "operator_review_steps": 3,
        "required_validation_commands": 2,
        "review_checks": 24,
        "source_artifact_references": 6,
        "source_contract_references": 6,
        "source_evidence_links": 6,
        "warnings": 0,
    }
    assert tuple(row["source_id"] for row in link_map["source_evidence_links"]) == EXPECTED_SOURCE_IDS

    first = link_map["source_evidence_links"][0]
    assert first["link_id"] == (
        "pmbot-crypto-source-evidence-link-map-001."
        "read_only_crypto_data_contract_fixture.crypto_source_evidence_link"
    )
    assert first["link_state"] == LINK_ROW_STATE
    assert first["source_record_id"] == "crypto_live_data_source_inventory_001.read_only_contract_fixture"
    assert first["source_artifact"]["local_reference"] == (
        "pm_bot/tests/fixtures/crypto_live/pmbot_read_only_crypto_data_contract.valid.json"
    )
    assert first["source_contract"]["source_contract_id"] == "crypto_live_read_only_crypto_data_contract"
    assert first["source_contract"]["contract_coverage"] == "direct_contract_documentation"
    assert first["source_inventory"]["local_reference"] == CRYPTO_INVENTORY_FIXTURE_PATH
    assert len(first["review_checks"]) == 4
    assert all(check["operator_review_status"] == OPERATOR_REVIEW_STATUS for check in first["review_checks"])


def test_crypto_source_evidence_link_map_is_deterministic() -> None:
    inventory = load_crypto_live_data_source_inventory(CRYPTO_INVENTORY_FIXTURE_PATH)

    first = build_crypto_source_evidence_link_map(inventory)
    second = build_crypto_source_evidence_link_map(deepcopy(inventory))

    assert first == second
    assert first["build_id"] == "pmbot-crypto-source-evidence-link-map-001-31b7949e98d1"


def test_static_sample_matches_crypto_source_evidence_link_map_builder_output() -> None:
    inventory = load_crypto_live_data_source_inventory(CRYPTO_INVENTORY_FIXTURE_PATH)
    sample = json.loads(SAMPLE_LINK_MAP.read_text(encoding="utf-8"))

    assert build_crypto_source_evidence_link_map(inventory) == sample


def test_static_sample_validates_as_crypto_source_evidence_link_map() -> None:
    sample = load_crypto_source_evidence_link_map(SAMPLE_LINK_MAP)

    validation = validate_crypto_source_evidence_link_map(sample)

    assert validation.valid is True
    assert validation.errors == ()


def test_static_markdown_sample_matches_crypto_operator_report_builder_output() -> None:
    sample = load_crypto_source_evidence_link_map(SAMPLE_LINK_MAP)
    sample_report = SAMPLE_OPERATOR_REPORT.read_text(encoding="utf-8")

    assert build_operator_report(sample) == sample_report


def test_cli_writes_crypto_source_evidence_link_map_and_operator_report(tmp_path: Path) -> None:
    map_path = tmp_path / "crypto_source_evidence_link_map.json"
    report_path = tmp_path / "crypto_source_evidence_link_map.md"

    exit_code = main(
        [
            "--inventory",
            CRYPTO_INVENTORY_FIXTURE_PATH,
            "--output-map",
            str(map_path),
            "--output-report",
            str(report_path),
        ]
    )

    link_map = json.loads(map_path.read_text(encoding="utf-8"))
    report = report_path.read_text(encoding="utf-8")
    assert exit_code == 0
    assert link_map["contract_version"] == LINK_MAP_CONTRACT_VERSION
    assert link_map["errors"] == []
    assert link_map["warnings"] == []
    assert "# PMBOT Crypto Source Evidence Link Map" in report
    assert "read_only_crypto_data_contract_fixture" in report
    assert "Records local references, byte counts, digests, and pending review state only." in report
    assert "Does not authorize execution and is not runtime input." in report


def test_crypto_link_map_validation_rejects_network_reference_and_digest_drift() -> None:
    sample = load_crypto_source_evidence_link_map(SAMPLE_LINK_MAP)
    sample["source_evidence_links"][0]["source_artifact"]["local_reference"] = (
        "https://example.invalid/crypto_source.json"
    )
    sample["source_evidence_links"][1]["source_contract"]["content_sha256"] = "0" * 64

    validation = validate_crypto_source_evidence_link_map(sample)

    assert validation.valid is False
    assert any("local_reference must point to a local fixture or static artifact" in error for error in validation.errors)
    assert any("content_sha256 must match local bytes" in error for error in validation.errors)


def test_crypto_source_evidence_link_map_rejects_invalid_inventory_payload() -> None:
    inventory = load_crypto_live_data_source_inventory(CRYPTO_INVENTORY_FIXTURE_PATH)
    inventory["source_records"][0]["operator_review_status"] = "reviewed"

    with pytest.raises(SourceQualityLedgerValidationError):
        build_crypto_source_evidence_link_map(inventory)


def test_crypto_source_evidence_link_map_has_no_decision_scoring_or_selection_terms() -> None:
    sample = load_crypto_source_evidence_link_map(SAMPLE_LINK_MAP)

    assert _find_disallowed_terms(sample) == []


def test_crypto_source_evidence_link_map_documentation_registers_local_artifacts() -> None:
    document = DOC_PATH.read_text(encoding="utf-8")

    assert f"Task: `{TASK_ID}`" in document
    assert f"Map: `{LINK_MAP_ID}`" in document
    assert f"Contract: `{LINK_MAP_CONTRACT_VERSION}`" in document
    assert f"Run mode: `{LINK_MAP_RUN_MODE}`" in document
    assert CRYPTO_INVENTORY_FIXTURE_PATH in document
    assert SAMPLE_LINK_MAP_PATH in document
    assert SAMPLE_OPERATOR_REPORT_PATH in document
    assert "This link map is not execution approval and is not runtime input." in document


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
