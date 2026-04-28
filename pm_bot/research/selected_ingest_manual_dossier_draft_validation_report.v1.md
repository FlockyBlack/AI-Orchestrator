# Selected Ingest Manual Dossier Draft Validation v1

## Summary

- task_id: PMBOT-INGEST-011-SELECTED-INGEST-MANUAL-DOSSIER-DRAFT-QUALITY-GATE
- source_draft_records_path: pm_bot/research/selected_ingest_manual_dossier_drafts_fixture.v1.json
- source_dossier_skeletons_path: pm_bot/research/selected_ingest_dossier_draft_skeletons.v1.json
- source_review_records_result_path: pm_bot/research/selected_ingest_operator_review_records_result.v1.json
- source_merged_packets_path: pm_bot/research/selected_ingest_merged_manual_research_packets.v1.json
- draft_records_read: 7
- draft_records_accepted: 1
- draft_records_rejected: 6
- draft_ready_for_human_review: 1
- needs_more_information: 0
- draft_incomplete: 0
- draft_rejected: 0
- errors_by_market_id:
  - 692258: 1
  - 824952: 56
  - unknown-market-id: 1

## Selected Market IDs

- 692258
- 824952
- 691547
- 597964
- 598936

## Exported Dossier Draft Skeleton Market IDs

- 824952

## Accepted Draft Records

### record 0: 824952
- draft_status: draft_ready_for_human_review
- next_manual_action: human_review_required
- evidence_summary_by_source_count: 3
- uncertainty_register_count: 2
- open_questions_count: 0

## Rejected Draft Records

### record 1: 692258
- draft_status: needs_more_information
- next_manual_action: add_missing_information
- errors:
  - market_id: non_skeleton_market_id - Selected-ingest manual dossier draft market_id was selected but was not exported as a dossier draft skeleton.

### record 3: 824952
- draft_status: draft_incomplete
- next_manual_action: fix_draft_structure
- errors:
  - title_question: immutable_skeleton_field_override:title_question - title_question is immutable skeleton content and cannot be supplied by a manual dossier draft.

### record 4: 824952
- draft_status: draft_incomplete
- next_manual_action: reject_draft_quality
- errors:
  - bet: prohibited_draft_field:bet - Trading, execution, recommendation, bet, stake, size, price, scoring, signal, probability, EV, wallet, private-key, side, buy/sell, and market-decision fields are prohibited.
  - bet: unexpected_draft_field:bet - bet is not an allowed selected-ingest manual dossier draft field.
  - entry_price: prohibited_draft_field:entry_price - Trading, execution, recommendation, bet, stake, size, price, scoring, signal, probability, EV, wallet, private-key, side, buy/sell, and market-decision fields are prohibited.
  - entry_price: unexpected_draft_field:entry_price - entry_price is not an allowed selected-ingest manual dossier draft field.
  - execution: prohibited_draft_field:execution - Trading, execution, recommendation, bet, stake, size, price, scoring, signal, probability, EV, wallet, private-key, side, buy/sell, and market-decision fields are prohibited.
  - execution: unexpected_draft_field:execution - execution is not an allowed selected-ingest manual dossier draft field.
  - limit_price: prohibited_draft_field:limit_price - Trading, execution, recommendation, bet, stake, size, price, scoring, signal, probability, EV, wallet, private-key, side, buy/sell, and market-decision fields are prohibited.
  - limit_price: unexpected_draft_field:limit_price - limit_price is not an allowed selected-ingest manual dossier draft field.
  - order: prohibited_draft_field:order - Trading, execution, recommendation, bet, stake, size, price, scoring, signal, probability, EV, wallet, private-key, side, buy/sell, and market-decision fields are prohibited.
  - order: unexpected_draft_field:order - order is not an allowed selected-ingest manual dossier draft field.
  - price_target: prohibited_draft_field:price_target - Trading, execution, recommendation, bet, stake, size, price, scoring, signal, probability, EV, wallet, private-key, side, buy/sell, and market-decision fields are prohibited.
  - price_target: unexpected_draft_field:price_target - price_target is not an allowed selected-ingest manual dossier draft field.
  - Private-key field violation: prohibited_draft_field(private-key-field) - Trading, execution, recommendation, bet, stake, size, price, scoring, signal, probability, EV, wallet, private-key, side, buy/sell, and market-decision fields are prohibited.
  - Private-key field violation: unexpected_draft_field(private-key-field) - The private-key field is not an allowed selected-ingest manual dossier draft field.
  - recommendation: prohibited_draft_field:recommendation - Trading, execution, recommendation, bet, stake, size, price, scoring, signal, probability, EV, wallet, private-key, side, buy/sell, and market-decision fields are prohibited.
  - recommendation: unexpected_draft_field:recommendation - recommendation is not an allowed selected-ingest manual dossier draft field.
  - size: prohibited_draft_field:size - Trading, execution, recommendation, bet, stake, size, price, scoring, signal, probability, EV, wallet, private-key, side, buy/sell, and market-decision fields are prohibited.
  - size: unexpected_draft_field:size - size is not an allowed selected-ingest manual dossier draft field.
  - stake: prohibited_draft_field:stake - Trading, execution, recommendation, bet, stake, size, price, scoring, signal, probability, EV, wallet, private-key, side, buy/sell, and market-decision fields are prohibited.
  - stake: unexpected_draft_field:stake - stake is not an allowed selected-ingest manual dossier draft field.
  - trade: prohibited_draft_field:trade - Trading, execution, recommendation, bet, stake, size, price, scoring, signal, probability, EV, wallet, private-key, side, buy/sell, and market-decision fields are prohibited.
  - trade: unexpected_draft_field:trade - trade is not an allowed selected-ingest manual dossier draft field.
  - wallet: prohibited_draft_field:wallet - Trading, execution, recommendation, bet, stake, size, price, scoring, signal, probability, EV, wallet, private-key, side, buy/sell, and market-decision fields are prohibited.
  - wallet: unexpected_draft_field:wallet - wallet is not an allowed selected-ingest manual dossier draft field.

