from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Mapping, Sequence

from pm_bot.trading_core.paper_position_ledger import run_paper_position_ledger
from pm_bot.trading_core.risk_limits import default_paper_risk_limits
from pm_bot.trading_core.schemas import (
    ARTIFACT_DIR,
    GENERATED_AT,
    PORTFOLIO_STATE_CONTRACT,
    assert_valid,
    bullet_lines,
    clean_text,
    load_json_object,
    mapping_rows,
    trading_core_safety_summary,
    validate_portfolio_state,
    write_json,
    write_text,
)

DEFAULT_TOTAL_PAPER_CAPITAL_USD = 1000.0


def build_portfolio_state(
    *,
    ledger: Mapping[str, Any],
    risk_limits: Mapping[str, Any] | None = None,
    unresolved_market_count: int = 6,
    feedback_ready_count: int = 0,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    limits = dict(risk_limits or default_paper_risk_limits(generated_at=generated_at))
    exposure_by_market: dict[str, float] = {}
    for position in mapping_rows(ledger.get("positions")):
        market_id = clean_text(position.get("market_id"))
        exposure_by_market[market_id] = round(
            exposure_by_market.get(market_id, 0.0) + float(position.get("paper_exposure_usd", 0) or 0),
            2,
        )
    total_exposure = round(sum(exposure_by_market.values()), 2)
    total_capital = DEFAULT_TOTAL_PAPER_CAPITAL_USD
    available_capital = round(max(total_capital - total_exposure, 0.0), 2)
    state = {
        "contract_version": PORTFOLIO_STATE_CONTRACT,
        "portfolio_id": "paper-portfolio-state-night-020-021",
        "generated_at": generated_at,
        "total_paper_capital_usd": total_capital,
        "total_paper_exposure_usd": total_exposure,
        "available_paper_capital_usd": available_capital,
        "exposure_by_market_usd": exposure_by_market,
        "open_position_count": int(ledger.get("open_position_count", 0) or 0),
        "unresolved_market_count": unresolved_market_count,
        "feedback_ready_count": feedback_ready_count,
        "risk_usage": {
            "total_exposure_limit_usd": limits.get("max_total_paper_exposure_usd"),
            "total_exposure_usage_pct": round(
                total_exposure / float(limits.get("max_total_paper_exposure_usd", 1) or 1) * 100,
                2,
            ),
            "max_market_exposure_usd": limits.get("max_market_paper_exposure_usd"),
            "max_market_exposure_usage_pct": round(
                (max(exposure_by_market.values()) if exposure_by_market else 0)
                / float(limits.get("max_market_paper_exposure_usd", 1) or 1)
                * 100,
                2,
            ),
            "open_position_limit": limits.get("max_open_paper_positions"),
            "open_position_usage_pct": round(
                int(ledger.get("open_position_count", 0) or 0)
                / float(limits.get("max_open_paper_positions", 1) or 1)
                * 100,
                2,
            ),
        },
        "paper_only": True,
        "real_money_used": False,
        "live_prices_used": False,
        "safety_summary": trading_core_safety_summary(),
    }
    valid, errors = validate_portfolio_state(state)
    assert_valid(state["portfolio_id"], valid, errors)
    return state


def run_portfolio_state(
    *,
    ledger: Mapping[str, Any] | None = None,
    risk_limits: Mapping[str, Any] | None = None,
    out_json_path: str | Path = ARTIFACT_DIR / "paper_portfolio_state.json",
    out_md_path: str | Path = ARTIFACT_DIR / "paper_portfolio_state.md",
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    active_ledger = dict(ledger or run_paper_position_ledger(generated_at=generated_at))
    state = build_portfolio_state(ledger=active_ledger, risk_limits=risk_limits, generated_at=generated_at)
    write_json(out_json_path, state)
    write_text(out_md_path, render_portfolio_state_markdown(state))
    return state


def render_portfolio_state_markdown(state: Mapping[str, Any]) -> str:
    lines = [
        "# PMBOT Paper Portfolio State",
        "",
        f"- Total paper capital: `${state.get('total_paper_capital_usd')}`",
        f"- Total paper exposure: `${state.get('total_paper_exposure_usd')}`",
        f"- Available paper capital: `${state.get('available_paper_capital_usd')}`",
        f"- Open paper positions: {state.get('open_position_count')}",
        f"- Unresolved markets: {state.get('unresolved_market_count')}",
        f"- Feedback ready: {state.get('feedback_ready_count')}",
        "",
        "## Exposure by market",
        "",
    ]
    for market_id, exposure in sorted(dict(state.get("exposure_by_market_usd", {})).items()):
        lines.append(f"- `{market_id}`: `${exposure}`")
    lines.extend(
        [
            "",
            "## Risk usage",
            "",
            *bullet_lines(f"{key}: `{value}`" for key, value in dict(state.get("risk_usage", {})).items()),
            "",
            "## Safety",
            "",
            "- Paper portfolio only.",
            "- No real money, wallet, live price, or trading endpoint is used.",
        ]
    )
    return "\n".join(lines) + "\n"


def load_and_run_portfolio_state(
    *,
    ledger_path: str | Path = ARTIFACT_DIR / "paper_position_ledger.json",
    risk_limits_path: str | Path = ARTIFACT_DIR / "paper_risk_limits.json",
    out_json_path: str | Path = ARTIFACT_DIR / "paper_portfolio_state.json",
    out_md_path: str | Path = ARTIFACT_DIR / "paper_portfolio_state.md",
) -> dict[str, Any]:
    ledger = load_json_object(ledger_path, label="paper position ledger")
    limits = load_json_object(risk_limits_path, label="paper risk limits")
    return run_portfolio_state(
        ledger=ledger,
        risk_limits=limits,
        out_json_path=out_json_path,
        out_md_path=out_md_path,
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build PMBOT paper portfolio state.")
    parser.add_argument("--ledger", default=str(ARTIFACT_DIR / "paper_position_ledger.json"))
    parser.add_argument("--limits", default=str(ARTIFACT_DIR / "paper_risk_limits.json"))
    parser.add_argument("--out-json", default=str(ARTIFACT_DIR / "paper_portfolio_state.json"))
    parser.add_argument("--out-md", default=str(ARTIFACT_DIR / "paper_portfolio_state.md"))
    args = parser.parse_args(argv)
    load_and_run_portfolio_state(
        ledger_path=args.ledger,
        risk_limits_path=args.limits,
        out_json_path=args.out_json,
        out_md_path=args.out_md,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
