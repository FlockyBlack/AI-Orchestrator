from __future__ import annotations

import argparse
import json
import os
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from .automation_dashboard import build_dashboard
from .codex_cli_batch_runner import DEFAULT_MAX_TASKS, HARD_MAX_TASKS, run_codex_batch
from .codex_cli_executor import (
    build_codex_cli_command,
    load_codex_cli_executor_config,
    result_json_path_for_packet,
    validate_codex_cli_executor_config,
)
from .codex_cli_postprocessor import postprocess_codex_batch
from .codex_cli_runner import DEFAULT_TIMEOUT_SECONDS, run_codex_once
from .codex_execution_packet import (
    create_execution_packet_for_next_task,
    inspect_execution_packets,
    write_execution_packet,
    write_execution_prompt,
    write_expected_result_template,
)
from .codex_result_ingestion import ingest_codex_result, ingest_codex_result_text
from .dry_run_runner import run_dry_run
from .long_run_controller import LongRunController
from .plan_contract import load_plan_contract, validate_plan_contract
from .plan_decomposer import get_next_runnable_tasks
from .plan_recovery import inspect_run as inspect_recovery_run
from .plan_run_state import create_checkpoint, load_state, record_task_artifacts, save_state, validate_state_consistency
from .plan_to_queue import create_queue_from_plan, inspect_queue, load_queue_manifest, validate_queue_manifest
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
from ai_orchestrator.symphony_adapter import (
    build_app_server_adapter_plan,
    build_session_plan,
    build_workspace_plan_for_task,
    inspect_schema_dir,
    map_plan_task_to_symphony_task,
    map_symphony_task_to_codex_packet,
    render_app_server_start_command,
    render_workspace_setup_commands,
    validate_app_server_adapter_plan,
    validate_session_plan,
    validate_workspace_plan,
)


