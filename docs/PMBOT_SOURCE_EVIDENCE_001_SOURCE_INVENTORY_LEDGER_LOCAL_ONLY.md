# PMBOT Source Evidence 001 Source Inventory Ledger Local Only

Task: `PMBOT-SOURCE-EVIDENCE-001-SOURCE-INVENTORY-LEDGER-LOCAL-ONLY`

Inventory: `source_evidence_inventory_ledger_fixture_001`
Contract: `pmbot_source_evidence_inventory_ledger.v1`
Run mode: `local_static_source_evidence_inventory`
Operator review: `pending_operator_review`

## Purpose

This document registers the local PMBOT source evidence inventory ledger for operator review. The ledger is deterministic and built from local files, local fixtures, and static samples only.

The ledger records source artifact presence, local references, content digests, top-level JSON field names, value types, and pending review checks. It does not copy source values into the inventory, refresh live data, call services, approve execution, or produce forecast scoring, action guidance, or selection advice.

## Static Artifacts

The local request fixture is:

`pm_bot/tests/fixtures/source_quality/source_evidence_inventory_ledger_request.valid.json`

The generated static ledger and report samples are:

- `pm_bot/source_quality/samples/source_evidence_inventory_ledger.fixture.json`
- `pm_bot/source_quality/samples/source_evidence_inventory_ledger.fixture.md`

The implementation is:

`pm_bot/source_quality/source_evidence_inventory_ledger.py`

## Source Basis

Reviewed local PMBOT artifacts:

- `pm_bot/tests/fixtures/weather/official_daily_climate_report_snapshot.json`
- `pm_bot/tests/fixtures/weather/airport_station_observation_log_snapshot.json`
- `pm_bot/tests/fixtures/crypto_paperlive_observation_ledger/static_crypto_reference_snapshot.valid.json`
- `pm_bot/source_quality/samples/unified_source_quality_ledger.fixture.json`
- `pm_bot/tests/fixtures/source_quality/unified_source_quality_ledger_request.valid.json`
- `pm_bot/tests/test_unified_source_quality_ledger.py`
- `pm_bot/tests/test_live_data_source_inventory.py`
- `tests/test_codex_queue_pmbot_templates.py`

These inputs keep the evidence inventory local-only, static, descriptive, and pending operator review.

## Ledger Content

Each source evidence row records:

- source identity and label
- local artifact path
- source domain and source type
- evidence role
- contract version observed in the local artifact
- snapshot identifier
- artifact byte count and SHA-256 digest
- declared top-level JSON field names and observed value types
- known limitations
- pending operator review checks

The ledger intentionally avoids copying artifact field values. A human operator can use the local references and digests to review the artifacts directly.

## Operator Review

Operators review:

- every local reference stays under allowed static paths
- every source row remains pending operator review
- digests and byte counts correspond to the local artifacts
- field names are descriptive inventory entries only
- source values are reviewed from the source files when needed, not copied into the ledger
- sensitive paths, credential stores, wallets, signing material, endpoint calls, runtime wiring, browser automation, workers, and timed automation remain outside scope
- validation output is captured before any later readiness status change

## Safety

- Local files, local fixtures, and static samples only.
- No network calls.
- No LLM provider calls.
- No external market API calls.
- No authenticated endpoint use.
- No credential, wallet, private-key, seed, signing, order, payment, or transaction path access.
- No runtime, dispatcher, scheduler, worker, browser, resident process, timed automation, or app-server wiring.
- No forecast scoring, action guidance, source ranking, numeric prediction metric, stance selection, or trade instruction output.
- This ledger is not execution approval and is not runtime input.

## Validation

Required local validation commands:

- `python -m compileall pm_bot tests`
- `pytest pm_bot/tests tests/test_codex_queue_pmbot_templates.py`
