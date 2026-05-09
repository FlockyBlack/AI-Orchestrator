# PMBOT One-Market Analysis Card

## Market

- Market ID: `synthetic-garden-permit-001`
- Title: Will the synthetic community garden permit be approved by June 30?
- Analysis ID: `synthetic-garden-permit-001.analysis.dce3e1b2a251`

## Main question

What local evidence would resolve the operator's review of: Will the synthetic community garden permit be approved by June 30?

## Sources used

- `synthetic_city_agenda` (Synthetic City Agenda): official_static_fixture, freshness `current`, claim `permit_status`
- `synthetic_local_article` (Synthetic Local Article): news_static_fixture, freshness `current`, claim `hearing_schedule`

## What we know

Local one-market review for Will the synthetic community garden permit be approved by June 30?. The local packet captures a synthetic civic permit market after committee review and before final council action. The packet has 2 used source(s), 2 missing evidence item(s), 0 stale source note(s), and 0 contradiction note(s). The result is a paper-only analysis record for later outcome review.

## What we do not know

- Final council vote record
- Official resolution notice

## Evidence quality

- Used sources: 2
- Unused sources: 1
- Missing evidence items: 2
- Stale source notes: 0
- Contradiction notes: 0

## Contradictions / stale data

- none

## Risks and traps

- The full council vote has not appeared in the local packet.
- The resolution source wording still needs final outcome confirmation.

## Paper-only hypothesis for tracking

- Safety label: `paper_only_non_executable_analysis_tracking`
- Tracked claim: Track whether the local source-backed analysis remains useful after the market outcome is reviewed.
- Outcome check: Later compare the final outcome record with the local rules summary, resolution source summary, and source attribution.

## What would prove this wrong

- Final council vote record
- Official resolution notice

## What to check next

- Collect local evidence for: Final council vote record
- Collect local evidence for: Official resolution notice
- Clarify uncertainty: The full council vote has not appeared in the local packet.
- Clarify uncertainty: The resolution source wording still needs final outcome confirmation.

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
