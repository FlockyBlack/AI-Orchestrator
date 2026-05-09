from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from pm_bot.source_quality.source_staleness_check_spec import (
    CHECK_ROW_STATE,
    EXPECTED_SAFETY_BOUNDARIES,
    OPERATOR_REVIEW_STATUS,
    REQUEST_CONTRACT_VERSION,
    SAMPLE_OPERATOR_REPORT_PATH,
    SAMPLE_SPEC_PATH,
    SPEC_CONTRACT_VERSION,
    SPEC_RUN_MODE,
    SourceQualityLedgerValidationError,
    build_operator_report,
    build_source_staleness_check_spec,
    load_source_staleness_check_spec_request,
    main,
    validate_source_staleness_check_spec,
    validate_source_staleness_check_spec_request,
)

DOC_PATH = Path("docs/PMBOT_SOURCE_EVIDENCE_003_SOURCE_STALENESS_CHECK_SPEC_LOCAL_ONLY.md")
VALID_REQUEST_REFERENCE = "pm_bot/tests/fixtures/source_quality/source_staleness_check_spec_request.valid.json"
VALID_REQUEST_PATH = Path(VALID_REQUEST_REFERENCE)


def test_valid_request_builds_source_staleness_check_spec() -> None:
    request = load_source_staleness_check_spec_request(VALID_REQUEST_PATH)
    validation = validate_source_staleness_check_spec_request(request)
    spec = build_source_staleness_check_spec(request)

    assert validation.valid is True
    assert validation.errors == ()
    assert spec["contract_version"] == SPEC_CONTRACT_VERSION
    assert spec["spec_id"] == "source_staleness_check_spec_fixture_001"
    assert spec["run_mode"] == SPEC_RUN_MODE
    assert spec["local_only"] is True
    assert spec["operator_review_required"] is True
    assert spec["operator_review"]["status"] == OPERATOR_REVIEW_STATUS
    assert spec["safety_boundaries"] == EXPECTED_SAFETY_BOUNDARIES
    assert spec["reference_clock"] == {
        "reference_source": "request_fixture_static_value",
        "reference_timestamp_utc": "2026-05-10T00:30:00Z",
        "system_clock_used": False,
    }
    assert spec["summary_counts"] == {
        "local_references": 7,
        "operator_review_steps": 3,
        "review_checks": 16,
        "source_artifact_references": 4,
        "source_evidence_links": 4,
        "source_staleness_checks": 4,
        "timestamp_fields_missing": 1,
        "timestamp_fields_present": 3,
        "warnings": 0,
    }
    assert [row["source_id"] for row in spec["source_staleness_checks"]] == [
        "airport_station_observation_log",
        "official_daily_climate_report",
        "static_crypto_reference_snapshot_2026_05_09_btc",
        "unified_source_quality_ledger_sample",
    ]
    first = spec["source_staleness_checks"][0]
    assert first["check_id"] == "source_staleness_check_spec_fixture_001.airport_station_observation_log.source_staleness_check"
    assert first["check_state"] == CHECK_ROW_STATE
    assert first["source_evidence_link_id"] == (
        "source_evidence_link_map_fixture_001.airport_station_observation_log.source_evidence_link"
    )
    assert first["source_artifact"] == {
        "artifact_format": "json_object",
        "byte_count": 536,
        "content_sha256": "e27ccc4dedeb4b3da48cd9e636d137e78be3cefa9683598879b2aed122370a8c",
        "local_reference": "pm_bot/tests/fixtures/weather/airport_station_observation_log_snapshot.json",
        "present": True,
        "source_artifact_present": True,
    }
    assert first["timestamp_field"] == "observation_timestamp"
    assert first["observed_timestamp_utc"] == "2026-05-09T23:58:00Z"
    assert first["age_seconds"] == 1920
    assert first["maximum_age_seconds"] == 86400
    assert first["staleness_state"] == "within_static_review_window"
    assert len(first["review_checks"]) == 4
    assert all(check["operator_review_status"] == OPERATOR_REVIEW_STATUS for check in first["review_checks"])


def test_source_staleness_check_spec_is_deterministic_for_same_request() -> None:
    request = load_source_staleness_check_spec_request(VALID_REQUEST_PATH)

    first = build_source_staleness_check_spec(request)
    second = build_source_staleness_check_spec(deepcopy(request))

    assert first == second
    assert first["build_id"] == "source_staleness_check_spec_fixture_001-6d7b66d4f994"


def test_static_sample_matches_source_staleness_check_spec_builder_output() -> None:
    request = load_source_staleness_check_spec_request(VALID_REQUEST_PATH)
    sample = json.loads(Path(SAMPLE_SPEC_PATH).read_text(encoding="utf-8"))

    assert build_source_staleness_check_spec(request) == sample


