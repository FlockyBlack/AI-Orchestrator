# PMBOT Crypto Numeric Lifecycle Replay

Deterministic offline/paper replay across lifecycle outcomes.

## Summary

- Scenarios: 7
- Filled orders: 3
- Not-filled orders: 2
- Open positions: 1
- Settled positions: 2
- Wins: 2
- Losses: 0
- Total paper PnL: 179.31
- Bad entries: 0
- Rejected bad cases: 1

## Scenarios

| scenario_id | status | submitted | filled | not_filled | open | settled | pnl | no_action | raw_rejects |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| filled_win | filled_win | 1 | 1 | 0 | 0 | 1 | 72.41 | 0 | 0 |
| filled_loss | not_filled | 1 | 0 | 1 | 0 | 0 | 0.00 | 0 | 0 |
| not_filled | not_filled | 1 | 0 | 1 | 0 | 0 | 0.00 | 0 | 0 |
| open_position | open_position | 1 | 1 | 0 | 1 | 0 | 6.90 | 0 | 0 |
| settled_position | settled_position | 1 | 1 | 0 | 0 | 1 | 100.00 | 0 | 0 |
| rejected_raw_market | rejected_raw_market | 0 | 0 | 0 | 0 | 0 | 0.00 | 0 | 1 |
| no_action_watchlist_or_reject | no_action_watchlist_or_reject | 0 | 0 | 0 | 0 | 0 | 0.00 | 1 | 0 |

## Limitations

- Uses fixture replay scenarios only; no live markets, prices, or APIs are fetched.
- Each scenario composes the offline intake, scoring, review, paper plan, and paper execution ledger components.
- Paper fills, no-fills, open status, settlement, and PnL are deterministic local calculations only.
- No runtime integration, prompt automation, credentials, wallet access, real orders, or live trading is included.

- offline_only=true; paper_only=true; execution_allowed=false; trading_allowed=false; real_order_created=false; wallet_used=false; api_used=false; network_used=false
