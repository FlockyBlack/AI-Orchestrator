from __future__ import annotations

from ai_orchestrator.codex_queue.schema import (
    DEFAULT_PACKET,
    HARD_BLOCK_RISK_FLAGS,
    MVP_ALLOWED_TASK_TYPES,
    QUEUE_DIRECTORIES,
    SCHEMA_VERSION,
    SPECIAL_APPROVAL_RISK_FLAGS,
    default_packet,
)


def test_schema_constants_match_task_packet_v1() -> None:
    assert SCHEMA_VERSION == "codex_task_packet.v1"
    assert DEFAULT_PACKET["schema_version"] == SCHEMA_VERSION
    assert "approved" in DEFAULT_PACKET["status"] or DEFAULT_PACKET["status"] == "inbox"
    assert set(MVP_ALLOWED_TASK_TYPES) == {
        "local_docs_only",
        "local_code_tests",
        "local_artifact_generation",
    }
    assert "approved" in QUEUE_DIRECTORIES
    assert "reports" in QUEUE_DIRECTORIES


def test_default_packet_is_deep_copied() -> None:
    packet = default_packet()
    packet["instructions"].append("extra instruction")

    assert DEFAULT_PACKET["instructions"] == ["Concrete instruction"]


def test_risk_flag_sets_are_disjoint() -> None:
    assert not set(HARD_BLOCK_RISK_FLAGS).intersection(SPECIAL_APPROVAL_RISK_FLAGS)

