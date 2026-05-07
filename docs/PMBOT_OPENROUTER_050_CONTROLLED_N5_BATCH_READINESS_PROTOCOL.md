# PMBOT-OPENROUTER-050 Controlled N5 Batch Readiness Protocol

Status: completed_pushed

This is a protocol-only readiness artifact. It does not approve, run, or simulate a future N=5 live OpenRouter batch. The proposed future live task is `PMBOT-OPENROUTER-051-CONTROLLED-N5-BATCH-LIVE-CALL`, and it requires separate approval before any live calls.

## Source State

- 046 completed the controlled 3-market OpenRouter batch for `569333`, `569334`, and `569343`.
- 046 performed 3 OpenRouter calls, 0 Polymarket API calls, and preserved raw responses.
- 047 created the baseline and operator summary with 18,686 total tokens and total cost 0.125982 USD.
- 047 recorded 3 accepted-for-operator-review responses, 0 blocked responses, and baseline suitability for future controlled expansion.
- 048 created passive operator-review surface artifacts only.
- 049 integrated the passive surface into the local workbench/export only.
- 048 and 049 preserved the no-authority boundary: no trading authority, no queue authority, no runtime authority, no dispatcher authority, and no wallet or order authority.

## Why N5 Is Not Run Here

050 is not a live batch task. It performs no OpenRouter calls and no Polymarket API calls. It does not inspect API credentials. It does not touch wallet, orders, trading, runtime wiring, dispatchers, background workers, browser automation, or queue state.

The future N=5 batch is not approved by 050. A future task must separately approve live calls, and that future task must cap live OpenRouter calls at 5 with no retries.

## Candidate Selection

Candidate selection used only existing local sanitized manual packet and prompt artifacts. No network, live data fetch, Polymarket API call, browser automation, or queue mutation was used.

Deterministic method:

1. Read `pm_bot/llm/manual_llm_packet_batch_manifest.v1.json`.
2. Use `exported_market_ids` order.
3. Exclude the 046 completed market IDs: `569333`, `569334`, `569343`.
4. Find the highest manifest index occupied by a 046 completed market ID.
5. Select the first 5 later market IDs that have both:
   - `pm_bot/llm/manual_packet_batch/{market_id}_packet.v1.json`
   - `pm_bot/llm/manual_packet_batch/{market_id}_prompt.v1.md`

Candidate selection status: ready

Proposed future N=5 market IDs:

- `569344`
- `569366`
- `569368`
- `569373`
- `573656`

If fewer than 5 eligible local packet/prompt pairs exist when the future task starts, the future N=5 live task must block before any live call.

## Future Model And Normalization

- Model: `anthropic/claude-sonnet-4.5`
- Adapter path: same path used by 046, `pm_bot/llm/run_openrouter_adapter.py`
- Required normalization policy: `fenced_json_normalization.v1`
- Raw response preservation required: true
- Semantic repair allowed: false

## Cost Guard

047 baseline source values:

- Average tokens per market: 6228.666667
- Average cost per market: 0.041994 USD

N=5 estimate:

- Estimated total tokens: 31143.333335
- Estimated total cost: 0.20997 USD

Future cap:

- Max total cost allowed: 0.35 USD
- Max OpenRouter calls allowed: 5
- Missing per-market usage or cost metadata must block the future task.
- Missing aggregate usage or cost report must block the future task.

## Future Fail-Fast Rules

The future live task must fail fast on the first blocking condition and must not retry automatically:

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

## Expected Future 051 Artifacts

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

## Future Validation Requirements

The future live task must run:

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

## Post-Success Handling

If the future N=5 live batch succeeds:

1. Create a baseline quality summary.
2. Create an operator summary.
3. Only then create a passive operator surface.
4. Only then integrate into the workbench.
5. Do not auto-promote into runtime.
6. Do not mutate queue state.

## Blocked Handling

If the future N=5 live batch blocks:

1. Preserve the blocked result and report.
2. Do not retry automatically.
3. Do not continue after fail-fast.
4. Create a diagnostic task before retry.
5. Keep the working tree clean if possible.

## Safety Statement

050 is local protocol work only. It performs 0 OpenRouter calls and 0 Polymarket API calls. It does not access API credential values, wallets, private keys, orders, trading paths, runtime wiring, dispatchers, background workers, browser automation, or queue state. Acceptance in any future artifact means only safe for operator review, not trading approval.

`PMBOT-OPENROUTER-051-CONTROLLED-N5-BATCH-LIVE-CALL` is not approved or run by 050.
