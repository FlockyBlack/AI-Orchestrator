from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from .files import ensure_queue_directories, read_json, safe_queue_path, write_json_atomic, write_text_atomic
from .queue_health import NEXT_ACTION_PRIORITY, collect_queue_health

MORNING_REPORT_SCHEMA_VERSION = "codex_morning_report.v1"


def generate_morning_report(
    queue_root: str | Path,
    output_dir: str | Path | None = None,
) -> dict[str, Any]:
    root = ensure_queue_directories(queue_root)
    reports_dir = _report_output_dir(root, output_dir)
    run_id = _run_id()
    health = collect_queue_health(root)
    latest_workspace = _latest_report(root, "latest_workspace_plan.json")

    report: dict[str, Any] = {
        "schema_version": MORNING_REPORT_SCHEMA_VERSION,
        "run_id": run_id,
        "queue_root": str(root),
        "queue_health": _health_summary(health),
        "latest_git_safety_summary": _latest_git_safety_summary(latest_workspace.get("payload")),
        "latest_dry_run_report": _report_status(root, "latest_dry_run_report.json", "dry_run"),
        "latest_workspace_plan": _workspace_report_status(latest_workspace),
        "latest_result_ingestion_report": _report_status(
            root,
            "latest_result_ingestion_report.json",
            "ingestion_status",
        ),
        "latest_operator_action": _report_status(root, "latest_operator_action.json", "status"),
        "tasks_needing_attention": _tasks_with_actions(
            health,
            {
                "blocked_requires_operator_attention",
                "ingest_result",
                "review_result",
                "ready_for_mark_done",
                "run_plan",
                "run_workspace_plan",
                "unknown_needs_operator_review",
            },
        ),
        "tasks_ready_for_manual_codex_handoff": _tasks_with_actions(health, {"manual_codex_handoff_ready"}),
        "tasks_ready_for_result_ingestion": _tasks_with_actions(health, {"ingest_result"}),
        "tasks_ready_for_review": _tasks_with_actions(health, {"review_result"}),
        "tasks_ready_for_mark_done": _tasks_with_actions(health, {"ready_for_mark_done"}),
        "blocked_tasks": health.get("blocked_tasks", []),
        "recommended_next_operator_actions": _recommended_actions(health),
        "codex_execution_added": False,
        "codex_app_server_used": False,
        "automatic_execution_enabled": False,
        "branch_created": False,
        "worktree_created": False,
        "background_worker_added": False,
        "scheduler_added": False,
        "network_calls_performed": 0,
        "credentials_accessed": False,
    }

    run_json = reports_dir / f"morning_report_{run_id}.json"
    latest_json = reports_dir / "latest_morning_report.json"
    latest_md = reports_dir / "latest_morning_report.md"
    report["report_paths"] = {
        "run_morning_report_json": str(run_json),
        "latest_morning_report_json": str(latest_json),
        "latest_morning_report_md": str(latest_md),
    }
    write_json_atomic(run_json, report)
    write_json_atomic(latest_json, report)
    write_text_atomic(latest_md, render_morning_report_markdown(report))
    return report


def render_morning_report_markdown(report: Mapping[str, Any]) -> str:
    health = report.get("queue_health", {})
    counts = health.get("counts", {})
    lines = [
        "# Codex Queue Morning Report",
        "",
        f"- run_id: `{report['run_id']}`",
        f"- queue_root: `{report['queue_root']}`",
        "",
        "## Queue Health",
        "",
    ]
    for state in ("inbox", "approved", "planned", "running", "review", "done", "blocked"):
        lines.append(f"- {state}: `{counts.get(state, 0)}`")
    lines.extend(
        [
            f"- ready_for_manual_handoff: `{len(report.get('tasks_ready_for_manual_codex_handoff', []))}`",
            f"- ready_for_result_ingestion: `{len(report.get('tasks_ready_for_result_ingestion', []))}`",
            f"- ready_for_review: `{len(report.get('tasks_ready_for_review', []))}`",
            f"- ready_for_mark_done: `{len(report.get('tasks_ready_for_mark_done', []))}`",
            "",
            "## Latest Reports",
            "",
            _latest_line("dry_run", report.get("latest_dry_run_report", {})),
            _latest_line("workspace_plan", report.get("latest_workspace_plan", {})),
            _latest_line("result_ingestion", report.get("latest_result_ingestion_report", {})),
            _latest_line("operator_action", report.get("latest_operator_action", {})),
            "",
            "## Recommended Next Operator Actions",
            "",
        ]
    )
    actions = list(report.get("recommended_next_operator_actions", []))
    if not actions:
        lines.append("- No immediate operator actions are recommended.")
    for action in actions:
        lines.append(
            f"- P{action['priority']} `{action['task_id']}`: `{action['next_action']}` - {action['reason']}"
        )
        if action.get("command"):
            lines.append(f"  - command: `{action['command']}`")
    lines.extend(
        [
            "",
            "## Blocked Tasks",
            "",
        ]
    )
    blocked_tasks = list(report.get("blocked_tasks", []))
    if not blocked_tasks:
        lines.append("- None.")
    for task in blocked_tasks:
        lines.append(f"- `{task['task_id']}`: {task.get('reason') or 'No reason recorded.'}")
    lines.extend(
        [
            "",
            "## Safety",
            "",
            "This morning report is local-only and operator-invoked. It reads queue/report artifacts and writes report files only; it does not execute Codex, call Codex app-server, create branches, create worktrees, move task packets, mark tasks done, start workers, add schedulers, call network services, or access credentials.",
            "",
        ]
    )
    return "\n".join(lines)


