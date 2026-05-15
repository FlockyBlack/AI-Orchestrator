from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

from pm_bot.trading_core.signer_smoke_contract import (
    build_signer_smoke_contract,
    fail_closed_for_forbidden_flags,
    render_signer_smoke_contract_cli_summary,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run PMBOT signer smoke contract 068A.")
    parser.add_argument("--market", default="BTC", help="Market symbol or review label.")
    parser.add_argument("--strategy", default="tiny-momentum", help="Paper strategy name.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Optional explicit marker. Dry-run contract-only mode is the default and only enabled mode.",
    )
    parser.add_argument(
        "--artifacts-dir",
        "--artifact-dir",
        dest="artifacts_dir",
        default="",
        help="Optional output directory. Defaults to the 068A signer smoke contract artifact directory.",
    )
    parser.add_argument("--json", action="store_true", help="Print latest contract status JSON.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    raw_args = list(sys.argv[1:] if argv is None else argv)
    fail_closed_for_forbidden_flags(raw_args)
    args = build_parser().parse_args(raw_args)

    result = build_signer_smoke_contract(
        market=args.market,
        strategy=args.strategy,
        dry_run=True,
        artifact_dir=Path(args.artifacts_dir) if args.artifacts_dir else None,
    )
    status = dict(result.get("latest_status", {}))
    if args.json:
        print(json.dumps(status, indent=2, sort_keys=True))
    else:
        print(render_signer_smoke_contract_cli_summary(status))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
