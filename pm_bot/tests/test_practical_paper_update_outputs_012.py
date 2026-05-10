from __future__ import annotations

import json
from pathlib import Path

from pm_bot.practical.practical_safety_scan import run_practical_safety_scan

ARTIFACT_DIR = Path("pm_bot/practical/artifacts/paper_update_application_012")
COMPARISON_JSON = ARTIFACT_DIR / "paper_update_before_after_comparison_012.json"
MORNING_CARD_JSON = ARTIFACT_DIR / "operator_morning_card_after_update_012.json"
SOURCE_LEARNING_JSON = ARTIFACT_DIR / "source_learning_after_paper_update_012.json"
SAFETY_SCAN_JSON = ARTIFACT_DIR / "paper_update_application_safety_scan_012.result.json"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_before_after_comparison_exists_and_is_paper_only() -> None:
    comparison = _load(COMPARISON_JSON)

    assert (ARTIFACT_DIR / "paper_update_before_after_comparison_012.md").exists()
    assert comparison["contract_version"] == "pmbot_paper_update_before_after_comparison.v1"
    assert comparison["update_candidate_id"] == "paper-hypothesis-update-candidate-009"
    assert comparison["before_summary"] != comparison["after_summary"]
    assert comparison["outcome_status_still_unresolved"] is True
    assert comparison["no_real_trade_decision"] is True


def test_morning_card_exists_and_has_safe_next_actions() -> None:
    card = _load(MORNING_CARD_JSON)

    assert (ARTIFACT_DIR / "operator_morning_card_after_update_012.md").exists()
    assert card["paper_update_status"] == "paper_update_applied"
    assert card["changed_market_id"] == "563650"
    assert card["changed_hypothesis_id"] == "563650.analysis.adc53630aa1f.paper_hypothesis"
    assert len(card["next_3_safe_operator_actions"]) == 3


def test_source_learning_after_update_exists() -> None:
    learning = _load(SOURCE_LEARNING_JSON)

    assert (ARTIFACT_DIR / "source_learning_after_paper_update_012.md").exists()
    assert learning["source_usefulness_for_tracking"] == "useful_for_paper_tracking_update"
    assert learning["linked_evidence_packet_ids"]
    assert learning["linked_source_ids"]
    assert learning["linked_market_ids"] == ["563650"]
    assert learning["linked_update_candidate_ids"] == ["paper-hypothesis-update-candidate-009"]
    assert learning["requires_outcome_resolution_for_accuracy_judgement"] is True
    assert learning["no_autonomous_training_performed"] is True


def test_safety_scan_passes_and_confirms_no_unsafe_outputs(tmp_path: Path) -> None:
    safety = _load(SAFETY_SCAN_JSON)
    rerun = run_practical_safety_scan(
        artifact_dirs=[ARTIFACT_DIR],
        out_json_path=tmp_path / "scan.json",
        out_md_path=tmp_path / "scan.md",
    )

    assert safety["safety_ok"] is True
    assert safety["issue_count"] == 0
    assert safety["live_network_used"] is False
    assert safety["openrouter_calls_performed"] == 0
    assert safety["new_polymarket_api_calls_performed"] == 0
    assert safety["authenticated_endpoints_used"] is False
    assert safety["wallet_or_private_key_access"] is False
    assert safety["orders_or_trading_actions"] is False
    assert safety["market_recommendation_generated"] is False
    assert safety["probability_ev_edge_or_side_selection_generated"] is False
    assert safety["automatic_analysis_update_performed"] is False
    assert safety["operator_approved_update_applied"] is True
    assert safety["no_scheduler_daemon_background_worker"] is True
    assert safety["no_autonomous_trading"] is True
    assert rerun["safety_ok"] is True
