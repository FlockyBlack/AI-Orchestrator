from __future__ import annotations

from ai_orchestrator.codex_queue.result_schema import (
    DEFAULT_RESULT,
    REQUIRED_SAFETY_FIELDS,
    REQUIRED_TOP_LEVEL_FIELDS,
    SCHEMA_VERSION,
    STATUS_VALUES,
    default_result,
)


def test_result_schema_constants_match_result_v1() -> None:
    assert SCHEMA_VERSION == "codex_task_result.v1"
    assert DEFAULT_RESULT["schema_version"] == SCHEMA_VERSION
    assert set(STATUS_VALUES) == {"completed", "partial", "blocked", "failed"}
    assert "safety_confirmation" in REQUIRED_TOP_LEVEL_FIELDS
    assert "network_calls_performed" in REQUIRED_SAFETY_FIELDS


def test_default_result_is_deep_copied() -> None:
    result = default_result()
    result["files_created"].append("docs/example.md")
    result["safety_confirmation"]["credentials_accessed"] = True

    assert DEFAULT_RESULT["files_created"] == []
    assert DEFAULT_RESULT["safety_confirmation"]["credentials_accessed"] is False
