# PMBOT One-Market Analysis Card

## Market

- Market ID: `synthetic-weather-rain-001`
- Title: Will the synthetic city record measurable rain on June 1?
- Analysis ID: `synthetic-weather-rain-001.analysis.6ba2343c0bce`

## Main question

What local evidence would resolve the operator's review of: Will the synthetic city record measurable rain on June 1?

## Sources used

- `weather_station_bulletin` (Synthetic Station Bulletin): official_static_fixture, freshness `current`, claim `station_setup`
- `weather_event_note` (Synthetic Event Note): operator_static_fixture, freshness `current`, claim `event_date`

## What we know

Local one-market review for Will the synthetic city record measurable rain on June 1?. A local packet captures static weather-like station and event-note records before the synthetic event date. The packet has 2 used source(s), 1 missing evidence item(s), 0 stale source note(s), and 0 contradiction note(s). The result is a paper-only analysis record for later outcome review.

## What we do not know

- Final station precipitation total for 2026-06-01

## Evidence quality

- Used sources: 2
- Unused sources: 0
- Missing evidence items: 1
- Stale source notes: 0
- Contradiction notes: 0

## Contradictions / stale data

- none

## Risks and traps

- The final station total is not yet present in the local packet.

## Paper-only hypothesis for tracking

- Safety label: `paper_only_non_executable_analysis_tracking`
- Tracked claim: Track whether the local source-backed analysis remains useful after the market outcome is reviewed.
- Outcome check: Later compare the final outcome record with the local rules summary, resolution source summary, and source attribution.

## What would prove this wrong

- Final station precipitation total for 2026-06-01

## What to check next

- Collect local evidence for: Final station precipitation total for 2026-06-01
- Clarify uncertainty: The final station total is not yet present in the local packet.

## Outcome tracking placeholder

- Status: `placeholder_pending_outcome_record`
- Required record: `pmbot_one_market_outcome_record.v1`

## Safety boundary

- Local JSON fixture input only.
- Live network used: false.
- OpenRouter calls performed: 0.
- Polymarket API calls performed: 0.
- Authenticated endpoints used: false.
- Wallet/private-key access: false.
- Orders or trading actions: false.
- Runtime or dispatcher changes: false.
- No real trade decision was produced.
- The paper-only hypothesis is non-executable and for analysis-quality tracking only.
