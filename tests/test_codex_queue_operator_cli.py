from __future__ import annotations

import json
import socket
import subprocess
from pathlib import Path

from ai_orchestrator.codex_queue.operator_cli import find_allowed_ingestion_report, main
from ai_orchestrator.codex_queue.result_schema import default_result
from ai_orchestrator.codex_queue.schema import default_packet


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _safe_packet(task_id: str, *, status: str = "inbox") -> dict:
    packet = default_packet()
    packet["task_id"] = task_id
    packet["title"] = f"{task_id} test packet"
    packet["status"] = status
    packet["task_type"] = "local_docs_only"
    packet["created_at"] = "2026-05-09T00:00:00Z"
    packet["priority"] = "low"
    packet["summary"] = "Safe local docs-only operator CLI test task."
    packet["instructions"] = ["Create a harmless docs note."]
    packet["repo"]["base_branch"] = "master"
    packet["repo"]["allowed_paths"] = ["docs/"]
    packet["repo"]["forbidden_paths"] = ["ai_orchestrator/", "runtime/", "pm_bot/"]
    packet["acceptance_checks"] = []
    packet["expected_outputs"] = ["docs/result.md"]
    if status in {"approved", "planned"}:
        packet["approved_by"] = "operator"
        packet["approved_at"] = "2026-05-09T00:00:00Z"
    return packet


def _safe_result(task_id: str, *, files_created: list[str] | None = None) -> dict:
    result = default_result()
    result["task_id"] = task_id
    result["completed_at"] = "2026-05-09T00:00:00Z"
    result["summary"] = "Safe manual result for operator CLI tests."
    result["files_created"] = files_created or ["docs/result.md"]
    result["commands_run"] = []
    return result


def _write_task(queue_root: Path, packet: dict) -> Path:
    path = queue_root / packet["status"] / f"{packet['task_id']}.task.json"
    _write_json(path, packet)
    return path


def _write_result(queue_root: Path, result: dict) -> Path:
    path = queue_root / "review" / f"{result['task_id']}.result.json"
    _write_json(path, result)
    return path


def _write_ready_handoff_artifacts(queue_root: Path, task_id: str) -> None:
    handoff_path = queue_root / "planned" / f"{task_id}.handoff_prompt.md"
    workspace_plan_path = queue_root / "planned" / f"{task_id}.workspace_plan.json"
    _write_json(
        queue_root / "planned" / f"{task_id}.plan.json",
        {
            "task_id": task_id,
            "handoff_prompt_path": str(handoff_path),
            "workspace_plan_path": str(workspace_plan_path),
        },
    )
    handoff_path.parent.mkdir(parents=True, exist_ok=True)
    handoff_path.write_text("# Manual handoff\n", encoding="utf-8")
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


def _state_files(queue_root: Path) -> set[str]:
    states = ("inbox", "approved", "planned", "running", "review", "done", "blocked")
    return {
        str(path.relative_to(queue_root))
        for state in states
        for path in (queue_root / state).glob("*")
        if path.is_file()
    }


def test_status_writes_latest_queue_status_reports(tmp_path: Path) -> None:
    queue_root = tmp_path / "agent_tasks"

    exit_code = main(["status", "--queue-root", str(queue_root)])

    assert exit_code == 0
    assert (queue_root / "reports" / "latest_queue_status.json").exists()
    assert (queue_root / "reports" / "latest_queue_status.md").exists()
    assert (queue_root / "reports" / "latest_operator_action.json").exists()


def test_create_demo_task_creates_inbox_packet(tmp_path: Path) -> None:
    queue_root = tmp_path / "agent_tasks"
    task_id = "ORCH-DEMO-CLI-TEST"

    exit_code = main(["create-demo-task", "--queue-root", str(queue_root), "--task-id", task_id])

    packet_path = queue_root / "inbox" / f"{task_id}.task.json"
    packet = json.loads(packet_path.read_text(encoding="utf-8"))
    assert exit_code == 0
    assert packet["schema_version"] == "codex_task_packet.v1"
    assert packet["status"] == "inbox"
    assert packet["task_type"] == "local_docs_only"
    assert packet["repo"]["allowed_paths"] == ["docs/"]
    assert all(value is False for value in packet["risk_flags"].values())


