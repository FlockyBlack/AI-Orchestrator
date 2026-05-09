# PMBOT Night Batch Postrun Audit Summary

Task: `PMBOT-SAFETY-002-NIGHT-BATCH-POSTRUN-AUDIT-SUMMARY-LOCAL-ONLY`

Summary: `pmbot-night-batch-postrun-audit-summary`
Contract: `pmbot_night_batch_postrun_audit_summary.v1`
Run mode: `local_static_night_batch_postrun_audit_summary`
Operator review: `pending_operator_review`

## Purpose

This summary defines a deterministic local postrun audit surface for PMBOT night batch records. It is a static operator review artifact only, using local docs, fixtures, and tests.

## Static Fixture

The local fixture is:

`pm_bot/tests/fixtures/safety/night_batch_postrun_audit_summary.valid.json`

The fixture records night batch audit rows, local references, observed states, summary counts, validation commands, and closed safety boundaries. It is not runtime input and does not approve execution.

## Audit Records

The fixture defines six deterministic audit records:

- Night batch task inventory.
- Batch runner guardrail record.
- Postprocess summary contract.
- Result packet shape.
- Safety gate carryover.
- Validation command record.

Each audit record stays in `pending_operator_review` and requires a later human review record before any status can change.

## Operator Review Boundary

Operators review whether the listed local references and observed states match the postrun batch records. The summary does not bridge results, mark tasks done, approve review, commit, push, schedule work, start a worker, access credentials, access wallets, call endpoints, or change runtime, dispatcher, browser, or app-server wiring.

## Safety

- Local files and static fixtures only.
- No network calls.
- No LLM provider calls.
- No external market API calls.
- No authenticated endpoint use.
- No credential, wallet, signing material, payment, or transaction endpoint use.
- No runtime, dispatcher, scheduler, worker, browser, or app-server wiring.
- No forecast scoring, action guidance, or selection advice.
- This summary is not execution approval and is not runtime input.
