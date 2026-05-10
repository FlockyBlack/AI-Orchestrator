from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

ARTIFACT_DIR = Path("pm_bot/practical/artifacts/manual_url_collection_017b")

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


def test_operator_card_approval_template_and_dashboard_exist() -> None:
    card = _load("manual_url_collection_operator_card_017b.json")
    approval = _load("future_new_market_fetch_approval_template_017b.json")
    dashboard = _load("public_evidence_dashboard_manual_url_pending_017b.json")

    assert (ARTIFACT_DIR / "manual_url_collection_operator_card_017b.md").exists()
    assert (ARTIFACT_DIR / "future_new_market_fetch_approval_template_017b.md").exists()
    assert (ARTIFACT_DIR / "public_evidence_dashboard_manual_url_pending_017b.md").exists()
    assert card["market"]["market_id"] == "573656"
    assert approval["approval_for_future_task_id"] == "ORCH-PMBOT-PRACTICAL-018-FIRST-PUBLIC-EVIDENCE-FETCH-FOR-NEW-MARKET"
    assert approval["approval_status"] == "pending"
    assert approval["operator_approval_granted"] is False
    assert dashboard["new_market_manual_url_collection_state"]["market_id"] == "573656"


def test_dashboard_tracks_six_markets_and_new_market_pending_state() -> None:
    dashboard = _load("public_evidence_dashboard_manual_url_pending_017b.json")

    assert dashboard["tracked_market_count"] == 6
    assert any(row["market_id"] == "573656" for row in dashboard["markets"])
    assert dashboard["missing_url_count"] == 3
    assert dashboard["manual_url_collection_required"] is True
    assert dashboard["executable_request_count"] == 0
    assert dashboard["future_fetch_ready"] is False
    assert dashboard["next_operator_action"] == "fill manual URL collection packet"


def test_safety_scan_passes_with_required_confirmations() -> None:
    scan = _load("manual_url_collection_safety_scan_017b.result.json")

    assert (ARTIFACT_DIR / "manual_url_collection_safety_scan_017b.md").exists()
    assert scan["safety_ok"] is True
    assert scan["issue_count"] == 0
    assert scan["manual_url_collection_safety_scan_passed"] is True
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


def test_no_trading_language_or_signal_flags_in_017b_artifacts() -> None:
    for path in sorted(ARTIFACT_DIR.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        text = path.read_text(encoding="utf-8")

        assert '"outcome_status": "resolved"' not in text
        assert _flag_values(payload, "market_recommendation_generated") <= {False}
        assert _flag_values(payload, "probability_ev_edge_or_side_selection_generated") <= {False}
        assert _flag_values(payload, "orders_or_trading_actions") <= {False}
        assert _flag_values(payload, "wallet_or_private_key_access") <= {False}
        _assert_no_unsafe_signal_text(text)


def test_no_wallet_order_trading_unsafe_flags() -> None:
    for name in [
        "manual_public_url_collection_packet_573656.json",
        "future_fetch_manifest_from_unfilled_packet_017b.json",
        "future_new_market_fetch_approval_template_017b.json",
        "manual_url_collection_operator_card_017b.json",
    ]:
        payload = _load(name)
        assert _flag_values(payload, "wallet_or_private_key_access") <= {False}
        assert _flag_values(payload, "orders_or_trading_actions") <= {False}
        assert _flag_values(payload, "runtime_or_dispatcher_changes") <= {False}


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
        if any(phrase in lowered for phrase in ("no ", "false", "prohibited", "not generated", "blocked")):
            continue
        assert ACTION_PATTERN.search(line) is None
        assert SIGNAL_PATTERN.search(line) is None
