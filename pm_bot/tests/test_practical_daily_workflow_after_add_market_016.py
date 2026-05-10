from __future__ import annotations

import json
from pathlib import Path

ARTIFACT_DIR = Path("pm_bot/practical/artifacts/add_market_016")


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_daily_workflow_summary_after_add_exists_and_tracks_six() -> None:
    summary = _load(ARTIFACT_DIR / "daily_workflow_summary_after_add_016.json")

    assert (ARTIFACT_DIR / "daily_workflow_summary_after_add_016.md").exists()
    assert summary["contract_version"] == "pmbot_daily_workflow_summary.v1"
    assert summary["summary_id"] == "daily-workflow-summary-after-add-016"
    assert summary["tracked_market_count"] == 6
    assert summary["active_paper_hypotheses_count"] >= 6
    assert summary["unresolved_outcome_count"] == 6
    assert summary["feedback_ready_count"] == 0
    assert any(row["market_id"] == "573656" for row in summary["tracked_markets"])


def test_operator_dashboard_after_add_exists() -> None:
    dashboard = _load(ARTIFACT_DIR / "operator_dashboard_after_add_market_016.json")

    assert (ARTIFACT_DIR / "operator_dashboard_after_add_market_016.md").exists()
    assert dashboard["contract_version"] == "pmbot_operator_dashboard_after_add_market.v1"
    assert dashboard["new_market_added"] is True
    assert dashboard["new_market"]["market_id"] == "573656"
    assert dashboard["total_tracked_markets"] == 6
    assert dashboard["unresolved_outcome_status"] == "unresolved"
    assert dashboard["source_dependencies"]
    assert dashboard["what_operator_should_inspect_next"]


def test_before_after_delta_exists_and_has_expected_counts() -> None:
    delta = _load(ARTIFACT_DIR / "add_market_tracking_delta_016.json")

    assert (ARTIFACT_DIR / "add_market_tracking_delta_016.md").exists()
    assert delta["contract_version"] == "pmbot_add_market_tracking_delta.v1"
    assert delta["before_tracked_market_count"] == 5
    assert delta["after_tracked_market_count"] == 6
    assert delta["added_market_id"] == "573656"
    assert delta["active_hypothesis_count_delta"] >= 1
    assert delta["unresolved_outcome_count_delta"] == 1
    assert delta["feedback_ready_count_delta"] == 0
    assert delta["source_records_delta"] == 7


def test_next_actions_exist_and_remain_non_executable() -> None:
    actions = _load(ARTIFACT_DIR / "new_market_operator_next_actions_016.json")

    assert (ARTIFACT_DIR / "new_market_operator_next_actions_016.md").exists()
    assert actions["contract_version"] == "pmbot_new_market_operator_next_actions.v1"
    assert actions["market_id"] == "573656"
    action_ids = {row["action_id"] for row in actions["actions"]}
    assert "inspect_analysis_card" in action_ids
    assert "inspect_paper_hypothesis" in action_ids
    assert "inspect_missing_evidence" in action_ids
    assert "decide_public_evidence_fetch_prep_later" in action_ids
    assert "wait_for_outcome_resolution" in action_ids
    assert "no_trading_action" in action_ids


def test_feedback_ready_count_remains_zero_without_resolution() -> None:
    feedback = _load(ARTIFACT_DIR / "feedback_readiness_dashboard_after_add_016.json")
    manual_packet = _load(ARTIFACT_DIR / "manual_feedback_packet_pending_016.json")

    assert feedback["tracked_market_count"] == 6
    assert feedback["unresolved_count"] == 6
    assert feedback["feedback_ready_count"] == 0
    assert feedback["resolved_local_outcome_packet_count"] == 0
    assert manual_packet["feedback_ready"] is False


def test_safety_flags_safe_across_daily_workflow_after_add() -> None:
    summary = _load(ARTIFACT_DIR / "daily_workflow_summary_after_add_016.json")
    dashboard = _load(ARTIFACT_DIR / "operator_dashboard_after_add_market_016.json")
    delta = _load(ARTIFACT_DIR / "add_market_tracking_delta_016.json")
    scan = _load(ARTIFACT_DIR / "add_market_safety_scan_016.result.json")

    for payload in (summary, dashboard, delta):
        safety = payload["safety_summary"]
        assert safety["live_network_used"] is False
        assert safety["openrouter_calls_performed"] == 0
        assert safety["new_polymarket_api_calls_performed"] == 0
        assert safety["authenticated_endpoints_used"] is False
        assert safety["wallet_or_private_key_access"] is False
        assert safety["orders_or_trading_actions"] is False
        assert safety["runtime_or_dispatcher_changes"] is False
        assert safety["market_recommendation_generated"] is False
        assert safety["probability_ev_edge_or_side_selection_generated"] is False
        assert safety["outcome_resolution_invented"] is False
        assert safety["no_scheduler_daemon_background_worker"] is True
        assert safety["no_autonomous_trading"] is True

    assert scan["safety_ok"] is True
    assert scan["issue_count"] == 0
