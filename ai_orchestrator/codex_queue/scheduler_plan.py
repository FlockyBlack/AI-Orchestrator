from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from .files import ensure_queue_directories, read_json, safe_queue_path, write_json_atomic, write_text_atomic
from .queue_health import collect_queue_health

SCHEDULER_PLAN_SCHEMA_VERSION = "codex_scheduler_readiness_plan.v1"


def generate_scheduler_readiness_plan(queue_root: str | Path) -> dict[str, Any]:
    root = ensure_queue_directories(queue_root)
    reports_dir = safe_queue_path(root, "reports")
    generated_at = _utc_iso()
    health = collect_queue_health(root)
    latest_night = _latest_report(root, "latest_night_dry_run_plan.json")
    latest_lock = _latest_report(root, "latest_night_runner_lock_check.json")
    latest_morning = _latest_report(root, "latest_morning_report.json")
    latest_ingestion = _latest_report(root, "latest_result_ingestion_report.json")
    gates = _required_safety_gates(latest_night, latest_lock, latest_morning, latest_ingestion)

    report: dict[str, Any] = {
        "schema_version": SCHEDULER_PLAN_SCHEMA_VERSION,
        "status": "ok",
        "queue_root": str(root),
        "generated_at": generated_at,
        "run_id": _run_id(),
        "current_readiness_status": {
            "ready_for_real_scheduler": False,
            "reason": "Planning reports are available, but real scheduler activation still requires explicit future operator approval.",
            "scheduler_registered": False,
            "operator_approval_recorded": False,
        },
        "queue_health": _health_summary(health),
        "latest_reports": {
            "night_dry_run_plan": _report_ref(latest_night),
            "night_runner_lock_check": _report_ref(latest_lock),
            "morning_report": _report_ref(latest_morning),
            "result_ingestion_report": _report_ref(latest_ingestion),
        },
        "required_safety_gates": gates,
        "future_windows_task_scheduler_command_outline": _future_windows_task_scheduler_outline(),
        "staged_activation_plan": _staged_activation_plan(),
        "recommended_future_scheduler_task": {
            "task_id": "ORCH-SYMPHONY-008-SCHEDULER-DRY-ACTIVATION-NO-CODEX-EXECUTION",
            "condition": "Create this task only if the operator explicitly approves scheduler dry activation later.",
            "scope": "Register a scheduler dry-run only after approval; still no Codex execution.",
        },
        "scheduler_registered": False,
        "real_scheduler_registered": False,
        "would_register_scheduler": False,
        "background_worker_added": False,
        "codex_execution_added": False,
        "codex_app_server_used": False,
        "automatic_execution_enabled": False,
        "branch_created": False,
        "worktree_created": False,
        "network_calls_performed": 0,
        "credentials_accessed": False,
        "errors": [],
        "warnings": _scheduler_warnings(gates),
    }

    latest_json = reports_dir / "latest_scheduler_plan.json"
    latest_md = reports_dir / "latest_scheduler_plan.md"
    report["report_paths"] = {
        "latest_scheduler_plan_json": str(latest_json),
        "latest_scheduler_plan_md": str(latest_md),
    }
    write_json_atomic(latest_json, report)
    write_text_atomic(latest_md, render_scheduler_plan_markdown(report))
    return report


def render_scheduler_plan_markdown(report: Mapping[str, Any]) -> str:
    readiness = _as_mapping(report.get("current_readiness_status"))
    lines = [
        "# Scheduler Readiness Plan",
        "",
        f"- status: `{report['status']}`",
        f"- generated_at: `{report['generated_at']}`",
        f"- queue_root: `{report['queue_root']}`",
        f"- scheduler_registered: `{report['scheduler_registered']}`",
        f"- ready_for_real_scheduler: `{readiness.get('ready_for_real_scheduler')}`",
        "",
        "No scheduler was registered. This is documentation and readiness reporting only.",
        "",
        "## Required Safety Gates",
        "",
    ]
    for gate in report.get("required_safety_gates", []):
        lines.append(
            f"- `{gate['gate_id']}`: satisfied=`{gate['satisfied']}` - {gate['description']}"
        )
    lines.extend(
        [
            "",
            "## FUTURE ONLY / DO NOT RUN YET",
            "",
        ]
    )
    outline = _as_mapping(report.get("future_windows_task_scheduler_command_outline"))
    for command in outline.get("command_outline", []):
        lines.append(f"- `{command}`")
    lines.extend(
        [
            "",
            "## Safe Staged Activation",
            "",
        ]
    )
    for stage in report.get("staged_activation_plan", []):
        lines.append(f"- {stage['stage']}. {stage['name']}: {stage['description']}")
    lines.extend(
        [
            "",
            "## Safety",
            "",
            "This scheduler plan only reads local queue/report artifacts and writes reports. It does not register Windows Task Scheduler jobs, start background workers, execute Codex, call Codex app-server, create branches, create worktrees, call network services, or access credentials.",
            "",
        ]
    )
    if report.get("warnings"):
        lines.extend(["## Warnings", ""])
        lines.extend(f"- {warning}" for warning in report.get("warnings", []))
        lines.append("")
    return "\n".join(lines)