def _tasks_with_actions(health: Mapping[str, Any], actions: set[str]) -> list[dict[str, Any]]:
    tasks = []
    for summary in health.get("task_summaries", []):
        if not isinstance(summary, Mapping) or summary.get("next_action") not in actions:
            continue
        tasks.append(
            {
                "task_id": summary.get("task_id"),
                "state": summary.get("state"),
                "next_action": summary.get("next_action"),
                "handoff_prompt_path": summary.get("handoff_prompt", {}).get("path"),
                "workspace_plan_path": summary.get("workspace_plan", {}).get("path"),
                "result_path": summary.get("result_packet", {}).get("path"),
                "review_report_path": summary.get("review_report", {}).get("path"),
                "expected_result_path": summary.get("expected_result_path"),
            }
        )
    return sorted(tasks, key=lambda item: str(item["task_id"]))


def _recommended_actions(health: Mapping[str, Any]) -> list[dict[str, Any]]:
    actions = []
    queue_root = str(health["queue_root"])
    for summary in health.get("task_summaries", []):
        if not isinstance(summary, Mapping):
            continue
        next_action = str(summary.get("next_action"))
        if next_action == "done_no_action_needed":
            continue
        actions.append(
            {
                "task_id": summary.get("task_id"),
                "next_action": next_action,
                "priority": NEXT_ACTION_PRIORITY.get(next_action, 90),
                "reason": _reason_for_action(next_action),
                "command": _command_for_action(queue_root, summary, next_action),
            }
        )
    return sorted(actions, key=lambda item: (item["priority"], str(item["task_id"])))


def _command_for_action(queue_root: str, summary: Mapping[str, Any], action: str) -> str:
    task_id = str(summary.get("task_id", ""))
    base = "python -m ai_orchestrator.codex_queue.operator_cli"
    if action == "blocked_requires_operator_attention":
        return f"{base} review --queue-root {queue_root} --task-id {task_id}"
    if action == "ingest_result":
        result_path = summary.get("result_packet", {}).get("path") or summary.get("expected_result_path")
        return f"{base} ingest-result --queue-root {queue_root} --result {result_path}"
    if action == "review_result":
        return f"{base} review --queue-root {queue_root} --task-id {task_id}"
    if action == "ready_for_mark_done":
        return f"{base} mark-done --queue-root {queue_root} --task-id {task_id}"
    if action == "run_plan":
        return f"{base} plan --queue-root {queue_root}"
    if action == "run_workspace_plan":
        return f"{base} workspace-plan --queue-root {queue_root} --task-id {task_id}"
    if action == "create_or_approve_task" and summary.get("state") == "inbox":
        return f"{base} approve --queue-root {queue_root} --task-id {task_id}"
    return ""


def _reason_for_action(action: str) -> str:
    reasons = {
        "blocked_requires_operator_attention": "Blocked task requires an operator decision.",
        "ingest_result": "Manual result packet exists and needs ingestion.",
        "review_result": "Accepted ingestion exists and needs task review.",
        "ready_for_mark_done": "Review report is ready for explicit mark-done.",
        "run_plan": "Approved task needs a dry-run plan and handoff prompt.",
        "run_workspace_plan": "Planned task needs a local workspace plan report.",
        "manual_codex_handoff_ready": "Task is ready for manual handoff after operator review.",
        "create_or_approve_task": "Inbox task needs approval before planning.",
        "unknown_needs_operator_review": "Task artifacts need manual inspection.",
    }
    return reasons.get(action, "Task needs operator review.")


