from __future__ import annotations

import json
import sys
from pathlib import Path

from ai_orchestrator.codex_queue.codex_cli_executor import (
    collect_codex_result,
    invoke_codex_cli,
    load_codex_cli_executor_config,
)
from ai_orchestrator.codex_queue.long_run_controller import LongRunController
from codex_plan_helpers import write_plan


def test_invoke_codex_cli_with_fake_command_writes_and_collects_result(tmp_path: Path) -> None:
    packet_path, config = _packet_and_config(tmp_path)
    packet = json.loads(packet_path.read_text(encoding="utf-8"))

    invocation = invoke_codex_cli(packet, config, 30)
    collected = collect_codex_result(packet, config)

    assert invocation.status == "completed"
    assert invocation.codex_invoked is True
    assert Path(invocation.stdout_log_path).exists()
    assert Path(invocation.stderr_log_path).exists()
    assert Path(invocation.invocation_log_path).exists()
    assert collected["status"] == "found"
    assert Path(collected["result_json_path"]).exists()


def test_invoke_codex_cli_missing_executable_blocks(tmp_path: Path) -> None:
    packet_path, _config = _packet_and_config(tmp_path)
    packet = json.loads(packet_path.read_text(encoding="utf-8"))
    bad_config_path = tmp_path / "agent_tasks" / "config" / "bad_config.json"
    bad_config_path.write_text(
        json.dumps(
            {
                **_config_payload("__definitely_missing_codex_command__"),
                "enabled": True,
            }
        ),
        encoding="utf-8",
    )

    invocation = invoke_codex_cli(packet, load_codex_cli_executor_config(bad_config_path), 30)

    assert invocation.status == "blocked"
    assert invocation.codex_invoked is False
    assert any("executable was not found" in error for error in invocation.errors)


def test_invoke_codex_cli_nonzero_exit_fails(tmp_path: Path, monkeypatch) -> None:
    packet_path, config = _packet_and_config(tmp_path)
    packet = json.loads(packet_path.read_text(encoding="utf-8"))
    monkeypatch.setenv("FAKE_CODEX_MODE", "nonzero")

    invocation = invoke_codex_cli(packet, config, 30)

    assert invocation.status == "failed"
    assert invocation.exit_code == 9
    assert any("exited with code 9" in error for error in invocation.errors)


def test_collect_codex_result_rejects_unsafe_fake_result(tmp_path: Path, monkeypatch) -> None:
    packet_path, config = _packet_and_config(tmp_path)
    packet = json.loads(packet_path.read_text(encoding="utf-8"))
    monkeypatch.setenv("FAKE_CODEX_MODE", "unsafe")

    invocation = invoke_codex_cli(packet, config, 30)
    collected = collect_codex_result(packet, config)

    assert invocation.status == "completed"
    assert collected["status"] == "invalid"
    assert any("wallet used" in error.lower() for error in collected["errors"])


def test_collect_codex_result_reports_missing_result(tmp_path: Path, monkeypatch) -> None:
    packet_path, config = _packet_and_config(tmp_path)
    packet = json.loads(packet_path.read_text(encoding="utf-8"))
    monkeypatch.setenv("FAKE_CODEX_MODE", "missing_result")

    invocation = invoke_codex_cli(packet, config, 30)
    collected = collect_codex_result(packet, config)

    assert invocation.status == "completed"
    assert collected["status"] == "missing"
    assert collected["exists"] is False


def _packet_and_config(tmp_path: Path) -> tuple[Path, object]:
    plan_path = write_plan(tmp_path / "plan.json")
    queue_root = tmp_path / "agent_tasks"
    result = LongRunController(repo_root=tmp_path).run_plan(
        plan_path,
        queue_root,
        run_id="RUN1",
        max_steps=1,
        executor="codex_packet",
    )
    config_path = queue_root / "config" / "codex_executor_config.json"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(json.dumps(_config_payload()) + "\n", encoding="utf-8")
    return Path(result["execution_packet_path"]), load_codex_cli_executor_config(config_path)


def _config_payload(command: str | list[str] | None = None) -> dict:
    fake_command = Path(__file__).with_name("fake_codex_command.py")
    return {
        "enabled": True,
        "codex_command": command if command is not None else [sys.executable, str(fake_command)],
        "mode": "cli",
        "working_directory_mode": "repo_root",
        "result_contract": "result_json_file",
        "result_json_relative_path": "agent_tasks/generated/<plan_id>/<run_id>/codex_packets/<task_id>/codex_result.json",
        "timeout_seconds": 30,
        "max_steps_per_invocation": 1,
        "allow_network": False,
        "allow_browser": False,
        "allow_auth": False,
        "allow_real_trading": False,
        "require_clean_worktree": False,
        "write_logs": True,
    }
