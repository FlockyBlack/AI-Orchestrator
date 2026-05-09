from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from pm_bot.source_quality.source_evidence_inventory_ledger import (
    EXPECTED_SAFETY_BOUNDARIES,
    LEDGER_CONTRACT_VERSION,
    LEDGER_ROW_STATE,
    LEDGER_RUN_MODE,
    OPERATOR_REVIEW_STATUS,
    REQUEST_CONTRACT_VERSION,
    SAMPLE_LEDGER_PATH,
    SAMPLE_OPERATOR_REPORT_PATH,
    SourceQualityLedgerValidationError,
    build_operator_report,
    build_source_evidence_inventory_ledger,
    load_source_evidence_inventory_request,
    main,
    validate_source_evidence_inventory_ledger,
    validate_source_evidence_inventory_request,
)

DOC_PATH = Path("docs/PMBOT_SOURCE_EVIDENCE_001_SOURCE_INVENTORY_LEDGER_LOCAL_ONLY.md")
VALID_REQUEST_REFERENCE = "pm_bot/tests/fixtures/source_quality/source_evidence_inventory_ledger_request.valid.json"
VALID_REQUEST_PATH = Path(VALID_REQUEST_REFERENCE)


def test_valid_request_builds_source_evidence_inventory_ledger() -> None:
    request = load_source_evidence_inventory_request(VALID_REQUEST_PATH)
    validation = validate_source_evidence_inventory_request(request)
    ledger = build_source_evidence_inventory_ledger(request)

    assert validation.valid is True
    assert validation.errors == ()
    assert ledger["contract_version"] == LEDGER_CONTRACT_VERSION
    assert ledger["inventory_id"] == "source_evidence_inventory_ledger_fixture_001"
    assert ledger["run_mode"] == LEDGER_RUN_MODE
    assert ledger["local_only"] is True
    assert ledger["operator_review_required"] is True
    assert ledger["operator_review"]["status"] == OPERATOR_REVIEW_STATUS
    assert ledger["safety_boundaries"] == EXPECTED_SAFETY_BOUNDARIES
    assert ledger["summary_counts"] == {
        "fields_declared": 39,
        "fields_missing": 0,
        "fields_present": 39,
        "local_references": 4,
        "operator_review_steps": 3,
        "review_checks": 12,
        "source_evidence_rows": 4,
        "warnings": 0,
    }
    assert [row["source_id"] for row in ledger["source_evidence_rows"]] == [
        "airport_station_observation_log",
        "official_daily_climate_report",
        "static_crypto_reference_snapshot_2026_05_09_btc",
        "unified_source_quality_ledger_sample",
    ]
    assert ledger["source_evidence_rows"][0] == {
        "artifact_format": "json_object",
        "byte_count": 536,
        "content_sha256": "e27ccc4dedeb4b3da48cd9e636d137e78be3cefa9683598879b2aed122370a8c",
        "contract_version": "pmbot_weather_observation_snapshot.v1",
        "evidence_role": "weather_observation_fixture",
        "field_inventory": [
            {
                "field_name": "contract_version",
                "observed_value_type": "str",
                "operator_review_status": OPERATOR_REVIEW_STATUS,
                "present": True,
            },
            {
                "field_name": "snapshot_id",
                "observed_value_type": "str",
                "operator_review_status": OPERATOR_REVIEW_STATUS,
                "present": True,
            },
            {
                "field_name": "source_id",
                "observed_value_type": "str",
                "operator_review_status": OPERATOR_REVIEW_STATUS,
                "present": True,
            },
            {
                "field_name": "source_type",
                "observed_value_type": "str",
                "operator_review_status": OPERATOR_REVIEW_STATUS,
                "present": True,
            },
            {
                "field_name": "observation_date",
                "observed_value_type": "str",
                "operator_review_status": OPERATOR_REVIEW_STATUS,
                "present": True,
            },
            {
                "field_name": "station_id",
                "observed_value_type": "str",
                "operator_review_status": OPERATOR_REVIEW_STATUS,
                "present": True,
            },
            {
                "field_name": "observed_high_temperature_f",
                "observed_value_type": "int",
                "operator_review_status": OPERATOR_REVIEW_STATUS,
                "present": True,
            },
            {
                "field_name": "observation_timestamp",
                "observed_value_type": "str",
                "operator_review_status": OPERATOR_REVIEW_STATUS,
                "present": True,
            },
            {
                "field_name": "source_snapshot_note",
                "observed_value_type": "str",
                "operator_review_status": OPERATOR_REVIEW_STATUS,
                "present": True,
            },
        ],
        "field_summary": {
            "declared": 9,
            "missing": 0,
            "present": 9,
        },
        "known_limitations": [
            "Static local artifact only; no external refresh is performed.",
            "Records field names and byte digests only, not source values.",
        ],
        "local_reference": "pm_bot/tests/fixtures/weather/airport_station_observation_log_snapshot.json",
        "operator_review_status": OPERATOR_REVIEW_STATUS,
        "record_id": "source_evidence_inventory_ledger_fixture_001.airport_station_observation_log.source_evidence",
        "review_checks": [
            {
                "check_id": "identity",
                "description": "Confirm artifact path and source identity match the local fixture.",
                "operator_review_status": OPERATOR_REVIEW_STATUS,
            },
            {
                "check_id": "digest",
                "description": "Confirm generated digest can be reviewed against local bytes.",
                "operator_review_status": OPERATOR_REVIEW_STATUS,
            },
            {
                "check_id": "field_inventory",
                "description": "Confirm declared field names exist without copying source values.",
                "operator_review_status": OPERATOR_REVIEW_STATUS,
            },
        ],
        "runner_state": LEDGER_ROW_STATE,
        "snapshot_id": "fixture_airport_station_observation_log_2026_05_09",
        "source_domain": "weather_observation",
        "source_id": "airport_station_observation_log",
        "source_label": "Airport station observation log",
        "source_type": "station_observation_snapshot",
    }


