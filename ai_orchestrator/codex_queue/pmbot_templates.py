from __future__ import annotations

import copy
from datetime import datetime, timezone
from typing import Any

from .files import validate_task_id
from .schema import default_packet

PMBOT_TEMPLATE_SCHEMA_VERSION = "pmbot_task_template.v1"
PMBOT_PROJECT = "PMBOT"
WEATHER_SOURCE_MONITORING_TEMPLATE = "weather-source-monitoring"
SUPPORTED_PMBOT_TEMPLATES = (WEATHER_SOURCE_MONITORING_TEMPLATE,)

WEATHER_SOURCE_MONITORING_TASK_ID = (
    "PMBOT-PAPERLIVE-010W-002-WEATHER-OUTCOME-SOURCE-MONITORING-PLAN-RUNNER-NO-TRADE"
)

PMBOT_REQUIRED_FORBIDDEN_ACTIONS = (
    "No wallet/private keys",
    "No orders",
    "No trading endpoints",
    "No OpenRouter calls",
    "No Polymarket API calls",
    "No authenticated endpoints",
    "No runtime/dispatcher/run_codex changes",
    "No background worker",
    "No scheduler execution",
    "No browser automation",
    "No destructive commands",
    "No git add .",
    "No git add -A",
    "No git add --all",
    "No force push",
    "No probability / EV / edge / confidence / side selection",
    "No buy/sell/hold/enter/exit recommendations",
    "No market-action guidance",
)

PMBOT_WEATHER_VALIDATION_COMMANDS = (
    "python -m compileall pm_bot tests",
    "pytest pm_bot/tests/test_weather_source_monitoring_plan_runner.py",
)

PMBOT_ALLOWED_ACTIONS = (
    "Inspect local files under the allowed paths before editing.",
    "Add deterministic local code, tests, fixtures, or docs only for weather outcome/source monitoring plan-runner support.",
    "Use local fixtures, local sample data, and operator-reviewed artifacts only.",
    "Run only the listed local validation commands.",
    "Return a strict result JSON packet for operator review.",
)

PMBOT_WEATHER_ALLOWED_PATHS = (
    "pm_bot/weather/",
    "pm_bot/tests/",
    "tests/",
    "docs/",
)

PMBOT_WEATHER_FORBIDDEN_PATHS = (
    ".env",
    ".env.*",
    ".git/",
    ".codex/",
    "runtime/",
    "dispatcher/",
    "run_codex/",
    "pm_bot/llm/",
    "pm_bot/wallet/",
    "pm_bot/trading/",
    "pm_bot/orders/",
    "agent_tasks/running/",
)


