from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .execution_lock import ExecutionLock, inspect_lock
from .plan_contract import load_plan_contract
from .plan_run_state import (
    PlanRunState,
    create_checkpoint,
    load_state,
    save_state,
    set_run_status,
    validate_state_consistency,
)
from .plan_to_queue import inspect_queue, validate_queue_manifest


def inspect_run(run_id: str, queue_root: str | Path) -> dict[str, Any]:
    inspection = inspect_queue(queue_root, run_id)
    if inspection["status"] not in {"found", "invalid"}:
        return {
            "status": "missing",
            "run_id": run_id,
            "queue_root": str(Path(queue_root)),
            "manifest_path": "",
            "state_path": "",
            "plan_id": "",
            "errors": inspection.get("errors", [f"run_id not found: {run_id}"]),
        }
    manifest = inspection.get("manifest", {})
    return {
        "status": "found" if inspection["status"] == "found" else "invalid_manifest",
        "run_id": run_id,
        "queue_root": str(Path(queue_root)),
        "manifest_path": inspection["manifest_path"],
        "state_path": inspection["state_path"],
        "run_root": inspection["run_dir"],
        "plan_id": str(manifest.get("plan_id") or inspection.get("plan_id") or ""),
        "manifest": manifest,
        "state_exists": Path(inspection["state_path"]).exists(),
        "manifest_validation": inspection.get("validation", {}),
        "errors": list(inspection.get("errors", [])),
        "warnings": list(inspection.get("warnings", [])),
    }


def recover_run(
    run_id: str,
    queue_root: str | Path,
    allow_stale_lock_clear: bool = False,
) -> dict[str, Any]:
    inspected_at = _utc_iso()
    inspection = inspect_run(run_id, queue_root)
    if inspection["status"] not in {"found", "invalid_manifest"}:
        return produce_recovery_report(
            {
                **inspection,
                "inspected_at": inspected_at,
                "lock_path": "",
                "lock_status": "unknown",
                "state_status": "missing",
                "consistency_errors": inspection.get("errors", []),
                "incomplete_tasks": [],
                "last_safe_checkpoint": None,
                "recommended_operator_action": "Create or select a valid run_id before recovery.",
                "recovery_performed": False,
                "stale_lock_cleared": False,
                "safety_ok": True,
            },
            queue_root,
        )

    manifest = dict(inspection.get("manifest", {}))
    plan_id = inspection["plan_id"]
    state_path = Path(inspection["state_path"])
    manifest_path = Path(inspection["manifest_path"])
    lock_path = Path(str(manifest.get("lock_path") or manifest_path.parent / "run.lock"))
    state: PlanRunState | None = None
    errors: list[str] = []
    warnings: list[str] = list(inspection.get("warnings", []))
    recovery_performed = False
    stale_lock_cleared = False

    manifest_validation = validate_queue_manifest(manifest)
    errors.extend(manifest_validation["errors"])
    warnings.extend(manifest_validation["warnings"])

    if state_path.exists():
        state = load_state(state_path)
        set_run_status(state, "recovering", reason="recover_plan")
        create_checkpoint(state, "recovery_inspection")
    else:
        errors.append("state.json is missing")

    plan = None
    plan_file = str(manifest.get("source_plan_file") or "")
    if plan_file and Path(plan_file).exists():
        plan = load_plan_contract(plan_file)
    elif plan_file:
        errors.append(f"source plan file missing: {plan_file}")
    else:
        errors.append("manifest missing source_plan_file")

    consistency = {"consistent": False, "errors": ["state or plan missing"], "pending_task_ids": []}
    if state and plan:
        consistency = validate_state_consistency(state, plan)
        errors.extend(consistency["errors"])

    lock = ExecutionLock(
        queue_root=queue_root,
        plan_id=plan_id,
        run_id=run_id,
        repo_root=".",
        lock_path=lock_path,
    )
    lock_state = inspect_lock(lock)
    if lock_state["exists"] and lock_state["stale"]:
        if allow_stale_lock_clear:
            Path(lock_state["lock_path"]).unlink(missing_ok=True)
            stale_lock_cleared = True
            recovery_performed = True
            lock_state = inspect_lock(lock)
        else:
            errors.append("stale lock detected; rerun recovery with --allow-stale-lock-clear to clear it")
    elif lock_state["exists"]:
        errors.append("active lock exists; do not recover while a run may be active")

    incomplete = identify_incomplete_tasks(inspection, state)
    checkpoint = identify_last_safe_checkpoint(state)
    report_status = "recovered" if not errors else "blocked"
    recommended = _recommended_action(report_status, bool(lock_state["exists"]), bool(consistency.get("consistent")))

    report = {
        **inspection,
        "status": report_status,
        "run_id": run_id,
        "plan_id": plan_id,
        "inspected_at": inspected_at,
        "state_path": str(state_path),
        "manifest_path": str(manifest_path),
        "lock_path": str(lock_path),
        "lock_status": _lock_status(lock_state),
        "lock": lock_state,
        "state_status": state.status if state else "missing",
        "manifest_status": manifest_validation["status"],
        "consistency_errors": list(dict.fromkeys(errors)),
        "errors": list(dict.fromkeys(errors)),
        "warnings": list(dict.fromkeys(warnings)),
        "incomplete_tasks": incomplete,
        "incomplete_task_ids": incomplete,
        "last_safe_checkpoint": checkpoint,
        "recommended_operator_action": recommended,
        "recovery_performed": recovery_performed,
        "stale_lock_cleared": stale_lock_cleared,
        "allow_stale_lock_clear": allow_stale_lock_clear,
        "safety_ok": True,
    }
    report = produce_recovery_report(report, queue_root)

    if state:
        state.latest_recovery_report_path = report.get("recovery_report_paths", {}).get("json", "")
        if report_status == "recovered":
            set_run_status(state, "recovered", reason="recover_plan_ok")
        else:
            set_run_status(state, "blocked", reason="recover_plan_blocked")
        create_checkpoint(state, "recovery_result")
        save_state(state, state_path, updated_by="plan_recovery")
    return report


