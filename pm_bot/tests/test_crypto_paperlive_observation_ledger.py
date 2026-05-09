from __future__ import annotations

import json
from pathlib import Path


DOC_PATH = Path("docs/PMBOT_CRYPTO_PILOT_003_CRYPTO_PAPERLIVE_OBSERVATION_LEDGER_LOCAL_ONLY.md")
FIXTURE_PATH = Path(
    "pm_bot/tests/fixtures/crypto_paperlive_observation_ledger/crypto_paperlive_observation_ledger.valid.json"
)
SNAPSHOT_PATH = Path(
    "pm_bot/tests/fixtures/crypto_paperlive_observation_ledger/static_crypto_reference_snapshot.valid.json"
)
CAPTURE_FIXTURE_PATH = Path(
    "pm_bot/tests/fixtures/crypto_market_class_capture/crypto_market_class_capture_template.valid.json"
)
PROTOCOL_FIXTURE_PATH = Path(
    "pm_bot/tests/fixtures/crypto_operator_review_protocol/crypto_operator_review_protocol.valid.json"
)
TASK_ID = "PMBOT-CRYPTO-PILOT-003-CRYPTO-PAPERLIVE-OBSERVATION-LEDGER-LOCAL-ONLY"
CONTRACT_VERSION = "pmbot_crypto_paperlive_observation_ledger.v1"
RUN_MODE = "local_descriptive_crypto_paperlive_observation_ledger"

EXPECTED_LEDGER_RECORD_FIELDS = (
    "record_id",
    "source_review_record_id",
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
    "observation_window_start_utc",
    "observation_window_end_utc",
    "reported_reference_value",
    "reported_reference_unit",
    "reported_at_utc",
    "observation_source_label",
    "local_source_reference",
    "copied_text_check",
    "operator_notes",
    "review_status",
)


def test_static_crypto_paperlive_observation_ledger_fixture_has_expected_contract() -> None:
    ledger = _load_ledger()

    assert tuple(ledger.keys()) == tuple(sorted(ledger.keys()))
    assert ledger["task_id"] == TASK_ID
    assert ledger["ledger_id"] == "crypto_paperlive_observation_ledger_001"
    assert ledger["contract_version"] == CONTRACT_VERSION
    assert ledger["run_mode"] == RUN_MODE
    assert ledger["created_at"] == "2026-05-09T00:20:00Z"
    assert ledger["local_only"] is True
    assert ledger["operator_review_required"] is True
    assert ledger["operator_review"]["status"] == "pending_operator_review"
    assert ledger["record_state"] == "ledger_only_static_sample"
    assert ledger["errors"] == []
    assert ledger["warnings"] == []


def test_ledger_record_fields_are_fixed_and_pending_operator_review() -> None:
    ledger = _load_ledger()
    record = ledger["observation_records"][0]

    assert tuple(ledger["ledger_record_fields"]) == EXPECTED_LEDGER_RECORD_FIELDS
    assert set(record) == set(EXPECTED_LEDGER_RECORD_FIELDS)
    assert record["review_status"] == "pending_operator_review"
    assert ledger["operator_review_steps"] == [
        "Confirm ledger row copies local static source labels, timestamps, and reference values.",
        "Confirm copied market text matches the local crypto operator review fixture.",
        "Confirm review status remains pending operator review.",
    ]


