# PMBOT-LLM-005 Manual LLM Review Quality Gate

Task: PMBOT-LLM-005-MANUAL-LLM-REVIEW-QUALITY-GATE

## Summary

This task adds a standalone deterministic offline quality gate for manual LLM paste-in review responses.

The gate reads a local LLM analysis packet, a local manually saved response JSON, and optionally the PMBOT-LLM-003 manual review artifact. It first runs the existing PMBOT-LLM-001 validator. If that base validator rejects the packet or response, the quality gate also fails.

After base validation passes, the gate checks whether the response is useful enough for an operator:

- required response sections are present
- required sections are non-empty
- minimum useful item counts are met
- generic placeholder text is rejected or warned
- uncertainties are explicitly marked
- missing evidence is recorded
- risk notes are present
- operator checklist actions are present
- citation/source gap notes are present
- unsafe certainty language is rejected
- safety acknowledgement fields are present and true
- forbidden fields and language from PMBOT-LLM-001 remain rejected

The canonical CLI is:

```powershell
python pm_bot\llm\evaluate_manual_llm_review_quality_gate.py `
  --packet pm_bot\llm\example_llm_analysis_packet.v1.json `
  --response pm_bot\llm\manual_llm_paste_in_response_example_valid.v1.json `
  --manual-review pm_bot\llm\manual_llm_paste_in_review.v1.json `
  --out-json pm_bot\llm\manual_llm_review_quality_gate.v1.json `
  --out-md pm_bot\llm\manual_llm_review_quality_gate.v1.md
```

## What It Does Not Do

This gate does not call an LLM API, browser, network service, exchange API, wallet, credential store, dispatcher, runtime service, or order path.

It does not generate prompts, automate prompt submission, fetch live market data, create paper orders, create real orders, route actions, or make market decisions.

It does not evaluate truth, probability, EV, edge, side, or trade execution.

## Why It Is Deterministic And Offline

All inputs are local JSON or Markdown artifacts. The evaluator uses only deterministic string, schema, and count checks over those local artifacts. It uses a deterministic generated marker instead of wall-clock timestamps for fixture stability.

The gate does not attempt to verify whether a market summary is factually correct. Truth review remains an operator/source-artifact task.

## Difference From PMBOT-LLM-001

PMBOT-LLM-001 validates the packet and response contract. It enforces schema shape, forbidden fields, forbidden language, certainty boundaries, and local-only safety constraints.

PMBOT-LLM-005 uses PMBOT-LLM-001 as its required first step, then adds operator-usefulness checks. A response can pass PMBOT-LLM-001 but still fail PMBOT-LLM-005 if it is too generic, too sparse, placeholder-only, missing practical checklist items, missing source-gap notes, or making unsafe certainty claims not covered by the base validator.

## Difference From PMBOT-LLM-003

PMBOT-LLM-003 creates a manual paste-in review artifact showing whether a local packet and response passed the PMBOT-LLM-001 validator.

PMBOT-LLM-005 evaluates the quality of that same manually saved response as operator context. It may optionally read the PMBOT-LLM-003 review artifact, but it does not depend on runtime integration and does not change the PMBOT-LLM-003 artifact format.

## Status Meanings

- `quality_passed`: PMBOT-LLM-001 passed, all required quality checks passed, and no material warnings were found.
- `quality_passed_with_warnings`: PMBOT-LLM-001 passed and no forbidden content was found, but non-critical quality warnings need operator review.
- `quality_failed`: PMBOT-LLM-001 failed, forbidden content was found, required sections are missing or empty, unsafe certainty language appears, or the response is too low-quality to accept as operator context.

## Boundary

This is a deterministic offline quality gate. It does not evaluate truth, probability, EV, edge, side, or trade execution.

The output is quality-control context only. `quality_counts` is not market scoring and must not be used for strategy, ranking, side selection, execution, paper order creation, or live trading.

## Next Recommended Task

PMBOT-LLM-006-MANUAL-LLM-QUALITY-GATE-WORKBENCH-SURFACE
