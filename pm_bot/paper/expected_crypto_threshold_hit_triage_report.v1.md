# Crypto Threshold-Hit Triage Report

- Source: embedded_crypto_threshold_hit_fixture
- Source shape: polymarket_gamma_markets_response
- Top-level shape: top_level_list
- Gamma market list detected: true
- Total markets seen: 6
- Threshold-hit-like markets found: 6
- Threshold-hit crypto candidates found: 5
- Supported triage candidates: 3
- Rejected/ambiguous candidates: 3
- Market type counts: {"ambiguous_threshold_hit": 1, "threshold_hit_before_event": 1, "threshold_hit_by_date": 4}
- Supported market type counts: {"ambiguous_threshold_hit": 0, "threshold_hit_before_event": 1, "threshold_hit_by_date": 2}
- Reason counts: {"ambiguous_asset": 1, "missing_target": 1, "unsupported_asset": 1}

## Candidate Table

| market_id | question | status | asset | target | type | deadline | event | yes | no | liquidity | reason |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| fixture_btc_hit_150k_by_date | Will BTC hit $150k by June 30, 2026? | supported | BTC | $150k | threshold_hit_by_date | 2026-06-30 |  | 0.21 | 0.79 | 12345.0 |  |
| fixture_bitcoin_hit_1m_before_event | Will Bitcoin hit $1m before GTA VI? | supported | BTC | $1m | threshold_hit_before_event |  | GTA VI | 0.49 | 0.51 | 23456.0 |  |
| fixture_eth_reach_5000_by_date | Will ETH reach $5,000 by December 31, 2026? | supported | ETH | $5,000 | threshold_hit_by_date | 2026-12-31 |  | 0.33 | 0.67 | 34567.0 |  |
| fixture_gold_hit_5000_by_date | Will gold hit $5,000 by December 31, 2026? | rejected |  | $5,000 | threshold_hit_by_date | 2026-12-31 |  | 0.25 | 0.75 | 45678.0 | unsupported_asset |
| fixture_bitcoin_missing_target | Will Bitcoin hit a new all time high by December 31, 2026? | rejected | BTC |  | ambiguous_threshold_hit |  |  | 0.5 | 0.5 | 56789.0 | missing_target |
| fixture_ambiguous_asset_hit_100000 | Will Bitcoin or Ethereum hit $100,000 by December 31, 2026? | rejected | BTC,ETH | $100,000 | threshold_hit_by_date | 2026-12-31 |  | 0.12 | 0.88 | 67890.0 | ambiguous_asset |

## Safety Flags

- offline_only=true; paper_only=true; live_fetcher_implemented=false; api_used=false; network_used=false; wallet_used=false; real_order_created=false; trading_allowed=false; runtime_wiring_changed=false; dispatcher_touched=false; prompt_automation_added=false

## Limitations

- Reads a local saved JSON file only; no live fetcher, network, external API, credentials, wallet access, orders, or trading are included.
- Threshold-hit candidates are triaged only and are not converted into the existing crypto numeric above/below scorer input.
- No paper orders, runtime wiring, dispatcher changes, or prompt automation are included.
