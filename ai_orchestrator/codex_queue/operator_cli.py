from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from .codex_cli_batch_runner import DEFAULT_MAX_TASKS, HARD_MAX_TASKS, run_codex_batch
from .codex_cli_postprocessor import postprocess_codex_batch
from .codex_cli_runner import DEFAULT_TIMEOUT_SECONDS, run_codex_once
from .dry_run_runner import run_dry_run
from .long_run_controller import LongRunController
from .plan_contract import load_plan_contract, validate_plan_contract
from .plan_to_queue import create_queue_from_plan
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
from .pmbot_templates import SUPPORTED_PMBOT_TEMPLATES, build_pmbot_task_packet
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

    inspect_plan_parser = subparsers.add_parser("inspect-plan", help="Validate and summarize a plan contract.")
    inspect_plan_parser.add_argument("--plan-file", required=True)
    _add_queue_root(inspect_plan_parser)
    inspect_plan_parser.set_defaults(func=_cmd_inspect_plan_contract)

    plan_to_queue_parser = subparsers.add_parser("plan-to-queue", help="Materialize a plan into a generated run queue.")
    plan_to_queue_parser.add_argument("--plan-file", required=True)
    _add_queue_root(plan_to_queue_parser)
    plan_to_queue_parser.add_argument("--run-id", default=None)
    plan_to_queue_parser.add_argument("--dry-run", action="store_true")
    plan_to_queue_parser.set_defaults(func=_cmd_plan_to_generated_queue)

    run_plan_parser = subparsers.add_parser("run-plan", help="Run a bounded supervised plan with a local executor.")
    run_plan_parser.add_argument("--plan-file", required=True)
    _add_queue_root(run_plan_parser)
    run_plan_parser.add_argument("--mode", default="long_supervised")
    run_plan_parser.add_argument("--max-steps", type=int, default=50)
    run_plan_parser.add_argument("--commit", action="store_true")
    run_plan_parser.add_argument("--push", action="store_true")
    run_plan_parser.add_argument("--dry-run", action="store_true")
    run_plan_parser.add_argument("--continue-until", default="blocked_or_done")
    run_plan_parser.add_argument("--executor", choices=("fake", "noop", "handoff"), default="fake")
    run_plan_parser.add_argument("--run-id", default=None)
    run_plan_parser.set_defaults(func=_cmd_run_plan_contract)

    continue_plan_parser = subparsers.add_parser("continue-plan", help="Continue a generated plan run.")
    continue_plan_parser.add_argument("--run-id", required=True)
    _add_queue_root(continue_plan_parser)
    continue_plan_parser.add_argument("--max-steps", type=int, default=50)
    continue_plan_parser.add_argument("--continue-until", default="blocked_or_done")
    continue_plan_parser.add_argument("--executor", choices=("fake", "noop", "handoff"), default="fake")
    continue_plan_parser.set_defaults(func=_cmd_continue_plan_contract)

    recover_plan_parser = subparsers.add_parser("recover-plan", help="Inspect or recover a generated plan run.")
    recover_plan_parser.add_argument("--run-id", required=True)
    _add_queue_root(recover_plan_parser)
    recover_plan_parser.add_argument("--allow-stale-lock-clear", action="store_true")
    recover_plan_parser.set_defaults(func=_cmd_recover_plan_contract)

    export_prompt_parser = subparsers.add_parser(
        "export-next-codex-prompt",
        help="Generate the next Codex handoff prompt without invoking Codex.",
    )
    export_prompt_parser.add_argument("--run-id", required=True)
    _add_queue_root(export_prompt_parser)
    export_prompt_parser.set_defaults(func=_cmd_export_next_codex_prompt)

    create_parser = subparsers.add_parser("create-demo-task", help="Create a safe docs-only demo task.")
    _add_queue_root(create_parser)
    create_parser.add_argument("--task-id", required=True)
    create_parser.add_argument("--overwrite", action="store_true")
    create_parser.set_defaults(func=_cmd_create_demo_task)

    pmbot_parser = subparsers.add_parser(
        "create-pmbot-task",
        help="Create a safe local-only PMBOT task packet from a supported template.",
    )
    _add_queue_root(pmbot_parser)
    pmbot_parser.add_argument("--task-id", required=True)
    pmbot_parser.add_argument("--template", required=True, choices=SUPPORTED_PMBOT_TEMPLATES)
    pmbot_parser.add_argument("--repo-root", default=".")
    pmbot_parser.add_argument("--branch", default="master")
    pmbot_parser.add_argument("--expected-head", default=None)
    pmbot_parser.add_argument("--overwrite", action="store_true")
    pmbot_parser.set_defaults(func=_cmd_create_pmbot_task)

    approve_parser = subparsers.add_parser("approve", help="Approve a safe inbox task.")
    _add_queue_root(approve_parser)
    approve_parser.add_argument("--task-id", required=True)
    approve_parser.set_defaults(func=_cmd_approve)

    plan_parser = subparsers.add_parser("plan", help="Run the dry-run planner for approved tasks.")
    _add_queue_root(plan_parser)
    plan_parser.set_defaults(func=_cmd_plan)

    run_codex_parser = subparsers.add_parser(
        "run-codex-once",
        help="Run Codex CLI once for one approved/planned task handoff prompt.",
    )
    _add_queue_root(run_codex_parser)
    run_codex_parser.add_argument("--task-id", required=True)
    run_codex_parser.add_argument("--dry-run", action="store_true")
    run_codex_parser.add_argument("--timeout-seconds", type=int, default=DEFAULT_TIMEOUT_SECONDS)
    run_codex_parser.set_defaults(func=_cmd_run_codex_once)

    run_codex_batch_parser = subparsers.add_parser(
        "run-codex-batch",
        help="Run a supervised bounded batch of approved/planned Codex CLI tasks.",
    )
    _add_queue_root(run_codex_batch_parser)
    run_codex_batch_parser.add_argument("--max-tasks", type=int, default=DEFAULT_MAX_TASKS)
    run_codex_batch_parser.add_argument("--dry-run", action="store_true")
    run_codex_batch_parser.add_argument("--task-id", action="append", default=[])
    run_codex_batch_parser.add_argument("--timeout-seconds", type=int, default=DEFAULT_TIMEOUT_SECONDS)
    run_codex_batch_parser.set_defaults(func=_cmd_run_codex_batch)

    postprocess_codex_batch_parser = subparsers.add_parser(
        "postprocess-codex-batch",
        help="Bridge completed Codex batch results and optionally run ingestion/review.",
    )
    _add_queue_root(postprocess_codex_batch_parser)
    postprocess_codex_batch_parser.add_argument("--batch-report", required=True)
    postprocess_codex_batch_parser.add_argument("--bridge-results", action="store_true")
    postprocess_codex_batch_parser.add_argument("--review-results", action="store_true")
    postprocess_codex_batch_parser.add_argument("--overwrite-results", action="store_true")
    postprocess_codex_batch_parser.set_defaults(func=_cmd_postprocess_codex_batch)

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
    return _exit_code_for_report(result)


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