def test_static_observation_record_copies_protocol_and_snapshot_fields() -> None:
    ledger = _load_ledger()
    protocol = _load_protocol()
    snapshot = _load_snapshot()
    record = ledger["observation_records"][0]
    review_record = protocol["static_review_records"][0]

    assert record == {
        "asset_name": "Bitcoin",
        "asset_symbol": "BTC",
        "comparison_rule": "at_or_above_threshold_by_deadline",
        "copied_text_check": "copied_from_static_crypto_review_and_reference_snapshot",
        "deadline_utc": "2026-12-31T23:59:59Z",
        "local_source_reference": str(SNAPSHOT_PATH).replace("\\", "/"),
        "market_class": "crypto_threshold_event",
        "market_slug": "static-sample-btc-threshold-2026",
        "market_title": "Static sample BTC threshold market",
        "measurement_source_label": "local fixture index close label",
        "metric_type": "spot_index_threshold",
        "observation_source_label": "Static crypto reference sample",
        "observation_window_end_utc": "2026-05-09T00:00:00Z",
        "observation_window_start_utc": "2026-05-08T00:00:00Z",
        "operator_notes": "Static sample for descriptive observation ledger shape only.",
        "quote_currency": "USD",
        "record_id": "crypto_paperlive_observation_ledger_001.sample.btc_threshold.observation",
        "reported_at_utc": "2026-05-09T00:00:00Z",
        "reported_reference_unit": "USD",
        "reported_reference_value": "102500.00",
        "review_status": "pending_operator_review",
        "source_review_record_id": "crypto_operator_review_protocol_001.sample.btc_threshold.review",
        "threshold_unit": "USD",
        "threshold_value": "150000.00",
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
        assert record[field] == review_record[field]
    assert record["source_review_record_id"] == review_record["review_record_id"]
    assert record["measurement_source_label"] == snapshot["measurement_source_label"]
    assert record["reported_reference_value"] == snapshot["reported_reference_value"]
    assert record["reported_reference_unit"] == snapshot["reported_reference_unit"]
    assert record["reported_at_utc"] == snapshot["reported_at_utc"]
    assert record["observation_source_label"] == snapshot["source_label"]


def test_observation_source_snapshot_is_local_static_sample() -> None:
    ledger = _load_ledger()
    snapshot = _load_snapshot()
    catalog_entry = ledger["observation_source_catalog"][0]

    assert tuple(snapshot.keys()) == tuple(sorted(snapshot.keys()))
    assert snapshot == {
        "asset_name": "Bitcoin",
        "asset_symbol": "BTC",
        "contract_version": "pmbot_static_crypto_reference_snapshot.v1",
        "created_at": "2026-05-09T00:20:00Z",
        "local_only": True,
        "measurement_source_label": "local fixture index close label",
        "metric_type": "spot_index_threshold",
        "reported_at_utc": "2026-05-09T00:00:00Z",
        "reported_reference_unit": "USD",
        "reported_reference_value": "102500.00",
        "snapshot_id": "static_crypto_reference_snapshot_2026_05_09_btc",
        "source_label": "Static crypto reference sample",
    }
    assert catalog_entry["contract_version"] == snapshot["contract_version"]
    assert catalog_entry["local_reference"] == str(SNAPSHOT_PATH).replace("\\", "/")
    assert set(catalog_entry["required_fields"]).issubset(snapshot)
    assert catalog_entry["operator_review_status"] == "pending_operator_review"


def test_source_contracts_reference_existing_local_crypto_fixtures() -> None:
    ledger = _load_ledger()
    capture_template = _load_capture_template()
    protocol = _load_protocol()

    assert ledger["source_contracts"] == [
        {
            "contract_version": "pmbot_crypto_market_class_capture_template.v1",
            "fixture_reference": str(CAPTURE_FIXTURE_PATH).replace("\\", "/"),
            "required_state": "template_only_static_sample",
            "sample_record_id": "crypto_market_class_capture_template_001.sample.btc_threshold",
        },
        {
            "contract_version": "pmbot_crypto_operator_review_protocol.v1",
            "fixture_reference": str(PROTOCOL_FIXTURE_PATH).replace("\\", "/"),
            "required_state": "protocol_only_static_sample",
            "sample_record_id": "crypto_operator_review_protocol_001.sample.btc_threshold.review",
        },
    ]
    assert ledger["source_contracts"][0]["contract_version"] == capture_template["contract_version"]
    assert ledger["source_contracts"][0]["required_state"] == capture_template["record_state"]
    assert ledger["source_contracts"][1]["contract_version"] == protocol["contract_version"]
    assert ledger["source_contracts"][1]["required_state"] == protocol["record_state"]


def test_summary_counts_match_ledger_content() -> None:
    ledger = _load_ledger()

    assert ledger["summary_counts"] == {
        "ledger_record_fields": len(ledger["ledger_record_fields"]),
        "observation_records": len(ledger["observation_records"]),
        "observation_sources": len(ledger["observation_source_catalog"]),
        "source_contracts": len(ledger["source_contracts"]),
        "warnings": len(ledger["warnings"]),
    }


def test_safety_boundaries_are_closed_for_local_observation_ledger() -> None:
    ledger = _load_ledger()

    assert ledger["safety_boundaries"] == {
        "authenticated_endpoint_calls_allowed": False,
        "background_process_allowed": False,
        "browser_automation_allowed": False,
        "external_market_api_calls_allowed": False,
        "local_static_samples_only": True,
        "network_calls_allowed": False,
        "operator_review_required": True,
        "paperlive_execution_allowed": False,
        "runtime_or_dispatcher_changes_allowed": False,
        "transaction_endpoint_calls_allowed": False,
        "wallet_or_signing_material_access_allowed": False,
    }


def test_ledger_references_only_local_static_fixture_paths() -> None:
    ledger = _load_ledger()
    references = sorted(
        set(
            _collect_values_for_key(ledger, "fixture_reference")
            + _collect_values_for_key(ledger, "local_reference")
            + _collect_values_for_key(ledger, "local_source_reference")
        )
    )

    assert references == [
        str(CAPTURE_FIXTURE_PATH).replace("\\", "/"),
        str(PROTOCOL_FIXTURE_PATH).replace("\\", "/"),
        str(SNAPSHOT_PATH).replace("\\", "/"),
    ]
    for reference in references:
        assert "://" not in reference
        assert reference.startswith("pm_bot/tests/fixtures/")


def test_fixture_has_no_guidance_scoring_or_selection_fields() -> None:
    ledger = _load_ledger()
    snapshot = _load_snapshot()

    assert _find_disallowed_terms(ledger) == []
    assert _find_disallowed_terms(snapshot) == []


def test_documentation_registers_ledger_contract_fixtures_and_safety_boundary() -> None:
    document = DOC_PATH.read_text(encoding="utf-8")

    assert f"Task: `{TASK_ID}`" in document
    assert "Ledger: `crypto-paperlive-observation-ledger`" in document
    assert f"Contract: `{CONTRACT_VERSION}`" in document
    assert str(FIXTURE_PATH).replace("\\", "/") in document
    assert str(SNAPSHOT_PATH).replace("\\", "/") in document
    assert str(CAPTURE_FIXTURE_PATH).replace("\\", "/") in document
    assert str(PROTOCOL_FIXTURE_PATH).replace("\\", "/") in document
    assert "No forecast scoring, action guidance, market ranking, or selection advice." in document
    assert "This ledger is not execution approval and is not runtime input." in document


def _load_ledger() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def _load_snapshot() -> dict:
    return json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))


def _load_capture_template() -> dict:
    return json.loads(CAPTURE_FIXTURE_PATH.read_text(encoding="utf-8"))


def _load_protocol() -> dict:
    return json.loads(PROTOCOL_FIXTURE_PATH.read_text(encoding="utf-8"))


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
