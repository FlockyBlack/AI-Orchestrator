from __future__ import annotations

import json
from pathlib import Path

from pm_bot.practical.practical_safety_scan import run_practical_safety_scan

ARTIFACT_DIR = Path("pm_bot/practical/artifacts/paper_update_application_012")
APPLIED_JSON = ARTIFACT_DIR / "applied_paper_update_012.json"
APPLIED_MD = ARTIFACT_DIR / "applied_paper_update_012.md"
CANDIDATE_JSON = Path("pm_bot/practical/artifacts/public_evidence_review_009/paper_hypothesis_update_candidate_009.json")


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_applied_update_exists_and_marks_update_applied() -> None:
    update = _load(APPLIED_JSON)

    assert APPLIED_MD.exists()
    assert update["contract_version"] == "pmbot_applied_paper_update.v1"
    assert update["update_candidate_id"] == "paper-hypothesis-update-candidate-009"
    assert update["update_applied"] is True
    assert update["operator_approval_required"] is True
    assert update["operator_approval_id"] == update["approval_id"]
    assert update["original_artifacts_preserved"] is True


def test_original_candidate_remains_unapplied() -> None:
    candidate = _load(CANDIDATE_JSON)

    assert candidate["update_candidate_id"] == "paper-hypothesis-update-candidate-009"
    assert candidate["update_applied"] is False
    assert candidate["original_hypothesis_changed"] is False


def test_original_hypothesis_file_was_not_overwritten() -> None:
    update = _load(APPLIED_JSON)
    hypothesis_path = Path(update["original_hypothesis_artifact_path"])
    hypothesis = _load(hypothesis_path)

    assert hypothesis["paper_hypothesis_summary"] == update["previous_paper_tracking_summary"]
    assert "applied_paper_tracking_summary" not in hypothesis
    assert "update_applied" not in hypothesis


def test_applied_update_has_safe_flags_and_no_unsafe_wording(tmp_path: Path) -> None:
    update = _load(APPLIED_JSON)
    scan = run_practical_safety_scan(
        artifact_paths=[APPLIED_JSON, APPLIED_MD],
        out_json_path=tmp_path / "scan.json",
        out_md_path=tmp_path / "scan.md",
    )

    assert update["no_real_trade_decision"] is True
    assert update["market_recommendation_generated"] is False
    assert update["probability_ev_edge_or_side_selection_generated"] is False
    assert update["orders_or_trading_actions"] is False
    assert update["wallet_or_private_key_access"] is False
    assert update["automatic_trading_allowed"] is False
    assert scan["safety_ok"] is True
