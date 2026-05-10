from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

ARTIFACT_DIR = Path("pm_bot/practical/artifacts/manual_url_collection_017c")
DOCS_DIR = Path("docs")

ACTION_PATTERN = re.compile(
    r"\b(?:should|must|recommend(?:ed)?|instruction|signal|execute|place)\s+"
    r"(?:a\s+)?(?:market\s+)?(?:buy|sell|hold|enter|exit|order)\b",
    re.IGNORECASE,
)
SIGNAL_PATTERN = re.compile(r"\b(?:probability|ev|edge|confidence)\b.{0,40}\b(?:signal|instruction)\b", re.IGNORECASE)


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def test_dashboard_operator_card_and_scoped_approval_outputs_exist() -> None:
    dashboard = _load(ARTIFACT_DIR / "public_evidence_dashboard_url_filled_pending_approval_017c.json")
    operator_card = _load(ARTIFACT_DIR / "manual_url_filled_operator_card_017c.json")
    approval = _load(ARTIFACT_DIR / "new_market_fetch_scoped_approval_pending_017c.json")

    assert (ARTIFACT_DIR / "public_evidence_dashboard_url_filled_pending_approval_017c.md").exists()
    assert (ARTIFACT_DIR / "manual_url_filled_operator_card_017c.md").exists()
    assert (ARTIFACT_DIR / "new_market_fetch_scoped_approval_pending_017c.md").exists()
    assert dashboard["tracked_market_count"] == 6
    assert dashboard["market_id"] == "573656"
    assert any(row["market_id"] == "573656" for row in dashboard["markets"])
    assert dashboard["filled_url_count"] == 3
    assert dashboard["executable_request_count"] == 3
    assert dashboard["missing_url_count"] == 0
    assert dashboard["blocked_request_count"] == 0
    assert dashboard["ready_for_operator_approval"] is True
    assert dashboard["approval_pending"] is True
    assert operator_card["market"]["market_id"] == "573656"
    assert operator_card["approval_still_pending"] is True
    assert approval["approval_for_future_task_id"] == "ORCH-PMBOT-PRACTICAL-018-FIRST-PUBLIC-EVIDENCE-FETCH-FOR-NEW-MARKET"
    assert approval["approval_status"] == "pending"
    assert approval["operator_approval_required"] is True
    assert approval["operator_approval_granted"] is False
    assert approval["max_request_count"] == 3
    assert approval["executable_request_count"] == 3
    assert approval["reusable"] is False
    assert approval["expires_after_future_task"] is True


def test_safety_scan_and_result_summary_pass() -> None:
    safety_scan = _load(ARTIFACT_DIR / "manual_url_filled_safety_scan_017c.result.json")
    result = _load(DOCS_DIR / "ORCH_PMBOT_PRACTICAL_017C_RESULT.json")

    assert (ARTIFACT_DIR / "manual_url_filled_safety_scan_017c.md").exists()
    assert safety_scan["manual_url_filled_safety_scan_passed"] is True
    assert safety_scan["safety_ok"] is True
    assert safety_scan["issue_count"] == 0
    assert safety_scan["live_network_used"] is False
    assert safety_scan["openrouter_calls_performed"] == 0
    assert safety_scan["new_polymarket_api_calls_performed"] == 0
    assert safety_scan["authenticated_endpoints_used"] is False
    assert safety_scan["wallet_or_private_key_access"] is False
    assert safety_scan["orders_or_trading_actions"] is False
    assert safety_scan["runtime_or_dispatcher_changes"] is False
    assert safety_scan["market_recommendation_generated"] is False
    assert safety_scan["probability_ev_edge_or_side_selection_generated"] is False
    assert safety_scan["outcome_resolution_invented"] is False
    assert safety_scan["no_scheduler_daemon_background_worker"] is True
    assert safety_scan["no_autonomous_trading"] is True
    assert result["selected_market_id"] == "573656"
    assert result["supplied_url_count"] == 3
    assert result["valid_url_count"] == 3
    assert result["manual_url_filled_safety_scan_passed"] is True
    assert result["validation_passed"] is True
    assert result["safety_ok"] is True


def test_operator_outputs_have_no_actionable_trading_language() -> None:
    paths = [
        ARTIFACT_DIR / "public_evidence_dashboard_url_filled_pending_approval_017c.md",
        ARTIFACT_DIR / "manual_url_filled_operator_card_017c.md",
        ARTIFACT_DIR / "new_market_fetch_scoped_approval_pending_017c.md",
        DOCS_DIR / "PMBOT_FILL_NEW_MARKET_PUBLIC_URL_PACKET.md",
        DOCS_DIR / "ORCH_PMBOT_PRACTICAL_017C_FILL_NEW_MARKET_PUBLIC_URL_PACKET_MANUALLY.md",
    ]

    for path in paths:
        text = path.read_text(encoding="utf-8")
        assert not ACTION_PATTERN.search(text), path
        assert not SIGNAL_PATTERN.search(text), path


def test_no_wallet_order_trading_or_unsafe_flags_are_set() -> None:
    payloads = [
        _load(ARTIFACT_DIR / "public_evidence_dashboard_url_filled_pending_approval_017c.json"),
        _load(ARTIFACT_DIR / "manual_url_filled_operator_card_017c.json"),
        _load(ARTIFACT_DIR / "new_market_fetch_scoped_approval_pending_017c.json"),
        _load(ARTIFACT_DIR / "manual_url_filled_safety_scan_017c.result.json"),
        _load(DOCS_DIR / "ORCH_PMBOT_PRACTICAL_017C_RESULT.json"),
    ]

    for payload in payloads:
        assert _flag_values(payload, "authenticated_endpoints_used") <= {False}
        assert _flag_values(payload, "market_recommendation_generated") <= {False}
        assert _flag_values(payload, "probability_ev_edge_or_side_selection_generated") <= {False}
        assert _flag_values(payload, "orders_or_trading_actions") <= {False}
        assert _flag_values(payload, "wallet_or_private_key_access") <= {False}
        assert _flag_values(payload, "runtime_or_dispatcher_changes") <= {False}
        assert _count_values(payload, "openrouter_calls_performed") <= {0}
        assert _count_values(payload, "new_polymarket_api_calls_performed") <= {0}


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


def _count_values(value: Any, key: str) -> set[Any]:
    found: set[Any] = set()
    if isinstance(value, dict):
        for item_key, item_value in value.items():
            if item_key == key:
                found.add(item_value)
            found.update(_count_values(item_value, key))
    elif isinstance(value, list):
        for item in value:
            found.update(_count_values(item, key))
    return found
