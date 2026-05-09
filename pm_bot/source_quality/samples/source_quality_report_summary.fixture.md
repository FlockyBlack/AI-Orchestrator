# PMBOT Source Quality Report Summary

Summary: `unified_source_quality_ledger_fixture_001.source_quality_report_summary`
Build: `unified_source_quality_ledger_fixture_001-be4cc5453863.source_quality_report_summary`
Ledger: `unified_source_quality_ledger_fixture_001`
Ledger build: `unified_source_quality_ledger_fixture_001-be4cc5453863`
Run mode: `local_source_quality_report_summary`
Operator review: `pending_operator_review`

## Summary Counts

- Source artifacts: 2
- Report summary rows: 2
- Declared fields: 8
- Present fields: 8
- Missing fields: 0
- Review checks: 4
- Known limitations: 4

## Source Report Rows

- `official_daily_climate_report` (Official daily climate report)
  - Local artifact: `pm_bot/tests/fixtures/weather/official_daily_climate_report_snapshot.json`
  - Snapshot: `fixture_official_daily_climate_report_2026_05_09`
  - Artifact role: `weather_observation_snapshot`
  - Fields present: 4/4
  - Review checks: 2 pending operator review
  - Known limitations: 2
- `airport_station_observation_log` (Airport station observation log)
  - Local artifact: `pm_bot/tests/fixtures/weather/airport_station_observation_log_snapshot.json`
  - Snapshot: `fixture_airport_station_observation_log_2026_05_09`
  - Artifact role: `weather_observation_snapshot`
  - Fields present: 4/4
  - Review checks: 2 pending operator review
  - Known limitations: 2

## Operator Review Steps

- Confirm each source artifact is an expected local fixture or static sample.
- Confirm each declared field is present before using the ledger as an operator review input.
- Record any source disputes outside this descriptive ledger.

## Safety

- Local fixture/static input only.
- Makes no network, LLM, external market API, wallet, order, transaction endpoint, runtime, browser, scheduler, or worker calls.
- Descriptive report summary only; no outcome resolution or trade instruction output.
- Not execution approval and not runtime input.
