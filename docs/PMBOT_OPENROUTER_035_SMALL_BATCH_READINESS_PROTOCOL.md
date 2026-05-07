# PMBOT OpenRouter 035 Small Batch Readiness Protocol

- task_id: PMBOT-OPENROUTER-035-SMALL-BATCH-READINESS-PROTOCOL
- future_task_id: PMBOT-OPENROUTER-036-SMALL-MANUAL-BATCH-LIVE-CALL
- status: protocol_only
- model: anthropic/claude-sonnet-4.5
- proposed_batch_size: 3
- max_openrouter_calls: 3 total
- retries_allowed: false
- api_key_needed_for_035: false

This task does not approve or perform batch live calls.

Any PMBOT-OPENROUTER-036 batch live test requires separate operator approval.

## Current Baseline

The current readiness baseline comes from the completed controlled one-market OpenRouter records and the passive two-call stability report:

- 028 result artifact: `docs/PMBOT_OPENROUTER_028_RESULT.json`
- 033 result artifact: `docs/PMBOT_OPENROUTER_033_RESULT.json`
- 034 result artifact: `docs/PMBOT_OPENROUTER_034_RESULT.json`
- 563650 operator surface: `pm_bot/llm/operator_live_review_surface_563650.v1.json`
- 569332 operator surface: `pm_bot/llm/operator_live_review_surface_569332.v1.json`

Validated baseline facts:

- 028 status is `completed_live_call_passed`.
- 033 status is `completed_live_call_passed`.
- 034 two-call stability artifacts are present in the pushed repository baseline at `9101d8f8117350d56156ee2f0ca3f187cf54f456`; the saved 034 JSON itself still records its authoring-time status as `completed_local_checks_passed_pending_commit`.
- Both completed live calls used `anthropic/claude-sonnet-4.5`.
- Both completed live calls recorded exactly one OpenRouter call.
- Both completed live calls were `accepted_for_operator_review`.
- Both completed live calls reported `prohibited_trading_content_detected: false`.
- Both completed live calls reported `api_key_leaked: false`.
- 034 explicitly preserved `batch_live_calls_approved: false`.

## Proposed 036 Candidate Set

Use exactly these three manually selected market ids for a future 036 batch, because their restored manual packet and prompt artifacts are present and neither market has already been used for a live call:

- `569333`
- `569334`
- `569343`

If any of those artifacts are missing at 036 precheck time, replace only the missing candidate slots with the next available ids, in order:

- `569344`
- `569366`
- `569368`
- `569373`
- `573656`
- `597964`
- `598936`
- `691547`
- `692258`

The already tested markets `563650` and `569332` must remain excluded from the 036 batch.

## 036 Execution Boundary

A future 036 task may only proceed after separate operator approval for that exact task and exact 3-market candidate set.

Required execution shape for 036:

- One model only: `anthropic/claude-sonnet-4.5`.
- Exactly 3 manually selected market ids.
- Maximum 3 total OpenRouter calls.
- No retries unless separately approved in a later task.
- One prompt and one response per market.
- Each accepted response remains operator-review-only.
- No automatic operator surface unless a separate surfacing step is included after validation.
- No runtime queue import.
- No dispatcher, background worker, scheduler, or runtime integration.
- No probability, EV, edge, confidence, scoring, or side-selection output.
- No market-action recommendations.
- No trading authority.

## Fail-Fast Rules

036 must stop the batch immediately if any of these occur:

- Any response fails raw validation.
- Any response fails the acceptance gate.
- Any prohibited trading content is detected.
- Any usage or cost artifact is missing.
- Any API key leak is detected.

After a stop condition, no remaining market prompts may be sent unless a separate operator-approved recovery task authorizes a new attempt.

## Cost Guard

036 must follow the existing OpenRouter cost and usage conventions:

- 010 established a conservative manual network adapter cost policy: a cost cap must be supplied or defaulted conservatively, missing usage or cost fails closed, and automatic retry loops are not allowed.
- 032 and 033 require cost and usage metadata to be recorded for manual live calls.
- 028 and 033 recorded per-call prompt tokens, completion tokens, total tokens, returned model, provider, and cost in the harness summary.

Conservative 036 budget cap:

- Aggregate batch cap: `0.15` USD total across all 3 calls.
- Per-market planning cap: `0.05` USD per call.
- If the underlying command supports an explicit cost cap, 036 must supply caps no higher than these values.
- If aggregate spend cannot be enforced automatically, the operator must review each per-market cost artifact before continuing to the next market.
- Missing or malformed usage or cost metadata is a fail-fast stop condition.

Required cost and usage artifacts:

