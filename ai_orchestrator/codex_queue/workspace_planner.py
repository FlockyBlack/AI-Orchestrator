from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from .files import ensure_queue_directories, find_task_packet, safe_queue_path, validate_task_id
from .git_safety import build_safe_branch_name, inspect_git_state, validate_branch_name
from .safety import classify_packet
from .validator import validate_packet

WORKSPACE_PLAN_SCHEMA_VERSION = "codex_workspace_plan.v1"


def plan_workspace_for_task(
    queue_root: str | Path,
    task_id: str,
    repo_root: str | Path = ".",
) -> dict[str, Any]:
    root = ensure_queue_directories(queue_root)
    safe_task_id = validate_task_id(task_id)
    plan = _base_plan(root, safe_task_id)

    match = find_task_packet(root, safe_task_id, states=("approved", "planned"))
    if not match["found"]:
        plan["errors"].append(f"no approved/planned task packet found for task_id: {safe_task_id}")
        plan["next_operator_action"] = "Approve or plan a valid local-only task before workspace planning."
        return plan

    packet = dict(match["packet"])
    validation = validate_packet(packet)
    classification = _classify_for_workspace(packet, validation)

    plan["task_packet_path"] = str(match["path"])
    plan["task_packet_state"] = str(match["state"])
    plan["task_validation"] = validation.to_dict()
    plan["safety_classification"] = classification.to_dict()
    plan["allowed_paths"] = list(packet.get("repo", {}).get("allowed_paths", []))
    plan["forbidden_paths"] = list(packet.get("repo", {}).get("forbidden_paths", []))
    plan["acceptance_checks"] = list(packet.get("acceptance_checks", []))
    plan["expected_outputs"] = list(packet.get("expected_outputs", []))
    plan["human_review_required"] = packet.get("symphony_mapping", {}).get("human_review_required") is True
    plan["proof_of_work_required"] = packet.get("symphony_mapping", {}).get("proof_of_work_required") is True

    if not validation.valid:
        plan["errors"].extend(validation.errors)
    if not classification.allowed:
        plan["errors"].extend(classification.reasons)

    git_state = inspect_git_state(str(repo_root))
    plan["git_state"] = git_state
    plan["repo_root"] = git_state.get("repo_root") or str(Path(repo_root).resolve(strict=False))
    plan["base_branch"] = git_state.get("branch") or str(packet.get("repo", {}).get("base_branch", ""))
    plan["base_head"] = git_state.get("head", "")
    plan["warnings"].extend(git_state.get("warnings", []))
    plan["errors"].extend(git_state.get("errors", []))

    if not git_state.get("branch"):
        plan["errors"].append("git branch could not be resolved; detached or invalid repository state")
    if not git_state.get("head"):
        plan["errors"].append("git HEAD could not be resolved")

    packet_repo_root = str(packet.get("repo", {}).get("repo_root", "")).strip()
    if packet_repo_root and packet_repo_root != str(repo_root):
        plan["warnings"].append(
            f"task packet repo.repo_root is {packet_repo_root!r}; workspace plan inspected {str(repo_root)!r}"
        )

    suggested_branch = build_safe_branch_name(safe_task_id)
    branch_validation = validate_branch_name(suggested_branch)
    plan["suggested_branch_name"] = suggested_branch
    plan["branch_name_validation"] = branch_validation
    if not branch_validation["valid"]:
        plan["errors"].extend(branch_validation["errors"])
    plan["warnings"].extend(branch_validation["warnings"])

    suggested_worktree_path = _suggest_worktree_path(plan["repo_root"], safe_task_id)
    plan["suggested_worktree_path"] = str(suggested_worktree_path)
    path_errors = _validate_suggested_worktree_path(
        suggested_worktree_path,
        repo_root=Path(plan["repo_root"]),
        queue_root=root,
    )
    plan["errors"].extend(path_errors)

    plan["would_create_branch"] = not plan["errors"]
    plan["would_create_worktree"] = not plan["errors"]
    plan["status"] = "blocked" if plan["errors"] else "planned"
    plan["next_operator_action"] = (
        "Review the workspace plan. Branch/worktree creation remains manual and separately approved."
        if plan["status"] == "planned"
        else "Resolve blocking errors before creating any branch or worktree."
    )
    return plan


