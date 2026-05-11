from __future__ import annotations

from pathlib import Path

from ai_orchestrator.codex_queue.plan_contract import PlanContract
from ai_orchestrator.codex_queue.plan_run_state import (
    PlanRunState,
    create_checkpoint,
    get_last_checkpoint,
    list_checkpoints,
    load_state,
    mark_task_done,
    restore_checkpoint,
    save_state,
    validate_state_consistency,
)
from codex_plan_helpers import minimal_plan


def test_state_atomic_save_load_and_checkpoint_restore(tmp_path: Path) -> None:
    plan = PlanContract.from_dict(minimal_plan(2))
    state = PlanRunState.create("RUN1", plan.plan_id)
    mark_task_done(state, "TEST-TASK-001", artifact_paths=["a.json"])
    checkpoint = create_checkpoint(state, "after_first")
    mark_task_done(state, "TEST-TASK-002", artifact_paths=["b.json"])

    path = save_state(state, tmp_path / "state.json")
    loaded = load_state(path)

    assert loaded.state_schema_version
    assert not list(tmp_path.glob("*.tmp"))
    assert list_checkpoints(loaded)[0]["checkpoint_reason"] == "after_first"
    restore_checkpoint(loaded, checkpoint["checkpoint_id"])
    assert loaded.completed_task_ids == ["TEST-TASK-001"]
    assert get_last_checkpoint(loaded)["checkpoint_id"] == checkpoint["checkpoint_id"]


def test_state_consistency_detects_duplicate_unknown_dependency_retry_and_completed_pending() -> None:
    plan = PlanContract.from_dict(minimal_plan(3))
    state = PlanRunState.create("RUN1", plan.plan_id)
    state.status = "completed"
    state.completed_task_ids = ["TEST-TASK-002", "UNKNOWN"]
    state.failed_task_ids = ["TEST-TASK-002"]
    state.current_task_id = "MISSING"
    state.retry_counts = {"TEST-TASK-001": -1}

    result = validate_state_consistency(state, plan)

    assert result["consistent"] is False
    joined = "\n".join(result["errors"])
    assert "multiple terminal status lists" in joined
    assert "unknown task ID in state: UNKNOWN" in joined
    assert "current_task_id not in plan: MISSING" in joined
    assert "completed task TEST-TASK-002 has incomplete dependency: TEST-TASK-001" in joined
    assert "retry count below zero" in joined
    assert "run marked completed while pending tasks exist" in joined
