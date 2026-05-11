from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .execution_lock import ExecutionLock, inspect_lock
from .plan_run_state import PlanRunState, load_state, mark_task_blocked, save_state


def inspect_run(run_id: str, queue_root: str | Path) -> dict[str, Any]:
    root = Path(queue_root)
    matches = sorted(root.glob(f"generated/*/{run_id}/manifest.json"))
    if not matches:
        return {
            "status": "missing",
            "run_id": run_id,
            "queue_root": str(root),
            "manifest_path": "",
            "state_path": "",
            "plan_id": "",
            "errors": [f"run_id not found: {run_id}"],
        }
    manifest_path = matches[0]
    state_path = manifest_path.parent / "state.json"
    manifest = _read_json(manifest_path)
    return {
        "status": "found",
        "run_id": run_id,
        "queue_root": str(root),
        "manifest_path": str(manifest_path),
        "state_path": str(state_path),
        "run_root": str(manifest_path.parent),
        "plan_id": str(manifest.get("plan_id") or manifest_path.parent.parent.name),
        "manifest": manifest,
        "state_exists": state_path.exists(),
        "errors": [],
    }


def recover_run(
    run_id: str,
    queue_root: str | Path,
    allow_stale_lock_clear: bool = False,
) -> dict[str, Any]:
    inspection = inspect_run(run_id, queue_root)
    if inspection["status"] != "found":
        return produce_recovery_report(inspection, queue_root)

    plan_id = inspection["plan_id"]
    state_path = Path(inspection["state_path"])
    state: PlanRunState | None = None
    errors: list[str] = []
    if state_path.exists():
        state = load_state(state_path)
    else:
        errors.append("state.json is missing")

    lock = ExecutionLock(queue_root=queue_root, plan_id=plan_id, run_id=run_id, repo_root=".")
    lock_state = inspect_lock(lock)
    if lock_state["exists"] and lock_state["stale"]:
        if allow_stale_lock_clear:
            Path(lock_state["lock_path"]).unlink(missing_ok=True)
        else:
            errors.append("stale lock detected; rerun recovery with allow_stale_lock_clear=True to clear it")
    elif lock_state["exists"]:
        errors.append("active lock exists; do not recover while a run may be active")

    incomplete = identify_incomplete_tasks(inspection, state)
    checkpoint = identify_last_safe_checkpoint(state)
    status = "recovered" if not errors else "blocked"
    report = {
        **inspection,
        "status": status,
        "errors": errors,
        "lock": lock_state,
        "incomplete_task_ids": incomplete,
        "last_safe_checkpoint": checkpoint,
        "allow_stale_lock_clear": allow_stale_lock_clear,
    }
    if state and errors:
        mark_task_blocked(state, state.current_task_id or "RUN", "; ".join(errors))
        save_state(state, state_path)
    return produce_recovery_report(report, queue_root)


def identify_incomplete_tasks(inspection: dict[str, Any], state: PlanRunState | None) -> list[str]:
    task_ids = list(inspection.get("manifest", {}).get("task_ids", []))
    if not state:
        return task_ids
    terminal = set(state.completed_task_ids) | set(state.blocked_task_ids) | set(state.failed_task_ids) | set(state.skipped_task_ids)
    return [task_id for task_id in task_ids if task_id not in terminal]


def identify_last_safe_checkpoint(state: PlanRunState | None) -> dict[str, Any]:
    if not state:
        return {"completed_task_id": "", "completed_count": 0}
    return {
        "completed_task_id": state.completed_task_ids[-1] if state.completed_task_ids else "",
        "completed_count": len(state.completed_task_ids),
        "git_head_last_verified": state.git_head_last_verified,
    }


def produce_recovery_report(report: dict[str, Any], queue_root: str | Path) -> dict[str, Any]:
    root = Path(queue_root)
    run_id = str(report.get("run_id") or "unknown")
    output_dir = root / "generated" / "_recovery"
    json_path = output_dir / f"{run_id}_recovery_report.json"
    md_path = output_dir / f"{run_id}_recovery_report.md"
    output_dir.mkdir(parents=True, exist_ok=True)
    report = dict(report)
    report["recovery_report_paths"] = {"json": str(json_path), "markdown": str(md_path)}
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_path.write_text(_render_recovery_markdown(report), encoding="utf-8")
    return report


def _read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _render_recovery_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# Recovery Report: {report.get('run_id')}",
        "",
        f"- status: `{report.get('status')}`",
        f"- plan_id: `{report.get('plan_id')}`",
        f"- manifest_path: `{report.get('manifest_path')}`",
        f"- state_path: `{report.get('state_path')}`",
        "",
        "## Incomplete Tasks",
        "",
    ]
    incomplete = report.get("incomplete_task_ids") or []
    lines.extend(f"- `{task_id}`" for task_id in incomplete) if incomplete else lines.append("- None")
    if report.get("errors"):
        lines.extend(["", "## Errors", ""])
        lines.extend(f"- {error}" for error in report["errors"])
    lines.extend(["", "Recovery is local-only and never pretends success when state is inconsistent.", ""])
    return "\n".join(lines)
