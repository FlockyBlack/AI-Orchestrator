# Source accessibility learning

- Learning ID: `source-accessibility-learning-009`
- Reachable sources: 1
- Failed sources: 4
- Replay-usable sources: 1

## Source records

- `public_fetch_request_intent_006_02_563650_563650_domain_public_evidence`
  Status: `reachable`
  Handling: `keep_for_operator_review`
  Replay usable: `true`
- `public_fetch_request_intent_006_06_598936_598936_domain_public_evidence`
  Status: `failed`
  Handling: `use_alternative_official_source`
  Replay usable: `false`
- `public_fetch_request_intent_006_04_597964_597964_domain_public_evidence`
  Status: `failed`
  Handling: `replace_url`
  Replay usable: `false`
- `public_fetch_request_intent_006_08_691547_691547_domain_public_evidence`
  Status: `failed`
  Handling: `replace_url`
  Replay usable: `false`
- `public_fetch_request_intent_006_10_692258_692258_domain_public_evidence`
  Status: `failed`
  Handling: `use_alternative_official_source`
  Replay usable: `false`

## Recommended handling updates

- `public_fetch_request_intent_006_02_563650_563650_domain_public_evidence` -> `keep_for_operator_review`
- `public_fetch_request_intent_006_06_598936_598936_domain_public_evidence` -> `use_alternative_official_source`
- `public_fetch_request_intent_006_04_597964_597964_domain_public_evidence` -> `replace_url`
- `public_fetch_request_intent_006_08_691547_691547_domain_public_evidence` -> `replace_url`
- `public_fetch_request_intent_006_10_692258_692258_domain_public_evidence` -> `use_alternative_official_source`

## Safety boundary

- Source accessibility learning only; no outcome-correctness learning is performed.
- No autonomous training, real trade decision, wallet path, order path, or executable market output is created.
- A later scoped task must handle any corrected URL/source packet.
