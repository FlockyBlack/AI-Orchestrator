# PMBOT Paper Accounting Ledger

Ledger ID: `paper_accounting_ledger_fixture_001`
Build ID: `paper_accounting_ledger_fixture_001-02801beecc93`
Run mode: `local_paper_only`
Operator review: `pending_operator_review`

## Summary

- Accounting entries: 3
- Source artifacts: 1
- Assets: 1
- Warnings: 0

## Balance Summary

- `USD` net quantity delta `992.50` from 3 entries.

## Accounting Entries

- `paper_fixture_account_001.2026-05-09.opening_balance`: `USD` delta `1000.00` from `paper_accounting_events_fixture_001`. Review `Opening paper cash balance`.
- `paper_fixture_account_001.2026-05-09.paper_adjustment`: `USD` delta `-12.50` from `paper_accounting_events_fixture_001`. Review `Offline accounting adjustment`.
- `paper_fixture_account_001.2026-05-09.paper_correction`: `USD` delta `5.00` from `paper_accounting_events_fixture_001`. Review `Offline accounting correction`.

## Safety

- Local fixture/static input only.
- Makes no network, LLM, external market API, wallet, order, transaction endpoint, or runtime calls.
- Descriptive paper accounting only; it is not an approval record for execution.
- Operator review remains required before using these records outside this local artifact.
