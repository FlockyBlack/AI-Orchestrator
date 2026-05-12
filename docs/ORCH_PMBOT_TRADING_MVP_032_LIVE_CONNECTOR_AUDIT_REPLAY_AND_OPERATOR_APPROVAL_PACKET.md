# ORCH PMBOT Trading MVP 032 Live Connector Audit Replay And Operator Approval Packet

## Purpose

This task adds a deterministic, local-only review layer around the disabled real wallet connector boundary. It lets an operator inspect what the disabled connector would have been asked to evaluate, why it refused, which live blockers remain unresolved, which dry-run references were used, and whether static secret-boundary validation passed.

This is not live trading approval. It does not enable a wallet connector, signing, order placement, authenticated endpoints, browser automation, or autonomous execution.

## What Is Allowed

- Build local disabled-connector audit replay records from existing disabled connector audit artifacts.
- Compare replayed disabled-connector identifiers and statuses against stored audit records.
- Build an operator review packet for future live-readiness inspection.
- Surface passive statuses in the paper daily dashboard and paper strategy evaluation artifacts.
- Validate packet and replay shapes with the static secret-boundary policy.
- Keep live blocker matrix rows unresolved.

## What Remains Blocked

- Real wallet connection.
- Private key, mnemonic, recovery phrase, credential, or signing-material handling.
- Cryptographic signing.
- Real order placement.
- Authenticated Polymarket endpoint use.
- External API calls from this flow.
- Browser automation.
- Autonomous live execution.
- Real-money activity.
- Live execution approval.

## Operator Review Is Not Live Approval

The operator packet may report `operator_review_ready: true` when static local artifacts are present and valid. That status means only that the packet is ready for human review.

The packet always reports:

- `live_execution_approved: false`
- `real_execution_available: false`
- `live_connector_enabled: false`
- `operator_review_is_not_live_approval: true`

It also includes the explicit statement:

`This packet is for operator review only and does not authorize live execution.`

## Required Artifacts

The replay and packet expect static references to:

- disabled connector audit records
- canary readiness packet IDs
- canary replay acceptance or dry-run receipt IDs
- wallet boundary packet IDs
- risk decision IDs
- static secret-boundary validation summaries
- live connector blocker matrix rows

Missing required references make the replay status `insufficient_artifacts`.

## Replay Validation Flow

`pm_bot/trading_core/live_connector_audit_replay.py` rebuilds safe static replay records from disabled connector audit records. It recalculates deterministic replay IDs from safe fields only:

- request ID
- connector ID
- blocked reason IDs
- missing prerequisites
- source audit/result IDs
- local artifact references

It then compares the replayed disabled-connector result and audit IDs against the original audit record. Any drift produces `replay_failed`. A clean deterministic replay produces `replay_passed`, while still reporting that execution remains blocked by the disabled connector and unresolved live blockers.

## Secret Boundary Validation

The secret boundary remains static-only. The validators inspect packet shapes and field names already present in supplied local payloads. They do not inspect environment variables, read machine secrets, persist secrets, or configure credentials.

New helper wrappers validate:

- audit replay records
- operator review packets
- operator checklist items
- result artifacts

Forbidden secret-like fields are rejected in replay/operator payloads.

## Blocker Matrix Behavior

The live connector blocker matrix remains unresolved. Critical blockers still include the disabled real wallet connector, static-only secret boundary, missing authenticated endpoint boundary, disabled real order submission, live approval not implemented, kill switch not wired to a live adapter, and live audit sink not finalized.

No blocker is resolved by this task.

## Dashboard And Strategy Evaluation

The paper daily dashboard now surfaces a passive `live_connector_audit_operator_summary` with:

- `audit_replay_status`
- `operator_packet_status`
- `operator_review_ready`
- `live_execution_approved: false`
- `real_execution_available: false`
- `unresolved_live_blocker_count`
- `disabled_connector_status`
- `secret_boundary_status`
- latest replay and operator packet paths

The paper strategy evaluation ledger and summary surface only passive status fields:

- `live_connector_audit_replay_status`
- `operator_review_packet_status`
- `live_execution_approved: false`
- `real_execution_available: false`

## Next Step

The recommended next task is a future tiny live canary preflight contract and manual runbook. That future task must still be non-executing unless a separate operator-approved task explicitly changes the safety boundaries.
