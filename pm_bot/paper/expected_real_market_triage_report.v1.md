# Real Market Triage Report

- Source: pm_bot\paper\manual_snapshot_import_source\008_polymarket_markets_active_minimized.fixture.json
- Source shape: polymarket_gamma_markets_response
- Top-level shape: top_level_list
- Gamma market list detected: true
- Total markets seen: 5
- Active counts: {"false": 0, "true": 5, "unknown": 0}
- Closed counts: {"false": 5, "true": 0, "unknown": 0}
- Real Gamma crypto numeric adapted: 2
- Crypto numeric actionable after adapter update: 2
- Adapter rejection reason counts: {"ambiguous_side": 1, "missing_target": 1, "unsupported_asset": 1}
- Numeric target detected: 4
- Above/below phrase detected: 5
- Up/down phrase detected: 0

## Asset Keyword Counts

- BTC: 1
- ETH: 1
- SOL: 0
- XRP: 0
- crypto: 0
- bitcoin: 1
- ethereum: 1

## Outcome Shape Counts

- yes_no: 5
- up_down: 0
- multi_outcome: 0
- unknown: 0

## Category Counts

- None

## Tag Counts

- None

## Supported Candidates

| market_id | question | asset | shape_or_side | target | support_type | reason |
| --- | --- | --- | --- | --- | --- | --- |
| gamma_btc_above_90000 | Will Bitcoin be above $90,000 on June 30, 2026? | BTC | above | 90000 | crypto_numeric_above_below | actionable: real Gamma crypto numeric adapter accepted |
| gamma_eth_below_3000 | Will Ethereum be below $3,000 on June 30, 2026? | ETH | below | 3000 | crypto_numeric_above_below | actionable: real Gamma crypto numeric adapter accepted |

## Still Rejected Candidates

| market_id | question | asset | shape_or_side | target | support_type | reason |
| --- | --- | --- | --- | --- | --- | --- |
| gamma_eth_ambiguous_side | Will ETH be above or below $3,000 on June 30, 2026? | ETH | yes_no | 3000 | crypto_numeric_above_below | rejected: ambiguous_side - Question does not specify exactly one above/below side. |
| gamma_btc_missing_target | Will BTC be above its current price on June 30, 2026? | BTC | above |  | unsupported | rejected: missing_target - Question does not include a numeric target price. |
| gamma_non_crypto_numeric | Will Harvey Weinstein be sentenced to less than 5 years in prison? |  | below | 5 | non_crypto_binary | rejected: unsupported_asset - Question does not identify supported BTC or ETH asset. |

## Limitations

- Reads a local saved JSON file only; no live fetcher, network, external API, credentials, wallet access, orders, or trading are included.
- Adapter support is limited to unambiguous Yes/No BTC, Bitcoin, ETH, or Ethereum numeric above/below markets.
- Suggested support types are deterministic triage labels for product readiness only, not runtime wiring.

- offline_only=true; paper_only=true; live_fetcher_implemented=false; api_used=false; network_used=false; wallet_used=false; real_order_created=false; trading_allowed=false; runtime_wiring_changed=false; dispatcher_touched=false; prompt_automation_added=false
