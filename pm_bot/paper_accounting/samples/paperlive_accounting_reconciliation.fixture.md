# PMBOT Paperlive To Accounting Reconciliation

Reconciliation ID: `paperlive_accounting_reconciliation_fixture_001`
Build ID: `paperlive_accounting_reconciliation_fixture_001-e515f0da1873`
Run mode: `local_static_paperlive_to_accounting_reconciliation`
Operator review: `pending_operator_review`

## Summary

- Paperlive records: 1
- Reconciliation rows: 1
- Accounting entries linked: 0
- Accounting entries total: 3
- Input artifacts: 4
- Warnings: 0

## Input Artifacts

- `crypto_paperlive_observation_ledger_001`: `crypto_paperlive_observation_ledger` from `pm_bot/tests/fixtures/crypto_paperlive_observation_ledger/crypto_paperlive_observation_ledger.valid.json`.
- `paper_accounting_ledger_fixture_001`: `paper_accounting_ledger` from `pm_bot/paper_accounting/samples/paper_accounting_ledger.fixture.json`.
- `paper_accounting_ledger_fixture_001.paper_accounting_validation`: `paper_accounting_validation` from `pm_bot/paper_accounting/samples/paper_accounting_validation.fixture.json`.
- `paper_accounting_ledger_fixture_001.paper_accounting_session_summary`: `paper_accounting_session_summary` from `pm_bot/paper_accounting/samples/paper_accounting_session_summary.fixture.json`.

## Reconciliation Rows

- `crypto_paperlive_observation_ledger_001.sample.btc_threshold.observation`: `no_accounting_delta_recorded` with 0 linked accounting entries and quantity delta `0.00`.

## Safety

- Local fixture/static paperlive and paper accounting inputs only.
- Makes no network, LLM, external market API, wallet, order, transaction endpoint, or runtime calls.
- Descriptive paperlive to accounting reconciliation only; it is not execution approval.
- Operator review remains required before using these records outside this local artifact.
