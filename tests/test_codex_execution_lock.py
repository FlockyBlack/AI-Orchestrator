from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from ai_orchestrator.codex_queue.execution_lock import ExecutionLock, acquire_lock, inspect_lock, release_lock


def test_lock_prevents_second_run(tmp_path: Path) -> None:
    lock = ExecutionLock(tmp_path, "plan", "run")

    first = acquire_lock(lock)
    second = acquire_lock(lock)

    assert first["acquired"] is True
    assert second["acquired"] is False
    assert second["status"] == "locked"
    assert release_lock(lock)["released"] is True


def test_stale_lock_detected_but_not_removed(tmp_path: Path) -> None:
    lock = ExecutionLock(tmp_path, "plan", "run", stale_after_seconds=1)
    path = lock.resolved_lock_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    old = (datetime.now(timezone.utc) - timedelta(hours=1)).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    path.write_text(json.dumps({"updated_at": old, "pid": 999999}), encoding="utf-8")

    inspection = inspect_lock(lock)

    assert inspection["exists"] is True
    assert inspection["stale"] is True
    assert path.exists()
