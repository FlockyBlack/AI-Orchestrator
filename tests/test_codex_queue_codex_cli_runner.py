from __future__ import annotations

import json
import subprocess
from pathlib import Path

from ai_orchestrator.codex_queue.codex_cli_runner import run_codex_once
from ai_orchestrator.codex_queue.operator_cli import main
from ai_orchestrator.codex_queue.schema import default_packet


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _approved_packet(task_id: str, *, expected_head: str | None = None, status: str = "approved") -> dict:
    packet = default_packet()
    packet["task_id"] = task_id
    packet["title"] = f"{task_id} Codex CLI runner test"
    packet["status"] = status
    packet["approved_by"] = "operator"
    packet["approved_at"] = "2026-05-09T00:00:00Z"
    packet["task_type"] = "local_code_tests"
    packet["summary"] = "Safe local code test task for supervised runner tests."
    packet["instructions"] = ["Inspect local files and write a strict result JSON packet."]
    packet["repo"]["repo_root"] = "."
    packet["repo"]["base_branch"] = "master"
    packet["repo"]["allowed_paths"] = ["docs/", "tests/"]
    packet["repo"]["forbidden_paths"] = ["runtime/", "dispatcher/", "run_codex/", "pm_bot/wallet/"]
    packet["acceptance_checks"] = []
    packet["expected_outputs"] = ["agent_tasks/review/result.json"]
    if expected_head is not None:
        packet["repo"]["expected_head"] = expected_head
    return packet


def _write_task(queue_root: Path, packet: dict, *, state: str = "approved") -> Path:
    path = queue_root / state / f"{packet['task_id']}.task.json"
    _write_json(path, packet)
    return path


def _write_ready_handoff(queue_root: Path, task_id: str) -> Path:
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
    return handoff_path


