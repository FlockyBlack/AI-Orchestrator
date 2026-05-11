from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from .automation_dashboard import build_dashboard
from .execution_lock import ExecutionLock
from .plan_contract import PlanContract, load_plan_contract, validate_plan_contract
from .plan_decomposer import get_next_runnable_tasks
from .plan_recovery import recover_run
from .plan_run_state import (
    PlanRunState,
    append_event,
    create_checkpoint,
    increment_retry,
    load_state,
    mark_task_blocked,
    mark_task_done,
    mark_task_failed,
    mark_task_needs_retry,
    mark_task_started,
    record_task_artifacts,
    save_state,
    set_run_status,
    summarize_state,
    validate_state_consistency,
)
from .plan_to_queue import create_queue_from_plan, inspect_queue, validate_queue_manifest
from .result_acceptance_policy import ACCEPTED, BLOCKED, FAILED, NEEDS_RETRY, evaluate_task_result
from .task_executor import (
    CodexHandoffExecutor,
    FakeTaskExecutor,
    LocalNoopExecutor,
    TaskExecutionContext,
    TaskExecutionResult,
    TaskExecutor,
)


@dataclass
class LongRunController:
    repo_root: str | Path = "."

    def run_plan(
        self,
        plan_file: str | Path,
        queue_root: str | Path,
        *,
        mode: str = "long_supervised",
        max_steps: int = 50,
        executor: str = "fake",
        continue_until: str = "blocked_or_done",
        run_id: str | None = None,
        commit: bool = False,
        push: bool = False,
        dry_run: bool = False,
        stop_after_current: bool = False,
    ) -> dict[str, Any]:
        queue = create_queue_from_plan(plan_file, queue_root, run_id=run_id, dry_run=dry_run)
        if queue.status == "blocked":
            return _controller_result(
                status="blocked",
                stop_reason="queue_blocked",
                plan_id=queue.plan_id,
                run_id=queue.run_id,
                errors=queue.errors,
                payload={"queue_creation": queue.to_dict()},
                safety_ok=True,
                validation_passed=False,
            )
        if dry_run:
            return _controller_result(
                status="dry_run",
                stop_reason="dry_run",
                plan_id=queue.plan_id,
                run_id=queue.run_id,
                payload={"queue_creation": queue.to_dict()},
                safety_ok=True,
                validation_passed=True,
            )
        plan = load_plan_contract(plan_file)
        manifest = _read_json(queue.queue_paths["manifest"])
        state_path = Path(manifest.get("state_path") or Path(queue.queue_paths["run_root"]) / "state.json")
        if state_path.exists():
            state = load_state(state_path)
            append_event(state, {"event": "run_plan_loaded_existing_state"})
        else:
            state = PlanRunState.create(
                queue.run_id,
                plan.plan_id,
                queue_manifest_path=queue.queue_paths["manifest"],
                git_head_start=_git_head(self.repo_root),
            )
            set_run_status(state, "queued", reason="queue_created")
            create_checkpoint(state, "before_first_execution")
            save_state(state, state_path)
        return self._run_existing(
            plan,
            state,
            state_path,
            Path(queue.queue_paths["run_root"]),
            Path(queue_root),
            max_steps=max_steps,
            executor=executor,
            continue_until=continue_until,
            mode=mode,
            commit=commit,
            push=push,
            stop_after_current=stop_after_current,
        )

    def continue_plan(
        self,
        run_id: str,
        queue_root: str | Path,
        *,
        max_steps: int = 50,
        executor: str = "fake",
        continue_until: str = "blocked_or_done",
        stop_after_current: bool = False,
    ) -> dict[str, Any]:
        inspection = inspect_queue(queue_root, run_id)
        if inspection["status"] not in {"found", "invalid"}:
            return _controller_result(
                status="blocked",
                stop_reason="missing_run",
                plan_id="",
                run_id=run_id,
                errors=tuple(inspection.get("errors", [])),
                payload=inspection,
                safety_ok=True,
                validation_passed=False,
            )
        manifest = inspection.get("manifest", {})
        manifest_validation = validate_queue_manifest(manifest)
        if not manifest_validation["valid"]:
            return _controller_result(
                status="blocked",
                stop_reason="invalid_manifest",
                plan_id=str(manifest.get("plan_id") or ""),
                run_id=run_id,
                errors=tuple(manifest_validation["errors"]),
                payload=inspection,
                safety_ok=True,
                validation_passed=False,
            )
        plan_file = manifest.get("source_plan_file")
        if not plan_file:
            return _controller_result(
                status="blocked",
                stop_reason="manifest_missing_plan",
                plan_id=str(manifest.get("plan_id") or ""),
                run_id=run_id,
                errors=("manifest missing source_plan_file",),
                payload=inspection,
                safety_ok=True,
                validation_passed=False,
            )
        plan = load_plan_contract(plan_file)
        state_path = Path(str(manifest.get("state_path") or Path(inspection["run_dir"]) / "state.json"))
        state = load_state(state_path)
        consistency = validate_state_consistency(state, plan)
        if not consistency["consistent"]:
            set_run_status(state, "inconsistent", reason="continue_preflight_consistency_failed")
            save_state(state, state_path)
            return _controller_result(
                status="blocked",
                stop_reason="inconsistent_state",
                plan_id=plan.plan_id,
                run_id=run_id,
                errors=tuple(consistency["errors"]),
                payload={
                    "inspection": inspection,
                    "state_consistency": consistency,
                    "state_path": str(state_path),
                    "run_root": str(Path(inspection["run_dir"])),
                },
                safety_ok=True,
                validation_passed=False,
            )
        return self._run_existing(
            plan,
            state,
            state_path,
            Path(inspection["run_dir"]),
            Path(queue_root),
            max_steps=max_steps,
            executor=executor,
            continue_until=continue_until,
            mode=plan.mode,
            commit=False,
            push=False,
            stop_after_current=stop_after_current,
        )

    def recover_plan(
        self,
        run_id: str,
        queue_root: str | Path,
        *,
        allow_stale_lock_clear: bool = False,
    ) -> dict[str, Any]:
        return recover_run(run_id, queue_root, allow_stale_lock_clear=allow_stale_lock_clear)

    def execute_next_task(
        self,
        plan: PlanContract,
        state: PlanRunState,
        state_path: str | Path,
        run_root: str | Path,
        queue_root: str | Path,
        executor: TaskExecutor,
    ) -> dict[str, Any]:
        next_tasks = get_next_runnable_tasks(
            plan.tasks,
            completed=state.completed_task_ids,
            blocked=state.blocked_task_ids,
            failed=state.failed_task_ids,
        )
        if not next_tasks:
            if len(state.completed_task_ids) == len(plan.tasks):
                set_run_status(state, "completed", reason="all_tasks_completed")
                save_state(state, state_path)
                return {"stop": True, "stop_reason": "done", "status": "done"}
            return {"stop": True, "stop_reason": "no_runnable_tasks", "status": "blocked"}
        task = next_tasks[0]
        mark_task_started(state, task.task_id)
        save_state(state, state_path)
        context = TaskExecutionContext(
            task_spec=task,
            plan=plan,
            queue_root=queue_root,
            run_id=state.run_id,
            plan_id=plan.plan_id,
            repo_root=self.repo_root,
            run_dir=run_root,
            state_summary=_state_summary_for_handoff(state),
        )
        execution = executor.execute(context)
        return self._apply_execution_result(plan, state, state_path, task.task_id, execution)

    def _run_existing(
        self,
        plan: PlanContract,
        state: PlanRunState,
        state_path: Path,
        run_root: Path,
        queue_root: Path,
        *,
        max_steps: int,
        executor: str,
        continue_until: str,
        mode: str,
        commit: bool,
        push: bool,
        stop_after_current: bool,
    ) -> dict[str, Any]:
        validation = validate_plan_contract(plan)
        if not validation.valid:
            return _controller_result(
                status="blocked",
                stop_reason="plan_validation_failed",
                plan_id=plan.plan_id,
                run_id=state.run_id,
                errors=validation.errors,
                payload={"validation": validation.to_dict()},
                safety_ok=True,
                validation_passed=False,
            )
        consistency = validate_state_consistency(state, plan)
        if not consistency["consistent"]:
            set_run_status(state, "inconsistent", reason="run_preflight_consistency_failed")
            save_state(state, state_path)
            return _controller_result(
                status="blocked",
                stop_reason="inconsistent_state",
                plan_id=plan.plan_id,
                run_id=state.run_id,
                errors=tuple(consistency["errors"]),
                payload={"state_consistency": consistency, "state_path": str(state_path), "run_root": str(run_root)},
                safety_ok=True,
                validation_passed=False,
            )
        lock = ExecutionLock(queue_root=queue_root, plan_id=plan.plan_id, run_id=state.run_id, repo_root=self.repo_root)
        lock_result = lock.acquire()
        if not lock_result["acquired"]:
            return _controller_result(
                status="blocked",
                stop_reason=str(lock_result["status"]),
                plan_id=plan.plan_id,
                run_id=state.run_id,
                errors=tuple(lock_result["errors"]),
                payload={"lock": lock_result, "state_path": str(state_path), "run_root": str(run_root)},
                safety_ok=True,
                validation_passed=False,
            )
        executor_instance = _executor_for_mode(executor)
        steps_attempted = 0
        steps_completed = 0
        status = "max_steps"
        stop_reason = "max_steps"
        dashboard: dict[str, Any] = {}
        try:
            while steps_attempted < max_steps:
                step_result = self.execute_next_task(plan, state, state_path, run_root, queue_root, executor_instance)
                steps_attempted += 1
                if step_result.get("status") == "accepted":
                    steps_completed += 1
                dashboard = build_dashboard(state, plan, run_root / "dashboard")
                save_state(state, state_path)
                if step_result.get("stop"):
                    status = str(step_result["status"])
                    stop_reason = str(step_result["stop_reason"])
                    break
                if step_result["status"] in {"blocked", "failed", "requiring_operator_handoff", "needs_retry"}:
                    status = str(step_result["status"])
                    stop_reason = status
                    break
                if stop_after_current:
                    status = "max_steps"
                    stop_reason = "stop_after_current"
                    set_run_status(state, "paused", reason=stop_reason)
                    break
                if continue_until == "one_step":
                    status = "max_steps"
                    stop_reason = "one_step"
                    set_run_status(state, "paused", reason=stop_reason)
                    break
                if len(state.completed_task_ids) == len(plan.tasks):
                    status = "done"
                    stop_reason = "done"
                    set_run_status(state, "completed", reason="all_tasks_completed")
                    break
            else:
                if len(state.completed_task_ids) == len(plan.tasks):
                    status = "done"
                    stop_reason = "done"
                    set_run_status(state, "completed", reason="all_tasks_completed")
                else:
                    set_run_status(state, "paused", reason="max_steps")
                dashboard = build_dashboard(state, plan, run_root / "dashboard")
        finally:
            lock.release()

        if not dashboard:
            dashboard = build_dashboard(state, plan, run_root / "dashboard")
        save_state(state, state_path)
        next_runnable_ids = _next_runnable_ids(plan, state)
        payload = {
            "plan_id": plan.plan_id,
            "run_id": state.run_id,
            "mode": mode,
            "continue_until": continue_until,
            "steps_executed": steps_attempted,
            "steps_attempted": steps_attempted,
            "steps_completed": steps_completed,
            "max_steps": max_steps,
            "executor": executor,
            "commit_requested": commit,
            "push_requested": push,
            "commit_performed": False,
            "push_performed": False,
            "dashboard": dashboard,
            "dashboard_path": dashboard.get("dashboard_paths", {}).get("json", ""),
            "state_path": str(state_path),
            "run_root": str(run_root),
            "recovery_report_path": state.latest_recovery_report_path,
            "handoff_prompt_path": state.latest_handoff_prompt_path,
            "next_runnable_task_ids": next_runnable_ids,
        }
        result = _controller_result(
            status=status,
            stop_reason=stop_reason,
            plan_id=plan.plan_id,
            run_id=state.run_id,
            payload=payload,
            steps_attempted=steps_attempted,
            steps_completed=steps_completed,
            blocked_task_ids=state.blocked_task_ids,
            failed_task_ids=state.failed_task_ids,
            completed_task_ids=state.completed_task_ids,
            next_runnable_task_ids=next_runnable_ids,
            state_path=str(state_path),
            dashboard_path=payload["dashboard_path"],
            recovery_report_path=state.latest_recovery_report_path,
            handoff_prompt_path=state.latest_handoff_prompt_path,
            safety_ok=True,
            validation_passed=validate_state_consistency(state, plan)["consistent"],
        )
        _write_json(run_root / "result.json", result)
        return result

    def _apply_execution_result(
        self,
        plan: PlanContract,
        state: PlanRunState,
        state_path: str | Path,
        task_id: str,
        execution: TaskExecutionResult,
    ) -> dict[str, Any]:
        if execution.status == "requiring_operator_handoff":
            record_task_artifacts(
                state,
                task_id,
                execution.artifact_paths,
                result_path=str(execution.artifact_paths[0]) if execution.artifact_paths else "",
            )
            state.latest_handoff_prompt_path = str(execution.artifact_paths[0]) if execution.artifact_paths else ""
            append_event(state, {"event": "operator_handoff_required", "task_id": task_id, "handoff_prompt_path": state.latest_handoff_prompt_path})
            set_run_status(state, "paused", reason="operator_handoff_required")
            save_state(state, state_path)
            return {"status": "requiring_operator_handoff", "stop": False, "execution": execution.to_dict()}
        task = next(item for item in plan.tasks if item.task_id == task_id)
        decision = evaluate_task_result(task, execution.result_payload, plan.safety_boundaries)
        if decision.status == ACCEPTED:
            mark_task_done(
                state,
                task_id,
                result_path=str(execution.artifact_paths[0]) if execution.artifact_paths else "",
                artifact_paths=list(execution.artifact_paths),
            )
            save_state(state, state_path)
            return {"status": "accepted", "stop": False, "decision": decision.to_dict(), "execution": execution.to_dict()}
        if decision.status == BLOCKED:
            record_task_artifacts(state, task_id, execution.artifact_paths)
            mark_task_blocked(state, task_id, "; ".join(decision.errors or decision.reasons))
            save_state(state, state_path)
            return {"status": "blocked", "stop": False, "decision": decision.to_dict(), "execution": execution.to_dict()}
        if decision.status == NEEDS_RETRY:
            record_task_artifacts(state, task_id, execution.artifact_paths)
            retry_count = increment_retry(state, task_id)
            if retry_count > task.max_retries:
                mark_task_blocked(state, task_id, f"retry exceeded: {retry_count}>{task.max_retries}; " + "; ".join(decision.errors or decision.reasons))
                save_state(state, state_path)
                return {"status": "blocked", "stop": False, "decision": decision.to_dict(), "execution": execution.to_dict(), "retry_count": retry_count}
            mark_task_needs_retry(state, task_id, "; ".join(decision.errors or decision.reasons))
            save_state(state, state_path)
            return {"status": "needs_retry", "stop": False, "decision": decision.to_dict(), "execution": execution.to_dict(), "retry_count": retry_count}
        if decision.status == FAILED:
            record_task_artifacts(state, task_id, execution.artifact_paths)
            mark_task_failed(state, task_id, "; ".join(decision.errors or decision.reasons))
            save_state(state, state_path)
            return {"status": "failed", "stop": False, "decision": decision.to_dict(), "execution": execution.to_dict()}
        return {"status": decision.status, "stop": False, "decision": decision.to_dict(), "execution": execution.to_dict()}


