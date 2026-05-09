# PMBOT Supervised Live 002 Live Data Source Inventory Local Only

Task: `PMBOT-SUPERVISED-LIVE-002-LIVE-DATA-SOURCE-INVENTORY-LOCAL-ONLY`

Inventory: `pmbot-supervised-live-data-source-inventory-001`
Contract: `pmbot_supervised_live_data_source_inventory.v1`
Run mode: `local_static_live_data_source_inventory`
Operator review: `pending_operator_review`

## Purpose

This document defines the local live data source inventory for supervised readiness review. It is a deterministic operator review artifact built from local files, local fixtures, and static samples only.

The inventory is descriptive only. It is not execution approval, runtime input, market analysis, forecast scoring, action guidance, or selection advice.

## Static Fixture

The local fixture is:

`pm_bot/tests/fixtures/readiness/pmbot_live_data_source_inventory.valid.json`

The fixture records fixed source record fields, static local source records, source contract references, operator review checks, required validation commands, summary counts, and closed safety boundaries. It does not fetch live data, call endpoints, approve execution, or produce market instructions.

## Source Basis

Reviewed local PMBOT artifacts:

- `docs/PMBOT_SUPERVISED_LIVE_001_READ_ONLY_LIVE_DATA_CONTRACT_LOCAL_ONLY.md`
- `pm_bot/readiness/PMBOT_ROADMAP_002_PMBOT_LOCAL_TO_SUPERVISED_LIVE_GAP_MATRIX.md`
- `docs/PMBOT_SOURCE_LEDGER_001_UNIFIED_SOURCE_QUALITY_LEDGER_LOCAL_ONLY.md`
- `pm_bot/source_quality/samples/unified_source_quality_ledger.fixture.json`
- `pm_bot/tests/fixtures/weather/official_daily_climate_report_snapshot.json`
- `pm_bot/tests/fixtures/weather/airport_station_observation_log_snapshot.json`
- `pm_bot/tests/fixtures/crypto_paperlive_observation_ledger/static_crypto_reference_snapshot.valid.json`
- `tests/test_codex_queue_pmbot_templates.py`

These sources keep PMBOT readiness work local-only, static, paper-mode, and pending operator review.

## Inventory Fields

Each local live data source record keeps these fields in a fixed contract:

- `captured_at_utc`
- `contract_version`
- `excluded_operations`
- `freshness_label`
- `included_fields`
- `local_reference`
- `notes`
- `operator_review_status`
- `record_id`
- `source_access_mode`
- `source_class`
- `source_domain`
- `source_id`
- `source_label`
- `snapshot_id`

The inventory may identify local fixture presence, source labels, static timestamps, and field names. It may not include prices, probabilities, ranks, sides, stake sizing, market instructions, or execution fields.

## Operator Review Checklist

Operators review:

- all local references are inside the allowed documentation, readiness, source quality, and test paths
- static records are bounded and copied from local fixtures only
- field inventories name local fixture fields without copying market values into this inventory
- freshness labels are descriptive and do not claim current external state
- sensitive paths, credentials, wallets, signing material, and authenticated endpoints remain excluded
- runtime, dispatcher, scheduler, worker, browser, resident process, and app-server boundaries remain closed
- output remains descriptive and contains no forecast scoring, action guidance, or selection advice
- validation output is captured by a human before any later readiness status change

## Safety

- Local files and static fixtures only.
- No network calls.
- No LLM provider calls.
- No external market API calls.
- No authenticated endpoint use.
- No credential, wallet, private-key, seed, signing, order, trading endpoint, payment, or transaction path access.
- No runtime, dispatcher, scheduler, worker, browser, resident process, timed automation, or app-server wiring.
- No forecast scoring, action guidance, market ranking, numeric prediction metric, stance selection, or trade action guidance.
- This inventory is not execution approval and is not runtime input.
