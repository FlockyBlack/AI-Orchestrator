# OpenRouter 051 N=5 Batch Quality Baseline

Artifact: `pm_bot/llm/openrouter_051_n5_batch_quality_baseline.v1.json`

This is a local artifact-quality baseline for the completed 051 N=5 batch. It does not approve trading, does not provide market decisions, and does not grant queue, runtime, or operator-execution authority.

## Aggregate Findings

- Attempted/completed/skipped markets: 5 / 5 / 0
- Completed market IDs: 569344, 569366, 569368, 569373, 573656
- Source OpenRouter calls in 051: 5
- OpenRouter calls in this 052 task: 0
- Polymarket API calls in this 052 task: 0
- Prompt/completion/total tokens: 20,768 / 9,119 / 29,887
- Total cost: 0.199089
- Average tokens per market: 5977.4
- Average cost per market: 0.0398178
- Accepted for operator review: 5
- Blocked: 0

## Estimate Versus Actual

- Estimated total tokens from 050: 31143.333335
- Actual total tokens from 051: 29,887
- Token delta actual minus estimate: -1256.333335
- Estimated total cost from 050: 0.20997
- Actual total cost from 051: 0.199089
- Cost delta actual minus estimate: -0.010881
- Max total cost allowed: 0.35

## Normalization Baseline

All five raw responses were Markdown-fenced. Strict raw JSON parsing failed for all five, then `fenced_json_normalization.v1` normalization produced parseable JSON for all five. Raw responses were preserved, and semantic repair was not allowed.

This is acceptable as a baseline for local artifact review, but future protocol work should keep trying to get clean raw JSON responses.

## Per-Market Status

| market_id | accepted | raw fenced | normalized | schema | gate | prompt tokens | completion tokens | total tokens | cost |
|---|---|---|---|---|---|---|---|---|---|
| 569344 | true | true | true | accepted | passed | 4,275 | 1,928 | 6,203 | 0.041745 |
| 569366 | true | true | true | accepted | passed | 4,327 | 1,617 | 5,944 | 0.037236 |
| 569368 | true | true | true | accepted | passed | 4,069 | 1,896 | 5,965 | 0.040647 |
| 569373 | true | true | true | accepted | passed | 4,035 | 2,044 | 6,079 | 0.042765 |
| 573656 | true | true | true | accepted | passed | 4,062 | 1,634 | 5,696 | 0.036696 |

## Operator-Usefulness Checks

Each completed market has populated evidence-gap/source-gap notes, contradiction checks, risk notes, and an operator checklist. The quality assessment is limited to artifact completeness, validation status, safety flags, and review structure.

| market_id | missing evidence count | source-gap count | contradiction checks | risk notes | checklist items |
|---|---|---|---|---|---|
| 569344 | 11 | 10 | 4 | 8 | 13 |
| 569366 | 10 | 9 | 3 | 6 | 10 |
| 569368 | 12 | 12 | 3 | 10 | 13 |
| 569373 | 13 | 12 | 4 | 10 | 15 |
| 573656 | 10 | 10 | 3 | 7 | 12 |

## Safety

No safety violations were found in the 051 result or the local 052 baseline analysis. The source artifacts record no Polymarket API calls, no wallet/order/trading activity, no runtime/dispatcher/background/browser/queue changes, no browser automation, no queue mutation, and no API key leak.

Acceptance means safe for operator review only. It is not trading approval, not a recommendation, not a market decision, and not queue/runtime authority.

## Future Readiness

Two possible future tasks are documented only:

- `PMBOT-OPENROUTER-053-PASSIVE-OPERATOR-SURFACE-051-N5-BATCH`: surface the 051 accepted N=5 responses as passive operator-review-only artifacts, with no queue/runtime/trading authority.
- `PMBOT-OPENROUTER-053B-CONTROLLED-N10-BATCH-READINESS-PROTOCOL`: protocol-only readiness for a future 10-market controlled batch, no live calls.

Neither future option is run or approved by this task.
