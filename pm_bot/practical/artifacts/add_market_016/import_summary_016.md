# PMBOT Local Market Packet Import

- Input: `pm_bot/llm/manual_packet_batch/573656_packet.v1.json`
- Output contract: `pmbot_one_market_input.v1`
- Market ID: `573656`
- Market title: Will Bitcoin hit $150k by December 31, 2026?
- Sources preserved: 7
- Missing evidence items: 11
- Source artifact path: `pm_bot/research/merged_manual_research_packets.v1.json`
- Normalized JSON: `pm_bot/practical/artifacts/add_market_016/normalized_input_016.json`

## Missing evidence

- full_market_resolution_criteria_text
- official_source_urls
- credible_news_source_urls
- yes_evidence
- no_or_counterevidence
- source_timestamps
- source_reliability_review
- operator_edge_assessment
- operator_risk_review
- benchmark_and_timezone_rules
- Referenced source artifact path is not present locally: pm_bot/research/merged_manual_research_packets.v1.json

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