def _health_summary(health: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "counts": health.get("counts", {}),
        "artifact_counts": health.get("artifact_counts", {}),
        "blocked_tasks_count": health.get("blocked_tasks_count", 0),
        "done_tasks_count": health.get("done_tasks_count", 0),
        "review_reports_ready_for_mark_done_count": health.get("review_reports_ready_for_mark_done_count", 0),
        "review_results_waiting_for_ingestion_count": health.get(
            "review_results_waiting_for_ingestion_count", 0
        ),
        "review_results_ingested_but_not_reviewed_count": health.get(
            "review_results_ingested_but_not_reviewed_count", 0
        ),
        "planned_tasks_with_handoff_prompts_count": health.get("planned_tasks_with_handoff_prompts_count", 0),
        "next_action_counts": health.get("next_action_counts", {}),
    }


def _latest_report(root: Path, filename: str) -> dict[str, Any]:
    path = safe_queue_path(root, "reports", filename)
    if not path.exists():
        return {"found": False, "path": str(path), "payload": None}
    try:
        payload = read_json(path)
    except (OSError, json.JSONDecodeError):
        return {"found": True, "path": str(path), "payload": None, "errors": ["invalid JSON"]}
    return {
        "found": True,
        "path": str(path),
        "payload": payload if isinstance(payload, Mapping) else None,
        "errors": [] if isinstance(payload, Mapping) else ["report payload is not an object"],
    }


def _report_status(root: Path, filename: str, status_key: str) -> dict[str, Any]:
    latest = _latest_report(root, filename)
    payload = latest.get("payload")
    status = None
    if isinstance(payload, Mapping):
        status = payload.get(status_key)
    return {
        "found": latest["found"],
        "path": latest["path"] if latest["found"] else None,
        "status": status,
        "errors": latest.get("errors", []),
    }


def _workspace_report_status(latest_workspace: Mapping[str, Any]) -> dict[str, Any]:
    payload = latest_workspace.get("payload")
    return {
        "found": bool(latest_workspace.get("found")),
        "path": latest_workspace.get("path") if latest_workspace.get("found") else None,
        "status": payload.get("status") if isinstance(payload, Mapping) else None,
        "task_id": payload.get("task_id") if isinstance(payload, Mapping) else None,
        "branch_created": bool(payload.get("branch_created", False)) if isinstance(payload, Mapping) else False,
        "worktree_created": bool(payload.get("worktree_created", False)) if isinstance(payload, Mapping) else False,
        "errors": latest_workspace.get("errors", []),
    }


def _latest_git_safety_summary(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, Mapping):
        return {"found": False, "source": None}
    git_state = payload.get("git_state")
    if not isinstance(git_state, Mapping):
        return {"found": False, "source": "latest_workspace_plan"}
    return {
        "found": True,
        "source": "latest_workspace_plan",
        "repo_root": git_state.get("repo_root"),
        "branch": git_state.get("branch"),
        "head": git_state.get("head"),
        "is_clean": git_state.get("is_clean"),
        "tracked_changes_count": git_state.get("tracked_changes_count"),
        "untracked_count": git_state.get("untracked_count"),
        "warnings": list(git_state.get("warnings", [])),
        "errors": list(git_state.get("errors", [])),
    }


def _latest_line(label: str, status: Any) -> str:
    payload = status if isinstance(status, Mapping) else {}
    return f"- {label}: found=`{payload.get('found')}` status=`{payload.get('status')}` path=`{payload.get('path')}`"


def _report_output_dir(root: Path, output_dir: str | Path | None) -> Path:
    if output_dir is None:
        return safe_queue_path(root, "reports")
    candidate = Path(output_dir)
    if not candidate.is_absolute():
        candidate = root / candidate
    candidate = candidate.resolve(strict=False)
    root_resolved = root.resolve(strict=False)
    try:
        candidate.relative_to(root_resolved)
    except ValueError as exc:
        raise ValueError(f"output_dir escapes queue root: {candidate}") from exc
    candidate.mkdir(parents=True, exist_ok=True)
    return candidate


def _run_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
