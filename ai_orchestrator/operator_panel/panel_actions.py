from __future__ import annotations

import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ai_orchestrator.symphony_adapter import (
    AppServerDryRunConfig,
    build_default_dry_run_config,
    describe_protocol_capabilities,
    render_dry_run_command,
    run_app_server_dry_run,
    validate_dry_run_config,
    write_app_server_dry_run_artifacts,
)
from ai_orchestrator.codex_queue.automation_dashboard import build_dashboard
from ai_orchestrator.codex_queue.codex_cli_executor import (
    build_codex_cli_command,
    load_codex_cli_executor_config,
    validate_codex_cli_executor_config,
)
from ai_orchestrator.codex_queue.codex_result_ingestion import ingest_codex_result, ingest_codex_result_text
from ai_orchestrator.codex_queue.long_run_controller import LongRunController
from ai_orchestrator.codex_queue.plan_contract import load_plan_contract, validate_plan_contract
from ai_orchestrator.codex_queue.plan_run_state import append_event, load_state, save_state
from ai_orchestrator.codex_queue.plan_to_queue import create_queue_from_plan
from ai_orchestrator.codex_queue.selective_staging_planner import collect_git_status

from .panel_state import discover_plans, discover_runs, load_panel_state, save_panel_state


def validate_plan_action(plan_file: str | Path) -> dict[str, Any]:
    plan = load_plan_contract(plan_file)
    validation = validate_plan_contract(plan)
    return {
        "status": "ok" if validation.valid else "blocked",
        "plan_id": plan.plan_id,
        "plan_file": str(plan_file),
        "validation": validation.to_dict(),
    }


def save_pasted_plan_action(plan_json_text: str, queue_root: str | Path, filename: str) -> dict[str, Any]:
    payload = json.loads(plan_json_text)
    if not isinstance(payload, dict):
        return {"status": "blocked", "errors": ["plan JSON must be an object"]}
    safe_name = _safe_filename(filename or f"{payload.get('plan_id', 'pasted_plan')}.json")
    path = Path(queue_root) / "plans" / safe_name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    state = load_panel_state(queue_root)
    state.selected_plan_file = str(path)
    state.last_action = {"action": "save_plan", "path": str(path)}
    save_panel_state(state, queue_root)
    return {"status": "ok", "path": str(path), "plan_id": payload.get("plan_id")}


def create_queue_action(plan_file: str | Path, queue_root: str | Path) -> dict[str, Any]:
    result = create_queue_from_plan(plan_file, queue_root)
    state = load_panel_state(queue_root)
    state.selected_plan_file = str(plan_file)
    state.active_run_id = result.run_id
    state.last_action = {"action": "create_queue", "status": result.status}
    save_panel_state(state, queue_root)
    return result.to_dict()


def run_fake_steps_action(plan_file: str | Path, queue_root: str | Path, max_steps: int) -> dict[str, Any]:
    plan = load_plan_contract(plan_file)
    result = LongRunController(repo_root=plan.repo_root or ".").run_plan(
        plan_file,
        queue_root,
        max_steps=max_steps,
        executor="fake",
        continue_until="blocked_or_done",
    )
    _remember_action(queue_root, "run_fake_steps", result)
    return result


def continue_run_action(run_id: str, queue_root: str | Path, max_steps: int, *, executor: str = "fake") -> dict[str, Any]:
    result = LongRunController().continue_plan(run_id, queue_root, max_steps=max_steps, executor=executor)
    _remember_action(queue_root, f"continue_run_{executor}", result, run_id=run_id)
    _record_run_event(queue_root, run_id, "panel_continue", result)
    return result


def test_codex_cli_config_action(queue_root: str | Path) -> dict[str, Any]:
    config_path = Path(queue_root) / "config" / "codex_executor_config.json"
    config = load_codex_cli_executor_config(config_path)
    validation = validate_codex_cli_executor_config(config)
    command = build_codex_cli_command(_preview_packet(queue_root), config)
    executable = _executable_status(command)
    status = "ok" if validation["valid"] and executable["available"] else "blocked"
    result = {
        "status": status,
        "config_path": str(config_path),
        "config": config.to_dict(),
        "validation": validation,
        "command_preview": command,
        "executable": executable,
        "codex_invoked": False,
    }
    _remember_action(queue_root, "test_codex_cli_config", result)
    return result


