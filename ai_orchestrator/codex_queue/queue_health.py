from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from .files import (
    QUEUE_STATE_DIRECTORIES,
    count_task_packets,
    ensure_queue_directories,
    find_task_packet,
    read_json,
    safe_queue_path,
    validate_task_id,
    write_json_atomic,
    write_text_atomic,
)

QUEUE_HEALTH_SCHEMA_VERSION = "codex_queue_health.v1"
NEXT_ACTIONS_SCHEMA_VERSION = "codex_next_actions.v1"

NEXT_ACTION_PRIORITY = {
    "blocked_requires_operator_attention": 10,
    "ingest_result": 20,
    "review_result": 30,
    "ready_for_mark_done": 40,
    "run_plan": 50,
    "run_workspace_plan": 60,
    "manual_codex_handoff_ready": 70,
    "create_or_approve_task": 80,
    "unknown_needs_operator_review": 90,
    "done_no_action_needed": 100,
}

READY_REVIEW_RECOMMENDATIONS = {
    "ready_for_operator_done",
    "ready_for_mark_done",
}


def collect_queue_health(queue_root: str | Path) -> dict[str, Any]:
    root = ensure_queue_directories(queue_root)
    task_ids = sorted(_collect_task_ids(root))
    task_summaries = [summarize_task_state(root, task_id) for task_id in task_ids]

    counts = {state: count_task_packets(root, state) for state in QUEUE_STATE_DIRECTORIES}
    artifact_counts = {
        "plans": len(list(safe_queue_path(root, "planned").glob("*.plan.json"))),
        "workspace_plans": len(list(safe_queue_path(root, "planned").glob("*.workspace_plan.json"))),
        "handoff_prompts": len(list(safe_queue_path(root, "planned").glob("*.handoff_prompt.md"))),
        "result_packets": len(list(safe_queue_path(root, "review").glob("*.result.json"))),
        "review_reports": len(list(safe_queue_path(root, "reports").glob("*.review.json"))),
        "blocked_reports": len(list(safe_queue_path(root, "reports").glob("*.blocked.json"))),
        "reports": len([path for path in safe_queue_path(root, "reports").glob("*") if path.is_file()]),
    }

    approved_without_plans = [
        _task_ref(summary)
        for summary in task_summaries
        if summary["state"] == "approved" and not summary["plan"]["found"]
    ]
    approved_or_planned_without_workspace_plans = [
        _task_ref(summary)
        for summary in task_summaries
        if summary["state"] in {"approved", "planned"} and not summary["workspace_plan"]["found"]
    ]
    planned_with_handoff_prompts = [
        _task_ref(summary)
        for summary in task_summaries
        if summary["plan"]["found"] and summary["handoff_prompt"]["found"]
    ]
    review_results_waiting_for_ingestion = [
        _task_ref(summary)
        for summary in task_summaries
        if summary["result_packet"]["found"] and not summary["ingestion"]["allowed"]
    ]
    review_results_ingested_but_not_reviewed = [
        _task_ref(summary)
        for summary in task_summaries
        if summary["result_packet"]["found"]
        and summary["ingestion"]["allowed"]
        and not summary["review_report"]["found"]
    ]
    review_reports_ready_for_mark_done = [
        _task_ref(summary)
        for summary in task_summaries
        if summary["review_report"]["ready_for_mark_done"] and summary["state"] != "done"
    ]
    blocked_tasks = [
        {
            **_task_ref(summary),
            "reason": summary.get("blocked_reason", ""),
        }
        for summary in task_summaries
        if summary["state"] == "blocked"
    ]
    done_tasks = [_task_ref(summary) for summary in task_summaries if summary["state"] == "done"]
    next_action_counts: dict[str, int] = {}
    for summary in task_summaries:
        action = str(summary["next_action"])
        next_action_counts[action] = next_action_counts.get(action, 0) + 1

    return {
        "schema_version": QUEUE_HEALTH_SCHEMA_VERSION,
        "run_id": _run_id(),
        "queue_root": str(root),
        "counts": counts,
        "artifact_counts": artifact_counts,
        "approved_tasks_without_plans": approved_without_plans,
        "approved_tasks_without_plans_count": len(approved_without_plans),
        "approved_or_planned_tasks_without_workspace_plans": approved_or_planned_without_workspace_plans,
        "approved_or_planned_tasks_without_workspace_plans_count": len(
            approved_or_planned_without_workspace_plans
        ),
        "planned_tasks_with_handoff_prompts": planned_with_handoff_prompts,
        "planned_tasks_with_handoff_prompts_count": len(planned_with_handoff_prompts),
        "review_results_waiting_for_ingestion": review_results_waiting_for_ingestion,
        "review_results_waiting_for_ingestion_count": len(review_results_waiting_for_ingestion),
        "review_results_ingested_but_not_reviewed": review_results_ingested_but_not_reviewed,
        "review_results_ingested_but_not_reviewed_count": len(review_results_ingested_but_not_reviewed),
        "review_reports_ready_for_mark_done": review_reports_ready_for_mark_done,
        "review_reports_ready_for_mark_done_count": len(review_reports_ready_for_mark_done),
        "blocked_tasks": blocked_tasks,
        "blocked_tasks_count": len(blocked_tasks),
        "done_tasks": done_tasks,
        "done_tasks_count": len(done_tasks),
        "next_action_counts": next_action_counts,
        "task_summaries": task_summaries,
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


def summarize_task_state(queue_root: str | Path, task_id: str) -> dict[str, Any]:
    root = ensure_queue_directories(queue_root)
    safe_task_id = validate_task_id(task_id)
    task_match = find_task_packet(root, safe_task_id)
    packet = dict(task_match["packet"]) if task_match["found"] else {}
    plan = _plan_summary(root, safe_task_id)
    handoff_prompt = _path_summary(safe_queue_path(root, "planned", f"{safe_task_id}.handoff_prompt.md"))
    workspace_plan = _workspace_plan_summary(root, safe_task_id)
    result_packet = _result_packet_summary(root, safe_task_id)
    ingestion = _ingestion_summary(root, safe_task_id)
    review_report = _review_report_summary(root, safe_task_id)
    blocked_reason = _blocked_reason(root, safe_task_id, packet)

    summary: dict[str, Any] = {
        "task_id": safe_task_id,
        "state": task_match.get("state"),
        "task_packet": {
            "found": bool(task_match["found"]),
            "path": str(task_match["path"]) if task_match.get("path") else None,
            "status": packet.get("status"),
            "title": packet.get("title"),
            "priority": packet.get("priority"),
            "task_type": packet.get("task_type"),
        },
        "plan": plan,
        "handoff_prompt": handoff_prompt,
        "workspace_plan": workspace_plan,
        "result_packet": result_packet,
        "ingestion": ingestion,
        "review_report": review_report,
        "blocked_reason": blocked_reason,
        "expected_result_path": str(safe_queue_path(root, "review", f"{safe_task_id}.result.json")),
    }
    summary["manual_handoff_ready"] = (
        summary["handoff_prompt"]["found"]
        and summary["workspace_plan"]["found"]
        and not summary["result_packet"]["found"]
        and summary["state"] not in {"blocked", "done"}
    )
    summary["next_action"] = recommend_next_action(summary)
    return summary


def recommend_next_action(task_summary: Mapping[str, Any]) -> str:
    state = task_summary.get("state")
    result_packet = _as_mapping(task_summary.get("result_packet"))
    ingestion = _as_mapping(task_summary.get("ingestion"))
    review_report = _as_mapping(task_summary.get("review_report"))
    plan = _as_mapping(task_summary.get("plan"))
    handoff_prompt = _as_mapping(task_summary.get("handoff_prompt"))
    workspace_plan = _as_mapping(task_summary.get("workspace_plan"))

    if state == "done":
        return "done_no_action_needed"
    if state == "blocked":
        return "blocked_requires_operator_attention"
    if result_packet.get("found") and not ingestion.get("allowed"):
        return "ingest_result"
    if result_packet.get("found") and ingestion.get("allowed") and not review_report.get("found"):
        return "review_result"
    if review_report.get("ready_for_mark_done"):
        return "ready_for_mark_done"
    if state in {None, "inbox"}:
        return "create_or_approve_task"
    if state in {"approved", "planned"} and (not plan.get("found") or not handoff_prompt.get("found")):
        return "run_plan"
    if state in {"approved", "planned"} and not workspace_plan.get("found"):
        return "run_workspace_plan"
    if handoff_prompt.get("found") and workspace_plan.get("found"):
        return "manual_codex_handoff_ready"
    return "unknown_needs_operator_review"


def generate_next_actions_report(
    queue_root: str | Path,
    output_dir: str | Path | None = None,
) -> dict[str, Any]:
    root = ensure_queue_directories(queue_root)
    reports_dir = _report_output_dir(root, output_dir)
    health = collect_queue_health(root)
    actions = _ordered_next_actions(health)
    report: dict[str, Any] = {
        "schema_version": NEXT_ACTIONS_SCHEMA_VERSION,
        "run_id": _run_id(),
        "queue_root": str(root),
        "queue_health": _health_summary(health),
        "next_actions": actions,
        "batch_plan": actions,
        "codex_execution_added": False,
        "codex_app_server_used": False,
        "automatic_execution_enabled": False,
        "branch_created": False,
        "worktree_created": False,
        "background_worker_added": False,
        "scheduler_added": False,
        "network_calls_performed": 0,
    }
    json_path = reports_dir / "latest_next_actions.json"
    md_path = reports_dir / "latest_next_actions.md"
    report["report_paths"] = {
        "latest_next_actions_json": str(json_path),
        "latest_next_actions_md": str(md_path),
    }
    write_json_atomic(json_path, report)
    write_text_atomic(md_path, render_next_actions_markdown(report))
    return report


def render_next_actions_markdown(report: Mapping[str, Any]) -> str:
    lines = [
        "# Latest Next Operator Actions",
        "",
        f"- run_id: `{report['run_id']}`",
        f"- queue_root: `{report['queue_root']}`",
        f"- action_count: `{len(report.get('next_actions', []))}`",
        "",
        "## Ordered Actions",
        "",
    ]
    actions = list(report.get("next_actions", []))
    if not actions:
        lines.append("- No queue actions are currently recommended.")
    for action in actions:
        lines.append(
            f"- P{action['priority']} `{action['task_id']}`: `{action['next_action']}` - {action['reason']}"
        )
        command = action.get("command")
        if command:
            lines.append(f"  - command: `{command}`")
        path = action.get("primary_path")
        if path:
            lines.append(f"  - path: `{path}`")
    lines.extend(
        [
            "",
            "## Safety",
            "",
            "This report only reads local queue artifacts and writes report files. It does not execute Codex, call Codex app-server, create branches, create worktrees, move task packets, mark tasks done, start workers, add schedulers, or call network services.",
            "",
        ]
    )
    return "\n".join(lines)


def _ordered_next_actions(health: Mapping[str, Any]) -> list[dict[str, Any]]:
    actions = []
    for summary in health.get("task_summaries", []):
        if not isinstance(summary, Mapping):
            continue
        action = str(summary.get("next_action", "unknown_needs_operator_review"))
        if action == "done_no_action_needed":
            continue
        actions.append(_next_action_entry(str(health["queue_root"]), summary, action))
    return sorted(actions, key=lambda item: (item["priority"], item["task_id"]))


def _next_action_entry(queue_root: str, summary: Mapping[str, Any], action: str) -> dict[str, Any]:
    task_id = str(summary.get("task_id", ""))
    command = _command_for_action(queue_root, task_id, summary, action)
    return {
        "task_id": task_id,
        "next_action": action,
        "priority": NEXT_ACTION_PRIORITY.get(action, 90),
        "reason": _reason_for_action(action),
        "command": command,
        "primary_path": _primary_path_for_action(summary, action),
        "expected_result_path": summary.get("expected_result_path"),
        "task_packet_path": _as_mapping(summary.get("task_packet")).get("path"),
        "plan_path": _as_mapping(summary.get("plan")).get("path"),
        "handoff_prompt_path": _as_mapping(summary.get("handoff_prompt")).get("path"),
        "workspace_plan_path": _as_mapping(summary.get("workspace_plan")).get("path"),
        "result_path": _as_mapping(summary.get("result_packet")).get("path"),
        "review_report_path": _as_mapping(summary.get("review_report")).get("path"),
    }


def _command_for_action(queue_root: str, task_id: str, summary: Mapping[str, Any], action: str) -> str:
    base = "python -m ai_orchestrator.codex_queue.operator_cli"
    if action == "create_or_approve_task":
        state = summary.get("state")
        if state == "inbox":
            return f"{base} approve --queue-root {queue_root} --task-id {task_id}"
        return f"{base} create-demo-task --queue-root {queue_root} --task-id ORCH-DEMO-004-RUNBOOK-MORNING-REPORT"
    if action == "run_plan":
        return f"{base} plan --queue-root {queue_root}"
    if action == "run_workspace_plan":
        return f"{base} workspace-plan --queue-root {queue_root} --task-id {task_id}"
    if action == "ingest_result":
        result_path = _as_mapping(summary.get("result_packet")).get("path") or summary.get("expected_result_path")
        return f"{base} ingest-result --queue-root {queue_root} --result {result_path}"
    if action == "review_result":
        return f"{base} review --queue-root {queue_root} --task-id {task_id}"
    if action == "ready_for_mark_done":
        return f"{base} mark-done --queue-root {queue_root} --task-id {task_id}"
    if action == "blocked_requires_operator_attention":
        return f"{base} review --queue-root {queue_root} --task-id {task_id}"
    if action == "manual_codex_handoff_ready":
        return ""
    return f"{base} status --queue-root {queue_root}"


def _primary_path_for_action(summary: Mapping[str, Any], action: str) -> str | None:
    if action == "manual_codex_handoff_ready":
        return _as_mapping(summary.get("handoff_prompt")).get("path")
    if action in {"ingest_result", "review_result"}:
        return _as_mapping(summary.get("result_packet")).get("path")
    if action == "ready_for_mark_done":
        return _as_mapping(summary.get("review_report")).get("path")
    if action == "run_workspace_plan":
        return _as_mapping(summary.get("plan")).get("path")
    return _as_mapping(summary.get("task_packet")).get("path")


def _reason_for_action(action: str) -> str:
    reasons = {
        "create_or_approve_task": "Task is in inbox or missing and needs operator approval or creation.",
        "run_plan": "Approved task does not yet have a dry-run plan and handoff prompt.",
        "run_workspace_plan": "Task has a plan but no local branch/worktree plan report.",
        "manual_codex_handoff_ready": "Handoff prompt and workspace plan are ready for manual operator review.",
        "ingest_result": "A result packet is present but no accepted ingestion report exists.",
        "review_result": "Result ingestion is accepted but no task review report exists.",
        "ready_for_mark_done": "Review report says the task is ready for explicit mark-done.",
        "blocked_requires_operator_attention": "Task is blocked and needs an operator decision.",
        "unknown_needs_operator_review": "Queue artifacts do not match a known happy-path state.",
    }
    return reasons.get(action, "No action reason is registered.")


def _health_summary(health: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "counts": health.get("counts", {}),
        "artifact_counts": health.get("artifact_counts", {}),
        "next_action_counts": health.get("next_action_counts", {}),
        "approved_tasks_without_plans_count": health.get("approved_tasks_without_plans_count", 0),
        "approved_or_planned_tasks_without_workspace_plans_count": health.get(
            "approved_or_planned_tasks_without_workspace_plans_count", 0
        ),
        "review_results_waiting_for_ingestion_count": health.get(
            "review_results_waiting_for_ingestion_count", 0
        ),
        "review_results_ingested_but_not_reviewed_count": health.get(
            "review_results_ingested_but_not_reviewed_count", 0
        ),
        "review_reports_ready_for_mark_done_count": health.get("review_reports_ready_for_mark_done_count", 0),
        "blocked_tasks_count": health.get("blocked_tasks_count", 0),
        "done_tasks_count": health.get("done_tasks_count", 0),
    }


def _collect_task_ids(root: Path) -> set[str]:
    task_ids: set[str] = set()
    for state in QUEUE_STATE_DIRECTORIES:
        for packet_path in safe_queue_path(root, state).glob("*.json"):
            payload = _read_mapping(packet_path)
            task_id = payload.get("task_id") if payload else _task_id_from_name(packet_path.name, ".task.json")
            if isinstance(task_id, str) and _is_valid_task_id(task_id):
                task_ids.add(task_id)
    for plan_path in safe_queue_path(root, "planned").glob("*.plan.json"):
        _add_task_id_from_artifact(task_ids, plan_path, ".plan.json")
    for workspace_plan_path in safe_queue_path(root, "planned").glob("*.workspace_plan.json"):
        _add_task_id_from_artifact(task_ids, workspace_plan_path, ".workspace_plan.json")
    for handoff_path in safe_queue_path(root, "planned").glob("*.handoff_prompt.md"):
        task_id = _task_id_from_name(handoff_path.name, ".handoff_prompt.md")
        if task_id and _is_valid_task_id(task_id):
            task_ids.add(task_id)
    for result_path in safe_queue_path(root, "review").glob("*.result.json"):
        _add_task_id_from_artifact(task_ids, result_path, ".result.json")
    for review_path in safe_queue_path(root, "reports").glob("*.review.json"):
        _add_task_id_from_artifact(task_ids, review_path, ".review.json")
    for blocked_path in safe_queue_path(root, "reports").glob("*.blocked.json"):
        _add_task_id_from_artifact(task_ids, blocked_path, ".blocked.json")
    return task_ids


def _add_task_id_from_artifact(task_ids: set[str], path: Path, suffix: str) -> None:
    payload = _read_mapping(path)
    task_id = payload.get("task_id") if payload else _task_id_from_name(path.name, suffix)
    if isinstance(task_id, str) and _is_valid_task_id(task_id):
        task_ids.add(task_id)


def _plan_summary(root: Path, task_id: str) -> dict[str, Any]:
    path = safe_queue_path(root, "planned", f"{task_id}.plan.json")
    payload = _read_mapping(path) if path.exists() else None
    return {
        "found": path.exists(),
        "path": str(path) if path.exists() else None,
        "handoff_prompt_path": payload.get("handoff_prompt_path") if payload else None,
        "workspace_plan_path": payload.get("workspace_plan_path") if payload else None,
    }


def _workspace_plan_summary(root: Path, task_id: str) -> dict[str, Any]:
    path = safe_queue_path(root, "planned", f"{task_id}.workspace_plan.json")
    payload = _read_mapping(path) if path.exists() else None
    return {
        "found": path.exists(),
        "path": str(path) if path.exists() else None,
        "status": payload.get("status") if payload else None,
        "suggested_branch_name": payload.get("suggested_branch_name") if payload else None,
        "suggested_worktree_path": payload.get("suggested_worktree_path") if payload else None,
        "branch_created": bool(payload.get("branch_created", False)) if payload else False,
        "worktree_created": bool(payload.get("worktree_created", False)) if payload else False,
    }


def _result_packet_summary(root: Path, task_id: str) -> dict[str, Any]:
    path = safe_queue_path(root, "review", f"{task_id}.result.json")
    payload = _read_mapping(path) if path.exists() else None
    return {
        "found": path.exists(),
        "path": str(path) if path.exists() else None,
        "status": payload.get("status") if payload else None,
        "completed_at": payload.get("completed_at") if payload else None,
    }


def _ingestion_summary(root: Path, task_id: str) -> dict[str, Any]:
    reports_dir = safe_queue_path(root, "reports")
    latest = reports_dir / "latest_result_ingestion_report.json"
    candidate_paths = sorted(reports_dir.glob("result_ingestion_report_*.json"), key=_mtime, reverse=True)

    matching_reports: list[dict[str, Any]] = []
    errors: list[str] = []
    latest_payload = _read_mapping(latest) if latest.exists() else None
    for path in candidate_paths:
        payload = _read_mapping(path)
        if not payload:
            if path.exists():
                errors.append(f"{path}: invalid or non-object JSON")
            continue
        if payload.get("task_id") != task_id:
            continue
        allowed = _ingestion_report_allowed(payload)
        status = "allowed" if allowed else str(payload.get("ingestion_status") or "unknown")
        report_ref = {
            "path": str(path),
            "status": status,
            "accepted": bool(payload.get("accepted")),
            "allowed": allowed,
            "errors": list(payload.get("errors", [])),
        }
        matching_reports.append(report_ref)
        if allowed:
            return {
                "found": True,
                "allowed": True,
                "status": "allowed",
                "path": str(path),
                "latest_report_path": str(latest) if latest.exists() else None,
                "latest_report_is_pointer": latest.exists(),
                "latest_report_task_id": latest_payload.get("task_id") if latest_payload else None,
                "latest_report_status": latest_payload.get("ingestion_status") if latest_payload else None,
                "matching_reports": matching_reports,
                "errors": errors,
            }

    return {
        "found": bool(matching_reports),
        "allowed": False,
        "status": matching_reports[0]["status"] if matching_reports else "missing",
        "path": matching_reports[0]["path"] if matching_reports else None,
        "latest_report_path": str(latest) if latest.exists() else None,
        "latest_report_is_pointer": latest.exists(),
        "latest_report_task_id": latest_payload.get("task_id") if latest_payload else None,
        "latest_report_status": latest_payload.get("ingestion_status") if latest_payload else None,
        "matching_reports": matching_reports,
        "errors": errors,
    }


def _review_report_summary(root: Path, task_id: str) -> dict[str, Any]:
    path = safe_queue_path(root, "reports", f"{task_id}.review.json")
    payload = _read_mapping(path) if path.exists() else None
    recommendation = payload.get("recommendation") if payload else None
    return {
        "found": path.exists(),
        "path": str(path) if path.exists() else None,
        "recommendation": recommendation,
        "ready_for_mark_done": recommendation in READY_REVIEW_RECOMMENDATIONS,
        "warnings": list(payload.get("warnings", [])) if payload else [],
    }


def _blocked_reason(root: Path, task_id: str, packet: Mapping[str, Any]) -> str:
    blocked_report_path = safe_queue_path(root, "reports", f"{task_id}.blocked.json")
    blocked_report = _read_mapping(blocked_report_path) if blocked_report_path.exists() else None
    if blocked_report and blocked_report.get("reason"):
        return str(blocked_report["reason"])
    return str(packet.get("operator_notes", ""))


def _path_summary(path: Path) -> dict[str, Any]:
    return {
        "found": path.exists(),
        "path": str(path) if path.exists() else None,
    }


def _ingestion_report_allowed(report: Mapping[str, Any]) -> bool:
    if report.get("errors"):
        return False
    status = report.get("ingestion_status")
    accepted = status in {"accepted", "allowed"} or report.get("accepted") is True
    if not accepted:
        return False
    for key in ("result_validation", "task_validation", "path_validation"):
        validation = report.get(key)
        if isinstance(validation, Mapping) and validation.get("valid") is False:
            return False
    return True


def _task_ref(summary: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "task_id": summary.get("task_id"),
        "state": summary.get("state"),
        "next_action": summary.get("next_action"),
        "task_packet_path": _as_mapping(summary.get("task_packet")).get("path"),
    }


def _read_mapping(path: Path) -> dict[str, Any] | None:
    try:
        payload = read_json(path)
    except (OSError, json.JSONDecodeError):
        return None
    return dict(payload) if isinstance(payload, Mapping) else None


def _task_id_from_name(name: str, suffix: str) -> str | None:
    if not name.endswith(suffix):
        return None
    return name[: -len(suffix)]


def _is_valid_task_id(task_id: str) -> bool:
    try:
        validate_task_id(task_id)
    except ValueError:
        return False
    return True


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


def _mtime(path: Path) -> float:
    try:
        return path.stat().st_mtime
    except FileNotFoundError:
        return 0.0


def _as_mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _run_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
