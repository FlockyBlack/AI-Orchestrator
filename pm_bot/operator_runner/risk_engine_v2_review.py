from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

from pm_bot.trading_core.risk_engine_v2_review import (
    fail_closed_for_forbidden_flags,
    render_risk_engine_v2_review_cli_summary,
    run_risk_engine_v2_review,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run PMBOT Risk Engine v2 local review.")
    parser.add_argument("--market", default="BTC", help="Market symbol or review label.")
    parser.add_argument("--strategy", default="tiny-momentum", help="Paper strategy name.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Required. Reads local artifacts only and keeps all live behavior blocked.",
    )
    parser.add_argument(
        "--artifact-root",
        default="",
        help="Optional input artifact root. Defaults to pm_bot/trading_core/artifacts.",
    )
    parser.add_argument(
        "--artifacts-dir",
        "--artifact-dir",
        dest="artifacts_dir",
        default="",
        help="Optional output directory. Defaults to the 074D Risk Engine v2 artifact directory.",
    )
    parser.add_argument("--json", action="store_true", help="Print latest status JSON.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    raw_args = list(sys.argv[1:] if argv is None else argv)
    fail_closed_for_forbidden_flags(raw_args)
    args = build_parser().parse_args(raw_args)
    if args.dry_run is not True:
        raise SystemExit("Risk Engine v2 review requires --dry-run; live execution is blocked")

    generated = run_risk_engine_v2_review(
        market=args.market,
        strategy=args.strategy,
        dry_run=True,
        artifact_root=Path(args.artifact_root) if args.artifact_root else None,
        output_dir=Path(args.artifacts_dir) if args.artifacts_dir else None,
    )
    status = dict(generated.get("latest_status", {}))
    if args.json:
        _safe_print(json.dumps(status, indent=2, sort_keys=True, ensure_ascii=False))
    else:
        _safe_print(render_risk_engine_v2_review_cli_summary(status))
    return 0


def _safe_print(value: str) -> None:
    text = str(value)
    try:
        print(text)
    except UnicodeEncodeError:
        sys.stdout.buffer.write(text.encode("utf-8", errors="replace") + b"\n")


if __name__ == "__main__":
    raise SystemExit(main())
