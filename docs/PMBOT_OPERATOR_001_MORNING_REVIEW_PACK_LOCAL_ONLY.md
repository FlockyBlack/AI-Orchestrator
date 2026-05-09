# PMBOT Morning Review Pack

Task: `PMBOT-OPERATOR-001-MORNING-REVIEW-PACK-LOCAL-ONLY`

Pack: `pmbot_morning_review_pack_fixture_001`
Contract: `pmbot_local_morning_review_pack.v1`
Run mode: `local_static_morning_review_pack`
Operator review: `pending_operator_review`

## Purpose

This pack defines a deterministic local morning review surface for PMBOT operator use. It groups static queue, dashboard, safety, and validation records so a human operator can inspect the local artifacts before any later work.

## Static Fixtures

The local request fixture is:

`pm_bot/tests/fixtures/operator/morning_review_pack_request.valid.json`

The generated local pack fixture is:

`pm_bot/dashboard/samples/local_morning_review_pack.fixture.json`

The generated local report fixture is:

`pm_bot/dashboard/samples/local_morning_review_pack.fixture.md`

## Pack Sections

The pack contains four deterministic sections:

- Queue review records for the PMBOT morning review task, night batch postrun audit summary, and queue paperlive status surface.
- Dashboard review records for local operator, queue paperlive, source quality, and paper accounting dashboard summaries.
- Safety review records for autonomy gate, night batch postrun audit, and forbidden action scan boundaries.
- Validation review records for the required local compile and pytest commands.

All records remain in `pending_operator_review`.

## Operator Review Boundary

Operators review whether the listed local references match the local PMBOT fixtures and documentation. The pack does not bridge results, mark tasks done, approve review, commit, push, schedule work, start a worker, access credentials, access wallets, call endpoints, or change runtime, dispatcher, browser, or app-server wiring.

## Safety

- Local files and static fixtures only.
- No network calls.
- No LLM provider calls.
- No external service calls.
- No authenticated endpoint use.
- No credential, wallet, signing material, payment, or transaction endpoint use.
- No runtime, dispatcher, scheduler, worker, browser, or app-server wiring.
- No forecast scoring, action guidance, or selection advice.
- This pack is not execution approval and is not runtime input.
