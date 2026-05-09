# PMBOT Crypto Live 001 Read Only Crypto Data Contract Local Only

Task: `PMBOT-CRYPTO-LIVE-001-READ-ONLY-CRYPTO-DATA-CONTRACT-LOCAL-ONLY`

Contract: `pmbot_crypto_live_read_only_crypto_data_contract.v1`
Run mode: `local_static_read_only_crypto_data_contract`
Operator review: `pending_operator_review`

## Purpose

This document defines the local read-only crypto data handling contract for supervised crypto pilot readiness review. It is a deterministic operator review artifact built from local files, local fixtures, and static samples only.

The contract is descriptive only. It is not execution approval, runtime input, market analysis, forecast scoring, action guidance, or selection advice.

## Static Fixture

The local fixture is:

`pm_bot/tests/fixtures/crypto_live/pmbot_read_only_crypto_data_contract.valid.json`

The fixture records the contract fields, static crypto sample handling rules, local source artifact references, required validation commands, summary counts, and closed safety boundaries. It does not fetch crypto data, call endpoints, approve execution, compare thresholds, or produce market instructions.

## Source Basis

Reviewed local PMBOT artifacts:

- `docs/PMBOT_CRYPTO_PILOT_001_CRYPTO_MARKET_CLASS_CAPTURE_TEMPLATE_LOCAL_ONLY.md`
- `docs/PMBOT_CRYPTO_PILOT_002_CRYPTO_OPERATOR_REVIEW_PROTOCOL_LOCAL_ONLY.md`
- `docs/PMBOT_CRYPTO_PILOT_003_CRYPTO_PAPERLIVE_OBSERVATION_LEDGER_LOCAL_ONLY.md`
- `docs/PMBOT_CRYPTO_PILOT_004_CRYPTO_SOURCE_QUALITY_CAPTURE_SURFACE_LOCAL_ONLY.md`
- `docs/PMBOT_SUPERVISED_LIVE_001_READ_ONLY_LIVE_DATA_CONTRACT_LOCAL_ONLY.md`
- `pm_bot/readiness/PMBOT_ROADMAP_002_PMBOT_LOCAL_TO_SUPERVISED_LIVE_GAP_MATRIX.md`
- `pm_bot/readiness/PMBOT_ROADMAP_004_REAL_WALLET_GATED_MILESTONE_SEPARATION_LOCAL_ONLY.md`
- `tests/test_codex_queue_pmbot_templates.py`

These sources keep PMBOT crypto readiness work local-only, static, paper-mode, and pending operator review.

## Contract Fields

Each local read-only crypto data sample record keeps these fields in a fixed contract:

- `record_id`
- `source_label`
- `source_class`
- `source_access_mode`
- `captured_at_utc`
- `asset_symbol`
- `asset_name`
- `metric_type`
- `measurement_source_label`
- `reported_at_utc`
- `reported_reference_unit`
- `local_snapshot_reference`
- `included_static_fields`
- `allowed_handling`
- `freshness_label`
- `operator_review_status`
- `excluded_operations`
- `notes`

The contract may identify crypto fixture presence, copied labels, copied timestamps, unit labels, and field names. It keeps numeric crypto source values in their referenced local fixture and does not copy them into this readiness contract.

## Operator Review Checklist

Operators review:

- all local references are inside the allowed documentation, readiness, and test paths
- static crypto samples are bounded and copied from local fixtures only
- field inventories name local crypto fixture fields without copying source values into this contract
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
- This contract is not execution approval and is not runtime input.
