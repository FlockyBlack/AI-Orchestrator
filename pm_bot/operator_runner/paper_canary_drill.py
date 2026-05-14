from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from pm_bot.trading_core.paper_canary_drill import (
    render_paper_canary_telegram_status,
    run_paper_canary_drill,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the PMBOT paper canary drill 052.")
    parser.add_argument("--market", default="BTC", help="Fixture market symbol. Currently supports BTC.")
    parser.add_argument("--dry-run", action="store_true", help="Required. Generates review-only paper artifacts.")
    parser.add_argument(
        "--artifact-dir",
        default="",
        help="Optional output directory. Defaults to PMBOT_ARTIFACT_DIR or the repo paper canary artifact directory.",
    )
    parser.add_argument(
        "--network-check",
        action="store_true",
        help="Records an explicit network-check request but remains fixture-only in this task.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.dry_run is not True:
        raise SystemExit("paper canary drill requires --dry-run; live execution is not available")
    result = run_paper_canary_drill(
        market=args.market,
        dry_run=True,
        artifact_dir=Path(args.artifact_dir) if args.artifact_dir else None,
        network_check=args.network_check,
        write_artifacts=True,
    )
    status = dict(result.get("operator_ui_status_feed", {}))
    print(render_paper_canary_telegram_status(status))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
