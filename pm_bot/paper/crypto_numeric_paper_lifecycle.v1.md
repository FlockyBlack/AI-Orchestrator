# PMBOT Crypto Numeric Paper Lifecycle

Deterministic offline/paper lifecycle: raw intake -> scorer -> review -> paper plan -> execution ledger -> portfolio exposure.

## Summary

- Raw markets: 11
- Normalized supported: 4
- Rejected raw markets: 7
- Markets scored: 4
- Paper candidates: 1
- Watchlist: 1
- Rejected after scoring: 2
- Paper orders submitted: 1
- Paper orders filled: 1
- Open positions: 0
- Settled positions: 1
- Total paper notional: 100.00
- Total max loss: 100.00
- Paper PnL: 72.41
- No-action entries: 3

## Rejected Raw Markets

| market_id | reason_code | reason |
| --- | --- | --- |
| raw_election_non_crypto | non_crypto_market | Record category is not crypto. |
| raw_weather_non_crypto | non_crypto_market | Record category is not crypto. |
| raw_btc_missing_target | missing_target | Question does not include a numeric target price. |
| raw_eth_missing_expiry | missing_expiry | Record does not include an expiry date. |
| raw_btc_unclear_side | unclear_side | Question does not clearly specify above or below. |
| raw_eth_ambiguous_intraday | ambiguous_settlement | Question uses ambiguous settlement wording. |
| raw_btc_missing_data | missing_market_data | Record is missing market data: spread. |

## Scoring Rejections

| market_id | asset | side | edge_after_buffer | reason |
| --- | --- | --- | --- | --- |
| raw_eth_above_4500_2026_06_30 | ETH | above | -0.2040 | buffered edge is not positive; risk needs review |
| raw_btc_below_80000_2026_06_30 | BTC | below | -0.1950 | buffered edge is not positive; risk needs review |

## Paper Positions

| market_id | status | fill_price | shares | notional | max_loss | paper_pnl |
| --- | --- | --- | --- | --- | --- | --- |
| raw_btc_above_90000_2026_05_31 | settled | 0.5800 | 172.4138 | 100.00 | 100.00 | 72.41 |

## Ledger Events

| event_type | market_id | reason |
| --- | --- | --- |
| paper_order_submitted | raw_btc_above_90000_2026_05_31 | Paper candidate clears edge, liquidity, spread, and risk limits. |
| paper_order_filled | raw_btc_above_90000_2026_05_31 | Fixture observed_yes_price is at or below the paper limit price. |
| no_action_preserved | raw_eth_below_3000_2026_05_31 | decision is watchlist; edge_after_buffer below minimum; risk needs operator review |
| no_action_preserved | raw_eth_above_4500_2026_06_30 | decision is reject; edge_after_buffer below minimum; risk needs operator review |
| no_action_preserved | raw_btc_below_80000_2026_06_30 | decision is reject; edge_after_buffer below minimum; risk needs operator review |

## Limitations

- Uses raw market, scoring, and execution fixtures only; no live markets, prices, or APIs are fetched.
- Execution fixture prices are aligned deterministically to raw-intake market IDs for this lifecycle command.
- Paper fills, settlement, exposure, and PnL are offline review calculations only.
- No runtime integration, prompt automation, credentials, wallet access, real orders, or live trading is included.

- offline_only=true; paper_only=true; execution_allowed=false; trading_allowed=false; real_order_created=false; wallet_used=false; api_used=false; network_used=false
