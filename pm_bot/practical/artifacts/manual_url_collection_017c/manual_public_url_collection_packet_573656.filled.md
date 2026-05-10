# Manual Public URL Collection Packet 573656

- Packet: `manual-public-url-collection-017c-573656-filled`
- Market: `573656` Will Bitcoin hit $150k by December 31, 2026?
- Operator fill required: `false`
- Filled URLs: 3
- Missing URLs: 0
- Blocked URLs: 0
- Live fetch performed: `false`

## Candidate URL Rows

- `manual_url_017c_01_573656_coingecko_bitcoin_btc_usd_public_price_chart`
  Source: `public_btc_price_reference` CoinGecko Bitcoin BTC/USD public price chart
  Evidence type: BTC/USD public price and chart reference for paper tracking
  operator_supplied_url: `https://www.coingecko.com/en/coins/bitcoin`
  url_status: `supplied_pending_validation`
- `manual_url_017c_02_573656_coinmarketcap_bitcoin_btc_usd_public_price_chart`
  Source: `public_btc_price_reference` CoinMarketCap Bitcoin BTC/USD public price chart
  Evidence type: BTC/USD public price and historical chart reference for paper tracking
  operator_supplied_url: `https://coinmarketcap.com/currencies/bitcoin/`
  url_status: `supplied_pending_validation`
- `manual_url_017c_03_573656_polymarket_public_event_page_for_bitcoin_150k_timing_market`
  Source: `public_resolution_reference` Polymarket public event page for Bitcoin $150k timing market
  Evidence type: public market/resolution context reference for the Bitcoin $150k paper tracking market
  operator_supplied_url: `https://polymarket.com/event/when-will-bitcoin-hit-150k`
  url_status: `supplied_pending_validation`

## Validation Rules

- operator_supplied_url may remain null while the packet is unfilled.
- If operator_supplied_url is present, it is validated locally as a URL string only.
- Only http and https schemes are accepted.
- Credentials in the URL are blocked.
- Credential-like query keys are blocked.
- Localhost, private IPs, internal hostnames, and private dashboard shapes are blocked.
- Wallet, signing, order, and trading endpoint shapes are blocked.
- Validation does not fetch the URL and does not approve a future fetch.

## Prohibited URL Patterns

- localhost, loopback, private IP, or internal hostname: not public evidence
- URL username or password: credential-bearing URL
- token, key, secret, signature, session, auth, or cookie query keys: credential-like query
- login, auth, session, kyc, admin, private, or oauth path hints: authentication or private view
- wallet, sign, order, trade, trading, clob, or withdraw path hints: execution-adjacent endpoint

## Next Action

- Fill `manual_public_url_collection_packet_573656.json`, then run `ORCH-PMBOT-PRACTICAL-018-FIRST-PUBLIC-EVIDENCE-FETCH-FOR-NEW-MARKET`.
