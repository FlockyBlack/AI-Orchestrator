from __future__ import annotations

import json
from pathlib import Path

from pm_bot.practical.public_fetch_approval_packet import (
    build_public_fetch_approval_packet,
    render_public_fetch_approval_packet_markdown,
)
from pm_bot.practical.public_fetch_evidence_save_plan import build_public_fetch_evidence_save_plan
from pm_bot.practical.public_fetch_replay_before_update_plan import build_public_fetch_replay_before_update_plan
from pm_bot.practical.public_fetch_request_manifest import build_public_fetch_request_manifest

PREP_DIR = Path("pm_bot/practical/artifacts/public_read_only_fetch_prep_005")


def _load(name: str) -> dict:
    return json.loads((PREP_DIR / name).read_text(encoding="utf-8"))


def test_approval_packet_is_generated_and_remains_pending() -> None:
    fetch_plan = _load("fetch_plan_5_markets.json")
    link_map = _load("fetch_plan_to_active_hypotheses_link_map.json")
    request_manifest = build_public_fetch_request_manifest(fetch_plan=fetch_plan, link_map=link_map)
    evidence_save_plan = build_public_fetch_evidence_save_plan(fetch_plan=fetch_plan)
    replay_plan = build_public_fetch_replay_before_update_plan(
        fetch_plan=fetch_plan,
        request_manifest=request_manifest,
        evidence_save_plan=evidence_save_plan,
    )
    packet = build_public_fetch_approval_packet(
        fetch_plan=fetch_plan,
        dry_run_preview=_load("fetch_dry_run_preview_5_markets.json"),
        operator_approval=_load("operator_approval_pending.json"),
        readiness_gate=_load("public_fetch_readiness_gate.result.json"),
        link_map=link_map,
        source_registry=_load("source_registry_snapshot.json"),
        request_manifest=request_manifest,
        evidence_save_plan=evidence_save_plan,
        replay_plan=replay_plan,
    )

    assert packet["contract_version"] == "pmbot_public_read_only_fetch_approval_packet.v1"
    assert packet["market_count"] == 5
    assert set(packet["market_ids"]) == {"563650", "597964", "598936", "691547", "692258"}
    assert packet["operator_approval_required"] is True
    assert packet["operator_approval_granted"] is False
    assert packet["ready_for_controlled_public_fetch"] is False
    assert packet["live_fetch_performed"] is False
    assert packet["live_network_used"] is False
    assert packet["safety_summary"]["authenticated_endpoints_used"] is False
    assert packet["safety_summary"]["wallet_or_private_key_access"] is False
    assert packet["safety_summary"]["orders_or_trading_actions"] is False


def test_approval_packet_markdown_is_rendered() -> None:
    artifact = Path("pm_bot/practical/artifacts/public_read_only_fetch_approval_006/approval_packet_5_markets.json")
    packet = json.loads(artifact.read_text(encoding="utf-8"))

    markdown = render_public_fetch_approval_packet_markdown(packet)

    assert "## Approval packet summary" in markdown
    assert "## Future allowed task if approved" in markdown
    assert "Operator approval granted: `false`" in markdown
