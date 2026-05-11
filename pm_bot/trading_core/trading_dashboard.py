from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Mapping, Sequence

from pm_bot.trading_core.schemas import (
    ARTIFACT_DIR,
    GENERATED_AT,
    PAPER_TRADING_DASHBOARD_CONTRACT,
    assert_valid,
    bullet_lines,
    clean_text,
    load_json_object,
    mapping_rows,
    trading_core_safety_summary,
    validate_paper_trading_dashboard,
    write_json,
    write_text,
)


def build_paper_trading_dashboard(
    *,
    candidates_batch: Mapping[str, Any],
    risk_gate_batch: Mapping[str, Any],
    execution_batch: Mapping[str, Any],
    ledger: Mapping[str, Any],
    portfolio_state: Mapping[str, Any],
    audit: Mapping[str, Any],
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    dashboard = {
        "contract_version": PAPER_TRADING_DASHBOARD_CONTRACT,
        "dashboard_id": "paper-trading-dashboard-night-020-021",
        "generated_at": generated_at,
        "intent_candidates": list(mapping_rows(candidates_batch.get("candidates"))),
        "risk_gate_results": list(mapping_rows(risk_gate_batch.get("results"))),
        "simulated_executions": list(mapping_rows(execution_batch.get("results"))),
        "paper_positions": list(mapping_rows(ledger.get("positions"))),
        "portfolio_exposure": {
            "total_paper_capital_usd": portfolio_state.get("total_paper_capital_usd"),
            "total_paper_exposure_usd": portfolio_state.get("total_paper_exposure_usd"),
            "available_paper_capital_usd": portfolio_state.get("available_paper_capital_usd"),
            "exposure_by_market_usd": portfolio_state.get("exposure_by_market_usd", {}),
            "open_position_count": portfolio_state.get("open_position_count"),
        },
        "audit_status": {
            "audit_passed": audit.get("audit_passed"),
            "violation_count": len(audit.get("violations", [])),
            "warning_count": len(audit.get("warnings", [])),
        },
        "counts": {
            "paper_intent_count": candidates_batch.get("paper_intent_count"),
            "risk_allowed_count": risk_gate_batch.get("risk_allowed_count"),
            "risk_blocked_count": risk_gate_batch.get("risk_blocked_count"),
            "simulated_execution_count": execution_batch.get("simulated_execution_count"),
            "simulated_fill_count": execution_batch.get("simulated_fill_count"),
            "skipped_count": execution_batch.get("skipped_count"),
            "rejected_count": execution_batch.get("rejected_count"),
            "open_paper_position_count": ledger.get("open_position_count"),
            "total_paper_exposure_usd": portfolio_state.get("total_paper_exposure_usd"),
        },
        "next_operator_actions": [
            "Review the dashboard and audit before treating any paper position as useful state.",
            "Collect or approve saved public evidence for observe-only markets before future paper simulation.",
            "Keep all six outcomes unresolved until saved local outcome evidence exists.",
            "Use the one-shot operator runner for the next explicit local refresh.",
        ],
        "what_is_still_not_real_trading": [
            "No wallet, signing, order placement, authenticated endpoint, live price, or trading endpoint exists here.",
            "Paper side labels are tracking labels only and are not real trading instructions.",
            "Fixture fills exist only to test ledger, portfolio, and audit plumbing.",
            "Real adapter, kill switch, reconciliation, and manual approval infrastructure remain missing.",
        ],
        "paper_only": True,
        "safety_summary": trading_core_safety_summary(),
    }
    valid, errors = validate_paper_trading_dashboard(dashboard)
    assert_valid(dashboard["dashboard_id"], valid, errors)
    return dashboard


def run_paper_trading_dashboard(
    *,
    candidates_batch: Mapping[str, Any],
    risk_gate_batch: Mapping[str, Any],
    execution_batch: Mapping[str, Any],
    ledger: Mapping[str, Any],
    portfolio_state: Mapping[str, Any],
    audit: Mapping[str, Any],
    out_json_path: str | Path = ARTIFACT_DIR / "paper_trading_dashboard.json",
    out_md_path: str | Path = ARTIFACT_DIR / "paper_trading_dashboard.md",
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    dashboard = build_paper_trading_dashboard(
        candidates_batch=candidates_batch,
        risk_gate_batch=risk_gate_batch,
        execution_batch=execution_batch,
        ledger=ledger,
        portfolio_state=portfolio_state,
        audit=audit,
        generated_at=generated_at,
    )
    write_json(out_json_path, dashboard)
    write_text(out_md_path, render_paper_trading_dashboard_markdown(dashboard))
    return dashboard


def render_paper_trading_dashboard_markdown(dashboard: Mapping[str, Any]) -> str:
    counts = dict(dashboard.get("counts", {}))
    portfolio = dict(dashboard.get("portfolio_exposure", {}))
    audit = dict(dashboard.get("audit_status", {}))
    lines = [
        "# PMBOT Paper Trading Dashboard",
        "",
        "## Intent candidates",
        "",
        f"- Paper intents: {counts.get('paper_intent_count')}",
    ]
    for candidate in mapping_rows(dashboard.get("intent_candidates")):
        lines.append(
            f"- `{candidate.get('market_id')}` `{candidate.get('paper_action_type')}` "
            f"`{candidate.get('side_label')}` - {candidate.get('market_title')}"
        )
    lines.extend(
        [
            "",
            "## Risk gate results",
            "",
            f"- Allowed: {counts.get('risk_allowed_count')}",
            f"- Blocked: {counts.get('risk_blocked_count')}",
        ]
    )
    for result in mapping_rows(dashboard.get("risk_gate_results")):
        lines.append(f"- `{result.get('market_id')}` `{result.get('risk_gate_status')}`")
    lines.extend(
        [
            "",
            "## Simulated executions",
            "",
            f"- Simulated results: {counts.get('simulated_execution_count')}",
            f"- Paper fixture fills: {counts.get('simulated_fill_count')}",
            f"- Skipped: {counts.get('skipped_count')}",
            f"- Rejected: {counts.get('rejected_count')}",
        ]
    )
    for execution in mapping_rows(dashboard.get("simulated_executions")):
        lines.append(f"- `{execution.get('market_id')}` `{execution.get('execution_status')}`")
    lines.extend(
        [
            "",
            "## Paper positions",
            "",
            f"- Open paper positions: {counts.get('open_paper_position_count')}",
        ]
    )
    for position in mapping_rows(dashboard.get("paper_positions")):
        lines.append(f"- `{position.get('market_id')}` `${position.get('paper_exposure_usd')}` unresolved")
    lines.extend(
        [
            "",
            "## Portfolio exposure",
            "",
            f"- Total paper capital: `${portfolio.get('total_paper_capital_usd')}`",
            f"- Total paper exposure: `${portfolio.get('total_paper_exposure_usd')}`",
            f"- Available paper capital: `${portfolio.get('available_paper_capital_usd')}`",
            "",
            "## Audit status",
            "",
            f"- Audit passed: `{str(audit.get('audit_passed')).lower()}`",
            f"- Violations: {audit.get('violation_count')}",
            f"- Warnings: {audit.get('warning_count')}",
            "",
            "## Next operator actions",
            "",
            *bullet_lines(str(item) for item in dashboard.get("next_operator_actions", [])),
            "",
            "## What is still not real trading",
            "",
            *bullet_lines(str(item) for item in dashboard.get("what_is_still_not_real_trading", [])),
        ]
    )
    return "\n".join(lines) + "\n"


def load_and_run_paper_trading_dashboard(
    *,
    candidates_path: str | Path = ARTIFACT_DIR / "paper_trade_intent_candidates.json",
    risk_gate_path: str | Path = ARTIFACT_DIR / "risk_gate_results.json",
    executions_path: str | Path = ARTIFACT_DIR / "simulated_execution_results.json",
    ledger_path: str | Path = ARTIFACT_DIR / "paper_position_ledger.json",
    portfolio_path: str | Path = ARTIFACT_DIR / "paper_portfolio_state.json",
    audit_path: str | Path = ARTIFACT_DIR / "post_execution_audit.json",
    out_json_path: str | Path = ARTIFACT_DIR / "paper_trading_dashboard.json",
    out_md_path: str | Path = ARTIFACT_DIR / "paper_trading_dashboard.md",
) -> dict[str, Any]:
    return run_paper_trading_dashboard(
        candidates_batch=load_json_object(candidates_path, label="intent candidates"),
        risk_gate_batch=load_json_object(risk_gate_path, label="risk gate"),
        execution_batch=load_json_object(executions_path, label="executions"),
        ledger=load_json_object(ledger_path, label="ledger"),
        portfolio_state=load_json_object(portfolio_path, label="portfolio"),
        audit=load_json_object(audit_path, label="audit"),
        out_json_path=out_json_path,
        out_md_path=out_md_path,
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build PMBOT paper trading dashboard.")
    parser.add_argument("--candidates", default=str(ARTIFACT_DIR / "paper_trade_intent_candidates.json"))
    parser.add_argument("--risk-gate", default=str(ARTIFACT_DIR / "risk_gate_results.json"))
    parser.add_argument("--executions", default=str(ARTIFACT_DIR / "simulated_execution_results.json"))
    parser.add_argument("--ledger", default=str(ARTIFACT_DIR / "paper_position_ledger.json"))
    parser.add_argument("--portfolio", default=str(ARTIFACT_DIR / "paper_portfolio_state.json"))
    parser.add_argument("--audit", default=str(ARTIFACT_DIR / "post_execution_audit.json"))
    parser.add_argument("--out-json", default=str(ARTIFACT_DIR / "paper_trading_dashboard.json"))
    parser.add_argument("--out-md", default=str(ARTIFACT_DIR / "paper_trading_dashboard.md"))
    args = parser.parse_args(argv)
    load_and_run_paper_trading_dashboard(
        candidates_path=args.candidates,
        risk_gate_path=args.risk_gate,
        executions_path=args.executions,
        ledger_path=args.ledger,
        portfolio_path=args.portfolio,
        audit_path=args.audit,
        out_json_path=args.out_json,
        out_md_path=args.out_md,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
