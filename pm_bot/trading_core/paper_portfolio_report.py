from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from pm_bot.trading_core.schemas import (
    GENERATED_AT,
    bullet_lines,
    clean_text,
    mapping_rows,
    trading_core_safety_summary,
    write_json,
    write_text,
)

PAPER_PORTFOLIO_REPORT_CONTRACT = "pmbot_paper_portfolio_report.v1"


def build_paper_portfolio_report(
    ledger: Mapping[str, Any],
    portfolio_state: Mapping[str, Any],
    *,
    execution_batch: Mapping[str, Any] | None = None,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    exposure_summary = calculate_paper_exposure_summary(ledger, portfolio_state)
    report = {
        "contract_version": PAPER_PORTFOLIO_REPORT_CONTRACT,
        "generated_at": generated_at,
        "paper_only": True,
        "exposure_summary": exposure_summary,
        "open_paper_positions": summarize_open_paper_positions(ledger),
        "simulated_fills": summarize_simulated_fills(execution_batch or ledger),
        "safety_summary": {
            **trading_core_safety_summary(),
            "market_recommendation_generated": False,
            "probability_ev_edge_or_side_selection_generated": False,
        },
        "operator_note": (
            "Paper portfolio report for local accounting only. It does not provide real trading advice, "
            "real order instructions, or real market direction."
        ),
    }
    return report


def calculate_paper_exposure_summary(
    ledger: Mapping[str, Any],
    portfolio_state: Mapping[str, Any],
) -> dict[str, Any]:
    positions = mapping_rows(ledger.get("positions"))
    exposure_by_market = dict(portfolio_state.get("exposure_by_market_usd", {}))
    if not exposure_by_market:
        for position in positions:
            market_id = clean_text(position.get("market_id"))
            exposure_by_market[market_id] = round(
                float(exposure_by_market.get(market_id, 0) or 0)
                + float(position.get("paper_exposure_usd", 0) or 0),
                2,
            )
    total_exposure = round(
        float(
            portfolio_state.get(
                "total_paper_exposure_usd",
                sum(float(row.get("paper_exposure_usd", 0) or 0) for row in positions),
            )
            or 0
        ),
        2,
    )
    return {
        "open_paper_position_count": int(portfolio_state.get("open_position_count", len(positions)) or 0),
        "unresolved_position_count": len([row for row in positions if row.get("outcome_status") == "unresolved"]),
        "total_paper_capital_usd": float(portfolio_state.get("total_paper_capital_usd", 0) or 0),
        "total_paper_exposure_usd": total_exposure,
        "available_paper_capital_usd": float(portfolio_state.get("available_paper_capital_usd", 0) or 0),
        "exposure_by_market_usd": exposure_by_market,
        "feedback_ready_count": int(portfolio_state.get("feedback_ready_count", 0) or 0),
        "unresolved_market_count": int(portfolio_state.get("unresolved_market_count", 0) or 0),
    }


def summarize_open_paper_positions(ledger: Mapping[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "position_id": clean_text(position.get("position_id")),
            "idempotency_key": clean_text(position.get("idempotency_key")),
            "market_id": clean_text(position.get("market_id")),
            "market_title": clean_text(position.get("market_title")),
            "paper_exposure_usd": float(position.get("paper_exposure_usd", 0) or 0),
            "paper_units": float(position.get("paper_units", 0) or 0),
            "outcome_status": clean_text(position.get("outcome_status") or "unresolved"),
            "paper_only": True,
        }
        for position in mapping_rows(ledger.get("positions"))
        if position.get("outcome_status", "unresolved") == "unresolved"
    ]


def summarize_simulated_fills(source: Mapping[str, Any]) -> list[dict[str, Any]]:
    if mapping_rows(source.get("results")):
        return [
            {
                "execution_id": clean_text(result.get("execution_id")),
                "idempotency_key": clean_text(result.get("idempotency_key")),
                "market_id": clean_text(result.get("market_id")),
                "simulated_fill": result.get("simulated_fill") is True,
                "filled_notional_usd": float(result.get("filled_notional_usd", 0) or 0),
                "paper_only": True,
            }
            for result in mapping_rows(source.get("results"))
            if result.get("simulated_fill") is True
        ]
    return [
        {
            "position_id": clean_text(position.get("position_id")),
            "idempotency_key": clean_text(position.get("idempotency_key")),
            "market_id": clean_text(position.get("market_id")),
            "simulated_fill": True,
            "filled_notional_usd": float(position.get("paper_exposure_usd", 0) or 0),
            "paper_only": True,
        }
        for position in mapping_rows(source.get("positions"))
    ]


def write_paper_portfolio_report(
    report: Mapping[str, Any],
    *,
    out_json_path: str | Path,
    out_md_path: str | Path,
) -> dict[str, Any]:
    active_report = dict(report)
    write_json(out_json_path, active_report)
    write_text(out_md_path, render_paper_portfolio_report_markdown(active_report))
    return active_report


def render_paper_portfolio_report_markdown(report: Mapping[str, Any]) -> str:
    exposure = dict(report.get("exposure_summary", {}))
    lines = [
        "# PMBOT Paper Portfolio Report",
        "",
        f"- Open paper positions: {exposure.get('open_paper_position_count')}",
        f"- Total paper exposure: `${exposure.get('total_paper_exposure_usd')}`",
        f"- Unresolved markets: {exposure.get('unresolved_market_count')}",
        f"- Feedback ready: {exposure.get('feedback_ready_count')}",
        "",
        "## Exposure by Market",
        "",
    ]
    for market_id, exposure_usd in sorted(dict(exposure.get("exposure_by_market_usd", {})).items()):
        lines.append(f"- `{market_id}`: `${exposure_usd}`")
    lines.extend(
        [
            "",
            "## Open Paper Positions",
            "",
            *bullet_lines(
                f"`{row.get('market_id')}` `${row.get('paper_exposure_usd')}` unresolved"
                for row in report.get("open_paper_positions", [])
            ),
            "",
            "## Simulated Fills",
            "",
            *bullet_lines(
                f"`{row.get('market_id')}` `${row.get('filled_notional_usd')}`"
                for row in report.get("simulated_fills", [])
            ),
            "",
            "## Safety",
            "",
            "- Paper accounting only.",
            "- No real trading advice, order instruction, wallet action, or trading endpoint is included.",
        ]
    )
    return "\n".join(lines) + "\n"
