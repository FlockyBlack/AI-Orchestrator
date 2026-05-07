# PMBOT-OPENROUTER-049 Workbench Passive Surface Integration

## Summary

Integrated the PMBOT-OPENROUTER-048 passive OpenRouter batch surface into the local PMBOT workbench/export artifacts as read-only operator context.

The workbench now writes a deterministic pointer artifact and surfaces the same summary in:

- `pm_bot/workbench/openrouter_passive_surface_pointer.v1.json`
- `pm_bot/workbench/openrouter_passive_surface_pointer.v1.md`
- `pm_bot/workbench/operator_review_pack.v1.json`
- `pm_bot/workbench/operator_review_pack.v1.md`
- `pm_bot/workbench/operator_workbench_export_run.v1.json`
- `pm_bot/workbench/operator_workbench_export_run.v1.md`

The integration exposes source task ids, surfaced markets, model name, total calls, aggregate usage/cost, normalization summary, quality summary, safety flags, and repo-relative artifact pointers. It does not embed full model response text.

## Source Artifacts Used

- `docs/PMBOT_OPENROUTER_048_RESULT.json`
- `docs/PMBOT_OPENROUTER_048_PASSIVE_OPERATOR_SURFACE_046_BATCH.md`
- `pm_bot/llm/operator_openrouter_batch_surface_046.v1.json`
- `pm_bot/llm/operator_openrouter_batch_surface_046.v1.md`
- `docs/PMBOT_OPENROUTER_046_RESULT.json`
- `docs/PMBOT_OPENROUTER_047_RESULT.json`
- `pm_bot/llm/openrouter_046_small_batch_quality_baseline.v1.json`
- `pm_bot/llm/openrouter_046_small_batch_quality_baseline.v1.md`
- `pm_bot/llm/openrouter_046_small_batch_operator_summary.v1.md`

## Integrated Surface

- source batch task: `PMBOT-OPENROUTER-046`
- source baseline task: `PMBOT-OPENROUTER-047`
- source surface task: `PMBOT-OPENROUTER-048`
- surfaced markets: `569333`, `569334`, `569343`
- model: `anthropic/claude-sonnet-4.5`
- total calls in source batch: `3`
- aggregate usage: `12859` prompt tokens, `5827` completion tokens, `18686` total tokens
- aggregate cost: `0.125982` total, `0.041994` average per market
- accepted for operator review: `3`
- blocked: `0`

## Safety And Authority Boundary

This is a local-only workbench/export surfacing change.

- operator_review_only: true
- passive_context_only: true
- analysis_only: true
- manual_review_only: true
- no_trading_authority: true
- no_queue_authority: true
- no_runtime_authority: true
- no_dispatcher_authority: true
- no_wallet_or_order_authority: true
- acceptance_is_not_trading_approval: true
- openrouter_calls_performed: 0
- polymarket_api_calls_performed: 0
- network_calls: 0
- orders_created: 0
- runtime_wiring_added: false
- dispatcher_changes_added: false
- background_workers_added: false
- queue_items_created: false
- queue_state_mutated: false
- browser_automation_added: false
- wallet_or_order_access_added: false

No live calls, no Polymarket calls, no queue changes, no runtime changes, no dispatcher changes, no wallet/order access, and no market-action authority were added.

## Known Warnings

- All 3 source responses required fenced JSON normalization.
- No clean raw JSON responses observed in 046.

## Validation Summary

Passed:

- `python -m compileall pm_bot`
- `python -m pytest tests pm_bot\llm\tests -q`
- `python -m pytest pm_bot\llm\tests\test_operator_openrouter_batch_surface_046.py -q`
- `python -m pytest tests\test_openrouter_result_artifacts.py -q`
- `python -m pytest pm_bot\workbench\tests -q`
- `python -m pm_bot.workbench.run_operator_workbench_export`

Additional local checks:

- JSON parse checks covered 048 result, 049 result, source surface JSON, pointer JSON, workbench export JSON, and operator review pack JSON.
- Result checks covered required 048 and 049 status/safety fields.
- Secret scan over changed files and 049 artifacts passed.

## Future Readiness Note

The following are possible future tasks only. They were not run or approved by 049.

Option A:

- `PMBOT-OPENROUTER-050-CONTROLLED-N5-BATCH-READINESS-PROTOCOL`
- Purpose: protocol-only readiness for a future 5-market controlled batch, no live calls.

Option B:

- `PMBOT-OPENROUTER-050-OPERATOR-WORKBENCH-OPENROUTER-UX-REFINEMENT`
- Purpose: improve local presentation of passive OpenRouter review data in workbench artifacts, no live calls.
