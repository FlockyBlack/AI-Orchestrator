# PMBOT Concrete URL Manifest Operator Card

- Original request intents: 10
- Executable concrete URL requests: 5
- Missing URL requests: 5
- Blocked requests: 0
- Next fetch can run after approval: `true`
- Live fetch performed: `false`

## What Changed After PRACTICAL-007

- Placeholder request intents were separated from executable concrete URL intents.
- Executable request count was capped at five.
- Operator approval for the next fetch remains pending.

## Why PRACTICAL-007 Blocked Fetch

- The prior manifest had placeholder source references instead of concrete HTTP(S) URLs.
- The prior manifest had ten request intents while scoped approval allowed five.

## Concrete Safe URLs

- `public_fetch_request_intent_006_02_563650_563650_domain_public_evidence` market `563650`
  URL: `https://www.supremecourt.gov/docket/docket.aspx`
  Reason: Official public Supreme Court docket search page; the exact docket id is still missing locally, so this is a future read-only source candidate only.
- `public_fetch_request_intent_006_06_598936_598936_domain_public_evidence` market `598936`
  URL: `https://www.parliament.uk/about/how/elections-and-voting/general/`
  Reason: Official UK Parliament public elections page; suitable as a public government/parliament source candidate, with final election-call evidence still requiring review.
- `public_fetch_request_intent_006_04_597964_597964_domain_public_evidence` market `597964`
  URL: `https://www.elysee.fr/emmanuel-macron`
  Reason: Official public Elysee page for Emmanuel Macron; suitable as a read-only official-status source candidate, without implying outcome verification.
- `public_fetch_request_intent_006_08_691547_691547_domain_public_evidence` market `691547`
  URL: `https://www.kraken.com/blog`
  Reason: Official public Kraken blog/news page; suitable as a read-only company announcement source candidate, without implying IPO outcome verification.
- `public_fetch_request_intent_006_10_692258_692258_domain_public_evidence` market `692258`
  URL: `https://www.microstrategy.com/press`
  Reason: Official public MicroStrategy press page pattern; suitable as a read-only issuer/company news source candidate, without implying Bitcoin sale outcome verification.

## Markets Still Needing URLs

- `public_fetch_request_intent_006_01_563650_563650_market_metadata` market `563650`
  Source category: `public_market_metadata_endpoint_placeholder`
  Reason: The local artifacts include only a market id and placeholder metadata reference; no stable public market metadata URL can be safely inferred without browsing or a Polymarket API call.
- `public_fetch_request_intent_006_03_597964_597964_market_metadata` market `597964`
  Source category: `public_market_metadata_endpoint_placeholder`
  Reason: The local artifacts include only a market id and placeholder metadata reference; no stable public market metadata URL can be safely inferred without browsing or a Polymarket API call.
- `public_fetch_request_intent_006_05_598936_598936_market_metadata` market `598936`
  Source category: `public_market_metadata_endpoint_placeholder`
  Reason: The local artifacts include only a market id and placeholder metadata reference; no stable public market metadata URL can be safely inferred without browsing or a Polymarket API call.
- `public_fetch_request_intent_006_07_691547_691547_market_metadata` market `691547`
  Source category: `public_market_metadata_endpoint_placeholder`
  Reason: The local artifacts include only a market id and placeholder metadata reference; no stable public market metadata URL can be safely inferred without browsing or a Polymarket API call.
- `public_fetch_request_intent_006_09_692258_692258_market_metadata` market `692258`
  Source category: `public_market_metadata_endpoint_placeholder`
  Reason: The local artifacts include only a market id and placeholder metadata reference; no stable public market metadata URL can be safely inferred without browsing or a Polymarket API call.

## Blocked Requests


## Operator Must Approve Next

- Approve the pending scoped approval artifact for the future PRACTICAL-008 controlled public read-only fetch task.
