from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

from pm_bot.source_quality.crypto_source_quality_capture_surface import (
    CAPTURE_SURFACE_CONTRACT_VERSION,
    CAPTURE_SURFACE_RUN_MODE,
    CRYPTO_CAPTURE_FIXTURE_PATH,
    CRYPTO_OBSERVATION_LEDGER_FIXTURE_PATH,
    CRYPTO_PROTOCOL_FIXTURE_PATH,
    CRYPTO_REFERENCE_SNAPSHOT_FIXTURE_PATH,
    EXPECTED_CAPTURE_SURFACE_FIELDS,
    EXPECTED_CAPTURE_SURFACE_SAFETY_BOUNDARIES,
    SAMPLE_CAPTURE_SURFACE_PATH,
    SAMPLE_OPERATOR_REPORT_PATH,
    TASK_ID,
    build_crypto_source_quality_capture_surface,
    build_operator_report,
    load_crypto_source_artifacts,
    load_crypto_source_quality_capture_surface,
    main,
    validate_crypto_source_quality_capture_surface,
)

DOC_PATH = Path("docs/PMBOT_CRYPTO_PILOT_004_CRYPTO_SOURCE_QUALITY_CAPTURE_SURFACE_LOCAL_ONLY.md")
SURFACE_PATH = Path(SAMPLE_CAPTURE_SURFACE_PATH)
REPORT_PATH = Path(SAMPLE_OPERATOR_REPORT_PATH)


def test_static_crypto_source_quality_capture_surface_has_expected_contract() -> None:
    surface = _load_surface()

    assert tuple(surface.keys()) == tuple(sorted(surface.keys()))
    assert surface["task_id"] == TASK_ID
    assert surface["capture_surface_id"] == "crypto_source_quality_capture_surface_001"
    assert surface["build_id"] == "crypto_source_quality_capture_surface_001-e3588b6b1073"
    assert surface["contract_version"] == CAPTURE_SURFACE_CONTRACT_VERSION
    assert surface["run_mode"] == CAPTURE_SURFACE_RUN_MODE
    assert surface["created_at"] == "2026-05-09T00:30:00Z"
    assert surface["local_only"] is True
    assert surface["operator_review_required"] is True
    assert surface["operator_review"]["status"] == "pending_operator_review"
    assert surface["record_state"] == "surface_only_static_sample"
    assert surface["errors"] == []
    assert surface["warnings"] == []


def test_capture_surface_records_are_fixed_and_descriptive() -> None:
    surface = _load_surface()
    first_record = surface["quality_capture_records"][0]

    assert tuple(surface["capture_surface_fields"]) == EXPECTED_CAPTURE_SURFACE_FIELDS
    assert set(first_record) == set(EXPECTED_CAPTURE_SURFACE_FIELDS)
    assert first_record == {
        "contract_check": "expected_contract_visible",
        "contract_version": "pmbot_crypto_market_class_capture_template.v1",
        "copy_lineage_check": "static_capture_fixture_retained",
        "field_presence_check": "all_required_fields_visible",
        "local_reference": CRYPTO_CAPTURE_FIXTURE_PATH,
        "local_reference_check": "relative_local_fixture_path",
        "missing_fields": [],
        "operator_notes": "Static sample for source quality capture surface only.",
        "operator_review_status": "pending_operator_review",
        "present_fields": [
            "contract_version",
            "template_id",
            "template_name",
            "capture_fields",
            "market_class_catalog",
            "sample_records",
            "operator_review",
            "summary_counts",
        ],
        "record_id": "crypto_source_quality_capture_surface_001.crypto_market_class_capture_template_001.quality_capture",
        "required_fields": [
            "contract_version",
            "template_id",
            "template_name",
            "capture_fields",
            "market_class_catalog",
            "sample_records",
            "operator_review",
            "summary_counts",
        ],
        "source_artifact_id": "crypto_market_class_capture_template_001",
        "source_artifact_label": "Crypto market class capture template",
        "source_artifact_role": "market_class_capture_template",
    }
    for record in surface["quality_capture_records"]:
        assert record["operator_review_status"] == "pending_operator_review"
        assert record["present_fields"] == record["required_fields"]
        assert record["missing_fields"] == []


def test_static_crypto_source_quality_capture_surface_matches_builder_output() -> None:
    artifacts = load_crypto_source_artifacts()
    surface = build_crypto_source_quality_capture_surface(artifacts)

    assert surface == _load_surface()


def test_crypto_source_quality_capture_surface_is_deterministic_for_same_inputs() -> None:
    artifacts = load_crypto_source_artifacts()

    first = build_crypto_source_quality_capture_surface(artifacts)
    second = build_crypto_source_quality_capture_surface(deepcopy(artifacts))

    assert first == second
    assert first["build_id"] == "crypto_source_quality_capture_surface_001-e3588b6b1073"


def test_static_surface_validates_as_crypto_source_quality_capture_artifact() -> None:
    surface = load_crypto_source_quality_capture_surface(SURFACE_PATH)

    validation = validate_crypto_source_quality_capture_surface(surface)

    assert validation.valid is True
    assert validation.errors == ()