def test_source_evidence_inventory_ledger_is_deterministic_for_same_request() -> None:
    request = load_source_evidence_inventory_request(VALID_REQUEST_PATH)

    first = build_source_evidence_inventory_ledger(request)
    second = build_source_evidence_inventory_ledger(deepcopy(request))

    assert first == second
    assert first["build_id"] == "source_evidence_inventory_ledger_fixture_001-911f62d75877"


def test_static_sample_matches_source_evidence_builder_output() -> None:
    request = load_source_evidence_inventory_request(VALID_REQUEST_PATH)
    sample = json.loads(Path(SAMPLE_LEDGER_PATH).read_text(encoding="utf-8"))

    assert build_source_evidence_inventory_ledger(request) == sample


def test_static_sample_validates_as_source_evidence_inventory_ledger() -> None:
    sample = json.loads(Path(SAMPLE_LEDGER_PATH).read_text(encoding="utf-8"))

    validation = validate_source_evidence_inventory_ledger(sample)

    assert validation.valid is True
    assert validation.errors == ()


def test_static_markdown_sample_matches_report_builder_output() -> None:
    sample = json.loads(Path(SAMPLE_LEDGER_PATH).read_text(encoding="utf-8"))
    sample_report = Path(SAMPLE_OPERATOR_REPORT_PATH).read_text(encoding="utf-8")

    assert build_operator_report(sample) == sample_report


def test_cli_writes_local_source_evidence_inventory_and_operator_report(tmp_path: Path) -> None:
    ledger_path = tmp_path / "source_evidence_inventory_ledger.json"
    report_path = tmp_path / "source_evidence_inventory_ledger.md"

    exit_code = main(
        [
            "--request",
            str(VALID_REQUEST_PATH),
            "--output-ledger",
            str(ledger_path),
            "--output-report",
            str(report_path),
        ]
    )

    assert exit_code == 0
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    report = report_path.read_text(encoding="utf-8")
    assert ledger["contract_version"] == LEDGER_CONTRACT_VERSION
    assert ledger["errors"] == []
    assert ledger["warnings"] == []
    assert "# PMBOT Source Evidence Inventory Ledger" in report
    assert "official_daily_climate_report" in report
    assert "Records file presence, digests, field names, and review state only." in report
    assert "Not execution approval and not runtime input." in report


