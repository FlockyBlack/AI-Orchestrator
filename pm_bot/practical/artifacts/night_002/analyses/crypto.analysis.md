# PMBOT One-Market Analysis Card

## Market

- Market ID: `synthetic-crypto-reference-001`
- Title: Will the synthetic token close above the reference level on June 2?
- Analysis ID: `synthetic-crypto-reference-001.analysis.7384b905ed0b`

## Main question

What local evidence would resolve the operator's review of: Will the synthetic token close above the reference level on June 2?

## Sources used

- `crypto_archived_reference` (Synthetic Archived Reference Close): local_static_fixture, freshness `stale`, claim `reference_close_context`
- `crypto_rules_capture` (Synthetic Crypto Rules Capture): operator_static_fixture, freshness `current`, claim `resolution_clock`

## What we know

Local one-market review for Will the synthetic token close above the reference level on June 2?. A local packet captures static crypto-like reference records without using live exchange data. The packet has 2 used source(s), 1 missing evidence item(s), 1 stale source note(s), and 0 contradiction note(s). The result is a paper-only analysis record for later outcome review.

## What we do not know

- Final reference close record for 2026-06-02

## Evidence quality

- Used sources: 2
- Unused sources: 0
- Missing evidence items: 1
- Stale source notes: 1
- Contradiction notes: 0

## Contradictions / stale data

- Stale source `crypto_archived_reference` (Synthetic Archived Reference Close): `stale`

## Risks and traps

- The archived source may be too old for the fixture window.

## Paper-only hypothesis for tracking

- Safety label: `paper_only_non_executable_analysis_tracking`
- Tracked claim: Track whether the local source-backed analysis remains useful after the market outcome is reviewed.
- Outcome check: Later compare the final outcome record with the local rules summary, resolution source summary, and source attribution.

## What would prove this wrong

- Final reference close record for 2026-06-02

## What to check next

- Collect local evidence for: Final reference close record for 2026-06-02
- Clarify uncertainty: The archived source may be too old for the fixture window.

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
