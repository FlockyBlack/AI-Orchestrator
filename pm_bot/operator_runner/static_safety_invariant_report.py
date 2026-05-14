from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

from pm_bot.trading_core.static_safety_invariant_report import (
    DEFAULT_SCOPE,
    fail_closed_for_forbidden_flags,
    render_static_safety_invariant_cli_summary,
    run_static_safety_invariant_report,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run PMBOT static safety invariant report 060Q.")
    parser.add_argument("--scope", default=DEFAULT_SCOPE, help="Repository-relative scan scope. Defaults to pm_bot.")
    parser.add_argument("--dry-run", action="store_true", help="Required. Generates review-only safety artifacts.")
    parser.add_argument(
        "--artifacts",
        action="store_true",
        help="Also scan committed PMBOT trading_core artifacts.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Include docs/tests as allowed-reference scan inputs and exit nonzero on critical findings.",
    )
    parser.add_argument(
        "--artifacts-dir",
        "--artifact-dir",
        dest="artifacts_dir",
        default="",
        help="Optional output directory. Defaults to the 060Q static safety invariant artifact directory.",
    )
    parser.add_argument("--json", action="store_true", help="Print latest report status JSON.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    raw_args = list(sys.argv[1:] if argv is None else argv)
    fail_closed_for_forbidden_flags(raw_args)
    args = build_parser().parse_args(raw_args)
    if args.dry_run is not True:
        raise SystemExit("static safety invariant report requires --dry-run; live execution is blocked")
    result = run_static_safety_invariant_report(
        scope=args.scope,
        dry_run=True,
        include_artifacts=args.artifacts is True,
        strict=args.strict is True,
        artifact_dir=Path(args.artifacts_dir) if args.artifacts_dir else None,
    )
    status = dict(result.get("latest_status", {}))
    if args.json:
        print(json.dumps(status, indent=2, sort_keys=True))
    else:
        print(render_static_safety_invariant_cli_summary(status))
    if args.strict and int(status.get("critical_count", 0) or 0) > 0:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
