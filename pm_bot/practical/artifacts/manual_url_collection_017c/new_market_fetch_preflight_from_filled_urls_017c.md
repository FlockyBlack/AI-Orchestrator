# PMBOT Enriched Manifest Execution Preflight

- Ready to execute public read-only fetch: `false`
- Would be ready after operator approval: `true`
- Executable requests: 3
- Request count within limit: `true`
- Missing URL count: 0
- Blocked request count: 0
- Approval required: `true`
- Approval granted: `false`
- Live fetch performed: `false`

## Blockers

- operator approval has not been granted

## Warnings

- none

## URL Safety

- `manual_url_fetch_request_017c_01_573656_coingecko_bitcoin_btc_usd_public_price_chart` allowed: `true`
  Market: `573656`
  URL: `https://www.coingecko.com/en/coins/bitcoin`
  Blockers: none
- `manual_url_fetch_request_017c_02_573656_coinmarketcap_bitcoin_btc_usd_public_price_chart` allowed: `true`
  Market: `573656`
  URL: `https://coinmarketcap.com/currencies/bitcoin/`
  Blockers: none
- `manual_url_fetch_request_017c_03_573656_polymarket_public_event_page_for_bitcoin_150k_timing_market` allowed: `true`
  Market: `573656`
  URL: `https://polymarket.com/event/when-will-bitcoin-hit-150k`
  Blockers: none

## Safety Boundary

- This preflight is local-only and performs no network request.
- Pending approval keeps execution blocked until an operator approves the future task.
