from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Mapping

from .safety import classify_packet
from .validator import validate_packet


def create_plan(packet: Mapping[str, Any], queue_root: str | Path = "agent_tasks") -> dict[str, Any]:
    validation = validate_packet(packet)
    classification = classify_packet(packet, validation)
    if not classification.allowed:
        raise ValueError(f"packet is not allowed for dry-run planning: {classification.status}")

    task_id = str(packet["task_id"])
    repo = packet["repo"]
    mapping = packet["symphony_mapping"]
    queue_root = Path(queue_root)
    suggested_workspace_name = _sanitize_name(
        str(mapping.get("workspace_key") or f"workspace-{task_id.lower()}")
    )
    target_branch = repo.get("target_branch")
    suggested_branch_name = target_branch or f"codex/{_sanitize_name(task_id.lower())}"
    handoff_prompt_path = queue_root / "planned" / f"{task_id}.handoff_prompt.md"
    workspace_plan_path = queue_root / "planned" / f"{task_id}.workspace_plan.json"

    return {
        "task_id": task_id,
        "would_create_workspace": True,
        "suggested_workspace_name": suggested_workspace_name,
        "suggested_branch_name": suggested_branch_name,
        "allowed_paths": list(repo.get("allowed_paths", [])),
        "forbidden_paths": list(repo.get("forbidden_paths", [])),
        "acceptance_checks": list(packet.get("acceptance_checks", [])),
        "expected_outputs": list(packet.get("expected_outputs", [])),
        "human_review_required": mapping.get("human_review_required") is True,
        "proof_of_work_required": mapping.get("proof_of_work_required") is True,
        "codex_execution_command": None,
        "codex_app_server_used": False,
        "automatic_execution_enabled": False,
        "handoff_prompt_path": str(handoff_prompt_path),
        "workspace_plan_path": str(workspace_plan_path),
    }


def render_handoff_prompt(packet: Mapping[str, Any], plan: Mapping[str, Any]) -> str:
    workspace_plan = _load_workspace_plan_if_present(packet, plan)
    result_shape = {
        "task_id": packet["task_id"],
        "status": "completed|partial|blocked",
        "summary": "",
        "files_changed": [],
        "validation_commands_run": [],
        "tests_passed": False,
        "safety_notes": [],
        "remaining_risks": [],
    }

    sections = [
        f"# Codex Local Handoff: {packet['task_id']}",
        "",
        "## Task",
        "",
        f"- task_id: `{packet['task_id']}`",
        f"- title: {packet['title']}",
        "",
    ]
    if workspace_plan:
        sections.extend(
            [
                "## Workspace Plan Context",
                "",
                f"- suggested_branch_name: `{workspace_plan.get('suggested_branch_name', '')}`",
                f"- suggested_worktree_path: `{workspace_plan.get('suggested_worktree_path', '')}`",
                f"- branch_created: `{workspace_plan.get('branch_created', False)}`",
                f"- worktree_created: `{workspace_plan.get('worktree_created', False)}`",
                "",
                "Branch/worktree creation is still manual unless the operator approves it separately.",
                "Codex must not work outside allowed paths.",
                "",
                "### Workspace Allowed Paths",
                "",
                *_bullet_lines(workspace_plan.get("allowed_paths", []), empty_value="- None specified"),
                "",
                "### Workspace Forbidden Paths",
                "",
                *_bullet_lines(workspace_plan.get("forbidden_paths", []), empty_value="- None specified"),
                "",
            ]
        )
    sections.extend(
        [
            "## Summary",
            "",
            str(packet["summary"]),
            "",
            "## Instructions",
            "",
            *_bullet_lines(packet.get("instructions", [])),
            "",
            "## Allowed Paths",
            "",
            *_bullet_lines(plan.get("allowed_paths", []), empty_value="- None specified"),
            "",
            "## Forbidden Paths",
            "",
            *_bullet_lines(plan.get("forbidden_paths", []), empty_value="- None specified"),
            "",
            "## Safety Boundaries",
            "",
            *_bullet_lines(packet.get("safety_boundaries", [])),
            "",
            "## Acceptance Checks",
            "",
            *_bullet_lines(plan.get("acceptance_checks", []), empty_value="- None specified"),
            "",
            "## Required Result JSON Shape",
            "",
            "```json",
            _json_like(result_shape),
            "```",
            "",
            "## Explicit Safety Statement",
            "",
            "Work only on this task. Do not use network unless explicitly allowed; this MVP does not allow network use. Do not touch credentials, wallet, trading, payment, runtime, dispatcher, run_codex, or Codex app-server code. Do not start background processes, daemons, workers, schedulers, or task scheduler jobs. Return the result JSON and a concise summary for human review.",
        ]
    )
    return "\n".join(sections).rstrip() + "\n"


def _sanitize_name(value: str) -> str:
    sanitized = re.sub(r"[^A-Za-z0-9._-]+", "-", value.strip())
    sanitized = sanitized.strip(".-_")
    return sanitized or "codex-task"


def _bullet_lines(values: Any, *, empty_value: str | None = None) -> list[str]:
    if not values:
        return [empty_value or "- None"]
    return [f"- {value}" for value in values]


def _json_like(value: Mapping[str, Any]) -> str:
    return json.dumps(value, indent=2, sort_keys=False)


def _load_workspace_plan_if_present(packet: Mapping[str, Any], plan: Mapping[str, Any]) -> dict[str, Any] | None:
    workspace_plan_path = plan.get("workspace_plan_path")
    if workspace_plan_path:
        candidate = Path(str(workspace_plan_path))
    else:
        handoff_prompt_path = plan.get("handoff_prompt_path")
        if not handoff_prompt_path:
            return None
        candidate = Path(str(handoff_prompt_path)).with_name(f"{packet['task_id']}.workspace_plan.json")

    if not candidate.exists():
        return None
    try:
        payload = json.loads(candidate.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None
