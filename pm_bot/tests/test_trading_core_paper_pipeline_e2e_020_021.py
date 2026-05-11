from __future__ import annotations

import socket

from pm_bot.trading_core.execution_simulator import run_execution_simulator
from pm_bot.trading_core.paper_position_ledger import build_paper_position_ledger
from pm_bot.trading_core.portfolio_state import build_portfolio_state
from pm_bot.trading_core.post_execution_audit import build_post_execution_audit
from pm_bot.trading_core.risk_gate import run_risk_gate
from pm_bot.trading_core.risk_limits import default_paper_risk_limits
from pm_bot.trading_core.schemas import write_json
from pm_bot.trading_core.trade_intent_candidate import build_paper_trade_intent_candidates
from pm_bot.trading_core.trading_core_safety_scan import run_trading_core_safety_scan
from pm_bot.trading_core.trading_dashboard import build_paper_trading_dashboard


def test_paper_trading_pipeline_e2e_no_real_execution_paths(monkeypatch, tmp_path) -> None:
    def blocked_socket(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise AssertionError("network socket should not be used")

    monkeypatch.setattr(socket, "socket", blocked_socket)
    candidates = build_paper_trade_intent_candidates()
    limits = default_paper_risk_limits()
    risk = run_risk_gate(candidates_batch=candidates, limits=limits)
    executions = run_execution_simulator(candidates_batch=candidates, risk_gate_batch=risk)
    ledger = build_paper_position_ledger(execution_batch=executions)
    portfolio = build_portfolio_state(ledger=ledger, risk_limits=limits)
    audit = build_post_execution_audit(
        candidates_batch=candidates,
        risk_gate_batch=risk,
        execution_batch=executions,
        ledger=ledger,
        portfolio_state=portfolio,
    )
    dashboard = build_paper_trading_dashboard(
        candidates_batch=candidates,
        risk_gate_batch=risk,
        execution_batch=executions,
        ledger=ledger,
        portfolio_state=portfolio,
        audit=audit,
    )
    for name, artifact in {
        "paper_trade_intent_candidates.json": candidates,
        "risk_gate_results.json": risk,
        "simulated_execution_results.json": executions,
        "paper_position_ledger.json": ledger,
        "paper_portfolio_state.json": portfolio,
        "post_execution_audit.json": audit,
        "paper_trading_dashboard.json": dashboard,
    }.items():
        write_json(tmp_path / name, artifact)
    safety = run_trading_core_safety_scan(
        artifact_dirs=[tmp_path],
        out_json_path=tmp_path / "trading_core_safety_scan.result.json",
        out_md_path=tmp_path / "trading_core_safety_scan.md",
    )

    assert candidates["paper_intent_count"] == 6
    assert risk["risk_blocked_count"] == 0
    assert executions["simulated_fill_count"] == 2
    assert ledger["open_position_count"] == 2
    assert portfolio["total_paper_exposure_usd"] == 50.0
    assert audit["audit_passed"] is True
    assert dashboard["paper_only"] is True
    assert safety["safety_ok"] is True
    assert all(row["paper_only"] is True for row in candidates["candidates"])
    assert all(row["real_order_submitted"] is False for row in executions["results"])
    assert all(row["wallet_used"] is False for row in executions["results"])
    assert all(row["trading_endpoint_used"] is False for row in executions["results"])
    assert dashboard["safety_summary"]["openrouter_calls_performed"] == 0
    assert dashboard["safety_summary"]["polymarket_api_calls_performed"] == 0
    assert dashboard["safety_summary"]["authenticated_endpoints_used"] is False
    assert dashboard["safety_summary"]["market_recommendation_generated"] is False
