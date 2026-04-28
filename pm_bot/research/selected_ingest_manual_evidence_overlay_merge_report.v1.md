# Selected Ingest Manual Evidence Overlay Merge Report v1

## Summary
- overlays_read: 5
- overlays_accepted: 2
- overlays_rejected: 3
- packets_written: 5
- ready_for_operator_review: 1
- needs_more_information: 1
- merged_packets_validation_passed: true

## Source Artifacts
- packet_stubs: `pm_bot/research/selected_ingest_research_packet_stubs.v1.json`
- overlay_template: `pm_bot/research/selected_ingest_manual_evidence_overlay_template.v1.json`
- overlay: `pm_bot/research/selected_ingest_manual_evidence_overlay_fixture.v1.json`
- output: `pm_bot/research/selected_ingest_merged_manual_research_packets.v1.json`

## Selected Market IDs
- `692258`
- `824952`
- `691547`
- `597964`
- `598936`

## Accepted Overlays
- `692258`
- `824952`

## Rejected Overlays
- `597964`
- `691547`
- `999999`

## Status Counts
- ready_for_operator_review_market_ids: 824952
- needs_more_information_market_ids: 692258

## Errors By Market ID
### `597964`
- prohibited_overlay_field:bet at `bet`: Trading, wallet, execution, recommendation, stake, size, price, scoring, probability, expected value, side, buy/sell, and market decision fields are prohibited.
- unexpected_overlay_field:bet at `bet`: bet is not an allowed manual evidence overlay field.
- prohibited_overlay_field:buy at `buy`: Trading, wallet, execution, recommendation, stake, size, price, scoring, probability, expected value, side, buy/sell, and market decision fields are prohibited.
- unexpected_overlay_field:buy at `buy`: buy is not an allowed manual evidence overlay field.
- prohibited_overlay_field:entry_price at `entry_price`: Trading, wallet, execution, recommendation, stake, size, price, scoring, probability, expected value, side, buy/sell, and market decision fields are prohibited.
- unexpected_overlay_field:entry_price at `entry_price`: entry_price is not an allowed manual evidence overlay field.
- prohibited_overlay_field:ev at `ev`: Trading, wallet, execution, recommendation, stake, size, price, scoring, probability, expected value, side, buy/sell, and market decision fields are prohibited.
- unexpected_overlay_field:ev at `ev`: ev is not an allowed manual evidence overlay field.
- prohibited_overlay_field:execution at `execution`: Trading, wallet, execution, recommendation, stake, size, price, scoring, probability, expected value, side, buy/sell, and market decision fields are prohibited.
- unexpected_overlay_field:execution at `execution`: execution is not an allowed manual evidence overlay field.
- prohibited_overlay_field:expected_value at `expected_value`: Trading, wallet, execution, recommendation, stake, size, price, scoring, probability, expected value, side, buy/sell, and market decision fields are prohibited.
- unexpected_overlay_field:expected_value at `expected_value`: expected_value is not an allowed manual evidence overlay field.
- prohibited_overlay_field:limit_price at `limit_price`: Trading, wallet, execution, recommendation, stake, size, price, scoring, probability, expected value, side, buy/sell, and market decision fields are prohibited.
- unexpected_overlay_field:limit_price at `limit_price`: limit_price is not an allowed manual evidence overlay field.
- prohibited_overlay_field:market_decision at `market_decision`: Trading, wallet, execution, recommendation, stake, size, price, scoring, probability, expected value, side, buy/sell, and market decision fields are prohibited.
- unexpected_overlay_field:market_decision at `market_decision`: market_decision is not an allowed manual evidence overlay field.
- prohibited_overlay_field:order at `order`: Trading, wallet, execution, recommendation, stake, size, price, scoring, probability, expected value, side, buy/sell, and market decision fields are prohibited.
- unexpected_overlay_field:order at `order`: order is not an allowed manual evidence overlay field.
- prohibited_overlay_field:price_target at `price_target`: Trading, wallet, execution, recommendation, stake, size, price, scoring, probability, expected value, side, buy/sell, and market decision fields are prohibited.
- unexpected_overlay_field:price_target at `price_target`: price_target is not an allowed manual evidence overlay field.
- prohibited_overlay_field:private_key at `private_key`: Trading, wallet, execution, recommendation, stake, size, price, scoring, probability, expected value, side, buy/sell, and market decision fields are prohibited.
- unexpected_overlay_field:private_key at `private_key`: private_key is not an allowed manual evidence overlay field.
- prohibited_overlay_field:probability at `probability`: Trading, wallet, execution, recommendation, stake, size, price, scoring, probability, expected value, side, buy/sell, and market decision fields are prohibited.
- unexpected_overlay_field:probability at `probability`: probability is not an allowed manual evidence overlay field.
- prohibited_overlay_field:recommendation at `recommendation`: Trading, wallet, execution, recommendation, stake, size, price, scoring, probability, expected value, side, buy/sell, and market decision fields are prohibited.
- unexpected_overlay_field:recommendation at `recommendation`: recommendation is not an allowed manual evidence overlay field.
- prohibited_overlay_field:score at `score`: Trading, wallet, execution, recommendation, stake, size, price, scoring, probability, expected value, side, buy/sell, and market decision fields are prohibited.
- unexpected_overlay_field:score at `score`: score is not an allowed manual evidence overlay field.
- prohibited_overlay_field:sell at `sell`: Trading, wallet, execution, recommendation, stake, size, price, scoring, probability, expected value, side, buy/sell, and market decision fields are prohibited.
- unexpected_overlay_field:sell at `sell`: sell is not an allowed manual evidence overlay field.
- prohibited_overlay_field:side at `side`: Trading, wallet, execution, recommendation, stake, size, price, scoring, probability, expected value, side, buy/sell, and market decision fields are prohibited.
- unexpected_overlay_field:side at `side`: side is not an allowed manual evidence overlay field.
- prohibited_overlay_field:signal at `signal`: Trading, wallet, execution, recommendation, stake, size, price, scoring, probability, expected value, side, buy/sell, and market decision fields are prohibited.
- unexpected_overlay_field:signal at `signal`: signal is not an allowed manual evidence overlay field.
- prohibited_overlay_field:size at `size`: Trading, wallet, execution, recommendation, stake, size, price, scoring, probability, expected value, side, buy/sell, and market decision fields are prohibited.
- unexpected_overlay_field:size at `size`: size is not an allowed manual evidence overlay field.
- prohibited_overlay_field:stake at `stake`: Trading, wallet, execution, recommendation, stake, size, price, scoring, probability, expected value, side, buy/sell, and market decision fields are prohibited.
- unexpected_overlay_field:stake at `stake`: stake is not an allowed manual evidence overlay field.
- prohibited_overlay_field:trade at `trade`: Trading, wallet, execution, recommendation, stake, size, price, scoring, probability, expected value, side, buy/sell, and market decision fields are prohibited.
- unexpected_overlay_field:trade at `trade`: trade is not an allowed manual evidence overlay field.
- prohibited_overlay_field:wallet at `wallet`: Trading, wallet, execution, recommendation, stake, size, price, scoring, probability, expected value, side, buy/sell, and market decision fields are prohibited.
- unexpected_overlay_field:wallet at `wallet`: wallet is not an allowed manual evidence overlay field.
- prohibited_overlay_field:yes_no_decision at `yes_no_decision`: Trading, wallet, execution, recommendation, stake, size, price, scoring, probability, expected value, side, buy/sell, and market decision fields are prohibited.
- unexpected_overlay_field:yes_no_decision at `yes_no_decision`: yes_no_decision is not an allowed manual evidence overlay field.
### `691547`
- immutable_field_override:title at `title`: title is immutable and must remain sourced from the selected ingest stub.
### `999999`
- unknown_market_id at `market_id`: Overlay market_id is not one of the five selected live-ingest market IDs.

## Safety Boundary
- offline_only: true
- live_fetchers: false
- network_api_calls: false
- credentials: false
- wallet_private_keys: false
- authenticated_endpoints: false
- trading_endpoints: false
- real_orders: false
- live_trading: false
- paper_orders: false
- betting_recommendations: false
- truth_inference: false
- market_scoring: false
- probability_estimates: false
- expected_value_calculations: false
- side_recommendations: false
- market_decisions: false
- runtime_wiring: false
- dispatcher_run_codex_touched: false
- prompt_automation: false
- codex_copy_roots: false
- completed_dossiers: false
