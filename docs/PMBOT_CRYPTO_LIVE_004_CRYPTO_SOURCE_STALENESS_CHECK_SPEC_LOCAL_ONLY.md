# PMBOT Crypto Live 004 Crypto Source Staleness Check Spec Local Only

Task: `PMBOT-CRYPTO-LIVE-004-CRYPTO-SOURCE-STALENESS-CHECK-SPEC-LOCAL-ONLY`

Spec: `pmbot-crypto-source-staleness-check-spec-001`
Contract: `pmbot_crypto_source_staleness_check_spec.v1`
Run mode: `local_static_crypto_source_staleness_check_spec`
Operator review: `pending_operator_review`

## Purpose

This document registers the local PMBOT crypto source staleness check spec for operator review. The spec is deterministic and built from local files, local fixtures, and static samples only.

The spec maps each crypto source evidence link row to a descriptive staleness check row. It records local references, byte counts, SHA-256 digests, a fixed fixture reference timestamp, timestamp field paths, descriptive age windows, and pending review state only. It does not refresh crypto data, call services, approve execution, or produce forecast scoring, action guidance, or selection advice.

## Static Artifacts

The source evidence link map fixture is:

`pm_bot/source_quality/samples/crypto_source_evidence_link_map.fixture.json`

The generated static staleness spec and report samples are:

- `pm_bot/source_quality/samples/crypto_source_staleness_check_spec.fixture.json`
- `pm_bot/source_quality/samples/crypto_source_staleness_check_spec.fixture.md`

The implementation is:

`pm_bot/source_quality/crypto_source_staleness_check_spec.py`

## Source Basis

Reviewed local PMBOT artifacts:

- `docs/PMBOT_CRYPTO_LIVE_003_CRYPTO_SOURCE_EVIDENCE_LINK_MAP_LOCAL_ONLY.md`
- `pm_bot/source_quality/samples/crypto_source_evidence_link_map.fixture.json`
- `pm_bot/source_quality/samples/crypto_source_evidence_link_map.fixture.md`
- `pm_bot/tests/fixtures/crypto_live/pmbot_read_only_crypto_data_contract.valid.json`
- `pm_bot/tests/fixtures/crypto_market_class_capture/crypto_market_class_capture_template.valid.json`
- `pm_bot/tests/fixtures/crypto_operator_review_protocol/crypto_operator_review_protocol.valid.json`
- `pm_bot/tests/fixtures/crypto_paperlive_observation_ledger/crypto_paperlive_observation_ledger.valid.json`
- `pm_bot/source_quality/samples/crypto_source_quality_capture_surface.fixture.json`
- `pm_bot/tests/fixtures/crypto_paperlive_observation_ledger/static_crypto_reference_snapshot.valid.json`
- `pm_bot/tests/test_crypto_source_evidence_link_map.py`
- `tests/test_codex_queue_pmbot_templates.py`

These inputs keep the crypto staleness spec local-only, static, descriptive, paper-mode, and pending operator review.

## Spec Content

Each crypto source staleness check row records:

- source identity and label
- crypto source evidence link id
- source artifact reference, byte count, and digest
- source contract reference, byte count, and digest
- source inventory record reference, byte count, and digest
- timestamp field path selected by the fixed local rule
- fixed fixture reference timestamp
- descriptive age seconds
- fixed window label and maximum age seconds
- pending operator review checks

The spec uses `2026-05-09T01:30:00Z` as the fixed fixture reference timestamp. It does not use the system clock, timers, schedulers, workers, browser automation, or external services.

## Operator Review

Operators review:

- every crypto source evidence link row has exactly one local staleness check row
- every linked local reference stays under allowed static paths
- digests and byte counts correspond to the local artifacts
- timestamp field paths and descriptive age windows match local static artifact values
- every check row remains pending operator review
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
- This spec is not execution approval and is not runtime input.

## Validation

Required local validation commands:

- `python -m compileall pm_bot tests`
- `pytest pm_bot/tests tests/test_codex_queue_pmbot_templates.py`
