# PMBOT Local Market Packet Import

- Input: `pm_bot\tests\fixtures\practical_market_queue_batch\seeds\generic.seed.json`
- Output contract: `pmbot_one_market_input.v1`
- Market ID: `synthetic-generic-event-001`
- Market title: Will the synthetic event certificate be filed by June 5?
- Sources preserved: 2
- Missing evidence items: 2
- Normalized JSON: `pm_bot\tests\fixtures\practical_market_queue_batch\inputs\generic.one_market_input.json`

## Missing evidence

- Actual certificate filing record
- Clerk timestamp for the filing

## Source references

- `generic_planning_note` Synthetic Planning Note - `current`
- `generic_event_rules` Synthetic Event Rules Note - `current`

## Safety boundary

- Local packet normalization only.
- No live fetch or external API call was performed.
- Missing evidence is preserved instead of invented.
