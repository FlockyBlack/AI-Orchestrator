from __future__ import annotations

import json
import socket
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
from pm_bot.trading_core.wallet_execution_boundary import (
    FORBIDDEN_EXECUTION_REQUEST_FIELD_NAMES,
    STATUS_APPROVED_FOR_FUTURE_SIMULATION,
    STATUS_BLOCKED,
    STATUS_NEEDS_MANUAL_APPROVAL,
    build_execution_request_packet,
    build_risk_approved_action_packet,
    build_wallet_boundary_audit_ledger,
    build_wallet_boundary_contract,
    render_wallet_boundary_audit_ledger_markdown,
    validate_execution_request_packet,
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
            "manual_approval_required": False,
            "require_fresh_evidence": False,
            "block_on_source_gap": False,
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
        run_id="wallet-boundary-test-run",
        market_id="market-1",
        intent_id="intent-1",
        hypothesis_id="hypothesis-1",
        action_type="proposed_action",
        requested_notional_usd=10.0,
        current_total_exposure_usd=0.0,
        current_market_exposure_usd=0.0,
        evidence_freshness_status="fresh",
        source_gap_status="no_gap",
        operator_approval_status="not_required",
        config_version=RISK_ENGINE_CONFIG_VERSION,
    )
    value.update(overrides)
    return value


def _candidate(**overrides):  # type: ignore[no-untyped-def]
    value = {
        "daily_run_id": "wallet-boundary-test-run",
        "run_date": "2026-05-11",
        "intent_id": "intent-1",
        "market_id": "market-1",
        "market_title": "Static fixture market",
        "hypothesis_id": "hypothesis-1",
        "paper_action_type": "simulated_entry",
        "intended_notional_usd": 10.0,
    }
    value.update(overrides)
    return value


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


def test_wallet_boundary_contract_and_packet_schema_validate_for_future_simulation_only() -> None:
    _config, decision, packet = _packet()
    validation = packet["validation"]

    assert decision["decision"] == DECISION_ALLOWED
    assert decision["risk_decision_id"].startswith("risk-decision-v1-")
    assert packet["packet_status"] == STATUS_APPROVED_FOR_FUTURE_SIMULATION
    assert validation["status"] == STATUS_APPROVED_FOR_FUTURE_SIMULATION
    assert validation["reason_codes"] == []
    assert packet["paper_only"] is True
    assert packet["live_prep_only"] is True
    assert packet["execution_enabled"] is False
    assert packet["live_execution_enabled"] is False
    assert packet["requested_boundary_action"] == "future_simulation_review_only"


def test_missing_risk_decision_blocks_packet() -> None:
    action_packet = build_risk_approved_action_packet(
        candidate=_candidate(),
        risk_decision={},
        risk_config=_risk_config(),
    )
    packet = build_execution_request_packet(risk_approved_action_packet=action_packet)

    assert packet["packet_status"] == STATUS_BLOCKED
    assert "MISSING_RISK_DECISION_ID" in packet["validation"]["reason_codes"]
    assert "MISSING_RISK_AUDIT_ID" in packet["validation"]["reason_codes"]
    assert "RISK_ENGINE_DECISION_MISSING_OR_UNKNOWN" in packet["validation"]["reason_codes"]


def test_kill_switch_blocks_execution_request_packet() -> None:
    _config, decision, packet = _packet(config_overrides={"kill_switch_enabled": True})

    assert decision["decision"] == DECISION_BLOCKED
    assert packet["packet_status"] == STATUS_BLOCKED
    assert "KILL_SWITCH_ENABLED" in packet["validation"]["reason_codes"]
    assert "RISK_ENGINE_DECISION_BLOCKED" in packet["validation"]["reason_codes"]