def test_static_sample_validates_as_source_staleness_check_spec() -> None:
    sample = json.loads(Path(SAMPLE_SPEC_PATH).read_text(encoding="utf-8"))

    validation = validate_source_staleness_check_spec(sample)

    assert validation.valid is True
    assert validation.errors == ()


def test_static_markdown_sample_matches_report_builder_output() -> None:
    sample = json.loads(Path(SAMPLE_SPEC_PATH).read_text(encoding="utf-8"))
    sample_report = Path(SAMPLE_OPERATOR_REPORT_PATH).read_text(encoding="utf-8")

    assert build_operator_report(sample) == sample_report


def test_cli_writes_local_source_staleness_check_spec_and_operator_report(tmp_path: Path) -> None:
    spec_path = tmp_path / "source_staleness_check_spec.json"
    report_path = tmp_path / "source_staleness_check_spec.md"

    exit_code = main(
        [
            "--request",
            str(VALID_REQUEST_PATH),
            "--output-spec",
            str(spec_path),
            "--output-report",
            str(report_path),
        ]
    )

    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    report = report_path.read_text(encoding="utf-8")
    assert exit_code == 0
    assert spec["contract_version"] == SPEC_CONTRACT_VERSION
    assert spec["errors"] == []
    assert spec["warnings"] == []
    assert "# PMBOT Source Staleness Check Spec" in report
    assert "airport_station_observation_log" in report
    assert "Uses the request fixture reference timestamp, not the system clock." in report
    assert "Does not authorize execution and is not runtime input." in report


def test_request_rejects_network_like_link_map_reference() -> None:
    request = load_source_staleness_check_spec_request(VALID_REQUEST_PATH)
    request["source_evidence_link_map_reference"] = "https://example.invalid/source_evidence_link_map.json"

    validation = validate_source_staleness_check_spec_request(request)

    assert validation.valid is False
    assert any("local_reference must point to a local fixture or static artifact" in error for error in validation.errors)
    with pytest.raises(SourceQualityLedgerValidationError):
        build_source_staleness_check_spec(request)


def test_request_rejects_missing_source_rule() -> None:
    request = load_source_staleness_check_spec_request(VALID_REQUEST_PATH)
    request["source_staleness_rules"] = request["source_staleness_rules"][:-1]

    validation = validate_source_staleness_check_spec_request(request)

    assert validation.valid is False
    assert any("source_id set must match source_evidence_link_map sources" in error for error in validation.errors)


def test_spec_validation_rejects_digest_or_link_row_drift() -> None:
    sample = json.loads(Path(SAMPLE_SPEC_PATH).read_text(encoding="utf-8"))
    sample["source_staleness_checks"][0]["source_artifact"]["content_sha256"] = "0" * 64
    sample["source_staleness_checks"][0]["source_evidence_link_id"] = "wrong.local.link"

    validation = validate_source_staleness_check_spec(sample)

    assert validation.valid is False
    assert any("content_sha256 must match local bytes" in error for error in validation.errors)
    assert any("source_evidence_link_id must match source evidence link map row" in error for error in validation.errors)


def test_spec_validation_rejects_age_or_timestamp_state_drift() -> None:
    sample = json.loads(Path(SAMPLE_SPEC_PATH).read_text(encoding="utf-8"))
    sample["source_staleness_checks"][0]["age_seconds"] = 1
    sample["source_staleness_checks"][0]["staleness_state"] = "timestamp_field_missing"

    validation = validate_source_staleness_check_spec(sample)

    assert validation.valid is False
    assert any("age_seconds must match observed and reference timestamps" in error for error in validation.errors)
    assert any("staleness_state must be within_static_review_window" in error for error in validation.errors)


def test_output_contract_has_no_forecast_scoring_or_selection_terms() -> None:
    request = load_source_staleness_check_spec_request(VALID_REQUEST_PATH)
    spec = build_source_staleness_check_spec(request)

    assert _find_output_decision_terms(spec) == []


def test_source_staleness_check_spec_documentation_registers_local_artifacts() -> None:
    document = DOC_PATH.read_text(encoding="utf-8")

    assert "Task: `PMBOT-SOURCE-EVIDENCE-003-SOURCE-STALENESS-CHECK-SPEC-LOCAL-ONLY`" in document
    assert f"Contract: `{SPEC_CONTRACT_VERSION}`" in document
    assert f"Run mode: `{SPEC_RUN_MODE}`" in document
    assert VALID_REQUEST_REFERENCE in document
    assert SAMPLE_SPEC_PATH in document
    assert SAMPLE_OPERATOR_REPORT_PATH in document
    assert "This spec is not execution approval and is not runtime input." in document


def test_request_contract_version_is_explicit() -> None:
    request = load_source_staleness_check_spec_request(VALID_REQUEST_PATH)

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
