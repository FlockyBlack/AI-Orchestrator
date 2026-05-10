from __future__ import annotations

import json
from pathlib import Path

from pm_bot.practical.outcome_check_queue import build_outcome_check_queue, write_outcome_check_queue

QUEUE_PATH = Path("pm_bot/tests/fixtures/practical_market_queue_batch/market_queue_5.valid.json")


def test_outcome_check_queue_detects_pending_resolved_unknown() -> None:
    summary = build_outcome_check_queue(QUEUE_PATH)
    statuses = {row["outcome_check_status"] for row in summary["outcome_checks"]}

    assert {"not_due", "overdue", "resolved", "unknown"}.issubset(statuses)


def test_outcome_check_cli_writes_json_and_markdown(tmp_path: Path) -> None:
    out_json = tmp_path / "outcome.json"
    out_md = tmp_path / "outcome.md"

    summary = write_outcome_check_queue(queue_path=QUEUE_PATH, out_json_path=out_json, out_md_path=out_md)

    assert json.loads(out_json.read_text(encoding="utf-8")) == summary
    assert "# PMBOT Outcome Check Queue" in out_md.read_text(encoding="utf-8")
