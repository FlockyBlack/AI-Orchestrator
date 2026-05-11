from __future__ import annotations

from pathlib import Path

from ai_orchestrator.operator_panel.panel_app import route_get
from ai_orchestrator.operator_panel.panel_actions import run_fake_steps_action
from codex_plan_helpers import write_plan


def test_panel_dashboard_and_run_detail_show_active_run_and_tasks(tmp_path: Path) -> None:
    queue_root = tmp_path / "agent_tasks"
    plan_path = write_plan(queue_root / "plans" / "plan.json")
    run = run_fake_steps_action(plan_path, queue_root, max_steps=1)

    dashboard_html = route_get("/", "", tmp_path, queue_root)
    detail_html = route_get("/run", f"id={run['run_id']}", tmp_path, queue_root)

    assert run["run_id"] in dashboard_html
    assert "Active run" in dashboard_html
    assert "Tasks" in detail_html
    assert "TEST-TASK-001" in detail_html
    assert "Continue 1 step" in detail_html
    assert "Recover" in detail_html
