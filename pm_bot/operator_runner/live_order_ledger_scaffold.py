from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

from pm_bot.trading_core.live_order_ledger_scaffold import (
    fail_closed_for_forbidden_flags,
    render_live_order_ledger_scaffold_cli_summary,
    run_live_order_ledger_scaffold,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run PMBOT live order ledger scaffold 066.")
    parser.add_argument("--market", default="BTC", help="Market symbol or review label.")
    parser.add_argument("--strategy", default="tiny-momentum", help="Paper strategy name.")
    parser.add_argument("--dry-run", action="store_true", help="Required. Generates schema-only artifacts.")
    parser.add_argument(
        "--artifacts-dir",
        "--artifact-dir",
        dest="artifacts_dir",
        default="",
        help="Optional output directory. Defaults to the 066 live order ledger scaffold artifact directory.",
    )
    parser.add_argument("--json", action="store_true", help="Print latest scaffold status JSON.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    raw_args = list(sys.argv[1:] if argv is None else argv)
    fail_closed_for_forbidden_flags(raw_args)
    args = build_parser().parse_args(raw_args)
    if args.dry_run is not True:
        raise SystemExit("live order ledger scaffold requires --dry-run; live execution is blocked")

    result = run_live_order_ledger_scaffold(
        market=args.market,
        strategy=args.strategy,
        dry_run=True,
        artifact_dir=Path(args.artifacts_dir) if args.artifacts_dir else None,
    )
    status = dict(result.get("latest_status", {}))
    if args.json:
        print(json.dumps(status, indent=2, sort_keys=True))
    else:
        print(render_live_order_ledger_scaffold_cli_summary(status))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
