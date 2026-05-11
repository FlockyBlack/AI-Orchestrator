from __future__ import annotations

import json
import subprocess
from pathlib import Path

from ai_orchestrator.codex_queue.nightly_lane_batch_runner import (
    NIGHTLY_LANE_BATCH_PLAN_SCHEMA_VERSION,
    run_nightly_lane_batch,
    validate_nightly_lane_batch_plan,
)


SAFETY_FLAGS = {
    "no_scheduler": True,
    "no_daemon": True,
    "no_background_worker": True,
    "no_autonomous_trading": True,
    "no_wallet_signing_or_orders": True,
    "no_external_apis": True,
    "no_browser_automation": True,
}


def test_nightly_lane_batch_plan_validation_requires_safety_flags() -> None:
    validation = validate_nightly_lane_batch_plan(
        {
            "schema_version": NIGHTLY_LANE_BATCH_PLAN_SCHEMA_VERSION,
            "batch_id": "NIGHTLY-VALIDATION",
            "expected_base_head": "abc1234",
            "lane_mode": "create_or_reuse",
            "max_steps_per_task": 1,
            "executor_mode": "fake",
            "stop_policy": "stop_on_first_blocker",
            "allow_real_codex_invocation": False,
            "tasks": [{"task_id": "ORCH-NIGHTLY-001"}],
        }
    )

    assert validation["valid"] is False
    assert any("safety_flags" in error for error in validation["errors"])


def test_nightly_lane_batch_dry_run_is_fake_and_does_not_create_lane(tmp_path: Path) -> None:
    repo, head = _init_git_repo(tmp_path)
    queue_root = tmp_path / "agent_tasks"
    plan_path = _write_plan(
        tmp_path,
        repo=repo,
        queue_root=queue_root,
        head=head,
        lane_root=tmp_path / "lanes",
        lane_mode="create_or_reuse",
        task_id="ORCH-NIGHTLY-DRY-RUN",
    )

    report = run_nightly_lane_batch(plan_path, queue_root=queue_root, dry_run=True)

    assert report["status"] == "dry_run"
    assert report["executor_mode"] == "fake"
    assert report["lane_mode"] == "plan_only"
    assert report["tasks"][0]["status"] == "completed"
    assert report["tasks"][0]["worktree_created"] is False
    assert report["codex_invocation_count"] == 0
    assert Path(report["report_paths"]["latest_nightly_lane_batch_report_json"]).exists()
    assert Path(report["report_paths"]["latest_nightly_lane_batch_report_md"]).exists()


def test_first_nightly_lane_batch_dry_run_fixture_routes_three_safe_tasks(tmp_path: Path) -> None:
    repo, head = _init_git_repo(tmp_path)
    queue_root = tmp_path / "agent_tasks"
    lane_root = tmp_path / "nightly-lanes"
    plan_path = tmp_path / "first_nightly_lane_batch_plan.json"
    plan = {
        "schema_version": NIGHTLY_LANE_BATCH_PLAN_SCHEMA_VERSION,
        "batch_id": "first-nightly-lane-batch-dry-run-031",
        "repo_root": str(repo),
        "queue_root": str(queue_root),
        "expected_base_branch": "master",
        "expected_base_head": head,
        "lane_root": str(lane_root),
        "lane_mode": "create_or_reuse",
        "max_steps_per_task": 1,
        "executor_mode": "fake",
        "stop_policy": "stop_on_first_blocker",
        "allow_real_codex_invocation": False,
        "safety_flags": dict(SAFETY_FLAGS),
        "tasks": [
            {
                "task_id": "ORCH-CODEX-AUTOMATION-031-AUTOMATION-SAFE-DRY-RUN",
                "task_category": "codex_automation",
                "allowed_paths": ["ai_orchestrator/codex_queue/", "tests/", "agent_tasks/reports/"],
                "executor_mode": "fake",
                "max_steps": 1,
            },
            {
                "task_id": "PMBOT-PAPERLIVE-031-LIVE-PREP-PLACEHOLDER",
                "task_category": "pmbot_paper_product",
                "allowed_paths": ["docs/", "agent_tasks/reports/", "pm_bot/readiness/"],
                "executor_mode": "fake",
                "max_steps": 1,
            },
            {
                "task_id": "PMBOT-SAFETY-031-NIGHTLY-BATCH-REPORTING-PLACEHOLDER",
                "task_category": "safety_review",
                "allowed_paths": ["docs/", "agent_tasks/reports/", "tests/"],
                "executor_mode": "fake",
                "max_steps": 1,
            },
        ],
    }
    plan_path.write_text(json.dumps(plan), encoding="utf-8")

    report = run_nightly_lane_batch(plan_path, queue_root=queue_root, dry_run=True)
    latest_md = Path(report["report_paths"]["latest_nightly_lane_batch_report_md"]).read_text(encoding="utf-8")

    assert report["schema_version"] == "nightly_lane_batch_report.v1"
    assert report["status"] == "dry_run"
    assert report["execution_status"] == "dry_run"
    assert report["dry_run"] is True
    assert report["executor_mode"] == "fake"
    assert report["lane_mode"] == "plan_only"
    assert report["planned_task_count"] == 3
    assert report["task_count"] == 3
    assert report["completed_count"] == 3
    assert report["blocked_count"] == 0
    assert report["failed_count"] == 0
    assert report["codex_invocation_count"] == 0
    assert {task["selected_subagent"] for task in report["tasks"]} == {"Builder", "Reviewer"}
    assert [task["subagent_route"]["category"] for task in report["tasks"]] == [
        "codex_automation",
        "pmbot_paper_product",
        "safety_review",
    ]
    for task in report["tasks"]:
        assert task["status"] == "completed"
        assert task["executor_mode"] == "fake"
        assert task["codex_invoked"] is False
        assert task["worktree_created"] is False
        assert task["branch_created"] is False
        assert task["branch"].startswith("codex/")
        assert str(lane_root) in task["lane_path"]
        assert Path(task["lane_path"]).exists() is False
        assert task["subagent_route"]["live_trading_permission"] is False
        assert task["safety_flags"]["external_api_calls_performed"] == 0
        assert task["safety_flags"]["wallet_or_private_key_accessed"] is False
        assert task["safety_flags"]["orders_or_trading_actions"] is False
        assert task["safety_flags"]["daemon_created"] is False
        assert task["safety_flags"]["scheduler_created"] is False
        assert task["safety_flags"]["background_worker_created"] is False
        assert task["next_action"]
    assert report["safety_summary"]["real_codex_invocation_allowed_by_plan"] is False
    assert report["safety_summary"]["real_codex_invocation_operator_flag"] is False
    assert report["safety_summary"]["wallet_or_order_code_added"] is False
    assert report["safety_summary"]["orders_or_trading_actions"] is False
    assert "safety_flags:" in latest_md
    assert "wallet_or_private_key_accessed=False" in latest_md


