# PMBOT-OPENROUTER-045 Analyze 044 Acceptance Forbidden Phrase Edge

## Summary

044 ended as `blocked_acceptance_failed` after the small manual batch retry. It made 2 OpenRouter calls, attempted markets `569333` and `569334`, completed `569333`, skipped `569343` after fail-fast, and stopped on `569334` with:

`acceptance_gate_failed:569334:response_schema:forbidden_phrase:edge`

No prohibited-content detector issue was recorded in 044. The safety fields were clean: no Polymarket API calls, no wallet/order/trading activity, no runtime/dispatcher/background/browser/queue changes, and no API key value printed or written.

## What 569333 Proved

The `569333` artifact path proved that fenced JSON normalization was working as intended:

- Raw Markdown fencing was detected.
- `fenced_json_normalization.v1` was applied.
- The normalized JSON parsed successfully.
- Semantic repair remained disabled.
- The response passed acceptance for operator review.
- No safety issue appeared in the pass path.

## Why 569334 Failed

`569334` also used fenced JSON normalization successfully, but the normalized response failed the response-schema acceptance gate.

Sanitized diagnostic:

- gate id: `response_schema`
- detector rule: `forbidden_phrase:edge`
- checked content: normalized response content
- field path: `operator_review_checklist[9]`
- redacted excerpt: `Check for any market-specific [redacted:safety-term] cases or resolution exceptions in official rules`
- source classification: neutral phrase in a model-generated checklist item
- diagnostic classification: `false_positive_contextual_phrase`

The phrase was not used as trading/action language. It appeared as neutral checklist wording for special resolution cases. The block still should be preserved because accepted model-generated content should not contain that literal unless a future explicit policy chooses to allow it.

## Local Hardening Performed

Acceptance-gate reporting was improved so future forbidden-language failures include:

- gate id
- detector rule id
- forbidden phrase
- field path
- safe redacted excerpt/snippet
- diagnostic classification
- diagnostic reason code
- checked content source
- violation category

Prompt hardening was performed:

- The OpenRouter Sonnet system prompt now explicitly tells the model not to use the blocked literal tokens in JSON strings and gives neutral substitute wording for resolution exceptions.
- Manual packet-batch prompts now use less echo-prone category wording.
- Generated packet labels that contained the blocked literal inside an underscore-delimited label were sanitized to `value-boundary`.

Block behavior was preserved:

- The raw/normalized response validator now blocks the literal even in neutral `edge cases` wording.
- The response-schema validator continues to block it.
- `569334` was not marked accepted.
- 044 was not rewritten as success.
- `fenced_json_normalization.v1` was not changed.

## Tests Added Or Updated

Focused tests now cover:

- raw/normalized forbidden-phrase diagnostics, including neutral-context preserve-block behavior
- response-schema forbidden-phrase diagnostics with safe redacted excerpts
- normalized-content checked-source reporting
- prompt hardening in generated local/manual batch prompts
- 045 result artifact invariants

## 046 Readiness Notes

A future separate task may be:

`PMBOT-OPENROUTER-046-RETRY-SMALL-MANUAL-BATCH-AFTER-ACCEPTANCE-PHRASE-HARDENING`

046 is not run by this task. 045 does not approve 046 automatically. No live OpenRouter calls, Polymarket API calls, wallet access, orders, trading actions, browser automation, dispatcher changes, background workers, or queue mutations were performed or authorized here.
