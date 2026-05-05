# PMBOT Local Snapshot Paper Portfolio State

Deterministic offline processing of one local snapshot against a saved paper portfolio state.

## Input

- Snapshot: series_snapshot_002
- Observed at: 2026-05-15T12:00:00Z
- Input open positions: 1
- Input settled positions: 0
- Input exposure: 100.00
- Input realized paper PnL: 0.00

## Summary

- New paper orders created: 0
- Duplicate orders blocked: 1
- Risk-limit orders blocked: 1
- Open positions after run: 1
- Settled positions after run: 0
- Exposure after run: 100.00
- Realized paper PnL after run: 0.00
- Output state path: 
- Output state written: false
- Safety flags locked: true

## Events

| event_type | timestamp | market_id | side | reason |
| --- | --- | --- | --- | --- |
| duplicate_paper_order_blocked | 2026-05-15T12:00:00Z | series_btc_above_90000_2026_05_31 | above | Paper position already exists for this market and side. |
| risk_limit_paper_order_blocked | 2026-05-15T12:00:00Z | series_eth_below_3000_2026_05_31 | below | Paper order would exceed max_total_paper_exposure.; Paper order would exceed max_open_positions. |

## Limitations

- Uses deterministic local snapshot and paper state fixtures only; no live fetcher, network, external API, credentials, wallet access, real orders, or live trading is included.
- Default run is read-only and writes state only when --out-state is provided.
- No runtime integration, command-routing changes, prompt automation, broad refactor, or new validation layer is included.

- offline_only=true; paper_only=true; live_fetcher_implemented=false; execution_allowed=false; trading_allowed=false; real_order_created=false; wallet_used=false; api_used=false; network_used=false