def render_workspace_plan_markdown(plan: Mapping[str, Any]) -> str:
    lines = [
        f"# Workspace Plan: {plan['task_id']}",
        "",
        f"- schema_version: `{plan['schema_version']}`",
        f"- status: `{plan['status']}`",
        f"- repo_root: `{plan['repo_root']}`",
        f"- base_branch: `{plan['base_branch']}`",
        f"- base_head: `{plan['base_head']}`",
        f"- suggested_branch_name: `{plan['suggested_branch_name']}`",
        f"- suggested_worktree_path: `{plan['suggested_worktree_path']}`",
        f"- would_create_branch: `{plan['would_create_branch']}`",
        f"- would_create_worktree: `{plan['would_create_worktree']}`",
        f"- branch_created: `{plan['branch_created']}`",
        f"- worktree_created: `{plan['worktree_created']}`",
        f"- codex_execution_enabled: `{plan['codex_execution_enabled']}`",
        f"- codex_app_server_used: `{plan['codex_app_server_used']}`",
        "",
        "## Allowed Paths",
        "",
        *_bullet_lines(plan.get("allowed_paths", []), empty_value="- None specified"),
        "",
        "## Forbidden Paths",
        "",
        *_bullet_lines(plan.get("forbidden_paths", []), empty_value="- None specified"),
        "",
        "## Acceptance Checks",
        "",
        *_bullet_lines(plan.get("acceptance_checks", []), empty_value="- None specified"),
        "",
        "## Expected Outputs",
        "",
        *_bullet_lines(plan.get("expected_outputs", []), empty_value="- None specified"),
        "",
    ]
    if plan.get("warnings"):
        lines.extend(["## Warnings", ""])
        lines.extend(f"- {warning}" for warning in plan["warnings"])
        lines.append("")
    if plan.get("errors"):
        lines.extend(["## Errors", ""])
        lines.extend(f"- {error}" for error in plan["errors"])
        lines.append("")
    lines.extend(
        [
            "## Manual Gate",
            "",
            "This plan is a local dry-run report only. It did not create a branch, create a worktree, execute Codex, call Codex app-server, run acceptance checks, start workers, add schedulers, or call network services.",
            "",
            f"Next operator action: {plan['next_operator_action']}",
            "",
        ]
    )
    return "\n".join(lines)


def _base_plan(queue_root: Path, task_id: str) -> dict[str, Any]:
    return {
        "schema_version": WORKSPACE_PLAN_SCHEMA_VERSION,
        "task_id": task_id,
        "status": "blocked",
        "repo_root": "",
        "base_branch": "",
        "base_head": "",
        "suggested_branch_name": "",
        "suggested_worktree_path": "",
        "would_create_branch": False,
        "would_create_worktree": False,
        "branch_created": False,
        "worktree_created": False,
        "codex_execution_enabled": False,
        "codex_app_server_used": False,
        "allowed_paths": [],
        "forbidden_paths": [],
        "acceptance_checks": [],
        "expected_outputs": [],
        "human_review_required": True,
        "proof_of_work_required": True,
        "git_state": {},
        "task_packet_path": "",
        "task_packet_state": "",
        "task_validation": None,
        "safety_classification": None,
        "branch_name_validation": None,
        "workspace_plan_path": str(safe_queue_path(queue_root, "planned", f"{task_id}.workspace_plan.json")),
        "errors": [],
        "warnings": [],
        "next_operator_action": "",
    }


def _classify_for_workspace(packet: Mapping[str, Any], validation: Any) -> Any:
    if packet.get("status") != "planned":
        return classify_packet(packet, validation)
    approved_view = dict(packet)
    approved_view["status"] = "approved"
    return classify_packet(approved_view, validation)


def _suggest_worktree_path(repo_root: str | Path, task_id: str) -> Path:
    repo_path = Path(repo_root).resolve(strict=False)
    safe_name = build_safe_branch_name(task_id).split("/", 1)[1]
    return (repo_path.parent / "AI-Orchestrator-worktrees" / safe_name).resolve(strict=False)


def _validate_suggested_worktree_path(
    suggested_path: Path,
    *,
    repo_root: Path,
    queue_root: Path,
) -> list[str]:
    errors: list[str] = []
    resolved_suggestion = suggested_path.resolve(strict=False)
    resolved_repo = repo_root.resolve(strict=False)
    resolved_queue = queue_root.resolve(strict=False)
    git_dir = (resolved_repo / ".git").resolve(strict=False)

    if _is_relative_to(resolved_suggestion, git_dir):
        errors.append("suggested worktree path points inside .git")
    if _is_relative_to(resolved_suggestion, resolved_queue):
        errors.append("suggested worktree path points inside agent_tasks")
    if _is_relative_to(resolved_suggestion, resolved_repo):
        errors.append("suggested worktree path must be outside the repository root")
    return errors


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def _bullet_lines(values: Any, *, empty_value: str | None = None) -> list[str]:
    if not values:
        return [empty_value or "- None"]
    return [f"- {value}" for value in values]
