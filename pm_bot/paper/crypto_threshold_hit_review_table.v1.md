# Crypto Threshold-Hit Review Table

- Source: embedded_crypto_threshold_hit_review_fixture
- Source shape: polymarket_gamma_markets_response
- As of date: 2026-04-27
- Markets seen: 3
- Threshold-hit candidates: 3
- Reference context used: false
- Assets with reference price: []
- No action: 1
- Watchlist: 2
- Paper candidates: 0
- Missing assumption reason counts: {"before_event_requires_event_model": 1, "missing_reference_price": 3}
- Paper orders created: 0

## Review Rows

| market_id | question | asset | target | type | deadline | event | yes | implied_probability | liquidity | reference | reference_captured_at | reference_source | distance_pct | target_multiple | days | assumption_status | decision | reason_codes | note |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| fixture_bitcoin_hit_1m_before_event | Will Bitcoin hit $1m before GTA VI? | BTC | $1m | threshold_hit_before_event |  | GTA VI | 0.49 | 0.49 | 23456.0 |  |  |  |  |  |  | before_event_requires_event_model | no_action | ["missing_reference_price", "before_event_requires_event_model"] | No action: before-event threshold market needs an explicit offline event model fixture before scoring. |
| fixture_btc_hit_150k_by_date | Will BTC hit $150k by June 30, 2026? | BTC | $150k | threshold_hit_by_date | 2026-06-30 |  | 0.21 | 0.21 | 12345.0 |  |  |  |  |  | 64 | missing_reference_price | watchlist | ["missing_reference_price"] | Watchlist only: supply an offline reference price fixture before reviewing distance to target. |
| fixture_eth_reach_5000_by_date | Will ETH reach $5,000 by December 31, 2026? | ETH | $5,000 | threshold_hit_by_date | 2026-12-31 |  | 0.33 | 0.33 | 34567.0 |  |  |  |  |  | 248 | missing_reference_price | watchlist | ["missing_reference_price"] | Watchlist only: supply an offline reference price fixture before reviewing distance to target. |

## Safety Flags

- offline_only=true; paper_only=true; live_fetcher_implemented=false; api_used=false; network_used=false; wallet_used=false; real_order_created=false; trading_allowed=false; runtime_wiring_changed=false; dispatcher_touched=false; prompt_automation_added=false

## Limitations

- Reads a local saved JSON file only; no live fetcher, network, external API, credentials, wallet access, orders, or trading are included.
- Threshold-hit review rows are not merged into the existing above/below crypto numeric scorer.
- No paper orders, runtime wiring, dispatcher changes, prompt automation, or workspace state writes are included.
- Default review uses no live reference price and no before-event timing model; missing assumptions prevent paper_candidate decisions.
- Reference context, when supplied, is read from a local fixture file only and does not enable paper candidates.
