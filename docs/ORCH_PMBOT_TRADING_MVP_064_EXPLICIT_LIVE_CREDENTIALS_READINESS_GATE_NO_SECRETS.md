# ORCH-PMBOT-TRADING-MVP-064 Explicit Live Credentials Readiness Gate No Secrets

## Purpose

This task implements a review-only live credentials readiness gate for future PMBOT live-credential preparation. The gate answers only whether explicit operator-controlled marker names are present. It does not read marker values or credential values.

The gate is safe to run with:

```text
python -m pm_bot.operator_runner.explicit_live_credentials_readiness_gate --market BTC --strategy tiny-momentum --dry-run
```

## Safety Boundary

The implementation is intentionally non-executable:

- `execution_mode=preflight`
- `review_only=true`
- `preflight_only=true`
- `presence_booleans_only=true`
- `allowed_for_live=false`
- `live_execution_approved=false`
- `operator_approved=false`
- `candidate_is_executable=false`
- `resolved_blocker_count=0`

It must not and does not:

- read private key, seed, mnemonic, raw API secret, auth token, passphrase, or wallet values
- print, hash, mask, prefix, suffix, length-leak, transform, or store credential values
- enumerate broad environment state
- read `.env` files, wallet files, credential stores, browser profiles, or auth stores
- connect a wallet
- instantiate a signer
- sign payloads
- generate signed order payloads
- submit or cancel orders
- read balances, positions, fills, or PnL
- make authenticated Polymarket calls
- enable live trading

## Presence-Only Behavior

The gate uses an explicit marker-name allowlist from the 064 design reference. Runtime checks are limited to marker membership:

- required credential-source markers
- required manual-control markers
- execution flag markers that must remain blocked if present
- optional non-secret context marker labels

For environment-backed runs, only `marker_label in environ` membership is used. Marker values are not read or parsed, so raw values cannot be emitted by this gate. Any present execution flag marker is recorded as a conflict by marker name only and does not enable live execution.

## Artifacts

The default artifact directory is:

```text
pm_bot/trading_core/artifacts/explicit_live_credentials_readiness_gate_064/
```

Generated artifacts:

- `explicit_live_credentials_readiness_gate_064_result.json`
- `explicit_live_credentials_readiness_gate_064_operator.md`
- `latest_explicit_live_credentials_readiness_gate_status_064.json`
- `redacted_marker_presence_064.json`
- `operator_approval_boundary_064.json`
- `credential_safety_policy_validation_064.json`
- `live_credentials_readiness_blockers_064.json`
- `explicit_live_credentials_operator_checklist_064.json`
- `explicit_live_credentials_readiness_summary_064.json`

## Status Semantics

`blocked` means one or more required markers are absent, an execution flag marker is present, or safety validation failed. Live execution is still blocked.

`redacted_presence_review_ready_live_blocked` means all required marker names are present and no execution flag marker is present. This is still not live readiness and still does not approve execution. `allowed_for_live` remains false.

## Remaining Blockers

The gate always preserves unresolved live blockers, including:

- live execution not approved
- credential values not verified by PMBOT
- operator review does not enable execution
- authenticated Polymarket requests blocked
- wallet connection blocked
- signer instantiation blocked
- private key reads blocked
- API secret reads blocked
- signed payload generation blocked
- order submission blocked
- order cancellation blocked
- balance and position reads blocked
- kill switch not bound to a live adapter
- rollback/cancel plan not implemented
- first live order task not present

## Validation

The focused validation is:

```text
python -m pytest pm_bot/tests/test_explicit_live_credentials_readiness_gate_064.py
```

The full task validation also runs the previous 063 and 060Q safety gates, all PMBOT tests, compile checks, dry-run commands, and diff whitespace checks.
