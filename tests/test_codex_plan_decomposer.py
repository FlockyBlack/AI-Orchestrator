from __future__ import annotations

from ai_orchestrator.codex_queue.plan_contract import PlanContract
from ai_orchestrator.codex_queue.plan_decomposer import (
    decompose_plan,
    detect_dependency_cycles,
    get_next_runnable_tasks,
    topological_sort_tasks,
)
from codex_plan_helpers import minimal_plan


def test_topological_sort_is_deterministic() -> None:
    plan = PlanContract.from_dict(minimal_plan(3))

    ordered = topological_sort_tasks(reversed(plan.tasks))

    assert [task.task_id for task in ordered] == ["TEST-TASK-001", "TEST-TASK-002", "TEST-TASK-003"]


def test_detect_dependency_cycles() -> None:
    payload = minimal_plan(2)
    payload["tasks"][0]["dependencies"] = ["TEST-TASK-002"]
    plan = PlanContract.from_dict(payload)

    cycles = detect_dependency_cycles(plan.tasks)

    assert cycles


def test_get_next_runnable_tasks_respects_completed_blocked_failed() -> None:
    plan = PlanContract.from_dict(minimal_plan(3))

    next_tasks = get_next_runnable_tasks(
        plan.tasks,
        completed=["TEST-TASK-001"],
        blocked=[],
        failed=[],
    )

    assert [task.task_id for task in next_tasks] == ["TEST-TASK-002"]


def test_decompose_plan_preserves_metadata() -> None:
    plan = PlanContract.from_dict(minimal_plan(2))

    result = decompose_plan(plan)

    assert not result.errors
    assert result.ordered_tasks[0].execution_lane == "lane_a"
    assert result.ordered_tasks[0].allowed_paths == ("docs/", "tests/")
