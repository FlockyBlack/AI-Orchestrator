# PMBOT Supervised Live 001 Read Only Live Data Contract Local Only

Task: `PMBOT-SUPERVISED-LIVE-001-READ-ONLY-LIVE-DATA-CONTRACT-LOCAL-ONLY`

Contract: `pmbot_supervised_live_read_only_live_data_contract.v1`
Run mode: `local_static_read_only_live_data_contract`
Operator review: `pending_operator_review`

## Purpose

This document defines the local read-only live data handling contract for a supervised readiness review. It is a deterministic operator review artifact built from local files, local fixtures, and static samples only.

The contract is descriptive only. It is not execution approval, runtime input, market analysis, forecast scoring, action guidance, or selection advice.

## Static Fixture

The local fixture is:

`pm_bot/tests/fixtures/readiness/pmbot_read_only_live_data_contract.valid.json`

The fixture records the contract fields, static sample record shape, read-only handling rules, source contract references, required validation commands, summary counts, and closed safety boundaries. It does not fetch live data, call endpoints, approve execution, or produce market instructions.

## Source Basis

Reviewed local PMBOT artifacts:

- `pm_bot/readiness/PMBOT_ROADMAP_001_REAL_WALLET_READINESS_BLOCKER_MATRIX.md`
- `pm_bot/readiness/PMBOT_ROADMAP_002_PMBOT_LOCAL_TO_SUPERVISED_LIVE_GAP_MATRIX.md`
- `docs/PMBOT_DASHBOARD_002_QUEUE_AND_PAPERLIVE_STATUS_SURFACE.md`
- `docs/PMBOT_SOURCE_LEDGER_001_UNIFIED_SOURCE_QUALITY_LEDGER_LOCAL_ONLY.md`
- `docs/PMBOT_PAPERLIVE_DECISION_001_SIMULATED_DECISION_PACKET_SCHEMA_NO_RECOMMENDATIONS.md`
- `docs/PMBOT_SAFETY_003_FORBIDDEN_ACTION_SCAN_LOCAL_ONLY.md`
- `tests/test_codex_queue_pmbot_templates.py`

These sources keep PMBOT readiness work local-only, static, paper-mode, and pending operator review.

## Contract Fields

Each local read-only live data sample record keeps these fields in a fixed contract:

- `record_id`
- `source_label`
- `source_class`
- `capture_mode`
- `captured_at_utc`
- `local_snapshot_reference`
- `read_only_use`
- `source_freshness_label`
- `operator_review_status`
- `excluded_operations`
- `notes`

The static sample may identify the presence of a local snapshot and its review state. It may not include prices, probabilities, ranks, sides, stake sizing, market instructions, or execution fields.

## Operator Review Checklist

Operators review:

- all local references are inside the allowed documentation, readiness, and test paths
- static samples are bounded and copied from local fixtures only
- source freshness labels are descriptive and do not claim current external state
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
- This contract is not execution approval and is not runtime input.
