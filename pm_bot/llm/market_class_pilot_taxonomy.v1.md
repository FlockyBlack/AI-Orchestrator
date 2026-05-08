# PMBOT SOURCE-008B Market Class Pilot Taxonomy

This taxonomy defines the first protocol-only market classes for future read-only source capture pilots. It is local-only and does not fetch data.

## Class Order

1. esports
2. weather
3. crypto

## Esports

- description: Markets resolved by recorded esports match, map, tournament, roster, or event outcomes where the settlement source should be an official tournament, organizer, league, game publisher, or recognized match data page.
- expected resolution source types: official tournament match page; official league or organizer results page; game publisher event page; recognized match statistics page when official source is unavailable.
- common resolution risks: forfeits, technical defaults, map count wording, post-dispute updates, team aliases, roster labels, and best-of format ambiguity.
- required capture fields: market_id, market_class, market_title_or_question, resolution_wording, event_name, game_title, team_or_player_names, match_or_event_start_time, official_source_name, official_source_reference, source_checked_at_local, captured_resolution_text, source_reliability_review, operator_notes, capture_status.
- operator review focus: exact match, map, team, event, special handling for postponements or replays, official source identity, timestamp, and source-name mismatch.
- future read-only fetch requirements: public unauthenticated fetch only in a separate approved task; raw artifact writes only; no canonical packet or capture template mutation.

## Weather

- description: Markets resolved by weather observations, measurements, warnings, or station reports where the settlement source should be an official meteorological agency, station, or published dataset named by the market.
- expected resolution source types: national or regional meteorological agency page; named station observation record; official warning or advisory archive; official climate or daily summary dataset.
- common resolution risks: station identity, timezone, observation window, units, rounding, revised preliminary readings, and mistaken nearby stations.
- required capture fields: market_id, market_class, market_title_or_question, resolution_wording, weather_location, station_or_agency_name, measurement_type, measurement_window, measurement_units, official_source_name, official_source_reference, source_checked_at_local, captured_resolution_text, source_reliability_review, operator_notes, capture_status.
- operator review focus: location, station, measurement type, units, time window, data revision risk, timezone handling, and source-detail gaps.
- future read-only fetch requirements: public unauthenticated fetch only in a separate approved task; raw artifact writes only; preserve agency or station identifiers and timestamps.

## Crypto

- description: Markets resolved by cryptocurrency price, index, chain event, ETF, or exchange-published event wording where the settlement source should be the named index, exchange, chain explorer, issuer page, or official market rules text.
- expected resolution source types: named price index methodology page; official exchange market data page; official chain explorer or protocol page; ETF issuer or regulatory filing page when named by the market; Polymarket rules text for exact settlement source naming.
- common resolution risks: price source, cutoff time, timezone, index methodology, chain reorganization, delayed data, ticker ambiguity, and named-source dependence.
- required capture fields: market_id, market_class, market_title_or_question, resolution_wording, asset_or_event_name, named_index_or_source, settlement_time_window, measurement_units, official_source_name, official_source_reference, source_checked_at_local, captured_resolution_text, source_reliability_review, operator_notes, capture_status.
- operator review focus: named source, asset identifier, measurement window, units, index methodology, timezone, cutoff wording, ticker ambiguity, and venue naming.
- future read-only fetch requirements: public unauthenticated fetch only in a separate approved task; raw artifact writes only; preserve named source and timestamp metadata.

## Safety Boundary

- no network calls
- no OpenRouter calls
- no Polymarket API calls
- no wallet or private key access
- no orders
- no runtime wiring
- no dispatcher, background worker, queue, or browser automation
- no canonical packet mutation
- no probability, EV, edge, confidence, side selection, trade recommendation, buy, sell, hold, enter, exit, guaranteed win, free money, or sure bet labels
