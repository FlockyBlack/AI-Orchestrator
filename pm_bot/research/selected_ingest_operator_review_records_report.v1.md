# Selected Ingest Operator Review Records v1

## Summary

- task_id: PMBOT-INGEST-009-SELECTED-INGEST-OPERATOR-REVIEW-RECORD-GATE
- source_review_records_path: pm_bot/research/selected_ingest_operator_review_records_fixture.v1.json
- source_operator_review_queue_path: pm_bot/research/selected_ingest_operator_review_queue.v1.json
- source_merged_packets_path: pm_bot/research/selected_ingest_merged_manual_research_packets.v1.json
- review_records_read: 6
- review_records_accepted: 3
- review_records_rejected: 3
- ready_for_dossier_drafting: 1
- needs_more_information: 1
- research_quality_rejected: 0
- watch_only_manual: 1
- errors_by_market_id:
  - 597964: 44
  - 691547: 1
  - unknown-market-id: 1

## Selected Market IDs

- 692258
- 824952
- 691547
- 597964
- 598936

## Accepted Review Records

### 692258
- review_status: needs_more_information
- review_outcome: needs_more_information
- queue_group: needs_more_information
- packet_completion_status: needs_more_information

### 824952
- review_status: review_completed
- review_outcome: ready_for_dossier_drafting
- queue_group: ready_for_operator_review
- packet_completion_status: ready_for_operator_review

### 598936
- review_status: not_reviewed
- review_outcome: watch_only_manual
- queue_group: stub_only
- packet_completion_status: stub_only

## Rejected Review Records

### 691547
- review_status: review_completed
- review_outcome: watch_only_manual
- queue_group: stub_only
- packet_completion_status: stub_only
- errors:
  - title: immutable_packet_field_override:title - title is immutable packet or queue content and cannot be supplied by an operator review record.

### 597964
- review_status: review_completed
- review_outcome: watch_only_manual
- queue_group: stub_only
- packet_completion_status: stub_only
- errors:
  - bet: prohibited_review_field:bet - Trading, execution, recommendation, bet, stake, size, price, scoring, probability, expected value, side, buy/sell, wallet, private-key, and market decision fields are prohibited.
  - bet: unexpected_review_field:bet - bet is not an allowed operator review record field.
  - buy: prohibited_review_field:buy - Trading, execution, recommendation, bet, stake, size, price, scoring, probability, expected value, side, buy/sell, wallet, private-key, and market decision fields are prohibited.
  - buy: unexpected_review_field:buy - buy is not an allowed operator review record field.
  - entry_price: prohibited_review_field:entry_price - Trading, execution, recommendation, bet, stake, size, price, scoring, probability, expected value, side, buy/sell, wallet, private-key, and market decision fields are prohibited.
  - entry_price: unexpected_review_field:entry_price - entry_price is not an allowed operator review record field.
  - ev: prohibited_review_field:ev - Trading, execution, recommendation, bet, stake, size, price, scoring, probability, expected value, side, buy/sell, wallet, private-key, and market decision fields are prohibited.
  - ev: unexpected_review_field:ev - ev is not an allowed operator review record field.
  - execution: prohibited_review_field:execution - Trading, execution, recommendation, bet, stake, size, price, scoring, probability, expected value, side, buy/sell, wallet, private-key, and market decision fields are prohibited.
  - execution: unexpected_review_field:execution - execution is not an allowed operator review record field.
  - expected_value: prohibited_review_field:expected_value - Trading, execution, recommendation, bet, stake, size, price, scoring, probability, expected value, side, buy/sell, wallet, private-key, and market decision fields are prohibited.
  - expected_value: unexpected_review_field:expected_value - expected_value is not an allowed operator review record field.
  - limit_price: prohibited_review_field:limit_price - Trading, execution, recommendation, bet, stake, size, price, scoring, probability, expected value, side, buy/sell, wallet, private-key, and market decision fields are prohibited.
  - limit_price: unexpected_review_field:limit_price - limit_price is not an allowed operator review record field.
  - market_decision: prohibited_review_field:market_decision - Trading, execution, recommendation, bet, stake, size, price, scoring, probability, expected value, side, buy/sell, wallet, private-key, and market decision fields are prohibited.
  - market_decision: unexpected_review_field:market_decision - market_decision is not an allowed operator review record field.
  - order: prohibited_review_field:order - Trading, execution, recommendation, bet, stake, size, price, scoring, probability, expected value, side, buy/sell, wallet, private-key, and market decision fields are prohibited.
  - order: unexpected_review_field:order - order is not an allowed operator review record field.
  - price_target: prohibited_review_field:price_target - Trading, execution, recommendation, bet, stake, size, price, scoring, probability, expected value, side, buy/sell, wallet, private-key, and market decision fields are prohibited.
  - price_target: unexpected_review_field:price_target - price_target is not an allowed operator review record field.
  - Private-key field violation: prohibited_review_field(private-key-field) - Trading, execution, recommendation, bet, stake, size, price, scoring, probability, expected value, side, buy/sell, wallet, private-key, and market decision fields are prohibited.
  - Private-key field violation: unexpected_review_field(private-key-field) - The private-key field is not an allowed operator review record field.
  - probability: prohibited_review_field:probability - Trading, execution, recommendation, bet, stake, size, price, scoring, probability, expected value, side, buy/sell, wallet, private-key, and market decision fields are prohibited.
  - probability: unexpected_review_field:probability - probability is not an allowed operator review record field.
  - recommendation: prohibited_review_field:recommendation - Trading, execution, recommendation, bet, stake, size, price, scoring, probability, expected value, side, buy/sell, wallet, private-key, and market decision fields are prohibited.
  - recommendation: unexpected_review_field:recommendation - recommendation is not an allowed operator review record field.
  - score: prohibited_review_field:score - Trading, execution, recommendation, bet, stake, size, price, scoring, probability, expected value, side, buy/sell, wallet, private-key, and market decision fields are prohibited.
  - score: unexpected_review_field:score - score is not an allowed operator review record field.
  - sell: prohibited_review_field:sell - Trading, execution, recommendation, bet, stake, size, price, scoring, probability, expected value, side, buy/sell, wallet, private-key, and market decision fields are prohibited.
  - sell: unexpected_review_field:sell - sell is not an allowed operator review record field.
  - side: prohibited_review_field:side - Trading, execution, recommendation, bet, stake, size, price, scoring, probability, expected value, side, buy/sell, wallet, private-key, and market decision fields are prohibited.
  - side: unexpected_review_field:side - side is not an allowed operator review record field.
  - signal: prohibited_review_field:signal - Trading, execution, recommendation, bet, stake, size, price, scoring, probability, expected value, side, buy/sell, wallet, private-key, and market decision fields are prohibited.
  - signal: unexpected_review_field:signal - signal is not an allowed operator review record field.
  - size: prohibited_review_field:size - Trading, execution, recommendation, bet, stake, size, price, scoring, probability, expected value, side, buy/sell, wallet, private-key, and market decision fields are prohibited.
  - size: unexpected_review_field:size - size is not an allowed operator review record field.
  - stake: prohibited_review_field:stake - Trading, execution, recommendation, bet, stake, size, price, scoring, probability, expected value, side, buy/sell, wallet, private-key, and market decision fields are prohibited.
  - stake: unexpected_review_field:stake - stake is not an allowed operator review record field.
  - trade: prohibited_review_field:trade - Trading, execution, recommendation, bet, stake, size, price, scoring, probability, expected value, side, buy/sell, wallet, private-key, and market decision fields are prohibited.
  - trade: unexpected_review_field:trade - trade is not an allowed operator review record field.
  - wallet: prohibited_review_field:wallet - Trading, execution, recommendation, bet, stake, size, price, scoring, probability, expected value, side, buy/sell, wallet, private-key, and market decision fields are prohibited.
  - wallet: unexpected_review_field:wallet - wallet is not an allowed operator review record field.
  - yes_no_decision: prohibited_review_field:yes_no_decision - Trading, execution, recommendation, bet, stake, size, price, scoring, probability, expected value, side, buy/sell, wallet, private-key, and market decision fields are prohibited.
  - yes_no_decision: unexpected_review_field:yes_no_decision - yes_no_decision is not an allowed operator review record field.

