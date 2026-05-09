# PMBOT Rehearsal 015 Rehearsal Paperlive Accounting Links Local Only

Task: `PMBOT-REHEARSAL-015-REHEARSAL-PAPERLIVE-ACCOUNTING-LINKS-LOCAL-ONLY`

Link set: `pmbot-rehearsal-paperlive-accounting-links-001`
Contract: `pmbot_rehearsal_paperlive_accounting_links.v1`
Run mode: `local_static_rehearsal_paperlive_accounting_links`
Operator review: `pending_operator_review`

## Purpose

This document registers deterministic local PMBOT rehearsal links between paperlive rehearsal artifacts and paperlive accounting records for operator review. The link set is built from local files, local fixtures, and static samples only.

The link set connects the static crypto paperlive rehearsal packet and observation replay row to the local paperlive-to-accounting reconciliation sample and paper accounting ledger, validation, and session summary samples. It records local references, byte counts, SHA-256 digests, record identifiers, and pending review state only. It does not refresh data, call services, approve execution, resolve outcomes, compare thresholds for a runtime decision, or produce forecast scoring, action guidance, market recommendations, selection advice, probability scores, EV, edge, confidence, or side selection.

## Static Artifacts

The local rehearsal paperlive accounting link artifacts are:

- Static JSON sample: `pm_bot/paper_accounting/samples/rehearsal_paperlive_accounting_links.fixture.json`
- Static operator report sample: `pm_bot/paper_accounting/samples/rehearsal_paperlive_accounting_links.fixture.md`
- Builder and validator: `pm_bot/paper_accounting/rehearsal_paperlive_accounting_links.py`
- Contract test: `pm_bot/tests/test_rehearsal_paperlive_accounting_links.py`

The JSON sample records fixed link fields, two rehearsal artifact references, four paper accounting artifact references, one rehearsal-to-paperlive-accounting link row, operator review steps, required validation commands, summary counts, and closed safety boundaries.

## Source Basis

Reviewed local PMBOT artifacts:

- `pm_bot/tests/fixtures/crypto_live/pmbot_crypto_paperlive_rehearsal_packet.valid.json`
- `pm_bot/tests/fixtures/crypto_live/pmbot_crypto_paperlive_observation_replay.valid.json`
- `pm_bot/paper_accounting/samples/paperlive_accounting_reconciliation.fixture.json`
- `pm_bot/paper_accounting/samples/paper_accounting_ledger.fixture.json`
- `pm_bot/paper_accounting/samples/paper_accounting_validation.fixture.json`
- `pm_bot/paper_accounting/samples/paper_accounting_session_summary.fixture.json`
- `docs/PMBOT_CRYPTO_LIVE_006_CRYPTO_PAPERLIVE_REHEARSAL_PACKET_LOCAL_ONLY.md`
- `docs/PMBOT_CRYPTO_LIVE_007_CRYPTO_PAPERLIVE_OBSERVATION_REPLAY_LOCAL_ONLY.md`
- `docs/PMBOT_PAPERLIVE_AUDIT_001_PAPERLIVE_TO_ACCOUNTING_RECONCILIATION_LOCAL_ONLY.md`
- `docs/PMBOT_PAPER_ACCOUNTING_001_PAPER_ONLY_ACCOUNTING_LEDGER_LOCAL_ONLY.md`
- `docs/PMBOT_PAPER_ACCOUNTING_002_PAPER_ONLY_ACCOUNTING_VALIDATOR_LOCAL_ONLY.md`
- `docs/PMBOT_PAPER_ACCOUNTING_003_PAPER_ONLY_SESSION_SUMMARY_LOCAL_ONLY.md`

These inputs keep the rehearsal paperlive accounting links local-only, deterministic, descriptive, paper-mode, and pending operator review.

## Link Coverage

The static link set maps:

- `pmbot-crypto-paperlive-rehearsal-packet-001.sample.btc_threshold.rehearsal`
- `pmbot-crypto-paperlive-observation-replay-001.sample.btc_threshold.replay`
- `crypto_paperlive_observation_ledger_001.sample.btc_threshold.to.paper_accounting.paperlive_accounting_reconciliation`
- `paper_accounting_ledger_fixture_001`

The static paperlive reconciliation row records `no_accounting_delta_recorded`, so the rehearsal paperlive accounting link row has zero linked accounting entries. Accounting values, reference values, and source numeric fields remain in the referenced local fixtures and samples rather than being copied into this link set.

## Operator Review

Operators review:

- the rehearsal packet and replay references resolve to expected local files
- the paperlive reconciliation row references the expected local observation record
- the paper accounting ledger, validation, and session summary samples remain pending operator review
- artifact byte counts and SHA-256 digests match current local bytes
- linked accounting entry identifiers are present when the reconciliation sample names them
- numeric source values remain in referenced artifacts rather than this link set
- sensitive paths, credential stores, wallets, signing material, endpoint calls, runtime wiring, browser automation, workers, and timed automation remain outside scope
- validation output is captured before any later readiness status change

## Safety

- Local files, local fixtures, and static samples only.
- No network calls.
- No OpenRouter calls.
- No Polymarket API calls.
- No LLM provider calls.
- No external service calls.
- No authenticated endpoint use.
- No credential, wallet, private-key, seed, signing, order, trading endpoint, payment, or transaction path access.
- No runtime, dispatcher, scheduler, worker, browser, resident process, timed automation, or run_codex wiring.
- No market recommendation, forecast scoring, action guidance, or selection advice.
- No probability, EV, edge, or confidence scoring.
- No real-money actions.
- This link set is not execution approval and is not runtime input.

## Validation

Required local validation commands:

- `python -m compileall pm_bot tests`
- `pytest pm_bot/tests tests/test_codex_queue_pmbot_templates.py`
