# PMBOT Local Snapshot Series Paper Portfolio

Deterministic offline replay of repeated local live-shaped snapshot reviews into a carried paper portfolio.

## Summary

- Snapshots processed: 3
- Total snapshot markets: 8
- Adapted raw markets: 6
- Adapter rejections: 2
- Paper orders created: 1
- Duplicate orders blocked: 1
- Risk-limit orders blocked: 1
- Open positions: 0
- Settled positions: 1
- Total paper notional: 100.00
- Max exposure: 100.00
- Realized paper PnL: 72.41
- Unrealized paper PnL: 0.00
- Bad entries: 0
- Safety flags locked: true

## Risk Limits

| limit | value |
| --- | --- |
| max_total_paper_exposure | 100.00 |
| max_asset_paper_exposure | 100.00 |
| max_orders_per_snapshot | 1 |
| max_open_positions | 1 |

## Risk-Limit Reasons

| reason_code | count |
| --- | --- |
| max_open_positions_exceeded | 1 |
| max_total_paper_exposure_exceeded | 1 |

## Risk-Limit Decisions

| timestamp | market_id | asset | side | decision | reason_codes |
| --- | --- | --- | --- | --- | --- |
| 2026-05-15T12:00:00Z | series_eth_below_3000_2026_05_31 | ETH | below | blocked | max_total_paper_exposure_exceeded, max_open_positions_exceeded |

## Snapshot Exposure

| snapshot_id | markets | adapted | candidates | orders | duplicates | risk_blocks | open | settled | exposure | realized_pnl | unrealized_pnl |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| series_snapshot_001 | 3 | 2 | 1 | 1 | 0 | 0 | 1 | 0 | 100.00 | 0.00 | 6.90 |
| series_snapshot_002 | 2 | 2 | 2 | 0 | 1 | 1 | 1 | 0 | 100.00 | 0.00 | 27.59 |
| series_snapshot_003 | 3 | 2 | 0 | 0 | 0 | 0 | 0 | 1 | 0.00 | 72.41 | 0.00 |

## Portfolio Events

| event_type | timestamp | market_id | side | reason |
| --- | --- | --- | --- | --- |
| paper_order_created | 2026-05-01T12:00:00Z | series_btc_above_90000_2026_05_31 | above | Paper candidate filled from local series fixture observed_yes_price. |
| no_action_preserved | 2026-05-01T12:00:00Z | series_eth_below_3000_2026_05_31 | below | decision is watchlist; edge_after_buffer below minimum; risk needs operator review |
| duplicate_paper_order_blocked | 2026-05-15T12:00:00Z | series_btc_above_90000_2026_05_31 | above | Paper position already exists for this market and side. |
| risk_limit_paper_order_blocked | 2026-05-15T12:00:00Z | series_eth_below_3000_2026_05_31 | below | Paper order would exceed max_total_paper_exposure.; Paper order would exceed max_open_positions. |
| no_action_preserved | 2026-05-31T23:59:00Z | series_btc_above_90000_2026_05_31 | above | decision is reject; edge_after_buffer below minimum |
| no_action_preserved | 2026-05-31T23:59:00Z | series_eth_below_3000_2026_05_31 | below | decision is reject; edge_after_buffer below minimum |
| paper_position_settled | 2026-05-31T23:59:00Z | series_btc_above_90000_2026_05_31 | above |  |

## Paper Positions

| market_id | side | status | fill_price | shares | notional | paper_pnl |
| --- | --- | --- | --- | --- | --- | --- |
| series_btc_above_90000_2026_05_31 | above | settled | 0.5800 | 172.4138 | 100.00 | 72.41 |

## Rejections

| stage | snapshot_id | market_id | reason_code | reason |
| --- | --- | --- | --- | --- |
| adapter | series_snapshot_001 | series_missing_question | missing_question | Snapshot does not include a question or title. |
| adapter | series_snapshot_003 | series_missing_price | missing_price | Snapshot does not include a Yes outcome price. |
| scoring | series_snapshot_003 | series_btc_above_90000_2026_05_31 | reject | buffered edge is not positive |
| scoring | series_snapshot_003 | series_eth_below_3000_2026_05_31 | reject | buffered edge is not positive |

## Limitations

- Uses a local fixture series of live-shaped snapshots only; no live fetcher, network, or external API is implemented.
- Paper orders, duplicate blocking, portfolio risk limits, carry-forward positions, settlements, exposure, and PnL are deterministic local calculations only.
- No runtime integration, prompt automation, credentials, wallet access, real orders, or live trading is included.

- offline_only=true; paper_only=true; live_fetcher_implemented=false; execution_allowed=false; trading_allowed=false; real_order_created=false; wallet_used=false; api_used=false; network_used=false
