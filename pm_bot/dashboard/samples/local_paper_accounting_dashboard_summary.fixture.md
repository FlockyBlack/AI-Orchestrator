# PMBOT Paper Accounting Dashboard Summary

Dashboard: `local_paper_accounting_dashboard_fixture_001`
Build: `local_paper_accounting_dashboard_fixture_001-9d977b7f5bc0`
Label: `PMBOT local paper accounting dashboard`
Run mode: `local_static_paper_accounting_dashboard_summary`
Operator review: `pending_operator_review`

## Summary Counts

- Queue records: 4
- Paper accounting artifacts: 3
- Ledger accounting entries: 3
- Validation rows: 6
- Validation checks: 18
- Failed validation checks: 0
- Session rows: 3
- Balance assets: 1
- Input artifacts: 2
- Source artifacts: 3
- Validation records: 2
- Pending operator review records: 10
- Warnings: 0

## Queue Records

- `PMBOT-DASHBOARD-004-PAPER-ACCOUNTING-DASHBOARD-SUMMARY`: group `next_twenty_template`, template `paper_accounting_dashboard_summary`, state `template_listed_static_record`, review `pending_operator_review`, reference `docs/PMBOT_DASHBOARD_004_PAPER_ACCOUNTING_DASHBOARD_SUMMARY.md`
- `PMBOT-PAPER-ACCOUNTING-001-PAPER-ONLY-ACCOUNTING-LEDGER-LOCAL-ONLY`: group `night_batch_template`, template `paper_accounting_ledger`, state `template_listed_static_record`, review `pending_operator_review`, reference `docs/PMBOT_PAPER_ACCOUNTING_001_PAPER_ONLY_ACCOUNTING_LEDGER_LOCAL_ONLY.md`
- `PMBOT-PAPER-ACCOUNTING-002-PAPER-ONLY-ACCOUNTING-VALIDATOR-LOCAL-ONLY`: group `next_twenty_template`, template `paper_accounting_validator`, state `template_listed_static_record`, review `pending_operator_review`, reference `docs/PMBOT_PAPER_ACCOUNTING_002_PAPER_ONLY_ACCOUNTING_VALIDATOR_LOCAL_ONLY.md`
- `PMBOT-PAPER-ACCOUNTING-003-PAPER-ONLY-SESSION-SUMMARY-LOCAL-ONLY`: group `next_twenty_template`, template `paper_accounting_session_summary`, state `template_listed_static_record`, review `pending_operator_review`, reference `docs/PMBOT_PAPER_ACCOUNTING_003_PAPER_ONLY_SESSION_SUMMARY_LOCAL_ONLY.md`

## Paper Accounting Artifacts

- `paper_accounting_ledger_fixture_001`: type `paper_accounting_ledger`, ledger entries 3, validation rows 0, session rows 0, review `pending_operator_review`, sample `pm_bot/paper_accounting/samples/paper_accounting_ledger.fixture.json`
- `paper_accounting_ledger_fixture_001.paper_accounting_validation`: type `paper_accounting_validation`, ledger entries 0, validation rows 3, session rows 0, review `pending_operator_review`, sample `pm_bot/paper_accounting/samples/paper_accounting_validation.fixture.json`
- `paper_accounting_ledger_fixture_001.paper_accounting_session_summary`: type `paper_accounting_session_summary`, ledger entries 0, validation rows 3, session rows 3, review `pending_operator_review`, sample `pm_bot/paper_accounting/samples/paper_accounting_session_summary.fixture.json`

## Balance Summary

- `USD` net quantity delta `992.50` from 3 entries, review `pending_operator_review`.

## Validation Status Records

- `compileall.pm_bot.tests`: status `not_run_static_record`, command `python -m compileall pm_bot tests`, reference `tests/test_codex_queue_pmbot_templates.py`
- `pytest.pm_bot_tests.queue_templates`: status `not_run_static_record`, command `pytest pm_bot/tests tests/test_codex_queue_pmbot_templates.py`, reference `tests/test_codex_queue_pmbot_templates.py`

## Operator Review Steps

- Confirm each paper accounting artifact row points to an expected local sample or documentation reference.
- Confirm displayed counts match the local ledger, validation, and session summary samples.
- Confirm balance rows remain descriptive local totals.
- Confirm all rows remain pending operator review before downstream human review.

## Safety

- Local fixture/static input only.
- Makes no network, LLM, external market API, wallet, order, transaction endpoint, runtime, browser, scheduler, or worker calls.
- Descriptive paper accounting dashboard only; no outcome resolution or trade instruction output.
- Not execution approval and not runtime input.
