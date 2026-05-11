from __future__ import annotations

from pathlib import Path

from ai_orchestrator.codex_queue.codex_execution_packet import (
    create_execution_packet_for_next_task,
    render_execution_prompt,
)
from ai_orchestrator.codex_queue.codex_executor_contract import validate_execution_packet
from ai_orchestrator.codex_queue.plan_contract import load_plan_contract
from ai_orchestrator.codex_queue.plan_run_state import PlanRunState, save_state
from ai_orchestrator.codex_queue.plan_to_queue import create_queue_from_plan
from codex_plan_helpers import write_plan


def test_codex_packet_includes_subagent_plan_and_memory_context(tmp_path: Path) -> None:
    plan_path = write_plan(tmp_path / "plan.json")
    queue_root = tmp_path / "agent_tasks"
    queue = create_queue_from_plan(plan_path, queue_root, run_id="RUN1")
    plan = load_plan_contract(plan_path)
    state = PlanRunState.create("RUN1", plan.plan_id, queue_manifest_path=queue.queue_paths["manifest"])
    save_state(state, queue.queue_paths["state_path"])

    packet = create_execution_packet_for_next_task("RUN1", queue_root)
    validation = validate_execution_packet(packet)
    prompt = render_execution_prompt(packet)

    assert validation.valid, validation.errors
    assert packet.agents_md_path == "AGENTS.md"
    assert "Scout" in packet.subagent_plan
    assert "Reviewer" in packet.role_assignments
    assert "memory-bank/activeContext.md" in packet.memory_context_paths
    assert "AGENTS.md" in prompt
    assert "Governed Subagent Workflow" in prompt
    assert "Scout" in prompt
    assert "Integrator" in prompt
    assert "Do not invent success" in prompt
