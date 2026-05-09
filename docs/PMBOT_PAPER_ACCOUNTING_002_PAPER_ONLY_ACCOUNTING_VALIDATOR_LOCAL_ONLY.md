# PMBOT Paper Accounting 002 Paper-Only Accounting Validator

Task: `PMBOT-PAPER-ACCOUNTING-002-PAPER-ONLY-ACCOUNTING-VALIDATOR-LOCAL-ONLY`

## What Changed

- Added a local paper accounting validator in `pm_bot/paper_accounting/paper_accounting_validator.py`.
- Added deterministic validation samples under `pm_bot/paper_accounting/samples/`.
- Added focused tests for deterministic output, CLI writing, stricter record checks, validation artifact drift, local path enforcement, and blocked scoring/action fields.

## Validation Contract

Validation artifacts use contract version `pmbot_paper_accounting_validation.v1`.

The validator consumes a local paper accounting ledger artifact and verifies:

- the ledger artifact contract still validates
- each accounting entry has the required descriptive fields
- each entry ID is unique
- each entry timestamp is an ISO-8601 UTC timestamp ending in `Z`
- each quantity delta uses canonical two-decimal formatting
- each local reference stays under the paper accounting fixture/static sample boundary
- each entry remains in `pending_operator_review`
- each source artifact reference is present in the ledger source inventory

The output contains one `record_validation_rows` entry per accounting entry and a deterministic summary count block.

## CLI

```powershell
python -m pm_bot.paper_accounting.paper_accounting_validator `
  --ledger pm_bot\paper_accounting\samples\paper_accounting_ledger.fixture.json `
  --output-validation <local-output-path>.json `
  --output-report <local-output-path>.md
```

The command writes:

- a JSON validation artifact with contract version `pmbot_paper_accounting_validation.v1`
- a Markdown operator report summarizing the same local validation surface

## Operator Review Boundary

The validator is a descriptive local review artifact. It checks local paper accounting records and reports deterministic pass/fail validation status for operator review.

It does not rank markets, approve execution, open endpoints, or modify accounts. Operators must review accounting disputes outside this validation artifact.

## Safety

- Local-only fixture/static artifact input.
- No network calls.
- No LLM provider calls.
- No external market API calls.
- No authenticated endpoint use.
- No wallet, order, trading endpoint, payment, transaction, or signing path.
- No runtime, dispatcher, scheduler, worker, browser, or app-server wiring.
- No market scoring metrics, stance selection, or trade action output.
- The validation JSON and Markdown report are not execution approval and are not runtime input.
