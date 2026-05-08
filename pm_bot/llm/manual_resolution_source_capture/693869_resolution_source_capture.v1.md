# Manual Resolution Source Capture - 693869

- contract_version: manual_resolution_source_capture.v1
- schema_version: manual_resolution_source_capture_schema.v1
- task_id: PMBOT-SOURCE-010B-WEATHER-DRAFT-CAPTURE-AUTOFILL-FROM-READONLY-CANDIDATE
- market_id: 693869
- market_class: weather
- market_title_or_question: Will the minimum Arctic sea ice extent this summer be less than 4m square kilometers?
- current_openrouter_review_status: not_reviewed
- current_readiness_band: draft_from_readonly_candidate
- source_capture_status: draft
- capture_status: draft
- operator_review_required: true
- ready_for_local_review: false
- auto_promote_to_ready_for_local_review: false

## Weather Fields

- location: Arctic
- weather_metric: minimum Arctic sea ice extent
- unit: million_square_kilometers
- threshold_or_condition: less than 4 million square kilometers
- date_or_time_window: between August 1, 2026 and October 1, 2026
- timezone: requires operator verification
- official_weather_source: National Snow and Ice Data Center
- official_weather_source_url: https://nsidc.org/sea-ice-today/sea-ice-tools
- station_or_source_hierarchy: National Snow and Ice Data Center Sea Ice Index Daily Extent data set, NH-Daily-Extent tab, minimum value for any day in the market window
- fallback_source_candidate: If this resolution source becomes unavailable, another resolution source will be chosen.

## Source Capture

### Full Market Resolution Criteria Text

This market will resolve according to the minimum Arctic sea ice extent for all days between August 1, 2026 and October 1, 2026, as published by the National Snow and Ice Data Center.

This market will remain open until data has been published for October 1, 2026, at which point it will resolve immediately. Any revisions to sea ice extent recorded after data is published for October 1, 2026 will not be considered.

The resolution source for this market measures temperatures to thousands of square kilometers (e.g. 4.255 million sq km). Thus, this is the level of precision that will be used when resolving the market.

The resolution source for this market will be information from the National Snow and Ice Data Center, specifically the minimum value recorded for any day between August 1, 2026 and October 1, 2026 in the \u201cNH-Daily-Extent\u201d tab of the \u201cSea Ice Index Daily Extent\u201d data set, available at https://nsidc.org/sea-ice-today/sea-ice-tools. If this resolution source becomes unavailable, another resolution source will be chosen.

### Full Resolution Rules

This market will resolve according to the minimum Arctic sea ice extent for all days between August 1, 2026 and October 1, 2026, as published by the National Snow and Ice Data Center.

This market will remain open until data has been published for October 1, 2026, at which point it will resolve immediately. Any revisions to sea ice extent recorded after data is published for October 1, 2026 will not be considered.

The resolution source for this market measures temperatures to thousands of square kilometers (e.g. 4.255 million sq km). Thus, this is the level of precision that will be used when resolving the market.

The resolution source for this market will be information from the National Snow and Ice Data Center, specifically the minimum value recorded for any day between August 1, 2026 and October 1, 2026 in the \u201cNH-Daily-Extent\u201d tab of the \u201cSea Ice Index Daily Extent\u201d data set, available at https://nsidc.org/sea-ice-today/sea-ice-tools. If this resolution source becomes unavailable, another resolution source will be chosen.

### Official Source References

- SOURCE-010A2 read-only Gamma market metadata artifact for market-specific rules text
- National Snow and Ice Data Center
- Sea Ice Index Daily Extent data set
- NH-Daily-Extent tab
- https://nsidc.org/sea-ice-today/sea-ice-tools
- according to the minimum Arctic sea ice extent for all days between August 1, 2026 and October 1, 2026, as publis
- If this resolution source becomes unavailable, another resolution source will be chosen.

### Source URLs Or Rule References

- https://nsidc.org/sea-ice-today/sea-ice-tools
- pm_bot/live_readonly/weather_market_discovery/weather_source_capture_candidate_010a2.v1.json

### Source Timestamps

- SOURCE-010A2 read-only fetch marker: 2026-05-08T00:00:00Z_SOURCE_010A2_REFINED_READONLY_ATTEMPT
- Market time window from SOURCE-010A2 metadata: between August 1, 2026 and October 1, 2026
- SOURCE-010B local autofill timestamp: 2026-05-08 Asia/Tbilisi; no network calls performed.

### Source Reliability Review

SOURCE-010A2 provides locally stored public read-only Gamma metadata for market rules text. The stored metadata names the National Snow and Ice Data Center Sea Ice Index Daily Extent data set and NH-Daily-Extent tab, but SOURCE-010B does not fetch or verify any live NSIDC page. Operator review must verify exact rules text, source hierarchy, time window, timezone, and fallback handling before any status promotion.

### Reviewed Local Evidence References

- pm_bot/live_readonly/weather_market_discovery/weather_market_raw_fetch_010a2.v1.json
- pm_bot/live_readonly/weather_market_discovery/weather_market_normalized_candidate_010a2.v1.json
- pm_bot/live_readonly/weather_market_discovery/weather_source_capture_candidate_010a2.v1.json
- pm_bot/live_readonly/weather_market_discovery/weather_operator_review_checklist_010a2.v1.json
- pm_bot/live_readonly/weather_market_discovery/weather_operator_review_checklist_010a2.v1.md
- pm_bot/live_readonly/weather_market_discovery/weather_discovery_refinement_diagnostics_010a2.v1.json
- pm_bot/llm/source_quality_observation_candidate_weather_010a2.v1.json

### Evidence Notes

SOURCE-010A2 locally stored Gamma metadata contains the weather market description, rules text, Arctic region, minimum sea ice extent metric, million-square-kilometer unit, less-than-4-million-square-kilometer condition, August 1 through October 1 2026 window, NSIDC source reference, and generic fallback-source clause. SOURCE-010B copies that evidence into a manual capture draft only; operator review remains required and no market decision is made.

## Unresolved Source Questions

- Operator must verify exact Polymarket/Gamma rules text before any status promotion.
- Operator must verify the Arctic sea ice extent metric, unit precision, threshold, and resolution window.
- Operator must verify that the stored NSIDC dataset and NH-Daily-Extent tab text matches the canonical market rules.
- Operator must verify fallback-source handling if the named weather source becomes unavailable.
- Operator must verify the market time window timezone.

## Operator Instructions

- Verify exact Polymarket/Gamma rules text against the stored 010A2 candidate and any approved local source review surface.
- Verify the NSIDC source, Sea Ice Index Daily Extent data set, and NH-Daily-Extent tab hierarchy.
- Verify region, metric, unit precision, threshold, time window, timezone, and fallback-source handling.
- Keep this capture as draft until operator review is complete.
- Do not add predictions, market action guidance, probability, EV, edge, confidence, or side selection.

## Safety Summary

- local-only draft from SOURCE-010A2 artifacts
- no OpenRouter calls
- no Polymarket API calls in SOURCE-010B
- no external network calls
- no market action guidance
- no probability, EV, edge, confidence scoring, or side selection
- no trading, queue, runtime, dispatcher, background, browser, wallet, or order authority
