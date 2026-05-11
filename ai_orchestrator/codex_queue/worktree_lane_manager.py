from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from .plan_contract import PlanContract


@dataclass(frozen=True)
class WorktreeLane:
    lane_id: str
    task_ids: tuple[str, ...]
    allowed_roots: tuple[str, ...] = ()
    suggested_branch: str = ""
    suggested_worktree_path: str = ""
    dry_run_only: bool = True

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["task_ids"] = list(self.task_ids)
        payload["allowed_roots"] = list(self.allowed_roots)
        return payload


@dataclass(frozen=True)
class LanePlan:
    plan_id: str
    repo_root: str
    branch: str
    lanes: tuple[WorktreeLane, ...]
    errors: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    commands: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "repo_root": self.repo_root,
            "branch": self.branch,
            "lanes": [lane.to_dict() for lane in self.lanes],
            "errors": list(self.errors),
            "warnings": list(self.warnings),
            "commands": list(self.commands),
        }


def build_lane_plan(plan_contract: PlanContract) -> LanePlan:
    lane_meta = {lane.lane_id: lane for lane in plan_contract.execution_lanes}
    tasks_by_lane: dict[str, list[str]] = {}
    for task in plan_contract.tasks:
        tasks_by_lane.setdefault(task.execution_lane, []).append(task.task_id)

    lanes: list[WorktreeLane] = []
    repo_root = Path(plan_contract.repo_root or ".").resolve(strict=False)
    for lane_id in sorted(tasks_by_lane):
        meta = lane_meta.get(lane_id)
        safe_lane = _safe_lane_name(lane_id)
        lanes.append(
            WorktreeLane(
                lane_id=lane_id,
                task_ids=tuple(sorted(tasks_by_lane[lane_id])),
                allowed_roots=meta.allowed_roots if meta else (),
                suggested_branch=f"codex/{safe_lane}",
                suggested_worktree_path=str(repo_root.parent / "AI-Orchestrator-worktrees" / safe_lane),
                dry_run_only=True,
            )
        )
    plan = LanePlan(
        plan_id=plan_contract.plan_id,
        repo_root=str(repo_root),
        branch=plan_contract.branch,
        lanes=tuple(lanes),
    )
    validation = validate_lane_isolation(plan)
    commands = tuple(render_worktree_commands(plan))
    return LanePlan(
        plan_id=plan.plan_id,
        repo_root=plan.repo_root,
        branch=plan.branch,
        lanes=plan.lanes,
        errors=tuple(validation["errors"]),
        warnings=tuple(validation["warnings"]),
        commands=commands,
    )


def validate_lane_isolation(lane_plan: LanePlan) -> dict[str, list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    for lane in lane_plan.lanes:
        if not lane.lane_id:
            errors.append("lane_id must not be empty")
        if not lane.task_ids:
            warnings.append(f"lane {lane.lane_id} has no tasks")
        if not lane.allowed_roots:
            warnings.append(f"lane {lane.lane_id} has no allowed_roots metadata")
        if ".git" in lane.suggested_worktree_path.replace("\\", "/"):
            errors.append(f"lane {lane.lane_id} suggested worktree path points inside .git")
    return {"errors": errors, "warnings": warnings}


def render_worktree_commands(lane_plan: LanePlan) -> list[str]:
    commands: list[str] = []
    for lane in lane_plan.lanes:
        commands.append(
            "git worktree add "
            f'"{lane.suggested_worktree_path}" '
            f'-b "{lane.suggested_branch}" '
            f'"{lane_plan.branch or "master"}"'
        )
    return commands


def _safe_lane_name(lane_id: str) -> str:
    value = "".join(ch.lower() if ch.isalnum() else "-" for ch in lane_id)
    while "--" in value:
        value = value.replace("--", "-")
    return value.strip("-") or "lane"
