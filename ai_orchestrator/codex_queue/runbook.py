from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from .files import ensure_queue_directories, safe_queue_path, write_json_atomic, write_text_atomic
from .queue_health import collect_queue_health

RUNBOOK_SCHEMA_VERSION = "controlled_codex_runbook.v1"

PROHIBITED_ACTIONS = [
    "Do not execute Codex automatically.",
    "Do not call Codex app-server.",
    "Do not create branches automatically.",
    "Do not create worktrees automatically.",
    "Do not commit or push.",
    "Do not move task states from this runbook.",
    "Do not mark tasks done automatically.",
    "Do not start background workers or schedulers.",
    "Do not call network services.",
    "Do not access credentials, wallet/private keys, orders, trading, or payment code.",
    "Do not modify dispatcher, run_codex, or runtime execution code.",
]


def generate_controlled_runbook(
    queue_root: str | Path,
    output_dir: str | Path | None = None,
) -> dict[str, Any]:
    root = ensure_queue_directories(queue_root)
    reports_dir = _report_output_dir(root, output_dir)
    health = collect_queue_health(root)
    ready_tasks = [
        _runbook_task(root, summary)
        for summary in health["task_summaries"]
        if summary.get("next_action") == "manual_codex_handoff_ready"
    ]
    handoff_candidates = [
        _runbook_task(root, summary)
        for summary in health["task_summaries"]
        if summary.get("handoff_prompt", {}).get("found")
    ]

    report: dict[str, Any] = {
        "schema_version": RUNBOOK_SCHEMA_VERSION,
        "run_id": _run_id(),
        "queue_root": str(root),
        "queue_health": _health_summary(health),
        "ready_for_manual_codex_handoff": ready_tasks,
        "handoff_candidates": handoff_candidates,
        "task_recommendations": [
            {
                "task_id": summary["task_id"],
                "state": summary["state"],
                "next_action": summary["next_action"],
                "handoff_prompt_path": summary["handoff_prompt"]["path"],
                "workspace_plan_path": summary["workspace_plan"]["path"],
                "expected_result_path": summary["expected_result_path"],
            }
            for summary in health["task_summaries"]
        ],
        "operator_commands": _operator_commands(str(root)),
        "manual_gate": {
            "codex_is_not_executed_automatically": True,
            "branch_worktree_creation_is_not_automatic": True,
            "operator_must_review_handoff_prompt": True,
            "operator_must_paste_or_run_handoff_manually": True,
            "operator_must_place_result_json_in_review": True,
            "operator_must_run_ingest_and_review": True,
            "operator_must_explicitly_mark_done": True,
        },
        "what_not_to_do": PROHIBITED_ACTIONS,
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
    }

    json_path = reports_dir / "latest_controlled_codex_runbook.json"
    md_path = reports_dir / "latest_controlled_codex_runbook.md"
    report["report_paths"] = {
        "latest_controlled_runbook_json": str(json_path),
        "latest_controlled_runbook_md": str(md_path),
    }
    write_json_atomic(json_path, report)
    write_text_atomic(md_path, render_controlled_runbook_markdown(report))
    return report


