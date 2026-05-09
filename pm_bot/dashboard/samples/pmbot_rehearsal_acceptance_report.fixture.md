# PMBOT Rehearsal Acceptance Report

Report: `pmbot-rehearsal-acceptance-report-001`
Run mode: `local_static_rehearsal_acceptance_report`
Operator review: `pending_operator_review`

## Summary Counts

- Acceptance sections: 6
- Readiness records: 26
- Supporting artifacts: 39
- Source artifacts: 35
- Operator review checks: 8
- Validation command records: 2
- Pending acceptance sections: 6
- Warnings: 0

## Acceptance Sections

- `rehearsal_inventory_review`: type `rehearsal_inventory_review`, records 4, supporting artifacts 4, review `pending_operator_review`, reference `tests/test_codex_queue_pmbot_templates.py`
- `rehearsal_dashboard_readiness_review`: type `dashboard_readiness_review`, records 4, supporting artifacts 4, review `pending_operator_review`, reference `pm_bot/dashboard/samples/pmbot_rehearsal_readiness_dashboard_card.fixture.json`
- `rehearsal_morning_card_review`: type `morning_card_review`, records 4, supporting artifacts 4, review `pending_operator_review`, reference `pm_bot/dashboard/samples/pmbot_rehearsal_morning_operator_card.fixture.json`
- `rehearsal_control_review`: type `rehearsal_control_review`, records 4, supporting artifacts 8, review `pending_operator_review`, reference `docs/PMBOT_REHEARSAL_001_READ_ONLY_REHEARSAL_SCENARIO_CONTRACT_LOCAL_ONLY.md`
- `rehearsal_source_validation_review`: type `source_validation_review`, records 6, supporting artifacts 14, review `pending_operator_review`, reference `docs/PMBOT_REHEARSAL_003_REHEARSAL_SOURCE_EVIDENCE_BUNDLE_LOCAL_ONLY.md`
- `rehearsal_safety_review`: type `safety_review`, records 4, supporting artifacts 5, review `pending_operator_review`, reference `pm_bot/tests/fixtures/rehearsal/pmbot_rehearsal_ci_safe_validation_runner.valid.json`

## Validation Status Records

- `python -m compileall pm_bot tests`: status `not_run_static_record`, reference `tests/test_codex_queue_pmbot_templates.py`
- `pytest pm_bot/tests tests/test_codex_queue_pmbot_templates.py`: status `not_run_static_record`, reference `tests/test_codex_queue_pmbot_templates.py`

## Operator Review

- Confirm acceptance sections have primary local references.
- Confirm source artifact references resolve inside allowed local paths.
- Confirm readiness dashboard card samples are included.
- Confirm morning operator card samples are included.
- Confirm control records remain local review material.
- Confirm validation command records are captured for operator review.
- Confirm sensitive path and execution wiring boundaries remain closed.
- Confirm the markdown report mirrors the static JSON report.

## Safety

- Local files, local fixtures, and static samples only.
- Makes no network, LLM provider, external service, wallet, order, transaction endpoint, runtime, browser, scheduler, or worker calls.
- Descriptive rehearsal acceptance report only; no live transition, data refresh, outcome resolution, market ranking, numeric prediction metric, threshold comparison output, or transaction output.
- Not execution approval and not runtime input.
