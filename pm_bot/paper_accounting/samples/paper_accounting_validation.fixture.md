# PMBOT Paper Accounting Validation

Validation ID: `paper_accounting_ledger_fixture_001.paper_accounting_validation`
Build ID: `paper_accounting_ledger_fixture_001-02801beecc93.paper_accounting_validation`
Ledger ID: `paper_accounting_ledger_fixture_001`
Ledger build ID: `paper_accounting_ledger_fixture_001-02801beecc93`
Run mode: `local_paper_only_validation`
Operator review: `pending_operator_review`

## Summary

- Accounting entries: 3
- Validation rows: 3
- Validation checks: 18
- Failed checks: 0
- Warnings: 0

## Record Validation Rows

- `paper_fixture_account_001.2026-05-09.opening_balance`: 6 checks `passed` for `USD` delta `1000.00`.
- `paper_fixture_account_001.2026-05-09.paper_adjustment`: 6 checks `passed` for `USD` delta `-12.50`.
- `paper_fixture_account_001.2026-05-09.paper_correction`: 6 checks `passed` for `USD` delta `5.00`.

## Safety

- Local fixture/static ledger input only.
- Makes no network, LLM, external market API, wallet, order, transaction endpoint, or runtime calls.
- Descriptive paper accounting validation only; it is not an approval record for execution.
- Operator review remains required before using these records outside this local artifact.