def run_plan(*args: Any, **kwargs: Any) -> dict[str, Any]:
    return LongRunController().run_plan(*args, **kwargs)


def continue_plan(*args: Any, **kwargs: Any) -> dict[str, Any]:
    return LongRunController().continue_plan(*args, **kwargs)


def recover_plan(*args: Any, **kwargs: Any) -> dict[str, Any]:
    return LongRunController().recover_plan(*args, **kwargs)


def _executor_for_mode(executor: str) -> TaskExecutor:
    if executor == "fake":
        return FakeTaskExecutor()
    if executor == "noop":
        return LocalNoopExecutor()
    if executor == "handoff":
        return CodexHandoffExecutor()
    raise ValueError(f"unsupported executor mode: {executor}")


def _state_summary_for_handoff(state: PlanRunState) -> dict[str, Any]:
    summary = summarize_state(state)
    summary.update(
        {
            "completed_task_ids": list(state.completed_task_ids),
            "blocked_task_ids": list(state.blocked_task_ids),
            "failed_task_ids": list(state.failed_task_ids),
            "retry_counts": dict(state.retry_counts),
            "latest_checkpoint": state.checkpoints[-1] if state.checkpoints else None,
        }
    )
    return summary


def _next_runnable_ids(plan: PlanContract, state: PlanRunState) -> list[str]:
    return [
        task.task_id
        for task in get_next_runnable_tasks(
            plan.tasks,
            completed=state.completed_task_ids,
            blocked=state.blocked_task_ids,
            failed=state.failed_task_ids,
        )
    ]


