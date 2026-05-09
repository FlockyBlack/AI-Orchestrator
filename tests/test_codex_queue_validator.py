from __future__ import annotations

from ai_orchestrator.codex_queue.schema import default_packet
from ai_orchestrator.codex_queue.validator import validate_packet


def _approved_packet() -> dict:
    packet = default_packet()
    packet["status"] = "approved"
    packet["approved_by"] = "operator"
    packet["approved_at"] = "2026-05-09T00:00:00Z"
    return packet


def test_valid_packet_passes_validation() -> None:
    result = validate_packet(_approved_packet())

    assert result.valid is True
    assert result.errors == ()


def test_missing_required_field_fails_validation() -> None:
    packet = _approved_packet()
    packet.pop("title")

    result = validate_packet(packet)

    assert result.valid is False
    assert "missing required field: title" in result.errors


def test_invalid_task_type_fails_validation() -> None:
    packet = _approved_packet()
    packet["task_type"] = "unknown_task_type"

    result = validate_packet(packet)

    assert result.valid is False
    assert any("task_type must be one of" in error for error in result.errors)


def test_approved_packet_requires_proof_of_work_and_human_review() -> None:
    packet = _approved_packet()
    packet["symphony_mapping"]["proof_of_work_required"] = False
    packet["symphony_mapping"]["human_review_required"] = False

    result = validate_packet(packet)

    assert result.valid is False
    assert "symphony_mapping.proof_of_work_required must be true for approved/planned tasks" in result.errors
    assert "symphony_mapping.human_review_required must be true for approved/planned tasks" in result.errors

