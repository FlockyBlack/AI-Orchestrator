# PMBOT Crypto Live 003 Crypto Source Evidence Link Map Local Only

Task: `PMBOT-CRYPTO-LIVE-003-CRYPTO-SOURCE-EVIDENCE-LINK-MAP-LOCAL-ONLY`

Map: `pmbot-crypto-source-evidence-link-map-001`
Contract: `pmbot_crypto_source_evidence_link_map.v1`
Run mode: `local_static_crypto_source_evidence_link_map`
Operator review: `pending_operator_review`

## Purpose

This document registers the local PMBOT crypto source evidence link map for operator review. The map is deterministic and built from local files, local fixtures, and static samples only.

The map links each crypto live data source inventory record to its local source artifact, the source inventory row, and the applicable source contract documentation. It records local references, byte counts, SHA-256 digests, and pending review state only. It does not copy crypto values, refresh crypto data, call services, approve execution, or produce forecast scoring, action guidance, or selection advice.

## Static Artifacts

The source inventory fixture is:

`pm_bot/tests/fixtures/crypto_live/pmbot_crypto_live_data_source_inventory.valid.json`

The generated static link map and report samples are:

- `pm_bot/source_quality/samples/crypto_source_evidence_link_map.fixture.json`
- `pm_bot/source_quality/samples/crypto_source_evidence_link_map.fixture.md`

The implementation is:

`pm_bot/source_quality/crypto_source_evidence_link_map.py`

## Source Basis

Reviewed local PMBOT artifacts:

- `docs/PMBOT_CRYPTO_LIVE_002_CRYPTO_LIVE_DATA_SOURCE_INVENTORY_LOCAL_ONLY.md`
- `docs/PMBOT_CRYPTO_LIVE_001_READ_ONLY_CRYPTO_DATA_CONTRACT_LOCAL_ONLY.md`
- `docs/PMBOT_CRYPTO_PILOT_001_CRYPTO_MARKET_CLASS_CAPTURE_TEMPLATE_LOCAL_ONLY.md`
- `docs/PMBOT_CRYPTO_PILOT_002_CRYPTO_OPERATOR_REVIEW_PROTOCOL_LOCAL_ONLY.md`
- `docs/PMBOT_CRYPTO_PILOT_003_CRYPTO_PAPERLIVE_OBSERVATION_LEDGER_LOCAL_ONLY.md`
- `docs/PMBOT_CRYPTO_PILOT_004_CRYPTO_SOURCE_QUALITY_CAPTURE_SURFACE_LOCAL_ONLY.md`
- `pm_bot/tests/fixtures/crypto_live/pmbot_read_only_crypto_data_contract.valid.json`
- `pm_bot/tests/fixtures/crypto_market_class_capture/crypto_market_class_capture_template.valid.json`
- `pm_bot/tests/fixtures/crypto_operator_review_protocol/crypto_operator_review_protocol.valid.json`
- `pm_bot/tests/fixtures/crypto_paperlive_observation_ledger/crypto_paperlive_observation_ledger.valid.json`
- `pm_bot/tests/fixtures/crypto_paperlive_observation_ledger/static_crypto_reference_snapshot.valid.json`
- `pm_bot/source_quality/samples/crypto_source_quality_capture_surface.fixture.json`
- `tests/test_codex_queue_pmbot_templates.py`

These inputs keep the link map local-only, static, descriptive, paper-mode, and pending operator review.

## Link Map Content

Each crypto source evidence link row records:

- source identity and label
- crypto live inventory record id
- local source artifact reference, byte count, and digest
- source contract documentation reference, byte count, and digest
- source inventory fixture reference, byte count, and digest
- known limitations
- pending operator review checks

The link map intentionally avoids copying artifact field values. A human operator can use the local references and digests to review the linked artifacts directly.

## Operator Review

Operators review:

- every crypto source inventory row has exactly one local link row
- every linked local reference stays under allowed static paths
- digests and byte counts correspond to the local artifacts
- source artifact references match the crypto live inventory rows
- source contract documentation matches the crypto live inventory contract references
- every link row remains pending operator review
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
- This link map is not execution approval and is not runtime input.

## Validation

Required local validation commands:

- `python -m compileall pm_bot tests`
- `pytest pm_bot/tests tests/test_codex_queue_pmbot_templates.py`
