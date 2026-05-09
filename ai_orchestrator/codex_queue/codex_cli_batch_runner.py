from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

from .codex_cli_runner import DEFAULT_TIMEOUT_SECONDS, run_codex_once
from .files import (
    ensure_queue_directories,
    find_task_packet,
    read_json,
    safe_existing_path_under_queue,
    safe_queue_path,
    validate_task_id,
    write_json_atomic,
    write_text_atomic,
)
from .git_safety import inspect_git_state
from .safety import classify_packet
from .validator import validate_packet

BATCH_REPORT_SCHEMA_VERSION = "codex_cli_batch_execution_report.v1"
DEFAULT_MAX_TASKS = 10
HARD_MAX_TASKS = 20
READY_STATES = ("approved", "planned")


def run_codex_batch(
    queue_root: str | Path = "agent_tasks",
    *,
    max_tasks: int = DEFAULT_MAX_TASKS,
    dry_run: bool = False,
    task_ids: Sequence[str] | None = None,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    root = ensure_queue_directories(queue_root)
    run_id = _run_id()
    report = _base_report(
        root=root,
        run_id=run_id,
        max_tasks=max_tasks,
        dry_run=dry_run,
        task_ids=task_ids,
        timeout_seconds=timeout_seconds,
    )

    if max_tasks <= 0:
        report["errors"].append("max_tasks must be greater than zero")
    if max_tasks > HARD_MAX_TASKS:
        report["errors"].append(f"max_tasks must be {HARD_MAX_TASKS} or fewer")
    if timeout_seconds <= 0:
        report["errors"].append("timeout_seconds must be greater than zero")

    requested_task_ids: list[str] | None = None
    if task_ids:
        requested_task_ids = []
        for task_id in task_ids:
            try:
                requested_task_ids.append(validate_task_id(task_id))
            except ValueError as exc:
                report["errors"].append(f"invalid task_id {task_id!r}: {exc}")

    if report["errors"]:
        report["status"] = "blocked"
        report["next_operator_action"] = "Fix batch arguments, then rerun run-codex-batch --dry-run."
        return _write_batch_report(root, report)

    candidates = _collect_candidates(root, requested_task_ids)
    selected: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    for candidate in candidates:
        report["task_order"].append(candidate["task_id"])
        if candidate["eligible"]:
            if len(selected) < max_tasks:
                selected.append(candidate)
            else:
                skipped.append(_skip_from_candidate(candidate, "beyond max_tasks cap"))
        else:
            skipped.append(_skip_from_candidate(candidate, candidate["reason"]))

    report["selected_task_ids"] = [candidate["task_id"] for candidate in selected]
    report["skipped_task_ids"] = [entry["task_id"] for entry in skipped]
    report["skipped_tasks"] = skipped
    report["selected_tasks"] = [_selected_task_summary(root, candidate, dry_run, timeout_seconds) for candidate in selected]

    if not selected:
        report["status"] = "ok" if dry_run else "blocked"
        report["next_operator_action"] = "Approve and plan eligible tasks, then rerun run-codex-batch --dry-run."
        return _write_batch_report(root, report)

    if dry_run:
        report["status"] = "ok"
        report["execution_status"] = "dry_run"
        report["would_invoke_one_task_runner_count"] = len(selected)
        report["next_operator_action"] = (
            "Review selected task order and one-task runner commands, then run without --dry-run only under supervision."
        )
        return _write_batch_report(root, report)

    report["execution_status"] = "running"
    git_baselines: dict[str, dict[str, Any]] = {}
    for candidate in selected:
        preflight = _inspect_git_before_task(candidate, git_baselines)
        report["git_preflight_checks"].append(preflight)
        if preflight.get("baseline_recorded"):
            report["git_baseline_checks"].append(
                {
                    "repo_root": preflight["repo_root"],
                    "task_id": candidate["task_id"],
                    "git_state": preflight["git_state"],
                }
            )
        if preflight["blocked"]:
            report["status"] = "blocked"
            report["execution_status"] = "stopped_before_task"
            report["stopped_on_task_id"] = candidate["task_id"]
            report["stopped_reason"] = preflight["reason"]
            report["errors"].append(preflight["reason"])
            report["next_operator_action"] = (
                "Resolve the git working tree state, then rerun run-codex-batch --dry-run before continuing."
            )
            return _write_batch_report(root, report)

        task_report = run_codex_once(
            root,
            task_id=candidate["task_id"],
            dry_run=False,
            timeout_seconds=timeout_seconds,
        )
        execution = _task_execution_summary(task_report)
        report["task_executions"].append(execution)
        report["one_task_runner_invocation_count"] += 1
        report["codex_invocation_count"] += int(task_report.get("codex_invocation_count") or 0)
        report["codex_exec_invoked"] = report["codex_exec_invoked"] or bool(task_report.get("codex_exec_invoked"))

        if task_report.get("status") != "ok":
            report["status"] = str(task_report.get("status") or "failed")
            report["execution_status"] = "stopped_after_task_failure"
            report["stopped_on_task_id"] = candidate["task_id"]
            report["stopped_reason"] = f"one-task runner returned status {task_report.get('status')}"
            report["errors"].extend(str(error) for error in task_report.get("errors", []))
            report["next_operator_action"] = (
                "Inspect the failed task execution report and logs; do not continue the batch until resolved."
            )
            return _write_batch_report(root, report)

    report["status"] = "ok"
    report["execution_status"] = "completed"
    report["next_operator_action"] = (
        "Inspect each Codex execution report and result JSON, then run ingest-result and review explicitly for each task."
    )
    return _write_batch_report(root, report)


def render_batch_report_markdown(report: Mapping[str, Any]) -> str:
    lines = [
        "# Codex CLI Batch Execution",
        "",
        f"- status: `{report['status']}`",
        f"- execution_status: `{report['execution_status']}`",
        f"- dry_run: `{report['dry_run']}`",
        f"- run_id: `{report['run_id']}`",
        f"- queue_root: `{report['queue_root']}`",
        f"- max_tasks: `{report['max_tasks']}`",
        f"- hard_max_tasks: `{report['hard_max_tasks']}`",
        f"- selected_count: `{len(report.get('selected_task_ids', []))}`",
        f"- skipped_count: `{len(report.get('skipped_task_ids', []))}`",
        f"- stopped_on_task_id: `{report.get('stopped_on_task_id')}`",
        "",
        "## Selected Tasks",
        "",
    ]
    selected_tasks = list(report.get("selected_tasks", []))
    if not selected_tasks:
        lines.append("- No tasks selected.")
    for index, task in enumerate(selected_tasks, start=1):
        lines.append(f"{index}. `{task['task_id']}`")
        lines.append(f"   - state: `{task.get('state')}`")
        lines.append(f"   - task_packet: `{task.get('task_packet_path')}`")
        lines.append(f"   - plan: `{task.get('plan_path')}`")
        lines.append(f"   - handoff_prompt: `{task.get('handoff_prompt_path')}`")
        lines.append(f"   - dry_run_command: `{task.get('one_task_dry_run_command')}`")
        lines.append(f"   - execution_command: `{task.get('one_task_execution_command')}`")
    lines.extend(["", "## Skipped Tasks", ""])
    skipped_tasks = list(report.get("skipped_tasks", []))
    if not skipped_tasks:
        lines.append("- No tasks skipped.")
    for skipped in skipped_tasks:
        lines.append(f"- `{skipped['task_id']}`: {skipped['reason']}")
    lines.extend(["", "## Task Executions", ""])
    executions = list(report.get("task_executions", []))
    if not executions:
        lines.append("- No task executions were performed.")
    for execution in executions:
        lines.append(
            f"- `{execution['task_id']}`: status `{execution['status']}`, "
            f"execution_status `{execution['execution_status']}`, exit_code `{execution.get('exit_code')}`"
        )
        if execution.get("execution_report_json"):
            lines.append(f"  - report: `{execution['execution_report_json']}`")
    if report.get("errors"):
        lines.extend(["", "## Errors", ""])
        lines.extend(f"- {error}" for error in report["errors"])
    if report.get("warnings"):
        lines.extend(["", "## Warnings", ""])
        lines.extend(f"- {warning}" for warning in report["warnings"])
    lines.extend(
        [
            "",
            "## Safety",
            "",
            "This is a manually invoked, bounded, supervised batch command. It never creates tasks, approves tasks, marks tasks done, ingests results, reviews results, commits, pushes, schedules itself, starts a daemon, or starts a background worker.",
            "",
            f"Next operator action: {report['next_operator_action']}",
            "",
        ]
    )
    return "\n".join(lines)


def _collect_candidates(root: Path, requested_task_ids: Sequence[str] | None) -> list[dict[str, Any]]:
    ordered_ids = list(requested_task_ids) if requested_task_ids else _planned_queue_order(root)
    return [_candidate_for_task_id(root, task_id) for task_id in ordered_ids]


def _planned_queue_order(root: Path) -> list[str]:
    ordered: list[str] = []
    seen: set[str] = set()
    for plan_path in sorted(safe_queue_path(root, "planned").glob("*.plan.json")):
        task_id = plan_path.name[: -len(".plan.json")]
        if _add_task_id(ordered, seen, task_id):
            continue
    for state in READY_STATES:
        for packet_path in sorted(safe_queue_path(root, state).glob("*.json")):
            task_id = _task_id_from_packet_or_name(packet_path)
            if task_id:
                _add_task_id(ordered, seen, task_id)
    return ordered


def _candidate_for_task_id(root: Path, task_id: str) -> dict[str, Any]:
    safe_task_id = validate_task_id(task_id)
    base: dict[str, Any] = {
        "task_id": safe_task_id,
        "eligible": False,
        "reason": "",
        "state": None,
        "task_packet_path": None,
        "plan_path": None,
        "handoff_prompt_path": None,
        "task_packet": None,
        "errors": [],
        "warnings": [],
    }
    match = find_task_packet(root, safe_task_id, states=READY_STATES)
    if not match["found"]:
        base["reason"] = "no approved/planned task packet found"
        base["errors"].extend(match.get("errors", []))
        return base

    packet = dict(match["packet"])
    base["state"] = match["state"]
    base["task_packet_path"] = str(match["path"])
    base["task_packet"] = packet
    if packet.get("status") not in READY_STATES:
        base["reason"] = f"task status is not approved/planned: {packet.get('status')}"
        return base

    validation = validate_packet(packet)
    classification = _classify_for_batch(packet, validation)
    base["validation"] = validation.to_dict()
    base["classification"] = classification.to_dict()
    if not validation.valid:
        base["reason"] = "task packet validation failed"
        base["errors"].extend(validation.errors)
        return base
    if not classification.allowed:
        base["reason"] = f"task safety classification is not allowed: {classification.status}"
        base["errors"].extend(classification.reasons)
        return base

    result_path = safe_queue_path(root, "review", f"{safe_task_id}.result.json")
    if result_path.exists():
        base["reason"] = f"result packet already exists: {result_path}"
        return base

    plan_path = safe_queue_path(root, "planned", f"{safe_task_id}.plan.json")
    if not plan_path.exists():
        base["reason"] = f"matching plan is required: {plan_path}"
        return base
    base["plan_path"] = str(plan_path)
    plan_payload = _read_plan(root, plan_path, base)
    if not plan_payload:
        if not base["reason"]:
            base["reason"] = f"plan must be a JSON object: {plan_path}"
        return base
    if plan_payload.get("task_id") != safe_task_id:
        base["reason"] = f"plan task_id does not match {safe_task_id}: {plan_payload.get('task_id')}"
        return base

    handoff_path = _handoff_path_from_plan(root, safe_task_id, plan_payload, base)
    if handoff_path is None:
        return base
    base["handoff_prompt_path"] = str(handoff_path)
    if not handoff_path.exists():
        base["reason"] = f"matching handoff prompt is required: {handoff_path}"
        return base

    base["eligible"] = True
    base["reason"] = "approved/planned task has matching plan and handoff prompt"
    return base


def _read_plan(root: Path, plan_path: Path, candidate: dict[str, Any]) -> dict[str, Any] | None:
    try:
        payload = read_json(plan_path)
    except json.JSONDecodeError as exc:
        candidate["reason"] = f"invalid plan JSON: {exc}"
        return None
    if not isinstance(payload, Mapping):
        return None
    return dict(payload)


def _handoff_path_from_plan(
    root: Path,
    task_id: str,
    plan_payload: Mapping[str, Any],
    candidate: dict[str, Any],
) -> Path | None:
    raw_handoff_path = plan_payload.get("handoff_prompt_path")
    if isinstance(raw_handoff_path, str) and raw_handoff_path.strip():
        try:
            return safe_existing_path_under_queue(root, raw_handoff_path)
        except ValueError as exc:
            candidate["reason"] = str(exc)
            return None
    return safe_queue_path(root, "planned", f"{task_id}.handoff_prompt.md")


def _selected_task_summary(
    root: Path,
    candidate: Mapping[str, Any],
    dry_run: bool,
    timeout_seconds: int,
) -> dict[str, Any]:
    task_id = str(candidate["task_id"])
    return {
        "task_id": task_id,
        "state": candidate.get("state"),
        "task_packet_path": candidate.get("task_packet_path"),
        "plan_path": candidate.get("plan_path"),
        "handoff_prompt_path": candidate.get("handoff_prompt_path"),
        "one_task_dry_run_command": _operator_command(root, task_id, timeout_seconds, dry_run=True),
        "one_task_execution_command": _operator_command(root, task_id, timeout_seconds, dry_run=False),
        "batch_mode_command": _operator_command(root, task_id, timeout_seconds, dry_run=dry_run),
    }


def _operator_command(root: Path, task_id: str, timeout_seconds: int, *, dry_run: bool) -> str:
    argv = [
        "python",
        "-m",
        "ai_orchestrator.codex_queue.operator_cli",
        "run-codex-once",
        "--queue-root",
        str(root),
        "--task-id",
        task_id,
    ]
    if dry_run:
        argv.append("--dry-run")
    else:
        argv.extend(["--timeout-seconds", str(timeout_seconds)])
    return subprocess.list2cmdline(argv)


def _inspect_git_before_task(
    candidate: Mapping[str, Any],
    git_baselines: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    repo_root = _repo_root_from_packet(candidate.get("task_packet"))
    repo_key = str(repo_root)
    git_state = inspect_git_state(str(repo_root))
    signature = _git_state_signature(git_state)
    baseline_recorded = False
    if repo_key not in git_baselines:
        git_baselines[repo_key] = {
            "signature": signature,
            "git_state": git_state,
        }
        baseline_recorded = True
    baseline_signature = git_baselines[repo_key]["signature"]
    changed_since_baseline = signature != baseline_signature
    blocked = bool(git_state.get("errors")) or changed_since_baseline
    reason = ""
    if git_state.get("errors"):
        reason = "; ".join(str(error) for error in git_state.get("errors", []))
    elif changed_since_baseline:
        reason = "git working tree changed since batch start before task execution"
    return {
        "task_id": candidate["task_id"],
        "repo_root": repo_key,
        "blocked": blocked,
        "reason": reason,
        "baseline_recorded": baseline_recorded,
        "changed_since_baseline": changed_since_baseline,
        "git_state": git_state,
    }


def _git_state_signature(git_state: Mapping[str, Any]) -> tuple[str, ...]:
    return tuple(str(line) for line in git_state.get("status_lines", []))


def _task_execution_summary(task_report: Mapping[str, Any]) -> dict[str, Any]:
    report_paths = task_report.get("report_paths", {})
    return {
        "task_id": task_report.get("task_id"),
        "status": task_report.get("status"),
        "execution_status": task_report.get("execution_status"),
        "exit_code": task_report.get("exit_code"),
        "execution_report_json": report_paths.get("execution_report_json") if isinstance(report_paths, Mapping) else None,
        "execution_report_md": report_paths.get("execution_report_md") if isinstance(report_paths, Mapping) else None,
        "stdout_log": report_paths.get("stdout_log") if isinstance(report_paths, Mapping) else None,
        "stderr_log": report_paths.get("stderr_log") if isinstance(report_paths, Mapping) else None,
        "next_operator_action": task_report.get("next_operator_action"),
        "errors": list(task_report.get("errors", [])),
        "warnings": list(task_report.get("warnings", [])),
    }


def _skip_from_candidate(candidate: Mapping[str, Any], reason: str) -> dict[str, Any]:
    return {
        "task_id": candidate["task_id"],
        "state": candidate.get("state"),
        "reason": reason,
        "task_packet_path": candidate.get("task_packet_path"),
        "plan_path": candidate.get("plan_path"),
        "handoff_prompt_path": candidate.get("handoff_prompt_path"),
        "errors": list(candidate.get("errors", [])),
        "warnings": list(candidate.get("warnings", [])),
    }


def _base_report(
    *,
    root: Path,
    run_id: str,
    max_tasks: int,
    dry_run: bool,
    task_ids: Sequence[str] | None,
    timeout_seconds: int,
) -> dict[str, Any]:
    return {
        "schema_version": BATCH_REPORT_SCHEMA_VERSION,
        "run_id": run_id,
        "queue_root": str(root),
        "status": "blocked",
        "execution_status": "blocked",
        "dry_run": dry_run,
        "started_at": _utc_iso(),
        "ended_at": None,
        "max_tasks": max_tasks,
        "hard_max_tasks": HARD_MAX_TASKS,
        "timeout_seconds": timeout_seconds,
        "requested_task_ids": list(task_ids or []),
        "task_order": [],
        "selected_task_ids": [],
        "selected_tasks": [],
        "skipped_task_ids": [],
        "skipped_tasks": [],
        "task_executions": [],
        "git_baseline_checks": [],
        "git_preflight_checks": [],
        "stopped_on_task_id": None,
        "stopped_reason": "",
        "one_task_runner_invocation_count": 0,
        "would_invoke_one_task_runner_count": 0,
        "codex_exec_invoked": False,
        "codex_invocation_count": 0,
        "result_ingested_automatically": False,
        "task_marked_done_automatically": False,
        "review_approved_automatically": False,
        "git_commit_performed": False,
        "git_push_performed": False,
        "scheduler_created": False,
        "daemon_created": False,
        "background_worker_created": False,
        "infinite_loop_created": False,
        "task_created_automatically": False,
        "task_approved_automatically": False,
        "network_calls_performed": 0,
        "openrouter_calls_performed": 0,
        "polymarket_api_calls_performed": 0,
        "wallet_or_private_key_access": False,
        "orders_or_trading_actions": False,
        "runtime_or_dispatcher_changes": False,
        "errors": [],
        "warnings": [],
        "next_operator_action": "",
        "report_paths": {},
    }


def _write_batch_report(root: Path, report: dict[str, Any]) -> dict[str, Any]:
    payload = dict(report)
    payload["ended_at"] = _utc_iso()
    reports_dir = safe_queue_path(root, "reports")
    json_path = reports_dir / f"codex_cli_batch_report_{payload['run_id']}.json"
    md_path = reports_dir / f"codex_cli_batch_report_{payload['run_id']}.md"
    latest_json_path = reports_dir / "latest_codex_cli_batch_report.json"
    latest_md_path = reports_dir / "latest_codex_cli_batch_report.md"
    payload["report_paths"] = {
        "batch_report_json": str(json_path),
        "batch_report_md": str(md_path),
        "latest_batch_report_json": str(latest_json_path),
        "latest_batch_report_md": str(latest_md_path),
    }
    write_json_atomic(json_path, payload)
    write_text_atomic(md_path, render_batch_report_markdown(payload))
    write_json_atomic(latest_json_path, payload)
    write_text_atomic(latest_md_path, render_batch_report_markdown(payload))
    return payload


def _classify_for_batch(packet: Mapping[str, Any], validation: Any) -> Any:
    if packet.get("status") != "planned":
        return classify_packet(packet, validation)
    approved_view = dict(packet)
    approved_view["status"] = "approved"
    return classify_packet(approved_view, validation)


def _repo_root_from_packet(packet: Any) -> Path:
    if isinstance(packet, Mapping):
        repo = packet.get("repo", {})
        if isinstance(repo, Mapping):
            repo_root = repo.get("repo_root")
            if isinstance(repo_root, str) and repo_root.strip():
                return Path(repo_root).resolve(strict=False)
    return Path(".").resolve(strict=False)


def _task_id_from_packet_or_name(packet_path: Path) -> str | None:
    try:
        payload = read_json(packet_path)
    except json.JSONDecodeError:
        return _task_id_from_name(packet_path.name, ".task.json")
    if isinstance(payload, Mapping):
        task_id = payload.get("task_id")
        if isinstance(task_id, str):
            return task_id
    return _task_id_from_name(packet_path.name, ".task.json")


def _task_id_from_name(name: str, suffix: str) -> str | None:
    if not name.endswith(suffix):
        return None
    return name[: -len(suffix)]


def _add_task_id(ordered: list[str], seen: set[str], task_id: str | None) -> bool:
    if not task_id:
        return False
    try:
        safe_task_id = validate_task_id(task_id)
    except ValueError:
        return False
    if safe_task_id in seen:
        return True
    seen.add(safe_task_id)
    ordered.append(safe_task_id)
    return True


def _run_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _utc_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
