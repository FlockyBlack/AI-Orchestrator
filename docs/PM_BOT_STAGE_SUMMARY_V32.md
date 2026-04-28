# PM Bot Stage Summary V32

## PMBOT-BRAIN-020 Portfolio Risk Scenario Coverage

- Status: completed_ready_for_review
- Scope: deterministic offline paper scenario coverage for local snapshot series portfolio risk limits
- Command: `python pm_bot\paper\run_local_snapshot_series_risk_scenarios.py`
- Markdown: `python pm_bot\paper\run_local_snapshot_series_risk_scenarios.py --markdown`

## Scenario Coverage

- Scenario count: 7
- Allowed paper orders: 7
- Duplicate orders blocked: 2
- Risk-limit orders blocked: 6
- Realized paper PnL: 100.00
- Bad entries: 0
- Safety flags locked: true

## Risk-Limit Reason Counts

- `max_total_paper_exposure_exceeded`: 3
- `max_asset_paper_exposure_exceeded`: 1
- `max_orders_per_snapshot_exceeded`: 2
- `max_open_positions_exceeded`: 1

## Included Scenarios

- `baseline_valid_order_allowed`
- `duplicate_market_side_blocked`
- `total_exposure_breach_blocked`
- `asset_exposure_breach_blocked`
- `max_orders_per_snapshot_breach_blocked`
- `max_open_positions_breach_blocked`
- `mixed_allowed_and_blocked_orders`

## Verification

- `python -m pytest pm_bot\paper\tests\test_run_local_snapshot_series_risk_scenarios.py -q`
- `python -m pytest pm_bot\scoring\tests pm_bot\paper\tests -q`
- `python pm_bot\paper\run_local_snapshot_series_risk_scenarios.py`
- `python pm_bot\paper\run_local_snapshot_series_risk_scenarios.py --markdown`
- `python pm_bot\paper\run_local_snapshot_series_paper_portfolio.py`
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

No live fetchers, network/API calls, credentials, wallet/private-key handling, real orders, live trading, runtime wiring, command-routing changes, prompt automation, broad refactor, unrelated cleanup, or new validation layer were added.