DEFAULT_APP_SERVER_SCHEMA_DIR = Path("C:/Users/OpenC/.openclaw/external_research/codex_app_server_schema")


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
    run_plan_parser.add_argument(
        "--executor",
        choices=("fake", "noop", "handoff", "codex_packet", "codex_cli_dry_run", "codex_cli_operator_approved_stub", "codex_cli"),
        default="fake",
    )
    run_plan_parser.add_argument("--run-id", default=None)
    run_plan_parser.add_argument("--auto-ingest", action="store_true")
    run_plan_parser.add_argument("--allow-real-codex-invocation", action="store_true")
    run_plan_parser.add_argument("--codex-config", default=None)
    run_plan_parser.add_argument("--codex-timeout-seconds", type=int, default=None)
    run_plan_parser.set_defaults(func=_cmd_run_plan_contract)

    continue_plan_parser = subparsers.add_parser("continue-plan", help="Continue a generated plan run.")
    continue_plan_parser.add_argument("--run-id", required=True)
    _add_queue_root(continue_plan_parser)
    continue_plan_parser.add_argument("--max-steps", type=int, default=50)
    continue_plan_parser.add_argument("--continue-until", default="blocked_or_done")
    continue_plan_parser.add_argument(
        "--executor",
        choices=("fake", "noop", "handoff", "codex_packet", "codex_cli_dry_run", "codex_cli_operator_approved_stub", "codex_cli"),
        default="fake",
    )
    continue_plan_parser.add_argument("--stop-after-current", action="store_true")
    continue_plan_parser.add_argument("--auto-ingest", action="store_true")
    continue_plan_parser.add_argument("--allow-real-codex-invocation", action="store_true")
    continue_plan_parser.add_argument("--codex-config", default=None)
    continue_plan_parser.add_argument("--codex-timeout-seconds", type=int, default=None)
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

    create_packet_parser = subparsers.add_parser(
        "create-codex-packet",
        help="Create a safe Codex execution packet for the next runnable task without invoking Codex.",
    )
    create_packet_parser.add_argument("--run-id", required=True)
    _add_queue_root(create_packet_parser)
    create_packet_parser.add_argument(
        "--adapter-mode",
        choices=("manual_handoff", "codex_cli_dry_run", "codex_cli_operator_approved"),
        default="manual_handoff",
    )
    create_packet_parser.add_argument("--task-id", default=None)
    create_packet_parser.set_defaults(func=_cmd_create_codex_packet)

    symphony_task_plan_parser = subparsers.add_parser(
        "create-symphony-task-plan",
        help="Create a Symphony-style workspace/session/app-server plan for the next runnable task.",
    )
    symphony_task_plan_parser.add_argument("--run-id", required=True)
    _add_queue_root(symphony_task_plan_parser)
    symphony_task_plan_parser.add_argument("--workspace-root", required=True)
    symphony_task_plan_parser.add_argument("--app-server-schema-dir", default=str(DEFAULT_APP_SERVER_SCHEMA_DIR))
    symphony_task_plan_parser.set_defaults(func=_cmd_create_symphony_task_plan)

    ingest_codex_parser = subparsers.add_parser(
        "ingest-codex-result",
        help="Validate and ingest a Codex adapter result JSON file.",
    )
    ingest_codex_parser.add_argument("--packet-path", required=True)
    ingest_codex_parser.add_argument("--result-json", required=True)
    _add_queue_root(ingest_codex_parser)
    ingest_codex_parser.set_defaults(func=_cmd_ingest_codex_result)

    ingest_codex_text_parser = subparsers.add_parser(
        "ingest-codex-result-text",
        help="Validate and ingest a Codex adapter result JSON stored in a text file.",
    )
    ingest_codex_text_parser.add_argument("--packet-path", required=True)
    ingest_codex_text_parser.add_argument("--result-text-file", required=True)
    _add_queue_root(ingest_codex_text_parser)
    ingest_codex_text_parser.set_defaults(func=_cmd_ingest_codex_result_text)

    adapter_dry_run_parser = subparsers.add_parser(
        "codex-adapter-dry-run",
        help="Render the future Codex CLI command and packet without invoking Codex.",
    )
    adapter_dry_run_parser.add_argument("--run-id", required=True)
    _add_queue_root(adapter_dry_run_parser)
    adapter_dry_run_parser.add_argument("--adapter-mode", choices=("codex_cli_dry_run",), default="codex_cli_dry_run")
    adapter_dry_run_parser.set_defaults(func=_cmd_codex_adapter_dry_run)

    test_codex_cli_config_parser = subparsers.add_parser(
        "test-codex-cli-config",
        help="Validate real Codex CLI executor config without invoking Codex.",
    )
    _add_queue_root(test_codex_cli_config_parser)
    test_codex_cli_config_parser.add_argument("--codex-config", default=None)
    test_codex_cli_config_parser.set_defaults(func=_cmd_test_codex_cli_config)

    print_codex_cli_command_parser = subparsers.add_parser(
        "print-codex-cli-command",
        help="Render the real Codex CLI command for the next runnable task without invoking Codex.",
    )
    print_codex_cli_command_parser.add_argument("--run-id", required=True)
    _add_queue_root(print_codex_cli_command_parser)
    print_codex_cli_command_parser.add_argument("--task-id", default=None)
    print_codex_cli_command_parser.add_argument("--codex-config", default=None)
    print_codex_cli_command_parser.set_defaults(func=_cmd_print_codex_cli_command)

    inspect_run_parser = subparsers.add_parser("inspect-run", help="Inspect a generated plan run.")
    inspect_run_parser.add_argument("--run-id", required=True)
    _add_queue_root(inspect_run_parser)
    inspect_run_parser.set_defaults(func=_cmd_inspect_run)

    list_runs_parser = subparsers.add_parser("list-runs", help="List generated plan runs.")
    _add_queue_root(list_runs_parser)
    list_runs_parser.set_defaults(func=_cmd_list_runs)

    validate_state_parser = subparsers.add_parser("validate-state", help="Validate run state consistency against its plan.")
    validate_state_parser.add_argument("--run-id", required=True)
    _add_queue_root(validate_state_parser)
    validate_state_parser.set_defaults(func=_cmd_validate_state)

    checkpoint_run_parser = subparsers.add_parser("checkpoint-run", help="Create a manual checkpoint for a generated run.")
    checkpoint_run_parser.add_argument("--run-id", required=True)
    checkpoint_run_parser.add_argument("--reason", required=True)
    _add_queue_root(checkpoint_run_parser)
    checkpoint_run_parser.set_defaults(func=_cmd_checkpoint_run)

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
        executor_options=_codex_executor_options(args),
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
        stop_after_current=args.stop_after_current,
        executor_options=_codex_executor_options(args),
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


