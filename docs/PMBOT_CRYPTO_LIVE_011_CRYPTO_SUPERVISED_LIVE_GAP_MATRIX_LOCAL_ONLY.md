# PMBOT Crypto Live 011 Crypto Supervised Live Gap Matrix Local Only

Task: `PMBOT-CRYPTO-LIVE-011-CRYPTO-SUPERVISED-LIVE-GAP-MATRIX-LOCAL-ONLY`

Matrix: `pmbot-crypto-supervised-live-gap-matrix-001`
Contract: `pmbot_crypto_supervised_live_gap_matrix.v1`
Run mode: `local_static_crypto_supervised_live_gap_matrix`
Operator review: `pending_operator_review`

## Purpose

This document registers the local PMBOT crypto pilot supervised live gap matrix for operator readiness review. The matrix is deterministic and built from local files, local fixtures, and static samples only.

The matrix connects fixed local crypto readiness rows to their current local state, the remaining supervised review gap, the local reference to inspect, the mapped source artifact, and the required human review evidence. It does not refresh crypto data, call services, approve execution, compare thresholds, resolve an outcome, or produce forecast scoring, action guidance, or selection advice.

## Static Fixture

The local crypto supervised live gap matrix fixture is:

`pm_bot/tests/fixtures/crypto_live/pmbot_crypto_supervised_live_gap_matrix.valid.json`

The fixture records fixed gap rows, source artifact references, operator review checks, required validation commands, summary counts, and closed safety boundaries.

## Source Basis

Reviewed local PMBOT artifacts:

- `docs/PMBOT_CRYPTO_LIVE_001_READ_ONLY_CRYPTO_DATA_CONTRACT_LOCAL_ONLY.md`
- `pm_bot/tests/fixtures/crypto_live/pmbot_read_only_crypto_data_contract.valid.json`
- `docs/PMBOT_CRYPTO_LIVE_002_CRYPTO_LIVE_DATA_SOURCE_INVENTORY_LOCAL_ONLY.md`
- `pm_bot/tests/fixtures/crypto_live/pmbot_crypto_live_data_source_inventory.valid.json`
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
- `docs/PMBOT_CRYPTO_LIVE_010_CRYPTO_STOP_CONDITION_MAPPING_LOCAL_ONLY.md`
- `pm_bot/tests/fixtures/crypto_live/pmbot_crypto_stop_condition_mapping.valid.json`
- `tests/test_codex_queue_pmbot_templates.py`

These inputs keep the crypto supervised live gap matrix local-only, static, descriptive, paper-mode, unresolved, and pending operator review.

## Gap Matrix

