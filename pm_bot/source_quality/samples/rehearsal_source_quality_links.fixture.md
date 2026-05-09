# PMBOT Rehearsal Source Quality Links

Task: `PMBOT-REHEARSAL-014-REHEARSAL-SOURCE-QUALITY-LINKS-LOCAL-ONLY`
Link set: `pmbot-rehearsal-source-quality-links-001`
Build: `pmbot-rehearsal-source-quality-links-001-ed9512fd23a0`
Contract: `pmbot_rehearsal_source_quality_links.v1`
Run mode: `local_static_rehearsal_source_quality_links`
Operator review: `pending_operator_review`

## Summary

- Rehearsal source quality links: 2
- Rehearsal artifacts: 3
- Source quality artifacts: 6
- Source quality record links: 12
- Rehearsal record links: 18
- Local references: 10

## Rehearsal Artifacts

- `rehearsal_source_evidence_bundle_fixture` -> `pm_bot/tests/fixtures/rehearsal/pmbot_rehearsal_source_evidence_bundle.valid.json` (1 records)
- `rehearsal_staleness_case_set_fixture` -> `pm_bot/tests/fixtures/rehearsal/pmbot_rehearsal_staleness_case_set.valid.json` (6 records)
- `rehearsal_contradiction_case_set_fixture` -> `pm_bot/tests/fixtures/rehearsal/pmbot_rehearsal_contradiction_case_set.valid.json` (6 records)

## Source Quality Artifacts

- `unified_source_quality_ledger_sample` -> `pm_bot/source_quality/samples/unified_source_quality_ledger.fixture.json` (2 records)
- `source_quality_report_summary_sample` -> `pm_bot/source_quality/samples/source_quality_report_summary.fixture.json` (2 records)
- `source_quality_regression_fixture_sample` -> `pm_bot/source_quality/samples/source_quality_regression.fixture.json` (2 records)
- `source_evidence_link_map_sample` -> `pm_bot/source_quality/samples/source_evidence_link_map.fixture.json` (4 records)
- `source_staleness_check_spec_sample` -> `pm_bot/source_quality/samples/source_staleness_check_spec.fixture.json` (4 records)
- `source_contradiction_ledger_sample` -> `pm_bot/source_quality/samples/source_contradiction_ledger.fixture.json` (1 records)

## Link Rows

- `official_daily_climate_report`
  - Source quality ledger row: `unified_source_quality_ledger_fixture_001.official_daily_climate_report.source_quality_review`
  - Source quality report row: `unified_source_quality_ledger_fixture_001.official_daily_climate_report.source_quality_review.source_quality_report_summary`
  - Source quality regression row: `unified_source_quality_ledger_fixture_001.official_daily_climate_report.source_quality_review`
  - Source evidence link: `source_evidence_link_map_fixture_001.official_daily_climate_report.source_evidence_link`
  - Source staleness check: `source_staleness_check_spec_fixture_001.official_daily_climate_report.source_staleness_check`
  - Source contradiction rows: 1
  - Rehearsal staleness cases: 3
  - Rehearsal contradiction cases: 6
- `airport_station_observation_log`
  - Source quality ledger row: `unified_source_quality_ledger_fixture_001.airport_station_observation_log.source_quality_review`
  - Source quality report row: `unified_source_quality_ledger_fixture_001.airport_station_observation_log.source_quality_review.source_quality_report_summary`
  - Source quality regression row: `unified_source_quality_ledger_fixture_001.airport_station_observation_log.source_quality_review`
  - Source evidence link: `source_evidence_link_map_fixture_001.airport_station_observation_log.source_evidence_link`
  - Source staleness check: `source_staleness_check_spec_fixture_001.airport_station_observation_log.source_staleness_check`
  - Source contradiction rows: 1
  - Rehearsal staleness cases: 1
  - Rehearsal contradiction cases: 6

## Operator Review Steps

- Confirm each rehearsal artifact row resolves to local source quality record identifiers.
- Confirm source quality artifact byte counts and SHA-256 digests match current local bytes.
- Confirm values remain in referenced local artifacts and link rows stay pending operator review.

## Safety

- Local files, local fixtures, and static samples only.
- Makes no network, OpenRouter, Polymarket, LLM, external service, authenticated endpoint, wallet, order, transaction, runtime, browser, scheduler, or worker calls.
- Records local links and pending review state only; source values remain in referenced artifacts.
- No forecast scoring, action guidance, market ranking, outcome resolution, selection advice, or trade instruction output.
- Not execution approval and not runtime input.
