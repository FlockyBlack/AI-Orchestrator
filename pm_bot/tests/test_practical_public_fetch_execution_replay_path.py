from __future__ import annotations

import json
from pathlib import Path

from pm_bot.practical.controlled_public_fetch_execution import (
    write_analysis_update_candidate_report,
    write_replay_blocked_no_evidence,
)
from pm_bot.practical.saved_evidence_replay_adapter import load_saved_evidence_packets, map_saved_evidence_to_source_packets

FIXTURE = Path("pm_bot/tests/fixtures/public_read_only_fetch_prep/saved_public_evidence_packet.fixture.json")


def test_replay_blocked_artifact_is_created_if_no_evidence(tmp_path: Path) -> None:
    result = write_replay_blocked_no_evidence(tmp_path, blockers=["No evidence was created."])

    assert result["replay_performed"] is False
    assert result["replay_status"] == "blocked_no_evidence"
    assert (tmp_path / "replay_blocked_no_evidence.json").exists()
    assert (tmp_path / "replay_blocked_no_evidence.md").exists()


def test_replay_adapter_can_map_saved_fixture_evidence_packet() -> None:
    packets = load_saved_evidence_packets(str(FIXTURE))
    mapped = map_saved_evidence_to_source_packets(packets)

    assert mapped["replay_mode"] is True
    assert mapped["live_network_used"] is False
    assert mapped["source_packets"][0]["evidence_packet_id"] == packets[0]["evidence_packet_id"]


def test_analysis_update_candidate_report_never_auto_updates_prior_analysis(tmp_path: Path) -> None:
    packets = load_saved_evidence_packets(str(FIXTURE))
    report = write_analysis_update_candidate_report(
        out_dir=tmp_path,
        replay_result={"replay_performed": True, "replay_status": "replayed_saved_evidence"},
        evidence_packets=packets,
        preflight={"blocked_request_count": 0},
    )

    assert report["automatic_update_performed"] is False
    assert report["no_real_trade_decision"] is True
    saved = json.loads((tmp_path / "analysis_update_candidate_report.json").read_text(encoding="utf-8"))
    assert saved["automatic_update_performed"] is False
