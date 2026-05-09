# PMBOT Rehearsal 008 Rehearsal Evidence Retention Ledger Local Only

Task: `PMBOT-REHEARSAL-008-REHEARSAL-EVIDENCE-RETENTION-LEDGER-LOCAL-ONLY`

Ledger: `pmbot-rehearsal-evidence-retention-ledger-001`
Contract: `pmbot_rehearsal_evidence_retention_ledger.v1`
Run mode: `local_static_rehearsal_evidence_retention_ledger`
Operator review: `pending_operator_review`

## Purpose

This document registers the deterministic local PMBOT rehearsal evidence retention ledger for operator review records. It is built from local files, local fixtures, and static samples only.

The ledger links prior rehearsal docs, fixtures, tests, safety references, and validation references into fixed retention rows. It records local references, retention classes, retained-for-review state, required prior state, operator review checks, and closed safety boundaries only. It does not delete files, start cleanup, call services, approve execution, produce market recommendations, produce forecast scoring, provide action guidance, or provide selection advice.

## Static Fixture

The local fixture is:

`pm_bot/tests/fixtures/rehearsal/pmbot_rehearsal_evidence_retention_ledger.valid.json`

The fixture records eight deterministic retention rows covering the prior rehearsal review records and local validation/safety review evidence. Every row remains pending operator review and retained for local operator review. The fixture does not start a scheduler, worker, background process, browser automation, cleanup process, network call, endpoint call, or state mutation.

## Source Basis

Reviewed local PMBOT artifacts:

- `docs/PMBOT_REHEARSAL_001_READ_ONLY_REHEARSAL_SCENARIO_CONTRACT_LOCAL_ONLY.md`
- `pm_bot/tests/fixtures/rehearsal/pmbot_read_only_rehearsal_scenario_contract.valid.json`
- `docs/PMBOT_REHEARSAL_002_REHEARSAL_MARKET_PACKET_SCHEMA_LOCAL_ONLY.md`
- `pm_bot/tests/fixtures/rehearsal/pmbot_rehearsal_market_packet_schema.valid.json`
- `docs/PMBOT_REHEARSAL_003_REHEARSAL_SOURCE_EVIDENCE_BUNDLE_LOCAL_ONLY.md`
- `pm_bot/tests/fixtures/rehearsal/pmbot_rehearsal_source_evidence_bundle.valid.json`
- `docs/PMBOT_REHEARSAL_004_REHEARSAL_OPERATOR_APPROVAL_RECORD_LOCAL_ONLY.md`
- `pm_bot/tests/fixtures/rehearsal/pmbot_rehearsal_operator_approval_record.valid.json`
- `docs/PMBOT_REHEARSAL_005_REHEARSAL_STOP_CONDITION_TRIGGER_MATRIX_LOCAL_ONLY.md`
- `pm_bot/tests/fixtures/rehearsal/pmbot_rehearsal_stop_condition_trigger_matrix.valid.json`
- `docs/PMBOT_REHEARSAL_006_REHEARSAL_STALENESS_CASE_SET_LOCAL_ONLY.md`
- `pm_bot/tests/fixtures/rehearsal/pmbot_rehearsal_staleness_case_set.valid.json`
- `docs/PMBOT_REHEARSAL_007_REHEARSAL_CONTRADICTION_CASE_SET_LOCAL_ONLY.md`
- `pm_bot/tests/fixtures/rehearsal/pmbot_rehearsal_contradiction_case_set.valid.json`
- `docs/PMBOT_SAFETY_003_FORBIDDEN_ACTION_SCAN_LOCAL_ONLY.md`
- `docs/PMBOT_SAFETY_005_FORBIDDEN_LANGUAGE_REGRESSION_SUITE_LOCAL_ONLY.md`
- `tests/test_codex_queue_pmbot_templates.py`

These inputs keep the rehearsal evidence retention ledger local-only, static, descriptive, paper-mode, and pending operator review.

## Ledger Content

The fixture defines eight deterministic retention rows:

- read-only rehearsal scenario contract review record
- rehearsal market packet schema review record
- rehearsal source evidence bundle review record
- rehearsal operator approval record review record
- rehearsal stop condition trigger matrix review record
- rehearsal staleness case set review record
- rehearsal contradiction case set review record
- local validation and safety review record

Every retention row records only local references, required prior state, retention class, retention reason, retained-for-review state, and operator review status. The ledger does not mark any file for deletion, publication, external transfer, execution, trading, or live use.

## Operator Review Boundary

Operators review whether the listed local references, retained-for-review states, prior review states, review checks, and closed safety boundaries are internally consistent. This ledger does not approve a live run, choose a market, resolve an outcome, change review status, open external services, access credentials, access wallets, call endpoints, delete evidence, or change runtime, dispatcher, scheduler, worker, browser, resident process, or run_codex wiring.

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
- No destructive cleanup or automated retention process.
- This ledger is not execution approval and is not runtime input.

## Validation

Required local validation commands:

- `python -m compileall pm_bot tests`
- `pytest pm_bot/tests tests/test_codex_queue_pmbot_templates.py`
