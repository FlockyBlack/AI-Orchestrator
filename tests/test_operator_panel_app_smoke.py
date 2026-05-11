from __future__ import annotations

from pathlib import Path

from ai_orchestrator.operator_panel.panel_app import make_handler, route_get, route_post
from codex_plan_helpers import write_plan


def test_panel_app_routes_render_without_long_running_server(tmp_path: Path) -> None:
    queue_root = tmp_path / "agent_tasks"
    plan_path = write_plan(queue_root / "plans" / "plan.json")

    handler = make_handler(tmp_path, queue_root)
    home = route_get("/", "", tmp_path, queue_root)
    plans = route_get("/plans", "", tmp_path, queue_root)
    result = route_post("/actions/validate-plan", {"plan_file": str(plan_path)}, tmp_path, queue_root)

    assert handler.__name__ == "OperatorPanelHandler"
    assert "Operator Panel" in home
    assert "test_plan" in plans
    assert result["status"] == "ok"
