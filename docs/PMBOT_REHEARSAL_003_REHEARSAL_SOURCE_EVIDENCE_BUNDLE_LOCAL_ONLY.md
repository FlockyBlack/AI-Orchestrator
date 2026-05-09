# PMBOT Rehearsal 003 Rehearsal Source Evidence Bundle Local Only

Task: `PMBOT-REHEARSAL-003-REHEARSAL-SOURCE-EVIDENCE-BUNDLE-LOCAL-ONLY`

Bundle: `pmbot-rehearsal-source-evidence-bundle-001`
Contract: `pmbot_rehearsal_source_evidence_bundle.v1`
Run mode: `local_static_rehearsal_source_evidence_bundle`
Operator review: `pending_operator_review`

## Purpose

This document registers the deterministic local PMBOT rehearsal source evidence bundle for operator review. It is built from local files, local fixtures, and static samples only.

The bundle links the local rehearsal market packet schema to the existing source evidence inventory, source evidence link map, staleness check spec, and contradiction ledger artifacts. It records local references, byte counts, SHA-256 digests, source record identifiers, and pending review state only. It does not fetch data, call services, approve execution, produce market recommendations, produce forecast scoring, provide action guidance, or provide selection advice.

## Static Fixture

The local fixture is:

`pm_bot/tests/fixtures/rehearsal/pmbot_rehearsal_source_evidence_bundle.valid.json`

The fixture records one static bundle record, source evidence artifact references, local digests, operator review checks, source bundle rules, validation commands, summary counts, and closed safety boundaries.

## Source Basis

Reviewed local PMBOT artifacts:

- `docs/PMBOT_REHEARSAL_001_READ_ONLY_REHEARSAL_SCENARIO_CONTRACT_LOCAL_ONLY.md`
- `pm_bot/tests/fixtures/rehearsal/pmbot_read_only_rehearsal_scenario_contract.valid.json`
- `docs/PMBOT_REHEARSAL_002_REHEARSAL_MARKET_PACKET_SCHEMA_LOCAL_ONLY.md`
- `pm_bot/tests/fixtures/rehearsal/pmbot_rehearsal_market_packet_schema.valid.json`
- `docs/PMBOT_SOURCE_EVIDENCE_001_SOURCE_INVENTORY_LEDGER_LOCAL_ONLY.md`
- `pm_bot/source_quality/samples/source_evidence_inventory_ledger.fixture.json`
- `pm_bot/source_quality/samples/source_evidence_inventory_ledger.fixture.md`
- `docs/PMBOT_SOURCE_EVIDENCE_002_SOURCE_EVIDENCE_LINK_MAP_LOCAL_ONLY.md`
- `pm_bot/source_quality/samples/source_evidence_link_map.fixture.json`
- `pm_bot/source_quality/samples/source_evidence_link_map.fixture.md`
- `docs/PMBOT_SOURCE_EVIDENCE_003_SOURCE_STALENESS_CHECK_SPEC_LOCAL_ONLY.md`
- `pm_bot/source_quality/samples/source_staleness_check_spec.fixture.json`
- `pm_bot/source_quality/samples/source_staleness_check_spec.fixture.md`
- `docs/PMBOT_SOURCE_EVIDENCE_004_SOURCE_CONTRADICTION_LEDGER_LOCAL_ONLY.md`
- `pm_bot/source_quality/samples/source_contradiction_ledger.fixture.json`
- `pm_bot/source_quality/samples/source_contradiction_ledger.fixture.md`

These inputs keep the rehearsal source evidence bundle local-only, deterministic, descriptive, paper-mode, and pending operator review.

## Bundle Content

The bundle contains:

- one static rehearsal source evidence bundle record
- four source evidence inventory record identifiers
- four source evidence link map row identifiers
- four source staleness check identifiers
- one source contradiction ledger row identifier
- twelve source evidence artifact references with local byte counts and SHA-256 digests
- operator review checks and source bundle rules

Source values remain in referenced local artifacts and are not copied into the bundle record.

## Operator Review Boundary

Operators review whether the listed local references, digests, source record identifiers, review checks, and closed safety boundaries are internally consistent. This bundle does not approve a live run, choose a market, resolve an outcome, change review status, open external services, access credentials, access wallets, call endpoints, or change runtime, dispatcher, scheduler, worker, browser, resident process, or run_codex wiring.

## Safety

- Local files, local fixtures, and static samples only.
- No network calls.
- No OpenRouter calls.
- No Polymarket API calls.
- No authenticated endpoints.
- No credential, wallet, private-key, seed, signing, order, trading endpoint, payment, or transaction path access.
- No runtime, dispatcher, scheduler, worker, browser, resident process, timed automation, or run_codex wiring.
- No market recommendation, forecast scoring, action guidance, or selection advice.
- No probability, EV, edge, or confidence scoring.
- No real-money actions.
- This bundle is not execution approval and is not runtime input.

## Validation

Required local validation commands:

- `python -m compileall pm_bot tests`
- `pytest pm_bot/tests tests/test_codex_queue_pmbot_templates.py`
