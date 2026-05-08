# SOURCE-010C Weather Operator Review Surface - 693869

This is a local-only operator review surface for market `693869`.

This is not a trading recommendation. No side is selected. No probability, EV, edge, or confidence is provided. This file only prepares source and rules readiness for future paper-live observation preparation.

## Market

- Title: Will the minimum Arctic sea ice extent this summer be less than 4m square kilometers?
- Market class: weather
- Capture status: draft
- Source capture status: draft
- Ready for local review: false
- Operator review required: true

## Known Local Inputs

- SOURCE-010A2 normalized candidate: `pm_bot/live_readonly/weather_market_discovery/weather_market_normalized_candidate_010a2.v1.json`
- SOURCE-010A2 source capture candidate: `pm_bot/live_readonly/weather_market_discovery/weather_source_capture_candidate_010a2.v1.json`
- SOURCE-010A2 operator checklist: `pm_bot/live_readonly/weather_market_discovery/weather_operator_review_checklist_010a2.v1.json`
- SOURCE-010B draft capture: `pm_bot/llm/manual_resolution_source_capture/693869_resolution_source_capture.v1.json`
- SOURCE-010B operator surface: `pm_bot/llm/weather_capture_operator_review_surface_010b.v1.json`
- SOURCE-010B source quality candidate: `pm_bot/llm/source_quality_observation_candidate_693869_010b.v1.json`
- Current readiness gate: `pm_bot/llm/post_capture_batch_readiness_gate.v1.json`

## Known Weather Fields

- Location: Arctic
- Weather metric: minimum Arctic sea ice extent
- Unit: million square kilometers
- Threshold or condition: less than 4 million square kilometers
- Date or time window: between August 1, 2026 and October 1, 2026
- Timezone: missing
- Official weather source candidate: National Snow and Ice Data Center
- Source hierarchy candidate: Sea Ice Index Daily Extent data set, NH-Daily-Extent tab, minimum value for any day in the market window
- Fallback source clause: another resolution source will be chosen if the named source becomes unavailable

## Review Status

- Direct rules text captured: true
- Official weather source identified from stored metadata: true
- Station or dataset hierarchy identified from stored metadata: true
- Source quality observation status: pending capture operator review and future outcome
- Paper-live preparation status: prepared pending operator review
- Simulated decision created: false

## Missing Or Ambiguous Items

- Timezone for the market window
- Operator-confirmed exact Polymarket/Gamma rules text
- Operator-confirmed official weather source availability at future observation time
- Operator-confirmed source timestamp for the future final measurement
- Operator-confirmed fallback source handling if the named source becomes unavailable

## Operator Checklist

- Verify exact Polymarket rules text.
- Verify location.
- Verify weather metric.
- Verify unit.
- Verify threshold or condition.
- Verify date or time window.
- Verify timezone.
- Verify official weather source.
- Verify station or source hierarchy.
- Verify fallback source.
- Verify whether source capture can be promoted to ready_for_local_review.
- Confirm no trading decision is made.

## Paper-Live Preparation Boundary

The paper-live artifacts created in SOURCE-010C are observation-only plans and contracts. They do not create a simulated trade, do not choose Yes or No, do not define a stake, do not create orders, and do not authorize wallet, runtime, dispatcher, queue, browser, or background worker behavior.

## Safety Summary

- no market action guidance
- no trading authority
- no execution authority
- no OpenRouter calls
- no Polymarket API calls
- no external network calls
- no authenticated endpoints
- no wallet or private key access
- no order creation
- no simulated trade
- no probability, EV, edge, confidence, or side-selection guidance
- no runtime, dispatcher, background worker, queue, browser, or canonical packet mutation
