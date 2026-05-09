# PMBOT Source Evidence 002 Source Evidence Link Map Local Only

Task: `PMBOT-SOURCE-EVIDENCE-002-SOURCE-EVIDENCE-LINK-MAP-LOCAL-ONLY`

Map: `source_evidence_link_map_fixture_001`
Contract: `pmbot_source_evidence_link_map.v1`
Run mode: `local_static_source_evidence_link_map`
Operator review: `pending_operator_review`

## Purpose

This document registers the local PMBOT source evidence link map for operator review. The map is deterministic and built from local files, local fixtures, and static samples only.

The map links each local source evidence inventory row to its source artifact, source evidence inventory ledger, inventory operator report, and documentation register. It records local references, byte counts, SHA-256 digests, and pending review state only. It does not copy source values, refresh live data, call services, approve execution, or produce forecast scoring, action guidance, or selection advice.

## Static Artifacts

The local request fixture is:

`pm_bot/tests/fixtures/source_quality/source_evidence_link_map_request.valid.json`

The generated static link map and report samples are:

- `pm_bot/source_quality/samples/source_evidence_link_map.fixture.json`
- `pm_bot/source_quality/samples/source_evidence_link_map.fixture.md`

The implementation is:

`pm_bot/source_quality/source_evidence_link_map.py`

## Source Basis

Reviewed local PMBOT artifacts:

- `pm_bot/source_quality/samples/source_evidence_inventory_ledger.fixture.json`
- `pm_bot/source_quality/samples/source_evidence_inventory_ledger.fixture.md`
- `docs/PMBOT_SOURCE_EVIDENCE_001_SOURCE_INVENTORY_LEDGER_LOCAL_ONLY.md`
- `pm_bot/tests/fixtures/weather/official_daily_climate_report_snapshot.json`
- `pm_bot/tests/fixtures/weather/airport_station_observation_log_snapshot.json`
- `pm_bot/tests/fixtures/crypto_paperlive_observation_ledger/static_crypto_reference_snapshot.valid.json`
- `pm_bot/source_quality/samples/unified_source_quality_ledger.fixture.json`
- `pm_bot/tests/test_source_evidence_inventory_ledger.py`
- `tests/test_codex_queue_pmbot_templates.py`

These inputs keep the link map local-only, static, descriptive, and pending operator review.

## Link Map Content

Each source evidence link row records:

- source identity and label
- source evidence inventory record id
- local source artifact reference, byte count, and digest
- source evidence inventory ledger reference, byte count, and digest
- inventory operator report reference, byte count, and digest
- documentation reference, byte count, and digest
- known limitations
- pending operator review checks

The link map intentionally avoids copying artifact field values. A human operator can use the local references and digests to review the linked artifacts directly.

## Operator Review

Operators review:

- every source evidence inventory row has exactly one local link row
- every linked local reference stays under allowed static paths
- digests and byte counts correspond to the local artifacts
- source artifact references match the inventory ledger rows
- every link row remains pending operator review
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
- This link map is not execution approval and is not runtime input.

## Validation

Required local validation commands:

- `python -m compileall pm_bot tests`
- `pytest pm_bot/tests tests/test_codex_queue_pmbot_templates.py`
