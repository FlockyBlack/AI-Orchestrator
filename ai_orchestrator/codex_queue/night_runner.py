from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from .files import ensure_queue_directories, read_json, safe_queue_path, write_json_atomic, write_text_atomic
from .git_safety import inspect_git_state
from .queue_health import NEXT_ACTION_PRIORITY, collect_queue_health

NIGHT_DRY_RUN_SCHEMA_VERSION = "codex_night_dry_run_plan.v1"
LOCK_CHECK_SCHEMA_VERSION = "codex_night_runner_lock_check.v1"


def generate_night_dry_run_plan(
    queue_root: str | Path,
    max_tasks: int = 5,
    *,
    ignore_stale_lock: bool = False,
) -> dict[str, Any]:
    root = ensure_queue_directories(queue_root)
    reports_dir = safe_queue_path(root, "reports")
    run_id = _run_id()
    generated_at = _utc_iso()
    warnings: list[str] = []
    errors: list[str] = []
    task_cap = _normalize_max_tasks(max_tasks, warnings)

    lock_check = inspect_night_runner_lock(root, ignore_stale_lock=ignore_stale_lock)
    if lock_check["status"] == "blocked":
        errors.append("night runner lock exists; dry-run planning is blocked")
    warnings.extend(lock_check.get("warnings", []))
    errors.extend(lock_check.get("errors", []))

    health = collect_queue_health(root)
    git_state = inspect_git_state(".")
    warnings.extend(git_state.get("warnings", []))
    errors.extend(git_state.get("errors", []))

    task_summaries = [
        summary for summary in health.get("task_summaries", []) if isinstance(summary, Mapping)
    ]
    eligible_all = _tasks_for_action(task_summaries, "manual_codex_handoff_ready")
    ordered_all = _ordered_next_actions(str(root), task_summaries)
    selected_batch = _select_batch(eligible_all, ordered_all, task_cap)

    report: dict[str, Any] = {
        "schema_version": NIGHT_DRY_RUN_SCHEMA_VERSION,
        "status": "blocked" if errors else "ok",
        "queue_root": str(root),
        "generated_at": generated_at,
        "run_id": run_id,
        "max_tasks": task_cap,
        "git_state": git_state,
        "queue_health": _health_summary(health),
        "eligible_for_manual_handoff": eligible_all[:task_cap],
        "needs_plan": _tasks_for_action(task_summaries, "run_plan"),
        "needs_workspace_plan": _tasks_for_action(task_summaries, "run_workspace_plan"),
        "needs_result_ingestion": _tasks_for_action(task_summaries, "ingest_result"),
        "needs_review": _tasks_for_action(task_summaries, "review_result"),
        "ready_for_mark_done": _tasks_for_action(task_summaries, "ready_for_mark_done"),
        "blocked_tasks": _blocked_tasks(health, task_summaries),
        "ordered_next_actions": ordered_all[:task_cap],
        "batch_evaluation": {
            "safe_batch_mode": "dry_run_only",
            "candidate_count": len(eligible_all),
            "ordered_action_count": len(ordered_all),
            "selected_task_count": len(selected_batch),
            "selected_task_ids": [task["task_id"] for task in selected_batch],
            "max_tasks": task_cap,
            "cap_applied": len(eligible_all) > task_cap or len(ordered_all) > task_cap,
            "skipped_manual_handoff_due_to_cap": max(0, len(eligible_all) - task_cap),
        },
        "lock_check": {
            "status": lock_check["status"],
            "lock_exists": lock_check["lock_exists"],
            "lock_path": lock_check["lock_path"],
            "ignored_stale_lock": lock_check["ignored_stale_lock"],
            "report_paths": lock_check["report_paths"],
        },
        "would_execute_codex": False,
        "would_create_branch": False,
        "would_create_worktree": False,
        "would_register_scheduler": False,
        "codex_execution_added": False,
        "codex_app_server_used": False,
        "automatic_execution_enabled": False,
        "branch_created": False,
        "worktree_created": False,
        "background_worker_added": False,
        "scheduler_added": False,
        "network_calls_performed": 0,
        "credentials_accessed": False,
        "task_packets_moved": False,
        "task_marked_done_automatically": False,
        "errors": errors,
        "warnings": warnings,
    }

    timestamped_json = reports_dir / f"night_dry_run_plan_{run_id}.json"
    latest_json = reports_dir / "latest_night_dry_run_plan.json"
    latest_md = reports_dir / "latest_night_dry_run_plan.md"
    report["report_paths"] = {
        "timestamped_night_dry_run_plan_json": str(timestamped_json),
        "latest_night_dry_run_plan_json": str(latest_json),
        "latest_night_dry_run_plan_md": str(latest_md),
    }
    write_json_atomic(timestamped_json, report)
    write_json_atomic(latest_json, report)
    write_text_atomic(latest_md, render_night_dry_run_markdown(report))
    return report


