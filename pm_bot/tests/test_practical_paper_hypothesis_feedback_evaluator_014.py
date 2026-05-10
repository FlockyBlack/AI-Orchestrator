from __future__ import annotations

import json
import re
from pathlib import Path

from pm_bot.practical.paper_hypothesis_feedback_evaluator import build_paper_hypothesis_feedback

ARTIFACT_DIR = Path("pm_bot/practical/artifacts/manual_outcome_feedback_014")
FIXTURE_DIR = Path("pm_bot/tests/fixtures/manual_outcome_feedback")
UNSAFE_ACTION_RE = re.compile(r"\bshould\s+(buy|sell|hold|enter|exit)\b|\b(buy|sell|hold|enter|exit)\s+signal\b", re.I)
UNSAFE_SIGNAL_RE = re.compile(r"\b(probability|ev|edge|confidence)\b.{0,40}\b(signal|instruction)\b", re.I)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_unresolved_outcome_returns_pending_feedback() -> None:
    packet = _load(ARTIFACT_DIR / "markets/563650/manual_outcome_resolution_packet.unresolved.json")

    feedback = build_paper_hypothesis_feedback(manual_outcome_packet=packet)

    assert feedback["feedback_ready"] is False
    assert feedback["paper_hypothesis_result_label"] == "pending"
    assert feedback["analysis_quality_label"] == "pending"
    assert feedback["evidence_usefulness_label"] == "pending"


def test_resolved_aligned_fixture_returns_useful_feedback() -> None:
    packet = _load(FIXTURE_DIR / "manual_outcome_resolution_packet.resolved_aligned.fixture.json")

    feedback = build_paper_hypothesis_feedback(manual_outcome_packet=packet)

    assert feedback["feedback_ready"] is True
    assert feedback["paper_hypothesis_result_label"] == "aligned"
    assert feedback["analysis_quality_label"] == "useful"
    assert feedback["evidence_usefulness_label"] == "useful"


def test_resolved_missing_evidence_fixture_returns_missing_evidence_label() -> None:
    packet = _load(FIXTURE_DIR / "manual_outcome_resolution_packet.resolved_not_aligned_missing_evidence.fixture.json")

    feedback = build_paper_hypothesis_feedback(manual_outcome_packet=packet)

    assert feedback["feedback_ready"] is True
    assert feedback["paper_hypothesis_result_label"] == "not_aligned"
    assert feedback["analysis_quality_label"] == "wrong_due_to_missing_evidence"
    assert feedback["evidence_usefulness_label"] == "insufficient"


def test_ambiguous_fixture_returns_ambiguous_feedback() -> None:
    packet = _load(FIXTURE_DIR / "manual_outcome_resolution_packet.resolved_ambiguous.fixture.json")

    feedback = build_paper_hypothesis_feedback(manual_outcome_packet=packet)

    assert feedback["feedback_ready"] is True
    assert feedback["paper_hypothesis_result_label"] == "ambiguous"
    assert feedback["analysis_quality_label"] == "ambiguous"
    assert feedback["evidence_usefulness_label"] == "unknown"


def test_feedback_contains_no_trading_action_language() -> None:
    packet = _load(FIXTURE_DIR / "manual_outcome_resolution_packet.resolved_aligned.fixture.json")
    feedback = build_paper_hypothesis_feedback(manual_outcome_packet=packet)
    text = json.dumps(feedback, sort_keys=True)

    assert UNSAFE_ACTION_RE.search(text) is None
    assert feedback["safety_summary"]["market_recommendation_generated"] is False


def test_feedback_contains_no_quantitative_signal_language() -> None:
    packet = _load(FIXTURE_DIR / "manual_outcome_resolution_packet.resolved_not_aligned_missing_evidence.fixture.json")
    feedback = build_paper_hypothesis_feedback(manual_outcome_packet=packet)
    text = json.dumps(feedback, sort_keys=True)

    assert UNSAFE_SIGNAL_RE.search(text) is None
    assert feedback["safety_summary"]["probability_ev_edge_or_side_selection_generated"] is False