### unknown-market-id
- review_status: review_completed
- review_outcome: watch_only_manual
- queue_group: 
- packet_completion_status: 
- errors:
  - market_id: unknown_market_id - Review record market_id is not present in the selected-ingest operator review queue.

## Errors By Market ID

### 597964
- bet: prohibited_review_field:bet - Trading, execution, recommendation, bet, stake, size, price, scoring, probability, expected value, side, buy/sell, wallet, private-key, and market decision fields are prohibited.
- bet: unexpected_review_field:bet - bet is not an allowed operator review record field.
- buy: prohibited_review_field:buy - Trading, execution, recommendation, bet, stake, size, price, scoring, probability, expected value, side, buy/sell, wallet, private-key, and market decision fields are prohibited.
- buy: unexpected_review_field:buy - buy is not an allowed operator review record field.
- entry_price: prohibited_review_field:entry_price - Trading, execution, recommendation, bet, stake, size, price, scoring, probability, expected value, side, buy/sell, wallet, private-key, and market decision fields are prohibited.
- entry_price: unexpected_review_field:entry_price - entry_price is not an allowed operator review record field.
- ev: prohibited_review_field:ev - Trading, execution, recommendation, bet, stake, size, price, scoring, probability, expected value, side, buy/sell, wallet, private-key, and market decision fields are prohibited.
- ev: unexpected_review_field:ev - ev is not an allowed operator review record field.
- execution: prohibited_review_field:execution - Trading, execution, recommendation, bet, stake, size, price, scoring, probability, expected value, side, buy/sell, wallet, private-key, and market decision fields are prohibited.
- execution: unexpected_review_field:execution - execution is not an allowed operator review record field.
- expected_value: prohibited_review_field:expected_value - Trading, execution, recommendation, bet, stake, size, price, scoring, probability, expected value, side, buy/sell, wallet, private-key, and market decision fields are prohibited.
- expected_value: unexpected_review_field:expected_value - expected_value is not an allowed operator review record field.
- limit_price: prohibited_review_field:limit_price - Trading, execution, recommendation, bet, stake, size, price, scoring, probability, expected value, side, buy/sell, wallet, private-key, and market decision fields are prohibited.
- limit_price: unexpected_review_field:limit_price - limit_price is not an allowed operator review record field.
- market_decision: prohibited_review_field:market_decision - Trading, execution, recommendation, bet, stake, size, price, scoring, probability, expected value, side, buy/sell, wallet, private-key, and market decision fields are prohibited.
- market_decision: unexpected_review_field:market_decision - market_decision is not an allowed operator review record field.
- order: prohibited_review_field:order - Trading, execution, recommendation, bet, stake, size, price, scoring, probability, expected value, side, buy/sell, wallet, private-key, and market decision fields are prohibited.
- order: unexpected_review_field:order - order is not an allowed operator review record field.
- price_target: prohibited_review_field:price_target - Trading, execution, recommendation, bet, stake, size, price, scoring, probability, expected value, side, buy/sell, wallet, private-key, and market decision fields are prohibited.
- price_target: unexpected_review_field:price_target - price_target is not an allowed operator review record field.
- Private-key field violation: prohibited_review_field(private-key-field) - Trading, execution, recommendation, bet, stake, size, price, scoring, probability, expected value, side, buy/sell, wallet, private-key, and market decision fields are prohibited.
- Private-key field violation: unexpected_review_field(private-key-field) - The private-key field is not an allowed operator review record field.
- probability: prohibited_review_field:probability - Trading, execution, recommendation, bet, stake, size, price, scoring, probability, expected value, side, buy/sell, wallet, private-key, and market decision fields are prohibited.
- probability: unexpected_review_field:probability - probability is not an allowed operator review record field.
- recommendation: prohibited_review_field:recommendation - Trading, execution, recommendation, bet, stake, size, price, scoring, probability, expected value, side, buy/sell, wallet, private-key, and market decision fields are prohibited.
- recommendation: unexpected_review_field:recommendation - recommendation is not an allowed operator review record field.
- score: prohibited_review_field:score - Trading, execution, recommendation, bet, stake, size, price, scoring, probability, expected value, side, buy/sell, wallet, private-key, and market decision fields are prohibited.
- score: unexpected_review_field:score - score is not an allowed operator review record field.
- sell: prohibited_review_field:sell - Trading, execution, recommendation, bet, stake, size, price, scoring, probability, expected value, side, buy/sell, wallet, private-key, and market decision fields are prohibited.
- sell: unexpected_review_field:sell - sell is not an allowed operator review record field.
- side: prohibited_review_field:side - Trading, execution, recommendation, bet, stake, size, price, scoring, probability, expected value, side, buy/sell, wallet, private-key, and market decision fields are prohibited.
- side: unexpected_review_field:side - side is not an allowed operator review record field.
- signal: prohibited_review_field:signal - Trading, execution, recommendation, bet, stake, size, price, scoring, probability, expected value, side, buy/sell, wallet, private-key, and market decision fields are prohibited.
- signal: unexpected_review_field:signal - signal is not an allowed operator review record field.
- size: prohibited_review_field:size - Trading, execution, recommendation, bet, stake, size, price, scoring, probability, expected value, side, buy/sell, wallet, private-key, and market decision fields are prohibited.
- size: unexpected_review_field:size - size is not an allowed operator review record field.
- stake: prohibited_review_field:stake - Trading, execution, recommendation, bet, stake, size, price, scoring, probability, expected value, side, buy/sell, wallet, private-key, and market decision fields are prohibited.
- stake: unexpected_review_field:stake - stake is not an allowed operator review record field.
- trade: prohibited_review_field:trade - Trading, execution, recommendation, bet, stake, size, price, scoring, probability, expected value, side, buy/sell, wallet, private-key, and market decision fields are prohibited.
- trade: unexpected_review_field:trade - trade is not an allowed operator review record field.
- wallet: prohibited_review_field:wallet - Trading, execution, recommendation, bet, stake, size, price, scoring, probability, expected value, side, buy/sell, wallet, private-key, and market decision fields are prohibited.
- wallet: unexpected_review_field:wallet - wallet is not an allowed operator review record field.
- yes_no_decision: prohibited_review_field:yes_no_decision - Trading, execution, recommendation, bet, stake, size, price, scoring, probability, expected value, side, buy/sell, wallet, private-key, and market decision fields are prohibited.
- yes_no_decision: unexpected_review_field:yes_no_decision - yes_no_decision is not an allowed operator review record field.

### 691547
- title: immutable_packet_field_override:title - title is immutable packet or queue content and cannot be supplied by an operator review record.

### unknown-market-id
- market_id: unknown_market_id - Review record market_id is not present in the selected-ingest operator review queue.

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

- Reads only local selected-ingest review records, selected-ingest operator review queue, and selected-ingest merged manual research packets.
- Records structural operator review outcomes only.
- Does not create dossiers, scores, recommendations, orders, runtime actions, truth inference, or market conclusions.
