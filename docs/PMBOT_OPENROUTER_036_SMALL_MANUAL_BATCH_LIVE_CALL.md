# PMBOT OpenRouter 036 Small Manual Batch Live Call

- task_id: PMBOT-OPENROUTER-036-SMALL-MANUAL-BATCH-LIVE-CALL
- status: blocked_validation_failed
- session_id: pmbot_openrouter_036_small_manual_batch_live_call
- model: anthropic/claude-sonnet-4.5
- approved_market_ids: 569333, 569334, 569343
- attempted_market_ids: 569333
- completed_market_ids: none
- skipped_market_ids: 569334, 569343
- total_openrouter_calls_performed: 1
- no_retries: true
- fail_fast_triggered: true
- fail_fast_reason: raw_response_validation_failed:569333

## Boundary

This was a controlled OpenRouter-only live test using local sanitized manual packet/prompt artifacts. It was not trading, market decisioning, runtime integration, queue processing, browser automation, wallet access, order handling, or Polymarket API work.

Acceptance means safe for operator review only. It is not trading approval.

## Outcome

The first OpenRouter response for market_id 569333 was saved, but strict raw JSON validation rejected it because the raw assistant content was Markdown-fenced. Local JSON fence repair was intentionally not enabled for this task, so markets 569334 and 569343 were skipped without calls.

No prohibited trading content, probability/EV/edge/confidence/side-selection content, or buy/sell/hold/enter/exit language was detected by the recorded validation metadata.

## Artifacts

- batch_summary: pm_bot/llm/openrouter_test_artifacts/pmbot_openrouter_036_small_manual_batch_live_call/openrouter_batch_summary.v1.json
- cost_report_json: pm_bot/llm/openrouter_test_artifacts/pmbot_openrouter_036_small_manual_batch_live_call/openrouter_batch_cost_report.v1.json
- cost_report_md: pm_bot/llm/openrouter_test_artifacts/pmbot_openrouter_036_small_manual_batch_live_call/openrouter_batch_cost_report.v1.md
- 569333_raw: pm_bot/llm/openrouter_test_artifacts/pmbot_openrouter_036_small_manual_batch_live_call/openrouter_sonnet_569333_raw.json
- 569333_content: pm_bot/llm/openrouter_test_artifacts/pmbot_openrouter_036_small_manual_batch_live_call/openrouter_sonnet_569333_content.json
- 569333_validation: pm_bot/llm/openrouter_test_artifacts/pmbot_openrouter_036_small_manual_batch_live_call/openrouter_sonnet_569333_validation.json
- 569333_summary: pm_bot/llm/openrouter_test_artifacts/pmbot_openrouter_036_small_manual_batch_live_call/openrouter_sonnet_569333_summary.json

## Cost

- aggregate_prompt_tokens: 4069
- aggregate_completion_tokens: 1965
- aggregate_total_tokens: 6034
- aggregate_cost: 0.041682

## Validation

- python -m compileall pm_bot: passed
- python -m pytest tests pm_bot\llm\tests -q: passed (265 passed in 5.38s)
- JSON parse checks for all newly created JSON artifacts: passed (7 JSON artifacts parsed)
- Result JSON checks for PMBOT_OPENROUTER_036_RESULT.json and batch summary: passed
- Secret scan over generated 036 docs and OpenRouter artifacts: passed
- Focused OpenRouter/LLM validator coverage: passed (covered by requested pytest set)

## Safety

- api_key_value_printed: false
- api_key_value_written: false
- api_key_leaked: false
- no_polymarket_api_calls: true
- no_wallet_orders_trading: true
- no_runtime_dispatcher_background_browser_queue_changes: true
- no_queue_mutation: true
- no_browser_automation: true
- operator_review_only: true
- acceptance_is_not_trading_approval: true

## Git

- commit_created: false
- pushed: false
- reason: blocked_validation_failed; artifacts remain local for review and were not pushed.