| Gate ID | Current Local State | Supervised Live Gap | Local Evidence Reference | Required Review Evidence |
| --- | --- | --- | --- | --- |
| `crypto_read_only_contract_gate` | Read-only crypto contract exists as a local static artifact with closed endpoint and value transformation boundaries. | Human review must confirm the contract remains local static material and non-execution input. | `docs/PMBOT_CRYPTO_LIVE_001_READ_ONLY_CRYPTO_DATA_CONTRACT_LOCAL_ONLY.md` | Review record naming contract artifact, reviewer, timestamp, and unresolved blockers. |
| `crypto_live_source_inventory_gate` | Crypto source inventory exists as a local static record with no source refresh in this task. | Human review must confirm every listed source row is static and locally referenced. | `docs/PMBOT_CRYPTO_LIVE_002_CRYPTO_LIVE_DATA_SOURCE_INVENTORY_LOCAL_ONLY.md` | Review record naming source rows, fixture references, excluded paths, and disputes. |
| `crypto_source_evidence_link_gate` | Crypto source evidence links are represented by local docs and fixtures only. | Human review must confirm each evidence link resolves to an allowed local artifact. | `docs/PMBOT_CRYPTO_LIVE_003_CRYPTO_SOURCE_EVIDENCE_LINK_MAP_LOCAL_ONLY.md` | Review record confirming path coverage and unresolved link gaps. |
| `crypto_source_staleness_gate` | Crypto source staleness checks remain a static local spec and do not refresh data. | Human review must confirm staleness fields are descriptive and no endpoint check occurred. | `docs/PMBOT_CRYPTO_LIVE_004_CRYPTO_SOURCE_STALENESS_CHECK_SPEC_LOCAL_ONLY.md` | Review record confirming static timestamp review and no service access. |
| `crypto_source_contradiction_gate` | Crypto contradiction rows remain local source review records. | Human review must confirm contradiction labels remain unresolved until a separate record closes them. | `docs/PMBOT_CRYPTO_LIVE_005_CRYPTO_SOURCE_CONTRADICTION_LEDGER_LOCAL_ONLY.md` | Review record naming row identifiers, local paths, and unresolved disputes. |
| `crypto_paperlive_rehearsal_gate` | Crypto paperlive rehearsal packet is a local static packet. | Human review must confirm packet fields remain descriptive and paper-only. | `docs/PMBOT_CRYPTO_LIVE_006_CRYPTO_PAPERLIVE_REHEARSAL_PACKET_LOCAL_ONLY.md` | Review record confirming packet field coverage and paper-only state. |
| `crypto_observation_replay_gate` | Crypto observation replay is a local static replay chain. | Human review must confirm replay links are copied from static local records and remain unresolved. | `docs/PMBOT_CRYPTO_LIVE_007_CRYPTO_PAPERLIVE_OBSERVATION_REPLAY_LOCAL_ONLY.md` | Review record confirming replay chain identifiers and unresolved state. |
| `crypto_outcome_evidence_gate` | Crypto outcome evidence bundle keeps numeric source values in referenced local artifacts. | Human review must confirm bundle evidence does not resolve or compare outcome state. | `docs/PMBOT_CRYPTO_LIVE_008_CRYPTO_OUTCOME_EVIDENCE_BUNDLE_LOCAL_ONLY.md` | Review record confirming retained source values and unresolved outcome state. |
| `crypto_operator_approval_gate` | Crypto operator gate fixture keeps every gate `not_approved` and `pending_operator_review`. | Human review must confirm no gate state changed and no transition is approved by this matrix. | `pm_bot/tests/fixtures/crypto_live/pmbot_crypto_operator_approval_gate_record.valid.json` | Review record confirming gate states, reviewer, timestamp, and blockers. |
| `crypto_stop_condition_gate` | Crypto stop condition mapping keeps every condition manual and pending review. | Human review must confirm stop rows map to existing local evidence and block transitions without records. | `pm_bot/tests/fixtures/crypto_live/pmbot_crypto_stop_condition_mapping.valid.json` | Review record confirming stop row coverage and manual record requirements. |
| `crypto_validation_replay_gate` | Queue template regression coverage includes the crypto live task sequence through this task. | Human review must confirm current compile and pytest output after fixture review. | `tests/test_codex_queue_pmbot_templates.py` | Review record confirming validation command output and unresolved failures, if any. |

## Operator Review

Operators review:

- every gap row has one local static evidence reference
- every mapped source artifact resolves to an expected local file
- every row remains `pending_operator_review`
- operator gate and stop condition references remain blocked until a human record is complete
- required validation output is captured before any later readiness status change
- sensitive paths, credential stores, wallets, signing material, endpoint calls, runtime wiring, browser automation, workers, and timed automation remain outside scope

## Safety

- Local files, local fixtures, and static samples only.
- No network calls.
- No LLM provider calls.
- No external market API calls.
- No authenticated endpoint use.
- No credential, wallet, private-key, seed, signing, order, payment, or transaction path access.
- No runtime, dispatcher, scheduler, worker, browser, resident process, timed automation, or app-server wiring.
- No forecast scoring, action guidance, market ranking, numeric prediction metric, threshold comparison output, outcome resolution, selection advice, or trade instruction output.
- This matrix is not execution approval and is not runtime input.

## Validation

Required local validation commands:

- `python -m compileall pm_bot tests`
- `pytest pm_bot/tests tests/test_codex_queue_pmbot_templates.py`
