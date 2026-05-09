# PMBOT Paperlive Decision 004 Simulated Decision Replay Summary

Task: `PMBOT-PAPERLIVE-DECISION-004-SIMULATED-DECISION-REPLAY-SUMMARY-NO-RECOMMENDATIONS`

## What Changed

- Added a local simulated decision replay summary builder under `pm_bot/simulated_decisions/`.
- Added a deterministic replay summary request fixture under `pm_bot/tests/fixtures/simulated_decisions/`.
- Added static schema and sample replay summary artifacts under `pm_bot/simulated_decisions/`.
- Added focused tests for deterministic output, local reference enforcement, review status checks, static sample parity, CLI artifact writing, and blocked market-action fields.

## Replay Summary Contract

Replay summary requests use contract version `pmbot_simulated_decision_replay_summary_request.v1`.

Replay summary outputs use contract version `pmbot_simulated_decision_replay_summary.v1`.

The replay summary restates:

- source audit ledgers
- source packet rows
- record section rows
- local reference rows
- replay check rows
- closed local-only safety boundaries

Every emitted row remains `pending_operator_review` and `recorded_for_operator_review`.

## CLI

```powershell
python -m pm_bot.simulated_decisions.replay_summary `
  --request pm_bot\tests\fixtures\simulated_decisions\simulated_decision_replay_summary_request.valid.json `
  --output-summary <local-output-path>.json `
  --output-report <local-output-path>.md
```

The command writes:

- a JSON replay summary for local operator review
- a Markdown report summarizing the same local review surface

## Safety

- Local files and static fixtures only.
- No network calls.
- No LLM provider calls.
- No external market API calls.
- No authenticated service use.
- No wallet, order, trading endpoint, payment, transaction, or signing path.
- No runtime, dispatcher, scheduler, worker, browser, or app-server wiring.
- No market metrics, ranked outputs, or execution instructions.
- The replay summary and Markdown report are not execution approval and are not runtime input.
