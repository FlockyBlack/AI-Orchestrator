from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from .plan_contract import load_plan_contract, validate_plan_contract
from .plan_decomposer import decompose_plan, serialize_task_for_queue


QUEUE_MANIFEST_SCHEMA_VERSION = "codex_plan_queue_manifest.v2"


@dataclass(frozen=True)
class QueueCreationResult:
    status: str
    plan_id: str
    run_id: str
    source_plan_file: str
    task_count: int
    task_ids: tuple[str, ...]
    queue_paths: dict[str, Any]
    errors: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    dry_run: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "plan_id": self.plan_id,
            "run_id": self.run_id,
            "source_plan_file": self.source_plan_file,
            "task_count": self.task_count,
            "task_ids": list(self.task_ids),
            "queue_paths": self.queue_paths,
            "errors": list(self.errors),
            "warnings": list(self.warnings),
            "dry_run": self.dry_run,
        }


def create_queue_from_plan(
    plan_file: str | Path,
    queue_root: str | Path,
    run_id: str | None = None,
    dry_run: bool = False,
) -> QueueCreationResult:
    source = Path(plan_file)
    queue_root_path = Path(queue_root)
    plan = load_plan_contract(source)
    validation = validate_plan_contract(plan)
    safe_run_id = run_id or _run_id()
    source_sha256 = _sha256(source)
    if not validation.valid:
        return QueueCreationResult(
            status="blocked",
            plan_id=plan.plan_id,
            run_id=safe_run_id,
            source_plan_file=str(source),
            task_count=len(plan.tasks),
            task_ids=tuple(task.task_id for task in plan.tasks),
            queue_paths={},
            errors=tuple(validation.errors),
            warnings=tuple(validation.warnings),
            dry_run=dry_run,
        )

    decomposition = decompose_plan(plan)
    if decomposition.errors:
        return QueueCreationResult(
            status="blocked",
            plan_id=plan.plan_id,
            run_id=safe_run_id,
            source_plan_file=str(source),
            task_count=len(plan.tasks),
            task_ids=tuple(task.task_id for task in plan.tasks),
            queue_paths={},
            errors=decomposition.errors,
            warnings=decomposition.warnings,
            dry_run=dry_run,
        )

    run_root = queue_root_path / "generated" / plan.plan_id / safe_run_id
    queue_paths = _queue_paths(run_root, plan.plan_id, safe_run_id, source, decomposition.ordered_tasks)
    task_ids = tuple(task.task_id for task in decomposition.ordered_tasks)
    manifest = _build_manifest(
        plan_id=plan.plan_id,
        run_id=safe_run_id,
        source=source,
        source_sha256=source_sha256,
        task_ids=task_ids,
        queue_paths=queue_paths,
    )

    if dry_run:
        return QueueCreationResult(
            status="dry_run",
            plan_id=plan.plan_id,
            run_id=safe_run_id,
            source_plan_file=str(source),
            task_count=len(task_ids),
            task_ids=task_ids,
            queue_paths=queue_paths,
            errors=(),
            warnings=tuple(validation.warnings),
            dry_run=True,
        )

    manifest_path = Path(queue_paths["manifest"])
    if manifest_path.exists():
        existing = _read_json(manifest_path)
        match = _manifest_matches(existing, manifest)
        if match["matches"]:
            validation_result = validate_queue_manifest(existing)
            status = "exists" if validation_result["valid"] else "blocked"
            return QueueCreationResult(
                status=status,
                plan_id=plan.plan_id,
                run_id=safe_run_id,
                source_plan_file=str(source),
                task_count=len(task_ids),
                task_ids=task_ids,
                queue_paths=queue_paths,
                errors=tuple(validation_result["errors"]),
                warnings=tuple(validation.warnings) + tuple(validation_result["warnings"]),
                dry_run=False,
            )
        return QueueCreationResult(
            status="blocked",
            plan_id=plan.plan_id,
            run_id=safe_run_id,
            source_plan_file=str(source),
            task_count=len(task_ids),
            task_ids=task_ids,
            queue_paths=queue_paths,
            errors=tuple(match["errors"]),
            warnings=tuple(validation.warnings),
            dry_run=False,
        )

    tasks_dir = Path(queue_paths["tasks_dir"])
    tasks_dir.mkdir(parents=True, exist_ok=True)
    for task in decomposition.ordered_tasks:
        _write_json(tasks_dir / f"{task.task_id}.json", serialize_task_for_queue(task, plan.plan_id, safe_run_id))
    _write_json(manifest_path, manifest)
    _write_text(Path(queue_paths["readme"]), _render_readme(plan.plan_id, safe_run_id, source, task_ids))

    validation_result = validate_queue_manifest(manifest)
    return QueueCreationResult(
        status="created" if validation_result["valid"] else "blocked",
        plan_id=plan.plan_id,
        run_id=safe_run_id,
        source_plan_file=str(source),
        task_count=len(task_ids),
        task_ids=task_ids,
        queue_paths=queue_paths,
        errors=tuple(validation_result["errors"]),
        warnings=tuple(validation.warnings) + tuple(validation_result["warnings"]),
        dry_run=False,
    )


