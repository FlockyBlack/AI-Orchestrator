from __future__ import annotations

import json
from pathlib import Path

from pm_bot.practical.public_fetch_approval_packet import build_manual_operator_approval_template

APPROVAL_PACKET = Path("pm_bot/practical/artifacts/public_read_only_fetch_approval_006/approval_packet_5_markets.json")


def test_manual_operator_approval_template_is_pending() -> None:
    approval_packet = json.loads(APPROVAL_PACKET.read_text(encoding="utf-8"))

    template = build_manual_operator_approval_template(approval_packet=approval_packet)

    assert template["contract_version"] == "pmbot_manual_operator_approval_template.v1"
    assert template["approval_status"] == "pending"
    assert template["operator_must_set_to_approved_manually"] is True
    assert template["approved_by"] is None
    assert template["approved_at"] is None
    assert template["operator_approval_granted"] is False
    assert template["ready_for_controlled_public_fetch"] is False
    assert template["explicit_non_approval_notice"]