def build_pmbot_task_packet(
    task_id: str,
    template: str,
    *,
    repo_root: str = ".",
    base_branch: str = "master",
    expected_head: str | None = None,
) -> dict[str, Any]:
    safe_task_id = validate_task_id(task_id)
    if template != WEATHER_SOURCE_MONITORING_TEMPLATE:
        raise ValueError(f"unsupported PMBOT template: {template}")

    clean_expected_head = expected_head.strip() if isinstance(expected_head, str) else expected_head
    if clean_expected_head == "":
        clean_expected_head = None

    packet = default_packet()
    packet.update(
        {
            "task_id": safe_task_id,
            "title": "PMBOT weather outcome source monitoring plan runner",
            "status": "inbox",
            "created_by": "operator_cli",
            "created_at": _utc_iso(),
            "approved_by": None,
            "approved_at": None,
            "priority": "normal",
            "project": PMBOT_PROJECT,
            "task_template": {
                "schema_version": PMBOT_TEMPLATE_SCHEMA_VERSION,
                "name": template,
                "project": PMBOT_PROJECT,
            },
            "task_type": "local_code_tests",
            "objective": (
                "Prepare a deterministic local PMBOT weather outcome/source monitoring plan runner "
                "with operator review and local validation only."
            ),
            "summary": (
                "Create local PMBOT weather outcome/source monitoring plan-runner support with fixtures, "
                "tests, docs, and explicit operator review boundaries."
            ),
            "instructions": [
                "Inspect local PMBOT files under the allowed paths before editing.",
                "Build only deterministic local plan-runner support for weather outcome/source monitoring using fixtures or static test data.",
                "Keep the implementation operator-reviewed and local-only; write docs and tests for the exact behavior.",
                "Do not use network calls.",
                "Do not call OpenRouter.",
                "Do not call Polymarket API.",
                "Do not touch wallet code.",
                "Do not create orders.",
                "Do not add scheduler execution, background worker support, runtime changes, dispatcher changes, run_codex changes, browser automation, or authenticated endpoint use.",
                "Do not add probability, EV, edge, confidence, side-selection, recommendation, or market-action output.",
                "Do not add buy, sell, hold, enter, or exit recommendations.",
                "Do not use git add ., git add -A, git add --all, force push, or destructive commands.",
                "Return a strict result JSON packet that follows the result contract expectations.",
            ],
            "safety_boundaries": list(PMBOT_REQUIRED_FORBIDDEN_ACTIONS),
            "explicit_safety_boundaries": list(PMBOT_REQUIRED_FORBIDDEN_ACTIONS),
            "allowed_actions": list(PMBOT_ALLOWED_ACTIONS),
            "forbidden_actions": list(PMBOT_REQUIRED_FORBIDDEN_ACTIONS),
            "acceptance_checks": list(PMBOT_WEATHER_VALIDATION_COMMANDS),
            "validation_commands": list(PMBOT_WEATHER_VALIDATION_COMMANDS),
            "expected_outputs": [
                "Local PMBOT weather monitoring plan-runner code, tests, or docs under allowed paths.",
                "Focused validation output for the listed commands.",
                "Strict result JSON packet for operator review.",
            ],
            "result_contract_expectations": _result_contract_expectations(safe_task_id),
            "operator_notes": (
                "Generated by operator_cli create-pmbot-task from weather-source-monitoring. "
                "Review the inbox packet before approval."
            ),
        }
    )
    packet["source"] = {
        "origin": "operator_cli_pmbot_template",
        "reference": template,
    }
    packet["symphony_mapping"] = {
        "issue_id": safe_task_id,
        "workspace_key": safe_task_id.lower(),
        "proof_of_work_required": True,
        "human_review_required": True,
    }
    packet["repo"] = {
        "repo_root": repo_root,
        "base_branch": base_branch,
        "target_branch": None,
        "expected_head": clean_expected_head,
        "allowed_paths": list(PMBOT_WEATHER_ALLOWED_PATHS),
        "forbidden_paths": list(PMBOT_WEATHER_FORBIDDEN_PATHS),
    }
    packet["risk_flags"] = {key: False for key in packet["risk_flags"]}
    return packet


def example_pmbot_weather_task_packet() -> dict[str, Any]:
    packet = build_pmbot_task_packet(
        WEATHER_SOURCE_MONITORING_TASK_ID,
        WEATHER_SOURCE_MONITORING_TEMPLATE,
        repo_root=".",
        base_branch="master",
        expected_head=None,
    )
    example = copy.deepcopy(packet)
    example["created_at"] = None
    example["created_by"] = "operator"
    example["operator_notes"] = (
        "Safe example only. Create a fresh inbox packet with operator_cli create-pmbot-task before approval."
    )
    return example


def _result_contract_expectations(task_id: str) -> dict[str, Any]:
    return {
        "schema_version": "codex_task_result.v1",
        "task_id": task_id,
        "status_values": ["completed", "partial", "blocked", "failed"],
        "required_top_level_fields": [
            "schema_version",
            "task_id",
            "status",
            "completed_by",
            "completed_at",
            "summary",
            "files_created",
            "files_modified",
            "files_deleted",
            "commands_run",
            "validation_results",
            "acceptance_checks_passed",
            "safety_confirmation",
            "operator_review_notes",
            "next_recommended_action",
        ],
        "required_safety_confirmation": {
            "network_calls_performed": 0,
            "credentials_accessed": False,
            "wallet_or_trading_touched": False,
            "runtime_or_dispatcher_touched": False,
            "background_worker_added": False,
            "scheduler_added": False,
            "telegram_or_openclaw_added": False,
            "openrouter_calls_performed": 0,
            "polymarket_api_calls_performed": 0,
            "codex_app_server_used": False,
            "destructive_commands_used": False,
        },
        "additional_expectations": [
            "Report every command that was run.",
            "Set acceptance_checks_passed to false unless the listed validation commands passed.",
            "Use status blocked or partial when a safety boundary prevents completion.",
            "Do not include probability, EV, edge, confidence, side selection, or market-action guidance.",
        ],
    }


def _utc_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