def test_create_demo_task_refuses_overwrite_by_default(tmp_path: Path) -> None:
    queue_root = tmp_path / "agent_tasks"
    task_id = "ORCH-DEMO-CLI-OVERWRITE"

    assert main(["create-demo-task", "--queue-root", str(queue_root), "--task-id", task_id]) == 0
    exit_code = main(["create-demo-task", "--queue-root", str(queue_root), "--task-id", task_id])

    action = json.loads((queue_root / "reports" / "latest_operator_action.json").read_text(encoding="utf-8"))
    assert exit_code == 1
    assert action["status"] == "blocked"
    assert "already exists" in action["errors"][0]


def test_approve_moves_safe_task_from_inbox_to_approved(tmp_path: Path) -> None:
    queue_root = tmp_path / "agent_tasks"
    task_id = "ORCH-APPROVE-SAFE"
    _write_task(queue_root, _safe_packet(task_id))

    exit_code = main(["approve", "--queue-root", str(queue_root), "--task-id", task_id])

    approved_path = queue_root / "approved" / f"{task_id}.task.json"
    packet = json.loads(approved_path.read_text(encoding="utf-8"))
    assert exit_code == 0
    assert not (queue_root / "inbox" / f"{task_id}.task.json").exists()
    assert packet["status"] == "approved"
    assert packet["approved_by"] == "operator_cli"
    assert packet["approved_at"].endswith("Z")


def test_approve_refuses_unsafe_task(tmp_path: Path) -> None:
    queue_root = tmp_path / "agent_tasks"
    task_id = "ORCH-APPROVE-UNSAFE"
    packet = _safe_packet(task_id)
    packet["risk_flags"]["requires_network"] = True
    _write_task(queue_root, packet)

    exit_code = main(["approve", "--queue-root", str(queue_root), "--task-id", task_id])

    action = json.loads((queue_root / "reports" / "latest_operator_action.json").read_text(encoding="utf-8"))
    assert exit_code == 1
    assert (queue_root / "inbox" / f"{task_id}.task.json").exists()
    assert not (queue_root / "approved" / f"{task_id}.task.json").exists()
    assert action["status"] == "blocked"
    assert any("special approval" in error for error in action["errors"])


def test_plan_command_writes_dry_run_report_and_handoff_prompt(tmp_path: Path) -> None:
    queue_root = tmp_path / "agent_tasks"
    task_id = "ORCH-PLAN-CLI"
    packet = _safe_packet(task_id, status="approved")
    packet["acceptance_checks"] = ["python -c \"raise SystemExit('must not run')\""]
    _write_task(queue_root, packet)

    exit_code = main(["plan", "--queue-root", str(queue_root)])

    assert exit_code == 0
    assert (queue_root / "reports" / "latest_dry_run_report.json").exists()
    assert (queue_root / "planned" / f"{task_id}.plan.json").exists()
    assert (queue_root / "planned" / f"{task_id}.handoff_prompt.md").exists()
    action = json.loads((queue_root / "reports" / "latest_operator_action.json").read_text(encoding="utf-8"))
    assert action["acceptance_checks_executed"] is False
    assert action["codex_execution_added"] is False
    assert action["codex_app_server_used"] is False


def test_ingest_result_command_writes_ingestion_report(tmp_path: Path) -> None:
    queue_root = tmp_path / "agent_tasks"
    task_id = "ORCH-INGEST-CLI"
    _write_task(queue_root, _safe_packet(task_id, status="approved"))
    result_path = _write_result(queue_root, _safe_result(task_id))

    exit_code = main(["ingest-result", "--queue-root", str(queue_root), "--result", str(result_path)])

    report = json.loads((queue_root / "reports" / "latest_result_ingestion_report.json").read_text(encoding="utf-8"))
    action = json.loads((queue_root / "reports" / "latest_operator_action.json").read_text(encoding="utf-8"))
    assert exit_code == 0
    assert report["accepted"] is True
    assert report["task_marked_done_automatically"] is False
    assert action["commands_from_result_executed"] is False


def test_review_command_writes_task_review_report(tmp_path: Path) -> None:
    queue_root = tmp_path / "agent_tasks"
    task_id = "ORCH-REVIEW-CLI"
    _write_task(queue_root, _safe_packet(task_id, status="approved"))
    assert main(["plan", "--queue-root", str(queue_root)]) == 0
    result_path = _write_result(queue_root, _safe_result(task_id))
    assert main(["ingest-result", "--queue-root", str(queue_root), "--result", str(result_path)]) == 0

    exit_code = main(["review", "--queue-root", str(queue_root), "--task-id", task_id])

    report_path = queue_root / "reports" / f"{task_id}.review.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert exit_code == 0
    assert report["recommendation"] == "ready_for_operator_done"
    assert report["ingestion"]["allowed"] is True


