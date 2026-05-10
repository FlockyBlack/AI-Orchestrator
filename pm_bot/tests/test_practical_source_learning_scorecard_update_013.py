from __future__ import annotations

import json
from pathlib import Path

ARTIFACT_DIR = Path("pm_bot/practical/artifacts/outcome_recheck_source_learning_013")
SCORECARD_JSON = ARTIFACT_DIR / "source_learning_scorecard_update_013.json"
SCORECARD_MD = ARTIFACT_DIR / "source_learning_scorecard_update_013.md"
SOURCE_LEARNING_012_JSON = Path("pm_bot/practical/artifacts/paper_update_application_012/source_learning_after_paper_update_012.json")


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_scorecard_update_exists() -> None:
    scorecard = _load(SCORECARD_JSON)

    assert SCORECARD_MD.exists()
    assert scorecard["contract_version"] == "pmbot_source_learning_scorecard_update.v1"
    assert scorecard["scorecard_update_id"] == "source-learning-scorecard-update-013"


def test_scorecard_update_includes_source_records() -> None:
    scorecard = _load(SCORECARD_JSON)

    assert len(scorecard["source_records"]) >= 5
    assert {row["market_id"] for row in scorecard["source_records"]} >= {
        "563650",
        "597964",
        "598936",
        "691547",
        "692258",
    }


def test_scorecard_marks_useful_for_paper_tracking_when_supported_by_practical_012() -> None:
    scorecard = _load(SCORECARD_JSON)
    learning_012 = _load(SOURCE_LEARNING_012_JSON)

    if learning_012["source_usefulness_for_tracking"] == "useful_for_paper_tracking_update":
        labels = {row["source_usefulness_label"] for row in scorecard["source_records"]}
        assert "useful_for_paper_tracking_update" in labels
        assert scorecard["sources_useful_for_paper_tracking"]


def test_scorecard_distinguishes_pending_outcome_resolution_from_prediction_accuracy() -> None:
    scorecard = _load(SCORECARD_JSON)

    assert scorecard["scorecard_context"]["requires_outcome_resolution_for_accuracy_judgement"] is True
    assert scorecard["sources_pending_outcome_resolution"]
    assert all(row["outcome_validated"] is False for row in scorecard["source_records"])
    assert all("not a prediction accuracy judgement" in row["usefulness_limit"] for row in scorecard["source_records"])


def test_scorecard_keeps_learning_non_autonomous_and_non_trade() -> None:
    scorecard = _load(SCORECARD_JSON)

    assert scorecard["no_autonomous_training_performed"] is True
    assert scorecard["no_real_trade_decision"] is True
    assert scorecard["safety_summary"]["market_recommendation_generated"] is False
    assert scorecard["safety_summary"]["probability_ev_edge_or_side_selection_generated"] is False
