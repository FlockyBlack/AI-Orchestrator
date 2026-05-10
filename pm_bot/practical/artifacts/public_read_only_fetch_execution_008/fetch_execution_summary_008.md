# PMBOT PRACTICAL-008 Fetch Execution Summary

- Live public read-only fetch performed: `true`
- Requests attempted: 5
- Requests succeeded: 1
- Requests failed: 4
- Requests blocked: 0
- Evidence packets created: 1
- Replay performed: `true`

## Fetch Results

- `public_fetch_request_intent_006_02_563650_563650_domain_public_evidence` `succeeded` `https://www.supremecourt.gov/docket/docket.aspx`
  HTTP status: `200`
  Evidence: `pm_bot/practical/artifacts/public_read_only_fetch_execution_008/evidence_packets/public_fetch_008_563650_public_fetch_request_intent_006_02_563650_563650_domain_public_evidence_a6d1969391feeee9.json`
- `public_fetch_request_intent_006_06_598936_598936_domain_public_evidence` `failed` `https://www.parliament.uk/about/how/elections-and-voting/general/`
  Error: HTTP fetch failed with status 403
- `public_fetch_request_intent_006_04_597964_597964_domain_public_evidence` `failed` `https://www.elysee.fr/emmanuel-macron`
  Error: HTTP fetch failed: [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer certificate (_ssl.c:1010)
- `public_fetch_request_intent_006_08_691547_691547_domain_public_evidence` `failed` `https://www.kraken.com/blog`
  Error: redirect blocked: 308 https://blog.kraken.com/
- `public_fetch_request_intent_006_10_692258_692258_domain_public_evidence` `failed` `https://www.microstrategy.com/press`
  Error: HTTP fetch failed with status 403

## Blockers

- none

## Warnings

- 5 missing URL request intents remain non-executable

## Safety Boundary

- Public read-only GET only, with no authentication, cookies, request body, wallet access, order path, or trading action.
- Saved evidence packets are replay inputs only and do not update prior analyses automatically.
