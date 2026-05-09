# PMBOT Rehearsal 004 Rehearsal Operator Approval Record Local Only

Task: `PMBOT-REHEARSAL-004-REHEARSAL-OPERATOR-APPROVAL-RECORD-LOCAL-ONLY`

Record: `pmbot-rehearsal-operator-approval-record-001`
Contract: `pmbot_rehearsal_operator_approval_record.v1`
Run mode: `local_static_rehearsal_operator_approval_record`
Operator review: `pending_operator_review`

## Purpose

This document registers the deterministic local PMBOT rehearsal operator approval record for read-only rehearsal control. It is built from local files, local fixtures, and static samples only.

The record is descriptive only. It is not execution approval, runtime input, market analysis, forecast scoring, action guidance, or selection advice.

## Static Fixture

The local fixture is:

`pm_bot/tests/fixtures/rehearsal/pmbot_rehearsal_operator_approval_record.valid.json`

The fixture records fixed approval rows, prior rehearsal artifact references, local review checks, required validation commands, summary counts, and closed safety boundaries. It does not approve a rehearsal transition, call endpoints, start processes, change status rows, alter runtime wiring, or produce market instructions.

## Source Basis

Reviewed local PMBOT artifacts:

- `docs/PMBOT_REHEARSAL_001_READ_ONLY_REHEARSAL_SCENARIO_CONTRACT_LOCAL_ONLY.md`
- `pm_bot/tests/fixtures/rehearsal/pmbot_read_only_rehearsal_scenario_contract.valid.json`
- `docs/PMBOT_REHEARSAL_002_REHEARSAL_MARKET_PACKET_SCHEMA_LOCAL_ONLY.md`
- `pm_bot/tests/fixtures/rehearsal/pmbot_rehearsal_market_packet_schema.valid.json`
- `docs/PMBOT_REHEARSAL_003_REHEARSAL_SOURCE_EVIDENCE_BUNDLE_LOCAL_ONLY.md`
- `pm_bot/tests/fixtures/rehearsal/pmbot_rehearsal_source_evidence_bundle.valid.json`
- `docs/PMBOT_SAFETY_003_FORBIDDEN_ACTION_SCAN_LOCAL_ONLY.md`
- `docs/PMBOT_SAFETY_005_FORBIDDEN_LANGUAGE_REGRESSION_SUITE_LOCAL_ONLY.md`
- `tests/test_codex_queue_pmbot_templates.py`

These inputs keep the rehearsal operator approval record local-only, static, descriptive, paper-mode, read-only, and pending operator review.

## Approval Records

The fixture defines six deterministic approval records:

- Read-only rehearsal scenario contract review.
- Rehearsal market packet schema review.
- Rehearsal source evidence bundle review.
- Local validation review.
- Safety boundary review.
- Human approval record completion.

Every approval record remains `pending_operator_review`, keeps `approval_state` as `not_approved`, and keeps `transition_state` as `blocked_until_record_complete`.

## Operator Review Boundary

Operators review whether the listed local references, prior states, evidence requirements, and closed boundaries match the read-only rehearsal handoff. This record does not approve a live run, choose a market, resolve an outcome, change review status, open external services, access credentials, access wallets, call endpoints, or change runtime, dispatcher, scheduler, worker, browser, resident process, or run_codex wiring.

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
- This record is not execution approval and is not runtime input.

## Validation

Required local validation commands:

- `python -m compileall pm_bot tests`
- `pytest pm_bot/tests tests/test_codex_queue_pmbot_templates.py`