def continue_run_with_codex_cli_action(
    run_id: str,
    queue_root: str | Path,
    max_steps: int,
    *,
    approval_text: str = "",
    approval_checked: bool = False,
) -> dict[str, Any]:
    required = "I approve real Codex CLI invocation for this run"
    if approval_text.strip() != required or not approval_checked:
        result = {
            "status": "blocked",
            "run_id": run_id,
            "errors": [f"approval checkbox and exact confirmation text are required: {required}"],
            "codex_invoked": False,
        }
        _remember_action(queue_root, "continue_run_codex_cli_blocked_approval", result, run_id=run_id)
        _record_run_event(queue_root, run_id, "panel_codex_cli_approval_missing", result)
        return result
    config_path = Path(queue_root) / "config" / "codex_executor_config.json"
    result = LongRunController().continue_plan(
        run_id,
        queue_root,
        max_steps=max_steps,
        executor="codex_cli",
        continue_until="blocked_or_done",
        executor_options={
            "allow_real_codex_invocation": True,
            "auto_ingest": True,
            "config_path": str(config_path),
        },
    )
    _remember_action(queue_root, "continue_run_codex_cli", result, run_id=run_id)
    _record_run_event(queue_root, run_id, "panel_continue_codex_cli", result)
    return result


def recover_run_action(run_id: str, queue_root: str | Path, *, allow_stale_lock_clear: bool = False) -> dict[str, Any]:
    result = LongRunController().recover_plan(run_id, queue_root, allow_stale_lock_clear=allow_stale_lock_clear)
    _remember_action(queue_root, "recover_run", result, run_id=run_id)
    _record_run_event(queue_root, run_id, "panel_recover", result)
    return result


def export_next_codex_prompt_action(run_id: str, queue_root: str | Path) -> dict[str, Any]:
    result = LongRunController().continue_plan(run_id, queue_root, max_steps=1, executor="handoff", continue_until="one_step")
    _remember_action(queue_root, "export_next_codex_prompt", result, run_id=run_id)
    _record_run_event(queue_root, run_id, "panel_export_handoff", result)
    return result


def create_codex_packet_action(
    run_id: str,
    queue_root: str | Path,
    adapter_mode: str = "manual_handoff",
) -> dict[str, Any]:
    executor = "codex_cli_dry_run" if adapter_mode == "codex_cli_dry_run" else "codex_packet"
    result = LongRunController().continue_plan(run_id, queue_root, max_steps=1, executor=executor, continue_until="one_step")
    _remember_action(queue_root, f"create_codex_packet_{adapter_mode}", result, run_id=run_id)
    _record_run_event(queue_root, run_id, "panel_create_codex_packet", result)
    return result


def codex_adapter_dry_run_action(run_id: str, queue_root: str | Path) -> dict[str, Any]:
    result = LongRunController().continue_plan(run_id, queue_root, max_steps=1, executor="codex_cli_dry_run", continue_until="one_step")
    _remember_action(queue_root, "codex_adapter_dry_run", result, run_id=run_id)
    _record_run_event(queue_root, run_id, "panel_codex_adapter_dry_run", result)
    return result


def ingest_codex_result_action(
    packet_path: str | Path,
    result_json_text_or_path: str,
    queue_root: str | Path,
) -> dict[str, Any]:
    candidate = Path(result_json_text_or_path)
    try:
        candidate_exists = candidate.exists()
    except OSError:
        candidate_exists = False
    if candidate_exists:
        result = ingest_codex_result(packet_path, candidate, queue_root)
    else:
        result = ingest_codex_result_text(packet_path, result_json_text_or_path, queue_root)
    _remember_action(queue_root, "ingest_codex_result", result, run_id=str(result.get("run_id") or ""))
    _record_run_event(queue_root, str(result.get("run_id") or ""), "panel_ingest_codex_result", result)
    return result


def inspect_git_action(repo_root: str | Path) -> dict[str, Any]:
    status = collect_git_status(repo_root)
    branch = _git(["rev-parse", "--abbrev-ref", "HEAD"], repo_root)
    head = _git(["rev-parse", "HEAD"], repo_root)
    return {
        "status": "ok" if status["returncode"] == 0 else "failed",
        "branch": branch.get("stdout", ""),
        "head": head.get("stdout", ""),
        "git_status": status,
    }


