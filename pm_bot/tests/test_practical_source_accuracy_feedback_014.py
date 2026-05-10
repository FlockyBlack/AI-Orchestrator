from __future__ import annotations

import json
from pathlib import Path

from pm_bot.practical.paper_hypothesis_feedback_evaluator import build_paper_hypothesis_feedback
from pm_bot.practical.source_accuracy_feedback import build_source_accuracy_feedback

ARTIFACT_DIR = Path("pm_bot/practical/artifacts/manual_outcome_feedback_014")
FIXTURE_DIR = Path("pm_bot/tests/fixtures/manual_outcome_feedback")


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_unresolved_outcome_keeps_source_accuracy_pending() -> None:
    source_feedback = _load(ARTIFACT_DIR / "markets/563650/source_accuracy_feedback.pending.json")

    assert source_feedback["outcome_status"] == "unresolved"
    assert source_feedback["source_accuracy_labels"]
    assert set(source_feedback["source_accuracy_labels"].values()) == {"pending"}
    assert all(row["source_accuracy_label"] == "pending" for row in source_feedback["source_records"])


def test_resolved_fixture_can_produce_source_feedback_labels() -> None:
    packet = _load(FIXTURE_DIR / "manual_outcome_resolution_packet.resolved_aligned.fixture.json")
    paper_feedback = build_paper_hypothesis_feedback(manual_outcome_packet=packet)

    source_feedback = build_source_accuracy_feedback(
        paper_hypothesis_feedback=paper_feedback,
        manual_outcome_packet=packet,
    )

    assert source_feedback["source_accuracy_labels"]
    assert set(source_feedback["source_accuracy_labels"].values()) == {"useful"}


def test_source_feedback_keeps_no_autonomous_training_flag_true() -> None:
    source_feedback = _load(ARTIFACT_DIR / "markets/597964/source_accuracy_feedback.pending.json")

    assert source_feedback["no_autonomous_training_performed"] is True
    assert source_feedback["safety_summary"]["no_autonomous_training_performed"] is True


def test_source_feedback_keeps_no_real_trade_decision_true() -> None:
    source_feedback = _load(ARTIFACT_DIR / "markets/598936/source_accuracy_feedback.pending.json")

    assert source_feedback["no_real_trade_decision"] is True
    assert source_feedback["safety_summary"]["no_real_trade_decision"] is True


def test_source_lessons_fields_exist() -> None:
    source_feedback = _load(ARTIFACT_DIR / "markets/691547/source_accuracy_feedback.pending.json")

    assert "source_lessons" in source_feedback
    assert "recommended_future_source_handling" in source_feedback
    assert isinstance(source_feedback["source_lessons"], list)
    assert isinstance(source_feedback["recommended_future_source_handling"], list)
