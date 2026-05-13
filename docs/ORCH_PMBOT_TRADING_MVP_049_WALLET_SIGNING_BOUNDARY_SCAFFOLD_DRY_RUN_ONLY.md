# ORCH-PMBOT-TRADING-MVP-049 Wallet Signing Boundary Scaffold

Task ID: `ORCH-PMBOT-TRADING-MVP-049-WALLET-SIGNING-BOUNDARY-SCAFFOLD-DRY-RUN-ONLY`

## Purpose

This task adds a dry-run-only wallet/signing boundary scaffold for future PMBOT tiny supervised live canary preparation.

The scaffold defines the report shape, refusal behavior, operator review fields, and passive integration points needed to discuss future wallet/signing work without making any live execution possible.

## What It Does

- Emits a review-only wallet/signing boundary report.
- Reports wallet/signing readiness as missing or redacted marker status only.
- Reads only explicitly safe marker config keys when asked to inspect an environment mapping:
  - `PMBOT_WALLET_SIGNING_ENABLED`
  - `PMBOT_WALLET_ADDRESS_CONFIGURED`
  - `PMBOT_SIGNING_PROVIDER_CONFIGURED`
  - `PMBOT_SIGNING_DRY_RUN_ONLY`
- Refuses every signing request through `validate_signing_request_for_review`.
- Adds passive visibility to:
  - live enablement preflight
  - live canary readiness evidence bundle
  - live connector blocker matrix
  - canary readiness packet metadata
  - final go/no-go blocker flow
  - paper daily loop artifacts
  - operator UI panel
  - static secret boundary policy

## What It Does Not Do

- Does not read private keys.
- Does not read mnemonics or seed phrases.
- Does not read wallet files.
- Does not connect to browser wallets.
- Does not connect to any wallet.
- Does not implement cryptographic signing.
- Does not implement wallet signing.
- Does not implement transaction signing.
- Does not generate signatures.
- Does not generate signed payloads.
- Does not generate signed orders.
- Does not generate transaction hashes or order IDs.
- Does not call authenticated Polymarket endpoints.
- Does not submit orders.
- Does not enable live trading.

## Why No Keys Are Read

This task is a boundary-shape and refusal layer only. It has no valid reason to inspect secret values because no signing provider, wallet connector, or live execution path is enabled.

The implementation only handles safe marker-style config. Unknown raw-like config names are counted without emitting key names or values. The boundary reports `no_raw_secrets_parsed_or_emitted: true`, and static secret boundary validation is applied to artifacts and UI summaries.

## Why No Signing Is Performed

Signing is explicitly outside this task. The scaffold forces these fields to remain false:

- `wallet_signing_enabled`
- `signing_enabled`
- `cryptographic_signing_enabled`
- `transaction_signing_enabled`
- `signed_payload_generation_enabled`
- `signed_order_generation_enabled`
- `real_execution_available`
- `allowed_for_live`

Every review request returns `SIGNING_REQUEST_REFUSED` and omits signature, signed payload, signed order, transaction hash, and order ID fields.

## Future Explicit Signing Task Requirements

A separate future operator-approved task would need, at minimum:

- dual-control live approval model
- reviewed credential and secret handling policy
- wallet address verification without exposing private material
- signing provider boundary design
- endpoint allowlist and audit policy
- disabled-first order adapter
- live kill-switch wired to every future live boundary
- all live blockers resolved in separate reviewed tasks

That future task must still begin disabled-first and refusal-first. This scaffold does not grant approval for it.

## Why This Does Not Enable Live Trading

All integrations are passive. They only surface review status and unresolved blockers. The live blocker matrix gains a new unresolved blocker for the review-only wallet signing scaffold, and `resolved_blocker_count` remains `0`.

The operator UI shows a passive "Wallet Signing Boundary" section with no executable action. The paper daily loop writes `wallet_signing_boundary_049.json` as a local review artifact only.
