from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

from pm_bot.trading_core.pre_live_tiny_order_gate import (
    DEFAULT_MAX_NOTIONAL,
    fail_closed_for_forbidden_flags,
    render_pre_live_tiny_order_gate_cli_summary,
    run_pre_live_tiny_order_gate,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run PMBOT pre-live tiny order gate 062P.")
    parser.add_argument("--market", default="BTC", help="Market symbol or review label.")
    parser.add_argument("--strategy", default="tiny-momentum", help="Paper strategy name.")
    parser.add_argument("--dry-run", action="store_true", help="Required. Generates review-only gate artifacts.")
    parser.add_argument(
        "--from-latest-tiny-scaffold",
        action="store_true",
        help="Use the latest 061 tiny order scaffold artifact. This is the default source preference.",
    )
    parser.add_argument(
        "--require-operator-approval",
        action="store_true",
        help="Keep manual operator approval as an explicit unresolved gate blocker.",
    )
    parser.add_argument(
        "--max-notional",
        type=float,
        default=DEFAULT_MAX_NOTIONAL,
        help="Tiny notional cap used only for review readiness evaluation.",
    )
    parser.add_argument(
        "--market-whitelist",
        default="BTC",
        help="Comma-separated market symbols allowed for this review gate.",
    )
    parser.add_argument(
        "--artifacts-dir",
        "--artifact-dir",
        dest="artifacts_dir",
        default="",
        help="Optional output directory. Defaults to the 062P pre-live gate artifact directory.",
    )
    parser.add_argument("--json", action="store_true", help="Print latest gate status JSON.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    raw_args = list(sys.argv[1:] if argv is None else argv)
    fail_closed_for_forbidden_flags(raw_args)
    args = build_parser().parse_args(raw_args)
    if args.dry_run is not True:
        raise SystemExit("pre-live tiny order gate requires --dry-run; live execution is blocked")

    result = run_pre_live_tiny_order_gate(
        market=args.market,
        strategy=args.strategy,
        dry_run=True,
        from_latest_tiny_scaffold=True,
        require_operator_approval=args.require_operator_approval,
        max_notional=args.max_notional,
        market_whitelist=args.market_whitelist,
        artifact_dir=Path(args.artifacts_dir) if args.artifacts_dir else None,
    )
    status = dict(result.get("latest_status", {}))
    if args.json:
        print(json.dumps(status, indent=2, sort_keys=True))
    else:
        print(render_pre_live_tiny_order_gate_cli_summary(status))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
