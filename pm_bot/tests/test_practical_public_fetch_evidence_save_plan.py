from __future__ import annotations

import json
from pathlib import Path

from pm_bot.practical.public_fetch_evidence_save_plan import build_public_fetch_evidence_save_plan

FETCH_PLAN = Path("pm_bot/practical/artifacts/public_read_only_fetch_prep_005/fetch_plan_5_markets.json")


def test_evidence_save_plan_requires_no_overwrite_and_metadata() -> None:
    fetch_plan = json.loads(FETCH_PLAN.read_text(encoding="utf-8"))

    plan = build_public_fetch_evidence_save_plan(fetch_plan=fetch_plan)

    assert plan["overwrite_policy"] == "no_overwrite"
    assert plan["validation_required_before_use"] is True
    assert plan["replay_before_analysis_update"] is True
    assert "evidence_packet_id" in plan["required_metadata_fields"]
    assert "source_reference" in plan["required_metadata_fields"]
    assert "normalized_claims" in plan["required_metadata_fields"]
    assert plan["safety_flags_required"]["auth_used"] is False
    assert plan["safety_flags_required"]["wallet_or_private_key_access"] is False
