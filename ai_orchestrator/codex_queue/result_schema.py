from __future__ import annotations

import copy
from typing import Any

SCHEMA_VERSION = "codex_task_result.v1"

STATUS_VALUES = (
    "completed",
    "partial",
    "blocked",
    "failed",
)

FILE_LIST_FIELDS = (
    "files_created",
    "files_modified",
    "files_deleted",
)

LIST_FIELDS = (
    *FILE_LIST_FIELDS,
    "commands_run",
    "validation_results",
)

SAFETY_COUNT_FIELDS = (
    "network_calls_performed",
    "openrouter_calls_performed",
    "polymarket_api_calls_performed",
)

SAFETY_BOOLEAN_FIELDS = (
    "credentials_accessed",
    "wallet_or_trading_touched",
    "runtime_or_dispatcher_touched",
    "background_worker_added",
    "scheduler_added",
    "telegram_or_openclaw_added",
    "codex_app_server_used",
    "destructive_commands_used",
)

DANGEROUS_SAFETY_FLAGS = SAFETY_BOOLEAN_FIELDS

REQUIRED_TOP_LEVEL_FIELDS = (
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
)

REQUIRED_SAFETY_FIELDS = (
    "network_calls_performed",
    "credentials_accessed",
    "wallet_or_trading_touched",
    "runtime_or_dispatcher_touched",
    "background_worker_added",
    "scheduler_added",
    "telegram_or_openclaw_added",
    "openrouter_calls_performed",
    "polymarket_api_calls_performed",
    "codex_app_server_used",
    "destructive_commands_used",
)

DEFAULT_RESULT: dict[str, Any] = {
    "schema_version": SCHEMA_VERSION,
    "task_id": "ORCH-EXAMPLE-001",
    "status": "completed",
    "completed_by": "manual_codex_handoff",
    "completed_at": None,
    "summary": "Short summary of work performed",
    "files_created": [],
    "files_modified": [],
    "files_deleted": [],
    "commands_run": [],
    "validation_results": [],
    "acceptance_checks_passed": True,
    "safety_confirmation": {
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
    "operator_review_notes": "",
    "next_recommended_action": "",
}


def default_result() -> dict[str, Any]:
    return copy.deepcopy(DEFAULT_RESULT)
