# PMBOT Rehearsal 018 Rehearsal Sensitive Path Audit Local Only

Task: `PMBOT-REHEARSAL-018-REHEARSAL-SENSITIVE-PATH-AUDIT-LOCAL-ONLY`

Audit: `pmbot-rehearsal-sensitive-path-audit-001`
Contract: `pmbot_rehearsal_sensitive_path_audit.v1`
Run mode: `local_static_rehearsal_sensitive_path_audit`
Operator review: `pending_operator_review`

## Purpose

This document registers a deterministic local PMBOT rehearsal sensitive path audit for operator review. The audit uses only local documents, local fixtures, and static records.

The audit restates the rehearsal sensitive path exclusions that must remain closed before any later operator decision. It does not refresh data, call services, mutate runtime state, approve execution, start automation, access sensitive material, place orders, or use trading surfaces. It does not produce forecast scoring, action guidance, market recommendations, selection advice, probability scores, EV, edge, confidence, or side selection.

## Static Fixture

The local rehearsal sensitive path audit fixture is:

`pm_bot/tests/fixtures/rehearsal/pmbot_rehearsal_sensitive_path_audit.valid.json`

The fixture records fixed allowed path prefixes, excluded path prefixes, local audit inputs, scope records, audit checks, source artifacts, validation command records, summary counts, and closed safety boundaries. It is not runtime input and does not approve execution.

## Source Basis

Reviewed local PMBOT artifacts:

- `tests/test_codex_queue_pmbot_templates.py`
- `docs/PMBOT_REHEARSAL_017_REHEARSAL_FORBIDDEN_ACTION_SCAN_LOCAL_ONLY.md`
- `pm_bot/tests/fixtures/rehearsal/pmbot_rehearsal_forbidden_action_scan.valid.json`
- `pm_bot/tests/test_rehearsal_forbidden_action_scan.py`
- `docs/PMBOT_SAFETY_004_SENSITIVE_PATH_EXCLUSION_AUDIT_LOCAL_ONLY.md`
- `pm_bot/tests/fixtures/safety/sensitive_path_exclusion_audit.valid.json`
- `pm_bot/tests/test_sensitive_path_exclusion_audit.py`
- `pm_bot/tests/test_rehearsal_sensitive_path_audit.py`

These inputs keep the rehearsal sensitive path audit local-only, deterministic, descriptive, paper-mode, and pending operator review.

## Excluded Path Prefixes

The fixture registers these deterministic exclusions:

- `.env`
- `.env.*`
- `.git/`
- `.codex/`
- `runtime/`
- `dispatcher/`
- `run_codex/`
- `pm_bot/llm/`
- `pm_bot/wallet/`
- `pm_bot/trading/`
- `pm_bot/orders/`
- `agent_tasks/running/`

## Audit Coverage

The fixture defines deterministic local-review records for:

- Allowed local output scope.
- Secret and metadata prefix exclusions.
- Execution wiring prefix exclusions.
- PMBOT sensitive module prefix exclusions.
- Rehearsal static reference scope.
- Operator review boundary.

Every scope record and audit check remains `pending_operator_review`.

## Operator Review Boundary

Operators review whether the listed local references, allowed prefixes, excluded prefixes, validation commands, and safety boundaries are present and internally consistent. This audit does not approve a live run, choose a market, resolve an outcome, change review status, open external services, access credentials, access wallets, call endpoints, or change runtime, dispatcher, scheduler, worker, browser, resident process, timed automation, app-server, or run_codex wiring.

This audit is not execution approval and is not runtime input.

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
- No validation command subprocess execution by this audit artifact.
- No market recommendation, forecast scoring, action guidance, or selection advice.
- No probability, EV, edge, or confidence scoring.
- No real-money actions.

## Validation

Required local validation commands:

- `python -m compileall pm_bot tests`
- `pytest pm_bot/tests tests/test_codex_queue_pmbot_templates.py`
