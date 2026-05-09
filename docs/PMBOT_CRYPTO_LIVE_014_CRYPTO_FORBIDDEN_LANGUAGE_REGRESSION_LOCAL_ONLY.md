# PMBOT Crypto Live 014 Crypto Forbidden Language Regression Local Only

Task: `PMBOT-CRYPTO-LIVE-014-CRYPTO-FORBIDDEN-LANGUAGE-REGRESSION-LOCAL-ONLY`

Regression: `pmbot-crypto-forbidden-language-regression-001`
Contract: `pmbot_crypto_forbidden_language_regression.v1`
Run mode: `local_static_crypto_forbidden_language_regression`
Operator review: `pending_operator_review`

## Purpose

This document registers a deterministic local PMBOT crypto pilot forbidden-language regression artifact for operator review. The artifact is built from local files, local fixtures, and static literal-token samples only.

The regression restates forbidden-language coverage for crypto pilot readiness without refreshing crypto data, calling external services, approving execution, resolving outcomes, mutating runtime state, or producing forecast scoring, action guidance, or selection advice.

## Static Fixture

The local crypto forbidden-language regression fixture is:

`pm_bot/tests/fixtures/crypto_live/pmbot_crypto_forbidden_language_regression.valid.json`

The fixture records fixed forbidden-language categories, literal-token samples, source artifacts, validation command records, excluded path prefixes, summary counts, and closed safety boundaries. The fixture is not runtime input and does not approve execution.

## Source Basis

Reviewed local PMBOT artifacts:

- `docs/PMBOT_SAFETY_005_FORBIDDEN_LANGUAGE_REGRESSION_SUITE_LOCAL_ONLY.md`
- `pm_bot/tests/fixtures/safety/forbidden_language_regression_suite.valid.json`
- `docs/PMBOT_CRYPTO_LIVE_013_CRYPTO_CI_SAFE_VALIDATION_SUBSET_LOCAL_ONLY.md`
- `pm_bot/tests/fixtures/crypto_live/pmbot_crypto_ci_safe_validation_subset.valid.json`
- `tests/test_codex_queue_pmbot_templates.py`
- `pm_bot/tests/test_crypto_forbidden_language_regression.py`

These inputs keep the crypto forbidden-language regression local-only, deterministic, descriptive, and pending operator review.

## Regression Coverage

The fixture defines deterministic literal-token coverage for:

- Trade action vocabulary.
- Forecast metric vocabulary.
- Selection vocabulary.
- Exposure vocabulary.
- Crypto position vocabulary.
- Clean crypto local-review samples with no expected category flags.

Each literal-token sample is marked `pending_operator_review` and exists only to verify token detection behavior. The samples are not operator instructions.

## Operator Review Boundary

Operators review whether the listed categories, samples, local references, excluded path prefixes, validation commands, and safety boundaries are internally consistent. This regression does not approve a live run, choose a market, resolve an outcome, change review status, open external services, access credentials, access wallets, call endpoints, or change runtime, dispatcher, scheduler, worker, browser, or app-server wiring.

## Safety

- Local files, local fixtures, and static samples only.
- Literal-token samples only; no operator instruction samples.
- No network calls.
- No LLM provider calls.
- No external service calls.
- No external market API calls.
- No authenticated endpoint use.
- No credential, wallet, private-key, seed, signing, order, trading endpoint, payment, or transaction path access.
- No runtime, dispatcher, scheduler, worker, browser, resident process, timed automation, or app-server wiring.
- No forecast scoring, action guidance, market ranking, numeric prediction metric, threshold comparison output, outcome resolution, selection advice, or trade instruction output.
- This regression is not execution approval and is not runtime input.

## Validation

Required local validation commands:

- `python -m compileall pm_bot tests`
- `pytest pm_bot/tests tests/test_codex_queue_pmbot_templates.py`
