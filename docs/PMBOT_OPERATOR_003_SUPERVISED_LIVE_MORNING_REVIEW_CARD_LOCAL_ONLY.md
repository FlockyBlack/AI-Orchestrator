# PMBOT Supervised Live Morning Review Card

Task: `PMBOT-OPERATOR-003-SUPERVISED-LIVE-MORNING-REVIEW-CARD-LOCAL-ONLY`

Card: `pmbot_supervised_live_morning_review_card_fixture_001`
Contract: `pmbot_local_supervised_live_morning_review_card.v1`
Run mode: `local_static_supervised_live_morning_review_card`
Operator review: `pending_operator_review`

## Purpose

This card defines a deterministic local morning review surface for PMBOT supervised-live readiness operator review. It summarizes static local dashboard, readiness, safety, and validation references for a human operator before any later status change outside this card.

The card is descriptive only. It is not execution approval, runtime input, market analysis, forecast scoring, action guidance, or selection advice.

## Static Fixtures

The local request fixture is:

`pm_bot/tests/fixtures/operator/supervised_live_morning_review_card_request.valid.json`

The generated local card fixture is:

`pm_bot/dashboard/samples/local_supervised_live_morning_review_card.fixture.json`

The generated local Markdown fixture is:

`pm_bot/dashboard/samples/local_supervised_live_morning_review_card.fixture.md`

## Card Sections

The card contains four deterministic sections:

- Readiness dashboard reference.
- Readiness evidence references.
- Safety boundary references.
- Validation replay references.

All section, review, safety, and validation rows remain in `pending_operator_review`.

## CLI

```powershell
python -m pm_bot.dashboard.local_supervised_live_morning_review_card `
  --request pm_bot/tests/fixtures/operator/supervised_live_morning_review_card_request.valid.json `
  --output-card pm_bot/dashboard/samples/local_supervised_live_morning_review_card.fixture.json `
  --output-report pm_bot/dashboard/samples/local_supervised_live_morning_review_card.fixture.md
```

## Operator Review Boundary

Operators review whether the listed local references match the local PMBOT fixtures, documentation, and tests. The card does not bridge results, mark tasks done, approve review, commit, push, schedule work, start a worker, access credentials, access wallets, call endpoints, refresh live data, or change runtime, dispatcher, browser, or app-server wiring.

This card is not execution approval and is not runtime input.

## Safety

- Local files and static fixtures only.
- No network calls.
- No LLM provider calls.
- No external service calls.
- No authenticated endpoint use.
- No credential, wallet, private-key, seed, signing, order, trading endpoint, payment, or transaction path access.
- No runtime, dispatcher, scheduler, worker, browser, resident process, timed automation, or app-server wiring.
- No forecast scoring, action guidance, market ranking, numeric prediction metric, stance selection, or trade action guidance.
- This card is not execution approval and is not runtime input.
