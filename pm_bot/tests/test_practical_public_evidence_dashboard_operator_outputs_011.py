from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

ARTIFACT_DIR = Path("pm_bot/practical/artifacts/public_evidence_dashboard_011")
ACTION_PATTERN = re.compile(
    r"\b(?:should|must|recommend(?:ed)?|instruction|signal|execute|place)\s+"
    r"(?:a\s+)?(?:market\s+)?(?:buy|sell|hold|enter|exit|order)\b",
    re.IGNORECASE,
)
SIGNAL_PATTERN = re.compile(r"\b(?:probability|ev|edge|confidence)\b.{0,40}\b(?:signal|instruction)\b", re.IGNORECASE)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _assert_no_unsafe_flags(value: Any) -> None:
    if isinstance(value, dict):
        for key, nested in value.items():
            if key in {
                "authenticated_endpoints_used",
                "market_recommendation_generated",
                "orders_or_trading_actions",
                "probability_ev_edge_or_side_selection_generated",
                "runtime_or_dispatcher_changes",
                "wallet_or_private_key_access",
                "automatic_analysis_update_performed",
                "new_live_fetch_performed",
            }:
                assert nested is False
            if key in {"openrouter_calls_performed", "polymarket_api_calls_performed", "new_polymarket_api_calls_performed"}:
                assert nested == 0
            _assert_no_unsafe_flags(nested)
    elif isinstance(value, list):
        for item in value:
            _assert_no_unsafe_flags(item)


def test_operator_output_artifacts_exist() -> None:
    for filename in [
        "operator_morning_card_011.json",
        "operator_morning_card_011.md",
        "paper_tracking_dashboard_delta_011.json",
        "paper_tracking_dashboard_delta_011.md",
        "unresolved_outcome_evidence_watchlist_011.json",
        "unresolved_outcome_evidence_watchlist_011.md",
        "source_url_backlog_011.json",
        "source_url_backlog_011.md",
        "public_evidence_dashboard_safety_scan_011.result.json",
        "public_evidence_dashboard_safety_scan_011.md",
    ]:
        assert (ARTIFACT_DIR / filename).exists()


def test_dashboard_safety_scan_passes_and_required_flags_are_safe() -> None:
    scan = _load(ARTIFACT_DIR / "public_evidence_dashboard_safety_scan_011.result.json")

    assert scan["safety_ok"] is True
    assert scan["public_evidence_dashboard_safety_scan_passed"] is True
    assert scan["live_network_used"] is False
    assert scan["openrouter_calls_performed"] == 0
    assert scan["new_polymarket_api_calls_performed"] == 0
    assert scan["authenticated_endpoints_used"] is False
    assert scan["wallet_or_private_key_access"] is False
    assert scan["orders_or_trading_actions"] is False
    assert scan["runtime_or_dispatcher_changes"] is False
    assert scan["market_recommendation_generated"] is False
    assert scan["probability_ev_edge_or_side_selection_generated"] is False
    assert scan["automatic_analysis_update_performed"] is False
    assert scan["scheduler_background_worker_or_polling"] is False
    assert scan["no_autonomous_trading"] is True


def test_operator_outputs_have_no_trading_recommendation_language() -> None:
    text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in ARTIFACT_DIR.rglob("*")
        if path.suffix.lower() in {".json", ".md"}
    )

    assert ACTION_PATTERN.search(text) is None
    assert SIGNAL_PATTERN.search(text) is None


def test_operator_outputs_have_no_wallet_order_trading_or_runtime_unsafe_flags() -> None:
    for path in ARTIFACT_DIR.rglob("*.json"):
        _assert_no_unsafe_flags(_load(path))
