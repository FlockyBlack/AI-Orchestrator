from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

from pm_bot.trading_core.clob_l2_auth_readonly_probe import (
    fail_closed_for_forbidden_flags,
    render_clob_l2_auth_readonly_probe_cli_summary,
    run_clob_l2_auth_readonly_probe,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run PMBOT CLOB L2 auth read-only probe 067C.")
    parser.add_argument("--market", default="BTC", help="Market symbol or review label.")
    parser.add_argument("--strategy", default="tiny-momentum", help="Paper strategy name.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Required. Allows a bounded read-only auth probe and blocks all order/wallet/signing behavior.",
    )
    parser.add_argument(
        "--artifacts-dir",
        "--artifact-dir",
        dest="artifacts_dir",
        default="",
        help="Optional output directory. Defaults to the 067C CLOB L2 auth read-only probe artifact directory.",
    )
    parser.add_argument("--json", action="store_true", help="Print latest status JSON.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    raw_args = list(sys.argv[1:] if argv is None else argv)
    fail_closed_for_forbidden_flags(raw_args)
    args = build_parser().parse_args(raw_args)
    if args.dry_run is not True:
        raise SystemExit("CLOB L2 auth read-only probe requires --dry-run; order execution is blocked")

    result = run_clob_l2_auth_readonly_probe(
        market=args.market,
        strategy=args.strategy,
        dry_run=True,
        artifact_dir=Path(args.artifacts_dir) if args.artifacts_dir else None,
    )
    status = dict(result.get("latest_status", {}))
    if args.json:
        print(json.dumps(status, indent=2, sort_keys=True))
    else:
        print(render_clob_l2_auth_readonly_probe_cli_summary(status))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
