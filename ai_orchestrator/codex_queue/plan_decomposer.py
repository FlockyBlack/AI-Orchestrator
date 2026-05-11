from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Iterable

from .plan_contract import PlanContract, PlanTaskSpec


@dataclass(frozen=True)
class DecompositionResult:
    plan_id: str
    ordered_tasks: tuple[PlanTaskSpec, ...]
    task_count: int
    cycles: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()

    def to_dict(self) -> dict:
        return {
            "plan_id": self.plan_id,
            "ordered_tasks": [task.to_dict() for task in self.ordered_tasks],
            "task_count": self.task_count,
            "cycles": list(self.cycles),
            "errors": list(self.errors),
            "warnings": list(self.warnings),
        }


def decompose_plan(plan_contract: PlanContract) -> DecompositionResult:
    cycles = tuple(detect_dependency_cycles(plan_contract.tasks))
    errors = tuple(cycles)
    ordered = tuple() if cycles else tuple(topological_sort_tasks(plan_contract.tasks))
    return DecompositionResult(
        plan_id=plan_contract.plan_id,
        ordered_tasks=ordered,
        task_count=len(plan_contract.tasks),
        cycles=cycles,
        errors=errors,
        warnings=(),
    )


def topological_sort_tasks(tasks: Iterable[PlanTaskSpec]) -> list[PlanTaskSpec]:
    task_by_id = {task.task_id: task for task in tasks}
    completed: set[str] = set()
    ordered: list[PlanTaskSpec] = []

    while len(ordered) < len(task_by_id):
        runnable = [
            task
            for task in task_by_id.values()
            if task.task_id not in completed and all(dependency in completed for dependency in task.dependencies)
        ]
        if not runnable:
            raise ValueError("dependency cycle detected")
        for task in sorted(runnable, key=lambda item: item.task_id):
            completed.add(task.task_id)
            ordered.append(task)
    return ordered


def detect_dependency_cycles(tasks: Iterable[PlanTaskSpec]) -> list[str]:
    task_by_id = {task.task_id: task for task in tasks}
    visiting: set[str] = set()
    visited: set[str] = set()
    cycles: list[str] = []

    def visit(task_id: str, path: list[str]) -> None:
        if task_id in visited:
            return
        if task_id in visiting:
            start = path.index(task_id) if task_id in path else 0
            cycles.append(" -> ".join(path[start:] + [task_id]))
            return
        visiting.add(task_id)
        for dependency in sorted(task_by_id[task_id].dependencies):
            if dependency in task_by_id:
                visit(dependency, path + [dependency])
        visiting.remove(task_id)
        visited.add(task_id)

    for task_id in sorted(task_by_id):
        visit(task_id, [task_id])
    return cycles


def get_next_runnable_tasks(
    tasks: Iterable[PlanTaskSpec],
    completed: Iterable[str],
    blocked: Iterable[str],
    failed: Iterable[str],
) -> list[PlanTaskSpec]:
    completed_set = set(completed)
    blocked_set = set(blocked)
    failed_set = set(failed)
    excluded = completed_set | blocked_set | failed_set
    ordered = topological_sort_tasks(tasks)
    return [
        task
        for task in ordered
        if task.task_id not in excluded and all(dependency in completed_set for dependency in task.dependencies)
    ]


def serialize_task_for_queue(task: PlanTaskSpec, plan_id: str, run_id: str) -> dict:
    payload = asdict(task)
    payload["dependencies"] = list(task.dependencies)
    payload["allowed_paths"] = list(task.allowed_paths)
    payload["forbidden_actions"] = list(task.forbidden_actions)
    payload["acceptance_gates"] = list(task.acceptance_gates)
    payload["expected_artifacts"] = list(task.expected_artifacts)
    payload["plan_id"] = plan_id
    payload["run_id"] = run_id
    payload["schema_version"] = "codex_plan_task.v1"
    return payload
