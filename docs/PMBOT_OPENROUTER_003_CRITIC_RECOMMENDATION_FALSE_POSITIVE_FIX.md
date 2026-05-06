# PMBOT OpenRouter 003 Critic Recommendation False Positive Fix

Task: `PMBOT-OPENROUTER-003-CRITIC-RECOMMENDATION-FALSE-POSITIVE-FIX`

## Purpose

Fix a critic validation false positive where safe JSON/schema edit wording such as "Minor edits are recommended" was rejected as if it were a trading recommendation.

The OpenRouter harness remains local, manual, operator-gated, and validator-gated. This patch does not add runtime wiring, dispatcher wiring, wallet access, order handling, automatic LLM loops, or trading authority.

## Validator Change

The forbidden recommendation rule is now context-aware.

Still rejected:

- Trading recommendation.
- Market recommendation.
- Recommended side, outcome, trade, position, entry, or exit.
- Recommend buying, selling, holding, entering, exiting, or trading.
- Recommend placing, submitting, sending, or creating an order.
- Recommend a market decision.

Allowed when otherwise safe:

- `candidate_json_edits`
- `proposed_edits`
- `suggested_fixes`
- `review_notes`
- `recommended_candidate_json_edits` compatibility field names.
- "Minor edits are recommended."
- "Operator review is recommended."
- "Manual source review is recommended."

Existing strict checks remain in place for probability, EV, edge, scoring, side selection, buy/sell/hold/enter/exit language, orders, wallet/private-key/credential language, and market decisions. The previously fixed benign `edge case` / `edge cases` allowance is preserved.

Follow-on note from PMBOT OpenRouter 004: negative safety attestations are also context-aware. The validator allows clear absence or avoidance statements that name forbidden categories, but still rejects actual market-action language and unsafe bypass phrasing.

## Critic Prompt

The critic system prompt now asks for edit feedback with field names such as `candidate_json_edits`, `proposed_edits`, `suggested_fixes`, or `review_notes`, and asks the model to avoid `recommended` where possible.

The validator still accepts safe edit-related `recommended` wording in case a model emits it.

## Content Artifacts

When raw, repaired, or effective model content parses as a JSON object but fails safety validation, the content artifact now records:

- `content_status: rejected`
- `status: rejected`
- `parsed_content`
- `validation_errors`

This prevents parsed JSON objects from being mislabeled as `not_valid_json_object`.

## Safety Boundary

- Analysis only.
- Manual review only.
- Operator gated.
- Validator gated.
- No trading recommendations.
- No side selection.
- No probability estimates.
- No EV, edge, value, or scoring output.
- No buy, sell, hold, enter, or exit instructions.
- No market decisions.
- No wallet, private key, credential, or order handling.
- No runtime or dispatcher wiring.
- No automatic LLM loops.
- No secrets in git, logs, artifacts, stdout, or stderr.
