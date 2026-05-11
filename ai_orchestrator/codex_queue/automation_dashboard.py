from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from .plan_contract import PlanContract
from .plan_decomposer import get_next_runnable_tasks
from .plan_run_state import PlanRunState, summarize_state, validate_state_consistency
from .plan_to_queue import validate_queue_manifest


def build_dashboard(state: PlanRunState, plan: PlanContract, output_dir: str | Path) -> dict[str, Any]:
    next_tasks = get_next_runnable_tasks(
        plan.tasks,
        completed=state.completed_task_ids,
        blocked=state.blocked_task_ids,
        failed=state.failed_task_ids,
    )
    lane_summary: dict[str, dict[str, Any]] = {}
    task_details: list[dict[str, Any]] = []
    for task in plan.tasks:
        lane = lane_summary.setdefault(task.execution_lane, {"task_count": 0, "completed": 0, "blocked": 0, "failed": 0})
        lane["task_count"] += 1
        status = _task_status(state, task.task_id)
        if status == "completed":
            lane["completed"] += 1
        if status == "blocked":
            lane["blocked"] += 1
        if status == "failed":
            lane["failed"] += 1
        task_state = state.task_states.get(task.task_id)
        task_details.append(
            {
                "task_id": task.task_id,
                "title": task.title,
                "status": status,
                "dependencies": list(task.dependencies),
                "retry_count": int(state.retry_counts.get(task.task_id, 0)),
                "max_retries": task.max_retries,
                "artifact_paths": list(task_state.artifact_paths) if task_state else [],
                "last_event": task_state.last_event if task_state else "",
            }
        )

    summary = summarize_state(state)
    completed_count = len(state.completed_task_ids)
    blocked_count = len(state.blocked_task_ids)
    failed_count = len(state.failed_task_ids)
    skipped_count = len(state.skipped_task_ids)
    total_count = len(plan.tasks)
    pending_count = max(0, total_count - completed_count - blocked_count - failed_count - skipped_count)
    lifecycle_status = "completed" if total_count and completed_count == total_count else state.status
    consistency = validate_state_consistency(state, plan)
    manifest = _read_json(state.queue_manifest_path) if state.queue_manifest_path else {}
    manifest_validation = validate_queue_manifest(manifest) if manifest else {"valid": False, "status": "missing", "errors": ["manifest missing"], "warnings": []}
    latest_artifacts = list(state.artifact_paths[-20:])
    dashboard = {
        "schema_version": "codex_automation_dashboard.v2",
        "plan_id": plan.plan_id,
        "run_id": state.run_id,
        "mode": plan.mode,
        "status": "done" if lifecycle_status == "completed" else lifecycle_status,
        "run_lifecycle_status": lifecycle_status,
        "queue_manifest_status": manifest_validation["status"],
        "state_consistency_status": consistency["status"],
        "state_consistency": consistency,
        "counts": {
            "completed": completed_count,
            "blocked": blocked_count,
            "failed": failed_count,
            "skipped": skipped_count,
            "pending": pending_count,
            "total": total_count,
        },
        "current_task": state.current_task_id,
        "next_runnable_tasks": [task.task_id for task in next_tasks[:10]],
        "blocked_details": _terminal_details(state, "blocked"),
        "failed_details": _terminal_details(state, "failed"),
        "retry_counts": dict(state.retry_counts),
        "retry_summary": [
            {
                "task_id": task.task_id,
                "retry_count": int(state.retry_counts.get(task.task_id, 0)),
                "max_retries": task.max_retries,
            }
            for task in plan.tasks
            if state.retry_counts.get(task.task_id)
        ],
        "checkpoints": list(state.checkpoints[-10:]),
        "latest_checkpoint": state.checkpoints[-1] if state.checkpoints else None,
        "lane_summary": lane_summary,
        "task_details": task_details,
        "safety_status": "ok" if not failed_count and consistency["consistent"] else "review_required",
        "last_git_verification": state.git_head_last_verified,
        "git_summary": _git_summary(plan.repo_root or "."),
        "artifact_paths": list(state.artifact_paths),
        "latest_artifacts": latest_artifacts,
        "latest_handoff_prompt_path": state.latest_handoff_prompt_path,
        "latest_recovery_report_path": state.latest_recovery_report_path,
        "dashboard_paths": {
            "json": str(Path(output_dir) / "dashboard.json"),
            "markdown": str(Path(output_dir) / "dashboard.md"),
        },
        "next_operator_action": _next_operator_action(lifecycle_status, next_tasks, consistency),
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
        "## Status Summary",
        "",
        f"- run_id: `{dashboard['run_id']}`",
        f"- mode: `{dashboard['mode']}`",
        f"- run_lifecycle_status: `{dashboard['run_lifecycle_status']}`",
        f"- queue_manifest_status: `{dashboard['queue_manifest_status']}`",
        f"- state_consistency_status: `{dashboard['state_consistency_status']}`",
        f"- current_task: `{dashboard['current_task']}`",
        f"- safety_status: `{dashboard['safety_status']}`",
        f"- branch: `{dashboard.get('git_summary', {}).get('branch', '')}`",
        f"- head: `{dashboard.get('git_summary', {}).get('head', '')}`",
        "",
        "## Task Counts",
        "",
    ]
    for key, value in dashboard["counts"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Current/Next Tasks", ""])
    lines.append(f"- current: `{dashboard.get('current_task') or 'none'}`")
    next_tasks = dashboard.get("next_runnable_tasks") or []
    lines.extend(f"- next: `{task_id}`" for task_id in next_tasks) if next_tasks else lines.append("- next: `none`")
    lines.extend(["", "## Blockers/Failures", ""])
    blockers = dashboard.get("blocked_details") or []
    failures = dashboard.get("failed_details") or []
    if blockers or failures:
        for item in blockers:
            lines.append(f"- blocked `{item['task_id']}`: {item.get('errors') or 'review required'}")
        for item in failures:
            lines.append(f"- failed `{item['task_id']}`: {item.get('errors') or 'review required'}")
    else:
        lines.append("- None")
    lines.extend(["", "## Recovery Notes", ""])
    latest_checkpoint = dashboard.get("latest_checkpoint") or {}
    lines.append(f"- latest_checkpoint: `{latest_checkpoint.get('checkpoint_id', 'none')}`")
    lines.append(f"- latest_recovery_report: `{dashboard.get('latest_recovery_report_path') or 'none'}`")
    if dashboard.get("state_consistency", {}).get("errors"):
        for error in dashboard["state_consistency"]["errors"]:
            lines.append(f"- consistency_error: {error}")
    lines.extend(["", "## Artifacts", ""])
    artifacts = dashboard.get("latest_artifacts") or []
    lines.extend(f"- `{path}`" for path in artifacts) if artifacts else lines.append("- None")
    if dashboard.get("latest_handoff_prompt_path"):
        lines.append(f"- latest_handoff_prompt: `{dashboard['latest_handoff_prompt_path']}`")
    lines.extend(["", "## Next Operator Action", "", str(dashboard["next_operator_action"]), ""])
    return "\n".join(lines)


def _task_status(state: PlanRunState, task_id: str) -> str:
    if task_id in state.completed_task_ids:
        return "completed"
    if task_id in state.blocked_task_ids:
        return "blocked"
    if task_id in state.failed_task_ids:
        return "failed"
    if task_id in state.skipped_task_ids:
        return "skipped"
    task_state = state.task_states.get(task_id)
    return task_state.status if task_state and task_state.status != "done" else "pending"


def _terminal_details(state: PlanRunState, kind: str) -> list[dict[str, Any]]:
    task_ids = state.blocked_task_ids if kind == "blocked" else state.failed_task_ids
    details: list[dict[str, Any]] = []
    for task_id in task_ids:
        task_state = state.task_states.get(task_id)
        details.append(
            {
                "task_id": task_id,
                "errors": list(task_state.errors) if task_state else [],
                "artifact_paths": list(task_state.artifact_paths) if task_state else [],
                "last_event": task_state.last_event if task_state else "",
            }
        )
    return details


def _next_operator_action(status: str, next_tasks: list[Any], consistency: dict[str, Any]) -> str:
    if not consistency.get("consistent", False):
        return "Run recover-plan before continuing; state consistency validation failed."
    if status == "completed":
        return "Review artifacts, validation, and selective commit/push decision."
    if status == "blocked":
        return "Inspect blocked tasks and run recover-plan or export a handoff prompt."
    if status == "failed":
        return "Inspect failed tasks and decide retry or recovery."
    if status == "paused":
        return "Run continue-plan when the operator is ready."
    if next_tasks:
        return f"Continue with next task {next_tasks[0].task_id} or export a Codex handoff prompt."
    return "Inspect state; no runnable task is available."


def _git_summary(repo_root: str | Path) -> dict[str, Any]:
    return {
        "branch": _git(["branch", "--show-current"], repo_root),
        "head": _git(["rev-parse", "HEAD"], repo_root),
        "dirty": bool(_git(["status", "--short"], repo_root)),
    }


def _git(args: list[str], repo_root: str | Path) -> str:
    try:
        completed = subprocess.run(
            ["git", *args],
            cwd=str(repo_root),
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError:
        return ""
    return completed.stdout.strip() if completed.returncode == 0 else ""


def _read_json(path: str | Path) -> dict[str, Any]:
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}
