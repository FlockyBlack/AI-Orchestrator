from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_STALE_SECONDS = 6 * 60 * 60


@dataclass
class ExecutionLock:
    queue_root: str | Path
    plan_id: str
    run_id: str
    repo_root: str | Path = "."
    stale_after_seconds: int = DEFAULT_STALE_SECONDS
    lock_path: str | Path | None = None

    def resolved_lock_path(self) -> Path:
        if self.lock_path:
            return Path(self.lock_path)
        return Path(self.queue_root) / "generated" / self.plan_id / self.run_id / "run.lock"

    def acquire(self) -> dict[str, Any]:
        return acquire_lock(self)

    def release(self) -> dict[str, Any]:
        return release_lock(self)

    def inspect(self) -> dict[str, Any]:
        return inspect_lock(self)


def acquire_lock(lock: ExecutionLock) -> dict[str, Any]:
    path = lock.resolved_lock_path()
    inspection = inspect_lock(lock)
    if inspection["exists"]:
        return {
            "acquired": False,
            "status": "locked_stale" if inspection["stale"] else "locked",
            "lock_path": str(path),
            "metadata": inspection["metadata"],
            "stale": inspection["stale"],
            "errors": ["lock already exists for this run_id"],
        }
    metadata = _metadata(lock, created_at=_utc_iso())
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("x", encoding="utf-8") as handle:
            json.dump(metadata, handle, indent=2, sort_keys=True)
            handle.write("\n")
    except FileExistsError:
        return acquire_lock(lock)
    return {
        "acquired": True,
        "status": "acquired",
        "lock_path": str(path),
        "metadata": metadata,
        "stale": False,
        "errors": [],
    }


def release_lock(lock: ExecutionLock) -> dict[str, Any]:
    path = lock.resolved_lock_path()
    if not path.exists():
        return {"released": False, "status": "missing", "lock_path": str(path), "errors": []}
    metadata = _read_metadata(path)
    current_pid = os.getpid()
    if metadata.get("pid") not in {current_pid, str(current_pid)}:
        return {
            "released": False,
            "status": "pid_mismatch",
            "lock_path": str(path),
            "metadata": metadata,
            "errors": ["lock pid does not match current process"],
        }
    path.unlink()
    return {
        "released": True,
        "status": "released",
        "lock_path": str(path),
        "metadata": metadata,
        "errors": [],
    }


def inspect_lock(lock: ExecutionLock) -> dict[str, Any]:
    path = lock.resolved_lock_path()
    if not path.exists():
        return {
            "exists": False,
            "stale": False,
            "lock_path": str(path),
            "metadata": {},
            "errors": [],
        }
    metadata = _read_metadata(path)
    stale = _is_stale(metadata, lock.stale_after_seconds)
    return {
        "exists": True,
        "stale": stale,
        "lock_path": str(path),
        "metadata": metadata,
        "errors": [] if metadata else ["lock metadata could not be read"],
    }


def _metadata(lock: ExecutionLock, *, created_at: str) -> dict[str, Any]:
    return {
        "run_id": lock.run_id,
        "plan_id": lock.plan_id,
        "pid": os.getpid(),
        "created_at": created_at,
        "updated_at": created_at,
        "repo_root": str(lock.repo_root),
        "lock_path": str(lock.resolved_lock_path()),
    }


def _read_metadata(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _is_stale(metadata: dict[str, Any], stale_after_seconds: int) -> bool:
    timestamp = str(metadata.get("updated_at") or metadata.get("created_at") or "")
    try:
        if timestamp.endswith("Z"):
            timestamp = timestamp[:-1] + "+00:00"
        dt = datetime.fromisoformat(timestamp)
    except ValueError:
        return True
    age = datetime.now(timezone.utc) - dt.astimezone(timezone.utc)
    return age.total_seconds() > stale_after_seconds


def _utc_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
