from __future__ import annotations

from pathlib import Path

from ai_orchestrator.codex_queue.plan_recovery import inspect_run, recover_run
from ai_orchestrator.codex_queue.plan_run_state import PlanRunState, mark_task_done, save_state
from ai_orchestrator.codex_queue.plan_to_queue import create_queue_from_plan
from codex_plan_helpers import write_plan


def test_recovery_report_identifies_incomplete_tasks(tmp_path: Path) -> None:
    plan_path = write_plan(tmp_path / "plan.json")
    queue_root = tmp_path / "agent_tasks"
    queue = create_queue_from_plan(plan_path, queue_root, run_id="RUN1")
    state = PlanRunState.create("RUN1", "test_plan", queue_manifest_path=queue.queue_paths["manifest"])
    mark_task_done(state, "TEST-TASK-001")
    save_state(state, Path(queue.queue_paths["run_root"]) / "state.json")

    inspection = inspect_run("RUN1", queue_root)
    recovery = recover_run("RUN1", queue_root)

    assert inspection["status"] == "found"
    assert recovery["status"] == "recovered"
    assert "TEST-TASK-002" in recovery["incomplete_task_ids"]
    assert Path(recovery["recovery_report_paths"]["json"]).exists()


def test_recovery_blocks_missing_run(tmp_path: Path) -> None:
    recovery = recover_run("MISSING", tmp_path / "agent_tasks")

    assert recovery["status"] == "missing"
    assert recovery["errors"]
