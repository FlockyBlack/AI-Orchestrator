from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

from pm_bot.trading_core.live_readonly_status_aggregator import (
    fail_closed_for_forbidden_flags,
    render_live_readonly_status_aggregator_cli_summary,
    run_live_readonly_status_aggregator,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run PMBOT live read-only status aggregator 071B.")
    parser.add_argument("--market", default="BTC", help="Market symbol or review label.")
    parser.add_argument("--strategy", default="tiny-momentum", help="Paper strategy name.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Required. Aggregates local read-only status artifacts and blocks all live behavior.",
    )
    parser.add_argument(
        "--artifact-root",
        default="",
        help="Optional input artifact root. Defaults to pm_bot/trading_core/artifacts.",
    )
    parser.add_argument(
        "--artifacts-dir",
        "--artifact-dir",
        dest="artifacts_dir",
        default="",
        help="Optional output directory. Defaults to the 071B live read-only status artifact directory.",
    )
    parser.add_argument("--json", action="store_true", help="Print latest status JSON.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    raw_args = list(sys.argv[1:] if argv is None else argv)
    fail_closed_for_forbidden_flags(raw_args)
    args = build_parser().parse_args(raw_args)
    if args.dry_run is not True:
        raise SystemExit("live read-only status aggregator requires --dry-run; live execution is blocked")

    result = run_live_readonly_status_aggregator(
        market=args.market,
        strategy=args.strategy,
        dry_run=True,
        artifact_root=Path(args.artifact_root) if args.artifact_root else None,
        artifact_dir=Path(args.artifacts_dir) if args.artifacts_dir else None,
    )
    status = dict(result.get("latest_status", {}))
    if args.json:
        print(json.dumps(status, indent=2, sort_keys=True))
    else:
        print(render_live_readonly_status_aggregator_cli_summary(status))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
