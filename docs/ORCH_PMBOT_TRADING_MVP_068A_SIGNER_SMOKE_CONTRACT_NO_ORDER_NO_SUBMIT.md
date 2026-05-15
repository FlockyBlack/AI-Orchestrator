# ORCH-PMBOT-TRADING-MVP-068A Signer Smoke Contract No Order No Submit

## Purpose

This task adds a contract-only signer smoke scaffold for future live-order readiness work. It defines what a future safe diagnostic signer smoke may verify, but it does not execute the smoke check in this task.

The operator command is:

```text
python -m pm_bot.operator_runner.signer_smoke_contract --market BTC --strategy tiny-momentum --dry-run
```

## Safety Boundary

The contract is intentionally blocked and non-executable:

- `execution_mode=preflight`
- `review_only=true`
- `preflight_only=true`
- `dry_run_only=true`
- `contract_only=true`
- `non_executable=true`
- `signer_smoke_executable=false`
- `allowed_for_live=false`
- `private_key_read=false`
- `polymarket_private_key_read=false`
- `address_derivation_performed=false`
- `diagnostic_challenge_signing_attempted=false`
- `order_payload_signing_enabled=false`
- `order_payload_signed=false`
- `order_submission_enabled=false`
- `order_cancellation_enabled=false`
- `authenticated_trading_enabled=false`
- `wallet_connection_enabled=false`
- `resolved_blocker_count=0`

It must not and does not:

- read private key, seed, mnemonic, API secret, auth token, passphrase, or credential values
- derive or emit a wallet address
- sign a diagnostic challenge
- sign order payloads
- generate signed order payloads
- submit or cancel orders
- connect a wallet UI
- call authenticated trading endpoints
- log raw or redacted key material
- create fake order IDs, transaction hashes, fills, balances, positions, or PnL
- create schedulers, daemons, background workers, or autonomous loops

## Future Contract Scope

A separate future operator-approved task may define an explicit opt-in signer smoke. The contract says such a future check may verify:

- address derivation
- non-order diagnostic challenge signing
- no order payload
- no order submit
- no raw key log

That future mode is documented only. It is not enabled by this task and cannot be selected from the 068A runner.

## Added Files

- `pm_bot/trading_core/signer_smoke_contract_models.py`
- `pm_bot/trading_core/signer_smoke_contract.py`
- `pm_bot/operator_runner/signer_smoke_contract.py`
- `pm_bot/tests/test_signer_smoke_contract_068a.py`

## Artifacts

The default artifact directory is:

```text
pm_bot/trading_core/artifacts/signer_smoke_contract_068a/
```

Generated artifacts:

- `signer_smoke_contract_068a_result.json`
- `latest_signer_smoke_contract_status_068a.json`
- `signer_smoke_safety_contract_068a.json`
- `signer_smoke_redaction_policy_068a.json`
- `signer_smoke_operator_summary_068a.md`

## Validation

Focused validation:

```text
python -m pytest pm_bot/tests/test_signer_smoke_contract_068a.py
```

Required integration validation is recorded in the paired result JSON.
