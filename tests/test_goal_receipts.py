from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GOAL_DIR = ROOT / "docs" / "goals" / "pmbot-paper-mvp"


def test_goal_board_files_exist() -> None:
    for path in [
        GOAL_DIR / "goal.md",
        GOAL_DIR / "state.yaml",
        GOAL_DIR / "README.md",
        GOAL_DIR / "receipts" / "README.md",
        GOAL_DIR / "receipts" / "receipt_template.json",
    ]:
        assert path.exists()


def test_receipt_template_contains_required_fields() -> None:
    payload = json.loads((GOAL_DIR / "receipts" / "receipt_template.json").read_text(encoding="utf-8"))
    for field in [
        "task_id",
        "status",
        "head_before",
        "head_after",
        "files_changed",
        "tests_run",
        "artifacts",
        "safety",
        "blockers",
        "next_recommended_task",
    ]:
        assert field in payload
    assert payload["safety"]["paper_only"] is True
