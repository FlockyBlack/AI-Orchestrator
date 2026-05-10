# PMBOT Repaired Public Fetch Manifest 010

- Executable requests: 1
- Max request count: 5
- Within request limit: `true`
- Live fetch performed: `false`

## Executable Request Intents

- `public_fetch_request_intent_006_08_691547_691547_domain_public_evidence`
  Market: `691547`
  Source: `https://blog.kraken.com/`
  Repair action: `replace_url`

## No-Retry Request Intents

- `public_fetch_request_intent_006_06_598936_598936_domain_public_evidence` `no_retry` `598936`

## Replacement-Missing Request Intents

- `public_fetch_request_intent_006_04_597964_597964_domain_public_evidence` `replacement_missing` `597964`

## Blocked Request Intents

- `public_fetch_request_intent_006_10_692258_692258_domain_public_evidence` `blocked` `692258`

## Safety Boundary

- Only executable request intents may be used by the second controlled fetch.
- Missing, no-retry, blocked, and omitted intents are not fetched.
