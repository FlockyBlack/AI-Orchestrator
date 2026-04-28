# PMBOT Dossier Human Review Records v1

## Summary

- task_id: PMBOT-RESEARCH-015-DOSSIER-HUMAN-REVIEW-RECORD-GATE
- source_review_records_path: pm_bot/research/dossier_human_review_records_fixture.v1.json
- source_review_pack_path: pm_bot/research/dossier_human_review_pack.v1.json
- source_validation_result_path: pm_bot/research/manual_dossier_draft_validation_result.v1.json
- source_dossier_skeletons_path: pm_bot/research/dossier_draft_skeletons.v1.json
- review_records_read: 10
- review_records_accepted: 1
- review_records_rejected: 9
- approved_for_final_dossier_draft: 1
- needs_draft_revision: 0
- rejected_for_research_quality: 0
- watch_only: 0
- errors_by_market_id:
  - 563650: 30
  - 569366: 1
  - 999999: 1

## Accepted Human Review Records

### record 0: 563650
- human_review_status: review_completed
- human_review_outcome: approved_for_final_dossier_draft
- review_pack_status: human_review_pack_only
- requested_revision_items_count: 0
- quality_flags_count: 0

## Rejected Human Review Records

### record 3: 563650
- human_review_status: not_reviewed
- human_review_outcome: watch_only
- review_pack_status: human_review_pack_only
- errors:
  - title_question: immutable_review_pack_field_override:title_question - title_question is immutable review pack content and cannot be supplied by a human review record.

### record 4: 563650
- human_review_status: needs_revision
- human_review_outcome: needs_draft_revision
- review_pack_status: human_review_pack_only
- errors:
  - execution: prohibited_human_review_field:execution - Trading, execution, recommendation, bet, stake, size, price, scoring, signal, probability, EV, wallet, private-key, side, buy, sell, and market-decision fields are prohibited in dossier human review records.
  - execution: unexpected_human_review_field:execution - execution is not an allowed human review record field.
  - execution.order: prohibited_human_review_field:order - Trading, execution, recommendation, bet, stake, size, price, scoring, signal, probability, EV, wallet, private-key, side, buy, sell, and market-decision fields are prohibited in dossier human review records.
  - recommendation: prohibited_human_review_field:recommendation - Trading, execution, recommendation, bet, stake, size, price, scoring, signal, probability, EV, wallet, private-key, side, buy, sell, and market-decision fields are prohibited in dossier human review records.
  - recommendation: unexpected_human_review_field:recommendation - recommendation is not an allowed human review record field.
  - trade: prohibited_human_review_field:trade - Trading, execution, recommendation, bet, stake, size, price, scoring, signal, probability, EV, wallet, private-key, side, buy, sell, and market-decision fields are prohibited in dossier human review records.
  - trade: unexpected_human_review_field:trade - trade is not an allowed human review record field.
  - wallet: prohibited_human_review_field:wallet - Trading, execution, recommendation, bet, stake, size, price, scoring, signal, probability, EV, wallet, private-key, side, buy, sell, and market-decision fields are prohibited in dossier human review records.
  - wallet: unexpected_human_review_field:wallet - wallet is not an allowed human review record field.

