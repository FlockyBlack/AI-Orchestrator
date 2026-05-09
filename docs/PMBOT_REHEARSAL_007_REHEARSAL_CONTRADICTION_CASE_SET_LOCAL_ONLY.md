# PMBOT Rehearsal 007 Rehearsal Contradiction Case Set Local Only

Task: `PMBOT-REHEARSAL-007-REHEARSAL-CONTRADICTION-CASE-SET-LOCAL-ONLY`

Case set: `pmbot-rehearsal-contradiction-case-set-001`
Contract: `pmbot_rehearsal_contradiction_case_set.v1`
Run mode: `local_static_rehearsal_contradiction_case_set`
Operator review: `pending_operator_review`

## Purpose

This document registers the deterministic local PMBOT rehearsal contradiction case set for operator source review. It is built from local files, local fixtures, and static samples only.

The case set links prior rehearsal source evidence review to the existing local source contradiction ledger. It records fixed contradiction cases, local references, review classes, operator review checks, and closed safety boundaries only. It does not refresh source data, call services, approve execution, produce market recommendations, produce forecast scoring, provide action guidance, or provide selection advice.

## Static Fixture

The local fixture is:

`pm_bot/tests/fixtures/rehearsal/pmbot_rehearsal_contradiction_case_set.valid.json`

The fixture records fixed static value difference, subject key match, subject key difference, field unavailable, and matching static value cases for source review. Every case remains pending operator review and uses the existing local source contradiction ledger fixture as its evidence basis.

## Source Basis

Reviewed local PMBOT artifacts:

- `docs/PMBOT_REHEARSAL_003_REHEARSAL_SOURCE_EVIDENCE_BUNDLE_LOCAL_ONLY.md`
- `pm_bot/tests/fixtures/rehearsal/pmbot_rehearsal_source_evidence_bundle.valid.json`
- `docs/PMBOT_REHEARSAL_006_REHEARSAL_STALENESS_CASE_SET_LOCAL_ONLY.md`
- `pm_bot/tests/fixtures/rehearsal/pmbot_rehearsal_staleness_case_set.valid.json`
- `docs/PMBOT_SOURCE_EVIDENCE_003_SOURCE_STALENESS_CHECK_SPEC_LOCAL_ONLY.md`
- `pm_bot/source_quality/samples/source_staleness_check_spec.fixture.json`
- `docs/PMBOT_SOURCE_EVIDENCE_004_SOURCE_CONTRADICTION_LEDGER_LOCAL_ONLY.md`
- `pm_bot/source_quality/samples/source_contradiction_ledger.fixture.json`
- `pm_bot/source_quality/samples/source_contradiction_ledger.fixture.md`
- `tests/test_codex_queue_pmbot_templates.py`

These inputs keep the rehearsal contradiction case set local-only, static, descriptive, paper-mode, and pending operator review.

## Case Set Content

The fixture defines six deterministic source review cases:

- static value difference from the local source contradiction ledger
- station id subject key match control
- observation date subject key match control
- subject key difference static boundary case
- field unavailable static boundary case
- matching static value boundary case

Each case records the linked local source contradiction row identifier, left and right source identifiers, mapped fields, static values, expected review class, and pending operator review status. The case set does not choose sources, prefer sources, change source state, change PMBOT state, or trigger any process.

## Operator Review Boundary

Operators review whether the listed contradiction case rows, linked local source contradiction row identifiers, field mappings, value match flags, review classes, local references, review checks, and closed safety boundaries are internally consistent. This case set does not approve a live run, choose a market, resolve an outcome, change review status, open external services, access credentials, access wallets, call endpoints, or change runtime, dispatcher, scheduler, worker, browser, resident process, or run_codex wiring.

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
- This case set is not execution approval and is not runtime input.

## Validation

Required local validation commands:

- `python -m compileall pm_bot tests`
- `pytest pm_bot/tests tests/test_codex_queue_pmbot_templates.py`
