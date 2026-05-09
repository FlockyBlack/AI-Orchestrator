# PMBOT Validation 001 Saved Evidence Replay Bundle Local Only

Task: `PMBOT-VALIDATION-001-SAVED-EVIDENCE-REPLAY-BUNDLE-LOCAL-ONLY`

Bundle: `pmbot-saved-evidence-replay-bundle-001`
Contract: `pmbot_saved_evidence_replay_bundle.v1`
Run mode: `local_static_saved_evidence_replay_bundle`
Operator review: `pending_operator_review`

## Purpose

This document registers a local PMBOT saved evidence replay bundle for validation review. The bundle is deterministic and built from local files, local fixtures, and static samples only.

The bundle is descriptive only. It is not execution approval, runtime input, market analysis, forecast scoring, action guidance, or selection advice.

## Static Fixture

The local fixture is:

`pm_bot/tests/fixtures/validation/pmbot_saved_evidence_replay_bundle.valid.json`

The fixture records fixed saved evidence records, replay sections, operator review checks, validation commands, summary counts, and closed safety boundaries. It does not fetch data, call endpoints, approve execution, start processes, mutate source artifacts, or produce market instructions.

## Source Basis

Reviewed local PMBOT artifacts:

- `docs/PMBOT_VALIDATION_001_SAVED_EVIDENCE_REPLAY_BUNDLE_LOCAL_ONLY.md`
- `pm_bot/tests/fixtures/validation/pmbot_saved_evidence_replay_bundle.valid.json`
- `docs/PMBOT_SUPERVISED_LIVE_005_LIVE_READINESS_EVIDENCE_BUNDLE_LOCAL_ONLY.md`
- `pm_bot/tests/fixtures/readiness/pmbot_supervised_live_readiness_evidence_bundle.valid.json`
- `pm_bot/tests/fixtures/readiness/pmbot_local_to_supervised_live_gap_matrix.valid.json`
- `pm_bot/simulated_decisions/samples/simulated_decision_replay_summary.fixture.json`
- `pm_bot/tests/fixtures/simulated_decisions/simulated_decision_replay_summary_request.valid.json`
- `pm_bot/simulated_decisions/samples/simulated_decision_audit_ledger.fixture.json`
- `pm_bot/simulated_decisions/samples/simulated_decision_packet.fixture.json`
- `tests/test_codex_queue_pmbot_templates.py`

These sources keep the validation replay local-only, static, descriptive, and pending operator review.

## Replay Sections

The fixture defines four deterministic replay sections:

- Bundle identity records for this local validation artifact.
- Readiness evidence records for supervised-live review artifacts.
- Simulated decision replay records for saved local packet, audit, and replay samples.
- Queue validation record for PMBOT task template safety boundaries.

Every saved evidence record remains `pending_operator_review`, names only local references, and requires a human record before any later status change.

## Operator Review Boundary

Operators review whether the listed local references, static artifacts, replay sections, and validation commands are present and internally consistent. This bundle does not approve a live run, choose a market, resolve an outcome, change review status, open external services, access credentials, access wallets, call endpoints, or change runtime, dispatcher, scheduler, worker, browser, or app-server wiring.

## Safety

- Local files, local fixtures, and static samples only.
- No network calls.
- No LLM provider calls.
- No external market API calls.
- No authenticated endpoint use.
- No credential, wallet, private-key, seed, signing, order, trading endpoint, payment, or transaction path access.
- No runtime, dispatcher, scheduler, worker, browser, resident process, timed automation, or app-server wiring.
- No forecast scoring, action guidance, market ranking, numeric prediction metric, stance selection, or trade action guidance.
- This bundle is not execution approval and is not runtime input.

## Validation

Required local validation commands:

- `python -m compileall pm_bot tests`
- `pytest pm_bot/tests tests/test_codex_queue_pmbot_templates.py`
