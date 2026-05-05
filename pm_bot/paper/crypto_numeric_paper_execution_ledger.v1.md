# PMBOT Crypto Numeric Paper Execution Ledger

Deterministic offline/paper ledger for crypto numeric paper order plans.

## Summary

- Paper orders seen: 1
- Paper orders submitted: 1
- Paper orders filled: 1
- Paper orders not filled: 0
- Paper positions opened: 1
- Paper positions closed or settled: 1
- No-action entries: 3
- Total paper notional: 100.00
- Total max loss: 100.00
- Paper PnL: 72.41

## Events

| event_type | market_id | paper_notional | price | reason |
| --- | --- | --- | --- | --- |
| paper_order_submitted | crypto_numeric_btc_above_90000_2026_05_31 | 100.00 | limit 0.5900 | Paper candidate clears edge, liquidity, spread, and risk limits. |
| paper_order_filled | crypto_numeric_btc_above_90000_2026_05_31 | 100.00 | fill 0.5800 | Fixture observed_yes_price is at or below the paper limit price. |
| no_action_preserved | crypto_numeric_eth_below_3000_2026_05_31 |  |  | decision is watchlist; edge_after_buffer below minimum; risk needs operator review |
| no_action_preserved | crypto_numeric_btc_above_90000_low_liquidity_2026_05_31 |  |  | decision is reject; edge_after_buffer below minimum; low liquidity rejected |
| no_action_preserved | crypto_numeric_eth_below_3000_wide_spread_2026_05_31 |  |  | decision is reject; wide spread rejected; risk fail rejected |

## Paper Positions

| market_id | status | fill_price | shares | paper_notional | max_loss | settlement | paper_pnl |
| --- | --- | --- | --- | --- | --- | --- | --- |
| crypto_numeric_btc_above_90000_2026_05_31 | settled | 0.5800 | 172.4138 | 100.00 | 100.00 | yes | 72.41 |

## No Action

| market_id | reason |
| --- | --- |
| crypto_numeric_eth_below_3000_2026_05_31 | decision is watchlist; edge_after_buffer below minimum; risk needs operator review |
| crypto_numeric_btc_above_90000_low_liquidity_2026_05_31 | decision is reject; edge_after_buffer below minimum; low liquidity rejected |
| crypto_numeric_eth_below_3000_wide_spread_2026_05_31 | decision is reject; wide spread rejected; risk fail rejected |

## Limitations

- Uses fixture paper order plan and fixture execution prices only; no live market data is fetched.
- Paper fills, settlement, and PnL are deterministic local calculations only.
- No real order, wallet, credential, network, runtime integration, or trading path is included.

- offline_only=true; paper_only=true; execution_allowed=false; trading_allowed=false; real_order_created=false; wallet_used=false; api_used=false; network_used=false
