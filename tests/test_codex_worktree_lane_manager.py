from __future__ import annotations

from ai_orchestrator.codex_queue.plan_contract import PlanContract
from ai_orchestrator.codex_queue.worktree_lane_manager import build_lane_plan, render_worktree_commands, validate_lane_isolation
from codex_plan_helpers import minimal_plan


def test_build_lane_plan_is_dry_run_safe() -> None:
    plan = PlanContract.from_dict(minimal_plan(2))

    lane_plan = build_lane_plan(plan)

    assert lane_plan.lanes[0].dry_run_only is True
    assert lane_plan.lanes[0].task_ids == ("TEST-TASK-001", "TEST-TASK-002")
    assert all("worktree add" in command for command in lane_plan.commands)
    assert not any("--force" in command for command in lane_plan.commands)


def test_validate_lane_isolation_reports_missing_roots() -> None:
    payload = minimal_plan(1)
    payload["execution_lanes"][0]["allowed_roots"] = []
    plan = PlanContract.from_dict(payload)

    lane_plan = build_lane_plan(plan)
    validation = validate_lane_isolation(lane_plan)

    assert validation["warnings"]
    assert render_worktree_commands(lane_plan)
