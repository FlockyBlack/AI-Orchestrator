# PMBOT Source Contradiction Ledger

Ledger: `source_contradiction_ledger_fixture_001`
Build: `source_contradiction_ledger_fixture_001-5d1565a70e0d`
Run mode: `local_static_source_contradiction_ledger`
Operator review: `pending_operator_review`

## Summary Counts

- Source contradiction rows: 1
- Source staleness checks: 2
- Source artifact references: 2
- Subject key comparisons: 2
- Subject key differences: 0
- Field comparisons: 1
- Static value differences: 1
- Local references: 5
- Review checks: 4

## Source Staleness Spec

- Spec: `pm_bot/source_quality/samples/source_staleness_check_spec.fixture.json`
- Spec id: `source_staleness_check_spec_fixture_001`
- Build: `source_staleness_check_spec_fixture_001-6d7b66d4f994`
- Rows: 4

## Source Contradiction Rows

- `weather_daily_high_temperature_static_compare` (Weather daily high temperature static comparison)
  - Left source: `official_daily_climate_report` -> `pm_bot/tests/fixtures/weather/official_daily_climate_report_snapshot.json`
  - Right source: `airport_station_observation_log` -> `pm_bot/tests/fixtures/weather/airport_station_observation_log_snapshot.json`
  - Contradiction state: `static_value_difference_pending_review`
  - Review checks: 4 pending operator review
  - daily_high_temperature_f: `high_temperature_f`=`74`; `observed_high_temperature_f`=`73`; state `different_static_values_pending_review`

## Operator Review Steps

- Confirm each source pair is copied from local static artifact references.
- Confirm mapped fields and static values match the local artifact bytes.
- Record unresolved differences outside this ledger before any later status change.

## Safety

- Local fixture/static input only.
- Makes no network, LLM, endpoint, wallet, order, runtime, browser, scheduler, or worker calls.
- Records local static source differences and pending review state only.
- Does not authorize execution and is not runtime input.
