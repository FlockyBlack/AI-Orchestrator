# PMBOT Crypto Live 017 Crypto Morning Review Card Local Only

Task: `PMBOT-CRYPTO-LIVE-017-CRYPTO-MORNING-REVIEW-CARD-LOCAL-ONLY`

Card: `pmbot-crypto-morning-review-card-001`
Contract: `pmbot_crypto_morning_review_card.v1`
Run mode: `local_static_crypto_morning_review_card`
Operator review: `pending_operator_review`

## Purpose

This document registers a deterministic local PMBOT crypto pilot morning review card for operator review. The card is built from local files, local fixtures, and static samples only.

The card restates local dashboard, crypto source, rehearsal, gate, validation, and safety review coverage without refreshing crypto data, calling external services, approving execution, resolving outcomes, mutating runtime state, or producing forecast scoring, action guidance, or selection advice.

## Static Artifacts

The local crypto morning review card artifacts are:

- Static card sample: `pm_bot/dashboard/samples/pmbot_crypto_morning_review_card.fixture.json`
- Static operator report sample: `pm_bot/dashboard/samples/pmbot_crypto_morning_review_card.fixture.md`
- Contract test: `pm_bot/tests/test_crypto_morning_review_card.py`

The JSON sample records fixed card sections, local source artifacts, operator review checks, validation command records, summary counts, and closed safety boundaries. The Markdown sample renders the same static card for human review.

## Source Basis

Reviewed local PMBOT artifacts:

- `pm_bot/dashboard/samples/pmbot_crypto_dashboard_readiness_summary.fixture.json`
- `pm_bot/dashboard/samples/pmbot_crypto_dashboard_readiness_summary.fixture.md`
- `docs/PMBOT_CRYPTO_LIVE_001_READ_ONLY_CRYPTO_DATA_CONTRACT_LOCAL_ONLY.md`
- `docs/PMBOT_CRYPTO_LIVE_002_CRYPTO_LIVE_DATA_SOURCE_INVENTORY_LOCAL_ONLY.md`
- `docs/PMBOT_CRYPTO_LIVE_003_CRYPTO_SOURCE_EVIDENCE_LINK_MAP_LOCAL_ONLY.md`
- `docs/PMBOT_CRYPTO_LIVE_004_CRYPTO_SOURCE_STALENESS_CHECK_SPEC_LOCAL_ONLY.md`
- `docs/PMBOT_CRYPTO_LIVE_005_CRYPTO_SOURCE_CONTRADICTION_LEDGER_LOCAL_ONLY.md`
- `pm_bot/tests/fixtures/crypto_live/pmbot_crypto_paperlive_rehearsal_packet.valid.json`
- `pm_bot/tests/fixtures/crypto_live/pmbot_crypto_paperlive_observation_replay.valid.json`
- `pm_bot/tests/fixtures/crypto_live/pmbot_crypto_outcome_evidence_bundle.valid.json`
- `pm_bot/tests/fixtures/crypto_live/pmbot_crypto_operator_approval_gate_record.valid.json`
- `pm_bot/tests/fixtures/crypto_live/pmbot_crypto_stop_condition_mapping.valid.json`
- `pm_bot/tests/fixtures/crypto_live/pmbot_crypto_supervised_live_gap_matrix.valid.json`
- `pm_bot/tests/fixtures/crypto_live/pmbot_crypto_validation_replay_bundle.valid.json`
- `pm_bot/tests/fixtures/crypto_live/pmbot_crypto_ci_safe_validation_subset.valid.json`
- `pm_bot/tests/fixtures/crypto_live/pmbot_crypto_forbidden_language_regression.valid.json`
- `pm_bot/tests/fixtures/crypto_live/pmbot_crypto_sensitive_path_exclusion_audit.valid.json`
- `tests/test_codex_queue_pmbot_templates.py`

These inputs keep the crypto morning review card local-only, deterministic, descriptive, and pending operator review.

## Card Sections

The static card defines six sections:

- Crypto dashboard readiness snapshot.
- Crypto source review snapshot.
- Crypto rehearsal review snapshot.
- Crypto gate review snapshot.
- Crypto validation review snapshot.
- Crypto safety review snapshot.

Every section names one primary local reference, a fixed source artifact set, descriptive counts, and a `pending_operator_review` status.

## Operator Review Boundary

Operators review whether the listed dashboard samples, crypto fixtures, local documentation references, validation commands, summary counts, and safety boundaries are present and internally consistent. This card does not approve a live run, choose a market, resolve an outcome, change review status, open external services, access credentials, access wallets, call endpoints, or change runtime, dispatcher, scheduler, worker, browser, or app-server wiring.

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
- This card is not execution approval and is not runtime input.

## Validation

Required local validation commands:

- `python -m compileall pm_bot tests`
- `pytest pm_bot/tests tests/test_codex_queue_pmbot_templates.py`
