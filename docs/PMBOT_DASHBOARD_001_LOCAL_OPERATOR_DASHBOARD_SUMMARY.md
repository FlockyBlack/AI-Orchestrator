# PMBOT Local Operator Dashboard Summary

Dashboard: `local_operator_dashboard_fixture_001`
Build: `local_operator_dashboard_fixture_001-46e124e79bf8`
Run mode: `local_static_dashboard_summary`
Operator review: `pending_operator_review`

## Summary Counts

- Queue records: 4
- Ledger records: 3
- Validation records: 2
- Pending operator review records: 9
- Warnings: 0

## Queue Records

- `PMBOT-DASHBOARD-001-LOCAL-OPERATOR-DASHBOARD-SUMMARY`: bucket `planned_template`, template `local_operator_dashboard_summary`, review `pending_operator_review`, reference `tests/test_codex_queue_pmbot_templates.py`
- `PMBOT-PAPER-ACCOUNTING-001-PAPER-ONLY-ACCOUNTING-LEDGER-LOCAL-ONLY`: bucket `planned_template`, template `paper_only_accounting_ledger`, review `pending_operator_review`, reference `docs/PMBOT_PAPER_ACCOUNTING_001_PAPER_ONLY_ACCOUNTING_LEDGER_LOCAL_ONLY.md`
- `PMBOT-SOURCE-LEDGER-001-UNIFIED-SOURCE-QUALITY-LEDGER-LOCAL-ONLY`: bucket `planned_template`, template `unified_source_quality_ledger`, review `pending_operator_review`, reference `docs/PMBOT_SOURCE_LEDGER_001_UNIFIED_SOURCE_QUALITY_LEDGER_LOCAL_ONLY.md`
- `PMBOT-PAPERLIVE-010W-005-WEATHER-OPERATOR-REVIEW-SURFACE-UPDATE-NO-TRADE`: bucket `planned_template`, template `weather_operator_review_surface`, review `pending_operator_review`, reference `docs/PMBOT_PAPERLIVE_010W_005_WEATHER_OPERATOR_REVIEW_SURFACE_UPDATE_NO_TRADE.md`

## Ledger Records

- `weather_observation_ledger_fixture_001`: type `weather_observation`, records 2, review `pending_operator_review`, reference `pm_bot/tests/fixtures/weather_observation_ledger_refresh_request.valid.json`
- `unified_source_quality_ledger_fixture_001`: type `source_quality`, records 2, review `pending_operator_review`, reference `pm_bot/tests/fixtures/source_quality/unified_source_quality_ledger_request.valid.json`
- `paper_accounting_ledger_fixture_001`: type `paper_accounting`, records 3, review `pending_operator_review`, reference `pm_bot/tests/fixtures/paper_accounting/paper_accounting_ledger_request.valid.json`

## Validation Status Records

- `compileall.pm_bot.tests`: status `not_run_static_record`, command `python -m compileall pm_bot tests`, reference `tests/test_codex_queue_pmbot_templates.py`
- `pytest.pm_bot_tests.queue_templates`: status `not_run_static_record`, command `pytest pm_bot/tests tests/test_codex_queue_pmbot_templates.py`, reference `tests/test_codex_queue_pmbot_templates.py`

## Safety

- Local fixture/static input only.
- Makes no network, LLM, external market API, wallet, order, transaction endpoint, runtime, browser, scheduler, or worker calls.
- Descriptive dashboard status only; no outcome resolution or trade instruction output.
- Not execution approval and not runtime input.