def inspect_queue(queue_root: str | Path, run_id: str) -> dict[str, Any]:
    located = find_run_dir(queue_root, run_id)
    if located["status"] != "found":
        return located
    manifest = load_queue_manifest(queue_root, run_id)
    validation = validate_queue_manifest(manifest)
    state_path = Path(str(manifest.get("state_path") or located["run_dir"] / "state.json"))
    return {
        "status": "found" if validation["valid"] else "invalid",
        "run_id": run_id,
        "plan_id": str(manifest.get("plan_id") or located.get("plan_id") or ""),
        "queue_root": str(Path(queue_root)),
        "run_dir": str(located["run_dir"]),
        "manifest_path": str(located["manifest_path"]),
        "state_path": str(state_path),
        "state_exists": state_path.exists(),
        "manifest": manifest,
        "validation": validation,
        "errors": list(validation["errors"]),
        "warnings": list(validation["warnings"]),
    }


def find_run_dir(queue_root: str | Path, run_id: str) -> dict[str, Any]:
    root = Path(queue_root)
    matches = sorted(root.glob(f"generated/*/{run_id}/manifest.json"))
    if not matches:
        return {
            "status": "missing",
            "run_id": run_id,
            "queue_root": str(root),
            "errors": [f"run_id not found: {run_id}"],
        }
    manifest_path = matches[0]
    return {
        "status": "found",
        "run_id": run_id,
        "plan_id": manifest_path.parent.parent.name,
        "run_dir": manifest_path.parent,
        "manifest_path": manifest_path,
        "errors": [],
    }


def load_queue_manifest(queue_root: str | Path, run_id: str) -> dict[str, Any]:
    located = find_run_dir(queue_root, run_id)
    if located["status"] != "found":
        raise FileNotFoundError(f"run_id not found: {run_id}")
    return _read_json(located["manifest_path"])


