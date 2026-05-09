# PMBOT Crypto Live 007 Crypto Paperlive Observation Replay Local Only

Task: `PMBOT-CRYPTO-LIVE-007-CRYPTO-PAPERLIVE-OBSERVATION-REPLAY-LOCAL-ONLY`

Replay: `pmbot-crypto-paperlive-observation-replay-001`
Contract: `pmbot_crypto_paperlive_observation_replay.v1`
Run mode: `local_static_crypto_paperlive_observation_replay`
Operator review: `pending_operator_review`

## Purpose

This document registers the local PMBOT crypto pilot paperlive observation replay for operator review. The replay is deterministic and built from local files, local fixtures, and static samples only.

The replay reconstructs one static observation-review chain from the crypto paperlive rehearsal packet, the crypto paperlive observation ledger, and the local static reference snapshot. It records local references, byte counts, SHA-256 digests, copied descriptive field checks, value-retention policy, and pending review state only. It does not refresh crypto data, call services, approve execution, compare thresholds, or produce forecast scoring, action guidance, or selection advice.

## Static Fixture

The local observation replay fixture is:

`pm_bot/tests/fixtures/crypto_live/pmbot_crypto_paperlive_observation_replay.valid.json`

The fixture records fixed replay fields, one static replay record, local source artifact references, operator review checks, required validation commands, summary counts, and closed safety boundaries.

## Source Basis

Reviewed local PMBOT artifacts:

- `docs/PMBOT_CRYPTO_LIVE_006_CRYPTO_PAPERLIVE_REHEARSAL_PACKET_LOCAL_ONLY.md`
- `pm_bot/tests/fixtures/crypto_live/pmbot_crypto_paperlive_rehearsal_packet.valid.json`
- `docs/PMBOT_CRYPTO_PILOT_003_CRYPTO_PAPERLIVE_OBSERVATION_LEDGER_LOCAL_ONLY.md`
- `pm_bot/tests/fixtures/crypto_paperlive_observation_ledger/crypto_paperlive_observation_ledger.valid.json`
- `pm_bot/tests/fixtures/crypto_paperlive_observation_ledger/static_crypto_reference_snapshot.valid.json`
- `pm_bot/tests/fixtures/crypto_market_class_capture/crypto_market_class_capture_template.valid.json`
- `pm_bot/tests/fixtures/crypto_operator_review_protocol/crypto_operator_review_protocol.valid.json`
- `tests/test_codex_queue_pmbot_templates.py`

These inputs keep the crypto paperlive observation replay local-only, static, descriptive, paper-mode, and pending operator review.

## Replay Content

Each crypto paperlive observation replay record keeps these fields in a fixed contract:

- `replay_record_id`
- `source_packet_record_id`
- `source_observation_record_id`
- `source_review_record_id`
- `source_capture_record_id`
- `market_class`
- `market_slug`
- `market_title`
- `asset_symbol`
- `asset_name`
- `quote_currency`
- `metric_type`
- `deadline_utc`
- `local_rehearsal_packet_reference`
- `local_observation_fixture_reference`
- `local_snapshot_reference`
- `replay_state`
- `operator_review_status`
- `static_copy_checks`
- `value_field_policy`

The replay may copy descriptive labels, market text, static timestamps, source record identifiers, and local paths. Numeric source values remain in the referenced local fixtures and are not copied into this replay.

## Operator Review

Operators review:

- every local reference resolves to an expected static file
- byte counts and SHA-256 digests match the local files named in the replay
- the replay record points to the static rehearsal packet record and paperlive observation row
- copied descriptive fields match the local source records
- value fields remain in source artifacts rather than this replay
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
- This replay is not execution approval and is not runtime input.

## Validation

Required local validation commands:

- `python -m compileall pm_bot tests`
- `pytest pm_bot/tests tests/test_codex_queue_pmbot_templates.py`
