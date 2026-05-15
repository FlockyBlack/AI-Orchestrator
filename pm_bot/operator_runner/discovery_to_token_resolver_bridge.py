from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

from pm_bot.trading_core.discovery_to_token_resolver_bridge import (
    fail_closed_for_forbidden_flags,
    render_discovery_to_token_resolver_bridge_summary,
    run_discovery_to_token_resolver_bridge,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run PMBOT discovery to token resolver bridge 071D.")
    parser.add_argument("--market", default="BTC", help="Allowed market scope. Only BTC is accepted.")
    parser.add_argument(
        "--strategy",
        default="tiny-momentum",
        help="Allowed strategy scope. Only tiny-momentum is accepted.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Required. Writes no-trading bridge artifacts.")
    parser.add_argument(
        "--select-candidate-id",
        "--selected-candidate-id",
        dest="selected_candidate_id",
        default="",
        help="Optional operator-selected source-backed bridge candidate id.",
    )
    parser.add_argument(
        "--discovery-result",
        default="",
        help="Optional explicit 071A public discovery result artifact path.",
    )
    parser.add_argument(
        "--discovery-artifacts-dir",
        "--discovery-artifact-dir",
        dest="discovery_artifacts_dir",
        default="",
        help="Optional 071A artifact directory. Defaults to the 071A artifact directory.",
    )
    parser.add_argument(
        "--artifacts-dir",
        "--artifact-dir",
        dest="artifacts_dir",
        default="",
        help="Optional output directory. Defaults to the 071D artifact directory.",
    )
    parser.add_argument("--json", action="store_true", help="Print latest bridge status JSON.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    raw_args = list(sys.argv[1:] if argv is None else argv)
    fail_closed_for_forbidden_flags(raw_args)
    args = build_parser().parse_args(raw_args)
    if args.dry_run is not True:
        raise SystemExit("discovery to token resolver bridge requires --dry-run; live execution is blocked")

    result = run_discovery_to_token_resolver_bridge(
        market=args.market,
        strategy=args.strategy,
        dry_run=True,
        discovery_result_path=Path(args.discovery_result) if args.discovery_result else None,
        discovery_artifacts_dir=Path(args.discovery_artifacts_dir) if args.discovery_artifacts_dir else None,
        selected_candidate_id=args.selected_candidate_id,
        artifact_dir=Path(args.artifacts_dir) if args.artifacts_dir else None,
    )
    status = dict(result.get("latest_status", {}))
    if args.json:
        print(json.dumps(status, indent=2, sort_keys=True))
    else:
        print(render_discovery_to_token_resolver_bridge_summary(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
