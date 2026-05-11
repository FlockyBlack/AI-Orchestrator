from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

from pm_bot.operator_runner.paper_daily_config import PaperDailyLoopConfig
from pm_bot.operator_runner.paper_daily_loop import run_paper_daily_loop
from pm_bot.trading_core.risk_engine import (
    DECISION_ALLOWED,
    DECISION_BLOCKED,
    DECISION_NEEDS_MANUAL_APPROVAL,
    build_risk_decision_input,
    evaluate_risk_decision,
)
from pm_bot.trading_core.risk_prep_config import (
    RISK_ENGINE_CONFIG_VERSION,
    build_default_risk_engine_config,
    validate_risk_engine_config,
)
from pm_bot.trading_core.signing_simulator import (
    STATUS_BLOCKED,
    STATUS_DRY_RUN_RECEIPT_READY,
    build_dry_run_execution_receipt_ledger,
    simulate_signing_for_execution_request,
    write_dry_run_execution_receipt_ledger,
)
from pm_bot.trading_core.wallet_execution_boundary import (
    build_execution_request_packet,
    build_risk_approved_action_packet,
)


def _risk_config(**overrides):  # type: ignore[no-untyped-def]
    config = build_default_risk_engine_config()
    config.update(
        {
            "max_total_exposure_usd": 100.0,
            "max_market_exposure_usd": 50.0,
            "max_per_market_exposure_usd": 50.0,
            "max_single_action_notional_usd": 25.0,
            "kill_switch_enabled": False,
            "manual_approval_required": True,
            "require_fresh_evidence": True,
            "block_on_source_gap": True,
        }
    )
    config.update(overrides)
    if "max_market_exposure_usd" in overrides and "max_per_market_exposure_usd" not in overrides:
        config["max_per_market_exposure_usd"] = config["max_market_exposure_usd"]
    valid, errors = validate_risk_engine_config(config)
    assert valid is True, errors
    return config


def _decision_input(**overrides):  # type: ignore[no-untyped-def]
    value = build_risk_decision_input(
        run_id="signing-simulator-test-run",
        market_id="market-1",
        intent_id="intent-1",
        hypothesis_id="hypothesis-1",
        action_type="proposed_action",
        requested_notional_usd=10.0,
        current_total_exposure_usd=0.0,
        current_market_exposure_usd=0.0,
        evidence_freshness_status="fresh",
        source_gap_status="no_gap",
        operator_approval_status="approved",
        config_version=RISK_ENGINE_CONFIG_VERSION,
    )
    value.update(overrides)
    return value


def _candidate() -> dict[str, object]:
    return {
        "daily_run_id": "signing-simulator-test-run",
        "run_date": "2026-05-11",
        "intent_id": "intent-1",
        "market_id": "market-1",
        "market_title": "Static fixture market",
        "hypothesis_id": "hypothesis-1",
        "paper_action_type": "simulated_entry",
        "intended_notional_usd": 10.0,
    }


def _packet(*, config_overrides=None, input_overrides=None):  # type: ignore[no-untyped-def]
    config = _risk_config(**(config_overrides or {}))
    decision = evaluate_risk_decision(_decision_input(**(input_overrides or {})), config)
    action_packet = build_risk_approved_action_packet(
        candidate=_candidate(),
        risk_decision=decision,
        risk_config=config,
    )
    packet = build_execution_request_packet(risk_approved_action_packet=action_packet)
    return config, decision, packet


