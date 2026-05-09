from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

from pm_bot.source_quality.crypto_source_contradiction_ledger import (
    CONTRADICTION_ROW_STATE,
    EXPECTED_SAFETY_BOUNDARIES,
    LEDGER_CONTRACT_VERSION,
    LEDGER_DOCUMENTATION_PATH,
    LEDGER_ID,
    LEDGER_RUN_MODE,
    MATCHING_STATIC_VALUES,
    NO_STATIC_DIFFERENCE_RECORDED,
    OPERATOR_REVIEW_STATUS,
    REQUIRED_VALIDATION_COMMANDS,
    SAMPLE_LEDGER_PATH,
    SAMPLE_OPERATOR_REPORT_PATH,
    SAMPLE_SPEC_PATH,
    TASK_ID,
    build_crypto_source_contradiction_ledger,
    build_operator_report,
    load_crypto_source_contradiction_ledger,
    load_crypto_source_staleness_check_spec,
    main,
    validate_crypto_source_contradiction_ledger,
)

DOC_PATH = Path(LEDGER_DOCUMENTATION_PATH)
LEDGER_PATH = Path(SAMPLE_LEDGER_PATH)
REPORT_PATH = Path(SAMPLE_OPERATOR_REPORT_PATH)


def test_crypto_source_contradiction_ledger_builds_from_crypto_staleness_spec() -> None:
    staleness_spec = load_crypto_source_staleness_check_spec(SAMPLE_SPEC_PATH)
    ledger = build_crypto_source_contradiction_ledger(staleness_spec)
    validation = validate_crypto_source_contradiction_ledger(ledger)

    assert validation.valid is True
    assert validation.errors == ()
    assert ledger["task_id"] == TASK_ID
    assert ledger["ledger_id"] == LEDGER_ID
    assert ledger["contract_version"] == LEDGER_CONTRACT_VERSION
    assert ledger["run_mode"] == LEDGER_RUN_MODE
    assert ledger["created_at"] == "2026-05-09T01:40:00Z"
    assert ledger["local_only"] is True
    assert ledger["operator_review_required"] is True
    assert ledger["operator_review"]["status"] == OPERATOR_REVIEW_STATUS
    assert ledger["safety_boundaries"] == EXPECTED_SAFETY_BOUNDARIES
    assert ledger["required_validation_commands"] == list(REQUIRED_VALIDATION_COMMANDS)
    assert ledger["summary_counts"] == {
        "different_field_comparisons": 0,
        "field_comparisons": 33,
        "local_references": 8,
        "matching_field_comparisons": 33,
        "operator_review_steps": 3,
        "required_validation_commands": 2,
        "review_checks": 16,
        "source_artifact_references": 5,
        "source_contradiction_rows": 4,
        "source_record_pairs": 4,
        "source_staleness_checks": 5,
        "subject_key_comparisons": 6,
        "subject_key_differences": 0,
        "warnings": 0,
    }

    first = ledger["source_contradiction_rows"][0]
    assert first["row_id"] == (
        "pmbot-crypto-source-contradiction-ledger-001."
        "read_only_contract_to_reference_snapshot_static_copy.crypto_source_contradiction_review"
    )
    assert first["row_state"] == CONTRADICTION_ROW_STATE
    assert first["contradiction_state"] == NO_STATIC_DIFFERENCE_RECORDED
    assert first["left_source"]["source_id"] == "read_only_crypto_data_contract_fixture"
    assert first["left_source"]["source_record_selector"] == "$.static_sample_records[0]"
    assert first["right_source"]["source_id"] == "static_crypto_reference_snapshot_2026_05_09_btc"
    assert first["right_source"]["source_record_selector"] == "$"
    assert first["field_comparisons"][0] == {
        "comparison_state": MATCHING_STATIC_VALUES,
        "left_field": "asset_name",
        "left_field_present": True,
        "left_value": "Bitcoin",
        "operator_review_status": OPERATOR_REVIEW_STATUS,
        "right_field": "asset_name",
        "right_field_present": True,
        "right_value": "Bitcoin",
        "semantic_field": "asset_name",
        "unit_label": "static_text",
        "values_match": True,
    }
    assert len(first["review_checks"]) == 4
    assert all(check["operator_review_status"] == OPERATOR_REVIEW_STATUS for check in first["review_checks"])