def _cmd_inspect_plan_contract(args: argparse.Namespace) -> dict[str, Any]:
    plan = load_plan_contract(args.plan_file)
    validation = validate_plan_contract(plan)
    status = "ok" if validation.valid else "blocked"
    return write_operator_action_report(
        args.queue_root,
        _action(
            "inspect-plan",
            status,
            "",
            args.queue_root,
            source_path=args.plan_file,
            errors=list(validation.errors),
            warnings=list(validation.warnings),
            next_operator_action=(
                "Create the queue or run the plan with a bounded local executor."
                if validation.valid
                else "Fix plan validation errors before queue creation."
            ),
            extra={
                "plan_validation": validation.to_dict(),
                "plan_id": plan.plan_id,
                "task_count": len(plan.tasks),
                "codex_execution_added": False,
                "network_calls_performed": 0,
            },
        ),
    )


def _cmd_plan_to_generated_queue(args: argparse.Namespace) -> dict[str, Any]:
    result = create_queue_from_plan(
        args.plan_file,
        args.queue_root,
        run_id=args.run_id,
        dry_run=args.dry_run,
    )
    status = "ok" if result.status in {"created", "dry_run"} else "blocked"
    return write_operator_action_report(
        args.queue_root,
        _action(
            "plan-to-queue",
            status,
            "",
            args.queue_root,
            source_path=args.plan_file,
            destination_path=result.queue_paths.get("run_root", ""),
            errors=list(result.errors),
            warnings=list(result.warnings),
            next_operator_action=(
                "Run run-plan or continue-plan with a bounded executor."
                if status == "ok"
                else "Fix plan errors before materializing the queue."
            ),
            extra={
                "queue_creation": result.to_dict(),
                "plan_id": result.plan_id,
                "run_id": result.run_id,
                "task_count": result.task_count,
                "codex_execution_added": False,
                "network_calls_performed": 0,
            },
        ),
    )


