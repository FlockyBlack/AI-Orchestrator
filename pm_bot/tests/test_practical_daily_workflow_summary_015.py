from __future__ import annotations

import json
from pathlib import Path

ARTIFACT_DIR = Path("pm_bot/practical/artifacts/daily_workflow_015")
SUMMARY_JSON = ARTIFACT_DIR / "daily_workflow_summary_015.json"
SUMMARY_MD = ARTIFACT_DIR / "daily_workflow_summary_015.md"
MARKET_IDS = {"563650", "597964", "598936", "691547", "692258"}


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_daily_workflow_summary_json_exists_and_validates() -> None:
    summary = _load(SUMMARY_JSON)

    assert SUMMARY_MD.exists()
    assert summary["contract_version"] == "pmbot_daily_workflow_summary.v1"
    assert summary["summary_id"] == "daily-workflow-summary-015"


def test_daily_workflow_summary_includes_current_counts() -> None:
    summary = _load(SUMMARY_JSON)

    assert summary["tracked_market_count"] == 5
    assert {row["market_id"] for row in summary["tracked_markets"]} == MARKET_IDS
    assert summary["active_paper_hypotheses_count"] == 5
    assert summary["applied_paper_update_count"] == 1
    assert summary["unresolved_outcome_count"] == 5
    assert summary["feedback_ready_count"] == 0
    assert summary["public_evidence_packet_count"] == 2
    assert summary["source_records_count"] == 5
    assert summary["source_url_backlog_count"] == 3


def test_daily_workflow_summary_lists_operator_actions_and_dashboards() -> None:
    summary = _load(SUMMARY_JSON)
    dashboard_paths = {row["path"] for row in summary["dashboard_files_to_open"]}

    assert summary["next_operator_actions"]
    assert "pm_bot/practical/artifacts/daily_workflow_015/operator_quickstart_card_015.md" in dashboard_paths
    assert "pm_bot/practical/artifacts/manual_outcome_feedback_014/feedback_readiness_dashboard_014.md" in dashboard_paths
    assert "pm_bot/practical/artifacts/outcome_recheck_source_learning_013/outcome_recheck_queue_013.md" in dashboard_paths
    assert "pm_bot/practical/artifacts/public_evidence_dashboard_011/public_evidence_tracking_dashboard_011.md" in dashboard_paths


def test_daily_workflow_summary_safety_flags_safe() -> None:
    summary = _load(SUMMARY_JSON)
    safety = summary["safety_summary"]

    assert safety["live_network_used"] is False
    assert safety["new_live_fetch_performed"] is False
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
