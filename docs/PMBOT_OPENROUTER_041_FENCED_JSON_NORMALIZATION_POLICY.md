# PMBOT OpenRouter 041 Fenced JSON Normalization Policy

Task: `PMBOT-OPENROUTER-041-FENCED-JSON-NORMALIZATION-POLICY`

## Summary

PMBOT-OPENROUTER-036 attempted a controlled small manual OpenRouter batch and stopped after the first market because the model returned a single Markdown-fenced JSON block instead of raw JSON. PMBOT-OPENROUTER-037 hardened the prompt and strict JSON tests. PMBOT-OPENROUTER-040 retried after artifact reconciliation and hit the same failure on market `569333`: `blocked_markdown_fence_detected` with `markdown_fence_detected:569333`.

The repeated 036 and 040 behavior shows that prompt-only hardening is insufficient for this provider/model path. The validator now has a narrow local normalization policy for exactly one full-response fenced JSON object.

## Local Changes Made

- Added `fenced_json_normalization.v1` to the OpenRouter/LLM response validation path.
- Kept raw strict JSON parsing strict and separately reported.
- Preserved the raw model response in raw artifacts, including any fence.
- Added raw-vs-normalized validation fields:
  - `raw_response_was_markdown_fenced`
  - `normalized_from_markdown_fence`
  - `raw_strict_json_parse_passed`
  - `normalized_json_parse_passed`
  - `normalization_policy_applied`
  - `normalization_policy_version`
  - `normalized_content_used`
- Added summary flags so future batch summaries can report raw fence detection and normalized content use.
- Added focused local tests for the normalization and rejection matrix.

## Acceptance Rules

The policy accepts clean raw JSON object text unchanged. It also accepts fenced content only when all of these are true:

- The raw content is exactly one Markdown fenced block, apart from surrounding whitespace.
- The fence language is `json` or empty.
- The extracted body parses as valid JSON.
- The parsed top-level value is a JSON object.
- The parsed object passes the existing PMBOT validation gates.

## Rejection Rules

The policy rejects:

- Prose before the opening fence.
- Prose after the closing fence.
- Multiple fenced blocks.
- Unsupported fence languages.
- Non-JSON Markdown content.
- JSON arrays where an object is required.
- Malformed or truncated JSON.
- Content that would require quote repair, comma repair, field invention, schema guessing, or semantic rewrite.
- Any normalized JSON that violates existing PMBOT safety checks.

## Not Semantic Repair

This is syntactic unwrapping only. The validator removes one exact Markdown wrapper when the body is already a valid JSON object. It does not infer missing fields, modify values, rewrite unsafe language, patch malformed JSON, guess schema intent, or convert arrays into objects.

## Raw Transparency

Raw response transparency is preserved. A fenced raw response must still report `raw_strict_json_parse_passed: false`. Acceptance can only happen through the explicit `fenced_json_normalization.v1` path, and artifacts must show that normalized content was used.

## Operator Review Boundary

Acceptance remains operator-review-only. It is not approval for resolution action, live trading, wallet access, orders, dispatcher/runtime wiring, background workers, queue mutation, or automated downstream execution. All existing schema, safety-language, prohibited-content, and manual-review gates still apply after normalization.

## Tests Added Or Updated

- Clean raw JSON object accepted without normalization.
- Single `json` fenced object normalized and accepted.
- Single unlabeled fenced object normalized and accepted.
- Prose before a fence rejected.
- Prose after a fence rejected.
- Multiple fenced blocks rejected.
- Fenced array rejected where object is required.
- Fenced malformed JSON rejected.
- Non-JSON Markdown rejected.
- Normalized content still rejected when PMBOT prohibited language is present.
- Normalized content still rejected when PMBOT prohibited analytic content is present.
- Result artifacts preserve raw-vs-normalized flags.

## Future 042 Readiness

A future task may be proposed as:

`PMBOT-OPENROUTER-042-RETRY-SMALL-MANUAL-BATCH-WITH-FENCED-JSON-NORMALIZATION`

This 041 task does not run 042, does not approve 042 automatically, and performs no live calls.
