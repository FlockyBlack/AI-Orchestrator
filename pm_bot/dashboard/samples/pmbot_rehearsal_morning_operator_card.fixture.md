# PMBOT Rehearsal Morning Operator Card

Card: `pmbot-rehearsal-morning-operator-card-001`
Run mode: `local_static_rehearsal_morning_operator_card`
Operator review: `pending_operator_review`

## Summary Counts

- Card sections: 6
- Readiness records: 23
- Supporting artifacts: 34
- Source artifacts: 31
- Operator review checks: 7
- Validation command records: 2
- Pending card sections: 6
- Warnings: 0

## Card Sections

- `morning_rehearsal_readiness_snapshot`: type `rehearsal_readiness_snapshot`, records 4, supporting artifacts 4, review `pending_operator_review`, reference `pm_bot/dashboard/samples/pmbot_rehearsal_readiness_dashboard_card.fixture.json`
- `morning_rehearsal_control_snapshot`: type `rehearsal_control_snapshot`, records 4, supporting artifacts 8, review `pending_operator_review`, reference `docs/PMBOT_REHEARSAL_001_READ_ONLY_REHEARSAL_SCENARIO_CONTRACT_LOCAL_ONLY.md`
- `morning_rehearsal_source_snapshot`: type `rehearsal_source_snapshot`, records 4, supporting artifacts 8, review `pending_operator_review`, reference `docs/PMBOT_REHEARSAL_003_REHEARSAL_SOURCE_EVIDENCE_BUNDLE_LOCAL_ONLY.md`
- `morning_rehearsal_validation_snapshot`: type `rehearsal_validation_snapshot`, records 3, supporting artifacts 6, review `pending_operator_review`, reference `docs/PMBOT_REHEARSAL_010_REHEARSAL_CI_SAFE_VALIDATION_RUNNER_LOCAL_ONLY.md`
- `morning_rehearsal_operator_review_snapshot`: type `rehearsal_operator_review_snapshot`, records 4, supporting artifacts 4, review `pending_operator_review`, reference `docs/PMBOT_REHEARSAL_012_REHEARSAL_MORNING_OPERATOR_CARD_LOCAL_ONLY.md`
- `morning_rehearsal_safety_snapshot`: type `rehearsal_safety_snapshot`, records 4, supporting artifacts 4, review `pending_operator_review`, reference `pm_bot/tests/fixtures/rehearsal/pmbot_rehearsal_ci_safe_validation_runner.valid.json`

## Validation Status Records

- `python -m compileall pm_bot tests`: status `not_run_static_record`, reference `tests/test_codex_queue_pmbot_templates.py`
- `pytest pm_bot/tests tests/test_codex_queue_pmbot_templates.py`: status `not_run_static_record`, reference `tests/test_codex_queue_pmbot_templates.py`

## Operator Review

- Confirm each morning card section has one primary local reference.
- Confirm the rehearsal readiness dashboard card is included as the morning basis.
- Confirm control records remain local static references.
- Confirm source evidence records remain local static references.
- Confirm validation records are captured for operator review.
- Confirm sensitive path and execution wiring boundaries remain closed.
- Confirm this report mirrors the static morning operator card.

## Safety

- Local files, local fixtures, and static samples only.
- Makes no network, LLM provider, external service, wallet, order, transaction endpoint, runtime, browser, scheduler, or worker calls.
- Descriptive rehearsal morning operator card only; no live transition, data refresh, ranking output, metric output, or transaction output.
- Not execution approval and not runtime input.
