from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

from pm_bot.trading_core.guarded_signer_diagnostic_smoke import (
    fail_closed_for_forbidden_flags,
    render_guarded_signer_diagnostic_cli_summary,
    run_guarded_signer_diagnostic_smoke,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run PMBOT guarded signer diagnostic smoke 069A.")
    parser.add_argument("--market", default="BTC", help="Market symbol or review label.")
    parser.add_argument("--strategy", default="tiny-momentum", help="Paper strategy name.")
    parser.add_argument("--dry-run", action="store_true", help="Required. Generates guarded no-order artifacts.")
    parser.add_argument(
        "--allow-private-key-diagnostic",
        action="store_true",
        help="Explicitly allow reading POLYMARKET_PRIVATE_KEY for the guarded local signer diagnostic.",
    )
    parser.add_argument(
        "--artifacts-dir",
        "--artifact-dir",
        dest="artifacts_dir",
        default="",
        help="Optional output directory. Defaults to the 069A guarded signer diagnostic artifact directory.",
    )
    parser.add_argument("--json", action="store_true", help="Print latest diagnostic status JSON.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    raw_args = list(sys.argv[1:] if argv is None else argv)
    fail_closed_for_forbidden_flags(raw_args)
    args = build_parser().parse_args(raw_args)
    if args.dry_run is not True:
        raise SystemExit("guarded signer diagnostic smoke requires --dry-run; live execution is blocked")

    result = run_guarded_signer_diagnostic_smoke(
        market=args.market,
        strategy=args.strategy,
        dry_run=True,
        allow_private_key_diagnostic=args.allow_private_key_diagnostic is True,
        artifact_dir=Path(args.artifacts_dir) if args.artifacts_dir else None,
    )
    status = dict(result.get("latest_status", {}))
    if args.json:
        print(json.dumps(status, indent=2, sort_keys=True))
    else:
        print(render_guarded_signer_diagnostic_cli_summary(status))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
