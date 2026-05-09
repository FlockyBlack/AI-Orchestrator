from __future__ import annotations

import copy
import re
from typing import Any

SCHEMA_VERSION = "codex_task_packet.v1"

STATUS_VALUES = (
    "inbox",
    "approved",
    "planned",
    "running",
    "review",
    "done",
    "blocked",
)

PRIORITY_VALUES = ("low", "normal", "high")

TASK_TYPE_VALUES = (
    "local_docs_only",
    "local_code_tests",
    "local_artifact_generation",
    "needs_network_approval",
    "needs_runtime_approval",
    "needs_external_tracker",
    "blocked_sensitive",
    "blocked_trading",
    "blocked_destructive",
)

MVP_ALLOWED_TASK_TYPES = (
    "local_docs_only",
    "local_code_tests",
    "local_artifact_generation",
)

RISK_FLAG_FIELDS = (
    "requires_network",
    "requires_credentials",
    "touches_trading",
    "touches_wallet",
    "touches_runtime",
    "touches_dispatcher",
    "allows_background_worker",
    "uses_codex_app_server",
    "requires_external_tracker",
)

HARD_BLOCK_RISK_FLAGS = (
    "requires_credentials",
    "touches_trading",
    "touches_wallet",
    "allows_background_worker",
    "uses_codex_app_server",
)

SPECIAL_APPROVAL_RISK_FLAGS = (
    "requires_network",
    "touches_runtime",
    "touches_dispatcher",
    "requires_external_tracker",
)

QUEUE_DIRECTORIES = (
    "inbox",
    "approved",
    "planned",
    "running",
    "review",
    "done",
    "blocked",
    "templates",
    "reports",
)

REQUIRED_TOP_LEVEL_FIELDS = (
    "schema_version",
    "task_id",
    "title",
    "status",
    "created_by",
    "created_at",
    "approved_by",
    "approved_at",
    "priority",
    "source",
    "symphony_mapping",
    "repo",
    "task_type",
    "summary",
    "instructions",
    "safety_boundaries",
    "acceptance_checks",
    "expected_outputs",
    "risk_flags",
    "operator_notes",
)

TASK_ID_RE = re.compile(r"^[A-Z0-9][A-Z0-9_-]*$")

DEFAULT_PACKET: dict[str, Any] = {
    "schema_version": SCHEMA_VERSION,
    "task_id": "ORCH-EXAMPLE-001",
    "title": "Short task title",
    "status": "inbox",
    "created_by": "operator",
    "created_at": None,
    "approved_by": None,
    "approved_at": None,
    "priority": "normal",
    "source": {
        "origin": "manual",
        "reference": "",
    },
    "symphony_mapping": {
        "issue_id": None,
        "workspace_key": None,
        "proof_of_work_required": True,
        "human_review_required": True,
    },
    "repo": {
        "repo_root": ".",
        "base_branch": "main",
        "target_branch": None,
        "allowed_paths": [],
        "forbidden_paths": [],
    },
    "task_type": "local_code_tests",
    "summary": "What should be done",
    "instructions": [
        "Concrete instruction",
    ],
    "safety_boundaries": [
        "No network calls",
        "No credentials",
        "No trading",
    ],
    "acceptance_checks": [
        "python -m compileall ai_orchestrator tests",
    ],
    "expected_outputs": [],
    "risk_flags": {
        "requires_network": False,
        "requires_credentials": False,
        "touches_trading": False,
        "touches_wallet": False,
        "touches_runtime": False,
        "touches_dispatcher": False,
        "allows_background_worker": False,
        "uses_codex_app_server": False,
        "requires_external_tracker": False,
    },
    "operator_notes": "",
}


def default_packet() -> dict[str, Any]:
    return copy.deepcopy(DEFAULT_PACKET)

