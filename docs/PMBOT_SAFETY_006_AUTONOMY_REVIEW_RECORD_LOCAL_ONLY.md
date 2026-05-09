# PMBOT Autonomy Review Record

Task: `PMBOT-SAFETY-006-AUTONOMY-REVIEW-RECORD-LOCAL-ONLY`

Record: `pmbot-autonomy-review-record`
Contract: `pmbot_autonomy_review_record.v1`
Run mode: `local_static_autonomy_review_record`
Operator review: `pending_operator_review`

## Purpose

This record defines a deterministic local PMBOT autonomy review surface for operator review. It is a static fixture and pytest artifact only, using local docs, local fixtures, and static samples.

## Static Fixture

The local fixture is:

`pm_bot/tests/fixtures/safety/autonomy_review_record.valid.json`

The fixture records allowed path prefixes, source inputs, review items, summary counts, required validation commands, and closed safety boundaries. It is not runtime input and does not approve execution.

## Source Basis

Reviewed local PMBOT artifacts:

- `tests/test_codex_queue_pmbot_templates.py`
- `docs/PMBOT_SAFETY_001_AUTONOMY_GATE_CHECKLIST_LOCAL_ONLY.md`
- `docs/PMBOT_SAFETY_002_NIGHT_BATCH_POSTRUN_AUDIT_SUMMARY_LOCAL_ONLY.md`
- `docs/PMBOT_SAFETY_003_FORBIDDEN_ACTION_SCAN_LOCAL_ONLY.md`
- `docs/PMBOT_SAFETY_004_SENSITIVE_PATH_EXCLUSION_AUDIT_LOCAL_ONLY.md`
- `docs/PMBOT_SAFETY_005_FORBIDDEN_LANGUAGE_REGRESSION_SUITE_LOCAL_ONLY.md`

These sources keep the record local-only, static, descriptive, deterministic, and pending operator review.

## Review Items

The fixture defines eight deterministic local review items:

- Allowed path scope.
- Source basis.
- Prior safety records.
- Endpoint boundary.
- Sensitive path boundary.
- Language boundary.
- Validation command record.
- Operator status.

Each item names a local reference under `docs/`, `pm_bot/tests/`, or `tests/` and remains `pending_operator_review`.

## Operator Review Boundary

Operators review whether the listed local references, source inputs, review items, safety boundaries, and validation commands are present and internally consistent. This record does not approve a live run, change review status, open external services, access credentials, access wallets, call endpoints, alter runtime or dispatcher wiring, start timed automation, or produce market instructions.

## Safety

- Local files, local fixtures, and static samples only.
- No network calls.
- No LLM provider calls.
- No external market API calls.
- No authenticated endpoint use.
- No credential, wallet, private-key, seed, signing, order, trading endpoint, payment, or transaction path access.
- No runtime, dispatcher, scheduler, worker, browser, resident process, timed automation, or app-server wiring.
- No forecast scoring, action guidance, or selection advice.
- This record is not execution approval and is not runtime input.

## Validation

Required local validation commands:

- `python -m compileall pm_bot tests`
- `pytest pm_bot/tests tests/test_codex_queue_pmbot_templates.py`
