from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

from pm_bot.trading_core.signed_order_payload_dry_run import (
    fail_closed_for_forbidden_flags,
    render_signed_order_payload_dry_run_cli_summary,
    build_signed_order_payload_dry_run,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run PMBOT signed order payload dry-run 070A.")
    parser.add_argument("--market", default="BTC", help="Market symbol or review label.")
    parser.add_argument("--strategy", default="tiny-momentum", help="Paper strategy name.")
    parser.add_argument("--dry-run", action="store_true", help="Required. Generates no-submit dry-run artifacts.")
    parser.add_argument(
        "--token-id",
        default="",
        help="Optional public token identifier for a future local diagnostic; stored only as a fingerprint.",
    )
    parser.add_argument(
        "--max-notional-usd",
        type=float,
        default=1.0,
        help="Maximum notional guard for any future local diagnostic. Must be <= 1.0 USD.",
    )
    parser.add_argument(
        "--allow-local-order-payload-signing-diagnostic",
        action="store_true",
        help="Explicitly request the guarded local payload signing diagnostic. 070A fails closed as not implemented.",
    )
    parser.add_argument(
        "--artifacts-dir",
        "--artifact-dir",
        dest="artifacts_dir",
        default="",
        help="Optional output directory. Defaults to the 070A signed order payload dry-run artifact directory.",
    )
    parser.add_argument("--json", action="store_true", help="Print latest dry-run status JSON.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    raw_args = list(sys.argv[1:] if argv is None else argv)
    fail_closed_for_forbidden_flags(raw_args)
    args = build_parser().parse_args(raw_args)
    if args.dry_run is not True:
        raise SystemExit("signed order payload dry-run requires --dry-run; live execution is blocked")

    result = build_signed_order_payload_dry_run(
        market=args.market,
        strategy=args.strategy,
        dry_run=True,
        token_id=args.token_id,
        max_notional_usd=args.max_notional_usd,
        allow_local_order_payload_signing_diagnostic=args.allow_local_order_payload_signing_diagnostic is True,
        artifact_dir=Path(args.artifacts_dir) if args.artifacts_dir else None,
    )
    status = dict(result.get("latest_status", {}))
    if args.json:
        print(json.dumps(status, indent=2, sort_keys=True))
    else:
        print(render_signed_order_payload_dry_run_cli_summary(status))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
