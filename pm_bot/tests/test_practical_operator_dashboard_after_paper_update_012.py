from __future__ import annotations

import json
from pathlib import Path

ARTIFACT_DIR = Path("pm_bot/practical/artifacts/paper_update_application_012")
DASHBOARD_JSON = ARTIFACT_DIR / "operator_dashboard_after_paper_update_012.json"
DASHBOARD_MD = ARTIFACT_DIR / "operator_dashboard_after_paper_update_012.md"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_dashboard_after_update_exists() -> None:
    dashboard = _load(DASHBOARD_JSON)

    assert DASHBOARD_MD.exists()
    assert dashboard["contract_version"] == "pmbot_operator_dashboard_after_paper_update.v1"
    assert dashboard["dashboard_id"] == "operator-dashboard-after-paper-update-012"


def test_dashboard_after_update_shows_tracking_state() -> None:
    dashboard = _load(DASHBOARD_JSON)

    assert len(dashboard["tracked_markets"]) == 5
    assert dashboard["applied_paper_update_count"] == 1
    assert dashboard["remaining_pending_update_count"] == 0
    assert len(dashboard["unresolved_outcomes"]) == 5
    assert len(dashboard["evidence_packet_links"]) >= 1
    assert dashboard["source_status_summary"]["source_record_count"] >= 5
    assert dashboard["next_operator_actions"]


def test_dashboard_after_update_has_safe_flags() -> None:
    dashboard = _load(DASHBOARD_JSON)
    safety = dashboard["safety_summary"]

    assert safety["live_network_used"] is False
    assert safety["openrouter_calls_performed"] == 0
    assert safety["new_polymarket_api_calls_performed"] == 0
    assert safety["authenticated_endpoints_used"] is False
    assert safety["wallet_or_private_key_access"] is False
    assert safety["orders_or_trading_actions"] is False
    assert safety["runtime_or_dispatcher_changes"] is False
    assert safety["market_recommendation_generated"] is False
    assert safety["probability_ev_edge_or_side_selection_generated"] is False
    assert safety["automatic_analysis_update_performed"] is False
