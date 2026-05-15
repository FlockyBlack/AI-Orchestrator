from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

from pm_bot.trading_core.public_market_token_discovery import (
    render_public_market_token_discovery_summary,
    run_public_market_token_discovery,
)
from pm_bot.trading_core.schemas import clean_text

FORBIDDEN_RUNTIME_FLAGS = (
    "--live",
    "--live-execution",
    "--execute",
    "--trade",
    "--auth",
    "--authenticated",
    "--wallet",
    "--private-key",
    "--sign",
    "--signing",
    "--order",
    "--submit",
    "--cancel",
    "--browser",
    "--loop",
    "--daemon",
    "--scheduler",
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run PMBOT public market token discovery 071A.")
    parser.add_argument("--market", default="BTC", help="Market symbol or review label.")
    parser.add_argument("--strategy", default="tiny-momentum", help="Review strategy label.")
    parser.add_argument("--dry-run", action="store_true", help="Required. Generates read-only discovery artifacts.")
    parser.add_argument("--query", default="", help="Optional public Gamma search query.")
    parser.add_argument("--slug", default="", help="Optional public Gamma market slug.")
    parser.add_argument("--tag-id", default="", help="Optional public Gamma tag id filter.")
    parser.add_argument("--limit", type=int, default=25, help="Public Gamma result limit.")
    parser.add_argument(
        "--local-artifact",
        action="append",
        default=[],
        help="Optional source-backed local artifact path. Can be passed more than once.",
    )
    parser.add_argument(
        "--artifacts-dir",
        "--artifact-dir",
        dest="artifacts_dir",
        default="",
        help="Optional output directory. Defaults to the 071A artifact directory.",
    )
    parser.add_argument("--json", action="store_true", help="Print latest status JSON.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    raw_args = list(sys.argv[1:] if argv is None else argv)
    fail_closed_for_forbidden_flags(raw_args)
    args = build_parser().parse_args(raw_args)
    if args.dry_run is not True:
        raise SystemExit("public market token discovery requires --dry-run; live execution is blocked")

    result = run_public_market_token_discovery(
        market=args.market,
        strategy=args.strategy,
        dry_run=True,
        query=args.query,
        slug=args.slug,
        tag_id=args.tag_id,
        limit=args.limit,
        artifact_dir=Path(args.artifacts_dir) if args.artifacts_dir else None,
        local_artifact_paths=[Path(path) for path in args.local_artifact] if args.local_artifact else None,
    )
    status = dict(result.get("latest_status", {}))
    if args.json:
        print(json.dumps(status, indent=2, sort_keys=True))
    else:
        print(render_public_market_token_discovery_summary(result))
    return 0


def fail_closed_for_forbidden_flags(argv: Sequence[str]) -> None:
    lowered = {clean_text(item).lower().split("=", 1)[0] for item in argv}
    requested = sorted(flag for flag in FORBIDDEN_RUNTIME_FLAGS if flag in lowered)
    if requested:
        raise SystemExit(
            "public market token discovery is read-only; unsupported live/auth/wallet/sign/order/browser flag(s): "
            + ", ".join(requested)
        )


if __name__ == "__main__":
    raise SystemExit(main())
