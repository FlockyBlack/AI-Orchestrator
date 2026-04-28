# Selected Ingest Dossier Human Review Records v1

## Summary

- task_id: PMBOT-INGEST-013-SELECTED-INGEST-DOSSIER-HUMAN-REVIEW-RECORD-GATE
- source_review_records_path: pm_bot/research/selected_ingest_dossier_human_review_records_fixture.v1.json
- source_review_pack_path: pm_bot/research/selected_ingest_dossier_human_review_pack.v1.json
- source_validation_result_path: pm_bot/research/selected_ingest_manual_dossier_draft_validation_result.v1.json
- source_dossier_skeletons_path: pm_bot/research/selected_ingest_dossier_draft_skeletons.v1.json
- review_records_read: 10
- review_records_accepted: 1
- review_records_rejected: 9
- approved_for_final_dossier_draft: 1
- needs_draft_revision: 0
- rejected_for_research_quality: 0
- watch_only: 0
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

## Review Pack Market IDs

- 824952

## Accepted Human Review Records

### record 0: 824952
- human_review_status: review_completed
- human_review_outcome: approved_for_final_dossier_draft
- review_pack_status: human_review_pack_only
- requested_revision_items_count: 0
- quality_flags_count: 0

## Rejected Human Review Records

### record 2: 692258
- human_review_status: review_completed
- human_review_outcome: watch_only
- review_pack_status: 
- errors:
  - market_id: selected_market_id_not_in_review_pack - Human review record market_id was selected but is not present in selected_ingest_dossier_human_review_pack.v1.json.

### record 3: 824952
- human_review_status: not_reviewed
- human_review_outcome: watch_only
- review_pack_status: human_review_pack_only
- errors:
  - title_question: immutable_review_pack_field_override:title_question - title_question is immutable review pack content and cannot be supplied by a human review record.

