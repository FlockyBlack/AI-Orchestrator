from __future__ import annotations

import json
from pathlib import Path

ARTIFACT_DIR = Path("pm_bot/practical/artifacts/public_evidence_review_009")
LEARNING_JSON = ARTIFACT_DIR / "source_accessibility_learning_009.json"
LEARNING_MD = ARTIFACT_DIR / "source_accessibility_learning_009.md"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_source_accessibility_learning_artifact_exists() -> None:
    learning = _load(LEARNING_JSON)

    assert LEARNING_MD.exists()
    assert learning["contract_version"] == "pmbot_source_accessibility_learning.v1"
    assert learning["learning_id"] == "source-accessibility-learning-009"


def test_source_accessibility_learning_has_reachable_and_failed_source_groups() -> None:
    learning = _load(LEARNING_JSON)

    assert learning["source_accessibility_records"]
    assert learning["reachable_sources"]
    assert learning["failed_sources"]
    assert learning["replay_usable_sources"]
    assert learning["sources_requiring_url_fix"]
    assert learning["sources_requiring_manual_review"]


def test_source_accessibility_learning_safety_flags_are_safe() -> None:
    learning = _load(LEARNING_JSON)

    assert learning["no_autonomous_training_performed"] is True
    assert learning["no_real_trade_decision"] is True
    assert learning["market_recommendation_generated"] is False
    assert learning["probability_ev_edge_or_side_selection_generated"] is False
    assert learning["orders_or_trading_actions"] is False
    assert learning["wallet_or_private_key_access"] is False
    assert learning["no_live_fetch_performed_in_this_task"] is True


def test_source_accessibility_learning_includes_handling_updates() -> None:
    learning = _load(LEARNING_JSON)

    assert learning["recommended_source_handling_updates"]
    assert all(item["requires_operator_review"] is True for item in learning["recommended_source_handling_updates"])
