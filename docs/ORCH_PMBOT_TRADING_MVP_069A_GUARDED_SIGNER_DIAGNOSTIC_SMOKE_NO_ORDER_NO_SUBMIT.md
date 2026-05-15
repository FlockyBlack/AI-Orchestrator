# ORCH PMBOT Trading MVP 069A Guarded Signer Diagnostic Smoke

Task ID: `ORCH-PMBOT-TRADING-MVP-069A-GUARDED-SIGNER-DIAGNOSTIC-SMOKE-NO-ORDER-NO-SUBMIT`

069A adds a guarded local signer diagnostic smoke runner. It is strictly non-trading: it does not sign order payloads, generate signed orders, submit orders, cancel orders, connect wallet UI, or call authenticated trading endpoints.

## Default Safe Run

Default dry-run mode does not read `POLYMARKET_PRIVATE_KEY`.

```powershell
python -m pm_bot.operator_runner.guarded_signer_diagnostic_smoke --market BTC --strategy tiny-momentum --dry-run
```

Expected default result:

- `diagnostic_status=diagnostic_not_requested`
- `private_key_read=false`
- `diagnostic_challenge_signed=false`
- `order_payload_signing_enabled=false`
- `order_submission_enabled=false`
- `order_cancel_enabled=false`
- `authenticated_trading_enabled=false`
- `allowed_for_live=false`

## Explicit Guarded Diagnostic

The key-reading path is opt-in only. The operator must pass `--allow-private-key-diagnostic` in the same command:

```powershell
python -m pm_bot.operator_runner.guarded_signer_diagnostic_smoke --market BTC --strategy tiny-momentum --dry-run --allow-private-key-diagnostic
```

Only this explicit diagnostic path may read `POLYMARKET_PRIVATE_KEY` from the environment. It validates key format, derives a local wallet address when the optional `eth-account` dependency is available, compares the derived address to `POLYMARKET_WALLET_ADDRESS`, and signs only the fixed diagnostic challenge:

```text
PMBOT_SIGNER_DIAGNOSTIC_ONLY_NO_ORDER_NO_SUBMIT
```

That challenge is not an order payload. It contains no price, size, side, maker, taker, token id, salt, nonce, expiration, fee, or order submission fields.

## Redaction Rules

The runner never prints or stores the raw private key. It never prints or stores raw API secret or passphrase values. It never prints the full diagnostic signature.

Allowed diagnostic metadata is limited to:

- private key presence and format booleans
- expected wallet address redacted to prefix and suffix
- derived wallet address redacted to prefix and suffix
- wallet match result
- diagnostic signature redacted to hash fingerprint and length

## Result Meanings

- `diagnostic_not_requested`: default dry-run completed without reading `POLYMARKET_PRIVATE_KEY`.
- `dependency_missing`: explicit diagnostic was requested, but `eth-account` was unavailable; the runner failed closed.
- `missing_private_key`: explicit diagnostic was requested, but `POLYMARKET_PRIVATE_KEY` was absent.
- `invalid_key_format`: explicit diagnostic was requested, but the key was not `0x` plus 64 hex characters.
- `missing_wallet_address`: explicit diagnostic was requested, but `POLYMARKET_WALLET_ADDRESS` was absent.
- `wallet_mismatch`: derived wallet did not match `POLYMARKET_WALLET_ADDRESS`; the diagnostic challenge was not signed.
- `diagnostic_ok`: derived wallet matched and only the fixed non-order challenge was signed. `allowed_for_live` remains `false`.

## Safety Contract

All modes keep these boundaries enforced:

- no order payload signing
- no signed order generation
- no order submission
- no order cancellation
- no authenticated trading calls
- no wallet connection UI
- no Telegram control changes
- no scheduler, daemon, background worker, or autonomous loop
- `allowed_for_live=false`
- `private_key_value_emitted=false`
- `raw_secret_values_emitted=false`