def test_nightly_lane_batch_creates_and_reuses_worktree_lane(tmp_path: Path) -> None:
    repo, head = _init_git_repo(tmp_path)
    queue_root = tmp_path / "agent_tasks"
    plan_path = _write_plan(
        tmp_path,
        repo=repo,
        queue_root=queue_root,
        head=head,
        lane_root=tmp_path / "lanes",
        lane_mode="create_or_reuse",
        task_id="ORCH-NIGHTLY-LANE",
    )

    first = run_nightly_lane_batch(plan_path, queue_root=queue_root)
    second = run_nightly_lane_batch(plan_path, queue_root=queue_root)

    assert first["status"] == "completed"
    assert first["tasks"][0]["worktree_created"] is True
    assert Path(first["tasks"][0]["lane_path"]).exists()
    assert second["status"] == "completed"
    assert second["tasks"][0]["lane_reused"] is True
    assert second["tasks"][0]["worktree_created"] is False


def test_nightly_lane_batch_routes_subagent_profile(tmp_path: Path) -> None:
    repo, head = _init_git_repo(tmp_path)
    queue_root = tmp_path / "agent_tasks"
    plan_path = _write_plan(
        tmp_path,
        repo=repo,
        queue_root=queue_root,
        head=head,
        lane_root=tmp_path / "lanes",
        lane_mode="plan_only",
        task_id="ORCH-NIGHTLY-DOCS",
        task_category="docs_maintenance",
    )

    report = run_nightly_lane_batch(plan_path, queue_root=queue_root)

    assert report["status"] == "completed"
    assert report["tasks"][0]["selected_subagent"] == "Docs"
    assert report["tasks"][0]["subagent_route"]["category"] == "docs_maintenance"


def test_nightly_lane_batch_blocks_dirty_and_wrong_branch(tmp_path: Path) -> None:
    repo, head = _init_git_repo(tmp_path)
    queue_root = tmp_path / "agent_tasks"
    plan_path = _write_plan(
        tmp_path,
        repo=repo,
        queue_root=queue_root,
        head=head,
        lane_root=tmp_path / "lanes",
        lane_mode="create_or_reuse",
        task_id="ORCH-NIGHTLY-BLOCK",
    )
    (repo / "docs" / "base.md").write_text("dirty\n", encoding="utf-8")

    dirty = run_nightly_lane_batch(plan_path, queue_root=queue_root)
    _git(repo, "checkout", "--", "docs/base.md")
    _git(repo, "checkout", "-b", "feature/not-master")
    wrong_branch = run_nightly_lane_batch(plan_path, queue_root=queue_root)

    assert dirty["status"] == "blocked"
    assert any("uncommitted or untracked" in error for error in dirty["errors"])
    assert wrong_branch["status"] == "blocked"
    assert any("does not match expected base branch" in error for error in wrong_branch["errors"])