### record 4: 824952
- human_review_status: needs_revision
- human_review_outcome: needs_draft_revision
- review_pack_status: human_review_pack_only
- errors:
  - bet: prohibited_human_review_field:bet - Trading, execution, recommendation, bet, stake, size, price, scoring, signal, probability, EV, wallet, private-key, side, buy/sell, and market-decision fields are prohibited in selected-ingest dossier human review records.
  - bet: unexpected_human_review_field:bet - bet is not an allowed selected-ingest human review record field.
  - entry_price: prohibited_human_review_field:entry_price - Trading, execution, recommendation, bet, stake, size, price, scoring, signal, probability, EV, wallet, private-key, side, buy/sell, and market-decision fields are prohibited in selected-ingest dossier human review records.
  - entry_price: unexpected_human_review_field:entry_price - entry_price is not an allowed selected-ingest human review record field.
  - execution: prohibited_human_review_field:execution - Trading, execution, recommendation, bet, stake, size, price, scoring, signal, probability, EV, wallet, private-key, side, buy/sell, and market-decision fields are prohibited in selected-ingest dossier human review records.
  - execution: unexpected_human_review_field:execution - execution is not an allowed selected-ingest human review record field.
  - execution.order: prohibited_human_review_field:order - Trading, execution, recommendation, bet, stake, size, price, scoring, signal, probability, EV, wallet, private-key, side, buy/sell, and market-decision fields are prohibited in selected-ingest dossier human review records.
  - limit_price: prohibited_human_review_field:limit_price - Trading, execution, recommendation, bet, stake, size, price, scoring, signal, probability, EV, wallet, private-key, side, buy/sell, and market-decision fields are prohibited in selected-ingest dossier human review records.
  - limit_price: unexpected_human_review_field:limit_price - limit_price is not an allowed selected-ingest human review record field.
  - order: prohibited_human_review_field:order - Trading, execution, recommendation, bet, stake, size, price, scoring, signal, probability, EV, wallet, private-key, side, buy/sell, and market-decision fields are prohibited in selected-ingest dossier human review records.
  - order: unexpected_human_review_field:order - order is not an allowed selected-ingest human review record field.
  - price_target: prohibited_human_review_field:price_target - Trading, execution, recommendation, bet, stake, size, price, scoring, signal, probability, EV, wallet, private-key, side, buy/sell, and market-decision fields are prohibited in selected-ingest dossier human review records.
  - price_target: unexpected_human_review_field:price_target - price_target is not an allowed selected-ingest human review record field.
  - Private-key field violation: prohibited_human_review_field(private-key-field) - Trading, execution, recommendation, bet, stake, size, price, scoring, signal, probability, EV, wallet, private-key, side, buy/sell, and market-decision fields are prohibited in selected-ingest dossier human review records.
  - Private-key field violation: unexpected_human_review_field(private-key-field) - The private-key field is not an allowed selected-ingest human review record field.
  - recommendation: prohibited_human_review_field:recommendation - Trading, execution, recommendation, bet, stake, size, price, scoring, signal, probability, EV, wallet, private-key, side, buy/sell, and market-decision fields are prohibited in selected-ingest dossier human review records.
  - recommendation: unexpected_human_review_field:recommendation - recommendation is not an allowed selected-ingest human review record field.
  - size: prohibited_human_review_field:size - Trading, execution, recommendation, bet, stake, size, price, scoring, signal, probability, EV, wallet, private-key, side, buy/sell, and market-decision fields are prohibited in selected-ingest dossier human review records.
  - size: unexpected_human_review_field:size - size is not an allowed selected-ingest human review record field.
  - stake: prohibited_human_review_field:stake - Trading, execution, recommendation, bet, stake, size, price, scoring, signal, probability, EV, wallet, private-key, side, buy/sell, and market-decision fields are prohibited in selected-ingest dossier human review records.
  - stake: unexpected_human_review_field:stake - stake is not an allowed selected-ingest human review record field.
  - trade: prohibited_human_review_field:trade - Trading, execution, recommendation, bet, stake, size, price, scoring, signal, probability, EV, wallet, private-key, side, buy/sell, and market-decision fields are prohibited in selected-ingest dossier human review records.
  - trade: unexpected_human_review_field:trade - trade is not an allowed selected-ingest human review record field.
  - wallet: prohibited_human_review_field:wallet - Trading, execution, recommendation, bet, stake, size, price, scoring, signal, probability, EV, wallet, private-key, side, buy/sell, and market-decision fields are prohibited in selected-ingest dossier human review records.
  - wallet: unexpected_human_review_field:wallet - wallet is not an allowed selected-ingest human review record field.

