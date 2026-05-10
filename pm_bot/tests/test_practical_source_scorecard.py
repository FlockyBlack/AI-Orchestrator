from __future__ import annotations

import json
from pathlib import Path

from pm_bot.practical.source_scorecard import run_source_scorecard

LEDGER_PATH = Path("pm_bot/practical/artifacts/night_002/source_learning_batch_5.result.json")


def test_source_scorecard_counts_usefulness_labels(tmp_path: Path) -> None:
    scorecard = run_source_scorecard(
        ledger_path=str(LEDGER_PATH),
        out_json_path=str(tmp_path / "scorecard.json"),
        out_md_path=str(tmp_path / "scorecard.md"),
    )

    rows = {row["source_id"]: row for row in scorecard["source_scorecard"]}
    assert rows["crypto_archived_reference"]["stale_count"] == 1
    assert rows["esports_roster_note"]["misleading_count"] == 1
    assert rows["politics_committee_note_a"]["contradictory_count"] == 1


def test_source_scorecard_markdown_written(tmp_path: Path) -> None:
    run_source_scorecard(
        ledger_path=str(LEDGER_PATH),
        out_json_path=str(tmp_path / "scorecard.json"),
        out_md_path=str(tmp_path / "scorecard.md"),
    )

    assert "# PMBOT Source Scorecard" in (tmp_path / "scorecard.md").read_text(encoding="utf-8")
    assert json.loads((tmp_path / "scorecard.json").read_text(encoding="utf-8"))["source_count"] >= 5
