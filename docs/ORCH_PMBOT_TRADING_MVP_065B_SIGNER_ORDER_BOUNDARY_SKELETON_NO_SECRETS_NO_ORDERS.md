# ORCH-PMBOT-TRADING-MVP-065B Signer/Order Boundary Skeleton No Secrets No Orders

## Purpose

This task adds a non-executable signer/order boundary skeleton for future 065 live-order work. It is an interface/spec scaffold only. It does not instantiate a signer, read secrets, generate signed material, submit orders, cancel orders, make authenticated trading calls, or connect a wallet.

The operator command is:

```text
python -m pm_bot.operator_runner.live_order_boundary_contract --market BTC --strategy tiny-momentum --dry-run
```

## Safety Boundary

The scaffold is intentionally blocked and non-executable:

- `execution_mode=preflight`
- `review_only=true`
- `preflight_only=true`
- `dry_run_only=true`
- `interface_only=true`
- `non_executable=true`
- `boundary_is_executable=false`
- `allowed_for_live=false`
- `signer_boundary_available=false`
- `signer_instantiated=false`
- `private_key_read=false`
- `credential_value_read=false`
- `signed_payload_generation_enabled=false`
- `order_submission_enabled=false`
- `order_cancel_enabled=false`
- `authenticated_trading_enabled=false`
- `wallet_connection_enabled=false`
- `resolved_blocker_count=0`

It must not and does not:

- read private key, seed, mnemonic, API secret, auth token, passphrase, or credential values
- instantiate a signer
- connect a wallet
- generate signatures, signed payloads, signed orders, or order payloads
- expose submit/cancel methods or endpoint paths
- use POST, PUT, PATCH, or DELETE endpoint code
- submit or cancel orders
- make authenticated trading calls
- create fake order IDs, transaction hashes, fills, balances, positions, or PnL
- create schedulers, daemons, background workers, or autonomous loops

## Added Interfaces

The model file defines:

- `NonExecutableSignerBoundary`
- `NonExecutableOrderSubmissionBoundary`
- `NonExecutableOrderCancelBoundary`
- `LiveBoundarySafetyContract`
- `RedactionPolicy`
- `FutureLiveOrderBoundaryChecklist`

Each model emits static review artifacts only. The boundary classes expose `to_dict()` only and no executable signing, submit, cancel, wallet, or endpoint methods.

## Artifacts

The default artifact directory is:

```text
pm_bot/trading_core/artifacts/live_order_boundary_contract_065b/
```

Generated artifacts:

- `live_order_boundary_contract_065b_result.json`
- `latest_live_order_boundary_contract_status_065b.json`
- `live_order_boundary_safety_contract_065b.json`
- `live_order_redaction_policy_065b.json`
- `live_order_boundary_checklist_065b.json`
- `live_order_non_executable_interfaces_065b.json`
- `live_order_boundary_operator_summary_065b.md`

## Validation Notes

The focused validation is:

```text
python -m pytest pm_bot/tests/test_live_order_boundary_contract_065b.py
```

The full PMBOT suite was also run with:

```text
python -B -m pytest pm_bot/tests
```

On Windows, the required worktree path makes one pre-existing public-evidence fixture path hit the 260-character boundary. A temporary `O:` alias pointing to the same worktree was used for the full-suite rerun so Python path checks could access that pre-existing fixture. The command itself and repository contents were unchanged.