def _cmd_create_codex_packet(args: argparse.Namespace) -> dict[str, Any]:
    packet = create_execution_packet_for_next_task(
        args.run_id,
        args.queue_root,
        adapter_mode=args.adapter_mode,
        task_id=args.task_id,
    )
    output_dir = Path(packet.prompt_path).parent
    packet_path = write_execution_packet(packet, output_dir)
    prompt_path = write_execution_prompt(packet, output_dir)
    template_path = write_expected_result_template(packet, output_dir)
    _record_packet_artifacts_for_dashboard(
        packet,
        args.queue_root,
        [str(packet_path), str(prompt_path), str(template_path), str(output_dir / "README.md")],
    )
    inspection = inspect_execution_packets(args.run_id, args.queue_root)
    return write_operator_action_report(
        args.queue_root,
        _action(
            "create-codex-packet",
            "ok",
            packet.task_id,
            args.queue_root,
            source_path=packet.task_spec_path,
            destination_path=str(packet_path),
            next_operator_action="Open prompt.md, run it manually only if approved, then ingest the returned JSON.",
            extra={
                "run_id": packet.run_id,
                "plan_id": packet.plan_id,
                "packet_id": packet.packet_id,
                "adapter_mode": packet.adapter_mode,
                "requires_operator_approval": packet.requires_operator_approval,
                "execution_packet_path": str(packet_path),
                "execution_prompt_path": str(prompt_path),
                "expected_result_template_path": str(template_path),
                "codex_packets": inspection,
                "codex_execution_added": False,
                "codex_invoked": False,
                "network_calls_performed": 0,
            },
        ),
    )


def _cmd_create_symphony_task_plan(args: argparse.Namespace) -> dict[str, Any]:
    inspection = inspect_queue(args.queue_root, args.run_id)
    if inspection["status"] not in {"found", "invalid"}:
        return write_operator_action_report(
            args.queue_root,
            _action(
                "create-symphony-task-plan",
                "blocked",
                "",
                args.queue_root,
                errors=list(inspection.get("errors", [])),
                next_operator_action="Create or recover a generated run before building a Symphony task plan.",
                extra={"run_id": args.run_id, "codex_app_server_used": False, "real_app_server_started": False},
            ),
        )
    manifest = dict(inspection.get("manifest", {}))
    plan_file = str(manifest.get("source_plan_file") or "")
    state_path = Path(str(manifest.get("state_path") or inspection.get("state_path") or ""))
    plan = load_plan_contract(plan_file)
    state = load_state(state_path)
    next_tasks = get_next_runnable_tasks(
        plan.tasks,
        completed=state.completed_task_ids,
        blocked=state.blocked_task_ids,
        failed=state.failed_task_ids,
    )
    if not next_tasks:
        return write_operator_action_report(
            args.queue_root,
            _action(
                "create-symphony-task-plan",
                "blocked",
                "",
                args.queue_root,
                source_path=state_path,
                errors=["no runnable task available for Symphony task plan"],
                next_operator_action="Inspect run state; there is no next runnable task.",
                extra={"run_id": args.run_id, "plan_id": plan.plan_id, "codex_app_server_used": False},
            ),
        )

    task = next_tasks[0]
    symphony_task = map_plan_task_to_symphony_task(task, state, plan)
    task_source = dict(symphony_task.source.to_dict())
    task_source.update(
        {
            "source_plan_file": plan_file,
            "task_spec_path": str(dict(manifest.get("task_paths", {})).get(task.task_id) or ""),
            "state_path": str(state_path),
            "manifest_path": str(inspection.get("manifest_path") or ""),
        }
    )
    symphony_task = symphony_task.from_dict({**symphony_task.to_dict(), "source": task_source})
    repo_root = plan.repo_root or "."
    workspace_plan = build_workspace_plan_for_task(symphony_task, repo_root, args.workspace_root)
    session_plan = build_session_plan(symphony_task, workspace_plan, args.app_server_schema_dir)
    schema_index = inspect_schema_dir(args.app_server_schema_dir)
    app_server_adapter_plan = build_app_server_adapter_plan(session_plan, schema_index)
    codex_packet_preview = map_symphony_task_to_codex_packet(symphony_task, workspace_plan, session_plan)

    workspace_validation = validate_workspace_plan(workspace_plan)
    session_validation = validate_session_plan(session_plan)
    app_server_validation = validate_app_server_adapter_plan(app_server_adapter_plan)
    errors = (
        list(workspace_validation["errors"])
        + list(session_validation["errors"])
        + list(app_server_validation["errors"])
        + list(schema_index.errors)
    )
    warnings = (
        list(workspace_validation["warnings"])
        + list(session_validation["warnings"])
        + list(app_server_validation["warnings"])
        + list(schema_index.warnings)
    )

    output_dir = Path(str(inspection["run_dir"])) / "symphony_tasks" / task.task_id
    artifact_paths = {
        "symphony_task": str(output_dir / "symphony_task.json"),
        "workspace_plan": str(output_dir / "workspace_plan.json"),
        "session_plan": str(output_dir / "session_plan.json"),
        "app_server_adapter_plan": str(output_dir / "app_server_adapter_plan.json"),
        "codex_packet_preview": str(output_dir / "codex_packet_preview.json"),
        "readme": str(output_dir / "README.md"),
    }
    _write_symphony_json(output_dir / "symphony_task.json", symphony_task.to_dict())
    _write_symphony_json(output_dir / "workspace_plan.json", workspace_plan.to_dict())
    _write_symphony_json(output_dir / "session_plan.json", session_plan.to_dict())
    _write_symphony_json(output_dir / "app_server_adapter_plan.json", app_server_adapter_plan.to_dict())
    _write_symphony_json(output_dir / "codex_packet_preview.json", codex_packet_preview)
    _write_symphony_text(
        output_dir / "README.md",
        _render_symphony_task_plan_readme(
            symphony_task.to_dict(),
            workspace_plan.to_dict(),
            session_plan.to_dict(),
            app_server_adapter_plan.to_dict(),
        ),
    )

    status = "ok" if not errors else "blocked"
    return write_operator_action_report(
        args.queue_root,
        _action(
            "create-symphony-task-plan",
            status,
            task.task_id,
            args.queue_root,
            source_path=task_source["task_spec_path"],
            destination_path=output_dir,
            errors=list(dict.fromkeys(errors)),
            warnings=list(dict.fromkeys(warnings)),
            next_operator_action=(
                "Review Symphony task artifacts; app-server command is rendered only and was not executed."
                if status == "ok"
                else "Resolve validation errors before using this Symphony task plan."
            ),
            extra={
                "run_id": state.run_id,
                "plan_id": plan.plan_id,
                "symphony_task_plan": {
                    "task_id": task.task_id,
                    "artifact_dir": str(output_dir),
                    "artifact_paths": artifact_paths,
                    "workspace_setup_commands": list(render_workspace_setup_commands(workspace_plan)),
                    "app_server_start_command": render_app_server_start_command(app_server_adapter_plan)
                    if app_server_validation["valid"]
                    else "",
                    "schema_index_passed": not schema_index.errors,
                    "symphony_mapping_passed": symphony_task.status.runnable,
                    "app_server_adapter_boundary_ready": app_server_validation["valid"],
                },
                "schema_index_passed": not schema_index.errors,
                "symphony_mapping_passed": symphony_task.status.runnable,
                "app_server_adapter_boundary_ready": app_server_validation["valid"],
                "codex_app_server_used": False,
                "real_app_server_started": False,
                "real_codex_self_invocation": False,
                "daemon_created": False,
                "scheduler_created": False,
                "background_worker_created": False,
                "network_calls_performed": 0,
            },
        ),
    )


