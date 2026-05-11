from __future__ import annotations

from pathlib import Path

from ai_orchestrator.codex_queue.plan_run_state import (
    PlanRunState,
    append_event,
    increment_retry,
    load_state,
    mark_task_blocked,
    mark_task_done,
    mark_task_failed,
    mark_task_started,
    save_state,
    summarize_state,
)


def test_state_transitions_and_resume(tmp_path: Path) -> None:
    state = PlanRunState.create("RUN1", "PLAN1")
    mark_task_started(state, "TASK1")
    increment_retry(state, "TASK1")
    mark_task_done(state, "TASK1", artifact_paths=["artifact.json"])
    append_event(state, {"event": "custom"})
    path = save_state(state, tmp_path / "state.json")

    loaded = load_state(path)

    assert loaded.completed_task_ids == ["TASK1"]
    assert loaded.retry_counts["TASK1"] == 1
    assert loaded.artifact_paths == ["artifact.json"]
    assert summarize_state(loaded)["completed_count"] == 1


def test_blocked_and_failed_states_are_recorded() -> None:
    state = PlanRunState.create("RUN1", "PLAN1")
    mark_task_blocked(state, "TASK2", "waiting")
    mark_task_failed(state, "TASK3", "bad")

    assert "TASK2" in state.blocked_task_ids
    assert "TASK3" in state.failed_task_ids
    assert summarize_state(state)["status"] == "failed"
