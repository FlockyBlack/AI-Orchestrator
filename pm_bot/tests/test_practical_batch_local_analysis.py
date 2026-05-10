from __future__ import annotations

import json
from pathlib import Path

from pm_bot.practical.batch_local_analysis import run_batch_local_analysis

QUEUE_PATH = Path("pm_bot/tests/fixtures/practical_market_queue_batch/market_queue_5.valid.json")


def test_batch_analysis_processes_finite_queue_and_exits(tmp_path: Path) -> None:
    summary = run_batch_local_analysis(
        queue_path=QUEUE_PATH,
        out_dir=tmp_path / "analysis",
        out_summary_json_path=tmp_path / "summary.json",
        out_summary_md_path=tmp_path / "summary.md",
    )

    assert summary["processed_count"] == 1
    assert summary["skipped_count"] == 5
    assert Path(summary["processed_items"][0]["analysis_result_path"]).exists()


def test_original_queue_not_mutated_without_output_queue(tmp_path: Path) -> None:
    before = QUEUE_PATH.read_text(encoding="utf-8")

    run_batch_local_analysis(
        queue_path=QUEUE_PATH,
        out_dir=tmp_path / "analysis",
        out_summary_json_path=tmp_path / "summary.json",
        out_summary_md_path=tmp_path / "summary.md",
    )

    assert QUEUE_PATH.read_text(encoding="utf-8") == before


def test_batch_summary_is_generated_and_optional_queue_written(tmp_path: Path) -> None:
    out_queue = tmp_path / "updated_queue.json"
    summary = run_batch_local_analysis(
        queue_path=QUEUE_PATH,
        out_dir=tmp_path / "analysis",
        out_summary_json_path=tmp_path / "summary.json",
        out_summary_md_path=tmp_path / "summary.md",
        out_queue_path=out_queue,
    )

    assert json.loads((tmp_path / "summary.json").read_text(encoding="utf-8")) == summary
    updated = json.loads(out_queue.read_text(encoding="utf-8"))
    assert updated["items"][0]["status"] == "analysis_ready"