### record 5: 563650
- human_review_status: review_completed
- human_review_outcome: watch_only
- review_pack_status: human_review_pack_only
- errors:
  - ev: prohibited_human_review_field:ev - Trading, execution, recommendation, bet, stake, size, price, scoring, signal, probability, EV, wallet, private-key, side, buy, sell, and market-decision fields are prohibited in dossier human review records.
  - ev: unexpected_human_review_field:ev - ev is not an allowed human review record field.
  - expected_value: prohibited_human_review_field:expected_value - Trading, execution, recommendation, bet, stake, size, price, scoring, signal, probability, EV, wallet, private-key, side, buy, sell, and market-decision fields are prohibited in dossier human review records.
  - expected_value: unexpected_human_review_field:expected_value - expected_value is not an allowed human review record field.
  - market_decision: prohibited_dossier_language:market_decision - Completed/final dossier, recommendation, and market-decision language is prohibited in machine-readable human review record fields.
  - market_decision: prohibited_human_review_field:market_decision - Trading, execution, recommendation, bet, stake, size, price, scoring, signal, probability, EV, wallet, private-key, side, buy, sell, and market-decision fields are prohibited in dossier human review records.
  - market_decision: unexpected_human_review_field:market_decision - market_decision is not an allowed human review record field.
  - probability: prohibited_human_review_field:probability - Trading, execution, recommendation, bet, stake, size, price, scoring, signal, probability, EV, wallet, private-key, side, buy, sell, and market-decision fields are prohibited in dossier human review records.
  - probability: unexpected_human_review_field:probability - probability is not an allowed human review record field.
  - score: prohibited_human_review_field:score - Trading, execution, recommendation, bet, stake, size, price, scoring, signal, probability, EV, wallet, private-key, side, buy, sell, and market-decision fields are prohibited in dossier human review records.
  - score: unexpected_human_review_field:score - score is not an allowed human review record field.
  - side: prohibited_human_review_field:side - Trading, execution, recommendation, bet, stake, size, price, scoring, signal, probability, EV, wallet, private-key, side, buy, sell, and market-decision fields are prohibited in dossier human review records.
  - side: unexpected_human_review_field:side - side is not an allowed human review record field.
  - yes_no_decision: prohibited_human_review_field:yes_no_decision - Trading, execution, recommendation, bet, stake, size, price, scoring, signal, probability, EV, wallet, private-key, side, buy, sell, and market-decision fields are prohibited in dossier human review records.
  - yes_no_decision: unexpected_human_review_field:yes_no_decision - yes_no_decision is not an allowed human review record field.

### record 6: 563650
- human_review_status: review_completed
- human_review_outcome: approved_for_final_dossier_draft
- review_pack_status: human_review_pack_only
- errors:
  - review_checks.no_market_decision_present: required_approval_review_check_not_true:no_market_decision_present - review_checks.no_market_decision_present must be true before approved_for_final_dossier_draft can be accepted.
  - review_checks.no_probability_or_ev_present: required_approval_review_check_not_true:no_probability_or_ev_present - review_checks.no_probability_or_ev_present must be true before approved_for_final_dossier_draft can be accepted.

### record 7: 563650
- human_review_status: needs_revision
- human_review_outcome: needs_draft_revision
- review_pack_status: human_review_pack_only
- errors:
  - requested_revision_items: needs_draft_revision_requires_requested_revision_items - human_review_outcome needs_draft_revision requires non-empty requested_revision_items.

### record 8: 563650
- human_review_status: review_rejected
- human_review_outcome: rejected_for_research_quality
- review_pack_status: human_review_pack_only
- errors:
  - reviewer_notes: rejected_for_research_quality_requires_reviewer_notes - human_review_outcome rejected_for_research_quality requires non-empty reviewer_notes.

### record 9: 563650
- human_review_status: review_completed
- human_review_outcome: watch_only
- review_pack_status: human_review_pack_only
- errors:
  - reviewer_notes: prohibited_dossier_language:completed_dossier - Completed/final dossier, recommendation, and market-decision language is prohibited in machine-readable human review record fields.

### record 2: 569366
- human_review_status: review_completed
- human_review_outcome: watch_only
- review_pack_status: 
- errors:
  - market_id: non_review_pack_market_id - Human review record market_id is not present in dossier_human_review_pack.v1.json.

### record 1: 999999
- human_review_status: not_reviewed
- human_review_outcome: watch_only
- review_pack_status: 
- errors:
  - market_id: unknown_market_id - Human review record market_id is absent from the local dossier review pack, draft validation, and skeleton artifacts.

## Errors By Market ID

