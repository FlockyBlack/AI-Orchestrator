# Selected Ingest Research Packet Stubs

Deterministic offline bridge from validated ingest-selected candidates to empty research packet stubs.

## Summary
- selected_market_ids_read: 5
- research_packet_stubs_created: 5
- completion_status_all_stub_only: true

## Source Artifacts
- selection_index: `pm_bot/ingest/operator_candidate_selection_index.v1.json`
- selection_overlay: `pm_bot/ingest/operator_candidate_selection_overlay_selected_first5.v1.json`
- normalized_preview: `pm_bot/ingest/normalized_market_preview.v1.json`

## Safety Boundary
- offline_only: true
- manual_invocation_only: true
- stub_only: true
- external_fetch_performed: false
- downstream_wiring_changed: false

## Selected Market IDs
- `692258`
- `824952`
- `691547`
- `597964`
- `598936`

## Packet Stubs

### market_id: `692258`
- title: MicroStrategy sells any Bitcoin by June 30, 2026?
- event_id: `16167`
- event_title: MicroStrategy sells any Bitcoin by ___ ?
- category: Finance / Economy / Business / 2025 Predictions / Crypto / MicroStrategy / Stocks
- packet_type: `selected_ingest_market_research_stub`
- current_yes_price: 0.0285
- liquidity: 74969.19206
- volume: 998871.1045009972
- deadline: 2026-07-01T04:00:00Z
- completion_status: `stub_only`
- missing_information_count: 6

### market_id: `824952`
- title: MicroStrategy sells any Bitcoin by December 31, 2026?
- event_id: `16167`
- event_title: MicroStrategy sells any Bitcoin by ___ ?
- category: Finance / Economy / Business / 2025 Predictions / Crypto / MicroStrategy / Stocks
- packet_type: `selected_ingest_market_research_stub`
- current_yes_price: 0.095
- liquidity: 33862.5213
- volume: 574606.4678400013
- deadline: 2026-07-01T04:00:00Z
- completion_status: `stub_only`
- missing_information_count: 6

### market_id: `691547`
- title: Kraken IPO by December 31, 2026?
- event_id: `16183`
- event_title: Kraken IPO by ___ ?
- category: exchange / Tech / Crypto / Finance / Business / 2025 Predictions / Featured / IPOs
- packet_type: `selected_ingest_market_research_stub`
- current_yes_price: 0.74
- liquidity: 3865.8225
- volume: 506317.2901440019
- deadline: 2027-01-01T05:00:00Z
- completion_status: `stub_only`
- missing_information_count: 6

### market_id: `597964`
- title: Macron out by June 30, 2026?
- event_id: `16263`
- event_title: Macron out by...?
- category: France / Politics / Macron / World / 2025 Predictions / resign
- packet_type: `selected_ingest_market_research_stub`
- current_yes_price: 0.0155
- liquidity: 48751.13558
- volume: 343942.07421
- deadline: 2026-06-30T12:00:00Z
- completion_status: `stub_only`
- missing_information_count: 6

### market_id: `598936`
- title: Will the next UK election be called by June 30, 2026?
- event_id: `16423`
- event_title: UK election called by...?
- category: Starmer / UK / pedophile / England
- packet_type: `selected_ingest_market_research_stub`
- current_yes_price: 0.0525
- liquidity: 1241.81341
- volume: 19020.393714000005
- deadline: 2026-06-30T12:00:00Z
- completion_status: `stub_only`
- missing_information_count: 6
