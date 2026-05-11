from __future__ import annotations

from ai_orchestrator.operator_panel.panel_renderer import render_dashboard_page, render_handoff_page, render_runs_page


def test_panel_renderer_returns_html_with_plan_and_run_status() -> None:
    data = {
        "plans": [{"path": "agent_tasks/plans/plan.json", "plan_id": "test_plan", "title": "Test", "task_count": 3, "version": "1"}],
        "runs": [{"run_id": "RUN1", "plan_id": "test_plan", "status": "running", "completed_count": 1, "task_count": 3, "blocked_count": 0, "failed_count": 0}],
        "active_run": {"run_id": "RUN1", "status": "running"},
        "dashboard": {"status": "running"},
        "git": {"branch": "master", "head": "abc"},
        "nightly_lane_batch": {
            "status": "dry_run",
            "ready": True,
            "task_count": 2,
            "completed_count": 2,
            "blocked_count": 0,
            "failed_count": 0,
            "latest_report_json": "agent_tasks/reports/latest_nightly_lane_batch_report.json",
        },
    }

    html = render_dashboard_page(data, repo_root=".", queue_root="agent_tasks")
    runs = render_runs_page(data["runs"], repo_root=".", queue_root="agent_tasks")
    handoff = render_handoff_page("prompt text", ["handoff.md"], repo_root=".", queue_root="agent_tasks")

    assert "<html" in html
    assert "test_plan" in html
    assert "Nightly batch" in html
    assert "latest_nightly_lane_batch_report.json" in html
    assert "RUN1" in runs
    assert "prompt text" in handoff
