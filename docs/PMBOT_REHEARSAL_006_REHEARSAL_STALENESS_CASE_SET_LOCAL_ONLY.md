# PMBOT Rehearsal 006 Rehearsal Staleness Case Set Local Only

Task: `PMBOT-REHEARSAL-006-REHEARSAL-STALENESS-CASE-SET-LOCAL-ONLY`

Case set: `pmbot-rehearsal-staleness-case-set-001`
Contract: `pmbot_rehearsal_staleness_case_set.v1`
Run mode: `local_static_rehearsal_staleness_case_set`
Operator review: `pending_operator_review`

## Purpose

This document registers the deterministic local PMBOT rehearsal staleness case set for operator source review. It is built from local files, local fixtures, and static samples only.

The case set links the rehearsal source evidence bundle to the existing local source staleness check spec. It records fixed staleness cases, local references, review classes, operator review checks, and closed safety boundaries only. It does not refresh source data, call services, approve execution, produce market recommendations, produce forecast scoring, provide action guidance, or provide selection advice.

## Static Fixture

The local fixture is:

`pm_bot/tests/fixtures/rehearsal/pmbot_rehearsal_staleness_case_set.valid.json`

The fixture records fixed within-window, at-limit, outside-window, missing-timestamp, and timestamp-not-required cases for source review. Every case remains pending operator review and uses the static reference timestamp from the local source staleness check spec fixture.

## Source Basis

Reviewed local PMBOT artifacts:

- `docs/PMBOT_REHEARSAL_003_REHEARSAL_SOURCE_EVIDENCE_BUNDLE_LOCAL_ONLY.md`
- `pm_bot/tests/fixtures/rehearsal/pmbot_rehearsal_source_evidence_bundle.valid.json`
- `docs/PMBOT_SOURCE_EVIDENCE_003_SOURCE_STALENESS_CHECK_SPEC_LOCAL_ONLY.md`
- `pm_bot/source_quality/samples/source_staleness_check_spec.fixture.json`
- `pm_bot/source_quality/samples/source_staleness_check_spec.fixture.md`
- `tests/test_codex_queue_pmbot_templates.py`

These inputs keep the rehearsal staleness case set local-only, static, descriptive, paper-mode, and pending operator review.

## Case Set Content

The fixture defines six deterministic source review cases:

- within-window station observation from the local staleness spec
- within-window crypto reference sample from the local staleness spec
- at-limit static boundary case
- outside-window static boundary case
- missing required timestamp static boundary case
- timestamp-not-required local source quality sample

Each case records the linked local source staleness check identifier, static age window values when present, timestamp presence fields, the expected review class, and pending operator review status. The case set does not choose sources, prefer sources, change source state, change PMBOT state, or trigger any process.

## Operator Review Boundary

Operators review whether the listed case rows, linked local source staleness check identifiers, timestamp fields, review classes, local references, review checks, and closed safety boundaries are internally consistent. This case set does not approve a live run, choose a market, resolve an outcome, change review status, open external services, access credentials, access wallets, call endpoints, or change runtime, dispatcher, scheduler, worker, browser, resident process, or run_codex wiring.

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