def _cmd_ingest_codex_result(args: argparse.Namespace) -> dict[str, Any]:
    result = ingest_codex_result(args.packet_path, args.result_json, args.queue_root)
    status = "ok" if result["status"] in {"accepted", "blocked", "failed", "needs_retry"} else "blocked"
    return write_operator_action_report(
        args.queue_root,
        _action(
            "ingest-codex-result",
            status,
            result.get("task_id", ""),
            args.queue_root,
            source_path=args.result_json,
            destination_path=result.get("report_paths", {}).get("json", ""),
            errors=list(result.get("errors", [])),
            warnings=list(result.get("warnings", [])),
            next_operator_action=result.get("next_operator_action", ""),
            extra={
                "codex_result_ingestion": result,
                "run_id": result.get("run_id", ""),
                "packet_id": result.get("packet_id", ""),
                "codex_execution_added": False,
                "codex_invoked": False,
                "network_calls_performed": 0,
            },
        ),
    )


def _cmd_ingest_codex_result_text(args: argparse.Namespace) -> dict[str, Any]:
    result_text = Path(args.result_text_file).read_text(encoding="utf-8")
    result = ingest_codex_result_text(
        args.packet_path,
        result_text,
        args.queue_root,
        result_json_path=args.result_text_file,
    )
    status = "ok" if result["status"] in {"accepted", "blocked", "failed", "needs_retry"} else "blocked"
    return write_operator_action_report(
        args.queue_root,
        _action(
            "ingest-codex-result-text",
            status,
            result.get("task_id", ""),
            args.queue_root,
            source_path=args.result_text_file,
            destination_path=result.get("report_paths", {}).get("json", ""),
            errors=list(result.get("errors", [])),
            warnings=list(result.get("warnings", [])),
            next_operator_action=result.get("next_operator_action", ""),
            extra={
                "codex_result_ingestion": result,
                "packet_id": result.get("packet_id", ""),
                "codex_execution_added": False,
                "codex_invoked": False,
                "network_calls_performed": 0,
            },
        ),
    )


