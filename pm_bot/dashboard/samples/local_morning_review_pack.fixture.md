# PMBOT Morning Review Pack

Task: `PMBOT-OPERATOR-001-MORNING-REVIEW-PACK-LOCAL-ONLY`
Pack: `pmbot_morning_review_pack_fixture_001`
Build: `pmbot_morning_review_pack_fixture_001-a00add774289`
Contract: `pmbot_local_morning_review_pack.v1`
Run mode: `local_static_morning_review_pack`
Operator review: `pending_operator_review`

## Summary Counts

- Queue records: 3
- Dashboard records: 4
- Safety records: 3
- Validation records: 2
- Pending operator review records: 12
- Local references: 13
- Warnings: 0

## Queue Review

- `PMBOT-OPERATOR-001-MORNING-REVIEW-PACK-LOCAL-ONLY`: group `next_twenty_template`, template `morning_review_pack`, state `static_task_record_ready`, reference `docs/PMBOT_OPERATOR_001_MORNING_REVIEW_PACK_LOCAL_ONLY.md`
- `PMBOT-SAFETY-002-NIGHT-BATCH-POSTRUN-AUDIT-SUMMARY-LOCAL-ONLY`: group `safety_template`, template `night_batch_postrun_audit_summary`, state `static_task_record_ready`, reference `docs/PMBOT_SAFETY_002_NIGHT_BATCH_POSTRUN_AUDIT_SUMMARY_LOCAL_ONLY.md`
- `PMBOT-DASHBOARD-002-QUEUE-AND-PAPERLIVE-STATUS-SURFACE`: group `dashboard_template`, template `queue_and_paperlive_status_surface`, state `static_task_record_ready`, reference `docs/PMBOT_DASHBOARD_002_QUEUE_AND_PAPERLIVE_STATUS_SURFACE.md`

## Dashboard Review

- `local_operator_dashboard_summary`: type `dashboard_summary`, records 9, reference `docs/PMBOT_DASHBOARD_001_LOCAL_OPERATOR_DASHBOARD_SUMMARY.md`
- `queue_paperlive_status_surface`: type `dashboard_summary`, records 7, reference `docs/PMBOT_DASHBOARD_002_QUEUE_AND_PAPERLIVE_STATUS_SURFACE.md`
- `source_quality_dashboard_summary`: type `dashboard_summary`, records 6, reference `docs/PMBOT_DASHBOARD_003_SOURCE_QUALITY_DASHBOARD_SUMMARY.md`
- `paper_accounting_dashboard_summary`: type `dashboard_summary`, records 5, reference `docs/PMBOT_DASHBOARD_004_PAPER_ACCOUNTING_DASHBOARD_SUMMARY.md`

## Safety Review

- `autonomy_gate_checklist`: state `closed_local_only_boundary`, reference `docs/PMBOT_SAFETY_001_AUTONOMY_GATE_CHECKLIST_LOCAL_ONLY.md`
- `night_batch_postrun_audit`: state `closed_local_only_boundary`, reference `docs/PMBOT_SAFETY_002_NIGHT_BATCH_POSTRUN_AUDIT_SUMMARY_LOCAL_ONLY.md`
- `forbidden_action_scan`: state `closed_local_only_boundary`, reference `docs/PMBOT_SAFETY_003_FORBIDDEN_ACTION_SCAN_LOCAL_ONLY.md`

## Validation Review

- `compileall.pm_bot.tests`: status `not_run_static_record`, command `python -m compileall pm_bot tests`, reference `tests/test_codex_queue_pmbot_templates.py`
- `pytest.pm_bot_tests.queue_templates`: status `not_run_static_record`, command `pytest pm_bot/tests tests/test_codex_queue_pmbot_templates.py`, reference `tests/test_codex_queue_pmbot_templates.py`

## Safety

- Local files and static fixtures only.
- Makes no network, LLM, external service, wallet, signing, endpoint, runtime, browser, scheduler, or worker calls.
- Descriptive operator review material only.
- Not execution approval and not runtime input.
