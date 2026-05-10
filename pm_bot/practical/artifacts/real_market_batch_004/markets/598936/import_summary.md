# PMBOT Local Market Packet Import

- Input: `pm_bot/llm/manual_packet_batch/598936_packet.v1.json`
- Output contract: `pmbot_one_market_input.v1`
- Market ID: `598936`
- Market title: Will the next UK election be called by June 30, 2026?
- Sources preserved: 7
- Missing evidence items: 7
- Source artifact path: `pm_bot/research/selected_ingest_merged_manual_research_packets.v1.json`
- Normalized JSON: `pm_bot\practical\artifacts\real_market_batch_004\markets\598936\normalized_input.json`

## Missing evidence

- manual_research_not_started
- full_market_resolution_criteria_review
- official_source_references
- credible_news_source_references
- empty_evidence_slots
- operator_human_review_required
- Referenced source artifact path is not present locally: pm_bot/research/selected_ingest_merged_manual_research_packets.v1.json

## Source references

- `official_source_placeholder_001` official_source_placeholder - `unknown`
- `official_source_placeholder_002` official_source_placeholder - `unknown`
- `official_source_placeholder_003` official_source_placeholder - `unknown`
- `news_source_placeholder_004` news_source_placeholder - `unknown`
- `news_source_placeholder_005` news_source_placeholder - `unknown`
- `news_source_placeholder_006` news_source_placeholder - `unknown`
- `source_plan_007` source_plan - `unknown`

## Safety boundary

- Local packet normalization only.
- No live fetch or external API call was performed.
- Missing evidence is preserved instead of invented.
