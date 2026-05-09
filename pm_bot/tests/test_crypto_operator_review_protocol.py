from __future__ import annotations

import json
from pathlib import Path


DOC_PATH = Path("docs/PMBOT_CRYPTO_PILOT_002_CRYPTO_OPERATOR_REVIEW_PROTOCOL_LOCAL_ONLY.md")
FIXTURE_PATH = Path(
    "pm_bot/tests/fixtures/crypto_operator_review_protocol/crypto_operator_review_protocol.valid.json"
)
CAPTURE_FIXTURE_PATH = Path(
    "pm_bot/tests/fixtures/crypto_market_class_capture/crypto_market_class_capture_template.valid.json"
)
TASK_ID = "PMBOT-CRYPTO-PILOT-002-CRYPTO-OPERATOR-REVIEW-PROTOCOL-LOCAL-ONLY"
CONTRACT_VERSION = "pmbot_crypto_operator_review_protocol.v1"
RUN_MODE = "local_descriptive_operator_review_protocol"
PROTOCOL_NAME = "crypto-operator-review-protocol"

EXPECTED_REVIEW_FIELDS = (
    "review_record_id",
    "source_record_id",
    "market_class",
    "market_slug",
    "market_title",
    "asset_symbol",
    "asset_name",
    "quote_currency",
    "metric_type",
    "threshold_value",
    "threshold_unit",
    "comparison_rule",
    "deadline_utc",
    "local_source_reference",
    "copied_text_check",
    "timestamp_check",
    "field_presence_check",
    "operator_notes",
    "review_status",
)

EXPECTED_PROTOCOL_STEPS = (
    "field_presence_check",
    "copied_text_check",
    "timestamp_check",
    "pending_state_check",
)


def test_static_crypto_operator_review_protocol_fixture_has_expected_contract() -> None:
    protocol = _load_protocol()

    assert tuple(protocol.keys()) == tuple(sorted(protocol.keys()))
    assert protocol["task_id"] == TASK_ID
    assert protocol["protocol_name"] == PROTOCOL_NAME
    assert protocol["contract_version"] == CONTRACT_VERSION
    assert protocol["run_mode"] == RUN_MODE
    assert protocol["created_at"] == "2026-05-09T00:00:00Z"
    assert protocol["local_only"] is True
    assert protocol["operator_review_required"] is True
    assert protocol["operator_review"]["status"] == "pending_operator_review"
    assert protocol["record_state"] == "protocol_only_static_sample"
    assert protocol["errors"] == []
    assert protocol["warnings"] == []


def test_review_fields_are_fixed_and_protocol_steps_are_deterministic() -> None:
    protocol = _load_protocol()

    assert tuple(protocol["review_record_fields"]) == EXPECTED_REVIEW_FIELDS
    assert tuple(step["step_id"] for step in protocol["protocol_steps"]) == EXPECTED_PROTOCOL_STEPS
    for step in protocol["protocol_steps"]:
        assert step["expected_record_state"] == "pending_operator_review"
        assert set(step["required_fields"]).issubset(EXPECTED_REVIEW_FIELDS)


