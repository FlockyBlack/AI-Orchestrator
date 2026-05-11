from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path
from typing import Sequence

from pm_bot.operator_runner.paper_daily_config import DEFAULT_PAPER_DAILY_OUTPUT_DIR, PaperDailyConfigError, PaperDailyLoopConfig
from pm_bot.operator_runner.paper_daily_loop import run_paper_daily_loop


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the PMBOT local paper-only daily loop.")
    parser.add_argument("--run-date", default=date.today().isoformat())
    parser.add_argument("--max-markets", type=int, default=6)
    parser.add_argument("--output-dir", default=str(DEFAULT_PAPER_DAILY_OUTPUT_DIR))
    parser.add_argument("--previous-ledger", default=None)
    parser.add_argument("--previous-portfolio", default=None)
    parser.add_argument("--dry-run", action="store_true", default=False)
    parser.add_argument("--write-artifacts", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--allow-network", action="store_true", default=False)
    parser.add_argument("--allow-real-trading", action="store_true", default=False)
    parser.add_argument("--allow-openrouter", action="store_true", default=False)
    parser.add_argument("--allow-polymarket-api", action="store_true", default=False)
    args = parser.parse_args(argv)

    try:
        config = PaperDailyLoopConfig(
            run_date=args.run_date,
            max_markets=args.max_markets,
            output_dir=Path(args.output_dir),
            previous_ledger_path=Path(args.previous_ledger) if args.previous_ledger else None,
            previous_portfolio_path=Path(args.previous_portfolio) if args.previous_portfolio else None,
            allow_network=args.allow_network,
            allow_real_trading=args.allow_real_trading,
            allow_openrouter=args.allow_openrouter,
            allow_polymarket_api=args.allow_polymarket_api,
            write_artifacts=args.write_artifacts and not args.dry_run,
        )
        result = run_paper_daily_loop(config)
    except PaperDailyConfigError as exc:
        parser.error(str(exc))
    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
