from __future__ import annotations

from pathlib import Path

from ai_orchestrator.operator_panel.panel_actions import (
    create_queue_action,
    export_next_codex_prompt_action,
    recover_run_action,
    run_fake_steps_action,
    validate_plan_action,
)
from codex_plan_helpers import write_plan


def test_panel_action_validates_plan_and_creates_queue(tmp_path: Path) -> None:
    queue_root = tmp_path / "agent_tasks"
    plan_path = write_plan(queue_root / "plans" / "plan.json")

    validation = validate_plan_action(plan_path)
    queue = create_queue_action(plan_path, queue_root)

    assert validation["status"] == "ok"
    assert queue["status"] == "created"
    assert Path(queue["queue_paths"]["manifest"]).exists()


def test_panel_action_runs_fake_steps_and_exports_handoff(tmp_path: Path) -> None:
    queue_root = tmp_path / "agent_tasks"
    plan_path = write_plan(queue_root / "plans" / "plan.json")

    run_result = run_fake_steps_action(plan_path, queue_root, max_steps=1)
    run_id = run_result["payload"]["run_id"]
    handoff = export_next_codex_prompt_action(run_id, queue_root)
    recovery = recover_run_action(run_id, queue_root)

    assert run_result["status"] == "max_steps"
    assert handoff["status"] == "requiring_operator_handoff"
    assert recovery["status"] in {"recovered", "blocked"}
    assert list(queue_root.glob("generated/*/*/handoff/*_codex_prompt.md"))
