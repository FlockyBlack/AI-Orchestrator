# PMBOT Paper Accounting Session Summary

Session ID: `paper_accounting_ledger_fixture_001.paper_accounting_session_summary`
Build ID: `paper_accounting_ledger_fixture_001-02801beecc93.paper_accounting_session_summary`
Ledger ID: `paper_accounting_ledger_fixture_001`
Ledger build ID: `paper_accounting_ledger_fixture_001-02801beecc93`
Validation ID: `paper_accounting_ledger_fixture_001.paper_accounting_validation`
Validation build ID: `paper_accounting_ledger_fixture_001-02801beecc93.paper_accounting_validation`
Run mode: `local_paper_only_session_summary`
Operator review: `pending_operator_review`

## Summary

- Accounting entries: 3
- Input artifacts: 2
- Validation rows: 3
- Failed validation checks: 0
- Warnings: 0

## Balance Summary

- `USD` net quantity delta `992.50` from 3 entries.

## Session Review Rows

- `paper_fixture_account_001.2026-05-09.opening_balance`: `USD` delta `1000.00` with validation row `passed`.
- `paper_fixture_account_001.2026-05-09.paper_adjustment`: `USD` delta `-12.50` with validation row `passed`.
- `paper_fixture_account_001.2026-05-09.paper_correction`: `USD` delta `5.00` with validation row `passed`.

## Safety

- Local fixture/static ledger and validation inputs only.
- Makes no network, LLM, external market API, wallet, order, transaction endpoint, or runtime calls.
- Descriptive paper accounting session summary only; it is not an approval record for execution.
- Operator review remains required before using these records outside this local artifact.
