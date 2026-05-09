# PMBOT Source Evidence Inventory Ledger

Inventory: `source_evidence_inventory_ledger_fixture_001`
Build: `source_evidence_inventory_ledger_fixture_001-911f62d75877`
Run mode: `local_static_source_evidence_inventory`
Operator review: `pending_operator_review`

## Summary Counts

- Source evidence rows: 4
- Local references: 4
- Declared fields: 39
- Present fields: 39
- Missing fields: 0
- Review checks: 12

## Source Evidence Rows

- `airport_station_observation_log` (Airport station observation log)
  - Local artifact: `pm_bot/tests/fixtures/weather/airport_station_observation_log_snapshot.json`
  - Snapshot: `fixture_airport_station_observation_log_2026_05_09`
  - Role: `weather_observation_fixture`
  - Digest: `e27ccc4dedeb4b3da48cd9e636d137e78be3cefa9683598879b2aed122370a8c`
  - Fields present: 9/9
  - Review checks: 3 pending operator review
- `official_daily_climate_report` (Official daily climate report)
  - Local artifact: `pm_bot/tests/fixtures/weather/official_daily_climate_report_snapshot.json`
  - Snapshot: `fixture_official_daily_climate_report_2026_05_09`
  - Role: `weather_observation_fixture`
  - Digest: `5141db855f8039139fe1b875a2c945c06f83d1fa608a206a35122fd7c7ef5867`
  - Fields present: 9/9
  - Review checks: 3 pending operator review
- `static_crypto_reference_snapshot_2026_05_09_btc` (Static crypto reference sample)
  - Local artifact: `pm_bot/tests/fixtures/crypto_paperlive_observation_ledger/static_crypto_reference_snapshot.valid.json`
  - Snapshot: `static_crypto_reference_snapshot_2026_05_09_btc`
  - Role: `crypto_reference_fixture`
  - Digest: `1f0ffac6d0264f62bb8bf8689de09addc80fabf2069c15a76d40c306178fb1fe`
  - Fields present: 11/11
  - Review checks: 3 pending operator review
- `unified_source_quality_ledger_sample` (Unified source quality ledger sample)
  - Local artifact: `pm_bot/source_quality/samples/unified_source_quality_ledger.fixture.json`
  - Snapshot: `unified_source_quality_ledger_fixture_001-be4cc5453863`
  - Role: `source_quality_review_sample`
  - Digest: `7b95524e7c16ec9abec0ea15b8509c3a9c55ce310a8c0fde84abba4f611f74a9`
  - Fields present: 10/10
  - Review checks: 3 pending operator review

## Operator Review Steps

- Confirm every local reference stays under allowed static paths.
- Confirm content digests and field names match local artifacts.
- Record disputes outside this ledger before any later readiness change.

## Safety

- Local fixture/static input only.
- Makes no network, LLM, endpoint, wallet, order, runtime, browser, scheduler, or worker calls.
- Records file presence, digests, field names, and review state only.
- Not execution approval and not runtime input.
