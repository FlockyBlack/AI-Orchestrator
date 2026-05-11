from __future__ import annotations

from ai_orchestrator.codex_queue.plan_contract import PlanContract
from ai_orchestrator.codex_queue.result_acceptance_policy import evaluate_task_result, reject_forbidden_claims
from codex_plan_helpers import minimal_plan


def test_acceptance_requires_validation_and_safety_ok() -> None:
    plan = PlanContract.from_dict(minimal_plan(1))
    task = plan.tasks[0]
    payload = {
        "task_id": task.task_id,
        "status": "completed",
        "validation_passed": True,
        "safety_ok": True,
        "safety_boundaries_acknowledged": ["local_only"],
    }

    decision = evaluate_task_result(task, payload, plan.safety_boundaries)

    assert decision.accepted is True
    assert decision.status == "accepted"


def test_acceptance_rejects_forbidden_claims() -> None:
    plan = PlanContract.from_dict(minimal_plan(1))
    task = plan.tasks[0]
    payload = {
        "task_id": task.task_id,
        "status": "completed",
        "validation_passed": True,
        "safety_ok": True,
        "wallet_used": True,
    }

    decision = evaluate_task_result(task, payload, plan.safety_boundaries)

    assert decision.accepted is False
    assert decision.status == "failed"


def test_reject_forbidden_claims_scans_strings() -> None:
    errors = reject_forbidden_claims({"summary": "real order submitted"})

    assert errors