def test_crypto_source_contradiction_ledger_is_deterministic() -> None:
    staleness_spec = load_crypto_source_staleness_check_spec(SAMPLE_SPEC_PATH)

    first = build_crypto_source_contradiction_ledger(staleness_spec)
    second = build_crypto_source_contradiction_ledger(deepcopy(staleness_spec))

    assert first == second
    assert first["build_id"] == "pmbot-crypto-source-contradiction-ledger-001-7caf57862990"


def test_static_sample_matches_crypto_source_contradiction_builder_output() -> None:
    staleness_spec = load_crypto_source_staleness_check_spec(SAMPLE_SPEC_PATH)

    assert build_crypto_source_contradiction_ledger(staleness_spec) == _load_ledger()


def test_static_sample_validates_as_crypto_source_contradiction_ledger() -> None:
    validation = validate_crypto_source_contradiction_ledger(_load_ledger())

    assert validation.valid is True
    assert validation.errors == ()


def test_static_markdown_sample_matches_crypto_contradiction_report_builder_output() -> None:
    report = REPORT_PATH.read_text(encoding="utf-8")

    assert build_operator_report(_load_ledger()) == report


def test_cli_writes_crypto_source_contradiction_ledger_and_operator_report(tmp_path: Path) -> None:
    ledger_path = tmp_path / "crypto_source_contradiction_ledger.json"
    report_path = tmp_path / "crypto_source_contradiction_ledger.md"

    exit_code = main(
        [
            "--staleness-spec",
            SAMPLE_SPEC_PATH,
            "--output-ledger",
            str(ledger_path),
            "--output-report",
            str(report_path),
        ]
    )

    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    report = report_path.read_text(encoding="utf-8")
    assert exit_code == 0
    assert ledger == _load_ledger()
    assert "# PMBOT Crypto Source Contradiction Ledger" in report
    assert "Records descriptive source copy checks and pending review state only." in report
    assert "Not execution approval and not runtime input." in report


def test_validation_rejects_digest_or_static_value_drift() -> None:
    ledger = _load_ledger()
    row = ledger["source_contradiction_rows"][0]
    row["left_source"]["source_artifact"]["content_sha256"] = "0" * 64
    row["field_comparisons"][0]["right_value"] = "Ether"

    validation = validate_crypto_source_contradiction_ledger(ledger)

    assert validation.valid is False
    assert any("content_sha256 must match local bytes" in error for error in validation.errors)
    assert any("right_value must match right source record" in error for error in validation.errors)


def test_validation_rejects_missing_fixed_crypto_source_pair() -> None:
    ledger = _load_ledger()
    ledger["source_contradiction_rows"] = ledger["source_contradiction_rows"][:-1]

    validation = validate_crypto_source_contradiction_ledger(ledger)

    assert validation.valid is False
    assert any("one row per fixed crypto source pair" in error for error in validation.errors)


def test_crypto_source_contradiction_ledger_has_no_decision_scoring_or_selection_terms() -> None:
    assert _find_disallowed_terms(_load_ledger()) == []


def test_documentation_registers_crypto_source_contradiction_artifacts() -> None:
    document = DOC_PATH.read_text(encoding="utf-8")

    assert f"Task: `{TASK_ID}`" in document
    assert f"Ledger: `{LEDGER_ID}`" in document
    assert f"Contract: `{LEDGER_CONTRACT_VERSION}`" in document
    assert f"Run mode: `{LEDGER_RUN_MODE}`" in document
    assert SAMPLE_SPEC_PATH in document
    assert SAMPLE_LEDGER_PATH in document
    assert SAMPLE_OPERATOR_REPORT_PATH in document
    assert "No forecast scoring, action guidance, market ranking" in document
    assert "This ledger is not execution approval and is not runtime input." in document


def _load_ledger() -> dict:
    return load_crypto_source_contradiction_ledger(LEDGER_PATH)


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
