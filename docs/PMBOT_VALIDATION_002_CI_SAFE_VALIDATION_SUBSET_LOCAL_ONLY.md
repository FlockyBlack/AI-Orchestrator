# PMBOT Validation 002 CI Safe Validation Subset Local Only

Task: `PMBOT-VALIDATION-002-CI-SAFE-VALIDATION-SUBSET-LOCAL-ONLY`

Subset: `pmbot-ci-safe-validation-subset-001`
Contract: `pmbot_ci_safe_validation_subset.v1`
Run mode: `local_static_ci_safe_validation_subset`
Operator review: `pending_operator_review`

## Purpose

This document registers a deterministic PMBOT CI-safe validation subset for operator review. The subset is built from local files, local fixtures, and static samples only.

The subset is descriptive only. It is not execution approval, runtime input, market analysis, forecast scoring, action guidance, or selection advice.

## Static Fixture

The local fixture is:

`pm_bot/tests/fixtures/validation/pmbot_ci_safe_validation_subset.valid.json`

The fixture records fixed validation targets, local check records, required validation commands, closed safety boundaries, excluded path prefixes, summary counts, and pending operator review status. It does not fetch data, call endpoints, approve execution, start processes, mutate source artifacts, or produce market instructions.

## Source Basis

Reviewed local PMBOT artifacts:

- `docs/PMBOT_VALIDATION_001_SAVED_EVIDENCE_REPLAY_BUNDLE_LOCAL_ONLY.md`
- `pm_bot/tests/fixtures/validation/pmbot_saved_evidence_replay_bundle.valid.json`
- `pm_bot/tests/test_saved_evidence_replay_bundle.py`
- `pm_bot/tests/test_autonomy_gate_checklist.py`
- `pm_bot/tests/test_forbidden_action_scan.py`
- `tests/test_codex_queue_pmbot_templates.py`

These sources keep the subset local-only, static, descriptive, deterministic, and pending operator review.

## Validation Subset

The fixture defines seven deterministic local checks:

- Local reference scope.
- Static fixture scope.
- Validation command scope.
- External call boundary.
- Sensitive path boundary.
- Execution wiring boundary.
- Human review boundary.

Each check names a local reference under `docs/`, `pm_bot/tests/`, or `tests/` and remains `pending_operator_review`.

## Operator Review Boundary

Operators review whether the listed local references, static fixtures, safety boundaries, excluded path prefixes, and validation commands are present and internally consistent. This subset does not approve a live run, choose a market, resolve an outcome, change review status, open external services, access credentials, access wallets, call endpoints, or change runtime, dispatcher, scheduler, worker, browser, or app-server wiring.

## Safety

- Local files, local fixtures, and static samples only.
- No network calls.
- No LLM provider calls.
- No external market API calls.
- No authenticated endpoint use.
- No credential, wallet, private-key, seed, signing, order, trading endpoint, payment, or transaction path access.
- No runtime, dispatcher, scheduler, worker, browser, resident process, timed automation, or app-server wiring.
- No forecast scoring, action guidance, or selection advice.
- This subset is not execution approval and is not runtime input.

## Validation

Required local validation commands:

- `python -m compileall pm_bot tests`
- `pytest pm_bot/tests tests/test_codex_queue_pmbot_templates.py`
