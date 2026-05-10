from __future__ import annotations

import json
from pathlib import Path

from pm_bot.practical.public_fetch_operator_approval import validate_operator_approval

FIXTURE = Path("pm_bot/tests/fixtures/public_read_only_fetch_prep/operator_approval_pending.valid.json")


def test_pending_approval_record_validates() -> None:
    record = json.loads(FIXTURE.read_text(encoding="utf-8"))

    validation = validate_operator_approval(record)

    assert validation["valid"] is True
    assert record["operator_approval_required"] is True
    assert record["operator_approval_granted"] is False
    assert record["approved_by"] is None
    assert record["approved_at"] is None
    assert record["live_fetch_enabled_after_approval"] is False
