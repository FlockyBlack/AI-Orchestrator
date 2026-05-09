from __future__ import annotations

import re
import subprocess
from pathlib import Path
from typing import Any

BRANCH_MAX_LENGTH = 96
BRANCH_ALLOWED_RE = re.compile(r"^[a-z0-9][a-z0-9/-]*$")
WINDOWS_INVALID_CHARS_RE = re.compile(r'[<>:"\\|?*\s]')
CONFLICT_STATUS_CODES = {
    "DD",
    "AU",
    "UD",
    "UA",
    "DU",
    "AA",
    "UU",
}
MANY_UNTRACKED_THRESHOLD = 50


def inspect_git_state(repo_root: str) -> dict[str, Any]:
    """Inspect local git state using read-only git commands only."""
    cwd = Path(repo_root).resolve(strict=False)
    warnings: list[str] = []
    errors: list[str] = []

    top_level = _run_git(["rev-parse", "--show-toplevel"], cwd)
    if top_level["returncode"] != 0:
        return {
            "repo_root": str(cwd),
            "branch": "",
            "head": "",
            "status_lines": [],
            "is_clean": False,
            "tracked_changes_count": 0,
            "untracked_count": 0,
            "warnings": warnings,
            "errors": [top_level["error"] or "failed to resolve git repository root"],
        }

    resolved_root = top_level["stdout"].strip()
    git_cwd = Path(resolved_root).resolve(strict=False)

    branch_result = _run_git(["branch", "--show-current"], git_cwd)
    head_result = _run_git(["rev-parse", "HEAD"], git_cwd)
    status_result = _run_git(["status", "--short"], git_cwd)

    for label, result in (
        ("branch", branch_result),
        ("head", head_result),
        ("status", status_result),
    ):
        if result["returncode"] != 0:
            errors.append(result["error"] or f"failed to inspect git {label}")

    status_lines = status_result["stdout"].splitlines() if status_result["returncode"] == 0 else []
    classification = classify_working_tree_status(status_lines)
    dangerous = detect_dangerous_git_state(status_lines)

    warnings.extend(classification["warnings"])
    warnings.extend(dangerous["warnings"])
    errors.extend(dangerous["errors"])

    return {
        "repo_root": resolved_root,
        "branch": branch_result["stdout"].strip() if branch_result["returncode"] == 0 else "",
        "head": head_result["stdout"].strip() if head_result["returncode"] == 0 else "",
        "status_lines": status_lines,
        "is_clean": classification["is_clean"],
        "tracked_changes_count": classification["tracked_changes_count"],
        "untracked_count": classification["untracked_count"],
        "warnings": warnings,
        "errors": errors,
    }


def validate_branch_name(branch_name: str) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []

    if not isinstance(branch_name, str) or not branch_name.strip():
        return {
            "valid": False,
            "branch_name": branch_name,
            "errors": ["branch name must be a non-empty string"],
            "warnings": warnings,
        }

    value = branch_name.strip()
    if value != branch_name:
        errors.append("branch name must not have leading or trailing whitespace")
    if len(value) > BRANCH_MAX_LENGTH:
        errors.append(f"branch name must be {BRANCH_MAX_LENGTH} characters or fewer")
    if WINDOWS_INVALID_CHARS_RE.search(value):
        errors.append("branch name contains whitespace or Windows-invalid filename characters")
    if not BRANCH_ALLOWED_RE.match(value):
        errors.append("branch name must contain only lowercase letters, numbers, dash, and slash")
    if "/" not in value:
        warnings.append("branch name has no namespace slash")
    if value.startswith("/") or value.endswith("/"):
        errors.append("branch name must not start or end with slash")
    if "//" in value:
        errors.append("branch name must not contain consecutive slashes")
    if ".." in value:
        errors.append("branch name must not contain consecutive dots")
    if "@{" in value:
        errors.append("branch name must not contain @{")
    if value.endswith(".lock"):
        errors.append("branch name must not end with .lock")
    if any(part in {"", ".", ".."} for part in value.split("/")):
        errors.append("branch name must not contain empty or dot path segments")

    return {
        "valid": not errors,
        "branch_name": value,
        "errors": errors,
        "warnings": warnings,
    }


def build_safe_branch_name(task_id: str) -> str:
    raw = str(task_id).strip().lower()
    sanitized = re.sub(r"[^a-z0-9]+", "-", raw)
    sanitized = re.sub(r"-+", "-", sanitized).strip("-")
    if not sanitized:
        sanitized = "task"

    max_task_length = BRANCH_MAX_LENGTH - len("codex/")
    if len(sanitized) > max_task_length:
        sanitized = sanitized[:max_task_length].rstrip("-") or "task"

    branch_name = f"codex/{sanitized}"
    validation = validate_branch_name(branch_name)
    if validation["valid"]:
        return branch_name
    return "codex/task"


def classify_working_tree_status(status_lines: list[str]) -> dict[str, Any]:
    tracked_changes: list[str] = []
    untracked: list[str] = []
    ignored: list[str] = []

    for line in status_lines:
        status = _status_code(line)
        if status == "??":
            untracked.append(line)
        elif status == "!!":
            ignored.append(line)
        elif status:
            tracked_changes.append(line)

    warnings: list[str] = []
    if tracked_changes:
        warnings.append(
            f"tracked files have local changes and require operator review: {len(tracked_changes)}"
        )
    if len(untracked) >= MANY_UNTRACKED_THRESHOLD:
        warnings.append(f"working tree has many untracked files: {len(untracked)}")
    elif untracked:
        warnings.append(f"working tree has untracked files: {len(untracked)}")

    return {
        "is_clean": not tracked_changes and not untracked,
        "tracked_changes_count": len(tracked_changes),
        "untracked_count": len(untracked),
        "ignored_count": len(ignored),
        "tracked_change_lines": tracked_changes,
        "untracked_lines": untracked,
        "ignored_lines": ignored,
        "warnings": warnings,
    }


def detect_dangerous_git_state(status_lines: list[str]) -> dict[str, Any]:
    conflict_lines = [
        line
        for line in status_lines
        if _status_code(line) in CONFLICT_STATUS_CODES or _looks_conflict_like(_status_code(line))
    ]
    errors: list[str] = []
    if conflict_lines:
        errors.append("merge/rebase conflict indicators detected in git status")

    return {
        "blocked": bool(conflict_lines),
        "conflict_lines": conflict_lines,
        "warnings": [],
        "errors": errors,
    }


def _run_git(args: list[str], cwd: Path) -> dict[str, Any]:
    try:
        completed = subprocess.run(
            ["git", *args],
            cwd=str(cwd),
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError as exc:
        return {"returncode": 1, "stdout": "", "stderr": str(exc), "error": str(exc)}

    stderr = completed.stderr.strip()
    return {
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "error": stderr if completed.returncode != 0 else "",
    }


def _status_code(line: str) -> str:
    if len(line) < 2:
        return ""
    return line[:2]


def _looks_conflict_like(status: str) -> bool:
    if len(status) != 2:
        return False
    return "U" in status and status not in {"??", "!!"}
