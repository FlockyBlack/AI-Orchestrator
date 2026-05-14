from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from pm_bot.trading_core.paper_trading_loop import (
    render_paper_trading_loop_telegram_status,
    run_paper_trading_loop,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the PMBOT paper trading loop 053.")
    parser.add_argument("--market", default="BTC", help="Fixture market symbol. Currently supports BTC.")
    parser.add_argument("--strategy", default="tiny-momentum", help="Paper strategy name.")
    parser.add_argument("--dry-run", action="store_true", help="Required. Generates review-only paper artifacts.")
    parser.add_argument("--fixture", default="", help="Optional fixture JSON path.")
    parser.add_argument(
        "--artifacts-dir",
        "--artifact-dir",
        dest="artifacts_dir",
        default="",
        help="Optional output directory. Defaults to PMBOT_ARTIFACT_DIR or the 053 artifact directory.",
    )
    parser.add_argument("--json", action="store_true", help="Print latest status JSON instead of concise text.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.dry_run is not True:
        raise SystemExit("paper trading loop requires --dry-run; live execution is blocked")
    result = run_paper_trading_loop(
        market=args.market,
        strategy=args.strategy,
        dry_run=True,
        fixture=Path(args.fixture) if args.fixture else None,
        artifact_dir=Path(args.artifacts_dir) if args.artifacts_dir else None,
        write_artifacts=True,
    )
    status = dict(result.get("latest_status", {}))
    if args.json:
        print(json.dumps(status, indent=2, sort_keys=True))
    else:
        print(render_paper_trading_loop_telegram_status(status))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