def test_mark_done_refuses_when_no_allowed_ingestion_exists(tmp_path: Path) -> None:
    queue_root = tmp_path / "agent_tasks"
    task_id = "ORCH-DONE-NO-INGEST"
    _write_task(queue_root, _safe_packet(task_id, status="approved"))
    _write_result(queue_root, _safe_result(task_id))
    review_path = queue_root / "reports" / f"{task_id}.review.json"
    _write_json(review_path, {"task_id": task_id, "recommendation": "ready_for_operator_done"})

    exit_code = main(["mark-done", "--queue-root", str(queue_root), "--task-id", task_id])

    action = json.loads((queue_root / "reports" / "latest_operator_action.json").read_text(encoding="utf-8"))
    assert exit_code == 1
    assert action["status"] == "blocked"
    assert any("ingestion report" in error for error in action["errors"])
    assert (queue_root / "approved" / f"{task_id}.task.json").exists()


def test_latest_result_ingestion_report_is_pointer_only(tmp_path: Path) -> None:
    queue_root = tmp_path / "agent_tasks"
    task_id = "ORCH-LATEST-POINTER"
    _write_task(queue_root, _safe_packet(task_id, status="approved"))
    latest_path = queue_root / "reports" / "latest_result_ingestion_report.json"
    _write_json(
        latest_path,
        {
            "task_id": task_id,
            "ingestion_status": "accepted",
            "accepted": True,
            "errors": [],
            "result_validation": {"valid": True},
            "task_validation": {"valid": True},
            "path_validation": {"valid": True},
        },
    )

    ingestion = find_allowed_ingestion_report(queue_root, task_id)

    assert ingestion["allowed"] is False
    assert ingestion["status"] == "missing"
    assert ingestion["path"] is None
    assert ingestion["latest_report_path"] == str(latest_path)
    assert ingestion["latest_report_is_pointer"] is True
    assert ingestion["latest_report_task_id"] == task_id


def test_mark_done_succeeds_only_after_allowed_ingestion_and_ready_review(tmp_path: Path) -> None:
    queue_root = tmp_path / "agent_tasks"
    task_id = "ORCH-DONE-CLI"
    _write_task(queue_root, _safe_packet(task_id, status="approved"))
    assert main(["plan", "--queue-root", str(queue_root)]) == 0
    result_path = _write_result(queue_root, _safe_result(task_id))
    assert main(["ingest-result", "--queue-root", str(queue_root), "--result", str(result_path)]) == 0
    assert main(["review", "--queue-root", str(queue_root), "--task-id", task_id]) == 0

    exit_code = main(["mark-done", "--queue-root", str(queue_root), "--task-id", task_id])

    done_path = queue_root / "done" / f"{task_id}.task.json"
    packet = json.loads(done_path.read_text(encoding="utf-8"))
    assert exit_code == 0
    assert packet["status"] == "done"
    assert not (queue_root / "approved" / f"{task_id}.task.json").exists()
    assert (queue_root / "review" / f"{task_id}.result.json").exists()


def test_mark_blocked_moves_task_to_blocked_and_records_reason(tmp_path: Path) -> None:
    queue_root = tmp_path / "agent_tasks"
    task_id = "ORCH-BLOCKED-CLI"
    _write_task(queue_root, _safe_packet(task_id, status="approved"))

    exit_code = main(
        ["mark-blocked", "--queue-root", str(queue_root), "--task-id", task_id, "--reason", "waiting on operator"]
    )

    blocked_path = queue_root / "blocked" / f"{task_id}.task.json"
    packet = json.loads(blocked_path.read_text(encoding="utf-8"))
    assert exit_code == 0
    assert packet["status"] == "blocked"
    assert "waiting on operator" in packet["operator_notes"]
    assert (queue_root / "reports" / f"{task_id}.blocked.json").exists()


