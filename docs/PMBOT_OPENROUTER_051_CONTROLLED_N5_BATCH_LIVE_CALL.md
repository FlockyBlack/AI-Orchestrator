# PMBOT OpenRouter 051 Controlled N=5 Batch Live Call

Status: `completed_pushed`

This task performed a strictly bounded OpenRouter-only Sonnet batch for local PMBOT operator review artifacts. It did not perform trading, market decisioning, Polymarket API calls, wallet/order access, runtime wiring, dispatcher work, browser automation, or queue mutation.

## Batch Scope
- Approved market IDs: `['569344', '569366', '569368', '569373', '573656']`
- Attempted market IDs: `['569344', '569366', '569368', '569373', '573656']`
- Completed market IDs: `['569344', '569366', '569368', '569373', '573656']`
- Skipped market IDs: `[]`
- Total OpenRouter calls: `5`
- Model: `anthropic/claude-sonnet-4.5`
- No retries: `true`
- Fail-fast triggered: `False`
- Fail-fast reason: `None`

## Cost And Tokens
- Max total cost allowed: `0.35` USD
- Aggregate prompt tokens: `20768`
- Aggregate completion tokens: `9119`
- Aggregate total tokens: `29887`
- Aggregate cost: `0.199089` USD
- Cost cap exceeded: `False`

## Normalization
- Policy: `fenced_json_normalization.v1`
- Raw response preserved: `true`
- Semantic repair allowed: `false`
- Any raw Markdown fence detected: `True`
- Any normalization policy applied: `True`

## Acceptance And Safety
- All completed responses accepted for operator review: `True`
- Prohibited content detected: `False`
- Forbidden phrase detected: `False`
- Acceptance means safe for operator review only, not trading approval.
- No authority was created for trading, orders, wallets, runtime, dispatcher, browser automation, or queues.

## Artifacts
- Batch summary: `pm_bot/llm/openrouter_test_artifacts/pmbot_openrouter_051_controlled_n5_batch_live_call/openrouter_batch_summary.v1.json`
- Cost report JSON: `pm_bot/llm/openrouter_test_artifacts/pmbot_openrouter_051_controlled_n5_batch_live_call/openrouter_batch_cost_report.v1.json`
- Cost report Markdown: `pm_bot/llm/openrouter_test_artifacts/pmbot_openrouter_051_controlled_n5_batch_live_call/openrouter_batch_cost_report.v1.md`
- Result JSON: `docs/PMBOT_OPENROUTER_051_RESULT.json`

## Future Next Step
- `PMBOT-OPENROUTER-052-N5-BATCH-BASELINE-QUALITY-AND-OPERATOR-SUMMARY`

052 is not approved or run inside 051.

## Validation
- `python -m compileall pm_bot`: passed
- `python -m pytest tests pm_bot\llm\tests -q`: 296 passed
- Focused OpenRouter tests: passed
- Operator surface 046 test: passed
- Workbench tests: passed
- JSON parse checks: 23 JSON files checked
- Result JSON checks: 050 and 051 passed
- Secret scan: 25 files scanned; no API key value or secret-bearing auth material found
