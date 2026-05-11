from __future__ import annotations

from pathlib import Path

from ai_orchestrator.codex_queue.long_run_controller import LongRunController
from ai_orchestrator.codex_queue.plan_run_state import load_state
from codex_plan_helpers import write_plan


def test_handoff_executor_exports_prompt_and_records_state_path(tmp_path: Path) -> None:
    plan_path = write_plan(tmp_path / "plan.json")
    queue_root = tmp_path / "agent_tasks"
    controller = LongRunController(repo_root=tmp_path)
    run = controller.run_plan(plan_path, queue_root, run_id="RUN1", max_steps=1, executor="fake")

    handoff = controller.continue_plan("RUN1", queue_root, max_steps=1, executor="handoff", continue_until="one_step")
    state = load_state(run["state_path"])
    prompt_path = Path(handoff["handoff_prompt_path"])
    prompt = prompt_path.read_text(encoding="utf-8")

    assert handoff["status"] == "requiring_operator_handoff"
    assert prompt_path.exists()
    assert state.latest_handoff_prompt_path == str(prompt_path)
    assert "Return only JSON" in prompt
    assert "Previously Completed Tasks" in prompt
    assert "TEST-TASK-001" in prompt
    assert '"task_id": "TEST-TASK-002"' in prompt
