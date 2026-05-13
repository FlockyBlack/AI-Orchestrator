# ORCH-PMBOT-TRADING-MVP-050 Signed Order Payload Dry-Run Validation Gate

## Purpose

This task adds a review-only signed order payload validation gate for PMBOT tiny supervised live canary preparation.

The gate defines the shape of a future signed order payload workflow without producing any signature, signed payload, signed order, transaction hash, order ID, fill, balance, PnL, or execution result.

## What It Does

- Defines future required payload fields for review:
  - market or token identifier
  - side and outcome
  - price, size, and notional
  - order type
  - time-in-force or expiry
  - operator approval reference
  - risk decision reference
  - authenticated connector capability reference
  - wallet/signing boundary reference
- Validates missing fields and invalid field types.
- Rejects inputs that claim to contain signatures, signed payloads, signed orders, transaction hashes, order IDs, fills, balances, PnL, or execution results.
- Integrates passively with:
  - `authenticated_polymarket_connector.py` from task 048
  - `wallet_signing_boundary.py` from task 049
  - live readiness, evidence bundle, replay blocker matrix, go/no-go gate, paper daily loop, operator UI, and static secret boundary checks
- Emits `signed_order_payload_validation_gate_050.json` from the paper daily loop.

## What It Does Not Do

- It does not sign payloads.
- It does not generate signed payloads.
- It does not generate signed orders.
- It does not generate fake signatures, fake order IDs, fake transaction hashes, fake fills, balances, PnL, or execution results.
- It does not submit orders.
- It does not call authenticated Polymarket endpoints.
- It does not enable the live connector.
- It does not read private keys, mnemonics, wallet files, API secrets, auth tokens, Telegram tokens, or browser wallet data.
- It does not create browser automation, schedulers, daemons, or autonomous live trading loops.

## Why No Signing Occurs

Task 050 is a payload shape validation gate only. Signing remains outside the approved scope because wallet custody, private-key handling, cryptographic signing, endpoint authorization, live approval, and kill-switch coverage all require separate operator-approved tasks.

The gate calls the existing wallet/signing boundary only as a refusal boundary. That boundary returns review-only refusal metadata and keeps:

- `signing_enabled: false`
- `wallet_signing_enabled: false`
- `signed_payload_generation_enabled: false`
- `signed_order_generation_enabled: false`

## Why No Order Can Be Submitted

The gate never constructs an executable order and never exposes an order submission action. The authenticated connector scaffold remains passive and reports:

- `authenticated_polymarket_enabled: false`
- `live_connector_enabled: false`
- `order_submission_enabled: false`
- `real_execution_available: false`

The go/no-go gate and blocker matrix keep live blockers unresolved, including blockers for review-only signed payload validation and shape review not enabling signing.

## Dependency On 048 And 049

Task 048 defines the authenticated Polymarket connector scaffold as dry-run-only and non-executable. Task 050 uses its capability summary only as a reference proving authenticated calls, network calls, signing, and submission are disabled.

Task 049 defines the wallet/signing boundary as review-only and refusal-only. Task 050 uses that boundary to prove future signing requests remain refused and no signature material is produced.

## Future Explicit Live/Signing Task Requirements

A future task would need separate operator approval and would need to solve, at minimum:

- wallet custody and key-handling design
- redacted credential loading and audit policy
- authenticated endpoint allowlist and fully mocked tests
- signing adapter design and refusal-first tests
- disabled-first order adapter with kill-switch coverage
- dual-control live operator approval
- live audit, reconciliation, and rollback procedures
- explicit blocker resolution in the live blocker matrix

Until those are completed in separate reviewed tasks, this repository remains paper/dry-run only.

## Live Trading Status

This task does not enable live trading. The following flags remain false:

- `authenticated_polymarket_enabled`
- `live_connector_enabled`
- `order_submission_enabled`
- `wallet_signing_enabled`
- `signing_enabled`
- `signed_payload_generation_enabled`
- `signed_order_generation_enabled`
- `allowed_for_live`
- `canary_executable_now`
- `live_execution_approved`
- `real_execution_available`
