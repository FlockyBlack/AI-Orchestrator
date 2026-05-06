# PMBOT OpenRouter 002 Strict JSON Recovery Patch

Task: `PMBOT-OPENROUTER-002-STRICT-JSON-RECOVERY-PATCH`

## Purpose

Allow the local OpenRouter prompt test harness to recover from a common model formatting failure where an otherwise safe JSON object is wrapped in a Markdown `json` fence.

This remains a manual, operator-triggered harness. It does not add runtime wiring, automatic LLM loops, wallet access, order handling, or trading authority.

## Recovery Rule

The harness accepts recovery only when the full raw model response is exactly one Markdown code fence with `json` or no language:

````text
```json
{ ... }
```
````

The fence is stripped, the recovered body must parse as a top-level JSON object, and the existing PMBOT safety checks still run before critic handoff.

## Rejection Cases

The harness still rejects:

- Prose before or after the fenced block.
- Unsupported fence languages.
- Multiple fenced blocks.
- Recovered JSON candidates that still contain Markdown fences.
- Arrays or other non-object top-level JSON values.
- Forbidden PMBOT fields or safety-boundary language.

The word `edge` remains forbidden as trading-edge language, except for the benign phrase `edge case` or `edge cases`.

Recommendation language is still blocked when tied to trading, markets, sides, outcomes, positions, entries,
exits, orders, or market decisions. Safe critic edit/review wording such as `candidate_json_edits`,
`suggested_fix`, or "manual source review is recommended" is allowed.

## Artifacts

Raw artifacts preserve the original model content, including any recovered Markdown fence.

Validation artifacts record:

- `recovery.applied`
- `recovery.method`
- `recovery.raw_markdown_fence_present`
- `warnings[].code == markdown_fence_recovered` for successful recovery

Content artifacts and critic handoff use the parsed recovered JSON object.

If a recovered or raw candidate parses as a JSON object but fails safety validation, the content artifact
uses `content_status: rejected` with `parsed_content`; it is not mislabeled as `not_valid_json_object`.

Summary artifacts record:

- `sonnet_json_recovered`
- `critic_json_recovered`

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
