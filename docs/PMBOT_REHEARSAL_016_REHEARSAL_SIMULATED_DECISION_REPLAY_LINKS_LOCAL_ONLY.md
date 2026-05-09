# PMBOT Rehearsal 016 Rehearsal Simulated Decision Replay Links Local Only

Task: `PMBOT-REHEARSAL-016-REHEARSAL-SIMULATED-DECISION-REPLAY-LINKS-LOCAL-ONLY`

Link set: `pmbot-rehearsal-simulated-decision-replay-links-001`
Contract: `pmbot_rehearsal_simulated_decision_replay_links.v1`
Run mode: `local_static_rehearsal_simulated_decision_replay_links`
Operator review: `pending_operator_review`

## Purpose

This document registers deterministic local PMBOT rehearsal links between rehearsal artifacts and simulated decision replay records for operator review. The link set is built from local files, local fixtures, and static samples only.

The link set connects the static rehearsal validation replay packet, CI-safe validation runner fixture, and operator review documents to the simulated decision packet, audit ledger, replay summary, and outcome replay link samples. It records local references, byte counts, SHA-256 digests, record identifiers, link rows, and pending review state only. It does not refresh data, call services, approve execution, resolve outcomes, compare thresholds for a runtime decision, or produce forecast scoring, action guidance, market recommendations, selection advice, probability scores, EV, edge, confidence, or side selection.

## Static Artifacts

The local rehearsal simulated decision replay link artifacts are:

- Static JSON sample: `pm_bot/simulated_decisions/samples/rehearsal_simulated_decision_replay_links.fixture.json`
- Static operator report sample: `pm_bot/simulated_decisions/samples/rehearsal_simulated_decision_replay_links.fixture.md`
- Builder and validator: `pm_bot/simulated_decisions/rehearsal_simulated_decision_replay_links.py`
- Contract test: `pm_bot/tests/test_rehearsal_simulated_decision_replay_links.py`

The JSON sample records fixed link fields, five rehearsal artifact references, four simulated decision artifact references, two rehearsal-to-simulated-decision replay link rows, operator review steps, required validation commands, summary counts, and closed safety boundaries.

## Source Basis

Reviewed local PMBOT artifacts:

- `pm_bot/tests/fixtures/rehearsal/pmbot_rehearsal_validation_replay_packet.valid.json`
- `pm_bot/tests/fixtures/rehearsal/pmbot_rehearsal_ci_safe_validation_runner.valid.json`
- `docs/PMBOT_REHEARSAL_013_REHEARSAL_ACCEPTANCE_REPORT_LOCAL_ONLY.md`
- `docs/PMBOT_REHEARSAL_014_REHEARSAL_SOURCE_QUALITY_LINKS_LOCAL_ONLY.md`
- `docs/PMBOT_REHEARSAL_015_REHEARSAL_PAPERLIVE_ACCOUNTING_LINKS_LOCAL_ONLY.md`
- `pm_bot/simulated_decisions/samples/simulated_decision_packet.fixture.json`
- `pm_bot/simulated_decisions/samples/simulated_decision_audit_ledger.fixture.json`
- `pm_bot/simulated_decisions/samples/simulated_decision_replay_summary.fixture.json`
- `pm_bot/simulated_decisions/samples/simulated_decision_outcome_replay_links.fixture.json`

These inputs keep the rehearsal simulated decision replay links local-only, deterministic, descriptive, paper-mode, and pending operator review.

## Link Coverage

The static link set maps:

- Rehearsal validation replay packet and CI-safe validation runner records to simulated decision packet and audit ledger rows.
- Rehearsal acceptance, source-quality-link, and paperlive-accounting-link review documents to simulated decision replay summary and outcome replay link rows.

Each link row names the matching rehearsal artifact identifiers, simulated decision artifact identifiers, replay record row identifiers, local reference pairs, and review checks. Source values remain in referenced local fixtures and samples rather than being copied into this link set.

## Operator Review

Operators review:

- the rehearsal fixture and document references resolve to expected local files
- the simulated decision sample references resolve to expected local files
- each linked simulated decision replay record identifier exists in the named local sample
- rehearsal record identifiers exist in the named local rehearsal fixture or document record
- artifact byte counts and SHA-256 digests match current local bytes
- source values remain in referenced artifacts rather than this link set
- every link and artifact remains pending operator review
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
