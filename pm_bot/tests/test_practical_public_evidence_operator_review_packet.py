from __future__ import annotations

import json
from pathlib import Path

from pm_bot.practical.practical_safety_scan import run_practical_safety_scan

ARTIFACT_DIR = Path("pm_bot/practical/artifacts/public_read_only_fetch_execution_008")
REVIEW_JSON = ARTIFACT_DIR / "public_evidence_operator_review_packet_008.json"
REVIEW_MD = ARTIFACT_DIR / "public_evidence_operator_review_packet_008.md"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_review_packet_exists_and_includes_request_summary() -> None:
    review = _load(REVIEW_JSON)

    assert REVIEW_MD.exists()
    assert review["contract_version"] == "pmbot_public_evidence_operator_review_packet.v1"
    assert review["request_summary"]["attempted"] >= 0
    assert review["request_summary"]["succeeded"] >= 0
    assert review["request_summary"]["failed"] >= 0
    assert review["request_summary"]["blocked"] >= 0
    assert review["fetched_sources"]
    assert review["fetched_markets"]


def test_review_packet_includes_evidence_paths_or_no_evidence_explanation() -> None:
    review = _load(REVIEW_JSON)

    if review["saved_evidence_packet_paths"]:
        for path in review["saved_evidence_packet_paths"]:
            assert Path(path).exists()
    else:
        assert review["no_evidence_explanation"]


def test_review_packet_includes_replay_status_and_operator_checklist() -> None:
    review = _load(REVIEW_JSON)

    assert review["replay_status"] in {
        "replayed_saved_public_evidence",
        "blocked_no_saved_evidence",
    }
    assert review["replay_artifact_paths"]
    assert review["operator_review_checklist"]
    assert any("approved manifest request intent" in item for item in review["operator_review_checklist"])
    assert review["no_real_trade_decision"] is True


def test_review_packet_has_no_actionable_trading_language() -> None:
    scan = run_practical_safety_scan(artifact_paths=[REVIEW_JSON, REVIEW_MD])

    assert scan["safety_ok"] is True
    assert scan["issue_count"] == 0
