# PMBOT Crypto Numeric Paper Replay

Deterministic offline/paper replay for crypto numeric scoring and paper-plan decisions.

## Summary

- Replay cases: 5
- Paper orders: 1
- Wins: 1
- Losses: 0
- No action: 4
- Total paper PnL: 69.49
- Bad entries: 0
- Rejected bad cases: 2

## Replay Rows

| market_id | asset | side | decision | action | result | paper_pnl | max_loss | reason |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| replay_btc_above_90000_win | BTC | above | paper_candidate | paper_limit_order | win | 69.49 | 100.00 | Paper candidate clears edge, liquidity, spread, and risk limits. |
| replay_eth_below_3000_watchlist_win | ETH | below | watchlist | no_action | no_fill_or_no_action | 0.00 | 0.00 | decision is watchlist; edge_after_buffer below minimum; risk needs operator review |
| replay_btc_above_90000_low_liquidity_loss | BTC | above | reject | no_action | no_fill_or_no_action | 0.00 | 0.00 | decision is reject; edge_after_buffer below minimum; low liquidity rejected |
| replay_eth_below_3000_wide_spread_loss | ETH | below | reject | no_action | no_fill_or_no_action | 0.00 | 0.00 | decision is reject; wide spread rejected; risk fail rejected |
| replay_btc_above_100000_false_positive_loss | BTC | above | watchlist | no_action | no_fill_or_no_action | 0.00 | 0.00 | decision is watchlist |

## Limitations

- Uses fixture replay cases only; no live markets, prices, or APIs are fetched.
- Paper PnL is simulated from fixture resolution prices and paper plan entries only.
- No runtime integration, prompt automation, credentials, or wallet access is included.

- offline_only=true; paper_only=true; execution_allowed=false; trading_allowed=false
