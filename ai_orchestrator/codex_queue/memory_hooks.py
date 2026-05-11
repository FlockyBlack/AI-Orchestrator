from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .plan_contract import PlanTaskSpec


SAFE_SUFFIXES = {".md", ".json", ".py", ".txt"}
BLOCKED_NAME_PARTS = {".env", "secret", "credential", "wallet", "private_key"}


@dataclass(frozen=True)
class ProjectMemorySnapshot:
    repo_root: str
    allowed_roots: tuple[str, ...]
    captured_at: str
    files: tuple[dict[str, Any], ...] = ()
    warnings: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["allowed_roots"] = list(self.allowed_roots)
        payload["files"] = list(self.files)
        payload["warnings"] = list(self.warnings)
        return payload


@dataclass(frozen=True)
class MemoryHookResult:
    status: str
    snapshot: ProjectMemorySnapshot
    rendered_context: str = ""
    errors: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "snapshot": self.snapshot.to_dict(),
            "rendered_context": self.rendered_context,
            "errors": list(self.errors),
        }


def collect_local_project_context_snapshot(
    repo_root: str | Path,
    allowed_roots: tuple[str, ...] | list[str],
) -> ProjectMemorySnapshot:
    root = Path(repo_root).resolve(strict=False)
    warnings: list[str] = []
    files: list[dict[str, Any]] = []
    for allowed in allowed_roots:
        if _blocked_path(allowed):
            warnings.append(f"blocked sensitive allowed root skipped: {allowed}")
            continue
        base = (root / allowed).resolve(strict=False)
        if not _is_relative_to(base, root):
            warnings.append(f"allowed root escapes repo and was skipped: {allowed}")
            continue
        if not base.exists():
            warnings.append(f"allowed root does not exist: {allowed}")
            continue
        candidates = [base] if base.is_file() else sorted(path for path in base.rglob("*") if path.is_file())
        for path in candidates:
            if len(files) >= 40:
                warnings.append("snapshot file cap reached")
                break
            if _blocked_path(str(path)) or path.suffix.lower() not in SAFE_SUFFIXES:
                continue
            try:
                rel = path.relative_to(root).as_posix()
                size = path.stat().st_size
            except OSError:
                continue
            files.append({"path": rel, "size": size, "suffix": path.suffix.lower()})
    return ProjectMemorySnapshot(
        repo_root=str(root),
        allowed_roots=tuple(str(value) for value in allowed_roots),
        captured_at=_utc_iso(),
        files=tuple(files),
        warnings=tuple(warnings),
    )


def render_memory_context_for_task(task_spec: PlanTaskSpec, snapshot: ProjectMemorySnapshot) -> str:
    lines = [
        f"# Local Memory Context: {task_spec.task_id}",
        "",
        f"- repo_root: `{snapshot.repo_root}`",
        f"- captured_at: `{snapshot.captured_at}`",
        "",
        "## Allowed Roots",
        "",
    ]
    lines.extend(f"- `{root}`" for root in snapshot.allowed_roots)
    lines.extend(["", "## Local Files", ""])
    if snapshot.files:
        lines.extend(f"- `{item['path']}` ({item['size']} bytes)" for item in snapshot.files)
    else:
        lines.append("- None")
    if snapshot.warnings:
        lines.extend(["", "## Warnings", ""])
        lines.extend(f"- {warning}" for warning in snapshot.warnings)
    lines.extend(
        [
            "",
            "This context is local-only. It does not install Locus, use MCP, call external services, or read sensitive files.",
            "",
        ]
    )
    return "\n".join(lines)


def _blocked_path(value: str) -> bool:
    lowered = value.lower().replace("\\", "/")
    return any(part in lowered for part in BLOCKED_NAME_PARTS)


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def _utc_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
