from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .automation_dashboard import build_dashboard
from .execution_lock import ExecutionLock
from .plan_contract import PlanContract, load_plan_contract, validate_plan_contract
from .plan_decomposer import get_next_runnable_tasks
from .plan_recovery import recover_run
from .plan_run_state import (
    PlanRunState,
    load_state,
    mark_task_blocked,
    mark_task_done,
    mark_task_failed,
    mark_task_started,
    save_state,
)
from .plan_to_queue import create_queue_from_plan
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
    ) -> dict[str, Any]:
        queue = create_queue_from_plan(plan_file, queue_root, run_id=run_id, dry_run=dry_run)
        if queue.status == "blocked":
            return _result("blocked", queue.to_dict(), errors=queue.errors)
        if dry_run:
            return _result("dry_run", queue.to_dict())
        plan = load_plan_contract(plan_file)
        state_path = Path(queue.queue_paths["run_root"]) / "state.json"
        state = PlanRunState.create(
            queue.run_id,
            plan.plan_id,
            queue_manifest_path=queue.queue_paths["manifest"],
            git_head_start=_git_head(self.repo_root),
        )
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
        )

    def continue_plan(
        self,
        run_id: str,
        queue_root: str | Path,
        *,
        max_steps: int = 50,
        executor: str = "fake",
        continue_until: str = "blocked_or_done",
    ) -> dict[str, Any]:
        located = _locate_run(run_id, queue_root)
        if located["status"] != "found":
            return _result("blocked", located, errors=located["errors"])
        manifest = _read_json(located["manifest_path"])
        plan_file = manifest.get("source_plan_file")
        if not plan_file:
            return _result("blocked", located, errors=("manifest missing source_plan_file",))
        plan = load_plan_contract(plan_file)
        state_path = Path(located["run_root"]) / "state.json"
        state = load_state(state_path)
        return self._run_existing(
            plan,
            state,
            state_path,
            Path(located["run_root"]),
            Path(queue_root),
            max_steps=max_steps,
            executor=executor,
            continue_until=continue_until,
            mode=plan.mode,
            commit=False,
            push=False,
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
            return {"stop": True, "stop_reason": "done", "status": "done"}
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
    ) -> dict[str, Any]:
        validation = validate_plan_contract(plan)
        if not validation.valid:
            return _result("blocked", {"validation": validation.to_dict()}, errors=validation.errors)
        lock = ExecutionLock(queue_root=queue_root, plan_id=plan.plan_id, run_id=state.run_id, repo_root=self.repo_root)
        lock_result = lock.acquire()
        if not lock_result["acquired"]:
            return _result("blocked", {"lock": lock_result}, errors=tuple(lock_result["errors"]))
        executor_instance = _executor_for_mode(executor)
        steps = 0
        status = "max_steps"
        stop_reason = "max_steps"
        try:
            while steps < max_steps:
                step_result = self.execute_next_task(plan, state, state_path, run_root, queue_root, executor_instance)
                steps += 1
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
                if continue_until == "one_step":
                    status = "max_steps"
                    stop_reason = "one_step"
                    break
                if len(state.completed_task_ids) == len(plan.tasks):
                    status = "done"
                    stop_reason = "done"
                    break
            else:
                dashboard = build_dashboard(state, plan, run_root / "dashboard")
        finally:
            lock.release()

        payload = {
            "plan_id": plan.plan_id,
            "run_id": state.run_id,
            "mode": mode,
            "continue_until": continue_until,
            "steps_executed": steps,
            "max_steps": max_steps,
            "executor": executor,
            "commit_requested": commit,
            "push_requested": push,
            "commit_performed": False,
            "push_performed": False,
            "dashboard": dashboard,
            "state_path": str(state_path),
            "run_root": str(run_root),
        }
        result_path = run_root / "result.json"
        result = _result(status, payload, stop_reason=stop_reason)
        _write_json(result_path, result)
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
            for path in execution.artifact_paths:
                if path not in state.artifact_paths:
                    state.artifact_paths.append(path)
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
            mark_task_blocked(state, task_id, "; ".join(decision.errors or decision.reasons))
            save_state(state, state_path)
            return {"status": "blocked", "stop": False, "decision": decision.to_dict(), "execution": execution.to_dict()}
        if decision.status == NEEDS_RETRY:
            mark_task_failed(state, task_id, "; ".join(decision.errors or decision.reasons))
            save_state(state, state_path)
            return {"status": "needs_retry", "stop": False, "decision": decision.to_dict(), "execution": execution.to_dict()}
        if decision.status == FAILED:
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


def _locate_run(run_id: str, queue_root: str | Path) -> dict[str, Any]:
    root = Path(queue_root)
    matches = sorted(root.glob(f"generated/*/{run_id}/manifest.json"))
    if not matches:
        return {"status": "missing", "errors": [f"run_id not found: {run_id}"]}
    manifest = matches[0]
    return {
        "status": "found",
        "manifest_path": str(manifest),
        "run_root": str(manifest.parent),
        "state_path": str(manifest.parent / "state.json"),
    }


def _read_json(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def _write_json(path: str | Path, payload: dict[str, Any]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _result(
    status: str,
    payload: dict[str, Any],
    *,
    errors: tuple[str, ...] | list[str] = (),
    stop_reason: str = "",
) -> dict[str, Any]:
    return {
        "status": status,
        "stop_reason": stop_reason or status,
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
