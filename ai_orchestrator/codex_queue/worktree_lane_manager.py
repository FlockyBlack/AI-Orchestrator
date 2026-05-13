from __future__ import annotations

import hashlib
import subprocess
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from .files import ensure_queue_directories, safe_queue_path, validate_task_id, write_json_atomic, write_text_atomic
from .git_safety import BRANCH_MAX_LENGTH, inspect_git_state, validate_branch_name
from .plan_contract import PlanContract
from .subagent_routing import CATEGORY_CODEX_AUTOMATION, route_subagent_profile

WORKTREE_LANE_SCHEMA_VERSION = "codex_worktree_lane.v1"

@dataclass(frozen=True)
class WorktreeLane:
    lane_id: str
    task_ids: tuple[str, ...]
    allowed_roots: tuple[str, ...] = ()
    suggested_branch: str = ""
    suggested_worktree_path: str = ""
    dry_run_only: bool = True

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["task_ids"] = list(self.task_ids)
        payload["allowed_roots"] = list(self.allowed_roots)
        return payload


@dataclass(frozen=True)
class LanePlan:
    plan_id: str
    repo_root: str
    branch: str
    lanes: tuple[WorktreeLane, ...]
    errors: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    commands: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "repo_root": self.repo_root,
            "branch": self.branch,
            "lanes": [lane.to_dict() for lane in self.lanes],
            "errors": list(self.errors),
            "warnings": list(self.warnings),
            "commands": list(self.commands),
        }


def build_lane_plan(plan_contract: PlanContract) -> LanePlan:
    lane_meta = {lane.lane_id: lane for lane in plan_contract.execution_lanes}
    tasks_by_lane: dict[str, list[str]] = {}
    for task in plan_contract.tasks:
        tasks_by_lane.setdefault(task.execution_lane, []).append(task.task_id)

    lanes: list[WorktreeLane] = []
    repo_root = Path(plan_contract.repo_root or ".").resolve(strict=False)
    for lane_id in sorted(tasks_by_lane):
        meta = lane_meta.get(lane_id)
        safe_lane = _safe_lane_name(lane_id)
        lanes.append(
            WorktreeLane(
                lane_id=lane_id,
                task_ids=tuple(sorted(tasks_by_lane[lane_id])),
                allowed_roots=meta.allowed_roots if meta else (),
                suggested_branch=f"codex/{safe_lane}",
                suggested_worktree_path=str(repo_root.parent / "AI-Orchestrator-worktrees" / safe_lane),
                dry_run_only=True,
            )
        )
    plan = LanePlan(
        plan_id=plan_contract.plan_id,
        repo_root=str(repo_root),
        branch=plan_contract.branch,
        lanes=tuple(lanes),
    )
    validation = validate_lane_isolation(plan)
    commands = tuple(render_worktree_commands(plan))
    return LanePlan(
        plan_id=plan.plan_id,
        repo_root=plan.repo_root,
        branch=plan.branch,
        lanes=plan.lanes,
        errors=tuple(validation["errors"]),
        warnings=tuple(validation["warnings"]),
        commands=commands,
    )


