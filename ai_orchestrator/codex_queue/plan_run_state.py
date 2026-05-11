from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping


STATE_SCHEMA_VERSION = "codex_plan_run_state.v2"
RUN_LIFECYCLE_STATUSES = {
    "initialized",
    "queued",
    "running",
    "paused",
    "completed",
    "blocked",
    "failed",
    "recovering",
    "recovered",
    "inconsistent",
}
TERMINAL_STATUS_FIELDS = (
    "completed_task_ids",
    "blocked_task_ids",
    "failed_task_ids",
    "skipped_task_ids",
)


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
    last_event: str = ""

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
            last_event=str(payload.get("last_event") or ""),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class PlanRunState:
    run_id: str
    plan_id: str
    started_at: str
    updated_at: str
    status: str = "initialized"
    state_schema_version: str = STATE_SCHEMA_VERSION
    created_by: str = "long_run_controller"
    last_updated_by: str = "long_run_controller"
    current_task_id: str = ""
    completed_task_ids: list[str] = field(default_factory=list)
    blocked_task_ids: list[str] = field(default_factory=list)
    failed_task_ids: list[str] = field(default_factory=list)
    skipped_task_ids: list[str] = field(default_factory=list)
    retry_counts: dict[str, int] = field(default_factory=dict)
    task_states: dict[str, TaskRunState] = field(default_factory=dict)
    checkpoints: list[dict[str, Any]] = field(default_factory=list)
    events: list[dict[str, Any]] = field(default_factory=list)
    git_head_start: str = ""
    git_head_last_verified: str = ""
    queue_manifest_path: str = ""
    dashboard_paths: list[str] = field(default_factory=list)
    artifact_paths: list[str] = field(default_factory=list)
    latest_handoff_prompt_path: str = ""
    latest_recovery_report_path: str = ""

    @classmethod
    def create(
        cls,
        run_id: str,
        plan_id: str,
        *,
        queue_manifest_path: str = "",
        git_head_start: str = "",
        created_by: str = "long_run_controller",
    ) -> "PlanRunState":
        now = _utc_iso()
        return cls(
            run_id=run_id,
            plan_id=plan_id,
            started_at=now,
            updated_at=now,
            status="initialized",
            state_schema_version=STATE_SCHEMA_VERSION,
            created_by=created_by,
            last_updated_by=created_by,
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
            status=_normalize_run_status(str(payload.get("status") or "initialized")),
            state_schema_version=str(payload.get("state_schema_version") or STATE_SCHEMA_VERSION),
            created_by=str(payload.get("created_by") or "long_run_controller"),
            last_updated_by=str(payload.get("last_updated_by") or "long_run_controller"),
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
            checkpoints=[
                dict(item)
                for item in payload.get("checkpoints", [])
                if isinstance(item, Mapping)
            ],
            events=list(payload.get("events", [])),
            git_head_start=str(payload.get("git_head_start") or ""),
            git_head_last_verified=str(payload.get("git_head_last_verified") or ""),
            queue_manifest_path=str(payload.get("queue_manifest_path") or ""),
            dashboard_paths=[str(value) for value in payload.get("dashboard_paths", [])],
            artifact_paths=[str(value) for value in payload.get("artifact_paths", [])],
            latest_handoff_prompt_path=str(payload.get("latest_handoff_prompt_path") or ""),
            latest_recovery_report_path=str(payload.get("latest_recovery_report_path") or ""),
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


def save_state(state: PlanRunState, path: str | Path, *, updated_by: str | None = None) -> Path:
    state.updated_at = _utc_iso()
    state.state_schema_version = state.state_schema_version or STATE_SCHEMA_VERSION
    if updated_by:
        state.last_updated_by = updated_by
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(state.to_dict(), indent=2, sort_keys=True) + "\n"
    _atomic_write_text(target, payload)
    return target


def append_event(state: PlanRunState, event: Mapping[str, Any]) -> None:
    payload = dict(event)
    payload.setdefault("at", _utc_iso())
    state.events.append(payload)
    state.updated_at = _utc_iso()


def set_run_status(state: PlanRunState, status: str, *, reason: str = "", updated_by: str = "long_run_controller") -> None:
    normalized = _normalize_run_status(status)
    if state.status != normalized:
        append_event(state, {"event": "run_status_changed", "from": state.status, "to": normalized, "reason": reason})
    state.status = normalized
    state.last_updated_by = updated_by
    state.updated_at = _utc_iso()


def create_checkpoint(state: PlanRunState, reason: str, *, task_id: str | None = None) -> dict[str, Any]:
    created_at = _utc_iso()
    checkpoint = {
        "checkpoint_id": f"cp_{len(state.checkpoints) + 1:04d}_{created_at.replace(':', '').replace('-', '')}",
        "checkpoint_created_at": created_at,
        "checkpoint_reason": reason,
        "task_id": task_id if task_id is not None else state.current_task_id,
        "status": state.status,
        "completed_task_ids": list(state.completed_task_ids),
        "blocked_task_ids": list(state.blocked_task_ids),
        "failed_task_ids": list(state.failed_task_ids),
        "skipped_task_ids": list(state.skipped_task_ids),
        "retry_counts": dict(state.retry_counts),
        "artifact_paths": list(state.artifact_paths),
        "latest_handoff_prompt_path": state.latest_handoff_prompt_path,
        "latest_recovery_report_path": state.latest_recovery_report_path,
    }
    state.checkpoints.append(checkpoint)
    append_event(state, {"event": "checkpoint_created", "checkpoint_id": checkpoint["checkpoint_id"], "reason": reason})
    return checkpoint


def list_checkpoints(state: PlanRunState) -> list[dict[str, Any]]:
    return [dict(checkpoint) for checkpoint in state.checkpoints]


def get_last_checkpoint(state: PlanRunState) -> dict[str, Any] | None:
    return dict(state.checkpoints[-1]) if state.checkpoints else None


def restore_checkpoint(state: PlanRunState, checkpoint_id: str) -> dict[str, Any]:
    checkpoint = next((item for item in state.checkpoints if item.get("checkpoint_id") == checkpoint_id), None)
    if checkpoint is None:
        raise ValueError(f"checkpoint not found: {checkpoint_id}")
    state.current_task_id = str(checkpoint.get("task_id") or "")
    state.status = _normalize_run_status(str(checkpoint.get("status") or "recovered"))
    state.completed_task_ids = [str(value) for value in checkpoint.get("completed_task_ids", [])]
    state.blocked_task_ids = [str(value) for value in checkpoint.get("blocked_task_ids", [])]
    state.failed_task_ids = [str(value) for value in checkpoint.get("failed_task_ids", [])]
    state.skipped_task_ids = [str(value) for value in checkpoint.get("skipped_task_ids", [])]
    state.retry_counts = {str(key): int(value) for key, value in dict(checkpoint.get("retry_counts", {})).items()}
    state.artifact_paths = [str(value) for value in checkpoint.get("artifact_paths", [])]
    state.latest_handoff_prompt_path = str(checkpoint.get("latest_handoff_prompt_path") or "")
    state.latest_recovery_report_path = str(checkpoint.get("latest_recovery_report_path") or "")
    append_event(state, {"event": "checkpoint_restored", "checkpoint_id": checkpoint_id})
    return dict(checkpoint)


def mark_task_started(state: PlanRunState, task_id: str) -> None:
    set_run_status(state, "running", reason=f"task_started:{task_id}")
    task_state = state.task_states.get(task_id, TaskRunState(task_id=task_id))
    task_state.status = "running"
    task_state.started_at = task_state.started_at or _utc_iso()
    task_state.finished_at = ""
    task_state.attempts += 1
    task_state.last_event = "task_started"
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
    task_state.last_event = "task_done"
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
    if reason and reason not in task_state.errors:
        task_state.errors.append(reason)
    task_state.last_event = "task_blocked"
    state.task_states[task_id] = task_state
    state.current_task_id = task_id
    set_run_status(state, "blocked", reason=reason)
    append_event(state, {"event": "task_blocked", "task_id": task_id, "reason": reason})


def mark_task_failed(state: PlanRunState, task_id: str, reason: str) -> None:
    _remove_from_all_terminal_sets(state, task_id)
    if task_id not in state.failed_task_ids:
        state.failed_task_ids.append(task_id)
    task_state = state.task_states.get(task_id, TaskRunState(task_id=task_id))
    task_state.status = "failed"
    task_state.finished_at = _utc_iso()
    if reason and reason not in task_state.errors:
        task_state.errors.append(reason)
    task_state.last_event = "task_failed"
    state.task_states[task_id] = task_state
    state.current_task_id = task_id
    set_run_status(state, "failed", reason=reason)
    append_event(state, {"event": "task_failed", "task_id": task_id, "reason": reason})


def mark_task_needs_retry(state: PlanRunState, task_id: str, reason: str) -> None:
    task_state = state.task_states.get(task_id, TaskRunState(task_id=task_id))
    task_state.status = "needs_retry"
    task_state.finished_at = _utc_iso()
    if reason and reason not in task_state.errors:
        task_state.errors.append(reason)
    task_state.last_event = "task_needs_retry"
    state.task_states[task_id] = task_state
    state.current_task_id = task_id
    set_run_status(state, "paused", reason=reason)
    append_event(state, {"event": "task_needs_retry", "task_id": task_id, "reason": reason})


def record_task_artifacts(state: PlanRunState, task_id: str, artifact_paths: Iterable[str], *, result_path: str = "") -> None:
    task_state = state.task_states.get(task_id, TaskRunState(task_id=task_id))
    task_state.result_path = result_path or task_state.result_path
    for path in artifact_paths:
        value = str(path)
        if value not in task_state.artifact_paths:
            task_state.artifact_paths.append(value)
        if value not in state.artifact_paths:
            state.artifact_paths.append(value)
    state.task_states[task_id] = task_state
    append_event(state, {"event": "task_artifacts_recorded", "task_id": task_id, "artifact_paths": list(artifact_paths)})


def increment_retry(state: PlanRunState, task_id: str) -> int:
    state.retry_counts[task_id] = int(state.retry_counts.get(task_id, 0)) + 1
    append_event(state, {"event": "task_retry_incremented", "task_id": task_id, "retry_count": state.retry_counts[task_id]})
    return state.retry_counts[task_id]


def summarize_state(state: PlanRunState) -> dict[str, Any]:
    status = state.status
    if status == "initialized":
        if state.failed_task_ids:
            status = "failed"
        elif state.blocked_task_ids:
            status = "blocked"
        elif state.completed_task_ids:
            status = "running"
    return {
        "run_id": state.run_id,
        "plan_id": state.plan_id,
        "status": status,
        "state_schema_version": state.state_schema_version,
        "current_task_id": state.current_task_id,
        "completed_count": len(state.completed_task_ids),
        "blocked_count": len(state.blocked_task_ids),
        "failed_count": len(state.failed_task_ids),
        "skipped_count": len(state.skipped_task_ids),
        "retry_counts": dict(state.retry_counts),
        "artifact_count": len(state.artifact_paths),
        "latest_checkpoint": get_last_checkpoint(state),
        "latest_handoff_prompt_path": state.latest_handoff_prompt_path,
        "latest_recovery_report_path": state.latest_recovery_report_path,
        "last_event": state.events[-1] if state.events else None,
    }


def validate_state_consistency(state: PlanRunState, plan_contract_or_tasks: Any) -> dict[str, Any]:
    tasks = _extract_tasks(plan_contract_or_tasks)
    task_ids = {task["task_id"] for task in tasks}
    dependency_by_task = {task["task_id"]: set(task.get("dependencies", [])) for task in tasks}
    errors: list[str] = []
    warnings: list[str] = []

    errors.extend(detect_duplicate_task_statuses(state))
    errors.extend(detect_missing_current_task(state, tasks))
    errors.extend(detect_invalid_retry_counts(state))
    errors.extend(detect_orphan_task_states(state, tasks))

    completed = set(state.completed_task_ids)
    for task_id in state.completed_task_ids:
        for dependency in sorted(dependency_by_task.get(task_id, set())):
            if dependency not in completed:
                errors.append(f"completed task {task_id} has incomplete dependency: {dependency}")

    terminal = completed | set(state.blocked_task_ids) | set(state.failed_task_ids) | set(state.skipped_task_ids)
    pending = sorted(task_ids - terminal)
    if state.status == "completed" and pending:
        errors.append("run marked completed while pending tasks exist")
    if state.status not in RUN_LIFECYCLE_STATUSES:
        errors.append(f"invalid run lifecycle status: {state.status}")

    return {
        "status": "consistent" if not errors else "inconsistent",
        "consistent": not errors,
        "errors": list(dict.fromkeys(errors)),
        "warnings": warnings,
        "known_task_count": len(task_ids),
        "pending_task_ids": pending,
        "orphan_task_ids": _unknown_state_task_ids(state, task_ids),
    }


def detect_orphan_task_states(state: PlanRunState, plan_tasks: Any) -> list[str]:
    tasks = _extract_tasks(plan_tasks)
    known = {task["task_id"] for task in tasks}
    errors: list[str] = []
    for task_id in _unknown_state_task_ids(state, known):
        errors.append(f"unknown task ID in state: {task_id}")
    return errors


def detect_duplicate_task_statuses(state: PlanRunState) -> list[str]:
    task_to_statuses: dict[str, list[str]] = {}
    for field_name in TERMINAL_STATUS_FIELDS:
        for task_id in getattr(state, field_name):
            task_to_statuses.setdefault(str(task_id), []).append(field_name)
    errors: list[str] = []
    for task_id, fields in sorted(task_to_statuses.items()):
        if len(fields) > 1:
            errors.append(f"task {task_id} appears in multiple terminal status lists: {', '.join(fields)}")
    return errors


def detect_missing_current_task(state: PlanRunState, plan_tasks: Any) -> list[str]:
    if not state.current_task_id:
        return []
    tasks = _extract_tasks(plan_tasks)
    known = {task["task_id"] for task in tasks}
    if state.current_task_id not in known:
        return [f"current_task_id not in plan: {state.current_task_id}"]
    return []


def detect_invalid_retry_counts(state: PlanRunState) -> list[str]:
    errors: list[str] = []
    for task_id, count in sorted(state.retry_counts.items()):
        if int(count) < 0:
            errors.append(f"retry count below zero for task {task_id}: {count}")
    return errors


def _remove_from_all_terminal_sets(state: PlanRunState, task_id: str) -> None:
    for values in (
        state.completed_task_ids,
        state.blocked_task_ids,
        state.failed_task_ids,
        state.skipped_task_ids,
    ):
        while task_id in values:
            values.remove(task_id)


def _extract_tasks(plan_contract_or_tasks: Any) -> list[dict[str, Any]]:
    source = getattr(plan_contract_or_tasks, "tasks", plan_contract_or_tasks)
    tasks: list[dict[str, Any]] = []
    if source is None:
        return tasks
    for task in source:
        if isinstance(task, Mapping):
            task_id = str(task.get("task_id") or "")
            dependencies = [str(value) for value in task.get("dependencies", [])]
        else:
            task_id = str(getattr(task, "task_id", ""))
            dependencies = [str(value) for value in getattr(task, "dependencies", [])]
        if task_id:
            tasks.append({"task_id": task_id, "dependencies": dependencies})
    return tasks


def _unknown_state_task_ids(state: PlanRunState, known_task_ids: set[str]) -> list[str]:
    referenced: set[str] = set()
    for field_name in TERMINAL_STATUS_FIELDS:
        referenced.update(str(value) for value in getattr(state, field_name))
    referenced.update(str(value) for value in state.retry_counts)
    referenced.update(str(value) for value in state.task_states)
    if state.current_task_id:
        referenced.add(state.current_task_id)
    return sorted(task_id for task_id in referenced if task_id and task_id not in known_task_ids)


def _normalize_run_status(status: str) -> str:
    value = status.strip().lower()
    if value == "done":
        return "completed"
    if value == "max_steps":
        return "paused"
    return value if value in RUN_LIFECYCLE_STATUSES else "inconsistent"


def _atomic_write_text(target: Path, content: str) -> None:
    tmp_path = target.with_name(f".{target.name}.{os.getpid()}.tmp")
    with tmp_path.open("w", encoding="utf-8") as handle:
        handle.write(content)
        handle.flush()
        try:
            os.fsync(handle.fileno())
        except OSError:
            pass
    os.replace(tmp_path, target)
    try:
        directory_fd = os.open(str(target.parent), os.O_RDONLY)
    except OSError:
        return
    try:
        os.fsync(directory_fd)
    except OSError:
        pass
    finally:
        os.close(directory_fd)


def _utc_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
