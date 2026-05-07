# PMBOT OpenRouter 037 Strict JSON Hardening

## Summary

PMBOT-OPENROUTER-036 was a separately approved small manual OpenRouter batch test. It stopped after one OpenRouter call for market_id 569333. The first response was Markdown-fenced, strict raw JSON validation rejected it, no repair was applied, and market_ids 569334 and 569343 were skipped by fail-fast behavior.

The 036 result was meaningful because it showed the raw-response validator correctly enforced the contract: a Markdown-fenced response does not start with `{`, does not end with `}`, and contains Markdown fencing. Treating that as invalid protects the operator-review pipeline from silently accepting non-raw model output.

## Local Hardening

037 made no live calls. It only updated local prompt and validator-test coverage.

The OpenRouter harness system prompts now explicitly require exactly one raw JSON object, forbid Markdown wrapping, forbid ```json fences and other code fences, forbid prose before or after JSON, require `{` as the first character and `}` as the last character, and state that Markdown fencing makes the response invalid.

The manual prompt exporters and existing prompt artifacts were aligned with the same strict raw JSON wording. The safety boundary remains analysis-only and manual-review-only. Acceptance remains operator-review readiness only and is never trading approval.

Focused tests now cover strict Markdown-fence rejection, clean raw JSON acceptance, prompt wording for no Markdown fences, operator-review-only readiness, and prohibited trading language blocking.

No auto-repair was added. The existing local fence-repair path remains explicit and opt-in only; strict default validation continues to reject fenced raw content.

## 037 Safety

- OpenRouter calls performed: 0
- Polymarket API calls performed: 0
- Wallet/private-key access: none
- Orders/trading: none
- Runtime wiring/dispatcher/background workers: none
- Queue mutation: none
- Browser automation: none
- API key value read, printed, written, or committed: none

Ignored raw 036 OpenRouter artifacts remain under `pm_bot/llm/openrouter_test_artifacts/pmbot_openrouter_036_small_manual_batch_live_call` and were not staged.

## Future 038 Readiness

A future possible task name is:

`PMBOT-OPENROUTER-038-RETRY-SMALL-MANUAL-BATCH-AFTER-STRICT-JSON-HARDENING`

037 does not approve 038. 038 would require separate operator approval before any live OpenRouter call. Any future live run should keep fail-fast strict raw JSON validation, no automatic repair unless separately authorized, operator-review-only acceptance, and no trading approval.
