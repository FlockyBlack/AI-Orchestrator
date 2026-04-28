# PM Bot Read-Only Fetcher Implementation Plan V1

## Status

PMBOT-BATCH-008 is a design-only planning task. This document does not implement a live fetcher, does not add API calls, and does not authorize runtime wiring.

## Purpose

Define the exact future build plan for a read-only market snapshot fetcher that can be implemented later only after separate human approval and Flocky validation.

## Future Module Names Only

The following future module names are proposed for a later approved implementation. They are names only in this document and are not created by PMBOT-BATCH-008.

- `pm_bot/live_readonly/fetch_market_snapshots.py`
- `pm_bot/live_readonly/normalize_snapshot.py`
- `pm_bot/live_readonly/quarantine_snapshot.py`
- `pm_bot/live_readonly/validate_normalized_snapshot.py`
- `pm_bot/live_readonly/import_snapshot_to_paper_replay.py`
- `pm_bot/live_readonly/build_snapshot_manifest.py`
- `pm_bot/live_readonly/tests/test_fetch_market_snapshots.py`
- `pm_bot/live_readonly/tests/test_normalize_snapshot.py`
- `pm_bot/live_readonly/tests/test_quarantine_snapshot.py`
- `pm_bot/live_readonly/tests/test_import_snapshot_to_paper_replay.py`

## Future Allowed Files

If a later implementation is explicitly approved, the implementation should remain isolated to:

- `pm_bot/live_readonly/**`
- `pm_bot/contracts/**`
- `pm_bot/boundary/**`
- `pm_bot/audit/**`
- `docs/PM_BOT_*.md`
- `docs/PM_BOT_*.json`
- `docs/PMBOT_*.md`
- `docs/PMBOT_*.json`

## Future Forbidden Files

A later implementation must not create, modify, or wire behavior into:

- `codex_auto/**`
- `governance/**`
- `state/**`
- `results/**`
- `runtime/**`
- `dispatcher/**`
- `checkpoints/**`
- `freezes/**`
- `tasks/**`
- any `run_codex` file or folder
- approval, queue, or lifecycle artifacts
- root-level orchestration or runtime scripts
- existing PMBOT implementation modules outside the future `pm_bot/live_readonly/**` package

## Future Raw Snapshot Flow

1. Read approved public market data through a future read-only client after separate approval.
2. Capture the provider response without execution semantics.
3. Write a raw snapshot artifact that conforms to `pm_bot/contracts/raw_market_snapshot.schema.v1.json`.
4. Record deterministic metadata such as source name, capture timestamp, and snapshot identifier.
5. Reject or quarantine any payload that includes credentials, wallet fields, signer fields, or order fields.

## Future Normalized Snapshot Flow

1. Load a raw snapshot artifact only after capture completes.
2. Normalize market identifiers, title fields, status, outcome ordering, price fields, liquidity fields, and freshness metadata.
3. Validate the normalized output against `pm_bot/contracts/normalized_market_snapshot.schema.v1.json`.
4. Mark the normalized snapshot as `validation_status = valid` only when all schema and policy checks pass.
5. Keep normalization side effects limited to static artifacts; no dispatcher, runtime, or state mutation is allowed.

## Future Quarantine Flow

1. Quarantine malformed, stale, partial, contradictory, duplicate, or schema-drifted snapshots.
2. Emit a quarantine record that conforms to `pm_bot/contracts/snapshot_quarantine_record.schema.v1.json`.
3. Store the blocking reason, severity, source snapshot id, and allowed next step.
4. Prevent quarantined data from entering paper replay import.
5. Require manual review before any future contract change or parser relaxation.

## Future Paper Replay Import Flow

1. Accept normalized snapshots only when validation succeeds.
2. Import snapshots into paper replay through `pm_bot/contracts/paper_replay_import_contract.v1.json`.
3. Preserve paper-only semantics with no live trade path, no watchlist execution path, and no autonomous action path.
4. Treat imported snapshots as research inputs for replay only.
5. Keep replay import deterministic and auditable.

## Future Tests Required Before Network Or API Approval

The following test work must pass before any network or API implementation is approved:

- contract fixture tests for valid, invalid, stale, duplicate, and contradictory raw snapshots
- normalization tests for outcome mapping, price reconciliation, liquidity normalization, and market status handling
- quarantine tests for malformed payloads, schema drift, stale data, partial capture, and duplicate snapshots
- paper replay import tests proving no execution fields are accepted
- static audit tests proving no wallet, signer, order, trading, dispatcher, `run_codex`, or runtime wiring behavior exists
- dry-run parser tests backed by static fixtures only
- approval-gate validation showing human approval and Flocky validation remain mandatory

## Future Approval Gates

No implementation work may start until all of the following are true:

- human approval is explicitly granted for read-only fetcher implementation
- Flocky validates the planned boundary before implementation starts
- allowed files and forbidden files are re-checked
- contracts and quarantine rules are frozen for the implementation batch
- test plan is accepted before any network or API code is introduced
- paper replay remains the only downstream consumer

## Failure Handling And Rollback Direction

- If capture logic introduces schema drift, quarantine all affected snapshots and roll back to static fixtures.
- If a future implementation adds risky runtime wiring, block the batch and remove the new implementation package.
- If any network or API code escapes the approved package boundary, stop the batch and revert to design-only state.

## Explicit Non-Scope For PMBOT-BATCH-008

- no live fetcher implementation
- no network or API calls
- no live Polymarket API
- no API credentials
- no wallet or private key access
- no signer access
- no order generation or execution
- no trading logic
- no runtime wiring
- no dispatcher integration
- no `run_codex` integration
