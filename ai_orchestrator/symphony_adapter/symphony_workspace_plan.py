from __future__ import annotations

import re
import subprocess
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Mapping

from .symphony_task_contract import SymphonyTask


WORKSPACE_PLAN_SCHEMA_VERSION = "symphony_workspace_plan.v1"
_SAFE_SEGMENT_RE = re.compile(r"[^A-Za-z0-9._-]+")
_UNSAFE_COMMAND_PATTERNS = (
    "git reset --hard",
    "git clean",
    "git add .",
    "git add -a",
    "git add --all",
    "git push --force",
    "git push -f",
    "--force-with-lease",
    " rm -rf",
    " rmdir ",
    " del ",
    "git merge",
)


class WorkspaceIsolationMode(str, Enum):
    WORKTREE_PLANNED = "worktree_planned"
    DIRECTORY_ONLY = "directory_only"
    DISABLED = "disabled"


@dataclass(frozen=True)
class SymphonyWorkspacePlan:
    task_id: str
    repo_root: str
    workspace_root: str
    workspace_path: str
    isolation_mode: str = WorkspaceIsolationMode.WORKTREE_PLANNED.value
    branch_name: str = ""
    base_branch: str = ""
    base_head: str = ""
    setup_commands: tuple[str, ...] = ()
    dry_run_only: bool = True
    would_create_worktree: bool = False
    worktree_created: bool = False
    would_merge: bool = False
    automatic_merge: bool = False
    external_network_allowed: bool = False
    force_operations_allowed: bool = False
    errors: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    schema_version: str = WORKSPACE_PLAN_SCHEMA_VERSION

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "SymphonyWorkspacePlan":
        return cls(
            task_id=str(payload.get("task_id") or ""),
            repo_root=str(payload.get("repo_root") or ""),
            workspace_root=str(payload.get("workspace_root") or ""),
            workspace_path=str(payload.get("workspace_path") or ""),
            isolation_mode=str(payload.get("isolation_mode") or WorkspaceIsolationMode.WORKTREE_PLANNED.value),
            branch_name=str(payload.get("branch_name") or ""),
            base_branch=str(payload.get("base_branch") or ""),
            base_head=str(payload.get("base_head") or ""),
            setup_commands=tuple(str(value) for value in payload.get("setup_commands", [])),
            dry_run_only=bool(payload.get("dry_run_only", True)),
            would_create_worktree=bool(payload.get("would_create_worktree", False)),
            worktree_created=bool(payload.get("worktree_created", False)),
            would_merge=bool(payload.get("would_merge", False)),
            automatic_merge=bool(payload.get("automatic_merge", False)),
            external_network_allowed=bool(payload.get("external_network_allowed", False)),
            force_operations_allowed=bool(payload.get("force_operations_allowed", False)),
            errors=tuple(str(value) for value in payload.get("errors", [])),
            warnings=tuple(str(value) for value in payload.get("warnings", [])),
            schema_version=str(payload.get("schema_version") or WORKSPACE_PLAN_SCHEMA_VERSION),
        )

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["setup_commands"] = list(self.setup_commands)
        payload["errors"] = list(self.errors)
        payload["warnings"] = list(self.warnings)
        return payload


def build_workspace_plan_for_task(
    task: SymphonyTask | Mapping[str, Any],
    repo_root: str | Path,
    workspace_root: str | Path,
) -> SymphonyWorkspacePlan:
    task_obj = task if isinstance(task, SymphonyTask) else SymphonyTask.from_dict(task)
    repo = Path(repo_root).resolve(strict=False)
    workspace_base = Path(workspace_root).resolve(strict=False)
    safe_key = _safe_workspace_key(task_obj.task_id)
    workspace_path = (workspace_base / safe_key).resolve(strict=False)
    base_branch = _git_value(repo, ("branch", "--show-current"))
    base_head = _git_value(repo, ("rev-parse", "HEAD"))
    branch_name = f"codex/{safe_key.lower()}"
    commands = (
        f"git -C {str(repo)!r} status --short",
        f"git -C {str(repo)!r} rev-parse HEAD",
        f"git -C {str(repo)!r} worktree list",
        f"Write-Output 'DRY RUN: would prepare worktree {str(workspace_path)} on branch {branch_name}; no branch/worktree is created by this plan.'",
    )
    plan = SymphonyWorkspacePlan(
        task_id=task_obj.task_id,
        repo_root=str(repo),
        workspace_root=str(workspace_base),
        workspace_path=str(workspace_path),
        branch_name=branch_name,
        base_branch=base_branch,
        base_head=base_head,
        setup_commands=commands,
        dry_run_only=True,
        would_create_worktree=True,
        worktree_created=False,
        would_merge=False,
        automatic_merge=False,
        external_network_allowed=False,
        force_operations_allowed=False,
        warnings=tuple(_metadata_warnings(base_branch, base_head)),
    )
    validation = validate_workspace_plan(plan)
    return SymphonyWorkspacePlan.from_dict({**plan.to_dict(), "errors": validation["errors"], "warnings": validation["warnings"]})


