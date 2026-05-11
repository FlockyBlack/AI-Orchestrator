from __future__ import annotations

from pm_bot.trading_core.execution_simulator import run_execution_simulator
from pm_bot.trading_core.paper_position_ledger import build_paper_position_ledger
from pm_bot.trading_core.portfolio_state import build_portfolio_state
from pm_bot.trading_core.post_execution_audit import build_post_execution_audit
from pm_bot.trading_core.risk_gate import run_risk_gate
from pm_bot.trading_core.risk_limits import default_paper_risk_limits
from pm_bot.trading_core.schemas import write_json, write_text
from pm_bot.trading_core.trade_intent_candidate import build_paper_trade_intent_candidates
from pm_bot.trading_core.trading_core_safety_scan import run_trading_core_safety_scan
from pm_bot.trading_core.trading_dashboard import build_paper_trading_dashboard, render_paper_trading_dashboard_markdown


def _pipeline() -> tuple[dict, dict, dict, dict, dict, dict]:
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
    return candidates, risk, executions, ledger, portfolio, audit


def test_post_execution_audit_passes_for_pipeline() -> None:
    _candidates, _risk, _executions, _ledger, _portfolio, audit = _pipeline()

    assert audit["audit_passed"] is True
    assert audit["violations"] == []


def test_dashboard_contains_required_sections() -> None:
    candidates, risk, executions, ledger, portfolio, audit = _pipeline()
    dashboard = build_paper_trading_dashboard(
        candidates_batch=candidates,
        risk_gate_batch=risk,
        execution_batch=executions,
        ledger=ledger,
        portfolio_state=portfolio,
        audit=audit,
    )
    markdown = render_paper_trading_dashboard_markdown(dashboard)

    assert dashboard["paper_only"] is True
    assert "# PMBOT Paper Trading Dashboard" in markdown
    assert "## Intent candidates" in markdown
    assert "## Risk gate results" in markdown
    assert "## Simulated executions" in markdown
    assert "## What is still not real trading" in markdown


def test_trading_core_safety_scan_passes_generated_tmp_artifacts(tmp_path) -> None:
    candidates, risk, executions, ledger, portfolio, audit = _pipeline()
    dashboard = build_paper_trading_dashboard(
        candidates_batch=candidates,
        risk_gate_batch=risk,
        execution_batch=executions,
        ledger=ledger,
        portfolio_state=portfolio,
        audit=audit,
    )
    write_json(tmp_path / "paper_trade_intent_candidates.json", candidates)
    write_json(tmp_path / "risk_gate_results.json", risk)
    write_json(tmp_path / "simulated_execution_results.json", executions)
    write_json(tmp_path / "paper_position_ledger.json", ledger)
    write_json(tmp_path / "paper_portfolio_state.json", portfolio)
    write_json(tmp_path / "post_execution_audit.json", audit)
    write_text(tmp_path / "paper_trading_dashboard.md", render_paper_trading_dashboard_markdown(dashboard))

    report = run_trading_core_safety_scan(
        artifact_dirs=[tmp_path],
        out_json_path=tmp_path / "trading_core_safety_scan.result.json",
        out_md_path=tmp_path / "trading_core_safety_scan.md",
    )

    assert report["safety_ok"] is True
    assert report["issue_count"] == 0
