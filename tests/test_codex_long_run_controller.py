from __future__ import annotations

import json
from pathlib import Path

from ai_orchestrator.codex_queue.long_run_controller import LongRunController
from ai_orchestrator.codex_queue.plan_contract import PlanContract
from ai_orchestrator.codex_queue.plan_to_queue import create_queue_from_plan
from ai_orchestrator.codex_queue.task_executor import FakeTaskExecutor
from codex_plan_helpers import write_plan


def test_fake_run_completes_multiple_tasks(tmp_path: Path) -> None:
    plan_path = write_plan(tmp_path / "plan.json")
    queue_root = tmp_path / "agent_tasks"

    result = LongRunController(repo_root=tmp_path).run_plan(plan_path, queue_root, max_steps=3, executor="fake")

    assert result["status"] == "done"
    assert result["payload"]["steps_executed"] == 3
    assert Path(result["payload"]["state_path"]).exists()


def test_handoff_mode_stops_for_operator(tmp_path: Path) -> None:
    plan_path = write_plan(tmp_path / "plan.json")
    queue_root = tmp_path / "agent_tasks"

    result = LongRunController(repo_root=tmp_path).run_plan(plan_path, queue_root, max_steps=1, executor="handoff")

    assert result["status"] == "requiring_operator_handoff"
    assert list((Path(result["payload"]["run_root"]) / "handoff").glob("*_codex_prompt.md"))


def test_execute_next_task_stops_on_blocker(tmp_path: Path) -> None:
    plan_path = write_plan(tmp_path / "plan.json")
    queue_root = tmp_path / "agent_tasks"
    queue = create_queue_from_plan(plan_path, queue_root, run_id="RUN1")
    plan = PlanContract.from_dict(json.loads(plan_path.read_text(encoding="utf-8")))
    from ai_orchestrator.codex_queue.plan_run_state import PlanRunState, save_state

    state = PlanRunState.create("RUN1", plan.plan_id, queue_manifest_path=queue.queue_paths["manifest"])
    state_path = Path(queue.queue_paths["run_root"]) / "state.json"
    save_state(state, state_path)
    controller = LongRunController(repo_root=tmp_path)
    result = controller.execute_next_task(
        plan,
        state,
        state_path,
        queue.queue_paths["run_root"],
        queue_root,
        FakeTaskExecutor(blocked_task_ids={"TEST-TASK-001"}),
    )

    assert result["status"] == "blocked"
    assert "TEST-TASK-001" in state.blocked_task_ids
