# PMBOT Crypto Live 012 Crypto Validation Replay Bundle Local Only

Task: `PMBOT-CRYPTO-LIVE-012-CRYPTO-VALIDATION-REPLAY-BUNDLE-LOCAL-ONLY`

Bundle: `pmbot-crypto-validation-replay-bundle-001`
Contract: `pmbot_crypto_validation_replay_bundle.v1`
Run mode: `local_static_crypto_validation_replay_bundle`
Operator review: `pending_operator_review`

## Purpose

This document registers a deterministic local PMBOT crypto pilot validation replay bundle for operator review. The bundle is built from local files, local fixtures, and static samples only.

The bundle restates crypto pilot readiness records, replay records, and validation command records for human review. It does not refresh crypto data, call external services, approve execution, resolve outcomes, mutate runtime state, or produce forecast scoring, action guidance, or selection advice.

## Static Fixture

The local crypto validation replay bundle fixture is:

`pm_bot/tests/fixtures/crypto_live/pmbot_crypto_validation_replay_bundle.valid.json`

The fixture records fixed replay records, replay sections, validation command records, excluded path prefixes, summary counts, and closed safety boundaries. Every replay record remains `pending_operator_review` or a local validation reference.

## Source Basis

Reviewed local PMBOT artifacts:

- `docs/PMBOT_CRYPTO_LIVE_011_CRYPTO_SUPERVISED_LIVE_GAP_MATRIX_LOCAL_ONLY.md`
- `pm_bot/tests/fixtures/crypto_live/pmbot_crypto_supervised_live_gap_matrix.valid.json`
- `pm_bot/tests/fixtures/crypto_live/pmbot_crypto_operator_approval_gate_record.valid.json`
- `pm_bot/tests/fixtures/crypto_live/pmbot_crypto_stop_condition_mapping.valid.json`
- `pm_bot/tests/fixtures/crypto_live/pmbot_crypto_outcome_evidence_bundle.valid.json`
- `pm_bot/tests/fixtures/crypto_live/pmbot_crypto_paperlive_observation_replay.valid.json`
- `pm_bot/tests/fixtures/crypto_live/pmbot_crypto_paperlive_rehearsal_packet.valid.json`
- `pm_bot/simulated_decisions/samples/simulated_decision_replay_summary.fixture.json`
- `tests/test_codex_queue_pmbot_templates.py`
- `pm_bot/tests/test_crypto_validation_replay_bundle.py`

These inputs keep the crypto validation replay local-only, deterministic, descriptive, and pending operator review.

## Replay Sections

The fixture defines six deterministic replay sections:

- Bundle identity replay.
- Crypto readiness gate replay.
- Crypto evidence replay chain.
- Simulated decision static replay.
- Queue template validation replay.
- Validation command replay.

Every section names only local references and preserves the review status of the source records.

## Operator Review Boundary

Operators review whether the listed local references, static fixtures, replay sections, excluded path prefixes, and validation commands are present and internally consistent. This bundle does not approve a live run, choose a market, resolve an outcome, change review status, open external services, access credentials, access wallets, call endpoints, or change runtime, dispatcher, scheduler, worker, browser, or app-server wiring.

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
- This bundle is not execution approval and is not runtime input.

## Validation

Required local validation commands:

- `python -m compileall pm_bot tests`
- `pytest pm_bot/tests tests/test_codex_queue_pmbot_templates.py`