### 563650
- title_question: immutable_review_pack_field_override:title_question - title_question is immutable review pack content and cannot be supplied by a human review record.
- execution: prohibited_human_review_field:execution - Trading, execution, recommendation, bet, stake, size, price, scoring, signal, probability, EV, wallet, private-key, side, buy, sell, and market-decision fields are prohibited in dossier human review records.
- execution: unexpected_human_review_field:execution - execution is not an allowed human review record field.
- execution.order: prohibited_human_review_field:order - Trading, execution, recommendation, bet, stake, size, price, scoring, signal, probability, EV, wallet, private-key, side, buy, sell, and market-decision fields are prohibited in dossier human review records.
- recommendation: prohibited_human_review_field:recommendation - Trading, execution, recommendation, bet, stake, size, price, scoring, signal, probability, EV, wallet, private-key, side, buy, sell, and market-decision fields are prohibited in dossier human review records.
- recommendation: unexpected_human_review_field:recommendation - recommendation is not an allowed human review record field.
- trade: prohibited_human_review_field:trade - Trading, execution, recommendation, bet, stake, size, price, scoring, signal, probability, EV, wallet, private-key, side, buy, sell, and market-decision fields are prohibited in dossier human review records.
- trade: unexpected_human_review_field:trade - trade is not an allowed human review record field.
- wallet: prohibited_human_review_field:wallet - Trading, execution, recommendation, bet, stake, size, price, scoring, signal, probability, EV, wallet, private-key, side, buy, sell, and market-decision fields are prohibited in dossier human review records.
- wallet: unexpected_human_review_field:wallet - wallet is not an allowed human review record field.
- ev: prohibited_human_review_field:ev - Trading, execution, recommendation, bet, stake, size, price, scoring, signal, probability, EV, wallet, private-key, side, buy, sell, and market-decision fields are prohibited in dossier human review records.
- ev: unexpected_human_review_field:ev - ev is not an allowed human review record field.
- expected_value: prohibited_human_review_field:expected_value - Trading, execution, recommendation, bet, stake, size, price, scoring, signal, probability, EV, wallet, private-key, side, buy, sell, and market-decision fields are prohibited in dossier human review records.
- expected_value: unexpected_human_review_field:expected_value - expected_value is not an allowed human review record field.
- market_decision: prohibited_dossier_language:market_decision - Completed/final dossier, recommendation, and market-decision language is prohibited in machine-readable human review record fields.
- market_decision: prohibited_human_review_field:market_decision - Trading, execution, recommendation, bet, stake, size, price, scoring, signal, probability, EV, wallet, private-key, side, buy, sell, and market-decision fields are prohibited in dossier human review records.
- market_decision: unexpected_human_review_field:market_decision - market_decision is not an allowed human review record field.
- probability: prohibited_human_review_field:probability - Trading, execution, recommendation, bet, stake, size, price, scoring, signal, probability, EV, wallet, private-key, side, buy, sell, and market-decision fields are prohibited in dossier human review records.
- probability: unexpected_human_review_field:probability - probability is not an allowed human review record field.
- score: prohibited_human_review_field:score - Trading, execution, recommendation, bet, stake, size, price, scoring, signal, probability, EV, wallet, private-key, side, buy, sell, and market-decision fields are prohibited in dossier human review records.
- score: unexpected_human_review_field:score - score is not an allowed human review record field.
- side: prohibited_human_review_field:side - Trading, execution, recommendation, bet, stake, size, price, scoring, signal, probability, EV, wallet, private-key, side, buy, sell, and market-decision fields are prohibited in dossier human review records.
- side: unexpected_human_review_field:side - side is not an allowed human review record field.
- yes_no_decision: prohibited_human_review_field:yes_no_decision - Trading, execution, recommendation, bet, stake, size, price, scoring, signal, probability, EV, wallet, private-key, side, buy, sell, and market-decision fields are prohibited in dossier human review records.
- yes_no_decision: unexpected_human_review_field:yes_no_decision - yes_no_decision is not an allowed human review record field.
- review_checks.no_market_decision_present: required_approval_review_check_not_true:no_market_decision_present - review_checks.no_market_decision_present must be true before approved_for_final_dossier_draft can be accepted.
- review_checks.no_probability_or_ev_present: required_approval_review_check_not_true:no_probability_or_ev_present - review_checks.no_probability_or_ev_present must be true before approved_for_final_dossier_draft can be accepted.
- requested_revision_items: needs_draft_revision_requires_requested_revision_items - human_review_outcome needs_draft_revision requires non-empty requested_revision_items.
- reviewer_notes: rejected_for_research_quality_requires_reviewer_notes - human_review_outcome rejected_for_research_quality requires non-empty reviewer_notes.
- reviewer_notes: prohibited_dossier_language:completed_dossier - Completed/final dossier, recommendation, and market-decision language is prohibited in machine-readable human review record fields.

### 569366
- market_id: non_review_pack_market_id - Human review record market_id is not present in dossier_human_review_pack.v1.json.

### 999999
- market_id: unknown_market_id - Human review record market_id is absent from the local dossier review pack, draft validation, and skeleton artifacts.

## Limitations

- Reads only local human review records, dossier review packs, draft validation, and skeleton artifacts.
- Validates human review record structure and operational review labels only.
- Does not create final or completed dossiers, infer truth, score markets, estimate probabilities or EV, recommend sides, create orders, or route runtime work.
