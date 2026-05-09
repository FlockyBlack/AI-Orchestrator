from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from pm_bot.source_quality.source_evidence_link_map import (
    EXPECTED_SAFETY_BOUNDARIES,
    LINK_MAP_CONTRACT_VERSION,
    LINK_MAP_RUN_MODE,
    LINK_ROW_STATE,
    OPERATOR_REVIEW_STATUS,
    REQUEST_CONTRACT_VERSION,
    SAMPLE_LINK_MAP_PATH,
    SAMPLE_OPERATOR_REPORT_PATH,
    SourceQualityLedgerValidationError,
    build_operator_report,
    build_source_evidence_link_map,
    load_source_evidence_link_map_request,
    main,
    validate_source_evidence_link_map,
    validate_source_evidence_link_map_request,
)

DOC_PATH = Path("docs/PMBOT_SOURCE_EVIDENCE_002_SOURCE_EVIDENCE_LINK_MAP_LOCAL_ONLY.md")
VALID_REQUEST_REFERENCE = "pm_bot/tests/fixtures/source_quality/source_evidence_link_map_request.valid.json"
VALID_REQUEST_PATH = Path(VALID_REQUEST_REFERENCE)


def test_valid_request_builds_source_evidence_link_map() -> None:
    request = load_source_evidence_link_map_request(VALID_REQUEST_PATH)
    validation = validate_source_evidence_link_map_request(request)
    link_map = build_source_evidence_link_map(request)

    assert validation.valid is True
    assert validation.errors == ()
    assert link_map["contract_version"] == LINK_MAP_CONTRACT_VERSION
    assert link_map["map_id"] == "source_evidence_link_map_fixture_001"
    assert link_map["run_mode"] == LINK_MAP_RUN_MODE
    assert link_map["local_only"] is True
    assert link_map["operator_review_required"] is True
    assert link_map["operator_review"]["status"] == OPERATOR_REVIEW_STATUS
    assert link_map["safety_boundaries"] == EXPECTED_SAFETY_BOUNDARIES
    assert link_map["summary_counts"] == {
        "inventory_rows_linked": 4,
        "local_references": 7,
        "operator_review_steps": 3,
        "review_checks": 16,
        "source_artifact_references": 4,
        "source_evidence_links": 4,
        "warnings": 0,
    }
    assert [row["source_id"] for row in link_map["source_evidence_links"]] == [
        "airport_station_observation_log",
        "official_daily_climate_report",
        "static_crypto_reference_snapshot_2026_05_09_btc",
        "unified_source_quality_ledger_sample",
    ]
    first = link_map["source_evidence_links"][0]
    assert first["link_id"] == "source_evidence_link_map_fixture_001.airport_station_observation_log.source_evidence_link"
    assert first["link_state"] == LINK_ROW_STATE
    assert first["source_evidence_record_id"] == (
        "source_evidence_inventory_ledger_fixture_001.airport_station_observation_log.source_evidence"
    )
    assert first["source_artifact"] == {
        "artifact_format": "json_object",
        "byte_count": 536,
        "content_sha256": "e27ccc4dedeb4b3da48cd9e636d137e78be3cefa9683598879b2aed122370a8c",
        "local_reference": "pm_bot/tests/fixtures/weather/airport_station_observation_log_snapshot.json",
        "present": True,
        "source_artifact_present": True,
    }
    assert first["inventory_ledger"]["local_reference"] == "pm_bot/source_quality/samples/source_evidence_inventory_ledger.fixture.json"
    assert first["operator_report"]["local_reference"] == "pm_bot/source_quality/samples/source_evidence_inventory_ledger.fixture.md"
    assert first["documentation"]["local_reference"] == "docs/PMBOT_SOURCE_EVIDENCE_001_SOURCE_INVENTORY_LEDGER_LOCAL_ONLY.md"
    assert len(first["review_checks"]) == 4
    assert all(check["operator_review_status"] == OPERATOR_REVIEW_STATUS for check in first["review_checks"])


def test_source_evidence_link_map_is_deterministic_for_same_request() -> None:
    request = load_source_evidence_link_map_request(VALID_REQUEST_PATH)

    first = build_source_evidence_link_map(request)
    second = build_source_evidence_link_map(deepcopy(request))

    assert first == second
    assert first["build_id"] == "source_evidence_link_map_fixture_001-a888c8609457"


def test_static_sample_matches_source_evidence_link_map_builder_output() -> None:
    request = load_source_evidence_link_map_request(VALID_REQUEST_PATH)
    sample = json.loads(Path(SAMPLE_LINK_MAP_PATH).read_text(encoding="utf-8"))

    assert build_source_evidence_link_map(request) == sample


