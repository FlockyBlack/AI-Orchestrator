from __future__ import annotations

import json
from pathlib import Path

ARTIFACT_DIR = Path("pm_bot/practical/artifacts/manual_outcome_feedback_014")
SOURCE_ARTIFACT_DIR = Path("pm_bot/practical/artifacts/outcome_recheck_source_learning_013")
MARKET_IDS = {"563650", "597964", "598936", "691547", "692258"}


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_five_unresolved_market_feedback_packets_exist_if_source_artifacts_exist() -> None:
    assert SOURCE_ARTIFACT_DIR.exists()

    market_dirs = {path.name for path in (ARTIFACT_DIR / "markets").iterdir() if path.is_dir()}

    assert market_dirs == MARKET_IDS
    for market_id in MARKET_IDS:
        market_dir = ARTIFACT_DIR / "markets" / market_id
        assert (market_dir / "manual_outcome_resolution_packet.unresolved.json").exists()
        assert (market_dir / "manual_outcome_resolution_packet.unresolved.md").exists()
        assert (market_dir / "paper_hypothesis_feedback.pending.json").exists()
        assert (market_dir / "paper_hypothesis_feedback.pending.md").exists()
        assert (market_dir / "source_accuracy_feedback.pending.json").exists()
        assert (market_dir / "source_accuracy_feedback.pending.md").exists()
        assert (market_dir / "manual_feedback_packet.pending.json").exists()
        assert (market_dir / "manual_feedback_packet.pending.md").exists()


def test_feedback_ready_false_for_current_unresolved_markets() -> None:
    for market_id in MARKET_IDS:
        packet = _load(ARTIFACT_DIR / "markets" / market_id / "manual_feedback_packet.pending.json")

        assert packet["outcome_status"] == "unresolved"
        assert packet["feedback_ready"] is False


def test_feedback_readiness_dashboard_exists() -> None:
    dashboard = _load(ARTIFACT_DIR / "feedback_readiness_dashboard_014.json")

    assert (ARTIFACT_DIR / "feedback_readiness_dashboard_014.md").exists()
    assert dashboard["tracked_market_count"] == 5
    assert dashboard["unresolved_count"] == 5
    assert dashboard["feedback_ready_count"] == 0


def test_operator_guide_exists() -> None:
    guide = _load(ARTIFACT_DIR / "manual_outcome_operator_guide_014.json")

    assert (ARTIFACT_DIR / "manual_outcome_operator_guide_014.md").exists()
    assert guide["contract_version"] == "pmbot_manual_outcome_operator_guide.v1"
    assert "actual_outcome_summary" in guide["resolved_market_required_fields"]


def test_source_learning_update_candidate_unavailable_without_resolved_outcomes() -> None:
    candidate = _load(ARTIFACT_DIR / "source_learning_update_candidate_from_feedback_014.json")

    assert (ARTIFACT_DIR / "source_learning_update_candidate_from_feedback_014.md").exists()
    assert candidate["update_candidate_available"] is False
    assert candidate["reason"] == "no resolved local outcome records"
    assert candidate["pending_market_count"] == 5


def test_operator_console_feedback_loop_exists() -> None:
    console = _load(ARTIFACT_DIR / "operator_console_feedback_loop_014.json")

    assert (ARTIFACT_DIR / "operator_console_feedback_loop_014.md").exists()
    assert console["unresolved_market_count"] == 5
    assert console["feedback_ready"] is False
    assert console["outcome_packets_prepared"] is True


def test_safety_scan_passes() -> None:
    scan = _load(ARTIFACT_DIR / "manual_outcome_feedback_safety_scan_014.result.json")

    assert (ARTIFACT_DIR / "manual_outcome_feedback_safety_scan_014.md").exists()
    assert scan["safety_ok"] is True
    assert scan["issue_count"] == 0
    assert scan["manual_outcome_feedback_safety_scan_passed"] is True


def test_no_unsafe_flags() -> None:
    scan = _load(ARTIFACT_DIR / "manual_outcome_feedback_safety_scan_014.result.json")

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
