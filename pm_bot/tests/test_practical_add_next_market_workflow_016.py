from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

ARTIFACT_DIR = Path("pm_bot/practical/artifacts/add_market_016")
EXISTING_MARKET_IDS = {"563650", "597964", "598936", "691547", "692258"}
EXPECTED_MARKET_IDS = EXISTING_MARKET_IDS | {"573656"}

ACTION_PATTERN = re.compile(
    r"\b(?:should|must|recommend(?:ed)?|instruction|signal|execute|place)\s+"
    r"(?:a\s+)?(?:market\s+)?(?:buy|sell|hold|enter|exit|order)\b",
    re.IGNORECASE,
)
SIGNAL_PATTERN = re.compile(
    r"\b(?:probability|ev|edge|confidence)\b.{0,40}\b(?:signal|instruction)\b",
    re.IGNORECASE,
)


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _json_files() -> list[Path]:
    return sorted(ARTIFACT_DIR.glob("*.json"))


def test_candidate_inventory_and_selected_market_exist() -> None:
    inventory = _load(ARTIFACT_DIR / "candidate_inventory_016.json")
    selected = _load(ARTIFACT_DIR / "selected_market_016.json")

    assert (ARTIFACT_DIR / "candidate_inventory_016.md").exists()
    assert (ARTIFACT_DIR / "selected_market_016.md").exists()
    assert inventory["new_market_candidate_found"] is True
    assert selected["selected"] is True
    assert selected["market_id"] not in EXISTING_MARKET_IDS
    assert selected["already_tracked"] is False
    assert selected["live_network_used"] is False


def test_normalized_input_and_analysis_exist_for_selected_market() -> None:
    normalized = _load(ARTIFACT_DIR / "normalized_input_016.json")
    analysis = _load(ARTIFACT_DIR / "analysis_016.result.json")

    assert normalized["contract_version"] == "pmbot_one_market_input.v1"
    assert normalized["market_id"] == "573656"
    assert normalized["outcomes"] == ["Yes", "No"]
    assert normalized["source_packets"]
    assert normalized["missing_evidence"]
    assert analysis["contract_version"] == "pmbot_one_market_analysis_result.v1"
    assert analysis["market_id"] == "573656"
    assert analysis["paper_hypothesis_safety_label"] == "paper_only_non_executable_analysis_tracking"
    assert analysis["market_recommendation_generated"] is False
    assert analysis["probability_ev_edge_or_side_selection_generated"] is False
    assert analysis["orders_or_trading_actions"] is False


def test_paper_hypothesis_and_unresolved_outcome_are_paper_only() -> None:
    hypothesis = _load(ARTIFACT_DIR / "paper_hypothesis_016.json")
    outcome = _load(ARTIFACT_DIR / "outcome_record_unresolved_016.json")

    assert hypothesis["market_id"] == "573656"
    assert hypothesis["safety_label"] == "paper_only_non_executable_analysis_tracking"
    assert hypothesis["no_real_trade_decision"] is True
    assert hypothesis["market_recommendation_generated"] is False
    assert hypothesis["probability_ev_edge_or_side_selection_generated"] is False
    assert hypothesis["orders_or_trading_actions"] is False
    assert outcome["contract_version"] == "pmbot_one_market_outcome_record.v1"
    assert outcome["outcome_status"] == "unresolved"
    assert outcome["actual_outcome_summary"] == "unresolved"
    assert outcome["resolved_at"] is None
    assert outcome["outcome_resolution_invented"] is False


def test_manual_feedback_packet_is_pending_and_not_ready() -> None:
    manual_outcome = _load(ARTIFACT_DIR / "manual_outcome_resolution_packet_unresolved_016.json")
    feedback = _load(ARTIFACT_DIR / "manual_feedback_packet_pending_016.json")

    assert manual_outcome["outcome_status"] == "unresolved"
    assert manual_outcome["paper_hypothesis_result_label"] == "pending"
    assert manual_outcome["operator_approved"] is False
    assert feedback["outcome_status"] == "unresolved"
    assert feedback["feedback_ready"] is False
    assert feedback["outcome_resolution_invented"] is False


