from __future__ import annotations

import json
from pathlib import Path

ARTIFACT_DIR = Path("pm_bot/practical/artifacts/paper_update_application_012")
SNAPSHOT_JSON = ARTIFACT_DIR / "paper_tracking_state_snapshot_012.json"
SNAPSHOT_MD = ARTIFACT_DIR / "paper_tracking_state_snapshot_012.md"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_snapshot_exists_and_validates() -> None:
    snapshot = _load(SNAPSHOT_JSON)

    assert SNAPSHOT_MD.exists()
    assert snapshot["contract_version"] == "pmbot_paper_tracking_state_snapshot.v1"
    assert snapshot["snapshot_id"] == "paper-tracking-state-snapshot-012"
    assert snapshot["source_dashboard_id"] == "public-evidence-tracking-dashboard-011"


def test_applied_update_appears_in_snapshot() -> None:
    snapshot = _load(SNAPSHOT_JSON)

    assert snapshot["applied_update_ids"] == ["applied-paper-update-012-paper-hypothesis-update-candidate-009"]
    target = [
        row
        for row in snapshot["active_paper_hypotheses"]
        if row["hypothesis_id"] == "563650.analysis.adc53630aa1f.paper_hypothesis"
    ][0]
    assert target["update_applied_in_snapshot"] is True
    assert target["applied_paper_update_ids"] == snapshot["applied_update_ids"]
    assert target["paper_tracking_summary_after"] != target["paper_tracking_summary_before"]


def test_unresolved_outcomes_remain_unresolved() -> None:
    snapshot = _load(SNAPSHOT_JSON)

    assert len(snapshot["unresolved_outcomes"]) == 5
    assert all(row["outcome_status"] == "unresolved" for row in snapshot["unresolved_outcomes"])
    assert all(row["outcome_status"] == "unresolved" for row in snapshot["active_paper_hypotheses"])


def test_pending_updates_remaining_count_is_correct() -> None:
    snapshot = _load(SNAPSHOT_JSON)

    assert snapshot["pending_paper_updates_remaining_count"] == 0
    assert snapshot["pending_paper_updates_remaining"] == []
    assert snapshot["operator_next_actions"]