def test_happy_path_simulated_dry_run_receipt() -> None:
    _config, decision, packet = _packet()

    receipt = simulate_signing_for_execution_request(packet)
    repeat = simulate_signing_for_execution_request(packet)

    assert decision["decision"] == DECISION_ALLOWED
    assert receipt["status"] == STATUS_DRY_RUN_RECEIPT_READY
    assert receipt["blocked_reason"] is None
    assert receipt["receipt_id"] == repeat["receipt_id"]
    assert receipt["packet_id"] == packet["packet_id"]
    assert receipt["mode"] == "dry_run_only"
    assert receipt["simulation_mode"] == "simulation_only"
    assert receipt["gate_summary"]["valid_boundary_packet"] is True
    assert receipt["gate_summary"]["manual_approval_gate_required"] is True
    assert receipt["gate_summary"]["manual_approval_present"] is True
    assert receipt["gate_summary"]["evidence_gate_required"] is True
    assert receipt["gate_summary"]["evidence_fresh"] is True
    assert receipt["gate_summary"]["source_gap_gate_required"] is True
    assert receipt["gate_summary"]["source_gap_free"] is True
    assert receipt["wallet_used"] is False
    assert receipt["private_key_used"] is False
    assert receipt["signing_used"] is False
    assert receipt["real_signing_performed"] is False
    assert receipt["real_order_submitted"] is False
    assert receipt["authenticated_endpoint_used"] is False


def test_signing_simulator_blocks_when_kill_switch_is_active() -> None:
    _config, decision, packet = _packet(config_overrides={"kill_switch_enabled": True})

    receipt = simulate_signing_for_execution_request(packet)

    assert decision["decision"] == DECISION_BLOCKED
    assert receipt["status"] == STATUS_BLOCKED
    assert "KILL_SWITCH_ENABLED" in receipt["reason_codes"]
    assert "KILL_SWITCH_MUST_BE_DISABLED" in receipt["reason_codes"]
    assert receipt["gate_summary"]["kill_switch_disabled"] is False


def test_signing_simulator_blocks_when_manual_approval_is_missing() -> None:
    _config, decision, packet = _packet(input_overrides={"operator_approval_status": "pending"})

    receipt = simulate_signing_for_execution_request(packet)

    assert decision["decision"] == DECISION_NEEDS_MANUAL_APPROVAL
    assert receipt["status"] == STATUS_BLOCKED
    assert "MANUAL_APPROVAL_REQUIRED" in receipt["reason_codes"]
    assert receipt["gate_summary"]["manual_approval_gate_required"] is True
    assert receipt["gate_summary"]["manual_approval_present"] is False


def test_signing_simulator_blocks_when_risk_decision_is_missing() -> None:
    action_packet = build_risk_approved_action_packet(
        candidate=_candidate(),
        risk_decision={},
        risk_config=_risk_config(),
    )
    packet = build_execution_request_packet(risk_approved_action_packet=action_packet)

    receipt = simulate_signing_for_execution_request(packet)

    assert receipt["status"] == STATUS_BLOCKED
    assert "MISSING_RISK_DECISION_ID" in receipt["reason_codes"]
    assert "RISK_DECISION_REQUIRED" in receipt["reason_codes"]
    assert "RISK_DECISION_NOT_ALLOWED" in receipt["reason_codes"]
    assert receipt["gate_summary"]["risk_decision_present"] is False


def test_signing_simulator_blocks_on_evidence_gap() -> None:
    _config, decision, packet = _packet(
        input_overrides={
            "evidence_freshness_status": "missing",
            "source_gap_status": "gaps_present",
        },
    )

    receipt = simulate_signing_for_execution_request(packet)

    assert decision["decision"] == DECISION_BLOCKED
    assert receipt["status"] == STATUS_BLOCKED
    assert "EVIDENCE_NOT_FRESH" in receipt["reason_codes"]
    assert "SOURCE_GAP_PRESENT" in receipt["reason_codes"]
    assert receipt["gate_summary"]["evidence_fresh"] is False
    assert receipt["gate_summary"]["source_gap_free"] is False


def test_signing_simulator_rejects_forbidden_private_key_signature_order_and_auth_fields() -> None:
    _config, _decision, packet = _packet()
    packet = deepcopy(packet)
    packet["private_key"] = "forbidden"
    packet["risk_approved_action_packet"]["signature"] = "forbidden"
    packet["risk_approved_action_packet"]["nested"] = {
        "order_payload": {"side": "forbidden"},
        "authenticated_endpoint": "forbidden",
    }

    receipt = simulate_signing_for_execution_request(packet)

    assert receipt["status"] == STATUS_BLOCKED
    assert "FORBIDDEN_EXECUTION_REQUEST_FIELD_PRESENT" in receipt["reason_codes"]
    assert "$.private_key" in receipt["gate_summary"]["forbidden_field_paths"]
    assert "$.risk_approved_action_packet.signature" in receipt["gate_summary"]["forbidden_field_paths"]
    assert "$.risk_approved_action_packet.nested.order_payload" in receipt["gate_summary"]["forbidden_field_paths"]
    assert (
        "$.risk_approved_action_packet.nested.authenticated_endpoint"
        in receipt["gate_summary"]["forbidden_field_paths"]
    )


