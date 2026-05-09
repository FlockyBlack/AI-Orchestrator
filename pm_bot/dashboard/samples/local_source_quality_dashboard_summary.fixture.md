# PMBOT Source Quality Dashboard Summary

Dashboard: `local_source_quality_dashboard_fixture_001`
Build: `local_source_quality_dashboard_fixture_001-ebfa452f14b1`
Label: `PMBOT local source quality dashboard`
Run mode: `local_static_source_quality_dashboard_summary`
Operator review: `pending_operator_review`

## Summary Counts

- Queue records: 5
- Source quality artifacts: 4
- Source artifacts: 10
- Source quality rows: 10
- Declared fields: 59
- Present fields: 59
- Missing fields: 0
- Review checks: 28
- Known limitations: 12
- Review assertions: 11
- Validation records: 2
- Pending operator review records: 11
- Warnings: 0

## Queue Records

- `PMBOT-DASHBOARD-003-SOURCE-QUALITY-DASHBOARD-SUMMARY`: group `next_twenty_template`, template `source_quality_dashboard_summary`, state `template_listed_static_record`, review `pending_operator_review`, reference `docs/PMBOT_DASHBOARD_003_SOURCE_QUALITY_DASHBOARD_SUMMARY.md`
- `PMBOT-SOURCE-LEDGER-001-UNIFIED-SOURCE-QUALITY-LEDGER-LOCAL-ONLY`: group `night_batch_template`, template `unified_source_quality_ledger`, state `template_listed_static_record`, review `pending_operator_review`, reference `docs/PMBOT_SOURCE_LEDGER_001_UNIFIED_SOURCE_QUALITY_LEDGER_LOCAL_ONLY.md`
- `PMBOT-SOURCE-LEDGER-003-SOURCE-QUALITY-REPORT-SUMMARY-LOCAL-ONLY`: group `next_twenty_template`, template `source_quality_report_summary`, state `template_listed_static_record`, review `pending_operator_review`, reference `docs/PMBOT_SOURCE_LEDGER_003_SOURCE_QUALITY_REPORT_SUMMARY_LOCAL_ONLY.md`
- `PMBOT-SOURCE-LEDGER-004-SOURCE-QUALITY-REGRESSION-FIXTURE-LOCAL-ONLY`: group `next_twenty_template`, template `source_quality_regression_fixture`, state `template_listed_static_record`, review `pending_operator_review`, reference `docs/PMBOT_SOURCE_LEDGER_004_SOURCE_QUALITY_REGRESSION_FIXTURE_LOCAL_ONLY.md`
- `PMBOT-CRYPTO-PILOT-004-CRYPTO-SOURCE-QUALITY-CAPTURE-SURFACE-LOCAL-ONLY`: group `next_twenty_template`, template `crypto_source_quality_capture_surface`, state `template_listed_static_record`, review `pending_operator_review`, reference `docs/PMBOT_CRYPTO_PILOT_004_CRYPTO_SOURCE_QUALITY_CAPTURE_SURFACE_LOCAL_ONLY.md`

## Source Quality Artifacts

- `unified_source_quality_ledger_fixture_001`: type `unified_source_quality_ledger`, rows 2, fields 8/8, review `pending_operator_review`, sample `pm_bot/source_quality/samples/unified_source_quality_ledger.fixture.json`
- `unified_source_quality_ledger_fixture_001.source_quality_report_summary`: type `source_quality_report_summary`, rows 2, fields 8/8, review `pending_operator_review`, sample `pm_bot/source_quality/samples/source_quality_report_summary.fixture.json`
- `source_quality_regression_fixture_001`: type `source_quality_regression_fixture`, rows 2, fields 8/8, review `pending_operator_review`, sample `pm_bot/source_quality/samples/source_quality_regression.fixture.json`
- `crypto_source_quality_capture_surface_001`: type `crypto_source_quality_capture_surface`, rows 4, fields 35/35, review `pending_operator_review`, sample `pm_bot/source_quality/samples/crypto_source_quality_capture_surface.fixture.json`

## Validation Status Records

- `compileall.pm_bot.tests`: status `not_run_static_record`, command `python -m compileall pm_bot tests`, reference `tests/test_codex_queue_pmbot_templates.py`
- `pytest.pm_bot_tests.queue_templates`: status `not_run_static_record`, command `pytest pm_bot/tests tests/test_codex_queue_pmbot_templates.py`, reference `tests/test_codex_queue_pmbot_templates.py`

## Operator Review Steps

- Confirm each source quality artifact row points to an expected local sample or documentation reference.
- Confirm summary counts match the named static source quality artifacts.
- Confirm all rows remain pending operator review before downstream human review.
- Confirm this dashboard remains descriptive source quality inventory only.

## Safety

- Local fixture/static input only.
- Makes no network, LLM, external market API, wallet, order, transaction endpoint, runtime, browser, scheduler, or worker calls.
- Descriptive source quality dashboard only; no outcome resolution or trade instruction output.
- Not execution approval and not runtime input.
