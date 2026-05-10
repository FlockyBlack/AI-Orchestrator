from __future__ import annotations

import socket
from pathlib import Path

from pm_bot.practical.practical_io import write_json
from pm_bot.practical.public_fetch_dry_run_preview import build_fetch_dry_run_preview
from pm_bot.practical.public_fetch_operator_approval import build_pending_operator_approval
from pm_bot.practical.public_fetch_plan_builder import (
    build_fetch_plan_from_queue,
    build_public_fetch_prep_operator_card,
    build_public_fetch_prep_safety_scan_report,
)
from pm_bot.practical.public_fetch_readiness_gate import evaluate_public_fetch_readiness
from pm_bot.practical.saved_evidence_replay_adapter import map_saved_evidence_to_source_packets
from pm_bot.practical.saved_public_evidence_packet import build_saved_public_evidence_packet

QUEUE = Path("pm_bot/practical/artifacts/real_market_batch_004/real_market_batch_004.market_queue.json")
DEP_MAP = Path("pm_bot/practical/artifacts/real_market_batch_004/real_market_batch_004.source_dependency_map.json")


def test_public_read_only_fetch_prep_e2e_is_local_only_and_blocked_until_approval(tmp_path, monkeypatch) -> None:
    def blocked(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise AssertionError("network access is not allowed")

    monkeypatch.setattr(socket, "create_connection", blocked)

    plan = build_fetch_plan_from_queue(queue_path=QUEUE, source_dependency_map_path=DEP_MAP)
    preview = build_fetch_dry_run_preview(plan)
    approval = build_pending_operator_approval(plan)
    source = plan["requested_sources"][0]
    evidence = build_saved_public_evidence_packet(
        evidence_packet_id="e2e.fixture",
        source_id=source["source_id"],
        source_name=source["source_name"],
        source_category=source["source_category"],
        source_reference=source["source_reference"],
        market_ids=[source["market_id"]],
        hypothesis_ids=[source["hypothesis_id"]],
        raw_excerpt_or_summary="Local E2E fixture only; no public source was fetched.",
        normalized_claims=["Local E2E fixture is safe for replay."],
    )
    replay = map_saved_evidence_to_source_packets([evidence])
    gate = evaluate_public_fetch_readiness(fetch_plan=plan, approval=approval, dry_run_preview=preview)
    card = build_public_fetch_prep_operator_card(
        fetch_plan=plan,
        dry_run_preview=preview,
        operator_approval=approval,
        readiness_gate=gate,
    )

    for name, value in {
        "plan.json": plan,
        "preview.json": preview,
        "approval.json": approval,
        "evidence.json": evidence,
        "replay.json": replay,
        "gate.json": gate,
        "card.json": card,
    }.items():
        write_json(tmp_path / name, value)
    scan = build_public_fetch_prep_safety_scan_report(
        artifact_dir=tmp_path,
        readiness_gate=gate,
        operator_approval=approval,
    )

    assert plan["auth_required"] is False
    assert plan["wallet_required"] is False
    assert plan["trading_endpoint_allowed"] is False
    assert plan["order_endpoint_allowed"] is False
    assert plan["live_fetch_performed"] is False
    assert preview["live_fetch_allowed_now"] is False
    assert approval["operator_approval_granted"] is False
    assert replay["live_network_used"] is False
    assert gate["ready_for_controlled_public_fetch"] is False
    assert card["ready_for_controlled_public_fetch"] is False
    assert scan["public_fetch_prep_safety_scan_passed"] is True
    assert scan["live_network_used"] is False
    assert scan["openrouter_calls_performed"] == 0
    assert scan["polymarket_api_calls_performed"] == 0
    assert scan["authenticated_endpoints_used"] is False
    assert scan["wallet_or_private_key_access"] is False
    assert scan["orders_or_trading_actions"] is False
    assert scan["runtime_or_dispatcher_changes"] is False
    assert scan["market_recommendation_generated"] is False
    assert scan["probability_ev_edge_or_side_selection_generated"] is False
    assert scan["ready_for_controlled_public_fetch"] is False
