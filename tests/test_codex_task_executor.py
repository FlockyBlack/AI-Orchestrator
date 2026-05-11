from __future__ import annotations

from pathlib import Path

from ai_orchestrator.codex_queue.plan_contract import PlanContract
from ai_orchestrator.codex_queue.task_executor import (
    CodexHandoffExecutor,
    FakeTaskExecutor,
    FutureCodexAppAutomationExecutor,
    FutureCodexCliExecutor,
    TaskExecutionContext,
)
from codex_plan_helpers import minimal_plan


def _context(tmp_path: Path) -> TaskExecutionContext:
    plan = PlanContract.from_dict(minimal_plan(1))
    return TaskExecutionContext(
        task_spec=plan.tasks[0],
        plan=plan,
        queue_root=tmp_path / "agent_tasks",
        run_id="RUN1",
        plan_id=plan.plan_id,
        repo_root=tmp_path,
        run_dir=tmp_path / "agent_tasks" / "generated" / plan.plan_id / "RUN1",
    )


def test_fake_executor_writes_safe_artifact(tmp_path: Path) -> None:
    result = FakeTaskExecutor().execute(_context(tmp_path))

    assert result.status == "completed"
    assert result.result_payload["validation_passed"] is True
    assert Path(result.artifact_paths[0]).exists()


def test_fake_executor_supports_blocked_behavior(tmp_path: Path) -> None:
    context = _context(tmp_path)
    result = FakeTaskExecutor(blocked_task_ids={context.task_spec.task_id}).execute(context)

    assert result.status == "blocked"
    assert result.result_payload["status"] == "blocked"


def test_handoff_executor_creates_prompt_without_invoking_codex(tmp_path: Path) -> None:
    result = CodexHandoffExecutor().execute(_context(tmp_path))
    prompt = Path(result.artifact_paths[0]).read_text(encoding="utf-8")

    assert result.status == "requiring_operator_handoff"
    assert "Do not use unsafe git staging" in prompt
    assert "Codex" in prompt


def test_future_executors_raise_not_implemented(tmp_path: Path) -> None:
    context = _context(tmp_path)
    for executor in (FutureCodexCliExecutor(), FutureCodexAppAutomationExecutor()):
        try:
            executor.execute(context)
        except NotImplementedError:
            pass
        else:
            raise AssertionError("future executor must remain a stub")
