# PMBOT Local Market Packet Import

- Input: `pm_bot/llm/manual_packet_batch/692258_packet.v1.json`
- Output contract: `pmbot_one_market_input.v1`
- Market ID: `692258`
- Market title: MicroStrategy sells any Bitcoin by June 30, 2026?
- Sources preserved: 10
- Missing evidence items: 6
- Source artifact path: `pm_bot/research/selected_ingest_merged_manual_research_packets.v1.json`
- Normalized JSON: `pm_bot\practical\artifacts\real_market_batch_004\markets\692258\normalized_input.json`

## Missing evidence

- full_official_source_reference
- credible_news_source_references
- official_yes_or_no_evidence
- source_reliability_review
- Valid partial selected-ingest overlay used to prove deterministic merge behavior.
- Referenced source artifact path is not present locally: pm_bot/research/selected_ingest_merged_manual_research_packets.v1.json

## Source references

- `official_source_checked_001` official_source_checked - `unknown`
- `official_source_checked_002` official_source_checked - `unknown`
- `official_source_placeholder_003` official_source_placeholder - `unknown`
- `official_source_placeholder_004` official_source_placeholder - `unknown`
- `official_source_placeholder_005` official_source_placeholder - `unknown`
- `news_source_checked_006` news_source_checked - `unknown`
- `news_source_placeholder_007` news_source_placeholder - `unknown`
- `news_source_placeholder_008` news_source_placeholder - `unknown`
- `news_source_placeholder_009` news_source_placeholder - `unknown`
- `source_plan_010` source_plan - `unknown`

## Safety boundary

- Local packet normalization only.
- No live fetch or external API call was performed.
- Missing evidence is preserved instead of invented.
