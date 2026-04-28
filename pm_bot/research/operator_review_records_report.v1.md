# PMBOT Operator Review Records v1

## Summary

- task_id: PMBOT-RESEARCH-011-OPERATOR-REVIEW-RECORD-GATE
- source_review_records_path: pm_bot/research/operator_review_records_fixture.v1.json
- source_operator_review_queue_path: pm_bot/research/operator_review_queue.v1.json
- source_merged_packets_path: pm_bot/research/merged_manual_research_packets.v1.json
- review_records_read: 8
- review_records_accepted: 3
- review_records_rejected: 5
- ready_for_dossier_drafting: 1
- needs_more_information: 1
- research_quality_rejected: 0
- watch_only_manual: 1
- errors_by_market_id:
  - 569332: 1
  - 569333: 1
  - 569343: 3
  - 569344: 1
  - unknown-market-id: 1

## Accepted Review Records

### 563650
- review_status: review_completed
- review_outcome: ready_for_dossier_drafting
- queue_group: ready_for_operator_review
- packet_completion_status: ready_for_operator_review

### 569366
- review_status: needs_more_information
- review_outcome: needs_more_information
- queue_group: needs_more_information
- packet_completion_status: needs_more_information

### 573656
- review_status: not_reviewed
- review_outcome: watch_only_manual
- queue_group: stub_only
- packet_completion_status: stub_only

## Rejected Review Records

### 569332
- review_status: review_completed
- review_outcome: watch_only_manual
- queue_group: stub_only
- packet_completion_status: stub_only
- errors:
  - title: immutable_packet_field_override:title - title is immutable packet or queue content and cannot be supplied by an operator review record.

### 569333
- review_status: needs_more_information
- review_outcome: needs_more_information
- queue_group: stub_only
- packet_completion_status: stub_only
- errors:
  - requested_followup_information: needs_more_information_requires_followup - review_outcome needs_more_information requires non-empty requested_followup_information.

### 569343
- review_status: review_completed
- review_outcome: watch_only_manual
- queue_group: stub_only
- packet_completion_status: stub_only
- errors:
  - recommendation: prohibited_review_field:recommendation - Trading, execution, recommendation, bet, stake, target, scoring, probability, signal, wallet, private-key, and side fields are prohibited in operator review records.
  - recommendation: unexpected_review_field:recommendation - recommendation is not an allowed operator review record field.
  - review_checks.probability: prohibited_review_field:probability - Trading, execution, recommendation, bet, stake, target, scoring, probability, signal, wallet, private-key, and side fields are prohibited in operator review records.

### 569344
- review_status: review_completed
- review_outcome: ready_for_dossier_drafting
- queue_group: stub_only
- packet_completion_status: stub_only
- errors:
  - review_outcome: ready_outcome_requires_ready_queue_group - ready_for_dossier_drafting is allowed only for queue group ready_for_operator_review; current group is stub_only.

### unknown-market-id
- review_status: review_completed
- review_outcome: watch_only_manual
- queue_group: 
- packet_completion_status: 
- errors:
  - market_id: unknown_market_id - Review record market_id is not present in the operator review queue and merged packet set.

## Errors By Market ID

### 569332
- title: immutable_packet_field_override:title - title is immutable packet or queue content and cannot be supplied by an operator review record.

### 569333
- requested_followup_information: needs_more_information_requires_followup - review_outcome needs_more_information requires non-empty requested_followup_information.

### 569343
- recommendation: prohibited_review_field:recommendation - Trading, execution, recommendation, bet, stake, target, scoring, probability, signal, wallet, private-key, and side fields are prohibited in operator review records.
- recommendation: unexpected_review_field:recommendation - recommendation is not an allowed operator review record field.
- review_checks.probability: prohibited_review_field:probability - Trading, execution, recommendation, bet, stake, target, scoring, probability, signal, wallet, private-key, and side fields are prohibited in operator review records.

### 569344
- review_outcome: ready_outcome_requires_ready_queue_group - ready_for_dossier_drafting is allowed only for queue group ready_for_operator_review; current group is stub_only.

### unknown-market-id
- market_id: unknown_market_id - Review record market_id is not present in the operator review queue and merged packet set.

## Limitations

- Reads only local operator review records, operator review queue, and merged manual research packets.
- Records structural operator review outcomes only.
- Does not create dossiers, scores, recommendations, orders, runtime actions, or market conclusions.