### record 5: 824952
- human_review_status: review_completed
- human_review_outcome: watch_only
- review_pack_status: human_review_pack_only
- errors:
  - buy: prohibited_human_review_field:buy - Trading, execution, recommendation, bet, stake, size, price, scoring, signal, probability, EV, wallet, private-key, side, buy/sell, and market-decision fields are prohibited in selected-ingest dossier human review records.
  - buy: unexpected_human_review_field:buy - buy is not an allowed selected-ingest human review record field.
  - ev: prohibited_human_review_field:ev - Trading, execution, recommendation, bet, stake, size, price, scoring, signal, probability, EV, wallet, private-key, side, buy/sell, and market-decision fields are prohibited in selected-ingest dossier human review records.
  - ev: unexpected_human_review_field:ev - ev is not an allowed selected-ingest human review record field.
  - expected_value: prohibited_human_review_field:expected_value - Trading, execution, recommendation, bet, stake, size, price, scoring, signal, probability, EV, wallet, private-key, side, buy/sell, and market-decision fields are prohibited in selected-ingest dossier human review records.
  - expected_value: unexpected_human_review_field:expected_value - expected_value is not an allowed selected-ingest human review record field.
  - market_decision: prohibited_dossier_language:market_decision - Completed/final dossier, recommendation, and market-decision language is prohibited in machine-readable human review record fields.
  - market_decision: prohibited_human_review_field:market_decision - Trading, execution, recommendation, bet, stake, size, price, scoring, signal, probability, EV, wallet, private-key, side, buy/sell, and market-decision fields are prohibited in selected-ingest dossier human review records.
  - market_decision: unexpected_human_review_field:market_decision - market_decision is not an allowed selected-ingest human review record field.
  - probability: prohibited_human_review_field:probability - Trading, execution, recommendation, bet, stake, size, price, scoring, signal, probability, EV, wallet, private-key, side, buy/sell, and market-decision fields are prohibited in selected-ingest dossier human review records.
  - probability: unexpected_human_review_field:probability - probability is not an allowed selected-ingest human review record field.
  - score: prohibited_human_review_field:score - Trading, execution, recommendation, bet, stake, size, price, scoring, signal, probability, EV, wallet, private-key, side, buy/sell, and market-decision fields are prohibited in selected-ingest dossier human review records.
  - score: unexpected_human_review_field:score - score is not an allowed selected-ingest human review record field.
  - sell: prohibited_human_review_field:sell - Trading, execution, recommendation, bet, stake, size, price, scoring, signal, probability, EV, wallet, private-key, side, buy/sell, and market-decision fields are prohibited in selected-ingest dossier human review records.
  - sell: unexpected_human_review_field:sell - sell is not an allowed selected-ingest human review record field.
  - side: prohibited_human_review_field:side - Trading, execution, recommendation, bet, stake, size, price, scoring, signal, probability, EV, wallet, private-key, side, buy/sell, and market-decision fields are prohibited in selected-ingest dossier human review records.
  - side: unexpected_human_review_field:side - side is not an allowed selected-ingest human review record field.
  - signal: prohibited_human_review_field:signal - Trading, execution, recommendation, bet, stake, size, price, scoring, signal, probability, EV, wallet, private-key, side, buy/sell, and market-decision fields are prohibited in selected-ingest dossier human review records.
  - signal: unexpected_human_review_field:signal - signal is not an allowed selected-ingest human review record field.
  - yes_no_decision: prohibited_human_review_field:yes_no_decision - Trading, execution, recommendation, bet, stake, size, price, scoring, signal, probability, EV, wallet, private-key, side, buy/sell, and market-decision fields are prohibited in selected-ingest dossier human review records.
  - yes_no_decision: unexpected_human_review_field:yes_no_decision - yes_no_decision is not an allowed selected-ingest human review record field.

### record 6: 824952
- human_review_status: review_completed
- human_review_outcome: approved_for_final_dossier_draft
- review_pack_status: human_review_pack_only
- errors:
  - review_checks.no_market_decision_present: required_approval_review_check_not_true:no_market_decision_present - review_checks.no_market_decision_present must be true before approved_for_final_dossier_draft can be accepted.
  - review_checks.no_probability_or_ev_present: required_approval_review_check_not_true:no_probability_or_ev_present - review_checks.no_probability_or_ev_present must be true before approved_for_final_dossier_draft can be accepted.

### record 7: 824952
- human_review_status: needs_revision
- human_review_outcome: needs_draft_revision
- review_pack_status: human_review_pack_only
- errors:
  - requested_revision_items: needs_draft_revision_requires_requested_revision_items - human_review_outcome needs_draft_revision requires non-empty requested_revision_items.

### record 8: 824952
- human_review_status: review_rejected
- human_review_outcome: rejected_for_research_quality
- review_pack_status: human_review_pack_only
- errors:
  - reviewer_notes: rejected_for_research_quality_requires_reviewer_notes - human_review_outcome rejected_for_research_quality requires non-empty reviewer_notes.

