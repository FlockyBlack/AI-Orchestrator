# PMBOT Source Evidence Link Map

Map: `source_evidence_link_map_fixture_001`
Build: `source_evidence_link_map_fixture_001-a888c8609457`
Run mode: `local_static_source_evidence_link_map`
Operator review: `pending_operator_review`

## Summary Counts

- Source evidence links: 4
- Source artifact references: 4
- Inventory rows linked: 4
- Local references: 7
- Review checks: 16

## Source Inventory

- Ledger: `pm_bot/source_quality/samples/source_evidence_inventory_ledger.fixture.json`
- Inventory: `source_evidence_inventory_ledger_fixture_001`
- Build: `source_evidence_inventory_ledger_fixture_001-911f62d75877`
- Rows: 4

## Source Evidence Links

- `airport_station_observation_log` (Airport station observation log)
  - Source artifact: `pm_bot/tests/fixtures/weather/airport_station_observation_log_snapshot.json`
  - Source evidence row: `source_evidence_inventory_ledger_fixture_001.airport_station_observation_log.source_evidence`
  - Inventory ledger: `pm_bot/source_quality/samples/source_evidence_inventory_ledger.fixture.json`
  - Operator report: `pm_bot/source_quality/samples/source_evidence_inventory_ledger.fixture.md`
  - Documentation: `docs/PMBOT_SOURCE_EVIDENCE_001_SOURCE_INVENTORY_LEDGER_LOCAL_ONLY.md`
  - Review checks: 4 pending operator review
- `official_daily_climate_report` (Official daily climate report)
  - Source artifact: `pm_bot/tests/fixtures/weather/official_daily_climate_report_snapshot.json`
  - Source evidence row: `source_evidence_inventory_ledger_fixture_001.official_daily_climate_report.source_evidence`
  - Inventory ledger: `pm_bot/source_quality/samples/source_evidence_inventory_ledger.fixture.json`
  - Operator report: `pm_bot/source_quality/samples/source_evidence_inventory_ledger.fixture.md`
  - Documentation: `docs/PMBOT_SOURCE_EVIDENCE_001_SOURCE_INVENTORY_LEDGER_LOCAL_ONLY.md`
  - Review checks: 4 pending operator review
- `static_crypto_reference_snapshot_2026_05_09_btc` (Static crypto reference sample)
  - Source artifact: `pm_bot/tests/fixtures/crypto_paperlive_observation_ledger/static_crypto_reference_snapshot.valid.json`
  - Source evidence row: `source_evidence_inventory_ledger_fixture_001.static_crypto_reference_snapshot_2026_05_09_btc.source_evidence`
  - Inventory ledger: `pm_bot/source_quality/samples/source_evidence_inventory_ledger.fixture.json`
  - Operator report: `pm_bot/source_quality/samples/source_evidence_inventory_ledger.fixture.md`
  - Documentation: `docs/PMBOT_SOURCE_EVIDENCE_001_SOURCE_INVENTORY_LEDGER_LOCAL_ONLY.md`
  - Review checks: 4 pending operator review
- `unified_source_quality_ledger_sample` (Unified source quality ledger sample)
  - Source artifact: `pm_bot/source_quality/samples/unified_source_quality_ledger.fixture.json`
  - Source evidence row: `source_evidence_inventory_ledger_fixture_001.unified_source_quality_ledger_sample.source_evidence`
  - Inventory ledger: `pm_bot/source_quality/samples/source_evidence_inventory_ledger.fixture.json`
  - Operator report: `pm_bot/source_quality/samples/source_evidence_inventory_ledger.fixture.md`
  - Documentation: `docs/PMBOT_SOURCE_EVIDENCE_001_SOURCE_INVENTORY_LEDGER_LOCAL_ONLY.md`
  - Review checks: 4 pending operator review

## Operator Review Steps

- Confirm every source evidence row has a local artifact link and inventory row link.
- Confirm every linked local reference remains static and under allowed paths.
- Record disputes outside this map before any later readiness change.

## Safety

- Local fixture/static input only.
- Makes no network, LLM, endpoint, wallet, order, runtime, browser, scheduler, or worker calls.
- Records local references, byte counts, digests, and pending review state only.
- Does not authorize execution and is not runtime input.
