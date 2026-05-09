from __future__ import annotations

import json
from pathlib import Path

from ai_orchestrator.codex_queue.codex_cli_batch_runner import DEFAULT_MAX_TASKS, HARD_MAX_TASKS, run_codex_batch
from ai_orchestrator.codex_queue.schema import default_packet


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _approved_packet(task_id: str, *, status: str = "approved") -> dict:
    packet = default_packet()
    packet["task_id"] = task_id
    packet["title"] = f"{task_id} batch runner test"
    packet["status"] = status
    packet["approved_by"] = "operator"
    packet["approved_at"] = "2026-05-09T00:00:00Z"
    packet["task_type"] = "local_code_tests"
    packet["summary"] = "Safe local code test packet for supervised batch runner tests."
    packet["instructions"] = ["Inspect local files and return a strict result JSON packet."]
    packet["repo"]["repo_root"] = "."
    packet["repo"]["base_branch"] = "master"
    packet["repo"]["allowed_paths"] = ["docs/", "tests/"]
    packet["repo"]["forbidden_paths"] = ["runtime/", "dispatcher/", "run_codex/", "pm_bot/wallet/"]
    packet["acceptance_checks"] = []
    packet["expected_outputs"] = [f"agent_tasks/review/{task_id}.result.json"]
    return packet


def _inbox_packet(task_id: str) -> dict:
    packet = _approved_packet(task_id, status="inbox")
    packet["approved_by"] = None
    packet["approved_at"] = None
    return packet


def _write_task(queue_root: Path, packet: dict, *, state: str | None = None) -> None:
    target_state = state or packet["status"]
    _write_json(queue_root / target_state / f"{packet['task_id']}.task.json", packet)


def _write_ready_handoff(queue_root: Path, task_id: str) -> None:
    handoff_path = queue_root / "planned" / f"{task_id}.handoff_prompt.md"
    plan_path = queue_root / "planned" / f"{task_id}.plan.json"
    handoff_path.parent.mkdir(parents=True, exist_ok=True)
    handoff_path.write_text(f"# Handoff for {task_id}\nReturn strict JSON.\n", encoding="utf-8")
    _write_json(
        plan_path,
        {
            "task_id": task_id,
            "handoff_prompt_path": str(handoff_path),
            "workspace_plan_path": str(queue_root / "planned" / f"{task_id}.workspace_plan.json"),
        },
    )


def _write_ready_task(queue_root: Path, task_id: str, *, status: str = "approved") -> None:
    _write_task(queue_root, _approved_packet(task_id, status=status))
    _write_ready_handoff(queue_root, task_id)


def _clean_git_state() -> dict:
    return {
        "repo_root": str(Path.cwd()),
        "branch": "master",
        "head": "abc123",
        "status_lines": [],
        "is_clean": True,
        "tracked_changes_count": 0,
        "untracked_count": 0,
        "warnings": [],
        "errors": [],
    }


def _state_files(queue_root: Path) -> set[str]:
    states = ("inbox", "approved", "planned", "running", "review", "done", "blocked")
    return {
        str(path.relative_to(queue_root))
        for state in states
        for path in (queue_root / state).glob("*")
        if path.is_file()
    }


