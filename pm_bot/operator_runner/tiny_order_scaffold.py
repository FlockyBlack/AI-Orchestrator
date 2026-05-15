from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

from pm_bot.trading_core.tiny_order_scaffold import (
    DEFAULT_MAX_NOTIONAL,
    DEFAULT_MAX_PRICE,
    DEFAULT_MAX_SIZE,
    fail_closed_for_forbidden_flags,
    render_tiny_order_scaffold_cli_summary,
    run_tiny_order_scaffold,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run PMBOT tiny order scaffold 061.")
    parser.add_argument("--market", default="BTC", help="Market symbol or review label.")
    parser.add_argument("--strategy", default="tiny-momentum", help="Paper strategy name.")
    parser.add_argument("--dry-run", action="store_true", help="Required. Generates review-only scaffold artifacts.")
    parser.add_argument(
        "--from-latest-signer-boundary",
        action="store_true",
        help="Use the latest 060 signer boundary artifact as the only source.",
    )
    parser.add_argument(
        "--from-latest-paper-intent",
        action="store_true",
        help="Use the latest paper intent artifact as the only source unless signer boundary is also requested.",
    )
    parser.add_argument(
        "--max-notional",
        type=float,
        default=DEFAULT_MAX_NOTIONAL,
        help="Tiny notional cap for the review candidate.",
    )
    parser.add_argument(
        "--max-size",
        type=float,
        default=DEFAULT_MAX_SIZE,
        help="Tiny size cap for the review candidate.",
    )
    parser.add_argument(
        "--max-price",
        type=float,
        default=DEFAULT_MAX_PRICE,
        help="Tiny limit price cap for the review candidate.",
    )
    parser.add_argument(
        "--artifacts-dir",
        "--artifact-dir",
        dest="artifacts_dir",
        default="",
        help="Optional output directory. Defaults to the 061 tiny order scaffold artifact directory.",
    )
    parser.add_argument("--json", action="store_true", help="Print latest scaffold status JSON.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    raw_args = list(sys.argv[1:] if argv is None else argv)
    fail_closed_for_forbidden_flags(raw_args)
    args = build_parser().parse_args(raw_args)
    if args.dry_run is not True:
        raise SystemExit("tiny order scaffold requires --dry-run; live execution is blocked")

    result = run_tiny_order_scaffold(
        market=args.market,
        strategy=args.strategy,
        dry_run=True,
        from_latest_signer_boundary=args.from_latest_signer_boundary,
        from_latest_paper_intent=args.from_latest_paper_intent,
        max_notional=args.max_notional,
        max_size=args.max_size,
        max_price=args.max_price,
        artifact_dir=Path(args.artifacts_dir) if args.artifacts_dir else None,
    )
    status = dict(result.get("latest_status", {}))
    if args.json:
        print(json.dumps(status, indent=2, sort_keys=True))
    else:
        print(render_tiny_order_scaffold_cli_summary(status))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