def test_expanded_queue_active_hypotheses_and_recheck_queue_track_six_markets() -> None:
    queue = _load(ARTIFACT_DIR / "market_queue_6_016.json")
    active = _load(ARTIFACT_DIR / "active_paper_hypotheses_6_016.json")
    recheck = _load(ARTIFACT_DIR / "outcome_recheck_queue_6_016.json")

    assert queue["tracked_market_count"] == 6
    assert {row["market_id"] for row in queue["items"]} == EXPECTED_MARKET_IDS
    assert active["active_hypothesis_count"] >= 6
    assert {row["market_id"] for row in active["active_paper_hypotheses"]} == EXPECTED_MARKET_IDS
    assert recheck["tracked_market_count"] == 6
    assert recheck["unresolved_outcome_count"] == 6
    assert recheck["local_resolution_record_count"] == 0
    assert all(row["outcome_status"] == "unresolved" for row in recheck["recheck_items"])


def test_source_dependency_update_tracks_new_market_sources() -> None:
    update = _load(ARTIFACT_DIR / "source_dependency_update_016.json")

    assert update["new_market_id"] == "573656"
    assert len(update["new_source_records"]) == 7
    assert len(update["new_source_dependencies"]) == 7
    assert update["source_learning_pending_until_outcome_resolution"] is True
    assert update["no_autonomous_training_performed"] is True


def test_safety_scan_passes_and_flags_are_safe() -> None:
    scan = _load(ARTIFACT_DIR / "add_market_safety_scan_016.result.json")

    assert (ARTIFACT_DIR / "add_market_safety_scan_016.md").exists()
    assert scan["safety_ok"] is True
    assert scan["issue_count"] == 0
    assert scan["add_market_safety_scan_passed"] is True
    assert scan["live_network_used"] is False
    assert scan["openrouter_calls_performed"] == 0
    assert scan["new_polymarket_api_calls_performed"] == 0
    assert scan["authenticated_endpoints_used"] is False
    assert scan["wallet_or_private_key_access"] is False
    assert scan["orders_or_trading_actions"] is False
    assert scan["runtime_or_dispatcher_changes"] is False
    assert scan["market_recommendation_generated"] is False
    assert scan["probability_ev_edge_or_side_selection_generated"] is False
    assert scan["outcome_resolution_invented"] is False


def test_no_outcome_invented_or_unsafe_signal_flags_in_json_artifacts() -> None:
    for path in _json_files():
        payload = _load(path)
        text = path.read_text(encoding="utf-8")

        assert '"outcome_status": "resolved"' not in text
        assert '"outcome_status": "ambiguous"' not in text
        assert '"outcome_status": "void"' not in text
        _assert_no_unsafe_signal_text(text)
        assert _flag_values(payload, "market_recommendation_generated") <= {False}
        assert _flag_values(payload, "probability_ev_edge_or_side_selection_generated") <= {False}
        assert _flag_values(payload, "orders_or_trading_actions") <= {False}
        assert _flag_values(payload, "wallet_or_private_key_access") <= {False}


def _flag_values(value: Any, key: str) -> set[Any]:
    found: set[Any] = set()
    if isinstance(value, dict):
        for item_key, item_value in value.items():
            if item_key == key:
                found.add(item_value)
            found.update(_flag_values(item_value, key))
    elif isinstance(value, list):
        for item in value:
            found.update(_flag_values(item, key))
    return found


def _assert_no_unsafe_signal_text(text: str) -> None:
    for line in text.splitlines():
        lowered = line.lower()
        if any(phrase in lowered for phrase in ("no ", "false", "prohibited", "not generated")):
            continue
        assert ACTION_PATTERN.search(line) is None
        assert SIGNAL_PATTERN.search(line) is None
