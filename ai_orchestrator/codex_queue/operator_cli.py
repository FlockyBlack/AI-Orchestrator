from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from .dry_run_runner import run_dry_run
from .files import (
    QUEUE_STATE_DIRECTORIES,
    count_task_packets,
    ensure_queue_directories,
    find_task_packet,
    move_task_packet,
    read_json,
    safe_existing_path_under_queue,
    safe_queue_path,
    task_packet_path,
    validate_task_id,
    write_json_atomic,
    write_text_atomic,
)
from .morning_report import generate_morning_report
from .night_runner import generate_night_dry_run_plan
from .package_readiness import generate_package_readiness_report
from .portability import generate_portability_report
from .queue_health import generate_next_actions_report
from .result_ingestor import ingest_result
from .result_schema import default_result
from .runbook import generate_controlled_runbook
from .scheduler_plan import generate_scheduler_readiness_plan
from .schema import default_packet
from .safety import classify_packet
from .validator import validate_packet
from .workspace_planner import plan_workspace_for_task, render_workspace_plan_markdown


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Local-only Codex queue operator CLI.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    status_parser = subparsers.add_parser("status", help="Inspect queue state.")
    _add_queue_root(status_parser)
    status_parser.set_defaults(func=_cmd_status)

    create_parser = subparsers.add_parser("create-demo-task", help="Create a safe docs-only demo task.")
    _add_queue_root(create_parser)
    create_parser.add_argument("--task-id", required=True)
    create_parser.add_argument("--overwrite", action="store_true")
    create_parser.set_defaults(func=_cmd_create_demo_task)

    approve_parser = subparsers.add_parser("approve", help="Approve a safe inbox task.")
    _add_queue_root(approve_parser)
    approve_parser.add_argument("--task-id", required=True)
    approve_parser.set_defaults(func=_cmd_approve)

    plan_parser = subparsers.add_parser("plan", help="Run the dry-run planner for approved tasks.")
    _add_queue_root(plan_parser)
    plan_parser.set_defaults(func=_cmd_plan)

    workspace_plan_parser = subparsers.add_parser(
        "workspace-plan",
        help="Write a local-only branch/worktree plan for one approved or planned task.",
    )
    _add_queue_root(workspace_plan_parser)
    workspace_plan_parser.add_argument("--task-id", required=True)
    workspace_plan_parser.set_defaults(func=_cmd_workspace_plan)

    ingest_parser = subparsers.add_parser("ingest-result", help="Ingest a manual result packet.")
    _add_queue_root(ingest_parser)
    ingest_parser.add_argument("--result", required=True)
    ingest_parser.set_defaults(func=_cmd_ingest_result)

    review_parser = subparsers.add_parser("review", help="Write task review status reports.")
    _add_queue_root(review_parser)
    review_parser.add_argument("--task-id", required=True)
    review_parser.set_defaults(func=_cmd_review)

    done_parser = subparsers.add_parser("mark-done", help="Explicitly move a reviewed task to done.")
    _add_queue_root(done_parser)
    done_parser.add_argument("--task-id", required=True)
    done_parser.set_defaults(func=_cmd_mark_done)

    blocked_parser = subparsers.add_parser("mark-blocked", help="Explicitly move a task to blocked.")
    _add_queue_root(blocked_parser)
    blocked_parser.add_argument("--task-id", required=True)
    blocked_parser.add_argument("--reason", required=True)
    blocked_parser.set_defaults(func=_cmd_mark_blocked)

    runbook_parser = subparsers.add_parser("runbook", help="Generate the controlled manual Codex runbook.")
    _add_queue_root(runbook_parser)
    runbook_parser.set_defaults(func=_cmd_runbook)

    morning_report_parser = subparsers.add_parser("morning-report", help="Generate the morning queue report.")
    _add_queue_root(morning_report_parser)
    morning_report_parser.set_defaults(func=_cmd_morning_report)

    next_actions_parser = subparsers.add_parser("next-actions", help="Write ordered next operator actions.")
    _add_queue_root(next_actions_parser)
    next_actions_parser.set_defaults(func=_cmd_next_actions)

    night_dry_run_parser = subparsers.add_parser(
        "night-dry-run",
        help="Generate the local-only night-runner dry-run plan.",
    )
    _add_queue_root(night_dry_run_parser)
    night_dry_run_parser.add_argument("--max-tasks", type=int, default=5)
    night_dry_run_parser.add_argument("--ignore-stale-lock", action="store_true")
    night_dry_run_parser.set_defaults(func=_cmd_night_dry_run)

    scheduler_plan_parser = subparsers.add_parser(
        "scheduler-plan",
        help="Generate the scheduler readiness plan without registering a scheduler.",
    )
    _add_queue_root(scheduler_plan_parser)
    scheduler_plan_parser.set_defaults(func=_cmd_scheduler_plan)

    portability_parser = subparsers.add_parser(
        "portability-check",
        help="Generate the local portability report without executing queue tasks.",
    )
    _add_queue_root(portability_parser)
    portability_parser.set_defaults(func=_cmd_portability_check)

    package_readiness_parser = subparsers.add_parser(
        "package-readiness",
        help="Generate the package readiness report without staging or committing.",
    )
    _add_queue_root(package_readiness_parser)
    package_readiness_parser.set_defaults(func=_cmd_package_readiness)

    args = parser.parse_args(argv)
    try:
        result = args.func(args)
    except Exception as exc:  # pragma: no cover - defensive CLI boundary
        queue_root = getattr(args, "queue_root", "agent_tasks")
        task_id = getattr(args, "task_id", "")
        report = write_operator_action_report(
            queue_root,
            {
                "command": args.command,
                "status": "failed",
                "task_id": task_id,
                "queue_root": str(Path(queue_root)),
                "source_path": "",
                "destination_path": "",
                "errors": [str(exc)],
                "warnings": [],
                "next_operator_action": "Inspect the error and retry with a valid local queue path.",
            },
        )
        print(json.dumps(_cli_summary(report), indent=2, sort_keys=True))
        return 1

    print(json.dumps(_cli_summary(result), indent=2, sort_keys=True))
    return 0 if result.get("status") == "ok" else 1


