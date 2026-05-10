from __future__ import annotations

import json
from pathlib import Path

from pm_bot.practical.active_paper_hypotheses import build_active_paper_hypotheses, write_active_paper_hypotheses

FIXTURE_DIR = Path("pm_bot/tests/fixtures/practical_market_queue_batch")
QUEUE_PATH = FIXTURE_DIR / "market_queue_5.valid.json"
FEEDBACK_READY_QUEUE_PATH = FIXTURE_DIR / "market_queue_feedback_ready.valid.json"


def test_active_hypothesis_extracted_from_analysis_result() -> None:
    summary = build_active_paper_hypotheses(QUEUE_PATH)

    assert summary["contract_version"] == "pmbot_active_paper_hypotheses.v1"
    assert any(row["market_id"] == "synthetic-politics-measure-001" for row in summary["active_hypotheses"])


def test_unresolved_outcome_is_shown() -> None:
    summary = build_active_paper_hypotheses(QUEUE_PATH)
    esports = next(row for row in summary["active_hypotheses"] if row["market_id"] == "synthetic-esports-match-001")

    assert esports["outcome_status"] == "unresolved"
    assert esports["outcome_due_status"] == "overdue"


def test_feedback_pending_is_shown() -> None:
    summary = build_active_paper_hypotheses(FEEDBACK_READY_QUEUE_PATH)

    assert summary["feedback_pending_count"] >= 5
    assert any(row["feedback_status"] == "feedback_pending" for row in summary["active_hypotheses"])


def test_safety_label_preserved_and_no_real_trade_decision_present() -> None:
    summary = build_active_paper_hypotheses(QUEUE_PATH)

    for row in summary["active_hypotheses"]:
        assert row["safety_label"] == "paper_only_non_executable_analysis_tracking"
        assert row["no_real_trade_decision"] is True


def test_cli_writes_active_hypotheses_artifacts(tmp_path: Path) -> None:
    out_json = tmp_path / "active.json"
    out_md = tmp_path / "active.md"

    result = write_active_paper_hypotheses(queue_path=QUEUE_PATH, out_json_path=out_json, out_md_path=out_md)

    assert json.loads(out_json.read_text(encoding="utf-8")) == result
    assert "# PMBOT Active Paper Hypotheses" in out_md.read_text(encoding="utf-8")
