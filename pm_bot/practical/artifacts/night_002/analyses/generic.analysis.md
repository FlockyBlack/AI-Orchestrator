# PMBOT One-Market Analysis Card

## Market

- Market ID: `synthetic-generic-event-001`
- Title: Will the synthetic event certificate be filed by June 5?
- Analysis ID: `synthetic-generic-event-001.analysis.11f645d06c7a`

## Main question

What local evidence would resolve the operator's review of: Will the synthetic event certificate be filed by June 5?

## Sources used

- `generic_planning_note` (Synthetic Planning Note): operator_static_fixture, freshness `current`, claim `filing_intent`
- `generic_event_rules` (Synthetic Event Rules Note): rules_static_fixture, freshness `current`, claim `resolution_rule`

## What we know

Local one-market review for Will the synthetic event certificate be filed by June 5?. A local packet captures a generic event-resolution market with deliberately missing material evidence. The packet has 2 used source(s), 2 missing evidence item(s), 0 stale source note(s), and 0 contradiction note(s). The result is a paper-only analysis record for later outcome review.

## What we do not know

- Actual certificate filing record
- Clerk timestamp for the filing

## Evidence quality

- Used sources: 2
- Unused sources: 0
- Missing evidence items: 2
- Stale source notes: 0
- Contradiction notes: 0

## Contradictions / stale data

- none

## Risks and traps

- Expected filing notes are not resolution evidence.

## Paper-only hypothesis for tracking

- Safety label: `paper_only_non_executable_analysis_tracking`
- Tracked claim: Track whether the local source-backed analysis remains useful after the market outcome is reviewed.
- Outcome check: Later compare the final outcome record with the local rules summary, resolution source summary, and source attribution.

## What would prove this wrong

- Actual certificate filing record
- Clerk timestamp for the filing

## What to check next

- Collect local evidence for: Actual certificate filing record
- Collect local evidence for: Clerk timestamp for the filing
- Clarify uncertainty: Expected filing notes are not resolution evidence.

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
