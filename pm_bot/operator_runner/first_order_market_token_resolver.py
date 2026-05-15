from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

from pm_bot.trading_core.first_order_market_token_resolver import (
    fail_closed_for_forbidden_flags,
    render_first_order_market_token_cli_summary,
    run_first_order_market_token_resolver,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run PMBOT first order market token resolver 070B.")
    parser.add_argument("--market", default="BTC", help="Allowed market scope. Only BTC is accepted.")
    parser.add_argument(
        "--strategy",
        default="tiny-momentum",
        help="Allowed strategy scope. Only tiny-momentum is accepted.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Required. Writes no-trading resolver artifacts.")
    parser.add_argument("--market-slug", default="", help="Optional Polymarket market slug to validate.")
    parser.add_argument("--condition-id", default="", help="Optional 0x-prefixed condition_id to validate.")
    parser.add_argument("--token-id", default="", help="Optional explicit positive decimal outcome token_id.")
    parser.add_argument("--outcome", "--outcome-name", dest="outcome_name", default="", help="Optional outcome label.")
    parser.add_argument(
        "--artifacts-dir",
        "--artifact-dir",
        dest="artifacts_dir",
        default="",
        help="Optional output directory. Defaults to the 070B artifact directory.",
    )
    parser.add_argument("--json", action="store_true", help="Print latest resolver status JSON.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    raw_args = list(sys.argv[1:] if argv is None else argv)
    fail_closed_for_forbidden_flags(raw_args)
    args = build_parser().parse_args(raw_args)
    if args.dry_run is not True:
        raise SystemExit("first order market/token resolver requires --dry-run; live execution is blocked")

    result = run_first_order_market_token_resolver(
        market=args.market,
        strategy=args.strategy,
        dry_run=True,
        market_slug=args.market_slug,
        condition_id=args.condition_id,
        token_id=args.token_id,
        outcome_name=args.outcome_name,
        artifact_dir=Path(args.artifacts_dir) if args.artifacts_dir else None,
    )
    status = dict(result.get("latest_status", {}))
    if args.json:
        print(json.dumps(status, indent=2, sort_keys=True))
    else:
        print(render_first_order_market_token_cli_summary(status))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
