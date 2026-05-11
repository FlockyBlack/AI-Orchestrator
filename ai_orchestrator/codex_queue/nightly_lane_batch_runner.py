from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from .codex_cli_runner import DEFAULT_TIMEOUT_SECONDS, run_codex_once
from .files import ensure_queue_directories, read_json, safe_queue_path, validate_task_id, write_json_atomic, write_text_atomic
from .git_safety import inspect_git_state
from .subagent_routing import route_from_task_payload
from .worktree_lane_manager import (
    create_task_worktree_lane,
    inspect_task_worktree_lane,
    plan_task_worktree_lane,
    write_lane_state_artifacts,
)

NIGHTLY_LANE_BATCH_PLAN_SCHEMA_VERSION = "nightly_lane_batch_plan.v1"
NIGHTLY_LANE_BATCH_REPORT_SCHEMA_VERSION = "nightly_lane_batch_report.v1"

LANE_MODES = {"plan_only", "create_or_reuse"}
EXECUTOR_MODES = {"fake", "codex_cli_dry_run", "codex_cli"}
STOP_POLICIES = {"stop_on_first_blocker", "continue_on_task_blocker"}
DEFAULT_EXECUTOR_MODE = "fake"
DEFAULT_LANE_MODE = "create_or_reuse"
DEFAULT_STOP_POLICY = "stop_on_first_blocker"
DEFAULT_MAX_STEPS_PER_TASK = 1
HARD_MAX_STEPS_PER_TASK = 5

REQUIRED_TRUE_SAFETY_FLAGS = (
    "no_scheduler",
    "no_daemon",
    "no_background_worker",
    "no_autonomous_trading",
    "no_wallet_signing_or_orders",
    "no_external_apis",
    "no_browser_automation",
)


