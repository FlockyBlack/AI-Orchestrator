from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from pm_bot.rehearsal.static_replay_rehearsal import (
    FAILURE_MODE_RESULT_CONTRACT_VERSION,
    run_static_replay_failure_mode_batch,
    run_static_replay_rehearsal,
)


FIXTURE_ROOT = Path("pm_bot/tests/fixtures/rehearsal_static_replay_failure_modes")
SUMMARY_ARTIFACT_PATH = Path("pm_bot/rehearsal/artifacts/actual_static_replay_failure_modes_002.result.json")

STATIC_SAFE_FLAGS = {
    "authenticated_endpoints_used": False,
    "live_network_used": False,
    "market_recommendation_generated": False,
    "openrouter_calls_performed": 0,
    "operator_approval_granted": False,
    "operator_approval_required": True,
    "orders_or_trading_actions": False,
    "polymarket_api_calls_performed": 0,
    "probability_ev_edge_or_side_selection_generated": False,
    "wallet_or_private_key_access": False,
}
SUMMARY_SAFE_FLAGS = {
    "authenticated_endpoints_used": False,
    "live_network_used": False,
    "market_recommendation_generated": False,
    "openrouter_calls_performed": 0,
    "orders_or_trading_actions": False,
    "polymarket_api_calls_performed": 0,
    "probability_ev_edge_or_side_selection_generated": False,
    "runtime_or_dispatcher_changes": False,
    "wallet_or_private_key_access": False,
}
ACTION_WORDS = {"buy", "enter", "exit", "hold", "pick", "sell", "stake", "wager"}
SENSITIVE_VALUE_MARKERS = {".env", "c:/users/example", "private_key", "sk-local-test", "wallet/"}
DISALLOWED_FIELD_TOKENS = {
    "confidence",
    "edge",
    "enter",
    "ev",
    "exit",
    "hold",
    "order_intent",
    "probability",
    "recommendation",
    "side",
    "side_selection",
}
ALLOWED_SAFETY_FIELD_NAMES = {
    "market_recommendation_generated",
    "probability_ev_edge_or_side_selection_generated",
}


def test_missing_evidence_blocks_safely() -> None:
    result = _run_scenario("missing_evidence")

    assert result["rehearsal_passed"] is False
    assert result["source_evidence_status"]["status"] == "failed"
    assert result["source_evidence_status"]["missing_evidence_ids"] == ["evidence_station_static_log"]
    assert _has_blocker(result, "source_evidence:missing_required_evidence_ids:evidence_station_static_log")
    assert _has_blocker(result, "stop_condition:rehearsal_source_evidence_mismatch")


def test_stale_evidence_blocks_according_to_failure_contract() -> None:
    result = _run_scenario("stale_evidence")

    assert result["rehearsal_passed"] is False
    assert result["staleness_check_status"]["status"] == "blocked"
    assert result["staleness_check_status"]["hard_blocker_case_ids"] == [
        "actual_static_replay_rehearsal_001.staleness.official_report_current"
    ]
    assert _has_blocker(result, "stop_condition:rehearsal_stale_source_evidence")


def test_contradiction_is_detected_and_blocks_required_input() -> None:
    result = _run_scenario("contradiction_detected")

    assert result["rehearsal_passed"] is False
    assert result["contradiction_check_status"]["status"] == "blocked"
    assert result["contradiction_check_status"]["detected_case_ids"] == [
        "actual_static_replay_rehearsal_001.contradiction.subject_and_value_match"
    ]
    assert _has_blocker(result, "stop_condition:rehearsal_source_contradiction_detected")


def test_stop_condition_triggers_hard_block() -> None:
    result = _run_scenario("stop_condition_triggered")

    assert result["rehearsal_passed"] is False
    assert result["stop_condition_status"]["status"] == "blocked"
    assert result["stop_condition_status"]["hard_blocker_condition_ids"] == [
        "rehearsal_forced_matrix_block"
    ]
    assert result["stop_condition_status"]["triggered_conditions"] == [
        {
            "condition_id": "rehearsal_forced_matrix_block",
            "observed_status": "passed",
            "status_key": "market_packet_status",
            "trigger_state_after_match": "stopped_pending_manual_matrix_review",
        }
    ]


def test_malformed_market_packet_fails_safely() -> None:
    result = _run_scenario("malformed_market_packet")

    assert result["rehearsal_passed"] is False
    assert _has_blocker(
        result,
        "market_packet:market_packet.contract_version must be "
        "pmbot_actual_read_only_rehearsal_market_packet.v1",
    )
    assert result["source_evidence_status"]["status"] == "passed"
    assert result["stop_condition_status"]["status"] == "passed"


def test_forbidden_action_leakage_is_not_emitted_as_actionable_instruction() -> None:
    result = _run_scenario("forbidden_action_leakage_guard")

    assert result["rehearsal_passed"] is False
    assert result["input_safety_status"]["status"] == "blocked"
    assert _has_blocker(result, "safety:forbidden_action_text_sanitized")
    assert "safety_sanitized_forbidden_action_text" in result["warnings"]
    assert _find_action_word_values(result) == []


