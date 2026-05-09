# PMBOT Crypto Live 006 Crypto Paperlive Rehearsal Packet Local Only

Task: `PMBOT-CRYPTO-LIVE-006-CRYPTO-PAPERLIVE-REHEARSAL-PACKET-LOCAL-ONLY`

Packet: `pmbot-crypto-paperlive-rehearsal-packet-001`
Contract: `pmbot_crypto_paperlive_rehearsal_packet.v1`
Run mode: `local_static_crypto_paperlive_rehearsal_packet`
Operator review: `pending_operator_review`

## Purpose

This document registers the local PMBOT crypto pilot paperlive rehearsal packet for operator review. The packet is deterministic and built from local files, local fixtures, and static samples only.

The packet links one static crypto paperlive observation row to its local source review record, source fixture paths, and crypto live readiness documentation. It records local references, byte counts, SHA-256 digests, copied text checks, value-retention policy, and pending review state only. It does not refresh crypto data, call services, approve execution, compare thresholds, or produce forecast scoring, action guidance, or selection advice.

## Static Fixture

The local rehearsal packet fixture is:

`pm_bot/tests/fixtures/crypto_live/pmbot_crypto_paperlive_rehearsal_packet.valid.json`

The fixture records fixed packet fields, one static rehearsal record, local source artifact references, operator review checks, required validation commands, summary counts, and closed safety boundaries.

## Source Basis

Reviewed local PMBOT artifacts:

- `docs/PMBOT_CRYPTO_LIVE_001_READ_ONLY_CRYPTO_DATA_CONTRACT_LOCAL_ONLY.md`
- `docs/PMBOT_CRYPTO_LIVE_002_CRYPTO_LIVE_DATA_SOURCE_INVENTORY_LOCAL_ONLY.md`
- `docs/PMBOT_CRYPTO_LIVE_003_CRYPTO_SOURCE_EVIDENCE_LINK_MAP_LOCAL_ONLY.md`
- `docs/PMBOT_CRYPTO_LIVE_004_CRYPTO_SOURCE_STALENESS_CHECK_SPEC_LOCAL_ONLY.md`
- `docs/PMBOT_CRYPTO_LIVE_005_CRYPTO_SOURCE_CONTRADICTION_LEDGER_LOCAL_ONLY.md`
- `pm_bot/tests/fixtures/crypto_live/pmbot_read_only_crypto_data_contract.valid.json`
- `pm_bot/tests/fixtures/crypto_live/pmbot_crypto_live_data_source_inventory.valid.json`
- `pm_bot/tests/fixtures/crypto_market_class_capture/crypto_market_class_capture_template.valid.json`
- `pm_bot/tests/fixtures/crypto_operator_review_protocol/crypto_operator_review_protocol.valid.json`
- `pm_bot/tests/fixtures/crypto_paperlive_observation_ledger/crypto_paperlive_observation_ledger.valid.json`
- `pm_bot/tests/fixtures/crypto_paperlive_observation_ledger/static_crypto_reference_snapshot.valid.json`
- `tests/test_codex_queue_pmbot_templates.py`

These inputs keep the crypto paperlive rehearsal packet local-only, static, descriptive, paper-mode, and pending operator review.

## Packet Content

Each crypto paperlive rehearsal record keeps these fields in a fixed contract:

- `asset_name`
- `asset_symbol`
- `deadline_utc`
- `local_observation_fixture_reference`
- `local_snapshot_reference`
- `market_class`
- `market_slug`
- `market_title`
- `metric_type`
- `observation_record_id`
- `operator_review_status`
- `packet_record_id`
- `packet_state`
- `quote_currency`
- `reference_field_policy`
- `source_capture_record_id`
- `source_review_record_id`
- `static_copy_checks`
- `value_fields_retained_in_source_artifacts`

The packet may copy descriptive labels, market text, static timestamps, source record identifiers, and local paths. Numeric source values remain in the referenced local fixtures and are not copied into this packet.

## Operator Review

Operators review:

- every local reference resolves to an expected static file
- byte counts and SHA-256 digests match the local files named in the packet
- the packet record points to the static crypto operator review record and paperlive observation record
- copied descriptive fields match the local source records
- value fields remain in source artifacts rather than this packet
- every review row remains pending operator review
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
- This packet is not execution approval and is not runtime input.

## Validation

Required local validation commands:

- `python -m compileall pm_bot tests`
- `pytest pm_bot/tests tests/test_codex_queue_pmbot_templates.py`
