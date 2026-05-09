# PMBOT Autonomy Gate Checklist

Task: `PMBOT-SAFETY-001-AUTONOMY-GATE-CHECKLIST-LOCAL-ONLY`

Checklist: `pmbot-autonomy-gate-checklist`
Contract: `pmbot_autonomy_gate_checklist.v1`
Run mode: `local_static_operator_gate_checklist`
Operator review: `pending_operator_review`

## Purpose

This checklist defines a deterministic local gate for PMBOT autonomy review. It is a static operator review artifact only, using local docs, fixtures, and tests.

## Static Fixture

The local fixture is:

`pm_bot/tests/fixtures/safety/autonomy_gate_checklist.valid.json`

The fixture records gate entries, local references, expected states, summary counts, and closed safety boundaries. It is not runtime input and does not approve execution.

## Checklist Entries

The fixture defines seven deterministic inspection entries:

- Scope boundary check.
- Forbidden path check.
- Local reference check.
- Endpoint isolation check.
- Descriptive output check.
- Validation command check.
- Human review check.

Each entry stays in `pending_operator_review` and requires a later human review record before any status can change.

## Operator Review Boundary

Operators review whether the listed local references, states, and safety boundaries match the task handoff. The checklist does not choose a PMBOT path, resolve a market, or authorize a worker, scheduler, wallet, transaction endpoint, runtime, dispatcher, browser, or external service.

## Safety

- Local files and static fixtures only.
- No network calls.
- No LLM provider calls.
- No external market API calls.
- No authenticated endpoint use.
- No credential, wallet, signing material, payment, or transaction endpoint use.
- No runtime, dispatcher, scheduler, worker, browser, or app-server wiring.
- No forecast scoring, action guidance, market ranking, or selection advice.
- This checklist is not execution approval and is not runtime input.
