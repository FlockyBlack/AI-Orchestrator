from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

from pm_bot.source_quality.crypto_source_staleness_check_spec import (
    CHECK_ROW_STATE,
    EXPECTED_SAFETY_BOUNDARIES,
    EXPECTED_SOURCE_IDS,
    OPERATOR_REVIEW_STATUS,
    REFERENCE_TIMESTAMP_UTC,
    REQUIRED_VALIDATION_COMMANDS,
    SAMPLE_LINK_MAP_PATH,
    SAMPLE_OPERATOR_REPORT_PATH,
    SAMPLE_SPEC_PATH,
    SPEC_CONTRACT_VERSION,
    SPEC_ID,
    SPEC_RUN_MODE,
    TASK_ID,
    build_crypto_source_staleness_check_spec,
    build_operator_report,
    load_crypto_source_evidence_link_map,
    load_crypto_source_staleness_check_spec,
    main,
    validate_crypto_source_staleness_check_spec,
)

DOC_PATH = Path("docs/PMBOT_CRYPTO_LIVE_004_CRYPTO_SOURCE_STALENESS_CHECK_SPEC_LOCAL_ONLY.md")
SPEC_PATH = Path(SAMPLE_SPEC_PATH)
REPORT_PATH = Path(SAMPLE_OPERATOR_REPORT_PATH)


def test_crypto_source_staleness_check_spec_builds_from_crypto_link_map() -> None:
    link_map = load_crypto_source_evidence_link_map(SAMPLE_LINK_MAP_PATH)
    spec = build_crypto_source_staleness_check_spec(link_map)
    validation = validate_crypto_source_staleness_check_spec(spec)

    assert validation.valid is True
    assert validation.errors == ()
    assert spec["task_id"] == TASK_ID
    assert spec["spec_id"] == SPEC_ID
    assert spec["contract_version"] == SPEC_CONTRACT_VERSION
    assert spec["run_mode"] == SPEC_RUN_MODE
    assert spec["created_at"] == "2026-05-09T01:20:00Z"
    assert spec["local_only"] is True
    assert spec["operator_review_required"] is True
    assert spec["operator_review"]["status"] == OPERATOR_REVIEW_STATUS
    assert spec["safety_boundaries"] == EXPECTED_SAFETY_BOUNDARIES
    assert spec["required_validation_commands"] == list(REQUIRED_VALIDATION_COMMANDS)
    assert spec["reference_clock"] == {
        "reference_source": "static_fixture_reference_time",
        "reference_timestamp_utc": REFERENCE_TIMESTAMP_UTC,
        "system_clock_used": False,
    }
    assert spec["summary_counts"] == {
        "local_references": 15,
        "operator_review_steps": 3,
        "required_validation_commands": 2,
        "review_checks": 24,
        "source_artifact_references": 6,
        "source_contract_references": 6,
        "source_evidence_links": 6,
        "source_inventory_records": 6,
        "source_staleness_checks": 6,
        "timestamp_fields_missing": 0,
        "timestamp_fields_present": 6,
        "warnings": 0,
    }
    assert tuple(row["source_id"] for row in spec["source_staleness_checks"]) == EXPECTED_SOURCE_IDS

    first = spec["source_staleness_checks"][0]
    assert first["check_id"] == (
        "pmbot-crypto-source-staleness-check-spec-001."
        "read_only_crypto_data_contract_fixture.crypto_source_staleness_check"
    )
    assert first["check_state"] == CHECK_ROW_STATE
    assert first["source_evidence_link_id"] == (
        "pmbot-crypto-source-evidence-link-map-001."
        "read_only_crypto_data_contract_fixture.crypto_source_evidence_link"
    )
    assert first["timestamp_field_path"] == "$.created_at"
    assert first["observed_timestamp_utc"] == "2026-05-09T00:40:00Z"
    assert first["age_seconds"] == 3000
    assert first["maximum_age_seconds"] == 172800
    assert first["staleness_state"] == "within_static_review_window"
    assert first["source_artifact"] == {
        "artifact_format": "json_object",
        "byte_count": 15250,
        "content_sha256": "c6376ad29238c3ac64418a6efaf993a56bc34c8f2430bbff24c60cd8316b4a71",
        "local_reference": "pm_bot/tests/fixtures/crypto_live/pmbot_read_only_crypto_data_contract.valid.json",
        "present": True,
        "source_artifact_present": True,
    }
    assert len(first["review_checks"]) == 4
    assert all(check["operator_review_status"] == OPERATOR_REVIEW_STATUS for check in first["review_checks"])