def _add_queue_root(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--queue-root", default="agent_tasks", help="Local queue root directory.")


def _cmd_status(args: argparse.Namespace) -> dict[str, Any]:
    report = write_queue_status(args.queue_root)
    return write_operator_action_report(
        args.queue_root,
        _action(
            "status",
            "ok",
            "",
            args.queue_root,
            next_operator_action="Review queue counts and choose the next explicit operator command.",
            extra={
                "queue_status_report_paths": report["report_paths"],
                "queue_counts": report["counts"],
            },
        ),
    )


def _cmd_runbook(args: argparse.Namespace) -> dict[str, Any]:
    root = ensure_queue_directories(args.queue_root)
    report = generate_controlled_runbook(root)
    return write_operator_action_report(
        root,
        _action(
            "runbook",
            "ok",
            "",
            root,
            next_operator_action="Review the generated runbook before any manual Codex handoff.",
            extra={
                "controlled_runbook_report_paths": report["report_paths"],
                "ready_for_manual_codex_handoff_count": len(report["ready_for_manual_codex_handoff"]),
                "codex_execution_added": report["codex_execution_added"],
                "codex_app_server_used": report["codex_app_server_used"],
                "branch_created": report["branch_created"],
                "worktree_created": report["worktree_created"],
            },
        ),
    )


def _cmd_morning_report(args: argparse.Namespace) -> dict[str, Any]:
    root = ensure_queue_directories(args.queue_root)
    report = generate_morning_report(root)
    return write_operator_action_report(
        root,
        _action(
            "morning-report",
            "ok",
            "",
            root,
            next_operator_action="Review recommended next operator actions in the morning report.",
            extra={
                "morning_report_paths": report["report_paths"],
                "recommended_next_operator_actions_count": len(report["recommended_next_operator_actions"]),
                "codex_execution_added": report["codex_execution_added"],
                "codex_app_server_used": report["codex_app_server_used"],
                "branch_created": report["branch_created"],
                "worktree_created": report["worktree_created"],
            },
        ),
    )


def _cmd_next_actions(args: argparse.Namespace) -> dict[str, Any]:
    root = ensure_queue_directories(args.queue_root)
    report = generate_next_actions_report(root)
    return write_operator_action_report(
        root,
        _action(
            "next-actions",
            "ok",
            "",
            root,
            next_operator_action="Review the ordered next-actions report and run only explicit operator commands.",
            extra={
                "next_actions_report_paths": report["report_paths"],
                "next_actions": report["next_actions"],
                "batch_plan": report["batch_plan"],
                "codex_execution_added": report["codex_execution_added"],
                "codex_app_server_used": report["codex_app_server_used"],
                "branch_created": report["branch_created"],
                "worktree_created": report["worktree_created"],
            },
        ),
    )


def _cmd_night_dry_run(args: argparse.Namespace) -> dict[str, Any]:
    root = ensure_queue_directories(args.queue_root)
    report = generate_night_dry_run_plan(
        root,
        max_tasks=args.max_tasks,
        ignore_stale_lock=args.ignore_stale_lock,
    )
    status = "ok" if report["status"] == "ok" else "blocked"
    return write_operator_action_report(
        root,
        _action(
            "night-dry-run",
            status,
            "",
            root,
            errors=list(report.get("errors", [])),
            warnings=list(report.get("warnings", [])),
            next_operator_action=(
                "Review the night dry-run plan and run only explicit operator commands."
                if status == "ok"
                else "Resolve the blocking lock or git safety errors before using the night plan."
            ),
            extra={
                "night_dry_run_report_paths": report["report_paths"],
                "lock_check_report_paths": report["lock_check"]["report_paths"],
                "eligible_for_manual_handoff_count": len(report["eligible_for_manual_handoff"]),
                "ordered_next_actions_count": len(report["ordered_next_actions"]),
                "would_execute_codex": report["would_execute_codex"],
                "would_create_branch": report["would_create_branch"],
                "would_create_worktree": report["would_create_worktree"],
                "would_register_scheduler": report["would_register_scheduler"],
                "codex_execution_added": report["codex_execution_added"],
                "codex_app_server_used": report["codex_app_server_used"],
                "branch_created": report["branch_created"],
                "worktree_created": report["worktree_created"],
                "background_worker_added": report["background_worker_added"],
                "scheduler_added": report["scheduler_added"],
                "task_marked_done_automatically": report["task_marked_done_automatically"],
            },
        ),
    )


def _cmd_scheduler_plan(args: argparse.Namespace) -> dict[str, Any]:
    root = ensure_queue_directories(args.queue_root)
    report = generate_scheduler_readiness_plan(root)
    return write_operator_action_report(
        root,
        _action(
            "scheduler-plan",
            "ok",
            "",
            root,
            warnings=list(report.get("warnings", [])),
            next_operator_action="Review scheduler readiness gates; do not register a scheduler without a separate approval task.",
            extra={
                "scheduler_plan_report_paths": report["report_paths"],
                "scheduler_registered": report["scheduler_registered"],
                "real_scheduler_registered": report["real_scheduler_registered"],
                "would_register_scheduler": report["would_register_scheduler"],
                "codex_execution_added": report["codex_execution_added"],
                "codex_app_server_used": report["codex_app_server_used"],
                "background_worker_added": report["background_worker_added"],
                "branch_created": report["branch_created"],
                "worktree_created": report["worktree_created"],
                "network_calls_performed": report["network_calls_performed"],
                "credentials_accessed": report["credentials_accessed"],
            },
        ),
    )


def _cmd_portability_check(args: argparse.Namespace) -> dict[str, Any]:
    root = ensure_queue_directories(args.queue_root)
    report = generate_portability_report(Path.cwd(), root)
    return write_operator_action_report(
        root,
        _action(
            "portability-check",
            "ok",
            "",
            root,
            warnings=list(report.get("warnings", [])),
            next_operator_action="Review portability warnings before packaging or selectively staging files.",
            extra={
                "portability_report_paths": report["report_paths"],
                "package_import_ok": report["package_import_ok"],
                "absolute_path_leaks_count": report["absolute_path_leaks"]["count"],
                "hardcoded_c_path_occurrences_count": report["hardcoded_c_path_occurrences"]["count"],
                "codex_execution_added": report["codex_execution_added"],
                "codex_app_server_used": report["codex_app_server_used"],
                "branch_created": report["branch_created"],
                "worktree_created": report["worktree_created"],
                "background_worker_added": report["background_worker_added"],
                "scheduler_registered": report["scheduler_registered"],
                "network_calls_performed": report["network_calls_performed"],
                "credentials_accessed": report["credentials_accessed"],
            },
        ),
    )


def _cmd_package_readiness(args: argparse.Namespace) -> dict[str, Any]:
    root = ensure_queue_directories(args.queue_root)
    report = generate_package_readiness_report(root)
    return write_operator_action_report(
        root,
        _action(
            "package-readiness",
            "ok",
            "",
            root,
            warnings=list(report.get("warnings", [])),
            next_operator_action="Review readiness warnings and commit guidance before any selective git staging.",
            extra={
                "package_readiness_report_paths": report["report_paths"],
                "readiness_status": report["status"],
                "successful_pilot_core_evidence_present": report[
                    "successful_pilot_evidence_present"
                ]["core_evidence_present"],
                "git_add_performed": report["git_add_performed"],
                "git_commit_performed": report["git_commit_performed"],
                "git_push_performed": report["git_push_performed"],
                "branch_created": report["branch_created"],
                "worktree_created": report["worktree_created"],
                "real_scheduler_registered": report["real_scheduler_registered"],
                "background_worker_added": report["background_worker_added"],
                "codex_execution_added": report["codex_execution_added"],
                "codex_app_server_used": report["codex_app_server_used"],
                "network_calls_performed": report["network_calls_performed"],
                "credentials_accessed": report["credentials_accessed"],
            },
        ),
    )


def _cmd_create_demo_task(args: argparse.Namespace) -> dict[str, Any]:
    root = ensure_queue_directories(args.queue_root)
    task_id = validate_task_id(args.task_id)
    destination = task_packet_path(root, "inbox", task_id)
    if destination.exists() and not args.overwrite:
        return write_operator_action_report(
            root,
            _action(
                "create-demo-task",
                "blocked",
                task_id,
                root,
                destination_path=destination,
                errors=[f"task packet already exists: {destination}"],
                next_operator_action="Use --overwrite only when replacing this demo packet is intentional.",
            ),
        )

    packet = _demo_task_packet(task_id)
    write_json_atomic(destination, packet, overwrite=args.overwrite)
    return write_operator_action_report(
        root,
        _action(
            "create-demo-task",
            "ok",
            task_id,
            root,
            destination_path=destination,
            next_operator_action="Run approve for this task when ready.",
        ),
    )


def _cmd_approve(args: argparse.Namespace) -> dict[str, Any]:
    root = ensure_queue_directories(args.queue_root)
    task_id = validate_task_id(args.task_id)
    match = find_task_packet(root, task_id, states=("inbox",))
    if not match["found"]:
        return write_operator_action_report(
            root,
            _action(
                "approve",
                "blocked",
                task_id,
                root,
                errors=[f"no inbox task packet found for task_id: {task_id}", *match["errors"]],
                next_operator_action="Create or move a safe task packet into inbox before approval.",
            ),
        )

    packet = dict(match["packet"])
    validation = validate_packet(packet)
    if not validation.valid:
        return write_operator_action_report(
            root,
            _action(
                "approve",
                "blocked",
                task_id,
                root,
                source_path=match["path"],
                errors=list(validation.errors),
                next_operator_action="Fix the task packet schema before approval.",
            ),
        )

    if packet.get("status") != "inbox":
        return write_operator_action_report(
            root,
            _action(
                "approve",
                "blocked",
                task_id,
                root,
                source_path=match["path"],
                errors=[f"task status must be inbox before approval, got: {packet.get('status')}"],
                next_operator_action="Inspect the packet state before approving.",
            ),
        )

    approved_packet = dict(packet)
    approved_packet["status"] = "approved"
    approved_packet["approved_by"] = "operator_cli"
    approved_packet["approved_at"] = _utc_iso()
    approval_validation = validate_packet(approved_packet)
    classification = classify_packet(approved_packet, approval_validation)
    if not approval_validation.valid or not classification.allowed:
        errors = list(approval_validation.errors) + list(classification.reasons)
        return write_operator_action_report(
            root,
            _action(
                "approve",
                "blocked",
                task_id,
                root,
                source_path=match["path"],
                errors=errors,
                warnings=[f"safety classification: {classification.status}"],
                next_operator_action="Revise or block the task; unsafe tasks are not approved by this CLI.",
            ),
        )

    try:
        destination = move_task_packet(root, match["path"], task_id, "approved", approved_packet)
    except FileExistsError as exc:
        return write_operator_action_report(
            root,
            _action(
                "approve",
                "blocked",
                task_id,
                root,
                source_path=match["path"],
                errors=[str(exc)],
                next_operator_action="Resolve the existing approved packet before retrying.",
            ),
        )

    return write_operator_action_report(
        root,
        _action(
            "approve",
            "ok",
            task_id,
            root,
            source_path=match["path"],
            destination_path=destination,
            next_operator_action="Run plan to generate the dry-run plan and handoff prompt.",
        ),
    )


def _cmd_plan(args: argparse.Namespace) -> dict[str, Any]:
    root = ensure_queue_directories(args.queue_root)
    report = run_dry_run(root)
    return write_operator_action_report(
        root,
        _action(
            "plan",
            "ok",
            "",
            root,
            warnings=[],
            next_operator_action="Review generated plans and handoff prompts before any manual execution.",
            extra={
                "dry_run_report_paths": report["report_paths"],
                "packets_seen": report["packets_seen"],
                "allowed_count": report["allowed_count"],
                "acceptance_checks_executed": report["acceptance_checks_executed"],
                "codex_execution_added": report["codex_execution_added"],
                "codex_app_server_used": report["codex_app_server_used"],
            },
        ),
    )


def _cmd_workspace_plan(args: argparse.Namespace) -> dict[str, Any]:
    root = ensure_queue_directories(args.queue_root)
    task_id = validate_task_id(args.task_id)
    plan = plan_workspace_for_task(root, task_id, repo_root=".")

    plan_json_path = safe_queue_path(root, "planned", f"{task_id}.workspace_plan.json")
    task_report_md_path = safe_queue_path(root, "reports", f"{task_id}.workspace_plan.md")
    latest_json_path = safe_queue_path(root, "reports", "latest_workspace_plan.json")
    latest_md_path = safe_queue_path(root, "reports", "latest_workspace_plan.md")
    plan["report_paths"] = {
        "workspace_plan_json": str(plan_json_path),
        "workspace_plan_md": str(task_report_md_path),
        "latest_workspace_plan_json": str(latest_json_path),
        "latest_workspace_plan_md": str(latest_md_path),
    }
    markdown = render_workspace_plan_markdown(plan)
    write_json_atomic(plan_json_path, plan)
    write_text_atomic(task_report_md_path, markdown)
    write_json_atomic(latest_json_path, plan)
    write_text_atomic(latest_md_path, markdown)

    status = "ok" if plan["status"] == "planned" else "blocked"
    return write_operator_action_report(
        root,
        _action(
            "workspace-plan",
            status,
            task_id,
            root,
            destination_path=plan_json_path,
            errors=list(plan.get("errors", [])),
            warnings=list(plan.get("warnings", [])),
            next_operator_action=str(plan.get("next_operator_action", "")),
            extra={
                "workspace_plan_status": plan["status"],
                "workspace_plan_report_paths": plan["report_paths"],
                "branch_created": plan["branch_created"],
                "worktree_created": plan["worktree_created"],
                "codex_execution_enabled": plan["codex_execution_enabled"],
                "codex_app_server_used": plan["codex_app_server_used"],
            },
        ),
    )


def _cmd_ingest_result(args: argparse.Namespace) -> dict[str, Any]:
    root = ensure_queue_directories(args.queue_root)
    try:
        result_path = safe_existing_path_under_queue(root, args.result)
    except ValueError as exc:
        return write_operator_action_report(
            root,
            _action(
                "ingest-result",
                "blocked",
                "",
                root,
                source_path=args.result,
                errors=[str(exc)],
                next_operator_action="Place result packets under the local queue review directory.",
            ),
        )

    report = ingest_result(root, result_path)
    status = "ok" if report["accepted"] else "blocked"
    return write_operator_action_report(
        root,
        _action(
            "ingest-result",
            status,
            str(report.get("task_id") or ""),
            root,
            source_path=result_path,
            errors=list(report.get("errors", [])),
            next_operator_action=(
                "Run review for this task; ingestion never marks tasks done automatically."
                if report["accepted"]
                else "Fix the result packet or task packet before review."
            ),
            extra={
                "ingestion_status": report["ingestion_status"],
                "accepted": report["accepted"],
                "ingestion_report_paths": report["report_paths"],
                "task_marked_done_automatically": report["task_marked_done_automatically"],
                "commands_from_result_executed": report["commands_from_result_executed"],
            },
        ),
    )


def _cmd_review(args: argparse.Namespace) -> dict[str, Any]:
    root = ensure_queue_directories(args.queue_root)
    task_id = validate_task_id(args.task_id)
    review_report = build_review_report(root, task_id)
    status = "ok" if review_report["task_packet"]["found"] else "blocked"
    action_errors = [] if status == "ok" else [f"no task packet found for task_id: {task_id}"]
    action = write_operator_action_report(
        root,
        _action(
            "review",
            status,
            task_id,
            root,
            errors=action_errors,
            next_operator_action=(
                "Run mark-done only if recommendation is ready_for_operator_done."
                if review_report["recommendation"] == "ready_for_operator_done"
                else "Inspect the review report and address missing or blocked artifacts."
            ),
            extra={
                "review_report_paths": review_report["report_paths"],
                "recommendation": review_report["recommendation"],
            },
        ),
    )
    return action


def _cmd_mark_done(args: argparse.Namespace) -> dict[str, Any]:
    root = ensure_queue_directories(args.queue_root)
    task_id = validate_task_id(args.task_id)
    errors: list[str] = []

    review_path = safe_queue_path(root, "reports", f"{task_id}.review.json")
    review_report: dict[str, Any] | None = None
    if not review_path.exists():
        errors.append(f"matching review report is required: {review_path}")
    else:
        review_report = read_json(review_path)
        if review_report.get("recommendation") != "ready_for_operator_done":
            errors.append("review recommendation must be ready_for_operator_done")

    result_path = safe_queue_path(root, "review", f"{task_id}.result.json")
    result_payload: Mapping[str, Any] | None = None
    if not result_path.exists():
        errors.append(f"matching result packet is required: {result_path}")
    else:
        result_payload = read_json(result_path)
        if not isinstance(result_payload, Mapping) or result_payload.get("status") != "completed":
            errors.append("matching result packet status must be completed")

    ingestion = find_allowed_ingestion_report(root, task_id)
    if not ingestion["allowed"]:
        errors.append("latest or task-specific ingestion report status must be allowed")

    match = find_task_packet(root, task_id, states=("inbox", "approved", "planned", "running", "review", "blocked"))
    if not match["found"]:
        done_match = find_task_packet(root, task_id, states=("done",))
        if done_match["found"]:
            errors.append(f"task is already done: {done_match['path']}")
        else:
            errors.append(f"no movable task packet found for task_id: {task_id}")

    if errors:
        return write_operator_action_report(
            root,
            _action(
                "mark-done",
                "blocked",
                task_id,
                root,
                source_path=match.get("path") if match else "",
                errors=errors,
                next_operator_action="Resolve the blocked review, result, or ingestion precondition before retrying.",
            ),
        )

    packet = dict(match["packet"])
    packet["status"] = "done"
    destination = move_task_packet(root, match["path"], task_id, "done", packet)
    return write_operator_action_report(
        root,
        _action(
            "mark-done",
            "ok",
            task_id,
            root,
            source_path=match["path"],
            destination_path=destination,
            next_operator_action="No further queue action is required for this task.",
            extra={
                "review_report_path": str(review_path),
                "result_path": str(result_path),
                "ingestion_report_path": ingestion["path"],
                "result_packet_moved": False,
            },
        ),
    )


def _cmd_mark_blocked(args: argparse.Namespace) -> dict[str, Any]:
    root = ensure_queue_directories(args.queue_root)
    task_id = validate_task_id(args.task_id)
    reason = str(args.reason).strip()
    if not reason:
        return write_operator_action_report(
            root,
            _action(
                "mark-blocked",
                "blocked",
                task_id,
                root,
                errors=["--reason must be a non-empty string"],
                next_operator_action="Retry mark-blocked with a clear reason.",
            ),
        )

    match = find_task_packet(root, task_id, states=("inbox", "approved", "planned", "review"))
    if not match["found"]:
        return write_operator_action_report(
            root,
            _action(
                "mark-blocked",
                "blocked",
                task_id,
                root,
                errors=[f"no task packet found in inbox/approved/planned/review for task_id: {task_id}"],
                next_operator_action="Inspect queue status and choose an existing non-terminal task.",
            ),
        )

    packet = dict(match["packet"])
    packet["status"] = "blocked"
    packet["operator_notes"] = _append_operator_note(
        str(packet.get("operator_notes", "")),
        f"Blocked by operator_cli at {_utc_iso()}: {reason}",
    )
    destination = move_task_packet(root, match["path"], task_id, "blocked", packet)
    blocking_report_path = safe_queue_path(root, "reports", f"{task_id}.blocked.json")
    write_json_atomic(
        blocking_report_path,
        {
            "task_id": task_id,
            "blocked_at": _utc_iso(),
            "blocked_by": "operator_cli",
            "reason": reason,
            "source_path": str(match["path"]),
            "destination_path": str(destination),
        },
    )
    return write_operator_action_report(
        root,
        _action(
            "mark-blocked",
            "ok",
            task_id,
            root,
            source_path=match["path"],
            destination_path=destination,
            next_operator_action="Review the blocking reason before creating a replacement or revised task.",
            extra={"blocking_report_path": str(blocking_report_path)},
        ),
    )


def write_queue_status(queue_root: str | Path) -> dict[str, Any]:
    root = ensure_queue_directories(queue_root)
    counts = {state: count_task_packets(root, state) for state in QUEUE_STATE_DIRECTORIES}
    artifact_counts = {
        "plans": len(list(safe_queue_path(root, "planned").glob("*.plan.json"))),
        "handoff_prompts": len(list(safe_queue_path(root, "planned").glob("*.handoff_prompt.md"))),
        "result_packets": len(list(safe_queue_path(root, "review").glob("*.result.json"))),
    }
    latest_dry_run = _latest_existing(
        safe_queue_path(root, "reports", "latest_dry_run_report.json"),
        tuple(safe_queue_path(root, "reports").glob("dry_run_report_*.json")),
    )
    latest_ingestion = _latest_existing(
        safe_queue_path(root, "reports", "latest_result_ingestion_report.json"),
        tuple(safe_queue_path(root, "reports").glob("result_ingestion_report_*.json")),
    )
    report = {
        "run_id": _run_id(),
        "queue_root": str(root),
        "counts": counts,
        "artifact_counts": artifact_counts,
        "latest_dry_run_report_path": str(latest_dry_run) if latest_dry_run else None,
        "latest_result_ingestion_report_path": str(latest_ingestion) if latest_ingestion else None,
        "codex_execution_added": False,
        "codex_app_server_used": False,
        "automatic_execution_enabled": False,
        "acceptance_checks_executed": False,
        "network_calls_performed": 0,
    }
    json_path = safe_queue_path(root, "reports", "latest_queue_status.json")
    md_path = safe_queue_path(root, "reports", "latest_queue_status.md")
    report["report_paths"] = {
        "latest_queue_status_json": str(json_path),
        "latest_queue_status_md": str(md_path),
    }
    write_json_atomic(json_path, report)
    write_text_atomic(md_path, render_queue_status_markdown(report))
    return report


def build_review_report(queue_root: str | Path, task_id: str) -> dict[str, Any]:
    root = ensure_queue_directories(queue_root)
    safe_task_id = validate_task_id(task_id)
    task_match = find_task_packet(root, safe_task_id)
    plan_path = safe_queue_path(root, "planned", f"{safe_task_id}.plan.json")
    handoff_path = safe_queue_path(root, "planned", f"{safe_task_id}.handoff_prompt.md")
    result_path = safe_queue_path(root, "review", f"{safe_task_id}.result.json")
    ingestion = find_allowed_ingestion_report(root, safe_task_id)
    result_payload = read_json(result_path) if result_path.exists() else None
    result_status = result_payload.get("status") if isinstance(result_payload, Mapping) else None

    warnings: list[str] = []
    if not task_match["found"]:
        warnings.append("matching task packet was not found")
    if not plan_path.exists():
        warnings.append("matching plan was not found")
    if not handoff_path.exists():
        warnings.append("matching handoff prompt was not found")
    if not result_path.exists():
        warnings.append("matching result packet was not found")
    if not ingestion["allowed"]:
        warnings.append("no allowed ingestion report was found for this task")
    if result_path.exists() and result_status != "completed":
        warnings.append("result packet status is not completed")

    recommendation = (
        "ready_for_operator_done"
        if task_match["found"]
        and result_path.exists()
        and result_status == "completed"
        and ingestion["allowed"]
        and not ingestion["errors"]
        else "needs_operator_review"
    )

    json_path = safe_queue_path(root, "reports", f"{safe_task_id}.review.json")
    md_path = safe_queue_path(root, "reports", f"{safe_task_id}.review.md")
    report: dict[str, Any] = {
        "run_id": _run_id(),
        "task_id": safe_task_id,
        "queue_root": str(root),
        "task_packet": {
            "found": bool(task_match["found"]),
            "state": task_match.get("state"),
            "path": str(task_match["path"]) if task_match.get("path") else None,
            "validation": validate_packet(task_match["packet"]).to_dict() if task_match["found"] else None,
        },
        "plan": {
            "found": plan_path.exists(),
            "path": str(plan_path) if plan_path.exists() else None,
        },
        "handoff_prompt": {
            "found": handoff_path.exists(),
            "path": str(handoff_path) if handoff_path.exists() else None,
        },
        "result_packet": {
            "found": result_path.exists(),
            "path": str(result_path) if result_path.exists() else None,
            "status": result_status,
        },
        "ingestion": ingestion,
        "recommendation": recommendation,
        "warnings": warnings,
        "codex_execution_added": False,
        "codex_app_server_used": False,
        "automatic_execution_enabled": False,
        "task_marked_done_automatically": False,
        "report_paths": {
            "review_json": str(json_path),
            "review_md": str(md_path),
        },
    }
    write_json_atomic(json_path, report)
    write_text_atomic(md_path, render_review_markdown(report))
    return report


def find_allowed_ingestion_report(queue_root: str | Path, task_id: str) -> dict[str, Any]:
    root = ensure_queue_directories(queue_root)
    safe_task_id = validate_task_id(task_id)
    reports_dir = safe_queue_path(root, "reports")
    candidate_paths: list[Path] = []
    latest = reports_dir / "latest_result_ingestion_report.json"
    if latest.exists():
        candidate_paths.append(latest)
    candidate_paths.extend(sorted(reports_dir.glob("result_ingestion_report_*.json"), key=_mtime, reverse=True))

    latest_seen_path: str | None = str(latest) if latest.exists() else None
    latest_seen_status: str | None = None
    latest_seen_task_id: str | None = None
    matching_reports: list[dict[str, Any]] = []
    errors: list[str] = []

    for path in candidate_paths:
        try:
            payload = read_json(path)
        except json.JSONDecodeError as exc:
            errors.append(f"{path}: invalid JSON: {exc}")
            continue
        if not isinstance(payload, Mapping):
            continue
        if path == latest:
            latest_seen_status = str(payload.get("ingestion_status"))
            latest_seen_task_id = str(payload.get("task_id"))
        if payload.get("task_id") != safe_task_id:
            continue
        allowed = _ingestion_report_allowed(payload)
        matching_reports.append(
            {
                "path": str(path),
                "status": "allowed" if allowed else str(payload.get("ingestion_status")),
                "accepted": bool(payload.get("accepted")),
                "allowed": allowed,
                "errors": list(payload.get("errors", [])),
            }
        )
        if allowed:
            return {
                "allowed": True,
                "status": "allowed",
                "path": str(path),
                "latest_report_path": latest_seen_path,
                "latest_report_task_id": latest_seen_task_id,
                "latest_report_status": latest_seen_status,
                "matching_reports": matching_reports,
                "errors": errors,
            }

    return {
        "allowed": False,
        "status": matching_reports[0]["status"] if matching_reports else "missing",
        "path": matching_reports[0]["path"] if matching_reports else None,
        "latest_report_path": latest_seen_path,
        "latest_report_task_id": latest_seen_task_id,
        "latest_report_status": latest_seen_status,
        "matching_reports": matching_reports,
        "errors": errors,
    }


def write_operator_action_report(queue_root: str | Path, action: Mapping[str, Any]) -> dict[str, Any]:
    root = ensure_queue_directories(queue_root)
    reports_dir = safe_queue_path(root, "reports")
    payload = {
        "command": str(action.get("command", "")),
        "status": str(action.get("status", "failed")),
        "task_id": str(action.get("task_id", "")),
        "queue_root": str(root),
        "source_path": str(action.get("source_path") or ""),
        "destination_path": str(action.get("destination_path") or ""),
        "errors": list(action.get("errors", [])),
        "warnings": list(action.get("warnings", [])),
        "next_operator_action": str(action.get("next_operator_action", "")),
        "run_id": _run_id(),
    }
    for key, value in action.items():
        if key not in payload:
            payload[key] = value

    json_path = reports_dir / "latest_operator_action.json"
    md_path = reports_dir / "latest_operator_action.md"
    payload["report_paths"] = {
        "latest_operator_action_json": str(json_path),
        "latest_operator_action_md": str(md_path),
    }
    write_json_atomic(json_path, payload)
    write_text_atomic(md_path, render_operator_action_markdown(payload))
    return payload


def render_queue_status_markdown(report: Mapping[str, Any]) -> str:
    lines = [
        "# Latest Queue Status",
        "",
        f"- run_id: `{report['run_id']}`",
        f"- queue_root: `{report['queue_root']}`",
        f"- latest_dry_run_report: `{report.get('latest_dry_run_report_path')}`",
        f"- latest_result_ingestion_report: `{report.get('latest_result_ingestion_report_path')}`",
        "",
        "## Task Counts",
        "",
    ]
    for state, count in report["counts"].items():
        lines.append(f"- {state}: `{count}`")
    lines.extend(
        [
            "",
            "## Artifacts",
            "",
        ]
    )
    for name, count in report["artifact_counts"].items():
        lines.append(f"- {name}: `{count}`")
    lines.extend(
        [
            "",
            "## Safety",
            "",
            "This status command only inspects local queue files and writes reports. It does not execute Codex, run acceptance checks, call Codex app-server, start workers, schedule jobs, or make network calls.",
            "",
        ]
    )
    return "\n".join(lines)


def render_operator_action_markdown(report: Mapping[str, Any]) -> str:
    lines = [
        "# Latest Operator Action",
        "",
        f"- command: `{report['command']}`",
        f"- status: `{report['status']}`",
        f"- task_id: `{report['task_id']}`",
        f"- queue_root: `{report['queue_root']}`",
        f"- source_path: `{report['source_path']}`",
        f"- destination_path: `{report['destination_path']}`",
        f"- next_operator_action: {report['next_operator_action']}",
        "",
    ]
    if report["errors"]:
        lines.extend(["## Errors", ""])
        lines.extend(f"- {error}" for error in report["errors"])
        lines.append("")
    if report["warnings"]:
        lines.extend(["## Warnings", ""])
        lines.extend(f"- {warning}" for warning in report["warnings"])
        lines.append("")
    lines.extend(
        [
            "## Safety",
            "",
            "This operator action was local-only and operator-invoked. It did not execute Codex, call Codex app-server, start background workers, add schedulers, call network services, or access credentials.",
            "",
        ]
    )
    return "\n".join(lines)


def render_review_markdown(report: Mapping[str, Any]) -> str:
    lines = [
        f"# Task Review: {report['task_id']}",
        "",
        f"- recommendation: `{report['recommendation']}`",
        f"- task_packet: `{report['task_packet']['path']}`",
        f"- plan: `{report['plan']['path']}`",
        f"- handoff_prompt: `{report['handoff_prompt']['path']}`",
        f"- result_packet: `{report['result_packet']['path']}`",
        f"- ingestion_report: `{report['ingestion'].get('path')}`",
        f"- ingestion_allowed: `{report['ingestion']['allowed']}`",
        "",
    ]
    if report["warnings"]:
        lines.extend(["## Warnings", ""])
        lines.extend(f"- {warning}" for warning in report["warnings"])
        lines.append("")
    lines.extend(
        [
            "## Manual Gate",
            "",
            "This review report is advisory. It does not mark the task done; the operator must run `mark-done` explicitly after reviewing the task result and ingestion report.",
            "",
        ]
    )
    return "\n".join(lines)


def _demo_task_packet(task_id: str) -> dict[str, Any]:
    packet = default_packet()
    packet.update(
        {
            "task_id": task_id,
            "title": "Demo local docs task for operator CLI lifecycle",
            "status": "inbox",
            "created_by": "operator_cli",
            "created_at": _utc_iso(),
            "approved_by": None,
            "approved_at": None,
            "priority": "low",
            "task_type": "local_docs_only",
            "summary": "Operator CLI demo task packet for a harmless local documentation lifecycle test.",
            "instructions": [
                "Create or update a harmless Markdown note under docs/ for operator testing.",
                "Keep all changes local.",
                "Do not use external services.",
                "Do not modify code or runtime behavior.",
            ],
            "safety_boundaries": [
                "Local files only.",
                "No network calls.",
                "No credentials.",
                "No wallet, trading, payment, runtime, dispatcher, or scheduler changes.",
                "No background workers.",
            ],
            "acceptance_checks": [],
            "expected_outputs": [_demo_output_path(task_id)],
            "operator_notes": "Generated by operator_cli create-demo-task for local queue lifecycle testing only.",
        }
    )
    packet["source"] = {
        "origin": "operator_cli_demo",
        "reference": "ORCH-SYMPHONY-004-TASK-LIFECYCLE-AND-OPERATOR-CLI",
    }
    packet["symphony_mapping"] = {
        "issue_id": None,
        "workspace_key": task_id.lower().replace("_", "-"),
        "proof_of_work_required": True,
        "human_review_required": True,
    }
    packet["repo"] = {
        "repo_root": ".",
        "base_branch": "master",
        "target_branch": None,
        "allowed_paths": ["docs/"],
        "forbidden_paths": [
            "ai_orchestrator/",
            "agent_tasks/",
            "runtime/",
            "dispatcher/",
            "run_codex/",
            "pm_bot/",
            "merchant_pipeline/",
        ],
    }
    packet["risk_flags"] = {key: False for key in packet["risk_flags"]}
    return packet


def _action(
    command: str,
    status: str,
    task_id: str,
    queue_root: str | Path,
    *,
    source_path: str | Path = "",
    destination_path: str | Path = "",
    errors: list[str] | None = None,
    warnings: list[str] | None = None,
    next_operator_action: str = "",
    extra: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "command": command,
        "status": status,
        "task_id": task_id,
        "queue_root": str(queue_root),
        "source_path": str(source_path) if source_path else "",
        "destination_path": str(destination_path) if destination_path else "",
        "errors": errors or [],
        "warnings": warnings or [],
        "next_operator_action": next_operator_action,
    }
    if extra:
        payload.update(extra)
    return payload


def _append_operator_note(existing: str, note: str) -> str:
    if existing.strip():
        return f"{existing.rstrip()}\n{note}"
    return note


def _ingestion_report_allowed(report: Mapping[str, Any]) -> bool:
    status = report.get("ingestion_status")
    return (
        (status in {"accepted", "allowed"} or report.get("accepted") is True)
        and not report.get("errors")
        and report.get("result_validation", {}).get("valid") is True
        and report.get("task_validation", {}).get("valid") is True
        and report.get("path_validation", {}).get("valid") is True
    )


def _latest_existing(latest_path: Path, candidates: tuple[Path, ...]) -> Path | None:
    if latest_path.exists():
        return latest_path
    existing = [path for path in candidates if path.exists()]
    if not existing:
        return None
    return max(existing, key=_mtime)


def _mtime(path: Path) -> float:
    try:
        return path.stat().st_mtime
    except FileNotFoundError:
        return 0.0


def _cli_summary(report: Mapping[str, Any]) -> dict[str, Any]:
    summary = {
        "command": report.get("command"),
        "status": report.get("status"),
        "task_id": report.get("task_id"),
        "errors": report.get("errors", []),
        "warnings": report.get("warnings", []),
        "next_operator_action": report.get("next_operator_action", ""),
        "report_paths": report.get("report_paths", {}),
    }
    if "next_actions" in report:
        summary["next_actions"] = report["next_actions"]
    for key, value in report.items():
        if key.endswith("_report_paths"):
            summary[key] = value
    return summary


def _run_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _utc_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _demo_output_path(task_id: str) -> str:
    return f"docs/{task_id.replace('-', '_')}_OUTPUT.md"


def build_demo_result(task_id: str) -> dict[str, Any]:
    result = default_result()
    result.update(
        {
            "task_id": task_id,
            "status": "completed",
            "completed_by": "operator_cli_demo_manual_result",
            "completed_at": _utc_iso(),
            "summary": "Safe demo result packet for operator CLI lifecycle testing; the declared docs file was not created by this command.",
            "files_created": [_demo_output_path(task_id)],
            "files_modified": [],
            "files_deleted": [],
            "commands_run": [],
            "validation_results": [],
            "acceptance_checks_passed": True,
            "operator_review_notes": "Demo result packet only. It records a claimed manual result for ingestion and review testing.",
            "next_recommended_action": "Run operator_cli review, then mark-done only if the review recommendation allows it.",
        }
    )
    result["safety_confirmation"] = {
        "network_calls_performed": 0,
        "credentials_accessed": False,
        "wallet_or_trading_touched": False,
        "runtime_or_dispatcher_touched": False,
        "background_worker_added": False,
        "scheduler_added": False,
        "telegram_or_openclaw_added": False,
        "openrouter_calls_performed": 0,
        "polymarket_api_calls_performed": 0,
        "codex_app_server_used": False,
        "destructive_commands_used": False,
    }
    return result


if __name__ == "__main__":
    raise SystemExit(main())
