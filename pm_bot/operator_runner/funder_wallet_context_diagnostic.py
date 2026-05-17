from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

from pm_bot.trading_core.funder_wallet_context_077g import (
    fail_closed_for_forbidden_flags,
    render_funder_wallet_context_cli_summary,
    run_funder_wallet_context_diagnostic,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run PMBOT Polymarket funder wallet context diagnostic 077G."
    )
    parser.add_argument("--market", default="BTC", help="Market symbol or review label.")
    parser.add_argument("--strategy", default="tiny-momentum", help="Paper strategy name.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Required. Checks explicit wallet/funder environment visibility and writes redacted no-live artifacts.",
    )
    parser.add_argument(
        "--artifacts-dir",
        "--artifact-dir",
        dest="artifacts_dir",
        default="",
        help=(
            "Optional output directory. Defaults to PMBOT_ARTIFACT_DIR/funder_wallet_context_077g "
            "when PMBOT_ARTIFACT_DIR is set, otherwise the repo 077G artifact directory."
        ),
    )
    parser.add_argument("--json", action="store_true", help="Print latest funder wallet context status JSON.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    raw_args = list(sys.argv[1:] if argv is None else argv)
    fail_closed_for_forbidden_flags(raw_args)
    args = build_parser().parse_args(raw_args)
    if args.dry_run is not True:
        raise SystemExit("funder wallet context diagnostic requires --dry-run; live execution is blocked")

    result = run_funder_wallet_context_diagnostic(
        market=args.market,
        strategy=args.strategy,
        dry_run=True,
        artifact_dir=Path(args.artifacts_dir) if args.artifacts_dir else None,
    )
    status = dict(result.get("latest_status", {}))
    if args.json:
        print(json.dumps(status, indent=2, sort_keys=True))
    else:
        print(render_funder_wallet_context_cli_summary(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
