# PMBOT Crypto Numeric Paper Chain

Deterministic offline/paper chain: scorer -> review table -> paper order plan.

## Summary

- Markets scored: 4
- Paper candidates: 1
- Watchlist: 1
- Rejected: 2
- Paper limit orders: 1
- Total planned paper notional: 100.00
- Max loss: 100.00

## Paper Candidates

| market_id | asset | side | edge_after_buffer | decision | reason |
| --- | --- | --- | --- | --- | --- |
| crypto_numeric_btc_above_90000_2026_05_31 | BTC | above | 0.0647 | paper_candidate | positive buffered edge clears review gates |

## Watchlist

| market_id | asset | side | edge_after_buffer | decision | reason |
| --- | --- | --- | --- | --- | --- |
| crypto_numeric_eth_below_3000_2026_05_31 | ETH | below | 0.0045 | watchlist | positive buffered edge needs operator review; risk needs review |

## Rejected

| market_id | asset | side | edge_after_buffer | decision | reason |
| --- | --- | --- | --- | --- | --- |
| crypto_numeric_btc_above_90000_low_liquidity_2026_05_31 | BTC | above | -0.0993 | reject | buffered edge is not positive; liquidity gate failed; spread needs review |
| crypto_numeric_eth_below_3000_wide_spread_2026_05_31 | ETH | below | 0.1175 | reject | spread gate failed; risk gate failed |

## Generated Paper Order Plan

| market_id | action | limit_price | paper_notional | max_loss | reason |
| --- | --- | --- | --- | --- | --- |
| crypto_numeric_btc_above_90000_2026_05_31 | paper_limit_order | 0.5900 | 100.00 | 100.00 | Paper candidate clears edge, liquidity, spread, and risk limits. |
| crypto_numeric_eth_below_3000_2026_05_31 | no_action |  |  |  | decision is watchlist; edge_after_buffer below minimum; risk needs operator review |
| crypto_numeric_btc_above_90000_low_liquidity_2026_05_31 | no_action |  |  |  | decision is reject; edge_after_buffer below minimum; low liquidity rejected |
| crypto_numeric_eth_below_3000_wide_spread_2026_05_31 | no_action |  |  |  | decision is reject; wide spread rejected; risk fail rejected |

## Limitations

- Uses fixture input only; no live markets, prices, or APIs are fetched.
- Generated paper order plan is an offline review artifact only; no real order is created.
- No runtime integration, prompt automation, credentials, or wallet access is included.

- offline_only=true; paper_only=true; execution_allowed=false; trading_allowed=false
