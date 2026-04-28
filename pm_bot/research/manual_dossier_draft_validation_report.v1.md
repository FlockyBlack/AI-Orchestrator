# PMBOT Manual Dossier Draft Validation v1

## Summary

- task_id: PMBOT-RESEARCH-013-MANUAL-DOSSIER-DRAFT-QUALITY-GATE
- source_draft_records_path: pm_bot/research/manual_dossier_drafts_fixture.v1.json
- source_dossier_skeletons_path: pm_bot/research/dossier_draft_skeletons.v1.json
- source_review_records_result_path: pm_bot/research/operator_review_records_result.v1.json
- source_merged_packets_path: pm_bot/research/merged_manual_research_packets.v1.json
- draft_records_read: 8
- draft_records_accepted: 1
- draft_records_rejected: 7
- draft_ready_for_human_review: 1
- needs_more_information: 0
- draft_incomplete: 0
- draft_rejected: 0
- errors_by_market_id:
  - 563650: 29
  - 569366: 1
  - unknown-market-id: 1

## Accepted Draft Records

### record 0: 563650
- draft_status: draft_ready_for_human_review
- next_manual_action: human_review_required
- evidence_summary_by_source_count: 3
- uncertainty_register_count: 2
- open_questions_count: 1

## Rejected Draft Records

### record 3: 563650
- draft_status: draft_incomplete
- next_manual_action: fix_draft_structure
- errors:
  - title_question: immutable_skeleton_field_override:title_question - title_question is immutable skeleton content and cannot be supplied by a manual dossier draft.

### record 4: 563650
- draft_status: draft_incomplete
- next_manual_action: fix_draft_structure
- errors:
  - execution: prohibited_draft_field:execution - Trading, execution, recommendation, bet, stake, size, price, scoring, signal, probability, EV, wallet, private-key, side, buy, and sell fields are prohibited in manual dossier drafts.
  - execution: unexpected_draft_field:execution - execution is not an allowed manual dossier draft field.
  - execution.order: prohibited_draft_field:order - Trading, execution, recommendation, bet, stake, size, price, scoring, signal, probability, EV, wallet, private-key, side, buy, and sell fields are prohibited in manual dossier drafts.
  - recommendation: prohibited_draft_field:recommendation - Trading, execution, recommendation, bet, stake, size, price, scoring, signal, probability, EV, wallet, private-key, side, buy, and sell fields are prohibited in manual dossier drafts.
  - recommendation: unexpected_draft_field:recommendation - recommendation is not an allowed manual dossier draft field.
  - trade: prohibited_draft_field:trade - Trading, execution, recommendation, bet, stake, size, price, scoring, signal, probability, EV, wallet, private-key, side, buy, and sell fields are prohibited in manual dossier drafts.
  - trade: unexpected_draft_field:trade - trade is not an allowed manual dossier draft field.
  - wallet: prohibited_draft_field:wallet - Trading, execution, recommendation, bet, stake, size, price, scoring, signal, probability, EV, wallet, private-key, side, buy, and sell fields are prohibited in manual dossier drafts.
  - wallet: unexpected_draft_field:wallet - wallet is not an allowed manual dossier draft field.

