# PMBOT Crypto Live 013 Crypto CI Safe Validation Subset Local Only

Task: `PMBOT-CRYPTO-LIVE-013-CRYPTO-CI-SAFE-VALIDATION-SUBSET-LOCAL-ONLY`

Subset: `pmbot-crypto-ci-safe-validation-subset-001`
Contract: `pmbot_crypto_ci_safe_validation_subset.v1`
Run mode: `local_static_crypto_ci_safe_validation_subset`
Operator review: `pending_operator_review`

## Purpose

This document registers a deterministic local PMBOT crypto pilot CI-safe validation subset for operator review. The subset is built from local files, local fixtures, and static samples only.

The subset restates crypto pilot readiness validation targets and command records for human review. It does not refresh crypto data, call external services, approve execution, resolve outcomes, mutate runtime state, or produce forecast scoring, action guidance, or selection advice.

## Static Fixture

The local crypto CI-safe validation subset fixture is:

`pm_bot/tests/fixtures/crypto_live/pmbot_crypto_ci_safe_validation_subset.valid.json`

The fixture records fixed validation targets, subset sections, subset checks, validation command records, excluded path prefixes, summary counts, and closed safety boundaries. Every target remains `pending_operator_review` or a local validation reference.

## Source Basis

Reviewed local PMBOT artifacts:

- `docs/PMBOT_CRYPTO_LIVE_012_CRYPTO_VALIDATION_REPLAY_BUNDLE_LOCAL_ONLY.md`
- `pm_bot/tests/fixtures/crypto_live/pmbot_crypto_validation_replay_bundle.valid.json`
- `pm_bot/tests/fixtures/crypto_live/pmbot_crypto_supervised_live_gap_matrix.valid.json`
- `pm_bot/tests/fixtures/crypto_live/pmbot_crypto_operator_approval_gate_record.valid.json`
- `pm_bot/tests/fixtures/crypto_live/pmbot_crypto_stop_condition_mapping.valid.json`
- `pm_bot/tests/fixtures/crypto_live/pmbot_crypto_outcome_evidence_bundle.valid.json`
- `pm_bot/tests/fixtures/crypto_live/pmbot_crypto_paperlive_observation_replay.valid.json`
- `pm_bot/tests/fixtures/crypto_live/pmbot_crypto_paperlive_rehearsal_packet.valid.json`
- `tests/test_codex_queue_pmbot_templates.py`
- `pm_bot/tests/test_crypto_ci_safe_validation_subset.py`

These inputs keep the crypto validation subset local-only, deterministic, descriptive, and pending operator review.

## Validation Subset

The fixture defines six deterministic subset sections:

- Subset identity review.
- Crypto readiness gate review.
- Crypto replay chain review.
- Queue template validation review.
- Validation command review.
- Closed boundary review.

Every section names only local references and preserves the review status of the source records.

## Operator Review Boundary

Operators review whether the listed local references, static fixtures, subset sections, excluded path prefixes, and validation commands are present and internally consistent. This subset does not approve a live run, choose a market, resolve an outcome, change review status, open external services, access credentials, access wallets, call endpoints, or change runtime, dispatcher, scheduler, worker, browser, or app-server wiring.

## Safety

- Local files, local fixtures, and static samples only.
- No network calls.
- No LLM provider calls.
- No external service calls.
- No external market API calls.
- No authenticated endpoint use.
- No credential, wallet, private-key, seed, signing, order, trading endpoint, payment, or transaction path access.
- No runtime, dispatcher, scheduler, worker, browser, resident process, timed automation, or app-server wiring.
- No forecast scoring, action guidance, market ranking, numeric prediction metric, threshold comparison output, outcome resolution, selection advice, or trade instruction output.
- This subset is not execution approval and is not runtime input.

## Validation

Required local validation commands:

- `python -m compileall pm_bot tests`
- `pytest pm_bot/tests tests/test_codex_queue_pmbot_templates.py`
