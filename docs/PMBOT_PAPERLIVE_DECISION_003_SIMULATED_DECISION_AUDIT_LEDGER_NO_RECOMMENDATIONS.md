# PMBOT Paperlive Decision 003 Simulated Decision Audit Ledger

Task: `PMBOT-PAPERLIVE-DECISION-003-SIMULATED-DECISION-AUDIT-LEDGER-NO-RECOMMENDATIONS`

## What Changed

- Added a local simulated decision audit ledger builder under `pm_bot/simulated_decisions/`.
- Added a deterministic request fixture under `pm_bot/tests/fixtures/simulated_decisions/`.
- Added static schema and sample ledger artifacts under `pm_bot/simulated_decisions/`.
- Added focused tests for deterministic output, local reference enforcement, review status checks, static sample parity, CLI artifact writing, and blocked market-action fields.

## Ledger Contract

Audit requests use contract version `pmbot_simulated_decision_audit_ledger_request.v1`.

Ledger outputs use contract version `pmbot_simulated_decision_audit_ledger.v1`.

The ledger inventories:

- source simulated decision packets
- packet contract and count review rows
- record section rows
- local reference rows
- audit requirement rows
- closed local-only safety boundaries

Every emitted row remains `pending_operator_review` and `recorded_for_operator_review`.

## CLI

```powershell
python -m pm_bot.simulated_decisions.audit_ledger `
  --request pm_bot\tests\fixtures\simulated_decisions\simulated_decision_audit_ledger_request.valid.json `
  --output-ledger <local-output-path>.json `
  --output-report <local-output-path>.md
```

The command writes:

- a JSON audit ledger for local operator review
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
- The ledger and Markdown report are not execution approval and are not runtime input.
