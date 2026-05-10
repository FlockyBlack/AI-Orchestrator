# PMBOT One-Market Analysis Card

## Market

- Market ID: `692258`
- Title: MicroStrategy sells any Bitcoin by June 30, 2026?
- Analysis ID: `692258.analysis.bed289c1494d`

## Main question

What local evidence would resolve the operator's review of: MicroStrategy sells any Bitcoin by June 30, 2026?

## Sources used

- `official_source_checked_001` (official_source_checked): local_static_fixture, freshness `unknown`, claim `official_source_checked`
- `official_source_checked_002` (official_source_checked): local_static_fixture, freshness `unknown`, claim `official_source_checked`
- `official_source_placeholder_003` (official_source_placeholder): local_static_fixture, freshness `unknown`, claim `official_source_placeholder`
- `official_source_placeholder_004` (official_source_placeholder): local_static_fixture, freshness `unknown`, claim `official_source_placeholder`
- `official_source_placeholder_005` (official_source_placeholder): local_static_fixture, freshness `unknown`, claim `official_source_placeholder`
- `news_source_checked_006` (news_source_checked): local_static_fixture, freshness `unknown`, claim `news_source_checked`
- `news_source_placeholder_007` (news_source_placeholder): local_static_fixture, freshness `unknown`, claim `news_source_placeholder`
- `news_source_placeholder_008` (news_source_placeholder): local_static_fixture, freshness `unknown`, claim `news_source_placeholder`
- `news_source_placeholder_009` (news_source_placeholder): local_static_fixture, freshness `unknown`, claim `news_source_placeholder`
- `source_plan_010` (source_plan): local_static_fixture, freshness `unknown`, claim `source_plan`

## What we know

Local one-market review for MicroStrategy sells any Bitcoin by June 30, 2026?. Stub-only local market description excerpt for 'MicroStrategy sells any Bitcoin by June 30, 2026?': This market will resolve to "Yes" if MicroStrategy sells any of its Bitcoin by 11:59 PM ET on the date specified in the title. Otherwise, this market will resolve to "No". Manual completion must review the full local criteria before use. The packet has 10 used source(s), 6 missing evidence item(s), 0 stale source note(s), and 3 contradiction note(s). The result is a paper-only analysis record for later outcome review.

## What we do not know

- full_official_source_reference
- credible_news_source_references
- official_yes_or_no_evidence
- source_reliability_review
- Valid partial selected-ingest overlay used to prove deterministic merge behavior.
- Referenced source artifact path is not present locally: pm_bot/research/selected_ingest_merged_manual_research_packets.v1.json

## Evidence quality

- Used sources: 10
- Unused sources: 0
- Missing evidence items: 6
- Stale source notes: 0
- Contradiction notes: 3

## Contradictions / stale data

- Contradiction on `news_source_placeholder` across values: Manual check template: Associated Press coverage query for 'MicroStrategy sells any Bitcoin by June 30, 2026?', Manual check template: Reuters coverage query for 'MicroStrategy sells any Bitcoin by June 30, 2026?', Manual check template: major credible outlet query for 'Finance / Economy / Business / 2025 Predictions / Crypto / MicroStrategy / Stocks' and 'MicroStrategy sells any Bitcoin by June 30, 2026?'
- Contradiction on `official_source_checked` across values: offline-check:692258:company-source-placeholder, offline-check:692258:local-market-rules
- Contradiction on `official_source_placeholder` across values: Manual check template: local Polymarket rules and resolution criteria for market_id 692258, Manual check template: official primary source named in the local market description for 'MicroStrategy sells any Bitcoin by June 30, 2026?', Manual check template: original issuer, government, court, exchange, or company source relevant to 'MicroStrategy sells any Bitcoin by June 30, 2026?'

## Risks and traps

- Local packet may be incomplete; missing evidence is preserved below.

## Paper-only hypothesis for tracking

- Safety label: `paper_only_non_executable_analysis_tracking`
- Tracked claim: Track whether the local source-backed analysis remains useful after the market outcome is reviewed.
- Outcome check: Later compare the final outcome record with the local rules summary, resolution source summary, and source attribution.

## What would prove this wrong

- full_official_source_reference
- credible_news_source_references
- official_yes_or_no_evidence
- source_reliability_review
- Valid partial selected-ingest overlay used to prove deterministic merge behavior.
- Referenced source artifact path is not present locally: pm_bot/research/selected_ingest_merged_manual_research_packets.v1.json

## What to check next

- Collect local evidence for: full_official_source_reference
- Collect local evidence for: credible_news_source_references
- Collect local evidence for: official_yes_or_no_evidence
- Collect local evidence for: source_reliability_review
- Collect local evidence for: Valid partial selected-ingest overlay used to prove deterministic merge behavior.
- Collect local evidence for: Referenced source artifact path is not present locally: pm_bot/research/selected_ingest_merged_manual_research_packets.v1.json
- Clarify uncertainty: Local packet may be incomplete; missing evidence is preserved below.

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
