# PMBOT Validation 003 Batch Validation Replay Report Local Only

Task: `PMBOT-VALIDATION-003-BATCH-VALIDATION-REPLAY-REPORT-LOCAL-ONLY`

Report: `pmbot-batch-validation-replay-report-001`
Contract: `pmbot_batch_validation_replay_report.v1`
Run mode: `local_static_batch_validation_replay_report`
Operator review: `pending_operator_review`

## Purpose

This document registers a deterministic local PMBOT batch validation replay report for operator review. The report groups saved evidence replay, CI-safe validation subset, simulated decision replay, queue template boundary, and validation command records so a human operator can review the local validation surface before any later status change outside this report.

The report is descriptive only. It is not execution approval, runtime input, market analysis, forecast scoring, action guidance, or selection advice.

## Static Fixture

The local fixture is:

`pm_bot/tests/fixtures/validation/pmbot_batch_validation_replay_report.valid.json`

The fixture records fixed report sections, replay records, operator review checks, validation command records, excluded path prefixes, summary counts, and closed safety boundaries. It does not fetch data, call endpoints, approve execution, start processes, mutate source artifacts, or produce market instructions.

## Source Basis

Reviewed local PMBOT artifacts:

- `docs/PMBOT_VALIDATION_001_SAVED_EVIDENCE_REPLAY_BUNDLE_LOCAL_ONLY.md`
- `pm_bot/tests/fixtures/validation/pmbot_saved_evidence_replay_bundle.valid.json`
- `docs/PMBOT_VALIDATION_002_CI_SAFE_VALIDATION_SUBSET_LOCAL_ONLY.md`
- `pm_bot/tests/fixtures/validation/pmbot_ci_safe_validation_subset.valid.json`
- `pm_bot/simulated_decisions/samples/simulated_decision_replay_summary.fixture.json`
- `pm_bot/tests/fixtures/simulated_decisions/simulated_decision_replay_summary_request.valid.json`
- `pm_bot/simulated_decisions/samples/simulated_decision_audit_ledger.fixture.json`
- `pm_bot/simulated_decisions/samples/simulated_decision_packet.fixture.json`
- `tests/test_codex_queue_pmbot_templates.py`
- `pm_bot/tests/test_saved_evidence_replay_bundle.py`
- `pm_bot/tests/test_ci_safe_validation_subset.py`
- `pm_bot/tests/test_batch_validation_replay_report.py`

These sources keep the batch validation replay local-only, static, descriptive, deterministic, and pending operator review.

## Report Sections

The fixture defines six deterministic report sections:

- Batch validation replay identity.
- Saved evidence replay bundle records.
- CI-safe validation subset records.
- Simulated decision replay summary records.
- Queue template validation boundary.
- Validation command records.

Every report section remains `pending_operator_review` and names only local references.

## Replay Records

The replay records restate local documents, fixtures, samples, and tests that were already saved for validation review. They do not change source artifact state and do not mark any task accepted, complete, or ready for execution.

## Operator Review Boundary

Operators review whether the listed local references, static fixtures, report sections, replay records, excluded path prefixes, and validation commands are present and internally consistent. This report does not approve a live run, choose a market, resolve an outcome, change review status, open external services, access credentials, access wallets, call endpoints, or change runtime, dispatcher, scheduler, worker, browser, or app-server wiring.

## Safety

- Local files, local fixtures, and static samples only.
- No network calls.
- No LLM provider calls.
- No external service calls.
- No external market API calls.
- No authenticated endpoint use.
- No credential, wallet, private-key, seed, signing, order, trading endpoint, payment, or transaction path access.
- No runtime, dispatcher, scheduler, worker, browser, resident process, timed automation, or app-server wiring.
- No forecast scoring, action guidance, or selection advice.
- This report is not execution approval and is not runtime input.

## Validation

Required local validation commands:

- `python -m compileall pm_bot tests`
- `pytest pm_bot/tests tests/test_codex_queue_pmbot_templates.py`
