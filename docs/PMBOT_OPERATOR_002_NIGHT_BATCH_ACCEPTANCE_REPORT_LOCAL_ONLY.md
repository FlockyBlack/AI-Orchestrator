# PMBOT Night Batch Acceptance Report

Task: `PMBOT-OPERATOR-002-NIGHT-BATCH-ACCEPTANCE-REPORT-LOCAL-ONLY`

Report: `pmbot_night_batch_acceptance_report_fixture_001`
Contract: `pmbot_local_night_batch_acceptance_report.v1`
Run mode: `local_static_night_batch_acceptance_report`
Operator review: `pending_operator_review`

## Purpose

This report defines a deterministic local acceptance review surface for PMBOT night batch operator use. It groups static task inventory, postrun audit, morning review pack, dashboard surface, result contract, and validation records so a human operator can inspect the local artifacts before any later status change outside this report.

## Static Fixtures

The local request fixture is:

`pm_bot/tests/fixtures/operator/night_batch_acceptance_report_request.valid.json`

The generated local report fixture is:

`pm_bot/dashboard/samples/local_night_batch_acceptance_report.fixture.json`

The generated local Markdown fixture is:

`pm_bot/dashboard/samples/local_night_batch_acceptance_report.fixture.md`

## Report Sections

The report contains five deterministic sections:

- Queue template task inventory.
- Operator morning review pack.
- Night batch postrun audit summary.
- Queue and paperlive dashboard surface.
- Validation command record.

All section records remain in `pending_operator_review`.

## Acceptance Review Records

The acceptance review rows cover five local checks:

- Night batch task inventory.
- Postrun audit visibility.
- Morning review pack visibility.
- Result packet contract visibility.
- Validation command visibility.

Each row remains in `pending_operator_review` and requires a later human review record before any task status can change.

## Operator Review Boundary

Operators review whether the listed local references match the local PMBOT fixtures, documentation, and tests. The report does not bridge results, mark tasks done, approve review, commit, push, schedule work, start a worker, access credentials, access wallets, call endpoints, or change runtime, dispatcher, browser, or app-server wiring.

## Safety

- Local files and static fixtures only.
- No network calls.
- No LLM provider calls.
- No external service calls.
- No authenticated endpoint use.
- No credential, wallet, signing material, payment, or transaction endpoint use.
- No runtime, dispatcher, scheduler, worker, browser, or app-server wiring.
- No forecast scoring, action guidance, or selection advice.
- This report is not execution approval and is not runtime input.
