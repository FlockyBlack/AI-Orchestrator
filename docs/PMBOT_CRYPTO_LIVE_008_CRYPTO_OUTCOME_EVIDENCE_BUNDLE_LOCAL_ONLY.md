# PMBOT Crypto Live 008 Crypto Outcome Evidence Bundle Local Only

Task: `PMBOT-CRYPTO-LIVE-008-CRYPTO-OUTCOME-EVIDENCE-BUNDLE-LOCAL-ONLY`

Bundle: `pmbot-crypto-outcome-evidence-bundle-001`
Contract: `pmbot_crypto_outcome_evidence_bundle.v1`
Run mode: `local_static_crypto_outcome_evidence_bundle`
Operator review: `pending_operator_review`

## Purpose

This document registers the local PMBOT crypto pilot outcome evidence bundle for operator review. The bundle is deterministic and built from local files, local fixtures, and static samples only.

The bundle links the static crypto paperlive observation replay to its rehearsal packet, observation ledger, static reference snapshot, and source quality records. It records local references, byte counts, SHA-256 digests, copied descriptive field checks, value-retention policy, and pending review state only. It does not refresh crypto data, call services, approve execution, compare thresholds, resolve an outcome, or produce forecast scoring, action guidance, or selection advice.

## Static Fixture

The local outcome evidence bundle fixture is:

`pm_bot/tests/fixtures/crypto_live/pmbot_crypto_outcome_evidence_bundle.valid.json`

The fixture records fixed bundle fields, one static outcome evidence record, local source artifact references, operator review checks, required validation commands, summary counts, and closed safety boundaries.

## Source Basis

Reviewed local PMBOT artifacts:

- `docs/PMBOT_CRYPTO_LIVE_007_CRYPTO_PAPERLIVE_OBSERVATION_REPLAY_LOCAL_ONLY.md`
- `pm_bot/tests/fixtures/crypto_live/pmbot_crypto_paperlive_observation_replay.valid.json`
- `docs/PMBOT_CRYPTO_LIVE_006_CRYPTO_PAPERLIVE_REHEARSAL_PACKET_LOCAL_ONLY.md`
- `pm_bot/tests/fixtures/crypto_live/pmbot_crypto_paperlive_rehearsal_packet.valid.json`
- `docs/PMBOT_CRYPTO_PILOT_003_CRYPTO_PAPERLIVE_OBSERVATION_LEDGER_LOCAL_ONLY.md`
- `pm_bot/tests/fixtures/crypto_paperlive_observation_ledger/crypto_paperlive_observation_ledger.valid.json`
- `pm_bot/tests/fixtures/crypto_paperlive_observation_ledger/static_crypto_reference_snapshot.valid.json`
- `pm_bot/source_quality/samples/crypto_source_evidence_link_map.fixture.json`
- `pm_bot/source_quality/samples/crypto_source_staleness_check_spec.fixture.json`
- `pm_bot/source_quality/samples/crypto_source_contradiction_ledger.fixture.json`
- `tests/test_codex_queue_pmbot_templates.py`

These inputs keep the crypto outcome evidence bundle local-only, static, descriptive, paper-mode, unresolved, and pending operator review.

## Bundle Content

Each crypto outcome evidence record keeps these fields in a fixed contract:

- `record_id`
- `source_replay_record_id`
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
- `local_replay_fixture_reference`
- `local_rehearsal_packet_reference`
- `local_observation_fixture_reference`
- `local_snapshot_reference`
- `evidence_state`
- `operator_review_status`
- `static_copy_checks`
- `value_field_policy`

The bundle may copy descriptive labels, market text, static timestamps, source record identifiers, and local paths. Numeric source values remain in referenced local fixtures and are not copied into this bundle.

## Operator Review

Operators review:

- every local reference resolves to an expected static file
- byte counts and SHA-256 digests match the local files named in the bundle
- the bundle record points to the static replay, rehearsal packet, observation, review, and capture records
- copied descriptive fields match the local replay source record
- value fields remain in source artifacts rather than this bundle
- the outcome state remains unresolved and pending operator review
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
- No forecast scoring, action guidance, market ranking, numeric prediction metric, threshold comparison output, outcome resolution, selection advice, or trade instruction output.
- This bundle is not execution approval and is not runtime input.

## Validation

Required local validation commands:

- `python -m compileall pm_bot tests`
- `pytest pm_bot/tests tests/test_codex_queue_pmbot_templates.py`
