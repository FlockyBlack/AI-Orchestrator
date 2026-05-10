from __future__ import annotations

import json
from pathlib import Path

ARTIFACT_DIR = Path("pm_bot/practical/artifacts/public_evidence_dashboard_011")
SOURCE_BOARD_JSON = ARTIFACT_DIR / "merged_source_status_board_011.json"
SOURCE_BOARD_MD = ARTIFACT_DIR / "merged_source_status_board_011.md"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_source_status_board_includes_expected_categories() -> None:
    board = _load(SOURCE_BOARD_JSON)

    assert SOURCE_BOARD_MD.exists()
    assert board["contract_version"] == "pmbot_merged_source_status_board.v1"
    assert len(board["source_records"]) >= 5
    assert board["reachable_sources"]
    assert board["failed_sources"]
    assert board["repaired_sources"]


def test_source_status_board_tracks_specific_repair_outcomes() -> None:
    board = _load(SOURCE_BOARD_JSON)

    assert any(row["market_id"] == "691547" for row in board["repaired_sources"])
    assert any(row["latest_accessibility_status"] == "no_retry" for row in board["no_retry_sources"])
    assert any(row["latest_accessibility_status"] == "replacement_missing" for row in board["replacement_missing_sources"])
    assert any(row["latest_accessibility_status"] == "blocked" for row in board["blocked_sources"])


def test_source_status_board_safety_training_flag() -> None:
    board = _load(SOURCE_BOARD_JSON)

    assert board["no_autonomous_training_performed"] is True
    assert board["safety_summary"]["orders_or_trading_actions"] is False
