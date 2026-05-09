# PMBOT Roadmap 004 Real Wallet Gated Milestone Separation Local Only

Task: `PMBOT-ROADMAP-004-REAL-WALLET-GATED-MILESTONE-SEPARATION-LOCAL-ONLY`

Milestone set: `pmbot-real-wallet-gated-milestone-separation-001`
Contract: `pmbot_real_wallet_gated_milestone_separation.v1`
Run mode: `local_static_real_wallet_gated_milestone_separation`
Operator review: `pending_operator_review`

## Purpose

This document defines the local gated milestone separation record for PMBOT sensitive-access readiness review. It is a deterministic operator review artifact built from local files, local fixtures, and static samples only.

The record is descriptive only. It is not execution approval, runtime input, market analysis, forecast scoring, action guidance, or selection advice.

## Static Fixture

The local fixture is:

`pm_bot/tests/fixtures/readiness/pmbot_real_wallet_gated_milestone_separation.valid.json`

The fixture records fixed milestone rows, separation rules, local source artifacts, required validation commands, summary counts, allowed and excluded path prefixes, and closed safety boundaries. It does not approve real wallet access, credential access, signing, transaction endpoints, execution wiring, status changes, or live operation.

## Source Basis

Reviewed local PMBOT artifacts:

- `pm_bot/readiness/PMBOT_ROADMAP_001_REAL_WALLET_READINESS_BLOCKER_MATRIX.md`
- `pm_bot/readiness/PMBOT_ROADMAP_002_PMBOT_LOCAL_TO_SUPERVISED_LIVE_GAP_MATRIX.md`
- `docs/PMBOT_SUPERVISED_LIVE_003_OPERATOR_APPROVAL_GATE_RECORD_LOCAL_ONLY.md`
- `docs/PMBOT_SUPERVISED_LIVE_005_LIVE_READINESS_EVIDENCE_BUNDLE_LOCAL_ONLY.md`
- `docs/PMBOT_SAFETY_003_FORBIDDEN_ACTION_SCAN_LOCAL_ONLY.md`
- `docs/PMBOT_SAFETY_004_SENSITIVE_PATH_EXCLUSION_AUDIT_LOCAL_ONLY.md`
- `tests/test_codex_queue_pmbot_templates.py`

These sources keep PMBOT sensitive-access readiness work local-only, static, paper-mode, and pending operator review.

## Milestone Separation

The fixture defines six deterministic milestone rows:

- Paper-mode baseline milestone.
- Supervised review boundary milestone.
- Sensitive-access scope record milestone.
- Credential and wallet boundary milestone.
- Runtime wiring boundary milestone.
- Validation replay milestone.

Each row remains `pending_operator_review`, keeps `approval_state` as `not_approved`, and keeps `transition_state` as `blocked_until_separate_operator_record`.

## Separation Rules

The fixture defines fixed separation rules that keep paper-mode review, supervised review, sensitive-access scoping, credential and wallet handling, runtime wiring, and validation replay as separate operator-reviewed milestones. No milestone row changes another row's status, widens scope, or grants access to a later milestone.

## Operator Review Boundary

Operators review whether the listed local references, separated milestones, and required human records match the handoff. This record does not approve a live run, choose a market, resolve an outcome, change review status, open external services, access credentials, access wallets, call endpoints, or change runtime, dispatcher, scheduler, worker, browser, or app-server wiring.

## Safety

- Local files and static fixtures only.
- No network calls.
- No LLM provider calls.
- No external market API calls.
- No authenticated endpoint use.
- No credential, wallet, private-key, seed, signing, order, trading endpoint, payment, or transaction path access.
- No runtime, dispatcher, scheduler, worker, browser, resident process, timed automation, or app-server wiring.
- No forecast scoring, action guidance, market ranking, numeric prediction metric, stance selection, or trade action guidance.
- This record is not execution approval and is not runtime input.