def _cmd_run_plan_contract(args: argparse.Namespace) -> dict[str, Any]:
    plan = load_plan_contract(args.plan_file)
    controller = LongRunController(repo_root=plan.repo_root or ".")
    result = controller.run_plan(
        args.plan_file,
        args.queue_root,
        mode=args.mode,
        max_steps=args.max_steps,
        executor=args.executor,
        continue_until=args.continue_until,
        run_id=args.run_id,
        commit=args.commit,
        push=args.push,
        dry_run=args.dry_run,
    )
    return _write_plan_runner_action(args.queue_root, "run-plan", result, args.plan_file)


def _cmd_continue_plan_contract(args: argparse.Namespace) -> dict[str, Any]:
    controller = LongRunController(repo_root=".")
    result = controller.continue_plan(
        args.run_id,
        args.queue_root,
        max_steps=args.max_steps,
        executor=args.executor,
        continue_until=args.continue_until,
    )
    return _write_plan_runner_action(args.queue_root, "continue-plan", result, "")


def _cmd_recover_plan_contract(args: argparse.Namespace) -> dict[str, Any]:
    controller = LongRunController(repo_root=".")
    result = controller.recover_plan(
        args.run_id,
        args.queue_root,
        allow_stale_lock_clear=args.allow_stale_lock_clear,
    )
    status = "ok" if result.get("status") in {"found", "recovered"} else "blocked"
    return write_operator_action_report(
        args.queue_root,
        _action(
            "recover-plan",
            status,
            "",
            args.queue_root,
            errors=list(result.get("errors", [])),
            next_operator_action=(
                "Review recovery report and continue-plan if safe."
                if status == "ok"
                else "Resolve recovery blockers before continuing."
            ),
            extra={"plan_recovery": result, "run_id": args.run_id, "codex_execution_added": False},
        ),
    )


def _cmd_export_next_codex_prompt(args: argparse.Namespace) -> dict[str, Any]:
    controller = LongRunController(repo_root=".")
    result = controller.continue_plan(
        args.run_id,
        args.queue_root,
        max_steps=1,
        executor="handoff",
        continue_until="one_step",
    )
    return _write_plan_runner_action(args.queue_root, "export-next-codex-prompt", result, "")


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


