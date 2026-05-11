from __future__ import annotations

from typing import Any, Mapping

from pm_bot.trading_core.schemas import (
    GENERATED_AT,
    bullet_lines,
    clean_text,
    mapping_rows,
    trading_core_safety_summary,
)

PAPER_PORTFOLIO_ROLLFORWARD_CONTRACT = "pmbot_paper_portfolio_rollforward.v1"


def build_paper_portfolio_rollforward(
    *,
    previous_ledger: Mapping[str, Any] | None,
    previous_portfolio_state: Mapping[str, Any] | None,
    current_ledger: Mapping[str, Any],
    current_portfolio_state: Mapping[str, Any],
    idempotency_report: Mapping[str, Any],
    run_id: str,
    run_date: str,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    previous_positions = mapping_rows((previous_ledger or {}).get("positions"))
    current_positions = mapping_rows(current_ledger.get("positions"))
    previous_open_keys = {
        clean_text(row.get("idempotency_key") or row.get("source_execution_id"))
        for row in previous_positions
        if clean_text(row.get("outcome_status") or "unresolved") == "unresolved"
    }
    carried_positions = [
        row
        for row in current_positions
        if clean_text(row.get("idempotency_key") or row.get("source_execution_id")) in previous_open_keys
    ]
    current_position_ids = {clean_text(row.get("position_id")) for row in current_positions}
    dropped_previous_positions = [
        row
        for row in previous_positions
        if clean_text(row.get("position_id")) not in current_position_ids
        and clean_text(row.get("outcome_status") or "unresolved") != "unresolved"
    ]
    carried_exposure = round(sum(float(row.get("paper_exposure_usd", 0) or 0) for row in carried_positions), 2)
    return {
        "contract_version": PAPER_PORTFOLIO_ROLLFORWARD_CONTRACT,
        "rollforward_id": f"paper-portfolio-rollforward-023-{run_date}",
        "generated_at": generated_at,
        "run_id": run_id,
        "run_date": run_date,
        "previous_ledger_loaded": previous_ledger is not None,
        "previous_portfolio_loaded": previous_portfolio_state is not None,
        "previous_open_position_count": len(
            [row for row in previous_positions if clean_text(row.get("outcome_status") or "unresolved") == "unresolved"]
        ),
        "previous_total_paper_exposure_usd": float((previous_portfolio_state or {}).get("total_paper_exposure_usd", 0) or 0),
        "carried_forward_position_count": len(carried_positions),
        "carried_forward_exposure_usd": carried_exposure,
        "new_position_count": int(idempotency_report.get("new_applied_count", 0) or 0),
        "already_applied_count": int(idempotency_report.get("already_applied_count", 0) or 0),
        "already_open_position_count": int(idempotency_report.get("already_open_position_count", 0) or 0),
        "duplicate_fill_prevented_count": int(idempotency_report.get("duplicate_fill_prevented_count", 0) or 0),
        "dropped_resolved_position_count": len(dropped_previous_positions),
        "current_open_position_count": int(current_ledger.get("open_position_count", 0) or 0),
        "current_total_paper_exposure_usd": float(current_portfolio_state.get("total_paper_exposure_usd", 0) or 0),
        "exposure_preserved": carried_exposure <= float(current_portfolio_state.get("total_paper_exposure_usd", 0) or 0),
        "carried_forward_positions": [_position_summary(row) for row in carried_positions],
        "new_positions": [
            _position_summary(row)
            for row in current_positions
            if clean_text(row.get("idempotency_key") or row.get("source_execution_id")) not in previous_open_keys
        ],
        "paper_only": True,
        "outcome_resolution_invented": False,
        "safety_summary": trading_core_safety_summary(),
    }


def render_paper_portfolio_rollforward_markdown(report: Mapping[str, Any]) -> str:
    lines = [
        "# PMBOT Paper Portfolio Rollforward",
        "",
        f"- Previous ledger loaded: `{str(report.get('previous_ledger_loaded')).lower()}`",
        f"- Previous portfolio loaded: `{str(report.get('previous_portfolio_loaded')).lower()}`",
        f"- Previous open positions: {report.get('previous_open_position_count')}",
        f"- Carried-forward positions: {report.get('carried_forward_position_count')}",
        f"- New positions: {report.get('new_position_count')}",
        f"- Duplicate fills prevented: {report.get('duplicate_fill_prevented_count')}",
        f"- Current open positions: {report.get('current_open_position_count')}",
        f"- Current paper exposure: `${report.get('current_total_paper_exposure_usd')}`",
        "",
        "## Carried-Forward Positions",
        "",
    ]
    lines.extend(
        bullet_lines(
            f"`{row.get('market_id')}` `${row.get('paper_exposure_usd')}` `{row.get('outcome_status')}`"
            for row in mapping_rows(report.get("carried_forward_positions"))
        )
    )
    lines.extend(
        [
            "",
            "## New Positions",
            "",
            *bullet_lines(
                f"`{row.get('market_id')}` `${row.get('paper_exposure_usd')}` `{row.get('outcome_status')}`"
                for row in mapping_rows(report.get("new_positions"))
            ),
            "",
            "## Safety",
            "",
            "- Rollforward carries paper-only unresolved positions.",
            "- Resolved outcomes are not invented.",
            "- No wallet, order, live price, or trading endpoint is used.",
        ]
    )
    return "\n".join(lines) + "\n"


def _position_summary(position: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "position_id": clean_text(position.get("position_id")),
        "idempotency_key": clean_text(position.get("idempotency_key")),
        "market_id": clean_text(position.get("market_id")),
        "market_title": clean_text(position.get("market_title")),
        "intent_id": clean_text(position.get("intent_id")),
        "run_date": clean_text(position.get("run_date")),
        "paper_exposure_usd": float(position.get("paper_exposure_usd", 0) or 0),
        "paper_units": float(position.get("paper_units", 0) or 0),
        "outcome_status": clean_text(position.get("outcome_status") or "unresolved"),
        "paper_only": True,
    }
