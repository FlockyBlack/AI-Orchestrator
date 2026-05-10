from __future__ import annotations

import json
from pathlib import Path

from pm_bot.practical.source_learning_batch import run_source_learning_batch

NIGHT_DIR = Path("pm_bot/practical/artifacts/night_002")
BATCH_SUMMARY_PATH = NIGHT_DIR / "batch_paper_feedback_5.summary.json"


def test_source_learning_aggregates_multiple_feedback_files(tmp_path: Path) -> None:
    batch = json.loads(BATCH_SUMMARY_PATH.read_text(encoding="utf-8"))
    feedback_paths = [row["feedback_result_path"] for row in batch["generated_feedback"]]

    ledger = run_source_learning_batch(
        feedback_paths=feedback_paths,
        out_json_path=tmp_path / "ledger.json",
        out_md_path=tmp_path / "ledger.md",
    )

    assert ledger["source_usefulness_summary"]["useful"] >= 1
    assert ledger["source_usefulness_summary"]["stale"] == 1
    assert ledger["no_autonomous_training_performed"] is True


def test_stale_misleading_contradictory_labels_appear() -> None:
    ledger = json.loads((NIGHT_DIR / "source_learning_batch_5.result.json").read_text(encoding="utf-8"))
    labels = set(ledger["source_usefulness_summary"])

    assert {"stale", "misleading", "contradictory", "insufficient"}.issubset(labels)
