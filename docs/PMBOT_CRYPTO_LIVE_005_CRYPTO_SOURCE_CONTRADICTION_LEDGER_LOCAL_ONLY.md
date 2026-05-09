# PMBOT Crypto Live 005 Crypto Source Contradiction Ledger Local Only

Task: `PMBOT-CRYPTO-LIVE-005-CRYPTO-SOURCE-CONTRADICTION-LEDGER-LOCAL-ONLY`

Ledger: `pmbot-crypto-source-contradiction-ledger-001`
Contract: `pmbot_crypto_source_contradiction_ledger.v1`
Run mode: `local_static_crypto_source_contradiction_ledger`
Operator review: `pending_operator_review`

## Purpose

This document registers the local PMBOT crypto source contradiction ledger for operator review. The ledger is deterministic and built from local files, local fixtures, and static samples only.

The ledger maps selected crypto pilot source records into descriptive source-pair rows. It records local references, byte counts, SHA-256 digests, copied field checks, source key checks, and pending review state only. It does not refresh crypto data, call services, approve execution, or produce forecast scoring, action guidance, or selection advice.

## Static Artifacts

The source staleness spec fixture is:

`pm_bot/source_quality/samples/crypto_source_staleness_check_spec.fixture.json`

The generated static contradiction ledger and report samples are:

- `pm_bot/source_quality/samples/crypto_source_contradiction_ledger.fixture.json`
- `pm_bot/source_quality/samples/crypto_source_contradiction_ledger.fixture.md`

The implementation is:

`pm_bot/source_quality/crypto_source_contradiction_ledger.py`

## Source Basis

Reviewed local PMBOT artifacts:

- `docs/PMBOT_CRYPTO_LIVE_004_CRYPTO_SOURCE_STALENESS_CHECK_SPEC_LOCAL_ONLY.md`
- `pm_bot/source_quality/samples/crypto_source_staleness_check_spec.fixture.json`
- `pm_bot/source_quality/samples/crypto_source_staleness_check_spec.fixture.md`
- `pm_bot/tests/fixtures/crypto_live/pmbot_read_only_crypto_data_contract.valid.json`
- `pm_bot/tests/fixtures/crypto_market_class_capture/crypto_market_class_capture_template.valid.json`
- `pm_bot/tests/fixtures/crypto_operator_review_protocol/crypto_operator_review_protocol.valid.json`
- `pm_bot/tests/fixtures/crypto_paperlive_observation_ledger/crypto_paperlive_observation_ledger.valid.json`
- `pm_bot/tests/fixtures/crypto_paperlive_observation_ledger/static_crypto_reference_snapshot.valid.json`
- `pm_bot/source_quality/samples/crypto_source_quality_capture_surface.fixture.json`
- `pm_bot/tests/test_crypto_source_staleness_check_spec.py`
- `tests/test_codex_queue_pmbot_templates.py`

These inputs keep the crypto source contradiction ledger local-only, static, descriptive, paper-mode, and pending operator review.

## Ledger Content

Each crypto source contradiction row records:

- fixed left and right source ids
- source artifact reference, byte count, and digest for both sources
- selected nested record path for both sources
- source staleness check id and state for both sources
- source key comparisons
- mapped static field copy checks
- descriptive contradiction state
- pending operator review checks

The fixed source pairs are:

- read-only crypto contract static sample to static reference snapshot
- crypto market class capture sample to crypto operator review record
- crypto operator review record to crypto paperlive observation record
- crypto paperlive observation record to static reference snapshot

## Operator Review

Operators review:

- each crypto source pair resolves to local static artifacts and expected nested records
- every linked local reference stays under allowed static paths
- digests and byte counts correspond to the local artifacts
- copied source keys and mapped static fields match source records or remain pending review when they differ
- every ledger row remains pending operator review
- sensitive paths, credential stores, wallets, signing material, endpoint calls, runtime wiring, browser automation, workers, and timed automation remain outside scope
- validation output is captured before any later readiness status change

## Safety

- Local files, local fixtures, and static samples only.
- No network calls.
- No LLM provider calls.
- No external market API calls.
- No authenticated endpoint use.
- No credential, wallet, private-key, seed, signing, order, payment, or transaction path access.
- No runtime, dispatcher, scheduler, worker, browser, resident process, timed automation, or app-server wiring.
- No forecast scoring, action guidance, market ranking, numeric prediction metric, threshold comparison output, selection advice, or trade instruction output.
- This ledger is not execution approval and is not runtime input.

## Validation

Required local validation commands:

- `python -m compileall pm_bot tests`
- `pytest pm_bot/tests tests/test_codex_queue_pmbot_templates.py`