def test_static_review_record_is_copied_from_local_capture_fixture() -> None:
    protocol = _load_protocol()
    capture_template = _load_capture_template()
    review_record = protocol["static_review_records"][0]
    sample = capture_template["sample_records"][0]

    assert set(review_record) == set(EXPECTED_REVIEW_FIELDS)
    assert review_record == {
        "asset_name": "Bitcoin",
        "asset_symbol": "BTC",
        "comparison_rule": "at_or_above_threshold_by_deadline",
        "copied_text_check": "copied_from_static_capture_fixture",
        "deadline_utc": "2026-12-31T23:59:59Z",
        "field_presence_check": "all_required_fields_present",
        "local_source_reference": str(CAPTURE_FIXTURE_PATH).replace("\\", "/"),
        "market_class": "crypto_threshold_event",
        "market_slug": "static-sample-btc-threshold-2026",
        "market_title": "Static sample BTC threshold market",
        "metric_type": "spot_index_threshold",
        "operator_notes": "Static sample for review protocol shape only.",
        "quote_currency": "USD",
        "review_record_id": "crypto_operator_review_protocol_001.sample.btc_threshold.review",
        "review_status": "pending_operator_review",
        "source_record_id": "crypto_market_class_capture_template_001.sample.btc_threshold",
        "threshold_unit": "USD",
        "threshold_value": "150000.00",
        "timestamp_check": "deadline_copied_without_runtime_lookup",
    }
    for field in (
        "market_class",
        "market_slug",
        "market_title",
        "asset_symbol",
        "asset_name",
        "quote_currency",
        "metric_type",
        "threshold_value",
        "threshold_unit",
        "comparison_rule",
        "deadline_utc",
    ):
        assert review_record[field] == sample[field]
    assert review_record["source_record_id"] == sample["record_id"]
    assert review_record["local_source_reference"] == sample["source_snapshot_reference"]


def test_input_contract_references_the_crypto_capture_template_fixture() -> None:
    protocol = _load_protocol()
    input_contract = protocol["input_contracts"][0]
    capture_template = _load_capture_template()

    assert input_contract == {
        "contract_version": "pmbot_crypto_market_class_capture_template.v1",
        "fixture_reference": str(CAPTURE_FIXTURE_PATH).replace("\\", "/"),
        "required_state": "template_only_static_sample",
        "sample_record_id": "crypto_market_class_capture_template_001.sample.btc_threshold",
    }
    assert input_contract["contract_version"] == capture_template["contract_version"]
    assert input_contract["required_state"] == capture_template["record_state"]
    assert input_contract["sample_record_id"] == capture_template["sample_records"][0]["record_id"]


def test_summary_counts_match_protocol_content() -> None:
    protocol = _load_protocol()

    assert protocol["summary_counts"] == {
        "input_contracts": len(protocol["input_contracts"]),
        "protocol_steps": len(protocol["protocol_steps"]),
        "review_record_fields": len(protocol["review_record_fields"]),
        "static_review_records": len(protocol["static_review_records"]),
        "warnings": len(protocol["warnings"]),
    }


def test_safety_boundaries_are_closed_for_local_review_protocol() -> None:
    protocol = _load_protocol()

    assert protocol["safety_boundaries"] == {
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


def test_protocol_references_only_local_static_fixture_paths() -> None:
    protocol = _load_protocol()
    references = sorted(
        set(
            _collect_values_for_key(protocol, "fixture_reference")
            + _collect_values_for_key(protocol, "local_source_reference")
        )
    )

    assert references == [str(CAPTURE_FIXTURE_PATH).replace("\\", "/")]
    for reference in references:
        assert "://" not in reference
        assert reference.startswith("pm_bot/tests/fixtures/crypto_market_class_capture/")


def test_fixture_has_no_guidance_scoring_or_selection_fields() -> None:
    protocol = _load_protocol()

    assert _find_disallowed_terms(protocol) == []


def test_documentation_registers_protocol_contract_fixture_and_safety_boundary() -> None:
    document = DOC_PATH.read_text(encoding="utf-8")

    assert f"Task: `{TASK_ID}`" in document
    assert f"Protocol: `{PROTOCOL_NAME}`" in document
    assert f"Contract: `{CONTRACT_VERSION}`" in document
    assert str(FIXTURE_PATH).replace("\\", "/") in document
    assert str(CAPTURE_FIXTURE_PATH).replace("\\", "/") in document
    assert "No forecast scoring, action guidance, market ranking, or selection advice." in document
    assert "This protocol is not execution approval and is not runtime input." in document


def _load_protocol() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def _load_capture_template() -> dict:
    return json.loads(CAPTURE_FIXTURE_PATH.read_text(encoding="utf-8"))


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
