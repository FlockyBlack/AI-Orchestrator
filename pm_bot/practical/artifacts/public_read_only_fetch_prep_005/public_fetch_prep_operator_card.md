# PMBOT Public Fetch Prep Operator Card

- Fetch plan ID: `public-read-only-fetch-prep-005-5-markets`
- Live fetch allowed now: `false`
- Ready for controlled public fetch: `false`

## Ready

- Local source registry is defined.
- Fetch plan contract is valid.
- Dry-run preview is available.
- Saved evidence packet and replay format are available.
- Readiness gate can explain blockers before any future request.

## Blocked

- Operator approval has not been granted.
- Approval record does not enable live fetch after approval.

## Would Be Fetched Later

- `563650` `public_market_metadata_endpoint_placeholder` - public market metadata snapshot
- `563650` `public_court_government_page_placeholder` - official docket or resolution page snapshot
- `597964` `public_market_metadata_endpoint_placeholder` - public market metadata snapshot
- `597964` `public_resolution_source_page_placeholder` - public official status or resolution page snapshot
- `598936` `public_market_metadata_endpoint_placeholder` - public market metadata snapshot
- `598936` `public_court_government_page_placeholder` - public election or parliament page snapshot
- `691547` `public_market_metadata_endpoint_placeholder` - public market metadata snapshot
- `691547` `public_exchange_company_announcement_page_placeholder` - public listing or company announcement snapshot
- `692258` `public_market_metadata_endpoint_placeholder` - public market metadata snapshot
- `692258` `public_issuer_company_news_page_placeholder` - public issuer news or filing summary snapshot

## Will Not Be Fetched

- Authenticated endpoints
- Private API key endpoints
- Browser session or cookie-based sources
- KYC or login-gated sources
- Wallet, signing, custody, order, or trading endpoints
- Scheduler, polling, daemon, watcher, or unattended automation paths

## Why No Live Fetch

This task creates contracts, dry-run surfaces, evidence replay, and approval gates only. Operator approval is pending and live fetch is out of scope.

## Next Safe Action

Review the pending approval packet and readiness blockers before creating a separate first controlled public read-only fetch approval packet.
