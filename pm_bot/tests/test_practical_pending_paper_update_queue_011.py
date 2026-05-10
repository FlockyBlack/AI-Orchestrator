from __future__ import annotations

import json
from pathlib import Path

ARTIFACT_DIR = Path("pm_bot/practical/artifacts/public_evidence_dashboard_011")
QUEUE_JSON = ARTIFACT_DIR / "pending_paper_update_queue_011.json"
QUEUE_MD = ARTIFACT_DIR / "pending_paper_update_queue_011.md"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_pending_paper_update_queue_exists_and_includes_unapplied_candidate() -> None:
    queue = _load(QUEUE_JSON)

    assert QUEUE_MD.exists()
    assert queue["contract_version"] == "pmbot_pending_paper_update_queue.v1"
    assert queue["pending_update_count"] >= 1
    assert any(row["update_candidate_id"] == "paper-hypothesis-update-candidate-009" for row in queue["pending_updates"])
    assert all(row["update_applied"] is False for row in queue["pending_updates"])


def test_pending_queue_requires_operator_review_and_no_automatic_update() -> None:
    queue = _load(QUEUE_JSON)

    assert queue["operator_review_required_count"] == queue["pending_update_count"]
    assert queue["automatic_update_performed"] is False
    assert queue["next_operator_actions"]
