from __future__ import annotations

import json
from pathlib import Path

from pm_bot.practical.saved_public_evidence_packet import validate_saved_public_evidence_packet

FIXTURE_DIR = Path("pm_bot/tests/fixtures/public_read_only_fetch_prep")


def _load(name: str) -> dict:
    return json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))


def test_valid_saved_evidence_packet_validates() -> None:
    packet = _load("saved_public_evidence_packet.fixture.json")

    validation = validate_saved_public_evidence_packet(packet)

    assert validation["valid"] is True
    assert packet["live_network_used"] is False
    assert packet["safe_for_replay"] is True


def test_stale_evidence_is_marked_stale() -> None:
    packet = _load("saved_public_evidence_packet.stale.json")

    validation = validate_saved_public_evidence_packet(packet)

    assert validation["valid"] is True
    assert packet["freshness_status"] == "stale"
    assert "evidence is marked stale" in validation["warnings"]


def test_contradictory_evidence_has_contradiction_candidates() -> None:
    packet = _load("saved_public_evidence_packet.contradictory.json")

    validation = validate_saved_public_evidence_packet(packet)

    assert validation["valid"] is True
    assert packet["contradiction_candidates"]
    assert "evidence includes contradiction candidates" in validation["warnings"]


def test_saved_evidence_safety_flags_remain_safe() -> None:
    packet = _load("saved_public_evidence_packet.fixture.json")

    assert packet["auth_used"] is False
    assert packet["credentials_used"] is False
    assert packet["wallet_or_private_key_access"] is False
    assert packet["orders_or_trading_actions"] is False
