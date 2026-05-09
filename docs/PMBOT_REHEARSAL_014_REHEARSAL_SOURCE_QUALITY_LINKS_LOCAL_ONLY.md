# PMBOT Rehearsal 014 Rehearsal Source Quality Links Local Only

Task: `PMBOT-REHEARSAL-014-REHEARSAL-SOURCE-QUALITY-LINKS-LOCAL-ONLY`

Link set: `pmbot-rehearsal-source-quality-links-001`
Contract: `pmbot_rehearsal_source_quality_links.v1`
Run mode: `local_static_rehearsal_source_quality_links`
Operator review: `pending_operator_review`

## Purpose

This document registers deterministic local PMBOT rehearsal links between rehearsal artifacts and source quality records for operator review. The link set is built from local files, local fixtures, and static samples only.

The link set connects the static rehearsal source evidence bundle, staleness case set, and contradiction case set to local source quality ledger rows, source quality report rows, source quality regression rows, source evidence link rows, source staleness check rows, and source contradiction review rows. It records local references, byte counts, SHA-256 digests, source record identifiers, rehearsal record identifiers, and pending review state only. It does not refresh data, call services, approve execution, compare thresholds for a runtime decision, resolve outcomes, or produce forecast scoring, action guidance, market recommendations, selection advice, probability scores, EV, edge, confidence, or side selection.

## Static Artifacts

The local rehearsal source quality link artifacts are:

- Static JSON sample: `pm_bot/source_quality/samples/rehearsal_source_quality_links.fixture.json`
- Static operator report sample: `pm_bot/source_quality/samples/rehearsal_source_quality_links.fixture.md`
- Builder and validator: `pm_bot/source_quality/rehearsal_source_quality_links.py`
- Contract test: `pm_bot/tests/test_rehearsal_source_quality_links.py`

The JSON sample records fixed link fields, three rehearsal artifact references, six source quality artifact references, two rehearsal-to-source-quality link rows, operator review steps, required validation commands, summary counts, and closed safety boundaries.

## Source Basis

Reviewed local PMBOT artifacts:

- `docs/PMBOT_REHEARSAL_003_REHEARSAL_SOURCE_EVIDENCE_BUNDLE_LOCAL_ONLY.md`
- `pm_bot/tests/fixtures/rehearsal/pmbot_rehearsal_source_evidence_bundle.valid.json`
- `docs/PMBOT_REHEARSAL_006_REHEARSAL_STALENESS_CASE_SET_LOCAL_ONLY.md`
- `pm_bot/tests/fixtures/rehearsal/pmbot_rehearsal_staleness_case_set.valid.json`
- `docs/PMBOT_REHEARSAL_007_REHEARSAL_CONTRADICTION_CASE_SET_LOCAL_ONLY.md`
- `pm_bot/tests/fixtures/rehearsal/pmbot_rehearsal_contradiction_case_set.valid.json`
- `pm_bot/source_quality/samples/unified_source_quality_ledger.fixture.json`
- `pm_bot/source_quality/samples/source_quality_report_summary.fixture.json`
- `pm_bot/source_quality/samples/source_quality_regression.fixture.json`
- `pm_bot/source_quality/samples/source_evidence_link_map.fixture.json`
- `pm_bot/source_quality/samples/source_staleness_check_spec.fixture.json`
- `pm_bot/source_quality/samples/source_contradiction_ledger.fixture.json`

These inputs keep the rehearsal source quality links local-only, deterministic, descriptive, paper-mode, and pending operator review.

## Link Coverage

The static link set maps these source quality records:

- `official_daily_climate_report` rehearsal source records to the matching source quality ledger row, report row, regression row, source evidence link, staleness check, and contradiction row.
- `airport_station_observation_log` rehearsal source records to the matching source quality ledger row, report row, regression row, source evidence link, staleness check, and contradiction row.

Each link row names the matching rehearsal bundle record, rehearsal staleness case records, rehearsal contradiction case records, and source quality record identifiers. Source values remain in referenced local fixtures and are not copied into this link set.

## Operator Review

Operators review:

- the rehearsal fixture references resolve to expected local files
- each link row points to the intended fixed source identifier
- each source quality record identifier exists in the named local source quality artifact
- rehearsal record identifiers exist in the named local rehearsal fixture
- artifact byte counts and SHA-256 digests match current local bytes
- source values remain in referenced artifacts rather than this link set
- every link and source quality artifact remains pending operator review
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
- No probability, EV, edge, confidence, or side selection.
- No real-money actions.
- This link set is not execution approval and is not runtime input.

## Validation

Required local validation commands:

- `python -m compileall pm_bot tests`
- `pytest pm_bot/tests tests/test_codex_queue_pmbot_templates.py`
