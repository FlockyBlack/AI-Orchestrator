# PAPER-006 Human Review Record Gate

- task_id: PMBOT-PAPER-BATCH-006-010-PAPER-WORKBENCH-MVP
- source_gate_path: pm_bot/paper/paper_decision_simulation_gate.v1.json
- records_accepted: 1
- records_rejected: 3
- created_action_count: 0

## Accepted

- human-review-001: market_id=824952 review_outcome=approved_for_paper_simulation_plan_drafting

## Rejected

- human-review-rejected-prohibited-field: market_id=824952 reasons=prohibited_or_execution_field_present,unexpected_field_present
- human-review-rejected-unknown-market: market_id=000000 reasons=unknown_market_id
- human-review-rejected-unknown-outcome: market_id=824952 reasons=unknown_review_outcome

## Safety

- Offline local review gate only.
- Rejected rows are summarized without authorizing executable action.