def inspect_night_runner_lock(
    queue_root: str | Path,
    *,
    ignore_stale_lock: bool = False,
) -> dict[str, Any]:
    root = ensure_queue_directories(queue_root)
    lock_path = safe_queue_path(root, "running", "night_runner.lock.json")
    reports_dir = safe_queue_path(root, "reports")
    warnings: list[str] = []
    errors: list[str] = []
    payload: dict[str, Any] | None = None

    if lock_path.exists():
        try:
            raw_payload = read_json(lock_path)
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"lock file exists but is not valid JSON: {exc}")
        else:
            if isinstance(raw_payload, Mapping):
                payload = dict(raw_payload)
            else:
                errors.append("lock file exists but does not contain a JSON object")
        if ignore_stale_lock:
            warnings.append("night runner lock exists but was ignored by explicit operator flag")

    status = "ok"
    if lock_path.exists() and not ignore_stale_lock:
        status = "blocked"
    report: dict[str, Any] = {
        "schema_version": LOCK_CHECK_SCHEMA_VERSION,
        "status": status,
        "queue_root": str(root),
        "generated_at": _utc_iso(),
        "run_id": _run_id(),
        "lock_path": str(lock_path),
        "lock_exists": lock_path.exists(),
        "ignored_stale_lock": bool(lock_path.exists() and ignore_stale_lock),
        "lock_payload": payload,
        "lock_created": False,
        "lock_removed": False,
        "would_start_background_worker": False,
        "would_execute_codex": False,
        "errors": errors,
        "warnings": warnings,
    }
    latest_json = reports_dir / "latest_night_runner_lock_check.json"
    latest_md = reports_dir / "latest_night_runner_lock_check.md"
    report["report_paths"] = {
        "latest_night_runner_lock_check_json": str(latest_json),
        "latest_night_runner_lock_check_md": str(latest_md),
    }
    write_json_atomic(latest_json, report)
    write_text_atomic(latest_md, render_lock_check_markdown(report))
    return report


def render_night_dry_run_markdown(report: Mapping[str, Any]) -> str:
    health = report.get("queue_health", {})
    counts = _as_mapping(health.get("counts"))
    lines = [
        "# Night Dry-Run Plan",
        "",
        f"- status: `{report['status']}`",
        f"- generated_at: `{report['generated_at']}`",
        f"- queue_root: `{report['queue_root']}`",
        f"- max_tasks: `{report['max_tasks']}`",
        f"- lock_status: `{_as_mapping(report.get('lock_check')).get('status')}`",
        "",
        "## Queue Snapshot",
        "",
    ]
    for state in ("inbox", "approved", "planned", "running", "review", "done", "blocked"):
        lines.append(f"- {state}: `{counts.get(state, 0)}`")
    lines.extend(
        [
            "",
            "## Batch Evaluation",
            "",
            f"- eligible_for_manual_handoff: `{len(report.get('eligible_for_manual_handoff', []))}`",
            f"- needs_plan: `{len(report.get('needs_plan', []))}`",
            f"- needs_workspace_plan: `{len(report.get('needs_workspace_plan', []))}`",
            f"- needs_result_ingestion: `{len(report.get('needs_result_ingestion', []))}`",
            f"- needs_review: `{len(report.get('needs_review', []))}`",
            f"- ready_for_mark_done: `{len(report.get('ready_for_mark_done', []))}`",
            f"- blocked_tasks: `{len(report.get('blocked_tasks', []))}`",
            "",
            "## Ordered Next Actions",
            "",
        ]
    )
    actions = list(report.get("ordered_next_actions", []))
    if not actions:
        lines.append("- No immediate queue actions are recommended.")
    for action in actions:
        command = action.get("command")
        lines.append(
            f"- P{action['priority']} `{action['task_id']}`: `{action['next_action']}` - {action['reason']}"
        )
        if command:
            lines.append(f"  - command: `{command}`")

    if report.get("errors"):
        lines.extend(["", "## Errors", ""])
        lines.extend(f"- {error}" for error in report.get("errors", []))
    if report.get("warnings"):
        lines.extend(["", "## Warnings", ""])
        lines.extend(f"- {warning}" for warning in report.get("warnings", []))

    lines.extend(
        [
            "",
            "## Safety",
            "",
            "This night dry-run only reads local queue/git state and writes reports. It does not execute Codex, call Codex app-server, create branches, create worktrees, register schedulers, start background workers, move task packets, mark tasks done, call network services, or access credentials.",
            "",
        ]
    )
    return "\n".join(lines)


def render_lock_check_markdown(report: Mapping[str, Any]) -> str:
    lines = [
        "# Night Runner Lock Check",
        "",
        f"- status: `{report['status']}`",
        f"- generated_at: `{report['generated_at']}`",
        f"- lock_path: `{report['lock_path']}`",
        f"- lock_exists: `{report['lock_exists']}`",
        f"- ignored_stale_lock: `{report['ignored_stale_lock']}`",
        f"- lock_created: `{report['lock_created']}`",
        f"- lock_removed: `{report['lock_removed']}`",
        "",
    ]
    if report.get("errors"):
        lines.extend(["## Errors", ""])
        lines.extend(f"- {error}" for error in report.get("errors", []))
        lines.append("")
    if report.get("warnings"):
        lines.extend(["## Warnings", ""])
        lines.extend(f"- {warning}" for warning in report.get("warnings", []))
        lines.append("")
    lines.extend(
        [
            "## Safety",
            "",
            "This check is report-only. It did not create a long-running lock, remove a lock, start a worker, wait in a loop, execute Codex, or register a scheduler.",
            "",
        ]
    )
    return "\n".join(lines)


