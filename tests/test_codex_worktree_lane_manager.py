from __future__ import annotations

import json
import subprocess
from pathlib import Path

from ai_orchestrator.codex_queue.operator_cli import main
from ai_orchestrator.codex_queue.plan_contract import PlanContract
from ai_orchestrator.codex_queue.worktree_lane_manager import (
    build_lane_plan,
    create_task_worktree_lane,
    inspect_task_worktree_lane,
    plan_task_worktree_lane,
    render_worktree_commands,
    validate_lane_isolation,
    write_lane_state_artifacts,
)
from codex_plan_helpers import minimal_plan


def test_build_lane_plan_is_dry_run_safe() -> None:
    plan = PlanContract.from_dict(minimal_plan(2))

    lane_plan = build_lane_plan(plan)

    assert lane_plan.lanes[0].dry_run_only is True
    assert lane_plan.lanes[0].task_ids == ("TEST-TASK-001", "TEST-TASK-002")
    assert all("worktree add" in command for command in lane_plan.commands)
    assert not any("--force" in command for command in lane_plan.commands)


def test_validate_lane_isolation_reports_missing_roots() -> None:
    payload = minimal_plan(1)
    payload["execution_lanes"][0]["allowed_roots"] = []
    plan = PlanContract.from_dict(payload)

    lane_plan = build_lane_plan(plan)
    validation = validate_lane_isolation(lane_plan)

    assert validation["warnings"]
    assert render_worktree_commands(lane_plan)


def test_task_lane_plan_maps_task_run_to_branch_path_and_profile(tmp_path: Path) -> None:
    repo, head = _init_git_repo(tmp_path)
    queue_root = tmp_path / "agent_tasks"
    lane_root = tmp_path / "lanes"

    state = plan_task_worktree_lane(
        queue_root,
        task_id="ORCH-CODEX-AUTOMATION-029",
        run_id="R029",
        repo_root=repo,
        expected_base_branch="master",
        expected_base_head=head,
        lane_root=lane_root,
        task_category="codex_automation",
    )

    assert state["status"] == "planned"
    assert state["ready"] is True
    assert state["branch"] == "codex/orch-codex-automation-029-r029"
    assert state["worktree_path"] == str((lane_root / "orch-codex-automation-029-r029").resolve(strict=False))
    assert state["selected_subagent_profile"] == "Builder"
    assert state["subagent_route"]["live_trading_permission"] is False


def test_create_task_worktree_lane_creates_safe_fake_lane(tmp_path: Path) -> None:
    repo, head = _init_git_repo(tmp_path)
    queue_root = tmp_path / "agent_tasks"
    lane_root = tmp_path / "lanes"

    state = create_task_worktree_lane(
        queue_root,
        task_id="ORCH-CODEX-AUTOMATION-029",
        run_id="SAFE",
        repo_root=repo,
        expected_base_branch="master",
        expected_base_head=head,
        lane_root=lane_root,
        task_category="codex_automation",
    )
    state = write_lane_state_artifacts(queue_root, state)
    inspected = inspect_task_worktree_lane(
        queue_root,
        task_id="ORCH-CODEX-AUTOMATION-029",
        run_id="SAFE",
        repo_root=repo,
        expected_base_branch="master",
        expected_base_head=head,
        lane_root=lane_root,
        task_category="codex_automation",
    )

    assert state["status"] == "ready"
    assert state["worktree_created"] is True
    assert Path(state["worktree_path"]).exists()
    assert inspected["worktree_path_exists"] is True
    assert inspected["worktree_git_state"]["head"] == head


def test_dirty_tree_blocks_lane_creation(tmp_path: Path) -> None:
    repo, head = _init_git_repo(tmp_path)
    (repo / "docs" / "base.md").write_text("dirty\n", encoding="utf-8")

    state = create_task_worktree_lane(
        tmp_path / "agent_tasks",
        task_id="ORCH-CODEX-AUTOMATION-029",
        run_id="DIRTY",
        repo_root=repo,
        expected_base_branch="master",
        expected_base_head=head,
        lane_root=tmp_path / "lanes",
        task_category="codex_automation",
    )

    assert state["status"] == "blocked"
    assert state["worktree_created"] is False
    assert any("uncommitted or untracked changes" in blocker for blocker in state["blockers"])


def test_wrong_branch_and_wrong_head_block_lane_creation(tmp_path: Path) -> None:
    repo, head = _init_git_repo(tmp_path)
    _git(repo, "checkout", "-b", "feature/not-base")

    wrong_branch = create_task_worktree_lane(
        tmp_path / "agent_tasks",
        task_id="ORCH-CODEX-AUTOMATION-029",
        run_id="WRONG-BRANCH",
        repo_root=repo,
        expected_base_branch="master",
        expected_base_head=head,
        lane_root=tmp_path / "lanes",
        task_category="codex_automation",
    )
    _git(repo, "checkout", "master")
    wrong_head = create_task_worktree_lane(
        tmp_path / "agent_tasks",
        task_id="ORCH-CODEX-AUTOMATION-029",
        run_id="WRONG-HEAD",
        repo_root=repo,
        expected_base_branch="master",
        expected_base_head="deadbeef",
        lane_root=tmp_path / "lanes",
        task_category="codex_automation",
    )

    assert any("does not match expected base branch" in blocker for blocker in wrong_branch["blockers"])
    assert any("does not match expected base head" in blocker for blocker in wrong_head["blockers"])
    assert wrong_branch["worktree_created"] is False
    assert wrong_head["worktree_created"] is False


