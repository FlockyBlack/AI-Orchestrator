from __future__ import annotations

from ai_orchestrator.codex_queue.plan_contract import PlanContract
from ai_orchestrator.codex_queue.plan_run_state import PlanRunState, mark_task_done
from ai_orchestrator.symphony_adapter.symphony_mapping import (
    map_plan_task_to_symphony_task,
    map_symphony_task_to_codex_packet,
)
from ai_orchestrator.symphony_adapter.symphony_session_plan import build_session_plan
from ai_orchestrator.symphony_adapter.symphony_workspace_plan import build_workspace_plan_for_task
from codex_plan_helpers import minimal_plan


def test_map_plan_task_to_symphony_task_selects_runnable_status(tmp_path) -> None:
    plan = PlanContract.from_dict(minimal_plan(task_count=2))
    state = PlanRunState.create("RUN1", plan.plan_id, queue_manifest_path="manifest.json")
    mark_task_done(state, "TEST-TASK-001")

    symphony_task = map_plan_task_to_symphony_task(plan.tasks[1], state, plan)

    assert symphony_task.task_id == "TEST-TASK-002"
    assert symphony_task.status.runnable is True
    assert symphony_task.dependencies == ("TEST-TASK-001",)
    assert "unsafe git staging" in symphony_task.forbidden_actions


def test_map_symphony_task_to_codex_packet_renders_protocol_template(tmp_path) -> None:
    schema_dir = tmp_path / "schema"
    schema_dir.mkdir()
    (schema_dir / "ClientRequest.json").write_text('{"oneOf":[]}', encoding="utf-8")
    plan = PlanContract.from_dict(minimal_plan(task_count=1))
    state = PlanRunState.create("RUN1", plan.plan_id, queue_manifest_path="manifest.json")
    symphony_task = map_plan_task_to_symphony_task(plan.tasks[0], state, plan)
    workspace_plan = build_workspace_plan_for_task(symphony_task, ".", tmp_path / "workspaces")
    session_plan = build_session_plan(symphony_task, workspace_plan, schema_dir)

    packet = map_symphony_task_to_codex_packet(symphony_task, workspace_plan, session_plan)

    assert packet["requests"]["initialize"]["method"] == "initialize"
    assert packet["requests"]["thread_start"]["method"] == "thread/start"
    assert packet["requests"]["turn_start_template"]["method"] == "turn/start"
    assert packet["safety"]["real_app_server_started"] is False
