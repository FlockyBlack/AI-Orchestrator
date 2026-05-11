from __future__ import annotations

import json
import sys
from pathlib import Path

from ai_orchestrator.codex_queue.operator_cli import main
from ai_orchestrator.codex_queue.plan_run_state import load_state
from codex_plan_helpers import minimal_plan, write_plan


def test_continue_plan_codex_cli_auto_ingests_fake_result(tmp_path: Path) -> None:
    queue_root = tmp_path / "agent_tasks"
    plan_path = write_plan(tmp_path / "plan.json", minimal_plan(2))
    _write_enabled_config(queue_root)
    assert main(["run-plan", "--plan-file", str(plan_path), "--queue-root", str(queue_root), "--run-id", "RUN_REAL", "--max-steps", "0"]) == 0

    exit_code = main(
        [
            "continue-plan",
            "--run-id",
            "RUN_REAL",
            "--queue-root",
            str(queue_root),
            "--executor",
            "codex_cli",
            "--max-steps",
            "2",
            "--auto-ingest",
            "--allow-real-codex-invocation",
            "--continue-until",
            "blocked_or_done",
        ]
    )
    action = _latest_action(queue_root)
    state = load_state(action["state_path"])

    assert exit_code == 0
    assert action["run_status"] == "done"
    assert state.completed_task_ids == ["TEST-TASK-001", "TEST-TASK-002"]
    assert action["codex_execution_added"] is True
    assert action["codex_invoked"] is True
    assert action["codex_result_ingestion"]["status"] == "accepted"


def test_continue_plan_codex_cli_requires_operator_approval_flag(tmp_path: Path) -> None:
    queue_root = tmp_path / "agent_tasks"
    plan_path = write_plan(tmp_path / "plan.json", minimal_plan(1))
    _write_enabled_config(queue_root)
    assert main(["run-plan", "--plan-file", str(plan_path), "--queue-root", str(queue_root), "--run-id", "RUN_NO_APPROVAL", "--max-steps", "0"]) == 0

    exit_code = main(
        [
            "continue-plan",
            "--run-id",
            "RUN_NO_APPROVAL",
            "--queue-root",
            str(queue_root),
            "--executor",
            "codex_cli",
            "--max-steps",
            "1",
            "--auto-ingest",
            "--continue-until",
            "blocked_or_done",
        ]
    )
    action = _latest_action(queue_root)

    assert exit_code == 1
    assert action["run_status"] == "blocked"
    assert action["codex_invoked"] is False
    assert "operator approval flag" in json.dumps(action)


def test_continue_plan_codex_cli_requires_enabled_config(tmp_path: Path) -> None:
    queue_root = tmp_path / "agent_tasks"
    plan_path = write_plan(tmp_path / "plan.json", minimal_plan(1))
    _write_enabled_config(queue_root, enabled=False)
    assert main(["run-plan", "--plan-file", str(plan_path), "--queue-root", str(queue_root), "--run-id", "RUN_DISABLED", "--max-steps", "0"]) == 0

    exit_code = main(
        [
            "continue-plan",
            "--run-id",
            "RUN_DISABLED",
            "--queue-root",
            str(queue_root),
            "--executor",
            "codex_cli",
            "--max-steps",
            "1",
            "--auto-ingest",
            "--allow-real-codex-invocation",
        ]
    )
    action = _latest_action(queue_root)

    assert exit_code == 1
    assert action["run_status"] == "blocked"
    assert "config.enabled must be true" in json.dumps(action)


def test_cli_test_config_and_print_command_do_not_invoke_codex(tmp_path: Path) -> None:
    queue_root = tmp_path / "agent_tasks"
    plan_path = write_plan(tmp_path / "plan.json", minimal_plan(1))
    _write_enabled_config(queue_root)
    assert main(["run-plan", "--plan-file", str(plan_path), "--queue-root", str(queue_root), "--run-id", "RUN_PREVIEW", "--max-steps", "0"]) == 0

    assert main(["test-codex-cli-config", "--queue-root", str(queue_root)]) == 0
    test_action = _latest_action(queue_root)
    assert test_action["status"] == "ok"
    assert test_action["codex_invoked"] is False

    assert main(["print-codex-cli-command", "--run-id", "RUN_PREVIEW", "--queue-root", str(queue_root)]) == 0
    print_action = _latest_action(queue_root)
    assert print_action["status"] == "ok"
    assert print_action["codex_invoked"] is False
    assert "--result-json" in print_action["codex_cli_command"]


def _write_enabled_config(queue_root: Path, *, enabled: bool = True) -> Path:
    config_path = queue_root / "config" / "codex_executor_config.json"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    fake_command = Path(__file__).with_name("fake_codex_command.py")
    config_path.write_text(
        json.dumps(
            {
                "enabled": enabled,
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
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return config_path


def _latest_action(queue_root: Path) -> dict:
    return json.loads((queue_root / "reports" / "latest_operator_action.json").read_text(encoding="utf-8"))
