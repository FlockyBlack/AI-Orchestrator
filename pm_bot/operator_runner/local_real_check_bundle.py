from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

from pm_bot.trading_core.local_real_check_bundle import (
    fail_closed_for_forbidden_flags,
    render_local_real_check_bundle_cli_summary,
    run_local_real_check_bundle,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run PMBOT local real-check bundle 072C.")
    parser.add_argument("--market", default="BTC", help="Market symbol or review label.")
    parser.add_argument("--strategy", default="tiny-momentum", help="Paper strategy name.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Required. Runs a manual one-shot read-only bundle and blocks all live behavior.",
    )
    parser.add_argument(
        "--allow-private-key-diagnostic",
        action="store_true",
        help="Optional. Passes only to the guarded signer diagnostic smoke.",
    )
    parser.add_argument("--query", default="", help="Optional public discovery query.")
    parser.add_argument("--slug", default="", help="Optional public discovery market slug.")
    parser.add_argument("--tag-id", default="", help="Optional public discovery tag id.")
    parser.add_argument("--limit", type=int, default=25, help="Public discovery result limit.")
    parser.add_argument(
        "--local-artifact",
        action="append",
        default=[],
        help="Optional source-backed local public discovery artifact. Can be passed more than once.",
    )
    parser.add_argument(
        "--subcheck-artifact-root",
        default="",
        help="Optional root for subcheck artifacts. Defaults to pm_bot/trading_core/artifacts.",
    )
    parser.add_argument(
        "--artifacts-dir",
        "--artifact-dir",
        dest="artifacts_dir",
        default="",
        help="Optional bundle output directory. Defaults to the 072C artifact directory.",
    )
    parser.add_argument("--json", action="store_true", help="Print latest status JSON.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    raw_args = list(sys.argv[1:] if argv is None else argv)
    fail_closed_for_forbidden_flags(raw_args)
    args = build_parser().parse_args(raw_args)
    if args.dry_run is not True:
        raise SystemExit("local real-check bundle requires --dry-run; live execution is blocked")

    result = run_local_real_check_bundle(
        market=args.market,
        strategy=args.strategy,
        dry_run=True,
        allow_private_key_diagnostic=args.allow_private_key_diagnostic is True,
        artifact_dir=Path(args.artifacts_dir) if args.artifacts_dir else None,
        subcheck_artifact_root=Path(args.subcheck_artifact_root) if args.subcheck_artifact_root else None,
        public_discovery_local_artifact_paths=[Path(path) for path in args.local_artifact] if args.local_artifact else None,
        public_discovery_query=args.query,
        public_discovery_slug=args.slug,
        public_discovery_tag_id=args.tag_id,
        public_discovery_limit=args.limit,
    )
    status = dict(result.get("latest_status", {}))
    if args.json:
        print(json.dumps(status, indent=2, sort_keys=True))
    else:
        print(render_local_real_check_bundle_cli_summary(status))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