def test_summary_counts_match_surface_content() -> None:
    surface = _load_surface()

    assert surface["summary_counts"] == {
        "capture_surface_fields": len(surface["capture_surface_fields"]),
        "input_artifacts": len(surface["input_artifacts"]),
        "missing_fields": 0,
        "operator_review_steps": len(surface["operator_review_steps"]),
        "present_fields": 35,
        "quality_capture_records": len(surface["quality_capture_records"]),
        "required_fields": 35,
        "warnings": len(surface["warnings"]),
    }


def test_surface_references_existing_local_crypto_fixtures() -> None:
    surface = _load_surface()
    expected_references = [
        CRYPTO_CAPTURE_FIXTURE_PATH,
        CRYPTO_OBSERVATION_LEDGER_FIXTURE_PATH,
        CRYPTO_PROTOCOL_FIXTURE_PATH,
        CRYPTO_REFERENCE_SNAPSHOT_FIXTURE_PATH,
    ]
    references = sorted(
        set(
            _collect_values_for_key(surface, "local_reference")
        )
    )

    assert references == sorted(expected_references)
    for artifact in surface["input_artifacts"]:
        loaded = json.loads(Path(artifact["local_reference"]).read_text(encoding="utf-8"))
        assert artifact["contract_version"] == loaded["contract_version"]
        assert set(artifact["required_fields"]).issubset(loaded)
        assert "://" not in artifact["local_reference"]
        assert artifact["local_reference"].startswith("pm_bot/tests/fixtures/")


def test_safety_boundaries_are_closed_for_crypto_source_quality_capture_surface() -> None:
    surface = _load_surface()

    assert surface["safety_boundaries"] == EXPECTED_CAPTURE_SURFACE_SAFETY_BOUNDARIES


def test_operator_report_sample_matches_report_builder_output() -> None:
    surface = _load_surface()
    report = REPORT_PATH.read_text(encoding="utf-8")

    assert build_operator_report(surface) == report
    assert "# PMBOT Crypto Source Quality Capture Surface" in report
    assert "Descriptive source quality capture only" in report
    assert "Not execution approval and not runtime input." in report


def test_cli_writes_local_crypto_source_quality_capture_surface(tmp_path: Path) -> None:
    surface_path = tmp_path / "crypto_source_quality_capture_surface.json"
    report_path = tmp_path / "crypto_source_quality_capture_surface.md"

    exit_code = main(
        [
            "--output-surface",
            str(surface_path),
            "--output-report",
            str(report_path),
        ]
    )

    surface = json.loads(surface_path.read_text(encoding="utf-8"))
    report = report_path.read_text(encoding="utf-8")
    assert exit_code == 0
    assert surface == _load_surface()
    assert "Operator review: `pending_operator_review`" in report


def test_validation_rejects_non_operator_review_state_and_count_drift() -> None:
    surface = _load_surface()
    surface["quality_capture_records"][0]["operator_review_status"] = "accepted_without_review"
    surface["summary_counts"]["present_fields"] = 999

    validation = validate_crypto_source_quality_capture_surface(surface)

    assert validation.valid is False
    assert any("operator_review_status must be pending_operator_review" in error for error in validation.errors)
    assert any("summary_counts must match capture surface totals" in error for error in validation.errors)


def test_validation_rejects_missing_field_drift() -> None:
    surface = _load_surface()
    surface["quality_capture_records"][0]["missing_fields"] = ["contract_version"]

    validation = validate_crypto_source_quality_capture_surface(surface)

    assert validation.valid is False
    assert any("missing_fields must be empty for the static local sample" in error for error in validation.errors)


def test_validation_rejects_input_artifact_record_alignment_drift() -> None:
    surface = _load_surface()
    surface["quality_capture_records"][0]["local_reference"] = CRYPTO_PROTOCOL_FIXTURE_PATH

    validation = validate_crypto_source_quality_capture_surface(surface)

    assert validation.valid is False
    assert any("must match input_artifacts row crypto_market_class_capture_template_001" in error for error in validation.errors)


def test_fixture_has_no_guidance_scoring_or_selection_fields() -> None:
    surface = _load_surface()

    assert _find_disallowed_terms(surface) == []


def test_documentation_registers_surface_contract_fixtures_and_safety_boundary() -> None:
    document = DOC_PATH.read_text(encoding="utf-8")

    assert f"Task: `{TASK_ID}`" in document
    assert "Surface: `crypto-source-quality-capture-surface`" in document
    assert f"Contract: `{CAPTURE_SURFACE_CONTRACT_VERSION}`" in document
    assert SAMPLE_CAPTURE_SURFACE_PATH in document
    assert SAMPLE_OPERATOR_REPORT_PATH in document
    assert CRYPTO_CAPTURE_FIXTURE_PATH in document
    assert CRYPTO_PROTOCOL_FIXTURE_PATH in document
    assert CRYPTO_OBSERVATION_LEDGER_FIXTURE_PATH in document
    assert CRYPTO_REFERENCE_SNAPSHOT_FIXTURE_PATH in document
    assert "No forecast scoring, action guidance, market ranking, or selection advice." in document
    assert "This surface is not execution approval and is not runtime input." in document


def _load_surface() -> dict:
    return json.loads(SURFACE_PATH.read_text(encoding="utf-8"))


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