def test_dry_run_receipt_ledger_generation_is_idempotent(tmp_path: Path) -> None:
    _config, _decision, packet = _packet()
    out_json = tmp_path / "dry_run_execution_receipts.json"
    out_md = tmp_path / "dry_run_execution_receipts.md"

    first = write_dry_run_execution_receipt_ledger(
        execution_request_packets=[packet],
        out_json_path=out_json,
        out_md_path=out_md,
    )
    first_text = out_json.read_text(encoding="utf-8")
    second = write_dry_run_execution_receipt_ledger(
        execution_request_packets=[packet],
        out_json_path=out_json,
        out_md_path=out_md,
    )
    second_text = out_json.read_text(encoding="utf-8")

    assert first == second
    assert first_text == second_text
    assert first["receipt_ids_unique"] is True
    assert first["idempotency"]["deterministic_receipt_ids"] is True
    assert "PMBOT Dry-Run Execution Receipts" in out_md.read_text(encoding="utf-8")


def test_daily_dashboard_surfaces_dry_run_receipts_without_changing_paper_fills(tmp_path: Path) -> None:
    result = run_paper_daily_loop(PaperDailyLoopConfig(run_date="2026-05-11", max_markets=6, output_dir=tmp_path))

    receipts = json.loads((tmp_path / "dry_run_execution_receipts.json").read_text(encoding="utf-8"))
    dashboard = json.loads((tmp_path / "paper_daily_dashboard.json").read_text(encoding="utf-8"))
    strategy = json.loads((tmp_path / "paper_strategy_evaluation_ledger.json").read_text(encoding="utf-8"))
    dashboard_md = (tmp_path / "paper_daily_dashboard.md").read_text(encoding="utf-8")

    assert result.simulated_fill_count == 2
    assert result.dry_run_receipt_ledger_path.endswith("dry_run_execution_receipts.json")
    assert receipts["receipt_count"] == 6
    assert receipts["blocked_receipt_count"] == 6
    assert receipts["dry_run_receipt_ready_count"] == 0
    assert receipts["external_api_calls_performed"] is False
    assert receipts["wallet_used"] is False
    assert receipts["signing_used"] is False
    assert receipts["real_order_submitted"] is False
    assert dashboard["dry_run_receipt_summary"]["receipt_count"] == 6
    assert dashboard["counts"]["dry_run_receipt_count"] == 6
    assert dashboard["counts"]["simulated_fill_count"] == 2
    assert strategy["dry_run_receipt_summary"]["receipt_count"] == 6
    assert "Dry-Run Execution Receipts" in dashboard_md


def test_no_real_wallet_order_signing_or_authenticated_endpoint_code_introduced() -> None:
    source = Path("pm_bot/trading_core/signing_simulator.py").read_text(encoding="utf-8").lower()

    forbidden_runtime_markers = (
        "import requests",
        "import httpx",
        "socket.",
        "web3",
        "eth_account",
        "sign_transaction(",
        "send_raw_transaction(",
        "place_order(",
        "create_order(",
        "clobclient",
        "authenticatedsession",
        "polymarket",
    )
    for marker in forbidden_runtime_markers:
        assert marker not in source

    ledger = build_dry_run_execution_receipt_ledger(execution_request_packets=[])
    assert ledger["wallet_used"] is False
    assert ledger["private_key_used"] is False
    assert ledger["signing_used"] is False
    assert ledger["real_signing_performed"] is False
    assert ledger["real_order_submitted"] is False
    assert ledger["authenticated_endpoint_used"] is False
