from __future__ import annotations

import json
from pathlib import Path

from ai_orchestrator.codex_queue.plan_run_state import load_state
from ai_orchestrator.operator_panel.panel_actions import continue_run_action, recover_run_action, run_fake_steps_action
from codex_plan_helpers import write_plan


def test_panel_continue_action_updates_existing_run(tmp_path: Path) -> None:
    queue_root = tmp_path / "agent_tasks"
    plan_path = write_plan(queue_root / "plans" / "plan.json")
    run = run_fake_steps_action(plan_path, queue_root, max_steps=1)
    run_id = run["run_id"]

    continued = continue_run_action(run_id, queue_root, max_steps=1)
    state = load_state(continued["state_path"])

    assert continued["status"] == "max_steps"
    assert len(list(queue_root.glob("generated/test_plan/*/manifest.json"))) == 1
    assert state.completed_task_ids == ["TEST-TASK-001", "TEST-TASK-002"]


def test_panel_recover_action_reports_stale_lock_status(tmp_path: Path) -> None:
    queue_root = tmp_path / "agent_tasks"
    plan_path = write_plan(queue_root / "plans" / "plan.json")
    run = run_fake_steps_action(plan_path, queue_root, max_steps=1)
    lock_path = Path(run["payload"]["run_root"]) / "run.lock"
    lock_path.write_text(
        json.dumps({"created_at": "2000-01-01T00:00:00Z", "updated_at": "2000-01-01T00:00:00Z"}),
        encoding="utf-8",
    )

    result = recover_run_action(run["run_id"], queue_root)

    assert result["status"] == "blocked"
    assert result["lock_status"] == "stale"
    assert Path(result["recovery_report_paths"]["json"]).exists()
