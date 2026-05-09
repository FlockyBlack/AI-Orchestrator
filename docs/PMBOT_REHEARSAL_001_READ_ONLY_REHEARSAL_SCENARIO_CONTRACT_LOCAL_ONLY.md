# PMBOT Rehearsal 001 Read Only Rehearsal Scenario Contract Local Only

Task: `PMBOT-REHEARSAL-001-READ-ONLY-REHEARSAL-SCENARIO-CONTRACT-LOCAL-ONLY`

Contract: `pmbot_read_only_rehearsal_scenario_contract.v1`
Run mode: `local_static_read_only_rehearsal_scenario_contract`
Operator review: `pending_operator_review`

## Purpose

This document defines the local scenario contract for the first PMBOT read-only supervised-live rehearsal. It is a deterministic operator review artifact built from local files, local fixtures, and static samples only.

The contract is descriptive only. It is not execution approval, runtime input, market analysis, forecast scoring, action guidance, or selection advice.

## Static Fixture

The local fixture is:

`pm_bot/tests/fixtures/rehearsal/pmbot_read_only_rehearsal_scenario_contract.valid.json`

The fixture records fixed scenario fields, one static rehearsal scenario record, local source artifacts, operator review checks, validation commands, summary counts, and closed safety boundaries. It does not fetch data, call endpoints, approve execution, start processes, alter runtime wiring, or produce market instructions.

## Source Basis

Reviewed local PMBOT artifacts:

- `docs/PMBOT_SUPERVISED_LIVE_001_READ_ONLY_LIVE_DATA_CONTRACT_LOCAL_ONLY.md`
- `docs/PMBOT_SUPERVISED_LIVE_002_LIVE_DATA_SOURCE_INVENTORY_LOCAL_ONLY.md`
- `docs/PMBOT_SUPERVISED_LIVE_003_OPERATOR_APPROVAL_GATE_RECORD_LOCAL_ONLY.md`
- `docs/PMBOT_SUPERVISED_LIVE_004_SUPERVISED_LIVE_STOP_CONDITION_SPEC_LOCAL_ONLY.md`
- `docs/PMBOT_SUPERVISED_LIVE_005_LIVE_READINESS_EVIDENCE_BUNDLE_LOCAL_ONLY.md`
- `pm_bot/readiness/PMBOT_ROADMAP_002_PMBOT_LOCAL_TO_SUPERVISED_LIVE_GAP_MATRIX.md`
- `docs/PMBOT_SAFETY_003_FORBIDDEN_ACTION_SCAN_LOCAL_ONLY.md`
- `docs/PMBOT_SAFETY_005_FORBIDDEN_LANGUAGE_REGRESSION_SUITE_LOCAL_ONLY.md`
- `tests/test_codex_queue_pmbot_templates.py`

These sources keep the first rehearsal scenario local-only, static, descriptive, paper-mode, and pending operator review.

## Scenario Contract

The fixture defines one deterministic scenario record for the first read-only supervised-live rehearsal. The record names:

- local fixture input mode
- static source snapshot references
- operator gate reference
- stop-condition reference
- validation reference
- operator review steps
- excluded operations

Every scenario record remains `pending_operator_review`. It may identify local artifacts, fixture states, and review steps. It may not include prices, probabilities, ranks, sides, stake sizing, market instructions, or execution fields.

## Operator Review Boundary

Operators review whether the listed local references, scenario scope, source snapshots, gate record, stop-condition record, closed boundaries, and validation commands are internally consistent. This contract does not approve a live run, choose a market, resolve an outcome, change review status, open external services, access credentials, access wallets, call endpoints, or change runtime, dispatcher, scheduler, worker, browser, resident process, or run_codex wiring.

## Safety

- Local files, local fixtures, and static samples only.
- No network calls.
- No OpenRouter calls.
- No Polymarket API calls.
- No authenticated endpoints.
- No credential, wallet, private-key, seed, signing, order, trading endpoint, payment, or transaction path access.
- No runtime, dispatcher, scheduler, worker, browser, resident process, timed automation, or run_codex wiring.
- No market recommendation, forecast scoring, action guidance, or selection advice.
- No probability, EV, edge, or confidence scoring.
- No real-money actions.
- This contract is not execution approval and is not runtime input.

## Validation

Required local validation commands:

- `python -m compileall pm_bot tests`
- `pytest pm_bot/tests tests/test_codex_queue_pmbot_templates.py`