def validate_queue_manifest(manifest: Mapping[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    required = (
        "plan_id",
        "run_id",
        "source_plan_file",
        "source_plan_sha256",
        "created_at",
        "updated_at",
        "task_count",
        "task_ids",
        "task_paths",
        "status",
        "state_path",
        "dashboard_json_path",
        "dashboard_md_path",
        "handoff_dir",
        "recovery_report_path",
        "lock_path",
    )
    for field in required:
        if field not in manifest or manifest.get(field) in (None, ""):
            errors.append(f"manifest missing required field: {field}")

    task_ids = [str(value) for value in manifest.get("task_ids", [])] if isinstance(manifest.get("task_ids"), list) else []
    task_paths = manifest.get("task_paths", {})
    if not isinstance(task_paths, Mapping):
        errors.append("manifest task_paths must be an object")
        task_paths = {}
    if int(manifest.get("task_count", -1) or -1) != len(task_ids):
        errors.append("manifest task_count does not match task_ids length")
    if set(task_ids) != {str(key) for key in task_paths.keys()}:
        errors.append("manifest task IDs do not match task_paths keys")

    for task_id in task_ids:
        task_path = Path(str(task_paths.get(task_id) or ""))
        if not task_path.exists():
            errors.append(f"task file missing for {task_id}: {task_path}")
            continue
        payload = _read_json(task_path)
        if str(payload.get("task_id") or "") != task_id:
            errors.append(f"task file task_id mismatch for {task_id}: {task_path}")
        if str(payload.get("run_id") or "") and str(payload.get("run_id")) != str(manifest.get("run_id")):
            errors.append(f"task file run_id mismatch for {task_id}: {task_path}")

    source = Path(str(manifest.get("source_plan_file") or ""))
    if source.exists() and manifest.get("source_plan_sha256"):
        actual = _sha256(source)
        if actual != manifest.get("source_plan_sha256"):
            warnings.append("source plan sha256 differs from manifest")

    return {
        "valid": not errors,
        "status": "valid" if not errors else "invalid",
        "errors": list(dict.fromkeys(errors)),
        "warnings": list(dict.fromkeys(warnings)),
    }


def _queue_paths(run_root: Path, plan_id: str, run_id: str, source: Path, tasks: Any) -> dict[str, Any]:
    tasks_dir = run_root / "tasks"
    dashboard_dir = run_root / "dashboard"
    handoff_dir = run_root / "handoff"
    recovery_dir = run_root / "recovery"
    task_paths = {task.task_id: str(tasks_dir / f"{task.task_id}.json") for task in tasks}
    return {
        "run_root": str(run_root),
        "tasks_dir": str(tasks_dir),
        "manifest": str(run_root / "manifest.json"),
        "readme": str(run_root / "README.md"),
        "tasks": task_paths,
        "task_paths": task_paths,
        "state_path": str(run_root / "state.json"),
        "dashboard_json_path": str(dashboard_dir / "dashboard.json"),
        "dashboard_md_path": str(dashboard_dir / "dashboard.md"),
        "handoff_dir": str(handoff_dir),
        "recovery_dir": str(recovery_dir),
        "recovery_report_path": str(recovery_dir / "latest_recovery_report.json"),
        "lock_path": str(run_root / "run.lock"),
    }


def _build_manifest(
    *,
    plan_id: str,
    run_id: str,
    source: Path,
    source_sha256: str,
    task_ids: tuple[str, ...],
    queue_paths: dict[str, Any],
) -> dict[str, Any]:
    now = _utc_iso()
    return {
        "schema_version": QUEUE_MANIFEST_SCHEMA_VERSION,
        "plan_id": plan_id,
        "run_id": run_id,
        "source_plan_file": str(source),
        "source_plan_sha256": source_sha256,
        "created_at": now,
        "updated_at": now,
        "task_count": len(task_ids),
        "task_ids": list(task_ids),
        "task_paths": dict(queue_paths["task_paths"]),
        "queue_paths": queue_paths,
        "status": "created",
        "state_path": queue_paths["state_path"],
        "dashboard_json_path": queue_paths["dashboard_json_path"],
        "dashboard_md_path": queue_paths["dashboard_md_path"],
        "handoff_dir": queue_paths["handoff_dir"],
        "recovery_report_path": queue_paths["recovery_report_path"],
        "lock_path": queue_paths["lock_path"],
    }


def _manifest_matches(existing: Mapping[str, Any], expected: Mapping[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    for key in ("plan_id", "run_id", "source_plan_sha256", "task_count"):
        if existing.get(key) != expected.get(key):
            errors.append(f"manifest conflict on {key}: existing={existing.get(key)!r} expected={expected.get(key)!r}")
    if [str(value) for value in existing.get("task_ids", [])] != [str(value) for value in expected.get("task_ids", [])]:
        errors.append("manifest conflict on task_ids")
    return {"matches": not errors, "errors": errors}


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dict(payload), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _read_json(path: str | Path) -> dict[str, Any]:
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _render_readme(plan_id: str, run_id: str, source: Path, task_ids: tuple[str, ...]) -> str:
    lines = [
        f"# Generated Queue: {plan_id}",
        "",
        f"- run_id: `{run_id}`",
        f"- source_plan_file: `{source}`",
        f"- task_count: `{len(task_ids)}`",
        "",
        "## Tasks",
        "",
    ]
    lines.extend(f"- `{task_id}`" for task_id in task_ids)
    lines.extend(
        [
            "",
            "This queue was materialized locally. It does not invoke Codex, start workers, create schedulers, call network services, or perform git operations.",
            "",
        ]
    )
    return "\n".join(lines)


def _sha256(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def _run_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _utc_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
