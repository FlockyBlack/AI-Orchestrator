# OpenRouter 046 Small Batch Quality Baseline

Artifact: `pm_bot/llm/openrouter_046_small_batch_quality_baseline.v1.json`

This is a local artifact-quality baseline for the completed 046 small batch. It does not approve trading, does not provide market decisions, and does not grant queue, runtime, or operator-execution authority.

## Aggregate Findings

- Attempted/completed/skipped markets: 3 / 3 / 0
- Completed market IDs: 569333, 569334, 569343
- Source OpenRouter calls in 046: 3
- OpenRouter calls in this 047 task: 0
- Polymarket API calls in this 047 task: 0
- Prompt/completion/total tokens: 12,859 / 5,827 / 18,686
- Total cost: 0.125982
- Average tokens per market: 6,228.666667
- Average cost per market: 0.041994
- Accepted for operator review: 3
- Blocked: 0

## Normalization Baseline

All three raw responses were Markdown-fenced. Strict raw JSON parsing failed for all three, then `fenced_json_normalization.v1` normalization produced parseable JSON for all three. Raw responses were preserved, and semantic repair was not allowed.

This is acceptable as a baseline for local artifact review, but future protocol work should keep trying to get clean raw JSON responses.

## Per-Market Status

| market_id | accepted | raw fenced | normalized | schema | gate | prompt tokens | completion tokens | total tokens | cost |
|---|---:|---:|---:|---|---|---:|---:|---:|---:|
| 569333 | true | true | true | accepted | passed | 4,241 | 1,859 | 6,100 | 0.040608 |
| 569334 | true | true | true | accepted | passed | 4,292 | 1,883 | 6,175 | 0.041121 |
| 569343 | true | true | true | accepted | passed | 4,326 | 2,085 | 6,411 | 0.044253 |

## Operator-Usefulness Checks

Each completed market has populated evidence-gap/source-gap notes, contradiction checks, risk notes, and an operator checklist. The quality assessment is limited to artifact completeness, validation status, safety flags, and review structure.

| market_id | missing evidence count | source-gap count | contradiction checks | risk notes | checklist items |
|---|---:|---:|---:|---:|---:|
| 569333 | 12 | 10 | 4 | 7 | 12 |
| 569334 | 10 | 10 | 3 | 8 | 12 |
| 569343 | 12 | 10 | 4 | 10 | 15 |

## Safety

No safety violations were found in the 046 result or the local 047 baseline analysis. The source artifacts record no Polymarket API calls, no wallet/order/trading activity, no runtime/dispatcher/background/browser/queue changes, no browser automation, no queue mutation, and no API key leak.

Acceptance means safe for operator review only. It is not trading approval, not a recommendation, not a market decision, and not queue/runtime authority.

## Future Readiness

Two possible future tasks are documented only:

- `PMBOT-OPENROUTER-048-PASSIVE-OPERATOR-SURFACE-046-BATCH`: surface the 046 accepted responses as passive operator-review-only artifacts or dashboard state, with no queue, runtime, or trading authority.
- `PMBOT-OPENROUTER-048B-CONTROLLED-N5-BATCH-READINESS-PROTOCOL`: protocol-only readiness for a future 5-market controlled batch, with no live calls.

Neither future option is run or approved by this task.
