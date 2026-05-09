# PMBOT Paperlive Decision 001 Simulated Decision Packet Schema

Task: `PMBOT-PAPERLIVE-DECISION-001-SIMULATED-DECISION-PACKET-SCHEMA-NO-RECOMMENDATIONS`

## What Changed

- Added a local PMBOT simulated decision packet schema under `pm_bot/simulated_decisions/`.
- Added a static fixture packet that uses local PMBOT test fixtures only.
- Added focused tests for deterministic loading, required field coverage, local-only references, summary counts, and blocked scoring or market instruction fields.

## Schema Contract

The packet contract version is `pmbot_simulated_decision_packet.v1`.

The schema is a static local recordkeeping artifact. It describes:

- packet identity and static creation time
- local market snapshot metadata
- local input artifacts
- descriptive record sections
- operator notes and operator review status
- summary counts
- closed safety boundaries

The packet requires operator review and stays in `offline_recordkeeping` mode.

## Safety

- Local files and static fixtures only.
- No network calls.
- No LLM provider calls.
- No external market API calls.
- No authenticated service use.
- No wallet access or transaction signing.
- No runtime, dispatcher, scheduler, worker, browser, or app-server wiring.
- No market scoring metrics, numeric prediction metrics, ranked candidate output, or market instruction fields.
