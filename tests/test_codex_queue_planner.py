from __future__ import annotations

from ai_orchestrator.codex_queue.planner import create_plan, render_handoff_prompt
from ai_orchestrator.codex_queue.schema import default_packet


def _approved_packet() -> dict:
    packet = default_packet()
    packet["status"] = "approved"
    packet["approved_by"] = "operator"
    packet["approved_at"] = "2026-05-09T00:00:00Z"
    packet["repo"]["allowed_paths"] = ["ai_orchestrator/", "tests/"]
    packet["repo"]["forbidden_paths"] = ["runtime/", "pm_bot/", "merchant_pipeline/"]
    packet["acceptance_checks"] = ["python -m compileall ai_orchestrator tests"]
    packet["expected_outputs"] = ["Plan only"]
    return packet


def test_planner_creates_non_executing_plan() -> None:
    packet = _approved_packet()
    plan = create_plan(packet, queue_root="agent_tasks")

    assert plan["task_id"] == packet["task_id"]
    assert plan["would_create_workspace"] is True
    assert plan["allowed_paths"] == ["ai_orchestrator/", "tests/"]
    assert plan["forbidden_paths"] == ["runtime/", "pm_bot/", "merchant_pipeline/"]
    assert plan["codex_execution_command"] is None
    assert plan["codex_app_server_used"] is False
    assert plan["automatic_execution_enabled"] is False
    assert plan["human_review_required"] is True
    assert plan["proof_of_work_required"] is True
    assert plan["handoff_prompt_path"].endswith("agent_tasks\\planned\\ORCH-EXAMPLE-001.handoff_prompt.md") or plan[
        "handoff_prompt_path"
    ].endswith("agent_tasks/planned/ORCH-EXAMPLE-001.handoff_prompt.md")


def test_handoff_prompt_contains_required_safety_and_result_shape() -> None:
    packet = _approved_packet()
    plan = create_plan(packet)
    prompt = render_handoff_prompt(packet, plan)

    assert "task_id: `ORCH-EXAMPLE-001`" in prompt
    assert "Do not use network unless explicitly allowed; this MVP does not allow network use." in prompt
    assert "Do not touch credentials, wallet, trading, payment, runtime, dispatcher" in prompt
    assert "Do not start background processes" in prompt
    assert '"status": "completed|partial|blocked"' in prompt

