from __future__ import annotations

from pathlib import Path

from pm_bot.practical.analysis_quality_summary import run_analysis_quality_summary

FEEDBACK_DIR = Path("pm_bot/practical/artifacts/night_002/feedback_batch")


def test_quality_summary_aggregates_labels(tmp_path: Path) -> None:
    summary = run_analysis_quality_summary(
        feedback_dir=FEEDBACK_DIR,
        out_json_path=tmp_path / "quality.json",
        out_md_path=tmp_path / "quality.md",
    )

    assert summary["total_feedback_items"] == 6
    assert summary["useful_count"] >= 1
    assert summary["wrong_due_to_missing_evidence_count"] == 1
    assert summary["wrong_due_to_bad_reasoning_count"] == 1
    assert summary["unresolved_count"] == 1


def test_recurring_lessons_appear(tmp_path: Path) -> None:
    summary = run_analysis_quality_summary(
        feedback_dir=FEEDBACK_DIR,
        out_json_path=tmp_path / "quality.json",
        out_md_path=tmp_path / "quality.md",
    )

    assert summary["recurring_missing_evidence"]
    assert summary["recurring_reasoning_lessons"]
    assert summary["next_prompt_improvements"]
