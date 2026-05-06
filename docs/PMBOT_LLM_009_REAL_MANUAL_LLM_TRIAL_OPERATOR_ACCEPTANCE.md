# PMBOT-LLM-009 Real Manual LLM Trial Operator Acceptance

## What Operator Acceptance Means

PMBOT-LLM-009 adds a deterministic offline-only acceptance gate for the real local manual LLM market packet trial created by PMBOT-LLM-008.

Operator acceptance means the local PMBOT trial can be surfaced as accepted operator review context only after a human operator manually obtains an LLM response, saves that JSON locally, and labels it as `actual_operator_pasted_response`.

It does not mean the response is true, current, useful for trading, or suitable for any automated action.

## Why The Example Fixture Cannot Be Accepted

PMBOT-LLM-008 proved that the real local market packet validates, but it still used `pm_bot/llm/real_local_market_llm_trial_response_example.v1.json`.

That file is a fixture. It can pass schema validation, manual review validation, and the deterministic quality gate, but it is not evidence that an operator performed the real manual paste-in trial. PMBOT-LLM-009 therefore reports:

`pending_real_manual_response`

when the response source type is `example_fixture_response`.

## Response Source Types

`example_fixture_response` means the saved response is the deterministic fixture used for local tests and reproducible examples. It can validate, but it cannot be accepted as real operator acceptance.

`actual_operator_pasted_response` means a human operator manually pasted `pm_bot/llm/real_local_market_llm_trial_prompt.v1.md` into ChatGPT, Claude, or Gemini, requested strict JSON only, saved the returned JSON locally, and explicitly passed that saved file to the acceptance script.

The acceptance gate also rejects `actual_operator_pasted_response` if it points at the known example fixture response path.

## Acceptance Statuses

`accepted_for_operator_review` requires all of the following:

- `trial_packet_source_type == real_local_market_artifact`
- `used_example_packet_fallback == false`
- `response_source_type == actual_operator_pasted_response`
- packet validation accepted
- response validation accepted
- manual review accepted
- quality gate is `quality_passed` or `quality_passed_with_warnings`
- no forbidden content
- no unsafe certainty
- no probability/EV/edge/scoring/side/truth/trading content

`pending_real_manual_response` means the packet is verified real local market context and the response validates, but the response is still the example fixture source type.

`rejected` means a deterministic acceptance rule failed, such as non-real packet source, example packet fallback, response validation failure, manual review rejection, quality failure, forbidden content, unsafe certainty, unknown response source type, or an actual response label pointing at the example fixture path.

`blocked` means a required artifact is missing, malformed, or cannot be used to verify source selection.

## Required Manual Steps To Reach Accepted

1. Open `pm_bot/llm/real_local_market_llm_trial_prompt.v1.md`.
2. Paste manually into ChatGPT/Claude/Gemini.
3. Request strict JSON only.
4. Save the returned JSON to `pm_bot/llm/real_local_market_llm_trial_response_operator.v1.json`.
5. Rerun:

```powershell
python pm_bot\llm\evaluate_real_manual_llm_trial_operator_acceptance.py `
  --trial pm_bot\llm\real_local_market_llm_trial.v1.json `
  --packet pm_bot\llm\real_local_market_llm_trial_packet.v1.json `
  --prompt pm_bot\llm\real_local_market_llm_trial_prompt.v1.md `
  --response pm_bot\llm\real_local_market_llm_trial_response_operator.v1.json `
  --response-source-type actual_operator_pasted_response `
  --out-json pm_bot\llm\real_manual_llm_trial_operator_acceptance.v1.json `
  --out-md pm_bot\llm\real_manual_llm_trial_operator_acceptance.v1.md
```

6. Review the acceptance JSON and Markdown outputs.

## Why This Still Does Not Call An LLM API

The acceptance gate only reads and writes local files and calls existing local deterministic helpers:

- `pm_bot/llm/validate_llm_analysis_artifacts.py`
- `pm_bot/llm/validate_manual_llm_paste_in_review.py`
- `pm_bot/llm/evaluate_manual_llm_review_quality_gate.py`

It does not call an LLM API, browser, prompt automation layer, live market API, authenticated endpoint, wallet, credential store, dispatcher, runtime service, order path, or paper-order generator.

## Explicit Boundary

No API, no automation, no trading advice, no truth evaluation, no probability, no EV, no edge, no scoring, no side recommendation, no market decision, no trading execution, no real orders, no live trading, and no autonomous paper orders.

## Still Missing Before API Or Autonomous Trading

Before any LLM API integration, PMBOT still needs a separately approved runtime design, credential isolation, prompt/output audit logging, failure-mode handling, operator authorization, and tests proving that API responses cannot produce decisions or actions.

Before autonomous trading, PMBOT would need a separate strategy specification, risk model, compliance review, wallet/key controls, live-data validation, irreversible-action controls, and explicit approval for real-money execution. None of that is included here.

## Next Recommended Task

`PMBOT-LLM-010-ACTUAL-MANUAL-LLM-RESPONSE-TRIAL-RUN`
