from __future__ import annotations

import json
import re
import socket
import subprocess
import sys
from pathlib import Path
from typing import Any

from pm_bot.rehearsal.static_replay_rehearsal import (
    RESULT_CONTRACT_VERSION,
    build_operator_surface_link_map,
    render_markdown_summary,
    run_static_replay_rehearsal,
)


FIXTURE_DIR = Path("pm_bot/tests/fixtures/rehearsal_actual_static_replay")
MARKET_PACKET_PATH = FIXTURE_DIR / "rehearsal_market_packet.valid.json"
SOURCE_EVIDENCE_PATH = FIXTURE_DIR / "rehearsal_source_evidence_bundle.valid.json"
STALENESS_CASE_SET_PATH = FIXTURE_DIR / "rehearsal_staleness_case_set.valid.json"
CONTRADICTION_CASE_SET_PATH = FIXTURE_DIR / "rehearsal_contradiction_case_set.valid.json"
STOP_CONDITION_MATRIX_PATH = FIXTURE_DIR / "rehearsal_stop_condition_matrix.valid.json"
EXPECTED_RESULT_PATH = FIXTURE_DIR / "expected_static_replay_rehearsal_result.valid.json"

RESULT_ARTIFACT_PATH = Path("pm_bot/rehearsal/artifacts/actual_static_replay_rehearsal_001.result.json")
SUMMARY_ARTIFACT_PATH = Path("pm_bot/rehearsal/artifacts/actual_static_replay_rehearsal_001.md")
LINK_MAP_ARTIFACT_PATH = Path(
    "pm_bot/rehearsal/artifacts/actual_static_replay_rehearsal_001.operator_surface_link_map.json"
)

