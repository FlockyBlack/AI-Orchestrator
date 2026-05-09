# PMBOT Crypto Live 015 Crypto Sensitive Path Exclusion Audit Local Only

Task: `PMBOT-CRYPTO-LIVE-015-CRYPTO-SENSITIVE-PATH-EXCLUSION-AUDIT-LOCAL-ONLY`

Audit: `pmbot-crypto-sensitive-path-exclusion-audit-001`
Contract: `pmbot_crypto_sensitive_path_exclusion_audit.v1`
Run mode: `local_static_crypto_sensitive_path_exclusion_audit`
Operator review: `pending_operator_review`

## Purpose

This document registers a deterministic local PMBOT crypto pilot sensitive path exclusion audit for operator review. The audit is built from local files, local fixtures, and static records only.

The audit restates crypto pilot sensitive path exclusions for readiness review without refreshing crypto data, calling external services, approving execution, resolving outcomes, mutating runtime state, or producing forecast scoring, action guidance, or selection advice.

## Static Fixture

The local crypto sensitive path exclusion audit fixture is:

`pm_bot/tests/fixtures/crypto_live/pmbot_crypto_sensitive_path_exclusion_audit.valid.json`

The fixture records fixed allowed path prefixes, excluded path prefixes, source artifacts, audit scope records, audit checks, validation command records, summary counts, and closed safety boundaries. The fixture is not runtime input and does not approve execution.

## Source Basis

Reviewed local PMBOT artifacts:

- `docs/PMBOT_SAFETY_004_SENSITIVE_PATH_EXCLUSION_AUDIT_LOCAL_ONLY.md`
- `pm_bot/tests/fixtures/safety/sensitive_path_exclusion_audit.valid.json`
- `pm_bot/tests/test_sensitive_path_exclusion_audit.py`
- `docs/PMBOT_CRYPTO_LIVE_014_CRYPTO_FORBIDDEN_LANGUAGE_REGRESSION_LOCAL_ONLY.md`
- `pm_bot/tests/fixtures/crypto_live/pmbot_crypto_forbidden_language_regression.valid.json`
- `docs/PMBOT_CRYPTO_LIVE_013_CRYPTO_CI_SAFE_VALIDATION_SUBSET_LOCAL_ONLY.md`
- `pm_bot/tests/fixtures/crypto_live/pmbot_crypto_ci_safe_validation_subset.valid.json`
- `tests/test_codex_queue_pmbot_templates.py`
- `pm_bot/tests/test_crypto_sensitive_path_exclusion_audit.py`

These inputs keep the crypto sensitive path exclusion audit local-only, deterministic, descriptive, and pending operator review.

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
- Crypto local artifact reference scope.
- Operator review boundary.

Every audit scope record and audit check remains `pending_operator_review`.

## Operator Review Boundary

Operators review whether the listed local references, allowed prefixes, excluded prefixes, validation commands, and safety boundaries are present and internally consistent. This audit does not approve a live run, choose a market, resolve an outcome, change review status, open external services, access credentials, access wallets, call endpoints, or change runtime, dispatcher, scheduler, worker, browser, or app-server wiring.

## Safety

- Local files, local fixtures, and static records only.
- No network calls.
- No LLM provider calls.
- No external service calls.
- No external market API calls.
- No authenticated endpoint use.
- No credential, wallet, private-key, seed, signing, order, trading endpoint, payment, or transaction path access.
- No runtime, dispatcher, scheduler, worker, browser, resident process, timed automation, or app-server wiring.
- No forecast scoring, action guidance, market ranking, numeric prediction metric, threshold comparison output, outcome resolution, selection advice, or trade instruction output.
- This audit is not execution approval and is not runtime input.

## Validation

Required local validation commands:

- `python -m compileall pm_bot tests`
- `pytest pm_bot/tests tests/test_codex_queue_pmbot_templates.py`
