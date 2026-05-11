from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol

from .plan_contract import PlanContract, PlanTaskSpec


@dataclass(frozen=True)
class TaskExecutionContext:
    task_spec: PlanTaskSpec
    plan: PlanContract
    queue_root: str | Path
    run_id: str
    plan_id: str
    repo_root: str | Path
    run_dir: str | Path


@dataclass(frozen=True)
class TaskExecutionResult:
    status: str
    result_payload: dict[str, Any]
    artifact_paths: tuple[str, ...] = ()
    message: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "result_payload": self.result_payload,
            "artifact_paths": list(self.artifact_paths),
            "message": self.message,
        }


class TaskExecutor(Protocol):
    def execute(self, context: TaskExecutionContext) -> TaskExecutionResult:
        ...


@dataclass
class FakeTaskExecutor:
    blocked_task_ids: set[str] = field(default_factory=set)
    failed_task_ids: set[str] = field(default_factory=set)

    def execute(self, context: TaskExecutionContext) -> TaskExecutionResult:
        task = context.task_spec
        artifact_dir = Path(context.run_dir) / "artifacts"
        artifact_path = artifact_dir / f"{task.task_id}_fake_result.json"
        if task.task_id in self.blocked_task_ids:
            payload = _base_payload(task, context, status="blocked")
            payload["validation_passed"] = False
            payload["blocked_reason"] = "Injected fake blocker for test coverage."
            _write_json(artifact_path, payload)
            return TaskExecutionResult("blocked", payload, (str(artifact_path),), "fake task blocked")
        if task.task_id in self.failed_task_ids:
            payload = _base_payload(task, context, status="failed")
            payload["validation_passed"] = False
            payload["safety_ok"] = True
            payload["failure_reason"] = "Injected fake failure for test coverage."
            _write_json(artifact_path, payload)
            return TaskExecutionResult("failed", payload, (str(artifact_path),), "fake task failed")

        payload = _base_payload(task, context, status="completed")
        payload.update(
            {
                "validation_passed": True,
                "safety_ok": True,
                "artifacts": [str(artifact_path)],
                "commands_run": [],
                "fake_executor": True,
                "safety_boundaries_acknowledged": [
                    boundary.boundary_id for boundary in context.plan.safety_boundaries if boundary.required
                ],
                "real_order_submitted": False,
                "wallet_used": False,
                "trading_endpoint_used": False,
                "openrouter_used": False,
                "polymarket_api_used": False,
                "unsafe_git_staging_used": False,
                "force_push_used": False,
            }
        )
        _write_json(artifact_path, payload)
        return TaskExecutionResult("completed", payload, (str(artifact_path),), "fake task completed")


class LocalNoopExecutor:
    def execute(self, context: TaskExecutionContext) -> TaskExecutionResult:
        payload = _base_payload(context.task_spec, context, status="completed")
        payload.update(
            {
                "validation_passed": True,
                "safety_ok": True,
                "artifacts": [],
                "commands_run": [],
                "noop_executor": True,
                "safety_boundaries_acknowledged": [
                    boundary.boundary_id for boundary in context.plan.safety_boundaries if boundary.required
                ],
            }
        )
        return TaskExecutionResult("completed", payload, (), "noop task completed")


class CodexHandoffExecutor:
    def execute(self, context: TaskExecutionContext) -> TaskExecutionResult:
        task = context.task_spec
        handoff_dir = Path(context.run_dir) / "handoff"
        handoff_path = handoff_dir / f"{task.task_id}_codex_prompt.md"
        prompt = render_codex_handoff_prompt(context)
        handoff_path.parent.mkdir(parents=True, exist_ok=True)
        handoff_path.write_text(prompt, encoding="utf-8")
        payload = _base_payload(task, context, status="requiring_operator_handoff")
        payload.update(
            {
                "validation_passed": True,
                "safety_ok": True,
                "artifacts": [str(handoff_path)],
                "handoff_prompt_path": str(handoff_path),
                "commands_run": [],
                "codex_invoked": False,
                "safety_boundaries_acknowledged": [
                    boundary.boundary_id for boundary in context.plan.safety_boundaries if boundary.required
                ],
            }
        )
        return TaskExecutionResult(
            "requiring_operator_handoff",
            payload,
            (str(handoff_path),),
            "Codex handoff prompt generated; Codex was not invoked.",
        )


class FutureCodexCliExecutor:
    def execute(self, context: TaskExecutionContext) -> TaskExecutionResult:
        raise NotImplementedError(
            "FutureCodexCliExecutor is a boundary stub only. This task must not self-invoke Codex."
        )


class FutureCodexAppAutomationExecutor:
    def execute(self, context: TaskExecutionContext) -> TaskExecutionResult:
        raise NotImplementedError(
            "FutureCodexAppAutomationExecutor is a boundary stub only. No Codex App automation is registered here."
        )


def render_codex_handoff_prompt(context: TaskExecutionContext) -> str:
    task = context.task_spec
    result_shape = {
        "task_id": task.task_id,
        "status": "completed|blocked|failed",
        "validation_passed": True,
        "safety_ok": True,
        "artifacts": [],
        "commands_run": [],
        "summary": "",
        "remaining_risks": [],
    }
    lines = [
        f"# Codex Handoff: {task.task_id}",
        "",
        f"- task_id: `{task.task_id}`",
        f"- repo_root: `{context.repo_root}`",
        f"- branch: `{context.plan.branch}`",
        f"- expected_current_head: `{context.plan.expected_head}`",
        f"- execution_lane: `{task.execution_lane}`",
        "",
        "## Task",
        "",
        task.description,
        "",
        "## Allowed Paths",
        "",
        *_bullet_lines(task.allowed_paths),
        "",
        "## Forbidden Actions",
        "",
        *_bullet_lines(task.forbidden_actions),
        "",
        "## Expected Artifacts",
        "",
        *_bullet_lines(task.expected_artifacts),
        "",
        "## Acceptance Gates",
        "",
        *_bullet_lines(task.acceptance_gates),
        "",
        "## Required Result JSON Shape",
        "",
        "```json",
        json.dumps(result_shape, indent=2, sort_keys=True),
        "```",
        "",
        "## Safety Reminders",
        "",
        "- Do not use unsafe git staging. Never run `git add .`, `git add -A`, or `git add --all`.",
        "- Do not use wallet files, private keys, signing, orders, trading endpoints, or real-money flows.",
        "- Do not use OpenRouter or Polymarket API unless a separate task explicitly approves it.",
        "- Do not start daemons, schedulers, uncontrolled background workers, or browser automation.",
        "",
    ]
    return "\n".join(lines)


def _base_payload(task: PlanTaskSpec, context: TaskExecutionContext, *, status: str) -> dict[str, Any]:
    return {
        "schema_version": "codex_plan_task_result.v1",
        "task_id": task.task_id,
        "plan_id": context.plan_id,
        "run_id": context.run_id,
        "status": status,
        "completed_at": _utc_iso(),
        "summary": f"{status} by local executor for {task.task_id}.",
    }


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _bullet_lines(values: tuple[str, ...] | list[str]) -> list[str]:
    if not values:
        return ["- None"]
    return [f"- {value}" for value in values]


def _utc_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
