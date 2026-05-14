from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

from pm_bot.trading_core.authenticated_clob_preflight import (
    fail_closed_for_forbidden_flags,
    render_authenticated_clob_preflight_cli_summary,
    run_authenticated_clob_preflight,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run PMBOT authenticated no-order CLOB preflight 057.")
    parser.add_argument("--market", default="BTC", help="Market symbol or review label.")
    parser.add_argument("--dry-run", action="store_true", help="Required. Generates review-only preflight artifacts.")
    parser.add_argument(
        "--mock-auth",
        action="store_true",
        default=True,
        help="Use a mocked auth boundary plan. This is the default and performs no network request.",
    )
    parser.add_argument(
        "--auth-presence-only",
        action="store_true",
        help="Only check redacted L2 marker presence and skip the mocked no-order auth request plan.",
    )
    parser.add_argument(
        "--no-order-auth-check",
        action="store_true",
        default=True,
        help="Build the mocked no-order authenticated GET plan. No request is sent.",
    )
    parser.add_argument(
        "--no-order-auth-get",
        action="store_true",
        help="Run the optional task 059 no-order authenticated GET preflight boundary. Mocked by default.",
    )
    parser.add_argument(
        "--real-auth-read-only",
        action="store_true",
        help=(
            "Request real read-only authenticated GET mode. Requires --no-order-auth-get and "
            "PMBOT_ALLOW_REAL_NO_ORDER_AUTH_GET=true; fails closed otherwise."
        ),
    )
    parser.add_argument(
        "--clob-base-url",
        default="",
        help="Optional CLOB base URL override. The value is validated in memory and not written to artifacts.",
    )
    parser.add_argument(
        "--artifacts-dir",
        "--artifact-dir",
        dest="artifacts_dir",
        default="",
        help="Optional output directory. Defaults to the 057 authenticated CLOB preflight artifact directory.",
    )
    parser.add_argument("--json", action="store_true", help="Print latest preflight status JSON.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    raw_args = list(sys.argv[1:] if argv is None else argv)
    fail_closed_for_forbidden_flags(raw_args)
    args = build_parser().parse_args(raw_args)
    if args.dry_run is not True:
        raise SystemExit("authenticated CLOB preflight requires --dry-run; live execution is blocked")

    result = run_authenticated_clob_preflight(
        market=args.market,
        dry_run=True,
        mock_auth=True,
        auth_presence_only=args.auth_presence_only,
        no_order_auth_check=args.no_order_auth_check,
        no_order_auth_get_requested=args.no_order_auth_get,
        real_auth_read_only_requested=args.real_auth_read_only,
        clob_base_url=args.clob_base_url,
        artifact_dir=Path(args.artifacts_dir) if args.artifacts_dir else None,
    )
    status = dict(result.get("latest_status", {}))
    if args.json:
        print(json.dumps(status, indent=2, sort_keys=True))
    else:
        print(render_authenticated_clob_preflight_cli_summary(status))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
