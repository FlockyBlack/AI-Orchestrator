# PM Bot Stage Summary V31

## PMBOT-BRAIN-019 Portfolio Risk Limits

- Status: completed_ready_for_review
- Scope: deterministic local snapshot series paper portfolio replay only
- Root confirmed: `C:\Users\OpenC\Documents\AI-Orchestrator`
- Risk fixture: `pm_bot/paper/portfolio_risk_limits.v1.json`
- Output modes: JSON by default, Markdown with `--markdown`

## Replay Summary

- Paper orders created: 1
- Duplicate orders blocked: 1
- Risk-limit orders blocked: 1
- Risk-limit reason counts: `max_total_paper_exposure_exceeded=1`, `max_open_positions_exceeded=1`
- Total paper notional: 100.00
- Max exposure: 100.00
- Realized paper PnL: 72.41
- Bad entries: 0
- Safety flags locked: true

## Implemented Limits

- `max_total_paper_exposure`
- `max_asset_paper_exposure`
- `max_orders_per_snapshot`
- `max_open_positions`
- Duplicate market/side block remains active before portfolio risk checks.
- JSON and Markdown include the risk-limit config used, blocked-order decision rows, and reason-code counts.

## Verification

- `python -m pytest pm_bot\paper\tests\test_run_local_snapshot_series_paper_portfolio.py -q`
- `python -m pytest pm_bot\scoring\tests pm_bot\paper\tests -q`
- `python pm_bot\paper\run_local_snapshot_series_paper_portfolio.py`
- `python pm_bot\paper\run_local_snapshot_series_paper_portfolio.py --markdown`
- `python pm_bot\paper\run_crypto_numeric_lifecycle_regression_gates.py`

## Safety

- offline_only=true
- paper_only=true
- live_fetcher_implemented=false
- execution_allowed=false
- trading_allowed=false
- real_order_created=false
- wallet_used=false
- api_used=false
- network_used=false

No live fetchers, network/API calls, credentials, wallet/private-key handling, real orders, live trading, runtime wiring, dispatcher changes, prompt automation, unrelated cleanup, or new validation layer were added.
