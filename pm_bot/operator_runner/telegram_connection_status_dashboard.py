from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping

from pm_bot.trading_core.schemas import clean_text
from pm_bot.trading_core.telegram_wallet_auth_status_dashboard import (
    DEFAULT_ARTIFACT_DIR,
    TASK_ID,
    write_telegram_wallet_auth_status_067e_artifacts,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build PMBOT Telegram connection status dashboard 067E.")
    parser.add_argument("--market", default="BTC", help="Accepted review label; no live market call is made.")
    parser.add_argument("--strategy", default="tiny-momentum", help="Accepted review label; no strategy execution is made.")
    parser.add_argument("--dry-run", action="store_true", help="Required; writes local status artifacts only.")
    parser.add_argument(
        "--artifact-root",
        default="pm_bot/trading_core/artifacts",
        help="Local artifact root to read redacted status artifacts from.",
    )
    parser.add_argument(
        "--output-dir",
        default=str(DEFAULT_ARTIFACT_DIR),
        help="Local output directory for 067E status artifacts.",
    )
    parser.add_argument("--json", action="store_true", help="Print the redacted 067E result as JSON.")
    args = parser.parse_args(argv)

    if args.dry_run is not True:
        raise SystemExit("telegram connection status 067E requires --dry-run; live execution is blocked")

    generated = write_telegram_wallet_auth_status_067e_artifacts(
        artifact_root=Path(args.artifact_root),
        output_dir=Path(args.output_dir),
    )
    if args.json:
        print(json.dumps(generated["result"], indent=2, sort_keys=True))
    else:
        print(render_cli_summary(generated["latest_status"]))
    return 0


def render_cli_summary(status: Mapping[str, Any]) -> str:
    value = dict(status or {})
    return "\n".join(
        [
            "Telegram connection status 067E completed.",
            f"Task: {TASK_ID}",
            f"Status: {clean_text(value.get('status') or 'not_available')}",
            f"API keys: {clean_text(value.get('api_keys_status') or 'not_added')}",
            f"Private key: {clean_text(value.get('private_key_status') or 'not_added')}",
            f"L2 auth probe: {clean_text(value.get('l2_auth_probe_display') or 'not run')}",
            f"Open orders: {clean_text(value.get('open_orders_status') or 'unknown')}",
            f"Balance/allowance: {clean_text(value.get('balance_allowance_status') or 'unknown')}",
            "Values never shown.",
            "Review-only; no live trading, signing, wallet connection, authenticated call, submit, or cancel action.",
            "Connection screen: Podklyuchenie / Connection",
        ]
    )


if __name__ == "__main__":
    raise SystemExit(main())
