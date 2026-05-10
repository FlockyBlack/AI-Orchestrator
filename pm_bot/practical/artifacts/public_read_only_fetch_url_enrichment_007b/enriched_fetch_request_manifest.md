# PMBOT Enriched Public Fetch Request Manifest

- Source task: `ORCH-PMBOT-PRACTICAL-007-FIRST-CONTROLLED-PUBLIC-READ-ONLY-FETCH-EXECUTION-OPERATOR-APPROVED`
- Enrichment task: `ORCH-PMBOT-PRACTICAL-007B-ENRICH-PUBLIC-SOURCE-URL-MANIFEST-LOCAL-ONLY`
- Original request intents: 10
- Executable request intents: 5
- Missing URL intents: 5
- Blocked intents: 0
- Max requests: 5
- Within request limit: `true`
- Live fetch performed: `false`

## Executable Request Intents

- `public_fetch_request_intent_006_02_563650_563650_domain_public_evidence`
  Market: `563650` SCOTUS accepts sports event contract case by July 31, 2026?
  Source category: `public_court_government_page_placeholder`
  Concrete public URL: `https://www.supremecourt.gov/docket/docket.aspx`
  Reason: Official public Supreme Court docket search page; the exact docket id is still missing locally, so this is a future read-only source candidate only.
- `public_fetch_request_intent_006_06_598936_598936_domain_public_evidence`
  Market: `598936` Will the next UK election be called by June 30, 2026?
  Source category: `public_court_government_page_placeholder`
  Concrete public URL: `https://www.parliament.uk/about/how/elections-and-voting/general/`
  Reason: Official UK Parliament public elections page; suitable as a public government/parliament source candidate, with final election-call evidence still requiring review.
- `public_fetch_request_intent_006_04_597964_597964_domain_public_evidence`
  Market: `597964` Macron out by June 30, 2026?
  Source category: `public_resolution_source_page_placeholder`
  Concrete public URL: `https://www.elysee.fr/emmanuel-macron`
  Reason: Official public Elysee page for Emmanuel Macron; suitable as a read-only official-status source candidate, without implying outcome verification.
- `public_fetch_request_intent_006_08_691547_691547_domain_public_evidence`
  Market: `691547` Kraken IPO by December 31, 2026?
  Source category: `public_exchange_company_announcement_page_placeholder`
  Concrete public URL: `https://www.kraken.com/blog`
  Reason: Official public Kraken blog/news page; suitable as a read-only company announcement source candidate, without implying IPO outcome verification.
- `public_fetch_request_intent_006_10_692258_692258_domain_public_evidence`
  Market: `692258` MicroStrategy sells any Bitcoin by June 30, 2026?
  Source category: `public_issuer_company_news_page_placeholder`
  Concrete public URL: `https://www.microstrategy.com/press`
  Reason: Official public MicroStrategy press page pattern; suitable as a read-only issuer/company news source candidate, without implying Bitcoin sale outcome verification.

## Missing URL Request Intents

- `public_fetch_request_intent_006_01_563650_563650_market_metadata`
  Market: `563650` SCOTUS accepts sports event contract case by July 31, 2026?
  Source category: `public_market_metadata_endpoint_placeholder`
  Reason: The local artifacts include only a market id and placeholder metadata reference; no stable public market metadata URL can be safely inferred without browsing or a Polymarket API call.
- `public_fetch_request_intent_006_03_597964_597964_market_metadata`
  Market: `597964` Macron out by June 30, 2026?
  Source category: `public_market_metadata_endpoint_placeholder`
  Reason: The local artifacts include only a market id and placeholder metadata reference; no stable public market metadata URL can be safely inferred without browsing or a Polymarket API call.
- `public_fetch_request_intent_006_05_598936_598936_market_metadata`
  Market: `598936` Will the next UK election be called by June 30, 2026?
  Source category: `public_market_metadata_endpoint_placeholder`
  Reason: The local artifacts include only a market id and placeholder metadata reference; no stable public market metadata URL can be safely inferred without browsing or a Polymarket API call.
- `public_fetch_request_intent_006_07_691547_691547_market_metadata`
  Market: `691547` Kraken IPO by December 31, 2026?
  Source category: `public_market_metadata_endpoint_placeholder`
  Reason: The local artifacts include only a market id and placeholder metadata reference; no stable public market metadata URL can be safely inferred without browsing or a Polymarket API call.
- `public_fetch_request_intent_006_09_692258_692258_market_metadata`
  Market: `692258` MicroStrategy sells any Bitcoin by June 30, 2026?
  Source category: `public_market_metadata_endpoint_placeholder`
  Reason: The local artifacts include only a market id and placeholder metadata reference; no stable public market metadata URL can be safely inferred without browsing or a Polymarket API call.

## Blocked Request Intents


## Omitted Safe Candidates

- none

## Blockers

- none

## Warnings

- 5 placeholder request intents still lack concrete public URLs.

## Safety Boundary

- This artifact is local-only manifest preparation.
- No URL was fetched while creating this package.
- Non-executable missing, blocked, and omitted entries do not carry concrete HTTP(S) URLs.