def test_crypto_source_staleness_check_spec_is_deterministic() -> None:
    link_map = load_crypto_source_evidence_link_map(SAMPLE_LINK_MAP_PATH)

    first = build_crypto_source_staleness_check_spec(link_map)
    second = build_crypto_source_staleness_check_spec(deepcopy(link_map))

    assert first == second
    assert first["build_id"] == "pmbot-crypto-source-staleness-check-spec-001-8d78439513d2"


def test_static_sample_matches_crypto_source_staleness_builder_output() -> None:
    link_map = load_crypto_source_evidence_link_map(SAMPLE_LINK_MAP_PATH)

    assert build_crypto_source_staleness_check_spec(link_map) == _load_spec()


def test_static_sample_validates_as_crypto_source_staleness_spec() -> None:
    validation = validate_crypto_source_staleness_check_spec(_load_spec())

    assert validation.valid is True
    assert validation.errors == ()


def test_static_markdown_sample_matches_operator_report_builder_output() -> None:
    report = REPORT_PATH.read_text(encoding="utf-8")

    assert build_operator_report(_load_spec()) == report


def test_cli_writes_crypto_source_staleness_spec_and_operator_report(tmp_path: Path) -> None:
    spec_path = tmp_path / "crypto_source_staleness_check_spec.json"
    report_path = tmp_path / "crypto_source_staleness_check_spec.md"

    exit_code = main(
        [
            "--link-map",
            SAMPLE_LINK_MAP_PATH,
            "--output-spec",
            str(spec_path),
            "--output-report",
            str(report_path),
        ]
    )

    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    report = report_path.read_text(encoding="utf-8")
    assert exit_code == 0
    assert spec == _load_spec()
    assert "# PMBOT Crypto Source Staleness Check Spec" in report
    assert "Uses the fixed fixture reference timestamp, not the system clock." in report
    assert "Does not authorize execution and is not runtime input." in report


def test_validation_rejects_digest_or_timestamp_drift() -> None:
    spec = _load_spec()
    spec["source_staleness_checks"][0]["source_artifact"]["content_sha256"] = "0" * 64
    spec["source_staleness_checks"][0]["age_seconds"] = 1

    validation = validate_crypto_source_staleness_check_spec(spec)

    assert validation.valid is False
    assert any("content_sha256 must match local bytes" in error for error in validation.errors)
    assert any("age_seconds must match observed timestamp and fixed reference clock" in error for error in validation.errors)


def test_validation_rejects_missing_crypto_source_row() -> None:
    spec = _load_spec()
    spec["source_staleness_checks"] = spec["source_staleness_checks"][:-1]

    validation = validate_crypto_source_staleness_check_spec(spec)

    assert validation.valid is False
    assert any("one row per fixed crypto source" in error for error in validation.errors)


def test_crypto_source_staleness_spec_has_no_decision_scoring_or_selection_terms() -> None:
    assert _find_disallowed_terms(_load_spec()) == []


def test_documentation_registers_crypto_source_staleness_artifacts() -> None:
    document = DOC_PATH.read_text(encoding="utf-8")

    assert f"Task: `{TASK_ID}`" in document
    assert f"Spec: `{SPEC_ID}`" in document
    assert f"Contract: `{SPEC_CONTRACT_VERSION}`" in document
    assert f"Run mode: `{SPEC_RUN_MODE}`" in document
    assert SAMPLE_LINK_MAP_PATH in document
    assert SAMPLE_SPEC_PATH in document
    assert SAMPLE_OPERATOR_REPORT_PATH in document
    assert "No forecast scoring, action guidance, market ranking" in document
    assert "This spec is not execution approval and is not runtime input." in document


def _load_spec() -> dict:
    return load_crypto_source_staleness_check_spec(SPEC_PATH)


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