def _cmd_codex_adapter_dry_run(args: argparse.Namespace) -> dict[str, Any]:
    controller = LongRunController(repo_root=".")
    result = controller.continue_plan(
        args.run_id,
        args.queue_root,
        max_steps=1,
        executor="codex_cli_dry_run",
        continue_until="one_step",
    )
    return _write_plan_runner_action(args.queue_root, "codex-adapter-dry-run", result, "")


def _cmd_test_codex_cli_config(args: argparse.Namespace) -> dict[str, Any]:
    config_path = _codex_config_path(args.queue_root, getattr(args, "codex_config", None))
    config = load_codex_cli_executor_config(config_path)
    validation = validate_codex_cli_executor_config(config)
    command = build_codex_cli_command(_preview_packet_for_config(args.queue_root), config) if _command_can_preview(config) else []
    executable_status = _executable_status(command)
    errors = list(validation["errors"])
    if command and not executable_status["available"]:
        errors.append(str(executable_status["error"]))
    status = "ok" if validation["valid"] and executable_status["available"] else "blocked"
    return write_operator_action_report(
        args.queue_root,
        _action(
            "test-codex-cli-config",
            status,
            "",
            args.queue_root,
            source_path=config_path,
            errors=errors,
            warnings=list(validation["warnings"]),
            next_operator_action=(
                "Codex CLI config is enabled and command is resolvable."
                if status == "ok"
                else "Enable a safe config and install or configure the Codex command before real invocation."
            ),
            extra={
                "codex_cli_config": config.to_dict(),
                "codex_cli_config_validation": validation,
                "codex_cli_executable": executable_status,
                "command_preview": command,
                "codex_execution_added": False,
                "codex_invoked": False,
                "network_calls_performed": 0,
            },
        ),
    )


def _cmd_print_codex_cli_command(args: argparse.Namespace) -> dict[str, Any]:
    config_path = _codex_config_path(args.queue_root, getattr(args, "codex_config", None))
    config = load_codex_cli_executor_config(config_path)
    packet = create_execution_packet_for_next_task(
        args.run_id,
        args.queue_root,
        adapter_mode="codex_cli_operator_approved",
        task_id=args.task_id,
    )
    output_dir = Path(packet.prompt_path).parent
    packet_path = write_execution_packet(packet, output_dir)
    prompt_path = write_execution_prompt(packet, output_dir)
    template_path = write_expected_result_template(packet, output_dir)
    command = build_codex_cli_command(packet, config)
    validation = validate_codex_cli_executor_config(config)
    executable_status = _executable_status(command)
    return write_operator_action_report(
        args.queue_root,
        _action(
            "print-codex-cli-command",
            "ok",
            packet.task_id,
            args.queue_root,
            source_path=packet.task_spec_path,
            destination_path=str(packet_path),
            warnings=list(validation["warnings"]),
            next_operator_action="Review the command preview; no Codex process was started.",
            extra={
                "run_id": packet.run_id,
                "plan_id": packet.plan_id,
                "packet_id": packet.packet_id,
                "adapter_mode": packet.adapter_mode,
                "requires_operator_approval": packet.requires_operator_approval,
                "execution_packet_path": str(packet_path),
                "execution_prompt_path": str(prompt_path),
                "expected_result_template_path": str(template_path),
                "result_json_path": str(result_json_path_for_packet(packet, config)),
                "codex_cli_config_path": str(config_path),
                "codex_cli_config_validation": validation,
                "codex_cli_executable": executable_status,
                "codex_cli_command": command,
                "codex_execution_added": False,
                "codex_invoked": False,
                "network_calls_performed": 0,
            },
        ),
    )


def _cmd_inspect_run(args: argparse.Namespace) -> dict[str, Any]:
    inspection = inspect_recovery_run(args.run_id, args.queue_root)
    status = "ok" if inspection.get("status") in {"found", "invalid_manifest"} else "blocked"
    return write_operator_action_report(
        args.queue_root,
        _action(
            "inspect-run",
            status,
            "",
            args.queue_root,
            source_path=inspection.get("manifest_path", ""),
            destination_path=inspection.get("run_root", ""),
            errors=list(inspection.get("errors", [])),
            warnings=list(inspection.get("warnings", [])),
            next_operator_action=(
                "Review run state, dashboard, and choose continue-plan or recover-plan."
                if status == "ok"
                else "Select an existing run_id or create a queue first."
            ),
            extra={
                "run_inspection": inspection,
                "run_id": args.run_id,
                "plan_id": str(inspection.get("plan_id") or ""),
                "codex_execution_added": False,
            },
        ),
    )