def _required_safety_gates(
    latest_night: Mapping[str, Any],
    latest_lock: Mapping[str, Any],
    latest_morning: Mapping[str, Any],
    latest_ingestion: Mapping[str, Any],
) -> list[dict[str, Any]]:
    night_payload = _as_mapping(latest_night.get("payload"))
    return [
        _gate("queue_health_available", True, "Queue health can be collected locally."),
        _gate(
            "night_dry_run_available",
            latest_night.get("found") is True,
            "Latest night dry-run report exists.",
            latest_night.get("path"),
        ),
        _gate(
            "git_safety_available",
            bool(night_payload.get("git_state")),
            "Night dry-run includes git safety inspection.",
            latest_night.get("path"),
        ),
        _gate(
            "result_ingestion_available",
            True,
            "Result ingestion command exists and remains operator-invoked.",
            latest_ingestion.get("path") if latest_ingestion.get("found") else None,
        ),
        _gate(
            "morning_report_available",
            latest_morning.get("found") is True,
            "Latest morning report exists.",
            latest_morning.get("path"),
        ),
        _gate("max_task_cap", True, "Night dry-run requires a max task cap."),
        _gate(
            "lock_file_discipline",
            latest_lock.get("found") is True,
            "Night runner lock-check report exists.",
            latest_lock.get("path"),
        ),
        _gate("no_network_by_default", True, "Future scheduler must not call network by default."),
        _gate("no_credentials", True, "Future scheduler must not access credentials."),
        _gate(
            "no_automatic_codex_execution_without_approval",
            True,
            "Future scheduler must not execute Codex unless separately approved.",
        ),
        _gate(
            "explicit_operator_approval",
            False,
            "Real scheduler registration requires an explicit future operator approval task.",
        ),
    ]


def _gate(
    gate_id: str,
    satisfied: bool,
    description: str,
    evidence_path: str | None = None,
) -> dict[str, Any]:
    return {
        "gate_id": gate_id,
        "satisfied": bool(satisfied),
        "description": description,
        "evidence_path": evidence_path,
    }


def _future_windows_task_scheduler_outline() -> dict[str, Any]:
    base_command = (
        "python -m ai_orchestrator.codex_queue.operator_cli night-dry-run "
        "--queue-root agent_tasks --max-tasks 5"
    )
    return {
        "future_only": True,
        "do_not_run_yet": True,
        "scheduler_registered_now": False,
        "description": "Future manual outline for a dry-run-only Windows Task Scheduler entry.",
        "command_outline": [
            "FUTURE ONLY / DO NOT RUN YET",
            (
                'schtasks /Create /TN "AI-Orchestrator Night Dry Run" /SC DAILY /ST 02:00 '
                f'/TR "powershell.exe -NoProfile -Command '
                f"'Set-Location C:\\Users\\OpenC\\.openclaw\\workspace; {base_command}'" + '"'
            ),
        ],
    }


def _staged_activation_plan() -> list[dict[str, Any]]:
    return [
        {
            "stage": 1,
            "name": "manual_dry_run",
            "description": "Run night-dry-run manually and inspect JSON/Markdown reports.",
        },
        {
            "stage": 2,
            "name": "scheduled_dry_run_only",
            "description": "Only after explicit approval, run night-dry-run through Windows Task Scheduler with no Codex execution.",
        },
        {
            "stage": 3,
            "name": "scheduled_morning_report_only",
            "description": "Consider a scheduled morning report after dry-run scheduling proves stable.",
        },
        {
            "stage": 4,
            "name": "controlled_execution_after_approval",
            "description": "Only later, and only after separate explicit approval, consider controlled execution.",
        },
    ]


def _scheduler_warnings(gates: list[Mapping[str, Any]]) -> list[str]:
    warnings = []
    missing = [str(gate["gate_id"]) for gate in gates if not gate.get("satisfied")]
    if missing:
        warnings.append(
            "real scheduler activation remains blocked until these gates are satisfied: "
            + ", ".join(missing)
        )
    warnings.append("no scheduler was registered by this command")
    return warnings


def _latest_report(root: Path, filename: str) -> dict[str, Any]:
    path = safe_queue_path(root, "reports", filename)
    if not path.exists():
        return {"found": False, "path": str(path), "payload": None, "errors": []}
    try:
        payload = read_json(path)
    except (OSError, json.JSONDecodeError) as exc:
        return {"found": True, "path": str(path), "payload": None, "errors": [str(exc)]}
    return {
        "found": True,
        "path": str(path),
        "payload": payload if isinstance(payload, Mapping) else None,
        "errors": [] if isinstance(payload, Mapping) else ["report payload is not an object"],
    }


def _report_ref(report: Mapping[str, Any]) -> dict[str, Any]:
    payload = _as_mapping(report.get("payload"))
    return {
        "found": bool(report.get("found")),
        "path": report.get("path") if report.get("found") else None,
        "schema_version": payload.get("schema_version"),
        "status": payload.get("status"),
        "errors": list(report.get("errors", [])),
    }


def _health_summary(health: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": health.get("schema_version"),
        "run_id": health.get("run_id"),
        "counts": health.get("counts", {}),
        "artifact_counts": health.get("artifact_counts", {}),
        "next_action_counts": health.get("next_action_counts", {}),
        "blocked_tasks_count": health.get("blocked_tasks_count", 0),
        "done_tasks_count": health.get("done_tasks_count", 0),
    }


def _as_mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _run_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _utc_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
