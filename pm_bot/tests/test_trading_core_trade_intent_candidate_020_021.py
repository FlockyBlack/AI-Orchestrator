from __future__ import annotations

from pm_bot.trading_core.trade_intent_candidate import build_paper_trade_intent_candidates

EXPECTED_MARKET_IDS = {"563650", "573656", "597964", "598936", "691547", "692258"}


def test_generates_one_paper_intent_per_tracked_market() -> None:
    batch = build_paper_trade_intent_candidates()

    assert batch["paper_intent_count"] == 6
    assert {row["market_id"] for row in batch["candidates"]} == EXPECTED_MARKET_IDS


def test_generated_intents_are_non_executable_paper_only() -> None:
    batch = build_paper_trade_intent_candidates()

    for candidate in batch["candidates"]:
        assert candidate["paper_only"] is True
        assert candidate["non_executable"] is True
        assert candidate["real_order_allowed"] is False
        assert candidate["wallet_required"] is False
        assert candidate["trading_endpoint_required"] is False
        assert candidate["operator_review_required"] is True
        assert candidate["no_real_trade_decision"] is True


def test_observe_only_when_saved_evidence_is_missing() -> None:
    batch = build_paper_trade_intent_candidates()
    observe_only = [row for row in batch["candidates"] if row["paper_action_type"] == "observe_only"]

    assert observe_only
    assert all("saved_public_evidence_packet_missing" in row["missing_evidence"] for row in observe_only)


def test_simulated_entry_requires_local_saved_evidence() -> None:
    batch = build_paper_trade_intent_candidates()
    simulated_entries = [row for row in batch["candidates"] if row["paper_action_type"] == "simulated_entry"]

    assert len(simulated_entries) == 2
    assert all(row["evidence_source_paths"] for row in simulated_entries)
