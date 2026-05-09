# PMBOT Rehearsal 010 Rehearsal CI Safe Validation Runner Local Only

Task: `PMBOT-REHEARSAL-010-REHEARSAL-CI-SAFE-VALIDATION-RUNNER-LOCAL-ONLY`

Runner: `pmbot-rehearsal-ci-safe-validation-runner-001`
Contract: `pmbot_rehearsal_ci_safe_validation_runner.v1`
Run mode: `local_static_rehearsal_ci_safe_validation_runner`
Operator review: `pending_operator_review`

## Purpose

This document registers a deterministic local PMBOT rehearsal CI-safe validation runner for operator review. The runner validates only local rehearsal artifacts, local fixtures, and static test references.

The runner is descriptive and review-oriented. It reads a static fixture, confirms local references, checks pending review states, confirms closed safety boundaries, and emits a deterministic local review packet. It does not refresh data, call external services, execute shell validation commands, approve execution, mutate runtime state, or produce forecast scoring, action guidance, market recommendations, or selection advice.

## Static Fixture

The local fixture is:

`pm_bot/tests/fixtures/rehearsal/pmbot_rehearsal_ci_safe_validation_runner.valid.json`

The fixture records fixed runner targets, checklist items, validation command records, excluded path prefixes, summary counts, and closed safety boundaries. It does not fetch data, call endpoints, approve execution, start processes, mutate source artifacts, or produce market instructions.

## Local Runner

The local runner module is:

`pm_bot/tests/rehearsal_ci_safe_validation_runner.py`

The module exposes `run_rehearsal_ci_safe_validation()` for local CI-safe checks. It is limited to deterministic fixture reads and local path validation under `docs/`, `pm_bot/tests/`, and `tests/`.

## Source Basis

Reviewed local PMBOT artifacts:

- `docs/PMBOT_REHEARSAL_009_REHEARSAL_VALIDATION_REPLAY_PACKET_LOCAL_ONLY.md`
- `pm_bot/tests/fixtures/rehearsal/pmbot_rehearsal_validation_replay_packet.valid.json`
- `pm_bot/tests/fixtures/rehearsal/pmbot_read_only_rehearsal_scenario_contract.valid.json`
- `pm_bot/tests/fixtures/rehearsal/pmbot_rehearsal_market_packet_schema.valid.json`
- `pm_bot/tests/fixtures/rehearsal/pmbot_rehearsal_source_evidence_bundle.valid.json`
- `pm_bot/tests/fixtures/rehearsal/pmbot_rehearsal_operator_approval_record.valid.json`
- `pm_bot/tests/fixtures/rehearsal/pmbot_rehearsal_stop_condition_trigger_matrix.valid.json`
- `pm_bot/tests/fixtures/rehearsal/pmbot_rehearsal_staleness_case_set.valid.json`
- `pm_bot/tests/fixtures/rehearsal/pmbot_rehearsal_contradiction_case_set.valid.json`
- `pm_bot/tests/fixtures/rehearsal/pmbot_rehearsal_evidence_retention_ledger.valid.json`
- `pm_bot/tests/test_rehearsal_validation_replay_packet.py`
- `tests/test_codex_queue_pmbot_templates.py`

These inputs keep the runner local-only, deterministic, descriptive, paper-mode, and pending operator review.

## Runner Checks

The runner performs deterministic local checks:

- Local reference resolution.
- Prior rehearsal operator review state.
- Static fixture readability.
- Validation command record consistency.
- Closed safety boundary confirmation.
- Deterministic output confirmation.
- Human review boundary confirmation.

The runner records required validation commands for operator review but does not execute those commands itself.

## Operator Review Boundary

Operators review whether the listed local references, static fixtures, runner checks, excluded path prefixes, and validation commands are present and internally consistent. This runner does not approve a live run, choose a market, resolve an outcome, change review status, open external services, access credentials, access wallets, call endpoints, or change runtime, dispatcher, scheduler, worker, browser, resident process, or run_codex wiring.

## Safety

- Local files, local fixtures, and static samples only.
- No network calls.
- No OpenRouter calls.
- No Polymarket API calls.
- No authenticated endpoints.
- No credential, wallet, private-key, seed, signing, order, trading endpoint, payment, or transaction path access.
- No runtime, dispatcher, scheduler, worker, browser, resident process, timed automation, or run_codex wiring.
- No validation command subprocess execution by this runner.
- No forecast scoring, action guidance, market ranking, numeric prediction metric, outcome resolution, selection advice, or trade instruction output.
- No market recommendation, forecast scoring, action guidance, or selection advice.
- No probability, EV, edge, or confidence scoring.
- This runner is not execution approval and is not runtime input.

## Validation

Required local validation commands:

- `python -m compileall pm_bot tests`
- `pytest pm_bot/tests tests/test_codex_queue_pmbot_templates.py`