### record 5: 824952
- draft_status: draft_ready_for_human_review
- next_manual_action: human_review_required
- errors:
  - evidence_summary_by_source: required_ready_section_empty:evidence_summary_by_source - evidence_summary_by_source is required and must be non-empty for draft_ready_for_human_review.
  - market_context_notes: required_ready_section_empty:market_context_notes - market_context_notes is required and must be non-empty for draft_ready_for_human_review.
  - missing_information_review: required_ready_section_empty:missing_information_review - missing_information_review is required and must be non-empty for draft_ready_for_human_review.
  - operator_review_notes: required_ready_section_empty:operator_review_notes - operator_review_notes is required and must be non-empty for draft_ready_for_human_review.
  - resolution_criteria_notes: required_ready_section_empty:resolution_criteria_notes - resolution_criteria_notes is required and must be non-empty for draft_ready_for_human_review.
  - uncertainty_register: required_ready_section_empty:uncertainty_register - uncertainty_register is required and must be non-empty for draft_ready_for_human_review.

### record 6: 824952
- draft_status: draft_incomplete
- next_manual_action: reject_draft_quality
- errors:
  - buy: prohibited_draft_field:buy - Trading, execution, recommendation, bet, stake, size, price, scoring, signal, probability, EV, wallet, private-key, side, buy/sell, and market-decision fields are prohibited.
  - buy: unexpected_draft_field:buy - buy is not an allowed selected-ingest manual dossier draft field.
  - ev: prohibited_draft_field:ev - Trading, execution, recommendation, bet, stake, size, price, scoring, signal, probability, EV, wallet, private-key, side, buy/sell, and market-decision fields are prohibited.
  - ev: unexpected_draft_field:ev - ev is not an allowed selected-ingest manual dossier draft field.
  - expected_value: prohibited_draft_field:expected_value - Trading, execution, recommendation, bet, stake, size, price, scoring, signal, probability, EV, wallet, private-key, side, buy/sell, and market-decision fields are prohibited.
  - expected_value: unexpected_draft_field:expected_value - expected_value is not an allowed selected-ingest manual dossier draft field.
  - market_context_notes: prohibited_dossier_language:completed_dossier - Completed/final dossier, recommendation, and market-decision language is prohibited in machine-readable manual draft fields.
  - market_decision: prohibited_dossier_language:market_decision - Completed/final dossier, recommendation, and market-decision language is prohibited in machine-readable manual draft fields.
  - market_decision: prohibited_draft_field:market_decision - Trading, execution, recommendation, bet, stake, size, price, scoring, signal, probability, EV, wallet, private-key, side, buy/sell, and market-decision fields are prohibited.
  - market_decision: unexpected_draft_field:market_decision - market_decision is not an allowed selected-ingest manual dossier draft field.
  - missing_information_review: prohibited_dossier_language:bet_recommendation - Completed/final dossier, recommendation, and market-decision language is prohibited in machine-readable manual draft fields.
  - operator_review_notes: prohibited_dossier_language:trade_recommendation - Completed/final dossier, recommendation, and market-decision language is prohibited in machine-readable manual draft fields.
  - probability: prohibited_draft_field:probability - Trading, execution, recommendation, bet, stake, size, price, scoring, signal, probability, EV, wallet, private-key, side, buy/sell, and market-decision fields are prohibited.
  - probability: unexpected_draft_field:probability - probability is not an allowed selected-ingest manual dossier draft field.
  - resolution_criteria_notes: prohibited_dossier_language:final_dossier - Completed/final dossier, recommendation, and market-decision language is prohibited in machine-readable manual draft fields.
  - score: prohibited_draft_field:score - Trading, execution, recommendation, bet, stake, size, price, scoring, signal, probability, EV, wallet, private-key, side, buy/sell, and market-decision fields are prohibited.
  - score: unexpected_draft_field:score - score is not an allowed selected-ingest manual dossier draft field.
  - sell: prohibited_draft_field:sell - Trading, execution, recommendation, bet, stake, size, price, scoring, signal, probability, EV, wallet, private-key, side, buy/sell, and market-decision fields are prohibited.
  - sell: unexpected_draft_field:sell - sell is not an allowed selected-ingest manual dossier draft field.
  - side: prohibited_draft_field:side - Trading, execution, recommendation, bet, stake, size, price, scoring, signal, probability, EV, wallet, private-key, side, buy/sell, and market-decision fields are prohibited.
  - side: unexpected_draft_field:side - side is not an allowed selected-ingest manual dossier draft field.
  - signal: prohibited_draft_field:signal - Trading, execution, recommendation, bet, stake, size, price, scoring, signal, probability, EV, wallet, private-key, side, buy/sell, and market-decision fields are prohibited.
  - signal: unexpected_draft_field:signal - signal is not an allowed selected-ingest manual dossier draft field.
  - yes_no_decision: prohibited_draft_field:yes_no_decision - Trading, execution, recommendation, bet, stake, size, price, scoring, signal, probability, EV, wallet, private-key, side, buy/sell, and market-decision fields are prohibited.
  - yes_no_decision: unexpected_draft_field:yes_no_decision - yes_no_decision is not an allowed selected-ingest manual dossier draft field.