def _cmd_list_runs(args: argparse.Namespace) -> dict[str, Any]:
    root = Path(args.queue_root)
    runs: list[dict[str, Any]] = []
    for manifest_path in sorted(root.glob("generated/*/*/manifest.json")):
        manifest = read_json(manifest_path)
        if not isinstance(manifest, Mapping):
            continue
        state_path = Path(str(manifest.get("state_path") or manifest_path.parent / "state.json"))
        state_payload = read_json(state_path) if state_path.exists() else {}
        completed = list(state_payload.get("completed_task_ids", [])) if isinstance(state_payload, Mapping) else []
        blocked = list(state_payload.get("blocked_task_ids", [])) if isinstance(state_payload, Mapping) else []
        failed = list(state_payload.get("failed_task_ids", [])) if isinstance(state_payload, Mapping) else []
        total = int(manifest.get("task_count", 0) or 0)
        runs.append(
            {
                "run_id": str(manifest.get("run_id") or manifest_path.parent.name),
                "plan_id": str(manifest.get("plan_id") or manifest_path.parent.parent.name),
                "status": str(state_payload.get("status") or manifest.get("status") or "unknown") if isinstance(state_payload, Mapping) else "missing_state",
                "completed_count": len(completed),
                "blocked_count": len(blocked),
                "failed_count": len(failed),
                "pending_count": max(0, total - len(completed) - len(blocked) - len(failed)),
                "task_count": total,
                "updated_at": str(state_payload.get("updated_at") or manifest.get("updated_at") or "") if isinstance(state_payload, Mapping) else str(manifest.get("updated_at") or ""),
                "manifest_path": str(manifest_path),
                "state_path": str(state_path),
            }
        )
    return write_operator_action_report(
        args.queue_root,
        _action(
            "list-runs",
            "ok",
            "",
            args.queue_root,
            next_operator_action="Pick a run_id for inspect-run, continue-plan, recover-plan, or export-next-codex-prompt.",
            extra={
                "runs": runs,
                "run_count": len(runs),
                "codex_execution_added": False,
            },
        ),
    )


def _cmd_validate_state(args: argparse.Namespace) -> dict[str, Any]:
    inspection = inspect_queue(args.queue_root, args.run_id)
    errors: list[str] = list(inspection.get("errors", []))
    validation_result: dict[str, Any] = {"consistent": False, "errors": errors}
    plan_id = str(inspection.get("plan_id") or "")
    if inspection.get("status") in {"found", "invalid"}:
        manifest = load_queue_manifest(args.queue_root, args.run_id)
        manifest_validation = validate_queue_manifest(manifest)
        errors.extend(manifest_validation["errors"])
        plan_id = str(manifest.get("plan_id") or plan_id)
        plan_file = str(manifest.get("source_plan_file") or "")
        state_path = Path(str(manifest.get("state_path") or Path(inspection["run_dir"]) / "state.json"))
        if plan_file and Path(plan_file).exists() and state_path.exists():
            plan = load_plan_contract(plan_file)
            state = load_state(state_path)
            validation_result = validate_state_consistency(state, plan)
            errors.extend(validation_result["errors"])
        elif not state_path.exists():
            errors.append(f"state file missing: {state_path}")
        else:
            errors.append(f"source plan file missing: {plan_file}")
    status = "ok" if not errors else "blocked"
    return write_operator_action_report(
        args.queue_root,
        _action(
            "validate-state",
            status,
            "",
            args.queue_root,
            errors=list(dict.fromkeys(errors)),
            next_operator_action=(
                "State is consistent; continue-plan may proceed."
                if status == "ok"
                else "Run recover-plan or repair state before continuing."
            ),
            extra={
                "state_validation": validation_result,
                "run_id": args.run_id,
                "plan_id": plan_id,
                "codex_execution_added": False,
            },
        ),
    )