def test_ledger_validation_rejects_digest_or_byte_count_drift() -> None:
    sample = json.loads(Path(SAMPLE_LEDGER_PATH).read_text(encoding="utf-8"))
    sample["source_evidence_rows"][0]["content_sha256"] = "0" * 64
    sample["source_evidence_rows"][0]["byte_count"] = 1

    validation = validate_source_evidence_inventory_ledger(sample)

    assert validation.valid is False
    assert any("content_sha256 must match local artifact bytes" in error for error in validation.errors)
    assert any("byte_count must match local artifact bytes" in error for error in validation.errors)


def test_request_rejects_network_like_source_reference() -> None:
    request = load_source_evidence_inventory_request(VALID_REQUEST_PATH)
    request["source_artifacts"][0]["local_reference"] = "https://example.invalid/source.json"

    validation = validate_source_evidence_inventory_request(request)

    assert validation.valid is False
    assert any("local_reference must point to a local fixture or static artifact" in error for error in validation.errors)
    with pytest.raises(SourceQualityLedgerValidationError):
        build_source_evidence_inventory_ledger(request)


def test_request_rejects_forbidden_source_evidence_terms() -> None:
    request = load_source_evidence_inventory_request(VALID_REQUEST_PATH)
    request["source_artifacts"][0]["forecast_score"] = "not allowed in local evidence inventory"

    validation = validate_source_evidence_inventory_request(request)

    assert validation.valid is False
    assert any("forbidden source evidence term detected" in error for error in validation.errors)


def test_request_rejects_missing_declared_field() -> None:
    request = load_source_evidence_inventory_request(VALID_REQUEST_PATH)
    request["source_artifacts"][0]["expected_top_level_fields"].append("missing_fixture_field")

    validation = validate_source_evidence_inventory_request(request)

    assert validation.valid is False
    assert any("references fields missing from local artifact: missing_fixture_field" in error for error in validation.errors)
    with pytest.raises(SourceQualityLedgerValidationError):
        build_source_evidence_inventory_ledger(request)


def test_ledger_rejects_summary_mismatch_and_non_review_state() -> None:
    sample = json.loads(Path(SAMPLE_LEDGER_PATH).read_text(encoding="utf-8"))
    sample["summary_counts"]["fields_present"] = 99
    sample["source_evidence_rows"][0]["operator_review_status"] = "accepted_without_review"

    validation = validate_source_evidence_inventory_ledger(sample)

    assert validation.valid is False
    assert any("summary_counts must match source_evidence_rows totals" in error for error in validation.errors)
    assert any(
        "source_evidence_rows[0].operator_review_status must be pending_operator_review" in error
        for error in validation.errors
    )


def test_output_contract_has_no_forecast_scoring_or_selection_terms() -> None:
    request = load_source_evidence_inventory_request(VALID_REQUEST_PATH)
    ledger = build_source_evidence_inventory_ledger(request)

    assert _find_output_decision_terms(ledger) == []


def test_source_evidence_inventory_documentation_registers_local_artifacts() -> None:
    document = DOC_PATH.read_text(encoding="utf-8")

    assert "Task: `PMBOT-SOURCE-EVIDENCE-001-SOURCE-INVENTORY-LEDGER-LOCAL-ONLY`" in document
    assert f"Contract: `{LEDGER_CONTRACT_VERSION}`" in document
    assert f"Run mode: `{LEDGER_RUN_MODE}`" in document
    assert VALID_REQUEST_REFERENCE in document
    assert SAMPLE_LEDGER_PATH in document
    assert SAMPLE_OPERATOR_REPORT_PATH in document
    assert "This ledger is not execution approval and is not runtime input." in document


def test_request_contract_version_is_explicit() -> None:
    request = load_source_evidence_inventory_request(VALID_REQUEST_PATH)

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