def test_commands_do_not_execute_codex_acceptance_checks_or_network(tmp_path: Path, monkeypatch) -> None:
    queue_root = tmp_path / "agent_tasks"
    task_id = "ORCH-NO-EXEC-CLI"
    sentinel = tmp_path / "sentinel.txt"
    packet = _safe_packet(task_id, status="approved")
    packet["acceptance_checks"] = [
        f"python -c \"from pathlib import Path; Path(r'{sentinel}').write_text('bad')\"",
        "codex run should-not-execute",
    ]
    _write_task(queue_root, packet)

    def fail_subprocess_run(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise AssertionError("subprocess execution is not allowed in operator CLI tests")

    def fail_network(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise AssertionError("network access is not allowed in operator CLI tests")

    monkeypatch.setattr(subprocess, "run", fail_subprocess_run)
    monkeypatch.setattr(socket, "create_connection", fail_network)
    monkeypatch.setattr(socket, "socket", fail_network)
    monkeypatch.setattr(
        "ai_orchestrator.codex_queue.workspace_planner.inspect_git_state",
        lambda repo_root: {
            "repo_root": str(tmp_path / "repo"),
            "branch": "master",
            "head": "abc123",
            "status_lines": [],
            "is_clean": True,
            "tracked_changes_count": 0,
            "untracked_count": 0,
            "warnings": [],
            "errors": [],
        },
    )
    monkeypatch.setattr(
        "ai_orchestrator.codex_queue.night_runner.inspect_git_state",
        lambda repo_root: {
            "repo_root": str(tmp_path / "repo"),
            "branch": "master",
            "head": "abc123",
            "status_lines": [],
            "is_clean": True,
            "tracked_changes_count": 0,
            "untracked_count": 0,
            "warnings": [],
            "errors": [],
        },
    )

    assert main(["status", "--queue-root", str(queue_root)]) == 0
    assert main(["plan", "--queue-root", str(queue_root)]) == 0
    assert main(["run-codex-batch", "--queue-root", str(queue_root), "--max-tasks", "3", "--dry-run"]) == 0
    assert main(["workspace-plan", "--queue-root", str(queue_root), "--task-id", task_id]) == 0
    assert main(["runbook", "--queue-root", str(queue_root)]) == 0
    assert main(["morning-report", "--queue-root", str(queue_root)]) == 0
    assert main(["next-actions", "--queue-root", str(queue_root)]) == 0
    assert main(["night-dry-run", "--queue-root", str(queue_root), "--max-tasks", "5"]) == 0
    assert main(["scheduler-plan", "--queue-root", str(queue_root)]) == 0
    assert main(["portability-check", "--queue-root", str(queue_root)]) == 0
    assert main(["package-readiness", "--queue-root", str(queue_root)]) == 0
    assert not sentinel.exists()


def test_runbook_morning_report_and_next_actions_commands_write_reports(tmp_path: Path) -> None:
    queue_root = tmp_path / "agent_tasks"
    task_id = "ORCH-REPORT-CLI"
    _write_task(queue_root, _safe_packet(task_id, status="approved"))
    _write_ready_handoff_artifacts(queue_root, task_id)

    assert main(["runbook", "--queue-root", str(queue_root)]) == 0
    assert main(["morning-report", "--queue-root", str(queue_root)]) == 0
    assert main(["next-actions", "--queue-root", str(queue_root)]) == 0

    assert (queue_root / "reports" / "latest_controlled_codex_runbook.json").exists()
    assert (queue_root / "reports" / "latest_controlled_codex_runbook.md").exists()
    assert (queue_root / "reports" / "latest_morning_report.json").exists()
    assert (queue_root / "reports" / "latest_morning_report.md").exists()
    assert (queue_root / "reports" / "latest_next_actions.json").exists()
    assert (queue_root / "reports" / "latest_next_actions.md").exists()


def test_run_codex_batch_dry_run_command_writes_report_without_codex(tmp_path: Path, monkeypatch) -> None:
    queue_root = tmp_path / "agent_tasks"
    task_id = "ORCH-BATCH-CLI"
    _write_task(queue_root, _safe_packet(task_id, status="approved"))
    _write_ready_handoff_artifacts(queue_root, task_id)

    def fail_run_codex_once(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise AssertionError("batch dry-run must not invoke the one-task runner")

    monkeypatch.setattr("ai_orchestrator.codex_queue.codex_cli_batch_runner.run_codex_once", fail_run_codex_once)

    exit_code = main(["run-codex-batch", "--queue-root", str(queue_root), "--max-tasks", "3", "--dry-run"])

    action = json.loads((queue_root / "reports" / "latest_operator_action.json").read_text(encoding="utf-8"))
    assert exit_code == 0
    assert action["status"] == "ok"
    assert action["execution_status"] == "dry_run"
    assert action["selected_task_ids"] == [task_id]
    assert action["codex_exec_invoked"] is False
    assert action["codex_invocation_count"] == 0
    assert Path(action["codex_cli_batch_report_paths"]["batch_report_json"]).exists()


def test_postprocess_codex_batch_command_bridges_result(tmp_path: Path) -> None:
    queue_root = tmp_path / "agent_tasks"
    task_id = "ORCH-BATCH-POSTPROCESS-CLI"
    execution_dir = queue_root / "reports" / "codex_cli_runs" / task_id / "20260509T010000Z"
    execution_report_path = execution_dir / "execution_report.json"
    last_message_path = execution_dir / "last_message.md"
    _write_json(
        execution_report_path,
        {
            "schema_version": "codex_cli_execution_report.v1",
            "task_id": task_id,
            "run_id": "20260509T010000Z",
            "status": "ok",
            "execution_status": "completed",
            "exit_code": 0,
            "execution_ended_at": "2026-05-09T01:05:00Z",
            "report_paths": {"last_message": str(last_message_path)},
            "network_calls_performed": 0,
            "openrouter_calls_performed": 0,
            "polymarket_api_calls_performed": 0,
            "wallet_or_private_key_access": False,
            "orders_or_trading_actions": False,
            "runtime_or_dispatcher_changes": False,
            "background_worker_created": False,
            "scheduler_created": False,
            "codex_app_server_used": False,
            "destructive_commands_used": False,
        },
    )
    last_message_path.write_text(
        json.dumps(
            {
                "task_id": task_id,
                "status": "completed",
                "summary": "Completed CLI postprocess bridge test.",
                "files_changed": ["docs/postprocess.md"],
                "validation_commands_run": ["pytest tests/test_codex_queue_operator_cli.py"],
                "tests_passed": True,
                "safety_notes": ["No network, credentials, wallet, trading, runtime, scheduler, or destructive commands."],
            }
        ),
        encoding="utf-8",
    )
    batch_report_path = queue_root / "reports" / "codex_cli_batch_report_20260509T020000Z.json"
    _write_json(
        batch_report_path,
        {
            "schema_version": "codex_cli_batch_execution_report.v1",
            "run_id": "20260509T020000Z",
            "status": "ok",
            "execution_status": "completed",
            "ended_at": "2026-05-09T02:00:00Z",
            "task_executions": [
                {
                    "task_id": task_id,
                    "status": "ok",
                    "execution_status": "completed",
                    "exit_code": 0,
                    "execution_report_json": str(execution_report_path),
                    "errors": [],
                    "warnings": [],
                }
            ],
        },
    )

    exit_code = main(
        [
            "postprocess-codex-batch",
            "--queue-root",
            str(queue_root),
            "--batch-report",
            str(batch_report_path),
            "--bridge-results",
        ]
    )

    action = json.loads((queue_root / "reports" / "latest_operator_action.json").read_text(encoding="utf-8"))
    result = json.loads((queue_root / "review" / f"{task_id}.result.json").read_text(encoding="utf-8"))
    assert exit_code == 0
    assert action["status"] == "ok"
    assert action["bridged_count"] == 1
    assert action["task_marked_done_automatically"] is False
    assert action["git_commit_performed"] is False
    assert action["git_push_performed"] is False
    assert result["schema_version"] == "codex_task_result.v1"
    assert result["files_modified"] == ["docs/postprocess.md"]


def test_night_dry_run_and_scheduler_plan_commands_write_reports(tmp_path: Path, monkeypatch) -> None:
    queue_root = tmp_path / "agent_tasks"
    task_id = "ORCH-NIGHT-CLI"
    _write_task(queue_root, _safe_packet(task_id, status="approved"))
    _write_ready_handoff_artifacts(queue_root, task_id)
    monkeypatch.setattr(
        "ai_orchestrator.codex_queue.night_runner.inspect_git_state",
        lambda repo_root: {
            "repo_root": str(tmp_path / "repo"),
            "branch": "master",
            "head": "abc123",
            "status_lines": [],
            "is_clean": True,
            "tracked_changes_count": 0,
            "untracked_count": 0,
            "warnings": [],
            "errors": [],
        },
    )

    assert main(["night-dry-run", "--queue-root", str(queue_root), "--max-tasks", "5"]) == 0
    assert main(["scheduler-plan", "--queue-root", str(queue_root)]) == 0

    assert (queue_root / "reports" / "latest_night_dry_run_plan.json").exists()
    assert (queue_root / "reports" / "latest_night_dry_run_plan.md").exists()
    assert (queue_root / "reports" / "latest_night_runner_lock_check.json").exists()
    assert (queue_root / "reports" / "latest_night_runner_lock_check.md").exists()
    assert (queue_root / "reports" / "latest_scheduler_plan.json").exists()
    assert (queue_root / "reports" / "latest_scheduler_plan.md").exists()


def test_portability_and_package_readiness_commands_write_reports(tmp_path: Path) -> None:
    queue_root = tmp_path / "agent_tasks"

    assert main(["portability-check", "--queue-root", str(queue_root)]) == 0
    assert main(["package-readiness", "--queue-root", str(queue_root)]) == 0

    portability = json.loads(
        (queue_root / "reports" / "latest_portability_report.json").read_text(encoding="utf-8")
    )
    readiness = json.loads(
        (queue_root / "reports" / "latest_package_readiness.json").read_text(encoding="utf-8")
    )
    assert portability["package_import_ok"] is True
    assert portability["codex_execution_added"] is False
    assert portability["codex_app_server_used"] is False
    assert readiness["git_add_performed"] is False
    assert readiness["git_commit_performed"] is False
    assert readiness["git_push_performed"] is False
    assert (queue_root / "reports" / "latest_portability_report.md").exists()
    assert (queue_root / "reports" / "latest_package_readiness.md").exists()


def test_report_commands_do_not_create_branch_worktree_or_mutate_queue_states(tmp_path: Path, monkeypatch) -> None:
    queue_root = tmp_path / "agent_tasks"
    task_id = "ORCH-REPORT-NO-MUTATE"
    _write_task(queue_root, _safe_packet(task_id, status="approved"))
    _write_ready_handoff_artifacts(queue_root, task_id)
    before = _state_files(queue_root)
    monkeypatch.setattr(
        "ai_orchestrator.codex_queue.night_runner.inspect_git_state",
        lambda repo_root: {
            "repo_root": str(tmp_path / "repo"),
            "branch": "master",
            "head": "abc123",
            "status_lines": [],
            "is_clean": True,
            "tracked_changes_count": 0,
            "untracked_count": 0,
            "warnings": [],
            "errors": [],
        },
    )

    assert main(["runbook", "--queue-root", str(queue_root)]) == 0
    assert main(["morning-report", "--queue-root", str(queue_root)]) == 0
    assert main(["next-actions", "--queue-root", str(queue_root)]) == 0
    assert main(["night-dry-run", "--queue-root", str(queue_root), "--max-tasks", "5"]) == 0
    assert main(["scheduler-plan", "--queue-root", str(queue_root)]) == 0
    assert main(["portability-check", "--queue-root", str(queue_root)]) == 0
    assert main(["package-readiness", "--queue-root", str(queue_root)]) == 0

    runbook = json.loads((queue_root / "reports" / "latest_controlled_codex_runbook.json").read_text())
    morning = json.loads((queue_root / "reports" / "latest_morning_report.json").read_text())
    next_actions = json.loads((queue_root / "reports" / "latest_next_actions.json").read_text())
    night = json.loads((queue_root / "reports" / "latest_night_dry_run_plan.json").read_text())
    scheduler = json.loads((queue_root / "reports" / "latest_scheduler_plan.json").read_text())
    portability = json.loads((queue_root / "reports" / "latest_portability_report.json").read_text())
    readiness = json.loads((queue_root / "reports" / "latest_package_readiness.json").read_text())
    assert _state_files(queue_root) == before
    assert runbook["branch_created"] is False
    assert runbook["worktree_created"] is False
    assert morning["branch_created"] is False
    assert morning["worktree_created"] is False
    assert next_actions["branch_created"] is False
    assert next_actions["worktree_created"] is False
    assert night["branch_created"] is False
    assert night["worktree_created"] is False
    assert night["would_register_scheduler"] is False
    assert scheduler["branch_created"] is False
    assert scheduler["worktree_created"] is False
    assert scheduler["scheduler_registered"] is False
    assert portability["branch_created"] is False
    assert portability["worktree_created"] is False
    assert readiness["branch_created"] is False
    assert readiness["worktree_created"] is False
    assert readiness["git_commit_performed"] is False
