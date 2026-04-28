# PMBOT Live-Shaped Crypto Snapshot Adapter

Offline fixture adapter from read-only-market-shaped snapshots to crypto numeric raw market intake records.

## Summary

- Snapshot markets: 10
- Adapted raw markets: 3
- Adapter rejections: 7
- Intake chain check passed: true
- Chain markets scored: 3
- Chain paper candidates: 1
- Chain watchlist: 1
- Chain rejected after scoring: 1

## Rejection Reasons

- ambiguous_side: 1
- missing_expiry: 1
- missing_liquidity: 1
- missing_market_id: 1
- missing_price: 1
- missing_question: 1
- unsupported_asset: 1

## Adapted Raw Markets

| market_id | asset | side | target | expiry | yes_price | liquidity | spread |
| --- | --- | --- | --- | --- | --- | --- | --- |
| live_btc_above_90000_2026_05_31 | BTC | above | 90000.00 | 2026-05-31 | 0.5900 | 180000.00 | 0.0300 |
| live_eth_below_3000_2026_05_31 | ETH | below | 3000.00 | 2026-05-31 | 0.3600 | 125000.00 | 0.0400 |
| live_eth_above_4500_2026_06_30 | ETH | above | 4500.00 | 2026-06-30 | 0.4400 | 90000.00 | 0.0500 |

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

## Limitations

- Uses fixture live-shaped snapshots only; no live fetcher, network, or external API is implemented.
- Adapter output targets the existing crypto numeric raw market intake format and does not replace the intake chain.
- Current price, volatility, and momentum are fixture fields, not live market data.

- offline_only=true; paper_only=true; live_fetcher_implemented=false; network_used=false; api_used=false; credentials_used=false; wallet_used=false; real_order_created=false; trading_allowed=false