def build_panel_dashboard_action(repo_root: str | Path, queue_root: str | Path) -> dict[str, Any]:
    runs = discover_runs(queue_root)
    plans = discover_plans(queue_root)
    active = next((run for run in reversed(runs) if run["status"] not in {"done", "missing_state"}), None)
    dashboard: dict[str, Any] | None = None
    if active:
        state = load_state(active["state_path"])
        manifest = _read_json(active["manifest_path"])
        plan_file = manifest.get("source_plan_file")
        if plan_file and Path(plan_file).exists():
            plan = load_plan_contract(plan_file)
            dashboard = build_dashboard(state, plan, Path(active["manifest_path"]).parent / "dashboard")
    return {
        "status": "ok",
        "repo_root": str(repo_root),
        "queue_root": str(queue_root),
        "plans": plans,
        "runs": runs,
        "active_run": active,
        "dashboard": dashboard,
        "git": inspect_git_action(repo_root),
        "codex_cli": codex_cli_panel_status(queue_root),
        "worktree_lane": worktree_lane_panel_status(queue_root),
        "nightly_lane_batch": nightly_lane_batch_panel_status(queue_root),
        "app_server": app_server_panel_status(repo_root, queue_root),
        "project_contract": project_contract_panel_status(repo_root),
    }


def project_contract_panel_status(repo_root: str | Path) -> dict[str, Any]:
    root = Path(repo_root)
    agents_md = root / "AGENTS.md"
    memory_bank = root / "memory-bank"
    active_context = memory_bank / "activeContext.md"
    maintenance_prompt = root / "agent_tasks" / "automations" / "codex_maintenance_prompt.md"
    subagent_profiles = root / "agent_tasks" / "agents"
    return {
        "agents_md_path": str(agents_md),
        "agents_md_exists": agents_md.exists(),
        "memory_bank_path": str(memory_bank),
        "memory_bank_exists": memory_bank.is_dir(),
        "latest_milestone": _latest_milestone(active_context),
        "maintenance_prompt_path": str(maintenance_prompt),
        "maintenance_prompt_exists": maintenance_prompt.exists(),
        "subagent_profiles_path": str(subagent_profiles),
        "subagent_profiles_exists": subagent_profiles.is_dir(),
    }


def codex_cli_panel_status(queue_root: str | Path) -> dict[str, Any]:
    config_path = Path(queue_root) / "config" / "codex_executor_config.json"
    config = load_codex_cli_executor_config(config_path)
    validation = validate_codex_cli_executor_config(config)
    command = build_codex_cli_command(_preview_packet(queue_root), config)
    executable = _executable_status(command)
    return {
        "config_path": str(config_path),
        "enabled": config.enabled,
        "validation": validation,
        "command_preview": command,
        "executable": executable,
        "ready": validation["valid"] and executable["available"],
    }


def worktree_lane_panel_status(queue_root: str | Path) -> dict[str, Any]:
    latest_path = Path(queue_root) / "reports" / "latest_worktree_lane_state.json"
    state = _read_json(latest_path)
    if not state:
        return {
            "ready": False,
            "status": "missing",
            "latest_lane_state_path": str(latest_path),
            "selected_subagent_profile": "",
            "blocker_reason": "no worktree lane state has been written",
        }
    return {
        "ready": bool(state.get("ready", False)),
        "status": str(state.get("status") or "unknown"),
        "latest_lane_state_path": str(latest_path),
        "task_id": str(state.get("task_id") or ""),
        "run_id": str(state.get("run_id") or ""),
        "branch": str(state.get("branch") or ""),
        "worktree_path": str(state.get("worktree_path") or ""),
        "selected_subagent_profile": str(state.get("selected_subagent_profile") or ""),
        "selected_subagent_profile_path": str(state.get("selected_subagent_profile_path") or ""),
        "blocker_reason": state.get("blocker_reason"),
        "state": state,
    }


