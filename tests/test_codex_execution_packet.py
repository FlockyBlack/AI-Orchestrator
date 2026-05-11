from __future__ import annotations

import json
from pathlib import Path

from ai_orchestrator.codex_queue.codex_execution_packet import (
    create_execution_packet_for_next_task,
    inspect_execution_packets,
    write_execution_packet,
    write_execution_prompt,
    write_expected_result_template,
)
from ai_orchestrator.codex_queue.plan_contract import load_plan_contract
from ai_orchestrator.codex_queue.plan_run_state import PlanRunState, mark_task_done, save_state
from ai_orchestrator.codex_queue.plan_to_queue import create_queue_from_plan
from codex_plan_helpers import write_plan


def test_create_execution_packet_for_next_runnable_task(tmp_path: Path) -> None:
    plan_path = write_plan(tmp_path / "plan.json")
    queue_root = tmp_path / "agent_tasks"
    queue = create_queue_from_plan(plan_path, queue_root, run_id="RUN1")
    plan = load_plan_contract(plan_path)
    state = PlanRunState.create("RUN1", plan.plan_id, queue_manifest_path=queue.queue_paths["manifest"])
    mark_task_done(state, "TEST-TASK-001")
    save_state(state, queue.queue_paths["state_path"])

    packet = create_execution_packet_for_next_task("RUN1", queue_root)

    assert packet.task_id == "TEST-TASK-002"
    assert packet.adapter_mode == "manual_handoff"


def test_write_packet_prompt_and_template(tmp_path: Path) -> None:
    plan_path = write_plan(tmp_path / "plan.json")
    queue_root = tmp_path / "agent_tasks"
    queue = create_queue_from_plan(plan_path, queue_root, run_id="RUN1")
    plan = load_plan_contract(plan_path)
    state = PlanRunState.create("RUN1", plan.plan_id, queue_manifest_path=queue.queue_paths["manifest"])
    save_state(state, queue.queue_paths["state_path"])
    packet = create_execution_packet_for_next_task("RUN1", queue_root)
    output_dir = Path(packet.prompt_path).parent

    packet_path = write_execution_packet(packet, output_dir)
    prompt_path = write_execution_prompt(packet, output_dir)
    template_path = write_expected_result_template(packet, output_dir)
    inspection = inspect_execution_packets("RUN1", queue_root)
    prompt = prompt_path.read_text(encoding="utf-8")
    template = json.loads(template_path.read_text(encoding="utf-8"))

    assert packet_path.exists()
    assert "Do not use unsafe git staging" in prompt
    assert "Do not create a daemon" in prompt
    assert template["task_id"] == packet.task_id
    assert inspection["packet_count"] == 1
