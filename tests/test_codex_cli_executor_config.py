from __future__ import annotations

import json
import sys
from pathlib import Path

from ai_orchestrator.codex_queue.codex_cli_executor import (
    build_codex_cli_command,
    load_codex_cli_executor_config,
    validate_codex_cli_executor_config,
)


def test_codex_cli_config_defaults_block_real_invocation(tmp_path: Path) -> None:
    config = load_codex_cli_executor_config(tmp_path / "missing.json")
    validation = validate_codex_cli_executor_config(config)

    assert validation["valid"] is False
    assert any("does not exist" in error for error in validation["errors"])
    assert any("config.enabled must be true" in error for error in validation["errors"])


def test_codex_cli_config_accepts_safe_enabled_fake_command(tmp_path: Path) -> None:
    config_path = tmp_path / "agent_tasks" / "config" / "codex_executor_config.json"
    config_path.parent.mkdir(parents=True)
    fake_command = Path(__file__).with_name("fake_codex_command.py")
    config_path.write_text(
        json.dumps(
            {
                "enabled": True,
                "codex_command": [sys.executable, str(fake_command)],
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
        ),
        encoding="utf-8",
    )

    config = load_codex_cli_executor_config(config_path)
    validation = validate_codex_cli_executor_config(config)
    command = build_codex_cli_command(_packet(tmp_path), config)

    assert validation["valid"] is True
    assert command[:2] == [sys.executable, str(fake_command)]
    assert "--result-json" in command


def test_codex_cli_config_rejects_unsafe_flags(tmp_path: Path) -> None:
    config_path = tmp_path / "codex_executor_config.json"
    config_path.write_text(
        json.dumps(
            {
                "enabled": True,
                "codex_command": "codex",
                "allow_network": True,
                "allow_auth": True,
                "allow_browser": True,
                "allow_real_trading": True,
                "write_logs": False,
            }
        ),
        encoding="utf-8",
    )

    validation = validate_codex_cli_executor_config(load_codex_cli_executor_config(config_path))

    assert validation["valid"] is False
    assert "allow_network must be false" in validation["errors"]
    assert "allow_auth must be false" in validation["errors"]
    assert "allow_browser must be false" in validation["errors"]
    assert "allow_real_trading must be false" in validation["errors"]
    assert "write_logs must be true so stdout/stderr/invocation logs are captured" in validation["errors"]


def _packet(tmp_path: Path) -> dict:
    return {
        "packet_id": "packet1",
        "run_id": "RUN1",
        "plan_id": "test_plan",
        "task_id": "TEST-TASK-001",
        "created_at": "2026-05-11T00:00:00Z",
        "repo_root": str(tmp_path),
        "branch": "master",
        "expected_head": "",
        "queue_manifest_path": str(tmp_path / "agent_tasks" / "generated" / "test_plan" / "RUN1" / "manifest.json"),
        "state_path": str(tmp_path / "agent_tasks" / "generated" / "test_plan" / "RUN1" / "state.json"),
        "task_spec_path": str(tmp_path / "agent_tasks" / "generated" / "test_plan" / "RUN1" / "tasks" / "TEST-TASK-001.json"),
        "allowed_paths": ["docs/"],
        "forbidden_actions": ["Do not use wallet files."],
        "acceptance_gates": ["validation passes"],
        "prompt_path": str(tmp_path / "agent_tasks" / "generated" / "test_plan" / "RUN1" / "codex_packets" / "TEST-TASK-001" / "prompt.md"),
        "expected_result_path": str(tmp_path / "agent_tasks" / "generated" / "test_plan" / "RUN1" / "codex_packets" / "TEST-TASK-001" / "expected_result_template.json"),
        "adapter_mode": "codex_cli_operator_approved",
        "requires_operator_approval": True,
        "safety_boundaries": ["operator_approval_required_for_codex_execution"],
    }
