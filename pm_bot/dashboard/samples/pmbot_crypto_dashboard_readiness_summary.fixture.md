# PMBOT Crypto Dashboard Readiness Summary

Dashboard: `pmbot-crypto-dashboard-readiness-summary-001`
Run mode: `local_static_crypto_dashboard_readiness_summary`
Operator review: `pending_operator_review`

## Summary Counts

- Dashboard sections: 6
- Readiness records: 18
- Supporting artifacts: 22
- Source artifacts: 25
- Operator review checks: 6
- Validation command records: 2
- Pending dashboard sections: 6
- Warnings: 0

## Dashboard Sections

- `crypto_operator_dashboard_surface`: type `operator_dashboard_surface`, records 3, supporting artifacts 3, review `pending_operator_review`, reference `pm_bot/dashboard/samples/local_operator_dashboard_summary.fixture.json`
- `crypto_queue_and_replay_surface`: type `queue_replay_surface`, records 3, supporting artifacts 3, review `pending_operator_review`, reference `pm_bot/dashboard/samples/local_queue_paperlive_status_surface.fixture.json`
- `crypto_source_quality_surface`: type `source_quality_surface`, records 4, supporting artifacts 5, review `pending_operator_review`, reference `pm_bot/dashboard/samples/local_source_quality_dashboard_summary.fixture.json`
- `crypto_paper_accounting_surface`: type `paper_accounting_surface`, records 2, supporting artifacts 2, review `pending_operator_review`, reference `pm_bot/dashboard/samples/local_paper_accounting_dashboard_summary.fixture.json`
- `crypto_supervised_readiness_surface`: type `supervised_readiness_surface`, records 3, supporting artifacts 5, review `pending_operator_review`, reference `pm_bot/dashboard/samples/local_supervised_live_readiness_dashboard.fixture.json`
- `crypto_safety_review_surface`: type `safety_review_surface`, records 3, supporting artifacts 4, review `pending_operator_review`, reference `pm_bot/dashboard/samples/pmbot_crypto_dashboard_readiness_summary.fixture.json`

## Validation Status Records

- `python -m compileall pm_bot tests`: status `not_run_static_record`, reference `tests/test_codex_queue_pmbot_templates.py`
- `pytest pm_bot/tests tests/test_codex_queue_pmbot_templates.py`: status `not_run_static_record`, reference `tests/test_codex_queue_pmbot_templates.py`

## Operator Review

- Confirm each dashboard section has one primary local reference.
- Confirm source artifact references resolve inside the allowed local paths.
- Confirm crypto gate records remain pending operator review.
- Confirm local validation command records are captured for operator review.
- Confirm sensitive path and execution wiring boundaries remain closed.
- Confirm this report mirrors the static dashboard summary.

## Safety

- Local files, local fixtures, and static samples only.
- Makes no network, LLM provider, external service, wallet, order, transaction endpoint, runtime, browser, scheduler, or worker calls.
- Descriptive dashboard readiness summary only; no live transition, data refresh, outcome resolution, or trade instruction output.
- Not execution approval and not runtime input.
