from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

from pm_bot.trading_core.signer_boundary_preflight import (
    fail_closed_for_forbidden_flags,
    render_signer_boundary_preflight_cli_summary,
    run_signer_boundary_preflight,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run PMBOT signer boundary preflight 060.")
    parser.add_argument("--market", default="BTC", help="Market symbol or review label.")
    parser.add_argument("--strategy", default="tiny-momentum", help="Paper strategy name.")
    parser.add_argument("--dry-run", action="store_true", help="Required. Generates review-only preflight artifacts.")
    parser.add_argument(
        "--from-latest-paper-intent",
        action="store_true",
        help="Use the latest 053 paper intent artifact. This is the default source preference.",
    )
    parser.add_argument(
        "--from-latest-public-market-loop",
        action="store_true",
        help="Use the latest 054 public-market paper loop intent artifact if available.",
    )
    parser.add_argument(
        "--mock-unsigned-plan",
        action="store_true",
        help="Allow a schema-only unsigned plan artifact even when the source intent is missing.",
    )
    parser.add_argument(
        "--artifacts-dir",
        "--artifact-dir",
        dest="artifacts_dir",
        default="",
        help="Optional output directory. Defaults to the 060 signer boundary preflight artifact directory.",
    )
    parser.add_argument("--json", action="store_true", help="Print latest preflight status JSON.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    raw_args = list(sys.argv[1:] if argv is None else argv)
    fail_closed_for_forbidden_flags(raw_args)
    args = build_parser().parse_args(raw_args)
    if args.dry_run is not True:
        raise SystemExit("signer boundary preflight requires --dry-run; live execution is blocked")

    result = run_signer_boundary_preflight(
        market=args.market,
        strategy=args.strategy,
        dry_run=True,
        from_latest_paper_intent=True,
        from_latest_public_market_loop=args.from_latest_public_market_loop,
        mock_unsigned_plan=args.mock_unsigned_plan,
        artifact_dir=Path(args.artifacts_dir) if args.artifacts_dir else None,
    )
    status = dict(result.get("latest_status", {}))
    if args.json:
        print(json.dumps(status, indent=2, sort_keys=True))
    else:
        print(render_signer_boundary_preflight_cli_summary(status))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
