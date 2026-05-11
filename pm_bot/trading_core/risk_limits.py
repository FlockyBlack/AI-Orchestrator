from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Mapping, Sequence

from pm_bot.trading_core.schemas import ARTIFACT_DIR, GENERATED_AT, bullet_lines, write_json, write_text

PAPER_RISK_LIMITS_CONTRACT = "pmbot_paper_risk_limits.v1"


def default_paper_risk_limits(*, generated_at: str = GENERATED_AT) -> dict[str, Any]:
    return {
        "contract_version": PAPER_RISK_LIMITS_CONTRACT,
        "risk_limits_id": "paper-risk-limits-night-020-021",
        "generated_at": generated_at,
        "max_total_paper_exposure_usd": 1000,
        "max_market_paper_exposure_usd": 100,
        "max_single_intent_notional_usd": 25,
        "max_open_paper_positions": 10,
        "allow_real_orders": False,
        "allow_wallet": False,
        "allow_trading_endpoints": False,
        "allow_autonomous_execution": False,
        "require_operator_review": True,
    }


def write_default_paper_risk_limits(
    *,
    out_json_path: str | Path = ARTIFACT_DIR / "paper_risk_limits.json",
    out_md_path: str | Path = ARTIFACT_DIR / "paper_risk_limits.md",
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    limits = default_paper_risk_limits(generated_at=generated_at)
    write_json(out_json_path, limits)
    write_text(out_md_path, render_paper_risk_limits_markdown(limits))
    return limits


def render_paper_risk_limits_markdown(limits: Mapping[str, Any]) -> str:
    rows = [
        f"max_total_paper_exposure_usd: `{limits.get('max_total_paper_exposure_usd')}`",
        f"max_market_paper_exposure_usd: `{limits.get('max_market_paper_exposure_usd')}`",
        f"max_single_intent_notional_usd: `{limits.get('max_single_intent_notional_usd')}`",
        f"max_open_paper_positions: `{limits.get('max_open_paper_positions')}`",
        f"allow_real_orders: `{str(limits.get('allow_real_orders')).lower()}`",
        f"allow_wallet: `{str(limits.get('allow_wallet')).lower()}`",
        f"allow_trading_endpoints: `{str(limits.get('allow_trading_endpoints')).lower()}`",
        f"allow_autonomous_execution: `{str(limits.get('allow_autonomous_execution')).lower()}`",
        f"require_operator_review: `{str(limits.get('require_operator_review')).lower()}`",
    ]
    return "\n".join(
        [
            "# PMBOT Paper Risk Limits",
            "",
            "These limits apply only to local paper simulation.",
            "",
            "## Limits",
            "",
            *bullet_lines(rows),
        ]
    ) + "\n"


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Write default PMBOT paper risk limits.")
    parser.add_argument("--out-json", default=str(ARTIFACT_DIR / "paper_risk_limits.json"))
    parser.add_argument("--out-md", default=str(ARTIFACT_DIR / "paper_risk_limits.md"))
    args = parser.parse_args(argv)
    write_default_paper_risk_limits(out_json_path=args.out_json, out_md_path=args.out_md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
