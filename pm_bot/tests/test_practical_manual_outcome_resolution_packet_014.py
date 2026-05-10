from __future__ import annotations

import json
from pathlib import Path

from pm_bot.practical.manual_outcome_resolution_packet import (
    packet_claims_real_outcome,
    validate_manual_outcome_resolution_packet,
)

ARTIFACT_DIR = Path("pm_bot/practical/artifacts/manual_outcome_feedback_014")
FIXTURE_DIR = Path("pm_bot/tests/fixtures/manual_outcome_feedback")


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_unresolved_packet_validates() -> None:
    packet = _load(ARTIFACT_DIR / "markets/563650/manual_outcome_resolution_packet.unresolved.json")

    assert validate_manual_outcome_resolution_packet(packet) == []
    assert packet["contract_version"] == "pmbot_manual_outcome_resolution_packet.v1"
    assert packet["outcome_status"] == "unresolved"
    assert packet["paper_hypothesis_result_label"] == "pending"


def test_resolved_aligned_fixture_validates() -> None:
    packet = _load(FIXTURE_DIR / "manual_outcome_resolution_packet.resolved_aligned.fixture.json")

    assert packet["synthetic_fixture"] is True
    assert validate_manual_outcome_resolution_packet(packet) == []
    assert packet["paper_hypothesis_result_label"] == "aligned"


def test_resolved_not_aligned_fixture_validates() -> None:
    packet = _load(FIXTURE_DIR / "manual_outcome_resolution_packet.resolved_not_aligned_missing_evidence.fixture.json")

    assert packet["synthetic_fixture"] is True
    assert validate_manual_outcome_resolution_packet(packet) == []
    assert packet["paper_hypothesis_result_label"] == "not_aligned"


def test_ambiguous_fixture_validates() -> None:
    packet = _load(FIXTURE_DIR / "manual_outcome_resolution_packet.resolved_ambiguous.fixture.json")

    assert packet["synthetic_fixture"] is True
    assert validate_manual_outcome_resolution_packet(packet) == []
    assert packet["outcome_status"] == "ambiguous"


def test_invalid_missing_resolution_source_fails() -> None:
    packet = _load(FIXTURE_DIR / "manual_outcome_resolution_packet.invalid_missing_resolution_source.fixture.json")

    errors = validate_manual_outcome_resolution_packet(packet)

    assert any("resolution_source_reference" in error for error in errors)


def test_unresolved_packet_does_not_invent_outcome() -> None:
    packet = _load(ARTIFACT_DIR / "markets/597964/manual_outcome_resolution_packet.unresolved.json")

    assert packet_claims_real_outcome(packet) is False
    assert packet["actual_outcome_summary"] == ""
    assert packet["resolved_at"] == ""
    assert packet["resolution_source_reference"] == ""
    assert packet["source_evidence_used_for_resolution"] == []


def test_manual_outcome_packet_safety_flags_safe() -> None:
    packet = _load(ARTIFACT_DIR / "markets/598936/manual_outcome_resolution_packet.unresolved.json")
    safety = packet["safety_summary"]

    assert packet["no_real_trade_decision"] is True
    assert packet["orders_or_trading_actions"] is False
    assert packet["wallet_or_private_key_access"] is False
    assert safety["live_network_used"] is False
    assert safety["openrouter_calls_performed"] == 0
    assert safety["new_polymarket_api_calls_performed"] == 0
    assert safety["outcome_resolution_invented"] is False
