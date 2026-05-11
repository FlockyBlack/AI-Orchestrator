from __future__ import annotations

from ai_orchestrator.symphony_adapter.symphony_task_contract import (
    SymphonyAcceptancePolicy,
    SymphonyProofRequirement,
    SymphonyTask,
    proof_requirements_from_task,
)


def test_symphony_task_round_trip_preserves_contract_fields() -> None:
    task = SymphonyTask(
        task_id="TEST-TASK-001",
        title="Test task",
        description="Safe local task.",
        source_plan_id="plan",
        source_run_id="run",
        dependencies=("TEST-TASK-000",),
        allowed_paths=("docs/",),
        forbidden_actions=("unsafe git staging", "wallet"),
        acceptance_gates=("tests pass",),
        expected_artifacts=("docs/result.md",),
        max_retries=2,
        safety_boundaries=("local_only",),
        proof_requirements=(SymphonyProofRequirement("proof", "Proof required"),),
        acceptance_policy=SymphonyAcceptancePolicy(gates=("tests pass",), expected_artifacts=("docs/result.md",)),
    )

    payload = task.to_dict()
    restored = SymphonyTask.from_dict(payload)

    assert restored.task_id == "TEST-TASK-001"
    assert restored.forbidden_actions == ("unsafe git staging", "wallet")
    assert restored.acceptance_policy.require_safety_ok is True
    assert restored.proof_requirements[0].proof_id == "proof"


def test_proof_requirements_are_derived_from_gates_and_artifacts() -> None:
    requirements = proof_requirements_from_task(("validation passes",), ("docs/result.md",))

    assert [item.proof_id for item in requirements] == ["acceptance_gate_1", "expected_artifact_1"]
    assert requirements[1].evidence_paths == ("docs/result.md",)
