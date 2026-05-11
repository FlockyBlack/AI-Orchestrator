from __future__ import annotations

from pm_bot.trading_core.execution_simulator import run_execution_simulator
from pm_bot.trading_core.paper_position_ledger import build_paper_position_ledger
from pm_bot.trading_core.portfolio_state import build_portfolio_state
from pm_bot.trading_core.risk_gate import run_risk_gate
from pm_bot.trading_core.risk_limits import default_paper_risk_limits
from pm_bot.trading_core.trade_intent_candidate import build_paper_trade_intent_candidates


def test_ledger_creates_positions_from_simulated_fills() -> None:
    candidates = build_paper_trade_intent_candidates()
    limits = default_paper_risk_limits()
    risk = run_risk_gate(candidates_batch=candidates, limits=limits)
    executions = run_execution_simulator(candidates_batch=candidates, risk_gate_batch=risk)

    ledger = build_paper_position_ledger(execution_batch=executions)

    assert ledger["open_position_count"] == executions["simulated_fill_count"]
    assert ledger["total_paper_exposure_usd"] == 50.0
    assert all(row["outcome_status"] == "unresolved" for row in ledger["positions"])


def test_portfolio_state_computes_exposure_and_available_capital() -> None:
    candidates = build_paper_trade_intent_candidates()
    limits = default_paper_risk_limits()
    risk = run_risk_gate(candidates_batch=candidates, limits=limits)
    executions = run_execution_simulator(candidates_batch=candidates, risk_gate_batch=risk)
    ledger = build_paper_position_ledger(execution_batch=executions)

    portfolio = build_portfolio_state(ledger=ledger, risk_limits=limits)

    assert portfolio["total_paper_capital_usd"] == 1000.0
    assert portfolio["total_paper_exposure_usd"] == 50.0
    assert portfolio["available_paper_capital_usd"] == 950.0
    assert portfolio["open_position_count"] == 2