def render_controlled_runbook_markdown(report: Mapping[str, Any]) -> str:
    lines = [
        "# Controlled Manual Codex Runbook",
        "",
        f"- run_id: `{report['run_id']}`",
        f"- queue_root: `{report['queue_root']}`",
        "",
        "## Manual Gate",
        "",
        "Codex is not executed automatically. Branch/worktree creation is not automatic. The operator must review each handoff prompt before using it, paste or run that handoff manually in Codex or another controlled environment, place the returned result JSON in `agent_tasks/review/`, run ingestion and review commands, and explicitly run `mark-done` only after review.",
        "",
        "## Queue State",
        "",
    ]
    counts = report.get("queue_health", {}).get("counts", {})
    for state, count in counts.items():
        lines.append(f"- {state}: `{count}`")
    lines.extend(
        [
            "",
            "## Ready For Manual Codex Handoff",
            "",
        ]
    )
    ready_tasks = list(report.get("ready_for_manual_codex_handoff", []))
    if not ready_tasks:
        lines.append("- No tasks are currently ready for manual Codex handoff.")
    for task in ready_tasks:
        lines.append(f"- `{task['task_id']}`")
        lines.append(f"  - handoff_prompt: `{task['handoff_prompt_path']}`")
        lines.append(f"  - workspace_plan_exists: `{task['workspace_plan_exists']}`")
        lines.append(f"  - workspace_plan: `{task['workspace_plan_path']}`")
        lines.append(f"  - result_json_to_return: `{task['expected_result_path']}`")
        lines.append("  - manual_steps:")
        for step in task["manual_steps"]:
            lines.append(f"    - {step}")
        lines.append("  - after_result_commands:")
        for command in task["after_result_commands"]:
            lines.append(f"    - `{command}`")
    lines.extend(
        [
            "",
            "## General Operator Commands",
            "",
        ]
    )
    for label, command in report.get("operator_commands", {}).items():
        lines.append(f"- {label}: `{command}`")
    lines.extend(
        [
            "",
            "## What Not To Do",
            "",
        ]
    )
    for item in report.get("what_not_to_do", []):
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## Safety",
            "",
            "This runbook only reads local queue files and writes JSON/Markdown reports. It does not execute Codex, call Codex app-server, create branches, create worktrees, move tasks, mark tasks done, start workers, add schedulers, call network services, or access credentials.",
            "",
        ]
    )
    return "\n".join(lines)


def _runbook_task(root: Path, summary: Mapping[str, Any]) -> dict[str, Any]:
    task_id = str(summary["task_id"])
    expected_result_path = str(safe_queue_path(root, "review", f"{task_id}.result.json"))
    after_result_commands = [
        f"python -m ai_orchestrator.codex_queue.operator_cli ingest-result --queue-root {root} --result {expected_result_path}",
        f"python -m ai_orchestrator.codex_queue.operator_cli review --queue-root {root} --task-id {task_id}",
        f"python -m ai_orchestrator.codex_queue.operator_cli mark-done --queue-root {root} --task-id {task_id}",
    ]
    return {
        "task_id": task_id,
        "state": summary.get("state"),
        "next_action": summary.get("next_action"),
        "task_packet_path": summary.get("task_packet", {}).get("path"),
        "handoff_prompt_path": summary.get("handoff_prompt", {}).get("path"),
        "workspace_plan_exists": bool(summary.get("workspace_plan", {}).get("found")),
        "workspace_plan_path": summary.get("workspace_plan", {}).get("path"),
        "workspace_plan_status": summary.get("workspace_plan", {}).get("status"),
        "expected_result_path": expected_result_path,
        "manual_steps": [
            f"Open and review the handoff prompt at {summary.get('handoff_prompt', {}).get('path')}.",
            "Confirm the workspace plan is acceptable; it is advisory and did not create anything.",
            "Paste or run the handoff manually in Codex or the chosen controlled local environment.",
            f"Ask Codex to return a result JSON packet at {expected_result_path}.",
            "Inspect the result before ingestion.",
        ],
        "after_result_commands": after_result_commands,
    }


def _operator_commands(queue_root: str) -> dict[str, str]:
    base = "python -m ai_orchestrator.codex_queue.operator_cli"
    return {
        "status": f"{base} status --queue-root {queue_root}",
        "plan": f"{base} plan --queue-root {queue_root}",
        "runbook": f"{base} runbook --queue-root {queue_root}",
        "morning_report": f"{base} morning-report --queue-root {queue_root}",
        "next_actions": f"{base} next-actions --queue-root {queue_root}",
    }


def _health_summary(health: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "counts": health.get("counts", {}),
        "artifact_counts": health.get("artifact_counts", {}),
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
        "next_action_counts": health.get("next_action_counts", {}),
    }


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
