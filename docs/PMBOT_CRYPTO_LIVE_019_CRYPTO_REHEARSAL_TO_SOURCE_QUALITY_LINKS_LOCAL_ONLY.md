# PMBOT Crypto Live 019 Crypto Rehearsal To Source Quality Links Local Only

Task: `PMBOT-CRYPTO-LIVE-019-CRYPTO-REHEARSAL-TO-SOURCE-QUALITY-LINKS-LOCAL-ONLY`

Link set: `pmbot-crypto-rehearsal-source-quality-links-001`
Contract: `pmbot_crypto_rehearsal_source_quality_links.v1`
Run mode: `local_static_crypto_rehearsal_source_quality_links`
Operator review: `pending_operator_review`

## Purpose

This document registers deterministic local PMBOT crypto pilot links between the paperlive rehearsal packet and source quality records for operator review. The link set is built from local files, local fixtures, and static samples only.

The link set connects the static rehearsal packet record to local source quality capture rows, source evidence link rows, source staleness check rows, and source contradiction review rows. It records local references, byte counts, SHA-256 digests, source record identifiers, and pending review state only. It does not refresh crypto data, call services, approve execution, compare thresholds, resolve outcomes, or produce forecast scoring, action guidance, or selection advice.

## Static Artifacts

The local rehearsal to source quality link artifacts are:

- Static JSON sample: `pm_bot/source_quality/samples/crypto_rehearsal_source_quality_links.fixture.json`
- Static operator report sample: `pm_bot/source_quality/samples/crypto_rehearsal_source_quality_links.fixture.md`
- Builder and validator: `pm_bot/source_quality/crypto_rehearsal_source_quality_links.py`
- Contract test: `pm_bot/tests/test_crypto_rehearsal_source_quality_links.py`

The JSON sample records fixed link fields, one static rehearsal packet reference, four source quality artifact references, four rehearsal-to-source-quality link rows, operator review steps, required validation commands, summary counts, and closed safety boundaries.

## Source Basis

Reviewed local PMBOT artifacts:

- `docs/PMBOT_CRYPTO_LIVE_006_CRYPTO_PAPERLIVE_REHEARSAL_PACKET_LOCAL_ONLY.md`
- `pm_bot/tests/fixtures/crypto_live/pmbot_crypto_paperlive_rehearsal_packet.valid.json`
- `pm_bot/source_quality/samples/crypto_source_quality_capture_surface.fixture.json`
- `pm_bot/source_quality/samples/crypto_source_evidence_link_map.fixture.json`
- `pm_bot/source_quality/samples/crypto_source_staleness_check_spec.fixture.json`
- `pm_bot/source_quality/samples/crypto_source_contradiction_ledger.fixture.json`
- `docs/PMBOT_CRYPTO_LIVE_003_CRYPTO_SOURCE_EVIDENCE_LINK_MAP_LOCAL_ONLY.md`
- `docs/PMBOT_CRYPTO_LIVE_004_CRYPTO_SOURCE_STALENESS_CHECK_SPEC_LOCAL_ONLY.md`
- `docs/PMBOT_CRYPTO_LIVE_005_CRYPTO_SOURCE_CONTRADICTION_LEDGER_LOCAL_ONLY.md`
- `docs/PMBOT_CRYPTO_PILOT_004_CRYPTO_SOURCE_QUALITY_CAPTURE_SURFACE_LOCAL_ONLY.md`

These inputs keep the crypto rehearsal source quality links local-only, deterministic, descriptive, paper-mode, and pending operator review.

## Link Coverage

The static link set maps these rehearsal source fields:

- `source_capture_record_id` to market capture source quality records.
- `source_review_record_id` to operator review protocol source quality records.
- `observation_record_id` to paperlive observation ledger source quality records.
- `local_snapshot_reference` to the static crypto reference snapshot source quality records.

Each link row names the matching source quality capture record, source evidence link, source staleness check, and source contradiction review row or rows. Numeric source values remain in referenced local fixtures and are not copied into this link set.

## Operator Review

Operators review:

- the rehearsal packet fixture and documentation resolve to expected local files
- each link row points to the intended fixed rehearsal source field
- each source quality record identifier exists in the named local source quality artifact
- source quality artifact byte counts and SHA-256 digests match current local bytes
- source values remain in referenced artifacts rather than this link set
- every link and source quality artifact remains pending operator review
- sensitive paths, credential stores, wallets, signing material, endpoint calls, runtime wiring, browser automation, workers, and timed automation remain outside scope
- validation output is captured before any later readiness status change

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
- This link set is not execution approval and is not runtime input.

## Validation

Required local validation commands:

- `python -m compileall pm_bot tests`
- `pytest pm_bot/tests tests/test_codex_queue_pmbot_templates.py`