def nightly_lane_batch_panel_status(queue_root: str | Path) -> dict[str, Any]:
    latest_json = Path(queue_root) / "reports" / "latest_nightly_lane_batch_report.json"
    latest_md = Path(queue_root) / "reports" / "latest_nightly_lane_batch_report.md"
    report = _read_json(latest_json)
    if not report:
        return {
            "status": "missing",
            "ready": False,
            "latest_report_json": str(latest_json),
            "latest_report_md": str(latest_md),
            "task_count": 0,
            "completed_count": 0,
            "blocked_count": 0,
            "failed_count": 0,
            "blocker_reason": "no nightly lane batch report has been written",
        }
    return {
        "status": str(report.get("status") or "unknown"),
        "ready": report.get("status") in {"completed", "dry_run"},
        "batch_id": str(report.get("batch_id") or ""),
        "run_id": str(report.get("run_id") or ""),
        "latest_report_json": str(latest_json),
        "latest_report_md": str(latest_md),
        "task_count": int(report.get("task_count") or 0),
        "completed_count": int(report.get("completed_count") or 0),
        "blocked_count": int(report.get("blocked_count") or 0),
        "failed_count": int(report.get("failed_count") or 0),
        "blocker_reason": report.get("blocker_reason"),
        "report_paths": dict(report.get("report_paths", {})) if isinstance(report.get("report_paths"), dict) else {},
    }


def app_server_panel_status(repo_root: str | Path, queue_root: str | Path) -> dict[str, Any]:
    schema_dir = Path("C:/Users/OpenC/.openclaw/external_research/codex_app_server_schema")
    config = build_default_dry_run_config(repo_root, schema_dir, repo_root)
    validation = validate_dry_run_config(config)
    latest_result = _latest_app_server_dry_run_result(queue_root)
    return {
        "schema_dir": str(schema_dir),
        "schema_dir_exists": schema_dir.exists(),
        "schema_client_request_exists": (schema_dir / "ClientRequest.json").exists(),
        "codex_cli_version": _codex_cli_version(),
        "command_preview": render_dry_run_command(config),
        "validation": validation,
        "safety_flags": {
            "allow_network": config.allow_network,
            "allow_auth": config.allow_auth,
            "allow_browser": config.allow_browser,
            "allow_real_task_execution": config.allow_real_task_execution,
            "dry_run_only": config.dry_run_only,
            "operator_approved": config.operator_approved,
        },
        "last_dry_run_result": latest_result,
        "artifact_paths": latest_result.get("artifact_paths", {}) if isinstance(latest_result, dict) else {},
        "ready_to_render": validation["valid"],
    }


def probe_app_server_schema_action(queue_root: str | Path, schema_dir: str | Path) -> dict[str, Any]:
    capabilities = describe_protocol_capabilities(schema_dir)
    result = {
        "status": "ok" if not capabilities.get("errors") else "blocked",
        "schema_dir": str(schema_dir),
        "protocol_capabilities": capabilities,
        "app_server_started": False,
        "network_used": False,
    }
    _remember_action(queue_root, "app_server_schema_probe", result)
    return result


def render_app_server_dry_run_command_action(
    repo_root: str | Path,
    queue_root: str | Path,
    schema_dir: str | Path,
    listen_mode: str = "stdio",
) -> dict[str, Any]:
    config = build_default_dry_run_config(repo_root, schema_dir, repo_root)
    config = AppServerDryRunConfig.from_dict({**config.to_dict(), "listen_mode": listen_mode, "operator_approved": False})
    validation = validate_dry_run_config(config)
    result = {
        "status": "ok" if validation["valid"] else "blocked",
        "command_preview": render_dry_run_command(config),
        "validation": validation,
        "config": config.to_dict(),
        "app_server_started": False,
    }
    _remember_action(queue_root, "app_server_render_dry_run_command", result)
    return result


def run_short_app_server_dry_run_action(
    repo_root: str | Path,
    queue_root: str | Path,
    schema_dir: str | Path,
    *,
    approval_text: str = "",
) -> dict[str, Any]:
    required = "I approve short-lived Codex app-server dry-run"
    if approval_text.strip() != required:
        result = {
            "status": "blocked",
            "errors": [f"exact confirmation text is required: {required}"],
            "process_started": False,
            "app_server_started": False,
        }
        _remember_action(queue_root, "app_server_dry_run_blocked_approval", result)
        return result
    config = build_default_dry_run_config(repo_root, schema_dir, repo_root)
    config = AppServerDryRunConfig.from_dict({**config.to_dict(), "operator_approved": True})
    result = run_app_server_dry_run(config)
    run_id = _panel_run_id()
    output_dir = Path(queue_root) / "generated" / "panel_app_server_dry_run" / run_id / "app_server_dry_runs" / run_id
    artifact_paths = write_app_server_dry_run_artifacts(result, output_dir)
    payload = {
        **result.to_dict(),
        "status": result.status,
        "artifact_dir": str(output_dir),
        "artifact_paths": artifact_paths,
        "app_server_started": result.process_started,
    }
    _remember_action(queue_root, "app_server_dry_run", payload)
    return payload


