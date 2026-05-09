# PMBOT Source Evidence 003 Source Staleness Check Spec Local Only

Task: `PMBOT-SOURCE-EVIDENCE-003-SOURCE-STALENESS-CHECK-SPEC-LOCAL-ONLY`

Spec: `source_staleness_check_spec_fixture_001`
Contract: `pmbot_source_staleness_check_spec.v1`
Run mode: `local_static_source_staleness_check_spec`
Operator review: `pending_operator_review`

## Purpose

This document registers the local PMBOT source staleness check spec for operator review. The spec is deterministic and built from local files, local fixtures, and static samples only.

The spec maps each local source evidence link row to a descriptive staleness rule. It records local references, byte counts, SHA-256 digests, a fixed request fixture reference timestamp, timestamp field presence, descriptive age windows, and pending review state only. It does not refresh source data, call services, approve execution, or produce predictive metrics, stance output, source preference output, or trade instruction output.

## Static Artifacts

The local request fixture is:

`pm_bot/tests/fixtures/source_quality/source_staleness_check_spec_request.valid.json`

The generated static spec and report samples are:

- `pm_bot/source_quality/samples/source_staleness_check_spec.fixture.json`
- `pm_bot/source_quality/samples/source_staleness_check_spec.fixture.md`

The implementation is:

`pm_bot/source_quality/source_staleness_check_spec.py`

## Source Basis

Reviewed local PMBOT artifacts:

- `pm_bot/source_quality/samples/source_evidence_link_map.fixture.json`
- `pm_bot/source_quality/samples/source_evidence_link_map.fixture.md`
- `docs/PMBOT_SOURCE_EVIDENCE_002_SOURCE_EVIDENCE_LINK_MAP_LOCAL_ONLY.md`
- `pm_bot/tests/fixtures/weather/official_daily_climate_report_snapshot.json`
- `pm_bot/tests/fixtures/weather/airport_station_observation_log_snapshot.json`
- `pm_bot/tests/fixtures/crypto_paperlive_observation_ledger/static_crypto_reference_snapshot.valid.json`
- `pm_bot/source_quality/samples/unified_source_quality_ledger.fixture.json`
- `pm_bot/tests/test_source_evidence_link_map.py`
- `tests/test_codex_queue_pmbot_templates.py`

These inputs keep the staleness spec local-only, static, descriptive, and pending operator review.

## Spec Content

Each source staleness check row records:

- source identity and label
- source evidence link id
- source artifact reference, byte count, and digest
- timestamp field candidates and selected timestamp field, when the rule requires one
- request fixture reference timestamp
- descriptive age seconds, when a timestamp field exists
- rule threshold label and maximum age seconds, when applicable
- pending operator review checks

The spec uses `2026-05-10T00:30:00Z` from the request fixture as the reference timestamp. It does not use the system clock, timers, schedulers, workers, browser automation, or external services.

## Operator Review

Operators review:

- every source evidence link row has exactly one local staleness check row
- every local reference stays under allowed static paths
- digests and byte counts correspond to the local artifacts
- timestamp fields and descriptive age windows match local static artifact values
- every check row remains pending operator review
- sensitive paths, credential stores, wallets, signing material, endpoint calls, runtime wiring, browser automation, workers, and timed automation remain outside scope
- validation output is captured before any later status change

## Safety

- Local files, local fixtures, and static samples only.
- No network calls.
- No LLM provider calls.
- No external market API calls.
- No authenticated endpoint use.
- No credential, wallet, private-key, seed, signing, order, payment, or transaction path access.
- No runtime, dispatcher, scheduler, worker, browser, resident process, timed automation, or app-server wiring.
- No predictive metrics, source preference output, stance output, or trade instruction output.
- This spec is not execution approval and is not runtime input.

## Validation

Required local validation commands:

- `python -m compileall pm_bot tests`
- `pytest pm_bot/tests tests/test_codex_queue_pmbot_templates.py`
