# PMBOT Source Evidence 004 Source Contradiction Ledger Local Only

Task: `PMBOT-SOURCE-EVIDENCE-004-SOURCE-CONTRADICTION-LEDGER-LOCAL-ONLY`

Ledger: `source_contradiction_ledger_fixture_001`
Contract: `pmbot_source_contradiction_ledger.v1`
Run mode: `local_static_source_contradiction_ledger`
Operator review: `pending_operator_review`

## Purpose

This document registers the local PMBOT source contradiction ledger for operator review. The ledger is deterministic and built from local files, local fixtures, and static samples only.

The ledger maps local source staleness rows into static field comparison rows. It records source identities, local artifact references, byte counts, SHA-256 digests, mapped field values, subject key matches, static value differences, and pending review state only. It does not refresh data, call services, approve execution, rank sources, or produce predictive metrics, stance output, source preference output, or trade instruction output.

## Static Artifacts

The local request fixture is:

`pm_bot/tests/fixtures/source_quality/source_contradiction_ledger_request.valid.json`

The generated static ledger and report samples are:

- `pm_bot/source_quality/samples/source_contradiction_ledger.fixture.json`
- `pm_bot/source_quality/samples/source_contradiction_ledger.fixture.md`

The implementation is:

`pm_bot/source_quality/source_contradiction_ledger.py`

## Source Basis

Reviewed local PMBOT artifacts:

- `pm_bot/source_quality/samples/source_staleness_check_spec.fixture.json`
- `pm_bot/source_quality/samples/source_staleness_check_spec.fixture.md`
- `docs/PMBOT_SOURCE_EVIDENCE_003_SOURCE_STALENESS_CHECK_SPEC_LOCAL_ONLY.md`
- `pm_bot/tests/fixtures/weather/official_daily_climate_report_snapshot.json`
- `pm_bot/tests/fixtures/weather/airport_station_observation_log_snapshot.json`
- `pm_bot/tests/test_source_staleness_check_spec.py`
- `tests/test_codex_queue_pmbot_templates.py`

These inputs keep the contradiction ledger local-only, static, descriptive, and pending operator review.

## Ledger Content

Each source contradiction row records:

- source pair identity and labels
- source staleness check ids
- source artifact references, byte counts, and digests
- subject key field comparisons
- mapped value comparisons
- static difference state
- pending operator review checks

The initial static fixture compares the local official daily climate report high-temperature field with the local airport station observation high-temperature field for the same station and observation date. The row records the static value difference and leaves the state pending operator review.

## Operator Review

Operators review:

- every source pair points to local staleness rows and local artifact references
- every local reference stays under allowed static paths
- digests and byte counts correspond to the local artifacts
- subject keys and mapped field values match local static artifact bytes
- every row remains pending operator review
- sensitive paths, credential stores, wallets, signing material, endpoint calls, runtime wiring, browser automation, workers, and timed automation remain outside scope
- validation output is captured before any later status change

## Safety

- Local files, local fixtures, and static samples only.
- No network calls.
- No LLM provider calls.
- No external market API calls.
- No authenticated endpoint use.
- No credential, wallet, private-key, seed, signing, order, payment, or transaction path access.
- No runtime, dispatcher, scheduler, worker, browser, resident process, timed automation, or app-server wiring.
- No predictive metrics, source preference output, stance output, or trade instruction output.
- This ledger is not execution approval and is not runtime input.

## Validation

Required local validation commands:

- `python -m compileall pm_bot tests`
- `pytest pm_bot/tests tests/test_codex_queue_pmbot_templates.py`
