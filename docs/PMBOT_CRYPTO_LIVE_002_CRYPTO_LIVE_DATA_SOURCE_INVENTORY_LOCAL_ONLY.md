# PMBOT Crypto Live 002 Crypto Live Data Source Inventory Local Only

Task: `PMBOT-CRYPTO-LIVE-002-CRYPTO-LIVE-DATA-SOURCE-INVENTORY-LOCAL-ONLY`

Inventory: `pmbot-crypto-live-data-source-inventory-001`
Contract: `pmbot_crypto_live_data_source_inventory.v1`
Run mode: `local_static_crypto_live_data_source_inventory`
Operator review: `pending_operator_review`

## Purpose

This document defines the local crypto live data source inventory for supervised crypto pilot readiness review. It is a deterministic operator review artifact built from local files, local fixtures, and static samples only.

The inventory is descriptive only. It is not execution approval, runtime input, market analysis, forecast scoring, action guidance, or selection advice.

## Static Fixture

The local fixture is:

`pm_bot/tests/fixtures/crypto_live/pmbot_crypto_live_data_source_inventory.valid.json`

The fixture records fixed crypto source record fields, static local source records, source contract references, operator review checks, required validation commands, summary counts, and closed safety boundaries. It does not fetch crypto data, call endpoints, approve execution, compare thresholds, rank markets, or produce market instructions.

## Source Basis

Reviewed local PMBOT artifacts:

- `docs/PMBOT_CRYPTO_LIVE_001_READ_ONLY_CRYPTO_DATA_CONTRACT_LOCAL_ONLY.md`
- `docs/PMBOT_SUPERVISED_LIVE_002_LIVE_DATA_SOURCE_INVENTORY_LOCAL_ONLY.md`
- `docs/PMBOT_CRYPTO_PILOT_001_CRYPTO_MARKET_CLASS_CAPTURE_TEMPLATE_LOCAL_ONLY.md`
- `docs/PMBOT_CRYPTO_PILOT_002_CRYPTO_OPERATOR_REVIEW_PROTOCOL_LOCAL_ONLY.md`
- `docs/PMBOT_CRYPTO_PILOT_003_CRYPTO_PAPERLIVE_OBSERVATION_LEDGER_LOCAL_ONLY.md`
- `docs/PMBOT_CRYPTO_PILOT_004_CRYPTO_SOURCE_QUALITY_CAPTURE_SURFACE_LOCAL_ONLY.md`
- `pm_bot/tests/fixtures/crypto_live/pmbot_read_only_crypto_data_contract.valid.json`
- `pm_bot/tests/fixtures/crypto_market_class_capture/crypto_market_class_capture_template.valid.json`
- `pm_bot/tests/fixtures/crypto_operator_review_protocol/crypto_operator_review_protocol.valid.json`
- `pm_bot/tests/fixtures/crypto_paperlive_observation_ledger/crypto_paperlive_observation_ledger.valid.json`
- `pm_bot/tests/fixtures/crypto_paperlive_observation_ledger/static_crypto_reference_snapshot.valid.json`
- `pm_bot/source_quality/samples/crypto_source_quality_capture_surface.fixture.json`
- `tests/test_codex_queue_pmbot_templates.py`

These sources keep PMBOT crypto readiness work local-only, static, paper-mode, and pending operator review.

## Inventory Fields

Each local crypto live data source record keeps these fields in a fixed contract:

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

The inventory may identify local fixture presence, source labels, static timestamps, and field names. It may not include crypto prices, thresholds, probabilities, ranks, sides, stake sizing, market instructions, or execution fields.

## Operator Review Checklist

Operators review:

- all local references are inside the allowed documentation, readiness, source quality, and test paths
- static crypto records are bounded and copied from local fixtures only
- field inventories name local crypto fixture fields without copying crypto numeric values into this inventory
- freshness labels are descriptive and do not claim current external state
- sensitive paths, credentials, wallets, signing material, and authenticated endpoints remain excluded
- runtime, dispatcher, scheduler, worker, browser, resident process, and app-server boundaries remain closed
- output remains descriptive and contains no forecast scoring, action guidance, market ranking, numeric prediction metric, threshold comparison output, or selection advice
- validation output is captured by a human before any later readiness status change

## Safety

- Local files and static fixtures only.
- No network calls.
- No LLM provider calls.
- No external market API calls.
- No authenticated endpoint use.
- No credential, wallet, private-key, seed, signing, order, trading endpoint, payment, or transaction path access.
- No runtime, dispatcher, scheduler, worker, browser, resident process, timed automation, or app-server wiring.
- No forecast scoring, action guidance, market ranking, numeric prediction metric, stance selection, threshold comparison output, or trade action guidance.
- This inventory is not execution approval and is not runtime input.