def test_pmbot_unrelated_changes_are_not_mixed_into_automation_lane(tmp_path: Path) -> None:
    repo, head = _init_git_repo(tmp_path)
    (repo / "pm_bot" / "paper.py").write_text("changed paper artifact\n", encoding="utf-8")

    state = create_task_worktree_lane(
        tmp_path / "agent_tasks",
        task_id="ORCH-CODEX-AUTOMATION-029",
        run_id="PMBOT-DIRTY",
        repo_root=repo,
        expected_base_branch="master",
        expected_base_head=head,
        lane_root=tmp_path / "lanes",
        task_category="codex_automation",
    )

    assert state["status"] == "blocked"
    assert any("unrelated PMBOT changes" in blocker for blocker in state["blockers"])
    assert state["worktree_created"] is False


def test_operator_cli_worktree_lane_commands_write_json_reports(tmp_path: Path) -> None:
    repo, head = _init_git_repo(tmp_path)
    queue_root = tmp_path / "agent_tasks"
    lane_root = tmp_path / "lanes"

    create_exit = main(
        [
            "worktree-lane-create",
            "--queue-root",
            str(queue_root),
            "--task-id",
            "ORCH-CODEX-AUTOMATION-029",
            "--run-id",
            "CLI",
            "--repo-root",
            str(repo),
            "--expected-base-branch",
            "master",
            "--expected-base-head",
            head,
            "--lane-root",
            str(lane_root),
            "--task-category",
            "codex_automation",
        ]
    )
    status_exit = main(
        [
            "worktree-lane-status",
            "--queue-root",
            str(queue_root),
            "--task-id",
            "ORCH-CODEX-AUTOMATION-029",
            "--run-id",
            "CLI",
            "--repo-root",
            str(repo),
            "--expected-base-branch",
            "master",
            "--expected-base-head",
            head,
            "--lane-root",
            str(lane_root),
            "--task-category",
            "codex_automation",
        ]
    )

    latest = json.loads((queue_root / "reports" / "latest_worktree_lane_state.json").read_text(encoding="utf-8"))
    action = json.loads((queue_root / "reports" / "latest_operator_action.json").read_text(encoding="utf-8"))
    assert create_exit == 0
    assert status_exit == 0
    assert latest["status"] == "ready"
    assert action["command"] == "worktree-lane-status"
    assert action["worktree_lane_ready"] is True


def test_operator_cli_worktree_lane_abort_writes_clear_blocked_json(tmp_path: Path) -> None:
    repo, head = _init_git_repo(tmp_path)
    queue_root = tmp_path / "agent_tasks"

    exit_code = main(
        [
            "worktree-lane-abort",
            "--queue-root",
            str(queue_root),
            "--task-id",
            "ORCH-CODEX-AUTOMATION-029",
            "--run-id",
            "ABORT",
            "--repo-root",
            str(repo),
            "--expected-base-branch",
            "master",
            "--expected-base-head",
            head,
            "--lane-root",
            str(tmp_path / "lanes"),
            "--task-category",
            "codex_automation",
            "--reason",
            "unsafe lane preflight",
        ]
    )

    latest = json.loads((queue_root / "reports" / "latest_worktree_lane_state.json").read_text(encoding="utf-8"))
    action = json.loads((queue_root / "reports" / "latest_operator_action.json").read_text(encoding="utf-8"))
    assert exit_code == 1
    assert latest["status"] == "aborted"
    assert latest["blocker_reason"] == "unsafe lane preflight"
    assert latest["worktree_removed"] is False
    assert latest["branch_removed"] is False
    assert action["command"] == "worktree-lane-abort"
    assert action["status"] == "blocked"


def _init_git_repo(tmp_path: Path) -> tuple[Path, str]:
    repo = tmp_path / "repo"
    repo.mkdir()
    init = subprocess.run(
        ["git", "init", "--initial-branch", "master"],
        cwd=repo,
        check=False,
        capture_output=True,
        text=True,
    )
    if init.returncode != 0:
        _git(repo, "init")
        _git(repo, "checkout", "-B", "master")
    _git(repo, "config", "user.email", "tests@example.invalid")
    _git(repo, "config", "user.name", "Tests")
    _write(repo / "AGENTS.md", "# AGENTS\n")
    _write(repo / "agent_tasks" / "agents" / "builder_agent.md", "# Builder Agent\n")
    _write(repo / "agent_tasks" / "agents" / "docs_agent.md", "# Docs Agent\n")
    _write(repo / "agent_tasks" / "agents" / "reviewer_agent.md", "# Reviewer Agent\n")
    _write(repo / "ai_orchestrator" / "codex_queue" / "keep.py", "# keep\n")
    _write(repo / "pm_bot" / "paper.py", "paper only\n")
    _write(repo / "docs" / "base.md", "base\n")
    _write(repo / "tests" / "keep.py", "# keep\n")
    _git(
        repo,
        "add",
        "AGENTS.md",
        "agent_tasks/agents/builder_agent.md",
        "agent_tasks/agents/docs_agent.md",
        "agent_tasks/agents/reviewer_agent.md",
        "ai_orchestrator/codex_queue/keep.py",
        "pm_bot/paper.py",
        "docs/base.md",
        "tests/keep.py",
    )
    _git(repo, "commit", "-m", "base")
    return repo, _git(repo, "rev-parse", "HEAD").stdout.strip()


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True)
