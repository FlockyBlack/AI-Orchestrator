from __future__ import annotations

import json
from pathlib import Path

from ai_orchestrator.codex_queue.operator_cli import main
from ai_orchestrator.codex_queue.pmbot_templates import (
    PMBOT_PROJECT,
    PMBOT_REQUIRED_FORBIDDEN_ACTIONS,
    PMBOT_WEATHER_VALIDATION_COMMANDS,
    WEATHER_SOURCE_MONITORING_TASK_ID,
    WEATHER_SOURCE_MONITORING_TEMPLATE,
    build_pmbot_task_packet,
    example_pmbot_weather_task_packet,
)
from ai_orchestrator.codex_queue.safety import classify_packet
from ai_orchestrator.codex_queue.validator import validate_packet


def _approved_view(packet: dict) -> dict:
    approved = dict(packet)
    approved["status"] = "approved"
    approved["approved_by"] = "operator"
    approved["approved_at"] = "2026-05-09T00:00:00Z"
    return approved


def test_weather_template_packet_is_valid_and_approvable() -> None:
    packet = build_pmbot_task_packet(
        WEATHER_SOURCE_MONITORING_TASK_ID,
        WEATHER_SOURCE_MONITORING_TEMPLATE,
        repo_root=".",
        base_branch="master",
        expected_head="f8d45d3d45f4f8a9cc629accd88ad1148351ce7f",
    )

    assert validate_packet(packet).valid is True
    assert classify_packet(_approved_view(packet)).allowed is True
    assert packet["project"] == PMBOT_PROJECT
    assert packet["task_template"]["name"] == WEATHER_SOURCE_MONITORING_TEMPLATE
    assert packet["repo"]["repo_root"] == "."
    assert packet["repo"]["base_branch"] == "master"
    assert packet["repo"]["expected_head"] == "f8d45d3d45f4f8a9cc629accd88ad1148351ce7f"


def test_weather_template_includes_required_forbidden_actions() -> None:
    packet = build_pmbot_task_packet(WEATHER_SOURCE_MONITORING_TASK_ID, WEATHER_SOURCE_MONITORING_TEMPLATE)

    for action in PMBOT_REQUIRED_FORBIDDEN_ACTIONS:
        assert action in packet["forbidden_actions"]
        assert action in packet["safety_boundaries"]
        assert action in packet["explicit_safety_boundaries"]


def test_weather_template_includes_required_validation_commands() -> None:
    packet = build_pmbot_task_packet(WEATHER_SOURCE_MONITORING_TASK_ID, WEATHER_SOURCE_MONITORING_TEMPLATE)

    assert packet["validation_commands"] == list(PMBOT_WEATHER_VALIDATION_COMMANDS)
    assert packet["acceptance_checks"] == list(PMBOT_WEATHER_VALIDATION_COMMANDS)
    assert "python -m compileall pm_bot tests" in packet["validation_commands"]
    assert "pytest pm_bot/tests/test_weather_source_monitoring_plan_runner.py" in packet["validation_commands"]


def test_weather_template_does_not_request_unsafe_execution_or_runtime_changes() -> None:
    packet = build_pmbot_task_packet(WEATHER_SOURCE_MONITORING_TASK_ID, WEATHER_SOURCE_MONITORING_TEMPLATE)
    approved = _approved_view(packet)
    classification = classify_packet(approved)

    assert classification.allowed is True
    assert classification.forbidden_keywords == ()
    assert all(value is False for value in packet["risk_flags"].values())
    assert "runtime/" in packet["repo"]["forbidden_paths"]
    assert "dispatcher/" in packet["repo"]["forbidden_paths"]
    assert "run_codex/" in packet["repo"]["forbidden_paths"]
    assert "pm_bot/llm/" in packet["repo"]["forbidden_paths"]
    assert packet["task_type"] == "local_code_tests"


def test_weather_example_packet_passes_existing_queue_validation() -> None:
    packet = example_pmbot_weather_task_packet()

    assert validate_packet(packet).valid is True
    assert classify_packet(_approved_view(packet)).allowed is True


def test_static_weather_example_template_file_is_valid() -> None:
    path = Path("agent_tasks/templates/pmbot_weather_source_monitoring.example.task.json")
    packet = json.loads(path.read_text(encoding="utf-8"))

    assert validate_packet(packet).valid is True
    assert classify_packet(_approved_view(packet)).allowed is True


def test_create_pmbot_task_command_writes_inbox_packet_and_plans_after_approval(tmp_path: Path) -> None:
    queue_root = tmp_path / "agent_tasks"
    task_id = WEATHER_SOURCE_MONITORING_TASK_ID

    create_exit = main(
        [
            "create-pmbot-task",
            "--queue-root",
            str(queue_root),
            "--task-id",
            task_id,
            "--template",
            WEATHER_SOURCE_MONITORING_TEMPLATE,
            "--expected-head",
            "f8d45d3d45f4f8a9cc629accd88ad1148351ce7f",
        ]
    )

    packet_path = queue_root / "inbox" / f"{task_id}.task.json"
    packet = json.loads(packet_path.read_text(encoding="utf-8"))
    assert create_exit == 0
    assert packet["project"] == PMBOT_PROJECT
    assert packet["repo"]["expected_head"] == "f8d45d3d45f4f8a9cc629accd88ad1148351ce7f"
    assert validate_packet(packet).valid is True

    assert main(["approve", "--queue-root", str(queue_root), "--task-id", task_id]) == 0
    assert main(["plan", "--queue-root", str(queue_root)]) == 0

    approved_path = queue_root / "approved" / f"{task_id}.task.json"
    plan_path = queue_root / "planned" / f"{task_id}.plan.json"
    handoff_path = queue_root / "planned" / f"{task_id}.handoff_prompt.md"
    action = json.loads((queue_root / "reports" / "latest_operator_action.json").read_text(encoding="utf-8"))
    assert approved_path.exists()
    assert plan_path.exists()
    assert handoff_path.exists()
    assert action["acceptance_checks_executed"] is False
    assert action["codex_execution_added"] is False
    assert action["codex_app_server_used"] is False
