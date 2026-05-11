from __future__ import annotations

from pathlib import Path

from ai_orchestrator.codex_queue.long_run_controller import LongRunController
from ai_orchestrator.codex_queue.plan_run_state import load_state
from codex_plan_helpers import minimal_plan, write_plan


def test_continue_plan_continues_existing_run_without_duplicate_and_does_not_rerun_completed(tmp_path: Path) -> None:
    plan_path = write_plan(tmp_path / "plan.json", minimal_plan(5))
    queue_root = tmp_path / "agent_tasks"
    controller = LongRunController(repo_root=tmp_path)

    first = controller.run_plan(plan_path, queue_root, run_id="RUN1", max_steps=2, executor="fake")
    second = controller.continue_plan("RUN1", queue_root, max_steps=2, executor="fake")
    state = load_state(first["state_path"])

    assert first["status"] == "max_steps"
    assert second["status"] == "max_steps"
    assert len(list(queue_root.glob("generated/test_plan/*/manifest.json"))) == 1
    assert state.task_states["TEST-TASK-001"].attempts == 1
    assert len(state.completed_task_ids) == 4


def test_fake_blocked_task_stops_run(tmp_path: Path) -> None:
    plan = minimal_plan(2)
    plan["tasks"][1]["fake_behavior"] = "blocked"
    plan_path = write_plan(tmp_path / "plan.json", plan)

    result = LongRunController(repo_root=tmp_path).run_plan(plan_path, tmp_path / "agent_tasks", max_steps=3)

    assert result["status"] == "blocked"
    assert result["blocked_task_ids"] == ["TEST-TASK-002"]


def test_fake_failed_task_records_failure(tmp_path: Path) -> None:
    plan = minimal_plan(1)
    plan["tasks"][0]["fake_behavior"] = "failed"
    plan_path = write_plan(tmp_path / "plan.json", plan)

    result = LongRunController(repo_root=tmp_path).run_plan(plan_path, tmp_path / "agent_tasks", max_steps=1)

    assert result["status"] == "failed"
    assert result["failed_task_ids"] == ["TEST-TASK-001"]


def test_fake_needs_retry_increments_and_retry_exceeded_blocks(tmp_path: Path) -> None:
    plan = minimal_plan(1)
    plan["tasks"][0]["fake_behavior"] = "needs_retry"
    plan["tasks"][0]["max_retries"] = 1
    plan_path = write_plan(tmp_path / "plan.json", plan)
    queue_root = tmp_path / "agent_tasks"
    controller = LongRunController(repo_root=tmp_path)

    first = controller.run_plan(plan_path, queue_root, run_id="RUN1", max_steps=1)
    second = controller.continue_plan("RUN1", queue_root, max_steps=1)

    assert first["status"] == "needs_retry"
    assert second["status"] == "blocked"
    assert second["blocked_task_ids"] == ["TEST-TASK-001"]
