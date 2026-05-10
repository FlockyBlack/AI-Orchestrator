# PMBOT Local Market Packet Import

- Input: `pm_bot\tests\fixtures\practical_market_queue_batch\seeds\crypto.seed.json`
- Output contract: `pmbot_one_market_input.v1`
- Market ID: `synthetic-crypto-reference-001`
- Market title: Will the synthetic token close above the reference level on June 2?
- Sources preserved: 2
- Missing evidence items: 1
- Normalized JSON: `pm_bot\tests\fixtures\practical_market_queue_batch\inputs\crypto.one_market_input.json`

## Missing evidence

- Final reference close record for 2026-06-02

## Source references

- `crypto_archived_reference` Synthetic Archived Reference Close - `stale`
- `crypto_rules_capture` Synthetic Crypto Rules Capture - `current`

## Safety boundary

- Local packet normalization only.
- No live fetch or external API call was performed.
- Missing evidence is preserved instead of invented.
