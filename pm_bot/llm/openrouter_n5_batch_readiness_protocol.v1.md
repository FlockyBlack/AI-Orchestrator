# OpenRouter N5 Batch Readiness Protocol v1

Protocol version: `openrouter_n5_batch_readiness_protocol.v1`

This artifact defines readiness criteria for a future controlled N=5 OpenRouter batch. It is protocol-only and does not approve live calls. The future live task ID is `PMBOT-OPENROUTER-051-CONTROLLED-N5-BATCH-LIVE-CALL`.

## Approval Boundary

- 050 approves no live calls.
- The future task must separately approve live calls.
- Future maximum OpenRouter calls: 5.
- Retries: none.
- Fail-fast: required on the first blocking condition.
- Acceptance means safe for operator review only.

## Candidate Markets

Candidates are selected only from existing local sanitized manual packet/prompt artifacts.

Selection method:

1. Use `pm_bot/llm/manual_llm_packet_batch_manifest.v1.json`.
2. Use `exported_market_ids` manifest order.
3. Exclude the 046 completed market IDs unless a future task explicitly changes the protocol to test repeatability.
4. Select the first five eligible IDs after the highest 046 completed manifest index.
5. Require both local packet and prompt artifacts for every selected ID.

Candidate selection status: ready

Proposed future N=5 market IDs:

- `569344`
- `569366`
- `569368`
- `569373`
- `573656`

If fewer than five eligible local packet/prompt pairs are available, the future live task must block before any live call.

## Model, Adapter, And Response Handling

- Model: `anthropic/claude-sonnet-4.5`
- Adapter: `pm_bot/llm/run_openrouter_adapter.py`
- Normalization policy: `fenced_json_normalization.v1`
- Raw responses must be preserved.
- Semantic repair is not allowed.

## Cost Guard

Source estimates from 047:

- Average tokens per market: 6228.666667
- Average cost per market: 0.041994 USD

N=5 estimate:

- Estimated total tokens: 31143.333335
- Estimated total cost: 0.20997 USD

Future cap:

- Max total cost allowed: 0.35 USD
- Max OpenRouter calls allowed: 5
- Missing per-market usage or cost metadata blocks the future task.
- Missing aggregate usage or cost report blocks the future task.

## Fail-Fast Conditions

- Missing local packet or prompt artifact.
- Configured OpenRouter credential absent from process environment when checked by boolean presence only.
- Any OpenRouter request failure.
- Any malformed raw response.
- Response is not clean JSON and is not normalizable under `fenced_json_normalization.v1`.
- Normalization policy violation.
- Raw or normalized validator failure.
- Schema validation failure.
- Acceptance gate failure.
- Prohibited content detected.
- Forbidden phrase detected.
- Probability, EV, edge, confidence, or side selection content detected.
- Buy, sell, hold, enter, or exit recommendation language detected.
- Missing per-market usage or cost artifact.
- Missing aggregate usage or cost artifact.
- Any API key leak signal.
- Any runtime, dispatcher, background, browser, wallet, orders, trading, or queue mutation.

## Expected Future Artifacts

Future session directory:

`pm_bot/llm/openrouter_test_artifacts/pmbot_openrouter_051_controlled_n5_batch_live_call/`

Per market:

- `openrouter_sonnet_{market_id}_raw.json`
- `openrouter_sonnet_{market_id}_content.json`
- `openrouter_sonnet_{market_id}_validation.json`
- `openrouter_sonnet_{market_id}_summary.json`

Aggregate:

- `openrouter_batch_summary.v1.json`
- `openrouter_batch_cost_report.v1.json`
- `openrouter_batch_cost_report.v1.md`

## Required Future Validation

- `python -m compileall pm_bot`
- `python -m pytest tests pm_bot\llm\tests -q`
- `python -m pytest tests\test_openrouter_prompt_test.py -q`
- `python -m pytest tests\test_openrouter_result_artifacts.py -q`
- `python -m pytest tests\test_openrouter_fenced_json_normalization.py -q`
- `python -m pytest pm_bot\llm\tests\test_operator_openrouter_batch_surface_046.py -q`
- `python -m pytest pm_bot\workbench\tests -q`
- JSON parse checks for all new JSON artifacts
- Result JSON checks
- Secret scan over generated artifacts

## Future Outcomes

If the future N=5 live batch succeeds, create the baseline quality summary and operator summary first, then create the passive operator surface, then integrate into the workbench. Do not auto-promote into runtime and do not mutate queue state.

If the future N=5 live batch blocks, preserve the blocked result/report, do not retry automatically, do not continue after fail-fast, create a diagnostic task before retry, and keep the working tree clean if possible.

## Safety Boundary

This protocol has no trading authority, queue authority, runtime authority, dispatcher authority, browser automation authority, wallet authority, or order authority. It performs 0 OpenRouter calls and 0 Polymarket API calls. It does not access credential values. It is for operator-review readiness only.
