# PMBOT Supervised Live 004 Supervised Live Stop Condition Spec Local Only

Task: `PMBOT-SUPERVISED-LIVE-004-SUPERVISED-LIVE-STOP-CONDITION-SPEC-LOCAL-ONLY`

Spec: `pmbot-supervised-live-stop-condition-spec-001`
Contract: `pmbot_supervised_live_stop_condition_spec.v1`
Run mode: `local_static_supervised_live_stop_condition_spec`
Operator review: `pending_operator_review`

## Purpose

This document defines the local stop-condition specification for supervised-live readiness review. It is a deterministic operator review artifact built from local files, local fixtures, and static samples only.

The specification is descriptive only. It is not execution approval, runtime input, market analysis, forecast scoring, action guidance, or selection advice.

## Static Fixture

The local fixture is:

`pm_bot/tests/fixtures/readiness/pmbot_supervised_live_stop_condition_spec.valid.json`

The fixture records fixed stop-condition rows, trigger evidence references, required operator record fields, source artifacts, review checks, validation commands, summary counts, and closed safety boundaries. It does not start, stop, restart, approve, or mutate any live process; it only names local review conditions for a human record.

## Source Basis

Reviewed local PMBOT artifacts:

- `docs/PMBOT_SUPERVISED_LIVE_001_READ_ONLY_LIVE_DATA_CONTRACT_LOCAL_ONLY.md`
- `docs/PMBOT_SUPERVISED_LIVE_002_LIVE_DATA_SOURCE_INVENTORY_LOCAL_ONLY.md`
- `docs/PMBOT_SUPERVISED_LIVE_003_OPERATOR_APPROVAL_GATE_RECORD_LOCAL_ONLY.md`
- `pm_bot/readiness/PMBOT_ROADMAP_002_PMBOT_LOCAL_TO_SUPERVISED_LIVE_GAP_MATRIX.md`
- `docs/PMBOT_SAFETY_003_FORBIDDEN_ACTION_SCAN_LOCAL_ONLY.md`
- `tests/test_codex_queue_pmbot_templates.py`

These sources keep PMBOT supervised readiness work local-only, static, paper-mode, and pending operator review.

## Stop Condition Records

The fixture defines six deterministic stop-condition records:

- Operator manual stop request.
- Local artifact boundary breach.
- Forbidden operation request detected.
- Local validation command failed.
- Source record label dispute.
- Missing operator gate record.

Every stop-condition record remains `pending_operator_review`, requires a manual operator record, names a local evidence reference, and maps to a blocked or stopped review state.

## Operator Review Boundary

Operators review whether the listed stop conditions, evidence references, and required record fields match the supervised-live handoff. This specification does not approve a live run, choose a market, resolve an outcome, change review status, open external services, access credentials, access wallets, call endpoints, or change runtime, dispatcher, scheduler, worker, browser, or app-server wiring.

## Safety

- Local files and static fixtures only.
- No network calls.
- No LLM provider calls.
- No external market API calls.
- No authenticated endpoint use.
- No credential, wallet, private-key, seed, signing, order, trading endpoint, payment, or transaction path access.
- No runtime, dispatcher, scheduler, worker, browser, resident process, timed automation, or app-server wiring.
- No forecast scoring, action guidance, market ranking, numeric prediction metric, stance selection, or trade action guidance.
- This specification is not execution approval and is not runtime input.