def test_batch_dry_run_does_not_call_codex(tmp_path: Path, monkeypatch) -> None:
    queue_root = tmp_path / "agent_tasks"
    task_id = "ORCH-BATCH-DRY-RUN"
    _write_ready_task(queue_root, task_id)

    def fail_run_codex_once(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise AssertionError("batch dry-run must not call the one-task runner")

    monkeypatch.setattr("ai_orchestrator.codex_queue.codex_cli_batch_runner.run_codex_once", fail_run_codex_once)

    report = run_codex_batch(queue_root, dry_run=True)

    assert report["status"] == "ok"
    assert report["execution_status"] == "dry_run"
    assert report["selected_task_ids"] == [task_id]
    assert report["one_task_runner_invocation_count"] == 0
    assert report["codex_exec_invoked"] is False
    assert report["codex_invocation_count"] == 0
    assert "run-codex-once" in report["selected_tasks"][0]["one_task_dry_run_command"]
    assert "--dry-run" in report["selected_tasks"][0]["one_task_dry_run_command"]


def test_batch_max_tasks_cap_is_enforced(tmp_path: Path) -> None:
    queue_root = tmp_path / "agent_tasks"
    task_ids = [f"ORCH-BATCH-CAP-{index}" for index in range(1, 6)]
    for task_id in task_ids:
        _write_ready_task(queue_root, task_id)

    report = run_codex_batch(queue_root, max_tasks=3, dry_run=True)

    assert report["status"] == "ok"
    assert report["selected_task_ids"] == task_ids[:3]
    assert report["skipped_task_ids"] == task_ids[3:]
    assert all(skipped["reason"] == "beyond max_tasks cap" for skipped in report["skipped_tasks"])


def test_batch_default_max_tasks_is_ten(tmp_path: Path) -> None:
    queue_root = tmp_path / "agent_tasks"
    task_ids = [f"ORCH-BATCH-DEFAULT-{index:02d}" for index in range(1, 12)]
    for task_id in task_ids:
        _write_ready_task(queue_root, task_id)

    report = run_codex_batch(queue_root, dry_run=True)

    assert DEFAULT_MAX_TASKS == 10
    assert report["max_tasks"] == 10
    assert report["selected_task_ids"] == task_ids[:10]
    assert report["skipped_task_ids"] == task_ids[10:]


def test_batch_hard_cap_is_twenty(tmp_path: Path) -> None:
    queue_root = tmp_path / "agent_tasks"
    task_ids = [f"ORCH-BATCH-HARD-{index:02d}" for index in range(1, 22)]
    for task_id in task_ids:
        _write_ready_task(queue_root, task_id)

    report = run_codex_batch(queue_root, max_tasks=20, dry_run=True)

    assert HARD_MAX_TASKS == 20
    assert report["hard_max_tasks"] == 20
    assert report["selected_task_ids"] == task_ids[:20]
    assert report["skipped_task_ids"] == task_ids[20:]


def test_batch_hard_cap_rejects_values_above_twenty(tmp_path: Path) -> None:
    queue_root = tmp_path / "agent_tasks"
    _write_ready_task(queue_root, "ORCH-BATCH-HARD-CAP")

    report = run_codex_batch(queue_root, max_tasks=21, dry_run=True)

    assert report["status"] == "blocked"
    assert any("20 or fewer" in error for error in report["errors"])
    assert Path(report["report_paths"]["batch_report_json"]).exists()


def test_batch_stops_on_first_failure(tmp_path: Path, monkeypatch) -> None:
    queue_root = tmp_path / "agent_tasks"
    task_ids = ["ORCH-BATCH-FAIL-1", "ORCH-BATCH-FAIL-2", "ORCH-BATCH-FAIL-3"]
    for task_id in task_ids:
        _write_ready_task(queue_root, task_id)
    calls: list[str] = []

    monkeypatch.setattr("ai_orchestrator.codex_queue.codex_cli_batch_runner.inspect_git_state", lambda repo: _clean_git_state())

    def fake_run_codex_once(queue_root_arg, *, task_id, dry_run, timeout_seconds):  # type: ignore[no-untyped-def]
        calls.append(task_id)
        status = "failed" if task_id == "ORCH-BATCH-FAIL-2" else "ok"
        return {
            "task_id": task_id,
            "status": status,
            "execution_status": "failed" if status == "failed" else "completed",
            "exit_code": 12 if status == "failed" else 0,
            "report_paths": {"execution_report_json": f"{task_id}.json", "execution_report_md": f"{task_id}.md"},
            "codex_exec_invoked": True,
            "codex_invocation_count": 1,
            "errors": ["simulated failure"] if status == "failed" else [],
            "warnings": [],
            "next_operator_action": "inspect logs",
        }

    monkeypatch.setattr("ai_orchestrator.codex_queue.codex_cli_batch_runner.run_codex_once", fake_run_codex_once)

    report = run_codex_batch(queue_root, max_tasks=3)

    assert calls == task_ids[:2]
    assert report["status"] == "failed"
    assert report["execution_status"] == "stopped_after_task_failure"
    assert report["stopped_on_task_id"] == "ORCH-BATCH-FAIL-2"
    assert [execution["task_id"] for execution in report["task_executions"]] == task_ids[:2]


def test_batch_does_not_perform_forbidden_auto_actions(tmp_path: Path, monkeypatch) -> None:
    queue_root = tmp_path / "agent_tasks"
    task_id = "ORCH-BATCH-NO-AUTO"
    _write_ready_task(queue_root, task_id)
    before = _state_files(queue_root)
    monkeypatch.setattr("ai_orchestrator.codex_queue.codex_cli_batch_runner.inspect_git_state", lambda repo: _clean_git_state())
    monkeypatch.setattr(
        "ai_orchestrator.codex_queue.codex_cli_batch_runner.run_codex_once",
        lambda queue_root_arg, *, task_id, dry_run, timeout_seconds: {
            "task_id": task_id,
            "status": "ok",
            "execution_status": "completed",
            "exit_code": 0,
            "report_paths": {"execution_report_json": f"{task_id}.json", "execution_report_md": f"{task_id}.md"},
            "codex_exec_invoked": True,
            "codex_invocation_count": 1,
            "errors": [],
            "warnings": [],
            "next_operator_action": "inspect result",
        },
    )

    report = run_codex_batch(queue_root)

    assert _state_files(queue_root) == before
    assert report["result_ingested_automatically"] is False
    assert report["task_marked_done_automatically"] is False
    assert report["review_approved_automatically"] is False
    assert report["git_commit_performed"] is False
    assert report["git_push_performed"] is False
    assert report["task_created_automatically"] is False
    assert report["task_approved_automatically"] is False
    assert report["scheduler_created"] is False
    assert report["daemon_created"] is False
    assert report["background_worker_created"] is False
    assert report["infinite_loop_created"] is False
    assert report["network_calls_performed"] == 0
    assert report["openrouter_calls_performed"] == 0
    assert report["polymarket_api_calls_performed"] == 0
    assert report["wallet_or_private_key_access"] is False
    assert report["orders_or_trading_actions"] is False
    assert report["runtime_or_dispatcher_changes"] is False


def test_batch_writes_json_and_markdown_report(tmp_path: Path) -> None:
    queue_root = tmp_path / "agent_tasks"
    task_id = "ORCH-BATCH-REPORT"
    _write_ready_task(queue_root, task_id)

    report = run_codex_batch(queue_root, dry_run=True)

    assert Path(report["report_paths"]["batch_report_json"]).exists()
    assert Path(report["report_paths"]["batch_report_md"]).exists()
    assert Path(report["report_paths"]["latest_batch_report_json"]).exists()
    assert Path(report["report_paths"]["latest_batch_report_md"]).exists()
    assert "Codex CLI Batch Execution" in Path(report["report_paths"]["batch_report_md"]).read_text(encoding="utf-8")


def test_batch_skips_non_approved_non_planned_tasks(tmp_path: Path) -> None:
    queue_root = tmp_path / "agent_tasks"
    ready_task_id = "ORCH-BATCH-READY"
    inbox_task_id = "ORCH-BATCH-INBOX"
    _write_ready_task(queue_root, ready_task_id)
    _write_task(queue_root, _inbox_packet(inbox_task_id), state="inbox")
    _write_ready_handoff(queue_root, inbox_task_id)

    report = run_codex_batch(queue_root, dry_run=True)

    assert report["selected_task_ids"] == [ready_task_id]
    assert inbox_task_id in report["skipped_task_ids"]
    assert any(
        skipped["task_id"] == inbox_task_id and skipped["reason"] == "no approved/planned task packet found"
        for skipped in report["skipped_tasks"]
    )
