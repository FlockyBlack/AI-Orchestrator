# PMBOT SOURCE-008B Market Class Pilot Dry-Run Plan

- task_id: PMBOT-SOURCE-008B-MARKET-CLASS-PILOT-PROTOCOL-ESPORTS-WEATHER-CRYPTO
- status: dry_run_planned_not_fetched
- class_order: esports, weather, crypto
- target_class_count: 3
- candidate_count: 0
- network_calls_performed: 0
- openrouter_calls_performed: 0
- polymarket_api_calls_performed: 0
- validator_status: passed

## Class Plans

- esports: planned_not_fetched
  - required fields: market_id, market_class, market_title_or_question, resolution_wording, event_name, game_title, team_or_player_names, match_or_event_start_time, official_source_name, official_source_reference, source_checked_at_local, captured_resolution_text, source_reliability_review, operator_notes, capture_status
  - operator review required: true
  - future fetch: separate approved read-only task only
- weather: planned_not_fetched
  - required fields: market_id, market_class, market_title_or_question, resolution_wording, weather_location, station_or_agency_name, measurement_type, measurement_window, measurement_units, official_source_name, official_source_reference, source_checked_at_local, captured_resolution_text, source_reliability_review, operator_notes, capture_status
  - operator review required: true
  - future fetch: separate approved read-only task only
- crypto: planned_not_fetched
  - required fields: market_id, market_class, market_title_or_question, resolution_wording, asset_or_event_name, named_index_or_source, settlement_time_window, measurement_units, official_source_name, official_source_reference, source_checked_at_local, captured_resolution_text, source_reliability_review, operator_notes, capture_status
  - operator review required: true
  - future fetch: separate approved read-only task only

## Safety Boundary

- no network calls
- no data fetching
- no candidate creation from live markets
- no runtime, dispatcher, background worker, queue, or browser automation
- no canonical packet mutation
- no probability, EV, edge, confidence, side selection, trade recommendation, buy, sell, hold, enter, exit, guaranteed win, free money, or sure bet labels
