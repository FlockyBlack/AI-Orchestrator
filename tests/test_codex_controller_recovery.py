from __future__ import annotations

import json
from pathlib import Path

from ai_orchestrator.codex_queue.long_run_controller import LongRunController
from ai_orchestrator.codex_queue.plan_run_state import load_state, save_state
from codex_plan_helpers import write_plan


def _write_stale_lock(lock_path: Path) -> None:
    lock_path.write_text(
        json.dumps(
            {
                "run_id": "RUN1",
                "plan_id": "test_plan",
                "pid": 999999,
                "created_at": "2000-01-01T00:00:00Z",
                "updated_at": "2000-01-01T00:00:00Z",
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def test_recover_plan_detects_stale_lock_and_only_clears_with_flag(tmp_path: Path) -> None:
    plan_path = write_plan(tmp_path / "plan.json")
    queue_root = tmp_path / "agent_tasks"
    controller = LongRunController(repo_root=tmp_path)
    run = controller.run_plan(plan_path, queue_root, run_id="RUN1", max_steps=1)
    lock_path = Path(run["payload"]["run_root"]) / "run.lock"
    _write_stale_lock(lock_path)

    blocked = controller.recover_plan("RUN1", queue_root)
    assert lock_path.exists()
    recovered = controller.recover_plan("RUN1", queue_root, allow_stale_lock_clear=True)

    assert blocked["status"] == "blocked"
    assert recovered["status"] == "recovered"
    assert not lock_path.exists()
    assert Path(recovered["recovery_report_paths"]["json"]).exists()


def test_continue_plan_blocks_inconsistent_state_and_requires_recovery(tmp_path: Path) -> None:
    plan_path = write_plan(tmp_path / "plan.json")
    queue_root = tmp_path / "agent_tasks"
    controller = LongRunController(repo_root=tmp_path)
    run = controller.run_plan(plan_path, queue_root, run_id="RUN1", max_steps=1)
    state = load_state(run["state_path"])
    state.completed_task_ids.append("UNKNOWN")
    save_state(state, run["state_path"])

    result = controller.continue_plan("RUN1", queue_root, max_steps=1)

    assert result["status"] == "blocked"
    assert result["stop_reason"] == "inconsistent_state"
