# ORCH PMBOT Trading MVP 070A Signed Order Payload Dry-Run No Submit

Task ID: `ORCH-PMBOT-TRADING-MVP-070A-SIGNED-ORDER-PAYLOAD-DRY-RUN-NO-SUBMIT`

070A adds a guarded signed order payload dry-run scaffold for operator review. It builds a deterministic, non-executable payload contract and safety artifacts only. It does not read private keys, create signed material, submit orders, cancel orders, call trading write endpoints, or enable live trading.

## Default Safe Run

```powershell
python -m pm_bot.operator_runner.signed_order_payload_dry_run --market BTC --strategy tiny-momentum --dry-run
```

Expected default result:

- `local_signing_diagnostic_status=diagnostic_not_requested`
- `private_key_read=false`
- `local_payload_signing_attempted=false`
- `local_payload_signed=false`
- `signed_payload_submit_enabled=false`
- `order_submission_enabled=false`
- `order_cancel_enabled=false`
- `authenticated_trading_enabled=false`
- `network_write_performed=false`
- `allowed_for_live=false`

## Payload Contract

The contract artifact records field names, expected types, constraints, and a deterministic fingerprint. It does not emit an executable order payload. If a token id is provided for a future local diagnostic, the artifact stores only presence plus a SHA-256 fingerprint, not the raw token id.

The contract is intentionally not a trading recommendation. It does not select a side, price, outcome, confidence, edge, EV, or real trading action.

## Optional Local Diagnostic Flag

The runner accepts the explicit flag:

```powershell
python -m pm_bot.operator_runner.signed_order_payload_dry_run --market BTC --strategy tiny-momentum --dry-run --token-id <public-token-id> --max-notional-usd 1 --allow-local-order-payload-signing-diagnostic
```

070A does not implement real SDK signing. The guarded flag path checks the local safety gates and then fails closed as `signing_not_implemented` when:

- `--dry-run` is present
- `--max-notional-usd` is less than or equal to `1.0`
- a token id is provided

If the notional is above `1.0`, status is `max_notional_exceeded`. If the token id is missing, status is `missing_token_id`. In every case, private-key reads, local signing, signed payload output, order submission, cancellation, authenticated trading, and network writes remain disabled.

## Redaction Rules

Artifacts may include only contract metadata, booleans, paths, and hashes/fingerprints. They must not contain:

- raw private keys, wallet files, seed phrases, mnemonics, API secrets, auth tokens, or passphrases
- raw or full signed payloads
- raw or full signed orders
- submitted order identifiers, transaction hashes, fills, balances, positions, or PnL

## Artifacts

- `pm_bot/trading_core/artifacts/signed_order_payload_dry_run_070a/signed_order_payload_dry_run_070a_result.json`
- `pm_bot/trading_core/artifacts/signed_order_payload_dry_run_070a/latest_signed_order_payload_dry_run_status_070a.json`
- `pm_bot/trading_core/artifacts/signed_order_payload_dry_run_070a/signed_order_payload_contract_070a.json`
- `pm_bot/trading_core/artifacts/signed_order_payload_dry_run_070a/signed_order_payload_redaction_policy_070a.json`
- `pm_bot/trading_core/artifacts/signed_order_payload_dry_run_070a/signed_order_payload_safety_contract_070a.json`
- `pm_bot/trading_core/artifacts/signed_order_payload_dry_run_070a/signed_order_payload_operator_summary_070a.md`

## Safety Statement

070A is `allowed_for_live=false`, `signed_payload_submit_enabled=false`, and `order_submission_enabled=false`. It is a supervised dry-run contract scaffold only and requires a separate future operator-approved task before any real signing or live order path can exist.