def _fake_git_state(head: str = "abc123") -> dict:
    return {
        "repo_root": str(Path.cwd()),
        "branch": "master",
        "head": head,
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


def test_dry_run_does_not_call_codex_and_writes_report(tmp_path: Path, monkeypatch) -> None:
    queue_root = tmp_path / "agent_tasks"
    task_id = "ORCH-CODEX-DRY-RUN"
    _write_task(queue_root, _approved_packet(task_id, expected_head="abc123"))
    _write_ready_handoff(queue_root, task_id)
    monkeypatch.setattr("ai_orchestrator.codex_queue.codex_cli_runner.inspect_git_state", lambda repo_root: _fake_git_state())
    monkeypatch.setattr("ai_orchestrator.codex_queue.codex_cli_runner.shutil.which", lambda name: "codex")

    def fail_run(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise AssertionError("dry-run must not invoke Codex CLI")

    monkeypatch.setattr("ai_orchestrator.codex_queue.codex_cli_runner.subprocess.run", fail_run)

    report = run_codex_once(queue_root, task_id=task_id, dry_run=True)

    assert report["status"] == "ok"
    assert report["execution_status"] == "dry_run"
    assert report["codex_exec_invoked"] is False
    assert report["codex_invocation_count"] == 0
    assert report["would_invoke_codex"] is True
    assert report["command"]["argv"][:2] == ["codex", "exec"]
    assert report["command"]["stdin_from"].endswith(f"{task_id}.handoff_prompt.md")
    assert Path(report["report_paths"]["execution_report_json"]).exists()


def test_missing_codex_cli_blocks_safely(tmp_path: Path, monkeypatch) -> None:
    queue_root = tmp_path / "agent_tasks"
    task_id = "ORCH-CODEX-MISSING"
    _write_task(queue_root, _approved_packet(task_id))
    _write_ready_handoff(queue_root, task_id)
    monkeypatch.setattr("ai_orchestrator.codex_queue.codex_cli_runner.inspect_git_state", lambda repo_root: _fake_git_state())
    monkeypatch.setattr("ai_orchestrator.codex_queue.codex_cli_runner.shutil.which", lambda name: None)

    def fail_run(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise AssertionError("missing Codex CLI must block before subprocess")

    monkeypatch.setattr("ai_orchestrator.codex_queue.codex_cli_runner.subprocess.run", fail_run)

    report = run_codex_once(queue_root, task_id=task_id)

    assert report["status"] == "blocked"
    assert report["execution_status"] == "blocked"
    assert report["codex_exec_invoked"] is False
    assert any("Codex CLI executable was not found" in error for error in report["errors"])
    assert Path(report["report_paths"]["execution_report_json"]).exists()


def test_unapproved_or_unplanned_task_blocks_safely(tmp_path: Path, monkeypatch) -> None:
    queue_root = tmp_path / "agent_tasks"
    task_id = "ORCH-CODEX-UNAPPROVED"
    packet = _approved_packet(task_id, status="inbox")
    packet["approved_by"] = None
    packet["approved_at"] = None
    _write_task(queue_root, packet, state="inbox")
    _write_ready_handoff(queue_root, task_id)
    monkeypatch.setattr("ai_orchestrator.codex_queue.codex_cli_runner.inspect_git_state", lambda repo_root: _fake_git_state())
    monkeypatch.setattr("ai_orchestrator.codex_queue.codex_cli_runner.shutil.which", lambda name: "codex")

    def fail_run(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise AssertionError("unapproved task must block before subprocess")

    monkeypatch.setattr("ai_orchestrator.codex_queue.codex_cli_runner.subprocess.run", fail_run)

    report = run_codex_once(queue_root, task_id=task_id)

    assert report["status"] == "blocked"
    assert report["execution_status"] == "blocked"
    assert report["codex_exec_invoked"] is False
    assert any("no approved/planned task packet found" in error for error in report["errors"])


def test_expected_head_mismatch_blocks_before_codex(tmp_path: Path, monkeypatch) -> None:
    queue_root = tmp_path / "agent_tasks"
    task_id = "ORCH-CODEX-HEAD-MISMATCH"
    _write_task(queue_root, _approved_packet(task_id, expected_head="expected-head"))
    _write_ready_handoff(queue_root, task_id)
    monkeypatch.setattr(
        "ai_orchestrator.codex_queue.codex_cli_runner.inspect_git_state",
        lambda repo_root: _fake_git_state(head="actual-head"),
    )
    monkeypatch.setattr("ai_orchestrator.codex_queue.codex_cli_runner.shutil.which", lambda name: "codex")

    def fail_run(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise AssertionError("expected_head mismatch must block before subprocess")

    monkeypatch.setattr("ai_orchestrator.codex_queue.codex_cli_runner.subprocess.run", fail_run)

    report = run_codex_once(queue_root, task_id=task_id)

    assert report["status"] == "blocked"
    assert report["expected_head_verification"]["matched"] is False
    assert report["codex_exec_invoked"] is False
    assert any("expected_head mismatch" in error for error in report["errors"])


def test_execution_report_logs_stdout_stderr_and_exit_code(tmp_path: Path, monkeypatch) -> None:
    queue_root = tmp_path / "agent_tasks"
    task_id = "ORCH-CODEX-EXECUTE"
    _write_task(queue_root, _approved_packet(task_id, expected_head="abc123"))
    _write_ready_handoff(queue_root, task_id)
    monkeypatch.setattr("ai_orchestrator.codex_queue.codex_cli_runner.inspect_git_state", lambda repo_root: _fake_git_state())
    monkeypatch.setattr("ai_orchestrator.codex_queue.codex_cli_runner.shutil.which", lambda name: "codex")
    calls: list[dict] = []

    def fake_run(argv, **kwargs):  # type: ignore[no-untyped-def]
        calls.append({"argv": argv, **kwargs})
        assert argv[:2] == ["codex", "exec"]
        assert kwargs["input"].startswith("# Handoff")
        assert kwargs["capture_output"] is True
        assert kwargs["text"] is True
        return subprocess.CompletedProcess(argv, 0, stdout="codex stdout\n", stderr="codex stderr\n")

    monkeypatch.setattr("ai_orchestrator.codex_queue.codex_cli_runner.subprocess.run", fake_run)

    report = run_codex_once(queue_root, task_id=task_id, timeout_seconds=12)

    assert len(calls) == 1
    assert report["status"] == "ok"
    assert report["execution_status"] == "completed"
    assert report["exit_code"] == 0
    assert report["codex_exec_invoked"] is True
    assert report["codex_invocation_count"] == 1
    assert Path(report["report_paths"]["stdout_log"]).read_text(encoding="utf-8") == "codex stdout\n"
    assert Path(report["report_paths"]["stderr_log"]).read_text(encoding="utf-8") == "codex stderr\n"
    assert Path(report["report_paths"]["execution_report_md"]).exists()


def test_runner_does_not_perform_forbidden_auto_actions(tmp_path: Path, monkeypatch) -> None:
    queue_root = tmp_path / "agent_tasks"
    task_id = "ORCH-CODEX-NO-AUTO"
    _write_task(queue_root, _approved_packet(task_id))
    _write_ready_handoff(queue_root, task_id)
    before = _state_files(queue_root)
    monkeypatch.setattr("ai_orchestrator.codex_queue.codex_cli_runner.inspect_git_state", lambda repo_root: _fake_git_state())
    monkeypatch.setattr("ai_orchestrator.codex_queue.codex_cli_runner.shutil.which", lambda name: "codex")
    monkeypatch.setattr(
        "ai_orchestrator.codex_queue.codex_cli_runner.subprocess.run",
        lambda argv, **kwargs: subprocess.CompletedProcess(argv, 0, stdout="", stderr=""),
    )

    report = run_codex_once(queue_root, task_id=task_id)

    assert _state_files(queue_root) == before
    assert report["result_ingested_automatically"] is False
    assert report["task_marked_done_automatically"] is False
    assert report["review_approved_automatically"] is False
    assert report["git_push_performed"] is False
    assert report["scheduler_created"] is False
    assert report["daemon_created"] is False
    assert report["background_worker_created"] is False
    assert report["multi_task_loop_created"] is False


def test_operator_cli_run_codex_once_dry_run_command(tmp_path: Path, monkeypatch) -> None:
    queue_root = tmp_path / "agent_tasks"
    task_id = "ORCH-CODEX-CLI"
    _write_task(queue_root, _approved_packet(task_id))
    _write_ready_handoff(queue_root, task_id)
    monkeypatch.setattr("ai_orchestrator.codex_queue.codex_cli_runner.inspect_git_state", lambda repo_root: _fake_git_state())
    monkeypatch.setattr("ai_orchestrator.codex_queue.codex_cli_runner.shutil.which", lambda name: "codex")

    def fail_run(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise AssertionError("CLI dry-run must not invoke Codex CLI")

    monkeypatch.setattr("ai_orchestrator.codex_queue.codex_cli_runner.subprocess.run", fail_run)

    exit_code = main(
        [
            "run-codex-once",
            "--queue-root",
            str(queue_root),
            "--task-id",
            task_id,
            "--dry-run",
        ]
    )

    action = json.loads((queue_root / "reports" / "latest_operator_action.json").read_text(encoding="utf-8"))
    assert exit_code == 0
    assert action["status"] == "ok"
    assert action["execution_status"] == "dry_run"
    assert action["codex_exec_invoked"] is False
    assert Path(action["codex_cli_execution_report_paths"]["execution_report_json"]).exists()
