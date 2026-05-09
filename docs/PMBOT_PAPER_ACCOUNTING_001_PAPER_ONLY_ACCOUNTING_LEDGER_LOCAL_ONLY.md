# PMBOT Paper Accounting 001 Paper-Only Accounting Ledger

Task: `PMBOT-PAPER-ACCOUNTING-001-PAPER-ONLY-ACCOUNTING-LEDGER-LOCAL-ONLY`

## What Changed

- Added a local paper accounting ledger builder in `pm_bot/paper_accounting/paper_accounting_ledger.py`.
- Added deterministic local request and event fixtures under `pm_bot/tests/fixtures/paper_accounting/`.
- Added a static sample ledger under `pm_bot/paper_accounting/samples/`.
- Added focused tests for deterministic output, CLI writing, local path enforcement, local event matching, operator review state, and blocked scoring/action fields.

## Ledger Contract

Requests use contract version `pmbot_paper_accounting_ledger_request.v1`.

Required fields:

- `contract_version`
- `ledger_id`
- `scope`
- `local_only`
- `operator_review_required`
- `account_context`
- `source_artifacts`
- `entry_specs`
- `operator_review_steps`

Each source artifact must point to a repository-relative local fixture or static artifact under the paper accounting boundary. Network-like references, path traversal, forbidden operational paths, and undeclared local scopes are rejected.

Each accounting entry references a declared local event by identifier. The builder verifies that the entry asset code, entry type, and quantity delta match the local event before emitting the ledger.

## CLI

```powershell
python -m pm_bot.paper_accounting.paper_accounting_ledger `
  --request pm_bot\tests\fixtures\paper_accounting\paper_accounting_ledger_request.valid.json `
  --output-ledger <local-output-path>.json `
  --output-report <local-output-path>.md
```

The command writes:

- a JSON ledger with contract version `pmbot_paper_accounting_ledger.v1`
- a Markdown operator report summarizing the same local review surface

## Operator Review Boundary

The ledger is a descriptive local review artifact. It inventories local paper accounting events, entry deltas, source artifacts, and balance totals for operator review.

It does not rank markets, approve execution, open endpoints, or modify accounts. Operators must review accounting disputes outside this ledger.

## Safety

- Local-only fixture/static artifact input.
- No network calls.
- No LLM provider calls.
- No external market API calls.
- No authenticated endpoint use.
- No wallet, order, trading endpoint, payment, transaction, or signing path.
- No runtime, dispatcher, scheduler, worker, browser, or app-server wiring.
- No market scoring metrics, stance selection, or trade action output.
- The ledger and Markdown report are not execution approval and are not runtime input.
