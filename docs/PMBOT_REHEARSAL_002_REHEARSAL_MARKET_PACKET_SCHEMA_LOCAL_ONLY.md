# PMBOT Rehearsal 002 Rehearsal Market Packet Schema Local Only

Task: `PMBOT-REHEARSAL-002-REHEARSAL-MARKET-PACKET-SCHEMA-LOCAL-ONLY`

Schema: `pmbot_rehearsal_market_packet_schema.v1`
Run mode: `local_static_rehearsal_market_packet_schema`
Operator review: `pending_operator_review`

## Purpose

This document defines the deterministic local schema for descriptive PMBOT rehearsal market packets. It is built from local files, local fixtures, and static samples only.

The schema is descriptive only. It is not execution approval, runtime input, market analysis, forecast scoring, action guidance, or selection advice.

## Static Fixture

The local fixture is:

`pm_bot/tests/fixtures/rehearsal/pmbot_rehearsal_market_packet_schema.valid.json`

The fixture records fixed packet fields, a schema field catalog, one static sample packet record, local source artifacts, operator review checks, validation commands, summary counts, and closed safety boundaries. It does not fetch data, call endpoints, approve execution, start processes, alter runtime wiring, or produce market instructions.

## Source Basis

Reviewed local PMBOT artifacts:

- `docs/PMBOT_REHEARSAL_001_READ_ONLY_REHEARSAL_SCENARIO_CONTRACT_LOCAL_ONLY.md`
- `pm_bot/tests/fixtures/rehearsal/pmbot_read_only_rehearsal_scenario_contract.valid.json`
- `docs/PMBOT_SUPERVISED_LIVE_001_READ_ONLY_LIVE_DATA_CONTRACT_LOCAL_ONLY.md`
- `docs/PMBOT_SUPERVISED_LIVE_002_LIVE_DATA_SOURCE_INVENTORY_LOCAL_ONLY.md`
- `docs/PMBOT_SUPERVISED_LIVE_003_OPERATOR_APPROVAL_GATE_RECORD_LOCAL_ONLY.md`
- `pm_bot/tests/fixtures/readiness/pmbot_read_only_live_data_contract.valid.json`
- `pm_bot/tests/fixtures/readiness/pmbot_live_data_source_inventory.valid.json`
- `pm_bot/tests/fixtures/readiness/pmbot_operator_approval_gate_record.valid.json`
- `tests/test_codex_queue_pmbot_templates.py`

These sources keep the rehearsal market packet schema local-only, static, descriptive, paper-mode, and pending operator review.

## Schema Contract

The fixture defines a closed packet field list for descriptive rehearsal market packet records. The fields cover:

- packet identity and state
- packet kind and rehearsal phase
- descriptive title, category, venue, currency, and close-time labels
- label-only outcome names
- local scenario contract reference
- local static source references
- field exclusion policy
- operator review status

Every packet record remains `pending_operator_review`. Records may identify local artifacts, copied descriptive labels, and review state. They may not include prices, ranks, numeric prediction metrics, market instructions, execution payloads, credential references, wallet references, or endpoint payloads.

## Operator Review Boundary

Operators review whether the listed local references, fixed field list, field catalog, static sample record, closed boundaries, and validation commands are internally consistent. This schema does not approve a live run, choose a market, resolve an outcome, change review status, open external services, access credentials, access wallets, call endpoints, or change runtime, dispatcher, scheduler, worker, browser, resident process, or run_codex wiring.

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
- This schema is not execution approval and is not runtime input.

## Validation

Required local validation commands:

- `python -m compileall pm_bot tests`
- `pytest pm_bot/tests tests/test_codex_queue_pmbot_templates.py`
