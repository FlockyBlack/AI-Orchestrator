# PMBOT Enriched Manifest Execution Preflight

- Ready to execute public read-only fetch: `false`
- Would be ready after operator approval: `true`
- Executable requests: 5
- Request count within limit: `true`
- Missing URL count: 5
- Blocked request count: 0
- Approval required: `true`
- Approval granted: `false`
- Live fetch performed: `false`

## Blockers

- operator approval has not been granted

## Warnings

- 5 missing URL request intents remain non-executable.

## URL Safety

- `public_fetch_request_intent_006_02_563650_563650_domain_public_evidence` allowed: `true`
  Market: `563650`
  URL: `https://www.supremecourt.gov/docket/docket.aspx`
  Blockers: none
- `public_fetch_request_intent_006_06_598936_598936_domain_public_evidence` allowed: `true`
  Market: `598936`
  URL: `https://www.parliament.uk/about/how/elections-and-voting/general/`
  Blockers: none
- `public_fetch_request_intent_006_04_597964_597964_domain_public_evidence` allowed: `true`
  Market: `597964`
  URL: `https://www.elysee.fr/emmanuel-macron`
  Blockers: none
- `public_fetch_request_intent_006_08_691547_691547_domain_public_evidence` allowed: `true`
  Market: `691547`
  URL: `https://www.kraken.com/blog`
  Blockers: none
- `public_fetch_request_intent_006_10_692258_692258_domain_public_evidence` allowed: `true`
  Market: `692258`
  URL: `https://www.microstrategy.com/press`
  Blockers: none

## Safety Boundary

- This preflight is local-only and performs no network request.
- Pending approval keeps execution blocked until an operator approves the future task.
