# PMBOT Local Market Packet Import

- Input: `pm_bot\tests\fixtures\practical_market_queue_batch\seeds\esports.seed.json`
- Output contract: `pmbot_one_market_input.v1`
- Market ID: `synthetic-esports-match-001`
- Market title: Will synthetic Team Azure win the map-three match on June 4?
- Sources preserved: 2
- Missing evidence items: 1
- Normalized JSON: `pm_bot\tests\fixtures\practical_market_queue_batch\inputs\esports.one_market_input.json`

## Missing evidence

- Final match result sheet

## Source references

- `esports_roster_note` Synthetic Roster Note - `current`
- `esports_match_note` Synthetic Match Note - `current`

## Safety boundary

- Local packet normalization only.
- No live fetch or external API call was performed.
- Missing evidence is preserved instead of invented.
