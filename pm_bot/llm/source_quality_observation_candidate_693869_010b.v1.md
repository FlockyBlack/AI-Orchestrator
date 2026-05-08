# PMBOT SOURCE-010B Weather Source Quality Observation Candidate

- task_id: PMBOT-SOURCE-010B-WEATHER-DRAFT-CAPTURE-AUTOFILL-FROM-READONLY-CANDIDATE
- market_id: 693869
- market_class: weather
- source_quality_status: pending_capture_operator_review_and_outcome
- outcome_known: false
- source_scoring_performed: false
- source_ranking_updated: false
- trading_profit_used_for_scoring: false
- profit_or_pnl_recorded: false
- operator_review_required: true

## Sources Observed

- gamma_market_metadata:693869
- gamma_market_rules:693869
- https://nsidc.org/sea-ice-today/sea-ice-tools
- NSIDC Sea Ice Index Daily Extent NH-Daily-Extent tab
- source_010b_manual_capture_draft_693869
- source_010b_operator_review_surface_693869
- unresolved_weather_source_questions

## Source Roles

- gamma_market_metadata:693869: market_metadata_source
- gamma_market_rules:693869: market_rules_source
- https://nsidc.org/sea-ice-today/sea-ice-tools: official_weather_source_candidate
- NSIDC Sea Ice Index Daily Extent NH-Daily-Extent tab: station_or_measurement_source_candidate
- If this resolution source becomes unavailable, another resolution source will be chosen.: fallback_weather_source_candidate
- pm_bot/llm/manual_resolution_source_capture/693869_resolution_source_capture.v1.json: local_capture_source
- pm_bot/llm/weather_capture_operator_review_surface_010b.v1.json: operator_review_surface
- unresolved_weather_source_questions: unresolved_source

## Notes

- Observation hook only; no source score is assigned.
- Outcome is not known in SOURCE-010B.
- Future review should compare stored source text to final outcome evidence after operator review.

## Safety Boundary

- observation hook only
- no market action guidance
- no source score
- no side selection
