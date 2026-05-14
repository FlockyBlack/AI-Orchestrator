from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

from pm_bot.trading_core.paper_decision_ledger import (
    SOURCE_LATEST,
    SUPPORTED_SOURCES,
    fail_closed_for_forbidden_flags,
    render_paper_decision_ledger_telegram_status,
    run_paper_decision_ledger,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Append a PMBOT paper-only decision ledger entry 055.")
    parser.add_argument("--market", default="BTC", help="Market symbol or review label.")
    parser.add_argument("--strategy", default="tiny-momentum", help="Paper strategy name.")
    parser.add_argument("--dry-run", action="store_true", help="Required. Generates review-only ledger artifacts.")
    parser.add_argument(
        "--artifacts-dir",
        "--artifact-dir",
        dest="artifacts_dir",
        default="",
        help="Optional ledger artifact directory. Also used to discover test source artifacts.",
    )
    parser.add_argument(
        "--source",
        choices=SUPPORTED_SOURCES,
        default=SOURCE_LATEST,
        help="Artifact source to read. Defaults to latest available 054, then 053, then 052.",
    )
    parser.add_argument("--json", action="store_true", help="Print latest ledger status JSON.")
    parser.add_argument("--reset-for-test", action="store_true", help="Remove known 055 ledger artifacts before appending.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    raw_args = list(sys.argv[1:] if argv is None else argv)
    fail_closed_for_forbidden_flags(raw_args)
    args = build_parser().parse_args(raw_args)
    if args.dry_run is not True:
        raise SystemExit("paper decision ledger requires --dry-run; live execution is blocked")
    result = run_paper_decision_ledger(
        market=args.market,
        strategy=args.strategy,
        dry_run=True,
        artifact_dir=Path(args.artifacts_dir) if args.artifacts_dir else None,
        source=args.source,
        reset_for_test=args.reset_for_test,
    )
    status = dict(result.get("latest_status", {}))
    if args.json:
        print(json.dumps(status, indent=2, sort_keys=True))
    else:
        print(render_paper_decision_ledger_telegram_status(status))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