def validate_workspace_plan(plan: SymphonyWorkspacePlan | Mapping[str, Any]) -> dict[str, Any]:
    plan_obj = plan if isinstance(plan, SymphonyWorkspacePlan) else SymphonyWorkspacePlan.from_dict(plan)
    errors: list[str] = []
    warnings: list[str] = list(plan_obj.warnings)
    repo = Path(plan_obj.repo_root).resolve(strict=False)
    workspace_root = Path(plan_obj.workspace_root).resolve(strict=False)
    workspace_path = Path(plan_obj.workspace_path).resolve(strict=False)
    if not plan_obj.task_id.strip():
        errors.append("missing task_id")
    if not plan_obj.base_head:
        warnings.append("base_head is empty; git HEAD metadata could not be resolved")
    if not plan_obj.base_branch:
        warnings.append("base_branch is empty; git branch metadata could not be resolved")
    if not _is_relative_to(workspace_path, workspace_root):
        errors.append("workspace_path must stay inside workspace_root")
    if _is_relative_to(workspace_path, repo):
        warnings.append("workspace_path is inside repo_root; keep this as a render-only plan unless a separate task approves workspace materialization")
    if _is_relative_to(workspace_path, repo / ".git"):
        errors.append("workspace_path must not be inside .git")
    if plan_obj.worktree_created:
        errors.append("workspace plan must not claim a worktree was created")
    if plan_obj.automatic_merge or plan_obj.would_merge:
        errors.append("workspace plan must not perform or schedule automatic merge")
    if plan_obj.external_network_allowed:
        errors.append("workspace plan must not allow external network")
    if plan_obj.force_operations_allowed:
        errors.append("workspace plan must not allow force operations")
    if not plan_obj.dry_run_only:
        errors.append("workspace plan must be dry_run_only")
    for command in plan_obj.setup_commands:
        lowered = command.lower()
        for pattern in _UNSAFE_COMMAND_PATTERNS:
            if pattern in lowered:
                errors.append(f"unsafe workspace setup command: {pattern}")
    return {"valid": not errors, "errors": list(dict.fromkeys(errors)), "warnings": list(dict.fromkeys(warnings))}


def render_workspace_setup_commands(plan: SymphonyWorkspacePlan | Mapping[str, Any]) -> tuple[str, ...]:
    plan_obj = plan if isinstance(plan, SymphonyWorkspacePlan) else SymphonyWorkspacePlan.from_dict(plan)
    validation = validate_workspace_plan(plan_obj)
    if not validation["valid"]:
        return (
            "Write-Output 'BLOCKED: workspace setup command preview is invalid; inspect workspace_plan.json errors.'",
        )
    return plan_obj.setup_commands


def _safe_workspace_key(task_id: str) -> str:
    safe = _SAFE_SEGMENT_RE.sub("_", task_id.strip()).strip("._-")
    return safe or "symphony_task"


def _git_value(repo: Path, args: tuple[str, ...]) -> str:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=repo,
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        return ""
    return result.stdout.strip() if result.returncode == 0 else ""


def _metadata_warnings(base_branch: str, base_head: str) -> list[str]:
    warnings: list[str] = []
    if not base_branch:
        warnings.append("git branch metadata unavailable")
    if not base_head:
        warnings.append("git head metadata unavailable")
    return warnings


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True
