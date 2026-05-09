from __future__ import annotations

import json
from pathlib import Path

from ai_orchestrator.codex_queue.night_runner import generate_night_dry_run_plan
from ai_orchestrator.codex_queue.schema import default_packet


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _approved_packet(task_id: str) -> dict:
    packet = default_packet()
    packet["task_id"] = task_id
    packet["title"] = f"{task_id} night runner test"
    packet["status"] = "approved"
    packet["created_at"] = "2026-05-09T00:00:00Z"
    packet["approved_by"] = "operator"
    packet["approved_at"] = "2026-05-09T00:00:00Z"
    packet["task_type"] = "local_docs_only"
    packet["priority"] = "low"
    packet["summary"] = "Safe local night dry-run test task."
    packet["instructions"] = ["Create a harmless docs note."]
    packet["repo"]["base_branch"] = "master"
    packet["repo"]["allowed_paths"] = ["docs/"]
    packet["repo"]["forbidden_paths"] = ["runtime/", "dispatcher/", "run_codex/", "pm_bot/"]
    packet["acceptance_checks"] = []
    packet["expected_outputs"] = ["docs/result.md"]
    return packet


def _write_ready_task(queue_root: Path, task_id: str) -> None:
    handoff_path = queue_root / "planned" / f"{task_id}.handoff_prompt.md"
    workspace_plan_path = queue_root / "planned" / f"{task_id}.workspace_plan.json"
    _write_json(queue_root / "approved" / f"{task_id}.task.json", _approved_packet(task_id))
    _write_json(
        queue_root / "planned" / f"{task_id}.plan.json",
        {
            "task_id": task_id,
            "handoff_prompt_path": str(handoff_path),
            "workspace_plan_path": str(workspace_plan_path),
        },
    )
    _write_text(handoff_path, "# Manual handoff\n")
    _write_json(
        workspace_plan_path,
        {
            "task_id": task_id,
            "status": "planned",
            "branch_created": False,
            "worktree_created": False,
            "suggested_branch_name": f"codex/{task_id.lower()}",
            "suggested_worktree_path": str(queue_root.parent / "worktrees" / task_id.lower()),
        },
    )


def _fake_git_state(repo_root: str = ".") -> dict:
    return {
        "repo_root": repo_root,
        "branch": "master",
        "head": "abc123",
        "status_lines": [],
        "is_clean": True,
        "tracked_changes_count": 0,
        "untracked_count": 0,
        "warnings": [],
        "errors": [],
    }


def test_night_dry_run_writes_latest_json_and_markdown(tmp_path: Path, monkeypatch) -> None:
    queue_root = tmp_path / "agent_tasks"
    _write_ready_task(queue_root, "ORCH-NIGHT-READY")
    monkeypatch.setattr("ai_orchestrator.codex_queue.night_runner.inspect_git_state", _fake_git_state)

    report = generate_night_dry_run_plan(queue_root, max_tasks=5)

    assert report["schema_version"] == "codex_night_dry_run_plan.v1"
    assert report["status"] == "ok"
    assert (queue_root / "reports" / "latest_night_dry_run_plan.json").exists()
    assert (queue_root / "reports" / "latest_night_dry_run_plan.md").exists()
    assert Path(report["report_paths"]["timestamped_night_dry_run_plan_json"]).exists()


def test_night_dry_run_safety_flags_are_false(tmp_path: Path, monkeypatch) -> None:
    queue_root = tmp_path / "agent_tasks"
    _write_ready_task(queue_root, "ORCH-NIGHT-SAFE")
    monkeypatch.setattr("ai_orchestrator.codex_queue.night_runner.inspect_git_state", _fake_git_state)

    report = generate_night_dry_run_plan(queue_root)

    assert report["would_execute_codex"] is False
    assert report["would_create_branch"] is False
    assert report["would_create_worktree"] is False
    assert report["would_register_scheduler"] is False
    assert report["codex_app_server_used"] is False
    assert report["task_marked_done_automatically"] is False


def test_night_dry_run_respects_max_tasks(tmp_path: Path, monkeypatch) -> None:
    queue_root = tmp_path / "agent_tasks"
    _write_ready_task(queue_root, "ORCH-NIGHT-CAP-A")
    _write_ready_task(queue_root, "ORCH-NIGHT-CAP-B")
    monkeypatch.setattr("ai_orchestrator.codex_queue.night_runner.inspect_git_state", _fake_git_state)

    report = generate_night_dry_run_plan(queue_root, max_tasks=1)

    assert len(report["eligible_for_manual_handoff"]) == 1
    assert len(report["ordered_next_actions"]) == 1
    assert report["batch_evaluation"]["cap_applied"] is True


def test_lock_check_blocks_when_lock_file_exists(tmp_path: Path, monkeypatch) -> None:
    queue_root = tmp_path / "agent_tasks"
    _write_ready_task(queue_root, "ORCH-NIGHT-LOCKED")
    _write_json(
        queue_root / "running" / "night_runner.lock.json",
        {"created_at": "2026-05-09T00:00:00Z", "owner": "test"},
    )
    monkeypatch.setattr("ai_orchestrator.codex_queue.night_runner.inspect_git_state", _fake_git_state)

    report = generate_night_dry_run_plan(queue_root)
    lock_report = json.loads(
        (queue_root / "reports" / "latest_night_runner_lock_check.json").read_text(encoding="utf-8")
    )

    assert report["status"] == "blocked"
    assert report["lock_check"]["lock_exists"] is True
    assert lock_report["status"] == "blocked"
    assert lock_report["lock_created"] is False
