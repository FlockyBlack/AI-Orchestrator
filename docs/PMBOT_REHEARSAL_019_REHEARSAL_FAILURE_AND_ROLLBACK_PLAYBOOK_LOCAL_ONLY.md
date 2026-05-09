# PMBOT Rehearsal 019 Rehearsal Failure And Rollback Playbook Local Only

Task: `PMBOT-REHEARSAL-019-REHEARSAL-FAILURE-AND-ROLLBACK-PLAYBOOK-LOCAL-ONLY`

Playbook: `pmbot-rehearsal-failure-and-rollback-playbook-001`
Contract: `pmbot_rehearsal_failure_and_rollback_playbook.v1`
Run mode: `local_static_rehearsal_failure_and_rollback_playbook`
Operator review: `pending_operator_review`

## Purpose

This document registers a deterministic local PMBOT rehearsal failure and rollback playbook for operator review. The playbook uses only local documents, local fixtures, and static records.

The playbook describes fixed rehearsal failure classes, manual review records, and rollback posture checks. It does not refresh data, call services, mutate runtime state, approve execution, start automation, access sensitive material, place orders, use trading surfaces, or roll back a live process. It does not produce forecast scoring, action guidance, market recommendations, selection advice, probability scores, EV, edge, confidence, or side selection.

## Static Fixture

The local rehearsal failure and rollback playbook fixture is:

`pm_bot/tests/fixtures/rehearsal/pmbot_rehearsal_failure_and_rollback_playbook.valid.json`

The fixture records fixed failure classes, rollback review steps, closed rollback boundaries, source artifacts, review sections, validation command records, summary counts, and closed safety boundaries. It is not runtime input and does not approve execution.

## Source Basis

Reviewed local PMBOT artifacts:

- `docs/PMBOT_REHEARSAL_004_REHEARSAL_OPERATOR_APPROVAL_RECORD_LOCAL_ONLY.md`
- `docs/PMBOT_REHEARSAL_005_REHEARSAL_STOP_CONDITION_TRIGGER_MATRIX_LOCAL_ONLY.md`
- `docs/PMBOT_REHEARSAL_009_REHEARSAL_VALIDATION_REPLAY_PACKET_LOCAL_ONLY.md`
- `docs/PMBOT_REHEARSAL_013_REHEARSAL_ACCEPTANCE_REPORT_LOCAL_ONLY.md`
- `docs/PMBOT_REHEARSAL_017_REHEARSAL_FORBIDDEN_ACTION_SCAN_LOCAL_ONLY.md`
- `docs/PMBOT_REHEARSAL_018_REHEARSAL_SENSITIVE_PATH_AUDIT_LOCAL_ONLY.md`
- `pm_bot/tests/fixtures/rehearsal/pmbot_rehearsal_operator_approval_record.valid.json`
- `pm_bot/tests/fixtures/rehearsal/pmbot_rehearsal_stop_condition_trigger_matrix.valid.json`
- `pm_bot/tests/fixtures/rehearsal/pmbot_rehearsal_validation_replay_packet.valid.json`
- `pm_bot/tests/fixtures/rehearsal/pmbot_rehearsal_forbidden_action_scan.valid.json`
- `pm_bot/tests/fixtures/rehearsal/pmbot_rehearsal_sensitive_path_audit.valid.json`
- `tests/test_codex_queue_pmbot_templates.py`

These inputs keep the rehearsal failure and rollback playbook local-only, deterministic, descriptive, paper-mode, and pending operator review.

## Failure Classes

The static playbook defines eight deterministic failure classes:

- Operator manual stop.
- Validation command failure.
- Local artifact boundary breach.
- Forbidden operation request.
- Sensitive path contact.
- Source evidence mismatch.
- Review record missing.
- Output boundary breach.

Each failure class remains `pending_operator_review`, requires a manual operator record, names local evidence, and maps to a non-executing rollback posture. The fixture does not evaluate live data, call services, or change any PMBOT state.

## Rollback Review Steps

The fixture defines six deterministic rollback review steps:

- Identify fixed failure class.
- Freeze rehearsal review status.
- Verify allowed local artifact scope.
- Confirm closed boundaries.
- Restore pending operator review posture.
- Record validation outcome.

Every step is a static operator review record. The steps do not start, stop, restart, schedule, automate, call endpoints, access credentials, access wallets, change runtime wiring, or place orders.

## Operator Review Boundary

Operators review whether the listed failure classes, rollback steps, local evidence references, validation commands, and closed safety boundaries are present and internally consistent. This playbook does not approve a live run, choose a market, resolve an outcome, change review status, open external services, access credentials, access wallets, call endpoints, or change runtime, dispatcher, scheduler, worker, browser, resident process, timed automation, app-server, or run_codex wiring.

This playbook is not execution approval and is not runtime input.

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
- No validation command subprocess execution by this playbook artifact.
- No market recommendation, forecast scoring, action guidance, or selection advice.
- No probability, EV, edge, or confidence scoring.
- No real-money actions.

## Validation

Required local validation commands:

- `python -m compileall pm_bot tests`
- `pytest pm_bot/tests tests/test_codex_queue_pmbot_templates.py`
