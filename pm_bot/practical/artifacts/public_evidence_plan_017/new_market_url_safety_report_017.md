# New Market URL Safety Report 017

- Checked request count: 3
- Allowed count: 0
- Blocked count: 0
- Missing URL count: 3
- Live fetch performed: `false`

## Per Request Safety

- `new_market_fetch_request_017_01_573656_public_market_metadata_page_reference` allowed: `false`
  URL status: `missing`
  URL reference: `public_source_placeholder:public_market_metadata_endpoint_placeholder:573656:public_market_metadata_page_reference`
  Blockers: source reference is a placeholder, not an explicit URL, URL scheme must be http or https
- `new_market_fetch_request_017_02_573656_public_bitcoin_price_reference_category` allowed: `false`
  URL status: `missing`
  URL reference: `public_source_placeholder:public_static_web_page_placeholder:573656:public_bitcoin_price_reference_category`
  Blockers: source reference is a placeholder, not an explicit URL, URL scheme must be http or https
- `new_market_fetch_request_017_03_573656_public_resolution_source_reference_category` allowed: `false`
  URL status: `missing`
  URL reference: `public_source_placeholder:public_resolution_source_page_placeholder:573656:public_resolution_source_reference_category`
  Blockers: source reference is a placeholder, not an explicit URL, URL scheme must be http or https

## Global Warnings

- 3 request intents are missing concrete URLs.

## Safety Boundary

- URL safety validation is local and happens before any request.
- This report did not fetch a URL.
