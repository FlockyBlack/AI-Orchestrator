from __future__ import annotations

from pathlib import Path

from ai_orchestrator.codex_queue.automation_dashboard import build_dashboard
from ai_orchestrator.codex_queue.plan_contract import PlanContract
from ai_orchestrator.codex_queue.plan_run_state import PlanRunState, mark_task_done
from codex_plan_helpers import minimal_plan


def test_dashboard_json_and_markdown_created(tmp_path: Path) -> None:
    plan = PlanContract.from_dict(minimal_plan(2))
    state = PlanRunState.create("RUN1", plan.plan_id)
    mark_task_done(state, "TEST-TASK-001", artifact_paths=["artifact.json"])

    dashboard = build_dashboard(state, plan, tmp_path / "dashboard")

    assert dashboard["counts"]["completed"] == 1
    assert dashboard["next_runnable_tasks"] == ["TEST-TASK-002"]
    assert (tmp_path / "dashboard" / "dashboard.json").exists()
    assert (tmp_path / "dashboard" / "dashboard.md").exists()