def create_app_server_session_plan_action(
    run_id: str,
    queue_root: str | Path,
    workspace_root: str | Path,
    schema_dir: str | Path,
) -> dict[str, Any]:
    from ai_orchestrator.codex_queue.operator_cli import main

    exit_code = main(
        [
            "create-app-server-session-plan",
            "--run-id",
            run_id,
            "--queue-root",
            str(queue_root),
            "--workspace-root",
            str(workspace_root),
            "--schema-dir",
            str(schema_dir),
        ]
    )
    latest = _read_json(Path(queue_root) / "reports" / "latest_operator_action.json")
    result = {"status": "ok" if exit_code == 0 else "blocked", "operator_action": latest, "app_server_started": False}
    _remember_action(queue_root, "create_app_server_session_plan", result, run_id=run_id)
    return result


def _latest_app_server_dry_run_result(queue_root: str | Path) -> dict[str, Any]:
    candidates = sorted(Path(queue_root).glob("generated/*/*/app_server_dry_runs/*/result.json"))
    if not candidates:
        return {}
    latest = candidates[-1]
    payload = _read_json(latest)
    payload["result_path"] = str(latest)
    payload["artifact_dir"] = str(latest.parent)
    payload["artifact_paths"] = {
        "dry_run_config": str(latest.parent / "dry_run_config.json"),
        "app_server_command": str(latest.parent / "app_server_command.txt"),
        "protocol_probe": str(latest.parent / "protocol_probe.json"),
        "stdout": str(latest.parent / "stdout.log"),
        "stderr": str(latest.parent / "stderr.log"),
        "result": str(latest),
        "readme": str(latest.parent / "README.md"),
    }
    return payload


def _codex_cli_version() -> str:
    executable = shutil.which("codex")
    if not executable:
        return "unavailable"
    try:
        completed = subprocess.run(
            [executable, "--version"],
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.TimeoutExpired):
        return "unavailable"
    output = (completed.stdout or completed.stderr).strip()
    return output or "unknown"


def _latest_milestone(active_context: Path) -> str:
    try:
        text = active_context.read_text(encoding="utf-8")
    except OSError:
        return "unknown"
    for line in text.splitlines():
        if "latest_completed_milestone" in line or "next_milestone" in line:
            value = line.split(":", 1)[-1].strip(" `")
            if value:
                return value
    return "unknown"


def _panel_run_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _remember_action(queue_root: str | Path, action: str, result: dict[str, Any], *, run_id: str = "") -> None:
    state = load_panel_state(queue_root)
    payload = result.get("payload", {}) if isinstance(result.get("payload", {}), dict) else {}
    state.active_run_id = run_id or str(payload.get("run_id") or state.active_run_id)
    state.last_action = {"action": action, "status": result.get("status"), "run_id": state.active_run_id}
    state.action_events.append(dict(state.last_action))
    state.action_events = state.action_events[-50:]
    save_panel_state(state, queue_root)


def _record_run_event(queue_root: str | Path, run_id: str, event: str, result: dict[str, Any]) -> None:
    if not run_id:
        return
    matches = sorted(Path(queue_root).glob(f"generated/*/{run_id}/state.json"))
    if not matches:
        return
    try:
        state = load_state(matches[0])
    except (OSError, json.JSONDecodeError, ValueError):
        return
    append_event(
        state,
        {
            "event": event,
            "status": result.get("status"),
            "stop_reason": result.get("stop_reason"),
        },
    )
    save_state(state, matches[0], updated_by="operator_panel")


def _safe_filename(value: str) -> str:
    name = "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in value)
    if not name.endswith(".json"):
        name += ".json"
    return name or "plan.json"


def _git(args: list[str], repo_root: str | Path) -> dict[str, Any]:
    completed = subprocess.run(["git", *args], cwd=str(repo_root), check=False, capture_output=True, text=True)
    return {"returncode": completed.returncode, "stdout": completed.stdout.strip(), "stderr": completed.stderr.strip()}


def _preview_packet(queue_root: str | Path) -> dict[str, Any]:
    root = Path(queue_root)
    return {
        "packet_id": "preview",
        "run_id": "<RUN_ID>",
        "plan_id": "<PLAN_ID>",
        "task_id": "<TASK_ID>",
        "created_at": "",
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


def _read_json(path: str | Path) -> dict[str, Any]:
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}
