from __future__ import annotations

import json
from pathlib import Path

from ai_orchestrator.codex_queue.operator_cli import main
from ai_orchestrator.codex_queue.planner import create_plan, render_handoff_prompt
from ai_orchestrator.codex_queue.schema import default_packet
from ai_orchestrator.codex_queue.workspace_planner import plan_workspace_for_task


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _approved_packet(task_id: str) -> dict:
    packet = default_packet()
    packet["task_id"] = task_id
    packet["title"] = f"{task_id} workspace plan test"
    packet["status"] = "approved"
    packet["approved_by"] = "operator"
    packet["approved_at"] = "2026-05-09T00:00:00Z"
    packet["task_type"] = "local_code_tests"
    packet["priority"] = "low"
    packet["summary"] = "Safe local-only workspace planning test task."
    packet["instructions"] = ["Make a safe local code/test change."]
    packet["repo"] = {
        "repo_root": ".",
        "base_branch": "master",
        "target_branch": None,
        "allowed_paths": ["ai_orchestrator/codex_queue/", "tests/"],
        "forbidden_paths": ["runtime/", "dispatcher/", "run_codex/", "pm_bot/"],
    }
    packet["acceptance_checks"] = ["python -m compileall ai_orchestrator tests"]
    packet["expected_outputs"] = ["workspace plan report"]
    packet["risk_flags"] = {key: False for key in packet["risk_flags"]}
    return packet


def _write_task(queue_root: Path, packet: dict) -> None:
    _write_json(queue_root / packet["status"] / f"{packet['task_id']}.task.json", packet)


def _fake_git_state(repo_root: Path) -> dict:
    return {
        "repo_root": str(repo_root),
        "branch": "master",
        "head": "abc123",
        "status_lines": [],
        "is_clean": True,
        "tracked_changes_count": 0,
        "untracked_count": 0,
        "warnings": [],
        "errors": [],
    }


def test_workspace_planner_creates_non_executing_plan_for_safe_approved_task(tmp_path: Path, monkeypatch) -> None:
    queue_root = tmp_path / "agent_tasks"
    repo_root = tmp_path / "repo"
    task_id = "ORCH-WORKSPACE-PLAN-SAFE"
    _write_task(queue_root, _approved_packet(task_id))
    monkeypatch.setattr(
        "ai_orchestrator.codex_queue.workspace_planner.inspect_git_state",
        lambda repo_root_arg: _fake_git_state(repo_root),
    )

    plan = plan_workspace_for_task(queue_root, task_id, repo_root=repo_root)

    assert plan["schema_version"] == "codex_workspace_plan.v1"
    assert plan["status"] == "planned"
    assert plan["suggested_branch_name"] == "codex/orch-workspace-plan-safe"
    assert plan["would_create_branch"] is True
    assert plan["would_create_worktree"] is True
    assert plan["branch_created"] is False
    assert plan["worktree_created"] is False
    assert plan["codex_execution_enabled"] is False
    assert plan["codex_app_server_used"] is False
    assert plan["allowed_paths"] == ["ai_orchestrator/codex_queue/", "tests/"]
    assert not Path(plan["suggested_worktree_path"]).exists()


def test_workspace_planner_blocks_unsafe_task(tmp_path: Path, monkeypatch) -> None:
    queue_root = tmp_path / "agent_tasks"
    repo_root = tmp_path / "repo"
    task_id = "ORCH-WORKSPACE-PLAN-UNSAFE"
    packet = _approved_packet(task_id)
    packet["risk_flags"]["requires_credentials"] = True
    _write_task(queue_root, packet)
    monkeypatch.setattr(
        "ai_orchestrator.codex_queue.workspace_planner.inspect_git_state",
        lambda repo_root_arg: _fake_git_state(repo_root),
    )

    plan = plan_workspace_for_task(queue_root, task_id, repo_root=repo_root)

    assert plan["status"] == "blocked"
    assert plan["branch_created"] is False
    assert plan["worktree_created"] is False
    assert any("hard-block risk flags set" in error for error in plan["errors"])


def test_workspace_planner_blocks_conflicted_git_state(tmp_path: Path, monkeypatch) -> None:
    queue_root = tmp_path / "agent_tasks"
    repo_root = tmp_path / "repo"
    task_id = "ORCH-WORKSPACE-PLAN-CONFLICT"
    _write_task(queue_root, _approved_packet(task_id))
    git_state = _fake_git_state(repo_root)
    git_state["status_lines"] = ["UU ai_orchestrator/example.py"]
    git_state["errors"] = ["merge/rebase conflict indicators detected in git status"]
    monkeypatch.setattr(
        "ai_orchestrator.codex_queue.workspace_planner.inspect_git_state",
        lambda repo_root_arg: git_state,
    )

    plan = plan_workspace_for_task(queue_root, task_id, repo_root=repo_root)

    assert plan["status"] == "blocked"
    assert "merge/rebase conflict indicators detected in git status" in plan["errors"]


def test_operator_cli_workspace_plan_writes_json_and_markdown_reports(tmp_path: Path, monkeypatch) -> None:
    queue_root = tmp_path / "agent_tasks"
    repo_root = tmp_path / "repo"
    task_id = "ORCH-WORKSPACE-PLAN-CLI"
    _write_task(queue_root, _approved_packet(task_id))
    monkeypatch.setattr(
        "ai_orchestrator.codex_queue.workspace_planner.inspect_git_state",
        lambda repo_root_arg: _fake_git_state(repo_root),
    )

    exit_code = main(["workspace-plan", "--queue-root", str(queue_root), "--task-id", task_id])

    assert exit_code == 0
    assert (queue_root / "planned" / f"{task_id}.workspace_plan.json").exists()
    assert (queue_root / "reports" / f"{task_id}.workspace_plan.md").exists()
    assert (queue_root / "reports" / "latest_workspace_plan.json").exists()
    assert (queue_root / "reports" / "latest_workspace_plan.md").exists()
    plan = json.loads((queue_root / "reports" / "latest_workspace_plan.json").read_text(encoding="utf-8"))
    assert plan["branch_created"] is False
    assert plan["worktree_created"] is False
    assert plan["codex_execution_enabled"] is False


def test_handoff_prompt_includes_workspace_plan_info_when_workspace_plan_exists(tmp_path: Path) -> None:
    queue_root = tmp_path / "agent_tasks"
    task_id = "ORCH-WORKSPACE-PLAN-HANDOFF"
    packet = _approved_packet(task_id)
    dry_plan = create_plan(packet, queue_root=queue_root)
    workspace_plan = {
        "suggested_branch_name": "codex/orch-workspace-plan-handoff",
        "suggested_worktree_path": str(tmp_path / "AI-Orchestrator-worktrees" / "orch-workspace-plan-handoff"),
        "branch_created": False,
        "worktree_created": False,
        "allowed_paths": ["ai_orchestrator/codex_queue/", "tests/"],
        "forbidden_paths": ["runtime/", "dispatcher/", "run_codex/"],
    }
    _write_json(Path(dry_plan["workspace_plan_path"]), workspace_plan)

    prompt = render_handoff_prompt(packet, dry_plan)

    assert "## Workspace Plan Context" in prompt
    assert "codex/orch-workspace-plan-handoff" in prompt
    assert "Branch/worktree creation is still manual unless the operator approves it separately." in prompt
    assert "Codex must not work outside allowed paths." in prompt
