from __future__ import annotations

import json
import sys
from pathlib import Path

from ai_orchestrator.codex_queue.plan_run_state import load_state
from ai_orchestrator.operator_panel.panel_actions import run_fake_steps_action
from ai_orchestrator.operator_panel.panel_app import route_get, route_post
from codex_plan_helpers import minimal_plan, write_plan


APPROVAL_TEXT = "I approve real Codex CLI invocation for this run"


def test_panel_codex_cli_page_shows_config_and_approval_controls(tmp_path: Path) -> None:
    queue_root = tmp_path / "agent_tasks"
    plan_path = write_plan(tmp_path / "plan.json", minimal_plan(1))
    _write_enabled_config(queue_root)
    run_fake_steps_action(plan_path, queue_root, max_steps=0)

    html = route_get("/codex-cli", "", tmp_path, queue_root)

    assert "Codex CLI Executor" in html
    assert "Test Codex CLI config" in html
    assert "Continue with Codex CLI, max 1 step" in html
    assert APPROVAL_TEXT in html


def test_panel_codex_cli_continue_requires_explicit_approval(tmp_path: Path) -> None:
    queue_root = tmp_path / "agent_tasks"
    plan_path = write_plan(tmp_path / "plan.json", minimal_plan(1))
    _write_enabled_config(queue_root)
    run = run_fake_steps_action(plan_path, queue_root, max_steps=0)

    result = route_post(
        "/actions/continue-codex-cli",
        {"run_id": run["run_id"], "max_steps": "1", "approval_text": "", "approval_checked": ""},
        tmp_path,
        queue_root,
    )

    assert result["status"] == "blocked"
    assert result["codex_invoked"] is False
    assert "approval checkbox" in result["errors"][0]


def test_panel_codex_cli_continue_with_fake_command_auto_ingests(tmp_path: Path) -> None:
    queue_root = tmp_path / "agent_tasks"
    plan_path = write_plan(tmp_path / "plan.json", minimal_plan(1))
    _write_enabled_config(queue_root)
    run = run_fake_steps_action(plan_path, queue_root, max_steps=0)

    result = route_post(
        "/actions/continue-codex-cli",
        {
            "run_id": run["run_id"],
            "max_steps": "1",
            "approval_text": APPROVAL_TEXT,
            "approval_checked": "on",
        },
        tmp_path,
        queue_root,
    )
    state = load_state(result["state_path"])

    assert result["status"] == "done"
    assert state.completed_task_ids == ["TEST-TASK-001"]


def test_panel_test_codex_cli_config_does_not_invoke_codex(tmp_path: Path) -> None:
    queue_root = tmp_path / "agent_tasks"
    _write_enabled_config(queue_root)

    result = route_post("/actions/test-codex-cli-config", {}, tmp_path, queue_root)

    assert result["status"] == "ok"
    assert result["codex_invoked"] is False


def _write_enabled_config(queue_root: Path) -> Path:
    config_path = queue_root / "config" / "codex_executor_config.json"
    config_path.parent.mkdir(parents=True, exist_ok=True)
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
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return config_path
