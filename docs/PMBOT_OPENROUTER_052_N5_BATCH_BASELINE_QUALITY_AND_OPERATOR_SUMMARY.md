# PMBOT OpenRouter 052 N=5 Batch Baseline Quality And Operator Summary

Task: `PMBOT-OPENROUTER-052-N5-BATCH-BASELINE-QUALITY-AND-OPERATOR-SUMMARY`

Status: `completed_pushed`

## Summary

051 completed the controlled 5-market OpenRouter batch and produced complete local artifacts for markets 569344, 569366, 569368, 569373, 573656. This 052 task analyzed those artifacts only and created a deterministic local quality baseline plus a concise operator-readable summary.

No OpenRouter calls, Polymarket API calls, wallet/order/trading activity, runtime wiring, dispatcher changes, background workers, browser automation, queue mutation, or API key access were performed by this task.

## Artifacts Analyzed

- `docs/PMBOT_OPENROUTER_051_RESULT.json`
- `pm_bot/llm/openrouter_test_artifacts/pmbot_openrouter_051_controlled_n5_batch_live_call/openrouter_batch_summary.v1.json`
- `pm_bot/llm/openrouter_test_artifacts/pmbot_openrouter_051_controlled_n5_batch_live_call/openrouter_batch_cost_report.v1.json`
- `pm_bot/llm/openrouter_test_artifacts/pmbot_openrouter_051_controlled_n5_batch_live_call/openrouter_batch_cost_report.v1.md`
- Per-market raw/content/validation/summary JSON artifacts for 569344, 569366, 569368, 569373, 573656.

## Baseline Findings

- Attempted/completed/skipped markets: 5 / 5 / 0
- Completed market IDs: 569344, 569366, 569368, 569373, 573656
- Source OpenRouter calls in 051: 5
- OpenRouter calls in 052: 0
- Polymarket API calls in 052: 0
- Accepted for operator review: 5
- Blocked: 0
- Fenced responses: 5
- Normalized responses: 5
- Clean raw JSON responses: 0
- Safety violations found: none
- Secret scan concerns found: none
- Baseline judgment: suitable as a local baseline for future controlled engineering expansion.

The only quality warning is structural: all five raw responses were Markdown-fenced, so strict raw JSON parsing failed and `fenced_json_normalization.v1` was required. Normalized JSON parsing, schema validation, and the acceptance gate passed for all five markets. Raw responses were preserved, and semantic repair was not allowed.

## Usage And Cost

| market_id | prompt tokens | completion tokens | total tokens | cost |
|---|---|---|---|---|
| 569344 | 4,275 | 1,928 | 6,203 | 0.041745 |
| 569366 | 4,327 | 1,617 | 5,944 | 0.037236 |
| 569368 | 4,069 | 1,896 | 5,965 | 0.040647 |
| 569373 | 4,035 | 2,044 | 6,079 | 0.042765 |
| 573656 | 4,062 | 1,634 | 5,696 | 0.036696 |
| total | 20,768 | 9,119 | 29,887 | 0.199089 |

Average tokens per market: 5977.4. Average cost per market: 0.0398178.

## Estimate Versus Actual

- Estimated total tokens from 050: 31143.333335
- Actual total tokens from 051: 29,887
- Token delta actual minus estimate: -1256.333335
- Estimated total cost from 050: 0.20997
- Actual total cost from 051: 0.199089
- Cost delta actual minus estimate: -0.010881
- Max total cost allowed: 0.35
- Cost cap exceeded: false

## Operator Summary Location

- `pm_bot/llm/openrouter_051_n5_batch_operator_summary.v1.md`
- Quality baseline JSON: `pm_bot/llm/openrouter_051_n5_batch_quality_baseline.v1.json`
- Quality baseline Markdown: `pm_bot/llm/openrouter_051_n5_batch_quality_baseline.v1.md`

## Safety Confirmation

This task is analysis-only and local-only. Acceptance means safe for operator review only. It is not trading approval, not a recommendation, not a market decision, and not queue/runtime authority.

The 051 source result records clean safety fields: no Polymarket API calls, no wallet/order/trading activity, no runtime/dispatcher/background/browser/queue changes, no browser automation, no queue mutation, and no API key leak. This 052 task did not inspect, print, write, expose, or commit an API key.

## Limitations

- No live calls were made, and this report does not validate future model behavior.
- Full model responses are intentionally not repeated in this report.
- Quality assessment is limited to artifact completeness, parsing, validation, safety flags, usage/cost accounting, and operator-review structure.
- The batch remains manual-review-only; nothing here creates runtime authority or queue authority.

## Future Readiness

Two possible future tasks are documented but not run or approved:

- Option A: `PMBOT-OPENROUTER-053-PASSIVE-OPERATOR-SURFACE-051-N5-BATCH`
  Purpose: surface the 051 accepted N=5 responses as passive operator-review-only artifacts, with no queue/runtime/trading authority.
- Option B: `PMBOT-OPENROUTER-053B-CONTROLLED-N10-BATCH-READINESS-PROTOCOL`
  Purpose: protocol-only readiness for a future 10-market controlled batch, no live calls.

Neither future option is performed by 052.
