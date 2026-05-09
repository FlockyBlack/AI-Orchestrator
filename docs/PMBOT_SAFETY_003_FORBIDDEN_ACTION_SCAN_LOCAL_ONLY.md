# PMBOT Forbidden Action Scan

Task: `PMBOT-SAFETY-003-FORBIDDEN-ACTION-SCAN-LOCAL-ONLY`

Scan: `pmbot-forbidden-action-scan`
Contract: `pmbot_forbidden_action_scan.v1`
Run mode: `local_static_forbidden_action_scan`
Operator review: `pending_operator_review`

## Purpose

This scan defines a deterministic local surface for PMBOT forbidden action review. It is a static operator review artifact only, using local docs, fixtures, and tests.

## Static Fixture

The local fixture is:

`pm_bot/tests/fixtures/safety/forbidden_action_scan.valid.json`

The fixture records scan inputs, review findings, local references, observed states, summary counts, validation commands, and closed safety boundaries. It is not runtime input and does not approve execution.

## Scan Findings

The fixture defines eight deterministic findings:

- Credential boundary remains closed.
- Endpoint boundary remains closed.
- Wallet boundary remains closed.
- Runtime boundary remains closed.
- Scheduler boundary remains closed.
- Network boundary remains closed.
- Descriptive output boundary remains closed.
- Human review boundary remains pending.

Each finding stays in `pending_operator_review` and requires a later human review record before any status can change.

## Operator Review Boundary

Operators review whether the listed local references and observed states match the task handoff. The scan does not bridge results, approve tasks, schedule work, start a worker, access credentials, access wallets, call endpoints, alter runtime or dispatcher wiring, use browser automation, or change execution surfaces.

## Safety

- Local files and static fixtures only.
- No network calls.
- No LLM provider calls.
- No external market API calls.
- No authenticated endpoint use.
- No credential, wallet, signing material, payment, or transaction endpoint use.
- No runtime, dispatcher, scheduler, worker, browser, or app-server wiring.
- No forecast scoring, action guidance, or selection advice.
- This scan is not execution approval and is not runtime input.
