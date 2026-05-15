from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

from pm_bot.trading_core.signed_payload_diagnostic_adapter import (
    fail_closed_for_forbidden_flags,
    render_signed_payload_diagnostic_adapter_cli_summary,
    run_signed_payload_diagnostic_adapter,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run PMBOT signed payload diagnostic adapter 072E.")
    parser.add_argument("--market", default="BTC", help="Market symbol or review label.")
    parser.add_argument("--strategy", default="tiny-momentum", help="Paper strategy name.")
    parser.add_argument("--dry-run", action="store_true", help="Required. Writes no-submit adapter artifacts.")
    parser.add_argument(
        "--token-candidate-path",
        default="",
        help="Optional local selected token candidate artifact path.",
    )
    parser.add_argument(
        "--order-prep-artifact-path",
        default="",
        help="Optional local order prep/status artifact path.",
    )
    parser.add_argument(
        "--signer-diagnostic-status-path",
        default="",
        help="Optional local guarded signer diagnostic status artifact path.",
    )
    parser.add_argument(
        "--signed-payload-dry-run-status-path",
        default="",
        help="Optional local signed payload dry-run status artifact path.",
    )
    parser.add_argument(
        "--allow-future-signing-diagnostic",
        action="store_true",
        help="Request the future signing diagnostic interface. 072E fails closed as not implemented.",
    )
    parser.add_argument(
        "--artifacts-dir",
        "--artifact-dir",
        dest="artifacts_dir",
        default="",
        help="Optional output directory. Defaults to the 072E signed payload diagnostic adapter artifact directory.",
    )
    parser.add_argument("--json", action="store_true", help="Print latest adapter status JSON.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    raw_args = list(sys.argv[1:] if argv is None else argv)
    fail_closed_for_forbidden_flags(raw_args)
    args = build_parser().parse_args(raw_args)
    if args.dry_run is not True:
        raise SystemExit("signed payload diagnostic adapter requires --dry-run; live execution is blocked")

    result = run_signed_payload_diagnostic_adapter(
        market=args.market,
        strategy=args.strategy,
        dry_run=True,
        token_candidate_path=Path(args.token_candidate_path) if args.token_candidate_path else None,
        order_prep_artifact_path=Path(args.order_prep_artifact_path) if args.order_prep_artifact_path else None,
        signer_diagnostic_status_path=Path(args.signer_diagnostic_status_path)
        if args.signer_diagnostic_status_path
        else None,
        signed_payload_dry_run_status_path=Path(args.signed_payload_dry_run_status_path)
        if args.signed_payload_dry_run_status_path
        else None,
        allow_future_signing_diagnostic=args.allow_future_signing_diagnostic is True,
        artifact_dir=Path(args.artifacts_dir) if args.artifacts_dir else None,
    )
    status = dict(result.get("latest_status", {}))
    if args.json:
        print(json.dumps(status, indent=2, sort_keys=True))
    else:
        print(render_signed_payload_diagnostic_adapter_cli_summary(status))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
