# PMBOT Public Source URL Repair 010

- Failed requests loaded: 4
- Executable candidates: 1
- Live fetch performed: `false`

## Repaired Intents

- `public_fetch_request_intent_006_06_598936_598936_domain_public_evidence` `no_retry`
  Market: `598936`
  Action: `mark_no_retry`
  URL: `https://www.parliament.uk/about/how/elections-and-voting/general/`
- `public_fetch_request_intent_006_04_597964_597964_domain_public_evidence` `replacement_missing`
  Market: `597964`
  Action: `mark_missing`
  URL: `https://www.elysee.fr/emmanuel-macron`
- `public_fetch_request_intent_006_08_691547_691547_domain_public_evidence` `executable_candidate`
  Market: `691547`
  Action: `replace_url`
  URL: `https://blog.kraken.com/`
- `public_fetch_request_intent_006_10_692258_692258_domain_public_evidence` `blocked`
  Market: `692258`
  Action: `block`
  URL: `https://www.microstrategy.com/press`

## Limitations

- The repair packet does not prove source relevance or market outcomes.
- The repair packet does not discover new URLs outside local artifacts and the curated fixture.
- Sources blocked by access controls remain unavailable to this controlled fetch loop.