def _read_json(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def _write_json(path: str | Path, payload: Mapping[str, Any]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(dict(payload), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _controller_result(
    *,
    status: str,
    stop_reason: str,
    plan_id: str,
    run_id: str,
    payload: dict[str, Any],
    errors: tuple[str, ...] | list[str] = (),
    steps_attempted: int = 0,
    steps_completed: int = 0,
    blocked_task_ids: list[str] | None = None,
    failed_task_ids: list[str] | None = None,
    completed_task_ids: list[str] | None = None,
    next_runnable_task_ids: list[str] | None = None,
    state_path: str = "",
    dashboard_path: str = "",
    recovery_report_path: str = "",
    handoff_prompt_path: str = "",
    safety_ok: bool = True,
    validation_passed: bool = True,
) -> dict[str, Any]:
    payload.setdefault("plan_id", plan_id)
    payload.setdefault("run_id", run_id)
    if state_path:
        payload.setdefault("state_path", state_path)
    return {
        "status": status,
        "run_id": run_id,
        "plan_id": plan_id,
        "stop_reason": stop_reason or status,
        "steps_attempted": steps_attempted,
        "steps_completed": steps_completed,
        "blocked_task_ids": list(blocked_task_ids or []),
        "failed_task_ids": list(failed_task_ids or []),
        "completed_task_ids": list(completed_task_ids or []),
        "next_runnable_task_ids": list(next_runnable_task_ids or []),
        "state_path": state_path,
        "dashboard_path": dashboard_path,
        "recovery_report_path": recovery_report_path,
        "handoff_prompt_path": handoff_prompt_path,
        "safety_ok": safety_ok,
        "validation_passed": validation_passed,
        "errors": list(errors),
        "payload": payload,
    }


def _git_head(repo_root: str | Path) -> str:
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(repo_root),
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError:
        return ""
    return completed.stdout.strip() if completed.returncode == 0 else ""
