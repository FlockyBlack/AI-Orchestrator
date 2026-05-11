from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from ai_orchestrator.codex_queue.automation_dashboard import build_dashboard
from ai_orchestrator.codex_queue.long_run_controller import LongRunController
from ai_orchestrator.codex_queue.plan_contract import load_plan_contract, validate_plan_contract
from ai_orchestrator.codex_queue.plan_run_state import load_state
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


def continue_run_action(run_id: str, queue_root: str | Path, max_steps: int) -> dict[str, Any]:
    result = LongRunController().continue_plan(run_id, queue_root, max_steps=max_steps, executor="fake")
    _remember_action(queue_root, "continue_run", result, run_id=run_id)
    return result


def recover_run_action(run_id: str, queue_root: str | Path) -> dict[str, Any]:
    result = LongRunController().recover_plan(run_id, queue_root)
    _remember_action(queue_root, "recover_run", result, run_id=run_id)
    return result


def export_next_codex_prompt_action(run_id: str, queue_root: str | Path) -> dict[str, Any]:
    result = LongRunController().continue_plan(run_id, queue_root, max_steps=1, executor="handoff", continue_until="one_step")
    _remember_action(queue_root, "export_next_codex_prompt", result, run_id=run_id)
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
    }


def _remember_action(queue_root: str | Path, action: str, result: dict[str, Any], *, run_id: str = "") -> None:
    state = load_panel_state(queue_root)
    payload = result.get("payload", {}) if isinstance(result.get("payload", {}), dict) else {}
    state.active_run_id = run_id or str(payload.get("run_id") or state.active_run_id)
    state.last_action = {"action": action, "status": result.get("status"), "run_id": state.active_run_id}
    save_panel_state(state, queue_root)


def _safe_filename(value: str) -> str:
    name = "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in value)
    if not name.endswith(".json"):
        name += ".json"
    return name or "plan.json"


def _git(args: list[str], repo_root: str | Path) -> dict[str, Any]:
    completed = subprocess.run(["git", *args], cwd=str(repo_root), check=False, capture_output=True, text=True)
    return {"returncode": completed.returncode, "stdout": completed.stdout.strip(), "stderr": completed.stderr.strip()}


def _read_json(path: str | Path) -> dict[str, Any]:
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}
