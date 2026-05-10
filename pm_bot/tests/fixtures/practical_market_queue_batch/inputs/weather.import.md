# PMBOT Local Market Packet Import

- Input: `pm_bot\tests\fixtures\practical_market_queue_batch\seeds\weather.seed.json`
- Output contract: `pmbot_one_market_input.v1`
- Market ID: `synthetic-weather-rain-001`
- Market title: Will the synthetic city record measurable rain on June 1?
- Sources preserved: 2
- Missing evidence items: 1
- Normalized JSON: `pm_bot\tests\fixtures\practical_market_queue_batch\inputs\weather.one_market_input.json`

## Missing evidence

- Final station precipitation total for 2026-06-01

## Source references

- `weather_station_bulletin` Synthetic Station Bulletin - `current`
- `weather_event_note` Synthetic Event Note - `current`

## Safety boundary

- Local packet normalization only.
- No live fetch or external API call was performed.
- Missing evidence is preserved instead of invented.