### record 9: 824952
- human_review_status: review_completed
- human_review_outcome: watch_only
- review_pack_status: human_review_pack_only
- errors:
  - next_manual_action: prohibited_dossier_language:market_decision - Completed/final dossier, recommendation, and market-decision language is prohibited in machine-readable human review record fields.
  - quality_flags[0]: prohibited_dossier_language:final_dossier - Completed/final dossier, recommendation, and market-decision language is prohibited in machine-readable human review record fields.
  - requested_revision_items[0]: prohibited_dossier_language:bet_recommendation - Completed/final dossier, recommendation, and market-decision language is prohibited in machine-readable human review record fields.
  - requested_revision_items[1]: prohibited_dossier_language:trade_recommendation - Completed/final dossier, recommendation, and market-decision language is prohibited in machine-readable human review record fields.
  - reviewer_notes: prohibited_dossier_language:completed_dossier - Completed/final dossier, recommendation, and market-decision language is prohibited in machine-readable human review record fields.

### record 1: unknown-market-id
- human_review_status: not_reviewed
- human_review_outcome: watch_only
- review_pack_status: 
- errors:
  - market_id: unknown_market_id - Human review record market_id is absent from the local selected-ingest review pack, draft validation, and skeleton artifacts.

## Errors By Market ID

### 692258
- market_id: selected_market_id_not_in_review_pack - Human review record market_id was selected but is not present in selected_ingest_dossier_human_review_pack.v1.json.

