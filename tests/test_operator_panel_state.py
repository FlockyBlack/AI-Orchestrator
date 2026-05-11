from __future__ import annotations

from pathlib import Path

from ai_orchestrator.codex_queue.long_run_controller import LongRunController
from ai_orchestrator.operator_panel.panel_state import discover_plans, discover_runs, load_panel_state, save_panel_state, summarize_active_run
from codex_plan_helpers import write_plan


def test_panel_state_discovers_plans_and_runs(tmp_path: Path) -> None:
    queue_root = tmp_path / "agent_tasks"
    plan_path = write_plan(queue_root / "plans" / "plan.json")
    LongRunController(repo_root=tmp_path).run_plan(plan_path, queue_root, max_steps=1, executor="fake")

    plans = discover_plans(queue_root)
    runs = discover_runs(queue_root)
    state = load_panel_state(queue_root)
    state.active_run_id = runs[0]["run_id"]
    save_panel_state(state, queue_root)

    assert plans[0]["plan_id"] == "test_plan"
    assert runs[0]["task_count"] == 3
    assert summarize_active_run(queue_root)["status"] == "found"