def validate_lane_isolation(lane_plan: LanePlan) -> dict[str, list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    for lane in lane_plan.lanes:
        if not lane.lane_id:
            errors.append("lane_id must not be empty")
        if not lane.task_ids:
            warnings.append(f"lane {lane.lane_id} has no tasks")
        if not lane.allowed_roots:
            warnings.append(f"lane {lane.lane_id} has no allowed_roots metadata")
        if ".git" in lane.suggested_worktree_path.replace("\\", "/"):
            errors.append(f"lane {lane.lane_id} suggested worktree path points inside .git")
    return {"errors": errors, "warnings": warnings}


def render_worktree_commands(lane_plan: LanePlan) -> list[str]:
    commands: list[str] = []
    for lane in lane_plan.lanes:
        commands.append(
            "git worktree add "
            f'"{lane.suggested_worktree_path}" '
            f'-b "{lane.suggested_branch}" '
            f'"{lane_plan.branch or "master"}"'
        )
    return commands


def _safe_lane_name(lane_id: str) -> str:
    value = "".join(ch.lower() if ch.isalnum() else "-" for ch in lane_id)
    while "--" in value:
        value = value.replace("--", "-")
    return value.strip("-") or "lane"


def plan_task_worktree_lane(
    queue_root: str | Path,
    *,
    task_id: str,
    run_id: str,
    repo_root: str | Path = ".",
    expected_base_branch: str = "master",
    expected_base_head: str = "",
    lane_root: str | Path | None = None,
    task_category: str = "",
    git_state_override: dict[str, Any] | None = None,
) -> dict[str, Any]:
    root = ensure_queue_directories(queue_root)
    safe_task_id = validate_task_id(task_id)
    safe_run_id = _safe_artifact_id(run_id, field_name="run_id")
    repo = Path(repo_root).resolve(strict=False)
    artifact_dir = _lane_artifact_dir(root, safe_task_id, safe_run_id)
    branch = _lane_branch_name(safe_task_id, safe_run_id)
    worktree_path = _lane_worktree_path(repo, safe_task_id, safe_run_id, lane_root)
    route = route_subagent_profile(
        safe_task_id,
        task_category=task_category,
        repo_root=repo,
    )
    git_state = (
        dict(git_state_override)
        if isinstance(git_state_override, dict)
        else inspect_git_state(str(repo))
    )
    blockers, warnings = _lane_preflight_blockers(
        repo=repo,
        queue_root=root,
        git_state=git_state,
        expected_base_branch=expected_base_branch,
        expected_base_head=expected_base_head,
        branch=branch,
        worktree_path=worktree_path,
        task_category=route.category,
    )
    warnings.extend(route.warnings)
    status = "blocked" if blockers else "planned"
    command = ["git", "worktree", "add", "-b", branch, str(worktree_path), expected_base_head or expected_base_branch]
    return {
        "schema_version": WORKTREE_LANE_SCHEMA_VERSION,
        "task_id": safe_task_id,
        "run_id": safe_run_id,
        "lane_id": f"{safe_task_id}:{safe_run_id}",
        "status": status,
        "ready": not blockers,
        "execution_allowed": not blockers,
        "blocker_reason": blockers[0] if blockers else None,
        "blockers": blockers,
        "warnings": warnings,
        "repo": {
            "root": str(git_state.get("repo_root") or repo),
            "expected_base_branch": expected_base_branch,
            "expected_base_head": expected_base_head,
            "current_branch": str(git_state.get("branch") or ""),
            "current_head": str(git_state.get("head") or ""),
            "is_clean": bool(git_state.get("is_clean", False)),
            "status_lines": list(git_state.get("status_lines", [])),
            "tracked_changes_count": int(git_state.get("tracked_changes_count", 0) or 0),
            "untracked_count": int(git_state.get("untracked_count", 0) or 0),
        },
        "task_category": route.category,
        "subagent_route": route.to_dict(),
        "selected_subagent_profile": route.selected_profile,
        "selected_subagent_profile_path": route.selected_profile_path,
        "branch": branch,
        "worktree_path": str(worktree_path),
        "artifact_dir": str(artifact_dir),
        "state_path": str(artifact_dir / "lane_state.json"),
        "would_create_branch": not blockers,
        "would_create_worktree": not blockers,
        "branch_created": False,
        "worktree_created": False,
        "git_command": command,
        "safety": _lane_safety_payload(route.category),
    }


def create_task_worktree_lane(
    queue_root: str | Path,
    *,
    task_id: str,
    run_id: str,
    repo_root: str | Path = ".",
    expected_base_branch: str = "master",
    expected_base_head: str = "",
    lane_root: str | Path | None = None,
    task_category: str = "",
) -> dict[str, Any]:
    state = plan_task_worktree_lane(
        queue_root,
        task_id=task_id,
        run_id=run_id,
        repo_root=repo_root,
        expected_base_branch=expected_base_branch,
        expected_base_head=expected_base_head,
        lane_root=lane_root,
        task_category=task_category,
    )
    if state["blockers"]:
        state["status"] = "blocked"
        state["ready"] = False
        state["execution_allowed"] = False
        return state

    repo = Path(state["repo"]["root"]).resolve(strict=False)
    command = ["worktree", "add", "-b", state["branch"], state["worktree_path"], expected_base_head or expected_base_branch]
    result = _run_git(command, repo)
    state["git_worktree_add"] = result
    if result["returncode"] != 0:
        error = result["stderr"] or result["stdout"] or "git worktree add failed"
        state["status"] = "blocked"
        state["ready"] = False
        state["execution_allowed"] = False
        state["blocker_reason"] = error
        state["blockers"] = [*state["blockers"], error]
        state["would_create_branch"] = False
        state["would_create_worktree"] = False
        return state

    state["status"] = "ready"
    state["ready"] = True
    state["execution_allowed"] = True
    state["branch_created"] = True
    state["worktree_created"] = True
    state["worktree_git_state"] = inspect_git_state(state["worktree_path"])
    return state


def inspect_task_worktree_lane(
    queue_root: str | Path,
    *,
    task_id: str,
    run_id: str,
    repo_root: str | Path = ".",
    expected_base_branch: str = "master",
    expected_base_head: str = "",
    lane_root: str | Path | None = None,
    task_category: str = "",
) -> dict[str, Any]:
    root = ensure_queue_directories(queue_root)
    safe_task_id = validate_task_id(task_id)
    safe_run_id = _safe_artifact_id(run_id, field_name="run_id")
    state_path = _lane_artifact_dir(root, safe_task_id, safe_run_id) / "lane_state.json"
    if state_path.exists():
        state = _read_json_object(state_path)
    else:
        state = plan_task_worktree_lane(
            root,
            task_id=safe_task_id,
            run_id=safe_run_id,
            repo_root=repo_root,
            expected_base_branch=expected_base_branch,
            expected_base_head=expected_base_head,
            lane_root=lane_root,
            task_category=task_category,
        )

    worktree_path = Path(str(state.get("worktree_path") or ""))
    state["worktree_path_exists"] = worktree_path.exists()
    if worktree_path.exists():
        state["worktree_git_state"] = inspect_git_state(str(worktree_path))
    state["branch_head"] = _branch_head(Path(str(state.get("repo", {}).get("root") or repo_root)), str(state.get("branch") or ""))
    if state.get("status") == "ready" and not state["worktree_path_exists"]:
        state["status"] = "blocked"
        state["ready"] = False
        state["execution_allowed"] = False
        state["blocker_reason"] = "lane state says ready but worktree path is missing"
        state["blockers"] = [*list(state.get("blockers", [])), state["blocker_reason"]]
    return state


def abort_task_worktree_lane(
    queue_root: str | Path,
    *,
    task_id: str,
    run_id: str,
    reason: str,
    repo_root: str | Path = ".",
    expected_base_branch: str = "master",
    expected_base_head: str = "",
    lane_root: str | Path | None = None,
    task_category: str = "",
) -> dict[str, Any]:
    state = inspect_task_worktree_lane(
        queue_root,
        task_id=task_id,
        run_id=run_id,
        repo_root=repo_root,
        expected_base_branch=expected_base_branch,
        expected_base_head=expected_base_head,
        lane_root=lane_root,
        task_category=task_category,
    )
    abort_reason = str(reason or "").strip() or str(state.get("blocker_reason") or "operator aborted unsafe lane execution")
    state["status"] = "aborted"
    state["ready"] = False
    state["execution_allowed"] = False
    state["abort_reason"] = abort_reason
    state["blocker_reason"] = abort_reason
    state["blockers"] = [*list(state.get("blockers", [])), abort_reason]
    state["worktree_removed"] = False
    state["branch_removed"] = False
    return state


def write_lane_state_artifacts(queue_root: str | Path, state: dict[str, Any]) -> dict[str, Any]:
    root = ensure_queue_directories(queue_root)
    artifact_dir = Path(str(state["artifact_dir"]))
    state_path = artifact_dir / "lane_state.json"
    md_path = artifact_dir / "lane_state.md"
    latest_json_path = safe_queue_path(root, "reports", "latest_worktree_lane_state.json")
    latest_md_path = safe_queue_path(root, "reports", "latest_worktree_lane_state.md")
    report_paths = {
        "lane_state_json": str(state_path),
        "lane_state_md": str(md_path),
        "latest_worktree_lane_state_json": str(latest_json_path),
        "latest_worktree_lane_state_md": str(latest_md_path),
    }
    payload = {**state, "report_paths": report_paths}
    write_json_atomic(state_path, payload)
    write_text_atomic(md_path, render_lane_state_markdown(payload))
    write_json_atomic(latest_json_path, payload)
    write_text_atomic(latest_md_path, render_lane_state_markdown(payload))
    return payload


def render_lane_state_markdown(state: dict[str, Any]) -> str:
    repo = state.get("repo", {}) if isinstance(state.get("repo"), dict) else {}
    lines = [
        f"# Worktree Lane: {state.get('task_id', '')}",
        "",
        f"- schema_version: `{state.get('schema_version', '')}`",
        f"- run_id: `{state.get('run_id', '')}`",
        f"- status: `{state.get('status', '')}`",
        f"- ready: `{state.get('ready', False)}`",
        f"- execution_allowed: `{state.get('execution_allowed', False)}`",
        f"- blocker_reason: `{state.get('blocker_reason') or 'none'}`",
        f"- repo_root: `{repo.get('root', '')}`",
        f"- expected_base_branch: `{repo.get('expected_base_branch', '')}`",
        f"- expected_base_head: `{repo.get('expected_base_head', '')}`",
        f"- current_branch: `{repo.get('current_branch', '')}`",
        f"- current_head: `{repo.get('current_head', '')}`",
        f"- branch: `{state.get('branch', '')}`",
        f"- worktree_path: `{state.get('worktree_path', '')}`",
        f"- selected_subagent_profile: `{state.get('selected_subagent_profile', '')}`",
        f"- worktree_created: `{state.get('worktree_created', False)}`",
        "",
        "## Blockers",
        "",
    ]
    blockers = list(state.get("blockers", []))
    lines.extend(f"- {blocker}" for blocker in blockers) if blockers else lines.append("- None")
    lines.extend(["", "## Warnings", ""])
    warnings = list(state.get("warnings", []))
    lines.extend(f"- {warning}" for warning in warnings) if warnings else lines.append("- None")
    lines.extend(
        [
            "",
            "## Safety",
            "",
            "This lane artifact is local-only and supervised. It does not execute Codex, call external services, use browser automation, access credentials, touch wallets/signing, place orders, create a daemon, register a scheduler, or start a background worker.",
            "",
        ]
    )
    return "\n".join(lines)


def _lane_preflight_blockers(
    *,
    repo: Path,
    queue_root: Path,
    git_state: dict[str, Any],
    expected_base_branch: str,
    expected_base_head: str,
    branch: str,
    worktree_path: Path,
    task_category: str,
) -> tuple[list[str], list[str]]:
    blockers: list[str] = []
    warnings: list[str] = [str(value) for value in git_state.get("warnings", [])]
    blockers.extend(str(value) for value in git_state.get("errors", []))

    current_branch = str(git_state.get("branch") or "")
    current_head = str(git_state.get("head") or "")
    if expected_base_branch and current_branch != expected_base_branch:
        blockers.append(f"current branch {current_branch or '<unknown>'} does not match expected base branch {expected_base_branch}")
    if expected_base_head and current_head != expected_base_head:
        blockers.append(f"current head {current_head or '<unknown>'} does not match expected base head {expected_base_head}")

    status_lines = list(git_state.get("status_lines", []))
    unrelated = _unrelated_status_lines(status_lines, _allowed_dirty_roots_for_category(task_category))
    if unrelated:
        if task_category == CATEGORY_CODEX_AUTOMATION and any(_status_path(line).startswith("pm_bot/") for line in unrelated):
            blockers.append("unrelated PMBOT changes are present and cannot be mixed into a Codex automation lane")
        else:
            blockers.append("unrelated changes are present in the current worktree")
    elif status_lines:
        blockers.append("current worktree has uncommitted or untracked changes")

    branch_validation = validate_branch_name(branch)
    if not branch_validation["valid"]:
        blockers.extend(branch_validation["errors"])
    warnings.extend(branch_validation["warnings"])

    repo_root = Path(str(git_state.get("repo_root") or repo)).resolve(strict=False)
    blockers.extend(_validate_lane_path(worktree_path, repo_root=repo_root, queue_root=queue_root))
    if worktree_path.exists():
        blockers.append(f"worktree path already exists: {worktree_path}")
    branch_head = _branch_head(repo_root, branch)
    if branch_head:
        blockers.append(f"branch already exists: {branch}")
    return blockers, warnings


def _allowed_dirty_roots_for_category(task_category: str) -> tuple[str, ...]:
    if task_category == CATEGORY_CODEX_AUTOMATION:
        return (
            "AGENTS.md",
            ".codex-agent/",
            "agent_tasks/",
            "ai_orchestrator/",
            "docs/",
            "memory-bank/",
            "tests/",
        )
    if task_category == "docs_maintenance":
        return ("AGENTS.md", "agent_tasks/", "docs/", "memory-bank/", "tests/")
    if task_category == "safety_review":
        return ("AGENTS.md", "agent_tasks/", "ai_orchestrator/", "docs/", "pm_bot/", "tests/")
    return ("AGENTS.md", "agent_tasks/", "docs/", "pm_bot/", "tests/")


def _unrelated_status_lines(status_lines: list[str], allowed_roots: tuple[str, ...]) -> list[str]:
    unrelated: list[str] = []
    for line in status_lines:
        path = _status_path(line)
        if path and not _path_is_allowed(path, allowed_roots):
            unrelated.append(line)
    return unrelated


def _status_path(line: str) -> str:
    value = str(line)
    if len(value) <= 3:
        return ""
    path = value[3:].strip().strip('"').replace("\\", "/")
    if " -> " in path:
        path = path.split(" -> ", 1)[1].strip().strip('"').replace("\\", "/")
    return path


def _path_is_allowed(path: str, allowed_roots: tuple[str, ...]) -> bool:
    normalized = path.replace("\\", "/")
    for root in allowed_roots:
        allowed = root.replace("\\", "/")
        if allowed.endswith("/"):
            if normalized.startswith(allowed):
                return True
        elif normalized == allowed:
            return True
    return False


def _validate_lane_path(worktree_path: Path, *, repo_root: Path, queue_root: Path) -> list[str]:
    errors: list[str] = []
    resolved_worktree = worktree_path.resolve(strict=False)
    resolved_repo = repo_root.resolve(strict=False)
    resolved_queue = queue_root.resolve(strict=False)
    git_dir = (resolved_repo / ".git").resolve(strict=False)
    if _is_relative_to(resolved_worktree, git_dir):
        errors.append("worktree path points inside .git")
    if _is_relative_to(resolved_worktree, resolved_queue):
        errors.append("worktree path points inside agent_tasks")
    if _is_relative_to(resolved_worktree, resolved_repo):
        errors.append("worktree path must be outside the repository root")
    return errors


def _lane_artifact_dir(queue_root: Path, task_id: str, run_id: str) -> Path:
    return safe_queue_path(
        queue_root,
        "generated",
        "worktree_lanes",
        _short_artifact_segment(run_id, max_length=40),
        _short_artifact_segment(task_id, max_length=48),
    )


def _short_artifact_segment(value: str, *, max_length: int) -> str:
    safe = "".join(ch if ch.isalnum() else "-" for ch in str(value).lower())
    while "--" in safe:
        safe = safe.replace("--", "-")
    safe = safe.strip("-") or "lane"
    if len(safe) <= max_length:
        return safe
    digest = hashlib.sha1(safe.encode("utf-8")).hexdigest()[:10]
    return f"{safe[: max_length - 11].rstrip('-')}-{digest}"


def _lane_worktree_path(repo: Path, task_id: str, run_id: str, lane_root: str | Path | None) -> Path:
    root = Path(lane_root).resolve(strict=False) if lane_root else _default_lane_root(repo)
    return (root / _lane_slug(task_id, run_id)).resolve(strict=False)


def _default_lane_root(repo: Path) -> Path:
    if repo.anchor and ":" in repo.anchor:
        return Path(repo.anchor) / "openclaw-lanes"
    return (repo.parent / "AI-Orchestrator-worktrees").resolve(strict=False)


def _lane_branch_name(task_id: str, run_id: str) -> str:
    slug = _lane_slug(task_id, run_id)
    max_slug_length = BRANCH_MAX_LENGTH - len("codex/")
    if len(slug) > max_slug_length:
        digest = hashlib.sha1(slug.encode("utf-8")).hexdigest()[:10]
        slug = f"{slug[: max_slug_length - 11].rstrip('-')}-{digest}"
    return f"codex/{slug}"


def _lane_slug(task_id: str, run_id: str) -> str:
    value = f"{task_id}-{run_id}".lower()
    safe = "".join(ch if ch.isalnum() else "-" for ch in value)
    while "--" in safe:
        safe = safe.replace("--", "-")
    return safe.strip("-") or "lane"


def _safe_artifact_id(value: str, *, field_name: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"{field_name} must be non-empty")
    safe = "".join(ch if ch.isalnum() or ch in "._-" else "-" for ch in text)
    safe = safe.strip(".-_")
    if not safe:
        raise ValueError(f"{field_name} must contain at least one safe character")
    return safe


def _lane_safety_payload(task_category: str) -> dict[str, Any]:
    return {
        "task_category": task_category,
        "codex_invoked": False,
        "external_api_calls_performed": 0,
        "browser_automation_used": False,
        "authenticated_endpoints_used": False,
        "wallet_or_private_key_accessed": False,
        "orders_or_trading_actions": False,
        "live_trading_permission": False,
        "daemon_created": False,
        "scheduler_created": False,
        "background_worker_created": False,
    }


def _branch_head(repo_root: Path, branch: str) -> str:
    if not branch:
        return ""
    result = _run_git(["rev-parse", "--verify", f"refs/heads/{branch}"], repo_root)
    return result["stdout"].strip() if result["returncode"] == 0 else ""


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
        return {"returncode": 1, "stdout": "", "stderr": str(exc)}
    return {
        "returncode": completed.returncode,
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
    }


def _read_json_object(path: Path) -> dict[str, Any]:
    import json

    payload = json.loads(path.read_text(encoding="utf-8"))
    return dict(payload) if isinstance(payload, dict) else {}


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True
