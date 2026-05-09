from __future__ import annotations

import json
from pathlib import Path

from ai_orchestrator.codex_queue.operator_cli import main
from ai_orchestrator.codex_queue.pmbot_templates import (
    CRYPTO_MARKET_CLASS_CAPTURE_TEMPLATE,
    PMBOT_NIGHT_BATCH_TASKS,
    PMBOT_NIGHT_BATCH_TASK_IDS,
    PMBOT_NEXT_TWENTY_TASKS,
    PMBOT_NEXT_TWENTY_TASK_IDS,
    PMBOT_PROJECT,
    PMBOT_REQUIRED_FORBIDDEN_ACTIONS,
    PMBOT_SUPERVISED_LIVE_READINESS_TASKS,
    PMBOT_SUPERVISED_LIVE_READINESS_TASK_IDS,
    PMBOT_WEATHER_VALIDATION_COMMANDS,
    SUPPORTED_PMBOT_TEMPLATES,
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


def _intent_text(packet: dict) -> str:
    values: list[str] = [
        packet["summary"],
        packet["operator_notes"],
        *packet["instructions"],
        *packet["expected_outputs"],
        *packet.get("allowed_actions", []),
        *packet.get("safety_boundaries", []),
    ]
    return "\n".join(values).lower()


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


def test_night_batch_templates_cover_requested_task_ids_and_stay_local_only() -> None:
    expected_task_ids = (
        "PMBOT-PAPERLIVE-010W-003-WEATHER-OBSERVATION-REFRESH-LEDGER-NO-TRADE",
        "PMBOT-PAPERLIVE-010W-004-WEATHER-OUTCOME-RECONCILIATION-PLACEHOLDER-NO-TRADE",
        "PMBOT-PAPERLIVE-010W-005-WEATHER-OPERATOR-REVIEW-SURFACE-UPDATE-NO-TRADE",
        "PMBOT-SOURCE-LEDGER-001-UNIFIED-SOURCE-QUALITY-LEDGER-LOCAL-ONLY",
        "PMBOT-SOURCE-LEDGER-002-SOURCE-QUALITY-VALIDATOR-LOCAL-ONLY",
        "PMBOT-PAPERLIVE-DECISION-001-SIMULATED-DECISION-PACKET-SCHEMA-NO-RECOMMENDATIONS",
        "PMBOT-PAPERLIVE-DECISION-002-SIMULATED-DECISION-VALIDATOR-NO-RECOMMENDATIONS",
        "PMBOT-PAPER-ACCOUNTING-001-PAPER-ONLY-ACCOUNTING-LEDGER-LOCAL-ONLY",
        "PMBOT-DASHBOARD-001-LOCAL-OPERATOR-DASHBOARD-SUMMARY",
        "PMBOT-ROADMAP-001-REAL-WALLET-READINESS-BLOCKER-MATRIX",
    )

    assert PMBOT_NIGHT_BATCH_TASK_IDS[: len(expected_task_ids)] == expected_task_ids

    for spec in PMBOT_NIGHT_BATCH_TASKS:
        packet = build_pmbot_task_packet(str(spec["task_id"]), str(spec["template"]))
        text = _intent_text(packet)

        assert str(spec["template"]) in SUPPORTED_PMBOT_TEMPLATES
        assert validate_packet(packet).valid is True
        assert classify_packet(_approved_view(packet)).allowed is True
        assert packet["project"] == PMBOT_PROJECT
        assert packet["task_template"]["name"] == spec["template"]
        assert all(value is False for value in packet["risk_flags"].values())
        assert packet["repo"]["expected_head"] is None
        assert "runtime/" in packet["repo"]["forbidden_paths"]
        assert "dispatcher/" in packet["repo"]["forbidden_paths"]
        assert "run_codex/" in packet["repo"]["forbidden_paths"]
        assert "pm_bot/llm/" in packet["repo"]["forbidden_paths"]
        assert "python -m compileall pm_bot tests" in packet["validation_commands"]
        assert "pytest pm_bot/tests tests/test_codex_queue_pmbot_templates.py" in packet["validation_commands"]
        for forbidden_word in ("buy", "sell", "hold", "enter", "exit"):
            assert forbidden_word not in text


def test_next_twenty_pmbot_templates_cover_requested_task_ids_and_stay_local_only() -> None:
    expected_task_ids = (
        "PMBOT-SOURCE-LEDGER-003-SOURCE-QUALITY-REPORT-SUMMARY-LOCAL-ONLY",
        "PMBOT-SOURCE-LEDGER-004-SOURCE-QUALITY-REGRESSION-FIXTURE-LOCAL-ONLY",
        "PMBOT-PAPERLIVE-DECISION-003-SIMULATED-DECISION-AUDIT-LEDGER-NO-RECOMMENDATIONS",
        "PMBOT-PAPERLIVE-DECISION-004-SIMULATED-DECISION-REPLAY-SUMMARY-NO-RECOMMENDATIONS",
        "PMBOT-PAPER-ACCOUNTING-002-PAPER-ONLY-ACCOUNTING-VALIDATOR-LOCAL-ONLY",
        "PMBOT-PAPER-ACCOUNTING-003-PAPER-ONLY-SESSION-SUMMARY-LOCAL-ONLY",
        "PMBOT-CRYPTO-PILOT-001-CRYPTO-MARKET-CLASS-CAPTURE-TEMPLATE-LOCAL-ONLY",
        "PMBOT-CRYPTO-PILOT-002-CRYPTO-OPERATOR-REVIEW-PROTOCOL-LOCAL-ONLY",
        "PMBOT-CRYPTO-PILOT-003-CRYPTO-PAPERLIVE-OBSERVATION-LEDGER-LOCAL-ONLY",
        "PMBOT-CRYPTO-PILOT-004-CRYPTO-SOURCE-QUALITY-CAPTURE-SURFACE-LOCAL-ONLY",
        "PMBOT-DASHBOARD-002-QUEUE-AND-PAPERLIVE-STATUS-SURFACE",
        "PMBOT-DASHBOARD-003-SOURCE-QUALITY-DASHBOARD-SUMMARY",
        "PMBOT-DASHBOARD-004-PAPER-ACCOUNTING-DASHBOARD-SUMMARY",
        "PMBOT-SAFETY-001-AUTONOMY-GATE-CHECKLIST-LOCAL-ONLY",
        "PMBOT-SAFETY-002-NIGHT-BATCH-POSTRUN-AUDIT-SUMMARY-LOCAL-ONLY",
        "PMBOT-SAFETY-003-FORBIDDEN-ACTION-SCAN-LOCAL-ONLY",
        "PMBOT-ROADMAP-002-PMBOT-LOCAL-TO-SUPERVISED-LIVE-GAP-MATRIX",
        "PMBOT-ROADMAP-003-NEXT-20-TASK-BACKLOG-GENERATOR",
        "PMBOT-OPERATOR-001-MORNING-REVIEW-PACK-LOCAL-ONLY",
        "PMBOT-OPERATOR-002-NIGHT-BATCH-ACCEPTANCE-REPORT-LOCAL-ONLY",
    )

    assert PMBOT_NEXT_TWENTY_TASK_IDS == expected_task_ids
    assert tuple(str(spec["task_id"]) for spec in PMBOT_NEXT_TWENTY_TASKS) == expected_task_ids

    seen_templates: set[str] = set()
    for spec in PMBOT_NEXT_TWENTY_TASKS:
        packet = build_pmbot_task_packet(str(spec["task_id"]), str(spec["template"]))
        text = _intent_text(packet)

        assert str(spec["template"]) in SUPPORTED_PMBOT_TEMPLATES
        assert str(spec["template"]) not in seen_templates
        assert validate_packet(packet).valid is True
        assert classify_packet(_approved_view(packet)).allowed is True
        assert packet["project"] == PMBOT_PROJECT
        assert packet["task_template"]["name"] == spec["template"]
        assert all(value is False for value in packet["risk_flags"].values())
        assert "runtime/" in packet["repo"]["forbidden_paths"]
        assert "dispatcher/" in packet["repo"]["forbidden_paths"]
        assert "run_codex/" in packet["repo"]["forbidden_paths"]
        assert "pm_bot/llm/" in packet["repo"]["forbidden_paths"]
        assert "python -m compileall pm_bot tests" in packet["validation_commands"]
        assert "pytest pm_bot/tests tests/test_codex_queue_pmbot_templates.py" in packet["validation_commands"]
        for forbidden_word in ("buy", "sell", "hold", "enter", "exit"):
            assert forbidden_word not in text
        seen_templates.add(str(spec["template"]))


def test_supervised_live_readiness_templates_cover_requested_task_ids_and_stay_local_only() -> None:
    expected_task_ids = (
        "PMBOT-SUPERVISED-LIVE-001-READ-ONLY-LIVE-DATA-CONTRACT-LOCAL-ONLY",
        "PMBOT-SUPERVISED-LIVE-002-LIVE-DATA-SOURCE-INVENTORY-LOCAL-ONLY",
        "PMBOT-SUPERVISED-LIVE-003-OPERATOR-APPROVAL-GATE-RECORD-LOCAL-ONLY",
        "PMBOT-SUPERVISED-LIVE-004-SUPERVISED-LIVE-STOP-CONDITION-SPEC-LOCAL-ONLY",
        "PMBOT-SUPERVISED-LIVE-005-LIVE-READINESS-EVIDENCE-BUNDLE-LOCAL-ONLY",
        "PMBOT-SOURCE-EVIDENCE-001-SOURCE-INVENTORY-LEDGER-LOCAL-ONLY",
        "PMBOT-SOURCE-EVIDENCE-002-SOURCE-EVIDENCE-LINK-MAP-LOCAL-ONLY",
        "PMBOT-SOURCE-EVIDENCE-003-SOURCE-STALENESS-CHECK-SPEC-LOCAL-ONLY",
        "PMBOT-SOURCE-EVIDENCE-004-SOURCE-CONTRADICTION-LEDGER-LOCAL-ONLY",
        "PMBOT-VALIDATION-001-SAVED-EVIDENCE-REPLAY-BUNDLE-LOCAL-ONLY",
        "PMBOT-VALIDATION-002-CI-SAFE-VALIDATION-SUBSET-LOCAL-ONLY",
        "PMBOT-VALIDATION-003-BATCH-VALIDATION-REPLAY-REPORT-LOCAL-ONLY",
        "PMBOT-SAFETY-004-SENSITIVE-PATH-EXCLUSION-AUDIT-LOCAL-ONLY",
        "PMBOT-SAFETY-005-FORBIDDEN-LANGUAGE-REGRESSION-SUITE-LOCAL-ONLY",
        "PMBOT-SAFETY-006-AUTONOMY-REVIEW-RECORD-LOCAL-ONLY",
        "PMBOT-PAPERLIVE-AUDIT-001-PAPERLIVE-TO-ACCOUNTING-RECONCILIATION-LOCAL-ONLY",
        "PMBOT-PAPERLIVE-AUDIT-002-SIMULATED-DECISION-TO-OUTCOME-REPLAY-LINKS-LOCAL-ONLY",
        "PMBOT-DASHBOARD-005-SUPERVISED-LIVE-READINESS-DASHBOARD-LOCAL-ONLY",
        "PMBOT-OPERATOR-003-SUPERVISED-LIVE-MORNING-REVIEW-CARD-LOCAL-ONLY",
        "PMBOT-ROADMAP-004-REAL-WALLET-GATED-MILESTONE-SEPARATION-LOCAL-ONLY",
    )

    assert PMBOT_SUPERVISED_LIVE_READINESS_TASK_IDS == expected_task_ids
    assert tuple(str(spec["task_id"]) for spec in PMBOT_SUPERVISED_LIVE_READINESS_TASKS) == expected_task_ids

    seen_templates: set[str] = set()
    for spec in PMBOT_SUPERVISED_LIVE_READINESS_TASKS:
        packet = build_pmbot_task_packet(str(spec["task_id"]), str(spec["template"]))
        text = _intent_text(packet)

        assert str(spec["template"]) in SUPPORTED_PMBOT_TEMPLATES
        assert str(spec["template"]) not in seen_templates
        assert validate_packet(packet).valid is True
        assert classify_packet(_approved_view(packet)).allowed is True
        assert packet["project"] == PMBOT_PROJECT
        assert packet["task_template"]["name"] == spec["template"]
        assert all(value is False for value in packet["risk_flags"].values())
        assert "runtime/" in packet["repo"]["forbidden_paths"]
        assert "dispatcher/" in packet["repo"]["forbidden_paths"]
        assert "run_codex/" in packet["repo"]["forbidden_paths"]
        assert "pm_bot/llm/" in packet["repo"]["forbidden_paths"]
        assert "python -m compileall pm_bot tests" in packet["validation_commands"]
        assert "pytest pm_bot/tests tests/test_codex_queue_pmbot_templates.py" in packet["validation_commands"]
        assert "No external service calls." in packet["safety_boundaries"]
        assert "No timed automation or resident process." in packet["safety_boundaries"]
        for forbidden_word in ("buy", "sell", "hold", "enter", "exit"):
            assert forbidden_word not in text
        seen_templates.add(str(spec["template"]))


def test_crypto_market_class_capture_queue_template_matches_local_only_scope() -> None:
    packet = build_pmbot_task_packet(
        "PMBOT-CRYPTO-PILOT-001-CRYPTO-MARKET-CLASS-CAPTURE-TEMPLATE-LOCAL-ONLY",
        CRYPTO_MARKET_CLASS_CAPTURE_TEMPLATE,
    )

    assert validate_packet(packet).valid is True
    assert classify_packet(_approved_view(packet)).allowed is True
    assert packet["task_template"]["name"] == CRYPTO_MARKET_CLASS_CAPTURE_TEMPLATE
    assert packet["title"] == "PMBOT crypto market class capture template"
    assert packet["summary"] == "Prepare a local PMBOT crypto market class capture template for descriptive records."
    assert packet["repo"]["allowed_paths"] == ["docs/", "pm_bot/tests/", "tests/"]
    assert packet["expected_outputs"] == [
        "Crypto market class capture template docs, fixtures, tests, or local artifacts under allowed paths.",
        "A strict result JSON packet for operator review.",
    ]
    assert all(value is False for value in packet["risk_flags"].values())


def test_create_all_pmbot_night_tasks_then_approve_and_plan(tmp_path: Path) -> None:
    queue_root = tmp_path / "agent_tasks"
    for spec in PMBOT_NIGHT_BATCH_TASKS:
        task_id = str(spec["task_id"])
        template = str(spec["template"])
        assert (
            main(
                [
                    "create-pmbot-task",
                    "--queue-root",
                    str(queue_root),
                    "--task-id",
                    task_id,
                    "--template",
                    template,
                    "--expected-head",
                    "603bd0e235594688ce1796b79e9f597a5f9ea465",
                ]
            )
            == 0
        )
        assert (queue_root / "inbox" / f"{task_id}.task.json").exists()

    for task_id in PMBOT_NIGHT_BATCH_TASK_IDS:
        assert main(["approve", "--queue-root", str(queue_root), "--task-id", task_id]) == 0
        assert (queue_root / "approved" / f"{task_id}.task.json").exists()

    assert main(["plan", "--queue-root", str(queue_root)]) == 0
    for task_id in PMBOT_NIGHT_BATCH_TASK_IDS:
        assert (queue_root / "planned" / f"{task_id}.plan.json").exists()
        assert (queue_root / "planned" / f"{task_id}.handoff_prompt.md").exists()


def test_create_all_supervised_live_readiness_tasks_then_approve_and_plan(tmp_path: Path) -> None:
    queue_root = tmp_path / "agent_tasks"
    for spec in PMBOT_SUPERVISED_LIVE_READINESS_TASKS:
        task_id = str(spec["task_id"])
        template = str(spec["template"])
        assert (
            main(
                [
                    "create-pmbot-task",
                    "--queue-root",
                    str(queue_root),
                    "--task-id",
                    task_id,
                    "--template",
                    template,
                    "--expected-head",
                    "603bd0e235594688ce1796b79e9f597a5f9ea465",
                ]
            )
            == 0
        )
        assert (queue_root / "inbox" / f"{task_id}.task.json").exists()

    for task_id in PMBOT_SUPERVISED_LIVE_READINESS_TASK_IDS:
        assert main(["approve", "--queue-root", str(queue_root), "--task-id", task_id]) == 0
        assert (queue_root / "approved" / f"{task_id}.task.json").exists()

    assert main(["plan", "--queue-root", str(queue_root)]) == 0
    for task_id in PMBOT_SUPERVISED_LIVE_READINESS_TASK_IDS:
        assert (queue_root / "planned" / f"{task_id}.plan.json").exists()
        assert (queue_root / "planned" / f"{task_id}.handoff_prompt.md").exists()