def test_sensitive_path_and_key_like_input_is_not_treated_as_credential_material() -> None:
    result = _run_scenario("sensitive_path_leakage_guard")

    assert result["rehearsal_passed"] is False
    assert result["input_safety_status"]["status"] == "blocked"
    assert _has_blocker(result, "safety:sensitive_text_sanitized")
    assert result["wallet_or_private_key_access"] is False
    assert "safety_sanitized_sensitive_text" in result["warnings"]
    assert _find_sensitive_value_markers(result) == []
    assert all("wallet" not in reference for reference in result["source_evidence_status"]["checked_local_references"])


def test_every_failure_mode_result_has_safe_flags() -> None:
    for scenario_dir in sorted(path for path in FIXTURE_ROOT.iterdir() if path.is_dir()):
        result = _run_scenario(scenario_dir.name)
        for field_name, expected_value in STATIC_SAFE_FLAGS.items():
            assert result[field_name] == expected_value, scenario_dir.name


def test_no_recommendation_probability_ev_edge_or_side_selection_fields_are_generated() -> None:
    for scenario_dir in sorted(path for path in FIXTURE_ROOT.iterdir() if path.is_dir()):
        result = _run_scenario(scenario_dir.name)
        unexpected_fields = _find_disallowed_field_names(result)

        assert unexpected_fields == [], scenario_dir.name
        assert result["market_recommendation_generated"] is False
        assert result["probability_ev_edge_or_side_selection_generated"] is False


def test_summary_artifact_json_is_valid_and_all_scenarios_behaved_as_expected() -> None:
    artifact = json.loads(SUMMARY_ARTIFACT_PATH.read_text(encoding="utf-8"))
    expected = run_static_replay_failure_mode_batch(fixture_root=FIXTURE_ROOT)

    assert artifact == expected
    assert artifact["contract_version"] == FAILURE_MODE_RESULT_CONTRACT_VERSION
    assert artifact["mode"] == "static_replay_failure_modes"
    assert artifact["base_rehearsal_id"] == "actual_static_replay_rehearsal_001"
    assert len(artifact["scenarios"]) == 7
    assert artifact["passed_scenario_count"] == 7
    assert artifact["failed_scenario_count"] == 0
    assert artifact["all_failure_modes_behaved_as_expected"] is True
    for field_name, expected_value in SUMMARY_SAFE_FLAGS.items():
        assert artifact[field_name] == expected_value


def _run_scenario(scenario_name: str) -> dict[str, Any]:
    scenario_dir = FIXTURE_ROOT / scenario_name
    return run_static_replay_rehearsal(
        market_packet_path=scenario_dir / "market_packet.json",
        source_evidence_path=scenario_dir / "source_evidence.json",
        staleness_case_set_path=scenario_dir / "staleness_case_set.json",
        contradiction_case_set_path=scenario_dir / "contradiction_case_set.json",
        stop_condition_matrix_path=scenario_dir / "stop_condition_matrix.json",
    )


def _has_blocker(result: dict[str, Any], expected_fragment: str) -> bool:
    return any(expected_fragment in blocker for blocker in result["hard_blockers"])


def _find_action_word_values(value: Any, path: str = "$") -> list[str]:
    hits: list[str] = []
    if isinstance(value, dict):
        for key, nested in value.items():
            hits.extend(_find_action_word_values(nested, f"{path}.{key}"))
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            hits.extend(_find_action_word_values(nested, f"{path}[{index}]"))
    elif isinstance(value, str):
        tokens = _tokens(value)
        if tokens & ACTION_WORDS:
            hits.append(path)
    return hits


def _find_sensitive_value_markers(value: Any, path: str = "$") -> list[str]:
    hits: list[str] = []
    if isinstance(value, dict):
        for key, nested in value.items():
            hits.extend(_find_sensitive_value_markers(nested, f"{path}.{key}"))
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            hits.extend(_find_sensitive_value_markers(nested, f"{path}[{index}]"))
    elif isinstance(value, str):
        lowered = value.lower()
        if any(marker in lowered for marker in SENSITIVE_VALUE_MARKERS):
            hits.append(path)
    return hits


def _find_disallowed_field_names(value: Any, path: str = "$") -> list[str]:
    hits: list[str] = []
    if isinstance(value, dict):
        for key, nested in value.items():
            key_string = str(key)
            key_path = f"{path}.{key_string}"
            if key_string not in ALLOWED_SAFETY_FIELD_NAMES:
                tokens = _tokens(key_string)
                if tokens & DISALLOWED_FIELD_TOKENS:
                    hits.append(key_path)
            hits.extend(_find_disallowed_field_names(nested, key_path))
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            hits.extend(_find_disallowed_field_names(nested, f"{path}[{index}]"))
    return hits


def _tokens(value: str) -> set[str]:
    normalized = re.sub(r"[^a-zA-Z0-9]+", "_", value.lower())
    return {token for token in normalized.split("_") if token}
