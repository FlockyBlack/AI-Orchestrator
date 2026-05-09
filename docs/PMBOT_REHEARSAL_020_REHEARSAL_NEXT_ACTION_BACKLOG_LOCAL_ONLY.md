# PMBOT Rehearsal 020 Rehearsal Next Action Backlog Local Only

Task: `PMBOT-REHEARSAL-020-REHEARSAL-NEXT-ACTION-BACKLOG-LOCAL-ONLY`

Backlog: `pmbot-rehearsal-next-action-backlog-001`
Contract: `pmbot_rehearsal_next_action_backlog.v1`
Run mode: `local_static_rehearsal_next_action_backlog`
Operator review: `pending_operator_review`

## Purpose

This document registers a deterministic local PMBOT rehearsal next action backlog for operator review. The backlog uses only local documents, local readiness artifacts, local fixtures, and local tests.

The backlog records fixed rehearsal follow-up review checkpoints that remain pending operator review. It does not refresh data, call services, mutate runtime state, approve execution, start automation, access sensitive material, place orders, use trading surfaces, or change runtime, dispatcher, scheduler, worker, browser, resident process, timed automation, app-server, or run_codex wiring. It does not produce forecast scoring, action guidance, market recommendations, selection advice, probability scores, EV, edge, confidence, or side selection.

## Static Fixture

The local rehearsal next action backlog fixture is:

`pm_bot/tests/fixtures/rehearsal/pmbot_rehearsal_next_action_backlog.valid.json`

The fixture records fixed backlog rows, source artifacts, validation command records, allowed path prefixes, excluded path prefixes, summary counts, and closed safety boundaries. Backlog row order is deterministic artifact order for human review only; it is not a priority order, execution queue, recommendation, runtime input, or approval.

## Source Basis

Reviewed local PMBOT artifacts:

- `pm_bot/readiness/PMBOT_ROADMAP_003_NEXT_20_TASK_BACKLOG_GENERATOR.md`
- `docs/PMBOT_REHEARSAL_010_REHEARSAL_CI_SAFE_VALIDATION_RUNNER_LOCAL_ONLY.md`
- `docs/PMBOT_REHEARSAL_011_REHEARSAL_READINESS_DASHBOARD_CARD_LOCAL_ONLY.md`
- `docs/PMBOT_REHEARSAL_012_REHEARSAL_MORNING_OPERATOR_CARD_LOCAL_ONLY.md`
- `docs/PMBOT_REHEARSAL_013_REHEARSAL_ACCEPTANCE_REPORT_LOCAL_ONLY.md`
- `docs/PMBOT_REHEARSAL_014_REHEARSAL_SOURCE_QUALITY_LINKS_LOCAL_ONLY.md`
- `docs/PMBOT_REHEARSAL_015_REHEARSAL_PAPERLIVE_ACCOUNTING_LINKS_LOCAL_ONLY.md`
- `docs/PMBOT_REHEARSAL_016_REHEARSAL_SIMULATED_DECISION_REPLAY_LINKS_LOCAL_ONLY.md`
- `docs/PMBOT_REHEARSAL_017_REHEARSAL_FORBIDDEN_ACTION_SCAN_LOCAL_ONLY.md`
- `docs/PMBOT_REHEARSAL_018_REHEARSAL_SENSITIVE_PATH_AUDIT_LOCAL_ONLY.md`
- `docs/PMBOT_REHEARSAL_019_REHEARSAL_FAILURE_AND_ROLLBACK_PLAYBOOK_LOCAL_ONLY.md`
- `pm_bot/tests/fixtures/rehearsal/pmbot_rehearsal_failure_and_rollback_playbook.valid.json`
- `tests/test_codex_queue_pmbot_templates.py`

These inputs keep the rehearsal next action backlog local-only, deterministic, descriptive, paper-mode, and pending operator review.

## Backlog Coverage

The fixture defines eleven deterministic review checkpoint rows:

- Roadmap backlog generator review.
- Rehearsal readiness dashboard card review.
- Rehearsal morning operator card review.
- Rehearsal acceptance report review.
- Rehearsal source quality link review.
- Rehearsal paperlive accounting link review.
- Rehearsal simulated replay link review.
- Rehearsal forbidden action scan review.
- Rehearsal sensitive path audit review.
- Rehearsal failure and rollback playbook review.
- Rehearsal next action backlog fixture review.

Each row names one allowed local reference, maps to declared source artifacts, and keeps `operator_review_status` as `pending_operator_review`.

## Operator Review Boundary

Operators review whether the listed local references, static fixtures, backlog rows, source artifacts, excluded path prefixes, and validation command records are present and internally consistent. This backlog does not approve a live run, choose a market, resolve an outcome, change review status, open external services, access credentials, access wallets, call endpoints, or change runtime, dispatcher, scheduler, worker, browser, resident process, timed automation, app-server, or run_codex wiring.

This backlog is not execution approval and is not runtime input.

## Safety

- Local files, local fixtures, and static samples only.
- No network calls.
- No OpenRouter calls.
- No Polymarket API calls.
- No LLM provider calls.
- No external service calls.
- No authenticated endpoint use.
- No credential, wallet, private-key, seed, signing, order, trading endpoint, payment, or transaction path access.
- No runtime, dispatcher, scheduler, worker, browser, resident process, timed automation, app-server, or run_codex wiring.
- No validation command subprocess execution by this backlog artifact.
- No market recommendation, forecast scoring, action guidance, or selection advice.
- No probability, EV, edge, or confidence scoring.
- No real-money actions.

## Validation

Required local validation commands:

- `python -m compileall pm_bot tests`
- `pytest pm_bot/tests tests/test_codex_queue_pmbot_templates.py`
