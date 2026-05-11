from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Mapping, Sequence

from pm_bot.trading_core.schemas import ARTIFACT_DIR, GENERATED_AT, bullet_lines, write_json, write_text

FUTURE_REAL_ADAPTER_BOUNDARY_CONTRACT = "pmbot_future_real_adapter_boundary.v1"


def build_future_real_adapter_boundary(*, generated_at: str = GENERATED_AT) -> dict[str, Any]:
    return {
        "contract_version": FUTURE_REAL_ADAPTER_BOUNDARY_CONTRACT,
        "boundary_id": "future-real-adapter-boundary-night-020-021",
        "generated_at": generated_at,
        "real_adapter_implemented": False,
        "wallet_implemented": False,
        "signing_implemented": False,
        "orders_implemented": False,
        "authenticated_endpoints_implemented": False,
        "kill_switch_required": True,
        "reconciliation_required": True,
        "manual_approval_required": True,
        "risk_engine_upgrade_required": True,
        "required_before_any_supervised_real_execution": [
            "Separate explicit approval task",
            "Wallet isolation design not implemented yet",
            "Signing isolation design not implemented yet",
            "Order adapter boundary not implemented yet",
            "Hard kill switch",
            "Post-order reconciliation not implemented yet",
            "Manual pre-trade approval gate",
            "Risk engine upgrade with tested caps and halt states",
        ],
        "not_implemented": [
            "real adapter",
            "wallet",
            "signing",
            "orders",
            "authenticated endpoints",
        ],
    }


def write_future_real_adapter_boundary(
    *,
    out_json_path: str | Path = ARTIFACT_DIR / "future_real_adapter_boundary.json",
    out_md_path: str | Path = ARTIFACT_DIR / "future_real_adapter_boundary.md",
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    boundary = build_future_real_adapter_boundary(generated_at=generated_at)
    write_json(out_json_path, boundary)
    write_text(out_md_path, render_future_real_adapter_boundary_markdown(boundary))
    return boundary


def render_future_real_adapter_boundary_markdown(boundary: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# PMBOT Future Real Adapter Boundary",
            "",
            "The real adapter is not implemented in this milestone.",
            "",
            "## Not implemented",
            "",
            *bullet_lines(f"{item} not implemented" for item in boundary.get("not_implemented", [])),
            "",
            "## Required before any supervised real execution",
            "",
            *bullet_lines(str(item) for item in boundary.get("required_before_any_supervised_real_execution", [])),
            "",
            "## Boundary flags",
            "",
            f"- real_adapter_implemented: `{str(boundary.get('real_adapter_implemented')).lower()}`",
            f"- wallet_implemented: `{str(boundary.get('wallet_implemented')).lower()}`",
            f"- signing_implemented: `{str(boundary.get('signing_implemented')).lower()}`",
            f"- orders_implemented: `{str(boundary.get('orders_implemented')).lower()}`",
            f"- authenticated_endpoints_implemented: `{str(boundary.get('authenticated_endpoints_implemented')).lower()}`",
            f"- kill_switch_required: `{str(boundary.get('kill_switch_required')).lower()}`",
            f"- reconciliation_required: `{str(boundary.get('reconciliation_required')).lower()}`",
            f"- manual_approval_required: `{str(boundary.get('manual_approval_required')).lower()}`",
            f"- risk_engine_upgrade_required: `{str(boundary.get('risk_engine_upgrade_required')).lower()}`",
        ]
    ) + "\n"


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Write the PMBOT future real adapter boundary artifact.")
    parser.add_argument("--out-json", default=str(ARTIFACT_DIR / "future_real_adapter_boundary.json"))
    parser.add_argument("--out-md", default=str(ARTIFACT_DIR / "future_real_adapter_boundary.md"))
    args = parser.parse_args(argv)
    write_future_real_adapter_boundary(out_json_path=args.out_json, out_md_path=args.out_md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
