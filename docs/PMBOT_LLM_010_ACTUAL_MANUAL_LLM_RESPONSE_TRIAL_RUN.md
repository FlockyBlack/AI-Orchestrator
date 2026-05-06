# PMBOT-LLM-010 Actual Manual LLM Response Trial Run

## Scope

This task adds a deterministic offline-only trial wrapper for an actual operator-pasted LLM response on the real local PMBOT market packet trial.

The real local trial is:

- Trial: `pm_bot/llm/real_local_market_llm_trial.v1.json`
- Packet: `pm_bot/llm/real_local_market_llm_trial_packet.v1.json`
- Prompt: `pm_bot/llm/real_local_market_llm_trial_prompt.v1.md`
- Expected operator response: `pm_bot/llm/real_local_market_llm_trial_response_operator.v1.json`
- Market ID: `824952`
- Source artifact: `pm_bot/research/selected_ingest_final_dossier_drafts.v1.json`

## What This Trial Means

An actual manual response trial means the operator manually opens the exported prompt, pastes it into a consumer LLM UI, requests strict JSON only, and saves the returned JSON into the expected local response path.

The wrapper then reads that saved local JSON and runs the existing offline gates:

- PMBOT-LLM-001 response validator
- PMBOT-LLM-003 manual review builder
- PMBOT-LLM-005 quality gate
- PMBOT-LLM-009 operator acceptance gate with `actual_operator_pasted_response`

The wrapper does not call an LLM, browse, automate a prompt, or connect to trading/runtime systems.

## Why Codex Cannot Generate The Actual Response

The acceptance contract distinguishes an example fixture from an actual operator-pasted response. If Codex generated or copied the actual response itself, the trial would falsely claim that a real operator-pasted response exists.

For that reason, `pm_bot/llm/real_local_market_llm_trial_response_operator.v1.json` is not created by this task. A missing operator response is a valid pending state, not a task failure.

## Missing Response Behavior

When `pm_bot/llm/real_local_market_llm_trial_response_operator.v1.json` is missing, the wrapper exports:

- `run_status`: `pending_operator_input`
- `acceptance_status`: `pending_real_manual_response`
- `next_safe_operator_action`: `save_actual_operator_pasted_response`

It does not create a fake response. It does not treat `real_local_market_llm_trial_response_example.v1.json` or the placeholder response as actual operator input.

## Manual Operator Steps

1. Open `pm_bot/llm/real_local_market_llm_trial_prompt.v1.md`.
2. Paste into ChatGPT/Claude/Gemini manually.
3. Request strict JSON only.
4. Save the returned JSON to `pm_bot/llm/real_local_market_llm_trial_response_operator.v1.json`.
5. Rerun:

```powershell
python pm_bot\llm\run_actual_manual_llm_response_trial.py `
  --trial pm_bot\llm\real_local_market_llm_trial.v1.json `
  --packet pm_bot\llm\real_local_market_llm_trial_packet.v1.json `
  --prompt pm_bot\llm\real_local_market_llm_trial_prompt.v1.md `
  --operator-response pm_bot\llm\real_local_market_llm_trial_response_operator.v1.json `
  --out-json pm_bot\llm\actual_manual_llm_response_trial.v1.json `
  --out-md pm_bot\llm\actual_manual_llm_response_trial.v1.md
```

## Acceptance Determination

If the operator response exists, the wrapper accepts it only when all of these are true:

- The PMBOT-LLM-008 trial proves `trial_packet_source_type == real_local_market_artifact`.
- `used_example_packet_fallback` is `false`.
- The response source type is evaluated as `actual_operator_pasted_response`.
- Packet validation passes.
- Response validation passes.
- Manual review accepts the response.
- Quality gate is `quality_passed` or `quality_passed_with_warnings`.
- No forbidden content or unsafe certainty is detected.

Accepted output uses `run_status: actual_response_accepted`. Failed content uses `actual_response_rejected`; malformed or unverifiable local artifacts use `actual_response_blocked`.

## Safety Boundary

No API, no automation, no trading advice, no truth/probability/EV/edge/side/trading execution.

The trial does not add:

- Live API calls
- LLM API calls
- Browser automation
- Prompt automation
- Runtime integration
- Wallet, key, credential, or signing access
- Real orders or live trading
- Autonomous paper orders
- Probability, EV, edge, scoring, side recommendation, truth evaluation, or market decision logic

## Still Missing Before API Or Autonomous Trading

Before any API or autonomous trading work could be considered, separate explicit approval and additional tasks would be required for architecture, safety review, credentials handling, execution controls, monitoring, auditability, and rollback. This task intentionally does none of that.

## Next Recommended Task

`PMBOT-LLM-011-ACTUAL-MANUAL-LLM-RESPONSE-VALIDATION-AND-WORKBENCH-SURFACE`
