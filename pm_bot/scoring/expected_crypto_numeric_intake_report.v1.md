# PMBOT Crypto Numeric Market Intake

Offline fixture intake for crypto numeric market records.

## Summary

- Raw markets: 11
- Normalized supported: 4
- Rejected: 7

## Rejection Reasons

- ambiguous_settlement: 1
- missing_expiry: 1
- missing_market_data: 1
- missing_target: 1
- non_crypto_market: 2
- unclear_side: 1

## Normalized Markets

| market_id | asset | side | target_price | expiry | yes_price | liquidity | spread |
| --- | --- | --- | --- | --- | --- | --- | --- |
| raw_btc_above_90000_2026_05_31 | BTC | above | 90000.00 | 2026-05-31 | 0.5900 | 180000.00 | 0.0300 |
| raw_eth_below_3000_2026_05_31 | ETH | below | 3000.00 | 2026-05-31 | 0.3600 | 125000.00 | 0.0400 |
| raw_eth_above_4500_2026_06_30 | ETH | above | 4500.00 | 2026-06-30 | 0.4400 | 90000.00 | 0.0500 |
| raw_btc_below_80000_2026_06_30 | BTC | below | 80000.00 | 2026-06-30 | 0.2200 | 110000.00 | 0.0400 |

## Rejections

| market_id | reason_code | reason |
| --- | --- | --- |
| raw_election_non_crypto | non_crypto_market | Record category is not crypto. |
| raw_weather_non_crypto | non_crypto_market | Record category is not crypto. |
| raw_btc_missing_target | missing_target | Question does not include a numeric target price. |
| raw_eth_missing_expiry | missing_expiry | Record does not include an expiry date. |
| raw_btc_unclear_side | unclear_side | Question does not clearly specify above or below. |
| raw_eth_ambiguous_intraday | ambiguous_settlement | Question uses ambiguous settlement wording. |
| raw_btc_missing_data | missing_market_data | Record is missing market data: spread. |

- offline_only=true; paper_only=true; execution_allowed=false; trading_allowed=false
