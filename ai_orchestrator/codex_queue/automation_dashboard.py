from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .plan_contract import PlanContract
from .plan_decomposer import get_next_runnable_tasks
from .plan_run_state import PlanRunState, summarize_state


def build_dashboard(state: PlanRunState, plan: PlanContract, output_dir: str | Path) -> dict[str, Any]:
    next_tasks = get_next_runnable_tasks(
        plan.tasks,
        completed=state.completed_task_ids,
        blocked=state.blocked_task_ids,
        failed=state.failed_task_ids,
    )
    lane_summary: dict[str, dict[str, Any]] = {}
    for task in plan.tasks:
        lane = lane_summary.setdefault(task.execution_lane, {"task_count": 0, "completed": 0, "blocked": 0, "failed": 0})
        lane["task_count"] += 1
        if task.task_id in state.completed_task_ids:
            lane["completed"] += 1
        if task.task_id in state.blocked_task_ids:
            lane["blocked"] += 1
        if task.task_id in state.failed_task_ids:
            lane["failed"] += 1

    summary = summarize_state(state)
    if len(state.completed_task_ids) == len(plan.tasks):
        status = "done"
    else:
        status = summary["status"]
    dashboard = {
        "schema_version": "codex_automation_dashboard.v1",
        "plan_id": plan.plan_id,
        "run_id": state.run_id,
        "mode": plan.mode,
        "status": status,
        "counts": {
            "completed": len(state.completed_task_ids),
            "blocked": len(state.blocked_task_ids),
            "failed": len(state.failed_task_ids),
            "skipped": len(state.skipped_task_ids),
            "total": len(plan.tasks),
        },
        "current_task": state.current_task_id,
        "next_runnable_tasks": [task.task_id for task in next_tasks[:10]],
        "retry_counts": dict(state.retry_counts),
        "lane_summary": lane_summary,
        "safety_status": "ok" if not state.failed_task_ids else "review_failed_tasks",
        "last_git_verification": state.git_head_last_verified,
        "artifact_paths": list(state.artifact_paths),
        "dashboard_paths": {
            "json": str(Path(output_dir) / "dashboard.json"),
            "markdown": str(Path(output_dir) / "dashboard.md"),
        },
        "next_operator_action": _next_operator_action(status, next_tasks),
        "recent_events": state.events[-10:],
    }
    write_dashboard_json(dashboard, Path(output_dir) / "dashboard.json")
    write_dashboard_markdown(dashboard, Path(output_dir) / "dashboard.md")
    for path in dashboard["dashboard_paths"].values():
        if path not in state.dashboard_paths:
            state.dashboard_paths.append(path)
    return dashboard


def write_dashboard_json(dashboard: dict[str, Any], path: str | Path) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(dashboard, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return target


def write_dashboard_markdown(dashboard: dict[str, Any], path: str | Path) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(_render_markdown(dashboard), encoding="utf-8")
    return target


def _render_markdown(dashboard: dict[str, Any]) -> str:
    lines = [
        f"# Automation Dashboard: {dashboard['plan_id']}",
        "",
        f"- run_id: `{dashboard['run_id']}`",
        f"- mode: `{dashboard['mode']}`",
        f"- status: `{dashboard['status']}`",
        f"- current_task: `{dashboard['current_task']}`",
        f"- safety_status: `{dashboard['safety_status']}`",
        f"- last_git_verification: `{dashboard['last_git_verification']}`",
        "",
        "## Counts",
        "",
    ]
    for key, value in dashboard["counts"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Next Runnable Tasks", ""])
    next_tasks = dashboard.get("next_runnable_tasks") or []
    lines.extend(f"- `{task_id}`" for task_id in next_tasks) if next_tasks else lines.append("- None")
    lines.extend(["", "## Lanes", ""])
    for lane_id, lane in dashboard["lane_summary"].items():
        lines.append(
            f"- `{lane_id}`: {lane['completed']}/{lane['task_count']} completed, "
            f"{lane['blocked']} blocked, {lane['failed']} failed"
        )
    lines.extend(["", "## Artifacts", ""])
    artifacts = dashboard.get("artifact_paths") or []
    lines.extend(f"- `{path}`" for path in artifacts) if artifacts else lines.append("- None")
    lines.extend(["", "## Next Operator Action", "", str(dashboard["next_operator_action"]), ""])
    return "\n".join(lines)


def _next_operator_action(status: str, next_tasks: list[Any]) -> str:
    if status == "done":
        return "Review artifacts, validation, and selective commit/push decision."
    if status == "blocked":
        return "Inspect blocked tasks and run recover-plan or export a handoff prompt."
    if status == "failed":
        return "Inspect failed tasks and decide retry or recovery."
    if next_tasks:
        return f"Continue with next task {next_tasks[0].task_id} or export a Codex handoff prompt."
    return "Inspect state; no runnable task is available."
