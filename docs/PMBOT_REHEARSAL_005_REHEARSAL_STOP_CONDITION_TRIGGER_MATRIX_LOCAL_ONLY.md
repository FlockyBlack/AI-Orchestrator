# PMBOT Rehearsal 005 Rehearsal Stop Condition Trigger Matrix Local Only

Task: `PMBOT-REHEARSAL-005-REHEARSAL-STOP-CONDITION-TRIGGER-MATRIX-LOCAL-ONLY`

Matrix: `pmbot-rehearsal-stop-condition-trigger-matrix-001`
Contract: `pmbot_rehearsal_stop_condition_trigger_matrix.v1`
Run mode: `local_static_rehearsal_stop_condition_trigger_matrix`
Operator review: `pending_operator_review`

## Purpose

This document registers the deterministic local PMBOT rehearsal stop condition trigger matrix for read-only rehearsal control. It is built from local files, local fixtures, and static samples only.

The matrix is descriptive only. It is not execution approval, runtime input, market analysis, forecast scoring, action guidance, or selection advice.

## Static Fixture

The local fixture is:

`pm_bot/tests/fixtures/rehearsal/pmbot_rehearsal_stop_condition_trigger_matrix.valid.json`

The fixture records fixed trigger rows, local evidence references, required operator record fields, prior rehearsal artifact references, review checks, validation commands, summary counts, and closed safety boundaries. It does not start, stop, restart, approve, automate, or mutate any process; it only names local review triggers for an operator record.

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
- `docs/PMBOT_SAFETY_003_FORBIDDEN_ACTION_SCAN_LOCAL_ONLY.md`
- `docs/PMBOT_SAFETY_005_FORBIDDEN_LANGUAGE_REGRESSION_SUITE_LOCAL_ONLY.md`
- `tests/test_codex_queue_pmbot_templates.py`

These inputs keep the rehearsal stop condition trigger matrix local-only, static, descriptive, paper-mode, read-only, and pending operator review.

## Trigger Matrix

The fixture defines eight deterministic trigger rows:

- Operator manual stop request.
- Rehearsal local artifact boundary breach.
- Rehearsal forbidden operation request detected.
- Rehearsal validation command failed.
- Rehearsal source evidence mismatch.
- Rehearsal operator approval record missing.
- Rehearsal review status changed without record.
- Rehearsal output boundary breach.

Every trigger row remains `pending_operator_review`, requires a manual operator record, names a local evidence reference, and maps to a blocked or stopped review state. The fixture does not evaluate live data, call services, or change any PMBOT state.

## Operator Review Boundary

Operators review whether the listed trigger rows, evidence references, blocked operations, and required record fields match the read-only rehearsal handoff. This matrix does not approve a live run, choose a market, resolve an outcome, change review status, open external services, access credentials, access wallets, call endpoints, or change runtime, dispatcher, scheduler, worker, browser, resident process, or run_codex wiring.

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
- This matrix is not execution approval and is not runtime input.

## Validation

Required local validation commands:

- `python -m compileall pm_bot tests`
- `pytest pm_bot/tests tests/test_codex_queue_pmbot_templates.py`
