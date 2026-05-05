# PMBOT Live-Shaped Snapshot Paper Lifecycle

Deterministic offline/paper lifecycle: live-shaped fixture -> adapter -> intake -> scorer -> review -> paper plan -> execution ledger -> portfolio exposure.

## Summary

- Snapshot markets: 10
- Adapted raw markets: 3
- Adapter rejections: 7
- Normalized supported: 3
- Intake rejections: 0
- Markets scored: 3
- Paper candidates: 1
- Watchlist: 1
- Rejected after scoring: 1
- Paper orders submitted: 1
- Paper orders filled: 1
- Open positions: 0
- Settled positions: 1
- Total paper notional: 100.00
- Total max loss: 100.00
- Paper PnL: 72.41
- No-action entries: 2

## Adapter Rejections

| market_id | reason_code | reason |
| --- | --- | --- |
| live_missing_question | missing_question | Snapshot does not include a question or title. |
| unknown | missing_market_id | Snapshot does not include a condition_id or market_id. |
| live_missing_price | missing_price | Snapshot does not include a Yes outcome price. |
| live_missing_liquidity | missing_liquidity | Snapshot does not include liquidity. |
| live_missing_expiry | missing_expiry | Snapshot does not include an expiry date. |
| live_unsupported_asset | unsupported_asset | Question does not identify supported BTC or ETH asset. |
| live_ambiguous_side | ambiguous_side | Question does not specify exactly one above/below side. |

## Intake Rejections

| market_id | reason_code | reason |
| --- | --- | --- |

## Scoring Rejections

| market_id | asset | side | edge_after_buffer | reason |
| --- | --- | --- | --- | --- |
| live_eth_above_4500_2026_06_30 | ETH | above | -0.2040 | buffered edge is not positive; risk needs review |

## Paper Positions

| market_id | status | fill_price | shares | notional | max_loss | paper_pnl |
| --- | --- | --- | --- | --- | --- | --- |
| live_btc_above_90000_2026_05_31 | settled | 0.5800 | 172.4138 | 100.00 | 100.00 | 72.41 |

## Ledger Events

| event_type | market_id | reason |
| --- | --- | --- |
| paper_order_submitted | live_btc_above_90000_2026_05_31 | Paper candidate clears edge, liquidity, spread, and risk limits. |
| paper_order_filled | live_btc_above_90000_2026_05_31 | Fixture observed_yes_price is at or below the paper limit price. |
| no_action_preserved | live_eth_below_3000_2026_05_31 | decision is watchlist; edge_after_buffer below minimum; risk needs operator review |
| no_action_preserved | live_eth_above_4500_2026_06_30 | decision is reject; edge_after_buffer below minimum; risk needs operator review |

## Limitations

- Uses fixture live-shaped snapshots only; no live fetcher, network, or external API is implemented.
- Adapter output is passed through the existing offline intake, scorer, review, paper plan, and paper ledger modules.
- Execution fixture prices are aligned deterministically to live-shaped adapted market IDs for this lifecycle command.
- Paper fills, settlement, exposure, and PnL are offline review calculations only.
- No runtime integration, prompt automation, credentials, wallet access, real orders, or live trading is included.

- offline_only=true; paper_only=true; live_fetcher_implemented=false; network_used=false; api_used=false; credentials_used=false; wallet_used=false; real_order_created=false; trading_allowed=false
