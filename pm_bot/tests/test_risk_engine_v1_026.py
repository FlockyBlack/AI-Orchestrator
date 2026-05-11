from __future__ import annotations

import json
import socket
from copy import deepcopy

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


def _config(**overrides):  # type: ignore[no-untyped-def]
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


def _input(**overrides):  # type: ignore[no-untyped-def]
    value = build_risk_decision_input(
        run_id="risk-engine-test-run",
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


def _load_json(path):  # type: ignore[no-untyped-def]
    return json.loads(path.read_text(encoding="utf-8"))


def test_risk_config_validation_accepts_v1_contract_and_rejects_bad_values() -> None:
    config = _config()

    valid, errors = validate_risk_engine_config(config)

    assert valid is True
    assert errors == []

    bad = deepcopy(config)
    bad["max_single_action_notional_usd"] = -1
    bad["market_denylist"] = ["market-1"]
    bad["market_allowlist"] = ["market-1"]

    valid, errors = validate_risk_engine_config(bad)

    assert valid is False
    assert "max_single_action_notional_usd must be >= 0" in errors
    assert "market_allowlist and market_denylist overlap: market-1" in errors


def test_kill_switch_blocks_all_proposed_actions() -> None:
    decision = evaluate_risk_decision(_input(), _config(kill_switch_enabled=True))

    assert decision["decision"] == DECISION_BLOCKED
    assert "KILL_SWITCH_ENABLED" in decision["reason_codes"]
    assert decision["applied_to_real_execution"] is False


def test_total_exposure_limit_blocks_projected_excess() -> None:
    decision = evaluate_risk_decision(
        _input(current_total_exposure_usd=95.0, requested_notional_usd=10.0),
        _config(max_total_exposure_usd=100.0),
    )

    assert decision["decision"] == DECISION_BLOCKED
    assert "TOTAL_EXPOSURE_LIMIT_EXCEEDED" in decision["reason_codes"]


def test_per_market_exposure_limit_blocks_projected_excess() -> None:
    decision = evaluate_risk_decision(
        _input(current_market_exposure_usd=45.0, requested_notional_usd=10.0),
        _config(max_market_exposure_usd=50.0),
    )

    assert decision["decision"] == DECISION_BLOCKED
    assert "MARKET_EXPOSURE_LIMIT_EXCEEDED" in decision["reason_codes"]


def test_single_action_notional_limit_blocks_projected_excess() -> None:
    decision = evaluate_risk_decision(
        _input(requested_notional_usd=30.0),
        _config(max_single_action_notional_usd=25.0),
    )

    assert decision["decision"] == DECISION_BLOCKED
    assert "SINGLE_ACTION_NOTIONAL_LIMIT_EXCEEDED" in decision["reason_codes"]


def test_allowlist_and_denylist_are_enforced() -> None:
    not_allowlisted = evaluate_risk_decision(
        _input(market_id="market-1"),
        _config(market_allowlist=["market-2"]),
    )
    denylisted = evaluate_risk_decision(
        _input(market_id="market-1"),
        _config(market_denylist=["market-1"]),
    )

    assert not_allowlisted["decision"] == DECISION_BLOCKED
    assert "MARKET_NOT_ALLOWLISTED" in not_allowlisted["reason_codes"]
    assert denylisted["decision"] == DECISION_BLOCKED
    assert "MARKET_DENYLISTED" in denylisted["reason_codes"]


def test_stale_or_missing_evidence_blocks_when_fresh_evidence_is_required() -> None:
    stale = evaluate_risk_decision(
        _input(evidence_freshness_status="stale"),
        _config(require_fresh_evidence=True, manual_approval_required=False),
    )
    missing = evaluate_risk_decision(
        _input(evidence_freshness_status="missing"),
        _config(require_fresh_evidence=True, manual_approval_required=False),
    )

    assert stale["decision"] == DECISION_BLOCKED
    assert missing["decision"] == DECISION_BLOCKED
    assert "EVIDENCE_NOT_FRESH" in stale["reason_codes"]
    assert "EVIDENCE_NOT_FRESH" in missing["reason_codes"]


def test_stale_evidence_can_require_manual_approval_by_config() -> None:
    decision = evaluate_risk_decision(
        _input(evidence_freshness_status="stale", operator_approval_status="pending"),
        _config(require_fresh_evidence=True, manual_approval_required=True),
    )

    assert decision["decision"] == DECISION_NEEDS_MANUAL_APPROVAL
    assert "EVIDENCE_NOT_FRESH_REQUIRES_MANUAL_APPROVAL" in decision["reason_codes"]
    assert "MANUAL_APPROVAL_REQUIRED" in decision["reason_codes"]


def test_source_gap_blocks_or_requires_manual_approval_by_config() -> None:
    blocked = evaluate_risk_decision(
        _input(source_gap_status="gaps_present"),
        _config(block_on_source_gap=True, manual_approval_required=False),
    )
    manual = evaluate_risk_decision(
        _input(source_gap_status="gaps_present", operator_approval_status="pending"),
        _config(block_on_source_gap=False, manual_approval_required=True),
    )

    assert blocked["decision"] == DECISION_BLOCKED
    assert "SOURCE_GAP_PRESENT" in blocked["reason_codes"]
    assert manual["decision"] == DECISION_NEEDS_MANUAL_APPROVAL
    assert "SOURCE_GAP_REQUIRES_MANUAL_APPROVAL" in manual["reason_codes"]


def test_manual_approval_required_gate_allows_only_approved_status() -> None:
    pending = evaluate_risk_decision(
        _input(operator_approval_status="pending"),
        _config(manual_approval_required=True),
    )
    approved = evaluate_risk_decision(
        _input(operator_approval_status="approved"),
        _config(manual_approval_required=True),
    )

    assert pending["decision"] == DECISION_NEEDS_MANUAL_APPROVAL
    assert "MANUAL_APPROVAL_REQUIRED" in pending["reason_codes"]
    assert approved["decision"] == DECISION_ALLOWED
    assert approved["reason_codes"] == []


def test_daily_dashboard_and_strategy_ledger_include_passive_risk_decisions(tmp_path) -> None:
    run_paper_daily_loop(PaperDailyLoopConfig(run_date="2026-05-11", max_markets=6, output_dir=tmp_path))

    ledger = _load_json(tmp_path / "risk_engine_decision_ledger.json")
    dashboard = _load_json(tmp_path / "paper_daily_dashboard.json")
    strategy = _load_json(tmp_path / "paper_strategy_evaluation_ledger.json")
    dashboard_md = (tmp_path / "paper_daily_dashboard.md").read_text(encoding="utf-8")

    assert ledger["decision_count"] == 6
    assert ledger["blocked_count"] == 6
    assert ledger["allowed_count"] == 0
    assert ledger["needs_manual_approval_count"] == 0
    assert ledger["reason_code_summary"]["KILL_SWITCH_ENABLED"] == 6
    assert ledger["passive_reporting_only"] is True
    assert ledger["applied_to_real_execution"] is False
    assert ledger["external_api_calls_performed"] is False
    assert dashboard["risk_decision_ledger_status"]["blocked_count"] == 6
    assert dashboard["risk_decision_ledger_status"]["passive_reporting_only"] is True
    assert "Risk Engine Decision Ledger" in dashboard_md
    assert all(row["risk_engine_decision"]["audit_id"] for row in strategy["records"])


def test_risk_engine_daily_loop_uses_no_network_wallet_order_or_invented_pnl(monkeypatch, tmp_path) -> None:
    def blocked_socket(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise AssertionError("network socket should not be used")

    monkeypatch.setattr(socket, "socket", blocked_socket)

    run_paper_daily_loop(PaperDailyLoopConfig(run_date="2026-05-11", max_markets=6, output_dir=tmp_path))
    ledger = _load_json(tmp_path / "risk_engine_decision_ledger.json")
    safety = _load_json(tmp_path / "paper_daily_safety_scan.json")
    risk_config = _load_json(tmp_path / "future_risk_engine_config.json")

    assert ledger["network_used"] is False
    assert ledger["external_api_calls_performed"] is False
    assert ledger["outcome_resolution_invented"] is False
    assert ledger["pnl_invented"] is False
    assert safety["safety_ok"] is True
    assert safety["safety_flags"]["wallet_used"] is False
    assert safety["safety_flags"]["signing_used"] is False
    assert safety["safety_flags"]["trading_endpoint_used"] is False
    assert risk_config["wallet_integration_enabled"] is False
    assert risk_config["signing_integration_enabled"] is False
    assert risk_config["order_placement_enabled"] is False
    assert risk_config["authenticated_endpoint_integration_enabled"] is False
    assert all(decision["wallet_used"] is False for decision in ledger["decisions"])
    assert all(decision["real_order_submitted"] is False for decision in ledger["decisions"])
