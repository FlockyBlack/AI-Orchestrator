# PMBOT Crypto Numeric Intake To Chain

Deterministic offline/paper chain: raw fixture intake -> scorer -> review table -> paper order plan.

## Summary

- Raw markets: 11
- Normalized supported: 4
- Rejected raw markets: 7
- Markets scored: 4
- Paper candidates: 1
- Watchlist: 1
- Rejected after scoring: 2
- Paper limit orders: 1
- Total planned paper notional: 100.00
- Max loss: 100.00

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

## Paper Candidates

| market_id | asset | side | edge_after_buffer | decision | reason |
| --- | --- | --- | --- | --- | --- |
| raw_btc_above_90000_2026_05_31 | BTC | above | 0.0647 | paper_candidate | positive buffered edge clears review gates |

## Watchlist

| market_id | asset | side | edge_after_buffer | decision | reason |
| --- | --- | --- | --- | --- | --- |
| raw_eth_below_3000_2026_05_31 | ETH | below | 0.0045 | watchlist | positive buffered edge needs operator review; risk needs review |

## Rejected After Scoring

| market_id | asset | side | edge_after_buffer | decision | reason |
| --- | --- | --- | --- | --- | --- |
| raw_eth_above_4500_2026_06_30 | ETH | above | -0.2040 | reject | buffered edge is not positive; risk needs review |
| raw_btc_below_80000_2026_06_30 | BTC | below | -0.1950 | reject | buffered edge is not positive; risk needs review |

## Generated Paper Order Plan

| market_id | action | limit_price | paper_notional | max_loss | reason |
| --- | --- | --- | --- | --- | --- |
| raw_btc_above_90000_2026_05_31 | paper_limit_order | 0.5900 | 100.00 | 100.00 | Paper candidate clears edge, liquidity, spread, and risk limits. |
| raw_eth_below_3000_2026_05_31 | no_action |  |  |  | decision is watchlist; edge_after_buffer below minimum; risk needs operator review |
| raw_eth_above_4500_2026_06_30 | no_action |  |  |  | decision is reject; edge_after_buffer below minimum; risk needs operator review |
| raw_btc_below_80000_2026_06_30 | no_action |  |  |  | decision is reject; edge_after_buffer below minimum; risk needs operator review |

## Limitations

- Uses raw fixture input only; no live markets, prices, or APIs are fetched.
- Rejected raw markets are retained with deterministic rejection reason codes.
- Generated paper order plan is an offline review artifact only; no real order is created.
- No runtime integration, prompt automation, credentials, or wallet access is included.

- offline_only=true; paper_only=true; execution_allowed=false; trading_allowed=false
