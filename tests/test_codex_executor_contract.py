from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

from ai_orchestrator.codex_queue.codex_executor_contract import (
    CodexExecutionPacket,
    build_execution_packet,
    expected_result_schema_for_packet,
    validate_execution_packet,
)
from ai_orchestrator.codex_queue.plan_contract import load_plan_contract
from ai_orchestrator.codex_queue.plan_run_state import PlanRunState, save_state
from ai_orchestrator.codex_queue.plan_to_queue import create_queue_from_plan
from codex_plan_helpers import write_plan


def _packet(tmp_path: Path) -> CodexExecutionPacket:
    plan_path = write_plan(tmp_path / "plan.json")
    queue_root = tmp_path / "agent_tasks"
    queue = create_queue_from_plan(plan_path, queue_root, run_id="RUN1")
    plan = load_plan_contract(plan_path)
    state = PlanRunState.create("RUN1", plan.plan_id, queue_manifest_path=queue.queue_paths["manifest"])
    save_state(state, queue.queue_paths["state_path"])
    manifest = {**json.loads(Path(queue.queue_paths["manifest"]).read_text(encoding="utf-8")), "manifest_path": queue.queue_paths["manifest"]}
    return build_execution_packet(plan.tasks[0], state, manifest, "manual_handoff")


def test_build_execution_packet_validates_safe_packet(tmp_path: Path) -> None:
    packet = _packet(tmp_path)
    validation = validate_execution_packet(packet)

    assert packet.task_id == "TEST-TASK-001"
    assert validation.valid is True
    assert validation.safety_ok is True


def test_packet_validation_rejects_missing_task_id(tmp_path: Path) -> None:
    packet = replace(_packet(tmp_path), task_id="")

    validation = validate_execution_packet(packet)

    assert validation.valid is False
    assert "missing task_id" in validation.errors


def test_packet_validation_rejects_unsafe_adapter_mode(tmp_path: Path) -> None:
    packet = replace(_packet(tmp_path), adapter_mode="uncontrolled_codex_loop")

    validation = validate_execution_packet(packet)

    assert validation.valid is False
    assert any("unsafe adapter mode" in error for error in validation.errors)


def test_expected_result_template_contains_task_id(tmp_path: Path) -> None:
    packet = _packet(tmp_path)

    template = expected_result_schema_for_packet(packet)

    assert template["task_id"] == "TEST-TASK-001"
    assert template["result_payload"]["task_id"] == "TEST-TASK-001"
