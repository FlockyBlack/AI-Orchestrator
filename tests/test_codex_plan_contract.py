from __future__ import annotations

from pathlib import Path

from ai_orchestrator.codex_queue.plan_contract import load_plan_contract, validate_plan_contract
from codex_plan_helpers import minimal_plan, write_plan


def test_valid_plan_loads_and_validates(tmp_path: Path) -> None:
    path = write_plan(tmp_path / "plan.json")
    plan = load_plan_contract(path)
    result = validate_plan_contract(plan)

    assert plan.plan_id == "test_plan"
    assert result.valid is True
    assert result.task_count == 3


def test_pmbot_plan_to_050_validates() -> None:
    plan = load_plan_contract("agent_tasks/plans/pmbot_master_plan_to_050.v1.json")
    result = validate_plan_contract(plan)

    assert result.valid is True
    assert result.task_count == 29
    assert plan.tasks[-1].task_id == "PMBOT-TRADING-MVP-050-SUPERVISED-PAPER-MVP-RELEASE-CHECKPOINT"


def test_duplicate_task_rejected(tmp_path: Path) -> None:
    payload = minimal_plan(2)
    payload["tasks"][1]["task_id"] = payload["tasks"][0]["task_id"]
    path = write_plan(tmp_path / "duplicate.json", payload)

    result = validate_plan_contract(load_plan_contract(path))

    assert result.valid is False
    assert any("duplicate task ID" in error for error in result.errors)


def test_dependency_cycle_rejected(tmp_path: Path) -> None:
    payload = minimal_plan(2)
    payload["tasks"][0]["dependencies"] = [payload["tasks"][1]["task_id"]]
    path = write_plan(tmp_path / "cycle.json", payload)

    result = validate_plan_contract(load_plan_contract(path))

    assert result.valid is False
    assert any("dependency cycle" in error for error in result.errors)


def test_forbidden_action_rejected(tmp_path: Path) -> None:
    payload = minimal_plan(1)
    payload["tasks"][0]["description"] = "Submit real order against a live market."
    path = write_plan(tmp_path / "danger.json", payload)

    result = validate_plan_contract(load_plan_contract(path))

    assert result.valid is False
    assert any("forbidden action" in error for error in result.errors)
