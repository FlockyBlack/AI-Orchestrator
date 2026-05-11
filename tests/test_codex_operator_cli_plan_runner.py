from __future__ import annotations

import json
from pathlib import Path

from ai_orchestrator.codex_queue.operator_cli import main
from codex_plan_helpers import write_plan


def _latest_action(queue_root: Path) -> dict:
    return json.loads((queue_root / "reports" / "latest_operator_action.json").read_text(encoding="utf-8"))


def test_cli_run_plan_works_in_fake_mode(tmp_path: Path) -> None:
    plan_path = write_plan(tmp_path / "plan.json")
    queue_root = tmp_path / "agent_tasks"

    exit_code = main(
        [
            "run-plan",
            "--plan-file",
            str(plan_path),
            "--queue-root",
            str(queue_root),
            "--mode",
            "long_supervised",
            "--max-steps",
            "3",
            "--executor",
            "fake",
            "--continue-until",
            "blocked_or_done",
        ]
    )

    action = _latest_action(queue_root)
    assert exit_code == 0
    assert action["run_status"] == "done"
    assert action["run_id"]


def test_cli_continue_plan_resumes_state(tmp_path: Path) -> None:
    plan_path = write_plan(tmp_path / "plan.json")
    queue_root = tmp_path / "agent_tasks"
    assert main(["run-plan", "--plan-file", str(plan_path), "--queue-root", str(queue_root), "--max-steps", "1", "--executor", "fake"]) == 0
    run_id = _latest_action(queue_root)["run_id"]

    exit_code = main(["continue-plan", "--run-id", run_id, "--queue-root", str(queue_root), "--max-steps", "10"])

    assert exit_code == 0
    assert _latest_action(queue_root)["run_status"] == "done"


def test_cli_export_next_codex_prompt_creates_handoff(tmp_path: Path) -> None:
    plan_path = write_plan(tmp_path / "plan.json")
    queue_root = tmp_path / "agent_tasks"
    assert main(["run-plan", "--plan-file", str(plan_path), "--queue-root", str(queue_root), "--max-steps", "1", "--executor", "fake"]) == 0
    run_id = _latest_action(queue_root)["run_id"]

    exit_code = main(["export-next-codex-prompt", "--run-id", run_id, "--queue-root", str(queue_root)])

    assert exit_code == 0
    assert _latest_action(queue_root)["run_status"] == "requiring_operator_handoff"
    assert list(queue_root.glob("generated/*/*/handoff/*_codex_prompt.md"))
