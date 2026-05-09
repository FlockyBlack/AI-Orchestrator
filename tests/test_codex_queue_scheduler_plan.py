from __future__ import annotations

import json
from pathlib import Path

from ai_orchestrator.codex_queue.scheduler_plan import generate_scheduler_readiness_plan


def test_scheduler_plan_writes_latest_json_and_markdown(tmp_path: Path) -> None:
    queue_root = tmp_path / "agent_tasks"

    report = generate_scheduler_readiness_plan(queue_root)

    assert report["schema_version"] == "codex_scheduler_readiness_plan.v1"
    assert report["status"] == "ok"
    assert (queue_root / "reports" / "latest_scheduler_plan.json").exists()
    assert (queue_root / "reports" / "latest_scheduler_plan.md").exists()


def test_scheduler_plan_states_scheduler_was_not_registered(tmp_path: Path) -> None:
    queue_root = tmp_path / "agent_tasks"

    report = generate_scheduler_readiness_plan(queue_root)
    payload = json.loads((queue_root / "reports" / "latest_scheduler_plan.json").read_text(encoding="utf-8"))

    assert report["scheduler_registered"] is False
    assert report["real_scheduler_registered"] is False
    assert report["would_register_scheduler"] is False
    assert payload["scheduler_registered"] is False
    assert "No scheduler was registered" in (
        queue_root / "reports" / "latest_scheduler_plan.md"
    ).read_text(encoding="utf-8")


def test_scheduler_plan_includes_required_safety_gates(tmp_path: Path) -> None:
    queue_root = tmp_path / "agent_tasks"

    report = generate_scheduler_readiness_plan(queue_root)

    gate_ids = {gate["gate_id"] for gate in report["required_safety_gates"]}
    assert {
        "queue_health_available",
        "night_dry_run_available",
        "git_safety_available",
        "result_ingestion_available",
        "morning_report_available",
        "max_task_cap",
        "lock_file_discipline",
        "no_network_by_default",
        "no_credentials",
        "no_automatic_codex_execution_without_approval",
        "explicit_operator_approval",
    }.issubset(gate_ids)
    assert any(gate["gate_id"] == "explicit_operator_approval" and not gate["satisfied"] for gate in report["required_safety_gates"])
