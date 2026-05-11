from __future__ import annotations

import json
from pathlib import Path

from ai_orchestrator.codex_queue.operator_cli import main
from ai_orchestrator.codex_queue.plan_run_state import load_state, save_state
from codex_plan_helpers import write_plan


def _latest_action(queue_root: Path) -> dict:
    return json.loads((queue_root / "reports" / "latest_operator_action.json").read_text(encoding="utf-8"))


def test_cli_list_inspect_validate_and_checkpoint_run(tmp_path: Path) -> None:
    plan_path = write_plan(tmp_path / "plan.json")
    queue_root = tmp_path / "agent_tasks"
    assert main(["run-plan", "--plan-file", str(plan_path), "--queue-root", str(queue_root), "--max-steps", "1"]) == 0
    run_id = _latest_action(queue_root)["run_id"]

    assert main(["list-runs", "--queue-root", str(queue_root)]) == 0
    assert _latest_action(queue_root)["run_count"] == 1
    assert main(["inspect-run", "--run-id", run_id, "--queue-root", str(queue_root)]) == 0
    assert _latest_action(queue_root)["run_inspection"]["run_id"] == run_id
    assert main(["validate-state", "--run-id", run_id, "--queue-root", str(queue_root)]) == 0
    assert _latest_action(queue_root)["state_validation"]["consistent"] is True
    assert main(["checkpoint-run", "--run-id", run_id, "--queue-root", str(queue_root), "--reason", "manual"]) == 0
    assert _latest_action(queue_root)["checkpoint"]["checkpoint_reason"] == "manual"


def test_cli_validate_state_returns_nonzero_for_inconsistent_state(tmp_path: Path) -> None:
    plan_path = write_plan(tmp_path / "plan.json")
    queue_root = tmp_path / "agent_tasks"
    assert main(["run-plan", "--plan-file", str(plan_path), "--queue-root", str(queue_root), "--run-id", "RUN1", "--max-steps", "1"]) == 0
    state_path = next(queue_root.glob("generated/*/RUN1/state.json"))
    state = load_state(state_path)
    state.completed_task_ids.append("UNKNOWN")
    save_state(state, state_path)

    exit_code = main(["validate-state", "--run-id", "RUN1", "--queue-root", str(queue_root)])

    assert exit_code == 1
    assert _latest_action(queue_root)["status"] == "blocked"
