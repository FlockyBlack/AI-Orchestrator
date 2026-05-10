# PMBOT Public Read-Only Fetch Plan

- Contract: `pmbot_public_read_only_fetch_plan.v1`
- Fetch plan ID: `public-read-only-fetch-prep-005-5-markets`
- Created at: `2026-05-10T00:00:00Z`
- Markets: 5
- Planned request count: 10
- Max request count: 10
- Operator approval required: `true`
- Operator approval granted: `false`
- Live fetch performed: `false`
- Validation valid: `true`

## Requested Sources

- `fetch-prep-005:563650:market_metadata` `public_market_metadata_endpoint_placeholder`
  Market: `563650` SCOTUS accepts sports event contract case by July 31, 2026?
  Evidence: public market metadata snapshot
  Role: future metadata check for market title, rules, status, and linked references
  Approval required: `true`
- `fetch-prep-005:563650:domain_public_evidence` `public_court_government_page_placeholder`
  Market: `563650` SCOTUS accepts sports event contract case by July 31, 2026?
  Evidence: official docket or resolution page snapshot
  Role: future official-source evidence for outcome and rules review
  Approval required: `true`
- `fetch-prep-005:597964:market_metadata` `public_market_metadata_endpoint_placeholder`
  Market: `597964` Macron out by June 30, 2026?
  Evidence: public market metadata snapshot
  Role: future metadata check for market title, rules, status, and linked references
  Approval required: `true`
- `fetch-prep-005:597964:domain_public_evidence` `public_resolution_source_page_placeholder`
  Market: `597964` Macron out by June 30, 2026?
  Evidence: public official status or resolution page snapshot
  Role: future public evidence for outcome review
  Approval required: `true`
- `fetch-prep-005:598936:market_metadata` `public_market_metadata_endpoint_placeholder`
  Market: `598936` Will the next UK election be called by June 30, 2026?
  Evidence: public market metadata snapshot
  Role: future metadata check for market title, rules, status, and linked references
  Approval required: `true`
- `fetch-prep-005:598936:domain_public_evidence` `public_court_government_page_placeholder`
  Market: `598936` Will the next UK election be called by June 30, 2026?
  Evidence: public election or parliament page snapshot
  Role: future official-source evidence for outcome review
  Approval required: `true`
- `fetch-prep-005:691547:market_metadata` `public_market_metadata_endpoint_placeholder`
  Market: `691547` Kraken IPO by December 31, 2026?
  Evidence: public market metadata snapshot
  Role: future metadata check for market title, rules, status, and linked references
  Approval required: `true`
- `fetch-prep-005:691547:domain_public_evidence` `public_exchange_company_announcement_page_placeholder`
  Market: `691547` Kraken IPO by December 31, 2026?
  Evidence: public listing or company announcement snapshot
  Role: future public evidence for IPO status review
  Approval required: `true`
- `fetch-prep-005:692258:market_metadata` `public_market_metadata_endpoint_placeholder`
  Market: `692258` MicroStrategy sells any Bitcoin by June 30, 2026?
  Evidence: public market metadata snapshot
  Role: future metadata check for market title, rules, status, and linked references
  Approval required: `true`
- `fetch-prep-005:692258:domain_public_evidence` `public_issuer_company_news_page_placeholder`
  Market: `692258` MicroStrategy sells any Bitcoin by June 30, 2026?
  Evidence: public issuer news or filing summary snapshot
  Role: future public evidence for company action review
  Approval required: `true`

## Allowed Categories

- `low_quality_forum_or_rumor_labeled_source`
- `public_court_government_page_placeholder`
- `public_exchange_company_announcement_page_placeholder`
- `public_issuer_company_news_page_placeholder`
- `public_market_metadata_endpoint_placeholder`
- `public_resolution_source_page_placeholder`
- `public_static_web_page_placeholder`

## Blocked Categories

- `authenticated_endpoint`
- `browser_session_cookie_based_source`
- `forum_rumor_only_unlabeled_source`
- `order_endpoint`
- `private_api_key_endpoint`
- `source_requiring_bypass_or_automation`
- `source_requiring_kyc_or_login`
- `trading_endpoint`
- `wallet_signing_endpoint`

## Safety Notes

- Operator-approved explicit command is required before any future public read-only request.
- This plan lists future requests only and performs no network access.
- Evidence saving is required before replay.
- Saved evidence replay is required before any analysis update.
- Authenticated, wallet, order, trading, scheduler, polling, and autonomous paths remain blocked.

## Validation

- none
