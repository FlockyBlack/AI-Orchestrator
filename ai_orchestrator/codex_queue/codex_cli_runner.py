from __future__ import annotations

import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

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

EXECUTION_REPORT_SCHEMA_VERSION = "codex_cli_execution_report.v1"
DEFAULT_TIMEOUT_SECONDS = 3600


def run_codex_once(
    queue_root: str | Path = "agent_tasks",
    *,
    task_id: str,
    dry_run: bool = False,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    root = ensure_queue_directories(queue_root)
    safe_task_id = validate_task_id(task_id)
    run_id = _run_id()
    started_at = _utc_iso()
    execution_dir = safe_queue_path(root, "reports", "codex_cli_runs", safe_task_id, run_id)
    paths = _execution_paths(root, safe_task_id, run_id, execution_dir)

    report = _base_report(
        root=root,
        task_id=safe_task_id,
        run_id=run_id,
        started_at=started_at,
        dry_run=dry_run,
        timeout_seconds=timeout_seconds,
        paths=paths,
    )

    packet_context = _load_ready_task_context(root, safe_task_id)
    context_paths = dict(packet_context.pop("paths"))
    report["paths"].update(context_paths)
    report.update(packet_context)
    report["errors"].extend(packet_context["errors"])
    report["warnings"].extend(packet_context["warnings"])

    repo_root = _repo_root_from_packet(packet_context.get("task_packet"))
    git_state = inspect_git_state(str(repo_root))
    report["repo_root"] = git_state.get("repo_root") or str(Path(repo_root).resolve(strict=False))
    report["git_state"] = git_state
    report["warnings"].extend(git_state.get("warnings", []))
    report["errors"].extend(git_state.get("errors", []))
    _verify_expected_head(report, packet_context.get("task_packet"), git_state)

    if timeout_seconds <= 0:
        report["errors"].append("timeout_seconds must be greater than zero")

    codex_path = shutil.which("codex")
    report["codex_cli"] = {
        "executable": "codex",
        "resolved_path": codex_path,
        "available": codex_path is not None,
    }

    handoff_prompt_path = str(report["paths"].get("handoff_prompt") or "")
    command = _build_command(report["repo_root"], paths["last_message"])
    report["command"] = {
        "argv": command,
        "display": _format_command(command),
        "stdin_from": handoff_prompt_path,
    }

    if dry_run and codex_path is None:
        report["warnings"].append("Codex CLI was not found on PATH; a real run would be blocked.")
    elif not dry_run and codex_path is None:
        report["errors"].append("Codex CLI executable was not found on PATH")

    if report["errors"]:
        report["status"] = "blocked"
        report["execution_status"] = "blocked"
        report["ended_at"] = _utc_iso()
        report["next_operator_action"] = "Resolve blocking errors, then rerun dry-run before supervised execution."
        return _write_execution_report(root, report, paths)

    if dry_run:
        report["status"] = "ok"
        report["execution_status"] = "dry_run"
        report["would_invoke_codex"] = True
        report["ended_at"] = _utc_iso()
        report["next_operator_action"] = "Review the command and paths, then rerun without --dry-run for one supervised execution."
        return _write_execution_report(root, report, paths)

    prompt = Path(handoff_prompt_path).read_text(encoding="utf-8")
    execution_dir.mkdir(parents=True, exist_ok=True)
    report["codex_exec_invoked"] = True
    report["codex_invocation_count"] = 1
    report["execution_started_at"] = _utc_iso()
    try:
        completed = subprocess.run(
            command,
            cwd=str(report["repo_root"]),
            input=prompt,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        stdout = _coerce_output(exc.stdout)
        stderr = _coerce_output(exc.stderr)
        if stderr:
            stderr += "\n"
        stderr += f"Timed out after {timeout_seconds} seconds."
        write_text_atomic(paths["stdout_log"], stdout)
        write_text_atomic(paths["stderr_log"], stderr)
        report["status"] = "failed"
        report["execution_status"] = "timed_out"
        report["exit_code"] = None
        report["execution_ended_at"] = _utc_iso()
        report["ended_at"] = report["execution_ended_at"]
        report["errors"].append(f"Codex CLI timed out after {timeout_seconds} seconds")
        report["next_operator_action"] = "Inspect stdout/stderr logs and decide whether to block or rerun under supervision."
        return _write_execution_report(root, report, paths)
    except OSError as exc:
        write_text_atomic(paths["stdout_log"], "")
        write_text_atomic(paths["stderr_log"], str(exc))
        report["status"] = "blocked"
        report["execution_status"] = "blocked"
        report["exit_code"] = None
        report["execution_ended_at"] = _utc_iso()
        report["ended_at"] = report["execution_ended_at"]
        report["errors"].append(f"failed to invoke Codex CLI: {exc}")
        report["next_operator_action"] = "Install or repair Codex CLI, then rerun dry-run before supervised execution."
        return _write_execution_report(root, report, paths)

    write_text_atomic(paths["stdout_log"], completed.stdout)
    write_text_atomic(paths["stderr_log"], completed.stderr)
    report["exit_code"] = completed.returncode
    report["execution_ended_at"] = _utc_iso()
    report["ended_at"] = report["execution_ended_at"]
    if completed.returncode == 0:
        report["status"] = "ok"
        report["execution_status"] = "completed"
        report["next_operator_action"] = (
            "Inspect Codex logs and result JSON, then run ingest-result and review explicitly."
        )
    elif _looks_codex_exec_unavailable(completed.stderr):
        report["status"] = "blocked"
        report["execution_status"] = "blocked"
        report["errors"].append("Codex CLI is available, but the `codex exec` command appears unavailable")
        report["next_operator_action"] = "Install or repair Codex CLI, then rerun dry-run before supervised execution."
    else:
        report["status"] = "failed"
        report["execution_status"] = "failed"
        report["errors"].append(f"Codex CLI exited with code {completed.returncode}")
        report["next_operator_action"] = "Inspect stdout/stderr logs and decide whether to block or retry manually."
    return _write_execution_report(root, report, paths)


def render_execution_report_markdown(report: Mapping[str, Any]) -> str:
    command = report.get("command", {})
    paths = report.get("paths", {})
    lines = [
        f"# Codex CLI Execution: {report['task_id']}",
        "",
        f"- status: `{report['status']}`",
        f"- execution_status: `{report['execution_status']}`",
        f"- dry_run: `{report['dry_run']}`",
        f"- run_id: `{report['run_id']}`",
        f"- started_at: `{report['started_at']}`",
        f"- ended_at: `{report.get('ended_at')}`",
        f"- exit_code: `{report.get('exit_code')}`",
        f"- timeout_seconds: `{report['timeout_seconds']}`",
        f"- task_packet: `{paths.get('task_packet')}`",
        f"- plan: `{paths.get('plan')}`",
        f"- handoff_prompt: `{paths.get('handoff_prompt')}`",
        f"- stdout_log: `{paths.get('stdout_log')}`",
        f"- stderr_log: `{paths.get('stderr_log')}`",
        f"- last_message: `{paths.get('last_message')}`",
        "",
        "## Command",
        "",
        f"`{command.get('display', '')}`",
        "",
        f"- stdin_from: `{command.get('stdin_from', '')}`",
        f"- codex_exec_invoked: `{report['codex_exec_invoked']}`",
        f"- codex_invocation_count: `{report['codex_invocation_count']}`",
        "",
    ]
    expected = report.get("expected_head_verification", {})
    lines.extend(
        [
            "## Git",
            "",
            f"- repo_root: `{report.get('repo_root', '')}`",
            f"- branch: `{report.get('git_state', {}).get('branch', '')}`",
            f"- head: `{report.get('git_state', {}).get('head', '')}`",
            f"- expected_head: `{expected.get('expected')}`",
            f"- expected_head_matched: `{expected.get('matched')}`",
            "",
        ]
    )
    if report.get("errors"):
        lines.extend(["## Errors", ""])
        lines.extend(f"- {error}" for error in report["errors"])
        lines.append("")
    if report.get("warnings"):
        lines.extend(["## Warnings", ""])
        lines.extend(f"- {warning}" for warning in report["warnings"])
        lines.append("")
    lines.extend(
        [
            "## Safety",
            "",
            "This supervised runner handles exactly one explicit task_id per invocation. It does not create schedulers, daemons, background workers, multi-task loops, branches, worktrees, review approvals, mark-done actions, pushes, or network service integrations.",
            "",
            f"Next operator action: {report['next_operator_action']}",
            "",
        ]
    )
    return "\n".join(lines)


def _load_ready_task_context(root: Path, task_id: str) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    paths: dict[str, str | None] = {
        "task_packet": None,
        "plan": None,
        "handoff_prompt": None,
    }

    match = find_task_packet(root, task_id, states=("approved", "planned"))
    task_packet = dict(match["packet"]) if match["found"] else None
    validation = validate_packet(task_packet) if task_packet else None
    classification = _classify_for_runner(task_packet, validation) if task_packet and validation else None

    if not match["found"]:
        errors.append(f"no approved/planned task packet found for task_id: {task_id}")
        errors.extend(match["errors"])
    else:
        paths["task_packet"] = str(match["path"])
        if match["state"] not in {"approved", "planned"}:
            errors.append(f"task packet must be in approved or planned, got: {match['state']}")
        if task_packet and task_packet.get("status") not in {"approved", "planned"}:
            errors.append(f"task status must be approved or planned, got: {task_packet.get('status')}")
        if validation and not validation.valid:
            errors.extend(validation.errors)
        if classification and not classification.allowed:
            errors.extend(classification.reasons)
            warnings.append(f"safety classification: {classification.status}")

    plan_path = safe_queue_path(root, "planned", f"{task_id}.plan.json")
    plan_payload: dict[str, Any] | None = None
    if not plan_path.exists():
        errors.append(f"matching plan is required: {plan_path}")
    else:
        paths["plan"] = str(plan_path)
        try:
            loaded = read_json(plan_path)
            if not isinstance(loaded, Mapping):
                errors.append(f"plan must be a JSON object: {plan_path}")
            else:
                plan_payload = dict(loaded)
                if plan_payload.get("task_id") != task_id:
                    errors.append(f"plan task_id does not match {task_id}: {plan_payload.get('task_id')}")
        except json.JSONDecodeError as exc:
            errors.append(f"invalid plan JSON: {exc}")

    handoff_path: Path | None = None
    if plan_payload:
        raw_handoff_path = plan_payload.get("handoff_prompt_path")
        if isinstance(raw_handoff_path, str) and raw_handoff_path.strip():
            try:
                handoff_path = safe_existing_path_under_queue(root, raw_handoff_path)
            except ValueError as exc:
                errors.append(str(exc))
        else:
            handoff_path = safe_queue_path(root, "planned", f"{task_id}.handoff_prompt.md")
    else:
        handoff_path = safe_queue_path(root, "planned", f"{task_id}.handoff_prompt.md")

    if handoff_path is not None:
        paths["handoff_prompt"] = str(handoff_path)
        if not handoff_path.exists():
            errors.append(f"matching handoff prompt is required: {handoff_path}")

    return {
        "task_packet": task_packet,
        "task_packet_state": match.get("state"),
        "task_validation": validation.to_dict() if validation else None,
        "safety_classification": classification.to_dict() if classification else None,
        "plan": plan_payload,
        "paths": paths,
        "errors": errors,
        "warnings": warnings,
    }


def _base_report(
    *,
    root: Path,
    task_id: str,
    run_id: str,
    started_at: str,
    dry_run: bool,
    timeout_seconds: int,
    paths: Mapping[str, str],
) -> dict[str, Any]:
    return {
        "schema_version": EXECUTION_REPORT_SCHEMA_VERSION,
        "run_id": run_id,
        "task_id": task_id,
        "queue_root": str(root),
        "repo_root": "",
        "status": "blocked",
        "execution_status": "blocked",
        "dry_run": dry_run,
        "started_at": started_at,
        "ended_at": None,
        "execution_started_at": None,
        "execution_ended_at": None,
        "timeout_seconds": timeout_seconds,
        "exit_code": None,
        "codex_cli": {},
        "command": {},
        "git_state": {},
        "expected_head_verification": {
            "present": False,
            "expected": None,
            "actual": None,
            "matched": None,
        },
        "task_packet": None,
        "task_packet_state": None,
        "task_validation": None,
        "safety_classification": None,
        "plan": None,
        "paths": dict(paths),
        "errors": [],
        "warnings": [],
        "codex_exec_invoked": False,
        "codex_invocation_count": 0,
        "would_invoke_codex": False,
        "stdout_captured": False,
        "stderr_captured": False,
        "execution_report_written": False,
        "result_ingested_automatically": False,
        "task_marked_done_automatically": False,
        "review_approved_automatically": False,
        "git_push_performed": False,
        "branch_created": False,
        "worktree_created": False,
        "scheduler_created": False,
        "daemon_created": False,
        "background_worker_created": False,
        "multi_task_loop_created": False,
        "openrouter_calls_performed": 0,
        "polymarket_api_calls_performed": 0,
        "wallet_or_private_key_access": False,
        "orders_or_trading_actions": False,
        "runtime_or_dispatcher_changes": False,
        "next_operator_action": "",
        "report_paths": {},
    }


def _execution_paths(root: Path, task_id: str, run_id: str, execution_dir: Path) -> dict[str, str]:
    return {
        "execution_dir": str(execution_dir),
        "stdout_log": str(execution_dir / "stdout.log"),
        "stderr_log": str(execution_dir / "stderr.log"),
        "last_message": str(execution_dir / "last_message.md"),
        "execution_report_json": str(execution_dir / "execution_report.json"),
        "execution_report_md": str(execution_dir / "execution_report.md"),
        "latest_execution_report_json": str(safe_queue_path(root, "reports", "latest_codex_cli_execution_report.json")),
        "latest_execution_report_md": str(safe_queue_path(root, "reports", "latest_codex_cli_execution_report.md")),
        "expected_result_json": str(safe_queue_path(root, "review", f"{task_id}.result.json")),
    }


def _write_execution_report(root: Path, report: dict[str, Any], paths: Mapping[str, str]) -> dict[str, Any]:
    report = dict(report)
    report["stdout_captured"] = Path(paths["stdout_log"]).exists()
    report["stderr_captured"] = Path(paths["stderr_log"]).exists()
    report["execution_report_written"] = True
    report_paths = {
        "execution_report_json": paths["execution_report_json"],
        "execution_report_md": paths["execution_report_md"],
        "latest_execution_report_json": paths["latest_execution_report_json"],
        "latest_execution_report_md": paths["latest_execution_report_md"],
        "stdout_log": paths["stdout_log"],
        "stderr_log": paths["stderr_log"],
        "last_message": paths["last_message"],
        "expected_result_json": paths["expected_result_json"],
    }
    report["report_paths"] = report_paths
    write_json_atomic(paths["execution_report_json"], report)
    write_text_atomic(paths["execution_report_md"], render_execution_report_markdown(report))
    write_json_atomic(paths["latest_execution_report_json"], report)
    write_text_atomic(paths["latest_execution_report_md"], render_execution_report_markdown(report))
    return report


def _classify_for_runner(packet: Mapping[str, Any], validation: Any) -> Any:
    if packet.get("status") != "planned":
        return classify_packet(packet, validation)
    approved_view = dict(packet)
    approved_view["status"] = "approved"
    return classify_packet(approved_view, validation)


def _verify_expected_head(
    report: dict[str, Any],
    packet: Mapping[str, Any] | None,
    git_state: Mapping[str, Any],
) -> None:
    repo = packet.get("repo", {}) if isinstance(packet, Mapping) else {}
    expected = repo.get("expected_head") if isinstance(repo, Mapping) else None
    if isinstance(expected, str):
        expected = expected.strip() or None
    actual = str(git_state.get("head") or "")
    report["expected_head_verification"] = {
        "present": expected is not None,
        "expected": expected,
        "actual": actual or None,
        "matched": (actual == expected) if expected else None,
    }
    if expected and actual != expected:
        report["errors"].append(f"expected_head mismatch: expected {expected}, got {actual or '<missing>'}")


def _repo_root_from_packet(packet: Any) -> Path:
    if isinstance(packet, Mapping):
        repo = packet.get("repo", {})
        if isinstance(repo, Mapping):
            repo_root = repo.get("repo_root")
            if isinstance(repo_root, str) and repo_root.strip():
                return Path(repo_root).resolve(strict=False)
    return Path(".").resolve(strict=False)


def _build_command(repo_root: str, last_message_path: str) -> list[str]:
    return [
        "codex",
        "exec",
        "--cd",
        str(repo_root),
        "--color",
        "never",
        "--output-last-message",
        last_message_path,
        "-",
    ]


def _format_command(argv: list[str]) -> str:
    return subprocess.list2cmdline([str(part) for part in argv])


def _coerce_output(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value


def _looks_codex_exec_unavailable(stderr: str) -> bool:
    text = stderr.lower()
    markers = (
        "unrecognized subcommand",
        "unknown command",
        "invalid subcommand",
        "no such subcommand",
        "command not found",
    )
    return any(marker in text for marker in markers)


def _run_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _utc_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
