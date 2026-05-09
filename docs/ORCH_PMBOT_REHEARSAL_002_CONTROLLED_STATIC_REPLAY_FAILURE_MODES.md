# ORCH-PMBOT-REHEARSAL-002 Controlled Static Replay Failure Modes

Task: `ORCH-PMBOT-REHEARSAL-002-CONTROLLED-STATIC-REPLAY-FAILURE-MODES`

## Summary

REHEARSAL-002 hardens the actual read-only supervised-live static replay rehearsal by adding deterministic local failure-mode scenarios. The batch remains static/replay-only and verifies that unsafe or incomplete local inputs fail closed, warn safely, or block before operator review can be mistaken for execution approval.

Artifacts:

- `pm_bot/rehearsal/artifacts/actual_static_replay_failure_modes_002.result.json`
- `pm_bot/rehearsal/artifacts/actual_static_replay_failure_modes_002.md`
- `pm_bot/tests/fixtures/rehearsal_static_replay_failure_modes/`
- `pm_bot/tests/test_actual_read_only_static_replay_failure_modes.py`

## Relation To REHEARSAL-001

REHEARSAL-001 proved the happy-path actual read-only supervised-live static replay could pass using saved local source packets. REHEARSAL-002 keeps the same static runner and base fixture contract, then mutates one controlled input surface at a time to prove that missing, stale, contradictory, stopped, malformed, noisy, or sensitive-looking local inputs do not silently pass.

Base rehearsal:

- Task: `ORCH-PMBOT-REHEARSAL-001-ACTUAL-READ-ONLY-SUPERVISED-LIVE-REHEARSAL-STATIC-REPLAY`
- Rehearsal ID: `actual_static_replay_rehearsal_001`
- Base head: `31769c8e58e1d651d66fc0bc6bd7c39a0f4fe913`

## Failure Modes Tested

- `missing_evidence`: source evidence omits a required evidence record.
- `stale_evidence`: a required evidence timestamp exceeds the fixed freshness window.
- `contradiction_detected`: two required evidence records disagree on the same required static fact.
- `stop_condition_triggered`: the local stop matrix intentionally trips a hard stop.
- `malformed_market_packet`: the market packet has an invalid contract version.
- `forbidden_action_leakage_guard`: noisy action-like input text is sanitized and blocked without being echoed as instruction text.
- `sensitive_path_leakage_guard`: fake sensitive-looking local strings are sanitized and blocked without credential use.

## Observed Behavior

All 7 scenarios behaved as expected.

- Missing evidence produced `source_evidence:missing_required_evidence_ids:evidence_station_static_log` and triggered the source evidence stop condition.
- Stale evidence produced a hard staleness blocker and triggered the stale source evidence stop condition.
- Contradictory evidence was detected and triggered the contradiction stop condition.
- The forced stop matrix scenario blocked even though the other replay inputs were valid.
- The malformed market packet failed on the invalid market-packet contract version.
- Noisy action-like input was sanitized into generic safety blockers and warnings.
- Fake sensitive-looking input was sanitized into generic safety blockers and warnings.

## Validation Performed

Required validation commands:

- `python -m compileall ai_orchestrator pm_bot tests`
- `pytest pm_bot/tests/test_actual_read_only_static_replay_rehearsal.py`
- `pytest pm_bot/tests/test_actual_read_only_static_replay_failure_modes.py`
- `pytest pm_bot/tests/test_rehearsal_acceptance_report.py pm_bot/tests/test_rehearsal_next_action_backlog.py`
- `python -m json.tool docs/ORCH_PMBOT_REHEARSAL_002_RESULT.json`
- `python -m json.tool pm_bot/rehearsal/artifacts/actual_static_replay_failure_modes_002.result.json`
- `git diff --check`

Additional fixture JSON files were generated under `pm_bot/tests/fixtures/rehearsal_static_replay_failure_modes/` and validated with `python -m json.tool` during the final validation pass.

## Safety Boundaries Preserved

- Live network used: false.
- OpenRouter calls performed: 0.
- Polymarket API calls performed: 0.
- Authenticated endpoints used: false.
- Wallet or private-key access: false.
- Orders or trading actions: false.
- Runtime or dispatcher changes: false.
- Market recommendation generated: false.
- Probability, EV, edge, or side-selection output generated: false.
- Operator approval remains required.

No scheduler, daemon, watcher, background worker, autonomous execution path, runtime path, dispatcher path, wallet path, signing path, order path, or authenticated endpoint was added or touched.

## What This Proves

The static replay rehearsal now has executable coverage for the main local failure modes that must fail closed before any controlled public read-only fetch preparation. It proves that the current static runner can identify missing evidence, stale evidence, contradictions, explicit stop conditions, malformed packets, unsafe action-like fixture text, and fake sensitive-looking strings without using live data or external services.

## What This Does Not Prove

This does not prove live public data fetching is ready. It does not validate live source availability, live source latency, live HTML/API parsing, authentication safety, remote service behavior, operator UX under live timing, or production readiness. It does not approve autonomous trading, real-money activity, wallet access, order placement, side selection, execution routing, or any unattended automation.

## Remaining Blockers Before Controlled Public Read-Only Fetch

- Operator review of the REHEARSAL-002 failure-mode artifacts.
- A separate controlled public read-only fetch preparation task with explicit allowed source inventory.
- A read-only network boundary test that proves no authenticated, wallet, order, or execution endpoints are reachable.
- A local-to-public evidence mapping that preserves the same fail-closed behavior when public read-only fetches are later introduced.
- Continued prohibition on OpenRouter, Polymarket API calls, signing, orders, and autonomous execution unless separately approved.

## Next Recommended Action

`ORCH-PMBOT-REHEARSAL-003-CONTROLLED-PUBLIC-READ-ONLY-FETCH-PREP`
