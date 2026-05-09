# PMBOT Rehearsal 012 Rehearsal Morning Operator Card Local Only

Task: `PMBOT-REHEARSAL-012-REHEARSAL-MORNING-OPERATOR-CARD-LOCAL-ONLY`

Card: `pmbot-rehearsal-morning-operator-card-001`
Contract: `pmbot_rehearsal_morning_operator_card.v1`
Run mode: `local_static_rehearsal_morning_operator_card`
Operator review: `pending_operator_review`

## Purpose

This document registers a deterministic local PMBOT rehearsal morning operator card for human review. The card uses only local documents, local fixtures, local dashboard samples, and local tests.

The card is descriptive and review-oriented. It does not refresh data, call external services, approve execution, mutate runtime state, or produce market recommendations, probability scores, EV, edge, confidence, action guidance, or side selection.

## Static Artifacts

- Static card sample: `pm_bot/dashboard/samples/pmbot_rehearsal_morning_operator_card.fixture.json`
- Static operator report sample: `pm_bot/dashboard/samples/pmbot_rehearsal_morning_operator_card.fixture.md`
- Contract test: `pm_bot/tests/test_rehearsal_morning_operator_card.py`

## Source Basis

Reviewed local PMBOT artifacts:

- `pm_bot/dashboard/samples/pmbot_rehearsal_readiness_dashboard_card.fixture.json`
- `pm_bot/dashboard/samples/pmbot_rehearsal_readiness_dashboard_card.fixture.md`
- `docs/PMBOT_REHEARSAL_001_READ_ONLY_REHEARSAL_SCENARIO_CONTRACT_LOCAL_ONLY.md`
- `docs/PMBOT_REHEARSAL_002_REHEARSAL_MARKET_PACKET_SCHEMA_LOCAL_ONLY.md`
- `docs/PMBOT_REHEARSAL_003_REHEARSAL_SOURCE_EVIDENCE_BUNDLE_LOCAL_ONLY.md`
- `docs/PMBOT_REHEARSAL_004_REHEARSAL_OPERATOR_APPROVAL_RECORD_LOCAL_ONLY.md`
- `docs/PMBOT_REHEARSAL_005_REHEARSAL_STOP_CONDITION_TRIGGER_MATRIX_LOCAL_ONLY.md`
- `docs/PMBOT_REHEARSAL_006_REHEARSAL_STALENESS_CASE_SET_LOCAL_ONLY.md`
- `docs/PMBOT_REHEARSAL_007_REHEARSAL_CONTRADICTION_CASE_SET_LOCAL_ONLY.md`
- `docs/PMBOT_REHEARSAL_008_REHEARSAL_EVIDENCE_RETENTION_LEDGER_LOCAL_ONLY.md`
- `docs/PMBOT_REHEARSAL_009_REHEARSAL_VALIDATION_REPLAY_PACKET_LOCAL_ONLY.md`
- `docs/PMBOT_REHEARSAL_010_REHEARSAL_CI_SAFE_VALIDATION_RUNNER_LOCAL_ONLY.md`
- `docs/PMBOT_REHEARSAL_011_REHEARSAL_READINESS_DASHBOARD_CARD_LOCAL_ONLY.md`
- `tests/test_codex_queue_pmbot_templates.py`

These inputs keep the morning operator card local-only, deterministic, descriptive, and pending operator review.

## Card Sections

The static card defines six sections:

- Rehearsal readiness snapshot.
- Rehearsal control snapshot.
- Rehearsal source snapshot.
- Rehearsal validation snapshot.
- Rehearsal operator review snapshot.
- Rehearsal safety snapshot.

Every section names one primary local reference, a fixed source artifact set, descriptive counts, and a `pending_operator_review` status.

## Operator Review Boundary

Operators review whether the listed local documents, fixtures, dashboard samples, validation commands, summary counts, and safety boundaries are present and internally consistent. This card does not approve a live run, choose a market, resolve an outcome, change review status, open external services, access credentials, access wallets, call endpoints, or change runtime, dispatcher, scheduler, worker, browser, or app-server wiring.

This card is not execution approval and is not runtime input.

## Safety

- Local files, local fixtures, and static samples only.
- No network calls.
- No OpenRouter calls.
- No Polymarket API calls.
- No LLM provider calls.
- No external service calls.
- No authenticated endpoint use.
- No credential, wallet, private-key, seed, signing, order, trading endpoint, payment, or transaction path access.
- No runtime, dispatcher, scheduler, worker, browser, resident process, timed automation, or app-server wiring.
- No validation command subprocess execution by this card.
- No market recommendation, forecast scoring, action guidance, or selection advice.
- No probability, EV, edge, or confidence scoring.
- No real-money actions.

## Validation

Required local validation commands:

- `python -m compileall pm_bot tests`
- `pytest pm_bot/tests tests/test_codex_queue_pmbot_templates.py`