def test_missing_manual_approval_marks_needs_manual_approval() -> None:
    _config, decision, packet = _packet(
        config_overrides={"manual_approval_required": True},
        input_overrides={"operator_approval_status": "pending"},
    )

    assert decision["decision"] == DECISION_NEEDS_MANUAL_APPROVAL
    assert packet["packet_status"] == STATUS_NEEDS_MANUAL_APPROVAL
    assert "MANUAL_APPROVAL_REQUIRED" in packet["validation"]["reason_codes"]


def test_present_manual_approval_allows_future_simulation_status() -> None:
    _config, decision, packet = _packet(
        config_overrides={"manual_approval_required": True},
        input_overrides={"operator_approval_status": "approved"},
    )

    assert decision["decision"] == DECISION_ALLOWED
    assert packet["packet_status"] == STATUS_APPROVED_FOR_FUTURE_SIMULATION
    assert packet["validation"]["reason_codes"] == []


def test_stale_or_missing_evidence_blocks_when_required() -> None:
    for evidence_status in ("stale", "missing"):
        _config, decision, packet = _packet(
            config_overrides={"require_fresh_evidence": True},
            input_overrides={"evidence_freshness_status": evidence_status},
        )

        assert decision["decision"] == DECISION_BLOCKED
        assert packet["packet_status"] == STATUS_BLOCKED
        assert "EVIDENCE_NOT_FRESH" in packet["validation"]["reason_codes"]


def test_source_gap_blocks_when_required() -> None:
    _config, decision, packet = _packet(
        config_overrides={"block_on_source_gap": True},
        input_overrides={"source_gap_status": "gaps_present"},
    )

    assert decision["decision"] == DECISION_BLOCKED
    assert packet["packet_status"] == STATUS_BLOCKED
    assert "SOURCE_GAP_PRESENT" in packet["validation"]["reason_codes"]


def test_exposure_limit_snapshot_is_required() -> None:
    _config, _decision, packet = _packet()
    packet = deepcopy(packet)
    del packet["risk_approved_action_packet"]["risk_snapshot"]["max_total_exposure_usd"]

    validation = validate_execution_request_packet(packet)

    assert validation["status"] == STATUS_BLOCKED
    assert "EXPOSURE_LIMIT_FIELD_MISSING_MAX_TOTAL_EXPOSURE_USD" in validation["reason_codes"]


def test_private_key_signature_token_and_order_endpoint_fields_are_forbidden() -> None:
    _config, _decision, packet = _packet()
    packet = deepcopy(packet)
    packet["private_key"] = "forbidden"
    packet["risk_approved_action_packet"]["signature"] = "forbidden"
    packet["risk_approved_action_packet"]["nested"] = {
        "api_token": "forbidden",
        "order_endpoint": "forbidden",
        "authenticated_endpoint": "forbidden",
    }

    validation = validate_execution_request_packet(packet)

    assert validation["status"] == STATUS_BLOCKED
    assert "FORBIDDEN_EXECUTION_REQUEST_FIELD_PRESENT" in validation["reason_codes"]
    assert "$.private_key" in validation["forbidden_field_paths"]
    assert "$.risk_approved_action_packet.signature" in validation["forbidden_field_paths"]
    assert "$.risk_approved_action_packet.nested.api_token" in validation["forbidden_field_paths"]
    assert "$.risk_approved_action_packet.nested.order_endpoint" in validation["forbidden_field_paths"]
    assert "$.risk_approved_action_packet.nested.authenticated_endpoint" in validation["forbidden_field_paths"]
    assert {"private_key", "signature", "api_token", "order_endpoint", "authenticated_endpoint"}.issubset(
        FORBIDDEN_EXECUTION_REQUEST_FIELD_NAMES
    )


