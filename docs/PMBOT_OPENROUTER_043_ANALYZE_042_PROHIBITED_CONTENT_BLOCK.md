# PMBOT OpenRouter 043 Analyze 042 Prohibited Content Block

## Summary

PMBOT-OPENROUTER-042 retried the small manual batch with `fenced_json_normalization.v1`. It performed 2 OpenRouter calls, completed market `569333`, attempted market `569334`, skipped market `569343`, and stopped with `blocked_prohibited_content_detected` because `569334` failed the content acceptance gate.

This 043 task was local-only. It made no OpenRouter calls, no Polymarket API calls, no wallet/order/trading changes, no runtime wiring changes, no dispatcher changes, no background worker changes, no browser automation, and no queue mutation.

## What 569333 Proved

Market `569333` showed that fenced JSON normalization worked as intended:

- The raw response was Markdown-fenced and preserved.
- Strict raw JSON parsing remained strict and did not pass on the fenced response.
- Normalized JSON parsing passed under `fenced_json_normalization.v1`.
- Semantic repair stayed disabled.
- Schema validation passed.
- The normalized response passed the acceptance gate for operator-review use only.

This confirms the pass path is represented correctly without changing the safety boundary.

## Why 569334 Blocked

Market `569334` also normalized successfully from a single full-response JSON fence and passed response schema validation. It blocked after content validation found prohibited action-keyword language in `risk_notes[3]`.

Sanitized diagnostic:

- detector_rule_id: `forbidden_phrase:buy`
- violation_category: `market_action_keyword`
- field_path: `risk_notes[3]`
- safe_redacted_snippet: `Political prediction markets for elections years in advance carry high uncertainty due to candidate [redacted:safety-term]/[redacted:safety-term], scandals, economic changes, and unforeseen events`
- diagnostic_classification: `false_positive_validator_rule`

The blocked text appears to describe candidate lifecycle uncertainty, not an operator market action. The validator rule was intentionally broad, so it classified a non-action phrase as prohibited content.

## Preserve The Block

The block should be preserved. This task does not mark `569334` accepted, does not rewrite 042 as success, does not weaken the validator to force acceptance, and does not change `fenced_json_normalization.v1`.

The diagnostic is useful for future review, but the safe behavior remains fail closed.

## Local Hardening

Validator reporting now includes structured prohibited-content diagnostics:

- `violation_category`
- `detector_rule_id`
- `field_path`
- `safe_redacted_snippet`
- `diagnostic_status`
- `diagnostic_reason_code`
- `prohibited_content_diagnostics`

The rejected content artifact also carries the sanitized diagnostics so a future block can be reviewed without exposing the full model response.

Prompt hardening was also performed:

- The Sonnet system prompt now asks for neutral candidate-participation wording instead of market-action verbs or slash-paired lifecycle shortcuts.
- The manual packet prompt generator now tells responses not to repeat restriction wording in output fields.
- The regenerated manual prompt files include the stricter wording.

Focused tests were added for the observed candidate-lifecycle false positive category and for normalized fenced JSON prohibited-content reporting.

## Future 044 Readiness

A future possible task is:

`PMBOT-OPENROUTER-044-RETRY-SMALL-MANUAL-BATCH-AFTER-PROHIBITED-CONTENT-HARDENING`

044 is not run by this task. 044 is not approved automatically by this task. Any future 044 must be a separate explicit task with fresh prechecks and its own safety gates before any live calls.

