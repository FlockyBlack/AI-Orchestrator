# Weather Source Quality Observation Flow - SOURCE-010C

This local-only flow connects `pm_bot/llm/source_quality_observation_candidate_693869_010b.v1.json` to future weather outcome tracking.

It is not a trading score. It is not a market recommendation. It does not produce probability, EV, edge, confidence, side selection, or trade guidance.

## Stages

1. Source observed.
2. Weather source role classified.
3. Operator reviews whether the source is official or credible.
4. Outcome or measurement becomes known later.
5. Source alignment reviewed.
6. Source reliability updated.
7. Source can be preferred in future source capture, not automatically trusted for trading.

## Weather Source Roles

- market_metadata_source
- market_rules_source
- official_weather_source_candidate
- station_or_dataset_source_candidate
- fallback_weather_source_candidate
- unresolved_source
- local_capture_source
- operator_review_surface

## Allowed Future Source Quality Fields

- resolution_alignment
- measurement_alignment
- timeliness
- official_source_status
- contradiction_count
- operator_usefulness_notes

## Forbidden Scoring Inputs

- no profit_only_score
- no PnL
- no ROI
- no EV
- no edge
- no betting confidence
- no side selection
- no trade recommendation

## Boundary

Future source preference may help later source capture workflows. It must not automatically trust a source for trading, create a market action score, rank sources for trading decisions, or authorize execution.
