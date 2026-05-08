# PMBOT SOURCE-010A2 Weather Source Quality Observation Candidate

- task_id: PMBOT-SOURCE-010A2-WEATHER-DISCOVERY-QUERY-REFINEMENT-AND-SECOND-READONLY-ATTEMPT
- market_id: 693869
- market_class: weather
- status: pending_future_capture_and_outcome_review
- outcome_known: false
- source_scoring_performed: false
- source_ranking_updated: false
- trading_profit_used_for_scoring: false
- operator_review_required: true

## Source Roles

- gamma_market_metadata:693869: market_metadata_source
- gamma_market_rules:693869: market_rules_source
- https://nsidc.org/sea-ice-today/sea-ice-tools: official_weather_source_candidate
- according to the minimum Arctic sea ice extent for all days between August 1, 2026 and October 1, 2026, as publis: station_or_measurement_source_candidate
- If this resolution source becomes unavailable, another resolution source will be chosen.: fallback_weather_source_candidate
- unresolved_weather_source_questions: unresolved_source

## Notes

- Weather source-quality observation is candidate-only until SOURCE-010B and future outcome review.
- No source scoring or ranking is performed in SOURCE-010A2.
