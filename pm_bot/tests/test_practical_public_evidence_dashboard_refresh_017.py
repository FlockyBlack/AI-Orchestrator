from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

ARTIFACT_DIR = Path("pm_bot/practical/artifacts/public_evidence_plan_017")

ACTION_PATTERN = re.compile(
    r"\b(?:should|must|recommend(?:ed)?|instruction|signal|execute|place)\s+"
    r"(?:a\s+)?(?:market\s+)?(?:buy|sell|hold|enter|exit|order)\b",
    re.IGNORECASE,
)
SIGNAL_PATTERN = re.compile(
    r"\b(?:probability|ev|edge|confidence)\b.{0,40}\b(?:signal|instruction)\b",
    re.IGNORECASE,
)


def _load(name: str) -> dict[str, Any]:
    return json.loads((ARTIFACT_DIR / name).read_text(encoding="utf-8"))


def test_refreshed_dashboard_tracks_six_markets_and_new_market() -> None:
    dashboard = _load("public_evidence_dashboard_6_market_refresh_017.json")

    assert (ARTIFACT_DIR / "public_evidence_dashboard_6_market_refresh_017.md").exists()
    assert dashboard["contract_version"] == "pmbot_public_evidence_dashboard_6_market_refresh.v1"
    assert dashboard["tracked_market_count"] == 6
    assert {row["market_id"] for row in dashboard["markets"]} == {
        "563650",
        "573656",
        "597964",
        "598936",
        "691547",
        "692258",
    }
    assert dashboard["new_market_evidence_plan_status"]["market_id"] == "573656"


def test_source_dependency_map_daily_refresh_and_operator_card_exist() -> None:
    source_map = _load("source_dependency_map_6_markets_017.json")
    daily = _load("daily_workflow_public_evidence_refresh_017.json")
    card = _load("new_market_public_evidence_operator_card_017.json")

    assert (ARTIFACT_DIR / "source_dependency_map_6_markets_017.md").exists()
    assert (ARTIFACT_DIR / "daily_workflow_public_evidence_refresh_017.md").exists()
    assert (ARTIFACT_DIR / "new_market_public_evidence_operator_card_017.md").exists()
    assert any(row["market_id"] == "573656" for row in source_map["market_to_source_links"])
    assert source_map["new_market_source_dependencies"]
    assert daily["tracked_market_count"] == 6
    assert daily["unresolved_outcome_count"] == 6
    assert daily["feedback_ready_count"] == 0
    assert card["market"]["market_id"] == "573656"


def test_safety_scan_passes_and_flags_are_safe() -> None:
    scan = _load("public_evidence_plan_safety_scan_017.result.json")

    assert (ARTIFACT_DIR / "public_evidence_plan_safety_scan_017.md").exists()
    assert scan["safety_ok"] is True
    assert scan["issue_count"] == 0
    assert scan["public_evidence_plan_safety_scan_passed"] is True
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
    assert scan["no_scheduler_daemon_background_worker"] is True
    assert scan["no_autonomous_trading"] is True


def test_no_recommendations_or_unsafe_signal_flags_in_017_artifacts() -> None:
    for path in sorted(ARTIFACT_DIR.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        text = path.read_text(encoding="utf-8")

        assert '"outcome_status": "resolved"' not in text
        assert _flag_values(payload, "market_recommendation_generated") <= {False}
        assert _flag_values(payload, "probability_ev_edge_or_side_selection_generated") <= {False}
        assert _flag_values(payload, "orders_or_trading_actions") <= {False}
        assert _flag_values(payload, "wallet_or_private_key_access") <= {False}
        _assert_no_unsafe_signal_text(text)


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
