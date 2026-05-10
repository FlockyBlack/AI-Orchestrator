from __future__ import annotations

import socket
from pathlib import Path

from pm_bot.practical.saved_evidence_replay_adapter import load_saved_evidence_packets, map_saved_evidence_to_source_packets

FIXTURE = Path("pm_bot/tests/fixtures/public_read_only_fetch_prep/saved_public_evidence_packet.fixture.json")


def test_replay_adapter_maps_evidence_to_source_packets_like_structure() -> None:
    packets = load_saved_evidence_packets(str(FIXTURE))
    mapped = map_saved_evidence_to_source_packets(packets)

    assert mapped["replay_mode"] is True
    assert mapped["live_network_used"] is False
    assert len(mapped["source_packets"]) == 1
    source = mapped["source_packets"][0]
    assert source["source_id"] == packets[0]["source_id"]
    assert source["source_category"] == packets[0]["source_category"]
    assert source["freshness_status"] == packets[0]["freshness_status"]
    assert source["known_limitations"] == packets[0]["limitations"]


def test_replay_adapter_needs_no_live_fetch(monkeypatch) -> None:
    def blocked(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise AssertionError("network access is not allowed")

    monkeypatch.setattr(socket, "create_connection", blocked)

    packets = load_saved_evidence_packets(str(FIXTURE))
    mapped = map_saved_evidence_to_source_packets(packets)

    assert mapped["live_network_used"] is False
    assert mapped["safety_summary"]["wallet_or_private_key_access"] is False
