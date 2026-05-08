# PMBOT SOURCE-010B Weather Operator Review Surface

- task_id: PMBOT-SOURCE-010B-WEATHER-DRAFT-CAPTURE-AUTOFILL-FROM-READONLY-CANDIDATE
- market_id: 693869
- title: Will the minimum Arctic sea ice extent this summer be less than 4m square kilometers?
- market_class: weather
- capture_status: draft
- operator_review_required: true
- ready_for_local_review: false

## Known Weather Fields

- location: Arctic
- weather_metric: minimum Arctic sea ice extent
- unit: million_square_kilometers
- threshold_or_condition: less than 4 million square kilometers
- date_or_time_window: between August 1, 2026 and October 1, 2026
- timezone:
- official_weather_source: National Snow and Ice Data Center
- official_weather_source_url: https://nsidc.org/sea-ice-today/sea-ice-tools
- station_or_source_hierarchy: National Snow and Ice Data Center Sea Ice Index Daily Extent data set, NH-Daily-Extent tab, minimum value for any day in the market window
- fallback_source_candidate: If this resolution source becomes unavailable, another resolution source will be chosen.
- official_weather_source_identified: True
- station_or_source_hierarchy_identified: True

## Missing Fields

- timezone

## Ambiguity Flags

- timezone_missing_in_source_010a2_metadata
- fallback_source_clause_is_generic_and_requires_operator_review
- stored_rules_text_not_refetched_in_source_010b

## Unresolved Source Questions

- Operator must verify exact Polymarket/Gamma rules text before any status promotion.
- Operator must verify the Arctic sea ice extent metric, unit precision, threshold, and resolution window.
- Operator must verify that the stored NSIDC dataset and NH-Daily-Extent tab text matches the canonical market rules.
- Operator must verify fallback-source handling if the named weather source becomes unavailable.
- Operator must verify the market time window timezone.

## Checklist Items From 010A2

- [unchecked] verify_exact_polymarket_rules_text: Verify exact Polymarket rules text.
- [unchecked] verify_location: Verify location.
- [unchecked] verify_weather_metric: Verify weather metric.
- [unchecked] verify_unit: Verify unit.
- [unchecked] verify_threshold_or_condition: Verify threshold or condition.
- [unchecked] verify_date_or_time_window: Verify date or time window.
- [unchecked] verify_timezone: Verify timezone.
- [unchecked] verify_official_weather_source: Verify official weather source.
- [unchecked] verify_station_or_source_hierarchy: Verify station or source hierarchy.
- [unchecked] verify_fallback_source: Verify fallback source.
- [unchecked] verify_source_capture_promotion_readiness: Verify whether source capture can be promoted to ready_for_local_review.
- [unchecked] no_trading_decision: No trading decision.

## Operator Next Actions

- Verify exact rules text from the stored SOURCE-010A2 market metadata.
- Verify NSIDC source hierarchy, dataset name, tab name, and source availability.
- Verify time window, timezone, threshold, unit precision, and fallback-source clause.
- Keep capture status as draft until review is complete.

## Safety Boundary

- no market action guidance
- operator review only
- no trading, queue, runtime, dispatcher, background, browser, wallet, or order authority
