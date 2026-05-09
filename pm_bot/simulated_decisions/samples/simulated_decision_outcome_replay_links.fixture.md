# PMBOT Simulated Decision To Outcome Replay Links

Links: `simulated_decision_outcome_replay_links_fixture_001`
Build: `simulated_decision_outcome_replay_links_fixture_001-4a5042fa723e`
Run mode: `offline_recordkeeping`
Operator review: `pending_operator_review`

## Summary Counts
- source_summaries: 1
- source_packets: 1
- outcome_artifacts: 1
- decision_to_outcome_links: 1
- local_references: 2
- link_requirements: 3
- warnings: 0
- errors: 0

## Link Rows
- simulated_decision_packet_fixture_001 -> weather_outcome_reconciliation_request_fixture_001 | records: 2 | review: pending_operator_review

## Local References
- source_replay_summary: `pm_bot/simulated_decisions/samples/simulated_decision_replay_summary.fixture.json` | exists: True
- weather_outcome_reconciliation_request: `pm_bot/tests/fixtures/weather_outcome_reconciliation_request.valid.json` | exists: True

## Safety Boundary
- Local fixture/static input only.
- Makes no network, LLM, external market API, wallet, order, transaction endpoint, runtime, worker, scheduler, or browser calls.
- Descriptive replay-link record only; not runtime input or execution approval.
- Leaves any final outcome record outside this artifact.
