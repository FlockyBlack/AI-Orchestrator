from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

from pm_bot.trading_core.live_connector_preflight import (
    fail_closed_for_forbidden_flags,
    render_live_connector_preflight_cli_summary,
    run_live_connector_preflight,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run PMBOT supervised live connector preflight 056.")
    parser.add_argument("--market", default="BTC", help="Market symbol or review label.")
    parser.add_argument("--dry-run", action="store_true", help="Required. Generates review-only preflight artifacts.")
    parser.add_argument(
        "--network-check",
        action="store_true",
        help="Also evaluate configured public CLOB base URL shape. No CLOB request is made.",
    )
    parser.add_argument(
        "--auth-check",
        action="store_true",
        help="Check redacted auth presence markers only; never perform authenticated requests.",
    )
    parser.add_argument(
        "--public-only",
        action="store_true",
        help="Force public-only mode and skip auth presence checks.",
    )
    parser.add_argument(
        "--artifacts-dir",
        "--artifact-dir",
        dest="artifacts_dir",
        default="",
        help="Optional output directory. Defaults to the 056 live connector preflight artifact directory.",
    )
    parser.add_argument("--json", action="store_true", help="Print latest preflight status JSON.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    raw_args = list(sys.argv[1:] if argv is None else argv)
    fail_closed_for_forbidden_flags(raw_args)
    args = build_parser().parse_args(raw_args)
    if args.dry_run is not True:
        raise SystemExit("live connector preflight requires --dry-run; live execution is blocked")

    auth_check = args.auth_check is True and args.public_only is not True
    public_only = args.public_only is True or auth_check is not True
    result = run_live_connector_preflight(
        market=args.market,
        dry_run=True,
        public_only=public_only,
        network_check=args.network_check,
        auth_check=auth_check,
        artifact_dir=Path(args.artifacts_dir) if args.artifacts_dir else None,
    )
    status = dict(result.get("latest_status", {}))
    if args.json:
        print(json.dumps(status, indent=2, sort_keys=True))
    else:
        print(render_live_connector_preflight_cli_summary(status))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
