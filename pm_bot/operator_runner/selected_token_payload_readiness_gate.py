from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

from pm_bot.trading_core.selected_token_payload_readiness_gate import (
    fail_closed_for_forbidden_flags,
    render_selected_token_payload_readiness_cli_summary,
    run_selected_token_payload_readiness_gate,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run PMBOT selected token payload readiness gate 073C.")
    parser.add_argument("--market", default="BTC", help="Market symbol or review label.")
    parser.add_argument("--strategy", default="tiny-momentum", help="Paper strategy name.")
    parser.add_argument("--dry-run", action="store_true", help="Required. Writes no-submit readiness artifacts.")
    parser.add_argument(
        "--selected-candidate-artifact-path",
        default="",
        help="Optional local selected candidate artifact 075D path.",
    )
    parser.add_argument(
        "--operator-token-selection-packet-path",
        default="",
        help="Optional local operator token selection packet 073B artifact path.",
    )
    parser.add_argument(
        "--selected-token-verification-bridge-path",
        default="",
        help="Optional local selected token verification bridge 076A artifact path.",
    )
    parser.add_argument(
        "--first-order-market-token-contract-path",
        default="",
        help="Optional local first order market token resolver 070B contract artifact path.",
    )
    parser.add_argument(
        "--signer-diagnostic-status-path",
        default="",
        help="Optional local guarded signer diagnostic 069A status artifact path.",
    )
    parser.add_argument(
        "--approval-contract-status-path",
        default="",
        help="Optional local first live order approval contract 065D status artifact path.",
    )
    parser.add_argument(
        "--signed-payload-dry-run-status-path",
        default="",
        help="Optional local signed payload dry-run 070A status artifact path.",
    )
    parser.add_argument(
        "--signed-payload-diagnostic-adapter-status-path",
        default="",
        help="Optional local signed payload diagnostic adapter 072E status artifact path.",
    )
    parser.add_argument(
        "--artifacts-dir",
        "--artifact-dir",
        dest="artifacts_dir",
        default="",
        help="Optional output directory. Defaults to the 073C readiness gate artifact directory.",
    )
    parser.add_argument("--json", action="store_true", help="Print latest readiness status JSON.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    raw_args = list(sys.argv[1:] if argv is None else argv)
    fail_closed_for_forbidden_flags(raw_args)
    args = build_parser().parse_args(raw_args)
    if args.dry_run is not True:
        raise SystemExit("selected token payload readiness gate requires --dry-run; submit/cancel/live is blocked")

    result = run_selected_token_payload_readiness_gate(
        market=args.market,
        strategy=args.strategy,
        dry_run=True,
        selected_candidate_artifact_path=Path(args.selected_candidate_artifact_path)
        if args.selected_candidate_artifact_path
        else None,
        operator_token_selection_packet_path=Path(args.operator_token_selection_packet_path)
        if args.operator_token_selection_packet_path
        else None,
        selected_token_verification_bridge_path=Path(args.selected_token_verification_bridge_path)
        if args.selected_token_verification_bridge_path
        else None,
        first_order_market_token_contract_path=Path(args.first_order_market_token_contract_path)
        if args.first_order_market_token_contract_path
        else None,
        signer_diagnostic_status_path=Path(args.signer_diagnostic_status_path)
        if args.signer_diagnostic_status_path
        else None,
        approval_contract_status_path=Path(args.approval_contract_status_path)
        if args.approval_contract_status_path
        else None,
        signed_payload_dry_run_status_path=Path(args.signed_payload_dry_run_status_path)
        if args.signed_payload_dry_run_status_path
        else None,
        signed_payload_diagnostic_adapter_status_path=Path(args.signed_payload_diagnostic_adapter_status_path)
        if args.signed_payload_diagnostic_adapter_status_path
        else None,
        artifact_dir=Path(args.artifacts_dir) if args.artifacts_dir else None,
    )
    status = dict(result.get("latest_status", {}))
    if args.json:
        print(json.dumps(status, indent=2, sort_keys=True))
    else:
        print(render_selected_token_payload_readiness_cli_summary(status))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