### 824952
- title_question: immutable_review_pack_field_override:title_question - title_question is immutable review pack content and cannot be supplied by a human review record.
- bet: prohibited_human_review_field:bet - Trading, execution, recommendation, bet, stake, size, price, scoring, signal, probability, EV, wallet, private-key, side, buy/sell, and market-decision fields are prohibited in selected-ingest dossier human review records.
- bet: unexpected_human_review_field:bet - bet is not an allowed selected-ingest human review record field.
- entry_price: prohibited_human_review_field:entry_price - Trading, execution, recommendation, bet, stake, size, price, scoring, signal, probability, EV, wallet, private-key, side, buy/sell, and market-decision fields are prohibited in selected-ingest dossier human review records.
- entry_price: unexpected_human_review_field:entry_price - entry_price is not an allowed selected-ingest human review record field.
- execution: prohibited_human_review_field:execution - Trading, execution, recommendation, bet, stake, size, price, scoring, signal, probability, EV, wallet, private-key, side, buy/sell, and market-decision fields are prohibited in selected-ingest dossier human review records.
- execution: unexpected_human_review_field:execution - execution is not an allowed selected-ingest human review record field.
- execution.order: prohibited_human_review_field:order - Trading, execution, recommendation, bet, stake, size, price, scoring, signal, probability, EV, wallet, private-key, side, buy/sell, and market-decision fields are prohibited in selected-ingest dossier human review records.
- limit_price: prohibited_human_review_field:limit_price - Trading, execution, recommendation, bet, stake, size, price, scoring, signal, probability, EV, wallet, private-key, side, buy/sell, and market-decision fields are prohibited in selected-ingest dossier human review records.
- limit_price: unexpected_human_review_field:limit_price - limit_price is not an allowed selected-ingest human review record field.
- order: prohibited_human_review_field:order - Trading, execution, recommendation, bet, stake, size, price, scoring, signal, probability, EV, wallet, private-key, side, buy/sell, and market-decision fields are prohibited in selected-ingest dossier human review records.
- order: unexpected_human_review_field:order - order is not an allowed selected-ingest human review record field.
- price_target: prohibited_human_review_field:price_target - Trading, execution, recommendation, bet, stake, size, price, scoring, signal, probability, EV, wallet, private-key, side, buy/sell, and market-decision fields are prohibited in selected-ingest dossier human review records.
- price_target: unexpected_human_review_field:price_target - price_target is not an allowed selected-ingest human review record field.
- Private-key field violation: prohibited_human_review_field(private-key-field) - Trading, execution, recommendation, bet, stake, size, price, scoring, signal, probability, EV, wallet, private-key, side, buy/sell, and market-decision fields are prohibited in selected-ingest dossier human review records.
- Private-key field violation: unexpected_human_review_field(private-key-field) - The private-key field is not an allowed selected-ingest human review record field.
- recommendation: prohibited_human_review_field:recommendation - Trading, execution, recommendation, bet, stake, size, price, scoring, signal, probability, EV, wallet, private-key, side, buy/sell, and market-decision fields are prohibited in selected-ingest dossier human review records.
- recommendation: unexpected_human_review_field:recommendation - recommendation is not an allowed selected-ingest human review record field.
- size: prohibited_human_review_field:size - Trading, execution, recommendation, bet, stake, size, price, scoring, signal, probability, EV, wallet, private-key, side, buy/sell, and market-decision fields are prohibited in selected-ingest dossier human review records.
- size: unexpected_human_review_field:size - size is not an allowed selected-ingest human review record field.
- stake: prohibited_human_review_field:stake - Trading, execution, recommendation, bet, stake, size, price, scoring, signal, probability, EV, wallet, private-key, side, buy/sell, and market-decision fields are prohibited in selected-ingest dossier human review records.
- stake: unexpected_human_review_field:stake - stake is not an allowed selected-ingest human review record field.
- trade: prohibited_human_review_field:trade - Trading, execution, recommendation, bet, stake, size, price, scoring, signal, probability, EV, wallet, private-key, side, buy/sell, and market-decision fields are prohibited in selected-ingest dossier human review records.
- trade: unexpected_human_review_field:trade - trade is not an allowed selected-ingest human review record field.
- wallet: prohibited_human_review_field:wallet - Trading, execution, recommendation, bet, stake, size, price, scoring, signal, probability, EV, wallet, private-key, side, buy/sell, and market-decision fields are prohibited in selected-ingest dossier human review records.
- wallet: unexpected_human_review_field:wallet - wallet is not an allowed selected-ingest human review record field.
- buy: prohibited_human_review_field:buy - Trading, execution, recommendation, bet, stake, size, price, scoring, signal, probability, EV, wallet, private-key, side, buy/sell, and market-decision fields are prohibited in selected-ingest dossier human review records.
- buy: unexpected_human_review_field:buy - buy is not an allowed selected-ingest human review record field.
- ev: prohibited_human_review_field:ev - Trading, execution, recommendation, bet, stake, size, price, scoring, signal, probability, EV, wallet, private-key, side, buy/sell, and market-decision fields are prohibited in selected-ingest dossier human review records.
- ev: unexpected_human_review_field:ev - ev is not an allowed selected-ingest human review record field.
- expected_value: prohibited_human_review_field:expected_value - Trading, execution, recommendation, bet, stake, size, price, scoring, signal, probability, EV, wallet, private-key, side, buy/sell, and market-decision fields are prohibited in selected-ingest dossier human review records.
- expected_value: unexpected_human_review_field:expected_value - expected_value is not an allowed selected-ingest human review record field.
- market_decision: prohibited_dossier_language:market_decision - Completed/final dossier, recommendation, and market-decision language is prohibited in machine-readable human review record fields.
- market_decision: prohibited_human_review_field:market_decision - Trading, execution, recommendation, bet, stake, size, price, scoring, signal, probability, EV, wallet, private-key, side, buy/sell, and market-decision fields are prohibited in selected-ingest dossier human review records.
- market_decision: unexpected_human_review_field:market_decision - market_decision is not an allowed selected-ingest human review record field.
- probability: prohibited_human_review_field:probability - Trading, execution, recommendation, bet, stake, size, price, scoring, signal, probability, EV, wallet, private-key, side, buy/sell, and market-decision fields are prohibited in selected-ingest dossier human review records.
- probability: unexpected_human_review_field:probability - probability is not an allowed selected-ingest human review record field.
- score: prohibited_human_review_field:score - Trading, execution, recommendation, bet, stake, size, price, scoring, signal, probability, EV, wallet, private-key, side, buy/sell, and market-decision fields are prohibited in selected-ingest dossier human review records.
- score: unexpected_human_review_field:score - score is not an allowed selected-ingest human review record field.
- sell: prohibited_human_review_field:sell - Trading, execution, recommendation, bet, stake, size, price, scoring, signal, probability, EV, wallet, private-key, side, buy/sell, and market-decision fields are prohibited in selected-ingest dossier human review records.
- sell: unexpected_human_review_field:sell - sell is not an allowed selected-ingest human review record field.
- side: prohibited_human_review_field:side - Trading, execution, recommendation, bet, stake, size, price, scoring, signal, probability, EV, wallet, private-key, side, buy/sell, and market-decision fields are prohibited in selected-ingest dossier human review records.
- side: unexpected_human_review_field:side - side is not an allowed selected-ingest human review record field.
- signal: prohibited_human_review_field:signal - Trading, execution, recommendation, bet, stake, size, price, scoring, signal, probability, EV, wallet, private-key, side, buy/sell, and market-decision fields are prohibited in selected-ingest dossier human review records.
- signal: unexpected_human_review_field:signal - signal is not an allowed selected-ingest human review record field.
- yes_no_decision: prohibited_human_review_field:yes_no_decision - Trading, execution, recommendation, bet, stake, size, price, scoring, signal, probability, EV, wallet, private-key, side, buy/sell, and market-decision fields are prohibited in selected-ingest dossier human review records.
- yes_no_decision: unexpected_human_review_field:yes_no_decision - yes_no_decision is not an allowed selected-ingest human review record field.
- review_checks.no_market_decision_present: required_approval_review_check_not_true:no_market_decision_present - review_checks.no_market_decision_present must be true before approved_for_final_dossier_draft can be accepted.
- review_checks.no_probability_or_ev_present: required_approval_review_check_not_true:no_probability_or_ev_present - review_checks.no_probability_or_ev_present must be true before approved_for_final_dossier_draft can be accepted.
- requested_revision_items: needs_draft_revision_requires_requested_revision_items - human_review_outcome needs_draft_revision requires non-empty requested_revision_items.
- reviewer_notes: rejected_for_research_quality_requires_reviewer_notes - human_review_outcome rejected_for_research_quality requires non-empty reviewer_notes.
- next_manual_action: prohibited_dossier_language:market_decision - Completed/final dossier, recommendation, and market-decision language is prohibited in machine-readable human review record fields.
- quality_flags[0]: prohibited_dossier_language:final_dossier - Completed/final dossier, recommendation, and market-decision language is prohibited in machine-readable human review record fields.
- requested_revision_items[0]: prohibited_dossier_language:bet_recommendation - Completed/final dossier, recommendation, and market-decision language is prohibited in machine-readable human review record fields.
- requested_revision_items[1]: prohibited_dossier_language:trade_recommendation - Completed/final dossier, recommendation, and market-decision language is prohibited in machine-readable human review record fields.
- reviewer_notes: prohibited_dossier_language:completed_dossier - Completed/final dossier, recommendation, and market-decision language is prohibited in machine-readable human review record fields.

### unknown-market-id
- market_id: unknown_market_id - Human review record market_id is absent from the local selected-ingest review pack, draft validation, and skeleton artifacts.

## Safety Boundary

- authenticated_endpoints: false
- betting_recommendations: false
- codex_copy_roots: false
- completed_dossiers: false
- Credential material present: false
- dispatcher_run_codex_touched: false
- expected_value_calculations: false
- final_dossier_drafts: false
- live_fetchers: false
- live_trading: false
- market_decisions: false
- market_scoring: false
- network_api_calls: false
- offline_only: true
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

- Reads only local selected-ingest human review records, selected-ingest dossier review packs, draft validation, and skeleton artifacts.
- Validates human review record structure and operational review labels only.
- Does not create final dossier drafts, completed dossiers, recommendations, scores, probabilities, EV calculations, side choices, orders, paper orders, runtime actions, or market decisions.
