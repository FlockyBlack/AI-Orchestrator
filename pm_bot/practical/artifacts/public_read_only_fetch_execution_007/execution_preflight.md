# PMBOT Public Fetch Execution Preflight

- Ready to execute public read-only fetch: `false`
- Approved executable requests: 0
- Blocked requests: 10
- Max requests: 5

## Blockers

- request manifest count exceeds scoped approval max request count
- No executable public read-only request intents passed validation.

## Warnings

- none

## Executable Request Intents


## Blocked Request Intents

- `public_fetch_request_intent_006_01_563650_563650_market_metadata`
  Market: `563650`
  Source: `public_source_placeholder:public_market_metadata_endpoint_placeholder:563650`
  Blockers: source reference is a placeholder, not an explicit URL, URL scheme must be http or https
- `public_fetch_request_intent_006_02_563650_563650_domain_public_evidence`
  Market: `563650`
  Source: `public_source_placeholder:public_court_government_page_placeholder:563650`
  Blockers: source reference is a placeholder, not an explicit URL, URL scheme must be http or https
- `public_fetch_request_intent_006_03_597964_597964_market_metadata`
  Market: `597964`
  Source: `public_source_placeholder:public_market_metadata_endpoint_placeholder:597964`
  Blockers: source reference is a placeholder, not an explicit URL, URL scheme must be http or https
- `public_fetch_request_intent_006_04_597964_597964_domain_public_evidence`
  Market: `597964`
  Source: `public_source_placeholder:public_resolution_source_page_placeholder:597964`
  Blockers: source reference is a placeholder, not an explicit URL, URL scheme must be http or https
- `public_fetch_request_intent_006_05_598936_598936_market_metadata`
  Market: `598936`
  Source: `public_source_placeholder:public_market_metadata_endpoint_placeholder:598936`
  Blockers: source reference is a placeholder, not an explicit URL, URL scheme must be http or https
- `public_fetch_request_intent_006_06_598936_598936_domain_public_evidence`
  Market: `598936`
  Source: `public_source_placeholder:public_court_government_page_placeholder:598936`
  Blockers: request count exceeds approved max request count, source reference is a placeholder, not an explicit URL, URL scheme must be http or https
- `public_fetch_request_intent_006_07_691547_691547_market_metadata`
  Market: `691547`
  Source: `public_source_placeholder:public_market_metadata_endpoint_placeholder:691547`
  Blockers: request count exceeds approved max request count, source reference is a placeholder, not an explicit URL, URL scheme must be http or https
- `public_fetch_request_intent_006_08_691547_691547_domain_public_evidence`
  Market: `691547`
  Source: `public_source_placeholder:public_exchange_company_announcement_page_placeholder:691547`
  Blockers: request count exceeds approved max request count, source reference is a placeholder, not an explicit URL, URL scheme must be http or https
- `public_fetch_request_intent_006_09_692258_692258_market_metadata`
  Market: `692258`
  Source: `public_source_placeholder:public_market_metadata_endpoint_placeholder:692258`
  Blockers: request count exceeds approved max request count, source reference is a placeholder, not an explicit URL, URL scheme must be http or https
- `public_fetch_request_intent_006_10_692258_692258_domain_public_evidence`
  Market: `692258`
  Source: `public_source_placeholder:public_issuer_company_news_page_placeholder:692258`
  Blockers: request count exceeds approved max request count, source reference is a placeholder, not an explicit URL, URL scheme must be http or https

## Safety Boundary

- This preflight is local only and performs no network request.
- Only explicit, scoped, public read-only GET intents may pass.
- Evidence save and replay-before-update remain required.
