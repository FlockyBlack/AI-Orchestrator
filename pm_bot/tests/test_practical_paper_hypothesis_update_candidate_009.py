from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from pm_bot.practical.practical_safety_scan import run_practical_safety_scan

ARTIFACT_DIR = Path("pm_bot/practical/artifacts/public_evidence_review_009")
CANDIDATE_JSON = ARTIFACT_DIR / "paper_hypothesis_update_candidate_009.json"
CANDIDATE_MD = ARTIFACT_DIR / "paper_hypothesis_update_candidate_009.md"
ORIGINAL_HYPOTHESIS = Path("pm_bot/practical/artifacts/real_market_batch_004/markets/563650/paper_hypothesis.json")
FORBIDDEN_ACTION_WORDS = re.compile(r"\b(?:buy|sell|hold|enter|exit)\b", re.IGNORECASE)


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def test_paper_hypothesis_update_candidate_exists() -> None:
    candidate = _load(CANDIDATE_JSON)

    assert CANDIDATE_MD.exists()
    assert candidate["contract_version"] == "pmbot_paper_hypothesis_update_candidate.v1"
    assert candidate["update_candidate_id"]
    assert candidate["source_review_id"] == "public-evidence-review-009"


def test_original_hypothesis_is_not_overwritten() -> None:
    candidate = _load(CANDIDATE_JSON)
    original = _load(ORIGINAL_HYPOTHESIS)

    assert candidate["existing_paper_hypothesis_artifact_path"] == str(ORIGINAL_HYPOTHESIS).replace("\\", "/")
    assert candidate["original_hypothesis_changed"] is False
    assert candidate["update_applied"] is False
    assert original["contract_version"] == "pmbot_real_market_paper_hypothesis.v1"
    assert original["hypothesis_id"] == candidate["hypothesis_id"]


def test_paper_hypothesis_update_candidate_requires_operator_approval() -> None:
    candidate = _load(CANDIDATE_JSON)

    assert candidate["operator_approval_required"] is True
    assert candidate["update_applied"] is False
    assert candidate["no_real_trade_decision"] is True
    assert candidate["market_recommendation_generated"] is False
    assert candidate["probability_ev_edge_or_side_selection_generated"] is False
    assert candidate["orders_or_trading_actions"] is False
    assert candidate["wallet_or_private_key_access"] is False


def test_paper_hypothesis_update_candidate_has_no_trading_instruction_language() -> None:
    text = CANDIDATE_JSON.read_text(encoding="utf-8") + "\n" + CANDIDATE_MD.read_text(encoding="utf-8")
    scan = run_practical_safety_scan(artifact_paths=[CANDIDATE_JSON, CANDIDATE_MD])

    assert FORBIDDEN_ACTION_WORDS.search(text) is None
    assert scan["safety_ok"] is True
    assert scan["issue_count"] == 0
