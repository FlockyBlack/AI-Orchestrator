# PMBOT Local Snapshot Inbox Paper Portfolio

Deterministic offline processing of local snapshot inbox files against a saved paper portfolio state.

## Input

- Inbox path: /pm_bot/paper/local_snapshot_inbox
- Input state path: /pm_bot/paper/paper_portfolio_state.v1.json
- Input processed snapshots: 1
- Input open positions: 1
- Input settled positions: 0
- Input exposure: 100.00
- Input realized paper PnL: 0.00

## Summary

- Snapshot files discovered: 3
- Snapshots skipped already processed: 1
- Snapshots processed: 2
- New paper orders created: 0
- Duplicate orders blocked: 1
- Risk-limit orders blocked: 1
- Open positions after run: 0
- Settled positions after run: 1
- Exposure after run: 0.00
- Realized paper PnL after run: 72.41
- Output state path: 
- Output state written: false
- Run ledger path: 
- Run ledger written: false
- Safety flags locked: true

## Snapshot Files

| file | snapshot_id | observed_at | status |
| --- | --- | --- | --- |
| 001_series_snapshot_001.json | series_snapshot_001 | 2026-05-01T12:00:00Z | skipped |
| 002_series_snapshot_002.json | series_snapshot_002 | 2026-05-15T12:00:00Z | processed |
| 003_series_snapshot_003.json | series_snapshot_003 | 2026-05-31T23:59:00Z | processed |

## Snapshot Runs

| snapshot_id | orders | duplicates | risk_blocks | open | settled | exposure | realized_pnl |
| --- | --- | --- | --- | --- | --- | --- | --- |
| series_snapshot_002 | 0 | 1 | 1 | 1 | 0 | 100.00 | 0.00 |
| series_snapshot_003 | 0 | 0 | 0 | 0 | 1 | 0.00 | 72.41 |

## Portfolio Events

| event_type | timestamp | market_id | side | reason |
| --- | --- | --- | --- | --- |
| duplicate_paper_order_blocked | 2026-05-15T12:00:00Z | series_btc_above_90000_2026_05_31 | above | Paper position already exists for this market and side. |
| risk_limit_paper_order_blocked | 2026-05-15T12:00:00Z | series_eth_below_3000_2026_05_31 | below | Paper order would exceed max_total_paper_exposure.; Paper order would exceed max_open_positions. |
| no_action_preserved | 2026-05-31T23:59:00Z | series_btc_above_90000_2026_05_31 | above | decision is reject; edge_after_buffer below minimum |
| no_action_preserved | 2026-05-31T23:59:00Z | series_eth_below_3000_2026_05_31 | below | decision is reject; edge_after_buffer below minimum |
| paper_position_settled | 2026-05-31T23:59:00Z | series_btc_above_90000_2026_05_31 | above |  |

## Limitations

- Uses deterministic local snapshot inbox files and paper state fixtures only; no live fetcher, network, external API, credentials, wallet access, real orders, or live trading is included.
- Default run is read-only and writes state only when --out-state is provided.
- No runtime integration, command-routing changes, prompt automation, broad refactor, or new validation layer is included.

- offline_only=true; paper_only=true; live_fetcher_implemented=false; execution_allowed=false; trading_allowed=false; real_order_created=false; wallet_used=false; api_used=false; network_used=false
