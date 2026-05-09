# PMBOT Forbidden Language Regression Suite

Task: `PMBOT-SAFETY-005-FORBIDDEN-LANGUAGE-REGRESSION-SUITE-LOCAL-ONLY`

Suite: `pmbot-forbidden-language-regression-suite`
Contract: `pmbot_forbidden_language_regression_suite.v1`
Run mode: `local_static_forbidden_language_regression_suite`
Operator review: `pending_operator_review`

## Purpose

This suite defines a deterministic local PMBOT forbidden-language regression surface for operator review. It is a static fixture and pytest artifact only, using local docs, local fixtures, and literal-token samples.

## Static Fixture

The local fixture is:

`pm_bot/tests/fixtures/safety/forbidden_language_regression_suite.valid.json`

The fixture records forbidden-language categories, literal-token regression samples, source artifacts, summary counts, required validation commands, and closed safety boundaries. It is not runtime input and does not approve execution.

## Source Basis

Reviewed local PMBOT artifacts:

- `docs/PMBOT_SAFETY_003_FORBIDDEN_ACTION_SCAN_LOCAL_ONLY.md`
- `docs/PMBOT_SAFETY_004_SENSITIVE_PATH_EXCLUSION_AUDIT_LOCAL_ONLY.md`
- `pm_bot/tests/fixtures/safety/forbidden_action_scan.valid.json`
- `tests/test_codex_queue_pmbot_templates.py`

These sources keep the suite local-only, static, descriptive, deterministic, and pending operator review.

## Regression Coverage

The fixture defines deterministic literal-token coverage for:

- Trade action vocabulary.
- Forecast metric vocabulary.
- Selection vocabulary.
- Exposure vocabulary.
- Clean local-review samples with no expected category flags.

Each literal-token sample is marked `pending_operator_review` and exists only to verify token detection behavior. The samples are not operator instructions.

## Operator Review Boundary

Operators review whether the listed categories, samples, source artifacts, safety boundaries, and validation commands are internally consistent. This suite does not approve a live run, change review status, open external services, access credentials, access wallets, call endpoints, alter runtime or dispatcher wiring, start timed automation, or produce market instructions.

## Safety

- Local files, local fixtures, and static samples only.
- Literal-token samples only; no operator instruction samples.
- No network calls.
- No LLM provider calls.
- No external market API calls.
- No authenticated endpoint use.
- No credential, wallet, private-key, seed, signing, order, trading endpoint, payment, or transaction path access.
- No runtime, dispatcher, scheduler, worker, browser, resident process, timed automation, or app-server wiring.
- No forecast scoring, action guidance, or selection advice.
- This suite is not execution approval and is not runtime input.

## Validation

Required local validation commands:

- `python -m compileall pm_bot tests`
- `pytest pm_bot/tests tests/test_codex_queue_pmbot_templates.py`
