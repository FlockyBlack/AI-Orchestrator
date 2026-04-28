# PMBOT Crypto Numeric Paper Order Plan

Offline paper-only plan generated from the crypto numeric review table.

- Paper limit orders: 1
- No-action entries: 3
- Total planned paper notional: 100.00

| market_id | asset | side | action | limit_price | paper_notional | max_loss | reason |
| --- | --- | --- | --- | --- | --- | --- | --- |
| crypto_numeric_btc_above_90000_2026_05_31 | BTC | above | paper_limit_order | 0.5900 | 100.00 | 100.00 | Paper candidate clears edge, liquidity, spread, and risk limits. |
| crypto_numeric_eth_below_3000_2026_05_31 | ETH | below | no_action |  |  |  | decision is watchlist; edge_after_buffer below minimum; risk needs operator review |
| crypto_numeric_btc_above_90000_low_liquidity_2026_05_31 | BTC | above | no_action |  |  |  | decision is reject; edge_after_buffer below minimum; low liquidity rejected |
| crypto_numeric_eth_below_3000_wide_spread_2026_05_31 | ETH | below | no_action |  |  |  | decision is reject; wide spread rejected; risk fail rejected |

- Paper order plans are offline review artifacts only. No execution, trading, order placement, or runtime action is allowed.
