from __future__ import annotations

import subprocess
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from .selective_staging_planner import StagingPlan, validate_staging_plan


@dataclass(frozen=True)
class CommitPushVerifyResult:
    status: str
    dry_run: bool
    commands: tuple[list[str], ...] = field(default_factory=tuple)
    local_head: str = ""
    remote_head: str = ""
    remote_verified: bool = False
    errors: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["commands"] = [list(command) for command in self.commands]
        payload["errors"] = list(self.errors)
        payload["warnings"] = list(self.warnings)
        return payload


def run_git(args: list[str], repo_root: str | Path) -> dict[str, Any]:
    _reject_unsafe_git_args(args)
    completed = subprocess.run(
        ["git", *args],
        cwd=str(repo_root),
        check=False,
        capture_output=True,
        text=True,
    )
    return {
        "returncode": completed.returncode,
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
        "args": ["git", *args],
    }


def selective_commit(
    repo_root: str | Path,
    staging_plan: StagingPlan,
    message: str,
    dry_run: bool = True,
) -> CommitPushVerifyResult:
    validation = validate_staging_plan(staging_plan)
    if not validation["valid"]:
        return CommitPushVerifyResult("blocked", dry_run, errors=tuple(validation["errors"]))
    commands = tuple(["git", "add", "--", path] for path in staging_plan.allowed_files) + (
        ["git", "commit", "-m", message],
    )
    if dry_run:
        return CommitPushVerifyResult("dry_run", True, commands=commands, warnings=tuple(validation["warnings"]))
    errors: list[str] = []
    for file_path in staging_plan.allowed_files:
        result = run_git(["add", "--", file_path], repo_root)
        if result["returncode"] != 0:
            errors.append(result["stderr"] or f"git add failed for {file_path}")
    if errors:
        return CommitPushVerifyResult("failed", False, commands=commands, errors=tuple(errors))
    result = run_git(["commit", "-m", message], repo_root)
    if result["returncode"] != 0:
        return CommitPushVerifyResult(
            "failed",
            False,
            commands=commands,
            errors=(result["stderr"] or "git commit failed",),
        )
    head = run_git(["rev-parse", "HEAD"], repo_root)
    return CommitPushVerifyResult(
        "committed",
        False,
        commands=commands,
        local_head=head["stdout"] if head["returncode"] == 0 else "",
        errors=(),
        warnings=tuple(validation["warnings"]),
    )


def push_and_verify(
    repo_root: str | Path,
    branch: str,
    remote: str = "origin",
    dry_run: bool = True,
) -> CommitPushVerifyResult:
    if not branch or branch.startswith("-"):
        return CommitPushVerifyResult("blocked", dry_run, errors=("invalid branch name",))
    commands = (["git", "push", remote, branch], ["git", "ls-remote", remote, f"refs/heads/{branch}"])
    if dry_run:
        local = run_git(["rev-parse", "HEAD"], repo_root)
        return CommitPushVerifyResult(
            "dry_run",
            True,
            commands=commands,
            local_head=local["stdout"] if local["returncode"] == 0 else "",
        )
    push = run_git(["push", remote, branch], repo_root)
    if push["returncode"] != 0:
        return CommitPushVerifyResult("failed", False, commands=commands, errors=(push["stderr"] or "git push failed",))
    local = run_git(["rev-parse", "HEAD"], repo_root)
    remote_result = run_git(["ls-remote", remote, f"refs/heads/{branch}"], repo_root)
    local_head = local["stdout"] if local["returncode"] == 0 else ""
    remote_head = remote_result["stdout"].split()[0] if remote_result["returncode"] == 0 and remote_result["stdout"] else ""
    return CommitPushVerifyResult(
        "verified" if local_head and local_head == remote_head else "failed",
        False,
        commands=commands,
        local_head=local_head,
        remote_head=remote_head,
        remote_verified=bool(local_head and local_head == remote_head),
        errors=() if local_head and local_head == remote_head else ("remote HEAD did not match local HEAD",),
    )


def _reject_unsafe_git_args(args: list[str]) -> None:
    lowered = [arg.lower() for arg in args]
    text = " ".join(lowered)
    if lowered[:1] == ["add"] and any(arg in {".", "-a", "--all"} for arg in lowered[1:]):
        raise ValueError("unsafe git add command rejected")
    if lowered[:1] == ["push"] and ("--force" in lowered or "-f" in lowered or "--force-with-lease" in lowered):
        raise ValueError("force push rejected")
    if "git add ." in text or "git add -a" in text or "git add --all" in text:
        raise ValueError("unsafe git add command rejected")
