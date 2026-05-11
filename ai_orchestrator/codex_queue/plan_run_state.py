from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping


@dataclass
class TaskRunState:
    task_id: str
    status: str = "pending"
    started_at: str = ""
    finished_at: str = ""
    attempts: int = 0
    result_path: str = ""
    artifact_paths: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "TaskRunState":
        return cls(
            task_id=str(payload.get("task_id") or ""),
            status=str(payload.get("status") or "pending"),
            started_at=str(payload.get("started_at") or ""),
            finished_at=str(payload.get("finished_at") or ""),
            attempts=int(payload.get("attempts", 0) or 0),
            result_path=str(payload.get("result_path") or ""),
            artifact_paths=[str(value) for value in payload.get("artifact_paths", [])],
            errors=[str(value) for value in payload.get("errors", [])],
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class PlanRunState:
    run_id: str
    plan_id: str
    started_at: str
    updated_at: str
    current_task_id: str = ""
    completed_task_ids: list[str] = field(default_factory=list)
    blocked_task_ids: list[str] = field(default_factory=list)
    failed_task_ids: list[str] = field(default_factory=list)
    skipped_task_ids: list[str] = field(default_factory=list)
    retry_counts: dict[str, int] = field(default_factory=dict)
    task_states: dict[str, TaskRunState] = field(default_factory=dict)
    events: list[dict[str, Any]] = field(default_factory=list)
    git_head_start: str = ""
    git_head_last_verified: str = ""
    queue_manifest_path: str = ""
    dashboard_paths: list[str] = field(default_factory=list)
    artifact_paths: list[str] = field(default_factory=list)

    @classmethod
    def create(cls, run_id: str, plan_id: str, *, queue_manifest_path: str = "", git_head_start: str = "") -> "PlanRunState":
        now = _utc_iso()
        return cls(
            run_id=run_id,
            plan_id=plan_id,
            started_at=now,
            updated_at=now,
            queue_manifest_path=queue_manifest_path,
            git_head_start=git_head_start,
            git_head_last_verified=git_head_start,
        )

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "PlanRunState":
        return cls(
            run_id=str(payload.get("run_id") or ""),
            plan_id=str(payload.get("plan_id") or ""),
            started_at=str(payload.get("started_at") or ""),
            updated_at=str(payload.get("updated_at") or ""),
            current_task_id=str(payload.get("current_task_id") or ""),
            completed_task_ids=[str(value) for value in payload.get("completed_task_ids", [])],
            blocked_task_ids=[str(value) for value in payload.get("blocked_task_ids", [])],
            failed_task_ids=[str(value) for value in payload.get("failed_task_ids", [])],
            skipped_task_ids=[str(value) for value in payload.get("skipped_task_ids", [])],
            retry_counts={str(key): int(value) for key, value in dict(payload.get("retry_counts", {})).items()},
            task_states={
                str(task_id): TaskRunState.from_dict(task_payload)
                for task_id, task_payload in dict(payload.get("task_states", {})).items()
                if isinstance(task_payload, Mapping)
            },
            events=list(payload.get("events", [])),
            git_head_start=str(payload.get("git_head_start") or ""),
            git_head_last_verified=str(payload.get("git_head_last_verified") or ""),
            queue_manifest_path=str(payload.get("queue_manifest_path") or ""),
            dashboard_paths=[str(value) for value in payload.get("dashboard_paths", [])],
            artifact_paths=[str(value) for value in payload.get("artifact_paths", [])],
        )

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["task_states"] = {task_id: state.to_dict() for task_id, state in self.task_states.items()}
        return payload


def load_state(path: str | Path) -> PlanRunState:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError("state JSON must be an object")
    return PlanRunState.from_dict(payload)


def save_state(state: PlanRunState, path: str | Path) -> Path:
    state.updated_at = _utc_iso()
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(state.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return target


def append_event(state: PlanRunState, event: Mapping[str, Any]) -> None:
    payload = dict(event)
    payload.setdefault("at", _utc_iso())
    state.events.append(payload)
    state.updated_at = _utc_iso()


def mark_task_started(state: PlanRunState, task_id: str) -> None:
    task_state = state.task_states.get(task_id, TaskRunState(task_id=task_id))
    task_state.status = "running"
    task_state.started_at = task_state.started_at or _utc_iso()
    task_state.attempts += 1
    state.task_states[task_id] = task_state
    state.current_task_id = task_id
    append_event(state, {"event": "task_started", "task_id": task_id})


def mark_task_done(
    state: PlanRunState,
    task_id: str,
    *,
    result_path: str = "",
    artifact_paths: list[str] | None = None,
) -> None:
    _remove_from_all_terminal_sets(state, task_id)
    if task_id not in state.completed_task_ids:
        state.completed_task_ids.append(task_id)
    task_state = state.task_states.get(task_id, TaskRunState(task_id=task_id))
    task_state.status = "done"
    task_state.finished_at = _utc_iso()
    task_state.result_path = result_path or task_state.result_path
    for path in artifact_paths or []:
        if path not in task_state.artifact_paths:
            task_state.artifact_paths.append(path)
        if path not in state.artifact_paths:
            state.artifact_paths.append(path)
    state.task_states[task_id] = task_state
    state.current_task_id = ""
    append_event(state, {"event": "task_done", "task_id": task_id, "result_path": result_path})


def mark_task_blocked(state: PlanRunState, task_id: str, reason: str) -> None:
    _remove_from_all_terminal_sets(state, task_id)
    if task_id not in state.blocked_task_ids:
        state.blocked_task_ids.append(task_id)
    task_state = state.task_states.get(task_id, TaskRunState(task_id=task_id))
    task_state.status = "blocked"
    task_state.finished_at = _utc_iso()
    task_state.errors.append(reason)
    state.task_states[task_id] = task_state
    state.current_task_id = task_id
    append_event(state, {"event": "task_blocked", "task_id": task_id, "reason": reason})


def mark_task_failed(state: PlanRunState, task_id: str, reason: str) -> None:
    _remove_from_all_terminal_sets(state, task_id)
    if task_id not in state.failed_task_ids:
        state.failed_task_ids.append(task_id)
    task_state = state.task_states.get(task_id, TaskRunState(task_id=task_id))
    task_state.status = "failed"
    task_state.finished_at = _utc_iso()
    task_state.errors.append(reason)
    state.task_states[task_id] = task_state
    state.current_task_id = task_id
    append_event(state, {"event": "task_failed", "task_id": task_id, "reason": reason})


def increment_retry(state: PlanRunState, task_id: str) -> int:
    state.retry_counts[task_id] = int(state.retry_counts.get(task_id, 0)) + 1
    append_event(state, {"event": "task_retry_incremented", "task_id": task_id, "retry_count": state.retry_counts[task_id]})
    return state.retry_counts[task_id]


def summarize_state(state: PlanRunState) -> dict[str, Any]:
    status = "running"
    if state.failed_task_ids:
        status = "failed"
    elif state.blocked_task_ids:
        status = "blocked"
    return {
        "run_id": state.run_id,
        "plan_id": state.plan_id,
        "status": status,
        "current_task_id": state.current_task_id,
        "completed_count": len(state.completed_task_ids),
        "blocked_count": len(state.blocked_task_ids),
        "failed_count": len(state.failed_task_ids),
        "skipped_count": len(state.skipped_task_ids),
        "retry_counts": dict(state.retry_counts),
        "artifact_count": len(state.artifact_paths),
        "last_event": state.events[-1] if state.events else None,
    }


def _remove_from_all_terminal_sets(state: PlanRunState, task_id: str) -> None:
    for values in (
        state.completed_task_ids,
        state.blocked_task_ids,
        state.failed_task_ids,
        state.skipped_task_ids,
    ):
        while task_id in values:
            values.remove(task_id)


def _utc_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
