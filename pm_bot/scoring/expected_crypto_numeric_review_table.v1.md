# PMBOT Crypto Numeric Review Table

Paper-only operator review table for deterministic crypto numeric scorer output.

- Paper candidates: 1
- Watchlist: 1
- Rejected: 2

| market_id | asset | side | market_probability | model_probability | edge_after_buffer | liquidity | spread | risk | decision | short_reason |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| crypto_numeric_btc_above_90000_2026_05_31 | BTC | above | 0.5900 | 0.6797 | 0.0647 | pass | pass | pass | paper_candidate | positive buffered edge clears review gates |
| crypto_numeric_eth_below_3000_2026_05_31 | ETH | below | 0.3600 | 0.3895 | 0.0045 | pass | pass | watch | watchlist | positive buffered edge needs operator review; risk needs review |
| crypto_numeric_btc_above_90000_low_liquidity_2026_05_31 | BTC | above | 0.4200 | 0.3457 | -0.0993 | fail | watch | pass | reject | buffered edge is not positive; liquidity gate failed; spread needs review |
| crypto_numeric_eth_below_3000_wide_spread_2026_05_31 | ETH | below | 0.6000 | 0.7425 | 0.1175 | pass | fail | fail | reject | spread gate failed; risk gate failed |

- Output is for paper-only operator review. No execution, trading, order placement, or runtime action is allowed.
