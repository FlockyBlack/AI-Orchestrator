# PMBOT Rehearsal 011 Rehearsal Readiness Dashboard Card Local Only

Task: `PMBOT-REHEARSAL-011-REHEARSAL-READINESS-DASHBOARD-CARD-LOCAL-ONLY`

Card: `pmbot-rehearsal-readiness-dashboard-card-001`
Contract: `pmbot_rehearsal_readiness_dashboard_card.v1`
Run mode: `local_static_rehearsal_readiness_dashboard_card`
Operator review: `pending_operator_review`

## Purpose

This document registers a deterministic local PMBOT rehearsal readiness dashboard card for operator review. The card uses only static local documents, local fixtures, local dashboard samples, and local tests.

The card is descriptive and review-oriented. It does not refresh data, call external services, approve execution, mutate runtime state, or produce market recommendations, probability scores, EV, edge, confidence, action guidance, or side selection.

## Local Artifacts

- Request fixture: `pm_bot/tests/fixtures/rehearsal/pmbot_rehearsal_readiness_dashboard_card_request.valid.json`
- Static card sample: `pm_bot/dashboard/samples/pmbot_rehearsal_readiness_dashboard_card.fixture.json`
- Static operator report sample: `pm_bot/dashboard/samples/pmbot_rehearsal_readiness_dashboard_card.fixture.md`
- Builder: `pm_bot/dashboard/local_rehearsal_readiness_dashboard_card.py`
- Contract test: `pm_bot/tests/test_rehearsal_readiness_dashboard_card.py`

## Dashboard Card Rows

- Card identity rows for the document, builder, contract test, and queue template test.
- Prior rehearsal rows for the scenario contract, market packet schema, source evidence bundle, operator record, stop condition matrix, staleness case set, contradiction case set, evidence retention ledger, validation replay packet, and CI-safe validation runner.
- Dashboard context row for the existing local supervised-live readiness dashboard sample.
- Closed safety rows for local material, endpoint and service boundaries, sensitive path exclusion, and execution wiring.
- Validation command records for the required local acceptance commands.

## CLI

```powershell
python -m pm_bot.dashboard.local_rehearsal_readiness_dashboard_card `
  --request pm_bot/tests/fixtures/rehearsal/pmbot_rehearsal_readiness_dashboard_card_request.valid.json `
  --output-card pm_bot/dashboard/samples/pmbot_rehearsal_readiness_dashboard_card.fixture.json `
  --output-report pm_bot/dashboard/samples/pmbot_rehearsal_readiness_dashboard_card.fixture.md
```

## Operator Review Boundary

Operators review whether each card row points to an expected local document, fixture, module, sample, or test and whether displayed counts match the named static artifacts. Every row remains `pending_operator_review` until a human updates a later artifact.

This card is not execution approval and is not runtime input.

## Safety

- Local files, local fixtures, and static samples only.
- No network calls.
- No OpenRouter calls.
- No Polymarket API calls.
- No authenticated endpoints.
- No credential, wallet, private-key, seed, signing, order, trading endpoint, payment, or transaction path access.
- No runtime, dispatcher, scheduler, worker, browser, resident process, timed automation, or run_codex wiring.
- No validation command subprocess execution by this card.
- No market recommendation, forecast scoring, action guidance, or selection advice.
- No probability, EV, edge, or confidence scoring.
- No real-money actions.
