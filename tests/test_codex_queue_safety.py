from __future__ import annotations

import pytest

from ai_orchestrator.codex_queue.schema import (
    HARD_BLOCK_RISK_FLAGS,
    SPECIAL_APPROVAL_RISK_FLAGS,
    default_packet,
)
from ai_orchestrator.codex_queue.safety import classify_packet


def _approved_packet() -> dict:
    packet = default_packet()
    packet["status"] = "approved"
    packet["approved_by"] = "operator"
    packet["approved_at"] = "2026-05-09T00:00:00Z"
    return packet


@pytest.mark.parametrize("flag", HARD_BLOCK_RISK_FLAGS)
def test_hard_block_risk_flags_block(flag: str) -> None:
    packet = _approved_packet()
    packet["risk_flags"][flag] = True

    classification = classify_packet(packet)

    assert classification.allowed is False
    assert classification.blocked is True
    assert classification.status == "blocked"
    assert flag in classification.hard_block_flags


@pytest.mark.parametrize("flag", SPECIAL_APPROVAL_RISK_FLAGS)
def test_special_approval_flags_are_not_allowed_by_mvp(flag: str) -> None:
    packet = _approved_packet()
    packet["risk_flags"][flag] = True

    classification = classify_packet(packet)

    assert classification.allowed is False
    assert classification.requires_special_approval is True
    assert classification.status == "requires_special_approval"
    assert flag in classification.special_approval_flags


def test_allowed_local_code_tests_approved_task_is_allowed() -> None:
    classification = classify_packet(_approved_packet())

    assert classification.allowed is True
    assert classification.status == "allowed"
    assert classification.blocked is False


def test_same_packet_with_inbox_status_is_not_allowed_to_run() -> None:
    packet = _approved_packet()
    packet["status"] = "inbox"

    classification = classify_packet(packet)

    assert classification.allowed is False
    assert classification.status == "not_approved"


def test_dangerous_trading_task_is_blocked_by_text_scan() -> None:
    packet = _approved_packet()
    packet["summary"] = "Add logic to place order and trade automatically."

    classification = classify_packet(packet)

    assert classification.allowed is False
    assert classification.blocked is True
    assert classification.status == "blocked"
    assert "place order" in classification.forbidden_keywords
    assert "trade" in classification.forbidden_keywords


def test_safety_boundaries_no_trading_does_not_itself_block() -> None:
    packet = _approved_packet()
    packet["safety_boundaries"] = [
        "No trading",
        "No wallet",
        "Do NOT call OpenRouter",
        "Do NOT use credentials",
    ]

    classification = classify_packet(packet)

    assert classification.allowed is True
    assert classification.forbidden_keywords == ()


@pytest.mark.parametrize(
    "instruction",
    [
        "Do not call OpenRouter",
        "No trading",
        "Do not touch wallet code",
        "Do not modify dispatcher",
        "No scheduler",
        "No background worker",
        "No OpenClaw integration",
        "No Polymarket API calls",
    ],
)
def test_negated_safety_instruction_text_does_not_block_by_itself(instruction: str) -> None:
    packet = _approved_packet()
    packet["instructions"] = [instruction]

    classification = classify_packet(packet)

    assert classification.allowed is True
    assert classification.forbidden_keywords == ()


@pytest.mark.parametrize(
    ("instruction", "keyword"),
    [
        ("call OpenRouter", "openrouter"),
        ("use api key", "api key"),
        ("touch wallet", "wallet"),
        ("place order", "place order"),
        ("modify dispatcher", "dispatcher"),
        ("add scheduler", "scheduler"),
        ("start background worker", "background worker"),
    ],
)
def test_non_negated_forbidden_instruction_text_blocks(instruction: str, keyword: str) -> None:
    packet = _approved_packet()
    packet["instructions"] = [instruction]

    classification = classify_packet(packet)

    assert classification.allowed is False
    assert classification.blocked is True
    assert classification.status == "blocked"
    assert keyword in classification.forbidden_keywords
