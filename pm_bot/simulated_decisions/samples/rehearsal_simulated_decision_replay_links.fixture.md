# PMBOT Rehearsal Simulated Decision Replay Links

Task: `PMBOT-REHEARSAL-016-REHEARSAL-SIMULATED-DECISION-REPLAY-LINKS-LOCAL-ONLY`
Link set: `pmbot-rehearsal-simulated-decision-replay-links-001`
Build: `pmbot-rehearsal-simulated-decision-replay-links-001-c5d6695c48b1`
Run mode: `local_static_rehearsal_simulated_decision_replay_links`
Operator review: `pending_operator_review`

## Summary Counts
- link_fields: 12
- local_references: 11
- operator_review_steps: 4
- rehearsal_artifacts: 5
- rehearsal_record_links: 5
- required_validation_commands: 2
- review_checks: 6
- simulated_decision_artifacts: 4
- simulated_decision_record_links: 22
- simulated_decision_replay_links: 2
- validation_command_records: 2
- warnings: 0

## Replay Links
- pmbot-rehearsal-simulated-decision-replay-links-001.validation_replay_to_packet_and_audit | rehearsal artifacts: 2 | simulated decision artifacts: 2 | review: pending_operator_review
- pmbot-rehearsal-simulated-decision-replay-links-001.operator_review_artifacts_to_replay_summary | rehearsal artifacts: 3 | simulated decision artifacts: 2 | review: pending_operator_review

## Local References
- rehearsal_validation_replay_packet_fixture: `pm_bot/tests/fixtures/rehearsal/pmbot_rehearsal_validation_replay_packet.valid.json` | records: 12 | present: True
- rehearsal_ci_safe_validation_runner_fixture: `pm_bot/tests/fixtures/rehearsal/pmbot_rehearsal_ci_safe_validation_runner.valid.json` | records: 16 | present: True
- rehearsal_acceptance_report_document: `docs/PMBOT_REHEARSAL_013_REHEARSAL_ACCEPTANCE_REPORT_LOCAL_ONLY.md` | records: 1 | present: True
- rehearsal_source_quality_links_document: `docs/PMBOT_REHEARSAL_014_REHEARSAL_SOURCE_QUALITY_LINKS_LOCAL_ONLY.md` | records: 1 | present: True
- rehearsal_paperlive_accounting_links_document: `docs/PMBOT_REHEARSAL_015_REHEARSAL_PAPERLIVE_ACCOUNTING_LINKS_LOCAL_ONLY.md` | records: 1 | present: True
- simulated_decision_packet_sample: `pm_bot/simulated_decisions/samples/simulated_decision_packet.fixture.json` | records: 2 | present: True
- simulated_decision_audit_ledger_sample: `pm_bot/simulated_decisions/samples/simulated_decision_audit_ledger.fixture.json` | records: 5 | present: True
- simulated_decision_replay_summary_sample: `pm_bot/simulated_decisions/samples/simulated_decision_replay_summary.fixture.json` | records: 7 | present: True
- simulated_decision_outcome_replay_links_sample: `pm_bot/simulated_decisions/samples/simulated_decision_outcome_replay_links.fixture.json` | records: 8 | present: True

## Safety Boundary
- Local files, local fixtures, and static samples only.
- Makes no network, LLM, external market API, wallet, order, transaction endpoint, runtime, worker, scheduler, or browser calls.
- Descriptive replay link record only.
- Not execution approval and not runtime input.
