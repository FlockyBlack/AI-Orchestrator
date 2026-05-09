# PMBOT Sensitive Path Exclusion Audit

Task: `PMBOT-SAFETY-004-SENSITIVE-PATH-EXCLUSION-AUDIT-LOCAL-ONLY`

Audit: `pmbot-sensitive-path-exclusion-audit`
Contract: `pmbot_sensitive_path_exclusion_audit.v1`
Run mode: `local_static_sensitive_path_exclusion_audit`
Operator review: `pending_operator_review`

## Purpose

This audit defines a deterministic local PMBOT sensitive path exclusion surface for operator review. It is a static operator review artifact only, using local docs, fixtures, and tests.

## Static Fixture

The local fixture is:

`pm_bot/tests/fixtures/safety/sensitive_path_exclusion_audit.valid.json`

The fixture records allowed path prefixes, excluded path prefixes, local audit inputs, audit checks, summary counts, required validation commands, and closed safety boundaries. It is not runtime input and does not approve execution.

## Source Basis

Reviewed local PMBOT artifacts:

- `tests/test_codex_queue_pmbot_templates.py`
- `docs/PMBOT_VALIDATION_002_CI_SAFE_VALIDATION_SUBSET_LOCAL_ONLY.md`
- `docs/PMBOT_SAFETY_003_FORBIDDEN_ACTION_SCAN_LOCAL_ONLY.md`
- `pm_bot/tests/fixtures/safety/forbidden_action_scan.valid.json`

These sources keep the audit local-only, static, descriptive, deterministic, and pending operator review.

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

## Audit Checks

The fixture defines eight deterministic local checks:

- Allowed path scope.
- Excluded path registry.
- Environment file exclusion.
- Codex metadata exclusion.
- Execution wiring exclusion.
- PMBOT sensitive module exclusion.
- Running task exclusion.
- Operator review boundary.

Each check names a local reference under `docs/`, `pm_bot/tests/`, or `tests/` and remains `pending_operator_review`.

## Operator Review Boundary

Operators review whether the listed local references, allowed prefixes, excluded prefixes, safety boundaries, and validation commands are present and internally consistent. This audit does not approve a live run, change review status, open external services, access credentials, access wallets, call endpoints, or change runtime, dispatcher, scheduler, worker, browser, or app-server wiring.

## Safety

- Local files, local fixtures, and static samples only.
- No network calls.
- No LLM provider calls.
- No external market API calls.
- No authenticated endpoint use.
- No credential, wallet, private-key, seed, signing, order, trading endpoint, payment, or transaction path access.
- No runtime, dispatcher, scheduler, worker, browser, resident process, timed automation, or app-server wiring.
- No forecast scoring, action guidance, or selection advice.
- This audit is not execution approval and is not runtime input.

## Validation

Required local validation commands:

- `python -m compileall pm_bot tests`
- `pytest pm_bot/tests tests/test_codex_queue_pmbot_templates.py`
