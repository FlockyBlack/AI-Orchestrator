# PMBOT One-Market Analysis Card

## Market

- Market ID: `synthetic-esports-match-001`
- Title: Will synthetic Team Azure win the map-three match on June 4?
- Analysis ID: `synthetic-esports-match-001.analysis.a6d4bc90b97b`

## Main question

What local evidence would resolve the operator's review of: Will synthetic Team Azure win the map-three match on June 4?

## Sources used

- `esports_roster_note` (Synthetic Roster Note): team_static_fixture, freshness `current`, claim `roster_status`
- `esports_match_note` (Synthetic Match Note): event_static_fixture, freshness `current`, claim `match_scope`

## What we know

Local one-market review for Will synthetic Team Azure win the map-three match on June 4?. A local packet captures static roster and match-note records before the synthetic match result. The packet has 2 used source(s), 1 missing evidence item(s), 0 stale source note(s), and 0 contradiction note(s). The result is a paper-only analysis record for later outcome review.

## What we do not know

- Final match result sheet

## Evidence quality

- Used sources: 2
- Unused sources: 0
- Missing evidence items: 1
- Stale source notes: 0
- Contradiction notes: 0

## Contradictions / stale data

- none

## Risks and traps

- Roster continuity does not resolve the match result.

## Paper-only hypothesis for tracking

- Safety label: `paper_only_non_executable_analysis_tracking`
- Tracked claim: Track whether the local source-backed analysis remains useful after the market outcome is reviewed.
- Outcome check: Later compare the final outcome record with the local rules summary, resolution source summary, and source attribution.

## What would prove this wrong

- Final match result sheet

## What to check next

- Collect local evidence for: Final match result sheet
- Clarify uncertainty: Roster continuity does not resolve the match result.

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
