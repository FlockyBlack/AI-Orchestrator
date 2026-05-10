# PMBOT Local Market Packet Import

- Input: `pm_bot\tests\fixtures\practical_market_queue_batch\seeds\politics.seed.json`
- Output contract: `pmbot_one_market_input.v1`
- Market ID: `synthetic-politics-measure-001`
- Market title: Will the synthetic policy measure pass committee by June 3?
- Sources preserved: 2
- Missing evidence items: 1
- Normalized JSON: `pm_bot\tests\fixtures\practical_market_queue_batch\inputs\politics.one_market_input.json`

## Missing evidence

- Final committee clerk record

## Source references

- `politics_committee_note_a` Synthetic Committee Note A - `current`
- `politics_committee_note_b` Synthetic Committee Note B - `current`

## Safety boundary

- Local packet normalization only.
- No live fetch or external API call was performed.
- Missing evidence is preserved instead of invented.
