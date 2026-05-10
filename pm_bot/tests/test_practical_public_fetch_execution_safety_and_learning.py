from __future__ import annotations

import json
from pathlib import Path

ARTIFACT_DIR = Path("pm_bot/practical/artifacts/public_read_only_fetch_execution_008")


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_public_fetch_execution_safety_scan_passes() -> None:
    scan = _load(ARTIFACT_DIR / "public_fetch_execution_safety_scan_008.result.json")

    assert scan["safety_ok"] is True
    assert scan["issue_count"] == 0
    assert scan["public_fetch_execution_safety_scan_passed"] is True
    assert scan["openrouter_calls_performed"] == 0
    assert scan["authenticated_endpoints_used"] is False
    assert scan["wallet_or_private_key_access"] is False
    assert scan["orders_or_trading_actions"] is False
    assert scan["runtime_or_dispatcher_changes"] is False
    assert scan["market_recommendation_generated"] is False
    assert scan["probability_ev_edge_or_side_selection_generated"] is False
    assert scan["automatic_analysis_update_performed"] is False
    assert scan["no_scheduler_background_worker_polling"] is True
    assert scan["no_autonomous_trading"] is True


def test_source_learning_pending_artifact_is_paper_only() -> None:
    source_learning = _load(ARTIFACT_DIR / "source_learning_public_fetch_pending_008.json")

    assert source_learning["contract_version"] == "pmbot_source_learning_public_fetch_pending.v1"
    assert source_learning["sources_fetched"] or source_learning["sources_blocked"]
    assert source_learning["source_accessibility_observations"]
    assert source_learning["markets_affected"]
    assert source_learning["what_can_be_learned_now_about_source_freshness_accessibility"]
    assert source_learning["what_can_be_learned_only_after_outcome_resolution"]
    assert source_learning["no_autonomous_training_performed"] is True
    assert source_learning["safety_summary"]["wallet_or_private_key_access"] is False
    assert source_learning["safety_summary"]["orders_or_trading_actions"] is False
    assert source_learning["safety_summary"]["runtime_or_dispatcher_changes"] is False


def test_operator_card_exists_and_keeps_analysis_update_nonautomatic() -> None:
    card = _load(ARTIFACT_DIR / "operator_public_fetch_execution_card_008.json")

    assert card["contract_version"] == "pmbot_operator_public_fetch_execution_card.v1"
    assert card["card_id"] == "operator-public-fetch-execution-card-008"
    assert card["automatic_analysis_update_performed"] is False
    assert card["operator_should_inspect_next"]
    assert card["what_remains_blocked"]
    assert card["safety_summary"]["market_recommendation_generated"] is False
    assert card["safety_summary"]["probability_ev_edge_or_side_selection_generated"] is False
