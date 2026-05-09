from __future__ import annotations

import json
from pathlib import Path


DOC_PATH = Path("docs/PMBOT_CRYPTO_PILOT_001_CRYPTO_MARKET_CLASS_CAPTURE_TEMPLATE_LOCAL_ONLY.md")
FIXTURE_PATH = Path(
    "pm_bot/tests/fixtures/crypto_market_class_capture/crypto_market_class_capture_template.valid.json"
)
TASK_ID = "PMBOT-CRYPTO-PILOT-001-CRYPTO-MARKET-CLASS-CAPTURE-TEMPLATE-LOCAL-ONLY"
CONTRACT_VERSION = "pmbot_crypto_market_class_capture_template.v1"
RUN_MODE = "local_descriptive_capture_template"
TEMPLATE_NAME = "crypto-market-class-capture"

EXPECTED_CAPTURE_FIELDS = (
    "record_id",
    "market_class",
    "market_slug",
    "market_title",
    "asset_symbol",
    "asset_name",
    "quote_currency",
    "metric_type",
    "measurement_source_label",
    "threshold_value",
    "threshold_unit",
    "comparison_rule",
    "deadline_utc",
    "source_snapshot_reference",
    "operator_notes",
    "capture_status",
)


def test_static_crypto_market_class_capture_fixture_has_expected_contract() -> None:
    template = _load_template()

    assert tuple(template.keys()) == tuple(sorted(template.keys()))
    assert template["task_id"] == TASK_ID
    assert template["template_name"] == TEMPLATE_NAME
    assert template["contract_version"] == CONTRACT_VERSION
    assert template["run_mode"] == RUN_MODE
    assert template["created_at"] == "2026-05-09T00:00:00Z"
    assert template["local_only"] is True
    assert template["operator_review_required"] is True
    assert template["operator_review"]["status"] == "pending_operator_review"
    assert template["errors"] == []
    assert template["warnings"] == []


def test_capture_fields_are_fixed_and_match_catalog_requirements() -> None:
    template = _load_template()
    catalog_entry = template["market_class_catalog"][0]

    assert tuple(template["capture_fields"]) == EXPECTED_CAPTURE_FIELDS
    assert tuple(catalog_entry["required_capture_fields"]) == EXPECTED_CAPTURE_FIELDS
    assert catalog_entry["class_id"] == "crypto_threshold_event"
    assert catalog_entry["review_focus"] == [
        "copy_market_text_exactly_from_local_snapshot",
        "confirm_measurement_label_is_descriptive",
        "confirm_deadline_timestamp_is_copied",
        "leave_capture_status_pending_operator_review",
    ]


def test_sample_record_is_descriptive_static_and_pending_operator_review() -> None:
    template = _load_template()
    sample = template["sample_records"][0]

    assert set(sample) == set(EXPECTED_CAPTURE_FIELDS)
    assert sample == {
        "asset_name": "Bitcoin",
        "asset_symbol": "BTC",
        "capture_status": "pending_operator_review",
        "comparison_rule": "at_or_above_threshold_by_deadline",
        "deadline_utc": "2026-12-31T23:59:59Z",
        "market_class": "crypto_threshold_event",
        "market_slug": "static-sample-btc-threshold-2026",
        "market_title": "Static sample BTC threshold market",
        "measurement_source_label": "local fixture index close label",
        "metric_type": "spot_index_threshold",
        "operator_notes": "Static sample for record shape only.",
        "quote_currency": "USD",
        "record_id": "crypto_market_class_capture_template_001.sample.btc_threshold",
        "source_snapshot_reference": str(FIXTURE_PATH).replace("\\", "/"),
        "threshold_unit": "USD",
        "threshold_value": "150000.00",
    }


def test_summary_counts_match_template_content() -> None:
    template = _load_template()

    assert template["summary_counts"] == {
        "capture_fields": len(template["capture_fields"]),
        "market_classes": len(template["market_class_catalog"]),
        "sample_records": len(template["sample_records"]),
        "warnings": len(template["warnings"]),
    }


def test_safety_boundaries_are_closed_for_local_capture_template() -> None:
    template = _load_template()

    assert template["safety_boundaries"] == {
        "authenticated_endpoint_calls_allowed": False,
        "background_process_allowed": False,
        "browser_automation_allowed": False,
        "external_market_api_calls_allowed": False,
        "local_static_samples_only": True,
        "network_calls_allowed": False,
        "operator_review_required": True,
        "runtime_or_dispatcher_changes_allowed": False,
        "transaction_endpoint_calls_allowed": False,
        "wallet_or_signing_material_access_allowed": False,
    }


def test_template_references_only_local_static_paths() -> None:
    template = _load_template()
    references = _collect_values_for_key(template, "source_snapshot_reference")

    assert references == [str(FIXTURE_PATH).replace("\\", "/")]
    for reference in references:
        assert "://" not in reference
        assert reference.startswith("pm_bot/tests/fixtures/crypto_market_class_capture/")


def test_fixture_has_no_guidance_scoring_or_selection_fields() -> None:
    template = _load_template()

    assert _find_disallowed_terms(template) == []


def test_documentation_registers_template_contract_fixture_and_safety_boundary() -> None:
    document = DOC_PATH.read_text(encoding="utf-8")

    assert f"Task: `{TASK_ID}`" in document
    assert f"Template: `{TEMPLATE_NAME}`" in document
    assert f"Contract: `{CONTRACT_VERSION}`" in document
    assert str(FIXTURE_PATH).replace("\\", "/") in document
    assert "No forecast scoring, action guidance, market ranking, or selection advice." in document
    assert "This template is not execution approval and is not runtime input." in document


def _load_template() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


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