def test_static_sample_validates_as_source_evidence_link_map() -> None:
    sample = json.loads(Path(SAMPLE_LINK_MAP_PATH).read_text(encoding="utf-8"))

    validation = validate_source_evidence_link_map(sample)

    assert validation.valid is True
    assert validation.errors == ()


def test_static_markdown_sample_matches_report_builder_output() -> None:
    sample = json.loads(Path(SAMPLE_LINK_MAP_PATH).read_text(encoding="utf-8"))
    sample_report = Path(SAMPLE_OPERATOR_REPORT_PATH).read_text(encoding="utf-8")

    assert build_operator_report(sample) == sample_report


def test_cli_writes_local_source_evidence_link_map_and_operator_report(tmp_path: Path) -> None:
    map_path = tmp_path / "source_evidence_link_map.json"
    report_path = tmp_path / "source_evidence_link_map.md"

    exit_code = main(
        [
            "--request",
            str(VALID_REQUEST_PATH),
            "--output-map",
            str(map_path),
            "--output-report",
            str(report_path),
        ]
    )

    assert exit_code == 0
    link_map = json.loads(map_path.read_text(encoding="utf-8"))
    report = report_path.read_text(encoding="utf-8")
    assert link_map["contract_version"] == LINK_MAP_CONTRACT_VERSION
    assert link_map["errors"] == []
    assert link_map["warnings"] == []
    assert "# PMBOT Source Evidence Link Map" in report
    assert "airport_station_observation_log" in report
    assert "Records local references, byte counts, digests, and pending review state only." in report
    assert "Does not authorize execution and is not runtime input." in report


def test_request_rejects_network_like_inventory_reference() -> None:
    request = load_source_evidence_link_map_request(VALID_REQUEST_PATH)
    request["source_inventory_ledger_reference"] = "https://example.invalid/source_evidence_inventory.json"

    validation = validate_source_evidence_link_map_request(request)

    assert validation.valid is False
    assert any("local_reference must point to a local fixture or static artifact" in error for error in validation.errors)
    with pytest.raises(SourceQualityLedgerValidationError):
        build_source_evidence_link_map(request)


def test_link_map_validation_rejects_digest_or_inventory_row_drift() -> None:
    sample = json.loads(Path(SAMPLE_LINK_MAP_PATH).read_text(encoding="utf-8"))
    sample["source_evidence_links"][0]["source_artifact"]["content_sha256"] = "0" * 64
    sample["source_evidence_links"][0]["source_evidence_record_id"] = "wrong.local.record"

    validation = validate_source_evidence_link_map(sample)

    assert validation.valid is False
    assert any("content_sha256 must match local bytes" in error for error in validation.errors)
    assert any("source_evidence_record_id must match source inventory row" in error for error in validation.errors)


def test_output_contract_has_no_forecast_scoring_or_selection_terms() -> None:
    request = load_source_evidence_link_map_request(VALID_REQUEST_PATH)
    link_map = build_source_evidence_link_map(request)

    assert _find_output_decision_terms(link_map) == []


def test_source_evidence_link_map_documentation_registers_local_artifacts() -> None:
    document = DOC_PATH.read_text(encoding="utf-8")

    assert "Task: `PMBOT-SOURCE-EVIDENCE-002-SOURCE-EVIDENCE-LINK-MAP-LOCAL-ONLY`" in document
    assert f"Contract: `{LINK_MAP_CONTRACT_VERSION}`" in document
    assert f"Run mode: `{LINK_MAP_RUN_MODE}`" in document
    assert VALID_REQUEST_REFERENCE in document
    assert SAMPLE_LINK_MAP_PATH in document
    assert SAMPLE_OPERATOR_REPORT_PATH in document
    assert "This link map is not execution approval and is not runtime input." in document


def test_request_contract_version_is_explicit() -> None:
    request = load_source_evidence_link_map_request(VALID_REQUEST_PATH)

    assert request["contract_version"] == REQUEST_CONTRACT_VERSION


def _find_output_decision_terms(value: object, path: str = "$") -> list[str]:
    forbidden_tokens = {
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
            if _has_token(str(key), forbidden_tokens):
                hits.append(key_path)
            hits.extend(_find_output_decision_terms(nested_value, key_path))
    elif isinstance(value, list):
        for index, nested_value in enumerate(value):
            hits.extend(_find_output_decision_terms(nested_value, f"{path}[{index}]"))
    elif isinstance(value, str) and _has_token(value, forbidden_tokens):
        hits.append(path)
    return hits


def _has_token(value: str, forbidden_tokens: set[str]) -> bool:
    normalized = "".join(character if character.isalnum() else "_" for character in value.lower())
    tokens = {token for token in normalized.split("_") if token}
    return bool(tokens & forbidden_tokens)