SAFETY_FLAGS = {
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
DISALLOWED_RESULT_FIELD_NAMES = {
    "buy",
    "confidence",
    "edge",
    "enter",
    "ev",
    "execution_intent",
    "exit",
    "hold",
    "market_side",
    "order_intent",
    "probability",
    "recommendation",
    "sell",
    "side",
    "side_selection",
}
DISALLOWED_ACTION_VALUE_WORDS = {
    "buy",
    "enter",
    "exit",
    "hold",
    "pick",
    "sell",
    "stake",
    "wager",
}


def test_happy_path_static_replay_matches_expected_result() -> None:
    result = _run_rehearsal()
    expected = _load_json(EXPECTED_RESULT_PATH)

    assert result == expected
    assert result["contract_version"] == RESULT_CONTRACT_VERSION
    assert result["mode"] == "static_replay"
    assert result["rehearsal_id"] == "actual_static_replay_rehearsal_001"
    assert result["rehearsal_passed"] is True
    assert result["hard_blockers"] == []
    assert result["warnings"] == []
    assert result["source_evidence_status"]["status"] == "passed"
    assert result["staleness_check_status"]["status"] == "passed"
    assert result["contradiction_check_status"]["status"] == "passed"
    assert result["stop_condition_status"]["status"] == "passed"


def test_missing_required_evidence_creates_hard_blocker(tmp_path: Path) -> None:
    source_evidence = _load_json(SOURCE_EVIDENCE_PATH)
    source_evidence["source_evidence_records"] = source_evidence["source_evidence_records"][:1]
    source_evidence_path = _write_json(tmp_path / "source_evidence.missing.json", source_evidence)

    result = _run_rehearsal(source_evidence_path=source_evidence_path)

    assert result["rehearsal_passed"] is False
    assert result["source_evidence_status"]["status"] == "failed"
    assert result["source_evidence_status"]["missing_evidence_ids"] == ["evidence_station_static_log"]
    assert any(item.startswith("source_evidence:missing_required_evidence_ids") for item in result["hard_blockers"])
    assert "stop_condition:rehearsal_source_evidence_mismatch" in result["hard_blockers"]


def test_stale_evidence_creates_blocker_and_stop_condition(tmp_path: Path) -> None:
    case_set = _load_json(STALENESS_CASE_SET_PATH)
    case_set["case_records"][0]["observed_timestamp_utc"] = "2026-05-09T21:30:00Z"
    staleness_path = _write_json(tmp_path / "staleness.stale.json", case_set)

    result = _run_rehearsal(staleness_case_set_path=staleness_path)

    assert result["rehearsal_passed"] is False
    assert result["staleness_check_status"]["status"] == "blocked"
    assert result["staleness_check_status"]["hard_blocker_case_ids"] == [
        "actual_static_replay_rehearsal_001.staleness.official_report_current"
    ]
    assert "stop_condition:rehearsal_stale_source_evidence" in result["hard_blockers"]


def test_contradiction_case_is_detected(tmp_path: Path) -> None:
    case_set = _load_json(CONTRADICTION_CASE_SET_PATH)
    case_set["case_records"][0]["right_static_value"] = "different_static_subject_key"
    case_set["case_records"][0]["subject_keys_match"] = False
    case_set["case_records"][0]["values_match"] = False
    contradiction_path = _write_json(tmp_path / "contradiction.detected.json", case_set)

    result = _run_rehearsal(contradiction_case_set_path=contradiction_path)

    assert result["rehearsal_passed"] is False
    assert result["contradiction_check_status"]["status"] == "blocked"
    assert result["contradiction_check_status"]["detected_case_ids"] == [
        "actual_static_replay_rehearsal_001.contradiction.subject_and_value_match"
    ]
    assert "stop_condition:rehearsal_source_contradiction_detected" in result["hard_blockers"]


def test_stop_condition_matrix_blocks_when_designed_to_block(tmp_path: Path) -> None:
    matrix = _load_json(STOP_CONDITION_MATRIX_PATH)
    matrix["trigger_matrix_records"][-1]["enabled"] = True
    matrix["trigger_matrix_records"][-1]["force_trigger_for_rehearsal"] = True
    matrix_path = _write_json(tmp_path / "stop_matrix.force_block.json", matrix)

    result = _run_rehearsal(stop_condition_matrix_path=matrix_path)

    assert result["rehearsal_passed"] is False
    assert result["stop_condition_status"]["status"] == "blocked"
    assert result["stop_condition_status"]["hard_blocker_condition_ids"] == [
        "rehearsal_forced_matrix_block"
    ]


def test_output_safety_flags_remain_closed_and_operator_approval_is_not_granted() -> None:
    result = _run_rehearsal()

    for field_name, expected_value in SAFETY_FLAGS.items():
        assert result[field_name] == expected_value


def test_no_action_signal_fields_are_generated() -> None:
    result = _run_rehearsal()
    field_names = _collect_field_names(result)

    assert not (field_names & DISALLOWED_RESULT_FIELD_NAMES)
    assert "market_recommendation_generated" in result
    assert result["market_recommendation_generated"] is False
    assert "probability_ev_edge_or_side_selection_generated" in result
    assert result["probability_ev_edge_or_side_selection_generated"] is False


def test_no_forbidden_action_language_is_emitted_as_value() -> None:
    result = _run_rehearsal()
    values = "\n".join(_collect_string_values(result)).lower()

    for word in DISALLOWED_ACTION_VALUE_WORDS:
        assert re.search(rf"\b{re.escape(word)}\b", values) is None


def test_runner_does_not_require_socket_network_access(monkeypatch: Any) -> None:
    def fail_socket(*_args: Any, **_kwargs: Any) -> None:
        raise AssertionError("socket access is not allowed for static replay rehearsal")

    monkeypatch.setattr(socket, "socket", fail_socket)

    result = _run_rehearsal()

    assert result["rehearsal_passed"] is True
    assert result["live_network_used"] is False


def test_sensitive_path_and_wallet_flags_are_not_used() -> None:
    result = _run_rehearsal()
    link_map = build_operator_surface_link_map(result)
    local_references = [
        *[value for value in result["input_artifacts"].values() if isinstance(value, str)],
        *[value for value in result["generated_artifacts"].values() if isinstance(value, str)],
        *[row["local_reference"] for row in link_map["surface_links"]],
    ]
    serialized_references = "\n".join(local_references).lower()

    assert result["wallet_or_private_key_access"] is False
    assert "pm_bot/wallet/" not in serialized_references
    assert "private_key" not in serialized_references
    assert "credential_reference" not in serialized_references


def test_cli_writes_json_markdown_and_link_map_artifacts(tmp_path: Path) -> None:
    result_path = tmp_path / "actual_static_replay_rehearsal_001.result.json"
    markdown_path = tmp_path / "actual_static_replay_rehearsal_001.md"
    link_map_path = tmp_path / "actual_static_replay_rehearsal_001.operator_surface_link_map.json"

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "pm_bot.rehearsal.static_replay_rehearsal",
            "--market-packet",
            str(MARKET_PACKET_PATH),
            "--source-evidence",
            str(SOURCE_EVIDENCE_PATH),
            "--staleness-case-set",
            str(STALENESS_CASE_SET_PATH),
            "--contradiction-case-set",
            str(CONTRADICTION_CASE_SET_PATH),
            "--stop-condition-matrix",
            str(STOP_CONDITION_MATRIX_PATH),
            "--out",
            str(result_path),
            "--markdown-out",
            str(markdown_path),
            "--link-map-out",
            str(link_map_path),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    cli_result = _load_json(result_path)
    markdown = markdown_path.read_text(encoding="utf-8")
    link_map = _load_json(link_map_path)

    assert cli_result["rehearsal_passed"] is True
    assert cli_result["generated_artifacts"]["rehearsal_result_json"] == str(result_path).replace("\\", "/")
    assert "This was actual read-only supervised-live rehearsal #1." in markdown
    assert "Mode: static/replayed source packets." in markdown
    assert "Live network used: false." in markdown
    assert "OpenRouter calls performed: 0." in markdown
    assert "Polymarket API calls performed: 0." in markdown
    assert "Authenticated endpoints used: false." in markdown
    assert "Wallet/private-key access: false." in markdown
    assert "Order or trading actions: false." in markdown
    assert link_map["summary_counts"]["surface_links"] == 6


def test_canonical_artifacts_exist_and_match_static_replay_safety_contract() -> None:
    result = _load_json(RESULT_ARTIFACT_PATH)
    markdown = SUMMARY_ARTIFACT_PATH.read_text(encoding="utf-8")
    link_map = _load_json(LINK_MAP_ARTIFACT_PATH)

    assert result == _load_json(EXPECTED_RESULT_PATH)
    assert result["rehearsal_passed"] is True
    assert result["live_network_used"] is False
    assert markdown.startswith("# Actual Read-Only Supervised-Live Rehearsal 001")
    assert link_map["rehearsal_result_reference"] == str(RESULT_ARTIFACT_PATH).replace("\\", "/")


def _run_rehearsal(
    *,
    market_packet_path: Path = MARKET_PACKET_PATH,
    source_evidence_path: Path = SOURCE_EVIDENCE_PATH,
    staleness_case_set_path: Path = STALENESS_CASE_SET_PATH,
    contradiction_case_set_path: Path = CONTRADICTION_CASE_SET_PATH,
    stop_condition_matrix_path: Path = STOP_CONDITION_MATRIX_PATH,
) -> dict[str, Any]:
    return run_static_replay_rehearsal(
        market_packet_path=market_packet_path,
        source_evidence_path=source_evidence_path,
        staleness_case_set_path=staleness_case_set_path,
        contradiction_case_set_path=contradiction_case_set_path,
        stop_condition_matrix_path=stop_condition_matrix_path,
    )


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> Path:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _collect_field_names(value: Any) -> set[str]:
    names: set[str] = set()
    if isinstance(value, dict):
        for key, nested in value.items():
            names.add(str(key))
            names.update(_collect_field_names(nested))
    elif isinstance(value, list):
        for item in value:
            names.update(_collect_field_names(item))
    return names


def _collect_string_values(value: Any) -> list[str]:
    values: list[str] = []
    if isinstance(value, dict):
        for nested in value.values():
            values.extend(_collect_string_values(nested))
    elif isinstance(value, list):
        for item in value:
            values.extend(_collect_string_values(item))
    elif isinstance(value, str):
        values.append(value)
    return values
