from __future__ import annotations

import json
from pathlib import Path

ARTIFACT_DIR = Path("pm_bot/practical/artifacts/public_evidence_dashboard_011")
DASHBOARD_JSON = ARTIFACT_DIR / "public_evidence_tracking_dashboard_011.json"
DASHBOARD_MD = ARTIFACT_DIR / "public_evidence_tracking_dashboard_011.md"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_dashboard_json_exists_and_validates() -> None:
    dashboard = _load(DASHBOARD_JSON)

    assert DASHBOARD_MD.exists()
    assert dashboard["contract_version"] == "pmbot_public_evidence_tracking_dashboard.v1"
    assert dashboard["dashboard_id"] == "public-evidence-tracking-dashboard-011"


def test_dashboard_includes_five_tracked_markets_and_unresolved_outcomes() -> None:
    dashboard = _load(DASHBOARD_JSON)

    assert len(dashboard["tracked_markets"]) == 5
    assert {row["market_id"] for row in dashboard["tracked_markets"]} == {
        "563650",
        "597964",
        "598936",
        "691547",
        "692258",
    }
    assert len(dashboard["unresolved_outcomes"]) == 5
    assert all(row["outcome_status"] == "unresolved" for row in dashboard["unresolved_outcomes"])


def test_dashboard_includes_first_and_second_public_evidence_packets() -> None:
    dashboard = _load(DASHBOARD_JSON)
    packet_ids = {row["evidence_packet_id"] for row in dashboard["evidence_packets"]}

    assert len(packet_ids) == 2
    assert any(packet_id.startswith("public_fetch_008_563650") for packet_id in packet_ids)
    assert any(packet_id.startswith("public_fetch_010_public_fetch_request_intent_006_08_691547") for packet_id in packet_ids)


def test_dashboard_includes_pending_updates_source_summary_and_next_actions() -> None:
    dashboard = _load(DASHBOARD_JSON)

    assert dashboard["update_candidates"]
    assert dashboard["source_status_summary"]["source_record_count"] >= 5
    assert dashboard["source_status_summary"]["reachable_source_count"] >= 2
    assert dashboard["next_operator_actions"]


def test_dashboard_safety_flags_are_safe() -> None:
    dashboard = _load(DASHBOARD_JSON)
    safety = dashboard["safety_summary"]

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
    assert safety["automatic_analysis_update_performed"] is False