### record 5: 563650
- draft_status: draft_incomplete
- next_manual_action: fix_draft_structure
- errors:
  - ev: prohibited_draft_field:ev - Trading, execution, recommendation, bet, stake, size, price, scoring, signal, probability, EV, wallet, private-key, side, buy, and sell fields are prohibited in manual dossier drafts.
  - ev: unexpected_draft_field:ev - ev is not an allowed manual dossier draft field.
  - expected_value: prohibited_draft_field:expected_value - Trading, execution, recommendation, bet, stake, size, price, scoring, signal, probability, EV, wallet, private-key, side, buy, and sell fields are prohibited in manual dossier drafts.
  - expected_value: unexpected_draft_field:expected_value - expected_value is not an allowed manual dossier draft field.
  - probability: prohibited_draft_field:probability - Trading, execution, recommendation, bet, stake, size, price, scoring, signal, probability, EV, wallet, private-key, side, buy, and sell fields are prohibited in manual dossier drafts.
  - probability: unexpected_draft_field:probability - probability is not an allowed manual dossier draft field.
  - score: prohibited_draft_field:score - Trading, execution, recommendation, bet, stake, size, price, scoring, signal, probability, EV, wallet, private-key, side, buy, and sell fields are prohibited in manual dossier drafts.
  - score: unexpected_draft_field:score - score is not an allowed manual dossier draft field.
  - side: prohibited_draft_field:side - Trading, execution, recommendation, bet, stake, size, price, scoring, signal, probability, EV, wallet, private-key, side, buy, and sell fields are prohibited in manual dossier drafts.
  - side: unexpected_draft_field:side - side is not an allowed manual dossier draft field.
  - yes_no_decision: prohibited_draft_field:yes_no_decision - Trading, execution, recommendation, bet, stake, size, price, scoring, signal, probability, EV, wallet, private-key, side, buy, and sell fields are prohibited in manual dossier drafts.
  - yes_no_decision: unexpected_draft_field:yes_no_decision - yes_no_decision is not an allowed manual dossier draft field.

### record 6: 563650
- draft_status: draft_ready_for_human_review
- next_manual_action: human_review_required
- errors:
  - evidence_summary_by_source: required_ready_section_empty:evidence_summary_by_source - evidence_summary_by_source is required and must be non-empty for draft_ready_for_human_review.
  - market_context_notes: required_ready_section_empty:market_context_notes - market_context_notes is required and must be non-empty for draft_ready_for_human_review.
  - missing_information_review: required_ready_section_empty:missing_information_review - missing_information_review is required and must be non-empty for draft_ready_for_human_review.
  - operator_review_notes: required_ready_section_empty:operator_review_notes - operator_review_notes is required and must be non-empty for draft_ready_for_human_review.
  - resolution_criteria_notes: required_ready_section_empty:resolution_criteria_notes - resolution_criteria_notes is required and must be non-empty for draft_ready_for_human_review.
  - uncertainty_register: required_ready_section_empty:uncertainty_register - uncertainty_register is required and must be non-empty for draft_ready_for_human_review.

### record 7: 563650
- draft_status: draft_incomplete
- next_manual_action: fix_draft_structure
- errors:
  - operator_review_notes: prohibited_dossier_language:completed_dossier - Completed/final dossier, recommendation, and market-decision language is prohibited in machine-readable manual draft fields.

### record 2: 569366
- draft_status: needs_more_information
- next_manual_action: add_missing_information
- errors:
  - market_id: non_skeleton_market_id - Manual dossier draft market_id was not exported as a RESEARCH-012 dossier draft skeleton.

### record 1: unknown-market-id
- draft_status: draft_incomplete
- next_manual_action: fix_draft_structure
- errors:
  - market_id: unknown_market_id - Manual dossier draft market_id is absent from the local skeleton, review, and merged-packet artifacts.

## Errors By Market ID

