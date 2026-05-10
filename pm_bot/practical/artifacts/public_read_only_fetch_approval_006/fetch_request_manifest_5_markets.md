# PMBOT Public Fetch Request Manifest

- Manifest ID: `public-read-only-fetch-prep-005-5-markets.request_manifest.006`
- Fetch plan ID: `public-read-only-fetch-prep-005-5-markets`
- Markets: 5
- Request intents: 10
- Max requests: 10
- Manifest only: `true`
- Live fetch performed: `false`

## Request Intents

- `public_fetch_request_intent_006_01_563650_563650_market_metadata`
  Market: `563650` SCOTUS accepts sports event contract case by July 31, 2026?
  Source category: `public_market_metadata_endpoint_placeholder`
  Source: public market metadata endpoint placeholder
  Evidence: public market metadata snapshot
  Allowed by registry: `true`
  Save evidence as: `pm_bot/practical/artifacts/public_read_only_fetch_execution_007/saved_public_evidence/563650/public_fetch_request_intent_006_01_563650_563650_market_metadata.saved_public_evidence_packet.json`
- `public_fetch_request_intent_006_02_563650_563650_domain_public_evidence`
  Market: `563650` SCOTUS accepts sports event contract case by July 31, 2026?
  Source category: `public_court_government_page_placeholder`
  Source: public court/government page placeholder
  Evidence: official docket or resolution page snapshot
  Allowed by registry: `true`
  Save evidence as: `pm_bot/practical/artifacts/public_read_only_fetch_execution_007/saved_public_evidence/563650/public_fetch_request_intent_006_02_563650_563650_domain_public_evidence.saved_public_evidence_packet.json`
- `public_fetch_request_intent_006_03_597964_597964_market_metadata`
  Market: `597964` Macron out by June 30, 2026?
  Source category: `public_market_metadata_endpoint_placeholder`
  Source: public market metadata endpoint placeholder
  Evidence: public market metadata snapshot
  Allowed by registry: `true`
  Save evidence as: `pm_bot/practical/artifacts/public_read_only_fetch_execution_007/saved_public_evidence/597964/public_fetch_request_intent_006_03_597964_597964_market_metadata.saved_public_evidence_packet.json`
- `public_fetch_request_intent_006_04_597964_597964_domain_public_evidence`
  Market: `597964` Macron out by June 30, 2026?
  Source category: `public_resolution_source_page_placeholder`
  Source: public resolution source page placeholder
  Evidence: public official status or resolution page snapshot
  Allowed by registry: `true`
  Save evidence as: `pm_bot/practical/artifacts/public_read_only_fetch_execution_007/saved_public_evidence/597964/public_fetch_request_intent_006_04_597964_597964_domain_public_evidence.saved_public_evidence_packet.json`
- `public_fetch_request_intent_006_05_598936_598936_market_metadata`
  Market: `598936` Will the next UK election be called by June 30, 2026?
  Source category: `public_market_metadata_endpoint_placeholder`
  Source: public market metadata endpoint placeholder
  Evidence: public market metadata snapshot
  Allowed by registry: `true`
  Save evidence as: `pm_bot/practical/artifacts/public_read_only_fetch_execution_007/saved_public_evidence/598936/public_fetch_request_intent_006_05_598936_598936_market_metadata.saved_public_evidence_packet.json`
- `public_fetch_request_intent_006_06_598936_598936_domain_public_evidence`
  Market: `598936` Will the next UK election be called by June 30, 2026?
  Source category: `public_court_government_page_placeholder`
  Source: public government or parliament page placeholder
  Evidence: public election or parliament page snapshot
  Allowed by registry: `true`
  Save evidence as: `pm_bot/practical/artifacts/public_read_only_fetch_execution_007/saved_public_evidence/598936/public_fetch_request_intent_006_06_598936_598936_domain_public_evidence.saved_public_evidence_packet.json`
- `public_fetch_request_intent_006_07_691547_691547_market_metadata`
  Market: `691547` Kraken IPO by December 31, 2026?
  Source category: `public_market_metadata_endpoint_placeholder`
  Source: public market metadata endpoint placeholder
  Evidence: public market metadata snapshot
  Allowed by registry: `true`
  Save evidence as: `pm_bot/practical/artifacts/public_read_only_fetch_execution_007/saved_public_evidence/691547/public_fetch_request_intent_006_07_691547_691547_market_metadata.saved_public_evidence_packet.json`
- `public_fetch_request_intent_006_08_691547_691547_domain_public_evidence`
  Market: `691547` Kraken IPO by December 31, 2026?
  Source category: `public_exchange_company_announcement_page_placeholder`
  Source: public exchange/company announcement page placeholder
  Evidence: public listing or company announcement snapshot
  Allowed by registry: `true`
  Save evidence as: `pm_bot/practical/artifacts/public_read_only_fetch_execution_007/saved_public_evidence/691547/public_fetch_request_intent_006_08_691547_691547_domain_public_evidence.saved_public_evidence_packet.json`
- `public_fetch_request_intent_006_09_692258_692258_market_metadata`
  Market: `692258` MicroStrategy sells any Bitcoin by June 30, 2026?
  Source category: `public_market_metadata_endpoint_placeholder`
  Source: public market metadata endpoint placeholder
  Evidence: public market metadata snapshot
  Allowed by registry: `true`
  Save evidence as: `pm_bot/practical/artifacts/public_read_only_fetch_execution_007/saved_public_evidence/692258/public_fetch_request_intent_006_09_692258_692258_market_metadata.saved_public_evidence_packet.json`
- `public_fetch_request_intent_006_10_692258_692258_domain_public_evidence`
  Market: `692258` MicroStrategy sells any Bitcoin by June 30, 2026?
  Source category: `public_issuer_company_news_page_placeholder`
  Source: public issuer/company news page placeholder
  Evidence: public issuer news or filing summary snapshot
  Allowed by registry: `true`
  Save evidence as: `pm_bot/practical/artifacts/public_read_only_fetch_execution_007/saved_public_evidence/692258/public_fetch_request_intent_006_10_692258_692258_domain_public_evidence.saved_public_evidence_packet.json`

## Blocked Source Categories

- `authenticated_endpoint`
- `browser_session_cookie_based_source`
- `forum_rumor_only_unlabeled_source`
- `order_endpoint`
- `private_api_key_endpoint`
- `source_requiring_bypass_or_automation`
- `source_requiring_kyc_or_login`
- `trading_endpoint`
- `wallet_signing_endpoint`

## Safety Boundary

- This is a request-intent manifest only.
- No public source is contacted.
- Auth, wallet, signing, orders, trading paths, schedulers, and polling remain blocked.
