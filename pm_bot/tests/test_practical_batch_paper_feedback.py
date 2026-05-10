from __future__ import annotations

from pathlib import Path

from pm_bot.practical.batch_paper_feedback import run_batch_paper_feedback

QUEUE_PATH = Path("pm_bot/tests/fixtures/practical_market_queue_batch/market_queue_feedback_ready.valid.json")


def test_batch_paper_feedback_generates_feedback_for_eligible_items(tmp_path: Path) -> None:
    summary = run_batch_paper_feedback(
        queue_path=QUEUE_PATH,
        out_dir=tmp_path / "feedback",
        out_summary_json_path=tmp_path / "summary.json",
        out_summary_md_path=tmp_path / "summary.md",
    )

    assert summary["generated_count"] == 6
    assert summary["skipped_count"] == 0


def test_unresolved_outcome_stays_unresolved(tmp_path: Path) -> None:
    summary = run_batch_paper_feedback(
        queue_path=QUEUE_PATH,
        out_dir=tmp_path / "feedback",
        out_summary_json_path=tmp_path / "summary.json",
        out_summary_md_path=tmp_path / "summary.md",
    )

    assert any(row["analysis_quality_label"] == "unresolved" for row in summary["generated_feedback"])


def test_resolved_outcomes_label_useful_and_incomplete_cases(tmp_path: Path) -> None:
    summary = run_batch_paper_feedback(
        queue_path=QUEUE_PATH,
        out_dir=tmp_path / "feedback",
        out_summary_json_path=tmp_path / "summary.json",
        out_summary_md_path=tmp_path / "summary.md",
    )
    labels = {row["analysis_quality_label"] for row in summary["generated_feedback"]}

    assert "useful" in labels
    assert "wrong_due_to_missing_evidence" in labels
    assert "wrong_due_to_bad_reasoning" in labels


def test_no_trading_output_appears(tmp_path: Path) -> None:
    run_batch_paper_feedback(
        queue_path=QUEUE_PATH,
        out_dir=tmp_path / "feedback",
        out_summary_json_path=tmp_path / "summary.json",
        out_summary_md_path=tmp_path / "summary.md",
    )

    text = (tmp_path / "summary.md").read_text(encoding="utf-8").lower()
    assert "should buy" not in text
    assert "should sell" not in text
    assert "wallet/private-key access" not in text
