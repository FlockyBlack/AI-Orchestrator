from __future__ import annotations

from pathlib import Path

from ai_orchestrator.symphony_adapter.symphony_task_contract import SymphonyTask
from ai_orchestrator.symphony_adapter.symphony_workspace_plan import (
    build_workspace_plan_for_task,
    render_workspace_setup_commands,
    validate_workspace_plan,
)


def test_workspace_plan_validates_and_preserves_git_metadata(tmp_path: Path) -> None:
    task = SymphonyTask(
        task_id="TEST-TASK-001",
        title="Task",
        description="Safe task.",
        source_plan_id="plan",
        source_run_id="run",
    )
    plan = build_workspace_plan_for_task(task, Path.cwd(), tmp_path / "workspaces")
    validation = validate_workspace_plan(plan)

    assert validation["valid"] is True
    assert plan.dry_run_only is True
    assert plan.worktree_created is False
    assert plan.branch_name.startswith("codex/")
    assert plan.base_head


def test_workspace_commands_are_dry_run_safe(tmp_path: Path) -> None:
    task = SymphonyTask(
        task_id="TEST-TASK-002",
        title="Task",
        description="Safe task.",
        source_plan_id="plan",
        source_run_id="run",
    )
    plan = build_workspace_plan_for_task(task, Path.cwd(), tmp_path / "workspaces")
    commands = render_workspace_setup_commands(plan)
    joined = "\n".join(commands).lower()

    assert "git worktree add" not in joined
    assert "git add ." not in joined
    assert "git push --force" not in joined
    assert "dry run" in joined
