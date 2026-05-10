from __future__ import annotations

import json
from pathlib import Path

from pm_bot.practical.operator_console import build_operator_console, write_operator_console

QUEUE_PATH = Path("pm_bot/tests/fixtures/practical_market_queue_batch/market_queue_5.valid.json")


def test_console_json_generated() -> None:
    console = build_operator_console(QUEUE_PATH)

    assert console["contract_version"] == "pmbot_practical_operator_console.v1"
    assert console["queue_status_counts"]["queued"] == 1


def test_console_markdown_generated(tmp_path: Path) -> None:
    out_json = tmp_path / "console.json"
    out_md = tmp_path / "console.md"

    console = write_operator_console(queue_path=QUEUE_PATH, out_json_path=out_json, out_md_path=out_md)

    assert json.loads(out_json.read_text(encoding="utf-8")) == console
    markdown = out_md.read_text(encoding="utf-8")
    assert "# PMBOT Practical Operator Console" in markdown
    assert "## Queue summary" in markdown


def test_console_surfaces_required_sections() -> None:
    console = build_operator_console(QUEUE_PATH)

    assert console["active_paper_hypotheses_count"] >= 4
    assert "source_usefulness_summary" in console["source_learning_summary"]
    assert console["next_operator_actions"]
    assert console["blocked_items"]
