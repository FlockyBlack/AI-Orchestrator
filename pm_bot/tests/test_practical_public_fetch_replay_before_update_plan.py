from __future__ import annotations

import json
from pathlib import Path

from pm_bot.practical.public_fetch_evidence_save_plan import build_public_fetch_evidence_save_plan
from pm_bot.practical.public_fetch_replay_before_update_plan import build_public_fetch_replay_before_update_plan
from pm_bot.practical.public_fetch_request_manifest import build_public_fetch_request_manifest

PREP_DIR = Path("pm_bot/practical/artifacts/public_read_only_fetch_prep_005")


def test_replay_plan_requires_adapter_and_blocks_automatic_updates() -> None:
    fetch_plan = json.loads((PREP_DIR / "fetch_plan_5_markets.json").read_text(encoding="utf-8"))
    link_map = json.loads((PREP_DIR / "fetch_plan_to_active_hypotheses_link_map.json").read_text(encoding="utf-8"))
    request_manifest = build_public_fetch_request_manifest(fetch_plan=fetch_plan, link_map=link_map)
    evidence_save_plan = build_public_fetch_evidence_save_plan(fetch_plan=fetch_plan)

    replay_plan = build_public_fetch_replay_before_update_plan(
        fetch_plan=fetch_plan,
        request_manifest=request_manifest,
        evidence_save_plan=evidence_save_plan,
    )

    assert replay_plan["replay_adapter_required"] is True
    assert replay_plan["source_packet_mapping_required"] is True
    assert replay_plan["contradiction_check_required"] is True
    assert replay_plan["staleness_check_required"] is True
    assert replay_plan["automatic_analysis_update_allowed"] is False
    assert replay_plan["automatic_trading_allowed"] is False
    assert len(replay_plan["affected_market_ids"]) == 5
    assert len(replay_plan["affected_hypothesis_ids"]) == 5
