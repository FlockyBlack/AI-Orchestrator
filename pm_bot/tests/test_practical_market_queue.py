from __future__ import annotations

import json
from pathlib import Path

from pm_bot.practical.market_queue import load_market_queue, render_market_queue_markdown, write_market_queue_summary

FIXTURE_DIR = Path("pm_bot/tests/fixtures/practical_market_queue_batch")
QUEUE_PATH = FIXTURE_DIR / "market_queue_5.valid.json"
MISSING_QUEUE_PATH = FIXTURE_DIR / "market_queue_missing_artifact.valid.json"


def test_valid_queue_loads() -> None:
    queue = load_market_queue(QUEUE_PATH)

    assert queue["contract_version"] == "pmbot_market_queue.v1"
    assert len(queue["items"]) == 6


def test_status_counts_are_correct() -> None:
    summary = write_market_queue_summary(queue_path=QUEUE_PATH)

    assert summary["status_counts"] == {
        "analysis_ready": 1,
        "blocked": 1,
        "feedback_complete": 1,
        "hypothesis_active": 1,
        "outcome_pending": 1,
        "queued": 1,
    }


def test_missing_artifacts_become_blockers() -> None:
    summary = write_market_queue_summary(queue_path=MISSING_QUEUE_PATH)

    assert summary["blocked_items"]
    assert summary["missing_linked_artifacts"][0]["field"] == "analysis_result_path"
    assert "Resolve the local blockers" in summary["blocked_items"][0]["next_operator_action"]


def test_next_operator_actions_are_generated() -> None:
    summary = write_market_queue_summary(queue_path=QUEUE_PATH)

    actions = {row["queue_item_id"]: row["next_operator_action"] for row in summary["next_operator_actions"]}
    assert "finite local analysis" in actions["queue-weather-001"]
    assert "source learning ledger" in actions["queue-generic-001"]


def test_markdown_summary_is_written(tmp_path: Path) -> None:
    out_json = tmp_path / "queue.json"
    out_md = tmp_path / "queue.md"

    summary = write_market_queue_summary(queue_path=QUEUE_PATH, out_json_path=out_json, out_md_path=out_md)

    assert json.loads(out_json.read_text(encoding="utf-8")) == summary
    markdown = out_md.read_text(encoding="utf-8")
    assert "# PMBOT Market Queue Summary" in markdown
    assert "Queue items: 6" in markdown
    assert render_market_queue_markdown(summary) == markdown


def test_no_safety_flags_are_unsafe() -> None:
    summary = write_market_queue_summary(queue_path=QUEUE_PATH)

    assert summary["safety_summary"]["live_network_used"] is False
    assert summary["safety_summary"]["orders_or_trading_actions"] is False
    assert summary["safety_summary"]["wallet_or_private_key_access"] is False
    for item in summary["items"]:
        assert item["safety_flags"]["no_real_trade_decision"] is True