- Per-market usage metadata for each attempted market.
- Aggregate batch usage summary.
- Operator-visible cost report.
- No spend automation is introduced by this protocol.

## Artifact Plan For 036

Do not create these artifacts in 035. These are reserved paths for a future approved 036 task:

- Per-market raw response:
  - `pm_bot/llm/openrouter_test_artifacts/pmbot_openrouter_036_small_manual_batch_live_call/569333/openrouter_sonnet_569333_raw.json`
  - `pm_bot/llm/openrouter_test_artifacts/pmbot_openrouter_036_small_manual_batch_live_call/569334/openrouter_sonnet_569334_raw.json`
  - `pm_bot/llm/openrouter_test_artifacts/pmbot_openrouter_036_small_manual_batch_live_call/569343/openrouter_sonnet_569343_raw.json`
- Per-market content:
  - `pm_bot/llm/openrouter_test_artifacts/pmbot_openrouter_036_small_manual_batch_live_call/569333/openrouter_sonnet_569333_content.json`
  - `pm_bot/llm/openrouter_test_artifacts/pmbot_openrouter_036_small_manual_batch_live_call/569334/openrouter_sonnet_569334_content.json`
  - `pm_bot/llm/openrouter_test_artifacts/pmbot_openrouter_036_small_manual_batch_live_call/569343/openrouter_sonnet_569343_content.json`
- Per-market validation:
  - `pm_bot/llm/openrouter_test_artifacts/pmbot_openrouter_036_small_manual_batch_live_call/569333/openrouter_sonnet_569333_validation.json`
  - `pm_bot/llm/openrouter_test_artifacts/pmbot_openrouter_036_small_manual_batch_live_call/569334/openrouter_sonnet_569334_validation.json`
  - `pm_bot/llm/openrouter_test_artifacts/pmbot_openrouter_036_small_manual_batch_live_call/569343/openrouter_sonnet_569343_validation.json`
- Per-market summary:
  - `pm_bot/llm/openrouter_test_artifacts/pmbot_openrouter_036_small_manual_batch_live_call/569333/openrouter_test_summary_569333.json`
  - `pm_bot/llm/openrouter_test_artifacts/pmbot_openrouter_036_small_manual_batch_live_call/569334/openrouter_test_summary_569334.json`
  - `pm_bot/llm/openrouter_test_artifacts/pmbot_openrouter_036_small_manual_batch_live_call/569343/openrouter_test_summary_569343.json`
- Batch aggregate summary:
  - `pm_bot/llm/openrouter_test_artifacts/pmbot_openrouter_036_small_manual_batch_live_call/batch_aggregate_summary.v1.json`
- Batch acceptance report:
  - `pm_bot/llm/openrouter_test_artifacts/pmbot_openrouter_036_small_manual_batch_live_call/batch_acceptance_report.v1.json`
- Batch cost report:
  - `pm_bot/llm/openrouter_test_artifacts/pmbot_openrouter_036_small_manual_batch_live_call/batch_cost_report.v1.json`

All 036 artifacts must remain local and review-only. Accepted content may be surfaced only by a separate explicitly included post-validation surfacing step.

## Safety Boundary Checklist

- No OpenRouter calls in 035.
- No Polymarket API calls.
- No wallet or private-key access.
- No orders.
- No trading.
- No runtime wiring.
- No dispatcher changes.
- No background workers.
- No browser automation.
- No runtime queue mutation.
- No probability, EV, edge, confidence, scoring, or side selection.
- No buy, sell, hold, enter, or exit recommendation.
- No `OPENROUTER_API_KEY` read, print, log, disk write, or commit.
- No API key is needed for 035.

## Go/No-Go Checklist For Future 036

036 may proceed only if every item below is true at the start of that future task:

- Separate operator approval explicitly names `PMBOT-OPENROUTER-036-SMALL-MANUAL-BATCH-LIVE-CALL`.
- The approved candidate set is exactly 3 market ids.
- The first candidate set remains `569333`, `569334`, and `569343`, or documented replacements are chosen only because artifacts are missing.
- All selected packet and prompt artifacts exist locally before the first call.
- Git precheck state is captured before any 036 changes.
- The selected model is exactly `anthropic/claude-sonnet-4.5`.
- Maximum OpenRouter calls is exactly 3.
- Retries are disabled.
- The aggregate budget cap is documented before the first call.
- Per-market usage and cost artifacts are required.
- Aggregate usage and cost reporting is required.
- Raw validation and acceptance gates are configured before the first call.
- Fail-fast stop rules are acknowledged before the first call.
- No runtime, dispatcher, queue, scheduler, background, wallet, order, or trading authority is introduced.

If any item is false, 036 is no-go until a separate operator-approved readiness task resolves the gap.