def test_nightly_lane_batch_real_codex_requires_plan_and_operator_flag(tmp_path: Path) -> None:
    repo, head = _init_git_repo(tmp_path)
    queue_root = tmp_path / "agent_tasks"
    plan_path = _write_plan(
        tmp_path,
        repo=repo,
        queue_root=queue_root,
        head=head,
        lane_root=tmp_path / "lanes",
        lane_mode="plan_only",
        executor_mode="codex_cli",
        allow_real_codex_invocation=False,
        task_id="ORCH-NIGHTLY-REAL-GATE",
    )

    blocked_by_plan = run_nightly_lane_batch(plan_path, queue_root=queue_root)
    plan_path_allowed = _write_plan(
        tmp_path,
        repo=repo,
        queue_root=queue_root,
        head=head,
        lane_root=tmp_path / "lanes",
        lane_mode="plan_only",
        executor_mode="codex_cli",
        allow_real_codex_invocation=True,
        task_id="ORCH-NIGHTLY-REAL-GATE",
    )
    blocked_by_flag = run_nightly_lane_batch(plan_path_allowed, queue_root=queue_root)

    assert blocked_by_plan["status"] == "blocked"
    assert "allow_real_codex_invocation" in blocked_by_plan["tasks"][0]["blocker_reason"]
    assert blocked_by_flag["status"] == "blocked"
    assert "--allow-real-codex-invocation" in blocked_by_flag["tasks"][0]["blocker_reason"]
    assert blocked_by_plan["codex_invocation_count"] == 0
    assert blocked_by_flag["codex_invocation_count"] == 0


def test_nightly_lane_batch_report_safety_flags_are_closed(tmp_path: Path) -> None:
    repo, head = _init_git_repo(tmp_path)
    queue_root = tmp_path / "agent_tasks"
    plan_path = _write_plan(
        tmp_path,
        repo=repo,
        queue_root=queue_root,
        head=head,
        lane_root=tmp_path / "lanes",
        lane_mode="plan_only",
        task_id="ORCH-NIGHTLY-SAFETY",
    )

    report = run_nightly_lane_batch(plan_path, queue_root=queue_root)
    safety = report["safety_summary"]

    assert safety["no_daemon_or_scheduler_added"] is True
    assert safety["no_background_worker_added"] is True
    assert safety["wallet_or_order_code_added"] is False
    assert safety["external_api_calls_performed"] == 0
    assert safety["wallet_or_private_key_access"] is False
    assert safety["orders_or_trading_actions"] is False


def test_nightly_lane_batch_source_has_no_worker_or_order_execution_code() -> None:
    source = (Path(__file__).resolve().parents[1] / "ai_orchestrator" / "codex_queue" / "nightly_lane_batch_runner.py").read_text(
        encoding="utf-8"
    )

    forbidden_snippets = (
        "threading.Thread",
        "subprocess.Popen",
        "daemon=True",
        "schedule.every",
        "place_order(",
        "sign_transaction(",
        "wallet.sign",
    )
    assert all(snippet not in source for snippet in forbidden_snippets)


def _write_plan(
    tmp_path: Path,
    *,
    repo: Path,
    queue_root: Path,
    head: str,
    lane_root: Path,
    lane_mode: str,
    task_id: str,
    task_category: str = "codex_automation",
    executor_mode: str = "fake",
    allow_real_codex_invocation: bool = False,
) -> Path:
    plan = {
        "schema_version": NIGHTLY_LANE_BATCH_PLAN_SCHEMA_VERSION,
        "batch_id": "NIGHTLY-TEST",
        "repo_root": str(repo),
        "queue_root": str(queue_root),
        "expected_base_branch": "master",
        "expected_base_head": head,
        "lane_root": str(lane_root),
        "lane_mode": lane_mode,
        "max_steps_per_task": 1,
        "executor_mode": executor_mode,
        "stop_policy": "stop_on_first_blocker",
        "allow_real_codex_invocation": allow_real_codex_invocation,
        "safety_flags": dict(SAFETY_FLAGS),
        "tasks": [{"task_id": task_id, "task_category": task_category}],
    }
    path = tmp_path / "nightly_lane_batch_plan.json"
    path.write_text(json.dumps(plan), encoding="utf-8")
    return path


def _init_git_repo(tmp_path: Path) -> tuple[Path, str]:
    repo = tmp_path / "repo"
    repo.mkdir()
    init = subprocess.run(["git", "init", "--initial-branch", "master"], cwd=repo, check=False, capture_output=True, text=True)
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
    _write(repo / "docs" / "base.md", "base\n")
    _write(repo / "tests" / "keep.py", "# keep\n")
    _git(repo, "add", "AGENTS.md", "agent_tasks/agents/builder_agent.md", "agent_tasks/agents/docs_agent.md")
    _git(repo, "add", "agent_tasks/agents/reviewer_agent.md", "ai_orchestrator/codex_queue/keep.py", "docs/base.md", "tests/keep.py")
    _git(repo, "commit", "-m", "base")
    return repo, _git(repo, "rev-parse", "HEAD").stdout.strip()


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True)
