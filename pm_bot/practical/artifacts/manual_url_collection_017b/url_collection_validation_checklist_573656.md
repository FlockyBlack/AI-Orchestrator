# Manual URL Collection Validation Checklist 573656

- Market: `573656` Will Bitcoin hit $150k by December 31, 2026?
- Fill target: `manual_public_url_collection_packet_573656.json`
- Live fetch performed: `false`

## Required URL Checks

- `public_http_url` must be public HTTP(S) (required)
  Operator check: Use a normal http or https page that can be opened without credentials.
- `no_login` must not require login (required)
  Operator check: Do not use pages behind accounts, KYC, paywalls, or identity gates.
- `no_api_key` must not require API key (required)
  Operator check: Do not use URLs that depend on tokens, API keys, signatures, or private headers.
- `no_cookies` must not require cookies (required)
  Operator check: Do not use browser-session URLs or profile-specific links.
- `no_wallet_or_execution_endpoint` must not be wallet, order, or trading endpoint (required)
  Operator check: Use read-only public reference pages only.
- `no_private_dashboard` must not be a private dashboard (required)
  Operator check: Avoid private dashboards, admin pages, local tools, and account-specific views.
- `no_local_or_internal_host` must not be localhost or internal IP (required)
  Operator check: Do not use localhost, private IP ranges, internal hostnames, or intranet links.
- `official_or_high_quality` should be official or high-quality public reference (preferred)
  Operator check: Prefer official market, resolution, benchmark, or durable public reference pages.
- `maps_to_expected_evidence` should map clearly to expected evidence type (preferred)
  Operator check: The URL should visibly support the evidence type named in the packet row.
- `stable_for_replay` should be stable enough for future replay (preferred)
  Operator check: Prefer durable pages over ephemeral search results, interactive state, or personalized views.

## Missing Source Rows

- `public_market_metadata_endpoint_placeholder` public market metadata page/reference
  Evidence type: public market metadata, rules, status, and linked reference snapshot
- `public_static_web_page_placeholder` public Bitcoin price reference category
  Evidence type: public Bitcoin price threshold reference snapshot
- `public_resolution_source_page_placeholder` public resolution source reference category
  Evidence type: public resolution rules or resolution-source reference snapshot

## Safety Boundary

- This checklist is local guidance only.
- No URL is fetched, approved, or treated as evidence by this artifact.