def _cmd_create_pmbot_task(args: argparse.Namespace) -> dict[str, Any]:
    root = ensure_queue_directories(args.queue_root)
    task_id = validate_task_id(args.task_id)
    destination = task_packet_path(root, "inbox", task_id)
    if destination.exists() and not args.overwrite:
        return write_operator_action_report(
            root,
            _action(
                "create-pmbot-task",
                "blocked",
                task_id,
                root,
                destination_path=destination,
                errors=[f"task packet already exists: {destination}"],
                next_operator_action="Use --overwrite only when replacing this PMBOT packet is intentional.",
            ),
        )

    packet = build_pmbot_task_packet(
        task_id,
        args.template,
        repo_root=args.repo_root,
        base_branch=args.branch,
        expected_head=args.expected_head,
    )
    validation = validate_packet(packet)
    approved_view = dict(packet)
    approved_view["status"] = "approved"
    approved_view["approved_by"] = "operator_cli_preflight"
    approved_view["approved_at"] = _utc_iso()
    approval_validation = validate_packet(approved_view)
    classification = classify_packet(approved_view, approval_validation)
    if not validation.valid or not approval_validation.valid or not classification.allowed:
        errors = list(validation.errors) + list(approval_validation.errors) + list(classification.reasons)
        return write_operator_action_report(
            root,
            _action(
                "create-pmbot-task",
                "blocked",
                task_id,
                root,
                errors=errors,
                warnings=[f"safety classification: {classification.status}"],
                next_operator_action="Revise the PMBOT template before creating an inbox task packet.",
            ),
        )

    write_json_atomic(destination, packet, overwrite=args.overwrite)
    return write_operator_action_report(
        root,
        _action(
            "create-pmbot-task",
            "ok",
            task_id,
            root,
            destination_path=destination,
            next_operator_action="Review the PMBOT inbox packet, then run approve only if it remains safe.",
            extra={
                "template": args.template,
                "project": packet.get("project"),
                "validation": validation.to_dict(),
                "approval_preflight_classification": classification.to_dict(),
            },
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


def _cmd_run_codex_once(args: argparse.Namespace) -> dict[str, Any]:
    root = ensure_queue_directories(args.queue_root)
    task_id = validate_task_id(args.task_id)
    report = run_codex_once(
        root,
        task_id=task_id,
        dry_run=args.dry_run,
        timeout_seconds=args.timeout_seconds,
    )
    status = "ok" if report["status"] == "ok" else report["status"]
    return write_operator_action_report(
        root,
        _action(
            "run-codex-once",
            status,
            task_id,
            root,
            source_path=report.get("paths", {}).get("handoff_prompt") or "",
            destination_path=report.get("paths", {}).get("execution_dir") or "",
            errors=list(report.get("errors", [])),
            warnings=list(report.get("warnings", [])),
            next_operator_action=str(report.get("next_operator_action", "")),
            extra={
                "codex_cli_execution_report_paths": report["report_paths"],
                "execution_status": report["execution_status"],
                "dry_run": report["dry_run"],
                "command": report["command"],
                "codex_exec_invoked": report["codex_exec_invoked"],
                "codex_invocation_count": report["codex_invocation_count"],
                "exit_code": report["exit_code"],
                "result_ingested_automatically": report["result_ingested_automatically"],
                "task_marked_done_automatically": report["task_marked_done_automatically"],
                "review_approved_automatically": report["review_approved_automatically"],
                "git_push_performed": report["git_push_performed"],
                "scheduler_created": report["scheduler_created"],
                "daemon_created": report["daemon_created"],
                "background_worker_created": report["background_worker_created"],
                "multi_task_loop_created": report["multi_task_loop_created"],
            },
        ),
    )


def _cmd_run_codex_batch(args: argparse.Namespace) -> dict[str, Any]:
    root = ensure_queue_directories(args.queue_root)
    report = run_codex_batch(
        root,
        max_tasks=args.max_tasks,
        dry_run=args.dry_run,
        task_ids=args.task_id or None,
        timeout_seconds=args.timeout_seconds,
    )
    status = "ok" if report["status"] == "ok" else report["status"]
    return write_operator_action_report(
        root,
        _action(
            "run-codex-batch",
            status,
            "",
            root,
            destination_path=report["report_paths"].get("batch_report_json", ""),
            errors=list(report.get("errors", [])),
            warnings=list(report.get("warnings", [])),
            next_operator_action=str(report.get("next_operator_action", "")),
            extra={
                "codex_cli_batch_report_paths": report["report_paths"],
                "execution_status": report["execution_status"],
                "dry_run": report["dry_run"],
                "max_tasks": report["max_tasks"],
                "hard_max_tasks": HARD_MAX_TASKS,
                "selected_task_ids": report["selected_task_ids"],
                "skipped_task_ids": report["skipped_task_ids"],
                "task_order": report["task_order"],
                "task_executions": report["task_executions"],
                "stopped_on_task_id": report["stopped_on_task_id"],
                "stopped_reason": report["stopped_reason"],
                "one_task_runner_invocation_count": report["one_task_runner_invocation_count"],
                "would_invoke_one_task_runner_count": report["would_invoke_one_task_runner_count"],
                "codex_exec_invoked": report["codex_exec_invoked"],
                "codex_invocation_count": report["codex_invocation_count"],
                "result_ingested_automatically": report["result_ingested_automatically"],
                "task_marked_done_automatically": report["task_marked_done_automatically"],
                "review_approved_automatically": report["review_approved_automatically"],
                "git_commit_performed": report["git_commit_performed"],
                "git_push_performed": report["git_push_performed"],
                "scheduler_created": report["scheduler_created"],
                "daemon_created": report["daemon_created"],
                "background_worker_created": report["background_worker_created"],
                "infinite_loop_created": report["infinite_loop_created"],
            },
        ),
    )


def _cmd_postprocess_codex_batch(args: argparse.Namespace) -> dict[str, Any]:
    root = ensure_queue_directories(args.queue_root)
    report = postprocess_codex_batch(
        root,
        batch_report_path=args.batch_report,
        bridge_results=args.bridge_results,
        review_results=args.review_results,
        overwrite_results=args.overwrite_results,
        review_result_func=build_review_report,
    )
    status = "ok" if report["status"] == "ok" else "blocked"
    return write_operator_action_report(
        root,
        _action(
            "postprocess-codex-batch",
            status,
            "",
            root,
            source_path=report.get("batch_report_path", ""),
            destination_path=report["report_paths"].get("post_batch_summary_json", ""),
            errors=list(report.get("errors", [])),
            warnings=list(report.get("warnings", [])),
            next_operator_action=str(report.get("next_operator_action", "")),
            extra={
                "post_batch_summary_report_paths": report["report_paths"],
                "batch_run_id": report.get("batch_run_id"),
                "bridge_results": report["bridge_results"],
                "review_results": report["review_results"],
                "overwrite_results": report["overwrite_results"],
                "task_results": report["task_results"],
                "completed_execution_count": report["completed_execution_count"],
                "bridged_count": report["bridged_count"],
                "ingested_count": report["ingested_count"],
                "reviewed_count": report["reviewed_count"],
                "blocked_count": report["blocked_count"],
                "skipped_count": report["skipped_count"],
                "result_json_written_count": report["result_json_written_count"],
                "task_marked_done_automatically": report["task_marked_done_automatically"],
                "review_approved_automatically": report["review_approved_automatically"],
                "git_commit_performed": report["git_commit_performed"],
                "git_push_performed": report["git_push_performed"],
                "scheduler_created": report["scheduler_created"],
                "daemon_created": report["daemon_created"],
                "background_worker_created": report["background_worker_created"],
                "infinite_loop_created": report["infinite_loop_created"],
                "codex_exec_invoked": report["codex_exec_invoked"],
                "codex_invocation_count": report["codex_invocation_count"],
                "openrouter_calls_performed": report["openrouter_calls_performed"],
                "polymarket_api_calls_performed": report["polymarket_api_calls_performed"],
                "wallet_or_private_key_access": report["wallet_or_private_key_access"],
                "orders_or_trading_actions": report["orders_or_trading_actions"],
                "runtime_or_dispatcher_changes": report["runtime_or_dispatcher_changes"],
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
        errors.append("stable task-specific ingestion report status must be allowed")

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
    latest_ingestion_pointer = safe_queue_path(root, "reports", "latest_result_ingestion_report.json")
    latest_stable_ingestion = _latest_stable_ingestion_report(root)
    report = {
        "run_id": _run_id(),
        "queue_root": str(root),
        "counts": counts,
        "artifact_counts": artifact_counts,
        "latest_dry_run_report_path": str(latest_dry_run) if latest_dry_run else None,
        "latest_result_ingestion_report_path": str(latest_ingestion_pointer) if latest_ingestion_pointer.exists() else None,
        "latest_result_ingestion_report_is_pointer": latest_ingestion_pointer.exists(),
        "latest_stable_result_ingestion_report_path": (
            str(latest_stable_ingestion) if latest_stable_ingestion else None
        ),
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
    latest = reports_dir / "latest_result_ingestion_report.json"
    candidate_paths = sorted(reports_dir.glob("result_ingestion_report_*.json"), key=_mtime, reverse=True)

    latest_seen_path: str | None = str(latest) if latest.exists() else None
    latest_seen_status: str | None = None
    latest_seen_task_id: str | None = None
    matching_reports: list[dict[str, Any]] = []
    errors: list[str] = []

    if latest.exists():
        try:
            latest_payload = read_json(latest)
            if isinstance(latest_payload, Mapping):
                latest_seen_status = str(latest_payload.get("ingestion_status"))
                latest_seen_task_id = str(latest_payload.get("task_id"))
        except json.JSONDecodeError as exc:
            errors.append(f"{latest}: invalid JSON: {exc}")

    for path in candidate_paths:
        try:
            payload = read_json(path)
        except json.JSONDecodeError as exc:
            errors.append(f"{path}: invalid JSON: {exc}")
            continue
        if not isinstance(payload, Mapping):
            continue
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
                "latest_report_is_pointer": latest.exists(),
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
        "latest_report_is_pointer": latest.exists(),
        "latest_report_task_id": latest_seen_task_id,
        "latest_report_status": latest_seen_status,
        "matching_reports": matching_reports,
        "errors": errors,
    }


def _write_plan_runner_action(
    queue_root: str | Path,
    command: str,
    result: Mapping[str, Any],
    source_path: str | Path,
) -> dict[str, Any]:
    run_status = str(result.get("status", "failed"))
    cli_status = run_status if run_status in {"done", "max_steps", "requiring_operator_handoff", "dry_run"} else (
        "ok" if run_status in {"accepted", "recovered"} else run_status
    )
    payload = result.get("payload", {}) if isinstance(result.get("payload", {}), Mapping) else {}
    return write_operator_action_report(
        queue_root,
        _action(
            command,
            cli_status,
            "",
            queue_root,
            source_path=source_path,
            destination_path=payload.get("run_root", ""),
            errors=list(result.get("errors", [])),
            warnings=[],
            next_operator_action=_next_action_for_plan_runner_status(run_status),
            extra={
                "plan_runner_result": dict(result),
                "run_status": run_status,
                "run_id": str(payload.get("run_id") or ""),
                "plan_id": str(payload.get("plan_id") or ""),
                "codex_execution_added": False,
                "codex_app_server_used": False,
                "network_calls_performed": 0,
            },
        ),
    )


def _next_action_for_plan_runner_status(status: str) -> str:
    if status == "done":
        return "Review dashboard, artifacts, and selective commit/push decision."
    if status == "max_steps":
        return "Run continue-plan to continue the bounded supervised run."
    if status == "requiring_operator_handoff":
        return "Open the generated Codex handoff prompt and run it manually if approved."
    if status in {"blocked", "failed", "needs_retry"}:
        return "Inspect result details and run recover-plan or retry after review."
    if status == "dry_run":
        return "Review dry-run queue materialization before running."
    return "Inspect generated plan-runner artifacts."


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
    if action.get("run_id"):
        payload["run_id"] = str(action["run_id"])

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
        f"- latest_result_ingestion_report_pointer: `{report.get('latest_result_ingestion_report_path')}`",
        f"- latest_stable_result_ingestion_report: `{report.get('latest_stable_result_ingestion_report_path')}`",
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
    lines.extend(["## Safety", ""])
    if report["command"] == "run-codex-once":
        lines.append(
            "This operator action is supervised and one-task only. When dry_run is false and preflight passes, it invokes exactly one local `codex exec` process and captures logs; it does not call Codex app-server, start background workers, add schedulers, approve review, mark tasks done, push git branches, call network services directly, or access credentials."
        )
    elif report["command"] == "run-codex-batch":
        lines.append(
            "This operator action is supervised and bounded by --max-tasks with a hard cap of 20. In dry-run it only reports selected tasks and one-task commands; in execution mode it invokes the existing one-task runner sequentially and stops on the first failure, git preflight error, or out-of-band git state change. It does not create tasks, approve tasks, ingest results, review results, mark tasks done, commit, push, schedule itself, start a daemon, start a background worker, call network services directly, or access credentials."
        )
    elif report["command"] == "postprocess-codex-batch":
        lines.append(
            "This operator action only reads an existing batch report and Codex execution artifacts. With --bridge-results it writes queue-compatible result JSON under review; with --review-results it runs the existing ingestion and review helpers. It does not execute Codex, mark tasks done, commit, push, schedule itself, start a daemon, start a background worker, call network services directly, or access credentials."
        )
    else:
        lines.append(
            "This operator action was local-only and operator-invoked. It did not execute Codex, call Codex app-server, start background workers, add schedulers, call network services, or access credentials."
        )
    lines.append("")
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


def _latest_stable_ingestion_report(queue_root: str | Path) -> Path | None:
    reports_dir = safe_queue_path(queue_root, "reports")
    candidates = [path for path in reports_dir.glob("result_ingestion_report_*.json") if path.exists()]
    if not candidates:
        return None
    return max(candidates, key=_mtime)


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
    for key in ("run_status", "run_id", "plan_id", "task_count"):
        if key in report:
            summary[key] = report[key]
    for key, value in report.items():
        if key.endswith("_report_paths"):
            summary[key] = value
    return summary


def _exit_code_for_report(report: Mapping[str, Any]) -> int:
    status = str(report.get("status", "failed"))
    run_status = str(report.get("run_status", ""))
    success_statuses = {"ok", "done", "max_steps", "requiring_operator_handoff", "dry_run"}
    failure_statuses = {"blocked", "failed", "needs_retry", "safety_failure", "validation_failure"}
    if status in failure_statuses or run_status in failure_statuses:
        return 1
    return 0 if status in success_statuses or run_status in success_statuses else 1


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
