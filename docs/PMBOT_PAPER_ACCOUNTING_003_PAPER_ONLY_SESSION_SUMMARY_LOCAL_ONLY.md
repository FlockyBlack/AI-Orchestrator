# PMBOT Paper Accounting 003 Paper-Only Session Summary

## Scope

This task adds a deterministic local session summary for PMBOT paper accounting review records.

## Changes

- Added `pm_bot/paper_accounting/paper_accounting_session_summary.py`.
- Added deterministic JSON and Markdown samples under `pm_bot/paper_accounting/samples/`.
- Added focused tests in `pm_bot/tests/test_paper_accounting_session_summary.py`.

## Contract

Session summary artifacts use contract version `pmbot_paper_accounting_session_summary.v1`.

The summary consumes only local paper accounting ledger and validation artifacts. It records:

- ledger and validation artifact identity
- local input artifact references
- pending operator review status
- accounting entry row summaries
- validation row status counts
- balance totals copied from the local ledger
- closed local-only safety boundaries

## Static Sample Command

```powershell
python -m pm_bot.paper_accounting.paper_accounting_session_summary `
  --ledger pm_bot\paper_accounting\samples\paper_accounting_ledger.fixture.json `
  --validation pm_bot\paper_accounting\samples\paper_accounting_validation.fixture.json `
  --output-summary pm_bot\paper_accounting\samples\paper_accounting_session_summary.fixture.json `
  --output-report pm_bot\paper_accounting\samples\paper_accounting_session_summary.fixture.md
```

## Safety

The session summary is descriptive and local-only. It does not make network, LLM, external market API, wallet, order, transaction endpoint, runtime, scheduler, or worker calls. It does not approve execution. Operator review remains required.

## Validation

```powershell
python -m compileall pm_bot tests
pytest pm_bot/tests tests/test_codex_queue_pmbot_templates.py
```
