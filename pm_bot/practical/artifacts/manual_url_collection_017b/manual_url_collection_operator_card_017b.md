# Manual URL Collection Operator Card 017B

- Market: `573656` Will Bitcoin hit $150k by December 31, 2026?
- File to fill: `pm_bot/practical/artifacts/manual_url_collection_017b/manual_public_url_collection_packet_573656.json`
- Next task after fill: `ORCH-PMBOT-PRACTICAL-017C-FILL-NEW-MARKET-PUBLIC-URL-PACKET-MANUALLY`

## Why Fetch Is Blocked

- PRACTICAL-017 found zero executable request intents for the new market.
- The capped manifest has three missing concrete public URLs.
- Operator approval alone is not enough until the URL packet is filled and validated.

## The 3 Missing URLs

- `new_market_fetch_request_017_01_573656_public_market_metadata_page_reference`
  Source: `public_market_metadata_endpoint_placeholder` public market metadata page/reference
  Evidence type: public market metadata, rules, status, and linked reference snapshot
- `new_market_fetch_request_017_02_573656_public_bitcoin_price_reference_category`
  Source: `public_static_web_page_placeholder` public Bitcoin price reference category
  Evidence type: public Bitcoin price threshold reference snapshot
- `new_market_fetch_request_017_03_573656_public_resolution_source_reference_category`
  Source: `public_resolution_source_page_placeholder` public resolution source reference category
  Evidence type: public resolution rules or resolution-source reference snapshot

## Acceptable URLs

- Public HTTP(S) page.
- No login, API key, cookie, private dashboard, localhost, internal host, wallet, order, or trading endpoint.
- Clear match to the expected evidence type.
- Stable enough for later replay and evidence capture.

## Prohibited URLs

- localhost, loopback, private IP, or internal hostname: not public evidence
- URL username or password: credential-bearing URL
- token, key, secret, signature, session, auth, or cookie query keys: credential-like query
- login, auth, session, kyc, admin, private, or oauth path hints: authentication or private view
- wallet, sign, order, trade, trading, clob, or withdraw path hints: execution-adjacent endpoint

## Safety Boundary

- Manual URL collection only.
- No live fetch, OpenRouter call, Polymarket API call, auth, cookies, wallet, orders, trading, scheduler, or background worker.
- No outcome is resolved and no market instruction is generated.
