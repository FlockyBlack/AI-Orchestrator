from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

from pm_bot.simulated_decisions.schema import (
    LOCAL_RUN_MODE,
    OPERATOR_REVIEW_STATUS,
    PACKET_STATE,
    SAMPLE_PACKET_PATH,
    SCHEMA_PATH,
    SIMULATED_DECISION_PACKET_CONTRACT_VERSION,
    SIMULATED_DECISION_PACKET_SCHEMA_ID,
    build_simulated_decision_packet_schema,
    example_simulated_decision_packet,
    required_packet_fields,
    validate_simulated_decision_packet,
)


def test_static_schema_has_expected_contract_and_required_fields() -> None:
    schema = build_simulated_decision_packet_schema()

    assert schema["schema_id"] == SIMULATED_DECISION_PACKET_SCHEMA_ID
    assert schema["contract_version"] == SIMULATED_DECISION_PACKET_CONTRACT_VERSION
    assert schema["recordkeeping_mode"] == LOCAL_RUN_MODE
    assert schema["local_only"] is True
    assert schema["operator_review_required"] is True
    assert schema["additional_fields_allowed"] is False
    assert tuple(schema["required_fields"]) == required_packet_fields()
    assert "market_snapshot" in schema["properties"]
    assert "record_sections" in schema["properties"]


def test_fixture_packet_matches_schema_shape_for_offline_recordkeeping() -> None:
    schema = build_simulated_decision_packet_schema()
    packet = example_simulated_decision_packet()

    assert tuple(packet.keys()) == tuple(sorted(packet.keys()))
    assert set(packet) == set(schema["required_fields"])
    assert packet["contract_version"] == SIMULATED_DECISION_PACKET_CONTRACT_VERSION
    assert packet["run_mode"] == LOCAL_RUN_MODE
    assert packet["packet_state"] == PACKET_STATE
    assert packet["local_only"] is True
    assert packet["operator_review_required"] is True
    assert packet["operator_review"]["status"] == OPERATOR_REVIEW_STATUS
    assert packet["errors"] == []
    assert packet["warnings"] == []
    assert packet["safety_boundaries"] == schema["safety_boundaries"]
    assert packet["summary_counts"] == {
        "input_artifacts": 1,
        "observations": 1,
        "record_sections": 1,
        "warnings": 0,
    }


def test_schema_and_fixture_loaders_return_detached_deterministic_copies() -> None:
    first_schema = build_simulated_decision_packet_schema()
    second_schema = build_simulated_decision_packet_schema()
    first_packet = example_simulated_decision_packet()
    second_packet = example_simulated_decision_packet()

    assert first_schema == second_schema
    assert first_packet == second_packet

    first_schema["schema_id"] = "mutated"
    first_packet["packet_id"] = "mutated"

    assert build_simulated_decision_packet_schema()["schema_id"] == SIMULATED_DECISION_PACKET_SCHEMA_ID
    assert example_simulated_decision_packet()["packet_id"] == "simulated_decision_packet_fixture_001"


def test_static_json_files_match_loader_outputs() -> None:
    schema = json.loads(Path(SCHEMA_PATH).read_text(encoding="utf-8"))
    packet = json.loads(Path(SAMPLE_PACKET_PATH).read_text(encoding="utf-8"))

    assert schema == build_simulated_decision_packet_schema()
    assert packet == example_simulated_decision_packet()


def test_fixture_validates_as_simulated_decision_packet_record() -> None:
    validation = validate_simulated_decision_packet(example_simulated_decision_packet())

    assert validation.valid is True
    assert validation.errors == ()


def test_validator_rejects_unexpected_packet_fields() -> None:
    packet = example_simulated_decision_packet()
    packet["extra_operator_field"] = "not part of the closed packet contract"

    validation = validate_simulated_decision_packet(packet)

    assert validation.valid is False
    assert any("$ has unexpected fields: extra_operator_field" in error for error in validation.errors)


def test_validator_rejects_non_local_references_without_loading_them() -> None:
    packet = example_simulated_decision_packet()
    packet["market_snapshot"]["local_reference"] = "https://example.invalid/static.json"

    validation = validate_simulated_decision_packet(packet)

    assert validation.valid is False
    assert any("$.market_snapshot.local_reference must be a local repository-relative reference" in error for error in validation.errors)


def test_validator_rejects_summary_count_drift() -> None:
    packet = example_simulated_decision_packet()
    packet["summary_counts"]["observations"] = 99

    validation = validate_simulated_decision_packet(packet)

    assert validation.valid is False
    assert any("$.summary_counts.observations must match packet content: 1" in error for error in validation.errors)


def test_validator_rejects_operator_review_bypass_state() -> None:
    packet = example_simulated_decision_packet()
    packet["operator_review"]["status"] = "accepted_without_review"

    validation = validate_simulated_decision_packet(packet)

    assert validation.valid is False
    assert any("$.operator_review.status must be 'pending_operator_review'" in error for error in validation.errors)


def test_validator_rejects_safety_boundary_drift() -> None:
    packet = example_simulated_decision_packet()
    packet["safety_boundaries"]["network_calls_allowed"] = True

    validation = validate_simulated_decision_packet(packet)

    assert validation.valid is False
    assert any("$.safety_boundaries must match the closed local-only safety boundary contract" in error for error in validation.errors)


def test_validator_rejects_undeclared_observation_source_artifact() -> None:
    packet = example_simulated_decision_packet()
    packet["record_sections"][0]["observations"][0]["source_artifact_ids"] = ["missing_artifact"]

    validation = validate_simulated_decision_packet(packet)

    assert validation.valid is False
    assert any(
        "$.record_sections[0].observations[0].source_artifact_ids[0] must reference a declared input artifact"
        in error
        for error in validation.errors
    )


def test_validator_rejects_guidance_or_scoring_fields() -> None:
    packet = example_simulated_decision_packet()
    packet["record_sections"][0]["observations"][0]["recommendation"] = "not allowed in simulated records"

    validation = validate_simulated_decision_packet(packet)

    assert validation.valid is False
    assert any(
        "forbidden guidance/scoring/action field detected in packet at "
        "$.record_sections[0].observations[0].recommendation"
        in error
        for error in validation.errors
    )


def test_validator_is_deterministic_for_equivalent_packets() -> None:
    packet = example_simulated_decision_packet()

    first = validate_simulated_decision_packet(packet)
    second = validate_simulated_decision_packet(deepcopy(packet))

    assert first == second


def test_schema_and_fixture_have_no_guidance_or_scoring_fields() -> None:
    schema = build_simulated_decision_packet_schema()
    packet = example_simulated_decision_packet()

    assert _find_disallowed_terms(schema) == []
    assert _find_disallowed_terms(packet) == []


def test_fixture_references_only_local_static_artifacts() -> None:
    packet = example_simulated_decision_packet()
    references = _collect_values_for_key(packet, "local_reference")
    references.append(packet["schema_reference"])

    assert references
    for reference in references:
        assert "://" not in reference
        assert reference.startswith(("pm_bot/tests/fixtures/", "pm_bot/simulated_decisions/"))


def test_fixture_summary_counts_match_record_content() -> None:
    packet = example_simulated_decision_packet()
    observation_count = sum(len(section["observations"]) for section in packet["record_sections"])

    assert packet["summary_counts"]["input_artifacts"] == len(packet["input_artifacts"])
    assert packet["summary_counts"]["record_sections"] == len(packet["record_sections"])
    assert packet["summary_counts"]["observations"] == observation_count
    assert packet["summary_counts"]["warnings"] == len(packet["warnings"])


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