def _tasks_for_action(task_summaries: list[Mapping[str, Any]], action: str) -> list[dict[str, Any]]:
    return [_task_entry(summary) for summary in task_summaries if summary.get("next_action") == action]


def _blocked_tasks(health: Mapping[str, Any], task_summaries: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    blocked_by_action = _tasks_for_action(task_summaries, "blocked_requires_operator_attention")
    reasons = {
        str(item.get("task_id")): item.get("reason", "")
        for item in health.get("blocked_tasks", [])
        if isinstance(item, Mapping)
    }
    for item in blocked_by_action:
        item["reason"] = reasons.get(str(item["task_id"]), "")
    return blocked_by_action


def _ordered_next_actions(queue_root: str, task_summaries: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    actions = []
    for summary in task_summaries:
        action = str(summary.get("next_action", "unknown_needs_operator_review"))
        if action == "done_no_action_needed":
            continue
        entry = _task_entry(summary)
        entry.update(
            {
                "priority": NEXT_ACTION_PRIORITY.get(action, 90),
                "reason": _reason_for_action(action),
                "command": _command_for_action(queue_root, summary, action),
            }
        )
        actions.append(entry)
    return sorted(actions, key=lambda item: (item["priority"], item["task_id"]))


def _select_batch(
    eligible_for_handoff: list[dict[str, Any]],
    ordered_actions: list[dict[str, Any]],
    max_tasks: int,
) -> list[dict[str, Any]]:
    if eligible_for_handoff:
        return eligible_for_handoff[:max_tasks]
    return ordered_actions[:max_tasks]


def _task_entry(summary: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "task_id": str(summary.get("task_id", "")),
        "state": summary.get("state"),
        "next_action": summary.get("next_action"),
        "task_packet_path": _as_mapping(summary.get("task_packet")).get("path"),
        "plan_path": _as_mapping(summary.get("plan")).get("path"),
        "handoff_prompt_path": _as_mapping(summary.get("handoff_prompt")).get("path"),
        "workspace_plan_path": _as_mapping(summary.get("workspace_plan")).get("path"),
        "result_path": _as_mapping(summary.get("result_packet")).get("path"),
        "review_report_path": _as_mapping(summary.get("review_report")).get("path"),
        "expected_result_path": summary.get("expected_result_path"),
    }


def _command_for_action(queue_root: str, summary: Mapping[str, Any], action: str) -> str:
    task_id = str(summary.get("task_id", ""))
    base = "python -m ai_orchestrator.codex_queue.operator_cli"
    if action == "blocked_requires_operator_attention":
        return f"{base} review --queue-root {queue_root} --task-id {task_id}"
    if action == "ingest_result":
        result_path = _as_mapping(summary.get("result_packet")).get("path") or summary.get("expected_result_path")
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
        "run_workspace_plan": "Task needs a local workspace plan report.",
        "manual_codex_handoff_ready": "Task is ready for manual handoff after operator review.",
        "create_or_approve_task": "Inbox task needs approval before planning.",
        "unknown_needs_operator_review": "Task artifacts need manual inspection.",
    }
    return reasons.get(action, "Task needs operator review.")


def _health_summary(health: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": health.get("schema_version"),
        "run_id": health.get("run_id"),
        "counts": health.get("counts", {}),
        "artifact_counts": health.get("artifact_counts", {}),
        "next_action_counts": health.get("next_action_counts", {}),
        "approved_tasks_without_plans_count": health.get("approved_tasks_without_plans_count", 0),
        "approved_or_planned_tasks_without_workspace_plans_count": health.get(
            "approved_or_planned_tasks_without_workspace_plans_count", 0
        ),
        "planned_tasks_with_handoff_prompts_count": health.get("planned_tasks_with_handoff_prompts_count", 0),
        "review_results_waiting_for_ingestion_count": health.get(
            "review_results_waiting_for_ingestion_count", 0
        ),
        "review_results_ingested_but_not_reviewed_count": health.get(
            "review_results_ingested_but_not_reviewed_count", 0
        ),
        "review_reports_ready_for_mark_done_count": health.get("review_reports_ready_for_mark_done_count", 0),
        "blocked_tasks_count": health.get("blocked_tasks_count", 0),
        "done_tasks_count": health.get("done_tasks_count", 0),
        "task_count": len(health.get("task_summaries", [])),
    }


def _normalize_max_tasks(max_tasks: int, warnings: list[str]) -> int:
    try:
        value = int(max_tasks)
    except (TypeError, ValueError):
        warnings.append(f"invalid max_tasks {max_tasks!r}; using 5")
        return 5
    if value < 1:
        warnings.append(f"max_tasks must be at least 1; using 1 instead of {value}")
        return 1
    return value


def _as_mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _run_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _utc_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
