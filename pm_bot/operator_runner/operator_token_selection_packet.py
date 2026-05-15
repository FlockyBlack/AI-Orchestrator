from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

from pm_bot.trading_core.operator_token_selection_packet import (
    fail_closed_for_forbidden_flags,
    render_operator_token_selection_cli_summary,
    run_operator_token_selection_packet,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run PMBOT operator token selection packet 073B.")
    parser.add_argument("--market", default="BTC", help="Market symbol or review label.")
    parser.add_argument("--strategy", default="tiny-momentum", help="Paper strategy name.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Required. Builds a local non-executable operator token selection packet.",
    )
    parser.add_argument(
        "--candidate-index",
        default="",
        help="Optional zero-based source-backed candidate_index emitted by the packet.",
    )
    parser.add_argument("--token-id", default="", help="Optional manually supplied positive decimal token_id.")
    parser.add_argument("--market-slug", default="", help="Optional market slug to validate with the selection.")
    parser.add_argument("--condition-id", default="", help="Optional 0x-prefixed condition_id to validate.")
    parser.add_argument(
        "--artifact-root",
        default="",
        help="Optional input artifact root. Defaults to pm_bot/trading_core/artifacts.",
    )
    parser.add_argument(
        "--discovery-result",
        default="",
        help="Optional explicit 071A public discovery result artifact path.",
    )
    parser.add_argument(
        "--bridge-result",
        default="",
        help="Optional explicit 071D discovery bridge result artifact path.",
    )
    parser.add_argument(
        "--discovery-artifacts-dir",
        "--discovery-artifact-dir",
        dest="discovery_artifacts_dir",
        default="",
        help="Optional 071A artifact directory.",
    )
    parser.add_argument(
        "--bridge-artifacts-dir",
        "--bridge-artifact-dir",
        dest="bridge_artifacts_dir",
        default="",
        help="Optional 071D artifact directory.",
    )
    parser.add_argument(
        "--artifacts-dir",
        "--artifact-dir",
        dest="artifacts_dir",
        default="",
        help="Optional output directory. Defaults to the 073B artifact directory.",
    )
    parser.add_argument("--json", action="store_true", help="Print latest packet status JSON.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    raw_args = list(sys.argv[1:] if argv is None else argv)
    fail_closed_for_forbidden_flags(raw_args)
    args = build_parser().parse_args(raw_args)
    if args.dry_run is not True:
        raise SystemExit("operator token selection packet requires --dry-run; live execution is blocked")

    result = run_operator_token_selection_packet(
        market=args.market,
        strategy=args.strategy,
        dry_run=True,
        candidate_index=args.candidate_index,
        token_id=args.token_id,
        market_slug=args.market_slug,
        condition_id=args.condition_id,
        artifact_root=Path(args.artifact_root) if args.artifact_root else None,
        artifact_dir=Path(args.artifacts_dir) if args.artifacts_dir else None,
        discovery_result_path=Path(args.discovery_result) if args.discovery_result else None,
        bridge_result_path=Path(args.bridge_result) if args.bridge_result else None,
        discovery_artifacts_dir=Path(args.discovery_artifacts_dir) if args.discovery_artifacts_dir else None,
        bridge_artifacts_dir=Path(args.bridge_artifacts_dir) if args.bridge_artifacts_dir else None,
    )
    status = dict(result.get("latest_status", {}))
    if args.json:
        print(json.dumps(status, indent=2, sort_keys=True))
    else:
        print(render_operator_token_selection_cli_summary(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