def _cmd_checkpoint_run(args: argparse.Namespace) -> dict[str, Any]:
    manifest = load_queue_manifest(args.queue_root, args.run_id)
    state_path = Path(str(manifest.get("state_path") or ""))
    state = load_state(state_path)
    checkpoint = create_checkpoint(state, args.reason)
    save_state(state, state_path, updated_by="operator_cli")
    return write_operator_action_report(
        args.queue_root,
        _action(
            "checkpoint-run",
            "ok",
            "",
            args.queue_root,
            source_path=state_path,
            next_operator_action="Checkpoint written; continue-plan or recover-plan can reference the latest safe point.",
            extra={
                "checkpoint": checkpoint,
                "run_id": args.run_id,
                "plan_id": str(manifest.get("plan_id") or ""),
                "codex_execution_added": False,
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
    cli_status = run_status if run_status in {"done", "max_steps", "requiring_operator_handoff", "adapter_dry_run_ready", "dry_run"} else (
        "ok" if run_status in {"accepted", "recovered"} else run_status
    )
    payload = result.get("payload", {}) if isinstance(result.get("payload", {}), Mapping) else {}
    executor = str(payload.get("executor") or "")
    codex_cli_invocation = payload.get("codex_cli_invocation", {})
    if not isinstance(codex_cli_invocation, Mapping):
        codex_cli_invocation = {}
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
                "state_path": result.get("state_path") or payload.get("state_path", ""),
                "dashboard_path": result.get("dashboard_path") or payload.get("dashboard_path", ""),
                "execution_packet_path": result.get("execution_packet_path") or payload.get("execution_packet_path", ""),
                "execution_prompt_path": result.get("execution_prompt_path") or payload.get("execution_prompt_path", ""),
                "expected_result_template_path": result.get("expected_result_template_path") or payload.get("expected_result_template_path", ""),
                "adapter_mode": result.get("adapter_mode") or payload.get("adapter_mode", ""),
                "result_json_path": result.get("result_json_path") or payload.get("result_json_path", ""),
                "auto_ingest_status": result.get("auto_ingest_status") or payload.get("auto_ingest_status", ""),
                "codex_execution_added": executor == "codex_cli",
                "codex_invoked": bool(codex_cli_invocation.get("codex_invoked", False)),
                "codex_result_ingestion": payload.get("codex_result_ingestion", {}),
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
    if status == "adapter_dry_run_ready":
        return "Review the Codex CLI dry-run artifact; no Codex process was started."
    if status in {"blocked", "failed", "needs_retry"}:
        return "Inspect result details and run recover-plan or retry after review."
    if status in {"validation_failure", "safety_failure"}:
        return "Inspect Codex invocation, result validation, and blocker reports before retrying."
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
    elif report["command"] in {"test-codex-cli-config", "print-codex-cli-command"}:
        lines.append(
            "This operator action only validates or previews the real Codex CLI executor configuration. It does not invoke Codex, start background workers, add schedulers, call browser automation, access credentials, or perform trading actions."
        )
    elif report["command"] in {"run-plan", "continue-plan"} and report.get("codex_execution_added") is True:
        lines.append(
            "This operator action may invoke the configured Codex CLI only when executor=codex_cli, config.enabled=true, --allow-real-codex-invocation is present, and --auto-ingest is present. It is bounded by max_steps and stops on blocked, failed, safety, or validation outcomes."
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


def _render_symphony_task_plan_readme(
    symphony_task: Mapping[str, Any],
    workspace_plan: Mapping[str, Any],
    session_plan: Mapping[str, Any],
    app_server_adapter_plan: Mapping[str, Any],
) -> str:
    return "\n".join(
        [
            f"# Symphony Task Plan: {symphony_task.get('task_id', '')}",
            "",
            f"- task_id: `{symphony_task.get('task_id', '')}`",
            f"- plan_id: `{symphony_task.get('source_plan_id', '')}`",
            f"- run_id: `{symphony_task.get('source_run_id', '')}`",
            f"- workspace_path: `{workspace_plan.get('workspace_path', '')}`",
            f"- session_id: `{session_plan.get('session_id', '')}`",
            f"- app_server_listen: `{app_server_adapter_plan.get('app_server_listen', '')}`",
            f"- adapter_mode: `{app_server_adapter_plan.get('mode', '')}`",
            "",
            "This directory contains a render-only Symphony-style task/workspace/session plan. It did not create a worktree, start Codex app-server, invoke Codex, create a daemon, register a scheduler, run browser automation, or call external network services.",
            "",
        ]
    )


def _write_symphony_json(path: str | Path, payload: Mapping[str, Any]) -> Path:
    return _write_symphony_text(path, json.dumps(dict(payload), indent=2, sort_keys=True) + "\n")


def _write_symphony_text(path: str | Path, content: str) -> Path:
    target = Path(path)
    _long_io_path(target.parent).mkdir(parents=True, exist_ok=True)
    temp_path = target.with_name(f".{target.name}.{os.getpid()}.{uuid.uuid4().hex}.tmp")
    _long_io_path(temp_path).write_text(content, encoding="utf-8")
    _long_io_path(temp_path).replace(_long_io_path(target))
    return target


def _long_io_path(path: Path) -> Path:
    if os.name != "nt":
        return path
    resolved = path.resolve(strict=False)
    text = str(resolved)
    if text.startswith("\\\\?\\"):
        return resolved
    return Path("\\\\?\\" + text)


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


def _codex_executor_options(args: argparse.Namespace) -> dict[str, Any]:
    if getattr(args, "executor", "") != "codex_cli":
        return {}
    return {
        "allow_real_codex_invocation": bool(getattr(args, "allow_real_codex_invocation", False)),
        "auto_ingest": bool(getattr(args, "auto_ingest", False)),
        "config_path": str(_codex_config_path(args.queue_root, getattr(args, "codex_config", None))),
        "timeout_seconds": getattr(args, "codex_timeout_seconds", None),
    }


def _codex_config_path(queue_root: str | Path, explicit_path: str | Path | None = None) -> Path:
    if explicit_path:
        return Path(explicit_path)
    return Path(queue_root) / "config" / "codex_executor_config.json"


def _command_can_preview(config: Any) -> bool:
    command = config.codex_command
    if isinstance(command, tuple):
        return bool(command)
    return bool(str(command or "").strip())


def _preview_packet_for_config(queue_root: str | Path) -> dict[str, Any]:
    root = Path(queue_root)
    return {
        "packet_id": "preview",
        "run_id": "<RUN_ID>",
        "plan_id": "<PLAN_ID>",
        "task_id": "<TASK_ID>",
        "created_at": _utc_iso(),
        "repo_root": ".",
        "branch": "master",
        "expected_head": "",
        "queue_manifest_path": str(root / "generated" / "<PLAN_ID>" / "<RUN_ID>" / "manifest.json"),
        "state_path": str(root / "generated" / "<PLAN_ID>" / "<RUN_ID>" / "state.json"),
        "task_spec_path": str(root / "generated" / "<PLAN_ID>" / "<RUN_ID>" / "tasks" / "<TASK_ID>.json"),
        "allowed_paths": [],
        "forbidden_actions": [],
        "acceptance_gates": [],
        "prompt_path": str(root / "generated" / "<PLAN_ID>" / "<RUN_ID>" / "codex_packets" / "<TASK_ID>" / "prompt.md"),
        "expected_result_path": str(root / "generated" / "<PLAN_ID>" / "<RUN_ID>" / "codex_packets" / "<TASK_ID>" / "expected_result_template.json"),
        "adapter_mode": "codex_cli_operator_approved",
        "requires_operator_approval": True,
        "safety_boundaries": ["operator_approval_required_for_codex_execution"],
    }


def _executable_status(command: list[str]) -> dict[str, Any]:
    if not command:
        return {"available": False, "executable": "", "resolved_path": None, "error": "codex_command is not configured"}
    executable = str(command[0])
    resolved = str(Path(executable).resolve(strict=False)) if Path(executable).exists() else shutil.which(executable)
    return {
        "available": resolved is not None,
        "executable": executable,
        "resolved_path": resolved,
        "error": "" if resolved else f"Codex CLI executable was not found or configured command is missing: {executable}",
    }


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


def _record_packet_artifacts_for_dashboard(packet: Any, queue_root: str | Path, artifact_paths: list[str]) -> None:
    try:
        state = load_state(packet.state_path)
        plan = load_plan_contract(_source_plan_for_packet(packet))
    except (OSError, json.JSONDecodeError, ValueError):
        return
    record_task_artifacts(state, packet.task_id, artifact_paths, result_path=artifact_paths[0] if artifact_paths else "")
    save_state(state, packet.state_path, updated_by="operator_cli")
    build_dashboard(state, plan, Path(packet.state_path).parent / "dashboard")
    save_state(state, packet.state_path, updated_by="operator_cli")


def _source_plan_for_packet(packet: Any) -> str:
    manifest = read_json(packet.queue_manifest_path)
    return str(manifest.get("source_plan_file") or "")


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
    for key in (
        "packet_id",
        "adapter_mode",
        "requires_operator_approval",
        "execution_packet_path",
        "execution_prompt_path",
        "expected_result_template_path",
        "result_json_path",
        "auto_ingest_status",
    ):
        if key in report:
            summary[key] = report[key]
    for key in (
        "runs",
        "run_count",
        "run_inspection",
        "state_validation",
        "checkpoint",
        "queue_creation",
        "plan_recovery",
        "codex_packets",
        "codex_result_ingestion",
        "codex_cli_config_validation",
        "codex_cli_executable",
        "codex_cli_command",
        "command_preview",
        "symphony_task_plan",
        "schema_index_passed",
        "symphony_mapping_passed",
        "app_server_adapter_boundary_ready",
        "real_app_server_started",
    ):
        if key in report:
            summary[key] = report[key]
    for key, value in report.items():
        if key.endswith("_report_paths"):
            summary[key] = value
    return summary


def _exit_code_for_report(report: Mapping[str, Any]) -> int:
    status = str(report.get("status", "failed"))
    run_status = str(report.get("run_status", ""))
    success_statuses = {"ok", "done", "max_steps", "requiring_operator_handoff", "adapter_dry_run_ready", "dry_run"}
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
