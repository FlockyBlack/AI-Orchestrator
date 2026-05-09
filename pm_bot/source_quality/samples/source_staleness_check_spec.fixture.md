# PMBOT Source Staleness Check Spec

Spec: `source_staleness_check_spec_fixture_001`
Build: `source_staleness_check_spec_fixture_001-6d7b66d4f994`
Run mode: `local_static_source_staleness_check_spec`
Operator review: `pending_operator_review`

## Static Reference Clock

- Reference timestamp: `2026-05-10T00:30:00Z`
- Reference source: `request_fixture_static_value`
- System clock used: `false`

## Summary Counts

- Source staleness checks: 4
- Source evidence links: 4
- Source artifact references: 4
- Timestamp fields present: 3
- Timestamp fields missing: 1
- Local references: 7
- Review checks: 16

## Source Evidence Link Map

- Link map: `pm_bot/source_quality/samples/source_evidence_link_map.fixture.json`
- Map: `source_evidence_link_map_fixture_001`
- Build: `source_evidence_link_map_fixture_001-a888c8609457`
- Rows: 4

## Source Staleness Checks

- `airport_station_observation_log` (Airport station observation log)
  - Source artifact: `pm_bot/tests/fixtures/weather/airport_station_observation_log_snapshot.json`
  - Source evidence link: `source_evidence_link_map_fixture_001.airport_station_observation_log.source_evidence_link`
  - Timestamp field: `observation_timestamp`
  - Age seconds: `1920`
  - Staleness state: `within_static_review_window`
  - Review checks: 4 pending operator review
- `official_daily_climate_report` (Official daily climate report)
  - Source artifact: `pm_bot/tests/fixtures/weather/official_daily_climate_report_snapshot.json`
  - Source evidence link: `source_evidence_link_map_fixture_001.official_daily_climate_report.source_evidence_link`
  - Timestamp field: `report_timestamp`
  - Age seconds: `1500`
  - Staleness state: `within_static_review_window`
  - Review checks: 4 pending operator review
- `static_crypto_reference_snapshot_2026_05_09_btc` (Static crypto reference sample)
  - Source artifact: `pm_bot/tests/fixtures/crypto_paperlive_observation_ledger/static_crypto_reference_snapshot.valid.json`
  - Source evidence link: `source_evidence_link_map_fixture_001.static_crypto_reference_snapshot_2026_05_09_btc.source_evidence_link`
  - Timestamp field: `reported_at_utc`
  - Age seconds: `88200`
  - Staleness state: `within_static_review_window`
  - Review checks: 4 pending operator review
- `unified_source_quality_ledger_sample` (Unified source quality ledger sample)
  - Source artifact: `pm_bot/source_quality/samples/unified_source_quality_ledger.fixture.json`
  - Source evidence link: `source_evidence_link_map_fixture_001.unified_source_quality_ledger_sample.source_evidence_link`
  - Timestamp field: `not required by rule`
  - Age seconds: `not recorded`
  - Staleness state: `timestamp_not_required_by_rule`
  - Review checks: 4 pending operator review

## Operator Review Steps

- Confirm each source has one local staleness rule and one check row.
- Confirm timestamp fields, age windows, and digests match local static artifacts.
- Record disputes outside this spec before any later status change.

## Safety

- Local fixture/static input only.
- Uses the request fixture reference timestamp, not the system clock.
- Makes no network, LLM, endpoint, wallet, order, runtime, browser, scheduler, or worker calls.
- Records descriptive age windows, digests, and pending review state only.
- Does not authorize execution and is not runtime input.
