from __future__ import annotations

import pytest

from ai_orchestrator.codex_queue.result_schema import default_result
from ai_orchestrator.codex_queue.result_validator import validate_result


def _valid_result() -> dict:
    result = default_result()
    result["task_id"] = "ORCH-RESULT-TEST"
    result["summary"] = "Manual result summary."
    return result


def test_valid_result_packet_passes_validation() -> None:
    result = validate_result(_valid_result())

    assert result.valid is True
    assert result.errors == ()


def test_missing_required_field_fails_validation() -> None:
    packet = _valid_result()
    packet.pop("summary")

    result = validate_result(packet)

    assert result.valid is False
    assert "missing required field: summary" in result.errors


def test_unsafe_safety_flag_blocks() -> None:
    packet = _valid_result()
    packet["safety_confirmation"]["credentials_accessed"] = True

    result = validate_result(packet)

    assert result.valid is False
    assert "safety_confirmation.credentials_accessed must be false" in result.errors


def test_network_calls_performed_blocks() -> None:
    packet = _valid_result()
    packet["safety_confirmation"]["network_calls_performed"] = 1

    result = validate_result(packet)

    assert result.valid is False
    assert "safety_confirmation.network_calls_performed must be 0" in result.errors


def test_openrouter_calls_performed_blocks() -> None:
    packet = _valid_result()
    packet["safety_confirmation"]["openrouter_calls_performed"] = 1

    result = validate_result(packet)

    assert result.valid is False
    assert "safety_confirmation.openrouter_calls_performed must be 0" in result.errors


def test_polymarket_api_calls_performed_blocks() -> None:
    packet = _valid_result()
    packet["safety_confirmation"]["polymarket_api_calls_performed"] = 1

    result = validate_result(packet)

    assert result.valid is False
    assert "safety_confirmation.polymarket_api_calls_performed must be 0" in result.errors


def test_files_deleted_non_empty_blocks_unless_failed_or_blocked() -> None:
    packet = _valid_result()
    packet["files_deleted"] = ["docs/old.md"]

    result = validate_result(packet)

    assert result.valid is False
    assert "files_deleted must be empty unless status is blocked or failed" in result.errors


@pytest.mark.parametrize("status", ["failed", "blocked"])
def test_files_deleted_non_empty_allowed_for_failed_or_blocked_status(status: str) -> None:
    packet = _valid_result()
    packet["status"] = status
    packet["files_deleted"] = ["docs/not-actually-deleted.md"]

    result = validate_result(packet)

    assert result.valid is True