def identify_incomplete_tasks(inspection: dict[str, Any], state: PlanRunState | None) -> list[str]:
    task_ids = list(inspection.get("manifest", {}).get("task_ids", []))
    if not state:
        return [str(task_id) for task_id in task_ids]
    terminal = set(state.completed_task_ids) | set(state.blocked_task_ids) | set(state.failed_task_ids) | set(state.skipped_task_ids)
    return [str(task_id) for task_id in task_ids if str(task_id) not in terminal]


def identify_last_safe_checkpoint(state: PlanRunState | None) -> dict[str, Any] | None:
    if not state:
        return None
    if state.checkpoints:
        return dict(state.checkpoints[-1])
    return {
        "completed_task_id": state.completed_task_ids[-1] if state.completed_task_ids else "",
        "completed_count": len(state.completed_task_ids),
        "git_head_last_verified": state.git_head_last_verified,
    }


def produce_recovery_report(report: dict[str, Any], queue_root: str | Path) -> dict[str, Any]:
    root = Path(queue_root)
    run_id = str(report.get("run_id") or "unknown")
    plan_id = str(report.get("plan_id") or "_recovery")
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    if plan_id and plan_id != "_recovery":
        output_dir = root / "generated" / plan_id / run_id / "recovery"
    else:
        output_dir = root / "generated" / "_recovery"
    json_path = output_dir / f"recovery_report_{timestamp}.json"
    md_path = output_dir / f"recovery_report_{timestamp}.md"
    latest_json_path = output_dir / "latest_recovery_report.json"
    latest_md_path = output_dir / "latest_recovery_report.md"
    output_dir.mkdir(parents=True, exist_ok=True)
    report = dict(report)
    report["recovery_report_paths"] = {
        "json": str(json_path),
        "markdown": str(md_path),
        "latest_json": str(latest_json_path),
        "latest_markdown": str(latest_md_path),
    }
    content = json.dumps(report, indent=2, sort_keys=True) + "\n"
    json_path.write_text(content, encoding="utf-8")
    latest_json_path.write_text(content, encoding="utf-8")
    markdown = _render_recovery_markdown(report)
    md_path.write_text(markdown, encoding="utf-8")
    latest_md_path.write_text(markdown, encoding="utf-8")
    return report


def _render_recovery_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# Recovery Report: {report.get('run_id')}",
        "",
        f"- status: `{report.get('status')}`",
        f"- plan_id: `{report.get('plan_id')}`",
        f"- inspected_at: `{report.get('inspected_at')}`",
        f"- manifest_path: `{report.get('manifest_path')}`",
        f"- state_path: `{report.get('state_path')}`",
        f"- lock_path: `{report.get('lock_path')}`",
        f"- lock_status: `{report.get('lock_status')}`",
        f"- safety_ok: `{report.get('safety_ok')}`",
        "",
        "## Consistency Errors",
        "",
    ]
    errors = report.get("consistency_errors") or []
    lines.extend(f"- {error}" for error in errors) if errors else lines.append("- None")
    lines.extend(["", "## Incomplete Tasks", ""])
    incomplete = report.get("incomplete_tasks") or report.get("incomplete_task_ids") or []
    lines.extend(f"- `{task_id}`" for task_id in incomplete) if incomplete else lines.append("- None")
    lines.extend(
        [
            "",
            "## Recommended Operator Action",
            "",
            str(report.get("recommended_operator_action") or ""),
            "",
            "Recovery is local-only and never clears a stale lock unless the operator requested it explicitly.",
            "",
        ]
    )
    return "\n".join(lines)


def _lock_status(lock_state: dict[str, Any]) -> str:
    if not lock_state.get("exists"):
        return "missing"
    return "stale" if lock_state.get("stale") else "active"


def _recommended_action(status: str, lock_exists: bool, consistency_ok: bool) -> str:
    if status == "recovered":
        return "Review recovery report, then continue-plan with a small max-steps value."
    if lock_exists:
        return "Inspect the lock. If it is stale and no run is active, rerun recover-plan with --allow-stale-lock-clear."
    if not consistency_ok:
        return "Inspect state consistency errors and restore a checkpoint or repair state before continuing."
    return "Resolve listed blockers before continuing."


def _utc_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
