# Manual Public URL Collection Packet 573656

- Packet: `manual-public-url-collection-017b-573656`
- Market: `573656` Will Bitcoin hit $150k by December 31, 2026?
- Operator fill required: `true`
- Filled URLs: 0
- Missing URLs: 3
- Blocked URLs: 0
- Live fetch performed: `false`

## Candidate URL Rows

- `new_market_fetch_request_017_01_573656_public_market_metadata_page_reference`
  Source: `public_market_metadata_endpoint_placeholder` public market metadata page/reference
  Evidence type: public market metadata, rules, status, and linked reference snapshot
  operator_supplied_url: `None`
  url_status: `missing`
- `new_market_fetch_request_017_02_573656_public_bitcoin_price_reference_category`
  Source: `public_static_web_page_placeholder` public Bitcoin price reference category
  Evidence type: public Bitcoin price threshold reference snapshot
  operator_supplied_url: `None`
  url_status: `missing`
- `new_market_fetch_request_017_03_573656_public_resolution_source_reference_category`
  Source: `public_resolution_source_page_placeholder` public resolution source reference category
  Evidence type: public resolution rules or resolution-source reference snapshot
  operator_supplied_url: `None`
  url_status: `missing`

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

- Fill `manual_public_url_collection_packet_573656.json`, then run `ORCH-PMBOT-PRACTICAL-017C-FILL-NEW-MARKET-PUBLIC-URL-PACKET-MANUALLY`.
