from __future__ import annotations

import json
import socket
from pathlib import Path

from pm_bot.practical.practical_io import write_json
from pm_bot.practical.public_fetch_approval_packet import (
    build_approval_blocker_scenarios,
    build_approval_packet_safety_scan_report,
    build_future_controlled_fetch_task_spec,
    build_manual_operator_approval_template,
    build_operator_public_fetch_approval_card,
    build_public_fetch_approval_packet,
)
from pm_bot.practical.public_fetch_evidence_save_plan import build_public_fetch_evidence_save_plan
from pm_bot.practical.public_fetch_replay_before_update_plan import build_public_fetch_replay_before_update_plan
from pm_bot.practical.public_fetch_request_manifest import build_public_fetch_request_manifest

PREP_DIR = Path("pm_bot/practical/artifacts/public_read_only_fetch_prep_005")


def _load(name: str) -> dict:
    return json.loads((PREP_DIR / name).read_text(encoding="utf-8"))


def test_public_fetch_approval_packet_e2e_is_local_only_and_pending(tmp_path, monkeypatch) -> None:
    def blocked(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise AssertionError("network access is not allowed")

    monkeypatch.setattr(socket, "create_connection", blocked)

    fetch_plan = _load("fetch_plan_5_markets.json")
    dry_run_preview = _load("fetch_dry_run_preview_5_markets.json")
    operator_approval = _load("operator_approval_pending.json")
    readiness_gate = _load("public_fetch_readiness_gate.result.json")
    link_map = _load("fetch_plan_to_active_hypotheses_link_map.json")
    source_registry = _load("source_registry_snapshot.json")

    request_manifest = build_public_fetch_request_manifest(fetch_plan=fetch_plan, link_map=link_map)
    evidence_save_plan = build_public_fetch_evidence_save_plan(fetch_plan=fetch_plan)
    replay_plan = build_public_fetch_replay_before_update_plan(
        fetch_plan=fetch_plan,
        request_manifest=request_manifest,
        evidence_save_plan=evidence_save_plan,
    )
    approval_packet = build_public_fetch_approval_packet(
        fetch_plan=fetch_plan,
        dry_run_preview=dry_run_preview,
        operator_approval=operator_approval,
        readiness_gate=readiness_gate,
        link_map=link_map,
        source_registry=source_registry,
        request_manifest=request_manifest,
        evidence_save_plan=evidence_save_plan,
        replay_plan=replay_plan,
    )
    future_spec = build_future_controlled_fetch_task_spec(approval_packet=approval_packet)
    approval_template = build_manual_operator_approval_template(approval_packet=approval_packet)
    blockers = build_approval_blocker_scenarios()
    card = build_operator_public_fetch_approval_card(approval_packet=approval_packet)

    for name, value in {
        "fetch_request_manifest_5_markets.json": request_manifest,
        "evidence_save_plan_5_markets.json": evidence_save_plan,
        "replay_before_update_plan_5_markets.json": replay_plan,
        "approval_packet_5_markets.json": approval_packet,
        "future_controlled_fetch_task_spec.json": future_spec,
        "manual_operator_approval_template.json": approval_template,
        "approval_blocker_scenarios.json": blockers,
        "operator_public_fetch_approval_card.json": card,
    }.items():
        write_json(tmp_path / name, value)
    scan = build_approval_packet_safety_scan_report(artifact_dir=tmp_path)

    assert request_manifest["live_network_used"] is False
    assert all(intent["requires_auth"] is False for intent in request_manifest["request_intents"])
    assert all(intent["wallet_or_signing_required"] is False for intent in request_manifest["request_intents"])
    assert all(intent["trading_or_order_endpoint"] is False for intent in request_manifest["request_intents"])
    assert evidence_save_plan["overwrite_policy"] == "no_overwrite"
    assert replay_plan["automatic_analysis_update_allowed"] is False
    assert replay_plan["automatic_trading_allowed"] is False
    assert approval_template["approval_status"] == "pending"
    assert approval_packet["operator_approval_granted"] is False
    assert approval_packet["ready_for_controlled_public_fetch"] is False
    assert card["current_status"] == "not approved"
    assert scan["approval_packet_safety_scan_passed"] is True
    assert scan["live_network_used"] is False
    assert scan["openrouter_calls_performed"] == 0
    assert scan["polymarket_api_calls_performed"] == 0
    assert scan["authenticated_endpoints_used"] is False
    assert scan["wallet_or_private_key_access"] is False
    assert scan["orders_or_trading_actions"] is False
    assert scan["runtime_or_dispatcher_changes"] is False
    assert scan["market_recommendation_generated"] is False
    assert scan["probability_ev_edge_or_side_selection_generated"] is False
    assert scan["operator_approval_granted"] is False
    assert scan["ready_for_controlled_public_fetch"] is False
    assert scan["scheduler_background_worker_or_polling"] is False
