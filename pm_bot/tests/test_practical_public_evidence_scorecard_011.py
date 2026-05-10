from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

ARTIFACT_DIR = Path("pm_bot/practical/artifacts/public_evidence_dashboard_011")
SCORECARD_JSON = ARTIFACT_DIR / "public_evidence_scorecard_011.json"
SCORECARD_MD = ARTIFACT_DIR / "public_evidence_scorecard_011.md"
UNSAFE_VALUE_PATTERN = re.compile(r"\b(?:trading edge|predictive confidence|side selection signal|market action)\b", re.IGNORECASE)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _string_values(value: Any) -> list[str]:
    if isinstance(value, dict):
        values: list[str] = []
        for nested in value.values():
            values.extend(_string_values(nested))
        return values
    if isinstance(value, list):
        values = []
        for nested in value:
            values.extend(_string_values(nested))
        return values
    if isinstance(value, str):
        return [value]
    return []


def test_scorecard_counts_attempts_successes_failures_and_packets() -> None:
    scorecard = _load(SCORECARD_JSON)

    assert SCORECARD_MD.exists()
    assert scorecard["contract_version"] == "pmbot_public_evidence_scorecard.v1"
    assert scorecard["total_fetch_attempts"] == 6
    assert scorecard["total_fetch_successes"] == 2
    assert scorecard["total_fetch_failures"] == 4
    assert scorecard["total_fetch_blocked"] == 1
    assert scorecard["evidence_packet_count"] == 2


def test_scorecard_summarizes_collection_quality_only() -> None:
    scorecard = _load(SCORECARD_JSON)

    assert scorecard["accessibility_success_rate_label"] in {"high", "medium", "low", "insufficient"}
    assert scorecard["automatic_update_count"] == 0
    assert all(UNSAFE_VALUE_PATTERN.search(value) is None for value in _string_values(scorecard))
