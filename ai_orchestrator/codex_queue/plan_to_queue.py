from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .plan_contract import load_plan_contract, validate_plan_contract
from .plan_decomposer import decompose_plan, serialize_task_for_queue


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
    if not validation.valid:
        return QueueCreationResult(
            status="blocked",
            plan_id=plan.plan_id,
            run_id=run_id or _run_id(),
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
            run_id=run_id or _run_id(),
            source_plan_file=str(source),
            task_count=len(plan.tasks),
            task_ids=tuple(task.task_id for task in plan.tasks),
            queue_paths={},
            errors=decomposition.errors,
            warnings=decomposition.warnings,
            dry_run=dry_run,
        )

    safe_run_id = run_id or _run_id()
    run_root = queue_root_path / "generated" / plan.plan_id / safe_run_id
    tasks_dir = run_root / "tasks"
    manifest_path = run_root / "manifest.json"
    readme_path = run_root / "README.md"
    task_ids = tuple(task.task_id for task in decomposition.ordered_tasks)
    task_paths = {
        task.task_id: str(tasks_dir / f"{task.task_id}.json")
        for task in decomposition.ordered_tasks
    }
    queue_paths = {
        "run_root": str(run_root),
        "tasks_dir": str(tasks_dir),
        "manifest": str(manifest_path),
        "readme": str(readme_path),
        "tasks": task_paths,
    }

    if not dry_run:
        tasks_dir.mkdir(parents=True, exist_ok=True)
        for task in decomposition.ordered_tasks:
            _write_json(tasks_dir / f"{task.task_id}.json", serialize_task_for_queue(task, plan.plan_id, safe_run_id))
        manifest = {
            "schema_version": "codex_plan_queue_manifest.v1",
            "plan_id": plan.plan_id,
            "run_id": safe_run_id,
            "source_plan_file": str(source),
            "created_at": _utc_iso(),
            "task_count": len(task_ids),
            "task_ids": list(task_ids),
            "queue_paths": queue_paths,
            "status": "created",
        }
        _write_json(manifest_path, manifest)
        _write_text(readme_path, _render_readme(plan.plan_id, safe_run_id, source, task_ids))

    return QueueCreationResult(
        status="created" if not dry_run else "dry_run",
        plan_id=plan.plan_id,
        run_id=safe_run_id,
        source_plan_file=str(source),
        task_count=len(task_ids),
        task_ids=task_ids,
        queue_paths=queue_paths,
        errors=(),
        warnings=tuple(validation.warnings),
        dry_run=dry_run,
    )


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


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


def _run_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _utc_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