### record 2: unknown-market-id
- draft_status: draft_incomplete
- next_manual_action: fix_draft_structure
- errors:
  - market_id: unknown_market_id - Selected-ingest manual dossier draft market_id is absent from selected_ingest_dossier_draft_skeletons.v1.json selected_market_ids.

## Errors By Market ID

### 692258
- market_id: non_skeleton_market_id - Selected-ingest manual dossier draft market_id was selected but was not exported as a dossier draft skeleton.

### 824952
- title_question: immutable_skeleton_field_override:title_question - title_question is immutable skeleton content and cannot be supplied by a manual dossier draft.
- bet: prohibited_draft_field:bet - Trading, execution, recommendation, bet, stake, size, price, scoring, signal, probability, EV, wallet, private-key, side, buy/sell, and market-decision fields are prohibited.
- bet: unexpected_draft_field:bet - bet is not an allowed selected-ingest manual dossier draft field.
- entry_price: prohibited_draft_field:entry_price - Trading, execution, recommendation, bet, stake, size, price, scoring, signal, probability, EV, wallet, private-key, side, buy/sell, and market-decision fields are prohibited.
- entry_price: unexpected_draft_field:entry_price - entry_price is not an allowed selected-ingest manual dossier draft field.
- execution: prohibited_draft_field:execution - Trading, execution, recommendation, bet, stake, size, price, scoring, signal, probability, EV, wallet, private-key, side, buy/sell, and market-decision fields are prohibited.
- execution: unexpected_draft_field:execution - execution is not an allowed selected-ingest manual dossier draft field.
- limit_price: prohibited_draft_field:limit_price - Trading, execution, recommendation, bet, stake, size, price, scoring, signal, probability, EV, wallet, private-key, side, buy/sell, and market-decision fields are prohibited.
- limit_price: unexpected_draft_field:limit_price - limit_price is not an allowed selected-ingest manual dossier draft field.
- order: prohibited_draft_field:order - Trading, execution, recommendation, bet, stake, size, price, scoring, signal, probability, EV, wallet, private-key, side, buy/sell, and market-decision fields are prohibited.
- order: unexpected_draft_field:order - order is not an allowed selected-ingest manual dossier draft field.
- price_target: prohibited_draft_field:price_target - Trading, execution, recommendation, bet, stake, size, price, scoring, signal, probability, EV, wallet, private-key, side, buy/sell, and market-decision fields are prohibited.
- price_target: unexpected_draft_field:price_target - price_target is not an allowed selected-ingest manual dossier draft field.
- Private-key field violation: prohibited_draft_field(private-key-field) - Trading, execution, recommendation, bet, stake, size, price, scoring, signal, probability, EV, wallet, private-key, side, buy/sell, and market-decision fields are prohibited.
- Private-key field violation: unexpected_draft_field(private-key-field) - The private-key field is not an allowed selected-ingest manual dossier draft field.
- recommendation: prohibited_draft_field:recommendation - Trading, execution, recommendation, bet, stake, size, price, scoring, signal, probability, EV, wallet, private-key, side, buy/sell, and market-decision fields are prohibited.
- recommendation: unexpected_draft_field:recommendation - recommendation is not an allowed selected-ingest manual dossier draft field.
- size: prohibited_draft_field:size - Trading, execution, recommendation, bet, stake, size, price, scoring, signal, probability, EV, wallet, private-key, side, buy/sell, and market-decision fields are prohibited.
- size: unexpected_draft_field:size - size is not an allowed selected-ingest manual dossier draft field.
- stake: prohibited_draft_field:stake - Trading, execution, recommendation, bet, stake, size, price, scoring, signal, probability, EV, wallet, private-key, side, buy/sell, and market-decision fields are prohibited.
- stake: unexpected_draft_field:stake - stake is not an allowed selected-ingest manual dossier draft field.
- trade: prohibited_draft_field:trade - Trading, execution, recommendation, bet, stake, size, price, scoring, signal, probability, EV, wallet, private-key, side, buy/sell, and market-decision fields are prohibited.
- trade: unexpected_draft_field:trade - trade is not an allowed selected-ingest manual dossier draft field.
- wallet: prohibited_draft_field:wallet - Trading, execution, recommendation, bet, stake, size, price, scoring, signal, probability, EV, wallet, private-key, side, buy/sell, and market-decision fields are prohibited.
- wallet: unexpected_draft_field:wallet - wallet is not an allowed selected-ingest manual dossier draft field.
- evidence_summary_by_source: required_ready_section_empty:evidence_summary_by_source - evidence_summary_by_source is required and must be non-empty for draft_ready_for_human_review.
- market_context_notes: required_ready_section_empty:market_context_notes - market_context_notes is required and must be non-empty for draft_ready_for_human_review.
- missing_information_review: required_ready_section_empty:missing_information_review - missing_information_review is required and must be non-empty for draft_ready_for_human_review.
- operator_review_notes: required_ready_section_empty:operator_review_notes - operator_review_notes is required and must be non-empty for draft_ready_for_human_review.
- resolution_criteria_notes: required_ready_section_empty:resolution_criteria_notes - resolution_criteria_notes is required and must be non-empty for draft_ready_for_human_review.
- uncertainty_register: required_ready_section_empty:uncertainty_register - uncertainty_register is required and must be non-empty for draft_ready_for_human_review.
- buy: prohibited_draft_field:buy - Trading, execution, recommendation, bet, stake, size, price, scoring, signal, probability, EV, wallet, private-key, side, buy/sell, and market-decision fields are prohibited.
- buy: unexpected_draft_field:buy - buy is not an allowed selected-ingest manual dossier draft field.
- ev: prohibited_draft_field:ev - Trading, execution, recommendation, bet, stake, size, price, scoring, signal, probability, EV, wallet, private-key, side, buy/sell, and market-decision fields are prohibited.
- ev: unexpected_draft_field:ev - ev is not an allowed selected-ingest manual dossier draft field.
- expected_value: prohibited_draft_field:expected_value - Trading, execution, recommendation, bet, stake, size, price, scoring, signal, probability, EV, wallet, private-key, side, buy/sell, and market-decision fields are prohibited.
- expected_value: unexpected_draft_field:expected_value - expected_value is not an allowed selected-ingest manual dossier draft field.
- market_context_notes: prohibited_dossier_language:completed_dossier - Completed/final dossier, recommendation, and market-decision language is prohibited in machine-readable manual draft fields.
- market_decision: prohibited_dossier_language:market_decision - Completed/final dossier, recommendation, and market-decision language is prohibited in machine-readable manual draft fields.
- market_decision: prohibited_draft_field:market_decision - Trading, execution, recommendation, bet, stake, size, price, scoring, signal, probability, EV, wallet, private-key, side, buy/sell, and market-decision fields are prohibited.
- market_decision: unexpected_draft_field:market_decision - market_decision is not an allowed selected-ingest manual dossier draft field.
- missing_information_review: prohibited_dossier_language:bet_recommendation - Completed/final dossier, recommendation, and market-decision language is prohibited in machine-readable manual draft fields.
- operator_review_notes: prohibited_dossier_language:trade_recommendation - Completed/final dossier, recommendation, and market-decision language is prohibited in machine-readable manual draft fields.
- probability: prohibited_draft_field:probability - Trading, execution, recommendation, bet, stake, size, price, scoring, signal, probability, EV, wallet, private-key, side, buy/sell, and market-decision fields are prohibited.
- probability: unexpected_draft_field:probability - probability is not an allowed selected-ingest manual dossier draft field.
- resolution_criteria_notes: prohibited_dossier_language:final_dossier - Completed/final dossier, recommendation, and market-decision language is prohibited in machine-readable manual draft fields.
- score: prohibited_draft_field:score - Trading, execution, recommendation, bet, stake, size, price, scoring, signal, probability, EV, wallet, private-key, side, buy/sell, and market-decision fields are prohibited.
- score: unexpected_draft_field:score - score is not an allowed selected-ingest manual dossier draft field.
- sell: prohibited_draft_field:sell - Trading, execution, recommendation, bet, stake, size, price, scoring, signal, probability, EV, wallet, private-key, side, buy/sell, and market-decision fields are prohibited.
- sell: unexpected_draft_field:sell - sell is not an allowed selected-ingest manual dossier draft field.
- side: prohibited_draft_field:side - Trading, execution, recommendation, bet, stake, size, price, scoring, signal, probability, EV, wallet, private-key, side, buy/sell, and market-decision fields are prohibited.
- side: unexpected_draft_field:side - side is not an allowed selected-ingest manual dossier draft field.
- signal: prohibited_draft_field:signal - Trading, execution, recommendation, bet, stake, size, price, scoring, signal, probability, EV, wallet, private-key, side, buy/sell, and market-decision fields are prohibited.
- signal: unexpected_draft_field:signal - signal is not an allowed selected-ingest manual dossier draft field.
- yes_no_decision: prohibited_draft_field:yes_no_decision - Trading, execution, recommendation, bet, stake, size, price, scoring, signal, probability, EV, wallet, private-key, side, buy/sell, and market-decision fields are prohibited.
- yes_no_decision: unexpected_draft_field:yes_no_decision - yes_no_decision is not an allowed selected-ingest manual dossier draft field.

### unknown-market-id
- market_id: unknown_market_id - Selected-ingest manual dossier draft market_id is absent from selected_ingest_dossier_draft_skeletons.v1.json selected_market_ids.

## Safety Boundary

- authenticated_endpoints: false
- betting_recommendations: false
- codex_copy_roots: false
- completed_dossiers: false
- Credential material present: false
- dispatcher_run_codex_touched: false
- expected_value_calculations: false
- live_fetchers: false
- live_trading: false
- market_decisions: false
- market_scoring: false
- network_api_calls: false
- paper_orders: false
- probability_estimates: false
- prompt_automation: false
- real_orders: false
- runtime_wiring: false
- side_recommendations: false
- trading_endpoints: false
- truth_inference: false
- Wallet or private-key material present: false

## Limitations

- Reads only local selected-ingest manual draft, selected-ingest skeleton, selected-ingest review-result, and selected-ingest merged-packet artifacts.
- Validates manual draft structure and next-action labels only.
- Does not infer outcomes, score markets, estimate probabilities, calculate expected value, choose sides, create dossiers, create orders, or route runtime work.
