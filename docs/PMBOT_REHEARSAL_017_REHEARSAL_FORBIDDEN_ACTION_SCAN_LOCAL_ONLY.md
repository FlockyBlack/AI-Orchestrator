# PMBOT Rehearsal 017 Rehearsal Forbidden Action Scan Local Only

Task: `PMBOT-REHEARSAL-017-REHEARSAL-FORBIDDEN-ACTION-SCAN-LOCAL-ONLY`

Scan: `pmbot-rehearsal-forbidden-action-scan-001`
Contract: `pmbot_rehearsal_forbidden_action_scan.v1`
Run mode: `local_static_rehearsal_forbidden_action_scan`
Operator review: `pending_operator_review`

## Purpose

This document registers a deterministic local PMBOT rehearsal forbidden action scan for operator review. The scan uses only local documents, local fixtures, and local tests.

The scan records a fixed set of closed boundaries for rehearsal review. It does not refresh data, call services, mutate runtime state, approve execution, start automation, access sensitive material, place orders, or use trading surfaces. It does not produce forecast scoring, action guidance, market recommendations, selection advice, probability scores, EV, edge, confidence, or side selection.

## Static Artifact

The local rehearsal scan fixture is:

`pm_bot/tests/fixtures/rehearsal/pmbot_rehearsal_forbidden_action_scan.valid.json`

The fixture records local scan inputs, forbidden action rows, allowed and excluded path prefixes, required validation commands, validation command records, summary counts, and closed safety boundaries. It is not runtime input and does not approve execution.

## Source Basis

Reviewed local PMBOT artifacts:

- `tests/test_codex_queue_pmbot_templates.py`
- `docs/PMBOT_REHEARSAL_016_REHEARSAL_SIMULATED_DECISION_REPLAY_LINKS_LOCAL_ONLY.md`
- `docs/PMBOT_SAFETY_002_NIGHT_BATCH_POSTRUN_AUDIT_SUMMARY_LOCAL_ONLY.md`
- `docs/PMBOT_SAFETY_003_FORBIDDEN_ACTION_SCAN_LOCAL_ONLY.md`
- `docs/PMBOT_SAFETY_004_SENSITIVE_PATH_EXCLUSION_AUDIT_LOCAL_ONLY.md`
- `pm_bot/tests/fixtures/safety/forbidden_action_scan.valid.json`
- `pm_bot/tests/fixtures/rehearsal/pmbot_rehearsal_validation_replay_packet.valid.json`
- `pm_bot/tests/fixtures/rehearsal/pmbot_rehearsal_ci_safe_validation_runner.valid.json`
- `pm_bot/tests/test_rehearsal_forbidden_action_scan.py`

These inputs keep the rehearsal forbidden action scan local-only, deterministic, descriptive, paper-mode, and pending operator review.

## Scan Rows

The static scan defines twelve deterministic rows:

- Local material boundary remains closed.
- Network boundary remains closed.
- OpenRouter boundary remains closed.
- Polymarket API boundary remains closed.
- Authenticated endpoint boundary remains closed.
- Credential and secret boundary remains closed.
- Wallet and signing boundary remains closed.
- Order and trading boundary remains closed.
- Runtime, dispatcher, and run_codex boundary remains closed.
- Scheduler, worker, and browser boundary remains closed.
- Descriptive output boundary remains closed.
- Human review boundary remains pending.

Each row stays in `pending_operator_review` and requires later human review before any status can change.

## Operator Review Boundary

Operators review whether the listed local references and observed states match this rehearsal handoff. The scan does not bridge results, approve tasks, schedule work, start a worker, access credentials, access wallets, call endpoints, alter runtime or dispatcher wiring, use browser automation, change execution surfaces, or alter review status.

This scan is not execution approval and is not runtime input.

## Safety

- Local files, local fixtures, and static samples only.
- No network calls.
- No OpenRouter calls.
- No Polymarket API calls.
- No LLM provider calls.
- No external service calls.
- No authenticated endpoint use.
- No credential, wallet, private-key, seed, signing, order, trading endpoint, payment, or transaction path access.
- No runtime, dispatcher, scheduler, worker, browser, resident process, timed automation, or run_codex wiring.
- No validation command subprocess execution by this scan artifact.
- No market recommendation, forecast scoring, action guidance, or selection advice.
- No probability, EV, edge, or confidence scoring.
- No real-money actions.

## Validation

Required local validation commands:

- `python -m compileall pm_bot tests`
- `pytest pm_bot/tests tests/test_codex_queue_pmbot_templates.py`
