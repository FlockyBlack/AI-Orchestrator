from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pm_bot.practical.practical_safety_scan import run_practical_safety_scan

ARTIFACT_DIR = Path("pm_bot/practical/artifacts/public_evidence_review_009")
PRACTICAL_008_RESULT = Path("docs/ORCH_PMBOT_PRACTICAL_008_RESULT.json")
REVIEW_JSON = ARTIFACT_DIR / "public_evidence_operator_review_009.json"
REVIEW_MD = ARTIFACT_DIR / "public_evidence_operator_review_009.md"


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _assert_safe_flags(value: Any) -> None:
    if isinstance(value, dict):
        for key, nested in value.items():
            if key in {
                "authenticated_endpoints_used",
                "market_recommendation_generated",
                "orders_or_trading_actions",
                "probability_ev_edge_or_side_selection_generated",
                "runtime_or_dispatcher_changes",
                "wallet_or_private_key_access",
            }:
                assert nested is False
            if key in {"openrouter_calls_performed", "polymarket_api_calls_performed"}:
                assert nested == 0
            _assert_safe_flags(nested)
    elif isinstance(value, list):
        for item in value:
            _assert_safe_flags(item)


def test_public_evidence_review_artifact_exists_and_reconciles_evidence_count() -> None:
    review = _load(REVIEW_JSON)
    practical_008 = _load(PRACTICAL_008_RESULT)

    assert REVIEW_MD.exists()
    assert review["contract_version"] == "pmbot_public_evidence_operator_review.v1"
    if practical_008["evidence_packets_created_count"] == 1:
        assert review["evidence_packet_count"] >= 1
    assert review["evidence_packets_reviewed"]


def test_public_evidence_review_includes_affected_market_and_hypothesis_fields() -> None:
    review = _load(REVIEW_JSON)

    assert review["affected_market_ids"]
    assert review["affected_hypothesis_ids"]
    assert review["normalized_evidence_summary"]
    assert review["evidence_relevance"] in {
        "supports_tracking_assumption",
        "weakens_tracking_assumption",
        "contradicts_tracking_assumption",
        "irrelevant",
        "insufficient",
        "unknown",
    }


def test_public_evidence_review_requires_operator_review_and_has_safe_flags() -> None:
    review = _load(REVIEW_JSON)

    assert review["operator_review_required"] is True
    assert review["no_real_trade_decision"] is True
    assert review["automatic_analysis_update_performed"] is False
    assert review["no_live_fetch_performed_in_this_task"] is True
    _assert_safe_flags(review)


def test_public_evidence_review_has_no_unsafe_actionable_output() -> None:
    scan = run_practical_safety_scan(artifact_paths=[REVIEW_JSON, REVIEW_MD])

    assert scan["safety_ok"] is True
    assert scan["issue_count"] == 0