### 563650
- title_question: immutable_skeleton_field_override:title_question - title_question is immutable skeleton content and cannot be supplied by a manual dossier draft.
- execution: prohibited_draft_field:execution - Trading, execution, recommendation, bet, stake, size, price, scoring, signal, probability, EV, wallet, private-key, side, buy, and sell fields are prohibited in manual dossier drafts.
- execution: unexpected_draft_field:execution - execution is not an allowed manual dossier draft field.
- execution.order: prohibited_draft_field:order - Trading, execution, recommendation, bet, stake, size, price, scoring, signal, probability, EV, wallet, private-key, side, buy, and sell fields are prohibited in manual dossier drafts.
- recommendation: prohibited_draft_field:recommendation - Trading, execution, recommendation, bet, stake, size, price, scoring, signal, probability, EV, wallet, private-key, side, buy, and sell fields are prohibited in manual dossier drafts.
- recommendation: unexpected_draft_field:recommendation - recommendation is not an allowed manual dossier draft field.
- trade: prohibited_draft_field:trade - Trading, execution, recommendation, bet, stake, size, price, scoring, signal, probability, EV, wallet, private-key, side, buy, and sell fields are prohibited in manual dossier drafts.
- trade: unexpected_draft_field:trade - trade is not an allowed manual dossier draft field.
- wallet: prohibited_draft_field:wallet - Trading, execution, recommendation, bet, stake, size, price, scoring, signal, probability, EV, wallet, private-key, side, buy, and sell fields are prohibited in manual dossier drafts.
- wallet: unexpected_draft_field:wallet - wallet is not an allowed manual dossier draft field.
- ev: prohibited_draft_field:ev - Trading, execution, recommendation, bet, stake, size, price, scoring, signal, probability, EV, wallet, private-key, side, buy, and sell fields are prohibited in manual dossier drafts.
- ev: unexpected_draft_field:ev - ev is not an allowed manual dossier draft field.
- expected_value: prohibited_draft_field:expected_value - Trading, execution, recommendation, bet, stake, size, price, scoring, signal, probability, EV, wallet, private-key, side, buy, and sell fields are prohibited in manual dossier drafts.
- expected_value: unexpected_draft_field:expected_value - expected_value is not an allowed manual dossier draft field.
- probability: prohibited_draft_field:probability - Trading, execution, recommendation, bet, stake, size, price, scoring, signal, probability, EV, wallet, private-key, side, buy, and sell fields are prohibited in manual dossier drafts.
- probability: unexpected_draft_field:probability - probability is not an allowed manual dossier draft field.
- score: prohibited_draft_field:score - Trading, execution, recommendation, bet, stake, size, price, scoring, signal, probability, EV, wallet, private-key, side, buy, and sell fields are prohibited in manual dossier drafts.
- score: unexpected_draft_field:score - score is not an allowed manual dossier draft field.
- side: prohibited_draft_field:side - Trading, execution, recommendation, bet, stake, size, price, scoring, signal, probability, EV, wallet, private-key, side, buy, and sell fields are prohibited in manual dossier drafts.
- side: unexpected_draft_field:side - side is not an allowed manual dossier draft field.
- yes_no_decision: prohibited_draft_field:yes_no_decision - Trading, execution, recommendation, bet, stake, size, price, scoring, signal, probability, EV, wallet, private-key, side, buy, and sell fields are prohibited in manual dossier drafts.
- yes_no_decision: unexpected_draft_field:yes_no_decision - yes_no_decision is not an allowed manual dossier draft field.
- evidence_summary_by_source: required_ready_section_empty:evidence_summary_by_source - evidence_summary_by_source is required and must be non-empty for draft_ready_for_human_review.
- market_context_notes: required_ready_section_empty:market_context_notes - market_context_notes is required and must be non-empty for draft_ready_for_human_review.
- missing_information_review: required_ready_section_empty:missing_information_review - missing_information_review is required and must be non-empty for draft_ready_for_human_review.
- operator_review_notes: required_ready_section_empty:operator_review_notes - operator_review_notes is required and must be non-empty for draft_ready_for_human_review.
- resolution_criteria_notes: required_ready_section_empty:resolution_criteria_notes - resolution_criteria_notes is required and must be non-empty for draft_ready_for_human_review.
- uncertainty_register: required_ready_section_empty:uncertainty_register - uncertainty_register is required and must be non-empty for draft_ready_for_human_review.
- operator_review_notes: prohibited_dossier_language:completed_dossier - Completed/final dossier, recommendation, and market-decision language is prohibited in machine-readable manual draft fields.

### 569366
- market_id: non_skeleton_market_id - Manual dossier draft market_id was not exported as a RESEARCH-012 dossier draft skeleton.

### unknown-market-id
- market_id: unknown_market_id - Manual dossier draft market_id is absent from the local skeleton, review, and merged-packet artifacts.

## Limitations

- Reads only local manual draft, skeleton, review-result, and merged-packet artifacts.
- Validates structure and operational next-action labels only.
- Does not resolve markets, infer outcomes, score markets, create orders, or route runtime work.
