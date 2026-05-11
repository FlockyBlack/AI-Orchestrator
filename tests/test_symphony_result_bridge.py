from __future__ import annotations

from ai_orchestrator.symphony_adapter.symphony_result_bridge import (
    SymphonyResultEnvelope,
    map_symphony_result_to_ai_orchestrator_result,
    map_symphony_result_to_codex_ingestion_payload,
    validate_symphony_result,
)
from ai_orchestrator.symphony_adapter.symphony_task_contract import SymphonyTask


def _task() -> SymphonyTask:
    return SymphonyTask(
        task_id="TEST-TASK-001",
        title="Task",
        description="Safe task.",
        source_plan_id="plan",
        source_run_id="run",
        expected_artifacts=("docs/result.md",),
    )


def test_unsafe_result_is_rejected() -> None:
    result = SymphonyResultEnvelope(
        task_id="TEST-TASK-001",
        status="completed",
        validation_passed=True,
        safety_ok=True,
        safety={"real_order_submitted": True},
    )

    validation = validate_symphony_result(result, _task())

    assert validation["valid"] is False
    assert any("real order submitted" in error for error in validation["errors"])


def test_accepted_result_maps_to_ai_orchestrator_and_ingestion_payload() -> None:
    result = SymphonyResultEnvelope(
        task_id="TEST-TASK-001",
        plan_id="plan",
        run_id="run",
        packet_id="packet",
        status="completed",
        summary="Done.",
        validation_passed=True,
        safety_ok=True,
        artifacts=("docs/result.md",),
        commands_run=("pytest tests/test_example.py",),
        safety={"real_order_submitted": False, "openrouter_used": False},
    )

    validation = validate_symphony_result(result, _task())
    ai_result = map_symphony_result_to_ai_orchestrator_result(result)
    ingestion = map_symphony_result_to_codex_ingestion_payload(result)

    assert validation["valid"] is True
    assert ai_result["task_id"] == "TEST-TASK-001"
    assert ai_result["safety_boundaries_acknowledged"] is True
    assert ingestion["result_payload"]["status"] == "completed"
    assert ingestion["packet_id"] == "packet"