def test_boundary_audit_ledger_summarizes_reason_codes_and_safety_assertion() -> None:
    config = _risk_config(kill_switch_enabled=True)
    decision = evaluate_risk_decision(_decision_input(), config)
    ledger = build_wallet_boundary_audit_ledger(
        candidates_batch={
            "daily_run_id": "wallet-boundary-test-run",
            "run_date": "2026-05-11",
            "candidates": [_candidate()],
        },
        risk_decision_ledger={"decisions": [decision]},
        risk_config=config,
    )
    markdown = render_wallet_boundary_audit_ledger_markdown(ledger)

    assert ledger["boundary_packets_created"] == 1
    assert ledger["blocked_packet_count"] == 1
    assert ledger["kill_switch_block_count"] == 1
    assert ledger["reason_code_summary"]["KILL_SWITCH_ENABLED"] == 1
    assert ledger["safety_assertion"] == "no signing / no wallet / no order placement"
    assert ledger["external_api_calls_performed"] is False
    assert ledger["outcome_resolution_invented"] is False
    assert ledger["pnl_invented"] is False
    assert "PMBOT Wallet Boundary Audit Ledger" in markdown


def test_daily_dashboard_surfaces_wallet_boundary_summary_without_changing_paper_fills(tmp_path: Path) -> None:
    result = run_paper_daily_loop(PaperDailyLoopConfig(run_date="2026-05-11", max_markets=6, output_dir=tmp_path))

    boundary = json.loads((tmp_path / "wallet_boundary_audit_ledger.json").read_text(encoding="utf-8"))
    dashboard = json.loads((tmp_path / "paper_daily_dashboard.json").read_text(encoding="utf-8"))
    dashboard_md = (tmp_path / "paper_daily_dashboard.md").read_text(encoding="utf-8")

    assert result.simulated_fill_count == 2
    assert boundary["boundary_packets_created"] == 6
    assert boundary["blocked_packet_count"] == 6
    assert boundary["kill_switch_block_count"] == 6
    assert dashboard["wallet_boundary_summary"]["boundary_packets_created"] == 6
    assert dashboard["wallet_boundary_summary"]["blocked_packet_count"] == 6
    assert dashboard["wallet_boundary_summary"]["missing_risk_decision_count"] == 0
    assert dashboard["wallet_boundary_summary"]["kill_switch_block_count"] == 6
    assert "Wallet Boundary Summary" in dashboard_md
    assert dashboard["counts"]["wallet_boundary_packets_created"] == 6
    assert dashboard["counts"]["simulated_fill_count"] == 2


def test_wallet_boundary_uses_no_external_api_calls_and_invents_no_outcome_or_pnl(monkeypatch, tmp_path: Path) -> None:
    def blocked_socket(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise AssertionError("network socket should not be used")

    monkeypatch.setattr(socket, "socket", blocked_socket)

    run_paper_daily_loop(PaperDailyLoopConfig(run_date="2026-05-11", max_markets=6, output_dir=tmp_path))
    boundary = json.loads((tmp_path / "wallet_boundary_audit_ledger.json").read_text(encoding="utf-8"))
    safety = json.loads((tmp_path / "paper_daily_safety_scan.json").read_text(encoding="utf-8"))

    assert boundary["external_api_calls_performed"] is False
    assert boundary["network_used"] is False
    assert boundary["outcome_resolution_invented"] is False
    assert boundary["pnl_invented"] is False
    assert safety["safety_ok"] is True
    assert safety["safety_flags"]["wallet_used"] is False
    assert safety["safety_flags"]["signing_used"] is False
    assert safety["safety_flags"]["trading_endpoint_used"] is False


def test_no_wallet_order_signing_runtime_or_authenticated_endpoint_code_introduced() -> None:
    source = Path("pm_bot/trading_core/wallet_execution_boundary.py").read_text(encoding="utf-8").lower()

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
    )
    for marker in forbidden_runtime_markers:
        assert marker not in source

    contract = build_wallet_boundary_contract()
    assert contract["execution_enabled"] is False
    assert contract["live_execution_enabled"] is False
    assert contract["authenticated_endpoint_used"] is False
    assert contract["external_api_calls_performed"] is False
