from __future__ import annotations

import subprocess
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


DEFAULT_ALLOWED_ROOTS = (
    "ai_orchestrator/codex_queue/",
    "ai_orchestrator/operator_panel/",
    "agent_tasks/plans/",
    "agent_tasks/generated/",
    "agent_tasks/automations/",
    "docs/",
    "tests/",
    "pm_bot/practical/automation/",
    "pm_bot/practical/artifacts/automation/",
)

DEFAULT_BLOCKED_PATTERNS = (
    ".git/",
    ".env",
    "__pycache__",
    ".pyc",
    "secrets",
    "private",
    "credential",
    "wallet",
)


@dataclass(frozen=True)
class StagingPlan:
    repo_root: str
    changed_files: tuple[str, ...]
    allowed_files: tuple[str, ...]
    blocked_files: tuple[str, ...]
    commands: tuple[str, ...] = field(default_factory=tuple)
    valid: bool = False
    errors: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["changed_files"] = list(self.changed_files)
        payload["allowed_files"] = list(self.allowed_files)
        payload["blocked_files"] = list(self.blocked_files)
        payload["commands"] = list(self.commands)
        payload["errors"] = list(self.errors)
        payload["warnings"] = list(self.warnings)
        return payload


def collect_git_status(repo_root: str | Path) -> dict[str, Any]:
    completed = subprocess.run(
        ["git", "status", "--short"],
        cwd=str(repo_root),
        check=False,
        capture_output=True,
        text=True,
    )
    lines = completed.stdout.splitlines() if completed.returncode == 0 else []
    return {
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "changed_files": tuple(_parse_status_path(line) for line in lines if _parse_status_path(line)),
        "status_lines": lines,
    }


def build_selective_staging_plan(
    repo_root: str | Path,
    changed_files: tuple[str, ...] | list[str],
    allowed_roots: tuple[str, ...] | list[str] = DEFAULT_ALLOWED_ROOTS,
    blocked_patterns: tuple[str, ...] | list[str] = DEFAULT_BLOCKED_PATTERNS,
) -> StagingPlan:
    allowed: list[str] = []
    blocked: list[str] = []
    warnings: list[str] = []
    for file_path in sorted(dict.fromkeys(str(path).replace("\\", "/") for path in changed_files)):
        if _blocked(file_path, blocked_patterns):
            blocked.append(file_path)
            continue
        if _allowed(file_path, allowed_roots):
            allowed.append(file_path)
        else:
            blocked.append(file_path)
            warnings.append(f"outside allowed staging roots: {file_path}")
    commands = tuple(render_git_add_commands_for_files(allowed))
    plan = StagingPlan(
        repo_root=str(repo_root),
        changed_files=tuple(changed_files),
        allowed_files=tuple(allowed),
        blocked_files=tuple(blocked),
        commands=commands,
        warnings=tuple(warnings),
    )
    validation = validate_staging_plan(plan)
    return StagingPlan(
        repo_root=plan.repo_root,
        changed_files=plan.changed_files,
        allowed_files=plan.allowed_files,
        blocked_files=plan.blocked_files,
        commands=plan.commands,
        valid=validation["valid"],
        errors=tuple(validation["errors"]),
        warnings=plan.warnings + tuple(validation["warnings"]),
    )


def validate_staging_plan(plan: StagingPlan) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    for command in plan.commands:
        lowered = command.lower()
        if lowered in {"git add .", "git add -a", "git add --all"}:
            errors.append(f"unsafe staging command rendered: {command}")
        if "git add ." in lowered or "git add -a" in lowered or "git add --all" in lowered:
            errors.append(f"unsafe staging command rendered: {command}")
    if not plan.allowed_files:
        warnings.append("no allowed files to stage")
    return {"valid": not errors, "errors": errors, "warnings": warnings}


def render_git_add_commands(plan: StagingPlan) -> list[str]:
    return list(plan.commands)


def render_git_add_commands_for_files(files: list[str]) -> list[str]:
    return [f'git add -- "{path}"' for path in files]


def _parse_status_path(line: str) -> str:
    if len(line) < 4:
        return ""
    path = line[3:].strip()
    if " -> " in path:
        path = path.split(" -> ", 1)[1]
    return path.replace("\\", "/").strip('"')


def _allowed(path: str, allowed_roots: tuple[str, ...] | list[str]) -> bool:
    normalized = path.replace("\\", "/")
    return any(normalized == root.rstrip("/") or normalized.startswith(root.replace("\\", "/")) for root in allowed_roots)


def _blocked(path: str, blocked_patterns: tuple[str, ...] | list[str]) -> bool:
    lowered = path.lower().replace("\\", "/")
    return any(pattern.lower().replace("\\", "/") in lowered for pattern in blocked_patterns)
