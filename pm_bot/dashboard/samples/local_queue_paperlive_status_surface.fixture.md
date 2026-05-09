# PMBOT Queue And Paperlive Status Surface

Surface: `local_queue_paperlive_status_surface_fixture_001-1891120f6f78`
Label: `PMBOT queue and paperlive local status`
Run mode: `local_static_queue_paperlive_status_surface`
Operator review: `pending_operator_review`

## Summary Counts

- Queue status records: 3
- Paperlive status records: 2
- Validation records: 2
- Pending operator review records: 7
- Warnings: 0

## Queue Status Records

- `PMBOT-DASHBOARD-002-QUEUE-AND-PAPERLIVE-STATUS-SURFACE`: group `next_twenty_template`, template `queue_and_paperlive_status_surface`, state `template_listed_static_record`, review `pending_operator_review`, reference `tests/test_codex_queue_pmbot_templates.py`
- `PMBOT-PAPERLIVE-010W-005-WEATHER-OPERATOR-REVIEW-SURFACE-UPDATE-NO-TRADE`: group `night_batch_template`, template `weather_operator_review_surface`, state `template_listed_static_record`, review `pending_operator_review`, reference `docs/PMBOT_PAPERLIVE_010W_005_WEATHER_OPERATOR_REVIEW_SURFACE_UPDATE_NO_TRADE.md`
- `PMBOT-CRYPTO-PILOT-003-CRYPTO-PAPERLIVE-OBSERVATION-LEDGER-LOCAL-ONLY`: group `next_twenty_template`, template `crypto_paperlive_observation_ledger`, state `template_listed_static_record`, review `pending_operator_review`, reference `docs/PMBOT_CRYPTO_PILOT_003_CRYPTO_PAPERLIVE_OBSERVATION_LEDGER_LOCAL_ONLY.md`

## Paperlive Status Records

- `weather_operator_review_surface_static_status`: area `weather_observation_review`, records 2, state `static_local_reference_ready`, review `pending_operator_review`, reference `docs/PMBOT_PAPERLIVE_010W_005_WEATHER_OPERATOR_REVIEW_SURFACE_UPDATE_NO_TRADE.md`
- `crypto_paperlive_observation_ledger_static_status`: area `crypto_observation_ledger`, records 1, state `static_local_reference_ready`, review `pending_operator_review`, reference `docs/PMBOT_CRYPTO_PILOT_003_CRYPTO_PAPERLIVE_OBSERVATION_LEDGER_LOCAL_ONLY.md`

## Validation Status Records

- `compileall.pm_bot.tests`: status `not_run_static_record`, command `python -m compileall pm_bot tests`, reference `tests/test_codex_queue_pmbot_templates.py`
- `pytest.pm_bot_tests.queue_templates`: status `not_run_static_record`, command `pytest pm_bot/tests tests/test_codex_queue_pmbot_templates.py`, reference `tests/test_codex_queue_pmbot_templates.py`

## Safety

- Local fixture/static input only.
- Makes no network, LLM, external market API, wallet, order, transaction endpoint, runtime, browser, scheduler, or worker calls.
- Descriptive status inventory only; no outcome resolution or trade instruction output.
- Not execution approval and not runtime input.
