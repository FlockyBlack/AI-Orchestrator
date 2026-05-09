# PMBOT Crypto Live 010 Crypto Stop Condition Mapping Local Only

Task: `PMBOT-CRYPTO-LIVE-010-CRYPTO-STOP-CONDITION-MAPPING-LOCAL-ONLY`

Mapping: `pmbot-crypto-stop-condition-mapping-001`
Contract: `pmbot_crypto_stop_condition_mapping.v1`
Run mode: `local_static_crypto_stop_condition_mapping`
Operator review: `pending_operator_review`

## Purpose

This document registers the local PMBOT crypto pilot stop condition mapping for supervised readiness review. The mapping is deterministic and built from local files, local fixtures, and static samples only.

The mapping links fixed local stop condition rows to crypto live gate rows, source artifacts, required manual record fields, closed safety boundaries, and validation commands. It does not refresh crypto data, call services, approve execution, compare thresholds, resolve an outcome, or produce forecast scoring, action guidance, or selection advice.

## Static Fixture

The local stop condition mapping fixture is:

`pm_bot/tests/fixtures/crypto_live/pmbot_crypto_stop_condition_mapping.valid.json`

The fixture records fixed condition rows, mapped operator gate identifiers, local trigger evidence references, required manual record fields, operator review checks, summary counts, and closed safety boundaries.

## Source Basis

Reviewed local PMBOT artifacts:

- `docs/PMBOT_CRYPTO_LIVE_001_READ_ONLY_CRYPTO_DATA_CONTRACT_LOCAL_ONLY.md`
- `docs/PMBOT_CRYPTO_LIVE_002_CRYPTO_LIVE_DATA_SOURCE_INVENTORY_LOCAL_ONLY.md`
- `docs/PMBOT_CRYPTO_LIVE_003_CRYPTO_SOURCE_EVIDENCE_LINK_MAP_LOCAL_ONLY.md`
- `docs/PMBOT_CRYPTO_LIVE_004_CRYPTO_SOURCE_STALENESS_CHECK_SPEC_LOCAL_ONLY.md`
- `docs/PMBOT_CRYPTO_LIVE_005_CRYPTO_SOURCE_CONTRADICTION_LEDGER_LOCAL_ONLY.md`
- `docs/PMBOT_CRYPTO_LIVE_006_CRYPTO_PAPERLIVE_REHEARSAL_PACKET_LOCAL_ONLY.md`
- `pm_bot/tests/fixtures/crypto_live/pmbot_crypto_paperlive_rehearsal_packet.valid.json`
- `docs/PMBOT_CRYPTO_LIVE_007_CRYPTO_PAPERLIVE_OBSERVATION_REPLAY_LOCAL_ONLY.md`
- `pm_bot/tests/fixtures/crypto_live/pmbot_crypto_paperlive_observation_replay.valid.json`
- `docs/PMBOT_CRYPTO_LIVE_008_CRYPTO_OUTCOME_EVIDENCE_BUNDLE_LOCAL_ONLY.md`
- `pm_bot/tests/fixtures/crypto_live/pmbot_crypto_outcome_evidence_bundle.valid.json`
- `docs/PMBOT_CRYPTO_LIVE_009_CRYPTO_OPERATOR_APPROVAL_GATE_RECORD_LOCAL_ONLY.md`
- `pm_bot/tests/fixtures/crypto_live/pmbot_crypto_operator_approval_gate_record.valid.json`
- `tests/test_codex_queue_pmbot_templates.py`

These inputs keep the crypto stop condition mapping local-only, static, descriptive, paper-mode, unresolved, and pending operator review.

## Mapping Content

Each crypto stop condition row keeps these fields in a fixed contract:

- `condition_class`
- `condition_id`
- `condition_label`
- `excluded_operations`
- `manual_record_required`
- `mapped_gate_id`
- `mapped_source_artifact_id`
- `operator_review_status`
- `required_operator_record`
- `stop_state`
- `trigger_evidence_reference`
- `trigger_source`

The fixture maps nine fixed stop conditions:

- operator manual stop request
- crypto local artifact boundary breach
- crypto forbidden operation request detected
- crypto validation command failed
- crypto source record label dispute
- crypto rehearsal record mismatch
- crypto observation replay chain mismatch
- crypto outcome state changed without record
- crypto operator gate record missing

Every condition row remains `pending_operator_review`, requires a manual record, and maps to a blocked or stopped local state.

## Operator Review

Operators review:

- every condition row has exactly one local static trigger reference
- every mapped gate identifier is present in the crypto operator approval gate record
- every mapped source artifact resolves to an expected local file
- required manual record fields are sufficient to record condition id, timestamp, reviewer, evidence, prior state, new state, review state, and unresolved blockers
- every condition row keeps the same closed excluded operations list
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
- This mapping is not execution approval and is not runtime input.

## Validation

Required local validation commands:

- `python -m compileall pm_bot tests`
- `pytest pm_bot/tests tests/test_codex_queue_pmbot_templates.py`
