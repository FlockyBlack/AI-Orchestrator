# ORCH PMBOT Trading MVP 034: Live Canary Dry-Run Operator Intent Packet

## Purpose

This task adds a dry-run operator intent packet for a future tiny live canary review. The packet is a local, deterministic, review-only artifact. It lets an operator record that specific local artifacts were reviewed and that unresolved blockers, limits, kill-switch requirements, abort conditions, and evidence requirements were acknowledged.

This is not live execution. It does not make a canary executable now.

## Operator-Signed Intent Definition

In this repository, operator-signed intent means a plain human acknowledgement in JSON/text form. It is not cryptographic signing.

Operator-signed intent does not mean:

- wallet signing
- private-key signing
- transaction signing
- order signing
- EIP-712 signing
- signed payload generation
- signed order generation
- authenticated endpoint authorization

Allowed human-context fields include `operator_signed_intent_acknowledgement` and `human_signed_acknowledgement_text` only when the packet also states that the acknowledgement is non-cryptographic and human-only.

## Explicit Non-Execution Statements

Every valid packet must include these statements:

- This operator intent packet is a dry-run acknowledgement only.
- This packet does not authorize live execution.
- This packet does not authorize wallet access, signing, order placement, or authenticated endpoint usage.
- Real execution remains unavailable in this build.

The packet always keeps:

- `live_execution_approved: false`
- `real_execution_available: false`
- `canary_executable_now: false`
- `live_connector_enabled: false`

## Required Artifact References

The intent packet must reference:

- future canary shape
- tiny live canary preflight contract
- manual runbook
- operator live review packet
- live connector audit replay
- disabled connector audit
- secret-boundary validation
- live connector blocker matrix
- risk review or fixed exposure review

These are references for operator review only. They are not authorization inputs for a live adapter.

## Acknowledgement Fields

The packet includes:

- `operator_identifier`, which may remain a placeholder in this dry-run build
- `operator_acknowledged_at`, which may remain a placeholder in this dry-run build
- `operator_acknowledgement_text`
- `human_signed_acknowledgement_text`
- `operator_signed_intent_acknowledgement`
- `operator_signed_intent_is_human_acknowledgement_only`

The acknowledgement model is intentionally text-only. It does not create or validate any cryptographic signature.

## Blocker Acknowledgement

The packet must include unresolved blocker IDs and must mark unresolved blockers as acknowledged for review. Acknowledgement does not resolve blockers.

The blocker matrix continues to keep all critical live blockers unresolved, including:

- operator intent packet is dry-run only
- operator intent is not live approval
- operator intent acknowledgement is not collected for live
- cryptographic signing remains unavailable
- live canary execution remains disabled
- live canary funding remains unconfigured
- live canary order adapter remains disabled

## Kill-Switch And Abort Conditions

The packet acknowledges kill-switch requirements and abort conditions, but kill-switch status remains not live-verified.

Abort conditions include:

- missing or invalid required artifacts
- any artifact claiming live execution is approved or available
- any request for secret, wallet, signing, order, or authenticated endpoint material
- any scheduler, daemon, recursive loop, or autonomous path that can bypass an operator

## Evidence Requirements

A valid packet acknowledges that future review evidence must capture:

- preflight contract reference
- manual runbook reference
- operator review packet reference
- audit replay reference
- disabled connector audit reference
- secret-boundary validation reference
- blocker matrix snapshot
- unresolved blocker IDs
- kill-switch and abort-condition acknowledgement

## Secret Boundary Rules

The static secret-boundary policy rejects cryptographic, wallet, order, and auth-style fields such as:

- `private_key`
- `mnemonic`
- `seed_phrase`
- `signature`
- `signed_order`
- `signed_payload`
- `raw_transaction`
- `auth_header`
- `bearer_token`
- `api_key`
- `order_submission_payload`
- `transaction_payload`

The validation remains static. It does not read environment variables, inspect secrets, print secrets, persist secrets, connect to wallets, or call external APIs.

## What Remains Blocked

This task does not add:

- real wallet integration
- secret or mnemonic handling
- cryptographic signing
- wallet signing
- transaction signing
- order signing
- real order placement
- authenticated Polymarket endpoints
- live connector enablement
- live canary execution
- autonomous live trading

## Future Gated Task Required

Before any real canary could be considered, a separate future operator-approved task would need to define and validate live-specific approval, credential handling, wallet boundary, signing boundary, order adapter, authenticated endpoint policy, funding and exposure reconciliation, live kill switch, and post-trade audit controls.

This dry-run intent packet is only a visibility and acknowledgement artifact for that future review path.