def validate_nightly_lane_batch_plan(payload: Mapping[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    if not isinstance(payload, Mapping):
        return {
            "valid": False,
            "errors": ["batch plan must be a JSON object"],
            "warnings": [],
            "plan": {},
        }

    batch_id = _safe_artifact_id(str(payload.get("batch_id") or ""), field_name="batch_id", errors=errors)
    expected_base_head = str(payload.get("expected_base_head") or "").strip()
    if not expected_base_head:
        errors.append("expected_base_head is required")
    expected_base_branch = str(payload.get("expected_base_branch") or "master").strip() or "master"

    lane_mode = str(payload.get("lane_mode") or DEFAULT_LANE_MODE).strip()
    if lane_mode not in LANE_MODES:
        errors.append(f"lane_mode must be one of {sorted(LANE_MODES)}")
        lane_mode = DEFAULT_LANE_MODE

    executor_mode = str(payload.get("executor_mode") or DEFAULT_EXECUTOR_MODE).strip()
    if executor_mode == "dry_run":
        executor_mode = "codex_cli_dry_run"
    if executor_mode not in EXECUTOR_MODES:
        errors.append(f"executor_mode must be one of {sorted(EXECUTOR_MODES)}")
        executor_mode = DEFAULT_EXECUTOR_MODE

    stop_policy = str(payload.get("stop_policy") or DEFAULT_STOP_POLICY).strip()
    if stop_policy not in STOP_POLICIES:
        errors.append(f"stop_policy must be one of {sorted(STOP_POLICIES)}")
        stop_policy = DEFAULT_STOP_POLICY

    max_steps = _int_range(
        payload.get("max_steps_per_task", DEFAULT_MAX_STEPS_PER_TASK),
        "max_steps_per_task",
        minimum=1,
        maximum=HARD_MAX_STEPS_PER_TASK,
        errors=errors,
    )

    safety_flags = payload.get("safety_flags")
    if not isinstance(safety_flags, Mapping):
        errors.append("safety_flags must be an object")
        safety_flags = {}
    for flag in REQUIRED_TRUE_SAFETY_FLAGS:
        if safety_flags.get(flag) is not True:
            errors.append(f"safety_flags.{flag} must be true")

    allow_real = bool(payload.get("allow_real_codex_invocation", False))
    if executor_mode == "codex_cli" and not allow_real:
        warnings.append("executor_mode codex_cli is configured but allow_real_codex_invocation is false")
    if allow_real and executor_mode != "codex_cli":
        warnings.append("allow_real_codex_invocation is true but executor_mode is not codex_cli")

    raw_tasks = payload.get("tasks")
    if not isinstance(raw_tasks, list) or not raw_tasks:
        errors.append("tasks must be a non-empty list")
        raw_tasks = []

    tasks: list[dict[str, Any]] = []
    seen_task_ids: set[str] = set()
    for index, raw_task in enumerate(raw_tasks, start=1):
        if not isinstance(raw_task, Mapping):
            errors.append(f"tasks[{index}] must be an object")
            continue
        raw_task_id = str(raw_task.get("task_id") or "")
        try:
            task_id = validate_task_id(raw_task_id)
        except ValueError as exc:
            errors.append(f"tasks[{index}].task_id is invalid: {exc}")
            continue
        if task_id in seen_task_ids:
            errors.append(f"duplicate task_id in batch plan: {task_id}")
        seen_task_ids.add(task_id)
        task_executor = str(raw_task.get("executor_mode") or executor_mode).strip()
        if task_executor == "dry_run":
            task_executor = "codex_cli_dry_run"
        if task_executor not in EXECUTOR_MODES:
            errors.append(f"tasks[{index}].executor_mode must be one of {sorted(EXECUTOR_MODES)}")
            task_executor = executor_mode
        task_steps = _int_range(
            raw_task.get("max_steps", max_steps),
            f"tasks[{index}].max_steps",
            minimum=1,
            maximum=max_steps,
            errors=errors,
        )
        tasks.append(
            {
                "task_id": task_id,
                "task_category": str(raw_task.get("task_category") or raw_task.get("category") or ""),
                "title": str(raw_task.get("title") or ""),
                "description": str(raw_task.get("description") or raw_task.get("summary") or ""),
                "allowed_paths": [str(value) for value in raw_task.get("allowed_paths", []) if str(value)],
                "executor_mode": task_executor,
                "max_steps": task_steps,
            }
        )

    plan = {
        "schema_version": str(payload.get("schema_version") or NIGHTLY_LANE_BATCH_PLAN_SCHEMA_VERSION),
        "batch_id": batch_id,
        "repo_root": str(payload.get("repo_root") or "."),
        "queue_root": str(payload.get("queue_root") or "agent_tasks"),
        "expected_base_branch": expected_base_branch,
        "expected_base_head": expected_base_head,
        "lane_root": str(payload.get("lane_root") or ""),
        "lane_mode": lane_mode,
        "max_steps_per_task": max_steps,
        "executor_mode": executor_mode,
        "allow_real_codex_invocation": allow_real,
        "stop_policy": stop_policy,
        "safety_flags": {flag: bool(safety_flags.get(flag)) for flag in REQUIRED_TRUE_SAFETY_FLAGS},
        "tasks": tasks,
    }
    if plan["schema_version"] != NIGHTLY_LANE_BATCH_PLAN_SCHEMA_VERSION:
        errors.append(f"schema_version must be {NIGHTLY_LANE_BATCH_PLAN_SCHEMA_VERSION}")

    return {
        "valid": not errors,
        "errors": errors,
        "warnings": warnings,
        "plan": plan,
    }


def run_nightly_lane_batch(
    plan_file: str | Path,
    *,
    queue_root: str | Path | None = None,
    repo_root: str | Path | None = None,
    dry_run: bool = False,
    allow_real_codex_invocation: bool = False,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    raw_plan = _read_plan_json(plan_file)
    fallback_queue_root = queue_root or _payload_string(raw_plan, "queue_root") or "agent_tasks"
    root = ensure_queue_directories(fallback_queue_root)
    run_id = _run_id()
    started_at = _utc_iso()
    validation = validate_nightly_lane_batch_plan(raw_plan if isinstance(raw_plan, Mapping) else {})
    plan = dict(validation["plan"])
    if queue_root is not None:
        plan["queue_root"] = str(root)
    repo = Path(repo_root or plan.get("repo_root") or ".").resolve(strict=False)
    if repo_root is not None:
        plan["repo_root"] = str(repo)
    if dry_run:
        plan["lane_mode"] = "plan_only"
        plan["executor_mode"] = "fake"

    report = _base_report(
        plan_file=plan_file,
        queue_root=root,
        repo=repo,
        run_id=run_id,
        started_at=started_at,
        plan=plan,
        validation=validation,
        dry_run=dry_run,
        allow_real_codex_invocation=allow_real_codex_invocation,
        timeout_seconds=timeout_seconds,
    )

    if not validation["valid"]:
        report["status"] = "blocked"
        report["execution_status"] = "blocked_plan_validation"
        report["errors"].extend(validation["errors"])
        report["warnings"].extend(validation["warnings"])
        report["next_operator_action"] = "Fix the nightly lane batch plan contract, then rerun with the fake executor first."
        return _write_batch_report(root, report)

    report["warnings"].extend(validation["warnings"])
    repo_preflight = _repo_preflight(repo, plan)
    report["repo_preflight"] = repo_preflight
    report["warnings"].extend(repo_preflight["warnings"])
    if repo_preflight["errors"]:
        report["status"] = "blocked"
        report["execution_status"] = "blocked_repo_preflight"
        report["errors"].extend(repo_preflight["errors"])
        report["blocker_reason"] = repo_preflight["errors"][0]
        report["next_operator_action"] = "Resolve the repository base, branch, or dirty-tree blocker before running the batch."
        return _write_batch_report(root, report)

    if timeout_seconds <= 0:
        report["status"] = "blocked"
        report["execution_status"] = "blocked_plan_validation"
        report["errors"].append("timeout_seconds must be greater than zero")
        report["next_operator_action"] = "Use a positive timeout_seconds value."
        return _write_batch_report(root, report)

    for task in plan["tasks"]:
        task_report = _run_one_task(
            root,
            repo,
            plan,
            task,
            repo_git_state=repo_preflight["git_state"],
            dry_run=dry_run,
            allow_real_codex_invocation=allow_real_codex_invocation,
            timeout_seconds=timeout_seconds,
        )
        report["tasks"].append(task_report)
        _accumulate_task_counts(report, task_report)
        if task_report.get("codex_invoked"):
            report["codex_invocation_count"] += int(task_report.get("codex_invocation_count") or 0)
        if _should_stop_after_task(plan["stop_policy"], task_report):
            report["stopped_on_task_id"] = task_report["task_id"]
            report["blocker_reason"] = task_report.get("blocker_reason") or task_report.get("status")
            break

    report["task_count"] = len(report["tasks"])
    report["status"] = _overall_status(report, dry_run=dry_run)
    report["execution_status"] = _execution_status(report, dry_run=dry_run)
    report["next_operator_action"] = _next_operator_action(report)
    return _write_batch_report(root, report)


def render_nightly_lane_batch_markdown(report: Mapping[str, Any]) -> str:
    safety = report.get("safety_summary", {}) if isinstance(report.get("safety_summary"), Mapping) else {}
    lines = [
        "# Nightly Lane Batch Report",
        "",
        f"- status: `{report.get('status')}`",
        f"- execution_status: `{report.get('execution_status')}`",
        f"- batch_id: `{report.get('batch_id')}`",
        f"- run_id: `{report.get('run_id')}`",
        f"- dry_run: `{report.get('dry_run')}`",
        f"- lane_mode: `{report.get('lane_mode')}`",
        f"- executor_mode: `{report.get('executor_mode')}`",
        f"- task_count: `{report.get('task_count')}`",
        f"- completed_count: `{report.get('completed_count')}`",
        f"- blocked_count: `{report.get('blocked_count')}`",
        f"- failed_count: `{report.get('failed_count')}`",
        f"- stopped_on_task_id: `{report.get('stopped_on_task_id')}`",
        "",
        "## Tasks",
        "",
    ]
    tasks = list(report.get("tasks", []))
    if not tasks:
        lines.append("- No tasks executed.")
    for index, task in enumerate(tasks, start=1):
        lines.extend(
            [
                f"{index}. `{task.get('task_id')}`",
                f"   - status: `{task.get('status')}`",
                f"   - lane_path: `{task.get('lane_path')}`",
                f"   - branch: `{task.get('branch')}`",
                f"   - selected_subagent: `{task.get('selected_subagent')}`",
                f"   - safety_flags: `{_safety_flags_text(task.get('safety_flags'))}`",
                f"   - test_summary: `{_summary_text(task.get('test_summary'))}`",
                f"   - blocker_reason: `{task.get('blocker_reason') or 'none'}`",
                f"   - next_action: {task.get('next_action')}",
            ]
        )
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
            f"- no_daemon_or_scheduler_added: `{safety.get('no_daemon_or_scheduler_added')}`",
            f"- no_background_worker_added: `{safety.get('no_background_worker_added')}`",
            f"- wallet_or_order_code_added: `{safety.get('wallet_or_order_code_added')}`",
            f"- external_api_calls_performed: `{safety.get('external_api_calls_performed')}`",
            f"- real_codex_invocation_allowed_by_plan: `{safety.get('real_codex_invocation_allowed_by_plan')}`",
            f"- real_codex_invocation_operator_flag: `{safety.get('real_codex_invocation_operator_flag')}`",
            "",
            "This is an operator-started, bounded batch report. It does not register schedulers, create daemons, start background workers, use browser automation, call external APIs directly, access credentials, touch wallets/signing/orders, or enable autonomous trading.",
            "",
            f"Next operator action: {report.get('next_operator_action')}",
            "",
        ]
    )
    return "\n".join(lines)


def _run_one_task(
    queue_root: Path,
    repo: Path,
    plan: Mapping[str, Any],
    task: Mapping[str, Any],
    *,
    repo_git_state: Mapping[str, Any] | None = None,
    dry_run: bool,
    allow_real_codex_invocation: bool,
    timeout_seconds: int,
) -> dict[str, Any]:
    task_id = str(task["task_id"])
    route = route_from_task_payload(task, repo_root=repo)
    lane_state = _lane_state_for_task(
        queue_root,
        repo,
        plan,
        task,
        dry_run=dry_run,
        repo_git_state=repo_git_state,
    )
    lane_state = write_lane_state_artifacts(queue_root, lane_state)
    executor_mode = "fake" if dry_run else str(task.get("executor_mode") or plan.get("executor_mode") or DEFAULT_EXECUTOR_MODE)
    if executor_mode == "dry_run":
        executor_mode = "codex_cli_dry_run"

    report = {
        "task_id": task_id,
        "status": "blocked",
        "execution_status": "blocked",
        "lane_status": lane_state.get("status"),
        "lane_path": lane_state.get("worktree_path"),
        "branch": lane_state.get("branch"),
        "lane_reused": bool(lane_state.get("lane_reused", False)),
        "worktree_created": bool(lane_state.get("worktree_created", False)),
        "branch_created": bool(lane_state.get("branch_created", False)),
        "selected_subagent": route.selected_profile,
        "selected_subagent_profile_path": route.selected_profile_path,
        "subagent_route": route.to_dict(),
        "safety_flags": dict(lane_state.get("safety", {})) if isinstance(lane_state.get("safety"), Mapping) else {},
        "executor_mode": executor_mode,
        "max_steps": int(task.get("max_steps") or plan.get("max_steps_per_task") or 1),
        "test_summary": {"status": "not_run", "details": "batch runner does not run tests inside task lanes"},
        "blocker_reason": lane_state.get("blocker_reason"),
        "next_action": "",
        "codex_invoked": False,
        "codex_invocation_count": 0,
        "execution_report_paths": {},
        "errors": list(lane_state.get("blockers", [])),
        "warnings": [*list(route.warnings), *list(lane_state.get("warnings", []))],
    }
    if lane_state.get("status") not in {"planned", "ready"} or lane_state.get("execution_allowed") is False:
        report["next_action"] = "Resolve the lane blocker before executing this task."
        return report

    if executor_mode == "fake":
        report["status"] = "completed"
        report["execution_status"] = "fake_completed"
        report["blocker_reason"] = None
        report["next_action"] = "Review the fake executor lane report, then decide whether to rerun with a stricter executor."
        return report

    if executor_mode == "codex_cli_dry_run":
        execution = run_codex_once(queue_root, task_id=task_id, dry_run=True, timeout_seconds=timeout_seconds)
        return _merge_codex_execution(report, execution, dry_run=True)

    if executor_mode == "codex_cli":
        if plan.get("allow_real_codex_invocation") is not True:
            report["blocker_reason"] = "plan allow_real_codex_invocation must be true for codex_cli executor"
            report["errors"].append(str(report["blocker_reason"]))
            report["next_action"] = "Set allow_real_codex_invocation only in a separately approved operator task."
            return report
        if not allow_real_codex_invocation:
            report["blocker_reason"] = "--allow-real-codex-invocation is required for codex_cli executor"
            report["errors"].append(str(report["blocker_reason"]))
            report["next_action"] = "Rerun with the explicit operator flag only after dry-run review."
            return report
        execution = run_codex_once(queue_root, task_id=task_id, dry_run=False, timeout_seconds=timeout_seconds)
        return _merge_codex_execution(report, execution, dry_run=False)

    report["blocker_reason"] = f"unsupported executor_mode: {executor_mode}"
    report["errors"].append(str(report["blocker_reason"]))
    report["next_action"] = "Fix executor_mode in the batch plan."
    return report


def _lane_state_for_task(
    queue_root: Path,
    repo: Path,
    plan: Mapping[str, Any],
    task: Mapping[str, Any],
    *,
    dry_run: bool,
    repo_git_state: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    lane_root = str(plan.get("lane_root") or "") or None
    common = {
        "task_id": str(task["task_id"]),
        "run_id": str(plan["batch_id"]),
        "repo_root": repo,
        "expected_base_branch": str(plan["expected_base_branch"]),
        "expected_base_head": str(plan["expected_base_head"]),
        "lane_root": lane_root,
        "task_category": str(task.get("task_category") or ""),
    }
    if dry_run or plan.get("lane_mode") == "plan_only":
        return plan_task_worktree_lane(
            queue_root,
            git_state_override=dict(repo_git_state) if isinstance(repo_git_state, Mapping) else None,
            **common,
        )

    existing = inspect_task_worktree_lane(queue_root, **common)
    if _lane_can_be_reused(existing, plan):
        existing["lane_reused"] = True
        existing["branch_created"] = False
        existing["worktree_created"] = False
        existing["status"] = "ready"
        existing["ready"] = True
        existing["execution_allowed"] = True
        return existing

    created = create_task_worktree_lane(queue_root, **common)
    created["lane_reused"] = False
    return created


def _lane_can_be_reused(state: Mapping[str, Any], plan: Mapping[str, Any]) -> bool:
    if state.get("status") != "ready" or state.get("worktree_path_exists") is not True:
        return False
    git_state = state.get("worktree_git_state", {})
    if not isinstance(git_state, Mapping):
        return False
    expected_head = str(plan.get("expected_base_head") or "")
    if expected_head and git_state.get("head") != expected_head:
        return False
    return not git_state.get("errors")


def _merge_codex_execution(task_report: dict[str, Any], execution: Mapping[str, Any], *, dry_run: bool) -> dict[str, Any]:
    merged = dict(task_report)
    merged["status"] = "completed" if execution.get("status") == "ok" else str(execution.get("status") or "blocked")
    merged["execution_status"] = str(execution.get("execution_status") or "blocked")
    merged["codex_invoked"] = bool(execution.get("codex_exec_invoked", False))
    merged["codex_invocation_count"] = int(execution.get("codex_invocation_count") or 0)
    merged["execution_report_paths"] = dict(execution.get("report_paths", {})) if isinstance(execution.get("report_paths"), Mapping) else {}
    merged["errors"] = [*list(merged.get("errors", [])), *list(execution.get("errors", []))]
    merged["warnings"] = [*list(merged.get("warnings", [])), *list(execution.get("warnings", []))]
    if execution.get("status") != "ok":
        merged["status"] = str(execution.get("status") or "blocked")
        merged["blocker_reason"] = "; ".join(str(error) for error in execution.get("errors", [])) or str(execution.get("status"))
    else:
        merged["blocker_reason"] = None
    merged["test_summary"] = {
        "status": "not_run",
        "details": "Codex execution reports may include command/log validation, but task tests remain task-owned.",
    }
    merged["next_action"] = str(execution.get("next_operator_action") or "Inspect the Codex execution report.")
    return merged


def _repo_preflight(repo: Path, plan: Mapping[str, Any]) -> dict[str, Any]:
    git_state = inspect_git_state(str(repo))
    errors: list[str] = [str(value) for value in git_state.get("errors", [])]
    warnings: list[str] = [str(value) for value in git_state.get("warnings", [])]
    expected_branch = str(plan.get("expected_base_branch") or "")
    expected_head = str(plan.get("expected_base_head") or "")
    current_branch = str(git_state.get("branch") or "")
    current_head = str(git_state.get("head") or "")
    if expected_branch and current_branch != expected_branch:
        errors.append(f"current branch {current_branch or '<unknown>'} does not match expected base branch {expected_branch}")
    if expected_head and current_head != expected_head:
        errors.append(f"current head {current_head or '<unknown>'} does not match expected base head {expected_head}")
    if git_state.get("status_lines"):
        errors.append("repository has uncommitted or untracked changes")
    return {
        "status": "blocked" if errors else "ok",
        "repo_root": str(git_state.get("repo_root") or repo),
        "git_state": git_state,
        "errors": errors,
        "warnings": warnings,
    }


def _base_report(
    *,
    plan_file: str | Path,
    queue_root: Path,
    repo: Path,
    run_id: str,
    started_at: str,
    plan: Mapping[str, Any],
    validation: Mapping[str, Any],
    dry_run: bool,
    allow_real_codex_invocation: bool,
    timeout_seconds: int,
) -> dict[str, Any]:
    return {
        "schema_version": NIGHTLY_LANE_BATCH_REPORT_SCHEMA_VERSION,
        "plan_schema_version": NIGHTLY_LANE_BATCH_PLAN_SCHEMA_VERSION,
        "batch_id": str(plan.get("batch_id") or ""),
        "run_id": run_id,
        "started_at": started_at,
        "ended_at": None,
        "plan_file": str(plan_file),
        "queue_root": str(queue_root),
        "repo_root": str(repo),
        "expected_base_branch": str(plan.get("expected_base_branch") or ""),
        "expected_base_head": str(plan.get("expected_base_head") or ""),
        "lane_mode": str(plan.get("lane_mode") or DEFAULT_LANE_MODE),
        "executor_mode": str(plan.get("executor_mode") or DEFAULT_EXECUTOR_MODE),
        "max_steps_per_task": int(plan.get("max_steps_per_task") or DEFAULT_MAX_STEPS_PER_TASK),
        "stop_policy": str(plan.get("stop_policy") or DEFAULT_STOP_POLICY),
        "dry_run": dry_run,
        "allow_real_codex_invocation_flag": allow_real_codex_invocation,
        "timeout_seconds": timeout_seconds,
        "status": "blocked",
        "execution_status": "blocked",
        "task_count": 0,
        "planned_task_count": len(plan.get("tasks", [])) if isinstance(plan.get("tasks"), list) else 0,
        "completed_count": 0,
        "blocked_count": 0,
        "failed_count": 0,
        "tasks": [],
        "repo_preflight": {},
        "plan_validation": {
            "valid": bool(validation.get("valid")),
            "errors": list(validation.get("errors", [])),
            "warnings": list(validation.get("warnings", [])),
        },
        "errors": [],
        "warnings": [],
        "blocker_reason": None,
        "stopped_on_task_id": None,
        "codex_invocation_count": 0,
        "safety_summary": {
            "no_daemon_or_scheduler_added": True,
            "no_background_worker_added": True,
            "wallet_or_order_code_added": False,
            "external_api_calls_performed": 0,
            "browser_automation_used": False,
            "autonomous_trading_enabled": False,
            "real_codex_invocation_allowed_by_plan": bool(plan.get("allow_real_codex_invocation", False)),
            "real_codex_invocation_operator_flag": allow_real_codex_invocation,
            "scheduler_created": False,
            "daemon_created": False,
            "background_worker_created": False,
            "wallet_or_private_key_access": False,
            "orders_or_trading_actions": False,
        },
        "next_operator_action": "",
        "report_paths": {},
    }


def _write_batch_report(queue_root: Path, report: dict[str, Any]) -> dict[str, Any]:
    payload = dict(report)
    payload["ended_at"] = _utc_iso()
    reports_dir = safe_queue_path(queue_root, "reports")
    batch_id = _safe_filename_part(str(payload.get("batch_id") or "nightly-lane-batch"))
    run_id = _safe_filename_part(str(payload.get("run_id") or _run_id()))
    json_path = reports_dir / f"nightly_lane_batch_report_{batch_id}_{run_id}.json"
    md_path = reports_dir / f"nightly_lane_batch_report_{batch_id}_{run_id}.md"
    latest_json = reports_dir / "latest_nightly_lane_batch_report.json"
    latest_md = reports_dir / "latest_nightly_lane_batch_report.md"
    payload["report_paths"] = {
        "nightly_lane_batch_report_json": str(json_path),
        "nightly_lane_batch_report_md": str(md_path),
        "latest_nightly_lane_batch_report_json": str(latest_json),
        "latest_nightly_lane_batch_report_md": str(latest_md),
    }
    write_json_atomic(json_path, payload)
    write_text_atomic(md_path, render_nightly_lane_batch_markdown(payload))
    write_json_atomic(latest_json, payload)
    write_text_atomic(latest_md, render_nightly_lane_batch_markdown(payload))
    return payload


def _accumulate_task_counts(report: dict[str, Any], task_report: Mapping[str, Any]) -> None:
    status = str(task_report.get("status") or "")
    if status == "completed":
        report["completed_count"] += 1
    elif status == "failed":
        report["failed_count"] += 1
    elif status in {"blocked", "failed"} or task_report.get("blocker_reason"):
        report["blocked_count"] += 1


def _should_stop_after_task(stop_policy: str, task_report: Mapping[str, Any]) -> bool:
    if stop_policy != "stop_on_first_blocker":
        return False
    status = str(task_report.get("status") or "")
    return status in {"blocked", "failed"} or bool(task_report.get("blocker_reason"))


def _overall_status(report: Mapping[str, Any], *, dry_run: bool) -> str:
    if report.get("failed_count"):
        return "failed"
    if report.get("blocked_count"):
        return "blocked"
    if dry_run:
        return "dry_run"
    return "completed"


def _execution_status(report: Mapping[str, Any], *, dry_run: bool) -> str:
    if report.get("stopped_on_task_id"):
        return "stopped"
    if report.get("failed_count"):
        return "failed"
    if report.get("blocked_count"):
        return "completed_with_blockers"
    if dry_run:
        return "dry_run"
    return "completed"


def _next_operator_action(report: Mapping[str, Any]) -> str:
    if report.get("status") == "dry_run":
        return "Review the report, then rerun without --dry-run only when lane creation is intended."
    if report.get("status") == "completed":
        return "Review lane reports and task outputs before any selective staging or follow-up execution."
    return "Resolve blockers in the report, then rerun the batch with the fake executor first."


def _read_plan_json(plan_file: str | Path) -> Any:
    try:
        return read_json(plan_file)
    except (OSError, json.JSONDecodeError):
        return {}


def _payload_string(payload: Any, key: str) -> str:
    if isinstance(payload, Mapping):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value
    return ""


def _int_range(value: Any, name: str, *, minimum: int, maximum: int, errors: list[str]) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError):
        errors.append(f"{name} must be an integer")
        return minimum
    if number < minimum or number > maximum:
        errors.append(f"{name} must be between {minimum} and {maximum}")
        return min(max(number, minimum), maximum)
    return number


def _safe_artifact_id(value: str, *, field_name: str, errors: list[str]) -> str:
    text = str(value or "").strip()
    if not text:
        errors.append(f"{field_name} is required")
        return ""
    safe = _safe_filename_part(text)
    if safe != text:
        errors.append(f"{field_name} contains unsafe characters")
    return safe


def _safe_filename_part(value: str) -> str:
    safe = "".join(ch if ch.isalnum() or ch in "._-" else "-" for ch in str(value or "").strip())
    safe = safe.strip(".-_")
    return safe or "batch"


def _summary_text(value: Any) -> str:
    if isinstance(value, Mapping):
        status = value.get("status", "unknown")
        details = value.get("details", "")
        return f"{status}: {details}" if details else str(status)
    return str(value or "unknown")


def _safety_flags_text(value: Any) -> str:
    if not isinstance(value, Mapping):
        return "unknown"
    keys = (
        "codex_invoked",
        "external_api_calls_performed",
        "browser_automation_used",
        "wallet_or_private_key_accessed",
        "orders_or_trading_actions",
        "daemon_created",
        "scheduler_created",
        "background_worker_created",
    )
    return ", ".join(f"{key}={value.get(key)}" for key in keys if key in value) or "none"


def _run_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _utc_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
