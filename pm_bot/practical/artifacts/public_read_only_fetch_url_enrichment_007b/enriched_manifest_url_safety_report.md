# PMBOT Enriched Manifest URL Safety Report

- Checked executable requests: 5
- Allowed executable URLs: 5
- Blocked/non-executable count: 0
- Missing URL count: 5
- Live fetch performed: `false`

## Per Request Safety

- `public_fetch_request_intent_006_02_563650_563650_domain_public_evidence` allowed: `true`
  Market: `563650`
  URL: `https://www.supremecourt.gov/docket/docket.aspx`
  Blockers: none
  Warnings: source category is a placeholder category with a concrete URL reference
- `public_fetch_request_intent_006_06_598936_598936_domain_public_evidence` allowed: `true`
  Market: `598936`
  URL: `https://www.parliament.uk/about/how/elections-and-voting/general/`
  Blockers: none
  Warnings: source category is a placeholder category with a concrete URL reference
- `public_fetch_request_intent_006_04_597964_597964_domain_public_evidence` allowed: `true`
  Market: `597964`
  URL: `https://www.elysee.fr/emmanuel-macron`
  Blockers: none
  Warnings: source category is a placeholder category with a concrete URL reference
- `public_fetch_request_intent_006_08_691547_691547_domain_public_evidence` allowed: `true`
  Market: `691547`
  URL: `https://www.kraken.com/blog`
  Blockers: none
  Warnings: source category is a placeholder category with a concrete URL reference
- `public_fetch_request_intent_006_10_692258_692258_domain_public_evidence` allowed: `true`
  Market: `692258`
  URL: `https://www.microstrategy.com/press`
  Blockers: none
  Warnings: source category is a placeholder category with a concrete URL reference

## Global Blockers

- none

## Global Warnings

- 5 request intents are missing concrete URLs and are non-executable.

## Safety Boundary

- URL safety validation is local and happens before any request.
- This report did not perform a network fetch.
